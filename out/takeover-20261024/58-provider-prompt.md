# 58 · P4 第三刀：真 provider 的接缝 + §4.4 三段 prompt

日期：2026-10-30　　玩家指令（逐字）：**「做1，直接整个去掉f4的热键，不用保留。然后做2」**（第 3 条 = 真 provider）

## 1. 目标与边界

规划 §4.3/§4.4 要求「生成」有两档（锚定模板 / 自由写码）、prompt 分三段（世界事实 / 规则摘要 / 任务与 JSON 契约），
并要求 self-repair 把上一轮的 findings 回给模型。这一刀把**接缝**做出来：队列本身仍然离线，
模型只是 `provider` 这个可换的 callable；能不能真连、连哪家，全由命令行决定。

## 2. 新增 tools/mlogprovider.py

| 部件 | 作用 |
| --- | --- |
| `build_prompt(job, hint=None)` | §4.4 三段。世界事实 = 处理器坐标（链接坐标是相对的）+ 快照摘要（bounds / cells / 附近方块 Top8 / 其他处理器数 / 地图名）+ **链接名白名单**；`links is None` 写 `UNKNOWN`、`links == []` 写 `EMPTY`（三态必须让模型看见）。规则摘要 8 条（mlog 语法、v160、必须有 end、任何 ERR 即拒）。任务段 = 玩家原话 + 上一轮 findings + JSON 契约两种形状 |
| `parse_reply(text)` | 只取第一个配平的 `{...}`（容忍 markdown 围栏与前后散文），校验 `code`/`template` 二选一、`params` 是对象、`assumptions`/`needs_links` 是字符串数组；不合格抛 `ProviderError` |
| `HttpProvider` | OpenAI 兼容 `/chat/completions`，标准库 urllib；key 只从环境变量读（`--llm-key-env`），**导入模块时不联网** |
| `ScriptedProvider` / `load_script` | 回放录制回复，第 i 条答第 i 次尝试（正好覆盖 self-repair） |
| `Recorder` | `--llm-record FILE` 把每次 `{prompt, reply}` 追加成 JSONL ⇒ 真跑一次就得到可回放的脚本 |
| `provider_from_args(args)` | CLI 到 provider 的唯一装配点，缺参数抛 `ValueError` |

## 3. 队列与 CLI 的改动

- `tools/jobqueue.py` `_materialize()`：回复里声明的 `needs_links` 若含权威链接表之外的名字，**直接**追加一条
  `link-name-not-bound` ERR（`fatal=True`）并拒绝——不等分析器从代码里发现（模型可能声明了却没写进代码）。
- `tools/logicd.py`：`--jobs-provider` 增加 `llm`；新增 `--llm-url/--llm-model/--llm-key-env/--llm-timeout/--llm-replay/--llm-record`；
  `llm` 既没 url 也没 replay ⇒ `exit 2`（不静默回落到模板档，避免「以为在跑模型其实在跑模板」）。

## 4. 验收（half D，9 项，全离线）

`tests/logicd/run_logicd_tests.py` 新增 `test_provider()`：三段 prompt 与白名单三态、围栏/散文解析、五种垃圾回复全部拒绝、
scripted 干净回复经真队列跑到 `done`（且 `bytes_b64` 非空）、幻觉链接 `rejected`（attempts 3、`code == ""`、rid 命中）、
self-repair 第二轮 prompt 里出现 `REJECTED by the gate` 与上轮 finding、`needs_links` 越界拒绝、
CLI 无端点 `exit 2`、replay 文件加载、**CLI `--jobs-drain --llm-replay` 把一台作业跑成 `done`**（整条缝端到端）。

实测：`protocol: 25` / `jobs: 12` / **`provider: 9`** / `write path: 7`（真 v160.7）⇒ `logicd OK`。

## 5. 诚实缺口

- 真端点**从未联调**（本机无网络、无 key），所以证据只到「接口与状态机正确」，没到「模型按 prompt 写出好代码」。
- 自由档的 cost 与 200 tick 模拟复检（§4.3）未接。
- 模组侧还不能选 provider（要改 sidecar 命令行）；面板里没有「本次用的是模板档还是模型」的提示。
- P5 多处理器事务写入未开始。
