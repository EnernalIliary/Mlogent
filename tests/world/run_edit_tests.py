"""Editing contracts without changing a running world."""
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from world_edits import edit


class EditTests(unittest.TestCase):
    def test_empty_block_is_refused_without_execution(self):
        world = SimpleNamespace(js=Mock())
        audit = Mock()
        self.assertFalse(edit(world, {'op': 'place'}, audit=audit, data_dir='unused')['ok'])
        world.js.assert_not_called()
        audit.assert_not_called()

    def test_placement_error_preserves_audit(self):
        world = SimpleNamespace(js=Mock(return_value=['ERR\tbad block']))
        audit = Mock()
        result = edit(world, {'op': 'place', 'block': 'bad', 'x': 1, 'y': 2}, audit=audit, data_dir='unused')
        self.assertEqual(result, {'ok': False, 'error': 'bad block'})
        audit.assert_called_once_with('place', block='bad', x=1, y=2)

    def test_spawn_count_and_unit_fields(self):
        world = SimpleNamespace(js=Mock(return_value=['SPAWNED\t1.0', 'U\t7\tmono\tsharded\t1.5\t2']))
        result = edit(world, {'op': 'spawn', 'type': 'mono'}, audit=Mock(), data_dir='unused')
        self.assertEqual(result['spawned'], 1)
        self.assertEqual(result['units'][0]['x'], 1.5)

    def test_logic_source_uses_file_channel_and_explicit_directory(self):
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / 'source.txt'
            source.write_text('end', encoding='utf-8')
            world = SimpleNamespace(js=Mock(return_value=['OK\t3']), put_file=Mock(return_value=source.name))
            result = edit(world, {'op': 'logic_set', 'x': 1, 'y': 2, 'code': 'end'}, audit=Mock(), data_dir=root)
            world.put_file.assert_called_once_with('end', 'src')
            self.assertEqual(result['codeLen'], 3)
            self.assertFalse(source.exists())


if __name__ == '__main__':
    unittest.main()
