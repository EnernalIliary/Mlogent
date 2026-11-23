"""Private Unix-socket control for the optional on-demand world supervisor."""
import json
import os
from pathlib import Path
import socket

CONTROL = str(Path(__file__).resolve().parents[1] / 'out/_world/sleep.sock')


def available():
    return hasattr(socket, 'AF_UNIX') and os.path.exists(CONTROL)


def request(payload, timeout=120):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as stream:
        stream.settimeout(timeout)
        stream.connect(CONTROL)
        stream.sendall((json.dumps(payload, ensure_ascii=False) + '\n').encode())
        with stream.makefile('rb') as reader:
            line = reader.readline(8 * 1024 * 1024)
        if not line:
            raise RuntimeError('World supervisor did not respond')
        result = json.loads(line)
        if not result.get('ok') and result.get('supervisorError'):
            raise RuntimeError(result['error'])
        return result
