"""Glossary and English index must stay in step with the files they describe.

Two generated pages, one test:

* `knowledge/GLOSSARY.md` -- the three-layer name table. Regenerated from
  `data/game/bundles/*.properties` + `data/game/aliases.json`, so a stale table
  means names drifted from the game.
* `knowledge/INDEX.en.md` -- English titles for every article, from
  `knowledge/00-data/en_titles.json`. An article without an English title is
  invisible to an English-only reader, which is the whole point of the index, so
  that is a failure and not a warning.
"""
from __future__ import annotations

import io
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
KBT = os.path.join(ROOT, "knowledge", "tools")


def run(script, *args):
    proc = subprocess.run([sys.executable, "-X", "utf8", os.path.join(KBT, script)] + list(args),
                          cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def read(path):
    return io.open(os.path.join(ROOT, path), encoding="utf-8", newline="").read()


class Glossary(unittest.TestCase):
    def test_generated_region_is_current(self):
        code, out = run("gen_glossary.py")
        self.assertEqual(code, 0, out.strip())

    def test_the_row_that_started_it_all(self):
        """parallax is 差扰 -- the official name, not a translation of the beam."""
        page = read("knowledge/GLOSSARY.md")
        self.assertRegex(page, r"\|\s*`parallax`\s*\|\s*Parallax\s*\|\s*差扰\s*\|")

    def test_legacy_names_survive_as_search_aliases(self):
        page = read("knowledge/GLOSSARY.md")
        for ident, official, legacy in (("flare", "星辉", "耀斑"),
                                        ("core-shard", "初代核心", "碎片核心"),
                                        ("metaglass", "钢化玻璃", "金属玻璃")):
            row = re.search(r"\| `%s` \|[^|]*\| ([^|]*) \| ([^|]*) \|" % re.escape(ident), page)
            self.assertIsNotNone(row, ident)
            self.assertEqual(row.group(1).strip(), official)
            self.assertIn(legacy, row.group(2))

    def test_every_entity_in_aliases_is_named(self):
        import json
        aliases = json.loads(read("data/game/aliases.json"))
        page = read("knowledge/GLOSSARY.md")
        missing = [ident for table in aliases.values() for ident in table
                   if "| `%s` |" % ident not in page]
        self.assertEqual(missing, [], "entities missing from GLOSSARY.md")

    def test_hand_written_half_is_not_regenerated(self):
        """The concept table must survive a rewrite -- it is not generated."""
        page = read("knowledge/GLOSSARY.md")
        self.assertIn("逻辑与工具链（手写）", page)
        self.assertIn("累积池", page)


class IndexEn(unittest.TestCase):
    def test_index_is_current(self):
        code, out = run("gen_index_en.py")
        self.assertEqual(code, 0, out.strip())

    def test_every_article_has_an_english_title(self):
        import json
        titles = json.loads(read("knowledge/00-data/en_titles.json"))
        missing = [t for t in titles.values()
                   if not t.get("en_title") or not t.get("en_summary")]
        self.assertEqual(missing, [])
        page = read("knowledge/INDEX.en.md")
        self.assertNotIn("missing — add it to", page)

    def test_no_chinese_leaks_into_the_english_half(self):
        import json
        titles = json.loads(read("knowledge/00-data/en_titles.json"))
        bad = [k for k, v in titles.items()
               if re.search(r"[\u4e00-\u9fff]", v.get("en_title", "") + v.get("en_summary", ""))]
        self.assertEqual(bad, [])

    def test_index_links_resolve(self):
        page = read("knowledge/INDEX.en.md")
        links = re.findall(r"\]\((0[1-8]-[^)]+\.md)\)", page)
        self.assertTrue(links)
        for rel in links:
            self.assertTrue(os.path.isfile(os.path.join(ROOT, "knowledge", rel)), rel)


if __name__ == "__main__":
    unittest.main(verbosity=2)
