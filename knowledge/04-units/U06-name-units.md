---
id: UNIT.NAMES.001
title: Unit name table — English and Chinese names for all 70 units (60 have an official Simplified Chinese name)
domain: unit
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "data/game/bundles/bundle_zh_CN.properties:1-3037"
  - "data/game/bundles/bundle.properties:1-3042"
data:
  - "00-data/units.json"
depends: [UNIT.MOVE.001, UNIT.PRODUCE.001]
tags: [names, Chinese name, English name, translation, lookup table, unit]
---

## One line

The Chinese names of the units against their ids. In the interface a unit shows only its name and never its id, while blueprints, logic and wave tables only know ids, so this table is the only bridge between the two.

## Rules / formulas

- The display-name key is `unit.<id>.name`; the numbers live in `00-data/units.json` (health, armor, speed, range and so on).
- There are 70 entries and 60 have an official Simplified Chinese name; the 10 that lack one are missile sub-units and a few internal placeholders.
- Units with no name (shown as "—" in the table): the missile types `*-missile`, `scathe-missile-*`, and the internal placeholders `block` / `dummy` / `turret-unit-build-tower`; in play they appear as ammunition or as build towers and never display a name.
- Units are sorted alphabetically by id; tiers (T1–T5) and the production chain are in UNIT.PRODUCE.001 and are not part of this table.

## Numbers

This section lists names only, no numbers; for speed units, hitSize, armor and the rest see UNIT.MOVE.001 and `00-data/units.json`.

| id | English name | Chinese name | Chinese name source | English name source |
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

## Source anchors

- `data/game/bundles/bundle_zh_CN.properties` (zh:N) and `bundle.properties` (en:N).
- `00-data/units.json`: 70 unit records, with `id` mapping one-to-one onto the bundle key.
- The generator script `knowledge/tools/gen_name_docs.py`.

## Measurements and counter-examples

- Counterexample 1: unit names are imagery, not function names — `dagger` (尖刀, a blade), `mace` (战锤, a warhammer), `fortress` (堡垒), `scepter` (权杖), `reign` (王座). Searching the Chinese names for "dagger" or "hammer" turns up nothing.
- Counterexample 2: two naming strategies coexist in one table — the official Chinese name of `anthicus` is a semantic coinage (天灾, "disaster") rather than a transliteration (安提库斯), while `alpha` / `beta` / `gamma` are pure transliterations (阿尔法, 贝塔, 伽马).
- Counterexample 3: `crawler` (爬虫) and `atrax` (毒蛛) are imagery in both languages, while `alpha` / `beta` / `gamma` keep the Greek letters as transliterations (阿尔法, 贝塔, 伽马).
- Counterexample 4: missile sub-units (such as `anthicus-missile`) have no display name, so searching the Chinese word for "missile" finds only the unit that fires them, `anthicus`, never the sub-unit itself.

## Common misconceptions

- Thinking unit names carry T1, T2: tier is not part of the name, and the official strings contain no level wording.
- Thinking the English name translates straight into an id: `Fortress` → `fortress` works, but colon-bearing names such as `Core: Shard` appear only in the block table.
- Thinking nameless units are a data gap: all 10 have records and numbers, the language bundle simply does not display a name for them.

## Related

- UNIT.MOVE.001 (speed units and terrain)
- UNIT.PRODUCE.001 (production chain and unit cap)
- UNIT.AI.001 (unit AI and commands)
- UNIT.ABILITY.001 (the 16 Ability classes)
- UNIT.PROGRESSION.001 (tiers and the wave table)
- COMBAT.UNITWEAPON.001 (unit weapons and DPS)
- WORLD.NAMES.001 / 002 / 003 / 004 (block and item names)
