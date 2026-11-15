from _harness import probe

# sin/cos take DEGREES: sin 90 = 1, cos 180 = -1.
CODE = 'op sin r 90\nop cos s 180\nprint r\nprint "|"\nprint s\n'

def check(rec):
    t = rec.get("text", "")
    return (t.startswith("1") and t.endswith("-1")), "text=%r (expect 1|-1; radians would give 0.894/-0.598)" % (t,)

def main():
    return probe("L1-09", "sin/cos/angle 以度为单位", CODE, check, steps=6)

if __name__ == "__main__":
    raise SystemExit(main())
