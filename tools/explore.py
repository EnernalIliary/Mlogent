"""Automatic exploration and failure shrinking (plan section 2 P3).

Two jobs, and they are separable on purpose:

``explore``  -- given a template and a parameter space (seeds, counts), build a
                scenario per point, run each one, and keep the ones that fail.
                The space is enumerated, not sampled blindly: same spec => same
                list, so a "found it at seed 7" claim can be replayed.

``shrink``   -- given a failing scenario, find the *smallest* variation that
                still fails, by delta-debugging its edits (the modifier list).
                A minimal repro is what turns "the sandbox broke somewhere" into
                "the sandbox breaks when the flare is teleported at tick 30".

The shrinking core (``ddmin``) is a pure predicate-driven function.  That is
deliberate: the interesting bugs in shrinking are in the algorithm, and an
algorithm can be tested with a fake oracle without a JVM, so CI covers it.

Nothing here talks to the live world: exploration multiplies the number of runs,
and a live world serialises them behind one server.  Use ``scenario.run(via=
"world")`` directly for the one case you decided to care about.
"""
from __future__ import annotations

import json
import os
import sys
import time

import scenario

SCHEMA = "mlog-explore/v1"


def default_dir() -> str:
    return os.environ.get("MLOG_EXPLORE_DIR") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out", "explore")


# --- the space -------------------------------------------------------------

def space(template: str = "unit-control", *, seeds=(1,), params: dict | None = None,
          modifiers: list | None = None) -> list:
    """Enumerate the points to try, deterministically and in a stable order.

    A point is a plain dict, so it can be printed, diffed and written to a
    ledger.  ``modifiers`` here is a *list of lists*: one candidate bundle per
    point, which is exactly what ``shrink()`` reduces later.
    """
    out = []
    for seed in seeds:
        # a bundle is a flat list of modifier entries, copied per point: the
        # shrinker rewrites a point's bundle, and two points must not share one
        out.append({"template": template, "seed": int(seed),
                    "params": dict(params or {}),
                    "modifiers": [dict(m) for m in (modifiers or [])]})
    return out


def variant(point: dict) -> dict:
    """One point of the space -> a runnable scenario dict.

    ``generate()`` returns the file *shape*; a runnable dict is what
    ``scenario.load()`` yields (it normalizes the world, fills rule defaults and
    validates).  Rather than re-implement that normalization here -- two
    normalizers drift -- the generated shape goes through the real loader, via a
    file in the ledger's tmp dir.
    """
    raw = scenario.generate({"template": point.get("template") or "unit-control",
                             "params": dict(point.get("params") or {}),
                             "seed": int(point.get("seed") or 0)})
    mods = list(point.get("modifiers") or [])
    if mods:
        raw["modifiers"] = mods
    raw["id"] = "%s-seed%d" % (point.get("template") or "unit-control",
                               int(point.get("seed") or 0))
    tmp = os.path.join(default_dir(), "tmp")
    os.makedirs(tmp, exist_ok=True)
    path = os.path.join(tmp, "%s.json" % raw["id"])
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(raw, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    return scenario.load(path)


# --- one run ---------------------------------------------------------------

def evaluate(sc: dict, *, via: str = "sim") -> dict:
    """Run one scenario; ``ok`` means "ran AND every check passed".

    Two different failures must not collapse into one boolean: a host that could
    not run (no jar) is not evidence about the scenario, so it is reported as
    ``skipped`` rather than as a failure of the thing being explored.
    """
    started = time.time()
    env = scenario.run(sc, via=via, level="summary")
    got = {"id": sc.get("id"), "via": via, "ok": False, "skipped": False,
           "failure_type": env.get("failure_type"), "stage": env.get("stage"),
           "seconds": round(time.time() - started, 2)}
    if not env.get("ok"):
        got["skipped"] = env.get("failure_type") == "unsupported_environment"
        return got
    checks = env.get("checks") or []
    got["checks"] = len(checks)
    got["failed_checks"] = [c.get("name") for c in checks if not c.get("ok")]
    got["ok"] = not got["failed_checks"]
    if not got["ok"]:
        got["failure_type"] = "assertion_failed"
    return got


def explore(points: list, *, via: str = "sim", evaluator=None, limit: int = 0) -> dict:
    """Run every point, keep the failures, stop early once ``limit`` is hit."""
    ev = evaluator or (lambda sc: evaluate(sc, via=via))
    rows, failures = [], []
    for point in points:
        row = ev(variant(point))
        # the point is recorded with the result so a failure is reproducible from
        # the ledger alone, without re-deriving which seed produced it
        row["point"] = point
        rows.append(row)
        if not row.get("ok") and not row.get("skipped"):
            failures.append(row)
            if limit and len(failures) >= limit:
                break
    skipped = [r for r in rows if r.get("skipped")]
    return {"schema": SCHEMA, "points": len(points), "ran": len(rows),
            "failures": failures, "skipped": len(skipped),
            "summary": {"points": len(points), "ran": len(rows),
                        "failed": len(failures), "skipped": len(skipped),
                        "ok": not failures and not skipped},
            "runs": rows}


# --- shrinking -------------------------------------------------------------

def _split(items: list, n: int) -> list:
    size = max(1, (len(items) + n - 1) // n)
    return [items[i:i + size] for i in range(0, len(items), size)]


def ddmin(items: list, fails) -> list:
    """Zeller's delta debugging: the smallest sub-list that still ``fails``.

    ``fails(sub)`` must be a predicate over a list.  Returns a sub-list in the
    original order; if nothing fails (not even the input) it returns ``[]``,
    which is the honest answer -- there is no minimal repro of a non-failure.
    """
    items = list(items)
    if not fails(items):
        return []
    n = 2
    while len(items) >= 2:
        chunks = _split(items, n)
        reduced = False
        for chunk in chunks:
            if chunk and fails(chunk):
                items, n, reduced = chunk, 2, True
                break
        if not reduced:
            for chunk in chunks:
                if len(chunk) == len(items):
                    continue
                rest = [x for x in items if x not in chunk]
                if rest and fails(rest):
                    items, n, reduced = rest, max(n - 1, 2), True
                    break
        if not reduced:
            if n >= len(items):
                break
            n = min(len(items), n * 2)
    return items


def shrink(point: dict, *, via: str = "sim", evaluator=None,
           max_rounds: int = 8) -> dict:
    """Shrink one failing point's modifier bundle, keeping the seed fixed.

    Seed is *not* shrunk: it is the point's identity ("seed 7 breaks"), and
    changing it while shrinking would make the repro unreproducible.  Each round
    re-verifies the reduced bundle from scratch, because a modifier can be
    individually harmless and jointly fatal (order matters).
    """
    ev = evaluator or (lambda sc: evaluate(sc, via=via))
    mods = list(point.get("modifiers") or [])
    base = ev(variant(point))
    if base.get("ok") or base.get("skipped"):
        return {"schema": SCHEMA, "shrank": False, "why": "point does not fail",
                "point": point, "result": base, "modifiers": mods}
    rounds = 0

    def fails(sub):
        cand = dict(point)
        cand["modifiers"] = list(sub)
        return not ev(variant(cand)).get("ok")

    while rounds < max_rounds:
        rounds += 1
        smaller = ddmin(mods, fails)
        if smaller == mods:
            break
        mods = smaller
    final = dict(point)
    final["modifiers"] = mods
    result = ev(variant(final))
    return {"schema": SCHEMA, "shrank": len(mods) < len(point.get("modifiers") or []),
            "rounds": rounds, "point": final, "result": result,
            "modifiers": mods, "kept": len(mods),
            "dropped": len(point.get("modifiers") or []) - len(mods)}


# --- ledger ----------------------------------------------------------------

def save(report: dict, *, directory: str | None = None, name: str | None = None) -> str:
    d = directory or default_dir()
    os.makedirs(d, exist_ok=True)
    stamp = name or time.strftime("%Y%m%d-%H%M%S")
    path = os.path.join(d, "%s.json" % stamp)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    os.replace(tmp, path)
    return path


def load_runs(directory: str | None = None) -> list:
    d = directory or default_dir()
    if not os.path.isdir(d):
        return []
    out = []
    for name in sorted(os.listdir(d)):
        if not name.endswith(".json"):
            continue
        try:
            with open(os.path.join(d, name), encoding="utf-8") as fh:
                rec = json.load(fh)
        except (OSError, ValueError):
            continue
        rec.setdefault("file", name)
        out.append(rec)
    return out


# --- CLI -------------------------------------------------------------------

def _selftest() -> int:
    fails = 0

    def check(cond, what):
        nonlocal fails
        if not cond:
            fails += 1
            print("FAIL %s" % what)

    check(ddmin([], lambda xs: True) == [], "empty input has no repro")
    check(ddmin([1, 2, 3], lambda xs: False) == [], "no failure -> no repro")
    # truffle: the failure needs exactly {a, c}, everything else is noise
    need = {"a", "c"}
    items = ["x1", "a", "y2", "c", "z3", "w4", "a"]
    got = ddmin(items, lambda xs: need <= set(xs))
    check(set(got) == need, "ddmin finds the minimal set (%r)" % (got,))
    check(got == ["a", "c"], "ddmin keeps original order (%r)" % (got,))
    # a failure triggered by any two elements also terminates and stays small
    got2 = ddmin(list("abcdefgh"), lambda xs: len(xs) >= 2)
    check(len(got2) <= 3, "ddmin on a monotone failure stays small (%r)" % (got2,))
    # space() is stable and does not alias caller lists
    mods = [{"kind": "unit_movement", "at_tick": 10,
             "params": {"mode": "push", "dx": 2, "dy": 0}}]
    sp = space("unit-control", seeds=(3, 4), modifiers=mods)
    check([p["seed"] for p in sp] == [3, 4], "space keeps seed order")
    check(sp[0]["modifiers"] is not mods, "space copies the modifier bundle")
    check(sp[0]["modifiers"][0] is not mods[0], "space copies each modifier entry")
    check(variant(sp[0])["version"] == 2, "variant is a v2 scenario")
    check(len(explore(sp, evaluator=lambda sc: {"id": sc["id"], "ok": True},
                      via="sim")["failures"]) == 0, "explore with all-ok has no failures")
    # skipped hosts are not failures
    rep = explore(sp, evaluator=lambda sc: {"id": sc["id"], "ok": False,
                                            "skipped": True}, via="sim")
    check(rep["failures"] == [] and rep["skipped"] == 2,
          "unsupported hosts are skipped, not failed")
    print("selftest: 10 checks, %d failure(s)" % fails)
    return 1 if fails else 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print("usage: explore.py {list|run|shrink|selftest} ...")
        return 0 if argv else 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "selftest":
        return _selftest()
    if cmd == "list":
        rows = scenario._cmd_generate.__doc__  # not used; keep the import honest
        for name in scenario.TEMPLATE_ORDER:
            print("%-18s %s" % (name, ", ".join(scenario.TEMPLATE_PARAMS[name])))
        return 0
    if cmd in ("run", "shrink"):
        import argparse
        ap = argparse.ArgumentParser(prog="explore.py " + cmd)
        ap.add_argument("--template", default="unit-control")
        ap.add_argument("--seeds", default="1-5", help="1-5, 1,3,9 ...")
        ap.add_argument("--via", default="sim", choices=["sim", "world"])
        ap.add_argument("--limit", type=int, default=0, help="stop after N failures")
        ap.add_argument("--modifier-file", default=None,
                        help="JSON file holding a list of modifier entries; "
                             "every point gets the same bundle (shrink then reduces it)")
        ap.add_argument("--json", action="store_true")
        ap.add_argument("--save", action="store_true")
        a = ap.parse_args(rest)
        seeds = []
        for part in a.seeds.split(","):
            if "-" in part:
                lo, hi = part.split("-", 1)
                seeds.extend(range(int(lo), int(hi) + 1))
            elif part.strip():
                seeds.append(int(part))
        mods = None
        if a.modifier_file:
            with open(a.modifier_file, encoding="utf-8-sig") as fh:
                mods = json.load(fh)
            if not isinstance(mods, list):
                raise SystemExit("--modifier-file must hold a JSON list")
        if cmd == "run":
            rep = explore(space(a.template, seeds=seeds, modifiers=mods),
                          via=a.via, limit=a.limit)
            if a.save:
                print("saved %s" % save(rep))
        else:
            first = explore(space(a.template, seeds=seeds, modifiers=mods),
                            via=a.via, limit=1)
            if not first["failures"]:
                print("no failure to shrink (%d point(s) tried)" % first["ran"])
                return 0
            rep = shrink(first["failures"][0]["point"], via=a.via)
            if a.save:
                print("saved %s" % save(rep))
        if a.json:
            print(json.dumps(rep, ensure_ascii=False, indent=1))
        else:
            s = rep.get("summary") or {}
            if s:
                print("%d point(s), %d failed, %d skipped"
                      % (s["points"], s["failed"], s["skipped"]))
                for row in rep["failures"][:5]:
                    print("  %s seed=%s failed=%s"
                          % (row["point"]["template"], row["point"]["seed"],
                             ",".join(row.get("failed_checks") or []) or row.get("failure_type")))
            else:
                print("shrunk to %d modifier(s) (dropped %d)"
                      % (rep.get("kept", 0), rep.get("dropped", 0)))
        return 0 if not (rep.get("failures") or rep.get("result", {}).get("ok") is False) else 1
    print("unknown command %r" % cmd)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
