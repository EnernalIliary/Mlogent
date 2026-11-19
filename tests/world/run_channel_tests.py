"""Control-channel concurrency, file payload and failure contracts."""
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[2] / 'tools'
sys.path.insert(0, str(TOOLS))
from world_channel import WorldChannel


class Process:
    def __init__(self, root):
        self.data_dir = root
        self.log_path = str(Path(root) / 'log')
        self.lines = deque()
        self.seq = 0
        self.eof = False
        self.js_timeout = 1
        self._lock = threading.RLock()
        self._cv = threading.Condition()
        self.guard = threading.Lock()
        self.active = self.peak = 0
        self.threads = []
        self.result = None
        self.drop_result = False

    def emit(self, text):
        with self._cv:
            self.seq += 1
            self.lines.append((self.seq, text))
            self._cv.notify_all()

    def send(self, cmd):
        with self.guard:
            self.active += 1
            self.peak = max(self.active, self.peak)
        def respond():
            time.sleep(0.005)
            if cmd.startswith('js '):
                case = re.search(r'CASE:(\d+)', cmd)
                name = re.search(r"PrintWriter\('([^']+)'", cmd).group(1)
                self.emit('console noise')
                text = self.result if self.result is not None else 'result-' + (case.group(1) if case else '0')
                if not self.drop_result:
                    pending = Path(self.data_dir) / (name + '.tmp')
                    pending.write_text(text, encoding='utf-8')
                    with self.guard:
                        self.active -= 1
                        pending.replace(Path(self.data_dir) / name)
                    return
            else:
                self.emit('reply:' + cmd)
            with self.guard:
                self.active -= 1
        thread = threading.Thread(target=respond)
        self.threads.append(thread)
        thread.start()


class ChannelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.process = Process(self.temp.name)
        self.channel = WorldChannel(self.process)

    def tearDown(self):
        for thread in self.process.threads:
            thread.join(timeout=3)
        self.temp.cleanup()

    def test_console_ignores_output_before_request(self):
        self.process.emit('stale')
        result = self.channel.console('status', quiet=0, timeout=0.04)
        self.assertEqual(result['lines'], ['reply:status'])
        self.assertTrue(result['ok'])
        self.assertEqual(result['cmd'], 'status')

    def test_concurrent_js_and_console_do_not_mix_results(self):
        def call(index):
            if index % 2:
                return self.channel.js("sb.append('CASE:%d');" % index, timeout=2)
            return self.channel.console(str(index), quiet=0, timeout=0.04)['lines']
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(call, range(8)))
        for index, result in enumerate(results):
            self.assertEqual(result, ['result-%d' % index] if index % 2 else ['reply:%d' % index])
        self.assertEqual(self.process.peak, 1)
        self.assertEqual(list(Path(self.temp.name).glob('res-*')), [])

    def test_file_payload_is_written_as_text_not_js(self):
        text = '中文\n"quotes" \\slashes\r\nnext'
        name = self.channel.put_file(text)
        self.assertEqual((Path(self.temp.name) / name).read_bytes(), text.encode('utf-8'))
        self.assertEqual(self.channel.take_file(name), text.replace('\r\n', '\n'))
        self.assertFalse((Path(self.temp.name) / name).exists())

    def test_js_error_is_propagated(self):
        self.process.result = 'ERR\tgame error'
        with self.assertRaisesRegex(RuntimeError, 'game error'):
            self.channel.js('test')

    def test_unreadable_result_is_not_empty_success(self):
        with patch('world_channel.open', side_effect=PermissionError('busy'), create=True):
            with self.assertRaisesRegex(RuntimeError, 'console noise'):
                self.channel.js('test', timeout=0.06)

    def test_missing_file_and_process_exit_are_diagnostic(self):
        with self.assertRaisesRegex(RuntimeError, 'missing.txt'):
            self.channel.take_file('missing.txt', timeout=0.02)
        self.process.eof = True
        with self.assertRaises(SystemExit) as error:
            self.channel.wait_for('loaded', timeout=0.1)
        self.assertIn(self.process.log_path, str(error.exception))

    def test_import_does_not_load_process_or_daemon(self):
        code = ('import sys; sys.path.insert(0,sys.argv[1]); import world_channel; '
                'assert "world_server" not in sys.modules; assert "world_process" not in sys.modules')
        subprocess.run([sys.executable, '-I', '-c', code, str(TOOLS)], check=True)


if __name__ == '__main__':
    unittest.main()
