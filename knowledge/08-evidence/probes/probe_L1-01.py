from _harness import probe

CODE = 'print @tick\nend\n'

def check(rec):
    t = rec.get("text", "")
    consec = t.isdigit() and all(int(b) == int(a) + 1 for a, b in zip(t, t[1:]))
    return (bool(t) and consec), "text=%r (consecutive per-tick digits => end resets to 0, next tick reruns)" % t

def main():
    return probe("L1-01", "执行到 end 后 @counter 归 0，下一 tick 从头跑", CODE, check, ticks=3)

if __name__ == "__main__":
    raise SystemExit(main())
