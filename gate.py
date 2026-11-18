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
    python gate.py                # walk the cheap gates (~5 s, measured 2026-10-28)
    python gate.py --full         # + selftest / probes / corpus / coverage (~25 s on this
                                  #   machine, measured 2026-10-28; needs a JRE); those four
                                  #   are independent, so they run concurrently and the long
                                  #   pole is selftest (15.8 s) and probes (15.0 s), not the
                                  #   sum -- --serial brings back the old one-at-a-time order
    python gate.py --kb-build     # rebuild the KB when it is stale
    python gate.py --only test    # run steps whose name contains "test"
    python gate.py -v             # stream child output instead of capturing it

Exit status: 0 when every step PASSes (WARN allowed unless --strict; with --strict a
SKIP is a failure too -- a machine that silently skips probes/corpus is not covered).
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
# went from ~63 s serial to ~24 s (2026-10-28, 12 steps), and the long pole is
# selftest/probes/corpus at ~19 s each, not the sum.
# --serial restores the sequential order; --stream implies it (interleaved
# child output would be unreadable).
PARALLEL = ("selftest", "probes", "logicd", "gtbprobe", "corpus", "coverage")


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
        # a streamed child must still have a deadline: without one, a hung JVM
        # pins the gate forever with no row and no failure.
        try:
            rc = subprocess.run([PY, *argv], cwd=str(ROOT), env=child_env(),
                                timeout=timeout).returncode
        except subprocess.TimeoutExpired:
            return (name, "FAIL", time.time() - t0, "", f"timeout after {timeout}s")
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
    # The KB answers "why does this rule fire" and "what does this fixture
    # assert", so rules/*.json and tests/cases/*.mlog are inputs even though
    # kb.py does not index them as documents: a rule rewritten yesterday and a
    # fixture added an hour ago both make the answers stale.
    for pat in ("rules/*.json", "tests/cases/*.mlog"):
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
        # The evaluation contract (tools/mlog_eval.py) is the interface the
        # scenario runner, the MCP layer and the Mindcode front end all build
        # on: one envelope, one closed failure vocabulary.  Three modules would
        # silently drift apart if the shape were only asserted in their own
        # tests, so it is asserted on its own here (tests/eval/).
        ("eval", ["tests/eval/run_eval_tests.py"], ""),
        # Task progress (tools/taskstate.py) is what lets a retry resume at the
        # stage that failed; the record is written before it is reported, and a
        # changed source demotes old progress.  Plain files, so it runs everywhere.
        ("taskstate", ["tests/taskstate/run_taskstate_tests.py"], ""),
        # The result cache (tools/cache.py) is opt-in and must stay invisible
        # unless MLOG_CACHE=1; a stale hit would be indistinguishable from a
        # wrong answer, so the key/eviction rules get their own step.
        ("cache", ["tests/cache/run_cache_tests.py"], ""),
        # The observation schema (tools/observation.py) is what makes two runs
        # comparable at all; the differential runner is layered on it.  Pure
        # data, so it runs everywhere -- only the live-world half can skip.
        ("observation", ["tests/observation/run_observation_tests.py"], ""),
        # The fidelity envelope (tools/fidelity.py) is what turns a simulated-vs-
        # live difference into a named boundary instead of a mystery; it is data,
        # so its selftest runs everywhere.
        ("fidelity", ["tools/fidelity.py", "selftest"], ""),
        ("lint", ["tools/rule_capture.py", "lint"], ""),
        # the checkers' own invariant: a malformed statement must still be
        # caught after junk tokens are appended, i.e. no check may parse a
        # statement with an anchored regex and fail open when the line grows
        # (tests/shapes/run_shapes.py).
        ("shapes", ["tests/shapes/run_shapes.py"], ""),
        # docs drift: the signature lines and field tables in the hand-written
        # docs must agree with tools/instr_semantics.json (tests/docsig/),
        # because a doc that teaches a nonexistent operand is how the radar
        # "count" myth spread to four PATTERNS.md mirrors (see the docstring).
        ("docsig", ["tests/docsig/run_docsig.py"], ""),
        # rule coverage: every active rule must fire on at least one fixture, the
        # rid of every finding must belong to a rules/*.json, and the (rid ->
        # cases) map must match tests/rule-coverage.json.  Without it, rewording a
        # message silently re-classifies findings and a rule that never fires
        # anywhere looks exactly like a rule that works (tests/ruleids/).
        ("ruleids", ["tests/ruleids/run_ruleids.py"], ""),
        # the in-game quick check: MlogAuxiliary/scripts/quickcheck.js answers "is this
        # instruction real / does it need a newer build / is this name a link" without
        # Python.  Its rule table is GENERATED from instr_semantics.json + mlogcheck,
        # so the first assertion is that the file on disk still matches the generator;
        # then 14 hand-checked programs; then that it never calls a name unbound when
        # the full checker is happy (under-reporting is allowed, inventing is not).
        ("quickcheck", ["tests/mlogauxiliary/run_quickcheck_tests.py"], ""),
        # the same cases, re-run inside the game engine.  Real Rhino (v160.7) splits
        # "abc def".split(/\s+/) into single characters -- a quantified pattern behaves
        # like an empty match in its String.split -- so a node-only test cannot see the
        # difference.  Needs the jar; exits 3 (SKIP) without it.
        ("rhinoparity", ["tests/mlogauxiliary/run_rhino_parity.py"], ""),
        # the mod whole init path, still without a window: main.js is loaded into the
        # script scope the way Mods.loadScripts does it, then asked to build its settings
        # table against a fake Table.  Catches Table/Cell drift and init-time throws that
        # node cannot see (reading the mount back with scope.get(k, scope) used to kill
        # init right after the rule table loaded).
        ("ui", ["tests/mlogauxiliary/run_ui_smoke.py"], ""),
        # the installable package: build it, then RUN it.  "打包安装即用" is easy
        # to fake by zipping the mod folder, and such a package cannot work -- the
        # mod is a front end.  So the assertions are behavioural: the sidecar
        # closure (including imports nested inside functions, e.g. rule_ids),
        # /health and /analyze served by the packaged copy, install.ps1 and
        # uninstall.ps1 against a throwaway saves\mods, VERSION.txt hashes, and a
        # zip without __pycache__.
        ("package", ["tests/packaging/run_pack_tests.py"], ""),
        # Grief to Ban is a separate project (see MOD_DEPS below): pure JS, so the
        # check is node --check over every script + the pure-logic suite in plain
        # node.  No jar, no game, no Python deps -- it must stay under a second.
        ("gtb", ["tests/grief-to-ban/run_gtb_tests.py"], ""),
        # Mindcode (.mnd -> mlog) is an external compiler driven as a
        # subprocess; the tests SKIP (exit 3) when no JAR/JRE21 is present,
        # which is the clean-checkout case.  Vendor a jar under
        # out/_mindcode/ or set MINDCODE_JAR to run them.
        ("mindcode", ["tests/mindcode/run_mindcode_tests.py"], ""),
        # Scenario files (scene v1 + assertions/observations) run through the
        # same executor as mlogsim; the runner is what makes "did the rig work"
        # a single verdict instead of a var dump.
        ("scenario", ["tests/scenario/run_scenario_tests.py"], ""),
        # Differential runs need a live world *and* the offline executor, so in a
        # clean checkout they exits 3 (SKIP) instead of pretending to pass.
        ("differential", ["tests/differential/run_differential_tests.py"], ""),
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
        # the mod <-> sidecar contract (tests/logicd/): logicd HTTP protocol, and --
        # when a jar is present -- the bytes travelling through the game own
        # configure() channel into a real v160.7 processor and back.  Exit 3 means
        # no JRE or no versioned jar, which is the clean-checkout case.
        steps.append(("logicd", ["tests/logicd/run_logicd_tests.py"], ""))
        # Grief to Ban has to survive the real thing: the mod is copied into a
        # throwaway server's config/mods, the server starts, and the mod's own
        # self-test runs inside Rhino (21 assertions: lib defaults, the
        # gen.Building.enabled public field, the package-private
        # NetServer$VoteSession.target we read through Class.forName).  This is
        # the only place where "Packages.xxx.MyClass is not a Class" bites --
        # node sees none of it.  rc 0 also on the clean-checkout SKIP (no jar).
        steps.append(("gtbprobe", ["tests/grief-to-ban/run_server_probe.py"], ""))
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
    # The two mods live in their own projects, side by side with this checkout
    # (D:\Develop\MlogAuxiliary, D:\Develop\GriefToBan), not underneath it: this
    # repo is the toolchain they call into.  When a mod is absent, its steps are
    # reported as SKIP instead of failing, so a checkout holding only the tools
    # still gates cleanly.  Put the mod back in the repo root and the steps run
    # again -- nothing here depends on where the flat layout came from.
    deps = {"quickcheck": "MlogAuxiliary", "rhinoparity": "MlogAuxiliary",
            "ui": "MlogAuxiliary", "package": "MlogAuxiliary",
            "gtb": "GriefToBan", "gtbprobe": "GriefToBan"}
    steps = [(n, None, deps[n] + "/ is a separate project (absent from this checkout)")
             if (a is not None and n in deps and not (ROOT / deps[n]).is_dir())
             else (n, a, s) for n, a, s in steps]
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
        summary += ", " + str(len(skips)) + " skipped (" + ", ".join(skips) + ")"
        if args.strict:
            summary += " -- --strict counts a SKIP as a failure"
    summary += f" in {time.time() - t_all:.1f}s"
    if fails:
        summary += " -- FAILED: " + ", ".join(fails)
    print(summary)
    strict_bad = (warns or skips) if args.strict else []
    return 1 if fails or (args.strict and strict_bad) else 0


if __name__ == "__main__":
    raise SystemExit(main())