"""Model endpoint URLs, public settings views and diagnostic requests.

Configuration is supplied explicitly by the caller. Importing this module does
not create a queue, read credentials or make network requests.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

import mlogprovider

def _mask_key(key):
    s = str(key or '')
    if not s:
        return ''
    if len(s) <= 4:
        return '*' * len(s)
    return '*' * 6 + s[-4:]


def public_state(state):
    st = state
    return {'ok': True, 'kind': st['kind'], 'url': st['url'], 'model': st['model'],
            'key_set': bool(st['key']), 'key_hint': _mask_key(st['key']),
            'timeout': int(st['timeout'] or 60),
            'max_tokens': int(st.get('max_tokens') or mlogprovider.DEFAULT_MAX_TOKENS)}


def models_url(url):
    """'.../v1/chat/completions' -> '.../v1/models'; anything else gets '/models'."""
    u = str(url or '').strip()
    if not u:
        raise ValueError('model url is empty')
    for tail in ('/chat/completions', '/completions', '/responses'):
        if u.endswith(tail):
            return u[:-len(tail)] + '/models'
    u = u.rstrip('/')
    if u.endswith('/models'):
        return u
    return u + '/models'


def completion_url(url):
    """A bare API base ('.../v1') becomes the chat endpoint; full endpoints pass through."""
    u = str(url or '').strip()
    if not u:
        raise ValueError('model url is empty')
    low = u.lower().rstrip('/')
    for tail in ('/chat/completions', '/completions', '/responses'):
        if low.endswith(tail):
            return u
    return u.rstrip('/') + '/chat/completions'


def probe_model(req, state):
    """POST /llm/probe -- one tiny chat call, so a player can see what the endpoint really says.

    The job path only reports 'empty reply' or 'HTTP 404', which leaves a player guessing.
    This returns the raw body excerpt, finish_reason, usage and the message keys instead.
    """
    url = str(req.get('url') or state['url'] or '').strip()
    if not url:
        raise ValueError('a model url is required (an OpenAI compatible /chat/completions)')
    if not (url.startswith('http://') or url.startswith('https://')):
        raise ValueError('the model url must start with http:// or https://')
    url = completion_url(url)
    model = str(req.get('model') if req.get('model') is not None else state['model']).strip()
    key = str(req.get('key') if req.get('key') is not None else state['key'])
    try:
        timeout = int(req.get('timeout') or state['timeout'] or 60)
    except (TypeError, ValueError):
        timeout = 60
    body = {'messages': [{'role': 'user',
                          'content': 'Reply with exactly this JSON and nothing else: {"ok": true}'}],
            'temperature': 0, 'max_tokens': max(512, int(state.get('max_tokens')
                                                              or 512) // 4)}
    if model:
        body['model'] = model
    out = {'ok': True, 'url': url, 'model': model, 'status': 0}
    request = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), method='POST')
    request.add_header('Content-Type', 'application/json')
    if key:
        request.add_header('Authorization', 'Bearer ' + key)
    raw = ''
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            raw = resp.read().decode('utf-8', 'replace')
            out['status'] = resp.status
    except urllib.error.HTTPError as exc:
        out['status'] = exc.code
        out['error'] = 'HTTP %s %s' % (exc.code, exc.reason)
        try:
            raw = exc.read().decode('utf-8', 'replace')
        except Exception:
            raw = ''
    except urllib.error.URLError as exc:
        out['error'] = 'cannot reach the endpoint: %s' % exc
    except OSError as exc:
        out['error'] = 'the call failed: %s' % exc
    out['raw_len'] = len(raw)
    out['raw'] = raw[:1200]
    try:
        doc = json.loads(raw) if raw else None
    except ValueError:
        doc = None
    if isinstance(doc, dict):
        choices = doc.get('choices')
        c0 = choices[0] if isinstance(choices, list) and choices else None
        if isinstance(c0, dict):
            out['finish_reason'] = c0.get('finish_reason')
            msg = c0.get('message')
            if isinstance(msg, dict):
                content = msg.get('content')
                out['content_len'] = len(content) if isinstance(content, str) else 0
                out['content'] = content[:800] if isinstance(content, str) else ''
                out['message_keys'] = sorted([str(k) for k in msg.keys()])
                for alt in ('reasoning_content', 'reasoning'):
                    v = msg.get(alt)
                    if isinstance(v, str) and v:
                        out['reasoning_len'] = len(v)
        usage = doc.get('usage')
        if isinstance(usage, dict) and usage:
            out['usage'] = usage
        if doc.get('error'):
            out['error'] = str(doc.get('error'))[:400]
    return out


def fetch_models(url, key='', timeout=20):
    """Ask the endpoint what it serves. Runs on the sidecar so the mod never needs TLS."""
    target = models_url(url)
    req = urllib.request.Request(target, method='GET')
    req.add_header('Accept', 'application/json')
    if key:
        req.add_header('Authorization', 'Bearer ' + str(key))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as exc:
        raise ValueError('model list refused: HTTP %s %s' % (exc.code, exc.reason))
    except urllib.error.URLError as exc:
        raise ValueError('cannot reach the model endpoint: %s' % (exc.reason,))
    except OSError as exc:
        raise ValueError('model list request failed: %s' % (exc,))
    try:
        doc = json.loads(raw)
    except ValueError:
        raise ValueError('the model endpoint did not answer with JSON')
    ids = []
    data = doc.get('data') if isinstance(doc, dict) else doc
    if isinstance(data, list):
        for item in data:
            mid = (item.get('id') or item.get('name')) if isinstance(item, dict) else item
            if mid:
                ids.append(str(mid))
    elif isinstance(doc, dict) and isinstance(doc.get('models'), list):
        for item in doc['models']:
            mid = (item.get('id') or item.get('name')) if isinstance(item, dict) else item
            if mid:
                ids.append(str(mid))
    out = sorted({s for s in ids if s})
    return {'ok': True, 'url': target, 'models': out, 'count': len(out)}
