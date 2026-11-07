"""生成对拍用的 cases.json：直接用 `mbo calc --json` 的输出当期望值。

用法：python -X utf8 ratio-calc/make_cases.py
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

CASES = [
    # (target, rate, boundary, force)
    ("graphite", 2, ["coal"], None),
    ("silicon", 5, ["coal", "sand"], None),
    ("surge-alloy", 1, [], None),
    ("metaglass", 4, ["sand", "lead"], None),
    ("plastanium", 1, [], None),
    ("blast-compound", 1, [], None),
    ("pyratite", 1, [], None),
    ("graphite", 1, ["coal"], None),
    ("silicon", 3, ["coal", "sand"], None),
    ("phase-fabric", 0.5, [], None),
    ("spore-pod", 2, [], None),
    # 强制配方：同一个物品换一台机器，台数与需求都要跟着变
    ("graphite", 2, ["coal"], {"graphite": "multi-press"}),
    ("silicon", 3, ["coal", "sand"], {"silicon": "silicon-crucible"}),
    ("surge-alloy", 1, [], {"surge-alloy": "surge-smelter"}),
]

out = []
for target, rate, boundary, force in CASES:
    cmd = [sys.executable, "-X", "utf8", "-m", "mbo", "calc",
           "%s:%s/s" % (target, rate), "--json"]
    if boundary:
        cmd += ["--boundary", ",".join(boundary)]
    if force:
        cmd += ["--force", ",".join("%s=%s" % kv for kv in force.items())]
    p = subprocess.run(cmd, cwd=os.path.join(ROOT, "MBO"),
                       capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        print("跳过 %s:%s/s（%s）" % (target, rate, p.stderr.strip()[:120]))
        continue
    d = json.loads(p.stdout)
    label = "%s %s/s" % (target, rate)
    if force:
        label += " [force " + ",".join("%s=%s" % kv for kv in force.items()) + "]"
    out.append({
        "label": label,
        "target": target,
        "rate": rate,
        "boundary": boundary,
        "force": force or {},
        "expect": {
            "machines": d["machines"],
            "demand": d["boundary_demand"],
            "power": d["power_need"],
        },
    })

path = os.path.join(HERE, "cases.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=2)
print("写出 %s：%d 个用例" % (path, len(out)))
