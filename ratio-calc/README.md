# 自动配比计算器（网页版）

算 Mindustry v160.7 的产线配比：给一个**目标**，算出要几台什么机器、上游每种物品多少/秒、总电力、
要几台发电厂烧多少燃料、外部原料用哪种钻头/要不要加水、兵厂 T1→T5 整条升级链要几台。
界面上的工厂、兵厂、单位、物品、发电厂、钻头全部用**原版贴图图标**（原尺寸内联 base64，不依赖外部图片）。

双击 `index.html` 就能开（不需要服务器、不需要联网）。

## 三种输入方式

| 模式 | 输入 | 适合 |
|---|---|---|
| **按建筑台数（满效）** | 选一个工厂 / 兵厂 + 台数 | "我要 4 台石墨压机满效跑" → 反推上下游 |
| **按物品速率** | 选物品 + 每秒产量 | 传统玩法："我要 5 硅/s" |
| **兵厂大循环** | 选一条 T1~T5 链 + 顶级速率 | "我要 0.05 reign/s" → 五级各要几台、材料多少 |

各模式下都能改：
- **递归层数**：上游展开到第几层（超过就当外部输入），默认 4
- **边界**：这些物品当"外部送进来"，不再展开
- **指定配方**：`物品=方块` 逗号分隔；点"多配方"表里的备选也会自动填

## 四块新功能

### 1. 外部来源可配置

边界表（页面中部"外部来源"）里，每种边界物品可以选：

- **接收（外部运入）** —— 默认，什么都不算；
- **钻头采集** —— 选钻头（10 种）+ 矿格数 + 是否加水/加氢/加氮/加臭氧/加氰；
  台数按 `60 × 矿格数 × speed² / delay` 反推，`delay = (drillTime + hardnessMult × 物品硬度)`，
  `speed` 加水时取该钻头的 `boostIntensity`（机械/气动/激光 1.6 ⇒ 吞吐 ×2.56，爆裂钻 1.8 ⇒ ×3.24）；
- **多产物 · 分离机 / 解离机** —— 这两台是"加权随机出一件"，台数按目标产物反推
  （`share = amount / Σamount`），并把**所有**副产物和输入列出来：
  - 分离机：矿渣 4/s + 66 电 → 铜 .714 / 铅 .429 / 石墨 .286 / 钛 .286 每台每秒
  - 解离机：废料 4/s + 矿渣 7.2/s + 240 电 → 沙 1.6 / 石墨 .8 / 钛 .8 / **钍 .8** 每台每秒

钻头/多产物的台数和耗电会并进机器表与总电力。

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

### 3. 兵厂 T1 → T5 大循环

10 条链（6 条原版 + 3 条 Erekir + 1 条 prime-refabricator），选链和顶级单位速率后按层级倒推：

以 `dagger 0.05/s` 为例：`ground-factory ×2 → additive-reconstructor ×1 → multiplicative ×2 →
exponential ×5 → tetrative ×12`，合计 **22 台兵厂、22944 电/s、硅 111.2/s、塑料 66.1/s、钛 47/s …**

> 兵厂的材料是"每造一个单位消耗多少"，不是每秒配方产出；台数按 `craftTime / 60` 折算成每秒。

### 4. 贴图原尺寸

方块/兵厂/发电厂按 `size × 32px` 显示（1×1=32、2×2=64、3×3=96、4×4=128、5×5=160），
不再统一缩到 32×32；物品 32×32、单位取 `units/<名>-base.png`（陆军）/ `<名>-cell.png`（飞行）。

## URL 预设

```
index.html?mode=building&block=graphite-press&count=2&depth=4
index.html?block=graphite-press&count=2&src=coal:drill:laser-drill:8:0&gen=combustion-generator&genfuel=coal
index.html?block=silicon-smelter&count=3&boundary=coal,sand&src=sand:multi:disassembler&gen=steam-generator
index.html?block=ground-factory&count=2&chain=dagger&chainrate=0.05
index.html?mode=item&item=silicon&rate=5&force=silicon=silicon-crucible
```

`src` 格式：`物品:drill:钻头:矿格数:是否加水(0/1)` 或 `物品:multi:方块` 或 `物品:import`，多项用逗号分隔。

## 文件

| 文件 | 作用 |
|---|---|
| `index.html` | 单页应用（样式 + 三个模式 + 来源/供电/兵厂链三块表，无第三方库） |
| `core.js` | 内核：展开、钻头/发电/多产物/兵厂链算法（浏览器 + node 通用，`module.exports`） |
| `data/gamedata.js` | 导出数据 + 内联图标：33 工厂 / 17 兵厂 / 14 发电厂 / 10 钻头 / 2 多产物 / 22 物品 / 129 图标 / 438 KB |
| `export_data.py` | 重新导出：`python -X utf8 ratio-calc/export_data.py` |
| `make_cases.py` | 用 `mbo calc --json` 生成对拍用例 |
| `test_core.cjs` | 14 项对拍 `mbo calc` + 29 项新算法断言 |
| `test_page.cjs` | 最小 DOM 桩跑页面：34 项断言，不用浏览器 |
| `docs/screenshot-*.png` | 页面截图（Edge headless） |

## 数据从哪来

| 数据 | 来源 |
|---|---|
| 配方 / 电力 / 尺寸 | `MBO/gamedata/v160.7/gamedata.json`（反射 dump 的 v160.7 快照） |
| 兵厂 plans / 升级链 / 组装厂 | `MBO/gamedata/v160.7/units_production.json`（Rhino 反射 dump） |
| 发电厂 / 钻头 / 多产物 / 物品属性 | `MBO/gamedata/v160.7/power_drill.json`（Rhino 反射 dump） |
| 图标 | `assetsraw/assets-raw/sprites/**`（原尺寸） |

## 已验证

```
node ratio-calc/test_core.cjs   → 14 项对拍 mbo calc 全部一致 + 29 项新算法断言通过
node ratio-calc/test_page.cjs   → 34 项页面链路断言通过
```

对拍用例覆盖石墨/硅/合金/玻璃/塑料/爆炸物/燃烧物/相织物/孢子荚 + 3 个 `--force`；
新算法断言覆盖钻头速率（含加水、煤硬度 2）、发电台数与燃料、分离机/解离机加权产物、
来源替换后的机器表与电力重算、dagger 与 stell 两条升级链。

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
- 液体默认按外部输入，不展开抽水/混合机；
- 组装厂（`UnitAssembler`）消耗的是**方块 Payload**，这里按外部输入处理，不展开；
- 多产物是"随机出一件"的期望值，实际有波动；
- 电力不展开成燃料链的闭环（发电厂烧的煤仍需自己配来源，不会自动接到钻头）。
