"""MCP task actions backed by the existing taskstate store."""

def task(args):
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


