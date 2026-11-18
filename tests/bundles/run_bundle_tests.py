"""Tests for the two name generators and the bundles they now read from the repo.

The pair used to resolve its only input from a sibling assets checkout
(`../TextureMDT`), so neither generator could run in CI and neither had a test:
the committed output was checked by hand or not at all.  The two files they
need (174 KB + 165 KB) are vendored under `data/game/bundles/`, which makes a
clean checkout sufficient -- and makes `--check` meaningful, because it now
compares against what is committed instead of merely skipping the write.

Run directly:  python tests/bundles/run_bundle_tests.py
"""

import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))

BUNDLES = os.path.join(ROOT, "data", "game", "bundles")
EN = os.path.join(BUNDLES, "bundle.properties")
ZH = os.path.join(BUNDLES, "bundle_zh_CN.properties")

NAME_DOCS = os.path.join(ROOT, "knowledge", "tools", "gen_name_docs.py")
ALIASES = os.path.join(ROOT, "knowledge", "tools", "gen_game_aliases.py")


def run(script, *args, bundles=None):
    env = dict(os.environ)
    env.pop("MLOG_ASSETS", None)
    if bundles is not None:
        env["MLOG_BUNDLES"] = bundles
    p = subprocess.run([sys.executable, "-X", "utf8", script] + list(args),
                       cwd=ROOT, env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def read_text(path, encoding="utf-8"):
    with io.open(path, encoding=encoding, errors="replace") as fh:
        return fh.read()


def read_bytes(path):
    with io.open(path, "rb") as fh:
        return fh.read()


def write_text(path, text):
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def keys_of(path):
    out = {}
    for raw in read_text(path, "utf-8-sig").splitlines():
        if not raw or raw.lstrip().startswith("#") or "=" not in raw:
            continue
        k, v = raw.split("=", 1)
        out[k.strip()] = v.strip()
    return out


class Vendored(unittest.TestCase):
    def test_both_files_are_in_the_repo(self):
        for path in (EN, ZH):
            self.assertTrue(os.path.isfile(path), path)
            self.assertGreater(os.path.getsize(path), 100 * 1024, path)

    def test_en_and_zh_cover_the_same_keys(self):
        en, zh = keys_of(EN), keys_of(ZH)
        self.assertGreater(len(en), 2700)
        self.assertEqual(sorted(en), sorted(zh))

    def test_the_name_sources_are_the_ones_the_docs_cite(self):
        # Every generated doc cites "zh:N" / "en:N" -- line N of these files.
        # A re-wrapped or re-saved bundle would silently shift all of them.
        for path in (EN, ZH):
            data = read_bytes(path)
            self.assertNotIn(b"\r\n", data, "%s must keep LF: zh:N cites line N" % path)
            self.assertFalse(data.startswith(b"\xef\xbb\xbf"), "%s has a BOM" % path)


class Resolves(unittest.TestCase):
    def test_repo_copy_wins_over_the_sibling_assets_tree(self):
        # MLOG_BUNDLES points nowhere: resolution must fall through to the
        # repo copy rather than to ../TextureMDT, which a clean checkout lacks.
        for script in (NAME_DOCS, ALIASES):
            code, out = run(script, "--check", bundles=os.path.join(ROOT, "out", "no-such-bundles"))
            self.assertEqual(code, 0, out)

    def test_both_generators_agree_with_the_committed_output(self):
        for script in (NAME_DOCS, ALIASES):
            code, out = run(script, "--check")
            self.assertEqual(code, 0, "%s drifted:\n%s" % (os.path.basename(script), out))


class Drift(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="bundles-")
        for name in ("bundle.properties", "bundle_zh_CN.properties"):
            shutil.copyfile(os.path.join(BUNDLES, name), os.path.join(self.tmp, name))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _rename(self, old, new):
        path = os.path.join(self.tmp, "bundle_zh_CN.properties")
        text = read_text(path)
        self.assertIn(old, text)
        write_text(path, text.replace(old, new, 1))

    def test_a_renamed_block_is_reported(self):
        self._rename("block.conveyor.name = ", "block.conveyor.name = 旧式")
        for script in (NAME_DOCS, ALIASES):
            code, out = run(script, "--check", bundles=self.tmp)
            self.assertEqual(code, 1, "%s accepted a changed name:\n%s"
                             % (os.path.basename(script), out))

    def _drop(self, key):
        path = os.path.join(self.tmp, "bundle_zh_CN.properties")
        text = read_text(path)
        self.assertIn(key, text)
        write_text(path, text.replace(key, "# gone", 1))

    def test_a_dropped_name_is_caught_by_the_docs_generator(self):
        # The docs list one row per id with the in-game name in a cell, so a
        # lost key shows up as a changed cell (and a lower 覆盖 count).
        self._drop("block.conveyor.name")
        code, out = run(NAME_DOCS, "--check", bundles=self.tmp)
        self.assertEqual(code, 1, out)
        self.assertIn("与磁盘不一致", out)

    def test_aliases_report_a_drop_the_coverage_line_but_not_as_drift(self):
        # A known blind spot, encoded here instead of assumed away: conveyor's
        # old hand-written alias is also 传送带, so dropping the official key
        # leaves the JSON byte-identical.  The coverage line is the only
        # signal -- which is why gen_name_docs (above) carries the real check.
        self._drop("block.conveyor.name")
        code, out = run(ALIASES, "--check", bundles=self.tmp)
        self.assertEqual(code, 0, out)
        self.assertIn("no official name 47", out)

    def test_check_never_writes(self):
        self._rename("block.conveyor.name = ", "block.conveyor.name = 旧式")
        ledger = os.path.join(ROOT, "data", "game", "aliases.json")
        before = read_bytes(ledger)
        run(ALIASES, "--check", bundles=self.tmp)
        after = read_bytes(ledger)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main(verbosity=1)
