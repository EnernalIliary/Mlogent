"""Scene preparation contracts without a game or projection thread."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from world_scenes import layout_scenes, load_dir_scenes, world_size


class SceneTests(unittest.TestCase):
    def test_layout_shifts_frame_and_anchor_without_mutating_source(self):
        world = SimpleNamespace(js=Mock(return_value=['128,128']))
        rows = [{'anchor': [10, 20], 'frame': [8, 18, 6, 8], 'label': 'demo'}]
        before = deepcopy(rows)
        result = layout_scenes(world, rows)
        self.assertEqual(result[0]['anchor'], [32, 32])
        self.assertEqual(result[0]['frame'], [30, 30, 6, 8])
        self.assertEqual(result[0]['shift'], [22, 12])
        self.assertEqual(rows, before)

    def test_world_size_cached_and_fallback_preserved(self):
        world = SimpleNamespace(js=Mock(side_effect=RuntimeError('unavailable')))
        self.assertEqual(world_size(world), (512, 512))
        self.assertEqual(world_size(world), (512, 512))
        world.js.assert_called_once()

    def test_explicit_bad_scene_fails_but_feed_scene_can_be_skipped(self):
        missing = str(Path(__file__).parent / 'does-not-exist.json')
        with self.assertRaises(Exception):
            load_dir_scenes([missing])
        self.assertEqual(load_dir_scenes([missing], skip_bad=True), [])


if __name__ == '__main__':
    unittest.main()
