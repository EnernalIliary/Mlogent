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
from world_mirrors import _mirror_slot, mirror_push, mirror_stop, mirror_watch


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


if __name__ == '__main__':
    unittest.main()
