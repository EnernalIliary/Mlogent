from _harness import probe

# read/write round-trip on a linked memory cell (@this is the processor).
CODE = 'set z 7\nwrite z cell1 0\nread r cell1 0\nprint r\n'

def check(rec):
    t = rec.get("text", "")
    if "r" not in (rec.get("vars") or {}) and t == "":
        return (None, "no cell1 link on the headless map; link a memory cell to run this probe")
    return (str((rec.get("vars") or {}).get("r")) == "7"), "vars.r=%r text=%r" % ((rec.get("vars") or {}).get("r"), t)

def main():
    return probe("L1-16", "read/write 对 @this 指向的处理器变量", CODE, check, steps=5)

if __name__ == "__main__":
    raise SystemExit(main())
