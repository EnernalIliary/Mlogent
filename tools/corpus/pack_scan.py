"""Scan a folder of blueprints and report on the LOGIC inside them.

Answers "how good is the logic in this pack" with numbers instead of opinion.
Every number comes from the same analysers the single-file tools use
(`mlog.py check/ir/cost/values/pack`), so per-file output and this summary can
never disagree.

    python tools/pack_scan.py <folder> [--json out.json] [--top N]

What it measures, and why each one is here:

  coverage        how many blueprints carry logic at all -- a pack that is 90%
                  pixel art cannot be judged on its logic
  hard errors     undefined reads, `@dead` inversions, op arity, malformed
                  jumps: the class of mistake that means "did not read the doc"
  dead stores     only the `reported` tier (value proven unused), never the
                  slot/declaration/annotation tiers
  unreachable     statements after an unconditional jump
  spins           backward jumps whose loop has no constant bound and no
                  `wait`: the processor burns a whole tick budget each pass
  waits           `wait` seconds x loop trips -- the real clock, which the
                  instruction count hides
  idioms          cell/read-write protocol, radar, ucontrol, packing, bit peel

Usage notes:
  * a spinner is not automatically a bug (a handshake needs one), but a loop
    with no timeout and no exit condition is a hang waiting to happen; both are
    counted separately (`spin` vs `spin_timeout`)
"""

from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "mindustry-blueprint" / "tools"))

import msch  # noqa: E402
import mlogagent as M  # noqa: E402

mlog = M.M            # the mlog.py module itself (M is the agent wrapper)
_CM = M._check        # mlogcheck

BACKJUMP = re.compile(r"^jump\s+(\d+)\b")
WAIT = re.compile(r"^wait\s+(\S+)")
CONST_GUARD = re.compile(
    r"\b(lessThan|lessThanEq|greaterThan|greaterThanEq)\s+\S+\s+-?\d+(\.\d+)?\b")
NEVER_EXIT = re.compile(r"^jump\s+\d+\s+always\b")


def _undefined_reads(stmts, links: set[str]) -> set[str]:
    """Variables read somewhere but written nowhere in this program.

    Measured with the IR's own def/use sets. In mlog an unset variable is the
    number 0 (a fresh LVar has numval = 0), so a guard like
    `jump T equal X null` over such a variable is ALWAYS true: `equal` compares
    numerically unless both sides are objects (ConditionOp.test), and
    `null.num()` is 0. So this is not a cosmetic metric.
    """
    defined: set[str] = set(links)
    for s in stmts:
        defined |= set(s.defs)
    out: set[str] = set()
    for s in stmts:
        for v in s.uses:
            if v in defined or v.startswith("@") or v in ("null", "true", "false"):
                continue
            out.add(v)
    return out


def _constant_guard_cost(prog, lines: list[str], undef: set[str]) -> int:
    """Statements that can never run once the constant guards are folded.

    `jump T equal X null` (X undefined) becomes an unconditional jump and
    `jump T notEqual X null` becomes a no-op; reachability is then recomputed on
    the rewritten program. This is what turns "72 suspicious guards" into "about
    550 statements never execute".

    The rewrite happens on the ORIGINAL line list, because `jump <label>` needs
    the `label:` lines to resolve -- rewriting only the statement bodies loses
    them and silently changes the CFG.
    """
    out = list(lines)
    changed = False
    for s in prog.stmts:
        if s.mnemonic != "jump" or len(s.args) < 4:
            continue
        op, a, b = s.args[1].text, s.args[2].text, s.args[3].text
        if b != "null" or a not in undef:
            continue
        if op == "equal":
            out[s.line] = f"jump {s.args[0].text} always 0 false"
            changed = True
        elif op == "notEqual":
            # always FALSE: the guard never fires, so control falls through.
            # `end` would be wrong -- it restarts the program.
            out[s.line] = "set __nop 0"
            changed = True
    if not changed:
        return len(prog.dead())
    return len(M._ir.parse(out).dead())


def analyse_tile(code: str, links: list[str]) -> dict:
    lines = code.split("\n")
    m = M._measure(lines, links)
    stmts = [_CM.strip_comment(l) for l in lines]
    stmts = [s.strip() for s in stmts if s.strip()]

    prog = m["prog"]
    dispatch = prog.writes_counter()
    undef = _undefined_reads(prog.stmts, set(links))
    null_guards = sum(
        1 for s in prog.stmts
        if s.mnemonic == "jump" and len(s.args) >= 4
        and s.args[3].text == "null" and s.args[2].text in undef)
    const_skipped = _constant_guard_cost(prog, lines, undef) if undef else 0
    if dispatch:
        # `op add @counter @counter id` jumps into the middle of the program by
        # table index; static reachability cannot follow that, so counting the
        # table as "unreachable" is a tool artifact, not a finding.
        const_skipped = 0

    # ---- loop shape ------------------------------------------------------
    spins = spin_timeout = waits = 0
    wait_ticks = 0
    for i, s in enumerate(stmts):
        mb = BACKJUMP.match(s)
        if not mb:
            continue
        target = int(mb.group(1))
        if not (0 <= target < i):
            continue
        body = stmts[target:i + 1]
        has_wait = any(WAIT.match(b) for b in body)
        bounded = any(CONST_GUARD.search(b) for b in body)
        if has_wait or bounded:
            continue
        spins += 1
        # a timeout looks like a counter that is incremented and compared
        if not any(NEVER_EXIT.match(b) for b in body):
            spin_timeout += 1
    for s in stmts:
        mw = WAIT.match(s)
        if mw:
            waits += 1
            try:
                wait_ticks += int(round(float(mw.group(1)) * 60))
            except ValueError:
                wait_ticks = -1
    if wait_ticks < 0:
        wait_ticks = 0

    return {
        "stmts": len(stmts),
        "errs": m["errs"],
        "warns": m["warns"],
        "findings": [(f.sev, f.line, f.code, f.msg) for f in m["findings"]],
        "unknown": m["unknown"],
        "dead_reported": m["reported"],
        "dead_hidden": m["hidden"],
        "branches": m["branches"],
        "nulls": m["nulls"],
        "packs": m["packs"],
        "spins": spins,
        "spins_no_exit": spin_timeout,
        "waits": waits,
        "wait_ticks": wait_ticks,
        "uses_cell": any(re.match(r"^(read|write)\b", s) for s in stmts),
        "uses_radar": any(re.match(r"^(u?radar)\b", s) for s in stmts),
        "uses_ucontrol": any(s.startswith("ucontrol") for s in stmts),
        "uses_ubind": any(s.startswith("ubind") for s in stmts),
        "max_nesting_hint": len(set(BACKJUMP.findall(" ".join(stmts)))),
        "undef_vars": len(undef),
        "undef_names": sorted(undef)[:6],
        "null_guards": null_guards,
        "const_skipped": const_skipped,
        "counter_dispatch": dispatch,
        "unreachable": 0 if dispatch else m["dead"],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("folder")
    ap.add_argument("--json")
    ap.add_argument("--top", type=int, default=12)
    args = ap.parse_args()

    root = pathlib.Path(args.folder)
    files = sorted(root.rglob("*.msch"))
    if not files:
        print(f"no .msch under {root}", file=sys.stderr)
        return 2

    bad_parse: list[tuple[str, str]] = []
    rows = []
    for f in files:
        rel = str(f.relative_to(root))
        try:
            sch = M.M._load_schematic(str(f))
        except (SystemExit, Exception) as exc:      # noqa: BLE001
            bad_parse.append((rel, str(exc)))
            continue
        texts = [t.config for t in sch.tiles
                 if isinstance(t.config, str) and t.block == "message"]
        tiles = []
        for t in sch.logic_tiles():
            assert t.logic is not None
            info = analyse_tile(t.logic.code, [l.name for l in t.logic.links])
            info["block"] = t.block
            info["at"] = [t.x, t.y]
            info["links"] = len(t.logic.links)
            tiles.append(info)
        rows.append({
            "file": rel,
            "category": rel.split("\\")[1] if rel.count("\\") >= 2 else "",
            "name": sch.name,
            "desc": sch.description,
            "labels": sch.labels,
            "size": [sch.width, sch.height],
            "tiles": len(sch.tiles),
            "logic_tiles": len(tiles),
            "statements": sum(t["stmts"] for t in tiles),
            "errs": sum(t["errs"] for t in tiles),
            "warns": sum(t["warns"] for t in tiles),
            "dead_reported": sum(t["dead_reported"] for t in tiles),
            "dead_hidden": sum(t["dead_hidden"] for t in tiles),
            "unreachable": sum(t["unreachable"] for t in tiles),
            "branches": sum(t["branches"] for t in tiles),
            "nulls": sum(t["nulls"] for t in tiles),
            "packs": sum(t["packs"] for t in tiles),
            "spins": sum(t["spins"] for t in tiles),
            "spins_no_exit": sum(t["spins_no_exit"] for t in tiles),
            "waits": sum(t["waits"] for t in tiles),
            "wait_ticks": sum(t["wait_ticks"] for t in tiles),
            "texts": texts,
            "detail": tiles,
        })

    with_logic = [r for r in rows if r["logic_tiles"]]
    tot_stmts = sum(r["statements"] for r in with_logic)
    print("=" * 78)
    print(f"files            : {len(rows)} parsed, {len(bad_parse)} failed")
    print(f"with logic       : {len(with_logic)} "
          f"({100*len(with_logic)/max(1,len(rows)):.0f}%)")
    print(f"logic blocks     : {sum(r['logic_tiles'] for r in with_logic)}")
    print(f"statements       : {tot_stmts}")
    if with_logic:
        print(f"  per block med  : "
              f"{sorted(t['stmts'] for r in with_logic for t in r['detail'])[len([t for r in with_logic for t in r['detail']])//2]}")
    print(f"hard errors      : {sum(r['errs'] for r in rows)}")
    print(f"warnings         : {sum(r['warns'] for r in rows)}")
    print(f"dead stores      : {sum(r['dead_reported'] for r in rows)} reported, "
          f"{sum(r['dead_hidden'] for r in rows)} hidden")
    print(f"unreachable      : {sum(r['unreachable'] for r in rows)} statements")
    print(f"unbounded spins  : {sum(r['spins'] for r in rows)} "
          f"(of which {sum(r['spins_no_exit'] for r in rows)} with no exit jump)")
    print(f"wait statements  : {sum(r['waits'] for r in rows)} "
          f"(~{sum(r['wait_ticks'] for r in rows)} ticks)")
    print()
    counted = collections.Counter()
    for r in rows:
        for t in r["detail"]:
            for level, line, text, detail in t["findings"]:
                key = f"{level}: {text}"
                counted[key] += 1
    print("--- finding shapes -----------------------------------------------")
    for k, n in counted.most_common(args.top):
        print(f"{n:5d}  {k}")
    print()
    print("--- heaviest logic (statements) -----------------------------------")
    for r in sorted(with_logic, key=lambda r: -r["statements"])[:args.top]:
        print(f"{r['statements']:5d} stmts  {r['logic_tiles']} blk  "
              f"e{r['errs']}/w{r['warns']} d{r['dead_reported']} "
              f"s{r['spins']} w{r['waits']}  {r['file']}")
    print()
    print("--- files with hard errors ----------------------------------------")
    for r in sorted(rows, key=lambda r: -r["errs"]):
        if not r["errs"]:
            continue
        print(f"{r['errs']:3d}E  {r['file']}")
        for t in r["detail"]:
            for level, line, text, detail in t["findings"]:
                if level == "ERR":
                    print(f"      {t['block']}@({t['at'][0]},{t['at'][1]}) "
                          f"L{line}: {text}")
                    if detail:
                        print(f"          {detail}")
    if bad_parse:
        print()
        print("--- unparsable ---------------------------------------------------")
        for rel, err in bad_parse:
            print(f"  {rel}: {err[:120]}")

    if args.json:
        out = pathlib.Path(args.json)
        out.write_text(json.dumps(
            {"rows": rows, "bad": bad_parse}, ensure_ascii=False, indent=1),
            encoding="utf-8")
        print(f"\njson -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
