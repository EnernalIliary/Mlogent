from _harness import probe

# logn 0 2 (log base 0) and 1/0 (div by zero) both yield null, not 0/Inf.
CODE = 'op logn r 0 2\nop div s 1 0\nprint r\nprint "|"\nprint s\n'

def check(rec):
    t = rec.get("text", "")
    v = rec.get("vars") or {}
    return (t == "null|null" and str(v.get("r")) == "null" and str(v.get("s")) == "null"), \
        "text=%r r=%r s=%r (logn 0 and 1/0 both yield null)" % (t, v.get("r"), v.get("s"))

def main():
    return probe("L1-08", "logn 0 2 与 1/0 均得 null", CODE, check, steps=6)

if __name__ == "__main__":
    raise SystemExit(main())
