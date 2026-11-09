#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""卡片自测：不依赖肉眼看图，直接查结构 / 文案 / 排版宽度。

  python -X utf8 ratio-calc/test_card.py

守的点：
  1. 卡片正文第一块是「工厂配比」（用户要求：配比结果是主要内容）
  2. 「外部入料」在配比之后，且默认走蓝带、带条数
  3. 兵厂链卡片：0 台的层级写「×0（不建）」，不吹数
  4. 每行「图标 + 名字 + 副标 + 右对齐值」不横向重叠
  5. 渲染出来的 PNG 高度 = Card.height()，非空
"""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import card as C  # noqa: E402

NODE = os.environ.get("RATIO_NODE") or "node"
CLI = os.path.join(HERE, "cli.cjs")

pass_n = 0
fail_n = 0


def ok(name, fn):
    global pass_n, fail_n
    try:
        fn()
        pass_n += 1
        print("  ✓ " + name)
    except AssertionError as e:
        fail_n += 1
        print("  × " + name + " — " + str(e))


def run_cli(args):
    out = subprocess.check_output([NODE, CLI, "--format", "json", "--icons"] + args,
                                  cwd=HERE)
    return json.loads(out.decode("utf-8"))


def texts(res):
    """把卡片压成 (kind, 文本) 列表，便于断顺序。"""
    seq = []
    for b in C.build_card(res).blocks:
        if b[0] == "title":
            seq.append(("title", b[1] + " | " + (b[3] or "")))
        elif b[0] == "section":
            seq.append(("section", b[1]))
        elif b[0] == "row":
            seq.append(("row", "%s %s %s" % (b[2], b[4] or "", b[3])))
        elif b[0] == "note":
            seq.append(("note", b[1]))
    return seq


def flat(res):
    return "\n".join(t for _, t in texts(res))


def idx_of(res, needle):
    seq = texts(res)
    for i, (_, t) in enumerate(seq):
        if needle in t:
            return i
    return -1


def check_width(res, width=700):
    """模拟 Card.render 的排版，检查「名字 + 副标 + 右值」不撞车。"""
    from PIL import ImageDraw, Image
    d = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    for b in C.build_card(res).blocks:
        if b[0] != "row":
            continue
        _, icon, name, right, sub, _accent = b
        rw = d.textlength(right, font=C.font(15, True))
        nw = d.textlength(name, font=C.font(15))
        left = C.PAD + 36 + nw
        if sub:
            sw = d.textlength(sub, font=C.font(12))
            sub_x = width - C.PAD - rw - sw - 14
        else:
            sub_x = width - C.PAD - rw
        assert sub_x > left, "行重叠：%s（名字到 %d，副标起点 %d）" % (name, left, sub_x)


print("卡片结构自测")


def case_building():
    r = run_cli(["--block", "graphite-press", "--count", "2"])
    t = flat(r)
    assert "graphite-press" in texts(r)[0][1], texts(r)[0]
    i_mix = idx_of(r, "工厂配比")
    i_src = idx_of(r, "外部入料")
    assert i_mix >= 0, t
    assert i_mix < i_src, "工厂配比应在外部入料之前：%s" % t
    sec = [x for k, x in texts(r) if k == "section"]
    assert sec[0].startswith("工厂配比"), sec
    assert "默认蓝带" in t and "条" in t, t
    assert "蓝带" in t and "12.015" in t, t
    check_width(r)


def case_item():
    r = run_cli(["--item", "silicon", "--rate", "5"])
    t = flat(r)
    assert idx_of(r, "工厂配比") < idx_of(r, "外部入料"), t
    assert "silicon-smelter" in t, t
    assert "120" in t, t          # 2 台硅炉的电力
    check_width(r)


def case_chain():
    r = run_cli(["--block", "tetrative-reconstructor", "--count", "5"])
    t = flat(r)
    assert "兵厂大循环" in texts(r)[0][1], texts(r)[0]
    assert "各级兵厂" in t, t
    assert idx_of(r, "各级兵厂") < idx_of(r, "外部入料"), t
    assert "reign" in t and "dagger" in t, t
    assert "9672" in t, t
    check_width(r)


def case_chain_partial():
    r = run_cli(["--block", "ground-factory", "--count", "2"])
    t = flat(r)
    assert "×0（不建）" in t, t
    assert "兵厂：dagger" in texts(r)[0][1], texts(r)[0]
    check_width(r)


def case_png():
    r = run_cli(["--item", "graphite", "--rate", "1"])
    c = C.build_card(r)
    img = c.render()
    assert img.width == 700, img.size
    assert img.height == c.height(), (img.size, c.height())
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "x.png")
        C.render_png(r, p)
        assert os.path.getsize(p) > 5000, os.path.getsize(p)


ok("建筑模式：配比在前、外部入料在后、默认蓝带带条数", case_building)
ok("物品模式：配比在前，电力写对", case_item)
ok("兵厂链：标题/各级/总额，配比在前", case_chain)
ok("兵厂链只建 T1：0 台层级写「×0（不建）」", case_chain_partial)
def case_generator():
    r = run_cli(["--block", "steam-generator", "--count", "2"])
    t = flat(r)
    assert "工厂配比" in t, t
    assert "电力 660/s" in t, t
    assert idx_of(r, "外部入料") > idx_of(r, "工厂配比"), texts(r)
    assert "供电" in t, t
    check_width(r)


def case_mixed():
    r = run_cli(["--mix", "silicon-arc-furnace:1,carbide-crucible:1"])
    assert r.get("mode") == "mixed", r.get("mode")
    t = flat(r)
    assert "混合厂" in texts(r)[0][1], texts(r)[0]
    assert "多个目标合并算上游" in texts(r)[0][1], texts(r)[0]
    assert "目标" in t, t
    assert idx_of(r, "目标") < idx_of(r, "工厂配比"), t
    assert "共享" in t and "11" in t, t        # 分别建 11 台石墨压机
    assert "对比分别建：机器 13 → 12" in t, t
    assert "graphite-press" in t, t
    check_width(r)


def case_mixed_generator():
    r = run_cli(["--mix", "silicon-smelter:2,combustion-generator:1"])
    t = flat(r)
    assert "厂内发电 60/s" in t, t
    assert "净电力 0/s" in t, t
    check_width(r)


def case_liquid_self():
    """煤炭不允许外部输入 + 液体自产：卡片要把煤炭处理线写出来、液体行用原版液体贴图 + 泵换算。"""
    r = run_cli(["--item", "coal", "--rate", "2", "--boundary", "none", "--liquids", "auto"])
    t = flat(r)
    assert "coal-centrifuge" in t, t
    assert "oil-extractor" in t, t
    assert "液体需求（净）" in t or "液体需求" in t, t
    assert "自产" in t, t
    rows = [b for b in C.build_card(r).blocks if b[0] == "row"]
    liq = [b for b in rows if b[2] in ("oil", "water")]
    assert liq, t
    for b in liq:
        assert b[1] and b[1].startswith("data:image/png;base64,"), b
    """液体行用的是原版 liquid-<名>.png 而不是色点"""
    icons = r.get("liquidIcons") or {}
    water = [b for b in liq if b[2] == "water"][0]
    assert icons.get("water") and water[1] == icons["water"], "水行图标不是原版贴图"
    """泵换算：加和口径（这台用到中泵 1 台就够 9/s 水）"""
    assert "泵换算" in t and "中泵 1 台" in t and "合计 12/s" in t, t[:400]
    """抽水机不算工厂机器：单列「抽水：」一行"""
    assert "工厂配比：2 台" in t and "抽水：" in t, t[:400]
    check_width(r)


def case_chain_icons():
    """兵厂链是另一条提前 return 的分支，曾经把入料图标全丢了。"""
    r = run_cli(["--chain", "dagger", "--chainrate", "0.05"])
    rows = [b for b in C.build_card(r).blocks if b[0] == "row"]
    assert rows, "chain 卡片没有任何 row"
    missing = [b[2] for b in rows if not b[1]]
    assert not missing, "这些行缺图标：%s" % missing


def case_mixed_icons():
    """混合厂的「目标」行以前传的是 None 图标。"""
    r = run_cli(["--mix", "silicon-arc-furnace:1,carbide-crucible:1"])
    rows = [b for b in C.build_card(r).blocks if b[0] == "row"]
    targets = [b for b in rows if b[2] in ("silicon-arc-furnace", "carbide-crucible")]
    assert len(targets) >= 2, [b[2] for b in rows]
    for b in targets:
        assert b[1], "目标行缺图标：" + str(b[2])


ok("液体自产：煤炭处理线写进卡片、液体行用原版贴图 + 泵换算", case_liquid_self)
ok("图标：兵厂链入料行不再缺图标", case_chain_icons)
ok("图标：混合厂目标行带方块图标", case_mixed_icons)
ok("发电设备：配比在前、发电量正确、带供电段", case_generator)
ok("混合厂：标题/目标表/共享省台数/对比分别建", case_mixed)
ok("混合厂：发电设备当目标时写厂内发电与净电力", case_mixed_generator)

print("\n通过 %d 项，失败 %d 项" % (pass_n, fail_n))
sys.exit(1 if fail_n else 0)
