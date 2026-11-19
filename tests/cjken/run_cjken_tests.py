# -*- coding: utf-8 -*-
"""Tests for `tools/cjken.py` -- the Chinese question -> English names bridge.

The bridge exists because the knowledge base is English while the people
asking it questions write Chinese.  Its failure modes are the boring ones:
a table that stops parsing, a longest-match that lets `处理器` fire inside
`逻辑处理器`, an expansion that silently rewrites the question instead of
appending to it.
"""
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
TOOLS = os.path.join(REPO, "tools")
sys.path.insert(0, TOOLS)

import cjken  # noqa: E402


_KNOWLEDGE = os.path.join(REPO, "knowledge")
if not os.path.isdir(_KNOWLEDGE):
    raise unittest.SkipTest("knowledge/ is not in this checkout"
                            " (it ships in the knowledge package)")

class Table(unittest.TestCase):
    def test_it_reads_the_name_tables_the_repo_keeps(self):
        t = cjken.table(force=True)
        self.assertGreaterEqual(len(t), 400, "the glossary + aliases should yield hundreds of terms")
        self.assertIn("差扰", t, "hand-written jargon row")
        self.assertIn("初代核心", t, "generated name table row")

    def test_every_value_is_ascii_and_deduped(self):
        for zh, forms in cjken.table(force=True).items():
            self.assertTrue(any(ord(c) > 127 for c in zh), zh)
            self.assertTrue(all(ord(c) < 128 for f in forms for c in f), (zh, forms))
            self.assertEqual(len(forms), len({f.lower() for f in forms}), (zh, forms))

    def test_cli_reports_the_size(self):
        cp = subprocess.run([sys.executable, "-X", "utf8",
                             os.path.join(TOOLS, "cjken.py")],
                            capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(cp.returncode, 0)
        self.assertRegex(cp.stdout, r"\d{3,} Chinese terms")

class Matching(unittest.TestCase):
    def test_longest_match_wins_and_matches_do_not_overlap(self):
        hit = cjken.matches("逻辑处理器的指令预算")
        terms = [h[0] for h in hit]
        self.assertTrue(any(t.startswith("逻辑处") for t in terms), terms)
        for t in terms:
            for other in terms:
                self.assertFalse(t != other and t in other, (t, other))
        self.assertEqual(len(terms), len(set(terms)))
        for i in range(len(terms) - 1):
            self.assertLess("逻辑处理器的指令预算".find(terms[i]),
                            "逻辑处理器的指令预算".find(terms[i + 1]),
                            "matches come back in reading order")

    def test_english_query_yields_no_chinese_matches(self):
        self.assertEqual(cjken.matches("what is the instruction pool"), [])

    def test_a_name_maps_to_both_spellings(self):
        _, hit = cjken.expand("初代核心怎么用")
        forms = [f for _, fs in hit for f in fs]
        self.assertTrue(any("-" in f for f in forms), forms)
        self.assertTrue(any(" " in f for f in forms), forms)

class Expansion(unittest.TestCase):
    def test_it_appends_and_never_rewrites(self):
        q = "差扰是什么"
        out, hit = cjken.expand(q)
        self.assertTrue(out.startswith(q), out)
        self.assertTrue(hit)
        self.assertIn("parallax", out)

    def test_it_does_not_repeat_a_word_already_in_the_query(self):
        out, _ = cjken.expand("parallax 差扰")
        self.assertEqual(out.lower().count("parallax"), 1, out)

    def test_the_escape_hatch_disables_it(self):
        os.environ["MLOG_NO_EXPAND"] = "1"
        try:
            out, hit = cjken.expand("差扰是什么")
            self.assertEqual((out, hit), ("差扰是什么", []))
        finally:
            del os.environ["MLOG_NO_EXPAND"]

    def test_a_query_without_names_is_returned_untouched(self):
        out, hit = cjken.expand("把 @counter set 成某个行号会发生什么")
        self.assertEqual(hit, [])
        self.assertEqual(out, "把 @counter set 成某个行号会发生什么")

if __name__ == "__main__":
    unittest.main(verbosity=2)
