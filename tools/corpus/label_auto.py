"""Auto-tag schematics by content, and measure how well it agrees with the
hand-written labels.

Design: the labels are faceted, and almost every value turns out to be carried
by one or two block types (see out/label_lift.md). So instead of hand-writing
rules, learn `value -> blocks` from half the corpus and score it on the other
half. What survives that is the honest accuracy; what does not is a value that
really is a human judgement (品质, 系列, 数量).

    python tools/label_auto.py                 # learn + held-out report
    python tools/label_auto.py --suggest F.msch
    python tools/label_auto.py --apply F.msch --out DIR
"""
from __future__ import annotations

import collections
import hashlib
import json
import pathlib
import re
import struct
import sys
import zlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TOOLS = ROOT / "mindustry-blueprint" / "tools"
sys.path.insert(0, str(TOOLS))
import msch  # noqa: E402
import mlogir  # noqa: E402

MARK = re.compile(r"\[([^\]]*)\]")
PUA = "".join(chr(c) for c in range(0xE000, 0xF900))
CORPUS = pathlib.Path.home() / "AppData" / "Roaming" / "Mindustry" / "schematics"
RULES = TOOLS / "label_rules.json"

# values that are not a function of the blueprint's content
NOT_CONTENT = ({"ILI", "常用", "未分类或低效", "实用", "诗词"}
               | {str(i) for i in range(1, 10)}
               | {"10~19", "20~29", "极多"})

# A block present in more than this share of ALL schematics cannot tell labels
# apart: `micro-processor` is in every blueprint that carries logic, so
# "contains a micro-processor" would fire on almost the whole corpus.
UBIQUITOUS = 0.20
MIN_COVER = 0.75        # must appear in at least this share of the value's files
MIN_LIFT = 0.45         # and be this much more common there than elsewhere
MAX_SIGNS = 1   # these values are single-block; a second signature is always
                # co-occurring support (cryo-mixer, radar) and leaks everywhere

MIN_PRECISION = 0.70    # a rule may only speak if it earned this on held-out data


def split_label(label: str) -> tuple[str, str]:
    m = MARK.search(label)
    colour = m.group(1) if m else ""
    body = MARK.sub("", label)
    text = "".join(ch for ch in body if ch not in PUA).strip()
    return colour, text or label


def facts(sch) -> tuple[collections.Counter[str], set[str], int]:
    """-> (block census, logic token set, max single-block repeat)."""
    blocks = collections.Counter(t.block for t in sch.tiles)
    toks: set[str] = set()
    for t in sch.logic_tiles():
        for line in t.logic.code.split("\n"):
            body = mlogir.strip_comment(line).strip()
            if not body:
                continue
            toks.add(body.split()[0].lower())
            toks.update(w.lower() for w in body.split()[1:] if w.startswith("@"))
    return blocks, toks, max(blocks.values()) if blocks else 0


def load_corpus() -> list[tuple[str, set[str], collections.Counter[str], set[str], int]]:
    rows = []
    for p in sorted(CORPUS.glob("*.msch")):
        try:
            sch = msch.parse_file(str(p))
        except Exception:
            continue
        texts = {split_label(l)[1] for l in (sch.labels or [])}
        blocks, toks, biggest = facts(sch)
        rows.append((p.name, texts, blocks, toks, biggest))
    return rows


def train(rows) -> dict[str, dict]:
    """value -> {blocks: [...], tokens: [...], min_biggest: N}"""
    n = len(rows)
    base_b: collections.Counter[str] = collections.Counter()
    base_t: collections.Counter[str] = collections.Counter()
    for _, _, b, t, _ in rows:
        base_b.update(b.keys())
        base_t.update(t)
    values = sorted({v for _, texts, _, _, _ in rows for v in texts} - NOT_CONTENT)

    rules: dict[str, dict] = {}
    for v in values:
        sel = [r for r in rows if v in r[1]]
        if len(sel) < 5:
            continue
        cb: collections.Counter[str] = collections.Counter()
        ct: collections.Counter[str] = collections.Counter()
        for _, _, b, t, _ in sel:
            cb.update(b.keys())
            ct.update(t)
        # a block is a signature of this value if it shows up in most of its
        # files AND is rare elsewhere -- and it must not be a block that sits in
        # every blueprint anyway, or the rule fires on everything
        cand_b = [(cb[k] / len(sel) - base_b[k] / n, k) for k in cb
                  if cb[k] / len(sel) >= MIN_COVER
                  and base_b[k] / n <= UBIQUITOUS
                  and cb[k] / len(sel) - base_b[k] / n >= MIN_LIFT]
        cand_t = [(ct[k] / len(sel) - base_t[k] / n, k) for k in ct
                  if ct[k] / len(sel) >= MIN_COVER
                  and base_t[k] / n <= UBIQUITOUS
                  and ct[k] / len(sel) - base_t[k] / n >= MIN_LIFT]
        blocks = [k for _, k in sorted(cand_b, reverse=True)[:MAX_SIGNS]]
        # a block beats a token: the block is the thing, the token is often how
        # it is driven (radar -> 火控/力墙/雷光 all at once)
        toks = [] if blocks else [k for _, k in sorted(cand_t, reverse=True)[:MAX_SIGNS]]
        if blocks or toks:
            rules[v] = {"blocks": sorted(blocks), "tokens": sorted(toks),
                        "files": len(sel)}
    return rules


def predict(rule: dict, blocks, toks, biggest: int) -> bool:
    if any(b in blocks for b in rule["blocks"]):
        return True
    return any(t in toks for t in rule["tokens"])


def precision(rows, rules, half: str = "test") -> dict[str, float]:
    """Per-value precision on a held-out half. This is the number that decides
    whether a rule is allowed to speak: a suggestion the user has to reject is
    worse than no suggestion at all."""
    def split(name: str) -> int:
        return int(hashlib.sha1(name.encode("utf-8")).hexdigest()[:8], 16) % 2

    idx = 0 if half == "train" else 1
    tp: collections.Counter[str] = collections.Counter()
    fp: collections.Counter[str] = collections.Counter()
    for name, texts, blocks, toks, biggest in rows:
        if split(name) != idx:
            continue
        for v, rule in rules.items():
            if predict(rule, blocks, toks, biggest):
                if v in texts:
                    tp[v] += 1
                else:
                    fp[v] += 1
    return {v: (tp[v] / (tp[v] + fp[v]) if tp[v] + fp[v] else 0.0) for v in rules}


def evaluate(rows, rules, half: str) -> None:
    def split(name: str) -> int:
        return int(hashlib.sha1(name.encode("utf-8")).hexdigest()[:8], 16) % 2

    idx = 0 if half == "train" else 1
    tp = collections.Counter()
    fp = collections.Counter()
    fn = collections.Counter()
    for name, texts, blocks, toks, biggest in rows:
        if split(name) != idx:
            continue
        for v, rule in rules.items():
            got = predict(rule, blocks, toks, biggest)
            want = v in texts
            if got and want:
                tp[v] += 1
            elif got and not want:
                fp[v] += 1
            elif want and not got:
                fn[v] += 1

    print(f"\n## 留出集({half})上逐标签的表现\n")
    print("| 标签 | 命中 | 误报 | 漏报 | 精确率 | 召回率 |")
    print("|---|---|---|---|---|---|")
    tot_p = tot_r = 0
    for v in sorted(tp.keys() | fn.keys()):
        p = tp[v] / (tp[v] + fp[v]) if tp[v] + fp[v] else 0.0
        r = tp[v] / (tp[v] + fn[v]) if tp[v] + fn[v] else 0.0
        print(f"| {v} | {tp[v]} | {fp[v]} | {fn[v]} | {p:.0%} | {r:.0%} |")
        tot_p += p
        tot_r += r
    n = max(1, len(tp.keys() | fn.keys()))
    print(f"\n平均精确率 {tot_p/n:.0%}，平均召回率 {tot_r/n:.0%}（{n} 个标签）")


def suggest(paths: list[str], rules: dict, show_all: bool = False) -> None:
    for raw in paths:
        p = pathlib.Path(raw)
        sch = msch.parse_file(str(p))
        blocks, toks, biggest = facts(sch)
        have = {split_label(l)[1] for l in (sch.labels or [])}
        hits = sorted(v for v, r in rules.items() if predict(r, blocks, toks, biggest))
        # only speak when the rule earned it on the held-out half
        trusted = [v for v in hits if rules[v].get("precision", 0) >= MIN_PRECISION]
        weak = [v for v in hits if v not in trusted]
        new = [v for v in trusted if v not in have]
        print(f"=== {p.name}")
        print(f"  现有: {', '.join(sorted(have)) or '(无)'}")
        print(f"  可信建议: {', '.join(trusted) or '(无)'}")
        if new:
            print(f"  建议补上: {', '.join(new)}")
        for v in new:
            r = rules[v]
            why = [b for b in r["blocks"] if b in blocks] or [t for t in r["tokens"] if t in toks]
            print(f"    {v}: 因为 {', '.join(why[:3])}（留出集精确率 {r['precision']:.0%}）")
        if show_all and weak:
            print(f"  低置信(仅供参考): {', '.join(weak)}")


def rewrite_labels(src: pathlib.Path, labels: list[str], out_dir: pathlib.Path) -> pathlib.Path:
    """Replace only the `labels` tag, copying the rest of the payload verbatim."""
    raw_file = src.read_bytes()
    if raw_file[:4] != msch.MAGIC:
        raise SystemExit(f"{src}: not a schematic")
    version = raw_file[4]
    raw = zlib.decompress(raw_file[5:])
    r = msch.Reader(raw)
    w, h = r.s(), r.s()
    n_tags = r.ub()
    tags: dict[str, str] = {}
    for _ in range(n_tags):
        k = r.utf()
        tags[k] = r.utf()
    tail = raw[r.pos:]

    tags["labels"] = json.dumps(labels, ensure_ascii=False)
    body = bytearray()
    body += struct.pack(">hh", w, h)
    body.append(len(tags))
    for k, v in tags.items():
        mschgen_write_utf(body, k)
        mschgen_write_utf(body, v)
    body += tail

    out_dir.mkdir(parents=True, exist_ok=True)
    dst = out_dir / src.name
    dst.write_bytes(msch.MAGIC + bytes([version]) + zlib.compress(bytes(body), 9))
    return dst


def mschgen_write_utf(out: bytearray, s: str) -> None:
    b = s.encode("utf-8")
    if len(b) > 0xFFFF:
        raise ValueError("string too long")
    out += struct.pack(">H", len(b)) + b


def main() -> None:
    rows = load_corpus()
    print(f"语料 {len(rows)} 份")

    if "--suggest" in sys.argv:
        i = sys.argv.index("--suggest")
        paths = [a for a in sys.argv[i + 1:] if not a.startswith("--")]
        suggest(paths, json.loads(RULES.read_text("utf-8")))
        return

    if "--apply" in sys.argv:
        i = sys.argv.index("--apply")
        args = sys.argv[i + 1:]
        out_dir = None
        if "--out" in args:
            j = args.index("--out")
            out_dir = pathlib.Path(args[j + 1])
            args = args[:j] + args[j + 2:]
        if out_dir is None:
            raise SystemExit("--apply needs --out DIR (never overwrite the originals)")
        rules = json.loads(RULES.read_text("utf-8"))
        for raw in args:
            p = pathlib.Path(raw)
            sch = msch.parse_file(str(p))
            blocks, toks, biggest = facts(sch)
            have = [l for l in (sch.labels or []) if l.strip()]
            have_text = {split_label(l)[1] for l in have}
            add = [v for v, r in rules.items()
                   if v not in have_text and predict(r, blocks, toks, biggest)
                   and r.get("precision", 0) >= MIN_PRECISION]
            dst = rewrite_labels(p, have + sorted(add), out_dir)
            print(f"{p.name} -> {dst.name}  (+{len(add)})")
        return

    rules = train(rows)
    prec = precision(rows, rules, "test")
    for v, p in prec.items():
        rules[v]["precision"] = round(p, 3)
    RULES.write_text(json.dumps(rules, ensure_ascii=False, indent=1, sort_keys=True),
                     encoding="utf-8")
    print(f"学到 {len(rules)} 条规则 -> {RULES.name}")
    trusted = sorted(v for v, p in prec.items() if p >= MIN_PRECISION)
    print(f"其中 {len(trusted)} 条留出集精确率 >= {MIN_PRECISION:.0%}:{'、'.join(trusted)}")
    evaluate(rows, rules, "train")
    evaluate(rows, rules, "test")


if __name__ == "__main__":
    main()
