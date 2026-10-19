import json,io
j=json.load(open(r'mindustry-blueprint/tools/cmd_index.json',encoding='utf-8'))
out=[]
for e in j:
    names=[p[0] for p in e.get('params') or []]
    out.append(f"{e['num']}|{e.get('format','')}|{names}|{e['title']}")
open(r'tools\_cmd_compact.txt','w',encoding='utf-8').write("\n".join(out))
print(len(j))
