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

    def test_stop_during_poll_does_not_process_another_frame(self):
        world = SimpleNamespace(js=Mock())
        services = SimpleNamespace(SB_SWEEP_JS='panels', FRAME_SWEEP_JS='frames')
        with patch('world_projection.threading.Thread') as thread:
            projection_director(world, None, services=services)
        world.js.reset_mock()
        with patch('world_projection.time.sleep', side_effect=lambda _: setattr(world, '_dir_stop', True)):
            thread.call_args.kwargs['target']()
        world.js.assert_not_called()

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

    def test_rearm_releases_old_slots_before_starting_new_director(self):
        thread = Mock()
        thread.is_alive.return_value = False
        world = SimpleNamespace(_dir_started=True, _dir_thread=thread,
                                _dir_frames=True, _projs={0:{'feed':'old'}, 2:{'feed':'removed'}},
                                mirror_feed='old')
        events = []
        def end(w, slot, why):
            self.assertTrue(w._dir_stop)
            thread.join.assert_called_once_with(timeout=3.0)
            events.append(slot)
            del w._projs[slot]
        def start(w, feed, at, **kwargs):
            self.assertEqual(w._projs, {})
            self.assertEqual(events, [0, 2])
            self.assertEqual(feed, 'new')
            self.assertEqual(kwargs['feeds'], ['new', 'second'])
            return True
        services = SimpleNamespace(end_projection=Mock(side_effect=end),
                                   projection_director=Mock(side_effect=start), frame_clear=Mock())
        result = control(world, {'op':'arm','feeds':['new','second']}, services=services, audit=Mock())
        self.assertTrue(result['ok'])
        self.assertEqual(result['feed'], 'new')
        services.frame_clear.assert_called_once_with(world)

    def test_rearm_wait_timeout_preserves_slots_and_does_not_restart(self):
        thread = Mock()
        thread.is_alive.return_value = True
        world = SimpleNamespace(_dir_started=True, _dir_thread=thread, _projs={0:{'feed':'old'}})
        services = SimpleNamespace(end_projection=Mock(), projection_director=Mock())
        result = control(world, {'op':'arm','feed':'new'}, services=services, audit=Mock())
        self.assertFalse(result['ok'])
        self.assertTrue(world._dir_stop)
        self.assertTrue(world._dir_started)
        self.assertIn(0, world._projs)
        services.end_projection.assert_not_called()
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
