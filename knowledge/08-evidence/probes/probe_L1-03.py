from _harness import probe

CODE = 'print @tick\njump 0 always\n'

def check(rec):
    t = rec.get("text", "")
    consec = t.isdigit() and all(int(b) == int(a) + 1 for a, b in zip(t, t[1:]))
    return (bool(t) and consec), "text=%r (same shape as L1-01 => jump 0 always == end)" % t

def main():
    return probe("L1-03", "jump 0 always 与 end 等价（都归 0）", CODE, check, ticks=3)

if __name__ == "__main__":
    raise SystemExit(main())
