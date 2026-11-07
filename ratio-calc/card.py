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


def build_card(res: dict) -> Card:
    c = Card()
    snap = res.get("snapshot") or ""
    if res.get("mode") == "chain":
        ch = res["chain"]
        goal = ("%s 台 T%s ≈ %s/s" % (ch["topCount"], ch.get("topTier"), fmt(ch.get("rate")))
                if ch.get("topCount") else "%s 台/s" % fmt(ch.get("rate")))
        c.title("兵厂大循环：%s → %s" % (ch["start"], ch["top"]),
                None, "目标 %s · %d 级 · 电力 %s/s · %s" % (goal, ch.get("tiers", 0),
                                                            fmt(ch.get("power")), snap))
        c.section("各级兵厂（台数按各自建造时间，不必 1:1）")
        for r in ch["rows"]:
            mat = "、".join("%s %s/s" % (i["name"], fmt(i["perSecond"])) for i in r.get("items") or [])
            right = "%s %s/s" % (r["unit"], fmt(r["actual"]))
            if r.get("feedsNext"):
                right += " · 1 台带 %s 台上级" % fmt(r["feedsNext"])
            if r.get("bottleneck"):
                right += " · 瓶颈"
            c.row(r.get("icon") or r.get("blockIcon"), "T%s  %s ×%d" % (r["tier"], r["block"], r["count"]),
                  right, "电 %s/s" % fmt(r.get("power")), BLUE)
            if mat:
                c.note("      材料：%s" % mat, DIM)
        if ch.get("bottleneck"):
            c.note("整链实际达成 %s/s（受最慢的 T%s %s 限制）"
                   % (fmt(ch.get("achieved")), ch.get("bottleneckTier"), ch["bottleneck"]), DIM)
        c.section("合计材料（/s · /min）")
        for k, v in sorted((ch.get("materials") or {}).items()):
            c.row(None, k, "%s/s · %s/min" % (fmt(v), fmt(v * 60)))
        return c

    if res.get("mode") == "building":
        head = "%s ×%s" % (res.get("target"), fmt(res.get("requested")))
        sub = "建筑模式（满效）· %s" % snap
    else:
        head = "%s %s/s" % (res.get("target"), fmt(res.get("requested")))
        sub = "物品模式 · %s" % snap
    c.title("配比：" + head, (res.get("machines") or [{}])[0].get("icon") if False else None, sub)

    prods = res.get("products") or []
    if prods:
        c.section("产出")
        for p in prods:
            kind = "单位" if p.get("type") == "unit" else "物品"
            c.row(p.get("icon"), "%s（%s）" % (p["name"], kind), "%s/s" % fmt(p.get("rate")), None, GREEN)

    c.section("建筑清单（共 %d 台 · 电力 %s/s）"
              % (sum(m["count"] for m in res.get("machines") or []), fmt(res.get("power"))))
    for m in res.get("machines") or []:
        right = "×%d" % m["count"]
        sub = None
        if m.get("powerTotal"):
            sub = "电 %s/s" % fmt(m["powerTotal"])
        outs = m.get("outItems") or []
        if outs and m.get("kind") in ("item", "unit"):
            sub = (sub + " · ") if sub else ""
            sub += "、".join("%s %s/s" % (o["name"], fmt(o["perSecond"])) for o in outs[:2])
        c.row(m.get("icon"), m["name"], right, sub)

    demand = res.get("demand") or []
    liquids = res.get("liquids") or []
    if demand:
        c.section("边界输入（外部运入）")
        for d in demand:
            c.row(d.get("icon"), d["name"], "%s/s" % fmt(d["perSecond"]))
    if liquids:
        pumps = {s["liquid"]: s for s in (res.get("liquidSources") or [])}
        c.section("液体需求")
        for l in liquids:
            src = pumps.get(l["name"])
            sub = None
            if src:
                sub = "%s ×%d（电 %s/s）" % (src["pump"], src["count"], fmt(src.get("power")))
            else:
                sub = "外部运入"
            c.row(None, l["name"], "%s/s" % fmt(l.get("perSecond")), sub, LIQUID)

    srcs = res.get("sources") or []
    if srcs:
        c.section("外部来源")
        for s in srcs:
            if s.get("type") == "drill":
                c.row(s.get("icon"), "%s ← %s ×%d" % (s["item"], s["drill"], s["count"]),
                      "%s/s" % fmt(s.get("perSecondTotal")),
                      "%s 格矿%s" % (s.get("tiles"), "·加水" if s.get("boosted") else "·不加水"))
            elif s.get("type") == "multi":
                bp = "、".join("%s %s/s" % (b["name"], fmt(b["perSecond"])) for b in (s.get("byproducts") or [])[:3])
                c.row(s.get("icon"), "%s ← %s ×%d" % (s["item"], s["block"], s["count"]),
                      "电 %s/s" % fmt(s.get("power")), bp)
            else:
                c.row(None, "%s ← 外部运入" % s["item"], "%s/s" % fmt(s.get("demand")))

    sup = res.get("supply")
    if sup:
        c.section("供电")
        fuel = sup.get("fuel") or {}
        c.row(sup.get("icon"), "%s ×%d" % (sup["name"], sup["count"]),
              "净 %s/s" % fmt(sup.get("netTotal")),
              ("烧 %s %s/s" % (fuel.get("name"), fmt(fuel.get("perSecond")))) if fuel.get("name") else None,
              GREEN)
        for l in sup.get("liquids") or []:
            c.row(None, "%s（液体）" % l["name"], "%s/s" % fmt(l.get("perSecond")), None, LIQUID)

    warns = res.get("warnings") or []
    if warns:
        c.section("提示")
        for w in warns:
            c.note("· " + w)
    return c


def parse_cli(argv):
    """手写解析：本文件自己的参数抽出来，其余原样交给 cli.cjs。"""
    known = {"--out": "out", "--json": "json", "--data": "data", "--node": "node",
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
