"""Map lifecycle contracts using simulated console/JS responses."""
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from world_maps import change_map


class MapTests(unittest.TestCase):
    def world(self):
        return SimpleNamespace(map_name='old', hosted=True, js=Mock(), console=Mock(return_value={'lines': ['ok']}))

    def test_missing_map_never_sends_commands(self):
        world = self.world()
        world.map_name = None
        self.assertFalse(change_map(world, {'op': 'switch'}, audit=Mock())['ok'])
        world.console.assert_not_called()

    def test_default_reset_uses_non_disconnecting_switch(self):
        world = self.world()
        world.js.side_effect = [['100'], ['0'], [], ['new'], ['players=2.0']]
        audit = Mock()
        with patch('world_maps.time.sleep'):
            result = change_map(world, {'op': 'reset', 'map': 'new'}, audit=audit)
        self.assertEqual(result, {'ok': True, 'map': 'new', 'players': 2})
        self.assertEqual([c.args[0] for c in world.console.call_args_list], ['nextmap new', 'gameover'])
        audit.assert_called_once_with('switch', map='new')

    def test_reload_timeout_preserves_old_map(self):
        world = self.world()
        world.js.return_value = ['100']
        with patch('world_maps.time.time', side_effect=[0, 46]):
            result = change_map(world, {'op': 'switch', 'map': 'new'}, audit=Mock())
        self.assertEqual(result['error'], 'map did not reload')
        self.assertEqual(world.map_name, 'old')

    def test_hard_reset_requires_successful_host(self):
        world = self.world()
        world.console.side_effect = [{'lines': []}, {'lines': ['host failed']}]
        result = change_map(world, {'op': 'reset', 'hard': True}, audit=Mock())
        self.assertFalse(result['ok'])
        world.js.assert_not_called()
        self.assertEqual([c.args[0] for c in world.console.call_args_list], ['stop', 'host old'])


if __name__ == '__main__':
    unittest.main()
