"""Projection scheduling with explicitly injected world actions and scripts."""
import json
import os
import threading
import time
from world_scenes import (scenes_from_feeds, load_dir_scenes, layout_scenes,
                          feed_age, feed_anchor, feed_bbox, feed_world, world_size)

def projection_director(w, feed, scene_path=None, at=None, poll=0.5,
                        fresh=25.0, lim=10, scenes=None, frames=True,
                        frame_floor="marker", at_cell=64, feeds=None, auto=True,
                        hold=0.0, *, services):
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
            w.js(services.FRAME_SWEEP_JS)
        except Exception:  # noqa: BLE001
            pass
    try:
        # 日志板同理: 上一轮进程画的面板要先擦, 否则叠一层旧文字
        w.js(services.SB_SWEEP_JS)
    except Exception:  # noqa: BLE001
        pass
    w._dir_scene = (w._dir_scenes[0]["path"] if w._dir_scenes else scene_path)
    w._dir_at = list(at) if at else None
    w._dir_stop = False
    w._proj_seen = getattr(w, "_proj_seen", set())

    def loop():
        while not getattr(w, "_dir_stop", False):
            time.sleep(poll)
            if getattr(w, "_dir_stop", False):
                break
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
                    win = max(services.FRAME_LIVE_MAX, float(hold or 0))
                    for si, d in enumerate(w._dir_scenes):
                        key0 = d["path"]
                        age0 = feed_age(d.get("feed"))
                        live = age0 is not None and age0 <= win
                        # 自动投影: 有仿真就自己铺, 不需要玩家放雷
                        if auto and d.get("feed"):
                            try:
                                if live and si not in services._projs(w):
                                    rr = services.project_at(w, int(d["anchor"][0]), int(d["anchor"][1]),
                                                    d["feed"], key0, tell=False,
                                                    anchor=d["anchor"], slot=si, pin=False)
                                    services.chat(w, "自动投影：%s" % d["label"])
                                    print("[info] 自动投影 %s @%s slot %d, 建筑 %d 块"
                                          % (d["label"], d["anchor"], si,
                                             rr.get("placed", 0)), flush=True)
                                elif (not live) and si in services._projs(w):
                                    services.end_projection(w, si, "仿真停了（%s）"
                                                   % os.path.basename(d["feed"] or "-"))
                            except Exception as exc:  # noqa: BLE001
                                print("[warn] 自动投影失败 %s: %s" % (d["label"], exc),
                                      flush=True)
                        if live != bool(onmap.get(key0)):
                            if live:
                                try:
                                    n0 = services.frame_paint(w, d["frame"], key0)
                                    print("[info] 仿真在跑（%s）：%s 的落雷框已画出（%d 个点）"
                                          % (os.path.basename(d["feed"] or "-"),
                                             d["label"], n0), flush=True)
                                except Exception as exc:  # noqa: BLE001
                                    print("[warn] 画边界失败 %s: %s" % (d["label"], exc),
                                          flush=True)
                            else:
                                try:
                                    services.frame_clear(w, key0)
                                    services.frame_clear(w, key0 + "@live")
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
                                    services.frame_paint(w, bb, key0 + "@live", step=stp,
                                                radius=5.0, color=services.LIVE_COLOR)
                                    livemap[key0] = tuple(bb)
                                except Exception as exc:  # noqa: BLE001
                                    print("[warn] 画仿真范围失败 %s: %s"
                                          % (d["label"], exc), flush=True)
                        else:
                            livemap.pop(key0, None)
                    w._dir_frames_on = onmap
                    w._dir_live = livemap
                # 每块沙盘的文本日志板: 标题 / feed 龄 / 投影状态 / 建筑数 / 单位数 / 事件
                win2 = max(services.FRAME_LIVE_MAX, float(hold or 0))
                prev2 = getattr(w, "_sb_live", None)
                if not isinstance(prev2, dict):
                    prev2 = {}
                    w._sb_live = prev2
                for si2, d2 in enumerate(w._dir_scenes):
                    try:
                        age2b = feed_age(d2.get("feed"))
                        live2 = age2b is not None and age2b <= win2
                        if bool(prev2.get(si2)) != live2:
                            services.sb_event(w, si2, "feed live" if live2 else "feed lost")
                            prev2[si2] = live2
                        if live2:
                            services.sb_render(w, si2, d=d2, age=age2b, live=live2)
                        elif services._sb_store(w).get(int(si2)):
                            # 没有仿真就别留板子(和"没仿真不画框"同一条规矩):
                            # sb_clear 会把 store/cache 一起清掉, 下一轮就不会再发 js
                            services.sb_clear(w, si2)
                    except Exception as exc:  # noqa: BLE001
                        print("[warn] 日志板 %s: %s" % (d2.get("label"), exc), flush=True)
                # 每块沙盘各自看圆心那颗雷还在不在(直接读格子上的方块名, 事件顺序不可靠)
                # 自动模式下根本不钉地雷, 也不该被地雷事件驱动 —— 整段跳过.
                for sl in ([] if auto else sorted(services._projs(w).keys())):
                    p = services._projs(w)[sl]
                    cx = p.get("center")
                    st = w.js(services.MINE_STATE_JS % {"x": int(cx[0]), "y": int(cx[1])})
                    cur = str(st[0]).strip() if st else ""
                    if cur != services.MINE_BLOCK:
                        services.end_projection(w, sl, "圆心那颗脉冲地雷不在了")
                        continue
                    # 仿真进程死了 / 被 --js-timeout 掐了: 影子会冻结在最后一帧,
                    # 留在场上只会误导, 超过 60 s 没新帧就自动收摊
                    age2 = feed_age(p.get("feed"))
                    if age2 is not None and age2 > 60.0:
                        services.end_projection(w, sl, "仿真 feed 已经 %.0f s 没更新了" % age2)
                hits = []
                out = [] if auto else (w.js(services.MINE_HITS_JS) or [])
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
                        services.chat(w, "这里没有配仿真 feed，放地雷不会有影子")
                        w._proj_seen.add(key)
                        continue
                    if pick is None:
                        # 场景是固定排布的, 框外放雷没有"最近的场景"可言 —— 直接拒绝,
                        # 免得复刻出来的东西和框对不上(以前会以雷为圆心乱铺)
                        services.chat(w, "这颗地雷没落在任何沙盘边界里，先在框里放才会有投影")
                        w._proj_seen.add(key)
                        continue
                    if not feed_now:
                        services.chat(w, "这个沙盘没有配仿真 feed，先给 --watch-feed 补一条")
                        w._proj_seen.add(key)
                        continue
                    age = feed_age(feed_now)
                    if age is None:
                        services.chat(w, "还没看到仿真在跑（%s 不存在），先起 mlogsim"
                             % os.path.basename(feed_now))
                        w._proj_seen.add(key)
                        continue
                    if age > 25.0:
                        services.chat(w, "仿真 feed %s 已经 %.0f s 没更新了，先把 mlogsim 起起来再放雷"
                             % (os.path.basename(feed_now), age))
                        w._proj_seen.add(key)
                        continue
                    r = services.project_at(w, x, y, feed_now, pick, anchor=anchor, slot=slot_i)
                    print("[info] 投影 %s @(%d,%d) slot %d, 建筑 %d 块, 仿真帧龄 %.1fs"
                          % (label or "-", x, y, slot_i, r.get("placed", 0), age),
                          flush=True)
            except Exception as exc:
                print("[warn] 投影导演: %s" % exc, flush=True)

    th = threading.Thread(target=loop, name="projection-director", daemon=True)
    th.start()
    w._dir_thread = th
    return True


CONTROL_OPERATIONS = frozenset(("arm", "frames", "projection", "projstat", "sblog"))

def control(w, req, *, services, audit):
    op = (req.get("op") or "").strip()
    if op == "arm":
        # 开启"玩家放地雷即投影"的监听: 不自己放雷, 只等玩家放
        raw_feeds0 = req.get("feeds") or req.get("feeds_arr")
        if isinstance(raw_feeds0, str):
            raw_feeds0 = [raw_feeds0]
        feed = str(req.get("feed") or (raw_feeds0[0] if raw_feeds0 else None)
                   or getattr(w, "mirror_feed", None) or "")
        if not feed and not (raw_feeds0 or []):
            return {"ok": False, "error": "need feed path (mlogsim --push)"}
        # 重复 arm = 换场景/换边界: 先停旧导演、擦掉旧边界, 再起新的(不重启世界)
        if getattr(w, "_dir_started", False):
            w._dir_stop = True
            old_thread = getattr(w, "_dir_thread", None)
            if old_thread is not None:
                old_thread.join(timeout=3.0)
                if old_thread.is_alive():
                    return {"ok": False, "error": "previous projection director is still stopping; retry arm"}
            w._dir_started = False
            if getattr(w, "_dir_frames", False):
                try:
                    services.frame_clear(w)
                except Exception:  # noqa: BLE001
                    pass
        # 旧槽位会阻止 auto 分支重新创建，必须先回收其建筑和 feed 监听。
        for slot in list(getattr(w, "_projs", {})):
            services.end_projection(w, slot, "投影配置已更新")
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
        started = services.projection_director(w, feed_list[0] if feed_list else feed, None,
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
            out = w.js(services.FRAME_LIST_JS)
            return {"ok": True, "frames": (str(out[0]) if out else ""),
                    "scenes": [{"path": d["path"], "label": d["label"],
                                "frame": d["frame"], "anchor": d["anchor"]}
                               for d in getattr(w, "_dir_scenes", [])]}
        if act == "clear":
            n = services.frame_clear(w, req.get("scene"))
            return {"ok": True, "restored": n}
        if act == "paint":
            n = 0
            for d in getattr(w, "_dir_scenes", []):
                n += services.frame_paint(w, d["frame"], d["path"],
                                 step=int(req.get("step") or 1),
                                 radius=float(req.get("radius") or 7.0))
            return {"ok": True, "painted": n,
                    "scenes": [d["path"] for d in getattr(w, "_dir_scenes", [])]}
        return {"ok": False, "error": "action must be list|clear|paint"}
    if op == "projection":
        on = bool(req.get("on", True))
        if not on:
            # 关全部槽: 每块沙盘的影子一起收掉
            services.mirror_stop(w)
            return {"ok": True, "on": False}
        slot = int(req.get("slot") or 0)
        mir = services._mirror_slot(w, slot)
        meta = {"feed": req.get("feed") or mir.get("feed")
                or getattr(w, "mirror_feed", None),
                "scene": req.get("scene"), "scene_at": req.get("at")}
        r = services.start_projection(w, meta, slot=slot)
        return r
    if op == "projstat":
        # 多槽: 每块沙盘一份 {slot, center, builds, feed, off}
        rows = []
        props = getattr(w, "_projs", None) or {}
        for sl in sorted(props.keys()):
            p = props[sl]
            mir = services._mirror_slot(w, sl)
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
            rows = services.sb_event(w, slot, txt)
            try:
                services.sb_render(w, slot, d=d, age=feed_age((d or {}).get("feed")),
                          live=False, force=True)
            except Exception as exc:  # noqa: BLE001
                return {"ok": False, "error": "render failed: %s" % exc}
            return {"ok": True, "slot": slot, "lines": list(rows)}
        if act == "clear":
            n = services.sb_clear(w, slot if req.get("slot") is not None else None)
            try:
                w.js(services.SB_SWEEP_JS)
            except Exception:  # noqa: BLE001
                pass
            return {"ok": True, "cleared": n}
        out = {}
        win3 = max(services.FRAME_LIVE_MAX, float(getattr(w, "_dir_hold", 0.0) or 0.0))
        for si, dd in enumerate(getattr(w, "_dir_scenes", []) or []):
            ag = feed_age(dd.get("feed"))
            out[str(si)] = services.sb_lines(w, si, d=dd, age=ag,
                                    live=(ag is not None and ag <= win3))
        return {"ok": True, "panels": out}
    return NotImplemented
