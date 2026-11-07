from _harness import probe

CODE = 'print foo\n'

def check(rec):
    t = rec.get("text", "")
    return (bool(t) and t.replace("null", "") == ""), "text=%r (unset variable is null; print emits null)" % t

def main():
    return probe("L1-05", "未赋值变量是 null；print 输出 null", CODE, check, steps=2)

if __name__ == "__main__":
    raise SystemExit(main())
