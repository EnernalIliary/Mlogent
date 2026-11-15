
import json,subprocess,sys,os,collections
sys.stdout.reconfigure(encoding='utf-8',errors='replace')
root=r"<repo>\knowledge"
p=subprocess.run([sys.executable,"-u",os.path.join(root,"tools","check_kb.py"),"--root",root,"--json"],capture_output=True)
txt=p.stdout.decode('utf-8',errors='replace'); d=json.loads(txt[txt.index('{'):])
print("files",d['files'],"errors",d['errors'],"warnings",d['warnings'],"tokens",d['tokens'])
print(d['domain_counts'])
print(dict(collections.Counter(x['code'] for x in d['error_list'])))
for x in d['error_list']:
    print(" -",x['path'],x['line'],x['code'],x['msg'][:110])
