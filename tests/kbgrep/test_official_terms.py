"""Run directly with Python; no extra test dependencies."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import official_terms
from mlogent.mcp import queries


class OfficialTermsTests(unittest.TestCase):
    def test_bundle_is_the_authority(self):
        rows = official_terms.lookup('meltdown foreshadow lancer parallax cyclone ripple')
        names = {r['id']: r['zh_CN'] for r in rows}
        self.assertEqual(names, {'meltdown': '熔毁', 'foreshadow': '厄兆', 'lancer': '蓝瑟',
                                 'parallax': '差扰', 'cyclone': '气旋', 'ripple': '浪涌'})

    def test_alias_is_returned_as_official_name(self):
        self.assertIn({'kind': 'block', 'id': 'parallax', 'zh_CN': '差扰', 'en': 'Parallax'},
                      official_terms.lookup('差劲光束是什么'))

    def test_long_names_do_not_match_embedded_short_names(self):
        rows = official_terms.lookup('强化导管的作用')
        self.assertIn('reinforced-conduit', [r['id'] for r in rows])
        self.assertNotIn('conduit', [r['id'] for r in rows])

    def test_unknown_mod_is_not_translated(self):
        self.assertEqual(official_terms.lookup('dp-made-up-unknown'), [])

    def test_mcp_returns_terms_without_changing_hit_contract(self):
        result = queries.knowledge({'query': 'foreshadow', 'k': 1})
        self.assertEqual(result['count'], len(result['hits']))
        self.assertEqual(result['official_terms'][0]['zh_CN'], '厄兆')
        self.assertEqual(result['terminology_source'], official_terms.SOURCE)

    def test_turret_queries_supply_full_names(self):
        result = queries.knowledge({'query': '炮台排行', 'k': 1})
        ids = {r['id'] for r in result['official_terms']}
        self.assertTrue({'lancer', 'foreshadow', 'meltdown', 'ripple'} <= ids)


if __name__ == '__main__':
    unittest.main()
