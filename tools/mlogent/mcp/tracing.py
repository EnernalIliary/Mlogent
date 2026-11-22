"""Trace parsing, filtering and comparison with injected artifact lookup."""
from __future__ import annotations

from bisect import bisect_right
from itertools import zip_longest
import json

import mlogir as _ir


def validate_variables(names) -> list[str]:
    if (not isinstance(names, list) or len(names) > 16
            or any(not isinstance(name, str) or not name or len(name) > 100
                   or any(c in name for c in "=;\t\r\n") for name in names)
            or len(set(names)) != len(names)):
        raise ValueError("trace variables must be a list of up to 16 distinct names")
    return names


def _trace_rows(text: str, source: str | None):
    captured = set()
    mode = None
    if text.lstrip().startswith("{"):
        bundle = json.loads(text)
        if bundle.get("schema") != "mlog-itrace/v1":
            raise ValueError("artifact is not an instruction trace")
        text = bundle["tsv"]
        source = source if source is not None else bundle["mlog"]
        captured.update(bundle["vars"])
        mode = bundle.get("mode")
    lines = iter(text.lstrip("\ufeff").rstrip("\r\n").split("\n"))
    if next(lines, "").rstrip("\r") != "tick\tpc\tvars\tsource":
        raise ValueError("expected an instruction trace TSV with tick, pc, vars, and source columns")

    # Group aliases at each exact target and use the preceding target as the section.
    program = _ir.parse(source.splitlines()) if source is not None else None
    by_pc = {}
    if program is not None:
        for name, pc in program.labels.items():
            by_pc.setdefault(pc, []).append(name)
    boundaries = sorted(by_pc)
    rows = []
    for raw in lines:
        try:
            tick, pc, variables, instruction = raw.rstrip("\r").split("\t", 3)
            row = {"step": len(rows), "tick": int(tick), "pc": int(pc), "source": instruction,
                   "vars": dict(item.split("=", 1) for item in variables.split(";") if item)}
        except ValueError as exc:
            raise ValueError(f"invalid instruction trace row {len(rows) + 2}") from exc
        captured.update(row["vars"])
        if program is not None and 0 <= row["pc"] < len(program.stmts):
            stmt = program.stmts[row["pc"]]
            # Do not attach a source line to a row that was captured from different code.
            if instruction.strip() in (stmt.raw.strip(), stmt.raw[:512].strip()):
                row["line"] = stmt.line
                section = bisect_right(boundaries, row["pc"]) - 1
                row["labels"] = by_pc[boundaries[section]] if section >= 0 else []
        rows.append(row)
    return rows, captured, mode


def _trace_argument(args: dict, inline: str, reference: str, *, required: bool, lookup_artifact) -> str | None:
    if inline in args and reference in args:
        raise ValueError(f"choose {inline} or {reference}")
    if reference in args:
        ref = args[reference]
        result = lookup_artifact(ref) if isinstance(ref, str) else None
        if result is None:
            raise ValueError(f"unknown trace reference {ref!r}")
        return result
    if inline in args:
        if not isinstance(args[inline], str):
            raise ValueError(f"{inline} must be text")
        return args[inline]
    if required:
        raise ValueError(f"provide {inline} or {reference}")
    return None


def trace(args, *, lookup_artifact):
    source = args.get("mlog")
    label = args.get("label")
    if source is not None and not isinstance(source, str):
        raise ValueError("mlog must be text")
    rows, captured, mode = _trace_rows(_trace_argument(args, "trace", "trace_ref", required=True, lookup_artifact=lookup_artifact), source)
    baseline = _trace_argument(args, "baseline_trace", "baseline_ref", required=False, lookup_artifact=lookup_artifact)
    variables = validate_variables(args["vars"]) if "vars" in args else sorted(captured)
    missing = set(variables) - captured
    if missing:
        raise ValueError(f"variables not captured: {', '.join(sorted(missing))}")
    if label is not None and (not isinstance(label, str) or not label.strip()):
        raise ValueError("label must be a non-empty name")
    offset, limit = args.get("offset", 0), args.get("limit", 40)
    if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 200:
        raise ValueError("offset must be non-negative and limit must be between 1 and 200")

    def project(row):
        if row is None:
            return None
        return {**row, "vars": {name: row["vars"].get(name) for name in variables}}

    selected = [row for row in rows if label is None or label in row.get("labels", ())]
    page = selected[offset:offset + limit]
    result = {"total": len(rows), "matched": len(selected), "rows": [project(row) for row in page],
              "next_offset": offset + len(page) if offset + len(page) < len(selected) else None,
              "variables": variables,
              "labels": list(dict.fromkeys(name for row in rows for name in row.get("labels", ())))}
    if mode is not None:
        result["mode"] = mode
    if baseline is not None:
        previous, previous_vars, previous_mode = _trace_rows(baseline, None)
        if mode and previous_mode and mode != previous_mode:
            raise ValueError("compare traces captured in the same simulation mode")
        missing = set(variables) - previous_vars
        if missing:
            raise ValueError(f"variables not captured in baseline: {', '.join(sorted(missing))}")
        def state(row):
            if row is None:
                return None
            return row["tick"], row["pc"], tuple(row["vars"].get(name) for name in variables)

        divergence = None
        for step, (before, after) in enumerate(zip_longest(previous, rows)):
            if state(before) != state(after):
                divergence = {"step": step, "baseline": project(before), "current": project(after)}
                break
        result["first_divergence"] = divergence
    return result


