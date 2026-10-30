#!/usr/bin/env python3
"""jobqueue -- P4, first cut: the job queue, its state machine, and the write gate.

The mod posts a *job* (one sentence + the region snapshot it was drawn over); a
worker turns that into mlog, runs the same analyzer the gate runs, and only a
clean program ever reaches the 'done' state.  No model is wired in yet: the
generator is a pluggable provider and the built-in one is the template router
that already exists in logicd, so the whole state machine is exercised offline
(docs/Mlog辅助-规划.md section 4.5 asks for exactly that).

Contract (docs/Mlog辅助-规划.md section 4.1)
-------------------------------------------
    {id: sha1(snapshot+desc+mode)[:16], created, state, mode, desc, snapshot,
     attempts, findings[], code, explanation, assumptions[]}

    queued -> running -> done | rejected | failed | cancelled

Every transition is written to <dir>/<id>.json before it is reported (the mod
also keeps its own copy, so a sidecar crash does not lose the job).  On startup
a job found in 'running' is put back to 'queued' with its attempt count intact --
that is what "双写可续" means here.

Why link-name-not-bound is fatal here but only a WARN in the analyzer
--------------------------------------------------------------------
mlogcheck reports a link-shaped name the processor does not own as WARN: a human
may be halfway through wiring it up and still wants to see the rest.  A job is
machine output written straight into a processor, so an unbound link name is a
broken write, not a hint.  FATAL_RIDS promotes exactly that rule to a refusal,
and it is the one case docs/Mlog辅助-规划.md section 4.5 names as an acceptance
test.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import threading
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

#: one first try plus two self-repairs (docs/Mlog辅助-规划.md:175)
MAX_ATTEMPTS = 3

STATES = ('queued', 'running', 'done', 'rejected', 'failed', 'cancelled')
TERMINAL = ('done', 'rejected', 'failed', 'cancelled')

#: analyzer WARNs that a machine write must not accept (see the module docstring)
FATAL_RIDS = ('link-name-not-bound',)

DEFAULT_DIR = os.path.join(ROOT, 'out', 'jobs')


def _logicd():
    """Late import: logicd imports this module at load time, so the edge is one-way."""
    import logicd
    return logicd


def default_dir():
    return os.environ.get('MLOG_JOBS_DIR') or DEFAULT_DIR


def job_id(snapshot, desc, mode):
    """sha1(snapshot + desc + mode)[:16] -- stable across retries, so POST is idempotent."""
    blob = json.dumps({'snapshot': snapshot, 'desc': desc, 'mode': mode},
                      ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha1(blob.encode('utf-8')).hexdigest()[:16]


def _int(v, name, default=None):
    if v is None and default is not None:
        return default
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError('%s must be an integer' % name)
    return int(v)


def normalize(body):
    """A request body -> the job object of section 4.1 (raises ValueError on junk)."""
    if not isinstance(body, dict):
        raise ValueError('job must be a JSON object')
    desc = body.get('desc')
    if not isinstance(desc, str) or not desc.strip():
        raise ValueError('job.desc must be a non-empty string')
    desc = desc.strip()
    if len(desc) > 2000:
        raise ValueError('job.desc is too long (2000 characters)')
    mode = body.get('mode') or 'new'
    if mode not in ('new', 'edit'):
        raise ValueError("job.mode must be 'new' or 'edit'")
    snap = body.get('snapshot')
    if snap is None:
        snap = {}
    if not isinstance(snap, dict):
        raise ValueError('job.snapshot must be an object (main.js: maiSnapshot(x1,y1,x2,y2))')
    # null means "the mod could not read the link table" (unknown); [] means the
    # table is known and empty, which is what the gate needs to catch a
    # hallucinated link name on a processor that links to nothing.
    links = body.get('links')
    if links is not None and not isinstance(links, list):
        raise ValueError('job.links must be a list, or null when the link table is unknown')
    origin = body.get('origin')
    if origin is not None:
        if not isinstance(origin, dict):
            raise ValueError('job.origin must be an object with x and y')
        origin = {'x': _int(origin.get('x'), 'origin.x', 0),
                  'y': _int(origin.get('y'), 'origin.y', 0)}
    ipt = _int(body.get('ipt'), 'job.ipt', 2)
    if not 1 <= ipt <= 40:
        raise ValueError('job.ipt must be 1..40 (LogicBlock.maxInstructionsPerTick)')
    jid = job_id(snap, desc, mode)
    return {'id': jid, 'created': int(body.get('created') or time.time() * 1000),
            'state': 'queued', 'mode': mode, 'desc': desc, 'snapshot': snap,
            'links': links, 'origin': origin, 'ipt': ipt,
            'attempts': 0, 'findings': [], 'code': '', 'explanation': '',
            'assumptions': [], 'template': None, 'params': {}, 'bytes_b64': ''}


def gate(code, links, ipt=2):
    """Analyze generated code and promote FATAL_RIDS to refusals.

    links=[] is authoritative (the processor has no links), links=None is unknown
    and skips the link check entirely -- logicd.analyse() keeps that distinction.

    Returns the same shape logicd.analyse() returns, plus 'fatal' -- the promoted
    findings, so the mod can tell "the model wrote a link it does not own" apart
    from "the model wrote an unrelated ERR".
    """
    res = _logicd().analyse(code, links, ipt=ipt)
    fatal = []
    for f in res['findings']:
        if f.get('rid') in FATAL_RIDS:
            f['sev'] = 'ERR'
            f['fatal'] = True
            fatal.append(f)
    if fatal:
        res['errors'] += len(fatal)
        res['ok'] = False
    res['fatal'] = fatal
    return res


class Store:
    """One JSON file per job; every write is tmp + os.replace so a crash never truncates."""

    def __init__(self, path=None):
        self.path = path or default_dir()
        os.makedirs(self.path, exist_ok=True)

    def file(self, jid):
        return os.path.join(self.path, jid + '.json')

    def save(self, job):
        body = json.dumps(job, ensure_ascii=False, indent=1, sort_keys=True)
        tmp = self.file(job['id']) + '.tmp'
        with open(tmp, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(body)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, self.file(job['id']))
        return self.file(job['id'])

    def load(self, jid):
        path = self.file(jid)
        if not os.path.isfile(path):
            return None
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)

    def ids(self):
        return sorted(n[:-5] for n in os.listdir(self.path) if n.endswith('.json'))

    def all(self):
        out = []
        for jid in self.ids():
            try:
                job = self.load(jid)
            except Exception:
                continue                      # a half-written file is not a job
            if isinstance(job, dict) and job.get('id'):
                out.append(job)
        return out


class Queue:
    """The state machine.  provider(job, hint) -> output dict is the only seam to a model."""

    def __init__(self, store=None, provider=None, poll=0.05):
        self.store = store or Store()
        self.provider = provider or template_provider
        self.poll = poll
        self.lock = threading.RLock()
        self.jobs = {}
        self.thread = None
        self.running = False
        self.resumed = 0
        for job in self.store.all():
            if job.get('state') == 'running':     # crashed mid-flight: put it back
                job['state'] = 'queued'
                job['resumed'] = True
                self.store.save(job)
                self.resumed += 1
            elif job.get('state') == 'queued':
                self.resumed += 1
            self.jobs[job['id']] = job

    # -- public API ------------------------------------------------------
    def enqueue(self, body):
        """-> (job, created).  A second POST of the same body is a no-op (section 4.2)."""
        job = normalize(body)
        with self.lock:
            old = self.jobs.get(job['id'])
            if old is not None:
                return dict(old), False
            self.jobs[job['id']] = job
            self.store.save(job)
            return dict(job), True

    def get(self, jid):
        with self.lock:
            job = self.jobs.get(jid)
            return dict(job) if job else None

    def list(self, state=None):
        with self.lock:
            jobs = [dict(j) for j in self.jobs.values()]
        if state:
            jobs = [j for j in jobs if j.get('state') == state]
        else:
            jobs = [j for j in jobs if j.get('state') not in TERMINAL]
        return sorted(jobs, key=lambda j: (j.get('created') or 0, j.get('id') or ''))

    def cancel(self, jid):
        """Cancelling is allowed in every non-terminal state (section 4.2)."""
        with self.lock:
            job = self.jobs.get(jid)
            if job is None:
                return None
            if job['state'] in TERMINAL:
                return dict(job)
            job['cancel_requested'] = True
            if job['state'] == 'queued':
                job['state'] = 'cancelled'
                job['finished'] = int(time.time() * 1000)
            self.store.save(job)
            return dict(job)

    def start(self):
        if self.thread is not None:
            return self
        self.running = True
        self.thread = threading.Thread(target=self._loop, name='jobqueue', daemon=True)
        self.thread.start()
        return self

    def stop(self):
        self.running = False
        t = self.thread
        self.thread = None
        if t is not None:
            t.join(timeout=5)
        return self

    def drain(self, timeout=20.0):
        """Run the worker inline until nothing is queued (tests, one-shot CLI)."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            jid = self._next()
            if jid is None:
                return True
            self._run(jid)
        return False

    # -- worker ----------------------------------------------------------
    def _next(self):
        with self.lock:
            for jid in sorted(self.jobs, key=lambda i: (self.jobs[i].get('created') or 0, i)):
                if self.jobs[jid]['state'] == 'queued':
                    return jid
        return None

    def _loop(self):
        while self.running:
            jid = self._next()
            if jid is None:
                time.sleep(self.poll)
                continue
            try:
                self._run(jid)
            except Exception:                 # the worker must outlive one bad job
                traceback.print_exc()

    def _set(self, jid, **fields):
        with self.lock:
            job = self.jobs[jid]
            job.update(fields)
            self.store.save(job)
            return job

    def _cancelled(self, job):
        if job.get('cancel_requested'):
            self._set(job['id'], state='cancelled', finished=int(time.time() * 1000))
            return True
        return False

    def _run(self, jid):
        with self.lock:
            job = self.jobs.get(jid)
            if job is None or job['state'] != 'queued':
                return
            job['state'] = 'running'
            job['started'] = int(time.time() * 1000)
            job.pop('resumed', None)
            self.store.save(job)
        hint = None
        while True:
            if self._cancelled(job):
                return
            if job['attempts'] >= MAX_ATTEMPTS:
                self._set(jid, state='rejected', finished=int(time.time() * 1000),
                          explanation=job.get('explanation') or
                          'refused after %d attempt(s): the gate never saw a clean program'
                          % MAX_ATTEMPTS)
                return
            job['attempts'] += 1
            with self.lock:
                self.store.save(job)
            try:
                out = self.provider(dict(job), hint)
            except Exception as exc:
                self._set(jid, state='failed', finished=int(time.time() * 1000),
                          explanation='provider raised %s: %s' % (type(exc).__name__, exc))
                return
            if self._cancelled(job):
                return
            if not isinstance(out, dict):
                out = {'error': 'provider returned %r, want an object' % (out,)}
            if out.get('error'):
                hint = [{'sev': 'ERR', 'rid': 'provider-error', 'line': 0,
                         'msg': str(out['error'])}]
                self._set(jid, findings=hint)
                continue
            res = self._materialize(job, out)
            self._set(jid, findings=res['findings'], explanation=res.get('explanation') or '',
                      assumptions=res.get('assumptions') or [],
                      template=res.get('template'), params=res.get('params') or {})
            if res['ok']:
                self._set(jid, state='done', code=res['code'],
                          bytes_b64=res.get('bytes_b64') or '',
                          statements=res.get('statements') or 0,
                          finished=int(time.time() * 1000))
                return
            hint = res['findings']

    def _materialize(self, job, out):
        """Provider output -> {ok, code, findings, ...}; the anchored tier goes through compose."""
        L = _logicd()
        # keep None ("the mod could not read the table") apart from [] ("no links"):
        # the gate treats the empty list as authoritative and skips None entirely.
        links = job.get('links')
        ipt = job.get('ipt') or 2
        if isinstance(out.get('code'), str) and out['code'].strip():
            code = out['code']
            res = gate(code, links, ipt=ipt)
            # the reply may also DECLARE which links it wants (section 4.3 needs_links);
            # a name that is not in an authoritative table is a refusal, not a warning.
            if links is not None:
                have = L._link_names(links)
                missing = [str(n) for n in (out.get('needs_links') or []) if str(n) not in have]
                if missing:
                    bad = {'sev': 'ERR', 'rid': 'link-name-not-bound', 'line': 0,
                           'fatal': True,
                           'msg': 'the reply needs link(s) this processor does not have: '
                                  + ', '.join(missing)}
                    res['findings'].append(bad)
                    res['fatal'].append(bad)
                    res['errors'] += 1
                    res['ok'] = False
            payload = L.msch.build_logic_data(code, L._relative_links(links or [], job.get('origin')))
            res.update({'code': code,
                        'bytes_b64': base64.b64encode(payload).decode('ascii'),
                        'explanation': out.get('explanation') or '',
                        'assumptions': out.get('assumptions') or []})
            return res
        tid = out.get('template')
        if not tid:
            res = gate('', links, ipt=ipt)
            res['findings'] = [{'sev': 'ERR', 'rid': 'provider-no-code', 'line': 0,
                                'msg': 'provider returned neither code nor template'}]
            res['ok'] = False
            res['code'] = ''
            return res
        cres = L.compose({'template': tid, 'params': out.get('params') or {},
                          'links': links, 'ipt': ipt, 'origin': job.get('origin')})
        # compose() reports analyzer severities; the job gate is stricter
        fatal = []
        for f in cres['findings']:
            if f.get('rid') in FATAL_RIDS and f['sev'] != 'ERR':
                f['sev'] = 'ERR'
                f['fatal'] = True
                fatal.append(f)
        if fatal:
            cres['errors'] += len(fatal)
            cres['ok'] = False
        cres['fatal'] = fatal
        cres['explanation'] = out.get('explanation') or ''
        cres['assumptions'] = out.get('assumptions') or []
        cres['template'] = tid
        cres['params'] = out.get('params') or {}
        return cres


# ---------------------------------------------------------------- providers

def template_provider(job, hint=None):
    """The offline tier: the intent router already in logicd picks a template."""
    L = _logicd()
    res = L.plan({'intent': job['desc'], 'links': job.get('links') or [],
                  'ipt': job.get('ipt') or 2, 'origin': job.get('origin')})
    if not res.get('template'):
        why = res.get('reason') or 'no template matched this description'
        return {'error': why + ' | 当前是模板档，只能套固定样板；要自由描述，请在 设置 -> '
                                'Mlog辅助 -> 大模型 里填地址/密钥/模型，再点「启用模型档」'}
    return {'template': res['template'], 'params': res.get('params') or {},
            'explanation': res.get('reason') or ('template %s' % res['template']),
            'assumptions': []}


class FakeProvider:
    """Test-only provider: answers from a table keyed by a substring of the description.

    A value may be a list, consumed one entry per attempt -- that is how a
    self-repair case is written (first a hallucinated link, then good code).  A
    value may carry 'sleep' seconds so a cancellation test has a window.
    """

    def __init__(self, table, default=None):
        self.table = table or {}
        self.default = default if default is not None else {'error': 'no fake response'}
        self.calls = {}

    def _pick(self, job, hint):
        # longest key wins, so a table can hold both a short and a longer phrase
        key = None
        for k in self.table:
            if k and k in job['desc'] and (key is None or len(k) > len(key)):
                key = k
        if key is None:
            return self.default
        val = self.table[key]
        if isinstance(val, list):
            n = self.calls.get(key, 0)
            self.calls[key] = n + 1
            return val[min(n, len(val) - 1)]
        return val

    def __call__(self, job, hint=None):
        out = self._pick(job, hint)
        if isinstance(out, dict) and out.get('sleep'):
            time.sleep(float(out['sleep']))
        return out


def load_fake_provider(path):
    with open(path, encoding='utf-8') as fh:
        table = json.load(fh)
    if not isinstance(table, dict):
        raise ValueError('fake provider file must be a JSON object')
    default = table.pop('__default__', None)
    return FakeProvider(table, default)
