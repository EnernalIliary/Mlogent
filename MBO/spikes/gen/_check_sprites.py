"""自检：贴图渲染是否真的贴上了、方向是否按 rotation 生效。"""
import pathlib
import sys

from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from mbo import preview, sprites  # noqa: E402
from mbo.model import Layout, ROT  # noqa: E402
from mbo.gamedata import GameData  # noqa: E402

R = pathlib.Path(__file__).resolve().parents[2]
gd = GameData()
ss = sprites.discover()
print("贴图根目录:", ss.root, "索引", ss.names())

# 1) 贴图能不能找到 + 尺寸对不对
for name in ("conveyor", "graphite-press", "item-source", "item-void", "router",
             "overflow-gate", "container", "vault", "power-source", "power-node"):
    p = ss.path(name)
    print("%-16s %s" % (name, "MISSING" if p is None else "%s (%s)" % (p.name, Image.open(p).size)))

# 2) 单格渲染：四条带子（0/1/2/3）逐格放，看像素是不是各向不同
sizes = {n: b.size for n, b in gd.blocks.items()}
lay = Layout(8, 4, sizes, name="rot", description="rotation probe")
for rot in range(4):
    lay.add("conveyor", 1 + rot * 2, 1, rot)
    lay.add("item-source", 1 + rot * 2, 2, 0)

img = preview.render_png(lay, gd, "rotation probe", "conveyor rot=0..3", scale=3, sprites=ss)
out = R / "out/_sprite_check_rot.png"
out.parent.mkdir(exist_ok=True)
img.save(out)
print("已写", out, img.size)

# 3) 比对每格中心区域与原始贴图（应几乎一致；网格线只占边缘 1px）
cell = preview.CELL * 3
g = preview.geometry(lay, 3)
sizes_px = g["cell"] + 1
for rot in range(4):
    tx = 1 + rot * 2
    crop = img.crop((g["ox"] + tx * cell + 6, g["oy"] + 1 * cell + 6,
                     g["ox"] + tx * cell + cell - 6, g["oy"] + 1 * cell + cell - 6))
    ref = ss.tile_image("conveyor", 1, rot, True, cell_px=cell).resize(crop.size)
    diff = sum(abs(a - b) for pa, pb in zip(crop.getdata(), ref.getdata())
               for a, b in zip(pa[:3], pb[:3])) / (crop.size[0] * crop.size[1] * 3)
    print("rot=%d 与期望贴图平均像素差 %.2f" % (rot, diff))

# 4) 四个方向彼此必须不同（防止 rotation 被忽略）
cells = []
for rot in range(4):
    tx = 1 + rot * 2
    cells.append(img.crop((g["ox"] + tx * cell, g["oy"] + cell,
                           g["ox"] + tx * cell + cell, g["oy"] + 2 * cell)).tobytes())
import itertools  # noqa: E402
same = [(i, j) for i, j in itertools.combinations(range(4), 2) if cells[i] == cells[j]]
print("方向相同的格对:", same if same else "无（四向都不同）")

# 5) p-one 真实蓝图：贴图色数应远多于色块版
run = R / "runs/p-one"
trace, p_lay, _ = preview.load_run(run)
a = preview.render_png(p_lay, gd, "x", "", scale=2, sprites=None)
b = preview.render_png(p_lay, gd, "x", "", scale=2, sprites=ss)
print("色块版颜色数 %d / 贴图版颜色数 %d" % (len(a.convert("RGB").getcolors(1 << 20)),
                                            len(b.convert("RGB").getcolors(1 << 20))))
