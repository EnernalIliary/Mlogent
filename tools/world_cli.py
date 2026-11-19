"""Side-effect-free argument definitions for the persistent world daemon."""
import argparse
import json
import os
import sys
import threading
import time
from world_protocol import API
from world_runtime import WorldRuntime


def build_parser(default_jar):
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
    ap.add_argument("--jar", default=default_jar)
    return ap


def run(argv=None, *, default_jar, paths, services):
    a = build_parser(default_jar).parse_args(argv)
    if not a.watch_feed and not a.mirror_feed:
        # 不给 --watch-feed 就盯默认 feed：任何 --project 的仿真一跑就自动
        # 出现在地图上，跑完自动收摊。要看纯图就给 --no-projection。
        a.watch_feed = [paths.feed]

    java = services.find_java(a.java)
    jar = os.path.abspath(a.jar)
    if not os.path.isfile(jar):
        raise SystemExit("找不到 jar: " + jar)

    services.configure_chat(bool(a.chat_log), a.chat_prefix)

    game_port, port_note = services.pick_port(a.game_port)
    if port_note:
        print("[warn] " + port_note, file=sys.stderr)
    w = services.create_world(java, jar, map_name=a.map, host=not a.no_host, paused=a.paused,
              game_port=game_port, js_timeout=a.js_timeout, server_name=a.name, paths=paths,
              no_push_admin=bool(a.no_push_admin))
    runtime = WorldRuntime(w, paths)
    try:
        if a.mirror_feed:
            services.mirror_watch(w, a.mirror_feed)
        if not a.no_projection and (getattr(a, "watch_feed", None) or getattr(a, "watch_scene", None)):
            # 玩家放下一颗脉冲地雷, 就以它为圆心开始投影 (不自己放雷、不用点击)
            services.projection_director(w, a.watch_feed, None, scenes=getattr(a, "watch_scene", None),
                                frames=str(getattr(a, "frame_floor", "") or "").lower() != "none",
                                frame_floor=getattr(a, "frame_floor", "marker"),
                                at_cell=int(getattr(a, "frame_cell", 64) or 64),
                                feeds=getattr(a, "watch_feed", None),
                                 auto=not getattr(a, "manual", False),
                                 hold=float(getattr(a, "hold", 0.0) or 0.0))

        srv = API(("127.0.0.1", a.api_port), services.make_handler(w, runtime.stopped.set))
        runtime.api = srv
        port = srv.server_address[1]
        runtime.api_thread = threading.Thread(target=srv.serve_forever, daemon=True)
        runtime.api_thread.start()
        info = {"pid": os.getpid(), "apiPort": port, "gamePort": w.game_port,
                "map": getattr(w, "map_actual", None) or w.map_name,
                "hosted": getattr(w, "hosted", False), "portNote": port_note,
                "startedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
                "dataDir": runtime.paths.data, "log": runtime.paths.log, "java": java, "jar": jar}
        with open(runtime.paths.handshake, "w", encoding="utf-8") as stream:
            json.dump(info, stream, ensure_ascii=False, indent=2)
        print(json.dumps(info, ensure_ascii=False), flush=True)
        while not runtime.stopped.wait(0.5):
            if w.proc and w.proc.poll() is not None:
                print("java 退出, 关掉控制口", file=sys.stderr)
                break
    except KeyboardInterrupt:
        pass
    finally:
        runtime.close()
