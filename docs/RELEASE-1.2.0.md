# Mlogent 1.2.0 — 2026-11-18

工具链从「静态分析 + 真执行器」扩成「编译前端 → 场景实验 → 与活世界对账 → 可复现评测」的一条链，
并且每一环都由 `gate.py` 的一步盯着。这一版按**三个包**发布，因为三类人只要其中一部分。

## 包里有什么

| 包 | 大小 | 内容 | 先跑这条 |
|---|---|---|---|
| `mlog-agent-1.2.0-toolchain.zip` | 1.3 MB | `tools/`、`rules/`、`data/`、`tests/`、`docs/`、`bench/`、`gate.py`（297 个文件） | `python gate.py` |
| `mlog-agent-1.2.0-knowledge.zip` | 1.35 MB | `knowledge/`（133 篇 md + 12 张数据表 + 85 条 claim 证据）+ `data/game/`（388 个文件） | `python tools/kb.py build` |
| `mlog-agent-1.2.0-skills.zip` | 0.6 MB | 两份可直接放进 `~/.dsh/skills/` 的技能包（77 个文件） | 拷进去即可 |

`SHA256SUMS.txt` 逐包给 sha256，`PACKAGE.txt` 在包内说明这个包负责什么。

**不打包**：蓝图语料 `logic-corpus/`（12.8 MB）、随仓库的 `Mindustry-Source/` 与 `Arc-Source/`、
Mindustry 服务端 jar 与 JRE（150 MB 级，且许可是别人的）、私人调试地图与笔记。

## 这一版新做的

**编译前端**：`mindcode_compile` 把 `.mnd` 编成 mlog，失败按 `compilation_error` /
`unsupported_environment` 分开归因，带 `file/line/col`。基线钉在 Mindcode 3.19.3 —— 3.21.0 在本机
每次真编译都会死锁（`UpdateChecker` → `dev.dirs` → PowerShell 子进程管道互锁，线程栈与源码行号
都记在 `docs/Mindcode集成.md` 里）。另有源码映射（指令 ↔ 语句，前缀编译对齐）与增量记忆
（25 条语句 17.4 s → 0.14 s）。

**判定信封**：每个结果都带 `ok / failure_type / levels / task / artifacts`，四个成功维度
（execution / static / simulation / real runtime）分别记 `true/false/null`，`null` 是「没跑过」而
不是「通过了」。`mlog_validate` 把编译 → 静态 → 仿真 → 断言串成一次调用；`mlog_task` 记住
「上一轮到哪一步停了」，源码一改旧进度降级成 stale。

**场景实验**：schema v2 加 8 类扰动（单位移动/生成/死亡、控制权竞争、建筑增删、资源压力、
时间压力、世界改动），按 `at_tick` 稳定排序；`generate --seed` 参数化生成；`explore` 跑一批
变体并用 ddmin 把失败缩到最小扰动集。

**与活世界对账**：同一个场景既能在离线执行器跑、也能铺进真实世界跑，两侧观测统一成
`mlog-observation/v1` 再逐字段比。差异要么被已知保真度边界解释（`tick-model` / `unit-motion`），
要么原样列出——实测一次 240 tick 的对照：5 处差异、0 处解释不掉。

**评测**：6 个确定性任务、三种判据（观测状态 / 真执行过的指令 / 静态干净），首批 6 次运行
success 6/6、first-pass 4/6，账本入库在 `bench/results/runs.jsonl`。

**知识库**：新增 Mindcode 集成与语法两篇（M09、M10），85 条 claim 的证据指针从行号改成
`file#ID` 锚点（迁移时发现其中 89 个早就指错了行）；游戏语言包入库存进 `data/game/bundles/`，
生成器不再依赖仓库外的素材树。

## 用这条命令验一遍

```bash
unzip mlog-agent-1.2.0-toolchain.zip -d mlog && cd mlog
python gate.py        # 16 PASS / 11 SKIP（Java 与知识库不在包里）/ 0 FAIL
```

把知识库包解到同一目录，`claims` 与 `bundles` 两步也会跑起来（28 步全量需要 Java 21+ 与服务端 jar）。

## 已知边界

执行器的循环行为不确定，所以 `executed` 判据只能当下限；投影贴图只能眼看；增量编译只覆盖源码映射；
`skipped` 的 11 步里有 5 步因为模组已是独立仓库、3 步因为包内没有 Java/JRE。
