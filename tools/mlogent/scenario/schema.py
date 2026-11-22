"""Scenario v1/v2 loading, normalization and validation without an executor."""
from __future__ import annotations

import json
import os

import scene as _scene
import modifier as _modifier
import world_probe as _world_probe


#: Keys schema v2 adds on top of scene v1.
V2_KEYS = ("id", "title", "goal", "limits", "observations", "assertions",
           "success_criteria", "modifiers", "world_probe")
ALLOWED_KEYS = set(_scene.TOP_KEYS) | set(V2_KEYS)
AGGREGATES = ("last", "max", "min", "sum")
OPS = ("eq", "ne", "gt", "ge", "lt", "le", "contains")

DEFAULT_LIMITS = {"ticks": 120, "timeout_s": 60.0}


class ScenarioError(ValueError):
    """A scenario is unreadable or fails validation."""


def _scene_team(sc: dict) -> str:
    """The team the scenario speaks for: the first unit's, else a building's."""
    for u in sc.get("units") or []:
        if u.get("team"):
            return str(u["team"])
    for b in sc.get("buildings") or []:
        if b.get("team"):
            return str(b["team"])
    return "sharded"


def _read_json(path: str):
    with open(path, encoding="utf-8-sig") as fh:
        return json.load(fh)


def _shadow_path(full: str, shadow_dir: str) -> str:
    os.makedirs(shadow_dir, exist_ok=True)
    return os.path.join(shadow_dir, os.path.basename(full))


def _strip_to_v1(raw: dict, full: str, workspace_root: str) -> dict:
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
        for cand in (os.path.join(base, str(code)), os.path.join(workspace_root, str(code))):
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


def load(path: str, *, workspace_root: str, shadow_dir: str, via: str | None = None) -> dict:
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
        shadow = _shadow_path(full, shadow_dir)
        with open(shadow, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(_strip_to_v1(raw, full, workspace_root), fh, ensure_ascii=False, indent=2)
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
    if "world_probe" in raw:
        sc["world_probe"] = raw["world_probe"]
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

    probe_checks = []
    if "world_probe" in sc:
        try:
            probe_checks = _world_probe.validate(sc["world_probe"]).get("checks", [])
        except ValueError as exc:
            errs.append(str(exc))
    if v2 and not (assertions or probe_checks):
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
