"""Run the four theory benches and print a PASS/FAIL table.

    python out/scenes/benches/run.py

memory-bench / processor-bench are schematics built by build.py.
sensor-bench spawns five real units and compares every mlog `sensor` read
against the engine's own value for that unit.
core-bench runs core-bench.mlog on the blank world: a core-shard is filled by
`Server.fill_cores`, then the unit reads it, takes 15, drops 5, reads it again.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import mlogsim as M  # noqa: E402

FAILS = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(("PASS  " if ok else "FAIL  ") + name + (("  -- " + detail) if detail and not ok else ""))
    if not ok:
        FAILS.append(name)


def run_scene(path: Path, ticks: int):
    srv = M.Server(M._default_java(), M._default_jar())
    try:
        recs = M.run_msch(srv, path.name, str(path), ticks, ticks=True, update="none")
        cap = srv.js("print(Vars.state.rules.unitCap)")
        return {r["label"]: r for r in recs}, cap
    finally:
        srv.close()


# ---------------------------------------------------------------- memory bench
def memory_bench() -> None:
    by, _ = run_scene(HERE / "memory-bench.msch", 12)
    var = lambda label, k: by[label]["vars"].get(k)
    check("memory: cell1[0] == 7", var("6,0", "a") == "7", var("6,0", "a"))
    check("memory: unwritten cell slot reads 0 (not null)", var("6,0", "b") == "0", var("6,0", "b"))
    check("memory: other cell slot reads 0", var("6,0", "c") == "0", var("6,0", "c"))
    check("memory: another processor's var == 42", var("6,0", "d") == "42", var("6,0", "d"))
    check("memory: writer's var is declared", var("0,0", "declared") == "42", var("0,0", "declared"))
    check("memory: slot 1 == 8", var("9,0", "e") == "8", var("9,0", "e"))
    check("memory: write then read slot 2 == 99", var("9,0", "f") == "99", var("9,0", "f"))


# ------------------------------------------------------------- processor bench
def processor_bench() -> None:
    by, cap = run_scene(HERE / "processor-bench.msch", 14)
    ipt = lambda label: by[label]["ipt"]
    check("processor: micro @ipt == 2", ipt("0,0") == 2.0, str(ipt("0,0")))
    check("processor: logic @ipt == 8", ipt("4,0") == 8.0, str(ipt("4,0")))
    check("processor: hyper @ipt == 25", ipt("8,0") == 25.0, str(ipt("8,0")))
    check("processor: world @ipt == 8", ipt("12,0") == 8.0, str(ipt("12,0")))
    check("processor: hyper bank[63] == 25", by["8,0"]["vars"].get("w") == "25",
          by["8,0"]["vars"].get("w"))
    check("processor: world setrule unitCap == 77", "77" in cap, cap)


# ---------------------------------------------------------------- sensor bench
UNITS = [("dagger", 1), ("flare", 2), ("mono", 3), ("mega", 4), ("fortress", 5)]

SPAWN = r"""
var defs = %(defs)s;
var team = Packages.mindustry.game.Team.sharded;
Vars.state.rules.logicUnitControl = true;
Vars.state.rules.unitCap = 1000;
for(var i = 0; i < defs.length; i++){
    var name = defs[i][0], flag = defs[i][1];
    var ut = null;
    for(var k = 0; k < Vars.content.units().size; k++){
        var t = Vars.content.units().get(k);
        if(t.name == name){ ut = t; break; }
    }
    if(ut == null){ print("NOUNIT\t" + name); continue; }
    var u = ut.spawn(team, (10 + i * 4) * 8 + 4, 10 * 8 + 4);
    u.flag = flag;
}
Vars.state.teams.updateTeamStats();
for(var k = 0; k < Packages.mindustry.gen.Groups.unit.size(); k++){
    var u = Packages.mindustry.gen.Groups.unit.index(k);
    print("ENGINE\t" + u.type.name + "\t" + u.flag + "\t" + u.health + "\t"
        + u.type.armor + "\t" + u.shield + "\t" + (u.type.maxRange / 8) + "\t"
        + u.dead + "\t" + (u.x / 8) + "\t" + (u.y / 8));
}
"""


def sensor_bench() -> None:
    names = [n for n, _ in UNITS]
    probe = []
    for n in names:
        probe.append(f"ubind @{n}")
        for field, var in (("health", "h"), ("armor", "a"), ("shield", "s"),
                           ("range", "r"), ("speed", "v"), ("flag", "f"),
                           ("type", "t"), ("controlled", "c"), ("dead", "d"),
                           ("x", "x"), ("y", "y")):
            probe.append(f"sensor {var}_{n} @unit @{field}")
    probe.append("end")
    code = "\n".join(probe)

    srv = M.Server(M._default_java(), M._default_jar())
    try:
        lines = srv.js(SPAWN % {"defs": str(UNITS).replace("(", "[").replace(")", "]")})
        engine = {}
        for ln in lines:
            if ln.startswith("ENGINE\t"):
                _, name, flag, hp, armor, shield, rng, dead, x, y = ln.split("\t")
                engine[name] = dict(flag=flag, hp=hp, armor=armor, shield=shield,
                                    rng=rng, dead=dead, x=x, y=y, ctl="0")
        rec = M.run_mlog(srv, "sensor-bench", code, 45, ticks=True)
    finally:
        srv.close()

    v = rec["vars"]

    def num_eq(key, want, tol=0.02):
        try:
            return abs(float(v.get(key)) - float(want)) <= tol
        except (TypeError, ValueError):
            return False

    for name, flag in UNITS:
        e = engine.get(name)
        if e is None:
            check(f"sensor: {name} spawned", False, "no engine line")
            continue
        check(f"sensor: {name} flag == {flag}", v.get(f"f_{name}") == str(flag), v.get(f"f_{name}"))
        check(f"sensor: {name} health == engine", num_eq(f"h_{name}", e["hp"]), v.get(f"h_{name}"))
        check(f"sensor: {name} armor == engine", num_eq(f"a_{name}", e["armor"]), v.get(f"a_{name}"))
        check(f"sensor: {name} range == engine", num_eq(f"r_{name}", e["rng"]), v.get(f"r_{name}"))
        check(f"sensor: {name} dead == 0", v.get(f"d_{name}") == "0", v.get(f"d_{name}"))
        check(f"sensor: {name} x == engine", num_eq(f"x_{name}", e["x"]), v.get(f"x_{name}"))
        check(f"sensor: {name} y == engine", num_eq(f"y_{name}", e["y"]), v.get(f"y_{name}"))
        check(f"sensor: {name} controlled == engine", v.get(f"c_{name}") == ("1" if e["ctl"] == "true" else "0"),
              f"mlog={v.get('c_' + name)} engine={e['ctl']}")
        check(f"sensor: {name} type reads the type", v.get(f"t_{name}") is not None and "null" not in str(v.get(f"t_{name}")),
              str(v.get(f"t_{name}")))

    print("\n| unit | flag | health | armor | shield | range | speed | controlled |")
    print("|---|---|---|---|---|---|---|---|")
    for name, _ in UNITS:
        print("| {} | {} | {} | {} | {} | {} | {} | {} |".format(
            name, v.get(f"f_{name}"), v.get(f"h_{name}"), v.get(f"a_{name}"),
            v.get(f"s_{name}"), v.get(f"r_{name}"), v.get(f"v_{name}"),
            v.get(f"c_{name}")))
    print()


# ------------------------------------------------------------------ core bench
def core_bench() -> None:
    code = (HERE / "core-bench.mlog").read_text(encoding="utf-8")
    srv = M.Server(M._default_java(), M._default_jar())
    try:
        srv.fill_cores("silicon:400")
        srv.js(M.UNIT_JS % {"spec": '[["mono", 1]]', "wx": 4, "wy": 4})
        rec = M.run_mlog(srv, "core-bench", code, 300, ticks=True, update="all")
    finally:
        srv.close()

    v = rec["vars"]
    check("core: stock before/after take reads 385", v.get("si") == "385", str(v.get("si")))
    check("core: unit took 15", v.get("have") == "15", str(v.get("have")))
    check("core: unit dropped 5 -> 10", v.get("left") == "10", str(v.get("left")))
    check("core: stock after drop == 390", v.get("after") == "390", str(v.get("after")))


def main() -> int:
    memory_bench()
    processor_bench()
    sensor_bench()
    core_bench()
    print()
    if FAILS:
        print(f"{len(FAILS)} check(s) FAILED")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
