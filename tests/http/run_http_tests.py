"""HTTP transport contracts without importing or starting logicd."""
from __future__ import annotations

from contextlib import contextmanager
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import sys
import threading
from types import SimpleNamespace
import unittest
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from logic_http import make_handler


@contextmanager
def server(version):
    app = SimpleNamespace(SIDECAR_VERSION=version, PROTOCOL=1, LAST_PING=0,
                          STOP=threading.Event(), _exe_path=lambda: 'test-app')
    http = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(app))
    thread = threading.Thread(target=http.serve_forever, kwargs={'poll_interval': 0.01})
    thread.start()
    try:
        yield app, 'http://127.0.0.1:%d' % http.server_port
    finally:
        http.shutdown()
        http.server_close()
        thread.join(timeout=5)


def request(base, path, data=None):
    body = json.dumps(data).encode() if data is not None else None
    with urllib.request.urlopen(base + path, data=body, timeout=5) as response:
        return json.load(response), response.headers['Server']


class HTTPTests(unittest.TestCase):
    def test_applications_do_not_share_lifecycle_state(self):
        with server('first') as (first, first_url), server('second') as (second, second_url):
            health, header = request(first_url, '/health')
            self.assertEqual(health['version'], 'first')
            self.assertIn('logicd/first', header)
            self.assertGreater(first.LAST_PING, 0)
            self.assertEqual(second.LAST_PING, 0)
            request(second_url, '/ping', {})
            self.assertGreater(second.LAST_PING, 0)
            request(first_url, '/shutdown', {})
            self.assertTrue(first.STOP.wait(timeout=2))
            self.assertFalse(second.STOP.is_set())
            self.assertEqual(request(second_url, '/health')[0]['version'], 'second')

    def test_analysis_needs_no_queue_or_chat_runtime(self):
        with server('standalone') as (_, base):
            result, _ = request(base, '/analyze', {'code': 'end', 'links': []})
            self.assertTrue(result['ok'])
            self.assertEqual(result['statements'], 1)
        self.assertNotIn('logicd', sys.modules)
        self.assertNotIn('jobqueue', sys.modules)
        self.assertNotIn('chats', sys.modules)


if __name__ == '__main__':
    unittest.main()
