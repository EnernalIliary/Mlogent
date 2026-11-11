# 自动配比计算器（网页 + 命令行 + HTTP + PNG 卡片）

算 Mindustry v160.7 的产线配比：给一个**目标**，算出要几台什么机器、上游每种物品多少/秒、总电力、
要几台发电厂烧多少燃料、外部原料用哪种钻头/要不要加水、兵厂 T1→T5 整条升级链要几台。
界面上的工厂、兵厂、单位、物品、发电厂、钻头全部用**原版贴图图标**（原尺寸内联 base64，不依赖外部图片）。

双击 `index.html` 就能开（不需要服务器、不需要联网）；要接到 bot 上就看下面的
[接入 bot（四种接法）](#接入-bot四种接法)：命令行、HTTP、Python、直接出图。

## 三种输入方式

| 模式 | 输入 | 适合 |
|---|---|---|
| **按建筑台数（满效）** | 选一个工厂 / 兵厂 + 台数 | "我要 4 台石墨压机满效跑" → 反推上下游 |
| **按物品速率** | 选物品 + 每秒产量 | 传统玩法："我要 5 硅/s" |
| **兵厂大循环** | 选一条 T1~T5 链 + 顶级速率 | "我要 0.05 reign/s" → 五级各要几台、材料多少 |
| **混合厂** | 多个目标（工厂 / 兵厂 / 发电厂）+ 各自台数 | "石墨压机 3 台 + 硅电弧炉 1 台一起建，共享上游怎么配" → 合并后机器清单、省了多少 |

各模式下都能改：
- **递归层数**：上游展开到第几层（超过就当外部输入），默认 4
- **边界**：22 种物品 + 11 种液体的**开关**（芯片点一下切换，勾上就按"外部送进来"，不再展开）；
  液体也能进边界——`oil` 勾上，煤处理线就止于煤炭分离机，不再自动接石油钻井/孢子压缩
- **指定配方**：只有多配方的物品才列，一行一个下拉（默认「自动」按规则挑）；点"多配方"表里的备选也会把下拉切过去
- 命令行仍然用文本：`--boundary a,b` / `--force 物品=方块`（页面只是把这两个参数做成了按钮，不是另写一套算法）

## 四块新功能

### 0. 统一入口（先看这一节，别复制算法）

五层各有**唯一入口**，下层只调用上层，不重写算法；bot 只用记一行：

| 层 | 文件 | 入口 | 返回 |
|---|---|---|---|
| 内核（唯一算法） | `core.js` | `buildIndex(data)`、`expand`、`expandBuilding`、`expandMixed`、`chainFromTop`、`chainFromBlock`、`chainsForBlock`、`applySources`、`generatorPlan`、`pumpPlan`、`separatorPlan`、`drillRate`、`unitChain`、`liquidSourcePlan`、`DEFAULT_CHANNEL` | 纯 JS 对象 |
| 命令行 / HTTP 逻辑 | `cli.cjs` | **`query(opts)`** → JSON；`renderText` / `renderMarkdown` / `renderList`；`loadData` | JSON / 文本 |
| HTTP | `serve.cjs` | `handle(req, res)`、`optsFromQuery(q)`（内部就是 `cli.query`） | HTTP 响应 |
| Python | `ratio.py` | **`calc(**kw)`**（= `query`）、`text`、`markdown`、`image`、`card`、`http_query` | dict / str / PNG |
| 卡片 | `card.py` | **`build_card(res)`**、`render_png(res, out)`、`card_from_json(path, out)` | PIL / PNG |

规矩：

1. **默认值只在一处**：外部入料默认蓝带写在 `core.js` 的 `DEFAULT_CHANNEL`，网页下拉、`cli.cjs`、`card.py`、`ratio.py` 全部读它；
2. **四种模式的 JSON 同构**（`mode: item | building | chain | mixed`），字段见下文「JSON 结构」；
3. `--chain X --chainexpr 5t5` 与 `--block <T5 兵厂> --count 5` 走**同一段装配**（`cli.cjs` 的 `chainResult`），结果按字段逐项相同；
4. 改算法只改 `core.js`；改数据只改 `export_data.py`。

### 1. 外部来源可配置（含入料方式：灰带 / 蓝带 / 接收台…）

边界表（页面中部"外部来源"）里，每种边界物品可以选：

- **接收（外部运入）** —— 默认；入料方式默认**蓝带**（`titanium-conveyor` 12.015/s 一条），
  条数 = `ceil(需求 / 12.015)`，并按条数算电力（蓝带 0 电，布桥/质驱才算）；
- **钻头采集** —— 选钻头（10 种）+ 矿格数 + 是否加水/加氢/加氮/加臭氧/加氰；
  台数按 `60 × 矿格数 × speed² / delay` 反推，`delay = (drillTime + hardnessMult × 物品硬度)`，
  `speed` 加水时取该钻头的 `boostIntensity`（机械/气动/激光 1.6 ⇒ 吞吐 ×2.56，爆裂钻 1.8 ⇒ ×3.24）；
- **多产物 · 分离机 / 解离机** —— 这两台是"加权随机出一件"，台数按目标产物反推
  （`share = amount / Σamount`），并把**所有**副产物和输入列出来：
  - 分离机：矿渣 4/s + 66 电 → 铜 .714 / 铅 .429 / 石墨 .286 / 钛 .286 每台每秒
  - 解离机：废料 4/s + 矿渣 7.2/s + 240 电 → 沙 1.6 / 石墨 .8 / 钛 .8 / **钍 .8** 每台每秒

钻头/多产物的台数和耗电会并进机器表与总电力；**钻头不是"外部来源"里的另一类机器**，
它就是工厂配比里的一员：机器表写「laser-drill ×1 · 电 66/s · coal 3.234/s」，台数与耗电计入工厂合计，
来源表只负责配"用哪台钻头、几格矿、要不要加水"。

**外部运入再细分**（"参数"列下拉，7 种；不要傻运，选条带子能看出要几路）：

| key | 入料方式 | 方块 | 速率 | 电力/s | 说明 |
|---|---|---|---|---|---|
| `belt-grey` | 灰带 | `conveyor` | 5.25/s | 0 | 最便宜；v160.7 jar `speed 0.035` → `speed×60/0.4` |
| `belt-blue` | 蓝带 | `titanium-conveyor` | 12.015/s | 0 | 主力 |
| `belt-green` | 绿带 | `plastanium-conveyor` | 40/s | 0 | 大批量 |
| `phase-bridge` | 布桥 | `phase-conveyor` | 30/s | 18 | 跨距离，要电 |
| `mass-driver` | 质驱 | `mass-driver` | 36/s | 105 | 跨地图投送 |
| `pad` | 接收台 | `landing-pad` | 不限 | 0 | 从别的核心接收 |
| `other` | 其它 | — | 不限 | 0 | 手动 / 逻辑 |

条数 = `ceil(需求 / 单条速率)`，台数与电力并进机器表（`pad`/`other` 不显示条数）。
数值来自 `Conveyor.java:27-32` 的 `itemSpace = 0.4`（吞吐 = `speed × 60 / 0.4`），**以 v160.7 jar 为准**（`knowledge/00-data/blocks.json#conveyor.speed = 0.035` ⇒ 5.25/s），集中在 `export_data.py` 的 `INPUT_CHANNELS`，要改只改那一处。

### 2. 发电厂

页面下部"供电"：14 种发电厂按单台净发电排序，选燃料后自动算**要几台**（或手填台数看能供多少）、
净发电合计、燃料每秒、需要的液体、以及发电厂自身的耗电（冲击反应堆自耗 1500/s）。
燃料发电按 `itemDuration` 与可燃性/放射性折算：

- 燃烧发电机 60/s（煤 .5/s；孢子荚 → 69；爆炸混合物 → 24；黄炸药 .1667 → 84）
- 蒸汽发电机 330/s（煤 .667/s + 水 6/s；黄炸药 → 462）
- 差动发电机 1080（黄炸药 .273 + 冷却液 6）、钍反应堆 900（钍 .167 + 冷却液 2.4）
- 冲击反应堆 7800（爆炸混合物 .429 + 冷却液 15，自耗电 1500）
- 还有 RTG 270、热力 108、大型太阳能 96、太阳能 7.2、涡轮冷凝器 20、热解 1400、化合燃烧室 550、
  通量反应堆 18000、新质反应堆 8400

**发电设备也能当目标建筑**：「按目标建筑台数」页第三组选单里直接选发电厂（14 种），填台数，
就按 100% 效率算**总发电 / 燃料 / 液体 / 自耗电**。

这时**发电厂会像普通工厂一样展开递归树**（燃料和液体从哪来都要交代清楚）：

```
node ratio-calc/cli.cjs --block steam-generator --count 2 --boundary "coal,sand" --liquids auto
#   产出：电力 660/s
#   供电：steam-generator ×2（净 660/s，烧 coal 1.333/s，water 12/s）
#   液体自产：water ← 小泵 2 台（钻井合计 14/s）

node ratio-calc/cli.cjs --block differential-generator --count 1 --boundary coal --liquids auto
#   pyratite-mixer ×1（电 12/s），吃 coal 0.75/s + lead 1.5/s + sand 1.5/s → pyratite 0.75/s
#   pulverizer ×1（电 30/s），吃 scrap 1.5/s → sand 1.5/s
#   cryofluid-mixer ×1（电 60/s），吃 titanium 0.5/s + water 12/s
#   供电：differential-generator ×1（净 1080/s，烧 pyratite 0.273/s，cryofluid 6/s）
```

- 燃料/液体写进边界（`--boundary coal`、页面勾「煤」）就停在边界，不再往上追；不写就一路追到矿——
  `--block combustion-generator --count 2 --boundary none` 会自己配出 `coal-centrifuge ×1` 再去配油/泵；
- **但仍然不做「电力递归」**：发电厂自己发的电不会反过来推「还要几台发电机」，自耗电（冲击反应堆 1500/s）
  只按字面记在 `selfUse` 上；同样，**普通工厂缺电也不递归**，电力只是数字，发电是独立的供电表。

```
node ratio-calc/cli.cjs --block impact-reactor --count 2 --genfuel blast-compound
#   产出：电力 12600/s（单台毛 7800、自耗 1500 → 净 6300）
```

### 3. 兵厂 T1 → T5 大循环（**在「按目标建筑台数」页选兵厂就行**）

不必单开一类：左侧选一个兵厂、填台数，选中兵厂的那一刻就直接按大循环算——
「台数」指的是**这一级要几台**，其它层级由它反推（选 T1 工厂就是"1 座 dagger 厂"，选 T5 就是"5 座 T5 厂"）。

- 一个工厂服务多条线时（`tetrative-reconstructor` 同时升地面/空军/机甲）：单位工厂用「生产计划」下拉选线，
  重建厂用新出现的「升级线」下拉选线，默认优先 dagger 线；
- `5t5` / `3t4` 这种写法仍可在 URL 与 CLI 里用作快捷方式（`?chain=dagger&chainexpr=5t5`、`--chainexpr 5t5`）。

10 条链（6 条原版 + 3 条 Erekir + 1 条 prime-refabricator），选定顶级台数后按层级倒推：

1. 每级台数 = `ceil(目标速率 / 单台每秒)`，各自按自己的 `constructTime` 折算，**不必 1:1**
   （例如 1 台 T4 `scepter` 0.0111/s 能带 **2.67 台** T5 `reign` 0.00417/s）；
2. 整条链的实际产出 = 各段产能的**最小值**（流水线由最慢的一段决定），不是"上级产能继续往下乘"；
3. 材料按实际只跑到的产出算：`craft/s = 达成 / 该级每秒产出`，`材料 = 单次消耗 × craft/s`，
   多放的机器只会闲置（表里"利用率"就是这个比值）。

**输入方式有两种**：给台数（`5t5` = 5 台 T5 厂，满效）或给速率（`0.02` = 每秒 0.02 个 T5 单位）。

以「5 台 T5」为例（页面上选 `tetrative-reconstructor` + 台数 5，等价写法 `5t5`）：

| 层级 | 单位 | 方块 | 台数 | 单台/s | 产能/s | 实际/s |
|---|---|---|---|---|---|---|
| T1 | dagger | `ground-factory` | 1 | 0.0667 | 0.0667 | 0.0208 |
| T2 | mace | `additive-reconstructor` | 1 | 0.1 | 0.1 | 0.0208 |
| T3 | fortress | `multiplicative-reconstructor` | 1 | 0.0333 | 0.0333 | 0.0208 |
| T4 | scepter | `exponential-reconstructor` | 2 | 0.0111 | 0.0222 | 0.0208 |
| T5 | reign | `tetrative-reconstructor` | **5** | 0.00417 | 0.0208 | 0.0208 |

合计 **10 台兵厂、9672 电/s**，达成 **0.021/s**（瓶颈 T5）；资源按每秒：硅 42.292、塑料 26.042、钛 17.292、
surge-alloy 10.417、相织物 7.292、石墨 0.833、玻璃 0.833、铅 0.208 —— 页面 2 列都给了 `/s` 与 `/min`
（硅 2537/min）。

另一种口径 `dagger 0.05/s`：`ground-factory ×1 → additive ×1 → multiplicative ×2 → exponential ×5 →
tetrative ×12`，合计 **21 台兵厂、22872 电/s**，瓶颈在 T5；材料硅 101.5/s、塑料 62.5/s、钛 41.5/s、
相织物 17.5/s、surge-alloy 25/s …

> 兵厂的材料是"每造一个单位消耗多少"，不是每秒配方产出；台数按 `craftTime / 60` 折算成每秒。

### 3.5 抽水机（液体也能自己产）

液体需求表里每种液体可以选**外部运入**或**抽水机**，选抽水机后自动按每秒需求补台数、并把台数与耗电并进机器表：

| 抽水机 | 尺寸 | 每秒（满格水面） | 电力/s | 额外消耗 | 说明 |
|---|---|---|---|---|---|
| `mechanical-pump` | 1×1 | 7（1 格 × 0.1167/tick × 60） | 0 | — | 最省，只能抽地表水 |
| `rotary-pump` | 2×2 | **48**（4 格 × 0.2/tick × 60） | 18 | — | |
| `impulse-pump` | 3×3 | **118.8**（9 格 × 0.22/tick × 60） | 78 | — | |
| `reinforced-pump` | 2×2 | **80**（4 格 × 0.3333/tick × 60） | 0 | 氢 1.5/s | 不耗电但吃氢 |
| `water-extractor` | 2×2 | 6.6（`pumpAmount 0.11×60`，与格数无关） | 90 | — | 要地下水源，效率看地块 |
| `oil-extractor` | 3×3 | **22.5**（油，`0.25×60×1.5`） | 180 | 沙 1/s + 水 9/s | 要油田（满黑沙属性） |

> **多格泵按有效水格数缩放**：`Pump.java:162` 是 `amount * pumpAmount * edelta()`，amount = 有效水格数；
> 所以 2×2 回转泵是 4 格、3×3 脉冲泵是 9 格，不能只乘 60（只乘 60 会低估 4 倍 / 9 倍，2026-11-09 已修）。
> 深水（`liquidMultiplier 1.5`）还要再 ×1.5：回转泵在深水上 72/s、浅水上 48/s。
> `water-extractor`/`oil-extractor` 是 `SolidPump`/`Fracker`，走 `pumpAmount * delta() * fraction`，与格数无关。
> **石油钻井要看地板属性**：`Fracker` 继承 `SolidPump`，每秒 = `pumpAmount × 60 × Attribute.oil`。
> 满黑沙（`darksand` 1.5）就是 `0.25×60×1.5 = 22.5` 油/s；游戏 UI 印的 15/s 只是
> `pumpAmount×60`（属性 1.0 的乐观值，和钻头 UI 同一类坑）。属性表：
> `sand-floor` 0.7 / `darksand` 1.5 / `salt` 0.3 / `shale` 2.0。
> 口径对照：煤炭分离机吃 6 油/s，**3 台离心机（18 油/s）只需 1 台石油钻井**（用户 2026-11-09 指出；
> 按 15/s 会算成 2 台钻井）。
> **已真机实测**（v160.7，`MBO/spikes/sim/oil_floor_probe.py`，见 `../MBO/docs/24-石油钻井地板属性实测.md`）：
> darksand 1.5 → **22.502 油/s**、sand-floor 0.7 → **10.502**、shale 2.0 → **30.002**（偏差 0.0%）；
> 同一场景 `coal-centrifuge` 吃 5.999 油/s、产 2.045 煤/s ⇒ 3:1 得到实测确认。

> 泵的台数会迭代收敛：泵自己也吃液体（抽油机吃水、强化泵吃氢），所以补台数时会重算几轮。


### 3.6 液体自产（不允许外部输入时，自动带出「煤炭处理线」）

机器要的液体**没人供**时，可以让它自己产：`--liquids auto`（网页上是「液体自产」勾选）。
默认**钻井优先**（有钻井就用钻井，没有钻井才用转化方块），也可以逐种指定：

```bash
# 煤炭 2/s：原版没有"煤矿"，煤只能靠煤炭分离机（3 油 → 1 煤），于是自动接石油钻井
node cli.cjs --item coal --rate 2 --boundary none --liquids auto
#   产出：coal 2/s
#   coal-centrifuge ×1（电 42/s），吃 oil 6/s
#   pulverizer ×1（电 30/s），吃 scrap 1.5/s    ← 钻井要沙，沙没边界就走粉碎机（吃废料）
#   工厂合计：2 台，电力 252/s（含抽水 180/s）
#   抽水：mechanical-pump ×2 + oil-extractor ×1（电 180/s），吃 sand 1/s + water 9/s
#   外部电力：电力 252/s ≈ combustion-generator 5 台（合计 300/s，富余 48/s）
#   边界输入：scrap 1.5/s
#   液体自产：石油 ← oil-extractor ×1（钻井 22.5/s）
#   液体自产：水 ← 小泵 2 台（钻井合计 14/s）
#   泵换算：水 9/s ≈ 小泵 2 台（合计 14/s，富余 5/s）

# 换孢子压缩：石油不钻井，用孢子压（spore-press 吃 spore-pod，再往上自动展开种植机）
node cli.cjs --item coal --rate 6 --boundary none --liquid oil=make
#   coal-centrifuge ×3 / cultivator ×5 / spore-press ×1（coal 6/s 时）
#   coal 2/s 时：coal-centrifuge ×1 / cultivator ×5 / spore-press ×1
#   工厂合计：7 台，电力 502/s（含抽水 18/s）
#   外部电力：电力 502/s ≈ 蒸汽发电机 1 台 + 燃烧发电机 3 台（合计 510/s，富余 8/s）
#   液体自产：石油 ← spore-press ×1（转化方块 18/s）
#   液体自产：水 ← 中泵 1 台 + 小泵 6 台（钻井合计 90/s）
```

| 参数 | 作用 |
|---|---|
| `--liquids auto` | 打开液体自产（不打开时行为和以前一样：液体只算外部运入） |
| `--liquid oil=make` | 逐种指定：`auto` / `pump`（钻井）/ `make`（转化方块）/ `import`（外部运入） |
| `--liquid oil=make:spore-press` | 方式 + 方块名 |
| `--liquidname oil=spore-press` | 只指定方块名，方式仍按 auto 判 |
| `--attr oil=0.7,water=1.2` | 环境属性（`Attribute.*`）：抽液方块每秒 = `pumpAmount×60×(validTiles+属性)`。oil 默认 1.5（满黑沙 ⇒ 石油钻井 22.5/s）、water 默认 1（地下水抽取器 6.6/s） |
| `--oilfloor 0.7` | 旧写法，等价于 `--attr oil=0.7`（保留，别打断已有脚本） |

- 产线数据（`data/gamedata.js`）：`coal-centrifuge` 30 帧、吃 oil 6/s、出 coal 2/s（3 油换 1 煤）；
  `oil-extractor` **22.5/s**（吃沙 1/s + 水 9/s，要油田，按满黑沙属性 1.5 算；游戏 UI 印的 15/s 是
  `0.25×60` 的乐观值，见 §3.5）；`spore-press` 20 帧、吃 spore-pod 1、**出 oil 18/s**
  （数据里 `outputLiquids` 是 **per-tick**：0.3/tick × 60 = 18/s，不是 ×cyclesPerSecond 的 0.9/s）。
- 输出里会写「边界输入：…、石油 6/s（液体，外部运入）」和「液体自产：石油 ← oil-extractor ×1（钻井 22.5/s）」——
  **液体一律显示中文名**（`names.liquids`，来自 `bundle_zh_CN.properties` 的 `liquid.<名>.name`：水/矿渣/石油/冷冻液/
  瘤液/芳油/镓液/臭氧/氢气/氮气/氰气）；JSON 输出里仍是英文键（`water`/`slag`/`cryofluid`…），脚本对接不受影响——
  **液体也是边界**：写进 `--boundary` 就不再抽/压（煤处理线止于分离机），页面上点液体芯片即可切换；
  液体图标用原版 `sprites/items/liquid-<名>.png`（11 种全有，UI 用 `ui/liquid-<名>-ui.png` 兜底），
  拿不到贴图时才退回 `knowledge/00-data/liquids.json` 的 `colorHex` 色点。

### 3.6.1 其它液体也递归（冷冻液、矿渣…）

液体来源不只是水/油：**转化方块的物品入料现在会回到物品递归图里继续展开**（用户 2026-11-11）。
以前的混合厂只把转化方块的入料记成「按外部输入计」，于是 `--mix differential-generator:1 --liquids auto`
只会建 `cryofluid-mixer`、把 titanium 当外部输入，**冷冻液的水从哪来就没交代**。

```bash
# 矿渣：slag-centrifuge 吃 slag 40/s → melter ×4 产 slag 12/s → melter 吃 scrap 24/s
node cli.cjs --mix "slag-centrifuge:1" --boundary sand --liquids auto
#   melter ×4（电 240/s），吃 scrap 24/s
#   边界输入：sand 0.5/s、scrap 24/s
#   液体自产：矿渣 ← melter ×4（转化方块 12/s）
#   ⚠ scrap 没有配方产出，按外部输入处理        ← 原版 scrap 只能回收/挖，链到这里为止是正常的

# 石油不钻井、用孢子压：spore-press 吃 spore-pod → cultivator ×5 吃水 90/s → 中泵 1 + 小泵 6
node cli.cjs --mix "coal-centrifuge:1" --boundary none --liquids auto --liquid "oil=make"
#   cultivator ×5（电 400/s），吃 water 90/s → spore-pod 3/s
#   液体自产：石油 ← spore-press ×1（转化方块 18/s）
#   液体自产：水 ← 中泵 1 台 + 小泵 6 台（钻井合计 90/s）
```

实现上混合厂改成了**外层不动点**：物品展开 → 液体自产 → 把转化方块的物品入料塞回物品根 → 重新展开，
直到入料不再变化（通常 2 轮）。单目标模式（`--item/--block`）本来就是这个行为，只有混合厂缺这一步。

| 液体 | 来源方块（吃料） | 备注 |
|---|---|---|
| 水 water | 抽水机 / `vent-condenser`(30/s) / `electrolyzer` 副产 | 默认钻井优先 |
| 石油 oil | `oil-extractor`(22.5/s，吃沙+水) / `spore-press`(18/s，吃 spore-pod) | |
| 冷冻液 cryofluid | `cryofluid-mixer`(12/s，吃 titanium 1 + **水 12/s**) | 水会继续递归成抽水机 |
| 矿渣 slag | `melter`(12/s，吃 scrap 1/s) | scrap 无物品配方，链止于边界 |
| 镓液 gallium | `slag-centrifuge`(1.002/s，吃 sand 1 + slag 40/s) | 矿渣再递归到 melter |
| 臭氧/氢气 | `electrolyzer`(4.002 / 6 /s，吃水 10/s) | 两者同时产出 |
| 氮气 nitrogen | `atmospheric-concentrator`(16/s) | 无入料，只耗电 |
| 氰气 cyanogen | `cyanogen-synthesizer`(12/s，吃 graphite 1 + **芳油 160/s**) | 芳油只能外部运入 |
| 瘤液 neoplasm / 芳油 arkycite | 无 | 只能外部运入（进边界） |

### 3.7 分离机 / 解离机也在递归树里（默认不自动用）

这两台是"一次随机出一件、按份额加权"的多产物方块，以前只能当 `--src` 的来源，**不进递归树**。
现在它们正式成为候选配方：页面的「指定配方」下拉里能看到 `separator` / `disassembler`，
选了就会展开它自己的输入（矿渣 / 废料），递归树上标出**份额**和**顺带产物**。

```bash
node ratio-calc/cli.cjs --item graphite --rate 1 --boundary "coal,sand" --force graphite=separator
#   产出：graphite 1.143/s
#   separator ×4（电 264/s）
#   边界输入：slag 16/s（液体，外部运入）
#   顺带产物：copper 2.857/s、lead 1.714/s、titanium 1.143/s（多产物方块副产，不算进需求）
```

算法口径（`core.js`）：

| 环节 | 怎么算 |
|---|---|
| 台数 | 按目标产物的**份额**反推：`ceil(需求 / (cps × share))`，如石墨占分离机 16.67% ⇒ 1/s 要 4 台 |
| 输入 | 按**台数**展开（每台吃一份），不吃"份额"；分离机吃矿渣 4/s、解离机吃废料 4/s + 矿渣 7.2/s |
| 副产 | 其它产物记成 `byproducts`（页面/命令行/卡片都单列），**不进需求**、不会递归展开 |
| 电力 | 台数 × 单台耗电（分离机 66、解离机 240），进总电力 |

- **默认不自动参与**：铜/铅/钛、沙子这些"没有普通工厂能干"的物品，如果自动用分离机，`lead 2/s`
  就会被算成"建 5 台吃 20/s 矿渣的分离机"，把本该挖矿的产物全带偏。所以只有两种方式让它上：
  - 在页面「指定配方」里把它选给某个物品（或 CLI `--force item=separator`）；
  - CLI `--multi` / 页面「分离机/解离机参与递归」开关 —— 打开后才允许自动挑选。
- 不指定时，`lead 2/s` 仍按外部输入处理，并提示「分离机/解离机能产它，要展开请指定配方或加 --multi」。
- **泵按加和计量、富余优先**：水这类液体按「几台小泵 + 几台中泵 + 几台大泵」算，先让**富余最小**、富余相同再比台数少（`core.pumpMix`）。
  例：`water 9/s ≈ 小泵 2 台（合计 14/s，富余 5/s）`、`18/s ≈ 小泵 3 台（21/s，富余 3/s）`、
  `90/s ≈ 中泵 1 台 + 小泵 6 台（合计 90/s，富余 0）`、`630/s ≈ 中泵 7 台 + 小泵 42 台（630/s，富余 0）`
  （2026-11-09 按用户口径从"台数最少"改成"富余最小"，两者对 9/s 的差别是 中泵 1 台富余 39 vs 小泵 2 台富余 5）；
  机械泵=小泵（7/s，不吃电）、回转泵=中泵（48/s，18 电）、脉冲泵=大泵（118.8/s，78 电），
  强化泵（80/s，要氢）与地下水抽取器（6.6/s，要地下水）只在命令行里出现，不进卡片的加和行。
- **外部电力也按发电厂加和计量**：`powerMix`（`core.js`）把「还要从外面接多少电」换算成
  `燃烧发电机 / 蒸汽发电机 / 差速发电机` 的最省组合，同样是富余优先、再台数少。
  例：`电力 252/s ≈ 燃烧发电机 5 台（合计 300/s，富余 48/s）`、`646/s ≈ 蒸汽发电机 2 台（660/s，富余 14/s）`、
  `1080/s ≈ 差速发电机 1 台（1080/s，富余 0）`。页面供电表、CLI、卡片都显示这一行。

  页面供电表与卡片那一行都带**发电厂贴图**（`blockIcon` 以前只查物品工厂，
  发电机/钻头/泵/多产物方块都取不到图，2026-11-09 修）。
- **机器表多一列「吃料/s」**：每台机器吃多少东西直接写在行里
  （`coal-centrifuge ×3 → 吃 oil 18/s`、`oil-extractor ×1 → 吃 sand 1/s + water 9/s`），
  CLI 文本、页面机器表、卡片抽水节都带。泵行的「单台产出/合计产出」也修好了
  （以前泵行单台产出恒显 0、合计只写「—」）。
- **钻井吃的沙本来就计算在内**：钻井的 `inputs`（sand）从一开始就进了递归需求
  （沙没进边界就自动接粉碎机吃 scrap；进了边界就写在「边界输入」），
  只是以前机器行不显示，看起来像没算。
- **环境属性可调（`--attr`，旧名 `--oilfloor`）**：抽液方块（`Fracker` / `SolidPump`）的每秒产量是
  `pumpAmount × 60 × (validTiles + Attribute.X)`，所以地板/水源属性直接决定台数。
  - oil 默认 **1.5（满黑沙）= 22.5 油/s**；改成 0.7（沙地）= 10.5 油/s，`coal 6/s` 就从 1 台钻井变 2 台；
    2.0（页岩）= 30 油/s。
  - water 默认 1（地下水抽取器 `0.11×60×1 = 6.6/s`），改成 1.2 就变 7.2/s。
  - 统一入口 `--attr oil=0.7,water=1.2`；`--oilfloor 0.7` 是 `--attr oil=0.7` 的旧写法，两条命令输出完全一致。
  - 页面是「环境属性」两个数字框（oil / water，`?oilfloor=0.7&waterfloor=1.2` 也能预设）；
    CLI 多打一行「环境属性：oil 0.7（oil-extractor 10.5/s）、water 1（water-extractor 13.2/s）」；
    卡片抽水节注一行（`_attr_note`）。
  - 水属性只对**显式指定的**泵生效：自动加和里只有机械泵/回转泵/脉冲泵，
    地下水抽取器要 `--liquid water=pump:water-extractor` 才会被选。
- **物品工厂现在会写产出**：以前产出行被 `kind !== "item"` 挡掉，`pulverizer` 只写「吃 scrap 1.5/s」
  不写「→ sand」，看起来沙凭空消失（用户 2026-11-09 就因此问过"油井的沙算了吗"）。
  现在写成「吃 scrap 1.5/s → sand 1.5/s」。
- **混合厂的液体不再算两遍**：`expandMixed` 曾把目标方块的输入液体同时记进 `machines`（`liquidDemand` 读）
  和 `liquidExtra`（`recalcPower` 也读），3 台离心机的油算成 36/s，于是同时打「外部运入 oil 13.5/s」
  和「液体自产 oil 22.5/s」。现在只走 `machines` 一条路（与 `expandBuilding` 第 705 行同一个坑的注释一致）。
- **抽水机不算工厂配比**：钻井/泵在机器表里单列一行「抽水：…」（电力仍计入合计，写在「含抽水 X/s」里），
  所以「工厂合计 N 台」只数真正的工厂机器。
- **孢子路线的配比（即"513"）**：3 台分离机吃 18 油/s ⇒ 1 台压缩机（18 油/s，同时吃 3 孢子/s）⇒ 5 台培养基（0.6 孢子/s 各）
  ⇒ **培养基 : 压缩 : 分离 = 5 : 1 : 3**，水 90/s，即 **15 水 / 煤**。
  `--item coal --rate 6 --liquid oil=make` 就是这个比例（望远镜看：5 台培养基、1 台压缩机、3 台分离机）。
- **液体来源在页面上可以直接选**：每行液体一个下拉，选项是「外部运入 / 抽水机 · 方块名 / 转化 · 方块名」，
  选转化方块（`spore-press` / 电解槽之类）等价于 `--liquid oil=make:spore-press`；
  命令行的 `__ratio.liq("oil", "make:spore-press")` 是同一个入口。
- 液体递归（2026-11-11 已修）：混合厂里转化方块的物品入料以前按**外部输入**计并给 warning，
  现在会回到物品递归图继续展开（见 §3.6.1）；只有真的没有配方的物品（scrap 这类）才落回边界 + warning。


### 3.8 环检测（循环产线会被标出来，不会无限展开）

配方图里可能存在环（这台机器的产物是那台的原料、那台又吃回来）。`core.js` 有两层防护：

| 层 | 函数 | 做什么 |
|---|---|---|
| 递归展开时 | `makeExpander().need()` 的 `path` | 已经走过这条路就停：节点标 `reason:"cycle"`、`node.cycle` 记 `A ← B ← A`，缺的量按**外部输入**记，不再展开 |
| 结果成型后 | `detectCycles(idx, machines)` + `attachLoops` | 只看**已建出来的**方块，沿「方块 → 它吃的物品 → 谁能产这个物品」找回到起点的路径（≤8 步），结果放 `res.loops = [{path:[…], items:[…]}]` 并推一条 warning |

展示方式：

```
#   ⚠ 循环产线：reinforced-pump -[ hydrogen ]-> electrolyzer -[ water ]-> reinforced-pump
#     （环内互相供料；环里产不抵耗的部分已按外部输入记）
```

- 递归树上出现 `⟲ 循环（环内自供，不再展开）` 标签，下一行写环链 `reinforced-pump ← electrolyzer ← reinforced-pump`；
- 卡片单列一节「循环产线（环内互相供料，缺的按外部输入记）」。

```bash
node ratio-calc/cli.cjs --item coal --rate 6 --boundary none --liquids auto \
  --liquid oil=make:spore-press --liquid water=pump:reinforced-pump
#   抽水：reinforced-pump ×2 + electrolyzer ×1（强化泵要氢，电解槽吃水又产氢 ⇒ 成环）
#   ⚠ 循环产线：reinforced-pump -[ hydrogen ]-> electrolyzer -[ water ]-> reinforced-pump
```

- **真实数据里没有纯物品环**：煤炭分离机吃油、解离机吃废料、熔炉吃废料，都是单向；
  能成环的只有**液体**（强化泵吃氢 ↔ 电解槽吃水又产氢），所以这个功能主要对付液体环。
- **不自动解环**：环内台数由外部输入兜底（警告里写「产不抵耗的部分已按外部输入记」），
  自动解环要解方程，暂不做；工具只负责**告诉你环在哪**，别把环当成免费产能。


### 3.9 归一化（`--flow`：分数台数，按物品每秒算）

前面所有算法都是「**整台 + 满效**」：要 1 石墨/s 就建 2 台压机（每台真实跑到 66.7%）。
`--flow`（页面「归一化」勾选框）换成另一种口径——学 TMI 的配比图：**台数不取整，给满效等价的小数台数**，
所有物品/液体数量都按每秒精确守恒。

```bash
node ratio-calc/cli.cjs --item graphite --rate 1 --boundary "coal,sand" --flow
#   graphite-press ×1.5（整台 2 台 ⇒ 每台 75%），吃 coal 2/s → graphite 1/s
#   工厂合计：1.5 台
#   归一化：台数为满效等价值（可为小数），数量按每秒守恒；整台建时每台效率 = 小数台数 / 向上取整

node ratio-calc/cli.cjs --item coal --rate 6 --boundary "none,sand" --liquids auto --flow
#   coal-centrifuge ×3（电 126/s），吃 oil 18/s → coal 6/s
#   抽水：mechanical-pump ×1.03（整台 2 台 ⇒ 每台 51.5%） + oil-extractor ×0.8（整台 1 台 ⇒ 每台 80%）（电 144/s）
#   液体自产：oil ← oil-extractor ×0.8（钻井 22.5/s）
```

两种口径的分工：

| 模式 | 回答的问题 | 台数 | 速率 |
|---|---|---|---|
| 默认（整台） | 「要建几台机器」 | 整数（向上取整） | 只保证够用，多出来的是富余 |
| `--flow`（归一化） | 「每秒各物品要多少」 | 小数（满效等价） | 精确，守恒 |

- `--flow` 下泵也归一化：不再拆「小泵 2 台」这种整数组合，而是 `小泵 1.03 台`（总量正好 7.2/s）；
- 台数后面那句「整台 N 台 ⇒ 每台 P%」就是**真按整数建时的等效效率**（`P = 小数台数 / 向上取整`）；
- 页面：勾「归一化 · 分数台数」（`?flow=1`），机器表台数列会写 `1.5（整台 2）`；卡片同一口径；
- 军事/兵厂链（`5t5` 反推）仍然是整数台，归一化只管物品与液体产线。

### 4. 贴图原尺寸（优先 `-full` 大图）

方块/兵厂/发电厂/单位优先用 `sprites/generated/block-<名>-full.png`、`unit-<名>-full.png`（原版高清整图，
256 张方块 + 67 张单位），没有再回退到 `blocks/**`、`units/<名>-base.png` / `-cell.png`；物品用 `items/item-<名>.png`。
页面按 `size × 32px` 显示（1×1=32、2×2=64、3×3=96、4×4=128、5×5=160），不缩放。
同时导出中文名（`assets/bundles/bundle_zh_CN.properties`，493 条），页面标签显示「英文名 + 灰字中文名」，
物品/建筑选择格的 tooltip 也带中文。

### 5. 混合厂（多个目标合并算上游，共享产物只建一份）

前三个模式一次只算**一个**目标。混合厂一次给**多个目标**（物品工厂、兵厂、发电厂都能混），
把它们的上游需求**合并成一份**再取整，所以两边都要用的中间产物只建一份，而不是各建一份再相加。

**兵厂就当普通工厂算**（用户 2026-11-10 定）：目标写兵厂时按「台数 × 生产计划」算单位产出与吃料
（升级厂按 `craftTime` 折算），材料照常进同一张共享递归图；单位本身不是中间物品，不参与目标间抵扣。
想要 T1→T5 每级几台那种纯台数比例，用「兵厂大循环」页（选 T5 兵厂 + 台数）——它按最慢一级反推各级台数。

```bash
# 硅电弧炉 1 台 + 碳化物坩埚 1 台：两边都要吃石墨
node cli.cjs --mix "silicon-arc-furnace:1,carbide-crucible:1"
node cli.cjs --mix "graphite-press:3,silicon-arc-furnace:1"          # 目标之间互供
node cli.cjs --mix "silicon-smelter:2,combustion-generator:1"        # 混一台发电厂
node cli.cjs --mix "ground-factory:2,silicon-smelter:1" --boundary "coal,sand,lead"
#   兵厂按普通工厂算：2 台陆战厂吃硅 1.333/s、铅 1.333/s；硅由 1 台硅炉（1.5/s）抵扣，不进边界
python -X utf8 card.py --mix "silicon-arc-furnace:1,carbide-crucible:1" --out mix.png
```

网页上是第三个页签「混合厂（多个目标）」：点建筑格只选中、点「加入清单」进目标列表，再点「算」。
URL 预设：`index.html?mode=mixed&mix=silicon-arc-furnace:1,carbide-crucible:1`
液体自产：`index.html?item=coal&rate=2&liquids=auto`

算法（`core.js` 的 `expandMixed`，和单目标共用同一套 `servable` / `chooseProducer`）：

1. **先合并、后取整**：按速率把各目标的上游需求累加成一张 `rate[物品]` 表，然后在**汇总速率**上
   一次性 `ceil` 出机器台数。单目标各算各的时，两边各 `ceil` 一次会把小数部分浪费掉，这是混合厂省机器的来源。
2. **目标互供抵扣**：一个目标的产出先顶掉别的目标对同一物品的需求（`internals`），扣完还缺才另外建。
3. **配方复核**：汇总速率可能改变"哪个配方更划算"（比如石墨够多时改用 multi-press），所以整轮重算，
   直到配方不再变化（实际 1~2 轮收敛，上限 6 轮，不收敛会给 warning）。
4. **对比分别建**：同时把每个目标单独展开一遍，给出「机器 13 → 12（省 1）、占地 62 → 58 格（省 4）」。

实测（默认边界 `coal, sand, tungsten`，蓝带入料）：

| 目标 | 合并后机器 | 电力 | 分别建 | 省 |
|---|---|---|---|---|
| `silicon-arc-furnace×1 + carbide-crucible×1` | `graphite-press×10` + 两个目标 = 12 台 | 420/s | 13 台 | 石墨压机 11 → 10（省 1 台、4 格） |
| `graphite-press×3 + silicon-arc-furnace×1` | `graphite-press×3` + 电弧炉 = 4 台 | 300/s | 6 台 | 目标自产石墨 2/s 已够吃 1.2/s，省 2 台 |
| `silicon-smelter×2 + combustion-generator×1` | 硅炉×2 + 发电机×1 | 用 60、发 60、净 0 | 3 台 | 无共享，只核电力 |

边界输入也算在一起：上表第一行 `coal 13.31/s + sand 4.8/s + tungsten 3.636/s`。

## URL 预设

```
index.html?mode=building&block=graphite-press&count=2&depth=4
index.html?block=graphite-press&count=2&src=coal:drill:laser-drill:8:0&gen=combustion-generator&genfuel=coal
index.html?block=silicon-smelter&count=3&boundary=coal,sand&src=sand:multi:disassembler&gen=steam-generator
index.html?block=silicon-smelter&count=3&src=sand:drill:laser-drill:8:1&src=water:pump:rotary-pump
# 兵厂大循环（等价于「选中 T5 兵厂 + 台数 5」）
index.html?chain=dagger&chainexpr=5t5
index.html?mode=building&block=tetrative-reconstructor&count=5
index.html?mode=item&item=silicon&rate=1
index.html?mode=item&item=graphite&rate=1&src=coal:belt:belt-blue
index.html?mode=item&item=silicon&rate=5&force=silicon=silicon-crucible
# 混合厂（多个目标合并算上游）
index.html?mode=mixed&mix=silicon-arc-furnace:1,carbide-crucible:1
```

`src` 格式：`物品:drill:钻头:矿格数:是否加水(0/1)` / `物品:multi:方块` / `物品:import` / **`液体:pump:抽水机`**，多项用逗号分隔（页面上的液体来源下拉就是往这里写 `pump:`）。

## 接入 bot（四种接法）

网页只是壳，算法在 `core.js`；bot 侧随便用下面任意一种，**结果完全一致**（同一份 `core.js`，`test_cli.cjs` 里有逐项对拍）。

### 1. 命令行（最省事，subprocess 直接调）

```bash
node ratio-calc/cli.cjs --item silicon --rate 5
node ratio-calc/cli.cjs --block graphite-press --count 2 --format json
node ratio-calc/cli.cjs --block silicon-smelter --count 3 --boundary coal,sand \
     --src sand=drill:laser-drill:8:1 --gen steam-generator --genfuel coal --format md
node ratio-calc/cli.cjs --block tetrative-reconstructor --count 5   # 选兵厂 + 台数 = 大循环
node ratio-calc/cli.cjs --chain dagger --chainexpr 5t5              # 等价写法
node ratio-calc/cli.cjs --item graphite --rate 1 --src coal=belt:belt-grey
node ratio-calc/cli.cjs --block silicon-smelter --count 3 --src sand=drill:laser-drill:8 \
     --src water=pump:rotary-pump --format md   # 水自己抽
node ratio-calc/cli.cjs --list          # 列出物品/工厂/兵厂/发电厂/钻头/多产物/抽水泵/兵厂链
```

| 参数 | 说明 |
|---|---|
| `--item X --rate N` | 按目标产物速率算（次模式） |
| `--block X --count N` | 按满效建筑台数算（主模式）。**选兵厂时自动走 T1→T5 大循环**：`count` 就是这一级的台数 |
| `--plan N` | 兵厂有多个生产计划时选第 N 个（默认 0）；`--block ground-factory --plan 1` 就是 crawler 线 |
| `--chainline 单位` | 一台重建厂能升多条线时指定升级线（默认优先 dagger 线） |
| `--chain 单位 --chainexpr 5t5` | 兵厂大循环，给台数（5 台 T5 厂满效），反推 T4/T3/T2/T1 台数与整链资源 |
| `--chain 单位 --chainrate N` | 同上，但按每秒几个顶级单位给 |
| `--src 物品=belt:belt-grey` | 外部运入细分成带子/接收台：`belt-grey`(5.25/s)、`belt-blue`(12.015/s)、`belt-green`(40/s)、`phase-bridge`(30/s，18 电)、`mass-driver`(36/s，105 电)、`pad`(不限)、`other`(不限) |
| `--boundary a,b` | 外部输入的物品；不写默认 `coal,sand`；`all` = 所有矿，`none` = 全部自产 |
| `--src 物品=drill:钻头:矿格数:0/1`<br>`--src 物品=multi:分离机/解离机`<br>`--src 物品=import` | 每项边界输入从哪来（可重复） |
| `--src 液体=pump:抽水机` | 液体（水/油）自己抽，自动补台数并计入电力（可重复） |
| `--force 物品=方块` | 指定多配方物品用哪个方块 |
| `--depth N` | 递归层数（超过的按外部输入） |
| `--gen 发电厂 --genfuel 燃料 [--gencount N]` | 供电方案；台数 0/省略 = 自动补足 |
| `--format text\|md\|json` | 输出格式（`md` 是表格，适合 bot 卡片） |
| `--icons` | JSON 里保留 base64 图标（默认剔除，JSON 会小一半以上） |
| `--data 文件` | 换数据文件（默认 `data/gamedata.js`） |

退出码：成功 0，参数/数据错误 2（`--format json` 时错误也是 `{ok:false,error}`）。

### 2. HTTP（常驻服务）

```bash
node ratio-calc/serve.cjs --port 8799 --host 127.0.0.1
curl "http://127.0.0.1:8799/calc?item=graphite&rate=1"
curl "http://127.0.0.1:8799/calc?block=ground-factory&count=2&gen=steam-generator&genfuel=coal&format=md"
curl "http://127.0.0.1:8799/list?format=json"
curl "http://127.0.0.1:8799/healthz"
```

- `/calc` 接受与 CLI 同名的参数（`src` 可重复），缺 `item/block/chain` 返回 400；
- `/list` 返回清单；`/healthz` 返回 `{"ok":true}`；`Access-Control-Allow-Origin: *` 已开。

### 3. Python（bot 是 Python 时最顺）

```python
import sys; sys.path.insert(0, "ratio-calc")
import ratio

d = ratio.query(item="silicon", rate=5)                       # dict
print(ratio.text(block="graphite-press", count=2))            # 纯文本
print(ratio.markdown(chain="dagger", chainexpr="5t5"))          # 5 台 T5 厂满效
ratio.image("card.png", item="graphite", rate=2)               # 出 PNG 卡片
d2 = ratio.http_query("http://127.0.0.1:8799", item="graphite", rate=1)   # 走 HTTP 服务
```

```bash
python -X utf8 ratio-calc/ratio.py --item silicon --rate 5
python -X utf8 ratio-calc/ratio.py --block ground-factory --count 2 --image gf.png
```

`ratio.py` 用 `RATIO_NODE` 环境变量指定 node（默认 `node`），本身只用标准库。

### 4. 图（bot 直接发图）

```bash
python -X utf8 ratio-calc/card.py --item silicon --rate 5 --out card.png
python -X utf8 ratio-calc/card.py --block ground-factory --count 2 \
    --gen steam-generator --genfuel coal --scale 2 --out gf.png
python -X utf8 ratio-calc/card.py --chain dagger --chainexpr 5t5 --out chain.png
python -X utf8 ratio-calc/card.py --json result.json --out card.png   # 喂现成 JSON
```

深色主题、700px 宽（`--width` 可改，`--scale` 出 2 倍图），建筑/物品**原尺寸图标**（`size×32px`）随卡片一起画好，
不依赖 emoji 或外部字体。

**卡片正文顺序（bot 发图就用这个）**：

1. **工厂配比**（主要内容）：每台机器 `名字 ×台数 · 电力/s · 产出/s`，标题行给"共 N 台 · 电力 X/s"；
   兵厂链模式下这里是 `各级兵厂（配比结果）`，包含每级台数、单台/s、产能、实际、利用率、1 台带几台上级；
2. **外部入料（默认蓝带）**：每种边界物品一行，右侧 `X/s`，副标写 `蓝带 titanium-conveyor ×N 条（12.015/s）`、
   `钻头 ×N（加水）`、`解离机 ×N · 副产 钍 …`、`接收台 · 不限速`；
3. 液体需求（水/油/冷冻液） → 4. 供电 → 5. 提示（warnings）。

示例：`docs/card-graphite.png`(700×248)、`docs/card-silicon.png`(700×282)、
`docs/card-chain.png`(700×622)、`docs/card-chain-t1.png`(700×378)、
`docs/card-via.png`(700×248，蓝带入料)、`docs/card-pump.png`(700×414，钻头 + 抽水机)、
`docs/card-unit.png`(700×378，兵厂单级)、`docs/mix.png`(700×376，混合厂卡片)、`docs/page-mixed.png`（混合厂页签整页截图）、
`docs/card-coal.png`(700×526，煤炭 6/s：离心机×3 + 石油钻井×1（22.5 油/s）+ 吃料 sand/water + 泵换算 + 带图标的外部电力换算)、
`docs/page-coal.png`（1180×2150，页面截图：边界全物品/液体开关 + 配方下拉 + 多产物方块开关 + 环境属性两个数字框（oil / water） + 机器表「吃料/s」列 + 带发电厂图标的外部电力换算）、
`docs/card-drill.png`(700×394，钻头并入工厂配比：机器行写 coal 3.234/s)、
`docs/card-separator.png`（分离机进递归：台数按份额反推、顺带产物单列一节）、
`docs/page-multi.png`（1180×2150，页面截图：指定配方选 separator，递归树带份额与顺带产物）。

### JSON 结构（四种模式统一）

```jsonc
{
  "ok": true,
  "mode": "item | building | chain | mixed",
  "target": "silicon 5/s" ,              // 一句话描述
  "products": [{ "name": "silicon", "type": "item", "rate": 5 }],
  "machines": [{ "name": "silicon-smelter", "count": 3, "kind": "item",
                 "size": 2, "powerEach": 60, "powerTotal": 180,
                 "icon": "data:image/png;base64,…",        // --icons 时才有
                 "outItems": [{ "name": "silicon", "perSecond": 2.5, "icon": "…" }] }],
  "demand":  [{ "name": "coal", "perSecond": 3.6, "icon": "…" }],
  "liquids": [{ "name": "water", "perSecond": 12 }],       // 要自己接管线
  "liquidSources": [{ "liquid": "water", "pump": "rotary-pump", "count": 1,
                      "perSecondEach": 12, "power": 18 }],  // 选了抽水机才有
  "power": 180,
  "sources": [{ "item": "sand", "type": "drill", "drill": "laser-drill", "count": 3,
                "perSecondEach": 1.263, "liquid": { "name": "water", "perSecond": 4.8 },
                "power": 198, "byproducts": [] }],
  "supply":  { "name": "steam-generator", "count": 1, "netTotal": 330,
               "fuel": { "name": "coal", "perSecondEach": 0.667, "perSecond": 0.667 },
               "liquids": [{ "name": "water", "perSecond": 6 }] },
  "chain":   { "rows": [{ "tier": 1, "unit": "dagger", "block": "ground-factory",
                          "count": 1, "perSecond": 0.0667, "capacity": 0.0667,
                          "actual": 0.05, "utilization": 0.75,
                          "feedsNext": 0.667, "bottleneck": false }],
               "achieved": 0.05, "bottleneck": "reign", "bottleneckTier": 5,
               "materials": { "silicon": 101.5 }, "power": 22872 },  // 按最慢一段算
  // ---- 只有 mixed 模式才有的字段 ----
  "targets": [{ "block": "silicon-arc-furnace", "count": 1, "kind": "item",
                "products": [{ "name": "silicon", "type": "item", "rate": 4.8 }],
                "inputs": [{ "name": "graphite", "amount": 1.2 }],
                "power": 300, "powerOut": 0 }],
  "shared":  [{ "item": "graphite", "block": "graphite-press", "perMachine": 0.667,
                "need": 6.655, "fromTargets": 0, "netNeed": 6.655,
                "mixedCount": 10, "separateCount": 11, "saved": 1, "tileEach": 4 }],
  "internals": [{ "item": "graphite", "need": 1.2, "fromTargets": 1.2, "stillNeed": 0 }],
  "compare": { "machinesMixed": 12, "machinesSeparate": 13, "savedMachines": 1,
               "powerMixed": 420, "powerSeparate": 420, "savedPower": 0,
               "tilesMixed": 58, "tilesSeparate": 62, "savedTiles": 4,
               "detail": { "graphite-press": 11, "arc": 1 } },
  "powerOut": 0, "netPower": 420,        // 厂内发电 / 净电力（mixed 才有）
  "warnings": ["…"]
}
```

## 文件

| 文件 | 作用 |
|---|---|
| `index.html` | 单页应用（样式 + 四个模式 + 来源/供电/兵厂链/液体四块表，无第三方库） |
| `core.js` | 内核：展开、钻头/发电/多产物/兵厂链/液体算法（浏览器 + node 通用，`module.exports`） |
| `data/gamedata.js` | 导出数据 + 内联图标 + 中文名：33 工厂 / 17 兵厂 / 14 发电厂 / 10 钻头 / 2 多产物 / 6 抽水泵 / 22 物品 / 139 图标 / 11 液体图标+颜色 / 504 中文名（含 11 种液体）/ 1141.8 KB（出液量按 per-tick ×60 换算） |
| `export_data.py` | 重新导出：`python -X utf8 ratio-calc/export_data.py` |
| `make_cases.py` | 用 `mbo calc --json` 生成对拍用例 |
| `cli.cjs` | **bot 入口**：命令行 + 文本/Markdown/JSON 渲染 |
| `serve.cjs` | **bot 入口**：HTTP 服务（`/calc` `/list` `/healthz`） |
| `ratio.py` | **bot 入口**：Python 包装（`query/text/markdown/image/http_query`） |
| `card.py` | **bot 入口**：把结果画成 PNG 卡片（带原尺寸图标） |
| `test_core.cjs` | 14 项对拍 `mbo calc` + 213 项断言：钻头/发电/多产物/兵厂链/抽水机/入料方式/发电设备当目标/混合厂（含兵厂目标）/液体自产/液体递归 |
| `test_page.cjs` | 最小 DOM 桩跑页面：116 项断言，不用浏览器 |
| `test_cli.cjs` | 79 项：CLI/HTTP 与 `core.js` 逐项对拍 + 渲染 + 默认蓝带 + 液体自产/液体递归/液体中文名 + 错误分支 |
| `test_card.py` | 17 项：卡片结构（配比在前）/ 默认蓝带条数 / 0 台不建 / 行不重叠 / PNG 可渲染 / 发电卡片 / 混合厂（含兵厂）/ 液体自产 / 图标齐全 |
| `docs/screenshot-*.png` | 页面截图（Edge headless） |
| `docs/card-*.png` | PNG 卡片示例 |

## 数据从哪来

| 数据 | 来源 |
|---|---|
| 配方 / 电力 / 尺寸 | `MBO/gamedata/v160.7/gamedata.json`（反射 dump 的 v160.7 快照） |
| 兵厂 plans / 升级链 / 组装厂 | `MBO/gamedata/v160.7/units_production.json`（Rhino 反射 dump） |
| 发电厂 / 钻头 / 多产物 / 物品属性 | `MBO/gamedata/v160.7/power_drill.json`（Rhino 反射 dump） |
| 抽水泵 | `power_drill.json` 的 Pump 段（`pumpAmount` per-tick ×60；源码 `Blocks.java` 核对） |
| 液体贴图 | `assetsraw/assets-raw/sprites/items/liquid-<名>.png`（11 种），UI 版 `ui/liquid-<名>-ui.png` 兜底 |
| 液体颜色 | `knowledge/00-data/liquids.json` 的 `colorHex`（贴图缺失时才画色点） |
| 图标 | `assetsraw/assets-raw/sprites/generated/*-full.png`（优先）、`blocks/**`、`units/**`、`items/**`（原尺寸） |
| 中文名 | `assetsraw/assets/bundles/bundle_zh_CN.properties`（`item/block/unit.<名>.name`） |

## 已验证

```
node ratio-calc/test_core.cjs   → 14 项对拍 mbo calc 全部一致 + 204 项新算法断言通过（共 218 行 ok）
node ratio-calc/test_page.cjs   → 116 项页面链路断言通过（含混合厂 11 项、液体自产 5 项、液体中文名 2 项、边界开关/配方下拉、钻头并入工厂配比、多产物方块进递归树 6 项、发电厂递归树 3 项、归一化 2 项）
node ratio-calc/test_cli.cjs    → 79 项 CLI/HTTP 与 core.js 对拍通过（含 `--mix` 6 项（含兵厂目标）、液体自产 6 项、液体递归 2 项、液体中文名 1 项、钻头写入机器清单、分离机/解离机 5 项、发电厂树 2 项、归一化 2 项）
python -X utf8 ratio-calc/test_card.py → 17 项卡片结构/排版断言通过（含混合厂 3 项（含兵厂目标）、液体自产 1 项、图标 2 项、多产物副产 1 项、发电厂树 1 项、归一化 1 项）
```

对拍用例覆盖石墨/硅/合金/玻璃/塑料/爆炸物/燃烧物/相织物/孢子荚 + 3 个 `--force`；
新算法断言覆盖钻头速率（含加水、煤硬度 2）、发电台数与燃料、分离机/解离机加权产物、
来源替换后的机器表与电力重算、抽水机台数与液体来源、入料方式 7 种、`5t5` 反推（1/1/1/2/5）、
`chainsForBlock`/`chainFromBlock`（同一重建厂多线、默认 dagger、指定 flare → eclipse）、
dagger 与 stell 两条升级链、发电设备当目标建筑（蒸汽 ×2 → 660/s、冲击堆扣自耗、
燃料/液体展开成递归树：煤不在边界 → coal-centrifuge、差速发电机 → pyratite-mixer + pulverizer、
但不做「电→燃料→电」的电力递归）、
混合厂（合并上游后石墨压机 10 台 vs 分别建 11 台、目标互供抵扣省 2 台、发电厂当目标并入净电力）、
泵富余优先（9/s → 小泵 2 台富余 5、18/s → 小泵 3 台富余 3、90/s 富余 0）、外部电力按发电厂加和
（646/s → 蒸汽 2 台、1080/s → 差速 1 台）、液体也是边界（oil 进边界就不再建石油钻井）、
石油钻井地板属性（默认 1.5 → 22.5 油/s、3 台离心机只要 1 台钻井、0.7 → 2 台 10.5/s、2.0 → 1 台 30/s）、
混合厂液体只算一遍（3 台离心机 18 油/s、不再报外部运入）、
多产物进递归树（`graphite` 的候选含 separator、默认仍走压机、`--force graphite=separator` → 4 台/电 264/矿渣 16/s、
`--force sand=disassembler` → 1 台/废料 4/s、`--multi` 时 lead 2/s → 分离机 5 台、默认仍按外部输入）、
环境属性通用化（`attrsOf` 数字/对象、`--attr oil=0.7` 与 `--oilfloor 0.7` 输出相同、water 1 ⇒ 13.2/s、
非法值报「数值不对」）、环检测（`detectCycles` 报出强化泵↔电解槽、`cycleText` 文案、普通产线 `loops` 为空、
页面对应场景树里出现 `⟲`、卡片出现「循环产线」节）、
归一化 flow（graphite 1/s → 压机 1.5 台、整数模式仍 2 台、coal 6/s 下钻井 0.8 台/小泵 1.0286 台、混合厂同样归一、
卡片写「1.5（整台 2）」、CLI 写「整台 2 台 ⇒ 每台 75%」、flow 下不再给整数泵换算）。

截图用 Edge headless（Chrome headless 在这台机器上会超时被 kill）：
`--headless=new --disable-gpu --no-sandbox --window-size=1180,2000 --virtual-time-budget=5000 --screenshot=...`

## 计算规则（与 MBO 一致）

1. 台数 = `ceil(需求 / 单台速率)`，向上取整；
2. 输入递归展开，遇到边界物品停下；
3. 同一物品有多个配方时：先选"输入端也能自己造"的（不新引入边界），再选向上取整后最贴近目标的，
   再选占地小的，最后按名字定序；
4. 没有配方产出的物品按外部输入处理，并在页面上给警告；
5. `mode: "unit"` 的兵厂按 `plans` 的 `time/60` 折算每秒，材料按单位消耗 × 每秒产量。

## 已知局限

- 只算配比，不算布局/物流/传送带容量；
- 液体默认按外部输入；要自产就加 `--liquids auto`（或网页勾「液体自产」），此时钻井优先、没有钻井才用转化方块；
- 液体自产只认"一种方块供一种液体"：`reinforced-pump` 要氢这类自反馈被排序规避（优先选不吃液体的泵），不保证全局最优；
- 混合厂里的液体自产：转化方块的**物品**入料按外部输入计并给 warning（不展开那一层物品链）；
- 组装厂（`UnitAssembler`）消耗的是**方块 Payload**，这里按外部输入处理，不展开；
- 多产物是"随机出一件"的期望值，实际有波动；它默认不参与自动递归（见 §3.7），指定配方或 `--multi` 才上；
- 电力不展开成「电→燃料→电」的闭环：普通工厂的耗电只当数字（发电看独立供电表），
  发电厂当目标时才展开燃料链，且不会因为厂内自耗电再反推建更多发电机；
- 混合厂收兵厂，但兵厂之间**不互相喂单位**：T1 厂造的单位不会抵扣 T2 升级厂「吃低阶单位」那一步，
  升级厂只按自己的材料配方算；要台数比例请用「兵厂大循环」页；组装厂（Payload 方块）仍不收；
- 混合厂的"对比分别建"是按每个目标**各自独立展开**算的，不是按最优顺序分批建；先合并速率再取整，
  所以结果是"最少机器"口径，不保证最少占地（占地只作对比展示）。
