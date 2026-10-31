# Mlog 辅助：把 Python 后端改成 JS 的成本评估

> 结论先说：**能改，但它是「重写核心校验器」，不是「换个语言」。** 现在 Python 后端 5,640 行里
> 2,388 行是静态检查器（`tools/mlogcheck.py`），它同时是 `gate.py` 十七步门禁的母本、1401 个
> `.mlog` 语料和 833 个 `.msch` 蓝图语料的唯一裁判。把这份东西搬进游戏内的 Rhino，
> 代价是**两份实现长期并存 + 一套 parity 回归**，估 **3000–3500 行 JS**、
> **14–20 个工作日**（一个人、按现在的节奏），而且**不会让门禁变简单**——门禁仍然要跑 Python 那份。
>
> 所以：v0.13.1 已经把「玩家要装 Python」这件事消掉了（随包 `logicd.exe` + 模组自己拉起）。
> JS 移植只在一种情况下值得做：**你要的是「连 exe 都没有、模组自带全部能力」的形态**，
> 并且愿意接受两份实现。下面是把这件事拆开之后的账。

## 1. 现在到底是什么在跑

```
游戏进程（Mindustry + Rhino）
  MlogAuxiliary/scripts/main.js   3,930 行   F3 框选、描述框、作业面板、写入/撤销、聊天播报、自动拉起后端
  MlogAuxiliary/scripts/quickcheck.js + rules.generated.js   游戏内快检（RULES 表 + 单条语句检查）
        │  原始 socket（断言表要求，不许用 URL.openConnection）
        ▼
本机 sidecar 进程（Python 3.11，只用标准库）
  tools/logicd.py        1,444 行   HTTP 服务、区域快照处理、作业队列、LLM 转发、健康检查
  tools/mlogcheck.py     2,388 行   静态检查器：分词、跳转图、变量可达、链接槽、成本、跨处理器
  tools/msch.py            553 行   .msch 蓝图解析/组装
  tools/mlogprovider.py    544 行   OpenAI 兼容 provider、重试、预算
  tools/jobqueue.py        614 行   作业队列、持久化、重试
  tools/rule_ids.py         97 行   规则 id 表
        │  HTTPS
        ▼
外部大模型 API
```

数据表（**不用移植，可以原样搬进模组**）：

| 文件 | 大小 | 谁在用 |
| --- | --- | --- |
| `tools/instr_semantics.json` | 57,875 B | 指令参数语义（mlogcheck 主表） |
| `tools/sensor_attrs.json` | 13,920 B | 传感器属性表 |
| `tools/content_names.json` | 12,209 B | 内容名（方块/物品/单位） |
| `tools/block_sizes.json` | 9,644 B | 方块尺寸 |
| `tools/status_names.json` | 913 B | 状态效果名 |
| `rules/*.json` | 40 个，约 48 KB | 检查规则文案与判据 |

合计约 **143 KB**，塞进模组包没有压力（现在模组本身不到 300 KB）。

## 2. 为什么「换个运行时」不算解法

三条路都试算过：

| 路线 | 玩家要装什么 | 结论 |
| --- | --- | --- |
| 现状（v0.13.0）：`python tools/logicd.py` | Python 3 + 手动开窗口 | 已废弃 |
| v0.13.1：随包 `logicd.exe` + 模组拉起 | **什么都不用装** | 已落地，17/17 门禁通过 |
| 换成 Node/Deno 后端 | 还要装 Node | 只是把 Python 换成 Node，问题不变 |
| 全搬进游戏内 Rhino | 什么都不用装，**连 exe 都没有** | 真正的零依赖，但要重写校验器 |

所以真正值得讨论的只有最后一格。它省掉的是「一个 2.2 MB 的 exe 和一次进程启动」，
换来的是「两份校验器 + 一套 parity 回归」。

## 3. 逐模块移植账

| 模块 | Python 行数 | 估 JS 行数 | 难点 | 风险 |
| --- | --- | --- | --- | --- |
| `logicd.py` | 1,444 | ~250 | HTTP 服务层整段消失（模组里 `httpJson` 已经在用）；剩下是路由分派、区域快照处理、`/health` 版本协商 | 低 |
| `mlogcheck.py` | 2,388 | ~1,900 | 分词器、跳转图、变量可达性、链接槽、成本估算、跨处理器分析，全要逐条对齐 findings 的 code/line/severity | **高** |
| `msch.py` | 553 | ~450 | 蓝图 zlib 解压/组装（Rhino 里能拿 `java.util.zip.Inflater`，比 Node 还方便） | 中 |
| `mlogprovider.py` | 544 | ~350 | HTTP POST + JSON、`finish_reason=length` 预算重试、reasoning 抽取 | 中（模组已有 socket 传输，但 LLM 侧要新写） |
| `jobqueue.py` | 614 | ~250 | 队列状态机可以砍掉一半：进程内没有「重启后恢复」的强需求，落盘恢复可选 | 低 |
| `rule_ids.py` | 97 | ~40 | 纯查表 | 低 |
| **合计** | **5,640** | **~3,240** | | |

外加：数据表搬进模组（0 行代码，打包 +143 KB）、`rules.generated.js` 与 Python `rules/*.json`
的对齐（现在已经是「同一份规则的两种投影」，搬完要保证 findings 一字不差）。

## 4. 六个真风险（前两个已经踩过）

1. **Rhino 的正则不是 JS 的正则。** 真 v160.7 里 `String.prototype.split` 传带 `+` 量词的正则
   会等价于空匹配——这正是模组里所有扫描都手写、`tests/mlogauxiliary/run_rhino_parity.py` 守着
   的原因。Python 的 `re` 语义（`\b`、贪婪、回溯）不能直接照抄成 JS 正则，得逐条验。
   还踩过一次更狠的：**正则字面量的 codegen bug 让整段 `main.js` 静默不执行**。
2. **Rhino 缺 ES6 的一半。** 没有 `Map`/`Set`/`Promise`/`async`/生成器/`dict` 推导；
   模组现有代码全是 `var` + 手写循环 + 回调，这个风格得延续下去，不能照抄 Python 的迭代器写法。
3. **性能要实测，不能估。** `mlogcheck.analyse` 在 CPython 里对单条程序是毫秒级；
   Rhino 解释执行大概慢 3–10 倍。1401 个 `.mlog` 语料全跑一遍，Python 约 20 s，
   Rhino 可能 1–3 分钟——**如果只是单条检查（框选 5–20 台处理器），完全够用**；
   但如果想把「全图 200 台处理器巡检」也搬进来，就会卡帧，得放到后台线程 + 分帧。
4. **进程生命周期变了。** 现在 sidecar 独立于游戏，游戏退了作业还在跑；搬进 Rhino 之后
   作业跟着游戏进程走。要接受「退出游戏 = 作业中断」，或者把队列继续落盘（`out/jobs/*.json`）做恢复。
5. **两份实现会漂移。** Python 那份是 `gate.py` 十七步的母本，也是 `docs/断言表.md` 里
   L1/L2 断言的依据。两份并存意味着：任何规则改动要改两遍，并且必须有一套
   「同一输入 → 同一 findings」的 parity 回归（现成的语料：`logic-corpus/` 1,427 个 `.mlog`
   + 833 个 `.msch`，门禁的 `corpus` 步还会从 44k 程序的外部语料抽样 400 条）。
6. **API 密钥的位置变了。** 现在密钥在模组 `Core.settings` 里存、推给 sidecar 进程内存；
   搬进 Rhino 之后密钥直接进游戏进程，并且 HTTPS 请求要自己拼（模组传输层现在是原始 socket，
   因为 Rhino 调 `URL.openConnection()` 会 `IllegalAccessException`）。TLS 得用
   `javax.net.ssl.SSLSocketFactory` 包一层，这块是新的工作量。

## 5. 三档方案

| 方案 | 做什么 | 玩家要装什么 | 工作量 | 门禁 |
| --- | --- | --- | --- | --- |
| **A（当前）** v0.13.1 | 随包 exe + 模组自动拉起 | 什么都不用装 | 已完成 | 17/17 |
| **B 混合** | 只把 `mlogcheck` + `msch` + `rule_ids` 搬进 Rhino（快检与预览变本地），LLM 与队列仍走 exe | 什么都不用装 | 8–11 人日 | 需新增 parity 步 |
| **C 全搬** | 六个模块全进 Rhino，模组自带全部能力 | 什么都不用装，无 exe | 14–20 人日 | 需新增 parity 步 + 保留 Python 母本 |

方案 B 的实际收益是：**点开面板看到检查结论不再依赖后端在线**（现在后端没起来，面板只显示
「连不上 sidecar」）。但玩家视角的差别很小——v0.13.1 已经把「后端没起来」这件事变得几乎不会发生。

## 6. 如果要做，按这个顺序

1. **先做 parity 骨架**（1–2 人日）：把 `logic-corpus/` 的 1,427 + 833 个文件做成
   「输入 → 期望 findings」的金标准，Python 侧先冻结一份基线 JSON。没有这个，后面每一步都在盲改。
2. **搬 `mlogcheck` 的分词与单语句检查**（3–4 人日）：这是体量最大、最容易出偏差的部分；
   与模组里已有的 `quickcheck.js` 会重叠，优先合并而不是并存。
3. **搬跳转图与可达性、链接槽、成本**（3–4 人日）：`jump`/`counter`/`cost` 三块，逐条对齐 findings。
4. **搬 `msch` + `rule_ids`**（2 人日）：蓝图解析在 Rhino 里反而比 Node 省事（`java.util.zip`）。
5. **接 LLM 与队列**（3–5 人日）：`mlogprovider` 的预算重试逻辑要原样搬（`finish_reason=length`
   → 4× 预算重试一次，这条是有真机作业证据的），HTTPS 走 `SSLSocketFactory`。
6. **收尾**（1–2 人日）：把 `gate.py` 加一步 `js-parity`，断言表补 L2 条目，README/规划同步。

## 7. 建议

- **短期不需要做。** v0.13.1 之后「即装即用」已经成立：解压 → 双击 `安装.bat` → 按 F3，
  模组自己把后端拉起来，玩家不需要 Python、不需要命令行窗口。
- **中期想要「连 exe 都没有」再上方案 B。** B 的收益（面板不依赖后端）比 C 的收益（省一个 exe）
  更真实，成本只有 C 的一半多一点。
- **无论哪个方案，Python 那份都不能删。** 它是 `gate.py` 的母本、断言表的依据、以及
  「游戏内实现和规范不一致时」的裁判。两份实现的关系是「规范 + 实现」，不是「旧 + 新」。

## 8. 这份评估里哪些是估计、哪些是事实

- **事实**：各模块行数（`wc -l`）、数据表大小、语料文件数、模组现有 3,930 行、
  门禁 17 步、v0.13.1 的 exe 实测（onedir 2.2 MB / 100 个文件，`/health` 0.13.1，
  包内 `/analyze` 通过）、`onefile` 在临时目录被策略拦住（`Could not create temporary directory!`）。
- **估计**：JS 行数、人日、Rhino 相对 CPython 的倍数。人日的口径是「一个人、有现成语料做回归、
  不需要重新设计规则」。
