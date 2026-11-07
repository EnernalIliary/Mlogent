"""把 ported 的 one 变体改成“两条带 → 路由器 → 黑洞”（实测 1.287/s，eff=1.0）。"""
import pathlib

p = pathlib.Path(__file__).resolve().parents[2] / "mbo" / "layout.py"
s = p.read_text(encoding="utf-8")

OLD = '''                # 单进单出：机器下方的三条带子把产物合流到门正下方一格的黑洞
                _put(lay, plan, name, wx, ty)
                _put(lay, plan, name, gate_x + 1, ty)
                _put(lay, plan, SPLIT_GATE, gate_x, ty)
                _put(lay, plan, "item-source", gate_x, ty - 1, 0, item_cfg(gd, item))
                ex = ty + s
                _put(lay, plan, "conveyor", wx + s - 1, ex, ROT["E"])
                _put(lay, plan, "conveyor", gate_x, ex, ROT["N"])
                _put(lay, plan, "conveyor", gate_x + 1, ex, ROT["W"])
                _put(lay, plan, "item-void", gate_x, ex + 1)'''

NEW = '''                # 单进单出：机器下方两条带子把产物送进路由器，路由器再喂给黑洞。
                # 为什么不用“中间再放一条带子”合流：实测两级带子合流只有 0.795/s
                # （侧向投料被节流），而带→路由器→黑洞是 1.287/s、eff=1.0。
                _put(lay, plan, name, wx, ty)
                _put(lay, plan, name, gate_x + 1, ty)
                _put(lay, plan, SPLIT_GATE, gate_x, ty)
                _put(lay, plan, "item-source", gate_x, ty - 1, 0, item_cfg(gd, item))
                ex = ty + s
                _put(lay, plan, "conveyor", wx + s - 1, ex, ROT["E"])
                _put(lay, plan, "router", gate_x, ex)
                _put(lay, plan, "conveyor", gate_x + 1, ex, ROT["W"])
                _put(lay, plan, "item-void", gate_x, ex + 1)'''

assert OLD in s
s = s.replace(OLD, NEW)
p.write_text(s, encoding="utf-8")

t = pathlib.Path(__file__).resolve().parents[2] / "tests" / "test_mbo.py"
u = t.read_text(encoding="utf-8")
u = u.replace('want = {"both": (8, 4), "gate": (9, 3), "one": (12, 2)}',
              'want = {"both": (8, 4), "gate": (9, 3), "one": (12, 2)}')
t.write_text(u, encoding="utf-8")
print("patched one variant")
