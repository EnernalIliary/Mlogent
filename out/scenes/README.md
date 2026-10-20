# mlogsim 场景文件（v3：现实场景优先）

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

## 已有场景（现实场景优先）

| 文件 | 覆盖 | 场景里有什么 |
|---|---|---|
| `Mlog场景-进攻-open.msav` | 空旷对峙、远距离寻的、射程保持 | 64×64，双方各 1 核心 |
| `Mlog场景-进攻-garded-line.msav` | 防御线、炮台集火、进攻方生存 | 64×64，防守方炮台 + 单位 |
| `Mlog场景-进攻-maze.msav` | 墙/迷宫、卡墙、寻路失败 | 64×64，石墙隔断 |
| `Mlog场景-复杂-PVP.msav` | 双基地对称局：双方各 2 核心（nucleus + shard）、钻头/传送带/工厂、各 5 mono + 5 poly；蓝队 118 item-source + 62 scorch | 64×64，sharded/crux/blue |
| `Mlog场景-复杂-campaign.msav` | 战役生产基地：core-foundation、硅/塑钢/爆炸物/冷冻液/电力、8 mass-driver、4 air-factory、1 个 5534 字节 micro 处理器；mega/mono/poly 各 5 | 64×64，单队 sharded |

现实场景优先：它同时带地形、队伍、建筑状态和生产链，能测到合成台摆不出的“世界语义”。合成台只补现实场景不好摆的盲区。

**版本注意**：这两个复杂存档是 build 160 格式。v159.3 能读 PVP，读不了 campaign（`Error reading region map`）——`mlogsim` 默认已切到 v160.7，两个都能载；旧场景要回退就设 `MLOGSIM_JAR=out/_server159.jar`。

## 快照

```bash
# 需要带 Pillow 的 bundled python
& 'C:\Users\lliary\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe' out/scenes/_snapshot.py
```

每张存档渲染成 `out/scenes/snap_<name>.png`：一格 11 px，颜色按“核心=队伍色（字母 S/C/B）、红=防御、黄=物流、绿=逻辑、青=钻头/抽水、紫=生产、橙=电力、青绿=单位工厂、灰=墙”，底下有图例；圆点=单位（队伍色），网格线每 8 格。

`_block_hist.py <存档>` 打方块直方图（核对快照里的色块到底是什么）。快照只画方块和单位，不画地板细节以外的世界状态（电力、液体、工厂进度）。

## 还需要什么

### P0：四个盲区合成台（已建好）

`out/scenes/benches/`：`build.py` 重建两张 `.msch`，`run.py` 四台全跑（62 项断言，全绿）。

| 场景 | 摆什么 | 验证什么 | 实测结论 |
|---|---|---|---|
| `memory-bench` | 3 个 micro + 2 个 memory cell：写入端、读取端、协调端 | 跨处理器 `read`/`write` 按名；未写槽的读值；同轮写入可见性 | 跨处理器读 `set` 变量=42；**未写槽读 0（不是 null）**；write 后同轮 read=99 |
| `processor-bench` | micro、logic、hyper、world 各一个，各连 memory cell；hyper 另连 bank | `@ipt` 是否为 2/8/25/8；特权语句只有 world 能编译；链接名怎么读 | ipt 2/8/25/8；hyper 写 bank 槽 63=25；world 的 `setrule unitCap 77` 生效 |
| `sensor-bench` | 脚本 spawn 五个单位：dagger、flare、mono、mega、fortress，`flag` 设 1..5 | `sensor` 读数与引擎值是否一致；null 与 0 的区别 | 五项 health/armor/range/speed/flag 全对上；controlled 全 0；`@type` 返回类型对象 |
| `core-bench` | `--core-items silicon:400` 自动放核心并灌料；mono 取 15、放回 5 | `ulocate` 找核心、`itemTake`/`itemDrop` 距离与库存变化 | 385 / 15 / 10 / 390 全对上 |

链接范围只有 **10 格**（`LogicBlock.range = 8 * 10`），超出的链接装载时静默变 `null`——这是第一版台子 `cell1=null` 的原因。

### 现实场景已经覆盖的（不用另做）

| 需求 | 用哪个 |
|---|---|
| 多核心、毁核后重选 | PVP 双方各 2 核心，打掉一个即可 |
| 射程边界（0.9R/1.0R/1.1R） | PVP 双方核心相距约 60 格，fortress 从基地出发正好跨过 30 格射程 |
| 队伍/误伤判定 | PVP 的 sharded/crux/blue 三队 |
| 经济/工厂/电力 | campaign 的完整生产线（矿→冶炼→工厂→仓库） |
| 防御线/集火 | garded-line |
| 墙/卡墙/寻路 | maze + `control-bench` 里一条 `pathfind` 用例 |
| 显示/消息 | 在任一现实场景里摆一个 message 方块即可，不必单独建场景 |

### 现实场景还缺的（要补就按这个）

| 缺口 | 为什么现在测不了 | 怎么补 |
|---|---|---|
| 波次相关逻辑 | 现有存档全部 `rules.waves=false` | 一张 attack 模式、开了波次的 64×64 存档 |
| 天气自然循环 | 存档里没有激活的天气 | 用 `--weather rain` 强制；要测自然循环再做一张带天气的地图 |

### P2：边界与压力

| 场景 | 验证什么 |
|---|---|
| `error-bench` | 坏链接名、未定义变量、越界 `jump`、不存在 content 的报错路径 |
| `scale-bench` | 30+ 处理器互联：链接上限、重名、性能 |
| `edge-bench` | 地图四角/纯水面：坐标 0 与 W-1、越界读写、单位落水 |

## 场景模板（每个场景都按这个来）

- 一张图一个 `.msav`，64×64 以内；文件名 `Mlog场景-<类别>-<名字>.msav`。
- **必须有我方核心**（`sharded`）：处理器自动落位靠它找空地；没有核心就用 `--base X,Y`。
- **不要专门摆处理器**：`mlogsim` 会在核心旁另放一个作为入口；存档里原有的处理器不会被执行（跨处理器测试用 `memory-bench`）。
- 需要目标的场景放一个敌方核心（`crux`）；只测单位就放 2–3 个不同单位并设 `flag`。
- 存档前先 `pause`，避免存档里带着半截生产进度；世界时钟加载时会被归零。
- 每个场景配一句说明（建议写进 `out/scenes/index.md`）：测什么、期望什么、用什么断言。
- 场景不需要完美：能复现一个逻辑分支就够。

## 模拟器边界（这些场景测不了，别白做）

- **电力图**：只支持 `--power full/none` 把消费者钉在满电/断电，不跑真实发电与电网平衡。
- **刷怪/波次**：不跑 `Logic` 的刷怪器与波次计时；波次相关逻辑目前只能测规则值，不能测真的刷怪。
- **寻路**：不单独做场景。逻辑能做的只有 `ucontrol pathfind`，路径由引擎算；在 `control-bench` 里留一条“绕墙到目标点”的用例即可验证它接没接通。
- **绘制/特效**：`draw`、`effect` 在 headless 下静默执行，没有画面可看。
- **payload/单位建造**：不模拟 payload 搬运与单位建造进度；相关方块只当静态建筑。
