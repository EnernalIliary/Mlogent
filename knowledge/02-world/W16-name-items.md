---
id: WORLD.NAMES.004
title: Item / liquid / status effect name mapping (56 entries)
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "data/game/bundles/bundle_zh_CN.properties:1-3037"
  - "data/game/bundles/bundle.properties:1-3042"
data:
  - "00-data/items.json"
  - "00-data/liquids.json"
  - "00-data/status.json"
depends: [WORLD.CRAFTING.001, COMBAT.STATUS.001]
tags: [names, chinese-name, english-name, translation, mapping-table, item, liquid, status]
---

## One line

The display-name mapping for the three entity classes - items, liquids and status effects - which show only a name in the UI and have no block id; it is the only way back from a recipe table, a status icon or a liquid swatch to an id.

## Rules / formulas

- Key rule: `item.<id>.name` / `liquid.<id>.name` / `status.<id>.name`; the records behind the three tables are in 00-data.
- Order: 22 items (`00-data/items.json`) → 11 liquids (`liquids.json`) → 23 statuses (`status.json`), alphabetical by id inside each group.
- Three statuses are "nameless" entries: `none` / `invincible` / `dynamic`; they are not player-obtainable statuses and the bundle has no display name for them, so the table records a "—".
- Item names are mostly substance names (copper, lead, silicon), liquid names are mostly liquid names (water, slag, oil), and status names are mostly adjectives (slow, overload, disarmed).

## Numbers

This section lists names only; hardness, cost, flammability, multipliers and similar numbers are in `00-data/items.json` / `liquids.json` / `status.json`, with conventions in COMBAT.STATUS.001.

### Items

| id | English name | Chinese name | Chinese name source | English name source |
|---|---|---|---|---|
| `beryllium` | Beryllium | 铍 | zh:1745 | en:1750 |
| `blast-compound` | Blast Compound | 爆炸混合物 | zh:1740 | en:1745 |
| `carbide` | Carbide | 碳化物 | zh:1748 | en:1753 |
| `coal` | Coal | 煤炭 | zh:1730 | en:1735 |
| `copper` | Copper | 铜 | zh:1728 | en:1733 |
| `dormant-cyst` | Dormant Cyst | 休眠囊肿 | zh:1749 | en:1754 |
| `fissile-matter` | Fissile Matter | 裂变产物 | zh:1744 | en:1749 |
| `graphite` | Graphite | 石墨 | zh:1731 | en:1736 |
| `lead` | Lead | 铅 | zh:1729 | en:1734 |
| `metaglass` | Metaglass | 钢化玻璃 | zh:1742 | en:1747 |
| `oxide` | Oxide | 氧化物 | zh:1747 | en:1752 |
| `phase-fabric` | Phase Fabric | 相织布 | zh:1736 | en:1741 |
| `plastanium` | Plastanium | 塑钢 | zh:1735 | en:1740 |
| `pyratite` | Pyratite | 硫化物 | zh:1741 | en:1746 |
| `sand` | Sand | 沙 | zh:1739 | en:1744 |
| `scrap` | Scrap | 废料 | zh:1743 | en:1748 |
| `silicon` | Silicon | 硅 | zh:1734 | en:1739 |
| `spore-pod` | Spore Pod | 孢子荚 | zh:1738 | en:1743 |
| `surge-alloy` | Surge Alloy | 巨浪合金 | zh:1737 | en:1742 |
| `thorium` | Thorium | 钍 | zh:1733 | en:1738 |
| `titanium` | Titanium | 钛 | zh:1732 | en:1737 |
| `tungsten` | Tungsten | 钨 | zh:1746 | en:1751 |

### Liquids

| id | English name | Chinese name | Chinese name source | English name source |
|---|---|---|---|---|
| `arkycite` | Arkycite | 芳油 | zh:1756 | en:1761 |
| `cryofluid` | Cryofluid | 冷冻液 | zh:1754 | en:1759 |
| `cyanogen` | Cyanogen | 氰气 | zh:1761 | en:1766 |
| `gallium` | Gallium | 镓液 | zh:1757 | en:1762 |
| `hydrogen` | Hydrogen | 氢气 | zh:1759 | en:1764 |
| `neoplasm` | Neoplasm | 瘤液 | zh:1755 | en:1760 |
| `nitrogen` | Nitrogen | 氮气 | zh:1760 | en:1765 |
| `oil` | Oil | 石油 | zh:1753 | en:1758 |
| `ozone` | Ozone | 臭氧 | zh:1758 | en:1763 |
| `slag` | Slag | 矿渣 | zh:1752 | en:1757 |
| `water` | Water | 水 | zh:1751 | en:1756 |

### Status effects

| id | English name | Chinese name | Chinese name source | English name source |
|---|---|---|---|---|
| `blasted` | Blasted | 爆炸 | zh:1081 | en:1086 |
| `boss` | Guardian | Boss | zh:1084 | en:1089 |
| `burning` | Burning | 燃烧 | zh:1069 | en:1074 |
| `corroded` | Corroded | 腐蚀 | zh:1082 | en:1087 |
| `disarmed` | Disarmed | 缴械 | zh:1088 | en:1093 |
| `dynamic` | — | — | — | — |
| `electrified` | Electrified | 麻痹 | zh:1075 | en:1080 |
| `fast` | Fast | 迅捷 | zh:1086 | en:1091 |
| `freezing` | Freezing | 冻结 | zh:1070 | en:1075 |
| `invincible` | — | — | — | — |
| `melting` | Melting | 熔化 | zh:1073 | en:1078 |
| `muddy` | Muddy | 泥泞 | zh:1072 | en:1077 |
| `none` | — | — | — | — |
| `overclock` | Overclock | 超频 | zh:1079 | en:1084 |
| `overdrive` | Overdrive | 过载 | zh:1078 | en:1083 |
| `sapped` | Sapped | 弱化 | zh:1074 | en:1079 |
| `shielded` | Shielded | 保护 | zh:1087 | en:1092 |
| `shocked` | Shocked | 电击 | zh:1080 | en:1085 |
| `slow` | Slow | 缓慢 | zh:1085 | en:1090 |
| `spore-slowed` | Spore Slowed | 孢子减速 | zh:1076 | en:1081 |
| `tarred` | Tarred | 油浸 | zh:1077 | en:1082 |
| `unmoving` | Unmoving | 静止 | zh:1083 | en:1088 |
| `wet` | Wet | 潮湿 | zh:1071 | en:1076 |

## Source anchors

- `data/game/bundles/bundle_zh_CN.properties` (zh:N) and `bundle.properties` (en:N).
- `00-data/items.json` (22 entries) / `liquids.json` (11 entries) / `status.json` (23 entries); 56 entries across the three classes, 53 of them with a Chinese name.
- Generator script `knowledge/tools/gen_name_docs.py`.

## Measurements and counter-examples

- **Counter-example A** - `plastanium` is plastic-steel (塑钢), not plastic (塑料); `phase-fabric` is phase fabric (相织布), not phase cloth (相位布) - literal readings by English root go wrong.
- **Counter-example B** - `pyratite` is officially sulfide (硫化物), which is not the same thing as pyrite (黄铁矿); the English names look alike but the Chinese strings are completely different.
- **Counter-example C** - `surge-alloy` is officially surge alloy (巨浪合金), not surge alloy (电涌合金); `carbide` is carbide (碳化物) and `oxide` is oxide (氧化物), which belong to the same alloy family as `beryllium`, beryllium (铍), yet the naming is not uniform.
- **Counter-example D** - the statuses `none` / `invincible` / `dynamic` have no Chinese name, so reverse-looking up an id from "no status" or "invincible" returns nothing; the correct ids are literally those three.
- **Counter-example E** - the liquid `neoplasm` is tumor fluid (瘤液), `arkycite` is arkycite (芳油) and `gallium` is gallium liquid (镓液); of the three, only gallium keeps the liquid (液) suffix of an element name.

## Common misconceptions

- Assuming a status name is a block name: `overdrive` is both a status and the product of the block `overdrive-projector`; the two ids are named differently.
- Assuming liquid names and item names share a table: `water` / `slag` are only in the liquids table and `sand` / `coal` only in the items table, so a name lookup across tables misses.
- Assuming every status has a Chinese name: 3 of the 23 do not (the three special statuses).

## Related

- WORLD.CRAFTING.001 (recipes and products)
- WORLD.LIQUIDS.001 (liquid properties and conduits)
- COMBAT.STATUS.001 (status multipliers and stacking)
- WORLD.NAMES.001 / WORLD.NAMES.002 / WORLD.NAMES.003 (block names)
- UNIT.NAMES.001 (unit names)
