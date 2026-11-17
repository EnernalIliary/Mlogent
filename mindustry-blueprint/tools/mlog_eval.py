#!/usr/bin/env python
"""mlog_eval.py -- one result envelope for every evaluation path.

Why this exists
---------------
Three callers used to answer "did it work?" in three dialects: `mlogcheck`
returns findings, `mlogsim` returns vars/text, `scene` returns checks, and the
MCP layer wrapped each of them in its own ad-hoc dict.  A model driving the
toolkit therefore had to learn three schemas and guess which of them said
"failed".  Worse, nothing distinguished *why* it failed -- a syntax error, a
static finding and a simulation that produced the wrong number all looked like
"ok: false with some text".

This module is the single answer shape:

    {"schema": "mlog-eval/v1", "ok": bool, "stage": str,
     "failure_type": <one of FAILURE_TYPES> | null, "message": str,
     "level": "summary"|"diagnostics"|"full",
     "diagnostics": [...], "artifacts": {...}, "next_steps": [...],
     "trace": null, "elapsed_ms": int}

`level` is the token budget knob: "summary" is what a model needs to decide the
next move (a dozen lines), "diagnostics" adds the findings/var dump, "full"
adds the execution trace.  Callers pass the level they can afford; nothing here
decides to dump 60 findings unasked.

`failure_type` is a closed vocabulary rather than free text, because the
repair move depends on it: a compilation error means fix the source, a timeout
means shrink the run, `unsupported_environment` means stop retrying and tell
the user, and `simulation_real_difference` means the model and the game
disagree (do not "fix" the program).

Run:  python tools/mlog_eval.py selftest
"""
from __future__ import annotations

import json
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

SCHEMA = "mlog-eval/v1"

#: Closed failure vocabulary (规划 §4 P2).  Adding a value here is a public
#: change: callers switch on these strings.
FAILURE_TYPES = (
    "compilation_error",          # the source does not compile (mindcode/asm)
    "static_analysis_error",      # it compiles, mlogcheck rejects it
    "runtime_error",              # the executor threw / the program died
    "assertion_failed",           # it ran, the expected value did not appear
    "timeout",                    # it did not finish inside the budget
    "unsupported_environment",    # no JVM/jar/feature here -- do not retry
    "simulation_real_difference", # mlogsim and the game disagree
)

#: Token budgets.  "diagnostics" is a superset of "summary"; "full" of both.
LEVELS = ("summary", "diagnostics", "full")

#: The four success dimensions of 规划 §4 P1, in the order they become
#: knowable.  A true value is evidence, None is "not evaluated", False is a
#: failure -- collapsing these into one boolean is exactly what makes a
#: simulation pass look like a shipping program.
SUCCESS_LEVELS = ("execution", "static", "simulation", "real_runtime")

#: What to do next, per failure type.  Short on purpose: this is what a model
#: reads before its next tool call, not documentation.
NEXT_STEPS = {
    "compilation_error": "Fix the reported source lines, then compile again.",
    "static_analysis_error": "Read the findings; rerun `python tools/mlog.py check FILE --cost` for the loop report.",
    "runtime_error": "Rerun with `python tools/mlogsim.py FILE --ticks 60 --update none --itrace out/_trace.txt` to see the failing step.",
    "assertion_failed": "Compare the observed values with the expectation; fix the program or the expectation (only one of them is wrong).",
    "timeout": "Lower --ticks/--steps or raise limits.timeout_s; an infinite loop also shows up here.",
    "unsupported_environment": "Run `python tools/mlog_doctor` (or `python tools/mlog_mcp.py` doctor) and fix the missing JVM/jar; do not retry blindly.",
    "simulation_real_difference": "Diff the two runs; the world server is the tie-breaker for anything engine-version dependent.",
}

_STAGE_ORDER = ("compilation", "static", "simulation", "assertion", "scenario")


def _trim(env: dict, level: str) -> dict:
    """Cut the envelope down to what *level* promises to deliver."""
    if level not in LEVELS:
        raise ValueError("level must be one of %s, got %r" % (LEVELS, level))
    keep = ["schema", "ok", "stage", "failure_type", "message", "level",
            "levels", "next_steps", "elapsed_ms"]
    if level in ("diagnostics", "full"):
        keep += ["diagnostics", "artifacts"]
    if level == "full":
        keep += ["trace"]
    out = {k: env[k] for k in keep if k in env}
    if level == "summary" and env.get("artifacts"):
        # References are pointers, not payloads: a caller in summary mode still
        # needs to know where the compiled code went, and a 40-character id
        # costs far less than losing the artifact entirely.
        refs = {k: v for k, v in env["artifacts"].items() if k.endswith("_ref")}
        if refs:
            out["artifacts"] = refs
    return out


def result(*, ok: bool, stage: str, failure_type: str | None = None,
           message: str = "", diagnostics: list | None = None,
           artifacts: dict | None = None, next_steps: list | None = None,
           trace: dict | None = None, level: str = "summary",
           levels: dict | None = None, elapsed_ms: int | None = None) -> dict:
    """Build one envelope.  See the module docstring for the shape.

    ``ok=False`` requires a known ``failure_type`` -- an untyped failure is the
    thing this module exists to prevent, so it is a programming error, not a
    runtime condition.
    """
    if not ok and failure_type is None:
        raise ValueError("ok=False needs a failure_type (one of %s)" % (FAILURE_TYPES,))
    if failure_type is not None and failure_type not in FAILURE_TYPES:
        raise ValueError("unknown failure_type %r (one of %s)"
                         % (failure_type, FAILURE_TYPES))
    env = {
        "schema": SCHEMA,
        "ok": bool(ok),
        "stage": stage,
        "failure_type": failure_type,
        "message": message or "",
        "level": level,
        # The four success dimensions from 规划 §4 P1: they are not
        # interchangeable, and "the executor finished" is not "the program was
        # correct".  None means "that stage did not run", not "failed".
        "levels": {k: (levels or {}).get(k) for k in SUCCESS_LEVELS},
        "diagnostics": list(diagnostics or []),
        "artifacts": dict(artifacts or {}),
        "next_steps": list(next_steps if next_steps is not None
                           else ([NEXT_STEPS[failure_type]] if failure_type else [])),
        "trace": trace,
        "elapsed_ms": int(elapsed_ms) if elapsed_ms is not None else 0,
    }
    return _trim(env, level)


def classify(exc: BaseException) -> str:
    """Map an exception to the failure vocabulary.

    Deliberately coarse: the point is the *repair move*, not the exception
    class.  Anything that means "this machine cannot run it" is
    unsupported_environment; everything else that blew up during execution is a
    runtime_error.
    """
    name = type(exc).__name__
    text = str(exc).lower()
    if name in ("TimeoutExpired", "TimeoutError") or "timed out" in text:
        return "timeout"
    if name in ("FileNotFoundError", "PermissionError"):
        return "unsupported_environment"
    if "no java" in text or "no jre" in text or "jre21" in text or "server jar" in text:
        return "unsupported_environment"
    if isinstance(exc, SyntaxError):
        return "compilation_error"
    return "runtime_error"


def summarize(env: dict) -> str:
    """One line for a log or a chat reply."""
    if env.get("ok"):
        return "PASS %s (%d ms)" % (env.get("stage"), env.get("elapsed_ms") or 0)
    return "FAIL %s [%s] %s" % (env.get("stage"), env.get("failure_type"),
                                (env.get("message") or "").splitlines()[0][:160])


# ---------------------------------------------------------------- evaluation

def _static_findings(mlog: str) -> list:
    """Run the repo's own static analyzer over mlog source text."""
    import mlogcheck as _check
    lines = mlog.split("\n")
    try:
        prepared = _check.prepare(lines)
        names = getattr(prepared, "links", None)
    except Exception:                       # noqa: BLE001 -- analyzer is lenient
        prepared, names = lines, None
    findings = _check.analyse(lines, names)
    return [{"kind": "finding", "sev": f.sev, "line": f.line,
             "code": f.code, "message": f.msg} for f in findings]


def _simulate(mlog: str, *, ticks: int = 60, steps: int | None = None,
              timeout: float | None = None) -> dict:
    """Run mlog on the real executor and return its record."""
    import mlogsim as _sim
    srv = _sim.Server(_sim._default_java(), _sim._default_jar())
    try:
        return _sim.run_mlog(srv, "eval", mlog, steps or ticks,
                             ticks=steps is None, update="all")
    finally:
        try:
            srv.close()
        except Exception:                   # noqa: BLE001
            pass


def evaluate(*, mlog: str | None = None, static: bool = True,
             sim: dict | None = None, expectations: list | None = None,
             limits: dict | None = None, level: str = "summary",
             workdir: str | None = None) -> dict:
    """Walk the pipeline stages this caller asked for and stop at the first
    failure.

    ``sim`` is the record produced by the simulation stage (or None to run it
    here when ``limits`` asks for it); ``expectations`` is a list of
    ``{"var": name, "op": ..., "value": ...}`` checked against the result.
    """
    del workdir                            # reserved: callers may sandbox later
    t0 = time.time()
    limits = limits or {}
    diagnostics: list = []
    artifacts: dict = {}
    # The four success dimensions start out "not evaluated" (None).  Each stage
    # lowers the ones it made observable; a False sticks even when a later stage
    # is skipped, so "the executor finished" never upgrades a static failure.
    lv = {k: None for k in SUCCESS_LEVELS}

    def done(ok: bool, stage: str, failure_type=None, message="", extra=None) -> dict:
        if extra:
            artifacts.update(extra)
        return result(ok=ok, stage=stage, failure_type=failure_type,
                      message=message, diagnostics=diagnostics,
                      artifacts=artifacts, level=level, levels=lv,
                      elapsed_ms=int((time.time() - t0) * 1000))

    if static and mlog is not None:
        try:
            findings = _static_findings(mlog)
        except Exception as exc:            # noqa: BLE001
            lv["static"] = False
            diagnostics.append({"kind": "static", "message": "%s: %s"
                                % (type(exc).__name__, exc)})
            return done(False, "static", classify(exc), "static analysis crashed")
        diagnostics.extend(findings)
        errors = [f for f in findings if f["sev"] in ("ERR", "SUSPECT")]
        artifacts["finding_counts"] = {
            s: sum(1 for f in findings if f["sev"] == s)
            for s in ("ERR", "SUSPECT", "WARN", "INFO")}
        lv["static"] = not errors
        if errors:
            return done(False, "static", "static_analysis_error",
                        "%d error-level finding(s)" % len(errors),
                        {"first_error": errors[0]})

    if sim is None and limits.get("ticks"):
        try:
            sim = _simulate(mlog or "", ticks=int(limits["ticks"]))
        except Exception as exc:            # noqa: BLE001
            lv["execution"] = False
            diagnostics.append({"kind": "sim", "message": "%s: %s"
                                % (type(exc).__name__, exc)})
            return done(False, "simulation", classify(exc), "simulation failed")

    if sim is not None:
        artifacts["sim"] = {k: sim.get(k) for k in ("vars", "counter", "text")
                            if k in sim}
        if sim.get("error"):
            lv["execution"] = False
            diagnostics.append({"kind": "sim", "message": str(sim["error"])})
            return done(False, "simulation", "runtime_error", str(sim["error"]))
        lv["execution"] = True

    if expectations and sim is not None:
        vals = sim.get("vars") or {}
        failed = []
        for exp in expectations:
            name = exp.get("var")
            actual = vals.get(name)
            if not _matches(actual, exp.get("op", "eq"), exp.get("value")):
                failed.append({"var": name, "expect": exp.get("value"),
                               "op": exp.get("op", "eq"), "actual": actual})
        lv["simulation"] = not failed
        if failed:
            diagnostics.extend({"kind": "assertion", **f} for f in failed)
            return done(False, "assertion", "assertion_failed",
                        "%d of %d expectation(s) failed"
                        % (len(failed), len(expectations)), {"failed": failed})

    stage = "assertion" if expectations else (limits.get("ticks") and "simulation" or "static")
    return done(True, stage)


def _matches(actual, op: str, expect) -> bool:
    """Compare one observed value.  Everything arrives as a string from the
    executor, so numbers are compared numerically when both sides parse."""
    if op == "contains":
        return actual is not None and str(expect) in str(actual)
    if op == "ne":
        return str(actual) != str(expect)
    if actual is None:
        return False
    if op in ("gt", "ge", "lt", "le"):
        try:
            a, e = float(actual), float(expect)
        except (TypeError, ValueError):
            return False
        return {"gt": a > e, "ge": a >= e, "lt": a < e, "le": a <= e}[op]
    try:
        return float(actual) == float(expect)
    except (TypeError, ValueError):
        return str(actual) == str(expect)


# ---------------------------------------------------------------- CLI

def selftest() -> int:
    """Prove the envelope trims and the vocabulary holds -- no JVM involved."""
    fails = 0

    def ok(cond, what):
        nonlocal fails
        if not cond:
            fails += 1
            print("FAIL " + what)
        else:
            print("ok   " + what)

    s = result(ok=True, stage="static", level="summary")
    ok(set(s) == {"schema", "ok", "stage", "failure_type", "message", "level",
                  "levels", "next_steps", "elapsed_ms"},
       "summary keeps 9 keys, got %s" % sorted(s))
    ok(set(s["levels"]) == set(SUCCESS_LEVELS) and not any(s["levels"].values()),
       "a bare result leaves every success level unevaluated")
    d = result(ok=False, stage="static", failure_type="static_analysis_error",
               diagnostics=[{"kind": "finding"}], artifacts={"a": 1},
               level="diagnostics")
    ok("diagnostics" in d and "artifacts" in d and "trace" not in d,
       "diagnostics level adds findings but not trace")
    f = result(ok=False, stage="simulation", failure_type="timeout", trace={"t": 1},
               level="full")
    ok("trace" in f, "full level carries the trace")
    ok(f["next_steps"] == [NEXT_STEPS["timeout"]], "default next_steps follow failure_type")
    try:
        result(ok=False, stage="x")
    except ValueError:
        ok(True, "untyped failure is rejected")
    else:
        ok(False, "untyped failure is rejected")
    try:
        result(ok=False, stage="x", failure_type="nope")
    except ValueError:
        ok(True, "unknown failure_type is rejected")
    else:
        ok(False, "unknown failure_type is rejected")
    ok(classify(TimeoutError("boom")) == "timeout", "TimeoutError -> timeout")
    ok(classify(FileNotFoundError("no jar")) == "unsupported_environment",
       "FileNotFoundError -> unsupported_environment")
    ok(classify(RuntimeError("x")) == "runtime_error", "RuntimeError -> runtime_error")
    ok(summarize(result(ok=True, stage="static", elapsed_ms=3)).startswith("PASS static"),
       "summarize on success")
    ok(_matches("12", "gt", 10) and not _matches("8", "gt", 10), "numeric gt")
    ok(_matches("abc def", "contains", "def"), "string contains")
    ok(_matches("1.0", "eq", 1), "numeric eq across types")

    env = evaluate(mlog="set x 1\nprint x\n", level="summary")
    ok(env["ok"] is True, "tiny valid program passes static stage")
    ok(env["stage"] in _STAGE_ORDER[:4], "stage is from the vocabulary")

    print("-" * 48)
    print("selftest: %d failure(s)" % fails)
    return 1 if fails else 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.split("\n\n")[0])
        print("usage: python tools/mlog_eval.py selftest")
        return 0 if argv else 2
    if argv[0] == "selftest":
        return selftest()
    print("unknown command %r" % argv[0], file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:                       # noqa: BLE001
        traceback.print_exc()
        raise SystemExit(1)
