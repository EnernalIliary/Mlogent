"""Read-only query response contracts, without a JVM."""
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from world_queries import query

class QueryTests(unittest.TestCase):
    def world(self, lines):
        return SimpleNamespace(js=Mock(return_value=lines), started=0, game_port=6567)

    def test_status_numbers_flags_and_explicit_directory(self):
        w=self.world(['wave=3.0', 'paused=1.0', 'infinite=0', 'units=bad', 'w=64'])
        r=query(w, {'op':'status'}, data_dir='isolated')
        self.assertEqual((r['wave'],r['width'],r['units']), (3,64,0))
        self.assertTrue(r['paused']); self.assertFalse(r['infiniteResources'])
        self.assertEqual(r['dataDir'], 'isolated')

    def test_maps_and_player_truncation(self):
        r=query(self.world(['Fork\tmap.msav']), {'op':'maps'}, data_dir='x')
        self.assertEqual(r['maps'], [{'name':'Fork','file':'map.msav'}])
        r=query(self.world(['Alice\tsharded\t1.5\t2\t1', 'TRUNC']), {'op':'players'}, data_dir='x')
        self.assertTrue(r['truncated']); self.assertEqual(r['rows'][0]['x'], 1.5)

    def test_unit_errors_and_empty_table(self):
        r=query(self.world(['ERR\tno unit']), {'op':'unit','id':2}, data_dir='x')
        self.assertEqual(r, {'ok':False,'error':'no unit'})
        r=query(self.world([]), {'op':'units','format':'table'}, data_dir='x')
        self.assertEqual(r['table'], '(no units)')

    def test_writes_are_not_handled(self):
        w=self.world([])
        self.assertIs(query(w, {'op':'spawn'}, data_dir='x'), NotImplemented)
        w.js.assert_not_called()

    def test_missing_building_and_multitile_origin(self):
        result=query(self.world([]), {'op':'building','x':5,'y':6}, data_dir='x')
        self.assertEqual(result, {'ok':True,'block':None,'x':5,'y':6,'found':False})
        result=query(self.world(['core-shard\tsharded\t4\t5\t100\t0\t1000']), {'op':'building','x':5,'y':6}, data_dir='x')
        self.assertEqual(result['origin'], {'x':4,'y':5})

    def test_logic_code_uses_file_channel_and_counts_lines(self):
        w=self.world(['OK'])
        w.take_file=Mock(return_value='set a 1\nend\n')
        result=query(w, {'op':'logic_code','x':1,'y':2}, data_dir='x')
        self.assertEqual(result['lines'], 2)
        self.assertEqual(result['code'], 'set a 1\nend\n')
        w.take_file.assert_called_once()

    def test_logic_variable_values_are_coerced(self):
        result=query(self.world(['count\t2.0','name\tmono']), {'op':'logic_vars','x':1,'y':2}, data_dir='x')
        self.assertEqual(result['count'], 2)
        self.assertEqual(result['vars'], [{'name':'count','value':2}, {'name':'name','value':'mono'}])

if __name__ == '__main__':
    unittest.main()
