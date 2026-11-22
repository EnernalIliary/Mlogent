"""Simulator script/record contracts without starting a game process."""
import io
from pathlib import Path
import subprocess
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[2] / 'tools'
sys.path.insert(0, str(TOOLS))

from mlogent.simulation import scripts, results


class DataTests(unittest.TestCase):
    def test_builders_and_parsers_import_without_runtime(self):
        script = (
            'import sys; sys.path.insert(0, sys.argv[1]); '
            'from mlogent.simulation import scripts, results; '
            'assert "mlogsim" not in sys.modules; '
            'assert "mlogent.simulation.process" not in sys.modules'
        )
        subprocess.run([sys.executable, '-X', 'utf8', '-I', '-c', script, str(TOOLS)], check=True)

    def test_processor_records_keep_types_and_do_not_mix_sources(self):
        records = results.parse_results([
            'noise', '@@BEGIN\tfirst', 'VAR\tn\t42', 'COUNTER\t3', 'IPT\t60',
            'ACC\t0.5', 'BLOCK\tworld-processor', 'RAN\ttrue', 'TEXT\t你好\\nworld',
            '@@END', 'SKIP\tunsupported', '@@BEGIN\tsecond', 'VAR\tx\tvalue\twith-tab', '@@END',
        ])
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]['vars'], {'n': '42'})
        self.assertEqual(records[0]['ipt'], 60.0)
        self.assertEqual(records[0]['text'], '你好\nworld')
        self.assertEqual(records[0]['processor_block'], 'world-processor')
        self.assertEqual(records[0]['accumulator'], 0.5)
        self.assertTrue(records[0]['executed'])
        self.assertEqual(records[0]['skipped'], ['unsupported'])
        self.assertEqual(records[1]['vars'], {'x': 'value\twith-tab'})
        self.assertIsNone(records[1]['ipt'])

    def test_pad_numeric_fields_and_partial_rows(self):
        pads = results.parse_pads(['noise', 'PAD\tpad1\t3\t4\tcopper\tnull\tbad\t5',
                                   'PAD\tpad2\t7'])
        self.assertEqual(pads[0]['x'], 3.0)
        self.assertEqual(pads[0]['config'], 'copper')
        self.assertIsNone(pads[0]['cooldown'])
        self.assertEqual(pads[0]['items'], 5.0)
        self.assertEqual(pads[1], {'name': 'pad2', 'x': 7.0})

    def test_trace_parse_and_assertion_output(self):
        values = ['flare'] + ['1'] * (len(results.TRACE_COLUMNS) - 1)
        rows = results.parse_trace(['TRACE\tshort', 'noise', 'TRACE\t' + '\t'.join(values)])
        self.assertEqual(rows, [values])
        output = io.StringIO()
        self.assertEqual(results.check_asserts(rows, ['dist <= range'], output=output), 0)
        self.assertIn('ASSERT PASS', output.getvalue())
        output = io.StringIO()
        self.assertEqual(results.check_asserts(rows, ['unknown_value > 0'], output=output), 1)
        self.assertIn('ASSERT FAILED', output.getvalue())

    def test_tick_builders_keep_native_power_update_order(self):
        self.assertIn('unitTick(); worldTick();', scripts._world_tick_js(None, 'logic'))
        self.assertIn('worldTick(); unitTick();', scripts._world_tick_js(1.0, 'logic'))
        stepped = scripts._loop_js('b', 3, ticks=False)
        self.assertIn('executor.runOnce()', stepped)
        self.assertNotIn('Vars.state.tick++', stepped)
        scene = scripts._scene_loop_js(3, ticks=True, update='all', power=None)
        self.assertIn('procs[j].updateTile()', scene)
        self.assertIn('finally', scene)
        self.assertEqual(scripts._scene_chunks([1, 2, 3], 2), [[1, 2], [3]])


if __name__ == '__main__':
    unittest.main()
