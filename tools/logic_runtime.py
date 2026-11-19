"""Application-owned configuration, queues, chat storage and server lifecycle."""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import json
import os
import sys
import threading
import time
from http.server import ThreadingHTTPServer

import jobqueue
import mlogprovider
import logic_models
from logic_models import completion_url, fetch_models
from logic_templates import TEMPLATES
from logic_http import make_handler

SIDECAR_VERSION = '0.24.1'

BRIEF_DROP = ('snapshot', 'code', 'bytes_b64', 'reasoning', 'links', 'assumptions')
_CURRENT = ContextVar('logic_application', default=None)
_DEFAULT = None
_DEFAULT_LOCK = threading.RLock()


def default_application():
    global _DEFAULT
    with _DEFAULT_LOCK:
        if _DEFAULT is None:
            _DEFAULT = Application()
        return _DEFAULT


def current_application():
    app = _CURRENT.get()
    return app if app is not None else default_application()


@contextmanager
def using_application(app):
    token = _CURRENT.set(app)
    try:
        yield
    finally:
        _CURRENT.reset(token)


class ChatFacade:
    """Bind the existing chat API and its worker context to one application."""
    def __init__(self, app):
        self.app = app

    def __getattr__(self, name):
        import chats
        value = getattr(chats, name)
        if not callable(value) or isinstance(value, type):
            return value
        def call(*args, **kwargs):
            with using_application(self.app):
                return value(*args, **kwargs)
        return call


class Application:
    PROTOCOL = 1
    SIDECAR_VERSION = SIDECAR_VERSION
    GAME = 'mindustry v160.7 (executor jar out/_server160.jar)'
    IPT_MAX = 40
    LINK_RANGE_TILES = 10
    jobqueue = jobqueue
    fetch_models = staticmethod(fetch_models)

    def __init__(self, writable_root=None):
        frozen = bool(getattr(sys, 'frozen', False))
        self.HERE = (getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(sys.executable)))
                     if frozen else os.path.dirname(os.path.abspath(__file__)))
        self.WROOT = (str(writable_root) if writable_root is not None else
                      os.path.dirname(os.path.abspath(sys.executable)) if frozen else
                      os.path.dirname(self.HERE))
        self.SNAP_DIR = os.path.join(self.WROOT, 'out', 'snapshots')
        self.LLM_STATE = {'kind': 'template', 'url': '', 'model': '', 'key': '',
                          'timeout': 60, 'max_tokens': mlogprovider.DEFAULT_MAX_TOKENS}
        self.LAST_PING = time.time()
        self.STOP = threading.Event()
        self.jobs_dir = (os.path.join(self.WROOT, 'out', 'jobs') if writable_root is not None else
                         (os.environ.get('MLOG_JOBS_DIR') or os.path.join(self.WROOT, 'out', 'jobs'))
                         if frozen else None)
        self.JOBS = None
        self.JOB_WORKERS = 3
        self.queue_lock = threading.RLock()
        self.closed = False
        self.chat_store = None
        self.chat_store_lock = threading.RLock()
        self.chat_running = set()
        self.chat_run_lock = threading.RLock()
        self.chat_gone = set()
        self.chat_context = threading.local()
        self.chats = ChatFacade(self)

    def close(self):
        with self.queue_lock:
            if self.closed:
                return
            self.closed = True
            self.STOP.set()
            queue = self.JOBS
        if queue is not None:
            queue.stop()

    def capabilities(self):
        try:
            sem = json.load(open(os.path.join(self.HERE, 'instr_semantics.json'), encoding='utf-8'))
        except Exception:
            sem = {}
        ins = sem.get('instructions') or {}
        ops = sorted((sem.get('ops') or {}).keys())
        return {'ok': True, 'protocol': self.PROTOCOL, 'game': self.GAME,
                'instructions': sorted(ins.keys()),
                'ops': list(ops),
                'templates': [t.spec() for t in TEMPLATES.values()],
                'limits': {'ipt_max': self.IPT_MAX, 'link_range_tiles': self.LINK_RANGE_TILES}}


    def snapshot_dump(self, req):
        """POST /snapshot -- keep one region snapshot on disk and say where it went.

        F3 in the game drags a rectangle and posts what the box contained.  P3 is
        deliberately model-free (docs/Mlog辅助-规划.md:100): the job of this endpoint is
        to prove *what the box actually contained*, so the file is the evidence, not a
        step towards code generation.
        """
        snap = req.get('snapshot')
        if not isinstance(snap, dict):
            raise ValueError('snapshot must be an object (main.js: maiSnapshot(x1,y1,x2,y2))')
        try:
            schema = int(snap.get('schema') or 0)
        except (TypeError, ValueError):
            raise ValueError('snapshot.schema must be 1')
        if schema != 1:
            raise ValueError('snapshot.schema must be 1')
        bounds = snap.get('bounds')
        if not isinstance(bounds, dict):
            raise ValueError('snapshot.bounds must be an object with x1,y1,x2,y2')
        for k in ('x1', 'y1', 'x2', 'y2'):
            v = bounds.get(k)
            if isinstance(v, bool) or not isinstance(v, int):
                raise ValueError('snapshot.bounds.%s must be an integer' % k)
        body = json.dumps(snap, ensure_ascii=False, indent=1, sort_keys=True)
        data = body.encode('utf-8')
        digest = hashlib.sha1(data).hexdigest()[:8]
        stamp = time.strftime('%Y%m%d-%H%M%S')
        os.makedirs(self.SNAP_DIR, exist_ok=True)
        path = os.path.join(self.SNAP_DIR, 'snap-%s-%s.json' % (stamp, digest))
        with open(path, 'wb') as fh:
            fh.write(data)
        return {'ok': True,
                'path': os.path.relpath(path, self.WROOT).replace('\\', '/'),
                'bytes': len(data),
                'bounds': bounds,
                'cells': int(snap.get('cells') or 0),
                'processors': len(snap.get('processors') or [])}


    def llm_state(self):
        return logic_models.public_state(self.LLM_STATE)


    def probe_model(self, req):
        return logic_models.probe_model(req, self.LLM_STATE)


    def apply_llm(self, req):
        """POST /llm -- switch the running queue between the model tier and「未配置模型」.

        v0.14.4：模板档已从产品里删掉（用户 2026-11-01），kind=template/off/none 现在
        表示「没有模型」，队列换成一个只会说「未配置模型」的 provider，不生成任何代码。
        """
        kind = str(req.get('kind') or 'llm').strip().lower()
        if kind in ('template', 'off', 'none', 'default'):
            self.LLM_STATE['kind'] = 'none'
            self.jobs_queue().provider = jobqueue.unconfigured_provider
            return self.llm_state()
        if kind not in ('llm', 'model'):
            raise ValueError('kind must be llm or none')
        url = str(req.get('url') or self.LLM_STATE['url'] or '').strip()
        if not url:
            raise ValueError('a model url is required (an OpenAI compatible /chat/completions)')
        if not (url.startswith('http://') or url.startswith('https://')):
            raise ValueError('the model url must start with http:// or https://')
        url = completion_url(url)
        model = str(req.get('model') if req.get('model') is not None else self.LLM_STATE['model']).strip()
        key = str(req.get('key') if req.get('key') is not None else self.LLM_STATE['key'])
        try:
            timeout = int(req.get('timeout') or self.LLM_STATE['timeout'] or 60)
        except (TypeError, ValueError):
            raise ValueError('timeout must be a whole number of seconds')
        if timeout < 5 or timeout > 600:
            raise ValueError('timeout must be between 5 and 600 seconds')
        try:
            max_tokens = int(req.get('max_tokens') or self.LLM_STATE.get('max_tokens')
                             or mlogprovider.DEFAULT_MAX_TOKENS)
        except (TypeError, ValueError):
            raise ValueError('max_tokens must be a whole number')
        if max_tokens < 64 or max_tokens > 64000:
            raise ValueError('max_tokens must be between 64 and 64000')
        self.LLM_STATE.update({'kind': 'llm', 'url': url, 'model': model, 'key': key,
                          'timeout': timeout, 'max_tokens': max_tokens})
        self.jobs_queue().provider = mlogprovider.HttpProvider(url, model=model, key=key,
                                                          timeout=timeout,
                                                          max_tokens=max_tokens)
        return self.llm_state()


    def job_brief(self, job):
        """A job without the parts that make a listing heavy (v0.12.5).

        The manager window lists up to fifty runs and re-reads the list every couple of
        seconds; a row only needs state, sentence, findings and timings.  The full
        record (reasoning, code, snapshot) stays one GET /jobs?id= away -- a rejected
        reasoning-model run carries ~12k characters of thinking, which is pointless to
        ship fifty times over loopback every second.
        """
        if not isinstance(job, dict):
            return job
        return {k: v for k, v in job.items() if k not in BRIEF_DROP}


    def _exe_path(self):
        """Where this process came from -- the module uses it to recognise its own build."""
        try:
            if getattr(sys, 'frozen', False):
                return os.path.abspath(sys.executable)
            return os.path.abspath(sys.argv[0] or '')
        except Exception:
            return ''


    def jobs_queue(self):
        with self.queue_lock:
            if self.closed:
                raise RuntimeError('application is closed')
            if self.JOBS is None:
                self.JOBS = jobqueue.Queue(jobqueue.Store(self.jobs_dir), workers=self.JOB_WORKERS).start()
            return self.JOBS


    def chats_store(self):
        """v0.20.0: the chat store is lazy too, so a sidecar started only for jobs
        never creates out/jobs/chats."""
        return self.chats.store()


    def serve(self, host, port, idle_exit=0):
        srv = ThreadingHTTPServer((host, port), make_handler(self))
        real = srv.server_address
        print('logicd listening on http://%s:%d' % (real[0], real[1]), flush=True)
        th = threading.Thread(target=srv.serve_forever, kwargs={'poll_interval': 0.5})
        th.daemon = True
        th.start()
        try:
            while not self.STOP.wait(0.5):
                if idle_exit > 0 and time.time() - self.LAST_PING > idle_exit:
                    # Never kill a job that is still working: a long model call can outlast
                    # the idle window on a slow endpoint, and losing it would waste the call.
                    busy = True
                    try:
                        busy = (any(j.get('state') in ('queued', 'claimed', 'running')
                                    for j in self.jobs_queue().list(None))
                                or self.chats.running() > 0)
                    except Exception:
                        busy = True
                    if not busy:
                        print('logicd idle for %d s with no ping, exiting' % idle_exit,
                              flush=True)
                        break
        except KeyboardInterrupt:
            pass
        finally:
            try:
                srv.shutdown()
            except Exception:
                pass
            srv.server_close()
