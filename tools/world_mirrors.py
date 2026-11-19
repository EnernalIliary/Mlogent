"""Per-world unit marker feeds, generation guards and mirror cleanup."""
from world_protocol import coerce
import base64
import json
import os
import threading
import time

MS_INSTALL_JS = r"""
/* 每块沙盘一份 marker 空间: 第 sl 号槽占 [6000+sl*400, +400) 的 id 段,
   互不覆盖. 之前所有投影共用 base=6000, 后开始的那块沙盘会把前面那块
   的图标原地改写 —— 看起来就是"marker 冲突". */
if(typeof _ms === 'undefined'){
  _ms = {slots: {}, size: 16, labels: true, span: 400};
  _msSlot = function(sl){
    var k = String(sl | 0);
    if(_ms.slots[k] == null){
      _ms.slots[k] = {base: 6000 + (sl | 0) * _ms.span, n: 0, ids: {}, txt: {}};
    }
    return _ms.slots[k];
  };
  _msCol = function(c){
    if(c == 1) return [0.35, 1, 1];    /* 逻辑控 = 青 */
    if(c == 2) return [1, 0.9, 0.45];  /* 玩家   = 黄 */
    return [1, 1, 1];                  /* 自由   = 白 */
  };
  _msIcon = function(mid, x, y, ty, w, tint, rot){
    var C = Packages.mindustry.gen.Call;
    var tm = new Packages.mindustry.game.MapObjectives$TextureMarker();
    tm.pos = new Packages.arc.math.geom.Vec2(x, y);
    tm.texture = new Packages.mindustry.game.MapObjectives$TextureHolder();
    /* 单位 rotation 0 指向 +x, 而精灵本身"朝上", 所以贴图要减 90 */
    tm.width = w; tm.height = w; tm.rotation = (rot == null ? 0 : rot - 90); tm.autoscale = false;
    if(tint != null) tm.color = new Packages.arc.graphics.Color(tint[0], tint[1], tint[2], 1);
    tm.world = 1; tm.minimap = -1; tm.light = -1;
    try{ C.removeMarker(mid); }catch(e0){}
    C.createMarker(mid, tm);
    /* 贴图值必须是内容对象(UnitType): 与 vanilla 的 setmarker texture 存的是同一类型;
       字符串也能显示, 但换兵种/换图标全靠这个对象 */
    var c = null; try{ c = Vars.content.unit(ty); }catch(e1){}
    C.updateMarkerTexture(mid, c == null ? ty : c);
  };
  _msText = function(tid, x, y, s, sz){
    var C = Packages.mindustry.gen.Call;
    var t = new Packages.mindustry.game.MapObjectives$TextMarker();
    t.pos = new Packages.arc.math.geom.Vec2(x, y); t.text = s; t.fontSize = sz;
    /* Align 是位掩码: center=1 top=2 bottom=4 left=8 right=16; 单位头顶那行居中 */
    t.flags = 0; t.textAlign = 1; t.lineAlign = 2;
    t.world = 1; t.minimap = -1; t.light = -1;
    try{ C.removeMarker(tid); }catch(e2){}
    C.createMarker(tid, t);
  };
  /* txt = JSON: [{"type":"poly","x":464,"y":544,"amount":30,"ctrl":1}, ...]
     x/y 是**世界坐标**; 想按格给就写 tx/ty, 这里乘 8 */
  _msApply = function(sl, txt){
    var C = Packages.mindustry.gen.Call;
    var LC = Packages.mindustry.logic.LMarkerControl;
    var S = _msSlot(sl);
    var arr = JSON.parse(String(txt));
    var n = arr.length;
    for(var i = 0; i < n; i++){
      var e = arr[i], ctrl = e.ctrl | 0, col = _msCol(ctrl);
      /* 坐标一律按格给(tiles). 注意两条通道量纲不同:
         createMarker 直接写 pos 字段 -> 世界单位;
         updateMarker(pos) 走 PosMarker.control -> 内部 *tilesize, 所以要给格 */
      var gx = (e.x != null ? e.x : e.tx), gy = (e.y != null ? e.y : e.ty);
      var x = gx * 8, y = gy * 8;
      var ty = String(e.type), mid = S.base + i * 2, tid = mid + 1;
      var prev = S.ids[i];
      var rot = (e.rot == null ? null : e.rot);
      if(prev == null || prev.ty != ty || prev.size != _ms.size || prev.ctrl != ctrl){
        _msIcon(mid, x, y, ty, _ms.size, col, rot);
        S.ids[i] = {ty: ty, size: _ms.size, ctrl: ctrl, rot: rot};
      }else{
        C.updateMarker(mid, LC.pos, gx, gy, 0);
        /* 朝向要在已有 marker 上改: rotation 走 control(), 单位是度, 不乘 tilesize */
        if(rot != null && prev.rot != rot){
          C.updateMarker(mid, LC.rotation, rot - 90, 0, 0);
          prev.rot = rot;
        }
      }
      if(_ms.labels){
        /* 头顶那行: 兵种 + 携带的物品名 + 数量, 例如 "poly copper x12" */
        var s = ty + (e.item ? (' ' + e.item) : '') + ((e.amount | 0) > 0 ? (' x' + (e.amount | 0)) : '');
        var pt = S.txt[i];
        if(pt == null || pt.s != s){ _msText(tid, x, y + 14, s, 1.1); S.txt[i] = {s: s}; }
        else{ C.updateMarker(tid, LC.pos, gx, gy + 1.75, 0); }
      }
    }
    for(var j = n; j < S.n; j++){
      try{ C.removeMarker(S.base + j * 2); }catch(e3){}
      try{ C.removeMarker(S.base + j * 2 + 1); }catch(e4){}
      delete S.ids[j]; delete S.txt[j];
    }
    S.n = n;
    return n;
  };
  sb.append('MSINSTALLED');
}else{
  /* 已经在跑: 兼容旧结构(没有 slots 的), 补上就行 */
  if(_ms.slots == null){ _ms.slots = {}; _ms.span = 400; }
  sb.append('MSALREADY');
}
"""


MS_APPLY_JS = r"""
var txt = new java.lang.String(Packages.java.util.Base64.getDecoder().decode('%(b64)s'), 'UTF-8');
sb.append(_msApply(%(slot)d, String(txt)));
"""


MS_CLEAR_JS = r"""
/* 清掉某个槽(或全部)的状态镜 marker(图标 + 头顶文字).
   按固定窗口扫, 不只按 n: 守护进程重启过 / 上一步崩在半路时,
   n 可能是 0 而屏幕上还留着上一次的图标(实测踩过).
   槽之间 id 段不重叠, 所以清一块沙盘不会碰别的沙盘. */
var C = Packages.mindustry.gen.Call;
var want = %(slot)s, gone = 0;
var ks = [];
if(want == null){ for(var k0 in _ms.slots){ if(_ms.slots.hasOwnProperty(k0)){ ks.push(k0); } } }
else { ks.push(String(want)); }
for(var ki = 0; ki < ks.length; ki++){
  var S2 = _ms.slots[ks[ki]];
  if(S2 == null){ continue; }
  var lim = (S2.n > 64 ? S2.n : 64);
  for(var i = 0; i < lim; i++){
    try{ C.removeMarker(S2.base + i * 2); gone++; }catch(e0){}
    try{ C.removeMarker(S2.base + i * 2 + 1); }catch(e1){}
  }
  S2.n = 0; S2.ids = {}; S2.txt = {};
  delete _ms.slots[ks[ki]];
}
sb.append(gone);
"""


def _mirror_slot(w, slot):
    """一块沙盘 = 一个槽: 自己的 feed / 偏移 / 代次 / marker id 段."""
    if not hasattr(w, "_mirrors"):
        w._mirrors = {}
    k = int(slot)
    st = w._mirrors.get(k)
    if st is None:
        st = {"feed": None, "off": (0.0, 0.0), "seq": 0, "thread": None}
        w._mirrors[k] = st
    return st


def mirror_push(w, units, dx=0.0, dy=0.0, gen=None, slot=0):
    """把一组 {type,x,y,amount,ctrl} 画成世界 marker（只画在 slot 自己的 id 段里）.

    dx/dy 是按格算的整体偏移: 仿真世界和真世界坐标系不同, 用它把图标挪到
    玩家当前看的地方 (1 格 = 8 wu).

    gen 是调用方看到的代次: 投影结束时 mirror_stop 会把该槽的 seq 加一,
    于是"清理前就已经在路上的那一帧"会被丢掉, 否则它会抢在清理之后把图标
    又画回来 (实测过: 拆雷后 marker 还剩 16 个).
    多块沙盘并行时各自用不同的 slot, marker id 段互不重叠 —— 不会互相覆盖.
    """
    st = _mirror_slot(w, slot)
    if gen is not None and gen != st.get("seq", 0):
        return {"ok": False, "error": "mirror stopped"}
    # units 里的 x/y 是格(tiles); 仿真侧就在 push 时除过 8 了
    if dx or dy:
        units = [dict(u, x=float(u.get("x", 0)) + dx, y=float(u.get("y", 0)) + dy)
                 if isinstance(u, dict) else u for u in units]
    txt = json.dumps(units, ensure_ascii=False)
    b64 = base64.b64encode(txt.encode("utf-8")).decode("ascii")
    out = w.js(MS_INSTALL_JS)
    if out and str(out[0]).startswith("ERR"):
        return {"ok": False, "error": str(out[0][4:])}
    if gen is not None and gen != st.get("seq", 0):
        return {"ok": False, "error": "mirror stopped"}
    res = w.js(MS_APPLY_JS % {"b64": b64, "slot": int(slot)})
    if not res:
        return {"ok": False, "error": "no output"}
    if str(res[0]).startswith("ERR"):
        return {"ok": False, "error": str(res[0][4:])}
    return {"ok": True, "count": int(float(res[0])) if str(res[0]).strip() else len(units)}


def mirror_watch(w, path, slot=0, dx=0.0, dy=0.0, cell=None):
    """后台线程: 盯着 push 文件, 内容一变就把整张表应用到世界（该槽的 id 段）.

    mlogsim --push 每 N tick 覆写这个文件; 服务端在这里读, 所以仿真进程
    不需要知道 apiPort/协议, 两边只靠一个文件解耦 (OneDrive 目录下也行).
    """
    st = _mirror_slot(w, slot)
    mirror_stop(w, slot)
    st["feed"] = str(path)
    st["off"] = (float(dx), float(dy))
    # cell = 这块沙盘的场景锚点(格心). feed 自己带 anchor(仿真场景锚点)时,
    # 偏移要用 "格心 - 仿真锚点" 现算: 仿真世界和真世界的原点并不一致.
    st["cell"] = (float(cell[0]), float(cell[1])) if cell else None
    my_gen = int(st.get("seq", 0))
    if int(slot) == 0:
        w.mirror_feed = str(path)
        w.mirror_off = st["off"]
    last = None

    def loop():
        nonlocal last
        # 该槽的 feed 被清空/换路径/代次变了, 线程自己退出
        while st.get("feed") == str(path) and st.get("seq", 0) == my_gen:
            time.sleep(0.12)
            try:
                fst = os.stat(path)
                stamp = (fst.st_mtime_ns, fst.st_size)
                if stamp == last:
                    continue
                last = stamp
                with open(path, "r", encoding="utf-8") as fh:
                    txt = fh.read().strip()
                if not txt:
                    continue
                # 写端是直接覆写, 抽到的可能是半截 JSON: 就地重试几次, 抽不到就等下一拍
                units = None
                for _try in range(4):
                    try:
                        units = json.loads(txt)
                        break
                    except ValueError:
                        time.sleep(0.02)
                        try:
                            with open(path, "r", encoding="utf-8") as fh:
                                txt = fh.read().strip()
                        except OSError:
                            break
                if units is None:
                    last = None
                    continue
                # 新格式是 {world:[w,h], units:[...]}: world 让沙盘画出仿真世界边界
                if isinstance(units, dict):
                    wsize = units.get("world")
                    st["world"] = list(wsize) if wsize else None
                    wanc = units.get("anchor")
                    st["feed_anchor"] = list(wanc) if wanc else None
                    units = units.get("units") or []
                dxs, dys = st.get("off", (0.0, 0.0))
                fa, cl = st.get("feed_anchor"), st.get("cell")
                if fa and cl:
                    # 仿真坐标以它自己场景的锚点为基准: 换到真世界要减掉它再加格心
                    dxs, dys = float(cl[0]) - float(fa[0]), float(cl[1]) - float(fa[1])
                r = mirror_push(w, units, dxs, dys, gen=my_gen, slot=slot)
                if not r.get("ok"):
                    print("[warn] 状态镜推送失败 (slot %d): %s" % (slot, r.get("error")),
                          flush=True)
                    last = None
            except FileNotFoundError:
                continue
            except Exception as exc:  # noqa: BLE001
                now = time.time()
                if now - getattr(w, "_mirror_warn_at", 0) > 30:
                    w._mirror_warn_at = now
                    print("[warn] 状态镜读取失败: %s" % exc, flush=True)
                last = None

    th = threading.Thread(target=loop, name="mirror-%d" % int(slot), daemon=True)
    st["thread"] = th
    th.start()


def mirror_stop(w, slot=None):
    """停掉盯文件的线程并清空该槽的 marker(含"已上路的那一帧").

    slot=None 表示全部(老接口 mirror_clear 用).
    """
    if slot is None:
        keys = sorted(getattr(w, "_mirrors", {}).keys())
    else:
        keys = [int(slot)]
    for k in keys:
        st = _mirror_slot(w, k)
        st["feed"] = None
        st["seq"] = int(st.get("seq", 0)) + 1
    if int(slot or 0) == 0 and slot is not None:
        w.mirror_feed = None
    n = 0
    for attempt in (0, 1):
        for k in keys:
            try:
                out = w.js(MS_CLEAR_JS % {"slot": int(k)})
                n += int(float(out[0])) if out else 0
            except Exception:  # noqa: BLE001 - 停线程比清屏重要
                pass
        if attempt == 0:
            time.sleep(0.2)   # 给"已经在半路的"那一帧落地时间, 再清一遍
    return n


MK_INSTALL_JS = r"""
/* 标记镜: 世界标记 (ObjectiveMarker) 由服务端直接下发, 客户端渲染.
   实测结论(2026-11-16, v160.7 真机):
   - Call.createMarker(int id, ObjectiveMarker) / removeMarker(int) /
     updateMarker(int id, LMarkerControl, double a, double b, double c) / updateMarkerTexture(int, Object)
   - 贴图版必须是 TextureMarker + Call.updateMarkerTexture(id, "<兵种>-full") —— 就是 mlog 的
     "makemarker texture 1 x y true" + "setmarker texture 1 0 @poly 0" 这两步; 先建空 marker 再填贴图.
     把 texture 直接塞进创建包会渲染成白模, 字符串 "poly" 也不行, 必须 "poly-full" 这个全尺寸精灵名.
   - width/height=0 表示用精灵原尺寸; world/minimap/light 是引擎自动分配的层号(不是布尔),
     传 1 会被改写成下一个空层号, 传 -1 表示该层不画.
   - 逐帧钩子只能 Events.run(Trigger.update, new java.lang.Runnable({...})).
   所有状态挂隐式全局 (var 出不了单次 js 调用). */
if(typeof _mk === 'undefined'){
  _mk = {on: false, div: 2, frame: 0, next: 2000, slots: {}, spr: {}, col: {}, tag: {}, txt: {},
         labels: true, size: 16, tint: true};
  _mkT = Packages.mindustry.game.MapObjectives$TextureMarker;
  _mkTH = Packages.mindustry.game.MapObjectives$TextureHolder;
  _mkV = Packages.arc.math.geom.Vec2;
  _mkC = Packages.arc.graphics.Color;
  _mkCall = Packages.mindustry.gen.Call;
  _mkLC = Packages.mindustry.logic.LMarkerControl;
  /* 单位贴图名: 就用纯兵种名. updateMarkerTexture 会把它解析成内容对象,
     客户端画的是该 UnitType 的 full icon; 写成 "<type>-full" 会变成缺图(ohno). */
  _mkSprite = function(u){ return String(u.type.name); };
  /* 新建一只单位的图标 marker: 先建空贴图 marker, 再 updateMarkerTexture 填精灵 */
  _mkIcon = function(mid, x, y, sprite, w, tint){
    var tm = new _mkT();
    tm.pos = new _mkV(x, y);
    tm.texture = new _mkTH();
    tm.width = (w == null ? 0 : w); tm.height = (w == null ? 0 : w);
    tm.rotation = 0; tm.autoscale = false;
    if(tint != null && _mk.tint){ tm.color = new _mkC(tint[0], tint[1], tint[2], 1); }
    tm.world = 1; tm.minimap = -1; tm.light = -1;
    _mkCall.createMarker(mid, tm);
    /* 贴图字段存"内容对象"(UnitType), 和 vanilla 的 setmarker @poly 存的是同一个类型;
       传字符串也能显示, 但内容对象是引擎原生路径, 换兵种/换图标都靠它 */
    var c = null; try{ c = Vars.content.unit(sprite); }catch(e0){}
    _mkCall.updateMarkerTexture(mid, c == null ? sprite : c);
  };
  _mkText = function(mid, x, y, text, size){
    var t = new Packages.mindustry.game.MapObjectives$TextMarker();
    t.pos = new _mkV(x, y);
    t.text = text; t.fontSize = (size == null ? 1.2 : size);
    t.flags = 0; t.textAlign = 0; t.lineAlign = 0;
    t.world = 1; t.minimap = -1; t.light = -1;
    _mkCall.createMarker(mid, t);
  };
  _mkUnitColor = function(ctrl){
    if(ctrl == 1) return [0.35, 1, 1];
    if(ctrl == 2) return [1, 0.9, 0.45];
    return [1, 1, 1];
  };
  _mkTick = function(){
    if(!_mk.on) return;
    if((_mk.frame++ % _mk.div) != 0) return;
    var seen = {}, arr = Packages.mindustry.gen.Groups.unit;
    for(var i=0;i<arr.size();i++){
      var u = arr.index(i);
      if(u == null || u.dead) continue;
      var uid = u.id; seen[uid] = 1;
      var ctrl = 0, c = u.controller();
      if(c != null){
        var cn = String(c.getClass().getName());
        if(cn.indexOf('Player') >= 0) ctrl = 2;
        else if(cn.indexOf('LogicAI') >= 0) ctrl = 1;
      }
      var amt = 0; try{ if(u.stack != null) amt = u.stack.amount; }catch(e1){}
      var spr = _mkSprite(u);
      var mid = _mk.slots[uid];
      if(mid == null){
        mid = _mk.next++; _mk.slots[uid] = mid; _mk.col[uid] = ctrl; _mk.spr[uid] = spr;
        _mkIcon(mid, u.x, u.y, spr, _mk.size, _mkUnitColor(ctrl));
      } else {
        _mkCall.updateMarker(mid, _mkLC.pos, u.x, u.y, 0);
        if(_mk.spr[uid] != spr){
          _mk.spr[uid] = spr;
          try{ _mkCall.updateMarkerTexture(mid, spr); }catch(e2){}
        }
        if(_mk.col[uid] != ctrl){
          _mk.col[uid] = ctrl;
          var cc = _mkUnitColor(ctrl);
          _mkCall.updateMarker(mid, _mkLC.color, cc[0], cc[1], cc[2]);
        }
      }
      if(_mk.labels){
        var tag = String(u.type.name) + (amt > 0 ? (' x' + amt) : '');
        var tid = _mk.tag[uid];
        if(tid == null || _mk.txt[uid] != tag){
          if(tid != null){ try{ _mkCall.removeMarker(tid); }catch(e3){} }
          tid = mid + 5000; _mk.tag[uid] = tid; _mk.txt[uid] = tag;
          _mkText(tid, u.x, u.y + 9, tag, 1.1);
        } else {
          _mkCall.updateMarker(tid, _mkLC.pos, u.x, u.y + 9, 0);
        }
      }
    }
    for(var k in _mk.slots){
      if(!_mk.slots.hasOwnProperty(k)) continue;
      if(seen[k] != 1){
        try{ _mkCall.removeMarker(_mk.slots[k]); }catch(e4){}
        if(_mk.tag[k] != null){ try{ _mkCall.removeMarker(_mk.tag[k]); }catch(e5){} }
        delete _mk.slots[k]; delete _mk.col[k]; delete _mk.spr[k];
        delete _mk.tag[k]; delete _mk.txt[k];
      }
    }
  };
  /* 钩子经一层间接, 以后热替换 _mkTick 不用重装监听 */
  Packages.arc.Events.run(Packages.mindustry.game.EventType$Trigger.update,
                          new java.lang.Runnable({run: function(){ _mkTick(); }}));
  sb.append('INSTALLED');
} else { sb.append('ALREADY'); }
"""


MK_STATE_JS = r"""
var lit = 0;
for(var k in _mk.slots){ if(_mk.slots.hasOwnProperty(k)) lit++; }
sb.append('on\t').append(_mk.on ? 1 : 0).append('\n');
sb.append('div\t').append(_mk.div).append('\n');
sb.append('units\t').append(Packages.mindustry.gen.Groups.unit.size()).append('\n');
sb.append('markers\t').append(lit).append('\n');
sb.append('worldMarkers\t').append(Vars.state.markers.worldMarkers.size);
"""


MK_ON_JS = r"""
_mk.on = %(on)s;
if(%(div)d > 0) _mk.div = %(div)d;
if(%(size)s > 0 && _mk.size != %(size)s){
  /* 尺寸变了: 已建 marker 没法改贴图大小, 直接清掉重建 */
  for(var k0 in _mk.slots){
    if(!_mk.slots.hasOwnProperty(k0)) continue;
    try{ Packages.mindustry.gen.Call.removeMarker(_mk.slots[k0]); }catch(e6){}
    if(_mk.tag[k0] != null){ try{ Packages.mindustry.gen.Call.removeMarker(_mk.tag[k0]); }catch(e7){} }
    delete _mk.slots[k0]; delete _mk.col[k0]; delete _mk.spr[k0];
    delete _mk.tag[k0]; delete _mk.txt[k0];
  }
  _mk.size = %(size)s;
}
if('%(labels)s' != 'null') _mk.labels = %(labels)s;
if('%(tint)s' != 'null') _mk.tint = %(tint)s;
var lit = 0;
for(var k in _mk.slots){ if(_mk.slots.hasOwnProperty(k)) lit++; }
sb.append('on\t').append(_mk.on ? 1 : 0).append('\n').append('markers\t').append(lit);
sb.append('\n').append('size\t').append(_mk.size).append('\n').append('labels\t').append(_mk.labels ? 1 : 0)
  .append('\n').append('tint\t').append(_mk.tint ? 1 : 0);
"""


MK_CLEAR_JS = r"""
var nc = 0;
for(var k in _mk.slots){
  if(!_mk.slots.hasOwnProperty(k)) continue;
  try{ Packages.mindustry.gen.Call.removeMarker(_mk.slots[k]); }catch(e2){}
  delete _mk.slots[k]; delete _mk.col[k]; nc++;
}
_mk.on = false;
sb.append('CLEARED\t').append(nc);
"""


MK_ADD_JS = r"""
var kind = %(kind)s, mx = %(x)f, my = %(y)f, mid = %(id)d;
var mm = Vars.state.markers;
var had = mm.has(mid);
if(had){ try{ Packages.mindustry.gen.Call.removeMarker(mid); }catch(e0){} }
if(kind == 'text'){
  var tm = new Packages.mindustry.game.MapObjectives$TextMarker();
  tm.pos = new Packages.arc.math.geom.Vec2(mx, my);
  tm.text = %(text)s;
  tm.fontSize = %(size)f;
  tm.flags = 0; tm.textAlign = 0; tm.lineAlign = 0;
  tm.world = 1; tm.minimap = 1; tm.light = -1;
  Packages.mindustry.gen.Call.createMarker(mid, tm);
} else if(kind == 'shape'){
  var sm = new Packages.mindustry.game.MapObjectives$ShapeMarker();
  sm.pos = new Packages.arc.math.geom.Vec2(mx, my);
  sm.color = new Packages.arc.graphics.Color(%(r)f, %(g)f, %(b)f, 1);
  sm.radius = %(radius)f; sm.stroke = %(stroke)f;
  sm.rotation = 0; sm.startAngle = 0; sm.endAngle = 360;
  sm.fill = false; sm.outline = true; sm.sides = 4;
  sm.world = 1; sm.minimap = 1; sm.light = -1;
  Packages.mindustry.gen.Call.createMarker(mid, sm);
} else {
  _mkPoint(mid, mx, my, %(r)f, %(g)f, %(b)f, %(radius)f, 1);
}
sb.append('OK\t').append(mid).append('\t').append(mm.worldMarkers.size);
"""


MK_LIST_JS = r"""
var mm = Vars.state.markers;
sb.append('WORLD\t').append(mm.worldMarkers.size).append('\n');
sb.append('MINIMAP\t').append(mm.mapMarkers.size).append('\n');
sb.append('LIGHT\t').append(mm.lightMarkers.size).append('\n');
var lit = 0;
for(var k in _mk.slots){ if(_mk.slots.hasOwnProperty(k)) lit++; }
sb.append('MIRROR\t').append(lit);
"""


CONTROL_OPERATIONS = frozenset(("mirror_state", "mirror_feed", "mirror_clear", "mirror", "marker", "markers", "marker_clear"))

def control(w, req, *, root, audit):
    op = (req.get("op") or "").strip()
    if op in ("mirror_state", "mirror_feed", "mirror_clear"):
        # 状态镜: 坐标由调用方给(mlogsim 仿真 / 脚本), 不读 Groups.unit
        if op == "mirror_feed":
            path = str(req.get("path") or "")
            if not path:
                return {"ok": False, "error": "need path"}
            if not os.path.isabs(path):
                path = os.path.join(root, path)
            slot = int(req.get("slot") or 0)
            dx = float(req.get("dx") or 0)
            dy = float(req.get("dy") or 0)
            mirror_watch(w, path.replace("\\", "/"), slot=slot, dx=dx, dy=dy)
            audit("mirror_feed", path=path)
            return {"ok": True, "path": path, "slot": slot, "dx": dx, "dy": dy}
        if op == "mirror_clear":
            cleared = mirror_stop(w)
            audit("mirror_clear")
            return {"ok": True, "cleared": cleared}
        units = req.get("units")
        if units is None:
            fpath = str(req.get("file") or "")
            if not fpath:
                return {"ok": False, "error": "need units or file"}
            if not os.path.isabs(fpath):
                fpath = os.path.join(root, fpath)
            with open(fpath, "r", encoding="utf-8") as fh:
                units = json.load(fh)
        r = mirror_push(w, units, float(req.get("dx") or 0), float(req.get("dy") or 0))
        audit("mirror_state", count=len(units))
        return r
    if op in ("mirror", "marker", "markers", "marker_clear"):
        # 标记镜: 世界标记(ObjectiveMarker)是服务端可下发的, 客户端直接画在世界上
        # —— 不占方块、不用显示屏、不依赖逐帧位置包(Call 里根本没有那种包).
        inst = w.js(MK_INSTALL_JS)
        if inst and inst[0].startswith("ERR"):
            return {"ok": False, "error": inst[0][4:]}
        if op == "markers":
            res = {}
            for ln in w.js(MK_LIST_JS):
                k, _, v = ln.partition("\t")
                res[k.lower()] = coerce(v)
            return {"ok": True, **res}
        if op == "marker_clear":
            for ln in w.js(MK_CLEAR_JS):
                return {"ok": True, "cleared": coerce(ln.split("\t")[1])}
            return {"ok": False, "error": "no output"}
        if op == "marker":
            kind = str(req.get("kind") or "point")
            x = float(req.get("x") or 0) * 8.0
            y = float(req.get("y") or 0) * 8.0
            mid = int(req.get("id") or 9001)
            body = MK_ADD_JS % {"kind": json.dumps(kind), "x": x, "y": y, "id": mid,
                                "text": json.dumps(str(req.get("text") or "")),
                                "size": float(req.get("size") or 2.0),
                                "r": float(req.get("r") or 1.0), "g": float(req.get("g") or 0.9),
                                "b": float(req.get("b") or 0.3),
                                "radius": float(req.get("radius") or 6.0),
                                "stroke": float(req.get("stroke") or 2.0)}
            out = w.js(body)
            if not out:
                return {"ok": False, "error": "no output"}
            if out[0].startswith("ERR"):
                return {"ok": False, "error": out[0][4:]}
            audit("marker", kind=kind, x=x / 8.0, y=y / 8.0, id=mid)
            return {"ok": True, "id": mid, "kind": kind}
        on = str(req.get("on") or req.get("state") or "on").lower() in ("1", "on", "true", "start", "yes")
        div = int(req.get("div") or 2)
        size = float(req.get("size") or 0)
        def _tri(v):
            if v is None or str(v) == "":
                return "null"
            return "true" if str(v).lower() in ("1", "true", "on", "yes") else "false"
        res = {}
        for ln in w.js(MK_ON_JS % {"on": "true" if on else "false", "div": div, "size": size,
                                   "labels": _tri(req.get("labels")), "tint": _tri(req.get("tint"))}):
            k, _, v = ln.partition("\t")
            res[k] = coerce(v)
        audit("mirror", on=on, div=div, size=size)
        return {"ok": True, "on": on, **res}
    return NotImplemented
