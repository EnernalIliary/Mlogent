"""Contracts for calling the logic service without the sidecar runtime."""
from __future__ import annotations

import base64
from pathlib import Path
import subprocess
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[2] / 'tools'
sys.path.insert(0, str(TOOLS))

import logic_service as service
import msch


class ServiceTests(unittest.TestCase):
    def test_queue_gate_does_not_load_sidecar(self):
        code = (
            'import sys; sys.path.insert(0, sys.argv[1]); '
            'import jobqueue; '
            'assert jobqueue.gate("end", None)["ok"]; '
            'assert "logicd" not in sys.modules; '
            'assert "chats" not in sys.modules; '
            'assert "http.server" not in sys.modules'
        )
        subprocess.run([sys.executable, '-I', '-c', code, str(TOOLS)], check=True)

    def test_empty_link_table_is_authoritative(self):
        code = 'printflush message1\nend'
        unknown = service.analyse(code, None)
        empty = service.analyse(code, [])
        self.assertNotIn('link-name-not-bound', [f['rid'] for f in unknown['findings']])
        self.assertIn('link-name-not-bound', [f['rid'] for f in empty['findings']])

    def test_signed_payload_uses_relative_coordinates(self):
        result = service.compose({
            'template': 'timer-flush', 'origin': {'x': 20, 'y': 30},
            'links': [{'name': 'message2', 'x': 21, 'y': 31},
                      {'name': 'message3', 'x': 25, 'y': 36}],
        })
        self.assertTrue(result['ok'])
        self.assertTrue(result['sig'])
        self.assertIn('printflush message2', result['code'])
        parsed = msch.parse_logic(base64.b64decode(result['bytes_b64']))
        self.assertEqual(parsed.code, result['code'])
        self.assertEqual([(p.name, p.x, p.y) for p in parsed.links],
                         [('message2', 1, 1), ('message3', 5, 6)])

    def test_plan_refuses_missing_links(self):
        result = service.plan({'intent': 'timer every 2 seconds', 'links': []})
        self.assertEqual(result['template'], 'timer-flush')
        self.assertFalse(result['ok'])
        self.assertIn('template-needs-link', [f['rid'] for f in result['findings']])

    def test_unmatched_intent_is_explicit(self):
        result = service.plan({'intent': 'xyzzy'})
        self.assertFalse(result['ok'])
        self.assertIsNone(result['template'])
        self.assertTrue(result['candidates'])


if __name__ == '__main__':
    unittest.main()
