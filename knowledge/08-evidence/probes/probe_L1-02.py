from _harness import probe

# "X" once per tick; the "Y" after end must never run.
CODE = 'print "X"\nend\nprint "Y"\n'

def check(rec):
    t = rec.get("text", "")
    return (("Y" not in t) and t.count("X") >= 1), \
        "text=%r (no Y => statements after end never execute)" % (t,)

def main():
    return probe("L1-02", "end 之后的语句永不执行", CODE, check, steps=8)

if __name__ == "__main__":
    raise SystemExit(main())
