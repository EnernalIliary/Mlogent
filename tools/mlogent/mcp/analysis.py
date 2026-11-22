"""Analysis adapters with injected program loading and artifact storage.

This module never imports the MCP server or owns its mutable state.
"""
from __future__ import annotations

import json

import mlogcheck as _check
import mlogir as _ir
import mlogval as _val


def check(args, *, programs, stash):
    level = args.get("level") or "summary"
    limit = int(args.get("limit") or (20 if level == "summary" else 200))
    out = []
    for label, lines, names in programs(args["path"]):
        fs = _check.analyse(lines, names)
        counts = {s: sum(1 for f in fs if f.sev == s)
                  for s in ("ERR", "SUSPECT", "WARN", "INFO")}
        rec = {"program": label, "counts": counts}
        if level != "summary":
            findings = [{"sev": f.sev, "line": f.line, "code": f.code, "msg": f.msg}
                        for f in fs]
            if len(findings) > limit:
                rec["findings"] = findings[:limit]
                rec["more"] = stash(json.dumps(findings[limit:], ensure_ascii=False))
            else:
                rec["findings"] = findings
        if args.get("cost"):
            cost = _check.cost_report(_check.prepare(lines), names)
            cost = cost if isinstance(cost, str) else str(cost)
            rec["cost"] = cost[:4000] if level == "full" else stash(cost)
        out.append(rec)
    return out


def ir(args, *, programs):
    out = []
    for label, lines, names in programs(args["path"]):
        prog = _ir.parse(lines)
        out.append({
            "program": label,
            "statements": len(prog.stmts),
            "unreachable": prog.dead()[:80],
            "dead_stores": [{"line": i + 1, "name": n}
                            for i, n in prog.dead_stores()[:60]],
        })
    return out


def values(args, *, programs, stash):
    out = []
    for label, lines, names in programs(args["path"]):
        prog = _ir.parse(lines)
        st = _val.analyze(prog)
        report = _val.format_report(label, prog, st)
        out.append({"program": label,
                    "report": report[:5000] if len(report) <= 5000 else stash(report)})
    return out


