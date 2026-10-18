"""Find every textual form of the alt account's name, so the pattern list is
built from evidence instead of a guess."""
import collections
import pathlib
import re
import sys

sys.path.insert(0, "mindustry-blueprint/tools")
import msch  # noqa: E402

C = pathlib.Path.home() / "AppData" / "Roaming" / "Mindustry" / "schematics"
PROBE = re.compile(r".{0,14}鱼.{0,14}")

found: collections.Counter[str] = collections.Counter()
files: dict[str, set[str]] = collections.defaultdict(set)

for p in sorted(C.glob("*.msch")):
    try:
        sch = msch.parse_file(str(p))
    except Exception:
        continue
    blobs = [sch.description or "", sch.name or ""]
    for t in sch.tiles:
        if isinstance(t.config, str):
            blobs.append(t.config)
    for t in sch.logic_tiles():
        for line in t.logic.code.split("\n"):
            if "鱼" in line:
                blobs.append(line)
    for b in blobs:
        for m in PROBE.finditer(b):
            s = m.group(0).strip()
            found[s] += 1
            files[s].add(p.name)

print(f"含「鱼」的片段 {len(found)} 种，出现 >=2 次的：")
for s, n in found.most_common(40):
    if n >= 2:
        print(f"  {n:4d}  {s!r}")
print("\n只看可能和账号有关的：")
for s, n in found.items():
    if re.search(r"鱼\s*(破|破冰|冰|破冰)", s):
        print(f"  {n:4d}  {s!r}  例: {sorted(files[s])[:2]}")
