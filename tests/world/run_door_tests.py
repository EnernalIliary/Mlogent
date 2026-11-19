"""Door persistence contracts without operating on a real world."""
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from world_doors import door_register, door_reload, door_operation


class DoorTests(unittest.TestCase):
    def test_same_tile_is_replaced_without_losing_other_doors(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'doors.json'
            world = SimpleNamespace(js=Mock(return_value=['OK']))
            for x, label in [(1, 'first'), (2, 'other'), (1, 'replacement')]:
                door_register(world, x, 3, label=label, doors_file=path)
            rows = json.loads(path.read_text(encoding='utf-8'))
            self.assertEqual(len(rows), 2)
            self.assertEqual(world._doors_meta['1,3']['scene_at'], [1, 3])
            self.assertEqual(next(r for r in rows if r['x'] == 1)['label'], 'replacement')

    def test_reload_does_not_rewrite_file(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'doors.json'
            world = SimpleNamespace(js=Mock(return_value=['OK']))
            door_register(world, 1, 2, doors_file=path)
            before = path.read_bytes()
            self.assertEqual(door_reload(world, doors_file=path), 1)
            self.assertEqual(path.read_bytes(), before)

    def test_game_refusal_does_not_persist_metadata(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'doors.json'
            world = SimpleNamespace(js=Mock(return_value=['ERR\tbad block']))
            with self.assertRaisesRegex(RuntimeError, 'bad block'):
                door_register(world, 1, 2, doors_file=path)
            self.assertFalse(path.exists())
            self.assertFalse(hasattr(world, '_doors_meta'))

    def test_nonpersistent_registration_keeps_only_memory(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'doors.json'
            world = SimpleNamespace(js=Mock(return_value=['OK']))
            door_register(world, 1, 2, persist=False, doors_file=path)
            self.assertFalse(path.exists())
            self.assertIn('1,2', world._doors_meta)

    def test_clear_updates_disk_memory_and_reload(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'doors.json'
            world = SimpleNamespace(js=Mock(return_value=['OK']))
            door_register(world, 1, 2, doors_file=path)
            world.js.return_value = ['CLEARED\t1.0']
            result = door_operation(world, {'op': 'door_clear'}, audit=Mock(), doors_file=path)
            self.assertEqual(result, {'ok': True, 'cleared': 1})
            self.assertEqual(world._doors_meta, {})
            self.assertEqual(json.loads(path.read_text()), [])
            self.assertEqual(door_reload(world, doors_file=path), 0)

    def test_no_player_is_not_reported_as_success(self):
        world = SimpleNamespace(js=Mock(return_value=['NOPLAYER']))
        audit = Mock()
        result = door_operation(world, {'op': 'door_enter'}, audit=audit, doors_file='unused')
        self.assertEqual(result, {'ok': False, 'error': 'no player online'})
        audit.assert_not_called()

    def test_taps_preserve_sequence_and_numeric_fields(self):
        world = SimpleNamespace(js=Mock(return_value=['1.0\t2.0\t3.0\t4.0\tplayer', 'SEQ\t1.0']))
        result = door_operation(world, {'op': 'taps'}, audit=Mock(), doors_file='unused')
        self.assertEqual(result['nextSeq'], 1)
        self.assertEqual(result['rows'][0], {'seq': 1, 'tick': 2, 'x': 3, 'y': 4, 'player': 'player'})


if __name__ == '__main__':
    unittest.main()
