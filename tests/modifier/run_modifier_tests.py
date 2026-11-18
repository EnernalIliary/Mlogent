#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Contract tests for tools/modifier.py + the scenario-side modifier timeline.

Three layers, cheapest first:

1. the catalogue itself (8 kinds, the five required declarations per kind);
2. pure functions -- param validation, requirements, seeded plans, ordering;
3. the schema/run integration -- load() refusals, generator constraints, and
   (when a JVM + the executor jar are present) one real run whose modifiers
   really fire, in order, at the ticks they declare.

No pytest: plain prints, exit 0 = all passed, 1 = a failure, 3 = the parts that
need an executor were skipped because this checkout has no JRE/server jar (that
is the normal state of a clean CI run; tests/scenario and tests/mindcode do the
same).
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import modifier as M  # noqa: E402
import scenario  # noqa: E402

TOOLS = os.path.join(ROOT, "tools")
SCEN = os.path.join(ROOT, "scenes", "scenarios")
TMP = os.path.join(ROOT, "out", "_modifier", "tests")

FAILS: list[str] = []
SKIPPED: list[str] = []


def ok(cond, what: str) -> bool:
    print("  %s  %s" % ("ok  " if cond else "FAIL", what))
    if not cond:
        FAILS.append(what)
    return bool(cond)


def skip(what: str) -> None:
    print("  skip  %s" % what)
    SKIPPED.append(what)


def cli(*args: str, timeout: int = 600):
    return subprocess.run([sys.executable, os.path.join(TOOLS, "scenario.py"),
                           *args], cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def mcli(*args: str):
    return subprocess.run([sys.executable, os.path.join(TOOLS, "modifier.py"),
                           *args], cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=120)


def raises(fn, needle: str) -> bool:
    """True when fn() raises with `needle` in the message."""
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 -- the message is the assertion
        if needle and needle not in str(exc):
            print("        raised %r, wanted %r" % (str(exc), needle))
            return False
        return True
    return False


def ctx(**over) -> dict:
    base = {"size": 64, "ticks": 120, "team": "sharded",
            "units": [{"type": "flare", "count": 2, "at": [10, 32]}],
            "buildings": [{"name": "ctrl", "block": "micro-processor",
                           "x": 6, "y": 32}],
            "pool": 2}
    base.update(over)
    return base


def problems(entry, c) -> list[str]:
    """validate_entry reports problems instead of raising; keep the text."""
    try:
        _, found = M.validate_entry(entry, c)
    except Exception as exc:  # noqa: BLE001 -- a raise is a problem too
        return [str(exc)]
    return list(found or [])


def _write(name: str, raw) -> str:
    os.makedirs(TMP, exist_ok=True)
    path = os.path.join(TMP, name)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(raw, fh, ensure_ascii=False, indent=2)
    return path


def scenario_dict(mods=None, ticks: int = 120, extra: dict | None = None) -> dict:
    """A minimal but genuinely runnable v2 scenario (one steerable flare)."""
    sc = {
        "id": "mod-fixture",
        "title": "modifier fixture",
        "goal": "prove a modifier fires mid-run without breaking the assertions",
        "version": 2,
        "world": {"size": 64},
        "buildings": [{"name": "ctrl", "block": "micro-processor", "x": 6, "y": 32,
                       "code_inline": ["ubind @flare",
                                       "sensor ux @unit @x",
                                       "ucontrol move 44 32 0 0",
                                       "op add c c 1"]}],
        "units": [{"type": "flare", "count": 1, "at": [10, 32], "team": "sharded"}],
        "limits": {"ticks": ticks, "timeout_s": 120.0},
        "modifiers": list(mods or []),
        "observations": [{"name": "ux", "logic": "ctrl", "var": "ux"},
                         {"name": "cycles", "logic": "ctrl", "var": "c"}],
        "assertions": [{"id": "A1", "logic": "ctrl", "var": "c", "op": "ge",
                        "value": 2},
                       {"id": "A2", "logic": "ctrl", "var": "ux", "op": "ge",
                        "value": 11}],
        "success_criteria": {"all_assertions": True},
    }
    if extra:
        sc.update(extra)
    return sc


# ---------------------------------------------------------------- catalogue


def test_catalogue() -> None:
    print("catalogue")
    ok(tuple(M.KIND_ORDER) == tuple(M.KINDS), "8 kinds in a fixed, ordered registry")
    ok(set(M.KINDS) == set(M.KIND_ORDER) and len(M.KINDS) == 8,
       "the 8 kinds are exactly the ones planning names")
    for kind in M.KIND_ORDER:
        d = M.KINDS[kind]
        ok(bool(d.get("summary")), "%s declares what it is" % kind)
        ok(isinstance(d.get("via"), (tuple, list)) and set(d["via"]) <= {"sim", "world"}
           and len(d["via"]) >= 1, "%s declares its hosts (via=%s)" % (kind, d["via"]))
        ok(isinstance(d.get("requires"), (tuple, list))
           and set(d["requires"]) <= set(M.REQUIREMENTS),
           "%s requires only known capabilities (%s)" % (kind, d["requires"]))
        ok(bool(d.get("provides")) and bool(d.get("cannot")),
           "%s declares what it can and cannot disturb" % kind)
        ok(isinstance(d.get("random"), bool),
           "%s declares whether it randomizes (random=%r)" % (kind, d.get("random")))
        ok(isinstance(d.get("params"), dict) and d["params"],
           "%s publishes a param spec" % kind)
        for name, ps in d["params"].items():
            ok(set(ps) >= {"kind", "doc", "default"},
               "%s.%s has kind/doc/default" % (kind, name))
            ok(ps["kind"] in ("int", "float", "str", "bool", "choice"),
               "%s.%s has a known type (%s)" % (kind, name, ps["kind"]))
            if ps["kind"] in ("int", "float") and name not in ("x", "y", "seed"):
                ok(ps.get("min") is not None and ps.get("max") is not None,
                   "%s.%s declares its range" % (kind, name))
            if ps["kind"] == "choice":
                ok(bool(ps.get("choices")), "%s.%s lists its choices" % (kind, name))
            ok(bool(ps.get("doc")) and isinstance(ps.get("unit") or "", str),
               "%s.%s self-describes its unit/doc" % (kind, name))
        if kind in ("unit_movement", "unit_spawn", "unit_death",
                    "control_competition"):
            ok("seed" in d["params"], "%s exposes an explicit seed" % kind)
        # every kind can at least example() itself
        ok(M.example(kind) is not None, "%s has a legal minimal example" % kind)
    ok(set(M.ENTRY_KEYS) == {"kind", "at_tick", "params"},
       "an entry is {kind, at_tick, params}")
    ok(M.MAX_ENTRIES > 0, "there is a cap on entries (MAX_ENTRIES=%d)" % M.MAX_ENTRIES)


def test_examples_validate() -> None:
    print("examples")
    for kind in M.KIND_ORDER:
        entry = M.example(kind)
        c = ctx(via="sim")
        if kind == "resource_pressure":
            c["buildings"] = [{"name": "core", "block": "core-shard", "x": 30, "y": 30}]
        norm, problems = M.validate_entry(entry, c)
        ok(not problems and norm is not None,
           "example(%s) validates (%s)" % (kind, "; ".join(problems) or "clean"))


# ---------------------------------------------------------------- validation


def test_param_validation() -> None:
    print("param validation")
    c = ctx()

    def norm(kind, params):
        return M.normalize(kind, params, c)

    ok(raises(lambda: norm("nope", {}), "unknown modifier kind"),
       "unknown kind is refused")
    ok(raises(lambda: norm("unit_spawn", {"type": "dagger", "count": 0}), "count"),
       "count=0 is refused (below min)")
    ok(raises(lambda: norm("unit_spawn", {"type": "dagger", "count": 999}), "count"),
       "count=999 is refused (above max)")
    ok(raises(lambda: norm("unit_spawn", {"type": "dagger", "count": "3"}), "count"),
       "a string count is refused (type)")
    ok(raises(lambda: norm("unit_spawn", {"type": "dagger", "bogus": 1}), "bogus"),
       "an unknown param is refused")
    ok(raises(lambda: norm("unit_spawn", {}), "type"),
       "a missing required param is refused")
    ok(raises(lambda: norm("unit_spawn", {"type": "dagger", "x": 9999}), "x"),
       "a coordinate outside world.size is refused")
    ok(raises(lambda: norm("unit_spawn", {"type": "dagger", "team": "nato"}), "team"),
       "an out-of-list choice is refused")
    ok(any("at_tick" in p for p in problems({"kind": "unit_spawn", "at_tick": -1,
                                             "params": {"type": "dagger"}}, c)),
       "a negative at_tick is refused")
    ok(any("limits.ticks" in p for p in problems(
        {"kind": "unit_spawn", "at_tick": 121,
         "params": {"type": "dagger"}}, c)),
       "at_tick past limits.ticks is refused")
    ok(any("unknown key" in p for p in problems(
        {"kind": "unit_spawn", "at_tick": 5, "params": {"type": "dagger"},
         "extra": 1}, c)),
       "an unknown entry key is refused")
    ok(any("kind" in p for p in problems({"at_tick": 5}, c)),
       "an entry without kind is refused")
    normed = norm("unit_spawn", {"type": "dagger", "x": 40, "y": 32})
    ok(normed["count"] == 1 and normed["team"] == "sharded" and normed["seed"] == 0,
       "normalize() fills defaults (count=1 team=sharded seed=0)")
    ok(isinstance(normed["seed"], int), "seeded randomness is explicit in every entry")


def test_requirements() -> None:
    print("applicability")
    no_units = ctx(units=[])
    ok(any("units" in p for p in problems({"kind": "unit_death", "at_tick": 5},
                                          no_units)),
       "unit_death is refused when the scene has no units")
    no_core = ctx(buildings=[{"name": "p", "block": "micro-processor",
                              "x": 4, "y": 4}])
    ok(any("core" in p for p in problems(
        {"kind": "resource_pressure", "at_tick": 5,
         "params": {"item": "copper"}}, no_core)),
       "resource_pressure is refused without a core")
    ok(any("sim clock" in p for p in problems(
        {"kind": "time_pressure", "at_tick": 5, "params": {"burn": 10}},
        ctx(via="world"))),
       "time_pressure is refused under via=world")
    ok(M.requirements_errors("time_pressure", ctx(via="sim")) == [],
       "time_pressure is fine under via=sim")
    ok(M.requirements_errors("building_change", ctx()) == [],
       "terrain/script are host capabilities, always available (nothing to refuse)")


# ---------------------------------------------------------------- determinism


def test_seed_reproducibility() -> None:
    print("reproducibility")
    entry = {"kind": "unit_spawn", "at_tick": 30,
             "params": {"type": "dagger", "count": 5, "x": 32, "y": 32,
                        "radius": 3, "seed": 11}}
    c = ctx()
    a = M.plan(copy.deepcopy(entry), c)
    b = M.plan(copy.deepcopy(entry), c)
    ok(a == b, "the same config + seed yields the same plan twice")
    jitter = {"kind": "unit_movement", "at_tick": 30,
              "params": {"count": 2, "jitter": 4, "seed": 11}}
    ja = M.plan(copy.deepcopy(jitter), c)
    jb = M.plan(dict(jitter, params=dict(jitter["params"], seed=12)), c)
    ok(ja != jb, "a different seed yields a different plan")
    ok(ja == M.plan(copy.deepcopy(jitter), c),
       "the same seed reproduces that plan exactly")
    ok(all(0 <= p["x"] < 64 and 0 <= p["y"] < 64 for p in a),
       "planned spawn tiles stay inside the world")
    ok(all(abs(p["x"] - 32) <= 3.5 and abs(p["y"] - 32) <= 3.5 for p in a),
       "planned spawn tiles stay inside the declared radius")
    script = M.script(copy.deepcopy(entry), c)
    ok(script["script"] == M.script(copy.deepcopy(entry), c)["script"],
       "the emitted JS is byte-identical for the same seed")
    ok(script["skip"] == 0, "unit_spawn burns no ticks")
    clock = M.script({"kind": "time_pressure", "at_tick": 10,
                      "params": {"burn": 25}}, c)
    ok(clock["skip"] == 25, "time_pressure reports the ticks it burns (skip=25)")


def test_reports_on_both_hosts() -> None:
    """A report line has to be readable where it is printed.

    The offline host captures `print(...)`; the live daemon captures only what
    the script appends to its `sb` builder.  Every kind used to hard-code
    `print`, so `--via world` ran the disturbance and then reported "NOT
    APPLIED (the host ran the script but printed no MOD line)" -- a silent
    disagreement between two hosts that no offline test could see.
    """
    print("reports")
    c = ctx()
    samples = {k: dict(v) for k, v in M._EXAMPLES.items()}
    for kind, params in samples.items():
        entry = {"kind": kind, "at_tick": 20, "params": params}
        world = M.script(copy.deepcopy(entry), dict(c, flavor="world", via="world"))
        text = world["script"]
        ok(text.count("print(") == 1,
           "%s: the world script has no bare print() outside MOD_say" % kind)
        ok("MOD_say(" in text, "%s: reports go through MOD_say" % kind)
        ok("sb.append(" in text, "%s: MOD_say reaches the daemon's sb builder" % kind)
        sim = M.script(copy.deepcopy(entry), dict(c, flavor="sim", via="sim"))
        ok("MOD_say(" in sim["script"],
           "%s: the same helper serves the offline host" % kind)

    ok("typeof sb" in M.script({"kind": "time_pressure", "at_tick": 5,
                                "params": {"burn": 1}},
                               dict(c, flavor="world", via="world"))["script"],
       "the helper picks the host at run time, not at build time")


def test_ordering() -> None:
    print("ordering")
    entries = [
        {"kind": "unit_spawn", "at_tick": 90, "params": {"type": "dagger"}},
        {"kind": "unit_spawn", "at_tick": 30, "params": {"type": "dagger"}},
        {"kind": "unit_death", "at_tick": 90, "params": {"count": 1}},
        {"kind": "time_pressure", "at_tick": 10, "params": {"burn": 1}},
    ]
    ordered = M.sort_entries(entries)
    ok([e["at_tick"] for e in ordered] == [10, 30, 90, 90],
       "entries sort by at_tick")
    ok([e["kind"] for e in ordered if e["at_tick"] == 90]
       == ["unit_spawn", "unit_death"],
       "same-tick entries keep declaration order")
    queue = scenario._modifier_queue({**scenario_dict(), "modifiers": entries},
                                     "sim")
    ok([r["at_tick"] for r in queue] == [10, 30, 90, 90],
       "the runtime queue is sorted the same way")
    ok(sorted(r["_index"] for r in queue) == [0, 1, 2, 3],
       "each record keeps the declaration index it came from")


# ---------------------------------------------------------------- schema


def test_schema_errors() -> None:
    print("schema")
    good = scenario_dict([{"kind": "unit_spawn", "at_tick": 40,
                           "params": {"type": "dagger", "count": 2,
                                      "x": 50, "y": 10}}])
    sc = scenario.load(_write("good.json", good))
    ok(len(sc["modifiers"]) == 1, "a scenario with one modifier loads")
    ok(sc["modifiers"][0]["kind"] == "unit_spawn", "the modifier survives load")

    def refused(what, mutate, needle):
        raw = copy.deepcopy(good)
        mutate(raw)
        ok(raises(lambda: scenario.load(_write("bad.json", raw)), needle), what)

    refused("an unknown kind is refused at load()",
            lambda raw: raw["modifiers"][0].update(kind="teleport_all"),
            "not a modifier")
    refused("an illegal param is refused at load()",
            lambda raw: raw["modifiers"][0]["params"].update(count=0), "count")
    refused("at_tick past limits.ticks is refused at load()",
            lambda raw: raw["modifiers"][0].update(at_tick=121), "limits.ticks")
    raw = copy.deepcopy(good)
    raw["modifiers"][0].update(kind="time_pressure")
    raw["modifiers"][0]["params"] = {"burn": 12}
    path = _write("bad-via.json", raw)
    ok(raises(lambda: scenario.load(path, via="world"), "does not run under via=world"),
       "load(via='world') refuses a sim-only modifier")
    ok(scenario.load(path, via="sim")["modifiers"][0]["kind"] == "time_pressure",
       "the same file loads fine for via=sim")
    refused("a scenario-level 'modifiers' of the wrong type is refused",
            lambda raw: raw.update(modifiers={"kind": "unit_spawn"}),
            "modifiers must be a list")
    many = [{"kind": "unit_spawn", "at_tick": 5, "params": {"type": "dagger"}}
            for _ in range(M.MAX_ENTRIES + 1)]
    refused("more than MAX_ENTRIES is refused",
            lambda raw: raw.update(modifiers=many), "at most")

    # the run-side degradation: not applicable => a note, never a fake success
    q = scenario._modifier_queue({**scenario_dict(), "modifiers": [
        {"kind": "time_pressure", "at_tick": 10, "params": {"burn": 5}}]}, "world")
    ok(q[0]["executed"] is False and q[0]["notes"],
       "_modifier_queue(via=world) records a sim-only modifier as not applicable")
    notes = scenario._modifier_notes(q)
    ok(len(notes) == 1 and "time_pressure" in notes[0] and "not applied" in notes[0],
       "that becomes a note, not a silent pass: %r" % (notes[0] if notes else ""))


# ---------------------------------------------------------------- generator


def test_generator_constraints() -> None:
    print("generator")
    sc = scenario.generate({"template": "unit-control",
                            "params": {"targets": 4, "distractors": 2,
                                       "obstacles": 3, "processors": 2,
                                       "disturb_at": 60, "start_x": 12,
                                       "spread": 3.0, "size": 80, "ticks": 200},
                            "seed": 5})
    ok(sc["version"] == 2 and sc["world"]["size"] == 80, "the generated world is 80x80")
    units = [u for u in sc["units"] if u["type"] == "flare"]
    ok(sum(u["count"] for u in units) == 4, "targets=4 became 4 flare units")
    routers = [b for b in sc["buildings"] if b["block"] == "router"]
    ok(len(routers) == 3, "obstacles=3 became 3 router tiles")
    procs = [b for b in sc["buildings"] if b["block"] == "micro-processor"]
    ok(len(procs) == 2, "processors=2 became 2 micro-processors")
    ok(sum(1 for b in procs if b.get("code_inline")) == 1,
       "exactly one processor carries the program")
    ok(all(0 <= b["x"] < 80 and 0 <= b["y"] < 80 for b in sc["buildings"]),
       "every building is inside the world")
    cy = 80 // 2
    ok(all(abs(b["y"] - cy) >= 3 for b in routers),
       "no obstacle sits on the corridor the steered units travel")
    ok(len(sc["modifiers"]) == 1, "distractors>0 emits exactly one modifier")
    ok(sc["modifiers"][0]["at_tick"] == 60
       and sc["modifiers"][0]["params"]["count"] == 2,
       "the modifier fires at disturb_at with distractors count")
    sc0 = scenario.generate({"template": "unit-control", "params": {"distractors": 0},
                             "seed": 5})
    ok(sc0["modifiers"] == [], "distractors=0 emits no modifier at all")
    ok(raises(lambda: scenario.generate({"template": "nope"}), "unknown template"),
       "an unknown template is refused")
    ok(raises(lambda: scenario.generate({"template": "unit-control",
                                         "params": {"targets": 99}}), "targets"),
       "an out-of-range knob is refused")
    ok(raises(lambda: scenario.generate({"template": "unit-control",
                                         "params": {"warp": 1}}), "warp"),
       "an unknown knob is refused")
    ok(raises(lambda: scenario.generate({"template": "unit-control",
                                         "params": {"disturb_at": 500,
                                                    "ticks": 100}}), "disturb_at"),
       "disturb_at >= ticks is refused")
    ok(raises(lambda: scenario.generate({"template": "resource-drain",
                                         "params": {"stock": 10,
                                                    "drain": 20}}), "drain"),
       "draining more than the stock is refused")
    drain = scenario.generate({"template": "resource-drain", "params": {"stock": 90,
                                                                       "drain": 30}})
    ok(drain["modifiers"][0]["params"]["amount"] == 30,
       "resource-drain passes the amount through")
    ok(scenario.validate(drain) == [], "the generated dict validates clean")


def test_generator_determinism() -> None:
    print("generator determinism")
    a = scenario.generate({"template": "unit-control", "params": {"obstacles": 4},
                           "seed": 21})
    b = scenario.generate({"template": "unit-control", "params": {"obstacles": 4},
                           "seed": 21})
    ok(json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True),
       "the same template + params + seed is byte-identical")
    c = scenario.generate({"template": "unit-control", "params": {"obstacles": 4},
                           "seed": 22})
    ok([bb for bb in b["buildings"] if bb["block"] == "router"]
       != [bb for bb in c["buildings"] if bb["block"] == "router"],
       "a different seed moves the obstacles")
    path = _write("gen.json", a)
    ok(scenario.load(path)["id"] == a["id"], "the generated file loads back")
    first = scenario._write_scenario(a, os.path.join(TMP, "gen-a.json"))
    second = scenario._write_scenario(b, os.path.join(TMP, "gen-b.json"))
    with open(first, "rb") as fa, open(second, "rb") as fb:
        ok(fa.read() == fb.read(), "the written JSON is byte-identical too")
    with open(first, "rb") as fh:
        blob = fh.read()
    ok(not blob.startswith(b"\xef\xbb\xbf") and b"\r\n" not in blob,
       "generated files are UTF-8 without BOM and LF-only")


# ---------------------------------------------------------------- CLI


def test_cli() -> None:
    print("cli")
    r = mcli("list")
    ok(r.returncode == 0, "modifier.py list exits 0")
    rows = [ln for ln in r.stdout.splitlines() if ln.strip()]
    ok(all(k in r.stdout for k in M.KIND_ORDER), "list names all 8 kinds")
    ok(len(rows) >= 9, "list prints a header plus one row per kind")
    r = mcli("show", "unit_death")
    ok(r.returncode == 0 and "unit_death" in r.stdout, "show unit_death exits 0")
    ok("cannot" in r.stdout.lower(), "show prints what the kind cannot do")
    r = mcli("show", "nope")
    ok(r.returncode == 2 and "unknown modifier kind" in r.stderr,
       "show <unknown> exits 2 with a clear message")
    r = mcli("selftest")
    ok(r.returncode == 0, "modifier.py selftest exits 0")
    ok("failed" in r.stdout or "ok" in r.stdout, "selftest reports its checks")
    r = cli("generate", "--template", "unit-control",
            "--params", '{"targets": 3, "distractors": 1}', "--seed", "4",
            "--out", os.path.join(TMP, "cli-gen.json"), "--json")
    ok(r.returncode == 0, "scenario.py generate exits 0")
    payload = json.loads(r.stdout)
    ok(payload["ok"] and payload["units"] == 3, "generate reports the units it made")
    ok(len(payload["modifiers"]) == 1, "generate reports the modifier it planted")
    r = cli("generate", "--list")
    ok(r.returncode == 0 and "resource-drain" in r.stdout,
       "generate --list prints the templates")


# ---------------------------------------------------------------- real run


def test_real_run() -> None:
    print("real run")
    sc = scenario.load(_write("run.json", scenario_dict([
        {"kind": "unit_spawn", "at_tick": 40,
         "params": {"type": "dagger", "count": 2, "x": 50, "y": 10}},
        {"kind": "time_pressure", "at_tick": 40, "params": {"burn": 10}},
    ], ticks=120)))
    env = scenario.run(sc, level="diagnostics")
    ok(env["ok"], "the scenario passes on the executor (%s)" % env.get("message"))
    mods = (env.get("artifacts") or {}).get("modifiers") or []
    ok(len(mods) == 2, "the envelope records both modifiers")
    ok([m["kind"] for m in mods] == ["unit_spawn", "time_pressure"],
       "records keep the declared order for the same tick")
    ok(all(m["executed"] for m in mods),
       "both really executed (%s)" % [(m["kind"], m["executed"]) for m in mods])
    ok(mods[0]["applied_at_tick"] == 40 and mods[1]["applied_at_tick"] == 40,
       "each fired before its at_tick (%s)"
       % [m["applied_at_tick"] for m in mods])
    ok(mods[1]["burned"] == 10, "time_pressure reports the 10 ticks it burned")
    ok(any("MOD" in ln for ln in mods[0]["lines"]),
       "the host printed a MOD line the runner could see")
    ok(not (env.get("artifacts") or {}).get("notes"),
       "no notes when everything applied")

    late = scenario.load(_write("run-late.json", scenario_dict([
        {"kind": "unit_spawn", "at_tick": 60,
         "params": {"type": "dagger", "count": 1, "x": 50, "y": 10}}], ticks=60)))
    env = scenario.run(late, level="diagnostics")
    mods = (env.get("artifacts") or {}).get("modifiers") or []
    ok(len(mods) == 1 and mods[0]["executed"] and mods[0]["applied_at_tick"] == 60,
       "a modifier on the very last tick still fires")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    fast = "--fast" in args

    test_catalogue()
    test_examples_validate()
    test_param_validation()
    test_requirements()
    test_seed_reproducibility()
    test_reports_on_both_hosts()
    test_ordering()
    test_schema_errors()
    test_generator_constraints()
    test_generator_determinism()
    test_cli()

    env = scenario.environment()
    if not env["ok"]:
        print("env  " + "; ".join(env.get("notes") or ["JVM unavailable"]))
    if not fast and env["ok"]:
        test_real_run()
    else:
        skip("real run (%s)" % ("--fast" if fast else "no JVM/jar"))

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
