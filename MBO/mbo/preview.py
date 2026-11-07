"""把 Layout 渲染成便于人审阅的俯视图。

三种形态（都从 runs/<run_id>/trace.json 重建，不依赖游戏）：
  - PNG  : 每个格子一块颜色 + 方块短名 + 朝向箭头 + 电力连线，附标题与图例
  - ASCII: 终端直接看（适合快速 diff / 贴进 issue）
  - HTML : `--all` 生成 runs/index.html 画廊，一页看完所有 run（含预测/实测/结论）

坐标口径沿用 R1：Tile 存的是**中心格**；渲染时按 size 展开成 footprint。
"""

from __future__ import annotations

import html
import json
import os
import pathlib

from .model import DIRV, Layout, read_points
from .gamedata import GameData

CELL = 26          # 每格像素
PAD = 18           # 边距
LEGEND_H = 74      # 图例高度
MARGIN = 1         # 裁剪时四周留的空格

COLORS = {
    "item-source": (150, 90, 200),
    "liquid-source": (90, 150, 210),
    "power-source": (235, 200, 70),
    "power-node": (240, 220, 120),
    "conveyor": (110, 120, 135),
    "duct": (120, 140, 150),
    "container": (215, 140, 70),
    "vault": (205, 120, 55),
    "core": (200, 60, 60),
    "crafter": (90, 175, 120),
    "drill": (150, 130, 90),
    "wall": (70, 70, 70),
    "gate": (200, 110, 165),
    "void": (170, 80, 200),
}
BG = (24, 26, 30)
GRID = (45, 48, 54)
FG = (235, 235, 235)
LINK = (255, 210, 60)

SHORT = {
    "silicon-smelter": "SMELT",
    "graphite-press": "PRESS",
    "kiln": "KILN",
    "surge-smelter": "SURGE",
    "item-source": "SRC",
    "power-source": "PSRC",
    "power-node": "PN",
    "container": "CONT",
    "vault": "VAULT",
    "conveyor": "BELT",
    "underflow-gate": "UFLOW",
    "overflow-gate": "OVFLW",
    "item-void": "VOID",
    "core-shard": "CORE",
}


def _family(gd: GameData, name: str) -> str:
    b = gd.blocks.get(name)
    if b is None:
        return "wall"
    cat = (b.category or "").lower()
    if b.is_sandbox_power:
        return "power-source"
    if name in ("power-node", "power-node-large", "beam-node", "beam-tower"):
        return "power-node"
    if name == "container":
        return "container"
    if name == "vault":
        return "vault"
    if name in ("overflow-gate", "underflow-gate"):
        return "gate"
    if name in ("item-void", "liquid-void"):
        return "void"
    if name.startswith("core-"):
        return "core"
    if "conveyor" in name or "duct" in name or name in ("junction", "router", "sorter",
                                                       "unloader", "bridge-conveyor"):
        return "conveyor" if "conveyor" in name else "duct"
    if name.endswith("-source"):
        return "item-source" if not name.startswith("liquid") else "liquid-source"
    if b.recipe is not None:
        return "crafter"
    if "drill" in name:
        return "drill"
    if cat.startswith("power"):
        return "power-node"
    return "wall"


def _font(size: int):
    from PIL import ImageFont
    for cand in (
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\consola.ttf",
    ):
        if os.path.exists(cand):
            try:
                return ImageFont.truetype(cand, size)
            except OSError:
                pass
    return ImageFont.load_default()


def _arrow(draw, x0, y0, cell, rot, color):
    dx, dy = DIRV.get(rot, (1, 0))
    cx, cy = x0 + cell / 2, y0 + cell / 2
    L = cell * 0.34
    if dx:
        pts = [(cx + dx * L, cy), (cx - dx * L * 0.5, cy - L * 0.55),
               (cx - dx * L * 0.5, cy + L * 0.55)]
    else:
        pts = [(cx, cy - dy * L), (cx - L * 0.55, cy + dy * L * 0.5),
               (cx + L * 0.55, cy + dy * L * 0.5)]
    draw.polygon(pts, fill=color)


def bbox(lay: Layout):
    """已用区域的格子范围（含 MARGIN），无方块时返回整张画布。"""
    if not lay.tiles:
        return 0, 0, lay.w - 1, lay.h - 1
    xs, ys, xe, ye = lay.w, lay.h, -1, -1
    for t in lay.tiles:
        s = lay.sizes.get(t.block, 1)
        tx, ty = lay.origin(t.block, t.x, t.y)
        xs, ys = min(xs, tx), min(ys, ty)
        xe, ye = max(xe, tx + s - 1), max(ye, ty + s - 1)
    xs, ys = max(0, xs - MARGIN), max(0, ys - MARGIN)
    xe, ye = min(lay.w - 1, xe + MARGIN), min(lay.h - 1, ye + MARGIN)
    return xs, ys, xe, ye


def geometry(lay: Layout, scale: int = 2):
    """渲染几何：格子像素边长、裁剪范围、左上角像素偏移、画布尺寸。测试与预览共用。"""
    xs, ys, xe, ye = bbox(lay)
    cell = CELL * scale
    cw, ch = xe - xs + 1, ye - ys + 1
    return {"cell": cell, "xs": xs, "ys": ys, "xe": xe, "ye": ye,
            "ox": PAD, "oy": PAD + 54,
            "W": cw * cell + PAD * 2, "H": ch * cell + PAD * 2 + 58 + LEGEND_H}


def render_png(lay: Layout, gd: GameData, title: str, subtitle: str = "", scale: int = 2,
               sprites=None):
    """渲染俯视图。给 `sprites`（mbo.sprites.SpriteSet）就贴原版贴图，否则画色块。"""
    from PIL import Image, ImageDraw

    g = geometry(lay, scale)
    xs, ys, xe, ye = g["xs"], g["ys"], g["xe"], g["ye"]
    cw, ch, cell, W, H = xe - xs + 1, ye - ys + 1, g["cell"], g["W"], g["H"]
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    f_title = _font(17 * scale)
    f_sub = _font(12 * scale)
    f_small = _font(max(9, 9 * scale))

    d.text((PAD, 10), title, font=f_title, fill=FG)
    if subtitle:
        d.text((PAD, 10 + 22 * scale), subtitle, font=f_sub, fill=(175, 180, 190))

    ox, oy = g["ox"], g["oy"]

    def px(cx, cy):
        return ox + (cx - xs) * cell, oy + (cy - ys) * cell

    d.rectangle([ox, oy, ox + cw * cell, oy + ch * cell], outline=GRID)
    for gx in range(cw + 1):
        d.line([(ox + gx * cell, oy), (ox + gx * cell, oy + ch * cell)], fill=GRID)
    for gy in range(ch + 1):
        d.line([(ox, oy + gy * cell), (ox + cw * cell, oy + gy * cell)], fill=GRID)

    for t in lay.tiles:
        if t.block not in ("power-node", "power-node-large", "power-source"):
            continue
        pts = read_points(t.config) or []
        cx0, cy0 = px(t.x, t.y)
        for (dx, dy) in pts:
            x2, y2 = px(t.x + dx, t.y + dy)
            d.line([(cx0 + cell / 2, cy0 + cell / 2), (x2 + cell / 2, y2 + cell / 2)],
                   fill=LINK, width=max(1, scale))

    for t in lay.tiles:
        fam = _family(gd, t.block)
        col = COLORS.get(fam, (90, 90, 90))
        s = lay.sizes.get(t.block, 1)
        tx, ty = lay.origin(t.block, t.x, t.y)
        x0, y0 = px(tx, ty)
        blk = gd.block(t.block)
        tex = None
        if sprites is not None:
            tex = sprites.tile_image(t.block, s, t.rotation,
                                     bool(getattr(blk, "rotate", False)), cell_px=int(cell))
        if tex is not None:
            img.paste(tex, (int(x0), int(y0)), tex)
            continue
        d.rectangle([x0 + 1, y0 + 1, x0 + cell * s - 1, y0 + cell * s - 1], fill=col,
                    outline=(20, 20, 22))
        if fam in ("conveyor", "duct", "crafter", "drill"):
            _arrow(d, x0, y0, cell * s, t.rotation, (20, 20, 22))
        if cell >= 20:
            label = SHORT.get(t.block, t.block[:6].upper())
            d.text((x0 + 3, y0 + cell * s - 12 * scale), label, font=f_small, fill=(15, 15, 18))

    ly = H - LEGEND_H + 6
    fams = [("item-source", "物料源"), ("conveyor", "物流"), ("crafter", "生产"),
            ("container", "产物仓"), ("power-node", "节点"), ("power-source", "电源"),
            ("gate", "物流门"), ("void", "黑洞")]
    x = PAD
    for fam, name in fams:
        d.rectangle([x, ly + 3, x + 14, ly + 17], fill=COLORS[fam])
        d.text((x + 20, ly + 2), name, font=f_sub, fill=FG)
        x += 20 + 11 * len(name) + 22
    st = lay.stats()
    d.text((PAD, ly + 26),
           "blocks=%d  tiles=%d  canvas=%dx%d  crop=(%d,%d)-(%d,%d)"
           % (st["blocks"], st["tiles"], lay.w, lay.h, xs, ys, xe, ye),
           font=f_sub, fill=(175, 180, 190))
    return img


def render_ascii(lay: Layout, gd: GameData) -> str:
    ch = {"item-source": "S", "liquid-source": "L", "power-source": "P", "power-node": "n",
          "conveyor": "=", "duct": "-", "container": "C", "vault": "V", "core": "K",
          "crafter": "M", "drill": "d", "wall": ".", "gate": "+", "void": "x"}
    arrow = {0: ">", 1: "v", 2: "<", 3: "^"}
    xs, ys, xe, ye = bbox(lay)
    grid = [[" "] * (xe - xs + 1) for _ in range(ye - ys + 1)]
    for t in lay.tiles:
        fam = _family(gd, t.block)
        s = lay.sizes.get(t.block, 1)
        tx, ty = lay.origin(t.block, t.x, t.y)
        c = ch.get(fam, "?")
        if t.block in ("router", "junction", "sorter", "inverted-sorter"):
            c = "n"          # 这些是“节点”而不是带子，别画成箭头
        for yy in range(ty, ty + s):
            for xx in range(tx, tx + s):
                if xs <= xx <= xe and ys <= yy <= ye:
                    grid[yy - ys][xx - xs] = c
        if s == 1 and fam in ("conveyor", "duct", "crafter", "drill") \
                and t.block not in ("router", "junction", "sorter", "inverted-sorter"):
            grid[ty - ys][tx - xs] = arrow.get(t.rotation, "?")
    head = "    " + "".join(str((x + xs) // 10 % 10) for x in range(xe - xs + 1))
    ruler = "    " + "".join(str((x + xs) % 10) for x in range(xe - xs + 1))
    rows = ["%3d %s" % (y + ys, "".join(r)) for y, r in enumerate(grid)]
    st = lay.stats()
    return "\n".join([head, ruler] + rows +
                     ["", "blocks=%d tiles=%d  crop=(%d,%d)-(%d,%d)  "
                      "S=物料源 n=节点 P=电源 M=机器 >v<^=朝向 C=仓 +=物流门 x=黑洞" % (st["blocks"], st["tiles"],
                                                                    xs, ys, xe, ye)])


def load_run(run_dir: pathlib.Path, gd: GameData | None = None):
    gd = gd or GameData()
    trace = json.loads((run_dir / "trace.json").read_text(encoding="utf-8"))
    sizes = {n: b.size for n, b in gd.blocks.items()}
    lay = Layout.from_snapshot(trace["layout"], trace["canvas"][0], trace["canvas"][1],
                               sizes, name=trace.get("layout_name", ""),
                               description=trace.get("layout_description", ""))
    return trace, lay, gd


def summarize(run_dir: pathlib.Path, trace: dict) -> str:
    mp = run_dir / "metrics.json"
    if not mp.exists():
        return ""
    m = json.loads(mp.read_text(encoding="utf-8"))
    pred = m.get("predicted", {})
    eng = (m.get("engine") or {}).get("metrics", {})
    parts = ["预测 %.3f/s" % pred.get("expected_rate", 0.0)]
    if eng:
        r, p = eng.get("rate", 0.0), max(pred.get("expected_rate", 1.0), 1e-9)
        parts.append("实测 %.3f/s（%+.1f%%）" % (r, 100.0 * (r - p) / p))
        parts.append("wall %.1fs" % (m.get("engine") or {}).get("wall_s", 0.0))
    v = m.get("verdict", {})
    parts.append("Gate %s" % ("PASS" if v.get("pass") else "FAIL"))
    return "  ·  ".join(parts)


def write_png(run_dir: pathlib.Path, out: pathlib.Path | None = None, scale: int = 2,
              sprites=None):
    trace, lay, gd = load_run(run_dir)
    title = "%s  ·  %s" % (trace.get("run_id", run_dir.name), trace.get("target", ""))
    img = render_png(lay, gd, title, summarize(run_dir, trace), scale=scale, sprites=sprites)
    out = out or (run_dir / "preview.png")
    img.save(out)
    return out, lay


def write_index(runs_dir: pathlib.Path, out: pathlib.Path | None = None):
    rows = []
    for d in sorted(p for p in runs_dir.iterdir() if (p / "trace.json").exists()):
        trace, lay = load_run(d)[:2]
        if not (d / "preview.png").exists():
            write_png(d)
        m = json.loads((d / "metrics.json").read_text(encoding="utf-8"))
        rows.append((d.name, trace.get("target", ""), m, m.get("verdict", {}), d))
    out = out or (runs_dir / "index.html")
    cells = []
    for name, target, m, v, d in rows:
        pred = m.get("predicted", {}).get("expected_rate", 0)
        eng = (m.get("engine") or {}).get("metrics", {}).get("rate")
        rate = "—" if eng is None else "%.3f/s（%+.1f%%）" % (eng, 100 * (eng - pred) / max(pred, 1e-9))
        ok = v.get("pass")
        cells.append(
            "<figure><figcaption><b>%s</b> · %s<br>预测 %.3f/s · 实测 %s<br>"
            "<span class='%s'>%s</span></figcaption>"
            "<img src='%s/preview.png'></figure>"
            % (html.escape(name), html.escape(str(target)), pred, rate,
               "ok" if ok else "bad", "PASS" if ok else "FAIL", html.escape(name)))
    doc = """<!doctype html><meta charset="utf-8"><title>MBO runs</title>
<style>
body{background:#181a1e;color:#e8e8ea;font:14px/1.5 system-ui,"Microsoft YaHei";margin:24px}
h1{font-size:20px}
figure{display:inline-block;vertical-align:top;margin:0 18px 18px 0;background:#20232a;
       border:1px solid #2e323b;border-radius:8px;padding:10px}
figcaption{margin-bottom:8px;color:#c9ccd4}
img{image-rendering:pixelated;max-width:900px}
.ok{color:#6ee7a0}.bad{color:#ff8b8b}
</style><h1>MBO 运行快照</h1><p>俯视图：紫=物料源，灰=物流，绿=生产，橙=产物仓，黄=电力。</p>
%s</body>""" % "\n".join(cells)
    out.write_text(doc, encoding="utf-8")
    return out, len(rows)
