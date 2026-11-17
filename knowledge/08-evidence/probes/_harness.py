"""Probe harness for 08-evidence/probes.

Runs mlog source on the REAL v160.7 LogicExecutor, in-process (no jar
reflection, no subprocess CLI): the same code path the MCP tool mlog_sim uses.

    import mlogsim as sim
    srv = sim.Server(sim._default_java(), sim._default_jar(), 64)
    rec = sim.run_mlog(srv, "inline", code, steps, ticks=False, update="none", links="auto")

One JVM boot ~6 s; the server is cached per process so several probes in one
python process pay it once.

Repository location: env MLOG_REPO, default the repo root this file lives in.
"""
import atexit
import json
import os
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = pathlib.Path(os.environ.get(
    "MLOG_REPO", HERE.parents[3]))   # knowledge/08-evidence/probes -> 仓库根
OUT = HERE / "out"
FENCE = chr(96) * 3

# --- workaround: the repo lives on an OneDrive-synced folder; tempfile.mkdtemp
# inside <repo>/out/_sim stalls there (observed: >120 s, then hang). Redirect the
# simulator's per-run workdir to this probe dir instead (same filesystem, fast).
SIM_WORK = HERE / "out" / "_simwork"
SIM_WORK.mkdir(parents=True, exist_ok=True)
_orig_mkdtemp = tempfile.mkdtemp


def _mkdtemp(prefix=None, suffix=None, dir=None):
    return _orig_mkdtemp(prefix=prefix or "", suffix=suffix or "", dir=str(SIM_WORK))


tempfile.mkdtemp = _mkdtemp

sys.path.insert(0, str(REPO / "tools"))

import mlogsim as sim  # noqa: E402

_srv = None


def server():
    global _srv
    if _srv is None:
        _srv = sim.Server(sim._default_java(), sim._default_jar(), 64)
    return _srv


def run(logic, steps=6, ticks=None):
    srv = server()
    if ticks:
        return sim.run_mlog(srv, "inline", logic, int(ticks), ticks=True,
                            update="all", links="auto")
    return sim.run_mlog(srv, "inline", logic, int(steps), ticks=False,
                        update="none", links="auto")


def close():
    global _srv
    if _srv is not None:
        try:
            _srv.close()
        finally:
            _srv = None


atexit.register(close)


def probe(pid, claim, logic, check, steps=6, ticks=None, note=""):
    """Run one probe: returns 0 on PASS, 1 on FAIL; writes out/<pid>.txt."""
    OUT.mkdir(parents=True, exist_ok=True)
    rec = run(logic, steps=steps, ticks=ticks)
    ok, why = check(rec)[:2]
    label = "INCONCLUSIVE" if ok is None else ("PASS" if ok else "FAIL")
    mode = ("ticks=%d (update=all)" % ticks) if ticks else ("steps=%d (update=none)" % steps)
    lines = [
        "# probe " + pid,
        "",
        "claim   : " + claim,
        "mode    : " + mode,
        "verdict : " + label,
        "why     : " + why,
        "python  : " + sys.version.split()[0],
        "repo    : " + str(REPO),
    ]
    if note:
        lines.append("note    : " + note)
    lines += ["", "## mlog source (paste into a processor to reproduce)", "", FENCE]
    lines.append(logic.rstrip("\n"))
    lines += [FENCE, "", "## executor readback", "", FENCE + "json"]
    keep = {k: rec.get(k) for k in ("vars", "text", "counter", "mode", "steps", "ipt")}
    lines.append(json.dumps(keep, ensure_ascii=False, indent=2))
    lines += [FENCE, ""]
    txt = "\n".join(lines) + "\n"
    (OUT / (pid + ".txt")).write_text(txt, encoding="utf-8")
    print("%s  %-12s  %s" % (pid, label, why))
    return 0 if ok else 1
