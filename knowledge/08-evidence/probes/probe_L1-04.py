from _harness import probe

CODE = 'print "A"\njump -1 always\n'

def check(rec):
    t = rec.get("text", "")
    return (bool(t) and set(t) == {"A"}), "text=%r (counter<0 reset to 0 => rerun from top, not a nop)" % t

def main():
    return probe("L1-04", "jump -1 不是 nop：counter<0 被重置为 0，等于从头跑", CODE, check, steps=8)

if __name__ == "__main__":
    raise SystemExit(main())
