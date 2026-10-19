"""mlogsim -- run real Mindustry mlog on the real LExecutor, headless.

No JDK, no compilation, no mods: starts the official server jar and uses its
console `js` command (Rhino) to place blocks, load code, step
`LExecutor.runOnce()` manually and read back every variable plus the print
buffer.

    python tools/mlogsim.py out/prog.mlog --steps 50
    python tools/mlogsim.py blueprints/x.msch --steps 200

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


BASE = (80, 80)  # scene origin on the hosted map


class SimError(RuntimeError):
    pass


class Server:
    def __init__(self, java: str, jar: str):
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
        self.wait_for("Server loaded.", 60)
        # `pause` before a world exists is rejected; host first, then freeze
        self.send("host")
        self.wait_for("Opened a server", 120)
        self.send("pause on")
        time.sleep(0.4)

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


PLACE_JS = (
    "var T=Packages.mindustry.game.Team.sharded;"
    "Vars.world.tile(%d,%d).setBlock(Vars.content.block('air'), T);"
    "Vars.world.tile(%d,%d).setBlock(Vars.content.block('micro-processor'), T);"
    "print('PLACED');" % (BASE[0], BASE[1], BASE[0], BASE[1])
)

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
b.accumulator = -1000000;
for(var i = 0; i < %(steps)d; i++){ b.executor.runOnce(); }
print("@@BEGIN");
var vs = b.executor.vars;
for(var i = 0; i < vs.length; i++){
    var v = vs[i], val;
    if(v.isobj){ val = String(v.objval); } else { val = "" + v.numval; }
    print("VAR\t" + v.name + "\t" + val);
}
print("COUNTER\t" + b.executor.counter.numval);
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
    b.accumulator = -1000000;
    procs.push(b);
}
print("PROCS\t" + procs.length);
for(var i = 0; i < procs.length; i++){
    for(var k = 0; k < %(steps)d; k++){ procs[i].executor.runOnce(); }
}
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
    print("TEXT\t" + String(b.executor.textBuffer.toString()).replace(/\n/g, "\\n"));
    print("@@END");
}
'''


def parse_results(lines: list[str]) -> list[dict]:
    """Turn @@BEGIN blocks into records."""
    recs: list[dict] = []
    cur = None
    for ln in lines:
        if ln.startswith("@@BEGIN"):
            cur = {"label": ln.split("\t", 1)[1] if "\t" in ln else "", "vars": {}, "counter": None, "text": "", "skipped": []}
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
            elif ln.startswith("TEXT\t"):
                cur["text"] = ln.split("\t", 1)[1].replace("\\n", "\n")
    return recs


def run_mlog(srv: Server, name: str, code: str, steps: int) -> dict:
    # a fresh processor keeps textBuffer/vars from leaking between programs
    srv.js(PLACE_JS)
    fd, path = tempfile.mkstemp(suffix=".mlog", dir=srv.workdir, text=True)
    os.close(fd)
    try:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(code)
        js = STEP_JS % {"path": path.replace("\\", "/"), "x": BASE[0], "y": BASE[1], "steps": steps}
        recs = parse_results(srv.js(js))
        rec = recs[0] if recs else {"vars": {}, "counter": None, "text": ""}
        rec["name"] = name
        rec["steps"] = steps
        return rec
    finally:
        os.unlink(path)


def run_msch(srv: Server, name: str, path: str, steps: int) -> list[dict]:
    sys.path.insert(0, TOOLS)
    import msch  # noqa: E402

    sch = msch.parse_file(path)
    minx = min(t.x for t in sch.tiles)
    miny = min(t.y for t in sch.tiles)
    tiles = []
    for t in sch.tiles:
        x, y = BASE[0] + (t.x - minx), BASE[1] + (t.y - miny)
        entry = {"block": t.block, "x": x, "y": y, "logic": None, "links": []}
        if t.logic is not None:
            entry["logic"] = t.logic.code
            entry["links"] = [
                {"name": l.name, "x": BASE[0] + (l.x - minx), "y": BASE[1] + (l.y - miny)}
                for l in t.logic.links
            ]
        tiles.append(entry)
    js = SCENE_JS % {"tiles": json.dumps(tiles), "steps": steps}
    recs = parse_results(srv.js(js, timeout=120))
    for r in recs:
        r["name"] = name
        r["steps"] = steps
    return recs


def main(argv=None):
    ap = argparse.ArgumentParser(description="run mlog on the real Mindustry LExecutor")
    ap.add_argument("files", nargs="+", help=".mlog files (or .msch schematics)")
    ap.add_argument("--steps", type=int, default=200, help="instructions per program (default 200)")
    ap.add_argument("--jar", default=_default_jar())
    ap.add_argument("--java", default=_default_java())
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if not os.path.exists(args.jar):
        sys.exit(f"missing server jar: {args.jar}")

    srv = Server(args.java, args.jar)
    results = []
    try:
        for f in args.files:
            if f.lower().endswith(".msch"):
                results.extend(run_msch(srv, os.path.basename(f), f, args.steps))
            else:
                # utf-8-sig: PowerShell's `Set-Content -Encoding utf8` prepends a BOM,
                # and the parser turns a BOM-prefixed first line into a noop
                with open(f, encoding="utf-8-sig") as fh:
                    code = fh.read()
                results.append(run_mlog(srv, os.path.basename(f), code, args.steps))
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
            print(f"== {r['name']} @{r.get('label', '')} ({r['steps']} steps) ==")
            for k, v in r["vars"].items():
                print(f"  {k} = {v}")
            if r["text"]:
                print(f"  print: {r['text']}")
            print(f"  @counter = {r['counter']}")
            if r.get("skipped"):
                print(f"  skipped: {', '.join(r['skipped'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
