#!/usr/bin/env python
"""mlog_mcp.py -- MCP (stdio) server for the mlog toolkit.

Exposes the analysis side of `mlog.py`, the real-executor simulator
(`mlogsim.py`), the Mindcode compiler front end (`mindcode.py`) and the scenario
runner (`scenario.py`) as MCP tools, so a model does not have to discover the
repo layout or pipe PowerShell output.  Everything is JSON in / JSON out.

Two conventions keep the tool surface cheap to use:

* every answer says *which stage* produced it and, on failure, *which kind* of
  failure it is (``tools/mlog_eval.py`` builds that envelope).  A model can pick
  its repair move without reading 60 findings first;
* ``level`` ("summary" | "diagnostics" | "full") is the token budget, and any
  blob that survives the trim is stored behind an ``artifact_ref`` that
  ``mlog_fetch`` hands back on demand -- large output is opt-in, not default.

Run:  python tools/mlog_mcp.py
"""
from __future__ import annotations

import base64
import re
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from bisect import bisect_right
from itertools import zip_longest
import difflib
import hashlib
import json
import signal
import os
import subprocess
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import mlogcheck as _check  # noqa: E402
import mlogir as _ir  # noqa: E402
import mlogval as _val  # noqa: E402
import msch  # noqa: E402
import mlog_eval as _eval  # noqa: E402
import mlogsim as _sim  # noqa: E402

try:  # every byte this process writes is UTF-8
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover
    pass

PROTO = "2024-11-05"
NAME = "mlog-toolkit"
VERSION = "0.4.0"

#: Blobs bigger than this are moved behind an artifact ref when the caller did
#: not ask for "full".  2 KB is roughly the point where a truncated preview
#: stops being cheaper than just reading the thing.
ARTIFACT_THRESHOLD = 2000

TOOLS = [
    {
        "name": "mlog_doctor",
        "description": "Start here. Environment check: repo root, python, JRE/server "
                       "jar, simulator readiness, and the Mindcode front end "
                       "(jar + java it will use).",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "mlog_check",
        "description": "Static analysis of mlog (.mlog, or every processor in a "
                       ".msch). One finding per line: sev, line, code, message.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": ".mlog or .msch path"},
                "cost": {"type": "boolean", "description": "also include the cost/loop report"},
                "limit": {"type": "integer",
                          "description": "max findings per program (default 20)"},
                "level": {"type": "string", "enum": ["summary", "diagnostics", "full"],
                          "description": "summary = counts only (default)"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "mlog_ir",
        "description": "Control-flow overview: statement count, unreachable statement "
                       "indices, dead stores (write never read).",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "mlog_values",
        "description": "Abstract-value report: constant branches, provable nulls, "
                       "with per-line evidence.",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "mlog_gen",
        "description": "Turn mlog source into a blueprint paste code (base64 .msch). "
                       "Signs the embedded program and optionally writes a binary schematic.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": ".mlog path within the server workspace"},
                "logic": {"type": "string", "description": "inline mlog code"},
                "name": {"type": "string"},
                "links": {"type": "array", "items": {"type": "string"},
                          "description": "name@dx,dy, relative to the processor"},
                "blocks": {"type": "array", "items": {"type": "string"},
                           "description": "block@dx,dy extra blocks"},
                "out": {"type": "string", "description": "optional .msch output path"},
            },
        },
    },
    {
        "name": "mlog_extract",
        "description": "Extract editable labelled mlog or a partial Mindcode draft. "
                       "Supply blueprint_code, mlog or a server workspace path. "
                       "For a multi-processor blueprint, omit index/all for the inventory and signed comment previews. "
                       "Use mlog_fetch for referenced output. Mindcode drafts need manual "
                       "control-flow edits before they can compile.",
        "annotations": {"readOnlyHint": True},
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "blueprint_code": {"type": "string", "description": "Mindustry blueprint paste code"},
                "mlog": {"type": "string", "description": "inline mlog source"},
                "path": {"type": "string", "description": ".msch or .mlog path inside the server workspace"},
                "index": {"type": "integer", "minimum": 0, "description": "zero-based processor index"},
                "all": {"type": "boolean", "description": "extract every processor"},
                "format": {"type": "string", "enum": ["mlog", "mindcode"], "default": "mlog"},
            },
            "oneOf": [{"required": [key]} for key in ("blueprint_code", "mlog", "path")],
            "not": {"required": ["index", "all"], "properties": {"all": {"const": True}}},
        },
    },
    {
        "name": "mlog_inject",
        "description": "Replace one processor's mlog in an existing blueprint and return a new "
                       "paste code. Use the zero-based index from mlog_extract. Preserves the "
                       "original blueprint's layout, links and other configurations. Named jumps "
                       "are resolved for delivery and their names saved in the signature payload. "
                       "Use preview to inspect the diff and checks before generating, then pass "
                       "source_sha256 back as expected_sha256 to guard against stale edits. "
                       "Successful generation stores a revision for mlog_revision.",
        "annotations": {"destructiveHint": False},
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "blueprint_code": {"type": "string", "description": "Mindustry blueprint paste code"},
                "path": {"type": "string", "description": ".msch path inside the server workspace"},
                "index": {"type": "integer", "minimum": 0, "description": "zero-based processor index"},
                "mlog": {"type": "string", "description": "complete replacement mlog, optionally with labels"},
                "preview": {"type": "boolean", "default": False,
                            "description": "validate and show the diff without generating a blueprint"},
                "expected_sha256": {"type": "string", "pattern": "^[0-9a-fA-F]{64}$",
                                    "description": "expected source_sha256 from a previous preview"},
            },
            "required": ["index", "mlog"],
            "oneOf": [{"required": ["blueprint_code"]}, {"required": ["path"]}],
        },
    },
    {
        "name": "mlog_revision",
        "description": "Read a saved mlog_inject revision and its original processor source. "
                       "With action=rollback, return the original blueprint paste code after verifying "
                       "that the supplied current blueprint exactly matches the generated revision.",
        "annotations": {"readOnlyHint": True},
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "revision": {"type": "string", "pattern": "^[0-9a-f]{32}$"},
                "action": {"enum": ["show", "rollback"], "default": "show"},
                "blueprint_code": {"type": "string", "description": "current blueprint for rollback"},
            },
            "required": ["revision"],
            "if": {"required": ["action"], "properties": {"action": {"const": "rollback"}}},
            "then": {"required": ["blueprint_code"]},
        },
    },
    {
        "name": "mlog_sim",
        "description": "Run code on the real v160.7 executor in a time-limited worker. "
                       "Returns variables, @counter and text. Use power=grid for the native grid, "
                       "or power_profile to vary external power-source output over time. Add project "
                       "to write a projection feed in the allowed output directory.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": ".mlog or .msch within the server workspace"},
                "logic": {"type": "string", "description": "inline mlog (instead of path)"},
                "ticks": {"type": "integer", "minimum": 1, "maximum": 1200},
                "steps": {"type": "integer", "minimum": 1, "maximum": 2400},
                "power": {"type": "string", "enum": ["full", "none", "grid"],
                          "description": "Building power mode. Defaults to full, or grid when power_profile is supplied."},
                "power_profile": {
                    "type": "array", "minItems": 1, "maxItems": _sim.POWER_PROFILE_MAX_POINTS,
                    "description": "Output schedule per power-source block in a loaded save or scene. "
                                   "Start at tick 1 and use strictly increasing ticks. "
                                   "A point applies before its tick's grid update and holds until the next point.",
                    "items": {
                        "type": "object", "additionalProperties": False,
                        "required": ["tick", "power_per_second"],
                        "properties": {
                            "tick": {"type": "integer", "minimum": 1, "maximum": 1200},
                            "power_per_second": {"type": "number", "minimum": 0,
                                                 "maximum": _sim.POWER_PROFILE_MAX_PER_SECOND},
                        },
                    },
                },
                "trace_vars": {"type": "array", "items": {"type": "string"}, "maxItems": 16,
                               "description": "capture an instruction trace (inline or .mlog, 1–600 ticks or 1–1200 steps)"},
                "units": {"type": "string", "description": "e.g. 'mono:1,flare:2'"},
                "unit_pos": {"type": "string", "description": "x,y tile position"},
                "core_items": {"type": "string", "description": "e.g. 'silicon:400'"},
                "save": {"type": "string", "description": ".msav scene to load"},
                "scene": {"type": "string",
                          "description": "v1 scene JSON to load (its processors, units and "
                                         "buildings); the scene is also recorded in the "
                                         "projection feed so the world can rebuild it"},
                "scene_json": {
                    "oneOf": [{"type": "object"}, {"type": "string"}],
                    "description": "Upload a self-contained v1 scene as a JSON object or file text. "
                                   "Defaults to grid mode and adds a power-source to the selected grid.",
                },
                "power_target": {"type": "string", "minLength": 1, "maxLength": 128,
                                 "description": "Uploaded scene building name. Required when there are multiple consumer grids."},
                "project": {"type": "string",
                            "description": "JSON feed under out/_proj or out/_world/feeds, or out/_world/feed.json"},
                "project_every": {"type": "integer",
                                  "description": "feed refresh period in ticks (default 3)"},
                "rt": {"type": "number",
                       "description": "realtime pacing: 1 = 60 ticks/s (watchable), "
                                      "3 = 3x faster; omit to run flat out"},
                "update": {"type": "string", "enum": ["all", "none"]},
                "links": {"type": "string", "enum": ["auto", "off"]},
            },
            "required": [],
        },
    },
    {
        "name": "mlog_trace",
        "description": "Inspect a saved instruction trace by label and variable. Compare against "
                       "another trace to find the first change in tick, program counter or watched "
                       "values. Use mlog_sim(trace_vars=...) to capture live-executor traces.",
        "annotations": {"readOnlyHint": True},
        "inputSchema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "trace_ref": {"type": "string", "description": "artifact_ref from mlog_sim"},
                "trace": {"type": "string", "description": "raw --itrace TSV"},
                "mlog": {"type": "string", "description": "source for labelling an uploaded TSV"},
                "label": {"type": "string", "description": "return rows from the named label section"},
                "vars": {"type": "array", "items": {"type": "string"}, "maxItems": 16},
                "baseline_ref": {"type": "string"},
                "baseline_trace": {"type": "string"},
                "offset": {"type": "integer", "minimum": 0, "default": 0},
                "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 40},
            },
            "oneOf": [{"required": ["trace_ref"]}, {"required": ["trace"]}],
            "not": {"required": ["baseline_ref", "baseline_trace"]},
        },
    },
    {
        "name": "mindcode_compile",
        "description": "Compile Mindcode (.mnd, the high-level language) to mlog. Returns "
                       "the mlog plus file:line:col diagnostics; nothing is written to "
                       "disk unless you pass out. Pass map:true to also get the "
                       "mlog->source line map.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "inline Mindcode source"},
                "path": {"type": "string", "description": ".mnd file (instead of source)"},
                "target": {"type": "string",
                           "description": "Mindustry target version, default 7.0"},
                "optimize": {"type": "boolean", "description": "run the optimizer (default true)"},
                "out": {"type": "string", "description": "optional .mlog output path"},
                "map": {"type": "boolean",
                        "description": "also return an mlog line -> .mnd line map "
                                       "(inferred by prefix compilation; loop bodies stay "
                                       "unmapped on purpose)"},
                "level": {"type": "string", "enum": ["summary", "diagnostics", "full"]},
            },
        },
    },
    {
        "name": "mlog_validate",
        "description": "One call that answers \"does this work?\": static analysis, then "
                       "(optionally) a real run, then your expectations. Returns a single "
                       "verdict with a failure_type and the next step.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": ".mlog or .msch"},
                "logic": {"type": "string", "description": "inline mlog"},
                "mind": {"type": "string",
                         "description": "inline Mindcode (.mnd); compiled first, then validated"},
                "mnd_path": {"type": "string", "description": "a .mnd file to compile first"},
                "target": {"type": "string", "description": "Mindustry target for Mindcode, default 7.0"},
                "ticks": {"type": "integer",
                          "description": "also run this many ticks on the executor"},
                "expect": {"type": "array", "description": "list of {var, op, value}",
                           "items": {"type": "object"}},
                "level": {"type": "string", "enum": ["summary", "diagnostics", "full"]},
                "task": {"type": "string",
                         "description": "task id to record this run into (see mlog_task); "
                                        "omit the id to derive one from the source"},
                "task_id": {"type": "string",
                            "description": "alias of task, kept for callers that name it "
                                           "after the plan's field"},
                "hypothesis": {"type": "string", "description": "stored on the task record"},
                "next_step": {"type": "string", "description": "stored on the task record"},
            },
        },
    },
    {
        "name": "mlog_task",
        "description": "Task progress that survives between turns: what already ran, what "
                       "failed, what to try next. Read it before re-validating, so a retry "
                       "resumes at the stage that failed instead of redoing the pipeline.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["show", "list", "resume", "note", "clear"],
                           "description": "show=one record, list=all, resume=what is left, "
                                          "note=set hypothesis/next_step, clear=delete"},
                "task_id": {"type": "string", "description": "task id (ts-...)"},
                "source": {"type": "string",
                           "description": "resume: the current program text, to detect that "
                                          "the record was measured on a different source"},
                "hypothesis": {"type": "string"},
                "next_step": {"type": "string"},
            },
            "required": ["action"],
        },
    },
    {
        "name": "scenario_run",
        "description": "Run a scenario file (scenes/scenarios/*.json: world + program + "
                       "observations + assertions) and evaluate its assertions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "scenario .json path"},
                "via": {"type": "string", "enum": ["sim", "world"]},
                "level": {"type": "string", "enum": ["summary", "diagnostics", "full"]},
            },
            "required": ["path"],
        },
    },
    {
        "name": "mlog_diff",
        "description": "Run one scenario on the offline executor and on the live game "
                       "world (python tools/world_server.py), then diff the two "
                       "observations. Differences carry the fidelity verdict that "
                       "explains them (tools/fidelity.py).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "scenario .json path"},
                "spec": {"type": "object",
                         "description": "optional per-section compare rules; see "
                                        "docs/观察与差分-契约.md for the shape"},
                "level": {"type": "string", "enum": ["summary", "diagnostics", "full"]},
            },
            "required": ["path"],
        },
    },
    {
        "name": "mlog_fidelity",
        "description": "The fidelity boundary: which capabilities the offline executor "
                       "actually reproduces, and which differences are explained by a "
                       "known boundary. action=list returns the 15-row table, "
                       "action=show takes one capability name, action=explain takes a "
                       "difference ({path,left,right}) and names the boundary it falls "
                       "in -- or returns null, which means the difference is real.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "show", "explain"],
                           "description": "default list"},
                "capability": {"type": "string",
                               "description": "for action=show, e.g. unit-motion"},
                "difference": {"type": "object",
                               "description": "for action=explain: {path,left,right}"},
            },
        },
    },
    {
        "name": "mlog_observe",
        "description": "Compare two observations (mlog-observation/v1 JSON files) with "
                       "the four rule kinds: exact, tolerance, match, ordered events. "
                       "Use it on what differential_run wrote, or on two runs of your "
                       "own. Notes are differences that do not change the verdict.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "a": {"type": "string", "description": "path to the left observation"},
                "b": {"type": "string", "description": "path to the right observation"},
                "spec": {"type": "object",
                         "description": "optional per-section rule overrides"},
                "level": {"type": "string", "enum": ["summary", "diagnostics", "full"]},
            },
            "required": ["a", "b"],
        },
    },
    {
        "name": "mlog_explore",
        "description": "Enumerate scenario variants and keep the failures. action=list "
                       "shows the templates and their knobs; action=run evaluates the "
                       "cartesian product of seeds x modifier bundles (each point is a "
                       "fresh scenario), stops at limit, and with shrink=true reduces "
                       "the first failure to the smallest bundle that still fails.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "run"],
                           "description": "default list"},
                "template": {"type": "string",
                             "description": "unit-control or resource-drain"},
                "seeds": {"type": "array", "items": {"type": "integer"},
                          "description": "one point per seed, default [1]"},
                "params": {"type": "object",
                           "description": "template knobs; list shows the names"},
                "modifiers": {"type": "array",
                              "description": "one bundle (list of modifiers) per point"},
                "via": {"type": "string", "enum": ["sim", "world"], "description": "default sim"},
                "limit": {"type": "integer",
                          "description": "stop after this many failures, default 1"},
                "shrink": {"type": "boolean",
                           "description": "reduce the first failure to a minimal repro"},
            },
        },
    },
    {
        "name": "mlog_kb",
        "description": "Keyword search over knowledge/ (130+ articles: mechanics, "
                       "numbers, source anchors) and optionally docs/. No embeddings, "
                       "no index build: pure lexical BM25 over heading sections, so it "
                       "works on a bare deployment. Use it to check a fact before you "
                       "write mlog (what a block is called in Chinese, tick budgets, "
                       "why a link variable reads null).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "what to look for"},
                "k": {"type": "integer", "description": "hits, default 6"},
                "kind": {"type": "string", "enum": ["knowledge", "all"],
                         "description": "knowledge = articles only (default); "
                                        "all = also docs/ (evidence and entry docs)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "mlog_fetch",
        "description": "Read an artifact that a previous call replaced with an "
                       "artifact_ref (large traces/variable dumps). Optional byte window.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ref": {"type": "string"},
                "offset": {"type": "integer", "description": "byte offset, default 0"},
                "limit": {"type": "integer", "description": "max bytes, default 40000"},
            },
            "required": ["ref"],
        },
    },
]

#: ref -> the text it stands for.  Bounded so a long session cannot grow without
#: limit; the oldest entry is dropped (the caller can always rerun the tool).
_ARTIFACTS: dict[str, str] = {}
_ARTIFACT_ORDER: list[str] = []
_ARTIFACT_MAX = 32
_ARTIFACT_LOCK = threading.Lock()


def _stash(text: str) -> dict:
    """Store *text* and return the reference record that goes in its place."""
    ref = "a" + hashlib.sha1(text.encode("utf-8", "replace")).hexdigest()[:12]
    with _ARTIFACT_LOCK:
        if ref not in _ARTIFACTS:
            _ARTIFACTS[ref] = text
            _ARTIFACT_ORDER.append(ref)
            while len(_ARTIFACT_ORDER) > _ARTIFACT_MAX:
                _ARTIFACTS.pop(_ARTIFACT_ORDER.pop(0), None)
    return {"artifact_ref": ref, "bytes": len(text),
            "preview": text[:200].replace("\n", " ")[:200],
            "how": "call mlog_fetch with this ref"}


_SRV = None
_SRV_KEY = None


def _server(save: str | None):
    global _SRV, _SRV_KEY
    key = save or ""
    if _SRV is not None and _SRV_KEY == key:
        _SRV.reset_world()
        return _SRV
    if _SRV is not None:
        try:
            _SRV.close()
        except Exception:
            pass
    _SRV = _sim.Server(_sim._default_java(), _sim._default_jar(),
                       save=save or None)
    _SRV_KEY = key
    return _SRV


def _programs(path: str):
    p = Path(path)
    if p.suffix.lower() == ".msch":
        sch = msch.parse_file(str(p))
        for t in sch.logic_tiles():
            assert t.logic is not None
            yield (f"{path} [{t.block} @({t.x},{t.y})]",
                   t.logic.code.split("\n"),
                   [l.name for l in t.logic.links])
    else:
        yield path, p.read_text(encoding="utf-8-sig").split("\n"), None


def tool_doctor(_args):
    root = HERE.parent
    jar = root / "out" / "_server160.jar"
    jre = root / "out" / "jre21" / "jdk-21.0.5+11-jre" / "bin" / "java.exe"
    try:
        import mindcode as _mnd
        mnd = _mnd.locate()
    except Exception as exc:                 # noqa: BLE001 -- optional module
        mnd = {"ok": False, "notes": ["mindcode.py unavailable: %s" % exc]}
    # A differential run needs the live world too, and the only honest answer to
    # "is it up?" is to ask it -- the handshake file survives a crashed daemon.
    try:
        import world_client as _wc
        st = _wc.call({"op": "status"}) or {}
        world = {"ok": bool(st.get("map") or st.get("paused") is not None),
                 "map": st.get("map"), "paused": st.get("paused")}
    except Exception as exc:                 # noqa: BLE001 -- optional rig
        world = {"ok": False, "notes": ["world server not running: %s: %s"
                                        % (type(exc).__name__, exc)]}
    try:
        import cache as _cache
        cache = {"enabled": _cache.enabled(), "root": _cache.default_dir()}
        cache.update({k: _cache.stats()[k] for k in ("entries", "bytes")})
    except Exception as exc:                 # noqa: BLE001 -- optional module
        cache = {"enabled": False, "notes": ["cache.py unavailable: %s" % exc]}
    # `mlog_kb` reads Markdown; a deployment without knowledge/ pays for the tool
    # but gets an honest zero, so say which of the two it is.
    kb_root = root / "knowledge"
    try:
        import kb_grep as _kbg
        kb = {"present": kb_root.is_dir(), "root": str(kb_root),
              "sections": len(_kbg.load(str(kb_root))) if kb_root.is_dir() else 0}
    except Exception as exc:                 # noqa: BLE001 -- optional data
        kb = {"present": False, "notes": ["knowledge/ unavailable: %s" % exc]}
    return {
        "repo": str(root),
        "entry": str(HERE / "mlog.py"),
        "python": "%d.%d.%d" % sys.version_info[:3],
        "stdout_utf8": True,
        "server_jar": jar.exists(),
        "jre21": jre.exists(),
        "sim_ready": jar.exists() and jre.exists(),
        "mindcode": mnd,
        "world": world,
        "differential_ready": jar.exists() and jre.exists() and bool(world["ok"]),
        "cache": cache,
        "knowledge": kb,
        "commands": [
            "python tools/mlog.py check FILE --cost",
            "python tools/mlog.py ir FILE",
            "python tools/mlog.py values FILE",
            "python tools/mlog.py gen --source FILE --name demo",
            "python tools/mlogsim.py FILE --ticks 120 --update all",
            "python tools/mindcode.py compile FILE.mnd -o FILE.mlog",
            "python tools/scenario.py run scenes/scenarios/unit-control.json",
            "python tools/differential.py run scenes/scenarios/unit-control.json",
            "MLOG_CACHE=1 python tools/cache.py stats     (opt-in result cache)",
        ],
    }


def tool_check(args):
    level = args.get("level") or "summary"
    limit = int(args.get("limit") or (20 if level == "summary" else 200))
    out = []
    for label, lines, names in _programs(args["path"]):
        fs = _check.analyse(lines, names)
        counts = {s: sum(1 for f in fs if f.sev == s)
                  for s in ("ERR", "SUSPECT", "WARN", "INFO")}
        rec = {"program": label, "counts": counts}
        if level != "summary":
            findings = [{"sev": f.sev, "line": f.line, "code": f.code, "msg": f.msg}
                        for f in fs]
            if len(findings) > limit:
                rec["findings"] = findings[:limit]
                rec["more"] = _stash(json.dumps(findings[limit:], ensure_ascii=False))
            else:
                rec["findings"] = findings
        if args.get("cost"):
            cost = _check.cost_report(_check.prepare(lines), names)
            cost = cost if isinstance(cost, str) else str(cost)
            rec["cost"] = cost[:4000] if level == "full" else _stash(cost)
        out.append(rec)
    return out


def tool_ir(args):
    out = []
    for label, lines, names in _programs(args["path"]):
        prog = _ir.parse(lines)
        out.append({
            "program": label,
            "statements": len(prog.stmts),
            "unreachable": prog.dead()[:80],
            "dead_stores": [{"line": i + 1, "name": n}
                            for i, n in prog.dead_stores()[:60]],
        })
    return out


def tool_values(args):
    out = []
    for label, lines, names in _programs(args["path"]):
        prog = _ir.parse(lines)
        st = _val.analyze(prog)
        report = _val.format_report(label, prog, st)
        out.append({"program": label,
                    "report": report[:5000] if len(report) <= 5000 else _stash(report)})
    return out


def tool_gen(args):
    root = HERE.parent
    cmd = [sys.executable, str(HERE / "mlog.py"), "gen"]
    source, logic = args.get("source"), args.get("logic")
    if bool(source) == bool(logic):
        raise ValueError("provide exactly one of source or logic")
    if source:
        logic = _workspace_input_path(source, (".mlog",)).read_text(encoding="utf-8-sig")
    if args.get("name"):
        cmd += ["--name", args["name"]]
    for link in args.get("links") or []:
        cmd += ["--link", link]
    for b in args.get("blocks") or []:
        cmd += ["--with-block", b]
    if args.get("out"):
        cmd += ["--binary", args["out"]]
    p = subprocess.run(cmd, cwd=str(root), input=logic, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout).strip()[:2000])
    code = (p.stdout or "").strip().splitlines()[-1].strip()
    return {"blueprint_base64": code,
            "binary": args.get("out"),
            "stderr": (p.stderr or "").strip()[:500]}


def _workspace_input_path(value: str, suffixes: tuple[str, ...]) -> Path:
    root = HERE.parent
    path = Path(os.path.abspath(root / Path(value).expanduser()))
    if path.is_relative_to(root):
        path = path.resolve()
    if not path.is_relative_to(root) or path.suffix.lower() not in suffixes:
        raise ValueError(f"path must be a {' or '.join(suffixes)} file within the server workspace")
    return path


def _blueprint_bytes(code: str) -> bytes:
    return base64.b64decode("".join(code.lstrip("\ufeff").split()), validate=True)


def tool_extract(args):
    from mindcode import DecompileError
    from mlog import decode_logic_input, logic_programs, render_extracted_logic

    inputs = [key for key in ("blueprint_code", "mlog", "path") if key in args]
    if len(inputs) != 1:
        raise ValueError("provide exactly one of blueprint_code, mlog, or path")
    key = inputs[0]
    value = args[key]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")

    output_format = args.get("format", "mlog")
    if output_format not in ("mlog", "mindcode"):
        raise ValueError("format must be mlog or mindcode")
    index = args.get("index")
    all_programs = args.get("all", False)
    if "index" in args and (type(index) is not int or index < 0):
        raise ValueError("index must be a non-negative integer")
    if type(all_programs) is not bool:
        raise ValueError("all must be a boolean")
    if index is not None and all_programs:
        raise ValueError("choose index or all, not both")

    if key == "blueprint_code":
        schematic, text = msch.parse_bytes(_blueprint_bytes(value)), None
    elif key == "mlog":
        schematic, text = None, value.lstrip("\ufeff")
    else:
        path = _workspace_input_path(value, (".msch", ".mlog"))
        schematic, text = decode_logic_input(path.read_bytes(), expect_schematic=path.suffix.lower() == ".msch")

    programs = logic_programs(schematic, text)
    count = len(programs)
    response = {"ok": True, "format": output_format, "total": count}
    if schematic is not None:
        response["blueprint"] = {"name": schematic.name, "width": schematic.width, "height": schematic.height}
    if index is not None and index >= count:
        raise ValueError(f"index {index} exceeds the number of processors ({count})")
    if not count or (count > 1 and index is None and not all_programs):
        from aigenerated import extract_text, verify_text

        inventory = []
        for info, code in programs:
            entry = dict(info)
            if "aigenerated:" in code and not verify_text(code):
                comments = extract_text(code)
                if comments:
                    entry["comment_preview"] = [
                        {"line": item["line"], "text": item["text"][:160]}
                        for item in comments[:2]
                    ]
            inventory.append(entry)
        return {**response, "mode": "inventory", "processors": inventory}

    selected = programs[index:index + 1] if index is not None else programs
    result = []
    for info, code in selected:
        try:
            draft, diagnostic = render_extracted_logic(code, format=output_format)
        except DecompileError as exc:
            return {**response, "ok": False, "index": info["index"],
                    "failure_type": exc.kind, "message": str(exc)}
        detail = {**info, "code": draft}
        if diagnostic:
            detail["diagnostic"] = diagnostic
        result.append(detail)

    response.update(mode="extract", processors=result)
    if output_format == "mindcode":
        response["note"] = "Partial decompilation; control flow may need manual rewriting before compilation."
    # A batch uses a single reference, so it cannot evict its own earlier outputs.
    if sum(len(item["code"].encode("utf-8")) for item in result) > ARTIFACT_THRESHOLD:
        if len(result) == 1:
            result[0]["code_ref"] = _stash(result[0].pop("code"))
        else:
            codes = [{"index": item["index"], "code": item.pop("code")} for item in result]
            response["programs_ref"] = {"encoding": "json", **_stash(json.dumps(codes, ensure_ascii=False))}
    return response


def _inject_review_source(code: str) -> str:
    import aigenerated
    from mlog import render_extracted_logic

    try:
        labelled, _ = render_extracted_logic(code)
    except (ValueError, aigenerated.SignError):
        # An existing malformed signature should not prevent fixing the program.
        labelled = code
    return aigenerated._body(labelled) if aigenerated._find(labelled) else labelled


def _inject_checks(target: msch.LogicCodeTarget, code: str) -> dict:
    from mschgen import block_size

    links = target.tile.logic.links
    ipt = {"micro-processor": 2, "logic-processor": 8, "hyper-processor": 25,
           "world-processor": 8}.get(target.tile.block, 2)
    findings = _check.analyse(code.splitlines(), [link.name for link in links],
                              ipt=ipt, links_authoritative=True)
    diagnostics = [{"severity": f.sev, "line": f.line, "code": f.code, "message": f.msg,
                    "rule_id": f.rid} for f in findings]
    checks = {
        "counts": {severity: sum(f.sev == severity for f in findings)
                   for severity in ("ERR", "SUSPECT", "WARN", "INFO")},
        "findings": diagnostics,
    }

    # Parsed msch links are already absolute. Include multi-tile footprints,
    # and describe absence from the blueprint rather than claiming runtime null.
    wanted = {(link.x, link.y) for link in links}
    targets = {}
    for tile in target.schematic.tiles if wanted else ():
        size = block_size(tile.block)
        half = (size - 1) // 2
        for x in range(tile.x - half, tile.x - half + size):
            for y in range(tile.y - half, tile.y - half + size):
                if (x, y) in wanted:
                    targets[x, y] = tile.block
    checks["links"] = [
        {"name": link.name, "x": link.x, "y": link.y,
         "target_block": targets.get((link.x, link.y)),
         "in_blueprint": (link.x, link.y) in targets}
        for link in links
    ]
    return checks


def _revision_path(revision: str) -> Path:
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{32}", revision):
        raise ValueError("revision must be a 32-digit lowercase hex ID")
    directory = os.environ.get("MLOG_REVISION_DIR")
    root = Path(directory).expanduser() if directory else HERE.parent / "out" / "_mlog_revisions"
    return root / f"{revision}.json"


def _write_revision(original: bytes, updated: bytes, info: dict, diff: str, checks: dict) -> str:
    revision = uuid.uuid4().hex
    path = _revision_path(revision)
    record = {
        "schema": "mlog-revision/v1", "revision": revision,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "before_blueprint_sha256": hashlib.sha256(original).hexdigest(),
        "after_blueprint_sha256": hashlib.sha256(updated).hexdigest(),
        **info, "diff": diff, "checks": checks,
        "before_blueprint": base64.b64encode(original).decode("ascii"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, encoding="utf-8", mode="w",
                                     prefix=".revision-", delete=False) as stream:
        temp = Path(stream.name)
        try:
            json.dump(record, stream, ensure_ascii=False)
            stream.close()
            temp.replace(path)
        finally:
            stream.close()
            temp.unlink(missing_ok=True)
    return revision


def _review_fields(response: dict, diff: str, checks: dict) -> None:
    if len(diff.encode("utf-8")) > ARTIFACT_THRESHOLD:
        response["diff_ref"] = _stash(diff)
    else:
        response["diff"] = diff
    diagnostics = checks["findings"]
    response["checks"] = {**checks, "findings": diagnostics[:20]}
    if len(diagnostics) > 20:
        response["checks"]["findings_ref"] = _stash(json.dumps(diagnostics, ensure_ascii=False))


def tool_revision(args):
    revision = args.get("revision")
    action = args.get("action", "show")
    if action not in ("show", "rollback"):
        raise ValueError("action must be show or rollback")
    current = args.get("blueprint_code")
    if action == "rollback" and (not isinstance(current, str) or not current.strip()):
        raise ValueError("rollback requires the current blueprint_code")
    try:
        record = json.loads(_revision_path(revision).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError("revision not found") from exc
    if record.get("schema") != "mlog-revision/v1" or record.get("revision") != revision:
        raise ValueError("unrecognized or mismatched revision record")
    original_code = record.pop("before_blueprint")
    original = _blueprint_bytes(original_code)
    if hashlib.sha256(original).hexdigest() != record["before_blueprint_sha256"]:
        raise ValueError("revision's original blueprint failed its integrity check")
    diff, checks = record.pop("diff"), record.pop("checks")
    response = {"ok": True, **record}
    if action == "rollback":
        if hashlib.sha256(_blueprint_bytes(current)).hexdigest() != record["after_blueprint_sha256"]:
            return {"ok": False, "revision": revision, "failure_type": "blueprint_conflict",
                    "message": "current blueprint differs from this revision's generated blueprint"}
        response["blueprint_base64"] = original_code
    else:
        target = msch.logic_code_target(original, record["processor"]["index"])
        code = target.tile.logic.code
        if len(code.encode("utf-8")) > ARTIFACT_THRESHOLD:
            response["original_mlog_ref"] = _stash(code)
        else:
            response["original_mlog"] = code
    _review_fields(response, diff, checks)
    return response


def tool_inject(args):
    from aigenerated import DEFAULT_AUTHOR, sign_delivery
    from mlog import logic_programs

    inputs = [key for key in ("blueprint_code", "path") if key in args]
    if len(inputs) != 1:
        raise ValueError("provide exactly one of blueprint_code or path")
    key = inputs[0]
    value = args[key]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    index = args.get("index")
    if type(index) is not int or index < 0:
        raise ValueError("index must be a non-negative integer")
    source = args.get("mlog")
    if not isinstance(source, str) or not source.lstrip("\ufeff").strip():
        raise ValueError("mlog must be a non-empty replacement program")
    preview = args.get("preview", False)
    if type(preview) is not bool:
        raise ValueError("preview must be a boolean")
    expected = args.get("expected_sha256")
    if "expected_sha256" in args and (
            not isinstance(expected, str) or len(expected) != 64
            or any(c not in "0123456789abcdefABCDEF" for c in expected)):
        raise ValueError("expected_sha256 must be a 64-digit hexadecimal SHA-256")

    if key == "path":
        data = _workspace_input_path(value, (".msch",)).read_bytes()
        if not data.startswith(msch.MAGIC):
            data = _blueprint_bytes(data.decode("utf-8-sig"))
    else:
        data = _blueprint_bytes(value)

    target = msch.logic_code_target(data, index)
    original = target.tile.logic.code
    source_sha256 = hashlib.sha256(target.original_code_bytes).hexdigest()
    response = {
        "ok": True,
        "mode": "preview" if preview else "apply",
        "processor": logic_programs(target.schematic, None)[index][0],
        "source_sha256": source_sha256,
    }
    if expected is not None and expected.lower() != source_sha256:
        return {**response, "ok": False, "failure_type": "source_conflict",
                "message": "processor source changed; extract or preview it again"}

    code, _, _, _ = sign_delivery(source.lstrip("\ufeff"), DEFAULT_AUTHOR)
    updated = target.replace(code, preview=preview)
    before = _inject_review_source(original).splitlines()
    after = _inject_review_source(code)
    diff = "\n".join(difflib.unified_diff(before, after.splitlines(),
                                         fromfile="original.mlog", tofile="replacement.mlog",
                                         lineterm=""))
    response["replacement_sha256"] = hashlib.sha256(code.encode("utf-8")).hexdigest()
    checks = _inject_checks(target, after)
    if updated is not None:
        info = {key: response[key] for key in ("processor", "source_sha256", "replacement_sha256")}
        response["revision"] = _write_revision(data, updated, info, diff, checks)
        response["blueprint_base64"] = base64.b64encode(updated).decode("ascii")
    _review_fields(response, diff, checks)
    return response


_MCP_SIM_TIMEOUT = 45.0
_MCP_SIM_JS_TIMEOUT = 30.0
_MCP_SIM_RESULT_LIMIT = 8 * 1024 * 1024
_MCP_SIM_INPUT_LIMITS = {".mlog": 100 * 1024, ".json": 2 * 1024 * 1024,
                        ".msch": 16 * 1024 * 1024, ".msav": 32 * 1024 * 1024}


def _projection_path(value: str) -> Path:
    root = HERE.parent
    path = Path(os.path.abspath(root / Path(value).expanduser()))
    if path.is_relative_to(root):
        path = path.resolve()
    relative = path.relative_to(root) if path.is_relative_to(root) else None
    if (relative is None or path.suffix.lower() != ".json"
            or (relative != Path("out/_world/feed.json")
                and not any(relative.is_relative_to(folder) and relative != folder
                            for folder in (Path("out/_proj"), Path("out/_world/feeds"))))):
        raise ValueError("project must be a JSON feed in out/_proj, out/_world/feeds or out/_world/feed.json")
    return path


def _bounded_sim_worker(command: list[str]) -> str:
    # Files avoid holding unbounded pipe data in memory and let us reap the worker
    # even if a descendant briefly survives and still holds an output descriptor.
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        proc = subprocess.Popen(command, cwd=HERE.parent, stdout=stdout, stderr=stderr,
                                stdin=subprocess.DEVNULL, start_new_session=os.name != "nt")
        try:
            proc.wait(timeout=_MCP_SIM_TIMEOUT)
        except subprocess.TimeoutExpired as exc:
            try:
                if os.name == "nt":
                    # The simulator owns a KILL_ON_JOB_CLOSE job for its JVM.
                    proc.kill()
                else:
                    os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait(timeout=3)
            raise RuntimeError(f"simulation exceeded the {_MCP_SIM_TIMEOUT:g}s wall-clock limit") from exc
        if proc.returncode:
            stderr.seek(0)
            message = stderr.read(2000).decode("utf-8", errors="replace").strip()
            raise RuntimeError(message or f"simulation exited with code {proc.returncode}")
        stdout.seek(0)
        data = stdout.read(_MCP_SIM_RESULT_LIMIT + 1)
        if len(data) > _MCP_SIM_RESULT_LIMIT:
            raise RuntimeError("simulation result exceeds the MCP output limit")
        return data.decode("utf-8")


def _sim_subprocess(args):
    if "ticks" in args and "steps" in args:
        raise ValueError("choose ticks or steps")
    has_profile = "power_profile" in args
    uploaded = "scene_json" in args
    power = args.get("power", "grid" if has_profile or uploaded else "full")
    if power not in ("full", "none", "grid"):
        raise ValueError("power must be full, none or grid")
    if has_profile and power != "grid":
        raise ValueError("power_profile requires power=grid")
    ticks = "ticks" in args or ("steps" not in args and
                                bool(args.get("project") or args.get("rt") or power == "grid" or uploaded))
    key = "ticks" if ticks else "steps"
    limit = 1200 if ticks else 2400
    names = _trace_vars(args["trace_vars"]) if "trace_vars" in args else None
    if names is not None:
        limit = 600 if ticks else 1200
        if "ticks" not in args and "steps" not in args:
            ticks, key, limit = True, "ticks", 600
    count = args.get(key, 60)
    if type(count) is not int or not 1 <= count <= limit:
        raise ValueError(f"simulation {key} must be between 1 and {limit}")
    if power == "grid" and (not ticks or args.get("update", "all") != "all"):
        raise ValueError("power=grid requires a tick run with update=all")
    profile = _sim.validate_power_profile(args["power_profile"], count) if has_profile else None
    target = args.get("power_target")
    if "power_target" in args and (not uploaded or power != "grid"
            or not isinstance(target, str) or not target.strip() or len(target) > 128
            or not target.isprintable()):
        raise ValueError("power_target requires scene_json in grid mode and a printable building name")
    if uploaded:
        if any(key in args for key in ("scene", "save", "project")):
            raise ValueError("scene_json cannot be combined with scene, save or project")
        upload = args["scene_json"]
        if isinstance(upload, str):
            if len(upload.encode("utf-8")) > _MCP_SIM_INPUT_LIMITS[".json"]:
                raise ValueError("scene_json exceeds the simulation input size limit")
            upload = json.loads(upload.lstrip("\ufeff"))
        if not isinstance(upload, dict):
            raise ValueError("scene_json must be a scene JSON object or its file text")
        scene_text = json.dumps(upload, ensure_ascii=False, allow_nan=False)
        if len(scene_text.encode("utf-8")) > _MCP_SIM_INPUT_LIMITS[".json"]:
            raise ValueError("scene_json exceeds the simulation input size limit")

    files = {}
    for field, suffixes in (("path", (".mlog", ".msch")), ("scene", (".json",)), ("save", (".msav",))):
        if field in args:
            value = args[field]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be a non-empty workspace path")
            path = _workspace_input_path(value, suffixes)
            if not path.is_file():
                raise ValueError(f"{field} must name an existing regular file")
            if path.stat().st_size > _MCP_SIM_INPUT_LIMITS[path.suffix.lower()]:
                raise ValueError(f"{field} exceeds the simulation input size limit")
            files[field] = path
    if (power == "grid" or uploaded) and "path" in files and files["path"].suffix.lower() == ".msch":
        raise ValueError("power=grid requires a layout with power links; use save instead of a .msch file")
    logic = args.get("logic")
    if "logic" in args and (not isinstance(logic, str) or not logic.strip()):
        raise ValueError("logic must be non-empty text")
    if logic and "path" in files:
        raise ValueError("choose logic or path")
    if not logic and not uploaded and not ({"path", "scene"} & files.keys()):
        raise ValueError("path, logic, scene or scene_json required")
    if logic and len(logic.encode("utf-8")) > 100 * 1024:
        raise ValueError("inline logic exceeds the 100 KiB input limit")

    project = None
    if "project" in args:
        value = args["project"]
        if not isinstance(value, str) or not value.strip():
            raise ValueError("project must be a JSON feed path")
        project = _projection_path(value)
    rt = args.get("rt", 0)
    if type(rt) not in (int, float) or not 0 <= rt <= 60:
        raise ValueError("rt must be between 0 and 60")
    if (project or rt) and (not ticks or ("path" in files and files["path"].suffix.lower() == ".msch")):
        raise ValueError("pacing and projection require a tick run with mlog or a scene")
    if rt and count > 60 * rt * (_MCP_SIM_JS_TIMEOUT - 5):
        raise ValueError("realtime pacing exceeds the MCP simulation budget; use fewer ticks or a faster rt")
    if names is not None and (project or rt or uploaded or "scene" in files or "save" in files
            or any(args.get(k) for k in ("units", "unit_pos", "core_items"))
            or ("path" in files and files["path"].suffix.lower() != ".mlog")):
        raise ValueError("trace_vars supports inline or .mlog input without scene options")
    every = args.get("project_every", 3)
    if project and (type(every) is not int or not 1 <= every <= 1200):
        raise ValueError("project_every must be between 1 and 1200")
    units = args.get("units")
    if units is not None:
        if not isinstance(units, str) or len(units) > 1024:
            raise ValueError("units must be text of at most 1024 characters")
        quantities = []
        for spec in units.split(","):
            name, separator, number = spec.strip().partition(":")
            if not name or (separator and (not number.isascii() or not number.isdigit() or len(number) > 2)):
                raise ValueError("units must use positive counts, e.g. flare:2")
            quantities.append(int(number) if separator else 1)
        if not all(quantities) or sum(quantities) > 64:
            raise ValueError("at most 64 units can be spawned per simulation")

    for field, limit in (("unit_pos", 64), ("core_items", 1024)):
        if field in args and (not isinstance(args[field], str) or len(args[field]) > limit):
            raise ValueError(f"{field} must be text of at most {limit} characters")
    for field, choices in (("update", ("all", "none")), ("links", ("auto", "off"))):
        if field in args and args[field] not in choices:
            raise ValueError(f"{field} must be {' or '.join(choices)}")

    with tempfile.TemporaryDirectory(prefix="mlog-mcp-sim-") as directory:
        work = Path(directory)
        path = files.get("path")
        if logic is not None:
            path = work / "inline.mlog"
            path.write_text(logic.lstrip("\ufeff"), encoding="utf-8", newline="\n")
        cmd = [sys.executable, "-X", "utf8", str(HERE / "mlogsim.py"),
               f"--{key}={count}", f"--js-timeout={_MCP_SIM_JS_TIMEOUT}",
               f"--workspace-root={HERE.parent}", f"--power={power}", "--json"]
        if profile is not None:
            cmd.append("--power-profile=" + json.dumps(profile, allow_nan=False, separators=(",", ":")))
        if uploaded:
            scene_file = work / "scene.json"
            scene_file.write_text(scene_text, encoding="utf-8")
            cmd.append(f"--uploaded-scene={scene_file}")
            if target is not None:
                cmd.append(f"--power-target={target}")
        for field in ("scene", "save"):
            if field in files:
                cmd.append(f"--{field}={files[field]}")
        for arg_name, flag in (("units", "units"), ("unit_pos", "unit-pos"), ("core_items", "core-items"),
                               ("update", "update"), ("links", "links")):
            if args.get(arg_name) is not None:
                cmd.append(f"--{flag}={args[arg_name]}")
        if rt:
            cmd.append(f"--rt={rt}")
        if project:
            project.parent.mkdir(parents=True, exist_ok=True)
            cmd.extend([f"--push={project}", f"--push-every={every}"])
        trace_file = work / "trace.tsv"
        source = None
        if names is not None:
            cmd.append(f"--itrace={trace_file}")
            cmd.extend(f"--itrace-var={name}" for name in names)
            source = path.read_text(encoding="utf-8-sig")
        if path is not None:
            cmd.extend(["--", str(path)])

        records = json.loads(_bounded_sim_worker(cmd))
        if not isinstance(records, list) or not records or not all(isinstance(x, dict) for x in records):
            raise RuntimeError("simulation did not return any processor results")
        trace_ref = None
        if names is not None:
            bundle = {"schema": "mlog-itrace/v1", "mlog": source, "vars": names,
                      "mode": records[0]["mode"], "tsv": trace_file.read_text(encoding="utf-8")}
            trace_ref = _stash(json.dumps(bundle, ensure_ascii=False))
    return records, trace_ref, project, files.get("scene")


def _run_code(path: str | None, logic: str | None, args: dict):
    """Return the executor record for an inline program or a file path."""
    if path and not path.lower().endswith(".msch"):
        return None, Path(path).read_text(encoding="utf-8-sig")
    if path and path.lower().endswith(".msch"):
        return None, None
    return None, logic


def _trace_vars(names) -> list[str]:
    if (not isinstance(names, list) or len(names) > 16
            or any(not isinstance(name, str) or not name or len(name) > 100
                   or any(c in name for c in "=;\t\r\n") for name in names)
            or len(set(names)) != len(names)):
        raise ValueError("trace variables must be a list of up to 16 distinct names")
    return names


def _trace_rows(text: str, source: str | None):
    captured = set()
    mode = None
    if text.lstrip().startswith("{"):
        bundle = json.loads(text)
        if bundle.get("schema") != "mlog-itrace/v1":
            raise ValueError("artifact is not an instruction trace")
        text = bundle["tsv"]
        source = source if source is not None else bundle["mlog"]
        captured.update(bundle["vars"])
        mode = bundle.get("mode")
    lines = iter(text.lstrip("\ufeff").rstrip("\r\n").split("\n"))
    if next(lines, "").rstrip("\r") != "tick\tpc\tvars\tsource":
        raise ValueError("expected an instruction trace TSV with tick, pc, vars, and source columns")

    # Group aliases at each exact target and use the preceding target as the section.
    program = _ir.parse(source.splitlines()) if source is not None else None
    by_pc = {}
    if program is not None:
        for name, pc in program.labels.items():
            by_pc.setdefault(pc, []).append(name)
    boundaries = sorted(by_pc)
    rows = []
    for raw in lines:
        try:
            tick, pc, variables, instruction = raw.rstrip("\r").split("\t", 3)
            row = {"step": len(rows), "tick": int(tick), "pc": int(pc), "source": instruction,
                   "vars": dict(item.split("=", 1) for item in variables.split(";") if item)}
        except ValueError as exc:
            raise ValueError(f"invalid instruction trace row {len(rows) + 2}") from exc
        captured.update(row["vars"])
        if program is not None and 0 <= row["pc"] < len(program.stmts):
            stmt = program.stmts[row["pc"]]
            # Do not attach a source line to a row that was captured from different code.
            if instruction.strip() in (stmt.raw.strip(), stmt.raw[:512].strip()):
                row["line"] = stmt.line
                section = bisect_right(boundaries, row["pc"]) - 1
                row["labels"] = by_pc[boundaries[section]] if section >= 0 else []
        rows.append(row)
    return rows, captured, mode


def _trace_argument(args: dict, inline: str, reference: str, *, required: bool) -> str | None:
    if inline in args and reference in args:
        raise ValueError(f"choose {inline} or {reference}")
    if reference in args:
        ref = args[reference]
        with _ARTIFACT_LOCK:
            result = _ARTIFACTS.get(ref) if isinstance(ref, str) else None
        if result is None:
            raise ValueError(f"unknown trace reference {ref!r}")
        return result
    if inline in args:
        if not isinstance(args[inline], str):
            raise ValueError(f"{inline} must be text")
        return args[inline]
    if required:
        raise ValueError(f"provide {inline} or {reference}")
    return None


def tool_trace(args):
    source = args.get("mlog")
    label = args.get("label")
    if source is not None and not isinstance(source, str):
        raise ValueError("mlog must be text")
    rows, captured, mode = _trace_rows(_trace_argument(args, "trace", "trace_ref", required=True), source)
    baseline = _trace_argument(args, "baseline_trace", "baseline_ref", required=False)
    variables = _trace_vars(args["vars"]) if "vars" in args else sorted(captured)
    missing = set(variables) - captured
    if missing:
        raise ValueError(f"variables not captured: {', '.join(sorted(missing))}")
    if label is not None and (not isinstance(label, str) or not label.strip()):
        raise ValueError("label must be a non-empty name")
    offset, limit = args.get("offset", 0), args.get("limit", 40)
    if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 200:
        raise ValueError("offset must be non-negative and limit must be between 1 and 200")

    def project(row):
        if row is None:
            return None
        return {**row, "vars": {name: row["vars"].get(name) for name in variables}}

    selected = [row for row in rows if label is None or label in row.get("labels", ())]
    page = selected[offset:offset + limit]
    result = {"total": len(rows), "matched": len(selected), "rows": [project(row) for row in page],
              "next_offset": offset + len(page) if offset + len(page) < len(selected) else None,
              "variables": variables,
              "labels": list(dict.fromkeys(name for row in rows for name in row.get("labels", ())))}
    if mode is not None:
        result["mode"] = mode
    if baseline is not None:
        previous, previous_vars, previous_mode = _trace_rows(baseline, None)
        if mode and previous_mode and mode != previous_mode:
            raise ValueError("compare traces captured in the same simulation mode")
        missing = set(variables) - previous_vars
        if missing:
            raise ValueError(f"variables not captured in baseline: {', '.join(sorted(missing))}")
        def state(row):
            if row is None:
                return None
            return row["tick"], row["pc"], tuple(row["vars"].get(name) for name in variables)

        divergence = None
        for step, (before, after) in enumerate(zip_longest(previous, rows)):
            if state(before) != state(after):
                divergence = {"step": step, "baseline": project(before), "current": project(after)}
                break
        result["first_divergence"] = divergence
    return result


def tool_sim(args):
    records, trace_ref, project, scene = _sim_subprocess(args)
    rec = records[0]
    text = rec.get("text") or ""
    out = {
        "vars": rec.get("vars", {}),
        "counter": rec.get("counter"),
        "text": text[:400] if len(text) <= 400 else _stash(text),
        "mode": rec.get("mode"),
        "processor": rec.get("processor"),
        "links": rec.get("links", []),
    }
    if any(key in args for key in ("power", "power_profile", "scene_json")):
        out["power"] = args.get("power", "grid")
    if trace_ref is not None:
        out["trace_ref"] = trace_ref
    if len(records) > 1:
        out["results_ref"] = _stash(json.dumps(records, ensure_ascii=False))
    if rec.get("scene"):
        out["scene"] = rec["scene"]
    if rec.get("scene_probe") is not None:
        out["scene_probe"] = rec["scene_probe"]
    if project:
        out["projection"] = {
            "feed": str(project),
            "scene": str(scene) if scene else None,
            "watch": "python tools/world_server.py --watch-feed %s" % project,
        }
    return out


def _read_text(path):
    with open(path, encoding="utf-8-sig") as fh:
        return fh.read()


def _compile_artifacts(res, level, out):
    """The compiled mlog is the deliverable; in summary mode it travels as a
    reference so the envelope stays small but nothing is lost."""
    artifacts = {"stats": res.get("stats"), "tool": res.get("tool")}
    if out:
        artifacts["out"] = out
    code = res.get("mlog") or ""
    if code:
        if level == "summary":
            artifacts["mlog_ref"] = _stash(code)
        else:
            artifacts["mlog"] = code
    return {k: v for k, v in artifacts.items() if v is not None}


def tool_mindcode_compile(args):
    import mindcode as _mnd
    level = args.get("level") or "diagnostics"
    if args.get("source"):
        res = _mnd.compile_source(args["source"],
                                  target=args.get("target") or "7.0",
                                  optimize=args.get("optimize", True))
    elif args.get("path"):
        # compile_file keeps the caller's path in diagnostics (better than
        # "<source>") and owns the BOM/encoding handling, so the two entry
        # points cannot drift apart.
        res = _mnd.compile_file(args["path"], target=args.get("target") or "7.0",
                                optimize=args.get("optimize", True))
    else:
        raise ValueError("source or path required")
    if res.get("ok") and args.get("out"):
        Path(args["out"]).write_text(res["mlog"], encoding="utf-8")
    failed = not res.get("ok")
    failure = None
    if failed:
        # A missing/incompatible compiler is not a fault in the user's source:
        # say so instead of blaming their code.
        tool = res.get("tool") or {}
        failure = ("compilation_error" if tool.get("jar") and tool.get("java")
                   else "unsupported_environment")
    _map = None
    if args.get("map"):
        # 源码映射是推断出来的，不塞进信封（信封只回答「成没成」），作为单独的键
        # 返回：没接上的行带原因，读的人自己判断信不信。
        # 映射固定用 optimize=False：优化器正是会把「想标位置的语句」删掉的那一步，
        # 开着它去对齐，等于拿删干净的输出找原句。
        try:
            import sourcemap as _sm
            src = args.get("source") or _read_text(args["path"])
            built = _sm.build_from_text(src, target=args.get("target") or "7.0",
                                        optimize=False)
            if built.get("ok"):
                entries = [{"mlog": m["mlog"], "mnd_line": m["mnd_line"], "why": m["why"]}
                           for m in built.get("map") or [] if m["mlog"] is not None]
                unmapped = [{"mnd_line": m["mnd_line"], "why": m["why"]}
                            for m in built.get("map") or [] if m["mlog"] is None]
                _map = {"schema": built.get("schema"),
                              "mapped": len(entries), "unmapped": len(unmapped),
                              "entries": entries[:200], "unmapped_why": unmapped[:20],
                              "note": "prefix alignment, optimize=False; "
                                      "control-flow bodies stay unmapped by design"}
            else:
                _map = {"ok": False, "diagnostics": built.get("diagnostics") or []}
        except Exception as exc:      # noqa: BLE001 -- never fail a compile over a map
            _map = {"ok": False, "error": str(exc)}
    env = _eval.result(
        ok=not failed, stage="compilation", failure_type=failure,
        message="" if not failed else (res.get("diagnostics") or
                                       [{"message": "compilation failed"}])[0].get("message", ""),
        diagnostics=res.get("diagnostics") or [],
        artifacts=_compile_artifacts(res, level, args.get("out")),
        level=level, elapsed_ms=res.get("elapsed_ms"),
    )
    if _map is not None:
        env["map"] = _map
    return env


def _compile_mind(args):
    """Mindcode source -> mlog, or a finished failure envelope.

    This is the whole point of having a compiler in the loop: an agent writes
    .mnd, and the same call that compiles it also says whether the *compiled*
    program is right.  A compilation failure is reported as such (stage
    "compilation"), never as a static or simulation failure.
    """
    import mindcode as _mnd
    if args.get("mind"):
        res = _mnd.compile_source(args["mind"], target=args.get("target") or "7.0",
                                  optimize=args.get("optimize", True))
    else:
        res = _mnd.compile_file(args["mnd_path"], target=args.get("target") or "7.0",
                                optimize=args.get("optimize", True))
    if res.get("ok"):
        return res["mlog"], None
    tool = res.get("tool") or {}
    return None, _eval.result(
        ok=False, stage="compilation",
        failure_type=("compilation_error" if tool.get("jar") and tool.get("java")
                      else "unsupported_environment"),
        message=(res.get("diagnostics") or [{"message": "compilation failed"}])[0].get("message", ""),
        diagnostics=res.get("diagnostics") or [],
        artifacts={"stats": res.get("stats"), "tool": tool},
        level=args.get("level") or "summary", elapsed_ms=res.get("elapsed_ms"))


def tool_mlog_validate(args):
    level = args.get("level") or "summary"
    path, logic = args.get("path"), args.get("logic")
    mind = args.get("mind") or args.get("mnd_path")
    if not path and not logic and not mind:
        raise ValueError("path, logic or mind required")
    if mind:
        logic, failed = _compile_mind(args)
        if failed is not None:
            return failed
    programs = []
    if path:
        programs = [(label, "\n".join(lines), names)
                    for label, lines, names in _programs(path)]
    else:
        programs = [("inline", logic, None)]
    import taskstate as _ts
    tid = args.get("task") or args.get("task_id")
    task = None
    if tid or args.get("hypothesis") or args.get("next_step"):
        # One task per program: a batch that shares an id would overwrite the
        # stages of the previous program with the next one's.
        first = programs[0][1] if programs else ""
        task = _ts.begin(task_id=tid or None, source=first,
                         hypothesis=args.get("hypothesis") or "",
                         next_step=args.get("next_step") or "")
    results = []
    for label, code, _names in programs:
        limits = {"ticks": int(args["ticks"])} if args.get("ticks") else {}
        env = _eval.evaluate(mlog=code, limits=limits,
                             expectations=args.get("expect") or None,
                             level=level, task=task)
        env["program"] = label
        results.append(env)
    if len(results) == 1:
        return results[0]
    ok = all(r.get("ok") for r in results)
    failed = [r for r in results if not r.get("ok")]
    # A batch is only as good as its weakest dimension: carry the per-program
    # levels up so a caller can see "compiles everywhere, wrong in two".
    levels = {}
    for k in _eval.SUCCESS_LEVELS:
        seen = [r["levels"][k] for r in results if (r.get("levels") or {}).get(k) is not None]
        levels[k] = (False if False in seen else (True if seen else None))
    return _eval.result(
        ok=ok, stage="assertion" if ok else failed[0].get("stage", "static"),
        failure_type=None if ok else failed[0].get("failure_type"),
        message="" if ok else "%d of %d program(s) failed" % (len(failed), len(results)),
        diagnostics=[d for r in failed for d in (r.get("diagnostics") or [])],
        artifacts={"programs": [{k: r.get(k) for k in ("program", "ok", "stage",
                                                       "failure_type", "message")}
                                for r in results]},
        level=level, levels=levels, task=_eval._ts_summary(task))


def tool_task(args):
    import taskstate as _ts
    action = args.get("action") or "list"
    tid = args.get("task_id")
    if action == "list":
        rows = []
        for one in _ts.ids():
            try:
                task = _ts.load(one)
            except Exception:                # noqa: BLE001 -- half-written file
                continue
            if task:
                rows.append({"task_id": one, "source_version": task.get("source_version"),
                             "completed": task.get("completed_stages") or [],
                             "failed": task.get("failed_stages") or [],
                             "next_step": task.get("next_step") or "",
                             "updated": task.get("updated")})
        return {"dir": _ts.default_dir(), "count": len(rows), "tasks": rows}
    if action == "clear":
        return {"removed": _ts.clear(tid)}
    if not tid:
        raise ValueError("task_id required for action=%r" % action)
    if action == "resume":
        return _ts.resume(tid, source=args.get("source"))
    if action == "note":
        task = _ts.note(tid, hypothesis=args.get("hypothesis"),
                        next_step=args.get("next_step"))
        return _ts.summary_of(task)
    if action == "show":
        task = _ts.load(tid)
        if task is None:
            raise ValueError("no such task: %s" % tid)
        return task
    raise ValueError("unknown action %r (show|list|resume|note|clear)" % action)


def tool_scenario_run(args):
    import scenario as _scen
    level = args.get("level") or "summary"
    sc = _scen.load(args["path"])
    return _scen.run(sc, via=args.get("via") or "sim", level=level)


def tool_diff(args):
    import differential as _diff
    return _diff.run(args["path"], spec=args.get("spec"),
                     level=args.get("level") or "summary")


def tool_fidelity(args):
    import fidelity as _fid
    action = args.get("action") or "list"
    if action == "show":
        name = args.get("capability")
        got = _fid.lookup(name or "")
        if got is None:
            raise ValueError("unknown capability %r (action=list shows the names)" % name)
        return got
    if action == "explain":
        diff = args.get("difference") or {}
        if not isinstance(diff, dict):
            raise ValueError("difference must be an object {path,left,right}")
        line = _fid.annotate(diff)
        if line is None:
            return {"capability": None, "explained": False,
                    "note": "no known boundary covers this difference: treat it as real"}
        name = str(line).split(" (", 1)[0]
        return {"capability": name, "explained": True, "line": line,
                "detail": _fid.lookup(name)}
    table = _fid.load()
    rows = table.get("entries") or []
    counts: dict[str, int] = {}
    for row in rows:
        v = row.get("verdict") or "unknown"
        counts[v] = counts.get(v, 0) + 1
    return {"count": len(rows), "counts": counts,
            "capabilities": [{"name": r.get("id"), "verdict": r.get("verdict"),
                              "scope": r.get("scope"), "note": r.get("note")}
                             for r in rows]}


def tool_observe(args):
    import observation as _obs
    a = _load_json(args["a"])
    b = _load_json(args["b"])
    got = _obs.compare(a, b, spec=args.get("spec"))
    level = args.get("level") or "diagnostics"
    if level == "summary":
        diffs = got.get("differences") or []
        return {"same": got.get("same"), "count": len(diffs),
                "unexplained": sum(1 for d in diffs if not d.get("explained")),
                "notes": got.get("notes") or [], "level": "summary"}
    text = json.dumps(got, ensure_ascii=False)
    if len(text) > 2000 and level != "full":
        got = dict(got)
        got["differences_ref"] = _stash(json.dumps(got.pop("differences") or [],
                                                   ensure_ascii=False, indent=1))
    return got


def tool_explore(args):
    import explore as _xp
    action = args.get("action") or "list"
    if action == "list":
        return _xp.catalogue() if hasattr(_xp, "catalogue") else _explore_catalogue()
    points = _xp.space(args.get("template") or "unit-control",
                       seeds=tuple(args.get("seeds") or (1,)),
                       params=args.get("params"),
                       modifiers=args.get("modifiers"))
    got = _xp.explore(points, via=args.get("via") or "sim",
                      limit=int(args.get("limit") or 1))
    summ = got.get("summary") or {}
    out = {"template": args.get("template") or "unit-control",
           "ran": summ.get("ran") or got.get("ran"),
           "points": summ.get("points") or got.get("points"),
           "failed": summ.get("failed"),
           "skipped": summ.get("skipped"),
           "ok": summ.get("ok")}
    fails = got.get("failures") or []
    out["failures"] = [{"seed": (f.get("point") or {}).get("seed"),
                        "failure_type": f.get("failure_type"),
                        "next_step": f.get("next_step")} for f in fails[:8]]
    if args.get("shrink") and fails:
        first = fails[0]
        shr = _xp.shrink(first["point"], via=args.get("via") or "sim")
        pt = shr.get("point") or {}
        out["shrunk"] = {
            "seed": pt.get("seed"),
            "kept": sorted(m.get("kind") for m in (pt.get("modifiers") or [])),
            "dropped": shr.get("dropped"),
            "still_fails": shr.get("still_fails"),
        }
    return out


def _explore_catalogue():
    import scenario as _scen
    rows = []
    for name in _scen.TEMPLATE_ORDER:
        rows.append({"template": name,
                     "knobs": sorted((_scen.TEMPLATE_PARAMS.get(name) or {}).keys())})
    return {"templates": rows,
            "note": "action=run takes template + seeds (+ optional params/modifiers); "
                    "each seed x modifier bundle is one fresh generated scenario"}


def _load_json(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def tool_fetch(args):
    ref = args.get("ref")
    with _ARTIFACT_LOCK:
        text = _ARTIFACTS.get(ref)
    if text is None:
        raise ValueError("unknown artifact ref %r (re-run the tool that produced it)"
                         % ref)
    off = int(args.get("offset") or 0)
    lim = int(args.get("limit") or 40000)
    chunk = text[off:off + lim]
    return {"ref": ref, "bytes": len(text), "offset": off,
            "next_offset": off + len(chunk) if off + len(chunk) < len(text) else None,
            "text": chunk}


def tool_kb(args):
    """Lexical retrieval.  `kb.py` is the better index; this one runs anywhere."""
    import kb_grep
    query = (args.get("query") or "").strip()
    if not query:
        raise ValueError("query is required")
    k = max(1, min(int(args.get("k") or 6), 20))
    kind = args.get("kind") or "knowledge"
    hits = kb_grep.search(query, k=k, include_docs=(kind == "all"))
    return {"count": len(hits), "mode": "keyword",
            "note": "BM25 over knowledge/ sections, no embeddings. For semantic "
                    "search with rerank use tools/kb.py locally.",
            "hits": hits}


HANDLERS = {
    "mlog_doctor": tool_doctor,
    "mlog_check": tool_check,
    "mlog_ir": tool_ir,
    "mlog_values": tool_values,
    "mlog_gen": tool_gen,
    "mlog_extract": tool_extract,
    "mlog_inject": tool_inject,
    "mlog_revision": tool_revision,
    "mlog_sim": tool_sim,
    "mlog_trace": tool_trace,
    "mindcode_compile": tool_mindcode_compile,
    "mlog_validate": tool_mlog_validate,
    "mlog_task": tool_task,
    "scenario_run": tool_scenario_run,
    "mlog_diff": tool_diff,
    "mlog_kb": tool_kb,
    "mlog_fetch": tool_fetch,
    "mlog_fidelity": tool_fidelity,
    "mlog_observe": tool_observe,
    "mlog_explore": tool_explore,
}


def _write_stdout(msg):
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _reply(rid, result=None, error=None, *, sink=None):
    msg = {"jsonrpc": "2.0", "id": rid}
    if error is not None:
        msg["error"] = error
    else:
        msg["result"] = result
    (sink or _write_stdout)(msg)
    return msg


def handle(req, emit=None):
    """Dispatch one JSON-RPC request.

    `emit` defaults to writing the reply to stdout (the stdio transport).  The
    HTTP transport passes a collector instead, so the same dispatch serves both
    and there is no second copy of the method table.
    """
    method = req.get("method")
    rid = req.get("id")
    sink = emit

    def reply(*args, **kwargs):                    # bind the transport once
        return _reply(*args, sink=sink, **kwargs)
    if method == "initialize":
        return reply(rid, {
            "protocolVersion": PROTO,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": NAME, "version": VERSION},
        })
    if method == "notifications/initialized":
        return
    if method == "ping":
        return reply(rid, {})
    if method == "tools/list":
        return reply(rid, {"tools": TOOLS})
    if method == "tools/call":
        params = req.get("params") or {}
        name = params.get("name")
        fn = HANDLERS.get(name)
        if fn is None:
            return reply(rid, error={"code": -32602, "message": f"unknown tool {name}"})
        try:
            out = fn(params.get("arguments") or {})
            text = json.dumps(out, ensure_ascii=False)
            return reply(rid, {"content": [{"type": "text", "text": text}],
                                "isError": False})
        except Exception as exc:  # report, do not crash the server
            return reply(rid, {"content": [{"type": "text",
                                             "text": "%s: %s" % (type(exc).__name__, exc)}],
                                "isError": True})
    if rid is None:
        return
    return reply(rid, error={"code": -32601, "message": f"method not found: {method}"})


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            handle(req)
        except Exception:
            traceback.print_exc(file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
