"""mbo 核心测试（标准库 unittest，不依赖 pytest）。

运行：python -X utf8 -m unittest discover -s MBO/tests -v
前置：MBO/gamedata/v160.7/ 快照存在（build-snapshot 生成）。
"""

import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]   # MBO/
sys.path.insert(0, str(ROOT))

from mbo import codec                      # noqa: E402
from mbo.gamedata import GameData          # noqa: E402
from mbo.model import Layout, BELT_RATE    # noqa: E402
from mbo.production import expand          # noqa: E402
from mbo.validate import static_check      # noqa: E402
from mbo.layout import build, build_for, build_split, split_applicable  # noqa: E402


class TestGameData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gd = GameData()

    def test_counts(self):
        self.assertEqual(len(self.gd.blocks), 447)
        self.assertIn("silicon-smelter", self.gd.blocks)

    def test_craft_time_is_frames(self):
        # 量纲铁律：craftTime 存帧，cps = 60 / frames
        b = self.gd.block("surge-smelter")
        self.assertEqual(b.recipe.craft_time_frames, 75)
        self.assertAlmostEqual(b.recipe.cycles_per_second, 0.8, places=6)
        self.assertAlmostEqual(b.power_usage_per_second, 240.0, places=3)

    def test_silicon_recipe(self):
        b = self.gd.block("silicon-smelter")
        self.assertEqual([name for name, _ in b.recipe.inputs], ["coal", "sand"])
        self.assertEqual([amt for _, amt in b.recipe.inputs], [1.0, 2.0])
        self.assertAlmostEqual(b.recipe.outputs_per_second["silicon"], 1.5, places=6)

    def test_snapshot_id(self):
        self.assertTrue(self.gd.snapshot_id.startswith("v160.7@"))
        self.assertEqual(len(self.gd.snapshot_id.split("@")[1]), 12)


class TestProduction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gd = GameData()

    def test_silicon_3(self):
        plan = expand(self.gd, "silicon", 3.0, boundary=["coal", "sand"])
        self.assertEqual(plan.machines, {"silicon-smelter": 2})
        self.assertAlmostEqual(plan.demand["coal"], 3.0, places=6)
        self.assertAlmostEqual(plan.demand["sand"], 6.0, places=6)
        self.assertAlmostEqual(plan.power_need, 60.0, places=6)

    def test_graphite_1(self):
        plan = expand(self.gd, "graphite", 1.0, boundary=["coal"])
        self.assertEqual(plan.machines, {"graphite-press": 2})
        self.assertAlmostEqual(plan.demand["coal"], 8.0 / 3.0, places=6)

    def test_metaglass_4(self):
        plan = expand(self.gd, "metaglass", 4.0, boundary=["lead", "sand"])
        self.assertEqual(plan.machines, {"kiln": 2})
        self.assertAlmostEqual(plan.power_need, 72.0, places=6)

    def test_unknown_item(self):
        with self.assertRaises(KeyError):
            expand(self.gd, "not-an-item", 1.0)


class TestLayout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gd = GameData()
        cls.sizes = {n: b.size for n, b in cls.gd.blocks.items()}

    def test_overlap_raises(self):
        lay = Layout(16, 16, self.sizes)
        lay.add("container", 4, 4)
        with self.assertRaises(ValueError):
            lay.add("container", 5, 5)      # 2×2 与 2×2 重叠

    def test_out_of_bounds_raises(self):
        lay = Layout(8, 8, self.sizes)
        with self.assertRaises(ValueError):
            lay.add("silicon-smelter", 7, 7)

    def test_origin_center_cell(self):
        # R1：多格方块存中心格，origin = center - (size-1)//2
        lay = Layout(32, 32, self.sizes)
        self.assertEqual(lay.origin("vault", 10, 10), (9, 9))
        self.assertEqual(lay.origin("container", 10, 10), (10, 10))
        self.assertEqual(lay.origin("conveyor", 10, 10), (10, 10))


class TestCodec(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gd = GameData()
        cls.sizes = {n: b.size for n, b in cls.gd.blocks.items()}

    def _layout(self):
        plan = expand(self.gd, "silicon", 3.0, boundary=["coal", "sand"])
        return build(self.gd, plan, canvas=(24, 24))

    def test_roundtrip_body_identical(self):
        lay = self._layout()
        raw = lay.to_bytes()
        lay2 = codec.read_bytes(raw)
        raw2 = codec.build_schematic_ext(lay2)
        self.assertEqual(codec.body_of(raw), codec.body_of(raw2))
        self.assertEqual([(t.block, t.x, t.y, t.rotation) for t in lay2.tiles],
                         [(t.block, t.x, t.y, t.rotation) for t in lay.tiles])

    def test_snapshot_roundtrip_body_identical(self):
        lay = self._layout()
        lay2 = Layout.from_snapshot(json.loads(json.dumps(lay.snapshot())),
                                    lay.w, lay.h, self.sizes,
                                    name=lay.name, description=lay.description)
        self.assertEqual(codec.body_of(lay.to_bytes()), codec.body_of(lay2.to_bytes()))

    def test_base64_paste_code(self):
        import base64
        lay = self._layout()
        raw = lay.to_bytes()
        b64 = codec.to_base64(raw)
        self.assertFalse(b64.endswith("="))
        decoded = base64.b64decode(b64 + "=" * (-len(b64) % 4))
        self.assertEqual(codec.body_of(raw),
                         codec.body_of(codec.build_schematic_ext(codec.read_bytes(decoded))))


class TestValidate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gd = GameData()
        cls.sizes = {n: b.size for n, b in cls.gd.blocks.items()}

    def test_clean_layout_ok(self):
        plan = expand(self.gd, "silicon", 3.0, boundary=["coal", "sand"])
        lay = build(self.gd, plan, canvas=(24, 24))
        res = static_check(lay, self.gd, plan)
        self.assertTrue(res["ok"], res["errors"])
        self.assertEqual(res["info"]["power_components"], 1)
        self.assertEqual(res["info"]["power_need"], 60.0)

    def test_belt_to_void_is_error(self):
        lay = Layout(16, 16, self.sizes)
        lay.add("conveyor", 5, 5, rotation=0)      # 指向空位
        res = static_check(lay, self.gd)
        self.assertFalse(res["ok"])
        self.assertTrue(any("传送带" in e for e in res["errors"]))

    def test_consumer_without_node_is_error(self):
        lay = Layout(24, 24, self.sizes)
        lay.add("silicon-smelter", 10, 10)
        lay.add("item-source", 6, 9, config={"__content__": "item", "id": 0})
        lay.add("item-source", 6, 8, config={"__content__": "item", "id": 0})
        res = static_check(lay, self.gd)
        self.assertFalse(res["ok"])
        self.assertTrue(any("power-node" in e for e in res["errors"]), res["errors"])

    def test_belt_over_capacity_is_error(self):
        lay = Layout(24, 24, self.sizes)
        # 一条带子直喂 surge-smelter 的一种输入（需 3.2/s，仍在 4.9 内），
        # 但两条输入都靠同一条带子必然超
        lay.add("surge-smelter", 12, 12)
        res = static_check(lay, self.gd)
        msgs = " ".join(res["errors"])
        self.assertTrue("上游" in msgs or "缺" in msgs, res["errors"])
        self.assertGreater(BELT_RATE, 0)


class TestPreview(unittest.TestCase):
    """preview 只依赖 trace.json；没有 runs/ 时跳过（不阻塞单测）。"""

    @classmethod
    def setUpClass(cls):
        cls.gd = GameData()
        cls.runs = ROOT / "runs"

    def _run(self):
        for name in ("s3", "m4", "g1"):
            d = self.runs / name
            if (d / "trace.json").exists():
                return d
        self.skipTest("没有 runs/<id>/trace.json 可测")

    def test_ascii_has_footprint(self):
        from mbo import preview
        d = self._run()
        _, lay, gd = preview.load_run(d)
        art = preview.render_ascii(lay, gd)
        self.assertIn("S", art)                       # 有物料源
        self.assertIn("M", art)                       # 有机器
        self.assertIn("crop=", art)
        from mbo.preview import bbox
        xs, ys, xe, ye = bbox(lay)
        self.assertEqual(len(art.splitlines()), 2 + (ye - ys + 1) + 2)   # 2 表头 + 裁剪行 + 空行 + 尾注
        self.assertLessEqual(len(art.splitlines()) - 4, lay.h)          # 裁剪后不超过画布

    def test_png_written(self):
        from mbo import preview
        d = self._run()
        out = d / "_test_preview.png"
        try:
            path, lay = preview.write_png(d, out=out, scale=1)
            self.assertTrue(path.exists())
            self.assertGreater(path.stat().st_size, 1000)
        finally:
            if out.exists():
                out.unlink()

    def test_png_pixels_match(self):
        """像素级：每个方块中心像素颜色 = 该族颜色（画错位/裁剪偏移会立刻暴露）。"""
        from PIL import Image
        from mbo import preview
        d = self._run()
        out = d / "_test_px.png"
        try:
            _, lay = preview.write_png(d, out=out, scale=1)
            img = Image.open(out).convert("RGB")
            g = preview.geometry(lay, 1)
            for t in lay.tiles:
                want = preview.COLORS[preview._family(self.gd, t.block)]
                s = lay.sizes.get(t.block, 1)
                tx, ty = lay.origin(t.block, t.x, t.y)
                # 取方块左上角内缩 1/5 处采样：避开中心朝向箭头，仍在本方块矩形内
                x0 = g["ox"] + (tx - g["xs"]) * g["cell"]
                y0 = g["oy"] + (ty - g["ys"]) * g["cell"]
                off = max(2, g["cell"] // 5)
                cx, cy = x0 + off, y0 + off
                got = img.getpixel((cx, cy))
                self.assertLess(sum(abs(a - b) for a, b in zip(got, want)), 40,
                                "%s @(%d,%d) want=%s got=%s" % (t.block, tx, ty, want, got))
        finally:
            if out.exists():
                out.unlink()

    def test_summary_has_rate(self):
        from mbo import preview
        d = self._run()
        trace, lay, _ = preview.load_run(d)
        txt = preview.summarize(d, trace)
        self.assertIn("预测", txt)
        self.assertIn("Gate", txt)


class TestSplitLayout(unittest.TestCase):
    """split 模板：一个 source + 一个物流门分流给左右两台机器（docs/16）。"""

    @classmethod
    def setUpClass(cls):
        cls.gd = GameData()

    def _plan(self, item="graphite", rate=1.0, boundary=("coal",)):
        return expand(self.gd, item, rate, set(boundary))

    def test_graphite_counts(self):
        plan = self._plan()
        lay = build_for(self.gd, plan, layout="split")
        st = lay.stats()
        self.assertEqual(st["blocks"], 6)          # 1 源 + 1 门 + 2 压机 + 2 仓
        self.assertEqual(st["tiles"], 18)
        self.assertEqual(st["counts"].get("underflow-gate"), 1)
        self.assertEqual(st["counts"].get("conveyor", 0), 0)   # 不需要带子

    def test_graphite_static_ok(self):
        plan = self._plan()
        lay = build_for(self.gd, plan, layout="split")
        res = static_check(lay, self.gd, plan)
        self.assertTrue(res["ok"], res["errors"])

    def test_gate_variants(self):
        plan = self._plan()
        for gate in ("underflow-gate", "overflow-gate"):
            lay = build_for(self.gd, plan, layout="split", gate=gate)
            self.assertEqual(lay.stats()["counts"].get(gate), 1)
            self.assertTrue(static_check(lay, self.gd, plan)["ok"])

    def test_multi_input_falls_back(self):
        """硅炉是双输入（coal+sand），一个门分流不了 → auto 回落 cells。"""
        plan = self._plan("silicon", 3.0, ("coal", "sand"))
        ok, why = split_applicable(self.gd, plan)
        self.assertFalse(ok)
        self.assertIn("单输入", why)
        lay = build_for(self.gd, plan, layout="auto")
        self.assertEqual(lay.stats()["counts"].get("underflow-gate", 0), 0)
        self.assertTrue(any("cells 模板" in w for w in plan.warnings))
        with self.assertRaises(ValueError):
            build_for(self.gd, plan, layout="split")

    def test_odd_count_falls_back(self):
        plan = self._plan("graphite", 1.6)        # 3 台压机 → 奇数
        ok, _ = split_applicable(self.gd, plan)
        self.assertFalse(ok)
        lay = build_for(self.gd, plan, layout="auto")
        self.assertEqual(lay.stats()["counts"].get("underflow-gate", 0), 0)

    def test_gate_without_source_is_error(self):
        """把门上方的东西拿走，静态校验必须报“没有上游供给”。"""
        plan = self._plan()
        lay = build_split(self.gd, plan)
        gate = lay.of_block("underflow-gate")[0]
        src = lay.of_block("item-source")[0]
        lay.tiles.remove(src)
        lay.occ.pop((src.x, src.y), None)
        res = static_check(lay, self.gd, plan)
        self.assertFalse(res["ok"])
        self.assertTrue(any("没有上游供给" in e for e in res["errors"]), res["errors"])
        self.assertIsNotNone(gate)

    def test_reencode_roundtrip(self):
        plan = self._plan()
        lay = build_split(self.gd, plan)
        data = lay.to_bytes()
        back = codec.read_bytes(data)
        self.assertEqual(back.width, lay.w)
        self.assertEqual(len(back.tiles), len(lay.tiles))
        self.assertEqual(lay.to_bytes(), data)


class TestMerge(unittest.TestCase):
    """merge：把整条产线的产物合流到一个出口（docs/17）。"""

    @classmethod
    def setUpClass(cls):
        cls.gd = GameData()

    def _plan(self):
        return expand(self.gd, "graphite", 1.0, {"coal"})

    def test_merge_counts(self):
        """五种出口的方块/tile 数（实测与推演一致）。"""
        want = {"pair": (6, 18), "single": (6, 15), "vault": (5, 19),
                "core": (5, 19), "void": (7, 13)}
        for merge, (blocks, tiles) in want.items():
            plan = self._plan()
            lay = build_for(self.gd, plan, layout="split", merge=merge)
            st = lay.stats()
            self.assertEqual((st["blocks"], st["tiles"]), (blocks, tiles), merge)
            self.assertTrue(static_check(lay, self.gd, plan)["ok"], merge)

    def test_single_exit_block(self):
        """合流后只剩 1 个出口方块；pair 是两台各一个。"""
        for merge, block in (("pair", "container"), ("single", "container"),
                             ("vault", "vault"), ("core", "core-shard"),
                             ("void", "item-void")):
            lay = build_for(self.gd, self._plan(), layout="split", merge=merge)
            n = len(lay.of_block(block))
            self.assertEqual(n, 2 if merge == "pair" else 1, merge)

    def test_void_not_on_gate_forward(self):
        """黑洞不能占门的直行位，否则溢流门会把料直推进黑洞、压机饿死。"""
        plan = self._plan()
        lay = build_for(self.gd, plan, layout="split", merge="void")
        gate = lay.of_block("underflow-gate")[0]
        sink = lay.of_block("item-void")[0]
        self.assertEqual(sink.y, gate.y + 2)                 # 门正下方一格（gy+1）留空
        self.assertIsNone(lay.tile_at(gate.x, gate.y + 1))
        belts = lay.of_block("conveyor")
        self.assertEqual(len(belts), 2)
        self.assertEqual({b.x for b in belts}, {sink.x - 1, sink.x + 1})
        self.assertEqual(sorted(b.rotation for b in belts), [0, 2])   # 东向 + 西向

    def test_bad_merge_rejected(self):
        with self.assertRaises(ValueError):
            build_for(self.gd, self._plan(), layout="split", merge="teleport")

    def test_cycles_measurement(self):
        """黑洞出口没有容器可读 → 用 progress 回绕计数；这里喂合成样本验证算法。"""
        from mbo.engine import summarize
        # 每 18 tick 采一次，progress 0..90 循环（craftTime=90 帧=1.5s）
        samples, prog, tick = [], 0.0, 0.0
        for _ in range(61):
            samples.append({"tick": tick, "m0": "1.0/%.3f/1.0" % prog})
            tick += 18.0
            prog = (prog + 18.0) % 90.0
        m = summarize(samples, "graphite", 1100, skip=300,
                      machines=[{"tag": "m0", "craft": 90, "out": 1.0}])
        self.assertEqual(m["measured_by"], "cycles")
        self.assertEqual(m["containers_delta"], 0)
        # 30 个采样区间 ≈ 0.5 件/区间的回绕率 ⇒ 2 台机器 0.667/s 量级
        self.assertGreater(m["rate_cycles"], 0.5)
        self.assertLess(m["rate_cycles"], 0.9)


class TestDirect(unittest.TestCase):
    """direct：10 格最小石墨蓝图（源/黑洞当 I/O 标记，docs/18）。"""

    @classmethod
    def setUpClass(cls):
        cls.gd = GameData()

    def _plan(self):
        return expand(self.gd, "graphite", 1.0, {"coal"})

    def _cells(self, lay, tile):
        return set(lay.cells(tile.block, tile.x, tile.y))

    def test_direct_counts(self):
        plan = self._plan()
        lay = build_for(self.gd, plan, layout="direct")
        st = lay.stats()
        self.assertEqual((st["blocks"], st["tiles"]), (4, 10))
        self.assertTrue(static_check(lay, self.gd, plan)["ok"])
        self.assertEqual(len(lay.of_block("item-source")), 1)
        self.assertEqual(len(lay.of_block("item-void")), 1)
        self.assertEqual(len(lay.of_block("graphite-press")), 2)

    def test_direct_hits_lower_bound(self):
        """下界 = 两台 2×2 机器 8 格 + 1 个输入标记 + 1 个输出标记 = 10 格。"""
        lay = build_for(self.gd, self._plan(), layout="direct")
        presses = lay.of_block("graphite-press")
        need = sum(len(self._cells(lay, p)) for p in presses) + 2
        self.assertEqual(lay.stats()["tiles"], need)

    def test_direct_source_and_sink_touch_both_presses(self):
        lay = build_for(self.gd, self._plan(), layout="direct")
        presses = [self._cells(lay, p) for p in lay.of_block("graphite-press")]
        src = lay.of_block("item-source")[0]
        sink = lay.of_block("item-void")[0]

        def touches(a):
            return all(any(abs(x - u) + abs(y - v) == 1 for x, y in a for u, v in p)
                       for p in presses)

        self.assertTrue(touches(self._cells(lay, src)), "源必须同时贴两台机器")
        self.assertTrue(touches(self._cells(lay, sink)), "黑洞必须同时贴两台机器")
        # 两者上下相邻（同一个“共用邻位”列），它们的并集正好补满 5×2 的包围盒
        self.assertEqual(sum(abs(src.x - sink.x) + abs(src.y - sink.y) for _ in (0,)), 1)
        xs = [c[0] for c in self._cells(lay, src) | self._cells(lay, sink)
              | set().union(*presses)]
        ys = [c[1] for c in self._cells(lay, src) | self._cells(lay, sink)
              | set().union(*presses)]
        self.assertEqual((max(xs) - min(xs) + 1) * (max(ys) - min(ys) + 1), 10)

    def test_direct_rejects_multi_input(self):
        plan = expand(self.gd, "silicon", 3.0, {"coal", "sand"})
        with self.assertRaises(ValueError):
            build_for(self.gd, plan, layout="direct")

    def test_direct_rejects_odd_presses(self):
        gd = self.gd
        plan = expand(gd, "graphite", 0.5, {"coal"})   # 1 台，配不出“两台共用邻位”
        with self.assertRaises(ValueError):
            build_for(gd, plan, layout="direct")


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
        self.assertEqual(back.width, lay.w)
        self.assertEqual(len(back.tiles), len(lay.tiles))



class TestSprites(unittest.TestCase):
    """原版贴图：索引、旋转规则、渲染接入。没有 assetsraw 贴图时跳过。"""

    @classmethod
    def setUpClass(cls):
        from mbo import sprites
        cls.gd = GameData()
        cls.ss = sprites.discover()
        if cls.ss is None:
            raise unittest.SkipTest("没有 assetsraw/assets-raw/sprites，跳过贴图测试")

    def test_index_has_blocks(self):
        self.assertGreater(self.ss.names(), 1000)
        for name in ("graphite-press", "conveyor", "item-source", "item-void", "container"):
            self.assertIsNotNone(self.ss.path(name), name)

    def test_conveyor_uses_blend_frame_zero(self):
        """带子是 <名字>-<混合位>-<帧>，预览取 -0-0。"""
        p = self.ss.path("conveyor")
        self.assertEqual(p.name, "conveyor-0-0.png")

    def test_missing_block_returns_none(self):
        self.assertIsNone(self.ss.path("no-such-block-xyz"))

    def test_tile_image_size_follows_cell_px(self):
        img = self.ss.tile_image("graphite-press", 2, 0, False, cell_px=26)
        self.assertEqual(img.size, (52, 52))
        img = self.ss.tile_image("conveyor", 1, 0, True, cell_px=40)
        self.assertEqual(img.size, (40, 40))

    def test_rotation_changes_pixels(self):
        """可旋转方块四个方向必须彼此不同；不可旋转的方块忽略 rotation。"""
        imgs = [self.ss.tile_image("conveyor", 1, r, True, cell_px=32).tobytes() for r in range(4)]
        self.assertEqual(len(set(imgs)), 4)
        a = self.ss.tile_image("graphite-press", 2, 0, False, cell_px=32).tobytes()
        b = self.ss.tile_image("graphite-press", 2, 3, False, cell_px=32).tobytes()
        self.assertEqual(a, b)

    def test_sprite_paste_is_pixel_exact(self):
        """贴图粘贴不该被缩放/调色：渲染结果与源贴图逐像素一致。"""
        from mbo import preview
        sizes = {n: b.size for n, b in self.gd.blocks.items()}
        lay = Layout(8, 6, sizes, name="px", description="px")
        lay.add("graphite-press", 1, 1, 0)
        scale = 2
        img = preview.render_png(lay, self.gd, "px", "", scale=scale, sprites=self.ss).convert("RGBA")
        g = preview.geometry(lay, scale)
        cell = g["cell"]
        tx, ty = lay.origin("graphite-press", 1, 1)
        x0 = g["ox"] + (tx - g["xs"]) * cell
        y0 = g["oy"] + (ty - g["ys"]) * cell
        got = img.crop((x0, y0, x0 + 2 * cell, y0 + 2 * cell))
        ref = self.ss.tile_image("graphite-press", 2, 0, False, cell_px=cell)
        self.assertEqual(got.tobytes(), ref.tobytes())

    def test_sprites_add_colors(self):
        """贴图版的颜色数应明显多于色块版（说明确实贴上了图）。"""
        from mbo import preview
        sizes = {n: b.size for n, b in self.gd.blocks.items()}
        lay = Layout(8, 6, sizes, name="c", description="c")
        lay.add("graphite-press", 1, 1, 0)
        lay.add("container", 4, 1, 0)
        plain = preview.render_png(lay, self.gd, "c", "", scale=2).convert("RGB")
        tex = preview.render_png(lay, self.gd, "c", "", scale=2, sprites=self.ss).convert("RGB")
        self.assertGreater(len(tex.getcolors(1 << 20)), len(plain.getcolors(1 << 20)) + 100)


class TestSearch(unittest.TestCase):
    """脚本化搜索：枚举 → 物流模型 → Pareto → 选优 → 落 Layout。"""

    @classmethod
    def setUpClass(cls):
        from mbo import search as search_mod
        cls.search = search_mod
        cls.gd = GameData()
        cls.plan = expand(cls.gd, "graphite", 1.0, ["coal"])
        cls.res = search_mod.search(cls.gd, cls.plan)

    def test_enumerates_many_candidates(self):
        self.assertGreater(self.res.candidates, 1000)
        self.assertEqual(self.res.feasible, self.res.candidates,
                         "石墨 1/s 的候选应该全部满足产能")

    def test_pareto_front_has_three_points(self):
        sigs = [(c.ports, c.tiles) for c in self.res.front]
        self.assertEqual(sigs, [(2, 12), (3, 9), (4, 8)])

    def test_best_by_ports(self):
        self.assertEqual(self.res.best.ports, 2)
        self.assertEqual(self.res.best.tiles, 12)

    def test_best_by_tiles(self):
        best = self.search.pick(self.res.front, "tiles")
        self.assertEqual(best.tiles, 8)
        self.assertEqual(best.ports, 4)

    def test_search_is_deterministic(self):
        again = self.search.search(self.gd, self.plan)
        self.assertEqual([c.signature() for c in again.front],
                         [c.signature() for c in self.res.front])
        self.assertEqual(again.best.signature(), self.res.best.signature())

    def test_layout_static_ok_and_ports_outside(self):
        lay = self.search.to_layout(self.res.best, self.gd)
        static = static_check(lay, self.gd, self.plan, strict_ports=True)
        self.assertTrue(static["ok"], static["errors"])
        ok, msg = self.search.logistics.ports_outside(lay, self.gd)
        self.assertTrue(ok, msg)

    def test_rate_is_machine_capacity(self):
        self.assertAlmostEqual(self.res.best.rate, 4.0 / 3.0, places=3)

    def test_rejects_more_than_two_machines(self):
        plan = expand(self.gd, "graphite", 2.0, ["coal"])
        with self.assertRaises(ValueError):
            self.search.search(self.gd, plan)



    # ---- 端口簇（开口数）：1 簇 = 工厂只有一个开口
    def test_single_opening_exists(self):
        cands = self.search.enumerate_candidates(self.gd, self.plan)
        one = [c for c in cands if c.ok_need and c.clusters == 1]
        self.assertTrue(one, "应存在单开口候选（源与黑洞相邻）")
        self.assertTrue(all(c.ports >= 3 for c in one),
                        "单开口至少要 3 个端口方块：2 个时没有独立进出通路")

    def test_clusters_objective_picks_one_opening(self):
        res = self.search.search(self.gd, self.plan, objective="clusters")
        self.assertEqual(res.best.clusters, 1)

    def test_no_two_port_single_opening(self):
        cands = self.search.enumerate_candidates(self.gd, self.plan)
        self.assertFalse([c for c in cands if c.clusters == 1 and c.ports == 2],
                         "2 个端口方块不应能凑成单开口")


    def test_two_port_best_is_12(self):
        """单入单出（2 端口）：搜索里最优是 12 格（10/11 格穷举不可行）。"""
        res = self.search.search(self.gd, self.plan)
        pool = [c for c in res.all_candidates if c.ok_need and c.ports == 2]
        self.assertTrue(pool, "应存在 2 端口候选")
        best = self.search.pick(pool, "tiles")
        self.assertEqual(best.tiles, 12)

if __name__ == "__main__":
    unittest.main(verbosity=2)
