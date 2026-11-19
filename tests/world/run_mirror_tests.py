"""Marker generation and slot contracts without a live world."""
import base64
import json
from pathlib import Path
import re
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from world_mirrors import _mirror_slot, mirror_push, mirror_stop, mirror_watch, control


class MirrorTests(unittest.TestCase):
    def test_stale_frame_is_rejected_without_js(self):
        world = SimpleNamespace(js=Mock())
        _mirror_slot(world, 0)['seq'] = 2
        self.assertFalse(mirror_push(world, [], gen=1)['ok'])
        world.js.assert_not_called()

    def test_generation_is_checked_again_after_install(self):
        world = SimpleNamespace()
        def install(_):
            _mirror_slot(world, 0)['seq'] += 1
            return []
        world.js = Mock(side_effect=install)
        self.assertFalse(mirror_push(world, [], gen=0)['ok'])
        world.js.assert_called_once()

    def test_offsets_are_encoded_without_mutating_units(self):
        world = SimpleNamespace(js=Mock(side_effect=[[], ['1.0']]))
        units = [{'type': 'mono', 'x': 1, 'y': 2}]
        self.assertEqual(mirror_push(world, units, dx=3, dy=4, slot=2), {'ok': True, 'count': 1})
        encoded = re.search(r"decode\('([^']+)'", world.js.call_args.args[0]).group(1)
        self.assertEqual(json.loads(base64.b64decode(encoded))[0]['x'], 4)
        self.assertEqual(units[0]['x'], 1)

    def test_watch_replacement_and_stop_are_slot_local(self):
        world = SimpleNamespace(js=Mock(return_value=['0']))
        with patch('world_mirrors.time.sleep'), patch('world_mirrors.threading.Thread') as thread:
            mirror_watch(world, 'first', slot=0)
            old = _mirror_slot(world, 0)['seq']
            mirror_watch(world, 'second', slot=1)
            mirror_stop(world, 0)
            self.assertGreater(_mirror_slot(world, 0)['seq'], old)
            self.assertIsNone(_mirror_slot(world, 0)['feed'])
            self.assertEqual(_mirror_slot(world, 1)['feed'], 'second')
            self.assertEqual(thread.call_count, 2)

    def test_feed_control_uses_explicit_root_and_slot(self):
        import os
        world = SimpleNamespace()
        audit = Mock()
        with patch('world_mirrors.mirror_watch') as watch:
            result = control(world, {'op':'mirror_feed','path':'feed.json','slot':2,'dx':3}, root='isolated', audit=audit)
        expected = os.path.join('isolated','feed.json')
        self.assertEqual(result['path'], expected)
        watch.assert_called_once_with(world, expected.replace('\\','/'), slot=2, dx=3.0, dy=0.0)

    def test_marker_coordinates_and_audit_stay_in_tiles(self):
        world = SimpleNamespace(js=Mock(side_effect=[[],['OK']]))
        audit = Mock()
        result = control(world, {'op':'marker','x':2,'y':3}, root='unused', audit=audit)
        self.assertEqual(result, {'ok':True,'id':9001,'kind':'point'})
        audit.assert_called_once_with('marker',kind='point',x=2.0,y=3.0,id=9001)

    def test_failed_install_does_not_apply_marker_action(self):
        world = SimpleNamespace(js=Mock(return_value=['ERR\tinstall failed']))
        result = control(world, {'op':'marker'}, root='unused', audit=Mock())
        self.assertEqual(result, {'ok':False,'error':'install failed'})
        world.js.assert_called_once()


if __name__ == '__main__':
    unittest.main()
