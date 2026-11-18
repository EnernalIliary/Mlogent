#!/usr/bin/env python
"""scenario.py -- run a scenario (scene schema v2) on the real executor.

Why this exists
---------------
`tools/scene.py` describes a *world* (buildings, items, units, a processor's
code) and `tools/mlogsim.py` can drive it; what was missing is the other half of
an experiment: what to look at, what must be true afterwards, and one answer
shape that says which of the two it was.  A scenario therefore is a scene plus

    id, title, goal, version: 2,
    limits:       {"ticks": int, "timeout_s": float},
    observations: [{"name", "logic", "var", "aggregate": last|max|min|sum}],
    assertions:   [{"id", "desc", "logic", "var", "op", "value",
                    "observation": optional observation name}],
    success_criteria: {"all_assertions": true}

and `run()` returns the shared envelope from `tools/mlog_eval.py`
(`schema="mlog-eval/v1"`), so a scenario, a static check and a compile report all
answer "did it work, and if not, why" in the same shape.

v1 stays valid
--------------
Every existing file in `scenes/` is v1 and must keep working: a v1 file is
loaded by `scene.load()` exactly as before (so `checks` keep their `equals`
semantics, including comparing a variable against a scene building's toString),
and only gets default `limits`/observations.  v2 files are projected onto a v1
shadow (the extra keys removed, `code` paths made absolute) which is then read
by `scene.load()` -- one loader, one normalizer, no second copy of the rules.

What the pieces mean
--------------------
* `observations` are sampled *every tick* while the scenario ticks, then
  aggregated (`last` by default).  Sampling every tick is what makes `max`/`sum`
  meaningful; the cost is small because only the named variables are read.
* `assertions` compare, in this order: the observation named by its optional
  `"observation"` key, else the `last`-valued observation of the same
  `logic`/`var`, else the processor's final value.  `op` is one of
  eq/ne/gt/ge/lt/le/contains; numbers compare numerically, so "1.0" eq 1, and a
  string expectation naming a scene building matches that building's
  `[x,y]:block` (the v1 `checks` semantics).  The `observation` key exists so a
  scenario can assert on `max`/`sum` -- it has to say so on purpose instead of
  silently getting whichever aggregate happens to be first.
* `stage` is always "scenario" and `ok=False` always carries one of
  `mlog_eval.FAILURE_TYPES`: `assertion_failed`, `runtime_error`, `timeout`,
  `unsupported_environment`.

Usage
-----
    python tools/scenario.py check scenes/scenarios/unit-control.json
    python tools/scenario.py run   scenes/scenarios/unit-control.json --json
    python tools/scenario.py list

Exit codes: 0 everything passed, 1 an assertion failed (or the run errored),
3 the environment cannot run it (no JVM / too-old java / no server jar).

Two hosts, one result shape
---------------------------
`via="sim"` runs the scene on `tools/mlogsim.py` (a headless server whose clock
this process drives).  `via="world"` runs the *same* scene file through
`tools/world_client.py` on the live `tools/world_server.py` rig: it writes the
scene v1 projection to `out/_scenario/world/`, applies it with `scene`, waits for
the world clock to advance `limits.ticks`, then reads the processors back with
`logic_vars` (and units/buildings/core with `js`).  Both paths return the same
record -- `ticks`/`samples`/`finals`/`checks`/`report`/`refs` -- so the
observation, the assertions and the envelope never fork on `via`.

The live side genuinely cannot see everything the offline side can: the world
clock is real (60 Hz wall clock, not `Time.delta=1` steps) so the per-tick trace
becomes a ~5 Hz poll (`report["sampling"] == "poll"`, `report["sampling_detail"]`
says how many polls).  A world that is not there -- no `out/_world/daemon.json`,
a dead daemon, no JVM, no jar -- is `unsupported_environment` with exit 3, never
a difference: an experiment that did not run must not look like a disagreement.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import scene as _scene  # noqa: E402
import modifier as _modifier  # noqa: E402
from mlog_eval import FAILURE_TYPES, classify, result  # noqa: E402

SCENARIO_DIR = os.path.join(ROOT, "scenes", "scenarios")
#: v2 files are projected onto a v1 shadow here, then handed to scene.load().
SHADOW_DIR = os.path.join(ROOT, "out", "_scenario", "v1")

#: Keys schema v2 adds on top of scene v1.
V2_KEYS = ("id", "title", "goal", "limits", "observations", "assertions",
           "success_criteria", "modifiers")
ALLOWED_KEYS = set(_scene.TOP_KEYS) | set(V2_KEYS)
AGGREGATES = ("last", "max", "min", "sum")
OPS = ("eq", "ne", "gt", "ge", "lt", "le", "contains")

DEFAULT_LIMITS = {"ticks": 120, "timeout_s": 60.0}
#: Ticks per `js` command: small enough that `limits.timeout_s` can interrupt a
#: runaway program, large enough that the per-command overhead stays noise.
TICK_CHUNK = 30
#: Mindustry v146+ needs a modern JVM; the box's PATH java is 8 and fails at boot.
MIN_JAVA_MAJOR = 17

#: Where the v1 projection handed to the live world is written.  The daemon is a
#: separate process reading the file with `scene.load()`, so it must be scene v1
#: (no scenario keys) at an absolute path (its cwd is its own data dir).
WORLD_SCENE_DIR = os.path.join(ROOT, "out", "_scenario", "world")
#: How often `via="world"` asks the host how far it has ticked (seconds).  The
#: live clock is real time, so this is a poll rate, not a tick rate.
WORLD_POLL_S = 0.2
#: Units closer than this (tiles) to a scene spawn point count as "ours".  The
#: scene's own spiral puts them exactly on those points; the radius only absorbs
#: the pixel rounding `u.x/8` picks up on the way back.
WORLD_UNIT_PICK_R = 4.0

_ENV_CACHE: dict = {}


class ScenarioError(ValueError):
    """A scenario is unreadable or fails validation."""


class _Timeout(Exception):
    """Internal: limits.timeout_s ran out mid-run."""


# ---------------------------------------------------------------- loading

def _read_json(path: str):
    with open(path, encoding="utf-8-sig") as fh:
        return json.load(fh)


def _shadow_path(full: str) -> str:
    os.makedirs(SHADOW_DIR, exist_ok=True)
    return os.path.join(SHADOW_DIR, os.path.basename(full))


def _strip_to_v1(raw: dict, full: str) -> dict:
    """The scene-v1 projection of a v2 file, with `code` paths made absolute.

    `scene.load()` resolves a relative `code` against the scene's own folder and
    then the repo root.  The shadow lives elsewhere, so the same two candidates
    are tried here and the hit is written as an absolute path: the loader then
    finds it from any directory.
    """
    out = {k: v for k, v in raw.items() if k not in V2_KEYS}
    out["version"] = 1
    base = os.path.dirname(full)
    for b in out.get("buildings") or []:
        if not isinstance(b, dict):
            continue
        # v2 lets code_inline be a list of lines (it reads better in JSON); the v1
        # loader does str(b["code_inline"]), which would stringify the Python list
        # into "['ubind @flare', ...]" and compile to nothing.
        if isinstance(b.get("code_inline"), list):
            b["code_inline"] = "\n".join(str(ln) for ln in b["code_inline"])
        code = b.get("code")
        if not code or os.path.isabs(str(code)):
            continue
        for cand in (os.path.join(base, str(code)), os.path.join(ROOT, str(code))):
            if os.path.exists(cand):
                b["code"] = cand
                break
    return out


def _has_code_list(raw: dict) -> bool:
    """True when some building carries code_inline as a list of lines.

    Such a file must take the shadow path even if it claims to be v1: the v1
    loader does str(b["code_inline"]) and would write the Python repr of a list.
    """
    for b in raw.get("buildings") or []:
        if isinstance(b, dict) and isinstance(b.get("code_inline"), list):
            return True
    return False


def load(path: str, *, via: str | None = None) -> dict:
    """Read + validate + normalize a scenario file; the result carries "path".

    Raises ScenarioError when the file is not a scenario at all (unreadable JSON,
    unknown keys, scene-level errors).  Field-level v2 problems are collected by
    validate() and raised here as one message, so a caller never gets a
    half-normalized dict it would have to re-check.

    ``via`` (§2 P2) asks one extra question at load time: can every modifier run
    under that host?  A run-path caller leaves it empty and lets the modifier
    list its own notes instead -- refusing to load would leave a world run with
    nothing to say about the disturbance it could not fire.
    """
    full = path if os.path.isabs(path) else os.path.abspath(path)
    if not os.path.exists(full):
        raise ScenarioError("scenario not found: %s" % full)
    try:
        raw = _read_json(full)
    except json.JSONDecodeError as exc:
        raise ScenarioError("not valid JSON: %s" % exc) from exc
    if not isinstance(raw, dict):
        raise ScenarioError("scenario must be a JSON object")

    unknown = set(raw) - ALLOWED_KEYS
    if unknown:
        raise ScenarioError("unknown top-level key(s): %s" % ", ".join(sorted(unknown)))
    if not isinstance(raw.get("version") or 1, (int, float)) or isinstance(raw.get("version"), bool):
        raise ScenarioError("version must be a number")

    v2 = (int(raw.get("version") or 0) >= 2
          or any(k in raw for k in V2_KEYS if k != "title"))
    # A v1 file may still spell code_inline as a list of lines; it goes through
    # the shadow as well, but only v2 files get v2 validation.
    if v2 or _has_code_list(raw):
        shadow = _shadow_path(full)
        with open(shadow, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(_strip_to_v1(raw, full), fh, ensure_ascii=False, indent=2)
        base = shadow
    else:
        base = full

    try:
        sc = _scene.load(base)
    except _scene.SceneError as exc:
        raise ScenarioError(str(exc)) from exc

    sc["path"] = full
    sc["dir"] = os.path.dirname(full)
    sc["version"] = 2 if v2 else 1
    if raw.get("name"):
        sc["name"] = str(raw["name"])
    _apply_v2(sc, raw, v2)

    errors = validate(sc, via=via)
    if errors:
        raise ScenarioError("; ".join(errors))
    return sc


def _apply_v2(sc: dict, raw: dict, v2: bool) -> None:
    """Copy/normalize the v2 keys.  Ill-typed values are kept as-is so that
    validate() can name them precisely instead of this function crashing."""
    if not v2:
        sc["id"] = str(sc.get("name") or "")
        sc["title"] = str(raw.get("title") or sc.get("name") or "")
        sc["goal"] = str(raw.get("goal") or "")
        sc["limits"] = dict(DEFAULT_LIMITS)
        sc["observations"] = []
        sc["assertions"] = []
        sc["success_criteria"] = {"all_assertions": True}
        sc["modifiers"] = []
        return

    sc["id"] = raw.get("id")
    sc["title"] = raw.get("title")
    sc["goal"] = raw.get("goal")
    sc["limits"] = raw.get("limits")
    observations = raw.get("observations")
    sc["observations"] = observations if isinstance(observations, list) else (
        [] if observations is None else observations)
    assertions = raw.get("assertions")
    sc["assertions"] = assertions if isinstance(assertions, list) else (
        [] if assertions is None else assertions)
    sc["success_criteria"] = raw.get("success_criteria") or {"all_assertions": True}
    modifiers = raw.get("modifiers")
    sc["modifiers"] = modifiers if isinstance(modifiers, list) else (
        [] if modifiers is None else modifiers)


def _positive_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def _positive_num(value) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and value > 0)


def validate(sc: dict, via: str | None = None) -> list[str]:
    """Everything wrong with this scenario, as text.  Empty list = runnable.

    Works on a hand-built dict as well as a loaded one: every field is read with
    .get() and every type is checked, so a test can feed it a broken literal.
    """
    errs: list[str] = []
    if not isinstance(sc, dict):
        return ["scenario must be an object"]
    try:
        errs.extend(_scene.validate(sc))
    except Exception as exc:  # noqa: BLE001 -- a malformed dict must be reported, not raised
        errs.append("scene validation failed: %s: %s" % (type(exc).__name__, exc))

    version = sc.get("version") or 1
    v2 = isinstance(version, (int, float)) and version >= 2

    limits = sc.get("limits")
    if limits is not None and not isinstance(limits, dict):
        errs.append("limits must be an object")
        limits = None
    if v2:
        if limits is None:
            errs.append("limits is required ({\"ticks\": int, \"timeout_s\": float})")
        else:
            if limits.get("ticks") is None:
                errs.append("limits.ticks is required")
            elif not _positive_int(limits.get("ticks")):
                errs.append("limits.ticks must be a positive integer, got %r"
                            % (limits.get("ticks"),))
            if limits.get("timeout_s") is not None and not _positive_num(limits.get("timeout_s")):
                errs.append("limits.timeout_s must be a positive number, got %r"
                            % (limits.get("timeout_s"),))
        for key, desc in (("id", "short stable slug"), ("title", "one line"),
                          ("goal", "what the scenario proves")):
            value = sc.get(key)
            if not isinstance(value, str) or not value.strip():
                errs.append("%s is required for schema v2 (%s)" % (key, desc))

    buildings = [b for b in (sc.get("buildings") or []) if isinstance(b, dict)]
    by_name = {b.get("name"): b for b in buildings if b.get("name")}
    with_code = {b.get("name") for b in buildings if b.get("code")}

    observations = sc.get("observations")
    if observations is not None and not isinstance(observations, list):
        errs.append("observations must be a list")
        observations = []
    observations = observations or []
    seen_obs: set = set()
    for i, obs in enumerate(observations):
        where = "observations[%d]" % i
        if not isinstance(obs, dict):
            errs.append("%s must be an object" % where)
            continue
        for key in ("name", "logic", "var"):
            if not isinstance(obs.get(key), str) or not obs.get(key, "").strip():
                errs.append("%s needs a non-empty %r" % (where, key))
        name = obs.get("name")
        if isinstance(name, str):
            if name in seen_obs:
                errs.append("%s: duplicate observation name %r" % (where, name))
            seen_obs.add(name)
        agg = obs.get("aggregate", "last")
        if agg not in AGGREGATES:
            errs.append("%s.aggregate must be one of %s, got %r"
                        % (where, "/".join(AGGREGATES), agg))
        logic = obs.get("logic")
        if isinstance(logic, str) and by_name and logic not in by_name:
            errs.append("%s.logic %r is not a building of this scene (%s)"
                        % (where, logic, ", ".join(sorted(by_name))))

    assertions = sc.get("assertions")
    if assertions is not None and not isinstance(assertions, list):
        errs.append("assertions must be a list")
        assertions = []
    assertions = assertions or []
    seen_ids: set = set()
    for i, a in enumerate(assertions):
        where = "assertions[%d]" % i
        if not isinstance(a, dict):
            errs.append("%s must be an object" % where)
            continue
        for key in ("id", "logic", "var"):
            if not isinstance(a.get(key), str) or not a.get(key, "").strip():
                errs.append("%s needs a non-empty %r" % (where, key))
        aid = a.get("id")
        if isinstance(aid, str):
            if aid in seen_ids:
                errs.append("%s: duplicate assertion id %r" % (where, aid))
            seen_ids.add(aid)
        op = a.get("op", "eq")
        if op not in OPS:
            errs.append("%s.op must be one of %s, got %r"
                        % (where, "/".join(OPS), op))
        if "value" not in a:
            errs.append("%s needs 'value' (the expected value)" % where)
        logic = a.get("logic")
        if isinstance(logic, str) and by_name and logic not in by_name:
            errs.append("%s.logic %r is not a building of this scene (%s)"
                        % (where, logic, ", ".join(sorted(by_name))))
        elif isinstance(logic, str) and with_code and logic not in with_code:
            errs.append("%s.logic %r has no code -- assertions read a processor's "
                        "variables, and this building is not one" % (where, logic))
        named = a.get("observation")
        if named is not None and named not in seen_obs:
            errs.append("%s.observation %r is not one of this scenario's "
                        "observations (%s)"
                        % (where, named, ", ".join(sorted(seen_obs)) or "none"))

    if v2 and not assertions:
        errs.append("a v2 scenario needs at least one assertion (otherwise it "
                    "cannot fail)")

    crit = sc.get("success_criteria")
    if crit is not None:
        if not isinstance(crit, dict):
            errs.append("success_criteria must be an object")
        else:
            if crit.get("all_assertions") is not True:
                errs.append("success_criteria.all_assertions must be true: schema "
                            "v2 declares every assertion mandatory")

    modifiers = sc.get("modifiers")
    if modifiers is not None:
        if not isinstance(modifiers, list):
            errs.append("modifiers must be a list of {kind, at_tick, params} "
                        "objects, got %s" % type(modifiers).__name__)
        elif len(modifiers) > _modifier.MAX_ENTRIES:
            errs.append("modifiers has %d entries; at most %d keep a timeline "
                        "measurable" % (len(modifiers), _modifier.MAX_ENTRIES))
        else:
            ctx = _modifier_ctx(sc)
            for i, entry in enumerate(modifiers):
                _, problems = _modifier.validate_entry(entry, ctx)
                for problem in problems:
                    errs.append("modifiers[%d]: %s" % (i, problem))
                kind = entry.get("kind") if isinstance(entry, dict) else None
                hosts = _modifier.KINDS.get(kind, {}).get("via") if kind else None
                if via and hosts and via not in hosts:
                    errs.append("modifiers[%d]: %s does not run under via=%s "
                                "(declared for %s)"
                                % (i, kind, via, "/".join(hosts)))
    return errs


def _modifier_ctx(sc: dict, via: str | None = None) -> dict:
    """What a modifier may consult: world size, tick budget, team, the scene.

    Kept separate from the run so `validate`/`load`/`generate` can check an
    entry without an executor -- the same context the runtime passes down.
    """
    limits = sc.get("limits")
    ticks = limits.get("ticks") if isinstance(limits, dict) else None
    world = sc.get("world")
    size = world.get("size") if isinstance(world, dict) else None
    units = sc.get("units") or []
    return {
        "size": size if isinstance(size, int) and size > 0 else None,
        "ticks": ticks if _positive_int(ticks) else None,
        "team": _scene_team(sc),
        "units": units,
        "buildings": sc.get("buildings") or [],
        # How many units the scene declares; a pick cannot count live units.
        "pool": sum(int(u.get("count") or 1) for u in units if isinstance(u, dict)) or 1,
        "via": via,
    }



def warnings(sc: dict) -> list[str]:
    """Non-fatal smells: a check/assertion nothing observes, a v1 scene."""
    out: list[str] = []
    if (sc.get("version") or 1) < 2:
        out.append("version 1 scene: run through checks only (no limits/observations)")
    if sc.get("path"):
        for w in _scene.warn_labeled(sc):
            out.append(w)
    return out


# ---------------------------------------------------------------- environment

def environment(*, cached: bool = True) -> dict:
    """{"ok", "java", "jar", "notes"} for the simulator host.

    A missing jar or a Java 8 runtime is `unsupported_environment`, not a
    scenario failure: retrying will not help, so the envelope says so.
    """
    if cached and _ENV_CACHE:
        return _ENV_CACHE
    notes: list[str] = []
    try:
        import mlogsim
        java = mlogsim._default_java()
        jar = mlogsim._default_jar()
    except Exception as exc:  # noqa: BLE001
        env = {"ok": False, "java": "", "jar": "",
               "notes": ["cannot import mlogsim: %s: %s" % (type(exc).__name__, exc)]}
        _ENV_CACHE.update(env)
        return env
    if not jar or not os.path.exists(jar):
        notes.append("missing server jar (looked for out/_server160.jar, "
                     "out/_server159.jar, out/_server146.jar); set MLOGSIM_JAR")
    if not java or not (os.path.exists(java) or not os.path.dirname(java)):
        notes.append("missing java (set MLOGSIM_JAVA or install a JRE 21)")
    else:
        ok, why = _java_major(java)
        if not ok:
            notes.append(why)
    env = {"ok": not notes, "java": java, "jar": jar, "notes": notes}
    _ENV_CACHE.update(env)
    return env


def _java_major(java: str) -> tuple:
    """(usable, why-not).  Runs `java -version` once; the answer is cached."""
    try:
        proc = subprocess.run([java, "-version"], capture_output=True, text=True,
                              timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        return False, "cannot run %s: %s" % (java, exc)
    text = (proc.stderr or "") + (proc.stdout or "")
    match = re.search(r'version "(\d+)', text)
    if not match:
        return True, ""                       # unparseable but it runs: trust it
    major = int(match.group(1))
    if major < MIN_JAVA_MAJOR:
        return False, ("java %d at %s is too old (need %d+; the repo's JRE 21 is "
                       "out/jre21/jdk-21.0.5+11-jre)" % (major, java, MIN_JAVA_MAJOR))
    return True, ""


# ---------------------------------------------------------------- evaluation

def _as_number(value, default=None):
    """float(value) if it parses, else default."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _format_number(value):
    """Integral floats read as ints in JSON (95, not 95.0)."""
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def aggregate(values: list, how: str):
    """Fold per-tick samples into the value an assertion compares against.

    Samples that never resolved are dropped first: mlog prints an unset variable
    as the text "null", and one such sample must not win a `last` fold (the unit
    control template reads @x before it has a bound unit, for instance).
    """
    clean = [v for v in values
             if v is not None and str(v).strip() not in ("", "null")]
    if not clean:
        return None
    numbers = [n for n in (_as_number(v) for v in clean) if n is not None]
    if numbers and len(numbers) == len(clean):
        if how == "max":
            return _format_number(max(numbers))
        if how == "min":
            return _format_number(min(numbers))
        if how == "sum":
            return _format_number(sum(numbers))
        return _format_number(numbers[-1])
    if how == "sum":
        return None if not numbers else _format_number(sum(numbers))
    if how in ("max", "min"):
        return None if not numbers else _format_number({"max": max, "min": min}[how](numbers))
    return clean[-1]


def _same(actual, expect, refs: dict) -> bool:
    """Equality with the semantics scene.check_vars uses, plus bools.

    A string expectation that names a scene building compares as that building
    (`Building#211[30,32]:container`), so an assertion can say "container1"
    without pinning the engine's entity id.
    """
    text = str(actual).strip() if actual is not None else ""
    if isinstance(expect, str) and expect in refs:
        ox, oy, block = refs[expect]
        return text.endswith("[%d,%d]:%s" % (ox, oy, block))
    if isinstance(expect, bool):
        wanted = ("true", "1", "1.0") if expect else ("false", "0", "0.0", "null")
        return text in wanted
    a, e = _as_number(actual), _as_number(expect)
    if a is not None and e is not None:
        return abs(a - e) < 1e-6
    return text == str(expect)


def compare(actual, op: str, expect, refs: dict | None = None) -> bool:
    """Evaluate one assertion against one observed value.

    `ne` is "not equal" (including when there is no value at all, which is how
    "the variable never appeared" is expressed); the ordered ops are numeric
    only, because "abc" > 3 has no meaning here.
    """
    refs = refs or {}
    if op == "ne":
        return actual is None or not _same(actual, expect, refs)
    if actual is None:
        return False
    if op == "contains":
        return str(expect) in str(actual)
    if op in ("gt", "ge", "lt", "le"):
        a, e = _as_number(actual), _as_number(expect)
        if a is None or e is None:
            return False
        return {"gt": a > e, "ge": a >= e, "lt": a < e, "le": a <= e}[op]
    return _same(actual, expect, refs)


def _deadline_guard(deadline: float, tick: int) -> None:
    if time.time() > deadline:
        raise _Timeout("limits.timeout_s expired after %d tick(s)" % tick)


# ---------------------------------------------------------------- the sim run

_SAMPLE_JS = (
    "for(var i=0;i<SCN_OBS.length;i++){"
    "var o=SCN_OBS[i],s='',b=null;"
    "var tt=Vars.world.tile(o.x,o.y);if(tt!=null){b=tt.build;}"
    "if(b!=null){var vs=b.executor.vars;"
    "for(var q=0;q<vs.length;q++){if(vs[q].name==o.var){"
    "try{s=vs[q].isobj?String(vs[q].objval):String(vs[q].numval);}catch(e2){s='?';}"
    "break;}}}"
    "SCN_VALS[i].push(s);}"
)


def _step_js(ticks: int, sample: bool) -> str:
    """One `js` command: run `ticks` world ticks with every scene processor."""
    return (
        "var GS=Packages.mindustry.core.GameState,ST=GS.State;"
        "Vars.state.set(ST.playing);Time.delta=1.0;"
        "try{for(var t=0;t<%d;t++){"
        "Vars.state.tick++;Time.update();Vars.logicVars.update();"
        "worldTick();unitTick();"
        "var P=(typeof PROCS=='undefined'?[]:PROCS);"
        "for(var j=0;j<P.length;j++){P[j].updateTile();}"
        "%s"
        "}}finally{Vars.state.set(ST.paused);}"
        % (ticks, _SAMPLE_JS if sample else "")
    )

#: Final variable table.  mlogsim.SCENE_DUMP_JS does the same through
#: `globalThis.procs`, which this Rhino does not have -- a top-level `var` is the
#: global here, so the scene's own PROCS array is read directly.
_DUMP_JS = (
    "var _P=(typeof PROCS=='undefined'?[]:PROCS);var _n=0;"
    "for(var i=0;i<_P.length;i++){var b=_P[i];var vs=b.executor.vars;_n++;"
    "print('@@BEGIN" + "\t" + "'+b.tileX()+','+b.tileY());"
    "for(var j=0;j<vs.length;j++){var v=vs[j];var val;"
    "if(v.isobj){val=String(v.objval);}else{val=''+v.numval;}"
    "print('VAR" + "\t" + "'+v.name+'" + "\t" + "'+val);}"
    "print('COUNTER" + "\t" + "'+b.executor.counter.numval);"
    "print('IPT" + "\t" + "'+b.executor.ipt.numval);"
    "print('ACC" + "\t" + "'+b.accumulator);"
    "print('@@END');}"
    "print('DUMPED" + "\t" + "'+_n);"
)


def _js(srv, script: str) -> list:
    """Run one `js` script and return what it printed.

    The console echoes the *value* of the script's last expression, and
    `Server.js` waits for the literal "undefined": a script that ends in a loop
    or an assignment echoes "4.0" instead and then blocks until the js timeout.
    Pinning `void 0` at the tail makes every call terminate.
    """
    return srv.js(script.rstrip().rstrip(";") + ";void 0")


def _prepare_js(sc: dict) -> str:
    """Rules a scene needs before its units are spawned.

    A blank world has no cores, so `Units.getCap()` is 0 and `UnitType.spawn()`
    returns a unit that is already dead (`dead=true`, dropped from Groups.unit on
    the next frame): the spawn "succeeds" and then nothing is there.  Raising the
    rule cap is what makes the units in the scene real.
    """
    total = sum(int(u.get("count") or 1) for u in sc.get("units") or [])
    return "Vars.state.rules.unitCap=%d;" % max(64, total * 8 + 32)


def _modifier_queue(sc: dict, via: str) -> list[dict]:
    """Every declared disturbance, sorted by tick, with its JS prebuilt.

    Sorting is `(at_tick, declaration index)` (``modifier.sort_entries``), so two
    entries on the same tick fire in the order the file lists them.  An entry
    that cannot run on this host is kept in the queue with ``executed=False`` and
    the reason in ``notes``: the run records what did *not* happen too, rather
    than dropping it or pretending.
    """
    entries = sc.get("modifiers") or []
    if not entries:
        return []
    ctx = _modifier_ctx(sc, via)
    # Structural problems (bad kind/params/at_tick) are a broken file: raise.
    # Applicability (via, missing units/core) is *not*: it becomes a note, so a
    # via=world run still reports the disturbance it could not fire.
    shape = _modifier_ctx(sc)
    queue = []
    for index, entry in enumerate(entries):
        norm, problems = _modifier.validate_entry(entry, shape)
        if problems:
            raise ScenarioError("modifiers[%d]: %s" % (index, "; ".join(problems)))
        kind = norm["kind"]
        rec = {"kind": kind, "at_tick": norm["at_tick"],
               "params": dict(entry.get("params") or {}), "seed": norm.get("seed"),
               "_index": index, "executed": False, "applied_at_tick": None,
               "burned": 0, "plan": [], "lines": [], "error": "", "notes": []}
        reasons = []
        if via not in _modifier.KINDS[kind]["via"]:
            reasons.append("declared for via=%s only; a via=%s run cannot fire it"
                           % ("/".join(_modifier.KINDS[kind]["via"]), via))
        reasons.extend(_modifier.requirements_errors(kind, ctx))
        built = None
        if not reasons:
            try:
                built = _modifier.script(norm, dict(ctx, via=via, flavor=via,
                                                    at_tick=norm["at_tick"]))
            except _modifier.ModifierError as exc:
                raise ScenarioError("modifiers[%d]: %s" % (index, exc)) from exc
        if reasons:
            rec["notes"] = reasons
        else:
            rec["_script"] = built["script"]
            rec["plan"] = built["plan"]
            rec["_burn"] = int(built["skip"])
        queue.append(rec)
    return _modifier.sort_entries(queue)


def _modifier_fire(rec: dict, apply_js, done: int) -> int:
    """Apply one queued disturbance at tick ``done``; returns the new tick.

    ``apply_js`` runs a one-line script on the host and returns its printed
    lines.  A disturbance that throws is recorded, not raised: a scenario whose
    program is under test should still report its assertions when a modifier
    misfires.
    """
    if not rec.get("_script"):
        return done
    try:
        lines = apply_js(rec["_script"]) or []
    except Exception as exc:  # noqa: BLE001 -- recorded; the run continues
        rec["error"] = "%s: %s" % (type(exc).__name__, exc)
        return done
    rec["lines"] = [str(line) for line in lines if str(line).startswith("MOD")]
    bad = [line for line in rec["lines"] if line.startswith("MODERR")]
    if bad:
        rec["executed"] = False
        rec["error"] = bad[0].split("\t", 2)[-1]
    elif rec["lines"]:
        rec["executed"] = True
    else:
        rec["executed"] = False
        rec["error"] = "the host ran the script but printed no MOD line"
    rec["applied_at_tick"] = done
    burn = int(rec.pop("_burn", 0) or 0)
    rec["burned"] = burn
    return done + burn


def _modifier_flush(queue: list[dict], fire, done: int) -> None:
    """Fire every queued disturbance whose tick has been reached.

    The live clock is polled, so an entry lands on the first poll *at or after*
    its tick; the record keeps both numbers and says so in ``notes`` instead of
    claiming the exact tick.
    """
    for rec in queue:
        if not rec.get("_script") or rec.get("applied_at_tick") is not None:
            continue
        planned = int(rec["at_tick"])
        if planned > done:
            break  # the queue is sorted; nothing later is due yet
        _modifier_fire(rec, fire, done)
        if rec.get("applied_at_tick") is not None and rec["applied_at_tick"] != planned:
            rec["notes"].append(
                "fired at tick %d instead of %d: via=world polls the live clock "
                "instead of stepping it (overshoot %d ticks)"
                % (rec["applied_at_tick"], planned,
                   rec["applied_at_tick"] - planned))


def _public_modifiers(queue: list[dict]) -> list[dict]:
    """Drop the private JS/burn keys before the record becomes JSON."""
    return [{k: v for k, v in rec.items() if not k.startswith("_")}
            for rec in queue]


def _sim(sc: dict, deadline: float) -> dict:
    """Lay the scene down, tick it, sample observations; returns the raw record.

    To watch a run in the live world, project it with the tools that already do
    that (`mlogsim.py --push` feeding `world_client.py arm`): the scenario runner
    stays one experiment, not one experiment plus a renderer.
    """
    import mlogsim

    env = environment()
    if not env["ok"]:
        raise _Environment("; ".join(env["notes"]))

    srv = mlogsim.Server(env["java"], env["jar"], world_size=sc["world"]["size"])
    try:
        remaining = max(5.0, deadline - time.time())
        srv.js_timeout = remaining
        if sc.get("units"):
            _js(srv, _prepare_js(sc))
        srv._scene = sc
        srv.prepare()
        report = getattr(srv, "_scene_report", None) or {}
        if report.get("errors"):
            raise ScenarioError("scene did not apply: " + "; ".join(report["errors"]))

        refs = _scene.building_index(sc, report)
        shift = list(report.get("shift") or [0, 0])[:2]
        # The scene's units are picked out now, while they are still where the
        # scene put them: by the end of the run they have moved (that is usually
        # the point of the scenario), and a live world has other units anyway.
        ids = _picked(_js(srv, _select_js(sc, shift, False))) if sc.get("units") else []
        observations = list(sc.get("observations") or [])
        specs = []
        for obs in observations:
            where = refs.get(obs["logic"])
            if where is None:
                raise ScenarioError("observation %r: %r is not a placed building"
                                    % (obs["name"], obs["logic"]))
            specs.append({"x": where[0], "y": where[1], "var": obs["var"]})

        if observations:
            _js(srv, mlogsim._world_js(1.0, "logic")
                + "var SCN_OBS=%s;var SCN_VALS=[];"
                  "for(var i=0;i<SCN_OBS.length;i++){SCN_VALS.push([]);}"
                % json.dumps(specs))
        else:
            _js(srv, mlogsim._world_js(1.0, "logic"))

        total = int(sc["limits"]["ticks"])
        mods = _modifier_queue(sc, "sim")
        fire = lambda js: _js(srv, js)  # noqa: E731 -- one host call, one line
        done = 0
        pending = 0
        while done < total:
            _deadline_guard(deadline, done)
            # A modifier acts *before* its tick, so the timeline is split at
            # every at_tick: run 0 -> at_tick, apply the disturbance, continue.
            while pending < len(mods) and int(mods[pending]["at_tick"]) <= done:
                done = _modifier_fire(mods[pending], fire, done)
                pending += 1
            if done >= total:
                break
            nxt = int(mods[pending]["at_tick"]) if pending < len(mods) else total
            step = min(TICK_CHUNK, total - done, max(1, nxt - done))
            _js(srv, _step_js(step, bool(observations)))
            done += step
        # Everything at exactly limits.ticks still fires: no segment is left to
        # run, but at_tick == total is a legal point on the timeline.
        while pending < len(mods):
            done = _modifier_fire(mods[pending], fire, done)
            pending += 1
        _deadline_guard(deadline, done)

        samples: dict[int, list] = {}
        if observations:
            lines = _js(srv, "for(var i=0;i<SCN_VALS.length;i++){"
                             "for(var q=0;q<SCN_VALS[i].length;q++){"
                             "print('OV\\t'+i+'\\t'+SCN_VALS[i][q]);}}")
            for line in lines:
                parts = line.split("\t")
                if len(parts) >= 3 and parts[0] == "OV":
                    try:
                        samples.setdefault(int(parts[1]), []).append(parts[2])
                    except ValueError:
                        continue

        finals: dict[str, dict] = {}
        for rec in mlogsim.parse_results(_js(srv, _DUMP_JS)):
            name = _record_name(sc, refs, rec.get("label") or "")
            if name:
                finals[name] = rec.get("vars") or {}

        checks: list = []
        if sc.get("checks"):
            srv._scene_report = report
            checks = _scene.probe_sim(srv, sc)["checks"]

        # The final state, so the offline side has something to compare against
        # the live one: same two snapshots `_world()` takes, same `js` bodies.
        units, _ = _snapshot(_js(srv, _units_js(ids, False)))
        _, buildings = _snapshot(_js(srv, _builds_js(refs, False)))

        return {"ticks": done, "samples": samples, "finals": finals,
                "checks": checks, "report": report, "refs": refs,
                "units": units, "buildings": buildings,
                "modifiers": _public_modifiers(mods)}
    finally:
        try:
            srv.close()
        except Exception:  # noqa: BLE001 -- closing twice is not an error worth reporting
            pass


class _Environment(Exception):
    """Internal: this machine cannot run the scenario."""


def _record_name(sc: dict, refs: dict, label: str) -> str:
    """Map a dump row ("x,y") back to the scene building name it belongs to."""
    try:
        xy = tuple(int(float(v)) for v in label.split(",")[:2])
    except ValueError:
        return ""
    for name, (x, y, _block) in refs.items():
        if (x, y) == xy:
            return name
    return ""


# ---------------------------------------------------------------- the live world
#
# Everything below is the `via="world"` half: it talks to `tools/world_server.py`
# through `tools/world_client.py` (the daemon's JSON-line protocol) and returns
# the same record `_sim()` does, so nothing above this line has to care which
# host ran the scenario.  The ops used are:
#
#   status       map/world size/clock/paused -- the experiment's environment
#   changes      the daemon's tile/config event log (ring buffer, `nextSeq`)
#   js           one script, its lines come back (the daemon appends to `sb`)
#   scene        apply a scene *file* (v1: the daemon loads it with scene.load)
#   logic_vars   one processor's variable table, values already coerced
#
# Coordinates: the daemon speaks tiles for tile-addressed ops (`scene`,
# `logic_vars`, `units`) and the scene's own spiral is in pixels (`*8`), so the
# unit picker is the only place that divides.  `js` bodies must not contain a real
# newline -- `World.js` folds the body onto one `js ...` console line.

def _world_client():
    """The daemon client, imported lazily: only `via="world"` needs it."""
    import world_client

    return world_client


def _host_version(jar, java=None) -> tuple:
    """(mindustry "vNNN", java "x.y.z") read off the daemon's own binaries.

    Same two regexes `observation.detect_env()` uses, but pointed at the handshake
    file so the live side reports the jar it is *actually* running, not the one
    the offline host would pick.
    """
    mid = None
    match = re.search(r"_server(\d+)\.jar", str(jar or ""))
    if match:
        mid = "v" + match.group(1)
    ver = None
    match = re.search(r"jdk-(\d+\.\d+\.\d+)", str(java or ""))
    if match:
        ver = match.group(1)
    return mid, ver


def world_environment() -> dict:
    """Is a live world there, and what is it?  Never raises, says why it cannot.

    A handshake file is not proof: a killed daemon leaves `daemon.json` behind
    and every call then dies with a refused connection -- which must read as
    "no environment", not as a difference between the two hosts.
    """
    out = {"ok": False, "why": "", "notes": [], "handshake": None, "status": None,
           "mindustry": None, "java": None, "jar": None, "map": None,
           "world_size": None, "tick": None, "paused": None}
    try:
        client = _world_client()
    except Exception as exc:  # noqa: BLE001 -- a missing client is an environment fact
        out["notes"].append("tools/world_client.py is not importable: %s: %s"
                            % (type(exc).__name__, exc))
        out["why"] = out["notes"][-1]
        return out
    try:
        hs = client.handshake()
    except Exception as exc:  # noqa: BLE001 -- WorldError when there is no file
        out["notes"].append(str(exc))
        out["why"] = str(exc)
        return out
    out["handshake"] = hs
    out["java"], out["jar"] = hs.get("java"), hs.get("jar")
    out["mindustry"], java_ver = _host_version(out["jar"], out["java"])
    if java_ver:
        out["notes"].append("world java %s" % java_ver)
    try:
        status = client.call({"op": "status"}, timeout=20.0, hs=hs)
    except Exception as exc:  # noqa: BLE001
        out["notes"].append("%s: %s" % (type(exc).__name__, exc))
        where = os.path.relpath(str(getattr(client, "HANDSHAKE", "daemon.json")),
                                ROOT)
        out["why"] = ("%s exists but the daemon is not answering: %s"
                      % (where, exc))
        return out
    if not isinstance(status, dict) or not status.get("ok"):
        out["notes"].append("world status refused: %r" % (status,))
        out["why"] = "the world daemon refused `status`: %r" % (
            (status or {}).get("error"),)
        return out
    out["status"] = status
    out["map"] = status.get("map")
    out["world_size"] = [status.get("width"), status.get("height")]
    out["tick"] = status.get("tick")
    out["paused"] = bool(status.get("paused"))
    out["ok"] = True
    return out


def _slug(sc: dict) -> str:
    """A file-name-safe scenario id, derived from the path (never absolute)."""
    stem = os.path.splitext(os.path.basename(str(sc.get("path") or "")))[0]
    stem = stem or str(sc.get("id") or sc.get("name") or "scenario")
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", stem).strip("-") or "scenario"


def _world_scene_file(sc: dict) -> str:
    """Write the scene v1 projection the live world applies; return its path.

    The daemon is a separate process: it reads this file with `scene.load()`, so
    it must be plain scene v1 (no scenario keys, `code_inline` folded, `code`
    paths absolute) at an absolute path -- the daemon's cwd is its data dir.

    Two deliberate edits:

    * `project.units = "spawn"`.  The default ("mirror") is a *display* mode: it
      disables every processor and draws units as markers, which is the exact
      opposite of an experiment.  The scene's units have to be real objects the
      processor can bind, so the world spawns them.
    * `project.at` / `project.anchor` dropped.  The offline host always applies
      the scene at its own coordinates (`apply_sim` never translates), so moving
      the live copy would compare two different experiments.
    """
    raw = _read_json(sc["path"])
    proj = _strip_to_v1(raw, sc["path"])
    project = dict(proj.get("project") or {})
    project["units"] = "spawn"
    project.pop("at", None)
    project.pop("anchor", None)
    proj["project"] = project
    os.makedirs(WORLD_SCENE_DIR, exist_ok=True)
    path = os.path.join(WORLD_SCENE_DIR, "%s.json" % _slug(sc))
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(proj, fh, ensure_ascii=False, indent=2)
    return path


def _scene_team(sc: dict) -> str:
    """The team the scenario speaks for: the first unit's, else a building's."""
    for u in sc.get("units") or []:
        if u.get("team"):
            return str(u["team"])
    for b in sc.get("buildings") or []:
        if b.get("team"):
            return str(b["team"])
    return "sharded"


def _text(value) -> str:
    """A log value as text: 149, 149.0 and "149" are the same variable."""
    number = _as_number(value)
    if number is None:
        return "" if value is None else str(value)
    return str(_format_number(number))


def _lines(res: dict) -> list:
    return [str(ln) for ln in (res.get("lines") or [])]


def _num(text):
    """A dumped number: int when integral, float otherwise, None when unset."""
    number = _as_number(text)
    if number is None:
        return None
    return _format_number(number)


def _rep(world: bool, expr: str) -> str:
    """One report line: `print` offline, `sb.append(...+'\\n')` on the daemon."""
    if world:
        return "sb.append(%s+'\\n')" % expr
    return "print(%s)" % expr


def _picked(lines: list) -> list:
    """The unit ids `_select_js` reported, in order."""
    ids = []
    for line in lines:
        parts = str(line).split("\t")
        if parts[0] == "I" and len(parts) > 1:
            number = _num(parts[1])
            if number is not None:
                ids.append(int(number))
    return ids


def _select_js(sc: dict, shift, world: bool) -> str:
    """Ids of the units the scene just spawned (the live world has others)."""
    points = []
    for u in sc.get("units") or []:
        for wx, wy in _scene._unit_positions(u):
            points.append([round(wx / 8.0, 3) + float(shift[0]),
                           round(wy / 8.0, 3) + float(shift[1])])
    return (
        "var PTS=%s;var G=Packages.mindustry.gen.Groups.unit;"
        "for(var i=0;i<G.size();i++){var u=G.index(i);"
        "if(u==null||u.dead){continue;}"
        "var ux=u.x/8,uy=u.y/8;"
        "for(var k=0;k<PTS.length;k++){"
        "var ddx=ux-PTS[k][0],ddy=uy-PTS[k][1];"
        "if(ddx*ddx+ddy*ddy<=%f){%s;break;}}}"
        % (json.dumps(points), WORLD_UNIT_PICK_R, _rep(world, "'I\\t'+u.id"))
    )


def _units_js(ids: list, world: bool) -> str:
    """Final state of exactly those units, in tiles (pixels / 8)."""
    return (
        "var IDS=%s;var G=Packages.mindustry.gen.Groups.unit;"
        "for(var i=0;i<IDS.length;i++){var u=G.getByID(IDS[i]);"
        "if(u==null||u.dead){continue;}"
        "var cu='';try{var ku=u.controller();"
        "if(ku!=null){cu=ku.getClass().getSimpleName();}}catch(e0){}"
        "var lx=Math.round(u.x/8*1000)/1000,ly=Math.round(u.y/8*1000)/1000;"
        "%s}"
        % (json.dumps([int(i) for i in ids]),
           _rep(world, "'U\\t'+u.id+'\\t'+u.type.name+'\\t'+u.team.name+'\\t'"
                       "+lx+'\\t'+ly+'\\t'+Math.round(u.health)+'\\t'+cu"))
    )


def _builds_js(refs: dict, world: bool) -> str:
    """Per-building item counts; the daemon's `buildings` op only has the total."""
    tiles = [[int(v[0]), int(v[1])] for v in refs.values()]
    return (
        "var TILES=%s;"
        "for(var i=0;i<TILES.length;i++){"
        "var bt=Vars.world.tile(TILES[i][0],TILES[i][1]);"
        "var bb=bt==null?null:bt.build;if(bb==null){continue;}"
        "var it='';try{var md=bb.items;if(md!=null){"
        "var its=Vars.content.items();"
        "for(var k=0;k<its.size;k++){var ii=its.get(k);var nn=md.get(ii);"
        "if(nn>0){it+=(it?',':'')+ii.name+'='+nn;}}}}catch(e1){it='?';}"
        "%s}"
        % (json.dumps(tiles),
           _rep(world, "'B\\t'+bb.tile.x+'\\t'+bb.tile.y+'\\t'+bb.block.name"
                       "+'\\t'+bb.team.name+'\\t'+it"))
    )


def _core_js(world: bool = True) -> str:
    """The team core's items: a core block is a StorageBlock, items live on it."""
    return (
        "var G=Packages.mindustry.gen.Groups.build;"
        "for(var i=0;i<G.size();i++){var b=G.index(i);"
        "if(b==null||b.block==null){continue;}"
        "if(!(b.block instanceof "
        "Packages.mindustry.world.blocks.storage.CoreBlock)){continue;}"
        "var it='';try{var md=b.items;if(md!=null){"
        "var its=Vars.content.items();"
        "for(var k=0;k<its.size;k++){var ii=its.get(k);var nn=md.get(ii);"
        "if(nn>0){it+=(it?',':'')+ii.name+'='+nn;}}}}catch(e2){it='?';}"
        "%s}"
        % _rep(world, "'C\\t'+b.tile.x+'\\t'+b.tile.y+'\\t'+b.team.name+'\\t'+it")
    )


def _sample_js(specs: list) -> str:
    """One poll of every observation variable; `_SAMPLE_JS` is the per-tick twin."""
    return (
        "var OBS=%s;"
        "for(var i=0;i<OBS.length;i++){var o=OBS[i],s='';"
        "var tt=Vars.world.tile(o.x,o.y);var b=null;if(tt!=null){b=tt.build;}"
        "var vs=null;if(b!=null){try{vs=b.executor.vars;}catch(e4){vs=null;}}"
        "if(vs!=null){for(var q=0;q<vs.length;q++){if(vs[q].name==o.var){"
        "try{s=vs[q].isobj?String(vs[q].objval):String(vs[q].numval);}"
        "catch(e3){s='?';}break;}}}"
        "%s}"
        % (json.dumps(specs), _rep(True, "'OV\\t'+i+'\\t'+s"))
    )


def _items(text: str) -> dict:
    """"copper=30,sand=12" -> {"copper": 30, "sand": 12}; "?" stays a marker."""
    if not text or text == "?":
        return {} if not text else {"?": text}
    out = {}
    for pair in text.split(","):
        name, _, count = pair.partition("=")
        if not name:
            continue
        out[name] = _num(count) if _num(count) is not None else count
    return out


def _snapshot(lines: list) -> tuple:
    """(units, buildings) from one `js` reply, in the shape the payload wants."""
    units, buildings = [], []
    for line in lines:
        parts = str(line).split("\t")
        if parts[0] == "U" and len(parts) >= 7:
            units.append({"id": _num(parts[1]), "type": parts[2], "team": parts[3],
                          "x": _num(parts[4]), "y": _num(parts[5]),
                          "hp": _num(parts[6]),
                          "controller": parts[7] if len(parts) > 7 and parts[7] else None,
                          "amount": None})
        elif parts[0] == "B" and len(parts) >= 5:
            # a building with no item module ends the line after its team
            buildings.append({"block": parts[3], "x": _num(parts[1]),
                              "y": _num(parts[2]), "team": parts[4],
                              "items": _items(parts[5] if len(parts) > 5 else "")})
    return units, buildings


def _core(lines: list) -> dict:
    for line in lines:
        parts = str(line).split("\t")
        if parts[0] == "C" and len(parts) >= 5:
            return {"items": _items(parts[4]), "x": _num(parts[1]),
                    "y": _num(parts[2]), "team": parts[3]}
    return {}


def _events(res: dict, tick0: int) -> list:
    """Tile/config events as the run saw them, on a clock that starts at 0.

    The daemon's ticks are absolute (`Vars.state.tick`, thousands by the time a
    rig is up); relative ticks keep the trace comparable to the offline record,
    whose clock always starts at 0.
    """
    kinds = {"P": "place", "B": "remove", "C": "config"}
    out = []
    for row in res.get("rows") or []:
        tick = int(row.get("tick") or 0) - tick0
        if tick < 0:
            continue
        out.append({"tick": tick,
                    "type": kinds.get(str(row.get("kind")), str(row.get("kind"))),
                    "block": row.get("block"), "x": row.get("x"), "y": row.get("y"),
                    "team": row.get("team"), "seq": row.get("seq")})
    out.sort(key=lambda e: (e["tick"], e["seq"] or 0))
    return out


def _collect_samples(res: dict, samples: dict) -> int:
    """Append one poll's values; returns how many samples landed."""
    got = 0
    for line in _lines(res):
        parts = line.split("\t")
        if len(parts) >= 3 and parts[0] == "OV":
            try:
                samples.setdefault(int(parts[1]), []).append(parts[2])
                got += 1
            except ValueError:
                continue
    return got


def _world(sc: dict, deadline: float) -> dict:
    """Apply the scene to the live world, let it tick, read the rig back."""
    env = world_environment()
    if not env["ok"]:
        raise _Environment(env["why"] or "; ".join(env["notes"]) or "no live world")

    client = _world_client()
    hs = env["handshake"]

    def call(req: dict, timeout: float = 60.0) -> dict:
        budget = max(5.0, min(timeout, deadline - time.time() + 5.0))
        res = client.call(req, timeout=budget, hs=hs)
        if not isinstance(res, dict):
            raise ScenarioError("world answered %r to op %r" % (res, req.get("op")))
        if not res.get("ok"):
            raise ScenarioError("world op %r failed: %s"
                                % (req.get("op"), res.get("error") or res))
        return res

    status = env["status"]
    tick0 = int(status.get("tick") or 0)
    size = [int(status.get("width") or 0), int(status.get("height") or 0)]
    was_paused = bool(status.get("paused"))
    since = int(call({"op": "changes", "since": 2 ** 31 - 1, "limit": 1},
                     30.0).get("nextSeq") or 0)

    scene_file = _world_scene_file(sc)
    if sc.get("units"):
        # A live world's unit cap comes from its cores; the scene's units must
        # not be born dead the way a blank sim world's were (see _prepare_js).
        call({"op": "js", "code": _prepare_js(sc)}, 30.0)
    if was_paused:
        call({"op": "pause", "on": False}, 30.0)
    try:
        report = dict(call({"op": "scene", "path": scene_file}, 180.0).get("scene") or {})
        if report.get("errors"):
            raise ScenarioError("scene did not apply: " + "; ".join(report["errors"]))
        shift = list(report.get("shift") or [0, 0])[:2]
        refs = _scene.building_index(sc, report)

        picked = _lines(call({"op": "js", "code": _select_js(sc, shift, True)}, 30.0))
        ids = _picked(picked)

        observations = list(sc.get("observations") or [])
        specs = []
        for obs in observations:
            where = refs.get(obs["logic"])
            if where is None:
                raise ScenarioError("observation %r: %r is not a placed building"
                                    % (obs["name"], obs["logic"]))
            specs.append({"x": where[0], "y": where[1], "var": obs["var"]})

        total = int(sc["limits"]["ticks"])
        mods = _modifier_queue(sc, "world")
        fire_world = lambda js: _lines(call({"op": "js", "code": js}, 30.0))  # noqa: E731
        samples: dict[int, list] = {i: [] for i in range(len(observations))}
        polls = 0
        done = 0
        while done < total:
            now = call({"op": "status"}, 30.0)
            done = max(0, int(now.get("tick") or 0) - tick0)
            if now.get("paused"):
                call({"op": "pause", "on": False}, 30.0)
            _modifier_flush(mods, fire_world, done)
            if done >= total:
                break
            _deadline_guard(deadline, done)
            if specs:
                _collect_samples(call({"op": "js", "code": _sample_js(specs)}, 30.0),
                                 samples)
                polls += 1
            # The clock is real time at ~60 tick/s and the round trip costs more
            # than a tick, so a fixed nap overshoots the budget.  Near the end,
            # sleep only as long as the ticks that are left: a scenario that
            # counts loop iterations cannot tell an overshoot from a fidelity
            # gap, and this file is the measurement instrument.
            left = max(0.0, (total - done) / 60.0)
            time.sleep(min(WORLD_POLL_S, max(0.02, left)))
        _deadline_guard(deadline, done)
        # Anything pinned to the final tick (or reached by the last poll) fires
        # here, so `at_tick == limits.ticks` is not silently dropped.
        _modifier_flush(mods, fire_world, done)
        if specs:
            # one last read, so `last` is the final value and not the last poll
            _collect_samples(call({"op": "js", "code": _sample_js(specs)}, 30.0),
                             samples)
            polls += 1
        overshoot = max(0, done - total)

        finals: dict[str, dict] = {}
        for b in sc.get("buildings") or []:
            if not b.get("code"):
                continue
            x, y = refs.get(b["name"], (b["x"], b["y"], b["block"]))[:2]
            table = {}
            for row in call({"op": "logic_vars", "x": x, "y": y}, 30.0).get("vars") or []:
                table[str(row.get("name"))] = _text(row.get("value"))
            finals[b["name"]] = table

        vals = {(name, var): value for name, table in finals.items()
                for var, value in table.items()}
        checks = _scene.check_vars(sc, vals, report) if sc.get("checks") else []

        units, _ = _snapshot(_lines(call({"op": "js", "code": _units_js(ids, True)},
                                         30.0)))
        _, buildings = _snapshot(_lines(call({"op": "js", "code": _builds_js(refs, True)},
                                            30.0)))
        core = _core(_lines(call({"op": "js", "code": _core_js()}, 30.0)))
        events = _events(call({"op": "changes", "since": since, "limit": 500}, 60.0),
                         tick0)

        report["sampling"] = "poll"
        report["sampling_detail"] = {
            "mode": "poll", "poll_s": WORLD_POLL_S, "polls": polls,
            "samples": sum(len(v) for v in samples.values()),
            "note": "the live clock is real time, so this is a poll and not a "
                    "per-tick trace: `last` is exact, `max`/`min` are close, "
                    "`sum` is indicative",
        }
        report["world"] = {"map": env["map"], "world_size": size,
                           "team": _scene_team(sc), "tick0": tick0,
                           "tick1": tick0 + done, "ticks": done,
                           "overshoot": overshoot,
                           "paused_at_start": was_paused, "scene_file": scene_file,
                           "api_port": hs.get("apiPort")}
        payload = {
            "scenario": str(sc.get("id") or sc.get("name") or ""),
            "ticks": done,
            "errors": [],
            "scene": {"placed": report.get("placed"),
                      "configured": report.get("configured"),
                      "stocked": report.get("stocked"),
                      "linked": report.get("linked"),
                      "units": report.get("units"), "errors": []},
            "logs": finals,
            "units": units,
            "buildings": buildings,
            "core": core,
            "events": events,
            "env": {"mindustry": env["mindustry"], "java": env["java"] or None,
                    "map": env["map"], "world_size": size,
                    "team": _scene_team(sc), "update": "live", "sampling": "poll"},
        }
        return {"via": "world", "ticks": done, "samples": samples, "finals": finals,
                "checks": checks, "report": report, "refs": refs,
                "units": units, "buildings": buildings, "core": core,
                "events": events, "payload": payload, "env": payload["env"],
                "modifiers": _public_modifiers(mods)}
    finally:
        if was_paused:
            try:
                client.call({"op": "pause", "on": True}, timeout=20.0, hs=hs)
            except Exception:  # noqa: BLE001 -- the rig may be gone; not our result
                pass


# ---------------------------------------------------------------- scoring

def _observe(sc: dict, sim: dict) -> dict:
    """name -> {"value", "logic", "var", "aggregate", "samples"(diagnostics only)}"""
    out = {}
    for i, obs in enumerate(sc.get("observations") or []):
        values = sim["samples"].get(i) or []
        how = obs.get("aggregate", "last")
        out[obs["name"]] = {
            "logic": obs["logic"],
            "var": obs["var"],
            "aggregate": how,
            "value": aggregate(values, how),
            "samples": values,
        }
    return out


def _pick_actual(a: dict, sim: dict, observations: dict):
    """Which value an assertion compares.

    Precedence: the observation it names (`"observation": "..."`), else the
    last-valued observation of the same (logic, var), else the processor's final
    variable table.  Max/min/sum observations are reports first -- an assertion
    only reads one on purpose.
    """
    named = a.get("observation")
    if named:
        obs = observations.get(str(named))
        return obs["value"] if obs else None
    for obs in observations.values():
        if (obs["logic"] == a["logic"] and obs["var"] == a["var"]
                and obs["aggregate"] == "last"):
            return obs["value"]
    value = (sim["finals"].get(a["logic"]) or {}).get(a["var"])
    number = _as_number(value)
    return _format_number(number) if number is not None else value


def _assertions(sc: dict, sim: dict, observations: dict) -> list[dict]:
    """One evaluated record per v1 check and per v2 assertion."""
    refs = sim["refs"]
    evaluated: list[dict] = []
    for chk in sim["checks"]:
        evaluated.append({
            "kind": "assertion", "source": "check",
            "id": "%s.%s" % (chk["logic"], chk["var"]),
            "desc": "v1 scene check", "logic": chk["logic"], "var": chk["var"],
            "op": chk.get("op") or "eq", "expect": chk["expect"],
            "actual": chk["actual"], "ok": bool(chk["ok"]),
        })
    for a in sc.get("assertions") or []:
        actual = _pick_actual(a, sim, observations)
        evaluated.append({
            "kind": "assertion", "source": "assertion",
            "id": a["id"], "desc": a.get("desc") or "", "logic": a["logic"],
            "var": a["var"], "op": a.get("op", "eq"), "expect": a["value"],
            "actual": actual,
            "ok": compare(actual, a.get("op", "eq"), a["value"], refs),
        })
        if a.get("observation"):
            evaluated[-1]["observation"] = str(a["observation"])
    return evaluated


def _brief(values: list, keep: int = 6) -> dict:
    """A short trace of a per-tick observation: a full list is noise in JSON."""
    if not values:
        return {"count": 0}
    return {"count": len(values), "first": values[:keep],
            "last": values[-keep:] if len(values) > keep else values}


def _diagnostics(evaluated: list[dict], observations: dict) -> list[dict]:
    """One diagnostic per assertion, carrying the observation it read."""
    out = []
    for a in evaluated:
        entry = dict(a)
        for name, obs in observations.items():
            if obs["logic"] == a["logic"] and obs["var"] == a["var"]:
                entry["observation"] = name
                entry["samples"] = _brief(obs["samples"])
                break
        out.append(entry)
    return out


def _report_texts(sc: dict, evaluated: list[dict], ticks: int) -> tuple:
    """(message, next_steps) for the envelope."""
    failed = [a for a in evaluated if not a["ok"]]
    if not evaluated:
        return ("%d tick(s) simulated; the scenario asserts nothing" % ticks, [])
    if not failed:
        return ("all %d assertion(s) passed after %d tick(s)"
                % (len(evaluated), ticks), [])
    lines = ["%s: expected %s %r, got %r"
             % (a["id"], a["op"], a["expect"], a["actual"]) for a in failed[:5]]
    steps = lines + [
        "Fix the mlog (or the expectation -- only one of them is wrong), then "
        "rerun: python tools/scenario.py run %s --level diagnostics --json"
        % (sc.get("path") or "FILE")]
    return ("%d of %d assertion(s) failed after %d tick(s): %s"
            % (len(failed), len(evaluated), ticks, "; ".join(lines[:3])), steps)


def run(sc: dict, *, via: str = "sim", level: str = "summary") -> dict:
    """Run a scenario and answer in the mlog_eval envelope.

    `via="sim"` drives the offline executor (`tools/mlogsim.py`), `via="world"`
    drives the live one (`tools/world_server.py`) through the daemon client.
    Both return the same record shape, so scoring, assertions and the envelope
    are one code path; what differs is only how the rig gets laid down and read.

    A live world that is not there is `unsupported_environment` (exit 3), never a
    result: an experiment that did not run has no outcome to report.
    """
    return _execute(sc, via=via, level=level)[0]


def run_record(sc: dict, *, via: str = "sim", level: str = "diagnostics") -> dict:
    """`run()`, plus the raw record it scored: {"envelope", "record"}.

    The differential runner needs both halves of one execution -- the envelope to
    say whether this host ran at all, the record to turn into an observation.
    Running twice would mean two different experiments.
    """
    envelope, record = _execute(sc, via=via, level=level)
    return {"envelope": envelope, "record": record}


def _env_artifacts(sc: dict, via: str, sid: str) -> dict:
    """Why this host could not run it -- whichever host that was."""
    if via == "world":
        wenv = world_environment()
        notes = ([wenv["why"]] if wenv.get("why") else []) + list(wenv["notes"])
        return {"scenario": sid, "via": "world", "java": wenv.get("java"),
                "jar": wenv.get("jar"), "notes": notes}
    env = environment()
    return {"scenario": sid, "via": "sim", "java": env["java"],
            "jar": env["jar"], "notes": env["notes"]}


def _execute(sc: dict, via: str = "sim", level: str = "summary") -> tuple:
    """(envelope, raw record or None) for one host."""
    if isinstance(sc, str):
        sc = load(sc)
    if level not in ("summary", "diagnostics", "full"):
        raise ValueError("level must be summary|diagnostics|full, got %r" % (level,))
    if via not in ("sim", "world"):
        raise ValueError("via must be sim|world, got %r" % (via,))

    sid = str(sc.get("id") or sc.get("name") or "(unnamed)")
    started = time.time()

    errors = validate(sc)
    if errors:
        return result(
            ok=False, stage="scenario", failure_type="runtime_error",
            message="scenario is invalid: " + "; ".join(errors),
            next_steps=["Fix the scenario file: python tools/scenario.py check "
                        "%s" % (sc.get("path") or "FILE")],
            artifacts={"scenario": sid, "errors": errors}, level=level,
            elapsed_ms=int((time.time() - started) * 1000)), None

    limits = sc.get("limits") or dict(DEFAULT_LIMITS)
    timeout_s = float(limits.get("timeout_s") or DEFAULT_LIMITS["timeout_s"])
    deadline = started + timeout_s

    diagnostics: list[dict] = []
    try:
        record = _world(sc, deadline) if via == "world" else _sim(sc, deadline)
        observations = _observe(sc, record)
        evaluated = _assertions(sc, record, observations)
        message, next_steps = _report_texts(sc, evaluated, record["ticks"])
        failed = [a for a in evaluated if not a["ok"]]
        diagnostics = _diagnostics(evaluated, observations)
        report = record["report"]
        artifacts = {
            "scenario": sid,
            "via": via,
            "ticks": record["ticks"],
            "limits": {"ticks": int(limits.get("ticks") or 0), "timeout_s": timeout_s},
            "observations": {k: v["value"] for k, v in observations.items()},
            "assertions": [{k: a[k] for k in ("id", "ok", "expect", "actual")}
                           for a in evaluated],
            "scene": {"placed": report.get("placed"),
                      "configured": report.get("configured"),
                      "stocked": report.get("stocked"),
                      "linked": report.get("linked"),
                      "units": report.get("units"),
                      "errors": list(report.get("errors") or [])},
            "warnings": warnings(sc),
            # What this run actually disturbed, in order, with the tick it
            # really fired on and the seeded plan it executed.
            "modifiers": list(record.get("modifiers") or []),
            # A disturbance that could not run is a note, never a silent pass.
            "notes": _modifier_notes(record.get("modifiers") or []),
        }
        if via == "world":
            # A live run is a poll, not a per-tick trace: say so in the envelope
            # rather than let `sum` observations look exact.
            artifacts["sampling"] = report.get("sampling")
            artifacts["sampling_detail"] = report.get("sampling_detail")
            artifacts["world"] = report.get("world")
        artifacts["state"] = {"units": len(record.get("units") or []),
                              "buildings": len(record.get("buildings") or [])}
        # The scored view rides with the record: a caller that wants to diff two
        # hosts needs the same numbers the envelope was built from, per assertion.
        record["assertions"] = evaluated
        record["observations"] = {k: v["value"] for k, v in observations.items()}
        return result(
            ok=not failed, stage="scenario",
            failure_type="assertion_failed" if failed else None,
            message=message, diagnostics=diagnostics, artifacts=artifacts,
            next_steps=next_steps if failed else [], level=level,
            # The tick loop really ran, so that host's dimension is evidence;
            # the other three were never evaluated (None, not False).  A live run
            # is real_runtime, an offline one is simulation -- they are not the
            # same claim and must not be merged.
            levels={"real_runtime": True} if via == "world" else {"simulation": True},
            elapsed_ms=int((time.time() - started) * 1000)), record
    except _Environment as exc:
        return result(
            ok=False, stage="scenario", failure_type="unsupported_environment",
            message=str(exc),
            next_steps=_env_steps(via),
            artifacts=_env_artifacts(sc, via, sid),
            level=level, elapsed_ms=int((time.time() - started) * 1000)), None
    except _Timeout as exc:
        return result(
            ok=False, stage="scenario", failure_type="timeout", message=str(exc),
            artifacts={"scenario": sid, "via": via, "timeout_s": timeout_s},
            level=level, elapsed_ms=int((time.time() - started) * 1000)), None
    except ScenarioError as exc:
        return result(
            ok=False, stage="scenario", failure_type="runtime_error",
            message=str(exc),
            diagnostics=[{"kind": "scene", "message": str(exc)}],
            artifacts={"scenario": sid, "via": via}, level=level,
            elapsed_ms=int((time.time() - started) * 1000)), None
    except Exception as exc:  # noqa: BLE001 -- a host crash is a result, not a traceback
        failure = classify(exc)
        if failure not in FAILURE_TYPES:
            failure = "runtime_error"
        return result(
            ok=False, stage="scenario", failure_type=failure,
            message="%s: %s" % (type(exc).__name__, exc),
            diagnostics=[{"kind": "runtime",
                          "message": "%s: %s" % (type(exc).__name__, exc)}],
            artifacts={"scenario": sid, "via": via}, level=level,
            elapsed_ms=int((time.time() - started) * 1000)), None


def _modifier_notes(mods: list[dict]) -> list[str]:
    """One line per disturbance that did not apply, for the envelope's notes."""
    out = []
    for rec in mods:
        if rec.get("executed"):
            continue
        why = "; ".join(rec.get("notes") or []) or rec.get("error") or "not applied"
        out.append("modifier %s at tick %s was not applied: %s"
                   % (rec.get("kind"), rec.get("at_tick"), why))
    return out


def _env_steps(via: str) -> list:
    if via == "world":
        return ["Start the live world: python tools/world_server.py --map Fork "
                "(needs a JVM 17+ and out/_server160.jar)",
                "Check it answers: python tools/world_client.py status",
                "Then rerun: python tools/scenario.py run %s --via world" % "FILE"]
    return ["Run `python tools/mlogsim.py --help` after fixing the JVM/jar; "
            "nothing about the scenario itself is wrong."]


def exit_code(env: dict) -> int:
    """CLI mapping: 0 pass, 3 environment, 1 anything else that failed."""
    if env.get("ok"):
        return 0
    if env.get("failure_type") == "unsupported_environment":
        return 3
    return 1


# ---------------------------------------------------------------- CLI

def _describe(sc: dict) -> str:
    lines = [_scene.summary(sc)]
    lines.append("id       %s" % (sc.get("id") or "-"))
    lines.append("title    %s" % (sc.get("title") or "-"))
    if sc.get("goal"):
        lines.append("goal     %s" % sc["goal"])
    limits = sc.get("limits") or {}
    lines.append("limits   ticks=%s timeout_s=%s"
                 % (limits.get("ticks"), limits.get("timeout_s")))
    for obs in sc.get("observations") or []:
        lines.append("observe  %s = %s.%s (%s)"
                     % (obs["name"], obs["logic"], obs["var"],
                        obs.get("aggregate", "last")))
    for a in sc.get("assertions") or []:
        lines.append("assert   %s  %s.%s %s %r"
                     % (a["id"], a["logic"], a["var"], a.get("op", "eq"), a["value"]))
    for i, m in enumerate(sc.get("modifiers") or []):
        lines.append("modifier [%d] %s at tick %s %s"
                     % (i, m.get("kind"), m.get("at_tick"),
                        json.dumps(m.get("params") or {}, ensure_ascii=False)))
    return "\n".join(lines)


# ---------------------------------------------------------------- generation
#
# Parametric templates, not random maps: every knob is clamped to a range, every
# position is drawn from a candidate list that a constraint already filtered,
# and the same template + params + seed yields byte-identical JSON.  The output
# is a schema-v2 scenario, so `load()`/`run()` accept it with no extra step.

GENERATED_DIR = os.path.join(ROOT, "out", "_scenario", "generated")

TEMPLATE_ORDER = ("unit-control", "resource-drain")


def _gp(kind, default, lo, hi, doc):
    return {"kind": kind, "default": default, "min": lo, "max": hi, "doc": doc}


#: The knobs planning asks the generator to expose: how many target units, how
#: many distractors, where they start, how obstacles are spread, how many
#: processors, and when the disturbance fires.  Widths/height stay inside
#: scene.py's 8..1024 world limit and inside what a 240-tick run can cross.
TEMPLATE_PARAMS: dict = {
    "unit-control": {
        "targets": _gp("int", 2, 1, 8,
                       "units the program steers (one `ubind @flare` loop)"),
        "distractors": _gp("int", 2, 0, 8,
                           "units a mid-run `unit_spawn` adds, of another type "
                           "so they cannot confuse the observations"),
        "obstacles": _gp("int", 2, 0, 8,
                         "router blocks scattered between the start and the "
                         "target, never on the corridor"),
        "processors": _gp("int", 1, 1, 3,
                          "micro-processors placed; the first carries the code"),
        "disturb_at": _gp("int", 120, 10, 900,
                          "tick the disturbance fires (must be < ticks)"),
        "start_x": _gp("int", 10, 6, 24, "tile x the steered units start on"),
        "spread": _gp("float", 2.0, 0.0, 6.0,
                      "radius of the start cluster in tiles (unit positions)"),
        "size": _gp("int", 64, 40, 128, "square world size in tiles"),
        "ticks": _gp("int", 240, 60, 900, "run length in ticks"),
    },
    "resource-drain": {
        "stock": _gp("int", 100, 10, 500, "copper seeded into the core"),
        "drain": _gp("int", 40, 1, 500,
                     "copper the `resource_pressure` modifier removes"),
        "obstacles": _gp("int", 1, 0, 8, "router blocks around the core"),
        "processors": _gp("int", 1, 1, 3, "micro-processors; the first watches "
                                          "the core"),
        "disturb_at": _gp("int", 120, 10, 900, "tick the drain fires"),
        "size": _gp("int", 64, 40, 128, "square world size in tiles"),
        "ticks": _gp("int", 240, 60, 900, "run length in ticks"),
    },
}


def _obstacle_tiles(rng, count: int, size: int, start_x: int, tx: int,
                    cy: int, taken) -> list:
    """`count` tiles off the corridor, drawn without replacement from a filter.

    The filters are the constraint: inside the map margin, between the start and
    the target, at least 3 tiles away from the steer line (so a steered unit is
    never blocked), never on a building already placed.  That is what keeps
    "random obstacles" from producing an unscorable scene.
    """
    if count <= 0:
        return []
    candidates = []
    for x in range(start_x + 3, max(start_x + 4, tx - 2)):
        for y in range(6, size - 6):
            if abs(y - cy) < 3 or (x, y) in taken:
                continue
            candidates.append((x, y))
    if len(candidates) < count:
        raise ScenarioError("obstacles=%d does not fit: only %d tile(s) outside "
                            "the corridor in a %dx%d world"
                            % (count, len(candidates), size, size))
    return rng.sample(candidates, count)


def _template_unit_control(p: dict, rng, seed: int) -> dict:
    size, ticks = int(p["size"]), int(p["ticks"])
    cy = size // 2
    start_x = int(p["start_x"])
    tx = size - 12
    if tx - start_x < 12:
        raise ScenarioError("start_x=%d leaves no room to travel in a %dx%d "
                            "world (need 12 tiles before x=%d)"
                            % (start_x, size, size, tx))
    code = ["ubind @flare",
            "sensor ux @unit @x",
            "sensor uy @unit @y",
            "sensor uhp @unit @health",
            "ucontrol move %d %d 0 0" % (tx, cy),
            "op add n n 1"]
    buildings = [{"name": "ctrl", "block": "micro-processor", "x": 6, "y": cy,
                  "code_inline": code}]
    for i in range(1, int(p["processors"])):
        buildings.append({"name": "idle%d" % i, "block": "micro-processor",
                          "x": 6, "y": cy + 3 * i})
    taken = {(b["x"], b["y"]) for b in buildings}
    for i, (x, y) in enumerate(
            _obstacle_tiles(rng, int(p["obstacles"]), size, start_x, tx, cy, taken)):
        buildings.append({"name": "wall%d" % i, "block": "router", "x": x, "y": y})
    modifiers = []
    if int(p["distractors"]) > 0:
        modifiers.append({
            "kind": "unit_spawn", "at_tick": int(p["disturb_at"]),
            "params": {"type": "dagger", "count": int(p["distractors"]),
                       "x": size - 6, "y": 6, "radius": 1.5,
                       "team": "sharded", "seed": seed},
        })
    lo_ux = start_x + 1
    return {
        "title": "%d flare(s) steered across a field of %d obstacle(s), "
                 "%d distractor(s) at tick %d"
                 % (int(p["targets"]), int(p["obstacles"]),
                    int(p["distractors"]), int(p["disturb_at"])),
        "goal": "A micro-processor binds flares and drives them to (%d,%d) while "
                "a disturbance fires at tick %d. The scenario passes only if the "
                "processor keeps looping, the flares really move right, and they "
                "stay near the corridor." % (tx, cy, int(p["disturb_at"])),
        "notes": "Generated by `tools/scenario.py generate --template "
                 "unit-control` (seed %d). units=%d spread=%.1f start_x=%d "
                 "obstacles=%d processors=%d."
                 % (seed, int(p["targets"]), float(p["spread"]), start_x,
                    int(p["obstacles"]), int(p["processors"])),
        "world": {"size": size},
        "buildings": buildings,
        "units": [{"type": "flare", "count": int(p["targets"]),
                   "team": "sharded", "at": [start_x, cy],
                   "radius": float(p["spread"])}],
        "limits": {"ticks": ticks, "timeout_s": max(60.0, ticks / 2.0)},
        "modifiers": modifiers,
        "observations": [
            {"name": "ux", "logic": "ctrl", "var": "ux", "aggregate": "last"},
            {"name": "ux_max", "logic": "ctrl", "var": "ux", "aggregate": "max"},
            {"name": "uy", "logic": "ctrl", "var": "uy", "aggregate": "last"},
            {"name": "hp", "logic": "ctrl", "var": "uhp", "aggregate": "last"},
            {"name": "cycles", "logic": "ctrl", "var": "n", "aggregate": "last"},
        ],
        "assertions": [
            {"id": "A1", "desc": "the processor kept looping",
             "logic": "ctrl", "var": "n", "op": "ge",
             "value": max(5, ticks // 24)},
            {"id": "A2", "desc": "the steered unit moved right of its start",
             "logic": "ctrl", "var": "ux", "op": "ge", "value": lo_ux},
            {"id": "A3", "desc": "it travelled at least 6 tiles",
             "logic": "ctrl", "var": "ux", "observation": "ux_max", "op": "ge",
             "value": min(tx - 1, start_x + 6)},
            {"id": "A4", "desc": "it stayed on the side of the corridor it "
                                 "started on",
             "logic": "ctrl", "var": "uy", "op": "ge", "value": cy - 10},
            {"id": "A5", "desc": "... but not below the corridor either",
             "logic": "ctrl", "var": "uy", "op": "le", "value": cy + 10},
            {"id": "A6", "desc": "the flare survived the disturbance",
             "logic": "ctrl", "var": "uhp", "op": "gt", "value": 0},
        ],
        "success_criteria": {"all_assertions": True},
    }


def _template_resource_drain(p: dict, rng, seed: int) -> dict:
    size, ticks = int(p["size"]), int(p["ticks"])
    cy = size // 2
    stock, drain = int(p["stock"]), int(p["drain"])
    if drain > stock:
        raise ScenarioError("drain=%d is more than stock=%d: the core cannot "
                            "lose what it never had" % (drain, stock))
    buildings = [
        {"name": "hub", "block": "core-shard", "x": size - 12, "y": cy - 1,
         "items": {"copper": stock}},
        {"name": "watch", "block": "micro-processor", "x": size - 20, "y": cy - 1,
         "links": ["hub"],
         "code_inline": ["sensor c hub @copper", "op add n n 1"]},
    ]
    for i in range(1, int(p["processors"])):
        buildings.append({"name": "idle%d" % i, "block": "micro-processor",
                          "x": size - 20, "y": cy + 3 * i})
    taken = {(b["x"], b["y"]) for b in buildings}
    for i, (x, y) in enumerate(
            _obstacle_tiles(rng, int(p["obstacles"]), size, size - 28, size - 20,
                            cy, taken)):
        buildings.append({"name": "wall%d" % i, "block": "router", "x": x, "y": y})
    return {
        "title": "core stocked with %d copper, %d drained at tick %d"
                 % (stock, drain, int(p["disturb_at"])),
        "goal": "A processor watches a core's copper. At tick %d a "
                "resource_pressure modifier drains %d copper; the scenario passes "
                "only if the buffer really fell by exactly that much and the "
                "processor kept sampling." % (int(p["disturb_at"]), drain),
        "notes": "Generated by `tools/scenario.py generate --template "
                 "resource-drain` (seed %d). stock=%d drain=%d processors=%d."
                 % (seed, stock, drain, int(p["processors"])),
        "world": {"size": size},
        "buildings": buildings,
        "limits": {"ticks": ticks, "timeout_s": max(60.0, ticks / 2.0)},
        "modifiers": [{"kind": "resource_pressure",
                       "at_tick": int(p["disturb_at"]),
                       "params": {"op": "drain", "item": "copper",
                                  "amount": drain}}],
        "observations": [
            {"name": "copper", "logic": "watch", "var": "c", "aggregate": "last"},
            {"name": "copper_min", "logic": "watch", "var": "c", "aggregate": "min"},
            {"name": "cycles", "logic": "watch", "var": "n", "aggregate": "last"},
        ],
        "assertions": [
            {"id": "A1", "desc": "the processor kept sampling",
             "logic": "watch", "var": "n", "op": "ge", "value": max(5, ticks // 24)},
            {"id": "A2", "desc": "the buffer fell to stock-drain",
             "logic": "watch", "var": "c", "op": "le", "value": stock - drain},
            {"id": "A3", "desc": "and it fell by the amount asked for, no more",
             "logic": "watch", "var": "c", "op": "ge", "value": stock - drain},
            {"id": "A4", "desc": "the dip really happened mid-run",
             "logic": "watch", "var": "c", "observation": "copper_min", "op": "le",
             "value": stock - drain},
        ],
        "success_criteria": {"all_assertions": True},
    }


TEMPLATES = {
    "unit-control": _template_unit_control,
    "resource-drain": _template_resource_drain,
}


def _gen_params(template: str, raw: dict, seed) -> dict:
    """Clamp/validate the knobs.  Unknown knobs are refused, not ignored."""
    if not isinstance(raw, dict):
        raise ScenarioError("generate params must be an object, got %r" % (raw,))
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ScenarioError("seed must be a non-negative integer, got %r" % (seed,))
    spec = TEMPLATE_PARAMS[template]
    unknown = sorted(set(raw) - set(spec))
    if unknown:
        raise ScenarioError("template %r has no param(s) %s (known: %s)"
                            % (template, ", ".join(unknown), ", ".join(spec)))
    out = {}
    for name, ps in spec.items():
        value = raw.get(name, ps["default"])
        if ps["kind"] == "int":
            if isinstance(value, bool) or not isinstance(value, int):
                raise ScenarioError("%s must be an integer, got %r" % (name, value))
        else:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ScenarioError("%s must be a number, got %r" % (name, value))
            value = float(value)
        if value < ps["min"] or value > ps["max"]:
            raise ScenarioError("%s=%r is outside %s..%s"
                                % (name, value, ps["min"], ps["max"]))
        out[name] = value
    out["seed"] = seed
    # Cross-knob constraint: a disturbance after the end of the run would be
    # dead weight (and `load()` would refuse it as at_tick past limits.ticks).
    if "disturb_at" in out and out["disturb_at"] >= out["ticks"]:
        raise ScenarioError("disturb_at=%d must be < ticks=%d (a disturbance "
                            "after the run never fires)"
                            % (out["disturb_at"], out["ticks"]))
    return out


def generate(spec: dict) -> dict:
    """Template + params + seed -> a schema-v2 scenario dict (no executor).

    Pure and deterministic: same ``spec`` => same dict, so a generated file can
    be diffed, regenerated and reviewed like a hand-written one.
    """
    if not isinstance(spec, dict):
        raise ScenarioError("generate() takes {template, params, seed}")
    template = spec.get("template") or "unit-control"
    if template not in TEMPLATES:
        raise ScenarioError("unknown template %r (known: %s)"
                            % (template, ", ".join(TEMPLATE_ORDER)))
    params = _gen_params(template, spec.get("params") or {}, spec.get("seed", 0))
    seed = params.pop("seed")
    sc = TEMPLATES[template](params, random.Random(seed), seed)
    # scene.validate() reads sc["units"] directly, so a template with no units
    # (resource-drain) must still emit the empty list rather than omit the key.
    sc.setdefault("units", [])
    sc["id"] = str(spec.get("id") or "%s-seed%d" % (template, seed))
    sc["version"] = 2
    return sc


def _write_scenario(sc: dict, path: str) -> str:
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(sc, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    return path


def _cmd_generate(args) -> int:
    if args.list_templates:
        rows = [(name, TEMPLATE_PARAMS[name]) for name in TEMPLATE_ORDER]
        if args.json:
            print(json.dumps({name: {k: {"default": v["default"],
                                         "min": v["min"], "max": v["max"],
                                         "doc": v["doc"]}
                                     for k, v in ps.items()}
                              for name, ps in rows}, ensure_ascii=False, indent=2))
            return 0
        for name, ps in rows:
            print("%s" % name)
            for key, v in ps.items():
                print("  %-12s %-6s default=%-6r range=%s..%s  %s"
                      % (key, v["kind"], v["default"], v["min"], v["max"], v["doc"]))
        return 0
    try:
        params = json.loads(args.params or "{}")
    except json.JSONDecodeError as exc:
        print("--params is not JSON: %s" % exc, file=sys.stderr)
        return 2
    try:
        sc = generate({"template": args.template, "params": params,
                       "seed": args.seed, "id": args.id})
    except ScenarioError as exc:
        print("cannot generate: %s" % exc, file=sys.stderr)
        return 2
    out = args.out or os.path.join(GENERATED_DIR, "%s.json" % sc["id"])
    _write_scenario(sc, out)
    try:
        loaded = load(out)  # the generated file must pass the same gate
    except ScenarioError as exc:
        print("generated %s but it is invalid: %s" % (out, exc), file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps({"ok": True, "path": loaded["path"], "id": loaded["id"],
                          "template": args.template, "seed": args.seed,
                          "buildings": len(loaded["buildings"]),
                          "units": sum(u["count"] for u in loaded["units"]),
                          "modifiers": loaded.get("modifiers") or [],
                          "assertions": len(loaded.get("assertions") or [])},
                         ensure_ascii=False, indent=2))
        return 0
    if args.dump:
        print(json.dumps(sc, ensure_ascii=False, indent=2))
        return 0
    print("generated %s" % loaded["path"])
    print(_describe(loaded))
    print("ok       scenario valid")
    return 0


def _cmd_check(args) -> int:
    try:
        sc = load(args.path, via=getattr(args, "via", None))
    except ScenarioError as exc:
        if args.json:
            print(json.dumps({"ok": False, "path": args.path,
                              "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        else:
            print("scenario invalid: %s" % exc, file=sys.stderr)
        return 1
    if args.json:
        payload = {
            "ok": True, "path": sc["path"], "version": sc["version"],
            "id": sc.get("id"), "title": sc.get("title"),
            "limits": sc.get("limits"),
            "buildings": len(sc["buildings"]),
            "units": sum(u["count"] for u in sc["units"]),
            "checks": len(sc["checks"]),
            "observations": len(sc.get("observations") or []),
            "assertions": len(sc.get("assertions") or []),
            "errors": [], "warnings": warnings(sc),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(_describe(sc))
        for w in warnings(sc):
            print("warn     " + w)
        print("ok       scenario valid")
    return 0


def _cmd_run(args) -> int:
    try:
        sc = load(args.path)
    except ScenarioError as exc:
        env = result(ok=False, stage="scenario", failure_type="runtime_error",
                     message="scenario is invalid: %s" % exc,
                     next_steps=["Fix the file: python tools/scenario.py check %s"
                                 % args.path], level=args.level)
        if args.json:
            print(json.dumps(env, ensure_ascii=False, indent=2))
        else:
            print("FAIL scenario: %s" % exc, file=sys.stderr)
        return 1
    env = run(sc, via=args.via, level=args.level)
    if args.json:
        print(json.dumps(env, ensure_ascii=False, indent=2))
    else:
        print("%s  %s" % ("PASS" if env["ok"] else "FAIL", sc.get("id") or sc["name"]))
        print("  " + (env.get("message") or ""))
        for d in env.get("diagnostics") or []:
            if d.get("kind") != "assertion":
                continue
            print("  %s %-14s %s.%s %s %r  (got %r)"
                  % ("ok  " if d["ok"] else "FAIL", d["id"], d["logic"], d["var"],
                     d["op"], d["expect"], d["actual"]))
        for rec in (env.get("artifacts") or {}).get("modifiers") or []:
            state = ("applied at tick %s" % rec.get("applied_at_tick")
                     if rec.get("executed") else "NOT APPLIED")
            print("  mod %-20s at_tick=%-4s %s%s"
                  % (rec.get("kind"), rec.get("at_tick"), state,
                     ("  (%s)" % rec["error"]) if rec.get("error") else ""))
        for note in (env.get("artifacts") or {}).get("notes") or []:
            print("  note " + note)
        for step in env.get("next_steps") or []:
            print("  -> " + step)
        print("  %d ms" % (env.get("elapsed_ms") or 0))
    return exit_code(env)


def _cmd_list(args) -> int:
    entries = []
    if os.path.isdir(SCENARIO_DIR):
        for name in sorted(os.listdir(SCENARIO_DIR)):
            if not name.lower().endswith(".json"):
                continue
            path = os.path.join(SCENARIO_DIR, name)
            entry = {"path": path, "id": None, "title": None, "ok": False,
                     "errors": []}
            try:
                sc = load(path)
                entry.update({"id": sc.get("id"), "title": sc.get("title") or sc["name"],
                              "version": sc["version"], "ok": True})
            except ScenarioError as exc:
                entry["errors"] = [str(exc)]
            entries.append(entry)
    if args.json:
        print(json.dumps({"dir": SCENARIO_DIR, "count": len(entries),
                          "scenarios": entries}, ensure_ascii=False, indent=2))
        return 0
    if not entries:
        print("no scenarios in %s" % SCENARIO_DIR)
        return 0
    for e in entries:
        if e["ok"]:
            print("%-24s %s" % (e["id"], e["title"]))
        else:
            print("%-24s INVALID: %s" % (os.path.basename(e["path"]),
                                         "; ".join(e["errors"])))
    print("--")
    print("%d scenario(s) in %s" % (len(entries), SCENARIO_DIR))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="run a scenario (scene schema v2) on the offline executor")
    sub = ap.add_subparsers(dest="cmd")

    c = sub.add_parser("check", help="validate a scenario without running it")
    c.add_argument("path")
    c.add_argument("--json", action="store_true")
    c.add_argument("--via", default=None, choices=["sim", "world"],
                   help="also refuse modifiers that cannot run under this host")

    r = sub.add_parser("run", help="run a scenario and report the envelope")
    r.add_argument("path")
    r.add_argument("--json", action="store_true")
    r.add_argument("--via", default="sim", choices=["sim", "world"])
    r.add_argument("--level", default="summary",
                   choices=["summary", "diagnostics", "full"])

    ls = sub.add_parser("list", help="list scenarios in scenes/scenarios/")
    ls.add_argument("--json", action="store_true")

    g = sub.add_parser("generate", help="build a scenario from a template + params")
    g.add_argument("--template", default="unit-control",
                   choices=list(TEMPLATE_ORDER))
    g.add_argument("--params", default="{}",
                   help='JSON object of template knobs, e.g. \'{"targets": 4}\'')
    g.add_argument("--seed", type=int, default=0,
                   help="seed for the constrained choices (same seed, same file)")
    g.add_argument("--id", default=None, help="scenario id (default: template+seed)")
    g.add_argument("--out", default=None,
                   help="write here (default: out/_scenario/generated/<id>.json)")
    g.add_argument("--list", action="store_true", dest="list_templates",
                   help="print the templates and their knobs")
    g.add_argument("--dump", action="store_true", help="print the JSON, write nothing")
    g.add_argument("--json", action="store_true")

    args = ap.parse_args(argv)
    if not args.cmd:
        ap.print_help()
        return 2
    return {"check": _cmd_check, "run": _cmd_run, "list": _cmd_list,
            "generate": _cmd_generate}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
