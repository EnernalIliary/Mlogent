from _harness import probe

# x 未赋值: equal x null 为真则跳到第 2 条 (print "T")，为假则落到第 1 条 print "F"
CODE = 'jump 2 equal x null\nprint "F"\nprint "T"\nend\n'

def check(rec):
    t = rec.get("text", "")
    return (bool(t) and set(t) == {"T"}), "text=%r (only T branch taken => equal x null true)" % t

def main():
    return probe("L1-07", "null.num()==0，故 equal x null 对未赋值 x 为真", CODE, check, steps=6)

if __name__ == "__main__":
    raise SystemExit(main())
