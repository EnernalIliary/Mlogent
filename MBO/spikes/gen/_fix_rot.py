import pathlib

p = pathlib.Path(__file__).resolve().parents[2] / "mbo" / "layout.py"
s = p.read_text(encoding="utf-8")
n = s.count('_put(lay, plan, "conveyor", gate_x, ex, ROT["S"])')
s = s.replace('_put(lay, plan, "conveyor", gate_x, ex, ROT["S"])',
              '_put(lay, plan, "conveyor", gate_x, ex, ROT["N"])')
p.write_text(s, encoding="utf-8")

q = pathlib.Path(__file__).resolve().parent / "_check_designs.py"
t = q.read_text(encoding="utf-8")
t = t.replace('("conveyor", 3, 3, 1, None)', '("conveyor", 3, 3, 3, None)')
q.write_text(t, encoding="utf-8")
print("rot fixed:", n)
