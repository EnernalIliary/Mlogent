"""Scenario, differential and exploratory experiment adapters for MCP."""

import json


def scenario_run(args):
    import scenario as _scen
    level = args.get("level") or "summary"
    sc = _scen.load(args["path"])
    return _scen.run(sc, via=args.get("via") or "sim", level=level)


def diff(args):
    import differential as _diff
    return _diff.run(args["path"], spec=args.get("spec"),
                     level=args.get("level") or "summary")


def observe(args, *, stash):
    import observation as _obs
    a = _load_json(args["a"])
    b = _load_json(args["b"])
    got = _obs.compare(a, b, spec=args.get("spec"))
    level = args.get("level") or "diagnostics"
    if level == "summary":
        diffs = got.get("differences") or []
        return {"same": got.get("same"), "count": len(diffs),
                "unexplained": sum(1 for d in diffs if not d.get("explained")),
                "notes": got.get("notes") or [], "level": "summary"}
    text = json.dumps(got, ensure_ascii=False)
    if len(text) > 2000 and level != "full":
        got = dict(got)
        got["differences_ref"] = stash(json.dumps(got.pop("differences") or [],
                                                   ensure_ascii=False, indent=1))
    return got


def explore(args):
    import explore as _xp
    action = args.get("action") or "list"
    if action == "list":
        return _xp.catalogue() if hasattr(_xp, "catalogue") else _explore_catalogue()
    points = _xp.space(args.get("template") or "unit-control",
                       seeds=tuple(args.get("seeds") or (1,)),
                       params=args.get("params"),
                       modifiers=args.get("modifiers"))
    got = _xp.explore(points, via=args.get("via") or "sim",
                      limit=int(args.get("limit") or 1))
    summ = got.get("summary") or {}
    out = {"template": args.get("template") or "unit-control",
           "ran": summ.get("ran") or got.get("ran"),
           "points": summ.get("points") or got.get("points"),
           "failed": summ.get("failed"),
           "skipped": summ.get("skipped"),
           "ok": summ.get("ok")}
    fails = got.get("failures") or []
    out["failures"] = [{"seed": (f.get("point") or {}).get("seed"),
                        "failure_type": f.get("failure_type"),
                        "next_step": f.get("next_step")} for f in fails[:8]]
    if args.get("shrink") and fails:
        first = fails[0]
        shr = _xp.shrink(first["point"], via=args.get("via") or "sim")
        pt = shr.get("point") or {}
        out["shrunk"] = {
            "seed": pt.get("seed"),
            "kept": sorted(m.get("kind") for m in (pt.get("modifiers") or [])),
            "dropped": shr.get("dropped"),
            "still_fails": shr.get("still_fails"),
        }
    return out


def _explore_catalogue():
    import scenario as _scen
    rows = []
    for name in _scen.TEMPLATE_ORDER:
        rows.append({"template": name,
                     "knobs": sorted((_scen.TEMPLATE_PARAMS.get(name) or {}).keys())})
    return {"templates": rows,
            "note": "action=run takes template + seeds (+ optional params/modifiers); "
                    "each seed x modifier bundle is one fresh generated scenario"}


def _load_json(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


