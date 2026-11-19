"""Panel state, cache and frame contracts without a game world."""
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from world_display import sb_event, sb_render, sb_clear, frame_paint, frame_clear


class DisplayTests(unittest.TestCase):
    def test_events_are_bounded_and_worlds_are_isolated(self):
        first, second = SimpleNamespace(), SimpleNamespace()
        for i in range(5):
            sb_event(first, 0, str(i), keep=2)
        sb_event(second, 0, 'other')
        self.assertEqual(len(first._sb_log[0]), 2)
        self.assertEqual(len(second._sb_log[0]), 1)

    def test_render_uses_world_directory_and_skips_unchanged_panel(self):
        with tempfile.TemporaryDirectory() as root:
            world = SimpleNamespace(js=Mock(), data_dir=root)
            self.assertGreater(sb_render(world, 0), 0)
            self.assertTrue((Path(root) / 'sb0.txt').is_file())
            self.assertEqual(sb_render(world, 0), 0)
            world.js.assert_called_once()

    def test_clear_one_slot_keeps_other_slot(self):
        with tempfile.TemporaryDirectory() as root:
            world = SimpleNamespace(js=Mock(), data_dir=root)
            for slot in (0, 1):
                sb_event(world, slot, 'event')
                sb_render(world, slot)
            self.assertEqual(sb_clear(world, 0), 1)
            self.assertNotIn(0, world._sb_log)
            self.assertIn(1, world._sb_log)
            self.assertIn(1, world._sb_cache)

    def test_frame_results_keep_numeric_conversion(self):
        world = SimpleNamespace(js=Mock(return_value=['FRAME\tkey\t4.0']))
        self.assertEqual(frame_paint(world, [1, 2, 3, 4], 'key'), 4)
        world.js.return_value = ['FRAMECLEAR\t4.0']
        self.assertEqual(frame_clear(world, 'key'), 4)


if __name__ == '__main__':
    unittest.main()
