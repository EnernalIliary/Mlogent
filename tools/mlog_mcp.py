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

import re
import threading
import hashlib
import json
import os
import subprocess  # Compatibility patch point for existing worker supervision clients.
import sys
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
_MCP_AUTHOR_CACHE = None
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from mlogent.paths import TOOLS_ROOT, WORKSPACE_ROOT  # noqa: E402
from mlogent.mcp import analysis as _analysis  # noqa: E402
from mlogent.mcp import blueprints as _blueprints  # noqa: E402
from mlogent.mcp import compilation as _compilation  # noqa: E402
from mlogent.mcp import simulation as _simulation  # noqa: E402
from mlogent.mcp import tracing as _tracing  # noqa: E402
from mlogent.mcp import tasks as _tasks  # noqa: E402
from mlogent.mcp import queries as _queries  # noqa: E402
from mlogent.mcp import experiments as _experiments  # noqa: E402

HERE = TOOLS_ROOT

import msch  # noqa: E402
import mlogsim as _sim  # noqa: E402
import world_probe as _world_probe  # noqa: E402

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
                       "Signs the embedded program when a safe slot exists, otherwise delivers unsigned "
                       "with a warning. Optionally writes a binary schematic.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": ".mlog path within the server workspace"},
                "logic": {"type": "string", "description": "inline mlog code"},
                "name": {"type": "string"},
                "author": {"type": "string", "minLength": 1,
                            "description": "author required for unsigned input with a safe signature slot; no-slot code is delivered unsigned"},
                "allow_unsigned": {"type": "boolean", "default": False,
                                   "description": "allow writing when no safe signature slot exists"},
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
                "author": {"type": "string", "minLength": 1,
                            "description": "author required when the replacement has a safe signature slot but no valid signature; no-slot code is delivered unsigned"},
                "allow_unsigned": {"type": "boolean", "default": False,
                                   "description": "allow writing when no safe signature slot exists"},
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
        "name": "marker_from_svg",
        "description": "Compile static SVG primitives into world-processor mlog. Supports line, "
                       "polyline, polygon, rect, circle, ellipse and groups with solid fills and strokes. "
                       "Send the returned mlog and preview_ticks to mlog_sim with marker_preview=true.",
        "inputSchema": {
            "type": "object", "required": ["svg"], "additionalProperties": False,
            "properties": {
                "svg": {"type": "string", "maxLength": 65536, "description": "Inline SVG XML"},
                "width": {"type": "number", "exclusiveMinimum": 0, "maximum": 1024,
                          "description": "Drawing width in tiles (default 24). Preserves aspect ratio."},
                "x": {"type": "number", "minimum": -10000, "maximum": 10000,
                      "description": "Lower-left x in tiles (default 2)"},
                "y": {"type": "number", "minimum": -10000, "maximum": 10000,
                      "description": "Lower-left y in tiles (default 2)"},
                "start_id": {"type": "integer", "minimum": 0, "maximum": 2147483647,
                             "description": "First reserved world marker ID (default 1000)"},
            },
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
                "processor": {"type": "string", "enum": ["auto", "micro", "world"],
                              "description": "Processor for standalone Mlog (default auto). Scene and blueprint processors keep their types."},
                "world_probe": _world_probe.QUERY_SCHEMA,
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
                "marker_preview": {"type": "boolean", "description":
                                   "Return final world marker state and a PNG on a tile grid. Uses ticks "
                                   "(default 60) and a world processor for standalone mlog."},
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
    root = WORKSPACE_ROOT
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
    return _analysis.check(args, programs=_programs, stash=_stash)


def tool_ir(args):
    return _analysis.ir(args, programs=_programs)


def tool_values(args):
    return _analysis.values(args, programs=_programs, stash=_stash)


def _workspace_input_path(value: str, suffixes: tuple[str, ...]) -> Path:
    root = WORKSPACE_ROOT
    path = Path(os.path.abspath(root / Path(value).expanduser()))
    if path.is_relative_to(root):
        path = path.resolve()
    if not path.is_relative_to(root) or path.suffix.lower() not in suffixes:
        raise ValueError(f"path must be a {' or '.join(suffixes)} file within the server workspace")
    return path


def _cached_author():
    return _MCP_AUTHOR_CACHE


def _cache_author(author):
    global _MCP_AUTHOR_CACHE
    _MCP_AUTHOR_CACHE = author


def _blueprint_context():
    return _blueprints.BlueprintContext(
        tools_root=HERE, workspace_root=WORKSPACE_ROOT,
        workspace_input_path=_workspace_input_path, stash=_stash,
        artifact_threshold=ARTIFACT_THRESHOLD,
        get_author=_cached_author, set_author=_cache_author,
    )


def tool_gen(args):
    return _blueprints.generate(args, context=_blueprint_context())


def tool_extract(args):
    return _blueprints.extract(args, context=_blueprint_context())


def tool_inject(args):
    return _blueprints.inject(args, context=_blueprint_context())


def tool_revision(args):
    return _blueprints.revision(args, context=_blueprint_context())


_MCP_SIM_TIMEOUT = 45.0
_MCP_SIM_JS_TIMEOUT = 30.0
_MCP_SIM_RESULT_LIMIT = 8 * 1024 * 1024
_MCP_SIM_INPUT_LIMITS = {".mlog": 100 * 1024, ".json": 2 * 1024 * 1024,
                        ".msch": 16 * 1024 * 1024, ".msav": 32 * 1024 * 1024}


def _projection_path(value: str) -> Path:
    return _simulation.projection_path(value, workspace_root=WORKSPACE_ROOT)


def _bounded_sim_worker(command: list[str]) -> str:
    return _simulation.bounded_worker(
        command, workspace_root=WORKSPACE_ROOT, timeout=_MCP_SIM_TIMEOUT,
        result_limit=_MCP_SIM_RESULT_LIMIT,
    )


def _sim_subprocess(args):
    context = _simulation.SimulationContext(
        tools_root=HERE, workspace_root=WORKSPACE_ROOT,
        workspace_input_path=_workspace_input_path, stash=_stash,
        trace_vars=_trace_vars, run_worker=_bounded_sim_worker,
        input_limits=_MCP_SIM_INPUT_LIMITS, js_timeout=_MCP_SIM_JS_TIMEOUT,
    )
    return _simulation.run(args, context=context)


def _trace_vars(names):
    return _tracing.validate_variables(names)


def tool_trace(args):
    return _tracing.trace(args, lookup_artifact=_lookup_artifact)


def tool_marker_from_svg(args):
    import marker_svg

    return marker_svg.convert(**args)


def tool_sim(args, *, images=None):
    return _simulation.simulate(args, run_simulation=_sim_subprocess, stash=_stash, images=images)


def tool_mindcode_compile(args):
    return _compilation.compile(args, stash=_stash)


def tool_mlog_validate(args):
    return _compilation.validate(args, load_programs=_programs)


def tool_task(args):
    return _tasks.task(args)


def tool_scenario_run(args):
    return _experiments.scenario_run(args)


def tool_diff(args):
    return _experiments.diff(args)


def tool_fidelity(args):
    return _queries.fidelity(args)


def tool_observe(args):
    return _experiments.observe(args, stash=_stash)


def tool_explore(args):
    return _experiments.explore(args)


def _lookup_artifact(ref):
    with _ARTIFACT_LOCK:
        return _ARTIFACTS.get(ref)


def tool_fetch(args):
    ref = args.get("ref")
    text = _lookup_artifact(ref)
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
    return _queries.knowledge(args)


HANDLERS = {
    "mlog_doctor": tool_doctor,
    "mlog_check": tool_check,
    "mlog_ir": tool_ir,
    "mlog_values": tool_values,
    "mlog_gen": tool_gen,
    "mlog_extract": tool_extract,
    "mlog_inject": tool_inject,
    "mlog_revision": tool_revision,
    "marker_from_svg": tool_marker_from_svg,
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
            arguments = params.get("arguments") or {}
            images = []
            out = fn(arguments, images=images) if fn is tool_sim else fn(arguments)
            text = json.dumps(out, ensure_ascii=False)
            return reply(rid, {"content": [{"type": "text", "text": text}, *images],
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
