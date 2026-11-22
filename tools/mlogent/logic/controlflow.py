"""Address-preserving conversion checks, not a proof about arbitrary edits."""
from __future__ import annotations

from .labels import resolve


def _program(text):
    from mlogir import parse
    from .signature import _body

    numeric, _, _ = resolve(_body(text), strict=True)
    return parse(numeric)


def _meaningful(stmt):
    from mlogir import tokenize
    from .cleanup import clean

    line, _ = clean(stmt.raw)
    tokens = [t.text for t in tokenize(line)]
    # Neither comparison operand participates in an unconditional jump. This
    # comparison does not remove user declarations from the delivered source.
    if len(tokens) >= 3 and tokens[0] == "jump" and tokens[2] == "always":
        return tokens[:3]
    return tokens


def difference(before: str, after: str) -> dict:
    original, output = _program(before), _program(after)
    modified, jump_changes = [], []
    equivalent = len(original.stmts) == len(output.stmts)
    for index, (left, right) in enumerate(zip(original.stmts, output.stmts)):
        if left.raw != right.raw:
            modified.append({"instruction": index, "before": left.raw, "after": right.raw})
        equivalent = equivalent and _meaningful(left) == _meaningful(right)
        if left.mnemonic == "jump" and left.arg_text(0) != right.arg_text(0):
            jump_changes.append({"instruction": index, "before": left.arg_text(0),
                                 "after": right.arg_text(0)})
    return {"original_instructions": len(original.stmts), "output_instructions": len(output.stmts),
            "added": [s.raw for s in output.stmts[len(original.stmts):]],
            "removed": [s.raw for s in original.stmts[len(output.stmts):]],
            "modified": modified, "jump_target_changes": jump_changes,
            "instruction_semantics_preserved": bool(equivalent)}


def extraction_diagnostics(original: str, editable: str) -> dict:
    from mlogir import parse, tokenize
    from .signature import _find, verify_text

    program = _program(original)
    output = parse(editable)
    static, labeled, unconverted, writes, reads = 0, 0, [], [], []
    for index, stmt in enumerate(program.stmts):
        if "@counter" in stmt.defs:
            writes.append({"instruction": index, "code": stmt.raw})
        if "@counter" in stmt.uses:
            reads.append({"instruction": index, "code": stmt.raw})
        if stmt.mnemonic != "jump":
            continue
        target = stmt.jump_target()
        if target is None:
            unconverted.append({"instruction": index, "target": stmt.arg_text(0),
                                "reason": "unresolved or non-integer target"})
            continue
        static += 1
        if not 0 <= target < len(program.stmts):
            unconverted.append({"instruction": index, "target": target,
                                "reason": "target does not address an existing instruction"})
        elif tokenize(output.stmts[index].raw)[1].text in output.labels:
            labeled += 1
        else:
            unconverted.append({"instruction": index, "target": target,
                                "reason": "static target was not converted to a label"})
    diff = difference(original, editable)
    return {"original_instructions": len(program.stmts), "output_instructions": len(output.stmts),
            "static_jumps": static, "labeled_jumps": labeled, "unconverted_jumps": unconverted,
            "counter_writes": writes, "counter_reads": reads,
            "dynamic_counter_operations": len(writes),
            "signature_status": ("valid" if not verify_text(original) else "invalid")
                                if _find(original) else "unsigned",
            "safe_to_recompile": diff["instruction_semantics_preserved"] and not unconverted,
            "recompile_safety_scope": "Unedited output preserves instruction semantics and addresses; "
                                      "this does not validate arbitrary edits or runtime conditions.",
            "address_sensitive": bool(writes or reads),
            "limitations": (["Dynamic @counter control flow is preserved by keeping every instruction address. "
                              "Adding, removing or reordering instructions requires manual analysis; "
                              "dynamic destinations are not proven."] if writes or reads else []),
            "conversion": diff}
