"""Veto must fail closed, and never execute on cancellation or missing state."""
import importlib.util
import pathlib
import base64
import re
import unittest
from unittest.mock import patch, Mock
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location('world_abort', pathlib.Path(__file__).resolve().parents[1] / 'tools/world_abort.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class VetoTests(unittest.TestCase):
    def test_player_announcements_describe_function(self):
        self.assertEqual(guard.describe_action('world_stop', {}), '关闭游戏服务器')
        self.assertIn('作用：清除当前试验场景', guard.describe_action('world_js', {'purpose': '清除当前试验场景'}))
        for name in guard.DESTRUCTIVE:
            self.assertNotIn('world_', guard.describe_action(name, {}))
        self.assertIn('地图编号：25122', guard.describe_action('world_switch_map', {'map_id': 25122}))

    def test_pending_mutation_requires_purpose(self):
        with self.assertRaisesRegex(ValueError, 'purpose'):
            guard.schedule(None, 'world_js', Mock(), {'code': "Vars.state.wave=1"})

    def test_mutation_tool_schema_requires_purpose(self):
        tools = [{'name': 'world_js', 'description': 'JS', 'inputSchema': {
            'type': 'object', 'properties': {'code': {'type': 'string'}}, 'required': ['code']}}]
        guard.install({'world_js': Mock()}, tools, SimpleNamespace())
        self.assertIn('purpose', tools[0]['inputSchema']['required'])

    def test_in_game_notice_contains_agent_purpose(self):
        captured = []
        def js(_client, code):
            if code == guard.GAME_INSTALL:
                return 'ready'
            captured.append(code)
            return 'queued'
        purpose = '清理指定区域的测试建筑'
        with patch.object(guard, '_js', side_effect=js), patch.object(guard, '_record'), patch.object(guard.threading, 'Thread') as thread:
            result = guard.schedule(None, 'world_js', Mock(), {'code': "test", 'purpose': purpose})
        encoded = re.search(r'decode\("([A-Za-z0-9+/=]+)"\)', captured[0]).group(1)
        notice = base64.b64decode(encoded).decode('utf-8')
        self.assertIn(purpose, notice)
        self.assertEqual(result['purpose'], purpose)
        self.assertNotIn('purpose', thread.call_args.kwargs['args'][4])

    def test_delays(self):
        self.assertEqual(guard.delay_for('world_stop', {}), 60)
        for name in ('world_load', 'world_reset', 'world_clear', 'world_kill_units', 'world_switch_map'):
            self.assertEqual(guard.delay_for(name, {}), 15)
        self.assertEqual(guard.delay_for('world_status', {}), 0)
        self.assertEqual(guard.delay_for('world_push_action', {'action': 'switch_map'}), 15)
        self.assertEqual(guard.delay_for('world_js', {'code': '// a harmless string mentioning stop'}), 15)
        self.assertEqual(guard.delay_for('world_js', {'code': 'Vars.net.closeServer();'}), 60)
        self.assertEqual(guard.delay_for('world_console', {'cmd': 'stop'}), 60)

    def test_veto_and_state_loss_never_execute(self):
        for state in ('cancelled', 'lost', 'early'):
            with self.subTest(state=state), patch.object(guard.time, 'sleep'), patch.object(guard, '_js', return_value=state), patch.object(guard, '_record'):
                calls = []
                guard._finish(None, 'a'*32, 15, lambda args: calls.append(args), {})
                self.assertEqual(calls, [])

    def test_only_claimed_operation_executes(self):
        with patch.object(guard.time, 'sleep'), patch.object(guard, '_js', return_value='execute'), patch.object(guard, '_record') as record:
            calls = []
            guard._finish(None, 'a'*32, 15, lambda args: calls.append(args), {'x': 1})
            self.assertEqual(calls, [{'x': 1}])
            self.assertEqual(record.call_args.kwargs['state'], 'completed')

    def test_disconnected_control_fails_closed(self):
        with patch.object(guard.time, 'sleep'), patch.object(guard, '_js', side_effect=RuntimeError('offline')), patch.object(guard, '_record') as record:
            calls = []
            guard._finish(None, 'a'*32, 15, lambda args: calls.append(args), {})
            self.assertEqual(calls, [])
            self.assertEqual(record.call_args.kwargs['state'], 'failed')

    def test_submission_only_stages_and_never_calls_handler(self):
        with patch.object(guard, '_js', side_effect=['ready', 'queued']), patch.object(guard, '_record'), patch.object(guard.threading, 'Thread') as thread:
            calls = []
            result = guard.schedule(None, 'world_stop', lambda args: calls.append(args), {'purpose': '安全关闭测试服务器'})
            self.assertEqual(result['status'], 'scheduled')
            self.assertEqual(result['delay_seconds'], 60)
            self.assertEqual(calls, [])
            thread.return_value.start.assert_called_once()

    def test_sleeping_shutdown_is_immediate_without_game_veto_or_handler(self):
        stopped = {'ok': True, 'handled': True, 'status': 'stopped', 'manualStop': True}
        client = SimpleNamespace(stop_if_sleeping=Mock(return_value=stopped))
        handler = Mock()
        with patch.object(guard, '_js') as js, patch.object(guard.threading, 'Thread') as thread:
            self.assertEqual(guard.schedule(client, 'world_stop', handler, {'purpose': '安全关闭测试服务器'}), stopped)
            js.assert_not_called()
            thread.assert_not_called()
            handler.assert_not_called()

    def test_running_managed_shutdown_retains_sixty_second_veto(self):
        client = SimpleNamespace(stop_if_sleeping=Mock(return_value=None))
        with patch.object(guard, '_js', side_effect=['ready', 'queued']), patch.object(guard, '_record'), patch.object(guard.threading, 'Thread'):
            result = guard.schedule(client, 'world_stop', Mock(), {'purpose': '安全关闭测试服务器'})
        self.assertEqual(result['status'], 'scheduled')
        self.assertEqual(result['delay_seconds'], 60)


if __name__ == '__main__':
    unittest.main()
