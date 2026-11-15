---
id: CAMP.DIFFICULTY.001
title: 难度系数换算卡——三元组如何变成血量、数量、造价与波次间隔
domain: camp
status: active
ver: [v159.3_src, v160.7_rt]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/game/Difficulty.java:5-21"
  - "Mindustry-Source/core/src/mindustry/game/CampaignRules.java:39-42"
  - "Mindustry-Source/core/src/mindustry/game/Rules.java:85-87,111,302-304,374-384"
  - "Mindustry-Source/core/src/mindustry/ai/WaveSpawner.java:77-82"
  - "Mindustry-Source/core/src/mindustry/game/Waves.java:258-260,299-302,436-441"
  - "Mindustry-Source/core/src/mindustry/maps/planet/SerpuloPlanetGenerator.java:730"
data: [00-data/formulas.json, 00-data/constants_rules_difficulty_drill_heat.json]
depends: [CAMP.WAVES.001, CAMP.SPAWN.001]
tags: [难度, 战役, 三元组, 敌血, 数量倍率, 造价]
tokens: 616
---

## 一句话

难度就是三个浮点数 `(enemyHealthMultiplier, enemySpawnMultiplier, waveTimeMultiplier)`；`CampaignRules` 把它们写进**敌方阵营**的 4 个 team 规则字段，于是「难度」= 敌血 ×N、敌数 ×M、波时 ×T 三件事，**完全不含伤害倍率**。

## 规则 / 公式

```
Difficulty 枚举 = (enemyHealthMultiplier, enemySpawnMultiplier, waveTimeMultiplier)   [Difficulty.java:5-10]

CampaignRules.apply 时写入 waveTeam：                                                  [CampaignRules.java:39-42]
  team.blockHealthMultiplier    = enemyHealthMultiplier
  team.unitHealthMultiplier     = enemyHealthMultiplier
  team.unitCostMultiplier       = 1 / enemySpawnMultiplier
  team.unitBuildSpeedMultiplier = enemySpawnMultiplier

有效血量 = type.health × max(rules.unitHealthMultiplier × team.unitHealthMultiplier, 1e-6)   [Rules.java:302-304]
每波数量 = round(getSpawned(w) × enemySpawnMultiplier)   （非 boss 组）                          [WaveSpawner.java:80-81]
          = (int)(getSpawned(w) × enemySpawnMultiplier) （boss 组，向下取整，1.5×1 不会变 2 个）
波次间隔 = waveSpacing × waveTimeMultiplier                                                [Logic.java:322]
压力指数 P = enemyHealthMultiplier × enemySpawnMultiplier / waveTimeMultiplier
```

生成（随机）地图还有两层难度曲线：

```
generate(difficulty) → generate(pow(difficulty, 1.12), ...)     [Waves.java:258-260]
开局整体前移 shift = max((int)(difficulty*14 - 5), 0) 波          [Waves.java:436-441]
  d=0.4 → shift 0；d=0.6 → shift 3；d=1.0 → shift 9
```

## 数值

| 难度 | 敌血倍率 | 数量倍率 | 波时倍率 | 敌方造价 | 敌方造速 | 压力指数 P | 来源 |
|---|---|---|---|---|---|---|---|
| casual | 0.5 | 0.5 | 2.0 | ×2.0 | ×0.5 | 0.125 | [v160.7] |
| easy | 1.0 | 0.75 | 1.5 | ×1.33 | ×0.75 | 0.500 | [v160.7] |
| normal | 1.0 | 1.0 | 1.0 | ×1.0 | ×1.0 | 1.000 | [v160.7] |
| hard | 1.25 | 1.5 | 0.8 | ×0.67 | ×1.5 | 2.344 | [v160.7] |
| eradication | 1.5 | 2.0 | 0.6 | ×0.5 | ×2.0 | 5.000 | [v160.7] |

三元组为 [verified v160.7]（jar 反射逐值核对：0.5/0.5/2.0、1.0/0.75/1.5、1.0/1.0/1.0、1.25/1.5/0.8、1.5/2.0/0.6）；造价/造速两列由上面的倒数与直乘公式算出，压力指数为 P 的三项运算结果。

| 同一张图、同一单位 | casual | normal | eradication | 来源 |
|---|---|---|---|---|
| 单位类型 health = 200 的敌人 | 100 | 200 | 300 | Rules.java:302-304 代入 |
| 非 boss 组 getSpawned = 6 的实际刷出 | 3 | 6 | 12 | WaveSpawner.java:80-81 代入 |
| 到达第 30 波时刻 | 7440 s | 3720 s | 2232 s | CAMP.WAVES.001 的 T(N) |
| 进攻模式胜利波数 winWave | — | 10+5×max(d×10,1) | — | SerpuloPlanetGenerator.java:730 |

## 源码锚点

- Difficulty.java:5-10 五档三元组；:15-21 字段与构造顺序（enemyHealth / enemySpawn / waveTime）。
- CampaignRules.java:39-42 三元组 → team 的 4 个字段（blockHealth / unitHealth / unitCost 的倒数 / unitBuildSpeed）。
- Rules.java:85,87,111 全局倍率默认 1；:374-384 TeamRules 的同名三字段；:302-304 `unitHealth(team)` 取乘积且下限 1e-6。
- WaveSpawner.java:77-82 数量乘难度后 `Mathf.round`（boss 用 `(int)`）。
- Waves.java:258-260 `pow(difficulty,1.12)`；:299-302 生成地图的 cap=150、shieldsPerWave=20+d×30；:436-441 shift [src: Waves.java:258-302,436-441]。
- SerpuloPlanetGenerator.java:730 进攻模式 `winWave = 10 + 5×max(d×10,1)`。

## 实测与反例

**反例 1：以为高难度敌人伤害更高。** 难度三元组里没有伤害项，`rules.unitDamageMultiplier` 也不被 CampaignRules 改写（全局默认 1 [verified v160.7]）——eradication 下敌人子弹的基础伤害与 casual 相同，变的是血量（÷1.5 血）与同时在场数量（×4）。

**反例 2：以为 enemySpawnMultiplier 只影响刷怪。** 它还让敌方 AI 的兵**更便宜（unitCost ÷ M）且造得更快（unitBuildSpeed × M）**；所以 hard 难度下敌方生产线的实际产能是 normal 的 1.5 倍建速。

**反例 3：以为 hard 只是「血多 25%」。** 同时数量 ×1.5、间隔 ×0.8 → P = 1.25×1.5/0.8 ≈ 2.34，等效压力是 normal 的 2.34 倍，而非 1.25。

**反例 4：以为难度直接改 SpawnGroup 的护盾。** 固定关卡里护盾由 `shields/shieldScaling` 决定；随机生成地图的 `shieldsPerWave = 20 + difficulty×30` 才含难度项（Waves.java:301），两者别混。

**可复算**：某单位 `type.health=200`、某非 boss 组 `getSpawned=6` → normal 实际刷出 6 只、每只 200 血；eradication 刷出 `round(12)=12` 只、每只 `200×1.5=300` 血，同屏等效血量池 1200 → 3600（3 倍），再叠加波次间隔 0.6 倍，压力指数 5.0（代入见 00-data/formulas.json DATA.FORMULA.012/013）。

## 常见误解

- 「难度影响的是伤害」→ 不；只影响敌血、敌数、敌造速/造价、波时。
- 「casual 只是怪少」→ 血也减半、波次间隔翻倍（P=0.125，是 normal 的 1/8）[v160.7]。
- 「难度在 Rules 里直接改」→ 战役是 `CampaignRules` 写 team 字段；沙盒改 Rules 不会动这三元组。
- 「难度改的是波数上限」→ 波数上限由 `winWave`/地图决定，与难度无关（进攻模式例外，见 SerpuloPlanetGenerator.java:730）。

## 相关

- [[CAMP.WAVES.001]] 波次计时与 T(N) 的完整推导
- [[CAMP.SPAWN.001]] SpawnGroup 的实参与每波数量/护盾公式
- DATA.FORMULA.013 难度三元组与派生字段
- DATA.FORMULA.012 波次血量缩放（结论：不随波数增长）
