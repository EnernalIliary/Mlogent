"""Simulator console record/trace parsers and trace assertion reporting."""
from __future__ import annotations

import sys


def parse_trace(lines: list[str]) -> list[list[str]]:
    rows = []
    for ln in lines:
        if ln.startswith("TRACE\t"):
            parts = ln.split("\t")
            if len(parts) >= 15:
                rows.append(parts[1:])
    return rows


PAD_COLUMNS = ["name", "x", "y", "config", "arriving", "cooldown", "items",
                "water", "efficiency", "landings", "allow_edit", "configurable"]


def parse_pads(lines: list[str]) -> list[dict]:
    """Collect the PAD status rows printed by pads_js().

    One row per pad: name, tile x/y, config (the item it is told to receive),
    arriving (the item currently in flight), cooldown, items, water, efficiency
    and how many times something landed. cooldown/arriving are the two things
    logic cannot read at all (LAccess has no such entries), so this is the only
    way to watch a pad's cycle.
    """
    out = []
    for ln in lines:
        if not ln.startswith("PAD\t"):
            continue
        vals = ln.split("\t")[1:]
        rec = dict(zip(PAD_COLUMNS, vals))
        for k in ("x", "y", "cooldown", "items", "water", "efficiency", "landings"):
            if k in rec:
                try:
                    rec[k] = float(rec[k])
                except ValueError:
                    rec[k] = None
        out.append(rec)
    return out


def parse_results(lines: list[str]) -> list[dict]:
    """Turn @@BEGIN blocks into records."""
    recs: list[dict] = []
    cur = None
    for ln in lines:
        if ln.startswith("@@BEGIN"):
            cur = {"label": ln.split("\t", 1)[1] if "\t" in ln else "", "vars": {}, "counter": None,
                   "ipt": None, "accumulator": None, "text": "", "skipped": []}
            recs.append(cur)
        elif ln.startswith("@@END"):
            cur = None
        elif ln.startswith("SKIP\t") and recs:
            recs[-1]["skipped"].append(ln.split("\t", 1)[1])
        elif cur is not None:
            if ln.startswith("VAR\t"):
                _, k, v = ln.split("\t", 2)
                cur["vars"][k] = v
            elif ln.startswith("COUNTER\t"):
                cur["counter"] = float(ln.split("\t", 1)[1])
            elif ln.startswith("IPT\t"):
                cur["ipt"] = float(ln.split("\t", 1)[1])
            elif ln.startswith("BLOCK\t"):
                cur["processor_block"] = ln.split("\t", 1)[1]
            elif ln.startswith("RAN\t"):
                cur["executed"] = ln.split("\t", 1)[1] == "true"
            elif ln.startswith("ACC\t"):
                cur["accumulator"] = float(ln.split("\t", 1)[1])
            elif ln.startswith("TEXT\t"):
                cur["text"] = ln.split("\t", 1)[1].replace("\\n", "\n")
    return recs


TRACE_COLUMNS = ["unit", "tick", "ux", "uy", "uhp", "range", "tx", "ty", "dist",
                 "cx", "cy", "chp", "bullets", "shots"]


def check_asserts(rows: list[list[str]], exprs: list[str], *, output=None) -> int:
    """Evaluate EXPR per trace row; return the number of failed evaluations."""
    if not rows:
        print("ASSERT: no unit trace rows (spawn units or use a scene with units)", file=sys.stderr)
        return 1
    fails = []
    for expr in exprs:
        for row in rows:
            env = {}
            for key, val in zip(TRACE_COLUMNS, row):
                if key == "unit":
                    env[key] = val
                else:
                    try:
                        env[key] = float(val)
                    except ValueError:
                        env[key] = None
            try:
                ok = bool(eval(expr, {"__builtins__": {}}, env))  # noqa: S307 - local, no builtins
            except Exception as e:  # noqa: BLE001 - report, do not crash
                ok = False
                env["_error"] = str(e)
            if not ok:
                fails.append((expr, env))
    if not fails:
        print(f"ASSERT PASS  {len(rows)} row(s) x {len(exprs)} expr(s)", file=output)
        return 0
    for expr, env in fails[:5]:
        detail = " ".join(f"{k}={env[k]}" for k in
                          ("tick", "unit", "dist", "range", "chp", "ux", "uy") if k in env)
        err = f"  ({env['_error']})" if "_error" in env else ""
        print(f"ASSERT FAIL  {expr}\n              {detail}{err}", file=output)
    print(f"ASSERT FAILED  {len(fails)}/{len(rows) * len(exprs)} evaluation(s)", file=output)
    return len(fails)


def _write_trace(path: str, rows: list[list[str]]):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(",".join(TRACE_COLUMNS) + "\n")
        for row in rows:
            fh.write(",".join(row) + "\n")
