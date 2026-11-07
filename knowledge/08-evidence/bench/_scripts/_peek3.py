
import json,os
os.makedirs(r'F:\OneDrive\文档\deepseek-harness\default-workspace\kb-stage\08-evidence\bench',exist_ok=True)
d=json.load(open(r'F:\OneDrive\桌面\AtomicStates\tools\instr_semantics.json',encoding='utf-8'))
print('OPS:', ','.join(d['ops'].keys()))
for k in ['jump','setrate','print','draw','ucontrol','ulocate','radar','getblock','setblock','lookup','packcolor','sync','message','status','sensor','select','uradar','spawn','op','getlink','read','write']:
    v=d['instructions'].get(k)
    if v: print(f"[{k}] note={v.get('note','')[:260]} | wspecial={v.get('writes_special')} | min_build={v.get('min_build')}")
print('RO:', ','.join(d['builtin_readonly_vars']))
print('WSPECIAL:', d['builtin_special_writable'])
