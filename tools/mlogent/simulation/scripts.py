"""Pure simulator JavaScript templates and builders, without process startup."""
from __future__ import annotations

import json
import math
import os
import re


LOAD_JS = r'''
Vars.world.loadGenerator(%(n)d,%(n)d,function(tiles){
    tiles.fill();
    var floor = Vars.content.block('stone').asFloor();
    for(var x = 0; x < %(n)d; x++){
        for(var y = 0; y < %(n)d; y++){ tiles.get(x,y).setFloor(floor); }
    }
    %(ore)s
});
print("WORLD\t" + Vars.world.width() + "x" + Vars.world.height());
'''


def load_js(n: int, ore: str = "", ore_at=None, ore_radius: int = 4) -> str:
    """Build the world-loading JS, optionally painting an ore disc.

    The paint MUST happen inside the loadGenerator callback: BlockIndexer only
    fills its ore quadrants while handling WorldLoadEvent (BlockIndexer.java:94-118),
    so an ore tile placed afterwards is invisible to `ulocate ore` even though
    `ucontrol mine` (which only looks at the tile itself) works.
    """
    code = ""
    if ore:
        x, y = ore_at or (int(n * 0.75), int(n * 0.75))
        code = ("""var ob = Vars.content.block('ore-%(ore)s');
    if(ob == null){ print("OREWARN" + "\t" + "%(ore)s"); }
    else{
        for(var ox = -%(r)d; ox <= %(r)d; ox++){
            for(var oy = -%(r)d; oy <= %(r)d; oy++){
                if(ox*ox + oy*oy > %(r)d*%(r)d) continue;
                var tx = %(x)d + ox, ty = %(y)d + oy;
                if(tx < 1 || ty < 1 || tx >= %(n)d - 1 || ty >= %(n)d - 1) continue;
                tiles.get(tx,ty).setFloor(ob.asFloor());
            }
        }
        print("ORE" + "\t" + ob.name + "\t" + %(x)d + "\t" + %(y)d);
    }""" % {"ore": ore, "x": x, "y": y, "r": int(ore_radius), "n": int(n)})
    return LOAD_JS % {"n": int(n), "ore": code}


PICK_BASE_JS = r'''
print("WORLD\t" + Vars.world.width() + "x" + Vars.world.height());
/* a save carries its own world clock; scene runs start from zero so @tick/@time
   are readable and repeatable (the absolute value is meaningless between saves) */
Vars.state.tick = 0; Packages.arc.util.Time.setInternalTime(0); Vars.logicVars.update();
var W = Vars.world, air = Vars.content.block("air");
var own = null, GB = Packages.mindustry.gen.Groups.build;
for(var i = 0; i < GB.size(); i++){
    var b = GB.index(i);
    if(b.block instanceof Packages.mindustry.world.blocks.storage.CoreBlock
       && b.team == Packages.mindustry.game.Team.sharded){ own = b; break; }
}
var cx = own == null ? 2 : Math.round(own.x / 8), cy = own == null ? 2 : Math.round(own.y / 8);
var found = null;
/* spiral outward: an air tile with a non-solid floor is safe to put a processor on */
for(var r = 3; r < 40 && found == null; r++){
    for(var dx = -r; dx <= r && found == null; dx++){
        for(var dy = -r; dy <= r && found == null; dy++){
            if(Math.max(Math.abs(dx), Math.abs(dy)) != r) continue;
            var x = cx + dx, y = cy + dy;
            if(x < 1 || y < 1 || x >= W.width() - 1 || y >= W.height() - 1) continue;
            var t = W.tile(x, y);
            if(t.block().name != "air" || t.floor().solid || t.floor().isLiquid) continue;
            found = [x, y];
        }
    }
}
if(found == null){ found = [1, 1]; }
print("BASE\t" + found[0] + "\t" + found[1]);
'''


CORE_JS = r'''
var spec = %(spec)s;
var team = Packages.mindustry.game.Team.sharded;
var GB = Packages.mindustry.gen.Groups.build;
var found = 0;
for(var i = 0; i < GB.size(); i++){
    var b = GB.index(i);
    if(!(b.block instanceof Packages.mindustry.world.blocks.storage.CoreBlock)) continue;
    if(b.team != team) continue;
    if(b.items == null) continue;
    found++;
    for(var k in spec){
        var it = Vars.content.item(k);
        if(it == null) throw new Error("unknown item: " + k);
        b.items.add(it, spec[k]);
    }
    print("CORE\t" + Math.round(b.x / 8) + "\t" + Math.round(b.y / 8) + "\t"
          + b.block.name + "\t" + b.items.total());
}
if(found == 0){
    var x = %(cx)d, y = %(cy)d;
    Vars.world.tile(x, y).setBlock(Vars.content.block("core-shard"), team);
    /* Tile.setBlock does NOT update BlockIndexer (Tile.java:208); without this
       ulocate building core finds nothing, and the team's building list is empty */
    Vars.indexer.addIndex(Vars.world.tile(x, y));
    var nb = Vars.world.build(x, y);
    for(var k2 in spec){
        var it2 = Vars.content.item(k2);
        if(it2 == null) throw new Error("unknown item: " + k2);
        nb.items.add(it2, spec[k2]);
    }
    print("CORE\t" + x + "\t" + y + "\tcore-shard\t" + nb.items.total());
}
'''


def place_js(x: int, y: int, block: str = "micro-processor") -> str:
    return ("var T=Packages.mindustry.game.Team.sharded;"
            "Vars.world.tile(%d,%d).setBlock(Vars.content.block('air'), T);"
            "Vars.world.tile(%d,%d).setBlock(Vars.content.block('%s'), T);"
            "print('PLACED');" % (x, y, x, y, block))

def pads_js(count: int, radius: int = 11, water: float = -1.0,
            drain: float = 0.0, refill: bool = True) -> tuple[str, str]:
    """Place COUNT real landing pads and wire them as link 0..COUNT-1.

    Two things made a pad undebuggable out of the box:

      * Tile.setBlock() CENTERS a multiblock (Tile.java:255-288), so placing a
        4x4 pad by its origin can cover the processor tile. The processor then
        loses isValid() (BuildingComp.java:2036-2038) and every "read ... @this"
        silently returns null;
      * LandingPad.config() bails out when !accessible(), and accessible() is
        false in a non-campaign sandbox (LandingPad.java:160-163), so
        "control config" was a no-op: config stayed null and nothing landed.

    So this flips rules.allowEditWorldProcessors (the only accessible() branch
    that does not change consumption), fills the water the efficiency gate
    wants, and optionally drains items to emulate an output logistics.
    Returns (setup_js, report_js).
    """
    w = repr(float(water))
    setup = ("""/* --- landing pads (--pads %(count)d) --- */
var TB = String.fromCharCode(9);
var PADS = [];
var PAD_WATER = Vars.content.liquid("water");
var PAD_DRAIN = %(drain)s;
var PAD_REFILL = %(refill)s;
var PAD_BLK = Vars.content.block("landing-pad");
if(%(count)d > 0){ Vars.state.rules.allowEditWorldProcessors = true; }
for(var pi = 0; pi < %(count)d; pi++){
    var pspot = freeSpot(PAD_BLK.size, %(radius)d);
    if(pspot == null){ print("PADWARN" + TB + "no space for pad " + (pi + 1)); break; }
    W.tile(pspot[0], pspot[1]).setBlock(PAD_BLK, team);
    var pob = W.build(pspot[0], pspot[1]);
    var poff = -Math.floor((PAD_BLK.size - 1) / 2);
    placed.push([pspot[0] + poff, pspot[1] + poff, PAD_BLK.size]);
    b.links.add(new LL(pspot[0], pspot[1], "pad" + (pi + 1), true));
    if(pob.liquids != null){
        pob.liquids.add(PAD_WATER, %(water)s < 0 ? PAD_BLK.liquidCapacity : %(water)s);
    }
    PADS.push({b: pob, name: "pad" + (pi + 1), landings: 0, prev: pob.items.total(), acc: 0.0});
    print("PADPLACE" + TB + "pad" + (pi + 1) + TB + pspot[0] + TB + pspot[1]);
}
function padTick(){
    for(var i = 0; i < PADS.length; i++){
        var p = PADS[i], pb = p.b, now = pb.items.total();
        /* items only arrive by landing, so an upward jump is one arrival */
        if(now > p.prev) p.landings += 1;
        p.prev = now;
        /* every landing drinks 1500 water (consumeLiquidAmount) out of a 3000
           tank, so without a pump a pad stops after two landings and reads
           efficiency 0 forever. Top up by default to emulate the real supply. */
        if(PAD_REFILL && pb.liquids != null){
            pb.liquids.set(PAD_WATER, PAD_BLK.liquidCapacity);
        }
        if(PAD_DRAIN <= 0) continue;
        if(now <= 0){ p.acc = 0; continue; }
        p.acc += PAD_DRAIN;
        while(p.acc >= 1 && pb.items.total() > 0){
            var it = pb.items.first();
            if(it == null){ p.acc = 0; break; }
            pb.items.remove(it, 1);
            p.acc -= 1;
        }
    }
}
""" % {"count": int(count), "radius": int(radius), "water": w,
        "drain": repr(float(drain)), "refill": "true" if refill else "false"})
    report = """for(var pq = 0; pq < PADS.length; pq++){
    var pbuild = PADS[pq].b;
    print("PAD" + TB + PADS[pq].name + TB + pbuild.tileX() + TB + pbuild.tileY()
          + TB + pbuild.config + TB + pbuild.arriving + TB + pbuild.cooldown
          + TB + pbuild.items.total() + TB + pbuild.liquids.get(PAD_WATER)
          + TB + pbuild.efficiency + TB + PADS[pq].landings
          + TB + Vars.state.rules.allowEditWorldProcessors
          + TB + pbuild.block.logicConfigurable);
}
"""
    return setup, report


STEP_JS = r'''
var p = "%(path)s";
var s = Packages.java.nio.file.Files.readString(
    Packages.java.nio.file.Paths.get(p),
    Packages.java.nio.charset.StandardCharsets.UTF_8);
var b = Vars.world.build(%(x)d,%(y)d);
b.code = s;
/* a .mlog file has no link table; place a matching block next to the processor
   and wire it, so `read cell1 0` / `print message1` behave like the real build.
   Link names follow the game's defaults: memory-cell -> cell1, memory-bank -> bank1. */
var links = %(links)s;
var LL = Packages.mindustry.world.blocks.logic.LogicBlock.LogicLink;
var W = Vars.world, team = Packages.mindustry.game.Team.sharded;
var air = Vars.content.block("air");
var bx = %(x)d, by = %(y)d;
var placed = [];
function freeSpot(size, maxr){
    if(maxr === undefined) maxr = 24;
    /* Tile.setBlock CENTERS a multiblock: the occupied rect starts at
       origin + off with off = -(size-1)/2 (Tile.java:255-288), so a 4x4 pad
       placed at (28,31) really covers 27..30 x 30..33 and used to eat the
       processor tile. Every rect below is [topLeftX, topLeftY, size]. */
    var off = -Math.floor((size - 1) / 2);
    for(var r = 2; r <= maxr; r++){
        for(var dx = -r; dx <= r; dx++){
            for(var dy = -r; dy <= r; dy++){
                if(Math.max(Math.abs(dx), Math.abs(dy)) != r) continue;
                var x = bx + dx, y = by + dy;
                var x0 = x + off, y0 = y + off;
                if(x0 < 0 || y0 < 0 || x0 + size > W.width() || y0 + size > W.height()) continue;
                var ok = true;
                for(var i = 0; i < size && ok; i++){
                    for(var j = 0; j < size; j++){
                        var t = W.tile(x0 + i, y0 + j);
                        if(t.block() != air || t.build != null){ ok = false; break; }
                    }
                }
                /* a multi-block's non-origin tiles still read as air, so also
                   reject anything overlapping a rectangle placed during this run */
                if(ok){
                    for(var q = 0; q < placed.length; q++){
                        var p = placed[q];
                        if(x0 < p[0] + p[2] && x0 + size > p[0]
                           && y0 < p[1] + p[2] && y0 + size > p[1]){ ok = false; break; }
                    }
                }
                if(ok) return [x, y];
            }
        }
    }
    return null;
}
for(var k = 0; k < links.length; k++){
    var spec = links[k];
    var blk = Vars.content.block(spec.block);
    if(blk == null){ print("LINKWARN\t" + spec.name + "\tunknown block " + spec.block); continue; }
    var spot = freeSpot(blk.size);
    if(spot == null){ print("LINKWARN\t" + spec.name + "\tno space"); continue; }
    W.tile(spot[0], spot[1]).setBlock(blk, team);
    /* keep the CENTERED rect, not the origin tile: see freeSpot */
    var loff = -Math.floor((blk.size - 1) / 2);
    placed.push([spot[0] + loff, spot[1] + loff, blk.size]);
    b.links.add(new LL(spot[0], spot[1], spec.name, true));
    print("LINK\t" + spec.name + "\t" + spot[0] + "\t" + spot[1] + "\t" + blk.name);
}
%(pads)s
%(compile)s
b.updateCode(s);
/* compile errors (undefined label, malformed statement) leave no instructions;
   fail here in ~3 s instead of after a full scene run */
var runnable = b.executor.initialized();
if(!runnable && !%(diagnostics)s){
    throw new Error("PREFLIGHT: program did not compile (run mlog.py check; "
                    + "a jump target out of range/undefined label compiles to nothing)");
}
/* a link that is out of range/silently unbound becomes a null constant; catch it
   now instead of debugging "why is cell1 null" after a long run */
for(var k = 0; k < b.links.size; k++){
    var lk = b.links.get(k);
    if(!lk.valid){
        throw new Error("PREFLIGHT: link '" + lk.name + "' did not bind (missing target "
                        + "or farther than 10 tiles)");
    }
}
/* updateTile() copies the team in; paused world never runs it */
b.executor.team = Packages.mindustry.game.Team.sharded;
/* a block placed via setBlock keeps efficiency 0 until updateEfficiency runs */
b.efficiency = 1;
/* probe hook: runs after the program compiled and the units exist but before the
   first instruction executes, so a probe can put the world in a state (kill the
   bound unit, hand it to another processor) and then let the program see it.
   `b` is this processor's building; empty when the caller passes nothing. */
%(setup)s
if(runnable){ %(loop)s }
%(pads_report)s
print("@@BEGIN");
var vs = b.executor.vars;
for(var i = 0; i < vs.length; i++){
    var v = vs[i], val;
    if(v.isobj){ val = String(v.objval); } else { val = "" + v.numval; }
    print("VAR\t" + v.name + "\t" + val);
}
print("COUNTER\t" + b.executor.counter.numval);
print("IPT\t" + b.executor.ipt.numval);
print("BLOCK\t" + b.block.name);
print("RAN\t" + runnable);
print("ACC\t" + b.accumulator);
print("TEXT\t" + String(b.executor.textBuffer.toString()).replace(/\n/g, "\\n"));
print("@@END");
'''

SCENE_JS = r'''
var content = Vars.content;
var team = Packages.mindustry.game.Team.sharded;
var LL = Packages.mindustry.world.blocks.logic.LogicBlock.LogicLink;
var tiles = %(tiles)s;
for(var i = 0; i < tiles.length; i++){
    var t = tiles[i];
    var blk = content.block(t.block);
    if(blk == null){ print("SKIP\t" + t.block); continue; }
    Vars.world.tile(t.x, t.y).setBlock(blk, team);
}
var procs = [];
for(var i = 0; i < tiles.length; i++){
    var t = tiles[i];
    if(!t.logic){ continue; }
    var b = Vars.world.build(t.x, t.y);
    if(b == null){ print("NOPROC\t" + t.x + "," + t.y); continue; }
    b.code = t.logic;
    b.links.clear();
    for(var j = 0; j < t.links.length; j++){
        var l = t.links[j];
        b.links.add(new LL(l.x, l.y, l.name, true));
    }
    b.updateCode(b.code);
    if(!b.executor.initialized()){
        throw new Error("PREFLIGHT: processor at " + t.x + "," + t.y + " did not compile");
    }
    for(var k = 0; k < b.links.size; k++){
        var lk = b.links.get(k);
        if(!lk.valid){
            throw new Error("PREFLIGHT: processor at " + t.x + "," + t.y + " link '"
                            + lk.name + "' did not bind (missing target or farther than 10 tiles)");
        }
    }
    /* updateTile() copies the team in; paused world never runs it */
    b.executor.team = team;
    b.efficiency = 1;
    procs.push(b);
}
print("PROCS\t" + procs.length);
%(loop)s
for(var i = 0; i < procs.length; i++){
    var b = procs[i];
    print("@@BEGIN\t" + b.tileX() + "," + b.tileY());
    var vs = b.executor.vars;
    for(var j = 0; j < vs.length; j++){
        var v = vs[j], val;
        if(v.isobj){ val = String(v.objval); } else { val = "" + v.numval; }
        print("VAR\t" + v.name + "\t" + val);
    }
    print("COUNTER\t" + b.executor.counter.numval);
    print("IPT\t" + b.executor.ipt.numval);
    print("ACC\t" + b.accumulator);
    print("TEXT\t" + String(b.executor.textBuffer.toString()).replace(/\n/g, "\\n"));
    print("@@END");
}
'''

# --- batched scene loading -------------------------------------------------
# A scene with thousands of processors cannot travel through one js command:
# the tile JSON (code included) grows past what the GraalJS bridge will carry
# (~700 MB for 22k processors) and it dies with
#   NullPointerException: Cannot invoke "rhino.classfile.FieldOrMethodRef.getType()"
# Loading in batches keeps every single command small. globalThis.procs holds
# the processor handles between commands (the JS context survives across js()).
SCENE_PLACE_JS = r'''
var content = Vars.content;
var team = Packages.mindustry.game.Team.sharded;
var tiles = %(tiles)s;
var placed = 0;
for(var i = 0; i < tiles.length; i++){
    var t = tiles[i];
    var blk = content.block(t.block);
    if(blk == null){ print("SKIP\t" + t.block); continue; }
    Vars.world.tile(t.x, t.y).setBlock(blk, team);
    placed++;
}
print("PLACED\t" + placed);
'''

SCENE_CONF_JS = r'''
var content = Vars.content;
var team = Packages.mindustry.game.Team.sharded;
var LL = Packages.mindustry.world.blocks.logic.LogicBlock.LogicLink;
var tiles = %(tiles)s;
if(globalThis.procs === undefined){ globalThis.procs = []; }
var procs = globalThis.procs;
for(var i = 0; i < tiles.length; i++){
    var t = tiles[i];
    if(!t.logic){ continue; }
    var b = Vars.world.build(t.x, t.y);
    if(b == null){ print("NOPROC\t" + t.x + "," + t.y); continue; }
    b.code = t.logic;
    b.links.clear();
    for(var j = 0; j < t.links.length; j++){
        var l = t.links[j];
        b.links.add(new LL(l.x, l.y, l.name, true));
    }
    b.updateCode(b.code);
    if(!b.executor.initialized()){
        throw new Error("PREFLIGHT: processor at " + t.x + "," + t.y + " did not compile");
    }
    for(var k = 0; k < b.links.size; k++){
        var lk = b.links.get(k);
        if(!lk.valid){
            throw new Error("PREFLIGHT: processor at " + t.x + "," + t.y + " link '"
                            + lk.name + "' did not bind (missing target or farther than 10 tiles)");
        }
    }
    b.executor.team = team;
    b.efficiency = 1;
    procs.push(b);
}
print("PROCS\t" + procs.length);
'''

SCENE_DUMP_JS = r'''
var procs = globalThis.procs;
var want = %(want)s;
var dumped = 0;
for(var i = 0; i < procs.length; i++){
    var b = procs[i];
    var vs = b.executor.vars;
    var keep = (want == null);
    if(!keep){
        for(var j = 0; j < vs.length; j++){
            if(want.indexOf(vs[j].name) >= 0){ keep = true; break; }
        }
    }
    if(!keep){ continue; }
    dumped++;
    print("@@BEGIN\t" + b.tileX() + "," + b.tileY());
    for(var j = 0; j < vs.length; j++){
        var v = vs[j], val;
        if(v.isobj){ val = String(v.objval); } else { val = "" + v.numval; }
        print("VAR\t" + v.name + "\t" + val);
    }
    print("COUNTER\t" + b.executor.counter.numval);
    print("IPT\t" + b.executor.ipt.numval);
    print("ACC\t" + b.accumulator);
    print("TEXT\t" + String(b.executor.textBuffer.toString()).replace(/\n/g, "\\n"));
    print("@@END");
}
print("DUMPED\t" + dumped);
'''


def _scene_chunks(tiles, size):
    """Split tiles so that no chunk carries more than size entries."""
    return [tiles[i:i + size] for i in range(0, len(tiles), size)]


UNIT_JS = r'''
var spec = %(spec)s;            /* [[name, count], ...] */
var team = Packages.mindustry.game.Team.sharded;
var wantx = %(wx)f, wanty = %(wy)f;
Vars.state.rules.logicUnitControl = true;
/* Two distinct failure modes, do not conflate them:
 * (a) BLANK WORLD HAS NO CORES -> Units.getCap() == 0 -> every unit is removed
 *     inside add() before any update() runs. This is what "spawned and died
 *     instantly" looked like historically; raising the cap is what makes the
 *     spawn possible at all.
 * (b) SPAWNING ON A SOLID TILE was believed to kill the unit on its first
 *     update(). NOT reproduced on v160.7: a dagger placed on stone-wall or on a
 *     micro-processor tile stayed alive for 5 updated ticks
 *     (out/takeover-20261024/07-assert-runs.md, assertion L2-07 overturned).
 * freeSpot() is therefore kept only to get a clean landing spot: the processor
 * is placed at the base tile, and a +16px offset can land inside a multi-tile
 * core. It skips the base tile itself and spawns at the tile center. */
function freeSpot(cx, cy){
    var bw = Math.floor(cx / 8), bh = Math.floor(cy / 8);
    for(var r = 1; r < 16; r++){
        for(var dx = -r; dx <= r; dx++){
            for(var dy = -r; dy <= r; dy++){
                if(Math.max(Math.abs(dx), Math.abs(dy)) != r) continue;
                var x = bw + dx, y = bh + dy;
                if(x < 1 || y < 1 || x >= Vars.world.width() - 1 || y >= Vars.world.height() - 1) continue;
                var t = Vars.world.tile(x, y);
                if(t.block().name != "air" || t.floor().solid || t.floor().isLiquid) continue;
                return [x * 8 + 4, y * 8 + 4];
            }
        }
    }
    return [cx, cy];
}
var made = 0;
var SPAWNED = [];
var total = 0;
for(var s = 0; s < spec.length; s++){
    var name = spec[s][0], n = spec[s][1];
    total += n;
    var ut = null;
    for(var i = 0; i < Vars.content.units().size; i++){
        var t = Vars.content.units().get(i);
        if(t.name == name){ ut = t; break; }
    }
    if(ut == null){ print("NOUNIT\t" + name); continue; }
    for(var k = 0; k < n; k++){
        var sp = freeSpot(wantx + (k %% 5) * 16, wanty + ((k / 5) | 0) * 16);
        SPAWNED.push(ut.spawn(team, sp[0], sp[1]));
        made++;
    }
}
if(made < total){
    throw new Error("PREFLIGHT: requested " + total + " unit(s), spawned " + made
                    + " (unknown unit name? see --units)");
}
/* paused world never runs Teams.updateTeamStats, so ubind would see no units */
Vars.state.teams.updateTeamStats();
print("UNITS\t" + made);
'''


WORLD_JS = r'''
var GS = Packages.mindustry.core.GameState; var ST = GS.State;
var GB = Packages.mindustry.gen.Groups.build;
/* Snapshot first: update() may add/remove buildings and shift the group. */
function worldTick(){
    %(power_update)s
    var arr = [];
    for(var k = 0; k < GB.size(); k++){ arr.push(GB.index(k)); }
    for(var k = 0; k < arr.length; k++){
        var w = arr[k];
        if(w.block.name.indexOf("processor") >= 0) continue;
        %(fixed_power)s
        w.update();
    }
}
'''

# Weather is a real state machine in Logic.updateWeather(): every entry has a
# cooldown; when it fires, an event is created with a random duration and the
# cooldown becomes duration + random frequency. WeatherState.update() counts
# life down (Time.delta per tick), fades opacity, applies its status effect to
# units, and removes itself at life < 0 -- that is exactly what `weathersense`
# / `weatherset` observe and drive.
WEATHER_JS = r'''
var GW = Packages.mindustry.gen.Groups.weather;
var WR = Vars.state.rules.weather;
var WSEED = 123456789;
function wrnd(){ WSEED = (WSEED * 16807) % 2147483647; return WSEED / 2147483647.0; }
function weatherTick(){
    for(var i = 0; i < WR.size; i++){
        var e = WR.get(i);
        if(e.weather == null) continue;
        e.cooldown -= Time.delta;
        if((e.cooldown < 0 || e.always) && !e.weather.isActive()){
            var dur = e.always ? 1e30 : e.minDuration + wrnd() * (e.maxDuration - e.minDuration);
            e.cooldown = dur + e.minFrequency + wrnd() * (e.maxFrequency - e.minFrequency);
            e.weather.create(e.intensity, dur);
        }
    }
    GW.update();
}
'''


def weather_js(name: str, intensity: float = 1.0) -> str:
    return ("var W = Vars.content.weather('%s');"
            "if(W == null){ throw new Error('unknown weather: %s'); }"
            "W.create(%f, 1e30);"
            "print('WEATHER\\t' + W.name);" % (name, name, intensity))



UNITS_JS = r'''
var UG = Packages.mindustry.gen.Groups.unit;
var UNIT_ALL = %(all)s;
/* Snapshot first: update() may kill/despawn units and shift the group. */
function unitTick(){
    var arr = [];
    for(var k = 0; k < UG.size(); k++){ arr.push(UG.index(k)); }
    for(var k = 0; k < arr.length; k++){
        var u = arr[k];
        if(!u.isValid()) continue;
        /* logic-controlled units always; --unit-ai all adds the world's own AI */
        if(UNIT_ALL || u.controller() instanceof Packages.mindustry.ai.types.LogicAI) u.update();
    }
}
'''

# Cheap first-tick checks: a unit spawned on a solid tile is killed by its first
# update() (900 HP gone in one frame) and the run then looks like "the unit did
# not move". Fail at tick 1 with the real cause instead of after 1200 ticks.
PREFLIGHT_JS = r'''
function preflightTick(){
    if(typeof SPAWNED === "undefined") return;
    for(var i = 0; i < SPAWNED.length; i++){
        var u = SPAWNED[i];
        if(u == null || !u.isValid()){
            throw new Error("PREFLIGHT: a spawned unit died on tick 1 (solid spawn tile? "
                            + "use --unit-pos; pass --no-preflight to ignore)");
        }
    }
}
'''


COMBAT_JS = r'''
var GBU = Packages.mindustry.gen.Groups.bullet;
var GUU = Packages.mindustry.gen.Groups.unit;
/* Logic.updateEntities() runs bullet/unit physics first, then the updates,
   then bullet.update()/collide(). Mirror that order, otherwise real bullets
   never move and never deal damage. */
function combatPre(){ GBU.updatePhysics(); GUU.updatePhysics(); }
function combatPost(){ GBU.update(); GBU.collide(); }
'''

# Per-tick trace of the unit a processor is steering. Coordinates are tiles.
# Columns: unit,tick,ux,uy,uhp,range,tx,ty,dist,cx,cy,chp,bullets,shots
TRACE_JS = r'''
var TRACE = [];
var GBT = Packages.mindustry.gen.Groups.build;
var GUT = Packages.mindustry.gen.Groups.unit;
var GBL = Packages.mindustry.gen.Groups.bullet;
function traceCore(u){
    var best = null, bd = 1e30;
    for(var i = 0; i < GBT.size(); i++){
        var w = GBT.index(i);
        if(w == null || !w.isValid()) continue;
        if(!(w.block instanceof Packages.mindustry.world.blocks.storage.CoreBlock)) continue;
        if(w.team == u.team) continue;
        var dx = w.x - u.x, dy = w.y - u.y;
        var d = Math.sqrt(dx*dx + dy*dy);
        if(d < bd){ bd = d; best = w; }
    }
    return best;
}
function traceTick(){
    for(var i = 0; i < GUT.size(); i++){
        var u = GUT.index(i);
        if(u == null || !u.isValid()) continue;
        var ctl = u.controller();
        if(!(ctl instanceof Packages.mindustry.ai.types.LogicAI)) continue;
        var tx = "", ty = "", dist = "";
        if(("" + ctl.aimControl) == "target"){
            tx = ctl.posTarget.x / 8.0; ty = ctl.posTarget.y / 8.0;
            var ax = ctl.posTarget.x - u.x, ay = ctl.posTarget.y - u.y;
            dist = Math.sqrt(ax*ax + ay*ay) / 8.0;
        }
        var c = traceCore(u);
        var cx = "", cy = "", chp = "";
        if(c != null){ cx = c.x / 8.0; cy = c.y / 8.0; chp = c.health; }
        var shots = 0;
        try { for(var m = 0; m < u.mounts.length; m++){ shots += u.mounts[m].totalShots; } } catch(e){}
        TRACE.push(["TRACE", u.type.name, Vars.state.tick, (u.x/8.0), (u.y/8.0), u.health,
                    (u.type.maxRange/8.0), tx, ty, dist, cx, cy, chp, GBL.size(), shots].join("\t"));
    }
}
'''


def _world_js(power: float | None, unit_ai: str = "logic") -> str:
    # None lets the engine own power.status, which also holds battery charge.
    world = WORLD_JS % {
        "power_update": "Packages.mindustry.gen.Groups.powerGraph.update();" if power is None else "",
        "fixed_power": f"if(w.power != null) w.power.status = {power};" if power is not None else "",
    }
    return world + UNITS_JS % {"all": "true" if unit_ai == "all" else "false"}


def _world_tick_js(power: float | None, unit_ai: str) -> str:
    # The live engine steps units before power graphs, then updates buildings.
    calls = "unitTick(); worldTick();" if power is None else "worldTick(); unitTick();"
    return _world_js(power, unit_ai) + calls



ITRACE_JS = """
var ITRACE = [];
var ITR_CODE = __CODE__;
var ITR_VARS = __VARS__;
function itr_val(ex, name){
  try{
    var v = ex.optionalVar(name);
    if(v == null) return "?";
    return v.isobj ? "<obj>" : String(v.numval);
  }catch(e){ return "?"; }
}
function itr_sample(ex, t){
  if(ex.instructions.length === 0) return;
  var counter = ex.counter.numval;
  var pc = (counter < 0 || counter >= ex.instructions.length) ? 0 : counter|0;
  var src = (ex.instructions.length === ITR_CODE.length && pc < ITR_CODE.length) ? ITR_CODE[pc] : "";
  var extra = "";
  for(var q = 0; q < ITR_VARS.length; q++){ extra += ITR_VARS[q] + "=" + itr_val(ex, ITR_VARS[q]) + ";"; }
  ITRACE.push("ITRACE\t" + t + "\t" + pc + "\t" + extra + "\t" + src);
}
function itr_exec(obj, t){
  var ex = obj.executor;
  if(!obj.enabled || !ex.initialized()) return;
  obj.accumulator += obj.block.instructionsPerTick;
  var guard = 0;
  while(obj.accumulator >= 1){
    itr_sample(ex, t);
    ex.runOnce();
    obj.accumulator -= 1;
    if(++guard > 2000) break;
    if(ex.yield){ ex.yield = false; obj.accumulator = 0; break; }
  }
}
""".strip()

PUSH_DEF_JS = (
    "var PUSHF = __PATH__;"
    "_pushNow = function(){"
    " var o = [];"
    # EntityGroup has no get(int) in Rhino; each(Cons) coerces a JS function fine
    " Packages.mindustry.gen.Groups.unit.each(function(u){"
    "  if(u == null || u.dead) return;"
    "  var c = 0, ct = u.controller();"
    "  if(ct != null){ var cn = String(ct.getClass().getName());"
    "   if(cn.indexOf('Player') >= 0) c = 2; else if(cn.indexOf('LogicAI') >= 0) c = 1; }"
    "  var amt = 0, itm = null;"
    "  try{ if(u.stack != null){ amt = u.stack.amount; itm = String(u.stack.item.name); } }catch(e0){}"
    "  o.push({type: String(u.type.name), x: u.x / 8, y: u.y / 8, amount: amt, item: itm, ctrl: c, rot: u.rotation});"
    " });"
    # 直接覆写: 读端每 0.12 s 抽一次并自带重试, 偶尔抽到半截会重读.
    # (试过 tmp + Files.move 原子改名: Windows 上读端正开着文件时改名会 AccessDenied)
    # 数组带上"模拟器世界多大": 世界侧要把这个尺寸画成一个边界框,
    # 让玩家一眼看出这块沙盘里仿真的范围(单位跑不出这个框)
    # scene/label 让世界侧自己知道"这块影子是哪张场景铺出来的":
    # 只给 --watch-feed 不配 --watch-scene 时，投影导演按这里给的路径补场景，
    # 否则它只有单位没有建筑（框、雷、日志板全都起不来）。
    " var pay = {world: [Vars.world.width(), Vars.world.height()], anchor: __ANCHOR__,"
    " scene: __SCENE__, label: __LABEL__, units: o};"
    " var w2 = new java.io.PrintWriter(PUSHF, 'UTF-8'); w2.print(JSON.stringify(pay)); w2.close();"
    "};"
)


def _push_js(path: str, every: int, anchor=None, scene=None, label=None) -> str:
    """状态镜推送: 每 every tick 把 Groups.unit 的 (兵种, 世界坐标, 携带量, 控制者)
    覆写进一个 JSON 文件; world_server 的 mirror_feed 线程读它并画成 marker.

    scene / label 是"这张影子来自哪张场景"的出处: world_server 只拿到 feed 时
    也能按它把建筑复刻出来（见 projection_director 的 feed 自足模式）。"""
    # the JVM's cwd is a temp dir, so a relative path would land somewhere else
    full = os.path.abspath(path).replace("\\", "/")
    fields = {
        "__PATH__": full,
        "__ANCHOR__": list(anchor) if anchor else None,
        "__SCENE__": scene.replace("\\", "/") if scene else None,
        "__LABEL__": label or None,
    }
    body = re.sub(r"__PATH__|__ANCHOR__|__SCENE__|__LABEL__",
                  lambda match: json.dumps(fields[match.group()]), PUSH_DEF_JS)
    return (" if(i == 0){" + body + "}"
            " if(i %% %d == 0) _pushNow();" % max(1, int(every)))


AUTO_POWER_SOURCE_JS = """
(function(){
    var input = %s, entries = input[0], named = input[1], base = input[2];
    var world = Vars.world, target = null, targetName = null;
    for(var i = 0; i < entries.length; i++){
        var entry = entries[i], build = world.build(entry[1], entry[2]);
        if(build == null || build.power == null || (!named && !build.block.consumesPower)) continue;
        if(target != null && target.power.graph != build.power.graph)
            throw new Error("scene has multiple power grids; specify power_target");
        if(target == null){ target = build; targetName = entry[0]; }
    }
    if(target == null) throw new Error("no powered target found; specify a powered scene building with power_target");
    function report(source, added){
        print("AUTO_POWER " + JSON.stringify({x: source.tileX(), y: source.tileY(), target: targetName, added: added}));
    }
    var producers = target.power.graph.producers;
    for(var p = 0; p < producers.size; p++){
        var source = producers.get(p);
        if(source.block == Blocks.powerSource && source.enabled){ report(source, false); return; }
    }
    var links = java.lang.reflect.Array.newInstance(java.lang.Class.forName("arc.math.geom.Point2"), 1);
    var directions = [[1,0],[-1,0],[0,1],[0,-1]];
    for(var r = 1; r <= Math.ceil(Blocks.powerSource.laserRange); r++){
        for(var dx = -r; dx <= r; dx++){
            for(var dy = -r; dy <= r; dy++){
                if(Math.max(Math.abs(dx), Math.abs(dy)) != r) continue;
                var x = target.tileX() + dx, y = target.tileY() + dy;
                if(x == base[0] && y == base[1]) continue;
                var tile = world.tile(x, y);
                if(tile == null || tile.block() != Blocks.air || tile.floor().isLiquid || tile.floor().solid) continue;
                var separateGrid = false;
                for(var d = 0; d < directions.length; d++){
                    var neighbor = world.build(x + directions[d][0], y + directions[d][1]);
                    if(neighbor != null && neighbor.team == target.team && neighbor.power != null &&
                       neighbor.power.graph != target.power.graph){ separateGrid = true; break; }
                }
                if(separateGrid) continue;
                tile.setBlock(Blocks.powerSource, target.team);
                var source = tile.build;
                if(source.block.linkValid(source, target)){
                    links[0] = new Packages.arc.math.geom.Point2(-dx, -dy);
                    source.configured(null, links);
                    if(source.power.links.contains(target.pos()) && source.power.graph == target.power.graph){
                        report(source, true);
                        return;
                    }
                }
                tile.setBlock(Blocks.air);
            }
        }
    }
    throw new Error("no free tile in range for an automatic power-source");
})();
"""


def _power_profile_js(profile: list[dict]) -> str:
    # Only validated numeric pairs enter JS. Check the layout after it has
    # loaded, since a scene can place the source as well as a save.
    schedule = [[point["tick"], point["power_per_second"]] for point in profile]
    return """
        var gridSchedule = %s, gridPoint = 0;
        var gridSource = Blocks.powerSource, sourceFound = false;
        var graphs = Packages.mindustry.gen.Groups.powerGraph;
        for(var gi=0; gi<graphs.size() && !sourceFound; gi++){
            var producers = graphs.index(gi).graph.producers;
            for(var pi=0; pi<producers.size; pi++){
                if(producers.get(pi).block == gridSource){ sourceFound = true; break; }
            }
        }
        if(!sourceFound) throw new Error("power_profile requires a power-source block in the loaded world");
        function applyGridProfile(tick){
            if(gridPoint < gridSchedule.length && gridSchedule[gridPoint][0] == tick){
                gridSource.powerProduction = gridSchedule[gridPoint][1] / 60;
                gridPoint++;
            }
        }
    """ % json.dumps(schedule, allow_nan=False, separators=(",", ":"))


def _loop_js(obj: str, steps: int, ticks: bool, update: str = "none", power: float | None = 1.0,
             combat: bool = False, trace: bool = False, unit_ai: str = "logic",
             preflight: bool = True, itrace: dict | None = None,
             tick_extra: str = "", power_profile: list[dict] | None = None) -> str:
    """Instruction mode steps the executor directly; tick mode drives updateTile.

    In tick mode Time.delta must be 1.0: edelta() = delta * timeScale feeds the
    accumulator (ipt per tick) and WaitI adds Time.delta/60 per execution, so
    1.0 is the value that makes 60 ticks equal one second.

    itrace={"code": [...], "vars": [...]} switches tick mode from updateTile()
    to a hand-driven loop that records (tick, pc, vars, source line) per
    executed instruction. That is the only way to see which line ran: reading
    @counter after updateTile only tells you where the tick ended. In instruction
    mode no world ticks advance, so every trace row uses tick 0.
    """
    itr_setup = itr_dump = ""
    if itrace is not None:
        values = {"__CODE__": itrace.get("code", []), "__VARS__": itrace.get("vars", [])}
        itr_setup = re.sub(r"__CODE__|__VARS__", lambda m: json.dumps(values[m[0]], ensure_ascii=False),
                           ITRACE_JS)
        itr_dump = " for(var q = 0; q < ITRACE.length; q++){ print(ITRACE[q]); }"
    if ticks:
        world = _world_tick_js(power, unit_ai) if update == "all" else ""
        profile_setup = _power_profile_js(power_profile) if power_profile else ""
        if power_profile:
            world = "applyGridProfile(i + 1); " + world
        setup = PREFLIGHT_JS + WEATHER_JS
        pre = post = ""
        if combat:
            setup += COMBAT_JS
            pre = "combatPre(); "
            post = " combatPost();"
        if trace:
            setup += TRACE_JS
        setup += itr_setup
        trace_tick = " traceTick();" if trace else ""
        if itrace is not None:
            body = pre + world + tick_extra + " itr_exec(%s, i);" % obj + post + trace_tick
        else:
            body = pre + world + tick_extra + " %s.updateTile();" % obj + post + trace_tick
        check = " if(i == 0) preflightTick();" if preflight else ""
        dump = ""
        if trace:
            dump += " for(var q = 0; q < TRACE.length; q++){ print(TRACE[q]); }"
        dump += itr_dump
        return (profile_setup + "var GS = Packages.mindustry.core.GameState; var ST = GS.State;"
                " Vars.state.set(ST.playing); Time.delta = 1.0; %s"
                " try{ for(var i = 0; i < %d; i++){"
                " Vars.state.tick++; Time.update(); Vars.logicVars.update(); weatherTick(); %s%s }"
                " } finally { Vars.state.set(ST.paused); }%s" % (setup, steps, body, check, dump))
    sample = f"itr_sample({obj}.executor, 0); " if itrace is not None else ""
    return (itr_setup + f"for(var i = 0; i < {steps}; i++){{ {sample}{obj}.executor.runOnce(); }}"
            + itr_dump)


def _scene_loop_js(steps: int, ticks: bool, update: str = "none", power: float | None = 1.0,
                   combat: bool = False, trace: bool = False, unit_ai: str = "logic",
                   preflight: bool = True) -> str:
    """Same, but tick every processor together so cross-reads see one world.

    A scene has N processors, so the tick loop must nest: outer ticks, inner
    processors. Iterating each processor for `steps` ticks in isolation would
    let one processor run far ahead of the other.
    """
    if ticks:
        world = _world_tick_js(power, unit_ai) if update == "all" else ""
        setup = PREFLIGHT_JS + WEATHER_JS
        pre = post = ""
        if combat:
            setup += COMBAT_JS
            pre = "combatPre(); "
            post = " combatPost();"
        if trace:
            setup += TRACE_JS
        dump = (" for(var q = 0; q < TRACE.length; q++){ print(TRACE[q]); }" if trace else "")
        check = " if(t == 0) preflightTick();" if preflight else ""
        return ("var GS = Packages.mindustry.core.GameState; var ST = GS.State;"
                " Vars.state.set(ST.playing); Time.delta = 1.0; %s"
                " try{ for(var t = 0; t < %d; t++){"
                " Vars.state.tick++; Time.update(); Vars.logicVars.update(); weatherTick(); %s"
                " for(var j = 0; j < procs.length; j++){ procs[j].updateTile(); }"
                " %s%s%s }"
                " } finally { Vars.state.set(ST.paused); }%s"
                % (setup, steps, pre + world, post, " traceTick();" if trace else "", check, dump))
    return ("for(var i = 0; i < procs.length; i++){"
            " for(var k = 0; k < %d; k++){ procs[i].executor.runOnce(); } }" % steps)
