"""preview：节点类方块不要被箭头覆盖。"""
import pathlib

p = pathlib.Path(__file__).resolve().parents[2] / "mbo" / "preview.py"
s = p.read_text(encoding="utf-8")
OLD = '''        if s == 1 and fam in ("conveyor", "duct", "crafter", "drill"):'''
NEW = '''        if s == 1 and fam in ("conveyor", "duct", "crafter", "drill") \\
                and t.block not in ("router", "junction", "sorter", "inverted-sorter"):'''
assert OLD in s
s = s.replace(OLD, NEW, 1)
p.write_text(s, encoding="utf-8")
print("patched arrow override")
