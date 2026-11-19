"""World runtime cleanup and path configuration contracts."""
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from world_runtime import WorldPaths, WorldRuntime

class RuntimeTests(unittest.TestCase):
    def test_paths_are_derived_without_creating_directories(self):
        with tempfile.TemporaryDirectory() as root:
            paths=WorldPaths.from_root(root)
            # The root is resolved (Windows temp dirs come back as 8.3 names like
            # RUNNER~1, and resolve() expands them), so the expectation is derived
            # from the resolved root rather than the raw argument.
            self.assertEqual(Path(paths.root),Path(root).resolve())
            self.assertEqual(paths.handshake,str(Path(paths.root)/'out/_world/daemon.json'))
            self.assertFalse((Path(root)/'out').exists())

    def test_close_invalidates_watchers_and_removes_handshake_once(self):
        with tempfile.TemporaryDirectory() as root:
            paths=WorldPaths.from_root(root)
            Path(paths.world).mkdir(parents=True)
            Path(paths.handshake).write_text('{}')
            thread=Mock(); thread.is_alive.return_value=False
            state={'feed':'live','seq':2,'thread':thread}
            world=SimpleNamespace(close=Mock(),_mirrors={0:state},_dir_thread=thread)
            api=Mock()
            runtime=WorldRuntime(world,paths,api)
            runtime.close(); runtime.close()
            world.close.assert_called_once(); api.server_close.assert_called_once()
            self.assertTrue(world._dir_stop)
            self.assertEqual(state['seq'],3); self.assertIsNone(state['feed'])
            self.assertFalse(Path(paths.handshake).exists())
            self.assertTrue(runtime.stopped.is_set())

    def test_world_cleanup_failure_still_removes_handshake(self):
        with tempfile.TemporaryDirectory() as root:
            paths=WorldPaths.from_root(root)
            Path(paths.world).mkdir(parents=True)
            Path(paths.handshake).write_text('{}')
            runtime=WorldRuntime(SimpleNamespace(close=Mock(side_effect=RuntimeError('close failed'))),paths)
            runtime.close()
            self.assertFalse(Path(paths.handshake).exists())
            self.assertIn('close failed',runtime.cleanup_errors)

    def test_tcp_failure_does_not_skip_world_cleanup(self):
        with tempfile.TemporaryDirectory() as root:
            world=SimpleNamespace(close=Mock())
            api=Mock(); api.server_close.side_effect=OSError('socket failed')
            runtime=WorldRuntime(world,WorldPaths.from_root(root),api)
            runtime.close()
            world.close.assert_called_once()
            self.assertIn('socket failed',runtime.cleanup_errors)

if __name__=='__main__': unittest.main()
