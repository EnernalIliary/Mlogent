
p = r"<scratch-dir>\kb-stage\08-evidence\claims.jsonl"
b = open(p,'rb').read(200)
print(b[:120])
try:
    s = b.decode('utf-8'); print("UTF8 OK:", s[:160])
except Exception as e:
    print("not utf8", e)
    s = b.decode('gbk'); print("GBK:", s[:160])
