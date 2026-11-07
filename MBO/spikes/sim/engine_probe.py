"""engine_probe.py -- MBO 硬核 spike: 把真实工厂蓝图放进 v160.7 官方服务端真引擎跑 tick。

用法（Windows, pwsh）:
    python MBO\\spikes\\sim\\engine_probe.py --mode introspect
    python MBO\\spikes\\sim\\engine_probe.py --mode place
    python MBO\\spikes\\sim\\engine_probe.py --mode power
    python MBO\\spikes\\sim\\engine_probe.py --mode blueprint --msch logic-corpus/.../metaglass-2.msch --ticks 600
    python MBO\\spikes\\sim\\engine_probe.py --mode all

自带超时与进程清理：结束/异常都会 kill java，并向 out/_probe/ 写日志与 JSON。
不 import tools/mlogsim.py（只复制其思路）；只 import tools/msch.py 做离线解析。
"""
from __future__ import annotations

import argparse
import atexit
import base64
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# ROOT = F:\OneDrive\桌面\AtomicStates
TOOLS = os.path.join(ROOT, "tools")
OUT = os.path.join(ROOT, "out", "_probe")
JAR = os.path.join(ROOT, "out", "_server160.jar")
JAR159 = os.path.join(ROOT, "out", "_server159.jar")
JAVA = os.path.join(ROOT, "out", "jre21", "jdk-21.0.5+11-jre", "bin", "java.exe")

sys.path.insert(0, TOOLS)


# --------------------------------------------------------------------- process
def _job_kill_with_parent(proc):
    """Windows job object so the JVM dies with this process (KILL_ON_JOB_CLOSE)."""
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.CreateJobObjectW.restype = ctypes.c_void_p
        k32.CreateJobObjectW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
        k32.SetInformationJobObject.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                               ctypes.c_void_p, wintypes.DWORD]
        k32.AssignProcessToJobObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

        class _BASE(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64),
                        ("PerJobUserTimeLimit", ctypes.c_int64),
                        ("LimitFlags", wintypes.DWORD),
                        ("MinimumWorkingSetSize", ctypes.c_size_t),
                        ("MaximumWorkingSetSize", ctypes.c_size_t),
                        ("ActiveProcessLimit", wintypes.DWORD),
                        ("Affinity", ctypes.c_size_t),
                        ("PriorityClass", wintypes.DWORD),
                        ("SchedulingClass", wintypes.DWORD)]

        class _IO(ctypes.Structure):
            _fields_ = [("a", ctypes.c_ulonglong), ("b", ctypes.c_ulonglong),
                        ("c", ctypes.c_ulonglong), ("d", ctypes.c_ulonglong),
                        ("e", ctypes.c_ulonglong), ("f", ctypes.c_ulonglong)]

        class _EXT(ctypes.Structure):
            _fields_ = [("BasicLimitInformation", _BASE), ("IoInfo", _IO),
                        ("ProcessMemoryLimit", ctypes.c_size_t),
                        ("JobMemoryLimit", ctypes.c_size_t),
                        ("PeakProcessMemoryUsed", ctypes.c_size_t),
                        ("PeakJobMemoryUsed", ctypes.c_size_t)]

        job = k32.CreateJobObjectW(None, None)
        info = _EXT()
        info.BasicLimitInformation.LimitFlags = 0x2000
        if not job or not k32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info)):
            return None
        if not k32.AssignProcessToJobObject(job, ctypes.c_void_p(int(proc._handle))):
            return None
        return job
    except Exception:
        return None


class SimError(RuntimeError):
    pass


class Server:
    """Minimal console-driven Mindustry server (same launch shape as mlogsim)."""

    def __init__(self, jar: str = JAR, java: str = JAVA, world: int = 128, name: str = "run"):
        self.workdir = tempfile.mkdtemp(prefix="mbo-", dir=OUT)
        os.makedirs(os.path.join(self.workdir, "config", "logs"), exist_ok=True)
        self.t_start = time.time()
        self.proc = subprocess.Popen(
            [java, "-Dstdout.encoding=UTF-8", "-Dstderr.encoding=UTF-8", "-jar", jar],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            cwd=self.workdir, text=True, encoding="utf-8", errors="replace", bufsize=1)
        self._job = _job_kill_with_parent(self.proc)
        self._closed = False
        self.all: list[str] = []
        self.lines: queue.Queue = queue.Queue()
        threading.Thread(target=self._pump, daemon=True).start()
        _LIVE.append(self)
        try:
            self.wait_for("Server loaded.", 90)
            self.t_loaded = time.time()
            self.world = world
            self.js(LOAD_JS % {"n": world})
            self.t_world = time.time()
        except Exception:
            self.close()
            raise

    def _pump(self):
        for line in self.proc.stdout:
            self.lines.put(line.rstrip("\r\n"))
        self.lines.put(None)

    def send(self, cmd: str):
        self.proc.stdin.write(cmd + "\n")
        self.proc.stdin.flush()

    def wait_for(self, needle: str, timeout: float = 60.0) -> list[str]:
        deadline = time.time() + timeout
        out = []
        while time.time() < deadline:
            try:
                line = self.lines.get(timeout=0.2)
            except queue.Empty:
                continue
            if line is None:
                raise SimError("server exited:\n" + "\n".join(self.all[-25:]))
            self.all.append(line)
            out.append(line)
            if needle in line:
                return out
        raise SimError("timeout waiting %r; tail:\n%s" % (needle, "\n".join(self.all[-25:])))

    def js(self, script: str, timeout: float = 90.0) -> list[str]:
        """Run one `js` command (single line!) and return its printed lines."""
        if "\n" in script:
            script = " ".join(script.splitlines())
        self.send("js " + script)
        lines = self.wait_for("undefined", timeout)
        out = [ln.split("[none/base.js]:", 1)[1].strip() for ln in lines if "[none/base.js]:" in ln]
        err = [ln for ln in lines if "Exception" in ln or "Error:" in ln]
        if err:
            raise SimError("\n".join(err))
        return out

    def close(self):
        if getattr(self, "_closed", False):
            return
        self._closed = True
        try:
            _LIVE.remove(self)
        except ValueError:
            pass
        proc = self.proc
        try:
            if proc.poll() is None:
                try:
                    self.send("exit")
                    proc.wait(timeout=12)
                except Exception:
                    proc.kill()
                    try:
                        proc.wait(timeout=8)
                    except Exception:
                        pass
        finally:
            for st in (proc.stdin, proc.stdout):
                try:
                    st.close()
                except Exception:
                    pass


_LIVE: list[Server] = []
atexit.register(lambda: [s.close() for s in list(_LIVE)])


# --------------------------------------------------------------------------- js
LOAD_JS = r"""(function(){
Vars.world.loadGenerator(%(n)d,%(n)d,function(tiles){
  tiles.fill();
  var floor = Vars.content.block('stone').asFloor();
  for(var x = 0; x < %(n)d; x++){ for(var y = 0; y < %(n)d; y++){ tiles.get(x,y).setFloor(floor); } }
});
print("WORLD\t" + Vars.world.width() + "x" + Vars.world.height());
})();"""

# What can we call from the console? Enumerate the classes the spike needs.
INTROSPECT_JS = r"""(function(){
function C(n){ try { return Packages.java.lang.Class.forName(n); } catch(e){ return null; } }
function ms(n){ var c=C(n); if(c==null) return "CLASS-MISSING";
  var a=[], m=c.getDeclaredMethods();
  for(var i=0;i<m.length;i++){ var x=m[i]; a.push(x.getName()+"/"+(x.getModifiers()&8?"S":"I")+"("+x.getParameterTypes().length+")"); }
  return a.sort().join(","); }
function fs(n){ var c=C(n); if(c==null) return "CLASS-MISSING";
  var a=[], f=c.getDeclaredFields();
  for(var i=0;i<f.length;i++){ a.push(f[i].getName()+":"+f[i].getType().getSimpleName()); }
  return a.sort().join(","); }
print("STATE\t" + Vars.state.tick + "\tplaying=" + Vars.state.isPlaying()
      + "\tworld=" + Vars.world.width() + "x" + Vars.world.height()
      + "\tbuildings=" + Packages.mindustry.gen.Groups.build.size());
print("CLS\tmindustry.game.Schematics\t" + ms("mindustry.game.Schematics"));
print("CLS\tmindustry.game.Schematic\t" + ms("mindustry.game.Schematic"));
print("FLD\tmindustry.game.Schematic\t" + fs("mindustry.game.Schematic"));
print("CLS\tmindustry.core.Logic\t" + ms("mindustry.core.Logic"));
print("CLS\tmindustry.world.blocks.power.PowerGraph\t" + ms("mindustry.world.blocks.power.PowerGraph"));
print("CLS\tmindustry.world.modules.PowerModule\t" + ms("mindustry.world.modules.PowerModule"));
print("FLD\tmindustry.world.modules.PowerModule\t" + fs("mindustry.world.modules.PowerModule"));
print("CLS\tmindustry.gen.Building\t" + ms("mindustry.gen.Building"));
print("CLS\tmindustry.world.Tile\t" + ms("mindustry.world.Tile"));
print("CLS\tmindustry.world.blocks.power.PowerGenerator\t" + ms("mindustry.world.blocks.power.PowerGenerator"));
})();"""

# Does the dedicated server advance Vars.state.tick on its own (no players)?
CLOCK_JS = r"""(function(){
print("CLOCK\t" + Vars.state.tick + "\t" + Vars.state.isPlaying() + "\t"
      + Packages.mindustry.core.GameState.State.playing + "\t" + Vars.state.getState());
})();"""

CLOCK_PLAYING_JS = r"""(function(){
var GS = Packages.mindustry.core.GameState;
Vars.state.set(GS.State.playing);
print("CLOCKSET\t" + Vars.state.tick + "\t" + Vars.state.isPlaying() + "\t" + Vars.state.getState());
})();"""

# Multi-block placement semantics: which tile does setBlock(2x2) occupy / own the build?
PLACE_SEMANTICS_JS = r"""(function(){
var W = Vars.world, T = Packages.mindustry.game.Team.sharded;
var blk = Vars.content.block("graphite-press");
W.tile(10,10).setBlock(blk, T);
for(var x = 8; x <= 12; x++){
  for(var y = 8; y <= 12; y++){
    var t = W.tile(x,y);
    if(t.block().name != "air"){
      print("TILE\t" + x + "\t" + y + "\t" + t.block().name + "\tsize=" + t.block().size
            + "\tbuild=" + (t.build == null ? "-" : (Math.round(t.build.x/8) + "," + Math.round(t.build.y/8)))
            + "\tbuildTile=" + (t.build == null ? "-" : (t.build.tileX() + "," + t.build.tileY())));
    }
  }
}
var b = W.build(10,10);
print("BUILD_AT_10_10\t" + (b == null ? "null" : b.block.name + "\t" + b.tileX() + "," + b.tileY()));
})();"""

SIG_JS = r"""(function(){
function C(n){ try { return Packages.java.lang.Class.forName(n); } catch(e){ return null; } }
function sig(cn, want){
  var c = C(cn); if(c == null){ print("SIG\t" + cn + "\tMISSING"); return; }
  var m = c.getDeclaredMethods();
  for(var i = 0; i < m.length; i++){
    var x = m[i], n = x.getName();
    if(want.length > 0 && want.indexOf(n) < 0) continue;
    var pt = x.getParameterTypes(), a = [];
    for(var j = 0; j < pt.length; j++) a.push(pt[j].getSimpleName());
    print("SIG\t" + cn.split(".").pop() + "." + n + "(" + a.join(",") + ")" + (x.getModifiers() & 8 ? " static" : ""));
  }
}
sig("mindustry.game.Schematics", ["place", "read", "write", "create", "readBase64", "writeBase64"]);
sig("mindustry.world.Tile", ["setBlock", "getLinkedTiles"]);
sig("mindustry.world.modules.ItemModule", []);
sig("mindustry.world.modules.LiquidModule", []);
sig("mindustry.core.GameState", ["set", "isPlaying", "getState"]);
sig("mindustry.world.blocks.power.Battery", []);
sig("mindustry.world.blocks.power.PowerNode", []);
})();"""

# Real-time power test: does the running server tick the power graph?
POWER_PLACE_JS = r"""(function(){
var W = Vars.world, T = Packages.mindustry.game.Team.sharded;
function put(name, x, y, rot){
  W.tile(x,y).setBlock(Vars.content.block(name), T, rot);
  Vars.indexer.addIndex(W.tile(x,y));
}
put("power-source", 5, 5, 0);
put("battery", 6, 5, 0);
put("illuminator", 7, 5, 0);
var ps = W.build(5,5), bat = W.build(6,5), il = W.build(7,5);
print("PLACE_OK\t" + (ps!=null) + "\t" + (bat!=null) + "\t" + (il!=null));
print("GRAPH\t" + (ps.power.graph == null ? "null" : ps.power.graph.getID() + "\tprod=" + ps.power.graph.getPowerProduced()
      + "\tneed=" + ps.power.graph.getPowerNeeded() + "\tsat=" + ps.power.graph.getSatisfaction()));
print("BAT_START\t" + bat.power.graph.getBatteryStored() + "/" + bat.power.graph.getBatteryCapacity());
print("TICK0\t" + Vars.state.tick);
})();"""

POWER_READ_JS = r"""(function(){
var W = Vars.world;
var ps = W.build(5,5), bat = W.build(6,5), il = W.build(7,5);
print("TICK1\t" + Vars.state.tick);
print("GRAPH_AFTER\tprod=" + bat.power.graph.getPowerProduced() + "\tneed=" + bat.power.graph.getPowerNeeded()
      + "\tsat=" + bat.power.graph.getSatisfaction() + "\tbal=" + bat.power.graph.getPowerBalance()
      + "\tstored=" + bat.power.graph.getBatteryStored() + "/" + bat.power.graph.getBatteryCapacity());
print("STATUS\tps=" + (ps.power == null ? "-" : ps.power.status) + "\tbat=" + (bat.power == null ? "-" : bat.power.status)
      + "\til=" + (il.power == null ? "-" : il.power.status) + "\til.eff=" + il.efficiency);
})();"""

# Real-time production test: does a crafter actually craft while the server ticks itself?
PROD_PLACE_JS = r"""(function(){
var W = Vars.world, T = Packages.mindustry.game.Team.sharded;
W.tile(3,3).setBlock(Vars.content.block("graphite-press"), T, 0);
var g = W.build(3,3);
if(g == null){ print("PROD_FAIL\tno-build"); return; }
g.items.add(Vars.content.item("coal"), 20);
print("PROD_START\tcoal=" + g.items.get(Vars.content.item("coal")) + "\tgraphite=" + g.items.get(Vars.content.item("graphite"))
      + "\tprogress=" + g.progress + "\ttick=" + Vars.state.tick);
})();"""

PROD_READ_JS = r"""(function(){
var g = Vars.world.build(3,3);
print("PROD_AFTER\tcoal=" + g.items.get(Vars.content.item("coal")) + "\tgraphite=" + g.items.get(Vars.content.item("graphite"))
      + "\tprogress=" + g.progress + "\ttick=" + Vars.state.tick + "\teff=" + g.efficiency);
})();"""

DUMP_JS = r"""(function(){
var GB = Packages.mindustry.gen.Groups.build;
for(var k = 0; k < GB.size; k++){
  var b = GB.index(k), its = [];
  if(b.items != null){
    var all = Vars.content.items();
    for(var j = 0; j < all.size; j++){ var amt = b.items.get(all.get(j)); if(amt != 0) its.push(all.get(j).name + ":" + amt); }
  }
  print("B\t" + b.block.name + "\t" + b.tileX() + "," + b.tileY() + "\trot=" + b.rotation
    + "\titems=" + its.join(",")
    + "\tprog=" + Math.round(b.progress*1000)/1000 + "\teff=" + Math.round(b.efficiency*100)/100
    + "\tconsume=" + b.shouldConsume() + "\tvalid=" + b.productionValid()
    + "\tcfg=" + (b.config() == null ? "null" : String(b.config())));
}
})();"""


# ----- blueprint mode -------------------------------------------------------
# Route: fresh generated world -> core (so the game cannot declare a game over)
# -> Schematics.readBase64(.msch bytes) -> Schematics.place (the game's own
# placement path, so rotations/configs are applied exactly like a paste in game)
# -> optional sink instrumentation (item-void -> container, so output is
# countable) -> the server's own 60 Hz loop runs the world -> snapshot deltas.
BP_PREP_JS = r"""(function(){
var n = %(n)d;
var GS = Packages.mindustry.core.GameState;
try { Vars.state.set(GS.State.paused); } catch(e){ print("PAUSE_WARN\t" + e); }
Vars.world.loadGenerator(n, n, function(tiles){
  tiles.fill();
  var floor = Vars.content.block('stone').asFloor();
  for(var x = 0; x < n; x++){ for(var y = 0; y < n; y++){ tiles.get(x,y).setFloor(floor); } }
});
var R = Vars.state.rules;
try { R.canGameOver = false; } catch(e){ print("RULES_WARN\tcanGameOver " + e); }
try { R.waves = false; } catch(e){ print("RULES_WARN\twaves " + e); }
try { R.attackMode = false; } catch(e){}
try { R.infiniteResources = false; } catch(e){}
try { R.canGameOver = false; } catch(e){}
var T = Packages.mindustry.game.Team.sharded;
Vars.world.tile(8, 8).setBlock(Vars.content.block("core-shard"), T, 0);
Vars.indexer.addIndex(Vars.world.tile(8, 8));
var core = Vars.world.build(8, 8);
print("PREP\tworld=" + Vars.world.width() + "x" + Vars.world.height() + "\tcore=" + (core != null)
      + "\tcanGameOver=" + R.canGameOver + "\twaves=" + R.waves + "\tbuildings=" + Packages.mindustry.gen.Groups.build.size());
})();"""

BP_PLACE_JS = r"""(function(){
var W = Vars.world, T = Packages.mindustry.game.Team.sharded;
var sch = null;
try { sch = Packages.mindustry.game.Schematics.readBase64("%(b64)s"); }
catch(e){ print("BP\t%(i)d\tREAD_FAIL\t" + e); return; }
print("BP\t%(i)d\tREAD\t" + sch.width + "x" + sch.height + "\ttiles=" + sch.tiles.size
      + "\tcore=" + sch.hasCore() + "\tpowerCons=" + Math.round(sch.powerConsumption()*100)/100
      + "\tpowerProd=" + Math.round(sch.powerProduction()*100)/100);
try { Packages.mindustry.game.Schematics.place(sch, %(px)d, %(py)d, T, true); }
catch(e){ print("BP\t%(i)d\tPLACE_FAIL\t" + e); return; }
var indexed = 0, minx = 99999, miny = 99999, maxx = -1, maxy = -1;
for(var x = 0; x < W.width(); x++){
  for(var y = 0; y < W.height(); y++){
    var t = W.tile(x,y);
    if(t.block().name == "air") continue;
    Vars.indexer.addIndex(t);
    if(!(x >= 8 && x <= 10 && y >= 8 && y <= 10)){ indexed++;
      if(x < minx) minx = x; if(x > maxx) maxx = x;
      if(y < miny) miny = y; if(y > maxy) maxy = y; }
  }
}
print("BP\t%(i)d\tPLACED\tindexed=" + indexed + "\tbbox=" + minx + "," + miny + ".." + maxx + "," + maxy
      + "\tbuildings=" + Packages.mindustry.gen.Groups.build.size());
})();"""

# Measurement instrumentation: only sinks are rewritten; topology is untouched.
BP_SINK_JS = r"""(function(){
var W = Vars.world, T = Packages.mindustry.game.Team.sharded;
var GB = Packages.mindustry.gen.Groups.build, arr = [];
for(var k = 0; k < GB.size(); k++) arr.push(GB.index(k));
var swapped = 0, names = [];
for(var k = 0; k < arr.length; k++){
  var b = arr[k];
  var nm = b.block.name, to = null;
  if(nm == "item-void") to = "container";
  else if(nm == "liquid-void") to = "liquid-container";
  if(to != null){
    var t = W.tile(b.tileX(), b.tileY());
    t.setBlock(Vars.content.block(to), T, 0);
    Vars.indexer.addIndex(t);
    swapped++; names.push(nm + "->" + to);
  }
}
print("BP\t%(i)d\tSINKS\t" + swapped + "\t" + names.join(","));
})();"""

# Whole-world snapshot (one blueprint per world => no region filtering needed).
BP_SNAP_JS = r"""(function(){
var GB = Packages.mindustry.gen.Groups.build;
var built = 0, items = {}, sinkItems = {}, liquids = {}, counts = {}, graphs = {};
var effLow = 0, effN = 0, effSum = 0, progSum = 0, coreAmt = 0, cores = [];
for(var k = 0; k < GB.size(); k++){
  var b = GB.index(k);
  built++;
  var nm = b.block.name;
  counts[nm] = (counts[nm] || 0) + 1;
  if(nm.indexOf("core") == 0){ cores.push(nm + "@" + b.tileX() + "," + b.tileY()); if(b.items != null) coreAmt += b.items.total(); }
  if(b.items != null){
    var its = Vars.content.items();
    for(var j = 0; j < its.size; j++){
      var item = its.get(j), amt = b.items.get(item);
      if(amt != 0){ items[item.name] = (items[item.name] || 0) + amt;
        if(nm == "container") sinkItems[item.name] = (sinkItems[item.name] || 0) + amt; }
    }
  }
  if(b.liquids != null){
    var lqs = Vars.content.liquids();
    for(var j = 0; j < lqs.size; j++){
      var lq = lqs.get(j), amt = b.liquids.get(lq);
      if(amt > 0.0001){ liquids[lq.name] = (liquids[lq.name] || 0) + amt;
        if(nm == "liquid-container") sinkItems["L:" + lq.name] = (sinkItems["L:" + lq.name] || 0) + amt; }
    }
  }
  if(b.block.hasPower){
    effN++; effSum += b.efficiency; if(b.efficiency < 0.05) effLow++;
    progSum += b.progress;
    if(b.power != null && b.power.graph != null){
      var g = b.power.graph, id = g.getID();
      if(graphs[id] == null){
        graphs[id] = "prod=" + Math.round(g.getPowerProduced()*100)/100
          + " need=" + Math.round(g.getPowerNeeded()*100)/100
          + " sat=" + Math.round(g.getSatisfaction()*100)/100
          + " stored=" + Math.round(g.getBatteryStored());
      }
    }
  }
}
var gs = [];
for(var k in graphs) gs.push(k + ":" + graphs[k]);
print("SNAP\t%(tag)s\t" + Math.round(Vars.state.tick*100)/100 + "\tbuilt=" + built
  + "\tcore=" + cores.join("|") + "\tcoreAmt=" + coreAmt
  + "\teffLow=" + effLow + "/" + effN + "\teffAvg=" + (effN == 0 ? 0 : Math.round(effSum/effN*100)/100)
  + "\tprogSum=" + Math.round(progSum*100)/100
  + "\titems=" + Object.keys(items).map(function(k){ return k + "=" + Math.round(items[k]*100)/100; }).sort().join(",")
  + "\tsink=" + Object.keys(sinkItems).map(function(k){ return k + "=" + Math.round(sinkItems[k]*100)/100; }).sort().join(",")
  + "\tliquids=" + Object.keys(liquids).map(function(k){ return k + "=" + Math.round(liquids[k]*100)/100; }).sort().join(",")
  + "\tgraphs=" + gs.join(";")
  + "\tcounts=" + Object.keys(counts).sort().map(function(k){ return k + ":" + counts[k]; }).join(","));
})();"""



# Is a 2x2 block's origin the tile we passed, or (x-1,y-1)?
PLACE_ORIGIN_JS = r"""(function(){
var W = Vars.world, T = Packages.mindustry.game.Team.sharded;
var air = Vars.content.block("air");
for(var x = 0; x < 20; x++){ for(var y = 0; y < 20; y++){ if(W.tile(x,y).block().name != "air"){ W.tile(x,y).setBlock(air, T); } } }
W.tile(3,3).setBlock(Vars.content.block("graphite-press"), T);   /* 2x2 */
var b = W.build(3,3);
print("ORIGIN\t" + (b == null ? "null-build" : b.tileX() + "," + b.tileY() + " centerPx=" + b.x + "," + b.y));
for(var x = 1; x <= 6; x++){ for(var y = 1; y <= 6; y++){
  var t = W.tile(x,y);
  print("CELL\t" + x + "\t" + y + "\t" + t.block().name + "\t" + (t.build ? "B" : "-") + "\t" + (t.isCenter ? "" : ""));
} }
})();"""


# ============ supplement A: does placement auto-link power nodes? =============
# Schematics.place() = setBlock + build.configureAny(config) and does NOT call
# Building.placed(); PowerNodeBuild.placed() is where the auto-links are made.
# Rig: power-source -(4 tiles, <= laserRange 6)-> node -(4)-> node -> illuminator
PWR_RIG_JS = r"""(function(){
var W = Vars.world, T = Packages.mindustry.game.Team.sharded;
function put(x,y,name){
  var b = Vars.content.block(name);
  if(b == null){ print("PWR\tMISSING\t" + name); return null; }
  var t = W.tile(x,y);
  t.setBlock(b, T, 0);
  Vars.indexer.addIndex(t);
  var bl = W.build(x,y);
  print("PWR\tPUT\t" + name + "@" + x + "," + y + "\tbuild=" + (bl != null) + "\tsize=" + b.size);
  return bl;
}
put(20,20,"power-source");
put(24,20,"power-node");
put(28,20,"power-node");
put(32,20,"illuminator");
print("PWR\tBUILT\tgroups=" + Packages.mindustry.gen.Groups.build.size());
})();"""

PWR_READ_JS = r"""(function(){
var W = Vars.world, out = [];
function num(v){ return (typeof v == "number") ? (Math.round(v * 1000) / 1000) : String(v); }
function L(a){ if(a == null) return -1; try { return a.size; } catch(e){ } try { return a.length; } catch(e2){ } return -2; }
var pts = [["src",20,20],["n1",24,20],["n2",28,20],["ill",32,20]];
for(var i = 0; i < pts.length; i++){
  var b = W.build(pts[i][1], pts[i][2]);
  if(b == null){ out.push(pts[i][0] + ":null"); continue; }
  var p = b.power, g = (p == null ? null : p.graph);
  var parts = [pts[i][0] + ":links=" + (p == null ? "nopower" : L(p.links))
               + ",status=" + (p == null ? "-" : num(p.status))];
  if(g == null){ parts.push("graph=none"); }
  else {
    parts.push("gid=" + java.lang.System.identityHashCode(g) + ",gn=" + L(g.all));
    try {
      var fs = g.getClass().getDeclaredFields();
      for(var k = 0; k < fs.length; k++){
        var nm = fs[k].getName(), vv = null;
        try { vv = g[nm]; } catch(e){ continue; }
        if(typeof vv == "number"){ parts.push(nm + "=" + num(vv)); }
        else if(vv != null && String(vv).length < 10 && String(vv).indexOf("@") < 0){ parts.push(nm + "=" + vv); }
      }
    } catch(e){ parts.push("fields_err=" + e); }
  }
  out.push(parts.join(","));
}
print("PWR\t" + Vars.state.tick + "\t" + out.join("\t"));
})();"""

# explicit config: give the node its links by hand (the "generator must emit
# array config" hypothesis), then see whether that is what makes the graph work.
PWR_LINK_JS = r"""(function(){
var W = Vars.world;
var n1 = W.build(24,20), n2 = W.build(28,20), src = W.build(20,20), ill = W.build(32,20);
function trySet(b, name){
  if(b == null){ print("PWRCFG\t" + name + "\tNULL"); return; }
  try {
    b.configureAny(java.util.Arrays.asList([ill]));   // worst case: garbage config
    print("PWRCFG\t" + name + "\tconfigureAny(list) ok");
  } catch(e){ print("PWRCFG\t" + name + "\tconfigureAny FAILED\t" + e); }
}
trySet(n1, "node1");
try { print("PWRCFG\tnode1\tlinks_after=" + (n1.power.links == null ? "null" : n1.power.links.size)); } catch(e){ print("PWRCFG\tnode1\t" + e); }
})();"""

# ============ supplement B: where does the product actually go? ==============
# rig1: item-source(coal) -> graphite-press -> container   (pure adjacency, no belts)
# rig2: item-source(coal) -> graphite-press -> core-shard  (team item pool)
YIELD_RIG_JS = r"""(function(){
var W = Vars.world, T = Packages.mindustry.game.Team.sharded;
function put(x,y,name,rot,cfg){
  var b = Vars.content.block(name);
  if(b == null){ print("Y\tMISSING\t" + name); return null; }
  var t = W.tile(x,y);
  t.setBlock(b, T, rot == null ? 0 : rot);
  Vars.indexer.addIndex(t);
  var bl = W.build(x,y);
  if(cfg != null && bl != null){ try { bl.configureAny(cfg); } catch(e){ print("Y\tCFG_WARN\t" + name + "\t" + e); } }
  print("Y\tPUT\t" + name + "@" + x + "," + y + "\tbuild=" + (bl != null)
        + "\tsize=" + b.size + "\trot=" + (rot == null ? 0 : rot)
        + "\titemCap=" + b.itemCapacity);
  return bl;
}
var coal = Vars.content.item("coal");
put(20,20,"item-source",0,coal);      /* rig1 source */
put(21,20,"graphite-press",0,null);   /* 2x2 at 21..22,20..21 */
put(23,20,"container",0,null);
put(30,20,"item-source",0,coal);      /* rig2 source */
put(31,20,"graphite-press",0,null);   /* 2x2 at 31..32,20..21 */
put(33,20,"vault",0,null);
var dbg = [];
for(var x = 29; x <= 36; x++){ for(var y = 19; y <= 23; y++){ var tt = W.tile(x,y); if(tt.block().name != "air"){ dbg.push(x + "," + y + "=" + tt.block().name); } } }
print("Y\tTILEDUMP\t" + dbg.join(" "));
print("Y\tBUILT\tgroups=" + Packages.mindustry.gen.Groups.build.size());
})();"""

YIELD_READ_JS = r"""(function(){
var W = Vars.world, T = Packages.mindustry.game.Team.sharded;
var names = ["coal","graphite","sand","lead","metaglass","silicon","copper","titanium","pyratite"];
function holds(b){
  if(b == null) return "null";
  var m = b.items; if(m == null) return "noitems";
  var out = [];
  for(var i = 0; i < names.length; i++){
    var it = Vars.content.item(names[i]); if(it == null) continue;
    var v = m.get(it); if(v > 0) out.push(names[i] + "=" + v);
  }
  return out.length == 0 ? "0" : out.join("+");
}
function prog(b){ if(b == null) return "-"; return Math.round(b.progress * 10000) / 10000; }
function tot(b){ if(b == null) return -1; try { return b.items.total(); } catch(e){ return -2; } }
var pool = "?";
try { var td = Vars.state.teams.get(T); pool = (td == null ? "null" : tot(td)); } catch(e){ pool = "ERR"; }
print("Y\t" + Vars.state.tick
      + "\tc1=" + holds(W.build(23,20)) + ",c1tot=" + tot(W.build(23,20))
      + "\tp1=" + holds(W.build(21,20)) + ",p1prog=" + prog(W.build(21,20))
      + "\tp2=" + holds(W.build(31,20)) + ",p2prog=" + prog(W.build(31,20))
      + "\tcore8=" + holds(W.build(8,8))
      + "\tcore33=" + holds(W.build(33,20))
      + "\tpool=" + pool
      + "\tgroups=" + Packages.mindustry.gen.Groups.build.size());
})();"""

# is "team pool" even a thing we can read? dump the TeamData surface.
YIELD_TEAM_JS = r"""(function(){
var T = Packages.mindustry.game.Team.sharded;
function C(n){ try { return java.lang.Class.forName(n); } catch(e){ return null; } }
var out = [];
try {
  var td = Vars.state.teams.get(T);
  var c = td.getClass();
  var fs = c.getDeclaredFields();
  for(var i = 0; i < fs.length; i++){ out.push(fs[i].getName() + ":" + fs[i].getType().getSimpleName()); }
  print("TEAM\t" + c.getName() + "\t" + out.sort().join(","));
} catch(e){ print("TEAM\tERR\t" + e); }
})();"""


# do a REAL corpus blueprint's stored link configs materialise as power links?
BP_PWR_READ_JS = r"""(function(){
var W = Vars.world, out = [];
function L(a){ if(a == null) return -1; try { return a.size; } catch(e){ } try { return a.length; } catch(e2){ } return -2; }
for(var x = 0; x < W.width(); x++){
  for(var y = 0; y < W.height(); y++){
    var b = W.tile(x,y).build;
    if(b == null || b.power == null) continue;
    if(b.tileX() != x || b.tileY() != y) continue;
    var g = b.power.graph;
    out.push(b.block.name + "@" + x + "," + y + ":links=" + L(b.power.links)
             + ",gid=" + (g == null ? "none" : java.lang.System.identityHashCode(g))
             + ",gn=" + (g == null ? -1 : L(g.all))
             + ",sat=" + (g == null ? "-" : Math.round(g.satisfaction * 1000) / 1000)
             + ",status=" + Math.round(b.power.status * 1000) / 1000);
  }
}
print("BPLINK\t" + Vars.state.tick + "\t" + out.join("\t"));
})();"""


# ---------------------------------------------------------------------- helpers
def load_schematic_b64(path: str) -> str:
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode("ascii")


def parse_msch(path: str):
    import msch
    return msch.parse_file(path)


SCHEM_READ_JS = r"""(function(){
var sch = Packages.mindustry.game.Schematics.read("%(b64)s");
print("SCH\t" + sch.width + "\t" + sch.height + "\t" + sch.tiles.size + "\ttags=" + sch.tags.size());
for(var i = 0; i < sch.tiles.size; i++){
  var st = sch.tiles.get(i);
  print("ST\t" + st.x + "\t" + st.y + "\t" + st.block.name + "\t" + st.rotation + "\t"
        + (st.config == null ? "null" : String(st.config)) + "\t" + (st.config == null ? "-" : st.config.getClass().getSimpleName()));
}
})();"""


TICK_READ_JS = r"""(function(){ print("TICKNOW\t" + Vars.state.tick + "\t" + Vars.state.isPlaying()); })();"""


def _read_tick(srv) -> float:
    for ln in srv.js(TICK_READ_JS):
        if ln.startswith("TICKNOW"):
            return float(ln.split("\t")[1])
    return 0.0


def _block_counts(sch) -> dict:
    counts: dict = {}
    for t in sch.tiles:
        name = getattr(t, "block", None)
        counts[name] = counts.get(name, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: -kv[1]))


def _kv_list(text: str) -> dict:
    out = {}
    for part in text.split(","):
        if "=" in part:
            k, v = part.split("=", 1)
            try:
                out[k] = float(v)
            except ValueError:
                out[k] = v
    return out


def _parse_snap(line: str) -> dict:
    f = line.split("\t")
    d = {"tag": f[1], "tick": float(f[2]), "items": {}, "sink": {}, "liquids": {}}
    for part in f[3:]:
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        if k in ("items", "sink", "liquids"):
            d[k] = _kv_list(v)
        else:
            d[k] = v
    return d


def _snap_tick(snaps: dict) -> float:
    for v in snaps.values():
        if v:
            return _parse_snap(v)["tick"]
    return 0.0


def _diff(after: dict, before: dict) -> dict:
    out = {}
    for k in set(after) | set(before):
        d = after.get(k, 0) - before.get(k, 0)
        if abs(d) > 1e-6:
            out[k] = round(d, 3)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="all",
                    choices=["introspect", "clock", "place", "realtime", "power", "blueprint", "dump",
                             "pwrl", "yield", "bpwr", "all"])
    ap.add_argument("--warmup", type=float, default=13.0,
                    help="seconds to wait after Server loaded before touching the world"
                    "(the server loads its own map ~12s in)")
    ap.add_argument("--jar", default=JAR)
    ap.add_argument("--world", type=int, default=128)
    ap.add_argument("--msch", nargs="+", default=[os.path.join(ROOT, "logic-corpus", "pixecoz-SchematicsPack",
                                                              "msch", "metaglass-2.msch")])
    ap.add_argument("--ticks", type=int, default=600)
    ap.add_argument("--instrument", type=int, default=1,
                    help="1 = rewrite void sinks into containers so output can be counted")
    ap.add_argument("--json", default=os.path.join(OUT, "engine_probe.json"))
    ap.add_argument("--log", default=os.path.join(OUT, "engine_probe.log"))
    args = ap.parse_args(argv)

    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    srv = None
    report: dict = {"mode": args.mode, "jar": args.jar, "world": args.world}
    log: list[str] = []

    def emit(tag: str, *parts):
        line = "\t".join(str(p) for p in (tag,) + parts)
        log.append(line)
        print(line, flush=True)

    try:
        srv = Server(args.jar, JAVA, args.world)
        emit("TIMING", "java_start_to_Server_loaded_s", round(srv.t_loaded - srv.t_start, 2))
        emit("TIMING", "loadGenerator_to_world_ready_s", round(srv.t_world - srv.t_loaded, 2))
        report["timing"] = {"start_s": round(srv.t_loaded - srv.t_start, 2),
                            "world_s": round(srv.t_world - srv.t_loaded, 2)}

        if args.mode in ("introspect", "all"):
            for ln in srv.js(INTROSPECT_JS):
                emit("INTRO", ln)

        if args.mode in ("clock", "all"):
            t = time.time()
            for ln in srv.js(CLOCK_JS):
                emit("CLOCK", ln)
            time.sleep(2.0)
            for ln in srv.js(CLOCK_JS):
                emit("CLOCK+2s", ln)
            for ln in srv.js(CLOCK_PLAYING_JS):
                emit("CLOCK", ln)
            time.sleep(2.0)
            for ln in srv.js(CLOCK_JS):
                emit("CLOCK+2s_after_set_playing", ln)
            emit("TIMING", "clock_probe_s", round(time.time() - t, 2))

        if args.mode in ("realtime", "power", "all"):
            for ln in srv.js(SIG_JS):
                emit("SIG", ln)
            # make the server's own 60 Hz loop run the world (no players needed)
            srv.js(CLOCK_PLAYING_JS)
            t = time.time()
            for ln in srv.js(POWER_PLACE_JS):
                emit("POWER", ln)
            time.sleep(2.0)
            for ln in srv.js(POWER_READ_JS):
                emit("POWER+2s", ln)
            for ln in srv.js(PROD_PLACE_JS):
                emit("PROD", ln)
            time.sleep(2.0)
            for ln in srv.js(PROD_READ_JS):
                emit("PROD+2s", ln)
            emit("TIMING", "realtime_probe_s", round(time.time() - t, 2))
            report["realtime"] = {"log_tail": log[-8:]}

        if args.mode in ("place", "all"):
            for ln in srv.js(PLACE_SEMANTICS_JS):
                emit("PLACE", ln)
            for ln in srv.js(PLACE_ORIGIN_JS):
                emit("ORIGIN", ln)
        if args.mode == "pwrl":
            # does placement produce working power links without an array config?
            t = time.time()
            for ln in srv.js(BP_PREP_JS % {"n": args.world}):
                emit("PREP", ln)
            for ln in srv.js(PWR_RIG_JS):
                emit("JRIG", ln)
            for ln in srv.js(PWR_READ_JS):
                emit("JR0", ln)
            srv.js(CLOCK_PLAYING_JS)
            time.sleep(1.0)
            for ln in srv.js(PWR_READ_JS):
                emit("JRA1s", ln)
            time.sleep(max(args.ticks / 60.0 - 1.0, 0.5))
            for ln in srv.js(PWR_READ_JS):
                emit("JREND", ln)
            for ln in srv.js(PWR_LINK_JS):
                emit("JRLINK", ln)
            for ln in srv.js(PWR_READ_JS):
                emit("JRAFLINK", ln)
            emit("TIMING", "pwrl_s", round(time.time() - t, 2))
            report["powerlink"] = {"log_tail": log[-14:]}

        if args.mode == "yield":
            # where does the product actually land, and can we count it?
            t = time.time()
            for ln in srv.js(BP_PREP_JS % {"n": args.world}):
                emit("PREP", ln)
            for ln in srv.js(YIELD_RIG_JS):
                emit("JRIG", ln)
            for ln in srv.js(YIELD_READ_JS):
                emit("JR0", ln)
            for ln in srv.js(YIELD_TEAM_JS):
                emit("JTEAM", ln)
            srv.js(CLOCK_PLAYING_JS)
            tick0 = _read_tick(srv)
            cur, samples, sample_ticks = tick0, [], []
            while cur - tick0 < args.ticks:
                time.sleep(0.25)
                cur = _read_tick(srv)
                if cur < tick0:                      # world replaced under us
                    emit("WIPE", "yield rig: world swapped mid-run")
                    break
                for ln in srv.js(YIELD_READ_JS):
                    emit("JRS", ln)
                    samples.append(ln)
                    sample_ticks.append(cur)
            # progress-wrap counting (path 3): a wrap 1 -> 0 means one finished craft
            def _prog(ln, key):
                m = re.search(key + r"=(-?[0-9.]+)", ln)
                return float(m.group(1)) if m else None
            wraps = {k: 0 for k in ("p1prog", "p2prog")}
            prev = {}
            for ln in samples:
                for k in wraps:
                    v = _prog(ln, k)
                    if v is None:
                        continue
                    if k in prev and v < prev[k] - 0.5:
                        wraps[k] += 1
                    prev[k] = v
            emit("JWRAP", "p1_progress_wraps", wraps["p1prog"], "p2_progress_wraps", wraps["p2prog"],
                 "samples", len(samples))
            for ln in srv.js(YIELD_READ_JS):
                emit("JREND", ln)
            emit("TIMING", "yield_s", round(time.time() - t, 2))
            report["yield"] = {"wraps": wraps, "samples": len(samples),
                               "ticks": round(cur - tick0, 2), "log_tail": log[-4:]}

        if args.mode == "bpwr":
            # real blueprint -> do its stored power-node link configs take effect?
            path = args.msch[0] if isinstance(args.msch, list) else args.msch
            path = path if os.path.isabs(path) else os.path.join(ROOT, path)
            for ln in srv.js(BP_PREP_JS % {"n": args.world}):
                emit("PREP", ln)
            for ln in srv.js(BP_PLACE_JS % {"b64": load_schematic_b64(path), "i": 0, "px": 40, "py": 40}):
                emit("BP", ln)
            for ln in srv.js(BP_PWR_READ_JS):
                emit("BPLINK0", ln)
            srv.js(CLOCK_PLAYING_JS)
            time.sleep(2.0)
            for ln in srv.js(BP_PWR_READ_JS):
                emit("BPLINK2s", ln)
            report["bpwr"] = {"log_tail": log[-4:]}

        if args.mode in ("blueprint", "dump"):
            paths = args.msch if isinstance(args.msch, list) else [args.msch]
            paths = [p if os.path.isabs(p) else os.path.join(ROOT, p) for p in paths]
            srv.js(CLOCK_PLAYING_JS)          # the server's own loop drives the world
            results = []
            for i, path in enumerate(paths):
                t_one = time.time()
                sch = parse_msch(path)
                for ln in srv.js(BP_PREP_JS % {"n": args.world}):
                    emit("PREP", ln)
                t_prep = time.time()
                for ln in srv.js(BP_PLACE_JS % {"b64": load_schematic_b64(path), "i": i,
                                                "px": 40, "py": 40}):
                    emit("BP", ln)
                if args.instrument:
                    for ln in srv.js(BP_SINK_JS % {"i": i}):
                        emit("BP", ln)
                t_place = time.time()
                if args.mode == "dump":
                    for ln in srv.js(DUMP_JS):
                        emit("DUMP0", ln)
                # rig is built while paused -> now let the real 60 Hz loop run it
                srv.js(CLOCK_PLAYING_JS)
                snap_lines = {}
                for ln in srv.js(BP_SNAP_JS % {"tag": "t0_%d" % i}):
                    emit("SNAP", ln)
                    snap_lines["t0"] = ln
                a = _parse_snap(snap_lines["t0"])
                tick0 = a["tick"]
                t_run = time.time()
                wiped = False
                cur = tick0
                while cur - tick0 < args.ticks:
                    time.sleep(0.3)
                    cur = _read_tick(srv)
                    if cur < tick0:                       # world reloaded under us
                        wiped = True
                        break
                run_wall = time.time() - t_run
                if wiped:
                    emit("WIPE", "msch=%s worst-case: server replaced the world mid-run" % path)
                if args.mode == "dump" and not wiped:
                    for ln in srv.js(DUMP_JS):
                        emit("DUMPN", ln)
                for ln in ([] if wiped else srv.js(BP_SNAP_JS % {"tag": "tN_%d" % i})):
                    emit("SNAP", ln)
                    snap_lines["tN"] = ln
                b = _parse_snap(snap_lines["tN"] if not wiped else snap_lines["t0"])
                ticks = b["tick"] - tick0
                secs = max(ticks / 60.0, 1e-6)
                produced = _diff(b["sink"], a["sink"])
                res = {
                    "msch": os.path.relpath(path, ROOT).replace("\\", "/"),
                    "offline": {"w": sch.width, "h": sch.height, "tiles": len(sch.tiles),
                                "blocks": _block_counts(sch)},
                    "engine": {"buildings": b["built"], "core": b["core"],
                               "effLow": b["effLow"], "effAvg": b["effAvg"],
                               "graphs": b["graphs"], "counts": b["counts"]},
                    "produced": produced,
                    "produced_per_s": {k: round(v / secs, 3) for k, v in produced.items()},
                    "core_delta": _diff(b["items"], a["items"]),
                    "liquid_sink": b["sink"],
                    "ticks": round(ticks, 1),
                    "wall_s": round(run_wall, 2),
                    "ms_per_tick": round(run_wall * 1000 / max(ticks, 1e-6), 2),
                    "prep_s": round(t_prep - t_one, 2),
                    "place_s": round(t_place - t_prep, 2),
                    "world_wiped": wiped,
                }
                results.append(res)
                emit("RESULT", res["msch"], "tiles", res["offline"]["tiles"],
                     "->buildings", res["engine"]["buildings"], "produced", produced,
                     "per_s", res["produced_per_s"], "ticks", res["ticks"],
                     "wall_s", res["wall_s"], "eff", res["engine"]["effAvg"],
                     "effLow", res["engine"]["effLow"], "graphs", res["engine"]["graphs"])
            report["blueprints"] = results
            report["timing_total_s"] = round(time.time() - t0, 2)


        report["log"] = log
        with open(args.log, "w", encoding="utf-8") as fh:
            fh.write("\n".join(log) + "\n")
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=2)
        emit("TOTAL", "wall_s", round(time.time() - t0, 2))
        return 0
    except Exception as exc:  # noqa: BLE001 - spike: report, never hang
        emit("FAIL", type(exc).__name__, str(exc)[:1500])
        with open(args.log, "w", encoding="utf-8") as fh:
            fh.write("\n".join(log) + "\n")
        return 1
    finally:
        if srv is not None:
            srv.close()
        # no stray JVMs from this script
        try:
            out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq java.exe", "/FO", "CSV"],
                                 capture_output=True, text=True, timeout=30)
            rest = [ln for ln in (out.stdout or "").splitlines() if "java.exe" in ln.lower()]
            emit("JAVA_PROCS_AFTER", len(rest))
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
