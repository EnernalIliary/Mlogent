"""Startup and compatibility contracts for the sidecar entry point."""
from contextlib import redirect_stdout
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[2] / 'tools'
sys.path.insert(0, str(TOOLS))
from logic_cli import main
from logic_runtime import Application


class CLITests(unittest.TestCase):
    def test_compatibility_import_is_lazy_and_state_is_shared(self):
        code = '''import sys
sys.path.insert(0, sys.argv[1])
import logicd, logic_runtime, logic_service
assert logic_runtime._DEFAULT is None
assert logicd.analyse is logic_service.analyse
app = logicd.APP
assert logicd.LLM_STATE is app.LLM_STATE
assert logicd.STOP is app.STOP
app.JOB_WORKERS = 7
assert logicd.JOB_WORKERS == 7
assert logicd.Handler.app is app
assert app.JOBS is None and app.chat_store is None
'''
        subprocess.run([sys.executable, '-I', '-c', code, str(TOOLS)], check=True)

    def test_one_shot_commands_do_not_create_stores(self):
        with tempfile.TemporaryDirectory() as root:
            for options in (['--print-template', 'patrol'], ['--plan', 'timer every 2 seconds']):
                result = subprocess.run(
                    [sys.executable, str(TOOLS / 'logicd.py'), *options,
                     '--jobs-dir', str(Path(root) / 'jobs'),
                     '--chats-dir', str(Path(root) / 'chats')],
                    cwd=root, capture_output=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(result.stdout)
                self.assertEqual(list(Path(root).iterdir()), [])

    def test_unknown_template_is_explicit_without_storage(self):
        with tempfile.TemporaryDirectory() as root:
            app = Application(root)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(['--print-template', 'unknown'], application=app), 2)
            self.assertIsNone(app.JOBS)
            self.assertFalse((Path(root) / 'out').exists())

    def test_failed_worker_start_still_closes_application(self):
        with tempfile.TemporaryDirectory() as root:
            app = Application(root)
            with patch('logic_cli.jobqueue.Queue') as factory:
                factory.return_value.start.side_effect = RuntimeError('start failed')
                with self.assertRaisesRegex(RuntimeError, 'start failed'):
                    main([], application=app)
                factory.return_value.stop.assert_called_once()
            self.assertTrue(app.closed)
            self.assertTrue(app.STOP.is_set())


if __name__ == '__main__':
    unittest.main()
