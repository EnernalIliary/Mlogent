from _harness import probe

# jump target is 0-based: line 0 jumps to line 2, so "A" (line 1) never prints.
# The program wraps around (counter>end resets), hence several B's in 4 steps.
CODE = 'jump 2 always\nprint "A"\nprint "B"\n'

def check(rec):
    t = rec.get("text", "")
    return (t != "" and set(t) == {"B"}), "text=%r (no A => target index is 0-based)" % (t,)

def main():
    return probe("L1-10", "jump N 的指令序号从 0 起算", CODE, check, steps=4)

if __name__ == "__main__":
    raise SystemExit(main())
