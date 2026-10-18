"""Build a clean, publishable export of the mlog toolkit under dist/mlog-toolkit.

The working repo cannot be pushed as-is: it tracks 334.8 MB, and two files exceed
GitHub's hard 100 MB per-file limit (`logic-corpus/blocks.json` = 144 MB,
`logic-corpus/by-blueprint/Linux on mlogv32.md` = 103 MB). It also carries the
user's own blueprint corpus, extracted game assets and private mod sources.

So the public artifact is a *subset*: the toolchain, its docs, and the tests.
This script copies that subset, scrubs absolute personal paths, writes
README/LICENSE/NOTICE, and initialises a fresh git repo with one commit.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist" / "mlog-toolkit"
BP = ROOT / "mindustry-blueprint"
AGENT = ROOT / ".dsh" / "skills" / "mlogagent"
TESTS = ROOT / "tests"

README = """# mlog-toolkit

Static analysis, decoding and generation for **Mindustry** blueprint logic (`.msch` / `mlog`) —
plus the data tables you need to write mlog without guessing.

No game install, no simulator, no third-party packages. Pure Python 3.10+.

```
$ python mlogagent/tools/mlogagent.py report your.msch

=== your.msch [micro-processor @(0,0)]
--- check -------------------------------------------------
no issues found
--- ir ----------------------------------------------------
34 statements, 27 read / 15 written
--- values -------------------------------------------------
3 rounds, stable
--- pack --------------------------------------------------
no packed-config idiom found
VERDICT   check 0E/0W | dead-code 0 | dead-store 0 | branches 0 | nulls 0 | packs 0
```

## What it does

Six analyses, each answering a question the others cannot:

| Command | Question it answers | Evidence |
|---|---|---|
| `check` | Does this program contain a statement that cannot work? | strongest — a hit is usually a real defect |
| `check --cost` | How long is one cycle, and how much of it is `wait`? | exact instruction count per tick budget |
| `ir` | Is any code unreachable, or any value computed and dropped? | CFG + liveness fixpoint |
| `values` | Which branches are constant? Which variables are provably `null`? | abstract interpretation |
| `pack` | Is the config bit-packing wide enough for every item id? | field layout + capacity |
| `cross` | Do cross-processor `read`/`write` slots exist on the other side? | per-blueprint link resolution |

Plus the writing side:

| Command | Purpose |
|---|---|
| `explain <mnemonic>` | which parameter is the output, which is a fixed token — from the source, not the docs |
| `unit` / `block` / `item` | unit attributes, block recipes & capacities, item ids |
| `find <words>` | find a blueprint in your own library that already solves this job |
| `gen` | turn mlog into a paste-ready blueprint code |
| `text` | print every message-board text in a blueprint |
| `parse` | blueprint → block table + logic source |

## Install

```bash
git clone <this repo> && cd mlog-toolkit
python mlogagent/tools/mlogagent.py info    # sanity check; no config needed
```

Two entry points, same code:

- **`mlogagent/tools/mlogagent.py`** — one command, all analyses, verdict first (self-contained).
- **`mindustry-blueprint/tools/mlog.py`** — one subcommand per analysis, scripting friendly.

## Environment

- **Python 3.10+**, standard library only.
- **Blueprint folder** (only for `selftest` and `find`): defaults to
  `%APPDATA%\\Mindustry\\schematics`; override with `MLOG_CORPUS` or `--corpus`.
  Everything else works on files you pass in.
- **Mindustry source checkout** (only for regenerating the data tables):
  clone `Anuken/Mindustry` next to this repo as `Mindustry-Source/`.
  Day-to-day use needs none of it — all eight tables ship in `tools/`.
- Console must be UTF-8 (`chcp 65001` on Windows), or Chinese identifiers render as mojibake.

## Calibration — read this before believing a report

Measured over 617 blueprints / 2409 processors of real community logic:

- `ir` dead stores: **82.0 % of processors report nothing**; p50 = 0, p90 = 1 per block.
- `values`: 4.1 % of blocks have a constant branch; 39 ms/block.
- `pack`: **3 of 2420 blocks** use the bit-packing idiom.

So `ir` is a linter, `pack` is a "speaks only when it sees something" check, and neither
proves correctness. What the tools **cannot** do:

- judge whether a computed value is *right* (a distance computed with `op add` instead of
  `op len` is invisible — the value is used, just wrong);
- see across processors except where `cross` resolves a declared slot;
- see anything a simulation would: external inputs are modelled as unknown.

## Tests

```bash
python tests/run_tests.py          # 13 golden digests
python tests/run_tests.py --write  # after an intentional behaviour change — then read the diff
python mindustry-blueprint/tools/mlog.py selftest   # parser round-trip against your own library
```

## Documentation

- [`mindustry-blueprint/SKILL.md`](mindustry-blueprint/SKILL.md) — operating manual, traps, cost model
- [`mindustry-blueprint/REFERENCE.md`](mindustry-blueprint/REFERENCE.md) — the knowledge base: mechanics, instruction budget, refuted conclusions
- [`mindustry-blueprint/PATTERNS.md`](mindustry-blueprint/PATTERNS.md) — logic patterns found in real blueprints
- [`mindustry-blueprint/BUILDS.md`](mindustry-blueprint/BUILDS.md) — which build introduced which statement
- `mlogagent/SKILL.md` — the standalone agent skill (self-contained copy with `MANIFEST.sha256`)

Docs are written in Chinese; the code and comments are English.

## Data provenance

All tables were derived from **Mindustry v159.3** (`Anuken/Mindustry` @ `5811844`) by the
scripts in `tools/*_from_source.py`, not hand-typed. To refresh after a game update, put a
fresh checkout at `Mindustry-Source/` and re-run them.

Mindustry is licensed GPLv3. This project contains no game code: it ships derived facts
(block ids, sizes, recipes, unit attributes), short quotations for citation, and its own
implementation. See `NOTICE`.
"""

NOTICE = """mlog-toolkit
============

This project analyses and generates blueprints for Mindustry.

Mindustry is Copyright (c) Anuken and contributors, licensed under the GNU General
Public License v3. https://github.com/Anuken/Mindustry

No Mindustry source code is included. What is included:

* Data tables derived from Mindustry v159.3 source by mechanical extraction
  (`tools/*_from_source.py`): block content ids and sizes, item ids, recipes and
  capacities, unit attributes, per-instruction read/write slots.
  These are factual observations of the game's behaviour.
* Short quotations of Java source lines inside documentation and `explain` output,
  for citation only (each carries a `File.java:line` reference).
* Original implementations of: blueprint (.msch) reader/writer, mlog tokenizer and
  parser, control-flow and liveness analysis, abstract-value analysis, packing
  analysis, cross-processor slot resolution.

If you redistribute this project together with Mindustry itself, the GPLv3 of
Mindustry applies to Mindustry, not to this project.
"""

GITIGNORE = """__pycache__/
*.pyc
.find_cache.json
dist/
"""

LICENSE = """MIT License

Copyright (c) {year} {who}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# absolute personal paths -> portable placeholders.
# replacements go through callables: a literal `\\` in re.sub's template is an escape.
SCRUBS = [
    (re.compile(r"[A-Za-z]:[\\/]Users[\\/]lliary[\\/]AppData[\\/]Roaming[\\/]Mindustry[\\/]schematics"),
     lambda m: r"%APPDATA%\Mindustry\schematics"),
    (re.compile(r"[A-Za-z]:[\\/]Users[\\/]lliary[\\/]AppData[\\/]Roaming[\\/]Mindustry[\\/]schematics"),
     lambda m: r"%APPDATA%\Mindustry\schematics"),
    (re.compile(r"[A-Za-z]:[\\/]Users[\\/]lliary"), lambda m: "~"),
    (re.compile(r"[A-Za-z]:[\\/]OneDrive[\\/][^\s`'\")\]]*?AtomicStates[\\/]?"), lambda m: ""),
    (re.compile(r"F:/OneDrive/[^/\s`'\"]*/AtomicStates"), lambda m: "<repo>"),
]


def copy_tree(src: Path, dst: Path) -> int:
    n = 0
    for f in sorted(src.rglob("*")):
        if not f.is_file():
            continue
        if "__pycache__" in f.parts or f.name.endswith(".pyc"):
            continue
        if f.name == ".find_cache.json":
            continue
        target = dst / f.relative_to(src)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)
        n += 1
    return n


def scrub(root: Path) -> int:
    changed = 0
    for f in root.rglob("*"):
        if not f.is_file() or f.suffix.lower() not in {".md", ".py", ".json", ".txt"}:
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        new = text
        for pat, rep in SCRUBS:
            new = pat.sub(rep, new)
        if new != text:
            f.write_text(new, encoding="utf-8")
            changed += 1
    return changed


def main() -> int:
    if DIST.exists():
        # OneDrive can hold a lock on __pycache__; it is gitignored anyway
        shutil.rmtree(DIST, ignore_errors=True)
        for junk in DIST.rglob("__pycache__"):
            shutil.rmtree(junk, ignore_errors=True)
    DIST.mkdir(parents=True, exist_ok=True)

    n_bp = copy_tree(BP, DIST / "mindustry-blueprint")
    n_ag = copy_tree(AGENT, DIST / "mlogagent")
    n_ts = copy_tree(TESTS, DIST / "tests")
    print(f"copied: blueprint {n_bp}, mlogagent {n_ag}, tests {n_ts}")

    changed = scrub(DIST)
    print(f"scrubbed absolute paths in {changed} file(s)")

    (DIST / "README.md").write_text(README, encoding="utf-8")
    (DIST / "NOTICE").write_text(NOTICE, encoding="utf-8")
    (DIST / ".gitignore").write_text(GITIGNORE, encoding="utf-8")
    (DIST / "LICENSE").write_text(LICENSE.format(year=2026, who="iliary"), encoding="utf-8")

    # sanity: tests must pass inside the export, using only exported files
    r = subprocess.run([sys.executable, "tests/run_tests.py"], cwd=DIST, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-400:])

    # manifest for the standalone skill copy
    print(f"total {sum(1 for _ in DIST.rglob('*') if _.is_file())} files, "
          f"{sum(f.stat().st_size for f in DIST.rglob('*') if f.is_file())/1048576:.2f} MB")
    return 0 if r.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
