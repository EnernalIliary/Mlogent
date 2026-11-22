"""Blueprint MCP adapters: generate, extract, inject and durable revisions.

Protocol dispatch, artifact cache and author state belong to the entry point.
Dependencies are passed per call, so this module never imports the server.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timezone
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Callable
import uuid

import mlogcheck as _check
import msch


@dataclass(frozen=True)
class BlueprintContext:
    tools_root: Path
    workspace_root: Path
    workspace_input_path: Callable[[str, tuple[str, ...]], Path]
    stash: Callable[[str], dict]
    artifact_threshold: int
    get_author: Callable[[], str | None]
    set_author: Callable[[str], None]


def generate(args, *, context: BlueprintContext):
    root = context.workspace_root
    cmd = [sys.executable, str(context.tools_root / "mlog.py"), "gen"]
    source, logic = args.get("source"), args.get("logic")
    import aigenerated
    supplied_author = str(args.get("author") or "").strip()
    if bool(source) == bool(logic):
        raise ValueError("provide exactly one of source or logic")
    if source:
        logic = context.workspace_input_path(source, (".mlog",)).read_text(encoding="utf-8-sig")
    existing = aigenerated._find(logic)
    if existing and aigenerated.verify_text(logic):
        raise ValueError("input contains an invalid signature")
    signed_author = existing[0].group(1) if existing else ""
    author = signed_author or supplied_author or context.get_author()
    allow_unsigned = bool(args.get("allow_unsigned", False))
    if not author and not allow_unsigned:
        raise ValueError("author is required when mlog has no valid signature")
    if supplied_author:
        context.set_author(supplied_author)
    if args.get("name"):
        cmd += ["--name", args["name"]]
    if author:
        cmd += ["--author", author]
    if allow_unsigned and not existing:
        cmd += ["--no-sign"]
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
    signed = bool(existing) or (bool(author) and not allow_unsigned)
    return {"blueprint_base64": code, "signed": signed,
            "warning": None if signed else "no signature requested",
            "binary": args.get("out"),
            "stderr": (p.stderr or "").strip()[:500]}


def _blueprint_bytes(code: str) -> bytes:
    return base64.b64decode("".join(code.lstrip("\ufeff").split()), validate=True)


def extract(args, *, context: BlueprintContext):
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
        path = context.workspace_input_path(value, (".msch", ".mlog"))
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
            if "AI-Generated:Mlogent:" in code and not verify_text(code):
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
    if sum(len(item["code"].encode("utf-8")) for item in result) > context.artifact_threshold:
        if len(result) == 1:
            result[0]["code_ref"] = context.stash(result[0].pop("code"))
        else:
            codes = [{"index": item["index"], "code": item.pop("code")} for item in result]
            response["programs_ref"] = {"encoding": "json", **context.stash(json.dumps(codes, ensure_ascii=False))}
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


def _revision_path(revision: str, context: BlueprintContext) -> Path:
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{32}", revision):
        raise ValueError("revision must be a 32-digit lowercase hex ID")
    directory = os.environ.get("MLOG_REVISION_DIR")
    root = Path(directory).expanduser() if directory else context.workspace_root / "out" / "_mlog_revisions"
    return root / f"{revision}.json"


def _write_revision(original: bytes, updated: bytes, info: dict, diff: str, checks: dict, context: BlueprintContext) -> str:
    revision = uuid.uuid4().hex
    path = _revision_path(revision, context)
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


def _review_fields(response: dict, diff: str, checks: dict, context: BlueprintContext) -> None:
    if len(diff.encode("utf-8")) > context.artifact_threshold:
        response["diff_ref"] = context.stash(diff)
    else:
        response["diff"] = diff
    diagnostics = checks["findings"]
    response["checks"] = {**checks, "findings": diagnostics[:20]}
    if len(diagnostics) > 20:
        response["checks"]["findings_ref"] = context.stash(json.dumps(diagnostics, ensure_ascii=False))


def revision(args, *, context: BlueprintContext):
    revision = args.get("revision")
    action = args.get("action", "show")
    if action not in ("show", "rollback"):
        raise ValueError("action must be show or rollback")
    current = args.get("blueprint_code")
    if action == "rollback" and (not isinstance(current, str) or not current.strip()):
        raise ValueError("rollback requires the current blueprint_code")
    try:
        record = json.loads(_revision_path(revision, context).read_text(encoding="utf-8"))
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
        if len(code.encode("utf-8")) > context.artifact_threshold:
            response["original_mlog_ref"] = context.stash(code)
        else:
            response["original_mlog"] = code
    _review_fields(response, diff, checks, context)
    return response


def inject(args, *, context: BlueprintContext):
    from aigenerated import sign_delivery
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
        data = context.workspace_input_path(value, (".msch",)).read_bytes()
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

    import aigenerated
    supplied_author = str(args.get("author") or "").strip()
    existing = aigenerated._find(source)
    if existing and aigenerated.verify_text(source):
        raise ValueError("replacement contains an invalid signature")
    signed_author = existing[0].group(1) if existing else ""
    author = signed_author or supplied_author or context.get_author()
    allow_unsigned = bool(args.get("allow_unsigned", False))
    if not author and not allow_unsigned:
        raise ValueError("author is required when replacement has no valid signature")
    if supplied_author:
        context.set_author(supplied_author)
    signed = True
    try:
        code, _, _, _ = sign_delivery(source.lstrip("\ufeff"), author)
    except aigenerated.SignError as exc:
        if not allow_unsigned or "no safe signature slot" not in str(exc):
            raise
        code, _, _ = aigenerated.resolve_labels(source.lstrip("\ufeff"))
        signed = False
    updated = target.replace(code, preview=preview)
    before = _inject_review_source(original).splitlines()
    after = _inject_review_source(code)
    diff = "\n".join(difflib.unified_diff(before, after.splitlines(),
                                         fromfile="original.mlog", tofile="replacement.mlog",
                                         lineterm=""))
    response["replacement_sha256"] = hashlib.sha256(code.encode("utf-8")).hexdigest()
    response["signed"] = signed
    if not signed:
        response["warning"] = "no safe signature slot; written unsigned"
    checks = _inject_checks(target, after)
    if updated is not None:
        info = {key: response[key] for key in ("processor", "source_sha256", "replacement_sha256")}
        response["revision"] = _write_revision(data, updated, info, diff, checks, context)
        response["blueprint_base64"] = base64.b64encode(updated).decode("ascii")
    _review_fields(response, diff, checks, context)
    return response


