#!/usr/bin/env python3
"""Turn numeric jump targets into labels, so a .mlog is easier to edit.

Usage:
    python tools/mlog_labelize.py Logic/foo.mlog             # writes foo.labels.mlog
    python tools/mlog_labelize.py Logic/foo.mlog -o out.mlog
    python tools/mlog_labelize.py Logic/foo.mlog --prefix J  # J12: instead of L12

What it does
------------
* A label line (`name:`) is not a statement: the assembler gives it no slot,
  so inserting labels does **not** shift any statement index.
* Every `jump N ...` whose N is a literal inside 0..statement-count-1 gets N
  replaced by `L<N>` (or an existing label directly above that statement).
* Labels are inserted immediately before their target statement.
* Jumps to -1 / out of range, and jumps that already use a label, are left
  alone. Duplicate labels and invalid prefixes are rejected.
* Comments and blank lines are preserved.

The result is for *editing*. Mindustry's LAssembler accepts `label:` lines, but
for delivery run the same post-process as the signature:

    python tools/aigenerated.py post foo.labels.mlog -o foo.mlog

That turns labels back into line numbers and re-signs in one step; the round
trip preserves the jump targets. Signing may normalize the text.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import aigenerated  # noqa: E402
import mlogir  # noqa: E402

LABEL_NAME_RE = aigenerated.LABEL_NAME
LABEL_RE = re.compile(r"^\s*(" + LABEL_NAME_RE.pattern + r"):\s*$")
JUMP_RE = re.compile(r"^(\s*jump\s+)(-?\d+)(\s+.*)?$", re.I)


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


def _check_jump_targets(before: str, after: str):
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


def labelize(text: str, prefix: str = "L", *, preferred_labels: dict[int, str] | None = None):
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

    for t in targets:
        # find the source line of statement t
        line_no = next(i for i, (kind, idx) in enumerate(kinds) if kind == "stmt" and idx == t)
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
    _check_jump_targets(text, result)
    return result, total, len(jumps), sorted(set(names.values()))


def labelize_source(text: str, prefix: str = "L", *, sign: bool = False):
    """Convert editable source, retaining attribution and payload on signed input."""
    hits = aigenerated._find(text)
    saved_labels = {}
    signed = bool(hits)
    if signed:
        problems = aigenerated.verify_text(text)
        if problems:
            raise aigenerated.SignError(problems[0])
        token = hits[0]
        author = token.group(1)
        comments, meta, saved_labels = aigenerated.decode_signature_payload(token.group(3))
        text = aigenerated._body(text)
    elif sign:
        author = aigenerated.DEFAULT_AUTHOR
        comments, meta = aigenerated.collect_comments(text), None

    out_text, total, njumps, labels = labelize(text, prefix, preferred_labels=saved_labels)
    signature = None
    if signed or sign:
        out_text, pid = aigenerated.sign_text(
            out_text, author, force=True, comments=comments, meta=meta,
            labels={target: name for target, name in saved_labels.items() if target < total})
        if comments:
            out_text, pid, _ = aigenerated.restore_text(out_text)
        _check_jump_targets(aigenerated._body(text), aigenerated._body(out_text))
        signature = (author, pid)
    return out_text, total, njumps, labels, signature


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="convert numeric jump targets to labels")
    ap.add_argument("file", help="input .mlog")
    ap.add_argument("-o", "--output", help="output path (default: <stem>.labels.mlog)")
    ap.add_argument("--prefix", default="L", help="label prefix (default: L)")
    ap.add_argument("--check", action="store_true", help="run mlog.py check on the result")
    ap.add_argument("--sign", action="store_true",
                    help="re-apply the @aigenerated signature (automatic if the input is signed)")
    args = ap.parse_args(argv)

    src = Path(args.file)
    if not src.is_file():
        print(f"missing input: {src}", file=sys.stderr)
        return 1
    text = src.read_text(encoding="utf-8-sig")

    try:
        out_text, total, njumps, labels, signature = labelize_source(text, args.prefix, sign=args.sign)
    except (ValueError, aigenerated.SignError) as exc:
        print(f"{src}: {exc}", file=sys.stderr)
        return 1

    dst = Path(args.output) if args.output else src.with_suffix(".labels.mlog")
    dst.write_text(out_text.replace("\r\n", "\n"), encoding="utf-8", newline="\n")
    print(f"labelized {src.name}: {total} statements, {njumps} jump(s), {len(labels)} label(s) -> {dst}")
    if signature:
        author, pid = signature
        print(f"re-signed as {author} (id {pid})")

    if args.check:
        import subprocess
        r = subprocess.run([sys.executable, str(HERE / "mlog.py"), "check", str(dst)])
        if r.returncode:
            return r.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
