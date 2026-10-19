import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "tools")
import blocks_from_source as B  # noqa: E402

text = B.BLOCKS.read_text("utf-8", errors="replace")
data = json.loads(Path("tools/block_attrs.json").read_text("utf-8"))
have = data["blocks"]

consume = 0
consume_missing = []
for _f, cls, name, body in B.entries(text):
    t = "\n".join(body)
    has_c = ("consumeItem(" in t) or ("consumeItems(" in t) or ("consumeLiquid" in t)
    if has_c:
        consume += 1
        if name not in have or ("inputs" not in have[name] and "liquids" not in have[name]):
            consume_missing.append((name, cls))

print("entries:", len(B.entries(text)))
print("captured:", len(have))
print("bodies with consume*:", consume, " of which missing from JSON:", len(consume_missing))
for n, c in consume_missing[:20]:
    print("   MISS", n, c)

# which consume forms do we fail to parse?
forms: dict[str, int] = {}
for _f, cls, name, body in B.entries(text):
    t = "\n".join(body)
    for m in re.finditer(r"consume\w*\(", t):
        forms[m.group(0)] = forms.get(m.group(0), 0) + 1
print("consume call forms:", dict(sorted(forms.items(), key=lambda kv: -kv[1])))
