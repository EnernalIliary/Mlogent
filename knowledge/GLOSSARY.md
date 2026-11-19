# 术语对照 · Glossary（中 / 英 / 旧译与口语）

这份文件回答一个具体问题：**看到中文说法时，它对应哪个英文 id、哪篇文档。**

三个来源，各管一段：

1. **本页上半部分（手写）** —— 概念、系统名、逻辑处理器黑话。这些词没有官方英文 id，只有约定俗成的叫法。
2. **本页下半部分（`<!-- AUTO -->` 之间，生成）** —— 游戏实体的三列对照：英文 id / 官方英文名 / 官方中文名 / 旧译与口语。由 `knowledge/tools/gen_glossary.py` 从 `data/game/bundles/*.properties` 与 `data/game/aliases.json` 生成，**不要手改**。
3. **`data/game/aliases.json`** —— 机器可读的 `id → [官方中文, 旧译…]`，`tools/game.py` 的中英搜索用的就是它。

## 1. 逻辑与工具链（手写）

| 中文说法 | English | 是什么 | 出处 |
|---|---|---|---|
| 微处 / 微处理器 | micro-processor | 标准处理器，`ipt=2`，累积池 10 | `knowledge/06-mlog/M01-处理器与预算.md` |
| 逻辑处 | logic-processor | 3×3 处理器，`ipt=8`，池 40 | 同上 |
| 超处 | hyper-processor | 大型处理器，`ipt=25`，池 125 | 同上 |
| 世处 | world-processor | 世界处理器，特权，`setrate` 可到 1000 | 同上 |
| 累积池 | instruction accumulator | 每帧复位成 `maxInstructionScale × ipt` 的指令预算 | `knowledge/01-execution/E01-执行模型与预算.md` |
| 指令预算 / 单 tick 上限 | per-tick budget | 就是累积池；`maxInstructionsPerTick` **不参与**削顶 | `knowledge/VERSION.md` |
| 内联 | inlined | Mindcode 的 `def` 不生成函数，直接展开 | `knowledge/06-mlog/M10-Mindcode-Syntax.md` |
| 前缀编译 | prefix compilation | 逐条语句编译前缀，用差分归因 mlog 行 | `knowledge/06-mlog/M09-Mindcode.md` |
| 源码映射 | source map | `.mnd` 行 ↔ `.mlog` 行 | `tools/sourcemap.py` |
| 链接名 | link name | 处理器里指向方块的变量名；读档时会按基名重算 | `knowledge/01-execution/E05-链接与@常量.md` |
| `@` 常量 | `@`-variables | `@this`、`@counter`、`@unit`、`@copper` 这类内建引用 | 同上 |
| 边沿 | rising edge | `0→1` 的跳变；可能被采样跳过，所以用相位号 | `knowledge/07-patterns/P03-comm-bus.md` |
| 相位 / 握手 | phase / handshake | 用只增计数代替边沿的跨处理器同步 | 同上 |
| 交货口 / 卸货器 | unloader | 从核心/容器往传送带取货的方块 | `knowledge/02-world/W06-logistics.md` |
| 热容 / 冷却液 | heat capacity / coolant | 炮塔与发电机的液体冷却机制 | `knowledge/02-world/W05-heat.md` |
| 载荷 | payload | 能搬运方块与单位的那套机制（`payload-*`） | `knowledge/02-world/W08-payload.md` |
| 单位多控 | unit multi-control | 一个处理器同时控制多台单位（`ucontrol`） | `knowledge/07-patterns/P07-unit-multicontrol.md` |
| 沙盘 / 场景 | sandbox / scenario | 一个可复现的实验装置（建筑+单位+断言） | `tools/scenario.py`、`scenes/scenarios/` |
| 活世界 | live world | 真跑起来的 Mindustry 服务端（`world_server.py`） | `docs/联机调试世界.md` |
| 投影 | projection | 把离线仿真的单位与建筑画进活世界（给人看，不是判据） | `docs/联机调试世界.md` §17 |
| 扰动 | modifier | 场景运行中途对世界做的事（推单位、换控制权、抽核心货…） | `tools/modifier.py` |
| 种子 / 收缩 | seed / shrink | 参数化场景的随机种子；失败后把扰动缩到最小集合 | `tools/explore.py` |
| 差分 | differential | 同一场景在离线执行器与活世界各跑一次再比 | `docs/观察与差分-契约.md` |
| 保真度边界 | fidelity boundary | 已知的、可解释的差异（地形、时钟、指令集） | `tools/fidelity.py` |
| 信封 | envelope | 所有判定共用的返回结构（`mlog-eval/v1`） | `tools/mlog_eval.py` |
| 分级 | level | 同一结果的三种深浅：`summary` / `diagnostics` / `full` | 同上 |
| 失败类型 | failure type | 七种归一化失败（`compilation_error` 等） | 同上 |
| 四维成功 | success levels | `execution` / `static` / `simulation` / `real_runtime`；`null` ≠ 通过 | 同上 |
| 任务状态 / 续跑 | task state / resume | 跨轮记住「哪一段已经过了」 | `tools/taskstate.py` |
| 基准 / 一次过 | benchmark / first pass | 六个任务上的 Onboarding 评测与它的首批数字 | `tools/benchmark.py`、`bench/results/README.md` |
| 断言 / 证据指针 | claim / evidence pointer | `L1-17` 这类 id；指针指向 `docs/验证记录.md` 的具体行 | `tools/claims.py` |
| 母本 | source of truth | 一份事实只在这里定义，别处指路 | `knowledge/CONVENTIONS.md` |
| 官方名 / 旧译 / 口语 | official name / legacy translation / colloquial | 中文名的三层：bundle 里的、早年翻译的、玩家顺口叫的 | 本页下半部分 |

## 2. 名字的三层，怎么用

同一个东西在中文里往往有三个名字，判断用哪个：

| 层 | 例子 | 规则 |
|---|---|---|
| **官方名** | `parallax` = 差扰、`core-shard` = 初代核心 | 文档里**必须**用这一层（`bundle_zh_CN.properties` 是母本） |
| **旧译** | 耀斑（今 星辉）、金玻（今 钢化玻璃）、碎片核心（今 初代核心） | 只在搜索别名里保留，正文不用 |
| **口语** | 硅厂（硅冶炼厂）、爆混（爆炸混合物）、微处（微型处理器） | 允许出现在正文的括号里，但不做标题 |

搜不到东西时按这个顺序换词：官方名 → 英文 id → 旧译 → 口语。`tools/kb_grep.py` 与 `mlog_kb` 都是词面匹配，换词比换问法有效。

<!-- AUTO:BEGIN —— 以下由 knowledge/tools/gen_glossary.py 生成，勿手改 -->

## 3. 实体名对照（生成）

「旧译与口语」列来自 `data/game/aliases.json`：第一个别名恒为官方中文名，其后是早年翻译与口语；与任何官方名撞车的会被生成器剔除。

### 物品（items） 22 条

| id | 官方英文名 | 官方中文名 | 旧译与口语 |
|---|---|---|---|
| `beryllium` | Beryllium | 铍 |  |
| `blast-compound` | Blast Compound | 爆炸混合物 | 爆混 |
| `carbide` | Carbide | 碳化物 |  |
| `coal` | Coal | 煤炭 | 煤 |
| `copper` | Copper | 铜 | 铜矿 |
| `dormant-cyst` | Dormant Cyst | 休眠囊肿 | 休眠孢, 休眠囊 |
| `fissile-matter` | Fissile Matter | 裂变产物 | 裂变物质 |
| `graphite` | Graphite | 石墨 |  |
| `lead` | Lead | 铅 | 铅矿 |
| `metaglass` | Metaglass | 钢化玻璃 | 金属玻璃, 玻璃 |
| `oxide` | Oxide | 氧化物 | 氧化剂 |
| `phase-fabric` | Phase Fabric | 相织布 | 相织物, 相位织物 |
| `plastanium` | Plastanium | 塑钢 |  |
| `pyratite` | Pyratite | 硫化物 | 黄炸药, 硫磺炸药 |
| `sand` | Sand | 沙 |  |
| `scrap` | Scrap | 废料 | 废金属 |
| `silicon` | Silicon | 硅 |  |
| `spore-pod` | Spore Pod | 孢子荚 | 孢子 |
| `surge-alloy` | Surge Alloy | 巨浪合金 | 浪涌合金 |
| `thorium` | Thorium | 钍 | 钍矿 |
| `titanium` | Titanium | 钛 | 钛矿 |
| `tungsten` | Tungsten | 钨 |  |

### 液体（liquids） 11 条

| id | 官方英文名 | 官方中文名 | 旧译与口语 |
|---|---|---|---|
| `arkycite` | Arkycite | 芳油 |  |
| `cryofluid` | Cryofluid | 冷冻液 |  |
| `cyanogen` | Cyanogen | 氰气 |  |
| `gallium` | Gallium | 镓液 |  |
| `hydrogen` | Hydrogen | 氢气 |  |
| `neoplasm` | Neoplasm | 瘤液 |  |
| `nitrogen` | Nitrogen | 氮气 |  |
| `oil` | Oil | 石油 |  |
| `ozone` | Ozone | 臭氧 |  |
| `slag` | Slag | 矿渣 |  |
| `water` | Water | 水 |  |

### 单位（units） 60 条

| id | 官方英文名 | 官方中文名 | 旧译与口语 |
|---|---|---|---|
| `aegires` | Aegires | 玄武 | 海麒麟 |
| `alpha` | Alpha | 阿尔法 |  |
| `anthicus` | Anthicus | 天灾 |  |
| `antumbra` | Antumbra | 月影 | 半影 |
| `arkyid` | Arkyid | 毒蛊 | 蜘蛛 |
| `assembly-drone` | Assembly Drone | 装配无人机 |  |
| `atrax` | Atrax | 毒蛛 | 阿特拉克斯 |
| `avert` | Avert | 遮蔽 |  |
| `beta` | Beta | 贝塔 |  |
| `bryde` | Bryde | 戟鲸 | 布氏鲸 |
| `cleroi` | Cleroi | 天赐 |  |
| `collaris` | Collaris | 天帝 |  |
| `conquer` | Conquer | 领主 |  |
| `corvus` | Corvus | 死星 |  |
| `crawler` | Crawler | 爬虫 |  |
| `cyerce` | Cyerce | 江豚 | 海麒麟 |
| `dagger` | Dagger | 尖刀 | 匕首 |
| `disrupt` | Disrupt | 悲怆 |  |
| `eclipse` | Eclipse | 日蚀 | 日食 |
| `elude` | Elude | 挣脱 |  |
| `emanate` | Emanate | 发散 |  |
| `evoke` | Evoke | 苏醒 |  |
| `flare` | Flare | 星辉 | 耀斑 |
| `fortress` | Fortress | 堡垒 |  |
| `gamma` | Gamma | 伽马 |  |
| `horizon` | Horizon | 天垠 | 地平线 |
| `incite` | Incite | 策动 |  |
| `latum` | Latum | Latum |  |
| `locus` | Locus | 循迹 |  |
| `mace` | Mace | 战锤 | 钉锤 |
| `manifold` | Manifold | 货运无人机 |  |
| `mega` | Mega | 巨像 | 兆 |
| `merui` | Merui | 天守 |  |
| `minke` | Minke | 飞鲨 | 小须鲸 |
| `mono` | Mono | 独影 | 单子 |
| `navanax` | Navanax | 龙王 | 蓝斑 |
| `nova` | Nova | 新星 |  |
| `obviate` | Obviate | 消散 |  |
| `oct` | Oct | 要塞 | 八隅 |
| `omura` | Omura | 海神 | 大村鲸 |
| `oxynoe` | Oxynoe | 电鳗 |  |
| `poly` | Poly | 幻型 | 多面 |
| `precept` | Precept | 准绳 |  |
| `pulsar` | Pulsar | 恒星 | 脉冲星 |
| `quad` | Quad | 雷霆 | 四联 |
| `quasar` | Quasar | 耀星 | 类星体 |
| `quell` | Quell | 遏止 |  |
| `reign` | Reign | 王座 | 王权 |
| `renale` | Renale | Renale |  |
| `retusa` | Retusa | 潜螺 | 海兔 |
| `risso` | Risso | 梭鱼 | 里索 |
| `scepter` | Scepter | 权杖 |  |
| `sei` | Sei | 蛟龙 | 塞鲸 |
| `spiroct` | Spiroct | 血蛭 | 螺旋虫 |
| `stell` | Stell | 围护 |  |
| `tecta` | Tecta | 天理 |  |
| `toxopid` | Toxopid | 天蝎 |  |
| `vanquish` | Vanquish | 征服 |  |
| `vela` | Vela | 灾星 | 帆船座 |
| `zenith` | Zenith | 苍穹 | 天顶 |

### 方块（blocks） 411 条

| id | 官方英文名 | 官方中文名 | 旧译与口语 |
|---|---|---|---|
| `additive-reconstructor` | Additive Reconstructor | 数增级单位重构工厂 | 增材重构厂 |
| `advanced-launch-pad` | Launch Pad | 发射台 |  |
| `afflict` | Afflict | 劫难 |  |
| `air-factory` | Air Factory | 空军工厂 |  |
| `arc` | Arc | 电弧 |  |
| `arkycite-floor` | Arkycite | 芳油 |  |
| `arkyic-boulder` | Arkyic Boulder | 芳石块 |  |
| `arkyic-stone` | Arkyic Stone | 芳石 |  |
| `arkyic-vent` | Arkyic Vent | 芳石喷口 |  |
| `arkyic-wall` | Arkyic Wall | 芳石墙 |  |
| `armored-conveyor` | Armored Conveyor | 装甲传送带 |  |
| `armored-duct` | Armored Duct | 装甲管道 |  |
| `atmospheric-concentrator` | Atmospheric Concentrator | 大气收集器 |  |
| `basalt` | Basalt | 玄武岩 |  |
| `basalt-boulder` | Basalt Boulder | 玄武岩石块 |  |
| `basalt-vent` | Basalt Vent | 玄武岩喷口 |  |
| `basic-assembler-module` | Basic Assembler Module | 基本装配厂模块 |  |
| `battery` | Battery | 电池 |  |
| `battery-large` | Large Battery | 大型电池 |  |
| `beam-link` | Beam Link | 激光连接器 |  |
| `beam-node` | Beam Node | 激光节点 |  |
| `beam-tower` | Beam Tower | 激光塔 |  |
| `beryllic-boulder` | Beryllic Boulder | 铍石块 |  |
| `beryllic-stone` | Beryllic Stone | 铍石 |  |
| `beryllic-stone-wall` | Beryllic Stone Wall | 铍石墙 |  |
| `beryllium-wall` | Beryllium Wall | 铍墙 |  |
| `beryllium-wall-large` | Large Beryllium Wall | 大型铍墙 |  |
| `blast-door` | Blast Door | 防爆闸门 |  |
| `blast-drill` | Airblast Drill | 爆破钻头 |  |
| `blast-mixer` | Blast Mixer | 爆炸物混合器 | 爆混混合器 |
| `bluemat` | Bluemat | 蓝地垫 |  |
| `boulder` | Boulder | 石块 |  |
| `breach` | Breach | 撕裂 |  |
| `bridge-conduit` | Bridge Conduit | 导管桥 |  |
| `bridge-conveyor` | Bridge Conveyor | 传送带桥 |  |
| `build-tower` | Build Tower | 建造塔 |  |
| `canvas` | Canvas | 画板 |  |
| `carbide-crucible` | Carbide Crucible | 碳化物坩埚 |  |
| `carbide-wall` | Carbide Wall | 碳化物墙 |  |
| `carbide-wall-large` | Large Carbide Wall | 大型碳化物墙 |  |
| `carbon-boulder` | Carbon Boulder | 碳石块 |  |
| `carbon-stone` | Carbon Stone | 碳石 |  |
| `carbon-vent` | Carbon Vent | 碳石喷口 |  |
| `carbon-wall` | Carbon Wall | 碳石墙 |  |
| `char` | Charred Stone | 焦土 |  |
| `character-overlay` | Character Overlay | 标识贴片 |  |
| `character-overlay-white` | Character Overlay (White) | 标识贴片 (白色) |  |
| `chemical-combustion-chamber` | Chemical Combustion Chamber | 化学燃烧室 |  |
| `cliff` | Cliff | 悬崖 |  |
| `cliff-crusher` | Cliff Crusher | 墙壁粉碎机 |  |
| `coal-centrifuge` | Coal Centrifuge | 煤炭离心机 |  |
| `colored-floor` | Colored Floor | 染色地板 |  |
| `colored-wall` | Colored Wall | 染色墙壁 |  |
| `combustion-generator` | Combustion Generator | 火力发电机 | 燃烧发电机 |
| `conduit` | Conduit | 导管 |  |
| `constructor` | Constructor | 构筑器 |  |
| `container` | Container | 容器 |  |
| `conveyor` | Conveyor | 传送带 |  |
| `copper-wall` | Copper Wall | 铜墙 |  |
| `copper-wall-large` | Large Copper Wall | 大型铜墙 |  |
| `core-acropolis` | Core: Acropolis | 卫城核心 |  |
| `core-bastion` | Core: Bastion | 城堡核心 |  |
| `core-citadel` | Core: Citadel | 堡垒核心 | 要塞核心 |
| `core-foundation` | Core: Foundation | 次代核心 | 基础核心 |
| `core-nucleus` | Core: Nucleus | 终代核心 | 核心中枢 |
| `core-shard` | Core: Shard | 初代核心 | 碎片核心 |
| `core-zone` | Core Zone | 核心区 |  |
| `crater-stone` | Craters | 陨石坑 |  |
| `cryofluid-mixer` | Cryofluid Mixer | 冷冻液混合器 |  |
| `crystal-blocks` | Crystal Blocks | 风化晶体 |  |
| `crystal-cluster` | Crystal Cluster | 水晶簇 |  |
| `crystal-floor` | Crystal Floor | 晶石地板 |  |
| `crystal-orbs` | Crystal Orbs | 晶石球 |  |
| `crystalline-boulder` | Crystalline Boulder | 晶石块 |  |
| `crystalline-stone` | Crystalline Stone | 晶石 |  |
| `crystalline-stone-wall` | Crystalline Stone Wall | 晶石墙 |  |
| `crystalline-vent` | Crystalline Vent | 晶石喷口 |  |
| `cultivator` | Cultivator | 培养机 |  |
| `cyanogen-synthesizer` | Cyanogen Synthesizer | 氰合成机 |  |
| `cyclone` | Cyclone | 气旋 |  |
| `dacite` | Dacite | 安山岩 |  |
| `dacite-boulder` | Dacite Boulder | 安山石块 |  |
| `dacite-wall` | Dacite Wall | 安山岩墙 |  |
| `dark-metal` | Dark Metal | 暗金属 |  |
| `dark-panel-1` | Dark Panel 1 | 暗面板 1 |  |
| `dark-panel-2` | Dark Panel 2 | 暗面板 2 |  |
| `dark-panel-3` | Dark Panel 3 | 暗面板 3 |  |
| `dark-panel-4` | Dark Panel 4 | 暗面板 4 |  |
| `dark-panel-5` | Dark Panel 5 | 暗面板 5 |  |
| `dark-panel-6` | Dark Panel 6 | 暗面板 6 |  |
| `darksand` | Dark Sand | 黑沙 |  |
| `darksand-tainted-water` | Dark Sand Tainted Water | 黑沙污水 |  |
| `darksand-water` | Dark Sand Water | 黑沙浅滩 |  |
| `deconstructor` | Large Deconstructor | 大型解构器 |  |
| `deep-tainted-water` | Deep Tainted Water | 深污水 |  |
| `deep-water` | Deep Water | 深水 |  |
| `dense-red-stone` | Dense Red Stone | 高密红石 |  |
| `differential-generator` | Differential Generator | 温差发电机 |  |
| `diffuse` | Diffuse | 扩散 |  |
| `diode` | Battery Diode | 二极管 |  |
| `dirt` | Dirt | 泥土 |  |
| `dirt-wall` | Dirt Wall | 泥土墙 |  |
| `disassembler` | Disassembler | 解离机 |  |
| `disperse` | Disperse | 驱离 |  |
| `distributor` | Distributor | 分配器 |  |
| `door` | Door | 门 |  |
| `door-large` | Large Door | 大门 |  |
| `duct` | Duct | 物品管道 |  |
| `duct-bridge` | Duct Bridge | 物品管道桥 |  |
| `duct-router` | Duct Router | 物品管道路由器 |  |
| `duct-unloader` | Duct Unloader | 管道装卸器 |  |
| `dune-wall` | Dune Wall | 沙丘岩 |  |
| `duo` | Duo | 双管 |  |
| `electric-heater` | Electric Heater | 电制热机 |  |
| `electrolyzer` | Electrolyzer | 电解机 |  |
| `empty` | Empty | 空 |  |
| `eruption-drill` | Eruption Drill | 爆裂钻头 |  |
| `exponential-reconstructor` | Exponential Reconstructor | 多幂级单位重构工厂 | 指数重构厂 |
| `ferric-boulder` | Ferric Boulder | 铁石块 |  |
| `ferric-craters` | Ferric Craters | 铁陨石坑 |  |
| `ferric-stone` | Ferric Stone | 铁石 |  |
| `ferric-stone-wall` | Ferric Stone Wall | 铁石墙 |  |
| `flux-reactor` | Flux Reactor | 通量反应堆 |  |
| `force-projector` | Force Projector | 力墙投影 | 力场投影器 |
| `foreshadow` | Foreshadow | 厄兆 |  |
| `fuse` | Fuse | 雷光 |  |
| `graphite-press` | Graphite Press | 石墨压缩机 | 石墨压机 |
| `graphitic-wall` | Graphitic Wall | 石墨墙 |  |
| `grass` | Grass | 草地 |  |
| `ground-factory` | Ground Factory | 陆军工厂 |  |
| `hail` | Hail | 冰雹 |  |
| `heat-reactor` | Heat Reactor | 热量反应堆 |  |
| `heat-redirector` | Heat Redirector | 热量传输机 |  |
| `heat-router` | Heat Router | 热量路由器 |  |
| `heat-source` | Heat Source | 热量源 |  |
| `hotrock` | Hot Rock | 灼热岩石 |  |
| `hyper-processor` | Hyper Processor | 超核处理器 |  |
| `ice` | Ice | 冰 |  |
| `ice-snow` | Ice Snow | 冰雪地 |  |
| `ice-wall` | Ice Wall | 冰墙 |  |
| `illuminator` | Illuminator | 照明器 |  |
| `impact-drill` | Impact Drill | 冲击钻头 |  |
| `impact-reactor` | Impact Reactor | 冲击反应堆 |  |
| `impulse-pump` | Impulse Pump | 脉冲泵 |  |
| `incinerator` | Incinerator | 焚化炉 |  |
| `interplanetary-accelerator` | Interplanetary Accelerator | 行星际加速器 |  |
| `inverted-sorter` | Inverted Sorter | 反向分类器 |  |
| `item-source` | Item Source | 物品源 |  |
| `item-void` | Item Void | 物品黑洞 |  |
| `junction` | Junction | 交叉器 |  |
| `kiln` | Kiln | 窑炉 |  |
| `lancer` | Lancer | 蓝瑟 |  |
| `landing-pad` | Landing Pad | 接收台 | 着陆台 |
| `large-canvas` | Large Canvas | 大型画板 |  |
| `large-cliff-crusher` | Advanced Cliff Crusher | 高级墙壁粉碎机 |  |
| `large-constructor` | Large Constructor | 大型构筑器 |  |
| `large-logic-display` | Large Logic Display | 大型逻辑显示屏 |  |
| `large-payload-mass-driver` | Large Payload Mass Driver | 大型载荷质量驱动器 |  |
| `large-plasma-bore` | Advanced Plasma Bore | 高级等离子钻机 |  |
| `large-shield-projector` | Large Barrier Projector | 大型护盾投影器 |  |
| `laser-drill` | Laser Drill | 激光钻头 |  |
| `launch-pad` | Launch Pad (Legacy) | 发射台（旧版） |  |
| `liquid-container` | Liquid Container | 流体容器 |  |
| `liquid-junction` | Liquid Junction | 流体交叉器 |  |
| `liquid-router` | Liquid Router | 流体路由器 |  |
| `liquid-source` | Liquid Source | 液体源 |  |
| `liquid-tank` | Liquid Tank | 流体储罐 |  |
| `liquid-void` | Liquid Void | 液体黑洞 |  |
| `logic-display` | Logic Display | 逻辑显示屏 |  |
| `logic-processor` | Logic Processor | 逻辑处理器 |  |
| `lustre` | Lustre | 光辉 |  |
| `magmarock` | Magma Rock | 熔融岩石 |  |
| `malign` | Malign | 魔灵 |  |
| `mass-driver` | Mass Driver | 质量驱动器 |  |
| `mech-assembler` | Mech Assembler | 机甲组装厂 |  |
| `mech-fabricator` | Mech Fabricator | 机甲制造厂 |  |
| `mech-refabricator` | Mech Refabricator | 机甲重构厂 |  |
| `mechanical-drill` | Mechanical Drill | 机械钻头 |  |
| `mechanical-pump` | Mechanical Pump | 机械泵 |  |
| `meltdown` | Meltdown | 熔毁 |  |
| `melter` | Melter | 熔炉 |  |
| `memory-bank` | Memory Bank | 内存库 |  |
| `memory-cell` | Memory Cell | 内存元 | 内存格 |
| `mend-projector` | Mend Projector | 修理投影 | 维修投影器 |
| `mender` | Mender | 修理器 |  |
| `message` | Message | 信息板 | 消息方块 |
| `metal-floor` | Metal Floor 1 | 金属地板 1 |  |
| `metal-floor-2` | Metal Floor 2 | 金属地板 2 |  |
| `metal-floor-3` | Metal Floor 3 | 金属地板 3 |  |
| `metal-floor-4` | Metal Floor 4 | 金属地板 4 |  |
| `metal-floor-5` | Metal Floor 5 | 金属地板 5 |  |
| `metal-floor-damaged` | Damaged Metal Floor | 损坏的金属地板 |  |
| `metal-tiles-1` | Metal Tiles 1 | 金属地基 1 |  |
| `metal-tiles-10` | Metal Tiles 10 | 金属地基 10 |  |
| `metal-tiles-11` | Metal Tiles 11 | 金属地基 11 |  |
| `metal-tiles-12` | Metal Tiles 12 | 金属地基 12 |  |
| `metal-tiles-13` | Metal Tiles 13 | 金属地基 13 |  |
| `metal-tiles-2` | Metal Tiles 2 | 金属地基 2 |  |
| `metal-tiles-3` | Metal Tiles 3 | 金属地基 3 |  |
| `metal-tiles-4` | Metal Tiles 4 | 金属地基 4 |  |
| `metal-tiles-5` | Metal Tiles 5 | 金属地基 5 |  |
| `metal-tiles-6` | Metal Tiles 6 | 金属地基 6 |  |
| `metal-tiles-7` | Metal Tiles 7 | 金属地基 7 |  |
| `metal-tiles-8` | Metal Tiles 8 | 金属地基 8 |  |
| `metal-tiles-9` | Metal Tiles 9 | 金属地基 9 |  |
| `metal-wall-1` | Metal Wall 1 | 金属墙 1 |  |
| `metal-wall-2` | Metal Wall 2 | 金属墙 2 |  |
| `metal-wall-3` | Metal Wall 3 | 金属墙 3 |  |
| `micro-processor` | Micro Processor | 微型处理器 | 微处理器 |
| `molten-slag` | Slag | 矿渣液 |  |
| `moss` | Moss | 苔藓地 |  |
| `mud` | Mud | 泥巴 |  |
| `multi-press` | Multi-Press | 多重压缩机 | 多联压机 |
| `multiplicative-reconstructor` | Multiplicative Reconstructor | 倍乘级单位重构工厂 | 乘材重构厂 |
| `naval-factory` | Naval Factory | 海军工厂 |  |
| `neoplasia-reactor` | Neoplasia Reactor | 瘤变反应堆 |  |
| `oil-extractor` | Oil Extractor | 石油钻井 |  |
| `overdrive-dome` | Overdrive Dome | 超速穹顶 |  |
| `overdrive-projector` | Overdrive Projector | 超速投影 | 超速投影器 |
| `overflow-duct` | Overflow Duct | 溢流管道 |  |
| `overflow-gate` | Overflow Gate | 溢流门 |  |
| `oxidation-chamber` | Oxidation Chamber | 氧化室 |  |
| `parallax` | Parallax | 差扰 |  |
| `payload-conveyor` | Payload Conveyor | 载荷传送带 |  |
| `payload-loader` | Payload Loader | 载荷装载器 |  |
| `payload-mass-driver` | Payload Mass Driver | 载荷质量驱动器 |  |
| `payload-router` | Payload Router | 载荷路由器 |  |
| `payload-source` | Payload Source | 载荷源 |  |
| `payload-unloader` | Payload Unloader | 载荷卸载器 |  |
| `payload-void` | Payload Void | 载荷黑洞 |  |
| `pebbles` | Pebbles | 鹅卵石 |  |
| `phase-conduit` | Phase Conduit | 相织布导管桥 |  |
| `phase-conveyor` | Phase Conveyor | 相织布传送带桥 |  |
| `phase-heater` | Phase Heater | 相织制热机 |  |
| `phase-synthesizer` | Phase Synthesizer | 相织布合成机 |  |
| `phase-wall` | Phase Wall | 相织布墙 |  |
| `phase-wall-large` | Large Phase Wall | 大型相织布墙 |  |
| `phase-weaver` | Phase Weaver | 相织布编织器 | 相织物编织器 |
| `pine` | Pine | 松树 |  |
| `plasma-bore` | Plasma Bore | 等离子钻机 |  |
| `plastanium-compressor` | Plastanium Compressor | 塑钢压缩机 |  |
| `plastanium-conveyor` | Plastanium Conveyor | 塑钢传送带 |  |
| `plastanium-wall` | Plastanium Wall | 塑钢墙 |  |
| `plastanium-wall-large` | Large Plastanium Wall | 大型塑钢墙 |  |
| `plated-conduit` | Plated Conduit | 电镀导管 |  |
| `pneumatic-drill` | Pneumatic Drill | 气动钻头 |  |
| `pooled-cryofluid` | Cryofluid | 冷冻液 |  |
| `power-node` | Power Node | 电力节点 |  |
| `power-node-large` | Large Power Node | 大型电力节点 |  |
| `power-source` | Power Source | 电力源 |  |
| `power-void` | Power Void | 电力黑洞 |  |
| `prime-refabricator` | Prime Refabricator | 高级再重构工厂 |  |
| `pulse-conduit` | Pulse Conduit | 脉冲导管 |  |
| `pulverizer` | Pulverizer | 粉碎机 |  |
| `pur-bush` | Pur Bush | 紫灌木丛 |  |
| `pyratite-mixer` | Pyratite Mixer | 硫化物混合器 | 黄炸药混合器 |
| `pyrolysis-generator` | Pyrolysis Generator | 热解发生器 |  |
| `radar` | Radar | 雷达 |  |
| `red-diamond-wall` | Red Diamond Wall | 红钻墙 |  |
| `red-ice` | Red Ice | 红冰 |  |
| `red-ice-boulder` | Red Ice Boulder | 红冰石块 |  |
| `red-ice-wall` | Red Ice Wall | 红冰墙 |  |
| `red-stone` | Red Stone | 红石 |  |
| `red-stone-boulder` | Red Stone Boulder | 红石块 |  |
| `red-stone-vent` | Red Stone Vent | 红石喷口 |  |
| `red-stone-wall` | Red Stone Wall | 红石墙 |  |
| `redmat` | Redmat | 红地垫 |  |
| `redweed` | Redweed | 赤藻 |  |
| `regen-projector` | Regen Projector | 再生投影器 |  |
| `regolith` | Regolith | 风化岩 |  |
| `regolith-wall` | Regolith Wall | 风化墙 |  |
| `reinforced-bridge-conduit` | Reinforced Bridge Conduit | 强化流体带桥 |  |
| `reinforced-conduit` | Reinforced Conduit | 强化导管 |  |
| `reinforced-container` | Reinforced Container | 强化容器 |  |
| `reinforced-liquid-container` | Reinforced Liquid Container | 强化流体容器 |  |
| `reinforced-liquid-junction` | Reinforced Liquid Junction | 强化流体交叉器 |  |
| `reinforced-liquid-router` | Reinforced Liquid Router | 强化流体路由器 |  |
| `reinforced-liquid-tank` | Reinforced Liquid Tank | 强化流体储罐 |  |
| `reinforced-message` | Reinforced Message | 强化信息板 |  |
| `reinforced-payload-conveyor` | Reinforced Payload Conveyor | 强化载荷传送带 |  |
| `reinforced-payload-router` | Reinforced Payload Router | 强化载荷路由器 |  |
| `reinforced-pump` | Reinforced Pump | 强化泵 |  |
| `reinforced-surge-wall` | Reinforced Surge Wall | 强化合金墙 |  |
| `reinforced-surge-wall-large` | Large Reinforced Surge Wall | 大型强化合金墙 |  |
| `reinforced-vault` | Reinforced Vault | 强化仓库 |  |
| `remove-ore` | Remove Ore | 移除矿 |  |
| `remove-wall` | Remove Wall | 移除墙体 |  |
| `repair-point` | Repair Point | 维修点 |  |
| `repair-turret` | Repair Turret | 维修塔 |  |
| `rhyolite` | Rhyolite | 流纹岩 |  |
| `rhyolite-boulder` | Rhyolite Boulder | 流纹石块 |  |
| `rhyolite-crater` | Rhyolite Crater | 流纹岩坑 |  |
| `rhyolite-vent` | Rhyolite Vent | 流纹石喷口 |  |
| `rhyolite-wall` | Rhyolite Wall | 流纹岩墙 |  |
| `ripple` | Ripple | 浪涌 |  |
| `rotary-pump` | Rotary Pump | 回转泵 |  |
| `rough-rhyolite` | Rough Rhyolite | 粗糙流纹岩 |  |
| `router` | Router | 路由器 |  |
| `rtg-generator` | RTG Generator | RTG 发电机 |  |
| `rune-overlay` | Rune Overlay | 符文贴片 |  |
| `rune-overlay-crux` | Rune Overlay (Crux) | 符文贴片 （红队） |  |
| `salt` | Salt | 盐碱地 |  |
| `salt-wall` | Salt Wall | 盐墙 |  |
| `salvo` | Salvo | 齐射 |  |
| `sand-boulder` | Sand Boulder | 砂岩 |  |
| `sand-floor` | Sand | 沙子 |  |
| `sand-wall` | Sand Wall | 沙墙 |  |
| `sand-water` | Sand Water | 浅滩 |  |
| `scathe` | Scathe | 创伤 |  |
| `scatter` | Scatter | 分裂 |  |
| `scorch` | Scorch | 火焰 |  |
| `scrap-wall` | Scrap Wall | 废墙 |  |
| `scrap-wall-gigantic` | Gigantic Scrap Wall | 超巨型废墙 |  |
| `scrap-wall-huge` | Huge Scrap Wall | 巨型废墙 |  |
| `scrap-wall-large` | Large Scrap Wall | 大型废墙 |  |
| `segment` | Segment | 裂解 |  |
| `separator` | Separator | 分离机 |  |
| `shale` | Shale | 页岩地 |  |
| `shale-boulder` | Shale Boulder | 页岩石块 |  |
| `shale-wall` | Shale Wall | 页岩墙 |  |
| `shallow-water` | Water | 水 |  |
| `shield-projector` | Barrier Projector | 护盾投影器 |  |
| `shielded-wall` | Shielded Wall | 盾墙 |  |
| `ship-assembler` | Ship Assembler | 飞船组装厂 |  |
| `ship-fabricator` | Ship Fabricator | 飞船制造厂 |  |
| `ship-refabricator` | Ship Refabricator | 飞船重构厂 |  |
| `shock-mine` | Shock Mine | 脉冲地雷 |  |
| `shockwave-tower` | Shockwave Tower | 震爆塔 |  |
| `shrubs` | Shrubs | 灌木丛 |  |
| `silicon-arc-furnace` | Silicon Arc Furnace | 电弧硅炉 | 硅电弧炉 |
| `silicon-crucible` | Silicon Crucible | 热能坩埚 | 硅坩埚, 硅熔炉 |
| `silicon-smelter` | Silicon Smelter | 硅冶炼厂 | 硅厂 |
| `slag-centrifuge` | Slag Centrifuge | 矿渣离心机 |  |
| `slag-heater` | Slag Heater | 矿渣制热机 |  |
| `slag-incinerator` | Slag Incinerator | 矿渣焚化炉 |  |
| `small-deconstructor` | Deconstructor | 解构器 |  |
| `small-heat-redirector` | Small Heat Redirector | 小型热量传输机 |  |
| `smite` | Smite | 天谴 |  |
| `snow` | Snow | 雪 |  |
| `snow-boulder` | Snow Boulder | 雪石块 |  |
| `snow-pine` | Snow Pine | 雪树 |  |
| `snow-wall` | Snow Wall | 雪墙 |  |
| `solar-panel` | Solar Panel | 太阳能板 |  |
| `solar-panel-large` | Large Solar Panel | 大型太阳能板 |  |
| `sorter` | Sorter | 分类器 |  |
| `space` | Space | 太空 |  |
| `spawn` | Enemy Spawn | 敌人出生点 |  |
| `spectre` | Spectre | 幽灵 |  |
| `spore-cluster` | Spore Cluster | 孢子簇 |  |
| `spore-moss` | Spore Moss | 孢子苔藓地 |  |
| `spore-pine` | Spore Pine | 孢子树 |  |
| `spore-press` | Spore Press | 孢子压缩机 | 孢子压机 |
| `spore-wall` | Spore Wall | 孢子墙 |  |
| `steam-generator` | Steam Generator | 涡轮发电机 | 蒸汽发电机 |
| `stone` | Stone | 石头 |  |
| `stone-vent` | Stone Vent | 岩石喷口 |  |
| `stone-wall` | Stone Wall | 石墙 |  |
| `sublimate` | Sublimate | 升华 |  |
| `surge-conveyor` | Surge Conveyor | 合金传送带 |  |
| `surge-crucible` | Surge Crucible | 合金坩埚 |  |
| `surge-router` | Surge Router | 合金路由器 |  |
| `surge-smelter` | Surge Smelter | 合金冶炼厂 | 巨浪合金冶炼厂 |
| `surge-tower` | Surge Tower | 巨浪电力塔 |  |
| `surge-wall` | Surge Wall | 合金墙 |  |
| `surge-wall-large` | Large Surge Wall | 大型合金墙 |  |
| `swarmer` | Swarmer | 蜂群 |  |
| `switch` | Switch | 开关 |  |
| `tainted-water` | Tainted Water | 污水 |  |
| `tank-assembler` | Tank Assembler | 坦克组装厂 |  |
| `tank-fabricator` | Tank Fabricator | 坦克制造厂 |  |
| `tank-refabricator` | Tank Refabricator | 坦克重构厂 |  |
| `tar` | Tar | 石油 |  |
| `tendrils` | Tendrils | 卷须 |  |
| `tetrative-reconstructor` | Tetrative Reconstructor | 无量级单位重构工厂 | 四次重构厂 |
| `thermal-generator` | Thermal Generator | 热能发电机 | 地热发电机 |
| `thorium-reactor` | Thorium Reactor | 钍反应堆 |  |
| `thorium-wall` | Thorium Wall | 钍墙 |  |
| `thorium-wall-large` | Large Thorium Wall | 大型钍墙 |  |
| `thruster` | Thruster | 推进器残骸 |  |
| `tile-logic-display` | Tiled Logic Display | 逻辑显示单元 |  |
| `titan` | Titan | 泰坦 |  |
| `titanium-conveyor` | Titanium Conveyor | 钛传送带 |  |
| `titanium-wall` | Titanium Wall | 钛墙 |  |
| `titanium-wall-large` | Large Titanium Wall | 大型钛墙 |  |
| `tsunami` | Tsunami | 海啸 |  |
| `tungsten-wall` | Tungsten Wall | 钨墙 |  |
| `tungsten-wall-large` | Large Tungsten Wall | 大型钨墙 |  |
| `turbine-condenser` | Turbine Condenser | 涡轮冷凝器 |  |
| `underflow-duct` | Underflow Duct | 反向溢流管 |  |
| `underflow-gate` | Underflow Gate | 反向溢流门 |  |
| `unit-cargo-loader` | Unit Cargo Loader | 单位物流装载器 |  |
| `unit-cargo-unload-point` | Unit Cargo Unload Point | 单位物流卸载点 |  |
| `unit-repair-tower` | Unit Repair Tower | 单位维修塔 |  |
| `unloader` | Unloader | 装卸器 | 卸货器 |
| `vault` | Vault | 仓库 |  |
| `vent-condenser` | Vent Condenser | 排气冷凝器 |  |
| `vibrant-crystal-cluster` | Vibrant Crystal Cluster | 鲜艳水晶簇 |  |
| `water-extractor` | Water Extractor | 抽水机 |  |
| `wave` | Wave | 波浪 |  |
| `white-tree` | White Tree | 白树 |  |
| `white-tree-dead` | White Tree Dead | 枯萎的白树 |  |
| `world-cell` | World Cell | 世界内存元 |  |
| `world-message` | World Message | 世界信息板 |  |
| `world-processor` | World Processor | 世界处理器 |  |
| `world-switch` | World Switch | 世界开关 |  |
| `yellow-stone` | Yellow Stone | 黄石 |  |
| `yellow-stone-boulder` | Yellow Stone Boulder | 黄石块 |  |
| `yellow-stone-plates` | Yellow Stone Plates | 黄石地板 |  |
| `yellow-stone-vent` | Yellow Stone Vent | 黄石喷口 |  |
| `yellow-stone-wall` | Yellow Stone Wall | 黄石墙 |  |
| `yellowcoral` | Yellowcoral | 黄珊瑚 |  |

<!-- AUTO:END -->
