#!/usr/bin/env python
"""observation.py -- one observation schema for two hosts, plus the diff engine.

Why this exists
---------------
`tools/mlogsim.py` runs the real executor with real unit updates, but it has no
wave AI and no full terrain collision; the live world server
(`tools/world_server.py`) is the real game, but slow and expensive.  The plan
(section 3) asks for the same scenario to be run on both hosts and for their
*observations* to be compared: what differs is the fidelity boundary (P2), not a
bug.  A comparison
only means something if both sides answer in one shape, so this module owns

  * the observation schema `mlog-observation/v1` and `normalize()`, which is the
    only canonical form anyone compares (events sorted by tick, numbers as
    numbers, log values as strings),
  * the converters for the two sources: `from_scenario()` (the offline
    `scenario._sim()` record) and `from_world()` (the raw world payload),
  * the rule-driven diff engine: `compare()` over state plus events, `parity()`
    over `env`, and `report()` which wraps both in the shared mlog_eval
    envelope so a disagreement is `simulation_real_difference`, not "fix your
    scenario".

Schema `mlog-observation/v1`
----------------------------
    {
      "schema": "mlog-observation/v1",
      "source": "sim" | "world",
      "scenario": str,
      "ticks": int,
      "summary": {"ok": bool, "errors": [str],
                  "instructions": int|null, "elapsed_ms": int|null},
      "state": {
        "logs": {logic: {var: str}},
        "units": [{"id", "type", "team", "controller", "x", "y", "hp",
                   "amount"}],
        "buildings": [{"block", "x", "y", "team", "items"}],
        "core": {"items": {item: int}, "x": int, "y": int} | null
      },
      "events": [{"tick": int, "type": str, "logic": str, "detail": str}],
      "env": {"mindustry": str|null, "java": str|null, "map": str|null,
              "world_size": [int, int]|null, "team": str|null,
              "update": str|null, "sampling": "final"|"every-tick"|"poll"|null}
    }

Every key is always present: a missing value is `null`, never an omitted key,
because an omission and a zero are different facts and a diff must not confuse
them.  Numbers are numbers (`"7"` survives only in `logs`, where mlog variables
are strings by nature).  Unit positions are tiles, not pixels.  `id` is stable
only within one side and is never compared across sides.

`make()` builds that shape from scratch, `normalize()` returns a deep copy in
canonical form (idempotent), and both converters end in `make()` so the two
sources cannot drift apart.

Comparison rules
----------------
`SPEC` says how each top-level part of `state` (and `events`) is compared:

  exact      value and structure must match.  Numbers compare numerically, so
             `7` and `7.0` are the same, and strings compare after `strip()`.
  tolerance  numbers may differ: a plain number is an absolute tolerance, a
             `"5%"` string is relative to the larger absolute value.  Non-numeric
             values fall back to `exact`.
  match      pair list entries by `key` first (in order inside each key group),
             then compare `fields` (each field may carry its own tolerance);
             an entry that cannot be paired is a difference with null sides.
  ordered    pair events as a *subsequence* on `key`: extra events on the right
             are insertions and are recorded as notes, while an event present
             only on the left, an order inversion, or a field/tick mismatch is a
             difference.  `tick_tolerance` allows clock drift between hosts.

`compare()` treats its first argument (`a`, by convention the `sim` observation)
as the reference for event presence.  `env` is not part of `compare()`: it is
`parity()`'s job, because two runs on different hosts are expected to disagree
about the map (that is what the fidelity envelope is for) while `compare()` is
about the program's behaviour.

There is deliberately no `json.dumps(a) == json.dumps(b)` shortcut anywhere in
this module.  Serialization order is not semantics: dict key order, `7` vs
`7.0`, tolerance, and insertion-tolerant event streams all would say "different"
for the wrong reason.  (`json.dumps` appears only in `_brief()` for readable
diagnostics, never in a predicate.)

Usage
-----
    python tools/observation.py selftest
    python tools/observation.py show out/_obs/sim.json
    python tools/observation.py compare out/_obs/sim.json out/_obs/world.json --json

Exit codes: 0 same / ok, 1 different, 2 bad arguments or unreadable input.
"""
from __future__ import annotations

import copy
import json
import math
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from mlog_eval import result  # noqa: E402

SCHEMA = "mlog-observation/v1"
SOURCES = ("sim", "world")

#: How each part of an observation is compared.  Callers may pass a partial
#: spec; `_spec()` merges it over this one section by section.
#: `events.optional` means "one side captured no events at all" (the world side
#: samples `final`), which is a note, not a difference.
SPEC = {
    "logs": {"mode": "exact"},
    "units": {"mode": "match", "key": ["type"],
              "fields": {"x": 0.5, "y": 0.5, "hp": "5%"}},
    "buildings": {"mode": "match", "key": ["block", "x", "y"],
                  "fields": {"items": "exact"}},
    "core": {"mode": "exact"},
    "events": {"mode": "ordered", "key": ["type"], "tick_tolerance": 3,
               "optional": True},
}

MODES = ("exact", "tolerance", "match", "ordered")

SUMMARY_KEYS = {"ok": True, "errors": [], "instructions": None, "elapsed_ms": None}
STATE_KEYS = {"logs": {}, "units": [], "buildings": [], "core": None}
ENV_KEYS = {"mindustry": None, "java": None, "map": None, "world_size": None,
            "team": None, "update": None, "sampling": None}
UNIT_KEYS = ("id", "type", "team", "controller", "x", "y", "hp", "amount")
BUILDING_KEYS = ("block", "x", "y", "team", "items")

#: `id` is per-host and never compared (the contract says so); everything else a
#: unit carries is compared exactly unless `SPEC["units"]["fields"]` gives it a
#: tolerance.
SKIP_FIELDS = {"id"}

_NUM_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")

#: Sentinel for "this key is not in the dict at all", which is a different fact
#: from "the key is there and null".
_MISSING = object()


# ---------------------------------------------------------------- primitives

def _is_num(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _as_num(value):
    """float(value) for numbers and numeric strings, else None.

    mlog variables are strings at the source and a world probe may hand one
    back, so `"90.0"` has to compare as the number 90.0 instead of producing
    string-vs-number noise.  Bools are numbers in Python but not in mlog.
    """
    if _is_num(value):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if _NUM_RE.match(text):
            try:
                return float(text)
            except ValueError:  # pragma: no cover -- the regex already decided
                return None
    return None


def _is_nan(value) -> bool:
    return _is_num(value) and value != value


def _num_eq(left, right) -> bool:
    """Numeric equality that treats two NaNs as "the same absent value"."""
    if _is_nan(left) and _is_nan(right):
        return True
    if _is_nan(left) or _is_nan(right):
        return False
    lf, rf = _as_num(left), _as_num(right)
    return lf is not None and rf is not None and lf == rf


def _fmt(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        if value != value:
            return "nan"
        return "%g" % value
    return str(value)


def _diff(path: str, rule: str, left, right, detail: str) -> dict:
    return {"path": path, "rule": rule, "left": left, "right": right,
            "detail": detail}


def _brief(value, limit: int = 120) -> str:
    """Compact one-line rendering for a difference's `detail` (never a predicate)."""
    try:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    except (TypeError, ValueError):
        text = repr(value)
    if len(text) > limit:
        text = text[:limit - 3] + "..."
    return text


def _union_keys(left: dict, right: dict) -> list:
    return sorted(set(left) | set(right), key=str)


def _norm_numbers(value):
    """Integral floats become ints, containers are walked, everything else stays."""
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, float):
        if value != value:                 # NaN: not a number, keep as-is
            return value
        if math.isfinite(value) and value.is_integer():
            return int(value)
        return value
    if isinstance(value, dict):
        return {k: _norm_numbers(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_norm_numbers(v) for v in value]
    return value


def _tick_key(event):
    """Sort key: ticked events in tick order, then unticked ones in input order."""
    tick = event.get("tick") if isinstance(event, dict) else None
    number = _as_num(tick)
    if number is None or number != number:
        return (1, 0.0)
    return (0, number)


# ---------------------------------------------------------------- schema

def make(source, *, scenario, ticks, summary=None, state=None,
         events=None, env=None) -> dict:
    """Build a complete `mlog-observation/v1` observation.

    Missing arguments become null / empty containers so the two sources always
    have the same shape, and the result is normalized (events sorted, numbers
    canonical, log values stringified).
    """
    if source not in SOURCES:
        raise ValueError("source must be one of %s, got %r" % (SOURCES, source))
    if ticks is None:
        ticks = 0
    summary_block = dict(SUMMARY_KEYS)
    summary_block.update(copy.deepcopy(summary or {}))
    state_block = copy.deepcopy(STATE_KEYS)
    state_block.update(copy.deepcopy(state or {}))
    env_block = dict(ENV_KEYS)
    env_block.update(copy.deepcopy(env or {}))
    obs = {
        "schema": SCHEMA,
        "source": source,
        "scenario": str(scenario or ""),
        "ticks": int(ticks),
        "summary": summary_block,
        "state": state_block,
        "events": list(copy.deepcopy(events or [])),
        "env": env_block,
    }
    return normalize(obs)


def normalize(obs: dict) -> dict:
    """Return a canonical deep copy of an observation.

    Canonical means: log values are strings, integral floats are ints, other
    numbers are numeric, and events are stably sorted by `tick`.  It never
    fills in missing keys (that is `make()`'s job) and never mutates its
    argument, so calling it twice yields the same structure.
    """
    if not isinstance(obs, dict):
        raise TypeError("observation must be a dict, got %s" % type(obs).__name__)
    out = copy.deepcopy(obs)

    state = out.get("state")
    if isinstance(state, dict):
        logs = state.get("logs")
        if isinstance(logs, dict):
            clean = {}
            for logic, table in logs.items():
                if not isinstance(table, dict):
                    clean[str(logic)] = table
                    continue
                clean[str(logic)] = {
                    str(var): (None if value is None else str(value))
                    for var, value in table.items()}
            state["logs"] = clean
        for key in ("units", "buildings", "core"):
            if key in state:
                state[key] = _norm_numbers(state[key])

    for key in ("summary", "env", "ticks"):
        if key in out:
            out[key] = _norm_numbers(out[key])

    events = out.get("events")
    if isinstance(events, list):
        for event in events:
            if isinstance(event, dict):
                for field in list(event):
                    event[field] = _norm_numbers(event[field])
        out["events"] = sorted(events, key=_tick_key)
    return out


# ---------------------------------------------------------------- converters

def _sim_buildings(refs: dict, scene: dict | None) -> list:
    """Buildings the offline record does know about: name -> origin + block.

    `_sim()` returns `refs` (the placement report's real origins), which is the
    only building evidence the offline path has -- no item contents yet, so
    `items` stays null instead of pretending to be an empty container.
    """
    teams = {}
    for b in (scene or {}).get("buildings") or []:
        if isinstance(b, dict) and b.get("team"):
            teams[b.get("name")] = b.get("team")
    out = []
    for name, where in (refs or {}).items():
        if not isinstance(where, (list, tuple)) or len(where) < 3:
            continue
        x, y, block = where[0], where[1], where[2]
        out.append({"block": block, "x": x, "y": y,
                    "team": teams.get(name), "items": None})
    return out


def from_scenario(sim: dict, *, scenario: str = "", ticks: int | None = None,
                  scene: dict | None = None, env: dict | None = None) -> dict:
    """Turn the offline `scenario._sim()` record into an observation.

    `_sim()` returns `{"ticks", "samples", "finals", "checks", "report",
    "refs"}`: the processor variable tables (`finals`) are the mlog-visible
    state, `refs` gives the buildings' real origins, and `report` carries the
    scene-application counts, which land in `env["scene"]` (the contract allows
    keys beyond the minimal env).  The offline record has no unit snapshot and
    no per-tick event log, so `state.units` is null ("not observed", which
    `compare()` reports as a note) and `events` is empty; a scenario that needs
    those has to grow the record first.

    Two optional extras keep the caller from re-deriving facts it already has:
    `scene` (the loaded scenario) supplies the map name, world size and teams,
    `env` overrides whatever the caller knows better (e.g. `detect_env()`).
    Neither is required, and nothing here touches the JVM.
    """
    if not isinstance(sim, dict):
        raise TypeError("from_scenario needs the _sim() dict, got %s"
                        % type(sim).__name__)
    report = sim.get("report") or {}
    errors = [str(e) for e in (report.get("errors") or [])]
    checks = sim.get("checks") or []
    finals = sim.get("finals") or {}

    env_block = dict(ENV_KEYS)
    env_block.update({"update": "all", "sampling": "every-tick"})
    if scene:
        world = scene.get("world") or {}
        size = world.get("size")
        if isinstance(size, (int, float)):
            env_block["world_size"] = [int(size), int(size)]
            env_block["map"] = "blank-%d" % int(size)
        elif isinstance(size, (list, tuple)) and len(size) == 2:
            env_block["world_size"] = [int(size[0]), int(size[1])]
            env_block["map"] = "blank-%dx%d" % (int(size[0]), int(size[1]))
        for unit in scene.get("units") or []:
            if isinstance(unit, dict) and unit.get("team"):
                env_block["team"] = unit["team"]
                break
        if not env_block["team"]:
            for building in scene.get("buildings") or []:
                if isinstance(building, dict) and building.get("team"):
                    env_block["team"] = building["team"]
                    break
    env_block.update(copy.deepcopy(env or {}))
    env_block["scene"] = {
        "placed": report.get("placed"),
        "configured": report.get("configured"),
        "stocked": report.get("stocked"),
        "linked": report.get("linked"),
        "units": report.get("units"),
        "errors": errors,
        "warnings": [str(w) for w in (report.get("warnings") or [])],
        "done": report.get("done"),
        "checks": {"total": len(checks),
                   "failed": sum(1 for c in checks if not c.get("ok"))},
    }

    return make(
        "sim",
        scenario=scenario or (scene or {}).get("id") or "",
        ticks=sim.get("ticks") if ticks is None else ticks,
        summary={"ok": not errors, "errors": errors,
                 "instructions": None, "elapsed_ms": sim.get("elapsed_ms")},
        state={"logs": finals, "units": None,
               "buildings": _sim_buildings(sim.get("refs") or {}, scene),
               "core": None},
        events=[],
        env=env_block,
    )


def _unit_row(row: dict) -> dict:
    out = {key: row.get(key) for key in UNIT_KEYS}
    out.update({k: v for k, v in row.items() if k not in out})
    return out


def _building_row(row: dict) -> dict:
    out = {key: row.get(key) for key in BUILDING_KEYS}
    out.update({k: v for k, v in row.items() if k not in out})
    return out


def from_world(payload: dict, *, scenario: str = "") -> dict:
    """Turn the raw world payload (contract §5) into an observation.

    Coordinates are expected in tiles already: the world client divides pixels
    by 8, because a schema that silently mixes units is worse than a client
    that has to convert.  Unknown item/blocks are passed through untouched.
    """
    if not isinstance(payload, dict):
        raise TypeError("from_world needs the world payload dict, got %s"
                        % type(payload).__name__)
    errors = [str(e) for e in (payload.get("errors") or [])]
    env_block = dict(ENV_KEYS)
    env_block.update({"update": "live", "sampling": "final"})
    env_block.update(copy.deepcopy(payload.get("env") or {}))
    if "scene" in payload:
        env_block["scene"] = copy.deepcopy(payload["scene"])

    core = payload.get("core")
    if isinstance(core, dict):
        core = dict(core)
        if "items" not in core:
            core["items"] = None
        core.setdefault("x", None)
        core.setdefault("y", None)
    else:
        core = None

    return make(
        "world",
        scenario=scenario or payload.get("scenario") or "",
        ticks=payload.get("ticks"),
        summary={"ok": not errors, "errors": errors,
                 "instructions": payload.get("instructions"),
                 "elapsed_ms": payload.get("elapsed_ms")},
        state={"logs": copy.deepcopy(payload.get("logs") or {}),
               "units": [_unit_row(u) for u in payload.get("units") or []],
               "buildings": [_building_row(b)
                             for b in payload.get("buildings") or []],
               "core": core},
        events=copy.deepcopy(payload.get("events") or []),
        env=env_block,
    )


def detect_env() -> dict:
    """Best-effort env for the offline host: jar name -> mindustry, jdk -> java.

    Kept out of `from_scenario()` on purpose: `scenario.environment()` runs
    `java -version` once, and an observation converter must stay a pure data
    transformation (the tests run without a JVM).  Callers that want a real
    `env` block call this and pass it as `env=`.
    """
    env = dict(ENV_KEYS)
    env.update({"update": "all", "sampling": "every-tick"})
    try:
        import scenario as _scenario
        host = _scenario.environment(cached=True)
    except Exception:                       # noqa: BLE001 -- env is optional
        return env
    jar = str(host.get("jar") or "")
    match = re.search(r"_server(\d+)\.jar$", jar)
    if match:
        env["mindustry"] = "v" + match.group(1)
    java = str(host.get("java") or "")
    match = re.search(r"jdk-(\d+\.\d+\.\d+)", java)
    if match:
        env["java"] = match.group(1)
    return env


# ---------------------------------------------------------------- diff engine

def _spec(spec: dict | None) -> dict:
    out = copy.deepcopy(SPEC)
    for section, cfg in (spec or {}).items():
        if not isinstance(cfg, dict):
            raise ValueError("spec[%r] must be a dict, got %s"
                             % (section, type(cfg).__name__))
        merged = out.get(section) or {}
        merged.update(copy.deepcopy(cfg))
        out[section] = merged
    for section, cfg in out.items():
        mode = cfg.get("mode", "exact")
        if mode not in MODES:
            raise ValueError("spec[%r]: mode must be one of %s, got %r"
                             % (section, MODES, mode))
    return out


def _walk_exact(left, right, path: str, out: list, rule: str = "exact") -> int:
    """Append one difference per mismatching leaf; return comparisons made."""
    if left is _MISSING or right is _MISSING:
        if left is _MISSING and right is _MISSING:
            return 1
        if left is _MISSING:
            out.append(_diff(path, rule, None, right, "key missing on the left"))
        else:
            out.append(_diff(path, rule, left, None, "key missing on the right"))
        return 1

    if isinstance(left, dict) and isinstance(right, dict):
        checks = 0
        for key in _union_keys(left, right):
            child = "%s.%s" % (path, key)
            if key not in left:
                out.append(_diff(child, rule, None, right[key],
                                 "key missing on the left"))
                checks += 1
            elif key not in right:
                out.append(_diff(child, rule, left[key], None,
                                 "key missing on the right"))
                checks += 1
            else:
                checks += _walk_exact(left[key], right[key], child, out, rule)
        return checks

    if isinstance(left, list) and isinstance(right, list):
        checks = 1
        if len(left) != len(right):
            out.append(_diff(path, rule, len(left), len(right),
                             "length %d != %d" % (len(left), len(right))))
        for index in range(min(len(left), len(right))):
            checks += _walk_exact(left[index], right[index],
                                  "%s[%d]" % (path, index), out, rule)
        return checks

    if isinstance(left, dict) or isinstance(right, dict) \
            or isinstance(left, list) or isinstance(right, list):
        out.append(_diff(path, rule, left, right,
                         "structure differs: %s vs %s"
                         % (_kind(left), _kind(right))))
        return 1

    if isinstance(left, bool) != isinstance(right, bool):
        out.append(_diff(path, rule, left, right,
                         "bool vs %s" % _kind(right if isinstance(left, bool) else left)))
        return 1

    if _is_num(left) or _is_num(right) or (_as_num(left) is not None
                                           and _as_num(right) is not None):
        if _num_eq(left, right):
            return 1
        out.append(_diff(path, rule, left, right,
                         "%s != %s" % (_fmt(left), _fmt(right))))
        return 1

    if isinstance(left, str) and isinstance(right, str):
        if left.strip() == right.strip():
            return 1
        out.append(_diff(path, rule, left, right,
                         "%r != %r" % (left.strip(), right.strip())))
        return 1

    if left is None or right is None:
        if left is None and right is None:
            return 1
        out.append(_diff(path, rule, left, right,
                         "%s vs %s" % (_kind(left), _kind(right))))
        return 1

    if left == right:
        return 1
    out.append(_diff(path, rule, left, right,
                     "%s != %s" % (_brief(left), _brief(right))))
    return 1


def _kind(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    return type(value).__name__


def _rel_fraction(tol) -> float | None:
    if isinstance(tol, str) and tol.strip().endswith("%"):
        try:
            return float(tol.strip()[:-1]) / 100.0
        except ValueError:
            return None
    return None


def _diff_tol(left, right, path: str, tol, out: list) -> int:
    """Compare one value under a tolerance spec (`0.5`, `"5%"`, `"exact"`)."""
    if tol is None or (isinstance(tol, str) and tol.strip().lower() == "exact"):
        return _walk_exact(left, right, path, out)
    relative = _rel_fraction(tol)
    if relative is None and not _is_num(tol):
        try:
            tol = float(str(tol).strip())
        except (TypeError, ValueError):
            return _walk_exact(left, right, path, out)

    lf, rf = _as_num(left), _as_num(right)
    if lf is None or rf is None:
        return _walk_exact(left, right, path, out)

    if _num_eq(left, right):
        return 1
    if (lf != lf) or (rf != rf):           # one NaN, not both: a real difference
        out.append(_diff(path, "tolerance", left, right,
                         "%s vs %s (NaN is never within tolerance)"
                         % (_fmt(lf), _fmt(rf))))
        return 1

    delta = abs(lf - rf)
    if relative is not None:
        base = max(abs(lf), abs(rf))
        limit = relative * base
        if delta <= limit + 1e-12:
            return 1
        out.append(_diff(path, "tolerance", left, right,
                         "|Δ|=%s > %s%% of %s (=%s)"
                         % (_fmt(delta), _fmt(relative * 100.0), _fmt(base),
                            _fmt(limit))))
        return 1

    if delta <= float(tol) + 1e-12:
        return 1
    out.append(_diff(path, "tolerance", left, right,
                     "|Δ|=%s > %s" % (_fmt(delta), _fmt(tol))))
    return 1


def _walk_tolerance(left, right, path: str, out: list, tol) -> int:
    """`tolerance` section mode: numbers use `tol`, containers recurse."""
    if isinstance(left, dict) and isinstance(right, dict):
        checks = 0
        for key in _union_keys(left, right):
            child = "%s.%s" % (path, key)
            if key not in left:
                out.append(_diff(child, "exact", None, right[key],
                                 "key missing on the left"))
                checks += 1
            elif key not in right:
                out.append(_diff(child, "exact", left[key], None,
                                 "key missing on the right"))
                checks += 1
            else:
                checks += _walk_tolerance(left[key], right[key], child, out, tol)
        return checks
    if isinstance(left, list) and isinstance(right, list):
        checks = 1
        if len(left) != len(right):
            out.append(_diff(path, "exact", len(left), len(right),
                             "length %d != %d" % (len(left), len(right))))
        for index in range(min(len(left), len(right))):
            checks += _walk_tolerance(left[index], right[index],
                                      "%s[%d]" % (path, index), out, tol)
        return checks
    if isinstance(left, dict) or isinstance(right, dict) \
            or isinstance(left, list) or isinstance(right, list):
        return _walk_exact(left, right, path, out)
    return _diff_tol(left, right, path, tol, out)


def _entry_label(key: tuple, count: int, index: int, keyed_by_one: bool) -> str:
    """`flare#0` for units, `container@10,10` for buildings.

    A single-field key (`units.key = ["type"]`) cannot tell two entries apart on
    its own, so the index is always shown; a multi-field key already names a
    building by block and tile and only grows a `#n` suffix when it repeats.
    """
    parts = [str(v) for v in key]
    base = parts[0] + ("@" + ",".join(parts[1:]) if len(parts) > 1 else "")
    if count > 1 or keyed_by_one:
        return "%s#%d" % (base, index)
    return base


def _group(entries: list, keyf: list) -> dict:
    groups: dict[tuple, list] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raw = (_brief(entry),)
        else:
            raw = tuple(_key_value(entry.get(f)) for f in keyf)
        groups.setdefault(raw, []).append(entry)
    return groups


def _key_value(value):
    """Make a key component hashable while keeping numeric identity."""
    if isinstance(value, (dict, list, tuple)):
        return _brief(value)
    return value


def _diff_entry(left, right, path: str, keyf: list, fields: dict,
                out: list) -> int:
    if not isinstance(left, dict) or not isinstance(right, dict):
        return _walk_exact(left, right, path, out)
    checks = 0
    for field in _union_keys(left, right):
        if field in keyf or field in SKIP_FIELDS:
            continue
        child = "%s.%s" % (path, field)
        if field not in left:
            out.append(_diff(child, "exact", None, right[field],
                             "key missing on the left"))
            checks += 1
        elif field not in right:
            out.append(_diff(child, "exact", left[field], None,
                             "key missing on the right"))
            checks += 1
        elif field in fields:
            checks += _diff_tol(left[field], right[field], child, fields[field],
                                out)
        else:
            # Everything a unit carries is part of the observation: a field the
            # spec does not mention is compared exactly instead of ignored.
            checks += _walk_exact(left[field], right[field], child, out)
    return checks


def _diff_match(left, right, path: str, cfg: dict, out: list) -> int:
    keyf = list(cfg.get("key") or [])
    fields = dict(cfg.get("fields") or {})
    if not keyf:
        return _walk_exact(left, right, path, out)
    if not isinstance(left, list) or not isinstance(right, list):
        out.append(_diff(path, "match", left, right,
                         "match mode needs two arrays, got %s vs %s"
                         % (_kind(left), _kind(right))))
        return 1

    ga, gb = _group(left, keyf), _group(right, keyf)
    checks = 0
    for raw in list(ga) + [k for k in gb if k not in ga]:
        la, lb = ga.get(raw, []), gb.get(raw, [])
        count = max(len(la), len(lb))
        keyed_by_one = len(keyf) == 1
        for index in range(count):
            name = _entry_label(raw if isinstance(raw, tuple) else (raw,),
                                count, index, keyed_by_one)
            child = "%s[%s]" % (path, name)
            if index >= len(la):
                out.append(_diff(child, "match", None, None,
                                 "present on the right only: %s"
                                 % _brief(lb[index])))
                checks += 1
            elif index >= len(lb):
                out.append(_diff(child, "match", None, None,
                                 "present on the left only: %s"
                                 % _brief(la[index])))
                checks += 1
            else:
                checks += _diff_entry(la[index], lb[index], child, keyf, fields,
                                      out)
    return checks


def _event_key(event: dict, keyf: list):
    if not isinstance(event, dict):
        return ("<non-object>",)
    return tuple(_key_value(event.get(field)) for field in keyf)


def _greedy_pairs(ka: list, kb: list):
    """Fallback alignment when the LCS table would be too large."""
    pairs = []
    i = j = 0
    while i < len(ka) and j < len(kb):
        if ka[i] == kb[j]:
            pairs.append((i, j))
            i += 1
            j += 1
        elif kb[j] not in ka[i + 1:]:
            i += 1
        elif ka[i] not in kb[j + 1:]:
            j += 1
        else:
            i += 1
    return pairs, [i for i in range(len(ka)) if i not in {p for p, _ in pairs}], \
        [j for j in range(len(kb)) if j not in {p for _, p in pairs}]


def _align(ka: list, kb: list):
    """Longest-common-subsequence alignment of two event key sequences."""
    n, m = len(ka), len(kb)
    if n * m > 250_000:
        return _greedy_pairs(ka, kb)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        row, nxt = dp[i], dp[i + 1]
        head = ka[i]
        for j in range(m - 1, -1, -1):
            if head == kb[j]:
                row[j] = nxt[j + 1] + 1
            else:
                row[j] = nxt[j] if nxt[j] >= row[j + 1] else row[j + 1]
    pairs = []
    i = j = 0
    while i < n and j < m:
        if ka[i] == kb[j]:
            pairs.append((i, j))
            i += 1
            j += 1
        elif dp[i + 1][j] >= dp[i][j + 1]:
            i += 1
        else:
            j += 1
    paired_a = {i for i, _ in pairs}
    paired_b = {j for _, j in pairs}
    return (pairs,
            [i for i in range(n) if i not in paired_a],
            [j for j in range(m) if j not in paired_b])


def _diff_event_pair(le: dict, re_: dict, path: str, keyf: list,
                     tick_tolerance, out: list) -> int:
    checks = 0
    for field in _union_keys(le, re_):
        if field in keyf:
            continue
        child = "%s.%s" % (path, field)
        if field not in le:
            out.append(_diff(child, "exact", None, re_[field],
                             "key missing on the left"))
            checks += 1
        elif field not in re_:
            out.append(_diff(child, "exact", le[field], None,
                             "key missing on the right"))
            checks += 1
        elif field == "tick":
            checks += _diff_tick(le[field], re_[field], child, tick_tolerance,
                                 out)
        else:
            checks += _walk_exact(le[field], re_[field], child, out)
    return checks


def _diff_tick(left, right, path: str, tolerance, out: list) -> int:
    lf, rf = _as_num(left), _as_num(right)
    if lf is None or rf is None:
        return _walk_exact(left, right, path, out)
    try:
        limit = float(tolerance or 0)
    except (TypeError, ValueError):
        limit = 0.0
    if abs(lf - rf) <= limit + 1e-12:
        return 1
    out.append(_diff(path, "ordered", left, right,
                     "tick %s vs %s (tolerance %s)"
                     % (_fmt(left), _fmt(right), _fmt(limit))))
    return 1


def _diff_events(left, right, cfg: dict, out: list, notes: list) -> int:
    keyf = list(cfg.get("key") or ["type"])
    tolerance = cfg.get("tick_tolerance", 0)
    optional = bool(cfg.get("optional"))
    if not isinstance(left, list) or not isinstance(right, list):
        out.append(_diff("events", "ordered", left, right,
                         "ordered mode needs two arrays, got %s vs %s"
                         % (_kind(left), _kind(right))))
        return 1
    if not left and not right:
        return 0
    if optional and (not left or not right):
        notes.append({"path": "events", "rule": "ordered",
                      "left": len(left), "right": len(right),
                      "detail": "one side reports no events at all (%d vs %d): "
                                "that is a sampling limit, not a difference"
                                % (len(left), len(right))})
        return 1

    ka = [_event_key(e, keyf) for e in left]
    kb = [_event_key(e, keyf) for e in right]
    pairs, only_left, only_right = _align(ka, kb)
    checks = 0
    for i, j in pairs:
        checks += _diff_event_pair(left[i], right[j], "events[%d]" % i, keyf,
                                   tolerance, out)
    for i in only_left:
        checks += 1
        out.append(_diff("events[%d]" % i, "ordered", None, None,
                         "event %s is missing on the right"
                         % _brief(left[i])))
    for j in only_right:
        checks += 1
        notes.append({"path": "events[%d]" % j, "rule": "ordered",
                      "left": None, "right": _brief(right[j]),
                      "detail": "extra event on the right (insertions are "
                                "allowed), not a difference"})
    return checks


def compare(a: dict, b: dict, spec: dict | None = None) -> dict:
    """Diff two observations field by field.

    Returns `{"same": bool, "checked": int, "differences": [...], "notes": [...]}`.
    Each difference carries `path`, `rule`, `left`, `right` and a human-readable
    `detail`; `checked` counts field-level comparisons performed (an unpaired
    entry counts once).  `a` is the reference for event presence -- the usual
    call is `compare(sim_obs, world_obs)`.  `env` belongs to `parity()`.
    """
    if not isinstance(a, dict) or not isinstance(b, dict):
        raise TypeError("compare needs two observation dicts")
    left, right = normalize(a), normalize(b)
    sp = _spec(spec)

    differences: list = []
    notes: list = []
    checked = 0

    sa = left.get("state")
    sb = right.get("state")
    sa = sa if isinstance(sa, dict) else {}
    sb = sb if isinstance(sb, dict) else {}
    side_la = str(left.get("source") or "left")
    side_lb = str(right.get("source") or "right")

    order = ["logs", "units", "buildings", "core"]
    order += sorted((set(sa) | set(sb)) - set(order), key=str)
    for section in order:
        cfg = sp.get(section) or {}
        mode = cfg.get("mode", "exact")
        path = "state.%s" % section
        la = sa.get(section, _MISSING)
        lb = sb.get(section, _MISSING)
        if la is _MISSING and lb is _MISSING:
            continue
        if la is _MISSING:
            differences.append(_diff(path, mode, None, lb,
                                     "section missing on the left"))
            checked += 1
            continue
        if lb is _MISSING:
            differences.append(_diff(path, mode, la, None,
                                     "section missing on the right"))
            checked += 1
            continue
        if la is None or lb is None:
            if la is None and lb is None:
                continue
            # A whole section that is null means "this source does not observe
            # it" (the offline record has no unit snapshot, for instance).  That
            # is a coverage gap of the observation, and reporting it as a
            # difference would drown every run in noise, so it is a note.
            notes.append({"path": path, "rule": mode,
                          "left": None if la is None else _brief(la),
                          "right": None if lb is None else _brief(lb),
                          "detail": "%s does not record %s (unobserved, not a "
                                    "difference)"
                                    % (side_la if la is None else side_lb, path)})
            continue

        if mode == "match":
            checked += _diff_match(la, lb, path, cfg, differences)
        elif mode == "ordered":
            checked += _diff_events(la, lb, cfg, differences, notes)
        elif mode == "tolerance":
            checked += _walk_tolerance(la, lb, path, differences,
                                       cfg.get("tolerance", 0.5))
        else:
            checked += _walk_exact(la, lb, path, differences)

    events_cfg = sp["events"]
    events_mode = events_cfg.get("mode", "exact")
    ev_a = left.get("events") or []
    ev_b = right.get("events") or []
    if events_mode == "ordered":
        checked += _diff_events(ev_a, ev_b, events_cfg, differences, notes)
    elif events_mode == "match":
        checked += _diff_match(ev_a, ev_b, "events", events_cfg, differences)
    elif events_mode == "tolerance":
        checked += _walk_tolerance(ev_a, ev_b, "events", differences,
                                   events_cfg.get("tolerance", 0))
    else:
        checked += _walk_exact(ev_a, ev_b, "events", differences)

    return {"same": not differences, "checked": checked,
            "differences": differences, "notes": notes}


# ---------------------------------------------------------------- parity

def _env(obs: dict) -> dict:
    block = obs.get("env") if isinstance(obs, dict) else None
    return block if isinstance(block, dict) else {}


def _major(version):
    """Mindustry major from `v160.7`, `160`, `Mindustry v160.7`; None if absent."""
    if version is None:
        return None
    match = re.search(r"v?(\d+)", str(version))
    return int(match.group(1)) if match else None


def parity(a: dict, b: dict) -> dict:
    """Compare only `env`: are these two runs even the same experiment?

    `mindustry` compares by major version (both jars are "v160.x" as far as the
    program is concerned); `map`, `world_size` and `team` must agree.  Three
    things are deliberately *notes* instead of failures:

    * `update` -- the offline host pins `Time.delta` and steps the world itself,
      the live host runs the real 60 Hz loop; `"all"` vs `"live"` differs by
      construction, so failing on it would fail every honest pair.
    * `sampling` -- every-tick trace vs a poll at the end is recording fidelity.
  `poll` is the live world's honest answer: the clock is wall time, so per-tick
  sampling is not offered and the sampler walks the clock instead.
    * a field only one side reports -- "we did not record it" is not "the two
      environments disagree".  It is still surfaced (never silently dropped),
      because an unverified field must not look like a passed one.
    """
    ea, eb = _env(a), _env(b)
    side_a = str((a or {}).get("source") or "left")
    side_b = str((b or {}).get("source") or "right")
    checks = []
    notes = []

    def add(field, ok, left, right, detail=""):
        checks.append({"field": field, "left": left, "right": right,
                       "ok": bool(ok), "detail": detail})

    def one_side(field, va, vb):
        """Record "only one side reported it" as a note, not a mismatch."""
        missing = side_a if va is None else side_b
        notes.append({"field": field, "left": va, "right": vb,
                      "detail": "only one side reports it (%s has none): "
                                "recorded as a note, the field stays unverified"
                                % (side_a if va is None else side_b)})

    la, lb = ea.get("mindustry"), eb.get("mindustry")
    ma, mb = _major(la), _major(lb)
    if la is None and lb is None:
        add("mindustry", True, la, lb, "not reported on either side")
    elif la is None or lb is None:
        one_side("mindustry", la, lb)
    elif ma is None or mb is None:
        add("mindustry", False, la, lb,
            "cannot read a major version from %r vs %r" % (la, lb))
    elif ma != mb:
        add("mindustry", False, la, lb, "major %d vs %d" % (ma, mb))
    else:
        add("mindustry", True, la, lb, "")

    for field in ("map", "team"):
        va, vb = ea.get(field), eb.get(field)
        if va is None and vb is None:
            add(field, True, va, vb, "not reported on either side")
        elif va is None or vb is None:
            one_side(field, va, vb)
        elif str(va).strip().casefold() == str(vb).strip().casefold():
            add(field, True, va, vb, "")
        else:
            add(field, False, va, vb, "%r != %r" % (va, vb))

    # `update` names how the host drives the clock, and that is exactly what the
    # two hosts do differently -- see the docstring.
    ua, ub = ea.get("update"), eb.get("update")
    if ua != ub:
        notes.append({"field": "update", "left": ua, "right": ub,
                      "detail": "host drive differs (%r vs %r): the offline host "
                                "steps the clock, the live host runs the real loop"
                                % (ua, ub)})

    wa, wb = ea.get("world_size"), eb.get("world_size")
    if wa is None and wb is None:
        add("world_size", True, wa, wb, "not reported on either side")
    elif wa is None or wb is None:
        one_side("world_size", wa, wb)
    else:
        ok = True
        detail = ""
        try:
            fa = [_as_num(v) for v in wa]
            fb = [_as_num(v) for v in wb]
            if len(fa) != len(fb) or any(v is None for v in fa + fb):
                ok = False
                detail = "%r vs %r" % (wa, wb)
            elif any(abs(x - y) > 1e-9 for x, y in zip(fa, fb)):
                ok = False
                detail = "%r != %r" % (wa, wb)
        except TypeError:
            ok, detail = False, "%r vs %r" % (wa, wb)
        add("world_size", ok, wa, wb, detail)

    sa, sb_ = ea.get("sampling"), eb.get("sampling")
    if sa != sb_:
        notes.append({"field": "sampling", "left": sa, "right": sb_,
                      "detail": "sampling differs (%r vs %r): recorded as a "
                                "note, not a failure" % (sa, sb_)})

    return {"same": all(check["ok"] for check in checks), "checks": checks,
            "notes": notes}


# ---------------------------------------------------------------- envelope

_NEXT_STEPS = [
    "Do not change the scenario to hide a difference: the two hosts disagree "
    "(plan section 3, P2).",
    "Record the gap in the Fidelity Envelope (map/terrain/engine-version "
    "dependence) before trusting the offline run.",
    "`mlogsim` is for iteration, the world server is the tie-breaker: rerun "
    "both after any engine change.",
]


def report(a, b, *, spec: dict | None = None, scenario: str = "",
           level: str = "summary") -> dict:
    """Wrap `compare()` + `parity()` in the shared mlog_eval envelope.

    A disagreement is `failure_type="simulation_real_difference"` and
    `next_steps` point at the fidelity envelope, never at "fix the scene":
    deciding which host is right is the whole point of the exercise.
    """
    started = time.time()
    diff = compare(a, b, spec)
    env = parity(a, b)
    ok = diff["same"] and env["same"]

    diagnostics = []
    for item in diff["differences"]:
        diagnostics.append({"kind": "difference", "path": item["path"],
                            "rule": item["rule"], "left": item["left"],
                            "right": item["right"],
                            "detail": item["detail"]})
    for item in env["checks"]:
        if not item["ok"]:
            diagnostics.append({"kind": "parity", "field": item["field"],
                                "left": item["left"], "right": item["right"],
                                "detail": item["detail"]})
    for item in diff["notes"] + env["notes"]:
        entry = {"kind": "note"}
        entry.update(item)
        diagnostics.append(entry)

    failed_parity = sum(1 for c in env["checks"] if not c["ok"])
    if ok:
        message = ("observations agree: %d field(s) checked, %d env field(s) "
                   "checked" % (diff["checked"], len(env["checks"])))
    else:
        message = ("observations disagree: %d state/event difference(s), "
                   "%d env mismatch(es), %d field(s) checked"
                   % (len(diff["differences"]), failed_parity, diff["checked"]))

    artifacts = {
        "scenario": scenario or a.get("scenario") or b.get("scenario") or "",
        "sources": [a.get("source"), b.get("source")],
        "checked": diff["checked"],
        "parity_checks": len(env["checks"]),
        "differences": len(diff["differences"]),
        "notes": len(diff["notes"]) + len(env["notes"]),
    }

    return result(
        ok=ok, stage="observation",
        failure_type=None if ok else "simulation_real_difference",
        message=message, diagnostics=diagnostics, artifacts=artifacts,
        next_steps=[] if ok else list(_NEXT_STEPS), level=level,
        elapsed_ms=int((time.time() - started) * 1000))


# ---------------------------------------------------------------- CLI

def selftest() -> int:
    """Prove the schema and the four rules on tiny in-memory observations."""
    fails = 0

    def ok(cond, what):
        nonlocal fails
        if not cond:
            fails += 1
            print("FAIL " + what)
        else:
            print("ok   " + what)

    base = make("sim", scenario="selftest", ticks=10,
                state={"logs": {"p": {"x": "7"}}})
    ok(base["schema"] == SCHEMA and set(base["state"]) >= set(STATE_KEYS),
       "make() fills the schema")
    ok(base["events"] == [] and base["state"]["core"] is None,
       "make() fills empty containers with null/[]")
    ok(base["state"]["logs"]["p"]["x"] == "7", "log values stay strings")

    e = make("sim", scenario="s", ticks=1,
             events=[{"tick": 5, "type": "print", "detail": "b"},
                     {"tick": 2, "type": "print", "detail": "a"}])
    ok([ev["tick"] for ev in e["events"]] == [2, 5], "normalize sorts events")

    same = compare(base, normalize(base))
    ok(same["same"] and same["checked"] > 0, "an observation equals itself")

    moved = copy.deepcopy(base)
    moved["state"]["units"] = [{"id": 1, "type": "flare", "x": 12.5,
                                "y": 30.0, "hp": 90.0, "amount": 0,
                                "team": "sharded", "controller": "LogicAI"}]
    moved2 = copy.deepcopy(moved)
    moved2["state"]["units"][0]["x"] = 12.9
    ok(compare(moved, moved2)["same"], "0.4 is inside the 0.5 tile tolerance")
    moved2["state"]["units"][0]["x"] = 14.0
    res = compare(moved, moved2)
    ok(not res["same"] and res["differences"][0]["rule"] == "tolerance",
       "a 1.5 tile drift is a tolerance difference")

    ok(parity({"env": {"mindustry": "v160.7"}},
              {"env": {"mindustry": "v160.4"}})["same"],
       "parity compares the mindustry major only")
    ok(not parity({"env": {"mindustry": "v159.0"}},
                  {"env": {"mindustry": "v160.7"}})["same"],
       "a different major fails parity")

    env = report(base, base, scenario="selftest", level="diagnostics")
    ok(env["ok"] and env["failure_type"] is None, "report() passes an equal pair")
    bad = copy.deepcopy(base)
    bad["state"]["logs"]["p"]["x"] = "8"
    env = report(base, bad, scenario="selftest", level="diagnostics")
    ok(env["ok"] is False
       and env["failure_type"] == "simulation_real_difference",
       "report() names a real difference")
    ok(all(d.get("detail") for d in env["diagnostics"]),
       "every diagnostic has readable text")

    print("-" * 48)
    print("selftest: %d failure(s)" % fails)
    return 1 if fails else 0


def _load(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("%s does not hold a JSON object" % path)
    return data


def _utf8_streams() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):   # pragma: no cover -- exotic hosts
            pass


USAGE = """usage:
  python tools/observation.py selftest
  python tools/observation.py show FILE
  python tools/observation.py compare A B [--spec FILE] [--json]

Exit codes: 0 same / ok, 1 different, 2 bad arguments or unreadable input.
"""


def main(argv=None) -> int:
    _utf8_streams()
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print(USAGE, end="")
        return 0 if argv else 2

    command = argv[0]
    if command == "selftest":
        return selftest()

    if command == "show":
        rest = argv[1:]
        if len(rest) != 1:
            print(USAGE, end="", file=sys.stderr)
            return 2
        try:
            obs = normalize(_load(rest[0]))
        except (OSError, ValueError) as exc:
            print("cannot read %s: %s" % (rest[0], exc), file=sys.stderr)
            return 2
        print(json.dumps(obs, ensure_ascii=False, indent=2, sort_keys=False))
        return 0

    if command == "compare":
        rest = list(argv[1:])
        as_json = False
        spec_path = None
        files = []
        index = 0
        while index < len(rest):
            arg = rest[index]
            if arg == "--json":
                as_json = True
            elif arg == "--spec" and index + 1 < len(rest):
                spec_path = rest[index + 1]
                index += 1
            elif arg.startswith("--spec="):
                spec_path = arg.split("=", 1)[1]
            elif arg.startswith("-"):
                print("unknown option %r" % arg, file=sys.stderr)
                return 2
            else:
                files.append(arg)
            index += 1
        if len(files) != 2:
            print(USAGE, end="", file=sys.stderr)
            return 2
        try:
            left, right = _load(files[0]), _load(files[1])
            spec = _load(spec_path) if spec_path else None
        except (OSError, ValueError) as exc:
            print("cannot read input: %s" % exc, file=sys.stderr)
            return 2
        diff = compare(left, right, spec)
        par = parity(left, right)
        if as_json:
            payload = dict(diff)
            payload["parity"] = par
            print(json.dumps(payload, ensure_ascii=False, indent=2,
                             sort_keys=False))
        else:
            print("same:    %s" % ("true" if diff["same"] and par["same"]
                                   else "false"))
            print("checked: %d field(s), %d env field(s)"
                  % (diff["checked"], len(par["checks"])))
            for item in diff["differences"]:
                print("  differ  %s [%s] %s" % (item["path"], item["rule"],
                                                item["detail"]))
            for check in par["checks"]:
                if not check["ok"]:
                    print("  parity  %s: %s" % (check["field"],
                                                check["detail"]))
            for note in diff["notes"] + par["notes"]:
                print("  note    %s" % note.get("detail"))
        return 0 if diff["same"] and par["same"] else 1

    print("unknown command %r\n%s" % (command, USAGE), file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:                       # noqa: BLE001
        import traceback
        traceback.print_exc()
        raise SystemExit(1)
