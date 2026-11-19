"""Real DPS on a white target: what a single adjacent enemy actually loses.

The panel number (`60/reload * shots * damage`) is a *bullet-layer* number.  It
is right for direct-fire turrets and wrong in both directions for the rest:
splash/frag weapons deliver more to one target, artillery delivers less because
shells disperse.  This module measures instead of deriving.

`sbox()` must run first: `scatter` is anti-air only (targetGround=false) and
`ripple` has minRange=50, so a ground target at three tiles is invisible to one
and inside the blind spot of the other.  That is why the naive probe reported
0 dps for both.

The rig (each item below cost a debugging round, keep them):
  * scene buildings take "x"/"y"; units take "at"; scene.load() normalises, so
    never hand a raw dict to Server._scene (KeyError: 'clear').
  * srv.js() runs in console.js: no worldTick()/combatPre(), no `sb`, and `log`
    is already declared there (a local `var log` is a SyntaxError).
  * stocking a turret's ItemModule does NOT fill its `ammo` seq; call
    handleItem() or the turret sits there with items and no target
    (ItemTurret.java:155-179).
  * Time.update() resets Time.delta from the wall clock, so a tight loop starves
    every delta-driven timer; set delta back to 1.0 afterwards.
  * heal the dummy every tick - and the turret too: a dagger kills a duo in
    ~600 ticks and the truncated sample reads as low dps.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

TILE = 8.0

BOX_JS = r"""
var GB = Packages.mindustry.gen.Groups.build;
var acc = [];
try{
  Vars.state.set(Packages.mindustry.core.GameState.State.playing);
  for(var i = 0; i < GB.size(); i++){
    var w = GB.index(i);
    if(w != null && w.block != null && ('' + w.block.name) == '%(block)s'){
      var b = w.block;
      acc.push(JSON.stringify({range: b.range, minRange: b.minRange,
        targetGround: b.targetGround, targetAir: b.targetAir,
        reload: b.reload, shots: b.shoot.shots, ammoCapacity: b.ammoCapacity}));
    }
  }
}catch(e){ acc.push('ERR ' + e); }
finally{ Vars.state.set(Packages.mindustry.core.GameState.State.paused); print(acc.join('\n')); }
"""

MEASURE_JS = r"""
var GB = Packages.mindustry.gen.Groups.build;
var GU = Packages.mindustry.gen.Groups.unit;
var GBU = Packages.mindustry.gen.Groups.bullet;
var GS = Packages.mindustry.core.GameState, ST = GS.State;
var acc = [];
try{
  Vars.state.set(ST.playing);
  Time.delta = 1.0;
  var tur = null, tgt = null;
  for(var i = 0; i < GB.size(); i++){
    var w = GB.index(i);
    if(w != null && w.block != null && ('' + w.block.name) == '%(block)s') tur = w;
  }
  for(var i = 0; i < GU.size(); i++){
    var u = GU.index(i);
    if(u != null && u.team == Packages.mindustry.game.Team.crux) tgt = u;
  }
  if(tur == null || tgt == null){ acc.push('ERR missing turret or target'); }
  else{
    var blk = tur.block;
    var item = Vars.content.item('%(ammo)s');
    var bt = item == null ? null : blk.ammoTypes.get(item);
    if(bt == null){ acc.push('ERR ' + blk.name + ' does not take %(ammo)s'); }
    else{
      for(var k = 0; k < tur.items.total(); k++) tur.handleItem(null, item);
      var maxHp = tgt.maxHealth, total = 0, firstHit = -1;
      for(var k = 0; k < %(ticks)d; k++){
        GBU.updatePhysics(); GU.updatePhysics();
        Vars.state.tick++; Time.update(); Time.delta = 1.0;
        var hp0 = tgt.health;
        var ba = []; for(var q = 0; q < GB.size(); q++) ba.push(GB.index(q));
        for(var q = 0; q < ba.length; q++){ var b = ba[q]; if(b != null && b.isValid()) b.update(); }
        var ua = []; for(var q = 0; q < GU.size(); q++) ua.push(GU.index(q));
        for(var q = 0; q < ua.length; q++){ var u = ua[q]; if(u != null && !u.dead) u.update(); }
        GBU.update(); GBU.collide();
        var d = hp0 - tgt.health;
        if(d > 0){ total += d; if(firstHit < 0) firstHit = k; }
        tgt.health = maxHp;
        if(tur.health < tur.maxHealth) tur.health = tur.maxHealth;
      }
      acc.push(JSON.stringify({block: blk.name, ammo: item.name, ticks: %(ticks)d,
        firstHit: firstHit, damage: Math.round(total*100)/100,
        dps: Math.round(total/(%(ticks)d/60)*100)/100,
        damagePerShot: bt.damage, splash: bt.splashDamage, pierce: bt.pierce,
        frag: bt.fragBullets, reload: blk.reload, shots: blk.shoot.shots}));
    }
  }
}catch(e){ acc.push('ERR ' + e); }
finally{ Vars.state.set(ST.paused); print(acc.join('\n')); }
"""


def panel_dps(shots, reload, damage):
    """The number every doc quotes: 60/reload * shots * damage."""
    if not reload:
        raise ValueError("reload must be positive")
    return round(60.0 / float(reload) * int(shots) * float(damage), 2)


def _parse(lines, keys):
    for ln in reversed(list(lines)):
        body = ln[ln.find("{"):] if "{" in ln else ""
        if not body:
            continue
        try:
            obj = json.loads(body)
        except ValueError:
            continue
        if keys & set(obj):
            return obj
    return None


def _server(size=96):
    import mlogsim
    import scenario
    env = scenario.environment()
    return mlogsim.Server(env["java"], env["jar"], world_size=size)


def _mount(srv, block, ammo, unit=None, at=None, stock=200, size=96):
    import scene as scenelib
    sc = {"name": "dps-%s" % block, "version": 1,
          "world": {"size": size, "rules": {"unitCap": 60}},
          "buildings": [{"block": block, "x": 30, "y": 40, "team": "sharded",
                         "items": {ammo: stock}}]}
    if unit:
        sc["units"] = [{"type": unit, "count": 1, "team": "crux", "at": at}]
    path = os.path.join(ROOT, "out", "_dps_%s.json" % block)
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(sc, indent=1))
    srv._scene = scenelib.load(path)
    srv.prepare()
    return path


def box(block, ammo="copper"):
    """Everything needed to place a legal target: range, blind spot, domain."""
    srv = _server()
    try:
        _mount(srv, block, ammo)
        srv.js(BOX_JS % {"block": block}, timeout=300)
        got = _parse(srv.all, {"range", "targetGround"})
        if not got:
            raise RuntimeError("could not read the box of %r; tail:\n%s"
                               % (block, "\n".join(srv.all[-8:])))
        return got
    finally:
        srv.close()


def pick_target(spec):
    """Ground vs air, and a distance that is inside range but outside minRange."""
    rng, mn = float(spec["range"]), float(spec.get("minRange") or 0)
    middle = max(mn + 3 * TILE, min(rng - 3 * TILE, (mn + rng) / 2.0))
    unit = "dagger" if spec.get("targetGround") else "flare"
    return unit, round(middle / TILE, 1)


def measure(block, ammo, *, ticks=1800, stock=200, unit=None, distance_tiles=None):
    spec = box(block, ammo)
    if unit is None or distance_tiles is None:
        u, d = pick_target(spec)
        unit = unit or u
        distance_tiles = distance_tiles if distance_tiles is not None else d
    srv = _server()
    try:
        _mount(srv, block, ammo, unit, [30 + distance_tiles, 40], stock)
        srv.js(MEASURE_JS % {"block": block, "ammo": ammo, "ticks": ticks}, timeout=600)
        got = _parse(srv.all, {"damage", "dps"})
        if not got:
            raise RuntimeError("could not measure %r/%r; tail:\n%s"
                               % (block, ammo, "\n".join(srv.all[-8:])))
        got.update({"unit": unit, "distanceTiles": distance_tiles,
                    "panel": panel_dps(got["shots"], got["reload"], got["damagePerShot"]),
                    "box": spec})
        got["ratio"] = round(got["dps"] / got["panel"], 3) if got["panel"] else None
        return got
    finally:
        srv.close()


def _selftest():
    checks = []
    checks.append(("panel duo", panel_dps(1, 20, 9) == 27.0))
    checks.append(("panel salvo", panel_dps(4, 29, 15) == 124.14))
    checks.append(("panel spectre", panel_dps(1, 7, 50) == 428.57))
    checks.append(("panel rounds", panel_dps(3, 35, 66) == 339.43))
    checks.append(("pick ground", pick_target(
        {"range": 160, "minRange": 0, "targetGround": True}) == ("dagger", 10.0)))
    checks.append(("pick air", pick_target(
        {"range": 220, "minRange": 0, "targetGround": False}) == ("flare", 13.8)))
    checks.append(("pick minRange", pick_target(
        {"range": 290, "minRange": 50, "targetGround": True}) == ("dagger", 21.2)))
    checks.append(("pick short range", pick_target(
        {"range": 40, "minRange": 0, "targetGround": True})[1] >= 2.0))
    try:
        panel_dps(1, 0, 9)
        checks.append(("zero reload refuses", False))
    except ValueError:
        checks.append(("zero reload refuses", True))
    bad = [n for n, ok in checks if not ok]
    for name, ok in checks:
        print("%-28s %s" % (name, "ok" if ok else "FAIL"))
    print("%d/%d checks passed" % (len(checks) - len(bad), len(checks)))
    return 1 if bad else 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print("usage: dps.py selftest | box <block> [ammo] | measure <block> <ammo>"
              " [--ticks N] [--unit flare|dagger] [--distance T]")
        return 0 if argv else 2
    cmd = argv.pop(0)
    if cmd == "selftest":
        return _selftest()
    if cmd == "box":
        print(json.dumps(box(argv[0], argv[1] if len(argv) > 1 else "copper"),
                         ensure_ascii=False, indent=1))
        return 0
    if cmd == "measure":
        opts = {"ticks": 1800, "unit": None, "distance_tiles": None}
        while argv:
            token = argv.pop(0)
            if token == "--ticks":
                opts["ticks"] = int(argv.pop(0))
            elif token == "--unit":
                opts["unit"] = argv.pop(0)
            elif token == "--distance":
                opts["distance_tiles"] = float(argv.pop(0))
            elif token.startswith("-"):
                raise SystemExit("unknown option %r" % token)
            else:
                argv.insert(0, token)
                break
        block = argv.pop(0)
        ammo = argv.pop(0) if argv else "copper"
        print(json.dumps(measure(block, ammo, **opts), ensure_ascii=False, indent=1))
        return 0
    raise SystemExit("unknown command %r" % cmd)


if __name__ == "__main__":
    sys.exit(main())
