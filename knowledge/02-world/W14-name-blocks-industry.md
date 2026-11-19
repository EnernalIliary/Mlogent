---
id: WORLD.NAMES.002
title: Block name mapping II - logistics / power / liquids / production (168 entries)
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "data/game/bundles/bundle_zh_CN.properties:1-3037"
  - "data/game/bundles/bundle.properties:1-3042"
data:
  - "00-data/blocks.json"
depends: [WORLD.BLOCKS.001, WORLD.LOGISTICS.001]
tags: [names, chinese-name, english-name, translation, mapping-table, logistics, power, liquids, production]
---

## One line

The Chinese name ↔ English name ↔ id mapping for the four buildable block groups - logistics, power, liquids and production; grouped by `category`, alphabetical by id inside each group.

## Rules / formulas

- The 168 blocks whose `category` is one of {distribution, power, liquid, production, defense} (terrain, ore and walls are excluded - see WORLD.NAMES.001).
- The order is the table order: distribution first (conveyors, routers, junctions, bridges, drivers), then power, liquid, production, defense.
- Display names come from `block.<id>.name`; a "—" means the bundle has no such entry (a hidden or placeholder block).
- `defense` has only a handful of entries in this group; the walls and doors that actually decide defensive numbers are in WORLD.NAMES.001 and COMBAT.DEFENSE.001.

## Numbers

This section lists names only; power draw, capacity, speed and similar numbers follow `00-data/blocks.json` (see the measurement sections of WORLD.LOGISTICS.001 / WORLD.POWER.001).

| id | English name | Chinese name | Chinese name source | English name source |
|---|---|---|---|---|
| `arkyic-boulder` | Arkyic Boulder | 芳石块 | zh:2129 | en:2134 |
| `arkyic-wall` | Arkyic Wall | 芳石墙 | zh:2117 | en:2122 |
| `armored-conveyor` | Armored Conveyor | 装甲传送带 | zh:1953 | en:1958 |
| `armored-duct` | Armored Duct | 装甲管道 | zh:2172 | en:2177 |
| `basalt-boulder` | Basalt Boulder | 玄武岩石块 | zh:1828 | en:1833 |
| `beryllic-boulder` | Beryllic Boulder | 铍石块 | zh:2127 | en:2132 |
| `beryllic-stone-wall` | Beryllic Stone Wall | 铍石墙 | zh:2116 | en:2121 |
| `boulder` | Boulder | 石块 | zh:1840 | en:1845 |
| `bridge-conveyor` | Bridge Conveyor | 传送带桥 | zh:2006 | en:2011 |
| `build1` | — | — | — | — |
| `build10` | — | — | — | — |
| `build11` | — | — | — | — |
| `build12` | — | — | — | — |
| `build13` | — | — | — | — |
| `build14` | — | — | — | — |
| `build15` | — | — | — | — |
| `build16` | — | — | — | — |
| `build2` | — | — | — | — |
| `build3` | — | — | — | — |
| `build4` | — | — | — | — |
| `build5` | — | — | — | — |
| `build6` | — | — | — | — |
| `build7` | — | — | — | — |
| `build8` | — | — | — | — |
| `build9` | — | — | — | — |
| `carbon-boulder` | Carbon Boulder | 碳石块 | zh:2125 | en:2130 |
| `carbon-wall` | Carbon Wall | 碳石墙 | zh:2114 | en:2119 |
| `cliff` | Cliff | 悬崖 | zh:1826 | en:1831 |
| `colored-wall` | Colored Wall | 染色墙壁 | zh:1918 | en:1923 |
| `command-center` | — | — | — | — |
| `conveyor` | Conveyor | 传送带 | zh:1950 | en:1955 |
| `crystal-blocks` | Crystal Blocks | 风化晶体 | zh:2132 | en:2137 |
| `crystal-cluster` | Crystal Cluster | 水晶簇 | zh:2130 | en:2135 |
| `crystal-orbs` | Crystal Orbs | 晶石球 | zh:2133 | en:2138 |
| `crystalline-boulder` | Crystalline Boulder | 晶石块 | zh:2134 | en:2139 |
| `crystalline-stone-wall` | Crystalline Stone Wall | 晶石墙 | zh:2118 | en:2123 |
| `dacite-boulder` | Dacite Boulder | 安山石块 | zh:1882 | en:1887 |
| `dacite-wall` | Dacite Wall | 安山岩墙 | zh:1881 | en:1886 |
| `dark-metal` | Dark Metal | 暗金属 | zh:1929 | en:1934 |
| `dirt-wall` | Dirt Wall | 泥土墙 | zh:1890 | en:1895 |
| `distributor` | Distributor | 分配器 | zh:1956 | en:1961 |
| `duct` | Duct | 物品管道 | zh:2059 | en:2064 |
| `duct-bridge` | Duct Bridge | 物品管道桥 | zh:2061 | en:2066 |
| `duct-router` | Duct Router | 物品管道路由器 | zh:2060 | en:2065 |
| `duct-unloader` | Duct Unloader | 管道装卸器 | zh:2175 | en:2180 |
| `dune-wall` | Dune Wall | 沙丘岩 | zh:1887 | en:1892 |
| `ferric-boulder` | Ferric Boulder | 铁石块 | zh:2126 | en:2131 |
| `ferric-stone-wall` | Ferric Stone Wall | 铁石墙 | zh:2115 | en:2120 |
| `graphitic-wall` | Graphitic Wall | 石墨墙 | zh:2138 | en:2143 |
| `ice-wall` | Ice Wall | 冰墙 | zh:1885 | en:1890 |
| `inverted-sorter` | Inverted Sorter | 反向分类器 | zh:1958 | en:1963 |
| `item-source` | Item Source | 物品源 | zh:1992 | en:1997 |
| `item-void` | Item Void | 物品黑洞 | zh:1993 | en:1998 |
| `junction` | Junction | 交叉器 | zh:1954 | en:1959 |
| `legacy-mech-pad` | — | — | — | — |
| `legacy-unit-factory` | — | — | — | — |
| `legacy-unit-factory-air` | — | — | — | — |
| `legacy-unit-factory-ground` | — | — | — | — |
| `mass-driver` | Mass Driver | 质量驱动器 | zh:2025 | en:2030 |
| `metal-wall-1` | Metal Wall 1 | 金属墙 1 | zh:1914 | en:1919 |
| `metal-wall-2` | Metal Wall 2 | 金属墙 2 | zh:1915 | en:1920 |
| `metal-wall-3` | Metal Wall 3 | 金属墙 3 | zh:1916 | en:1921 |
| `overflow-duct` | Overflow Duct | 溢流管道 | zh:2173 | en:2178 |
| `overflow-gate` | Overflow Gate | 溢流门 | zh:1964 | en:1969 |
| `phase-conveyor` | Phase Conveyor | 相织布传送带桥 | zh:2005 | en:2010 |
| `pine` | Pine | 松树 | zh:1888 | en:1893 |
| `plastanium-conveyor` | Plastanium Conveyor | 塑钢传送带 | zh:1952 | en:1957 |
| `pur-bush` | Pur Bush | 紫灌木丛 | zh:2123 | en:2128 |
| `red-diamond-wall` | Red Diamond Wall | 红钻墙 | zh:2121 | en:2126 |
| `red-ice-boulder` | Red Ice Boulder | 红冰石块 | zh:2135 | en:2140 |
| `red-ice-wall` | Red Ice Wall | 红冰墙 | zh:2119 | en:2124 |
| `red-stone-boulder` | Red Stone Boulder | 红石块 | zh:2137 | en:2142 |
| `red-stone-wall` | Red Stone Wall | 红石墙 | zh:2120 | en:2125 |
| `redweed` | Redweed | 赤藻 | zh:2122 | en:2127 |
| `regolith-wall` | Regolith Wall | 风化墙 | zh:2111 | en:2116 |
| `remove-wall` | Remove Wall | 移除墙体 | zh:1859 | en:1864 |
| `rhyolite-boulder` | Rhyolite Boulder | 流纹石块 | zh:2136 | en:2141 |
| `rhyolite-wall` | Rhyolite Wall | 流纹岩墙 | zh:2113 | en:2118 |
| `router` | Router | 路由器 | zh:1955 | en:1960 |
| `salt-wall` | Salt Wall | 盐墙 | zh:1834 | en:1839 |
| `sand-boulder` | Sand Boulder | 砂岩 | zh:1827 | en:1832 |
| `sand-wall` | Sand Wall | 沙墙 | zh:1837 | en:1842 |
| `shale-boulder` | Shale Boulder | 页岩石块 | zh:1844 | en:1849 |
| `shale-wall` | Shale Wall | 页岩墙 | zh:1848 | en:1853 |
| `shrubs` | Shrubs | 灌木丛 | zh:1846 | en:1851 |
| `snow-boulder` | Snow Boulder | 雪石块 | zh:1841 | en:1846 |
| `snow-pine` | Snow Pine | 雪树 | zh:1842 | en:1847 |
| `snow-wall` | Snow Wall | 雪墙 | zh:1886 | en:1891 |
| `sorter` | Sorter | 分类器 | zh:1957 | en:1962 |
| `spore-cluster` | Spore Cluster | 孢子簇 | zh:1894 | en:1899 |
| `spore-pine` | Spore Pine | 孢子树 | zh:1838 | en:1843 |
| `spore-wall` | Spore Wall | 孢子墙 | zh:1839 | en:1844 |
| `stone-wall` | Stone Wall | 石墙 | zh:1884 | en:1889 |
| `surge-conveyor` | Surge Conveyor | 合金传送带 | zh:2176 | en:2181 |
| `surge-router` | Surge Router | 合金路由器 | zh:2177 | en:2182 |
| `titanium-conveyor` | Titanium Conveyor | 钛传送带 | zh:1951 | en:1956 |
| `underflow-duct` | Underflow Duct | 反向溢流管 | zh:2174 | en:2179 |
| `underflow-gate` | Underflow Gate | 反向溢流门 | zh:1965 | en:1970 |
| `unit-cargo-loader` | Unit Cargo Loader | 单位物流装载器 | zh:2178 | en:2183 |
| `unit-cargo-unload-point` | Unit Cargo Unload Point | 单位物流卸载点 | zh:2179 | en:2184 |
| `unloader` | Unloader | 装卸器 | zh:1998 | en:2003 |
| `vibrant-crystal-cluster` | Vibrant Crystal Cluster | 鲜艳水晶簇 | zh:2131 | en:2136 |
| `white-tree` | White Tree | 白树 | zh:1893 | en:1898 |
| `white-tree-dead` | White Tree Dead | 枯萎的白树 | zh:1892 | en:1897 |
| `yellow-stone-boulder` | Yellow Stone Boulder | 黄石块 | zh:2128 | en:2133 |
| `yellow-stone-wall` | Yellow Stone Wall | 黄石墙 | zh:2112 | en:2117 |
| `yellowcoral` | Yellowcoral | 黄珊瑚 | zh:2124 | en:2129 |
| `battery` | Battery | 电池 | zh:1979 | en:1984 |
| `battery-large` | Large Battery | 大型电池 | zh:1980 | en:1985 |
| `beam-link` | Beam Link | 激光连接器 | zh:2189 | en:2194 |
| `beam-node` | Beam Node | 激光节点 | zh:2187 | en:2192 |
| `beam-tower` | Beam Tower | 激光塔 | zh:2188 | en:2193 |
| `chemical-combustion-chamber` | Chemical Combustion Chamber | 化学燃烧室 | zh:2191 | en:2196 |
| `combustion-generator` | Combustion Generator | 火力发电机 | zh:1981 | en:1986 |
| `differential-generator` | Differential Generator | 温差发电机 | zh:1983 | en:1988 |
| `diode` | Battery Diode | 二极管 | zh:1978 | en:1983 |
| `flux-reactor` | Flux Reactor | 通量反应堆 | zh:2238 | en:2243 |
| `impact-reactor` | Impact Reactor | 冲击反应堆 | zh:1984 | en:1989 |
| `neoplasia-reactor` | Neoplasia Reactor | 瘤变反应堆 | zh:2239 | en:2244 |
| `power-node` | Power Node | 电力节点 | zh:1975 | en:1980 |
| `power-node-large` | Large Power Node | 大型电力节点 | zh:1976 | en:1981 |
| `power-source` | Power Source | 电力源 | zh:1997 | en:2002 |
| `power-void` | Power Void | 电力黑洞 | zh:1996 | en:2001 |
| `pyrolysis-generator` | Pyrolysis Generator | 热解发生器 | zh:2192 | en:2197 |
| `rtg-generator` | RTG Generator | RTG 发电机 | zh:2040 | en:2045 |
| `solar-panel` | Solar Panel | 太阳能板 | zh:2010 | en:2015 |
| `solar-panel-large` | Large Solar Panel | 大型太阳能板 | zh:2011 | en:2016 |
| `steam-generator` | Steam Generator | 涡轮发电机 | zh:1982 | en:1987 |
| `surge-tower` | Surge Tower | 巨浪电力塔 | zh:1977 | en:1982 |
| `thermal-generator` | Thermal Generator | 热能发电机 | zh:2028 | en:2033 |
| `thorium-reactor` | Thorium Reactor | 钍反应堆 | zh:2024 | en:2029 |
| `turbine-condenser` | Turbine Condenser | 涡轮冷凝器 | zh:2190 | en:2195 |
| `bridge-conduit` | Bridge Conduit | 导管桥 | zh:2022 | en:2027 |
| `conduit` | Conduit | 导管 | zh:1990 | en:1995 |
| `impulse-pump` | Impulse Pump | 脉冲泵 | zh:2027 | en:2032 |
| `liquid-container` | Liquid Container | 流体容器 | zh:2020 | en:2025 |
| `liquid-junction` | Liquid Junction | 流体交叉器 | zh:2021 | en:2026 |
| `liquid-router` | Liquid Router | 流体路由器 | zh:2018 | en:2023 |
| `liquid-source` | Liquid Source | 液体源 | zh:1994 | en:1999 |
| `liquid-tank` | Liquid Tank | 流体储罐 | zh:2019 | en:2024 |
| `liquid-void` | Liquid Void | 液体黑洞 | zh:1995 | en:2000 |
| `mechanical-pump` | Mechanical Pump | 机械泵 | zh:1991 | en:1996 |
| `phase-conduit` | Phase Conduit | 相织布导管桥 | zh:2017 | en:2022 |
| `plated-conduit` | Plated Conduit | 电镀导管 | zh:2016 | en:2021 |
| `pulse-conduit` | Pulse Conduit | 脉冲导管 | zh:2015 | en:2020 |
| `reinforced-bridge-conduit` | Reinforced Bridge Conduit | 强化流体带桥 | zh:2183 | en:2188 |
| `reinforced-conduit` | Reinforced Conduit | 强化导管 | zh:2181 | en:2186 |
| `reinforced-liquid-container` | Reinforced Liquid Container | 强化流体容器 | zh:2185 | en:2190 |
| `reinforced-liquid-junction` | Reinforced Liquid Junction | 强化流体交叉器 | zh:2182 | en:2187 |
| `reinforced-liquid-router` | Reinforced Liquid Router | 强化流体路由器 | zh:2184 | en:2189 |
| `reinforced-liquid-tank` | Reinforced Liquid Tank | 强化流体储罐 | zh:2186 | en:2191 |
| `reinforced-pump` | Reinforced Pump | 强化泵 | zh:2180 | en:2185 |
| `rotary-pump` | Rotary Pump | 回转泵 | zh:2023 | en:2028 |
| `blast-drill` | Airblast Drill | 爆破钻头 | zh:2026 | en:2031 |
| `cliff-crusher` | Cliff Crusher | 墙壁粉碎机 | zh:2194 | en:2199 |
| `cultivator` | Cultivator | 培养机 | zh:1989 | en:1994 |
| `eruption-drill` | Eruption Drill | 爆裂钻头 | zh:2199 | en:2204 |
| `impact-drill` | Impact Drill | 冲击钻头 | zh:2198 | en:2203 |
| `large-cliff-crusher` | Advanced Cliff Crusher | 高级墙壁粉碎机 | zh:2195 | en:2200 |
| `large-plasma-bore` | Advanced Plasma Bore | 高级等离子钻机 | zh:2197 | en:2202 |
| `laser-drill` | Laser Drill | 激光钻头 | zh:1987 | en:1992 |
| `mechanical-drill` | Mechanical Drill | 机械钻头 | zh:1985 | en:1990 |
| `oil-extractor` | Oil Extractor | 石油钻井 | zh:2012 | en:2017 |
| `plasma-bore` | Plasma Bore | 等离子钻机 | zh:2196 | en:2201 |
| `pneumatic-drill` | Pneumatic Drill | 气动钻头 | zh:1986 | en:1991 |
| `vent-condenser` | Vent Condenser | 排气冷凝器 | zh:2193 | en:2198 |
| `water-extractor` | Water Extractor | 抽水机 | zh:1988 | en:1993 |
| `target-dummy` | — | — | — | — |

## Source anchors

- `data/game/bundles/bundle_zh_CN.properties` (Chinese names, zh:N is the line number) and `bundle.properties` (English names, en:N is the line number).
- The `category` field of `00-data/blocks.json` is this article's grouping key; 146 of the 168 entries have a Chinese name.
- Generator script `knowledge/tools/gen_name_docs.py`.

## Measurements and counter-examples

- **Counter-example A** - `junction` is officially junction (交叉器), not "intersection"; router (路由器) is a different block, `router`. Calling junction an intersection by the literal reading lumps it in with doors and road blocks.
- **Counter-example B** - `duct` is officially item duct (物品管道), not just "duct"; conveyor (传送带) is what `conveyor` means. The two sit at different tiers (ducts move bulk volume, conveyors one item at a time), so the names are close but not synonyms.
- **Counter-example B** - `phase-conveyor` is phase conveyor bridge (相织布传送带桥) and `bridge-conduit` is conduit bridge (导管桥); both are called a "bridge", but one bridges conveyors and the other bridges liquid conduits.
- **Counter-example C** - `mass-driver` is officially mass driver (质量驱动器), unrelated to motor and thruster class "drivers"; it is a long-range item delivery block (see WORLD.PAYLOAD.001).
- **Counter-example D** - `unloader` is officially unloader (装卸器), not the common unloader (卸载器); `sorter` is officially sorter (分类器), not the common sorter (分拣器). Searching with the usual translations finds nothing.
- **Counter-example E** - `force-projector` is force projector (力墙投影), also called force field projector (力场投影仪); the official string has no instrument (仪) character in it.

## Common misconceptions

- Confusing `router` (路由器) with `sorter` (分类器): the first splits flow evenly, the second filters by item; the mechanics are entirely different.
- Assuming duct (管道) and conveyor (传送带) share an id: `duct` and `conveyor` are two independent logistics lines with different throughput conventions.
- Assuming category is group: `category` is the internal class grouping (it covers all 168 entries here), while `group` covers only part of the buildable blocks, with 240 entries at `none`.

## Related

- WORLD.LOGISTICS.001 (conveyor throughput conventions, and bridge and junction queuing)
- WORLD.POWER.001 (the power network)
- WORLD.LIQUIDS.001 (liquids and conduits)
- WORLD.STORAGE.001 (containers, vaults, core capacity)
- WORLD.PAYLOAD.001 (payloads and the mass driver)
- WORLD.NAMES.001 / WORLD.NAMES.003 (the remaining block names)
