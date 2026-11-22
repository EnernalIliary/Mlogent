"""Package boundaries and public MCP analysis behavior, including relocation."""
from pathlib import Path
import base64
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[2] / 'tools'
sys.path.insert(0, str(TOOLS))

import mlog_mcp


class PackageTests(unittest.TestCase):
    def test_analysis_import_does_not_start_server(self):
        script = (
            'import sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]); '
            'from mlogent.mcp import analysis; '
            'from mlogent.mcp import blueprints; '
            'from mlogent.mcp import compilation; '
            'from mlogent.mcp import simulation; '
            'from mlogent.mcp import tracing, tasks, queries, experiments; '
            'from mlogent.paths import TOOLS_ROOT, WORKSPACE_ROOT; '
            'assert TOOLS_ROOT == Path(sys.argv[1]).resolve(); '
            'assert WORKSPACE_ROOT == TOOLS_ROOT.parent; '
            'assert "mlog_mcp" not in sys.modules; '
            'assert "mlogsim" not in sys.modules'
        )
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run([sys.executable, '-X', 'utf8', '-I', '-c', script, str(TOOLS)],
                           cwd=directory, check=True)

    def call(self, name, arguments):
        result = mlog_mcp.handle({
            'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
            'params': {'name': name, 'arguments': arguments},
        }, emit=lambda reply: None)['result']
        self.assertFalse(result['isError'], result)
        return json.loads(result['content'][0]['text'])

    def test_public_analysis_tools_read_source(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.mlog'
            path.write_text('set n 7\nprint n\nend\n', encoding='utf-8')
            args = {'path': str(path)}
            checked = self.call('mlog_check', args)[0]
            self.assertEqual(checked['counts']['ERR'], 0)
            self.assertEqual(checked['program'], str(path))
            self.assertNotIn('findings', checked)
            ir = self.call('mlog_ir', args)[0]
            self.assertEqual(ir['statements'], 3)
            self.assertEqual(ir['unreachable'], [])
            values = self.call('mlog_values', args)[0]
            self.assertTrue(values['report'])

    def test_truncated_findings_remain_fetchable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'source.mlog'
            path.write_text('print missingA\nprint missingB\nend\n', encoding='utf-8')
            report = self.call('mlog_check', {
                'path': str(path), 'level': 'diagnostics', 'limit': 1,
            })[0]
            self.assertEqual(len(report['findings']), 1)
            fetched = self.call('mlog_fetch', {'ref': report['more']['artifact_ref']})
            self.assertTrue(json.loads(fetched['text']))

    def test_blueprint_tools_share_author_and_preserve_rollback(self):
        import aigenerated
        import msch

        with tempfile.TemporaryDirectory() as directory, \
                patch.dict('os.environ', {'MLOG_REVISION_DIR': directory}), \
                patch.object(mlog_mcp, '_MCP_AUTHOR_CACHE', None):
            generated = self.call('mlog_gen', {
                'logic': 'print 1\njump 0 always 0\nend\n', 'author': 'package-test',
            })
            original = generated['blueprint_base64']
            extracted = self.call('mlog_extract', {'blueprint_code': original})
            self.assertIn('print 1', extracted['processors'][0]['code'])
            applied = self.call('mlog_inject', {
                'blueprint_code': original, 'index': 0,
                'mlog': 'print 2\njump 0 always 0\nend\n',
            })
            code = msch.parse_base64(applied['blueprint_base64']).logic_tiles()[0].logic.code
            self.assertFalse(aigenerated.verify_text(code))
            self.assertEqual(aigenerated._find(code)[0].group(1), 'package-test')
            record = self.call('mlog_revision', {'revision': applied['revision']})
            self.assertIn('print 1', record['original_mlog'])
            restored = self.call('mlog_revision', {
                'revision': applied['revision'], 'action': 'rollback',
                'blueprint_code': applied['blueprint_base64'],
            })
            self.assertEqual(base64.b64decode(restored['blueprint_base64']),
                             base64.b64decode(original))

    def test_extract_uses_shared_artifact_store_and_current_threshold(self):
        with patch.object(mlog_mcp, 'ARTIFACT_THRESHOLD', 1):
            result = self.call('mlog_extract', {'mlog': 'print 42\nend\n'})
        processor = result['processors'][0]
        self.assertNotIn('code', processor)
        fetched = self.call('mlog_fetch', {'ref': processor['code_ref']['artifact_ref']})
        self.assertEqual(fetched['text'], 'print 42\nend\n')

    def test_compiler_deliverable_is_written_and_fetchable(self):
        result = {'ok': True, 'mlog': 'print 42\nend\n', 'diagnostics': [],
                  'tool': {'jar': 'compiler.jar', 'java': 'java'}, 'elapsed_ms': 12}
        with tempfile.TemporaryDirectory() as directory, \
                patch('mindcode.compile_file', return_value=result) as compiler, \
                patch('sourcemap.build_from_text', return_value={
                    'ok': True, 'schema': 'test-map',
                    'map': [{'mlog': 0, 'mnd_line': 1, 'why': 'prefix'},
                            {'mlog': None, 'mnd_line': 2, 'why': 'control-flow'}],
                }) as source_map:
            source = Path(directory) / 'source.mnd'
            source.write_text('\ufeffprint(42);', encoding='utf-8')
            output = Path(directory) / 'output.mlog'
            compiled = self.call('mindcode_compile', {
                'path': str(source), 'out': str(output), 'level': 'summary',
                'target': '8.0', 'optimize': False, 'map': True,
            })
            compiler.assert_called_once_with(str(source), target='8.0', optimize=False)
            self.assertTrue(compiled['ok'])
            source_map.assert_called_once_with('print(42);', target='8.0', optimize=False)
            self.assertEqual(compiled['map']['mapped'], 1)
            self.assertEqual(compiled['map']['unmapped'], 1)
            self.assertEqual(output.read_text(encoding='utf-8'), result['mlog'])
            ref = compiled['artifacts']['mlog_ref']['artifact_ref']
            self.assertEqual(self.call('mlog_fetch', {'ref': ref})['text'], result['mlog'])

    def test_compile_failures_keep_stage_and_do_not_run_validation(self):
        for tool, failure in (({}, 'unsupported_environment'),
                              ({'jar': 'compiler.jar', 'java': 'java'}, 'compilation_error')):
            with self.subTest(failure=failure), patch('mindcode.compile_source', return_value={
                    'ok': False, 'tool': tool, 'diagnostics': [{'message': 'compiler diagnostic'}],
            }), patch('mlog_eval.evaluate') as evaluate:
                for name, arguments in (
                    ('mindcode_compile', {'source': 'broken', 'level': 'diagnostics'}),
                    ('mlog_validate', {'mind': 'broken', 'level': 'diagnostics'}),
                ):
                    failed = self.call(name, arguments)
                    self.assertFalse(failed['ok'])
                    self.assertEqual(failed['stage'], 'compilation')
                    self.assertEqual(failed['failure_type'], failure)
                    self.assertEqual(failed['diagnostics'][0]['message'], 'compiler diagnostic')
                evaluate.assert_not_called()

    def test_validation_batch_aggregates_static_failure(self):
        import mschgen

        blueprint = mschgen.Blueprint('validation')
        blueprint.add_logic('print 1\nend\n')
        blueprint.add_logic('jump 99 always 0\nend\n', x=3)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.msch'
            source.write_bytes(blueprint.build())
            report = self.call('mlog_validate', {'path': str(source), 'level': 'diagnostics'})
        self.assertFalse(report['ok'])
        self.assertEqual(report['failure_type'], 'static_analysis_error')
        self.assertFalse(report['levels']['static'])
        self.assertIsNone(report['levels']['execution'])
        programs = report['artifacts']['programs']
        self.assertEqual([program['ok'] for program in programs], [True, False])

    def test_simulation_preview_and_large_text_survive_adapter(self):
        png = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=')

        def run(command):
            preview = next(arg.split('=', 1)[1] for arg in command
                           if arg.startswith('--marker-preview='))
            Path(preview).write_bytes(png)
            self.assertIn('--processor=world', command)
            self.assertIn('--compile-diagnostics', command)
            return json.dumps([{
                'vars': {'n': 42}, 'text': 'x' * 500, 'mode': 'ticks',
                'processor': 'world', 'processor_block': 'world-processor',
                'ipt': 60, 'compile': {'ok': True}, 'executed': True,
                'marker_preview': {'count': 1},
            }])

        with patch.object(mlog_mcp, '_bounded_sim_worker', side_effect=run):
            reply = mlog_mcp.handle({
                'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                'params': {'name': 'mlog_sim', 'arguments': {
                    'logic': 'setrate 60\nend\n', 'ticks': 1,
                    'processor': 'world', 'marker_preview': True,
                }},
            }, emit=lambda reply: None)['result']
        self.assertFalse(reply['isError'], reply)
        result = json.loads(reply['content'][0]['text'])
        self.assertEqual(result['ipt'], 60)
        self.assertTrue(result['compile']['ok'])
        self.assertTrue(result['executed'])
        self.assertEqual(result['vars']['n'], 42)
        self.assertEqual(self.call('mlog_fetch', {'ref': result['text']['artifact_ref']})['text'],
                         'x' * 500)
        image = next(item for item in reply['content'] if item['type'] == 'image')
        self.assertEqual(image['mimeType'], 'image/png')
        self.assertEqual(base64.b64decode(image['data']), png)

    def test_simulation_worker_obeys_current_output_budget(self):
        with patch.object(mlog_mcp, '_MCP_SIM_RESULT_LIMIT', 8):
            with self.assertRaisesRegex(RuntimeError, 'output limit'):
                mlog_mcp._bounded_sim_worker([sys.executable, '-c', "print('123456789')"])

    def test_trace_references_keep_labels_pagination_and_divergence(self):
        source = 'loop:\nset n 1\nprint n\nend\n'
        tsv = 'tick\tpc\tvars\tsource\n0\t0\tn=1\tset n 1\n0\t1\tn=1\tprint n\n'
        bundle = {'schema': 'mlog-itrace/v1', 'mlog': source, 'vars': ['n'],
                  'mode': 'ticks', 'tsv': tsv}
        current = mlog_mcp._stash(json.dumps(bundle))['artifact_ref']
        baseline = mlog_mcp._stash(json.dumps({**bundle, 'tsv': tsv.replace('n=1', 'n=0')}))['artifact_ref']
        report = self.call('mlog_trace', {
            'trace_ref': current, 'baseline_ref': baseline, 'label': 'loop',
            'limit': 1, 'vars': ['n'],
        })
        self.assertEqual(report['matched'], 2)
        self.assertEqual(report['next_offset'], 1)
        self.assertEqual(report['rows'][0]['labels'], ['loop'])
        self.assertEqual(report['first_divergence']['step'], 0)
        self.assertEqual(report['mode'], 'ticks')
        tail = self.call('mlog_trace', {'trace_ref': current, 'offset': 1})
        self.assertEqual(tail['rows'][0]['pc'], 1)
        self.assertEqual(json.loads(self.call('mlog_fetch', {'ref': current})['text']), bundle)
        with self.assertRaisesRegex(ValueError, 'unknown trace reference'):
            mlog_mcp.tool_trace({'trace_ref': 'does-not-exist'})

    def test_tasks_share_validation_store_and_resume_changed_source(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.dict('os.environ', {'MLOG_TASK_DIR': directory}):
            report = self.call('mlog_validate', {
                'logic': 'print 1\nend\n', 'hypothesis': 'check static behavior',
                'next_step': 'try simulation',
            })
            tid = report['task']['task_id']
            self.assertIn('static', self.call('mlog_task', {
                'action': 'show', 'task_id': tid,
            })['completed_stages'])
            self.call('mlog_task', {'action': 'note', 'task_id': tid, 'next_step': 'review'})
            listed = self.call('mlog_task', {'action': 'list'})
            self.assertEqual(listed['count'], 1)
            self.assertEqual(listed['tasks'][0]['next_step'], 'review')
            resumed = self.call('mlog_task', {
                'action': 'resume', 'task_id': tid, 'source': 'print 2\nend\n',
            })
            self.assertTrue(resumed['source_changed'])
            self.assertIn('static', resumed['stale_stages'])
            self.assertEqual(self.call('mlog_task', {'action': 'clear', 'task_id': tid})['removed'], [tid])
            self.assertEqual(self.call('mlog_task', {'action': 'list'})['count'], 0)

    def test_observation_differences_can_be_fetched(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = [Path(directory) / name for name in ('a.json', 'b.json')]
            for path, value in zip(paths, (0, 1)):
                path.write_text(json.dumps({'state': {'custom': {
                    f'value{i}': value for i in range(40)
                }}}), encoding='utf-8')
            args = {'a': str(paths[0]), 'b': str(paths[1])}
            summary = self.call('mlog_observe', {**args, 'level': 'summary'})
            self.assertFalse(summary['same'])
            self.assertEqual(summary['count'], 40)
            detail = self.call('mlog_observe', args)
            differences = json.loads(self.call('mlog_fetch', {
                'ref': detail['differences_ref']['artifact_ref'],
            })['text'])
            self.assertEqual(len(differences), summary['count'])

    def test_query_and_experiment_catalogues_remain_available(self):
        capabilities = self.call('mlog_fidelity', {'action': 'list'})
        self.assertEqual(capabilities['count'], len(capabilities['capabilities']))
        self.assertGreater(capabilities['count'], 0)
        catalogue = self.call('mlog_explore', {'action': 'list'})
        self.assertTrue(catalogue['templates'])
        with patch('kb_grep.search', return_value=[{'title': 'result'}]) as search:
            found = self.call('mlog_kb', {'query': '  processor  ', 'k': 100, 'kind': 'all'})
            search.assert_called_once_with('processor', k=20, include_docs=True)
            self.assertEqual(found['count'], 1)


if __name__ == '__main__':
    unittest.main()
