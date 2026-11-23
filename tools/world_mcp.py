#!/usr/bin/env python
"""world_mcp.py -- MCP (stdio) server for the local Mindustry debug world.

它只是 world_server.py 的薄壳: 所有真实动作 (java 进程、js、console) 都在那个
常驻进程里完成. 这样 MCP 随 DSH 会话重启时玩家不会掉线 —— 世界活在别处.

Run:  python tools/world_mcp.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import world_client as _wc  # noqa: E402
from world_cache import ResponseCache  # noqa: E402

try:
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

PROTO = "2024-11-05"
NAME = "mindustry-world"
VERSION = "0.1.0"

_READ_CACHEABLE = frozenset({
    "world_status", "world_players", "world_units", "world_unit",
    "world_buildings", "world_building", "world_logic", "world_logic_code",
    "world_logic_graph", "world_logic_snapshot", "world_logic_vars",
})
_CACHE_CONTROL_TOOLS = frozenset({"world_cache_stats"})
_READ_CACHE = ResponseCache(ttl=0.75, limit=256)

SERVER = str(HERE / "world_server.py")

TOOLS = [
    {
        "name": "world_status",
        "description": "活世界快照: 地图/模式/波次/世界 tick/玩家数/单位数/建筑数/暂停/"
                       "无限资源/游戏端口/运行时长。没在跑时返回明确的错误(用 world_start 开)。",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "world_players",
        "description": "在线玩家: 名字、队伍、格坐标、是否管理员。",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "world_units",
        "description": "单位清单(可按队伍/兵种/半径过滤)。controller 字段是 UnitController "
                       "的类名: Player=人控, LogicAI=逻辑控, CommandAI=编队, 其余为 AI。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "team": {"type": "string", "description": "队伍名, 如 sharded / crux"},
                "type": {"type": "string", "description": "兵种名, 如 flare / poly / mono"},
                "x": {"type": "number", "description": "中心格 x (配合 radius)"},
                "y": {"type": "number", "description": "中心格 y (配合 radius)"},
                "radius": {"type": "number", "description": "半径(格)"},
                "limit": {"type": "number", "description": "最多返回条数, 默认 200"},
                "format": {"type": "string", "enum": ["json", "table"],
                           "description": "table = 额外返回对齐的纯文本表(带 flag/ctrl/mine/boost)"},
            },
        },
    },
    {
        "name": "world_unit",
        "description": "按 id 查一只单位的全部字段(比 world_units 多: 世界坐标、mineTile、speed、shooting、range)。",
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "number", "description": "单位 id (world_units 的 id 列)"}},
            "required": ["id"],
        },
    },
    {
        "name": "world_changes",
        "description": "建筑变更日志(增量): TileChangeEvent(放置 P / 拆除 B)+ ConfigEvent(改配置 C)。"
                       "用 since=上次返回的 nextSeq 取增量; 环形缓冲只含最近 500 条, 重启守护进程会清空。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "since": {"type": "number", "description": "只要 seq > since 的条目, 默认 0 = 全部"},
                "limit": {"type": "number", "description": "默认 200"},
            },
        },
    },
    {
        "name": "world_buildings",
        "description": "建筑清单(可按队伍/方块名/半径过滤)。items/capacity 对无货舱建筑为 -1。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "team": {"type": "string"},
                "block": {"type": "string", "description": "方块名, 如 landing-pad / core-shard"},
                "x": {"type": "number"},
                "y": {"type": "number"},
                "radius": {"type": "number"},
                "limit": {"type": "number"},
            },
        },
    },
    {
        "name": "world_building",
        "description": "查单个格子上的建筑(不看 Groups.build, 直接看 tile)。返回 block/team/原点格/health/items/capacity; "
                       "空格子返回 found=false。看刚放的 container/传送带这类不更新的方块用它。",
        "inputSchema": {
            "type": "object",
            "properties": {"x": {"type": "number"}, "y": {"type": "number"}},
            "required": ["x", "y"],
        },
    },
    {
        "name": "world_maps",
        "description": "服务端可开的内置图名(host 接受的名字, 如 Fork / Archipelago).",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "world_place",
        "description": "在格 (x,y) 放一个方块(如 micro-processor / container / landing-pad)并启用它。"
                       "生成团队默认是世界的 defaultTeam。破坏性写操作。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "block": {"type": "string"},
                "x": {"type": "number"}, "y": {"type": "number"},
            },
            "required": ["block", "x", "y"],
        },
    },
    {
        "name": "world_clear",
        "description": "清掉格 (x,y) 上的方块(置 air)。破坏性写操作。",
        "inputSchema": {
            "type": "object",
            "properties": {"x": {"type": "number"}, "y": {"type": "number"}},
            "required": ["x", "y"],
        },
    },
    {
        "name": "world_spawn",
        "description": "在格 (x,y) 周围生成 count 只 type 单位(黄金角螺旋铺开, 不会叠在一点)。"
                       "调单位逻辑前先造兵用。写入操作。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "description": "单位类型, 如 flare / poly / pulsar / mono"},
                "count": {"type": "number", "description": "数量, 默认 1"},
                "x": {"type": "number"}, "y": {"type": "number"},
                "radius": {"type": "number", "description": "散布半径(格), 默认 3"},
                "team": {"type": "string", "description": "默认 sharded"},
            },
            "required": ["type", "x", "y"],
        },
    },
    {
        "name": "world_kill_units",
        "description": "清掉单位(可按队/半径过滤, 默认保留玩家操纵的单位)。调试前恢复干净场面用。破坏性写操作。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "team": {"type": "string"},
                "include_players": {"type": "boolean", "description": "默认 false: 跳过玩家控制的单位"},
                "x": {"type": "number"}, "y": {"type": "number"},
                "radius": {"type": "number", "description": "0 = 全图"},
            },
        },
    },
    {
        "name": "world_clear_buildings",
        "description": "清掉建筑(默认保留核心, 可按半径)。破坏性写操作。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keepcore": {"type": "boolean", "description": "默认 true"},
                "x": {"type": "number"}, "y": {"type": "number"},
                "radius": {"type": "number", "description": "0 = 全图"},
            },
        },
    },
    {
        "name": "world_reset",
        "description": "把世界恢复到刚开图的干净状态(清空建筑与单位)。默认走 nextmap+gameover 换图, "
                       "玩家不掉线; 传 hard=true 才 stop+host(会断开所有玩家)。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "hard": {"type": "boolean", "description": "默认 false = 不踢人"},
                "map": {"type": "string", "description": "可选: 换成另一张图"},
            },
        },
    },
    {
        "name": "world_switch_map",
        "description": "换图但不踢玩家: nextmap 登记下一张图, gameover 触发重载; 客户端自动重载新地图。"
                       "换完会把 waves=off / infiniteResources=on 等调试规则重新钉死。",
        "inputSchema": {
            "type": "object",
            "properties": {"map": {"type": "string", "description": "省略 = 重载当前图"}},
        },
    },
    {
        "name": "world_logic",
        "description": "列出逻辑处理器(可按半径)。每行 x/y/block/codeLen/vars(变量数)。单台详情由 "
                       "world_logic_code 返回源码、revision、@ipt 和链接目标。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "x": {"type": "number"}, "y": {"type": "number"},
                "radius": {"type": "number"},
                "limit": {"type": "number", "description": "默认 40"},
            },
        },
    },
    {
        "name": "world_logic_code",
        "description": "读取处理器类型、源码、带标签的源码、当前 @ipt、链接和用于修改的 revision。",
        "inputSchema": {
            "type": "object",
            "properties": {"x": {"type": "number"}, "y": {"type": "number"}},
            "required": ["x", "y"],
        },
    },
    {
        "name": "world_logic_graph",
        "description": "读取多台处理器的 revision、链接目标和处理器间依赖边，供批量编辑预览使用。",
        "inputSchema": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "x": {"type": "integer", "minimum": 0}, "y": {"type": "integer", "minimum": 0},
                "radius": {"type": "integer", "minimum": 0, "maximum": 32767},
                "limit": {"type": "integer", "minimum": 1, "maximum": 1024},
            },
        },
    },
    {
        "name": "world_logic_batch_preview",
        "description": "预览多台处理器的源码和链接联合修改。只做 revision、原版汇编器和链接校验，不写入游戏。",
        "inputSchema": {
            "type": "object", "required": ["processors"], "additionalProperties": False,
            "properties": {"processors": {"type": "array", "minItems": 1, "maxItems": 32, "items": {
                "type": "object", "required": ["x", "y", "expected_revision"], "additionalProperties": False,
                "properties": {
                    "x": {"type": "integer", "minimum": 0}, "y": {"type": "integer", "minimum": 0},
                    "expected_revision": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "code": {"type": "string", "maxLength": 102400},
                    "link_changes": {"type": "object"},
                },
            }}},
        },
    },
    {
        "name": "world_logic_batch_set",
        "description": "提交已预览的多处理器源码和链接修改。先整批复核 revision 与原版汇编，失败时恢复已写入处理器。",
        "inputSchema": {
            "type": "object", "required": ["processors"], "additionalProperties": False,
            "properties": {"processors": {"type": "array", "minItems": 1, "maxItems": 32, "items": {
                "type": "object", "required": ["x", "y", "expected_revision"], "additionalProperties": False,
                "properties": {
                    "x": {"type": "integer", "minimum": 0}, "y": {"type": "integer", "minimum": 0},
                    "expected_revision": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                    "code": {"type": "string", "maxLength": 102400},
                    "link_changes": {"type": "object"},
                },
            }}},
        },
    },
    {
        "name": "world_logic_batch_rollback",
        "description": "原子回滚一批处理器快照。先核对所有当前 revision，成功后为本次回滚生成反向快照。",
        "inputSchema": {
            "type": "object", "required": ["snapshot_ids"], "additionalProperties": False,
            "properties": {"snapshot_ids": {"type": "array", "minItems": 1, "maxItems": 32,
                                               "uniqueItems": True, "items": {"type": "string", "pattern": "^[0-9a-f]{32}$"}}},
        },
    },
    {
        "name": "world_logic_snapshot",
        "description": "读取 world_logic_set 生成的持久快照，返回回滚前源码、带标签源码、链接和前后 revision。",
        "inputSchema": {
            "type": "object", "required": ["snapshot_id"], "additionalProperties": False,
            "properties": {"snapshot_id": {"type": "string", "pattern": "^[0-9a-f]{32}$"}},
        },
    },
    {
        "name": "world_logic_set",
        "description": "按 world_logic_code 返回的 revision 写入源码或修改单台处理器的链接。"
                       "用在线原版汇编器验证，写后回读并返回可回滚的 snapshot_id。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "x": {"type": "integer"}, "y": {"type": "integer"},
                "code": {"type": "string"},
                "expected_revision": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                "link_changes": {"type": "object", "additionalProperties": False, "properties": {
                    "add": {"type": "array", "items": {
                        "type": "object", "required": ["x", "y"], "additionalProperties": False,
                        "properties": {"x": {"type": "integer"}, "y": {"type": "integer"},
                                       "name": {"type": "string"}},
                    }},
                    "remove": {"type": "array", "items": {"type": "string"}},
                }},
            },
            "required": ["x", "y", "expected_revision"],
        },
    },
    {
        "name": "world_logic_rollback",
        "description": "用 snapshot_id 回滚一次在线编辑，核对处理器源码和链接仍匹配编辑后的版本。",
        "inputSchema": {
            "type": "object", "required": ["snapshot_id"],
            "properties": {"snapshot_id": {"type": "string", "pattern": "^[0-9a-f]{32}$"}},
        },
    },
    {
        "name": "world_logic_vars",
        "description": "读处理器 (x,y) 的运行时变量表(executor.vars): 名字/当前值。逻辑里 set 过的"
                       "变量都在, 对象值(单位/建筑)显示为 toString。",
        "inputSchema": {
            "type": "object",
            "properties": {"x": {"type": "number"}, "y": {"type": "number"}},
            "required": ["x", "y"],
        },
    },
    {
        "name": "world_schematic",
        "description": "把蓝图 (.msch) 放进世界: 先放普通方块, 再放处理器(处理器链接必须指向已存在的建筑)。"
                       "src 给 path(本地 .msch 路径) 或 b64(蓝图 base64)；x/y 省略则居中。写操作。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": ".msch 文件路径"},
                "b64": {"type": "string", "description": "蓝图 base64(与 path 二选一)"},
                "x": {"type": "number"}, "y": {"type": "number"},
                "team": {"type": "string", "description": "默认 sharded"},
            },
        },
    },
    {
        "name": "world_schematic_save",
        "description": "把世界矩形区域 (x,y,w,h) 存成蓝图 config/schematics/<name>.msch;"
                       "处理器代码与链接、方块配置都会一起存进去。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "x": {"type": "number"}, "y": {"type": "number"},
                "w": {"type": "number"}, "h": {"type": "number"},
                "name": {"type": "string"},
            },
            "required": ["x", "y", "w", "h"],
        },
    },
    {
        "name": "world_schematics",
        "description": "列出服务端已知蓝图(名字/尺寸/作者)。",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "world_scene",
        "description": "把一份场景 JSON(与 mlogsim --scene 同一个格式)铺进真世界: 清区域、放建筑、"
                       "配置/装货、建链接、写逻辑代码、刷单位。坐标是格, 多格建筑以它为中心。"
                       "返回 placed/config/stock/logic/units/rows/errors 报告。写操作。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "场景文件路径(相对仓库根或绝对), 如 scenes/v27-rig.json"},
                "at": {"type": "array", "items": {"type": "number"},
                       "description": "把场景锚点落到这一格 [x,y](省略=原地)。通常给脉冲地雷所在格"},
                "door": {"type": "boolean", "description": "铺完在锚点放一扇门(脉冲地雷), 点它就进沙盘"},
                "door_kind": {"type": "string", "description": "门类型 possess|camera|exit(默认 possess)"},
                "door_unit": {"type": "string", "description": "门里给玩家附身的兵种(默认 poly)"},
                "door_label": {"type": "string", "description": "门在表里的名字"},
                "mirror_feed": {"type": "string", "description": "铺完接上仿真投影文件(mlogsim --push 写的那个)"},
                "mirror_dx": {"type": "number", "description": "投影偏移(格); 省略=用场景位移"},
                "mirror_dy": {"type": "number", "description": "投影偏移(格)"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "world_mirror_state",
        "description": "把一份单位状态数组画成世界标记(贴图 marker + 头顶文字): 传 units=[{type,x,y,amount,ctrl}] "
                       "(x/y 是世界坐标) 或 file=JSON 文件路径。用于把 mlogsim 的仿真状态映射到真世界。写操作。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "units": {"type": "array", "items": {"type": "object"},
                          "description": "单位快照; 每项 {type: 兵种名, x, y: 世界坐标, amount?: 携带量, ctrl?: 0自由/1逻辑/2玩家}"},
                "file": {"type": "string", "description": "也可以给一个 JSON 文件路径"},
                "labels": {"type": "boolean", "description": "是否画头顶文字(默认 true)"},
                "size": {"type": "number", "description": "图标尺寸(世界单位, 默认 16)"},
                "dx": {"type": "number", "description": "整体偏移(格), 把仿真坐标挪到玩家附近"},
                "dy": {"type": "number", "description": "整体偏移(格)"},
            },
        },
    },
    {
        "name": "world_mirror_feed",
        "description": "让服务端持续盯住一个 JSON 文件(mlogsim --push 会覆写它), 文件一变就把里面的单位刷新成 marker。"
                       "配套 mlogsim --push FILE --push-every N 使用, 即可在真世界里实时看仿真。写操作(起后台线程)。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "JSON 文件路径(相对仓库根或绝对)"},
                "dx": {"type": "number", "description": "整体偏移(格)"},
                "dy": {"type": "number", "description": "整体偏移(格)"},
                "stop": {"type": "boolean", "description": "true = 停止盯文件并清空状态镜"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "world_scene_probe",
        "description": "铺场景后再按场景里的 checks 读逻辑处理器变量并逐条判定 ok/FAIL。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "场景文件路径"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "world_door",
        "description": "点击门: 在世界里放一块可点的方块(默认脉冲地雷 shock-mine), 玩家点它就把"
                       "操作交给沙盘里的一只新单位(或只把镜头拉过去)。action=set 注册/建门, "
                       "list 看已登记的门, clear 清空, enter 让服务端代替玩家触发一次(没人在线时自测)。"
                       "kind=possess(附身到 tx,ty 刷的新单位) | camera(只拉镜头) | exit(把玩家送回原单位)。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["set", "list", "clear", "enter"],
                           "description": "默认 set"},
                "x": {"type": "integer", "description": "门所在的格(玩家点的那一格)"},
                "y": {"type": "integer"},
                "kind": {"type": "string", "description": "possess | camera | exit, 默认 possess"},
                "unit": {"type": "string", "description": "kind=possess 时刷什么兵种, 默认 poly"},
                "tx": {"type": "integer", "description": "沙盘落点格 x, 省略=门自己那格"},
                "ty": {"type": "integer"},
                "label": {"type": "string", "description": "备注名"},
                "block": {"type": "string", "description": "门用哪种方块, 默认 shock-mine; 传空串=不建方块"},
                "who": {"type": "string", "description": "enter 时指定玩家名子串, 省略=第一个在线玩家"},
            },
        },
    },
    {
        "name": "world_arm",
        "description": "开启投影导演。默认 auto=true: 只要 feed 新鲜就自动把场景复刻到对应格子"
                       "(建筑真放, 单位画贴图 marker 跟着 feed 动), 不需要玩家放地雷; feed 一停就收摊。"
                       "auto=false 才退回「玩家放一颗 shock-mine 才开始」。"
                       "feed=mlogsim --push 写的 JSON。**场景通常不用给**: mlogsim --scene X --push F "
                       "已经把 X 的路径写进 F, 导演会自己读出来; scene/scenes 只用于覆盖它"
                       "(手写 feed、或想换一张场景来对照)。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "feed": {"type": "string", "description": "仿真 feed 文件路径"},
                "scene": {"type": "string",
                          "description": "可选：覆盖 feed 里记的场景（放雷/自动投影时复刻哪张）"},
                "scenes": {"type": "array", "items": {"type": "string"},
                           "description": "多个场景：每个场景有自己的矩形边界，"
                                          "地雷落在哪个框里就复刻哪个"},
                "frames": {"type": "boolean",
                           "description": "是否用地板环画出场景边界（默认 true）"},
                "frame_floor": {"type": "string",
                                "description": "边界画法：marker（默认，一圈点）/ none"},
                "frame_cell": {"type": "integer",
                               "description": "沙盘格子边长，默认 64：场景按 N×N 从地图左上角开始排"},
            },
            "required": ["feed"],
        },
    },
    {
        "name": "world_frames",
        "description": "场景边界的矩形框：action=list 看已注册的场景与边界，"
                       "clear 擦掉（还原地板），paint 重画。只影响地板，不动建筑。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "clear", "paint"]},
                "scene": {"type": "string", "description": "clear 时可只擦某一个场景"},
                "frame_floor": {"type": "string"},
            },
        },
    },
    {
        "name": "world_projection",
        "description": "手动开关仿真投影: on=true 立刻在 at 处复刻场景并跟着 feed 画单位影子, "
                       "on=false 停掉。正常走「玩家放雷」, 这个是给自测用的直通车。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "on": {"type": "boolean", "description": "默认 true"},
                "feed": {"type": "string"},
                "scene": {"type": "string"},
                "at": {"type": "array", "items": {"type": "integer"}},
            },
        },
    },
    {
        "name": "world_projstat",
        "description": "看当前投影状态: 圆心格、复刻出来的建筑清单 [x,y,block]、feed 路径、"
                       "整体偏移、director 是否在跑、已经处理过的雷格。只读。",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "world_sblog",
        "description": "沙盘日志板: 每块沙盘左上角有一块用 TextMarker 写的面板(标题/feed 新鲜度/"
                       "投影状态/建筑数/单位数/最近事件)。action=list 读当前文本, log 往面板追加"
                       "一行(text, 只保留 ASCII), clear 擦掉。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "log", "clear"]},
                "slot": {"type": "integer", "description": "第几块沙盘, 默认 0"},
                "text": {"type": "string", "description": "action=log 时要追加的一行"},
            },
        },
    },
    {
        "name": "world_taps",
        "description": "读点击日志(玩家点了哪一格)。since 传上次的 nextSeq 取增量。"
                       "用来确认玩家真的点到了门, 或者把任意方块当按钮做交互。只读。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "since": {"type": "integer", "description": "只要 seq > since, 默认 0=全部"},
                "limit": {"type": "integer", "description": "最多返回条数, 默认 50"},
            },
        },
    },
    {
        "name": "world_chat",
        "description": "读玩家聊天(玩家发到聊天栏的消息)。since 传上次返回的 nextSeq 取增量, "
                       "limit 默认 80。返回 seq/tick/player/message。只读。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "since": {"type": "integer", "description": "只要 seq > since 的消息, 默认 0=全部"},
                "limit": {"type": "integer", "description": "最多返回条数, 默认 80"},
            },
        },
    },
    {
        "name": "world_push",
        "description": "读/取走管理员在游戏里打的 /push 消息队列。 /push 是注册进服务器的真命令"
                       "(在 /help 里, 带 <text...> 参数提示, 不会当聊天广播; '!push <文本>' 作为回退同样可用)。"
                       "drain=true(默认)取走后清空, false 只读。返回 rows[{tick,player,message}]。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "drain": {"type": "boolean", "description": "true=取走并清空(默认), false=只读"},
            },
        },
    },
    {
        "name": "world_say",
        "description": "在游戏里广播一句话(玩家可见)。写操作, 会进审计日志。",
        "inputSchema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
    },
    {
        "name": "world_pause",
        "description": "暂停/恢复世界。注意: 有玩家在线时暂停可能被客户端/加入事件解除, "
                       "返回后用 world_status 复核 paused。",
        "inputSchema": {
            "type": "object",
            "properties": {"on": {"type": "boolean", "description": "true=暂停, false=恢复"}},
            "required": ["on"],
        },
    },
    {
        "name": "world_save",
        "description": "把世界存到 config/saves/<name>.msav (相对名, 不含扩展名)。",
        "inputSchema": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
    },
    {
        "name": "world_load",
        "description": "读取 config/saves/<name>.msav 为当前世界(会踢掉现有局面)。",
        "inputSchema": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
    },
    {
        "name": "world_console",
        "description": "执行一条服务端控制台命令并返回它的输出行。只读命令: status / players / "
                       "dumpsettings。危险命令(host/stop/load/exit)会真的改变世界。",
        "inputSchema": {
            "type": "object",
            "properties": {"cmd": {"type": "string"}},
            "required": ["cmd"],
        },
    },
    {
        "name": "world_js",
        "description": "在服务端 JVM 里执行一段 Rhino JS (全反射调试口)。脚本里 sb 是一个 "
                       "StringBuilder, 用 sb.append(...) 追加返回值; 每行一条。例: "
                       "sb.append(Vars.state.wave)。注意: 大范围扫描会卡 tick, 自己加半径/上限。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "timeout": {"type": "number", "description": "秒, 默认 60"},
            },
            "required": ["code"],
        },
    },
    {
        "name": "world_start",
        "description": "后台拉起一个世界服务端(独立进程, MCP 退出也不掉)。已有世界在跑时, "
                       "除非 restart=true 否则报错。返回 gamePort/apiPort/map。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "map": {"type": "string", "description": "内置图名, 省略则随机"},
                "paused": {"type": "boolean", "description": "开服后立即暂停"},
                "game_port": {"type": "number", "description": "游戏端口, 默认 6567(不可用时自动换)"},
                "restart": {"type": "boolean", "description": "先关掉已有世界再开"},
            },
        },
    },
    {
        "name": "world_stop",
        "description": "关闭游戏世界。休眠时直接转为手动关闭，不唤醒；托管运行时经 60 秒否决期后保存恢复存档再关服。非托管世界仍需先 world_save。",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def _alive() -> bool:
    try:
        hs = _wc.handshake()
    except _wc.WorldError:
        return False
    try:
        r = _wc.call({"op": "ping"}, timeout=5, hs=hs)
        return bool(r.get("ok"))
    except Exception:
        return False


def tool_status(_args):
    return _wc.call({"op": "status"})


def tool_players(_args):
    return _wc.call({"op": "players"})


def tool_units(a):
    return _wc.call({"op": "units", "team": a.get("team"), "type": a.get("type"),
                     "x": a.get("x") or 0, "y": a.get("y") or 0,
                     "radius": a.get("radius") or 0,
                     "limit": a.get("limit") or 200,
                     "format": a.get("format")})


def tool_unit(a):
    return _wc.call({"op": "unit", "id": int(a["id"])})


def tool_changes(a):
    return _wc.call({"op": "changes", "since": int(a.get("since") or 0),
                     "limit": int(a.get("limit") or 200)})


def tool_chat(a):
    return _wc.call({"op": "chat", "since": int(a.get("since") or 0),
                     "limit": int(a.get("limit") or 80)})


def tool_push(a):
    return _wc.call({"op": "push", "drain": bool(a.get("drain", True))})


def tool_door(a):
    act = str(a.get("action") or "set").lower()
    if act == "list":
        return _wc.call({"op": "doors"})
    if act == "clear":
        return _wc.call({"op": "door_clear"})
    if act == "enter":
        return _wc.call({"op": "door_enter", "x": int(a.get("x") or 0),
                         "y": int(a.get("y") or 0), "who": a.get("who")})
    req = {"op": "door", "x": int(a.get("x") or 0), "y": int(a.get("y") or 0),
           "kind": str(a.get("kind") or "watch"), "unit": str(a.get("unit") or "poly")}
    if a.get("tx") is not None:
        req["tx"] = int(a["tx"])
    if a.get("ty") is not None:
        req["ty"] = int(a["ty"])
    if a.get("label"):
        req["label"] = str(a["label"])
    if a.get("block") is not None:
        req["block"] = str(a["block"])
    return _wc.call(req)


def tool_arm(a):
    req = {"op": "arm", "feed": str(a.get("feed") or "")}
    if a.get("scene"):
        req["scene"] = str(a["scene"])
    if a.get("scenes"):
        req["scenes"] = [str(s) for s in a["scenes"]]
    if "frames" in a:
        req["frames"] = bool(a["frames"])
    if a.get("frame_floor"):
        req["frame_floor"] = str(a["frame_floor"])
    if a.get("frame_cell"):
        req["frame_cell"] = int(a["frame_cell"])
    if a.get("at"):
        req["at"] = [int(v) for v in a["at"]]
    if a.get("force"):
        req["force"] = True
    return _wc.call(req, timeout=60.0)


def tool_projection(a):
    req = {"op": "projection", "on": bool(a.get("on", True))}
    for k in ("feed", "scene"):
        if a.get(k):
            req[k] = str(a[k])
    if a.get("at"):
        req["at"] = [int(v) for v in a["at"]]
    return _wc.call(req, timeout=60.0)


def tool_frames(a):
    req = {"op": "frames", "action": str(a.get("action") or "list")}
    if a.get("scene"):
        req["scene"] = str(a["scene"])
    if a.get("frame_floor"):
        req["frame_floor"] = str(a["frame_floor"])
    return _wc.call(req, timeout=90.0)


def tool_projstat(a):
    return _wc.call({"op": "projstat"}, timeout=60.0)


def tool_sblog(a):
    req = {"op": "sblog", "action": str(a.get("action") or "list"),
           "slot": int(a.get("slot") or 0)}
    if a.get("text"):
        req["text"] = str(a["text"])
    return _wc.call(req, timeout=60.0)


def tool_taps(a):
    return _wc.call({"op": "taps", "since": int(a.get("since") or 0),
                     "limit": int(a.get("limit") or 50)})


def tool_buildings(a):
    return _wc.call({"op": "buildings", "team": a.get("team"), "block": a.get("block"),
                     "x": a.get("x") or 0, "y": a.get("y") or 0,
                     "radius": a.get("radius") or 0,
                     "limit": a.get("limit") or 200})


def tool_building(a):
    return _wc.call({"op": "building", "x": int(a["x"]), "y": int(a["y"])})


def tool_place(a):
    return _wc.call({"op": "place", "block": str(a.get("block") or ""),
                     "x": int(a["x"]), "y": int(a["y"])})


def tool_clear(a):
    return _wc.call({"op": "clear", "x": int(a["x"]), "y": int(a["y"])})


def tool_spawn(a):
    return _wc.call({"op": "spawn", "type": str(a.get("type") or ""),
                     "count": int(a.get("count") or 1),
                     "x": float(a["x"]), "y": float(a["y"]),
                     "radius": float(a.get("radius") or 3),
                     "team": str(a.get("team") or "sharded")}, timeout=120)


def tool_kill_units(a):
    return _wc.call({"op": "killunits", "team": a.get("team"),
                     "include_players": bool(a.get("include_players", False)),
                     "x": a.get("x") or 0, "y": a.get("y") or 0,
                     "radius": a.get("radius") or 0}, timeout=120)


def tool_clear_buildings(a):
    return _wc.call({"op": "clearbuilds", "keepcore": bool(a.get("keepcore", True)),
                     "x": a.get("x") or 0, "y": a.get("y") or 0,
                     "radius": a.get("radius") or 0}, timeout=120)


def tool_reset(a):
    req = {"op": "reset"}
    if a.get("hard"):
        req["hard"] = True
    if a.get("map"):
        req["map"] = str(a["map"])
    return _wc.call(req, timeout=240)


def tool_switch_map(a):
    req = {"op": "switch"}
    if a.get("map"):
        req["map"] = str(a["map"])
    return _wc.call(req, timeout=240)


def tool_logic(a):
    return _wc.call({"op": "logic", "x": a.get("x") or 0, "y": a.get("y") or 0,
                     "radius": a.get("radius") or 0,
                     "limit": a.get("limit") or 40})


def tool_logic_code(a):
    return _wc.call({"op": "logic_code", "x": int(a["x"]), "y": int(a["y"])})


def tool_logic_graph(a):
    return _wc.call({"op": "logic_graph", **{key: int(value) for key, value in a.items()}})


def tool_logic_batch_preview(a):
    return _wc.call({"op": "logic_batch_preview", "processors": a["processors"]}, timeout=180)


def tool_logic_batch_set(a):
    return _wc.call({"op": "logic_batch_set", "processors": a["processors"]}, timeout=180)


def tool_logic_batch_rollback(a):
    return _wc.call({"op": "logic_batch_rollback", "snapshot_ids": a["snapshot_ids"]}, timeout=180)


def tool_logic_snapshot(a):
    return _wc.call({"op": "logic_snapshot", "snapshot_id": a["snapshot_id"]})


def tool_logic_set(a):
    return _wc.call({**a, "op": "logic_set"}, timeout=180)


def tool_logic_rollback(a):
    return _wc.call({"op": "logic_rollback", "snapshot_id": a["snapshot_id"]}, timeout=180)


def tool_logic_vars(a):
    return _wc.call({"op": "logic_vars", "x": int(a["x"]), "y": int(a["y"])})



def tool_schematic(a):
    req = {"op": "schematic"}
    if a.get("b64"):
        req["b64"] = str(a["b64"])
    if a.get("path"):
        req["path"] = str(a["path"])
    if a.get("x") is not None:
        req["x"] = int(a["x"])
    if a.get("y") is not None:
        req["y"] = int(a["y"])
    if a.get("team"):
        req["team"] = str(a["team"])
    return _wc.call(req, timeout=180)


def tool_schematic_save(a):
    req = {"op": "schematic_save", "x": int(a["x"]), "y": int(a["y"]),
           "w": int(a["w"]), "h": int(a["h"])}
    if a.get("name"):
        req["name"] = str(a["name"])
    return _wc.call(req, timeout=180)


def tool_schematics(_a):
    return _wc.call({"op": "schematics"})

def tool_scene(a):
    req = {"op": "scene", "path": str(a.get("path") or "")}
    if a.get("at") is not None:
        req["at"] = [int(a["at"][0]), int(a["at"][1])]
    if a.get("door"):
        req["door"] = True
        for k in ("door_kind", "door_unit", "door_label"):
            if a.get(k):
                req[k] = str(a[k])
    if a.get("mirror_feed"):
        req["mirror_feed"] = str(a["mirror_feed"])
        for k in ("mirror_dx", "mirror_dy"):
            if a.get(k) is not None:
                req[k] = float(a[k])
    return _wc.call(req, timeout=240)

def tool_mirror_state(a):
    req = {"op": "mirror_state"}
    if a.get("units") is not None:
        req["units"] = a["units"]
    if a.get("file"):
        req["file"] = str(a["file"])
    if a.get("labels") is not None:
        req["labels"] = bool(a["labels"])
    if a.get("size") is not None:
        req["size"] = float(a["size"])
    if a.get("dx") is not None:
        req["dx"] = float(a["dx"])
    if a.get("dy") is not None:
        req["dy"] = float(a["dy"])
    return _wc.call(req, timeout=120)


def tool_mirror_feed(a):
    if a.get("stop"):
        return _wc.call({"op": "mirror_clear"}, timeout=120)
    req = {"op": "mirror_feed", "path": str(a.get("path") or "")}
    if a.get("dx") is not None:
        req["dx"] = float(a["dx"])
    if a.get("dy") is not None:
        req["dy"] = float(a["dy"])
    return _wc.call(req, timeout=120)


def tool_scene_probe(a):
    return _wc.call({"op": "scene_probe", "path": str(a.get("path") or "")}, timeout=240)

def tool_maps(_args):
    return _wc.call({"op": "maps"})


def tool_say(a):
    return _wc.call({"op": "say", "text": str(a.get("text") or "")})


def tool_pause(a):
    return _wc.call({"op": "pause", "on": bool(a.get("on", True))})


def tool_save(a):
    return _wc.call({"op": "save", "name": str(a.get("name") or "world")})


def tool_load(a):
    return _wc.call({"op": "load", "name": str(a.get("name") or "")})


def tool_console(a):
    return _wc.call({"op": "console", "cmd": str(a.get("cmd") or "")}, timeout=200)


def tool_js(a):
    return _wc.call({"op": "js", "code": str(a.get("code") or ""),
                     "timeout": float(a.get("timeout") or 0)}, timeout=240)


def tool_start(a):
    import world_sleep_client
    if world_sleep_client.available():
        return world_sleep_client.request({'op': 'start', 'arguments': a}, timeout=120)
    if _alive() and not a.get("restart"):
        return {"ok": False, "error": "已有世界在跑; 传 restart=true 才会重开",
                "handshake": _wc.handshake()}
    if a.get("restart") and _alive():
        try:
            _wc.call({"op": "shutdown"}, timeout=20)
        except Exception:
            pass
        for _ in range(60):
            if not _alive():
                break
            time.sleep(0.5)
    args = [sys.executable, SERVER, "--api-port", "0"]
    if a.get("map"):
        args += ["--map", str(a["map"])]
    if a.get("paused"):
        args += ["--paused"]
    if a.get("game_port"):
        args += ["--game-port", str(int(a["game_port"]))]
    try:
        os.remove(_wc.HANDSHAKE)
    except OSError:
        pass
    flags = 0
    if os.name == "nt":
        # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP (+ 先试 BREAKAWAY 逃出作业对象)
        flags = 0x00000008 | 0x00000200
        try:
            subprocess.Popen(args, cwd=str(ROOT), stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             creationflags=flags | 0x01000000, close_fds=True)
            flags = -1
        except OSError:
            flags = 0x00000008 | 0x00000200
    if flags >= 0:
        subprocess.Popen(args, cwd=str(ROOT), stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=flags, close_fds=True)
    for _ in range(180):
        time.sleep(0.5)
        if os.path.isfile(_wc.HANDSHAKE):
            try:
                hs = _wc.handshake()
                r = _wc.call({"op": "ping"}, timeout=5, hs=hs)
                if r.get("ok"):
                    st = _wc.call({"op": "status"}, timeout=30, hs=hs)
                    return {"ok": True, "handshake": hs,
                            "status": {k: st.get(k) for k in
                                       ("map", "mode", "players", "units", "buildings",
                                        "gamePort", "paused")}}
            except Exception:
                continue
    return {"ok": False, "error": "90s 内世界没有就绪, 看 out/_world/server.log"}


def tool_stop(_args):
    return _wc.call({"op": "shutdown"}, timeout=20)


def tool_cache_stats(_args):
    return {"ok": True, "cache": _READ_CACHE.stats(), "cacheable_tools": sorted(_READ_CACHEABLE)}


HANDLERS = {
    "world_status": tool_status,
    "world_players": tool_players,
    "world_units": tool_units,
    "world_unit": tool_unit,
    "world_changes": tool_changes,
    "world_buildings": tool_buildings,
    "world_building": tool_building,
    "world_place": tool_place,
    "world_spawn": tool_spawn,
    "world_kill_units": tool_kill_units,
    "world_clear_buildings": tool_clear_buildings,
    "world_reset": tool_reset,
    "world_switch_map": tool_switch_map,
    "world_clear": tool_clear,
    "world_logic": tool_logic,
    "world_logic_code": tool_logic_code,
    "world_logic_graph": tool_logic_graph,
    "world_logic_batch_preview": tool_logic_batch_preview,
    "world_logic_batch_set": tool_logic_batch_set,
    "world_logic_batch_rollback": tool_logic_batch_rollback,
    "world_logic_snapshot": tool_logic_snapshot,
    "world_logic_set": tool_logic_set,
    "world_logic_rollback": tool_logic_rollback,
    "world_logic_vars": tool_logic_vars,
    "world_schematic": tool_schematic,
    "world_schematic_save": tool_schematic_save,
    "world_schematics": tool_schematics,
    "world_scene": tool_scene,
    "world_mirror_state": tool_mirror_state,
    "world_mirror_feed": tool_mirror_feed,
    "world_scene_probe": tool_scene_probe,
    "world_maps": tool_maps,
    "world_chat": tool_chat,
    "world_push": tool_push,
    "world_door": tool_door,
    "world_arm": tool_arm,
    "world_projection": tool_projection,
    "world_projstat": tool_projstat,
    "world_frames": tool_frames,
    "world_sblog": tool_sblog,
    "world_taps": tool_taps,
    "world_say": tool_say,
    "world_pause": tool_pause,
    "world_save": tool_save,
    "world_load": tool_load,
    "world_console": tool_console,
    "world_js": tool_js,
    "world_start": tool_start,
    "world_stop": tool_stop,
    "world_cache_stats": tool_cache_stats,
}

TOOLS.append({
    "name": "world_cache_stats",
    "description": "读取真实世界 MCP 只读查询缓存的命中、未命中、TTL 和容量统计。",
    "inputSchema": {"type": "object", "additionalProperties": False, "properties": {}},
})
for _tool in TOOLS:
    if _tool["name"] in _READ_CACHEABLE:
        _tool["inputSchema"].setdefault("properties", {})["cache"] = {
            "type": "string", "enum": ["auto", "fresh"],
            "description": "auto 使用 0.75 秒进程缓存，fresh 绕过缓存并刷新结果。",
        }


from world_abort import install as _install_veto
from world_work import wrap as _with_world_work
for _work_name, _work_handler in list(HANDLERS.items()):
    HANDLERS[_work_name] = _with_world_work(_work_name, _work_handler, _wc)
_install_veto(HANDLERS, TOOLS, _wc)


def _reply(rid, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": rid}
    if error is not None:
        msg["error"] = error
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def handle(req):
    method = req.get("method")
    rid = req.get("id")
    if method == "initialize":
        return _reply(rid, {
            "protocolVersion": PROTO,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": NAME, "version": VERSION},
        })
    if method == "notifications/initialized":
        return
    if method == "ping":
        return _reply(rid, {})
    if method == "tools/list":
        return _reply(rid, {"tools": TOOLS})
    if method == "tools/call":
        params = req.get("params") or {}
        name = params.get("name")
        fn = HANDLERS.get(name)
        if fn is None:
            return _reply(rid, error={"code": -32602, "message": f"unknown tool {name}"})
        try:
            arguments = dict(params.get("arguments") or {})
            cache_mode = arguments.pop("cache", "auto")
            cache_key = json.dumps(arguments, ensure_ascii=False, sort_keys=True, default=str)
            if name in _READ_CACHEABLE and cache_mode not in ("auto", "fresh"):
                raise ValueError("cache must be auto or fresh")
            out = _READ_CACHE.get((name, cache_key)) if name in _READ_CACHEABLE and cache_mode == "auto" else None
            if out is None:
                if name not in _READ_CACHEABLE and name not in _CACHE_CONTROL_TOOLS:
                    _READ_CACHE.clear()
                out = fn(arguments)
                if name in _READ_CACHEABLE and isinstance(out, dict) and out.get("ok"):
                    _READ_CACHE.put((name, cache_key), out)
            if isinstance(out, dict) and "ok" in out and not out.get("ok"):
                raise RuntimeError(out.get("error") or "world_server 返回失败")
            return _reply(rid, {"content": [{"type": "text",
                                             "text": json.dumps(out, ensure_ascii=False)}],
                                "isError": False})
        except Exception as exc:
            return _reply(rid, {"content": [{"type": "text",
                                             "text": "%s: %s" % (type(exc).__name__, exc)}],
                                "isError": True})
    if rid is None:
        return
    return _reply(rid, error={"code": -32601, "message": f"method not found: {method}"})


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            handle(json.loads(line))
        except Exception:
            traceback.print_exc(file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
