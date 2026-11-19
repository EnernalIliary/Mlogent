# Mindustry mechanics knowledge base · entry point (KB.md)

> Version: v1.2 · covers Mindustry v160.7 (numbers) / v159.3 (source semantics) · vanilla mechanics only, no mods and no tool-product development
> Audience: **AI and humans**. The goal is not "you can look up an answer" but **"you can derive an answer"**.
> Scale: **92 articles / 12 canonical data tables / 85 assertions / 20 executable probes / 300 evaluation questions**; the retrieval database holds ≈9,460 chunk, measured hit@1 **59.0%**, hit@6 **85.0%** (k=6, frozen 300-question set).

## 0. 30-second start

1. Read this file first (you are reading it) → then `08-evidence/CHEAT.md` (the cheat card: 40 pitfalls + 30 numbers + 20 routes) → to wire in an AI, see `AI-SETUP.md`. The contract and versions are in `CONVENTIONS.md` and `VERSION.md`; **for whether the old knowledge bases still count, see `INTEGRATION.md`**.
2. Want to know "how a mechanic computes" → look up tables in `00-data/`, formulas in `05-campaign/`.
3. Want to know "what number a thing has" → `00-data/blocks.json`, `turrets.json`, `bullets.json`, `units.json`.
4. Want to write or read mlog → `01-execution/` (execution model and pitfalls) + `06-mlog/` (instruction semantics).
5. Want to reuse a proven pattern → `07-patterns/` (architectures and idioms).
6. Doubt a conclusion → `08-evidence/claims.jsonl` (85 re-testable assertions) + `probes/` (executable probes) + `bench/` (300 evaluation questions).

## 1. Directory map

| Directory | Contents | When to use |
|---|---|---|
| `00-data/` | machine-readable fact tables: blocks/turrets/bullets/turret_shots/units/liquids/items/status/rules + formulas.json | looking up any number, doing arithmetic, checking a conclusion |
| `01-execution/` | the mlog execution model, instruction budget, 30 semantic pitfalls, variable boundaries, time precision, cross-version differences | required reading before writing logic; debugging weird behaviour |
| `02-world/` | blocks and anchors, recipes, power, liquids, heat, logistics, drilling, payloads, terrain, storage, configuration, sandbox, English-Chinese name tables (W01-W16) | how a mechanic "works" |
| `03-combat/` | damage pipeline, turrets, ballistics, status, armor, unit weapons, healing and shields, enemies, defense, DPS worked examples, turret verdicts (C01-C11), per-turret pages (turrets/ T101-T118 / T201-T210) | combat numbers and damage resolution, turret selection |
| `04-units/` | unit types/movement, production, AI, abilities, experience and levels, unit name tables (U01-U06) | unit behaviour and throughput |
| `05-campaign/` | waves, difficulty, victory and defeat, enemy bases, version differences, the full Rules field list (CAMP.*) | campaign and rule customisation |
| `06-mlog/` | instruction table (73 entries in instructions.json) + 8 articles on language semantics (M01-M08) | looking up instruction arguments and semantic edges |
| `07-patterns/` | architecture, state machines, buses, data structures, targeting, performance, unit multicontrol, @counter architectures, finished code library (P01-P09) + six paste-ready .mlog files in `code/` + idioms.json | designing a blueprint / copying a finished one |
| `08-evidence/` | claims.jsonl (85 re-testable assertions), probes/ (executable probes), idioms.json, anti-patterns.md, bench/ (300 questions + cross-source derivation questions) | verification and evaluation |
| `tools/` | extract_rt.py (jar reflection), extract_src.py (source tree), check_kb.py, build_index.py, eval_kb.py, kb.py | reproducing and maintaining |

## 2. AI usage protocol (important)

### 2.1 Retrieval order (do not skip steps)
1. **Look up the table exactly**: `00-data/*.json` — structured, with ids; whatever hits first wins.
2. **Mechanics formulas**: `00-data/formulas.json` — take the formula, then substitute.
3. **Article body**: read the `.md` for the domain, and pay attention to the "Common misconceptions" section — it exists to correct intuition.
4. **Evidence layer**: find the re-testable assertion in `08-evidence/claims.jsonl`; when conclusions conflict, trace back by id.
5. **Source / source of truth**: only when the above is not enough, read `Mindustry-Source/` (v159.3 semantics) or rerun `tools/extract_rt.py` (v160.7 numbers).

### 2.2 Confidence (the conf field on every piece of knowledge)
- `S` checkable in the source (file:line given)
- `E` reproducible measurement (script and output given)
- `I` derived from S/E (the derivation chain must be written out)
- `U` unverified (**an answer must declare the uncertainty**; never use it as fact)

### 2.3 Five hard rules
1. **Never state a number without a source**. It comes from `00-data/`, or from `file:line`, or from a measurement record.
2. **Units are explicit**. Always say whether a rate is `/tick` or `/s` (1/tick = 60/s), and whether a length is tile or px (1 tile = 8 px).
3. **Two versions**. Numbers default to v160.7; semantics and source citations are marked v159.3; known differences are in `VERSION.md` and `05-campaign/CAMP.VERSION.001`.
4. **Counter-examples first**. When learning a mechanic, read its "Common misconceptions" and the anti-patterns first; a wrong intuition is more dangerous than ignorance.
5. **No tooling**. This library describes the game and mlog only; tool, mod and product material does not belong here.

### 2.5 Self-check before answering (4 questions)
1. Does this number come from `00-data/`, or am I reciting it?
2. Are the units stated (/tick or /s, tile or px)?
3. Does the "Common misconceptions" section of the relevant article contradict this conclusion? Read it before answering.
4. On a conflict, did I compare the two versions (v160.7 numbers / v159.3 semantics)?

### 2.4 Answer style (for an AI)
- Give the **conclusion + the arithmetic** first, then the source (an anchor such as `00-data/blocks.json#id=duo`).
- On a trade-off, give **two or more options** with their costs (power / space / budget / complexity).
- If unsure, mark `conf: U` and say which verification step is missing; **do not paper over it with "generally speaking"**.

## 3. 12 capability domains → article index

| # | Capability domain | Main entry points |
|---|---|---|
| 1 | Execution model and tick | `01-execution/E01`, `06-mlog/M01` |
| 2 | Variables and scope | `01-execution/E03`, `06-mlog/M02` |
| 3 | Control flow and time | `01-execution/E04`, `06-mlog/M03` |
| 4 | Reading, writing and sensing | `06-mlog/M04` |
| 5 | Drawing and text | `06-mlog/M05` |
| 6 | World interaction | `06-mlog/M06`, `02-world/W11` |
| 7 | Unit control | `06-mlog/M07`, `04-units/U03`, `07-patterns/P07`, `07-patterns/P08` |
| 8 | Performance and budget | `01-execution/E01`, `06-mlog/M08`, `07-patterns/P06`, `07-patterns/P08` |
| 9 | Blocks / power / heat / logistics | `02-world/W01-W06` |
| 10 | Combat and damage | `03-combat/C01-C05` |
| 11 | Units and throughput | `04-units/U01-U05`, `03-combat/C06` |
| 12 | Campaign and rules | `05-campaign/CAMP.*` |

(The full article list is generated into `index.json` by `tools/build_index.py`.)

### 3.2 Q&A route: how do I write Mindcode syntax

For questions like "should `if` be followed by `then` or `do`", "does the function really get called", "how do I declare an array", see
`06-mlog/M10-Mindcode-Syntax.md` (`MLOG.MIND.002`): every rule comes with the mlog it compiles to, and all five traps
(`then` is not `do`, `end` needs a semicolon, an unused variable is an error under optimisation, `stack` does not give you arrays,
the trailing banner line) quote the actual error text. For compile options and version arbitration, stick with M09.

### 3.3 Names do not line up: Chinese name / legacy translation / English id

The same thing often has three names in Chinese (official, legacy translation, colloquial), and there is no rule linking the English id to the Chinese name.
For questions like "which turret is parallax (差扰)" or "what is the id of tempered glass (钢化玻璃)", do not guess — look in `GLOSSARY.md`:
the upper half is the jargon of concepts and the toolchain (micro processor (微处) / accumulator pool (累积池) / payload (载荷) / diff (差分)…), the lower half is the **504 entities, three name columns** generated from
`data/game/bundles/*.properties` + `data/game/aliases.json`
(English id / official English name / official Chinese name / legacy and colloquial). When a search misses, change the word in this order:
official name → English id → legacy translation → colloquial; `tools/kb_grep.py` and the MCP `mlog_kb` both match on the word surface,
so changing the word works better than changing the question.

English readers (or English-only models) come in through `INDEX.en.md`: one line of English title + a one-sentence summary per article, 86 articles.

### 3.1 Q&A route: the Mindcode compile front end (`06-mlog/M09`, `MLOG.MIND.001`)

| Question | Where it lands |
|---|---|
| "how does a `.mnd` become mlog / how do I read a compile error" | `06-mlog/M09` §1–§3, §6 |
| "why default to 3.19.3 rather than 3.21.0" | `06-mlog/M09` §5; the long-form rationale in `docs/Mindcode集成.md:54-84` |
| "how do I call `mindcode_compile` / `mlog_validate(mind=…)`" | `06-mlog/M09` §3, §7 |
| "should this report `unsupported_environment` or `compilation_error`" | `06-mlog/M09` §8 (look at `diagnostics[0].kind` first) |

## 4. Numeric source-of-truth priority

1. `00-data/*.json` (generated by reflection on the real v160.7 server, `tools/extract_rt.py`)
2. `Mindustry-Source/core/src/**` (v159.3, the semantic authority)
3. the measurements that pass in `08-evidence/claims.jsonl`
4. the article bodies in this library
5. other notes in the repo (`../MBO/`, `docs/`, `Logic-Docs`) — **leads only, never evidence** (`MBO/` has been split out into a sibling project)

Known-error list (read it first): `VERSION.md` §known errors. Typical cases: craftTime in `data/game` was once -1 everywhere (re-imported as real values in 2026-11 by `tools/dev/dump_game.py`: 33 blocks carry a value, 414 are null); the deleted block-recipe cheat sheet (`docs/游戏速查/方块配方.md`) had a power-draw column that is actually per /tick but was labelled /s (a factor of 60 off).

## 5. Common traps Top 10 (learn these first; they avoid 80% of the mistakes)

1. `wait` takes **seconds** (`LExecutor.java:1218-1232`: `curTime += Time.delta/60f`), so `wait 1` ≈ 60 tick; writing "wait N tick" is the classic mistake. `@time` is in **milliseconds** (`GlobalVars.java:195`); only `@second`/`@minute` are seconds.
2. `reload` is "ticks between two shots"; DPS is `damage × shots / reload × 60`, and do not forget `ammoMultiplier`.
3. `range` is in **tile** (1 tile = 8 px); bullet range = `lifetime × speed` in px, so divide by 8 for tiles.
4. `usage` is power per tick, `usagePerSecond = usage × 60` (the field only exists in v160.7).
5. Whether armor reduction is **multiplicative or subtractive** follows the current `Damage.java` implementation and has changed between versions — do not recite an old conclusion.
6. Conveyor throughput is `items/s = speed × 60 / per-item slot`, not the "speed" itself.
7. Status effects of the same kind **do not stack** (the duration refreshes); different kinds multiply; order affects the result.
8. `getlink` indices **start at 0** and shift as buildings change, so the numbering is wrong after a blueprint is pasted again.
9. `@counter` is writable and a jump is an **absolute index**; changing it inside a loop produces unpredictable jumps.
10. The per-tick instruction budget is finite (`instructionsPerTick` and friends), so a big loop must be split across ticks.
11. `set @ipt ...` / `set @unit ...` are silently dropped (`putConst` at `LAssembler.java:26-27`): constants cannot be changed, only `setrate`/`ubind` change runtime values; `@counter`, by contrast, is writable.
12. The **5th argument of `uradar` (order) is a dead slot**: writing it neither errors nor has any effect; the radar cache is **30 tick** (`LExecutor.java:761-763`), not 40.
13. `ucontrol` coordinate arguments are always in **tile** (internally `World.unconv` multiplies by 8 to get px); feeding pixel coordinates lands you 8× off.
14. `strictEqual` is not always false: the `(a,b)->false` in `ConditionOp` is only the `function` field, and `LExecutor.test()` special-cases identical type bits plus exact equality, so `jump strictEqual` can hold.
15. Memory capacity is not 32: **memory-cell 64 / memory-bank 512 / world-cell 512** (32 is the class default); **an out-of-range read returns null (NaN), not 0**, and an out-of-range write is silently dropped (`MemoryBlock.java:64-81`).
16. `format` replaces **one** placeholder per call, and only the **lowest-numbered one already in the text buffer**; placeholders accept single digits `{0}`-`{9}` only, so the order is "`print` first, then `format`".
17. `@ipt` is in **points/tick** (hyper 25 ⇒ 1500 points/s); the real single-tick budget is `min(5×ipt, maxInstructionsPerTick)`, so hyper is clipped to **40** — do not compute loop cost from 125.

## 6. Maintenance

```powershell
# 重新生成 v160.7 数据表（需 out/_server160.jar + out/jre21）
python knowledge/tools/extract_rt.py
# 索引 / 门禁（--strict 让 warning 也阻断）
python knowledge/tools/build_index.py
python knowledge/tools/check_kb.py --all
# 重建检索库：KB_ROOT 必须是仓库根，KB_DIR 指定输出目录
$env:KB_ROOT='<仓库根>'; $env:KB_DIR='<临时目录>'
python knowledge/tools/kb.py build
# MCP 在跑时不要直接覆盖 out/_kb/kb.sqlite3（WinError 5），用 backup 原地发布
python knowledge/tools/publish_db.py <临时目录>\kb.sqlite3 out\_kb\kb.sqlite3
# 发布后固定义务：三项校验（STRUCT/COUNT/RETRIEVAL）
python knowledge/tools/postpublish.py --db out/_kb/kb.sqlite3 --staging <临时目录>\kb.sqlite3
# 评测（300 题，A+B+C 检索开关默认已开）
python knowledge/tools/eval_kb.py --kb knowledge --engine kb -k 6
# 冒烟（20 题确定性样本，同一批行号）
python knowledge/tools/bench20.py --db out/_kb/kb.sqlite3
```

A `check_kb.py` warning is **advisory and non-blocking** (exit 0 means compliant); most `W_NUM_NO_SOURCE` hits are source line numbers and example values, so you do not have to add a source line by line.

To add an article: copy the template → fill in the frontmatter (unique id) → all seven sections present → zero errors from `check_kb.py` → rerun the index and the kb rebuild → add a re-testable assertion to `claims.jsonl`.
