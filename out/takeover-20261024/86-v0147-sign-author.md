# 86 · v0.14.7：签名作者名改 `MAI`

## 一句话

签名里的作者名从中文「猪猪鱼」改成 ASCII 的 **MAI**（用户 m07277「那个签名改成MAI吧」）；
顺带把发行包里的模组 README 换成重写版，版本三处升 `0.14.7`。

## 为什么要改（不只是口味问题）

`tools/aigenerated.py` 的 CLI 会 `print(sign(...))` 把签名整行打出去，签名行里带作者名。
作者名是中文时，在 cp1252 之类窄编码控制台上直接 `UnicodeEncodeError: 'charmap' codec can't encode characters`，
进程退出码非 0 —— GitHub `windows-latest` 的默认编码就是 cp1252，于是 CI 首跑
（run 41231288166）里 `tool/aigenerated` 这一条红：`slot_line`/`terminal_line` 全部 expected 0 got 1。

改作者名把这条**根因**去掉，另外两处兜底也保留（`main()` 把 stdout/stderr 切 UTF-8、CI 顶层 `PYTHONUTF8=1`）。

## 改了什么

- `tools/aigenerated.py`：`DEFAULT_AUTHOR = "MAI"`；文件头注释里的示例改成 `"aigenerated:MAI:1f02465d9e75"`。
- `tools/mlog.py`：`--author` 的帮助串改成 `signature author (default: MAI)`。
- 受影响的下游不用改：`tools/jobqueue.py` 与 `tools/logicd.py` 都读 `aigenerated.SIGN_AUTHOR`
  （仍可用 `MAI_SIGN_AUTHOR` 覆盖），签名格式 `jump 0 always 0 "aigenerated:<author>:<12hex>[:<payload>]"` 不变。
- **旧签名仍然有效**：`SIG_RE` 的第 2 组才是哈希，校验只比对它 ⇒ 之前用「猪猪鱼」签过的程序与作业不会失效。
- 版本三处：`MlogAuxiliary/scripts/main.js` 的 `MOD_VERSION`、`MlogAuxiliary/mod.hjson` 的 `version`、
  `tools/logicd.py` 的 `SIDECAR_VERSION` → `0.14.7`。
- 文档：`MlogAuxiliary/README.md` 的签名说明改 `aigenerated:MAI:<12 位哈希>`；新增 `CHANGELOG.md` 的 0.14.7 条目；
  断言表 L2-75（总 134 条）；规划状态表加 v0.14.7 行。

## 验证

| 项 | 结果 |
|---|---|
| `node --check MlogAuxiliary/scripts/main.js` | 0 |
| 窄编码复现 | `$env:PYTHONIOENCODING='cp1252'; python tools/aigenerated.py sign …` → 退出码 0（改前是 `UnicodeEncodeError`） |
| `tests/run_tests.py` | 46/46（`tests/expected.json` 里两条期望签名串跟着换成 `MAI:…`） |
| `tests/logicd/run_logicd_tests.py` | `logicd OK`（protocol 26 / jobs 16 / provider 12 / improve 8 / llm 12 / write path 7 模板） |
| `tests/mlogauxiliary/run_ui_smoke.py` | EXIT=0 |
| `gate.py --full --kb-build` | 17/17 |

## 教训

- 测试里写死的期望串（`tests/expected.json` 的 `slot_line`/`terminal_line`）会钉住签名内容：
  改作者名必须同步改期望，否则 `tool/aigenerated` 一红就是两条哈希对不上。
- `tools/aigenerated.py` 的 `sign` 子命令没有 `-o/--output`（只有 `post` 有），就地改文件、要备份先复制。
- 门禁的 `mirror`/`global` 步会盯 `tools/*.py`：动过 `aigenerated.py` 就要
  `python tools/sync_mlogagent.py --mirror all` 再 `--global`，不然 14/17。
