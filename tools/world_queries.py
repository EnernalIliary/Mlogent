"""Read-only world queries with explicit process and data-directory inputs."""
import json
import base64
import os
import time
from world_protocol import coerce, parse_tsv, units_table
from world_logic_edit import batch_preview, read as read_logic, snapshot as read_snapshot

OPERATIONS = frozenset(('', 'ping', 'status', 'maps', 'players', 'units', 'unit', 'buildings', 'building', 'logic', 'logic_code', 'logic_graph', 'logic_batch_preview', 'logic_snapshot', 'logic_vars'))

STATUS_JS = r"""
var put=function(k,v){ sb.append(k).append('=').append(v).append('\n'); };
put('map', Vars.state.map.name());
put('mode', Vars.state.rules.mode().name());
put('wave', Vars.state.wave);
put('tick', Vars.state.tick);
put('w', Vars.world.width());
put('h', Vars.world.height());
put('players', Packages.mindustry.gen.Groups.player.size());
put('units', Packages.mindustry.gen.Groups.unit.size());
put('builds', Packages.mindustry.gen.Groups.build.size());
try{ put('paused', Vars.state.isPaused()?1:0); }catch(e){ put('paused', '?'); }
try{ put('infinite', Vars.state.rules.infiniteResources?1:0); }catch(e){ put('infinite', '?'); }
try{ put('waveIn', Math.round(Vars.state.wavetime/60)); }catch(e){ put('waveIn', '?'); }
"""


PLAYERS_JS = r"""
var G=Packages.mindustry.gen.Groups.player;
for(var i=0;i<G.size();i++){
  var p=G.index(i); if(p==null) continue;
  sb.append(p.name).append('\t').append(p.team.name).append('\t')
    .append(Math.round(p.x/8)).append('\t').append(Math.round(p.y/8)).append('\t')
    .append(p.admin?'1':'0').append('\n');
}
"""


UNITS_JS = r"""
var G=Packages.mindustry.gen.Groups.unit, n=0, lim=%(limit)d, R=%(R)f, CX=%(CX)f, CY=%(CY)f;
var TF=%(team)s, YF=%(type)s;
for(var i=0;i<G.size();i++){
  var u=G.index(i); if(u==null||!u.isValid()) continue;
  if(TF!=null && u.team.name!=TF) continue;
  if(YF!=null && u.type.name!=YF) continue;
  if(R>0){ var dx=u.x/8-CX, dy=u.y/8-CY; if(dx*dx+dy*dy>R*R) continue; }
  var ctl='-'; try{ var c=u.controller(); if(c!=null) ctl=c.getClass().getSimpleName(); }catch(e){ ctl='?'; }
  var dead='?'; try{ dead = u.dead?1:0; }catch(e){ try{ dead = u.dead()?1:0; }catch(e2){} }
  var item='-', carry=-1, capu=-1, elev=-1, ctlTick=-1, flag=0, ctrl=-1, mine=0, boost=0;
  try{ item = u.stack.item==null ? '-' : u.stack.item.name; carry = u.stack.amount; }catch(e){}
  try{ capu = u.type.itemCapacity; }catch(e){}
  try{ elev = Math.round(u.elevation*100)/100; }catch(e){}
  try{ var cc = u.controller(); if(cc instanceof Packages.mindustry.ai.types.LogicAI) ctlTick = cc.controlTimer; }catch(e){}
  try{ flag = u.flag; }catch(e){}
  try{ ctrl = u.sense(Packages.mindustry.logic.LAccess.controlled); }catch(e){}
  try{ mine = u.mineTile==null ? 0 : 1; }catch(e){}
  try{ boost = (u.type.canBoost && u.elevation > 0.09) ? 1 : 0; }catch(e){}
  sb.append(u.id).append('\t').append(u.type.name).append('\t').append(u.team.name).append('\t')
    .append(Math.round(u.x/8)).append('\t').append(Math.round(u.y/8)).append('\t')
    .append(Math.round(u.health)).append('\t').append(Math.round(u.type.health)).append('\t')
    .append(dead).append('\t').append(ctl).append('\t')
    .append(item).append('\t').append(carry).append('\t').append(capu).append('\t')
    .append(elev).append('\t').append(ctlTick).append('\t')
    .append(flag).append('\t').append(ctrl).append('\t').append(mine).append('\t').append(boost).append('\n');
  if(++n>=lim) break;
}
if(n>=lim) sb.append('TRUNC\t').append(lim).append('\n');
"""


UNIT_JS = r"""
var u = Packages.mindustry.gen.Groups.unit.getByID(%(id)d);
if(u==null || !u.isValid()){ sb.append('ERR\tno unit id %(id)d'); }
else {
  var put=function(k,v){ sb.append(k).append('=').append(v).append('\n'); };
  put('id', u.id); put('type', u.type.name); put('team', u.team.name);
  put('tx', Math.round(u.x/8)); put('ty', Math.round(u.y/8));
  put('wx', Math.round(u.x*10)/10); put('wy', Math.round(u.y*10)/10);
  put('health', Math.round(u.health)); put('maxHealth', Math.round(u.type.health));
  put('dead', u.dead?1:0);
  try{ var c=u.controller(); put('controller', c==null?'-':c.getClass().getSimpleName()); }catch(e){ put('controller','?'); }
  try{ put('flag', u.flag); }catch(e){ put('flag','?'); }
  try{ put('controlled', u.sense(Packages.mindustry.logic.LAccess.controlled)); }catch(e){ put('controlled','?'); }
  try{ put('item', u.stack.item==null?'-':u.stack.item.name); put('carry', u.stack.amount); }catch(e){}
  try{ put('itemCapacity', u.type.itemCapacity); }catch(e){}
  try{ put('elevation', Math.round(u.elevation*100)/100); }catch(e){}
  try{ put('boosting', (u.type.canBoost && u.elevation>0.09)?1:0); }catch(e){}
  try{ put('mining', u.mineTile==null?0:1); if(u.mineTile!=null){ put('mineTile', u.mineTile.x+','+u.mineTile.y); } }catch(e){}
  try{ put('shooting', u.isShooting?1:0); }catch(e){}
  try{ put('speed', Math.round(u.speed()*100)/100); }catch(e){}
  try{ var cc=u.controller(); if(cc instanceof Packages.mindustry.ai.types.LogicAI){ put('controlTimer', cc.controlTimer); } }catch(e){}
  try{ put('rangeTiles', Math.round(u.range()/8*10)/10); }catch(e){}
}
"""


MAPS_JS = r"""
var ms = Vars.maps.all();
for(var i=0;i<ms.size;i++){
  var m=ms.get(i);
  var f='-'; try{ f = m.file==null ? '-' : String(m.file.name()); }catch(e){}
  sb.append(m.name()).append('\t').append(f).append('\n');
}
"""


BUILDS_JS = r"""
var n=0, lim=%(limit)d, R=%(R)f, CX=%(CX)f, CY=%(CY)f;
var TF=%(team)s, BF=%(block)s;
var w=Vars.world, W=w.width(), H=w.height();
var x0=0, y0=0, x1=W-1, y1=H-1;
if(R>0){
  x0=Math.max(0, Math.floor(CX-R)); x1=Math.min(W-1, Math.ceil(CX+R));
  y0=Math.max(0, Math.floor(CY-R)); y1=Math.min(H-1, Math.ceil(CY+R));
}
outer:
for(var ty=y0; ty<=y1; ty++){
  for(var tx=x0; tx<=x1; tx++){
    var t=w.tile(tx,ty); var b = t==null ? null : t.build;
    if(b==null || !b.isValid()) continue;
    /* 多格建筑在每格都会命中, 只在它自己的原点格报一次 */
    if(b.tile.x!=tx || b.tile.y!=ty) continue;
    if(TF!=null && b.team.name!=TF) continue;
    if(BF!=null && b.block.name!=BF) continue;
    var tot=-1, cap=-1;
    try{ if(b.items!=null){ tot=b.items.total(); } }catch(e){}
    /* v160 的 itemCapacity 在 Block 上, ItemModule 已经没有 capacity 字段/方法 */
    try{ cap = b.block.itemCapacity; }catch(e){}
    sb.append(b.block.name).append('\t').append(b.team.name).append('\t')
      .append(b.tile.x).append('\t').append(b.tile.y).append('\t')
      .append(Math.round(b.health)).append('\t').append(tot).append('\t').append(cap).append('\n');
    if(++n>=lim) break outer;
  }
}
if(n>=lim) sb.append('TRUNC\t').append(lim).append('\n');
"""


BUILDING_AT_JS = r"""
var t=Vars.world.tile(%(x)d, %(y)d);
var b = t==null ? null : t.build;
if(b!=null && b.isValid()){
  var tot=-1, cap=-1;
  try{ if(b.items!=null){ tot=b.items.total(); } }catch(e){}
  try{ cap = b.block.itemCapacity; }catch(e){}
  sb.append(b.block.name).append('\t').append(b.team.name).append('\t')
    .append(b.tile.x).append('\t').append(b.tile.y).append('\t')
    .append(Math.round(b.health)).append('\t').append(tot).append('\t').append(cap).append('\n');
}
"""


LOGIC_LIST_JS = r"""
var n=0, lim=%(limit)d, R=%(R)f, CX=%(CX)f, CY=%(CY)f;
var w=Vars.world, W=w.width(), H=w.height();
var x0=0, y0=0, x1=W-1, y1=H-1;
if(R>0){
  x0=Math.max(0, Math.floor(CX-R)); x1=Math.min(W-1, Math.ceil(CX+R));
  y0=Math.max(0, Math.floor(CY-R)); y1=Math.min(H-1, Math.ceil(CY+R));
}
outer:
for(var ty=y0; ty<=y1; ty++){
  for(var tx=x0; tx<=x1; tx++){
    var t=w.tile(tx,ty); var b = t==null ? null : t.build;
    if(b==null || !b.isValid()) continue;
    if(b.getClass().getName().indexOf('LogicBlock$')<0) continue;
    var cl=0, vn=0;
    try{ cl = b.code==null ? 0 : b.code.length; }catch(e){}
    try{ vn = b.executor.vars.length; }catch(e){}
    sb.append(b.tile.x).append('\t').append(b.tile.y).append('\t')
      .append(b.block.name).append('\t').append(cl).append('\t').append(vn).append('\n');
    if(++n>=lim) break outer;
  }
}
if(n>=lim) sb.append('TRUNC\t').append(lim).append('\n');
"""


LOGIC_VARS_JS = r"""
var t=Vars.world.tile(%(x)d, %(y)d);
var b = t==null ? null : t.build;
if(b==null){ sb.append('ERR\tno building at %(x)d,%(y)d'); }
else if(b.getClass().getName().indexOf('LogicBlock$')<0){ sb.append('ERR\tnot a logic block: '+b.block.name); }
else {
  var V=b.executor.vars;
  for(var k=0;k<V.length;k++){
    var v=V[k], s='';
    try{ s = v.isobj ? String(v.objval) : String(v.numval); }catch(e){ s='?'; }
    sb.append(v.name).append('\t').append(s).append('\n');
  }
}
"""


LOGIC_GRAPH_JS = r"""
var world=Vars.world, result=[], seen=Object.create(null);
var cx=%(cx)d, cy=%(cy)d, radius=%(radius)d, limit=%(limit)d;
function digest(text){
  var bytes=new java.lang.String(String(text)).getBytes(java.nio.charset.StandardCharsets.UTF_8);
  var hash=java.security.MessageDigest.getInstance("SHA-256").digest(bytes);
  return String(java.util.HexFormat.of().formatHex(hash));
}
function targetOf(link){
  var t=world.build(link.x,link.y);
  return t==null ? null : {x:t.tileX(),y:t.tileY(),block:String(t.block.name),team:String(t.team.name),
    processor:t.getClass().getName().indexOf('LogicBlock$')>=0};
}
for(var y=0;y<world.height();y++) for(var x=0;x<world.width();x++){
  var b=world.build(x,y);
  if(b==null || !b.isValid() || b.getClass().getName().indexOf('LogicBlock$')<0) continue;
  var bx=b.tileX(), by=b.tileY(), key=bx+','+by;
  if(seen[key] || (radius>0 && (bx-cx)*(bx-cx)+(by-cy)*(by-cy)>radius*radius)) continue;
  seen[key]=true;
  var code=String(b.code||''), links=[], targets=[];
  for(var i=0;i<b.links.size;i++){ var l=b.links.get(i), target=targetOf(l); links.push({name:String(l.name),x:l.x,y:l.y,valid:l.valid,target:target}); if(target!=null && target.processor) targets.push(target.x+','+target.y); }
  var linksHash=digest(JSON.stringify(links)), sourceHash=digest(code);
  result.push({x:bx,y:by,block:String(b.block.name),codeLen:code.length,ipt:b.ipt,
    source_sha256:sourceHash,links_sha256:linksHash,
    revision:digest(bx+','+by+':'+sourceHash+':'+linksHash),links:links,processor_targets:targets});
  if(result.length>=limit) break;
}
var payload=java.util.Base64.getEncoder().encodeToString(new java.lang.String(JSON.stringify({processors:result,total:result.length>=limit?result.length+1:result.length})).getBytes("UTF-8"));
sb.append('LOGIC_GRAPH\t').append(payload);
"""


def query(w, req, *, data_dir):
    op = (req.get("op") or "").strip()
    if op in ("ping", ""):
        return {"ok": True, "pid": os.getpid(), "java": w.proc.pid if w.proc else None,
                "hosted": getattr(w, "hosted", False), "map": w.map_name,
                "gamePort": w.game_port, "uptime": round(time.time() - w.started, 1),
                "dataDir": data_dir}
    if op == "status":
        raw = {}
        for ln in w.js(STATUS_JS):
            k, _, v = ln.partition("=")
            raw[k] = v
        def num(k, cast=int, default=None):
            try:
                return cast(float(raw[k]))
            except Exception:
                return default

        def flag(k):
            try:
                return float(raw[k]) != 0
            except Exception:
                return False
        d = {
            "map": raw.get("map"),
            "mode": raw.get("mode"),
            "wave": num("wave", int),
            "waveIn": num("waveIn", int),
            "tick": num("tick", int),
            "width": num("w", int),
            "height": num("h", int),
            "players": num("players", int, 0),
            "units": num("units", int, 0),
            "buildings": num("builds", int, 0),
            # Rhino 把 ?1:0 打印成 "1.0"，字符串比较永远不等 —— 按数值判
            "paused": flag("paused"),
            "infiniteResources": flag("infinite"),
            "gamePort": w.game_port,
            "uptime": round(time.time() - w.started, 1),
            "dataDir": data_dir,
        }
        return {"ok": True, **d}
    if op == "maps":
        rows = []
        for ln in w.js(MAPS_JS):
            name, _, f = ln.partition("\t")
            rows.append({"name": name, "file": f})
        return {"ok": True, "maps": rows, "count": len(rows)}
    if op == "players":
        return {"ok": True, **parse_tsv(w.js(PLAYERS_JS), ["name", "team", "x", "y", "admin"])}
    if op == "units":
        body = UNITS_JS % {"limit": int(req.get("limit") or 200),
                           "R": float(req.get("radius") or 0),
                           "CX": float(req.get("x") or 0), "CY": float(req.get("y") or 0),
                           "team": json.dumps(req.get("team")),
                           "type": json.dumps(req.get("type"))}
        res = {"ok": True, **parse_tsv(w.js(body), ["id", "type", "team", "x", "y",
                                                  "health", "maxHealth", "dead", "controller",
                                                  "item", "carry", "itemCapacity",
                                                  "elevation", "controlTimer",
                                                  "flag", "controlled", "mining", "boosting"])}
        if str(req.get("format") or "").lower() == "table":
            res["table"] = units_table(res["rows"])
        return res
    if op == "unit":
        uid = int(req.get("id"))
        raw = {}
        for ln in w.js(UNIT_JS % {"id": uid}):
            if ln.startswith("ERR"):
                return {"ok": False, "error": ln[4:]}
            k, _, v = ln.partition("=")
            raw[k] = v
        return {"ok": True, **{k: coerce(v) for k, v in raw.items()}}
    if op == "buildings":
        body = BUILDS_JS % {"limit": int(req.get("limit") or 200),
                            "R": float(req.get("radius") or 0),
                            "CX": float(req.get("x") or 0), "CY": float(req.get("y") or 0),
                            "team": json.dumps(req.get("team")),
                            "block": json.dumps(req.get("block"))}
        return {"ok": True, **parse_tsv(w.js(body), ["block", "team", "x", "y",
                                                    "health", "items", "capacity"])}
    if op == "building":
        x, y = int(req.get("x")), int(req.get("y"))
        out = w.js(BUILDING_AT_JS % {"x": x, "y": y})
        rows = parse_tsv(out, ["block", "team", "x", "y", "health", "items", "capacity"])
        if not rows["rows"]:
            return {"ok": True, "block": None, "x": x, "y": y, "found": False}
        return {"ok": True, "found": True, **rows["rows"][0],
                "origin": {"x": rows["rows"][0]["x"], "y": rows["rows"][0]["y"]}}
    if op == "logic":
        body = LOGIC_LIST_JS % {"limit": int(req.get("limit") or 40),
                                "R": float(req.get("radius") or 0),
                                "CX": float(req.get("x") or 0), "CY": float(req.get("y") or 0)}
        return {"ok": True, **parse_tsv(w.js(body), ["x", "y", "block", "codeLen", "vars"])}
    if op == "logic_code":
        return read_logic(w, req)
    if op == "logic_graph":
        limit = int(req.get("limit") or 256)
        radius = int(req.get("radius") or 0)
        cx, cy = int(req.get("x") or 0), int(req.get("y") or 0)
        if not 1 <= limit <= 1024 or not 0 <= radius <= 32767:
            raise ValueError("logic_graph limit must be 1..1024 and radius 0..32767")
        if not 0 <= cx <= 32767 or not 0 <= cy <= 32767:
            raise ValueError("logic_graph x and y must be in 0..32767")
        rows = w.js(LOGIC_GRAPH_JS % {"cx": cx, "cy": cy, "radius": radius, "limit": limit})
        row = next((line for line in rows if line.startswith("LOGIC_GRAPH\t")), None)
        if row is None:
            raise RuntimeError("game did not return a processor graph")
        return {"ok": True, **json.loads(base64.b64decode(row.split("\t", 1)[1], validate=True))}
    if op == "logic_batch_preview":
        return batch_preview(w, req, data_dir=data_dir)
    if op == "logic_snapshot":
        return read_snapshot(data_dir, req.get("snapshot_id"))
    if op == "logic_vars":
        x, y = int(req.get("x")), int(req.get("y"))
        rows = []
        for ln in w.js(LOGIC_VARS_JS % {"x": x, "y": y}):
            if ln.startswith("ERR"):
                return {"ok": False, "error": ln[4:]}
            name, _, val = ln.partition("\t")
            rows.append({"name": name, "value": coerce(val)})
        return {"ok": True, "x": x, "y": y, "vars": rows, "count": len(rows)}
    return NotImplemented
