"""One-off patch: teach the deadlock rule that `ubind` may or may not progress.

Why: `12硅II构型.msch` L5-L8 is

    ubind @flare
    sensor t @unit @controller
    jump 8 strictEqual t @unit
    jump 4 notEqual t @this

Each pass re-binds a *different* flare, so the loop does terminate -- my first
version excluded `ubind` from LOOP_PROGRESS and reported it as a deadlock.
But `自动重构逻辑.msch` L5-L9 is

    jump 1 equal E 0
    ubind null
    sensor c @unit @controller
    jump 9 strictEqual c @unit
    jump 5 notEqual c @this

and `ubind null` changes nothing, so that one really does spin forever.

So: `ubind <type>` counts as progress (WARN at most), `ubind null` does not
(ERR). The WARN still matters for the generated logic: with a single flare, the
round-robin re-binds the same unit and the guard stays true forever.
"""
import pathlib

P = (pathlib.Path(__file__).resolve().parents[1]
     / "mindustry-blueprint" / "tools" / "mlogcheck.py")
S = P.read_text(encoding="utf-8")

OLD_SCAN = """        mnem = set()
        for k in range(tgt, i + 1):
            parts = stmts[k][1].split()
            if parts:
                mnem.add(parts[0].lower())
"""
NEW_SCAN = """        mnem = set()
        ubind_real = False
        for k in range(tgt, i + 1):
            parts = stmts[k][1].split()
            if not parts:
                continue
            m = parts[0].lower()
            mnem.add(m)
            # `ubind <type>` walks to a different unit next pass, so the loop
            # can make progress. `ubind null` only resets @unit -- it changes
            # nothing the next pass would read differently.
            if m == "ubind" and len(parts) > 1 and parts[1].lower() != "null":
                ubind_real = True
"""

OLD_ERR = '''        if "@this" in guard:
            out.append(Finding(
                "ERR", orig + 1, c,
                f"this loop deadlocks itself: it jumps back to L{head} whenever the "
                f"guard holds, and `@this` can only become the unit's controller "
                f"through a `ucontrol` -- there is none between L{head} and here. So "
                f"the moment the unit is yours the guard stays true forever and "
                f"nothing after this line ever runs (`ubind` is a round-robin, so it "
                f"re-binds the same unit)"))'''

NEW_ERR = '''        if "@this" in guard and ubind_real:
            out.append(Finding(
                "WARN", orig + 1, c,
                f"this loop only leaves once a unit of another controller is bound: "
                f"`ubind` walks the round-robin, but a unit this processor already "
                f"controls keeps `@this` true, so with a single such unit on the map "
                f"the loop spins forever and nothing after this line ever runs"))
        elif "@this" in guard:
            out.append(Finding(
                "ERR", orig + 1, c,
                f"this loop deadlocks itself: it jumps back to L{head} whenever the "
                f"guard holds, and `@this` can only become the unit's controller "
                f"through a `ucontrol` -- there is none between L{head} and here. So "
                f"the moment the unit is yours the guard stays true forever and "
                f"nothing after this line ever runs"))'''

for old, new, tag in ((OLD_SCAN, NEW_SCAN, "scan"), (OLD_ERR, NEW_ERR, "err")):
    assert old in S, f"{tag} anchor not found"
    S = S.replace(old, new)

P.write_text(S, encoding="utf-8")
print("patched mlogcheck.py")
