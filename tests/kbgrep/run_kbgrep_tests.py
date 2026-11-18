"""Wiring tests for `tools/kb_grep.py` and the `mlog_kb` MCP tool.

Two things are worth pinning here.  First, the retriever must rank the article
that actually answers the question first -- that is the whole value of shipping
it next to a server.  Second, it must not quietly depend on anything the server
package does not contain: no fastembed, no sqlite index, no network.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOLS = os.path.join(ROOT, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import kb_grep  # noqa: E402


class Ranking(unittest.TestCase):
    def test_chinese_name_question_lands_on_the_name_article(self):
        hits = kb_grep.search("core-shard 中文名 初代核心", k=5)
        self.assertTrue(hits)
        paths = [h["path"] for h in hits]
        self.assertTrue(any(p.startswith("knowledge/02-world/W14-") for p in paths),
                        paths)

    def test_link_naming_question_lands_on_the_link_article(self):
        hits = kb_grep.search("链接名 读档 重算 shard1", k=3)
        self.assertTrue(hits)
        self.assertIn("E05", hits[0]["path"], hits[0]["path"])

    def test_syntax_question_lands_on_the_mindcode_article(self):
        hits = kb_grep.search("Mindcode then 内联 def", k=3)
        self.assertTrue(hits)
        self.assertIn("M10", hits[0]["path"], hits[0]["path"])

    def test_a_hit_carries_a_snippet_that_contains_the_query(self):
        hits = kb_grep.search("printflush 清空 文本缓冲", k=1)
        self.assertTrue(hits)
        self.assertIn("printflush", hits[0]["snippet"])

    def test_alphabet_soup_finds_nothing_rather_than_everything(self):
        self.assertEqual(kb_grep.search("zzzzqqqqxxxx", k=3), [])
        self.assertEqual(kb_grep.search("   ", k=3), [])

    def test_docs_are_only_searched_on_request(self):
        knowledge_only = kb_grep.search("差分 保真度", k=8)
        both = kb_grep.search("差分 保真度", k=8, include_docs=True)
        self.assertTrue(all(h["path"].startswith("knowledge/") for h in knowledge_only))
        self.assertTrue(any(h["path"].startswith("docs/") for h in both)
                        or len(both) >= len(knowledge_only))

    def test_results_are_ordered_and_capped(self):
        hits = kb_grep.search("单位 控制 ubind", k=4)
        self.assertLessEqual(len(hits), 4)
        scores = [h["score"] for h in hits]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_edit_invalidates_the_cache(self):
        # The stamp is (count, newest mtime); touching a file must rebuild.
        target = os.path.join(ROOT, "knowledge", "01-execution", "E01-执行模型与预算.md")
        before = kb_grep.search("预算 累积池", k=1)
        stamp_before = kb_grep._stamp(os.path.join(ROOT, "knowledge"), False)
        os.utime(target, None)
        stamp_after = kb_grep._stamp(os.path.join(ROOT, "knowledge"), False)
        after = kb_grep.search("预算 累积池", k=1)
        self.assertNotEqual(stamp_before, stamp_after)
        self.assertEqual([h["path"] for h in before], [h["path"] for h in after])


class NoDependencies(unittest.TestCase):
    def test_the_module_imports_nothing_third_party(self):
        # The docstring is allowed to *name* fastembed (it explains why kb.py is
        # the better retriever but not the shippable one); the imports are not.
        import ast
        tree = ast.parse(open(os.path.join(TOOLS, "kb_grep.py"),
                              encoding="utf-8").read())
        used = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                used.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                used.add(node.module.split(".")[0])
        banned = {"fastembed", "onnxruntime", "numpy", "requests", "sqlite3",
                  "yaml", "httpx"}
        self.assertEqual(used & banned, set(), "kb_grep must stay dependency-free")
        self.assertLessEqual(used, {"os", "re", "sys", "json", "__future__",
                                    "collections", "math", "typing"},
                             "unexpected import: %s" % sorted(used))

    def test_the_cli_answers_without_a_built_index(self):
        cp = subprocess.run([sys.executable, "-X", "utf8",
                             os.path.join(TOOLS, "kb_grep.py"), "search",
                             "链接名 读档", "-k", "2", "--json"],
                            capture_output=True, text=True, encoding="utf-8",
                            timeout=300)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        hits = json.loads(cp.stdout)
        self.assertTrue(hits)
        self.assertIn("path", hits[0])


class McpSurface(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import mlog_mcp
        cls.mcp = mlog_mcp

    def test_the_tool_is_listed_and_handled(self):
        names = [t["name"] for t in self.mcp.TOOLS]
        self.assertIn("mlog_kb", names)
        self.assertIn("mlog_kb", self.mcp.HANDLERS)

    def test_descriptions_are_english(self):
        spec = next(t for t in self.mcp.TOOLS if t["name"] == "mlog_kb")
        self.assertFalse(any("\u4e00" <= ch <= "\u9fff" for ch in spec["description"]))

    def test_it_answers_a_question(self):
        out = self.mcp.HANDLERS["mlog_kb"]({"query": "链接名 读档", "k": 3})
        self.assertEqual(out["mode"], "keyword")
        self.assertTrue(out["count"] >= 1)
        self.assertIn("hits", out)

    def test_a_missing_query_is_an_error_not_an_empty_answer(self):
        with self.assertRaises(ValueError):
            self.mcp.HANDLERS["mlog_kb"]({})

    def test_doctor_says_whether_the_knowledge_base_is_here(self):
        doc = self.mcp.HANDLERS["mlog_doctor"]({})
        self.assertIn("knowledge", doc)
        self.assertTrue(doc["knowledge"]["present"])
        self.assertGreater(doc["knowledge"]["sections"], 100)


if __name__ == "__main__":
    unittest.main(verbosity=2)
