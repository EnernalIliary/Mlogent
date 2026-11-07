# MBO 与配比计算器（知识库）

> 工作区里两个"自己写的东西"的长期知识：`MBO/`（蓝图生成 + 优化 + 真机验证）与 `ratio-calc/`（自动配比计算器网页）。
> 本文只记**能被复用的结论、公式、数值和踩过的坑**，不记过程。最后更新：2026-11-07。

---

## 1. 两个项目在哪、怎么跑

| | `MBO/` | `ratio-calc/` |
|---|---|---|
| 定位 | 蓝图自动化：生成 / 搜索 / 优化 / 真机验证 / 出报告 | 单页网页：按目标建筑台数或物品速率算配比 |
| 入口 | `python -X utf8 -m mbo <calc\|gen\|opt\|verify\|preview\|build-snapshot>`（在 `MBO/` 下） | 双击 `ratio-calc/index.html`（无服务器、无外网） |
| 核心模块 | `mbo/gamedata.py` `production.py` `model.py` `layout.py` `codec.py` `engine.py` `validate.py` `logistics.py` `search.py` `sprites.py` `report.py` `cli.py` | `core.js`（内核，浏览器+node 通用）、`data/gamedata.js`（数据+内联图标） |
| 数据 | `MBO/gamedata/v160.7/{gamedata,units_production,power_drill}.json` | 由 `export_data.py` 从上面三份导出 |
| 测试 | `python -X utf8 -m unittest discover -s tests`（68 项）、`python -X utf8 gate.py`（12/12） | `node ratio-calc/test_core.cjs`（14 对拍 + 新算法断言）、`node ratio-calc/test_page.cjs`（58 断言）、`node ratio-calc/test_cli.cjs`（39 断言）、`node ratio-calc/test_core.cjs`（14 对拍 + 72 断言）、`python -X utf8 ratio-calc/test_card.py`（5 断言） |
| 产物 | `MBO/runs/<run_id>/{blueprint.msch,blueprint.b64.txt,metrics.json,report.md,trace.json,preview.png}` | `ratio-calc/docs/screenshot-*.png` |

约束（用户定的）：规则要程序化（不靠 LLM 拍脑袋）、确定性优先、多目标不塌缩、可追溯可复现。
石墨优化阶段用户口径：**源/黑洞只作为蓝图的输入输出标记，且必须落在工厂外接矩形之外；速率由物流元件决定。**

---

## 2. 真机验证协议（MBO）——所有数字都按这个协议测

- 官方服务端：`out/_server160.jar` + `out/jre21/.../java.exe`，`tools/mlogsim.py` 的 `Server(...)` 起服；整张 `.msch` 用 `Schematics.readBase64` + `place` 放进世界。
- **warmup 13 s**：服务器起来约 12 s 后世界会被换图，13 s 之前的读数全部作废。
- **丢掉前 300 tick**，之后按行采样，采样行的 `tick` 在 `parts[1]`。
- 读数坐标要加偏移 **`ox = 64 - w//2`**（`place` 锚点是蓝图中心）。
- 产物流入 `item-void`（物品黑洞）时容器差分测不出吞吐 ⇒ 用**分数周期回绕计数**（`progress` 下降记一次完成，`cycles_frac`）；整数回绕在 25 s 窗口有 ±6% 量化误差。
- 电力：必须显式写**对称的 `Point2[]` config**（tag=8 相对偏移），且 consumer 必须与 node **正交相邻**；"自动连线"是错误断言。
- 生成器必须**自校验 occupancy**：`place` 会静默覆盖，覆盖掉方块会导致饿死。
- `verify`：用自写 writer 重编码，与官方 `writeBase64` 的 **body 逐字节一致**（tags 可差：官方多 `contentMap`/`labels`）。
- 计速口径：`cps = 60 / craftTime`（`craftTime` 单位是**帧**）；目标速率 = 单机速率 × n。

---

## 3. 石墨（graphite）优化：结论与实测

`graphite-press`：2×2、`craftTime = 90` 帧、`2 coal → 1 graphite`、cps = 0.6667、**不耗电**。

真机结果（`MBO/runs/*/metrics.json`，`rate` 为实测产出/s）：

| run | 速率 | eff | 总格 | 端口 | 开口 | 说明 |
|---|---|---|---|---|---|---|
| `g1` | 1.3666 | 1.0 | 22 | — | — | 早期 cells 基线（源/机器/容器各一列） |
| `g1-split` | 1.3569 | 1.0 | 18 | — | — | 反溢流门支线 |
| `m4` | 4.0119 | 1.0 | 31 | — | — | 4 台压机（旧口径，端口在外之后作废） |
| `m-void` | 1.3591 | 1.0 | 13 | — | — | 出口接物品黑洞 |
| `m-single` | 1.3191 | 1.0 | 15 | — | — | 单容器出口（容器差分） |
| `d10` | 1.3588 | 1.0 | 10 | — | — | 4 方块/10 格 direct（**端口在外口径下作废**） |
| `p-both` | 1.2817 | 1.0 | 12 | 4 | 2 | 端口在外，双出口 |
| `p-gate` | 1.2865 | 1.0 | 12 | 3 | 2 | 端口在外，门出口 |
| `p-one` | 1.3588 | 1.0 | 14 | 2 | 2 | 端口在外，单出口 |
| `o-tiles` | 1.3589 | 1.0 | 12 | 4 | 2 | 最省格（8 工厂格 + 4 端口） |
| `o-cluster8` | 1.3539 | 1.0 | 12 | 4 | **1** | 8 工厂格 / 4 端口 / 单开口 |
| `o-cluster9` | 1.2866 | 1.0 | 12 | 3 | **1** | 9 工厂格 / 3 端口 / 单开口（源与黑洞相邻会互抢） |
| `o-dual` | 1.3521 | 1.0 | 14 | **2** | 2 | 双端最优：12 工厂格 + 2 端口 |
| `q-single` | 1.2849 | 0.466 | 45 | 2 | 2 | 四核单源单汇，路由器主干（差） |
| `q-tap1` | **1.9236** | 0.71 | 40 | 2 | 2 | 四核单源单汇最终版（78.5% of 2.45 上限） |
| `q6` / `q8` | 2.7026 / 2.7081 | 1.0 | 24 | 6 / 8 | 6 / 8 | 6/8 路进料 |
| `s3` | 2.9581 | 1.0 | 31 | — | — | 硅 3/s（目标 3.0） |

关键结论：

1. **2 端口的格数下界是 12 工厂格**：10 格 **7 446 种摆法 0 可行**、11 格 **3 418 380 种摆法 0 可行**；12 格唯一可行解就是 `S / MM+MM / MM MM / >n< / x` 模板，实测 1.352/s。
2. **单个端口方块不可能**（源只发不收、黑洞只收不发）；1 端口方块的最小解是 2 端口/9 工厂格（实测 1.2866），且源与黑洞相邻会互相抢料。
3. **侧向合流会掉吞吐**：三条带子侧向投进同一黑洞只有 **0.7952/s**（eff 0.58），两条带子直指黑洞 1.3569，带→路由器→黑洞 1.2868。判别口径：估值与真机差 >5% 先怀疑侧向合流。
4. 两颗/四颗压机的机器本身不是瓶颈，**瓶颈在物品怎么进去、出来怎么合流**。

---

## 4. 物流容量模型（`mbo/logistics.py`）与单源上限

- 模型：Dinic 最大流；`TILE_CAP = BELT_RATE = 4.9`（品/s）。传送带只连正前方；门/路由器连所有相邻运输方块并可向相邻 sink 卸货；`item-source` 挂 S（cap 100）。
- `estimate()` 返回 `rate = min(machine_cap, in_limited, out_limited)` + `bottleneck`；对 7 张历史图复算全部 1.3333、bottleneck=machine，与实测差 <2%。
- **单格物流上限 4.9/s**：4 台压机需煤 5.3333/s ⇒ **单源最多供 2.45 石墨/s**，缺的 8% 是约束内必然。
- 拆分探针（`MBO/spikes/gen/`）：源→带→容器 4.61/s、加 3 台路由器 4.69/s（**路由器不劈流量**）、单门 4.90/s、源→主干→4 门→4 容器 **4.9324/s**（输入网络本身能送满）；4 源合并输出 → 唯一黑洞 **2.5718/s**。
- **模型盲区（两类）**：①纯容量模型把压机四邻都当理想汇点，没建模"压机推料会占掉紧贴它的干线/输出带容量"——这正是 `q-tap1` 只到 78.5% 的原因（门喂压机与产物合流同时挂在 2×2 压机四邻上会掉 21%）；②它表达不了**方向性回吐死锁**：送料带指向压机时，压机把产物吐回脚下那格带子，带子又推回机器 ⇒ 吞吐 0，而模型仍报 2.45/s（实测 `runs/q-gap1` 死锁、`runs/q-gate-trunk` 只有 0.6794/s）。
- 门的语义（`OverflowGate`，同类的 `invert` 字段）：**overflow 直行优先、堵了走两侧；underflow 两侧优先（都通则按 rotation 交替）、两侧都堵才直行。**
- `DIRV = {0:(1,0), 1:(0,-1), 2:(-1,0), 3:(0,1)}` ⇒ `ROT["S"]` 指向 −y、`ROT["N"]` 才指向 +y（**极易搞反**）；`Layout(width, height, sizes)`、`add(name,x,y,rot,config)`、2×2 方块的 `(x,y)` 是左上角。

---

## 5. 配比计算器 `ratio-calc/`（结构与行为）

三种输入：**按建筑台数（满效）** / **按物品速率** / **兵厂 T1~T5 大循环**。

`core.js` 公开 API（都在 `module.exports` 上）：

```
buildIndex(data)                     → 索引：items/itemProps/generators/drills/multi/pumps/channels/channelsByKey/unitProducers/unitChains/unitIcons
expand(data, item, rate, boundary, force, opts)          传统：按物品速率
expandBuilding(data, blockName, count, opts)             按建筑台数（物品工厂/兵厂/升级厂）
drillRate(data, drill, item, tiles, boosted)             60*tiles*speed²/delay
drillsNeeded(...)                     → {count, perSecondEach, power, liquid, ...}
generatorPlan(data, demand, gen, fuel) → {count, netEach, fuel:{perSecond}, liquids, surplus}
generatorSupply(data, gen, fuel, count)                   手填台数
separatorPlan(data, name, count)      → {outputs:[{name,share,perSecond}], inputs, inputLiquids}
pumpPlan(data, liquid, amount, pump)  → {count, perSecondEach, power, inputs, inputLiquids}（液体自己抽）
unitChain(data, startUnit, rate, opts) → opts 支持 {topTier, topCount}（给台数，如 5t5）或 rate（给速率）
                                       → {topTier, topCount, rows:[{tier,unit,block,count,perSecond,capacity,actual,utilization,feedsNext,bottleneck,...}],
chainFromTop(data, startUnit, tier, count, opts) → unitChain 的「给台数」包装（页面/CLI 的 `5t5` 走这条）
chainsForBlock(data, blockName)      → 这个兵厂属于哪几条升级线 [{start,top,tier,tiers}]，按 CHAIN_PREF（dagger 优先）排序
chainFromBlock(data, blockName, count, opts) → 选中兵厂 + 台数直接走大循环；opts.chainStart 指定升级线；非兵厂返回 null
                                         achieved, bottleneck, bottleneckTier, power, materials}
applySources(data, res, cfg)          把边界物品/液体换成本地来源（import / drill / multi / pump）并重算机器与电力
liquidDemand(idx, machines, extra)    → [{name, perSecond}]（extra = 钻头加速液）
machineRows(data, res)                → 表格行（含 outItems）
anyBlock(idx, name)                   统一 blocks/drills/multi/generators 视图
```

- 展开规则（与 `MBO/mbo/production.py` 一致）：①`n = ceil(需求/单台)`；②输入递归、遇 boundary 停；③多配方时先选"输入也能自造"（不新增边界），再选 `round(n*per)` 最接近，再比 `size²`，最后按名字；④无配方 → 外部输入 + warning；⑤`depth > maxDepth` 记 `reason:"depth"`。
- 页面四块新表：**外部来源**（钻头+矿格数+加水 / 分离机·解离机 / 外部运入——7 种带子与接收台）、**供电**（14 发电厂，选燃料自动算台数与燃料/液体）、**液体需求**（外部运入 / 抽水机，自动补台数与电力）、**兵厂大循环**（10 条链 T1–T5，可给台数 `5t5` 或速率）。
- **兵厂链口径（2026-11-07 修正）**：台数按各自 `constructTime` 算、**不必 1:1**（1 台 T4 scepter 0.0111/s 能带 2.67 台 T5 reign 0.00417/s）；整链产出 = 各段产能**最小值**（最慢一段决定），材料按实际达成算，多出的机器记"利用率"；`feedsNext` = 1 台本级能带几台上级。
- **兵厂链给台数（2026-11-08 加）**：输入框 `#chainexpr` 写 `5t5`（5 台 T5 厂满效）或 `0.02`（每秒几个）；`parseChainExpr` 用 `/^(\d+(?:\.\d+)?)\s*[x×*]?\s*t\s*([1-5])$/i` 解析，走 `chainFromTop`。`5t5` 实测：T1–T5 台数 **1/1/1/2/5**、达成 **0.021/s**、瓶颈 reign、**9672 电**、硅 42.292/s（2537/min）、塑料 26.042、钛 17.292、surge-alloy 10.417、相织物 7.292、石墨/玻璃 0.833、铅 0.208。链块只在「按目标物品速率」页显示（`<div class="mode-item hidden" id="chainsec">`），`#chainres` 表给 /s 与 /min。
- **外部入料方式细分（2026-11-08 加）**：`INPUT_CHANNELS`（`export_data.py`）7 种，键/速率/电力：`belt-grey` 灰带 conveyor 5.25/s 0 · `belt-blue` 蓝带 titanium-conveyor 12.015/s 0 · `belt-green` 绿带 plastanium-conveyor 40/s 0 · `phase-bridge` 布桥 phase-conveyor 30/s 18 · `mass-driver` 质驱 36/s 105 · `pad` 接收台 不限 0 · `other` 其它 不限 0。吞吐 = `speed×60/itemSpace(0.4)`（`Conveyor.java:27-32`）：v160.7 jar 灰带 `speed=0.035` ⇒ **5.25/s**（v159.3 源码是 0.046 ⇒ 6.9/s，已按"以 jar 为准"改成 5.25），蓝带 0.0801 ⇒ 12.015/s；MBO 真机实测约 4.9 items/s（含量化/采样误差）。数值口径以 `knowledge/00-data/blocks.json` 与 `knowledge/08-evidence/CHEAT.md` 为准，要改只改 `export_data.py` 的 `INPUT_CHANNELS`。条数 = `ceil(需求/单条)`，经 `applySources` 的 `type:"import", via` 分支累加进 `res.extraPower`（`recalcPower` 里 `res.power = power + extraPower`，否则会被重算抹掉）。
- **兵厂链并进「按目标建筑台数」页（2026-11-08 二次修正，用户 m07495）**：不再单开一类。选中兵厂 + 填台数就自动走大循环（`run()` 里 `selB.kind === "unit"` → `R.chainFromBlock`，`chainToRes` 把链摊成 machines/demand/power/products，`products` 取**目标级自己的满效产能** `rows[topTier-1].capacity`，不是整链 achieved）；同一重建厂服务多条线时用「升级线」下拉（单位工厂则用已有的「生产计划」下拉，避免两个下拉重复），默认优先 dagger 线，`tetrative-reconstructor` 3 个候选、切 flare 后 T5 显示 eclipse；0 台层级显示「×0（不建）」、材料不列 0；`#chainsec` 改成 `mode-block`，`#chain`/`#chainexpr` 输入条删除（`chainLink()` 仍把 URL 的 `?chain=dagger&chainexpr=5t5` 翻译成"选中 T5 兵厂 + 台数 5"）。CLI 侧 `--block <兵厂> --count N` 同样返回 `mode:"chain"` 且填好 machines/demand/power，`--plan N` 映射成升级线。
- URL 参数：`?mode=building|item&block=&count=&item=&rate=&boundary=&force=&depth=&gen=&genfuel=&gencount=&chain=&chainexpr=5t5&chainrate=&src=sand:drill:laser-drill:8:1,scrap:multi:disassembler,water:pump:rotary-pump,coal:belt:belt-blue`；兵厂链直接 `?mode=building&block=tetrative-reconstructor&count=5` 或 `?chain=dagger&chainexpr=5t5`。
- 贴图为**原尺寸**且**优先 `-full` 高清整图**（`sprites/generated/block-<名>-full.png`、`unit-<名>-full.png`，缺了回退 `blocks/**` / `units/<名>-base.png`），全部内联 base64：`data/gamedata.js` = 33 工厂 / 17 兵厂 / 14 发电厂 / 10 钻头 / 2 多产物 / 6 抽水泵 / 22 物品 / **139 图标 / 493 中文名 / 1130.8 KB**。
- 中文名来自 `assetsraw/assets/bundles/bundle_zh_CN.properties`（key 形如 `item.<名>.name` / `block.<名>.name` / `unit.<名>.name`），导出成 `data.names = {items, blocks, units}`；页面标签显示「英文名 + 灰字中文名」，选择格 tooltip 也带中文。
- 实例：`graphite-press ×2` → 石墨 1.333/s、煤 2.667/s、电力 0；煤改激光钻 8 格 → 3 台激光钻、电力 198 → 燃烧发电机 4 台、烧煤 2/s；`silicon-smelter ×3` + 沙用解离机 → 6 台解离机、电力 1530、副产石墨/钛/钍各 4.8/s、吃废料 24/s；`silicon-smelter ×3` + 沙用激光钻（加水）+ 水用 rotary-pump → 水 14.4/s、泵 2 台（电力 +36）、总电力 324；`dagger 0.05/s` → **1/1/2/5/12** 台、**22872** 电、硅 101.5/s、瓶颈 T5 reign。

**发电设备当目标建筑（2026-11-08 加）**：建筑页第三组选单是 14 个发电厂，选中后按台数算
总发电/燃料/液体/自耗电，**不做电力递归**（`expandGenerator`，`DEFAULT_GENERATOR="combustion-generator"`、
`DEFAULT_FUEL="coal"`；`supply.netTotal = (gross - powerUsage) * count`）。
对应测试：`test_core` 98 行 ok、`test_page` 62、`test_cli` 42、`test_card` 6。

### 5.1 接入 bot 的四个入口（2026-11-07 加）

算法只有一份（`core.js`），四个壳都只是调它，`test_cli.cjs` 里有逐项对拍：

| 入口 | 文件 | 用法 | 适合 |
|---|---|---|---|
| 命令行 | `cli.cjs` | `node cli.cjs --item silicon --rate 5 --format json` | bot subprocess |
| HTTP | `serve.cjs` | `GET /calc?item=silicon&rate=5&format=md`、`/list`、`/healthz` | 常驻服务、跨语言 |
| Python | `ratio.py` | `ratio.query(...)` / `ratio.text(...)` / `ratio.image("c.png", ...)` | Python bot 直接 import |
| 图 | `card.py` | `python card.py --item silicon --rate 5 --out card.png` | bot 发图（PIL 画、原尺寸图标内联） |

- `cli.cjs` 的 `--boundary` 不写时默认 `coal,sand`（与网页一致，避免算出 `coal-centrifuge` 吃油的绕路链）；`all` = 所有矿外部输入，`none` = 全自产。
- JSON 默认**剔除** base64 图标（`--icons` 保留）：体积能小一半以上；要发图就用 `card.py`。
- 液体单独成表：方块条目的 `input_liquids`/`output_liquids` 来自 dump 的 per-tick `amount`×60；`res.liquids` 汇总全链液体（含水钻加速液）。
- 卡片用 `C:\Windows\Fonts\msyh.ttc`，700px 宽、深色；`--scale 2` 出 2 倍图。示例 `ratio-calc/docs/card-{graphite,unit,chain,pump,bot}.png`。
- 液体来源：`--src water=pump:rotary-pump`（CLI）/ `src=water:pump:rotary-pump`（URL）/ 页面液体需求表的下拉；`applySources` 迭代 6 轮收敛（泵自己可能吃液体：抽油机吃水 9/s、强化泵吃氢 1.5/s）。

**统一入口（2026-11-08 规范化）** —— 五层各有唯一入口，下层只调上层、不复制算法：

| 层 | 入口 |
|---|---|
| `core.js`（唯一算法） | `buildIndex(data)` → `expand` / `expandBuilding` / `chainFromTop` / `chainFromBlock` / `chainsForBlock` / `applySources` / `generatorPlan` / `pumpPlan` / `separatorPlan` / `drillRate` / `unitChain`；常量 `DEFAULT_CHANNEL` |
| `cli.cjs` | **`query(opts) -> JSON`**、`renderText` / `renderMarkdown` / `renderList`、`loadData`；内部 `chainResult()` 是 `--chain` 与 `--block <兵厂>` **共用**的一段装配 |
| `serve.cjs` | `handle(req, res)`、`optsFromQuery(q)`（就是 `cli.query`） |
| `ratio.py` | **`calc(**kw)`**（`query` 的别名）、`text`、`markdown`、`image`、`card(res, out)`、`http_query` |
| `card.py` | **`build_card(res)`**、`render_png(res, out)`、`card_from_json(path, out)`；`--from-json` = `--json` |

**外部入料默认蓝带**：`core.js` 的 `DEFAULT_CHANNEL = "belt-blue"`（12.015/s 一条）是唯一默认值，网页下拉、CLI、卡片、`ratio.py` 全读它；
`applySources` 的 import 分支不再要求显式 `via`，缺省即蓝带 ⇒ 每项边界输入**自动给出条数**，条数电耗进 `res.extraPower`。

**bot 卡片内容顺序**（`card.py`，2026-11-08 调整）：① 工厂配比（正文主体，`工厂配比：N 台 · 电力 X/s` + 每台 `×台数 · 电 · 产出`；
兵厂链模式换成 `各级兵厂（配比结果）`）→ ② 外部入料（默认蓝带，`蓝带 titanium-conveyor ×N 条（12.015/s）`）→ ③ 液体需求 → ④ 供电 → ⑤ 提示。
`test_card.py` 用结构断言守住"配比在前、蓝带在后、行不重叠、PNG 可渲染"，不靠肉眼看图。

---

## 6. 数值公式（v160.7，全部从服务端反射 dump 核对过）

| 量 | 公式 |
|---|---|
| 配方速率 | `cps = 60 / craftTime(帧)`；每秒消耗 = `cps × 配方数量` |
| 钻头速率 | `items/s = 60 × 矿格数 × speed² / delay`，`delay = (drillTime + 50 × 物品hardness) / mult`，`speed = boosted ? boostIntensity : 1`（加水是 `boostIntensity²`：机械/气动/激光 1.6 ⇒ ×2.56，爆裂钻 1.8 ⇒ ×3.24） |
| 发电 | 台数 = `ceil(需求 / (gross − 自耗))`；燃料/s = `1 / (itemDuration/60 × mult)`，`mult` = 该物品 `flammability`（`ConsumeItemFlammable`）或 `radioactivity`（`ConsumeItemRadioact`） |
| 多产物 | 每次 craft **随机按权重取一件**：`share = amount / Σamount`，`perSecond = cps × share` |
| 兵厂 | 每秒 = `60 / time(帧)`；材料 = 每个单位的消耗 × 每秒产量；升级厂 `constructTime` 同理 |
| 兵厂链 | 每级台数 `ceil(目标/单台)`（各自 `constructTime`，**不必 1:1**）；整链达成 = `min_k(产能_k)`（最慢一段）；材料按 `达成/该级每秒 × 单次消耗` |
| 抽水 | `perSecond = pumpAmount(per-tick) × 60`；台数 = `ceil(需求 / perSecond)`；抽油机另吃沙 `60/itemUseTime` 与 水 9/s |

物品属性：`hardness`（copper/lead 1、coal 2、多数 0）、`flammability`（coal 1、spore-pod 1.15、pyratite 1.4、blast-compound 0.4）、`radioactivity`（thorium 1、phase-fabric 0.6）。

### 6.1 读「游戏速查」的耗电口径（历史 bug）

`docs/游戏速查/方块.md` 里的「耗电 x/s」其实是 **per-tick** 值，×60 才是每秒：

- `ground-factory` / `air-factory` / `naval-factory` 写成 1.2/s，真值 **72/s**；
- `graphite-press` 没有耗电（0），不是 0/60 的问题而是本来就不耗电；
- 本节与第 7 节的电力数字来自反射 dump（`gamedata.json` 的 `power.usagePerSecond`），**以 dump 为准**。

同理，任何「/s」都要先问一句：这个数字是配方里的 per-tick 还是已经换算过的每秒。

---

## 7. 数值表（直接可用）

### 7.1 发电厂（净发电 /s，燃料为每秒）

| 方块 | 尺寸 | 净发电 | 燃料 | 液体 |
|---|---|---|---|---|
| solar-panel | 1 | 7.2 | passive | — |
| combustion-generator | 1 | 60 | coal .5（spore-pod → 69、blast-compound → 24、pyratite .1667 → 84） | — |
| turbine-condenser | 2 | 20 | — | — |
| solar-panel-large | 3 | 96 | passive | — |
| thermal-generator | 2 | 108 | passive（热源） | — |
| steam-generator | 2 | 330 | coal .667（pyratite .2222 → 462） | water 6 |
| rtg-generator | 2 | 270 | thorium .0714（phase-fabric .004762 → 162、fissile-matter .0714 → 405） | — |
| thorium-reactor | 3 | 900 | thorium .1667 | cryofluid 2.4 |
| differential-generator | 3 | 1080 | pyratite .2727 | cryofluid 6 |
| chemical-combustion-chamber | 3 | 550 | — | ozone 2 + arkycite 40 |
| pyrolysis-generator | 3 | 1400 | — | slag 20 + arkycite 40 |
| impact-reactor | 4 | 7800（自耗 1500） | blast-compound .4286 | cryofluid 15 |
| neoplasia-reactor | 5 | 8400 | phase-fabric .3333 | arkycite 80 + water 10 |
| flux-reactor | 5 | 18000 | — | cyanogen 9 |

### 7.2 钻头

| 方块 | 尺寸 | tier | drillTime | 加成液体 | boost |
|---|---|---|---|---|---|
| mechanical-drill | 2 | 2 | 600 | water 3/s | 1.6 |
| pneumatic-drill | 2 | 3 | 400 | water 3.5/s | 1.6 |
| laser-drill | 3 | 4 | 280 | water 4.8/s（66 电） | 1.6 |
| blast-drill | 4 | 5 | 280 | water 6/s（180 电） | 1.8 |
| plasma-bore | 2 | 3 | 160 | hydrogen .25/s（9 电） | 1.0 |
| large-plasma-bore | 3 | 5 | 100 | nitrogen 3/s（48 电） | 1.0 |
| impact-drill | 4 | 6 | 720 | ozone 3/s（160 电） | 1.75 |
| eruption-drill | 5 | 7 | 281.25 | cyanogen .75/s（360 电） | 2.0 |
| cliff-crusher | 2 | 0 | 110 | —（11 电） | — |
| large-cliff-crusher | 3 | — | 48 | —（60 电） | — |

### 7.3 多产物（每台每秒）

- `separator` 2×2：cps 1.7143，吃 slag 4/s、电 66 → copper .714 / lead .429 / graphite .286 / titanium .286
- `disassembler` 3×3：cps 4，吃 scrap 4/s + slag 7.2/s、电 240 → sand 1.6 / graphite .8 / titanium .8 / **thorium .8**

### 7.3.5 抽水泵（`power_drill.json` 的 Pump 段）

| 泵 | 尺寸 | 每秒 | 电力/s | 额外消耗 | 备注 |
|---|---|---|---|---|---|
| mechanical-pump | 1 | 7 | 0 | — | 地表水 |
| rotary-pump | 2 | 12 | 18 | — | |
| impulse-pump | 3 | 13.2 | 78 | — | |
| reinforced-pump | 2 | 20 | 0 | hydrogen 1.5/s | |
| water-extractor | 2 | 6.6 | 90 | — | 要地下水 |
| oil-extractor | 3 | 15（oil） | 180 | sand 1/s + water 9/s | 要油田 |

### 7.4 兵厂升级链（`units_production.json`：70 单位 / 17 兵厂）

- dagger→mace→fortress→scepter→reign（additive 600 帧 / multiplicative 1800 / exponential 5400 / tetrative 14400）
- nova→pulsar→quasar→vela→corvus；crawler→atrax→spiroct→arkyid→toxopid；flare→horizon→zenith→antumbra→eclipse；mono→poly→mega→quad→oct；risso→minke→bryde→sei→omura；retusa→oxynoe→cyerce→aegires→navanax
- Erekir：stell→locus→precept（tank-fabricator → tank-refabricator → prime-refabricator）、merui→cleroi→anthicus（mech-assembler）、elude→avert→obviate（ship-assembler）
- 兵厂电力：ground/air/naval-factory 72、mech/ship/tank-fabricator 90、additive 180、multiplicative 360、exponential 780、tetrative 1500、prime-refabricator 270、*-assembler 150~180、basic-assembler-module 210

---

## 8. 反射 dump 的铁律（Rhino + `tools/mlogsim.py`）

1. **`Server.js()` 用 `wait_for("undefined")` 判定脚本结束**：输出里任何一行出现字符串 `undefined` 都会被当成结束信号、后续行全部丢失。所有插值必须过
   `function S(v){ if(v===null||v===undefined) return ''; if(typeof v==='number'&&v!==v) return ''; return ''+v; }`。
2. **循环里 `print` 会让脚本中途挂掉**（447 个方块只出 1 行）：先 `var L=[]; L.push(...)`，循环结束后统一 `print`。
3. `b.consumers` 是 **Java 数组**（`[Lmindustry.world.consumers.Consume;`）：只能用 `.length` + `[k]`，调 `.get/.size` 会抛
   `EvaluatorException: Java class "[L...Consume;" has no public instance field or method named "get"`。
4. **`while(it.hasNext)` 在 Rhino 里恒真**（方法对象恒真）⇒ 遍历 Java Map 会死循环，只能按名字 `map.get(name, 1)` 逐个取。
5. 服务端方块多是**匿名子类**（`mindustry.content.Blocks$322`）：靠 `getClass().getName().indexOf("UnitFactory")` 永远匹配不到，要**按字段探测**（有 `plans` → 单位工厂/组装厂；有 `upgrades` → 升级厂；用 plan 的类名区分 Assembler）。
6. 匿名子类上读不到的字段返回 `undefined` 而不是抛错 ⇒ 判空要写 `!= null && !== undefined`。
7. `BlockPower` 在 Rhino 里读不到（`b.power.usage` 全抛）⇒ 电力从 `gamedata.json` 的 `power.usagePerSecond` 合并。
8. `ItemStack[]` 有 `.length`、`Seq` 只有 `.size`；`Seq` 取元素用 `.get(i)` 或 `[i]` 兜底。
9. `itemDurationMultipliers` 在 **consumer**（`ConsumeItemEfficiency`）上，不在 `Block` 上；`ConsumeLiquid`（单数）用 `.liquid`，`ConsumeLiquids`（复数）用 `.liquids`；液体 `amount` 是 **per-tick**（×60 得每秒）。
10. `try { }` 必须有 `catch`（Rhino 报 `'try' without 'catch' or 'finally'`）；变量名 `cons` 会撞 `redeclaration of const cons`。

产出脚本：`out/_dump_units_production.py`（兵厂）、`out/_dump_power_drill.py`（发电/钻头/多产物）、旧的 `out/_dump_game.py`（全量方块）。

---

## 9. 工具链的坑（都踩过）

- **`bash` 工具实际是 PowerShell**：没有 heredoc（`<<'PY'` 直接语法错）、`&&` 不可靠、`python -c` 里的引号容易被吞 ⇒ 一律**先 write 成 `.py` 再 `python -X utf8 file.py`**。
- **不要用 `Get-Content -Raw | Set-Content` 改 UTF-8 源码**（会把中文写坏成 `?`，随后 `SyntaxError: Invalid or unexpected token`）⇒ 改源码用 write/edit 工具。
- 控制台输出中文可能乱码（GBK）：读文件内容用 `read` 工具，不要 `cat`/`Get-Content` 判内容。
- Chrome headless 在这台机器上会挂（超时被 kill）⇒ 用 **Edge headless**：
  `msedge.exe --headless=new --disable-gpu --no-sandbox --no-first-run --user-data-dir=<tmp> --window-size=1180,2000 --virtual-time-budget=5000 --screenshot=<绝对路径> <file:/// url>`；只要 DOM 串就用 `--dump-dom`。
- 页面在 node 里跑测试时：`window`/`document` 要自己搭桩，`querySelectorAll` 返回 `[]`、`addEventListener` 是空函数 ⇒ 交互必须留 `window.__ratio` 之类的钩子；浏览器里 `children` 是 `HTMLCollection`（**没有 `forEach`**，要 `Array.prototype.slice.call(...)`）。
- `file://` 下 `fetch` 有 CORS 限制 ⇒ 数据必须写成 `.js`（`window.MBO_DATA = {...}`）而不是 `.json`。
- 页面 URL 中文路径要百分号编码：`file:///F:/OneDrive/%E6%A1%8C%E9%9D%A2/...`。

---

## 10. 复现命令

```powershell
# MBO
cd F:\OneDrive\桌面\AtomicStates\MBO
python -X utf8 -m unittest discover -s tests        # 68 项
python -X utf8 gate.py                              # 12/12
python -X utf8 -m mbo opt graphite:1/s --boundary coal --only-ports 2 --objective tiles --crop --out o-dual
python -X utf8 -m mbo preview o-dual --scale 14

# 数据 dump（需要 out/jre21 + out/_server160.jar）
python -X utf8 out\_dump_power_drill.py
python -X utf8 out\_dump_units_production.py

# 配比计算器
python -X utf8 ratio-calc\export_data.py
node ratio-calc\test_core.cjs
node ratio-calc\test_page.cjs
```

---

## 11. 还没做 / 下一步

- MBO：把"机器四邻哪些格是合法出口"写进 `logistics.py`，抢回四核线掉的那 21%；再压 `q-tap1` 的 40 格。
- 配比计算器：发电燃料没接回钻头/分离机（燃料链不闭环）；液体默认外部输入；组装厂吃的是方块 Payload，不展开；多产物按期望值算，没给波动。
- 蓝图预览画廊：`MBO/runs/index.html`（贴图版，`mbo preview --all` 生成）。
