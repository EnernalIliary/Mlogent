"""Command-line parsing and startup assembly for the logic sidecar."""
from __future__ import annotations

import argparse
import json
import os
import sys

import jobqueue
import mlogprovider
from logic_runtime import default_application
from logic_service import plan
from logic_templates import TEMPLATES

def build_parser():
    ap = argparse.ArgumentParser(description='local half of the in-game logic-writing service')
    ap.add_argument('--host', default='127.0.0.1', help='bind address (loopback by default)')
    ap.add_argument('--port', type=int, default=8765, help='0 = pick a free port')
    ap.add_argument('--print-template', metavar='ID', help='dump one template and exit')
    ap.add_argument('--plan', metavar='TEXT', help='route one intent, print the JSON result, exit')
    ap.add_argument('--jobs-dir', metavar='DIR',
                    help='where job files live (default out/jobs, or $MLOG_JOBS_DIR)')
    ap.add_argument('--chats-dir', metavar='DIR',
                    help='where chat files live (default <jobs-dir>/chats, or $MLOG_CHATS_DIR)')
    ap.add_argument('--jobs-provider', choices=('none', 'template', 'fake', 'llm'),
                    default='none',
                    help='none = 未配置模型, the product default since v0.14.4; '
                         'template = the offline intent router (kept for tests); '
                         'fake = test table; llm = a real model endpoint (or a recorded replay)')
    ap.add_argument('--jobs-workers', type=int, default=3, metavar='N',
                    help='how many jobs may wait on the model at once (v0.15.0; '
                         'default 3). One F3 selection used to run its jobs one by '
                         'one, so eight processors meant eight round trips in a row')
    ap.add_argument('--fake-provider', metavar='FILE',
                    help='JSON table for --jobs-provider fake: {"<desc substring>": output}')
    ap.add_argument('--llm-url', metavar='URL',
                    help='OpenAI-compatible /chat/completions URL for --jobs-provider llm')
    ap.add_argument('--llm-model', metavar='NAME', default='', help='model name to send, if any')
    ap.add_argument('--llm-key-env', metavar='VAR', default='',
                    help='env var holding the bearer token (never passed on the command line)')
    ap.add_argument('--llm-timeout', type=int, default=60, help='model call timeout in seconds')
    ap.add_argument('--llm-max-tokens', type=int, default=mlogprovider.DEFAULT_MAX_TOKENS,
                    help='reply budget per call; a reasoning model spends it on '
                         'reasoning_content before it writes anything (default %d)'
                         % mlogprovider.DEFAULT_MAX_TOKENS)
    ap.add_argument('--llm-replay', metavar='FILE',
                    help='replay recorded replies instead of calling a model (offline tests)')
    ap.add_argument('--llm-record', metavar='FILE',
                    help='append every {prompt, reply} to this JSONL file (real transcripts)')
    ap.add_argument('--idle-exit', type=int, default=0, metavar='SEC',
                    help='exit after SEC seconds without a ping and with no job in '
                         'flight (v0.15.0; the module passes 45 so a sidecar cannot '
                         'outlive the game). 0 = never')
    ap.add_argument('--jobs-drain', action='store_true',
                    help='run the queued jobs to completion, print them, exit')
    return ap


def main(argv=None, *, application=None):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    a = build_parser().parse_args(argv)
    if a.plan:
        out = plan({'intent': a.plan})
        out.pop('bytes_b64', None)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    if a.print_template:
        t = TEMPLATES.get(a.print_template)
        if t is None:
            print('unknown template %r; known: %s' % (a.print_template, ', '.join(sorted(TEMPLATES))))
            return 2
        print(t.build({})[0] and '\n'.join(t.build({})[0]))
        return 0
    app = application if application is not None else default_application()
    if getattr(sys, 'frozen', False):
        os.environ.setdefault('MLOG_JOBS_DIR', os.path.join(app.WROOT, 'out', 'jobs'))
    if a.jobs_provider == 'fake' and not a.fake_provider:
        print('--jobs-provider fake needs --fake-provider FILE')
        return 2
    try:
        provider = mlogprovider.provider_from_args(a)
    except ValueError as exc:
        print(str(exc))
        return 2
    if app.closed or app.JOBS is not None:
        raise RuntimeError('application is already configured or closed')
    app.LLM_STATE.update({'kind': a.jobs_provider if a.jobs_provider in ('llm', 'fake') else 'none',
                      'url': a.llm_url or '', 'model': a.llm_model or '',
                      'key': (os.environ.get(a.llm_key_env) if a.llm_key_env else '') or '',
                      'timeout': int(a.llm_timeout or 60),
                      'max_tokens': int(a.llm_max_tokens or mlogprovider.DEFAULT_MAX_TOKENS)})
    app.JOB_WORKERS = max(1, int(getattr(a, 'jobs_workers', None) or app.JOB_WORKERS))
    app.JOBS = jobqueue.Queue(jobqueue.Store(a.jobs_dir or app.jobs_dir), provider=provider,
                          workers=app.JOB_WORKERS)
    if getattr(a, 'chats_dir', None):
        app.chats.store(a.chats_dir)
    try:
        if a.jobs_drain:
            app.JOBS.drain()
            print(json.dumps({'ok': True, 'jobs': app.JOBS.list(None)}, ensure_ascii=False, indent=1))
            return 0
        app.JOBS.start()
        app.serve(a.host, a.port, idle_exit=max(0, int(getattr(a, 'idle_exit', 0) or 0)))
    finally:
        app.close()
    return 0
