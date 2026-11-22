"""Owned JVM process, output buffer and deterministic resource cleanup."""
from __future__ import annotations

from collections import deque
import os
import subprocess
import threading
import time

from mlogent.simulation.process import bind_to_parent as _win_kill_with_parent


def _release_job(job):
    if job is not None and os.name == 'nt':
        import ctypes
        ctypes.WinDLL('kernel32').CloseHandle(ctypes.c_void_p(job))


class WorldProcess:
    """Manage a JVM without hosting a map or touching daemon handshake files."""

    def __init__(self, java, jar, *, data_dir, log_path):
        self.java = os.path.abspath(java) if os.path.dirname(java) else java
        self.jar = os.path.abspath(jar)
        self.data_dir = os.path.abspath(data_dir)
        self.log_path = os.path.abspath(log_path)
        self.started = time.time()
        self.lines = deque(maxlen=8000)
        self.seq = 0
        self._cv = threading.Condition()
        self._lock = threading.RLock()
        self._write_lock = threading.Lock()
        self._close_lock = threading.Lock()
        self.proc = None
        self.eof = False
        self.pump_error = None
        self._logf = None
        self._job = None
        self._pump_thread = None
        self._closed = False
        self.cleanup_errors = []
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            self._spawn()
        except BaseException:
            self.close(force=True)
            raise

    def _spawn(self):
        self._logf = open(self.log_path, 'a', encoding='utf-8', buffering=1)
        self._logf.write('\n===== %s  %s =====\n' %
                         (time.strftime('%Y-%m-%d %H:%M:%S'), self.jar))
        self.proc = subprocess.Popen(
            [self.java, '-Dstdout.encoding=UTF-8', '-Dstderr.encoding=UTF-8', '-jar', self.jar],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            cwd=self.data_dir, text=True, encoding='utf-8', errors='replace', bufsize=1)
        self._job = _win_kill_with_parent(self.proc)
        self._pump_thread = threading.Thread(target=self._pump, daemon=True)
        self._pump_thread.start()

    def _pump(self):
        try:
            for raw in self.proc.stdout:
                line = raw.rstrip('\r\n')
                with self._cv:
                    self.seq += 1
                    self.lines.append((self.seq, line))
                    self._cv.notify_all()
                try:
                    self._logf.write(line + '\n')
                except Exception:
                    pass
        except Exception as exc:
            self.pump_error = str(exc)
        finally:
            with self._cv:
                self.eof = True
                self._cv.notify_all()

    def send(self, cmd):
        with self._write_lock:
            assert self.proc and self.proc.stdin
            self.proc.stdin.write(cmd + '\n')
            self.proc.stdin.flush()

    def close(self, force=False):
        with self._close_lock:
            if self._closed:
                return
            self._closed = True
            proc = self.proc
            try:
                if proc and proc.poll() is None:
                    if not force:
                        try:
                            self.send('exit')
                        except Exception as exc:
                            self.cleanup_errors.append(str(exc))
                        try:
                            proc.wait(timeout=3)
                        except subprocess.TimeoutExpired:
                            pass
                        except OSError as exc:
                            self.cleanup_errors.append(str(exc))
                    if proc.poll() is None:
                        proc.kill()
            except Exception as exc:
                self.cleanup_errors.append(str(exc))
            finally:
                try:
                    _release_job(self._job)
                except Exception as exc:
                    self.cleanup_errors.append(str(exc))
                self._job = None
                if proc:
                    try:
                        proc.wait(timeout=5)
                    except (OSError, subprocess.TimeoutExpired) as exc:
                        self.cleanup_errors.append(str(exc))
                pump = self._pump_thread
                if pump and pump is not threading.current_thread():
                    try:
                        pump.join(timeout=2)
                    except RuntimeError as exc:
                        self.cleanup_errors.append(str(exc))
                # Never block closing a pipe still being read by a stuck pump.
                for pipe in ((proc.stdin, proc.stdout) if proc else ()):
                    if pipe is proc.stdout and pump and pump.is_alive():
                        self.cleanup_errors.append('stdout pump did not stop')
                        continue
                    if pipe:
                        try:
                            pipe.close()
                        except Exception as exc:
                            self.cleanup_errors.append(str(exc))
                if self._logf:
                    try:
                        self._logf.close()
                    except Exception as exc:
                        self.cleanup_errors.append(str(exc))

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
