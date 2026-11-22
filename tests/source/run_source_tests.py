"""Executable source and comment anchors survive all public conversions."""
from pathlib import Path
import base64
import json
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[2] / 'tools'
sys.path.insert(0, str(TOOLS))

import aigenerated
from mlogent.logic import source
from mlogent.logic import labels
from mlogent.logic import payload, signature, slots


class SourceTests(unittest.TestCase):
    def test_full_unconditional_jump_reuses_zero_placeholder_without_moving_targets(self):
        for text in ('set x 1\njump 0 always 0 0\n',
                     'jump 3 equal x 1\nset x 1\njump 1 always 0 0\nend\n'):
            signed, _ = signature.sign_text(text, 'Iliary')
            self.assertEqual(signature.verify_text(signed), [])
            self.assertEqual(signature.sign_text(signed, 'Iliary')[0], signed)
            expected = signature._body(text).replace('always 0 0', 'always 0')
            self.assertEqual(signature._body(signed), expected)
            self.assertEqual(len(signature._body(signed).splitlines()), len(expected.splitlines()))
            delivered, *_ = source.to_delivery(text, 'Iliary')
            self.assertEqual(signature.verify_text(delivered), [])
            self.assertEqual(signature._body(delivered), expected)

    def test_roundtrip_keeps_control_flow_author_and_context(self):
        text = 'set n 0\nretry:\nop add n n 1\njump retry lessThan n 3\njump 0 always 0\nend\n'
        signed, _ = aigenerated.sign_text(text, 'source-test', meta={'job': 'source-context'})
        delivered, *_ = source.to_delivery(signed, 'ignored')
        editable, *_ = source.to_editable(delivered)
        self.assertTrue(editable.splitlines()[-1].startswith('# AI-Generated:Mlogent:source-test:'))
        self.assertFalse(aigenerated.verify_text(editable))
        numeric, *_ = aigenerated.resolve_labels(aigenerated._body(editable))
        self.assertEqual(numeric, aigenerated._body(delivered))
        restored, *_ = source.to_delivery(editable, 'ignored')
        self.assertEqual(restored, delivered)
        token = aigenerated._find(restored)[0]
        self.assertEqual(aigenerated.decode_meta(token.group(3))['job'], 'source-context')

    def test_comment_anchors_ignore_labels_and_keep_trailing_comments(self):
        text = ('# header\nentry:\nalias:\nset n 0\n# loop body\nretry:\n'
                'op add n n 1\njump retry lessThan n 3\njump 0 always 0\nend\n# trailing\n')
        delivered, *_ = source.to_delivery(text, 'source-test')
        editable, *_ = source.to_editable(delivered)
        expected = [(c['stmt'], c['text']) for c in aigenerated.collect_comments(text)]
        actual = [(c['stmt'], c['text']) for c in aigenerated.collect_comments(editable)]
        self.assertEqual(actual, expected)
        self.assertIn('end\n# trailing\n# AI-Generated:', editable)

    def test_decompiler_keeps_original_jump_and_signature_like_literals(self):
        text = ('print "AI-Generated:Mlogent:example"\n'
                'jump 3 always 0\nprint "skipped"\nset n 1\nend\n')
        delivered, *_ = source.to_delivery(text, 'source-test')
        with patch('mindcode.decompile_source', side_effect=lambda code, **kw: (code, 'draft')) as compiler:
            draft, diagnostic = source.extract(delivered, format='mindcode', timeout=5)
        self.assertEqual(diagnostic, 'draft')
        compiler.assert_called_once_with(draft, timeout=5)
        self.assertIn('print "AI-Generated:Mlogent:example"', draft)
        self.assertIn('jump 3 always 0', draft)
        self.assertFalse(aigenerated._find(draft))
        numeric, *_ = aigenerated.resolve_labels(draft)
        self.assertEqual(numeric, aigenerated._body(delivered))

    def test_signed_editable_output_is_always_a_comment(self):
        editable, *_ = source.to_editable('set n 1\njump 0 always 0\nend\n', sign=True)
        self.assertIsNotNone(aigenerated.SIG_COMMENT_RE.match(editable.splitlines()[-1]))
        self.assertFalse(aigenerated.verify_text(editable))
        self.assertEqual(aigenerated.collect_comments(editable), [])

    def test_invalid_signature_and_missing_safe_slot_still_fail(self):
        delivered, *_ = source.to_delivery('set n 1\njump 0 always 0\nend\n', 'source-test')
        with self.assertRaises(aigenerated.SignError):
            source.to_editable(delivered.replace('set n 1', 'set n 2'))
        with self.assertRaisesRegex(aigenerated.SignError, 'no safe signature slot'):
            source.to_delivery('set n 1\nend\n', 'source-test')

    def test_cli_keeps_normal_error_handler_after_delegation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.mlog'
            path.write_text('set n 1\nend\n', encoding='utf-8')
            result = subprocess.run([sys.executable, '-X', 'utf8', str(TOOLS / 'aigenerated.py'),
                                     'post', str(path)], capture_output=True, text=True,
                                    encoding='utf-8')
            self.assertEqual(result.returncode, 1)
            self.assertIn('no safe signature slot', result.stderr)
            self.assertNotIn('Traceback', result.stderr)
            self.assertEqual(path.read_text(encoding='utf-8'), 'set n 1\nend\n')

    def test_label_engine_imports_without_signing_or_cli(self):
        script = (
            'import sys; sys.path.insert(0, sys.argv[1]); '
            'from mlogent.logic import labels; '
            'assert "aigenerated" not in sys.modules; '
            'assert "mlog_labelize" not in sys.modules; '
            'assert "mlog_mcp" not in sys.modules'
        )
        subprocess.run([sys.executable, '-X', 'utf8', '-I', '-c', script, str(TOOLS)], check=True)

    def test_shared_scanner_resolves_aliases_and_ignores_annotations(self):
        text = '# header\nfirst:\nalias:\nset n 1\n\n# loop\nnext:\njump alias always 0\n'
        numeric, declarations, rewritten = labels.resolve(text, strict=True)
        self.assertEqual(declarations, {'first': 0, 'alias': 0, 'next': 1})
        self.assertEqual(rewritten, 1)
        self.assertEqual(numeric, '# header\nset n 1\n\n# loop\njump 0 always 0\n')
        self.assertEqual(labels.split_lines(text)[2], 2)
        with self.assertRaises(labels.LabelError):
            labels.resolve('same:\nset n 0\nsame:\nend\n', strict=True)
        with self.assertRaises(aigenerated.SignError):
            aigenerated._resolve_labels('same:\nset n 0\nsame:\nend\n', strict=True)

    def test_out_of_range_jumps_and_unknown_names_are_preserved(self):
        text = ('entry:\nset n 0\njump -1 always 0\njump 99 always 0\n'
                'jump 0 lessThan n 2\njump absent equal n 3\nend\n')
        editable, *_ = labels.labelize(text)
        self.assertIn('jump entry lessThan n 2', editable)
        for jump in ('jump -1 always 0', 'jump 99 always 0', 'jump absent equal n 3'):
            self.assertIn(jump, editable)
        self.assertEqual(labels.resolve(editable)[0], labels.resolve(text)[0])

    def test_many_jump_destinations_roundtrip(self):
        text = ''.join(f'jump {index} lessThan n 3\n' for index in range(600)) + 'end\n'
        editable, count, rewritten, names = labels.labelize(text)
        self.assertEqual((count, rewritten, len(names)), (601, 600, 600))
        self.assertEqual(labels.resolve(editable)[0], text)

    def test_signing_implementation_imports_without_legacy_entrypoints(self):
        script = (
            'import sys; sys.path.insert(0, sys.argv[1]); '
            'from mlogent.logic import source, signature, payload, slots; '
            'assert "aigenerated" not in sys.modules; '
            'assert "mlog_labelize" not in sys.modules; '
            'assert "mlog_mcp" not in sys.modules'
        )
        subprocess.run([sys.executable, '-X', 'utf8', '-I', '-c', script, str(TOOLS)], check=True)

    def test_last_safe_slot_selection_does_not_mutate_instructions(self):
        lines = ['jump 4 always 0', 'set n 1', 'jump 0 equal n 1',
                 'jump 1 always 0', 'print n', 'end']
        before = list(lines)
        slot = slots.find_slot(lines)
        self.assertEqual(slot.index, 3)
        self.assertEqual(lines, before)
        signed, _ = signature.sign_text('\n'.join(lines) + '\n', 'source-test')
        self.assertFalse(signature.verify_text(signed))
        self.assertEqual(signature._body(signed), '\n'.join(lines) + '\n')
        self.assertEqual(signed.splitlines()[-2:], ['print n', 'end'])
        self.assertIsNone(slots.find_slot(['jump 0 equal n 1', 'jump 0 always 0 1', 'end']))

    def test_bare_jump_value_is_normalized_before_hashing(self):
        signed, _ = signature.sign_text('set n 1\njump 0 always\nend\n', 'source-test')
        self.assertIn('jump 0 always 0 "AI-Generated:', signed)
        self.assertFalse(signature.verify_text(signed))
        self.assertEqual(signature.sign_text(signed, 'source-test')[0], signed)
        self.assertIs(aigenerated.SignError, payload.SignError)

    def test_payload_roundtrip_and_rejects_ambiguous_labels(self):
        comments = [{'line': 1, 'stmt': 0, 'text': '# 注释 😀'}]
        metadata = {'author': 'source-test', 'job': 'roundtrip'}
        encoded = payload.encode_comments(comments, metadata, labels={2: 'retry', 0: 'start'})
        self.assertEqual(payload.decode_signature_payload(encoded),
                         (comments, metadata, {0: 'start', 2: 'retry'}))
        for table in ([[0, 'same'], [1, 'same']], [[0, 'first'], [0, 'second']], [[True, 'bool']], []):
            with self.subTest(table=table):
                raw = json.dumps({'v': 3, 'c': [], 'labels': table}).encode('utf-8')
                invalid = base64.urlsafe_b64encode(b'j' + raw).decode('ascii').rstrip('=')
                with self.assertRaisesRegex(payload.SignError, 'bad label table'):
                    payload.decode_signature_payload(invalid)


if __name__ == '__main__':
    unittest.main()
