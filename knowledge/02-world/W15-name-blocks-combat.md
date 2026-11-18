---
id: WORLD.NAMES.003
title: 方块名对照③：合成 / 炮塔 / 效果 / 单位方块 / 逻辑（143 条）
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "data/game/bundles/bundle_zh_CN.properties:1-3037"
  - "data/game/bundles/bundle.properties:1-3042"
data:
  - "00-data/blocks.json"
depends: [WORLD.BLOCKS.001, COMBAT.TURRET.001]
tags: [名词, 中文名, 英文名, 翻译, 对照表, 炮塔, 合成, 逻辑, 单位方块]
---

## 一句话

合成厂、炮塔、特效块、单位建造方块与逻辑块的「中文名 ↔ 英文名 ↔ id」对照；炮塔名常是意象词，查数值前先确认是哪一张表。

## 规则 / 公式

- `category` 属于 {crafting, turret, effect, units, logic} 且不含地形类型的 143 条方块。
- 表内先 crafting、再 turret、effect、units、logic，组内按 id 字母序。
- 炮塔数值不在本文，见 `00-data/turrets.json` 与 COMBAT.TURRET.001；单位数值见 `00-data/units.json` 与 UNIT.MOVE.001。
- 逻辑块（`logic-*`）的指令语义见 06-mlog 域，本文只给名字。

## 数值

本节只列名词，不含射程、DPS、装填等数值；这类数字统一在 COMBAT.TURRET.001 与 COMBAT.NUMBERS.001。

| id | 英文名 | 中文名 | 中文名出处 | 英文名出处 |
|---|---|---|---|---|
| `atmospheric-concentrator` | Atmospheric Concentrator | 大气收集器 | zh:2141 | en:2146 |
| `blast-mixer` | Blast Mixer | 爆炸物混合器 | zh:2009 | en:2014 |
| `carbide-crucible` | Carbide Crucible | 碳化物坩埚 | zh:2150 | en:2155 |
| `coal-centrifuge` | Coal Centrifuge | 煤炭离心机 | zh:1974 | en:1979 |
| `cryofluid-mixer` | Cryofluid Mixer | 冷冻液混合器 | zh:1969 | en:1974 |
| `cyanogen-synthesizer` | Cyanogen Synthesizer | 氰合成机 | zh:2153 | en:2158 |
| `disassembler` | Disassembler | 解离机 | zh:2065 | en:2070 |
| `electric-heater` | Electric Heater | 电制热机 | zh:2143 | en:2148 |
| `electrolyzer` | Electrolyzer | 电解机 | zh:2140 | en:2145 |
| `graphite-press` | Graphite Press | 石墨压缩机 | zh:1855 | en:1860 |
| `heat-reactor` | Heat Reactor | 热量反应堆 | zh:2155 | en:2160 |
| `heat-redirector` | Heat Redirector | 热量传输机 | zh:2146 | en:2151 |
| `heat-router` | Heat Router | 热量路由器 | zh:2148 | en:2153 |
| `heat-source` | Heat Source | 热量源 | zh:2079 | en:2084 |
| `incinerator` | Incinerator | 焚化炉 | zh:1971 | en:1976 |
| `kiln` | Kiln | 窑炉 | zh:1854 | en:1859 |
| `melter` | Melter | 熔炉 | zh:1970 | en:1975 |
| `multi-press` | Multi-Press | 多重压缩机 | zh:1856 | en:1861 |
| `oxidation-chamber` | Oxidation Chamber | 氧化室 | zh:2142 | en:2147 |
| `phase-heater` | Phase Heater | 相织制热机 | zh:2145 | en:2150 |
| `phase-synthesizer` | Phase Synthesizer | 相织布合成机 | zh:2154 | en:2159 |
| `phase-weaver` | Phase Weaver | 相织布编织器 | zh:1967 | en:1972 |
| `plastanium-compressor` | Plastanium Compressor | 塑钢压缩机 | zh:2007 | en:2012 |
| `pulverizer` | Pulverizer | 粉碎机 | zh:1968 | en:1973 |
| `pyratite-mixer` | Pyratite Mixer | 硫化物混合器 | zh:2008 | en:2013 |
| `separator` | Separator | 分离机 | zh:1973 | en:1978 |
| `silicon-arc-furnace` | Silicon Arc Furnace | 电弧硅炉 | zh:2139 | en:2144 |
| `silicon-crucible` | Silicon Crucible | 热能坩埚 | zh:2066 | en:2071 |
| `silicon-smelter` | Silicon Smelter | 硅冶炼厂 | zh:1966 | en:1971 |
| `slag-centrifuge` | Slag Centrifuge | 矿渣离心机 | zh:2151 | en:2156 |
| `slag-heater` | Slag Heater | 矿渣制热机 | zh:2144 | en:2149 |
| `slag-incinerator` | Slag Incinerator | 矿渣焚化炉 | zh:2149 | en:2154 |
| `small-heat-redirector` | Small Heat Redirector | 小型热量传输机 | zh:2147 | en:2152 |
| `spore-press` | Spore Press | 孢子压缩机 | zh:1972 | en:1977 |
| `surge-crucible` | Surge Crucible | 合金坩埚 | zh:2152 | en:2157 |
| `surge-smelter` | Surge Smelter | 合金冶炼厂 | zh:2029 | en:2034 |
| `afflict` | Afflict | 劫难 | zh:2209 | en:2214 |
| `arc` | Arc | 电弧 | zh:2039 | en:2044 |
| `breach` | Breach | 撕裂 | zh:2205 | en:2210 |
| `cyclone` | Cyclone | 气旋 | zh:2034 | en:2039 |
| `diffuse` | Diffuse | 扩散 | zh:2234 | en:2239 |
| `disperse` | Disperse | 驱离 | zh:2208 | en:2213 |
| `duo` | Duo | 双管 | zh:1945 | en:1950 |
| `foreshadow` | Foreshadow | 厄兆 | zh:2043 | en:2048 |
| `fuse` | Fuse | 雷光 | zh:2035 | en:2040 |
| `hail` | Hail | 冰雹 | zh:1948 | en:1953 |
| `lancer` | Lancer | 蓝瑟 | zh:1949 | en:1954 |
| `lustre` | Lustre | 光辉 | zh:2210 | en:2215 |
| `malign` | Malign | 魔灵 | zh:2237 | en:2242 |
| `meltdown` | Meltdown | 熔毁 | zh:2042 | en:2047 |
| `parallax` | Parallax | 差扰 | zh:1825 | en:1830 |
| `ripple` | Ripple | 浪涌 | zh:2004 | en:2009 |
| `salvo` | Salvo | 齐射 | zh:2003 | en:2008 |
| `scathe` | Scathe | 创伤 | zh:2211 | en:2216 |
| `scatter` | Scatter | 分裂 | zh:1947 | en:1952 |
| `scorch` | Scorch | 火焰 | zh:1946 | en:1951 |
| `segment` | Segment | 裂解 | zh:2049 | en:2054 |
| `smite` | Smite | 天谴 | zh:2236 | en:2241 |
| `spectre` | Spectre | 幽灵 | zh:2041 | en:2046 |
| `sublimate` | Sublimate | 升华 | zh:2206 | en:2211 |
| `swarmer` | Swarmer | 蜂群 | zh:2002 | en:2007 |
| `titan` | Titan | 泰坦 | zh:2207 | en:2212 |
| `tsunami` | Tsunami | 海啸 | zh:2001 | en:2006 |
| `wave` | Wave | 波浪 | zh:2000 | en:2005 |
| `advanced-launch-pad` | Launch Pad | 发射台 | zh:2046 | en:2051 |
| `build-tower` | Build Tower | 建造塔 | zh:2167 | en:2172 |
| `container` | Container | 容器 | zh:2044 | en:2049 |
| `core-acropolis` | Core: Acropolis | 卫城核心 | zh:2202 | en:2207 |
| `core-bastion` | Core: Bastion | 城堡核心 | zh:2200 | en:2205 |
| `core-citadel` | Core: Citadel | 堡垒核心 | zh:2201 | en:2206 |
| `core-foundation` | Core: Foundation | 次代核心 | zh:1862 | en:1867 |
| `core-nucleus` | Core: Nucleus | 终代核心 | zh:1863 | en:1868 |
| `core-shard` | Core: Shard | 初代核心 | zh:1861 | en:1866 |
| `force-projector` | Force Projector | 力墙投影 | zh:2038 | en:2043 |
| `illuminator` | Illuminator | 照明器 | zh:1963 | en:1968 |
| `interplanetary-accelerator` | Interplanetary Accelerator | 行星际加速器 | zh:2068 | en:2073 |
| `landing-pad` | Landing Pad | 接收台 | zh:2047 | en:2052 |
| `large-shield-projector` | Large Barrier Projector | 大型护盾投影器 | zh:2171 | en:2176 |
| `launch-pad` | Launch Pad (Legacy) | 发射台（旧版） | zh:2045 | en:2050 |
| `mend-projector` | Mend Projector | 修理投影 | zh:2031 | en:2036 |
| `mender` | Mender | 修理器 | zh:2030 | en:2035 |
| `overdrive-dome` | Overdrive Dome | 超速穹顶 | zh:2067 | en:2072 |
| `overdrive-projector` | Overdrive Projector | 超速投影 | zh:2037 | en:2042 |
| `radar` | Radar | 雷达 | zh:2166 | en:2171 |
| `regen-projector` | Regen Projector | 再生投影器 | zh:2168 | en:2173 |
| `reinforced-container` | Reinforced Container | 强化容器 | zh:2203 | en:2208 |
| `reinforced-vault` | Reinforced Vault | 强化仓库 | zh:2204 | en:2209 |
| `shield-projector` | Barrier Projector | 护盾投影器 | zh:2170 | en:2175 |
| `shock-mine` | Shock Mine | 脉冲地雷 | zh:2036 | en:2041 |
| `shockwave-tower` | Shockwave Tower | 震爆塔 | zh:2169 | en:2174 |
| `vault` | Vault | 仓库 | zh:1999 | en:2004 |
| `additive-reconstructor` | Additive Reconstructor | 数增级单位重构工厂 | zh:2053 | en:2058 |
| `air-factory` | Air Factory | 空军工厂 | zh:2051 | en:2056 |
| `basic-assembler-module` | Basic Assembler Module | 基本装配厂模块 | zh:2235 | en:2240 |
| `constructor` | Constructor | 构筑器 | zh:2069 | en:2074 |
| `deconstructor` | Large Deconstructor | 大型解构器 | zh:2073 | en:2078 |
| `exponential-reconstructor` | Exponential Reconstructor | 多幂级单位重构工厂 | zh:2055 | en:2060 |
| `ground-factory` | Ground Factory | 陆军工厂 | zh:2050 | en:2055 |
| `large-constructor` | Large Constructor | 大型构筑器 | zh:2071 | en:2076 |
| `large-payload-mass-driver` | Large Payload Mass Driver | 大型载荷质量驱动器 | zh:2062 | en:2067 |
| `mech-assembler` | Mech Assembler | 机甲组装厂 | zh:2220 | en:2225 |
| `mech-fabricator` | Mech Fabricator | 机甲制造厂 | zh:2230 | en:2235 |
| `mech-refabricator` | Mech Refabricator | 机甲重构厂 | zh:2216 | en:2221 |
| `multiplicative-reconstructor` | Multiplicative Reconstructor | 倍乘级单位重构工厂 | zh:2054 | en:2059 |
| `naval-factory` | Naval Factory | 海军工厂 | zh:2052 | en:2057 |
| `payload-conveyor` | Payload Conveyor | 载荷传送带 | zh:2057 | en:2062 |
| `payload-loader` | Payload Loader | 载荷装载器 | zh:2075 | en:2080 |
| `payload-mass-driver` | Payload Mass Driver | 载荷质量驱动器 | zh:2223 | en:2228 |
| `payload-router` | Payload Router | 载荷路由器 | zh:2058 | en:2063 |
| `payload-source` | Payload Source | 载荷源 | zh:2064 | en:2069 |
| `payload-unloader` | Payload Unloader | 载荷卸载器 | zh:2077 | en:2082 |
| `payload-void` | Payload Void | 载荷黑洞 | zh:2063 | en:2068 |
| `prime-refabricator` | Prime Refabricator | 高级再重构工厂 | zh:2232 | en:2237 |
| `reinforced-payload-conveyor` | Reinforced Payload Conveyor | 强化载荷传送带 | zh:2221 | en:2226 |
| `reinforced-payload-router` | Reinforced Payload Router | 强化载荷路由器 | zh:2222 | en:2227 |
| `repair-point` | Repair Point | 维修点 | zh:2013 | en:2018 |
| `repair-turret` | Repair Turret | 维修塔 | zh:2014 | en:2019 |
| `ship-assembler` | Ship Assembler | 飞船组装厂 | zh:2219 | en:2224 |
| `ship-fabricator` | Ship Fabricator | 飞船制造厂 | zh:2231 | en:2236 |
| `ship-refabricator` | Ship Refabricator | 飞船重构厂 | zh:2217 | en:2222 |
| `small-deconstructor` | Deconstructor | 解构器 | zh:2224 | en:2229 |
| `tank-assembler` | Tank Assembler | 坦克组装厂 | zh:2218 | en:2223 |
| `tank-fabricator` | Tank Fabricator | 坦克制造厂 | zh:2229 | en:2234 |
| `tank-refabricator` | Tank Refabricator | 坦克重构厂 | zh:2215 | en:2220 |
| `tetrative-reconstructor` | Tetrative Reconstructor | 无量级单位重构工厂 | zh:2056 | en:2061 |
| `unit-repair-tower` | Unit Repair Tower | 单位维修塔 | zh:2233 | en:2238 |
| `canvas` | Canvas | 画板 | zh:2225 | en:2230 |
| `hyper-processor` | Hyper Processor | 超核处理器 | zh:2244 | en:2249 |
| `large-canvas` | Large Canvas | 大型画板 | zh:2226 | en:2231 |
| `large-logic-display` | Large Logic Display | 大型逻辑显示屏 | zh:2246 | en:2251 |
| `logic-display` | Logic Display | 逻辑显示屏 | zh:2245 | en:2250 |
| `logic-processor` | Logic Processor | 逻辑处理器 | zh:2243 | en:2248 |
| `memory-bank` | Memory Bank | 内存库 | zh:2249 | en:2254 |
| `memory-cell` | Memory Cell | 内存元 | zh:2248 | en:2253 |
| `message` | Message | 信息板 | zh:1959 | en:1964 |
| `micro-processor` | Micro Processor | 微型处理器 | zh:2242 | en:2247 |
| `reinforced-message` | Reinforced Message | 强化信息板 | zh:1960 | en:1965 |
| `switch` | Switch | 开关 | zh:2241 | en:2246 |
| `tile-logic-display` | Tiled Logic Display | 逻辑显示单元 | zh:2247 | en:2252 |
| `world-cell` | World Cell | 世界内存元 | zh:2228 | en:2233 |
| `world-message` | World Message | 世界信息板 | zh:1961 | en:1966 |
| `world-processor` | World Processor | 世界处理器 | zh:2227 | en:2232 |
| `world-switch` | World Switch | 世界开关 | zh:1962 | en:1967 |

## 源码锚点

- `data/game/bundles/bundle_zh_CN.properties`（zh:N）与 `bundle.properties`（en:N）。
- `00-data/blocks.json`：`category` 分组；143 条中 143 条有中文名。
- 生成脚本 `knowledge/tools/gen_name_docs.py`。

## 实测与反例

- 反例一：炮塔中文名三种策略并存——`duo`=双管（意译）、`scatter`=分裂与 `hail`=冰雹（意象）、`lancer`=蓝瑟（纯音译）、`fuse`=雷光（造词）。按「散射」「长矛」「引信」直译都搜不到官方串。
- 反例二：单位方块（`category=units`）是工厂本身，不是单位——陆军、空军、海军工厂与坦克、飞船、机甲制造厂都在方块表，单位记录只在 `00-data/units.json`；查 `dagger` 这类单位名到方块表里找必然落空。
- 反例三：重构厂用非直译词——Additive→「数增级」、Multiplicative→「倍乘级」、Exponential→「多幂级」、Tetrative→「无量级」；按 add、multiply、exponential 直译找不到。
- 反例四：`core-shard` 英文 “Core: Shard”，中文「初代核心」——不是直译（直译是「核心：碎片」），按英文逐词翻找不到中文名叫什么。
- 反例五：`mender` 方块中文「修理器」，与单位能力里的 repair、mend 概念共享词根，但它是可建造方块（见 COMBAT.SUPPORT.001）。
- 反例六：`overdrive` 作为状态是「过载」，作为方块 `overdrive-projector` 却是「超速投影」——英文同源、中文不同名，按「过载投影仪」搜不到。
- 反例七：逻辑块 `logic-processor` 是「逻辑处理器」，`logic-display` 是「逻辑显示屏」；缩写 LP、LD 只在社区口头用，不是显示名。

## 常见误解

- 以为炮塔中文名带「炮」字：官方串里 `duo` 就叫「双管」、`ripple` 叫「涟漪」，没有「炮」字。
- 把 `effect` 类当纯装饰：这类块有实际判定（如 `overdrive-projector` 超速投影），名字像装饰但机制在 COMBAT.STATUS.001。
- 以为合成厂名与产物同名：`silicon-smelter` 是「硅冶炼厂」，产物是 `silicon`「硅」，名字不同。

## 相关

- COMBAT.TURRET.001（炮塔射程、装填、弹药）
- COMBAT.DEFENSE.001（墙体、门、护盾、修理器）
- COMBAT.STATUS.001（状态与过载）
- WORLD.CRAFTING.001（配方与制造）
- UNIT.PRODUCE.001（单位生产链与单位方块）
- WORLD.NAMES.001 / WORLD.NAMES.002（其余方块名）
