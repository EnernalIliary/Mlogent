"""Director startup contracts with injected world actions and no live thread."""
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from world_projection import projection_director


class ProjectionTests(unittest.TestCase):
    def test_startup_configuration_and_duplicate_start(self):
        world = SimpleNamespace(js=Mock())
        services = SimpleNamespace(SB_SWEEP_JS='clear panels', FRAME_SWEEP_JS='clear frames')
        with patch('world_projection.threading.Thread') as thread:
            self.assertTrue(projection_director(world, None, feeds=['first', 'second'],
                            frames=False, at_cell=32, hold=3, services=services))
            self.assertEqual(world._dir_feeds, ['first', 'second'])
            self.assertEqual(world._dir_cell, 32)
            self.assertEqual(world._dir_hold, 3)
            world._dir_stop = True
            thread.call_args.kwargs['target']()
            self.assertFalse(projection_director(world, None, services=services))
            thread.assert_called_once()

    def test_startup_sweeps_are_injected(self):
        world = SimpleNamespace(js=Mock())
        services = SimpleNamespace(SB_SWEEP_JS='panels', FRAME_SWEEP_JS='frames')
        with patch('world_projection.threading.Thread'):
            projection_director(world, None, services=services)
        self.assertEqual([c.args[0] for c in world.js.call_args_list][-2:], ['frames', 'panels'])


if __name__ == '__main__':
    unittest.main()
