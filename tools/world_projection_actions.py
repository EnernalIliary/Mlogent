"""Projection slot lifecycle with explicitly injected world actions."""
import json
import threading
import time
from world_scenes import feed_age, feed_scene

def _projs(w):
    """正在投影的沙盘: slot -> {center, builds, feed, scene}. 多块可以同时投影."""
    if not hasattr(w, "_projs"):
        w._projs = {}
    return w._projs


def project_at(w, x, y, feed, scene_path=None, tell=True, anchor=None, slot=0, pin=True, *, services):
    """以玩家放下的那颗地雷为圆心: 复刻场景 + 把单位影子挂到该槽的 feed 上.

    场景自带 clear 矩形, 会把地雷一起抹掉, 所以铺完要原样钉回去 —— 那颗雷
    既是圆心也是"这里已经在投影"的标记.
    slot 决定 marker 的 id 段, 所以多块沙盘可以同时投影、互不覆盖.
    """
    slot = int(slot)
    if slot in _projs(w):
        end_projection(w, slot, "这个沙盘又放了一颗地雷", services=services)
    if not scene_path:
        # feed 自带场景出处时(mlogsim --scene X --push F)就不用手工再指一遍
        got = feed_scene(feed)
        if got:
            scene_path = got["path"]
    x, y = int(x), int(y)
    ax, ay = (int(anchor[0]), int(anchor[1])) if anchor else (x, y)
    shift = [0.0, 0.0]
    placed = 0
    builds = []
    if scene_path:
        import scene as scene_mod
        sc = scene_mod.load(str(scene_path))
        # anchor 给了就按场景自己的锚点摆(多场景 = 固定区域), 否则以雷为圆心
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
        w.js(services.REPLACE_MINE_JS % {"x": x, "y": y, "block": json.dumps(services.MINE_BLOCK)})
    if builds:
        try:
            services.resync_builds(w, builds)
        except Exception as exc:  # noqa: BLE001
            print("[warn] 补发代码/配置失败: %s" % exc, flush=True)
        # 客户端可能还没把这一格建出来(同帧 setNet + tileConfig), 隔一秒再补一次
        def _late(wd_=w, bl=list(builds)):
            time.sleep(1.2)
            try:
                services.resync_builds(wd_, bl)
            except Exception:  # noqa: BLE001
                pass
        threading.Thread(target=_late, daemon=True).start()
    services.mirror_watch(w, feed, slot=slot, dx=shift[0], dy=shift[1], cell=[ax, ay])
    _projs(w)[slot] = {"center": (x, y), "builds": builds, "feed": feed,
                       "scene": scene_path}
    w._proj_seen = getattr(w, "_proj_seen", set())
    w._proj_seen.add("%d,%d" % (x, y))
    services.sb_event(w, slot, "proj start, bld %d" % len(builds))
    if tell:
        services.chat(w, "投影已开始：地雷 (%d,%d) 就是圆心，拆掉它就结束" % (x, y))
    return {"ok": True, "x": x, "y": y, "feed": feed, "scene": scene_path,
            "placed": placed, "shift": shift, "slot": slot}


def end_projection(w, slot, why="地雷被拆除", *, services):
    """拆掉圆心那颗脉冲地雷 = 结束这块沙盘的投影: 停影子、拆建筑、放回地雷位."""
    slot = int(slot)
    p = _projs(w).get(slot)
    if p is None:
        return {"ok": False, "error": "not projecting"}
    cx = p.get("center")
    services.mirror_stop(w, slot)
    key = "%d,%d" % (int(cx[0]), int(cx[1]))
    getattr(w, "_proj_seen", set()).discard(key)
    # 铺下去的建筑要一起拆掉(含核心), 否则地面上留下一堆跑不动的空壳
    builds = p.get("builds") or []
    dn = 0
    if builds:
        try:
            res = w.js(services.DEMOLISH_JS % {"list": json.dumps(builds)})
            for ln in (res or []):
                s = str(ln)
                if s.startswith("DEMOLISH\t"):
                    dn = int(float(s.split("\t")[1]))
        except Exception as exc:
            print("[warn] 拆除投影建筑失败: %s" % exc)
    del _projs(w)[slot]
    # 再清一次 marker: 走 setNet 拆楼会触发一批事件, 万一有帧漏进来也在这里扫掉
    try:
        w.js(services.MS_CLEAR_JS % {"slot": int(slot)})
    except Exception:  # noqa: BLE001
        pass
    services.sb_event(w, slot, "proj end, razed %d" % dn)
    print("[info] 投影结束 (slot %d, %d,%d)：%s，拆掉 %d 座建筑"
          % (slot, int(cx[0]), int(cx[1]), why, dn), flush=True)
    services.chat(w, "投影已结束：%s（拆掉 %d 座建筑）" % (why, dn))
    return {"ok": True, "ended": [int(cx[0]), int(cx[1])], "why": why, "slot": slot}


def start_projection(w, meta, slot=0, *, services):
    """手动开投影(projection op): 没给坐标就用 meta 里的 scene_at / 世界中心."""
    meta = meta or {}
    feed = meta.get("feed")
    if not feed:
        return {"ok": False, "error": "need feed path (mlogsim --push)"}
    if feed_age(feed) is None:
        return {"ok": False, "error": "feed 不存在: %s" % feed}
    spot = meta.get("scene_at") or meta.get("at") or list(getattr(w, "base", (0, 0)))
    return project_at(w, spot[0], spot[1], feed, meta.get("scene"), slot=slot, services=services)
