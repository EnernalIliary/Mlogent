"""Event stream contracts without installing hooks in a game."""
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from world_events import read_events

class EventTests(unittest.TestCase):
    def read(self,op,lines):
        return read_events(SimpleNamespace(js=Mock(return_value=lines)),{'op':op})

    def test_chat_preserves_tabs_and_sequence(self):
        r=self.read('messages',['1.0\t2.0\tplayer\thello\tworld','SEQ\t3.0'])
        self.assertEqual(r['rows'][0]['message'],'hello\tworld')
        self.assertEqual(r['nextSeq'],3)

    def test_push_json_and_raw_fallback(self):
        r=self.read('agent_push',['{"job":1}','not json','SEQ\t4.0'])
        self.assertEqual(r['rows'],[{'job':1},{'raw':'not json'}])
        self.assertEqual(r['nextSeq'],4)

    def test_multitile_covered_removal_is_filtered(self):
        r=self.read('changes',['P\t1\t10\t2\t3\tcore\tsharded\tsize=2',
                               'B\t2\t10\t3\t3\tair\tsharded\t',
                               'B\t3\t10\t9\t9\tair\tsharded\t','SEQ\t3'])
        self.assertEqual([(x['x'],x['y']) for x in r['rows']],[(2,3),(9,9)])

    def test_missing_hooks_are_explicit(self):
        for op in ['chat','push','changes']:
            self.assertFalse(self.read(op,['NOSETUP'])['ok'])

if __name__=='__main__':
    unittest.main()
