from _harness import probe

# memory-cell capacity is read back from the block itself (@memoryCapacity):
# in-range unset cells read 0; index >= capacity (and negatives) read null/NaN.
# Source: MemoryBlock.java:65-69 has the literal comment
#   "//Return null when out of bounds. (instead of 0)"
CODE = ('sensor cap cell1 @memoryCapacity\n'
        'read a cell1 0\nread b cell1 63\nread c cell1 64\nread d cell1 -1\n'
        'print cap\nprint "|"\nprint a\nprint b\nprint c\nprint d\n')

def check(rec):
    v = rec.get("vars") or {}
    if "cell1" not in v:
        return (None, "no cell1 link in this run")
    cap = v.get("cap")
    got = (v.get("a"), v.get("b"), v.get("c"), v.get("d"))
    oob_null = str(got[2]) == "null" and str(got[3]) == "null"
    in_zero = str(got[0]) == "0" and str(got[1]) == "0"
    if in_zero and oob_null:
        return (False, "cap=%r: in-range unset reads 0, but OOB reads null (claim says 0) => claim contradicted" % (cap,))
    return (None, "cap=%r a/b/c/d=%r" % (cap, got))

def main():
    return probe("L1-18", "记忆格越界读出 0（实测 null，见 README 冲突一节）", CODE, check, steps=9)


if __name__ == "__main__":
    raise SystemExit(main())
