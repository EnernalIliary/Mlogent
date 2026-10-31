# 74 · v0.12.9：区域快照补全（库存 / 单位 / 敌方）

## 74.1 为什么这一刀

`docs/Mlog辅助-规划.md` 的 §3.2 从 v0.4.2 起就摆着一张 schema 表：`blocks`、`items`/`liquids`、
`units`、`enemies` 四段一直写着「规划」，实现只填了 `bounds`/`world`/`map`/`grid`/`processors`
五段（`docs/Mlog辅助-规划.md:130-131` 自己写着「未实现」）。

结果是模型看区域只有两样东西：格子（方块名）和处理器。它能数出「这片区域有 4 个容器」，
但容器里有没有铜、有没有水、旁边停着谁的单位、敌方建筑在哪，一概不知道。凡是补给、巡逻、
开火类的描述，模型只能猜，猜完还得玩家自己补一句「区域里有 100 铜」——而这本来是框选就能
自动带出去的事实。

这一刀就是把那张表补齐：**模组负责「区域里到底有什么」，sidecar 负责把它写成模型能读的世界事实。**

## 74.2 三个引擎事实（决定了实现形状）

1. **库存挂在建筑上，不挂在格子上。** `bld.items` 是 `ItemModule`、`bld.liquids` 是
   `LiquidModule`；没有库存能力的建筑（比如 `switch`）上这两个字段是 `null`。
2. **一个 2x2 方块在四个格子上是同一个建筑（同一个 `bld`）。** 所以 `grid`/`blocks` 按格计数
   （container 2x2 = 4 格）是对的，但库存/队伍必须**按建筑身份去重**（`String(bld.id)`），
   否则 100 铜会被数成 400。这条有断言钉着（`items.copper` 必须正好 100）。
3. **单位根本不在方块网格里。** 得走 `Groups.unit`，再按 `Math.floor(u.x / Vars.tilesize)` 把
   世界像素落成 tile 坐标去筛边界。

## 74.3 一个 Rhino 坑（本轮踩了两次，值得单独记）

`Groups.unit` 是 `mindustry.entities.EntityGroup`（`extends Seq<Unit>`），它在真实 v160.7 Rhino 里
和普通 `Seq` 表现不一样：

- `typeof Groups.unit.get === "undefined"` —— 真调用报 `Cannot find function get`（继承来的
  `Seq.get(int)` 被挡住了），而 `Groups.unit.each` / `Groups.unit.rawSeq()` 都在；
- `Groups.unit.size` 是个**函数**（`EntityGroup` 自己声明了 `size ()I`，把 `Seq` 的
  `public int size` 字段挡住），而普通 `Seq`（如 `Vars.content.items()`）的 `.size` 是数字。

两条一起踩的后果是 `for(i = 0; i < seq.size; i++){ seq.get(i) }` **一次都不循环**，单位数静默变 0
（ui smoke 就是这么暴露的：`v0.12.9: snapshot units: {"total": 0, "types": {}, "teams": {}}`）。

修法：`seqSize(seq)` 先当数字取 `seq.size`，不是数字再当函数调；`unitStats()` 先 `rawSeq()` 拿底层
Seq 按索引走，`get` 不是函数就退回 `each(fn)`。两条路都留着，因为哪条能用取决于引擎版本。

复现工具（本轮留下）：`out/takeover-20261024/tools/probe_entitygroup.py` 在真 v160.7 里逐条打印
`Groups.unit` 的 `size`/`get`/`each`/`rawSeq()` 与 `Vars.content.items().get`（每步单独 try/catch，
一个抛不会藏住其余）；`out/takeover-20261024/tools/clsfields.py` 直接从 jar 里读某个类的字段/方法表
（没有 javap 也能查「某个成员到底是字段还是方法」——这次就是靠它确认 `EntityGroup` 声明了 `size ()I`）。

## 74.4 改动清单

| 文件 | 改动 |
|---|---|
| `MlogAuxiliary/scripts/main.js` | `MOD_VERSION` 0.12.9；新增 `SNAP_MAX_STORES = 16` / `seqSize()` / `stockOf()` / `addInto()` / `countKeys()` / `stockText()` / `unitStats()`；`regionSnapshot()` 多出 `blocks` / `items` / `liquids` / `stores` / `units` / `enemies`（无本地玩家时 `enemies.note` 说明「enemy 没有意义，两个计数都是 0」）；`regionText()` 多一行「方块 N 种 物品 … 液体 … 单位 …（敌方单位 …，敌方建筑 …）」 |
| `tools/mlogprovider.py` | `snapshot_facts()` 重写：优先用模组给的 `blocks`（没有才从 `grid` 回退数），新增四行世界事实 `items stored in the area:` / `liquids stored in the area:` / `units in the area: N (dagger x2; teams: sharded 2)` / `enemies in the area: N unit(s) …, M enemy building(s)`；助手 `_num()`（`120.0` → `120`）/ `_top()`（按值降序、名字升序，稳定） |
| `tools/logicd.py` | `SIDECAR_VERSION` 0.12.6 → 0.12.9（这版 sidecar 有改动，得重启） |
| `MlogAuxiliary/mod.hjson` | `version` 0.12.9 + description 追加一段 |
| `tests/mlogauxiliary/run_ui_smoke.py` | `region_probe()` 往 2x2 容器塞 100 铜、往 `Groups.unit` 插一个 dagger；`MAISNAP` 新增六条断言（blocks / items 100 / stores 1 条且坐标对 / units.total+types / teams / enemies 0）；新增五条源码红线（`function stockOf(`、`function seqSize(`、`seenIds[bid] !== true`、`Packages.mindustry.gen.Groups.unit`、`typeof seq.rawSeq === "function"`、`function unitStats(`、`blocks: blocks, items: items, liquids: liquids, stores: stores`） |
| `tests/logicd/run_logicd_tests.py` | `test_provider()` 末尾加五条：`container x4`（模组计数优先于 grid 回退）、四行世界事实逐条比对 |
| `docs/断言表.md` | 新增 **L2-60**（快照补全：库存按建筑去重 / 单位走 `Groups.unit` / 敌方计数）与 **L2-61**（`EntityGroup` 挡住 `Seq.get`、`Groups.unit.size` 是方法）；总数 118 → **120 条**（L1 31 / L2 61 / L3 6 / L4 4 / S 18） |
| `docs/Mlog辅助-规划.md` | §3.2 的「未实现」改成实现口径；§9 加 v0.12.9 行 |
| `MlogAuxiliary/README.md` | 新增「v0.12.9：区域快照不只说有几台处理器，还说这里有什么」一节（含上面那个 Rhino 坑） |

## 74.5 验证

- `node --check MlogAuxiliary/scripts/main.js` → 0
- `python -X utf8 tests/mlogauxiliary/run_ui_smoke.py` → EXIT=0；`MAISNAP` 六条 v0.12.9 断言全过
- `python -X utf8 tests/logicd/run_logicd_tests.py` → protocol 26 / jobs 16 / provider 12 / llm 12 /
  write path 7，`logicd OK`
- `python -X utf8 gate.py` → 10/11（`kb` WARN：`tools/logicd.py` 比 `out/_kb/kb.sqlite3` 新，正常）
- `python -X utf8 gate.py --full --kb-build` → 见下

## 74.6 没做 / 待玩家验

- **真机未验**：本轮全部在无头 v160.7 里验的（无头没有本地玩家 ⇒ `enemies` 恒 0 的分支被覆盖，
  有玩家时的敌方分支只能靠代码审）。玩家重启游戏 + sidecar 后，框一片有容器和单位的区域，
  看面板那行摘要和模型的世界事实即可。
- **stores 上限 16**：超过 16 台有库存的建筑只记前 16 条（总量 `items`/`liquids` 仍然是全的）。
- **没有做** `units` 的血量 / 朝向 / 是否在攻击这些更细的字段——规划里没要求，模型目前也用不上。
