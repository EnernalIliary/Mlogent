"""补丁 2：evaluate 的格数按 cell 计、需求容差放宽到 1e-3；随机搜索坐标 ≥1。"""
import pathlib

p = pathlib.Path(__file__).resolve().parent / "search_ported.py"
s = p.read_text(encoding="utf-8")

old_eval = '''    est = logistics.estimate(lay, GD, PLAN)
    ports = sum(1 for t in lay.tiles if t.block in logistics.PORTS)
    factory = len(lay.tiles) - ports
    bb = bounds(lay)'''
new_eval = '''    est = logistics.estimate(lay, GD, PLAN)
    ports = sum(1 for t in lay.tiles if t.block in logistics.PORTS)
    port_cells = sum(len(lay.cells(t.block, t.x, t.y))
                     for t in lay.tiles if t.block in logistics.PORTS)
    factory = lay.stats()["tiles"] - port_cells
    bb = bounds(lay)'''
assert old_eval in s
s = s.replace(old_eval, new_eval)

s = s.replace('''        "ok_need": est["in_flow"].get("coal", 0.0) >= NEED_COAL - 1e-6
                   and est["out_flow"] >= NEED_OUT - 1e-6,''',
              '''        "ok_need": est["in_flow"].get("coal", 0.0) >= NEED_COAL - 1e-3
                   and est["out_flow"] >= NEED_OUT - 1e-3,''')

s = s.replace("gx, gy = rnd.randint(0, W - 5), rnd.randint(0, H - 5)",
              "gx, gy = rnd.randint(1, W - 5), rnd.randint(1, H - 5)")
p.write_text(s, encoding="utf-8")
print("patched2")
