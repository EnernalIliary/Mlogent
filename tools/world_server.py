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
import socketserver
import subprocess
import sys
import threading
import time
import uuid
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mlogsim import _win_kill_with_parent, sweep_orphans  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORLD = os.path.join(ROOT, "out", "_world")
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


class World:
    """一个 java 服务端 + 它的控制通道."""

    def __init__(self, java: str, jar: str, *, map_name: str | None = None,
                 host: bool = True, paused: bool = False, game_port: int = 6567,
                 js_timeout: float = 60.0, server_name: str | None = None):
        self.java, self.jar = java, jar
        self.map_name = map_name
        self.game_port = game_port
        self.js_timeout = js_timeout
        self.started = time.time()
        self.lines: deque[tuple[int, str]] = deque(maxlen=8000)
        self.seq = 0
        self._cv = threading.Condition()
        self._lock = threading.RLock()      # 串行化 console/js
        self.proc: subprocess.Popen | None = None
        self.eof = False
        self.players_peak = 0
        self._logf = None
        self.mirror_feed: str | None = None   # 状态镜推送文件 (mlogsim/脚本往里写 JSON)
        self._mirror_started = False
        os.makedirs(os.path.join(DATA, "config", "logs"), exist_ok=True)
        os.makedirs(os.path.join(DATA, "config", "saves"), exist_ok=True)
        os.makedirs(WORLD, exist_ok=True)
        self._spawn()
        self._boot(host=host, paused=paused, server_name=server_name)

    # ---- 进程 -------------------------------------------------------
    def _spawn(self):
        self._logf = open(LOG, "a", encoding="utf-8", buffering=1)
        self._logf.write("\n===== %s  %s =====\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), self.jar))
        self.proc = subprocess.Popen(
            [self.java, "-Dstdout.encoding=UTF-8", "-Dstderr.encoding=UTF-8", "-jar", self.jar],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            cwd=DATA, text=True, encoding="utf-8", errors="replace", bufsize=1,
        )
        self._job = _win_kill_with_parent(self.proc)
        threading.Thread(target=self._pump, daemon=True).start()

    def _pump(self):
        assert self.proc and self.proc.stdout
        for raw in self.proc.stdout:
            line = raw.rstrip("\r\n")
            with self._cv:
                self.seq += 1
                self.lines.append((self.seq, line))
                self._cv.notify_all()
            try:
                self._logf.write(line + "\n")
            except Exception:
                pass
        self.eof = True
        with self._cv:
            self._cv.notify_all()

    def send(self, cmd: str):
        assert self.proc and self.proc.stdin
        self.proc.stdin.write(cmd + "\n")
        self.proc.stdin.flush()

    def wait_for(self, needle: str, timeout: float) -> list[str]:
        raise NotImplementedError

    # ---- 控制 -------------------------------------------------------
    def console(self, cmd: str, quiet: float = 0.30, timeout: float = 8.0) -> dict:
        """发一条控制台命令, 收集它在 stdout 上的输出."""
        with self._lock:
            t0 = time.time()
            seq0 = self.seq
            self.send(cmd)
            buf = self._collect(seq0, quiet, timeout)
            return {"ok": True, "cmd": cmd, "lines": buf, "ms": round((time.time() - t0) * 1000)}

    def _collect(self, seq0: int, quiet: float, timeout: float) -> list[str]:
        out, last_change, last_seq = [], time.time(), seq0
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._cv:
                self._cv.wait(0.05)
                new = [ln for (s, ln) in self.lines if s > last_seq]
                if new:
                    last_seq = self.lines[-1][0]
            if new:
                out.extend(new)
                last_change = time.time()
            elif out and (time.time() - last_change) >= quiet:
                break
            elif self.eof:
                break
        return out

    # ---- js ---------------------------------------------------------
    def js(self, body: str, timeout: float | None = None) -> list[str]:
        """执行一段 JS, 返回它追加进 sb 的行 (文件通道)."""
        timeout = timeout or self.js_timeout
        tok = uuid.uuid4().hex[:12]
        res = "res-%s.txt" % tok
        path = os.path.join(DATA, res)
        script = (
            "var sb = new java.lang.StringBuilder();"
            " try { (function(){ " + " ".join(body.splitlines()) + " })(); }"
            " catch (e) { sb.append('ERR\t' + e); }"
            " var __w = new java.io.PrintWriter('%s', 'UTF-8');"
            " __w.print(sb.toString()); __w.close();" % res
        )
        with self._lock:
            seq0 = self.seq
            self.send("js " + " ".join(script.splitlines()))
            deadline = time.time() + timeout
            while time.time() < deadline:
                if os.path.exists(path):
                    for _ in range(20):     # 写完 -> 可读, 极少需要重试
                        try:
                            with open(path, "r", encoding="utf-8") as f:
                                text = f.read()
                            break
                        except Exception:
                            time.sleep(0.02)
                    else:
                        text = ""
                    try:
                        os.remove(path)
                    except Exception:
                        pass
                    if text.startswith("ERR\t") and "\n" not in text:
                        raise RuntimeError(text[4:])
                    return text.splitlines()
                time.sleep(0.02)
            with self._cv:
                tail = [ln for (s, ln) in self.lines if s > seq0][-12:]
        raise RuntimeError("js 超时 (%.0fs): %s" % (timeout, " | ".join(tail)))

    # ---- 文件通道 (避免把任意文本塞进 JS 字符串) ----------------------
    def put_file(self, text: str, prefix: str = "in") -> str:
        name = "%s-%s.txt" % (prefix, uuid.uuid4().hex[:12])
        with open(os.path.join(DATA, name), "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        return name

    def take_file(self, name: str, timeout: float = 10.0) -> str:
        path = os.path.join(DATA, name)
        deadline = time.time() + timeout
        while time.time() < deadline:
            if os.path.exists(path):
                for _ in range(50):
                    try:
                        with open(path, "r", encoding="utf-8") as fh:
                            text = fh.read()
                        try:
                            os.remove(path)
                        except Exception:
                            pass
                        return text
                    except Exception:
                        time.sleep(0.02)
            time.sleep(0.02)
        raise RuntimeError("读不到 JS 输出文件 %s" % name)

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
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._cv:
                self._cv.wait(0.05)
                hit = [ln for (_, ln) in self.lines if needle in ln]
            if hit:
                return hit
            if self.eof:
                raise SystemExit("服务端提前退出, 见 " + LOG)
        raise SystemExit("等 %.0fs 没等到 %r, 见 %s" % (timeout, needle, LOG))

    # ---- 结束 -------------------------------------------------------
    def close(self, force: bool = False):
        try:
            if self.proc and self.proc.poll() is None:
                if not force:
                    try:
                        self.send("exit")
                    except Exception:
                        pass
                    for _ in range(60):
                        if self.proc.poll() is not None:
                            break
                        time.sleep(0.05)
                if self.proc.poll() is None:
                    self.proc.kill()
        except Exception:
            pass
        try:
            self._logf.close()
        except Exception:
            pass


# ---- JS 转储 ---------------------------------------------------------
def switch_map(w, target: str, audit) -> dict:
    """换图但不踢人: nextmap 只登记下一张图, gameover 触发 loadMap;
    NetServer 的连接表不动, 客户端自己重载新地图。"""
    before = None
    try:
        before = float((w.js("sb.append(Vars.state.tick);") or ["0"])[0])
    except Exception:
        pass
    audit("switch", map=target)
    out1 = w.console("nextmap " + target, quiet=0.4, timeout=15)
    out2 = w.console("gameover", quiet=0.6, timeout=30)
    deadline = time.time() + 45
    loaded = False
    while time.time() < deadline:
        time.sleep(0.5)
        try:
            tick = float((w.js("sb.append(Vars.state.tick);") or ["0"])[0])
        except Exception:
            continue
        if before is None or tick < before:
            loaded = True
            break
    if not loaded:
        return {"ok": False, "error": "map did not reload",
                "nextmap": out1.get("lines"), "gameover": out2.get("lines")}
    try:
        w.js("var r=Vars.state.rules; r.waves=false; r.infiniteResources=true; "
             "r.canGameOver=false; r.logicUnitControl=true; sb.append(r.waves);")
    except Exception:
        pass
    try:
        w.map_name = w.js("sb.append(Vars.state.map.name());")[0]
    except Exception:
        w.map_name = target
    st = w.js(STATUS_JS)
    players = next((ln.split("=", 1)[1] for ln in st if ln.startswith("players=")), None)
    return {"ok": True, "map": w.map_name, "players": coerce(players)}


STATUS_JS = r"""
var put=function(k,v){ sb.append(k).append('=').append(v).append('\n'); };
put('map', Vars.state.map.name());
put('mode', Vars.state.rules.mode().name());
put('wave', Vars.state.wave);
put('tick', Vars.state.tick);
put('w', Vars.world.width());
put('h', Vars.world.height());
put('players', Packages.mindustry.gen.Groups.player.size());
put('units', Packages.mindustry.gen.Groups.unit.size());
put('builds', Packages.mindustry.gen.Groups.build.size());
try{ put('paused', Vars.state.isPaused()?1:0); }catch(e){ put('paused', '?'); }
try{ put('infinite', Vars.state.rules.infiniteResources?1:0); }catch(e){ put('infinite', '?'); }
try{ put('waveIn', Math.round(Vars.state.wavetime/60)); }catch(e){ put('waveIn', '?'); }
"""

PLAYERS_JS = r"""
var G=Packages.mindustry.gen.Groups.player;
for(var i=0;i<G.size();i++){
  var p=G.index(i); if(p==null) continue;
  sb.append(p.name).append('\t').append(p.team.name).append('\t')
    .append(Math.round(p.x/8)).append('\t').append(Math.round(p.y/8)).append('\t')
    .append(p.admin?'1':'0').append('\n');
}
"""

UNITS_JS = r"""
var G=Packages.mindustry.gen.Groups.unit, n=0, lim=%(limit)d, R=%(R)f, CX=%(CX)f, CY=%(CY)f;
var TF=%(team)s, YF=%(type)s;
for(var i=0;i<G.size();i++){
  var u=G.index(i); if(u==null||!u.isValid()) continue;
  if(TF!=null && u.team.name!=TF) continue;
  if(YF!=null && u.type.name!=YF) continue;
  if(R>0){ var dx=u.x/8-CX, dy=u.y/8-CY; if(dx*dx+dy*dy>R*R) continue; }
  var ctl='-'; try{ var c=u.controller(); if(c!=null) ctl=c.getClass().getSimpleName(); }catch(e){ ctl='?'; }
  var dead='?'; try{ dead = u.dead?1:0; }catch(e){ try{ dead = u.dead()?1:0; }catch(e2){} }
  var item='-', carry=-1, capu=-1, elev=-1, ctlTick=-1, flag=0, ctrl=-1, mine=0, boost=0;
  try{ item = u.stack.item==null ? '-' : u.stack.item.name; carry = u.stack.amount; }catch(e){}
  try{ capu = u.type.itemCapacity; }catch(e){}
  try{ elev = Math.round(u.elevation*100)/100; }catch(e){}
  try{ var cc = u.controller(); if(cc instanceof Packages.mindustry.ai.types.LogicAI) ctlTick = cc.controlTimer; }catch(e){}
  try{ flag = u.flag; }catch(e){}
  try{ ctrl = u.sense(Packages.mindustry.logic.LAccess.controlled); }catch(e){}
  try{ mine = u.mineTile==null ? 0 : 1; }catch(e){}
  try{ boost = (u.type.canBoost && u.elevation > 0.09) ? 1 : 0; }catch(e){}
  sb.append(u.id).append('\t').append(u.type.name).append('\t').append(u.team.name).append('\t')
    .append(Math.round(u.x/8)).append('\t').append(Math.round(u.y/8)).append('\t')
    .append(Math.round(u.health)).append('\t').append(Math.round(u.type.health)).append('\t')
    .append(dead).append('\t').append(ctl).append('\t')
    .append(item).append('\t').append(carry).append('\t').append(capu).append('\t')
    .append(elev).append('\t').append(ctlTick).append('\t')
    .append(flag).append('\t').append(ctrl).append('\t').append(mine).append('\t').append(boost).append('\n');
  if(++n>=lim) break;
}
if(n>=lim) sb.append('TRUNC\t').append(lim).append('\n');
"""


UNIT_JS = r"""
var u = Packages.mindustry.gen.Groups.unit.getByID(%(id)d);
if(u==null || !u.isValid()){ sb.append('ERR\tno unit id %(id)d'); }
else {
  var put=function(k,v){ sb.append(k).append('=').append(v).append('\n'); };
  put('id', u.id); put('type', u.type.name); put('team', u.team.name);
  put('tx', Math.round(u.x/8)); put('ty', Math.round(u.y/8));
  put('wx', Math.round(u.x*10)/10); put('wy', Math.round(u.y*10)/10);
  put('health', Math.round(u.health)); put('maxHealth', Math.round(u.type.health));
  put('dead', u.dead?1:0);
  try{ var c=u.controller(); put('controller', c==null?'-':c.getClass().getSimpleName()); }catch(e){ put('controller','?'); }
  try{ put('flag', u.flag); }catch(e){ put('flag','?'); }
  try{ put('controlled', u.sense(Packages.mindustry.logic.LAccess.controlled)); }catch(e){ put('controlled','?'); }
  try{ put('item', u.stack.item==null?'-':u.stack.item.name); put('carry', u.stack.amount); }catch(e){}
  try{ put('itemCapacity', u.type.itemCapacity); }catch(e){}
  try{ put('elevation', Math.round(u.elevation*100)/100); }catch(e){}
  try{ put('boosting', (u.type.canBoost && u.elevation>0.09)?1:0); }catch(e){}
  try{ put('mining', u.mineTile==null?0:1); if(u.mineTile!=null){ put('mineTile', u.mineTile.x+','+u.mineTile.y); } }catch(e){}
  try{ put('shooting', u.isShooting?1:0); }catch(e){}
  try{ put('speed', Math.round(u.speed()*100)/100); }catch(e){}
  try{ var cc=u.controller(); if(cc instanceof Packages.mindustry.ai.types.LogicAI){ put('controlTimer', cc.controlTimer); } }catch(e){}
  try{ put('rangeTiles', Math.round(u.range()/8*10)/10); }catch(e){}
}
"""


EV_INSTALL_JS = r"""
if(typeof _evlog === 'undefined'){
  _evlog = []; _evseq = 0; _mineHits = []; _mineIgnore = null;
  /* 管理员在游戏里打 /push <文本> = 直接把话插给 agent(队列由 Python 侧取走) */
  _pushlog = [];
  /* 玩家拆掉脉冲地雷 = 结束投影. _mineGone 收所有被清空的格子, 由导演挑出圆心那颗 */
  _mineGone = []; _mineIgnoreAir = null;
  var Cons = Packages.arc.func.Cons;
  /* 注意: 嵌套类必须写成完整的 Packages...EventType$Xxx, 不能拿 ET 再做字符串拼接 */
  var EV_TILE = Packages.mindustry.game.EventType$TileChangeEvent;
  var EV_CONF = Packages.mindustry.game.EventType$ConfigEvent;
  var push = function(kind, t, blockName, teamName, extra){
    _evseq++;
    _evlog.push(kind+'\t'+_evseq+'\t'+Vars.state.tick+'\t'+t.x+'\t'+t.y+'\t'
      +blockName+'\t'+teamName+'\t'+extra);
    /* 环形缓冲: 只留最近 500 条 */
    if(_evlog.length > 500) _evlog.shift();
  };
  Packages.arc.Events.on(EV_TILE, new JavaAdapter(Cons, {get: function(e){
    try{
      var t = e.tile;
      if(t == null) return;
      var b = t.block();
      var sz = 0; try{ sz = b.size; }catch(e2){}
      /* 多格方块落地时, 非原点格会各报一条 air, 靠 size 在 Python 侧消掉 */
      push(b.name=='air' ? 'B' : 'P', t, b.name, t.team().name, 'size='+sz);
      /* 玩家放下脉冲地雷 = 请求投影; _mineIgnore 用来吞掉服务端自己钉回去的那一颗 */
      try{
        if(b.name == %(mineblock)s){
          var mk = t.x + ',' + t.y;
          if(_mineIgnore == mk){ _mineIgnore = null; }
          else { _mineHits.push(mk); }
        }else if(b.name == 'air'){
          /* 拆雷 = 结束. 场景 clear 会先抹掉地雷再钉回来, 那一格由 _mineIgnoreAir 吞掉 */
          var ak = t.x + ',' + t.y;
          if(_mineIgnoreAir == ak){ _mineIgnoreAir = null; }
          else {
            _mineGone.push(ak);
            if(_mineGone.length > 200) _mineGone.shift();
          }
        }
      }catch(e6){}
    }catch(err){}
  }}));
  Packages.arc.Events.on(EV_CONF, new JavaAdapter(Cons, {get: function(e){
    try{
      var b = e.tile; if(b == null) return;
      push('C', b.tile, b.block.name, b.team.name, (e.value==null?'':String(e.value)));
    }catch(err){}
  }}));
  sb.append('installed');
  /* 玩家聊天: 服务端 PlayerChatEvent(player, message), 记到 _chatlog + chat.log */
  try{
    if(typeof _chatlog === 'undefined'){
      _chatlog = []; _chatseq = 0;
      var EV_CHAT = Packages.mindustry.game.EventType$PlayerChatEvent;
      var CHATLOG_PATH = %(chatlog)s;
      Packages.arc.Events.on(EV_CHAT, new JavaAdapter(Cons, {get: function(e){
        try{
          var nm = '?'; try{ nm = e.player.name; }catch(e3){}
          var msg = e.message == null ? '' : String(e.message);
          _chatseq++;
          _chatlog.push(_chatseq + '\t' + Vars.state.tick + '\t' + nm + '\t' + msg);
          if(_chatlog.length > 300) _chatlog.shift();
          try{
            var fw = new java.io.PrintWriter(new java.io.FileWriter(CHATLOG_PATH, true));
            fw.println('[' + Math.floor(Vars.state.tick) + '] ' + nm + ': ' + msg); fw.close();
          }catch(e4){}
          /* /push <文本> = 管理员往 agent 会话插一句话. 不是管理员就回绝并说明. */
          try{
            var low = msg.toLowerCase();
            if(low.indexOf('/push ') == 0 || low.indexOf('!push ') == 0){
              var body = msg.substring(6).replace(/^\s+/, '');
              var adm = false; try{ adm = e.player != null && e.player.admin; }catch(e7){}
              var plain = nm; try{ plain = e.player.plainName(); }catch(e8){}
              if(!adm){
                try{ e.player.sendMessage('[scarlet]只有管理员能用 /push[]. 让主机在控制台打: admin ' + plain); }catch(e9){}
              }else if(body.length > 0){
                _pushlog.push(JSON.stringify({tick: Math.floor(Vars.state.tick), player: String(plain), message: body}));
                if(_pushlog.length > 50) _pushlog.shift();
                try{
                  var pw2 = new java.io.PrintWriter(new java.io.FileWriter(%(pushfile)s, true));
                  pw2.println(JSON.stringify({tick: Math.floor(Vars.state.tick), player: String(plain), message: body}));
                  pw2.close();
                }catch(pe){}
                try{ e.player.sendMessage('[accent][agent][] 收到 /push(' + body.length + ' 字), 已转交给会话'); }catch(pa){}
              }
            }
          }catch(ea){}
        }catch(err){}
      }}));
      sb.append(' chat=1');
    }
  }catch(e5){ sb.append(' chat=ERR:' + e5); }

  /* 调试世界: 进来的玩家自动给 admin, 这样他才能在聊天栏用 /push 跟 agent 说话.
     (真正的线上服不该这样; 用 --no-push-admin 关掉) */
  try{
    if(%(autoadmin)d){
      var EV_JOIN = Packages.mindustry.game.EventType$PlayerJoinEvent;
      Packages.arc.Events.on(EV_JOIN, new JavaAdapter(Cons, {get: function(e){
        try{ if(e.player != null) e.player.admin = true; }catch(ej){}
      }}));
      try{ Packages.mindustry.gen.Groups.player.each(function(p){ try{ p.admin = true; }catch(ep){} }); }catch(ep2){}
      sb.append(' admin=1');
    }
  }catch(ea0){}
  /* 点击门: 玩家点一下地雷/任意方块, 就把他的视角/操作带进沙盘 */
  try{
    if(typeof _doors === 'undefined'){
      _doors = {}; _doorjs = {}; _taplog = []; _tapseq = 0; _ret = {}; _doorHits = [];
      var EV_TAP = Packages.mindustry.game.EventType$TapEvent;
      Packages.arc.Events.on(EV_TAP, new JavaAdapter(Cons, {get: function(e){
        try{
          var t = e.tile; if(t == null) return;
          var np = '-'; try{ np = (e.player == null ? '-' : e.player.name); }catch(e1){}
          _tapseq++;
          _taplog.push(_tapseq + '\t' + Math.floor(Vars.state.tick) + '\t' + t.x + '\t' + t.y + '\t' + np);
          if(_taplog.length > 200) _taplog.shift();
          _doorAct(e.player, t.x, t.y);
        }catch(err){}
      }}));
      sb.append(' tap=1');
    }
  }catch(e6){ sb.append(' tap=ERR:' + e6); }
} else {
  sb.append('already');
}
"""


DOOR_ACT_JS = r"""
/* 门的动作本体. 由 TapEvent 监听调用, 也供 door_enter 直接触发(没有玩家时也能测) */
/* 注意: 这里必须用隐式全局赋值, 不能写 var —— Java 侧每次 eval 是独立作用域,
   var 声明的名字出不了这次调用(实测 typeof _doorAct == 'undefined') */
_doorAct = function(pl, dx, dy){
  var d = _doors[dx + ',' + dy];
  if(d == null) return 'nodoor';
  /* 场景先铺: 即使没有玩家(合成点击/自测)也让世界变成"那个世界" */
  if(d.scene != null){
    try{ eval(_doorjs[dx + ',' + dy]); _doorerr = 'ok'; }catch(e7){ _doorerr = String(e7); }
  }
  /* 只有一种门: watch. 点一下 = 打开这扇门后面的仿真投影.
     开局投影本身(读 feed 文件)是 Python 侧的后台线程, 这里只留一个"被点了"的凭据,
     由 projection_director 取走 —— Java 侧不能回调 Python. */
  if(d.kind == 'watch'){
    _doorHits.push(dx + ',' + dy);
    return 'watch';
  }
  return 'noop';
};
"""


MK_INSTALL_JS = r"""
/* 标记镜: 世界标记 (ObjectiveMarker) 由服务端直接下发, 客户端渲染.
   实测结论(2026-11-16, v160.7 真机):
   - Call.createMarker(int id, ObjectiveMarker) / removeMarker(int) /
     updateMarker(int id, LMarkerControl, double a, double b, double c) / updateMarkerTexture(int, Object)
   - 贴图版必须是 TextureMarker + Call.updateMarkerTexture(id, "<兵种>-full") —— 就是 mlog 的
     "makemarker texture 1 x y true" + "setmarker texture 1 0 @poly 0" 这两步; 先建空 marker 再填贴图.
     把 texture 直接塞进创建包会渲染成白模, 字符串 "poly" 也不行, 必须 "poly-full" 这个全尺寸精灵名.
   - width/height=0 表示用精灵原尺寸; world/minimap/light 是引擎自动分配的层号(不是布尔),
     传 1 会被改写成下一个空层号, 传 -1 表示该层不画.
   - 逐帧钩子只能 Events.run(Trigger.update, new java.lang.Runnable({...})).
   所有状态挂隐式全局 (var 出不了单次 js 调用). */
if(typeof _mk === 'undefined'){
  _mk = {on: false, div: 2, frame: 0, next: 2000, slots: {}, spr: {}, col: {}, tag: {}, txt: {},
         labels: true, size: 16, tint: true};
  _mkT = Packages.mindustry.game.MapObjectives$TextureMarker;
  _mkTH = Packages.mindustry.game.MapObjectives$TextureHolder;
  _mkV = Packages.arc.math.geom.Vec2;
  _mkC = Packages.arc.graphics.Color;
  _mkCall = Packages.mindustry.gen.Call;
  _mkLC = Packages.mindustry.logic.LMarkerControl;
  /* 单位贴图名: 就用纯兵种名. updateMarkerTexture 会把它解析成内容对象,
     客户端画的是该 UnitType 的 full icon; 写成 "<type>-full" 会变成缺图(ohno). */
  _mkSprite = function(u){ return String(u.type.name); };
  /* 新建一只单位的图标 marker: 先建空贴图 marker, 再 updateMarkerTexture 填精灵 */
  _mkIcon = function(mid, x, y, sprite, w, tint){
    var tm = new _mkT();
    tm.pos = new _mkV(x, y);
    tm.texture = new _mkTH();
    tm.width = (w == null ? 0 : w); tm.height = (w == null ? 0 : w);
    tm.rotation = 0; tm.autoscale = false;
    if(tint != null && _mk.tint){ tm.color = new _mkC(tint[0], tint[1], tint[2], 1); }
    tm.world = 1; tm.minimap = -1; tm.light = -1;
    _mkCall.createMarker(mid, tm);
    /* 贴图字段存"内容对象"(UnitType), 和 vanilla 的 setmarker @poly 存的是同一个类型;
       传字符串也能显示, 但内容对象是引擎原生路径, 换兵种/换图标都靠它 */
    var c = null; try{ c = Vars.content.unit(sprite); }catch(e0){}
    _mkCall.updateMarkerTexture(mid, c == null ? sprite : c);
  };
  _mkText = function(mid, x, y, text, size){
    var t = new Packages.mindustry.game.MapObjectives$TextMarker();
    t.pos = new _mkV(x, y);
    t.text = text; t.fontSize = (size == null ? 1.2 : size);
    t.flags = 0; t.textAlign = 0; t.lineAlign = 0;
    t.world = 1; t.minimap = -1; t.light = -1;
    _mkCall.createMarker(mid, t);
  };
  _mkUnitColor = function(ctrl){
    if(ctrl == 1) return [0.35, 1, 1];
    if(ctrl == 2) return [1, 0.9, 0.45];
    return [1, 1, 1];
  };
  _mkTick = function(){
    if(!_mk.on) return;
    if((_mk.frame++ % _mk.div) != 0) return;
    var seen = {}, arr = Packages.mindustry.gen.Groups.unit;
    for(var i=0;i<arr.size();i++){
      var u = arr.index(i);
      if(u == null || u.dead) continue;
      var uid = u.id; seen[uid] = 1;
      var ctrl = 0, c = u.controller();
      if(c != null){
        var cn = String(c.getClass().getName());
        if(cn.indexOf('Player') >= 0) ctrl = 2;
        else if(cn.indexOf('LogicAI') >= 0) ctrl = 1;
      }
      var amt = 0; try{ if(u.stack != null) amt = u.stack.amount; }catch(e1){}
      var spr = _mkSprite(u);
      var mid = _mk.slots[uid];
      if(mid == null){
        mid = _mk.next++; _mk.slots[uid] = mid; _mk.col[uid] = ctrl; _mk.spr[uid] = spr;
        _mkIcon(mid, u.x, u.y, spr, _mk.size, _mkUnitColor(ctrl));
      } else {
        _mkCall.updateMarker(mid, _mkLC.pos, u.x, u.y, 0);
        if(_mk.spr[uid] != spr){
          _mk.spr[uid] = spr;
          try{ _mkCall.updateMarkerTexture(mid, spr); }catch(e2){}
        }
        if(_mk.col[uid] != ctrl){
          _mk.col[uid] = ctrl;
          var cc = _mkUnitColor(ctrl);
          _mkCall.updateMarker(mid, _mkLC.color, cc[0], cc[1], cc[2]);
        }
      }
      if(_mk.labels){
        var tag = String(u.type.name) + (amt > 0 ? (' x' + amt) : '');
        var tid = _mk.tag[uid];
        if(tid == null || _mk.txt[uid] != tag){
          if(tid != null){ try{ _mkCall.removeMarker(tid); }catch(e3){} }
          tid = mid + 5000; _mk.tag[uid] = tid; _mk.txt[uid] = tag;
          _mkText(tid, u.x, u.y + 9, tag, 1.1);
        } else {
          _mkCall.updateMarker(tid, _mkLC.pos, u.x, u.y + 9, 0);
        }
      }
    }
    for(var k in _mk.slots){
      if(!_mk.slots.hasOwnProperty(k)) continue;
      if(seen[k] != 1){
        try{ _mkCall.removeMarker(_mk.slots[k]); }catch(e4){}
        if(_mk.tag[k] != null){ try{ _mkCall.removeMarker(_mk.tag[k]); }catch(e5){} }
        delete _mk.slots[k]; delete _mk.col[k]; delete _mk.spr[k];
        delete _mk.tag[k]; delete _mk.txt[k];
      }
    }
  };
  /* 钩子经一层间接, 以后热替换 _mkTick 不用重装监听 */
  Packages.arc.Events.run(Packages.mindustry.game.EventType$Trigger.update,
                          new java.lang.Runnable({run: function(){ _mkTick(); }}));
  sb.append('INSTALLED');
} else { sb.append('ALREADY'); }
"""

MK_STATE_JS = r"""
var lit = 0;
for(var k in _mk.slots){ if(_mk.slots.hasOwnProperty(k)) lit++; }
sb.append('on\t').append(_mk.on ? 1 : 0).append('\n');
sb.append('div\t').append(_mk.div).append('\n');
sb.append('units\t').append(Packages.mindustry.gen.Groups.unit.size()).append('\n');
sb.append('markers\t').append(lit).append('\n');
sb.append('worldMarkers\t').append(Vars.state.markers.worldMarkers.size);
"""

MK_ON_JS = r"""
_mk.on = %(on)s;
if(%(div)d > 0) _mk.div = %(div)d;
if(%(size)s > 0 && _mk.size != %(size)s){
  /* 尺寸变了: 已建 marker 没法改贴图大小, 直接清掉重建 */
  for(var k0 in _mk.slots){
    if(!_mk.slots.hasOwnProperty(k0)) continue;
    try{ Packages.mindustry.gen.Call.removeMarker(_mk.slots[k0]); }catch(e6){}
    if(_mk.tag[k0] != null){ try{ Packages.mindustry.gen.Call.removeMarker(_mk.tag[k0]); }catch(e7){} }
    delete _mk.slots[k0]; delete _mk.col[k0]; delete _mk.spr[k0];
    delete _mk.tag[k0]; delete _mk.txt[k0];
  }
  _mk.size = %(size)s;
}
if('%(labels)s' != 'null') _mk.labels = %(labels)s;
if('%(tint)s' != 'null') _mk.tint = %(tint)s;
var lit = 0;
for(var k in _mk.slots){ if(_mk.slots.hasOwnProperty(k)) lit++; }
sb.append('on\t').append(_mk.on ? 1 : 0).append('\n').append('markers\t').append(lit);
sb.append('\n').append('size\t').append(_mk.size).append('\n').append('labels\t').append(_mk.labels ? 1 : 0)
  .append('\n').append('tint\t').append(_mk.tint ? 1 : 0);
"""

MK_CLEAR_JS = r"""
var nc = 0;
for(var k in _mk.slots){
  if(!_mk.slots.hasOwnProperty(k)) continue;
  try{ Packages.mindustry.gen.Call.removeMarker(_mk.slots[k]); }catch(e2){}
  delete _mk.slots[k]; delete _mk.col[k]; nc++;
}
_mk.on = false;
sb.append('CLEARED\t').append(nc);
"""

# 状态镜: 把外部给的坐标表画成 marker, 不读 Groups.unit
# ------------------------------------------------------
# 和 MK_INSTALL_JS(跟随真单位) 的区别: 这里的坐标来自 mlogsim / 脚本 / push 文件,
# 所以可以画"仿真的影子"——单位在真世界里不动也能看到它们在跑.
MS_INSTALL_JS = r"""
/* 每块沙盘一份 marker 空间: 第 sl 号槽占 [6000+sl*400, +400) 的 id 段,
   互不覆盖. 之前所有投影共用 base=6000, 后开始的那块沙盘会把前面那块
   的图标原地改写 —— 看起来就是"marker 冲突". */
if(typeof _ms === 'undefined'){
  _ms = {slots: {}, size: 16, labels: true, span: 400};
  _msSlot = function(sl){
    var k = String(sl | 0);
    if(_ms.slots[k] == null){
      _ms.slots[k] = {base: 6000 + (sl | 0) * _ms.span, n: 0, ids: {}, txt: {}};
    }
    return _ms.slots[k];
  };
  _msCol = function(c){
    if(c == 1) return [0.35, 1, 1];    /* 逻辑控 = 青 */
    if(c == 2) return [1, 0.9, 0.45];  /* 玩家   = 黄 */
    return [1, 1, 1];                  /* 自由   = 白 */
  };
  _msIcon = function(mid, x, y, ty, w, tint, rot){
    var C = Packages.mindustry.gen.Call;
    var tm = new Packages.mindustry.game.MapObjectives$TextureMarker();
    tm.pos = new Packages.arc.math.geom.Vec2(x, y);
    tm.texture = new Packages.mindustry.game.MapObjectives$TextureHolder();
    /* 单位 rotation 0 指向 +x, 而精灵本身"朝上", 所以贴图要减 90 */
    tm.width = w; tm.height = w; tm.rotation = (rot == null ? 0 : rot - 90); tm.autoscale = false;
    if(tint != null) tm.color = new Packages.arc.graphics.Color(tint[0], tint[1], tint[2], 1);
    tm.world = 1; tm.minimap = -1; tm.light = -1;
    try{ C.removeMarker(mid); }catch(e0){}
    C.createMarker(mid, tm);
    /* 贴图值必须是内容对象(UnitType): 与 vanilla 的 setmarker texture 存的是同一类型;
       字符串也能显示, 但换兵种/换图标全靠这个对象 */
    var c = null; try{ c = Vars.content.unit(ty); }catch(e1){}
    C.updateMarkerTexture(mid, c == null ? ty : c);
  };
  _msText = function(tid, x, y, s, sz){
    var C = Packages.mindustry.gen.Call;
    var t = new Packages.mindustry.game.MapObjectives$TextMarker();
    t.pos = new Packages.arc.math.geom.Vec2(x, y); t.text = s; t.fontSize = sz;
    /* Align 是位掩码: center=1 top=2 bottom=4 left=8 right=16; 单位头顶那行居中 */
    t.flags = 0; t.textAlign = 1; t.lineAlign = 2;
    t.world = 1; t.minimap = -1; t.light = -1;
    try{ C.removeMarker(tid); }catch(e2){}
    C.createMarker(tid, t);
  };
  /* txt = JSON: [{"type":"poly","x":464,"y":544,"amount":30,"ctrl":1}, ...]
     x/y 是**世界坐标**; 想按格给就写 tx/ty, 这里乘 8 */
  _msApply = function(sl, txt){
    var C = Packages.mindustry.gen.Call;
    var LC = Packages.mindustry.logic.LMarkerControl;
    var S = _msSlot(sl);
    var arr = JSON.parse(String(txt));
    var n = arr.length;
    for(var i = 0; i < n; i++){
      var e = arr[i], ctrl = e.ctrl | 0, col = _msCol(ctrl);
      /* 坐标一律按格给(tiles). 注意两条通道量纲不同:
         createMarker 直接写 pos 字段 -> 世界单位;
         updateMarker(pos) 走 PosMarker.control -> 内部 *tilesize, 所以要给格 */
      var gx = (e.x != null ? e.x : e.tx), gy = (e.y != null ? e.y : e.ty);
      var x = gx * 8, y = gy * 8;
      var ty = String(e.type), mid = S.base + i * 2, tid = mid + 1;
      var prev = S.ids[i];
      var rot = (e.rot == null ? null : e.rot);
      if(prev == null || prev.ty != ty || prev.size != _ms.size || prev.ctrl != ctrl){
        _msIcon(mid, x, y, ty, _ms.size, col, rot);
        S.ids[i] = {ty: ty, size: _ms.size, ctrl: ctrl, rot: rot};
      }else{
        C.updateMarker(mid, LC.pos, gx, gy, 0);
        /* 朝向要在已有 marker 上改: rotation 走 control(), 单位是度, 不乘 tilesize */
        if(rot != null && prev.rot != rot){
          C.updateMarker(mid, LC.rotation, rot - 90, 0, 0);
          prev.rot = rot;
        }
      }
      if(_ms.labels){
        /* 头顶那行: 兵种 + 携带的物品名 + 数量, 例如 "poly copper x12" */
        var s = ty + (e.item ? (' ' + e.item) : '') + ((e.amount | 0) > 0 ? (' x' + (e.amount | 0)) : '');
        var pt = S.txt[i];
        if(pt == null || pt.s != s){ _msText(tid, x, y + 14, s, 1.1); S.txt[i] = {s: s}; }
        else{ C.updateMarker(tid, LC.pos, gx, gy + 1.75, 0); }
      }
    }
    for(var j = n; j < S.n; j++){
      try{ C.removeMarker(S.base + j * 2); }catch(e3){}
      try{ C.removeMarker(S.base + j * 2 + 1); }catch(e4){}
      delete S.ids[j]; delete S.txt[j];
    }
    S.n = n;
    return n;
  };
  sb.append('MSINSTALLED');
}else{
  /* 已经在跑: 兼容旧结构(没有 slots 的), 补上就行 */
  if(_ms.slots == null){ _ms.slots = {}; _ms.span = 400; }
  sb.append('MSALREADY');
}
"""

MS_APPLY_JS = r"""
var txt = new java.lang.String(Packages.java.util.Base64.getDecoder().decode('%(b64)s'), 'UTF-8');
sb.append(_msApply(%(slot)d, String(txt)));
"""

MS_CLEAR_JS = r"""
/* 清掉某个槽(或全部)的状态镜 marker(图标 + 头顶文字).
   按固定窗口扫, 不只按 n: 守护进程重启过 / 上一步崩在半路时,
   n 可能是 0 而屏幕上还留着上一次的图标(实测踩过).
   槽之间 id 段不重叠, 所以清一块沙盘不会碰别的沙盘. */
var C = Packages.mindustry.gen.Call;
var want = %(slot)s, gone = 0;
var ks = [];
if(want == null){ for(var k0 in _ms.slots){ if(_ms.slots.hasOwnProperty(k0)){ ks.push(k0); } } }
else { ks.push(String(want)); }
for(var ki = 0; ki < ks.length; ki++){
  var S2 = _ms.slots[ks[ki]];
  if(S2 == null){ continue; }
  var lim = (S2.n > 64 ? S2.n : 64);
  for(var i = 0; i < lim; i++){
    try{ C.removeMarker(S2.base + i * 2); gone++; }catch(e0){}
    try{ C.removeMarker(S2.base + i * 2 + 1); }catch(e1){}
  }
  S2.n = 0; S2.ids = {}; S2.txt = {};
  delete _ms.slots[ks[ki]];
}
sb.append(gone);
"""

SB_INSTALL_JS = r"""
/* 每块沙盘一块"文本日志板": 在格子左上角列几行 TextMarker.
   内容由 Python 侧每轮轮询重写(标题 / feed 新鲜度 / 投影状态 / 建筑数 / 单位数 /
   最近几条事件), 所以世界里能直接看到调用日志, 不用切回聊天栏.
   id 段是 [5000, 6000), 与状态镜的 6000 段、边界框的 7000 段都不重叠. */
if(typeof _sb === 'undefined'){
  _sb = {next: 5000, span: 8, slots: {}};
  /* 上一进程画的板子还留在客户端: 先擦掉, 免得对齐方式/行距改了还显示老样式 */
  for(var _sk = 5000; _sk < 6000; _sk++){ try{ Packages.mindustry.gen.Call.removeMarker(_sk); }catch(_se){} }
  _sbSlot = function(sl){
    var k = String(sl | 0);
    if(_sb.slots[k] == null){ _sb.slots[k] = {base: 5000 + (sl | 0) * _sb.span}; }
    return _sb.slots[k];
  };
  _sbLine = function(sl, i, gx, gy, s, sz){
    var C = Packages.mindustry.gen.Call;
    var LC = Packages.mindustry.logic.LMarkerControl;
    var S = _sbSlot(sl), id = S.base + i, m = null;
    try{ m = Vars.state.markers.get(id); }catch(e0){}
    if(m == null){
      var t = new Packages.mindustry.game.MapObjectives$TextMarker();
      t.pos = new Packages.arc.math.geom.Vec2(gx * 8, gy * 8);
      /* Align 位掩码: left=8, top=2 —— 面板每行从锚点往右写、往下排 */
      t.text = s; t.fontSize = sz; t.flags = 0; t.textAlign = 8; t.lineAlign = 2;
      t.world = 1; t.minimap = -1; t.light = -1;
      C.createMarker(id, t);
    }else{
      /* 已有 marker: pos 走 control() 是格; 文字只能走 updateMarkerText
         (LMarkerControl 里没有 text, 改文字用 flushText) */
      C.updateMarker(id, LC.pos, gx, gy, 0);
      C.updateMarker(id, LC.fontSize, sz, 0, 0);
      C.updateMarkerText(id, LC.flushText, true, s);
    }
  };
  _sbSet = function(sl, gx, gy, txt, sz){
    var arr = JSON.parse(String(txt)), i;
    for(i = 0; i < arr.length && i < 8; i++){
      _sbLine(sl, i, gx, gy - i * 0.95, String(arr[i]), sz);
    }
    var S = _sbSlot(sl);
    for(i = arr.length; i < 8; i++){
      try{ Packages.mindustry.gen.Call.removeMarker(S.base + i); }catch(e1){}
    }
    return arr.length;
  };
  /* 从文件读面板文本再刷: 控制台的 js 行会把参数里的字符串字面量弄坏,
     所以文本一律走文件(DATA/sb<slot>.txt = java cwd), 只传数字. */
  _sbSetF = function(sl, gx, gy, sz){
    var p = Packages.java.nio.file.Path.of('sb' + (sl | 0) + '.txt');
    var t = String(Packages.java.nio.file.Files.readString(p));
    return _sbSet(sl, gx, gy, t, sz);
  };
  sb.append('SBINSTALLED');
}else{
  sb.append('SBALREADY');
}
"""

# 文本先由 Python 写进 DATA/sb<slot>.txt, 这里只传数字:
# 控制台 js 行会破坏参数里的字符串字面量(SyntaxError: Unexpected token).
SB_SET_JS = r"""
sb.append(_sbSetF(%(slot)d, %(gx)f, %(gy)f, %(sz)f));
"""

SB_SWEEP_JS = r"""
/* 重启后 _sb 是空的, 客户端屏幕上还留着上次进程画的日志板 -> 先把整段清掉 */
var C = Packages.mindustry.gen.Call, gone = 0;
for(var i = 5000; i < 6000; i++){ try{ C.removeMarker(i); gone++; }catch(e0){} }
_sb = {next: 5000, span: 8, slots: {}};
sb.append(gone);
"""


# 手放一个标记: 点或文字. text 非空时用 TextMarker(点标记 + 一行字)
MK_ADD_JS = r"""
var kind = %(kind)s, mx = %(x)f, my = %(y)f, mid = %(id)d;
var mm = Vars.state.markers;
var had = mm.has(mid);
if(had){ try{ Packages.mindustry.gen.Call.removeMarker(mid); }catch(e0){} }
if(kind == 'text'){
  var tm = new Packages.mindustry.game.MapObjectives$TextMarker();
  tm.pos = new Packages.arc.math.geom.Vec2(mx, my);
  tm.text = %(text)s;
  tm.fontSize = %(size)f;
  tm.flags = 0; tm.textAlign = 0; tm.lineAlign = 0;
  tm.world = 1; tm.minimap = 1; tm.light = -1;
  Packages.mindustry.gen.Call.createMarker(mid, tm);
} else if(kind == 'shape'){
  var sm = new Packages.mindustry.game.MapObjectives$ShapeMarker();
  sm.pos = new Packages.arc.math.geom.Vec2(mx, my);
  sm.color = new Packages.arc.graphics.Color(%(r)f, %(g)f, %(b)f, 1);
  sm.radius = %(radius)f; sm.stroke = %(stroke)f;
  sm.rotation = 0; sm.startAngle = 0; sm.endAngle = 360;
  sm.fill = false; sm.outline = true; sm.sides = 4;
  sm.world = 1; sm.minimap = 1; sm.light = -1;
  Packages.mindustry.gen.Call.createMarker(mid, sm);
} else {
  _mkPoint(mid, mx, my, %(r)f, %(g)f, %(b)f, %(radius)f, 1);
}
sb.append('OK\t').append(mid).append('\t').append(mm.worldMarkers.size);
"""

MK_LIST_JS = r"""
var mm = Vars.state.markers;
sb.append('WORLD\t').append(mm.worldMarkers.size).append('\n');
sb.append('MINIMAP\t').append(mm.mapMarkers.size).append('\n');
sb.append('LIGHT\t').append(mm.lightMarkers.size).append('\n');
var lit = 0;
for(var k in _mk.slots){ if(_mk.slots.hasOwnProperty(k)) lit++; }
sb.append('MIRROR\t').append(lit);
"""


CHANGES_JS = r"""
if(typeof _evlog === 'undefined'){ sb.append('NOSETUP\t0'); }
else {
  var since = %(since)d, lim = %(limit)d, n = 0;
  for(var i=0;i<_evlog.length;i++){
    var ln = _evlog[i];
    var p = ln.split('\t');
    if(p.length < 2) continue;
    if(parseInt(p[1], 10) <= since) continue;
    sb.append(ln).append('\n');
    if(++n >= lim) break;
  }
  sb.append('SEQ\t').append(_evseq);
}
"""

CHAT_JS = r"""
if(typeof _chatlog === 'undefined'){ sb.append('NOSETUP\t0'); }
else {
  var since = %(since)d, lim = %(limit)d, n = 0;
  for(var i=0;i<_chatlog.length;i++){
    var ln = _chatlog[i];
    var p = ln.split('\t');
    if(p.length < 2) continue;
    if(parseInt(p[0], 10) <= since) continue;
    sb.append(ln).append('\n');
    if(++n >= lim) break;
  }
  sb.append('SEQ\t').append(_chatseq);
}
"""

PUSH_JS = r"""
/* 管理员在游戏里打的 /push 队列: 取走(drain)或只读. 行是 JSON 字符串. */
if(typeof _pushlog === 'undefined'){ sb.append('NOSETUP\t0'); }
else {
  var n2 = _pushlog.length;
  for(var i2 = 0; i2 < n2; i2++){ sb.append(_pushlog[i2]).append('\n'); }
  if(%(drain)d) _pushlog = [];
  sb.append('SEQ\t').append(n2);
}
"""

DOOR_SET_JS = r"""
var dk = %(kind)s, du = %(unit)s, dtx = %(tx)d, dty = %(ty)d, dl = %(label)s;
var dblk = %(block)s;
var t = Vars.world.tile(%(x)d, %(y)d);
if(t == null){ sb.append('ERR\ttile out of bounds'); }
else {
  if(dblk != null && dblk != ''){
    var blk = Vars.content.block(dblk);
    if(blk == null){ sb.append('ERR\tno such block ').append(dblk); }
    else { t.setNet(blk, Vars.state.rules.defaultTeam, 0); }
  }
  _doors[%(x)d + ',' + %(y)d] = {kind: dk, unit: du, tx: dtx, ty: dty, label: dl, scene: %(hasjs)s};
  _doorjs[%(x)d + ',' + %(y)d] = %(scenejs)s;
  if(sb.indexOf('ERR') < 0){ sb.append('OK\t').append(dk).append('\t').append(dtx + ',' + dty); }
}
"""

DOORS_JS = r"""
var nd = 0;
for(var k in _doors){
  if(!_doors.hasOwnProperty(k)) continue;
  var d = _doors[k];
  sb.append(k).append('\t').append(d.kind).append('\t').append(d.unit)
    .append('\t').append(d.tx + ',' + d.ty).append('\t').append(d.label).append('\n');
  nd++;
}
sb.append('COUNT\t').append(nd);
"""

DOOR_HITS_JS = r"""
/* 取走"刚被点过的门"列表(JSON 数组), 由 Python 的 projection_director 轮询 */
if(typeof _doorHits === 'undefined'){ sb.append('[]'); }
else { var a = _doorHits.splice(0, _doorHits.length); sb.append(JSON.stringify(a)); }
"""

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

FRAME_PAINT_JS = r"""
/* 用一批小方块 ShapeMarker 沿矩形边画虚线框。不用真地板: 换地板会盖掉玩家
   自己的染色地板, 而且看起来"没有仿真也有东西"。
   注意量纲: ShapeMarker.radius 是**世界单位**(Lines.poly 直接吃), 而
   PointMarker.radius 是**格**(内部 *tilesize, 而且还带 1.67 s 扩散动画)。 */
if(typeof _fr === 'undefined'){ _fr = {next: 7000, keys: {}}; }
var fx = %(x)d, fy = %(y)d, fw = %(w)d, fh = %(h)d, fk = %(key)s;
var step = %(step)d; if(step < 1){ step = 1; }
var rad = %(radius)s;
var C = Packages.mindustry.gen.Call;
var old = _fr.keys[fk];
if(old != null){
  for(var oi = 0; oi < old.length; oi++){ try{ C.removeMarker(old[oi]); }catch(e0){} }
}
var pts = [], seen = {};
var addp = function(px, py){
  var k2 = px + ',' + py;
  if(seen[k2] != null) return;
  seen[k2] = 1; pts.push([px, py]);
};
for(var ix = 0; ix < fw; ix += step){ addp(fx + ix, fy); addp(fx + ix, fy + fh - 1); }
for(var iy = 0; iy < fh; iy += step){ addp(fx, fy + iy); addp(fx + fw - 1, fy + iy); }
addp(fx + fw - 1, fy); addp(fx, fy + fh - 1); addp(fx + fw - 1, fy + fh - 1);
var ids = [];
for(var pi = 0; pi < pts.length; pi++){
  var mid = _fr.next + pi;
  var pm = new Packages.mindustry.game.MapObjectives$ShapeMarker();
  pm.pos = new Packages.arc.math.geom.Vec2(pts[pi][0] * 8 + 4, pts[pi][1] * 8 + 4);
  pm.radius = rad; pm.sides = 4; pm.rotation = 45; pm.fill = true; pm.outline = false;
  pm.stroke = 1; pm.color = new Packages.arc.graphics.Color(%(r)s, %(g)s, %(b)s, 1);
  pm.world = 1; pm.minimap = -1; pm.light = -1;
  try{ C.removeMarker(mid); }catch(e1){}
  C.createMarker(mid, pm);
  ids.push(mid);
}
_fr.next += pts.length + 4;
_fr.keys[fk] = ids;
sb.append('FRAME	').append(fk).append('	').append(ids.length);
"""

FRAME_CLEAR_JS = r"""
/* 擦掉边界 marker(只 removeMarker, 不碰地板). key 为空时清掉全部. */
if(typeof _fr === 'undefined'){ _fr = {next: 7000, keys: {}}; }
var C = Packages.mindustry.gen.Call;
var want = %(key)s, n = 0;
for(var k in _fr.keys){
  if(!_fr.keys.hasOwnProperty(k)){ continue; }
  if(want != null && want != '' && k != want){ continue; }
  var ids2 = _fr.keys[k];
  for(var i2 = 0; i2 < ids2.length; i2++){ try{ C.removeMarker(ids2[i2]); n++; }catch(e2){} }
  delete _fr.keys[k];
}
sb.append('FRAMECLEAR	').append(n);
"""

FRAME_SWEEP_JS = r"""
/* 守护进程重启后 _fr 是空的, 但客户端屏幕上还留着上次画的框:
  按固定 id 段扫一遍(7000..7999), 保证起来时是干净的. */
var C = Packages.mindustry.gen.Call;
var n3 = 0;
for(var sid = 7000; sid < 8000; sid++){ try{ C.removeMarker(sid); n3++; }catch(e3){} }
_fr = {next: 7000, keys: {}};
sb.append('SWEEP	').append(n3);
"""

FRAME_LIST_JS = r"""
if(typeof _fr === 'undefined'){ _fr = {next: 7000, keys: {}}; }
var out2 = [];
for(var k3 in _fr.keys){
  if(_fr.keys.hasOwnProperty(k3)){ out2.push(k3 + ':' + _fr.keys[k3].length); }
}
sb.append(out2.join(' | '));
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

DOOR_CLEAR_JS = r"""
var nc = 0;
for(var k in _doors){ if(_doors.hasOwnProperty(k)){ delete _doors[k]; nc++; } }
sb.append('CLEARED\t').append(nc);
"""

TAPS_JS = r"""
if(typeof _taplog === 'undefined'){ sb.append('NOSETUP\t0'); }
else {
  var tsince = %(since)d, tlim = %(limit)d, tn = 0;
  for(var ti=0;ti<_taplog.length;ti++){
    var tln = _taplog[ti];
    var tq = tln.split('\t');
    if(tq.length < 2) continue;
    if(parseInt(tq[1], 10) <= tsince) continue;
    sb.append(tln).append('\n');
    if(++tn >= tlim) break;
  }
  sb.append('SEQ\t').append(_tapseq);
}
"""

TAP_FIRE_JS = r"""
var fpl = null;
var fwant = %(who)s;
for(var fi=0;fi<Groups.player.size();fi++){
  var fc = Groups.player.index(fi);
  if(fwant == null || fwant == '' || String(fc.name).indexOf(fwant) >= 0){ fpl = fc; break; }
}
var ft = Vars.world.tile(%(x)d, %(y)d);
if(ft == null){ sb.append('ERR	tile out of bounds'); }
else {
  Packages.arc.Events.fire(new Packages.mindustry.game.EventType.TapEvent(fpl, ft));
  sb.append('FIRED	').append(%(x)d + ',' + %(y)d).append('	').append(fpl == null ? '-' : String(fpl.name));
}
"""

DOORS_FILE = os.path.join(DATA, "doors.json")
MINE_BLOCK = "shock-mine"       # 玩家放下这颗地雷 = 请求投影


def door_register(w, x, y, kind="watch", unit="poly", tx=None, ty=None,
                  label=None, block="shock-mine", scene_path=None, persist=True,
                  scene_at=None, feed=None):
    """登记一扇门: 放按钮方块 + 写 _doors 表 + (可选)编译场景 JS 塞进 _doorjs.

    scene_at 给了就按那一点为中心铺场景 (默认 = 门自己), 这样地雷就是圆心.
    """
    tx = x if tx is None else int(tx)
    ty = y if ty is None else int(ty)
    label = str(label or kind)
    scene_js = None
    shift = [0.0, 0.0]
    if scene_path:
        import scene as scene_mod
        sc = scene_mod.load(str(scene_path))
        want = scene_at or [int(x), int(y)]
        scene_js, _dx, _dy = scene_mod.world_js(sc, at=want)
        shift = [float(_dx), float(_dy)]
    out = w.js(DOOR_SET_JS % {"x": int(x), "y": int(y), "kind": json.dumps(str(kind)),
                              "unit": json.dumps(str(unit)), "tx": int(tx), "ty": int(ty),
                              "label": json.dumps(label),
                              "block": json.dumps(str(block)),
                              "hasjs": "null" if scene_js is None else "true",
                              "scenejs": "null" if scene_js is None else json.dumps(scene_js)})
    if not out:
        raise RuntimeError("no output")
    if out[0].startswith("ERR"):
        raise RuntimeError(out[0][4:])
    if persist:
        rows = []
        try:
            with open(DOORS_FILE, "r", encoding="utf-8") as fh:
                rows = json.load(fh)
        except Exception:
            rows = []
        key = "%d,%d" % (int(x), int(y))
        rows = [r0 for r0 in rows if "%s,%s" % (r0.get("x"), r0.get("y")) != key]
        rows.append({"x": int(x), "y": int(y), "kind": str(kind), "unit": str(unit),
                     "tx": int(tx), "ty": int(ty), "label": label,
                     "block": str(block), "scene": scene_path, "feed": feed,
                     "scene_at": (list(scene_at) if scene_at else None),
                     "shift": shift})
        with open(DOORS_FILE, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, ensure_ascii=False, indent=2)
    meta = {"kind": str(kind), "unit": str(unit), "block": str(block),
            "scene": scene_path, "feed": feed, "shift": shift,
            "scene_at": (list(scene_at) if scene_at else [int(x), int(y)])}
    if not hasattr(w, "_doors_meta"):
        w._doors_meta = {}
    w._doors_meta["%d,%d" % (int(x), int(y))] = meta
    return {"tile": "%d,%d" % (int(x), int(y)), "kind": str(kind),
            "unit": str(unit), "target": [int(tx), int(ty)], "label": label}


def _mirror_slot(w, slot):
    """一块沙盘 = 一个槽: 自己的 feed / 偏移 / 代次 / marker id 段."""
    if not hasattr(w, "_mirrors"):
        w._mirrors = {}
    k = int(slot)
    st = w._mirrors.get(k)
    if st is None:
        st = {"feed": None, "off": (0.0, 0.0), "seq": 0, "thread": None}
        w._mirrors[k] = st
    return st


def mirror_push(w, units, dx=0.0, dy=0.0, gen=None, slot=0):
    """把一组 {type,x,y,amount,ctrl} 画成世界 marker（只画在 slot 自己的 id 段里）.

    dx/dy 是按格算的整体偏移: 仿真世界和真世界坐标系不同, 用它把图标挪到
    玩家当前看的地方 (1 格 = 8 wu).

    gen 是调用方看到的代次: 投影结束时 mirror_stop 会把该槽的 seq 加一,
    于是"清理前就已经在路上的那一帧"会被丢掉, 否则它会抢在清理之后把图标
    又画回来 (实测过: 拆雷后 marker 还剩 16 个).
    多块沙盘并行时各自用不同的 slot, marker id 段互不重叠 —— 不会互相覆盖.
    """
    st = _mirror_slot(w, slot)
    if gen is not None and gen != st.get("seq", 0):
        return {"ok": False, "error": "mirror stopped"}
    # units 里的 x/y 是格(tiles); 仿真侧就在 push 时除过 8 了
    if dx or dy:
        units = [dict(u, x=float(u.get("x", 0)) + dx, y=float(u.get("y", 0)) + dy)
                 if isinstance(u, dict) else u for u in units]
    txt = json.dumps(units, ensure_ascii=False)
    b64 = base64.b64encode(txt.encode("utf-8")).decode("ascii")
    out = w.js(MS_INSTALL_JS)
    if out and str(out[0]).startswith("ERR"):
        return {"ok": False, "error": str(out[0][4:])}
    if gen is not None and gen != st.get("seq", 0):
        return {"ok": False, "error": "mirror stopped"}
    res = w.js(MS_APPLY_JS % {"b64": b64, "slot": int(slot)})
    if not res:
        return {"ok": False, "error": "no output"}
    if str(res[0]).startswith("ERR"):
        return {"ok": False, "error": str(res[0][4:])}
    return {"ok": True, "count": int(float(res[0])) if str(res[0]).strip() else len(units)}


def mirror_watch(w, path, slot=0, dx=0.0, dy=0.0, cell=None):
    """后台线程: 盯着 push 文件, 内容一变就把整张表应用到世界（该槽的 id 段）.

    mlogsim --push 每 N tick 覆写这个文件; 服务端在这里读, 所以仿真进程
    不需要知道 apiPort/协议, 两边只靠一个文件解耦 (OneDrive 目录下也行).
    """
    st = _mirror_slot(w, slot)
    mirror_stop(w, slot)
    st["feed"] = str(path)
    st["off"] = (float(dx), float(dy))
    # cell = 这块沙盘的场景锚点(格心). feed 自己带 anchor(仿真场景锚点)时,
    # 偏移要用 "格心 - 仿真锚点" 现算: 仿真世界和真世界的原点并不一致.
    st["cell"] = (float(cell[0]), float(cell[1])) if cell else None
    my_gen = int(st.get("seq", 0))
    if int(slot) == 0:
        w.mirror_feed = str(path)
        w.mirror_off = st["off"]
    last = None

    def loop():
        nonlocal last
        # 该槽的 feed 被清空/换路径/代次变了, 线程自己退出
        while st.get("feed") == str(path) and st.get("seq", 0) == my_gen:
            time.sleep(0.12)
            try:
                fst = os.stat(path)
                stamp = (fst.st_mtime_ns, fst.st_size)
                if stamp == last:
                    continue
                last = stamp
                with open(path, "r", encoding="utf-8") as fh:
                    txt = fh.read().strip()
                if not txt:
                    continue
                # 写端是直接覆写, 抽到的可能是半截 JSON: 就地重试几次, 抽不到就等下一拍
                units = None
                for _try in range(4):
                    try:
                        units = json.loads(txt)
                        break
                    except ValueError:
                        time.sleep(0.02)
                        try:
                            with open(path, "r", encoding="utf-8") as fh:
                                txt = fh.read().strip()
                        except OSError:
                            break
                if units is None:
                    last = None
                    continue
                # 新格式是 {world:[w,h], units:[...]}: world 让沙盘画出仿真世界边界
                if isinstance(units, dict):
                    wsize = units.get("world")
                    st["world"] = list(wsize) if wsize else None
                    wanc = units.get("anchor")
                    st["feed_anchor"] = list(wanc) if wanc else None
                    units = units.get("units") or []
                dxs, dys = st.get("off", (0.0, 0.0))
                fa, cl = st.get("feed_anchor"), st.get("cell")
                if fa and cl:
                    # 仿真坐标以它自己场景的锚点为基准: 换到真世界要减掉它再加格心
                    dxs, dys = float(cl[0]) - float(fa[0]), float(cl[1]) - float(fa[1])
                r = mirror_push(w, units, dxs, dys, gen=my_gen, slot=slot)
                if not r.get("ok"):
                    print("[warn] 状态镜推送失败 (slot %d): %s" % (slot, r.get("error")),
                          flush=True)
                    last = None
            except FileNotFoundError:
                continue
            except Exception as exc:  # noqa: BLE001
                now = time.time()
                if now - getattr(w, "_mirror_warn_at", 0) > 30:
                    w._mirror_warn_at = now
                    print("[warn] 状态镜读取失败: %s" % exc, flush=True)
                last = None

    th = threading.Thread(target=loop, name="mirror-%d" % int(slot), daemon=True)
    st["thread"] = th
    th.start()


def mirror_stop(w, slot=None):
    """停掉盯文件的线程并清空该槽的 marker(含"已上路的那一帧").

    slot=None 表示全部(老接口 mirror_clear 用).
    """
    if slot is None:
        keys = sorted(getattr(w, "_mirrors", {}).keys())
    else:
        keys = [int(slot)]
    for k in keys:
        st = _mirror_slot(w, k)
        st["feed"] = None
        st["seq"] = int(st.get("seq", 0)) + 1
    if int(slot or 0) == 0 and slot is not None:
        w.mirror_feed = None
    n = 0
    for attempt in (0, 1):
        for k in keys:
            try:
                out = w.js(MS_CLEAR_JS % {"slot": int(k)})
                n += int(float(out[0])) if out else 0
            except Exception:  # noqa: BLE001 - 停线程比清屏重要
                pass
        if attempt == 0:
            time.sleep(0.2)   # 给"已经在半路的"那一帧落地时间, 再清一遍
    return n


def door_reload(w):
    """守护进程启动后把 doors.json 里的门重新登记一遍(场景 JSON 也会重新编译)."""
    try:
        with open(DOORS_FILE, "r", encoding="utf-8") as fh:
            rows = json.load(fh)
    except Exception:
        return 0
    n = 0
    for r0 in rows:
        try:
            door_register(w, r0["x"], r0["y"], r0.get("kind") or "possess",
                          r0.get("unit") or "poly", r0.get("tx"), r0.get("ty"),
                          r0.get("label"), r0.get("block") or "shock-mine",
                          r0.get("scene"), persist=False)
            n += 1
        except Exception as exc:
            print("[warn] 门 %s,%s 重装失败: %s" % (r0.get("x"), r0.get("y"), exc), flush=True)
    return n



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


def feed_age(path):
    """Seconds since the feed file was last written; None if it is not there."""
    try:
        return max(0.0, time.time() - os.stat(path).st_mtime)
    except OSError:
        return None


FRAME_COLOR = (1.0, 0.82, 0.35)
# 第二个框（按 feed 里单位实际坐标算出来的外接框）用的颜色: 青色，和落雷框区分开
LIVE_COLOR = (0.35, 0.95, 0.95)
# 边界框只在「仿真 feed 还新鲜」的时候画出来: 没跑仿真时满屏框只会让人困惑
FRAME_LIVE_MAX = 10.0


def feed_world(path):
    """读一条 feed 里带的"模拟器世界尺寸" [w, h]（老格式没有就返回 None）。"""
    if not path:
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:  # noqa: BLE001
        return None
    if isinstance(data, dict):
        ws = data.get("world")
        if ws:
            try:
                return [int(float(ws[0])), int(float(ws[1]))]
            except Exception:  # noqa: BLE001
                return None
    return None


def feed_anchor(path):
    """读 feed 里带的仿真场景锚点(格); 老格式/没有返回 None."""
    if not path:
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            rows = json.load(fh)
    except Exception:  # noqa: BLE001
        return None
    if isinstance(rows, dict) and rows.get("anchor"):
        try:
            return [float(rows["anchor"][0]), float(rows["anchor"][1])]
        except Exception:  # noqa: BLE001
            return None
    return None


def feed_scene(path):
    """读 feed 里带的场景出处 {"path", "label"}; 老格式/没有返回 None.

    `mlogsim --scene X --push F` 会把 X 的绝对路径和场景名写进 F。这样世界侧
    只拿一条 feed 也能把建筑一起复刻出来，不必用 --watch-scene 再指一遍同一张
    场景 —— 少了这个，feed 只够画单位影子，框/雷/日志板全都起不来。
    """
    if not path:
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:  # noqa: BLE001
        return None
    if not isinstance(data, dict):
        return None
    sc = data.get("scene")
    if not sc:
        return None
    sc = str(sc)
    if not os.path.isfile(sc):
        return None
    return {"path": sc, "label": str(data.get("label") or "") or None}


def feed_bbox(path, pad=2):
    """读一条 feed，返回里面所有单位的外接矩形 [x, y, w, h]（世界格，含 pad）。

    场景 JSON 的 frame 只是「在哪放雷」的选区，单位实际会跑去矿区/核心/容器，
    所以「这个仿真的边界」只能按真实坐标算。读不到返回 None。
    """
    if not path:
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            rows = json.load(fh)
    except Exception:  # noqa: BLE001
        return None
    if isinstance(rows, dict):
        rows = rows.get("units") or []
    xs, ys = [], []
    for e in (rows or []):
        if not isinstance(e, dict):
            continue
        try:
            mx = e.get("x") if e.get("x") is not None else e.get("tx")
            my = e.get("y") if e.get("y") is not None else e.get("ty")
            xs.append(float(mx))
            ys.append(float(my))
        except Exception:  # noqa: BLE001
            continue
    if not xs:
        return None
    x0, y0 = int(math.floor(min(xs))) - int(pad), int(math.floor(min(ys))) - int(pad)
    x1, y1 = int(math.ceil(max(xs))) + int(pad), int(math.ceil(max(ys))) + int(pad)
    return [x0, y0, max(1, x1 - x0), max(1, y1 - y0)]


# ---------------------------------------------------------------- 沙盘日志板
# 世界里每块沙盘左上角都用 TextMarker 列一块小面板: 标题 / feed 新鲜度 / 投影状态 /
# 单位数 / 最近几条事件. 这样"沙盘在干什么"不用切回聊天栏看.
SB_BASE = 5000
SB_SPAN = 8            # 每块沙盘占 8 个 id
SB_MAX_LINES = 8
SB_FONT = 0.9
SB_EVENTS = 3          # 面板上留几行事件


def _sb_store(w):
    st = getattr(w, "_sb_log", None)
    if st is None:
        st = {}
        w._sb_log = st
    return st


def sb_event(w, slot, msg, keep=SB_EVENTS):
    """往某块沙盘的日志板尾追加一行(ASCII, 中文在逻辑字体里画不出来)."""
    slot = int(slot)
    rows = _sb_store(w).setdefault(slot, [])
    rows.append("%s %s" % (time.strftime("%H:%M:%S"), str(msg)))
    del rows[:-keep]
    return rows


def feed_units(path):
    """feed 里这一帧有多少只单位(读不到返回 0)."""
    if not path:
        return 0
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:  # noqa: BLE001
        return 0
    if isinstance(data, dict):
        data = data.get("units") or []
    try:
        return len(data or [])
    except TypeError:
        return 0


def _sb_write(w, slot, text):
    """把面板文本写到 java 进程 cwd 里(控制台 js 行传不了字符串字面量)."""
    path = os.path.join(DATA, "sb%d.txt" % int(slot))
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    return path


def sb_lines(w, slot, d=None, age=None, live=False):
    """一块沙盘面板的完整文本行(第一行在最上面)."""
    slot = int(slot)
    d = d or {}
    p = _projs(w).get(slot)
    stem = os.path.splitext(os.path.basename(d.get("path") or "scene"))[0]
    out = ["#%d %s" % (slot + 1, stem)]
    if age is None:
        out.append("feed --   (mlogsim --push)")
    else:
        out.append("feed %.1fs %s" % (age, "live" if live else "idle"))
    out.append(("proj ON  bld %d" % len(p.get("builds") or [])) if p else "proj --")
    out.append("units %d" % feed_units(d.get("feed")))
    fr = d.get("frame")
    if fr:
        out.append("frame %d,%d %dx%d" % (int(fr[0]), int(fr[1]), int(fr[2]), int(fr[3])))
    rows = _sb_store(w).get(slot) or []
    room = SB_MAX_LINES - len(out)
    if room > 0 and rows:
        out.extend(rows[-room:])
    return out[:SB_MAX_LINES]


def sb_render(w, slot, d=None, age=None, live=False, force=False):
    """把面板刷到世界里; 文本没变就不发 js(每 0.5 s 一轮, 省往返)."""
    slot = int(slot)
    lines = sb_lines(w, slot, d=d, age=age, live=live)
    key = "\n".join(lines)
    cache = getattr(w, "_sb_cache", None)
    if cache is None:
        cache = {}
        w._sb_cache = cache
    if not force and cache.get(slot) == key:
        return 0
    cell = (d or {}).get("cell")
    if cell:
        gx = float(cell[0]) + 2.0
        gy = float(cell[1]) + 3.0
    else:
        bw, bh = getattr(w, "base", (0, 0))
        gx, gy = float(bw), float(bh)
    # _sbSet 里 JSON.parse 的是一行一个元素的数组, 不能直接喂纯文本
    _sb_write(w, slot, json.dumps(lines, ensure_ascii=False))
    w.js(SB_SET_JS % {"slot": slot, "gx": gx, "gy": gy, "sz": SB_FONT})
    cache[slot] = key
    return len(lines)


def sb_clear(w, slot=None):
    """擦掉一块(或全部)日志板."""
    ks = [int(slot)] if slot is not None else sorted(_sb_store(w).keys())
    for k in ks:
        try:
            _sb_write(w, k, "[]")
            w.js(SB_SET_JS % {"slot": k, "gx": 0.0, "gy": 0.0, "sz": SB_FONT})
        except Exception:  # noqa: BLE001
            pass
        _sb_store(w).pop(k, None)
        getattr(w, "_sb_cache", {}).pop(k, None)
    return len(ks)



def frame_paint(wd_, rect, key, step=1, radius=7.0, color=None):
    """给一个场景的矩形边界画一圈 marker(点). rect 是世界格 [x, y, w, h].

    只画 marker, 不动地形: 之前用 metal-floor 铺了一圈真地板, 会盖掉玩家自己
    刷的染色地板, 而且看起来"没有仿真也有东西".

    注意参数名不能叫 w —— 解包 rect 时会把 w 覆盖成整数, 于是 w.js 崩成
    "'int' object has no attribute 'js'".
    """
    fx, fy, fw, fh = [int(v) for v in rect[:4]]
    col = color or FRAME_COLOR
    out = wd_.js(FRAME_PAINT_JS % {"x": fx, "y": fy, "w": fw, "h": fh,
                                   "key": json.dumps(str(key)),
                                   "step": max(1, int(step)),
                                   "radius": float(radius),
                                   "r": float(col[0]), "g": float(col[1]),
                                   "b": float(col[2])})
    for ln in (out or []):
        s = str(ln)
        if s.startswith("FRAME	"):
            try:
                return int(float(s.split("	")[2]))
            except (IndexError, ValueError):
                pass
    return 0


def frame_clear(wd_, key=None):
    """擦掉边界 marker; key 省略 = 全部."""
    out = wd_.js(FRAME_CLEAR_JS % {"key": json.dumps(key) if key else "null"})
    for ln in (out or []):
        s = str(ln)
        if s.startswith("FRAMECLEAR	"):
            try:
                return int(float(s.split("	")[1]))
            except (IndexError, ValueError):
                pass
    return 0


def scenes_from_feeds(feeds):
    """[feed] -> [场景路径], 顺序跟 feed 一一对应; 没有任何 feed 带场景时返回 [].

    某条 feed 没带场景就借用第一条的 —— 让 layout/索引保持对齐（第 i 条 feed
    仍然对应第 i 块沙盘），而不是塌成一条把后面的场景挤掉。
    """
    picked = []
    for f in (feeds or []):
        got = feed_scene(f)
        picked.append(got["path"] if got else None)
    first = next((p for p in picked if p), None)
    if not first:
        return []
    return [p or first for p in picked]


def load_dir_scenes(paths, skip_bad=False):
    """[scene path] -> [{path, sc, frame, anchor, label}], 全是场景自己的坐标.

    skip_bad=True 时跳过读不动的场景（feed 自带的场景路径是"别人写的提醒"，
    坏一张不该把整个投影导演拖死；--watch-scene 显式给的仍然老实报错）。
    """
    import scene as scene_mod
    out = []
    for p in (paths or []):
        try:
            sc = scene_mod.load(str(p))
        except Exception as exc:  # noqa: BLE001
            if not skip_bad:
                raise
            print("[warn] 跳过场景 %s: %s" % (p, exc), flush=True)
            continue
        out.append({
            "path": str(p),
            "sc": sc,
            "label": sc.get("name") or os.path.splitext(os.path.basename(str(p)))[0],
            "frame": scene_mod.frame_of(sc),
            "anchor": scene_mod.anchor_of(sc),
        })
    return out


def world_size(w):
    """世界格数 (宽, 高). 查一次就缓存在 w 上."""
    sz = getattr(w, "_world_size", None)
    if sz:
        return sz
    try:
        out = w.js("sb.append(Vars.world.width()).append(',').append(Vars.world.height());")
        a, b = str(out[0]).split(",")[:2]
        sz = (int(float(a)), int(float(b)))
    except Exception:  # noqa: BLE001
        sz = (512, 512)
    w._world_size = sz
    return sz


def layout_scenes(w, scenes, cell=64, origin=(0, 0)):
    """把每个场景按 cell×cell 的格子从左上角开始排, 锚点落在格子中心.

    每个场景原本带着自己的一整套绝对坐标(建筑/单位/clear/frame/anchor), 这里
    只算一个整体位移: 锚点 -> 格子中心。frame 和 clear 跟着一起平移, 所以
    "雷落在框里" 的判断不用改。

    返回的每项多出 cell / origin_anchor / origin_frame, 方便排查。
    """
    ww, wh = world_size(w)
    cols = max(1, ww // int(cell))
    rows = max(1, wh // int(cell))
    out = []
    for i, d in enumerate(scenes or []):
        col, row = i % cols, i // cols
        if row >= rows:          # 场景比格子多: 叠回最后一格, 不越界
            row = rows - 1
        cx = int(origin[0]) + col * int(cell) + int(cell) // 2
        cy = int(origin[1]) + row * int(cell) + int(cell) // 2
        ax, ay = d["anchor"]
        dx, dy = cx - int(ax), cy - int(ay)
        fx, fy, fw, fh = d["frame"]
        e = dict(d)
        e["cell"] = [int(origin[0]) + col * int(cell), int(origin[1]) + row * int(cell), int(cell), int(cell)]
        e["origin_anchor"] = [int(ax), int(ay)]
        e["origin_frame"] = [fx, fy, fw, fh]
        e["anchor"] = [cx, cy]
        e["frame"] = [fx + dx, fy + dy, fw, fh]
        e["shift"] = [dx, dy]
        out.append(e)
    return out


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


def _projs(w):
    """正在投影的沙盘: slot -> {center, builds, feed, scene}. 多块可以同时投影."""
    if not hasattr(w, "_projs"):
        w._projs = {}
    return w._projs


def project_at(w, x, y, feed, scene_path=None, tell=True, anchor=None, slot=0, pin=True):
    """以玩家放下的那颗地雷为圆心: 复刻场景 + 把单位影子挂到该槽的 feed 上.

    场景自带 clear 矩形, 会把地雷一起抹掉, 所以铺完要原样钉回去 —— 那颗雷
    既是圆心也是"这里已经在投影"的标记.
    slot 决定 marker 的 id 段, 所以多块沙盘可以同时投影、互不覆盖.
    """
    slot = int(slot)
    if slot in _projs(w):
        end_projection(w, slot, "这个沙盘又放了一颗地雷")
    if not scene_path:
        # feed 自带场景出处时(mlogsim --scene X --push F)就不用手工再指一遍
        got = feed_scene(feed)
        if got:
            scene_path = got["path"]
    x, y = int(x), int(y)
    shift = [0.0, 0.0]
    placed = 0
    builds = []
    if scene_path:
        import scene as scene_mod
        sc = scene_mod.load(str(scene_path))
        # anchor 给了就按场景自己的锚点摆(多场景 = 固定区域), 否则以雷为圆心
        ax, ay = (int(anchor[0]), int(anchor[1])) if anchor else (x, y)
        js, sdx, sdy = scene_mod.world_js(sc, at=[ax, ay])
        shift = [float(sdx), float(sdy)]
        out = w.js(js)
        rows = [str(ln) for ln in (out or []) if str(ln).startswith("B\t")]
        placed = len(rows)
        for ln in rows:
            f2 = ln.split("\t")
            if len(f2) >= 5:
                try:
                    # Rhino 打出来的数字是 "246.0", 不能直接 int()
                    builds.append([int(float(f2[3])), int(float(f2[4])), f2[2]])
                except ValueError:
                    pass
    if pin:
        # 自动投影不钉雷(没有"圆心那颗雷"这回事, 钉了反而会被拆雷逻辑误判)
        w.js(REPLACE_MINE_JS % {"x": x, "y": y, "block": json.dumps(MINE_BLOCK)})
    if builds:
        try:
            resync_builds(w, builds)
        except Exception as exc:  # noqa: BLE001
            print("[warn] 补发代码/配置失败: %s" % exc, flush=True)
        # 客户端可能还没把这一格建出来(同帧 setNet + tileConfig), 隔一秒再补一次
        def _late(wd_=w, bl=list(builds)):
            time.sleep(1.2)
            try:
                resync_builds(wd_, bl)
            except Exception:  # noqa: BLE001
                pass
        threading.Thread(target=_late, daemon=True).start()
    mirror_watch(w, feed, slot=slot, dx=shift[0], dy=shift[1], cell=[ax, ay])
    _projs(w)[slot] = {"center": (x, y), "builds": builds, "feed": feed,
                       "scene": scene_path}
    w._proj_seen = getattr(w, "_proj_seen", set())
    w._proj_seen.add("%d,%d" % (x, y))
    sb_event(w, slot, "proj start, bld %d" % len(builds))
    if tell:
        chat(w, "投影已开始：地雷 (%d,%d) 就是圆心，拆掉它就结束" % (x, y))
    return {"ok": True, "x": x, "y": y, "feed": feed, "scene": scene_path,
            "placed": placed, "shift": shift, "slot": slot}


def end_projection(w, slot, why="地雷被拆除"):
    """拆掉圆心那颗脉冲地雷 = 结束这块沙盘的投影: 停影子、拆建筑、放回地雷位."""
    slot = int(slot)
    p = _projs(w).get(slot)
    if p is None:
        return {"ok": False, "error": "not projecting"}
    cx = p.get("center")
    mirror_stop(w, slot)
    key = "%d,%d" % (int(cx[0]), int(cx[1]))
    getattr(w, "_proj_seen", set()).discard(key)
    # 铺下去的建筑要一起拆掉(含核心), 否则地面上留下一堆跑不动的空壳
    builds = p.get("builds") or []
    dn = 0
    if builds:
        try:
            res = w.js(DEMOLISH_JS % {"list": json.dumps(builds)})
            for ln in (res or []):
                s = str(ln)
                if s.startswith("DEMOLISH\t"):
                    dn = int(float(s.split("\t")[1]))
        except Exception as exc:
            print("[warn] 拆除投影建筑失败: %s" % exc)
    del _projs(w)[slot]
    # 再清一次 marker: 走 setNet 拆楼会触发一批事件, 万一有帧漏进来也在这里扫掉
    try:
        w.js(MS_CLEAR_JS % {"slot": int(slot)})
    except Exception:  # noqa: BLE001
        pass
    sb_event(w, slot, "proj end, razed %d" % dn)
    print("[info] 投影结束 (slot %d, %d,%d)：%s，拆掉 %d 座建筑"
          % (slot, int(cx[0]), int(cx[1]), why, dn), flush=True)
    chat(w, "投影已结束：%s（拆掉 %d 座建筑）" % (why, dn))
    return {"ok": True, "ended": [int(cx[0]), int(cx[1])], "why": why, "slot": slot}


def start_projection(w, meta, slot=0):
    """手动开投影(projection op): 没给坐标就用 meta 里的 scene_at / 世界中心."""
    meta = meta or {}
    feed = meta.get("feed")
    if not feed:
        return {"ok": False, "error": "need feed path (mlogsim --push)"}
    if feed_age(feed) is None:
        return {"ok": False, "error": "feed 不存在: %s" % feed}
    spot = meta.get("scene_at") or meta.get("at") or list(getattr(w, "base", (0, 0)))
    return project_at(w, spot[0], spot[1], feed, meta.get("scene"), slot=slot)


def projection_director(w, feed, scene_path=None, at=None, poll=0.5,
                        fresh=25.0, lim=10, scenes=None, frames=True,
                        frame_floor="marker", at_cell=64, feeds=None, auto=True,
                        hold=0.0):
    """0.5 s 一圈: 玩家放下一颗脉冲地雷就开始投影.

    多场景: scenes 是场景路径列表(命令行 --watch-scene 可重复)。场景按 at_cell
    见方的格子从地图左上角开始固定排布(第 i 个场景 -> 第 i 格, 锚点落在格心),
    边界用一圈小方块 marker 画出来, 只在仿真 feed 新鲜时出现, 一停就擦掉。
    放雷落在哪个框里就用哪个场景; 落在框外直接拒绝(不再"以雷为圆心"乱铺)。

    auto=True(默认): 不看地雷. 某块沙盘的 feed 新鲜就自动复刻并挂影子, feed 一停就收摊.
    地雷只在 auto=False(--manual)时才是开关.

    Java 回调不了 Python, 所以 TileChangeEvent 里只把新地雷的格子塞进
    _mineHits; 真正铺场景/挂 marker 的是这个线程.
    """
    if getattr(w, "_dir_started", False):
        return False
    if not hasattr(w, "_doors_meta"):
        w._doors_meta = {}
    w._dir_started = True
    # 多条仿真并行时, 每个场景配一条自己的 feed (第 i 个场景 -> 第 i 条 feed);
    # 只给一条就所有场景共用, 兼容老的 --watch-feed 单值写法.
    feeds0 = []
    for f in (feeds if feeds else ([feed] if feed else [])):
        if f:
            feeds0.append(str(f))
    w._dir_feeds = feeds0
    w._dir_feed = feeds0[0] if feeds0 else None
    paths = list(scenes) if scenes else ([scene_path] if scene_path else [])
    from_feed = False
    # feed 自足模式: 只给了 --watch-feed 时，按 feed 里记的场景出处补上场景。
    # 顺序跟 feed 一一对应（第 i 条 feed -> 第 i 张场景）；某条 feed 没带场景就
    # 借用第一条的，保证 layout/索引仍然对齐。
    if not paths and feeds0:
        from_feed = True
        paths = scenes_from_feeds(feeds0)
        if paths:
            print("[info] 场景来自 feed: %s" % ", ".join(
                os.path.basename(p) for p in paths), flush=True)
    if os.environ.get("WORLD_DEBUG_SCENES"):
        print("[info] 场景路径: %r" % (paths,), flush=True)
    w._dir_scenes = load_dir_scenes(paths, skip_bad=from_feed)
    w._dir_frames = bool(frames)
    w._dir_frame_floor = frame_floor
    # 场景不再"跟着雷到处跑": 按 64x64 的格子从左上角开始固定排布,
    # 每个场景的锚点落在自己那格的正中心.
    w._dir_cell = int(at_cell)
    # 仿真停下后投影/框还留多久(sblog 也用这个判 live) 
    w._dir_hold = float(hold or 0.0)

    def arm_scenes(paths_, skip_bad=False):
        """排布 + 配 feed; 启动时和"服务先起、仿真后到"的热接都走这里."""
        ds = layout_scenes(w, load_dir_scenes(paths_, skip_bad=skip_bad),
                           cell=w._dir_cell)
        for i, d in enumerate(ds):
            d["feed"] = (feeds0[i] if i < len(feeds0)
                         else (feeds0[0] if feeds0 else None))
            print("[info] 沙盘 #%d %s 格子 %s -> 框 %s 锚点 %s feed %s"
                  % (i + 1, d["label"], d["cell"], d["frame"], d["anchor"],
                     os.path.basename(d["feed"]) if d["feed"] else "-"), flush=True)
        w._dir_scenes = ds
        if ds:
            w._dir_scene = ds[0]["path"]
        return ds

    arm_scenes(paths, skip_bad=from_feed)
    w._dir_frames_on = {}
    if w._dir_frames:
        try:
            # 先扫掉上次进程留下的框(重启后 _fr 是空的, 屏幕上还留着旧 marker)
            w.js(FRAME_SWEEP_JS)
        except Exception:  # noqa: BLE001
            pass
    try:
        # 日志板同理: 上一轮进程画的面板要先擦, 否则叠一层旧文字
        w.js(SB_SWEEP_JS)
    except Exception:  # noqa: BLE001
        pass
    w._dir_scene = (w._dir_scenes[0]["path"] if w._dir_scenes else scene_path)
    w._dir_at = list(at) if at else None
    w._dir_stop = False
    w._proj_seen = getattr(w, "_proj_seen", set())

    def loop():
        while not getattr(w, "_dir_stop", False):
            time.sleep(poll)
            try:
                # 服务先起、仿真后到: 启动时 feed 里还没有场景出处, 等它写出来
                # 再补一次（否则得重启服务才有建筑/框/日志板）
                if not w._dir_scenes and w._dir_feeds:
                    got = scenes_from_feeds(w._dir_feeds)
                    if got:
                        print("[info] 场景来自 feed（热接）: %s" % ", ".join(
                            os.path.basename(p) for p in got), flush=True)
                        arm_scenes(got, skip_bad=True)
                # 边界框: 只在仿真真的在跑时出现; 仿真一停就擦掉
                if w._dir_frames:
                    onmap = getattr(w, "_dir_frames_on", None)
                    if not isinstance(onmap, dict):
                        onmap = {}
                    livemap = getattr(w, "_dir_live", None)
                    if not isinstance(livemap, dict):
                        livemap = {}
                    # hold: 仿真已经停了, 但故意把框/投影多留 N 秒 (tick 级调试时
                    # 跑完一轮要停下来看变量, 默认 10 s 一到画面就被拆了)
                    win = max(FRAME_LIVE_MAX, float(hold or 0))
                    for si, d in enumerate(w._dir_scenes):
                        key0 = d["path"]
                        age0 = feed_age(d.get("feed"))
                        live = age0 is not None and age0 <= win
                        # 自动投影: 有仿真就自己铺, 不需要玩家放雷
                        if auto and d.get("feed"):
                            try:
                                if live and si not in _projs(w):
                                    rr = project_at(w, int(d["anchor"][0]), int(d["anchor"][1]),
                                                    d["feed"], key0, tell=False,
                                                    anchor=d["anchor"], slot=si, pin=False)
                                    chat(w, "自动投影：%s" % d["label"])
                                    print("[info] 自动投影 %s @%s slot %d, 建筑 %d 块"
                                          % (d["label"], d["anchor"], si,
                                             rr.get("placed", 0)), flush=True)
                                elif (not live) and si in _projs(w):
                                    end_projection(w, si, "仿真停了（%s）"
                                                   % os.path.basename(d["feed"] or "-"))
                            except Exception as exc:  # noqa: BLE001
                                print("[warn] 自动投影失败 %s: %s" % (d["label"], exc),
                                      flush=True)
                        if live != bool(onmap.get(key0)):
                            if live:
                                try:
                                    n0 = frame_paint(w, d["frame"], key0)
                                    print("[info] 仿真在跑（%s）：%s 的落雷框已画出（%d 个点）"
                                          % (os.path.basename(d["feed"] or "-"),
                                             d["label"], n0), flush=True)
                                except Exception as exc:  # noqa: BLE001
                                    print("[warn] 画边界失败 %s: %s" % (d["label"], exc),
                                          flush=True)
                            else:
                                try:
                                    frame_clear(w, key0)
                                    frame_clear(w, key0 + "@live")
                                except Exception:  # noqa: BLE001
                                    pass
                                livemap.pop(key0, None)
                                print("[info] 仿真停了（%s）：%s 的边界已擦掉"
                                      % (os.path.basename(d.get("feed") or "-"),
                                         d["label"]), flush=True)
                            onmap[key0] = live
                        # 第二个框画"仿真真实范围": feed 里单位的外接框(带 pad)。
                        # 落雷框只是"在哪放雷"的选区, 单位会跑去矿区/核心,
                        # 所以真正的边界要按实际坐标算.
                        if live:
                            # 第二个框 = 模拟器那张地图的整体边界: 场景锚点落在格心,
                            # 仿真世界 [0,0,w,h] 平移到真世界就是格心 - 锚点 开始的那一块.
                            # 单位在仿真里的活动范围永远出不了它, 所以这才是"真边界".
                            sx0, sy0 = d.get("shift") or (0, 0)
                            fa0 = feed_anchor(d.get("feed"))
                            if fa0 and d.get("anchor"):
                                # 仿真坐标以它自己场景的锚点为原点: 平移量 = 格心 - 那个锚点
                                sx0 = float(d["anchor"][0]) - fa0[0]
                                sy0 = float(d["anchor"][1]) - fa0[1]
                            ws = feed_world(d.get("feed"))
                            bb = None
                            if ws:
                                ww0, wh0 = world_size(w)
                                bx = int(round(sx0))
                                by = int(round(sy0))
                                bb = [max(0, bx), max(0, by),
                                      max(1, min(ws[0], ww0 - max(0, bx))),
                                      max(1, min(ws[1], wh0 - max(0, by)))]
                            else:
                                bb = feed_bbox(d.get("feed"))
                                if bb:
                                    bb = [bb[0] + int(round(sx0)), bb[1] + int(round(sy0)),
                                          bb[2], bb[3]]
                            if bb and tuple(bb) != livemap.get(key0):
                                try:
                                    # 大框(仿真世界整张图)线条多, 按周长收缩点的密度
                                    stp = max(1, int(round((bb[2] + bb[3]) / 48.0)))
                                    frame_paint(w, bb, key0 + "@live", step=stp,
                                                radius=5.0, color=LIVE_COLOR)
                                    livemap[key0] = tuple(bb)
                                except Exception as exc:  # noqa: BLE001
                                    print("[warn] 画仿真范围失败 %s: %s"
                                          % (d["label"], exc), flush=True)
                        else:
                            livemap.pop(key0, None)
                    w._dir_frames_on = onmap
                    w._dir_live = livemap
                # 每块沙盘的文本日志板: 标题 / feed 龄 / 投影状态 / 建筑数 / 单位数 / 事件
                win2 = max(FRAME_LIVE_MAX, float(hold or 0))
                prev2 = getattr(w, "_sb_live", None)
                if not isinstance(prev2, dict):
                    prev2 = {}
                    w._sb_live = prev2
                for si2, d2 in enumerate(w._dir_scenes):
                    try:
                        age2b = feed_age(d2.get("feed"))
                        live2 = age2b is not None and age2b <= win2
                        if bool(prev2.get(si2)) != live2:
                            sb_event(w, si2, "feed live" if live2 else "feed lost")
                            prev2[si2] = live2
                        if live2:
                            sb_render(w, si2, d=d2, age=age2b, live=live2)
                        elif _sb_store(w).get(int(si2)):
                            # 没有仿真就别留板子(和"没仿真不画框"同一条规矩):
                            # sb_clear 会把 store/cache 一起清掉, 下一轮就不会再发 js
                            sb_clear(w, si2)
                    except Exception as exc:  # noqa: BLE001
                        print("[warn] 日志板 %s: %s" % (d2.get("label"), exc), flush=True)
                # 每块沙盘各自看圆心那颗雷还在不在(直接读格子上的方块名, 事件顺序不可靠)
                # 自动模式下根本不钉地雷, 也不该被地雷事件驱动 —— 整段跳过.
                for sl in ([] if auto else sorted(_projs(w).keys())):
                    p = _projs(w)[sl]
                    cx = p.get("center")
                    st = w.js(MINE_STATE_JS % {"x": int(cx[0]), "y": int(cx[1])})
                    cur = str(st[0]).strip() if st else ""
                    if cur != MINE_BLOCK:
                        end_projection(w, sl, "圆心那颗脉冲地雷不在了")
                        continue
                    # 仿真进程死了 / 被 --js-timeout 掐了: 影子会冻结在最后一帧,
                    # 留在场上只会误导, 超过 60 s 没新帧就自动收摊
                    age2 = feed_age(p.get("feed"))
                    if age2 is not None and age2 > 60.0:
                        end_projection(w, sl, "仿真 feed 已经 %.0f s 没更新了" % age2)
                hits = []
                out = [] if auto else (w.js(MINE_HITS_JS) or [])
                if out:
                    try:
                        hits = json.loads(str(out[0]))
                    except Exception:
                        hits = []
                for key in hits:
                    key = str(key)
                    x, y = [int(float(v)) for v in key.split(",")[:2]]
                    if x < 0 or y < 0:
                        continue
                    if key in w._proj_seen:
                        continue
                    # 落在哪个场景的边界里, 就用哪个场景(连带它自己的 feed 和 marker 槽)
                    pick, anchor, label, feed_now, slot_i = None, None, "", None, None
                    for si, d in enumerate(getattr(w, "_dir_scenes", [])):
                        fx, fy, fw, fh = d["frame"]
                        if fx <= x < fx + fw and fy <= y < fy + fh:
                            pick, anchor, label = d["path"], d["anchor"], d["label"]
                            feed_now, slot_i = d.get("feed"), si
                            break
                    if not getattr(w, "_dir_feeds", None):
                        chat(w, "这里没有配仿真 feed，放地雷不会有影子")
                        w._proj_seen.add(key)
                        continue
                    if pick is None:
                        # 场景是固定排布的, 框外放雷没有"最近的场景"可言 —— 直接拒绝,
                        # 免得复刻出来的东西和框对不上(以前会以雷为圆心乱铺)
                        chat(w, "这颗地雷没落在任何沙盘边界里，先在框里放才会有投影")
                        w._proj_seen.add(key)
                        continue
                    if not feed_now:
                        chat(w, "这个沙盘没有配仿真 feed，先给 --watch-feed 补一条")
                        w._proj_seen.add(key)
                        continue
                    age = feed_age(feed_now)
                    if age is None:
                        chat(w, "还没看到仿真在跑（%s 不存在），先起 mlogsim"
                             % os.path.basename(feed_now))
                        w._proj_seen.add(key)
                        continue
                    if age > 25.0:
                        chat(w, "仿真 feed %s 已经 %.0f s 没更新了，先把 mlogsim 起起来再放雷"
                             % (os.path.basename(feed_now), age))
                        w._proj_seen.add(key)
                        continue
                    r = project_at(w, x, y, feed_now, pick, anchor=anchor, slot=slot_i)
                    print("[info] 投影 %s @(%d,%d) slot %d, 建筑 %d 块, 仿真帧龄 %.1fs"
                          % (label or "-", x, y, slot_i, r.get("placed", 0), age),
                          flush=True)
            except Exception as exc:
                print("[warn] 投影导演: %s" % exc, flush=True)

    th = threading.Thread(target=loop, name="projection-director", daemon=True)
    th.start()
    w._dir_thread = th
    return True


DOOR_ENTER_JS = r"""
var dpl = null;
var dwant = %(who)s;
for(var di=0;di<Groups.player.size();di++){
  var dcand = Groups.player.index(di);
  if(dwant == null || dwant == '' || String(dcand.name).indexOf(dwant) >= 0){ dpl = dcand; break; }
}
if(dpl == null){ sb.append('NOPLAYER'); }
/* 先算结果再追加: _doorAct 会铺场景并往 sb 里写 B/I/L/U 行,
   链式 append 会让那些行插在 'R\t' 之后, 解析时拿到的是场景的第一行 */
else { var rres = String(_doorAct(dpl, %(x)d, %(y)d)); sb.append('R\t').append(rres); }
"""

BUILDS_JS = r"""
var n=0, lim=%(limit)d, R=%(R)f, CX=%(CX)f, CY=%(CY)f;
var TF=%(team)s, BF=%(block)s;
var w=Vars.world, W=w.width(), H=w.height();
var x0=0, y0=0, x1=W-1, y1=H-1;
if(R>0){
  x0=Math.max(0, Math.floor(CX-R)); x1=Math.min(W-1, Math.ceil(CX+R));
  y0=Math.max(0, Math.floor(CY-R)); y1=Math.min(H-1, Math.ceil(CY+R));
}
outer:
for(var ty=y0; ty<=y1; ty++){
  for(var tx=x0; tx<=x1; tx++){
    var t=w.tile(tx,ty); var b = t==null ? null : t.build;
    if(b==null || !b.isValid()) continue;
    /* 多格建筑在每格都会命中, 只在它自己的原点格报一次 */
    if(b.tile.x!=tx || b.tile.y!=ty) continue;
    if(TF!=null && b.team.name!=TF) continue;
    if(BF!=null && b.block.name!=BF) continue;
    var tot=-1, cap=-1;
    try{ if(b.items!=null){ tot=b.items.total(); } }catch(e){}
    /* v160 的 itemCapacity 在 Block 上, ItemModule 已经没有 capacity 字段/方法 */
    try{ cap = b.block.itemCapacity; }catch(e){}
    sb.append(b.block.name).append('\t').append(b.team.name).append('\t')
      .append(b.tile.x).append('\t').append(b.tile.y).append('\t')
      .append(Math.round(b.health)).append('\t').append(tot).append('\t').append(cap).append('\n');
    if(++n>=lim) break outer;
  }
}
if(n>=lim) sb.append('TRUNC\t').append(lim).append('\n');
"""


BUILDING_AT_JS = r"""
var t=Vars.world.tile(%(x)d, %(y)d);
var b = t==null ? null : t.build;
if(b!=null && b.isValid()){
  var tot=-1, cap=-1;
  try{ if(b.items!=null){ tot=b.items.total(); } }catch(e){}
  try{ cap = b.block.itemCapacity; }catch(e){}
  sb.append(b.block.name).append('\t').append(b.team.name).append('\t')
    .append(b.tile.x).append('\t').append(b.tile.y).append('\t')
    .append(Math.round(b.health)).append('\t').append(tot).append('\t').append(cap).append('\n');
}
"""


_NUM = re.compile(r"^-?\d+(\.\d+)?$")


def coerce(v: str):
    """把 JS 拼出来的 "149.0" 还原成 149; 非数字原样返回."""
    if isinstance(v, str) and _NUM.match(v):
        f = float(v)
        return int(f) if f.is_integer() else f
    return v


def units_table(rows: list[dict]) -> str:
    """把 units 的 JSON 行渲染成对齐的纯文本表（给人/agent 直接读）。"""
    if not rows:
        return "(no units)"
    ctrl_names = {0: "free", 1: "logic", 2: "player", 3: "command"}
    body = []
    for r in rows:
        item = r.get("item")
        carry = r.get("carry")
        cap = r.get("itemCapacity")
        kit = "-" if item in (None, "-", "") else "%s %s/%s" % (item, carry, cap)
        ctrl = ctrl_names.get(r.get("controlled"), str(r.get("controlled")))
        body.append([
            str(r.get("id")), str(r.get("type")),
            "%s,%s" % (r.get("x"), r.get("y")),
            str(r.get("controller")), kit,
            str(r.get("flag")), ctrl,
            "1" if r.get("mining") == 1 else "0",
            "1" if r.get("boosting") == 1 else "0",
            "%s/%s" % (r.get("health"), r.get("maxHealth")),
        ])
    head = ["id", "type", "tile", "controller", "items", "flag", "ctrl", "mine", "boost", "hp"]
    widths = [max(len(head[i]), *(len(row[i]) for row in body)) for i in range(len(head))]
    fmt = "  ".join("%-" + str(width) + "s" for width in widths)
    return "\n".join([fmt % tuple(head)] + [fmt % tuple(row) for row in body])


def parse_tsv(lines: list[str], cols: list[str]) -> dict:
    rows, trunc = [], False
    for ln in lines:
        parts = ln.split("\t")
        if parts[0] == "TRUNC":
            trunc = True
            continue
        if parts[0] == "ERR":
            raise RuntimeError(ln[4:])
        rows.append({k: coerce(v) for k, v in zip(cols, parts)})
    return {"rows": rows, "count": len(rows), "truncated": trunc}


PLACE_JS = r"""
var blk = Vars.content.block('%(block)s');
var t = Vars.world.tile(%(x)d, %(y)d);
if(blk == null){ sb.append('ERR\tno such block: %(block)s'); }
else if(t == null){ sb.append('ERR\ttile out of range'); }
else {
  try{
    t.setNet(blk, Vars.state.rules.defaultTeam, 0);
    var b = t.build;
    if(b != null){ b.enabled = true; }
    sb.append('OK\t'+blk.name+'\t'+%(x)d+'\t'+%(y)d);
  }catch(e){ sb.append('ERR\t'+e); }
}
"""

CLEAR_JS = r"""
var t = Vars.world.tile(%(x)d, %(y)d);
if(t == null){ sb.append('ERR\ttile out of range'); }
else { try{ t.setNet(Vars.content.block('air')); sb.append('OK'); }catch(e){ sb.append('ERR\t'+e); } }
"""

SPAWN_JS = r"""
var ty = Vars.content.unit('%(type)s');
if(ty == null){ sb.append('ERR\tno such unit type'); }
else {
  var team = null, TA = Packages.mindustry.game.Team.all;
  for(var i = 0; i < TA.length; i++){ if(TA[i].name == '%(team)s'){ team = TA[i]; break; } }
  if(team == null){ sb.append('ERR\tno such team'); }
  else {
    var cap = Vars.state.rules.unitCap, have = Packages.mindustry.gen.Groups.unit.size();
    var cx = %(cx)f * 8, cy = %(cy)f * 8, r = %(radius)f * 8, n = 0;
    for(var k = 0; k < %(count)d; k++){
      if(have + n >= cap){ sb.append('ERR\tunit cap reached'); break; }
      /* golden-angle spiral: 防止单位叠在同一个点互相挤开 */
      var ang = k * 2.39996323, rr = %(count)d <= 1 ? 0 : r * Math.sqrt(k / %(count)d);
      var u = ty.spawn(team, cx + Math.cos(ang) * rr, cy + Math.sin(ang) * rr);
      if(u == null){ sb.append('ERR\tspawn returned null'); break; }
      n++;
      sb.append('U\t').append(u.id).append('\t').append(u.type.name).append('\t').append(u.team.name)
        .append('\t').append(Math.round(u.x / 8)).append('\t').append(Math.round(u.y / 8)).append('\n');
    }
    sb.append('SPAWNED\t').append(n).append('\t').append(ty.name);
  }
}
"""

KILLUNITS_JS = r"""
var G = Packages.mindustry.gen.Groups.unit, n = 0, kept = 0, R = %(radius)f, CX = %(cx)f, CY = %(cy)f;
var TF = %(team)s;
for(var i = G.size() - 1; i >= 0; i--){
  var u = G.index(i); if(u == null) continue;
  if(%(keep_player)d == 1){
    var ctl = null; try{ ctl = u.controller(); }catch(e){}
    if(ctl instanceof Packages.mindustry.gen.Player){ kept++; continue; }
  }
  if(TF != null && u.team.name != TF){ kept++; continue; }
  if(R > 0){ var dx = u.x / 8 - CX, dy = u.y / 8 - CY; if(dx * dx + dy * dy > R * R){ kept++; continue; } }
  try{ u.kill(); n++; }catch(e){}
}
sb.append('KILLED\t').append(n).append('\t').append(kept);
"""

CLEARBUILDS_JS = r"""
var G = Packages.mindustry.gen.Groups.build, n = 0, kept = 0, R = %(radius)f, CX = %(cx)f, CY = %(cy)f;
var air = Vars.content.block('air');
for(var i = G.size() - 1; i >= 0; i--){
  var b = G.index(i); if(b == null) continue;
  if(%(keepcore)d == 1 && b.block instanceof Packages.mindustry.world.blocks.storage.CoreBlock){ kept++; continue; }
  if(R > 0){ var dx = b.x / 8 - CX, dy = b.y / 8 - CY; if(dx * dx + dy * dy > R * R){ kept++; continue; } }
  try{ b.tile.setNet(air); n++; }catch(e){}
}
sb.append('CLEARED\t').append(n).append('\t').append(kept);
"""

LOGIC_LIST_JS = r"""
var n=0, lim=%(limit)d, R=%(R)f, CX=%(CX)f, CY=%(CY)f;
var w=Vars.world, W=w.width(), H=w.height();
var x0=0, y0=0, x1=W-1, y1=H-1;
if(R>0){
  x0=Math.max(0, Math.floor(CX-R)); x1=Math.min(W-1, Math.ceil(CX+R));
  y0=Math.max(0, Math.floor(CY-R)); y1=Math.min(H-1, Math.ceil(CY+R));
}
outer:
for(var ty=y0; ty<=y1; ty++){
  for(var tx=x0; tx<=x1; tx++){
    var t=w.tile(tx,ty); var b = t==null ? null : t.build;
    if(b==null || !b.isValid()) continue;
    if(b.getClass().getName().indexOf('LogicBlock$')<0) continue;
    var cl=0, vn=0;
    try{ cl = b.code==null ? 0 : b.code.length; }catch(e){}
    try{ vn = b.executor.vars.length; }catch(e){}
    sb.append(b.tile.x).append('\t').append(b.tile.y).append('\t')
      .append(b.block.name).append('\t').append(cl).append('\t').append(vn).append('\n');
    if(++n>=lim) break outer;
  }
}
if(n>=lim) sb.append('TRUNC\t').append(lim).append('\n');
"""

LOGIC_GET_JS = r"""
var t=Vars.world.tile(%(x)d, %(y)d);
var b = t==null ? null : t.build;
if(b==null){ sb.append('ERR\tno building at %(x)d,%(y)d'); }
else if(b.getClass().getName().indexOf('LogicBlock$')<0){ sb.append('ERR\tnot a logic block: '+b.block.name); }
else {
  var w=new java.io.PrintWriter('%(res)s','UTF-8');
  w.print(b.code==null ? '' : b.code); w.close();
  sb.append('OK');
}
"""

LOGIC_SET_JS = r"""
var t=Vars.world.tile(%(x)d, %(y)d);
var b = t==null ? null : t.build;
if(b==null){ sb.append('ERR\tno building at %(x)d,%(y)d'); }
else if(b.getClass().getName().indexOf('LogicBlock$')<0){ sb.append('ERR\tnot a logic block: '+b.block.name); }
else {
  try{
    var src=new java.lang.String(java.nio.file.Files.readAllBytes(java.nio.file.Paths.get('%(src)s')), 'UTF-8');
    b.updateCode(src);
    sb.append('OK\t'+b.code.length);
  }catch(e){ sb.append('ERR\t'+e); }
}
"""

LOGIC_VARS_JS = r"""
var t=Vars.world.tile(%(x)d, %(y)d);
var b = t==null ? null : t.build;
if(b==null){ sb.append('ERR\tno building at %(x)d,%(y)d'); }
else if(b.getClass().getName().indexOf('LogicBlock$')<0){ sb.append('ERR\tnot a logic block: '+b.block.name); }
else {
  var V=b.executor.vars;
  for(var k=0;k<V.length;k++){
    var v=V[k], s='';
    try{ s = v.isobj ? String(v.objval) : String(v.numval); }catch(e){ s='?'; }
    sb.append(v.name).append('\t').append(s).append('\n');
  }
}
"""

SCHEMATIC_PLACE_JS = r"""
var S = Packages.mindustry.game.Schematics;
var bytes = null, src = %(src)s;
try{
  if(src != null && src.indexOf('b64:') == 0){
    bytes = java.util.Base64.getDecoder().decode(src.substring(4));
  }else{
    bytes = java.nio.file.Files.readAllBytes(java.nio.file.Paths.get(String(src)));
  }
}catch(e){ sb.append('ERR\tread: '+e+'\n'); }
if(bytes != null){
  var sch = null;
  try{ sch = S.read(new java.io.ByteArrayInputStream(bytes)); }
  catch(e){ sb.append('ERR\tparse: '+e+'\n'); }
  if(sch != null){
    var team = Vars.state.rules.defaultTeam, TN = %(team)s;
    if(TN != null){
      var TA = Packages.mindustry.game.Team.all;
      for(var q=0;q<TA.length;q++){ if(TA[q].name == TN){ team = TA[q]; break; } }
    }
    var ox = %(ox)s, oy = %(oy)s;
    if(ox < 0){ ox = Math.floor((Vars.world.width() - sch.width) / 2); }
    if(oy < 0){ oy = Math.floor((Vars.world.height() - sch.height) / 2); }
    var placed = 0, cfgs = 0, logic = 0, skipped = 0, failed = 0, cleared = 0, keptc = 0;
    var LB = Packages.mindustry.world.blocks.logic.LogicBlock;
    var AIR = Vars.content.block('air');
    /* 先清出目标矩形，避免旧建筑与蓝图重叠导致 setBlock 互相拆 */
    for(var cx = 0; cx < sch.width; cx++){
      for(var cy = 0; cy < sch.height; cy++){
        var ct = Vars.world.tile(ox + cx, oy + cy);
        if(ct == null || ct.build == null) continue;
        /* 核心永不拆（拆了单位就没地方回货，玩家也会立刻发现） */
        var cb = ct.build;
        if(cb.block instanceof Packages.mindustry.world.blocks.storage.CoreBlock){ keptc++; continue; }
        try{ ct.setNet(AIR); cleared++; }catch(e){}
      }
    }
    /* 两遍：先放普通方块，再放处理器 —— readCompressed 通过 world.build(x,y) 解析链接，
       链接目标必须已经存在，否则链接变 null。 */
    for(var pass = 0; pass < 2; pass++){
      for(var i = 0; i < sch.tiles.size; i++){
        var st = sch.tiles.get(i);
        var isLogic = false;
        try{ isLogic = (st.block instanceof LB); }catch(e){ isLogic = false; }
        if((pass == 0) == isLogic) continue;
        var tx = ox + st.x, ty = oy + st.y;
        var t = Vars.world.tile(tx, ty);
        if(t == null){ skipped++; continue; }
        var bn = t.build;
        if(bn != null && (bn.tile.x != tx || bn.tile.y != ty)){ skipped++; continue; }
        try{
          t.setNet(st.block, team, st.rotation);
          var b = t.build;
          if(b == null){ skipped++; continue; }
          b.enabled = true;
          placed++;
          if(isLogic){ logic++; }
          if(st.config != null){
            if(isLogic){
              b.readCompressed(st.config, true); cfgs++;
            }else{
              var cons = b.block.configurations.get(st.config.getClass());
              if(cons != null){ cons.get(b, st.config); cfgs++; }
              else { b.configureAny(st.config); cfgs++; }
            }
          }
        }catch(e){ failed++; sb.append('ERR\tplace '+tx+','+ty+': '+e+'\n'); }
      }
    }
    var nm = '-'; try{ nm = String(sch.tags.get('name')); }catch(e){}
    sb.append('OK\tplaced='+placed+'\tlogic='+logic+'\tcfg='+cfgs+'\tskipped='+skipped+'\tfailed='+failed+'\tcleared='+cleared+'\tkeptcore='+keptc+'\tw='+sch.width+'\th='+sch.height+'\tx='+ox+'\ty='+oy+'\tname='+nm+'\n');
    sb.append('TILES\t'+sch.tiles.size+'\n');
  }
}
"""

SCHEMATIC_SAVE_JS = r"""
var seq = new Packages.arc.struct.Seq();
var x0 = %(x)d, y0 = %(y)d, w = %(w)d, h = %(h)d, n = 0;
for(var dx = 0; dx < w; dx++){
  for(var dy = 0; dy < h; dy++){
    var t = Vars.world.tile(x0 + dx, y0 + dy);
    if(t == null || t.build == null) continue;
    var b = t.build;
    if(b.block == null || b.block.name == 'air') continue;
    if(b.tile.x != x0 + dx || b.tile.y != y0 + dy) continue;   /* 多格建筑只在原点存一份 */
    var cfg = null; try{ cfg = b.config(); }catch(e){ cfg = null; }
    var rot = 0; try{ rot = b.rotation; }catch(e){ rot = 0; }
    seq.add(new Packages.mindustry.game.Schematic$Stile(b.block, dx, dy, cfg, rot));
    n++;
  }
}
var tags = new Packages.arc.struct.StringMap();
tags.put('name', %(name)s);
tags.put('author', %(author)s);
var sch = new Packages.mindustry.game.Schematic(seq, tags, %(w)d, %(h)d);
var out = null;
try{
  out = new java.io.FileOutputStream(%(path)s);
  Packages.mindustry.game.Schematics.write(sch, out);
  sb.append('OK\t'+n+'\t'+%(path)s+'\n');
}catch(e){ sb.append('ERR\twrite: '+e+'\n'); }
finally{ try{ if(out != null) out.close(); }catch(e2){} }
"""

SCHEMATIC_LIST_JS = r"""
var all = Vars.schematics == null ? null : Vars.schematics.all();
if(all == null || all.size == 0){
  var dir = new java.io.File(%(dir)s);
  var fs = dir.listFiles();
  if(fs != null){
    for(var i=0;i<fs.length;i++){
      var fn = String(fs[i].getName());
      if(fn.length > 5 && fn.substring(fn.length-5) == '.msch'){
        sb.append(fn.substring(0, fn.length-5)).append('\t').append(fs[i].length).append('\tfile\n');
      }
    }
  }
}else{
  for(var i=0;i<all.size;i++){
    var s = all.get(i);
    var nm='-', au='-';
    try{ nm = String(s.tags.get('name')); }catch(e){}
    try{ au = String(s.tags.get('author')); }catch(e){}
    sb.append(nm).append('\t').append(s.width).append('x').append(s.height).append('\t').append(au).append('\n');
  }
}
"""

MAPS_JS = r"""
var ms = Vars.maps.all();
for(var i=0;i<ms.size;i++){
  var m=ms.get(i);
  var f='-'; try{ f = m.file==null ? '-' : String(m.file.name()); }catch(e){}
  sb.append(m.name()).append('\t').append(f).append('\n');
}
"""



class API(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def make_handler(world: World, stop_cb):
    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            for raw in self.rfile:
                try:
                    req = json.loads(raw.decode("utf-8"))
                except Exception as e:
                    self._send({"ok": False, "error": "bad json: %s" % e})
                    continue
                try:
                    resp = dispatch(world, req, stop_cb)
                except Exception as e:
                    resp = {"ok": False, "error": "%s: %s" % (type(e).__name__, e)}
                self._send(resp)

        def _send(self, obj):
            try:
                self.wfile.write((json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8"))
                self.wfile.flush()
            except Exception:
                pass
    return Handler


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
    if op in ("ping", ""):
        return {"ok": True, "pid": os.getpid(), "java": w.proc.pid if w.proc else None,
                "hosted": getattr(w, "hosted", False), "map": w.map_name,
                "gamePort": w.game_port, "uptime": round(time.time() - w.started, 1),
                "dataDir": DATA}
    if op == "status":
        raw = {}
        for ln in w.js(STATUS_JS):
            k, _, v = ln.partition("=")
            raw[k] = v
        def num(k, cast=int, default=None):
            try:
                return cast(float(raw[k]))
            except Exception:
                return default

        def flag(k):
            try:
                return float(raw[k]) != 0
            except Exception:
                return False
        d = {
            "map": raw.get("map"),
            "mode": raw.get("mode"),
            "wave": num("wave", int),
            "waveIn": num("waveIn", int),
            "tick": num("tick", int),
            "width": num("w", int),
            "height": num("h", int),
            "players": num("players", int, 0),
            "units": num("units", int, 0),
            "buildings": num("builds", int, 0),
            # Rhino 把 ?1:0 打印成 "1.0"，字符串比较永远不等 —— 按数值判
            "paused": flag("paused"),
            "infiniteResources": flag("infinite"),
            "gamePort": w.game_port,
            "uptime": round(time.time() - w.started, 1),
            "dataDir": DATA,
        }
        return {"ok": True, **d}
    if op == "maps":
        rows = []
        for ln in w.js(MAPS_JS):
            name, _, f = ln.partition("\t")
            rows.append({"name": name, "file": f})
        return {"ok": True, "maps": rows, "count": len(rows)}
    if op == "players":
        return {"ok": True, **parse_tsv(w.js(PLAYERS_JS), ["name", "team", "x", "y", "admin"])}
    if op == "units":
        body = UNITS_JS % {"limit": int(req.get("limit") or 200),
                           "R": float(req.get("radius") or 0),
                           "CX": float(req.get("x") or 0), "CY": float(req.get("y") or 0),
                           "team": json.dumps(req.get("team")),
                           "type": json.dumps(req.get("type"))}
        res = {"ok": True, **parse_tsv(w.js(body), ["id", "type", "team", "x", "y",
                                                  "health", "maxHealth", "dead", "controller",
                                                  "item", "carry", "itemCapacity",
                                                  "elevation", "controlTimer",
                                                  "flag", "controlled", "mining", "boosting"])}
        if str(req.get("format") or "").lower() == "table":
            res["table"] = units_table(res["rows"])
        return res
    if op == "unit":
        uid = int(req.get("id"))
        raw = {}
        for ln in w.js(UNIT_JS % {"id": uid}):
            if ln.startswith("ERR"):
                return {"ok": False, "error": ln[4:]}
            k, _, v = ln.partition("=")
            raw[k] = v
        return {"ok": True, **{k: coerce(v) for k, v in raw.items()}}
    if op in ("chat", "chat_log", "messages"):
        since = int(req.get("since") or 0)
        limit = int(req.get("limit") or 80)
        rows, seq = [], since
        for ln in w.js(CHAT_JS % {"since": since, "limit": limit}):
            if ln.startswith("ERR"):
                return {"ok": False, "error": ln[4:]}
            if ln.startswith("NOSETUP"):
                return {"ok": False, "error": "chat hook not installed (daemon predates chat listener)"}
            if ln.startswith("SEQ\t"):
                seq = int(float(ln.split("\t")[1]))
                continue
            p = ln.split("\t")
            if len(p) >= 4:
                rows.append({"seq": int(float(p[0])), "tick": int(float(p[1])),
                             "player": p[2], "message": "\t".join(p[3:])})
        return {"ok": True, "rows": rows, "count": len(rows), "since": since, "nextSeq": seq}
    if op in ("push", "agent_push"):
        drain = 1 if req.get("drain", True) else 0
        rows, seq = [], 0
        for ln in w.js(PUSH_JS % {"drain": drain}):
            if ln.startswith("NOSETUP"):
                return {"ok": False, "error": "push hook not installed (restart the daemon)"}
            if ln.startswith("SEQ\t"):
                seq = int(float(ln.split("\t")[1]))
                continue
            ln = ln.strip()
            if not ln:
                continue
            try:
                rows.append(json.loads(ln))
            except Exception:
                rows.append({"raw": ln})
        return {"ok": True, "rows": rows, "count": len(rows), "nextSeq": seq}
    if op == "changes":
        since = int(req.get("since") or 0)
        limit = int(req.get("limit") or 200)
        rows, seq = [], since
        for ln in w.js(CHANGES_JS % {"since": since, "limit": limit}):
            if ln.startswith("SEQ\t"):
                # Rhino 把 number 交给 StringBuilder.append(double) 会打成 "12.0"
                seq = int(float(ln.split("\t")[1]))
                continue
            if ln.startswith("NOSETUP"):
                return {"ok": False, "error": "event listeners not installed (daemon predates EV_INSTALL_JS)"}
            p = ln.split("\t")
            if len(p) < 8:
                continue
            extra = p[7]
            size = 0
            if extra.startswith("size="):
                try:
                    size = int(float(extra[5:]))
                except Exception:
                    size = 0
                extra = ""
            rows.append({"kind": p[0], "seq": int(float(p[1])), "tick": int(float(p[2])),
                         "x": int(p[3]), "y": int(p[4]), "block": p[5],
                         "team": p[6], "size": size, "extra": extra})
        # 多格方块放置时相邻格会各报一条 air, 只保留原点那一条 + 真正的拆除
        covered = set()
        for r in rows:
            if r["kind"] == "P" and r["size"] > 1:
                for dx in range(r["size"]):
                    for dy in range(r["size"]):
                        if dx or dy:
                            covered.add((r["tick"], r["x"] + dx, r["y"] + dy))
        rows = [r for r in rows
                if not (r["kind"] == "B" and (r["tick"], r["x"], r["y"]) in covered)]
        return {"ok": True, "rows": rows, "count": len(rows), "since": since, "nextSeq": seq}
    if op == "buildings":
        body = BUILDS_JS % {"limit": int(req.get("limit") or 200),
                            "R": float(req.get("radius") or 0),
                            "CX": float(req.get("x") or 0), "CY": float(req.get("y") or 0),
                            "team": json.dumps(req.get("team")),
                            "block": json.dumps(req.get("block"))}
        return {"ok": True, **parse_tsv(w.js(body), ["block", "team", "x", "y",
                                                    "health", "items", "capacity"])}
    if op == "building":
        x, y = int(req.get("x")), int(req.get("y"))
        out = w.js(BUILDING_AT_JS % {"x": x, "y": y})
        rows = parse_tsv(out, ["block", "team", "x", "y", "health", "items", "capacity"])
        if not rows["rows"]:
            return {"ok": True, "block": None, "x": x, "y": y, "found": False}
        return {"ok": True, "found": True, **rows["rows"][0],
                "origin": {"x": rows["rows"][0]["x"], "y": rows["rows"][0]["y"]}}
    if op == "place":
        blk = str(req.get("block") or "")
        if not blk:
            return {"ok": False, "error": "empty block"}
        audit("place", block=blk, x=req.get("x"), y=req.get("y"))
        out = w.js(PLACE_JS % {"block": blk, "x": int(req.get("x")), "y": int(req.get("y"))})
        if out and out[0].startswith("ERR"):
            return {"ok": False, "error": out[0][4:]}
        return {"ok": True, "block": blk, "x": int(req.get("x")), "y": int(req.get("y"))}
    if op == "clear":
        audit("clear", x=req.get("x"), y=req.get("y"))
        out = w.js(CLEAR_JS % {"x": int(req.get("x")), "y": int(req.get("y"))})
        if out and out[0].startswith("ERR"):
            return {"ok": False, "error": out[0][4:]}
        return {"ok": True, "x": int(req.get("x")), "y": int(req.get("y"))}
    if op == "spawn":
        ty = str(req.get("type") or "").strip()
        if not ty:
            return {"ok": False, "error": "empty type"}
        cnt = max(1, int(req.get("count") or 1))
        audit("spawn", type=ty, count=cnt, x=req.get("x"), y=req.get("y"))
        body = SPAWN_JS % {"type": ty, "team": str(req.get("team") or "sharded"),
                           "count": cnt, "cx": float(req.get("x") or 0),
                           "cy": float(req.get("y") or 0),
                           "radius": float(req.get("radius") or 3)}
        spawned, units = 0, []
        for ln in w.js(body):
            if ln.startswith("ERR"):
                return {"ok": False, "error": ln[4:].split("\t", 1)[-1], "spawned": spawned}
            parts = ln.split("\t")
            if parts[0] == "SPAWNED":
                spawned = int(coerce(parts[1]) or 0)
            elif parts[0] == "U":
                units.append({"id": coerce(parts[1]), "type": parts[2], "team": parts[3],
                              "x": coerce(parts[4]), "y": coerce(parts[5])})
        return {"ok": True, "spawned": spawned, "units": units, "count": len(units)}
    if op == "killunits":
        audit("killunits", team=req.get("team"))
        body = KILLUNITS_JS % {"keep_player": 0 if req.get("include_players") else 1,
                               "team": ("'%s'" % req.get("team")) if req.get("team") else "null",
                               "cx": float(req.get("x") or 0), "cy": float(req.get("y") or 0),
                               "radius": float(req.get("radius") or 0)}
        out = w.js(body)
        if out and out[0].startswith("ERR"):
            return {"ok": False, "error": out[0][4:]}
        parts = (out[0] if out else "").split("\t")
        return {"ok": True, "killed": coerce(parts[1]) if len(parts) > 1 else 0,
                "kept": coerce(parts[2]) if len(parts) > 2 else 0}
    if op == "clearbuilds":
        keepcore = 1 if req.get("keepcore", True) else 0
        audit("clearbuilds", keepcore=keepcore, radius=req.get("radius"))
        body = CLEARBUILDS_JS % {"keepcore": keepcore,
                                 "cx": float(req.get("x") or 0), "cy": float(req.get("y") or 0),
                                 "radius": float(req.get("radius") or 0)}
        out = w.js(body)
        if out and out[0].startswith("ERR"):
            return {"ok": False, "error": out[0][4:]}
        parts = (out[0] if out else "").split("\t")
        return {"ok": True, "cleared": coerce(parts[1]) if len(parts) > 1 else 0,
                "kept": coerce(parts[2]) if len(parts) > 2 else 0}
    if op == "switch":
        target = str(req.get("map") or w.map_name or "").strip()
        if not target:
            return {"ok": False, "error": "no map name"}
        return switch_map(w, target, audit)
    if op == "reset":
        # 默认走「不踢人」的换图路径；hard=true 才 stop+host（会断开所有玩家）
        if not req.get("hard"):
            target = str(req.get("map") or w.map_name or "").strip()
            if not target:
                return {"ok": False, "error": "no map name"}
            return switch_map(w, target, audit)
        audit("reset", map=w.map_name, hard=True)
        w.console("stop", quiet=0.6, timeout=30)
        res = w.console("host " + (w.map_name or ""), quiet=1.0, timeout=180)
        text = "\n".join(res.get("lines") or [])
        if "Opened a server" not in text:
            return {"ok": False, "error": "rehost failed", "lines": res.get("lines")}
        w.hosted = True
        try:
            w.js("var r=Vars.state.rules; r.waves=false; r.infiniteResources=true; "
                 "r.canGameOver=false; r.logicUnitControl=true; sb.append(r.waves);")
        except Exception:
            pass
        return {"ok": True, "map": w.map_name, "lines": res.get("lines")[-3:]}
    if op == "logic":
        body = LOGIC_LIST_JS % {"limit": int(req.get("limit") or 40),
                                "R": float(req.get("radius") or 0),
                                "CX": float(req.get("x") or 0), "CY": float(req.get("y") or 0)}
        return {"ok": True, **parse_tsv(w.js(body), ["x", "y", "block", "codeLen", "vars"])}
    if op == "logic_code":
        x, y = int(req.get("x")), int(req.get("y"))
        res = "code-%s.txt" % uuid.uuid4().hex[:12]
        out = w.js(LOGIC_GET_JS % {"x": x, "y": y, "res": res})
        if out and out[0].startswith("ERR"):
            return {"ok": False, "error": out[0][4:]}
        code = w.take_file(res)
        return {"ok": True, "x": x, "y": y, "code": code,
                "lines": code.count("\n") + (0 if code.endswith("\n") or not code else 1)}
    if op == "logic_set":
        x, y = int(req.get("x")), int(req.get("y"))
        code = str(req.get("code") or "")
        audit("logic_set", x=x, y=y, bytes=len(code))
        src = w.put_file(code, "src")
        out = w.js(LOGIC_SET_JS % {"x": x, "y": y, "src": src})
        try:
            os.remove(os.path.join(DATA, src))
        except Exception:
            pass
        if out and out[0].startswith("ERR"):
            return {"ok": False, "error": out[0][4:]}
        return {"ok": True, "x": x, "y": y,
                "codeLen": coerce(out[0].partition("\t")[2]) if out else None}
    if op == "logic_vars":
        x, y = int(req.get("x")), int(req.get("y"))
        rows = []
        for ln in w.js(LOGIC_VARS_JS % {"x": x, "y": y}):
            if ln.startswith("ERR"):
                return {"ok": False, "error": ln[4:]}
            name, _, val = ln.partition("\t")
            rows.append({"name": name, "value": coerce(val)})
        return {"ok": True, "x": x, "y": y, "vars": rows, "count": len(rows)}
    if op == "schematic":
        src = req.get("src") or req.get("path") or ""
        if not src and req.get("b64"):
            src = "b64:" + str(req.get("b64")).strip()
        if not src:
            return {"ok": False, "error": "need src (path or b64)"}
        if not src.startswith("b64:") and not os.path.exists(src):
            # 裸名字: 先在 schematics 目录里找 <name>.msch / <name>
            for cand in (os.path.join(SCHEM_DIR, src), os.path.join(SCHEM_DIR, src + ".msch")):
                if os.path.exists(cand):
                    src = cand
                    break
        if not src.startswith("b64:"):
            src = os.path.abspath(src).replace("\\", "/")
        x = int(req["x"]) if req.get("x") is not None else -1
        y = int(req["y"]) if req.get("y") is not None else -1
        team = req.get("team")
        audit("schematic", src=str(src)[:120], x=x, y=y)
        body = SCHEMATIC_PLACE_JS % {"src": json.dumps(str(src)), "ox": x, "oy": y,
                                     "team": json.dumps(team)}
        rows, ok_line, tiles = [], None, 0
        for ln in w.js(body, timeout=120):
            if ln.startswith("ERR"):
                return {"ok": False, "error": ln[4:]}
            if ln.startswith("OK\t"):
                ok_line = ln
            elif ln.startswith("TILES\t"):
                tiles = int(coerce(ln.split("\t")[1]) or 0)
        if not ok_line:
            return {"ok": False, "error": "no result from schematic placement"}
        kv = {}
        for part in ok_line.split("\t")[1:]:
            k, _, v = part.partition("=")
            kv[k] = coerce(v) if v != "" else None
        kv["tiles"] = tiles
        return {"ok": True, **kv}
    if op == "schematic_save":
        x, y = int(req.get("x")), int(req.get("y"))
        ww = int(req.get("w") or 0)
        hh = int(req.get("h") or 0)
        name = str(req.get("name") or "schem").strip()
        if ww <= 0 or hh <= 0:
            return {"ok": False, "error": "need w,h"}
        if ww > 128 or hh > 128:
            return {"ok": False, "error": "schematic max 128x128"}
        safe = "".join(c for c in name if c not in '\\/:*?"<>|').strip() or "schem"
        target = os.path.join(SCHEM_DIR, safe + ".msch")
        audit("schematic_save", x=x, y=y, w=ww, h=hh, name=safe)
        body = SCHEMATIC_SAVE_JS % {"x": x, "y": y, "w": ww, "h": hh,
                                    "name": json.dumps(name),
                                    "author": json.dumps("DeepSeek"),
                                    "path": json.dumps(target.replace("\\", "/"))}
        out = w.js(body, timeout=120)
        if out and out[0].startswith("ERR"):
            return {"ok": False, "error": out[0][4:]}
        parts = (out[0] if out else "").split("\t")
        # 让服务端内存里的蓝图表也能看到（客户端列表走磁盘，不依赖这个）
        try:
            w.js("try{ Vars.schematics.load(); sb.append('RELOADED'); }catch(e){ sb.append('ERR '+e); }")
        except Exception:
            pass
        return {"ok": True, "path": target, "tiles": coerce(parts[1]) if len(parts) > 1 else 0,
                "name": safe,
                "bytes": os.path.getsize(target) if os.path.exists(target) else None}
    if op == "schematics":
        rows = []
        for ln in w.js(SCHEMATIC_LIST_JS % {"dir": json.dumps(SCHEM_DIR.replace("\\", "/"))}):
            if ln.startswith("ERR"):
                return {"ok": False, "error": ln[4:]}
            p = ln.split("\t")
            if len(p) >= 3:
                rows.append({"name": p[0], "size": p[1], "author": p[2]})
        return {"ok": True, "items": rows, "count": len(rows)}
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
    if op == "arm":
        # 开启"玩家放地雷即投影"的监听: 不自己放雷, 只等玩家放
        feed = str(req.get("feed") or getattr(w, "mirror_feed", None) or "")
        raw_feeds0 = req.get("feeds")
        if isinstance(raw_feeds0, str):
            raw_feeds0 = [raw_feeds0]
        if not feed and not (raw_feeds0 or []):
            return {"ok": False, "error": "need feed path (mlogsim --push)"}
        # 重复 arm = 换场景/换边界: 先停旧导演、擦掉旧边界, 再起新的(不重启世界)
        if getattr(w, "_dir_started", False):
            w._dir_stop = True
            w._dir_started = False
            time.sleep(1.5)
            if getattr(w, "_dir_frames", False):
                try:
                    frame_clear(w)
                except Exception:  # noqa: BLE001
                    pass
        # scene 可以是单个路径, 也可以是路径数组(多场景: 各自有矩形边界)
        raw_scenes = req.get("scenes")
        if raw_scenes is None:
            raw_scenes = req.get("scene")
        if isinstance(raw_scenes, str):
            raw_scenes = [raw_scenes] if raw_scenes else []
        scene_paths = [str(s) for s in (raw_scenes or [])]
        raw_feeds = req.get("feeds")
        if raw_feeds is None:
            raw_feeds = req.get("feeds_arr")
        if isinstance(raw_feeds, str):
            raw_feeds = [raw_feeds]
        feed_list = [str(f) for f in (raw_feeds or []) if f] or ([feed] if feed else [])
        started = projection_director(w, feed_list[0] if feed_list else feed, None,
                                     scenes=scene_paths,
                                     frames=bool(req.get("frames", True)),
                                     frame_floor=str(req.get("frame_floor")
                                                     or "marker"),
                                     at_cell=int(req.get("frame_cell") or 64),
                                     feeds=feed_list,
                                     auto=bool(req.get("auto", True)))
        audit("arm", feed=feed, scene=scene_paths)
        age = feed_age(feed)
        return {"ok": True, "director": started, "feed": feed,
                "scenes": [{"path": d["path"], "frame": d["frame"],
                            "anchor": d["anchor"]} for d in getattr(w, "_dir_scenes", [])],
                "age": age,
                "note": "把脉冲地雷放到想投影的位置（落在哪个框里就复刻哪个场景），放下即开始"}
    if op == "frames":
        # 场景边界: action=list 看 / clear 擦掉(可指定 scene 路径) / paint 重画
        act = str(req.get("action") or "list")
        if act == "list":
            out = w.js(FRAME_LIST_JS)
            return {"ok": True, "frames": (str(out[0]) if out else ""),
                    "scenes": [{"path": d["path"], "label": d["label"],
                                "frame": d["frame"], "anchor": d["anchor"]}
                               for d in getattr(w, "_dir_scenes", [])]}
        if act == "clear":
            n = frame_clear(w, req.get("scene"))
            return {"ok": True, "restored": n}
        if act == "paint":
            n = 0
            for d in getattr(w, "_dir_scenes", []):
                n += frame_paint(w, d["frame"], d["path"],
                                 step=int(req.get("step") or 1),
                                 radius=float(req.get("radius") or 7.0))
            return {"ok": True, "painted": n,
                    "scenes": [d["path"] for d in getattr(w, "_dir_scenes", [])]}
        return {"ok": False, "error": "action must be list|clear|paint"}
    if op == "projection":
        on = bool(req.get("on", True))
        if not on:
            # 关全部槽: 每块沙盘的影子一起收掉
            mirror_stop(w)
            return {"ok": True, "on": False}
        slot = int(req.get("slot") or 0)
        mir = _mirror_slot(w, slot)
        meta = {"feed": req.get("feed") or mir.get("feed")
                or getattr(w, "mirror_feed", None),
                "scene": req.get("scene"), "scene_at": req.get("at")}
        r = start_projection(w, meta, slot=slot)
        return r
    if op == "projstat":
        # 多槽: 每块沙盘一份 {slot, center, builds, feed, off}
        rows = []
        props = getattr(w, "_projs", None) or {}
        for sl in sorted(props.keys()):
            p = props[sl]
            mir = _mirror_slot(w, sl)
            rows.append({"slot": int(sl), "center": list(p.get("center") or []),
                         "builds": p.get("builds") or [],
                         "feed": p.get("feed"), "off": list(mir.get("off") or (0, 0)),
                         "scene": p.get("scene")})
        first = rows[0] if rows else {}
        return {"ok": True, "count": len(rows), "projections": rows,
                "slot": first.get("slot"),
                "center": first.get("center") or None,
                "builds": first.get("builds") or [],
                "feed": first.get("feed"),
                "off": first.get("off") or [0, 0],
                "director": bool(getattr(w, "_dir_started", False)),
                "seen": sorted(getattr(w, "_proj_seen", set()))}
    if op == "sblog":
        # 沙盘日志板: action=log 追加一行 / list 读当前面板文本 / clear 擦掉
        act = str(req.get("action") or ("log" if req.get("text") else "list")).lower()
        slot = int(req.get("slot") or 0)
        if act == "log":
            txt = str(req.get("text") or "").strip()
            if not txt:
                return {"ok": False, "error": "need text"}
            # 逻辑字体只有 ASCII: 非 ASCII 一律换掉, 免得面板上出现一串 ohno
            txt = "".join(ch if 32 <= ord(ch) < 127 else "?" for ch in txt)[:48]
            d = None
            for si, dd in enumerate(getattr(w, "_dir_scenes", []) or []):
                if si == slot:
                    d = dd
            rows = sb_event(w, slot, txt)
            try:
                sb_render(w, slot, d=d, age=feed_age((d or {}).get("feed")),
                          live=False, force=True)
            except Exception as exc:  # noqa: BLE001
                return {"ok": False, "error": "render failed: %s" % exc}
            return {"ok": True, "slot": slot, "lines": list(rows)}
        if act == "clear":
            n = sb_clear(w, slot if req.get("slot") is not None else None)
            try:
                w.js(SB_SWEEP_JS)
            except Exception:  # noqa: BLE001
                pass
            return {"ok": True, "cleared": n}
        out = {}
        win3 = max(FRAME_LIVE_MAX, float(getattr(w, "_dir_hold", 0.0) or 0.0))
        for si, dd in enumerate(getattr(w, "_dir_scenes", []) or []):
            ag = feed_age(dd.get("feed"))
            out[str(si)] = sb_lines(w, si, d=dd, age=ag,
                                    live=(ag is not None and ag <= win3))
        return {"ok": True, "panels": out}
    if op in ("door", "doors", "door_clear", "door_enter", "taps"):
        # 点击门：TapEvent 在任意方块上都会 fire（InputHandler.java:732-739），
        # 这里只登记「哪一格是哪扇门」，点下去的动作由 DOOR_ACT_JS 里的 _doorAct 做。
        if op == "taps":
            since = int(req.get("since") or 0)
            limit = int(req.get("limit") or 100)
            rows, seq = [], 0
            for ln in w.js(TAPS_JS % {"since": since, "limit": limit}):
                if ln.startswith("NOSETUP"):
                    return {"ok": False, "error": "event listeners not installed"}
                if ln.startswith("SEQ\t"):
                    seq = int(float(ln.split("\t")[1]))
                    continue
                q = ln.split("\t")
                if len(q) >= 5:
                    rows.append({"seq": int(float(q[0])), "tick": coerce(q[1]),
                                 "x": coerce(q[2]), "y": coerce(q[3]), "player": q[4]})
            return {"ok": True, "rows": rows, "count": len(rows), "nextSeq": seq}
        if op == "doors":
            rows = []
            for ln in w.js(DOORS_JS):
                if ln.startswith("COUNT\t"):
                    continue
                q = ln.split("\t")
                if len(q) >= 5:
                    rows.append({"tile": q[0], "kind": q[1], "unit": q[2],
                                 "target": q[3], "label": q[4]})
            return {"ok": True, "doors": rows, "count": len(rows)}
        if op == "door_clear":
            out = w.js(DOOR_CLEAR_JS)
            # 端掉的不仅是内存表: doors.json 不清会在下次重启时把旧门全"复活"
            try:
                with open(DOORS_FILE, "w", encoding="utf-8") as fh:
                    json.dump([], fh)
            except Exception:
                pass
            w._doors_meta = {}
            if out:
                return {"ok": True, "cleared": coerce(out[0].split("\t")[1])}
            return {"ok": False, "error": "no output"}
        x = int(req.get("x") or 0)
        y = int(req.get("y") or 0)
        if op == "door_enter":
            # 没有真人点击也能测: 直接替某个在线玩家执行一次门的动作
            who = req.get("who")
            out = w.js(DOOR_ENTER_JS % {"x": x, "y": y,
                                        "who": json.dumps(str(who) if who else None)})
            if not out:
                return {"ok": False, "error": "no output"}
            if out[0].startswith("NOPLAYER"):
                return {"ok": False, "error": "no player online"}
            line = next((ln for ln in out if ln.startswith("R\t")), out[-1])
            res = line.split("\t")[1] if "\t" in line else line
            audit("door_enter", x=x, y=y, result=res)
            return {"ok": True, "result": res}
        kind = str(req.get("kind") or "watch")
        unit = str(req.get("unit") or "poly")
        tx = int(req["tx"]) if req.get("tx") is not None else x
        ty = int(req["ty"]) if req.get("ty") is not None else y
        label = str(req.get("label") or kind)
        block = str(req.get("block") or "shock-mine")
        try:
            info = door_register(w, x, y, kind, unit, tx, ty, label, block,
                                 req.get("scene"))
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
        audit("door", x=x, y=y, kind=kind, unit=unit, tx=tx, ty=ty, label=label)
        chat_line("door", req, {"ok": True})
        res = {"ok": True}
        res.update(info)
        return res
    if op in ("mirror_state", "mirror_feed", "mirror_clear"):
        # 状态镜: 坐标由调用方给(mlogsim 仿真 / 脚本), 不读 Groups.unit
        if op == "mirror_feed":
            path = str(req.get("path") or "")
            if not path:
                return {"ok": False, "error": "need path"}
            if not os.path.isabs(path):
                path = os.path.join(ROOT, path)
            slot = int(req.get("slot") or 0)
            dx = float(req.get("dx") or 0)
            dy = float(req.get("dy") or 0)
            mirror_watch(w, path.replace("\\", "/"), slot=slot, dx=dx, dy=dy)
            audit("mirror_feed", path=path)
            return {"ok": True, "path": path, "slot": slot, "dx": dx, "dy": dy}
        if op == "mirror_clear":
            cleared = mirror_stop(w)
            audit("mirror_clear")
            return {"ok": True, "cleared": cleared}
        units = req.get("units")
        if units is None:
            fpath = str(req.get("file") or "")
            if not fpath:
                return {"ok": False, "error": "need units or file"}
            if not os.path.isabs(fpath):
                fpath = os.path.join(ROOT, fpath)
            with open(fpath, "r", encoding="utf-8") as fh:
                units = json.load(fh)
        r = mirror_push(w, units, float(req.get("dx") or 0), float(req.get("dy") or 0))
        audit("mirror_state", count=len(units))
        return r
    if op in ("mirror", "marker", "markers", "marker_clear"):
        # 标记镜: 世界标记(ObjectiveMarker)是服务端可下发的, 客户端直接画在世界上
        # —— 不占方块、不用显示屏、不依赖逐帧位置包(Call 里根本没有那种包).
        inst = w.js(MK_INSTALL_JS)
        if inst and inst[0].startswith("ERR"):
            return {"ok": False, "error": inst[0][4:]}
        if op == "markers":
            res = {}
            for ln in w.js(MK_LIST_JS):
                k, _, v = ln.partition("\t")
                res[k.lower()] = coerce(v)
            return {"ok": True, **res}
        if op == "marker_clear":
            for ln in w.js(MK_CLEAR_JS):
                return {"ok": True, "cleared": coerce(ln.split("\t")[1])}
            return {"ok": False, "error": "no output"}
        if op == "marker":
            kind = str(req.get("kind") or "point")
            x = float(req.get("x") or 0) * 8.0
            y = float(req.get("y") or 0) * 8.0
            mid = int(req.get("id") or 9001)
            body = MK_ADD_JS % {"kind": json.dumps(kind), "x": x, "y": y, "id": mid,
                                "text": json.dumps(str(req.get("text") or "")),
                                "size": float(req.get("size") or 2.0),
                                "r": float(req.get("r") or 1.0), "g": float(req.get("g") or 0.9),
                                "b": float(req.get("b") or 0.3),
                                "radius": float(req.get("radius") or 6.0),
                                "stroke": float(req.get("stroke") or 2.0)}
            out = w.js(body)
            if not out:
                return {"ok": False, "error": "no output"}
            if out[0].startswith("ERR"):
                return {"ok": False, "error": out[0][4:]}
            audit("marker", kind=kind, x=x / 8.0, y=y / 8.0, id=mid)
            return {"ok": True, "id": mid, "kind": kind}
        on = str(req.get("on") or req.get("state") or "on").lower() in ("1", "on", "true", "start", "yes")
        div = int(req.get("div") or 2)
        size = float(req.get("size") or 0)
        def _tri(v):
            if v is None or str(v) == "":
                return "null"
            return "true" if str(v).lower() in ("1", "true", "on", "yes") else "false"
        res = {}
        for ln in w.js(MK_ON_JS % {"on": "true" if on else "false", "div": div, "size": size,
                                   "labels": _tri(req.get("labels")), "tint": _tri(req.get("tint"))}):
            k, _, v = ln.partition("\t")
            res[k] = coerce(v)
        audit("mirror", on=on, div=div, size=size)
        return {"ok": True, "on": on, **res}
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
    ap.add_argument("--manual", action="store_true",
                    help="关掉自动投影：只有放下脉冲地雷才开始（默认是有仿真就自己铺）")
    ap.add_argument("--no-push-admin", action="store_true",
                    help="不要自动给进来的玩家 admin（默认给，这样他们能在聊天栏用 /push 跟 agent 说话）")
    ap.add_argument("--java", default=None)
    ap.add_argument("--jar", default=DEFAULT_JAR)
    a = ap.parse_args(argv)

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
