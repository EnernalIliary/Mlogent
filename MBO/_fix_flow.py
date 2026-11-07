# -*- coding: utf-8 -*-
"""修 flow_single.py 里的引号嵌套语法错误。"""
import io

P = "spikes/gen/flow_single.py"
s = io.open(P, encoding="utf-8").read()
lines = s.splitlines(keepends=True)
out = []
fixed = 0
for ln in lines:
    if "喂不满" in ln and "print(" in ln:
        out.append('        print("  （模型判喂不满：单源 4.9/s 对 %d 台来说不够）" % args.machines)\n')
        fixed += 1
    else:
        out.append(ln)
io.open(P, "w", encoding="utf-8").write("".join(out))
print("fixed", fixed)
