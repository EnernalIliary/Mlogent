"""One-off: turn out/caime_scan.json into the numbers behind the pack portrait."""
from __future__ import annotations

import collections
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
D = json.loads((ROOT / "out" / "caime_scan.json").read_text(encoding="utf-8"))
ROWS = D["rows"]

FUSED = re.compile(
    r"`?(\d+(?:sensor|control|jump|set|op|print|read|write|ucontrol|ulocate|"
    r"draw|wait|end|getlink|ubind))\b")


def tiles():
    for r in ROWS:
        for t in r["detail"]:
            yield r, t


print("=" * 78)
print("A. 规模")
withlogic = [r for r in ROWS if r["logic_tiles"]]
blocks = sum(r["logic_tiles"] for r in withlogic)
stmts = sum(r["statements"] for r in withlogic)
print(f"  files parsed        {len(ROWS)}  (failed {len(D['bad'])})")
print(f"  files with logic    {len(withlogic)}  ({100*len(withlogic)/len(ROWS):.0f}%)")
print(f"  logic blocks        {blocks}")
print(f"  statements          {stmts:,}")
per = sorted(t["stmts"] for _, t in tiles())
print(f"  per-block           med {per[len(per)//2]}, p90 {per[int(len(per)*.9)]}, max {per[-1]}")

print()
print("B. 缺陷总量")
tot = collections.Counter()
for r in ROWS:
    for k in ("errs", "warns", "dead_reported", "dead_hidden", "unreachable",
              "spins", "spins_no_exit", "waits", "wait_ticks", "branches", "nulls"):
        tot[k] += r[k]
for k in ("errs", "warns", "dead_reported", "dead_hidden", "unreachable",
          "spins", "spins_no_exit", "waits", "wait_ticks", "branches", "nulls"):
    print(f"  {k:<14}{tot[k]:,}")

undef_t = nullg = cskip = 0
affected_undef = affected_cskip = 0
for _, t in tiles():
    u = t.get("undef_vars", 0)
    undef_t += u
    nullg += t.get("null_guards", 0)
    c = t.get("const_skipped", 0)
    cskip += c
    affected_undef += 1 if u else 0
    affected_cskip += 1 if c else 0
print(f"  undef vars     {undef_t:,} distinct reads in {affected_undef} block(s)")
print(f"  null guards    {nullg:,}  (jump on an unset variable vs null)")
print(f"  const-skipped  {cskip:,} statements provably unreachable, "
      f"in {affected_cskip} block(s)")

print()
print("C. 常见错误形态 (top 12)")
shapes = collections.Counter()
for _, t in tiles():
    for level, line, text, detail in t["findings"]:
        shapes[(level, text)] += 1
for (level, text), n in shapes.most_common(12):
    print(f"  {n:5}  {level}: {text}")

print()
print("D. 折掉恒真守卫后最空的块 (top 12)")
rows_c = sorted(((t.get("const_skipped", 0), r["file"], t) for r, t in tiles()),
                key=lambda x: -x[0])[:12]
for c, f, t in rows_c:
    if not c:
        break
    print(f"  {c:5} / {t['stmts']:5} stmts  {t['block']}@{tuple(t['at'])}  "
          f"{t.get('null_guards',0)} guards  {f.split(chr(92))[-1]}")
    print(f"        undef: {', '.join(t.get('undef_names', []))}")

print()
print("E. 按分类")
cat = collections.defaultdict(lambda: collections.Counter())
for r in ROWS:
    c = cat[r["category"] or "(根目录)"]
    c["files"] += 1
    c["with_logic"] += 1 if r["logic_tiles"] else 0
    c["blocks"] += r["logic_tiles"]
    c["stmts"] += r["statements"]
    c["errs"] += r["errs"]
    c["dead"] += r["dead_reported"]
    c["spins"] += r["spins"]
    c["cskip"] += sum(t.get("const_skipped", 0) for t in r["detail"])
print(f"  {'分类':<26}{'文件':>5}{'有逻辑':>7}{'块':>6}{'语句':>9}{'硬错':>6}{'死存':>6}{'自旋':>7}{'恒假跳过':>9}")
for k, c in sorted(cat.items(), key=lambda kv: -kv[1]["stmts"]):
    print(f"  {k[:24]:<26}{c['files']:>5}{c['with_logic']:>7}{c['blocks']:>6}"
          f"{c['stmts']:>9,}{c['errs']:>6}{c['dead']:>6}{c['spins']:>7}{c['cskip']:>9,}")

print()
print("F. 硬错最多的文件 (top 10)")
for r in sorted(ROWS, key=lambda r: -r["errs"])[:10]:
    if not r["errs"]:
        break
    print(f"  {r['errs']:4} errs / {r['logic_tiles']:3} blocks  {r['file'].split(chr(92))[-1]}")

print()
print("G. 死存储最多的文件 (top 10)")
for r in sorted(ROWS, key=lambda r: -r["dead_reported"])[:10]:
    if not r["dead_reported"]:
        break
    print(f"  {r['dead_reported']:5} dead / {r['statements']:6} stmts  "
          f"{r['file'].split(chr(92))[-1]}")

print()
print("H. 换行丢失 (两条语句粘成一条) 的迹象")
fused = [(r["file"], t) for r, t in tiles()
         if any(FUSED.search(d) for _, _, _, d in t["findings"])]
print(f"  {len(fused)} block(s)")
for f, t in fused[:8]:
    for level, line, text, detail in t["findings"]:
        m = FUSED.search(detail)
        if m:
            print(f"    L{line}: {text}  <- `{m.group(1)}`  {f.split(chr(92))[-1]}")
            break

print()
print("I. 带信息板的文件 / 自称作者")
who = collections.Counter()
for r in ROWS:
    txt = "\n".join(r["texts"])
    for m in re.finditer(r"(?i)\bby[ _:：-]*([A-Za-z0-9_\u4e00-\u9fff]{2,20})", txt):
        who[m.group(1).strip()] += 1
print(f"  files with message board: {sum(1 for r in ROWS if r['texts'])} / {len(ROWS)}")
for k, n in who.most_common(12):
    print(f"    {n:4}  {k}")
