"""Tests for tools/explore.py -- exploration and failure shrinking.

The shrinking algorithm is tested with a fake oracle: a delta-debugger's bugs
are in the algorithm, and an algorithm does not need a JVM to be wrong.  The
integration case (one real scenario run) is gated on a compiler/JRE being
present, so CI still covers everything above it.
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import explore as X                                     # noqa: E402

MOD = {"kind": "unit_movement", "at_tick": 10,
       "params": {"mode": "push", "dx": 2, "dy": 0}}


def _jvm_ready():
    try:
        import scenario as S
    except Exception:                                   # noqa: BLE001
        return False
    env = S.environment()
    return bool(env.get("ok"))


class Ddmin(unittest.TestCase):
    def test_no_failure_means_no_repro(self):
        self.assertEqual(X.ddmin([1, 2, 3], lambda xs: False), [])

    def test_empty_input(self):
        self.assertEqual(X.ddmin([], lambda xs: True), [])

    def test_finds_the_minimal_set_and_keeps_order(self):
        need = {"a", "c"}
        items = ["x1", "a", "y2", "c", "z3", "w4"]
        got = X.ddmin(items, lambda xs: need <= set(xs))
        self.assertEqual(got, ["a", "c"])

    def test_handles_a_complement_case(self):
        # failure needs "keep" to be ABSENT: the complement branch has to fire,
        # which is the half that naive shrinkers forget
        items = ["keep", "a", "b", "c"]
        got = X.ddmin(items, lambda xs: "keep" not in xs)
        self.assertEqual(got, [])

    def test_monotone_failure_terminates_small(self):
        got = X.ddmin(list("abcdefgh"), lambda xs: len(xs) >= 2)
        self.assertLessEqual(len(got), 3)

    def test_single_item_survives(self):
        got = X.ddmin(["boom"], lambda xs: bool(xs))
        self.assertEqual(got, ["boom"])


class Space(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="mlog-ex-")
        self._old = os.environ.get("MLOG_EXPLORE_DIR")
        os.environ["MLOG_EXPLORE_DIR"] = self.tmp

    def tearDown(self):
        if self._old is None:
            os.environ.pop("MLOG_EXPLORE_DIR", None)
        else:
            os.environ["MLOG_EXPLORE_DIR"] = self._old

    def test_seed_order_and_isolation(self):
        pts = X.space("unit-control", seeds=(5, 3), modifiers=[MOD])
        self.assertEqual([p["seed"] for p in pts], [5, 3])
        self.assertIsNot(pts[0]["modifiers"], pts[1]["modifiers"])
        pts[0]["modifiers"].append({"kind": "unit_death"})
        self.assertEqual(len(pts[1]["modifiers"]), 1)

    def test_variant_is_runnable(self):
        sc = X.variant(X.space("unit-control", seeds=(2,))[0])
        self.assertEqual(sc["version"], 2)
        self.assertIn("world", sc)
        self.assertEqual(sc["id"], "unit-control-seed2")

    def test_variant_carries_modifiers(self):
        sc = X.variant(X.space("unit-control", seeds=(1,), modifiers=[MOD])[0])
        self.assertEqual(len(sc["modifiers"]), 1)
        self.assertEqual(sc["modifiers"][0]["kind"], "unit_movement")


class Explore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="mlog-ex-")
        self._old = os.environ.get("MLOG_EXPLORE_DIR")
        os.environ["MLOG_EXPLORE_DIR"] = self.tmp

    def tearDown(self):
        if self._old is None:
            os.environ.pop("MLOG_EXPLORE_DIR", None)
        else:
            os.environ["MLOG_EXPLORE_DIR"] = self._old

    def test_failures_are_kept_with_their_point(self):
        pts = X.space("unit-control", seeds=(1, 2, 3))

        def ev(sc):
            seed = int(sc["id"].rsplit("seed", 1)[1])
            return {"id": sc["id"], "ok": seed != 2, "skipped": False}

        rep = X.explore(pts, evaluator=ev)
        self.assertEqual(rep["summary"]["failed"], 1)
        self.assertEqual(rep["failures"][0]["point"]["seed"], 2)

    def test_limit_stops_early(self):
        pts = X.space("unit-control", seeds=tuple(range(1, 9)))
        rep = X.explore(pts, evaluator=lambda sc: {"id": sc["id"], "ok": False,
                                                   "skipped": False}, limit=2)
        self.assertEqual(rep["summary"]["failed"], 2)
        self.assertEqual(rep["ran"], 2)

    def test_unsupported_host_is_skipped_not_failed(self):
        pts = X.space("unit-control", seeds=(1, 2))
        rep = X.explore(pts, evaluator=lambda sc: {"id": sc["id"], "ok": False,
                                                   "skipped": True})
        self.assertEqual(rep["failures"], [])
        self.assertEqual(rep["skipped"], 2)
        self.assertFalse(rep["summary"]["ok"])

    def test_shrink_drops_the_harmless_modifiers(self):
        noisy = [MOD, {"kind": "unit_movement", "at_tick": 30,
                       "params": {"mode": "push", "dx": -1, "dy": 0}},
                 {"kind": "unit_death", "at_tick": 12,
                  "params": {"mode": "kill", "count": 64}}]
        point = X.space("unit-control", seeds=(1,), modifiers=noisy)[0]

        # oracle: only the unit_death entry makes the run fail
        def ev(sc):
            kinds = [m["kind"] for m in sc.get("modifiers") or []]
            return {"id": sc["id"], "ok": "unit_death" not in kinds,
                    "skipped": False}

        rep = X.shrink(point, evaluator=ev)
        self.assertTrue(rep["shrank"])
        self.assertEqual([m["kind"] for m in rep["modifiers"]], ["unit_death"])
        self.assertEqual(rep["dropped"], 2)

    def test_shrink_says_so_when_the_point_passes(self):
        point = X.space("unit-control", seeds=(1,), modifiers=[MOD])[0]
        rep = X.shrink(point, evaluator=lambda sc: {"ok": True, "skipped": False})
        self.assertFalse(rep["shrank"])
        self.assertEqual(rep["why"], "point does not fail")

    def test_ledger_roundtrip(self):
        rep = {"schema": X.SCHEMA, "summary": {"points": 1, "failed": 0}}
        path = X.save(rep, directory=self.tmp, name="one")
        self.assertTrue(os.path.isfile(path))
        got = X.load_runs(self.tmp)
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]["schema"], X.SCHEMA)


@unittest.skipUnless(_jvm_ready(), "no JRE/jar on this checkout")
class Integration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="mlog-ex-int-")
        self._old = os.environ.get("MLOG_EXPLORE_DIR")
        os.environ["MLOG_EXPLORE_DIR"] = self.tmp

    def tearDown(self):
        if self._old is None:
            os.environ.pop("MLOG_EXPLORE_DIR", None)
        else:
            os.environ["MLOG_EXPLORE_DIR"] = self._old

    def test_one_seed_runs_and_reports_a_verdict(self):
        rep = X.explore(X.space("unit-control", seeds=(1,)))
        self.assertEqual(rep["ran"], 1)
        row = rep["runs"][0]
        self.assertIn("ok", row)
        self.assertFalse(row.get("skipped"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
