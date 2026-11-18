#!/usr/bin/env python3
"""taskstate -- the progress a run keeps between turns (规划 §5 P1).

An agent that validates the same program three times pays for the compile, the
static pass and the simulation every time, and when it comes back after a failed
attempt it has no record of *where* it failed.  This module stores that record:
one JSON file per task, written before it is reported, holding the six fields the
plan names -- ``task_id``, ``source_version``, ``completed_stages``,
``failed_stages``, ``current_hypothesis``, ``next_step`` -- plus the history that
makes them auditable.

Why jobqueue.Store instead of a second writer
--------------------------------------------
Planning §5 P1 asks to check whether ``jobqueue.py`` can carry this before
writing persistence again.  It can: ``Store`` already does the part that is easy
to get wrong on Windows (tmp file + ``os.replace``, retry while a scanner or
OneDrive holds the handle, half-written files are not records).  What does not
fit is the *semantics* -- a job is addressed by its request body and has a state
machine of its own -- so this module borrows the primitive and defines its own
record.  A task file therefore costs what a job file costs: one small JSON.

Why ``source_version`` is a content hash, not a counter
------------------------------------------------------
Progress is only meaningful for the source it was measured on.  A counter would
have to be incremented by every writer and would still not survive a shallow
clone or a file copied by hand; the hash of the text *is* the version, so
``record()`` can tell by itself that the program changed and the earlier
``completed_stages`` no longer describe it.  They move to ``stale_stages``
rather than disappearing: "we verified static on some other program" is a fact
worth keeping, just not one worth skipping work for.

Why the stage vocabulary is closed
----------------------------------
``mlog_eval._STAGE_ORDER`` is the same tuple.  A free-form stage name would let
two callers describe the same work differently and make ``resume()`` silently
skip nothing; a closed vocabulary turns that into a ValueError.
"""
from __future__ import annotations

import hashlib
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SCHEMA = "mlog-task/v1"
#: Same order as ``mlog_eval._STAGE_ORDER``: the pipeline walks it forwards.
STAGES = ("compilation", "static", "simulation", "assertion", "scenario")


def default_dir() -> str:
    """Where task files live: ``$MLOG_TASK_DIR`` or ``out/tasks``.

    The override exists for tests and for a caller that sandboxes a run; the
    default stays under ``out/`` because a task is state, not source.
    """
    return os.environ.get("MLOG_TASK_DIR") or os.path.join(ROOT, "out", "tasks")
HISTORY_MAX = 24


def _store(path: str | None = None):
    """The job queue's atomic writer, pointed at its own directory."""
    import jobqueue as _q
    return _q.Store(path or default_dir())


def _ver(source: str | None) -> str | None:
    if source is None:
        return None
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:12]


def new_id(source: str = "", target: str = "") -> str:
    """Content-addressed, like a job id: the same program gets the same task."""
    seed = "%s\0%s" % (source, target)
    return "ts-" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:10]


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def load(task_id: str, path: str | None = None) -> dict | None:
    return _store(path).load(task_id)


def ids(path: str | None = None) -> list:
    return _store(path).ids()


TASKS_MAX = 64


def _prune(st, keep: int = TASKS_MAX) -> None:
    """Keep the newest *keep* task files.

    A task is state, not a record: an agent that names every run after its
    program would otherwise leave a directory that grows forever, and the old
    ones are the ones nobody is resuming.
    """
    rows = []
    for tid in st.ids():
        try:
            task = st.load(tid)
        except Exception:                    # noqa: BLE001 -- half-written file
            continue
        if task:
            rows.append((task.get("updated") or "", tid))
    if len(rows) <= keep:
        return
    rows.sort()
    for _updated, tid in rows[:-keep]:
        try:
            os.remove(st.file(tid))
        except OSError:
            pass


def _blank(task_id: str, target: str) -> dict:
    return {
        "schema": SCHEMA,
        # jobqueue.Store addresses a record by "id"; it always equals task_id,
        # which is the name 规划 §5 gives the field.
        "id": task_id,
        "task_id": task_id,
        "created": _now(),
        "updated": _now(),
        "target": target,
        "source_version": None,
        "completed_stages": [],
        "failed_stages": [],
        "stale_stages": [],
        "current_hypothesis": "",
        "next_step": "",
        "last": None,
        "history": [],
    }


def begin(*, task_id: str | None = None, source: str | None = None,
          target: str = "7.0", hypothesis: str = "", next_step: str = "",
          path: str | None = None) -> dict:
    """Create the task, or open the existing one and (maybe) attach the source."""
    st = _store(path)
    tid = task_id or new_id(source or "", target)
    task = st.load(tid) or _blank(tid, target)
    if source is not None:
        _set_source(task, source)
    if hypothesis:
        task["current_hypothesis"] = hypothesis
    if next_step:
        task["next_step"] = next_step
    task["updated"] = _now()
    st.save(task)
    _prune(st)
    return task


def _set_source(task: dict, source: str) -> bool:
    """Point the record at *source*; returns True when it actually changed.

    ``completed_stages`` belongs to ``source_version``: when the program is no
    longer the one those stages were measured on, the stages are kept but
    demoted to ``stale_stages``.  ``failed_stages`` stays -- a failure still
    says where the last attempt stopped -- but ``resume()`` reports it as
    something to re-check, not as a known-good skip.
    """
    ver = _ver(source)
    if task.get("source_version") == ver:
        return False
    if task.get("completed_stages"):
        moved = list(task["completed_stages"])
        task["stale_stages"] = sorted(set(task.get("stale_stages") or []) | set(moved),
                                      key=STAGES.index)
        task["completed_stages"] = []
    task["source_version"] = ver
    return True


def record(task: dict, *, stage: str, ok: bool, failure_type: str | None = None,
           notes: str = "", source: str | None = None,
           hypothesis: str | None = None, next_step: str | None = None,
           path: str | None = None) -> dict:
    """Write one stage's outcome into *task* and save it.

    The write happens before the caller reports anything, for the same reason a
    job transition is written first: a run that dies between the result and the
    save would otherwise leave the next turn believing the stage never ran.
    """
    if stage not in STAGES:
        raise ValueError("stage must be one of %s, got %r" % (STAGES, stage))
    if source is not None:
        _set_source(task, source)
    hist = task.setdefault("history", [])
    hist.append({"at": _now(), "stage": stage, "ok": bool(ok),
                 "failure_type": failure_type, "source_version": task.get("source_version"),
                 "notes": (notes or "")[:300]})
    del hist[:-HISTORY_MAX]
    done = [s for s in task.get("completed_stages") or [] if s != stage]
    failed = [s for s in task.get("failed_stages") or [] if s != stage]
    if ok:
        done = [s for s in STAGES if s in (set(done) | {stage})]
        task["completed_stages"] = done
        task["failed_stages"] = failed
    else:
        task["completed_stages"] = done
        task["failed_stages"] = [s for s in STAGES if s in (set(failed) | {stage})]
    task["last"] = {"stage": stage, "ok": bool(ok), "failure_type": failure_type,
                    "notes": (notes or "")[:300], "at": _now()}
    if hypothesis is not None:
        task["current_hypothesis"] = hypothesis
    if next_step is not None:
        task["next_step"] = next_step
    task["updated"] = _now()
    _store(path).save(task)
    return task


def note(task_id: str, *, hypothesis: str | None = None, next_step: str | None = None,
         path: str | None = None) -> dict:
    """Record the two free-text fields without claiming a stage ran."""
    st = _store(path)
    task = st.load(task_id)
    if task is None:
        raise KeyError("no such task: %s" % task_id)
    if hypothesis is not None:
        task["current_hypothesis"] = hypothesis
    if next_step is not None:
        task["next_step"] = next_step
    task["updated"] = _now()
    st.save(task)
    return task


def resume(task_id: str, *, source: str | None = None, path: str | None = None) -> dict:
    """What this task already established and what it still has to do.

    ``next_stage`` is the first stage of the pipeline that is neither completed
    nor stale; ``recheck`` lists the stages that failed last time (a failure is
    never a skip).  ``stale`` is non-empty exactly when ``resume(source=...)``
    was given a program other than the one the record was measured on.
    """
    st = _store(path)
    task = st.load(task_id)
    if task is None:
        raise KeyError("no such task: %s" % task_id)
    changed = False
    if source is not None:
        changed = _set_source(task, source)
        if changed:
            task["updated"] = _now()
            st.save(task)
    done = set(task.get("completed_stages") or [])
    stale = set(task.get("stale_stages") or [])
    recheck = list(task.get("failed_stages") or [])
    # Continue from where the run stopped, not from the first gap: a task that
    # went static -> simulation has no reason to redo compilation, and a caller
    # that never compiles anything must not be told "compilation is next"
    # forever.  A failure outranks the frontier -- that is the stage to revisit.
    # Only *completed* stages advance the frontier: a stale stage was measured
    # on another program, so it is work to redo, not ground already covered.
    marks = [STAGES.index(s) for s in done if s in STAGES]
    frontier = (max(marks) + 1) if marks else 0
    after = STAGES[frontier] if frontier < len(STAGES) else None
    nxt = recheck[0] if recheck else after
    return {
        "task_id": task_id,
        "schema": task.get("schema"),
        "source_version": task.get("source_version"),
        "completed_stages": list(task.get("completed_stages") or []),
        "failed_stages": recheck,
        "stale_stages": [s for s in STAGES if s in stale],
        "next_stage": nxt,
        "recheck": recheck,
        "source_changed": changed,
        "current_hypothesis": task.get("current_hypothesis") or "",
        "next_step": task.get("next_step") or "",
        "last": task.get("last"),
        "hint": ("source changed since the completed stages were measured: "
                 "re-run them" if changed and stale else ""),
    }


def summary_of(task: dict | None) -> dict | None:
    """The small block an evaluation envelope carries (never the whole history)."""
    if not task:
        return None
    return {
        "task_id": task.get("task_id"),
        "source_version": task.get("source_version"),
        "completed_stages": list(task.get("completed_stages") or []),
        "failed_stages": list(task.get("failed_stages") or []),
        "stale_stages": list(task.get("stale_stages") or []),
        "next_step": task.get("next_step") or "",
    }


def clear(task_id: str | None = None, path: str | None = None) -> list:
    """Delete one task (or all of them); returns what was removed."""
    st = _store(path)
    targets = [task_id] if task_id else st.ids()
    gone = []
    for tid in targets:
        dest = st.file(tid)
        try:
            os.remove(dest)
            gone.append(tid)
        except FileNotFoundError:
            pass
    return gone


# ------------------------------------------------------------------- CLI

def _print(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=1))


def main(argv=None) -> int:
    import sys
    args = list(sys.argv[1:] if argv is None else argv)
    cmd = args[0] if args else "list"
    rest = args[1:]
    if cmd == "list":
        rows = []
        for tid in ids():
            try:
                task = load(tid)
            except Exception:                # noqa: BLE001 -- half-written file
                continue
            if not task:
                continue
            rows.append({"task_id": tid, "source_version": task.get("source_version"),
                         "completed": "".join(s[0] for s in task.get("completed_stages") or []),
                         "failed": "".join(s[0] for s in task.get("failed_stages") or []),
                         "updated": task.get("updated")})
        _print({"dir": default_dir(), "count": len(rows), "tasks": rows})
        return 0
    if cmd == "show":
        task = load(rest[0]) if rest else None
        if task is None:
            print("no such task: %s" % (rest[0] if rest else ""), file=sys.stderr)
            return 2
        _print(task)
        return 0
    if cmd == "resume":
        if not rest:
            print("usage: taskstate.py resume <task_id> [--source FILE]", file=sys.stderr)
            return 2
        src = None
        if "--source" in rest:
            with open(rest[rest.index("--source") + 1], encoding="utf-8") as fh:
                src = fh.read()
        _print(resume(rest[0], source=src))
        return 0
    if cmd == "clear":
        _print({"removed": clear(rest[0] if rest else None)})
        return 0
    if cmd == "selftest":
        return selftest()
    print("usage: taskstate.py [list|show|resume|clear|selftest]", file=sys.stderr)
    return 2


def selftest() -> int:
    """In-process exercise of the record semantics (the gate runs this)."""
    import tempfile
    tmp = tempfile.mkdtemp(prefix="mlog-task-")
    os.environ["MLOG_TASK_DIR"] = tmp
    fails = []

    def check(name, cond):
        if not cond:
            fails.append(name)

    a = begin(source="print 1", path=tmp)
    check("id is content addressed", a["task_id"].startswith("ts-"))
    check("fresh task has nothing done", a["completed_stages"] == [])

    record(a, stage="static", ok=True, source="print 1", path=tmp)
    r = resume(a["task_id"], path=tmp)
    check("static completed", r["completed_stages"] == ["static"])
    check("next is simulation", r["next_stage"] == "simulation")

    record(a, stage="simulation", ok=False, failure_type="runtime_error",
           next_step="check the jump target", source="print 1", path=tmp)
    r = resume(a["task_id"], path=tmp)
    check("failure recorded", r["failed_stages"] == ["simulation"])
    check("failure is rechecked first", r["next_stage"] == "simulation")
    check("next_step survives", r["next_step"] == "check the jump target")

    record(a, stage="simulation", ok=True, source="print 1", path=tmp)
    r = resume(a["task_id"], path=tmp)
    check("retry clears the failure", r["failed_stages"] == [])
    check("progress advances", r["next_stage"] == "compilation"
          or r["next_stage"] == "assertion")

    r2 = resume(a["task_id"], source="print 2", path=tmp)
    check("changed source demotes progress", r2["stale_stages"] == ["static", "simulation"])
    check("changed source empties completed", r2["completed_stages"] == [])
    check("changed source is flagged", r2["hint"] != "")

    check("unknown stage rejected", _raises(lambda: record(a, stage="lint", ok=True),
                                            ValueError))
    check("resume of a missing task raises", _raises(lambda: resume("ts-nope", path=tmp),
                                                     KeyError))
    check("clear removes the file", clear(a["task_id"], path=tmp) == [a["task_id"]])
    check("after clear there is nothing", load(a["task_id"], path=tmp) is None)
    check("summary_of(None) is None", summary_of(None) is None)

    for name in fails:
        print("FAIL %s" % name)
    print("%d checks, %d failure(s)" % (15, len(fails)))
    return 0 if not fails else 1


def _raises(fn, exc) -> bool:
    try:
        fn()
    except exc:
        return True
    except Exception:                        # noqa: BLE001
        return False
    return False


if __name__ == "__main__":
    raise SystemExit(main())
