#!/usr/bin/env python3
"""Logic sidecar entry point and compatibility exports.

Run ``python tools/logicd.py --help`` for the CLI. New code should import
logic_service, logic_http or logic_runtime directly.
"""
from __future__ import annotations

import os
import sys

# Support direct execution and file-based imports without changing installation.
_SOURCE = os.path.dirname(os.path.abspath(__file__))
if _SOURCE not in sys.path:
    sys.path.insert(0, _SOURCE)

import mlogcheck as C          # noqa: E402
import msch                    # noqa: E402
import jobqueue                # noqa: E402  (queue calls the independent logic service)
import mlogprovider           # noqa: E402  (prompt / reply parsing / model call; offline at import)
import aigenerated             # noqa: E402  (the hidden @aigenerated signature)
import chats                   # noqa: E402  (compatibility export; app owns its state)
import logic_models
from logic_models import _mask_key, models_url, completion_url, fetch_models

# Keep the public template registry available to chats and existing callers.
from logic_templates import Template, TEMPLATES, route_intent as _route
from logic_links import (
    _link_names, _link_objects, _link_stem, _nearest_link, _substitute_links,
    _relative_links, TILESIZE, _block_sizes, _block_size, _link_base,
    _taken_numbers, _uses, _code_idents, _result_names, _known_bases,
    _mlog_words, _linkish, region,
)

from logic_service import analyse, compose, plan, _rid, SIGN_AUTHOR

from logic_runtime import SIDECAR_VERSION, default_application
from logic_http import make_handler

from logic_cli import main

__all__ = [
    'main', 'APP', 'Handler', 'analyse', 'compose', 'plan', 'region',
    'TEMPLATES', 'Template', 'SIDECAR_VERSION', 'LLM_STATE', 'STOP',
    'capabilities', 'snapshot_dump', 'llm_state', 'probe_model', 'apply_llm',
    'jobs_queue', 'chats_store', 'serve', 'job_brief',
    'models_url', 'completion_url', 'fetch_models', 'PROTOCOL', 'GAME',
    'IPT_MAX', 'LINK_RANGE_TILES', 'JOBS', 'JOB_WORKERS', 'LAST_PING',
]

_APP_METHODS = {
    'capabilities', 'snapshot_dump', 'llm_state', 'probe_model', 'apply_llm',
    'job_brief', '_exe_path', 'jobs_queue', 'chats_store', 'serve',
}
_APP_FIELDS = {
    'LLM_STATE', 'STOP', 'JOBS', 'JOB_WORKERS', 'LAST_PING', 'SNAP_DIR',
    'HERE', 'WROOT', 'PROTOCOL', 'GAME', 'IPT_MAX', 'LINK_RANGE_TILES',
}


def __getattr__(name):
    if name == 'FROZEN':
        return bool(getattr(sys, 'frozen', False))
    if name == 'APP':
        return default_application()
    if name == 'Handler':
        handler = make_handler(default_application())
        globals()['Handler'] = handler
        return handler
    if name in _APP_METHODS or name in _APP_FIELDS:
        return getattr(default_application(), name)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')


def __dir__():
    return sorted(set(globals()) | _APP_METHODS | _APP_FIELDS | set(__all__))


if __name__ == '__main__':
    sys.exit(main())
