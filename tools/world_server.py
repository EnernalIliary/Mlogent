#!/usr/bin/env python3
"""world_server.py — 常驻 Mindustry headless 世界 + 本地 JSON 控制口.

玩家用游戏客户端连 <host>:<gamePort>; Agent / 脚本通过 127.0.0.1:<apiPort>
的 JSON 行协议读写这个世界 (world_mcp.py 是它的 MCP 外壳).

为什么要它
----------
tools/mlogsim.py 的 Server 是"一次性沙盒": cwd 用 mkdtemp, 退出即丢弃. 玩家
要长期待在一个世界里, 数据目录 (config/ saves/ logs/) 必须固定, 所以这里
单独起一个常驻进程, 并且把 MCP 与它拆开 —— MCP 随 DSH 会话重启, 服务端不能.

js 结果为什么走文件
-------------------
stdout 是共享的: 玩家聊天/进出、autosave、mod 日志都会插进 js 的输出里, 只等
"undefined" 在多客户端下会串话. 所以每个 js 脚本把结果用 PrintWriter 写进
res-<tok>.txt, 本进程轮询该文件 —— 文件通道与 stdout 噪声完全隔离.

用法
----
    python tools/world_server.py --map groundZero
    python tools/world_server.py --map groundZero --paused --game-port 6567
    python tools/world_server.py --no-host          # 只起 JVM, 不开服 (调试启动链)

握手文件 out/_world/daemon.json 里有 pid / apiPort / gamePort / map, MCP 和
脚本都读它来找这个世界. 日志: out/_world/server.log, 审计: out/_world/audit.log.
"""
from __future__ import annotations

import argparse
import base64
import json
import math
import os
import re
import socket
import sys
import threading
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mlogsim import sweep_orphans  # noqa: E402
from world_process import WorldProcess
from types import SimpleNamespace
from world_projection import projection_director as _run_projection_director
from world_projection import CONTROL_OPERATIONS as PROJECTION_CONTROL_OPS, control as projection_control
import world_projection_actions as _projection_actions_module
from world_projection_actions import _projs
from world_channel import WorldChannel
from world_mirrors import (MK_INSTALL_JS, MK_STATE_JS, MK_ON_JS, MK_CLEAR_JS, MK_ADD_JS,
                           MK_LIST_JS, CONTROL_OPERATIONS as MIRROR_CONTROL_OPS, control as mirror_control)
from world_events import (EV_INSTALL_JS, CHANGES_JS, CHAT_JS, PUSH_JS,
                          OPERATIONS as WORLD_EVENT_OPS, read_events)
from world_queries import BUILDS_JS, BUILDING_AT_JS, LOGIC_LIST_JS, LOGIC_GET_JS, LOGIC_VARS_JS
import world_doors as _door_registry
from world_doors import OPERATIONS as WORLD_DOOR_OPS
from world_doors import (DOORS_JS, DOOR_ACT_JS, DOOR_CLEAR_JS, DOOR_ENTER_JS, DOOR_HITS_JS, DOOR_SET_JS, TAPS_JS, TAP_FIRE_JS)
from world_mirrors import (MS_INSTALL_JS, MS_APPLY_JS, MS_CLEAR_JS,
                           _mirror_slot, mirror_push, mirror_watch, mirror_stop)
from world_display import (FRAME_CLEAR_JS, FRAME_COLOR, FRAME_LIST_JS, FRAME_LIVE_MAX, FRAME_PAINT_JS, FRAME_SWEEP_JS, LIVE_COLOR, SB_BASE, SB_EVENTS, SB_FONT, SB_INSTALL_JS, SB_MAX_LINES, SB_SET_JS, SB_SPAN, SB_SWEEP_JS, _sb_store, _sb_write, frame_clear, frame_paint, sb_clear, sb_event, sb_lines, sb_render)
from world_scenes import (feed_age, feed_world, feed_anchor, feed_scene, feed_bbox,
                          feed_units, scenes_from_feeds, load_dir_scenes, world_size, layout_scenes)
from world_maps import switch_map, change_map, OPERATIONS as WORLD_MAP_OPS
from world_schematics import (SCHEMATIC_PLACE_JS, SCHEMATIC_SAVE_JS, SCHEMATIC_LIST_JS,
                              OPERATIONS as WORLD_SCHEMATIC_OPS, schematic as schematic_world)
from world_edits import (PLACE_JS, CLEAR_JS, SPAWN_JS, KILLUNITS_JS, CLEARBUILDS_JS,
                         LOGIC_SET_JS, OPERATIONS as WORLD_EDIT_OPS, edit as edit_world)
from world_queries import (STATUS_JS, PLAYERS_JS, UNITS_JS, UNIT_JS, MAPS_JS,
                           OPERATIONS as WORLD_QUERY_OPS, query as query_world)
from world_protocol import API, coerce, units_table, parse_tsv
from world_protocol import make_handler as _make_protocol_handler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORLD = os.path.join(ROOT, "out", "_world")
DEFAULT_FEED = os.path.join(WORLD, "feed.json")
DATA = os.path.join(WORLD, "server")          # java cwd: ASCII, 持久
HANDSHAKE = os.path.join(WORLD, "daemon.json")
LOG = os.path.join(WORLD, "server.log")
AUDIT = os.path.join(WORLD, "audit.log")
SCHEM_DIR = os.path.join(DATA, "config", "schematics")   # 客户端也从这里拿蓝图
DEFAULT_JAR = os.path.join(ROOT, "out", "_server160.jar")
JAVA_CANDIDATES = [
    os.path.join(ROOT, "out", "jre21", "jdk-21.0.5+11-jre", "bin", "java.exe"),
    r"E:\Program Files (x86)\Steam\steamapps\common\Mindustry\jre\bin\java.exe",
]


def find_java(explicit: str | None = None) -> str:
    for c in ([explicit] if explicit else []) + JAVA_CANDIDATES + ["java"]:
        if not c:
            continue
        if os.path.isabs(c):
            if os.path.isfile(c):
                return c
        else:
            from shutil import which
            p = which(c)
            if p:
                return p
    raise SystemExit("找不到 java: 用 --java 指定")


def port_free(port: int) -> bool:
    """Mindustry 同时要 UDP 和 TCP; Windows 上 6528-6727 常被 Hyper-V/WinNAT 保留.

    TCP 落到保留段时 bind 报 WSAEACCES(10013), 而 Mindustry 会把任何 bind 失败
    都打印成 "Unable to host: Port ... already in use" —— 所以开服前自己先探一遍,
    否则会看到"每个端口都被占用"的假象.
    """
    for typ in (socket.SOCK_DGRAM, socket.SOCK_STREAM):
        s = socket.socket(socket.AF_INET, typ)
        try:
            s.bind(("0.0.0.0", port))
        except OSError:
            return False
        finally:
            s.close()
    return True


def pick_port(preferred: int, span: int = 40) -> tuple[int, str | None]:
    if port_free(preferred):
        return preferred, None
    for p in range(15000, 15000 + span):
        if port_free(p):
            return p, ("端口 %d 不可用 (Windows 保留段/Hyper-V), 已改用 %d"
                       % (preferred, p))
    raise SystemExit("15000..%d 都被占用, 无法开服" % (15000 + span))


def audit(op: str, **kw):
    try:
        os.makedirs(WORLD, exist_ok=True)
        with open(AUDIT, "a", encoding="utf-8") as f:
            f.write(json.dumps({"t": time.strftime("%Y-%m-%d %H:%M:%S"), "op": op, **kw},
                               ensure_ascii=False) + "\n")
    except Exception:
        pass


class World(WorldProcess):
    """一个 java 服务端 + 它的控制通道."""

    def __init__(self, java: str, jar: str, *, map_name: str | None = None,
                 host: bool = True, paused: bool = False, game_port: int = 6567,
                 js_timeout: float = 60.0, server_name: str | None = None):
        self.java, self.jar = java, jar
        self.map_name = map_name
        self.game_port = game_port
        self.js_timeout = js_timeout
        self.players_peak = 0
        self.mirror_feed: str | None = None   # 状态镜推送文件 (mlogsim/脚本往里写 JSON)
        self._mirror_started = False
        os.makedirs(os.path.join(DATA, "config", "logs"), exist_ok=True)
        os.makedirs(os.path.join(DATA, "config", "saves"), exist_ok=True)
        os.makedirs(WORLD, exist_ok=True)
        super().__init__(java, jar, data_dir=DATA, log_path=LOG)
        self._channel = WorldChannel(self)
        try:
            self._boot(host=host, paused=paused, server_name=server_name)
        except BaseException:
            self.close(force=True)
            raise

    def wait_for(self, needle: str, timeout: float) -> list[str]:
        return self._channel.wait_for(needle, timeout)

    def console(self, cmd: str, quiet: float = 0.30, timeout: float = 8.0) -> dict:
        return self._channel.console(cmd, quiet, timeout)

    def _collect(self, seq0: int, quiet: float, timeout: float) -> list[str]:
        return self._channel._collect(seq0, quiet, timeout)

    def js(self, body: str, timeout: float | None = None) -> list[str]:
        return self._channel.js(body, timeout)

    def put_file(self, text: str, prefix: str = 'in') -> str:
        return self._channel.put_file(text, prefix)

    def take_file(self, name: str, timeout: float = 10.0) -> str:
        return self._channel.take_file(name, timeout)

    # ---- 启动链 -----------------------------------------------------
    def _boot(self, host: bool, paused: bool, server_name: str | None):
        self._wait("Server loaded.", 90)
        if server_name:
            self.console("name " + server_name, quiet=0.2, timeout=4)
        if self.game_port:
            self.console("config port %d" % self.game_port, quiet=0.2, timeout=4)
        if not host:
            self.hosted = False
            return
        cmd = "host" + ((" " + self.map_name) if self.map_name else "")
        for attempt in range(10):
            res = self.console(cmd, quiet=1.0, timeout=180)
            out = res["lines"]
            text = "\n".join(out)
            if "Opened a server" in text:
                break
            if "already in use" in text and attempt < 9:
                # 端口的 TIME_WAIT / 上一个实例还没退干净: 换一个真的空闲端口重试
                self.game_port, _ = pick_port(self.game_port + 1)
                self.console("config port %d" % self.game_port, quiet=0.25, timeout=5)
                continue
            bad = [ln for ln in out if "Unable" in ln or "Error" in ln or "unknown" in ln.lower()]
            hint = ""
            if "No map with name" in text and self.map_name:
                # 自定义图还没装进 config/maps: 退回随机内置图，别让守护进程整个起不来
                try:
                    names = [ln.split("\t")[0] for ln in self.js(MAPS_JS)][:12]
                    print("[warn] 地图 %r 不存在, 回退随机图。可用图名(前 12): %s"
                          % (self.map_name, ", ".join(names)), flush=True)
                except Exception:
                    print("[warn] 地图 %r 不存在, 回退随机图" % self.map_name, flush=True)
                self.map_name = None
                cmd = "host"
                continue
            if "No map with name" in text:
                try:
                    names = [ln.split("\t")[0] for ln in self.js(MAPS_JS)][:12]
                    hint = " 可用图名(前 12): " + ", ".join(names)
                except Exception:
                    hint = " (拿不到图名列表, 见日志)"
            self.close()
            raise SystemExit("开服失败: " + (" | ".join(bad) or text[-400:]) + hint)
        self.hosted = True
        # headless host 会用自己的规则覆盖存档里的 rules（waves 会变 true）:
        # 调试世界统一在这里钉死，重启也不需要人工再改一遍。
        try:
            self.js("var r=Vars.state.rules; r.waves=false; r.infiniteResources=true; "
                    "r.canGameOver=false; r.logicUnitControl=true; sb.append(r.waves);")
        except Exception:
            pass
        # 建筑变更日志: TileChangeEvent(放置/拆除) + ConfigEvent(改配置) 都记进环形缓冲
        try:
            r = self.js(EV_INSTALL_JS % {"chatlog": json.dumps(os.path.join(DATA, "chat.log").replace("\\", "/")),
                                   "pushfile": json.dumps(os.path.join(DATA, "push.jsonl").replace("\\", "/")),
                                   "autoadmin": 0 if getattr(self, "no_push_admin", False) else 1,
                                   "mineblock": json.dumps(MINE_BLOCK)})
            if not r or not str(r[0]).startswith("installed"):
                print("[warn] 变更日志监听安装失败: %r" % (r,), flush=True)
        except Exception as exc:
            print("[warn] 变更日志监听安装失败: %s" % exc, flush=True)
        # 门的动作本体: 只定义一次, TapEvent 监听与 door_enter 共用
        try:
            self.js(DOOR_ACT_JS)
        except Exception as exc:
            print("[warn] 门动作安装失败: %s" % exc, flush=True)
        # 状态镜: 外部(mlogsim/脚本)给坐标表, 服务端画成兵种图标 marker
        try:
            self.js(MS_INSTALL_JS)
            self.js(SB_INSTALL_JS)
        except Exception as exc:
            print("[warn] 状态镜安装失败: %s" % exc, flush=True)
        # 点击门已废弃（改成「放下脉冲地雷即开始投影」），boot 不再重装
        # doors.json 里的旧门。以前重装会就地补一颗 shock-mine，TileChangeEvent
        # 又把它当成玩家新放的雷 ⇒ 凭空多出一次投影。
        # try:
        #     n = door_reload(self)
        #     ...
        # except Exception as exc: ...

        try:
            for ln in self.js(STATUS_JS):
                if ln.startswith("map="):
                    self.map_actual = ln.split("=", 1)[1]
                    if not self.map_name:
                        self.map_name = self.map_actual
        except Exception:
            pass
        if paused:
            self.console("pause on", quiet=0.2, timeout=4)

    def _wait(self, needle: str, timeout: float) -> list[str]:
        return self.wait_for(needle, timeout)

# ---- JS 转储 ---------------------------------------------------------
















# 状态镜: 把外部给的坐标表画成 marker, 不读 Groups.unit
# ------------------------------------------------------
# 和 MK_INSTALL_JS(跟随真单位) 的区别: 这里的坐标来自 mlogsim / 脚本 / push 文件,
# 所以可以画"仿真的影子"——单位在真世界里不动也能看到它们在跑.




# 文本先由 Python 写进 DATA/sb<slot>.txt, 这里只传数字:
# 控制台 js 行会破坏参数里的字符串字面量(SyntaxError: Unexpected token).



# 手放一个标记: 点或文字. text 非空时用 TextMarker(点标记 + 一行字)









MINE_HITS_JS = r"""
/* 取走"玩家刚放下的脉冲地雷"列表(JSON 数组), 由 projection_director 轮询 */
if(typeof _mineHits === 'undefined'){ sb.append('[]'); }
else { var a = _mineHits.splice(0, _mineHits.length); sb.append(JSON.stringify(a)); }
"""

MINE_GONE_JS = r"""
/* 取走"最近被清空的格子"列表(仅调试用; 结束判定已改为直接读圆心方块) */
if(typeof _mineGone === 'undefined'){ sb.append('[]'); }
else { var a = _mineGone.splice(0, _mineGone.length); sb.append(JSON.stringify(a)); }
"""

MINE_STATE_JS = r"""
/* 圆心那颗地雷现在还在不在? 直接读格子上的方块名, 不依赖事件顺序:
   场景 clear 会在投影开始的同一瞬间产生大量 air 事件, 用事件判"被拆"必然误报. */
var stx = %(x)d, sty = %(y)d;
var stl = Vars.world.tile(stx, sty);
if(stl == null || stl.block() == null){ sb.append('null'); }
else { sb.append(String(stl.block().name)); }
"""





REPLACE_MINE_JS = r"""
/* 场景的 clear 矩形会把玩家放的地雷抹掉, 这里原样钉回去.
   先写 _mineIgnore, 让监听器知道这一颗是自己放的, 不会再次触发投影. */
var mx = %(x)d, my = %(y)d;
_mineIgnore = mx + ',' + my;
_mineIgnoreAir = mx + ',' + my;
var mblk = Vars.content.block(%(block)s);
var mt = Vars.world.tile(mx, my);
if(mt != null && mblk != null){
  mt.setNet(mblk, Vars.state.rules.defaultTeam, 0);
  sb.append('MINE	').append(mx).append(',').append(my);
} else { sb.append('MINE	-1,-1'); }
"""

DEMOLISH_JS = r"""
/* 拆掉这次投影铺下去的建筑(含核心), 走 setNet 才能让客户端同步看到消失.
   pick = [[x,y,blockName], ...]; 只有当前格还是当初放的那个方块才拆, 不误伤玩家后放的东西. */
/* list 直接内联成 JS 数组字面量: 之前写成 JSON.parse([[...]]) 会把已经
   解析好的数组再 String() 一次, 报 Expected end of stream at char 3 */
var pick = %(list)s;
var DRAIR = Vars.content.block('air'), DRTEAM = Vars.state.rules.defaultTeam, dn = 0;
for(var di=0;di<pick.length;di++){
  var dpx = pick[di][0], dpy = pick[di][1], dpb = pick[di][2];
  var dtl = Vars.world.tile(dpx, dpy);
  if(dtl != null && dtl.build != null && String(dtl.block().name) == dpb){
    dtl.setNet(DRAIR, DRTEAM, 0); dn++;
  }
}
sb.append('DEMOLISH	').append(dn);
"""




DOORS_FILE = os.path.join(DATA, "doors.json")
MINE_BLOCK = "shock-mine"       # 玩家放下这颗地雷 = 请求投影














# ---------------------------------------------------------------- 投影导演
# 有仿真在跑 -> 放一颗脉冲地雷当按钮 + 聊天栏提示; 玩家点它 = 开始投影.
# "投影"分两半: 建筑是场景脚本一次性复刻(处理器放上去但禁用), 单位是 marker 影子,
# 每 0.12 s 从 mlogsim --push 写的 JSON 文件里读一次.

FREE_TILE_JS = r"""
/* 从 (cx,cy) 往外螺旋找一格空地; 越界或找不到返回 -1,-1 */
var cx = %(cx)d, cy = %(cy)d, lim = %(lim)d;
var found = false, fx = -1, fy = -1;
for(var r = 0; r <= lim && !found; r++){
  for(var dyy = -r; dyy <= r && !found; dyy++){
    for(var dxx = -r; dxx <= r && !found; dxx++){
      if(Math.max(Math.abs(dxx), Math.abs(dyy)) != r) continue;
      var tx = cx + dxx, ty = cy + dyy;
      var t = Vars.world.tile(tx, ty);
      if(t == null) continue;
      if(t.block() == Packages.mindustry.content.Blocks.air && t.build == null){
        fx = tx; fy = ty; found = true;
      }
    }
  }
}
sb.append(fx).append(',').append(fy);
"""


def door_register(w, x, y, kind="watch", unit="poly", tx=None, ty=None,
                  label=None, block="shock-mine", scene_path=None, persist=True,
                  scene_at=None, feed=None):
    return _door_registry.door_register(w, x, y, kind, unit, tx, ty, label, block,
                                       scene_path, persist, scene_at, feed, doors_file=DOORS_FILE)


def door_reload(w):
    return _door_registry.door_reload(w, doors_file=DOORS_FILE)


def find_free_tile(w, near, lim=10):
    """Spiral out from *near* until a tile with no block on it shows up."""
    out = w.js(FREE_TILE_JS % {"cx": int(near[0]), "cy": int(near[1]), "lim": int(lim)})
    if not out:
        return [int(near[0]), int(near[1])]
    try:
        a, b = str(out[0]).split(",")
        x, y = int(float(a)), int(float(b))
    except Exception:
        return [int(near[0]), int(near[1])]
    if x < 0 or y < 0:
        return [int(near[0]), int(near[1])]
    return [x, y]




# 第二个框（按 feed 里单位实际坐标算出来的外接框）用的颜色: 青色，和落雷框区分开
# 边界框只在「仿真 feed 还新鲜」的时候画出来: 没跑仿真时满屏框只会让人困惑










# ---------------------------------------------------------------- 沙盘日志板
# 世界里每块沙盘左上角都用 TextMarker 列一块小面板: 标题 / feed 新鲜度 / 投影状态 /
# 单位数 / 最近几条事件. 这样"沙盘在干什么"不用切回聊天栏看.




























RESYNC_JS = r"""
/* setNet 只给方块本身; 客户端那台处理器要有代码/配置, 必须靠 tileConfig 包.
   首包可能和方块创建同帧被丢, 所以投影铺完再补发一次(幂等). */
var pick = %(list)s, nb = 0, LB = Packages.mindustry.world.blocks.logic.LogicBlock;
for(var i = 0; i < pick.length; i++){
  var b = Vars.world.build(pick[i][0], pick[i][1]);
  if(b == null) continue;
  try{
    b.configureAny(b.config());
    nb++;
  }catch(e1){}
}
sb.append('RESYNC	').append(nb);
"""


def resync_builds(w, builds):
    """把场景里处理器/建筑的 config 再往客户端补发一次(见 RESYNC_JS)."""
    rows = [[int(b[0]), int(b[1]), str(b[2])] for b in (builds or [])]
    if not rows:
        return 0
    out = w.js(RESYNC_JS % {"list": json.dumps(rows)})
    n = 0
    for ln in (out or []):
        s = str(ln)
        if s.startswith("RESYNC	"):
            try:
                n = int(float(s.split("	")[1]))
            except Exception:  # noqa: BLE001
                n = 0
    return n










def _projection_actions():
    return SimpleNamespace(**{name: globals()[name] for name in ('MINE_BLOCK', 'REPLACE_MINE_JS', 'DEMOLISH_JS', 'MS_CLEAR_JS', 'mirror_watch', 'mirror_stop', 'resync_builds', 'sb_event', 'chat')})


def project_at(w, x, y, feed, scene_path=None, tell=True, anchor=None, slot=0, pin=True):
    return _projection_actions_module.project_at(w, x, y, feed, scene_path, tell, anchor, slot, pin,
                                                 services=_projection_actions())


def end_projection(w, slot, why="地雷被拆除"):
    return _projection_actions_module.end_projection(w, slot, why, services=_projection_actions())


def start_projection(w, meta, slot=0):
    return _projection_actions_module.start_projection(w, meta, slot, services=_projection_actions())


def projection_director(w, feed, scene_path=None, at=None, poll=0.5,
                        fresh=25.0, lim=10, scenes=None, frames=True,
                        frame_floor="marker", at_cell=64, feeds=None, auto=True,
                        hold=0.0):
    services = SimpleNamespace(**{name: globals()[name] for name in ('FRAME_LIVE_MAX', 'FRAME_SWEEP_JS', 'LIVE_COLOR', 'MINE_BLOCK', 'MINE_HITS_JS', 'MINE_STATE_JS', 'SB_SWEEP_JS', '_projs', '_sb_store', 'chat', 'end_projection', 'frame_clear', 'frame_paint', 'project_at', 'sb_clear', 'sb_event', 'sb_render')})
    return _run_projection_director(w, feed, scene_path, at, poll, fresh, lim, scenes,
                                    frames, frame_floor, at_cell, feeds, auto, hold,
                                    services=services)





















def make_handler(world: World, stop_cb):
    """Compatibility factory: bind the daemon dispatcher explicitly."""
    return _make_protocol_handler(world, stop_cb, dispatch)


CHAT_LOG = True            # --chat-log 控制：把 agent 的写操作打进游戏聊天栏
CHAT_PREFIX = "[agent] "
CHAT_OPS = {"place", "clear", "spawn", "killunits", "clearbuilds", "reset", "switch", "door",
            "logic_set", "schematic", "schematic_save", "scene", "load", "save", "pause",
            "mirror", "mirror_state", "mirror_feed", "arm", "projection", "frames",
            "sblog"}


def chat(w: World, text: str):
    """把一行字打进游戏聊天栏（console say）。任何失败都不影响主流程。"""
    if not CHAT_LOG or not text:
        return
    line = (CHAT_PREFIX + text).replace("\n", " ").replace("\r", " ").strip()
    if len(line) > 220:
        line = line[:217] + "..."
    try:
        w.console("say " + line, quiet=0.12, timeout=4)
    except Exception:
        pass


def chat_line(op: str, req: dict, resp: dict) -> str:
    if not isinstance(resp, dict) or not resp.get("ok"):
        if isinstance(resp, dict) and resp.get("error"):
            return "%s 失败: %s" % (op, str(resp.get("error"))[:80])
        return ""
    if op == "place":
        return "place %s @ %s,%s" % (req.get("block"), req.get("x"), req.get("y"))
    if op == "clear":
        return "clear @ %s,%s" % (req.get("x"), req.get("y"))
    if op == "spawn":
        return "spawn %s x%s @ %s,%s" % (req.get("type"), resp.get("spawned"),
                                         req.get("x"), req.get("y"))
    if op == "killunits":
        return "kill units 清掉 %s，留下 %s" % (resp.get("killed"), resp.get("kept"))
    if op == "clearbuilds":
        return "clear builds 清掉 %s" % resp.get("cleared")
    if op in ("reset", "switch"):
        return "换图 -> %s" % (resp.get("map") or req.get("map") or "?")
    if op == "logic_set":
        return "logic @ %s,%s (%s 字节)" % (req.get("x"), req.get("y"), resp.get("codeLen"))
    if op == "schematic":
        return "蓝图 %s @ %s,%s (放下 %s 块)" % (resp.get("name") or "?", resp.get("x"),
                                              resp.get("y"), resp.get("placed"))
    if op == "schematic_save":
        return "存蓝图 %s (%s 块)" % (resp.get("name"), resp.get("tiles"))
    if op == "scene":
        rep = resp.get("scene") or {}
        return "场景 %s：%s 座建筑 / %s 只单位" % (
            str(req.get("path") or "").replace("\\", "/").split("/")[-1],
            rep.get("placed"), rep.get("units"))
    if op == "door":
        return "门 %s @ %s,%s -> %s(%s) 目标 %s" % (resp.get("kind"), req.get("x"), req.get("y"),
                                                resp.get("unit"), resp.get("label"), resp.get("target"))
    if op == "save":
        return "存档 %s" % req.get("name")
    if op == "load":
        return "读档 %s" % req.get("name")
    if op == "pause":
        return "暂停" if req.get("on", True) else "恢复"
    if op == "mirror":
        return "标记镜 开（%s 个标记）" % resp.get("markers") if req.get("on", True) else "标记镜 关"
    if op == "arm":
        sc = resp.get("scenes") or []
        if len(sc) > 1:
            return "监听中：%d 块沙盘，放下脉冲地雷即开始投影" % len(sc)
        return "监听中：放下脉冲地雷即开始投影"
    if op == "frames":
        return "场景边界已更新"
    return ""


def dispatch(w: World, req: dict, stop_cb) -> dict:
    op = (req.get("op") or "").strip()
    resp = _dispatch(w, req, stop_cb)
    if op in CHAT_OPS:
        try:
            msg = chat_line(op, req, resp)
            if msg:
                chat(w, msg)
        except Exception:
            pass
    return resp


def _dispatch(w: World, req: dict, stop_cb) -> dict:
    op = (req.get("op") or "").strip()
    if op in WORLD_MAP_OPS:
        return change_map(w, req, audit=audit)
    if op in WORLD_QUERY_OPS:
        return query_world(w, req, data_dir=DATA)
    if op in WORLD_EDIT_OPS:
        return edit_world(w, req, audit=audit, data_dir=DATA)
    if op in WORLD_SCHEMATIC_OPS:
        return schematic_world(w, req, audit=audit, schematic_dir=SCHEM_DIR)
    if op in WORLD_EVENT_OPS:
        return read_events(w, req)
    if op == "tap":
        # 合成一次点击: 等价于玩家真的点了这一格(测试门用; 有玩家时连门一起触发)
        x = int(req.get("x") or 0)
        y = int(req.get("y") or 0)
        who = req.get("who")
        out = w.js(TAP_FIRE_JS % {"x": x, "y": y,
                                  "who": json.dumps(str(who) if who else None)})
        if not out:
            return {"ok": False, "error": "no output"}
        audit("tap", x=x, y=y, result=out[0])
        return {"ok": True, "result": out[0]}
    if op in PROJECTION_CONTROL_OPS:
        services = SimpleNamespace(**{name: globals()[name] for name in ('projection_director', 'frame_clear', 'frame_paint', 'FRAME_LIST_JS', 'mirror_stop', '_mirror_slot', 'start_projection', 'sb_event', 'sb_render', 'sb_clear', 'SB_SWEEP_JS', 'FRAME_LIVE_MAX', 'sb_lines')})
        return projection_control(w, req, services=services, audit=audit)
    if op in WORLD_DOOR_OPS:
        return _door_registry.door_operation(w, req, audit=audit, doors_file=DOORS_FILE)
    if op in MIRROR_CONTROL_OPS:
        return mirror_control(w, req, root=ROOT, audit=audit)
    if op in ("scene", "scene_probe"):
        # 同一份 tools/scene.py 描述文件，mlogsim 和这里都认：模拟器里验证过的
        # 布局/链接/代码可以在真世界里原样复现，不用手抄坐标。
        path = req.get("path") or req.get("scene") or ""
        if not path:
            return {"ok": False, "error": "need path"}
        import scene as scene_mod
        try:
            sc = scene_mod.load(path)
        except scene_mod.SceneError as exc:
            return {"ok": False, "error": str(exc)}
        at = req.get("at")
        if at is None and req.get("at_x") is not None:
            at = [req.get("at_x"), req.get("at_y")]
        rep = scene_mod.apply_world(w, sc, at=at)
        w._scene_report = rep
        res = {"ok": not rep["errors"], "scene": rep}
        if req.get("door"):
            # 场景先铺, 门最后放: clear 矩形会把先放的地雷抹掉
            d = door_register(w, rep["anchor"][0], rep["anchor"][1],
                              kind=req.get("door_kind") or "watch",
                              unit=req.get("door_unit") or "poly",
                              label=req.get("door_label"),
                              block=req.get("door_block") or "shock-mine",
                              scene_path=None,
                              feed=req.get("mirror_feed"))
            res["door"] = d
        if req.get("mirror_feed"):
            # 场景铺完就把仿真投影接到同一批坐标上; 偏移量按格算
            try:
                mirror_stop(w)
                # 没显式给偏移就用场景自己的位移: 仿真坐标 + 位移 = 世界坐标
                _sh = rep.get("shift") or [0, 0]
                _dx = float(req.get("mirror_dx") if req.get("mirror_dx") is not None else _sh[0])
                _dy = float(req.get("mirror_dy") if req.get("mirror_dy") is not None else _sh[1])
                _slot = int(req.get("mirror_slot") or 0)
                w.mirror_off = (_dx, _dy)
                mirror_watch(w, str(req["mirror_feed"]), slot=_slot, dx=_dx, dy=_dy)
                res["mirror"] = {"on": True, "slot": _slot, "off": [_dx, _dy]}
            except Exception as exc:
                res["mirror"] = {"on": False, "error": str(exc)}
        audit("scene", path=path, name=sc["name"], shift=rep.get("shift"),
              placed=rep["placed"], units=rep["units"], errors=len(rep["errors"]))
        if op == "scene_probe":
            # a freshly loaded processor has not ticked yet: its executor has no
            # variables until updateTile() runs once, so reads would all be null.
            time.sleep(1.5)
            res["probe"] = scene_mod.probe_world(w, sc)
        return res
    if op == "console":
        cmd = str(req.get("cmd") or "").strip()
        if not cmd:
            return {"ok": False, "error": "empty cmd"}
        audit("console", cmd=cmd)
        return w.console(cmd, quiet=float(req.get("quiet") or 0.3),
                         timeout=float(req.get("timeout") or 8))
    if op == "js":
        src = str(req.get("code") or "")
        if not src.strip():
            return {"ok": False, "error": "empty code"}
        audit("js", code=src[:500])
        return {"ok": True, "lines": w.js(src, timeout=float(req.get("timeout") or 0) or None)}
    if op == "say":
        txt = str(req.get("text") or "").rstrip()
        audit("say", text=txt)
        return w.console("say " + txt, quiet=0.2, timeout=5)
    if op == "pause":
        on = bool(req.get("on", True))
        audit("pause", on=on)
        return w.console("pause " + ("on" if on else "off"), quiet=0.25, timeout=6)
    if op == "save":
        name = str(req.get("name") or "world").strip().replace(" ", "_")
        audit("save", name=name)
        return w.console("save " + name, quiet=0.5, timeout=30)
    if op == "load":
        name = str(req.get("name") or "").strip()
        if not name:
            return {"ok": False, "error": "empty name"}
        audit("load", name=name)
        return w.console("load " + name, quiet=0.8, timeout=120)
    if op == "shutdown":
        audit("shutdown")
        threading.Thread(target=stop_cb, daemon=True).start()
        return {"ok": True, "bye": True}
    return {"ok": False, "error": "unknown op: %r" % op}


def main(argv=None):
    ap = argparse.ArgumentParser(description="常驻 Mindustry 世界 + JSON 控制口")
    ap.add_argument("--map", default="大肥鱼的调试世界",
                    help="地图名（内置图如 Fork，或 config/maps 里的自定义图）；找不到时回退随机图")
    ap.add_argument("--no-host", action="store_true", help="只起 JVM, 不开服")
    ap.add_argument("--paused", action="store_true", help="开服后立即暂停")
    ap.add_argument("--game-port", type=int, default=6567, help="游戏端口 (默认 6567)")
    ap.add_argument("--api-port", type=int, default=0, help="JSON 控制口端口 (0=自动)")
    ap.add_argument("--js-timeout", type=float, default=60.0)
    ap.add_argument("--chat-log", default=True, action=argparse.BooleanOptionalAction,
                    help="把 agent 的写操作打进游戏聊天栏 (默认开)")
    ap.add_argument("--chat-prefix", default="[agent] ")
    ap.add_argument("--name", default="world.execute(Mindustry)", help="服务器名")
    ap.add_argument("--mirror-feed", default=None, metavar="FILE",
                    help="盯住这个 JSON 文件（mlogsim --push 写它），一变就把里面的单位画成 marker（立即开始）")
    ap.add_argument("--watch-feed", default=None, metavar="FILE", action="append",
                    help="仿真 feed（mlogsim --push 写它），可重复给多条：按顺序与 "
                         "--watch-scene 一一配对（第 i 个场景盯第 i 条 feed），"
                         "只给一条则所有场景共用；默认 auto 模式：feed 新鲜就自己铺，"
                         "不放雷也能看")
    ap.add_argument("--watch-scene", default=None, metavar="JSON", action="append",
                    help="要复刻的场景文件，可重复给多个：每个场景有自己的矩形边界，"
                         "地雷落在哪个框里就复刻哪个场景。缺省=用 feed 里记的场景"
                         "（mlogsim --scene X --push F 会把 X 写进 F），也就是说只给 "
                         "--watch-feed 就够；这里的显式值只用于覆盖/对照")
    ap.add_argument("--frame-floor", default="marker", metavar="X",
                    help="场景边界：marker（默认，用点状标记画框）/ none（不画）；"
                         "旧值 metal-floor 等仍接受但已改成 marker —— 不再动地形")
    ap.add_argument("--frame-cell", type=int, default=64, metavar="N",
                    help="沙盘格子边长（默认 64）：场景按 N×N 的格子从地图左上角开始排，"
                         "锚点落在格子正中")
    ap.add_argument("--watch-at", default=None, metavar="X,Y",
                    help="已废弃：现在由玩家放下的地雷决定圆心")
    ap.add_argument("--hold", type=float, default=0.0, metavar="SEC",
                    help="仿真停下后, 框和投影再多留 SEC 秒（默认 0 = 10 s 内收摊）; "
                         "tick 级调试跑完想停下来看的时候给 60 之类")
    ap.add_argument("--no-projection", action="store_true",
                    help="完全不开投影导演（连默认 feed 也不盯）")
    ap.add_argument("--manual", action="store_true",
                    help="关掉自动投影：只有放下脉冲地雷才开始（默认是有仿真就自己铺）")
    ap.add_argument("--no-push-admin", action="store_true",
                    help="不要自动给进来的玩家 admin（默认给，这样他们能在聊天栏用 /push 跟 agent 说话）")
    ap.add_argument("--java", default=None)
    ap.add_argument("--jar", default=DEFAULT_JAR)
    a = ap.parse_args(argv)
    if not a.watch_feed and not a.mirror_feed:
        # 不给 --watch-feed 就盯默认 feed：任何 --project 的仿真一跑就自动
        # 出现在地图上，跑完自动收摊。要看纯图就给 --no-projection。
        a.watch_feed = [DEFAULT_FEED]

    java = find_java(a.java)
    jar = os.path.abspath(a.jar)
    if not os.path.isfile(jar):
        raise SystemExit("找不到 jar: " + jar)

    global CHAT_LOG, CHAT_PREFIX
    CHAT_LOG = bool(a.chat_log)
    CHAT_PREFIX = a.chat_prefix

    game_port, port_note = pick_port(a.game_port)
    if port_note:
        print("[warn] " + port_note, file=sys.stderr)
    w = World(java, jar, map_name=a.map, host=not a.no_host, paused=a.paused,
              game_port=game_port, js_timeout=a.js_timeout, server_name=a.name)
    w.no_push_admin = bool(getattr(a, "no_push_admin", False))
    if a.mirror_feed:
        mirror_watch(w, a.mirror_feed)
    if getattr(a, "watch_feed", None) or getattr(a, "watch_scene", None):
        # 玩家放下一颗脉冲地雷, 就以它为圆心开始投影 (不自己放雷、不用点击)
        projection_director(w, a.watch_feed, None, scenes=getattr(a, "watch_scene", None),
                            frames=str(getattr(a, "frame_floor", "") or "").lower() != "none",
                            frame_floor=getattr(a, "frame_floor", "marker"),
                            at_cell=int(getattr(a, "frame_cell", 64) or 64),
                            feeds=getattr(a, "watch_feed", None),
                             auto=not getattr(a, "manual", False),
                             hold=float(getattr(a, "hold", 0.0) or 0.0))

    srv = API(("127.0.0.1", a.api_port), make_handler(w, lambda: None))
    port = srv.server_address[1]
    state = {"stopping": False}

    def stop():
        if state["stopping"]:
            return
        state["stopping"] = True
        try:
            w.close()
        finally:
            try:
                os.remove(HANDSHAKE)
            except Exception:
                pass
            os._exit(0)

    srv.RequestHandlerClass = make_handler(w, stop)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    info = {"pid": os.getpid(), "apiPort": port, "gamePort": w.game_port,
            "map": getattr(w, "map_actual", None) or w.map_name,
            "hosted": getattr(w, "hosted", False),
            "portNote": port_note,
            "startedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
            "dataDir": DATA, "log": LOG,
            "java": java, "jar": jar}
    with open(HANDSHAKE, "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    print(json.dumps(info, ensure_ascii=False))
    sys.stdout.flush()
    try:
        while not state["stopping"]:
            time.sleep(0.5)
            if w.proc and w.proc.poll() is not None:
                state["stopping"] = True
                try:
                    os.remove(HANDSHAKE)
                except Exception:
                    pass
                print("java 退出, 关掉控制口", file=sys.stderr)
                break
    except KeyboardInterrupt:
        pass
    stop()


if __name__ == "__main__":
    main()
