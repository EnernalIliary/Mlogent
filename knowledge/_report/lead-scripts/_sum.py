
import json,subprocess,sys,collections
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
root=r"<repo>\knowledge"
p=subprocess.run([sys.executable,r"<repo>\knowledge\tools\check_kb.py","--root",root,"--all","--json"],capture_output=True,text=True,encoding='utf-8',errors='replace')
d=json.loads(p.stdout)
print("domain_counts",d["domain_counts"])
wl=d["warning_list"]
print("warn codes",dict(collections.Counter((w[2] if isinstance(w,list) else w.get("code")) for w in wl)))
print("sample",wl[:3])
