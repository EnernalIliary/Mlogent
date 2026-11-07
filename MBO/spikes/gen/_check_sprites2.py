"""精确定位贴图渲染的像素差来源。"""
import pathlib
import sys

from PIL import Image

R = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R))

from mbo import preview, sprites  # noqa: E402
from mbo.gamedata import GameData  # noqa: E402
from mbo.model import Layout  # noqa: E402

gd = GameData()
ss = sprites.discover()
sizes = {n: b.size for n, b in gd.blocks.items()}

for name in ("graphite-press", "vault", "conveyor"):
    lay = Layout(8, 6, sizes, name="px", description="px")
    if not lay.free(name, 1, 1):
        raise SystemExit("no space")
    lay.add(name, 1, 1, 0)
    scale = 3
    img = preview.render_png(lay, gd, "px", "", scale=scale, sprites=ss).convert("RGBA")
    g = preview.geometry(lay, scale)
    cell = g["cell"]
    s = sizes[name]
    tx, ty = lay.origin(name, 1, 1)
    x0 = g["ox"] + (tx - g["xs"]) * cell
    y0 = g["oy"] + (ty - g["ys"]) * cell
    size_px = s * cell
    got = img.crop((x0, y0, x0 + size_px, y0 + size_px))
    ref = ss.tile_image(name, s, 0, False, cell_px=cell)
    print("%-16s cell=%d sprite_px=%d got=%s ref=%s" % (name, cell, size_px, got.size, ref.size))
    # 只在 ref 不透明处比较（贴图有透明背景）
    diffs = []
    worst = None
    for (rp, gp) in zip(ref.getdata(), got.getdata()):
        if rp[3] < 250:
            continue
        d = sum(abs(a - b) for a, b in zip(rp[:3], gp[:3])) / 3.0
        diffs.append(d)
        if worst is None or d > worst[0]:
            worst = (d, rp, gp)
    print("  不透明像素 %d 平均差 %.2f 最大差 %.1f %s" % (len(diffs), sum(diffs) / max(len(diffs), 1),
                                                    worst[0] if worst else -1, worst[1:3] if worst else ""))
