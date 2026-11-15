import json, subprocess, sys
from pathlib import Path
from collections import Counter
W = Path("<scratch-dir>/kb-stage")
p = subprocess.run([sys.executable, str(W/"tools"/"check_kb.py"), "--root", "<repo>/knowledge", "--json"], capture_output=True, text=True, encoding="utf-8", errors="replace")
doc = json.loads(p.stdout)
ws = [w for w in doc["warning_list"] if w["code"] == "W_NUM_NO_SOURCE"]
per = Counter(w["path"] for w in ws)
out = ["# W_NUM_NO_SOURCE 抽样（共 %d 条 / %d 个文件）" % (len(ws), len(per)), ""]
out += ["| 文件 | 条数 |", "|---|---:|"] + ["| %s | %d |" % (k, v) for k, v in per.most_common()]
out += ["", "## 逐条（前 40，原文截断 90 字）", ""]
for w in ws[:40]:
    msg = w["msg"].split(": ", 1)[-1][:90].replace("|", "/")
    out.append("- %s:%s  %s" % (w["path"], w["line"], msg))
(W/"_report"/"warn_num_samples.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out[:12]))
print("...")
print("\n".join(out[12:34]))
