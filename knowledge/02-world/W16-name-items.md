---
tokens: 721
id: WORLD.NAMES.004
title: 物品 / 液体 / 状态效果名对照（56 条）
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "assets/bundles/bundle_zh_CN.properties:1-3038"
  - "assets/bundles/bundle.properties:1-3438"
data:
  - "00-data/items.json"
  - "00-data/liquids.json"
  - "00-data/status.json"
depends: [WORLD.CRAFTING.001, COMBAT.STATUS.001]
tags: [名词, 中文名, 英文名, 翻译, 对照表, 物品, 液体, 状态]
---

## 一句话

物品、液体、状态效果三类实体的显示名对照——这三类在界面上只有名字没有方块 id，是把配方表、状态图标、液体色块翻译回 id 的唯一入口。

## 规则 / 公式

- key 规则：`item.<id>.name` / `liquid.<id>.name` / `status.<id>.name`；三张表的记录见 00-data。
- 顺序：物品 22 条（`00-data/items.json`）→ 液体 11 条（`liquids.json`）→ 状态 23 条（`status.json`），组内按 id 字母序。
- 状态里有 `none` / `invincible` / `dynamic` 三个「无名」项：它们不是玩家可获状态，语言包没有对应显示名，表内记「—」。
- 物品名多为物质名（铜、铅、硅），液体名多为液体名（水、矿渣、石油），状态名多为形容词（缓慢、过载、缴械）。

## 数值

本节只列名词；硬度、造价、可燃性、倍率等数值见 `00-data/items.json` / `liquids.json` / `status.json`，口径见 COMBAT.STATUS.001。

### 物品

| id | 英文名 | 中文名 | 中文名出处 | 英文名出处 |
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

### 液体

| id | 英文名 | 中文名 | 中文名出处 | 英文名出处 |
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

### 状态效果

| id | 英文名 | 中文名 | 中文名出处 | 英文名出处 |
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

## 源码锚点

- `assets/bundles/bundle_zh_CN.properties`（zh:N）与 `bundle.properties`（en:N）。
- `00-data/items.json`（22 条）/ `liquids.json`（11 条）/ `status.json`（23 条）；三类共 56 条，53 条有中文名。
- 生成脚本 `knowledge/tools/gen_name_docs.py`。

## 实测与反例

- 反例一：`plastanium` 中文是「塑钢」，不是「塑料」；`phase-fabric` 是「相织布」而不是「相位布」——按英文词根直译会错。
- 反例二：`pyratite` 官方中文「硫化物」，和 pyrite（黄铁矿）不是一回事；英文名形近但中文串完全不同。
- 反例三：`surge-alloy` 是「巨浪合金」，不是「电涌合金」；`carbide` 是「碳化物」、`oxide` 是「氧化物」，与 `beryllium`「铍」同属合金体系但命名不统一。
- 反例四：状态 `none` / `invincible` / `dynamic` 查不到中文名，若按「无状态」「无敌」去反查 id 会得到空结果；正确 id 就是字面那三个。
- 反例五：液体 `neoplasm` 是「瘤液」、`arkycite` 是「芳油」、`gallium` 是「镓液」——三条中只有 gallium 保留了元素名的「液」后缀。

## 常见误解

- 以为状态名就是方块名：`overdrive` 既是状态也是方块 `overdrive-projector` 的产物，两个 id 不同名。
- 以为液体名与物品名同表：`water` / `slag` 只在 liquids 表，`sand` / `coal` 只在 items 表；跨表按名字查会漏。
- 以为每个状态都有中文名：23 条里有 3 条没有（三个特殊状态）。

## 相关

- WORLD.CRAFTING.001（配方与产物）
- WORLD.LIQUIDS.001（液体属性与导管）
- COMBAT.STATUS.001（状态倍率与叠加）
- WORLD.NAMES.001 / WORLD.NAMES.002 / WORLD.NAMES.003（方块名）
- UNIT.NAMES.001（单位名）
