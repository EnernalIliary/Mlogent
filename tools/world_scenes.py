"""Feed reading, scene loading and layout, independent of projection threads."""
import json
import math
import os
import time

def feed_age(path):
    """Seconds since the feed file was last written; None if it is not there."""
    try:
        return max(0.0, time.time() - os.stat(path).st_mtime)
    except OSError:
        return None


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
