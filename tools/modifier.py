#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Composable disturbances for scenario timelines (planning §2 P2).

A *modifier* is one disturbance applied at one tick of a scenario run: spawn a
wave of units, kill the ones the program is steering, hand them to another team,
gut a building, drain the core, burn clock ticks, sprinkle ore.  The scenario
file names them in its ``modifiers`` list and ``tools/scenario.py`` plays them
back on the timeline it already has (``_step_js()`` segments), so there is no
second executor and no second projection.

Every kind in :data:`KINDS` declares the five things planning asks for:

``params``
    Name/type/default/range/unit for every knob, plus a doc line.  ``list`` and
    ``show`` print it, ``normalize``/``validate_entry`` enforce it, and the
    defaults are what make one entry readable without the docs.
``via``
    Where it can run: ``"sim"`` (offline executor, per-tick stepping) and/or
    ``"world"`` (live game, coarse poll).  A kind that needs a fast-forwardable
    clock is ``sim`` only and says so, instead of failing at tick time.
``requires``
    The capabilities it leans on, from :data:`REQUIREMENTS`: script access,
    ``Groups.unit``, ``Groups.build``, a core, the terrain API, the sim clock.
    ``requirements_errors`` refuses a scenario that does not meet them.
``provides`` / ``cannot``
    What it really perturbs, and the honest list of what it does *not* do.
``plan`` + ``seed``
    The random part is drawn in Python from an explicit ``params.seed`` before
    any JS runs, so the same config + seed yields the same concrete sequence
    (offsets, picked indices, tiles) in the record.  No hidden RNG anywhere.

CLI::

    python -X utf8 tools/modifier.py list
    python -X utf8 tools/modifier.py show unit_spawn
    python -X utf8 tools/modifier.py plan unit_movement --params '{"count":2,"jitter":2,"seed":3}'
    python -X utf8 tools/modifier.py js unit_death --params '{"count":2,"pick":"random","seed":3}'
    python -X utf8 tools/modifier.py selftest

Pure stdlib; importable from :mod:`scenario` without touching the executor.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys

__all__ = [
    "ModifierError", "KINDS", "REQUIREMENTS", "ENTRY_KEYS", "KIND_ORDER",
    "sort_entries", "validate_entry", "normalize", "plan", "script",
    "requirements_errors", "describe", "example", "list_rows", "selftest",
]

#: At most this many disturbances in one scenario: a timeline is a measurement,
#: not a fuzz target, and every entry costs one `js` round trip.
MAX_ENTRIES = 32


class ModifierError(ValueError):
    """A modifier entry is unknown or malformed."""


#: Capability ids used by ``requires``.  The text is what `list`/`show` prints.
REQUIREMENTS = {
    "script": "JS injection on the host (both hosts expose `js`)",
    "units": "`Groups.unit` + `Vars.content.units()`: the scene declares units",
    "buildings": "`Groups.build`: the scene declares buildings",
    "core": "a `CoreBlock` on the scenario's team (item pressure needs a buffer)",
    "terrain": "`Vars.world.tile(x,y)`: setBlock/setNet/setOverlay on one tile",
    "sim_clock": "the sim's per-tick `Vars.state.tick` stepping (no live fast-forward)",
}

#: Required key set of one modifier entry; unknown keys are rejected so a typo
#: ("atTick") fails at load instead of being silently ignored.
ENTRY_KEYS = ("kind", "at_tick", "params")

KIND_ORDER = ("unit_movement", "unit_spawn", "unit_death", "control_competition",
              "building_change", "resource_pressure", "time_pressure",
              "world_change")

# ---------------------------------------------------------------- param shapes

def _p_int(doc, *, default=None, required=False, lo=None, hi=None, unit=""):
    return {"kind": "int", "doc": doc, "default": default, "required": required,
            "min": lo, "max": hi, "unit": unit}


def _p_float(doc, *, default=None, required=False, lo=None, hi=None, unit=""):
    return {"kind": "float", "doc": doc, "default": default, "required": required,
            "min": lo, "max": hi, "unit": unit}


def _p_str(doc, *, default=None, required=False, unit="", nonempty=None):
    # An empty string is a real value for the filters ("any type"), so only
    # required strings are non-empty by default.
    if nonempty is None:
        nonempty = bool(required)
    return {"kind": "str", "doc": doc, "default": default, "required": required,
            "unit": unit, "nonempty": nonempty}


def _p_choice(doc, choices, *, default=None, required=False):
    return {"kind": "choice", "doc": doc, "choices": tuple(choices),
            "default": default, "required": required}


# ---------------------------------------------------------------- JS pieces

#: Helpers each script carries so it never depends on scene.py's globals (the
#: sim shares one Rhino scope, but a modifier must also work when it is the
#: first script a host ever sees).
_JS_HELPERS = (
    "var MOD_TA=Packages.mindustry.game.Team.all;"
    "function MOD_team(n){for(var i=0;i<MOD_TA.length;i++){"
    "if(String(MOD_TA[i].name)==n)return MOD_TA[i];}return null;}"
    "function MOD_unit(n){var us=Vars.content.units();"
    "for(var i=0;i<us.size;i++){var c=us.get(i);if(String(c.name)==n)return c;}"
    "return null;}"
    # scan order is `Groups.unit` order: deterministic, so plan()'s indices mean
    # the same thing twice with the same seed.
    "function MOD_sel(t,tm,ax,ay,r){var G=Packages.mindustry.gen.Groups.unit,o=[];"
    "for(var i=0;i<G.size();i++){var u=G.index(i);if(u==null||u.dead)continue;"
    "if(t!==''&&String(u.type.name)!==t)continue;"
    "if(tm!==''&&String(u.team.name)!==tm)continue;"
    "if(r>0){var dx=u.x/8-ax,dy=u.y/8-ay;if(dx*dx+dy*dy>r*r)continue;}"
    "o.push(u);}return o;}"
    # one reporter for both hosts: the daemon captures only sb.append(...),
    # the offline sandbox only print(...), so pick at runtime instead of at
    # build time -- a modifier cannot know where it will be replayed.
    "function MOD_say(s){"
    "if(typeof sb!=='undefined'){sb.append(String(s)).append('\\n');}"
    "else{print(String(s));}"
    "}"
)


def _rep(flavor: str, parts: list) -> str:
    """One report line; parts are JS expressions, same shape scene.py uses."""
    if flavor == "sim":
        return "print(%s);" % " + ".join(parts)
    return "sb.append(%s).append('\\n');" % ").append(".join(parts)


def _js(v) -> str:
    return json.dumps(v, ensure_ascii=False)


def _emit(flavor: str, body: str) -> str:
    return _JS_HELPERS + body


# ---------------------------------------------------------------- plans

def _rng(params: dict) -> random.Random:
    return random.Random(int(params.get("seed") or 0))


def _spawn_spots(px: float, py: float, count: int, radius: float) -> list:
    """Golden-angle spiral in tiles; same shape scene.py uses for its own units."""
    out = []
    for i in range(count):
        r = 0.0 if count <= 1 else radius * math.sqrt((i + 0.5) / count)
        ang = i * 2.399963229728653
        out.append((round(px + math.cos(ang) * r, 3),
                    round(py + math.sin(ang) * r, 3)))
    return out


def _plan_spawn(p: dict, ctx: dict) -> list:
    spots = _spawn_spots(float(p["x"]), float(p["y"]), int(p["count"]),
                         float(p["radius"]))
    return [{"index": i, "x": x, "y": y} for i, (x, y) in enumerate(spots)]


def _pool(ctx: dict) -> int:
    """How many units the scenario declares; the plan cannot see live units."""
    return max(1, int(ctx.get("pool") or 1))


def _pick_indices(p: dict, ctx: dict) -> list:
    n = min(int(p["count"]), _pool(ctx))
    order = list(range(_pool(ctx)))
    if p.get("pick") == "random":
        _rng(p).shuffle(order)
    return order[:n]


def _plan_death(p: dict, ctx: dict) -> list:
    return [{"index": i} for i in _pick_indices(p, ctx)]


def _plan_flip(p: dict, ctx: dict) -> list:
    return [{"index": i, "team": p["team"]} for i in _pick_indices(p, ctx)]


def _plan_movement(p: dict, ctx: dict) -> list:
    jit = float(p.get("jitter") or 0.0)
    rng = _rng(p)
    out = []
    for i in range(int(p["count"])):
        dx = float(p.get("dx") or 0.0)
        dy = float(p.get("dy") or 0.0)
        if jit > 0.0:
            dx += rng.uniform(-jit, jit)
            dy += rng.uniform(-jit, jit)
        out.append({"index": i, "dx": round(dx, 3), "dy": round(dy, 3)})
    return out


def _plan_building(p: dict, ctx: dict) -> list:
    return [{"op": p["op"], "x": int(p["x"]), "y": int(p["y"]),
             "block": p["block"] or "", "team": ctx.get("team") or ""}]


def _plan_resource(p: dict, ctx: dict) -> list:
    return [{"op": p["op"], "item": p["item"], "amount": int(p["amount"]),
             "team": ctx.get("team") or ""}]


def _plan_clock(p: dict, ctx: dict) -> list:
    return [{"burn": int(p["burn"]), "at_tick": ctx.get("at_tick")}]


def _plan_world(p: dict, ctx: dict) -> list:
    if p["op"] == "rule":
        return [{"op": "rule", "key": p["key"], "value": p["value"]}]
    cx, cy, r = int(p["x"]), int(p["y"]), int(p["radius"])
    tiles = []
    for ty in range(cy - r, cy + r + 1):
        for tx in range(cx - r, cx + r + 1):
            if (tx - cx) ** 2 + (ty - cy) ** 2 <= r * r:
                tiles.append({"x": tx, "y": ty})
    return [{"op": "ore", "ore": p["ore"], "tiles": tiles}]


# ---------------------------------------------------------------- JS builders

def _js_spawn(plan_list: list, p: dict, ctx: dict) -> str:
    body = (
        "var T=MOD_team(%s);var ut=MOD_unit(%s);"
        "if(ut==null){MOD_say('MODERR\\tunit_spawn\\tno unit type %s');}"
        "else if(T==null){MOD_say('MODERR\\tunit_spawn\\tno team %s');}else{var n=0;"
        % (_js(p["team"]), _js(p["type"]), p["type"], p["team"]))
    for spot in plan_list:
        body += ("var u=ut.spawn(T,%.3f*8+4,%.3f*8+4);if(u!=null){n=n+1;}"
                 % (spot["x"], spot["y"]))
    body += ("Vars.state.teams.updateTeamStats();"
             + _rep(ctx["flavor"], [_js("MOD\tunit_spawn\t"), "n",
                                    _js("/%d" % len(plan_list))]) + "}")
    return _emit(ctx["flavor"], body)


def _js_death(plan_list: list, p: dict, ctx: dict) -> str:
    body = (
        "var sel=MOD_sel(%s,%s,%s,%s,%s);var n=0;"
        % (_js(p.get("type") or ""), _js(p.get("team") or ""),
           float(p.get("x") or 0), float(p.get("y") or 0),
           float(p.get("radius") or 0)))
    for spot in plan_list:
        i = int(spot["index"])
        body += ("if(sel.length>%d){var u=sel[%d];if(u!=null&&!u.dead){%s;n=n+1;}}"
                 % (i, i, "u.kill()" if p["mode"] == "kill" else "u.remove()"))
    body += _rep(ctx["flavor"], [_js("MOD\tunit_death\t"), "n",
                                 _js("/%d" % len(plan_list))])
    return _emit(ctx["flavor"], body)


def _js_flip(plan_list: list, p: dict, ctx: dict) -> str:
    body = (
        "var sel=MOD_sel(%s,%s,%s,%s,%s);var n=0;var MT=MOD_team(%s);"
        "if(MT==null){MOD_say('MODERR\\tcontrol_competition\\tno team %s');}else{"
        % (_js(p.get("type") or ""), _js(p.get("team") or ""),
           float(p.get("x") or 0), float(p.get("y") or 0),
           float(p.get("radius") or 0), _js(p["team"]), p["team"]))
    for spot in plan_list:
        i = int(spot["index"])
        body += ("if(sel.length>%d){var u=sel[%d];if(u!=null&&!u.dead){u.team=MT;n=n+1;}}"
                 % (i, i))
    body += ("Vars.state.teams.updateTeamStats();"
             + _rep(ctx["flavor"], [_js("MOD\tcontrol_competition\t"), "n",
                                    _js("/%d" % len(plan_list))]) + "}")
    return _emit(ctx["flavor"], body)


def _js_movement(plan_list: list, p: dict, ctx: dict) -> str:
    push = p["mode"] == "push"
    body = (
        "var sel=MOD_sel(%s,%s,%s,%s,%s);"
        "var W=Vars.world.width()*8,H=Vars.world.height()*8;var n=0;"
        % (_js(p.get("type") or ""), _js(p.get("team") or ""),
           float(p.get("x") or 0), float(p.get("y") or 0),
           float(p.get("radius") or 0)))
    for spot in plan_list:
        i = int(spot["index"])
        dx, dy = spot["dx"], spot["dy"]
        move = ("u.vel.set(%.3f,%.3f)" % (dx * 8.0, dy * 8.0)) if push else (
            "u.x=Math.max(4,Math.min(W-4,u.x+%.3f*8));"
            "u.y=Math.max(4,Math.min(H-4,u.y+%.3f*8))" % (dx, dy))
        body += ("if(sel.length>%d){var u=sel[%d];if(u!=null&&!u.dead){%s;n=n+1;}}"
                 % (i, i, move))
    body += _rep(ctx["flavor"], [_js("MOD\tunit_movement\t"), "n",
                                 _js("/%d" % len(plan_list))])
    return _emit(ctx["flavor"], body)


def _js_building(plan_list: list, p: dict, ctx: dict) -> str:
    spot = plan_list[0]
    block = spot["block"]
    lookup = "Vars.content.block('air')" if not block else \
        "Vars.content.block(%s)" % _js(block)
    setter = ("setNet(B,MOD_team(%s),0)" % _js(spot["team"])
              if ctx["flavor"] == "world" else "setBlock(B)")
    body = (
        "var B=%s;var tt=Vars.world.tile(%d,%d);"
        "if(tt==null){MOD_say('MODERR\\tbuilding_change\\tno tile %d,%d');}"
        "else if(B==null){MOD_say('MODERR\\tbuilding_change\\tno block %s');}"
        "else{tt.%s;%s}"
        % (lookup, spot["x"], spot["y"], spot["x"], spot["y"], block, setter,
           _rep(ctx["flavor"], [_js("MOD\tbuilding_change\t"),
                                "String(Vars.world.tile(%d,%d).block().name)"
                                % (spot["x"], spot["y"])]))
    )
    return _emit(ctx["flavor"], body)


def _js_resource(plan_list: list, p: dict, ctx: dict) -> str:
    spot = plan_list[0]
    op = "add" if spot["op"] == "add" else "remove"
    body = (
        "var it=Vars.content.item(%s);var found=0;"
        "if(it==null){MOD_say('MODERR\\tresource_pressure\\tno item %s');}else{"
        "var G=Packages.mindustry.gen.Groups.build;"
        "for(var i=0;i<G.size();i++){var b=G.index(i);"
        "if(b==null||b.block==null)continue;"
        "if(!(b.block instanceof Packages.mindustry.world.blocks.storage.CoreBlock))continue;"
        "if(String(b.team.name)!==%s)continue;found=1;"
        "try{b.items.%s(it,%d);}catch(e){MOD_say('MODERR\\tresource_pressure\\t'+e);}"
        "MOD_say('MOD\\tresource_pressure\\t'+(b.tile.x)+','+(b.tile.y)+'='+b.items.get(it));"
        "Vars.state.teams.updateTeamStats();break;}"
        "if(found===0){MOD_say('MODERR\\tresource_pressure\\tno core on team %s');}}"
        % (_js(spot["item"]), spot["item"], _js(spot["team"]), op,
           int(spot["amount"]), spot["team"])
    )
    return _emit(ctx["flavor"], body)


def _js_clock(plan_list: list, p: dict, ctx: dict) -> str:
    burn = int(plan_list[0]["burn"])
    body = (
        "var T0=Vars.state.tick;Vars.state.tick=T0+%d;"
        "MOD_say('MOD\\ttime_pressure\\t'+T0+'->'+Vars.state.tick);" % burn
    )
    return _emit(ctx["flavor"], body)


def _js_world(plan_list: list, p: dict, ctx: dict) -> str:
    spot = plan_list[0]
    if spot["op"] == "rule":
        body = (
            "Vars.state.rules.%s=%s;"
            % (spot["key"], repr(float(spot["value"])))
            + _rep(ctx["flavor"], [_js("MOD\tworld_change\t"),
                                   _js(spot["key"] + "="),
                                   "String(Vars.state.rules.%s)" % spot["key"]])
        )
        return _emit(ctx["flavor"], body)
    body = ("var O=Vars.content.block('ore-'+%s);var n=0;"
            "if(O==null){MOD_say('MODERR\\tworld_change\\tno ore overlay for %s');}else{"
            % (_js(spot["ore"]), spot["ore"]))
    for tile in spot["tiles"]:
        body += ("var tt=Vars.world.tile(%d,%d);if(tt!=null){tt.setOverlay(O);n=n+1;}"
                 % (tile["x"], tile["y"]))
    body += _rep(ctx["flavor"], [_js("MOD\tworld_change\t"), "n",
                                 _js(" tile(s) ore-" + spot["ore"])]) + "}"
    return _emit(ctx["flavor"], body)


_JS_BUILDERS = {
    "unit_spawn": _js_spawn,
    "unit_death": _js_death,
    "unit_movement": _js_movement,
    "control_competition": _js_flip,
    "building_change": _js_building,
    "resource_pressure": _js_resource,
    "time_pressure": _js_clock,
    "world_change": _js_world,
}


# ---------------------------------------------------------------- checks

def _check_spawn(p: dict, ctx: dict) -> list:
    return []


def _check_area(p: dict, kind: str) -> list:
    errs = []
    if p.get("x") is not None and p.get("y") is None:
        errs.append("%s: 'x' needs 'y' (the area is a circle: both or neither)"
                    % kind)
    if p.get("y") is not None and p.get("x") is None:
        errs.append("%s: 'y' needs 'x' (the area is a circle: both or neither)"
                    % kind)
    if (p.get("radius") or 0) > 0 and p.get("x") is None:
        errs.append("%s: 'radius' needs 'x'/'y' as the circle centre" % kind)
    return errs


def _check_death(p: dict, ctx: dict) -> list:
    return _check_area(p, "unit_death")


def _check_movement(p: dict, ctx: dict) -> list:
    errs = _check_area(p, "unit_movement")
    if p.get("dx") is None and p.get("dy") is None and not (p.get("jitter") or 0):
        errs.append("unit_movement: give 'dx'/'dy' (a direction) or 'jitter' > 0")
    return errs


def _check_flip(p: dict, ctx: dict) -> list:
    errs = _check_area(p, "control_competition")
    if p.get("team") == (ctx.get("team") or ""):
        errs.append("control_competition: 'team' is the scenario's own team %r; "
                    "handing units to themselves competes with nobody"
                    % (p.get("team"),))
    return errs


def _check_building(p: dict, ctx: dict) -> list:
    errs = []
    if p["op"] in ("place", "replace") and not p.get("block"):
        errs.append("building_change: op=%r needs 'block' (the 1x1 block to put "
                    "on the tile)" % p["op"])
    if p["op"] == "remove" and p.get("block"):
        errs.append("building_change: op='remove' takes no 'block' "
                    "(set op='replace' to swap)")
    return errs


def _check_resource(p: dict, ctx: dict) -> list:
    return []


def _check_clock(p: dict, ctx: dict) -> list:
    errs = []
    ticks = ctx.get("ticks")
    if ticks is not None and int(p["burn"]) > int(ticks):
        errs.append("time_pressure: burn=%d exceeds limits.ticks=%d"
                    % (int(p["burn"]), int(ticks)))
    return errs


def _check_world(p: dict, ctx: dict) -> list:
    errs = []
    if p["op"] == "ore":
        if p.get("x") is None or p.get("y") is None:
            errs.append("world_change: op='ore' needs 'x' and 'y' (the centre tile)")
    elif p.get("key") is None or p.get("value") is None:
        # Both have defaults, so this only fires for an explicit null.
        errs.append("world_change: op='rule' needs a numeric 'key' and 'value'")
    return errs


# ---------------------------------------------------------------- registry

KINDS: dict = {
    "unit_movement": {
        "summary": "nudge/teleport the units the program is steering",
        "via": ("sim", "world"),
        "requires": ("script", "units"),
        "provides": (
            "moves up to `count` matching units by dx/dy (or a seeded jitter), "
            "either by writing x/y (teleport) or by setting velocity (push); "
            "filters by type/team/area so it can hit one group and leave another",
        ),
        "cannot": (
            "no pathfinding: teleport writes x/y directly, so a unit can land "
            "inside a wall or a building",
            "no rotation control (facing is not touched)",
            "the unit AI immediately steers back toward its mission, so a push "
            "is a disturbance, not a relocation",
            "skips dead units and never touches units outside the filter",
        ),
        "random": True,
        "params": {
            "count": _p_int("how many matching units to move", default=1,
                            lo=1, hi=64, unit="units"),
            "dx": _p_float("tiles to move on x (with 'dy': the direction)",
                           default=None, lo=-64.0, hi=64.0, unit="tiles"),
            "dy": _p_float("tiles to move on y", default=None, lo=-64.0, hi=64.0,
                           unit="tiles"),
            "jitter": _p_float("seeded extra offset, ± this many tiles; 0 = exact",
                               default=0.0, lo=0.0, hi=8.0, unit="tiles"),
            "mode": _p_choice("how the move is applied", ("teleport", "push"),
                              default="teleport"),
            "type": _p_str("unit type to move ('' = any type)", default=""),
            "team": _p_str("team to move ('' = any team)", default=""),
            "x": _p_int("circle centre tile x for the area filter", default=None),
            "y": _p_int("circle centre tile y for the area filter", default=None),
            "radius": _p_float("area filter radius in tiles; 0 = the whole map",
                               default=0.0, lo=0.0, hi=64.0, unit="tiles"),
            "seed": _p_int("explicit RNG seed for the jitter draws", default=0),
        },
        "plan": _plan_movement,
        "check": _check_movement,
        "js": _js_movement,
    },
    "unit_spawn": {
        "summary": "spawn a wave of units at a tick",
        "via": ("sim", "world"),
        "requires": ("script", "units"),
        "provides": (
            "adds `count` units of one type on one team, spread on a golden-angle "
            "spiral around (x,y) with `radius`, through UnitType.spawn() exactly "
            "as the scene's own `units` do",
        ),
        "cannot": (
            "no facing/rotation control and no per-unit loadout",
            "cannot exceed the unit cap: rules.unitCap is what makes the first "
            "scene spawns real, so a wave above it is born dead",
            "does not give the new units a mission; they get the free AI",
            "world path: coords are scene tiles, so the world sees them where "
            "the scene was laid down",
        ),
        "random": True,
        "params": {
            "type": _p_str("unit type name, e.g. 'dagger'", required=True),
            "count": _p_int("how many to spawn", default=1, lo=1, hi=64,
                            unit="units"),
            "x": _p_int("centre tile x (default: 4 tiles right of the first "
                        "scene unit, else the map centre)", default=None),
            "y": _p_int("centre tile y (default: the first scene unit's y)",
                        default=None),
            "radius": _p_float("spiral radius", default=1.0, lo=0.0, hi=16.0,
                               unit="tiles"),
            "team": _p_choice("team to spawn on", ("sharded", "crux", "green",
                                                   "blue", "derelict"),
                              default="sharded"),
            "seed": _p_int("explicit RNG seed (the spiral itself is exact; "
                           "kept so a jittered spread stays reproducible)",
                           default=0),
        },
        "plan": _plan_spawn,
        "check": _check_spawn,
        "js": _js_spawn,
    },
    "unit_death": {
        "summary": "kill or despawn units mid-run",
        "via": ("sim", "world"),
        "requires": ("script", "units"),
        "provides": (
            "removes up to `count` matching units: kill() runs death effects, "
            "remove() silently despawns; `pick='random'` with a seed decides "
            "which of the matching units go first",
        ),
        "cannot": (
            "cannot kill buildings (that is building_change) and leaves a "
            "player-piloted unit alone",
            "cannot address a unit by id; only by type/team/area and scan order",
            "does not damage: the unit leaves in one step, so a 'wounded' "
            "scenario is not expressible here",
        ),
        "random": True,
        "params": {
            "count": _p_int("how many matching units to remove", default=1,
                            lo=1, hi=64, unit="units"),
            "mode": _p_choice("kill() runs death effects; remove() despawns",
                              ("kill", "remove"), default="remove"),
            "pick": _p_choice("which matching units: scan order or seeded random",
                              ("stable", "random"), default="stable"),
            "type": _p_str("unit type filter ('' = any)", default=""),
            "team": _p_str("team filter ('' = any)", default=""),
            "x": _p_int("circle centre tile x", default=None),
            "y": _p_int("circle centre tile y", default=None),
            "radius": _p_float("area radius in tiles; 0 = whole map", default=0.0,
                               lo=0.0, hi=64.0, unit="tiles"),
            "seed": _p_int("explicit RNG seed for pick='random'", default=0),
        },
        "plan": _plan_death,
        "check": _check_death,
        "js": _js_death,
    },
    "control_competition": {
        "summary": "hand units to another team so the program loses them",
        "via": ("sim", "world"),
        "requires": ("script", "units"),
        "provides": (
            "flips `count` matching units to `team` at a tick, so a processor's "
            "ubind stops finding them and they start shooting/being shot as the "
            "other side: control is contested for the rest of the run",
        ),
        "cannot": (
            "does not run a second processor (that is a scene building; see "
            "scenes/scenarios/processor-competition.json)",
            "cannot restore the original team: the flip is one-way",
            "does not take over the player's unit (a Player controller is left "
            "alone)",
            "the old team's stats update immediately, but a per-team unit cap "
            "already spent elsewhere is not refunded",
        ),
        "random": True,
        "params": {
            "count": _p_int("how many units to hand over", default=1, lo=1, hi=64,
                            unit="units"),
            "team": _p_choice("team that gets them", ("crux", "green", "blue",
                                                      "derelict"),
                              default="crux"),
            "pick": _p_choice("which matching units: scan order or seeded random",
                              ("stable", "random"), default="stable"),
            "type": _p_str("unit type filter ('' = any)", default=""),
            "x": _p_int("circle centre tile x", default=None),
            "y": _p_int("circle centre tile y", default=None),
            "radius": _p_float("area radius in tiles; 0 = whole map", default=0.0,
                               lo=0.0, hi=64.0, unit="tiles"),
            "seed": _p_int("explicit RNG seed for pick='random'", default=0),
        },
        "plan": _plan_flip,
        "check": _check_flip,
        "js": _js_flip,
    },
    "building_change": {
        "summary": "put/swap/remove one tile's building at a tick",
        "via": ("sim", "world"),
        "requires": ("script", "terrain"),
        "provides": (
            "setBlock (sim) / setNet (world) on one tile: place a block, replace "
            "a block, or clear it to air; the report line reads the block back "
            "so the record shows what the tile held afterwards",
        ),
        "cannot": (
            "multi-tile blocks are refused at validation: the tile API writes "
            "one tile and a 2x2 block would be clipped",
            "does not configure the new building (items, links, code, team stats)",
            "does not fire a player-style placement event; logic sensors see the "
            "block, the world event log may not",
            "works on one tile per entry: no area edits (world_change does ore, "
            "not walls)",
        ),
        "random": False,
        "params": {
            "op": _p_choice("what to do with the tile", ("remove", "place",
                                                         "replace"),
                            default="remove"),
            "x": _p_int("tile x", required=True),
            "y": _p_int("tile y", required=True),
            "block": _p_str("1x1 block name for place/replace, e.g. 'router'",
                            default=""),
        },
        "plan": _plan_building,
        "check": _check_building,
        "js": _js_building,
    },
    "resource_pressure": {
        "summary": "add or drain one item in the scenario team's core",
        "via": ("sim", "world"),
        "requires": ("script", "core"),
        "provides": (
            "moves `amount` of one item into/out of the team's CoreBlock buffer "
            "at a tick, then reports the resulting count; this is the resource "
            "starvation/glut knob for launch and production scenarios",
        ),
        "cannot": (
            "needs a core on the scenario team; without one the entry records "
            "executed=false and the reason, it does not invent a core",
            "does not change mining or production rates, only the buffer",
            "drains at most what is there (ItemModule.remove returns what it "
            "could take)",
            "world path edits the live core the player sees (the world bridge "
            "audits it)",
        ),
        "random": False,
        "params": {
            "op": _p_choice("add to or remove from the core buffer",
                            ("add", "drain"), default="drain"),
            "item": _p_str("item name, e.g. 'copper'", required=True),
            "amount": _p_int("how many items", default=10, lo=1, hi=100000,
                             unit="items"),
        },
        "plan": _plan_resource,
        "check": _check_resource,
        "js": _js_resource,
    },
    "time_pressure": {
        "summary": "burn clock ticks with no updates (a stall spike)",
        "via": ("sim",),
        "requires": ("script", "sim_clock"),
        "provides": (
            "advances Vars.state.tick by `burn` with no worldTick/unitTick/"
            "processor update, so the clock moves while logic does not: the "
            "tick-budget version of a lag spike",
        ),
        "cannot": (
            "sim only: the live world's clock is real time and cannot be "
            "fast-forwarded from a script",
            "does not shrink limits.ticks -- the declared budget stays, this "
            "consumes ticks inside it",
            "does not slow the wall clock (limits.timeout_s keeps running)",
            "physics is skipped during the burn, so units do not drift",
        ),
        "random": False,
        "params": {
            "burn": _p_int("ticks to advance without updating anything",
                           default=30, lo=1, hi=100000, unit="ticks"),
        },
        "plan": _plan_clock,
        "check": _check_clock,
        "js": _js_clock,
    },
    "world_change": {
        "summary": "sprinkle ore on the ground or move one rule knob",
        "via": ("sim", "world"),
        "requires": ("script", "terrain"),
        "provides": (
            "op='ore': setOverlay ore-<ore> on every tile of a disc (the plan "
            "lists the exact tiles); op='rule': assign one whitelisted "
            "Vars.state.rules field and report its new value",
        ),
        "cannot": (
            "ore is an overlay: setOverlay replaces whatever overlay was there "
            "and this API has no drill-yield amount",
            "rule keys are the short whitelist in the 'key' choices; arbitrary "
            "fields, and anything not numeric, are not touched",
            "cannot raise terrain walls or add weather (no weather hook in the "
            "executor); clearing a building is building_change",
            "world path changes the live map the player sees (audited)",
        ),
        "random": False,
        "params": {
            "op": _p_choice("what to change", ("ore", "rule"), default="ore"),
            "ore": _p_choice("ore overlay for op='ore'",
                             ("copper", "lead", "coal", "titanium", "thorium",
                              "scrap", "sand"), default="copper"),
            "x": _p_int("disc centre tile x (op='ore')", default=None),
            "y": _p_int("disc centre tile y (op='ore')", default=None),
            "radius": _p_int("disc radius in tiles (op='ore')", default=1, lo=0,
                             hi=8, unit="tiles"),
            "key": _p_choice("rules field for op='rule'",
                             ("unitCap", "unitBuildSpeedMultiplier",
                              "buildSpeedMultiplier", "unitCostMultiplier",
                              "deconstructSpeedMultiplier",
                              "logicUnitBuildSpeedMultiplier"),
                             default="unitCap"),
            "value": _p_float("numeric value for op='rule'", default=32.0,
                              lo=0.0, hi=100000.0),
        },
        "plan": _plan_world,
        "check": _check_world,
        "js": _js_world,
    },
}


# ---------------------------------------------------------------- validation

def _param_error(where: str, ps: dict, value) -> str:
    kind = ps["kind"]
    if kind == "int":
        if isinstance(value, bool) or not isinstance(value, int):
            return "%s must be an integer, got %r" % (where, value)
    elif kind == "float":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return "%s must be a number, got %r" % (where, value)
    elif kind == "str":
        if not isinstance(value, str):
            return "%s must be a string, got %r" % (where, value)
        if ps.get("nonempty") and not value.strip():
            return "%s must not be empty" % where
        return ""
    elif kind == "bool":
        return "" if isinstance(value, bool) else (
            "%s must be true/false, got %r" % (where, value))
    elif kind == "choice":
        return "" if value in ps["choices"] else (
            "%s must be one of %s, got %r" % (where, "/".join(ps["choices"]), value))
    lo, hi = ps.get("min"), ps.get("max")
    if lo is not None and value < lo:
        return "%s must be >= %s, got %r" % (where, lo, value)
    if hi is not None and value > hi:
        return "%s must be <= %s, got %r" % (where, hi, value)
    return ""


def normalize(kind: str, params, ctx: dict | None = None) -> dict:
    """Fill defaults and type-check one ``params`` object; raises ModifierError.

    ``ctx`` narrows the coordinate range (``ctx["size"]``) and tick budget;
    missing ctx keys are simply not checked.
    """
    ctx = ctx or {}
    if kind not in KINDS:
        raise ModifierError("unknown modifier kind %r (known: %s)"
                            % (kind, ", ".join(KIND_ORDER)))
    spec = KINDS[kind]
    if params is None:
        params = {}
    if not isinstance(params, dict):
        raise ModifierError("%s.params must be an object, got %r"
                            % (kind, params))
    errs = []
    unknown = sorted(set(params) - set(spec["params"]))
    if unknown:
        errs.append("%s: unknown param(s): %s (known: %s)"
                    % (kind, ", ".join(unknown), ", ".join(spec["params"])))
        raise ModifierError("; ".join(errs))
    out = {}
    for name, ps in spec["params"].items():
        if name in params:
            value = params[name]
        elif ps.get("required"):
            errs.append("%s: missing required param %r (%s)"
                        % (kind, name, ps["doc"]))
            continue
        else:
            value = ps.get("default")
        if value is None:
            out[name] = None
            continue
        err = _param_error("%s.%s" % (kind, name), ps, value)
        if err:
            errs.append(err)
            continue
        out[name] = float(value) if ps["kind"] == "float" else value
    size = ctx.get("size")
    if size:
        for name in ("x", "y"):
            v = out.get(name)
            if v is not None and not (0 <= v < int(size)):
                errs.append("%s.%s=%r is outside the %dx%d world"
                            % (kind, name, v, size, size))
    if errs:
        raise ModifierError("; ".join(errs))
    errs = list(spec["check"](out, ctx) or [])
    if errs:
        raise ModifierError("; ".join(errs))
    return out


def requirements_errors(kind: str, ctx: dict) -> list:
    """The `requires` capabilities this scenario/via does not offer."""
    out = []
    for need in KINDS[kind]["requires"]:
        if need == "units" and not ctx.get("units"):
            out.append("%s needs `units` (a scene unit to disturb) but this "
                       "scenario declares none" % kind)
        elif need == "buildings" and not ctx.get("buildings"):
            out.append("%s needs `buildings` but this scenario declares none"
                       % kind)
        elif need == "core" and not any(
                "core" in str((b or {}).get("block", "")).lower()
                for b in ctx.get("buildings") or [] if isinstance(b, dict)):
            out.append("%s needs a core (`core-*` building) on the scenario "
                       "team; add one to `buildings`" % kind)
        elif need == "sim_clock" and ctx.get("via") == "world":
            out.append("%s needs the sim clock; via='world' cannot fast-forward "
                       "a live game" % kind)
    return out


def validate_entry(entry, ctx: dict | None = None) -> tuple:
    """(normalized entry, errors).  Never raises: callers collect text.

    The normalized entry is ``{"kind", "at_tick", "params", "seed"}`` where
    ``params`` has defaults filled and types coerced.
    """
    ctx = ctx or {}
    if not isinstance(entry, dict):
        return None, ["modifier must be an object, got %r" % (entry,)]
    errs = []
    unknown = sorted(set(entry) - set(ENTRY_KEYS))
    if unknown:
        errs.append("unknown key(s): %s (known: %s)"
                    % (", ".join(unknown), ", ".join(ENTRY_KEYS)))
    kind = entry.get("kind")
    if not isinstance(kind, str) or kind not in KINDS:
        errs.append("kind %r is not a modifier (known: %s)"
                    % (kind, ", ".join(KIND_ORDER)))
        return None, errs
    at = entry.get("at_tick")
    if isinstance(at, bool) or not isinstance(at, int):
        errs.append("at_tick must be an integer tick, got %r" % (at,))
        at = None
    elif at < 0:
        errs.append("at_tick must be >= 0, got %r" % (at,))
    elif ctx.get("ticks") is not None and at > int(ctx["ticks"]):
        errs.append("at_tick=%d is past limits.ticks=%d"
                    % (at, int(ctx["ticks"])))
    try:
        params = normalize(kind, entry.get("params"), ctx)
    except ModifierError as exc:
        errs.append(str(exc))
        params = None
    if params is not None:
        errs.extend(requirements_errors(kind, ctx))
    if errs:
        return None, errs
    return {"kind": kind, "at_tick": int(at), "params": params,
            "seed": params.get("seed")}, []


def sort_entries(entries: list) -> list:
    """Stable sort by at_tick: same tick keeps declaration order.

    ``_index`` is the declaration index the caller stamps on; without it the
    sort is still stable on the list order (Python's sort is stable), so this is
    only needed for entries that have already been regrouped.
    """
    return sorted(entries, key=lambda e: (int(e["at_tick"]), e.get("_index", 0)))


def plan(entry, ctx: dict | None = None) -> list:
    """The seeded, concrete decisions for one entry (no executor needed).

    Same config + seed => identical list; that is the reproducibility contract.
    """
    ctx = ctx or {}
    kind = entry.get("kind")
    if kind not in KINDS:
        raise ModifierError("unknown modifier kind %r (known: %s)"
                            % (kind, ", ".join(KIND_ORDER)))
    params = normalize(kind, entry.get("params"), ctx)
    return KINDS[kind]["plan"](params, ctx)


def _resolve_spot(kind: str, params: dict, ctx: dict) -> dict:
    """Scene-dependent defaults for the spawn centre (needs the scene's units)."""
    if kind != "unit_spawn" or params.get("x") is not None:
        return params
    units = ctx.get("units") or []
    first = units[0] if units and isinstance(units[0], dict) else {}
    at = first.get("at") or []
    size = int(ctx.get("size") or 64)
    params = dict(params)
    params["x"] = int(at[0]) + 4 if len(at) >= 2 else size // 2
    if params.get("y") is None:
        params["y"] = int(at[1]) if len(at) >= 2 else size // 2
    return params


def script(entry, ctx: dict | None = None) -> dict:
    """{"script": one-line js, "skip": ticks to burn, "plan": [...]}."""
    ctx = dict(ctx or {})
    ctx.setdefault("flavor", "sim")
    ctx.setdefault("team", "sharded")
    ctx.setdefault("size", 64)
    kind = entry.get("kind")
    if kind not in KINDS:
        raise ModifierError("unknown modifier kind %r (known: %s)"
                            % (kind, ", ".join(KIND_ORDER)))
    params = normalize(kind, entry.get("params"), ctx)
    params = _resolve_spot(kind, params, ctx)
    ctx["at_tick"] = entry.get("at_tick", 0)
    plan_list = KINDS[kind]["plan"](params, ctx)
    js = KINDS[kind]["js"](plan_list, params, ctx)
    skip = int(params["burn"]) if kind == "time_pressure" else 0
    if "\n" in js or "\r" in js:
        raise ModifierError("%s: the host folds a script onto one console line; "
                            "a newline here would split the command" % kind)
    return {"script": js, "skip": skip, "plan": plan_list}


# ---------------------------------------------------------------- presentation

def describe(kind: str) -> str:
    spec = KINDS[kind]
    lines = ["%-20s %s" % (kind, spec["summary"]),
             "  via      %s" % ", ".join(spec["via"])]
    lines.append("  requires %s" % ", ".join(
        "%s (%s)" % (r, REQUIREMENTS[r]) for r in spec["requires"]))
    lines.append("  provides")
    for item in spec["provides"]:
        lines.append("    + " + item)
    lines.append("  cannot")
    for item in spec["cannot"]:
        lines.append("    - " + item)
    lines.append("  params")
    for name, ps in spec["params"].items():
        bits = [ps["kind"]]
        if ps.get("required"):
            bits.append("required")
        elif ps.get("default") is not None:
            bits.append("default=%r" % (ps["default"],))
        if ps.get("choices"):
            bits.append("choices=%s" % "/".join(ps["choices"]))
        if ps.get("min") is not None or ps.get("max") is not None:
            bits.append("range=%s..%s" % (ps.get("min"), ps.get("max")))
        if ps.get("unit"):
            bits.append("unit=%s" % ps["unit"])
        lines.append("    %-10s %-26s %s" % (name, " ".join(bits), ps["doc"]))
    lines.append("  example  %s" % json.dumps(example(kind), ensure_ascii=False))
    return "\n".join(lines)


#: Valid minimal params per kind, so `show`/`selftest` never print an entry
#: that the validator would refuse.
_EXAMPLES = {
    "unit_movement": {"count": 1, "dx": 4.0, "dy": 0.0, "mode": "teleport"},
    "unit_spawn": {"type": "dagger", "count": 3, "x": 40, "y": 32},
    "unit_death": {"count": 1, "mode": "remove"},
    "control_competition": {"count": 1, "team": "crux"},
    "building_change": {"op": "remove", "x": 8, "y": 8},
    "resource_pressure": {"op": "drain", "item": "copper", "amount": 10},
    "time_pressure": {"burn": 30},
    "world_change": {"op": "ore", "ore": "copper", "x": 32, "y": 32, "radius": 1},
}
_EXAMPLE_AT = {"unit_spawn": 120, "world_change": 60, "time_pressure": 90}


def example(kind: str) -> dict:
    """A minimal valid entry for `show` and the docs."""
    return {"kind": kind, "at_tick": _EXAMPLE_AT.get(kind, 30),
            "params": dict(_EXAMPLES[kind])}


def list_rows() -> list:
    rows = []
    for kind in KIND_ORDER:
        spec = KINDS[kind]
        rows.append({
            "kind": kind,
            "via": "+".join(spec["via"]),
            "params": len(spec["params"]),
            "random": "seed" if spec["random"] else "-",
            "requires": ",".join(spec["requires"]),
            "summary": spec["summary"],
        })
    return rows


def selftest() -> int:
    """Real checks over the registry, the validator and the JS builders."""
    state = {"n": 0, "fail": 0}

    def ok(cond, what):
        state["n"] += 1
        if not cond:
            state["fail"] += 1
        print("%s %s" % ("ok  " if cond else "FAIL", what))

    ok(tuple(KINDS) == KIND_ORDER, "the 8 planning kinds are registered in order")
    ok(len(KINDS) == 8, "exactly 8 kinds (got %d)" % len(KINDS))

    for kind in KIND_ORDER:
        spec = KINDS[kind]
        facets = ("summary", "via", "requires", "provides", "cannot", "params",
                  "plan", "check", "js")
        missing = [f for f in facets if not spec.get(f)]
        ok(not missing, "%s declares params/via/requires/provides/cannot/plan/js%s"
           % (kind, (" (missing: %s)" % ", ".join(missing)) if missing else ""))
        ok(bool(spec["via"]) and all(v in ("sim", "world") for v in spec["via"]),
           "%s via is a non-empty subset of sim/world" % kind)
        ok(all(r in REQUIREMENTS for r in spec["requires"]),
           "%s requires only known capabilities" % kind)
        ok("script" in spec["requires"], "%s needs script access" % kind)
        bad = [n for n, ps in spec["params"].items()
               if not ps.get("doc") or "kind" not in ps]
        ok(not bad, "%s every param has a kind+doc" % kind)
        bad = [n for n, ps in spec["params"].items()
               if ps.get("default") is not None and _param_error(n, ps, ps["default"])]
        ok(not bad, "%s defaults satisfy their own ranges" % kind)

    def refused(what, kind, params, needle, ctx=None):
        try:
            normalize(kind, params, ctx or {})
        except ModifierError as exc:
            ok(needle in str(exc), "%s (error says %r)" % (what, needle))
            return
        ok(False, "%s: expected ModifierError mentioning %r" % (what, needle))

    refused("unknown kind is rejected", "unit_out", {}, "unknown modifier kind")
    refused("unknown param is rejected", "unit_spawn",
            {"type": "x", "bogus": 1}, "unknown param")
    refused("wrong type is rejected", "unit_spawn",
            {"type": "dagger", "count": "3"}, "must be an integer")
    refused("range is enforced", "unit_spawn",
            {"type": "dagger", "count": 0}, "must be >= 1")
    refused("missing required param is named", "unit_spawn", {},
            "missing required param")
    refused("choice is enforced", "unit_death", {"mode": "explode"},
            "must be one of")
    refused("coords outside the world are refused", "building_change",
            {"op": "place", "x": 99, "y": 3, "block": "router"},
            "outside the", {"size": 64})
    refused("movement without a direction is refused", "unit_movement",
            {"count": 1}, "give 'dx'/'dy'")
    refused("ore without a centre is refused", "world_change", {"op": "ore"},
            "needs 'x' and 'y'")
    refused("burn above the budget is refused", "time_pressure",
            {"burn": 500}, "exceeds", {"ticks": 240})
    refused("flip to the own team is refused", "control_competition",
            {"team": "crux"}, "own team", {"team": "crux"})

    norm, errs = validate_entry({"kind": "nope", "at_tick": 0})
    ok(bool(errs) and "is not a modifier" in errs[0], "unknown kind is named")
    norm, errs = validate_entry({"kind": "unit_spawn", "at_tick": 500,
                                 "params": {"type": "dagger"}}, {"ticks": 240})
    ok(bool(errs) and "past limits.ticks" in errs[0],
       "at_tick past the budget is named")
    norm, errs = validate_entry({"kind": "unit_spawn", "atTick": 1,
                                 "params": {"type": "dagger"}})
    ok(bool(errs) and "unknown key(s): atTick" in errs[0], "a typo'd key is named")
    norm, errs = validate_entry({"kind": "unit_spawn", "at_tick": 10,
                                 "params": {"type": "dagger"}},
                                {"units": [{"at": [24, 32]}],
                                 "buildings": [{"block": "core-shard"}]})
    ok(not errs and norm["at_tick"] == 10 and norm["params"]["count"] == 1,
       "a minimal valid entry normalizes")

    ue = requirements_errors("unit_death", {"units": [], "buildings": []})
    ok(any("needs `units`" in e for e in ue), "no units => unit_death refused")
    ce = requirements_errors("resource_pressure",
                             {"units": [{}], "buildings": [{"block": "router"}]})
    ok(any("needs a core" in e for e in ce),
       "no core => resource_pressure refused")
    we = requirements_errors("time_pressure", {"units": [{}], "via": "world"})
    ok(any("sim clock" in e for e in we), "time_pressure refuses via=world")

    a = plan({"kind": "unit_movement",
              "params": {"count": 4, "jitter": 3.0, "seed": 7}}, {"pool": 4})
    b = plan({"kind": "unit_movement",
              "params": {"count": 4, "jitter": 3.0, "seed": 7}}, {"pool": 4})
    c = plan({"kind": "unit_movement",
              "params": {"count": 4, "jitter": 3.0, "seed": 8}}, {"pool": 4})
    ok(a == b, "same seed => identical unit_movement plan")
    ok(a != c, "different seed => different unit_movement plan")
    d = plan({"kind": "unit_death",
              "params": {"count": 3, "pick": "random", "seed": 1}}, {"pool": 5})
    e = plan({"kind": "unit_death",
              "params": {"count": 3, "pick": "random", "seed": 1}}, {"pool": 5})
    f = plan({"kind": "unit_death",
              "params": {"count": 3, "pick": "random", "seed": 2}}, {"pool": 5})
    ok(d == e, "same seed => identical unit_death pick")
    ok(d != f, "different seed => different unit_death pick")
    ok(len(d) == 3 and len({x["index"] for x in d}) == 3,
       "unit_death pick draws 3 distinct indices")
    g = plan({"kind": "unit_spawn",
              "params": {"type": "dagger", "count": 3, "x": 40, "y": 32,
                         "radius": 0.0}}, {"size": 64})
    ok(len(g) == 3 and all(s["x"] == 40.0 and s["y"] == 32.0 for s in g),
       "unit_spawn with radius 0 puts every spot on the centre tile")

    raw = [{"kind": "unit_spawn", "at_tick": 30, "params": {"type": "a"},
            "_index": 0},
           {"kind": "unit_spawn", "at_tick": 10, "params": {"type": "b"},
            "_index": 1},
           {"kind": "unit_spawn", "at_tick": 30, "params": {"type": "c"},
            "_index": 2}]
    order = [x["params"]["type"] for x in sort_entries(raw)]
    ok(order == ["b", "a", "c"],
       "sort_entries orders by at_tick and keeps declaration order on ties")

    for kind in KIND_ORDER:
        entry = example(kind)
        ctx = {"flavor": "sim", "size": 64, "team": "sharded", "pool": 4,
               "ticks": 240, "units": [{"at": [24, 32]}],
               "buildings": [{"block": "core-shard"}]}
        try:
            built = script(entry, ctx)
        except ModifierError as exc:
            ok(False, "%s builds a script (%s)" % (kind, exc))
            continue
        js = built["script"]
        ok(bool(js) and "\n" not in js and "\r" not in js,
           "%s script is one console line" % kind)
        ok("MOD\\t" in js, "%s script reports a MOD line" % kind)
        ok(js.count("{") == js.count("}") and js.count("(") == js.count(")"),
           "%s script has balanced braces/parens" % kind)
        if "world" in KINDS[kind]["via"]:
            try:
                world_js = script(entry, dict(ctx, flavor="world"))["script"]
                ok(bool(world_js) and "\n" not in world_js,
                   "%s also builds for flavor=world" % kind)
            except ModifierError as exc:
                ok(False, "%s world script (%s)" % (kind, exc))

    ok(script({"kind": "time_pressure", "at_tick": 10,
               "params": {"burn": 5}})["skip"] == 5,
       "time_pressure reports its burn as skip")
    ok(script({"kind": "unit_spawn", "at_tick": 10,
               "params": {"type": "dagger", "count": 1}})["skip"] == 0,
       "a non-burn kind reports skip=0")

    print("--")
    print("%d check(s), %d failed" % (state["n"], state["fail"]))
    return 1 if state["fail"] else 0


# ---------------------------------------------------------------- CLI

def _load_params(text: str) -> dict:
    try:
        value = json.loads(text) if text else {}
    except json.JSONDecodeError as exc:
        raise ModifierError("--params is not JSON: %s" % exc) from exc
    if not isinstance(value, dict):
        raise ModifierError("--params must be a JSON object")
    return value


def _cmd_list(args) -> int:
    rows = list_rows()
    if args.json:
        print(json.dumps({"count": len(rows), "kinds": rows}, ensure_ascii=False,
                         indent=2))
        return 0
    print("%-20s %-10s %-6s %-7s %-20s %s"
          % ("KIND", "VIA", "PARAMS", "RANDOM", "REQUIRES", "DISTURBS"))
    for row in rows:
        print("%-20s %-10s %-6d %-7s %-20s %s"
              % (row["kind"], row["via"], row["params"], row["random"],
                 row["requires"], row["summary"]))
    print("--")
    print("%d modifier kind(s); timings live in the scenario's `modifiers` list"
          % len(rows))
    return 0


def _cmd_show(args) -> int:
    if args.kind not in KINDS:
        print("unknown modifier kind %r (known: %s)"
              % (args.kind, ", ".join(KIND_ORDER)), file=sys.stderr)
        return 2
    print(describe(args.kind))
    return 0


def _ctx_from_args(args) -> dict:
    return {"size": args.size, "ticks": args.ticks, "team": args.team,
            "pool": args.pool}


def _cmd_plan(args) -> int:
    try:
        params = _load_params(args.params)
        ctx = _ctx_from_args(args)
        norm = normalize(args.kind, params, ctx)
    except ModifierError as exc:
        print("invalid modifier: %s" % exc, file=sys.stderr)
        return 2
    print(json.dumps(KINDS[args.kind]["plan"](norm, ctx), ensure_ascii=False,
                     indent=2))
    return 0


def _cmd_js(args) -> int:
    try:
        built = script({"kind": args.kind, "at_tick": args.at_tick,
                        "params": _load_params(args.params)},
                       dict(_ctx_from_args(args), flavor=args.flavor))
    except ModifierError as exc:
        print("invalid modifier: %s" % exc, file=sys.stderr)
        return 2
    print(built["script"])
    print("-- skip=%d plan=%s" % (built["skip"],
                                  json.dumps(built["plan"], ensure_ascii=False)))
    return 0


def _cmd_selftest(args) -> int:
    return selftest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="composable disturbances for scenario timelines")
    sub = ap.add_subparsers(dest="cmd")

    ls = sub.add_parser("list", help="table of the 8 modifier kinds")
    ls.add_argument("--json", action="store_true")

    sh = sub.add_parser("show", help="one kind: params, via, requires, cannot")
    sh.add_argument("kind")

    pl = sub.add_parser("plan", help="print the seeded decisions of one entry")
    pl.add_argument("kind")
    pl.add_argument("--params", default="{}")
    pl.add_argument("--size", type=int, default=64)
    pl.add_argument("--ticks", type=int, default=240)
    pl.add_argument("--team", default="sharded")
    pl.add_argument("--pool", type=int, default=4)

    js = sub.add_parser("js", help="print the JS a host would run for one entry")
    js.add_argument("kind")
    js.add_argument("--params", default="{}")
    js.add_argument("--flavor", default="sim", choices=["sim", "world"])
    js.add_argument("--size", type=int, default=64)
    js.add_argument("--ticks", type=int, default=240)
    js.add_argument("--team", default="sharded")
    js.add_argument("--pool", type=int, default=4)
    js.add_argument("--at-tick", type=int, default=0)

    sub.add_parser("selftest", help="check the registry, validator and JS")

    args = ap.parse_args(argv)
    if not args.cmd:
        ap.print_help()
        return 2
    return {"list": _cmd_list, "show": _cmd_show, "plan": _cmd_plan,
            "js": _cmd_js, "selftest": _cmd_selftest}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
