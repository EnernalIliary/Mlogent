from _harness import probe

# No ubind: @unit is null; @dead of a null unit reads 1.
CODE = 'sensor d @unit @dead\n'

def check(rec):
    v = (rec.get("vars") or {}).get("d")
    return (str(v) == "1"), "d=%r (no ubind => @unit null; @dead of null unit is 1)" % (v,)

def main():
    return probe("L1-06", "@dead 对 null 单位返回 1", CODE, check, steps=2)

if __name__ == "__main__":
    raise SystemExit(main())
