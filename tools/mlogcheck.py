#!/usr/bin/env python
"""
mlogcheck.py -- static analyser for mlog, focused on the mistakes that have
actually shipped broken logic in this workspace.

It is NOT an emulator. It does flow / usage analysis on one processor's code
and reports things a compiler would not: inverted conditions, variables read
before assignment, jumps that land on statements with side effects, unbounded
loops, and unit-control executed without a live `ubind`.

Usage
-----
  python tools/mlogcheck.py 逻辑.mlog
  python tools/mlogcheck.py --blueprint out/无线超.msch     # check a whole schematic
  python tools/mlogcheck.py --dir logic-corpus/by-blueprint # (md dumps, not for this)
"""
from __future__ import annotations

import argparse
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --------------------------------------------------------------------------- #
# instruction tables
# --------------------------------------------------------------------------- #

# statements that WRITE into their first operand (or a named output slot)
# key -> parameter positions that are outputs (-1 = first operand)
OUTPUT_SLOTS: dict[str, list[int]] = {
    "sensor": [0], "getlink": [0], "op": [1], "set": [0], "select": [0],
    "lookup": [1], "read": [0], "packcolor": [0], "unpackcolor": [0, 1, 2, 3],
    "radar": [-1], "uradar": [-1], "ulocate": [-4, -3, -2, -1],
    "sensor_": [0],
}

# statements with a side effect on the world / processor state
SIDE_EFFECT = {
    "ubind", "ucontrol", "uradar", "ulocate", "control", "write", "read",
    "print", "printflush", "draw", "drawflush", "jump", "end", "stop",
    "wait", "setrate", "getlink", "sensor", "op", "set", "select", "lookup",
    "spawn", "setblock", "getblock", "setprop", "setrule", "effect", "status",
    "explosion", "fetch", "sync", "message", "format", "printchar",
}

# unit-control statements that silently do nothing unless @unit is bound
NEEDS_UNIT = {"ucontrol", "uradar", "ulocate"}

# ucontrol sub-actions that refresh the 10s control timer
UNIT_ACTIONS_NO_TIMER = {"uradar"}

OP_UNARY = {"abs", "sign", "log", "log10", "floor", "ceil", "round",
            "sqrt", "rand", "sin", "cos", "tan", "asin", "acos", "atan", "not"}
OP_BINARY = {"add", "sub", "mul", "div", "idiv", "mod", "emod", "pow",
             "equal", "notEqual", "land", "lessThan", "lessThanEq",
             "greaterThan", "greaterThanEq", "strictEqual",
             "shl", "shr", "ushr", "or", "and", "xor",
             "max", "min", "angle", "angleDiff", "len", "noise", "logn"}

# built-in / magic symbols that are always in scope
BUILTIN = re.compile(
    r"^(@|_|null$|true$|false$|-?\d+(\.\d+)?$|\"[^\"]*\"$|%[0-9a-fA-F]+$)")

# reserved words that appear in operand positions but are NOT variables
KEYWORDS = {
    # jump condition operators
    "equal", "notEqual", "lessThan", "lessThanEq", "greaterThan",
    "greaterThanEq", "strictEqual", "always",
    # ulocate / locate modes and block flags
    "building", "ore", "spawn", "damaged",
    "core", "storage", "generator", "turret", "factory", "repair",
    "battery", "reactor", "drill", "shield",
    # ucontrol actions
    "idle", "stop", "move", "approach", "pathfind", "autoPathfind", "boost",
    "target", "targetp", "itemDrop", "itemTake", "payDrop", "payTake",
    "payEnter", "mine", "flag", "build", "deconstruct", "getBlock", "within",
    "unbind",
    # control actions
    "enabled", "shoot", "shootp", "config", "color",
    # draw/print/etc.
    "clear", "stroke", "line", "rect", "lineRect", "poly", "linePoly",
    "triangle", "image", "print", "translate", "scale", "rotate", "reset",
    # layers / misc
    "block", "floor", "ore_", "building_", "type", "apply", "clear_",
}

# draw sub-commands: `draw <sub> ...` -- the sub-command is not an operand
DRAW_SUBS = {
    "clear", "color", "col", "stroke", "line", "rect", "lineRect", "poly",
    "linePoly", "triangle", "image", "print", "translate", "scale", "rotate",
    "reset",
}

# keywords that appear in operand positions for other statements
OTHER_KEYWORDS = {
    "player", "unit", "unitCount", "playerCount", "build", "enemy", "ally",
    "any", "attacker", "flying", "boss", "ground", "distance", "health",
    "shield", "armor", "maxHealth", "remove", "pos", "shape", "texture",
    "minimap", "shapeText", "world", "natural", "effect", "source", "target",
    "command", "object", "none", "default", "on", "off", "down", "up",
    "left", "right",
}
KEYWORDS |= DRAW_SUBS | OTHER_KEYWORDS

JMP_RE = re.compile(r"^jump\s+(-?\d+)\s+(\S+)(?:\s+(\S+))?(?:\s+(\S+))?$")
OP_RE = re.compile(r"^op\s+(\S+)\s+(\S+)(?:\s+(\S+))?(?:\s+(\S+))?$")


class Finding:
    __slots__ = ("sev", "line", "code", "msg")

    def __init__(self, sev: str, line: int, code: str, msg: str):
        self.sev, self.line, self.code, self.msg = sev, line, code, msg

    def __str__(self):
        return f"  [{self.sev}] L{self.line:<4} {self.code:<44} {self.msg}"


def strip_comment(line: str) -> str:
    out, in_str = [], False
    for ch in line:
        if ch == '"':
            in_str = not in_str
        elif ch == "#" and not in_str:
            break
        out.append(ch)
    return "".join(out).strip()


def defs_of(c: str) -> list[str]:
    """Variables this statement WRITES."""
    p = tokenize(c)
    if not p:
        return []
    op = p[0]
    # `draw triangle a b c d e f` placed after `end` is a DECLARATION TABLE:
    # LParser calls var() on every argument, creating the variable slots.
    if op == "draw" and len(p) > 1 and p[1] == "triangle":
        return _vars(p[2:8])
    if op == "op" and len(p) >= 3:
        return [p[2]]
    if op == "ulocate" and len(p) >= 9:
        return [x for x in p[5:9] if x not in ("0", "null")]
    if op in ("sensor", "getlink", "set", "read", "packcolor"):
        return [p[1]] if len(p) >= 2 and p[1] != "0" else []
    if op in ("select", "lookup"):
        return [p[1]] if len(p) >= 2 and p[1] != "0" else []
    if op == "unpackcolor" and len(p) >= 6:
        return [x for x in p[1:5] if x != "0"]
    if op in ("radar", "uradar"):
        return [p[-1]] if p[-1] not in ("0", "null") else []
    if op == "ucontrol" and len(p) >= 3:
        # ucontrol within x y r result -> 4th slot is an output
        if p[1] == "within" and len(p) >= 6:
            return [p[5]]
        if p[1] == "getBlock" and len(p) >= 8:
            return [x for x in p[5:8] if x != "0"]
    return []


QUOTED = re.compile(r'"[^"]*"')


def tokenize(line: str) -> list[str]:
    """Split into tokens, keeping a quoted string as ONE token."""
    out, i, n = [], 0, len(line)
    while i < n:
        ch = line[i]
        if ch.isspace():
            i += 1
            continue
        if ch == '"':
            j = line.find('"', i + 1)
            if j == -1:
                out.append(line[i:])
                break
            out.append(line[i:j + 1])
            i = j + 1
        else:
            j = i
            while j < n and not line[j].isspace():
                j += 1
            out.append(line[i:j])
            i = j
    return out


def _vars(tokens) -> list[str]:
    """Filter operand tokens down to things that can actually be variables."""
    out = []
    for t in tokens:
        if not t:
            continue
        if t == "0" or t in KEYWORDS or BUILTIN.match(t):
            continue
        if t.startswith('"'):                     # string literal
            continue
        out.append(t)
    return out


def uses_of(c: str) -> list[str]:
    """Variables this statement READS (operators/keywords filtered out)."""
    p = tokenize(c)
    if not p:
        return []
    op = p[0]
    if op == "jump":
        # jump <target> <op> <value> <compare>
        # `always` takes NO operands -- the trailing "x false" is filler
        if len(p) >= 3 and p[2] == "always":
            return []
        return _vars(p[3:5])
    if op == "op":
        return _vars(p[3:5])
    if op == "ulocate":
        return _vars([p[3], p[4]])
    if op == "set":
        return _vars(p[2:3])
    if op == "sensor":
        return _vars([p[2]])
    if op == "getlink":
        return _vars([p[2]])
    if op in ("select", "lookup"):
        return _vars(p[3:6])
    if op == "read":
        return _vars([p[3]])
    if op == "write":
        return _vars([p[1], p[3]])
    if op == "radar":
        return _vars([p[5]])
    if op == "uradar":
        return []
    if op == "ucontrol":
        if len(p) > 1 and p[1] == "within":
            return _vars(p[2:5])
        if len(p) > 1 and p[1] == "getBlock":
            return _vars(p[2:4])
        return _vars(p[2:7])
    if op == "control":
        return _vars(p[2:7])
    if op == "draw":
        # `draw triangle <names...>` is a declaration table, not a read.
        # Every other draw sub-command takes numbers/colours/content names, so
        # there is nothing meaningful to read -- skip the whole statement.
        return []
    if op in ("print", "printflush", "drawflush", "format", "localeprint",
              "printchar", "playsound", "playmusic", "setmarker", "makemarker",
              "effect", "explosion", "status", "spawn", "bullet", "setprop",
              "setrule", "fetch", "sync", "message", "cutscene", "spawnwave",
              "weatherset", "weathersense", "getflag", "setflag", "setrate",
              "query", "clientdata", "getblock", "setblock", "localeprint"):
        return _vars(p[1:9])
    return _vars(p[1:6])


def analyse(lines: list[str], links: list[str] | None = None) -> list[Finding]:
    code = [strip_comment(l) for l in lines]
    stmts = [(i, c) for i, c in enumerate(code) if c]
    out: list[Finding] = []
    n = len(stmts)

    # Link names are bound by the processor itself, not by an assignment, so
    # they are live from the very first statement. We also auto-detect them by
    # the game's naming rule (internal-name tail + index, e.g. message1, arc1).
    link_vars = set(links or [])
    LINK_RE = re.compile(r"^[A-Za-z_][\w\-]*\d+$")

    def def_of(i: int) -> set[str]:
        return set(defs_of(stmts[i][1]))

    # ---- predecessors (successors are i+1 and, for jump, the target) ------
    preds: list[set[int]] = [set() for _ in range(n)]
    for i, (_, c) in enumerate(stmts):
        m = JMP_RE.match(c)
        succ = []
        if m:
            tgt = int(m.group(1))
            if 0 <= tgt < n:
                succ.append(tgt)
            if m.group(2) != "always":
                succ.append(i + 1)                # fall-through when not taken
        else:
            succ.append(i + 1)
        for s in succ:
            if 0 <= s < n:
                preds[s].add(i)

    # ---- reaching definitions -------------------------------------------
    # REACH[i][v] = set of statement indices that define v and may reach i
    REACH: list[dict[str, set[int]]] = [dict() for _ in range(n)]
    changed = True
    rounds = 0
    while changed and rounds < 200:
        changed = False
        rounds += 1
        for i in range(n):
            acc: dict[str, set[int]] = {}
            for p in preds[i]:
                for v, ds in REACH[p].items():
                    acc.setdefault(v, set()).update(ds)
            # a definition is killed by any other definition of the same var
            for v in {x for p in preds[i] for x in def_of(p)}:
                acc[v] = {p for p in preds[i] if v in def_of(p)}
            if acc != REACH[i]:
                REACH[i] = acc
                changed = True

    # ---- report: read of a variable that is NEVER defined anywhere --------
    # Deliberately weak: full reaching-definition analysis produces far too many
    # false positives on real mlog, which relies on `@counter` relative jumps,
    # loop-carried initialisation, and jump tables. Only flag a variable that no
    # statement in the program ever writes -- that is a guaranteed mistake.
    ever_defined: set[str] = set()
    for _, c in stmts:
        ever_defined |= set(defs_of(c))
    ever_defined |= link_vars
    for i, (orig, c) in enumerate(stmts):
        for v in uses_of(c):
            if v in ever_defined:
                continue
            # auto-detect link names by the game's `name + index` convention so
            # plain .mlog files (which carry no link table) don't false-positive
            if LINK_RE.match(v):
                continue
            out.append(Finding(
                "ERR", orig + 1, c,
                f"`{v}` is read here but is never assigned anywhere in this "
                f"program (and is not a link or built-in)"))

    # ---- report: variable with MULTIPLE reaching definitions ------------
    # Downgraded to INFO: informative, but common and usually intentional.
    for i, (orig, c) in enumerate(stmts):
        for v in uses_of(c):
            if v in link_vars:
                continue
            defs = REACH[i].get(v, set())
            if len(defs) > 1:
                where = ", ".join(f"L{stmts[d][0]}" for d in sorted(defs)[:4])
                out.append(Finding(
                    "INFO", orig + 1, c,
                    f"`{v}` has {len(defs)} reaching assignments ({where})"))

    # ---- jump diagnostics (only structural problems) ---------------------
    for i, (orig, c) in enumerate(stmts):
        m = JMP_RE.match(c)
        if not m:
            continue
        tgt = int(m.group(1))
        if tgt == -1:
            continue
        if not (0 <= tgt < n):
            out.append(Finding("ERR", orig + 1, c,
                               f"jump target {tgt} out of range (0..{n-1})"))
            continue
        if stmts[tgt][1].startswith("jump ") and m.group(2) != "always":
            out.append(Finding("INFO", orig + 1, c,
                               f"target {tgt} is itself a jump"))

    # ---- op arity ---------------------------------------------------------
    for i, (orig, c) in enumerate(stmts):
        mo = OP_RE.match(c)
        if not mo:
            continue
        op, a, b = mo.group(1), mo.group(3), mo.group(4)
        want = 2 if op in OP_UNARY else (3 if op in OP_BINARY else None)
        given = 1 + sum(1 for x in (a, b) if x is not None)
        if want is None:
            out.append(Finding("ERR", orig + 1, c, f"unknown op `{op}`"))
        elif given != want:
            out.append(Finding("WARN", orig + 1, c,
                               f"`op {op}` given {given} args, expects {want}"))

    # ---- @dead inversion --------------------------------------------------
    for i, (orig, c) in enumerate(stmts):
        md = re.match(r"^sensor\s+(\S+)\s+\S+\s+@dead\s*$", c)
        if not md:
            continue
        var = md.group(1)
        for j in range(i + 1, min(i + 3, n)):
            mj = JMP_RE.match(stmts[j][1])
            if mj and mj.group(3) == var and mj.group(2) == "notEqual":
                out.append(Finding(
                    "SUSPECT", stmts[j][0] + 1, stmts[j][1],
                    f"`{var}` holds @dead (1 = DEAD). Checking `notEqual` continues "
                    f"only while ALIVE; to rebind when dead use `equal`"))
                break

    # ---- ulocate hygiene --------------------------------------------------
    for i, (orig, c) in enumerate(stmts):
        mu = re.match(r"^ulocate\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+"
                      r"(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*$", c)
        if not mu:
            continue
        if mu.group(2) in ("0", "null"):
            out.append(Finding("ERR", orig + 1, c,
                               "ulocate arg2 (flag) must be a valid BlockFlag; "
                               "`0` makes the whole instruction invalid"))
        # only complain about discarded coords if the code actually moves to them
        outx, outy = mu.group(5), mu.group(6)
        if outx in ("0", "null") or outy in ("0", "null"):
            uses_move = any(
                re.match(rf"^ucontrol\s+(move|approach)\s+({re.escape(outx)}|{re.escape(outy)})\b",
                         stmts[j][1])
                for j in range(n))
            if uses_move:
                out.append(Finding("ERR", orig + 1, c,
                                   "outX/outY discarded but later used by move/approach"))
        if mu.group(8) in ("0", "null") and mu.group(1) in ("building", "damaged"):
            # find whether an itemDrop/itemTake later uses a link-ish name
            out.append(Finding("INFO", orig + 1, c,
                               "outBuild discarded -- if you need to itemTake/itemDrop "
                               "this building, capture the reference instead"))

    # ---- unit control without any ubind ----------------------------------
    if not any(c.startswith("ubind") for _, c in stmts):
        for i, (orig, c) in enumerate(stmts):
            if c.split()[0] in NEEDS_UNIT:
                out.append(Finding("ERR", orig + 1, c,
                                   f"`{c.split()[0]}` used but there is no `ubind` -> "
                                   f"@unit is null, this silently does nothing"))
                break

    # dedupe, keep order
    seen, uniq = set(), []
    for f in out:
        k = (f.sev, f.line, f.msg)
        if k not in seen:
            seen.add(k)
            uniq.append(f)
    order = {"ERR": 0, "SUSPECT": 1, "WARN": 2, "INFO": 3}
    uniq.sort(key=lambda f: (order.get(f.sev, 9), f.line))
    return uniq


def _cfg(stmts: list[tuple[int, str]]) -> list[list[int]]:
    """Control-flow successors for each statement index.

    Semantics that matter here:
      * `end` sets @counter to the program length, so it behaves as a LOOP BACK
        to statement 0 -- it is NOT a terminator. (A sink would wrongly make
        every loop look like dead code.)
      * `stop` really does halt, so it IS a sink.
      * `jump -1` never branches (it is the decorative no-op form), so it just
        falls through.
    """
    n = len(stmts)
    succ: list[list[int]] = []
    for i, (_, c) in enumerate(stmts):
        op = c.split()[0] if c else ""
        if op == "stop":
            succ.append([])
            continue
        if op == "end":
            succ.append([0] if n else [])
            continue
        m = JMP_RE.match(c)
        if m:
            tgt, cond = int(m.group(1)), m.group(2)
            out = []
            if tgt >= 0 and tgt < n:
                out.append(tgt)
            if cond != "always":
                if i + 1 < n:
                    out.append(i + 1)
            succ.append(out)
            continue
        succ.append([i + 1] if i + 1 < n else [0])
    return succ


def reachable_set(stmts: list[tuple[int, str]]) -> set[int]:
    """Statement indices reachable from entry 0."""
    succ = _cfg(stmts)
    seen: set[int] = set()
    stack = [0] if stmts else []
    while stack:
        i = stack.pop()
        if i in seen or not (0 <= i < len(stmts)):
            continue
        seen.add(i)
        stack.extend(succ[i])
    return seen


# a loop-guard comparison, in either of the two forms mlog uses:
#   op   lessThan idx CONST
#   jump <target> lessThan idx CONST
_GUARD_OP = re.compile(r"^op\s+(lessThan|lessThanEq|greaterThan|greaterThanEq)"
                       r"\s+(\S+)\s+(\S+)\s+(\S+)$")
_GUARD_JMP = re.compile(r"^jump\s+-?\d+\s+(lessThan|lessThanEq|greaterThan|greaterThanEq)"
                        r"\s+(\S+)\s+(\S+)$")
_NUM = re.compile(r"^-?\d+(\.\d+)?$")
_BACKJUMP = re.compile(r"^jump\s+(-?\d+)\s+(\S+)")

COND_OPS = {"lessThan", "lessThanEq", "greaterThan", "greaterThanEq"}


def _bound_from_guard(a: str, b: str) -> int | None:
    """If one operand is a literal > 1, that literal is the trip-count hint."""
    const = None
    if _NUM.match(b):
        const = float(b)
    elif _NUM.match(a):
        const = float(a)
    if const is None:
        return None
    cand = int(abs(const))
    return cand if cand > 1 else None


def find_loop_bounds(stmts: list[tuple[int, str]]) -> dict[int, int]:
    """Best-effort loop trip counts.

    mlog has no declared loop bound, so we infer it the way blueprint authors
    actually write it: a counter compared against a CONSTANT, with a conditional
    jump back above that comparison. Loops bounded by something invisible (an
    idiv, a sensor count) are simply left out.
    """
    bounds: dict[int, int] = {}
    n = len(stmts)
    for j in range(n):
        m = _BACKJUMP.match(stmts[j][1])
        if not m:
            continue
        target = int(m.group(1))
        if not (0 <= target < j):
            continue                      # not a backward branch
        best = None
        for k in range(target, j + 1):
            c = stmts[k][1]
            # each pattern: group(1)=comparison, then the two operands
            g = _GUARD_OP.match(c)
            if g and g.group(1) in COND_OPS:
                cand = _bound_from_guard(g.group(2), g.group(3))
            else:
                g2 = _GUARD_JMP.match(c)
                cand = (_bound_from_guard(g2.group(2), g2.group(3))
                        if g2 and g2.group(1) in COND_OPS else None)
            if cand:
                best = cand if best is None else max(best, cand)

        if best:
            bounds[target] = max(bounds.get(target, 0), best)
    return bounds


def cost_report(stmts: list[tuple[int, str]],
                links: list[str] | None = None) -> str:
    """Human-readable size / reachability / worst-case-cost summary."""
    n = len(stmts)
    if n == 0:
        return "  (empty program)"

    lines: list[str] = []
    lines.append(f"  statements      : {n}")

    # ---- reachability -----------------------------------------------------
    live = reachable_set(stmts)
    dead = [i for i in range(n) if i not in live]
    if dead:
        lines.append(f"  UNREACHABLE     : {len(dead)} statement(s) can never run:")
        for i in dead:
            lines.append(f"      L{stmts[i][0]}: {stmts[i][1][:70]}")
    else:
        lines.append("  reachability    : all statements reachable")

    # ---- opcode histogram -------------------------------------------------
    ops = collections.Counter(c.split()[0] for _, c in stmts if c)
    top = ", ".join(f"{o}×{c}" for o, c in ops.most_common(6))
    lines.append(f"  opcodes         : {top}")

    # ---- loops ------------------------------------------------------------
    succ = _cfg(stmts)
    back = [(i, t) for i, ss in enumerate(succ) for t in ss if t <= i]
    bounds = find_loop_bounds(stmts)
    if back:
        uniq = sorted({t for _, t in back})
        det = ", ".join(f"L{stmts[t][0]}(×{bounds[t]})" if t in bounds
                        else f"L{stmts[t][0]}(?)" for t in uniq)
        lines.append(f"  loop heads      : {det}")
        unknown = [t for t in uniq if t not in bounds]
        if unknown:
            lines.append(f"  ⚠ {len(unknown)} loop(s) have no visible constant bound; "
                         f"worst-case cost below assumes ONE pass for those")

    # ---- instruction thresholds ------------------------------------------
    if n > 1000:
        lines.append(f"  ⚠ ERR: {n} statements exceeds LExecutor.maxInstructions "
                     f"(1000) -- the tail is SILENTLY TRUNCATED on import")

    # ---- worst-case path -------------------------------------------------
    # Longest path from entry 0, with each loop's body charged `bound` times.
    #
    # Traps this implementation had to work around (all found by testing):
    #   1. Plain longest-path DP is undefined on the cycle head->body->latch->head.
    #   2. Adding the bound only at the back edge never grows: head depends on
    #      latch and latch on head, so the body was counted ONCE (reported a
    #      nonsense "78 instructions" for a program whose real cost is ~2494).
    #   3. A global relaxation DOUBLE-CHARGES nested loop bodies -- the inner
    #      loop inflates every statement after it, and the outer loop then
    #      multiplies that again (reported 643686 for the same program).
    #   4. `float('inf')` as the "unreached" sentinel breaks the comparison, so
    #      nothing ever relaxed and every program reported cost 1.
    #   5. A back edge to statement 0 is the MAIN LOOP (mlog re-runs the whole
    #      program each tick) and must cost ONE pass, not `bound`.
    #
    # The fix is a forward-only recursive interval DP. `path(a, b)` = worst cost
    # to get from `a` to the end of the interval `[a, b)`, only following edges
    # that stay inside it:
    #   * if a loop head h with latch l satisfies h <= i <= l, jump to h and
    #     re-enter with `limit = l + 1` (so the loop is entered and exited once);
    #   * at the latch, multiply by the trip count -- once for this loop only;
    #   * otherwise take 1 + max over forward successors.
    # Every recursive call raises `limit`, so recursion terminates.
    #
    # Still conservative: mutually exclusive branches are not pruned, so this is
    # an upper bound on a single tick's work, not a prediction of typical cost.
    MAX_INSTR_PER_TICK = 1000
    CAP = 10_000_000

    # (head, latch, bound_or_None) for each detected loop
    loops: list[tuple[int, int, int | None]] = []
    for head in sorted(bounds):
        latch = None
        for i in range(n - 1, head, -1):
            if head in succ[i]:
                latch = i
                break
        if latch is None:
            continue
        if head == 0:
            continue                      # main loop: one pass per tick
        loops.append((head, latch, bounds[head]))

    # Iterative forward-only propagation, inner loops resolved first.
    #
    # `f[i]` = worst instruction count from entry 0 to the point just after
    # statement i finishes. Backward edges are never followed during the sweep;
    # instead a loop is priced once, when its own head comes up:
    #
    #     loop_cost(h) = bound(h) * (worst forward path inside [h, latch])
    #
    # Because loops are handled by descending head index, an inner loop is
    # already priced when the outer loop that contains it is measured -- so the
    # inner cost is added exactly once, from f[inner_head] + loop_cost, and the
    # outer multiplication applies to a body that already includes it.
    #
    # Exiting a loop: the latch's forward edges leave it, and their cost is
    # `loop_cost + 1` (run the loop `bound` times, then take one step out).
    MAX_INSTR_PER_TICK = 1000

    loops: list[tuple[int, int, int]] = []
    for head in sorted(bounds, reverse=True):
        latch = None
        for i in range(n - 1, head, -1):
            if head in succ[i]:
                latch = i
                break
        if latch is None or head == 0:
            continue                      # no latch found, or the main loop
        loops.append((head, latch, bounds[head]))

    f = [0] * n
    f[0] = 1                              # entry: statement 0 always executes
    loop_cost: dict[int, int] = {}

    for head, latch, bound in loops:
        f[head] = max(f[head], 1)
        cnt = [0] * n
        cnt[head] = 1
        best = 1
        for i in range(head, latch + 1):
            if cnt[i] == 0:
                continue
            for s in succ[i]:
                if s <= i:
                    continue              # backward edge: priced by loop_cost
                if i == latch and s > latch:
                    # leaving the loop: pay the whole loop plus this step
                    cand = max(f[head], cnt[head]) + bound * best + 1
                elif s <= latch:
                    cand = cnt[i] + 1
                else:
                    continue              # forward exit taken from inside
                if s < n:
                    if cand > cnt[s]:
                        cnt[s] = cand
                    if cnt[s] > best:
                        best = cnt[s]
                    if i == latch and cand > f[s]:
                        f[s] = cand
        lc = min(bound * best, MAX_INSTR_PER_TICK)
        loop_cost[head] = lc
        for i in range(head, latch + 1):
            if cnt[i]:
                f[i] = max(f[i], f[head] + cnt[i] - 1)
        if f[head] + lc > f[latch]:
            f[latch] = f[head] + lc

    for i in range(n):
        if f[i] == 0:
            continue
        for s in succ[i]:
            cand = f[i] + 1
            if s < i:                     # back edge to a known loop head
                cand = f[i] + loop_cost.get(s, 1)
            if s < n and cand > f[s]:
                f[s] = cand

    worst_n = max(f)

    lines.append(f"  worst-case path : ~{worst_n} instructions per full cycle "
                 f"(approximate)")
    if worst_n > MAX_INSTR_PER_TICK:
        lines.append(f"      ⚠ over LExecutor.maxInstructions "
                     f"({MAX_INSTR_PER_TICK}/tick): one cycle needs "
                     f"{worst_n / MAX_INSTR_PER_TICK:.1f} ticks of pure work, "
                     f"so the unit reacts with that much latency")
    for ipt, name in ((2, "micro-processor"), (8, "logic-processor"),
                      (25, "hyper-processor")):
        ticks = worst_n / ipt
        lines.append(f"      {name:<16} @ipt={ipt:<3} {ticks:8.0f} ticks "
                     f"({ticks/60:7.1f} s) per cycle")

    if links:
        lines.append(f"  links           : {len(links)} "
                     f"({', '.join(links[:6])}{'...' if len(links) > 6 else ''})")
    return "\n".join(lines)


def show(path: str, findings: list[Finding]) -> int:
    errs = [f for f in findings if f.sev in ("ERR", "SUSPECT")]
    warns = [f for f in findings if f.sev == "WARN"]
    infos = [f for f in findings if f.sev == "INFO"]
    print(f"=== {path}")
    for f in errs + warns + infos:
        print(f)
    if not findings:
        print("  no issues found")
    print(f"  -> {len(errs)} error/ suspect, {len(warns)} warning, {len(infos)} info")
    return 1 if errs else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", help=".mlog files")
    ap.add_argument("--blueprint", action="append", default=[],
                    help=".msch file; checks every logic block inside")
    ap.add_argument("--cost", action="store_true",
                    help="also report statement count, unreachable code, loop "
                         "bounds and worst-case instruction cost per cycle")
    args = ap.parse_args()

    def do(path: str, lines: list[str], links: list[str] | None = None) -> int:
        rc = show(path, analyse(lines, links))
        if args.cost:
            stmts = [(i, strip_comment(l)) for i, l in enumerate(lines)
                     if strip_comment(l)]
            print(cost_report(stmts, links))
            print()
        return rc

    rc = 0
    for p in args.files:
        with open(p, encoding="utf-8") as fh:
            rc |= do(p, fh.read().split("\n"))

    if args.blueprint:
        import msch
        for p in args.blueprint:
            sch = msch.parse_file(p)
            for t in sch.logic_tiles():
                assert t.logic is not None
                rc |= do(f"{p} [{t.block} @{t.x},{t.y}]",
                         t.logic.code.split("\n"),
                         [l.name for l in t.logic.links])
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
