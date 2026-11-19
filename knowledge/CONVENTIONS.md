# Knowledge base writing conventions (CONVENTIONS) v1

This file is the **single writing contract**. Everything produced under knowledge/ must obey it, or check_kb.py fails.

## 1. Directories and ownership

    00-data/       machine-readable fact tables (script-generated; never hand-edit)
    01-execution/  execution model (processor / budget / frame diff / sync)
    02-world/      blocks / logistics / power / liquids / heat / drilling
    03-combat/     ballistics / damage / armor / status / turrets
    04-units/      units / AI / abilities / production
    05-campaign/   waves / rules / win and loss
    06-mlog/       the language layer (syntax / instructions / traps)
    07-patterns/   blueprint architecture / idioms / anti-patterns
    08-evidence/   evidence (claims/probes/bench)
    tools/         generation and validation scripts
    .index/        retrieval artifacts

## 2. Knowledge atom ID

Format: domain.subdomain.three-digit number, all upper case.

    WORLD.LOGISTICS.002
    COMBAT.DAMAGE.003
    MLOG.BUDGET.001
    EXEC.PROCESSOR.001
    UNIT.AI.001
    CAMP.WAVES.001
    PATTERN.SWARM.001

- Domain codes are fixed: EXEC / WORLD / COMBAT / UNIT / CAMP / MLOG / PATTERN / DATA
- one md = one ID; an article may be long, but past 250 lines it must be split into several IDs in the same subdomain.
- an ID is never reused and never renumbered once published; retire it with status: deprecated.

## 3. frontmatter (required in every article, YAML)

    ---
    id: WORLD.LOGISTICS.002
    title: conveyor throughput and capacity
    domain: world
    status: active          # active | draft | deprecated
    ver: [v160.7_rt, v159.3_src]
    conf: E                 # S source / E measured / I inferred / U unverified
    src:
      - ("MBO/docs/14-传送带与布线器实测.md:1-60")
      - "mindustry.world.blocks.distribution.Conveyor (v159.3)"
    data: [00-data/logistics.json#conveyor]   # data tables cited by this article
    depends: [WORLD.LOGISTICS.001]
    tags: [logistics, throughput, conveyor]
    tokens: 1600
    ---

tokens is backfilled by the check script; you do not hand-write an exact value.

## 4. Confidence (conf)

- **S**: directly backed by a source line number or a jar-reflected field.
- **E**: measured on the real machine (MBO/ratio-calc/mlog_sim probes), with the experimental conditions attached.
- **I**: inferred from S/E, and the derivation chain must be written out in the article.
- **U**: unverified; it must state "what experiment would verify this", and it **must not appear on an answer path in KB.md**.

> **Source paths are written with their old names and found in the sibling directory**: `MBO/`, `ratio-calc/`, `assetsraw/` are
> **sibling standalone projects** split out of this repository (`../MBO/`, `../ratio-calc/`, `../TextureMDT/`). `src:` and `[measured: …]`
> keep the old name so history still lines up; when you actually go looking for the file, go to the sibling directory, because it is not in this repository.

## 5. Hard rules (violating one is a failure)

1. **no number without a source**. Every value must satisfy one of these:
   - it comes from 00-data/*.json (write `see DATA#xxx`, or cite the field name directly);
   - it is immediately followed by `[src: file:line]`;
   - it comes from a measurement and carries `[measured: MBO/docs/xx]`.
   Better to write "see the data table" than to write a number from memory.
2. **units must be explicit**. /tick and /s must not be mixed; for energy 1 unit/tick = 60/s. Write `1.5/tick (90/s)`.
3. **two versions**: wherever v159.3 and v160.7 may differ, write `[v159.3]… [v160.7]…`; never just one.
4. **a counter-example is mandatory**. Every article needs at least one "when this does not hold / common misconception" — that is what stops hallucination.
5. **no product or tool-development content** (panel widths, jobqueue, undo snapshots and the like); that belongs to the engineering library.
6. **no mod content** (DP-*, MindustryX); v1 covers vanilla only.

## 6. Seven-section template

    ## In one sentence
    <a one-sentence conclusion that can serve as the first line of an answer>

    ## Rules / formulas
    <computable rules; put formulas in a ``` code block; state what each variable means>

    ## Numbers
    <a table, generated from 00-data where possible; list typical values and boundary values>

    ## Source anchors
    <class:line, and what that piece of code is doing>

    ## Measurements and counter-examples
    <real numbers + experimental conditions; at least one counter-example / boundary>

    ## Common misconceptions
    <the 2-4 things an AI is most likely to get wrong, each with the correct statement>

    ## Related
    <ID list + data table paths>

## 7. Tables and code

- use markdown tables; the first column is the id or the name, and numeric columns carry units.
- code block language tags: mlog / json / java / text.
- always write paths relative to the repository root, so they are easy to grep.

## 8. Data table contract

Every 00-data/*.json record must contain:

    id        the in-game id (kebab-case)
    name      the name field
    src       the source ("jar:v160.7#..." or "src:path:line")
    ver       "v160.7" | "v159.3" | "both"
    value fields   uniformly { v: value, unit: unit }, or a bare value with the unit declared in that table's README

The table-level README states the units, the definition, the generator script, the generation time and the record count.

## 9. Knowledge ownership and commit points (since 2026-11-08)

**New mechanics / numbers / formulas / logic semantics knowledge is committed to `knowledge/` only**, filed by the domains in §1; data goes to `00-data/` and evidence to `08-evidence/`. Stop appending to the old documents below — they serve only as archive and as regression-test input:

| Old document | Status | Still read by |
|---|---|---|
| `Logic-Docs-v1.1.0.md` | archive (partly absorbed) | the src of `tests/docsig/run_docsig.py`, `rules/slot-not-in-enum.json`, `rules/under-arity.json` |
| `mlog工作笔记.md` | archive (partly absorbed) | `tests/docsig/run_docsig.py` |
| `蓝图逻辑模式库.md` / `蓝图层逐类精讲.md` | **the root-level copies were physically deleted (2026-11-15)**; the pattern-library content lives in 07-patterns | the surviving copies `mindustry-blueprint/PATTERNS.md` / `BLUEPRINT-ANALYSIS.md` are now docsig's input source and are no longer derived from the root level |
| `docs/游戏速查/` | archive (a thin projection; its numbers are void) | DOC_GLOBS in `tools/kb.py` (retrieval corpus) |
| `docs/断言表.md` / `docs/验证记录.md` | archive (the real mechanic parts are layered into claims/probes already) | referenced by product-side process |

- tool usage (how to run the commands, how to self-check) still belongs to `mindustry-blueprint/SKILL.md`; mod and product docs still live under (`docs/Mlog辅助-*`). Neither is a knowledge entry, so do not write them into `knowledge/` (see §5 rules 5 and 6).
- if you physically delete an old document, you must in the same change update `tests/docsig/run_docsig.py` (it uses those files as input to validate signatures) and the `src` strings in `rules/*.json` that reference it, then run `python gate.py --full`.
- the retrieval corpus is built from `knowledge/` only (`build_index.py --root knowledge` → `kb.py build` → `publish_db.py` → `postpublish.py`); working artifacts go in `knowledge/_report/` and stay out of the index.
