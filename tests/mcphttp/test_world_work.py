"""Scope/cleanup contracts for MCP's game-owned world execution leases."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import world_work


class WorldWorkTests(unittest.TestCase):
    def test_queries_and_offline_operations_do_not_wake_or_switch(self):
        for name in ('world_status', 'world_players', 'world_maps', 'world_logic_vars',
                     'mlog_sim', 'mlog_gen', 'mlog_inject', 'mlog_doctor', 'world_save',
                     'world_start', 'world_stop', 'world_pause', 'world_switch_map'):
            with self.subTest(name=name):
                client = Mock()
                fn = Mock(return_value={'ok': True})
                self.assertEqual(world_work.wrap(name, fn, client)({}), {'ok': True})
                client.call.assert_not_called()

    def test_world_work_wakes_then_restores_even_when_handler_throws(self):
        for failed in (False, True):
            client = Mock()
            client.call.return_value = {'ok': True, 'lines': ['ready']}
            fn = Mock(side_effect=RuntimeError('task failed') if failed else None, return_value='done')
            run = world_work.wrap('world_scene_probe', fn, client)
            if failed:
                with self.assertRaisesRegex(RuntimeError, 'task failed'):
                    run({})
            else:
                self.assertEqual(run({}), 'done')
            self.assertEqual(client.call.call_count, 2)
            acquired = client.call.call_args_list[0].args[0]['code']
            released = client.call.call_args_list[1].args[0]['code']
            self.assertIn('Vars.world.loadMap', acquired)
            self.assertIn("Core.settings.put('autoPause',true)", released)
            self.assertIn('Groups.player.size()===0', released)

    def test_expiry_is_game_owned_and_renewable(self):
        self.assertIn('Packages.arc.util.Timer.schedule', world_work.ACQUIRE)
        self.assertIn('Core.app.post', world_work.ACQUIRE)
        self.assertIn('now+60000', world_work.ACQUIRE)
        self.assertIn('+60000', world_work.RENEW)
        self.assertIn('delete q.leases[LEASE]', world_work.RELEASE)

    def test_switch_is_empty_only_and_original_map_is_saved_first(self):
        code = world_work.ACQUIRE
        self.assertLess(code.index('if(Groups.player.size()===0)'), code.index('Vars.world.loadMap'))
        self.assertLess(code.index('SaveIO.save'), code.index('Vars.world.loadMap'))
        self.assertIn('Player joined; automatic map switch cancelled', code)

    def test_failed_acquire_prevents_task_execution(self):
        client = Mock()
        client.call.return_value = {'ok': False, 'error': 'no map'}
        fn = Mock()
        with self.assertRaisesRegex(RuntimeError, 'lease failed'):
            world_work.wrap('world_js', fn, client)({'code': 'test'})
        fn.assert_not_called()

    def test_manual_pause_commands_and_previews_are_not_overridden(self):
        for cmd in ('pause on', 'pause off', 'config autoPause true', 'stop', 'nextmap test'):
            self.assertFalse(world_work.needs_world('world_console', {'cmd': cmd}))
        self.assertFalse(world_work.needs_world('world_logic_set', {'preview': True}))
        self.assertTrue(world_work.needs_world('world_js', {}))

    def test_abort_wraps_the_work_scope_so_scheduled_is_not_execution(self):
        text = (Path(__file__).resolve().parents[2] / 'tools/world_mcp.py').read_text(encoding='utf-8')
        self.assertLess(text.index('HANDLERS[_work_name] = _with_world_work'),
                        text.index('_install_veto(HANDLERS, TOOLS, _wc)'))


if __name__ == '__main__':
    unittest.main()
