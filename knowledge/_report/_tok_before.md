---
id: WORLD.BLOCKS.001
title: 方块模型与多格锚点
domain: world
status: active
ver: [v160.7_rt, v159.3_src]
conf: S
src:
  - "Mindustry-Source/core/src/mindustry/Vars.java:135"
  - "Mindustry-Source/core/src/mindustry/world/Block.java:112-160"
  - "Mindustry-Source/core/src/mindustry/world/Build.java:237-270"
  - "Mindustry-Source/core/src/mindustry/world/Tile.java:219-279"
  - "MBO/gamedata/v160.7/gamedata.json (jar 反射，447 blocks)"
data: [00-data/blocks.json]
depends: []
tags: [方块, 多格, 锚点, 放置, tileSize]
tokens: 1900
---

## 一句话

Mindustry 的地图是 8px 一格（tile）；方块用 `size` 表示占 n×n 格，放置时以**光标所在格为锚点**、按 `offset = -(size-1)/2`（整数除法）向四周展开——奇数尺寸居中于光标，**偶数尺寸偏左上**，且 n² 个格子共享同一个 `Building` 实体。

## 规则 / 公式

### 1. 格与像素

```
tilesize = 8                          // px / tile  [src: Vars.java:135]
tilePayload = tilesize * tilesize     // = 64 px², 载荷面积单位  [src: Vars.java:137]
blockPx = size * 8                    // 方块视觉/碰撞边长
bounds(x,y) = Rect(size*8) 中心 (x*8+offset, y*8+offset)   // [src: Block.java:1010-1012]
```

### 2. 多格锚点（最容易写错的一条）

```
offset = -(size - 1) / 2      // Java int 除法，向零取整  [src: Build.java:237-238, Tile.java:256]
覆盖格 = [x + offset, x + offset + size - 1] × 同 y
```

| size | offset | 相对光标的覆盖列 | 是否居中 | 像素边长 |
|---|---|---|---|---|
| 1 | 0 | x | 居中 | 8px |
| 2 | 0 | x … x+1 | **偏左上** | 16px |
| 3 | -1 | x-1 … x+1 | 居中 | 24px |
| 4 | -1 | x-1 … x+2 | 偏左上 | 32px |
| 5 | -2 | x-2 … x+2 | 居中 | 40px |
| 6 | -2 | x-2 … x+3 | 偏左上 | 48px |

偶数尺寸"偏左上"不是 bug：`-(size-1)` 对 size=2 得 -1，`-1/2` 在 Java 里是 `0`，所以光标格就是覆盖块的**第 0 行第 0 列**。编辑器里同样的逻辑见 `[src: MapEditor.java:228-231]`。

### 3. 一个 Building，n² 个代理格

```java
// Tile.java:254-279  放置多格方块时
if(block.isMultiblock()){
    int offset = -(block.size - 1) / 2;
    Building entity = this.build;
    for(int pass = 0; pass < 2; pass++){          // 两遍：先清场，再填充
        for(int dx = 0; dx < block.size; dx++)
          for(int dy = 0; dy < block.size; dy++){
            if(!(worldx == x && worldy == y)){
                if(pass == 0) other.setBlock(Blocks.air);   // 清场
                else { other.build = entity; other.block = block; }  // 代理
            }
        }
    }
}
```

- 被覆盖格子的 `tile.block` 也是该方块（渲染/占位一致），但 `tile.build` 指向**中心**那一个实体。
- `tile.centerX()/centerY()` 对被覆盖格返回中心格坐标 `[src: Tile.java:219-225]` —— 按格子遍历时想拿到"这个多格方块"，用 center 而不是 `tile.x`。
- `isMultiblock()` 只判断 `size > 1` `[src: Block.java:1014-1016]`。

### 4. 放置合法性（顺序即语义）

`validPlace` 依次检查 `[src: Build.java:183-270]`：

| 顺序 | 检查 | 不通过即失败 |
|---|---|---|
| 1 | `type.environmentBuildable()` / `isPlaceable()` | 禁止建造、环境不允许 |
| 2 | 核心保护（`polygonCoreProtection` 或敌方核心建造半径内） | 敌方核心附近不能造 |
| 3 | `type.canPlaceOn(tile, team, rotation)` | 地面不可放（深水除非 floating/placeableLiquid） |
| 4 | 战役黑暗 `world.getDarkness(x,y) >= 3` | 未探明区域不能造 |
| 5 | `requiresWater` / `placeableLiquid` / 浅水接触 | 需要水却没水 |
| 6 | 遍历 n×n 每格：深水、derelict、`interactable`、同块同朝向、`canReplace` | 任一格不合法 |
| 7 | `placeRangeCheck` 时查敌方重叠（`placeOverlapRange` 默认 50f） | 距离敌方建筑太近 |

### 5. 四个布尔字段的真实含义

| 字段 | 定义行 | 含义 | 不是 |
|---|---|---|---|
| `solid` | Block.java:112 | 单位/地面移动的碰撞体，单位绕行 | 不挡子弹 |
| `underBullets` | Block.java:118 | 子弹在此方块上绘制于其**下方**，可越过 | 不表示"打不到它" |
| `squareSprite` | Block.java:160 | 贴图是轴对齐正方形，旋转时只转方向不斜切 | 与命中判定无关 |
| `rotate` | Block.java:120 | 允许 4 向旋转（0..3，`Mathf.mod(rotation,4)`） | 不保证玩家能转（阵营/编辑器限制另算） |

## 数值

| id | size | 格数 | 像素边长 | health | 说明 |
|---|---|---|---|---|---|
| duo | 1 | 1 | 8px | 250 | 最小炮塔，可旋转 |
| graphite-press | 2 | 4 | 16px | 160 | 2×2 制造机，不可旋转 |
| laser-drill | 3 | 9 | 24px | 360 | 3×3 钻头，可采 4 级矿 |
| core-shard | 3 | 9 | 24px | 1100 | 3×3 核心，itemCapacity 4000 |
| core-nucleus | 5 | 25 | 40px | 6000 | 5×5 核心 |
| core-acropolis | 6 | 36 | 48px | 30000 | 6×6，最大核心 |
| interplanetary-accelerator | 7 | 49 | 56px | 3920 | 7×7 |
| tetrative-reconstructor | 9 | 81 | 72px | 5830 | 原版最大可放置方块之一 |

以上 health/size 取自 v160.7 jar 反射 `[src: jar:v160.7#blocks[name=…].size/health]`，即 `00-data/blocks.json#id=<name>` 的同源字段。

尺寸分布（447 个方块，含 `air`/`spawn`/`build1..build16` 等内部占位块）：

| size | 数量 | 占比 |
|---|---|---|
| 1 | 251 | 56.2% |
| 2 | 64 | 14.3% |
| 3 | 77 | 17.2% |
| 4 | 19 | 4.3% |
| 5 | 19 | 4.3% |
| ≥6 | 17 | 3.8% |

其它计数（同一次 jar 反射）：`rotate=true` 92 个、`solid=true` 257 个、`underBullets=true` 40 个、`squareSprite=false` 0 个（v160.7 全部方块都是方贴图）。

## 源码锚点

- `Vars.java:135` `public static final int tilesize = 8;` —— 全项目唯一的格宽真源。
- `Block.java:213-219` `size`/`offset`/`sizeOffset` 定义，注释明写 "changing size often leads to catastrophic issues"（运行期改 size 会炸存档）。
- `Block.java:1010-1012` `bounds()`：`Rect(size*8).setCenter(x*8+offset, y*8+offset)` —— 碰撞/命中框。
- `Build.java:237-242` 放置时的 `offsetx/offsety = -(size-1)/2` 与 n×n 遍历。
- `Build.java:248` 只对 **size==2** 在遍历中额外查黑暗：`type.size == 2 && getDarkness(...) >= 3`。
- `Tile.java:254-279` 多格"两遍法"：先 `setBlock(Blocks.air)` 清场，再赋 `build`/`block` 代理。

## 实测与反例

**反例 1（偶数尺寸不居中）**：想造 2×2 的石墨压机时，光标要放在目标 2×2 的**左上格**；放在"看起来的中心"会整体右移一格、下移一格。按 `Build.java:237` 的公式手算：size=2 → offset=0，覆盖 x..x+1。UI 上贴图从锚点向右下画，玩家常误判为居中。

**反例 2（放置会吞掉已有方块）**：`Tile.setBlock` 的第一遍直接 `other.setBlock(Blocks.air)` `[src: Tile.java:270-274]`，**不做 canReplace 检查**。玩家手动建造时被 `validPlace` 第 6 步拦住；但编辑器、载荷投放（`checkVisible=false`）走另一条路径，会静默销毁被压住的方块。判定"能不能压"要看 `Block.canReplace` / `replaceable`。

**边界（size=2 的黑暗检查）**：`Build.java:229` 只检查锚点格黑暗，`Build.java:248` 额外检查 size==2 的每一格。所以 3×3 方块只要中心亮就能造，2×2 必须 4 格全亮——这个不对称是源码既有行为，不是数据错误。

## 常见误解

1. **"size=2 的方块以鼠标为中心"** → 错。锚点永远是光标格，偶数尺寸偏左上（`offset=0`）；奇数尺寸才居中（size=3 → offset=-1）。
2. **"solid 就是挡子弹"** → 错。`solid` 管地面通行，挡子弹/激光靠 `underBullets`、`absorbLasers` 等另一组字段；传送带 `solid=false, underBullets=true` 就是典型。
3. **"打多格方块的边角格不掉血"** → 错。n² 格的 `build` 是同一个实体（`Tile.java:277`），打任意一格等于打整个方块。
4. **"`rotate=true` 就有 4 个贴图"** → 不一定。`rotateDraw=false` 时贴图不随方向转（`Block.java:122`），只有逻辑朝向变。
5. **"8px 是渲染精度"** → 8px 是**逻辑格**，与屏幕缩放无关；世界坐标 1 格 = 8 世界单位。

## 相关

- `WORLD.CRAFTING.001`（size 影响工厂布局与蓝图复制）
- `WORLD.LOGISTICS.001`（传送带 size=1、`underBullets` 的用途）
- `WORLD.PAYLOAD.001`（载荷方块用 `size` 算载荷面积）
- `WORLD.SANDBOX.001`（`placeablePlayer`/`inEditor` 决定编辑器可见性）
- 数据表：`00-data/blocks.json`（`size`/`health`/`solid`/`underBullets`/`rotate` 字段）
- 源码：`Mindustry-Source/core/src/mindustry/world/Block.java`、`world/Build.java`、`world/Tile.java`、`Vars.java`
