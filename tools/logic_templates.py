"""Deterministic logic templates and offline intent routing.

Independent of the HTTP server, job queue and model provider. Generated code is
validated and encoded by logicd before it is returned to a caller.
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = (getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(sys.executable)))
        if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- templates

class Template:
    """One deterministic pattern.  Params are typed so a bad request is a 400."""

    def __init__(self, tid, title, params, build):
        self.id = tid
        self.title = title
        self.params = params      # name -> (type, default, help)
        self.build = build        # (params) -> (lines, referenced link names)

    def spec(self):
        return {'id': self.id, 'title': self.title,
                'params': [{'name': k, 'type': v[0], 'default': v[1], 'help': v[2]}
                           for k, v in self.params.items()]}


def _p(params, name, kind, default):
    v = params.get(name, default)
    if kind == 'int':
        try:
            return int(v)
        except (TypeError, ValueError):
            raise ValueError('param %r must be an integer, got %r' % (name, v))
    if kind == 'float':
        try:
            return float(v)
        except (TypeError, ValueError):
            raise ValueError('param %r must be a number, got %r' % (name, v))
    if kind == 'link':
        s = str(v or '').strip()
        if not s or not s.replace('_', 'a').replace('-', 'a').isalnum():
            raise ValueError('param %r must be a link name, got %r' % (name, v))
        return s
    if kind == 'unit':
        s = str(v or '').strip()
        if not s:
            raise ValueError('param %r must be a unit type' % name)
        return s if s.startswith('@') else '@' + s
    if kind == 'item':
        s = str(v or '').strip()
        if not s:
            raise ValueError('param %r must be an item name' % name)
        return s if s.startswith('@') else '@' + s
    s = str(v if v is not None else '')
    if len(s) > 120:
        raise ValueError('param %r is too long' % name)
    return s.replace('\n', ' ').replace('\r', ' ')


def _t_patrol(params):
    unit = _p(params, 'unit', 'unit', 'flare')
    x1, y1 = _p(params, 'x1', 'int', 10), _p(params, 'y1', 'int', 10)
    x2, y2 = _p(params, 'x2', 'int', 20), _p(params, 'y2', 'int', 10)
    hold = _p(params, 'wait', 'float', 1)
    lines = ['ubind ' + unit,
             'loop:',
             'ucontrol move %d %d 0 0 0' % (x1, y1),
             'wait %s' % hold,
             'ucontrol move %d %d 0 0 0' % (x2, y2),
             'wait %s' % hold,
             'jump loop always']
    return lines, []


def _t_item_threshold(params):
    cell = _p(params, 'container', 'link', 'container1')
    item = _p(params, 'item', 'item', 'copper')
    thr = _p(params, 'threshold', 'int', 100)
    msg = _p(params, 'message', 'link', 'message1')
    lines = ['loop:',
             'sensor n %s %s' % (cell, item),
             'jump enough greaterThanEq n %d' % thr,
             'print "low"',
             'printflush %s' % msg,
             'enough:',
             'wait 1',
             'jump loop always']
    return lines, [cell, msg]


def _t_radar_fire(params):
    turret = _p(params, 'turret', 'link', 'turret1')
    lines = ['loop:',
             'radar enemy any any distance %s 1 target' % turret,
             'jump fire notEqual target null',
             'wait 0.5',
             'jump loop always',
             'fire:',
             'control shootp %s target 1' % turret,
             'jump loop always']
    return lines, [turret]


def _t_memory_table(params):
    cell = _p(params, 'cell', 'link', 'cell1')
    idx = _p(params, 'index', 'int', 0)
    val = _p(params, 'value', 'int', 42)
    lines = ['write %d %s %d' % (val, cell, idx),
             'read out %s %d' % (cell, idx),
             'print out',
             'printflush message1',
             'end']
    return lines, [cell]


def _t_timer_flush(params):
    msg = _p(params, 'message', 'link', 'message1')
    secs = _p(params, 'seconds', 'float', 2)
    text = _p(params, 'text', 'str', 'tick')
    lines = ['loop:',
             'wait %s' % secs,
             'print "%s"' % text,
             'printflush %s' % msg,
             'jump loop always']
    return lines, [msg]


def _t_counter(params):
    cell = _p(params, 'cell', 'link', 'cell1')
    step = _p(params, 'step', 'int', 1)
    lines = ['loop:',
             'read n %s 0' % cell,
             'op add n n %d' % step,
             'write n %s 0' % cell,
             'wait 1',
             'jump loop always']
    return lines, [cell]


TEMPLATES = {t.id: t for t in [
    Template('patrol', 'bind a unit and move it between two tiles', {
        'unit': ('unit', 'flare', 'unit type, @ optional'),
        'x1': ('int', 10, 'first tile x'), 'y1': ('int', 10, 'first tile y'),
        'x2': ('int', 20, 'second tile x'), 'y2': ('int', 10, 'second tile y'),
        'wait': ('float', 1, 'seconds to hold at each end'),
    }, _t_patrol),
    Template('item-threshold', 'print when a container holds enough of an item', {
        'container': ('link', 'container1', 'container link name'),
        'item': ('item', 'copper', 'item name, @ optional'),
        'threshold': ('int', 100, 'count that counts as enough'),
        'message': ('link', 'message1', 'message link name'),
    }, _t_item_threshold),
    Template('radar-fire', 'point a turret at the nearest enemy unit', {
        'turret': ('link', 'turret1', 'turret link name'),
    }, _t_radar_fire),
    Template('memory-table', 'write and read one memory cell slot', {
        'cell': ('link', 'cell1', 'memory cell link name'),
        'index': ('int', 0, 'cell slot'), 'value': ('int', 42, 'value to store'),
    }, _t_memory_table),
    Template('timer-flush', 'print a line every N seconds', {
        'message': ('link', 'message1', 'message link name'),
        'seconds': ('float', 2, 'period in seconds'), 'text': ('str', 'tick', 'line to print'),
    }, _t_timer_flush),
    Template('counter', 'count up in a memory cell forever', {
        'cell': ('link', 'cell1', 'memory cell link name'),
        'step': ('int', 1, 'increment per second'),
    }, _t_counter),
]}


# ---------------------------------------------------------------- intent routing
#
# This is the ONE place a language model would plug in.  Everything downstream is
# the deterministic path (template -> code -> analyzer -> byte payload), so a model
# can only ever choose a template and fill its parameters -- it never hands raw mlog
# to the game.  The default backend is keyword rules, which runs offline; swapping in
# a model means replacing route_intent() and keeping its return shape.

_NUM = re.compile(r'-?[0-9]+(?:[.][0-9]+)?')
_ATNAME = re.compile(r'@[A-Za-z][A-Za-z0-9_-]*')

#: keyword sets, most specific first (ordered because ties break by position)
_INTENTS = [
    ('radar-fire', ('雷达', '开火', '炮塔', '攻击', '打怪', '射击', '瞄准',
                    'radar', 'turret', 'fire', 'shoot', 'aim')),
    ('item-threshold', ('物品', '资源', '容器', '阈值', '库存', '够', '满了', '铜', '铅',
                        'container', 'vault', 'threshold', 'item', 'stock', 'enough')),
    ('timer-flush', ('定时', '每隔', '周期', '报时', '刷屏', 'timer', 'every', 'interval')),
    ('counter', ('计数', '自增', '累加', 'counter', 'count up', 'count', 'increment')),
    ('memory-table', ('内存', '存储', '记忆', '存值', 'memory', 'store', 'save')),
    ('patrol', ('巡逻', '来回', '移动', '飞过去', 'patrol', 'move', 'walk', 'fly')),
]

_ITEMS = None


def _content_items():
    """Item names from tools/content_names.json, for "watch copper" style intents."""
    global _ITEMS
    if _ITEMS is None:
        try:
            data = json.load(open(os.path.join(HERE, 'content_names.json'), encoding='utf-8'))
            _ITEMS = [str(x) for x in (data.get('items') or [])]
        except Exception:
            _ITEMS = []
    return _ITEMS


def _numbers(text):
    out = []
    for m in _NUM.findall(text):
        try:
            f = float(m)
        except ValueError:
            continue
        out.append(int(f) if f == int(f) else f)
    return out


def _atoms(text):
    return _ATNAME.findall(text)


_ZH_LINK = {
    '容器': 'container', '仓库': 'vault', '核心': 'core', '内存': 'cell',
    '电池': 'battery', '消息': 'message', '炮塔': 'turret', '炮': 'turret',
    '显示器': 'display', '开关': 'switch',
}


_ITEM_ZH = {
    '铜': 'copper', '铅': 'lead', '煤': 'coal', '钛': 'titanium', '硅': 'silicon',
    '石墨': 'graphite', '钢化玻璃': 'metaglass', '爆炸物': 'blast-compound',
    '合金': 'surge-alloy', '相织物': 'phase-fabric', '碳化物': 'carbide',
    '裂变物质': 'fissile-matter', '铍': 'beryllium', '钨': 'tungsten',
    '废料': 'scrap', '钍': 'thorium', '沙': 'sand', '冰': 'ice', '孢子荚': 'spore-pod',
}


def _match_item(text):
    """First item mentioned in the sentence, English or Chinese.

    Order: @atoms, then English words with a word boundary (so 'sand' does not
    match 'thousand'), then the Chinese table.  None when nothing matches, so the
    caller keeps the template default.
    """
    items = _content_items()
    low = text.lower()
    for a in _atoms(text):
        name = a.lstrip('@')
        if name in items:
            return name
    for name in items:
        if re.search(r'\b' + re.escape(name.lower()) + r'\b', low):
            return name
    for zh, en in _ITEM_ZH.items():
        if zh in text and en in items:
            return en
    return None

def _pick_link(names, *subs):
    """First link whose name contains one of the substrings.

    Chinese substrings are translated to the English block names the game builds
    link names from (LogicBlock.getLinkName takes the block name), so a Chinese
    sentence can still pick the right link instead of silently falling back to
    whatever came first.
    """
    want = []
    for sub in subs:
        want.append(sub)
        for zh, en in _ZH_LINK.items():
            if zh in sub:
                want.append(en)
    for sub in want:
        for n in names:
            if sub in n.lower():
                return n
    return None


def _fallback_link(names, *avoid):
    for n in names:
        low = n.lower()
        if not any(a in low for a in avoid):
            return n
    return names[0] if names else None


def _params_patrol(text, names):
    atoms = _atoms(text)
    nums = _numbers(text)
    p = {}
    if atoms:
        p['unit'] = atoms[0].lstrip('@')
    if len(nums) >= 4:
        p['x1'], p['y1'], p['x2'], p['y2'] = nums[0], nums[1], nums[2], nums[3]
    elif len(nums) == 2:
        p['x2'], p['y2'] = nums[0], nums[1]
    return p


def _params_radar_fire(text, names):
    turret = _pick_link(names, 'turret', '炮', 'tur', 'duo', 'scatter', 'lance', 'arc')
    if turret is None:
        turret = _fallback_link(names, 'message', 'msg', 'cell', 'bank')
    return {'turret': turret} if turret else {}


def _params_item_threshold(text, names):
    p = {}
    container = _pick_link(names, 'container', 'vault', 'storage', '容器', 'core')
    if container is None:
        container = _fallback_link(names, 'message', 'msg', 'cell')
    if container:
        p['container'] = container
    message = _pick_link(names, 'message', 'msg')
    if message:
        p['message'] = message
    item = _match_item(text)
    if item:
        p['item'] = item
    nums = _numbers(text)
    if nums:
        p['threshold'] = nums[0]
    return p


def _params_memory(text, names):
    p = {}
    cell = _pick_link(names, 'cell', 'memory', 'bank', '内存')
    if cell is None:
        cell = _fallback_link(names, 'message', 'msg', 'container')
    if cell:
        p['cell'] = cell
    nums = _numbers(text)
    if len(nums) >= 2:
        p['index'], p['value'] = nums[0], nums[1]
    elif nums:
        p['value'] = nums[0]
    return p


def _params_timer(text, names):
    p = {}
    message = _pick_link(names, 'message', 'msg')
    if message:
        p['message'] = message
    nums = _numbers(text)
    if nums:
        p['seconds'] = nums[0]
    return p


def _params_counter(text, names):
    p = {}
    cell = _pick_link(names, 'cell', 'memory', 'bank', '内存')
    if cell is None:
        cell = _fallback_link(names, 'message', 'msg', 'container')
    if cell:
        p['cell'] = cell
    nums = _numbers(text)
    if nums:
        p['step'] = nums[0]
    return p


_PARAMS = {
    'patrol': _params_patrol,
    'radar-fire': _params_radar_fire,
    'item-threshold': _params_item_threshold,
    'memory-table': _params_memory,
    'timer-flush': _params_timer,
    'counter': _params_counter,
}


def route_intent(intent, names):
    """intent text -> (template id, one-line reason, params).  Rules only, offline."""
    low = intent.lower()
    best, best_score, best_words = None, 0, []
    for tid, words in _INTENTS:
        hit = [w for w in words if w.lower() in low]
        if len(hit) > best_score:
            best, best_score, best_words = tid, len(hit), hit
    if best is None:
        return None, '', {}
    params = _PARAMS[best](intent, names)
    why = 'matched %s -> template %r' % (', '.join(best_words), best)
    return best, why, params
