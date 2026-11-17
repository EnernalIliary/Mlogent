#!/usr/bin/env python
"""Contract tests for tools/observation.py -- pure data, no JVM, no jar.

The suite pins the schema shape, the four comparison rules (exact / tolerance /
match / ordered), the missing-value rules, both converters, `parity()` and the
envelope `report()` returns.  Every assertion prints one line; a failure also
prints the concrete differences the comparison produced, so a red run says what
changed instead of just "assertion failed".

No `json.dumps(a) == json.dumps(b)` anywhere: the document is compared by the
contract's own rules, and one test proves that documents which are structurally
equal but stored in a different order (dict keys, unit lists, events) pass while
a whole-document string compare of the same pair would fail.

Run:  python -X utf8 tests/observation/run_observation_tests.py
Exit: 0 and "all observation tests passed" on success, 1 on any failure.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import observation as obs  # noqa: E402

try:                                     # details contain "Δ", keep cp936 alive
    sys.stdout.reconfigure(errors="replace")
    sys.stderr.reconfigure(errors="replace")
except (AttributeError, ValueError):     # pragma: no cover -- odd stream
    pass

PASSED = 0
FAILS: list[str] = []

SECTIONS: list[str] = []


def section(name):
    """Start a named group of assertions."""
    SECTIONS.append(name)
    print("\n-- " + name)




# ------------------------------------------------------------------ harness

def ok(cond, what, detail=""):
    """Record one assertion; print the evidence when it fails."""
    global PASSED
    if cond:
        PASSED += 1
        print("ok   " + what)
    else:
        FAILS.append(what)
        print("FAIL " + what)
        for line in str(detail or "").splitlines():
            print("       " + line)
    return bool(cond)


def eq(actual, expected, what):
    return ok(actual == expected, what,
              "" if actual == expected
              else "expected: %r\n   actual: %r" % (expected, actual))


def show(res):
    """Readable dump of one compare() result, used as failure evidence."""
    lines = []
    for item in res["differences"]:
        lines.append("%s [%s] %r != %r  -- %s"
                     % (item["path"], item["rule"], item["left"],
                        item["right"], item["detail"]))
    for note in res.get("notes") or []:
        lines.append("note %s: %s"
                     % (note.get("path") or note.get("field"),
                        note.get("detail")))
    if not lines:
        lines.append("(no differences, checked=%d)" % res["checked"])
    return "\n".join(lines)


def agrees(a, b, what, spec=None):
    """Assert the two observations are the same under `spec`; return the result."""
    res = obs.compare(a, b, spec)
    ok(res["same"] and not res["differences"], what, show(res))
    return res


def disagrees(a, b, path, what, spec=None, rule=None, detail=None):
    """Assert a difference exists at `path` (optionally with rule/detail)."""
    res = obs.compare(a, b, spec)
    hit = None
    for item in res["differences"]:
        if item["path"] != path:
            continue
        if rule is not None and item["rule"] != rule:
            continue
        if detail is not None and detail not in item["detail"]:
            continue
        hit = item
        break
    ok(hit is not None and res["same"] is False, what, show(res))
    return hit


def unchanged(a, b, path, what, spec=None):
    """Assert nothing at `path` is reported as a difference."""
    res = obs.compare(a, b, spec)
    hits = [item for item in res["differences"] if item["path"] == path]
    ok(not hits and res["same"], what, show(res))
    return res


def note_for(res, path):
    for note in res.get("notes") or []:
        if note.get("path") == path:
            return note
    return None


# ------------------------------------------------------------------ fixtures

def event(tick, kind="print", logic="ctrl", detail="hi"):
    return {"tick": tick, "type": kind, "logic": logic, "detail": detail}


def unit(**kw):
    row = {"id": 1, "type": "flare", "team": "sharded",
           "controller": "LogicAI", "x": 10.0, "y": 20.0, "hp": 90.0,
           "amount": 0}
    row.update(kw)
    return row


def building(**kw):
    row = {"block": "container", "x": 10, "y": 10, "team": "sharded",
           "items": {"copper": 30}}
    row.update(kw)
    return row


def sim_obs(**kw):
    """A small but complete `sim` observation, both hosts default to it."""
    base = dict(
        scenario="unit-control", ticks=120,
        summary={"ok": True, "errors": [], "instructions": 900,
                 "elapsed_ms": 12},
        state={"logs": {}, "units": [], "buildings": [], "core": None},
        events=[],
        env={"mindustry": "v160.7", "java": "21.0.5", "map": "blank-64",
             "world_size": [64, 64], "team": "sharded", "update": "all",
             "sampling": "every-tick"})
    base.update(kw)
    return obs.make("sim", **base)


def env_of(**kw):
    env = {"mindustry": "v160.7", "java": "21.0.5", "map": "blank-64",
           "world_size": [64, 64], "team": "sharded", "update": "all",
           "sampling": "every-tick"}
    env.update(kw)
    return env


# ------------------------------------------------------------------ schema

section("schema, make(), normalize()")

plain = obs.make("sim", scenario="s", ticks=10)
eq(set(plain), {"schema", "source", "scenario", "ticks", "summary", "state",
                "events", "env"},
   "make() produces exactly the eight contract keys")
eq(plain["schema"], obs.SCHEMA, "make() stamps mlog-observation/v1")
eq(plain["source"], "sim", "make() keeps the source name")
eq(set(plain["summary"]), {"ok", "errors", "instructions", "elapsed_ms"},
   "summary carries the four contract keys")
eq(set(plain["state"]), {"logs", "units", "buildings", "core"},
   "state carries the four contract keys")
eq(set(plain["env"]), {"mindustry", "java", "map", "world_size", "team",
                       "update", "sampling"},
   "env carries the seven contract keys")
eq(plain["state"]["core"], None, "core defaults to null instead of missing")
ok(plain["state"]["units"] == [] and plain["events"] == [],
   "absent arrays become [], never a dropped key")
eq(plain["ticks"], 10, "ticks is an int")
eq(obs.make("sim", scenario="s", ticks=12.0)["ticks"], 12,
   "make() coerces a float tick count to int")

try:
    obs.make("jvm", scenario="s", ticks=1)
    ok(False, "make() rejects a source outside SOURCES")
except ValueError:
    ok(True, "make() rejects a source outside SOURCES")

sorted_events = obs.make("sim", scenario="s", ticks=1,
                         events=[event(7), event(2), event(5)])
eq([e["tick"] for e in sorted_events["events"]], [2, 5, 7],
   "make() stores events in ascending tick order")

stringified = obs.make("sim", scenario="s", ticks=1,
                       state={"logs": {"p": {"n": 12, "ratio": 0.5}}})
eq(stringified["state"]["logs"]["p"], {"n": "12", "ratio": "0.5"},
   "log values are strings, as mlog gives them")

raw = {
    "schema": obs.SCHEMA, "source": "sim", "scenario": "s", "ticks": 1,
    "summary": {"ok": True, "errors": [], "instructions": None,
                "elapsed_ms": None},
    "state": {"logs": {}, "units": [], "buildings": [], "core": None},
    "events": [event(9), event(3)],
    "env": env_of(),
}
before = copy.deepcopy(raw)
once = obs.normalize(raw)
eq(raw, before, "normalize() never mutates its argument")
eq(obs.normalize(once), once, "normalize() is idempotent")
eq([e["tick"] for e in once["events"]], [3, 9],
   "normalize() sorts events by tick")


# ------------------------------------------------------------------ exact

section("exact rule")

base_logs = sim_obs(state={"logs": {"ctrl": {"x": "7", "flag": "true"}}})
res = agrees(base_logs,
             sim_obs(state={"logs": {"ctrl": {"x": "7", "flag": "true"}}}),
             "identical observations compare equal")
ok(res["checked"] >= 2, "exact mode counts the fields it inspected",
   "checked=%d" % res["checked"])

agrees(base_logs,
       sim_obs(state={"logs": {"ctrl": {"flag": "true", "x": "7"}}}),
       "key order inside a log table is irrelevant")

agrees(base_logs, sim_obs(state={"logs": {"ctrl": {"x": " 7 ", "flag": "true"}}}),
       "exact strings are compared after strip()")

agrees(base_logs, sim_obs(state={"logs": {"ctrl": {"x": 7, "flag": "true"}}}),
       "a numeric string equals the same number (7 == 7.0 == \"7\")")

disagrees(base_logs, sim_obs(state={"logs": {"ctrl": {"x": "8", "flag": "true"}}}),
          "state.logs.ctrl.x", "a different log value is a difference",
          rule="exact")

disagrees(base_logs, sim_obs(state={"logs": {"ctrl": {"x": "7"}}}),
          "state.logs.ctrl.flag", "a key missing on one side is a difference",
          detail="key missing on the right")

disagrees(sim_obs(state={"units": [unit(alive=True)]}),
          sim_obs(state={"units": [unit(alive=1)]}),
          "state.units[flare#0].alive", "bool and number never compare equal",
          rule="exact")

left_extra = sim_obs(state={"logs": {}, "extra": {"a": 1}})
right_extra = sim_obs(state={"logs": {}, "extra": {"a": 2}})
disagrees(left_extra, right_extra, "state.extra.a",
          "a section outside the schema is compared exactly, not ignored")

missing_section = copy.deepcopy(base_logs)
del missing_section["state"]["buildings"]
disagrees(base_logs, missing_section, "state.buildings",
          "a dropped section is a difference, not an unobserved field",
          detail="section missing on the right")


# ------------------------------------------------------------------ tolerance

section("tolerance rule")

agrees(sim_obs(state={"units": [unit(x=12.5)]}),
       sim_obs(state={"units": [unit(x=12.9)]}),
       "unit x within the 0.5 tile tolerance compares equal")

hit = disagrees(sim_obs(state={"units": [unit(x=12.5)]}),
                sim_obs(state={"units": [unit(x=13.1)]}),
                "state.units[flare#0].x",
                "unit x beyond the 0.5 tile tolerance is a difference",
                rule="tolerance", detail="|Δ|=0.6")
ok(hit is not None and "0.5" in hit["detail"],
   "the detail names the tolerance and the delta",
   "" if hit is None else hit["detail"])

agrees(sim_obs(state={"units": [unit(hp=90.0)]}),
       sim_obs(state={"units": [unit(hp=94.4)]}),
       "hp within 5% of the larger value compares equal")

hit = disagrees(sim_obs(state={"units": [unit(hp=90.0)]}),
                sim_obs(state={"units": [unit(hp=96.0)]}),
                "state.units[flare#0].hp",
                "hp beyond 5% is a difference", rule="tolerance",
                detail="5% of 96")
ok(hit is not None and "4.8" in hit["detail"],
   "relative tolerance reports the absolute limit it derived",
   "" if hit is None else hit["detail"])

wide = {"units": {"fields": {"x": 2.0}}}
agrees(sim_obs(state={"units": [unit(x=12.5)]}),
       sim_obs(state={"units": [unit(x=14.0)]}),
       "a caller spec can widen the x tolerance to 2.0", spec=wide)
disagrees(sim_obs(state={"units": [unit(x=12.5)]}),
          sim_obs(state={"units": [unit(x=14.0)]}),
          "state.units[flare#0].x",
          "the default 0.5 tolerance still rejects the same pair")

disagrees(sim_obs(state={"units": [unit(hp=None)]}),
          sim_obs(state={"units": [unit(hp=90.0)]}),
          "state.units[flare#0].hp",
          "null against a number is a difference, never within tolerance")

core_spec = {"core": {"mode": "tolerance", "tolerance": 1.0}}
core_a = sim_obs(state={"core": {"items": {"copper": 500}, "x": 20, "y": 20}})
agrees(core_a,
       sim_obs(state={"core": {"items": {"copper": 500.6}, "x": 20, "y": 20}}),
       "tolerance section mode accepts a 0.6 item drift", spec=core_spec)
hit = disagrees(core_a,
                sim_obs(state={"core": {"items": {"copper": 502},
                                        "x": 20, "y": 20}}),
                "state.core.items.copper",
                "tolerance section mode still reports a 2.0 drift",
                spec=core_spec, rule="tolerance", detail="|Δ|=2")
ok(hit is not None and hit["left"] == 500 and hit["right"] == 502,
   "the difference keeps both observed values",
   "" if hit is None else "%r vs %r" % (hit["left"], hit["right"]))


# ------------------------------------------------------------------ match

section("match rule")

flare = unit(type="flare", x=10.0)
mono = unit(id=2, type="mono", x=30.0)
pair_a = sim_obs(state={"units": [flare, mono]})
agrees(pair_a, sim_obs(state={"units": [copy.deepcopy(mono),
                                       copy.deepcopy(flare)]}),
       "match pairs units by type regardless of list order")

hit = disagrees(pair_a, sim_obs(state={"units": [copy.deepcopy(flare)]}),
                "state.units[mono#0]",
                "an entry only on the left is a difference", rule="match",
                detail="left only")
ok(hit is not None and hit["left"] is None and hit["right"] is None,
   "an unpaired entry has null on both sides, the label carries the key",
   "" if hit is None else "%r/%r" % (hit["left"], hit["right"]))

agrees(sim_obs(state={"units": [unit(id=1)]}),
       sim_obs(state={"units": [unit(id=99)]}),
       "unit id is never compared across hosts")

disagrees(sim_obs(state={"units": [unit(amount=0)]}),
          sim_obs(state={"units": [unit(amount=5)]}),
          "state.units[flare#0].amount",
          "a unit field the spec does not mention is still compared",
          rule="exact")

box = building()
disagrees(sim_obs(state={"buildings": [box]}),
          sim_obs(state={"buildings": [building(items={"copper": 31})]}),
          "state.buildings[container@10,10].items.copper",
          "building items compare exactly", rule="exact")

moved = obs.compare(sim_obs(state={"buildings": [building(x=10)]}),
                    sim_obs(state={"buildings": [building(x=20)]}))
eq(len(moved["differences"]), 2,
   "a building on a new tile is one left-only plus one right-only entry")
disagrees(sim_obs(state={"buildings": [building(x=10)]}),
          sim_obs(state={"buildings": [building(x=20)]}),
          "state.buildings[container@10,10]",
          "the left-only building keeps its own label")
disagrees(sim_obs(state={"buildings": [building(x=10)]}),
          sim_obs(state={"buildings": [building(x=20)]}),
          "state.buildings[container@20,10]",
          "the right-only building keeps its own label")

two_boxes = sim_obs(state={"buildings": [building(),
                                         building(x=12, y=12)]})
one_box = sim_obs(state={"buildings": [building()]})
disagrees(two_boxes, one_box, "state.buildings[container@12,12]",
          "a second container of the same block is a separate entry",
          detail="left only")

same_block_twice = sim_obs(state={"buildings": [building(),
                                                building(x=12, y=12,
                                                         items={"copper": 31})]})
disagrees(two_boxes, same_block_twice,
          "state.buildings[container@12,12].items.copper",
          "two containers of the same block pair by (block, x, y)")
pair_res = obs.compare(two_boxes, same_block_twice)
eq(len(pair_res["differences"]), 1,
   "pairing by (block, x, y) leaves one field difference, not two unpaired "
   "entries")


# ---------------------------------------------------- structural values / null

section("structural values, missing keys and null")

core_coords = sim_obs(state={"core": {"items": {},
                                      "x": 20, "y": 20,
                                      "coords": [1, 2]}})
agrees(core_coords,
       sim_obs(state={"core": {"items": {}, "x": 20, "y": 20,
                               "coords": [1, 2]}}),
       "an array value inside a field compares element by element")

disagrees(core_coords,
          sim_obs(state={"core": {"items": {}, "x": 20, "y": 20,
                                  "coords": [1, 3]}}),
          "state.core.coords[1]",
          "an array element that moved is reported by index", rule="exact")

disagrees(core_coords,
          sim_obs(state={"core": {"items": {}, "x": 20, "y": 20,
                                  "coords": [1, 2, 3]}}),
          "state.core.coords", "a longer array is a difference",
          detail="length")

disagrees(core_coords,
          sim_obs(state={"core": {"items": {}, "x": 20, "y": 20,
                                  "coords": {"x": 1}}}),
          "state.core.coords", "array vs object is a structure difference",
          detail="structure differs")

disagrees(sim_obs(state={"core": {"items": {"copper": 500}, "x": 20, "y": 20}}),
          sim_obs(state={"core": {"items": {"copper": 500, "lead": 1},
                                  "x": 20, "y": 20}}),
          "state.core.items.lead",
          "a key added to an item table is reported by name",
          detail="key missing on the left")

agrees(sim_obs(state={"core": {"items": {}, "x": None, "y": None}}),
       sim_obs(state={"core": {"items": {}, "x": None, "y": None}}),
       "null on both sides is the same absence")

core_note = obs.compare(sim_obs(state={"core": None}),
                        sim_obs(state={"core": {"items": {}, "x": 40,
                                                "y": 40}}))
ok(core_note["same"], "a section one host does not observe is not a difference",
   show(core_note))
note = note_for(core_note, "state.core")
ok(note is not None and "unobserved" in note["detail"],
   "the unobserved section is recorded as a note with a reason",
   "" if note is None else str(note))


# ------------------------------------------------------------------ events

section("ordered events")

print_event = event(10, "print", detail="hello")
shoot_event = event(20, "shoot", detail="target")
agrees(sim_obs(events=[print_event, shoot_event]),
       sim_obs(events=[event(10, "print", detail="hello"),
                       event(20, "shoot", detail="target")]),
       "identical event streams compare equal")

agrees(sim_obs(events=[event(20, "shoot"), event(10, "print")]),
       sim_obs(events=[event(10, "print"), event(20, "shoot")]),
       "event order on the wire is normalized before comparing")

agrees(sim_obs(events=[{"tick": 10, "type": "print", "logic": "c",
                        "detail": "hello"},
                       event(20, "shoot")]),
       sim_obs(events=[{"detail": "hello", "tick": 10, "logic": "c",
                        "type": "print"},
                       {"detail": "hi", "tick": 20, "logic": "ctrl",
                        "type": "shoot"}]),
       "event field order is irrelevant")

inserted = obs.compare(sim_obs(events=[print_event, shoot_event]),
                       sim_obs(events=[print_event, event(15, "ucontrol"),
                                       shoot_event]))
ok(inserted["same"] and not inserted["differences"],
   "an inserted event keeps the stream equal", show(inserted))
note = note_for(inserted, "events[1]")
ok(note is not None and "insertion" in note["detail"],
   "the insertion is recorded as a note, not swallowed",
   "" if note is None else str(note))

swapped = obs.compare(sim_obs(events=[event(12, "print"),
                                      event(12, "shoot")]),
                      sim_obs(events=[event(12, "shoot"),
                                      event(12, "print")]))
ok(swapped["same"] is False,
   "two events on the same tick keep their relative order", show(swapped))
disagrees(sim_obs(events=[event(12, "print"), event(12, "shoot")]),
          sim_obs(events=[event(12, "shoot"), event(12, "print")]),
          "events[0]", "the reordered event is named by index",
          detail="missing on the right")

agrees(sim_obs(events=[event(12, "print")]),
       sim_obs(events=[event(15, "print")]),
       "a tick inside the 3-tick tolerance compares equal")

hit = disagrees(sim_obs(events=[event(12, "print")]),
                sim_obs(events=[event(16, "print")]),
                "events[0].tick",
                "a tick beyond the tolerance is a difference",
                rule="ordered", detail="tolerance 3")
ok(hit is not None and hit["left"] == 12 and hit["right"] == 16,
   "the tick difference keeps both ticks",
   "" if hit is None else "%r vs %r" % (hit["left"], hit["right"]))

disagrees(sim_obs(events=[event(10, "print", detail="a")]),
          sim_obs(events=[event(10, "print", detail="b")]),
          "events[0].detail", "a different event payload is a difference")

disagrees(sim_obs(events=[event(10, "print"), event(12, "sensor")]),
          sim_obs(events=[event(10, "print")]),
          "events[1]", "an event missing on the right is a difference",
          detail="missing on the right")

optional = obs.compare(sim_obs(events=[]),
                       sim_obs(events=[event(10, "print")]))
ok(optional["same"], "a host with no event log is not a failure",
   show(optional))
note = note_for(optional, "events")
ok(note is not None and "no events" in note["detail"],
   "the empty event stream is explained as a sampling limit",
   "" if note is None else str(note))

disagrees(sim_obs(events=[event(10, "print")]),
          sim_obs(events=[event(10, "print"), event(15, "ucontrol")]),
          "events", "events mode exact turns the insertion into a difference",
          spec={"events": {"mode": "exact"}}, detail="length")

agrees(sim_obs(events=[event(10, "print")]),
       sim_obs(events=[event(12, "print")]),
       "events mode tolerance compares ticks with its own tolerance",
       spec={"events": {"mode": "tolerance", "tolerance": 2}})


# ------------------------------------------------------------------ parity

section("parity(): same experiment?")

par = obs.parity(sim_obs(env=env_of(mindustry="v160.7")),
                 sim_obs(env=env_of(mindustry="v160.4")))
ok(par["same"], "parity compares the mindustry major version only")
eq({c["field"] for c in par["checks"]},
   {"mindustry", "map", "world_size", "team"},
   "parity checks the contract env fields")
eq(par["notes"], [], "identical host drives produce no note")

par = obs.parity(sim_obs(env=env_of(mindustry="v159.9")),
                 sim_obs(env=env_of(mindustry="v160.7")))
ok(not par["same"], "a different mindustry major version fails parity")
major = [c for c in par["checks"] if c["field"] == "mindustry"]
ok(major and "major" in major[0]["detail"],
   "the parity check says which majors disagreed",
   "" if not major else str(major[0]))

par = obs.parity(sim_obs(env=env_of()), sim_obs(env=env_of(map="blank-32")))
ok(not par["same"], "a different map fails parity")
ok(any(c["field"] == "map" and not c["ok"] for c in par["checks"]),
   "the map mismatch is one named check")

par = obs.parity(sim_obs(env=env_of()),
                 sim_obs(env=env_of(world_size=[32, 32])))
ok(not par["same"], "a different world size fails parity")

par = obs.parity(sim_obs(env=env_of(world_size=[64, 64])),
                 sim_obs(env=env_of(world_size=[64.0, 64])))
ok(par["same"], "an integral world size compares equal as 64 vs 64.0")

par = obs.parity(sim_obs(env=env_of()), sim_obs(env=env_of(team="crux")))
ok(not par["same"], "a different team fails parity")

# `update` is how the host drives the clock: the offline host steps it, the live
# host runs the real loop.  Failing on that would fail every honest sim/world
# pair, so it is a note -- and the note still names both values.
par = obs.parity(sim_obs(env=env_of(update="all")),
                 sim_obs(env=env_of(update="live")))
ok(par["same"], "a different update mode is a note, not a parity failure")
ok(any(n["field"] == "update" and "all" in str(n["left"])
       and "live" in str(n["right"]) for n in par["notes"]),
   "the update note shows both values")

par = obs.parity(sim_obs(env=env_of(sampling="every-tick")),
                 sim_obs(env=env_of(sampling="final")))
ok(par["same"], "a different sampling is a note, not a parity failure")
ok(len(par["notes"]) == 1 and par["notes"][0]["field"] == "sampling",
   "the sampling difference is recorded as a note")

# "We did not record it" is not "the two environments disagree": the field is
# surfaced as a note so it stays visibly unverified instead of silently passing.
par = obs.parity(sim_obs(env=env_of(map=None)), sim_obs(env=env_of()))
ok(par["same"], "a field only one side reports does not fail parity")
ok(any(n["field"] == "map" and "only one side" in n["detail"]
       for n in par["notes"]),
   "an unverifiable field is surfaced as a note, not passed silently")
ok(not any(c["field"] == "map" for c in par["checks"]),
   "an unverifiable field is not counted as a passed check")


# ------------------------------------------------------------------ report

section("report(): the mlog_eval envelope")

good_a = sim_obs(state={"logs": {"ctrl": {"x": "7"}}})
good_b = sim_obs(state={"logs": {"ctrl": {"x": "7"}}})
rep = obs.report(good_a, good_b, scenario="unit-control", level="diagnostics")
ok(rep["ok"] is True, "agreeing observations report ok=True")
eq(rep.get("failure_type"), None, "a passing report has no failure_type")
eq(rep["stage"], "observation", "the report is staged as observation")
ok(str(rep["message"]).startswith("observations agree"),
   "the message says the observations agree", rep["message"])
eq(rep["next_steps"], [], "a passing report asks for no next step")
ok(int((rep.get("artifacts") or {}).get("checked") or 0) > 0,
   "the artifacts expose how many fields were compared",
   str(rep.get("artifacts")))

bad = obs.report(good_a, sim_obs(state={"logs": {"ctrl": {"x": "8"}}}),
                 level="diagnostics")
ok(bad["ok"] is False, "disagreeing observations report ok=False")
eq(bad["failure_type"], "simulation_real_difference",
   "a real disagreement is failure_type=simulation_real_difference")
ok(str(bad["message"]).startswith("observations disagree"),
   "the message says the observations disagree", bad["message"])
diags = bad.get("diagnostics") or []
hit = [d for d in diags if d.get("kind") == "difference"
       and d.get("path") == "state.logs.ctrl.x"]
ok(bool(hit), "the diagnostic names the differing path", str(diags))
ok(bool(hit) and hit[0].get("rule") == "exact" and hit[0].get("detail"),
   "every diagnostic carries its rule and a readable detail",
   "" if not hit else str(hit[0]))
ok(any("Fidelity Envelope" in step for step in bad["next_steps"]),
   "next_steps send the reader to the Fidelity Envelope, not to the scene",
   str(bad["next_steps"]))

parity_only = obs.report(sim_obs(env=env_of()),
                         sim_obs(env=env_of(map="blank-32")),
                         level="diagnostics")
ok(parity_only["ok"] is False, "an env mismatch alone fails the report")
ok(any(d.get("kind") == "parity" and d.get("field") == "map"
       for d in parity_only.get("diagnostics") or []),
   "the parity mismatch is a diagnostic of its own")

noted = obs.report(sim_obs(events=[]), sim_obs(events=[event(10, "print")]),
                   level="diagnostics")
ok(noted["ok"] is True, "a note alone does not fail the report")
ok(any(d.get("kind") == "note" for d in noted.get("diagnostics") or []),
   "notes appear in diagnostics so they are never invisible")

trimmed = obs.report(good_a, sim_obs(state={"logs": {"ctrl": {"x": "8"}}}))
ok("diagnostics" not in trimmed, "summary level trims the diagnostics")
ok("differences" not in (trimmed.get("artifacts") or {}),
   "summary level keeps only *_ref artifacts")

res = obs.compare(good_a, good_b)
ok(set(res) >= {"same", "checked", "differences"},
   "compare() returns the contract keys")
ok(isinstance(res.get("notes"), list),
   "compare() also returns the notes it set aside")
try:
    obs.compare(good_a, good_b, {"logs": {"mode": "fuzzy"}})
    ok(False, "compare() rejects an unknown rule")
except ValueError:
    ok(True, "compare() rejects an unknown rule")


# ------------------------------------------------- no whole-document compare

section("documents equal despite different storage order")

doc_a = sim_obs(state={"logs": {"a": {"x": "1"}, "b": {"y": "2"}},
                       "units": [unit(type="mono", x=30.0),
                                 unit(type="flare", x=10.0)]},
                events=[event(30, "shoot"), event(10, "print")])
doc_b = sim_obs(state={"logs": {"b": {"y": "2"}, "a": {"x": "1"}},
                       "units": [unit(type="flare", x=10.0),
                                 unit(type="mono", x=30.0)]},
                events=[event(10, "print"), event(30, "shoot")])
agrees(doc_a, doc_b,
       "structurally equal documents in a different storage order compare equal")
ok(json.dumps(doc_a) != json.dumps(doc_b),
   "the raw json of those two documents differs, so the pass is rule-based",
   "json.dumps would have reported a false difference")


# ------------------------------------------------------------------ converters

section("from_scenario() / from_world()")

SIM = {
    "ticks": 240,
    "samples": {0: ["24", "36"], 60: ["36", "36"]},
    "finals": {"ctrl": {"ux": "36.5", "uy": "32", "n": "60"}},
    "checks": [
        {"logic": "ctrl", "var": "n", "expect": 60, "actual": "60",
         "ok": True},
        {"logic": "ctrl", "var": "ux", "expect": 32, "actual": "36.5",
         "ok": False},
    ],
    "refs": {"ctrl": (20, 32, "micro-processor")},
    "report": {"placed": 1, "configured": 0, "stocked": 0, "linked": 1,
               "units": 1, "errors": [], "rows": []},
}
SCENE = {
    "id": "unit-control",
    "world": {"size": 64},
    "units": [{"type": "flare", "team": "sharded", "x": 34, "y": 36}],
    "buildings": [{"name": "ctrl", "block": "micro-processor", "x": 20,
                   "y": 32, "team": "sharded"}],
}

sim = obs.from_scenario(SIM, scenario="unit-control")
eq(sim["source"], "sim", "from_scenario() marks the observation as sim")
eq(sim["ticks"], 240, "from_scenario() keeps the simulated tick count")
eq(sim["state"]["logs"]["ctrl"]["ux"], "36.5",
   "from_scenario() takes the processor variables from finals")
ok(sim["state"]["units"] is None,
   "from_scenario() reports no unit snapshot as null, not as []")
eq(sim["state"]["buildings"],
   [{"block": "micro-processor", "x": 20, "y": 32, "team": None,
     "items": None}],
   "from_scenario() builds building rows from refs()")
eq(sim["env"]["scene"]["checks"], {"total": 2, "failed": 1},
   "from_scenario() counts the scene checks into env.scene")
eq((sim["env"]["scene"]["warnings"], sim["env"]["scene"]["done"]),
   ([], None), "from_scenario() passes scene warnings and done through")
eq(sim["env"]["update"], "all", "the offline host runs update=all")
eq(sim["env"]["sampling"], "every-tick",
   "the offline host records every tick")
eq(sim["env"]["mindustry"], None,
   "from_scenario() stays JVM-free and leaves the version to the caller")

with_scene = obs.from_scenario(SIM, scenario="unit-control", scene=SCENE)
eq(with_scene["env"]["map"], "blank-64",
   "the scene supplies the map name")
eq(with_scene["env"]["world_size"], [64, 64],
   "the scene supplies the world size")
eq(with_scene["env"]["team"], "sharded", "the scene supplies the team")
eq(with_scene["state"]["buildings"][0]["team"], "sharded",
   "the scene supplies the building team")

eq(obs.from_scenario(SIM, ticks=99)["ticks"], 99,
   "from_scenario(ticks=...) overrides the record")
empty = obs.from_scenario({})
eq((empty["ticks"], empty["state"]["logs"], empty["state"]["buildings"]),
   (0, {}, []), "from_scenario({}) degrades to an empty observation")
try:
    obs.from_scenario("nope")
    ok(False, "from_scenario() rejects a non-dict record")
except TypeError:
    ok(True, "from_scenario() rejects a non-dict record")


def world_payload(**kw):
    payload = {
        "scenario": "unit-control", "ticks": 240, "errors": [],
        "logs": {"ctrl": {"ux": 36.5, "uy": 32, "n": 60}},
        "units": [{"id": 7, "type": "flare", "team": "sharded",
                   "controller": "LogicAI", "x": 34.0, "y": 36.0,
                   "hp": 90.0, "amount": 0}],
        "buildings": [{"block": "micro-processor", "x": 20, "y": 32,
                       "team": "sharded", "items": None}],
        "core": {"items": {"copper": 500}, "x": 40, "y": 40},
        "events": [{"tick": 10, "type": "print", "logic": "ctrl",
                    "detail": "hi"}],
        "env": env_of(update="live", sampling="final"),
        "scene": {"placed": 1, "configured": 0, "stocked": 0, "linked": 1,
                  "units": 1, "errors": []},
    }
    payload.update(kw)
    return payload


world = obs.from_world(world_payload())
eq(world["source"], "world", "from_world() marks the observation as world")
eq(world["env"]["update"], "live", "the world host runs update=live")
eq(world["env"]["sampling"], "final",
   "the world host samples only the final state")
eq(set(world["state"]["units"][0]),
   {"id", "type", "team", "controller", "x", "y", "hp", "amount"},
   "from_world() gives every unit the full set of schema keys")
eq(world["summary"]["ok"], True, "no payload errors means summary.ok")

sparse = obs.from_world(world_payload(units=[{"type": "flare"}]))
eq(sparse["state"]["units"][0],
   {"id": None, "type": "flare", "team": None, "controller": None,
    "x": None, "y": None, "hp": None, "amount": None},
   "missing unit fields become null, never a dropped key")
eq(obs.from_world(world_payload(buildings=[{"block": "container"}],
                                units=[]))["state"]["buildings"][0],
   {"block": "container", "x": None, "y": None, "team": None,
    "items": None},
   "missing building fields become null too")

broken = obs.from_world(world_payload(errors=["boom"]))
eq((broken["summary"]["ok"], broken["summary"]["errors"]), (False, ["boom"]),
   "payload errors land in summary")

unordered = obs.from_world(world_payload(
    events=[event(20, "shoot"), event(10, "print")]))
eq([e["tick"] for e in unordered["events"]], [10, 20],
   "from_world() sorts the event stream")
try:
    obs.from_world(None)
    ok(False, "from_world() rejects a non-dict payload")
except TypeError:
    ok(True, "from_world() rejects a non-dict payload")


# ------------------------------------------------------- end to end, no JVM

section("sim observation vs world payload, end to end")

sim_full = obs.make(
    "sim", scenario="unit-control", ticks=240, summary={"ok": True},
    state={"logs": SIM["finals"],
           "units": [unit(id=1, x=34.0, y=36.0)],
           "buildings": [{"block": "micro-processor", "x": 20, "y": 32,
                          "team": "sharded", "items": None}],
           "core": {"items": {"copper": 500}, "x": 40, "y": 40}},
    events=[])
agrees(sim_full, obs.from_world(world_payload()),
       "the sim observation and the world payload of the same run agree")

moved_world = obs.from_world(world_payload(
    units=[{"id": 7, "type": "flare", "team": "sharded",
            "controller": "LogicAI", "x": 36.0, "y": 36.0, "hp": 90.0,
            "amount": 0}]))
disagrees(sim_full, moved_world, "state.units[flare#0].x",
          "a unit that moved 2 tiles in the world is a tolerance difference",
          rule="tolerance", detail="|Δ|=2")

world_par = obs.parity(sim_full, obs.from_world(world_payload()))
ok(world_par["same"],
   "a sim observation without a version still passes parity (map/team/size agree)")
ok(any(n["field"] == "mindustry" and "only one side" in n["detail"]
       for n in world_par["notes"]),
   "the missing version is reported as an unverifiable note")


# ------------------------------------------------------------------ summary

print()
if FAILS:
    print("%d FAILURE(S):" % len(FAILS))
    for name in FAILS:
        print("  - " + name)
    sys.exit(1)
print("all observation tests passed")
print("  %d assertion(s) across %d section(s)"
      % (PASSED, len(SECTIONS)))
