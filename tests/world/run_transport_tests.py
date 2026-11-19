"""Real TCP contracts for world_protocol, without a game process."""
from contextlib import contextmanager
import json
from pathlib import Path
import socket
import subprocess
import sys
import threading
import unittest

TOOLS = Path(__file__).resolve().parents[2] / 'tools'
sys.path.insert(0, str(TOOLS))
from world_protocol import API, make_handler


@contextmanager
def server(label):
    stopped = threading.Event()
    world = {'label': label}
    def dispatch(bound_world, req, stop):
        if req.get('op') == 'fail':
            raise ValueError('operation failed')
        if req.get('op') == 'stop':
            stop()
        return {'ok': True, 'world': bound_world['label'], 'text': req.get('text')}
    api = API(('127.0.0.1', 0), make_handler(world, stopped.set, dispatch))
    thread = threading.Thread(target=api.serve_forever, kwargs={'poll_interval': 0.01})
    thread.start()
    try:
        yield api.server_address, stopped
    finally:
        api.shutdown()
        api.server_close()
        thread.join(timeout=5)


def exchange(stream, body):
    stream.write(body + b'\n')
    stream.flush()
    return json.loads(stream.readline())


class TransportTests(unittest.TestCase):
    def test_bad_request_does_not_end_connection(self):
        with server('one') as (address, _), socket.create_connection(address, timeout=3) as client:
            with client.makefile('rwb') as stream:
                result = exchange(stream, b'{broken')
                self.assertFalse(result['ok'])
                self.assertIn('bad json:', result['error'])
                request = json.dumps({'op': 'echo', 'text': '中文'}).encode('utf-8')
                self.assertEqual(exchange(stream, request), {'ok': True, 'world': 'one', 'text': '中文'})

    def test_dispatch_error_is_json_and_connection_survives(self):
        with server('one') as (address, _), socket.create_connection(address, timeout=3) as client:
            with client.makefile('rwb') as stream:
                result = exchange(stream, b'{"op":"fail"}')
                self.assertEqual(result, {'ok': False, 'error': 'ValueError: operation failed'})
                self.assertTrue(exchange(stream, b'{"op":"echo"}')['ok'])

    def test_world_and_stop_callback_are_bound_per_server(self):
        with server('one') as (first, first_stop), server('two') as (second, second_stop):
            with socket.create_connection(first, timeout=3) as client, client.makefile('rwb') as stream:
                self.assertEqual(exchange(stream, b'{"op":"stop"}')['world'], 'one')
            self.assertTrue(first_stop.wait(timeout=2))
            self.assertFalse(second_stop.is_set())
            with socket.create_connection(second, timeout=3) as client, client.makefile('rwb') as stream:
                self.assertEqual(exchange(stream, b'{"op":"echo"}')['world'], 'two')

    def test_protocol_import_does_not_load_daemon_or_simulator(self):
        code = ('import sys; sys.path.insert(0,sys.argv[1]); import world_protocol; '
                'assert "world_server" not in sys.modules; assert "mlogsim" not in sys.modules')
        subprocess.run([sys.executable, '-I', '-c', code, str(TOOLS)], check=True)


if __name__ == '__main__':
    unittest.main()
