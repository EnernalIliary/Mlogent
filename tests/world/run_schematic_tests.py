"""Schematic contracts without modifying a game world."""
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from world_schematics import schematic


class SchematicTests(unittest.TestCase):
    def test_missing_source_does_not_execute(self):
        world = SimpleNamespace(js=Mock())
        result = schematic(world, {'op': 'schematic'}, audit=Mock(), schematic_dir='unused')
        self.assertFalse(result['ok'])
        world.js.assert_not_called()

    def test_local_name_resolution_and_placement_fields(self):
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / 'demo.msch'
            source.write_bytes(b'fixture')
            world = SimpleNamespace(js=Mock(return_value=['OK\tname=demo\tx=2\ty=3', 'TILES\t4.0']))
            audit = Mock()
            result = schematic(world, {'op': 'schematic', 'src': 'demo'}, audit=audit, schematic_dir=root)
            self.assertEqual(result, {'ok': True, 'name': 'demo', 'x': 2, 'y': 3, 'tiles': 4})
            self.assertIn(str(source).replace('\\', '/'), world.js.call_args.args[0])
            audit.assert_called_once()

    def test_export_bounds_refuse_without_execution(self):
        for width in (0, 129):
            world = SimpleNamespace(js=Mock())
            result = schematic(world, {'op': 'schematic_save', 'x': 0, 'y': 0, 'w': width, 'h': 1}, audit=Mock(), schematic_dir='unused')
            self.assertFalse(result['ok'])
            world.js.assert_not_called()

    def test_listing_and_error_shape(self):
        world = SimpleNamespace(js=Mock(return_value=['demo\t2x3\tauthor']))
        result = schematic(world, {'op': 'schematics'}, audit=Mock(), schematic_dir='isolated')
        self.assertEqual(result['items'], [{'name': 'demo', 'size': '2x3', 'author': 'author'}])
        world.js.return_value = ['ERR\tfailed']
        self.assertEqual(schematic(world, {'op': 'schematics'}, audit=Mock(), schematic_dir='isolated'), {'ok': False, 'error': 'failed'})


if __name__ == '__main__':
    unittest.main()
