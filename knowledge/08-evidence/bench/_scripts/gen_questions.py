# -*- coding: utf-8 -*-
"""主装配：调用各域 build_*，校验后写出 questions.jsonl。

用法（必须设 AS_REPO 指向仓库根）：
  python gen_questions.py
"""
import json, os, sys
from pathlib import Path

import _gen_core as C
import _gen_d1, _gen_d2a, _gen_d2b, _gen_d2c

DOMAINS = [
    ("执行模型",       _gen_d1.build_exec),
    ("变量与作用域",   _gen_d1.build_var),
    ("控制流",         _gen_d1.build_flow),
    ("读写感知",       _gen_d2a.build_io),
    ("绘制文本",       _gen_d2a.build_draw),
    ("世界交互",       _gen_d2a.build_world),
    ("单位控制",       _gen_d2b.build_unit),
    ("性能限制",       _gen_d2b.build_perf),
    ("方块与锚点",     _gen_d2b.build_block),
    ("电力与热",       _gen_d2c.build_power),
    ("液体与物流",     _gen_d2c.build_liquid),
    ("战斗与单位",     _gen_d2c.build_combat),
]

PER_DOMAIN = 25
DIFF_SPLIT = {1: 6, 2: 13, 3: 6}

def _normalize_difficulty(qs):
    """把每域难度归一到 6/13/6（24% / 52% / 24%）。

    每个域的 builder 手工标注了初始难度；这里按
      (手标难度, 是否 code/calc 题)
    升序稳定排序，前 6 名记 1（易）、中间 13 名记 2（中）、后 6 名记 3（难）。
    手标只用于排序，最终分布由 ASSERT 保证。排序是确定性的（stable sort，同键保序）。
    """
    by_domain = {}
    for x in qs:
        by_domain.setdefault(x["domain"], []).append(x)
    for name, items in by_domain.items():
        def key(x):
            return (x["difficulty"], 1 if x["type"] in ("code", "calc") else 0)
        order = sorted(range(len(items)), key=lambda i: key(items[i]))
        for rank, i in enumerate(order):
            items[i]["difficulty"] = 1 if rank < DIFF_SPLIT[1] else (2 if rank < DIFF_SPLIT[1] + DIFF_SPLIT[2] else 3)

def main():
    for name, fn in DOMAINS:
        before = len(C._QS)
        fn()
        got = len(C._QS) - before
        assert got == PER_DOMAIN, f"{name}: {got} 题（应为 {PER_DOMAIN}）"
    qs = C.all_questions()
    assert len(qs) == len(DOMAINS) * PER_DOMAIN == 300, len(qs)
    _normalize_difficulty(qs)

    # 难度与类型校验
    from collections import Counter
    diff_c = Counter(x["difficulty"] for x in qs)
    for d, n in DIFF_SPLIT.items():
        per = Counter(x["domain"] for x in qs if x["difficulty"] == d)
        for name, _ in DOMAINS:
            assert per[name] == n, f"{name} 难度 {d}: {per[name]}（应为 {n}）"
    type_c = Counter(x["type"] for x in qs)

    # src 必须指向真实文件；行号后缀需为 :N 或 :N-M
    repo = C.REPO
    bad = []
    for x in qs:
        p = x["src"].split("#")[0].split(":")[0] if not x["src"].startswith(("data/", "docs/", "tools/", "knowledge/")) else None
        # 统一取「路径部分」：去掉 #fragment 与 :行号
        path = x["src"]
        for sep in ("#",):
            path = path.split(sep)[0]
        # 行号形如 :123 或 :123-456；仅当剩余部分不是 Windows 盘符
        import re
        m = re.match(r"^(.*?)(?::(\d+)(?:-(\d+))?)?$", path)
        pth, l1, l2 = m.group(1), m.group(2), m.group(3)
        full = repo / pth
        if not full.exists():
            bad.append((x["domain"], x["src"], "文件不存在"))
            continue
        if l1:
            n = sum(1 for _ in full.open(encoding="utf-8", errors="ignore"))
            hi = int(l2 or l1)
            if int(l1) < 1 or hi > n:
                bad.append((x["domain"], x["src"], f"行号越界（文件 {n} 行）"))
    assert not bad, "src 校验失败：\n" + "\n".join(map(str, bad[:20]))

    out = Path(__file__).resolve().parent / "questions.jsonl"
    with out.open("w", encoding="utf-8", newline="\n") as f:
        for i, x in enumerate(qs, 1):
            rec = {
                "id": f"BENCH.{i:04d}",
                "domain": x["domain"],
                "difficulty": x["difficulty"],
                "type": x["type"],
                "q": x["q"],
                "answer": x["answer"],
                "why": x["why"],
                "src": x["src"],
                "ver": x["ver"],
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print("wrote", out)
    print("total", len(qs))
    print("difficulty", dict(sorted(diff_c.items())))
    print("type", dict(type_c))
    print("domains", len({x["domain"] for x in qs}))
    perm = Counter((x["domain"]) for x in qs)
    for name, _ in DOMAINS:
        print(f"  {name}: {perm[name]} 题, "
              f"E{sum(1 for x in qs if x['domain']==name and x['difficulty']==1)} "
              f"M{sum(1 for x in qs if x['domain']==name and x['difficulty']==2)} "
              f"H{sum(1 for x in qs if x['domain']==name and x['difficulty']==3)}")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
