---
tokens: 744
id: UNIT.NAMES.001
title: 单位名对照：70 个单位的英文名与中文名（其中 60 个有官方简中）
domain: unit
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "assetsraw/assets/bundles/bundle_zh_CN.properties:1-3038"
  - "assetsraw/assets/bundles/bundle.properties:1-3438"
data:
  - "00-data/units.json"
depends: [UNIT.MOVE.001, UNIT.PRODUCE.001]
tags: [名词, 中文名, 英文名, 翻译, 对照表, 单位]
---

## 一句话

单位的中文名与 id 对照。单位在界面只显示名字、不显示 id，而蓝图、逻辑、波次表只认 id，所以这张表是两边唯一的桥。

## 规则 / 公式

- 显示名 key 是 `unit.<id>.name`；数值在 `00-data/units.json`（血量、护甲、速度、射程等）。
- 共 70 条，60 条有官方简中名；缺名的 10 条集中在导弹子单位与几个内部占位单位。
- 缺名单位（表内「—」）：导弹类 `*-missile`、`scathe-missile-*`，以及内部占位 `block` / `dummy` / `turret-unit-build-tower`；它们在实战中以弹药或建造塔出现，不单独显示名字。
- 单位按 id 字母序排列；档次（T1～T5）与生产链见 UNIT.PRODUCE.001，不在这张表里。

## 数值

本节只列名词，不含数值；速度单位、hitSize、护甲等见 UNIT.MOVE.001 与 `00-data/units.json`。

| id | 英文名 | 中文名 | 中文名出处 | 英文名出处 |
|---|---|---|---|---|
| `aegires` | Aegires | 玄武 | zh:1792 | en:1797 |
| `alpha` | Alpha | 阿尔法 | zh:1794 | en:1799 |
| `anthicus` | Anthicus | 天灾 | zh:1809 | en:1814 |
| `anthicus-missile` | — | — | — | — |
| `antumbra` | Antumbra | 月影 | zh:1777 | en:1782 |
| `arkyid` | Arkyid | 毒蛊 | zh:1772 | en:1777 |
| `assembly-drone` | Assembly Drone | 装配无人机 | zh:1821 | en:1826 |
| `atrax` | Atrax | 毒蛛 | zh:1770 | en:1775 |
| `avert` | Avert | 遮蔽 | zh:1813 | en:1818 |
| `beta` | Beta | 贝塔 | zh:1795 | en:1800 |
| `block` | — | — | — | — |
| `bryde` | Bryde | 戟鲸 | zh:1786 | en:1791 |
| `cleroi` | Cleroi | 天赐 | zh:1808 | en:1813 |
| `collaris` | Collaris | 天帝 | zh:1811 | en:1816 |
| `conquer` | Conquer | 领主 | zh:1806 | en:1811 |
| `corvus` | Corvus | 死星 | zh:1800 | en:1805 |
| `crawler` | Crawler | 爬虫 | zh:1769 | en:1774 |
| `cyerce` | Cyerce | 江豚 | zh:1791 | en:1796 |
| `dagger` | Dagger | 尖刀 | zh:1763 | en:1768 |
| `disrupt` | Disrupt | 悲怆 | zh:1816 | en:1821 |
| `disrupt-missile` | — | — | — | — |
| `dummy` | — | — | — | — |
| `eclipse` | Eclipse | 日蚀 | zh:1778 | en:1783 |
| `elude` | Elude | 挣脱 | zh:1812 | en:1817 |
| `emanate` | Emanate | 发散 | zh:1819 | en:1824 |
| `evoke` | Evoke | 苏醒 | zh:1817 | en:1822 |
| `flare` | Flare | 星辉 | zh:1774 | en:1779 |
| `fortress` | Fortress | 堡垒 | zh:1765 | en:1770 |
| `gamma` | Gamma | 伽马 | zh:1796 | en:1801 |
| `horizon` | Horizon | 天垠 | zh:1775 | en:1780 |
| `incite` | Incite | 策动 | zh:1818 | en:1823 |
| `latum` | Latum | Latum | zh:1822 | en:1827 |
| `locus` | Locus | 循迹 | zh:1803 | en:1808 |
| `mace` | Mace | 战锤 | zh:1764 | en:1769 |
| `manifold` | Manifold | 货运无人机 | zh:1820 | en:1825 |
| `mega` | Mega | 巨像 | zh:1781 | en:1786 |
| `merui` | Merui | 天守 | zh:1807 | en:1812 |
| `minke` | Minke | 飞鲨 | zh:1785 | en:1790 |
| `mono` | Mono | 独影 | zh:1779 | en:1784 |
| `navanax` | Navanax | 龙王 | zh:1793 | en:1798 |
| `nova` | Nova | 新星 | zh:1766 | en:1771 |
| `obviate` | Obviate | 消散 | zh:1814 | en:1819 |
| `oct` | Oct | 要塞 | zh:1783 | en:1788 |
| `omura` | Omura | 海神 | zh:1788 | en:1793 |
| `oxynoe` | Oxynoe | 电鳗 | zh:1790 | en:1795 |
| `poly` | Poly | 幻型 | zh:1780 | en:1785 |
| `precept` | Precept | 准绳 | zh:1804 | en:1809 |
| `pulsar` | Pulsar | 恒星 | zh:1767 | en:1772 |
| `quad` | Quad | 雷霆 | zh:1782 | en:1787 |
| `quasar` | Quasar | 耀星 | zh:1768 | en:1773 |
| `quell` | Quell | 遏止 | zh:1815 | en:1820 |
| `quell-missile` | — | — | — | — |
| `reign` | Reign | 王座 | zh:1798 | en:1803 |
| `renale` | Renale | Renale | zh:1823 | en:1828 |
| `retusa` | Retusa | 潜螺 | zh:1789 | en:1794 |
| `risso` | Risso | 梭鱼 | zh:1784 | en:1789 |
| `scathe-missile` | — | — | — | — |
| `scathe-missile-phase` | — | — | — | — |
| `scathe-missile-surge` | — | — | — | — |
| `scathe-missile-surge-split` | — | — | — | — |
| `scepter` | Scepter | 权杖 | zh:1797 | en:1802 |
| `sei` | Sei | 蛟龙 | zh:1787 | en:1792 |
| `spiroct` | Spiroct | 血蛭 | zh:1771 | en:1776 |
| `stell` | Stell | 围护 | zh:1802 | en:1807 |
| `tecta` | Tecta | 天理 | zh:1810 | en:1815 |
| `toxopid` | Toxopid | 天蝎 | zh:1773 | en:1778 |
| `turret-unit-build-tower` | — | — | — | — |
| `vanquish` | Vanquish | 征服 | zh:1805 | en:1810 |
| `vela` | Vela | 灾星 | zh:1799 | en:1804 |
| `zenith` | Zenith | 苍穹 | zh:1776 | en:1781 |

## 源码锚点

- `assetsraw/assets/bundles/bundle_zh_CN.properties`（zh:N）与 `bundle.properties`（en:N）。
- `00-data/units.json`：70 条单位记录，`id` 与 bundle key 一一对应。
- 生成脚本 `knowledge/tools/gen_name_docs.py`。

## 实测与反例

- 反例一：单位名是意象词而不是功能名——`dagger`=尖刀、`mace`=战锤、`fortress`=堡垒、`scepter`=权杖、`reign`=王座。按「匕首」「锤子」搜中文名对不上。
- 反例二：同一张表里两种命名策略并存——`anthicus` 官方中文是「天灾」（意译造词，不是音译的「安提库斯」），而 `alpha` / `beta` / `gamma` 是纯音译（阿尔法、贝塔、伽马）。
- 反例三：`crawler`=爬虫、`atrax`=毒蛛，英文名与中文名都是意象；而 `alpha` / `beta` / `gamma` 直接保留希腊字母音译（阿尔法、贝塔、伽马）。
- 反例四：导弹子单位（如 `anthicus-missile`）无显示名，按「导弹」反查只能查到发射它的单位 `anthicus`，不是它本身。

## 常见误解

- 以为单位名带 T1、T2：档次不是名字的一部分，官方串里没有等级字样。
- 以为英文名可直译成 id：`Fortress` → `fortress` 可以，但 `Core: Shard` 这类带冒号的名字只出现在方块表。
- 以为缺名单位是数据遗漏：10 个缺名单位都有记录、有数值，只是语言包不显示名字。

## 相关

- UNIT.MOVE.001（速度单位与地形）
- UNIT.PRODUCE.001（生产链与单位上限）
- UNIT.AI.001（单位 AI 与指令）
- UNIT.ABILITY.001（16 类 Ability）
- UNIT.PROGRESSION.001（档次与波次表）
- COMBAT.UNITWEAPON.001（单位武器与 DPS）
- WORLD.NAMES.001 / 002 / 003 / 004（方块与物品名）
