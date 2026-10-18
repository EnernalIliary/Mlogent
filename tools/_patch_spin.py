# -*- coding: utf-8 -*-
"""One-shot patch: dedupe nested read-only loops in mlogcheck.py.

The `edit` tool keeps failing on files under OneDrive (mtime churn), so the
replacement is done here instead. Delete this file after it runs.
"""
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "mindustry-blueprint" / "tools" / "mlogcheck.py"
s = P.read_text(encoding="utf-8")

OLD1 = """    for i, (orig, c) in enumerate(stmts):
        mj = JMP_RE.match(c)
"""
NEW1 = """    _spin = []
    for i, (orig, c) in enumerate(stmts):
        mj = JMP_RE.match(c)
"""
assert s.count(OLD1) == 1, s.count(OLD1)
s = s.replace(OLD1, NEW1)

OLD2 = """        if not (mnem & EXTERNAL_READ):
            continue                       # nothing external is read
        head = stmts[tgt][0] + 1
"""
NEW2 = """        if not (mnem & EXTERNAL_READ):
            continue                       # nothing external is read
        _spin.append((tgt, i, orig, c))
    for tgt, i, orig, c in _spin:
        if any(o[0] <= tgt and i <= o[1] and (o[0], o[1]) != (tgt, i)
               for o in _spin):
            continue                       # inside a wider loop of the same shape
        head = stmts[tgt][0] + 1
"""
assert s.count(OLD2) == 1, s.count(OLD2)
s = s.replace(OLD2, NEW2)

# the comment above the block now also describes the nest handling
OLD3 = """    #   * anything else waits for someone outside to change the value
    #     (`sensor x cell1 0` / `jump loop equal x 0`). Legitimate handshake,
    #     but worth knowing that the loop cannot end by itself: INFO.
"""
NEW3 = """    #   * anything else waits for someone outside to change the value
    #     (`sensor x cell1 0` / `jump loop equal x 0`). Legitimate handshake,
    #     but worth knowing that the loop cannot end by itself: INFO.
    # A nest of these is one statement, not three, so only the outermost loop of
    # a nest is reported.
"""
if s.count(OLD3) == 1:
    s = s.replace(OLD3, NEW3)

P.write_text(s, encoding="utf-8")
print("patched", P)
