from _harness import probe

# print consumes exactly one argument; the extra token is dropped, no error.
CODE = 'print "a" "b"\nprint "c"\n'

def check(rec):
    t = rec.get("text", "")
    return (t != "" and "b" not in t and t.startswith("ac")), "text=%r (extra 2nd arg dropped, no crash)" % (t,)

def main():
    return probe("L1-13", "print 只取 1 个参数", CODE, check, steps=4)

if __name__ == "__main__":
    raise SystemExit(main())
