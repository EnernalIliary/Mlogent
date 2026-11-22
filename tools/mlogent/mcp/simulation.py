"""Bounded simulator invocation and MCP response shaping.

Process and input budgets are supplied by the entry point. This module does
not own server lifecycle, artifact state or concurrency controls.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
from typing import Callable, Mapping


@dataclass(frozen=True)
class SimulationContext:
    tools_root: Path
    workspace_root: Path
    workspace_input_path: Callable[[str, tuple[str, ...]], Path]
    stash: Callable[[str], dict]
    trace_vars: Callable[[list[str]], list[str]]
    run_worker: Callable[[list[str]], str]
    input_limits: Mapping[str, int]
    js_timeout: float


def projection_path(value: str, *, workspace_root: Path) -> Path:
    root = workspace_root
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


def bounded_worker(command: list[str], *, workspace_root: Path, timeout: float, result_limit: int) -> str:
    # Files avoid holding unbounded pipe data in memory and let us reap the worker
    # even if a descendant briefly survives and still holds an output descriptor.
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        proc = subprocess.Popen(command, cwd=workspace_root, stdout=stdout, stderr=stderr,
                                stdin=subprocess.DEVNULL, start_new_session=os.name != "nt")
        try:
            proc.wait(timeout=timeout)
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
            raise RuntimeError(f"simulation exceeded the {timeout:g}s wall-clock limit") from exc
        if proc.returncode:
            stderr.seek(0)
            message = stderr.read(2000).decode("utf-8", errors="replace").strip()
            raise RuntimeError(message or f"simulation exited with code {proc.returncode}")
        stdout.seek(0)
        data = stdout.read(result_limit + 1)
        if len(data) > result_limit:
            raise RuntimeError("simulation result exceeds the MCP output limit")
        return data.decode("utf-8")


def run(args, *, context: SimulationContext):
    import mlogsim as _sim
    import world_probe as _world_probe

    if "ticks" in args and "steps" in args:
        raise ValueError("choose ticks or steps")
    preview = args.get("marker_preview", False)
    if type(preview) is not bool:
        raise ValueError("marker_preview must be a boolean")
    if preview and "steps" in args:
        raise ValueError("marker_preview requires ticks")
    query = _world_probe.validate(args["world_probe"]) if "world_probe" in args else None
    if query is not None and "steps" in args:
        raise ValueError("world_probe requires ticks")
    processor = args.get("processor", "auto")
    if processor not in ("auto", "micro", "world"):
        raise ValueError("processor must be auto, micro or world")
    has_profile = "power_profile" in args
    uploaded = "scene_json" in args
    power = args.get("power", "grid" if has_profile or uploaded else "full")
    if power not in ("full", "none", "grid"):
        raise ValueError("power must be full, none or grid")
    if has_profile and power != "grid":
        raise ValueError("power_profile requires power=grid")
    ticks = "ticks" in args or ("steps" not in args and
                                bool(preview or query or args.get("project") or args.get("rt") or power == "grid" or uploaded))
    key = "ticks" if ticks else "steps"
    limit = 1200 if ticks else 2400
    names = context.trace_vars(args["trace_vars"]) if "trace_vars" in args else None
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
            if len(upload.encode("utf-8")) > context.input_limits[".json"]:
                raise ValueError("scene_json exceeds the simulation input size limit")
            upload = json.loads(upload.lstrip("\ufeff"))
        if not isinstance(upload, dict):
            raise ValueError("scene_json must be a scene JSON object or its file text")
        scene_text = json.dumps(upload, ensure_ascii=False, allow_nan=False)
        if len(scene_text.encode("utf-8")) > context.input_limits[".json"]:
            raise ValueError("scene_json exceeds the simulation input size limit")

    files = {}
    for field, suffixes in (("path", (".mlog", ".msch")), ("scene", (".json",)), ("save", (".msav",))):
        if field in args:
            value = args[field]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be a non-empty workspace path")
            path = context.workspace_input_path(value, suffixes)
            if not path.is_file():
                raise ValueError(f"{field} must name an existing regular file")
            if path.stat().st_size > context.input_limits[path.suffix.lower()]:
                raise ValueError(f"{field} exceeds the simulation input size limit")
            files[field] = path
    if (power == "grid" or uploaded) and "path" in files and files["path"].suffix.lower() == ".msch":
        raise ValueError("power=grid requires a layout with power links; use save instead of a .msch file")
    logic = args.get("logic")
    if "logic" in args and (not isinstance(logic, str) or not logic.strip()):
        raise ValueError("logic must be non-empty text")
    if logic and "path" in files:
        raise ValueError("choose logic or path")
    if "processor" in args and not (logic or ("path" in files and files["path"].suffix.lower() == ".mlog")):
        raise ValueError("processor requires inline logic or a .mlog path")
    if not logic and not uploaded and not ({"path", "scene"} & files.keys()):
        raise ValueError("path, logic, scene or scene_json required")
    if logic and len(logic.encode("utf-8")) > 100 * 1024:
        raise ValueError("inline logic exceeds the 100 KiB input limit")

    project = None
    if "project" in args:
        value = args["project"]
        if not isinstance(value, str) or not value.strip():
            raise ValueError("project must be a JSON feed path")
        project = projection_path(value, workspace_root=context.workspace_root)
    rt = args.get("rt", 0)
    if type(rt) not in (int, float) or not 0 <= rt <= 60:
        raise ValueError("rt must be between 0 and 60")
    if (project or rt) and (not ticks or ("path" in files and files["path"].suffix.lower() == ".msch")):
        raise ValueError("pacing and projection require a tick run with mlog or a scene")
    if rt and count > 60 * rt * (context.js_timeout - 5):
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
        cmd = [sys.executable, "-X", "utf8", str(context.tools_root / "mlogsim.py"),
               f"--{key}={count}", f"--js-timeout={context.js_timeout}",
               f"--workspace-root={context.workspace_root}", f"--power={power}", "--json"]
        if logic is not None or (path is not None and path.suffix.lower() == ".mlog"):
            cmd.append("--compile-diagnostics")
        preview_file = work / "markers.png"
        if preview:
            cmd.append(f"--marker-preview={preview_file}")
        if query is not None:
            probe_file = work / "world-probe.json"
            probe_file.write_text(json.dumps(query, ensure_ascii=False), encoding="utf-8")
            cmd.append(f"--world-probe={probe_file}")
        if "processor" in args:
            cmd.append(f"--processor={processor}")
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

        records = json.loads(context.run_worker(cmd))
        if not isinstance(records, list) or not records or not all(isinstance(x, dict) for x in records):
            raise RuntimeError("simulation did not return any processor results")
        trace_ref = None
        if names is not None:
            bundle = {"schema": "mlog-itrace/v1", "mlog": source, "vars": names,
                      "mode": records[0]["mode"], "tsv": trace_file.read_text(encoding="utf-8")}
            trace_ref = context.stash(json.dumps(bundle, ensure_ascii=False))
        png = preview_file.read_bytes() if preview else None
    return records, trace_ref, project, files.get("scene"), png


def simulate(args, *, run_simulation, stash, images=None):
    records, trace_ref, project, scene, png = run_simulation(args)
    rec = records[0]
    text = rec.get("text") or ""
    out = {
        "vars": rec.get("vars", {}),
        "counter": rec.get("counter"),
        "text": text[:400] if len(text) <= 400 else stash(text),
        "mode": rec.get("mode"),
        "processor": rec.get("processor"),
        "links": rec.get("links", []),
    }
    if any(key in args for key in ("power", "power_profile", "scene_json")):
        out["power"] = args.get("power", "grid")
    if trace_ref is not None:
        out["trace_ref"] = trace_ref
    if len(records) > 1:
        out["results_ref"] = stash(json.dumps(records, ensure_ascii=False))
    if rec.get("scene"):
        out["scene"] = rec["scene"]
    if rec.get("scene_probe") is not None:
        out["scene_probe"] = rec["scene_probe"]
    if "world_probe" in rec:
        out["world_probe"] = rec["world_probe"]
    for key in ("ipt", "processor_block", "compile", "executed"):
        if key in rec:
            out[key] = rec[key]
    if png is not None:
        out["marker_preview"] = rec["marker_preview"]
        if images is not None:
            images.append({"type": "image", "mimeType": "image/png",
                           "data": base64.b64encode(png).decode("ascii")})
    if project:
        out["projection"] = {
            "feed": str(project),
            "scene": str(scene) if scene else None,
            "watch": "python tools/world_server.py --watch-feed %s" % project,
        }
    return out


