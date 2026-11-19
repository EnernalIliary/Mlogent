"""Schematic placement, export and listing with explicit directory and audit."""
import json
import os
from world_protocol import coerce

OPERATIONS = frozenset(('schematic', 'schematic_save', 'schematics'))

SCHEMATIC_PLACE_JS = r"""
var S = Packages.mindustry.game.Schematics;
var bytes = null, src = %(src)s;
try{
  if(src != null && src.indexOf('b64:') == 0){
    bytes = java.util.Base64.getDecoder().decode(src.substring(4));
  }else{
    bytes = java.nio.file.Files.readAllBytes(java.nio.file.Paths.get(String(src)));
  }
}catch(e){ sb.append('ERR\tread: '+e+'\n'); }
if(bytes != null){
  var sch = null;
  try{ sch = S.read(new java.io.ByteArrayInputStream(bytes)); }
  catch(e){ sb.append('ERR\tparse: '+e+'\n'); }
  if(sch != null){
    var team = Vars.state.rules.defaultTeam, TN = %(team)s;
    if(TN != null){
      var TA = Packages.mindustry.game.Team.all;
      for(var q=0;q<TA.length;q++){ if(TA[q].name == TN){ team = TA[q]; break; } }
    }
    var ox = %(ox)s, oy = %(oy)s;
    if(ox < 0){ ox = Math.floor((Vars.world.width() - sch.width) / 2); }
    if(oy < 0){ oy = Math.floor((Vars.world.height() - sch.height) / 2); }
    var placed = 0, cfgs = 0, logic = 0, skipped = 0, failed = 0, cleared = 0, keptc = 0;
    var LB = Packages.mindustry.world.blocks.logic.LogicBlock;
    var AIR = Vars.content.block('air');
    /* 先清出目标矩形，避免旧建筑与蓝图重叠导致 setBlock 互相拆 */
    for(var cx = 0; cx < sch.width; cx++){
      for(var cy = 0; cy < sch.height; cy++){
        var ct = Vars.world.tile(ox + cx, oy + cy);
        if(ct == null || ct.build == null) continue;
        /* 核心永不拆（拆了单位就没地方回货，玩家也会立刻发现） */
        var cb = ct.build;
        if(cb.block instanceof Packages.mindustry.world.blocks.storage.CoreBlock){ keptc++; continue; }
        try{ ct.setNet(AIR); cleared++; }catch(e){}
      }
    }
    /* 两遍：先放普通方块，再放处理器 —— readCompressed 通过 world.build(x,y) 解析链接，
       链接目标必须已经存在，否则链接变 null。 */
    for(var pass = 0; pass < 2; pass++){
      for(var i = 0; i < sch.tiles.size; i++){
        var st = sch.tiles.get(i);
        var isLogic = false;
        try{ isLogic = (st.block instanceof LB); }catch(e){ isLogic = false; }
        if((pass == 0) == isLogic) continue;
        var tx = ox + st.x, ty = oy + st.y;
        var t = Vars.world.tile(tx, ty);
        if(t == null){ skipped++; continue; }
        var bn = t.build;
        if(bn != null && (bn.tile.x != tx || bn.tile.y != ty)){ skipped++; continue; }
        try{
          t.setNet(st.block, team, st.rotation);
          var b = t.build;
          if(b == null){ skipped++; continue; }
          b.enabled = true;
          placed++;
          if(isLogic){ logic++; }
          if(st.config != null){
            if(isLogic){
              b.readCompressed(st.config, true); cfgs++;
            }else{
              var cons = b.block.configurations.get(st.config.getClass());
              if(cons != null){ cons.get(b, st.config); cfgs++; }
              else { b.configureAny(st.config); cfgs++; }
            }
          }
        }catch(e){ failed++; sb.append('ERR\tplace '+tx+','+ty+': '+e+'\n'); }
      }
    }
    var nm = '-'; try{ nm = String(sch.tags.get('name')); }catch(e){}
    sb.append('OK\tplaced='+placed+'\tlogic='+logic+'\tcfg='+cfgs+'\tskipped='+skipped+'\tfailed='+failed+'\tcleared='+cleared+'\tkeptcore='+keptc+'\tw='+sch.width+'\th='+sch.height+'\tx='+ox+'\ty='+oy+'\tname='+nm+'\n');
    sb.append('TILES\t'+sch.tiles.size+'\n');
  }
}
"""


SCHEMATIC_SAVE_JS = r"""
var seq = new Packages.arc.struct.Seq();
var x0 = %(x)d, y0 = %(y)d, w = %(w)d, h = %(h)d, n = 0;
for(var dx = 0; dx < w; dx++){
  for(var dy = 0; dy < h; dy++){
    var t = Vars.world.tile(x0 + dx, y0 + dy);
    if(t == null || t.build == null) continue;
    var b = t.build;
    if(b.block == null || b.block.name == 'air') continue;
    if(b.tile.x != x0 + dx || b.tile.y != y0 + dy) continue;   /* 多格建筑只在原点存一份 */
    var cfg = null; try{ cfg = b.config(); }catch(e){ cfg = null; }
    var rot = 0; try{ rot = b.rotation; }catch(e){ rot = 0; }
    seq.add(new Packages.mindustry.game.Schematic$Stile(b.block, dx, dy, cfg, rot));
    n++;
  }
}
var tags = new Packages.arc.struct.StringMap();
tags.put('name', %(name)s);
tags.put('author', %(author)s);
var sch = new Packages.mindustry.game.Schematic(seq, tags, %(w)d, %(h)d);
var out = null;
try{
  out = new java.io.FileOutputStream(%(path)s);
  Packages.mindustry.game.Schematics.write(sch, out);
  sb.append('OK\t'+n+'\t'+%(path)s+'\n');
}catch(e){ sb.append('ERR\twrite: '+e+'\n'); }
finally{ try{ if(out != null) out.close(); }catch(e2){} }
"""


SCHEMATIC_LIST_JS = r"""
var all = Vars.schematics == null ? null : Vars.schematics.all();
if(all == null || all.size == 0){
  var dir = new java.io.File(%(dir)s);
  var fs = dir.listFiles();
  if(fs != null){
    for(var i=0;i<fs.length;i++){
      var fn = String(fs[i].getName());
      if(fn.length > 5 && fn.substring(fn.length-5) == '.msch'){
        sb.append(fn.substring(0, fn.length-5)).append('\t').append(fs[i].length).append('\tfile\n');
      }
    }
  }
}else{
  for(var i=0;i<all.size;i++){
    var s = all.get(i);
    var nm='-', au='-';
    try{ nm = String(s.tags.get('name')); }catch(e){}
    try{ au = String(s.tags.get('author')); }catch(e){}
    sb.append(nm).append('\t').append(s.width).append('x').append(s.height).append('\t').append(au).append('\n');
  }
}
"""


def schematic(w, req, *, audit, schematic_dir):
    op = (req.get("op") or "").strip()
    if op == "schematic":
        src = req.get("src") or req.get("path") or ""
        if not src and req.get("b64"):
            src = "b64:" + str(req.get("b64")).strip()
        if not src:
            return {"ok": False, "error": "need src (path or b64)"}
        if not src.startswith("b64:") and not os.path.exists(src):
            # 裸名字: 先在 schematics 目录里找 <name>.msch / <name>
            for cand in (os.path.join(schematic_dir, src), os.path.join(schematic_dir, src + ".msch")):
                if os.path.exists(cand):
                    src = cand
                    break
        if not src.startswith("b64:"):
            src = os.path.abspath(src).replace("\\", "/")
        x = int(req["x"]) if req.get("x") is not None else -1
        y = int(req["y"]) if req.get("y") is not None else -1
        team = req.get("team")
        audit("schematic", src=str(src)[:120], x=x, y=y)
        body = SCHEMATIC_PLACE_JS % {"src": json.dumps(str(src)), "ox": x, "oy": y,
                                     "team": json.dumps(team)}
        rows, ok_line, tiles = [], None, 0
        for ln in w.js(body, timeout=120):
            if ln.startswith("ERR"):
                return {"ok": False, "error": ln[4:]}
            if ln.startswith("OK\t"):
                ok_line = ln
            elif ln.startswith("TILES\t"):
                tiles = int(coerce(ln.split("\t")[1]) or 0)
        if not ok_line:
            return {"ok": False, "error": "no result from schematic placement"}
        kv = {}
        for part in ok_line.split("\t")[1:]:
            k, _, v = part.partition("=")
            kv[k] = coerce(v) if v != "" else None
        kv["tiles"] = tiles
        return {"ok": True, **kv}
    if op == "schematic_save":
        x, y = int(req.get("x")), int(req.get("y"))
        ww = int(req.get("w") or 0)
        hh = int(req.get("h") or 0)
        name = str(req.get("name") or "schem").strip()
        if ww <= 0 or hh <= 0:
            return {"ok": False, "error": "need w,h"}
        if ww > 128 or hh > 128:
            return {"ok": False, "error": "schematic max 128x128"}
        safe = "".join(c for c in name if c not in '\\/:*?"<>|').strip() or "schem"
        target = os.path.join(schematic_dir, safe + ".msch")
        audit("schematic_save", x=x, y=y, w=ww, h=hh, name=safe)
        body = SCHEMATIC_SAVE_JS % {"x": x, "y": y, "w": ww, "h": hh,
                                    "name": json.dumps(name),
                                    "author": json.dumps("DeepSeek"),
                                    "path": json.dumps(target.replace("\\", "/"))}
        out = w.js(body, timeout=120)
        if out and out[0].startswith("ERR"):
            return {"ok": False, "error": out[0][4:]}
        parts = (out[0] if out else "").split("\t")
        # 让服务端内存里的蓝图表也能看到（客户端列表走磁盘，不依赖这个）
        try:
            w.js("try{ Vars.schematics.load(); sb.append('RELOADED'); }catch(e){ sb.append('ERR '+e); }")
        except Exception:
            pass
        return {"ok": True, "path": target, "tiles": coerce(parts[1]) if len(parts) > 1 else 0,
                "name": safe,
                "bytes": os.path.getsize(target) if os.path.exists(target) else None}
    if op == "schematics":
        rows = []
        for ln in w.js(SCHEMATIC_LIST_JS % {"dir": json.dumps(schematic_dir.replace("\\", "/"))}):
            if ln.startswith("ERR"):
                return {"ok": False, "error": ln[4:]}
            p = ln.split("\t")
            if len(p) >= 3:
                rows.append({"name": p[0], "size": p[1], "author": p[2]})
        return {"ok": True, "items": rows, "count": len(rows)}
    return NotImplemented
