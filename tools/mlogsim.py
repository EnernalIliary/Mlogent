"""mlogsim -- run real Mindustry mlog on the real LExecutor, headless.

No JDK, no compilation, no mods: starts the official server jar and uses its
console `js` command (Rhino) to place blocks, load code, step
`LExecutor.runOnce()` manually and read back every variable plus the print
buffer.

    python tools/mlogsim.py out/prog.mlog --steps 50
    python tools/mlogsim.py blueprints/x.msch --steps 200
    python tools/mlogsim.py scene.msav --ticks 60 --units flare:2

By default the world is a blank 64x64 (`--world N` to resize, 0 or `--host` to
host a random map). Blueprints are at most 64x64, so the default fits any
schematic. No host means no 6567 port and no random-map load: ~1s per run
faster; making the world smaller than 64 does not speed anything up, because
instruction execution does not touch the map and `tile` lookup is O(1).
`--host` is only needed for programs that read real terrain or `@mapw`.

For a schematic every tile is placed, every logic block is compiled with its
named links, and the logic blocks are stepped in schematic order (so a
two-processor cross-read behaves like the save it came from).

World simulation (`--ticks` only; `--steps` stays pure logic stepping):

    --update all    (default for --ticks) every building is updated each tick,
                    so factories, conveyors, drills, power and turrets run
    --update none   logic only; buildings stay frozen

`--update all` snapshots Groups.build and skips processors (the step loop
drives those). `--power full` (default) or `--power none` pins power status
to 1.0 or 0.0. `--power grid` runs the original power graphs before buildings
and preserves the game's power status, including the charge in batteries.
The loop sets the game state to playing only while it drives the updates.

Units spawned with `--units` are driven by their controller in the same mode:
under `--update all` every unit whose controller is a `LogicAI` gets one real
`Unit.update()` per tick, so `ucontrol move/approach/stop/boost` actually moves
it, `within`/`@x`/`@y` see the result, and `@unit` stays the same object.
Units that are not logic-controlled are not updated by default (wild AI is not
simulated; `--unit-ai all` turns it on), and a unit whose 10s control timeout
expires simply stops -- it does not revert to its faction AI. This is "B
level": real executor, real unit update, real `LogicAI`, but no wave AI, combat
targeting or full terrain collision detail in the world. Passing here
does not replace a real game run.
`--update none` keeps units frozen where they spawned. `--unit-pos X,Y` spawns
them at a tile coordinate instead of two tiles off the processor, which makes
motion demos reproducible (e.g. start a unit exactly on its orbit).
Grid mode requires a local tick run with building updates. Use `--save`
to bring a real grid layout, node links and initial battery charge.

Scenes (`--save FILE`) load a real `.msav`: the map, teams, cores, buildings
and units come with it, so logic runs against the exact layout it will meet in
game. The processor is auto-placed on a free tile beside your core (`--base
X,Y` overrides) and the world size comes from the save, not `--world`. The
save's world clock is reset to 0 once, so `@tick`/`@time` start at 0 and runs
repeat; the absolute clock value inside a save is otherwise arbitrary.

Links (`--links auto`, default for a `.mlog`): a plain `.mlog` has no link
table, so `read cell1 0` normally compiles to a null constant. The simulator
finds names the program reads but never assigns and, when the name looks like
a link (`cell1`, `bank1`, `message1`, `dome1`), places the matching block on a
free tile next to the processor and wires it (10-tile link range, same team).
`--links off` restores the raw behaviour. A `.msch` keeps its own links.
`--unit-ai all` also updates units that no processor controls, i.e. the save's
own AI: turrets are buildings and already fire under `--update all`, while
this lets mobile defenders and attackers act. `CommandAI` units stay passive
unless the save gave them a command -- the stock server has no commander.

Weather (`--ticks` only) is the real state machine, not a stub: every tick each
`state.rules.weather` entry loses `Time.delta` from its cooldown, and an entry
whose cooldown expired (or that is `always`) creates its weather with a
duration/frequency randomized from a fixed seed, so a run repeats. Active
weathers fade/expire through `Groups.weather.update()`. `weathersense` and
`weatherset` are privileged: a program that uses them (or `setrule`, `message`,
`cutscene`, `spawn`, ...) is placed as a world processor automatically
(`--processor auto`), because a micro processor's parser silently replaces
those lines with invalid statements. `--weather NAME[:INTENSITY]` starts with
that weather already active (repeatable) instead of a clear sky.

Tick semantics: Mindustry adds `edelta()*ipt` to the accumulator *after* the
instruction loop, so the first update after placement executes nothing --
`--ticks N` therefore runs N-1 active ticks and `@tick` starts at 2. The print
buffer is capped by the game at `maxTextBuffer` = 400 chars; longer output is
truncated, not lost by the harness.

Preflight (default on; `--no-preflight` disables): the program must compile
(`executor.initialized()`), every `--units` entry must actually spawn, and at
tick 1 every spawned unit must still be alive. That last one matters: a unit
spawned on a solid tile is killed by its first `update()`, which otherwise
looks like "the unit never moved" only after the whole run has finished.
Failures abort with the cause instead of a silent wrong result.

Combat (`--ticks` only) mirrors `Logic.updateEntities()`: before the logic
step, `Groups.bullet.updatePhysics()` and `Groups.unit.updatePhysics()` run;
after it, `Groups.bullet.update()` and `.collide()`. A unit's `ucontrol target`
shots then really travel, hit buildings, and drain health. `--combat off`
leaves bullets frozen: useful to isolate aiming, but nothing takes damage.
Not a battle model: waves, enemy AI, death/despawn edge cases and block
destruction consequences are still the game's job.

Trace (`--ticks` only): `--trace FILE` writes one CSV row per tick per unit
whose controller is a `LogicAI` (a unit a processor took over):

    unit,tick,ux,uy,uhp,range,tx,ty,dist,cx,cy,chp,bullets,shots

`ux/uy` are tiles; `range` is `@range` (tiles); `tx/ty/dist` are the current
`ucontrol target` point (blank unless aim mode is target); `cx/cy/chp` are the
nearest enemy core (blank if none); `bullets` is `Groups.bullet.size()`;
`shots` sums each weapon mount's `totalShots`. Works with `--update none` too.

Assertions run on trace rows: `--assert EXPR` on every row (invariant, e.g.
`dist >= range - 1.5`), `--assert-last EXPR` on the final row only (outcome,
e.g. `chp < 1100`). Column names are variables, `eval` has no builtins, and
any failure exits 3. `ASSERT PASS` prints the row/expr counts.

Default runtime is the newest local pair, overridable with env vars:
    MLOGSIM_JAR   (default: out/_server160.jar, then out/_server159.jar, then out/_server146.jar)
    MLOGSIM_JAVA  (default: out/jre21/.../java.exe, then the Steam jre)

Saves made in build 160 (the current Mindustry format) need the v160 server:
v159.3 loads build-160 saves whose map uses the old tile encoding, and fails
with "Error reading region map" on the newer one. Keep both jars around; the
default is v160.7, and `MLOGSIM_JAR=.../_server159.jar` switches back.

Java 21+ is required (the Steam jlink image lacks java.logging).
v146 is kept for comparison only: it lacks `LogicBlock.readable`, so
cross-processor `read` by name always yields null there.

Child lifetime: the Java child goes into a Windows job object with
KILL_ON_JOB_CLOSE, so however this process ends -- a gate timeout, Ctrl-C, a
crash -- the kernel takes the server down with it. It used to survive (61 of
them once starved the machine until every probe failed with "insufficient
memory"). `--sweep-orphans` kills leftovers from older runs (only our jars,
only when the parent is gone) and exits.
Note: micro-processor runs 2 instructions/tick, logic-processor 8,
hyper-processor 25. `--steps` counts *instructions*, not ticks.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "mindustry-blueprint", "tools")

# Statements whose LStatement.privileged() is true: a micro processor silently
# turns them into InvalidStatement (LParser.read()), i.e. the line vanishes.
# Only the first word of a line is checked; operands are not.
# clientdata and localeprint are privileged too: ClientDataStatement
# (LStatements.java:2182-2184) and LocalePrintStatement (:2622-2625) both return
# true from privileged(), so a micro processor drops them -- the run then shows
# an empty instruction list, which reads like a version gap until you look.
PRIVILEGED_RE = re.compile(
    r"^\s*(weathersense|weatherset|setrule|message|cutscene|effect|fetch|sync|"
    r"getblock|setblock|getflag|setflag|spawnwave|spawn|status|clientdata|localeprint)\b", re.M)
STEAM_JAVA = r"E:\Program Files (x86)\Steam\steamapps\common\Mindustry\jre\bin\java.exe"
V160_JAR = os.path.join(ROOT, "out", "_server160.jar")
V159_JAR = os.path.join(ROOT, "out", "_server159.jar")
V159_JAVA = os.path.join(ROOT, "out", "jre21", "jdk-21.0.5+11-jre", "bin", "java.exe")
V146_JAR = os.path.join(ROOT, "out", "_server146.jar")


def _default_jar() -> str:
    if os.environ.get("MLOGSIM_JAR"):
        return os.environ["MLOGSIM_JAR"]
    for jar in (V160_JAR, V159_JAR, V146_JAR):
        if os.path.exists(jar):
            return jar
    return V146_JAR


def _default_java() -> str:
    env = os.environ.get("MLOGSIM_JAVA")
    if env:
        return env
    if os.path.exists(V159_JAVA):
        return V159_JAVA
    return STEAM_JAVA


from mlogent.simulation.process import (
    SimulatorProcess, SimError, absolute_command as _abs_path,
    bind_to_parent as _win_kill_with_parent, close_live_servers as _close_live_servers,
    powershell_json as _ps_json, LIVE_SERVERS as _LIVE_SERVERS,
)
from mlogent.simulation import process as _process


def sweep_orphans(dry_run=False):
    return _process.sweep_orphans(dry_run, query_processes=_ps_json)


_JS_CONSOLE_END = re.compile(r"\[[A-Z]\]\s+undefined\s*$")
_JS_CONSOLE_ERROR = re.compile(
    r"\[[A-Z]\]\s+(?:JavaScriptException|EcmaError|EvaluatorException|WrappedException):"
)


POWER_PROFILE_MAX_POINTS = 64
POWER_PROFILE_MAX_PER_SECOND = 600_000  # default native power-source output per second


def validate_power_profile(value, ticks: int) -> list[dict]:
    if not isinstance(value, list) or not 1 <= len(value) <= POWER_PROFILE_MAX_POINTS:
        raise ValueError(f"power_profile requires 1–{POWER_PROFILE_MAX_POINTS} points")
    previous = 0
    for point in value:
        if not isinstance(point, dict) or point.keys() != {"tick", "power_per_second"}:
            raise ValueError("each power_profile point requires tick and power_per_second")
        tick, power = point["tick"], point["power_per_second"]
        if type(tick) is not int or not previous < tick <= ticks or (previous == 0 and tick != 1):
            raise ValueError("power_profile must start at tick 1 and increase within the run")
        if type(power) not in (int, float) or not 0 <= power <= POWER_PROFILE_MAX_PER_SECOND:
            raise ValueError(f"power_per_second must be between 0 and {POWER_PROFILE_MAX_PER_SECOND}")
        previous = tick
    return value


class Server(SimulatorProcess):
    def __init__(self, java: str, jar: str, world_size: int | None = 64,
                 save: str | None = None, ore: str = "", ore_at=None,
                 ore_radius: int = 4, *, marker_preview: bool = False):
        self._save = save
        self._ore = ore
        self._ore_at = ore_at
        self._ore_radius = ore_radius
        self._base0 = None
        self._init_src = None
        self._core_spec = None
        self._unit_spec = None
        self._unit_pos = None
        self._weather_specs = []
        self._power_profile = None
        super().__init__(java, jar, workspace_root=ROOT, marker_preview=marker_preview,
                         bind_job=_win_kill_with_parent)
        try:
            self.wait_for("Server loaded.", 60)
            if save:
                # a save brings its own map, teams, cores, buildings and units;
                # `load` takes the slot name without the .msav suffix
                saves = os.path.join(self.workdir, "config", "saves")
                os.makedirs(saves, exist_ok=True)
                shutil.copyfile(save, os.path.join(saves, "scene.msav"))
                self.send("load scene")
                self.wait_for("Save loaded.", 120)
                self.send("pause on")
                time.sleep(0.3)
                out = self.js(PICK_BASE_JS)
                base_line = next((ln for ln in out if ln.startswith("BASE\t")), None)
                if base_line is None:
                    raise SimError("could not find an empty tile for the processor")
                _, bx, by = base_line.split("\t")
                self.base = (int(bx), int(by))
                world_line = next((ln for ln in out if ln.startswith("WORLD\t")), "")
                dims = world_line.split("\t", 1)[1].split("x") if "\t" in world_line else []
                self.world_size = int(dims[0]) if dims else None
            elif world_size:
                # no host: Vars.init already built state/world, loadGenerator makes
                # a blank map. Saves the ~0.5s random-map host and all port binding.
                self.world_size = world_size
                self.base = (0, 0)
                self.js(self._load_js())
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

    def js(self, script: str, timeout: float | None = None) -> list[str]:
        """Run one `js` command; return the lines it printed.

        TIMEOUT defaults to `self.js_timeout` (180 s unless `--js-timeout`).
        """
        self.buffer.clear()
        # the console reads one line per command: multi-line scripts would be
        # parsed as separate console commands
        self.send("js " + " ".join(script.splitlines()))
        if timeout is None:
            timeout = self.js_timeout
        lines = self.wait_for("JS result", timeout, terminal=lambda line: (
            _JS_CONSOLE_END.search(line) or _JS_CONSOLE_ERROR.search(line)))
        if _JS_CONSOLE_ERROR.search(lines[-1]):
            raise SimError(lines[-1])
        return [ln.split("[none/base.js]:", 1)[1].strip() for ln in lines if "[none/base.js]:" in ln]

    def fill_cores(self, spec: str) -> list[dict]:
        """Stock our team's cores; if there is none, drop a core-shard next to base.

        SPEC is `item:amount,item:amount` (item ids as in `sensor ... @copper`).
        """
        items: dict[str, int] = {}
        for part in spec.split(","):
            part = part.strip()
            if not part:
                continue
            name, _, amount = part.partition(":")
            name = name.strip().lstrip("@")
            if not name:
                raise SimError(f"bad --core-items entry: {part!r}")
            items[name] = int(amount) if amount else 1
        if not items:
            raise SimError("--core-items is empty")
        # auto-placed core: put it in a far corner.  A 3x3 core-shard dropped
        # next to base can be clipped by the auto-link ring (a 3x3 furnace
        # overlapping any of its tiles deletes the whole core).
        limit = self.world_size if self.world_size else 64
        cx = min(max(limit - 5, 2), limit - 3)
        cy = min(max(limit - 5, 2), limit - 3)
        out = self.js(CORE_JS % {"spec": json.dumps(items), "cx": cx, "cy": cy})
        cores = []
        for ln in out:
            if not ln.startswith("CORE\t"):
                continue
            _, x, y, name, total = ln.split("\t")
            cores.append({"x": int(x), "y": int(y), "block": name, "total": int(total)})
        if not cores:
            raise SimError("--core-items: no core found and the auto-placed one was not created")
        self.cores = cores
        return cores

    def reset_world(self):
        """Put the world back to its initial state so one JVM can run many jobs."""
        if getattr(self, "_save", None):
            self.send("load scene")
            self.wait_for("Save loaded.", 120)
            self.send("pause on")
            time.sleep(0.2)
            out = self.js(PICK_BASE_JS)
            base_line = next((ln for ln in out if ln.startswith("BASE\t")), None)
            if base_line is None:
                raise SimError("reset: could not find an empty tile for the processor")
            _, bx, by = base_line.split("\t")
            self.base = (int(bx), int(by))
        elif self.world_size:
            self.js(self._load_js())
        else:
            self.send("stop")
            time.sleep(0.2)
            self.send("host")
            self.wait_for("Opened a server", 120)
            self.send("pause on")
            time.sleep(0.3)
        if self._base0 is not None:
            self.base = self._base0

    def _load_js(self) -> str:
        return load_js(self.world_size or 64, self._ore, self._ore_at,
                       self._ore_radius)

    def prepare(self):
        """Re-apply world setup that reset_world() wipes (init-js, cores, units)."""
        if self._init_src:
            self.js(self._init_src)
        if self._core_spec:
            self.fill_cores(self._core_spec)
        if getattr(self, "_scene", None) is not None:
            # a scene brings its own buildings/units, so --units is ignored here
            import scene as _scene
            self._scene_report = _scene.apply_sim(self, self._scene)
            if self._scene.get("inline_only") and self._scene_report["errors"]:
                raise SimError("uploaded scene: " + self._scene_report["errors"][0])
        elif self._unit_spec:
            wx, wy = self._unit_pos or (self.base[0] * 8 + 4, self.base[1] * 8 + 4)
            self.js(UNIT_JS % {"spec": json.dumps(self._unit_spec), "wx": wx, "wy": wy})
        if getattr(self, "_auto_power_source", False):
            candidates = [[b["name"], b["x"], b["y"]] for b in self._scene["buildings"]
                          if self._power_target is None or b["name"] == self._power_target]
            lines = self.js(AUTO_POWER_SOURCE_JS % json.dumps(
                [candidates, self._power_target is not None, list(self.base)], ensure_ascii=True))
            result = next((line[11:] for line in lines if line.startswith("AUTO_POWER ")), None)
            if result is None:
                raise SimError("automatic power connection returned no result")
            self._scene_report["power_source"] = json.loads(result)
        if self._weather_specs:
            for wname, wint in self._weather_specs:
                self.js(weather_js(wname, wint))

from mlogent.simulation.scripts import (
    LOAD_JS, load_js, PICK_BASE_JS, CORE_JS, place_js,
    pads_js, STEP_JS, SCENE_JS, SCENE_PLACE_JS, SCENE_CONF_JS,
    SCENE_DUMP_JS, _scene_chunks, UNIT_JS, WORLD_JS, WEATHER_JS,
    weather_js, UNITS_JS, PREFLIGHT_JS, COMBAT_JS, TRACE_JS,
    _world_js, _world_tick_js, ITRACE_JS, PUSH_DEF_JS, _push_js,
    AUTO_POWER_SOURCE_JS, _power_profile_js, _loop_js, _scene_loop_js,
)


from mlogent.simulation.results import (
    parse_trace, PAD_COLUMNS, parse_pads, parse_results, TRACE_COLUMNS,
    check_asserts, _write_trace,
)


def _scene_anchor(srv):
    """仿真场景的锚点(格); 没场景返回 None. feed 带上它, 世界侧才能把
    "仿真坐标" 换成 "真世界坐标" (两边原点不同)."""
    sc = getattr(srv, "_scene", None)
    if not sc:
        return None
    try:
        import scene as _sc
        return _sc.anchor_of(sc)
    except Exception:  # noqa: BLE001
        return None


def _scene_path(srv):
    """仿真场景的绝对路径; 没场景返回 None. 写进 feed, 世界侧据此自己补场景."""
    p = getattr(srv, "_scene_path", None)
    return str(p) if p else None


LINK_ALIASES = {
    "cell": "memory-cell",
    "bank": "memory-bank",
    "message": "message",
    "switch": "switch",
    "sorter": "sorter",
    "unloader": "unloader",
    "dome": "overdrive-dome",
    "projector": "force-projector",
    "mender": "mender",
    "router": "router",
    "junction": "junction",
    "spectre": "spectre",
    "furnace": "silicon-arc-furnace",
    "pad": "landing-pad",
    "container": "container",
    "turret": "duo",
}


def infer_links(code: str) -> list[dict]:
    """Link names a `.mlog` uses but never assigns (`cell1`, `message2`, ...).

    A plain `.mlog` file has no link table: `read cell1 0` normally compiles to a
    null constant. With `--links auto` the simulator places a matching block next
    to the processor and wires it under that name. Names follow the game defaults
    (`memory-cell` -> `cell1`, `memory-bank` -> `bank1`, `overdrive-dome` -> `dome1`).
    """
    sys.path.insert(0, TOOLS)
    import mlogir  # noqa: E402

    prog = mlogir.parse(code)
    defined, used = set(), set()
    for st in prog.stmts:
        defined.update(st.defs)
        used.update(st.uses)
    out = []
    for name in sorted(used - defined):
        if name.startswith("@") or not re.fullmatch(r"[a-z][a-z0-9-]*\d+", name):
            continue
        base = re.sub(r"\d+$", "", name)
        if base not in LINK_ALIASES:
            continue
        out.append({"name": name, "block": LINK_ALIASES[base]})
    return out


def run_mlog(srv: Server, name: str, code: str, steps: int, ticks: bool = False,
             update: str = "none", power: float | None = 1.0, processor: str = "auto",
             combat: bool = False, trace: bool = False, unit_ai: str = "logic",
             preflight: bool = True, links: str = "auto",
             itrace: str | None = None, itrace_vars: tuple = (),
             setup_js: str | None = None, pads: int = 0, pad_radius: int = 11,
             pad_water: float = -1.0, pad_drain: float = 0.0,
             pad_refill: bool = True, push_file: str | None = None,
             push_every: int = 30, rt: float = 0.0, compile_diagnostics: bool = False) -> dict:
    # privileged statements exist only in world processors; selecting the block
    # that makes them compile is better than silently dropping whole lines.
    world_proc = processor == "world" or (processor == "auto" and PRIVILEGED_RE.search(code) is not None)
    link_specs = infer_links(code) if links == "auto" else []
    if pads:
        # pads_js() places and wires pad1..padN itself; an inferred duplicate
        # would add a second block under the same name (links are positional)
        link_specs = [s for s in link_specs if not re.fullmatch(r"pad\d+", s["name"])]
    pads_setup, pads_report = pads_js(pads, pad_radius, pad_water, pad_drain, pad_refill)
    # a scene brings its own processors: they must tick alongside the one under test
    scene_tick = ("var _p=(typeof PROCS=='undefined'?[]:PROCS);"
                  "for(var si=0;si<_p.length;si++){_p[si].updateTile();}") \
        if getattr(srv, "_scene", None) is not None else ""
    # a fresh processor keeps textBuffer/vars from leaking between programs
    srv.js(place_js(*srv.base, "world-processor" if world_proc else "micro-processor"))
    fd, path = tempfile.mkstemp(suffix=".mlog", dir=srv.workdir, text=True)
    os.close(fd)
    try:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(code)
        itr = None
        if itrace:
            from mlogir import parse

            itr = {"code": [stmt.raw[:512] for stmt in parse(code.splitlines()).stmts],
                   "vars": list(itrace_vars)}
        pace_ms = int(1000.0 / 60.0 / rt) if ticks and rt > 0 else 0
        compile_js = ""
        if compile_diagnostics:
            from native_mlog import COMPILE_JS

            compile_js = COMPILE_JS + r'print("COMPILE\t" + JSON.stringify(compileMlog(s, b.block.privileged)));'
        js = STEP_JS % {"path": path.replace("\\", "/"), "x": srv.base[0], "y": srv.base[1],
                        "links": json.dumps(link_specs, ensure_ascii=False),
                        "compile": compile_js, "diagnostics": "true" if compile_diagnostics else "false",
                        "setup": setup_js or "",
                        "pads": pads_setup,
                        "pads_report": pads_report,
                        "loop": _loop_js("b", steps, ticks, update, power, combat, trace, unit_ai,
                                         preflight, itr,
                                         power_profile=srv._power_profile,
                                         tick_extra=(
                                              ("try{ java.lang.Thread.sleep(%d); }catch(e9){} "
                                               % pace_ms if pace_ms else "")
                                              + scene_tick + (" padTick();" if pads else "")
                                              + (_push_js(push_file, push_every,
                                                          anchor=_scene_anchor(srv),
                                                          scene=_scene_path(srv),
                                                          label=getattr(srv, "_scene_name", None))
                                                 if push_file else "")))}
        if pace_ms and steps > 0 and not srv.js_timeout_explicit:
            # A paced run spends this much wall time sleeping before Java/IO overhead.
            lines = srv.js(js, timeout=srv.js_timeout + steps * pace_ms / 1000.0)
        else:
            lines = srv.js(js)
        if preflight:
            warns = [ln.split("\t") for ln in lines if ln.startswith("LINKWARN\t")]
            if warns:
                detail = "; ".join(f"{w[1]}: {w[2]}" for w in warns if len(w) > 2)
                raise SimError(f"link preflight: {detail} (use --links off to allow null links)")
        recs = parse_results(lines)
        rec = recs[0] if recs else {"vars": {}, "counter": None, "text": ""}
        if compile_diagnostics:
            rec["compile"] = next(json.loads(ln.split("\t", 1)[1]) for ln in lines
                                  if ln.startswith("COMPILE\t"))
        rec["trace"] = parse_trace(lines) if trace else []
        if itrace:
            rows = [ln for ln in lines if ln.startswith("ITRACE\t")]
            with open(itrace, "w", encoding="utf-8", newline="\n") as f:
                f.write("tick\tpc\tvars\tsource\n")
                for ln in rows:
                    f.write(ln[len("ITRACE\t"):] + "\n")
            rec["itrace"] = itrace
        rec["name"] = name
        rec["steps"] = steps
        rec["mode"] = "tick" if ticks else "instruction"
        rec["update"] = update
        rec["processor"] = "world" if world_proc else "micro"
        rec["links"] = link_specs
        rec["pads"] = parse_pads(lines)
        return rec
    finally:
        os.unlink(path)


def run_msch(srv: Server, name: str, path: str, steps: int, ticks: bool = False,
             update: str = "none", power: float | None = 1.0,
             combat: bool = False, trace: bool = False, unit_ai: str = "logic",
             preflight: bool = True) -> list[dict]:
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
    loop = _scene_loop_js(steps, ticks, update, power, combat, trace, unit_ai, preflight)
    batch = int(getattr(srv, "scene_batch", 0) or 0)
    if batch and len(tiles) > batch:
        # big scene: keep every js command small (see SCENE_PLACE_JS above).
        lines = []
        for chunk in _scene_chunks(tiles, batch):
            lines.extend(srv.js(SCENE_PLACE_JS % {"tiles": json.dumps(chunk)}))
        coded = [t for t in tiles if t.get("logic")]
        for chunk in _scene_chunks(coded, max(1, batch // 10)):
            lines.extend(srv.js(SCENE_CONF_JS % {"tiles": json.dumps(chunk)}))
        lines.extend(srv.js("var procs = globalThis.procs;" + loop))
        want = getattr(srv, "scene_dump", None)
        want_js = "null" if not want else json.dumps(list(want))
        lines.extend(srv.js(SCENE_DUMP_JS % {"want": want_js}))
    else:
        js = SCENE_JS % {"tiles": json.dumps(tiles), "loop": loop}
        lines = srv.js(js)
    recs = parse_results(lines)
    rows = parse_trace(lines) if trace else []
    for r in recs:
        r["name"] = name
        r["steps"] = steps
        r["mode"] = "tick" if ticks else "instruction"
        r["update"] = update
        r["trace"] = rows
    return recs


def _xy_arg(spec: str | None):
    """Parse an "X,Y" CLI option into a tuple, or None."""
    if not spec:
        return None
    try:
        x, y = spec.replace(" ", "").split(",")
        return int(float(x)), int(float(y))
    except Exception:
        raise SimError("bad coordinate %r (want X,Y)" % spec)


def configure_server(srv: Server, args):
    """Attach per-run world setup so prepare() can replay it after each reset."""
    if getattr(args, "js_timeout", None) is not None:
        srv.js_timeout = float(args.js_timeout)
        srv.js_timeout_explicit = True
    srv._power_profile = args.power_profile
    if args.base:
        srv.base = tuple(int(v) for v in args.base.split(","))
        srv._base0 = srv.base
    if args.init_js:
        if os.path.exists(args.init_js):
            with open(args.init_js, encoding="utf-8-sig") as fh:
                srv._init_src = fh.read()
        else:
            srv._init_src = args.init_js
    if args.core_items:
        srv._core_spec = args.core_items
    if args.units:
        spec = []
        for part in args.units.split(","):
            part = part.strip()
            if not part:
                continue
            name, _, cnt = part.partition(":")
            spec.append([name.strip(), int(cnt) if cnt else 1])
        srv._unit_spec = spec
        if args.unit_pos:
            ux, uy = (float(v) for v in args.unit_pos.split(","))
            srv._unit_pos = (ux * 8 + 4, uy * 8 + 4)
    if args.weather:
        for wspec in args.weather:
            wname, _, wint = wspec.partition(":")
            srv._weather_specs.append((wname.strip(), float(wint) if wint else 1.0))


DAEMON_FILE = os.path.join(ROOT, "out", "_mlogsimd.json")


def serve_daemon(args, steps: int, ticks: bool, update: str, power: float, combat: bool,
                 preflight: bool):
    """Boot once, then answer JSON-line jobs over localhost (prewarm for a session)."""
    import socket
    world_size = None if args.host or args.world == 0 else args.world
    srv = Server(args.java, args.jar, world_size, args.save, ore=args.ore,
                 ore_at=_xy_arg(args.ore_at), ore_radius=args.ore_radius)
    configure_server(srv, args)
    srv.prepare()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", args.port))
    sock.listen(4)
    port = sock.getsockname()[1]
    with open(DAEMON_FILE, "w", encoding="utf-8") as fh:
        json.dump({"pid": os.getpid(), "port": port, "world": world_size, "save": args.save}, fh)
    print("DAEMON\t%d" % port, flush=True)
    try:
        while True:
            conn, _ = sock.accept()
            try:
                with conn:
                    line = conn.makefile("r", encoding="utf-8").readline()
                    req = json.loads(line)
                    srv.reset_world()
                    srv.prepare()
                    f = req["file"]
                    n = int(req.get("ticks") or 0)
                    t = n > 0
                    st = n if t else int(req.get("steps") or steps)
                    if f.lower().endswith(".msch"):
                        recs = run_msch(srv, os.path.basename(f), f, st, t, update, power,
                                        combat, False, args.unit_ai, preflight)
                    else:
                        with open(f, encoding="utf-8-sig") as fh:
                            code = fh.read()
                        recs = [run_mlog(srv, os.path.basename(f), code, st, t, update, power,
                                         args.processor, combat, False, args.unit_ai,
                                         preflight, args.links,
                                         pads=args.pads, pad_radius=args.pad_radius,
                                         pad_water=args.pad_water, pad_drain=args.pad_drain,
                                         push_file=args.push, push_every=args.push_every, rt=args.rt)]
                    conn.sendall((json.dumps({"ok": True, "results": recs},
                                             ensure_ascii=False) + "\n").encode("utf-8"))
            except Exception as e:  # noqa: BLE001 - report to the client, keep serving
                try:
                    conn.sendall((json.dumps({"ok": False, "error": str(e)},
                                             ensure_ascii=False) + "\n").encode("utf-8"))
                except OSError:
                    pass
    finally:
        try:
            os.unlink(DAEMON_FILE)
        except OSError:
            pass
        srv.close()


def remote_client(args) -> int:
    """Send files to a running --daemon and print its results."""
    import socket
    if not os.path.exists(DAEMON_FILE):
        sys.exit("no daemon: start `python tools/mlogsim.py --daemon` first")
    with open(DAEMON_FILE, encoding="utf-8") as fh:
        cfg = json.load(fh)
    out = []
    for f in args.files:
        req = {"file": os.path.abspath(f)}
        if args.ticks:
            req["ticks"] = args.ticks
        elif args.steps:
            req["steps"] = args.steps
        try:
            with socket.create_connection(("127.0.0.1", cfg["port"]), timeout=300) as s:
                s.sendall((json.dumps(req) + "\n").encode("utf-8"))
                line = s.makefile("r", encoding="utf-8").readline()
        except OSError:
            sys.exit(f"daemon not running (stale {DAEMON_FILE}?); start --daemon again")
        resp = json.loads(line)
        if not resp.get("ok"):
            sys.exit(f"sim failed: {resp.get('error')}")
        out.extend(resp["results"])
    print(json.dumps(out, ensure_ascii=False, indent=2) if args.json else
          "\n".join(f"== {r['name']} ==" for r in out))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="run mlog on the real Mindustry LExecutor")
    ap.add_argument("files", nargs="*", help=".mlog files (or .msch schematics)")
    ap.add_argument("--daemon", action="store_true",
                    help="boot once and serve JSON jobs on 127.0.0.1 (warm start for a session)")
    ap.add_argument("--remote", action="store_true",
                    help="send the files to the running --daemon instead of booting a server")
    ap.add_argument("--port", type=int, default=0,
                    help="--daemon port (0 = pick a free one and write out/_mlogsimd.json)")
    ap.add_argument("--steps", type=int, default=None, help="instructions to execute (default 200)")
    ap.add_argument("--ticks", type=int, default=None,
                    help="simulated ticks: drive updateTile() with Time.delta=1 (accumulator/ipt/wait)")
    ap.add_argument("--marker-preview", metavar="PNG",
                    help="render the final marker frame to a PNG and include its state in --json")
    ap.add_argument("--compile-diagnostics", action="store_true",
                    help="report native compiler diagnostics for standalone Mlog in --json")
    ap.add_argument("--world-probe", metavar="FILE",
                    help="read a JSON query with optional checks for tiles, objective flags and rules "
                         "at the final tick (use with --json)")
    ap.add_argument("--js-timeout", type=float, metavar="SEC",
                    help="override the JS wall-clock budget (default: 180 s plus realtime pacing)")
    ap.add_argument("--world", type=int, default=None, metavar="N",
                    help="blank NxN world loaded with loadGenerator (default 64, or the "
                         "scene's world.size with --scene; 0 = host a random map)")
    ap.add_argument("--host", action="store_true",
                    help="host a random map instead of the blank world (needed for terrain/@mapw)")
    ap.add_argument("--jar", default=_default_jar())
    ap.add_argument("--java", default=_default_java())
    ap.add_argument("--init-js", metavar="FILE|CODE", default=None,
                    help="JS run once after the world exists: set rules, seed blocks")
    ap.add_argument("--scene", metavar="FILE", default=None,
                    help="scene JSON (tools/scene.py): place buildings/links/code/units "
                         "exactly like the world server would; replaces --units")
    ap.add_argument("--scene-probe", dest="scene_probe", action="store_true",
                    help="after the run, dump the scene's logic variables and evaluate "
                         "its \"checks\"")
    ap.add_argument("--units", metavar="NAME[:N],...", default=None,
                    help="spawn units near the processor as team sharded, e.g. flare:3,poly:1")
    ap.add_argument("--unit-pos", metavar="X,Y", default=None,
                    help="spawn units at this tile coordinate instead of 2 tiles off the processor, e.g. 6,4")
    ap.add_argument("--update", choices=["none", "all"], default=None,
                    help="world update per tick: all = every building (default in --ticks mode), none = logic only")
    ap.add_argument("--power", choices=["full", "none", "grid"],
                    help="full (default) or none pins power; grid advances the original power graphs in local tick runs")
    ap.add_argument("--power-profile", metavar="JSON",
                    help="grid output schedule for all power-source blocks, as tick/power_per_second points")
    ap.add_argument("--combat", choices=["on", "off"], default=None,
                    help="run bullet physics + damage each tick (default on with --ticks). "
                         "Without it a unit fires but bullets never move or hit")
    ap.add_argument("--itrace", metavar="FILE", default=None,
                    help="write per-instruction execution trace (tick, pc, vars, source)")
    ap.add_argument("--itrace-var", dest="itrace_vars", action="append", default=[],
                    metavar="NAME", help="variable to include in each --itrace row (repeatable)")
    ap.add_argument("--trace", metavar="FILE", default=None,
                    help="write per-tick CSV of logic-controlled units (tiles): "
                         "unit,tick,ux,uy,uhp,range,tx,ty,dist,cx,cy,chp,bullets,shots")
    ap.add_argument("--assert", dest="asserts", action="append", default=None, metavar="EXPR",
                    help="evaluate EXPR on every trace row (e.g. 'dist >= range - 1.5'); "
                         "exit 3 on any failure")
    ap.add_argument("--assert-last", dest="asserts_last", action="append", default=None, metavar="EXPR",
                    help="evaluate EXPR on the final trace row only (e.g. 'chp < 1100' = "
                         "the target took damage); exit 3 on failure")
    ap.add_argument("--processor", choices=["auto", "micro", "world"], default="auto",
                    help="block for a .mlog program; auto = world-processor when it uses privileged "
                         "statements (weathersense/weatherset/...), which a micro processor silently drops")
    ap.add_argument("--weather", metavar="NAME[:INTENSITY]", action="append", default=None,
                    help="force a weather active from tick 0, e.g. rain or sandstorm:0.5; repeatable. "
                         "Without it the world starts clear (a --host map can still start its own weather)")
    ap.add_argument("--unit-ai", choices=["logic", "all"], default="logic",
                    help="which units get Unit.update() per tick: logic = only units a "
                         "processor controls; all = also the world's own AI (enemy defenders shoot back)")
    ap.add_argument("--save", metavar="FILE", default=None,
                    help="load a .msav scene instead of a blank world: its map, teams, "
                         "cores, buildings and units all come with it (slot 'scene')")
    ap.add_argument("--core-items", metavar="ITEM:N,...", default=None,
                    help="fill our team's core(s) before the run, e.g. silicon:400,phase-fabric:200; "
                         "on a blank world a core-shard is placed next to the processor")
    ap.add_argument("--base", metavar="X,Y", default=None,
                    help="tile for the processor: default 0,0 on a blank world, auto "
                         "next to your core with --save")
    ap.add_argument("--no-preflight", action="store_true",
                    help="skip the tick-1 check that spawned units are still alive")
    ap.add_argument("--links", choices=["auto", "off"], default="auto",
                    help="auto (default): for a .mlog, place a block for every name it "
                         "reads but never assigns (cell1 -> memory-cell, message1 -> message) "
                         "and wire it; off: leave them null as a plain .mlog would")
    ap.add_argument("--project", action="store_true",
                    help="--push <repo>/out/_world/feed.json 的简写：世界服默认盯这条 feed，"
                         "所以「跑仿真就自动投影」只要这一个开关")
    ap.add_argument("--push", metavar="FILE", default=None,
                    help="every --push-every ticks, overwrite FILE with a JSON snapshot of the "
                         "world's units ([{type,x,y,amount,ctrl}], x/y in TILES). "
                         "Pair it with the world server's mirror_feed to draw the sim as markers")
    ap.add_argument("--push-every", type=int, default=30, metavar="N",
                    help="ticks between snapshots (default 30 = twice a second at 60fps)")
    ap.add_argument("--pads", type=int, default=0, metavar="N",
                    help="also place N real landing pads (4x4) and wire them as link 0..N-1, "
                         "then report config/arriving/cooldown/items/water/landings per pad. "
                         "Sets rules.allowEditWorldProcessors, otherwise LandingPad.config() "
                         "silently refuses every item. Needs --ticks with --update all")
    ap.add_argument("--pad-radius", type=int, default=11, metavar="R",
                    help="search radius (tiles) for pad spots around the processor (default 11)")
    ap.add_argument("--pad-water", type=float, default=-1.0, metavar="N",
                    help="water per pad; -1 (default) = full tank. The efficiency gate wants "
                         "1500, i.e. half a tank, so anything below that reads eff=0")
    ap.add_argument("--no-pad-refill", dest="pad_refill", action="store_false",
                    help="let the water run out instead of keeping the tank full; every landing "
                         "drinks 1500 of 3000, so a pad stops after two landings (eff -> 0)")
    ap.add_argument("--pad-drain", type=float, default=0.0, metavar="N",
                    help="remove N items per tick from each pad (emulates the output logistics; "
                         "a pad only lands again once its 100 items are gone)")
    ap.add_argument("--ore", metavar="ITEM", default="",
                    help="paint an ore disc of ITEM (e.g. copper -> block ore-copper) "
                         "so ulocate ore / ucontrol mine work; painted inside the "
                         "loadGenerator callback, which is what fills BlockIndexer's "
                         "ore quadrants")
    ap.add_argument("--ore-at", metavar="X,Y", default=None,
                    help="ore disc centre in tiles (default: 3/4 of the world size)")
    ap.add_argument("--ore-radius", type=int, default=4, metavar="R",
                    help="ore disc radius in tiles (default 4)")
    ap.add_argument("--sweep-orphans", action="store_true",
                    help="kill simulator JVMs left behind by killed runs, then exit")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--workspace-root", help=argparse.SUPPRESS)
    ap.add_argument("--uploaded-scene", help=argparse.SUPPRESS)
    ap.add_argument("--power-target", help=argparse.SUPPRESS)
    ap.add_argument("--rt", type=float, default=0.0, metavar="X",
                    help="simulation speed multiplier (1 = realtime, 3 = about 3x, 0 = unthrottled)")
    args = ap.parse_args(argv)
    if not math.isfinite(args.rt) or args.rt < 0:
        ap.error("--rt must be finite and non-negative")
    if args.js_timeout is not None and (not math.isfinite(args.js_timeout) or args.js_timeout <= 0):
        ap.error("--js-timeout must be finite and positive")
    if args.project and not args.push:
        args.push = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                 "out", "_world", "feed.json")

    if args.sweep_orphans:
        killed = sweep_orphans()
        print("orphan sweep: %d stale JVM(s)%s" % (
            len(killed), (" " + " ".join(str(p) for p in killed)) if killed else ""))
        return 0

    ticks = args.ticks is not None
    world_query = None
    if args.world_probe is not None:
        import world_probe

        if not ticks or args.ticks < 1 or args.steps is not None or args.remote or args.daemon or len(args.files) > 1:
            ap.error("--world-probe requires a positive local --ticks run with at most one input file")
        if not args.json:
            ap.error("--world-probe requires --json")
        try:
            with open(args.world_probe, encoding="utf-8-sig") as source:
                world_query = world_probe.validate(json.load(source))
        except (OSError, ValueError) as exc:
            ap.error(str(exc))
    if args.marker_preview:
        if not ticks or args.ticks < 1 or args.steps is not None or args.remote or args.daemon or len(args.files) > 1:
            ap.error("--marker-preview requires a positive local --ticks run with at most one input file")
        if args.processor == "auto":
            args.processor = "world"
        args.marker_preview = os.path.abspath(args.marker_preview)
    steps = args.ticks if ticks else (args.steps if args.steps is not None else 200)
    update = args.update if args.update is not None else ("all" if ticks else "none")
    args.power = args.power or ("grid" if args.power_profile is not None else "full")
    if args.power_profile is not None and args.power != "grid":
        ap.error("--power-profile requires --power grid")
    if args.power == "grid":
        if not ticks or args.ticks < 1 or update != "all" or args.remote or args.daemon:
            ap.error("--power grid requires a positive local --ticks count with --update all")
        if any(path.lower().endswith(".msch") for path in args.files):
            ap.error("--power grid needs a layout with power links; use --save instead of a .msch file")
    if args.power_profile is not None:
        try:
            args.power_profile = validate_power_profile(json.loads(args.power_profile), steps)
        except ValueError as exc:
            ap.error(str(exc))
    power = {"full": 1.0, "none": 0.0, "grid": None}[args.power]
    combat = (args.combat == "on") if args.combat else ticks
    want_trace = bool(args.trace or args.asserts or args.asserts_last)
    if want_trace and (not ticks or args.remote or args.daemon):
        ap.error("unit traces and their assertions require a local --ticks run")
    if args.itrace_vars and not args.itrace:
        ap.error("--itrace-var requires --itrace")
    if args.itrace and (args.remote or args.daemon or not args.files
                        or any(name.lower().endswith(".msch") for name in args.files)):
        ap.error("--itrace requires a local mlog file (not a blueprint or scene-only run)")
    preflight = not args.no_preflight

    if not os.path.exists(args.jar):
        sys.exit(f"missing server jar: {args.jar}")

    scene_obj = None
    if args.scene or args.uploaded_scene:
        import scene as _scene_mod
        try:
            scene_obj = _scene_mod.load(args.scene or args.uploaded_scene,
                                        workspace_root=args.workspace_root if args.scene else None,
                                        inline_only=bool(args.uploaded_scene))
        except (ValueError, TypeError, OverflowError) as exc:
            sys.exit(f"scene invalid: {exc}")
        if args.world is None:
            args.world = scene_obj["world"]["size"]
    if args.world is None:
        args.world = 64

    world_size = None if args.host or args.world == 0 else args.world
    if args.remote:
        return remote_client(args)
    if args.daemon:
        serve_daemon(args, steps, ticks, update, power, combat, preflight)
        return 0
    if not args.files and scene_obj is None:
        sys.exit("no input files (or use --daemon, or --scene with a logic file)")
    srv = Server(args.java, args.jar, world_size, args.save, ore=args.ore,
                 ore_at=_xy_arg(args.ore_at), ore_radius=args.ore_radius,
                 marker_preview=bool(args.marker_preview))
    configure_server(srv, args)
    if scene_obj is not None:
        srv._scene = scene_obj
        srv._auto_power_source = bool(args.uploaded_scene and args.power == "grid")
        srv._power_target = args.power_target
        # 路径与名字留给 --push: feed 里带上出处, 世界侧只拿 feed 也能补出建筑
        srv._scene_path = os.path.abspath(args.scene) if args.scene else None
        srv._scene_name = scene_obj["name"]
    results = []
    scene_probe = None
    try:
        for idx, f in enumerate(args.files or [None]):
            if idx:
                # one JVM for the whole batch: reload the world (~0.12 s) instead
                # of paying the ~3 s server boot for every file
                srv.reset_world()
            srv.prepare()
            if f is None:
                # scene-only run: the scene is applied by prepare(), keep a
                # resident no-op program so the executor has something to run
                results.append(run_mlog(srv, "<scene>", "end", steps, ticks, update, power,
                                        args.processor, combat, want_trace, args.unit_ai,
                                        preflight, args.links, None, (),
                                        push_file=args.push, push_every=args.push_every, rt=args.rt))
                continue
            if f.lower().endswith(".msch"):
                results.extend(run_msch(srv, os.path.basename(f), f, steps, ticks, update, power,
                                        combat, want_trace, args.unit_ai, preflight))
            else:
                # utf-8-sig: PowerShell's `Set-Content -Encoding utf8` prepends a BOM,
                # and the parser turns a BOM-prefixed first line into a noop
                with open(f, encoding="utf-8-sig") as fh:
                    code = fh.read()
                itr_path = args.itrace
                if itr_path and len(args.files) > 1:
                    itr_path = itr_path + "." + os.path.basename(f)
                results.append(run_mlog(srv, os.path.basename(f), code, steps, ticks,
                                        update, power, args.processor, combat, want_trace,
                                        args.unit_ai, preflight, args.links,
                                        itr_path, tuple(args.itrace_vars),
                                        pads=args.pads, pad_radius=args.pad_radius,
                                        pad_water=args.pad_water, pad_drain=args.pad_drain,
                                        pad_refill=args.pad_refill,
                                        push_file=args.push, push_every=args.push_every, rt=args.rt,
                                        compile_diagnostics=args.compile_diagnostics))
        if scene_obj is not None and (args.scene_probe or args.uploaded_scene):
            import scene as _scene_probe_mod
            scene_probe = _scene_probe_mod.probe_sim(srv, scene_obj)
        if args.marker_preview and results:
            import marker_preview
            results[0]["marker_preview"] = marker_preview.capture(srv, args.marker_preview, steps)
        if world_query is not None and results:
            results[0]["world_probe"] = world_probe.capture(srv.js, world_query, steps)
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

    scene_report = getattr(srv, "_scene_report", None)
    if results and (scene_report or scene_probe):
        results[0]["scene"] = scene_report
        results[0]["scene_probe"] = scene_probe

    trace_rows: list[list[str]] = []
    for r in results:
        trace_rows.extend(r.pop("trace", []) or [])
    if args.trace:
        _write_trace(args.trace, trace_rows)
    diagnostic_stream = sys.stderr if args.json else sys.stdout
    failed = check_asserts(trace_rows, args.asserts, output=diagnostic_stream) if args.asserts else 0
    if args.asserts_last:
        failed += check_asserts(trace_rows[-1:], args.asserts_last, output=diagnostic_stream)

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
            if r.get("mode") == "tick":
                print(f"  world = {r.get('update')}  power = {'full' if power else 'none'}"
                      f"  combat = {'on' if combat else 'off'}"
                      + (f"  processor = {r['processor']}" if r.get("processor") else ""))
            if r.get("skipped"):
                print(f"  skipped: {', '.join(r['skipped'])}")
            if r.get("scene"):
                sc_rep = r["scene"]
                print(f"  scene: placed={sc_rep['placed']} config={sc_rep['configured']}"
                      f" stock={sc_rep['stocked']} logic={sc_rep['linked']}"
                      f" units={sc_rep['units']}")
                for wmsg in sc_rep.get("warnings") or []:
                    print(f"  scene warn: {wmsg}")
                for emsg in sc_rep["errors"]:
                    print(f"  scene ERROR: {emsg}")
            if r.get("scene_probe"):
                sp = r["scene_probe"]
                for c in sp["checks"]:
                    mark = "ok  " if c["ok"] else "FAIL"
                    print(f"  check {mark} {c['logic']}.{c['var']} = {c['actual']!r}"
                          f" (want {c['expect']!r})")
                if not sp["checks"]:
                    print("  probe: " + ", ".join(f"{k}={v}" for k, v in sp["vars"].items()))
            for pd in r.get("pads") or []:
                num = lambda k, spec=".2f": ("?" if pd.get(k) is None else format(pd[k], spec))
                print(f"  PAD {pd.get('name')} ({num('x', '.0f')},{num('y', '.0f')})"
                      f" cfg={pd.get('config')} arriving={pd.get('arriving')}"
                      f" cd={num('cooldown')} items={num('items', '.0f')}"
                      f" water={num('water', '.0f')} eff={num('efficiency', '.0f')}"
                      f" landings={num('landings', '.0f')}")
    if args.trace:
        print(f"TRACE  {len(trace_rows)} row(s) -> {args.trace}", file=diagnostic_stream)
    if scene_report and scene_report["errors"]:
        failed += len(scene_report["errors"])
    if scene_probe and not args.uploaded_scene:
        failed += sum(0 if c["ok"] else 1 for c in scene_probe["checks"])
    return 3 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
