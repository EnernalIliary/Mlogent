
import re, glob, io, os
roots = [r"<repo>\knowledge", r"<scratch-dir>\kb-stage"]
n=0
for root in roots:
    for p in glob.glob(os.path.join(root,'06-mlog','*.md')):
        s=open(p,encoding='utf-8').read()
        s2=re.sub(r'^domain:\s*MLOG\s*$', 'domain: mlog', s, flags=re.M)
        if s2!=s:
            open(p,'w',encoding='utf-8',newline='\n').write(s2); n+=1
print('patched',n)
