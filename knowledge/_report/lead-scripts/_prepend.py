
p = r"<repo>\knowledge\08-evidence\README.md"
fm = open(r"<scratch-dir>\kb-stage\_fm.txt", encoding='utf-8').read()
s = open(p, encoding='utf-8').read()
if not s.startswith('---'):
    open(p,'w',encoding='utf-8',newline='\n').write(fm+s); print('prepended')
else:
    print('already')
