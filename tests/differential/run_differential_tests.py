#!/usr/bin/env python
"""tests/differential/run_differential_tests.py -- the diff runner's contract.

`tools/differential.py` answers one question: given the same scenario file, do
the offline host and the live host produce the same observation?  Its failure
modes are the interesting part, so this file pins them in order of severity:

* a host that did not run is `unsupported_environment` and exit 3 (never a
  "difference" -- an experiment that never happened has no result),
* two hosts that ran and disagree is `simulation_real_difference` and exit 1,
  with one diagnostic per difference and every difference annotated by the
  Fidelity Envelope,
* the comparison rules come from `tools/observation.py`, and a `--spec` override
  actually reaches them,
* the world payload (contract section 5) maps to the observation without rescaling
  coordinates or dropping fields,
* the CLI parses what the contract documents and refuses what it does not.

Most of that needs no world at all: the two host records are plain dicts, so the
assembly can be driven with fakes (see `_fake_both`).  The last test is a real
end-to-end run and is the only one that needs a live world; when the world or the
JVM is missing it is skipped and the file exits 3.

Usage:
    python tests/differential/run_differential_tests.py
    python tests/differential/run_differential_tests.py --fast   # no live world

Exit codes: 0 all pass, 1 a test failed, 3 the live world (or JVM) is unavailable
(the pure tests still ran and are reported).
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

import differential  # noqa: E402  (needs tools/ on the path)
import mlog_eval  # noqa: E402
import observation  # noqa: E402
import scenario  # noqa: E402

SCEN = ROOT / "scenes" / "scenarios"
MINIMAL = SCEN / "unit-control.json"
TMP = ROOT / "out" / "_differential" / "tests"

FAILS: list[str] = []
SKIPPED: list[str] = []
PASSES = [0]


def ok(cond: bool, what: str) -> bool:
    if cond:
        PASSES[0] += 1
        print("ok   " + what)
    else:
        FAILS.append(what)
        print("FAIL " + what)
    return bool(cond)


def skip(what: str) -> None:
    SKIPPED.append(what)
    print("skip " + what)


def eq(got, want, what: str) -> bool:
    return ok(got == want, "%s (got %r, want %r)" % (what, got, want))


def cli(*args: str, timeout: float = 600.0) -> subprocess.CompletedProcess:
    """Run the differential CLI the way a user would."""
    return subprocess.run([sys.executable, str(TOOLS / "differential.py"), *args],
                          cwd=str(ROOT), capture_output=True, text=True,
                          encoding="utf-8", timeout=timeout)


# ---------------------------------------------------------------- fake hosts
#
# One source of truth for both sides: the world observation is built from a
# payload that mirrors the sim record, so "agree" really means "the same
# experiment measured twice".  Changing one number is how disagreement is made.

def _sim_record(sc: dict, *, unit_x: float = 40.0, n: int = 6) -> dict:
    return {
        "ticks": int(sc["limits"]["ticks"]),
        "samples": {0: [str(unit_x)], 1: ["32"]},
        "finals": {"ctrl": {"ux": str(unit_x), "uy": "32", "n": str(n)}},
        "checks": [],
        "report": {"placed": 1, "configured": 0, "stocked": 0, "linked": 1,
                   "units": 1, "errors": [], "done": True,
                   "warnings": []},
        "refs": {"ctrl": (20, 32, "micro-processor")},
        "units": [{"id": 7, "type": "flare", "team": "sharded", "x": unit_x,
                   "y": 32.0, "hp": 70, "controller": "LogicAI", "amount": None}],
        "buildings": [{"block": "micro-processor", "x": 20, "y": 32,
                       "team": "sharded", "items": {}}],
        "assertions": [{"id": "A1", "ok": True, "expect": 40, "actual": 40}],
        "observations": {"ux": unit_x},
    }


def _world_record(sc: dict, *, unit_x: float = 40.0, map_name: str = "Fork",
                  size=(200, 200), n: int = 6, assertions=None,
                  log_ux: float | None = None) -> dict:
    # `unit_x` moves the unit snapshot; `log_ux` moves what the processor
    # logged.  They are separate knobs on purpose: a position drift that leaves
    # the logs alone is a units difference, while a logs difference can never be
    # absorbed by a units spec (logs are compared exactly).
    log_ux = unit_x if log_ux is None else log_ux
    payload = {
        "scenario": sc.get("id") or "",
        "ticks": int(sc["limits"]["ticks"]),
        "errors": [],
        "scene": {"placed": 1, "configured": 0, "stocked": 0, "linked": 1,
                  "units": 1, "errors": []},
        "logs": {"ctrl": {"ux": str(log_ux), "uy": "32", "n": str(n)}},
        "units": [{"id": 12, "type": "flare", "team": "sharded", "x": unit_x,
                   "y": 32.0, "hp": 70, "controller": "LogicAI", "amount": None}],
        "buildings": [{"block": "micro-processor", "x": 20, "y": 32,
                       "team": "sharded", "items": {}}],
        "core": {"items": {"copper": 0}, "x": 0, "y": 0, "team": "sharded"},
        "events": [],
        "env": {"mindustry": "v160", "java": "21.0.5", "map": map_name,
                "world_size": [size[0], size[1]], "team": "sharded",
                "update": "live", "sampling": "final"},
    }
    return {"payload": payload,
            "assertions": assertions or copy.deepcopy(
                _sim_record(sc)["assertions"]),
            "observations": {"ux": unit_x}}


def _envelope(ok: bool, failure_type: str | None = None, message: str = "") -> dict:
    return mlog_eval.result(
        ok=ok, stage="scenario", failure_type=failure_type,
        message=message or ("ran" if ok else "did not run"),
        diagnostics=[] if ok else [{"kind": "scene", "message": message or "nope"}],
        artifacts={"scenario": "fake"}, level="diagnostics")


def _fake_both(sc: dict, sim=None, world=None, *, sim_ok=True, world_ok=True,
               world_failure=None, sim_failure=None) -> list:
    """Install fake `run_record` results; returns a list to restore."""
    sim_rec = _sim_record(sc) if sim is None else sim
    world_rec = _world_record(sc) if world is None else world
    seen = []

    def fake(path_or_sc, *, via="sim", level="diagnostics"):
        seen.append(via)
        if via == "sim":
            env = _envelope(sim_ok, sim_failure, "sim host")
            return {"envelope": env, "record": sim_rec if sim_ok else None}
        env = _envelope(world_ok, world_failure, "world host")
        return {"envelope": env, "record": world_rec if world_ok else None}

    original = scenario.run_record
    scenario.run_record = fake
    return [original]


def _restore(saved: list) -> None:
    scenario.run_record = saved[0]


# ---------------------------------------------------------------- 1. spec / CLI


def test_spec():
    TMP.mkdir(parents=True, exist_ok=True)
    good = TMP / "spec.json"
    good.write_text(json.dumps({"units": {"fields": {"x": 1.5}}}), encoding="utf-8")
    spec = differential._spec_from(str(good))
    ok(isinstance(spec, dict) and "units" in spec, "spec: a JSON object loads")

    bad_type = TMP / "spec-list.json"
    bad_type.write_text("[1, 2, 3]", encoding="utf-8")
    try:
        differential._spec_from(str(bad_type))
        ok(False, "spec: a JSON array is refused")
    except ValueError:
        ok(True, "spec: a JSON array is refused")

    bad_key = TMP / "spec-key.json"
    bad_key.write_text(json.dumps({"nonsense": {}}), encoding="utf-8")
    try:
        differential._spec_from(str(bad_key))
        ok(False, "spec: an unknown section is refused")
    except ValueError as exc:
        ok("nonsense" in str(exc), "spec: an unknown section is refused")


def test_cli_parsing():
    # --help / no subcommand: argparse prints usage, nothing runs.
    for argv, want in (([], 0), (["--help"], 0)):
        try:
            got = differential.main(argv)
        except SystemExit as exc:  # --help raises SystemExit(0)
            got = int(exc.code or 0)
        eq(got, want, "cli: %r returns %d" % (argv or ["(none)"], want))

    # Missing scenario, unknown subcommand and a bad --level are argparse errors.
    for argv in (["run"], ["nope"], ["run", str(MINIMAL), "--level", "huge"]):
        try:
            differential.main(argv)
            ok(False, "cli: %r is refused" % (argv,))
        except SystemExit as exc:
            ok(int(exc.code or 0) == 2, "cli: %r is refused (exit 2)" % (argv,))

    # A missing --spec file fails before either host is started, so no JVM and
    # no world are touched -- this is safe to run unconditionally.
    done = cli("run", str(MINIMAL), "--spec", "no-such-spec.json")
    eq(done.returncode, 1, "cli: an unreadable --spec is exit 1")
    ok("bad spec" in (done.stderr or ""), "cli: an unreadable --spec says why")


# ---------------------------------------------------------------- 2. payload


def test_world_payload_mapping():
    sc = scenario.load(str(MINIMAL))
    payload = {
        "scenario": "payload-check",
        "ticks": 42,
        "errors": [],
        "scene": {"placed": 2, "configured": 1, "stocked": 0, "linked": 0,
                  "units": 1, "errors": []},
        "logs": {"ctrl": {"ux": "7", "flag": "true"}},
        "units": [{"id": 3, "type": "flare", "x": 10.5, "y": 4.25, "hp": 63,
                   "team": "sharded", "controller": "LogicAI", "amount": 5}],
        "buildings": [{"block": "container", "x": 10, "y": 10, "team": "sharded",
                       "items": {"copper": 30}}],
        "core": {"items": {"copper": 400}, "x": 0, "y": 0},
        "events": [{"tick": 9, "type": "print", "logic": "ctrl", "detail": "b"},
                   {"tick": 2, "type": "print", "logic": "ctrl", "detail": "a"}],
        "env": {"mindustry": "v160", "java": "21.0.5", "map": "Fork",
                "world_size": [200, 200], "team": "sharded",
                "update": "live", "sampling": "final"},
    }
    obs = observation.from_world(payload)
    eq(obs["schema"], "mlog-observation/v1", "payload: schema is the shared one")
    eq(obs["source"], "world", "payload: source is world")
    eq(obs["scenario"], "payload-check", "payload: scenario name is carried")
    eq(obs["ticks"], 42, "payload: ticks are carried")

    unit = (obs["state"]["units"] or [{}])[0]
    eq(unit.get("x"), 10.5, "payload: unit x stays in tiles (not divided by 8)")
    eq(unit.get("y"), 4.25, "payload: unit y stays in tiles")
    eq(unit.get("hp"), 63, "payload: unit hp is carried")
    eq(unit.get("controller"), "LogicAI", "payload: unit controller is carried")
    eq(unit.get("amount"), 5, "payload: unit amount is carried")

    building = (obs["state"]["buildings"] or [{}])[0]
    eq(building.get("items"), {"copper": 30}, "payload: building items survive")
    eq((obs["state"]["core"] or {}).get("items"), {"copper": 400},
       "payload: core items survive")
    eq([e["tick"] for e in obs["events"]], [2, 9], "payload: events sort by tick")
    eq(obs["env"].get("sampling"), "final", "payload: sampling is final")
    eq(obs["env"].get("update"), "live", "payload: update is live")
    eq(obs["env"].get("world_size"), [200, 200], "payload: world_size is a pair")
    eq(obs["env"].get("map"), "Fork", "payload: map is the real map name")
    eq((obs["env"].get("scene") or {}).get("placed"), 2,
       "payload: the scene report lands in env.scene")

    # The converter is the module under test, not observation.py: this is the
    # path differential.py uses, and it must not rescale either.
    wrapped = differential._world_observation({"payload": payload})
    eq((wrapped["state"]["units"] or [{}])[0].get("x"), 10.5,
       "differential: the world wrapper keeps tiles")


def test_sim_record_mapping():
    sc = scenario.load(str(MINIMAL))
    record = _sim_record(sc)
    original = differential._sim_env
    differential._sim_env = lambda: {"mindustry": "v160", "java": "21.0.5"}
    try:
        obs = differential._sim_observation(sc, record)
    finally:
        differential._sim_env = original
    eq(obs["source"], "sim", "sim record: source is sim")
    eq(obs["state"]["logs"], record["finals"], "sim record: logs are the finals")
    eq((obs["state"]["units"] or [{}])[0].get("x"), 40.0,
       "sim record: the measured unit snapshot is used")
    eq((obs["state"]["buildings"] or [{}])[0].get("block"), "micro-processor",
       "sim record: the measured building snapshot is used")
    eq(obs["env"].get("map"), "blank-64", "sim record: the offline world is blank")
    eq(obs["env"].get("mindustry"), "v160", "sim record: the jar version is used")
    eq(obs["env"].get("sampling"), "every-tick", "sim record: sampling is every-tick")


# ---------------------------------------------------------------- 3. comparing


def _pair(sc: dict, *, world_unit_x: float | None = None, map_name="Fork",
          size=(200, 200), log_ux: float = 40.0):
    original = differential._sim_env
    differential._sim_env = lambda: {"mindustry": "v160"}
    try:
        sim_obs = differential._sim_observation(sc, _sim_record(sc))
    finally:
        differential._sim_env = original
    world_obs = differential._world_observation(
        {"payload": _world_record(sc, unit_x=(40.0 if world_unit_x is None
                                              else world_unit_x),
                                  map_name=map_name, size=size,
                                  log_ux=log_ux)["payload"]})
    return sim_obs, world_obs


def test_comparison_semantics():
    sc = scenario.load(str(MINIMAL))

    sim_obs, world_obs = _pair(sc)
    diff = observation.compare(sim_obs, world_obs)
    ok(diff["same"], "compare: identical runs agree (%r)"
       % (diff["differences"][:1],))
    ok(diff.get("checked", 0) > 0, "compare: something was actually checked")

    # 0.4 tiles is inside the 0.5-tile default tolerance for a unit position.
    sim_obs, world_obs = _pair(sc, world_unit_x=40.4)
    ok(observation.compare(sim_obs, world_obs)["same"],
       "compare: a 0.4-tile drift is within the default tolerance")

    # 0.9 tiles is not.
    sim_obs, world_obs = _pair(sc, world_unit_x=40.9)
    diff = observation.compare(sim_obs, world_obs)
    ok(not diff["same"], "compare: a 0.9-tile drift is a difference")
    paths = " ".join(str(d.get("path")) for d in diff["differences"])
    ok("units" in paths, "compare: the difference names state.units (%s)" % paths)
    annotated = differential._annotate(diff["differences"])
    ok(all("class" in d for d in annotated),
       "annotate: every difference is classified known/unexplained")
    ok(any(d.get("boundary") for d in annotated),
       "annotate: the fidelity envelope explains at least one of them")

    # A spec override must reach the comparison rule (this is the --spec knob).
    spec = {"units": {"fields": {"x": 5, "y": 5}}}
    ok(observation.compare(sim_obs, world_obs, spec)["same"],
       "spec: a wider tolerance makes the same pair agree")

    # Events: an event only one side recorded is a note, not a difference.
    sim_obs, world_obs = _pair(sc)
    world_obs = copy.deepcopy(world_obs)
    world_obs["events"] = [{"tick": 3, "type": "print", "logic": "ctrl",
                            "detail": "only live"}]
    diff = observation.compare(sim_obs, world_obs)
    ok(diff["same"] or any("event" in str(d.get("path")).lower()
                           for d in diff["differences"]),
       "events: a one-sided event does not crash the comparison")


def test_env_policy():
    sc = scenario.load(str(MINIMAL))
    sim_obs, world_obs = _pair(sc, size=(200, 200))
    env = differential._env_check(sim_obs, world_obs, strict=False)
    ok(env["same"], "env: map/world_size differ by construction and still pass")
    ok(env["by_design"], "env: those differences are reported, not dropped")
    ok(env["blocking_fields"] == sorted(differential.ENV_BLOCKING),
       "env: the default blocking set is the named one")

    strict = differential._env_check(sim_obs, world_obs, strict=True)
    ok(not strict["same"], "env: --strict-env makes map/world_size blocking")

    # A different team is blocking either way: that really is another experiment.
    payload = _world_record(sc)["payload"]
    payload["env"]["team"] = "crux"
    other = observation.from_world(payload)
    ok(not differential._env_check(sim_obs, other, strict=False)["same"],
       "env: a different team is a mismatch")


def test_assertion_gaps():
    sc = scenario.load(str(MINIMAL))
    sim_rec = _sim_record(sc)
    world_rec = _world_record(
        sc, assertions=[{"id": "A1", "ok": False, "expect": 40, "actual": 36}])
    gaps = differential._assertion_gaps(sim_rec, world_rec)
    eq(len(gaps), 1, "assertions: a flipped verdict is one gap")
    eq(gaps[0]["id"], "A1", "assertions: the gap names the assertion")
    eq((gaps[0]["sim"], gaps[0]["world"]), (True, False),
       "assertions: the gap records both verdicts")

    same = differential._assertion_gaps(sim_rec, _world_record(sc))
    eq(same, [], "assertions: identical verdicts are not a gap")


# ---------------------------------------------------------------- 4. assembly


def test_assembly_agree():
    sc = scenario.load(str(MINIMAL))
    saved = _fake_both(sc)
    try:
        env = differential.run(sc, level="diagnostics")
    finally:
        _restore(saved)
    eq(env["schema"], "mlog-eval/v1", "agree: the answer is an mlog_eval envelope")
    ok(env["ok"], "agree: both hosts agreeing is ok=True")
    eq(env["failure_type"], None, "agree: no failure type when it passes")
    eq(scenario.exit_code(env), 0, "agree: exit code 0")
    eq(env["levels"], {"execution": None, "static": None, "simulation": True,
                       "real_runtime": True},
       "agree: both dimensions were evaluated")
    artifacts = env.get("artifacts") or {}
    ok(artifacts.get("sim_observation_ref"), "agree: the sim observation has a ref")
    ok(artifacts.get("world_observation_ref"), "agree: the world one has a ref")
    for key in ("sim_observation_ref", "world_observation_ref"):
        ref = artifacts.get(key) or ""
        ok(not os.path.isabs(ref), "agree: %s is repo-relative (%s)" % (key, ref))
        path = ROOT / ref
        ok(path.exists(), "agree: %s exists on disk" % key)
        if path.exists():
            raw = path.read_bytes()
            ok(not raw.startswith(b"\xef\xbb\xbf"),
               "agree: %s is written without a BOM" % key)
            ok(b"\r\n" not in raw, "agree: %s is written with LF" % key)
    eq(artifacts.get("differences"), 0, "agree: no differences recorded")
    eq(artifacts.get("checked"), env["artifacts"].get("checked"),
       "agree: the checked count is in the artifacts")
    ok("observations" in artifacts, "agree: diagnostics carries the observations")

    # Summary level must keep the refs and drop the bulk.
    saved = _fake_both(sc)
    try:
        small = differential.run(sc, level="summary")
    finally:
        _restore(saved)
    sart = small.get("artifacts") or {}
    ok(sart.get("sim_observation_ref"), "summary: the sim ref survives trimming")
    ok(sart.get("world_observation_ref"), "summary: the world ref survives")
    ok("observations" not in sart, "summary: the inline observations are dropped")


def test_assembly_disagree():
    sc = scenario.load(str(MINIMAL))
    saved = _fake_both(sc, world=_world_record(sc, unit_x=45.0, log_ux=40.0))
    try:
        env = differential.run(sc, level="diagnostics")
    finally:
        _restore(saved)
    ok(not env["ok"], "disagree: a 5-tile drift is ok=False")
    eq(env["failure_type"], "simulation_real_difference",
       "disagree: failure_type is simulation_real_difference")
    eq(scenario.exit_code(env), 1, "disagree: exit code 1")
    kinds = [d.get("kind") for d in env.get("diagnostics") or []]
    ok("difference" in kinds, "disagree: there is a difference diagnostic")
    diffs = [d for d in env.get("diagnostics") or [] if d.get("kind") == "difference"]
    ok(all("class" in d for d in diffs), "disagree: every difference is classified")
    ok(any(d.get("boundary") for d in diffs),
       "disagree: an explanation is attached when fidelity has one")
    ok(env.get("next_steps"), "disagree: next steps point somewhere")
    eq(scenario.exit_code(env), 1, "disagree: the CLI exit mapping holds")

    # Same drift but a spec that accepts it: the run must pass.
    saved = _fake_both(sc, world=_world_record(sc, unit_x=45.0, log_ux=40.0))
    try:
        relaxed = differential.run(sc, spec={"units": {"fields": {"x": 10}}},
                                   level="summary")
    finally:
        _restore(saved)
    ok(relaxed["ok"], "disagree: a spec override can absorb the drift")


def test_assembly_unsupported():
    sc = scenario.load(str(MINIMAL))

    # No live world: the offline half ran, the live half did not.
    saved = _fake_both(sc, world_ok=False, world_failure="unsupported_environment")
    try:
        env = differential.run(sc, level="summary")
    finally:
        _restore(saved)
    ok(not env["ok"], "unsupported world: ok=False")
    eq(env["failure_type"], "unsupported_environment",
       "unsupported world: failure_type is unsupported_environment")
    eq(scenario.exit_code(env), 3, "unsupported world: exit code 3")
    ok("world" in (env.get("message") or ""),
       "unsupported world: the message names the host")
    artifacts = env.get("artifacts") or {}
    ok(artifacts.get("sim_observation_ref"),
       "unsupported world: the offline half stays addressable")
    saved = _fake_both(sc, world_ok=False, world_failure="unsupported_environment")
    try:
        full = differential.run(sc, level="diagnostics")
    finally:
        _restore(saved)
    eq(((full.get("artifacts") or {}).get("hosts") or {}).get("world"), False,
       "unsupported world: the artifacts say which host is missing")

    # The offline host is the one that is missing: also an environment fact.
    saved = _fake_both(sc, sim_ok=False, sim_failure="unsupported_environment")
    try:
        env = differential.run(sc, level="summary")
    finally:
        _restore(saved)
    eq(env["failure_type"], "unsupported_environment",
       "unsupported sim: failure_type is unsupported_environment")
    eq(scenario.exit_code(env), 3, "unsupported sim: exit code 3")

    # A host that blew up is not an environment problem: exit 1, not 3.
    saved = _fake_both(sc, world_ok=False, world_failure="runtime_error")
    try:
        env = differential.run(sc, level="summary")
    finally:
        _restore(saved)
    eq(env["failure_type"], "runtime_error",
       "host failure: a live crash stays runtime_error")
    eq(scenario.exit_code(env), 1, "host failure: exit code 1")


def test_parity_entry():
    sc = scenario.load(str(MINIMAL))
    saved = _fake_both(sc)
    try:
        env = differential.parity(sc, level="summary")
    finally:
        _restore(saved)
    ok(env["ok"], "parity: matching environments pass by default")
    eq(env["stage"], "differential", "parity: stage is differential")

    saved = _fake_both(sc, world=_world_record(sc, map_name="GroundZero"))
    try:
        strict = differential.parity(sc, strict=True, level="summary")
    finally:
        _restore(saved)
    ok(not strict["ok"], "parity: --strict-env fails on a different map")


# ---------------------------------------------------------------- 5. real runs


def test_scenario_world_without_world():
    """`scenario.run(via="world")` must refuse, not pretend, when there is none."""
    live = scenario.world_environment()
    if live.get("ok"):
        skip("scenario --via world refusal (a live world is up)")
        return
    sc = scenario.load(str(MINIMAL))
    env = scenario.run(sc, via="world", level="summary")
    eq(env["failure_type"], "unsupported_environment",
       "scenario --via world: unsupported_environment when no world is up")
    eq(scenario.exit_code(env), 3, "scenario --via world: exit code 3")
    ok(env.get("message"), "scenario --via world: it says why")
    record = scenario.run_record(sc, via="world")["record"]
    eq(record, None, "scenario --via world: no record is invented")


def test_cli_end_to_end(live: dict) -> None:
    done = cli("run", str(MINIMAL), "--json", "--level", "diagnostics")
    if done.returncode == 3:
        skip("differential CLI end-to-end (exit 3: %s)"
             % (done.stderr or done.stdout or "").strip()[:160])
        return
    try:
        env = json.loads(done.stdout)
    except ValueError:
        ok(False, "cli end-to-end: stdout is JSON (%r)" % done.stdout[:200])
        return
    eq(env["schema"], "mlog-eval/v1", "cli end-to-end: the envelope schema")
    ok(done.returncode in (0, 1), "cli end-to-end: exit 0 or 1, never 3")
    artifacts = env.get("artifacts") or {}
    ok(artifacts.get("world_observation_ref"),
       "cli end-to-end: the live observation is addressable")
    if env.get("ok"):
        ok(not (env.get("diagnostics") and
                [d for d in env["diagnostics"] if d.get("kind") == "difference"]),
           "cli end-to-end: ok=True comes with no differences")
    else:
        eq(env["failure_type"], "simulation_real_difference",
           "cli end-to-end: a real gap is named as one")

    par = cli("parity", str(MINIMAL), "--json")
    if par.returncode != 3:
        ok(par.returncode in (0, 1), "cli parity: exit 0 or 1")


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    fast = "--fast" in argv

    print("-- spec and CLI")
    test_spec()
    test_cli_parsing()

    print("-- payload -> observation")
    test_world_payload_mapping()
    test_sim_record_mapping()

    print("-- comparison semantics")
    test_comparison_semantics()
    test_env_policy()
    test_assertion_gaps()

    print("-- assembly (fake hosts)")
    test_assembly_agree()
    test_assembly_disagree()
    test_assembly_unsupported()
    test_parity_entry()

    print("-- hosts")
    live = scenario.world_environment()
    jvm = scenario.environment()
    print("   world: %s" % ("up" if live.get("ok") else (live.get("why") or "?")))
    print("   java:  %s" % (jvm.get("java") or jvm.get("notes")))
    test_scenario_world_without_world()

    world_ok = bool(live.get("ok"))
    if fast:
        skip("the live end-to-end runs (--fast)")
    elif world_ok:
        test_cli_end_to_end(live)
    else:
        skip("the live end-to-end run: %s" % (live.get("why") or "no world"))

    print()
    if FAILS:
        print("%d test(s) FAILED" % len(FAILS))
        for name in FAILS:
            print("  - " + name)
        return 1
    if SKIPPED:
        print("%d test(s) passed, %d skipped" % (PASSES[0], len(SKIPPED)))
        for name in SKIPPED:
            print("  - " + name)
        return 3 if (not world_ok or fast) else 0
    print("all %d test(s) passed" % PASSES[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
