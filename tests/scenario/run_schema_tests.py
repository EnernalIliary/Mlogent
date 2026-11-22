"""Scenario schema relocation, path precedence and legacy compatibility."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[2] / 'tools'
sys.path.insert(0, str(TOOLS))

import scenario
from mlogent.scenario import schema


def example():
    return {'version': 2, 'id': 'schema-test', 'title': 'Schema test', 'goal': 'read n',
            'world': {'size': 16}, 'limits': {'ticks': 3, 'timeout_s': 30},
            'buildings': [{'name': 'ctrl', 'block': 'micro-processor', 'x': 3, 'y': 3,
                           'code_inline': ['set n 7', 'end']}],
            'assertions': [{'id': 'n', 'logic': 'ctrl', 'var': 'n', 'op': 'eq', 'value': 7}]}


class SchemaTests(unittest.TestCase):
    def test_schema_import_does_not_load_scenario_executor(self):
        script = (
            'import sys; sys.path.insert(0, sys.argv[1]); '
            'from mlogent.scenario import schema; '
            'assert "scenario" not in sys.modules; '
            'assert "mlogsim" not in sys.modules; '
            'assert "world_server" not in sys.modules'
        )
        subprocess.run([sys.executable, '-X', 'utf8', '-I', '-c', script, str(TOOLS)], check=True)

    def test_relative_code_prefers_scenario_folder_then_explicit_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'logic').mkdir()
            (root / 'logic/main.mlog').write_text('set n 1\nend\n', encoding='utf-8')
            scenes = root / 'scenes'
            scenes.mkdir()
            document = example()
            building = document['buildings'][0]
            del building['code_inline']
            building['code'] = 'logic/main.mlog'
            path = scenes / 'test.json'
            path.write_text(json.dumps(document), encoding='utf-8')

            def load():
                return schema.load(str(path), workspace_root=str(root), shadow_dir=str(root / 'shadow'))

            loaded = load()
            self.assertIn('set n 1', loaded['buildings'][0]['code'])
            self.assertEqual(loaded['path'], str(path))
            self.assertEqual(loaded['dir'], str(scenes))
            (scenes / 'logic').mkdir()
            (scenes / 'logic/main.mlog').write_text('set n 2\nend\n', encoding='utf-8')
            self.assertIn('set n 2', load()['buildings'][0]['code'])

    def test_legacy_loader_uses_current_shadow_directory_and_error_type(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            document = example()
            document = {k: document[k] for k in ('version', 'world', 'buildings')}
            document['version'] = 1
            path = root / 'v1.json'
            path.write_text(json.dumps(document), encoding='utf-8')
            with patch.object(scenario, 'SHADOW_DIR', str(root / 'shadow')):
                loaded = scenario.load(str(path))
            self.assertEqual(loaded['version'], 1)
            self.assertEqual(loaded['buildings'][0]['code'], 'set n 7\nend')
            self.assertTrue((root / 'shadow/v1.json').is_file())
            self.assertIs(scenario.ScenarioError, schema.ScenarioError)

    def test_invalid_fields_are_collected_before_execution(self):
        document = example()
        document['limits']['ticks'] = True
        document['assertions'][0]['op'] = 'invalid'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'invalid.json'
            path.write_text(json.dumps(document), encoding='utf-8')
            with self.assertRaises(schema.ScenarioError) as failed:
                schema.load(str(path), workspace_root=directory, shadow_dir=str(Path(directory) / 'shadow'))
        self.assertIn('limits.ticks', str(failed.exception))
        self.assertIn('assertions[0].op', str(failed.exception))


if __name__ == '__main__':
    unittest.main()
