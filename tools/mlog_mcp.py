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

import hashlib
import json
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
VERSION = "0.2.0"

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
                       "Optionally writes the binary and signs the source.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": ".mlog path (default: logic)"},
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
        "name": "mlog_sim",
        "description": "Run code on the real v160.7 executor (warm server, ~0.6 s after "
                       "the first call). Returns variables, @counter and the text buffer. "
                       "Add project (a feed path) to also write the live-world projection "
                       "feed; add rt to slow it down enough to watch in-game.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": ".mlog or .msch"},
                "logic": {"type": "string", "description": "inline mlog (instead of path)"},
                "ticks": {"type": "integer", "description": "run N ticks (time-accurate)"},
                "steps": {"type": "integer", "description": "run N instructions"},
                "units": {"type": "string", "description": "e.g. 'mono:1,flare:2'"},
                "unit_pos": {"type": "string", "description": "x,y tile position"},
                "core_items": {"type": "string", "description": "e.g. 'silicon:400'"},
                "save": {"type": "string", "description": ".msav scene to load"},
                "scene": {"type": "string",
                          "description": "v1 scene JSON to load (its processors, units and "
                                         "buildings); the scene is also recorded in the "
                                         "projection feed so the world can rebuild it"},
                "project": {"type": "string",
                            "description": "feed file to write each project_every ticks "
                                           "(world_server --watch-feed reads it)"},
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


def _stash(text: str) -> dict:
    """Store *text* and return the reference record that goes in its place."""
    ref = "a" + hashlib.sha1(text.encode("utf-8", "replace")).hexdigest()[:12]
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
    if args.get("source"):
        cmd += ["--source", args["source"]]
    if args.get("logic"):
        cmd += ["--logic", args["logic"]]
    if args.get("name"):
        cmd += ["--name", args["name"]]
    for link in args.get("links") or []:
        cmd += ["--link", link]
    for b in args.get("blocks") or []:
        cmd += ["--with-block", b]
    if args.get("out"):
        cmd += ["--binary", args["out"]]
    p = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout).strip()[:2000])
    code = (p.stdout or "").strip().splitlines()[-1].strip()
    return {"blueprint_base64": code,
            "binary": args.get("out"),
            "stderr": (p.stderr or "").strip()[:500]}


def _sim_subprocess(args):
    """Advanced options (units/save/core) go through the CLI so behaviour stays
    identical to the documented command; the warm path below covers the common case."""
    root = HERE.parent
    cmd = [sys.executable, str(HERE / "mlogsim.py")]
    if args.get("path"):
        cmd.append(args["path"])
    elif args.get("logic"):
        cmd += ["--logic", args["logic"]]
    # 只有 scene: 不传程序, 场景自带处理器
    if args.get("scene"):
        cmd += ["--scene", args["scene"]]
    if args.get("ticks"):
        cmd += ["--ticks", str(int(args["ticks"]))]
    elif not args.get("scene"):
        cmd += ["--steps", str(int(args.get("steps") or 60))]
    if args.get("project"):
        cmd += ["--push", args["project"]]
        cmd += ["--push-every", str(int(args.get("project_every") or 3))]
    if args.get("rt"):
        cmd += ["--rt", str(args["rt"])]
    if args.get("units"):
        cmd += ["--units", args["units"]]
    if args.get("unit_pos"):
        cmd += ["--unit-pos", args["unit_pos"]]
    if args.get("core_items"):
        cmd += ["--core-items", args["core_items"]]
    if args.get("save"):
        cmd += ["--save", args["save"]]
    if args.get("update"):
        cmd += ["--update", args["update"]]
    if args.get("links"):
        cmd += ["--links", args["links"]]
    cmd.append("--json")
    p = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout).strip()[:2000])
    data = json.loads((p.stdout or "").strip().splitlines()[-1])
    rec = (data.get("results") or [data])[0]
    return rec


def _run_code(path: str | None, logic: str | None, args: dict):
    """Return the executor record for an inline program or a file path."""
    if path and not path.lower().endswith(".msch"):
        return None, Path(path).read_text(encoding="utf-8-sig")
    if path and path.lower().endswith(".msch"):
        return None, None
    return None, logic


def tool_sim(args):
    path = args.get("path")
    logic = args.get("logic")
    if not path and not logic and not args.get("scene"):
        raise ValueError("path, logic or scene required")
    if args.get("scene") or args.get("project"):
        # 场景/投影走 CLI: 这两条路要 Java 侧的 _scene 与 push 循环, 进程内那条
        # warm 路径只覆盖"跑一段看变量"的常见用法.
        rec = _sim_subprocess(args)
    elif any(args.get(k) for k in ("units", "unit_pos", "core_items", "save")):
        rec = _sim_subprocess(args)
    else:
        srv = _server(None)
        ticks = bool(args.get("ticks"))
        steps = int(args.get("ticks") or args.get("steps") or 60)
        update = args.get("update") or ("all" if ticks else "none")
        links = args.get("links") or "auto"
        if logic:
            rec = _sim.run_mlog(srv, "inline", logic, steps, ticks=ticks,
                                update=update, links=links)
        elif path.lower().endswith(".msch"):
            rec = _sim.run_msch(srv, path, path, steps, ticks=ticks,
                                update=update)[0]
        else:
            code = Path(path).read_text(encoding="utf-8-sig")
            rec = _sim.run_mlog(srv, path, code, steps, ticks=ticks,
                                update=update, links=links)
    text = rec.get("text") or ""
    out = {
        "vars": rec.get("vars", {}),
        "counter": rec.get("counter"),
        "text": text[:400] if len(text) <= 400 else _stash(text),
        "mode": rec.get("mode"),
        "processor": rec.get("processor"),
        "links": rec.get("links", []),
    }
    if args.get("project"):
        # 投影这条路的"下一步"是可执行的: 一条命令就能把这帧画进游戏
        feed = os.path.abspath(args["project"])
        out["projection"] = {
            "feed": feed,
            "scene": os.path.abspath(args["scene"]) if args.get("scene") else None,
            "watch": "python tools/world_server.py --watch-feed %s" % args["project"],
            "note": "the scene path travels inside the feed, so --watch-scene is optional; "
                    "start the world before or after the sim -- it attaches either way",
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


HANDLERS = {
    "mlog_doctor": tool_doctor,
    "mlog_check": tool_check,
    "mlog_ir": tool_ir,
    "mlog_values": tool_values,
    "mlog_gen": tool_gen,
    "mlog_sim": tool_sim,
    "mindcode_compile": tool_mindcode_compile,
    "mlog_validate": tool_mlog_validate,
    "mlog_task": tool_task,
    "scenario_run": tool_scenario_run,
    "mlog_diff": tool_diff,
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
