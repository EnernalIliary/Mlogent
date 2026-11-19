# INDEX_CONTRACT.md — the index contract for knowledge/index.json

> Generator: `knowledge/tools/build_index.py` (single source of truth). This file describes **field semantics**; changing a field means changing this file and the generator first.
> Consumers: MCP pre-routing, the CI gate, and human retrieval. Fields may only be added, never renamed (v1 frozen).

## Top-level fields
| Field | Type | Semantics | Stability |
|---|---|---|---|
| `version` | int | contract version, currently 1 | frozen |
| `generated` | ISO8601 | generation time (dropped when `--check` compares) | changes every run |
| `root` | str | fixed `"knowledge"` (all paths use it as prefix) | frozen |
| `read_order` | [str] | recommended reading order | addable |
| `counts` | obj | summary numbers, see below | addable |
| `domains` | [obj] | the 8 domains, fixed order 01..08 | frozen |
| `data` | [obj] | `00-data/*.json` machine-readable tables | addable |
| `evidence` | [obj] | one entry per file under `08-evidence/` | addable |
| `evidence_dirs` | [obj] | directory summary for `08-evidence/{claims,probes,bench}/` (empty directories appear too) | new in v1.1 |
| `docs` | [obj] | contract documents (KB.md / CONVENTIONS.md / VERSION.md) | addable |
| `notes` | [str] | convention notes (tokens are an estimate, etc.) | addable |

## counts (the single entry point for asking "is the library usable")
```json
{"articles":37, "by_domain":{"01-execution":6,"02-world":5,"03-combat":10,"04-units":1,
  "05-campaign":0,"06-mlog":8,"07-patterns":6,"08-evidence":1},
  "data_tables":10, "data_records":948, "data_raw_tables":7,
  "evidence_files":21, "evidence_by_kind":{"top":6,"bench":15}, "evidence_dirs":2,
  "tokens_total":34073, "empty":false}
```
- `data_tables`/`data_records` **only count tables with kind=canonical**; `rt_*` and `*_raw.json` go into `data_raw_tables`, which are listed but not counted.
- `empty=true` means there are no articles at all (empty-library skeleton). `04-units`/`05-campaign` being 0 is a content gap, not an index error.

## domains[].articles[] — the article's 10 fields
| Field | Meaning |
|---|---|
| `id` | `DOMAIN.SUB.NNN`, same source as frontmatter; an empty string when missing (the gate reports E_MISSING_FIELD) |
| `path` | `knowledge/02-world/W01-xxx.md` (**includes** the knowledge/ prefix, so it can be joined straight onto the repo root) |
| `title` / `domain` / `status` / `conf` | taken from frontmatter; `conf ∈ {S,E,I,U}` |
| `ver` | always an array, e.g. `["v160.7_rt","v159.3_src"]` |
| `tokens` / `tokens_est` | tokens is the frontmatter-backfilled value; `tokens_est=true` means this script estimated it (0.62 per CJK character + 0.75 per English word) |
| `lines` | physical line count (over 250 lines should be split by convention) |

## data[] — 00-data machine-readable tables
```json
{"path":"knowledge/00-data/blocks.json","kind":"canonical","records":447,
 "bytes":311169,"keys":["armor","category","class","health","id","itemCapacity","name","rotate","size","src","ver"]}
```
- `kind`: `canonical` (the formal fact tables: blocks/turrets/units/items/liquids/bullets/status/rules/formulas/src_anchors) | `raw` (`rt_*` reflection spot-check files, **not directly citable as fact**).
- `records` supports two top-level shapes: an array, or `{records|items|entries|rows|data:[...]}`; any other dict is treated as a "value → record" map.
- `keys` is the union of fields across the first 2000 records of that table (at most 40), used to answer "what can this table be queried for"; it is not guaranteed complete.
- Numbers inside records are uniformly `{v, unit}` (the "00-data convention" in CONVENTIONS); the index does not expand unit.

## evidence[] / evidence_dirs[] — the evidence layer
- `evidence[]` per file: `{path, kind, bytes, desc}` plus `lines` for `.jsonl` and `entries` for `.json`.
- `evidence_dirs[]`: `{path, kind, desc, files, bytes}`, with `kind ∈ {claims, probes, bench}`.
- **probes/** currently has 0 files (the directory exists) — probe scripts appear automatically once landed; the evidence layer counts as usable only when `files`>0.
- `claims.jsonl` holds one re-testable assertion per line; `claims-excluded.jsonl` holds the excluded items (also counted, do not mix them up).

## Usage examples
1. **Routing**: read `counts.by_domain` first to see which domain has content; then pick the articles to load by `domains[].articles[].tokens`, avoiding stuffing the whole library into the context.
2. **Looking up a value**: if a number in an article is marked `see DATA#blocks`, locate the table via `data[]` → read that table's `#fragment` (`#id=duo`).
3. **Gate**: `build_index.py --check` exits 1 = index.json is stale (compared after dropping `generated`); in CI it runs serially with `check_kb.py`.
4. **MCP**: retrieval goes through kb.py (FTS + vectors); index.json only provides navigation and counts and takes no part in similarity.

## Division of labour with the gate
| Concern | check_kb.py | build_index.py |
|---|---|---|
| frontmatter completeness / seven sections / source markers | ✅ per article | ❌ |
| numbers conflicting with 00-data | ✅ `--audit` (num_audit.py) | ❌ |
| whole-library overview / counts / navigation | ❌ | ✅ |
| 00-data records and keys | validates data: references only | ✅ summarised |
