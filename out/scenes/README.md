# mlogsim 场景文件（v2：优先 `.msav`）

场景是给 `mlogsim` 用的“世界切片”：地图、队伍、核心、建筑、单位都摆好，
加载后直接跑逻辑，不用每次手搓 `--init-js`。

## 用哪种文件

| 格式 | 带地图/地形 | 带队伍 | 带单位 | 用途 |
|---|---|---|---|---|
| `.msav` 存档 | 是 | 是 | 是 | **首选**。游戏里摆好、存档、丢过来即可 |
| `.msch` 蓝图 | 否（只有建筑） | 否（贴图时同队） | 否 | 只测“几个方块 + 跨处理器链接”的小场景 |

`.msav` 一图一文件，不拼大图：存档已经自带 64×64 地图，拼图不会更省事，
坏一个还会连累全部。

## `.msav` 约定

- 位置随意；`--save` 接受绝对路径。
- 尺寸 ≤ 64×64（模拟器默认世界大小就是 64）；更大的图也能载，但处理器
  自动落位只在我方核心附近找空地。
- 我方 = `sharded`（和游戏里一样）。敌方用 `crux` 或任意敌队。
- 处理器不用摆：`mlogsim` 自动放在我方核心旁边的空地上（`--base X,Y` 可指定）。
- 存档里的世界时钟会被归零一次，所以 `@tick`/`@time` 每次从 0 开始，跑两遍
  结果一致；不要依赖存档里原来的绝对 tick。
- 炮台等建筑在 `--update all` 下会自动开火；会动的防守单位要加 `--unit-ai all`
  才会按游戏 AI 行动。`CommandAI` 单位没有命令时仍然不动（原版服务器没有指挥官）。

## `.msch` 约定（小场景）

- 位置：`out/scenes/<name>.msch`，≤ 64×64。
- 只放建筑（墙、核心、工厂、炮台、内存格……），**不要放处理器**。
- 加载时按最小 x/y 归一到 (0,0)；地板统一铺 stone。
- 默认整张图算敌方（`crux`）；需要在 `out/scenes/scenes.json` 里用 `ours`
  矩形声明我方，`start` 指定处理器落点。

```json
{
  "wall": { "start": [4, 32], "ours": [[0, 28, 8, 36]], "enemy_team": "crux" }
}
```

## 跑法

```bash
# 存档场景，跑 mlog，60 tick，世界更新 + 战斗，记录轨迹
python tools/mlogsim.py my.mlog --save scene.msav --ticks 60 --trace out/t.csv

# 让场景里的防守单位也行动
python tools/mlogsim.py my.mlog --save scene.msav --ticks 60 --unit-ai all

# 只看逻辑、不跑世界
python tools/mlogsim.py my.mlog --save scene.msav --ticks 60 --update none
```

## 已有场景

| 文件 | 覆盖 |
|---|---|
| `Mlog场景-进攻-open.msav` | 空旷对峙、远距离寻的、射程保持 |
| `Mlog场景-进攻-garded-line.msav` | 防御线、炮台集火、进攻方生存 |
| `Mlog场景-进攻-maze.msav` | 墙/迷宫、卡墙、寻路失败 |

## 还需要什么（按优先级）

写逻辑时真正卡住的不是“能不能编译”，而是**世界语义**：程序以为自己在打核心，实际在撞墙；以为单位在射程内，实际差 0.3 格。下面每类场景只回答一个问题：程序在这样的世界里，行为对不对。

### P0：先做这 6 个（覆盖大多数逻辑）

| 场景 | 摆什么 | 验证什么 | 建议断言 |
|---|---|---|---|
| `sensor-bench` | 我方核心旁一排不同单位：dagger、flare、mono、mega、fortress，`flag` 分别设 1..5（其中一个不设，留 null） | `sensor` 能读到什么：`@health/@armor/@shield/@range/@speed/@flag/@team/@type/@controlled/@dead/@x/@y`；null 与 0 的区别 | `flag == 3`、`dead == 0`、`hp > 0` |
| `control-bench` | 我方核心 + 目标点 + 一堵留 8 格口的墙 + dagger/flare/mono | `ucontrol move/approach/pathfind/within/stop/boost/flag/mine` 的真实位移与到达判定 | `dist < 2`、`within` 翻 1 |
| `processor-bench` | micro、logic、hyper、world 各一个，各连 memory cell、memory bank、message、switch | `@ipt` 是否为 2/8/25/8；`weatherset`、`setrule`、`message` 等特权语句只有 world 能编译；链接名怎么读 | `ipt == 8`（logic）、world 程序能跑 |
| `memory-bench` | 3 个 micro + 2 个 memory cell：写入端、读取端、协调端 | 跨处理器 `read`/`write` 按名；未声明槽读 `null`；`wait`/轮询的时序 | `a == 7`、`b == null` |
| `factory-bench` | 铜/铅矿 + 钻头 + 传送带 + 石墨压机 + 硅冶炼厂 + 容器/仓库 + 卸载器 | 物品计数、`@totalItems`、生产 `progress`、满电与 `--power none` 断电 | `silicon >= 1`；断电后 progress 不涨 |
| `range-bench` | 敌方核心 + 三个靶（建筑或单位）在 0.9R、1.0R、1.1R（fortress R≈30 格） | 射程边缘：该开火时开火、超出不浪费、保持距离不冲过头 | `dist <= range + 1`、`chp` 下降 |

### P1：按逻辑主题补（有空再做）

| 场景 | 摆什么 | 验证什么 |
|---|---|---|
| `multi-core-bench` | 2 个敌方核心（12 格与 56 格）+ 1 个我方核心 | 选近的；毁掉一个后 `ulocate` 能否重选 |
| `team-bench` | sharded/crux/green 三队的核心、建筑、单位 | `@team` 判定、误伤、`ulocate ... enemy` 不锁友军 |
| `rules-bench` | 世界处理器 + 不同单位上限/核心血量/波次间隔 | `setrule` 的读回与效果（**刷怪器不跑**，只能测规则值） |
| `weather-bench` | 四种天气 + 世界处理器 | `weathersense`/`weatherset`、240 tick 淡出、`@rain` 等常量 |
| `building-bench` | 炮台（arc/scatter/cyclone）、雷达、开关、显示器、修理器 | `control shoot/configure/color`、`radar/uradar` 的过滤、`sensor` 建筑属性 |
| `terrain-bench` | 沙/石/水/矿/墙/悬崖各一片 | `getblock`/`setblock`/`lookup`/`ulocate`、`@mapw`/`@maph`、地形阻挡 |
| `path-bench` | 迷宫、窄口、水域、悬崖 | 地面单位 `pathfind` 与卡墙（B 档路径支持待验证） |
| `display-bench` | message、display、printflush，多个处理器 | 文本缓冲 400 字符上限、flush 到 message、跨处理器消息 |

### P2：边界与压力

| 场景 | 摆什么 | 验证什么 |
|---|---|---|
| `empty-bench` | 只有我方核心 + 一个处理器 | 纯时钟/数学/打印，`@tick` 起点与 `--ticks` 语义 |
| `error-bench` | 坏链接名、未定义变量、越界 `jump`、不存在的 content | 检查器与模拟器的报错路径，别静默跑错 |
| `scale-bench` | 30+ 处理器互联 + 大量内存格 | 链接上限、重名、性能、批量 trace |
| `edge-bench` | 地图四角、边界、纯水面 | 坐标 0 与 W-1、越界读写、单位落水 |

## 场景模板（每个场景都按这个来）

- 一张图一个 `.msav`，64×64 以内；文件名 `Mlog场景-<类别>-<名字>.msav`。
- **必须有我方核心**（`sharded`）：处理器自动落位靠它找空地；没有核心就用 `--base X,Y`。
- **不要摆处理器**：`mlogsim` 会自己放；手工摆的处理器不会被当成本次运行的入口。
- 需要目标的场景放一个敌方核心（`crux`）；只测单位就放 2–3 个不同单位并设 `flag`。
- 存档前先 `pause`，避免存档里带着半截生产进度；世界时钟加载时会被归零。
- 每个场景配一句说明（建议写进 `out/scenes/index.md`）：测什么、期望什么、用什么断言。
- 场景不需要完美：能复现一个逻辑分支就够。

## 模拟器边界（这些场景测不了，别白做）

- **电力图**：只支持 `--power full/none` 把消费者钉在满电/断电，不跑真实发电与电网平衡。
- **刷怪/波次**：不跑 `Logic` 的刷怪器与波次计时；`rules-bench` 只能测规则值。
- **地形寻路**：`pathfind` 依赖游戏的 pathfinder 网格，B 档是否可用还没验证；先按“可能不通”设计。
- **绘制/特效**：`draw`、`effect` 在 headless 下静默执行，没有画面可看。
- **payload/单位建造**：不模拟 payload 搬运与单位建造进度；相关方块只当静态建筑。
