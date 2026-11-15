import re, sys
from pathlib import Path
from collections import Counter
ROOT = Path("<repo>/knowledge")
NUM = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?!\w)")
SRC = ("[src:", "[实测", "[ver", "[v1", "见 DATA", "00-data/")
DOM = ["01-execution","02-world","03-combat","04-units","05-campaign","06-mlog","07-patterns","08-evidence"]
sec_cnt = Counter(); tot = 0; perfile = Counter()
for d in DOM:
    for f in sorted((ROOT/d).rglob("*.md")):
        if f.name.lower() == "readme.md" or f.name.startswith("_"):
            continue
        cur = "(head)"
        in_fence = False
        for ln in f.read_text(encoding="utf-8-sig").splitlines():
            s = ln.strip()
            if s.startswith(chr(96)*3):
                in_fence = not in_fence; continue
            if in_fence: continue
            if s.startswith("#"):
                cur = s.lstrip("# ").strip()[:14]; continue
            if not s or s.startswith("|"): continue
            if not NUM.search(s): continue
            if any(m in s for m in SRC): continue
            tot += 1; sec_cnt[cur] += 1; perfile[f.name] += 1
print("逐行无源数字（不算表格/代码块，未套 6 行窗口）总=%d 文件=%d" % (tot, len(perfile)))
for k, v in sec_cnt.most_common(10):
    print("  小节 %-16s %d" % (k, v))
print("Top 文件:", ", ".join("%s×%d" % (k, v) for k, v in perfile.most_common(6)))
