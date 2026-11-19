"""Director startup contracts with injected world actions and no live thread."""
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from world_projection import projection_director, control


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

    def test_arm_missing_feed_never_starts_director(self):
        services = SimpleNamespace(projection_director=Mock())
        result = control(SimpleNamespace(), {'op':'arm'}, services=services, audit=Mock())
        self.assertFalse(result['ok'])
        services.projection_director.assert_not_called()

    def test_projection_off_stops_all_mirrors(self):
        world = SimpleNamespace()
        services = SimpleNamespace(mirror_stop=Mock())
        self.assertEqual(control(world, {'op':'projection','on':False}, services=services, audit=Mock()), {'ok':True,'on':False})
        services.mirror_stop.assert_called_once_with(world)

    def test_projection_status_keeps_sorted_slots_and_legacy_summary(self):
        world = SimpleNamespace(_projs={2:{'center':(3,4),'builds':[],'feed':'two'},0:{'center':(1,2),'builds':[],'feed':'zero'}})
        services = SimpleNamespace(_mirror_slot=Mock(return_value={'off':(5,6)}))
        result = control(world, {'op':'projstat'}, services=services, audit=Mock())
        self.assertEqual([p['slot'] for p in result['projections']], [0,2])
        self.assertEqual(result['center'], [1,2])
        self.assertEqual(result['count'], 2)

    def test_frame_clear_uses_explicit_action(self):
        world = SimpleNamespace()
        services = SimpleNamespace(frame_clear=Mock(return_value=4))
        result = control(world, {'op':'frames','action':'clear','scene':'demo'}, services=services, audit=Mock())
        self.assertEqual(result, {'ok':True,'restored':4})
        services.frame_clear.assert_called_once_with(world,'demo')


if __name__ == '__main__':
    unittest.main()
