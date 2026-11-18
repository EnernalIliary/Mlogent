#!/usr/bin/env python3
"""The Agent Onboarding Benchmark: tasks, prompts, runs, and the score.

Why this exists (实施记录 §七): the only way to know whether a stranger model can use
this toolchain is to hand it a task and *measure*.  Everything here is built so
that the measurement is honest:

* a **task** is a JSON file with a prompt and an *acceptance* that this tool can
  check itself -- never "the agent said it worked";
* a **run** is one recorded attempt: which task, which model/host, how many tool
  calls, tokens, repairs, whether the first try passed;
* **scores** are computed from runs, per 规划's table (first-pass success, task
  success rate, tokens per successful task, ...).

The prompt deliberately carries no technique hints: the point is whether the
documentation and tool descriptions are enough (Tool Discovery Rate).

CLI
    python tools/benchmark.py list
    python tools/benchmark.py prompt unit-control-move
    python tools/benchmark.py verify unit-control-move --file out/answer.mlog
    python tools/benchmark.py record --task ... --success yes ...
    python tools/benchmark.py score [--model X] [--host Y]
    python tools/benchmark.py selftest

Runs are appended to ``bench/results/runs.jsonl`` ($MLOG_BENCH_DIR overrides);
nothing is committed, only aggregated by ``score``.
"""
from __future__ import annotations

import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TASKS = os.path.join(ROOT, "bench", "tasks")
SCHEMA = "mlog-bench/v1"

#: 实施记录 §七 的指标，顺序即输出顺序。
METRICS = (
    "first_pass", "success", "tool_calls", "tool_accuracy", "repairs",
    "interventions", "tokens_in", "tokens_out", "seconds",
)


def default_dir() -> str:
    # bench/results, not out/: a benchmark number is only worth quoting if the
    # row that produced it stays in version control next to the tasks.
    return os.environ.get("MLOG_BENCH_DIR") or os.path.join(ROOT, "bench", "results")


# --------------------------------------------------------------------------
# tasks
# --------------------------------------------------------------------------

def tasks() -> list[dict]:
    """Every task file, sorted by id (so `list` is stable)."""
    out = []
    for path in sorted(glob.glob(os.path.join(TASKS, "*.json"))):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                task = json.load(fh)
        except (OSError, ValueError) as exc:
            raise SystemExit("%s: %s" % (path, exc))
        task["_path"] = path
        out.append(task)
    return out


def find(task_id: str) -> dict:
    for task in tasks():
        if task.get("id") == task_id:
            return task
    raise SystemExit("no such task: %s (try `list`)" % task_id)


def prompt(task: dict) -> str:
    """The text handed to a cold agent: goal + how success is judged, nothing more."""
    lines = [task["prompt"].strip(), ""]
    lines.append("Acceptance is checked mechanically; you do not grade yourself.")
    if task.get("tools_hint"):
        lines.append("You may use: " + ", ".join(task["tools_hint"]))
    return "\n".join(lines)


# --------------------------------------------------------------------------
# verification
# --------------------------------------------------------------------------

def verify(task: dict, *, file: str | None = None) -> dict:
    """Run the task's own acceptance against a candidate answer.

    Two rigs, one judge: ``validate`` runs the program on a bare processor,
    ``scene`` lays a small rig (units / buildings from the task file) down first
    so the program has something real to talk to, and ``static`` never runs
    anything -- it only asks the analyzer, so it works without a jar.  Checks read program variables,
    the text buffer, or the **trace** -- unit positions come from the executor's
    own per-tick row, not from a number the program wrote about itself.
    """
    accept = task.get("acceptance") or {}
    kind = accept.get("kind")
    if kind not in ("validate", "scene", "static"):
        raise SystemExit("task %s: unknown acceptance kind %r" % (task["id"], kind))
    if not file:
        raise SystemExit("task %s needs --file" % task["id"])
    with open(file, encoding="utf-8-sig") as fh:      # BOM-tolerant: agents write
        mlog = fh.read()                              # files with every tool

    if kind == "static":
        # 静态任务不碰执行器：干净 checkout 里没有 jar 也能判，CI 因此能覆盖到
        # 这个模块。判据就是仓库自己的分析器，和 Agent 手跑 mlog_check 同一条路。
        findings = [f for f in mlog_eval_static(mlog) if f["sev"] in ("ERR", "SUSPECT")]
        return {"ok": not findings, "task": task["id"], "kind": kind,
                "failures": [{"kind": "finding", "sev": f["sev"], "line": f["line"],
                              "message": f["message"]} for f in findings],
                "observed": {"findings": len(findings)}}

    limits = accept.get("limits") or {}
    ticks = int(limits.get("ticks") or 60)
    checks = list(accept.get("checks") or [])
    if accept.get("expect"):
        checks = list(accept["expect"]) + checks
    wanted = [c["history"]["var"] for c in checks if c.get("history")]
    need_trace = any("history" in c or "executed" in c for c in checks)
    rec, err = _run(mlog, kind=kind, rig=accept.get("rig"), ticks=ticks,
                    itrace_vars=wanted, itrace=need_trace)
    if err:
        return {"ok": False, "task": task["id"], "kind": kind,
                "failure_type": mlog_eval_classify(err), "error": str(err)}
    failed, seen = [], _context(rec)
    for check in checks:
        if "text_contains" in check:
            ok = check["text_contains"] in (rec.get("text") or "")
            if not ok:
                failed.append({"check": check, "actual": rec.get("text") or ""})
            continue
        if "executed" in check:
            bad = _executed_failure(seen.get("executed") or [], check["executed"])
            if bad:
                failed.append({"check": check, "executed": bad})
            continue
        if "history" in check:
            bad = _history_failure(seen.get("history") or {}, check["history"])
            if bad:
                failed.append({"check": check, "history": bad})
            continue
        name = check.get("name")
        if not _matches(seen.get(name), check.get("op", "eq"), check.get("value")):
            failed.append({"check": check, "actual": seen.get(name)})
    return {"ok": not failed, "task": task["id"], "kind": kind,
            "failures": failed,
            "observed": {k: seen.get(k) for k in
                         ("vars", "text", "ux_max", "ticks") if k in seen}}


def _executed_failure(executed: list, spec: dict) -> str | None:
    """A check on what the program *did*, not what it ended up holding.

    "The value must be computed, not typed" cannot be judged from the final
    state: `set r 35` and `op add t 3 4 / op mul r t 5` both end at 35.  The
    executor's per-instruction trace carries the source line behind each step,
    so the judge can require that arithmetic actually ran.  This is a floor, not
    a proof -- a determined liar can execute a real `op add` and then overwrite
    the result -- but it makes the cheap cheat fail.
    """
    patterns = list(spec.get("any_of") or [])
    if not patterns:
        return None
    for line in executed:
        for pat in patterns:
            if pat in line:
                return None
    seen = ", ".join(repr(x) for x in executed[:6]) or "nothing"
    return "no %s executed (first steps: %s)" % ("/".join(patterns), seen)


def _history_failure(history: dict, spec: dict) -> str | None:
    """A check on what the variable *did* while the program ran.

    Exists because a final state cannot tell a computation from a constant: the
    task "sum 1..5 into s" is satisfied by `set s 15` under a pure end-state
    check.  Requiring the variable to pass through intermediate values does not
    make cheating impossible (a liar can echo the intermediates too), it makes
    the cheap cheat fail.
    """
    var = spec.get("var")
    values = history.get(var) or []
    if not values:
        return "%s never appeared in the trace" % var
    nums = []
    for v in values:
        try:
            nums.append(float(v))
        except (TypeError, ValueError):
            nums.append(v)
    if "distinct_min" in spec and len(set(nums)) < int(spec["distinct_min"]):
        return "%s only ever held %d distinct value(s) %r" % (
            var, len(set(nums)), sorted(set(nums), key=str)[:6])
    if "contains" in spec and spec["contains"] not in nums:
        return "%s never held %r (saw %r)" % (var, spec["contains"], nums[:8])
    if "last" in spec and (not nums or nums[-1] != spec["last"]):
        return "%s ended at %r, wanted %r" % (var, nums[-1] if nums else None, spec["last"])
    return None


def mlog_eval_classify(exc) -> str:
    import mlog_eval as E
    return E.classify(exc)


def _matches(actual, op: str, want) -> bool:
    import mlog_eval as E
    return E._matches(actual, op, want)


def mlog_eval_static(mlog: str) -> list:
    """Findings from the repo's own static analyzer, via `mlog_eval`."""
    import mlog_eval as _ev
    return _ev._static_findings(mlog)


def _context(rec: dict) -> dict:
    """What checks may read: program variables, text, trace, and history."""
    vars_ = dict(rec.get("vars") or {})
    seen = {"vars": vars_, "text": rec.get("text") or "", "ticks": rec.get("ticks"),
            "history": rec.get("history") or {}, "executed": rec.get("executed") or []}
    trace = rec.get("trace") or []
    xs = [row.get("ux") for row in trace if row.get("ux") is not None]
    ys = [row.get("uy") for row in trace if row.get("uy") is not None]
    if xs:
        seen["ux_max"], seen["ux_min"] = max(xs), min(xs)
    if ys:
        seen["uy_max"], seen["uy_min"] = max(ys), min(ys)
    seen.update(vars_)
    return seen


def _run(mlog: str, *, kind: str, rig: dict | None, ticks: int, itrace_vars=(),
         itrace: bool = False):
    """(record, error) from a **fresh executor process**.

    One JVM per answer, driven through the CLI: the in-process path re-places a
    processor on a warm server, and its instruction throughput then depends on
    whatever the previous run left behind -- measured here as non-monotonic (the
    same program finished at 30 ticks and stalled at 120).  A cold process is
    slower but repeatable, and a benchmark that answers differently each run
    measures nothing.

    ``ticks`` is the budget.  It is *ticks*, not instructions: ``--steps`` is
    not monotonic on the executor (200 steps completed less than 30), while
    ``--ticks`` is, so the tick budget is the only currency that can be raised
    until a correct answer passes without also passing a wrong one.
    """
    work = os.path.join(default_dir(), "work")
    os.makedirs(work, exist_ok=True)
    src = os.path.join(work, "answer.mlog")
    with open(src, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(mlog)
    cmd = [sys.executable, os.path.join(HERE, "mlogsim.py"), src,
           "--ticks", str(ticks), "--json"]
    trace_path = None
    if itrace or itrace_vars:
        trace_path = os.path.join(work, "itrace.tsv")
        cmd += ["--itrace", trace_path]
        for name in itrace_vars:
            cmd += ["--itrace-var", name]
    if kind == "scene":
        sc = {"name": "bench", "version": 1,
              "world": dict((rig or {}).get("world") or {"size": 64}),
              "buildings": list((rig or {}).get("buildings") or []),
              "units": list((rig or {}).get("units") or [])}
        path = os.path.join(work, "rig.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(sc, fh, ensure_ascii=False, indent=1)
        cmd += ["--scene", path]
    try:
        out = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             timeout=180, cwd=ROOT)
    except (OSError, subprocess.SubprocessError) as exc:
        return None, exc
    text = out.stdout.decode("utf-8", "replace")
    match = re.search(r"(\[.*\]|\{.*\})\s*$", text, re.S)
    if not match:
        err = out.stderr.decode("utf-8", "replace").strip() or text.strip()
        return None, RuntimeError(err[-800:] or "executor produced no JSON")
    try:
        data = json.loads(match.group(1))
    except ValueError as exc:
        return None, exc
    rec = data[0] if isinstance(data, list) and data else data
    if not isinstance(rec, dict):
        return None, RuntimeError("unexpected executor answer")
    if rec.get("error"):
        return None, RuntimeError(str(rec["error"]))
    if trace_path:
        rec["history"], rec["executed"] = _read_itrace(trace_path)
    return rec, None


def _read_itrace(path: str):
    """(`{var: [value, ...]}`, `[source line, ...]`) from the executor trace.

    Rows are `tick / pc / r=1;s=3; / source`.  A variable the program has not
    written yet reads `?` there; those rows are skipped rather than recorded, so
    a history starts at the instruction that actually defined the name.  The
    source column is what makes "computed, not typed" checkable: `set r 35`
    executes one `set`, `(3+4)*5` executes `op add` and `op mul`.
    """
    history: dict[str, list] = {}
    executed: list = []
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            next(fh, None)                    # header: tick pc vars source
            for line in fh:
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 4:
                    continue
                src = parts[3].strip()
                if src and (not executed or executed[-1] != src):
                    executed.append(src)
                for chunk in parts[2].split(";"):
                    if "=" not in chunk:
                        continue
                    name, value = chunk.split("=", 1)
                    if value in ("?", "", "<obj>"):
                        continue
                    history.setdefault(name, []).append(value)
    except OSError:
        return {}, []
    return history, executed


def _parse_itrace(path: str) -> dict:
    """Backwards-compatible wrapper: just the per-variable history."""
    return _read_itrace(path)[0]


# --------------------------------------------------------------------------
# runs and scores
# --------------------------------------------------------------------------

def _runs_path() -> str:
    return os.path.join(default_dir(), "runs.jsonl")


def record_run(**row) -> dict:
    """Append one attempt.  Returns what was stored."""
    missing = [k for k in ("task", "success") if k not in row]
    if missing:
        raise SystemExit("record: missing " + ", ".join(missing))
    row = {"schema": SCHEMA,
           "task": row["task"],
           "success": _flag(row["success"]),
           "first_pass": _flag(row.get("first_pass", row["success"])),
           "model": row.get("model") or "",
           "host": row.get("host") or "",
           "lang": row.get("lang") or "",          # mlog | mindcode
           "tool_calls": _int(row.get("tool_calls")),
           "tool_accuracy": _float(row.get("tool_accuracy")),
           "repairs": _int(row.get("repairs")),
           "interventions": _int(row.get("interventions")),
           "tokens_in": _int(row.get("tokens_in")),
           "tokens_out": _int(row.get("tokens_out")),
           "seconds": _float(row.get("seconds")),
           "notes": row.get("notes") or ""}
    os.makedirs(default_dir(), exist_ok=True)
    with open(_runs_path(), "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def load_runs(*, model: str | None = None, host: str | None = None) -> list[dict]:
    path = _runs_path()
    if not os.path.isfile(path):
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if model and row.get("model") != model:
                continue
            if host and row.get("host") != host:
                continue
            rows.append(row)
    return rows


def score(runs: list[dict]) -> dict:
    """实施记录 §七 的汇总指标；空集合返回零而不是除零。"""
    if not runs:
        return {"runs": 0, "tasks": 0, "success_rate": 0.0, "first_pass_rate": 0.0,
                "tokens_per_success": None, "token_efficiency": None,
                "mean_repairs": 0.0, "mean_tool_calls": 0.0,
                "mean_tool_accuracy": None, "interventions": 0}
    wins = [r for r in runs if r.get("success")]
    tokens = sum(r.get("tokens_in", 0) + r.get("tokens_out", 0) for r in runs)
    accuracies = [r["tool_accuracy"] for r in runs
                  if isinstance(r.get("tool_accuracy"), float)]
    return {
        "runs": len(runs),
        "tasks": len({r.get("task") for r in runs}),
        "success_rate": round(len(wins) / len(runs), 4),
        "first_pass_rate": round(sum(1 for r in runs if r.get("first_pass")) / len(runs), 4),
        "tokens_per_success": round(tokens / len(wins), 1) if wins else None,
        "token_efficiency": round(len(wins) / tokens, 6) if tokens else None,
        "mean_repairs": round(sum(r.get("repairs", 0) for r in runs) / len(runs), 2),
        "mean_tool_calls": round(sum(r.get("tool_calls", 0) for r in runs) / len(runs), 2),
        "mean_tool_accuracy": round(sum(accuracies) / len(accuracies), 4) if accuracies else None,
        "interventions": sum(r.get("interventions", 0) for r in runs),
    }


def by_model(runs: list[dict]) -> dict:
    groups: dict[str, list] = {}
    for row in runs:
        groups.setdefault(row.get("model") or "(unknown)", []).append(row)
    return {name: score(rows) for name, rows in sorted(groups.items())}


def _flag(value) -> bool:
    text = str(value).strip().lower()
    return text in ("1", "true", "yes", "y", "ok", "pass")


def _int(value) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def _float(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------
# selftest
# --------------------------------------------------------------------------

def _selftest() -> int:
    import shutil
    import tempfile
    fails: list[str] = []

    def ok(cond, what):
        if not cond:
            fails.append(what)
            print("FAIL " + what)

    saved = os.environ.get("MLOG_BENCH_DIR")
    tmp = tempfile.mkdtemp(prefix="mlog-bench-")
    os.environ["MLOG_BENCH_DIR"] = tmp
    try:
        known = tasks()
        ok(len(known) >= 6, "at least six tasks (%d)" % len(known))
        ids = [t["id"] for t in known]
        ok(len(ids) == len(set(ids)), "task ids are unique")
        for task in known:
            ok(bool(task.get("prompt")), "%s has a prompt" % task["id"])
            kind = (task.get("acceptance") or {}).get("kind")
            ok(kind in ("validate", "scene", "static"),
               "%s has a machine-checkable acceptance" % task["id"])
            # a static task is judged by mlog_check being clean: there is no
            # list of checks to be non-empty, so the rule is "not a validate
            # task without checks".
            ok(kind == "static"
               or bool((task.get("acceptance") or {}).get("checks")
                       or (task.get("acceptance") or {}).get("expect")),
               "%s actually checks something" % task["id"])
            ok(task["id"] not in task["prompt"],
               "%s: the prompt does not leak the id" % task["id"])

        ok(load_runs() == [], "no runs yet")
        ok(score([])["success_rate"] == 0.0, "an empty score is zero, not a crash")

        record_run(task="t1", success="yes", model="m", tokens_in=100, tokens_out=20,
                   tool_calls=3, repairs=0, first_pass="yes")
        record_run(task="t2", success="no", model="m", tokens_in=50, tokens_out=10,
                   tool_calls=7, repairs=2, first_pass="no", interventions=1)
        rows = load_runs()
        ok(len(rows) == 2, "two runs recorded")
        one = score(rows)
        ok(one["runs"] == 2 and one["tasks"] == 2, "runs and distinct tasks counted")
        ok(one["success_rate"] == 0.5, "success rate")
        ok(one["first_pass_rate"] == 0.5, "first-pass rate")
        ok(one["tokens_per_success"] == 180.0, "tokens per success = 180, got %s"
           % one["tokens_per_success"])
        ok(one["mean_repairs"] == 1.0, "mean repairs")
        ok(one["interventions"] == 1, "interventions summed")
        ok(by_model(rows)["m"]["runs"] == 2, "grouped by model")
        ok(load_runs(model="nope") == [], "model filter")
        ok(load_runs(model="m")[0]["success"] is True, "flags are parsed, not stored raw")
        ok(score([record_run(task="t3", success="yes", tokens_in=0, tokens_out=0)])
           ["tokens_per_success"] == 0.0, "zero tokens does not divide by zero")
    finally:
        if saved is None:
            os.environ.pop("MLOG_BENCH_DIR", None)
        else:
            os.environ["MLOG_BENCH_DIR"] = saved
        shutil.rmtree(tmp, ignore_errors=True)

    if fails:
        print("-" * 48)
        print("%d failure(s)" % len(fails))
        return 1
    print("benchmark selftest: ok")
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    cmd = (argv[1] if len(argv) > 1 else "list").lower()
    args = argv[2:]

    def opt(name, default=None):
        if name in args:
            index = args.index(name)
            if index + 1 < len(args):
                return args[index + 1]
        return default

    if cmd == "list":
        print("%-26s %-10s %-14s %s" % ("id", "lang", "acceptance", "title"))
        for task in tasks():
            print("%-26s %-10s %-14s %s" % (task["id"], task.get("lang", ""),
                                            (task.get("acceptance") or {}).get("kind", ""),
                                            task.get("title", "")))
        print("\n%d task(s)" % len(tasks()))
        return 0
    if cmd == "prompt":
        print(prompt(find(args[0])))
        return 0
    if cmd == "verify":
        out = verify(find(args[0]), file=opt("--file"))
        print(json.dumps(out, ensure_ascii=False, indent=1)[:4000])
        return 0 if out["ok"] else 1
    if cmd == "record":
        row = record_run(task=opt("--task"), success=opt("--success", "no"),
                         first_pass=opt("--first-pass"), model=opt("--model"),
                         host=opt("--host"), lang=opt("--lang"),
                         tool_calls=opt("--tool-calls"), tool_accuracy=opt("--tool-accuracy"),
                         repairs=opt("--repairs"), interventions=opt("--interventions"),
                         tokens_in=opt("--tokens-in"), tokens_out=opt("--tokens-out"),
                         seconds=opt("--seconds"), notes=opt("--notes"))
        print(json.dumps(row, ensure_ascii=False))
        return 0
    if cmd == "score":
        runs = load_runs(model=opt("--model"), host=opt("--host"))
        print(json.dumps(score(runs), ensure_ascii=False, indent=1))
        if runs:
            print("\nby model:")
            print(json.dumps(by_model(runs), ensure_ascii=False, indent=1))
        return 0
    if cmd == "selftest":
        return _selftest()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
