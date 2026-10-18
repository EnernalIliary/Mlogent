"""Build a two-processor schematic to probe cross-processor `read`/`write`."""
import sys
from pathlib import Path

TOOLS = Path(r"F:\OneDrive\桌面\AtomicStates\mindustry-blueprint\tools")
sys.path.insert(0, str(TOOLS))

import mschgen as G  # noqa: E402

CODE_A = """set declared 7
set viawrite 8
end
"""

CODE_B = """read a processor1 "declared"
read b processor1 "nope"
write 99 processor1 "fresh"
read c processor1 "fresh"
print "A="
print a
print "|B="
print b
print "|C="
print c
print "|"
end
"""

bp = G.Blueprint(
    name="probe-cross",
    description="cross-processor read of declared vs undeclared slots",
    labels=["[blue]DeepSeek"],
)
bp.add_logic(CODE_A, 0, 0, links=[])
bp.add_logic(CODE_B, 3, 0, links=[G.Link("processor1", -3, 0)])

out = Path(r"F:\OneDrive\桌面\AtomicStates\out\probes\p8-cross.msch")
out.write_bytes(bp.build())
print(f"wrote {out} ({out.stat().st_size} B)")
print("link report:", bp.link_report() or "all links resolved")
