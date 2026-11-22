"""Pure scenario observation, assertion and diagnostic evaluation.

Consumes an execution record; never starts a backend, reads a scene file or
imports the scenario CLI. Comparison and result schemas stay shared by hosts.
"""
from __future__ import annotations


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


def observe(sc: dict, sim: dict) -> dict:
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


def pick_actual(a: dict, sim: dict, observations: dict):
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


def evaluate_assertions(sc: dict, sim: dict, observations: dict) -> list[dict]:
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
        actual = pick_actual(a, sim, observations)
        evaluated.append({
            "kind": "assertion", "source": "assertion",
            "id": a["id"], "desc": a.get("desc") or "", "logic": a["logic"],
            "var": a["var"], "op": a.get("op", "eq"), "expect": a["value"],
            "actual": actual,
            "ok": compare(actual, a.get("op", "eq"), a["value"], refs),
        })
        if a.get("observation"):
            evaluated[-1]["observation"] = str(a["observation"])
    for i, check in enumerate(sim.get("world_probe", {}).get("checks", []), 1):
        selection = {k: v for k, v in check.items() if k not in {"equals", "actual", "ok"}}
        evaluated.append({
            "kind": "assertion", "source": "world_probe", "id": "world_probe[%d]" % i,
            "desc": "", "logic": None, "var": None, "op": "eq", "selection": selection,
            "expect": check["equals"], "actual": check["actual"], "ok": check["ok"],
        })
    return evaluated


def brief(values: list, keep: int = 6) -> dict:
    """A short trace of a per-tick observation: a full list is noise in JSON."""
    if not values:
        return {"count": 0}
    return {"count": len(values), "first": values[:keep],
            "last": values[-keep:] if len(values) > keep else values}


def diagnostics(evaluated: list[dict], observations: dict) -> list[dict]:
    """One diagnostic per assertion, carrying the observation it read."""
    out = []
    for a in evaluated:
        entry = dict(a)
        named = a.get("observation")
        if named in observations:
            entry["samples"] = brief(observations[named]["samples"])
            out.append(entry)
            continue
        for name, obs in observations.items():
            if obs["logic"] == a["logic"] and obs["var"] == a["var"]:
                entry["observation"] = name
                entry["samples"] = brief(obs["samples"])
                break
        out.append(entry)
    return out


def report_texts(sc: dict, evaluated: list[dict], ticks: int) -> tuple:
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
