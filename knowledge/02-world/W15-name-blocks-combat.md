---
id: WORLD.NAMES.003
title: Block name mapping III - crafting / turrets / effects / unit blocks / logic (143 entries)
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
tags: [names, chinese-name, english-name, translation, mapping-table, turret, crafting, logic, unit-block]
---

## One line

The Chinese name ↔ English name ↔ id mapping for fabricators, turrets, effect blocks, unit-building blocks and logic blocks; turret names are often imagery words, so confirm which table you are in before looking up numbers.

## Rules / formulas

- The 143 blocks whose `category` is one of {crafting, turret, effect, units, logic} and which carry no terrain type.
- The table runs crafting first, then turret, effect, units and logic, alphabetical by id inside each group.
- Turret numbers are not in this article - see `00-data/turrets.json` and COMBAT.TURRET.001; unit numbers are in `00-data/units.json` and UNIT.MOVE.001.
- The instruction semantics of the logic blocks (`logic-*`) belong to the 06-mlog domain; this article gives names only.

## Numbers

This section lists names only and carries no range, DPS or reload numbers; those figures live uniformly in COMBAT.TURRET.001 and COMBAT.NUMBERS.001.

| id | English name | Chinese name | Chinese name source | English name source |
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

## Source anchors

- `data/game/bundles/bundle_zh_CN.properties` (zh:N) and `bundle.properties` (en:N).
- `00-data/blocks.json`: the `category` grouping; 143 of the 143 entries have a Chinese name.
- Generator script `knowledge/tools/gen_name_docs.py`.

## Measurements and counter-examples

- **Counter-example A** - three naming strategies coexist in the turret Chinese names: `duo` = twin-barrel (双管) (a free translation), `scatter` = scatter (分裂) and `hail` = hail (冰雹) (imagery), `lancer` = Lancer (蓝瑟) (pure transliteration), `fuse` = thunder-light (雷光) (a coined word). Literal readings as scattering, lance and fuse never match the official strings.
- **Counter-example B** - unit blocks (`category=units`) are the factories themselves, not units: the ground, air and naval factories and the tank, ship and mech fabricators all sit in the block table, while unit records live only in `00-data/units.json`; looking for a unit name such as `dagger` in the block table always comes up empty.
- **Counter-example C** - the refabricators use non-literal terms: Additive → quantity tier (数增级), Multiplicative → multiplier tier (倍乘级), Exponential → power tier (多幂级), Tetrative → boundless tier (无量级); literal add, multiply and exponential readings find nothing.
- **Counter-example D** - `core-shard` is "Core: Shard" in English and first-generation core (初代核心) in Chinese - not a literal translation (a literal one would be core: shard (核心：碎片)), so translating the English word by word never yields the Chinese name.
- **Counter-example E** - the block `mender` is repairer (修理器); it shares the root of the repair and mend concepts in unit abilities, but it is a buildable block (see COMBAT.SUPPORT.001).
- **Counter-example F** - `overdrive` as a status is overload (过载), yet as the block `overdrive-projector` it is overdrive projector (超速投影): same English root, different Chinese name, so overload projector (过载投影仪) finds nothing.
- **Counter-example G** - the logic block `logic-processor` is logic processor (逻辑处理器) and `logic-display` is logic display (逻辑显示屏); the abbreviations LP and LD are community shorthand only, not display names.

## Common misconceptions

- Assuming turret Chinese names contain the character for "cannon": in the official strings `duo` is simply twin-barrel (双管) and `ripple` is ripple (涟漪), with no cannon (炮) character at all.
- Treating the `effect` class as pure decoration: these blocks have real mechanics (such as `overdrive-projector`, overdrive projector (超速投影)); the name looks decorative but the mechanics are in COMBAT.STATUS.001.
- Assuming a fabricator is named after its product: `silicon-smelter` is silicon smelter (硅冶炼厂) while the product is `silicon`, silicon (硅); the names differ.

## Related

- COMBAT.TURRET.001 (turret range, reload, ammo)
- COMBAT.DEFENSE.001 (walls, doors, shields, the repairer)
- COMBAT.STATUS.001 (statuses and overload)
- WORLD.CRAFTING.001 (recipes and manufacturing)
- UNIT.PRODUCE.001 (the unit production chain and unit blocks)
- WORLD.NAMES.001 / WORLD.NAMES.002 (the remaining block names)
