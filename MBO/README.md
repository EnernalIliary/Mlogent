# MBO · Mindustry Blueprint Optimizer（第一版方案）

> 目标（来自 `../MBO.md` 项目书）：**用程序生成并优化 Mindustry 工厂蓝图**——给定"要产什么、多少、多大地方"，输出一张可导入游戏、能被真机验证、指标可量化比较的蓝图。
> 核心信条：**算力决定能探索多少，经验决定值得探索什么**；规则来自真机数据，不来自 LLM 记忆。

本目录是**调研 + 第一版方案**的交付物。所有数字均为本机实测（2026-11-04，工作区 `AtomicStates`），标注了可复现脚本。

---

## 0. 一句话结论

**这件事能做，而且工作区已经提供了最难自建的三块地基**：

| 地基 | 工作区现状（实测） | 对 MBO 的意义 |
|---|---|---|
| 蓝图语料 | `logic-corpus/` **833 张** .msch，其中工厂型 **574 张**、纯工厂基线 **406 张** | 测试集 + 模板挖掘 + A 组人工基线 |
| 蓝图编解码 | `tools/msch.py` 解析 **831/833（99.76%）**；补一层 writer 后往返 **831/831** | 不用从零写 .msch 读写 |
| 真机执行器 | v160.7 服务端 + JRE21，**整张蓝图可放进真实世界、真 60Hz 推进**、可读回 efficiency/电力/库存 | "离线预测 vs 真机实测"闭环 |

缺的部分是**规则数据数字化**（craftTime、传送带/钻头参数）、**生成侧能力**（坐标语义、写回、布局求解）和**搜索层**——这些正是 MBO 要新建的，规模可控（MVP 人日估算见 `docs/02`）。

**生成侧可信度已实测**（`docs/13`）：编码/坐标/旋转三层可信；电力与读数两条链路有硬约束（不满足时蓝图**能粘贴但不产货**，且不报错）。约束已固化成 R1–R7 七条，修完后端到端产量达到理论值 99.1%。

**唯一需要先纠偏的概念**：项目书里的"钛合金"在原版 **不存在**（22 个原版物品里没有），E2 实验映射为 **`surge-alloy`（合金，配方含钛，无液体输入）**。语料里有 **19 张工厂型**样本（+2 张混合型=21，其中**零逻辑 3 张**）可做 A 组基线；这个映射需要项目书作者确认。

---

## 1. 目录结构

```
MBO/
├── README.md                       ← 你在这里（总览 + 结论 + 下一步）
├── docs/
│   ├── 00-资源盘点与复用.md         工作区有什么、能复用什么、缺什么、风险
│   ├── 01-总体架构与数据模型.md      L0–L6 七层架构、IR、求解器分工、搜索与剪枝、验证与学习
│   ├── 02-MVP路线与最小实验.md      阶段 0-6 排期、E0/E1/E2 实验协议、里程碑、风险
│   ├── 10-蓝图层与语料盘点.md       .msch 格式、msch.py 能力边界、833 张语料全量实测
│   ├── 11-游戏数据层.md             从 jar 反射 dump 的完整建筑/配方/物流参数
│   ├── 12-真机验证可行性.md         引擎内验证的能力边界、最小流程、四个坑、补测（电力/产量/锚点）
│   ├── 13-生成器可信度测试.md       从零造蓝图→真引擎：六层可信度判定 + 七条硬约束（R1–R7）
│   ├── 14-传送带与布线器实测.md     带速/方向/延迟、电力布线器、E1 生成→真机 3.05/s
│   ├── 15-工程化与三条产线实测.md    mbo CLI v0.1：石墨/玻璃/硅三条产线全 PASS、5 件产物、verify
│   ├── 16-石墨优化与物流门.md        石墨 10→6 方块：一源 + 一门的 split 模板、门语义、实测对比
│   ├── 17-石墨单出口合流.md          合流到一个出口：pair/single/vault/core/void 实测对比
│   ├── 18-石墨蓝图下界与10格最小蓝图.md  direct：10 格下界证明 + 5×2 蓝图 + 分数周期计量
│   ├── 19-端口在外与物流限速.md      端口只能在外 + 速率由物流决定：8/4、9/3、12/2 三条前沿
│   ├── 20-原版贴图预览.md            用 assetsraw 原版贴图渲染 preview（缺图自动回落色块）
│   ├── 21-脚本化搜索与一条命令出图.md  mbo opt：枚举 6195 候选 → Pareto → 选优 → 真机验证
│   ├── 22-四核石墨线.md              4 台压机 = 2.67/s：8 端口/16 格 与 6 端口/18 格两档真机 PASS
│   └── 90-审阅意见.md               独立审阅：8 条阻断 + 10 条建议（全部已落地，留作痕迹）
├── mbo/                            ← 工程化实现（CLI v0.1）
│   ├── gamedata.py / codec.py / model.py / production.py
│   ├── layout.py / validate.py / engine.py / report.py / cli.py
│   ├── logistics.py / preview.py / sprites.py / search.py
│   └── __main__.py                 入口：python -m mbo calc|gen|opt|verify|preview|build-snapshot
├── gamedata/v160.7/                ← 版本化数据快照（gamedata.json + meta.json，带 sha256）
├── tests/test_mbo.py               ← 68 项单元测试（python -m unittest discover -s MBO/tests）
├── runs/<run_id>/                  ← 每次 gen 的 5 件产物（msch / b64 / metrics / report / trace）+ preview.png（原版贴图）
├── runs/index.html                 ← mbo preview --all 生成的画廊
├── spikes/                        ← 调研期的一次性脚本（可复现每个数字）
│   ├── bp/scan_corpus.py          全量语料扫描 + 往返测试（40s）
│   ├── bp/corpus_report.json      机器可读结果
│   ├── data/extract_game_data.py  从服务端 jar 反射 dump 游戏数据
│   ├── data/gamedata.json         数据层种子快照（v160.7）
│   ├── data/compare_data.py       三方交叉校验（新 dump / 旧 data-game / 游戏速查）
│   └── sim/engine_probe.py        真机引擎探针（蓝图入世界→跑 tick→读状态）
│   └── gen/                       生成器原型：gen_trust.py / belt_probe.py / gen_e1.py / gate_probe.py / api_probe.py
└── proto/
    └── mini_calc.py               生产计算器原型（已跑通，见 §3）
```

---

## 2. 核心实测数字（先看这一节就够判断可行性）

**语料**（`spikes/bp/scan_corpus.py` 全量 833 张，约 40 s）

- 解析 **831/833（99.76%）**；2 个文件 zlib 流损坏不可修复（foxitOS 包里）
- 分类：工厂型 **574** / 混合 **180** / 纯逻辑 **77**；含生产方块 527；**纯工厂（零逻辑）406**；覆盖率 ≥0.90 的 **276**
- 单张 tile 中位 40（工厂型 56），最大 4795；工厂方块覆盖率中位 **95.6%** → 人类蓝图极其紧凑，这是 B 组要挑战的硬指标
- 产物覆盖 **13 种**（工厂型口径）：silicon 114、pyratite 110、coal 94、spore-pod 63、graphite 60、plastanium 59、phase-fabric 37、metaglass 36、blast-compound 34、**surge-alloy 19**、sand 14、oxide 4、carbide 1
- v160.7 缺失方块只影响 8 张（0.96%）：`alloy-smelter`（旧名，→ surge-smelter）、`thermal-pump`

**写回**（决定能不能"生成"蓝图）

- 现成 `msch.build_schematic`：往返 **230/831（27.68%）**，失败原因唯一——`cannot serialize config of type list`（电力节点的连接点数组）
- 本调研补的 writer：**831/831 语义往返**，**830/831 body 逐字节一致**；实现只需保留 TypeIO tag 号 + 补 4 个数组分支

**游戏数据**（`spikes/data/gamedata.json`，从 `out/_server160.jar` 反射 dump）

- 447 方块中：**33 个配方方块**（craftTime 全 >0；29 有 IO、**27 输入输出完整**）、**107 个耗电**、**15 个发电**（含沙盒 `power-source`，真发电机 14）、92 个可旋转
- 关键发现：**原版没有"多物品产出"的配方**（0 个）；液体输入不在 `recipe.inputs` 而在 `consumers`；craftTime 单位是**帧**，`cyclesPerSecond = 60/craftTime`
- 物流参数：12 种传送带里 9 种有 items/s（conveyor **5** / titanium 10 / armored 10 / duct 4…），10 个钻头全部有 `drillTime`、8 个有 `tier`（`docs/11` §5.4）。真机实测 conveyor 稳态 **4.9 items/s**、单格容量 3，与 UI `displayedSpeed=5` 吻合（`docs/14`）
- 交叉校验（`compare_report.json`）：旧 `data/game` 的 `craftTime` **447 个全为 -1**；`docs/游戏速查/方块配方.md` 的**耗电列是"每 tick"，不是每秒**（107 行按 tick 全对、按秒只对 5 行）——直接抄会差 60 倍

**真机验证**（`spikes/sim/engine_probe.py`）

- 整张 .msch → `Schematics.readBase64` + `place(sch,x,y,team,true)` → 真 60Hz 推进（实测 60.1–60.3 tick/s）
- 成本：JVM 启动 1.8–2.3 s、造世界 0.5 s、**1800 tick ≈ 33 s**；**每 JVM 首张图必须付 warmup ~13 s，端到端单次约 46 s**；内存 ~150 MB → 可并发（4–6 进程）
- 能验证：蓝图能否落地、缺料/堵死（`efficiency`/`progress`）、电力平衡（`graph.satisfaction/production`）、液体吞吐
- **产量读数已闭环（补测）**：产物汇入 container/vault/core 后按 `build.items` 差分 → 稳态 0.684/s vs 理论 0.667/s（**+2.6%**）；`progress` 回绕计数与容器计数完全一致（可作交叉校验）
- **电力连线已定论（补测）**：放置蓝图**不会**自动连线（空 config 的 4 个电力方块 = 4 张独立电力图、links 全 0、sat=0）→ **生成蓝图必须显式写 power-node 的 array config**
- 六个坑：①服务端启动 ~12 s 会用自己的地图**换掉**我们的世界（需 `--warmup 13` + tick 回退检测）；②不能在运行中的世界上放方块（先 `State.paused`）；③`setBlock` 后必须 `Vars.indexer.addIndex(tile)`；④**多格方块锚点 = footprint 中心格**，origin = `(x-(size-1)//2, y-(size-1)//2)`（3×3 vault 传 (33,20) 实占 32..34/19..21；2×2 因除尽看似左下原点，曾误判）；⑤**`Groups.build` 不可信**（实测 21 个 tile 只有 5 个进组，源码自承可空）→ 一切读数扫 `Vars.world.tile`；⑥**`Schematics.place` 是静默覆盖**，重叠不报错（后写盖前写）→ 生成器必须自校验 occupancy
- **生成器端到端已验（`docs/13`）**：从零构造的 2×硅炉蓝图（含显式电力 config）进引擎跑 1940 tick，产量 **2.973/s vs 理论 3.0/s（−0.9%）**；旋转 0..3、中心格坐标、电力"节点紧贴 consumer + 显式 config"三条约束同时被证实
- **传送带 / 布线器 / E1 生成已验（`docs/14`）**：传送带稳态 **4.9 items/s**（带长只影响延迟 ≈0.47 s/tile，不影响吞吐），方向 **rot 0=东 1=南 2=西 3=北**；电力布线器自动生成 node 位置 + 对称 Point2[] links（连通块=1）；E1 在 24×24 画布上生成 19 tiles / 175 字节，真机 **3.05 硅/s（预测 3.00，+1.7%）**，两台炉 `eff=1.00`，端到端 46 s

---

## 3. 九个"已经跑通"的先行验证

方案不是纸上的——调研期做出四个最小可运行件，工程化后依次补上 CLI、石墨物流门、单出口合流、触底的 10 格最小蓝图，最后把整条搜索链路也脚本化：

| 件 | 现状 | 证明什么 |
|---|---|---|
| `proto/mini_calc.py` | 已跑通，吃真机 dump 输出建筑清单 | 生产层可行：`合金 0.8/s` → `surge-smelter ×1 + silicon-smelter ×2`，17 格 / 300 电/s |
| `spikes/bp/scan_corpus.py` 的 `build_schematic_ext` | 831/831 往返通过 | 生成侧可行：MBO 能写出游戏认的 .msch |
| `spikes/sim/engine_probe.py` | 整张蓝图入世界并读回状态 | 验证侧可行（部分）：真机闭环能建起来 |
| `spikes/gen/gen_e1.py` | 24×24 生成 → 静态校验 → 真机 1800 tick，**3.05 硅/s（+1.7%）** | 全链路可行：机器生成的蓝图在真游戏里跑出预测产量（`docs/14`） |
| `mbo/`（CLI v0.1） | 单命令出 5 件产物 + 真机验证：石墨 **1.367/s**（+2.5%）、玻璃 **4.012/s**（+0.3%）、硅 **2.958/s**（−1.4%），49 项单测通过 | 可工程化：三条产线全 PASS、`verify` 重编码逐字节一致（`docs/15`） |
| `mbo gen --layout split`（石墨优化） | 一源 + 一个反溢流门分流两台压机：**6 方块 / 18 格 / 1.357/s**（基线 10/22/1.367/s），`verify` 字节一致 | 优化闭环可行：同样吞吐、方块 −40%；门语义与官方 writer 交叉验证见 `docs/16` |
| `mbo gen --layout split --merge void`（单出口） | 两压机合流到 1 个 1×1 物品黑洞：**7 方块 / 13 格 / 1.359/s**（pair 6/18/1.357，cells 10/22/1.367），真机计量改用分数周期 | 出口也能优化：格数再 −41%；1×1 容器原版不存在，黑洞是沙盒方块（`docs/17`） |
| `mbo gen --layout direct --crop`（下界蓝图） | 源/黑洞当 I/O 标记直接贴两台机器的共用邻位：**4 方块 / 10 格 / 5×2 蓝图 / 1.359/s（+1.9%）**，`verify` 字节一致 | 触底：8 格机器 + 2 格端口 = 10 格是可证下界，外接矩形零空格（`docs/18`） |
| `mbo gen --layout ported --ports both --crop`（端口在外） | 源/黑洞只能落在工厂外框之外，每台压机各一进一出：**工厂 8 格 / 4 端口 / 6 方块 / 1.282/s（−3.9%）**；gate 变体 9 格/3 端口/1.287/s，one 变体 12 格/2 端口/1.359/s | 新口径下 10 格 direct 失效（端口嵌在工厂里），前沿改为 8/4、9/3、12/2，见 `docs/19` |
| `mbo opt`（脚本化搜索） | 一条命令：枚举 **6195 张候选** → 物流最大流打分 → Pareto 3 条（2端口/12格、3/9、4/8）→ 选优 → 静态 + 真机：**1.359/s（+1.9%）**、`verify` 字节一致 | 搜索链路全脚本化：几何、速率、选优都不靠人挑；模板也进同一候选池（`docs/21`） |
| `mbo opt --objective clusters`（单开口） | 源与黑洞相邻成 **1 个开口**：8 格 / 4 端口 `SxSx` → **1.354/s（−0.4%）**；9 格 / 3 端口 → 1.287/s（−3.5%）。1 个端口方块不可能（源只发不收、黑洞只收不发），2 端口方块凑不出单开口（随机 2.4 万张 0 命中） | 开口数成为可优化维度；单开口的代价是端口方块变多（`docs/21` §7） |
| `mbo opt --only-ports 2`（双端单入单出） | 卡死 2 个端口后穷举：10 格 7 446 种、11 格 3 418 380 种摆法全部不可行 ⇒ 12 格是下界；脚本给出 `S/MM+MM/MM MM/>n</x`，真机 1.352/s（+1.4%） | 单入单出的最优有反证，不是试出来的（docs/21 §8） |

| `spikes/gen/run_quad.py --ports 8/6`（四核） | 4 台压机、目标 2.67/s：煤 5.33/s 超单格 4.9 ⇒ 至少 2 个输入口。结构化枚举 600 张可行候选只有两档：**8 端口/16 格 2.708/s**、**6 端口/18 格 2.703/s**（2 门喂 2 源 + 每台一个黑洞），两条都 PASS | 四核靠脚本枚举（贪心 beam 会卡在"每台一套源+黑洞"，见 `docs/22` §2）；4 端口一档仍未搜到合法形状 |
`mini_calc.py` 同时暴露了两个必须在正式实现里处理的建模问题：
1. **取整过量**：`ceil` 让上游富余（硅需求 2.4 → 2 台产 3/s，富余 0.6/s 要不要回收 → 归 MILP）；
2. **非配方产出**：煤/沙主要来自钻头（无 craftTime），必须显式区分**配方产出 / 采矿产出（地图相关）/ 外部输入**三类供给。

---

## 4. 建议的下一步（第一个 sprint，约 2 周）

按 `docs/02` 的阶段表，**先做 E1（硅 3/s 的机器生成蓝图 + 真机验证）**，不要一上来做合金或全工厂：

| 天 | 任务 | 验收 |
|---|---|---|
| D1–2 | L0 数据层落地：把 `gamedata.json` 规范成版本化快照（补传送带/钻头参数） | 27 个完整配方 + 107 耗电块 + 12 传送带/10 钻头可查，字段无 null |
| D3–4 | L1 IR + codec：搬 `build_schematic_ext` 进 `mbo/blueprint/`，坐标/旋转/锚点单测 | 831 张语料往返通过，导出图能在游戏里放下 |
| D5–6 | L2 生产计算器正式化（LP 上界 + 取整 + MILP 精修）+ **E0 标定** | 单建筑满料/缺料误差 ≤5%（E0 只需 L2，**不依赖布局**，故前置） |
| D7–8 | **读数工具封装**（E1 的前置 Gate）：产量主口径 = 产物汇入 container/vault/core 后按 `build.items` 差分，辅口径 = `progress` 回绕计数（补测已打通 +2.6%，本阶段做成 `RunResult.produced` 并跑 1800 tick 复验） | 对一个手工已知产量的样本，读出误差 ≤3% |
| D9–12 | L2 布局生成（模板 + shelf packing + 传送带布线）生成硅 3/s | 静态校验全绿，**真机跑出 ≥2.85/s（相对预测 ≤5%）** ← E1 Gate |
| D13–14 | 封装 `mbo validate --engine`，跑通 E1 的完整记录（产量/电力/死锁/8 项指标） | 一条命令出报告（A/B/C 是 E2 的事，E1 不涉及） |

> **D9–12 的 E1 目标已完成工程化**：`mbo gen silicon:3/s --boundary coal,sand` 单命令出 5 件产物，真机 2.958/s（−1.4%），端到端 46 s，`mbo verify` 重编码逐字节一致（`docs/15`）。同一 CLI 下石墨 1/s、玻璃 4/s 也全 PASS——即"先石墨、再玻璃、后硅"的递进验证已完成。

跑通 E1 之后再进 E2（合金 0.8/s，A/B/C 九指标对比），见 `docs/02` §E2。

---

## 5. 复现命令

```powershell
# 正式 CLI（单次 gen 含真机 1800 tick ≈ 46s）
python -X utf8 -m mbo gen graphite:1/s  --boundary coal --out g1
python -X utf8 -m mbo gen metaglass:4/s --boundary lead,sand --out m4
python -X utf8 -m mbo gen silicon:3/s   --boundary coal,sand --out s3
python -X utf8 -m mbo verify s3          # 从 trace 重建 + 重编码逐字节校验
python -X utf8 -m mbo preview s3         # 俯视图 runs/s3/preview.png
python -X utf8 -m mbo preview --all      # 画廊 runs/index.html（所有 run 一页看完）
python -X utf8 -m mbo preview --all --scale 3 --sprites   # 重绘全部 PNG + 画廊（贴原版贴图）
python -X utf8 -m mbo preview d10 --no-sprites             # 强制色块（对比/排障用）
python -X utf8 -m mbo calc surge-alloy:0.8/s --boundary coal,sand,copper,lead,titanium

# 石墨优化（一源 + 一个反溢流门分流两台压机 → 6 方块/18 格，约 46s）
python -X utf8 -m mbo gen graphite:1/s --boundary coal --layout split --out g1-split
python -X utf8 -m mbo preview g1-split --ascii

# 单出口合流（pair/single/vault/core/void，约 46s）
python -X utf8 -m mbo gen graphite:1/s --boundary coal --layout split --merge void --out m-void
python -X utf8 -m mbo verify m-void

# 10 格下界蓝图（源/黑洞当 I/O 标记 + 裁到 5×2，约 46s）
python -X utf8 -m mbo gen graphite:1/s --boundary coal --layout direct --crop --out d10
python -X utf8 -m mbo gen graphite:1/s --boundary coal --layout ported --ports both --crop --out p-both
python -X utf8 -m mbo gen graphite:1/s --boundary coal --layout ported --ports one  --crop --out p-one
python -X utf8 spikes/gen/search_ported.py   # 端口在外 + 物流限速的枚举/随机搜索
python -X utf8 -m mbo verify d10
python -X utf8 -m mbo preview d10 --ascii

# 脚本化搜索：枚举 → 物流模型 → Pareto → 选优 → 真机（约 46s；--no-engine 只静态约 2s）
python -X utf8 -m mbo opt graphite:1/s --boundary coal --crop --out o-ports
python -X utf8 -m mbo opt graphite:1/s --boundary coal --objective tiles --crop --out o-tiles
python -X utf8 -m mbo verify o-ports
python -X utf8 -m mbo opt graphite:1/s --boundary coal --objective clusters --crop --out o-cluster8   # 单开口（1 簇）
python -X utf8 -m mbo opt graphite:1/s --boundary coal --no-engine   # 只看前沿，不跑真机

# 单元测试
python -X utf8 -m unittest discover -s MBO/tests -v

# 语料全量扫描（约 40s，产出 corpus_report.json）
python -X utf8 MBO\spikes\bp\scan_corpus.py

# 游戏数据 dump（需 out/jre21，全量约 85s）
python -X utf8 MBO\spikes\data\extract_game_data.py

# 生产计算器原型
python -X utf8 MBO\proto\mini_calc.py surge-alloy:0.8/s --boundary coal,sand,copper,lead,titanium
python -X utf8 MBO\proto\mini_calc.py silicon:3/s --boundary coal,sand --json

# 真机探针（单次约 33s / 1800 tick，跑完自动清 java）
python -X utf8 MBO\spikes\sim\engine_probe.py --mode dump --ticks 1800 --msch logic-corpus\pixecoz-SchematicsPack\msch\metaglass-2.msch
```

> Windows 编码注意：**一律写成 `.py` 再 `python -X utf8`**；不要用 `python -c "中文"`（会乱码/解析失败）。

---

## 6. 边界与不做的事

- 不改 `AtomicStates/tools/`、`data/`、`logic-corpus/`（原仓库门禁依赖镜像副本一致性）；MBO 的代码全部在本目录内。
- 不复用 `mindustry-blueprint/` 的四份大文档内容（主体是 mlog 逻辑，不是工厂布局），只借它的工程方法。
- `Mindustry-Source/` 是 v159.3，**只做语义参考，不做数值来源**（数值一律来自运行时 dump）。
- 语料是第三方 schematic 包，**只做测试/统计/模板挖掘，不当交付物转手**。
- 本项目 **不让 LLM 生成规则数据**；LLM 的位置在"生成策略/解释/人机对话"，且必须过 Validator。

更细的架构决策（七层 L0–L6（MBO.md 的 6 个逻辑组件 + 1 个界面层）、IR、剪枝表、Pareto、学习四阶段）见 `docs/01`；排期与实验协议见 `docs/02`。
