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
`--via world` answers `unsupported_environment` for now: the live world path is
a separate host and is not wired to scenarios yet -- say so once, cleanly,
instead of half-running an experiment.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import scene as _scene  # noqa: E402
from mlog_eval import FAILURE_TYPES, classify, result  # noqa: E402

SCENARIO_DIR = os.path.join(ROOT, "scenes", "scenarios")
#: v2 files are projected onto a v1 shadow here, then handed to scene.load().
SHADOW_DIR = os.path.join(ROOT, "out", "_scenario", "v1")

#: Keys schema v2 adds on top of scene v1.
V2_KEYS = ("id", "title", "goal", "limits", "observations", "assertions",
           "success_criteria")
ALLOWED_KEYS = set(_scene.TOP_KEYS) | set(V2_KEYS)
AGGREGATES = ("last", "max", "min", "sum")
OPS = ("eq", "ne", "gt", "ge", "lt", "le", "contains")

DEFAULT_LIMITS = {"ticks": 120, "timeout_s": 60.0}
#: Ticks per `js` command: small enough that `limits.timeout_s` can interrupt a
#: runaway program, large enough that the per-command overhead stays noise.
TICK_CHUNK = 30
#: Mindustry v146+ needs a modern JVM; the box's PATH java is 8 and fails at boot.
MIN_JAVA_MAJOR = 17

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


def load(path: str) -> dict:
    """Read + validate + normalize a scenario file; the result carries "path".

    Raises ScenarioError when the file is not a scenario at all (unreadable JSON,
    unknown keys, scene-level errors).  Field-level v2 problems are collected by
    validate() and raised here as one message, so a caller never gets a
    half-normalized dict it would have to re-check.
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

    errors = validate(sc)
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


def _positive_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def _positive_num(value) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and value > 0)


def validate(sc: dict) -> list[str]:
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
    return errs


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


def _sim(sc: dict, deadline: float) -> dict:
    """Lay the scene down, tick it, sample observations; returns the raw record."""
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
        done = 0
        while done < total:
            _deadline_guard(deadline, done)
            step = min(TICK_CHUNK, total - done)
            _js(srv, _step_js(step, bool(observations)))
            done += step
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

        return {"ticks": done, "samples": samples, "finals": finals,
                "checks": checks, "report": report, "refs": refs}
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

    `via="world"` is a deliberate `unsupported_environment`: the live world is a
    different host (`tools/world_server.py`) and is not wired to scenarios yet,
    so an experiment is refused once instead of half-executed.
    """
    if isinstance(sc, str):
        sc = load(sc)
    if level not in ("summary", "diagnostics", "full"):
        raise ValueError("level must be summary|diagnostics|full, got %r" % (level,))
    if via not in ("sim", "world"):
        raise ValueError("via must be sim|world, got %r" % (via,))

    sid = str(sc.get("id") or sc.get("name") or "(unnamed)")
    started = time.time()

    if via == "world":
        return result(
            ok=False, stage="scenario", failure_type="unsupported_environment",
            message="--via world is not implemented: scenarios run on the "
                    "offline executor (via=sim) only",
            next_steps=["Rerun without --via world.",
                        "Use `python tools/world_mcp.py` if the rig has to be "
                        "seen live in the game."],
            artifacts={"scenario": sid, "via": "world"}, level=level,
            elapsed_ms=int((time.time() - started) * 1000))

    errors = validate(sc)
    if errors:
        return result(
            ok=False, stage="scenario", failure_type="runtime_error",
            message="scenario is invalid: " + "; ".join(errors),
            next_steps=["Fix the scenario file: python tools/scenario.py check "
                        "%s" % (sc.get("path") or "FILE")],
            artifacts={"scenario": sid, "errors": errors}, level=level,
            elapsed_ms=int((time.time() - started) * 1000))

    limits = sc.get("limits") or dict(DEFAULT_LIMITS)
    timeout_s = float(limits.get("timeout_s") or DEFAULT_LIMITS["timeout_s"])
    deadline = started + timeout_s

    diagnostics: list[dict] = []
    try:
        sim = _sim(sc, deadline)
        observations = _observe(sc, sim)
        evaluated = _assertions(sc, sim, observations)
        message, next_steps = _report_texts(sc, evaluated, sim["ticks"])
        failed = [a for a in evaluated if not a["ok"]]
        diagnostics = _diagnostics(evaluated, observations)
        report = sim["report"]
        artifacts = {
            "scenario": sid,
            "via": "sim",
            "ticks": sim["ticks"],
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
        }
        return result(
            ok=not failed, stage="scenario",
            failure_type="assertion_failed" if failed else None,
            message=message, diagnostics=diagnostics, artifacts=artifacts,
            next_steps=next_steps if failed else [], level=level,
            # The tick loop really ran, so the simulation dimension is evidence;
            # execution/static/real_runtime were never evaluated (None, not False).
            levels={"simulation": True},
            elapsed_ms=int((time.time() - started) * 1000))
    except _Environment as exc:
        return result(
            ok=False, stage="scenario", failure_type="unsupported_environment",
            message=str(exc),
            next_steps=["Run `python tools/mlogsim.py --help` after fixing the "
                        "JVM/jar; nothing about the scenario itself is wrong."],
            artifacts={"scenario": sid, "java": environment()["java"],
                       "jar": environment()["jar"], "notes": environment()["notes"]},
            level=level, elapsed_ms=int((time.time() - started) * 1000))
    except _Timeout as exc:
        return result(
            ok=False, stage="scenario", failure_type="timeout", message=str(exc),
            artifacts={"scenario": sid, "timeout_s": timeout_s},
            level=level, elapsed_ms=int((time.time() - started) * 1000))
    except ScenarioError as exc:
        return result(
            ok=False, stage="scenario", failure_type="runtime_error",
            message=str(exc),
            diagnostics=[{"kind": "scene", "message": str(exc)}],
            artifacts={"scenario": sid}, level=level,
            elapsed_ms=int((time.time() - started) * 1000))
    except Exception as exc:  # noqa: BLE001 -- a host crash is a result, not a traceback
        failure = classify(exc)
        if failure not in FAILURE_TYPES:
            failure = "runtime_error"
        return result(
            ok=False, stage="scenario", failure_type=failure,
            message="%s: %s" % (type(exc).__name__, exc),
            diagnostics=[{"kind": "runtime",
                          "message": "%s: %s" % (type(exc).__name__, exc)}],
            artifacts={"scenario": sid}, level=level,
            elapsed_ms=int((time.time() - started) * 1000))


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
    return "\n".join(lines)


def _cmd_check(args) -> int:
    try:
        sc = load(args.path)
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

    r = sub.add_parser("run", help="run a scenario and report the envelope")
    r.add_argument("path")
    r.add_argument("--json", action="store_true")
    r.add_argument("--via", default="sim", choices=["sim", "world"])
    r.add_argument("--level", default="summary",
                   choices=["summary", "diagnostics", "full"])

    ls = sub.add_parser("list", help="list scenarios in scenes/scenarios/")
    ls.add_argument("--json", action="store_true")

    args = ap.parse_args(argv)
    if not args.cmd:
        ap.print_help()
        return 2
    return {"check": _cmd_check, "run": _cmd_run, "list": _cmd_list}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
