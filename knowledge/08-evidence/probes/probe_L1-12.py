from _harness import probe

# First tick after enabling does not execute: 1 tick => empty text, 2 ticks => one print.
CODE = 'print "x"\n'

def check(rec):
    t = rec.get("text", "")
    return (t == ""), "text=%r with ticks=1 (empty => first tick consumes without executing)" % (t,)

def main():
    return probe("L1-12", "处理器首 tick 不执行指令", CODE, check, ticks=1)

if __name__ == "__main__":
    raise SystemExit(main())
