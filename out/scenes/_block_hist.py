"""Block-name histogram for a scene save (for captions / sanity checks)."""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import mlogsim as M  # noqa: E402

JS = r"""
var c = {};
for(var y = 0; y < Vars.world.height(); y++){
    for(var x = 0; x < Vars.world.width(); x++){
        var b = Vars.world.tile(x, y).block();
        if(b == null || b.name == "air") continue;
        c[b.name] = (c[b.name] || 0) + 1;
    }
}
for(var k in c) print("H\t" + k + "\t" + c[k]);
print("DONE");
"""


def main() -> int:
    for name in sys.argv[1:]:
        srv = M.Server(M._default_java(), M._default_jar(), save=HERE / name)
        try:
            lines = srv.js(JS)
        finally:
            srv.close()
        hist = Counter()
        for ln in lines:
            p = ln.split("\t")
            if p[0] == "H":
                hist[p[1]] += int(p[2])
        print(f"== {name} ({sum(hist.values())} tiles, {len(hist)} kinds)")
        for k, v in hist.most_common(18):
            print(f"  {v:5d}  {k}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
