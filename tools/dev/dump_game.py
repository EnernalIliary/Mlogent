"""Dump the game content tables from the real v160.7 executor -> data/game/*.json.

Reproducible from a clean checkout (given the jar/JRE, see MLOGSIM_JAR /
MLOGSIM_JAVA in tools/mlogsim.py):

    python tools/dev/dump_game.py

Every value is read off `Vars.content` inside Rhino -- nothing is parsed from
the Java sources and nothing is filled in with a default.  Fields that a class
simply does not have (e.g. `craftTime` exists only on GenericCrafter and its
subclasses) come back as JSON `null`, which is the honest answer for "this
block has no such field"; that is deliberately different from a fabricated
`0`/`-1` that looks like a real value.

Two executor details worth knowing before you touch the JS:

* `Server.js()` stops reading output at the first line containing the word
  `undefined` (that is the sentinel it waits for), so the scripts below print
  `~` for a missing/null value.  Never print the literal word.
* `bullet.maxRange` is only -1/unset on most bullets; the value the game
  itself uses is `bullet.range`, filled in by `BulletType.init()` from
  `calculateRange()` (drag-aware, and respects `maxRange` when it is set).
  Reading that is one field instead of re-deriving `lifetime * speed`.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import mlogsim as M  # noqa: E402

OUT = ROOT / "data" / "game"

ITEMS_JS = "(function(){var it=Vars.content.items();for(var i=0;i<it.size;i++){var x=it.get(i);print('IT|'+x.id+'|'+x.name+'|'+x.color);}})();"
LIQUIDS_JS = "(function(){var lt=Vars.content.liquids();for(var i=0;i<lt.size;i++){var x=lt.get(i);print('LQ|'+x.id+'|'+x.name+'|'+x.color);}})();"

# Columns after the tag, in order:
#   id|name|size|health|category|hasPower|requirements|consumers|outputs|
#   craftTime|itemCapacity|liquidCapacity|range|reload
#
# consumers: item:<name>:<amount> / liquid:<name>:<amount> / power:<usage>
# outputs  : item:<name>:<amount> (outputItems, else `results` for separators)
BLOCKS_JS = """(function(){
var N=function(v){return (v==null)?'~':(''+v);};
var bt=Vars.content.blocks();
for(var i=0;i<bt.size;i++){
 var b=bt.get(i);
 try{
  var req='';
  if(b.requirements!=null){for(var j=0;j<b.requirements.length;j++){var s=b.requirements[j];req+=(j?',':'')+s.item.name+':'+s.amount;}}
  var csum='';
  try{
   for(var k=0;k<b.consumers.length;k++){
    var c=b.consumers[k];
    if(c instanceof Packages.mindustry.world.consumers.ConsumeItems){
     for(var m=0;m<c.items.length;m++){var s2=c.items[m];csum+=(csum?',':'')+'item:'+s2.item.name+':'+s2.amount;}
    }else if(c instanceof Packages.mindustry.world.consumers.ConsumeLiquids){
     for(var n=0;n<c.liquids.length;n++){var s3=c.liquids[n];csum+=(csum?',':'')+'liquid:'+s3.liquid.name+':'+s3.amount;}
    }else if(c instanceof Packages.mindustry.world.consumers.ConsumePower){
     csum+=(csum?',':'')+'power:'+c.usage;
    }
   }
  }catch(e2){csum+='?';}
  var outp='';
  try{
   var oi=b.outputItems;
   if(oi==null){try{oi=b.results;}catch(e4){}}
   if(oi!=null){for(var p=0;p<oi.length;p++){var s4=oi[p];outp+=(p?',':'')+s4.item.name+':'+s4.amount;}}
  }catch(e3){}
  print('BL|'+b.id+'|'+b.name+'|'+b.size+'|'+b.health+'|'+b.category.name()+'|'+(b.hasPower?'1':'0')+'|'+req+'|'+csum+'|'+outp+'|'+N(b.craftTime)+'|'+N(b.itemCapacity)+'|'+N(b.liquidCapacity)+'|'+N(b.range)+'|'+N(b.reload));
 }catch(e){print('BLERR|'+i+'|'+e);}
}
})();"""

# weapons: name:damage:bulletSpeed:bulletRange:reload, ';'-separated
UNITS_JS = """(function(){
var N=function(v){return (v==null)?'~':(''+v);};
var ut=Vars.content.units();
for(var i=0;i<ut.size;i++){
 var u=ut.get(i);
 try{
  var w='';
  for(var j=0;j<u.weapons.size;j++){
   var q=u.weapons.get(j);
   w+=(j?';':'')+N(q.name)+':'+N(q.bullet.damage)+':'+N(q.bullet.speed)+':'+N(q.bullet.range)+':'+N(q.reload);
  }
  print('UN|'+u.id+'|'+u.name+'|'+u.health+'|'+u.armor+'|'+u.speed+'|'+(u.flying?'1':'0')+'|'+u.hitSize+'|'+u.maxRange+'|'+w);
 }catch(e){print('UNERR|'+i+'|'+e);}
}
})();"""


def run(srv, script: str, tag: str) -> list[str]:
    lines = srv.js(script)
    errors = [ln for ln in lines if ln.startswith(tag + "ERR")]
    if errors:
        raise SystemExit(f"{tag}: executor reported errors:\n" + "\n".join(errors[:10]))
    out = [ln for ln in lines if ln.startswith(tag)]
    print(f"{tag}: {len(out)} rows")
    return out


SCRIPT_OUT: dict[str, list[str]] = {}


def rows(tag: str, n: int) -> list[list[str]]:
    return [p for p in (r.split("|") for r in SCRIPT_OUT[tag]) if len(p) >= n]


def _missing(s: str) -> bool:
    """'~' = the executor has no such field/value (-> JSON null)."""
    return s == "~"


def num(s: str, where: str) -> float:
    if _missing(s):
        raise SystemExit(f"{where}: expected a number, executor returned ~ (missing)")
    return float(s)


def opt_num(s: str, where: str) -> float | None:
    return None if _missing(s) else float(s)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    srv = M.Server(M._default_java(), M._default_jar())
    try:
        SCRIPT_OUT["IT"] = run(srv, ITEMS_JS, "IT")
        SCRIPT_OUT["LQ"] = run(srv, LIQUIDS_JS, "LQ")
        SCRIPT_OUT["BL"] = run(srv, BLOCKS_JS, "BL")
        SCRIPT_OUT["UN"] = run(srv, UNITS_JS, "UN")
    finally:
        srv.close()

    def stack(s: str) -> dict:
        name, val = s.split(":")
        return {"name": name, "amount": float(val)}

    items = [{"id": int(i[1]), "name": i[2], "color": i[3]} for i in rows("IT", 4)]
    liquids = [{"id": int(i[1]), "name": i[2], "color": i[3]} for i in rows("LQ", 4)]

    blocks = []
    for b in rows("BL", 14):
        where = f"block {b[2]}"
        cons = []
        for s in b[8].split(","):
            if not s:
                continue
            bits = s.split(":")
            if bits[0] == "power":
                cons.append({"kind": "power", "name": "", "amount": float(bits[1])})
                continue
            cons.append({"kind": bits[0], "name": bits[1] if len(bits) > 1 else "",
                         "amount": float(bits[2]) if len(bits) > 2 else 0.0})
        blocks.append({
            "id": int(b[1]), "name": b[2], "size": int(b[3]), "health": int(b[4]),
            "category": b[5], "hasPower": b[6] == "1",
            "requirements": [stack(s) for s in b[7].split(",") if s],
            "consumers": cons,
            "outputs": [stack(s) for s in b[9].split(",") if s],
            # craftTime only exists on GenericCrafter & subclasses; null = no field
            "craftTime": opt_num(b[10], where),
            "itemCapacity": int(num(b[11], where)),
            "liquidCapacity": num(b[12], where),
            "range": opt_num(b[13], where),
            "reload": opt_num(b[14], where),
        })

    units = []
    for u in rows("UN", 10):
        weapons = []
        seen = set()
        for s in u[9].split(";"):
            if not s or s in seen:
                continue
            seen.add(s)
            bits = s.split(":")
            where = f"unit {u[2]} weapon {bits[0]}"
            weapons.append({"name": "" if _missing(bits[0]) else bits[0],
                            "damage": num(bits[1], where),
                            "bulletSpeed": num(bits[2], where),
                            "bulletRange": num(bits[3], where),
                            "reload": num(bits[4], where)})
        units.append({
            "id": int(u[1]), "name": u[2], "health": float(u[3]), "armor": float(u[4]),
            "speed": float(u[5]), "flying": u[6] == "1", "hitSize": float(u[7]),
            "maxRange": float(u[8]), "weapons": weapons,
        })

    for name, arr in (("items", items), ("liquids", liquids), ("blocks", blocks), ("units", units)):
        (OUT / f"{name}.json").write_text(json.dumps(arr, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"wrote {name}.json: {len(arr)}")
    (OUT / "meta.json").write_text(json.dumps(
        {"version": "v160.7", "counts": {"items": len(items), "liquids": len(liquids),
                                         "blocks": len(blocks), "units": len(units)}},
        ensure_ascii=False, indent=1), encoding="utf-8")
    crafted = sum(1 for b in blocks if b["craftTime"] is not None)
    print(f"craftTime: {crafted} blocks with a real value, "
          f"{len(blocks) - crafted} with no such field (null)")


if __name__ == "__main__":
    main()
