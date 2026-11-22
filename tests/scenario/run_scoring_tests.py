"""Scenario scoring contracts independent of sim/world execution."""
import copy
from pathlib import Path
import subprocess
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[2] / 'tools'
sys.path.insert(0, str(TOOLS))

from mlogent.scenario import scoring


class ScoringTests(unittest.TestCase):
    def test_scoring_import_does_not_load_backends(self):
        script = (
            'import sys; sys.path.insert(0, sys.argv[1]); '
            'from mlogent.scenario import scoring; '
            'assert "scenario" not in sys.modules; '
            'assert "mlogsim" not in sys.modules; '
            'assert "world_server" not in sys.modules'
        )
        subprocess.run([sys.executable, '-X', 'utf8', '-I', '-c', script, str(TOOLS)], check=True)

    def test_named_observation_wins_and_diagnostic_reports_its_samples(self):
        sc = {'observations': [
            {'name': 'last', 'logic': 'ctrl', 'var': 'n', 'aggregate': 'last'},
            {'name': 'peak', 'logic': 'ctrl', 'var': 'n', 'aggregate': 'max'},
        ], 'assertions': [
            {'id': 'peak-check', 'logic': 'ctrl', 'var': 'n', 'op': 'eq', 'value': 9,
             'observation': 'peak'},
        ]}
        record = {'samples': {0: [1, 5], 1: [9, 2]}, 'finals': {'ctrl': {'n': '8'}},
                  'refs': {}, 'checks': []}
        before = copy.deepcopy(record)
        observations = scoring.observe(sc, record)
        assertions = scoring.evaluate_assertions(sc, record, observations)
        self.assertTrue(assertions[0]['ok'])
        self.assertEqual(assertions[0]['actual'], 9)
        diagnostics = scoring.diagnostics(assertions, observations)
        self.assertEqual(diagnostics[0]['observation'], 'peak')
        self.assertEqual(diagnostics[0]['samples']['first'], [9, 2])
        self.assertEqual(record, before)
        bare = {'logic': 'ctrl', 'var': 'n'}
        self.assertEqual(scoring.pick_actual(bare, record, observations), 5)
        self.assertEqual(scoring.pick_actual(bare, record, {}), 8)

    def test_v1_checks_and_world_side_effects_remain_mandatory_assertions(self):
        record = {'refs': {}, 'finals': {}, 'checks': [
            {'logic': 'ctrl', 'var': 'n', 'expect': 1, 'actual': '1', 'ok': True},
        ], 'world_probe': {'checks': [
            {'kind': 'tile', 'x': 3, 'y': 4, 'equals': 'air', 'actual': 'wall', 'ok': False},
        ]}}
        evaluated = scoring.evaluate_assertions({}, record, {})
        self.assertEqual([a['source'] for a in evaluated], ['check', 'world_probe'])
        self.assertEqual([a['ok'] for a in evaluated], [True, False])
        message, steps = scoring.report_texts({'path': 'scene.json'}, evaluated, 10)
        self.assertIn('1 of 2 assertion(s) failed', message)
        self.assertIn('world_probe[1]', message)
        self.assertIn('scene.json', steps[-1])

    def test_missing_values_boolean_and_building_reference_comparison(self):
        self.assertTrue(scoring.compare(None, 'ne', 1))
        self.assertFalse(scoring.compare(None, 'eq', 1))
        self.assertTrue(scoring.compare('1.0', 'eq', True))
        self.assertTrue(scoring.compare('null', 'eq', False))
        self.assertTrue(scoring.compare('Building#211[3,4]:container', 'eq', 'box',
                                        {'box': (3, 4, 'container')}))
        self.assertFalse(scoring.compare('abc', 'gt', 3))
        self.assertEqual(scoring.aggregate([None, 'null', '', '2', '3'], 'sum'), 5)
        self.assertIsNone(scoring.aggregate([], 'last'))

    def test_empty_and_success_reports_and_short_sample_history(self):
        self.assertIn('asserts nothing', scoring.report_texts({}, [], 3)[0])
        self.assertEqual(scoring.brief([]), {'count': 0})
        brief = scoring.brief(list(range(20)))
        self.assertEqual(brief['first'], list(range(6)))
        self.assertEqual(brief['last'], list(range(14, 20)))
        message, steps = scoring.report_texts({}, [{'ok': True}], 3)
        self.assertIn('all 1 assertion(s) passed', message)
        self.assertEqual(steps, [])


if __name__ == '__main__':
    unittest.main()
