# REBUILD.md — production library rebuild and publish (three lines of commands)

> Applies to: rebuilding the latest content of `knowledge/` into the production library `<repo>/out/_kb/kb.sqlite3` that MCP is currently serving.
> The production library holds a handle via `mcp__kb__kb_search` (kb.py serve), so `kb.py build` **cannot** be run in place (build unlinks the file; Windows raises PermissionError [WinError 5], and measured once it wiped the library down to a 24KB empty DB).

## 0. Preparation (one-time)
```powershell
$R = "<仓库根>"; $W = "<临时暂存目录>"   # 仓库根为本机仓库绝对路径；$W 为任意本地目录，脚本按参数/环境变量取
$py = "C:\Users\lliary\AppData\Local\Programs\Python\Python311\python.exe"
$env:KB_ROOT = $R; $env:KB_KNOWLEDGE = "$R\knowledge"
$env:KB_LIBS = "$R\out\_kblibs311"; $env:KB_MODELS = "$R\out\_kbmodels"
```

## 1. Build into a temporary directory (production library untouched)
```powershell
$env:KB_DIR = "$W\_kb_build"; & $py "$R\knowledge\tools\kb.py" build
```
Expected output looks like `{"chunks": N, "files": M, "data_tables": 10}`, taking 50–90s (embedding included).

## 2. Publish (sqlite backup, readers need not be closed)
```powershell
& $py "$R\knowledge\tools\publish_db.py" "$W\_kb_build\kb.sqlite3" "$R\out\_kb\kb.sqlite3"
```
Expected `published kb.sqlite3 -> ...\out\_kb\kb.sqlite3  chunks src=N dst=N fts=N`; it succeeded only if src==dst.

## 3. Verification
```powershell
& $py "$R\knowledge\tools\dbstat.py" "$R\out\_kb\kb.sqlite3"
& $py "$R\knowledge\tools\check_kb.py" --root "$R\knowledge" <# 期望 errors=0, exit 0 #>
& $py "$R\knowledge\tools\build_index.py" --root "$R\knowledge" --check
```
MCP-side smoke test: any `kb_search` call returning new article paths (e.g. `knowledge/03-combat/C05-armor.md`) means it took effect; no service restart needed.

## 3b. Fixed post-publish verification order (run in this order; roll back if any step fails)

0. **Wait for the journal to hit disk**: `out/_kb\kb.sqlite3-journal` must disappear, and dbstat must be readable with chunks matching the build output, before the smoke test is allowed (for an instant after publishing the library is unreadable: mode=ro raises `attempt to write a readonly database`, and measured bench20 then returns all 0 with p50 3ms, misjudged as "retrieval broke").
1. **Database health check** (10s): `dbstat.py <production db>` → check whether `chunks/files/kinds` match the build output; **the data blocks should be >100**, and paths like `knowledge/_report/` or `knowledge/_kb/` must not appear (work products do not enter the corpus).
2. **Index consistency** (2s): `build_index.py --root "$R\knowledge" --check` → expect "consistent with the library".
3. **Full gate** (5s): `check_kb.py --root "$R\knowledge" --all --audit --audit-out <report>` → expect errors=0 / RESULT PASS / exit 0; audit line counts are reported but do not block.
4. **Retrieval smoke test** (30s): `bench20.py --db <production db> --out <report>` → the 20-question fixed sample; check anchor-A top1/top3/top6, B answer hits, and the `top1 falls outside knowledge/` count; compare with the previous version, and A@1 must not drop.

> Rollback: keep a `kb.sqlite3.bak` beside the production library (copied before publishing); if step 4 degrades noticeably, copy the backup back and publish again.

## 3c. Run all of 3b with one command (post-publish verification)

> Step 0 must be done first to set `KB_ROOT/KB_KNOWLEDGE/KB_LIBS/KB_MODELS`; otherwise bench20 reports `no index yet: python tools/kb.py build` (in reality only the model/library path is missing, and the library itself is fine).

```powershell
& $py "$R\knowledge\tools\postpublish.py" --db "$R\out\_kb\kb.sqlite3" --knowledge "$R\knowledge" --staging "$W\_kb_build\kb.sqlite3" --min-a1 12 --out "$W\_report\postpublish.md"
```
Three verdicts: **STRUCT** (library readable, no work-product paths such as `knowledge/_report/`) / **COUNT** (chunks match the staging build) / **RETRIEVAL** (bench20 A@1 ≥ --min-a1 and outside_top1 ≤ --max-outside).
Exit code 0 = no FAIL (SKIP does not block); use `--json <path>` for JSON. When only an expected value is given without staging, use `--expect-chunks 8094`.

## Common pitfalls
| Symptom | Cause | Handling |
|---|---|---|
| `PermissionError [WinError 5]` on kb.sqlite3 | in-place build while MCP holds a handle | use the staging + publish flow of steps 1+2 |
| `attempt to write a readonly database` | the file is a OneDrive placeholder / flagged read-only by the sandbox | read the whole file once to hydrate it first; if that still fails, stop the MCP process before publishing |
| `Unexpected UTF-8 BOM` | PowerShell 5.1 `Set-Content -Encoding UTF8` writes a BOM | readers always use `encoding="utf-8-sig"` (the three scripts have been changed) |
| `data_tables=0` after building | 00-data holds only the rt_* spot-check files | canonical tables are required (blocks/turrets/units/items/liquids/bullets/status/rules) |

## Artifact map
| File | Role |
|---|---|
| `knowledge/tools/kb.py` | build / search / serve(MCP kb_search) / stats |
| `knowledge/tools/publish_db.py` | staging → production library (backup API) |
| `knowledge/tools/dbstat.py` | read-only database health check (chunks/files/kinds/data) |
| `knowledge/tools/build_index.py` | generates knowledge/index.json (--check compares) |
| `knowledge/tools/check_kb.py` | static gate (--audit adds the number audit) |
| `knowledge/tools/smoke_kb.py` | N-question retrieval smoke test (timing + top1/3/k hit rate) |
| `knowledge/tools/bench20.py` | bench/questions.jsonl deterministic 20 questions (**fixed rows 1,16,31,…,286**, question set frozen, do not edit), anchor + answer dual scoring plus outside-knowledge stats |
| `knowledge/tools/postpublish.py` | one-command post-publish verification: dbstat + chunks comparison + bench20 + three PASS/FAIL verdicts |
