"""JVM lifecycle contracts using owned fake processes and temporary paths."""
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from world_process import WorldProcess
from world_runtime import WorldPaths
import world_server


class Process:
    def __init__(self, text='', stubborn=False):
        self.stdin = io.StringIO()
        self.stdout = io.StringIO(text)
        self.returncode = None
        self.stubborn = stubborn
        self.killed = False
        self.waited = False

    def poll(self):
        return self.returncode

    def wait(self, timeout):
        self.waited = True
        if self.stubborn and self.returncode is None:
            raise subprocess.TimeoutExpired('fake-java', timeout)
        self.returncode = 0 if self.returncode is None else self.returncode
        return self.returncode

    def kill(self):
        self.killed = True
        self.returncode = -9


class ProcessTests(unittest.TestCase):
    def test_managed_boot_waits_for_explicit_game_thread_result(self):
        for resume in ('', 'mcp-hibernate-123'):
            with self.subTest(resume=resume), tempfile.TemporaryDirectory() as root:
                world = world_server.World.__new__(world_server.World)
                world.map_name = 'debug map'
                world.game_port = 16567
                world.paths = WorldPaths.from_root(root)
                world._wait = Mock()
                world.console = Mock(return_value={'lines': ['[ContentPatcher] warning']})
                world.js = Mock(side_effect=lambda body, **kw: ['managed-host-ready']
                                if 'managed-host-not-ready' in body else ['installed'])
                with patch.dict(os.environ, {'MLOG_WORLD_SLEEP_MANAGED': '1',
                                             'MLOG_WORLD_RESUME_SAVE': resume}):
                    world._boot(host=True, paused=False, server_name=None)
                self.assertTrue(world.hosted)
                self.assertFalse(any(c.args[0].startswith('js ') for c in world.console.call_args_list))
                hosts = [c for c in world.js.call_args_list if 'managed-host-not-ready' in c.args[0]]
                self.assertEqual(len(hosts), 1)
                self.assertEqual(hosts[0].kwargs['timeout'], 180)
                self.assertIn('SaveIO.load' if resume else 'Vars.world.loadMap', hosts[0].args[0])

    def test_managed_boot_does_not_accept_unopened_server(self):
        world = world_server.World.__new__(world_server.World)
        world.map_name = 'debug map'
        world.game_port = 16567
        world._wait = Mock()
        world.console = Mock(return_value={'lines': []})
        world.js = Mock(return_value=['managed-host-not-ready'])
        world.close = Mock()
        with patch.dict(os.environ, {'MLOG_WORLD_SLEEP_MANAGED': '1', 'MLOG_WORLD_RESUME_SAVE': ''}):
            with self.assertRaisesRegex(SystemExit, 'managed-host-not-ready'):
                world._boot(host=True, paused=False, server_name=None)
        world.close.assert_called_once()

    def test_graceful_exit_reaps_and_closes_resources_once(self):
        with tempfile.TemporaryDirectory() as root:
            fake = Process('loaded\n中文\n')
            with patch('world_process.subprocess.Popen', return_value=fake), \
                    patch('world_process._win_kill_with_parent', return_value=123), \
                    patch('world_process._release_job') as release:
                process = WorldProcess('java', 'game.jar', data_dir=root, log_path=Path(root) / 'log')
                process._pump_thread.join(timeout=2)
                self.assertEqual(list(process.lines), [(1, 'loaded'), (2, '中文')])
                process.close()
                process.close()
                release.assert_called_once_with(123)
            self.assertFalse(fake.killed)
            self.assertTrue(fake.waited)
            self.assertTrue(fake.stdin.closed and fake.stdout.closed)
            self.assertTrue(process._logf.closed)
            self.assertTrue(process.eof)
            self.assertEqual(process.cleanup_errors, [])

    def test_unresponsive_process_is_killed_and_reaped(self):
        with tempfile.TemporaryDirectory() as root:
            fake = Process(stubborn=True)
            with patch('world_process.subprocess.Popen', return_value=fake), \
                    patch('world_process._win_kill_with_parent', return_value=None):
                process = WorldProcess('java', 'game.jar', data_dir=root, log_path=Path(root) / 'log')
                process.close()
            self.assertTrue(fake.killed and fake.waited)
            self.assertTrue(fake.stdin.closed and fake.stdout.closed)

    def test_spawn_failure_closes_log_and_preserves_original_error(self):
        with tempfile.TemporaryDirectory() as root:
            process = WorldProcess.__new__(WorldProcess)
            with patch('world_process.subprocess.Popen', side_effect=OSError('spawn failed')):
                with self.assertRaisesRegex(OSError, 'spawn failed'):
                    process.__init__('java', 'game.jar', data_dir=root, log_path=Path(root) / 'log')
            self.assertTrue(process._logf.closed)
            self.assertTrue(process._closed)

    def test_pump_failure_notifies_eof(self):
        class BrokenOutput(io.StringIO):
            def __iter__(self):
                raise OSError('output failed')
        with tempfile.TemporaryDirectory() as root:
            fake = Process()
            fake.stdout = BrokenOutput()
            with patch('world_process.subprocess.Popen', return_value=fake), \
                    patch('world_process._win_kill_with_parent', return_value=None):
                with WorldProcess('java', 'game.jar', data_dir=root, log_path=Path(root) / 'log') as process:
                    process._pump_thread.join(timeout=2)
                    self.assertTrue(process.eof)
                    self.assertEqual(process.pump_error, 'output failed')

    def test_world_boot_failure_releases_started_process(self):
        with tempfile.TemporaryDirectory() as root:
            fake = Process()
            with patch.multiple(world_server, DATA=str(Path(root) / 'data'), WORLD=root,
                                LOG=str(Path(root) / 'log')), \
                    patch('world_process.subprocess.Popen', return_value=fake), \
                    patch('world_process._win_kill_with_parent', return_value=None), \
                    patch.object(world_server.World, '_boot', side_effect=SystemExit('boot failed')):
                with self.assertRaisesRegex(SystemExit, 'boot failed'):
                    world_server.World('java', 'game.jar', host=False)
            self.assertTrue(fake.killed and fake.waited)
            self.assertTrue(fake.stdin.closed and fake.stdout.closed)

    def test_paths_and_admin_policy_are_set_before_boot(self):
        with tempfile.TemporaryDirectory() as root:
            paths=WorldPaths.from_root(root)
            fake=Process()
            def boot(world, **kwargs):
                self.assertTrue(world.no_push_admin)
                self.assertEqual(world.data_dir,paths.data)
                self.assertEqual(world.log_path,paths.log)
            with patch('world_process.subprocess.Popen',return_value=fake), patch('world_process._win_kill_with_parent',return_value=None), patch.object(world_server.World,'_boot',autospec=True,side_effect=boot):
                with world_server.World('java','game.jar',host=False,paths=paths,no_push_admin=True): pass
            self.assertTrue(fake.stdin.closed and fake.stdout.closed)


if __name__ == '__main__':
    unittest.main()
