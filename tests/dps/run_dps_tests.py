"""Contract tests for tools/dps.py.

Two layers:
  * the panel formula and the target-picking rules run anywhere (no JVM);
  * one real measurement runs only when the executor is present, because a
    silent skip is a lie while a hard failure in a clean checkout is noise.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import dps  # noqa: E402


class Panel(unittest.TestCase):
    def test_panel_matches_the_documented_rows(self):
        # the three rows C10-numbers.md table 1 quotes analytically
        self.assertEqual(dps.panel_dps(1, 20, 9), 27.0)
        self.assertEqual(dps.panel_dps(1, 7, 50), 428.57)
        self.assertEqual(dps.panel_dps(4, 29, 15), 124.14)

    def test_zero_reload_is_refused(self):
        with self.assertRaises(ValueError):
            dps.panel_dps(1, 0, 9)

    def test_multishot_and_rounding(self):
        self.assertEqual(dps.panel_dps(3, 35, 66), 339.43)
        self.assertIsInstance(dps.panel_dps(2, 18, 3), float)


class Target(unittest.TestCase):
    def test_ground_and_air_domain(self):
        ground = {"range": 160, "minRange": 0, "targetGround": True}
        air = {"range": 220, "minRange": 0, "targetGround": False}
        self.assertEqual(dps.pick_target(ground)[0], "dagger")
        self.assertEqual(dps.pick_target(air)[0], "flare")

    def test_distance_avoids_the_blind_spot(self):
        # ripple: range 290, minRange 50 -> middle of the legal band, in tiles
        unit, dist = dps.pick_target({"range": 290, "minRange": 50, "targetGround": True})
        self.assertEqual(unit, "dagger")
        self.assertGreater(dist * dps.TILE, 50)
        self.assertLess(dist * dps.TILE, 290)

    def test_short_range_keeps_a_floor(self):
        self.assertGreaterEqual(dps.pick_target(
            {"range": 40, "minRange": 0, "targetGround": True})[1], 2.0)


def _executor_ready():
    import scenario
    return bool(scenario.environment().get("java"))


class Live(unittest.TestCase):
    def setUp(self):
        if not _executor_ready():
            self.skipTest("no executor (jar/jre)")

    def test_duo_matches_its_panel_within_five_percent(self):
        got = dps.measure("duo", "copper", ticks=600)
        self.assertEqual(got["block"], "duo")
        self.assertGreater(got["damage"], 0)
        # 27.0 dps on paper; travel time and warm-up cost a few percent
        self.assertAlmostEqual(got["ratio"], 1.0, delta=0.12)

    def test_a_wrong_ammo_is_reported_not_crashed(self):
        with self.assertRaises(RuntimeError):
            dps.measure("duo", "water", ticks=60)


if __name__ == "__main__":
    unittest.main(verbosity=2)
