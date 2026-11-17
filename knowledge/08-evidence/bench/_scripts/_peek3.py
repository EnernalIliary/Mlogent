
import pathlib as _pl
_HERE = _pl.Path(__file__).resolve().parent          # knowledge/08-evidence/bench/_scripts
_KB = _HERE.parents[2]                               # knowledge
_REPO = _HERE.parents[3]                             # 仓库根
import json,os
os.makedirs(str(_HERE.parent),exist_ok=True)
d=json.load(open(str(_KB / "tools" / "instr_semantics.json"),encoding="utf-8"))
print('OPS:', ','.join(d['ops'].keys()))
for k in ['jump','setrate','print','draw','ucontrol','ulocate','radar','getblock','setblock','lookup','packcolor','sync','message','status','sensor','select','uradar','spawn','op','getlink','read','write']:
    v=d['instructions'].get(k)
    if v: print(f"[{k}] note={v.get('note','')[:260]} | wspecial={v.get('writes_special')} | min_build={v.get('min_build')}")
print('RO:', ','.join(d['builtin_readonly_vars']))
print('WSPECIAL:', d['builtin_special_writable'])
