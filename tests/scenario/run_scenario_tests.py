#!/usr/bin/env python
"""tests/scenario/run_scenario_tests.py -- the contract tests for tools/scenario.py.

A scenario is a scene plus three promises: what to observe, what must be true,
and one mlog_eval envelope as the answer.  Those are the things this file pins:

* the schema gate (a scenario missing an id, a limit, a legal op or an aggregate
  has to be *refused*, not half-run),
* backwards compatibility (every v1 scene in scenes/ still loads and validates),
* the three shipped templates (each one is `check`-clean, and at least one is
  actually simulated and must pass its assertions),
* the failure path (a deliberately impossible assertion yields
  `assertion_failed`, one diagnostic per assertion, and CLI exit code 1),
* the envelope (the JSON on stdout is mlog_eval's, at the requested level).

Why not pytest: this repo's suites are plain scripts with "ok"/"FAIL" lines so a
reader sees the same output the CI log does, and so running one file needs no
virtualenv.  Same shape as tests/eval/run_eval_tests.py.

Usage:
    python tests/scenario/run_scenario_tests.py            # everything
    python tests/scenario/run_scenario_tests.py --fast     # skip the JVM tests

Exit codes: 0 all pass, 1 a test failed, 3 the JVM/jar is unavailable (the
simulation tests were skipped, everything else still ran).
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import scenario  # noqa: E402  (needs tools/ on the path)

SCEN = ROOT / "scenes" / "scenarios"
TMP = ROOT / "out" / "_scenario" / "tests"

TEMPLATES = ["unit-control.json", "building-interaction.json",
             "processor-competition.json"]
# A v1 scene that the repo already had: it must keep working untouched.
V1_SCENE = ROOT / "scenes" / "sim6" / "haul-flare.json"

FAILS: list[str] = []
SKIPPED: list[str] = []


def ok(cond: bool, what: str) -> bool:
    if cond:
        print("ok   " + what)
    else:
        FAILS.append(what)
        print("FAIL " + what)
    return bool(cond)


def skip(what: str) -> None:
    SKIPPED.append(what)
    print("skip " + what)


def cli(*args: str) -> subprocess.CompletedProcess:
    """Run the scenario CLI the way a user would; returns the finished process."""
    return subprocess.run([sys.executable, str(TOOLS / "scenario.py"), *args],
                          cwd=str(ROOT), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=600)


def cli_json(*args: str) -> tuple[dict, int]:
    cp = cli(*args)
    try:
        return json.loads(cp.stdout), cp.returncode
    except json.JSONDecodeError:
        raise AssertionError("stdout was not JSON (rc=%s):\n%s\n%s"
                             % (cp.returncode, cp.stdout[-800:], cp.stderr[-800:]))


def errs(sc: dict) -> str:
    return " | ".join(scenario.validate(sc))


# ---------------------------------------------------------------- schema

def test_templates_are_valid() -> None:
    for name in TEMPLATES:
        path = SCEN / name
        if not ok(path.is_file(), "%s exists" % name):
            continue
        sc = scenario.load(str(path))
        ok(sc["version"] == 2, "%s is schema v2" % name)
        ok(bool(sc.get("id")) and bool(sc.get("title")) and bool(sc.get("goal")),
           "%s carries id/title/goal" % name)
        ok(scenario.validate(sc) == [], "%s validates clean" % name)
        ok(sc["path"] == str(path), "%s keeps its path" % name)
        ok(isinstance(sc.get("limits"), dict)
           and isinstance(sc["limits"].get("ticks"), int)
           and sc["limits"]["ticks"] > 0,
           "%s has a positive integer tick limit" % name)
        ok(len(sc.get("assertions") or []) >= 1, "%s asserts something" % name)
        ok(len(sc.get("observations") or []) >= 1, "%s observes something" % name)
        builds = {b["name"] for b in sc["buildings"]}
        for a in sc["assertions"]:
            ok(a["logic"] in builds,
               "%s.%s reads a real building (%s)" % (sc["id"], a["id"], a["logic"]))
            ok(a["op"] in scenario.OPS, "%s.%s uses a legal op (%s)"
               % (sc["id"], a["id"], a["op"]))


def test_schema_errors() -> None:
    """Each mutation must be refused, and the message must name the field."""
    base = scenario.load(str(SCEN / "unit-control.json"))

    def refused(what: str, mutate, needle: str) -> None:
        sc = copy.deepcopy(base)
        mutate(sc)
        found = errs(sc)
        ok(bool(scenario.validate(sc)) and needle.lower() in found.lower(),
           "refused: %s (said %r)" % (what, found[:120]))

    refused("empty id", lambda s: s.__setitem__("id", ""), "id")
    refused("missing limits", lambda s: s.pop("limits", None), "limits")
    refused("zero ticks", lambda s: s["limits"].__setitem__("ticks", 0), "ticks")
    refused("text timeout", lambda s: s["limits"].__setitem__("timeout_s", "soon"),
            "timeout_s")
    refused("unknown aggregate",
            lambda s: s["observations"][0].__setitem__("aggregate", "median"),
            "aggregate")
    refused("observation of a ghost building",
            lambda s: s["observations"][0].__setitem__("logic", "ghost"),
            "not a building")
    refused("duplicate observation name",
            lambda s: s["observations"].append(dict(s["observations"][0])),
            "duplicate")
    refused("illegal op", lambda s: s["assertions"][0].__setitem__("op", "matches"),
            "op")
    refused("assertion without value",
            lambda s: s["assertions"][0].pop("value", None), "value")
    refused("no assertions", lambda s: s.__setitem__("assertions", []),
            "at least one assertion")
    refused("optional success criteria",
            lambda s: s.__setitem__("success_criteria", {"all_assertions": False}),
            "all_assertions")
    refused("assertion on a non-processor building",
            lambda s: s["assertions"][0].__setitem__("logic", "flare"),
            "not a building")
    refused("assertion naming a ghost observation",
            lambda s: s["assertions"][0].__setitem__("observation", "ghost"),
            "observation")

    # The same class of mistake must also stop the CLI, without a JVM.
    raw = json.loads((SCEN / "unit-control.json").read_text(encoding="utf-8"))
    raw["assertions"][0]["op"] = "matches"
    TMP.mkdir(parents=True, exist_ok=True)
    broken = TMP / "bad-op.json"
    broken.write_text(json.dumps(raw, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    env, rc = cli_json("check", str(broken), "--json")
    ok(rc == 1 and env["ok"] is False and env["errors"],
       "CLI check rejects an illegal op with exit 1")

    stray = TMP / "stray-key.json"
    stray.write_text(json.dumps({"name": "x", "version": 2, "bogus": 1}),
                     encoding="utf-8")
    env, rc = cli_json("check", str(stray), "--json")
    ok(rc == 1 and any("unknown top-level key" in e for e in env["errors"]),
       "unknown top-level keys are refused")


def test_v1_scenes_still_work() -> None:
    # scenes/ itself is not published (the rigs are private); the checked-in v1
    # file is a convenience, not a fixture this suite may depend on.  A clean
    # checkout still has to prove the v1 path loads, so synthesise one.
    TMP.mkdir(parents=True, exist_ok=True)
    if V1_SCENE.is_file():
        src = V1_SCENE
    else:
        skip("the checked-in v1 scene (%s) is not published" % V1_SCENE.name)
        src = TMP / "v1-synthetic.json"
        src.write_text(json.dumps({
            "name": "v1-synthetic", "version": 1, "world": {"size": 16},
            "buildings": [{"name": "p", "block": "micro-processor", "x": 8, "y": 8,
                           "code_inline": "set x 7\nend"}],
            "checks": [{"logic": "p", "var": "x", "equals": 7}],
        }), encoding="utf-8")
    sc = scenario.load(str(src))
    ok(sc["version"] == 1, "v1 scene loads as version 1")
    ok(sc["assertions"] == [], "v1 scene has no v2 assertions")
    ok(scenario.validate(sc) == [], "v1 scene validates clean")
    ok(sc["checks"], "v1 scene keeps its checks")
    env, rc = cli_json("check", str(src), "--json")
    ok(rc == 0 and env["ok"] is True, "CLI check accepts the v1 scene")
    ok(env["version"] == 1 and env["checks"] == len(sc["checks"]),
       "check --json reports the v1 check count")

    # A v1 file that spells code_inline as a list of lines must still work: the
    # v1 loader would stringify the list, so scenario.load takes over.
    TMP.mkdir(parents=True, exist_ok=True)
    inline = TMP / "v1-inline-list.json"
    inline.write_text(json.dumps({
        "name": "v1-inline-list", "version": 1, "world": {"size": 16},
        "buildings": [{"name": "p", "block": "micro-processor", "x": 8, "y": 8,
                       "code_inline": ["set x 1", "op add n n 1"]}],
        "checks": [{"logic": "p", "var": "x", "equals": 1}],
    }), encoding="utf-8")
    sc = scenario.load(str(inline))
    ok(sc["version"] == 1 and sc["checks"],
       "v1 file with list code_inline loads as v1")
    shadows = list((ROOT / "out" / "_scenario" / "v1").glob("v1-inline-list.json"))
    ok(bool(shadows), "list code_inline went through the shadow copy")


def test_list_cli() -> None:
    payload, rc = cli_json("list", "--json")
    ids = {e["id"] for e in payload["scenarios"] if e["id"]}
    ok(rc == 0, "list exits 0")
    for name in TEMPLATES:
        ok(name.replace(".json", "") in ids, "list shows %s" % name)
    ok(payload["count"] >= len(TEMPLATES), "list counts every scenario")
    ok(all(e["ok"] for e in payload["scenarios"]),
       "every shipped scenario validates")


# ---------------------------------------------------------------- scoring

def test_compare_and_aggregate() -> None:
    refs = {"core": (38, 30, "core-shard"), "belt": (35, 30, "conveyor")}
    T = scenario.compare
    ok(T("12", "gt", 10), "numeric gt")
    ok(not T("8", "gt", 10), "numeric gt false")
    ok(T(12, "ge", 12), "ge is inclusive")
    ok(T("9", "lt", 10) and not T(10, "lt", 10), "lt is exclusive")
    ok(T(10, "le", 10), "le is inclusive")
    ok(T("1", "eq", 1) and T("copper", "eq", "copper"), "eq across types")
    ok(T(None, "ne", 1), "a missing value satisfies ne but never eq")
    ok(not T(None, "eq", 1), "missing value never matches eq")
    ok(T("ping-pong", "contains", "pong") and not T("ping", "contains", "pong"),
       "contains is a substring test")
    ok(T("true", "eq", True) and T("0", "eq", False), "bools compare as text")
    ok(T("Building#211[38,30]:core-shard", "eq", "core", refs),
       "a building name matches its scene building")
    ok(not T("Building#211[35,30]:conveyor", "eq", "core", refs),
       "the wrong building does not match")

    A = scenario.aggregate
    ok(A(["3", "1", "2"], "max") == 3, "aggregate max")
    ok(A(["3", "1", "2"], "min") == 1, "aggregate min")
    ok(A(["3", "1", "2"], "sum") == 6, "aggregate sum")
    ok(A(["3", "1", "2"], "last") == 2, "aggregate last")
    ok(A([], "last") is None, "an empty sample list aggregates to None")
    ok(A(["null", "7"], "last") == 7, "null samples are skipped")


def test_envelope() -> None:
    """run() must answer in mlog_eval's vocabulary, not its own."""
    import mlog_eval as E

    # Whether a live world happens to be running must not change what this file
    # asserts (and it does move: CI has none, the dev box often does).  Force the
    # probe to answer "no world" so the refusal path is tested, not skipped.
    real_world_env = scenario.world_environment
    scenario.world_environment = lambda: {
        "ok": False, "why": "forced: no live world", "notes": ["forced"],
        "handshake": None, "status": None, "mindustry": None, "java": None,
        "jar": None, "map": None, "world_size": None, "tick": None}
    try:
        world_env = scenario.run(str(SCEN / "unit-control.json"), via="world")
    finally:
        scenario.world_environment = real_world_env
    ok(world_env["ok"] is False
       and world_env["failure_type"] == "unsupported_environment",
       "via=world refuses cleanly when no world is up")
    ok(world_env["next_steps"], "via=world suggests a next step")
    ok(scenario.exit_code(world_env) == 3, "unsupported_environment exits 3")
    ok(scenario.exit_code({"ok": True}) == 0, "a pass exits 0")
    ok(scenario.exit_code({"ok": False, "failure_type": "assertion_failed"}) == 1,
       "assertion failure exits 1")
    ok(set(world_env).issuperset({"schema", "ok", "stage", "failure_type",
                                  "message", "level", "next_steps"}),
       "the envelope has mlog_eval's keys")

    # An invalid dict never reaches the executor: it comes back as one envelope.
    bad = copy.deepcopy(scenario.load(str(SCEN / "unit-control.json")))
    bad["assertions"] = []
    env = scenario.run(bad, level="diagnostics")
    ok(env["ok"] is False and env["failure_type"] == "runtime_error",
       "an invalid scenario is a runtime_error, not a crash")
    ok(any("assertion" in a for a in env["artifacts"]["errors"]),
       "and the envelope names the problem")
    ok(E.FAILURE_TYPES == tuple(E.FAILURE_TYPES)
       and all(e["failure_type"] in E.FAILURE_TYPES
               for e in (world_env, env)),
       "every failure_type used is in mlog_eval.FAILURE_TYPES")

    # A box with no JVM must answer the same way, with exit code 3, instead of
    # crashing inside mlogsim: force the environment probe to fail.
    real = scenario.environment
    scenario.environment = lambda: {"ok": False, "java": "", "jar": "",
                                    "notes": ["forced: no JVM"], "version": None}
    try:
        no_jvm = scenario.run(scenario.load(str(SCEN / "unit-control.json")))
    finally:
        scenario.environment = real
    ok(no_jvm["ok"] is False
       and no_jvm["failure_type"] == "unsupported_environment",
       "no JVM -> unsupported_environment")
    ok(scenario.exit_code(no_jvm) == 3, "no JVM exits 3")
    ok(no_jvm["next_steps"], "no JVM suggests a next step (install a JRE, not a fix to the scenario)")


def test_simulation(env_ok: bool) -> None:
    if not env_ok:
        skip("simulation tests (no JVM/jar)")
        return
    import mlog_eval as E

    sc = scenario.load(str(SCEN / "unit-control.json"))
    env = scenario.run(sc, level="diagnostics")
    ok(env["ok"] is True, "unit-control passes in the simulator")
    ok(env["stage"] == "scenario" and env["failure_type"] is None,
       "a passing run names the scenario stage and no failure")
    ok("passed" in (env["message"] or ""), "the message says how many passed")

    diags = [d for d in env.get("diagnostics") or [] if d.get("kind") == "assertion"]
    ok(len(diags) == len(sc["assertions"]),
       "one diagnostic per assertion (%d)" % len(diags))
    ok(all(d["ok"] for d in diags) and all("actual" in d for d in diags),
       "each diagnostic carries its actual value")

    art = env["artifacts"]
    ok(art["scenario"] == sc["id"], "artifacts name the scenario")
    ok(set(art["observations"]) == {o["name"] for o in sc["observations"]},
       "artifacts report every observation")
    ok(art["assertions"] and art["assertions"][0]["id"] == sc["assertions"][0]["id"],
       "artifacts list the assertions")
    ok(isinstance(art.get("ticks"), int) and art["ticks"] == sc["limits"]["ticks"],
       "artifacts report the tick budget actually run")
    ok(art["scene"]["placed"] >= 1 and not art["scene"]["errors"],
       "the scene applied without errors")
    ok(isinstance(env.get("elapsed_ms"), int), "the envelope times the run")
    ok(env["levels"]["simulation"] is True,
       "the envelope records that the simulation dimension ran")
    ok(env["levels"]["real_runtime"] is None and env["levels"]["static"] is None,
       "and leaves the dimensions it never touched as None, not False")
    ok(set(E.result(ok=True, stage="scenario", level="summary")) - set(env) == set(),
       "diagnostics keeps every summary key")


def test_failed_assertion() -> None:
    env_ok = scenario.environment()["ok"]
    if not env_ok:
        skip("failed-assertion test (no JVM/jar)")
        return

    # Take a template and make one assertion impossible.  The tick budget stays
    # as shipped, so only that one assertion can fail and the test can insist on
    # "exactly the broken one is reported".
    raw = json.loads((SCEN / "processor-competition.json").read_text(encoding="utf-8"))
    raw["assertions"][0]["value"] = 999999
    raw["assertions"][0]["desc"] = "deliberately impossible"
    TMP.mkdir(parents=True, exist_ok=True)
    broken = TMP / "impossible.json"
    broken.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")

    payload, rc = cli_json("run", str(broken), "--json", "--level", "diagnostics")
    ok(rc == 1, "an impossible assertion exits 1 (got %s)" % rc)
    ok(payload["ok"] is False and payload["failure_type"] == "assertion_failed",
       "failure_type is assertion_failed")
    ok(payload["schema"] == "mlog-eval/v1" and payload["stage"] == "scenario",
       "the failure keeps the envelope's schema and stage")
    fails = [d for d in payload.get("diagnostics") or [] if not d.get("ok")]
    ok(len(fails) == 1 and fails[0]["id"] == raw["assertions"][0]["id"],
       "exactly the broken assertion is reported")
    ok(payload["next_steps"], "a failed run suggests a next step")
    ok(payload["artifacts"]["scenario"] == raw["id"], "the failure still names the run")

    printable = cli("run", str(broken))
    ok("FAIL" in printable.stdout and "999999" in printable.stdout,
       "the text report shows the missed expectation")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    fast = "--fast" in args

    test_templates_are_valid()
    test_schema_errors()
    test_v1_scenes_still_work()
    test_list_cli()
    test_compare_and_aggregate()
    test_envelope()

    env = scenario.environment()
    if not env["ok"]:
        print("env  " + "; ".join(env.get("notes") or ["JVM unavailable"]))
    if not fast and env["ok"]:
        test_simulation(True)
        test_failed_assertion()
    else:
        skip("simulation tests (%s)" % ("--fast" if fast else "no JVM/jar"))

    print("-" * 56)
    if FAILS:
        print("%d failure(s):" % len(FAILS))
        for f in FAILS:
            print("  - " + f)
        return 1
    if SKIPPED and not env["ok"]:
        print("all checks that need no JVM passed; %d skipped" % len(SKIPPED))
        return 3
    print("all %s passed%s" % (os.path.basename(__file__),
                               " (%d skipped)" % len(SKIPPED) if SKIPPED else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
