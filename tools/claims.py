"""Evidence pointers for the knowledge base's claim ledger.

`knowledge/08-evidence/claims.jsonl` states each MLOG claim once, with a
`src` list naming where it comes from. Those pointers used to be line numbers
(`docs/断言表.md:19`), which silently rot every time a document above the
row grows a paragraph -- by 2026-11-18, 89 of 168 pointers were off.

This module makes the pointers id-anchored instead: `docs/断言表.md#L1-01`
means "the table row whose first cell is L1-01". Line numbers are still
accepted (older records keep working) but they are checked, not trusted:
`check()` fails when a `:NN` pointer no longer lands on the claimed row.

    python tools/claims.py check          # exit 1 when a pointer is broken
    python tools/claims.py fix --write    # rewrite :NN pointers as #ID
    python tools/claims.py list L2-1      # show one claim and where it resolves
    python tools/claims.py selftest

Stdlib only. No absolute paths.
"""

import argparse
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CLAIMS = os.path.join(ROOT, "knowledge", "08-evidence", "claims.jsonl")

REF_RE = re.compile(r"^(?P<path>[^#]+?)(?:#(?P<ident>[A-Za-z0-9_-]+)|:(?P<line>\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*))$")
ROW_RE = re.compile(r"^\|\s*(?P<ident>[A-Za-z][A-Za-z0-9_-]*)\s*\|")

# Trees that are not part of this checkout, so a source pointer into them can
# only be checked for shape, not for content.
EXTERNAL = ("Mindustry-Source/", "out/", "Arc-Source/")


def _rel(path):
    return os.path.relpath(path, ROOT).replace("\\", "/")


def load(path=CLAIMS):
    """Read the ledger. Blank lines are skipped, not an error."""
    rows = []
    with io.open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def save(rows, path=CLAIMS):
    """Write the ledger back, one claim per line, UTF-8, LF, no BOM."""
    text = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n"
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def parse_ref(ref):
    """Split `path#ID` or `path:NN` into (path, ident, line)."""
    m = REF_RE.match(ref.strip())
    if not m:
        return None
    path = m.group("path").strip()
    ident = m.group("ident")
    spec = m.group("line") or None
    return path, ident, spec


def rows(path):
    """(line number, first cell) for every table row in `path`."""
    full = os.path.join(ROOT, path.replace("/", os.sep))
    if not os.path.isfile(full):
        return None
    out = []
    with io.open(full, encoding="utf-8") as fh:
        for i, line in enumerate(fh, 1):
            m = ROW_RE.match(line)
            if m:
                out.append((i, m.group("ident").strip()))
    return out


def _match(table, ident):
    """Rows for `ident`, tolerating the a/b splits the logs use (L2-10a)."""
    exact = [i for i, name in table if name == ident]
    if exact:
        return exact
    split = re.compile(r"^" + re.escape(ident) + r"[a-z]$")
    return [i for i, name in table if split.match(name)]


def resolve(ref):
    """Where does this pointer land? Returns (lines, problem-or-None).

    `path#ID` is the durable form: it finds the table row named ID, tolerating
    the a/b splits the verification log uses (L2-10a, S-13b). `path:NN` is
    accepted for older records and ranges (`:344-356`, `:6872-6883,6962-6969`)
    are accepted for source pointers, but only a bare number is checked for
    drift.
    """
    parsed = parse_ref(ref)
    if parsed is None:
        return [], "not a pointer (want path#ID or path:NN)"
    path, ident, spec = parsed
    table = rows(path)
    if table is None:
        if path.startswith(EXTERNAL):
            return [], None
        return [], "file not found: %s" % path
    if not table and path.startswith(EXTERNAL):
        # a source file: no table rows exist in it, only line numbers
        return [], None
    if ident:
        hits = _match(table, ident)
        if not hits:
            return [], "%s has no row named %s" % (path, ident)
        return hits, None
    first = int(spec.split("-")[0].split(",")[0])
    if first < 1 or first > max((i for i, _ in table), default=0) + 200:
        return [], "%s:%s is past the end" % (path, spec)
    if "-" in spec or "," in spec:
        return [first], None
    names = [name for i, name in table if i == first]
    if not names:
        return [], "%s:%s is not a table row" % (path, spec)
    return [first], None


def check(records=None):
    """Every pointer must resolve, and must resolve to the claim it belongs to.

    A `:NN` pointer also has to *land* on that claim's row -- that is the check
    that catches drift after a document above the table grows.
    """
    records = load() if records is None else records
    problems = []
    for rec in records:
        ident = rec.get("id", "?")
        for ref in rec.get("src") or []:
            lines, problem = resolve(ref)
            if problem:
                problems.append((ident, ref, problem))
                continue
            parsed = parse_ref(ref)
            want = ident
            if parsed[0].startswith(EXTERNAL):
                continue
            landed = [name for i, name in (rows(parsed[0]) or []) if i in lines]
            if not any(n == want or re.match(r"^" + re.escape(want) + r"[a-z]$", n)
                       for n in landed):
                problems.append((ident, ref, "lands on %s, not %s"
                                 % (", ".join(landed) or "nothing", want)))
    return problems


def fix(records=None, write=False):
    """Rewrite line pointers as id anchors. Returns (rows, changes)."""
    records = load() if records is None else records
    changes = []
    for rec in records:
        src = rec.get("src") or []
        new = []
        for ref in src:
            parsed = parse_ref(ref)
            if parsed is None or parsed[1] is not None:
                new.append(ref)
                continue
            path, _ident, _line = parsed
            target = path + "#" + rec["id"]
            # only migrate when the anchor actually exists for this claim
            lines, problem = resolve(target)
            if problem:
                changes.append((rec["id"], ref, "kept (no anchor: %s)" % problem))
                new.append(ref)
            else:
                changes.append((rec["id"], ref, "-> " + target))
                new.append(target)
        rec["src"] = new
    if write:
        save(records)
    return records, changes


TABLE = os.path.join(ROOT, "docs", "断言表.md")


def _cells(line):
    """Split a table row on unescaped pipes; the leading/trailing ones drop out."""
    body = line.rstrip("\n").strip()
    if not body.startswith("|"):
        return None
    parts = re.split(r"(?<!\\)\|", body)
    return parts[1:-1]


def _join(cells):
    return "|" + "|".join(cells) + "|\n"


def render(records=None, path=TABLE, write=False):
    """Rewrite the 断言 cell of every ledger row from claims.jsonl.

    The table is the human index; the ledger is the source. Three rows had
    already drifted (L1-18 still said "越界读出 0" where the ledger says null),
    which is exactly the failure mode a projection prevents.

    Only the 断言 cell is projected: 预期/验法/判定 are presentation, and the
    判定 cell carries prose ("⚠️ 结论成立（S），证据错误待重取…") that the
    ledger keeps in its own `evidence` field.
    """
    records = load() if records is None else records
    by_id = {r["id"]: r for r in records}
    with io.open(path, encoding="utf-8") as fh:
        lines = fh.readlines()
    changes = []
    for i, line in enumerate(lines):
        m = ROW_RE.match(line)
        if not m:
            continue
        ident = m.group("ident")
        rec = by_id.get(ident)
        if rec is None:
            continue
        cells = _cells(line)
        if not cells or len(cells) < 2:
            continue
        want = str(rec.get("claim", "")).strip().replace("|", "\\|")
        if cells[1].strip() == want:
            continue
        changes.append((ident, cells[1].strip()[:60], want[:60]))
        cells[1] = " " + want + " "
        lines[i] = _join(cells)
    if write and changes:
        with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.writelines(lines)
    return changes


def _selftest():
    ok = fail = 0

    def case(name, cond):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print("FAIL", name)

    case("parse id", parse_ref("docs/断言表.md#L1-01") == ("docs/断言表.md", "L1-01", None))
    case("parse line", parse_ref("docs/断言表.md:19") == ("docs/断言表.md", None, "19"))
    case("parse junk", parse_ref("L1-01") is None)
    table = rows("docs/断言表.md")
    case("table readable", bool(table))
    lines, problem = resolve("docs/断言表.md#L1-01")
    case("anchor resolves", problem is None and len(lines) == 1)
    case("anchor lands on the row", lines and
         io.open(os.path.join(ROOT, "docs", "断言表.md"), encoding="utf-8")
         .read().splitlines()[lines[0] - 1].startswith("| L1-01 |"))
    lines, problem = resolve("docs/断言表.md#NOPE-99")
    case("missing anchor is a problem", problem is not None)
    lines, problem = resolve("docs/nope.md#L1-01")
    case("missing file is a problem", problem is not None)
    case("split ids tolerated", bool(_match([(1, "L2-10a"), (2, "L2-10b")], "L2-10")))
    records = [{"id": "L1-01", "src": ["docs/断言表.md#L1-01"]}]
    case("clean record passes", check(records) == [])
    records = [{"id": "L1-02", "src": ["docs/断言表.md#L1-01"]}]
    case("wrong row is caught", len(check(records)) == 1)
    case("cells split on escaped pipe",
         _cells("| L1-08 | a \\| b | c | d |")[1].strip() == "a \\| b")
    case("render is a no-op on a synced table", render(records=[
        {"id": "L1-01", "claim": "执行到 `end` 后 `@counter` 归 0，下一 tick 从头跑"},
    ]) == [])
    case("render reports a stale cell", len(render(records=[
        {"id": "L1-01", "claim": "something else entirely"},
    ])) == 1)
    print("claims selftest: %d ok, %d failed" % (ok, fail))
    return 0 if fail == 0 else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("check", help="verify every pointer")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("fix", help="rewrite line pointers as id anchors")
    p.add_argument("--write", action="store_true")

    p = sub.add_parser("render", help="project claim text into docs/断言表.md")
    p.add_argument("--write", action="store_true")

    p = sub.add_parser("list", help="show one claim and where it resolves")
    p.add_argument("ident", nargs="?")
    p.add_argument("--json", action="store_true")

    sub.add_parser("selftest")

    args = ap.parse_args(argv)
    if args.cmd == "check":
        problems = check()
        if args.json:
            print(json.dumps({"ok": not problems, "problems": problems},
                             ensure_ascii=False, indent=1))
        else:
            for ident, ref, why in problems:
                print("%-8s %-34s %s" % (ident, ref, why))
            print("%d problem(s)" % len(problems))
        return 0 if not problems else 1
    if args.cmd == "fix":
        records, changes = fix(write=args.write)
        for ident, old, new in changes:
            print("%-8s %-30s %s" % (ident, old, new))
        print("%d pointer(s) %s" % (len(changes),
                                    "rewritten" if args.write else "would change"))
        return 0
    if args.cmd == "render":
        changes = render(write=args.write)
        for ident, was, now in changes:
            print("%-8s %s\n         -> %s" % (ident, was, now))
        print("%d row(s) %s" % (len(changes),
                                "rewritten" if args.write else "would change"))
        return 0 if not changes or args.write else 1
    if args.cmd == "list":
        records = load()
        for rec in records:
            if args.ident and rec.get("id") != args.ident:
                continue
            out = {"id": rec.get("id"), "claim": rec.get("claim"),
                   "conf": rec.get("conf"), "src": []}
            for ref in rec.get("src") or []:
                lines, problem = resolve(ref)
                out["src"].append({"ref": ref, "lines": lines, "problem": problem})
            print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0
    if args.cmd == "selftest":
        return _selftest()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
