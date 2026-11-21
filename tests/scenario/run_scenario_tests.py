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

import base64
import copy
import json
import math
import os
import struct
import subprocess
import sys
import tempfile
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


def test_live_rig_wiring() -> None:
    """What the live world needed that a blank sim world never exposed.

    The first `--via world` run of the generated scenes found three wiring bugs
    that no offline test could see, because the offline host applies the scene
    in-process and the live host goes through the game's own config payloads:

    * a modifier printed with `print(...)`, which the daemon does not capture
      (only `sb.append`), so the run said "applied ... NOT APPLIED";
    * `configureAny()` broadcasts the code as `readCompressed()` bytes, which
      rebuilds `links` with `findLinkName()` -- a link named "hub" came back as
      "shard1" and the code's `hub` silently stayed null;
    * a core's `items` were added to whatever the map already held there, so the
      same scene started at 120 offline and 285 live.

    None of that is visible without a world, so it is pinned on the generated JS.
    """
    import scene

    sc = scenario.load(str(SCEN / "generated-resource-drain.json"))
    js = scene.build_js("world", sc)

    cfg = js.find("configureAny(")
    ok(cfg != -1, "the world flavor broadcasts the code through configureAny()")
    relink = js.find("b.links.clear();", cfg if cfg != -1 else 0)
    ok(relink != -1 and cfg != -1 and relink > cfg,
       "named links are re-attached after the broadcast (readCompressed renames them)")
    rebind = js.find("b.updateCode(s);", relink if relink != -1 else 0)
    ok(rebind != -1 and relink != -1 and rebind > relink,
       "and updateCode re-binds them, or the code's `hub` stays null")
    ok('"hub"' in js, "the scene's own link name reaches the script")

    clear = js.find("b.items.clear();")
    add = js.find("b.items.add(")
    ok(clear != -1 and add != -1 and clear < add,
       "a core's stock is reset before the scene's items are added")


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


def test_instruction_trace_step_and_tick_modes() -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=TMP, prefix="itrace-") as directory:
        path = Path(directory) / "loop.mlog"
        path.write_text("set n 0\n# comment\nloop:\nop add n n 1\njump loop lessThan n 3\n"
                        "print n\nend\n", encoding="utf-8")
        command = [sys.executable, "-X", "utf8", str(TOOLS / "mlogsim.py"), str(path)]
        for flag, amount, expected_ticks in (
            ("--steps", "10", [0] * 10),
            ("--ticks", "5", [i for i in range(5) for _ in range(2)]),
        ):
            trace = Path(directory) / (flag[2:] + ".tsv")
            proc = subprocess.run(command + [flag, amount, "--itrace", str(trace),
                                             "--itrace-var", "n", "--json"],
                                  cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=45)
            if not ok(proc.returncode == 0 and trace.is_file(), f"{flag} writes a trace: {proc.stderr}"):
                continue
            rows = [line.split("\t", 3) for line in trace.read_text(encoding="utf-8").splitlines()[1:]]
            ok([int(row[0]) for row in rows] == expected_ticks, f"{flag} records the expected tick values")
            ok([int(row[1]) for row in rows] == [0, 1, 2, 1, 2, 1, 2, 3, 4, 0],
               f"{flag} traces each actual instruction, including restart at PC 0")
            ok(len(rows) == 10 and rows[1][3] == "op add n n 1" and rows[6][2] == "n=3;",
               f"{flag} maps labelled source and captures values before execution")

        refusal = subprocess.run(command + ["--remote", "--itrace", str(Path(directory) / "remote.tsv")],
                                 cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=10)
        ok(refusal.returncode == 2 and "--itrace requires a local mlog file" in refusal.stderr,
           "remote mode reports unsupported instruction tracing rather than dropping it")


def test_sim_json_trace_and_assertions() -> None:
    TMP.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=TMP, prefix="trace-json-") as directory:
        path = Path(directory) / "scene.json"
        trace = Path(directory) / "units.csv"
        path.write_text(json.dumps({
            "name": "unit trace", "world": {"size": 64},
            "buildings": [
                {"name": "core", "block": "core-shard", "x": 32, "y": 32},
                {"name": "ctrl", "block": "micro-processor", "x": 20, "y": 32,
                 "code_inline": "ubind @flare\nucontrol move 40 32 0 0\nend\n"},
            ],
            "units": [{"type": "flare", "count": 1, "at": [24, 32], "team": "sharded"}],
        }), encoding="utf-8")
        command = [sys.executable, "-X", "utf8", str(TOOLS / "mlogsim.py"), "--scene", str(path),
                   "--ticks", "5", "--trace", str(trace), "--json"]
        for expression, expected_code, diagnostic in (
            ("uhp > 0", 0, "ASSERT PASS"),
            ("uhp < 0", 3, "ASSERT FAILED"),
        ):
            proc = subprocess.run(command + ["--assert-last", expression],
                                  cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=45)
            ok(proc.returncode == expected_code and diagnostic in proc.stderr and "TRACE " in proc.stderr,
               f"JSON run reports {expression!r} and trace location on stderr with exit {expected_code}")
            try:
                result = json.loads(proc.stdout)
            except json.JSONDecodeError:
                result = []
            ok(bool(result) and result[0].get("steps") == 5,
               f"stdout stays JSON when asserting {expression!r}")


def test_pacing_extends_default_js_timeout() -> None:
    import mlogsim

    server = mlogsim.Server(mlogsim._default_java(), mlogsim._default_jar(), world_size=32)
    try:
        server.prepare()
        messages = server.js("print('undefined'); print('Error: user text');")
        ok(messages[-2:] == ["undefined", "Error: user text"], "JS console distinguishes printed text from protocol markers")
        try:
            server.js("throw new Error('intentional test failure');", timeout=3.0)
        except mlogsim.SimError as exc:
            ok("intentional test failure" in str(exc) and "timeout" not in str(exc),
               "JS exceptions fail immediately rather than timing out")
        else:
            ok(False, "JS exceptions fail immediately rather than timing out")
        # Test the same case as a long realtime projection without waiting 3 minutes.
        server.js_timeout = 1.0
        result = mlogsim.run_mlog(server, "paced", "end", 60, ticks=True, rt=0.5)
        ok(result["steps"] == 60, "default JS budget includes paced sleeps beyond the base timeout")
    finally:
        server.close()


GRID_EVENTS_JS = """
    Time.run(90, function(){ Vars.world.tile(4,20).setBlock(Blocks.air); });
    Time.run(120, function(){ Vars.world.tile(10,10).setBlock(Blocks.air); });
"""


def grid_tick_samples(save: Path, ticks: int, *, native: bool) -> list[list[float]]:
    import mlogsim

    server = mlogsim.Server(mlogsim._default_java(), mlogsim._default_jar(), world_size=32)
    try:
        # Read the save in one console command while paused, so neither run
        # advances between loading the grid and arming the tick sampler.
        server.js("""
            var stateEnum = Packages.mindustry.core.GameState.State;
            Packages.mindustry.io.SaveIO.load(new Packages.arc.files.Fi(%s));
            Vars.state.set(stateEnum.paused);
            Vars.state.rules.waves = false;
            Vars.state.rules.canGameOver = false;
            Time.setDeltaProvider(new Packages.arc.func.Floatp({get:function(){ return 1; }}));
            Time.delta = 1;
            var access = Packages.mindustry.logic.LAccess;
            var battery = Vars.world.build(11,10), load = Vars.world.build(12,10);
            var up = Vars.world.build(11,20), down = Vars.world.build(3,20);
            var gridSamples = [];
            function sampleGrid(){
                gridSamples.push([Time.delta, load.sense(access.powerNetIn), load.sense(access.powerNetOut),
                    battery.sense(access.powerNetStored), battery.sense(access.totalPower),
                    load.sense(access.efficiency), up.sense(access.efficiency), down.sense(access.efficiency)]);
            }
        """ % json.dumps(save.as_posix()) + GRID_EVENTS_JS)
        if native:
            # The reference lets Logic.update() drive the world through its
            # normal update path. Only the delta and the observed phase are fixed.
            server.js("""
                var afterTick = new java.lang.Runnable({run:function(){
                    sampleGrid();
                    if(gridSamples.length == %d){
                        Vars.state.set(stateEnum.paused);
                        print("POWER_GRID_DONE");
                    }
                }});
                Packages.arc.Events.run(Packages.mindustry.game.EventType$Trigger.afterGameUpdate, afterTick);
                Vars.state.set(stateEnum.playing);
            """ % ticks)
            server.wait_for("POWER_GRID_DONE", 45)
        else:
            server.js("var probe = {updateTile:function(){}};" + mlogsim._loop_js(
                "probe", ticks, True, update="all", power=None, tick_extra="sampleGrid();",
            ))
        samples = server.js('print("GRID\t" + JSON.stringify(gridSamples));')
        return json.loads(next(line.split("\t", 1)[1] for line in samples if line.startswith("GRID\t")))
    finally:
        server.close()


def check_grid_tick_parity(save: Path) -> None:
    ticks = 420
    simulated = grid_tick_samples(save, ticks, native=False)
    native = grid_tick_samples(save, ticks, native=True)
    if not ok(len(simulated) == len(native) == ticks, "both hosts captured all 420 power ticks"):
        return
    fields = ("delta", "powerNetIn", "powerNetOut", "powerNetStored", "battery charge",
              "battery load efficiency", "upstream efficiency", "downstream efficiency")
    max_error = 0.0
    for tick, (sim_row, native_row) in enumerate(zip(simulated, native), 1):
        for field, observed, expected in zip(fields, sim_row, native_row, strict=True):
            if not math.isclose(observed, expected, rel_tol=1e-6, abs_tol=1e-6):
                ok(False, f"first grid difference at tick {tick} in {field}: sim {observed:g}, native {expected:g}")
                return
            max_error = max(max_error, abs(observed - expected))
    ok(True, f"all 420 ticks match native power flow, charge and load efficiency (max error {max_error:g})")

    downstream_cut = next((tick for tick, row in enumerate(native, 1) if tick >= 90 and row[7] == 0), None)
    generation_stops = next((tick for tick, row in enumerate(native, 1) if tick >= 120 and row[1] == 0), None)
    battery_empty = next((tick for tick, row in enumerate(native, 1) if tick >= 120 and row[4] == 0), None)
    load_stops = next((tick for tick, row in enumerate(native, 1) if tick >= 120 and row[5] == 0), None)
    ok(downstream_cut == 90 and generation_stops == 120
       and battery_empty is not None and load_stops is not None
       and 120 < battery_empty <= load_stops <= ticks,
       f"matched transition ticks: downstream cut {downstream_cut}, generation stops {generation_stops}, "
       f"battery empty {battery_empty}, battery load stops {load_stops}")


def test_grid_power_from_save() -> None:
    import mlogsim

    TMP.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="power-grid-", dir=TMP) as directory:
        root = Path(directory)
        save = root / "grid.msav"
        logic = root / "observe.mlog"
        events = root / "events.js"
        server = mlogsim.Server(mlogsim._default_java(), mlogsim._default_jar(), world_size=32)
        try:
            server.js("""
                var team = Packages.mindustry.game.Team.sharded;
                function place(x,y,name){
                    Vars.world.tile(x,y).setBlock(Vars.content.block(name), team);
                    return Vars.world.build(x,y);
                }
                place(24,24,"core-shard");
                place(10,10,"solar-panel");
                place(11,10,"battery");
                place(12,10,"illuminator");
                place(10,20,"solar-panel");
                place(10,21,"solar-panel");
                place(11,20,"illuminator");
                var upstream = place(9,20,"power-node");
                var downstream = place(4,20,"power-node");
                place(3,20,"illuminator");
                var links = java.lang.reflect.Array.newInstance(java.lang.Class.forName("arc.math.geom.Point2"), 1);
                links[0] = new Packages.arc.math.geom.Point2(downstream.tileX() - upstream.tileX(), 0);
                upstream.configured(null, links);
                if(upstream.power.graph != downstream.power.graph){
                    throw new Error("fixture power nodes did not connect");
                }
                Packages.mindustry.io.SaveIO.save(new Packages.arc.files.Fi(%s));
            """ % json.dumps(save.as_posix()))
        finally:
            server.close()

        events.write_text(GRID_EVENTS_JS, encoding="utf-8")
        logic.write_text(
            "getblock building battery 11 10\n"
            "getblock building load 12 10\n"
            "getblock building upstream 11 20\n"
            "getblock building downstream 3 20\n"
            "sensor charge battery @totalPower\n"
            "sensor stored battery @powerNetStored\n"
            "sensor supplied load @efficiency\n"
            "sensor source load @powerNetIn\n"
            "sensor demand load @powerNetOut\n"
            "sensor upstreamPower upstream @efficiency\n"
            "sensor downstreamPower downstream @efficiency\n"
            "op max maxCharge maxCharge charge\n"
            "op max maxStored maxStored stored\n"
            "op max maxSource maxSource source\n"
            "op max maxDemand maxDemand demand\n"
            "op max maxDownstream maxDownstream downstreamPower\n"
            "op greaterThan stopped @tick 135\n"
            "op mul backup supplied stopped\n"
            "op max maxBackup maxBackup backup\n"
            "end\n",
            encoding="utf-8",
        )
        command = [sys.executable, str(TOOLS / "mlogsim.py"), str(logic),
                   "--save", str(save), "--init-js", str(events), "--base", "20,24",
                   "--processor", "world", "--links", "off", "--ticks", "420", "--json"]
        cp = subprocess.run([*command, "--power", "grid"], cwd=ROOT, capture_output=True,
                            text=True, encoding="utf-8", timeout=180)
        if not ok(cp.returncode == 0, "grid mode loads and runs a real save: " + cp.stderr.strip()):
            return
        values = {key: float(value) for key, value in json.loads(cp.stdout)[0]["vars"].items()
                  if key in {"charge", "supplied", "upstreamPower", "downstreamPower",
                             "maxCharge", "maxStored", "maxSource", "maxDemand", "maxDownstream", "maxBackup"}}
        ok(values["maxCharge"] > 0 and values["maxStored"] > 0
           and values["maxSource"] > values["maxDemand"] > 0,
           "surplus charges a battery and Mlog senses grid flow and storage")
        ok(values["maxBackup"] > 0.99 and values["charge"] == 0 and values["supplied"] == 0,
           "battery powers its load after generation stops, then the load loses power")
        ok(values["maxDownstream"] > 0.99 and values["downstreamPower"] == 0
           and values["upstreamPower"] > 0.99,
           "removing the node cuts just the downstream side of the saved link "
           "(downstream peak %.2f, final %.2f, upstream final %.2f)"
           % (values["maxDownstream"], values["downstreamPower"], values["upstreamPower"]))

        cp = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                            encoding="utf-8", timeout=180)
        if ok(cp.returncode == 0, "the default fixed-power mode still runs the same save"):
            values = json.loads(cp.stdout)[0]["vars"]
            ok(float(values["downstreamPower"]) > 0.99 and float(values["supplied"]) > 0.99,
               "default full mode still powers disconnected loads")

        check_grid_tick_parity(save)


def test_mcp_power_profile() -> None:
    import mlog_mcp

    TMP.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mcp-power-", dir=TMP) as directory:
        path = Path(directory) / "source.json"
        path.write_text(json.dumps({"buildings": [
            {"block": "power-source", "x": 10, "y": 10},
            {"block": "illuminator", "x": 11, "y": 10},
        ]}), encoding="utf-8")
        logic = (
            "getblock building lamp 11 10\n"
            "sensor input lamp @powerNetIn\n"
            "sensor efficiency lamp @efficiency\n"
            "op equal partial efficiency 0.5\n"
            "op max sawPartial sawPartial partial\n"
            "op equal off efficiency 0\n"
            "op mul offAfterPartial off sawPartial\n"
            "op max sawOutage sawOutage offAfterPartial\n"
            "end\n"
        )
        profile = [{"tick": tick, "power_per_second": rate}
                   for tick, rate in ((1, 12), (10, 1.5), (20, 0), (30, 12))]
        replies = []
        mlog_mcp.handle({
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": "mlog_sim", "arguments": {
                "scene": str(path), "logic": logic, "ticks": 40, "power_profile": profile,
            }},
        }, emit=replies.append)
        response = replies[0]["result"]
        payload = response["content"][0]["text"]
        if not ok(not response["isError"], f"MCP runs a power profile: {payload if response['isError'] else 'OK'}"):
            return
        result = json.loads(payload)
        values = result["vars"]
        ok(result["power"] == "grid" and values["sawPartial"] == values["sawOutage"] == "1"
           and values["input"] == "12" and values["efficiency"] == "1",
           "MCP observes brownout, outage and restored full supply in one run")


def test_uploaded_power_scene() -> None:
    import mlog_mcp

    scene_data = {"buildings": [
        {"name": "lamp", "block": "illuminator", "x": 10, "y": 10},
        {"name": "other", "block": "illuminator", "x": 12, "y": 9},
    ]}
    args = {
        "scene_json": json.dumps(scene_data),
        "power_target": "lamp",
        "power_profile": [{"tick": 1, "power_per_second": 1.5}],
        "ticks": 30,
        "logic": ("getblock building lamp 10 10\nsensor eff lamp @efficiency\n"
                  "getblock building other 12 9\nsensor otherEff other @efficiency\nend"),
    }
    result = mlog_mcp.tool_sim(args)
    source = result["scene"]["power_source"]
    ok(source["added"] and source["target"] == "lamp" and result["vars"]["eff"] == "0.5"
       and result["vars"]["otherEff"] == "0",
       "uploaded scene adds a native power connection to just the selected grid")


def test_native_world_processor_and_side_effects() -> None:
    import mlog_mcp

    rate = mlog_mcp.tool_sim({"logic": "setrate 60\nset recorded @ipt\nstop",
                              "processor": "world", "ticks": 4})
    ok(rate["processor"] == "world" and rate["processor_block"] == "world-processor"
       and rate["ipt"] == 60 and rate["vars"]["recorded"] == "60" and rate["compile"]["ok"],
       "native world-processor setrate 60 updates @ipt and reports the compiled block")
    bad = mlog_mcp.tool_sim({"logic": "jump missing always 0 0", "processor": "world", "ticks": 4})
    ok(not bad["executed"] and not bad["compile"]["ok"]
       and "Undefined jump" in bad["compile"]["diagnostics"][0]["message"],
       "the real assembler reports undefined labels without running the source")

    case = {
        "version": 2, "id": "side-effects", "title": "Side effects", "goal": "Inspect the real world",
        "limits": {"ticks": 8, "timeout_s": 30}, "world": {"size": 32},
        "buildings": [
            {"name": "control", "block": "world-processor", "x": 10, "y": 10, "code_inline": [
                "getblock building cell 13 10", "write 42 cell 5", 'write "gate" cell 6',
                "makemarker text 300 20 20 false", "setrule unitCap 20 0 0 0 0",
                "spawn @flare 20 20 0 @sharded spawned false", "stop",
            ]},
            {"name": "cell", "block": "world-cell", "x": 13, "y": 10},
        ],
        "world_probe": {"checks": [
            {"marker": 300, "equals": True}, {"marker": 301, "equals": False},
            {"memory": {"x": 13, "y": 10, "index": 5}, "equals": 42},
            {"memory": {"x": 13, "y": 10, "index": 6}, "equals": "gate"},
            {"memory": {"x": 13, "y": 10, "index": 7}, "equals": 0},
            {"unit_count": {"x": 18, "y": 18, "width": 4, "height": 4,
                            "team": "sharded", "type": "flare"}, "equals": 1},
            {"unit_count": {"x": 0, "y": 0, "width": 4, "height": 4}, "equals": 0},
        ]},
    }
    TMP.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="side-effects-", dir=TMP) as directory:
        path = Path(directory) / "scenario.json"
        path.write_text(json.dumps(case), encoding="utf-8")
        passed = scenario.run_record(scenario.load(str(path)), level="diagnostics")
        if ok(passed["envelope"]["ok"], f"scenario_run checks marker, world-cell and unit side effects: {passed['envelope']['message']}"):
            checks = passed["record"]["world_probe"]["checks"]
            ok([c["actual"] for c in checks] == [True, False, 42, "gate", 0, 1, 0],
               "scenario measures the changed area and confirms the unrelated observations")
        case["world_probe"]["checks"][-1]["equals"] = 1
        path.write_text(json.dumps(case), encoding="utf-8")
        failure = scenario.run(scenario.load(str(path)), level="diagnostics")
        ok(failure["failure_type"] == "assertion_failed"
           and failure["diagnostics"][-1]["actual"] == 0,
           "scenario_run fails when a world-state assertion is wrong")


def test_live_logic_edit() -> None:
    import mlogsim
    from world_runtime import WorldPaths
    from world_server import World
    from world_edits import edit
    from world_queries import query

    TMP.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="live-processor-", dir=TMP) as directory:
        paths = WorldPaths.from_root(directory)
        game = World(mlogsim._default_java(), mlogsim._default_jar(), host=False, game_port=0, paths=paths)
        try:
            game.js(mlogsim.load_js(32))
            for x, block in ((10, "world-processor"), (12, "memory-cell"), (14, "switch")):
                game.js(mlogsim.place_js(x, 10, block))
            game.js("Vars.state.rules.allowEditWorldProcessors=true;")
            at = {"x": 10, "y": 10}

            def read():
                return query(game, {"op": "logic_code", **at}, data_dir=paths.data)

            def change(op="logic_set", **args):
                request = {"op": op, **(at if op == "logic_set" else {}), **args}
                return edit(game, request, audit=lambda *a, **kw: None, data_dir=paths.data)

            original = read()
            graph = query(game, {"op": "logic_graph", "limit": 8}, data_dir=paths.data)
            ok(graph["ok"] and len(graph["processors"]) == 1
               and graph["processors"][0]["source_sha256"] == original["source_sha256"]
               and graph["processors"][0]["links_sha256"] == original["links_sha256"],
               "logic graph exposes the live processor hashes")
            batch = query(game, {"op": "logic_batch_preview", "processors": [{
                "x": 10, "y": 10, "expected_revision": original["revision"],
                "code": "setrate 60\nstop",
                "link_changes": {"add": [{"x": 14, "y": 10}]},
            }]}, data_dir=paths.data)
            ok(batch["ok"] and batch["processors"][0]["compile"]["ok"]
               and batch["processors"][0]["proposed"]["links"][0]["name"] == "switch1"
               and read()["revision"] == original["revision"],
               "batch preview validates source and links without writing")
            initial = change(expected_revision=original["revision"], code="jump 1 always 0 0\nstop",
                             link_changes={"add": [{"x": 14, "y": 10}]})
            if not ok(initial["ok"], f"world daemon installs validated source and link: {initial.get('error', 'OK')}"):
                return
            ok("jump L1" in initial["labelled_code"] and initial["links"][0]["name"] == "switch1"
               and initial["processor"] == "world-processor" and initial["compile"]["version"],
               "world readback includes labelled source, type, native version and link target")
            bad = change(expected_revision=initial["revision"], code="jump missing always 0 0",
                         link_changes={"remove": ["switch1"]})
            missing = change(expected_revision=initial["revision"], link_changes={"add": [{"x": 5, "y": 5}]})
            ok(not bad["ok"] and not bad["compile"]["ok"] and not missing["ok"]
               and read()["revision"] == initial["revision"],
               "invalid source and invalid link targets leave the live processor unchanged")
            changed = change(expected_revision=initial["revision"],
                             link_changes={"remove": ["switch1"], "add": [{"x": 12, "y": 10}]})
            if not ok(changed["ok"], f"world daemon accepts a link-only edit: {changed.get('error', 'OK')}"):
                return
            stale = change(expected_revision=initial["revision"], code="setrate 60\nstop")
            ok(stale["conflict"] and stale["source_sha256"] == initial["source_sha256"]
               and stale["links_sha256"] != initial["links_sha256"],
               "a changed link alone invalidates a pending code edit")
            restored = change("logic_rollback", snapshot_id=changed["snapshot_id"])
            ok(restored["ok"] and restored["code"] == initial["code"] and restored["links"] == initial["links"]
               and read()["revision"] == initial["revision"],
               "rollback restores code and links from the durable snapshot")
            both = change(expected_revision=initial["revision"], code="setrate 60\nstop",
                          link_changes={"remove": ["switch1"], "add": [{"x": 12, "y": 10}]})
            if not ok(both["ok"], "a single edit can replace both source and links"):
                return
            rolled_back = change("logic_rollback", snapshot_id=both["snapshot_id"])
            ok(rolled_back["ok"] and rolled_back["source_sha256"] == initial["source_sha256"]
               and rolled_back["links_sha256"] == initial["links_sha256"],
               "rollback restores a revision that changed both source and links")
            pending = change(expected_revision=initial["revision"], code="setrate 60\nstop")
            intervening = change(expected_revision=pending["revision"], code="setrate 30\nstop")
            stale_rollback = change("logic_rollback", snapshot_id=pending["snapshot_id"])
            ok(stale_rollback["conflict"] and stale_rollback["revision"] == intervening["revision"],
               "rollback refuses to overwrite a newer player edit")

            from world_probe import capture, validate

            probe = capture(game.js, validate({"checks": [{"flag": "门", "equals": False}]}), 0, live=True)
            ok(probe["checks_passed"] and probe["flags"][0]["name"] == "门",
               "live world probes preserve Unicode selectors through the console")
        finally:
            game.close()


def test_mcp_world_probe() -> None:
    import mlog_mcp_http

    def simulate(**args):
        status, reply = mlog_mcp_http.dispatch({
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": "mlog_sim", "arguments": args},
        })
        result = reply["result"]
        payload = result["content"][0]["text"]
        if not ok(status == 200 and not result["isError"],
                  f"MCP reads the simulated world: {payload if result['isError'] else 'OK'}"):
            return None
        return json.loads(payload)

    flag_logic = 'setflag "gate-open" true\nstop'
    flag_query = {"flags": ["unseen"], "checks": [{"flag": "gate-open", "equals": True}]}
    for processor, expected in (("auto", True), ("micro", False)):
        data = simulate(logic=flag_logic, processor=processor, world_probe=flag_query)
        if data:
            probe = data["world_probe"]
            ok(data["processor"] == ("world" if expected else "micro") and probe["ticks"] == 60
               and probe["flags"] == [{"name": "unseen", "value": False},
                                       {"name": "gate-open", "value": expected}]
               and probe["checks_passed"] == expected
               and probe["checks"] == [{"flag": "gate-open", "equals": True,
                                        "actual": expected, "ok": expected}],
               f"{processor} processor mode returns the expected flag state and verdict")

    scene = {"world": {"size": 32}, "buildings": [{
        "name": "gate", "block": "world-processor", "x": 10, "y": 10,
        "code_inline": ('setblock block @copper-wall 14 15 @sharded 0\n'
                        'setrule waveSpacing 5 0 0 0 0\nstop'),
    }]}
    data = simulate(scene_json=scene, power="full", ticks=5, world_probe={
        "checks": [
            {"tile": {"x": 14, "y": 15}, "field": "block", "equals": "copper-wall"},
            {"tile": {"x": 14, "y": 15}, "field": "building.team", "equals": "crux"},
            {"tile": {"x": 31, "y": 31}, "field": "has_building", "equals": False},
            {"tile": {"x": 31, "y": 31}, "field": "building.health", "equals": 0},
            {"tile": {"x": 32, "y": 0}, "field": "in_bounds", "equals": False},
            {"rule": "waveSpacing", "equals": 300},
        ],
    })
    if data:
        probe = data["world_probe"]
        wall, empty, outside = probe["tiles"]
        ok(probe["width"] == probe["height"] == 32 and probe["ticks"] == 5
           and wall["block"] == "copper-wall" and wall["building"]["team"] == "sharded"
           and wall["building"]["health"] == wall["building"]["max_health"]
           and empty["in_bounds"] and empty["building"] is None and not outside["in_bounds"]
           and probe["rules"] == [{"name": "waveSpacing", "value": 300}],
           "uploaded scene probe reports native tile, building and rule state")
        ok(probe["checks_passed"] is False
           and [c["ok"] for c in probe["checks"]] == [True, False, True, False, True, True]
           and [c["actual"] for c in probe["checks"]] == ["copper-wall", "sharded", False, None, False, 300],
           "checks-only query returns all actual values and preserves mixed verdicts")


def test_mcp_marker_preview() -> None:
    import mlog_mcp_http

    logic = """makemarker text 101 12 9 false
print "Gate ready"
setmarker flushText 101 false 0 0
makemarker shape 102 20 10 false
setmarker shape 102 5 true false
makemarker line 103 17 12 false
setmarker endPos 103 27 18 0
makemarker quad 104 0 0 false
setmarker posi 104 0 5 5
setmarker posi 104 1 5 9
setmarker posi 104 2 9 9
setmarker posi 104 3 9 5
makemarker point 105 24 12 false
setmarker minimap 105 true 0 0
setmarker world 105 false 0 0
makemarker text 106 1 1 false
setmarker remove 106 0 0 0
makemarker shapeText 107 36 20 false
makemarker texture 108 38 20 false
wait 0.2
setmarker pos 101 30 9 0
stop
"""

    def call(**options):
        arguments = {"marker_preview": True, **options}
        if "scene_json" not in options:
            arguments["logic"] = logic
        return mlog_mcp_http.dispatch({
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": "mlog_sim", "arguments": arguments},
        })[1]["result"]

    first, last = call(ticks=4), call()
    errors = [r["content"][0]["text"] for r in (first, last) if r["isError"]]
    if not ok(not first["isError"] and not last["isError"],
              f"MCP returns marker frames: {', '.join(errors) or 'OK'}"):
        return
    early = json.loads(first["content"][0]["text"])["marker_preview"]
    data = json.loads(last["content"][0]["text"])
    frame = data["marker_preview"]
    markers = {marker["id"]: marker for marker in frame["markers"]}
    ok(early["tick"] == 4 and early["markers"][0]["pos"] == [12, 9]
       and frame["tick"] == 60 and data["processor"] == "world"
       and markers[101]["pos"] == [30, 9] and markers[101]["text"] == "Gate ready",
       "marker snapshot follows the requested tick, defaulting to 60")
    ok(frame["total"] == 7 and 106 not in markers
       and markers[102]["sides"] == 5 and markers[102]["fill"]
       and markers[103]["end"] == [27, 18] and markers[104]["vertices"][2]["pos"] == [9, 9]
       and markers[105]["preview"] == "hidden" and markers[105]["minimap"]
       and markers[107]["preview"] == "drawn" and markers[108]["preview"] == "unsupported",
       "marker state keeps geometry and minimap-only markers, omits removed markers")
    text_block, image = last["content"]
    png = base64.b64decode(image["data"], validate=True)
    ok(text_block["type"] == "text" and "data" not in frame
       and image["type"] == "image" and image["mimeType"] == "image/png"
       and png.startswith(b"\x89PNG\r\n\x1a\n")
       and struct.unpack(">II", png[16:24]) == (frame["image"]["width"], frame["image"]["height"]),
       "MCP supplies a separate PNG content block with the advertised dimensions")
    ok(call(steps=60)["isError"], "marker preview rejects instruction-step mode")
    scene = {"world": {"size": 32}, "buildings": [{
        "name": "markerproc", "block": "world-processor", "x": 10, "y": 10,
        "code_inline": "makemarker point 987 14 14 false\nstop",
    }]}
    uploaded = call(scene_json=scene, power="full", ticks=3)
    payload = uploaded["content"][0]["text"]
    if ok(not uploaded["isError"], f"MCP previews an uploaded scene: {payload if uploaded['isError'] else 'OK'}"):
        scene_frame = json.loads(payload)["marker_preview"]
        ok(scene_frame["bounds"]["max_x"] == 31.5 and scene_frame["total"] == 1
           and scene_frame["markers"][0]["id"] == 987,
           "uploaded scene supplies its own world dimensions and processor markers")


def test_marker_from_svg_roundtrip() -> None:
    import mlog_mcp_http

    def call(name, args):
        return mlog_mcp_http.dispatch({
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": name, "arguments": args},
        })[1]["result"]

    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="10 20 100 50">
      <g fill="#4af">
        <rect x="10" y="20" width="20" height="20"/>
        <line x1="10" y1="70" x2="110" y2="20" style="stroke: #ff660080; stroke-width: 2"/>
        <polygon points="50,30 90,30 90,55 70,40 50,55" fill="#10ef80"/>
      </g>
    </svg>"""
    response = call("marker_from_svg", {"svg": svg, "x": 3, "y": 5, "width": 20, "start_id": 8000})
    payload = response["content"][0]["text"]
    if not ok(not response["isError"], f"MCP compiles SVG to Mlog: {payload if response['isError'] else 'OK'}"):
        return
    compiled = json.loads(payload)
    response = call("mlog_sim", {
        "logic": compiled["mlog"], "ticks": compiled["preview_ticks"], "marker_preview": True,
    })
    payload = response["content"][0]["text"]
    if not ok(not response["isError"], f"generated Mlog runs in the original executor: {payload if response['isError'] else 'OK'}"):
        return
    frame = json.loads(payload)["marker_preview"]
    markers = frame["markers"]
    ok(compiled["marker_count"] == frame["total"] == 5
       and [m["id"] for m in markers] == list(range(8000, 8005))
       and [m["draw_layer"] for m in markers] == sorted({m["draw_layer"] for m in markers}),
       "SVG paint order and reserved marker IDs survive the round trip")
    rect, line, *concave = markers
    ok({tuple(v["pos"]) for v in rect["vertices"]} == {(3, 11), (3, 15), (7, 11), (7, 15)}
       and all(v["color"] == "#44aaffff" for v in rect["vertices"])
       and line["pos"] == [3, 5] and line["end"] == [23, 15]
       and line["colors"] == ["#ff660080"] * 2 and math.isclose(line["stroke"], 0.4, abs_tol=1e-6),
       "SVG viewBox, group paint, stroke alpha and Y-axis flip survive the round trip")
    ok(all(m["type"] == "quad" and len({tuple(v["pos"]) for v in m["vertices"]}) == 3
           for m in concave) and response["content"][1]["mimeType"] == "image/png",
       "concave SVG fill reaches the PNG preview as three triangles")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    fast = "--fast" in args

    test_templates_are_valid()
    test_schema_errors()
    test_v1_scenes_still_work()
    test_list_cli()
    test_compare_and_aggregate()
    test_envelope()
    test_live_rig_wiring()

    env = scenario.environment()
    if not env["ok"]:
        print("env  " + "; ".join(env.get("notes") or ["JVM unavailable"]))
    if not fast and env["ok"]:
        test_simulation(True)
        test_failed_assertion()
        test_instruction_trace_step_and_tick_modes()
        test_sim_json_trace_and_assertions()
        test_pacing_extends_default_js_timeout()
        test_grid_power_from_save()
        test_mcp_power_profile()
        test_uploaded_power_scene()
        test_native_world_processor_and_side_effects()
        test_live_logic_edit()
        test_mcp_world_probe()
        test_mcp_marker_preview()
        test_marker_from_svg_roundtrip()
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
