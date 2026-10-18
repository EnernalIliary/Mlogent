"""逐条审计助手 —— 把「一堆发现」变成「你可以一条条判的清单」。

背景：分析器给出的是**行级**发现，一次几百上千条，读不了也没法回话。这个工具把
它们压成**可审的行**（每条规则在同一份程序里只留一条，见 `rule_audit.py --rows`），
给每行一个稳定 id，然后让你用四个词给它定案：

    ok      规则说得对（这是真问题）
    bad     规则说错了（这是噪声/误报）
    unsure  我看不出来（保留）
    skip    不想看（等同于没判）

判完 `stats` 会按规则算出你的准确率，`rule_capture.py` 用它决定该降级还是该删。

用法::

    python tools/review.py build --dir out/maps          # 扫一遍，生成 out/audit_rows.json
    python tools/review.py list --unjudged --limit 20    # 看还没判的
    python tools/review.py show 3f9c1a2b04               # 看这条所在的完整程序（标出该行）
    python tools/review.py bad 3f9c1a2b04 --note "mod 里的自定义方块"
    python tools/review.py stats                         # 每条规则你判了多少、错了几条
    python tools/review.py export                        # out/audit.md，按规则分组给人看
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mindustry-blueprint" / "tools"))

import map_logic as ML  # noqa: E402
import mlogcheck as _check  # noqa: E402

ROWS = ROOT / "out" / "audit_rows.json"
VERDICTS = ROOT / "out" / "verdicts.csv"
SAVE_DIR = ROOT / "out" / "maps"

VERDICT_WORDS = {"ok": "ok", "bad": "bad", "unsure": "unsure", "skip": "skip"}


def load_rows() -> list[dict]:
    if not ROWS.exists():
        sys.exit(f"no {ROWS}; run: python tools/review.py build")
    return json.loads(ROWS.read_text(encoding="utf-8"))


def load_verdicts() -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not VERDICTS.exists():
        return out
    with VERDICTS.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            out[row["id"]] = row
    return out


def save_verdict(fid: str, verdict: str, note: str) -> None:
    new = not VERDICTS.exists()
    VERDICTS.parent.mkdir(parents=True, exist_ok=True)
    with VERDICTS.open("a", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["id", "verdict", "note", "when"])
        w.writerow([fid, verdict, note, time.strftime("%Y-%m-%d %H:%M")])


def find_row(rows: list[dict], fid: str) -> dict:
    for r in rows:
        if r["id"] == fid:
            return r
    # also allow an unambiguous prefix
    hits = [r for r in rows if r["id"].startswith(fid)]
    if len(hits) == 1:
        return hits[0]
    sys.exit(f"no such row: {fid}" + (f" ({len(hits)} prefixes match)" if hits else ""))


def cmd_build(args) -> int:
    import rule_audit

    argv = ["--dir", args.dir, "--rows", str(ROWS),
            "--md", str(ROOT / "out" / "rule_audit_maps.md"),
            "--json", str(ROOT / "out" / "rule_audit_maps.json")]
    if args.serial:
        argv.append("--serial")
    return rule_audit.main(argv)


def cmd_list(args) -> int:
    rows = load_rows()
    verd = load_verdicts()
    if args.rule:
        rows = [r for r in rows if args.rule.lower() in r["rule"].lower()]
    if args.unjudged:
        rows = [r for r in rows if r["id"] not in verd]
    if not rows:
        print("nothing to show")
        return 0
    per_rule = Counter(r["rule"] for r in rows)
    print(f"{len(rows)} row(s) across {len(per_rule)} rule(s)\n")
    print(f"{'id':<12} {'rule':<38} {'sev':<7} {'where':<34} line")
    for r in rows[: args.limit or len(rows)]:
        where = f"{Path(r['file']).stem[:22]}:{r['x']},{r['y']}"
        mark = "  " + verd[r["id"]]["verdict"] if r["id"] in verd else ""
        print(f"{r['id']:<12} {r['rule'][:38]:<38} {r['sev']:<7} {where:<34} "
              f"{r['line']}{mark}")
    if args.limit and len(rows) > args.limit:
        print(f"... {len(rows) - args.limit} more")
    return 0


def _load_code(row: dict) -> str:
    path = SAVE_DIR / row["file"]
    if not path.exists():
        sys.exit(f"save not cached: {path}")
    info = ML.read_save(path)
    for t in info.get("logic") or []:
        if t["x"] == row["x"] and t["y"] == row["y"]:
            return (t.get("code") or "")
    sys.exit(f"no processor at ({row['x']},{row['y']}) in {row['file']}")


def _blueprint_for(row: dict, code: str) -> str:
    """A one-processor schematic holding exactly this program, as a paste-able code.

    The point is that judging a finding should not require opening the save. Paste the
    code in-game (or open it in the editor) and the processor is right there, with the
    variable list the user reads anyway.

    Links are NOT re-created: a row about a missing link is about the name being absent,
    and inventing a target would hide that. The names still appear in the code.
    """
    import base64

    import mschgen as G

    name = f"audit-{row['id']}"[:40]
    desc = f"{row['rule']} @ {Path(row['file']).stem}:{row['x']},{row['y']} L{row['line']}"
    bp = G.Blueprint(name, desc, [])
    bp.add_logic(code, 0, 0, "micro-processor", 0, [])
    return base64.b64encode(bp.build()).decode("ascii")


def cmd_code(args) -> int:
    row = find_row(load_rows(), args.id)
    code = _load_code(row)
    b64 = _blueprint_for(row, code)
    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        import base64

        path.write_bytes(base64.b64decode(b64))
        print(f"wrote {path}  ({len(b64)} chars of code)")
    print(b64)
    return 0


def cmd_codes(args) -> int:
    rows = load_rows()
    verd = load_verdicts()
    if args.rule:
        rows = [r for r in rows if args.rule.lower() in r["rule"].lower()]
    if args.unjudged:
        rows = [r for r in rows if r["id"] not in verd]
    if args.limit:
        rows = rows[: args.limit]
    out_dir = ROOT / "out" / "review"
    out_dir.mkdir(parents=True, exist_ok=True)
    md = [f"# 可粘贴的蓝图码（{len(rows)} 条）", ""]
    md.append("每条一个微处理器，源码就是那张图里那台处理器的原文。")
    md.append("粘贴进游戏即可在编辑器里看变量列表；`out/review/*.msch` 也可以直接丢进")
    md.append("存档目录的 `schematics/` 让它在游戏里出现。")
    md.append("")
    for r in rows:
        code = _load_code(r)
        b64 = _blueprint_for(r, code)
        (out_dir / f"{r['id']}.msch").write_bytes(__import__("base64").b64decode(b64))
        md.append(f"## `{r['id']}` — {r['rule']}")
        md.append("")
        md.append(f"- 出处：`{Path(r['file']).stem}` ({r['x']},{r['y']}) {r.get('block')}")
        md.append(f"- 第 {r['line']} 行：`{(r['code'] or '').strip()}`")
        md.append(f"- 判定行：`{r['msg'][:180]}`")
        md.append("")
        md.append("```")
        md.append(b64)
        md.append("```")
        md.append("")
    path = ROOT / "out" / "audit_codes.md"
    path.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"wrote {path} and {len(rows)} .msch file(s) in {out_dir}")
    return 0


def cmd_install(args) -> int:
    """Drop the review blueprints into the game's schematic folder."""
    rows = load_rows()
    verd = load_verdicts()
    if args.rule:
        rows = [r for r in rows if args.rule.lower() in r["rule"].lower()]
    if args.unjudged:
        rows = [r for r in rows if r["id"] not in verd]
    if args.limit:
        rows = rows[: args.limit]
    import base64

    import mschgen as G

    target = Path(G.default_schematics_dir() or "")
    if not target or not target.is_dir():
        sys.exit(f"schematic folder not found: {target}")
    target = target / "audit"
    target.mkdir(parents=True, exist_ok=True)
    n = 0
    for r in rows:
        b64 = _blueprint_for(r, _load_code(r))
        (target / f"audit-{r['id']}.msch").write_bytes(base64.b64decode(b64))
        n += 1
    print(f"installed {n} blueprint(s) into {target}")
    return 0


def cmd_show(args) -> int:
    row = find_row(load_rows(), args.id)
    code = _load_code(row)
    line = int(row["line"])
    print(f"rule  : {row['rule']}  [{row['sev']}]")
    print(f"claim : {row['msg'][:160]}")
    print(f"where : {row['file']} ({row['x']},{row['y']}) {row.get('block')}  line {line}")
    print()
    lines = code.splitlines()
    # `line` is a STATEMENT index -- the number you would type into a `jump`.
    # Map it to the raw line so the window can show surrounding text, then label
    # every printed row with its statement index so the two agree.
    stmts = _check.prepare(lines)
    idx_of = {ln + 1: k for k, (ln, _c) in enumerate(stmts)}
    if 0 <= line < len(stmts):
        raw = stmts[line][0] + 1
    else:
        raw = max(1, min(len(lines), line + 1))
    lo = max(1, raw - args.context)
    hi = min(len(lines), raw + args.context)
    for i in range(lo, hi + 1):
        k = idx_of.get(i)
        mark = ">>>>" if k == line else "    "
        print(f"{mark} {k if k is not None else '-':>4} | {lines[i - 1]}")
    verdict = load_verdicts().get(row["id"])
    print()
    if verdict:
        print(f"verdict: {verdict['verdict']}  ({verdict.get('note') or 'no note'})")
    else:
        print("verdict: (none)  --  ok / bad / unsure / skip")
    return 0


def cmd_verdict(args, word: str) -> int:
    row = find_row(load_rows(), args.id)
    save_verdict(row["id"], word, args.note or "")
    print(f"{row['id']} -> {word}" + (f"  ({args.note})" if args.note else ""))
    return 0


def cmd_stats(args) -> int:
    rows = load_rows()
    verd = load_verdicts()
    by_rule: dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        v = verd.get(r["id"])
        by_rule[r["rule"]][v["verdict"] if v else "unjudged"] += 1
    print(f"{'rule':<40} {'rows':>5} {'ok':>4} {'bad':>4} {'unsure':>7} {'left':>5}  verdict")
    for rule, c in sorted(by_rule.items(), key=lambda kv: -kv[1]["rows"]):
        judged = c["ok"] + c["bad"]
        if judged == 0:
            tail = "no verdict yet"
        elif c["bad"] == 0:
            tail = "100% right so far"
        else:
            tail = f"{c['ok'] / judged * 100:.0f}% right"
        print(f"{rule[:40]:<40} {c['rows']:>5} {c['ok']:>4} {c['bad']:>4} "
              f"{c['unsure']:>7} {c['unjudged']:>5}  {tail}")
    total = Counter(v["verdict"] for v in verd.values())
    print(f"\njudged {sum(total.values())} / {len(rows)} rows  "
          f"(ok {total['ok']}, bad {total['bad']}, unsure {total['unsure']}, skip {total['skip']})")
    return 0


def cmd_export(args) -> int:
    rows = load_rows()
    verd = load_verdicts()
    by_rule: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_rule[r["rule"]].append(r)
    out = [f"# 逐条待审清单（{len(rows)} 条）", ""]
    out.append("`python tools/review.py show <id>` 看上下文；`ok`/`bad`/`unsure` 判它。")
    out.append("")
    for rule, rs in sorted(by_rule.items(), key=lambda kv: -len(kv[1])):
        c = Counter(verd[r["id"]]["verdict"] for r in rs if r["id"] in verd)
        mark = ""
        if c["bad"] and not c["ok"]:
            mark = "  ← **你判的全是误报，考虑降级或删除**"
        out.append(f"## `{rule}` — {len(rs)} 条{mark}")
        out.append("")
        out.append("| id | 级别 | 位置 | 行 | 源码 | 判定 |")
        out.append("|---|---|---|---|---|---|")
        for r in rs:
            v = verd.get(r["id"])
            code = (r["code"] or "").replace("|", "\\|")[:70]
            out.append(f"| `{r['id']}` | {r['sev']} | {Path(r['file']).stem}:{r['x']},{r['y']} "
                       f"| {r['line']} | `{code}` | {v['verdict'] if v else ''} |")
        out.append("")
        out.append(f"> {rs[0]['msg'][:220]}")
        out.append("")
    path = ROOT / "out" / "audit.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="scan a folder and write out/audit_rows.json")
    b.add_argument("--dir", default=str(SAVE_DIR))
    b.add_argument("--serial", action="store_true")
    b.set_defaults(fn=cmd_build)

    ls = sub.add_parser("list", help="table of rows")
    ls.add_argument("--rule", default="")
    ls.add_argument("--unjudged", action="store_true")
    ls.add_argument("--limit", type=int, default=0)
    ls.set_defaults(fn=cmd_list)

    sh = sub.add_parser("show", help="show one row with context")
    sh.add_argument("id")
    sh.add_argument("--context", type=int, default=6)
    sh.set_defaults(fn=cmd_show)

    cd = sub.add_parser("code", help="print a paste-able blueprint code holding this program")
    cd.add_argument("id")
    cd.add_argument("--out", default="", help="also write the .msch file here")
    cd.set_defaults(fn=cmd_code)

    cs = sub.add_parser("codes", help="write out/audit_codes.md + out/review/*.msch")
    cs.add_argument("--rule", default="")
    cs.add_argument("--unjudged", action="store_true")
    cs.add_argument("--limit", type=int, default=0)
    cs.set_defaults(fn=cmd_codes)

    ins = sub.add_parser("install", help="drop the blueprints into the game's schematics/audit")
    ins.add_argument("--rule", default="")
    ins.add_argument("--unjudged", action="store_true")
    ins.add_argument("--limit", type=int, default=0)
    ins.set_defaults(fn=cmd_install)

    for word in VERDICT_WORDS:
        vp = sub.add_parser(word, help=f"mark a row as {word}")
        vp.add_argument("id")
        vp.add_argument("--note", default="")
        vp.set_defaults(fn=lambda a, w=word: cmd_verdict(a, w))

    st = sub.add_parser("stats", help="per-rule verdict tally")
    st.set_defaults(fn=cmd_stats)

    ex = sub.add_parser("export", help="write out/audit.md")
    ex.set_defaults(fn=cmd_export)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
