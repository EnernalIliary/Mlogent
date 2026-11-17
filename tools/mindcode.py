#!/usr/bin/env python3
"""mindcode.py -- Mindcode source in, mlog text out.

WHY THIS FILE EXISTS
====================
Mindcode (https://github.com/cardillan/mindcode) is a Java compiler: the only
interface is `java -jar mindcode.jar cm ...`.  Everything else in this repo
consumes mlog *text* (mlogcheck / mlogir / mlogagent / mlogsim), so every
consumer that shells out by hand has to rediscover the same traps below.  This
module is that seam, once:

    locate()          find a jar + JRE that actually run, and say why if not
    compile_source()  source string -> {"mlog", "diagnostics", "stats", ...}
    compile_file()    the same for a path on disk
    CLI: compile / doctor / version  (exit 0 = ok, 1 = the source did not
                                      compile, 2 = could not run at all: no
                                      usable compiler, unreadable source, or a
                                      timeout)

WHAT THE COMPILER ACTUALLY EMITS (measured against v3.19.3 here)
--------------------------------------------------------------
    stdout on success: "Mindcode: 17 AST nodes, instructions: 9 unoptimized,
                        10 optimized, performance: parsed in 98 ms,
                        compiled in 384 ms, optimized in 4 ms."
    stderr on failure: "<abs path>:<line>:<col> <category>: <message>"

Parse errors carry a category ("Parse error: missing semicolon after '1'"),
semantic errors often carry none ("Unknown property 'health'."), so a line is
classified by shape, not by a fixed list of categories.  Exit code is 1 for
both compile errors AND a failed output-file write -- which is why `ok` here is
decided by "did we get code and no error diagnostics", never by the exit code.

TRAPS (each one measured on this machine, each one handled below)
=================================================================
1. v3.19.3 is the default candidate; v3.21.0 deadlocks on `cm`.
   Upstream bug: `Main.java:40` declares `--no-update-check` only on the
   top-level parser, while `ToolAppAction.java:41` reads it from the subcommand
   namespace, so the flag never reaches the update checker.  The checker then
   runs unconditionally, `dev.dirs` shells out to PowerShell running inline C#
   and blocks forever on its stdout: no output at all, no CPU burn, JVM alive.
   Reproduced here: `cm` produced nothing for 30 s and had to be taskkilled.
   `--version` on 3.21 is fine, so a version probe cannot detect it -- only an
   actual compile can (that is what `doctor`'s smoke step is for).
   The jar is still a candidate because the contract's search order lists it,
   but it sits LAST and locate() leaves a note when it gets selected.

2. A UTF-8 BOM in the source file is a *syntax error at 1:1*:
       x.mnd:1:1 Parse error: '?': mismatched input '?' expecting {<EOF>, ...}
   The compiler does not skip the BOM; the leading U+FEFF becomes a stray '?'
   token.  So temporary source files are always written BOM-free, and a BOM in
   the caller's string/file is stripped before it ever reaches the compiler.

3. `java` on PATH is Java 8 here, and Mindcode needs 22+.
   There is no fallback to PATH on purpose: Java 8 answers with a
   `UnsupportedClassVersionError` at best and an obscure `LinkageError` at
   worst.  When nothing usable is found, locate() returns ok=False instead.

4. The bundled JRE 21 cannot run the v3.19.3 jar either.
   v3.19.3 is built for class file version 66.0 (Java 22); JRE 21 tops out at
   65.0, so the first java candidate in the documented order fails with:
       UnsupportedClassVersionError: info/teksol/mindcode/cmdline/Main has been
       compiled by a more recent version of the Java Runtime (class file
       version 66.0), this version of the Java Runtime only recognizes class
       file versions up to 65.0
   That is why the java candidates are *probed* and not just stat()ed: a JRE
   that exists but cannot load the jar must be skipped, with a note saying so.

5. Diagnostics are written in the ANSI code page, not UTF-8.
   A source path containing CJK characters comes back as cp936 bytes
   (`d6 d0 ce c4` for 中文) while the compiled mlog file itself is UTF-8.
   Decoding stderr as UTF-8 strictly fails there, so every stream goes through
   `_decode()`: UTF-8 strict first, then the locale code page, then replacement.

6. `-o <file>` can fail even when Python can write the same directory.
   Under a file sandbox the JVM child may be denied writes to the system temp
   dir; the compiler then prints "Error writing file <path>." on stderr, exits
   1, and still had the code ready.  Compilation therefore runs in a temp dir
   *inside the repo* when possible (`out/_mindcode/`, same place as the jar),
   and when the mlog file is missing the compile is retried once with `-o -`
   so the code is recovered from stdout instead of being lost.

OUTPUT NORMALISATION
====================
The compiler writes CRLF and a trailing blank line into the mlog file; the
returned `mlog` is normalised to LF with exactly one trailing newline, so
callers can hash/compare it.  Mindcode appends its signature line ("print
\"Compiled by Mindcode 3.19.3 - ...\"") unless `--no-signature` is passed; this
wrapper keeps the compiler's default and does not rewrite the program.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import locale
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "out"
MINDCODE_DIR = OUT / "_mindcode"

# --- the documented search order -------------------------------------------
# jar: MINDCODE_JAR -> out/_mindcode/mindcode-3.19.3.jar
#      -> out/_mindcode/mindcode.jar -> ~/src/mindcode-dist
PREFERRED_JAR = MINDCODE_DIR / "mindcode-3.19.3.jar"
FALLBACK_JAR = MINDCODE_DIR / "mindcode.jar"
USER_JAR = Path.home() / "src" / "mindcode-dist" / "mindcode.jar"

# java: MINDCODE_JAVA -> out/jre21/... -> out/_mindcode/jdk-25.../...
# PATH is deliberately absent; see trap 3 in the module docstring.
JAVA_21 = OUT / "jre21" / "jdk-21.0.5+11-jre" / "bin" / "java.exe"
JAVA_25 = MINDCODE_DIR / "jdk-25.0.5+8-jre" / "bin" / "java.exe"

VERSION_TIMEOUT = 30.0  # `--version` on a healthy jar takes ~0.3 s

_STATS_RE = re.compile(
    r"Mindcode:\s*(?P<ast>\d+)\s+AST nodes,\s*"
    r"instructions:\s*(?P<ins>\d+)\s+unoptimized,\s*(?P<opt>\d+)\s+optimized"
    r"(?:,\s*performance:\s*parsed in\s*(?P<parsed>\d+)\s*ms,\s*"
    r"compiled in\s*(?P<compiled>\d+)\s*ms,\s*optimized in\s*(?P<optimized>\d+)\s*ms)?",
    re.IGNORECASE,
)
_DIAG_RE = re.compile(r"^(?P<file>.+?):(?P<line>\d+):(?P<col>\d+)\s(?P<rest>.*)$")
_CATEGORY_RE = re.compile(
    r"^(?P<kind>(?:parse|syntax|compile|internal|runtime)\s+error|warning|note|info):\s*(?P<msg>.*)$",
    re.IGNORECASE,
)
_VERSION_RE = re.compile(r"version\s+([0-9][0-9A-Za-z._\-]*)")
_JAVA_VERSION_RE = re.compile(r'version\s+"([^"]+)"')
_CLASS_VERSION_RE = re.compile(
    r"class file version (\d+)\.0,\s*this version of the Java Runtime only "
    r"recognizes class file versions up to (\d+)\.0"
)

_NONFATAL_KINDS = {"warning", "note", "info"}
_ENV_KINDS = {"environment", "timeout", "io", "encoding"}

_LOCATE_CACHE: dict[tuple, dict] = {}


# ---------------------------------------------------------------------------
# locating a working jar + JRE
# ---------------------------------------------------------------------------
def _env_path(name: str) -> Path | None:
    raw = (os.environ.get(name) or "").strip()
    return Path(raw).expanduser() if raw else None


def _jar_candidates() -> list[tuple[Path, str]]:
    """(path, why) in the documented order.  An explicit MINDCODE_JAR wins."""
    env = _env_path("MINDCODE_JAR")
    if env is not None:
        return [(env, "MINDCODE_JAR")]
    return [
        (PREFERRED_JAR, "preferred: v3.19.3 is the build that terminates here"),
        (FALLBACK_JAR, "last resort: may be v3.21.0, whose `cm` action deadlocks"),
        (USER_JAR, "upstream download"),
    ]


def _java_candidates() -> list[tuple[Path, str]]:
    """(path, why) in the documented order.  An explicit MINDCODE_JAVA wins."""
    env = _env_path("MINDCODE_JAVA")
    if env is not None:
        return [(env, "MINDCODE_JAVA")]
    return [
        (JAVA_21, "bundled JRE 21 (first in the documented order)"),
        (JAVA_25, "bundled JRE 25 (can load the v3.19.3 jar, which targets Java 22+)"),
    ]


def _java_label(path: Path | str) -> str:
    p = Path(path)
    parts = p.parts
    if len(parts) >= 2:
        return parts[-3] if p.name.lower() == "java.exe" and len(parts) >= 3 else p.parent.name
    return p.name


def _decode(data: bytes) -> str:
    """Decode compiler output: UTF-8 first, then the ANSI code page (trap 5)."""
    if not data:
        return ""
    seen: list[str] = []
    for enc in ("utf-8", locale.getpreferredencoding(False) or "cp1252"):
        low = enc.lower()
        if low in seen:
            continue
        seen.append(low)
        try:
            return data.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return data.decode("utf-8", "replace")


def _flags() -> int:
    if os.name != "nt":
        return 0
    flags = 0
    for name in ("CREATE_NO_WINDOW", "CREATE_NEW_PROCESS_GROUP"):
        flags |= getattr(subprocess, name, 0)
    return flags


def _run(argv: list[str], timeout: float) -> tuple[int | None, bytes, bytes, bool]:
    """Run argv; return (rc, stdout, stderr, timed_out).  rc=None means no start."""
    try:
        proc = subprocess.Popen(
            [str(a) for a in argv],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=_flags(),
        )
    except OSError as exc:
        return None, b"", ("%s: %s" % (type(exc).__name__, exc)).encode("utf-8", "replace"), False
    try:
        out, err = proc.communicate(timeout=timeout)
        return proc.returncode, out, err, False
    except subprocess.TimeoutExpired:
        _kill_tree(proc)
        try:
            out, err = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            # Something still holds the pipe; give up on the tail rather than hang.
            for stream in (proc.stdout, proc.stderr):
                try:
                    stream.close()
                except Exception:
                    pass
            out, err = b"", b""
        rc = proc.returncode if proc.returncode is not None else -1
        return rc, out, err, True


def _kill_tree(proc: subprocess.Popen) -> None:
    """Kill the JVM at once, then sweep any child it spawned.

    Order matters: `proc.kill()` (TerminateProcess) is the call that actually
    lands here.  `taskkill /F /T` answers 255 "There is no running instance of
    the task" for a process that is demonstrably alive (a sandboxed
    TerminateProcess path), so it is only ever a best-effort sweep for the
    grandchildren the update checker spawns.
    """
    try:
        proc.kill()
    except Exception:
        pass
    if os.name == "nt":
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           timeout=2.0)
        except Exception:
            pass


def _probe_version(java: Path, jar: Path) -> dict:
    """Can this pair load at all?  Returns {status, version, detail}."""
    rc, out, err, timed_out = _run([java, "-jar", jar, "--version"], VERSION_TIMEOUT)
    stdout = _decode(out)
    stderr = _decode(err)
    if timed_out:
        return {"status": "timeout", "version": None,
                "detail": "`--version` did not return within %g s" % VERSION_TIMEOUT}
    if rc is None:
        return {"status": "error", "version": None, "detail": stderr.strip()[:400] or "could not start"}
    # The class-version failure mentions "version 66.0" itself, so it must be
    # classified before the version regex is allowed to look at the output.
    classes = _CLASS_VERSION_RE.search(stdout + "\n" + stderr)
    if classes:
        need, have = int(classes.group(1)), int(classes.group(2))
        return {"status": "incompatible", "version": None,
                "detail": "jar needs class file %d.0 (Java %d+), this runtime supports up to %d.0"
                          % (need, need - 44, have)}
    match = _VERSION_RE.search(stdout) if rc == 0 else None
    if match:
        return {"status": "ok", "version": match.group(1), "detail": stdout.strip()[:200]}
    hint = (stderr or stdout).strip().splitlines()
    hint = " ".join(hint[-1].split())[:300] if hint else "no version on stdout/stderr"
    return {"status": "error", "version": None, "detail": "exit %s: %s" % (rc, hint)}


def _fingerprint() -> tuple:
    """Cache key: env overrides plus mtime/size of every candidate."""
    parts: list[str] = [
        os.environ.get("MINDCODE_JAR") or "",
        os.environ.get("MINDCODE_JAVA") or "",
    ]
    for path, _why in _jar_candidates() + _java_candidates():
        try:
            st = path.stat()
            parts.append("%s|%d|%d" % (path, st.st_mtime_ns, st.st_size))
        except OSError:
            parts.append("%s|-" % (path,))
    return tuple(parts)


def _resolve() -> dict:
    """Full resolution report (locate() and doctor() both read it)."""
    key = _fingerprint()
    cached = _LOCATE_CACHE.get(key)
    if cached is not None:
        return {"jar": cached["jar"], "java": cached["java"], "version": cached["version"],
                "ok": cached["ok"], "notes": list(cached["notes"]),
                "warnings": list(cached["warnings"]),
                "jars": [dict(r) for r in cached["jars"]],
                "javas": [dict(r) for r in cached["javas"]],
                "probes": [dict(r) for r in cached["probes"]]}

    notes: list[str] = []
    # notes that matter to a *compile* (as opposed to a doctor report)
    warnings: list[str] = []
    jar_c, java_c = _jar_candidates(), _java_candidates()
    jars = [{"path": str(p), "why": w, "exists": p.is_file()} for p, w in jar_c]
    javas = [{"path": str(p), "why": w, "exists": p.is_file()} for p, w in java_c]
    for p, w in jar_c:
        if not p.is_file():
            notes.append("jar candidate missing (%s): %s" % (w, p))
    for p, w in java_c:
        if not p.is_file():
            notes.append("java candidate missing (%s): %s" % (w, p))

    live_jars = [(p, w) for p, w in jar_c if p.is_file()]
    live_javas = [(p, w) for p, w in java_c if p.is_file()]
    # Report the path the search order asks for, even when it is missing: an
    # explicit MINDCODE_JAR that does not exist must be named, not replaced by
    # a silently chosen neighbour.
    result = {"jar": str(jar_c[0][0]), "java": str(live_javas[0][0]) if live_javas
              else str(java_c[0][0]),
              "version": None, "ok": False, "notes": notes, "warnings": warnings,
              "jars": jars, "javas": javas, "probes": []}

    if not live_jars:
        notes.append("no mindcode jar found: set MINDCODE_JAR or place "
                     "mindcode-3.19.3.jar in out/_mindcode/")
    elif not live_javas:
        notes.append("no bundled java found: set MINDCODE_JAVA to a Java 22+ java.exe "
                     "(PATH java is never used -- it is Java 8 here)")
    else:
        for jar, _jw in live_jars:
            for java, _ww in live_javas:
                probe = _probe_version(java, jar)
                result["probes"].append({"jar": str(jar), "java": str(java),
                                         "status": probe["status"], "detail": probe["detail"]})
                if probe["status"] == "ok":
                    failed = [p for p in result["probes"][:-1]]
                    if failed:
                        notes.append("skipped %d incompatible pair(s) before selecting this one"
                                     % len(failed))
                    result.update(jar=str(jar), java=str(java),
                                  version=probe["version"], ok=True)
                    if probe["version"].startswith("3.21"):
                        msg = ("selected mindcode %s, whose `cm` action is known to "
                               "deadlock here (update checker): expect compile timeouts"
                               % probe["version"])
                        notes.append(msg)
                        warnings.append(msg)
                    break
                notes.append("%s + %s: %s"
                             % (jar.name, _java_label(java),
                                " ".join(probe["detail"].split())))
            if result["ok"]:
                break
        if not result["ok"]:
            notes.append("no jar/java pair could load the compiler")

    _LOCATE_CACHE[key] = {k: (list(v) if isinstance(v, list) else v) for k, v in result.items()}
    _LOCATE_CACHE[key]["jars"] = [dict(r) for r in jars]
    _LOCATE_CACHE[key]["javas"] = [dict(r) for r in javas]
    _LOCATE_CACHE[key]["probes"] = [dict(r) for r in result["probes"]]
    return result


def locate() -> dict:
    """Find a usable compiler.  {"jar","java","version","ok","notes"}."""
    r = _resolve()
    return {"jar": r["jar"], "java": r["java"], "version": r["version"],
            "ok": r["ok"], "notes": r["notes"]}


# ---------------------------------------------------------------------------
# compiling
# ---------------------------------------------------------------------------
def _blank_stats() -> dict:
    return {"ast_nodes": 0, "instructions": 0, "optimized_instructions": 0,
            "timings_ms": {}, "raw": "", "exit_code": None, "timed_out": False}


def _parse_stats(text: str) -> dict:
    stats = _blank_stats()
    match = _STATS_RE.search(text or "")
    if not match:
        return stats
    stats["ast_nodes"] = int(match.group("ast"))
    stats["instructions"] = int(match.group("ins"))
    stats["optimized_instructions"] = int(match.group("opt"))
    timings = {}
    for name in ("parsed", "compiled", "optimized"):
        if match.group(name) is not None:
            timings[name] = int(match.group(name))
    stats["timings_ms"] = timings
    stats["raw"] = match.group(0).strip()
    return stats


def _parse_diagnostics(text: str, name: str) -> tuple[list[dict], list[str]]:
    """Split compiler stderr into structured diagnostics + free-form notes."""
    diags: list[dict] = []
    notes: list[str] = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        match = _DIAG_RE.match(line)
        if not match:
            notes.append(line)
            continue
        rest = match.group("rest").strip()
        cat = _CATEGORY_RE.match(rest)
        kind = cat.group("kind") if cat else "error"
        message = (cat.group("msg") if cat else rest).strip()
        where = match.group("file")
        if where.endswith("input.mnd") or Path(where).name == "input.mnd":
            where = name
        diags.append({"file": where, "line": int(match.group("line")),
                      "col": int(match.group("col")), "kind": kind, "message": message})
    return diags, notes


def _error_diags(diags: list[dict]) -> list[dict]:
    return [d for d in diags if (d.get("kind") or "").lower() not in _NONFATAL_KINDS]


def _normalise_mlog(text: str) -> str:
    body = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip("\n")
    return body + "\n" if body.strip() else ""


def _read_mlog(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    text = _decode(data)
    return _normalise_mlog(text) if text.strip() else None


def _strip_bom(text: str) -> str:
    return text[1:] if text.startswith("\ufeff") else text


def _stats_text(out: str, err: str) -> str:
    for chunk in (out, err):
        if chunk and _STATS_RE.search(chunk):
            return chunk
    return ""


def _result(ok: bool, mlog: str | None, diags: list[dict], stats: dict,
            tool: dict, started: float, sha: str, notes: list[str]) -> dict:
    return {"ok": bool(ok), "mlog": mlog, "diagnostics": diags, "stats": stats,
            "tool": tool, "elapsed_ms": int((time.perf_counter() - started) * 1000),
            "source_sha256": sha, "notes": notes}


def _temp_base(workdir: str | None) -> str | None:
    """Where to create the throw-away compile dir (trap 6)."""
    if workdir:
        base = Path(workdir).expanduser()
        base.mkdir(parents=True, exist_ok=True)
        return str(base)
    return str(MINDCODE_DIR) if MINDCODE_DIR.is_dir() else None


def _compile(source: str, name: str, *, target: str, optimize: bool,
             timeout: float, workdir: str | None) -> dict:
    started = time.perf_counter()
    text = _strip_bom(source)
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    res = _resolve()
    tool = {"name": "mindcode", "version": res["version"],
            "jar": res["jar"], "java": res["java"]}
    notes = list(res["warnings"])

    if not res["ok"]:
        why = res["notes"][-1] if res["notes"] else "no usable compiler"
        return _result(False, None,
                       [{"file": name, "line": 0, "col": 0, "kind": "environment",
                         "message": "mindcode unavailable: " + why}],
                       _blank_stats(), tool, started, sha, notes)

    try:
        holder = tempfile.TemporaryDirectory(prefix="mindcode-", dir=_temp_base(workdir))
    except OSError:
        holder = tempfile.TemporaryDirectory(prefix="mindcode-")
    with holder as td:
        td = Path(td)
        src = td / "input.mnd"
        # trap 2: bytes, no BOM, whatever the caller handed us.
        src.write_bytes(text.encode("utf-8"))
        out_path = td / "output.mlog"
        log_path = td / "output.log"
        argv = [res["java"], "-jar", res["jar"], "cm", str(src),
                "-o", str(out_path), "-l", str(log_path)]
        if target:
            argv += ["-t", str(target)]
        if not optimize:
            argv += ["-O", "0"]

        rc, out_b, err_b, timed_out = _run(argv, timeout)
        out_txt, err_txt = _decode(out_b), _decode(err_b)
        diags, noise = _parse_diagnostics(err_txt, name)
        notes.extend(noise)

        if timed_out:
            stats = _parse_stats(_stats_text(out_txt, err_txt))
            stats["timed_out"] = True
            stats["exit_code"] = rc
            hint = ""
            if res["version"] and res["version"].startswith("3.21"):
                hint = (" -- mindcode %s deadlocks on `cm` (the update checker runs "
                        "unconditionally); use the 3.19.3 jar instead" % res["version"])
            return _result(
                False, None,
                [{"file": name, "line": 0, "col": 0, "kind": "timeout",
                  "message": "compiler did not finish within %g s and was killed%s" % (timeout, hint)}],
                stats, tool, started, sha, notes)

        mlog = _read_mlog(out_path)
        if mlog is None and rc is not None and not _error_diags(diags):
            # trap 6: the JVM could not write the file; the code is still on stdout.
            retry = [a for a in argv]
            retry[retry.index(str(out_path))] = "-"
            rc2, out2, err2, timed2 = _run(retry, timeout)
            code = _strip_stream_noise(_decode(out2))
            if code:
                mlog = _normalise_mlog(code)
                out_txt += "\n" + _decode(out2)
                err_txt += "\n" + _decode(err2)
                more, noise2 = _parse_diagnostics(_decode(err2), name)
                diags = diags or more
                notes.extend(noise2)
                notes.append("output file was not written by the JVM; code recovered via `-o -`")
            if timed2:
                notes.append("the `-o -` recovery run timed out")

        stats = _parse_stats(_stats_text(out_txt, err_txt))
        stats["exit_code"] = rc
        errors = _error_diags(diags)
        ok = bool(mlog) and not errors
        if not ok and not diags:
            tail = [ln for ln in (err_txt or out_txt).splitlines() if ln.strip()]
            diags = [{"file": name, "line": 0, "col": 0, "kind": "error",
                      "message": (tail[-1].strip() if tail else
                                  "compiler exited %s without a diagnostic" % rc)}]
        return _result(ok, mlog if ok else None, diags, stats, tool,
                       started, sha, notes)


def _strip_stream_noise(text: str) -> str:
    """`-o -` puts mlog on stdout; drop a stats line / diagnostics that leak in."""
    keep = []
    for line in (text or "").splitlines():
        if _STATS_RE.fullmatch(line.strip()) or _DIAG_RE.match(line.strip()):
            continue
        keep.append(line)
    return "\n".join(keep)


def compile_source(source: str, *, target: str = "7.0", optimize: bool = True,
                   timeout: float = 120.0, workdir: str | None = None) -> dict:
    """Compile Mindcode source text into mlog.

    Returns {"ok","mlog","diagnostics","stats","tool","elapsed_ms",
             "source_sha256","notes"}; `ok=False` implies mlog is None and
    diagnostics is non-empty.  `notes` is this wrapper's own commentary
    (skipped java candidates, compiler remarks, fallback runs); it is an
    addition to the contract, the six documented keys are always present.
    """
    return _compile(source, "<source>", target=target, optimize=optimize,
                    timeout=timeout, workdir=workdir)


def compile_file(path: str, **kw) -> dict:
    """Compile a .mnd file; diagnostics report the caller's own path."""
    p = Path(path).expanduser()
    try:
        data = p.read_bytes()
    except OSError as exc:
        return _result(False, None,
                       [{"file": str(path), "line": 0, "col": 0, "kind": "io",
                         "message": "%s: %s" % (type(exc).__name__, exc)}],
                       _blank_stats(),
                       {"name": "mindcode", "version": None, "jar": None, "java": None},
                       time.perf_counter(), "", [])
    try:
        text = data.decode("utf-8-sig")  # strips a BOM if the file has one
    except UnicodeDecodeError as exc:
        return _result(False, None,
                       [{"file": str(path), "line": 0, "col": 0, "kind": "encoding",
                         "message": "source is not valid UTF-8: %s" % exc}],
                       _blank_stats(),
                       {"name": "mindcode", "version": None, "jar": None, "java": None},
                       time.perf_counter(), hashlib.sha256(data).hexdigest(), [])
    kw.setdefault("target", "7.0")
    kw.setdefault("optimize", True)
    kw.setdefault("timeout", 120.0)
    kw.setdefault("workdir", None)
    return _compile(text, str(path), **kw)


# ---------------------------------------------------------------------------
# doctor
# ---------------------------------------------------------------------------
def _probe_java_version(java: Path) -> dict:
    rc, out, err, timed_out = _run([java, "-version"], VERSION_TIMEOUT)
    text = _decode(out) + "\n" + _decode(err)
    match = _JAVA_VERSION_RE.search(text)
    if timed_out:
        return {"version": None, "status": "timeout", "detail": "`java -version` timed out"}
    if match:
        return {"version": match.group(1), "status": "ok", "detail": text.strip().splitlines()[0]}
    return {"version": None, "status": "error",
            "detail": "exit %s: %s" % (rc, (text.strip().splitlines() or ["?"])[0])}


def _worst(statuses: list[str]) -> str:
    for status in ("timeout", "unavailable", "error"):
        if status in statuses:
            return status
    return "ok"


def doctor(timeout: float = 20.0, smoke: bool = True) -> dict:
    """Environment report: candidates, liveness, and a real compile smoke test."""
    started = time.perf_counter()
    res = _resolve()
    javas = []
    for row in res["javas"]:
        rec = dict(row)
        rec.update({"version": None, "status": "missing", "detail": None})
        if rec["exists"]:
            rec.update(_probe_java_version(Path(rec["path"])))
        javas.append(rec)
    path_java = shutil.which("java")
    checks: list[dict] = []

    compatible = [p for p in res["probes"] if p["status"] == "ok"]
    if res["ok"]:
        checks.append({"name": "version", "status": "ok",
                       "detail": "%s via %s" % (res["version"], _java_label(res["java"]))})
        if smoke:
            started_smoke = time.perf_counter()
            probe = _compile("print(1);\n", "<doctor>", target="7.0", optimize=True,
                             timeout=max(1.0, timeout), workdir=None)
            secs = (time.perf_counter() - started_smoke)
            if probe["ok"]:
                checks.append({
                    "name": "smoke-compile", "status": "ok",
                    "detail": "%d instruction(s) in %.2f s" % (probe["stats"]["instructions"], secs)})
            elif probe["stats"]["timed_out"]:
                checks.append({
                    "name": "smoke-compile", "status": "timeout",
                    "detail": "no answer within %g s -- this jar deadlocks on `cm` "
                              "(known for 3.21.0: the update checker runs unconditionally)"
                              % max(1.0, timeout)})
            else:
                msg = probe["diagnostics"][0]["message"] if probe["diagnostics"] else "unknown"
                checks.append({"name": "smoke-compile", "status": "error", "detail": msg})
    else:
        checks.append({"name": "version", "status": "unavailable",
                       "detail": res["notes"][-1] if res["notes"] else "no usable compiler"})
        if res["probes"]:
            checks.append({"name": "probe", "status": _worst([p["status"] for p in res["probes"]]),
                           "detail": res["probes"][-1]["detail"]})

    status = _worst([c["status"] for c in checks])
    notes = list(res["notes"])
    if path_java:
        notes.append("PATH java (%s) is deliberately ignored: Mindcode needs Java 22+"
                     % path_java)
    return {"ok": status == "ok", "status": status,
            "jar": res["jar"], "java": res["java"], "version": res["version"],
            "notes": notes, "candidates": {"jars": res["jars"], "javas": javas},
            "checks": checks, "compatible_pairs": compatible,
            "elapsed_ms": int((time.perf_counter() - started) * 1000)}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _exit_code(result: dict) -> int:
    if result.get("ok"):
        return 0
    kinds = {(d.get("kind") or "").lower() for d in result.get("diagnostics") or []}
    if result["stats"].get("timed_out") or kinds & _ENV_KINDS:
        return 2
    return 1


def _print_diagnostics(result: dict) -> None:
    for d in result["diagnostics"]:
        where = d["file"] or "<source>"
        if d["line"] or d["col"]:
            where += ":%d:%d" % (d["line"], d["col"])
        print("%s: %s: %s" % (where, d["kind"], d["message"]), file=sys.stderr)
    for note in result.get("notes") or []:
        print("note: %s" % note, file=sys.stderr)


def _emit_json(payload: dict) -> None:
    line = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def _cmd_compile(args) -> int:
    result = compile_file(args.file, target=args.target,
                          optimize=not args.no_optimize, timeout=args.timeout)
    if args.out and result["ok"]:
        Path(args.out).expanduser().write_text(result["mlog"] or "", encoding="utf-8", newline="\n")
    if args.json:
        _emit_json(result)
        return _exit_code(result)
    if result["ok"]:
        stats = result["stats"]
        summary = ("mindcode %s: %d AST nodes, %d -> %d instruction(s), "
                   "parsed %s ms, compiled %s ms, optimized %s ms (%d ms wall)"
                   % (result["tool"]["version"], stats["ast_nodes"], stats["instructions"],
                      stats["optimized_instructions"],
                      stats["timings_ms"].get("parsed", "-"),
                      stats["timings_ms"].get("compiled", "-"),
                      stats["timings_ms"].get("optimized", "-"),
                      result["elapsed_ms"]))
        if args.out:
            lines = len((result["mlog"] or "").splitlines())
            print("wrote %s (%d line(s))" % (args.out, lines))
            print(summary, file=sys.stderr)
        else:
            sys.stdout.write(result["mlog"] or "")
            sys.stdout.flush()
            print(summary, file=sys.stderr)
        for note in result.get("notes") or []:
            print("note: %s" % note, file=sys.stderr)
        return 0
    _print_diagnostics(result)
    return _exit_code(result)


def _cmd_doctor(args) -> int:
    report = doctor(timeout=args.timeout, smoke=not args.no_smoke)
    if args.json:
        _emit_json(report)
        return 0 if report["ok"] else 2
    print("mindcode %s" % (report["version"] or "-"))
    print("  jar     : %s" % (report["jar"] or "-"))
    print("  java    : %s" % (report["java"] or "-"))
    print("  status  : %s" % report["status"])
    print("  jars    :")
    for row in report["candidates"]["jars"]:
        print("    %-5s %s   (%s)" % ("yes" if row["exists"] else "no", row["path"], row["why"]))
    print("  javas   :")
    for row in report["candidates"]["javas"]:
        extra = row.get("version") or row.get("detail") or ("missing" if not row["exists"] else "")
        print("    %-5s %s   %s" % ("yes" if row["exists"] else "no", row["path"], extra))
    print("  checks  :")
    for check in report["checks"]:
        print("    %-11s %-12s %s" % (check["status"], check["name"], check["detail"] or ""))
    if report["notes"]:
        print("  notes   :")
        for note in report["notes"]:
            print("    - %s" % note)
    return 0 if report["ok"] else 2


def _cmd_version(args) -> int:
    info = locate()
    if not info["ok"]:
        print("mindcode unavailable")
        for note in info["notes"]:
            print("  - %s" % note)
        return 2
    print("mindcode %s" % info["version"])
    print("  jar  : %s" % info["jar"])
    print("  java : %s" % info["java"])
    for note in info["notes"]:
        print("  note: %s" % note)
    return 0


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(
        prog="mindcode.py",
        description="Compile Mindcode (.mnd) into mlog through mindcode.jar.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    cp = sub.add_parser("compile", help="compile one .mnd file")
    cp.add_argument("file", help="Mindcode source file")
    cp.add_argument("-o", "--out", help="write the mlog here (default: stdout)")
    cp.add_argument("--target", default="7.0", help="Mindustry target version (default 7.0)")
    cp.add_argument("--no-optimize", action="store_true", help="disable optimizer (-O 0)")
    cp.add_argument("--json", action="store_true", help="print the result dict as one JSON line")
    cp.add_argument("--timeout", type=float, default=120.0, help="compiler timeout in seconds")
    cp.set_defaults(func=_cmd_compile)

    dp = sub.add_parser("doctor", help="check jar/java, then compile a smoke program")
    dp.add_argument("--json", action="store_true", help="print the report as one JSON line")
    dp.add_argument("--timeout", type=float, default=20.0,
                    help="smoke compile timeout in seconds (default 20)")
    dp.add_argument("--no-smoke", action="store_true", help="skip the smoke compile")
    dp.set_defaults(func=_cmd_doctor)

    vp = sub.add_parser("version", help="print the located compiler and exit")
    vp.set_defaults(func=_cmd_version)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
