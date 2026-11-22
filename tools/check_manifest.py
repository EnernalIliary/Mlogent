#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Repo-wide integrity manifest: the code, the gates and the rule table.

The portable skill copies carry their own MANIFEST.sha256, checked by
`mlogagent.py info --verify`. That one deliberately covers only the payload that
gets copied onto another machine (11 modules + 11 data tables). Everything else
this repo ships -- the repo-side tools, the four test gates, the rule table --
was outside any manifest, so editing it silently changed behaviour with no way
for a reader to notice.

This manifest covers exactly that gap.

Covered:
    tools/*.py, tools/*.json          (top level only)
    tools/corpus/*.py
    tools/mlogent/**/*.{py,json,html,js,css}
    tests/**/*.py, tests/**/*.json, tests/cases/*.mlog
    rules/**/*.json

Not covered on purpose:
    knowledge/            edited constantly; a stale hash there costs more than
                          it protects (the schema gate is check_kb.py)
    docs/                 prose, rewritten every round
    .dsh/, mindustry-blueprint/
                          mirrored copies -- they carry their own MANIFEST.sha256
    out/, dist/, saves/, assetsraw/
                          drafts, build output, local data

Usage:
    python tools/check_manifest.py             # verify (exit 1 on any drift)
    python tools/check_manifest.py --write     # regenerate after an intended change
    python tools/check_manifest.py --root DIR  # check another tree (e.g. the public export)

Hashes are taken over CRLF-normalised bytes, same rule as `mlogagent._sha`, so a
Windows checkout and a Linux one agree.
"""
import argparse
import hashlib
import os
import subprocess
import sys

MANIFEST_NAME = "MANIFEST.repo.sha256"

PATTERNS = (
    "tools/*.py",
    "tools/*.json",
    "tools/corpus/*.py",
    "tools/mlogent/**/*.py",
    "tools/mlogent/**/*.json",
    "tools/mlogent/**/*.html",
    "tools/mlogent/**/*.js",
    "tools/mlogent/**/*.css",
    "tests/mcphttp/*.js",
    "tests/**/*.py",
    "tests/**/*.json",
    "tests/cases/*.mlog",
    "tests/source/fixtures/*.mlog",
    "rules/**/*.json",
)

SKIP_PARTS = ("__pycache__", ".pytest_cache")
SKIP_SUFFIX = (".pyc", ".bak")


def _tracked(root):
    """repo-tracked paths, or None when this is not a git checkout.

    清单只该描述"随仓库发出去的东西"：本机 out/ 下、被 .gitignore 挡住的临时脚本
    不该让校验在别的机器上失败，所以有 git 时按索引过滤。
    """
    try:
        raw = subprocess.run(["git", "-C", str(root), "ls-files", "-z"],
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                             check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    return {p for p in raw.decode("utf-8", "replace").split("\0") if p}


def _iter_files(root):
    tracked = _tracked(root)
    out = []
    for pat in PATTERNS:
        for path in root.glob(pat):
            if not path.is_file():
                continue
            rel = path.relative_to(root).as_posix()
            low = rel.lower()
            if any(p in low for p in SKIP_PARTS) or low.endswith(SKIP_SUFFIX) or ".bak" in low:
                continue
            if tracked is not None and rel not in tracked:
                continue
            out.append(rel)
    return sorted(set(out))


def _digest(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def build(root):
    return "".join("%s  %s\n" % (_digest(root / rel), rel) for rel in _iter_files(root))


def parse(text):
    entries = {}
    for line in text.splitlines():
        if "  " not in line:
            continue
        digest, rel = line.split("  ", 1)
        entries[rel.strip()] = digest.strip()
    return entries


def verify(root):
    dst = root / MANIFEST_NAME
    if not dst.is_file():
        print("no %s in %s" % (MANIFEST_NAME, root))
        print("run: python tools/check_manifest.py --write")
        return 2
    want = parse(dst.read_text(encoding="utf-8"))
    have = {rel: _digest(root / rel) for rel in _iter_files(root)}
    problems = []
    for rel in sorted(set(want) | set(have)):
        if rel not in have:
            problems.append(("MISSING", rel))
        elif rel not in want:
            problems.append(("UNLISTED", rel))
        elif want[rel] != have[rel]:
            problems.append(("DIFF", rel))
    if not problems:
        print("ok: %d file(s) match %s" % (len(have), MANIFEST_NAME))
        return 0
    for kind, rel in problems:
        print("%-9s %s" % (kind, rel))
    print("%d problem(s): the tree changed under %s." % (len(problems), MANIFEST_NAME))
    print("if the change was intended: python tools/check_manifest.py --write")
    return 1


def main():
    ap = argparse.ArgumentParser(description="repo-wide integrity manifest")
    ap.add_argument("--write", action="store_true", help="regenerate " + MANIFEST_NAME)
    ap.add_argument("--root", default=None, help="tree to check (default: repo root)")
    args = ap.parse_args()
    root = __import__("pathlib").Path(args.root).resolve() if args.root else \
        __import__("pathlib").Path(__file__).resolve().parent.parent
    if args.write:
        text = build(root)
        (root / MANIFEST_NAME).write_text(text, encoding="utf-8", newline="\n")
        print("wrote %s: %d file(s)" % (MANIFEST_NAME, len(text.splitlines())))
        return 0
    return verify(root)


if __name__ == "__main__":
    sys.exit(main())
