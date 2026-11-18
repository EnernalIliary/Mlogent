#!/usr/bin/env python3
"""fidelity.py -- what the offline executor reproduces, and what it does not.

`tools/mlogsim.py` runs the real `LExecutor` from the real v160.7 server jar,
but it is not the game: no wave AI, no power graphs, terrain collision only at
"B level", a processor placed by the harness instead of by a player.  That gap
is not a bug and cannot be closed by testing harder -- it has to be *written
down*, or every difference between a simulated run and a live run looks like a
regression.

规划 §3 P2 calls this the Fidelity Envelope.  Each capability carries one of
five verdicts:

    verified     the simulator has been checked against the live game and agrees
    unverified   it runs, nobody has compared it against the game yet
    partial      it runs, but with a known simplification
    unsupported  it does not exist offline; a scenario that needs it is not
                 measurable there
    unknown      nobody knows; treat any claim about it as unproven

`differential.py` annotates every difference with the envelope entry it falls
under, so a report says "known boundary" instead of "mystery".

    python tools/fidelity.py list
    python tools/fidelity.py show unit-motion
    python tools/fidelity.py selftest
"""
from __future__ import annotations

import argparse
import json
import sys

SCHEMA = "mlog-fidelity/v1"

#: The five verdicts, weakest-last is not meaningful: they are a vocabulary, not
#: an ordering.  `partial` and `unsupported` are the ones a report has to name.
VERDICTS = ("verified", "unverified", "partial", "unsupported", "unknown")

#: The envelope.  `scope` is a short human label for what the capability covers;
#: `evidence` points at where the claim comes from (a docstring line, a test, a
#: measured run) so a later reader can re-check it instead of trusting the table.
ENTRIES = [
    {
        "id": "instruction-set",
        "scope": "mlog instruction semantics (the `LExecutor` itself)",
        "verdict": "verified",
        "evidence": "tools/mlogsim.py runs the official server jar's LExecutor; "
                    "tests/shapes and tests/ruleids pin the instruction set",
        "note": "Opcodes, slot counts and numeric behaviour are the game's own code.",
    },
    {
        "id": "tick-model",
        "scope": "@tick / @time / update ordering",
        "verdict": "partial",
        "evidence": "tools/mlogsim.py docstring, 'Tick semantics'",
        "note": "Mindustry adds edelta()*ipt after the instruction loop, so --ticks N "
                "runs N-1 active ticks and @tick starts at 2; saves are re-zeroed. "
                "Measured 2026-11-17: a 240-tick scene against the live world leaves "
                "the loop counter one behind (@counter 4 vs 5) -- a sampling phase, "
                "which is why a log value off by one is annotated here, not excused.",
    },
    {
        "id": "unit-motion",
        "scope": "unit movement from ucontrol move/approach/stop/boost",
        "verdict": "unverified",
        "evidence": "tools/mlogsim.py docstring, 'Units spawned with --units'",
        "note": "Real Unit.update() per tick for LogicAI units, so motion is the "
                "game's code. Measured 2026-11-17 (240 ticks, blank-64 offline vs the "
                "Fork live world): a flare ended ~1.3 tiles apart, and the gap grew "
                "with every re-run -- different terrain and neighbouring units, not a "
                "different integrator. Diff on the same map before calling it a bug.",
    },
    {
        "id": "unit-ai",
        "scope": "non-logic unit AI, waves, map spawns",
        "verdict": "unsupported",
        "evidence": "tools/mlogsim.py: '--unit-ai all' updates the save's own AI, "
                    "but there is no wave scheduler or spawner",
        "note": "A scenario whose outcome depends on enemies arriving on their own is "
                "not measurable offline.",
    },
    {
        "id": "unit-collision",
        "scope": "terrain collision, knockback, unit-unit stacking",
        "verdict": "partial",
        "evidence": "tools/mlogsim.py docstring calls the model 'B level'",
        "note": "Position updates are real; detailed collision resolution is not.",
    },
    {
        "id": "combat",
        "scope": "bullets, damage, kills",
        "verdict": "partial",
        "evidence": "tools/mlogsim.py docstring, 'Combat'",
        "note": "Bullet physics, collide() and weapon mounts run for real under "
                "--ticks; destruction side effects and death edge cases are not modelled.",
    },
    {
        "id": "power",
        "scope": "power graphs, batteries, consumption",
        "verdict": "unsupported",
        "evidence": "tools/mlogsim.py: 'Power graphs are not simulated'",
        "note": "--power pins every consumer's power.status to 1.0 (or 0.0). A design "
                "whose behaviour depends on power shortage cannot be judged offline.",
    },
    {
        "id": "logistics",
        "scope": "conveyors, drills, factories, item transport",
        "verdict": "unverified",
        "evidence": "tools/mlogsim.py: '--update all' calls Building.update() per tick",
        "note": "The real block update runs, but throughput/timing has not been "
                "compared against the live world.",
    },
    {
        "id": "liquid",
        "scope": "liquid networks, tanks, pumps",
        "verdict": "unverified",
        "evidence": "same Building.update() path as logistics",
        "note": "No dedicated parity run yet.",
    },
    {
        "id": "weather",
        "scope": "weather state machine and weathersense",
        "verdict": "unverified",
        "evidence": "tools/mlogsim.py docstring, 'Weather'",
        "note": "The real state machine with a fixed seed is driven, so runs repeat; "
                "agreement with a live world is untested.",
    },
    {
        "id": "logic-links",
        "scope": "processor links and cross-processor reads",
        "verdict": "partial",
        "evidence": "tools/mlogsim.py docstring, 'Links'",
        "note": "A plain .mlog gets auto-wired links for cell1/message1/... on free "
                "tiles; a .msch keeps its own exact link table.",
    },
    {
        "id": "processor-placement",
        "scope": "where the harness puts the processor",
        "verdict": "partial",
        "evidence": "tools/mlogsim.py: auto-placed beside the core, --base overrides",
        "note": "A player-designed layout can differ in link distance and adjacency; "
                "use --base or a schematic when that matters.",
    },
    {
        "id": "text-buffer",
        "scope": "print buffer size",
        "verdict": "verified",
        "evidence": "tools/mlogsim.py: 'capped by the game at maxTextBuffer = 400 chars'",
        "note": "This is the game's own cap; long output is truncated, not lost.",
    },
    {
        "id": "map-terrain",
        "scope": "terrain, ores, map size",
        "verdict": "partial",
        "evidence": "tools/mlogsim.py: blank 64x64 by default, --world / --host / saves",
        "note": "A blank map is fine for logic and wrong for anything that reads tiles; "
                "load the real save (--save) when the layout matters.",
    },
    {
        "id": "world-clock",
        "scope": "@time / @tick base value, save clock",
        "verdict": "partial",
        "evidence": "tools/mlogsim.py: the save's world clock is reset to 0",
        "note": "Makes runs repeatable, but a program that reads an absolute wall clock "
                "will see different numbers than in a long-running world.",
    },
]

_BY_ID = {e["id"]: e for e in ENTRIES}


def load() -> dict:
    """The whole envelope, as it is written to reports."""
    return {"schema": SCHEMA, "verdicts": list(VERDICTS),
            "entries": [dict(e) for e in ENTRIES]}


def lookup(capability: str) -> dict | None:
    """Entry by id, or None.  Case/space tolerant so a report can pass its own text."""
    key = str(capability or "").strip().lower()
    if key in _BY_ID:
        return dict(_BY_ID[key])
    return None


def annotate(difference: dict) -> str | None:
    """Map one `compare()` difference onto the envelope entry that explains it.

    The match is deliberately conservative: a difference carries a `path` like
    `state.units[flare#0].x` or `events[tick=12,type=print]`; only an explicit
    `capability` hint, or a path whose prefix names a known area, is annotated.
    Anything else returns None so the caller reports it as unexplained -- silence
    is better than a wrong alibi.
    """
    if not isinstance(difference, dict):
        return None
    hint = difference.get("capability")
    if hint:
        entry = lookup(str(hint))
        if entry:
            return _line(entry)
        return None
    path = str(difference.get("path") or "")
    left = difference.get("left")
    right = difference.get("right")
    # Path prefixes know their own area; the mapping is intentionally short so
    # that a new area shows up as unexplained instead of silently absorbed.
    area = ""
    if path.startswith("state.units"):
        # Only the fields that come out of Unit.update() inherit the physics
        # boundary.  What a unit carries, who owns it and which type it is are
        # decided by the instructions (ubind/unit itemTake/unit control), so a
        # difference there is real and must stay unexplained.
        tail = path.rsplit(".", 1)[-1].strip("]")
        if "hp" in path:
            area = "combat"
        elif tail in _MOTION_FIELDS:
            area = "unit-motion"
        else:
            area = ""
    elif path.startswith("state.buildings"):
        area = "logistics"
    elif path.startswith("state.core"):
        area = "logistics"
    elif path.startswith("events"):
        area = "tick-model"
    elif path.startswith("state.logs"):
        # A processor variable that mirrors a physical quantity inherits that
        # quantity's boundary; a counter that is off by one is a sampling-phase
        # artefact; anything larger stays unexplained (instruction-set is
        # `verified`, and a verified area never gets to excuse a difference).
        tail = path.rsplit(".", 1)[-1]
        if tail in _PHYSICAL_VARS:
            area = "unit-motion"
        elif _near(left, right, 1.0):
            area = "tick-model"
        else:
            area = "instruction-set"
    if not area:
        return None
    entry = lookup(area)
    if not entry or entry["verdict"] == "verified":
        return None
    return _line(entry)


#: Processor variables that are copies of something physical, so a difference in
#: them belongs to the physics boundary rather than to the instruction set.
_PHYSICAL_VARS = {"x", "y", "ux", "uy", "hp", "uhp", "shx", "shy", "health"}

#: Unit fields that are positions/velocities, i.e. what Unit.update() moves.
_MOTION_FIELDS = {"x", "y", "ux", "uy", "rot", "shx", "shy", "speed", "velocity"}


def _near(left, right, limit: float) -> bool:
    """True when both sides parse as numbers and differ by at most `limit`."""
    try:
        return abs(float(left) - float(right)) <= limit
    except (TypeError, ValueError):
        return False


def _line(entry: dict) -> str:
    return "%s (%s): %s" % (entry["id"], entry["verdict"], entry["note"])


def selftest() -> int:
    problems = []
    ids = [e["id"] for e in ENTRIES]
    if len(ids) != len(set(ids)):
        problems.append("duplicate entry ids")
    for e in ENTRIES:
        for key in ("id", "scope", "verdict", "evidence", "note"):
            if not str(e.get(key) or "").strip():
                problems.append("entry %r has empty %s" % (e.get("id"), key))
        if e["verdict"] not in VERDICTS:
            problems.append("entry %r has verdict %r" % (e["id"], e["verdict"]))
    if json.loads(json.dumps(load())) != load():
        problems.append("envelope is not JSON-round-trippable")
    if lookup("Unit-Motion") is None:
        problems.append("lookup is not case tolerant")
    if lookup("no-such-capability") is not None:
        problems.append("lookup invents entries")
    ann = annotate({"path": "state.logs.ctrl.n", "left": "79", "right": "80",
                    "rule": "exact"})
    if not ann or "tick-model" not in ann:
        problems.append("a counter off by one is not attributed to the tick model")
    ann = annotate({"path": "state.logs.ctrl.ux", "left": "40.0",
                    "right": "39.0", "rule": "exact"})
    if not ann or "unit-motion" not in ann:
        problems.append("a variable mirroring a position is not attributed to motion")
    ann = annotate({"path": "state.logs.ctrl.n", "left": "79", "right": "40",
                    "rule": "exact"})
    if ann:
        problems.append("a large counter difference is excused, not reported")
    ann = annotate({"path": "state.logs.ctrl.logic", "left": "a", "right": "b",
                    "rule": "exact"})
    if ann:
        problems.append("a non-numeric log difference is excused, not reported")
    ann = annotate({"path": "state.units[flare#0].x", "rule": "tolerance"})
    if not ann or "unit-motion" not in ann:
        problems.append("unit differences are not annotated: %r" % (ann,))
    if annotate({"path": "state.logs.p.mode"}) is not None:
        problems.append("a verified area must not be annotated as a boundary")
    if annotate({"path": "something.else"}) is not None:
        problems.append("unknown paths must stay unexplained")
    if annotate({"path": "x", "capability": "power"}) is None:
        problems.append("explicit capability hints are ignored")
    for p in problems:
        print("FAIL " + p)
    if not problems:
        print("all fidelity checks passed (%d entries)" % len(ENTRIES))
    return 1 if problems else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Fidelity envelope for the offline mlog executor")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("list", help="every entry, one line each")
    show = sub.add_parser("show", help="one entry in full")
    show.add_argument("id")
    dump = sub.add_parser("dump", help="the envelope as JSON")
    dump.add_argument("--json", action="store_true")
    sub.add_parser("selftest")
    args = ap.parse_args(argv)

    if args.cmd == "list":
        for e in ENTRIES:
            print("%-20s %-11s %s" % (e["id"], e["verdict"], e["scope"]))
        return 0
    if args.cmd == "show":
        e = lookup(args.id)
        if not e:
            sys.stderr.write("unknown capability %r (try: python tools/fidelity.py list)\n"
                             % (args.id,))
            return 2
        for k in ("id", "scope", "verdict", "evidence", "note"):
            print("%-9s %s" % (k + ":", e[k]))
        return 0
    if args.cmd == "dump":
        print(json.dumps(load(), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "selftest":
        return selftest()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
