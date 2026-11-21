"""World edit operations with explicit audit and file-directory dependencies."""
from world_protocol import coerce
from world_logic_edit import edit as edit_logic

OPERATIONS = frozenset(('place', 'clear', 'spawn', 'killunits', 'clearbuilds', 'logic_set', 'logic_rollback'))

PLACE_JS = r"""
var blk = Vars.content.block('%(block)s');
var t = Vars.world.tile(%(x)d, %(y)d);
if(blk == null){ sb.append('ERR\tno such block: %(block)s'); }
else if(t == null){ sb.append('ERR\ttile out of range'); }
else {
  try{
    t.setNet(blk, Vars.state.rules.defaultTeam, 0);
    var b = t.build;
    if(b != null){ b.enabled = true; }
    sb.append('OK\t'+blk.name+'\t'+%(x)d+'\t'+%(y)d);
  }catch(e){ sb.append('ERR\t'+e); }
}
"""


CLEAR_JS = r"""
var t = Vars.world.tile(%(x)d, %(y)d);
if(t == null){ sb.append('ERR\ttile out of range'); }
else { try{ t.setNet(Vars.content.block('air')); sb.append('OK'); }catch(e){ sb.append('ERR\t'+e); } }
"""


SPAWN_JS = r"""
var ty = Vars.content.unit('%(type)s');
if(ty == null){ sb.append('ERR\tno such unit type'); }
else {
  var team = null, TA = Packages.mindustry.game.Team.all;
  for(var i = 0; i < TA.length; i++){ if(TA[i].name == '%(team)s'){ team = TA[i]; break; } }
  if(team == null){ sb.append('ERR\tno such team'); }
  else {
    var cap = Vars.state.rules.unitCap, have = Packages.mindustry.gen.Groups.unit.size();
    var cx = %(cx)f * 8, cy = %(cy)f * 8, r = %(radius)f * 8, n = 0;
    for(var k = 0; k < %(count)d; k++){
      if(have + n >= cap){ sb.append('ERR\tunit cap reached'); break; }
      /* golden-angle spiral: 防止单位叠在同一个点互相挤开 */
      var ang = k * 2.39996323, rr = %(count)d <= 1 ? 0 : r * Math.sqrt(k / %(count)d);
      var u = ty.spawn(team, cx + Math.cos(ang) * rr, cy + Math.sin(ang) * rr);
      if(u == null){ sb.append('ERR\tspawn returned null'); break; }
      n++;
      sb.append('U\t').append(u.id).append('\t').append(u.type.name).append('\t').append(u.team.name)
        .append('\t').append(Math.round(u.x / 8)).append('\t').append(Math.round(u.y / 8)).append('\n');
    }
    sb.append('SPAWNED\t').append(n).append('\t').append(ty.name);
  }
}
"""


KILLUNITS_JS = r"""
var G = Packages.mindustry.gen.Groups.unit, n = 0, kept = 0, R = %(radius)f, CX = %(cx)f, CY = %(cy)f;
var TF = %(team)s;
for(var i = G.size() - 1; i >= 0; i--){
  var u = G.index(i); if(u == null) continue;
  if(%(keep_player)d == 1){
    var ctl = null; try{ ctl = u.controller(); }catch(e){}
    if(ctl instanceof Packages.mindustry.gen.Player){ kept++; continue; }
  }
  if(TF != null && u.team.name != TF){ kept++; continue; }
  if(R > 0){ var dx = u.x / 8 - CX, dy = u.y / 8 - CY; if(dx * dx + dy * dy > R * R){ kept++; continue; } }
  try{ u.kill(); n++; }catch(e){}
}
sb.append('KILLED\t').append(n).append('\t').append(kept);
"""


CLEARBUILDS_JS = r"""
var G = Packages.mindustry.gen.Groups.build, n = 0, kept = 0, R = %(radius)f, CX = %(cx)f, CY = %(cy)f;
var air = Vars.content.block('air');
for(var i = G.size() - 1; i >= 0; i--){
  var b = G.index(i); if(b == null) continue;
  if(%(keepcore)d == 1 && b.block instanceof Packages.mindustry.world.blocks.storage.CoreBlock){ kept++; continue; }
  if(R > 0){ var dx = b.x / 8 - CX, dy = b.y / 8 - CY; if(dx * dx + dy * dy > R * R){ kept++; continue; } }
  try{ b.tile.setNet(air); n++; }catch(e){}
}
sb.append('CLEARED\t').append(n).append('\t').append(kept);
"""


def edit(w, req, *, audit, data_dir):
    op = (req.get("op") or "").strip()
    if op == "place":
        blk = str(req.get("block") or "")
        if not blk:
            return {"ok": False, "error": "empty block"}
        audit("place", block=blk, x=req.get("x"), y=req.get("y"))
        out = w.js(PLACE_JS % {"block": blk, "x": int(req.get("x")), "y": int(req.get("y"))})
        if out and out[0].startswith("ERR"):
            return {"ok": False, "error": out[0][4:]}
        return {"ok": True, "block": blk, "x": int(req.get("x")), "y": int(req.get("y"))}
    if op == "clear":
        audit("clear", x=req.get("x"), y=req.get("y"))
        out = w.js(CLEAR_JS % {"x": int(req.get("x")), "y": int(req.get("y"))})
        if out and out[0].startswith("ERR"):
            return {"ok": False, "error": out[0][4:]}
        return {"ok": True, "x": int(req.get("x")), "y": int(req.get("y"))}
    if op == "spawn":
        ty = str(req.get("type") or "").strip()
        if not ty:
            return {"ok": False, "error": "empty type"}
        cnt = max(1, int(req.get("count") or 1))
        audit("spawn", type=ty, count=cnt, x=req.get("x"), y=req.get("y"))
        body = SPAWN_JS % {"type": ty, "team": str(req.get("team") or "sharded"),
                           "count": cnt, "cx": float(req.get("x") or 0),
                           "cy": float(req.get("y") or 0),
                           "radius": float(req.get("radius") or 3)}
        spawned, units = 0, []
        for ln in w.js(body):
            if ln.startswith("ERR"):
                return {"ok": False, "error": ln[4:].split("\t", 1)[-1], "spawned": spawned}
            parts = ln.split("\t")
            if parts[0] == "SPAWNED":
                spawned = int(coerce(parts[1]) or 0)
            elif parts[0] == "U":
                units.append({"id": coerce(parts[1]), "type": parts[2], "team": parts[3],
                              "x": coerce(parts[4]), "y": coerce(parts[5])})
        return {"ok": True, "spawned": spawned, "units": units, "count": len(units)}
    if op == "killunits":
        audit("killunits", team=req.get("team"))
        body = KILLUNITS_JS % {"keep_player": 0 if req.get("include_players") else 1,
                               "team": ("'%s'" % req.get("team")) if req.get("team") else "null",
                               "cx": float(req.get("x") or 0), "cy": float(req.get("y") or 0),
                               "radius": float(req.get("radius") or 0)}
        out = w.js(body)
        if out and out[0].startswith("ERR"):
            return {"ok": False, "error": out[0][4:]}
        parts = (out[0] if out else "").split("\t")
        return {"ok": True, "killed": coerce(parts[1]) if len(parts) > 1 else 0,
                "kept": coerce(parts[2]) if len(parts) > 2 else 0}
    if op == "clearbuilds":
        keepcore = 1 if req.get("keepcore", True) else 0
        audit("clearbuilds", keepcore=keepcore, radius=req.get("radius"))
        body = CLEARBUILDS_JS % {"keepcore": keepcore,
                                 "cx": float(req.get("x") or 0), "cy": float(req.get("y") or 0),
                                 "radius": float(req.get("radius") or 0)}
        out = w.js(body)
        if out and out[0].startswith("ERR"):
            return {"ok": False, "error": out[0][4:]}
        parts = (out[0] if out else "").split("\t")
        return {"ok": True, "cleared": coerce(parts[1]) if len(parts) > 1 else 0,
                "kept": coerce(parts[2]) if len(parts) > 2 else 0}
    if op in {"logic_set", "logic_rollback"}:
        return edit_logic(w, req, audit=audit, data_dir=data_dir)
    return NotImplemented
