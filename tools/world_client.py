#!/usr/bin/env python3
"""world_client.py — world_server.py 的最小客户端 (也是 world_mcp.py 的地基).

    python tools/world_client.py status
    python tools/world_client.py units --radius 30 --x 80 --y 80 --limit 20
    python tools/world_client.py console "status"
    python tools/world_client.py say "hello from agent"
    python tools/world_client.py js "sb.append(Vars.state.wave);"

握手文件 out/_world/daemon.json 由 world_server.py 在开服成功后写; 连不上时
这里的错误信息会说明是进程死了还是端口没响应.
"""
from __future__ import annotations

import json
import os
import socket
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HANDSHAKE = os.path.join(ROOT, "out", "_world", "daemon.json")

# 控制台/管道默认是 cp936, 中文路径打出去会乱码; 统一钉成 UTF-8.
for _stream in (sys.stdout, sys.stderr, sys.stdin):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


class WorldError(RuntimeError):
    pass


def stop_if_sleeping():
    """Atomically stop an already sleeping managed world, without waking it."""
    import world_sleep_client
    if not world_sleep_client.available():
        return None
    result = world_sleep_client.request({'op': 'stop_if_sleeping'}, timeout=20)
    return result if result.get('handled') else None


def handshake() -> dict:
    if not os.path.isfile(HANDSHAKE):
        raise WorldError("没有运行中的世界: 先 python tools/world_server.py --map Fork"
                         " (或让 MCP 的 world_start 开一个)")
    try:
        with open(HANDSHAKE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise WorldError("握手文件坏了 (%s): %s" % (HANDSHAKE, e))


def call(req: dict, timeout: float = 180.0, hs: dict | None = None) -> dict:
    if hs is None:
        import world_sleep_client
        if world_sleep_client.available():
            return world_sleep_client.request({'op': 'call', 'request': req}, timeout=max(timeout, 120))
    hs = hs or handshake()
    port = int(hs["apiPort"])
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout) as s:
            s.settimeout(timeout)
            s.sendall((json.dumps(req, ensure_ascii=False) + "\n").encode("utf-8"))
            buf = b""
            while not buf.endswith(b"\n"):
                chunk = s.recv(65536)
                if not chunk:
                    break
                buf += chunk
    except (ConnectionRefusedError, socket.timeout, OSError) as e:
        raise WorldError("连不上世界控制口 127.0.0.1:%d (%s); 检查 out/_world/server.log"
                         % (port, e))
    if not buf.strip():
        raise WorldError("控制口没有回包 (pid=%s)" % hs.get("pid"))
    return json.loads(buf.decode("utf-8"))


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="world_server 客户端")
    ap.add_argument("op", help="ping|status|players|units|buildings|console|js|say|pause|save|load|push|"
                              "scene|scene_probe|door|doors|door_clear|door_enter|taps|"
                              "mirror|mirror_state|mirror_feed|mirror_clear|"
                              "arm|projection|frames|shutdown")
    ap.add_argument("arg", nargs="?", default=None, help="console 命令 / say 文本 / js 代码 / save 名")
    ap.add_argument("--team", default=None)
    ap.add_argument("--type", default=None)
    ap.add_argument("--block", default=None)
    ap.add_argument("--radius", type=float, default=0)
    ap.add_argument("--x", type=float, default=0)
    ap.add_argument("--y", type=float, default=0)
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--timeout", type=float, default=180)
    ap.add_argument("--kind", default=None, help="门类型 watch|possess|camera|exit")
    ap.add_argument("--unit", default=None, help="门里刷什么兵种")
    ap.add_argument("--tx", type=int, default=None)
    ap.add_argument("--ty", type=int, default=None)
    ap.add_argument("--who", default=None, help="door_enter: 玩家名子串（省略=第一个在线玩家）")
    ap.add_argument("--label", default=None, help="门/场景的备注名")
    ap.add_argument("--scene", default=None, help="门点下去要铺的场景文件（可选）")
    ap.add_argument("--at", default=None, help="scene: 场景锚点落在世界哪一格 x,y（省略=原地）")
    ap.add_argument("--door", action="store_true", help="scene: 铺完在锚点放一扇门（脉冲地雷）")
    ap.add_argument("--feed", default=None, help="scene/arm: 铺完接上仿真投影文件（mirror_feed）")
    ap.add_argument("--force", action="store_true", help="arm: feed 不存在/过期也放地雷")
    ap.add_argument("--dx", type=float, default=None, help="投影整体偏移（格，省=用场景位移）")
    ap.add_argument("--dy", type=float, default=None, help="投影整体偏移（格，省=用场景位移）")
    ap.add_argument("--since", type=int, default=0)
    ap.add_argument("--count", type=int, default=1, help="spawn 数量")
    ap.add_argument("--div", type=int, default=2, help="mirror: 每 N 帧刷新一次")
    ap.add_argument("--id", type=int, default=9001, help="marker id")
    ap.add_argument("--text", default=None, help="marker: 文字标记内容")
    ap.add_argument("--size", type=float, default=2.0, help="marker: 字号 / frames: 点半径(世界单位)")
    ap.add_argument("--action", default=None, help="frames: list|clear|paint")
    ap.add_argument("--step", type=int, default=None, help="frames paint: 每几格一个点（默认 1）")
    ap.add_argument("--icon", type=float, default=0, help="mirror: 图标尺寸(世界单位, 0=不变)")
    ap.add_argument("--file", default=None, help="mirror_state: units JSON 文件")
    ap.add_argument("--labels", action=argparse.BooleanOptionalAction, default=None,
                    help="mirror: 单位头顶文字标签")
    ap.add_argument("--tint", action=argparse.BooleanOptionalAction, default=None,
                    help="mirror: 按控制状态染色")
    a = ap.parse_args(argv)

    req = {"op": a.op}
    if a.op in ("console",):
        req["cmd"] = a.arg or ""
    elif a.op == "js":
        req["code"] = a.arg or ""
    elif a.op == "say":
        req["text"] = a.arg or ""
    elif a.op in ("save", "load"):
        req["name"] = a.arg or ""
    elif a.op in ("scene", "scene_probe"):
        req["path"] = a.arg or ""
        if a.at:
            req["at"] = [int(v) for v in str(a.at).replace(",", " ").split()[:2]]
        if a.door:
            req["door"] = True
            if a.kind:
                req["door_kind"] = a.kind
            if a.unit:
                req["door_unit"] = a.unit
            if a.label:
                req["door_label"] = a.label
            if a.block:
                req["door_block"] = a.block
        if a.feed:
            req["mirror_feed"] = a.feed
            if a.dx is not None:
                req["mirror_dx"] = a.dx
            if a.dy is not None:
                req["mirror_dy"] = a.dy
    elif a.op == "frames":
        req["action"] = a.action or (a.arg or "list")
        if a.scene:
            req["scene"] = a.scene
        if a.step is not None:
            req["step"] = a.step
        if a.radius:
            req["radius"] = a.radius
    elif a.op in ("door", "door_enter"):
        req["x"] = int(a.x)
        req["y"] = int(a.y)
        if a.kind:
            req["kind"] = a.kind
        if a.unit:
            req["unit"] = a.unit
        if a.tx is not None:
            req["tx"] = a.tx
        if a.ty is not None:
            req["ty"] = a.ty
        if a.who:
            req["who"] = a.who
        if a.block:
            req["block"] = a.block
        if a.label:
            req["label"] = a.label
        if a.scene:
            req["scene"] = a.scene
    elif a.op == "arm":
        # 有仿真在跑就放一颗地雷等玩家点; 不立刻开始投影
        feed = a.feed or a.arg
        if feed:
            req["feed"] = feed
        if a.scene:
            req["scene"] = a.scene
        if a.at:
            req["at"] = [int(v) for v in str(a.at).replace(",", " ").split()[:2]]
        if a.force:
            req["force"] = True
    elif a.op == "projection":
        on = (a.arg or "on").strip().lower() not in ("off", "0", "false", "stop")
        req["on"] = on
        if a.feed:
            req["feed"] = a.feed
        if a.scene:
            req["scene"] = a.scene
        if a.at:
            req["at"] = [int(v) for v in str(a.at).replace(",", " ").split()[:2]]
    elif a.op in ("place", "clear"):
        req.update({"block": a.block or a.arg, "x": int(a.x), "y": int(a.y)})
    elif a.op == "tap":
        req["x"] = int(a.x)
        req["y"] = int(a.y)
        if a.who:
            req["who"] = a.who
    elif a.op == "taps":
        req["since"] = a.since
        req["limit"] = a.limit
    elif a.op == "pause":
        req["on"] = (a.arg or "on").lower() not in ("off", "0", "false", "no")
    elif a.op == "spawn":
        req.update({"x": a.x, "y": a.y, "radius": a.radius, "type": a.type,
                    "count": a.count})
    elif a.op == "mirror":
        req.update({"on": a.arg or "on", "div": a.div, "size": a.icon,
                    "labels": a.labels, "tint": a.tint})
    elif a.op == "mirror_state":
        # arg 可以是 json 文件路径, 也可以省略(用 --file)
        src = a.arg or a.file
        if not src:
            raise SystemExit("mirror_state 需要 JSON 文件路径: mirror_state <units.json>")
        with open(src, "r", encoding="utf-8") as fh:
            req["units"] = json.load(fh)
    elif a.op == "mirror_feed":
        if not a.arg:
            raise SystemExit("mirror_feed 需要文件路径")
        req["path"] = a.arg
    elif a.op == "push":
        req["drain"] = (a.arg or "drain").lower() not in ("peek", "read", "0", "false", "no")
    elif a.op == "marker":
        req.update({"x": a.x, "y": a.y, "id": a.id, "kind": a.kind or "point",
                    "text": a.text, "size": a.size})
    if a.op in ("units", "buildings"):
        req.update({"team": a.team, "type": a.type, "block": a.block,
                    "radius": a.radius, "x": a.x, "y": a.y, "limit": a.limit})
    if a.op == "building":
        req.update({"x": int(a.x), "y": int(a.y)})
    if a.op == "unit":
        req["id"] = int(a.arg or a.x)
    if a.op in ("scene", "scene_probe"):
        req["path"] = a.arg or ""
    if a.op in ("changes", "chat", "push"):
        req["since"] = a.since
        req["limit"] = a.limit
    print(json.dumps(call(req, timeout=a.timeout), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
