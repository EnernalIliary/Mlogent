
import json,subprocess,sys,collections,os
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
root=r"<repo>\knowledge"
gate=os.path.join(root,"tools","check_kb.py")
p=subprocess.run([sys.executable,"-u",gate,"--root",root,"--json"],capture_output=True)
txt=p.stdout.decode('utf-8',errors='replace')
try:
    d=json.loads(txt[txt.index('{'):])
except Exception as e:
    print("PARSE FAIL",e); print(txt[:600]); sys.exit()
print("files",d.get("files"),"errors",d.get("errors"),"warnings",d.get("warnings"))
errs=[x for x in d.get("items",d.get("messages",[])) if str(x.get("level","")).lower().startswith("e")]
c=collections.Counter(x.get("code") for x in errs)
print(c)
for x in errs[:40]:
    print(x.get("code"),"|",x.get("file","")[-46:],"|",str(x.get("msg",""))[:120])
