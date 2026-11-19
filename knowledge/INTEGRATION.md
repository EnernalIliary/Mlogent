---
id: INTEGRATION.001
title: Legacy knowledge base integration mapping (what replaces what)
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src: 本仓库调研报告《Mindustry机制知识库-构建计划.md》§1.1 资产地图
data: []
depends: []
tags: [integration, legacy, migration]
tokens: 0
---

# Legacy knowledge base integration mapping

> Path convention: `MBO/`, `ratio-calc/`, `assetsraw/` in this document (and in each article's `src:`) are **sibling standalone projects**
> that were split out of this repository long ago (they are now `../MBO/`, `../ratio-calc/`, `../TextureMDT/`). They are written with their old names only so that
> historical sources stay matchable character for character — when citing them, look in the sibling directory, do not expect them to be in this repository.

> This document answers one question: **do the scattered knowledge bases that used to live in this repository still count, and when should you go and consult them?**
> The three-sentence version: **for any mechanics question this knowledge base (knowledge/) is authoritative**; old assets serve only as "original source" and "unique evidence"; near-duplicate copies among the old assets are no longer maintained.

## 1. How the three kinds of legacy asset are handled

| Category | Disposition | Reason |
|---|---|---|
| **fully absorbed** (content moved into articles, numbers re-checked against the jar) | no longer a basis for answers; cited only when you need to trace "where did this conclusion originally come from" | two sources of truth = divergence sooner or later; this library carries `src:` anchors so it can be traced back |
| **partly absorbed** (mechanism conclusions absorbed, not all measurement/ratio detail) | check this library first; numbers it explicitly does not contain may then be looked up in the old library, labelled "from an old measurement, not re-checked" | measured values depend on the environment and must not be mixed into field values |
| **not absorbed** (very large corpora, external tools) | still used the old way; this library does **not** copy them | running retrieval over a 1222MB corpus drowns the useful content |

## 2. Item-by-item mapping

| Old asset | Location | Size | Status | Counterpart in the new library | Notes |
|---|---|---|---|---|---|
| authoritative source v159.3 | `Mindustry-Source/core` | 807 .java / 5.9MB | **kept as the semantic source of truth** | every `core/...:line` in the library's `src:` points at it | the core module only; all numbers are overridden by the v160.7 jar |
| runtime dump v160.7 | `MBO/gamedata/v160.7/gamedata.json` | 3.0MB | **distilled** | `00-data/*.json` (blocks/turrets/units/items/liquids/bullets/status/rules, 447/26/70/22/11/137/23/118 records) | the raw parameters (consumers[]) remain the last stop for "how much power/liquid does block X draw, exactly" |
| thin projection | `data/game/*.json` | 234KB (`aliases.json` 19KB) | **partly usable** (re-exported in 2026-11 by `tools/dev/dump_game.py`: blocks have 15 fields including craftTime/capacity/range/reload/liquid output; unit weapons carry real ranges; still no class/types) | `00-data/` | quick lookups go through `tools/game.py`; fine semantics (class / liquid-consumption multiplier / the 75 columns) still go to `00-data/` |
| instruction semantics table | `tools/instr_semantics.json` | 56.5KB | **superseded** (its definition is "LStatement classes = 53 records") | `06-mlog/instructions.json` (73 records) + `enums.json` (13 groups) | from the old table only arity/defs/uses keep archaeological value; three size variants have already been found (56.5/62.8/50.6KB) |
| enum table | `tools/instr_enums.json` | — | **superseded** | `06-mlog/enums.json` | adds the full RadarTarget/LLocate/LAccess sets |
| language manual | `Logic-Docs-v1.1.0.md` | 546KB / lines (1.22万行) | **partly absorbed** | `06-mlog/M01-M08` | only 15-20% of the manual is mechanism prose, the rest transcribes instructions one by one; this library's 73-instruction table covers it, but an "unusual argument combination of instruction X" may still only be there |
| experience notes | `mlog工作笔记.md` | 227KB / 12 chapters | **partly absorbed** (iron rules → traps/anti-patterns) | `01-execution/E02`, `08-evidence/CHEAT.md`, `07-patterns/anti-patterns.md` | the notes' "old conclusions since overturned" were not carried over one by one; on a self-contradiction this library wins |
| assertion bank | `docs/断言表.md` | 202 records | **layered already**: 102 real-mechanics records → claims.jsonl(85) + probes(20); 82 tool-development records **discarded** | `08-evidence/claims.jsonl`, `probes/` | 41% of the original table is product assertions such as jobqueue/undo/panel width, which is not mechanics knowledge |
| verification log | `docs/验证记录.md` | 91KB / 120 records | **partly absorbed** (59.4% coverage) | the 20 executable probes in `08-evidence/probes/` + the verdicts in `claims.jsonl` | this library turns it into "rerunnable script + snapshot output", which is more re-verifiable than a pure text log |
| pattern library | `PATTERNS.md` (the root-level `蓝图逻辑模式库.md` was deleted on 2026-11-15) | 107KB / 2471 lines | **restructured** | `07-patterns/P01-P09` (including the six finished .mlog in `code/`) + `idioms.json`(30) + `anti-patterns.md`(AP-01..20) | the old text's "567 bugs" is on a 1081-logic-block definition; this library measures 677 on the `.mlog` definition (142 files); both definitions are recorded side by side |
| blueprint deep-dive | `BLUEPRINT-ANALYSIS.md` (the root-level `蓝图层逐类精讲.md` was deleted on 2026-11-15) | 79KB / 1875 lines | **not merged into 07-patterns** (it is "blueprint broken down class by class", not mechanics) | — | consult it only when you need "how a particular finished blueprint is implemented"; the deletion removed a duplicate copy only, the body stays with the skill docs |
| measurement layer | `MBO/docs` 00-23 + README | 22 articles / 21KB | **partly absorbed** | `02-world/W06/W07/W10` cite conveyor 4.9/s, silicon 2.973/s and the like | measurement values are marked `conf: E`; on a conflict with a field value, trust the field first and then explain "why the measurement differs" |
| ratio model | `ratio-calc` (gamedata.js 1.13MB) | 33 factories / 17 unit factories / 14 power / 10 drills | **not absorbed** (it is a calculator, not knowledge) | `02-world/W02` covers recipe mechanics only | to compute "how many machines does this production line need", still use it |
| ratio document (built by me) | `docs/MBO与配比计算器.md` | 246 lines | **retired (2026-11-08)** | mechanics/numbers merged into `02-world/W02/W03/W06/W07` + `04-units/U02`; the engineering part is carried by `ratio-calc/README.md` | the user asked for "everything to be committed to knowledge from now on"; a parallel knowledge base would create two sources of truth |
| retriever notes (built by me) | `docs/本地知识库.md` | — | **retired (2026-11-08)** | `knowledge/tools/README.md` + `REBUILD.md` | retrieval/rebuild usage belongs to the knowledge tool docs |
| skill package | `mindustry-blueprint/SKILL.md` (and 6 copies) | 61.5KB | **not replaced** (a superset of operating instructions) | — | it is "how to use the tools", this library is "what the mechanics are" — complementary |
| large corpus | `logic-corpus` (12.8MB / 2273 files) | 833 .msch + 5774 logic blocks | **statistical evidence only** | the frequency numbers in `07-patterns` come from it | already cited by this library as "how real code is distributed"; no need to search it directly any more |
| even larger corpus | `C:\Users\lliary\mlog-corpus` | 1222MB / 61822 files | **not absorbed** | — | searching it drowns the knowledge; used only for "how common is this idiom" statistics |
| external compiler | `C:\Users\lliary\src\mindcode` | 27.9MB | **for cross-validation** | — | on a semantic dispute, compare three ways (source / this library / mindcode) |
| global skill | `~/.dsh/skills/mlog-agentskill` (with mlog.py/mlogcheck.py/instr_semantics.json) | 35KB + tools | **toolchain still used**; its data tables are superseded by this library | `knowledge/tools/` | do not mix the two: this library does not copy its 82KB validator, it just calls it |

## 3. When you may go back to a legacy asset

Only in these four cases, and the answer must state "from a legacy asset, not re-checked by this library":

1. where this library's own article explicitly says it is not covered here and points at the old document;
2. when you need the implementation of a **finished blueprint** or a **specific mod** (blueprint deep-dive, MlogAuxiliary, DP-*);
3. when you need a **stopwatch-style measurement** and this library only gives the field value (MBO/docs);
4. when you need **ratios / machine counts for a production line** (ratio-calc).

Otherwise the answer may come from `knowledge/` only — because the legacy assets contain at least 6 known classes of error (treating the v159.3 source as current, craftTime all -1 (fixed in 2026-11), power draw per tick read as per second, two inconsistent Logic-Docs copies, three sizes of the semantics table, several copies of one conclusion), and this library has fixed each one and backs itself with the known-errors list in `VERSION.md`.

## 4. The three "deduplication" actions taken during integration (so it does not fork again)

1. **single source of truth**: numbers → `00-data/` (jar reflection); semantics → `Mindustry-Source` + article anchors; no second hand-copied table of numbers is kept.
2. **the definition goes into the file header**: every article marks both versions with `ver:`, and where the two versions differ the body uses a "version note" rather than two parallel tables.
3. **old copies are "frozen"**: `PATTERNS.md`, `Logic-Docs-v1.1.0.md` and the like stay where they are (externally referenced), but **any mechanics fix is made in `knowledge/` only**; the next time an old text conflicts with this library, file a claims entry according to the "conflict handling" of `CONVENTIONS.md`. (2026-11-15 exception: the user ruled that the root-level `蓝图逻辑模式库.md` / `蓝图层逐类精讲.md` duplicate their skill copies, so both root-level files were physically deleted; the body remains under `mindustry-blueprint/`.)

> **Tightened on 2026-11-08**: new knowledge is **committed to `knowledge/` only** (rules in `CONVENTIONS.md` §9); old documents are demoted to read-only archive and no longer receive new content. Before a physical deletion you must update `tests/docsig/run_docsig.py` and the `src` in `rules/*.json` in the same change (they still use these files as input), then run `python gate.py --full`. In the same period the knowledge base's own working artifacts were cleaned up: `knowledge/_report/attic` (6 old kb.sqlite3 files, 198 MB) and 46 one-off probe scripts (`p_*.py` and the like); the gate still reports `RESULT: PASS` and the index and the database agree.
