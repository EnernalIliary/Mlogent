"""Sweep every save for the reactor-guard-latency rule, deduped by source hash."""
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mindustry-blueprint" / "tools"))
import map_logic as M
import mlogcheck as C

IPT = {"micro-processor": 2, "logic-processor": 8, "hyper-processor": 25,
       "world-processor": 8, "world-cell": 8, "world-message": 8}
SAVES = Path.home() / "AppData/Roaming/Mindustry/saves"

def code_hash(code):
    norm = "\n".join(l.rstrip() for l in code.replace("\r\n", "\n").split("\n"))
    return hashlib.sha1(norm.strip("\n").encode("utf-8")).hexdigest()

reactors = guarded = 0
seen, dup, hits = {}, {}, []
for n, f in enumerate(sorted(SAVES.glob("*.msav")), 1):
    try:
        info = M.read_save(str(f))
    except Exception as e:
        print(f"!! {f.name}: {e}")
        continue
    for t in info["logic"]:
        code = t.get("code") or ""
        if "@heat" not in code or "reactor" not in code.lower():
            continue
        reactors += 1
        h = code_hash(code)
        lines = code.split("\n")
        if h in seen:
            dup[h] = dup.get(h, 0) + 1
            continue
        seen[h] = {"save": f.name, "x": t["x"], "y": t["y"],
                   "block": t["block"], "stmts": len(lines), "code": code}
        names = [l["name"] for l in t.get("links", [])]
        msgs = [fi.msg for fi in C.analyse(lines, names, IPT.get(t["block"], 2))
                if "reactor guard" in fi.msg]
        if msgs:
            hits.append({"hash": h, "msg": msgs[0], **{k: seen[h][k] for k in
                         ("save", "x", "y", "block", "stmts")}})
        guarded += any(l.split()[:2] == ["control", "enabled"] for l in lines)
        if "@heat" in code and "control enabled" in code:
            pass
    if n % 300 == 0:
        print(f"  {n}  reactor-programs={reactors} distinct={len(seen)} hits={len(hits)}", flush=True)

print(f"\nprograms touching a reactor + @heat : {reactors}")
print(f"distinct programs                 : {len(seen)}")
print(f"late guards (distinct)            : {len(hits)}")
print(f"late guards (with copies)         : {len(hits) + sum(dup.get(h['hash'], 0) for h in hits)}")
for h in hits:
    print(f"  {h['save']} ({h['x']},{h['y']}) {h['block']} [{h['stmts']} stmt x{1+dup.get(h['hash'], 0)}]: {h['msg'][:150]}")
Path("out/reactor_guard.json").write_text(json.dumps(
    {"reactors": reactors, "distinct": len(seen), "hits": hits}, ensure_ascii=False, indent=1), encoding="utf-8")
