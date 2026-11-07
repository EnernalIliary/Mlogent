import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import search_ported as S

rows = S.structured()
rows.sort(key=S.key)
for r in rows[:5]:
    print(r["label"], "ports", r["ports"], "tiles", r["tiles"], "rate", r["rate"],
          "in", r["in_flow"], "out", r["out_flow"], "need", r["ok_need"])
    print("   blocks:", [(b[0], b[1], b[2], b[3]) for b in r["blocks"]])
    print("   stats:", r["lay"].stats())
