"""Door registration and restoration with an explicit persistence file."""
import json
from world_protocol import coerce

DOOR_ACT_JS = r"""
/* 门的动作本体. 由 TapEvent 监听调用, 也供 door_enter 直接触发(没有玩家时也能测) */
/* 注意: 这里必须用隐式全局赋值, 不能写 var —— Java 侧每次 eval 是独立作用域,
   var 声明的名字出不了这次调用(实测 typeof _doorAct == 'undefined') */
_doorAct = function(pl, dx, dy){
  var d = _doors[dx + ',' + dy];
  if(d == null) return 'nodoor';
  /* 场景先铺: 即使没有玩家(合成点击/自测)也让世界变成"那个世界" */
  if(d.scene != null){
    try{ eval(_doorjs[dx + ',' + dy]); _doorerr = 'ok'; }catch(e7){ _doorerr = String(e7); }
  }
  /* 只有一种门: watch. 点一下 = 打开这扇门后面的仿真投影.
     开局投影本身(读 feed 文件)是 Python 侧的后台线程, 这里只留一个"被点了"的凭据,
     由 projection_director 取走 —— Java 侧不能回调 Python. */
  if(d.kind == 'watch'){
    _doorHits.push(dx + ',' + dy);
    return 'watch';
  }
  return 'noop';
};
"""


DOOR_SET_JS = r"""
var dk = %(kind)s, du = %(unit)s, dtx = %(tx)d, dty = %(ty)d, dl = %(label)s;
var dblk = %(block)s;
var t = Vars.world.tile(%(x)d, %(y)d);
if(t == null){ sb.append('ERR\ttile out of bounds'); }
else {
  if(dblk != null && dblk != ''){
    var blk = Vars.content.block(dblk);
    if(blk == null){ sb.append('ERR\tno such block ').append(dblk); }
    else { t.setNet(blk, Vars.state.rules.defaultTeam, 0); }
  }
  _doors[%(x)d + ',' + %(y)d] = {kind: dk, unit: du, tx: dtx, ty: dty, label: dl, scene: %(hasjs)s};
  _doorjs[%(x)d + ',' + %(y)d] = %(scenejs)s;
  if(sb.indexOf('ERR') < 0){ sb.append('OK\t').append(dk).append('\t').append(dtx + ',' + dty); }
}
"""


DOORS_JS = r"""
var nd = 0;
for(var k in _doors){
  if(!_doors.hasOwnProperty(k)) continue;
  var d = _doors[k];
  sb.append(k).append('\t').append(d.kind).append('\t').append(d.unit)
    .append('\t').append(d.tx + ',' + d.ty).append('\t').append(d.label).append('\n');
  nd++;
}
sb.append('COUNT\t').append(nd);
"""


DOOR_HITS_JS = r"""
/* 取走"刚被点过的门"列表(JSON 数组), 由 Python 的 projection_director 轮询 */
if(typeof _doorHits === 'undefined'){ sb.append('[]'); }
else { var a = _doorHits.splice(0, _doorHits.length); sb.append(JSON.stringify(a)); }
"""


DOOR_CLEAR_JS = r"""
var nc = 0;
for(var k in _doors){ if(_doors.hasOwnProperty(k)){ delete _doors[k]; nc++; } }
sb.append('CLEARED\t').append(nc);
"""


TAPS_JS = r"""
if(typeof _taplog === 'undefined'){ sb.append('NOSETUP\t0'); }
else {
  var tsince = %(since)d, tlim = %(limit)d, tn = 0;
  for(var ti=0;ti<_taplog.length;ti++){
    var tln = _taplog[ti];
    var tq = tln.split('\t');
    if(tq.length < 2) continue;
    if(parseInt(tq[1], 10) <= tsince) continue;
    sb.append(tln).append('\n');
    if(++tn >= tlim) break;
  }
  sb.append('SEQ\t').append(_tapseq);
}
"""


TAP_FIRE_JS = r"""
var fpl = null;
var fwant = %(who)s;
for(var fi=0;fi<Groups.player.size();fi++){
  var fc = Groups.player.index(fi);
  if(fwant == null || fwant == '' || String(fc.name).indexOf(fwant) >= 0){ fpl = fc; break; }
}
var ft = Vars.world.tile(%(x)d, %(y)d);
if(ft == null){ sb.append('ERR	tile out of bounds'); }
else {
  Packages.arc.Events.fire(new Packages.mindustry.game.EventType.TapEvent(fpl, ft));
  sb.append('FIRED	').append(%(x)d + ',' + %(y)d).append('	').append(fpl == null ? '-' : String(fpl.name));
}
"""


def door_register(w, x, y, kind="watch", unit="poly", tx=None, ty=None,
                  label=None, block="shock-mine", scene_path=None, persist=True,
                  scene_at=None, feed=None, *, doors_file):
    """登记一扇门: 放按钮方块 + 写 _doors 表 + (可选)编译场景 JS 塞进 _doorjs.

    scene_at 给了就按那一点为中心铺场景 (默认 = 门自己), 这样地雷就是圆心.
    """
    tx = x if tx is None else int(tx)
    ty = y if ty is None else int(ty)
    label = str(label or kind)
    scene_js = None
    shift = [0.0, 0.0]
    if scene_path:
        import scene as scene_mod
        sc = scene_mod.load(str(scene_path))
        want = scene_at or [int(x), int(y)]
        scene_js, _dx, _dy = scene_mod.world_js(sc, at=want)
        shift = [float(_dx), float(_dy)]
    out = w.js(DOOR_SET_JS % {"x": int(x), "y": int(y), "kind": json.dumps(str(kind)),
                              "unit": json.dumps(str(unit)), "tx": int(tx), "ty": int(ty),
                              "label": json.dumps(label),
                              "block": json.dumps(str(block)),
                              "hasjs": "null" if scene_js is None else "true",
                              "scenejs": "null" if scene_js is None else json.dumps(scene_js)})
    if not out:
        raise RuntimeError("no output")
    if out[0].startswith("ERR"):
        raise RuntimeError(out[0][4:])
    if persist:
        rows = []
        try:
            with open(doors_file, "r", encoding="utf-8") as fh:
                rows = json.load(fh)
        except Exception:
            rows = []
        key = "%d,%d" % (int(x), int(y))
        rows = [r0 for r0 in rows if "%s,%s" % (r0.get("x"), r0.get("y")) != key]
        rows.append({"x": int(x), "y": int(y), "kind": str(kind), "unit": str(unit),
                     "tx": int(tx), "ty": int(ty), "label": label,
                     "block": str(block), "scene": scene_path, "feed": feed,
                     "scene_at": (list(scene_at) if scene_at else None),
                     "shift": shift})
        with open(doors_file, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, ensure_ascii=False, indent=2)
    meta = {"kind": str(kind), "unit": str(unit), "block": str(block),
            "scene": scene_path, "feed": feed, "shift": shift,
            "scene_at": (list(scene_at) if scene_at else [int(x), int(y)])}
    if not hasattr(w, "_doors_meta"):
        w._doors_meta = {}
    w._doors_meta["%d,%d" % (int(x), int(y))] = meta
    return {"tile": "%d,%d" % (int(x), int(y)), "kind": str(kind),
            "unit": str(unit), "target": [int(tx), int(ty)], "label": label}


def door_reload(w, *, doors_file):
    """守护进程启动后把 doors.json 里的门重新登记一遍(场景 JSON 也会重新编译)."""
    try:
        with open(doors_file, "r", encoding="utf-8") as fh:
            rows = json.load(fh)
    except Exception:
        return 0
    n = 0
    for r0 in rows:
        try:
            door_register(w, r0["x"], r0["y"], r0.get("kind") or "possess",
                          r0.get("unit") or "poly", r0.get("tx"), r0.get("ty"),
                          r0.get("label"), r0.get("block") or "shock-mine",
                          r0.get("scene"), persist=False, doors_file=doors_file)
            n += 1
        except Exception as exc:
            print("[warn] 门 %s,%s 重装失败: %s" % (r0.get("x"), r0.get("y"), exc), flush=True)
    return n


DOOR_ENTER_JS = r"""
var dpl = null;
var dwant = %(who)s;
for(var di=0;di<Groups.player.size();di++){
  var dcand = Groups.player.index(di);
  if(dwant == null || dwant == '' || String(dcand.name).indexOf(dwant) >= 0){ dpl = dcand; break; }
}
if(dpl == null){ sb.append('NOPLAYER'); }
/* 先算结果再追加: _doorAct 会铺场景并往 sb 里写 B/I/L/U 行,
   链式 append 会让那些行插在 'R\t' 之后, 解析时拿到的是场景的第一行 */
else { var rres = String(_doorAct(dpl, %(x)d, %(y)d)); sb.append('R\t').append(rres); }
"""


OPERATIONS = frozenset(("door", "doors", "door_clear", "door_enter", "taps"))

def door_operation(w, req, *, audit, doors_file):
    op = (req.get("op") or "").strip()
    if op in ("door", "doors", "door_clear", "door_enter", "taps"):
        # 点击门：TapEvent 在任意方块上都会 fire（InputHandler.java:732-739），
        # 这里只登记「哪一格是哪扇门」，点下去的动作由 DOOR_ACT_JS 里的 _doorAct 做。
        if op == "taps":
            since = int(req.get("since") or 0)
            limit = int(req.get("limit") or 100)
            rows, seq = [], 0
            for ln in w.js(TAPS_JS % {"since": since, "limit": limit}):
                if ln.startswith("NOSETUP"):
                    return {"ok": False, "error": "event listeners not installed"}
                if ln.startswith("SEQ\t"):
                    seq = int(float(ln.split("\t")[1]))
                    continue
                q = ln.split("\t")
                if len(q) >= 5:
                    rows.append({"seq": int(float(q[0])), "tick": coerce(q[1]),
                                 "x": coerce(q[2]), "y": coerce(q[3]), "player": q[4]})
            return {"ok": True, "rows": rows, "count": len(rows), "nextSeq": seq}
        if op == "doors":
            rows = []
            for ln in w.js(DOORS_JS):
                if ln.startswith("COUNT\t"):
                    continue
                q = ln.split("\t")
                if len(q) >= 5:
                    rows.append({"tile": q[0], "kind": q[1], "unit": q[2],
                                 "target": q[3], "label": q[4]})
            return {"ok": True, "doors": rows, "count": len(rows)}
        if op == "door_clear":
            out = w.js(DOOR_CLEAR_JS)
            # 端掉的不仅是内存表: doors.json 不清会在下次重启时把旧门全"复活"
            try:
                with open(doors_file, "w", encoding="utf-8") as fh:
                    json.dump([], fh)
            except Exception:
                pass
            w._doors_meta = {}
            if out:
                return {"ok": True, "cleared": coerce(out[0].split("\t")[1])}
            return {"ok": False, "error": "no output"}
        x = int(req.get("x") or 0)
        y = int(req.get("y") or 0)
        if op == "door_enter":
            # 没有真人点击也能测: 直接替某个在线玩家执行一次门的动作
            who = req.get("who")
            out = w.js(DOOR_ENTER_JS % {"x": x, "y": y,
                                        "who": json.dumps(str(who) if who else None)})
            if not out:
                return {"ok": False, "error": "no output"}
            if out[0].startswith("NOPLAYER"):
                return {"ok": False, "error": "no player online"}
            line = next((ln for ln in out if ln.startswith("R\t")), out[-1])
            res = line.split("\t")[1] if "\t" in line else line
            audit("door_enter", x=x, y=y, result=res)
            return {"ok": True, "result": res}
        kind = str(req.get("kind") or "watch")
        unit = str(req.get("unit") or "poly")
        tx = int(req["tx"]) if req.get("tx") is not None else x
        ty = int(req["ty"]) if req.get("ty") is not None else y
        label = str(req.get("label") or kind)
        block = str(req.get("block") or "shock-mine")
        try:
            info = door_register(w, x, y, kind, unit, tx, ty, label, block,
                                 req.get("scene"), doors_file=doors_file)
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
        audit("door", x=x, y=y, kind=kind, unit=unit, tx=tx, ty=ty, label=label)
        res = {"ok": True}
        res.update(info)
        return res
    return NotImplemented
