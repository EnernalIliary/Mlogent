from _harness import probe

# @counter base is i+1: adding 1 at line 0 lands on line 2, skipping "A".
CODE = 'op add @counter @counter 1\nprint "A"\nprint "B"\n'

def check(rec):
    t = rec.get("text", "")
    return (t != "" and set(t) == {"B"}), "text=%r (B only => base i+1; A would mean base i)" % (t,)

def main():
    return probe("L1-11", "op add @counter 的基址是 i+1", CODE, check, steps=4)

if __name__ == "__main__":
    raise SystemExit(main())
