"""Scene preparation contracts without a game or projection thread."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from world_scenes import layout_scenes, load_dir_scenes, world_size, execute


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

    def test_scene_missing_path_has_no_side_effects(self):
        world = SimpleNamespace(js=Mock())
        actions = dict(audit=Mock(),door_register=Mock(),mirror_stop=Mock(),mirror_watch=Mock())
        self.assertEqual(execute(world, {'op':'scene'}, **actions), {'ok':False,'error':'need path'})
        for action in actions.values(): action.assert_not_called()

    def test_scene_report_mirror_shift_and_audit(self):
        world = SimpleNamespace()
        actions = dict(audit=Mock(),door_register=Mock(),mirror_stop=Mock(),mirror_watch=Mock())
        report = {'errors':[],'anchor':[1,2],'shift':[3,4],'placed':2,'units':1}
        with patch('scene.load', return_value={'name':'demo'}), patch('scene.apply_world', return_value=report):
            result = execute(world, {'op':'scene','path':'demo','mirror_feed':'feed','mirror_slot':2}, **actions)
        self.assertTrue(result['ok'])
        self.assertIs(world._scene_report, report)
        actions['mirror_stop'].assert_called_once_with(world)
        actions['mirror_watch'].assert_called_once_with(world,'feed',slot=2,dx=3.0,dy=4.0)
        actions['audit'].assert_called_once_with('scene',path='demo',name='demo',shift=[3,4],placed=2,units=1,errors=0)


if __name__ == '__main__':
    unittest.main()
