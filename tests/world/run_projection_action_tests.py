"""Projection slot lifecycle without game writes or mirror threads."""
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from world_projection_actions import project_at, end_projection, start_projection


class ActionTests(unittest.TestCase):
    def services(self):
        return SimpleNamespace(mirror_watch=Mock(), mirror_stop=Mock(), resync_builds=Mock(),
                               sb_event=Mock(), chat=Mock(), MS_CLEAR_JS='clear %(slot)d')

    def test_feed_only_projection_has_center_without_scene(self):
        world = SimpleNamespace(js=Mock())
        services = self.services()
        result = project_at(world, 4, 5, None, pin=False, tell=False, services=services)
        self.assertTrue(result['ok'])
        services.mirror_watch.assert_called_once_with(world, None, slot=0, dx=0.0, dy=0.0, cell=[4, 5])
        self.assertEqual(world._projs[0]['center'], (4, 5))

    def test_stopping_one_slot_preserves_another(self):
        world = SimpleNamespace(js=Mock(return_value=[]))
        services = self.services()
        for slot in (0, 1):
            project_at(world, slot, 5, None, slot=slot, pin=False, tell=False, services=services)
        result = end_projection(world, 0, services=services)
        self.assertTrue(result['ok'])
        self.assertNotIn(0, world._projs)
        self.assertIn(1, world._projs)
        services.mirror_stop.assert_called_once_with(world, 0)
        self.assertFalse(end_projection(world, 0, services=services)['ok'])

    def test_missing_feed_is_explicit(self):
        result = start_projection(SimpleNamespace(), {}, services=self.services())
        self.assertFalse(result['ok'])
        self.assertIn('feed', result['error'])


if __name__ == '__main__':
    unittest.main()
