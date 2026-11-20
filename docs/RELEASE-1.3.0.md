# 1.3.0 — 2026-11-20

这一版没有新工具，改的是"工具从哪里来、能不能被单独验证"。世界后端从单文件
拆成 18 个模块，技能载荷不再入库而是在构建时生成，并修掉两条只在 CI 的
Windows runner 上才会出现的 bug。

## 四个包

| 包 | 大小 | 文件数 | 里面是什么 |
| --- | --- | --- | --- |
| `toolchain` | 1.41 MB | ~300 | `tools/ rules/ data/ tests/ docs/ scenes/ bench/`、`gate.py`、`README`、`CHANGELOG`、`LICENSE`、`SECURITY`、`MANIFEST.repo.sha256` |
| `knowledge` | 1.39 MB | ~390 | `knowledge/`（101 篇英文正文 + 12 张数据表 + 证据）+ `data/game/` |
| `skills` | 1.59 MB | ~330 | `mlog-agentskill/` 与 `mindustry-blueprint/` 两个技能包（含生成的 `tools/`） |
| `mcp` | 2.14 MB | ~540 | `tools/ rules/ data/ deploy/ knowledge/`，`mlog_mcp_http.py` 与 `docs/MCP部署.md` |

解压后先看：`README.md`（入口）、`docs/README.md`（docs 与 knowledge 的分工）、
`knowledge/INDEX.en.md`（86 篇文章的英文标题）、`knowledge/GLOSSARY.md`（中文名 →
英文 id，也是 `mlog_kb` 的词表）。

## 这一版做了什么

- **世界后端模块化**：`tools/world_server.py` 164 KB → 29.7 KB，拆成 18 个
  `world_*.py`；契约测试 0 → 84 项（16 个 `tests/world/run_*_tests.py`），
  `gate.py` 总步数 34 → 54。
- **技能载荷构建时生成**（−75 760 行入库副本）：`.dsh/skills/*/tools` 与
  `mindustry-blueprint/tools` 不再跟踪，`tools/build_skills.py` 负责生成与自检。
  因此 `skills` 包比 1.2.3 大（0.62 → 1.59 MB，每个技能下 113 个 tool 文件）——
  这是"生成物随包走、仓库不存副本"的必然结果。
- **投影槽位**（`a5adac3`）：重新 arm feed 时清掉旧槽位的建筑。
- **两条 CI bug**：Windows 8.3 短名让 `WorldPaths` 的路径断言失败；`-I` 隐含
  `-E` 让编码环境变量失效，cp1252 控制台上中文告警变成 `UnicodeEncodeError`。
- `.dockerignore`、CI 工作流精简、`dsh-preset-mlog/sync_blueprint_docs.py`。

## 验一遍

```bash
# 1. toolchain 单包：测试与门禁（Java/知识库不在包里，相关步骤会 SKIP）
python tests/run_tests.py          # 50/50
python gate.py                     # 37 PASS / 16 SKIP / 1 WARN(无 kb 索引), 退出码 0

# 2. 叠上知识库后，知识相关的六步转为实跑
unzip -o ../mlog-agent-1.3.0-knowledge.zip -d .
for s in bundles glossary english claims kbgrep cjken; do python gate.py --only $s; done

# 3. mcp 包：16 个工具，且能读包内知识库
python -c "import sys;sys.path.insert(0,'tools');import mlog_mcp as m;print(len(m.TOOLS))"

# 4. skills 包：两个技能独立可用
python mlog-agentskill/tools/mlogagent.py info --verify
```

## 已知边界

- 完整联机验收（投影、多槽交互、门、显示）仍需真游戏客户端；`docs/World后端重构计划.md`
  把已测与未测分开写了。
- 知识库索引不入包：`python tools/kb.py build` 需要 `fastembed`，MCP 侧用
  `mlog_kb`（纯词面，读 `knowledge/**/*.md`）不需要索引也不需要模型。
- 中文机制问题打不中英文正文时，先过 `GLOSSARY.md` 或 `tools/cjken.py` 的名字桥。
- 5 个 SKIP 是设计内：两个模组（`MlogAuxiliary`、`GriefToBan`）已拆成同级独立项目；
  `mindcode`/`scenario`/`modifier`/`differential` 在缺 JVM 或缺活世界时跳过。
