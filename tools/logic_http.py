"""HTTP transport for the logic sidecar, with an explicitly bound application.

The application supplies queue/chat access, configuration and lifecycle hooks.
This module never imports the startup module or owns its runtime state.
"""
from __future__ import annotations

import json
import os
import time
import traceback
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from logic_service import analyse, compose, plan
from logic_links import region

class Handler(BaseHTTPRequestHandler):
    server_version = 'logicd'

    def log_message(self, fmt, *args):        # keep stdout clean for the ready line
        pass

    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _query(self):
        return {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}

    def do_GET(self):
        path = self.path.split('?')[0]
        try:
            if path == '/health':
                self.app.LAST_PING = time.time()
                self._send(200, {'ok': True, 'protocol': self.app.PROTOCOL,
                                 'version': self.app.SIDECAR_VERSION,
                                 'pid': os.getpid(), 'port': self.server.server_address[1],
                                 'exe': self.app._exe_path()})
            elif path == '/capabilities':
                self._send(200, self.app.capabilities())
            elif path == '/jobs':
                q = self._query()
                jid = q.get('id')
                if jid:
                    job = self.app.jobs_queue().get(jid)
                    if job is None:
                        self._send(404, {'ok': False, 'error': 'no such job: ' + jid})
                    else:
                        self._send(200, {'ok': True, 'job': job})
                else:
                    state = q.get('state') or None
                    if state is not None and state not in self.app.jobqueue.STATES:
                        self._send(400, {'ok': False,
                                         'error': 'state must be one of ' + ', '.join(self.app.jobqueue.STATES)})
                    else:
                        # v0.12.5: all=1 -> the job manager window's history, newest first.
                        # The rows are brief (no reasoning/code/snapshot): see job_brief.
                        want_all = str(q.get('all') or '').strip().lower() in ('1', 'true', 'yes')
                        if want_all:
                            try:
                                limit = int(q.get('limit') or 50)
                            except (TypeError, ValueError):
                                limit = 50
                            if limit < 1:
                                limit = 50
                            limit = min(limit, 200)
                            jobs = [self.app.job_brief(j) for j in
                                    self.app.jobs_queue().history(limit=limit, state=state)]
                            self._send(200, {'ok': True, 'jobs': jobs,
                                             'count': len(jobs), 'all': True})
                        else:
                            jobs = self.app.jobs_queue().list(state)
                            self._send(200, {'ok': True, 'jobs': jobs, 'count': len(jobs)})
            elif path == '/llm':
                self._send(200, self.app.llm_state())
            elif path == '/chats':
                q = self._query()
                want_all = str(q.get('all') or '').strip().lower() in ('1', 'true', 'yes')
                self._send(200, self.app.chats.list_chats(q.get('limit') or 50, want_all))
            elif path == '/chat':
                try:
                    self._send(200, self.app.chats.get_chat(self._query().get('id')))
                except self.app.chats.NotFound as exc:
                    self._send(404, {'ok': False, 'error': str(exc)})
                except ValueError as exc:
                    self._send(400, {'ok': False, 'error': str(exc)})
            else:
                self._send(404, {'ok': False, 'error': 'no such endpoint: ' + path})
        except Exception as exc:
            self._send(500, {'ok': False, 'error': '%s: %s' % (type(exc).__name__, exc)})

    def do_POST(self):
        path = self.path.split('?')[0]
        try:
            n = int(self.headers.get('Content-Length') or 0)
            if n > 4 * 1024 * 1024:
                self._send(413, {'ok': False, 'error': 'request too large'})
                return
            raw = self.rfile.read(n) if n else b'{}'
            try:
                req = json.loads(raw.decode('utf-8') or '{}')
            except Exception as exc:
                self._send(400, {'ok': False, 'error': 'bad json: %s' % exc})
                return
            if not isinstance(req, dict):
                self._send(400, {'ok': False, 'error': 'body must be a JSON object'})
                return
            if path == '/ping':
                # A live game says 'still here'; --idle-exit turns a silence into an exit.
                self.app.LAST_PING = time.time()
                self._send(200, {'ok': True, 'pid': os.getpid(),
                                 'version': self.app.SIDECAR_VERSION})
                return
            if path == '/shutdown':
                # The module retires a build it spawned itself (C1) instead of leaving a
                # stale sidecar holding the port for the next session.
                self._send(200, {'ok': True, 'bye': True, 'pid': os.getpid()})
                self.app.STOP.set()
                return
            if path == '/analyze':
                code = req.get('code')
                if not isinstance(code, str):
                    self._send(400, {'ok': False, 'error': 'code must be a string'})
                    return
                res = analyse(code, req.get('links'), ipt=int(req.get('ipt') or 2))
                self._send(200, res)
            elif path == '/compose':
                try:
                    self._send(200, compose(req))
                except ValueError as exc:
                    self._send(400, {'ok': False, 'error': str(exc)})
            elif path == '/region':
                try:
                    self._send(200, region(req))
                except ValueError as exc:
                    self._send(400, {'ok': False, 'error': str(exc)})
            elif path == '/snapshot':
                try:
                    self._send(200, self.app.snapshot_dump(req))
                except ValueError as exc:
                    self._send(400, {'ok': False, 'error': str(exc)})
            elif path == '/plan':
                try:
                    self._send(200, plan(req))
                except ValueError as exc:
                    self._send(400, {'ok': False, 'error': str(exc)})
            elif path == '/llm':
                try:
                    self._send(200, self.app.apply_llm(req))
                except ValueError as exc:
                    self._send(400, {'ok': False, 'error': str(exc)})
            elif path == '/llm/probe':
                try:
                    self._send(200, self.app.probe_model(req))
                except ValueError as exc:
                    self._send(400, {'ok': False, 'error': str(exc)})
            elif path == '/models':
                murl = str(req.get('url') or self.app.LLM_STATE['url'] or '')
                mkey = req.get('key') if req.get('key') is not None else self.app.LLM_STATE['key']
                try:
                    mto = int(req.get('timeout') or 20)
                except (TypeError, ValueError):
                    mto = 20
                try:
                    self._send(200, self.app.fetch_models(murl, mkey, mto))
                except ValueError as exc:
                    self._send(400, {'ok': False, 'error': str(exc)})
            elif path == '/chat':
                try:
                    self._send(200, self.app.chats.start(req))
                except ValueError as exc:
                    self._send(400, {'ok': False, 'error': str(exc)})
            elif path == '/jobs':
                body = req.get('job') if isinstance(req.get('job'), dict) else req
                try:
                    job, created = self.app.jobs_queue().enqueue(body)
                except ValueError as exc:
                    self._send(400, {'ok': False, 'error': str(exc)})
                else:
                    self._send(200, {'ok': True, 'id': job['id'], 'state': job['state'],
                                     'created': created, 'job': job})
            else:
                self._send(404, {'ok': False, 'error': 'no such endpoint: ' + path})
        except Exception:
            self._send(500, {'ok': False, 'error': traceback.format_exc(limit=3)})

    def do_DELETE(self):
        path = self.path.split('?')[0]
        try:
            if path == '/chat':
                try:
                    self._send(200, self.app.chats.delete_chat(self._query().get('id')))
                except self.app.chats.NotFound as exc:
                    self._send(404, {'ok': False, 'error': str(exc)})
                except ValueError as exc:
                    self._send(400, {'ok': False, 'error': str(exc)})
                return
            if path != '/jobs':
                self._send(404, {'ok': False, 'error': 'no such endpoint: ' + path})
                return
            jid = self._query().get('id')
            if not jid:
                self._send(400, {'ok': False, 'error': 'DELETE /jobs needs ?id='})
                return
            job = self.app.jobs_queue().cancel(jid)
            if job is None:
                self._send(404, {'ok': False, 'error': 'no such job: ' + jid})
            else:
                self._send(200, {'ok': True, 'id': job['id'], 'state': job['state'],
                                 'job': job})
        except Exception:
            self._send(500, {'ok': False, 'error': traceback.format_exc(limit=3)})


def make_handler(application):
    """Bind one application to a handler class, preserving per-server isolation."""
    class BoundHandler(Handler):
        app = application
        server_version = 'logicd/%s' % application.SIDECAR_VERSION

    return BoundHandler
