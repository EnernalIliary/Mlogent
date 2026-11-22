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
* Comments and blank lines are preserved; a signed editable result ends with
  the attribution token as a comment, ready for `aigenerated.py post` to mount
  it back into a safe slot.

The result is for *editing*. Mindustry's LAssembler accepts `label:` lines, but
for delivery run the same post-process as the signature:

    python tools/aigenerated.py post foo.labels.mlog -o foo.mlog

That turns labels back into line numbers and re-signs in one step; the round
trip preserves the jump targets. Signing may normalize the text.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import aigenerated  # noqa: E402
from mlogent.logic.labels import (  # noqa: E402
    LABEL_NAME_RE, LABEL_RE, JUMP_RE, split_lines, existing_label_above,
    check_jump_targets as _check_jump_targets, labelize,
)


def labelize_source(text: str, prefix: str = "L", *, sign: bool = False):
    """Compatibility entry point for the shared editable-source conversion."""
    from mlogent.logic.source import to_editable

    return to_editable(text, prefix, sign=sign)


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
