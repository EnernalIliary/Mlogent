import re
from pathlib import Path
from collections import Counter
ROOT = Path("<repo>/knowledge")
NUM = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?!\w)")
SRC = ("[src:", "[实测", "[ver", "[v1", "见 DATA", "00-data/")
DOM = ["01-execution","02-world","03-combat","04-units","05-campaign","06-mlog","07-patterns","08-evidence"]
with_marker = 0; without = 0; sections_without = Counter()
for d in DOM:
    for f in sorted((ROOT/d).rglob("*.md")):
        if f.name.lower() == "readme.md" or f.name.startswith("_"):
            continue
        secs = []  # (heading, [lines])
        cur = ["(head)", []]
        in_fence = False
        for ln in f.read_text(encoding="utf-8-sig").splitlines():
            s = ln.strip()
            if s.startswith(chr(96)*3):
                in_fence = not in_fence; cur[1].append(ln); continue
            if not in_fence and s.startswith("#"):
                secs.append(tuple(cur)); cur = [s.lstrip("# ").strip()[:16], []]
                continue
            cur[1].append(ln)
        secs.append(tuple(cur))
        for head, lines in secs:
            has = any(any(m in l for m in SRC) for l in lines)
            bad = sum(1 for l in lines if l.strip() and not l.strip().startswith("|") and NUM.search(l) and not any(m in l for m in SRC))
            if not bad:
                continue
            if has:
                with_marker += bad
            else:
                without += bad; sections_without[head] += bad
print("无源数字行：所在小节已有来源标记=%d  所在小节完全没有标记=%d" % (with_marker, without))
for k, v in sections_without.most_common(8):
    print("   无标记小节 %-16s %d" % (k, v))
