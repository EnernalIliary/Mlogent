"""Simulator child ownership and console contracts without requiring a JVM."""
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[2] / 'tools'
sys.path.insert(0, str(TOOLS))

import mlogsim
from mlogent.simulation import process


class Child:
    def __init__(self, text='', stubborn=False):
        self.stdin = io.StringIO()
        self.stdout = io.StringIO(text)
        self.returncode = None
        self.stubborn = stubborn
        self.killed = False
        self.waits = []

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        self.waits.append(timeout)
        if self.stubborn and self.returncode is None:
            raise subprocess.TimeoutExpired('owned-child', timeout)
        self.returncode = self.returncode if self.returncode is not None else 0
        return self.returncode

    def kill(self):
        self.killed = True
        self.returncode = -9


class ProcessTests(unittest.TestCase):
    def test_js_completion_is_explicit_and_ignores_console_colors_and_user_text(self):
        server = mlogsim.Server.__new__(mlogsim.Server)
        server.buffer = []
        server.js_timeout = 2
        marker = 'MLOGENDfixed'
        lines = [
            '\x1b[90m[I]\x1b[0m undefined',
            '[I] [none/base.js]: undefined',
            '[I] [none/base.js]: Error: user text',
            '\x1b[90m[I]\x1b[0m [none/base.js]: ' + marker + '\x1b[0m',
        ]

        def wait_for(needle, timeout, *, terminal):
            self.assertEqual(needle, marker)
            self.assertEqual(timeout, 2)
            self.assertEqual([bool(terminal(line)) for line in lines],
                             [False, False, False, True])
            self.assertTrue(terminal('[I] EcmaError: intentional failure'))
            return lines

        with patch.object(mlogsim.uuid, 'uuid4') as uid, \
                patch.object(server, 'send') as send, \
                patch.object(server, 'wait_for', side_effect=wait_for):
            uid.return_value.hex = 'fixed'
            self.assertEqual(server.js('print(1)'), ['undefined', 'Error: user text'])
            self.assertIn('print("' + marker + '")', send.call_args.args[0])

    def test_process_layer_imports_without_game_or_cli(self):
        script = (
            'import sys; sys.path.insert(0, sys.argv[1]); '
            'from mlogent.simulation import process; '
            'assert "mlogsim" not in sys.modules; '
            'assert "world_server" not in sys.modules'
        )
        subprocess.run([sys.executable, '-X', 'utf8', '-I', '-c', script, str(TOOLS)], check=True)

    def make(self, directory, child, **options):
        with patch.object(process.subprocess, 'Popen', return_value=child), \
                patch.object(process.threading.Thread, 'start'):
            return process.SimulatorProcess('java', 'game.jar', workspace_root=directory,
                                            bind_job=lambda child: None, **options)

    def test_launch_flags_paths_and_graceful_idempotent_close(self):
        with tempfile.TemporaryDirectory() as directory:
            child = Child()
            with patch.object(process.subprocess, 'Popen', return_value=child) as spawn, \
                    patch.object(process.threading.Thread, 'start'), \
                    patch.object(process, 'release_job') as release:
                server = process.SimulatorProcess('java', './game.jar', workspace_root=directory,
                                                 marker_preview=True, bind_job=lambda child: 123)
                try:
                    command = spawn.call_args.args[0]
                    self.assertEqual(command[0], 'java')
                    self.assertEqual(command[-1], str(Path('game.jar').resolve()))
                    self.assertIn('-Djava.awt.headless=true', command)
                    self.assertEqual(spawn.call_args.kwargs['cwd'], server.workdir)
                    self.assertTrue(Path(server.workdir).is_relative_to(Path(directory)))
                    self.assertIn(server, process.LIVE_SERVERS)
                    server.close()
                    server.close()
                    release.assert_called_once_with(123)
                    self.assertEqual(child.waits, [15])
                    self.assertFalse(child.killed)
                    self.assertTrue(child.stdin.closed and child.stdout.closed)
                    self.assertNotIn(server, process.LIVE_SERVERS)
                finally:
                    server.close()

    def test_unresponsive_child_is_killed_and_reaped(self):
        with tempfile.TemporaryDirectory() as directory:
            child = Child(stubborn=True)
            server = self.make(directory, child)
            server.close()
            self.assertTrue(child.killed)
            self.assertEqual(child.waits, [15, 10])
            self.assertTrue(child.stdout.closed)

    def test_broken_exit_pipe_still_reaps_child(self):
        with tempfile.TemporaryDirectory() as directory:
            child = Child()
            server = self.make(directory, child)
            child.stdin.close()
            server.close()
            self.assertTrue(child.killed)
            self.assertEqual(child.waits, [10])

    def test_initialization_failure_closes_partial_process(self):
        with tempfile.TemporaryDirectory() as directory:
            child = Child()
            before = list(process.LIVE_SERVERS)
            with patch.object(process.subprocess, 'Popen', return_value=child), \
                    patch.object(process.threading.Thread, 'start', side_effect=RuntimeError('start failed')), \
                    patch.object(process, 'release_job') as release:
                with self.assertRaisesRegex(RuntimeError, 'start failed'):
                    process.SimulatorProcess('java', 'game.jar', workspace_root=directory,
                                             bind_job=lambda child: 123)
                release.assert_called_once_with(123)
            self.assertTrue(child.stdin.closed and child.stdout.closed)
            self.assertEqual(child.waits, [15])
            self.assertEqual(process.LIVE_SERVERS, before)

    def test_console_queue_reports_output_eof_and_timeout(self):
        with tempfile.TemporaryDirectory() as directory:
            child = Child('中文\nServer loaded.\n')
            child.returncode = 17
            server = self.make(directory, child)
            try:
                server._pump()
                self.assertEqual(server.wait_for('Server loaded.'), ['中文', 'Server loaded.'])
                with self.assertRaisesRegex(process.SimError, 'code=17'):
                    server.wait_for('never')
                with self.assertRaisesRegex(process.SimError, 'timeout waiting'):
                    server.wait_for('never', timeout=0.01)
            finally:
                server.close()

    def test_server_boot_failure_uses_process_cleanup(self):
        with tempfile.TemporaryDirectory() as directory:
            child = Child()
            with patch.dict('os.environ', {'MLOG_SIM_BASEDIR': directory}), \
                    patch.object(process.subprocess, 'Popen', return_value=child), \
                    patch.object(process.threading.Thread, 'start'), \
                    patch.object(mlogsim.Server, 'wait_for', side_effect=process.SimError('boot failed')):
                with self.assertRaisesRegex(mlogsim.SimError, 'boot failed'):
                    mlogsim.Server('java', 'game.jar')
            self.assertTrue(child.stdin.closed and child.stdout.closed)
            self.assertEqual(child.waits, [15])

    def test_orphan_filter_keeps_live_parent_and_unrelated_java(self):
        processes = [
            {'ProcessId': 1, 'ParentProcessId': 0, 'Name': 'python.exe'},
            {'ProcessId': 2, 'ParentProcessId': 1, 'Name': 'java.exe', 'CommandLine': '_server160.jar'},
            {'ProcessId': 3, 'ParentProcessId': 999, 'Name': 'java.exe', 'CommandLine': 'other-game.jar'},
            {'ProcessId': 4, 'ParentProcessId': 999, 'Name': 'java.exe', 'CommandLine': '_server160.jar'},
        ]
        with patch.object(process.os, 'name', 'nt'), patch.object(process.subprocess, 'run') as kill:
            query = lambda script: processes
            self.assertEqual(process.sweep_orphans(True, query_processes=query), [4])
            kill.assert_not_called()
            self.assertEqual(process.sweep_orphans(query_processes=query), [4])
            self.assertEqual(kill.call_args.args[0], ['taskkill', '/PID', '4', '/F'])


if __name__ == '__main__':
    unittest.main()
