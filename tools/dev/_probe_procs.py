"""Distribution check: are the processor counts real, or walk noise?

A false positive would need a garbage block id that happens to be a processor
*and* a chunk payload that parses as a valid LogicBlock config, so the counts
are probably honest.  An empty processor (0 statements, 0 links) is also a real
thing people place.  Printing the histogram lets the shape be judged instead of
guessed.
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "mindustry-blueprint" / "tools"))
import map_logic as M

saves = Path(r"C:\Users\lliary\AppData\Roaming\Mindustry\saves")
for name in sys.argv[1:]:
    info = M.read_save(saves / name)
    procs = info["logic"]
    names = info["block_types"]
    stmts = [len([l for l in t["code"].splitlines() if l.strip()]) for t in procs]
    hist = Counter()
    for n in stmts:
        if n == 0:
            hist["0"] += 1
        elif n < 10:
            hist["1-9"] += 1
        elif n < 100:
            hist["10-99"] += 1
        elif n < 1000:
            hist["100-999"] += 1
        else:
            hist["1000+"] += 1
    kinds = Counter(t["block"] for t in procs)
    print(f"{name}  v{info['version']}  {info['width']}x{info['height']}  "
          f"{len(procs)} proc  {sum(stmts)} stmt")
    print("   kind:", dict(kinds))
    print("   stmt:", dict(hist))
    print("   links:", sum(len(t["links"]) for t in procs))
