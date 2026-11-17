import json, re, subprocess, sys
from pathlib import Path
from collections import Counter
W = Path("<scratch-dir>/kb-stage")
p = subprocess.run([sys.executable, str(W/"tools"/"check_kb.py"), "--root", "<repo>/knowledge", "--json"], capture_output=True, text=True, encoding="utf-8", errors="replace")
doc = json.loads(p.stdout)
ws = [w for w in doc["warning_list"] if w["code"] == "W_NUM_NO_SOURCE"]
extra = 0
det = 0
files = set()
for w in ws:
    m = re.search(r"另有 (\d+) 行", w["msg"] or "")
    if m:
        extra += int(m.group(1))
    else:
        det += 1
    files.add(w["path"])
print("W_NUM_NO_SOURCE 明细条=%d 折叠条=%d 折叠隐藏行=%d 估算真实无源数字行≈%d 涉及文件=%d" % (det, len(ws)-det, extra, det+extra, len(files)))
print("文件数(文章)=", doc["files"], " warnings总=", doc["warnings"])
