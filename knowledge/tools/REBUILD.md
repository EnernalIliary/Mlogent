# REBUILD.md — 正式库重建与发布（三行命令）

> 适用：把 `knowledge/` 的最新内容重建进 MCP 正在服务的正式库 `<repo>/out/_kb/kb.sqlite3`。
> 正式库被 `mcp__kb__kb_search`（kb.py serve）持有句柄，**不能**直接 `kb.py build`（build 会 unlink，Windows 报 PermissionError [WinError 5]，实测一度把库清成 24KB 空库）。

## 0. 准备（一次性）
```powershell
$R = "F:\OneDrive\桌面\AtomicStates"; $W = "F:\OneDrive\文档\deepseek-harness\default-workspace\kb-stage"
$py = "C:\Users\lliary\AppData\Local\Programs\Python\Python311\python.exe"
$env:KB_ROOT = $R; $env:KB_KNOWLEDGE = "$R\knowledge"
$env:KB_LIBS = "$R\out\_kblibs311"; $env:KB_MODELS = "$R\out\_kbmodels"
```

## 1. 构建到临时目录（不动正式库）
```powershell
$env:KB_DIR = "$W\_kb_build"; & $py "$R\knowledge\tools\kb.py" build
```
预期输出形如 `{"chunks": N, "files": M, "data_tables": 10}`，耗时 50–90s（含 embedding）。

## 2. 发布（sqlite backup，读方无需关闭）
```powershell
& $py "$R\knowledge\tools\publish_db.py" "$W\_kb_build\kb.sqlite3" "$R\out\_kb\kb.sqlite3"
```
预期 `published kb.sqlite3 -> ...\out\_kb\kb.sqlite3  chunks src=N dst=N fts=N`，src==dst 才成功。

## 3. 校验
```powershell
& $py "$R\knowledge\tools\dbstat.py" "$R\out\_kb\kb.sqlite3"
& $py "$R\knowledge\tools\check_kb.py" --root "$R\knowledge" <# 期望 errors=0, exit 0 #>
& $py "$R\knowledge\tools\build_index.py" --root "$R\knowledge" --check
```
MCP 侧冒烟：任意 `kb_search` 调用返回新文章路径（如 `knowledge/03-combat/C05-armor.md`）即生效，无需重启服务。

## 3b. 发布后固定校验顺序（按此顺序跑，任一步失败就回滚）

0. **等 journal 落盘**：`out/_kb\kb.sqlite3-journal` 必须消失，dbstat 能读且 chunks 与 build 输出一致，才允许冒烟（发布瞬间库不可读：mode=ro 会报 `attempt to write a readonly database`，实测 bench20 会全 0 且 p50 3ms，误判成"检索崩了"）。
1. **库体检**（10s）：`dbstat.py <正式库>` → 看 `chunks/files/kinds` 是否与 build 输出一致；**data 块应 >100**，且不应出现 `knowledge/_report/`、`knowledge/_kb/` 路径（工作产物不进口语料）。
2. **索引一致**（2s）：`build_index.py --root "$R\knowledge" --check` → 期望「与库一致」。
3. **门禁全量**（5s）：`check_kb.py --root "$R\knowledge" --all --audit --audit-out <报告>` → 期望 errors=0 / RESULT PASS / exit 0；audit 行数只报告不阻塞。
4. **检索冒烟**（30s）：`bench20.py --db <正式库> --out <报告>` → 20 题固定样本，看 A 锚点 top1/top3/top6、B 答案命中、`top1 落在 knowledge/ 之外` 计数；与上一版对比，A@1 不应下降。

> 回滚：正式库旁保留 `kb.sqlite3.bak`（发布前复制），第 4 步明显变差就 backup 回去再 publish。

## 3c. 一条命令跑完 3b（发布后校验）

```powershell
& $py "$R\knowledge\tools\postpublish.py" --db "$R\out\_kb\kb.sqlite3" --knowledge "$R\knowledge" --staging "$W\_kb_build\kb.sqlite3" --min-a1 12 --out "$W\_report\postpublish.md"
```
三项判定：**STRUCT**（库可读、无 `knowledge/_report/` 等工作产物路径）/ **COUNT**（chunks 与 staging 构建一致）/ **RETRIEVAL**（bench20 A@1 ≥ --min-a1 且 outside_top1 ≤ --max-outside）。
退出码 0 = 无 FAIL（SKIP 不阻塞）；JSON 用 `--json <path>`。只给期望值不传 staging 时用 `--expect-chunks 8094`。

## 常见坑
| 现象 | 原因 | 处理 |
|---|---|---|
| `PermissionError [WinError 5]` on kb.sqlite3 | 原地 build 且 MCP 持有句柄 | 用第 1+2 步的 staging + publish 流程 |
| `attempt to write a readonly database` | 该文件是 OneDrive 占位/被沙箱标只读 | 先整文件读一遍水合；仍失败则停 MCP 进程后再 publish |
| `Unexpected UTF-8 BOM` | PowerShell 5.1 `Set-Content -Encoding UTF8` 写 BOM | 读侧统一 `encoding="utf-8-sig"`（三个脚本已改） |
| 构建后 `data_tables=0` | 00-data 只有 rt_* 抽查件 | 需 canonical 表（blocks/turrets/units/items/liquids/bullets/status/rules） |

## 产物对照
| 文件 | 作用 |
|---|---|
| `knowledge/tools/kb.py` | build / search / serve(MCP kb_search) / stats |
| `knowledge/tools/publish_db.py` | staging → 正式库（backup API） |
| `knowledge/tools/dbstat.py` | 只读库体检（chunks/files/kinds/data） |
| `knowledge/tools/build_index.py` | 生成 knowledge/index.json（--check 比对） |
| `knowledge/tools/check_kb.py` | 静态门禁（--audit 附带数字审计） |
| `knowledge/tools/smoke_kb.py` | N 题检索冒烟（计时 + top1/3/k 命中率） |
| `knowledge/tools/bench20.py` | bench/questions.jsonl 确定性 20 题（**固定行 1,16,31,…,286**，题库冻结勿改），锚点+答案双口径 + outside-knowledge 统计 |
| `knowledge/tools/postpublish.py` | 发布后一条命令校验：dbstat + chunks 比对 + bench20 + 三项 PASS/FAIL |
