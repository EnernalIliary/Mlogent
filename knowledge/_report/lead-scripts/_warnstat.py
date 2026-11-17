import json, subprocess, sys
from collections import Counter, defaultdict
from pathlib import Path
W = Path("<scratch-dir>/kb-stage")
PY = sys.executable
ROOT = "<repo>/knowledge"
p = subprocess.run([PY, str(W/"tools"/"check_kb.py"), "--root", ROOT, "--json"],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
if p.returncode == 2 or not p.stdout.strip():
    print("FAIL rc=%s" % p.returncode)
    print(p.stderr[-1500:])
    sys.exit(1)
doc = json.loads(p.stdout)
ws = doc.get("warning_list", [])
es = doc.get("error_list", [])
c = Counter(w["code"] for w in ws)
by_path = defaultdict(Counter)
for w in ws:
    by_path[w.get("path", "?")][w["code"]] += 1
total = len(ws)
lines = ["# warning 按 code 统计（check_kb.py --json）", "",
         "- 生成: kb-stage/_warnstat.py  ·  根: " + ROOT,
         "- files=%d  errors=%d  warnings=%d  tokens~%s" % (doc.get("files", 0), len(es), total, doc.get("tokens", "?")),
         "- 退出码: %d" % p.returncode, "",
         "## 总表", "", "| code | 条数 | 占比 | 含义 |", "|---|---:|---:|---|"]
MEAN = {
 "W_NUM_NO_SOURCE": "数字声明行缺来源标记（[src: / [实测 / 见 DATA）",
 "W_TOKENS_STALE": "frontmatter tokens 与实际估算不符",
 "W_DATA_FILE_MISSING": "data: 引用的 00-data 文件不存在",
 "W_DATA_FRAGMENT": "data: #片段在表中不存在",
 "W_REF_UNKNOWN": "相关 小节引用了库里不存在的 ID",
 "W_SECTION_SHORT": "小节内容过短",
 "W_LINK_BROKEN": "相对链接不可达",
 "W_ID_DUP": "id 重复",
 "W_TITLE_DUP": "标题重复",
 "W_DOMAIN_EMPTY": "域目录下没有文章",
 "W_VER_MIXED": "ver 字段混用版本",
 "W_NUM_FORMAT": "{v,unit} 数值字段格式问题",
 "W_SRC_FORMAT": "src 条目不像 路径:行号 / jar: 形式",
 "W_DATA_RECORD": "00-data 记录缺 id/src/ver 之一",
 "W_DOMAIN_DIR_MISSING": "域目录缺失",
 "W_SECTION_EMPTY": "小节为空",
}
for code, n in c.most_common():
    lines.append("| %s | %d | %.1f%% | %s |" % (code, n, 100.0*n/total if total else 0, MEAN.get(code, "")))
lines += ["", "## 按文件（Top 20，warning 数最多）", "", "| 文件 | warning 数 | 主要 code |", "|---|---:|---|"]
for path, cc in sorted(by_path.items(), key=lambda kv: -sum(kv[1].values()))[:20]:
    main, mn = cc.most_common(1)[0]
    lines.append("| %s | %d | %s x%d |" % (path, sum(cc.values()), main, mn))
if es:
    lines += ["", "## errors（%d）" % len(es), "", "| 文件:行 | code | msg |", "|---|---|---|"]
    for e in es[:40]:
        lines.append("| %s:%s | %s | %s |" % (e.get("path"), e.get("line"), e.get("code"), e.get("msg", "")[:120].replace("|", "/")))
out = W/"_report"/"warnings_by_code.md"
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("wrote", out, "warnings", total, "codes", len(c))
print("\n".join(lines[:26]))
