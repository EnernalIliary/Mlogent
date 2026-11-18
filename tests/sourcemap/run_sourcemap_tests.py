"""Tests for tools/sourcemap.py -- the inferred .mnd -> mlog map.

Half of these are pure structure (statement splitting, mlog normalisation) and
run anywhere.  The attribution half needs a compiler, so it exits 3 (SKIP, the
gate's convention) when no jar is resolvable.
"""
import io
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import sourcemap as S                                     # noqa: E402


def _ready():
    try:
        import mindcode as M
    except Exception:                                      # noqa: BLE001
        return False
    return bool(M.locate().get("ok"))


class Structure(unittest.TestCase):
    def test_comments_and_blanks_are_not_statements(self):
        src = "a = 1; // note\n\n   \nb = 2;\n"
        got = S._lines(src)
        self.assertEqual([g["text"] for g in got], ["a = 1;", "b = 2;"])
        self.assertEqual([g["line"] for g in got], [1, 4])

    def test_block_depth(self):
        src = "s = 0;\nfor i in 0 .. 3 do\n    s += i;\nend;\nx = 1;\n"
        got = S._lines(src)
        self.assertEqual([g["depth"] for g in got], [0, 0, 1, 0, 0])

    def test_nested_block_depth(self):
        src = ("a = 0;\nwhile a < 3 do\n    if a == 1 do\n        b = 1;\n"
               "    end;\n    a += 1;\nend;\n")
        depths = [g["depth"] for g in S._lines(src)]
        self.assertEqual(depths[0], 0)          # a = 0;
        self.assertEqual(depths[1], 0)          # while ...
        self.assertEqual(depths[2], 1)          #   if ...
        self.assertEqual(depths[3], 2)          #     b = 1;
        self.assertEqual(depths[4], 1)          #   end;   (closes the if)

    def test_mlog_lines_drop_blanks(self):
        self.assertEqual(S._mlog_lines("a\n\n  b  \n"), ["a", "b"])
        self.assertEqual(S._mlog_lines(None), [])

    def test_show_on_empty_map_says_so(self):
        got = S.show({"map": []}, 3)
        self.assertIsNone(got["mnd_line"])
        self.assertIn("not attributed", got["why"])


@unittest.skipUnless(_ready(), "no mindcode jar/java on this checkout")
class Attribution(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="mlog-sm-")

    def _write(self, src):
        p = os.path.join(self.tmp, "t.mnd")
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(src)
        return p

    def test_straight_line_program_maps_its_output(self):
        p = self._write('a = 1;\nb = a + 2;\nprint($"b={b}");\n')
        res = S.build(p, optimize=False)
        self.assertTrue(res["ok"], res)
        mapped = [m for m in res["map"] if m["mlog"] is not None]
        self.assertTrue(mapped, res["map"])
        self.assertTrue(all(m["why"] == "prefix alignment" for m in mapped))
        self.assertIn(mapped[0]["mnd_line"], (1, 2, 3))

    def test_loop_body_is_reported_unmapped_not_guessed(self):
        p = self._write("s = 0;\nfor i in 0 .. 3 do\n    s += i;\nend;\n")
        res = S.build(p, optimize=False)
        self.assertTrue(res["ok"], res)
        inside = [m for m in res["map"] if m["mnd_line"] == 3]
        self.assertTrue(inside)
        self.assertTrue(all(m["mlog"] is None for m in inside))
        self.assertEqual(inside[0]["why"], "inside control flow")

    def test_build_from_text_matches_build(self):
        src = 'a = 1;\nprint($"a={a}");\n'
        p = self._write(src)
        from_file = S.build(p, optimize=False)
        from_text = S.build_from_text(src, optimize=False)
        self.assertTrue(from_text["ok"], from_text)
        self.assertEqual(len(from_file["map"]), len(from_text["map"]))

    def test_map_from_text_uses_a_repo_local_temp_dir(self):
        # Mindcode 写不了 %TEMP%（"Error writing file C:\\Users\\...\\Temp\\..."），
        # 所以 build_from_text 自己起临时目录、用完就删；这条守的是「不留下东西」。
        before = set(os.listdir(tempfile.gettempdir()))
        res = S.build_from_text('print("x");\n')
        self.assertTrue(res["ok"], res)
        after = set(os.listdir(tempfile.gettempdir()))
        self.assertEqual(before, after)

    def test_the_map_can_be_read_backwards(self):
        # Reading a trace asks the opposite question: "my line 2 misbehaves,
        # which instructions are mine?"  by_source is that index, built once.
        p = self._write('a = 1;\nb = a + 2;\nprint($"b={b}");\n')
        res = S.build(p, optimize=False)
        self.assertTrue(res["ok"], res)
        by_source = res["by_source"]
        self.assertTrue(by_source)
        for key, lines in by_source.items():
            self.assertEqual(lines, sorted(lines), key)
            for ln in lines:
                self.assertEqual(S.show(res, ln)["mnd_line"], int(key))
        total = sum(len(v) for v in by_source.values())
        self.assertEqual(total, sum(1 for m in res["map"] if m["mlog"] is not None))

    def test_show_source_names_the_lines_and_says_why_when_there_are_none(self):
        p = self._write('a = 1;\nb = a + 2;\n')
        res = S.build(p, optimize=False)
        got = S.show_source(res, 2)
        self.assertTrue(got["mapped"], got)
        self.assertEqual(got["text"].strip(), "b = a + 2;")
        self.assertEqual(got["mlog_lines"], sorted(got["mlog_lines"]))
        blank = S.show_source(res, 99)
        self.assertFalse(blank["mapped"])
        self.assertTrue(blank["why"])

    def test_a_loop_body_answers_unmapped_in_both_directions(self):
        src = 'i = 0;\nfor n in 1..3 do\n    i = i + n;\nend;\nprint($"i={i}");\n'
        p = self._write(src)
        res = S.build(p, optimize=False)
        self.assertTrue(res["ok"], res)
        inside = [m for m in res["map"] if (m.get("why") or "").startswith("inside control flow")]
        if not inside:
            self.skipTest("this compiler version attributed the loop body")
        line = inside[0]["mnd_line"]
        got = S.show_source(res, line)
        self.assertFalse(got["mapped"], got)
        self.assertIn("control flow", got["why"] or "")

    def test_compile_error_comes_back_as_diagnostics(self):
        p = self._write("a = ;\n")
        res = S.build(p)
        self.assertFalse(res["ok"])
        self.assertTrue(res["diagnostics"])



class Incremental(unittest.TestCase):
    """The prefix memo (`math` does not cache; this does, because the answer is
    a pure function of the text before it).

    A build compiles one prefix per statement in each direction, so a 40-line
    program starts ~80 compilers without it.  These cases count *real* compiler
    invocations -- timing them would measure the machine, not the memo.
    """

    def setUp(self):
        import mindcode as M
        self.M = M
        self.real = M.compile_source
        self.calls = 0

        def spy(*a, **kw):
            self.calls += 1
            return self.real(*a, **kw)

        M.compile_source = spy
        self.dir = tempfile.mkdtemp(prefix="sminc-")

    def tearDown(self):
        self.M.compile_source = self.real
        shutil.rmtree(self.dir, ignore_errors=True)

    def _write(self, text, name="inc.mnd"):
        p = os.path.join(self.dir, name)
        io.open(p, "w", encoding="utf-8", newline="\n").write(text)
        return p

    def test_second_build_of_an_unchanged_source_uses_no_compiler(self):
        p = self._write("a = 3;\nb = a + 4;\nprint(b);\n")
        first = S.build(p)
        self.assertTrue(first["ok"], first)
        self.calls = 0
        again = S.build(p)
        self.assertTrue(again["ok"], again)
        self.assertEqual(again["map"], first["map"])
        self.assertEqual(self.calls, 0, "an unchanged source re-ran the compiler")

    def test_appending_a_statement_recompiles_only_the_tail(self):
        body = ("a = 3;\nb = a + 4;\nc = b * 2;\nd = c - 1;\ne = d + 5;\n"
                "f = e * 2;\nprint(f);\n")
        p = self._write(body)
        self.assertTrue(S.build(p)["ok"])
        self._write(body + "g = f + 1;\nprint(g);\n")
        self.calls = 0
        res = S.build(p)
        self.assertTrue(res["ok"], res)
        # One prefix for the new statement, one for the whole source.  Anything
        # near len(_lines(body)) means the memo is not being consulted.
        self.assertLessEqual(self.calls, 3, "recompiled the prefix it already had")

    def test_a_compile_failure_is_not_memoised(self):
        p = self._write("a = ;\n")
        self.assertFalse(S.build(p)["ok"])
        self.calls = 0
        self.assertFalse(S.build(p)["ok"])
        self.assertGreaterEqual(self.calls, 1, "a failure was replayed from the memo")

    def test_the_memo_can_be_turned_off(self):
        p = self._write("a = 1;\nb = a + 1;\nprint(b);\n")
        old = os.environ.get("MLOG_CACHE")
        os.environ["MLOG_CACHE"] = "0"
        try:
            self.assertTrue(S.build(p)["ok"])
            self.calls = 0
            self.assertTrue(S.build(p)["ok"])
            self.assertGreaterEqual(self.calls, 1, "MLOG_CACHE=0 did not disable the memo")
        finally:
            if old is None:
                os.environ.pop("MLOG_CACHE", None)
            else:
                os.environ["MLOG_CACHE"] = old


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--exit-if-no-jar" and not _ready():
        raise SystemExit(3)
    unittest.main(verbosity=2)
