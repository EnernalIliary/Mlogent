# knowledge/tools — generators / gates / retrieval rebuild

Three commands cover day-to-day maintenance. Every script depends only on the standard library (kb.py additionally needs out/_kblibs* + out/_kbmodels), with no network access.

## 1. Generate the master index knowledge/index.json

    python knowledge/tools/build_index.py
    python knowledge/tools/build_index.py --root <kb root> --out <target path>    # dry run / mirror
    python knowledge/tools/build_index.py --check                                 # compare only (CI)

Output structure (the file an AI reads first; fields are only ever added, never changed):

    version / generated / root / read_order
    domains[]  {id, code, title, desc, articles[{id,path,title,tokens,conf,ver,status,lines}]}
    data[]     {path, kind(canonical|raw), records, bytes, keys[]}   # 00-data/*.json
    evidence[] {path, kind, bytes, lines|entries}       # 08-evidence/{claims,probes,bench}
    evidence_dirs[] {path, kind, files, bytes}          # subdirectory summary (empty probes dirs appear too)
    docs[]     {path, bytes, tokens}                    # KB.md / CONVENTIONS.md / VERSION.md
    counts     {articles, by_domain, data_tables, data_records, data_raw_tables,
                evidence_files, evidence_by_kind, evidence_dirs, tokens_total, empty}
    Field semantics are in INDEX_CONTRACT.md (changing a field means changing that file first).

`--check` compares after dropping the `generated` timestamp and exits 1 on a mismatch. An empty library still generates (counts.empty=true, exit 0).

## 2. Static gate check_kb.py

    python knowledge/tools/check_kb.py                   # human-readable report
    python knowledge/tools/check_kb.py --json            # machine-readable (CI artifact)
    python knowledge/tools/check_kb.py --write-tokens     # backfill frontmatter tokens
    python knowledge/tools/check_kb.py --root <kb root> --all
    python knowledge/tools/check_kb.py --strict          # force missing tables up to error (CI full pass)

Exit codes: 0 = no error (warnings do not block); 1 = at least one error; 2 = root directory does not exist.

Checks and error codes

| # | Rule | error code | warning code |
|---|---|---|---|
| 1 | the 8 required fields id/title/domain/status/ver/conf/src/data | E_MISSING_FIELD | — |
| 1 | id is domain.subdomain.three-digits, with 8 fixed domain codes | E_ID_FORMAT | — |
| 1 | id unique across the library | E_ID_DUP | — |
| 1 | status ∈ active/draft/deprecated, conf ∈ S/E/I/U | E_STATUS / E_CONF | — |
| 1 | domain uses the short name {exec,world,combat,unit,camp,mlog,pattern,evidence,data} and maps one-to-one to its directory | E_DOMAIN / E_DOMAIN_DIR | — |
| 2 | all seven template sections present | E_SECTION_MISSING | — |
| 3 | files referenced by frontmatter data: exist under 00-data (supports table.json#key and table.json#id=xxx). **Escalation rule**: once a canonical table appears under 00-data (blocks/turrets/units/items/liquids/bullets/status/rules.json with non-empty records), a missing table becomes E_DATA_FILE (treated as a wrong path); while the data layer is not landed or under --strict, W / E respectively. The rt_* spot-check files do not trigger the landed test | E_DATA_FILE (data layer landed, or --strict) | W_DATA_FILE_MISSING / W_DATA_FRAGMENT / W_DATA_JSON |
| 4 | number-declaration lines carry a source marker ([src: / [measured / [ver / see DATA, etc.); a table or multi-line block immediately preceded by a marked line is exempt as a whole; a table whose header has a "Source/src" column is exempt entirely | — | W_NUM_NO_SOURCE (first 5 per article line by line, the rest summarised) |
| 4 | numbers for "entity name + health/size/range" in an article conflict with 00-data/blocks.json or turrets.json | E_NUM_CONFLICT | — |
| 5 | ver is a list with legal values | E_VER_VALUE | W_VER_SINGLE / W_VER_MANY |
| 6 | relative links resolve | E_LINK_DEAD | — |
| 6 | IDs cited in the Related section exist | — | W_REF_UNKNOWN |
| — | article ≤ 250 lines | E_TOO_LONG | — |
| — | at least one counter-example per article (Measurements and counter-examples / Common misconceptions has real content) | — | W_NO_COUNTEREXAMPLE |
| — | tokens deviate from the current body by more than 20% | — | W_TOKENS_STALE / W_TOKENS_MISSING |
| — | 00-data table entries carry id/src/ver, README exists | — | W_DATA_RECORD / W_DATA_README |
| — | src entries look like path:line or jar: | — | W_SRC_FORMAT |
| — | duplicate titles | — | W_TITLE_DUP |
| — | domain directory exists and holds articles | — | W_DOMAIN_DIR_MISSING / W_DOMAIN_EMPTY |

The gate scans only *.md under the 01..08 domain directories; root contract documents (KB.md / CONVENTIONS.md / VERSION.md / README.md) are not involved.
The number check skips lines inside fenced code blocks (numbers in mlog samples are not declarations).

## 3. Rebuild the retrieval library kb.sqlite3

    python tools/kb.py build       # needs out/_kblibs311(py<3.12) or out/_kblibs, plus out/_kbmodels
    python tools/kb.py stats
    python tools/kb.py search "conveyor items/s" -k 6
    python tools/kb.py serve       # MCP(stdio), exposes kb_search

Corpus = the original fixed document list (README, Logic/, mindustry-blueprint/, the assertion table and verification record (断言表 / 验证记录), and so on)
+ (docs/游戏速查/*.md) + tools/*.py + tests/run_tests.py
**+ the whole knowledge/ library**: knowledge/**/*.md articles, entry summaries from knowledge/00-data/*.json, KB.md/CONVENTIONS.md/VERSION.md.

### Wiring (important)

tools/kb.py in the repo must be replaced with the knowledge-aware version (this directory's kb.py is that version, and kb.diff is the full diff against the old one):

    copy knowledge\tools\kb.py   tools\kb.py
    copy knowledge\tools\kb.diff (archive copy, optional)

Then rebuild the DB (build deletes the old library first, so **back it up before rebuilding**: out/_kb/kb.sqlite3 → kb.sqlite3.bak):

    copy out\_kb\kb.sqlite3 out\_kb\kb.sqlite3.bak
    python tools\kb.py build
    python tools\kb.py stats          # chunks / files / data_tables

On the MCP side (mcp__kb__kb_search) the profile's mcp config starts python tools/kb.py serve; every query opens a fresh sqlite connection,
so **no service restart is needed after a DB rebuild** as long as the process uses the same out/_kb/kb.sqlite3.

### Environment variables

| Variable | Default | Purpose |
|---|---|---|
| KB_ROOT | the script's parent directory | repository root (decides DOC_FILES/CODE_GLOBS/path prefixes); used to trial-run outside the repo |
| KB_KNOWLEDGE | <KB_ROOT>/knowledge | knowledge root (articles + 00-data) |
| KB_DIR | <KB_ROOT>/out/_kb | sqlite output directory |
| KB_LIBS | out/_kblibs311 (when py<3.12) else out/_kblibs | fastembed/numpy directory |
| KB_MODELS | out/_kbmodels | bge-small-zh-v1.5 / bge-reranker-base weight cache |

Changes against the old version: DOC_FILES gains 3 contract documents; new _knowledge_files() (recurses knowledge/**/*.md, excluding tools/ and 00-data/),
_data_summaries() (compresses each 00-data record to one line, ingested with kind=data), _rel() (paths normalised to repo-relative);
--kind gains data; stats gains data_tables; new KB_ROOT/KB_KNOWLEDGE environment variables (default behaviour matches the old version).
The embedding, RRF fusion and MCP protocol logic are unchanged.

## 4. Number audit (article vs 00-data)

    python knowledge/tools/num_audit.py --root <kb root> [--out report.md] [--json]
    python knowledge/tools/check_kb.py --audit --audit-out <report.md>   # run once after the gate

Read-only, it never edits articles, and prints one row per finding: "file:line | field | article value | table value | deviation | verdict | suggestion".
Verdicts: A_MATCH (within ±0.51 or ±2%) / A_MISMATCH / A_SUSPECT (a 60x reload-class gap).
Covers health/size/armor/range/reload/speed/itemCapacity for blocks+turrets+units; a missing field is skipped.
Looked up jointly by (blocks+turrets): a turret's range/reload live only in turrets.json.
Five classes of false positive are filtered out: entity word boundaries (avoiding production→duct), a number must directly follow its label and come after the entity, component-field prefixes (`SuppressionField range 200`), bullet speed ("projectile speed"), **declared vs resulting value** (`container` declares scaledHealth 55 ⇒ 220) and **source-anchor citations** (`world/Block.java:75 public int itemCapacity = 10;`). Currently 51 articles: 24 lines hit, A_MATCH=24 / A_MISMATCH=0.

## 5. Publish the production library (MCP is using it, so no in-place build)

See REBUILD.md: staging build → publish_db.py (sqlite backup, no unlink) → dbstat/check_kb/index --check verification.

## 6. Retrieval smoke test

    python knowledge/tools/bench20.py --db <kb.sqlite3> --out _report/bench20.md   # fixed 20 questions, see below
    python knowledge/tools/postpublish.py --db <production db> --staging <staging db>         # one-command check after publishing
    python knowledge/tools/smoke_kb.py --questions q.jsonl --out _report/smoke.md [--k 6] [--db <kb.sqlite3>]
    # question line format: {"q":"armor damage reduction formula","expect":["C05"]}  or plain text, one question per line
Outputs top1/top3/topk hit rates, per-question p50/p90 latency (the model is warmed up once), and the misses in detail; hits are counted after deduplicating by **distinct file**.

## 3b. Policy for number-source warnings (settled 2026-11-08)

- **W_NUM_NO_SOURCE is advisory and does not block publishing**: per CONVENTIONS rule 1 the author self-certifies, an exit 0 from the gate means pass, and the wrap-up/release report just notes "advisory-level warnings exist".
- The real scale is larger than the report: the 120 reported entries are the folded figure of "first 5 per article + another N lines", which expands to ≈**382 lines**, and the line-by-line full count (skipping tables/code blocks) is **1024 lines**; the bulk is source line numbers and example values, so **do not backfill [src:] line by line**.
- To cut the noise, add the "## Numbers" and "## Rules / formulas" sections (≈46 lines) and give tables a "Source" column (check_kb exempts any table with a source column entirely).

**Weighted evidence (a deterministic 20-question sample, question set frozen)**: after knowledge/ articles ×1.25 and tools//tests/ ×0.8 (applied at query time in kb.py, switchable off with KB_KNOWLEDGE_BOOST / KB_CODE_PENALTY), anchor-A top1 went **9/20 → 14/20 (45% → 70%)**, top3 12→15, and **top1 landing outside knowledge/ 10/20 → 1/20**, with p50 unchanged (~230ms). This is the combined payoff of the two variables "articles doubled + path weighting", and it is fixed in kb.py as the release baseline.

## Common pitfalls

- If build_index.py --check reports "stale", look at the diff first: usually there really is a new article; the timestamp is already excluded, so a re-run does not produce false alarms.
- On an empty library (no articles yet) the gate exits 0 with only warnings such as W_DOMAIN_EMPTY / W_DATA_README — that is designed behaviour, not a missed check.
- An article's domain: uses the short name (world) and must match its directory (02-world → world), otherwise E_DOMAIN / E_DOMAIN_DIR.
- Do not turn on --strict while the library is half-built: with 00-data not yet generated, data references lack files and are only downgraded to W_DATA_FILE_MISSING by default; once a canonical table lands, a missing table automatically becomes E_DATA_FILE.
- Read all JSON / md with encoding="utf-8-sig": PowerShell 5.1's Set-Content -Encoding UTF8 writes a BOM, and parsing it as plain utf-8 raises "Unexpected UTF-8 BOM".
- E_NUM_CONFLICT is a coarse check: it only covers health/size/range for blocks/turrets, requires the entity name and the label on the same line within <40 characters, and does not judge numbers in prose.
- Run --write-tokens once after writing an article, otherwise W_TOKENS_MISSING; tokens is an estimate (0.62 per CJK character + 0.75 per English word), not the tokenizer's true value.
- When a path contains Chinese, do not pass the Chinese directory to python as a command-line argument (the GBK console yields can't open file); use an ASCII path with --root or cd first.
- W_NUM_NO_SOURCE reports only 5 lines + 1 summary per article, and **the true count is far larger than the reported count**: measured, 37 articles reported 120 entries, which is 382 lines after expanding "another N lines", and 1024 lines under the line-by-line full count (skipping tables/code blocks). To decide "should sources be backfilled everywhere", read _report/warn_policy_advice.md instead of estimating effort from 120.
- Citing a component parameter in an article (`navanax（SuppressionField range 200）`) is not a unit attribute and num_audit already filters it; the gate's E_NUM_CONFLICT does no such filtering, so on a false positive check whether that spelling was hit.
