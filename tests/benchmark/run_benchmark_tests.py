#! /usr/bin/env python
"""Tests for tools/benchmark.py.

Two halves, deliberately: everything about *bookkeeping* (task files, prompts,
recorded runs, scores) runs anywhere; everything about *judging a program* needs
the real executor, so it is skipped -- not faked -- on a checkout without one.
A benchmark that silently scored nothing would be worse than no benchmark.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import benchmark as B          # noqa: E402
import mlogsim                 # noqa: E402

ANSWERS = os.path.join(HERE, "answers")


def sim_ready() -> bool:
    try:
        jar = mlogsim._default_jar()
        java = mlogsim._default_java()
    except Exception:                                  # noqa: BLE001
        return False
    return bool(jar and java and os.path.isfile(jar))


class Tasks(unittest.TestCase):
    def test_tasks_load_and_are_unique(self):
        known = B.tasks()
        self.assertGreaterEqual(len(known), 6)
        ids = [t["id"] for t in known]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids, sorted(ids), "list order is by file name")

    def test_every_task_is_answerable_and_checkable(self):
        for task in B.tasks():
            with self.subTest(task=task["id"]):
                self.assertTrue(task["prompt"].strip())
                accept = task["acceptance"]
                self.assertIn(accept["kind"], ("validate", "scene", "static"))
                if accept["kind"] == "static":
                    # 静态任务的判据是「分析器无 ERR」，没有逐变量断言
                    self.assertEqual(accept.get("checks") or [], [])
                    continue
                self.assertTrue(accept.get("checks") or accept.get("expect"))
                limits = accept["limits"]
                self.assertTrue("ticks" in limits or "instructions" in limits,
                                "a task needs a budget")
                budget = limits.get("instructions") or limits.get("ticks")
                self.assertGreaterEqual(budget, 100,
                                        "the executor is slow; a short budget "
                                        "would fail correct answers")

    def test_prompt_hides_the_acceptance(self):
        """The prompt must not read like a test case, or it measures nothing."""
        for task in B.tasks():
            with self.subTest(task=task["id"]):
                self.assertNotIn(task["id"], task["prompt"])
                self.assertNotIn("acceptance", task["prompt"].lower())

    def test_prompt_wrapper(self):
        text = B.prompt(B.find("arithmetic-constants"))
        self.assertIn("(3 + 4) * 5", text)
        self.assertIn("checked mechanically", text)

    def test_unknown_task(self):
        with self.assertRaises(SystemExit):
            B.find("no-such-task")


class Runs(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="mlog-bench-test-")
        self.saved = os.environ.get("MLOG_BENCH_DIR")
        os.environ["MLOG_BENCH_DIR"] = self.tmp

    def tearDown(self):
        if self.saved is None:
            os.environ.pop("MLOG_BENCH_DIR", None)
        else:
            os.environ["MLOG_BENCH_DIR"] = self.saved
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_record_and_load(self):
        row = B.record_run(task="t", success="yes", model="m", tokens_in=10,
                           tokens_out=2, tool_calls=4)
        self.assertTrue(row["success"])
        self.assertTrue(row["first_pass"], "first_pass defaults to success")
        rows = B.load_runs()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["tool_calls"], 4)

    def test_record_requires_task_and_verdict(self):
        with self.assertRaises(SystemExit):
            B.record_run(success="yes")
        with self.assertRaises(SystemExit):
            B.record_run(task="t")

    def test_bad_line_is_ignored(self):
        os.makedirs(self.tmp, exist_ok=True)
        with open(os.path.join(self.tmp, "runs.jsonl"), "w", encoding="utf-8") as fh:
            fh.write('{"task": "a", "success": true}\n')
            fh.write("not json\n")
        self.assertEqual(len(B.load_runs()), 1)

    def test_score_arithmetic(self):
        B.record_run(task="a", success="yes", tokens_in=100, tokens_out=20,
                     tool_calls=2, repairs=0)
        B.record_run(task="b", success="no", tokens_in=60, tokens_out=20,
                     tool_calls=6, repairs=3, interventions=2)
        one = B.score(B.load_runs())
        self.assertEqual(one["success_rate"], 0.5)
        self.assertEqual(one["first_pass_rate"], 0.5)
        self.assertEqual(one["tokens_per_success"], 200.0)
        self.assertEqual(one["mean_repairs"], 1.5)
        self.assertEqual(one["interventions"], 2)

    def test_score_empty(self):
        empty = B.score([])
        self.assertEqual(empty["runs"], 0)
        self.assertIsNone(empty["tokens_per_success"])

    def test_filters(self):
        B.record_run(task="a", success="yes", model="m1")
        B.record_run(task="a", success="no", model="m2")
        self.assertEqual(len(B.load_runs(model="m1")), 1)
        self.assertEqual(len(B.by_model(B.load_runs())), 2)


class StaticJudge(unittest.TestCase):
    """Judged by the analyzer alone: this class runs even without a jar."""

    def test_static_task_needs_no_executor(self):
        good = B.verify(B.find("repair-a-static-error"),
                        file=os.path.join(ANSWERS, "static-good.mlog"))
        self.assertTrue(good["ok"], good)
        bad = B.verify(B.find("repair-a-static-error"),
                       file=os.path.join(ANSWERS, "static-bad.mlog"))
        self.assertFalse(bad["ok"])
        self.assertEqual(bad["failures"][0]["sev"], "ERR")


class Judge(unittest.TestCase):
    """The half that needs the real executor."""

    def setUp(self):
        if not sim_ready():
            self.skipTest("no executor jar/java on this checkout")
        self.tmp = tempfile.mkdtemp(prefix="mlog-bench-judge-")
        self.saved = os.environ.get("MLOG_BENCH_DIR")
        os.environ["MLOG_BENCH_DIR"] = self.tmp

    def tearDown(self):
        if getattr(self, "saved", None) is None:
            os.environ.pop("MLOG_BENCH_DIR", None)
        elif hasattr(self, "saved"):
            os.environ["MLOG_BENCH_DIR"] = self.saved
        shutil.rmtree(getattr(self, "tmp", ""), ignore_errors=True)

    def _verify(self, task_id, name):
        return B.verify(B.find(task_id), file=os.path.join(ANSWERS, name))

    def test_good_answer_passes(self):
        for task_id, name in (("arithmetic-constants", "arith-good.mlog"),
                              ("branch-on-comparison", "branch-good.mlog"),
                              ("compute-average", "average-good.mlog"),
                              ("emit-a-text-report", "text-good.mlog"),
                              ("repair-a-hanging-program", "hang-good.mlog")):
            with self.subTest(task=task_id):
                out = self._verify(task_id, name)
                self.assertTrue(out["ok"], out)

    def test_wrong_answer_fails(self):
        out = self._verify("arithmetic-constants", "arith-bad.mlog")
        self.assertFalse(out["ok"])
        self.assertEqual(out["failures"][0]["check"]["name"], "r")

    def test_branch_task_rejects_the_constant_answer(self):
        out = self._verify("branch-on-comparison", "branch-bad.mlog")
        self.assertFalse(out["ok"])

    def test_hanging_program_never_finishes(self):
        """The unrepaired program must lose: `done` is never set."""
        out = self._verify("repair-a-hanging-program", "hang-bad.mlog")
        self.assertFalse(out["ok"])
        names = [f["check"]["name"] for f in out["failures"]]
        self.assertIn("done", names)

    def test_a_typed_answer_fails_the_executed_check(self):
        """`set r 35` reaches the right state without computing it.

        The end-state check alone cannot tell it from `op add` + `op mul`; the
        executor's per-instruction trace can, because it records the source line
        behind every step.  A determined liar can still execute a real `op add`
        and overwrite the result, so this is a floor, not a proof.
        """
        out = self._verify("arithmetic-constants", "arith-typed.mlog")
        self.assertFalse(out["ok"], out)
        kinds = [list(f["check"]) for f in out["failures"]]
        self.assertIn(["executed"], kinds)
        self.assertIn("no op add", out["failures"][0]["executed"])

    def test_executed_check_reads_the_trace_not_the_source(self):
        """The rule is "an arithmetic instruction ran", not "the file says op"."""
        lines = ["set t 3", "op add t t 4", "op mul r t 5"]
        self.assertIsNone(B._executed_failure(lines, {"any_of": ["op add"]}))
        bad = B._executed_failure(["set r 35"], {"any_of": ["op add", "op mul"]})
        self.assertIn("no op add/op mul executed", bad)
        self.assertIsNone(B._executed_failure(["whatever"], {}))

    def test_missing_file(self):
        with self.assertRaises(SystemExit):
            B.verify(B.find("arithmetic-constants"), file=None)


if __name__ == "__main__":
    unittest.main(verbosity=2)
