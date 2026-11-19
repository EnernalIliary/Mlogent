# 1.2.3 — 英文母本，中文提问

2026-11-19。这一版只有一件事：知识库的文章正文全部改成英文，同时保证写中文的人
仍然拿得到答案。四个包的分工与 1.2.0 起一致，包内文件路径不变。

## 包

| 包 | 内容 | 大小 | 解压后先看 |
| --- | --- | --- | --- |
| `mlog-agent-1.2.3-toolchain.zip` | `tools/ rules/ data/ tests/ docs/ scenes/ bench/` + `gate.py`、`MANIFEST.repo.sha256`、`README.md`、`CHANGELOG.md`、`LICENSE`、`SECURITY.md` | ~1.35 MB | `README.md` 的「快速开始」 |
| `mlog-agent-1.2.3-knowledge.zip` | `knowledge/`（101 篇文章 + 数据表 + 证据）、`data/game/` | ~1.39 MB | `knowledge/INDEX.en.md`、`knowledge/STYLE-en.md` |
| `mlog-agent-1.2.3-skills.zip` | `.dsh/skills/` 的两个技能包（落在压缩包根） | ~0.61 MB | `mindustry-blueprint/SKILL.md` |
| `mlog-agent-1.2.3-mcp.zip` | `tools/ rules/ data/ deploy/` + `knowledge/` + `docs/MCP部署.md` | ~2.17 MB | `deploy/README.md` |

`SHA256SUMS.txt` 四行，覆盖上面四个 zip。

## 这一版做了什么

**正文全英语化。** 101 篇正文（约 97K 汉字）改成英文，中文只留在三处对照：官方中文名的
括号 gloss（`flare (星辉)`）、名称表的中文列、`GLOSSARY.md` 的生成区。id、断言号、
`file.ext:NN` 锚点、wiki 链接、代码围栏逐字节保留——所以 `claims.jsonl` 的 85 条证据指针
一个都没动。契约是 `knowledge/STYLE-en.md`，守卫是 `knowledge/tools/check_en.py`
（`gate.py` 的 `english` 步，102/102 clean）。

**中文提问到英文语料的桥。** `tools/cjken.py` 读仓库里本来就有的名字表
（`GLOSSARY.md` 的手写黑话段与生成段、`data/game/aliases.json`，618 个中文词 / 1572 个
英文形），把问句里出现的中文名**追加**成英文名——只追加、不改写，最长匹配优先且不重叠。
`kb_grep.py`（MCP 的 `mlog_kb` 走它）与 `kb.py` 默认调用，`MLOG_NO_EXPAND=1` 关闭。

**重新量了一遍。** 同 300 道中文题、英文语料：hybrid hit@1 50.3% / hit@6 81.7%；
只开 dense 时多语言 embedding 领先（44.0% vs 38.7%），一上 hybrid 就打平——稀疏腿本来就
在补语言错配。所以默认仍是 `bge-small-zh`，多语言模型留作 `KB_EMB_MODEL`。数字与复现命令
在 `knowledge/08-evidence/bench/README.md` §12。

## 怎么验一遍

```bash
# 1) 工具链自带测试（不需要 Java，也不需要知识库）
python tests/run_tests.py          # 50/50
python gate.py                     # 该包内：18 PASS / 15 SKIP / 0 FAIL

# 2) 把 knowledge 包的内容解到同一目录后再跑，知识库相关的步会从 SKIP 变 PASS
python gate.py                     # 含知识库时：24 PASS / 9 SKIP / 0 FAIL

# 3) 中文提问能不能命中英文文章
python tools/cjken.py 差扰是什么
python tools/kb_grep.py search "差扰是什么"      # 命中 knowledge/03-combat/turrets/T108-parallax.md
```

## 已知边界

- **中文查询走词面检索时，只有名字能对上。** 问「把 @counter set 成行号会怎样」这类
  机制问题，桥帮不上——`kb_grep` 在英文正文上仍是 0 命中；要语义命中请用 `tools/kb.py`
  （需要 `fastembed` 与模型，不在包里）。
- **题库仍是中文。** 这是刻意的：它衡量「用中文提问能不能拿到英文母本」，也是真实用法；
  配一份英文题库会好看但失真。
- **5 项 SKIP** 是设计：两个模组已拆成同级独立项目；`differential` 需要真开服；
  干净 checkout 无 Java 时仿真类跳过。
