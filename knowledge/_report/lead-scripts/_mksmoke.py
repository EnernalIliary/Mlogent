import json, sys, pathlib
W = r"<scratch-dir>\kb-stage"
idx = json.loads((pathlib.Path(W) / "index.repo.json").read_text(encoding="utf-8-sig"))
rows = []
for d in idx["domains"]:
    for a in d["articles"]:
        rows.append({"q": a["title"], "expect": [a["id"], a["path"]], "kind": "doc"})
p = pathlib.Path(W) / "_report" / "smoke_self.jsonl"
p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
print(len(rows), p)