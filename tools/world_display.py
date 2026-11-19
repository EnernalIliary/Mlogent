"""Projection panels and boundary markers, with per-world state and paths."""
import json
import os
import time
from world_scenes import feed_units
from world_projection_actions import _projs

SB_INSTALL_JS = r"""
/* 每块沙盘一块"文本日志板": 在格子左上角列几行 TextMarker.
   内容由 Python 侧每轮轮询重写(标题 / feed 新鲜度 / 投影状态 / 建筑数 / 单位数 /
   最近几条事件), 所以世界里能直接看到调用日志, 不用切回聊天栏.
   id 段是 [5000, 6000), 与状态镜的 6000 段、边界框的 7000 段都不重叠. */
if(typeof _sb === 'undefined'){
  _sb = {next: 5000, span: 8, slots: {}};
  /* 上一进程画的板子还留在客户端: 先擦掉, 免得对齐方式/行距改了还显示老样式 */
  for(var _sk = 5000; _sk < 6000; _sk++){ try{ Packages.mindustry.gen.Call.removeMarker(_sk); }catch(_se){} }
  _sbSlot = function(sl){
    var k = String(sl | 0);
    if(_sb.slots[k] == null){ _sb.slots[k] = {base: 5000 + (sl | 0) * _sb.span}; }
    return _sb.slots[k];
  };
  _sbLine = function(sl, i, gx, gy, s, sz){
    var C = Packages.mindustry.gen.Call;
    var LC = Packages.mindustry.logic.LMarkerControl;
    var S = _sbSlot(sl), id = S.base + i, m = null;
    try{ m = Vars.state.markers.get(id); }catch(e0){}
    if(m == null){
      var t = new Packages.mindustry.game.MapObjectives$TextMarker();
      t.pos = new Packages.arc.math.geom.Vec2(gx * 8, gy * 8);
      /* Align 位掩码: left=8, top=2 —— 面板每行从锚点往右写、往下排 */
      t.text = s; t.fontSize = sz; t.flags = 0; t.textAlign = 8; t.lineAlign = 2;
      t.world = 1; t.minimap = -1; t.light = -1;
      C.createMarker(id, t);
    }else{
      /* 已有 marker: pos 走 control() 是格; 文字只能走 updateMarkerText
         (LMarkerControl 里没有 text, 改文字用 flushText) */
      C.updateMarker(id, LC.pos, gx, gy, 0);
      C.updateMarker(id, LC.fontSize, sz, 0, 0);
      C.updateMarkerText(id, LC.flushText, true, s);
    }
  };
  _sbSet = function(sl, gx, gy, txt, sz){
    var arr = JSON.parse(String(txt)), i;
    for(i = 0; i < arr.length && i < 8; i++){
      _sbLine(sl, i, gx, gy - i * 0.95, String(arr[i]), sz);
    }
    var S = _sbSlot(sl);
    for(i = arr.length; i < 8; i++){
      try{ Packages.mindustry.gen.Call.removeMarker(S.base + i); }catch(e1){}
    }
    return arr.length;
  };
  /* 从文件读面板文本再刷: 控制台的 js 行会把参数里的字符串字面量弄坏,
     所以文本一律走文件(DATA/sb<slot>.txt = java cwd), 只传数字. */
  _sbSetF = function(sl, gx, gy, sz){
    var p = Packages.java.nio.file.Path.of('sb' + (sl | 0) + '.txt');
    var t = String(Packages.java.nio.file.Files.readString(p));
    return _sbSet(sl, gx, gy, t, sz);
  };
  sb.append('SBINSTALLED');
}else{
  sb.append('SBALREADY');
}
"""


SB_SET_JS = r"""
sb.append(_sbSetF(%(slot)d, %(gx)f, %(gy)f, %(sz)f));
"""


SB_SWEEP_JS = r"""
/* 重启后 _sb 是空的, 客户端屏幕上还留着上次进程画的日志板 -> 先把整段清掉 */
var C = Packages.mindustry.gen.Call, gone = 0;
for(var i = 5000; i < 6000; i++){ try{ C.removeMarker(i); gone++; }catch(e0){} }
_sb = {next: 5000, span: 8, slots: {}};
sb.append(gone);
"""


FRAME_PAINT_JS = r"""
/* 用一批小方块 ShapeMarker 沿矩形边画虚线框。不用真地板: 换地板会盖掉玩家
   自己的染色地板, 而且看起来"没有仿真也有东西"。
   注意量纲: ShapeMarker.radius 是**世界单位**(Lines.poly 直接吃), 而
   PointMarker.radius 是**格**(内部 *tilesize, 而且还带 1.67 s 扩散动画)。 */
if(typeof _fr === 'undefined'){ _fr = {next: 7000, keys: {}}; }
var fx = %(x)d, fy = %(y)d, fw = %(w)d, fh = %(h)d, fk = %(key)s;
var step = %(step)d; if(step < 1){ step = 1; }
var rad = %(radius)s;
var C = Packages.mindustry.gen.Call;
var old = _fr.keys[fk];
if(old != null){
  for(var oi = 0; oi < old.length; oi++){ try{ C.removeMarker(old[oi]); }catch(e0){} }
}
var pts = [], seen = {};
var addp = function(px, py){
  var k2 = px + ',' + py;
  if(seen[k2] != null) return;
  seen[k2] = 1; pts.push([px, py]);
};
for(var ix = 0; ix < fw; ix += step){ addp(fx + ix, fy); addp(fx + ix, fy + fh - 1); }
for(var iy = 0; iy < fh; iy += step){ addp(fx, fy + iy); addp(fx + fw - 1, fy + iy); }
addp(fx + fw - 1, fy); addp(fx, fy + fh - 1); addp(fx + fw - 1, fy + fh - 1);
var ids = [];
for(var pi = 0; pi < pts.length; pi++){
  var mid = _fr.next + pi;
  var pm = new Packages.mindustry.game.MapObjectives$ShapeMarker();
  pm.pos = new Packages.arc.math.geom.Vec2(pts[pi][0] * 8 + 4, pts[pi][1] * 8 + 4);
  pm.radius = rad; pm.sides = 4; pm.rotation = 45; pm.fill = true; pm.outline = false;
  pm.stroke = 1; pm.color = new Packages.arc.graphics.Color(%(r)s, %(g)s, %(b)s, 1);
  pm.world = 1; pm.minimap = -1; pm.light = -1;
  try{ C.removeMarker(mid); }catch(e1){}
  C.createMarker(mid, pm);
  ids.push(mid);
}
_fr.next += pts.length + 4;
_fr.keys[fk] = ids;
sb.append('FRAME	').append(fk).append('	').append(ids.length);
"""


FRAME_CLEAR_JS = r"""
/* 擦掉边界 marker(只 removeMarker, 不碰地板). key 为空时清掉全部. */
if(typeof _fr === 'undefined'){ _fr = {next: 7000, keys: {}}; }
var C = Packages.mindustry.gen.Call;
var want = %(key)s, n = 0;
for(var k in _fr.keys){
  if(!_fr.keys.hasOwnProperty(k)){ continue; }
  if(want != null && want != '' && k != want){ continue; }
  var ids2 = _fr.keys[k];
  for(var i2 = 0; i2 < ids2.length; i2++){ try{ C.removeMarker(ids2[i2]); n++; }catch(e2){} }
  delete _fr.keys[k];
}
sb.append('FRAMECLEAR	').append(n);
"""


FRAME_SWEEP_JS = r"""
/* 守护进程重启后 _fr 是空的, 但客户端屏幕上还留着上次画的框:
  按固定 id 段扫一遍(7000..7999), 保证起来时是干净的. */
var C = Packages.mindustry.gen.Call;
var n3 = 0;
for(var sid = 7000; sid < 8000; sid++){ try{ C.removeMarker(sid); n3++; }catch(e3){} }
_fr = {next: 7000, keys: {}};
sb.append('SWEEP	').append(n3);
"""


FRAME_LIST_JS = r"""
if(typeof _fr === 'undefined'){ _fr = {next: 7000, keys: {}}; }
var out2 = [];
for(var k3 in _fr.keys){
  if(_fr.keys.hasOwnProperty(k3)){ out2.push(k3 + ':' + _fr.keys[k3].length); }
}
sb.append(out2.join(' | '));
"""


FRAME_COLOR = (1.0, 0.82, 0.35)


LIVE_COLOR = (0.35, 0.95, 0.95)


FRAME_LIVE_MAX = 10.0


SB_BASE = 5000


SB_SPAN = 8            # 每块沙盘占 8 个 id


SB_MAX_LINES = 8


SB_FONT = 0.9


SB_EVENTS = 3          # 面板上留几行事件


def _sb_store(w):
    st = getattr(w, "_sb_log", None)
    if st is None:
        st = {}
        w._sb_log = st
    return st


def sb_event(w, slot, msg, keep=SB_EVENTS):
    """往某块沙盘的日志板尾追加一行(ASCII, 中文在逻辑字体里画不出来)."""
    slot = int(slot)
    rows = _sb_store(w).setdefault(slot, [])
    rows.append("%s %s" % (time.strftime("%H:%M:%S"), str(msg)))
    del rows[:-keep]
    return rows


def _sb_write(w, slot, text):
    """把面板文本写到 java 进程 cwd 里(控制台 js 行传不了字符串字面量)."""
    path = os.path.join(w.data_dir, "sb%d.txt" % int(slot))
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    return path


def sb_lines(w, slot, d=None, age=None, live=False):
    """一块沙盘面板的完整文本行(第一行在最上面)."""
    slot = int(slot)
    d = d or {}
    p = _projs(w).get(slot)
    stem = os.path.splitext(os.path.basename(d.get("path") or "scene"))[0]
    out = ["#%d %s" % (slot + 1, stem)]
    if age is None:
        out.append("feed --   (mlogsim --push)")
    else:
        out.append("feed %.1fs %s" % (age, "live" if live else "idle"))
    out.append(("proj ON  bld %d" % len(p.get("builds") or [])) if p else "proj --")
    out.append("units %d" % feed_units(d.get("feed")))
    fr = d.get("frame")
    if fr:
        out.append("frame %d,%d %dx%d" % (int(fr[0]), int(fr[1]), int(fr[2]), int(fr[3])))
    rows = _sb_store(w).get(slot) or []
    room = SB_MAX_LINES - len(out)
    if room > 0 and rows:
        out.extend(rows[-room:])
    return out[:SB_MAX_LINES]


def sb_render(w, slot, d=None, age=None, live=False, force=False):
    """把面板刷到世界里; 文本没变就不发 js(每 0.5 s 一轮, 省往返)."""
    slot = int(slot)
    lines = sb_lines(w, slot, d=d, age=age, live=live)
    key = "\n".join(lines)
    cache = getattr(w, "_sb_cache", None)
    if cache is None:
        cache = {}
        w._sb_cache = cache
    if not force and cache.get(slot) == key:
        return 0
    cell = (d or {}).get("cell")
    if cell:
        gx = float(cell[0]) + 2.0
        gy = float(cell[1]) + 3.0
    else:
        bw, bh = getattr(w, "base", (0, 0))
        gx, gy = float(bw), float(bh)
    # _sbSet 里 JSON.parse 的是一行一个元素的数组, 不能直接喂纯文本
    _sb_write(w, slot, json.dumps(lines, ensure_ascii=False))
    w.js(SB_SET_JS % {"slot": slot, "gx": gx, "gy": gy, "sz": SB_FONT})
    cache[slot] = key
    return len(lines)


def sb_clear(w, slot=None):
    """擦掉一块(或全部)日志板."""
    ks = [int(slot)] if slot is not None else sorted(_sb_store(w).keys())
    for k in ks:
        try:
            _sb_write(w, k, "[]")
            w.js(SB_SET_JS % {"slot": k, "gx": 0.0, "gy": 0.0, "sz": SB_FONT})
        except Exception:  # noqa: BLE001
            pass
        _sb_store(w).pop(k, None)
        getattr(w, "_sb_cache", {}).pop(k, None)
    return len(ks)


def frame_paint(wd_, rect, key, step=1, radius=7.0, color=None):
    """给一个场景的矩形边界画一圈 marker(点). rect 是世界格 [x, y, w, h].

    只画 marker, 不动地形: 之前用 metal-floor 铺了一圈真地板, 会盖掉玩家自己
    刷的染色地板, 而且看起来"没有仿真也有东西".

    注意参数名不能叫 w —— 解包 rect 时会把 w 覆盖成整数, 于是 w.js 崩成
    "'int' object has no attribute 'js'".
    """
    fx, fy, fw, fh = [int(v) for v in rect[:4]]
    col = color or FRAME_COLOR
    out = wd_.js(FRAME_PAINT_JS % {"x": fx, "y": fy, "w": fw, "h": fh,
                                   "key": json.dumps(str(key)),
                                   "step": max(1, int(step)),
                                   "radius": float(radius),
                                   "r": float(col[0]), "g": float(col[1]),
                                   "b": float(col[2])})
    for ln in (out or []):
        s = str(ln)
        if s.startswith("FRAME	"):
            try:
                return int(float(s.split("	")[2]))
            except (IndexError, ValueError):
                pass
    return 0


def frame_clear(wd_, key=None):
    """擦掉边界 marker; key 省略 = 全部."""
    out = wd_.js(FRAME_CLEAR_JS % {"key": json.dumps(key) if key else "null"})
    for ln in (out or []):
        s = str(ln)
        if s.startswith("FRAMECLEAR	"):
            try:
                return int(float(s.split("	")[1]))
            except (IndexError, ValueError):
                pass
    return 0
