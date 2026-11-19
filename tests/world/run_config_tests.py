"""Explicit service contracts and side-effect-free CLI parsing."""
from pathlib import Path
import sys
import unittest
from dataclasses import FrozenInstanceError
from unittest.mock import Mock, patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from world_cli import build_parser, run
from world_runtime import ProjectionActionsServices, WorldStartupServices, WorldPaths

class ConfigTests(unittest.TestCase):
    def test_cli_keeps_defaults_and_jar_override(self):
        args=build_parser('default.jar').parse_args([])
        self.assertEqual(args.jar,'default.jar')
        self.assertEqual(args.game_port,6567)
        self.assertEqual(build_parser('default.jar').parse_args(['--jar','other.jar']).jar,'other.jar')

    def test_projection_switches_and_multiple_feeds(self):
        args=build_parser('game.jar').parse_args(['--no-projection','--watch-feed','one','--watch-feed','two','--manual'])
        self.assertTrue(args.no_projection and args.manual)
        self.assertEqual(args.watch_feed,['one','two'])

    def test_service_dependencies_are_required_and_immutable(self):
        with self.assertRaises(TypeError): ProjectionActionsServices()
        services=ProjectionActionsServices('mine','replace','demolish','clear',Mock(),Mock(),Mock(),Mock(),Mock())
        with self.assertRaises(FrozenInstanceError): services.chat=Mock()

    def test_cli_and_services_do_not_load_daemon(self):
        self.assertNotIn('world_server',sys.modules)

    def test_api_startup_failure_closes_constructed_world(self):
        import tempfile
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as root:
            jar=Path(root)/'game.jar'; jar.write_bytes(b'fixture')
            world=SimpleNamespace(close=Mock())
            factory=Mock(return_value=world)
            services=WorldStartupServices(Mock(return_value='java'),Mock(return_value=(0,None)),factory,Mock(),Mock(),Mock(),Mock())
            paths=WorldPaths.from_root(root)
            with patch('world_cli.API',side_effect=OSError('API failed')):
                with self.assertRaisesRegex(OSError,'API failed'):
                    run(['--no-host','--no-projection','--no-push-admin'],default_jar=str(jar),paths=paths,services=services)
            world.close.assert_called_once()
            self.assertIs(factory.call_args.kwargs['paths'],paths)
            self.assertTrue(factory.call_args.kwargs['no_push_admin'])
            services.projection_director.assert_not_called()

if __name__=='__main__': unittest.main()
