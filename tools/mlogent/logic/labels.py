"""Label syntax, instruction layout and reversible jump rewriting.

No signing or CLI dependencies. Comments and labels do not occupy instruction
slots; both conversion directions use the same layout scanner.
"""
from __future__ import annotations

import re

LABEL_NAME_RE = re.compile(r"[A-Za-z_][\w.\-]*")
LABEL_RE = re.compile(r"^\s*(" + LABEL_NAME_RE.pattern + r"):\s*$")
JUMP_RE = re.compile(r"^(\s*jump\s+)(-?\d+)(\s+.*)?$", re.I)
JUMP_LABEL_RE = re.compile(r"^(\s*jump\s+)([A-Za-z_][\w.\-]*)(\s+.*)?$", re.I)


class LabelError(ValueError):
    """A label declaration cannot be resolved without ambiguity."""


def split_lines(text: str):
    """Return (lines, kinds, stmt_index) where kind is blank/comment/label/stmt."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    kinds, idx = [], 0
    for line in lines:
        s = line.strip()
        if not s:
            kinds.append(("blank", None))
        elif s.startswith("#"):
            kinds.append(("comment", None))
        elif LABEL_RE.match(line):
            kinds.append(("label", None))
        else:
            kinds.append(("stmt", idx))
            idx += 1
    return lines, kinds, idx


def existing_label_above(lines, kinds, line_no: int) -> str | None:
    """Label on the line directly above (skipping blanks only)."""
    j = line_no - 1
    while j >= 0 and kinds[j][0] == "blank":
        j -= 1
    if j >= 0 and kinds[j][0] == "label":
        return lines[j].strip().rstrip(":")
    return None


def check_jump_targets(before: str, after: str):
    import mlogir

    def destinations(text):
        program = mlogir.parse(text)
        jumps = {}
        for index, stmt in enumerate(program.stmts):
            if stmt.mnemonic == "jump":
                target = stmt.jump_target()
                jumps[index] = target if target is not None else stmt.arg_text(0)
        return len(program.stmts), jumps

    before_count, before_jumps = destinations(before)
    after_count, after_jumps = destinations(after)
    if before_count != after_count or before_jumps.keys() != after_jumps.keys():
        raise ValueError("labelization changed the statement layout")
    for index, target in before_jumps.items():
        if after_jumps[index] != target:
            raise ValueError(f"labelization changed jump at instruction {index}: "
                             f"{target!r} -> {after_jumps[index]!r}")


def labelize(text: str, prefix: str = "L", *, preferred_labels: dict[int, str] | None = None,
            preserve_always: bool = False):
    if not LABEL_NAME_RE.fullmatch(prefix):
        raise ValueError(f"invalid label prefix: {prefix!r}")

    lines, kinds, total = split_lines(text)
    used: set[str] = set()
    for line_no, (line, (kind, _)) in enumerate(zip(lines, kinds), 1):
        if kind != "label":
            continue
        name = line.strip()[:-1]
        if name in used:
            raise ValueError(f"duplicate label {name!r} on line {line_no}")
        used.add(name)

    jumps = []          # (line_no, target)
    for i, (kind, idx) in enumerate(kinds):
        if kind != "stmt":
            continue
        # Keep the signed delivery mount point numeric in editable output.
        if preserve_always and re.match(
                r"^\s*jump\s+\S+\s+always(?:\s+\S+)?(?:\s+.*)?$", lines[i], re.I):
            continue
        m = JUMP_RE.match(lines[i])
        if not m:
            continue
        target = int(m.group(2))
        if 0 <= target < total:
            jumps.append((i, int(m.group(2))))

    targets = sorted({t for _, t in jumps})
    preferred_labels = preferred_labels or {}
    # Reserve saved names before generating defaults, even for a later target.
    preferred = {target: preferred_labels[target] for target in targets
                 if target in preferred_labels and preferred_labels[target] not in used
                 and LABEL_NAME_RE.fullmatch(preferred_labels[target])}
    reserved = set(preferred.values())
    insert_at: dict[int, list[str]] = {}
    names: dict[int, str] = {}

    statement_lines = {idx: i for i, (kind, idx) in enumerate(kinds) if kind == "stmt"}
    for t in targets:
        line_no = statement_lines[t]
        above = existing_label_above(lines, kinds, line_no)
        if above:
            names[t] = above
            continue
        name = preferred.get(t)
        if name is None or name in used:
            name = f"{prefix}{t}"
            n = 2
            while name in used or name in reserved:
                name = f"{prefix}{t}_{n}"
                n += 1
        used.add(name)
        names[t] = name
        insert_at.setdefault(line_no, []).append(f"{name}:")

    for i, target in jumps:
        m = JUMP_RE.match(lines[i])
        lines[i] = f"{m.group(1)}{names[target]}{m.group(3) or ''}"

    out = []
    for i, line in enumerate(lines):
        for name in insert_at.get(i, []):
            out.append(name)
        out.append(line)
    result = "\n".join(out) + "\n"
    check_jump_targets(text, result)
    return result, total, len(jumps), sorted(set(names.values()))


def resolve(text: str, *, strict: bool = False) -> tuple[str, dict[str, int], int]:
    """Resolve known jump labels and remove declarations, preserving all slots."""
    lines, kinds, _ = split_lines(text)
    declarations = {}
    statement = 0
    for line, (kind, index) in zip(lines, kinds):
        if kind == "label":
            name = LABEL_RE.match(line).group(1)
            if strict and name in declarations:
                raise LabelError(f"duplicate label {name!r}")
            declarations[name] = statement
        elif kind == "stmt":
            statement = index + 1
    out = []
    rewritten = 0
    for line, (kind, _) in zip(lines, kinds):
        if kind == "label":
            continue
        if kind == "stmt":
            match = JUMP_LABEL_RE.match(line)
            if match and match.group(2) in declarations:
                line = f"{match.group(1)}{declarations[match.group(2)]}{match.group(3) or ''}"
                rewritten += 1
        out.append(line)
    return "\n".join(out) + "\n", declarations, rewritten


