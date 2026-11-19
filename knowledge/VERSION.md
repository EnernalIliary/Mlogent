# Version and sources of truth (VERSION)

## Two versions side by side

| Code | Meaning | Location | Authority |
|---|---|---|---|
| v160.7_rt | the current live version (jar reflection + real machine) | out/_server160.jar, MBO/gamedata/v160.7/ | **numeric authority** |
| v159.3_src | the source tree (HEAD 5811844…, tag v159.3) | Mindustry-Source/core/src/mindustry | **semantic authority** |

The source lags one minor version behind: the source does not contain what v160.x added. Whenever the question is "is it still like this in the current version", v160.7 decides; whenever it is "how is the algorithm written", the source decides; a conflict between the two must be spelled out explicitly in the text.

## Numeric source-of-truth priority (adjudicate conflicts in this order)

1. v160.7 jar reflection (the real runtime values)
2. v159.3 source (formulas / field semantics / boundaries)
3. measurements on the real machine (MBO/ratio-calc, with experimental conditions)
4. hand-written manuals and notes (leads only; always go back to the source)
5. other copies (never indexed)

## Known errors (do not inherit them)

- ~~the old data/game/*.json had **all 447 craftTime entries at -1**~~ → **fixed in 2026-11**: `tools/dev/dump_game.py` reads `b.craftTime` directly, 33 blocks have real values (10–600 tick), and the other 414 blocks have no such field on the class (recorded as `null`). The -1 sentinel value is gone; a null means "this block has no craftTime", not "it completes instantly".
- the power-draw column in the block-recipe cheat sheet (`docs/游戏速查/方块配方.md`) is **per tick**, though the label says /s → a factor of 60 off.
- the root-level copies of (`蓝图逻辑模式库.md`) and (`蓝图层逐类精讲.md`) were deleted (2026-11-15, content duplicated by 07-patterns); the live version is `mindustry-blueprint/PATTERNS.md` / `BLUEPRINT-ANALYSIS.md`.
- instr_semantics.json exists in 3 size variants; the tools/ version in the repo (56.5KB) is authoritative, with instr_enums.json (v160.7) as the enum supplement.
- **unit numbers follow the jar**: toxopid armor jar=22 / v159.3 source=13; reign armor jar=30 / source=18; dagger main weapon jar=2 mounts × reload 26 (DPS 41.5) / source single mount reload 13 (DPS 83.1). Article headline values are always the jar; source differences go in a version note.
- **continuous damage is not estimateDPS**: meltdown's real DPS = damage/5×60 = **936**; the old draft's 4680 was the assumed value of BulletType.estimateDPS, and the Turret panel's 3120 is the product of dividing by reload twice.
- **BeamDrill baseRate in MBO/gamedata is off by 2× against the real value**; drillTime is not getDrillTime either (the latter adds 50×hardness).
- **the radar cache is 30 tick** (the old note said 40); the 5th argument of `uradar` (order) is a dead slot.
- **there are 8 ConditionOps** (the old question bank said 7, which only holds if always is excluded); `strictEqual` is not always false.
- **memory capacity is not 32**: memory-cell **64**, memory-bank/world-cell **512** (32 is only the class default at `MemoryBlock.java:12`, overridden by all three instances; v159.3 and v160.7 agree).
- **an out-of-range memory read is null (NaN), not 0**; an out-of-range write is silently dropped (`MemoryBlock.java:64-81`, comment text `Return null when out of bounds. (instead of 0)`).
- **`format` consumes 1 value per call**, filling the **lowest-numbered** placeholder already in the text buffer, so `print` must come before `format`; placeholders accept single digits 0-9 only (`{10}` is not replaced).
- **ipt is measured in points/tick, not points/s**: micro 2 / logic 8 / hyper 25 ⇒ 120/480/1500 points/s. The accumulator pool cap is **5×ipt** (micro 10 / logic 40 / hyper **125**); `maxInstructionsPerTick` only bounds the ipt that `setrate` can set (40 unprivileged, 1000 for a world processor) and **does not participate in the clipping** (`LogicBlock.java:565` uses `maxInstructionScale * ipt`, while `:558-559` resets an unprivileged processor's ipt to the block default every frame). The old claim that "hyper's 125 is clipped to 40" is wrong.
- **unit armor tables must not mix definitions**: spiroct jar=9 / source=5, arkyid 14/6, toxopid 22/13, eclipse 22/13, antumbra 17/9, scepter 20/10, reign 30/18 — U05/C05 now uniformly take the jar and carry a version note.
- **no turret has coolantMultiplier 0**: the minimum is foreshadow **0.4**, spectre **0.5**, arc **30** (a 75× spread); the old table's 0 is wrong.

## Environment traps (required reading before a rebuild or a repro)

1. `out/_kb/kb.sqlite3` is OneDrive-Pinned read-only: if MCP holds a handle, `unlink` raises WinError 5 and empties the database to a 24KB shell → you must use `tools/publish_db.py` (an in-place sqlite3 backup rewrite).
2. On a rebuild `KB_ROOT` must be the **repo root** (the root of the whole repository) and `KB_DIR` a temp directory; if `KB_ROOT` is set to `knowledge` it looks for `knowledge/out/_kblibs` → `ModuleNotFoundError: fastembed`.
3. `tempfile.mkdtemp(dir=<repo>/out/_sim)` in `tools/mlogsim.py` can hang for minutes inside a OneDrive-synced directory (stuck around `tempfile.py:375`); set the `MLOG_SIM_BASEDIR` environment variable to a local non-synced directory to bypass it (supported).
4. Warnings from the `check_kb.py` gate are advisory (exit 0 means compliant); `W_NUM_NO_SOURCE` mostly fires on source line numbers and example values, so you do not have to add a source line by line.

## 2026-11-08 consolidation rebuild (two external sessions merged in)

Two sessions in the same workspace merged their parallel knowledge bases into this one, and this library did a round of tidying on that basis (the content sources came in with commits 8494ea4 / 5c2f933 / a5cf501 / 805fb4d):

- **two parallel libraries retired**: the retriever notes (`docs/本地知识库.md`) and the ratio document (`docs/MBO与配比计算器.md`). Mechanics and numbers went into `02-world/W02/W03/W06/W07` + `04-units/U02`, retrieval usage into `tools/README.md`/`tools/REBUILD.md`, engineering detail into `ratio-calc/README.md`; the mapping is in `INTEGRATION.md` lines 45-46.
- **ratio derivation added**: `04-units/U02-production.md` lines 128-156, "per-building ratios and the whole-chain bottleneck" — per machine per second = 60/constructTime, machine counts in inverse proportion to rate, whole-chain output set by the slowest stage; includes a 1/1/1/2/5 example and the "pair T4/T5 at 1:1" counter-example.
- **conveyor throughput brought onto one definition**: v160.7 jar `speed=0.035`, `itemSpace=0.4` ⇒ **5.25 items/s** (the UI's `displayedSpeed=5` is a hand-entered approximation); v159.3 source `0.046` ⇒ 6.9 items/s is kept as a version note. 6.9 had previously been mistaken for the current value; `00-data/formulas.json`, `CHEAT.md` and the `W06` table now agree.
- **clean-up**: fixed the `EXEC.PROCESSOR.001` reference in `P01-architecture.md` that pointed at nothing → `EXEC.MODEL.001`; completed the definition in the conveyor row of the `W06` throughput table; deleted the stale `knowledge/index.repo.json` (the old 04:18 catalogue copy, moved to `_report/attic/`).
- **rebuild result**: index.json 57 articles / 18 tables; the production library **8,243 chunk / 140 files** (42.8MB, code 6322 / doc 1758 / data 163); postpublish three items PASS (A@1 16/20, off-library top1 0); 300 questions **hit@1 59.7% / hit@6 86.3% / mrr 0.694 / strong@6 94.2%** (per domain identical to the previous version, 41 questions missed).

## 2026-11-08 second round: turret verdicts + English-Chinese name mapping (external commits 49fac39 / 42aa158)

- **added `03-combat/C11-turret-verdict.md`** (`COMBAT.TURRET.002`, conf I): DPS/cost of 13 mainline turrets, selection by target armor, and the 7-turret anti-air gap that cannot hit air at all. DPS(0 armor) in table 1 / table 2 matches table 3 / table 4 of C10 cell by cell; cost = sum of item counts, power = `usagePerSecond`, range = `range/8`, all recomputed and passing; `targetAir=false` is exactly arc / hail / lancer / ripple / scathe / scorch / titan (3 of the 31 turrets records are non-combat: build-tower / repair-point / repair-turret).
- **added 5 name-mapping articles**: `02-world/W13-W15-name-blocks-*.md` covers **447 entries = all of `00-data/blocks.json`** (136 + 168 + 143, no duplicates and no gaps); `W16-name-items.md` (22 items + 11 liquids + 23 status = 56); `04-units/U06-name-units.md` (70 units, 60 with an official Simplified Chinese name).
- **naming source of truth**: `bundle.properties` + `bundle_zh_CN.properties` (2867 keys). Both language packs are now copied into the repo (`data/game/bundles/`, rationale in the `NOTICE.md` there), so the generator does not depend on an out-of-repo asset tree; external asset directories can still override, see `_bundle_dirs()` in `knowledge/tools/gen_name_docs.py` — `out/_server160.jar` has no bundle entry at all (the server jar strips resources), so names can only come from the asset packs; generator `tools/gen_name_docs.py` (key rule `<kind>.<id>.name`). `data/game/aliases.json` eats the same bundle: `knowledge/tools/gen_game_aliases.py` rewrites it, the first alias is always the official Chinese name, and old hand-written translations are demoted to search aliases only when they collide with no official name (2026-11-18 fixed 66 mistranslations, e.g. flare (耀斑→星辉), toxopid (毒蛛→天蝎)). The 36 blocks / 10 units / 3 statuses without a name are all internal placeholders (air, build1-7, `*-missile`, dummy, turret-unit-build-tower…).
- **cross-links**: C02/C10 → `[[COMBAT.TURRET.002]]`; W01 → `[[WORLD.NAMES.001]]`-003; U01 → `[[UNIT.NAMES.001]]`; a row "where to look up a Chinese name" added under the routing table in `08-evidence/CHEAT.md`.
- **rebuild result**: gate **61 articles / 0 error / 193 warning**; production library **8,317 chunk / 146 files** (43.6MB, doc 1831 / code 6322 / data 163); postpublish three items PASS (A@1 16/20, off-library top1 0, p50 68.3ms); 300 questions **hit@1 59.7% / hit@6 86.3% / mrr 0.693 / strong@6 94.2%** (the new content did not steal gold labels; the score is level with the previous version).

## 2026-11-15 fourth round: finished logic code library (P09)

- **new directory `07-patterns/code/`, holding six paste-ready finished .mlog files** (byte-for-byte copies from `Logic/`): `p09-haul-31slot-v27.mlog` (988 lines / 31 slots / stride 19 / sig `40d4b4c5cfef`), `p09-mine-30slot-v3.mlog` (966 lines / 30 slots / stride 18 / contains `ucontrol boost 1` ×30 / sig `daf5df426e9a`), `p09-haul-8slot-research.mlog` (313 lines / 8-slot research version / sig `78b191d1de02`), `p09-rows-v2.mlog` (71 lines / 50-row name table / declarations moved to the end / sig `6102cb1316d2`), `p09-luozi-v6-micro8.mlog` (463 lines / landing pad hard-coded to 8 / sig `8922af28ca6b`), `p09-luozi-v52-micro8.mlog` (149 lines / loop version / sig `b87d988e7ad9`). The subdirectory holds .mlog only — a .md there would raise `E_DOMAIN_DIR` because the directory name is not a domain name.
- **new article `07-patterns/P09-code-examples.md`** (`PATTERN.CODE.001` "finished logic code library (成品逻辑代码库)"): skeleton formulas (one round = 3 + N×stride; one round's time = entries/(60×ipt); relative dispatch `tmp.hp = -(N×stride+3)`) + a table of the six files' scale (with a "source" column) + five real-world counter-examples (putting the two dispatch ops at the head of the table lands them in slot slots−N, the return leg right after a failed `itemDrop` overwrites the outbound trip, `ubind u1` in the loc section is always empty when the unit count < N, the landing pad's cumulative quota floor sums short of npad by one pad, the transport loop itemTake 55 / itemDrop 48).
- **gate result**: `check_kb.py --root knowledge --write-tokens` ⇒ **PASS**, **92 articles / 0 error / 192 warning** (all warnings advisory; P09 itself has 0, its 5 first-round `W_NUM_NO_SOURCE` now carry `[src:]`/`[实测:]` markers and a table source column).
- note: the production library's chunks were not rebuilt — only the next `kb.py build` will bring P09 and `code/` into the index.

## 2026-11-15 third round: 28 per-turret pages + structural clean-up

- **added 28 per-turret pages under `03-combat/turrets/`**: `COMBAT.TURRET.101`-`118` (18 Serpulo (塞普罗) turrets) / `.201`-`.210` (10 Erekir (埃里克尔) turrets), each page 4.7-5.7KB with all seven sections (DPS / cost / ammo / range / evidence rows), cross-linked 56 times with the overview `C11-turret-verdict.md` (`COMBAT.TURRET.002`).
- **added `03-combat/_turrets/verdicts.serpulo.json` (52,441B) and `verdicts.erekir.json` (32,534B)**: the source data for the verdict copy that `tools/gen_turrets.py` renders; edit the copy and rerun the generator to regenerate the 28 pages + the overview.
- **added `00-data/turret_shots.json` (10,494B / 28 records)**: the only table that is not jar-reflected, derived by `tools/gen_turret_shots.py` from the v159.3 source as shots/pattern/barrels + evidence rows ⇒ canonical data tables 11 → **12**.
- **late-committed `07-patterns/P07-unit-multicontrol.md`, `P08-counter-architectures.md`** (previously only in the untracked list) ⇒ blueprint patterns 8 articles.
- **`C11-turret-verdict.md` rewritten as the overview** (98 lines, seven sections complete, 56 links out to T pages); `KB.md` / `README.md` / `00-data/README.md` had their structure trees and article counts synced.
- note: the chunk count from `kb.py build` is not strictly deterministic on the tokenizer estimate (the same content built twice gives 9,461 / 9,462), so the docs uniformly record ≈9,460.
- **rebuild result**: gate **91 articles / 0 error / 187 warning**; `index.json` regenerated (articles 93 / canonical 12 / records 1039); production library **≈9,460 chunk / 187 files / 19 data tables** (46.6MB, doc 2,098 / code 7,196 / data 167); postpublish three items PASS (bench20 A@1 16/20, off-library top1 0, p50 about 160ms (122-277ms on a rerun, varies with machine load)); 300 questions hit@1 **59.0%**, hit@6 **85.0%**, mrr 0.685.

## Delivery acceptance (v1.2, 2026-11-15)

| Item | Result | Repro command |
|---|---|---|
| gate | **92 articles / 0 error** (192 warning, all advisory) | `check_kb.py --root knowledge --all` |
| production library | **≈9,460 chunk / 187 files / 19 data tables** (46.6MB, doc 2,098 / code 7,196 / data 167) | `dbstat.py out/_kb/kb.sqlite3` |
| post-publish check | STRUCT / COUNT / RETRIEVAL **all three PASS** (chunks 9,461 = staging 9,461, files 187, journal flushed to disk) | `postpublish.py --db ... --staging ...` |
| 300-question frozen evaluation | coverage 100% / **hit@1 59.0% / hit@6 85.0%** / mrr 0.685 / strong@6 93.4% / off-library slot 0% (v1.2 rerun, including the 28 turret pages) | `08-evidence/bench/` (A+B+C all on, k=6) |
| derivation questions | formulas 22 questions hit@6 **72.7%** (16/22) / hit@1 59.1%; cross-source 24 questions hit@6 **83.3%** (20/24) / hit@1 75.0% | `bench/questions-derive.jsonl` (k=6) |
| 20-question smoke (bench20) | A@1 **16/20 (80%)**, A@3 16, off-library top1 **0/20**, p50 about 160ms (122-277ms on a rerun, varies with machine load) | `bench20.py --db out/_kb/kb.sqlite3` |
| executable probes | **17 PASS / 1 FAIL (claims since fixed) / 2 INCONCLUSIVE** | `08-evidence/probes/_run_all.py` |
| jar ground-truth check | **final RERUN: 178 records / PASS 175 / FAIL 0 / 3 definition gaps** (①CHEAT 26 · ②C10 14 · ③W06/W07 41 · ④C02 28(3 definition gaps) · ⑤C05 41 · ⑥C06 28), exit code 0 | `python knowledge/tools/rt_verify.py`; detail in `08-evidence/_report/_rtverify/RERUN.md` |

The three retrieval switches (all on by default, can be turned off with environment variables) are in `tools/REBUILD.md` §4: `KB_ONLY_KNOWLEDGE` (search knowledge/ only), `KB_DEDUPE_FILE` (dedupe by file), `KB_ASCII_BOOST` (weight ASCII identifiers).

## Current content scale (v1.2)

| Domain | Articles | Directory |
|---|---|---|
| execution model | 6 | `01-execution/` (E01-E06) |
| world / blocks | 16 | `02-world/` (W01-W16, including the name mappings in W13-W16) |
| combat | 39 | `03-combat/` (C01-C11 + `turrets/` T101-T210 per-turret pages) |
| units | 6 | `04-units/` (U01-U06, including the unit name mapping in U06) |
| campaign | 6 | `05-campaign/` (CAMP.*) |
| mlog language | 8 + 2 JSON | `06-mlog/` (M01-M08, instructions.json, enums.json) |
| blueprint patterns | 9 + JSON | `07-patterns/` (P01-P09, six finished .mlog in `code/`, idioms.json) |
| evidence / evaluation | 2 + 300 questions + probes | `08-evidence/` (claims.jsonl, CHEAT.md, bench/, probes/) |
| data tables | 12 canonical (+7 raw spot-check copies) | `00-data/` (blocks/turrets/turret_shots/units/bullets/items/liquids/status/rules/formulas/constants/src_anchors) |
