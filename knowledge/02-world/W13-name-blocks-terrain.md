---
id: WORLD.NAMES.001
title: Block name mapping I - terrain / ore / walls (136 entries)
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "data/game/bundles/bundle_zh_CN.properties:1-3037"
  - "data/game/bundles/bundle.properties:1-3042"
data:
  - "00-data/blocks.json"
depends: [WORLD.BLOCKS.001, WORLD.TERRAIN.001]
tags: [names, chinese-name, english-name, translation, mapping-table, terrain, ore, walls]
---

## One line

A Chinese name on screen is neither the id nor a literal translation of the English name; to cross-reference a map, the sandbox and a guide, use this table first to turn "the name you saw" into an id, then look up mechanics and numbers in the main articles.

## Rules / formulas

- The only source of a display name is the language bundle: `block.<id>.name` gives a block name and `<kind>.<id>.name` gives the remaining entities; this article only covers the terrain layer, `kind=block`.
- Grouping follows the `types` field in 00-data: the 136 entries containing `floor` / `wall` / `ore` are this article's scope, covering floors, ore layers, ore walls and editor-only terrain.
- A "—" in the table means the bundle has no `.name` entry for that id; it does not mean the name is unknown, because such blocks normally show no name in the UI (editor placeholders, legacy leftovers, ore overlays).
- A display string may carry colour markers (such as `[lightgray]`); the table strips the markers and keeps the text inside the parentheses.

## Numbers

This section lists names only and contains no numbers; health, size, armor and similar figures are in `00-data/blocks.json` and WORLD.BLOCKS.001.

| id | English name | Chinese name | Chinese name source | English name source |
|---|---|---|---|---|
| `air` | — | — | — | — |
| `arkycite-floor` | Arkycite | 芳油 | zh:2098 | en:2103 |
| `arkyic-stone` | Arkyic Stone | 芳石 | zh:2099 | en:2104 |
| `arkyic-vent` | Arkyic Vent | 芳石喷口 | zh:2102 | en:2107 |
| `basalt` | Basalt | 玄武岩 | zh:1930 | en:1935 |
| `basalt-vent` | Basalt Vent | 玄武岩喷口 | zh:2107 | en:2112 |
| `beryllic-stone` | Beryllic Stone | 铍石 | zh:2091 | en:2096 |
| `bluemat` | Bluemat | 蓝地垫 | zh:2109 | en:2114 |
| `carbon-stone` | Carbon Stone | 碳石 | zh:2088 | en:2093 |
| `carbon-vent` | Carbon Vent | 碳石喷口 | zh:2101 | en:2106 |
| `char` | Charred Stone | 焦土 | zh:1878 | en:1883 |
| `character-overlay` | Character Overlay | 标识贴片 | zh:1919 | en:1924 |
| `character-overlay-white` | Character Overlay (White) | 标识贴片 (白色) | zh:1920 | en:1925 |
| `colored-floor` | Colored Floor | 染色地板 | zh:1917 | en:1922 |
| `core-zone` | Core Zone | 核心区 | zh:2110 | en:2115 |
| `crater-stone` | Craters | 陨石坑 | zh:1875 | en:1880 |
| `crystal-floor` | Crystal Floor | 晶石地板 | zh:2093 | en:2098 |
| `crystalline-stone` | Crystalline Stone | 晶石 | zh:2092 | en:2097 |
| `crystalline-vent` | Crystalline Vent | 晶石喷口 | zh:2105 | en:2110 |
| `dacite` | Dacite | 安山岩 | zh:1879 | en:1884 |
| `dark-panel-1` | Dark Panel 1 | 暗面板 1 | zh:1923 | en:1928 |
| `dark-panel-2` | Dark Panel 2 | 暗面板 2 | zh:1924 | en:1929 |
| `dark-panel-3` | Dark Panel 3 | 暗面板 3 | zh:1925 | en:1930 |
| `dark-panel-4` | Dark Panel 4 | 暗面板 4 | zh:1926 | en:1931 |
| `dark-panel-5` | Dark Panel 5 | 暗面板 5 | zh:1927 | en:1932 |
| `dark-panel-6` | Dark Panel 6 | 暗面板 6 | zh:1928 | en:1933 |
| `darksand` | Dark Sand | 黑沙 | zh:1872 | en:1877 |
| `darksand-tainted-water` | Dark Sand Tainted Water | 黑沙污水 | zh:1868 | en:1873 |
| `darksand-water` | Dark Sand Water | 黑沙浅滩 | zh:1877 | en:1882 |
| `deep-tainted-water` | Deep Tainted Water | 深污水 | zh:1867 | en:1872 |
| `deep-water` | Deep Water | 深水 | zh:1864 | en:1869 |
| `dense-red-stone` | Dense Red Stone | 高密红石 | zh:2096 | en:2101 |
| `dirt` | Dirt | 泥土 | zh:1889 | en:1894 |
| `empty` | Empty | 空 | zh:2083 | en:2088 |
| `ferric-craters` | Ferric Craters | 铁陨石坑 | zh:2090 | en:2095 |
| `ferric-stone` | Ferric Stone | 铁石 | zh:2089 | en:2094 |
| `grass` | Grass | 草地 | zh:1829 | en:1834 |
| `hotrock` | Hot Rock | 灼热岩石 | zh:1931 | en:1936 |
| `ice` | Ice | 冰 | zh:1873 | en:1878 |
| `ice-snow` | Ice Snow | 冰雪地 | zh:1883 | en:1888 |
| `magmarock` | Magma Rock | 熔融岩石 | zh:1932 | en:1937 |
| `metal-floor` | Metal Floor 1 | 金属地板 1 | zh:1895 | en:1900 |
| `metal-floor-2` | Metal Floor 2 | 金属地板 2 | zh:1896 | en:1901 |
| `metal-floor-3` | Metal Floor 3 | 金属地板 3 | zh:1897 | en:1902 |
| `metal-floor-4` | Metal Floor 4 | 金属地板 4 | zh:1898 | en:1903 |
| `metal-floor-5` | Metal Floor 5 | 金属地板 5 | zh:1899 | en:1904 |
| `metal-floor-damaged` | Damaged Metal Floor | 损坏的金属地板 | zh:1900 | en:1905 |
| `metal-tiles-1` | Metal Tiles 1 | 金属地基 1 | zh:1901 | en:1906 |
| `metal-tiles-10` | Metal Tiles 10 | 金属地基 10 | zh:1910 | en:1915 |
| `metal-tiles-11` | Metal Tiles 11 | 金属地基 11 | zh:1911 | en:1916 |
| `metal-tiles-12` | Metal Tiles 12 | 金属地基 12 | zh:1912 | en:1917 |
| `metal-tiles-13` | Metal Tiles 13 | 金属地基 13 | zh:1913 | en:1918 |
| `metal-tiles-2` | Metal Tiles 2 | 金属地基 2 | zh:1902 | en:1907 |
| `metal-tiles-3` | Metal Tiles 3 | 金属地基 3 | zh:1903 | en:1908 |
| `metal-tiles-4` | Metal Tiles 4 | 金属地基 4 | zh:1904 | en:1909 |
| `metal-tiles-5` | Metal Tiles 5 | 金属地基 5 | zh:1905 | en:1910 |
| `metal-tiles-6` | Metal Tiles 6 | 金属地基 6 | zh:1906 | en:1911 |
| `metal-tiles-7` | Metal Tiles 7 | 金属地基 7 | zh:1907 | en:1912 |
| `metal-tiles-8` | Metal Tiles 8 | 金属地基 8 | zh:1908 | en:1913 |
| `metal-tiles-9` | Metal Tiles 9 | 金属地基 9 | zh:1909 | en:1914 |
| `molten-slag` | Slag | 矿渣液 | zh:1830 | en:1835 |
| `moss` | Moss | 苔藓地 | zh:1845 | en:1850 |
| `mud` | Mud | 泥巴 | zh:1891 | en:1896 |
| `ore-beryllium` | — | — | — | — |
| `ore-coal` | — | — | — | — |
| `ore-copper` | — | — | — | — |
| `ore-crystal-thorium` | — | — | — | — |
| `ore-lead` | — | — | — | — |
| `ore-scrap` | — | — | — | — |
| `ore-thorium` | — | — | — | — |
| `ore-titanium` | — | — | — | — |
| `ore-tungsten` | — | — | — | — |
| `ore-wall-beryllium` | — | — | — | — |
| `ore-wall-graphite` | — | — | — | — |
| `ore-wall-thorium` | — | — | — | — |
| `ore-wall-tungsten` | — | — | — | — |
| `pebbles` | Pebbles | 鹅卵石 | zh:1835 | en:1840 |
| `pooled-cryofluid` | Cryofluid | 冷冻液 | zh:1831 | en:1836 |
| `red-ice` | Red Ice | 红冰 | zh:2097 | en:2102 |
| `red-stone` | Red Stone | 红石 | zh:2095 | en:2100 |
| `red-stone-vent` | Red Stone Vent | 红石喷口 | zh:2104 | en:2109 |
| `redmat` | Redmat | 红地垫 | zh:2108 | en:2113 |
| `regolith` | Regolith | 风化岩 | zh:2086 | en:2091 |
| `remove-ore` | Remove Ore | 移除矿 | zh:1860 | en:1865 |
| `rhyolite` | Rhyolite | 流纹岩 | zh:1880 | en:1885 |
| `rhyolite-crater` | Rhyolite Crater | 流纹岩坑 | zh:2084 | en:2089 |
| `rhyolite-vent` | Rhyolite Vent | 流纹石喷口 | zh:2100 | en:2105 |
| `rough-rhyolite` | Rough Rhyolite | 粗糙流纹岩 | zh:2085 | en:2090 |
| `rune-overlay` | Rune Overlay | 符文贴片 | zh:1921 | en:1926 |
| `rune-overlay-crux` | Rune Overlay (Crux) | 符文贴片 （红队） | zh:1922 | en:1927 |
| `salt` | Salt | 盐碱地 | zh:1833 | en:1838 |
| `sand-floor` | Sand | 沙子 | zh:1871 | en:1876 |
| `sand-water` | Sand Water | 浅滩 | zh:1876 | en:1881 |
| `shale` | Shale | 页岩地 | zh:1843 | en:1848 |
| `shallow-water` | Water | 水 | zh:1865 | en:1870 |
| `snow` | Snow | 雪 | zh:1874 | en:1879 |
| `space` | Space | 太空 | zh:1832 | en:1837 |
| `spawn` | Enemy Spawn | 敌人出生点 | zh:1858 | en:1863 |
| `spore-moss` | Spore Moss | 孢子苔藓地 | zh:1847 | en:1852 |
| `stone` | Stone | 石头 | zh:1870 | en:1875 |
| `stone-vent` | Stone Vent | 岩石喷口 | zh:2106 | en:2111 |
| `tainted-water` | Tainted Water | 污水 | zh:1866 | en:1871 |
| `tar` | Tar | 石油 | zh:1869 | en:1874 |
| `tendrils` | Tendrils | 卷须 | zh:1836 | en:1841 |
| `yellow-stone` | Yellow Stone | 黄石 | zh:2087 | en:2092 |
| `yellow-stone-plates` | Yellow Stone Plates | 黄石地板 | zh:2094 | en:2099 |
| `yellow-stone-vent` | Yellow Stone Vent | 黄石喷口 | zh:2103 | en:2108 |
| `beryllium-wall` | Beryllium Wall | 铍墙 | zh:2156 | en:2161 |
| `beryllium-wall-large` | Large Beryllium Wall | 大型铍墙 | zh:2157 | en:2162 |
| `blast-door` | Blast Door | 防爆闸门 | zh:2160 | en:2165 |
| `carbide-wall` | Carbide Wall | 碳化物墙 | zh:2161 | en:2166 |
| `carbide-wall-large` | Large Carbide Wall | 大型碳化物墙 | zh:2162 | en:2167 |
| `copper-wall` | Copper Wall | 铜墙 | zh:1933 | en:1938 |
| `copper-wall-large` | Large Copper Wall | 大型铜墙 | zh:1934 | en:1939 |
| `door` | Door | 门 | zh:1943 | en:1948 |
| `door-large` | Large Door | 大门 | zh:1944 | en:1949 |
| `phase-wall` | Phase Wall | 相织布墙 | zh:1939 | en:1944 |
| `phase-wall-large` | Large Phase Wall | 大型相织布墙 | zh:1940 | en:1945 |
| `plastanium-wall` | Plastanium Wall | 塑钢墙 | zh:1937 | en:1942 |
| `plastanium-wall-large` | Large Plastanium Wall | 大型塑钢墙 | zh:1938 | en:1943 |
| `reinforced-surge-wall` | Reinforced Surge Wall | 强化合金墙 | zh:2163 | en:2168 |
| `reinforced-surge-wall-large` | Large Reinforced Surge Wall | 大型强化合金墙 | zh:2164 | en:2169 |
| `scrap-wall` | Scrap Wall | 废墙 | zh:1849 | en:1854 |
| `scrap-wall-gigantic` | Gigantic Scrap Wall | 超巨型废墙 | zh:1852 | en:1857 |
| `scrap-wall-huge` | Huge Scrap Wall | 巨型废墙 | zh:1851 | en:1856 |
| `scrap-wall-large` | Large Scrap Wall | 大型废墙 | zh:1850 | en:1855 |
| `shielded-wall` | Shielded Wall | 盾墙 | zh:2165 | en:2170 |
| `surge-wall` | Surge Wall | 合金墙 | zh:2032 | en:2037 |
| `surge-wall-large` | Large Surge Wall | 大型合金墙 | zh:2033 | en:2038 |
| `thorium-wall` | Thorium Wall | 钍墙 | zh:1941 | en:1946 |
| `thorium-wall-large` | Large Thorium Wall | 大型钍墙 | zh:1942 | en:1947 |
| `thruster` | Thruster | 推进器残骸 | zh:1853 | en:1858 |
| `titanium-wall` | Titanium Wall | 钛墙 | zh:1935 | en:1940 |
| `titanium-wall-large` | Large Titanium Wall | 大型钛墙 | zh:1936 | en:1941 |
| `tungsten-wall` | Tungsten Wall | 钨墙 | zh:2158 | en:2163 |
| `tungsten-wall-large` | Large Tungsten Wall | 大型钨墙 | zh:2159 | en:2164 |

## Source anchors

- `data/game/bundles/bundle_zh_CN.properties` - the Chinese display names; "Chinese name source zh:N" in the table is line N of that file.
- `data/game/bundles/bundle.properties` - the English display names; "English name source en:N" is line N of that file.
- `00-data/blocks.json` - the `id` / `types` / `category` fields; this article filters out 136 entries by `types` (122 of which have a Chinese name).
- The generator script `knowledge/tools/gen_name_docs.py` (re-run it after a game version update; it does not modify 00-data).

## Measurements and counter-examples

- **Counter-example A** - `dacite` has the English name "Dacite" (geologically dacite), yet the official Chinese name is andesite (安山岩); and andesite's English name is "Andesite" as well. The Chinese and English names do not line up, so matching by geological name goes wrong.
- **Counter-example B** - `char` has the English name "Charred Stone" and the Chinese name scorched earth (焦土) - neither a word-for-word translation nor a stone class (it is a floor).
- **Counter-example C** - ore layer ids such as `ore-copper` / `ore-lead` / `ore-thorium` have no `.name` entry at all in the bundle; they appear in the sandbox menu as textures with no name shown. Searching ids for copper ore (铜矿) always comes up empty - you have to cross-reference the resource table in WORLD.DRILLING.001.
- **Counter-example D** - the raw value of `block.launch-pad.name` is "launch pad (发射台)[lightgray] (legacy version)"; the colour marker is not part of the name, and copying it straight into a document drags `[lightgray]` along.
- **Counter-example E** - `build1`–`build16`, `air`, `target-dummy` and `legacy-*` likewise have no `.name`; they are editor placeholders or legacy leftovers and are invisible in the player UI.

## Common misconceptions

- Using the Chinese name as an id: conveyor (传送带) is not an id, `conveyor` is; documents, blueprints and logic only accept ids.
- Assuming the English name equals the id: `Titanium Conveyor` has spaces and capitals, while the id is `titanium-conveyor`.
- Assuming the Chinese name is a literal translation of the English one: Duo (双管), Dagger (尖刀), Mender (修理器) are none of them word-for-word.
- Assuming every block has a display name: 14 of the 136 entries here do not; a "—" means that block shows no name in the UI, not that the name is missing.

## Related

- WORLD.BLOCKS.001 (block model and multiblock anchors, the numeric conventions)
- WORLD.TERRAIN.001 (terrain, the ore-layer and wall three-layer structure, movement multipliers)
- WORLD.DRILLING.001 (ore layers and drill coverage, what ore-* is actually for)
- WORLD.SANDBOX.001 (editor visibility and the build series placeholders)
- WORLD.NAMES.002 / WORLD.NAMES.003 (the remaining block names)
- EV.CHEAT.001 (cheat sheet)
