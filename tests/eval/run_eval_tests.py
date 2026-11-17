#!/usr/bin/env python
"""tests/eval/run_eval_tests.py -- the contract tests for tools/mlog_eval.py.

The envelope is the interface three other modules build on (scenario runner,
MCP layer, mindcode front end), so its shape is asserted here rather than
assumed: which keys each level keeps, what a failure without a type does, and
that a real (if tiny) program walks the pipeline to a pass.

Exit codes: 0 all pass, 1 a test failed, 3 the JVM is unavailable (skipped).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import mlog_eval as E  # noqa: E402

FAILS: list[str] = []


def ok(cond: bool, what: str) -> None:
    if cond:
        print("ok   " + what)
    else:
        FAILS.append(what)
        print("FAIL " + what)


def test_envelope_shape() -> None:
    s = E.result(ok=True, stage="static", level="summary")
    ok(set(s) == {"schema", "ok", "stage", "failure_type", "message", "level",
                  "levels", "next_steps", "elapsed_ms"}, "summary envelope keys")
    ok(s["schema"] == "mlog-eval/v1", "schema tag is stable")
    ok(s["failure_type"] is None, "a pass carries no failure_type")
    ok(s["next_steps"] == [], "a pass suggests no next step")

    d = E.result(ok=False, stage="static", failure_type="static_analysis_error",
                 diagnostics=[{"kind": "finding", "sev": "ERR"}],
                 artifacts={"finding_counts": {"ERR": 1}}, level="diagnostics")
    ok("diagnostics" in d and d["diagnostics"][0]["sev"] == "ERR", "diagnostics kept")
    ok("artifacts" in d, "artifacts kept at diagnostics level")
    ok("trace" not in d, "trace dropped below full")

    f = E.result(ok=False, stage="simulation", failure_type="timeout",
                 trace={"rows": []}, level="full")
    ok("trace" in f, "trace kept at full level")


def test_vocabulary() -> None:
    for bad in ((), ("nope",)):
        try:
            E.result(ok=False, stage="x", failure_type=bad[0] if bad else None)
        except ValueError:
            ok(True, "rejects failure_type=%r" % (bad[0] if bad else None,))
        else:
            ok(False, "rejects failure_type=%r" % (bad[0] if bad else None,))

    ok(E.classify(TimeoutError("slow")) == "timeout", "timeout classifies")
    ok(E.classify(FileNotFoundError("x")) == "unsupported_environment",
       "missing file classifies as environment")
    ok(E.classify(RuntimeError("jre21 missing")) == "unsupported_environment",
       "message-based environment detection")
    ok(E.classify(RuntimeError("boom")) == "runtime_error", "generic runtime error")


def test_matches() -> None:
    ok(E._matches("12", "gt", 10), "numeric gt true")
    ok(not E._matches("8", "gt", 10), "numeric gt false")
    ok(E._matches("1.0", "eq", 1), "value compare across types")
    ok(E._matches("hello world", "contains", "wor"), "contains")
    ok(not E._matches(None, "eq", 1), "missing observation never matches")


def test_pipeline() -> None:
    env = E.evaluate(mlog="set x 1\nprint x\n", level="diagnostics")
    ok(env["ok"] is True, "valid program passes the static stage")
    ok(env["stage"] in ("static", "assertion"), "stage named from the pipeline")
    ok("finding_counts" in env["artifacts"], "finding counts reported")
    # "The executor finished" must not look like "the program is correct":
    # a static-only evaluation leaves execution/simulation unevaluated (None),
    # and only the stages that actually ran are true.
    ok(env["levels"]["static"] is True, "static stage marked true")
    ok(env["levels"]["execution"] is None and env["levels"]["simulation"] is None,
       "unrun stages stay None, not false")

    # A jump far outside the program is an ERR-level finding, so the static
    # stage must stop the pipeline there.  (Unknown builtins like `@nonsense`
    # are deliberately NOT errors -- mlogcheck is tolerant of newer content.)
    bad = E.evaluate(mlog="jump 99 always x greaterThan 1\n", level="diagnostics")
    ok(bad["ok"] is False and bad["failure_type"] == "static_analysis_error",
       "an ERR finding stops the pipeline as static_analysis_error")
    ok(bad["next_steps"], "failure carries a next step")

    # Truncated statements used to raise IndexError inside mlogcheck.uses_of
    # (`read x` has no operand at p[3]); the analyzer has to survive them,
    # because this stage must never crash on a half-written program.
    for src in ("read x\n", "write x\n", "sensor x\n", "getlink x\n",
                "ulocate x\n", "radar x\n"):
        try:
            env = E.evaluate(mlog=src, level="summary")
        except Exception as exc:            # noqa: BLE001
            ok(False, "truncated %r raised %s: %s" % (src.strip(), type(exc).__name__, exc))
        else:
            ok(True, "truncated %r analysed without crashing" % src.strip())

    yes = E.evaluate(mlog="set x 1\n", sim={"vars": {"x": "1"}},
                     expectations=[{"var": "x", "value": 1}], level="summary")
    ok(yes["ok"] is True, "expectation met")

    no = E.evaluate(mlog="set x 1\n", sim={"vars": {"x": "2"}},
                    expectations=[{"var": "x", "value": 1}], level="diagnostics")
    ok(no["ok"] is False and no["failure_type"] == "assertion_failed",
       "expectation missed -> assertion_failed")
    ok(any(d.get("kind") == "assertion" for d in no["diagnostics"]),
       "assertion diagnostic present")
    ok(no["levels"] == {"execution": True, "static": True, "simulation": False,
                        "real_runtime": None},
       "each success dimension recorded separately, got %s" % (no["levels"],))


def main() -> int:
    test_envelope_shape()
    test_vocabulary()
    test_matches()
    test_pipeline()
    print("-" * 48)
    if FAILS:
        print("%d failure(s):" % len(FAILS))
        for f in FAILS:
            print("  - " + f)
        return 1
    print("all %s passed" % os.path.basename(__file__))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
