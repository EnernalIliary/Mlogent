#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把配比结果画成一张 PNG 卡片（给 bot 直接发图用）。

数据来源就是 CLI 的 --format json --icons，所以卡片和网页/命令行用的是同一份算法结果，
这里只负责排版和把 base64 图标贴上去。

    python -X utf8 ratio-calc/card.py --item silicon --rate 5 --out card.png
    python -X utf8 ratio-calc/card.py --block ground-factory --count 2 \\
        --gen steam-generator --genfuel coal --out gf.png
    python -X utf8 ratio-calc/card.py --chain dagger --chainrate 0.05 --out chain.png

也可以喂现成的 json：  python ratio-calc/card.py --json result.json --out card.png
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "cli.cjs")

BG = (24, 27, 33)
PANEL = (32, 36, 44)
FG = (230, 233, 239)
DIM = (150, 157, 170)
ACCENT = (110, 190, 255)
GREEN = (120, 220, 150)
ORANGE = (255, 185, 100)
BLUE = (140, 180, 255)
LIQUID = (120, 200, 255)

PAD = 20
ROW_H = 34

_font_cache: dict = {}


def font(size: int, bold: bool = False):
    key = (size, bold)
    if key in _font_cache:
        return _font_cache[key]
    names = ["msyhbd.ttc", "msyh.ttc"] if bold else ["msyh.ttc", "msyhbd.ttc"]
    for n in names:
        p = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", n)
        if os.path.exists(p):
            f = ImageFont.truetype(p, size)
            _font_cache[key] = f
            return f
    f = ImageFont.load_default()
    _font_cache[key] = f
    return f


def icon_image(data_uri: str | None, px: int) -> Image.Image | None:
    if not data_uri or "," not in data_uri:
        return None
    try:
        raw = base64.b64decode(data_uri.split(",", 1)[1])
        im = Image.open(io.BytesIO(raw)).convert("RGBA")
    except Exception:
        return None
    if im.width != px:
        im = im.resize((px, px), Image.NEAREST)
    return im


def paste(canvas: Image.Image, im: Image.Image | None, x: int, y: int, px: int, letter: str = "?"):
    if im is None:
        d = ImageDraw.Draw(canvas)
        d.rounded_rectangle([x, y, x + px - 1, y + px - 1], 4, fill=(52, 58, 70), outline=(70, 78, 92))
        d.text((x + px / 2, y + px / 2), letter[:1].upper(), font=font(max(10, int(px * 0.5)), True),
               fill=DIM, anchor="mm")
        return
    canvas.alpha_composite(im, (x, y))


def fmt(x) -> str:
    if x is None:
        return "0"
    v = round(float(x), 3)
    return str(int(v)) if v == int(v) else ("%.3f" % v).rstrip("0").rstrip(".")


def load_result(args) -> dict:
    if args.json:
        with open(args.json, "r", encoding="utf-8") as f:
            return json.load(f)
    cmd = [args.node, CLI] + args.rest + ["--format", "json", "--icons"]
    if args.data:
        cmd += ["--data", args.data]
    out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        raise SystemExit((out.stderr or out.stdout or "cli 失败").strip())
    return json.loads(out.stdout)


class Card:
    def __init__(self, width: int = 700):
        self.width = width
        self.blocks: list = []      # 延迟绘制：先算高度

    # --- 排版原语 ---
    def title(self, text, icon=None, sub=None):
        self.blocks.append(("title", text, icon, sub))

    def section(self, text):
        self.blocks.append(("section", text))

    def row(self, icon, name, right, sub=None, accent=None):
        self.blocks.append(("row", icon, name, right, sub, accent))

    def note(self, text, color=None):
        self.blocks.append(("note", text, color))

    def blank(self, h=8):
        self.blocks.append(("blank", h))

    # --- 高度 ---
    def height(self) -> int:
        h = PAD
        for b in self.blocks:
            k = b[0]
            if k == "title":
                h += 56
            elif k == "section":
                h += 30
            elif k == "row":
                h += ROW_H
            elif k == "note":
                h += 24
            elif k == "blank":
                h += b[1]
        return h + PAD

    def render(self) -> Image.Image:
        W, H = self.width, self.height()
        img = Image.new("RGBA", (W, H), BG + (255,))
        d = ImageDraw.Draw(img)
        y = PAD
        for b in self.blocks:
            k = b[0]
            if k == "title":
                _, text, icon, sub = b
                im = icon_image(icon, 44)
                paste(img, im, PAD, y + 2, 44)
                d.text((PAD + 56, y + 4), text, font=font(22, True), fill=FG)
                if sub:
                    d.text((PAD + 56, y + 32), sub, font=font(13), fill=DIM)
                y += 56
            elif k == "section":
                d.text((PAD, y + 8), b[1], font=font(14, True), fill=ACCENT)
                d.line([PAD, y + 26, W - PAD, y + 26], fill=(48, 53, 64), width=1)
                y += 30
            elif k == "row":
                _, icon, name, right, sub, accent = b
                im = icon_image(icon, 26)
                paste(img, im, PAD + 2, y + 3, 26, name)
                d.text((PAD + 36, y + 6), name, font=font(15), fill=FG)
                rw = d.textlength(right, font=font(15, True))
                d.text((W - PAD - rw, y + 6), right, font=font(15, True), fill=accent or FG)
                if sub:
                    sw = d.textlength(sub, font=font(12))
                    d.text((W - PAD - rw - sw - 14, y + 9), sub, font=font(12), fill=DIM)
                y += ROW_H
            elif k == "note":
                _, text, color = b
                d.text((PAD, y + 4), text, font=font(12), fill=color or ORANGE)
                y += 24
            elif k == "blank":
                y += b[1]
        return img


def _machine_section(c, res):
    """工厂配比结果：机器清单是卡片的正文，放最前面。

    抽水机（钻井/泵）不算"工厂配比"里的机器：单列一节，电力仍然计入合计。"""
    allm = res.get("machines") or []
    pumps = res.get("pumps") or {}
    machines = [m for m in allm if not pumps.get(m.get("name"))]
    plist = [m for m in allm if pumps.get(m.get("name"))]
    total = sum(int(m.get("count") or 0) for m in machines)
    pump_power = sum(float(m.get("powerTotal") or 0) for m in plist)
    head = "工厂配比：%d 台 · 电力 %s/s" % (total, fmt(res.get("power")))
    if plist:
        head += "（含抽水 %s/s）" % fmt(pump_power)
    c.section(head)
    if not allm:
        c.note("· 没有要建的机器", DIM)
        return
    for m in machines:
        bits = []
        if m.get("powerTotal"):
            bits.append("电 %s/s" % fmt(m["powerTotal"]))
        outs = [o for o in (m.get("outItems") or []) if o.get("perSecond")]
        if outs and m.get("kind") in ("item", "unit", "generator"):
            bits.append("、".join("%s %s/s" % (o["name"], fmt(o["perSecond"])) for o in outs[:2]))
        c.row(m.get("icon"), m.get("name") or "?", "×%d" % int(m.get("count") or 0),
              " · ".join(bits) or None)
    if plist:
        c.section("抽水（钻井 / 泵）")
        for m in plist:
            bits = []
            if m.get("powerTotal"):
                bits.append("电 %s/s" % fmt(m["powerTotal"]))
            if m.get("rateEach"):
                bits.append("单台 %s/s" % fmt(m["rateEach"]))
            c.row(m.get("icon"), m.get("name") or "?", "×%d" % int(m.get("count") or 0),
                  " · ".join(bits) or None)


def _import_section(c, res):
    """外部入料：不给来源时默认蓝带（12.015/s 一条），条数 = ceil(需求/单条)。"""
    demand = [d for d in (res.get("demand") or []) if (d.get("perSecond") or 0) > 0]
    if not demand:
        return
    srcs = {}
    for s in (res.get("sources") or []):
        srcs[s.get("item")] = s
    belts = [s for s in srcs.values() if s.get("type") == "import" and s.get("count")]
    is_blue = any(s.get("via") == "belt-blue" for s in belts)
    total = sum(int(s.get("count") or 0) for s in belts)
    if belts:
        head = "外部入料（%s）：%d 条带子" % ("默认蓝带" if is_blue else "指定带子", total)
    else:
        head = "外部入料"
    c.section(head)
    for d in demand:
        s = srcs.get(d["name"]) or {}
        sub = None
        if s.get("type") == "drill":
            sub = "%s ×%s%s" % (s.get("drill"), s.get("count"), "（加水）" if s.get("boosted") else "（不加水）")
        elif s.get("type") == "multi":
            sub = "%s ×%s" % (s.get("block"), s.get("count"))
            bp = "、".join("%s %s/s" % (b["name"], fmt(b["perSecond"]))
                          for b in (s.get("byproducts") or [])[:2])
            if bp:
                sub += " · 副产 " + bp
        elif s.get("viaLabel") or s.get("via"):
            label = s.get("viaLabel") or s.get("via")
            if s.get("count") is None:
                sub = "%s · 不限速" % label
            else:
                sub = "%s ×%s 条（%s/s）" % (label, int(s["count"]), fmt(s.get("perSecondTotal")))
        c.row(d.get("icon"), d["name"], "%s/s" % fmt(d.get("perSecond")), sub)


GEN_LABEL = {
    "combustion-generator": "燃烧发电机", "steam-generator": "蒸汽发电机",
    "differential-generator": "差速发电机",
}

PUMP_LABEL = {
    "mechanical-pump": "小泵", "rotary-pump": "中泵", "impulse-pump": "大泵",
    "reinforced-pump": "强化泵", "water-extractor": "地下水", "oil-extractor": "钻井",
}


def _equiv_text(eq: dict | None) -> str | None:
    """泵换算：按"几台小泵 + 几台中泵 + 几台大泵"的加和计（用户口径）。

    eq 就是 core.pumpMix 的结果：{need, pumps:[{pump,count,perSecondEach}], total, extra}。"""
    if not isinstance(eq, dict):
        return None
    parts = eq.get("pumps") or []
    if not parts:
        return None
    text = " + ".join("%s %s 台" % (PUMP_LABEL.get(p["pump"], p["pump"]), p["count"]) for p in parts)
    total, extra = eq.get("total"), eq.get("extra") or 0
    if total:
        text += "（合计 %s/s" % fmt(total)
        if extra > 1e-6:
            text += "，富余 %s/s" % fmt(extra)
        text += "）"
    return text


def _power_mix_text(mix: dict | None) -> str | None:
    """外部电力换算成"几台发电厂"（与泵同一套口径：先富余小、再台数少）。"""
    if not isinstance(mix, dict):
        return None
    gens = mix.get("gens") or []
    if not gens:
        return None
    text = " + ".join("%s %s 台" % (GEN_LABEL.get(g["block"], g["block"]), g["count"]) for g in gens)
    total, extra = mix.get("total"), mix.get("extra") or 0
    text += "（合计 %s/s" % fmt(total)
    if extra > 1e-6:
        text += "，富余 %s/s" % fmt(extra)
    return text + "）"


def _power_mix_row(c, res):
    """外部电力（自己没发电、从外面接进来的电）补一行"换算成几台发电厂"。"""
    mix = res.get("powerMix")
    text = _power_mix_text(mix)
    if not text:
        return
    c.note("外部电力：电力 %s/s ≈ %s" % (fmt((mix or {}).get("need")), text), DIM)


def _liquid_icon(color: str | None, px: int = 16) -> str | None:
    """兜底色点：按 knowledge 的 colorHex 画圆点（原版液体贴图优先，见 liquid_icons）。"""
    if not color or not color.startswith("#") or len(color) < 7:
        return None
    try:
        rgb = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
    except ValueError:
        return None
    im = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse([1, 1, px - 2, px - 2], fill=rgb + (255,))
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _liquid_section(c, res):
    """液体段：自产之后还要从外面进的（liquidNet）才算需求；自产的写明是钻井还是转化方块。"""
    all_liq = res.get("liquids") or []
    auto = res.get("liquidFrom") or {}
    net = res.get("liquidNet")
    need = list(net) if isinstance(net, list) else all_liq
    if not need and not auto:
        return
    colors = (res.get("liquidColors") or {}) if isinstance(res.get("liquidColors"), dict) else {}
    icons = (res.get("liquidIcons") or {}) if isinstance(res.get("liquidIcons"), dict) else {}
    equiv = (res.get("pumpMix") or {}) if isinstance(res.get("pumpMix"), dict) else {}
    pumps = {s["liquid"]: s for s in (res.get("liquidSources") or [])}
    c.section("边界液体" + ("（净）" if auto else ""))
    for l in need:
        name = l.get("name")
        src = pumps.get(name)
        icon = l.get("icon") or icons.get(name) or _liquid_icon(colors.get(name) or l.get("color"))
        sub = ("自产 %s ×%s" % (auto[name]["block"], auto[name]["count"]) if name in auto else
               ("%s ×%s（电 %s/s）" % (src["pump"], src["count"], fmt(src.get("power")))
                if src else "外部运入"))
        c.row(icon, name, "%s/s" % fmt(l.get("perSecond")), sub, LIQUID)
        eq = _equiv_text(equiv.get(name))
        if eq:
            c.note("泵换算：%s %s/s ≈ %s" % (name, fmt(l.get("perSecond")), eq))
    for name, a in auto.items():
        if any(l.get("name") == name for l in need):
            continue
        icon = a.get("icon") or icons.get(name) or _liquid_icon(colors.get(name))
        kind = "转化方块" if a.get("type") == "make" else "钻井"
        c.row(icon, name, "%s/s" % fmt((a.get("count") or 0) * (a.get("perSecondEach") or 0)),
              "自产 %s ×%s（%s）" % (a.get("block"), a.get("count"), kind), LIQUID)
        eq = _equiv_text(equiv.get(name))
        if eq:
            need = (a.get("count") or 0) * (a.get("perSecondEach") or 0)
            c.note("泵换算：%s %s/s ≈ %s" % (name, fmt(need), eq))


def _power_section(c, res):
    sup = res.get("supply")
    if not sup:
        return
    fuel = sup.get("fuel") or {}
    c.section("供电")
    c.row(sup.get("icon"), "%s ×%d" % (sup["name"], sup["count"]),
          "净 %s/s" % fmt(sup.get("netTotal")),
          ("烧 %s %s/s" % (fuel.get("name"), fmt(fuel.get("perSecond")))) if fuel.get("name") else None,
          GREEN)
    icons = (res.get("liquidIcons") or {}) if isinstance(res.get("liquidIcons"), dict) else {}
    colors = (res.get("liquidColors") or {}) if isinstance(res.get("liquidColors"), dict) else {}
    for l in sup.get("liquids") or []:
        c.row(l.get("icon") or icons.get(l["name"]) or _liquid_icon(colors.get(l["name"])),
              "%s（液体）" % l["name"], "%s/s" % fmt(l.get("perSecond")), None, LIQUID)


def _warn_section(c, res):
    warns = res.get("warnings") or []
    if not warns:
        return
    c.section("提示")
    for w in warns:
        c.note("· " + w)


def build_card(res: dict) -> Card:
    """一张卡片：**工厂配比结果**是正文，外部入料（默认蓝带）/液体/供电是附注。"""
    c = Card()
    snap = res.get("snapshot") or ""
    mode = res.get("mode")

    if mode == "chain":
        ch = res["chain"]
        goal = ("%s 台 T%s ≈ %s/s" % (ch["topCount"], ch.get("topTier"), fmt(ch.get("rate")))
                if ch.get("topCount") else "%s 台/s" % fmt(ch.get("rate")))
        top_icon = None
        for r in ch["rows"]:
            if r.get("count"):
                top_icon = r.get("blockIcon") or r.get("icon")
                break
        built = [r for r in ch["rows"] if r.get("count")]
        shown_top = built[-1]["unit"] if built else ch["top"]
        head = ("兵厂大循环：%s → %s" % (ch["start"], shown_top) if len(built) > 1
                else "兵厂：%s ×%s" % (ch["start"], built[0]["count"] if built else 0))
        c.title(head, top_icon,
                "目标 %s · 电力 %s/s · %s" % (goal, fmt(res.get("power") or ch.get("power")), snap))
        c.section("各级兵厂（配比结果 · 台数按各自建造时间）")
        for r in ch["rows"]:
            if not r.get("count"):
                c.note("  T%s  %s ×0（不建）" % (r["tier"], r["block"]), DIM)
                continue
            right = "%s %s/s" % (r["unit"], fmt(r["actual"]))
            if r.get("bottleneck"):
                right += " · 瓶颈"
            sub = "电 %s/s" % fmt(r.get("power"))
            if r.get("feedsNext"):
                sub += " · 1 台带 %s 台上级" % fmt(r["feedsNext"])
            c.row(r.get("blockIcon") or r.get("icon"),
                  "T%s  %s ×%d" % (r["tier"], r["block"], r["count"]), right, sub, BLUE)
        if ch.get("bottleneck"):
            c.note("整链实际达成 %s/s（受最慢的 T%s %s 限制）"
                   % (fmt(ch.get("achieved")), ch.get("bottleneckTier"), ch["bottleneck"]), DIM)
        _import_section(c, res)
        _liquid_section(c, res)
        _power_section(c, res)
        _warn_section(c, res)
        return c

    if mode == "mixed":
        targets = res.get("targets") or []
        head = "混合厂：" + " + ".join("%s ×%s" % (t.get("block"), fmt(t.get("count"))) for t in targets[:3])
        if len(targets) > 3:
            head += " 等 %d 项" % len(targets)
        icon = None
        for m in res.get("machines") or []:
            if m.get("name") == (targets[0] or {}).get("block"):
                icon = m.get("icon")
                break
        c.title(head, icon, "多个目标合并算上游（共享产物只建一份）· %s" % snap)
        c.section("目标")
        blk_icon = {m.get("name"): m.get("icon") for m in (res.get("machines") or [])}
        for t in targets:
            outs = [p for p in (t.get("products") or []) if p.get("rate")]
            pos = "、".join("%s %s/s" % (p["name"], fmt(p["rate"])) for p in outs[:2]) or "—"
            c.row(blk_icon.get(t.get("block")), t.get("block") or "?", "×%s" % fmt(t.get("count")), "产出 " + pos,
                  ORANGE if t.get("kind") == "generator" else None)
        _machine_section(c, res)
        _power_mix_row(c, res)
        sh = [s for s in (res.get("shared") or []) if (s.get("saved") or 0) > 0]
        if sh:
            c.note("共享：「%s」，分别建要 ×%s（混合省 %s 台）"
                   % ("、".join(s["item"] for s in sh[:2]),
                      "/".join(str(s.get("separateCount")) for s in sh[:2]),
                      "/".join(str(s.get("saved")) for s in sh[:2])), GREEN)
        cmp_ = res.get("compare") or {}
        if cmp_:
            c.note("对比分别建：机器 %s → %s（省 %s），占地 %s → %s 格（省 %s）"
                   % (fmt(cmp_.get("machinesSeparate")), fmt(cmp_.get("machinesMixed")),
                      fmt(cmp_.get("savedMachines")), fmt(cmp_.get("tilesSeparate")),
                      fmt(cmp_.get("tilesMixed")), fmt(cmp_.get("savedTiles"))), DIM)
        if res.get("powerOut"):
            c.note("厂内发电 %s/s，净电力 %s/s"
                   % (fmt(res.get("powerOut")), fmt(res.get("netPower"))), DIM)
        _import_section(c, res)
        _liquid_section(c, res)
        _power_section(c, res)
        _warn_section(c, res)
        return c

    if mode == "building":
        head = "%s ×%s" % (res.get("target"), fmt(res.get("requested")))
        sub = "建筑模式（满效）· %s" % snap
    else:
        head = "%s %s/s" % (res.get("target"), fmt(res.get("requested")))
        sub = "物品模式 · %s" % snap

    icon = None
    for m in res.get("machines") or []:
        if m.get("name") == res.get("target"):
            icon = m.get("icon")
            break
    if not icon:
        machines = res.get("machines") or []
        icon = machines[0].get("icon") if machines else None
    c.title(head, icon, sub)

    _machine_section(c, res)
    _power_mix_row(c, res)

    prods = [p for p in (res.get("products") or []) if p.get("rate")]
    if prods:
        parts = []
        for p in prods[:3]:
            kind = "单位" if p.get("type") == "unit" else "物品"
            parts.append("%s %s/s（%s）" % (p["name"], fmt(p.get("rate")), kind))
        c.note("产出：" + "、".join(parts), GREEN)

    _import_section(c, res)
    _liquid_section(c, res)
    _power_section(c, res)
    _warn_section(c, res)
    return c


def render_png(res: dict, out: str, width: int = 700, scale: float = 1.0) -> str:
    """把结果 dict 直接画成 PNG，返回绝对路径（bot 侧调这个函数就行）。"""
    card = build_card(res)
    card.width = int(width)
    img = card.render()
    if scale and scale != 1.0:
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    path = os.path.abspath(out)
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    img.convert("RGB").save(path, "PNG")
    return path


def card_from_json(path: str, out: str, width: int = 700, scale: float = 1.0) -> str:
    """喂一份 cli.cjs --format json 的结果文件，出一张卡。"""
    with io.open(path, encoding="utf-8") as f:
        res = json.load(f)
    return render_png(res, out, width=width, scale=scale)


def parse_cli(argv):
    """手写解析：本文件自己的参数抽出来，其余原样交给 cli.cjs。"""
    known = {"--out": "out", "--json": "json", "--from-json": "json", "--data": "data", "--node": "node",
             "--width": "width", "--scale": "scale"}
    opts = {"out": None, "json": None, "data": None, "node": "node", "width": 700, "scale": 1.0}
    rest = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in known:
            key = known[a]
            i += 1
            if i >= len(argv):
                raise SystemExit("%s 缺少取值" % a)
            val = argv[i]
            if key in ("width",):
                opts[key] = int(val)
            elif key == "scale":
                opts[key] = float(val)
            else:
                opts[key] = val
        elif a in ("-h", "--help"):
            print(__doc__)
            raise SystemExit(0)
        else:
            rest.append(a)
        i += 1
    if not opts["out"]:
        raise SystemExit("要给 --out <png 路径>\n" + (__doc__ or ""))
    opts["rest"] = rest
    return opts


class _Args:
    def __init__(self, d):
        for k, v in d.items():
            setattr(self, k, v)


def main() -> None:
    args = _Args(parse_cli(sys.argv[1:]))
    res = load_result(args)
    card = build_card(res)
    card.width = args.width
    img = card.render()
    if args.scale and args.scale != 1.0:
        img = img.resize((int(img.width * args.scale), int(img.height * args.scale)), Image.LANCZOS)
    out = os.path.abspath(args.out)
    img.convert("RGB").save(out, "PNG")
    print(out)


if __name__ == "__main__":
    main()
