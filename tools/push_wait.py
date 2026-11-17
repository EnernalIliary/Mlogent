# -*- coding: utf-8 -*-
"""等一条管理员 /push 消息, 收到就打印并退出(供 agent 用后台任务"被敲门").

用法(后台常驻):
    python tools/push_wait.py --timeout 1800

退出码: 0 = 收到(消息在 stdout, JSON 一行一条), 2 = 超时, 3 = 世界守护进程没起.

为什么用后台任务而不是直连: DSH 会话没有对外的"插话"端口, 后台任务结束会唤醒
agent —— 这就是把游戏里的 /push 变成"插队消息"的最短路径.
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

import world_client as wc  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=float, default=1800.0, help="最多等多少秒(默认 1800)")
    ap.add_argument("--poll", type=float, default=1.5, help="轮询间隔秒(默认 1.5)")
    ap.add_argument("--api-port", type=int, default=0)
    a = ap.parse_args(argv)

    hs = wc.handshake()
    if not hs:
        print("world daemon not running", file=sys.stderr)
        return 3
    port = a.api_port or int(hs.get("apiPort") or 0)
    t0 = time.time()
    while True:
        try:
            res = wc.call({"op": "push", "drain": 1}, timeout=15, hs=hs if not port else hs)
        except Exception as exc:
            print("poll failed: %s" % exc, file=sys.stderr)
            res = None
        if res and res.get("ok") and res.get("rows"):
            for r in res["rows"]:
                print(json.dumps(r, ensure_ascii=False), flush=True)
            return 0
        if time.time() - t0 > a.timeout:
            print("timeout after %.0fs" % a.timeout, file=sys.stderr)
            return 2
        time.sleep(a.poll)


if __name__ == "__main__":
    sys.exit(main())
