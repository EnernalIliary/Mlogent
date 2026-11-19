"""Transport-independent logic analysis, composition and intent planning.

Call these functions directly without starting HTTP, a job queue or a model
provider. Findings and encoded payloads describe the same signed program.
"""
from __future__ import annotations

import base64

import aigenerated
import mlogcheck as C
import msch
from logic_templates import TEMPLATES, route_intent as _route
from logic_links import _link_names, _nearest_link, _substitute_links, _relative_links

SIGN_AUTHOR = aigenerated.SIGN_AUTHOR

def plan(req):
    """Natural-language intent -> the same payload /compose returns, plus the reasoning."""
    intent = str(req.get('intent') or '').strip()
    if not intent:
        raise ValueError('intent must be a non-empty string')
    if len(intent) > 2000:
        raise ValueError('intent is too long (2000 characters)')
    links = req.get('links') or []
    ipt = int(req.get('ipt') or 2)
    tid, why, params = _route(intent, _link_names(links))
    if tid is None:
        why = 'no template matched this intent -- say what the processor should do: patrol, watch an item, point a turret, count up, print on a timer, store a value'
        return {'ok': False, 'intent': intent, 'template': None, 'reason': why,
                'candidates': [{'id': t.id, 'title': t.title} for t in TEMPLATES.values()]}
    res = compose({'template': tid, 'params': params, 'links': links, 'ipt': ipt,
                   'origin': req.get('origin')})
    res['intent'] = intent
    res['params'] = params
    res['reason'] = why
    return res

# ---------------------------------------------------------------- analysis

def analyse(code, links, ipt=2):
    """Run the same analyzer the gate runs; return a JSON-ready dict.

    links is None when the caller does not know the processor's link table (a
    plain .mlog file), and [] when it knows the table is empty.  The mod reads
    LogicBlock.links, so its [] is authoritative: a link-shaped name in a link
    slot then really is unbound, and the gate must see it (v0.9.0; before this
    the empty list was collapsed to None and every hallucinated link name on a
    link-less processor slipped through).
    """
    names = _link_names(links) if links is not None else None
    lines = code.splitlines()
    # A label line is NOT a statement (LParser.java:117-125), so count slots with
    # the analyzer's own prepare() instead of counting non-blank lines.
    stmts = [(ln + 1, c) for ln, c in C.prepare(lines)]
    # Finding.line is a STATEMENT index; the panel highlights a line of the code
    # text, so translate through prepare()'s own (line, code) pairs.
    srcline = {i: ln for i, (ln, _) in enumerate(stmts)}
    findings = []
    for f in C.analyse(lines, links=names, ipt=ipt,
                       links_authoritative=links is not None):
        findings.append({'sev': f.sev, 'line': srcline.get(f.line, f.line + 1),
                         'stmt': f.line, 'rid': _rid(f), 'msg': f.msg})
    errors = sum(1 for f in findings if f['sev'] == 'ERR')
    warns = sum(1 for f in findings if f['sev'] == 'WARN')
    try:
        cost = C.cost_report(stmts, links=names)
    except Exception as exc:                       # cost model is advisory only
        cost = '  (cost model failed: %s)' % exc
    return {'ok': errors == 0, 'findings': findings, 'errors': errors, 'warns': warns,
            'statements': len(stmts), 'cost': cost}


def _rid(finding):
    try:
        from rule_ids import rule_id
        return rule_id(finding.sev, finding.msg)
    except Exception:
        return ''


def compose(req):
    """template + params + links -> code, findings, and the game's own byte payload."""
    tid = req.get('template')
    tmpl = TEMPLATES.get(tid)
    if tmpl is None:
        raise ValueError('unknown template %r (known: %s)' % (tid, ', '.join(sorted(TEMPLATES))))
    params = req.get('params') or {}
    if not isinstance(params, dict):
        raise ValueError('params must be an object')
    lines, refs = tmpl.build(params)
    code = '\n'.join(lines)
    links = req.get('links') or []
    names = _link_names(links)
    origin = req.get('origin')
    if origin is not None and not isinstance(origin, dict):
        raise ValueError('origin must be an object with x and y')
    # A template names the links it writes into the code (e.g. message1), but a player's
    # processor often holds message2 -- same block, different ordinal. Point the template
    # at the nearest bound link of the same block family instead of refusing outright,
    # and say so: silently printing into a different display would be worse than an INFO.
    subs, subs_info = {}, []
    for n in refs:
        if n in names:
            continue
        alt = _nearest_link(n, links, origin)
        if alt is not None:
            subs[n] = alt
            subs_info.append((n, alt))
    if subs:
        code = _substitute_links(code, subs)
    # v0.14.2: sign before analyzing, so the findings, the statement count and the
    # compiled payload all describe the text that actually gets written.  The
    # signature only touches the tail (the token rides in an unconditional jump's
    # value slot and the dead `end` behind it is dropped), so no line moves.
    code, sig = aigenerated.sign_text(code, SIGN_AUTHOR, force=True)
    # Anything still unbound is a hard error here: the analyzer would also say so, but a
    # template should name the link it wanted.
    missing = [n for n in refs if n not in names and n not in subs]
    res = analyse(code, links, ipt=int(req.get('ipt') or 2))
    for old, new in subs_info:
        res['findings'].insert(0, {
            'sev': 'INFO', 'line': 0, 'rid': 'template-link-substituted',
            'msg': 'template %r writes %s but this processor has no such link; used %s instead (nearest bound link of the same block)' % (tid, old, new)})
    if missing:
        res['findings'].insert(0, {
            'sev': 'ERR', 'line': 0, 'rid': 'template-needs-link',
            'msg': 'template %r writes %s into the code but the processor has no such link '
                   '(link names are <blockname><n>, e.g. container1; see docs/速查卡.md section 6)'
                   % (tid, ', '.join(missing))})
        res['errors'] += 1
        res['ok'] = False
    payload = msch.build_logic_data(code, _relative_links(links, origin))
    return {'ok': res['ok'], 'template': tid, 'code': code, 'sig': sig,
            'findings': res['findings'], 'errors': res['errors'], 'warns': res['warns'],
            'statements': res['statements'], 'cost': res['cost'],
            'links': _link_names(links),
            'origin': origin,
            'bytes_b64': base64.b64encode(payload).decode('ascii'),
            'bytes_len': len(payload)}
