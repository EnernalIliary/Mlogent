"""Tests for tools/claims.py -- the evidence pointers behind the claim ledger.

Run directly:  python tests/claims/run_claims_tests.py
"""

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import claims  # noqa: E402


class Pointers(unittest.TestCase):
    def test_id_anchor_parses(self):
        self.assertEqual(claims.parse_ref("docs/断言表.md#L1-01"),
                         ("docs/断言表.md", "L1-01", None))

    def test_line_pointer_parses(self):
        self.assertEqual(claims.parse_ref("docs/断言表.md:19"),
                         ("docs/断言表.md", None, "19"))

    def test_range_pointer_parses(self):
        self.assertEqual(
            claims.parse_ref("Mindustry-Source/core/src/mindustry/logic/LExecutor.java:1111-1159"),
            ("Mindustry-Source/core/src/mindustry/logic/LExecutor.java", None, "1111-1159"))

    def test_bare_id_is_not_a_pointer(self):
        self.assertIsNone(claims.parse_ref("L1-01"))

    def test_anchor_resolves_to_the_row(self):
        lines, problem = claims.resolve("docs/断言表.md#L1-01")
        self.assertIsNone(problem)
        self.assertEqual(len(lines), 1)

    def test_unknown_anchor_is_reported(self):
        _lines, problem = claims.resolve("docs/断言表.md#NOPE-99")
        self.assertIsNotNone(problem)

    def test_missing_file_is_reported(self):
        _lines, problem = claims.resolve("docs/no-such-file.md#L1-01")
        self.assertEqual(problem, "file not found: docs/no-such-file.md")

    def test_external_source_tree_is_not_a_failure(self):
        # Mindustry-Source is not part of this checkout; a pointer into it can
        # only be checked for shape.
        _lines, problem = claims.resolve(
            "Mindustry-Source/core/src/mindustry/logic/LExecutor.java:1111-1159")
        self.assertIsNone(problem)

    def test_split_ids_are_tolerated(self):
        table = [(1, "L2-10a"), (2, "L2-10b")]
        self.assertEqual(claims._match(table, "L2-10"), [1, 2])


class Drift(unittest.TestCase):
    def _ledger(self, tmp, rows):
        path = os.path.join(tmp, "claims.jsonl")
        with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        return path

    def test_a_wrong_row_is_caught(self):
        problems = claims.check([{"id": "L1-02", "src": ["docs/断言表.md#L1-01"]}])
        self.assertEqual(len(problems), 1)
        self.assertIn("L1-01", problems[0][2])

    def test_a_correct_record_passes(self):
        self.assertEqual(claims.check([{"id": "L1-01", "src": ["docs/断言表.md#L1-01"]}]), [])

    def test_fix_rewrites_only_when_the_anchor_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._ledger(tmp, [{"id": "L1-01", "src": ["docs/断言表.md:19"]}])
            rows = claims.load(path)
            rows, changes = claims.fix(rows, write=False)
            self.assertEqual(rows[0]["src"], ["docs/断言表.md#L1-01"])
            self.assertEqual(len(changes), 1)

    def test_fix_keeps_pointers_that_cannot_be_anchored(self):
        rows = [{"id": "L9-99", "src": ["docs/断言表.md:19"]}]
        rows, changes = claims.fix(rows, write=False)
        self.assertEqual(rows[0]["src"], ["docs/断言表.md:19"])
        self.assertIn("kept", changes[0][2])


class Sync(unittest.TestCase):
    def test_the_table_matches_the_ledger(self):
        # docs/断言表.md is a projection of the ledger for the 85 rows it covers;
        # three rows had already drifted before this was checked.
        self.assertEqual(claims.render(), [])


class RealLedger(unittest.TestCase):
    def test_the_ledger_loads(self):
        rows = claims.load()
        self.assertGreaterEqual(len(rows), 80)
        ids = [r["id"] for r in rows]
        self.assertEqual(len(ids), len(set(ids)), "claim ids must be unique")

    def test_every_pointer_resolves(self):
        problems = claims.check()
        self.assertEqual(problems, [], "broken evidence pointers: %r" % (problems[:5],))

    def test_every_claim_has_a_source(self):
        for row in claims.load():
            self.assertTrue(row.get("src"), "%s has no src" % row["id"])

    def test_the_gate_verb_agrees(self):
        out = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "claims.py"), "check"],
                             cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, encoding="utf-8", errors="replace")
        self.assertEqual(out.returncode, 0, out.stdout[-800:])


if __name__ == "__main__":
    unittest.main(verbosity=2)
