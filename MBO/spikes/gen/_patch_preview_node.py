"""preview：路由器/交叉器/分拣器用独立字符 n（不再画成带子箭头）。"""
import pathlib

p = pathlib.Path(__file__).resolve().parents[2] / "mbo" / "preview.py"
s = p.read_text(encoding="utf-8")

OLD = '''        c = ch.get(fam, "?")'''
NEW = '''        c = ch.get(fam, "?")
        if t.block in ("router", "junction", "sorter", "inverted-sorter"):
            c = "n"          # 这些是“节点”而不是带子，别画成箭头'''
assert OLD in s
s = s.replace(OLD, NEW, 1)
p.write_text(s, encoding="utf-8")
print("preview patched")
