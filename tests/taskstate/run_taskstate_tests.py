#!/usr/bin/env python3
"""Contract tests for taskstate -- the record that survives between turns.

What this pins down (规划 §5 P1): a task file is written before it is reported,
``completed_stages`` belongs to the ``source_version`` it was measured on, a
failure is never treated as a skip, and reopening a task in a *new process* sees
exactly what the previous one wrote.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import mlog_eval as E      # noqa: E402
import taskstate as T      # noqa: E402

FAILS: list[str] = []


def ok(cond, what: str) -> None:
    if not cond:
        FAILS.append(what)
        print("FAIL " + what)


def test_record_roundtrip() -> None:
    tmp = tempfile.mkdtemp(prefix="mlog-ts-")
    os.environ["MLOG_TASK_DIR"] = tmp
    src = "set x 1\n"
    task = T.begin(source=src, target="7.0", hypothesis="x should be 1")
    ok(task["schema"] == "mlog-task/v1", "schema tag")
    ok(task["id"] == task["task_id"], "storage key mirrors task_id")
    ok(task["source_version"] and len(task["source_version"]) == 12,
       "source_version is a 12-hex content hash")
    ok(task["created"] and task["updated"], "timestamps present")

    T.record(task, stage="static", ok=True, source=src)
    r = T.resume(task["task_id"])
    ok(r["completed_stages"] == ["static"], "static recorded")
    ok(r["next_stage"] == "simulation", "resume points at the next stage")

    # reopen through the filesystem, as a second process would
    again = T.load(task["task_id"])
    ok(again is not None and again["completed_stages"] == ["static"],
       "the record is on disk, not just in memory")
    raw = json.load(open(os.path.join(tmp, task["task_id"] + ".json"), encoding="utf-8"))
    ok(raw["task_id"] == task["task_id"], "file name and field agree")
    shutil.rmtree(tmp, ignore_errors=True)


def test_failure_is_rechecked_not_skipped() -> None:
    tmp = tempfile.mkdtemp(prefix="mlog-ts-")
    os.environ["MLOG_TASK_DIR"] = tmp
    src = "set x 1\n"
    task = T.begin(source=src)
    T.record(task, stage="static", ok=True, source=src)
    T.record(task, stage="simulation", ok=False, failure_type="runtime_error",
             notes="counter ran off", next_step="cap the loop", source=src)
    r = T.resume(task["task_id"])
    ok(r["failed_stages"] == ["simulation"], "failure recorded")
    ok(r["next_stage"] == "simulation", "a failure outranks the frontier")
    ok(r["next_step"] == "cap the loop", "next_step survives")

    T.record(task, stage="simulation", ok=True, source=src)
    r = T.resume(task["task_id"])
    ok(r["failed_stages"] == [], "a successful retry clears the failure")
    ok(r["completed_stages"] == ["static", "simulation"], "progress is ordered")
    ok(r["next_stage"] == "assertion", "frontier advances")
    shutil.rmtree(tmp, ignore_errors=True)


def test_source_change_demotes_progress() -> None:
    tmp = tempfile.mkdtemp(prefix="mlog-ts-")
    os.environ["MLOG_TASK_DIR"] = tmp
    task = T.begin(source="set x 1\n")
    T.record(task, stage="static", ok=True, source="set x 1\n")
    T.record(task, stage="simulation", ok=True, source="set x 1\n")
    r = T.resume(task["task_id"], source="set x 2\n")
    ok(r["source_changed"] is True, "changed source is reported")
    ok(r["completed_stages"] == [], "old progress is not claimed for new source")
    ok(r["stale_stages"] == ["static", "simulation"], "old progress is kept as stale")
    ok(r["next_stage"] == "compilation", "resume restarts the pipeline")
    ok(r["hint"], "the hint explains why")

    # same source again: nothing changes
    r2 = T.resume(task["task_id"], source="set x 2\n")
    ok(r2["source_changed"] is False, "an unchanged source is not a change")
    shutil.rmtree(tmp, ignore_errors=True)


def test_vocabulary_and_errors() -> None:
    tmp = tempfile.mkdtemp(prefix="mlog-ts-")
    os.environ["MLOG_TASK_DIR"] = tmp
    task = T.begin(source="set x 1\n")
    try:
        T.record(task, stage="lint", ok=True)
    except ValueError:
        ok(True, "unknown stage rejected")
    else:
        ok(False, "unknown stage rejected")
    try:
        T.resume("ts-does-not-exist")
    except KeyError:
        ok(True, "resume of a missing task raises")
    else:
        ok(False, "resume of a missing task raises")
    ok(T.summary_of(None) is None, "summary_of(None) is None")
    ok(set(T.summary_of(task)) == {"task_id", "source_version", "completed_stages",
                                   "failed_stages", "stale_stages", "next_step"},
       "the envelope block stays small")
    shutil.rmtree(tmp, ignore_errors=True)


def test_evaluate_records_each_stage() -> None:
    tmp = tempfile.mkdtemp(prefix="mlog-ts-")
    os.environ["MLOG_TASK_DIR"] = tmp
    src = "set x 7\n"
    task = T.begin(source=src)
    # An injected sim record, not a real run: this test is about *which stages
    # get recorded*, and a checkout without the executor jar must be able to
    # answer that (the same reason tests/eval injects ``sim`` everywhere).
    env = E.evaluate(mlog=src, sim={"vars": {"x": "7"}},
                     expectations=[{"var": "x", "value": 7}], task=task)
    ok(env["ok"], "the pipeline passes")
    ok(env["task"]["task_id"] == task["task_id"], "envelope carries the task block")
    ok(env["task"]["completed_stages"] == ["static", "simulation", "assertion"],
       "each passing stage is recorded, not just the last")

    bad = E.evaluate(mlog="set x 7\njump 99 always\n", task=task)
    ok(not bad["ok"] and bad["failure_type"] == "static_analysis_error",
       "a static failure is classified")
    ok(bad["task"]["failed_stages"] == ["static"], "the failure lands in the record")

    # without a task the envelope still has the key, and it is null
    plain = E.evaluate(mlog="set x 1\n")
    ok("task" in plain and plain["task"] is None, "no task means an explicit null")
    shutil.rmtree(tmp, ignore_errors=True)


def test_cli() -> None:
    tmp = tempfile.mkdtemp(prefix="mlog-ts-")
    os.environ["MLOG_TASK_DIR"] = tmp      # the parent writes the record the CLI reads
    env = dict(os.environ, MLOG_TASK_DIR=tmp, PYTHONIOENCODING="utf-8")
    script = os.path.join(ROOT, "tools", "taskstate.py")

    def run(*args):
        return subprocess.run([sys.executable, "-X", "utf8", script, *args],
                              capture_output=True, text=True, encoding="utf-8",
                              env=env, timeout=120)

    task = T.begin(source="print 1\n", next_step="prove it")
    T.record(task, stage="static", ok=True, source="print 1\n")
    r = run("list")
    ok(r.returncode == 0 and json.loads(r.stdout)["count"] == 1, "list finds the task")
    r = run("show", task["task_id"])
    ok(r.returncode == 0 and json.loads(r.stdout)["next_step"] == "prove it",
       "show prints the record")
    r = run("show", "ts-missing")
    ok(r.returncode == 2, "show of a missing task exits 2")
    r = run("resume", task["task_id"])
    ok(r.returncode == 0 and json.loads(r.stdout)["next_stage"] == "simulation",
       "resume works from the CLI")
    r = run("clear", task["task_id"])
    ok(json.loads(r.stdout)["removed"] == [task["task_id"]], "clear removes it")
    ok(run("list").returncode == 0 and json.loads(run("list").stdout)["count"] == 0,
       "nothing is left")
    shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    if FAILS:
        print("------------------------------------------------")
        print("%d failure(s):" % len(FAILS))
        for f in FAILS:
            print("  - " + f)
        return 1
    print("------------------------------------------------")
    print("all run_taskstate_tests.py passed")
    print("------------------------------------------------")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
