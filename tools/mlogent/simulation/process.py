"""Owned simulator process, console transport and orphan cleanup.

No game setup, scene construction or CLI dependencies. SimulatorProcess can be
used with the existing Server world facade or exercised with an owned test child.
"""
from __future__ import annotations

import atexit
import json
import os
import queue
import shutil
import subprocess
import tempfile
import threading
import time


class SimError(RuntimeError):
    pass


def release_job(job):
    if os.name == "nt":
        import ctypes
        ctypes.WinDLL("kernel32").CloseHandle(ctypes.c_void_p(job))


def absolute_command(p: str) -> str:
    """Resolve a jar/java path against the caller's cwd; keep bare commands as-is.

    Server() starts the Java child with cwd=<workdir under out/_sim> (Java must
    not write to %TEMP%), so a relative path would be resolved *there* and fail
    with "Unable to access jarfile". A bare name (e.g. --java java) must still
    go through PATH, so only paths with a directory part or an existing file
    are rewritten.
    """
    if os.path.dirname(p) or os.path.exists(p):
        return os.path.abspath(p)
    return p


# ------------------------------------------------------------- child lifetime
# The Java child used to outlive its Python parent: when the parent was killed
# (a gate timeout, Ctrl-C, a crashed probe) the JVM kept the pipe and stayed
# resident. 61 of them once piled up and starved the box so badly that the whole
# probes tier failed with "There is insufficient memory for the Java Runtime
# Environment to continue". On Windows the fix is a job object with
# KILL_ON_JOB_CLOSE: the job handle belongs to *this* process, so whenever this
# process ends for any reason the kernel kills every child inside it. atexit is
# the polite path; the job object is the one that survives a hard kill.
LIVE_SERVERS = []


def bind_to_parent(proc):
    """Put a Windows child in a job that dies with this process; None elsewhere."""
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.CreateJobObjectW.restype = ctypes.c_void_p
        k32.CreateJobObjectW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
        k32.SetInformationJobObject.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                                ctypes.c_void_p, wintypes.DWORD]
        k32.AssignProcessToJobObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        k32.CloseHandle.argtypes = [ctypes.c_void_p]

        class _IO_COUNTERS(ctypes.Structure):
            _fields_ = [("ReadOperationCount", ctypes.c_ulonglong),
                        ("WriteOperationCount", ctypes.c_ulonglong),
                        ("OtherOperationCount", ctypes.c_ulonglong),
                        ("ReadTransferCount", ctypes.c_ulonglong),
                        ("WriteTransferCount", ctypes.c_ulonglong),
                        ("OtherTransferCount", ctypes.c_ulonglong)]

        class _BASIC_LIMITS(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64),
                        ("PerJobUserTimeLimit", ctypes.c_int64),
                        ("LimitFlags", wintypes.DWORD),
                        ("MinimumWorkingSetSize", ctypes.c_size_t),
                        ("MaximumWorkingSetSize", ctypes.c_size_t),
                        ("ActiveProcessLimit", wintypes.DWORD),
                        ("Affinity", ctypes.c_size_t),
                        ("PriorityClass", wintypes.DWORD),
                        ("SchedulingClass", wintypes.DWORD)]

        class _EXTENDED_LIMITS(ctypes.Structure):
            _fields_ = [("BasicLimitInformation", _BASIC_LIMITS),
                        ("IoInfo", _IO_COUNTERS),
                        ("ProcessMemoryLimit", ctypes.c_size_t),
                        ("JobMemoryLimit", ctypes.c_size_t),
                        ("PeakProcessMemoryUsed", ctypes.c_size_t),
                        ("PeakJobMemoryUsed", ctypes.c_size_t)]

        job = k32.CreateJobObjectW(None, None)
        if not job:
            return None
        info = _EXTENDED_LIMITS()
        info.BasicLimitInformation.LimitFlags = 0x2000  # KILL_ON_JOB_CLOSE
        if not k32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info)):
            k32.CloseHandle(job)
            return None
        if not k32.AssignProcessToJobObject(job, ctypes.c_void_p(int(proc._handle))):
            k32.CloseHandle(job)
            return None
        return job
    except Exception:
        return None


def close_live_servers():
    for srv in list(LIVE_SERVERS):
        try:
            srv.close()
        except Exception:
            pass


atexit.register(close_live_servers)


# Any java.exe still running one of our jars whose parent is gone is a leftover
# from a killed run. Only our jars count: the game itself also runs a java.exe.
_JAR_MARKERS = ("_server160.jar", "_server159.jar", "_server146.jar", "jre21")


def powershell_json(script):
    exe = shutil.which("powershell") or "powershell"
    out = subprocess.run([exe, "-NoProfile", "-NonInteractive", "-Command", script],
                         capture_output=True, text=True, encoding="utf-8",
                         errors="replace", timeout=180)
    text = (out.stdout or "").strip()
    return json.loads(text) if text else None


def sweep_orphans(dry_run=False, *, query_processes=None):
    """Kill simulator JVMs whose Python parent no longer exists; return their pids."""
    if os.name != "nt":
        return []
    try:
        procs = (query_processes or powershell_json)("Get-CimInstance Win32_Process | "
                         "Select-Object ProcessId,ParentProcessId,Name,CommandLine | "
                         "ConvertTo-Json -Compress -Depth 3")
    except Exception:
        return []
    if not procs:
        return []
    if isinstance(procs, dict):
        procs = [procs]
    live = set()
    for item in procs:
        try:
            live.add(int(item.get("ProcessId") or 0))
        except (TypeError, ValueError):
            pass
    killed = []
    for item in procs:
        try:
            pid = int(item.get("ProcessId") or 0)
            ppid = int(item.get("ParentProcessId") or 0)
        except (TypeError, ValueError):
            continue
        if pid <= 0 or str(item.get("Name") or "").lower() != "java.exe":
            continue
        cmd = str(item.get("CommandLine") or "")
        if not any(mark in cmd for mark in _JAR_MARKERS):
            continue
        if ppid in live:
            continue          # parent still alive: not an orphan (pid reuse reads as alive)
        if dry_run:
            killed.append(pid)
            continue
        try:
            subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                           capture_output=True, timeout=30)
            killed.append(pid)
        except Exception:
            pass
    return killed


class SimulatorProcess:
    """Own a console process, its output queue and deterministic shutdown."""

    def __init__(self, java: str, jar: str, *, workspace_root: str,
                 marker_preview: bool = False, bind_job=None):
        java, jar = absolute_command(java), absolute_command(jar)
        base = os.environ.get("MLOG_SIM_BASEDIR") or os.path.join(workspace_root, "out", "_sim")
        os.makedirs(base, exist_ok=True)
        self.workdir = tempfile.mkdtemp(prefix="run-", dir=base)
        os.makedirs(os.path.join(self.workdir, "config", "logs"), exist_ok=True)
        self.proc = None
        self._job = None
        self._closed = False
        self._pump_thread = None
        self.lines: queue.Queue = queue.Queue()
        self.buffer: list[str] = []
        self.all: list[str] = []
        self.exit_code = None
        self.js_timeout = 180.0
        self.js_timeout_explicit = False
        jvm_options = ["-Dstdout.encoding=UTF-8", "-Dstderr.encoding=UTF-8"]
        if marker_preview:
            jvm_options += ["-Djava.awt.headless=true",
                            "--add-exports=java.desktop/sun.java2d=ALL-UNNAMED",
                            "--add-exports=java.desktop/sun.font=ALL-UNNAMED"]
        try:
            self.proc = subprocess.Popen(
                [java, *jvm_options, "-jar", jar],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                cwd=self.workdir, text=True, encoding="utf-8", errors="replace", bufsize=1,
            )
            self._job = (bind_job or bind_to_parent)(self.proc)
            LIVE_SERVERS.append(self)
            self._pump_thread = threading.Thread(target=self._pump, daemon=True)
            self._pump_thread.start()
        except BaseException:
            self.close()
            raise

    def _pump(self):
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self.lines.put(line.rstrip("\r\n"))
        self.exit_code = self.proc.wait()
        self.lines.put(None)

    def send(self, cmd: str):
        assert self.proc.stdin is not None
        self.proc.stdin.write(cmd + "\n")
        self.proc.stdin.flush()

    def wait_for(self, needle: str, timeout: float = 60.0, *, terminal=None) -> list[str]:
        deadline = time.monotonic() + timeout
        out: list[str] = []
        while (remaining := deadline - time.monotonic()) > 0:
            try:
                line = self.lines.get(timeout=min(0.2, remaining))
            except queue.Empty:
                continue
            if line is None:
                raise SimError(f"server exited (code={self.exit_code}):\n" + "\n".join(self.all[-20:]))
            self.buffer.append(line)
            self.all.append(line)
            out.append(line)
            matched = terminal(line) if terminal is not None else needle in line
            if matched:
                return out
        raise SimError(f"timeout waiting for {needle!r}; tail:\n" + "\n".join(self.all[-20:]))

    def close(self):
        """Reap the owned child and release streams/job exactly once."""
        if getattr(self, "_closed", False):
            return
        self._closed = True
        try:
            LIVE_SERVERS.remove(self)
        except ValueError:
            pass
        proc = getattr(self, "proc", None)
        try:
            if proc is not None and proc.poll() is None:
                self.send("exit")
                try:
                    proc.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=10)
        except Exception:
            if proc is not None:
                try:
                    proc.kill()
                    proc.wait(timeout=10)
                except Exception:
                    pass
        finally:
            thread = getattr(self, "_pump_thread", None)
            if thread is not None and thread is not threading.current_thread() and thread.is_alive():
                thread.join(timeout=1)
            if proc is not None:
                for stream in (proc.stdin, proc.stdout):
                    try:
                        stream.close()
                    except Exception:
                        pass
            job = getattr(self, "_job", None)
            if job:
                try:
                    release_job(job)
                except Exception:
                    pass
                self._job = None
