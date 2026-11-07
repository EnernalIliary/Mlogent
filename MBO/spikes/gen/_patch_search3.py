"""补丁 3：越界/重叠时 make 返回 None（搜索空间里合法地存在放不下的组合）。"""
import pathlib

p = pathlib.Path(__file__).resolve().parent / "search_ported.py"
s = p.read_text(encoding="utf-8")

s = s.replace('''def make(blocks):
    lay = Layout(W, H, SIZES)
    for name, x, y, rot, item in blocks:
        if name == "item-source":
            lay.add(name, x, y, rot, item_cfg(GD, item or "coal"))
        else:
            lay.add(name, x, y, rot)
    return lay''', '''def make(blocks):
    lay = Layout(W, H, SIZES)
    try:
        for name, x, y, rot, item in blocks:
            if name == "item-source":
                lay.add(name, x, y, rot, item_cfg(GD, item or "coal"))
            else:
                lay.add(name, x, y, rot)
    except ValueError:
        return None
    return lay''')

s = s.replace('''    if not no_overlap(blocks):
        return None
    lay = make(blocks)''', '''    if not no_overlap(blocks):
        return None
    lay = make(blocks)
    if lay is None:
        return None''')

s = s.replace('''    layb = make(body)
    bb = bounds(layb)''', '''    layb = make(body)
    if layb is None:
        return []
    bb = bounds(layb)''')

s = s.replace('''        for _k in range(rnd.randint(0, 2)):
            c = rnd.choice(cand)
            body.append((rnd.choice(("conveyor", "underflow-gate", "router")),
                         c[0], c[1], rnd.choice((0, 1, 2, 3)), None))''',
              '''        for _k in range(rnd.randint(0, 2)):
            c = rnd.choice(cand)
            trial = body + [(rnd.choice(("conveyor", "underflow-gate", "router")),
                             c[0], c[1], rnd.choice((0, 1, 2, 3)), None)]
            if no_overlap(trial) and make(trial) is not None:
                body = trial''')

s = s.replace('''        bb = bounds(make(body)) if no_overlap(body) else bb''',
              '''        lay_body = make(body)
        if lay_body is None:
            continue
        bb = bounds(lay_body)''')
p.write_text(s, encoding="utf-8")
print("patched3")
