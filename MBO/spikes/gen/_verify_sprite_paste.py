"""逐块核对（修正版）：只在贴图不透明的像素上比对 RGB，透明处应露出背景。"""
import pathlib
import sys

from PIL import Image

R = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R))
from mbo import preview, sprites  # noqa: E402
from mbo.gamedata import GameData  # noqa: E402

gd = GameData()
ss = sprites.discover()
bad = 0
checked = 0
for d in sorted((R / "runs").iterdir()):
    if not (d / "trace.json").exists():
        continue
    _, lay, _gd = preview.load_run(d)
    scale = 2
    img = preview.render_png(lay, gd, "chk", "", scale=scale, sprites=ss).convert("RGBA")
    g = preview.geometry(lay, scale)
    cell = g["cell"]
    for t in lay.tiles:
        blk = gd.block(t.block)
        s = lay.sizes.get(t.block, 1)
        tx, ty = lay.origin(t.block, t.x, t.y)
        ref = ss.tile_image(t.block, s, t.rotation, bool(getattr(blk, "rotate", False)),
                            cell_px=int(cell))
        if ref is None:
            print("%s: %s 无贴图" % (d.name, t.block))
            continue
        x0 = int(g["ox"] + (tx - g["xs"]) * cell)
        y0 = int(g["oy"] + (ty - g["ys"]) * cell)
        got = img.crop((x0, y0, x0 + ref.size[0], y0 + ref.size[1]))
        checked += 1
        rp, gp = list(ref.getdata()), list(got.getdata())
        opaque = [(a, b) for a, b in zip(rp, gp) if a[3] == 255]
        diff = sum(1 for a, b in opaque if a[:3] != b[:3])
        if diff:
            print("%s: %s@(%d,%d) 不透明像素 %d 中 %d 个不同" % (d.name, t.block, t.x, t.y,
                                                          len(opaque), diff))
            bad += 1
print("核对 %d 个方块，%d 个不一致" % (checked, bad))
