"""给 tests/test_mbo.py 追加 TestLogistics / TestPorted。"""
import pathlib

p = pathlib.Path(__file__).resolve().parents[2] / "tests" / "test_mbo.py"
s = p.read_text(encoding="utf-8")
assert "TestPorted" not in s

NEW = '''

class TestLogistics(unittest.TestCase):
    """docs/19：把“速率由物流元件决定”做成可计算的容量网络。"""

    @classmethod
    def setUpClass(cls):
        cls.gd = GameData("v160.7")
        cls.plan = expand(cls.gd, "graphite", 1.0, {"coal"})

    def _lay(self, ports="both"):
        from mbo.layout import build_ported
        return build_ported(self.gd, self.plan, ports=ports)

    def test_estimate_matches_plan(self):
        from mbo import logistics
        for ports in ("both", "gate", "one"):
            est = logistics.estimate(self._lay(ports), self.gd, self.plan)
            self.assertEqual(est["bottleneck"], "machine", ports)
            self.assertAlmostEqual(est["rate"], 1.3333, places=3)
            self.assertAlmostEqual(est["in_flow"]["coal"], 2.6667, places=3)
            self.assertAlmostEqual(est["out_flow"], 1.3333, places=3)

    def test_ports_outside_true_for_ported(self):
        from mbo import logistics
        for ports in ("both", "gate", "one"):
            ok, msg = logistics.ports_outside(self._lay(ports), self.gd)
            self.assertTrue(ok, "%s: %s" % (ports, msg))

    def test_ports_outside_false_for_direct(self):
        from mbo import logistics
        lay = build_for(self.gd, self.plan, layout="direct")
        ok, msg = logistics.ports_outside(lay, self.gd)
        self.assertFalse(ok)
        self.assertIn("工厂矩形", msg)

    def test_dead_belt_gives_zero_outflow(self):
        """带子朝空位 = 物流断链，模型必须看到 0 而不是按机器台数算。"""
        from mbo import logistics
        lay = Layout(8, 8, {b.name: b.size for b in self.gd.blocks.values()})
        lay.add("graphite-press", 1, 1, 0)
        lay.add("item-void", 6, 6, 0)
        lay.add("conveyor", 3, 3, 0)   # 朝东，前方 (4,3) 是空的
        self.assertEqual(logistics.flow(lay, self.gd, "graphite", "out"), 0.0)


class TestPorted(unittest.TestCase):
    """docs/19：端口必须落在工厂外接矩形之外；三个变体的格数/端口数是 Pareto 前沿。"""

    @classmethod
    def setUpClass(cls):
        cls.gd = GameData("v160.7")
        cls.plan = expand(cls.gd, "graphite", 1.0, {"coal"})

    @staticmethod
    def _counts(lay, gd):
        from mbo import logistics
        port_cells = sum(len(lay.cells(t.block, t.x, t.y)) for t in lay.tiles
                         if t.block in logistics.PORTS)
        ports = sum(1 for t in lay.tiles if t.block in logistics.PORTS)
        return lay.stats()["tiles"] - port_cells, ports

    def test_ported_tile_and_port_counts(self):
        from mbo.layout import build_ported
        want = {"both": (8, 4), "gate": (9, 3), "one": (12, 2)}
        for ports, (tiles, nports) in want.items():
            lay = build_ported(self.gd, self.plan, ports=ports)
            self.assertEqual(self._counts(lay, self.gd), (tiles, nports), ports)

    def test_ported_static_ok(self):
        from mbo.layout import build_ported
        for ports in ("both", "gate", "one"):
            lay = build_ported(self.gd, self.plan, ports=ports)
            res = static_check(lay, self.gd, self.plan, strict_ports=True)
            self.assertTrue(res["ok"], "%s: %s" % (ports, res["errors"]))
            self.assertTrue(res["info"]["ports_outside"])

    def test_strict_ports_flags_direct(self):
        lay = build_for(self.gd, self.plan, layout="direct")
        res = static_check(lay, self.gd, self.plan, strict_ports=True)
        self.assertFalse(res["ok"])
        self.assertTrue(any("端口位置违规" in e for e in res["errors"]))
        res2 = static_check(lay, self.gd, self.plan)
        self.assertTrue(res2["ok"])
        self.assertTrue(any("端口落在工厂矩形内" in w for w in res2["warnings"]))

    def test_ported_rejects_bad_ports(self):
        from mbo.layout import build_ported
        with self.assertRaises(ValueError):
            build_ported(self.gd, self.plan, ports="triple")

    def test_ported_rejects_multi_input(self):
        plan = expand(self.gd, "silicon", 3.0, {"coal", "sand"})
        with self.assertRaises(ValueError):
            build_for(self.gd, plan, layout="ported")

    def test_ported_body_roundtrip(self):
        from mbo.layout import build_ported
        lay = build_ported(self.gd, self.plan, ports="gate")
        back = codec.read_bytes(lay.to_bytes())
        self.assertEqual(back.w, lay.w)
        self.assertEqual(len(back.tiles), len(lay.tiles))


'''

marker = '\n\nif __name__ == "__main__":'
assert marker in s
s = s.replace(marker, NEW + '\nif __name__ == "__main__":', 1)
p.write_text(s, encoding="utf-8")
print("tests appended")
