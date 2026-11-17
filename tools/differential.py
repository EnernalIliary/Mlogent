#!/usr/bin/env python
"""Run one scenario on both hosts and compare the two observations.

`tools/mlogsim.py` is an approximation of Mindustry; `tools/world_server.py` is
Mindustry.  A scenario is the same file for both, so running it twice -- once
offline, once live -- and diffing the *observations* (not the JSON) is the only
honest way to know whether the approximation still holds.  This module is that
diff:

    python tools/differential.py run scenes/scenarios/unit-control.json
    python tools/differential.py run SCENARIO --spec spec.json --json --level diagnostics
    python tools/differential.py parity SCENARIO

What is compared comes from `tools/observation.py` (schema + rules), never from
`json.dumps(a) == json.dumps(b)`: exact values where the hosts must agree,
tolerances where a real 60 Hz loop cannot land on the same number, and ordered
event traces with a tick tolerance.

Three outcomes, and they are not the same thing:

* both hosts ran and agree          -> ok=True
* both hosts ran and disagree       -> ok=False, simulation_real_difference
* a host did not run at all         -> ok=False, unsupported_environment (exit 3)

The third is the important one: an experiment that never ran has no result, and
reporting "the hosts differ" would be a lie (plan section 3, P1).

Environment parity is a policy, not a switch.  Two of the four comparable fields
differ *by construction* between the hosts and are reported as findings instead
of failures unless `--strict-env` is given:

* `map` -- the offline host fabricates a blank world ("blank-64"); the live host
  has whatever map is loaded.  Nothing was ever going to make these equal.
* `world_size` -- the offline world is the scene's `world.size`; the live one is
  the map's size.  This matters (nothing fits in a world smaller than the scene)
  but the scene fitting is checked when it is applied, so the number itself is
  evidence, not a verdict.

`mindustry` (major version) and `team` stay blocking: a v159 jar against a v160
one, or two teams, is not the same experiment.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import fidelity
import mlog_eval
import observation
import scenario
from mlog_eval import result

ARTIFACT_DIR = os.path.join(ROOT, "out", "_differential")

# Which parity checks block a verdict.  See the module docstring for why `map`
# and `world_size` are evidence by default; `--strict-env` promotes them.
ENV_BLOCKING = ("mindustry", "team")
ENV_BY_DESIGN = ("map", "world_size")

NEXT_STEPS = [
    "Do not change the scenario to hide the difference: the point of the diff is "
    "to learn where the approximation breaks (plan section 3, P2).",
    "Record the gap in the Fidelity Envelope (`tools/fidelity.py`) before "
    "trusting an offline run that touches this behaviour.",
    "`mlogsim` is for iteration, the live world is the tie-breaker: rerun both "
    "after any engine change.",
]


# ---------------------------------------------------------------- observations
#
# The one place that knows how a host record becomes an observation.  Both hosts
# already return the same record shape (`scenario.run_record`), so the only
# asymmetry left is who builds the rows: `observation.from_scenario()` builds
# buildings from the scene and reports no units (the offline host had none when
# the schema was written), while `from_world()` builds both from what was read
# back.  The offline record now measures both, so they are pasted in here rather
# than left as "unobserved" -- an empty unit list would silently pass the diff.


def _unit_row(row: dict) -> dict:
    """Same shape `observation.from_world()` gives a unit row."""
    out = {key: row.get(key) for key in observation.UNIT_KEYS}
    out.update({k: v for k, v in row.items() if k not in out})
    return out


def _building_row(row: dict) -> dict:
    """Same shape `observation.from_world()` gives a building row."""
    out = {key: row.get(key) for key in observation.BUILDING_KEYS}
    out.update({k: v for k, v in row.items() if k not in out})
    return out


def _sid(sc: dict) -> str:
    return str(sc.get("id") or sc.get("name") or "(unnamed)")


def _sim_env() -> dict:
    """The offline host's identity (jar major, java), when it is already known.

    Parity needs the engine version, and the offline side is the only one that
    has to be *asked*: `scenario.environment()` caches, and the sim run always
    happens first, so this is free by the time it is called.  If there is no jar
    to name, the field stays unreported and parity records a note instead of
    inventing a version.
    """
    try:
        host = scenario.environment(cached=True)
    except Exception:  # noqa: BLE001 -- an absent host is not a crash here
        return {}
    if not host.get("ok"):
        return {}
    mid, ver = scenario._host_version(host.get("jar"), host.get("java"))
    env = {}
    if mid:
        env["mindustry"] = mid
    if ver:
        env["java"] = ver
    return env


def _sim_observation(sc: dict, record: dict) -> dict:
    """The offline run as an observation, with the state it actually reached."""
    obs = observation.from_scenario(record, scenario=_sid(sc), scene=sc,
                                    env=_sim_env())
    record_units = record.get("units")
    if record_units is not None:
        obs["state"]["units"] = [_unit_row(u) for u in record_units]
    record_buildings = record.get("buildings")
    if record_buildings is not None:
        obs["state"]["buildings"] = [_building_row(b) for b in record_buildings]
    return observation.normalize(obs)


def _world_observation(record: dict) -> dict:
    """The live run as an observation (the payload is the contract's section 5)."""
    return observation.normalize(observation.from_world(record["payload"]))


def _stash(slug: str, side: str, obs: dict) -> str:
    """Write the full observation and return a repo-relative ref to it.

    `mlog_eval` keeps artifact keys ending in `_ref` even at summary level, which
    is the whole point: the envelope stays small, the evidence stays addressable.
    """
    folder = os.path.join(ARTIFACT_DIR, slug)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "%s.json" % side)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obs, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return os.path.relpath(path, ROOT).replace(os.sep, "/")


# ---------------------------------------------------------------- comparison


def _annotate(differences: list) -> list:
    """Tag every difference with the fidelity entry that explains it, if any.

    An explanation is not permission: a difference the envelope knows about is
    still a difference (`ok=False`), it just says *why* it is expected there.
    """
    out = []
    for item in differences:
        entry = dict(item)
        # `fidelity.annotate()` reads path/capability; extra keys are harmless.
        boundary = fidelity.annotate(item)
        entry["boundary"] = boundary
        entry["class"] = "known" if boundary else "unexplained"
        out.append(entry)
    return out


def _env_check(sim_obs: dict, world_obs: dict, *, strict: bool) -> dict:
    """Environment parity with the blocking policy applied."""
    env = observation.parity(sim_obs, world_obs)
    blocking = set(ENV_BLOCKING) | set(ENV_BY_DESIGN) if strict else set(ENV_BLOCKING)
    blocking_checks, by_design = [], []
    for check in env.get("checks") or []:
        item = dict(check)
        item["blocking"] = item.get("field") in blocking
        (blocking_checks if item["blocking"] else by_design).append(item)
    return {"same": all(c["ok"] for c in blocking_checks),
            "checks": blocking_checks, "notes": list(env.get("notes") or []),
            "by_design": [c for c in by_design if not c["ok"]],
            "strict": bool(strict),
            "blocking_fields": sorted(blocking)}


def _assertion_gaps(sim_rec: dict, world_rec: dict) -> list:
    """Assertions whose verdict flipped between the hosts.

    The values themselves are already compared (logs/units), so this only looks
    at the verdict: a scenario the offline host passes and the live host fails is
    a real difference even when every individual number is within tolerance.
    """
    def verdicts(record):
        out = {}
        for a in record.get("assertions") or []:
            out[str(a.get("id"))] = a
        return out

    left, right = verdicts(sim_rec), verdicts(world_rec)
    gaps = []
    for key in sorted(set(left) | set(right)):
        a, b = left.get(key), right.get(key)
        if a is None or b is None:
            gaps.append({"id": key, "sim": None if a is None else bool(a.get("ok")),
                         "world": None if b is None else bool(b.get("ok")),
                         "detail": "only one host reported this assertion"})
        elif bool(a.get("ok")) != bool(b.get("ok")):
            gaps.append({"id": key, "sim": bool(a.get("ok")),
                         "world": bool(b.get("ok")),
                         "sim_actual": a.get("actual"),
                         "world_actual": b.get("actual"),
                         "expect": a.get("expect"), "op": a.get("op"),
                         "detail": "verdict differs: sim %s, world %s"
                                   % ("pass" if a.get("ok") else "fail",
                                      "pass" if b.get("ok") else "fail")})
    return gaps


def _diagnostics(diff: dict, env: dict, gaps: list) -> list:
    """Every finding, one per entry, in the order a reader should meet them."""
    out = []
    for item in diff.get("differences") or []:
        out.append({"kind": "difference", "path": item.get("path"),
                    "rule": item.get("rule"), "left": item.get("left"),
                    "right": item.get("right"), "detail": item.get("detail") or "",
                    "boundary": item.get("boundary"), "class": item.get("class")})
    for check in env.get("checks") or []:
        if not check.get("ok"):
            out.append({"kind": "parity", "field": check.get("field"),
                        "left": check.get("left"), "right": check.get("right"),
                        "detail": check.get("detail") or "",
                        "blocking": True})
    for check in env.get("by_design") or []:
        out.append({"kind": "parity", "field": check.get("field"),
                    "left": check.get("left"), "right": check.get("right"),
                    "detail": (check.get("detail") or "") +
                              " (differs by construction: the offline host "
                              "fabricates a blank world; use --strict-env to make "
                              "this blocking)",
                    "blocking": False})
    for gap in gaps:
        out.append({"kind": "assertion", "id": gap["id"], "sim": gap["sim"],
                    "world": gap["world"], "detail": gap["detail"],
                    "blocking": True})
    for note in (diff.get("notes") or []) + (env.get("notes") or []):
        out.append({"kind": "note", "field": note.get("field"),
                    "left": note.get("left"), "right": note.get("right"),
                    "detail": note.get("detail") or "", "blocking": False})
    return out


def _message(ok: bool, diff: dict, env: dict, gaps: list, refs: dict) -> str:
    checked = int(diff.get("checked") or 0)
    if ok:
        return ("the two hosts agree: %d field(s) checked, %d difference(s); "
                "observations: %s, %s"
                % (checked, len(diff.get("differences") or []),
                   refs.get("sim"), refs.get("world")))
    parts = ["%d difference(s)" % len(diff.get("differences") or [])]
    blocking = [c for c in env.get("checks") or [] if not c.get("ok")]
    if blocking:
        parts.append("%d environment mismatch(es)" % len(blocking))
    if gaps:
        parts.append("%d assertion gap(s)" % len(gaps))
    unexplained = [d for d in diff.get("differences") or []
                   if d.get("class") == "unexplained"]
    if unexplained:
        parts.append("%d unexplained by the fidelity envelope" % len(unexplained))
    return ("the two hosts disagree (%d field(s) checked): %s"
            % (checked, ", ".join(parts)))


# ---------------------------------------------------------------- entry points


def _ms(started: float) -> int:
    """Milliseconds since `started` -- every envelope reports its own cost."""
    return int((time.time() - started) * 1000)


def _load(sc):
    """Accept a path or an already-loaded scenario."""
    return scenario.load(sc) if isinstance(sc, str) else sc


def _host_failed(envelope: dict, side: str, level: str, elapsed_ms=None,
                 extra: dict | None = None) -> dict:
    """The envelope for "this host did not produce a run".

    The difference from a disagreement is the whole point: nothing was compared,
    so nothing failed.  `extra` lets the caller keep the half that *did* run
    addressable (the offline observation is still evidence, even when the live
    host never started).
    """
    failure = envelope.get("failure_type") or "runtime_error"
    if failure not in mlog_eval.FAILURE_TYPES:
        failure = "runtime_error"
    artifacts = {"scenario": envelope.get("artifacts", {}).get("scenario"),
                 "hosts": {side: False}, "failure_host": side}
    artifacts.update(extra or {})
    return result(
        ok=False, stage="differential", failure_type=failure,
        message="the %s host produced no run: %s" % (side, envelope.get("message")),
        diagnostics=list(envelope.get("diagnostics") or []),
        next_steps=list(envelope.get("next_steps") or []),
        artifacts=artifacts,
        level=level, elapsed_ms=elapsed_ms)


def run(sc, *, spec: dict | None = None, level: str = "summary",
        strict_env: bool = False) -> dict:
    """Run both hosts, compare, and answer in the mlog_eval envelope.

    This is the function the CLI and the MCP tool both call: one signature, one
    answer shape.  `spec` overrides the comparison rules (see
    `docs/观察与差分-契约.md`, section 2); `level` only affects how much of the
    envelope is returned -- the work is the same.
    """
    started = time.time()
    scenario_obj = _load(sc)
    sid = _sid(scenario_obj)

    errors = scenario.validate(scenario_obj)
    if errors:
        return result(
            ok=False, stage="differential", failure_type="runtime_error",
            message="scenario is invalid: " + "; ".join(errors),
            diagnostics=[{"kind": "scene", "message": e} for e in errors],
            next_steps=["Fix the scenario: python tools/scenario.py check %s"
                        % (scenario_obj.get("path") or "FILE")],
            artifacts={"scenario": sid}, level=level,
            elapsed_ms=int((time.time() - started) * 1000))

    if spec is not None and not isinstance(spec, dict):
        return result(
            ok=False, stage="differential", failure_type="runtime_error",
            message="spec must be a dict, got %s" % type(spec).__name__,
            artifacts={"scenario": sid}, level=level,
            elapsed_ms=int((time.time() - started) * 1000))

    # Sim first: it is the cheap one, and a scenario broken offline must not
    # spend minutes of a live world's clock to find out.
    sim = scenario.run_record(scenario_obj, via="sim", level="diagnostics")
    if sim.get("record") is None:
        return _host_failed(sim["envelope"], "sim", level, _ms(started))
    sim_obs = _sim_observation(scenario_obj, sim["record"])
    sim_ref = _stash(scenario._slug(scenario_obj), "sim", sim_obs)
    world = scenario.run_record(scenario_obj, via="world", level="diagnostics")
    if world.get("record") is None:
        # No world (or a world that refused the scene) is an environment fact,
        # never a difference -- the caller must be able to tell "did not run"
        # from "ran and disagreed" (exit 3 vs exit 1).  The offline half ran, so
        # its observation stays addressable through the envelope.
        return _host_failed(world["envelope"], "world", level, _ms(started),
                            extra={"scenario": sid,
                                   "hosts": {"sim": True, "world": False},
                                   "sim_observation_ref": sim_ref})

    world_obs = _world_observation(world["record"])
    diff = observation.compare(sim_obs, world_obs, spec)
    diff["differences"] = _annotate(list(diff.get("differences") or []))
    env = _env_check(sim_obs, world_obs, strict=strict_env)
    gaps = _assertion_gaps(sim["record"], world["record"])
    diagnostics = _diagnostics(diff, env, gaps)

    ok = bool(diff.get("same")) and bool(env.get("same")) and not gaps
    refs = {"sim": sim_ref,
            "world": _stash(scenario._slug(scenario_obj), "world", world_obs)}

    known = len([d for d in diff["differences"] if d.get("class") == "known"])
    artifacts = {
        "scenario": sid,
        "hosts": {"sim": True, "world": True},
        "sim_observation_ref": refs["sim"],
        "world_observation_ref": refs["world"],
        "checked": int(diff.get("checked") or 0),
        "differences": len(diff["differences"]),
        "annotated": known,
        "unexplained": len(diff["differences"]) - known,
        "env": {"same": env["same"], "strict": env["strict"],
                "blocking_fields": env["blocking_fields"],
                "checks": env["checks"], "by_design": env["by_design"]},
        "assertions": {"sim_ok": bool(sim["envelope"].get("ok")),
                       "world_ok": bool(world["envelope"].get("ok")),
                       "gaps": gaps},
        "warnings": scenario.warnings(scenario_obj),
    }
    if level != "summary":
        # Full observations ride along at diagnostics/full; at summary the two
        # `_ref` keys above are what survives `mlog_eval._trim()`.
        artifacts["observations"] = {"sim": sim_obs, "world": world_obs}

    return result(
        ok=ok, stage="differential",
        failure_type=None if ok else "simulation_real_difference",
        message=_message(ok, diff, env, gaps, refs),
        diagnostics=diagnostics,
        next_steps=[] if ok else list(NEXT_STEPS),
        artifacts=artifacts, level=level,
        levels={"simulation": True, "real_runtime": True},
        elapsed_ms=int((time.time() - started) * 1000))


def parity(sc, *, strict: bool = False, level: str = "summary") -> dict:
    """Run both hosts and compare only the environments (`parity` subcommand).

    Same runs as `run()`, one question instead of two: would these two runs even
    be the same experiment?  Nothing about the state is compared.
    """
    started = time.time()
    scenario_obj = _load(sc)
    sid = _sid(scenario_obj)

    sim = scenario.run_record(scenario_obj, via="sim", level="diagnostics")
    if sim.get("record") is None:
        return _host_failed(sim["envelope"], "sim", level, _ms(started))
    world = scenario.run_record(scenario_obj, via="world", level="diagnostics")
    if world.get("record") is None:
        envelope = _host_failed(world["envelope"], "world", level, _ms(started))
        envelope.setdefault("artifacts", {})["scenario"] = sid
        return envelope

    sim_obs = _sim_observation(scenario_obj, sim["record"])
    world_obs = _world_observation(world["record"])
    env = _env_check(sim_obs, world_obs, strict=strict)
    ok = bool(env.get("same"))
    diagnostics = [{"kind": "parity", "field": c.get("field"), "left": c.get("left"),
                    "right": c.get("right"), "detail": c.get("detail") or ""}
                   for c in env["checks"] if not c.get("ok")]
    diagnostics += [{"kind": "parity", "field": c.get("field"),
                     "left": c.get("left"), "right": c.get("right"),
                     "detail": (c.get("detail") or "") + " (by construction)",
                     "blocking": False} for c in env["by_design"]]
    message = ("the two hosts would run the same experiment"
               if ok else
               "the environments disagree: " + ", ".join(
                   "%s %r vs %r" % (c["field"], c["left"], c["right"])
                   for c in env["checks"] if not c["ok"]))
    return result(
        ok=ok, stage="differential",
        failure_type=None if ok else "simulation_real_difference",
        message=message, diagnostics=diagnostics,
        next_steps=[] if ok else list(NEXT_STEPS),
        artifacts={"scenario": sid, "hosts": {"sim": True, "world": True},
                   "env": {"same": env["same"], "strict": env["strict"],
                           "blocking_fields": env["blocking_fields"],
                           "checks": env["checks"], "by_design": env["by_design"]}},
        level=level, levels={"simulation": True, "real_runtime": True},
        elapsed_ms=int((time.time() - started) * 1000))


# ---------------------------------------------------------------- CLI


def _spec_from(path: str) -> dict:
    with open(path, encoding="utf-8-sig") as fh:
        spec = json.load(fh)
    if not isinstance(spec, dict):
        raise ValueError("spec must be a JSON object, got %s" % type(spec).__name__)
    unknown = [k for k in spec if k not in ("logs", "units", "buildings", "core",
                                            "events", "env", "summary", "state")]
    if unknown:
        raise ValueError("spec has unknown section(s): " + ", ".join(sorted(unknown)))
    return spec


def _print_text(envelope: dict) -> None:
    verdict = "PASS" if envelope.get("ok") else str(envelope.get("failure_type"))
    print("%-28s %s" % (verdict, envelope.get("message") or ""))
    artifacts = envelope.get("artifacts") or {}
    for key in ("sim_observation_ref", "world_observation_ref"):
        if artifacts.get(key):
            print("  %-24s %s" % (key, artifacts[key]))
    for item in envelope.get("diagnostics") or []:
        kind = item.get("kind")
        if kind == "difference":
            print("  difference  %s [%s] %r vs %r%s"
                  % (item.get("path"), item.get("rule"), item.get("left"),
                     item.get("right"),
                     ("  <- " + item["boundary"]) if item.get("boundary") else ""))
        elif kind == "parity":
            print("  parity      %s %r vs %r%s"
                  % (item.get("field"), item.get("left"), item.get("right"),
                     "" if item.get("blocking", True) else " (by construction)"))
        elif kind == "assertion":
            print("  assertion   %s sim=%s world=%s" % (item.get("id"),
                                                        item.get("sim"),
                                                        item.get("world")))
        elif kind == "note":
            print("  note        %s" % (item.get("detail") or ""))
    for step in envelope.get("next_steps") or []:
        print("  next        %s" % step)
    print("  elapsed     %s ms" % envelope.get("elapsed_ms"))


def _cmd_run(args) -> int:
    spec = None
    if args.spec:
        try:
            spec = _spec_from(args.spec)
        except (OSError, ValueError) as exc:
            print("bad spec: %s" % exc, file=sys.stderr)
            return 1
    envelope = run(args.scenario, spec=spec, level=args.level,
                   strict_env=args.strict_env)
    if args.json:
        print(json.dumps(envelope, ensure_ascii=False, indent=2))
    else:
        _print_text(envelope)
    return scenario.exit_code(envelope)


def _cmd_parity(args) -> int:
    envelope = parity(args.scenario, strict=args.strict_env, level=args.level)
    if args.json:
        print(json.dumps(envelope, ensure_ascii=False, indent=2))
    else:
        _print_text(envelope)
    return scenario.exit_code(envelope)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="differential.py",
        description="Run a scenario offline and live, then compare the two "
                    "observations (mlog-observation/v1).")
    sub = parser.add_subparsers(dest="cmd")

    p_run = sub.add_parser("run", help="run both hosts and diff the observations")
    p_run.add_argument("scenario", help="scenario file (scenes/scenarios/*.json)")
    p_run.add_argument("--spec", help="comparison rules (JSON), see the contract")
    p_run.add_argument("--json", action="store_true", help="print the envelope")
    p_run.add_argument("--level", default="summary",
                       choices=mlog_eval.LEVELS, help="envelope detail (default summary)")
    p_run.add_argument("--strict-env", action="store_true",
                       help="make map/world_size blocking too")
    p_run.set_defaults(func=_cmd_run)

    p_par = sub.add_parser("parity", help="compare only the environments")
    p_par.add_argument("scenario", help="scenario file (scenes/scenarios/*.json)")
    p_par.add_argument("--json", action="store_true", help="print the envelope")
    p_par.add_argument("--level", default="summary",
                       choices=mlog_eval.LEVELS, help="envelope detail")
    p_par.add_argument("--strict-env", action="store_true",
                       help="make map/world_size blocking too")
    p_par.set_defaults(func=_cmd_parity)

    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
