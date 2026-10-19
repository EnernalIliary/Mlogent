"""mlogsim -- run real Mindustry mlog on the real LExecutor, headless.

No JDK, no compilation, no mods: starts the official server jar and uses its
console `js` command (Rhino) to place blocks, load code, step
`LExecutor.runOnce()` manually and read back every variable plus the print
buffer.

    python tools/mlogsim.py out/prog.mlog --steps 50
    python tools/mlogsim.py blueprints/x.msch --steps 200
    python tools/mlogsim.py save.msch --ticks 60 --units flare:2

By default the world is a blank 64x64 (`--world N` to resize, 0 or `--host` to
host a random map). Blueprints are at most 64x64, so the default fits any
schematic. No host means no 6567 port and no random-map load: ~1s per run
faster; making the world smaller than 64 does not speed anything up, because
instruction execution does not touch the map and `tile` lookup is O(1).
`--host` is only needed for programs that read real terrain or `@mapw`.

For a schematic every tile is placed, every logic block is compiled with its
named links, and the logic blocks are stepped in schematic order (so a
two-processor cross-read behaves like the save it came from).

Default runtime is the newest local pair, overridable with env vars:
    MLOGSIM_JAR   (default: out/_server159.jar, then out/_server146.jar)
    MLOGSIM_JAVA  (default: out/jre21/.../java.exe, then the Steam jre)

v159.3 needs a Java 21+ runtime (the Steam jlink image lacks java.logging).
v146 is kept for comparison only: it lacks `LogicBlock.readable`, so
cross-processor `read` by name always yields null there.

Note: micro-processor runs 2 instructions/tick, logic-processor 8,
hyper-processor 25. `--steps` counts *instructions*, not ticks.
"""
from __future__ import annotations

import argparse
import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "mindustry-blueprint", "tools")
STEAM_JAVA = r"E:\Program Files (x86)\Steam\steamapps\common\Mindustry\jre\bin\java.exe"
V159_JAR = os.path.join(ROOT, "out", "_server159.jar")
V159_JAVA = os.path.join(ROOT, "out", "jre21", "jdk-21.0.5+11-jre", "bin", "java.exe")
V146_JAR = os.path.join(ROOT, "out", "_server146.jar")


def _default_jar() -> str:
    return os.environ.get("MLOGSIM_JAR") or (V159_JAR if os.path.exists(V159_JAR) else V146_JAR)


def _default_java() -> str:
    env = os.environ.get("MLOGSIM_JAVA")
    if env:
        return env
    if os.path.exists(V159_JAVA):
        return V159_JAVA
    return STEAM_JAVA


class SimError(RuntimeError):
    pass


class Server:
    def __init__(self, java: str, jar: str, world_size: int | None = 64):
        # writes must stay inside the workspace: Java child processes are not
        # allowed to write under %TEMP% (sandbox denies with "access denied")
        base = os.path.join(ROOT, "out", "_sim")
        os.makedirs(base, exist_ok=True)
        self.workdir = tempfile.mkdtemp(prefix="run-", dir=base)
        os.makedirs(os.path.join(self.workdir, "config", "logs"), exist_ok=True)
        self.proc = subprocess.Popen(
            [java, "-Dstdout.encoding=UTF-8", "-Dstderr.encoding=UTF-8", "-jar", jar],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=self.workdir,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        self.lines: queue.Queue = queue.Queue()
        self.buffer: list[str] = []
        self.all: list[str] = []
        self.exit_code = None
        threading.Thread(target=self._pump, daemon=True).start()
        try:
            self.wait_for("Server loaded.", 60)
            if world_size:
                # no host: Vars.init already built state/world, loadGenerator makes
                # a blank map. Saves the ~0.5s random-map host and all port binding.
                self.world_size = world_size
                self.base = (0, 0)
                self.js(LOAD_JS % {"n": world_size})
            else:
                self.world_size = None
                self.base = (80, 80)
                self.send("host")
                self.wait_for("Opened a server", 120)
                self.send("pause on")
                time.sleep(0.4)
        except Exception:
            self.close()
            raise

    def _pump(self):
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self.lines.put(line.rstrip("\r\n"))
        self.exit_code = self.proc.wait()
        self.lines.put(None)

    def send(self, cmd: str):
        assert self.proc.stdin is not None
        self.proc.stdin.write(cmd + "\n")
        self.proc.stdin.flush()

    def wait_for(self, needle: str, timeout: float = 60.0) -> list[str]:
        deadline = time.time() + timeout
        out: list[str] = []
        while time.time() < deadline:
            try:
                line = self.lines.get(timeout=0.2)
            except queue.Empty:
                continue
            if line is None:
                raise SimError(f"server exited (code={self.exit_code}):\n" + "\n".join(self.all[-20:]))
            self.buffer.append(line)
            self.all.append(line)
            out.append(line)
            if needle in line:
                return out
        raise SimError(f"timeout waiting for {needle!r}; tail:\n" + "\n".join(self.all[-20:]))

    def js(self, script: str, timeout: float = 60.0) -> list[str]:
        """Run one `js` command; return the lines it printed."""
        self.buffer.clear()
        # the console reads one line per command: multi-line scripts would be
        # parsed as separate console commands
        self.send("js " + " ".join(script.splitlines()))
        lines = self.wait_for("undefined", timeout)
        out = [ln.split("[none/base.js]:", 1)[1].strip() for ln in lines if "[none/base.js]:" in ln]
        err = [ln for ln in lines if "Exception" in ln or "Error:" in ln]
        if err:
            raise SimError("\n".join(err))
        return out

    def close(self):
        try:
            self.send("exit")
            self.proc.wait(timeout=15)
        except Exception:
            self.proc.kill()


LOAD_JS = r'''
Vars.world.loadGenerator(%(n)d,%(n)d,function(tiles){
    tiles.fill();
    var floor = Vars.content.block('stone').asFloor();
    for(var x = 0; x < %(n)d; x++){
        for(var y = 0; y < %(n)d; y++){ tiles.get(x,y).setFloor(floor); }
    }
});
print("WORLD\t" + Vars.world.width() + "x" + Vars.world.height());
'''


def place_js(x: int, y: int) -> str:
    return ("var T=Packages.mindustry.game.Team.sharded;"
            "Vars.world.tile(%d,%d).setBlock(Vars.content.block('air'), T);"
            "Vars.world.tile(%d,%d).setBlock(Vars.content.block('micro-processor'), T);"
            "print('PLACED');" % (x, y, x, y))

STEP_JS = r'''
var p = "%(path)s";
var s = Packages.java.nio.file.Files.readString(
    Packages.java.nio.file.Paths.get(p),
    Packages.java.nio.charset.StandardCharsets.UTF_8);
var b = Vars.world.build(%(x)d,%(y)d);
b.code = s;
b.updateCode(s);
/* updateTile() copies the team in; paused world never runs it */
b.executor.team = Packages.mindustry.game.Team.sharded;
/* a block placed via setBlock keeps efficiency 0 until updateEfficiency runs */
b.efficiency = 1;
%(loop)s
print("@@BEGIN");
var vs = b.executor.vars;
for(var i = 0; i < vs.length; i++){
    var v = vs[i], val;
    if(v.isobj){ val = String(v.objval); } else { val = "" + v.numval; }
    print("VAR\t" + v.name + "\t" + val);
}
print("COUNTER\t" + b.executor.counter.numval);
print("IPT\t" + b.executor.ipt.numval);
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

UNIT_JS = r'''
var spec = %(spec)s;            /* [[name, count], ...] */
var team = Packages.mindustry.game.Team.sharded;
Vars.state.rules.logicUnitControl = true;
var made = 0;
for(var s = 0; s < spec.length; s++){
    var name = spec[s][0], n = spec[s][1];
    var ut = null;
    for(var i = 0; i < Vars.content.units().size; i++){
        var t = Vars.content.units().get(i);
        if(t.name == name){ ut = t; break; }
    }
    if(ut == null){ print("NOUNIT\t" + name); continue; }
    for(var k = 0; k < n; k++){
        var wx = %(x)d * 8 + 16 + (k %% 5) * 12;
        var wy = %(y)d * 8 + 16 + ((k / 5) | 0) * 12;
        ut.spawn(team, wx, wy);
        made++;
    }
}
/* paused world never runs Teams.updateTeamStats, so ubind would see no units */
Vars.state.teams.updateTeamStats();
print("UNITS\t" + made);
'''


def _loop_js(obj: str, steps: int, ticks: bool) -> str:
    """Instruction mode steps the executor directly; tick mode drives updateTile.

    In tick mode Time.delta must be 1.0: edelta() = delta * timeScale feeds the
    accumulator (ipt per tick) and WaitI adds Time.delta/60 per execution, so
    1.0 is the value that makes 60 ticks equal one second.
    """
    if ticks:
        return "Time.delta = 1.0; for(var i = 0; i < %d; i++){ %s.updateTile(); }" % (steps, obj)
    return "for(var i = 0; i < %d; i++){ %s.executor.runOnce(); }" % (steps, obj)


def _scene_loop_js(steps: int, ticks: bool) -> str:
    """Same, but tick every processor together so cross-reads see one world.

    A scene has N processors, so the tick loop must nest: outer ticks, inner
    processors. Iterating each processor for `steps` ticks in isolation would
    let one processor run far ahead of the other.
    """
    if ticks:
        return ("Time.delta = 1.0; for(var t = 0; t < %d; t++){"
                " for(var j = 0; j < procs.length; j++){ procs[j].updateTile(); } }" % steps)
    return ("for(var i = 0; i < procs.length; i++){"
            " for(var k = 0; k < %d; k++){ procs[i].executor.runOnce(); } }" % steps)


def parse_results(lines: list[str]) -> list[dict]:
    """Turn @@BEGIN blocks into records."""
    recs: list[dict] = []
    cur = None
    for ln in lines:
        if ln.startswith("@@BEGIN"):
            cur = {"label": ln.split("\t", 1)[1] if "\t" in ln else "", "vars": {}, "counter": None,
                   "ipt": None, "accumulator": None, "text": "", "skipped": []}
            recs.append(cur)
        elif ln.startswith("@@END"):
            cur = None
        elif ln.startswith("SKIP\t") and recs:
            recs[-1]["skipped"].append(ln.split("\t", 1)[1])
        elif cur is not None:
            if ln.startswith("VAR\t"):
                _, k, v = ln.split("\t", 2)
                cur["vars"][k] = v
            elif ln.startswith("COUNTER\t"):
                cur["counter"] = float(ln.split("\t", 1)[1])
            elif ln.startswith("IPT\t"):
                cur["ipt"] = float(ln.split("\t", 1)[1])
            elif ln.startswith("ACC\t"):
                cur["accumulator"] = float(ln.split("\t", 1)[1])
            elif ln.startswith("TEXT\t"):
                cur["text"] = ln.split("\t", 1)[1].replace("\\n", "\n")
    return recs


def run_mlog(srv: Server, name: str, code: str, steps: int, ticks: bool = False) -> dict:
    # a fresh processor keeps textBuffer/vars from leaking between programs
    srv.js(place_js(*srv.base))
    fd, path = tempfile.mkstemp(suffix=".mlog", dir=srv.workdir, text=True)
    os.close(fd)
    try:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(code)
        js = STEP_JS % {"path": path.replace("\\", "/"), "x": srv.base[0], "y": srv.base[1],
                        "loop": _loop_js("b", steps, ticks)}
        recs = parse_results(srv.js(js))
        rec = recs[0] if recs else {"vars": {}, "counter": None, "text": ""}
        rec["name"] = name
        rec["steps"] = steps
        rec["mode"] = "tick" if ticks else "instruction"
        return rec
    finally:
        os.unlink(path)


def run_msch(srv: Server, name: str, path: str, steps: int, ticks: bool = False) -> list[dict]:
    sys.path.insert(0, TOOLS)
    import msch  # noqa: E402

    sch = msch.parse_file(path)
    minx = min(t.x for t in sch.tiles)
    miny = min(t.y for t in sch.tiles)
    w = max(t.x for t in sch.tiles) - minx + 1
    h = max(t.y for t in sch.tiles) - miny + 1
    if srv.world_size and (srv.base[0] + w > srv.world_size or srv.base[1] + h > srv.world_size):
        raise SimError("schematic is %dx%d, does not fit the %dx%d world (use --world %d or --host)"
                       % (w, h, srv.world_size, srv.world_size, max(w, h)))
    tiles = []
    for t in sch.tiles:
        x, y = srv.base[0] + (t.x - minx), srv.base[1] + (t.y - miny)
        entry = {"block": t.block, "x": x, "y": y, "logic": None, "links": []}
        if t.logic is not None:
            entry["logic"] = t.logic.code
            entry["links"] = [
                {"name": l.name, "x": srv.base[0] + (l.x - minx), "y": srv.base[1] + (l.y - miny)}
                for l in t.logic.links
            ]
        tiles.append(entry)
    js = SCENE_JS % {"tiles": json.dumps(tiles), "loop": _scene_loop_js(steps, ticks)}
    recs = parse_results(srv.js(js, timeout=180))
    for r in recs:
        r["name"] = name
        r["steps"] = steps
        r["mode"] = "tick" if ticks else "instruction"
    return recs


def main(argv=None):
    ap = argparse.ArgumentParser(description="run mlog on the real Mindustry LExecutor")
    ap.add_argument("files", nargs="+", help=".mlog files (or .msch schematics)")
    ap.add_argument("--steps", type=int, default=None, help="instructions to execute (default 200)")
    ap.add_argument("--ticks", type=int, default=None,
                    help="simulated ticks: drive updateTile() with Time.delta=1 (accumulator/ipt/wait)")
    ap.add_argument("--world", type=int, default=64, metavar="N",
                    help="blank NxN world loaded with loadGenerator (default 64, 0 = host a random map)")
    ap.add_argument("--host", action="store_true",
                    help="host a random map instead of the blank world (needed for terrain/@mapw)")
    ap.add_argument("--jar", default=_default_jar())
    ap.add_argument("--java", default=_default_java())
    ap.add_argument("--init-js", metavar="FILE|CODE", default=None,
                    help="JS run once after the world exists: set rules, seed blocks")
    ap.add_argument("--units", metavar="NAME[:N],...", default=None,
                    help="spawn units near the processor as team sharded, e.g. flare:3,poly:1")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    ticks = args.ticks is not None
    steps = args.ticks if ticks else (args.steps if args.steps is not None else 200)

    if not os.path.exists(args.jar):
        sys.exit(f"missing server jar: {args.jar}")

    world_size = None if args.host or args.world == 0 else args.world
    srv = Server(args.java, args.jar, world_size)
    results = []
    try:
        if args.init_js:
            if os.path.exists(args.init_js):
                with open(args.init_js, encoding="utf-8-sig") as fh:
                    init_src = fh.read()
            else:
                init_src = args.init_js
            srv.js(init_src)
        if args.units:
            spec = []
            for part in args.units.split(","):
                part = part.strip()
                if not part:
                    continue
                name, _, cnt = part.partition(":")
                spec.append([name.strip(), int(cnt) if cnt else 1])
            srv.js(UNIT_JS % {"spec": json.dumps(spec), "x": srv.base[0], "y": srv.base[1]})
        for f in args.files:
            if f.lower().endswith(".msch"):
                results.extend(run_msch(srv, os.path.basename(f), f, steps, ticks))
            else:
                # utf-8-sig: PowerShell's `Set-Content -Encoding utf8` prepends a BOM,
                # and the parser turns a BOM-prefixed first line into a noop
                with open(f, encoding="utf-8-sig") as fh:
                    code = fh.read()
                results.append(run_mlog(srv, os.path.basename(f), code, steps, ticks))
    except FileNotFoundError as e:
        sys.exit(f"missing input: {e.filename}")
    except SimError as e:
        sys.exit(f"sim failed: {e}")
    finally:
        try:
            with open(os.path.join(ROOT, "out", "_sim_server.log"), "w", encoding="utf-8") as fh:
                fh.write("\n".join(srv.all))
        except OSError:
            pass
        srv.close()

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            unit = "ticks" if r.get("mode") == "tick" else "steps"
            print(f"== {r['name']} @{r.get('label', '')} ({r['steps']} {unit}) ==")
            for k, v in r["vars"].items():
                print(f"  {k} = {v}")
            if r["text"]:
                print(f"  print: {r['text']}")
            print(f"  @counter = {r['counter']}  ipt = {r.get('ipt')}  acc = {r.get('accumulator')}")
            if r.get("skipped"):
                print(f"  skipped: {', '.join(r['skipped'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
