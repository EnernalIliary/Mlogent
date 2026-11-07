"""补丁：重写 search_ported.py 的 sink_options（上一版逻辑绕，重写为直白枚举）。"""
import pathlib

p = pathlib.Path(__file__).resolve().parent / "search_ported.py"
s = p.read_text(encoding="utf-8")

start = s.index("def sink_options")
end = s.index("def _free_cells")
new = '''def sink_options(presses, body):
    """出口方案：1~2 个 item-void；不贴机器的压机用 1 条带子把货送到 void。"""
    layb = make(body)
    bb = bounds(layb)
    cand = ring(bb, body)
    pcells = [cells_of("graphite-press", *p) for p in presses]
    used = set()
    for name, x, y, rot, item in body:
        used |= cells_of(name, x, y)
    opts = []

    # A) 每台压机各贴一个外部 void
    per = [[(v, []) for v in cand if adjacent(v, c)] for c in pcells]
    if all(per):
        for combo in itertools.product(*per):
            vs = [c[0] for c in combo]
            if len(set(vs)) == 2:
                opts.append([("item-void", v[0], v[1], 0, None) for v in vs])

    # B) 单个 void：每台压机要么直贴，要么用 1 条带子（带子格贴机器，front 指 void）
    for v in cand:
        per = []
        for c in pcells:
            if adjacent(v, c):
                per.append((v, []))
                continue
            belt = None
            for b in cand:
                if b == v or b in used:
                    continue
                if not adjacent(b, c):
                    continue
                rot = _rot_to(b, v)
                if rot is None:
                    continue
                belt = [(b[0], b[1], rot)]
                break
            per.append((v, belt) if belt else None)
        if not all(per):
            continue
        belts = set()
        for _, bl in per:
            belts |= {(b[0], b[1]) for b in bl}
        blk = [("item-void", v[0], v[1], 0, None)]
        blk += [("conveyor", bx, by, rot, None) for (bx, by, rot) in
                sorted({b for _, bl in per for b in bl})]
        if len(belts) == sum(len(bl) for _, bl in per):
            opts.append(blk)
    return opts


'''

p.write_text(s[:start] + new + s[end:], encoding="utf-8")
print("patched")
