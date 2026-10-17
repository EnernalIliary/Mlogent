#!/usr/bin/env python
"""
mlog.py -- Mindustry blueprint (.msch) toolkit: read, write, validate.

One entry point for everything this skill does.

Usage
-----
  python mlog.py parse  <file.msch>            # dump a blueprint's blocks + logic
  python mlog.py gen    <logic.mlog> [opts]    # build a .msch (or paste code)
  python mlog.py check  <logic.mlog | --msch F> # static analysis of mlog
  python mlog.py ir     <logic.mlog | --msch F> # CFG: unreachable code, dead stores
                                               #   (--all also shows forced output
                                               #    slots and literal declarations)
  python mlog.py id     [name]                 # block content ids / sizes
  python mlog.py item   [name] [--unpack N]    # item content ids / packed configs
  python mlog.py cmd    [pattern]              # mlog instruction reference
  python mlog.py selftest                      # round-trip every real blueprint

Examples
--------
  # blueprint -> readable dump (logic extracted verbatim)
  python mlog.py parse "schem/无线超.msch"

  # emit a paste-ready blueprint code, with the target block placed
  python mlog.py gen logic.mlog --name "无线超" \
      --link dome1@3,1 --with-block overdrive-dome@4,2=248

  # check logic before generating
  python mlog.py check logic.mlog
  python mlog.py check --msch out.msch

Notes
-----
* A schematic stores a block's CENTER tile, not its corner (verified 2 ways).
* Logic is stored as PLAIN TEXT inside the blueprint -- no decompilation needed.
* Content ids are NOT serialized in a schematic; the game resolves blocks by
  NAME on load. Ids matter only for building content values inside a config.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import mlogcheck as _check          # noqa: E402
import mlogir as _ir                # noqa: E402
import msch                          # noqa: E402
import mschgen as _gen              # noqa: E402


def _load_json(name: str) -> dict:
    p = os.path.join(HERE, name)
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


BLOCK_IDS = _load_json("wiki_block_ids.json").get("blocks", {})
BLOCK_SIZES = _load_json("block_sizes.json")
CMD_INDEX = _load_json("cmd_index.json")
ITEM_IDS = _load_json("item_ids.json").get("items", {})
ITEM_NAME_TO_ID = {v: int(k) for k, v in ITEM_IDS.items()}


# --------------------------------------------------------------------------- #
# parse
# --------------------------------------------------------------------------- #

def cmd_parse(args) -> int:
    sch = msch.parse_file(args.file)
    print(f"name  : {sch.name}")
    if sch.description:
        print(f"desc  : {sch.description}")
    if sch.labels:
        print(f"labels: {sch.labels}")
    print(f"size  : {sch.width} x {sch.height}")
    print(f"tiles : {len(sch.tiles)}")
    print()

    for t in sch.tiles:
        sz = _gen.block_size(t.block)
        half = (sz - 1) // 2
        span = (f"({t.x-half},{t.y-half})..({t.x-half+sz-1},{t.y-half+sz-1})"
                if sz > 1 else f"({t.x},{t.y})")
        extra = ""
        if t.logic:
            stmts = len(t.logic.statement_lines())
            links = ", ".join(f"{l.name}@({l.x},{l.y})" for l in t.logic.links)
            extra = f"  [{stmts} stmts]" + (f"  links: {links}" if links else "")
        print(f"  {t.block:22} center@({t.x},{t.y}) span {span}{extra}")

    logic = sch.logic_tiles()
    if logic:
        print()
        print("=" * 70)
        for t in logic:
            assert t.logic is not None
            print(f"--- {t.block} @({t.x},{t.y}) ---")
            print(t.logic.code.rstrip("\n"))
            print()
    return 0


# --------------------------------------------------------------------------- #
# gen
# --------------------------------------------------------------------------- #

def cmd_gen(args) -> int:
    if args.logic:
        code = args.logic
    elif args.source:
        with open(args.source, encoding="utf-8") as fh:
            code = fh.read()
    else:
        code = sys.stdin.read()

    try:
        px, py = (int(v) for v in args.at.split(","))
    except ValueError:
        print("--at must look like x,y", file=sys.stderr)
        return 2

    try:
        links = [_gen.parse_link(s) for s in args.link]
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2

    bp = _gen.Blueprint(args.name, args.description, args.label)
    bp.add_logic(code, px, py, args.block, args.rotation, links)

    placed = []
    for spec in args.with_block:
        try:
            blk, dx, dy, cid = _gen.parse_with_block(spec)
        except ValueError as e:
            print(str(e), file=sys.stderr)
            return 2
        bp.add_block(blk, px + dx, py + dy, 0, None, cid)
        placed.append(f"{blk} center@({px+dx},{py+dy})"
                      + (f" id={cid}" if cid is not None else ""))

    data = bp.build()

    # never emit something that does not read back
    back = msch.parse_bytes(data)
    got = back.logic_tiles()
    if not (got and got[0].logic and got[0].logic.code.strip() == code.strip()
            and back.name == args.name):
        print("VERIFY FAILED -- not emitting", file=sys.stderr)
        return 1

    stmts = len([l for l in code.split("\n") if l.strip()])
    w, h = bp.bounds()
    print(f"# {args.block} @({px},{py})  {stmts} stmts  {w}x{h}  "
          f"links={[f'{l.name}@{l.dx},{l.dy}' for l in links] or '(none)'}",
          file=sys.stderr)
    for p in placed:
        print(f"# placed: {p}", file=sys.stderr)
    for msg in bp.link_report():
        print(f"# NOTE: {msg}", file=sys.stderr)
    if args.auto_link:
        for lk in links:
            print(f"# link name check: {lk.name}", file=sys.stderr)

    if args.out:
        b64 = base64.b64encode(data).decode()
        with open(args.out, "w", encoding="ascii") as fh:
            fh.write(b64 + "\n")
        print(f"# wrote paste code -> {args.out}", file=sys.stderr)
    if args.binary:
        bp.write(args.binary)
        print(f"# wrote binary -> {args.binary} ({len(data)} bytes)", file=sys.stderr)
    if args.quiet:
        return 0
    print(base64.b64encode(data).decode())
    return 0


# --------------------------------------------------------------------------- #
# check
# --------------------------------------------------------------------------- #

def _report(label: str, findings: list) -> int:
    print(f"=== {label}")
    for f in findings:
        print(f)
    errs = [f for f in findings if f.sev in ("ERR", "SUSPECT")]
    if not findings:
        print("  no issues found")
    print(f"  -> {len(errs)} error/suspect, "
          f"{len([f for f in findings if f.sev == 'WARN'])} warn")
    print()
    return 1 if errs else 0


def _cost(lines: list[str], links: list[str] | None = None) -> None:
    """Print the reachability / loop-bound / instruction-cost summary."""
    stmts = [(i, _check.strip_comment(l)) for i, l in enumerate(lines)
             if _check.strip_comment(l)]
    print(_check.cost_report(stmts, links))
    print()


def cmd_check(args) -> int:
    rc = 0
    for p in args.files:
        with open(p, encoding="utf-8") as fh:
            lines = fh.read().split("\n")
        rc |= _report(p, _check.analyse(lines))
        if args.cost:
            _cost(lines)
    for p in args.msch:
        sch = msch.parse_file(p)
        for t in sch.logic_tiles():
            assert t.logic is not None
            lines = t.logic.code.split("\n")
            names = [l.name for l in t.logic.links]
            rc |= _report(f"{p} [{t.block} @({t.x},{t.y})]",
                          _check.analyse(lines, names))
            if args.cost:
                _cost(lines, names)
    return rc


# --------------------------------------------------------------------------- #
# ir -- structural / dataflow view
# --------------------------------------------------------------------------- #

# Names authors use purely as in-editor annotations. The game really does
# execute `set // foo` (only `#` starts a comment -- LParser.java:98-99), so
# these are technically dead stores, but reporting them is pure noise.
_ANNOTATION = re.compile(r"^[^A-Za-z0-9_@\"]*$")

# A def that is *forced by syntax*: these statements have several output
# slots and the author must name every one, so an unread slot is not a
# mistake, it is unavoidable. Measured over the corpus: 0.267/block for
# `ulocate` alone -- reporting those would bury the real findings.
_SLOT_FORCED = frozenset({
    "ulocate", "ucontrol", "radar", "uradar", "getlink", "getblock",
    "lookup", "weathersense", "spawn", "bullet", "status",
})

# `set x 3` with nothing reading x is how mlog authors "declare" a variable
# or leave a note. 0.99 per block across the corpus, so hidden by default.
_LITERAL = re.compile(r"^(?:-?\d+(?:\.\d+)?|true|false|@\S+|\"[^\"]*\")$")

# A *fullwidth punctuation* character inside a name is nearly always a typo'd
# `!` or `(` typed with a Chinese IME, and it silently creates a brand-new
# variable (`cy！` vs `cy!`). Pure Chinese names like `关闭时长` are perfectly
# legitimate, so the test is the fullwidth punctuation block only -- not
# "non-ASCII".
_FULLWIDTH = re.compile(
    "[\uff01-\uff0f\uff1a-\uff20\uff3b-\uff40\uff5b-\uff5e\u3000-\u303f]")


def _text(t) -> str:
    """A token's text, whichever shape `mlogir` hands us (Tok or str)."""
    return getattr(t, "text", t)


def _ir_tier(prog, i: int, v: str, kind: str) -> str:
    """`reported`, `slot` (forced by syntax), `declaration` or `annotation`."""
    # A name made only of punctuation (`//`, `--`, `===`) is a note the author
    # typed into the code, taken as a variable name because mlog has no
    # end-of-line comment (only `#` starts one, `LParser.java:98-99`). 222 of
    # these across the corpus -- the single largest noise source after `set`.
    if _ANNOTATION.match(v):
        return "annotation"
    if kind == "overwritten":
        return "reported"
    s = prog.stmts[i]
    if s.mnemonic in _SLOT_FORCED:
        return "slot"
    if s.mnemonic == "set" and all(_LITERAL.match(_text(a))
                                   for a in s.args[1:]):
        return "declaration"
    return "reported"


def _ir_report(label: str, lines: list[str], show_all: bool = False) -> int:
    prog = _ir.parse(lines)
    if not len(prog):
        return 0
    dead = prog.dead()
    graded = [(i, v, k) for i, v, k in prog.classify_dead_stores()
              if not _ANNOTATION.match(v)]
    tiers = [(i, v, k, _ir_tier(prog, i, v, k)) for i, v, k in graded]
    shown = [t for t in tiers if show_all or t[3] == "reported"]
    hidden: dict[str, int] = {}
    for t in tiers:
        if t not in shown:
            hidden[t[3]] = hidden.get(t[3], 0) + 1

    reads = {v for s in prog.stmts for v in s.uses}
    writes = {v for s in prog.stmts for v in s.defs}
    ops: dict[str, int] = {}
    for s in prog.stmts:
        ops[s.mnemonic] = ops.get(s.mnemonic, 0) + 1

    print(f"=== {label}")
    print(f"  statements      : {len(prog)}"
          + (f"   ({len(dead)} unreachable)" if dead else ""))
    print("  unknown         : "
          + (", ".join(sorted(prog.unknown_mnemonics)) or "none"))
    print(f"  variables       : {len(reads)} read, {len(writes)} written")
    if dead:
        print(f"  UNREACHABLE     : {len(dead)} statement(s) can never run: "
              + ", ".join(f"L{prog.stmts[i].line}" for i in dead[:12])
              + (" ..." if len(dead) > 12 else ""))
    if shown:
        print(f"  DEAD STORES     : {len(shown)} worth a look:")
        for i, v, kind, _tier in shown[:20]:
            why = ("value overwritten before any read"
                   if kind == "overwritten" else "computed, never read")
            print(f"      L{prog.stmts[i].line:<5} {v:<22} {why}")
            print(f"      {'':<5} {'':<22} {prog.stmts[i].raw.strip()[:70]}")
        if len(shown) > 20:
            print(f"      ... and {len(shown) - 20} more")
    else:
        print("  dead stores     : none")
    if hidden:
        bits = []
        if hidden.get("slot"):
            bits.append(f"{hidden['slot']} forced output slot(s)")
        if hidden.get("declaration"):
            bits.append(f"{hidden['declaration']} literal declaration(s)")
        print("  (hidden)        : " + ", ".join(bits)
              + "   -- rerun with --all to list them")
    weird: dict[str, list[int]] = {}
    for s in prog.stmts:
        for v in sorted(s.defs | s.uses):
            if v.startswith("@") or not _FULLWIDTH.search(v):
                continue
            weird.setdefault(v, []).append(s.line)
    if weird:
        print("  ODD NAMES       : fullwidth punctuation in a variable name "
              "(usually an IME typo, which silently "
              "creates a different variable):")
        for v, lns in list(weird.items())[:8]:
            print(f"      {v:<22} at "
                  + ", ".join(f"L{n}" for n in lns[:6])
                  + (" ..." if len(lns) > 6 else ""))
    print("  opcodes         : "
          + ", ".join(f"{k}x{v}" for k, v in
                      sorted(ops.items(), key=lambda kv: -kv[1])[:10]))
    print()
    return 0


def cmd_ir(args) -> int:
    rc = 0
    show_all = bool(getattr(args, "all", False))
    for p in args.files:
        with open(p, encoding="utf-8") as fh:
            rc |= _ir_report(p, fh.read().split("\n"), show_all)
    for p in args.msch:
        sch = msch.parse_file(p)
        for t in sch.logic_tiles():
            assert t.logic is not None
            rc |= _ir_report(f"{p} [{t.block} @({t.x},{t.y})]",
                             t.logic.code.split("\n"), show_all)
    return rc


# --------------------------------------------------------------------------- #
# id / cmd reference
# --------------------------------------------------------------------------- #

def cmd_id(args) -> int:
    if args.name:
        hits = [(k, v) for k, v in BLOCK_IDS.items() if args.name.lower() in v.lower()]
        if not hits:
            print(f"no block matching {args.name!r} in the id table")
            return 1
        for k, v in sorted(hits, key=lambda kv: int(kv[0])):
            print(f"  id={k:>4}  size={_gen.block_size(v):<2}  {v}")
        return 0

    print(f"{len(BLOCK_IDS)} blocks known (vanilla id table)")
    print()
    print("id / size / name")
    for k in sorted(BLOCK_IDS, key=int):
        v = BLOCK_IDS[k]
        print(f"  {k:>4}  {_gen.block_size(v):<2}  {v}")
    return 0


def cmd_item(args) -> int:
    """Item content ids, plus decoding of the common packed-config idiom."""
    if args.unpack:
        # The "portable config" idiom seen in the wild:
        #   data = status * 1e8 + outputID * 1e6 + inputMask
        # Decoding outputID is only valid when status == 0, because
        # idiv(data, 1e6) folds status into the quotient.
        data = int(args.unpack)
        status, rest = divmod(data, 1_000_000_000)
        output_id, mask = divmod(rest, 1_000_000)
        print(f"packed  : {data}  (0x{data:X})")
        print(f"status  : {status}")
        out_name = ITEM_IDS.get(str(output_id), f"<unknown id {output_id}>")
        print(f"output  : {output_id} = {out_name}"
              + ("   ⚠ status != 0: this field is NOT just the output id"
                 if status else ""))
        bits = [i for i in range(32) if mask >> i & 1]
        print(f"mask    : {mask}  (0x{mask:X}) -> bit positions {bits}")
        for b in bits:
            print(f"  bit {b:>2} -> {ITEM_IDS.get(str(b), f'<unknown id {b}>')}")
        if mask >= 1_000_000:
            print("  ⚠ mask overflows the 6-digit field")
        if max(bits, default=-1) >= 20:
            print(f"  ⚠ bit {max(bits)} >= 20: outside what this 20-bit slot "
                  f"holds safely")
        return 0

    if args.name:
        q = args.name.strip().lower()
        hits = []
        for k, v in ITEM_IDS.items():
            if q in v.lower() or q == k:
                hits.append((int(k), v))
        if not hits:
            print(f"no item matching {args.name!r} in the id table")
            return 1
        for i, v in sorted(hits):
            print(f"  id={i:>3}  {v}")
        return 0

    print(f"{len(ITEM_IDS)} items known (vanilla id = Items.java construction order)")
    print()
    for k in sorted(ITEM_IDS, key=int):
        print(f"  {k:>3}  {ITEM_IDS[k]}")
    print()
    print("tip: mlog.py item --unpack <number>  decodes "
          "status*1e8 + outputID*1e6 + inputMask")
    return 0


def cmd_cmd(args) -> int:
    if not CMD_INDEX:
        print("cmd_index.json missing", file=sys.stderr)
        return 1
    pat = (args.pattern or "").lower()
    shown = 0
    for c in CMD_INDEX:
        blob = (c.get("title", "") + " " + c.get("format", "")).lower()
        if pat and pat not in blob:
            continue
        shown += 1
        print(f"{c.get('num','?'):>3}  {c.get('title','')}")
        fmt = (c.get("format") or "").strip()
        if fmt:
            for line in fmt.split("\n")[:3]:
                print(f"        {line}")
        for note in (c.get("notes") or [])[:3]:
            print(f"        - {note[:110]}")
        print()
    if not shown:
        print(f"no command matching {pat!r}")
        return 1
    return 0


# --------------------------------------------------------------------------- #

def main() -> int:
    ap = argparse.ArgumentParser(
        prog="mlog", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("parse", help="dump a .msch blueprint")
    p.add_argument("file")
    p.set_defaults(fn=cmd_parse)

    p = sub.add_parser("gen", help="build a blueprint / paste code from mlog")
    p.add_argument("source", nargs="?", help=".mlog file (default: stdin)")
    p.add_argument("--logic", help="inline mlog code")
    p.add_argument("--name", default="blueprint")
    p.add_argument("--description", default="")
    p.add_argument("--label", action="append", default=[])
    p.add_argument("--block", default="micro-processor")
    p.add_argument("--at", default="0,0", help="processor center x,y")
    p.add_argument("--rotation", type=int, default=0)
    p.add_argument("--link", action="append", default=[],
                   help="name@dx,dy (relative to the processor)")
    p.add_argument("--with-block", action="append", default=[],
                   help="block@dx,dy[=contentId] -- CENTER coords; also places the link target")
    p.add_argument("--auto-link", action="store_true",
                   help="report the game link-name for each --with-block")
    p.add_argument("--out", help="write the paste code (base64) to this file")
    p.add_argument("--binary", help="write a .msch binary to this path")
    p.add_argument("--quiet", action="store_true", help="do not print the paste code")
    p.set_defaults(fn=cmd_gen)

    p = sub.add_parser("check", help="static analysis of mlog")
    p.add_argument("files", nargs="*", help=".mlog files")
    p.add_argument("--msch", action="append", default=[],
                   help="also check logic inside a .msch")
    p.add_argument("--cost", action="store_true",
                   help="also report statement count, unreachable code, loop "
                        "bounds and worst-case instruction cost per cycle")
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser("ir", help="structural view: dead code, dead stores")
    p.add_argument("files", nargs="*", metavar="logic.mlog")
    p.add_argument("--msch", action="append", default=[],
                   help="take the logic from a .msch instead")
    p.add_argument("--all", action="store_true",
                   help="also list forced output slots and literal "
                        "declarations (noisy: ~1.2 per block)")
    p.set_defaults(fn=cmd_ir)

    p = sub.add_parser("id", help="look up block content ids / sizes")
    p.add_argument("name", nargs="?", help="substring; omit to list all")
    p.set_defaults(fn=cmd_id)

    p = sub.add_parser("item", help="item content ids; decode packed configs")
    p.add_argument("name", nargs="?", help="name or id; omit to list all")
    p.add_argument("--unpack", metavar="N",
                   help="decode status*1e8 + outputID*1e6 + inputMask")
    p.set_defaults(fn=cmd_item)

    p = sub.add_parser("cmd", help="mlog instruction reference")
    p.add_argument("pattern", nargs="?", help="substring filter")
    p.set_defaults(fn=cmd_cmd)

    p = sub.add_parser("selftest", help="round-trip every blueprint in the game dir")
    p.set_defaults(fn=lambda a: _gen.selftest())

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
