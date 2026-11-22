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
from mlogent.logic.cleanup import clean
from mlogent.logic.controlflow import difference, extraction_diagnostics


class SourceTests(unittest.TestCase):
    def test_impact_startup_signature_extraction_roundtrip_preserves_all_86_addresses(self):
        original = (Path(__file__).parent / 'fixtures' / 'impact-startup.mlog').read_text(encoding='utf-8')
        self.assertEqual(labels.split_lines(original)[2], 86)
        delivered, *_ = source.to_delivery(original, 'Iliary')
        self.assertFalse(signature.verify_text(delivered))
        self.assertEqual(labels.split_lines(delivered)[2], 86)
        self.assertEqual(delivered.splitlines()[-1], 'op add @counter return 1')
        editable, *_ = source.to_editable(delivered)
        report = extraction_diagnostics(delivered, editable)
        self.assertEqual(report['static_jumps'], report['labeled_jumps'])
        self.assertEqual(report['unconverted_jumps'], [])
        self.assertTrue(report['safe_to_recompile'])
        self.assertTrue(report['address_sensitive'])
        self.assertEqual([x['instruction'] for x in report['counter_writes']], [85])
        self.assertEqual([x['instruction'] for x in report['counter_reads']], [15, 43])
        for target in (20, 21, 34, 63, 64, 67):
            self.assertIn(f'L{target}:\n', editable)
        self.assertEqual(editable.count('L67:'), 1)
        self.assertEqual(editable.count('jump L67 always'), 2)
        rebuilt, *_ = source.to_delivery(editable, 'ignored')
        self.assertTrue(difference(original, rebuilt)['instruction_semantics_preserved'])
        self.assertEqual(difference(original, rebuilt)['jump_target_changes'], [])
        self.assertFalse(signature.verify_text(rebuilt))

    def test_label_namespace_and_boundary_diagnostics(self):
        original = 'set L2 9\njump 2 always 0\njump 2 equal L2 9\njump 4 always 0\n'
        editable, *_ = source.to_editable(original)
        self.assertIn('L2_2:\n', editable)
        self.assertEqual(editable.count('L2_2:'), 1)
        report = extraction_diagnostics(original, editable)
        self.assertEqual(report['labeled_jumps'], 2)
        self.assertEqual(report['unconverted_jumps'][0]['target'], 4)
        self.assertFalse(report['safe_to_recompile'])
        self.assertTrue(report['conversion']['instruction_semantics_preserved'])
        original = 'jump missing always 0\njump -1 always 0\n'
        editable, *_ = source.to_editable(original)
        self.assertEqual(len(extraction_diagnostics(original, editable)['unconverted_jumps']), 2)

    def test_signature_no_longer_adds_end_and_detects_appended_instructions(self):
        original = 'set return @counter\njump 3 always 0 false\nend\nop add @counter return 1\n'
        signed, _ = signature.sign_text(original, 'Iliary')
        self.assertEqual(labels.split_lines(signed)[2], 4)
        self.assertTrue(difference(original, signed)['instruction_semantics_preserved'])
        self.assertTrue(signature.verify_text(signed + 'end\n'))

    def test_conversion_guard_rejects_layout_target_and_counter_changes(self):
        original = 'set return @counter\njump 3 always 0\nend\nop add @counter return 1\n'
        for changed in (original + 'end\n', original.replace('jump 3', 'jump 2'),
                        original.replace('return 1', 'return 2')):
            self.assertFalse(difference(original, changed)['instruction_semantics_preserved'])
        with self.assertRaisesRegex(ValueError, '@counter'):
            labels.check_jump_targets(original, original.replace('return 1', 'return 2'))

    def test_old_marker_like_variable_is_an_instruction_not_legacy_metadata(self):
        original = 'set aigenerated.abcdef123456 7\njump 0 always 0\n'
        signed, *_ = source.to_delivery(original, 'Iliary')
        self.assertEqual(signature._body(signed), original)
        self.assertEqual(labels.split_lines(signed)[2], 2)

    def test_cleanup_removes_only_ignored_editor_default_suffixes(self):
        examples = {
            'jump 7 always a b\n': 'jump 7 always\n',
            'op abs result x b\n': 'op abs result x\n',
            'ucontrol move x y false a b\n': 'ucontrol move x y\n',
            'draw clear true false a b true false\n': 'draw clear\n',
            'print "two words" a b\n': 'print "two words"\n',
            'end true false a b\n': 'end\n',
            '  entry:\r\n  print "hello" a b\r\n': '  entry:\r\n  print "hello"\r\n',
        }
        for before, expected in examples.items():
            with self.subTest(before=before):
                after, changes = clean(before)
                self.assertEqual(after, expected)
                self.assertTrue(changes)
                self.assertEqual(len(after.splitlines()), len(before.splitlines()))
                self.assertEqual(clean(after), (after, []))

    def test_cleanup_preserves_meaningful_values_declarations_and_unknown_syntax(self):
        for text in ('op add result a b\n', 'set a b\n', 'jump 0 equal a b\n',
                     'jump 0 always 0 0\n', 'jump 0 always a customDeclaration\n',
                     'print x b customDeclaration\n', 'print x "a"\n',
                     'modded x a b\n', 'op unknown result a b\n',
                     'ucontrol unknown a b\n', 'end a b # a\n', 'end; set x a\n'):
            with self.subTest(text=text):
                self.assertEqual(clean(text), (text, []))
        signed, _ = signature.sign_text('op abs out x b\njump 0 always 0\n', 'Iliary')
        self.assertEqual(clean(signed), (signed, []))
        self.assertFalse(signature.verify_text(signed))

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
        self.assertEqual(aigenerated._body(restored), aigenerated._body(delivered))
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
        self.assertIn('jump L3 always 0', draft)
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
