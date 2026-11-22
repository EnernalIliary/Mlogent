"""Knowledge retrieval and simulator capability queries for MCP."""

def fidelity(args):
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


def knowledge(args):
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


