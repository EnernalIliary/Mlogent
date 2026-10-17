#!/usr/bin/env python
"""
mlog.py -- Mindustry blueprint (.msch) toolkit: read, write, validate.

One entry point for everything this skill does.

Usage
-----
  python mlog.py parse  <file.msch>            # dump a blueprint's blocks + logic
  python mlog.py text   <file.msch...> [--plain] # what the message block (信息板) says
  python mlog.py gen    <logic.mlog> [opts]    # build a .msch (or paste code)
  python mlog.py check  <logic.mlog | --msch F> # static analysis of mlog
  python mlog.py ir     <logic.mlog | --msch F> # CFG: unreachable code, dead stores
                                               #   (--all also shows forced output
                                               #    slots and literal declarations)
  python mlog.py values <logic.mlog | --msch F> # abstract values: constant branches,
                                               #   provable nulls (--trace VAR)
  python mlog.py pack   <logic.mlog | --msch F> # packed configs: field layout + how
                                               #   many ids still fit the low field
  python mlog.py id     [name]                 # block content ids / sizes
  python mlog.py item   [name] [--unpack N]    # item content ids / packed configs
  python mlog.py cmd    [pattern]              # mlog instruction reference
  python mlog.py explain <mnemonic> [sub]      # one instruction: syntax + which
                                               #   positions are read / written
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

  # "which argument of this instruction is the output?"
  python mlog.py explain ulocate
  python mlog.py explain op add

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
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import mlogcheck as _check          # noqa: E402
import mlogir as _ir                # noqa: E402
import mlogpack as _pk              # noqa: E402
import mlogval as _val              # noqa: E402
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
# loading: a blueprint can arrive in two shapes with the same suffix
# --------------------------------------------------------------------------- #

def _load_schematic(path: str):
    """Read a blueprint from either the binary .msch the game writes or the
    base64 text you copy off a blueprint site / the in-game clipboard. The
    magic tells them apart, so the suffix does not have to be trusted."""
    with open(path, "rb") as fh:
        raw = fh.read()
    if raw[:4] == b"msch":
        return msch.parse_bytes(raw)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SystemExit(
            f"!! {path}: not a .msch binary and not base64 text ({exc})")
    try:
        return msch.parse_base64(text)
    except Exception as exc:                      # noqa: BLE001 - report, don't trace
        raise SystemExit(f"!! {path}: not a .msch binary and not a base64 "
                         f"blueprint ({exc})")


# --------------------------------------------------------------------------- #
# parse
# --------------------------------------------------------------------------- #

def cmd_parse(args) -> int:
    sch = _load_schematic(args.file)
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

    # Message blocks (信息板) are where authors explain what the blueprint is
    # for -- far more often than in the description tag (360 of 626 files here
    # carry one, versus 92 with a non-empty description). Printing it next to
    # the block list is usually what makes a dump readable at all.
    if not getattr(args, "no_text", False):
        texts = [t for t in sch.tiles
                 if t.block in _STRING_BLOCKS and isinstance(t.config, str)
                 and t.config.strip()]
        if texts:
            print()
            print("=" * 70)
            for t in texts:
                raw = t.config or ""
                body = _plain(raw) if getattr(args, "plain", False) else raw
                if getattr(args, "strip", False):
                    body = "\n".join(l for l in body.split("\n") if l.strip())
                icons = len(_PUA.findall(raw))
                head = f"--- {t.block} @({t.x},{t.y})"
                if icons:
                    head += f"  [{icons} icon(s) in the private-use area]"
                print(head)
                print(body)
                print()

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
    print(_check.cost_report(_check.prepare(lines), links))
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
    # `stale-write` (written 2+ times, read nowhere) outranks the slot and
    # declaration tiers on purpose: a forced output slot written *once* is just
    # the syntax making you name a variable you don't need, but writing the
    # same slot twice and never reading it means the first write is provably
    # discarded -- the `found`/`found` bug in
    # 17十七硫幽灵四熔毁四油海啸组.msch, which the slot tier used to hide.
    if kind in ("overwritten", "stale-write"):
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
    printed_dead = [] if prog.writes_counter() else dead
    print(f"  statements      : {len(prog)}"
          + (f"   ({len(printed_dead)} unreachable)" if printed_dead else ""))
    print("  unknown         : "
          + (", ".join(sorted(prog.unknown_mnemonics)) or "none"))
    print(f"  variables       : {len(reads)} read, {len(writes)} written")
    if printed_dead:
        print(f"  UNREACHABLE     : {len(printed_dead)} statement(s) can never run: "
              + ", ".join(f"L{prog.stmts[i].line}" for i in printed_dead[:12])
              + (" ..." if len(printed_dead) > 12 else ""))
    elif dead and prog.writes_counter():
        print("  UNREACHABLE     : not reported -- this program writes @counter "
              "(dispatch table), so static reachability is meaningless")
    if shown:
        print(f"  DEAD STORES     : {len(shown)} worth a look:")
        for i, v, kind, _tier in shown[:20]:
            why = {"overwritten": "value overwritten before any read",
                   "stale-write": "written more than once, read nowhere -- "
                                  "every write after the first is wasted",
                   }.get(kind, "computed, never read")
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
        tiles = list(sch.logic_tiles())
        for t in tiles:
            assert t.logic is not None
            rc |= _ir_report(f"{p} [{t.block} @({t.x},{t.y})]",
                             t.logic.code.split("\n"), show_all)
        # Cross-processor `read`/`write` addresses a NAMED slot in another
        # processor, and that slot must already exist there. Needs the whole
        # schematic, so it cannot live inside the per-tile report.
        blocks = [(f"{p} [{t.block} @({t.x},{t.y})]", t.logic.code.split("\n"))
                  for t in tiles if t.logic is not None]
        for f in _check.cross_processor(blocks):
            print(f"[{f.sev}] L{f.line} {f.code}")
            print(f"          {f.msg}")
            rc |= 1 if f.sev == "ERR" else 0
    return rc


def _val_report(label: str, lines: list[str],
                traces: list[str] | None = None) -> int:
    prog = _ir.parse(lines)
    st = _val.analyze(prog)
    print(_val.format_report(label, prog, st))
    for v in traces or []:
        rows = _val.trace(prog, st, v)
        print(f"  -- trace {v} --")
        for r in rows:
            print(r)
        if not rows:
            print("      (never written)")
    return 0


def cmd_values(args) -> int:
    rc = 0
    traces = list(getattr(args, "trace", None) or [])
    for p in args.files:
        with open(p, encoding="utf-8") as fh:
            rc |= _val_report(p, fh.read().split("\n"), traces)
    for p in args.msch:
        sch = msch.parse_file(p)
        for t in sch.logic_tiles():
            assert t.logic is not None
            rc |= _val_report(f"{p} [{t.block} @({t.x},{t.y})]",
                              t.logic.code.split("\n"), traces)
    return rc


def cmd_pack(args) -> int:
    """Recognise packed-config encode/decode and report field capacity."""
    rc = 0
    item_count = len(ITEM_IDS) or None
    for p in args.files:
        with open(p, encoding="utf-8") as fh:
            lines = fh.read().split("\n")
        print(_pk.format_report(_ir.parse(lines), item_count=item_count,
                                label=p))
        rc = 0
    for p in args.msch:
        sch = msch.parse_file(p)
        for t in sch.logic_tiles():
            assert t.logic is not None
            print(_pk.format_report(
                _ir.parse(t.logic.code.split("\n")), item_count=item_count,
                label=f"{p} [{t.block} @({t.x},{t.y})]"))
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
# explain -- syntax from cmd_index.json merged with semantics from LExecutor.java
# --------------------------------------------------------------------------- #

SEMANTICS = _load_json("instr_semantics.json")
_INSTR = {k.lower(): (k, v)
          for k, v in (SEMANTICS.get("instructions") or {}).items()}
_DISAGREE = [d for d in ((SEMANTICS.get("docs_crosscheck") or {})
                         .get("disagreements") or []) if isinstance(d, dict)]


def _kv(label: str, text: str, indent: int = 13) -> None:
    """`  label   : text`, wrapped so continuation lines stay aligned."""
    print(textwrap.fill(str(text), width=94,
                        initial_indent=f"  {label:<{indent}} ",
                        subsequent_indent=" " * (indent + 4)))


def _slots(idxs, params) -> str:
    if not idxs:
        return "-"
    out = []
    for i in idxs:
        nm = params[i] if i < len(params) else f"arg{i}"
        out.append(f"{i}={nm}")
    return ", ".join(out)


def _bullet(text: str, indent: int = 18) -> None:
    print(textwrap.fill(str(text), width=94,
                        initial_indent=" " * indent + "- ",
                        subsequent_indent=" " * (indent + 2)))


def _explain_ops(args) -> int:
    meta = SEMANTICS.get("ops_meta") or {}
    ops = SEMANTICS.get("ops") or {}
    want = (args.sub or "").strip().lower()
    for k, v in meta.items():
        if k == "legacy_aliases":
            _kv("aliases", ", ".join(f"{a} -> {b}" for a, b in v.items()))
        else:
            _kv(k, v)
    print()
    print(f"  {'op':<15}{'n':>2}  {'symbol':<9} what it does")
    for name, spec in ops.items():
        if want and want not in name.lower():
            continue
        print(f"  {name:<15}{spec.get('operands', '?'):>2}  "
              f"{spec.get('symbol', ''):<9}")
    if want and not any(want in n.lower() for n in ops):
        print(f"  (no operator matching {args.sub!r})")
        return 1
    return 0


def cmd_explain(args) -> int:
    key = args.name.strip().lower()
    if key in ("op", "ops"):
        return _explain_ops(args)

    hit = _INSTR.get(key)

    def _mnemonic_of(c) -> str:
        """First token of the documented format, lowercased.

        Matching on the format rather than on the title matters, because some
        titles begin with a *different* instruction: `ucontrol getBlock ...`
        would otherwise be listed as documentation for `getblock`.
        """
        toks = (c.get("format") or "").strip().split()
        return toks[0].lower() if toks else ""

    docs = [c for c in CMD_INDEX if _mnemonic_of(c) == key]
    if not docs:                       # some sections have no format line
        docs = [c for c in CMD_INDEX
                if (c.get("title") or "").strip().lower().startswith(key)]
    if args.sub:
        s = args.sub.lower()
        docs = [c for c in docs if s in (c.get("title") or "").lower()
                or s in (c.get("format") or "").lower()]
    if hit is None and not docs:
        print(f"unknown instruction {args.name!r}", file=sys.stderr)
        print(f"  try: python mlog.py cmd {key}", file=sys.stderr)
        return 1

    print(f"=== {args.name}")
    params: list = []
    if hit:
        canon, spec = hit
        params = spec.get("params") or []
        arity = spec.get("arity")
        _kv("arity", f"{arity}   (statement indices run 1..{arity}; "
                     f"index 0 is the mnemonic itself)")
        _kv("text", " ".join([canon] + [f"<{p}>" for p in params]))
        toks = spec.get("tokens") or {}
        for i, p in enumerate(params):
            tok = toks.get(str(i))
            tail = f"    [fixed token: {tok}]" if tok else ""
            print(f"  {'params' if i == 0 else '':<13} {i}  {p:<12}{tail}")
        _kv("writes", _slots(spec.get("defs") or [], params))
        _kv("reads", _slots(spec.get("uses") or [], params))
        if spec.get("maybe_uses"):
            _kv("maybe reads", _slots(spec["maybe_uses"], params))
        if spec.get("defs_conditional"):
            _kv("cond. writes", _slots(spec["defs_conditional"], params))
        if spec.get("always_evaluated"):
            _kv("always eval.",
                "positions " + ", ".join(str(i) for i in
                                         spec["always_evaluated"]))
        if spec.get("note"):
            _kv("semantics", spec["note"])

        subs = spec.get("subcommands") or {}
        if subs:
            print(f"  {'subcommands':<13} {len(subs)}: {', '.join(subs)}")
            for nm, s in subs.items():
                if args.sub and args.sub.lower() != nm.lower():
                    continue
                print(f"  {'':<13} {nm:<10} reads {_slots(s.get('uses') or [], params)}"
                      f"   writes {_slots(s.get('defs') or [], params)}")
                if s.get("note"):
                    print(textwrap.fill(s["note"], width=94,
                                        initial_indent=" " * 16,
                                        subsequent_indent=" " * 16))

    for c in docs:
        print(f"  {'docs':<13} {c.get('num', '?')}  {c.get('title', '')}"
              f"   (cmd_index.json:{c.get('line', '?')})")
        fmt = [l.strip() for l in (c.get("format") or "").split("\n") if l.strip()]
        for n, line in enumerate(fmt):
            print(f"  {'format' if n == 0 else '':<13} {line}")
        for pname, pdesc in (c.get("params") or []):
            print(textwrap.fill(f"{pname} : {pdesc}", width=94,
                                initial_indent=" " * 18,
                                subsequent_indent=" " * 22))
        for note in (c.get("notes") or []):
            _bullet(note)

    for d in _DISAGREE:
        if (d.get("instruction") or "").lower() != key:
            continue
        print(f"  {'!! DOCS WRONG':<13} the doc above is not what the game parses")
        _kv("docs say", d.get("docs_format", "?"))
        _kv("actually", d.get("source_order", "?"))
        _kv("impact", d.get("impact", ""))
        _kv("evidence", d.get("evidence", ""))
    return 0


# --------------------------------------------------------------------------- #
# text: read what a message block (信息板) actually says
# --------------------------------------------------------------------------- #

_MARKUP = re.compile(r"\[[^\]]{1,24}\]")
# Mindustry's icon font lives in the Private Use Area; in a console it is
# unreadable noise, but stripping it silently would lose information -- so it is
# only removed by --plain, and reported by count.
_PUA = re.compile("[\ue000-\uf8ff]")
_STRING_BLOCKS = ("message", "world-message", "world-label")


def _plain(s: str) -> str:
    return _PUA.sub("", _MARKUP.sub("", s)).strip()


def cmd_text(args) -> int:
    files = list(args.files)
    rc = 0
    for path in files:
        try:
            sch = _load_schematic(path)
        except (SystemExit, OSError) as exc:
            print(str(exc) if not isinstance(exc, SystemExit) else exc,
                  file=sys.stderr)
            rc = 1
            continue
        hits = [t for t in sch.tiles
                if t.block in _STRING_BLOCKS and isinstance(t.config, str)]
        if not hits and not (args.all and sch.description):
            print(f"--- {path}: no message block")
            continue
        print("=" * 70)
        print(f"{path}  ({sch.name})")
        if args.all and sch.description:
            print("--- description ---")
            print(_plain(sch.description) if args.plain else sch.description)
        for t in hits:
            text = t.config or ""
            body = _plain(text) if args.plain else text
            icons = len(_PUA.findall(text))
            head = f"--- {t.block} @({t.x},{t.y})"
            if icons:
                head += f"  [{icons} icon(s) in the private-use area]"
            print(head)
            if args.strip:
                body = "\n".join(l for l in body.split("\n") if l.strip())
            print(body)
    return rc


# --------------------------------------------------------------------------- #

def main() -> int:
    ap = argparse.ArgumentParser(
        prog="mlog", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("parse", help="dump a .msch blueprint")
    p.add_argument("file")
    p.add_argument("--plain", action="store_true",
                   help="strip [colour] markup and private-use icon glyphs")
    p.add_argument("--strip", action="store_true",
                   help="drop blank lines from message text")
    p.add_argument("--no-text", action="store_true",
                   help="do not print message-block (信息板) contents")
    p.set_defaults(fn=cmd_parse)

    p = sub.add_parser("text", help="read message-block (信息板) contents")
    p.add_argument("files", nargs="+")
    p.add_argument("--plain", action="store_true",
                   help="strip [colour] markup and private-use icon glyphs")
    p.add_argument("--strip", action="store_true",
                   help="drop blank lines (markup kept unless --plain)")
    p.add_argument("--all", action="store_true",
                   help="also print the blueprint description")
    p.set_defaults(fn=cmd_text)

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

    p = sub.add_parser("values",
                       help="abstract values: constant branches, provable nulls")
    p.add_argument("files", nargs="*", metavar="logic.mlog")
    p.add_argument("--msch", action="append", default=[],
                   help="take the logic from a .msch instead")
    p.add_argument("--trace", action="append", metavar="VAR",
                   help="trace one variable (repeatable)")
    p.set_defaults(fn=cmd_values)

    p = sub.add_parser("pack",
                       help="packed configs: field layout + how many ids fit")
    p.add_argument("files", nargs="*", metavar="logic.mlog")
    p.add_argument("--msch", action="append", default=[],
                   help="take the logic from a .msch instead")
    p.set_defaults(fn=cmd_pack)

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

    p = sub.add_parser("explain", help="one instruction: syntax + what it reads/writes")
    p.add_argument("name", help="mnemonic, e.g. ulocate | op | select | getblock")
    p.add_argument("sub", nargs="?",
                   help="subcommand or operator filter, e.g. `explain ulocate ore`")
    p.set_defaults(fn=cmd_explain)

    p = sub.add_parser("selftest", help="round-trip every blueprint in the game dir")
    p.set_defaults(fn=lambda a: _gen.selftest())

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
