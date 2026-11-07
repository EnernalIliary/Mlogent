"""生成“色块 vs 原版贴图”对照图（同一张蓝图，两种渲染并排）。"""
import pathlib
import sys

from PIL import Image, ImageDraw

R = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R))
from mbo import preview, sprites  # noqa: E402
from mbo.gamedata import GameData  # noqa: E402

gd = GameData()
ss = sprites.discover()
outdir = R / "docs" / "img"
outdir.mkdir(parents=True, exist_ok=True)


def label(img, text):
    d = ImageDraw.Draw(img)
    f = preview._font(20)
    d.rectangle([0, 0, img.size[0] - 1, 30], fill=(26, 28, 32))
    d.text((10, 5), text, font=f, fill=(235, 238, 244))
    return img


for run in ("d10", "p-one"):
    run_dir = R / "runs" / run
    trace, lay, _ = preview.load_run(run_dir)
    title = "%s · %s" % (run, trace.get("target", ""))
    sub = preview.summarize(run_dir, trace)
    a = label(preview.render_png(lay, gd, title, sub, scale=3, sprites=None), "色块示意")
    b = label(preview.render_png(lay, gd, title, sub, scale=3, sprites=ss), "原版贴图")
    W = a.size[0] + b.size[0] + 12
    H = max(a.size[1], b.size[1])
    canvas = Image.new("RGB", (W, H), (18, 19, 22))
    canvas.paste(a, (0, 0))
    canvas.paste(b, (a.size[0] + 12, 0))
    out = outdir / ("compare-%s.png" % run)
    canvas.save(out)
    print("已生成", out, canvas.size)
