import pathlib

p = pathlib.Path(__file__).resolve().parents[2] / "mbo" / "layout.py"
s = p.read_text(encoding="utf-8")
before = s.count("ex and gate_x")
s = s.replace("ex and gate_x", "gate_x")
p.write_text(s, encoding="utf-8")
print("replaced", before)
