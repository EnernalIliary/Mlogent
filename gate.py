#!/usr/bin/env python3
"""Run every gate this repo has, from one command.

Why this exists
---------------
The gate list used to live in 00-HANDOVER.md and in whoever remembered it, so a
round ended with five or six hand-typed commands.  Several of them got mangled on
the way -- this shell is Windows PowerShell 5.1, where "&&" is a parse error and
nested quotes inside python -c are a coin flip.  A gate that is not one command
does not reliably get run, and two of the checks below are the ones that quietly
stop being run first:

* mirror -- tests/run_tests.py imports the analyzers from the
  mindustry-blueprint/tools COPY, so an unsynced source tree means a green suite
  over stale code.  tests/run_tests.py refuses to start in that state now; this
  step checks it first so the failure is one line, not a traceback.
* kb -- the local knowledge base is a snapshot.  If kb.sqlite3 is older than
  docs/断言表.md or any tools/*.py, "kb.py search" answers from the previous
  round and nobody notices.  This step compares mtimes; it does not rebuild
  unless asked (--kb-build), because a rebuild needs the offline model cache.

Usage
-----
    python gate.py                # walk the cheap gates (~3 s)
    python gate.py --full         # + selftest / probes / corpus / coverage (~42 s, needs a JRE);
                                  #   those four are independent, so they run concurrently --
                                  #   --serial brings back the old one-at-a-time order
    python gate.py --kb-build     # rebuild the KB when it is stale
    python gate.py --only test    # run steps whose name contains "test"
    python gate.py -v             # stream child output instead of capturing it

Exit status: 0 when every step PASSes (WARN allowed unless --strict), 1 otherwise.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable

# The four --full steps are independent of each other and of the cheap gates:
# each drives its own JVM (mlogsim/mlog.py start one per run, and a host-less
# run binds no 6567 port), each writes a different file under out/_bench, and
# none of them reads another one's output.  Run them together: the full gate
# goes from ~75 s to ~42 s, and the long pole is probes (38 s) not the sum.
# --serial restores the sequential order; --stream implies it (interleaved
# child output would be unreadable).
PARALLEL = ("selftest", "probes", "corpus", "coverage")


def child_env() -> dict:
    e = dict(os.environ)
    e["PYTHONIOENCODING"] = "utf-8"
    e["PYTHONUTF8"] = "1"
    return e


def run_child(argv: list[str], timeout: int = 3600) -> tuple[int, str, float]:
    t0 = time.time()
    cp = subprocess.run([PY, *argv], cwd=str(ROOT), env=child_env(),
                        capture_output=True, text=True, encoding="utf-8",
                        errors="replace", timeout=timeout)
    out = (cp.stdout or "") + (cp.stderr or "")
    return cp.returncode, out, time.time() - t0


def run_step(name: str, argv: list[str], stream: bool = False) -> tuple[str, str, float, str, str]:
    """Run one child and turn its exit code into a gate row."""
    t0 = time.time()
    if stream:
        print("--> " + name + ": " + " ".join(argv), flush=True)
        rc = subprocess.run([PY, *argv], cwd=str(ROOT), env=child_env()).returncode
        out, secs = "", time.time() - t0
    else:
        rc, out, secs = run_child(argv)
    if rc == 3:
        # the child reports "nothing could run" as 3 (no JRE, no jars)
        note = [ln for ln in out.splitlines() if ln.startswith("SKIP")]
        return (name, "SKIP", secs, "", note[-1] if note else "child skipped")
    return (name, "PASS" if rc == 0 else "FAIL", secs, out, "")


def run_parallel(steps: list[tuple[str, list[str]]]) -> list[tuple[str, str, float, str, str]]:
    """Run independent steps at once, but return the rows in list order."""
    from concurrent.futures import ThreadPoolExecutor            # noqa: PLC0415

    with ThreadPoolExecutor(max_workers=len(steps)) as pool:
        futures = [pool.submit(run_step, name, argv) for name, argv in steps]
        return [f.result() for f in futures]


def tail(text: str, n: int = 12) -> str:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    return "\n".join("    " + ln for ln in lines[-n:])


# --------------------------------------------------------------------------- #
# KB freshness: reuse kb.py's own source list instead of guessing at globs.
# --------------------------------------------------------------------------- #

def kb_sources() -> tuple[Path, list[Path]]:
    sys.path.insert(0, str(ROOT / "tools"))
    import kb as K                                            # noqa: PLC0415

    src: list[Path] = []
    for rel in K.DOC_FILES:
        p = ROOT / rel
        if p.is_file():
            src.append(p)
    for pat in list(K.CODE_GLOBS) + list(K.DOC_GLOBS):
        src += [p for p in ROOT.glob(pat) if p.is_file()]
    return K.DB_PATH, src


def kb_status() -> tuple[str, str, Path | None]:
    """Return (PASS or WARN, note, newest source file)."""
    try:
        db, src = kb_sources()
    except Exception as exc:                                  # noqa: BLE001
        return "SKIP", "cannot introspect kb.py: " + type(exc).__name__ + ": " + str(exc), None
    rel_db = db.relative_to(ROOT) if db.is_absolute() else db
    if not db.is_file():
        return "WARN", "no " + str(rel_db) + " yet -- run: python tools/kb.py build", None
    if not src:
        return "PASS", str(rel_db) + " (no source list)", None
    newest = max(src, key=lambda p: p.stat().st_mtime)
    if newest.stat().st_mtime > db.stat().st_mtime + 1:
        return ("WARN", "stale: " + str(newest.relative_to(ROOT)) + " is newer than " + str(rel_db),
                newest)
    return "PASS", str(rel_db) + " covers " + str(len(src)) + " source file(s)", None


# --------------------------------------------------------------------------- #
# Steps
# --------------------------------------------------------------------------- #

def build_steps(full: bool, only: str | None) -> list[tuple[str, list[str] | None, str]]:
    """(name, argv or None for special steps, skip note)."""
    steps: list[tuple[str, list[str] | None, str]] = [
        ("mirror", ["tools/sync_mlogagent.py", "--mirror", "all", "--check"], ""),
        ("tests", ["tests/run_tests.py"], ""),
        ("lint", ["tools/rule_capture.py", "lint"], ""),
        # the checkers' own invariant: a malformed statement must still be
        # caught after junk tokens are appended, i.e. no check may parse a
        # statement with an anchored regex and fail open when the line grows
        # (tests/shapes/run_shapes.py).
        ("shapes", ["tests/shapes/run_shapes.py"], ""),
    ]
    global_skill = (Path(os.environ.get("DSH_HOME") or (Path.home() / ".dsh"))
                    / "skills" / "mlog-agentskill")
    if global_skill.is_dir():
        steps.append(("global", ["tools/sync_mlogagent.py", "--global", "--check"], ""))
    else:
        steps.append(("global", None, "not installed at " + str(global_skill)))
    if full:
        steps.append(("selftest", ["tools/mlog.py", "selftest"], ""))
        # runtime truth: probes need a JRE and the versioned jars under out/,
        # which are not in git, so a fresh clone SKIPs rather than fails.
        steps.append(("probes", ["tests/probes/run_probes.py"], ""))
        # A real-corpus smoke test: 400 programs sampled out of the 44k-program
        # Anon pack (see out/takeover-20261024/24-anon-corpus.md).  It lives
        # outside git, so a machine without it SKIPs.  What it asserts is that
        # the analyzers survive real code at all -- count drift is expected when
        # a rule changes on purpose, a crash is not.
        corpus = Path(os.environ.get("MLOG_CORPUS") or (Path.home() / "mlog-corpus" / "anon-corpus"))
        if corpus.is_dir():
            steps.append(("corpus", ["tools/corpus/check_corpus.py",
                                     "--corpus", str(corpus), "--procs", "_procs",
                                     "--stride", "37", "--limit", "400", "--jobs", "8",
                                     "--fail-on-errors",
                                     "--json", "out/_bench/_gate_corpus.json"], ""))
            # Instruction coverage cannot assert an absolute number (it depends on
            # the sample), but it can assert that the statements *this* sample
            # never uses are still the ones a human signed off on: adding a row to
            # tools/instr_semantics.json, or losing one from the sample, changes
            # the set and fails here until the baseline is re-recorded on purpose
            # (tests/corpus-coverage-baseline.json, written by
            # instr_coverage.py --write-baseline at the same --limit).
            steps.append(("coverage", ["tools/corpus/instr_coverage.py",
                                       "--src", str(corpus / "_procs"), "--limit", "400",
                                       "--baseline", "tests/corpus-coverage-baseline.json",
                                       "--json", "out/_bench/_gate_coverage.json",
                                       "--md", "out/_bench/_gate_coverage.md"], ""))
        else:
            steps.append(("corpus", None, "no corpus at " + str(corpus) + " (MLOG_CORPUS overrides)"))
            steps.append(("coverage", None, "no corpus at " + str(corpus) + " (MLOG_CORPUS overrides)"))
    steps.append(("kb", None, ""))                # handled inline, see main()
    if only:
        steps = [s for s in steps if only.lower() in s[0].lower()]
    return steps


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--full", action="store_true",
                    help="also run mlog.py selftest")
    ap.add_argument("--kb-build", action="store_true",
                    help="rebuild the KB when it is stale instead of warning")
    ap.add_argument("--only", help="run steps whose name contains this substring")
    ap.add_argument("--strict", action="store_true", help="treat WARN as failure")
    ap.add_argument("-v", "--stream", action="store_true",
                    help="let child output through instead of capturing it")
    ap.add_argument("--serial", action="store_true",
                    help="do not run the independent --full steps concurrently")
    args = ap.parse_args()

    results: list[tuple[str, str, float, str, str]] = []
    t_all = time.time()
    steps = build_steps(args.full, args.only)
    batch = [] if (args.serial or args.stream) else [s for s in steps
                                                    if s[0] in PARALLEL and s[1]]
    batch_done = False
    for name, argv, skip_note in steps:
        if name == "kb":
            t0 = time.time()
            status, note, _newest = kb_status()
            if status == "WARN" and args.kb_build:
                rc, out, _secs = run_child(["tools/kb.py", "build"])
                if rc != 0:
                    results.append((name, "FAIL", time.time() - t0, out, note))
                    continue
                status, note, _ = kb_status()
                note = "rebuilt; " + note
            results.append((name, status, time.time() - t0, "", note))
            continue
        if argv is None:
            results.append((name, "SKIP", 0.0, "", skip_note))
            continue
        if batch and name in PARALLEL:
            if not batch_done:                      # first of the batch: run them all
                results.extend(run_parallel([(n, a) for n, a, _s in batch]))
                batch_done = True
            continue
        results.append(run_step(name, argv, args.stream))

    width = max((len(r[0]) for r in results), default=5)
    print("gate".ljust(width) + "  status  secs  note")
    print("-" * (width + 40))
    for name, status, secs, _out, note in results:
        print(name.ljust(width) + "  " + status.ljust(6) + f"  {secs:5.1f}  " + note)
    print()
    for name, status, _secs, out, _note in results:
        if status == "FAIL" and out.strip():
            print("--- " + name + " (last lines) ---")
            print(tail(out))
            print()

    fails = [r[0] for r in results if r[1] == "FAIL"]
    warns = [r[0] for r in results if r[1] == "WARN"]
    skips = [r[0] for r in results if r[1] == "SKIP"]
    ok = len(results) - len(fails) - len(warns) - len(skips)
    summary = str(ok) + "/" + str(len(results)) + " passed"
    if warns:
        summary += ", " + str(len(warns)) + " warn (" + ", ".join(warns) + ")"
    if skips:
        summary += ", " + str(len(skips)) + " skipped"
    summary += f" in {time.time() - t_all:.1f}s"
    if fails:
        summary += " -- FAILED: " + ", ".join(fails)
    print(summary)
    return 1 if fails or (warns and args.strict) else 0


if __name__ == "__main__":
    raise SystemExit(main())
