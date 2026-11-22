"""Mindcode compilation and validation adapters for MCP.

Artifact storage and program loading are provided by the entry point. Compiler,
evaluation and task persistence retain their existing implementations.
"""
from __future__ import annotations

from pathlib import Path

import mlog_eval as _eval


def _read_text(path):
    with open(path, encoding="utf-8-sig") as fh:
        return fh.read()


def _compile_artifacts(res, level, out, *, stash):
    """The compiled mlog is the deliverable; in summary mode it travels as a
    reference so the envelope stays small but nothing is lost."""
    artifacts = {"stats": res.get("stats"), "tool": res.get("tool")}
    if out:
        artifacts["out"] = out
    code = res.get("mlog") or ""
    if code:
        if level == "summary":
            artifacts["mlog_ref"] = stash(code)
        else:
            artifacts["mlog"] = code
    return {k: v for k, v in artifacts.items() if v is not None}


def compile(args, *, stash):
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
        artifacts=_compile_artifacts(res, level, args.get("out"), stash=stash),
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


def validate(args, *, load_programs):
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
                    for label, lines, names in load_programs(path)]
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


