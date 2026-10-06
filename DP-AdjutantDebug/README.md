# DP-副官调试样板（Adjutant Debug）

这是一个 **v159.3 的「补丁与资源」数据补丁**（不是普通 `mod.hjson` 模组），格式与你现有的
`DP-AtomicStatesAssets*.zip` 完全一致：压缩包根目录下就是 `content/`、`patches/`、`sprites/`。

## 1. 导入方法

1. 进游戏 → **地图编辑器** → 打开任意地图 → **地图信息**（MapInfoDialog）
2. 点 **「补丁与资源」**（`asset.title`）按钮
3. 点 **「导入资源压缩包」**（`asset.importzip`）→ 选 `DP-AdjutantDebug.zip`

导入后这些资源会**跟着这张地图/存档走**（所以叫"此地图所有资源"），换图要重新导入。
想导出给别人/备份，用同一个界面里的 **「导出资源压缩包」**。

## 2. 命名规则（最容易踩的坑）

数据补丁有一个**硬编码的前缀 `dp-`**（源码里 `DataImagePacker.regionPrefix = "dp-"`，
`DataPatcher` 里的虚拟模组名也写死为 `dp`）：

| 你的文件 | 游戏里的内容名 / 贴图名 |
|---|---|
| `content/blocks/test-wall.json` | `dp-test-wall` |
| `content/units/adjutant.json` | `dp-adjutant` |
| `sprites/test-wall.png` | 贴图 `dp-test-wall`（前缀由游戏自动加，**文件名不要写 dp-**） |

所以：

- **JSON 文件名 == PNG 文件名**（都写 `adjutant.png` / `adjutant.json`，别写 `dp-adjutant`）
- 内容之间互相引用时，要写**完整内容名**，即带 `dp-` 前缀（例：`"block": "dp-adjutant-factory"`）
- 贴图放在 `sprites/` 根目录下，**不要**放进 `sprites/generated/`（那是游戏自动生成图标的缓存目录）

## 3. 样板里有什么

| 内容名 | 文件 | 作用 |
|---|---|---|
| `dp-adjutant` | `content/units/adjutant.json` | 副官：飞行、20000 血、30 护甲、140 范围治疗场、150 格视野 |
| `dp-adjutant-factory` | `content/blocks/adjutant-factory.json` | 副官组装厂：免费+瞬间，放下去就出副官 |
| `dp-source-item` | `content/blocks/source-item.json` | 物品源：1000/秒，可切换任意物品 |
| `dp-source-power` | `content/blocks/source-power.json` | 电力源：100 万电力，自动连线 |
| `dp-test-wall` | `content/blocks/test-wall.json` | 测试墙：100 万血 / 1000 护甲 / 吸激光 |
| （补丁） | `patches/patch-example.json` | 补丁语法示例：把原版电力节点改成零成本秒建 |

贴图是脚本生成的**占位图**，直接用 .pixil 重画覆盖同名文件即可（尺寸：1 格方块 32×32，
3 格工厂 96×96，副官 48×48）。

## 4. 常用改法

**副官换行为**：`adjutant.json` 里

- `"type"` 可选（`unitType()`）：`flying` / `mech` / `legs` / `naval` / `tank` / `hover` /
  `payload` / `missile` / `tether` / `crawl`
- `"defaultController"` 换 AI：`FlyingAI`（默认）/ `GroundAI` / `RepairAI` / `MinerAI` /
  `BuilderAI` / `CommandAI` / `CargoAI` / `DefenderAI` …
- `"commands"` 可用指令只有这些：`move`、`repair`、`rebuild`、`assist`、`mine`、
  `enterPayload`、`loadUnits`、`loadBlocks`、`unloadPayload`、`loopPayload`
- `"abilities"` 里可加 `{"type":"ForceFieldAbility", "radius":60, "regen":20, "max":5000, "cooldown":300}`
  之类的能力（类名取 `mindustry.entities.abilities` 下的类）

**想要武器/炮台**：直接照抄你现有模组的 JSON 写法（`ContinuousTurret` + `shootType` 等），
新内容的 `type` 就写 Java 类名（`ClassMap` 解析），例如 `ItemTurret`、`PowerTurret`、
`GenericCrafter`、`Separator`、`Drill`、`Wall`、`Battery`、`ImpactReactor`。

**让副官能建造/采矿**：加 `"commands": ["rebuild"]` 或 `["mine"]`，飞行的辅助单位就会自己干活。

**补丁（patches/）**：结构是 `{"name": "说明", "<内容类型>": {"<原内容名>": {字段: 值}}}`，
原内容名**不带** `dp-`（那是原版名）。可以一次补多个：

```json
{
  "name": "让原版核心和容器变成纸糊的",
  "block": {
    "core-nucleus": {"health": 1, "armor": 0},
    "container": {"health": 1}
  }
}
```

字段名与 Java 里的字段一一对应，最常用的查询入口是
[Block.java](../Mindustry-Source/core/src/mindustry/world/Block.java)（就是本工作目录里克隆的
v159.3 源码：`Mindustry-Source/core/src/mindustry/world/Block.java`）。

## 5. 注意事项

- `adjutant-factory.json` 里的 `capacities` 是一串 0：这样工厂**不会**接受任何物品，
  避免 `capacities` 数组越界崩溃（物品 id 是动态的）。想让它吃物品造兵，就把
  `capacities` 对应物品 id 的位置改成容量，并在副官的 `requirements.requirements` 里写需求。
- 单位要能造出来必须 `"alwaysUnlocked": true`，否则工厂界面里是锁着的。
- 改完 JSON 后回到「补丁与资源」界面重新导入即可；同名资源要先删掉旧的（有"全部清除"按钮）。
