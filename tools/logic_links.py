"""Link resolution, payload coordinates and region candidate analysis.

This module reads immutable tool data and computes results without starting a
server, creating jobs, writing snapshots or calling a model provider.
"""
from __future__ import annotations

import json
import os
import re
import sys

import mlogcheck as C
import msch

HERE = (getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(sys.executable)))
        if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__)))

def _link_names(links):
    """Accept ["a","b"] or [{"name":"a","x":1,"y":2}] and return the name list."""
    names = []
    for link in links or []:
        if isinstance(link, dict):
            n = link.get('name')
        else:
            n = link
        if n:
            names.append(str(n))
    return names


def _link_objects(links):
    out = []
    for link in links or []:
        if isinstance(link, dict):
            out.append(msch.LogicLink(str(link.get('name', '')), int(link.get('x', 0)),
                                      int(link.get('y', 0))))
        else:
            out.append(msch.LogicLink(str(link), 0, 0))
    return out


def _link_stem(name):
    """message2 -> message. Link names are <blockname><ordinal> (LogicBlock.java:331-360)."""
    m = re.match(r'^(.*?)(\d+)$', str(name))
    return m.group(1) if m else str(name)


def _nearest_link(name, links, origin):
    """A bound link of the same block family as `name`, closest to the processor."""
    base = _link_stem(name)
    ox = oy = None
    if isinstance(origin, dict):
        try:
            ox, oy = int(origin.get('x') or 0), int(origin.get('y') or 0)
        except (TypeError, ValueError):
            ox = oy = None
    best, best_d = None, None
    for link in links or []:
        if isinstance(link, dict):
            n = str(link.get('name') or '')
            try:
                x, y = int(link.get('x') or 0), int(link.get('y') or 0)
            except (TypeError, ValueError):
                x = y = 0
        else:
            n, x, y = str(link), 0, 0
        if not n or _link_stem(n) != base:
            continue
        d = 0 if ox is None else (x - ox) ** 2 + (y - oy) ** 2
        if best is None or d < best_d:
            best, best_d = n, d
    return best


def _substitute_links(code, subs):
    """Rewrite whole-word occurrences of a link name; message1 must not touch message10."""
    out = code
    for old, new in subs.items():
        out = re.sub(r'(?<![A-Za-z0-9_-])' + re.escape(old) + r'(?![A-Za-z0-9_-])', lambda _m, n=new: n, out)
    return out

def _relative_links(links, origin):
    """Payload link coordinates, relative to the processor tile.

    LogicBlock.config(byte[]) -> readCompressed(data, true) adds the processor tile
    back to every link coordinate (LogicBlock.java:304-307), so the byte[] payload
    stores them RELATIVE. The mod reports absolute tile positions (LogicLink.x/y are
    absolute), so subtract origin when the caller tells us where the processor is.
    Without an origin the coordinates are passed through untouched (already relative).
    """
    ox = oy = None
    if isinstance(origin, dict):
        ox, oy = int(origin.get('x') or 0), int(origin.get('y') or 0)
    out = []
    for link in links or []:
        if isinstance(link, dict):
            x, y = int(link.get('x', 0) or 0), int(link.get('y', 0) or 0)
            if ox is not None:
                x, y = x - ox, y - oy
            out.append(msch.LogicLink(str(link.get('name', '')), x, y))
        else:
            out.append(msch.LogicLink(str(link), 0, 0))
    return out


# ---------------------------------------------------------------- region

#: LogicBlock.range = 8 * 10 world units (LogicBlock.java:49) and tilesize is 8,
#: so a link is legal while centre distance <= 80 + other.size*4 (LogicBlock.java:736
#: uses other.within(this, range + other.block.size*tilesize/2f)).
TILESIZE = 8


def _block_sizes():
    try:
        return json.load(open(os.path.join(HERE, 'block_sizes.json'), encoding='utf-8'))
    except Exception:
        return {}


def _block_size(block, sizes):
    try:
        return max(1, int(sizes.get(block) or 1))
    except Exception:
        return 1


def _link_base(block):
    """LogicBlock.getLinkName() (LogicBlock.java:123-135).

    The last '-' segment, unless that segment is 'large' or numeric -- then the
    second-to-last one.  Kept in step with mschgen.link_name_for() by a test.
    """
    name = str(block)
    if '-' in name:
        parts = name.split('-')
        last = parts[-1]
        if len(parts) >= 2 and (last == 'large' or re.fullmatch(r'[0-9.]+', last)):
            name = parts[-2]
        else:
            name = last
    return name


def _taken_numbers(names, base):
    """findLinkName() (LogicBlock.java:331-360): numbers already used by base<n>."""
    taken = set()
    for n in names:
        if n.startswith(base):
            tail = n[len(base):]
            if tail.isdigit():
                taken.add(int(tail))
    return taken


def _uses(code, name):
    """True when the code reads that exact identifier (container1 != container10)."""
    return re.search(r'(?<![A-Za-z0-9_-])' + re.escape(name) + r'(?![A-Za-z0-9_])', code) is not None


def _code_idents(code):
    """Lower-case identifiers the code mentions -- possible link names."""
    return set(re.findall(r'(?<![A-Za-z0-9_@-])([a-z][a-z0-9_-]*)', code))


def _result_names(code):
    """Names the code assigns itself (result slot = token 1 on every mlog line)."""
    out = set()
    for line in code.splitlines():
        toks = line.split()
        if len(toks) >= 2:
            out.add(toks[1])
    return out


def _known_bases():
    """Every link base name the game could hand out, from the block table."""
    return {_link_base(b) for b in _block_sizes()}


def _mlog_words():
    """Instruction / subcommand / op words -- never a link reference."""
    words = set()
    # KEYWORDS / OTHER_KEYWORDS are deliberately absent: 'core' is a ulocate
    # parameter there, and 'core' is exactly the word this check exists for.
    for attr in ('OP_UNARY', 'OP_BINARY', 'OP_LEGACY'):
        v = getattr(C, attr, None)
        if isinstance(v, (set, frozenset, list, tuple)):
            words.update(str(x).lower() for x in v)
    specs = getattr(C, 'SPECS', None) or {}
    try:
        words.update(str(k).lower() for k in specs)
    except TypeError:
        pass
    words.update({'true', 'false', 'null', 'end'})
    return words


def _linkish(name, known, blocks):
    """Does this word look like a link name the game would hand out?

    'core' is the case that matters: the game never hands out 'core' (getLinkName
    turns core-shard into 'shard'), but that is exactly what people type.  So a
    word qualifies when it is a base name or a prefix of a block name.
    """
    if name in known:
        return True
    if len(name) < 3:
        return False
    return any(b.startswith(name) for b in blocks)


def region(req):
    """A region snapshot from the game -> per-processor link candidates.

    The snapshot is main.js regionSnapshot(): blocks come back by their internal
    name, which is exactly what getLinkName() consumes.  Candidates are numbered
    the way the game numbers a freshly linked block, so 'wire container1' in the
    panel produces a name the processor will really see.

    Nothing here writes: the caller feeds a chosen candidate into /plan or
    /compose, and the payload that comes back is the game's own logic@config.
    """
    snap = req.get('snapshot')
    if not isinstance(snap, dict):
        raise ValueError('snapshot must be an object (main.js: maiSnapshot(x1,y1,x2,y2))')
    grid = snap.get('grid') or []
    procs = snap.get('processors') or []
    if not isinstance(grid, list) or not isinstance(procs, list):
        raise ValueError('snapshot.grid and snapshot.processors must be arrays')
    sizes = _block_sizes()
    out_procs = []
    for p in procs:
        if not isinstance(p, dict):
            continue
        px, py = int(p.get('x') or 0), int(p.get('y') or 0)
        pblock = str(p.get('block') or '')
        psize = _block_size(pblock, sizes)
        code = str(p.get('code') or '')
        raw_links = p.get('links') or []
        existing = []
        for link in raw_links:
            if isinstance(link, dict):
                existing.append(str(link.get('name') or ''))
            else:
                existing.append(str(link))
        pcx = px * TILESIZE + psize * TILESIZE / 2.0
        pcy = py * TILESIZE + psize * TILESIZE / 2.0
        buckets = {}
        for cell in grid:
            if not isinstance(cell, dict):
                continue
            bx, by = int(cell.get('x') or 0), int(cell.get('y') or 0)
            block = str(cell.get('block') or '')
            if not block or block == 'air':
                continue
            if bx == px and by == py:
                continue
            bsize = _block_size(block, sizes)
            bcx = bx * TILESIZE + bsize * TILESIZE / 2.0
            bcy = by * TILESIZE + bsize * TILESIZE / 2.0
            limit = 80.0 + bsize * TILESIZE / 2.0
            dist = ((pcx - bcx) ** 2 + (pcy - bcy) ** 2) ** 0.5
            if dist > limit:
                continue
            buckets.setdefault(_link_base(block), []).append(
                {'block': block, 'x': bx, 'y': by, 'dist': round(dist / TILESIZE, 2)})
        candidates = []
        for base in sorted(buckets):
            taken = _taken_numbers(existing, base)
            items = sorted(buckets[base], key=lambda c: (c['dist'], c['x'], c['y']))
            for item in items:
                n = 1
                while n in taken:
                    n += 1
                taken.add(n)
                name = '%s%d' % (base, n)
                candidates.append({'name': name, 'block': item['block'],
                                   'x': item['x'], 'y': item['y'], 'dist': item['dist'],
                                   'used': _uses(code, name)})
        candidates.sort(key=lambda c: (not c['used'], c['dist'], c['name']))
        # What the code reads but nothing answers to: not linked, and no candidate
        # with that name in range.  This is the 'core is never a link name' case --
        # the check that used to be silent (LogicBlock.getLinkName + findLinkName).
        known = _known_bases()
        blocks = set(sizes)
        words = _mlog_words()
        cand_names = {c['name'] for c in candidates}
        results = _result_names(code)
        # 'turret' is not a link just because 'turretX' (a radar result) is in the
        # code: a word followed by an upper-case letter is that longer variable.
        toks = set(code.split())
        missing = []
        for ident in sorted(_code_idents(code)):
            if any(t.startswith(ident) and len(t) > len(ident) and t[len(ident)].isupper()
                   for t in toks):
                continue
            if ident == 'air' or ident in words or ident in existing:
                continue
            if ident in cand_names or ident in results:
                continue
            base = ident.rstrip('0123456789') or ident
            if not _linkish(base, known, blocks):
                continue
            sug = ''
            for c in candidates:
                if c['name'].rstrip('0123456789') == base or str(c['block']).startswith(base):
                    sug = c['name']
                    break
            missing.append({'name': ident, 'base': base, 'suggest': sug})
        out_procs.append({'x': px, 'y': py, 'block': pblock, 'links': existing,
                          'statements': len(code.splitlines()),
                          'in_range': len(candidates),
                          'used_unlinked': [c['name'] for c in candidates if c['used']],
                          'missing': missing,
                          'candidates': candidates})
    return {'ok': True, 'schema': 1, 'map': snap.get('map'),
            'world': snap.get('world'), 'bounds': snap.get('bounds'),
            'cells': len(grid), 'truncated': bool(snap.get('truncated')),
            'processors': out_procs}
