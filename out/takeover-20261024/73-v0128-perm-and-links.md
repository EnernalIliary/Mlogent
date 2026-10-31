# 73 — mai v0.12.8：冲突检测连链接表一起比 + 联机「无权限」提示

日期：2026-10-31
触发：用户 m02047「按你的顺序」——批准的顺序是 ①联机「无权限」提示 + ②冲突检测比链接表（合成一版）
→ ③快照补全 `blocks`/`items`/`liquids`/`units`/`enemies` → ④打包安装即用。

这一版只改模组（`MlogAuxiliary/scripts/main.js` + `mod.hjson` + `tests/mlogauxiliary/run_ui_smoke.py`），
sidecar 一行没动（仍是 0.12.6）。

## 73.1 冲突检测为什么必须连链接表一起比

v0.10.1 的写前冲突检测只比一件事：`String(b.code) === String(JOB_ORIG[k])`。作业是异步的——投递到
回来之间玩家有几十秒可以改那台处理器。代码变了会拦，但**链接表变了不拦**，而模型生成的代码里的链接名
是按**投递那一刻**的链接表写的。所以「代码没变」并不等于「这份代码现在还能用」：

- 玩家趁等的时候拆掉一条链接 ⇒ 代码里的 `iron` 变成未绑定，写进去满屏红箭头（`link-name-not-bound`）；
- 玩家把同名链接换到另一台方块上 ⇒ 代码照样能跑，但指向的东西换了，属于静默错语义。

两种情况都写进了一份「看起来成功」的程序，比覆盖掉代码更难查。修法（v0.12.8）：

- `linkSig(b)`：`linkListOrNull(b)` 每项拼成 `名字@x,y`，`parts.sort()` 之后空格 join；返回 `null` 表示
  「不知道这个处理器的链接表」（`linkListOrNull` 的 null 语义），**不知道就不判**，不制造假冲突。
- `rememberOrig(b)` 同时记 `JOB_ORIG[k]`（代码）与 `JOB_LINKS[k]`（签名）；`forgetOrig(b)` 三个表一起清。
- `conflictReason(b)` 两条都报：「处理器在你投递作业之后被改过（提交时 代码 3 行 → 5 行；链接表
  [iron@10,4] → [iron@10,4 copper@12,4]）」，两段都是可选的，只有一个变了就只报那一个。
- 绝对坐标进签名是有意的：同名链接从一台方块换到另一台，对生成的代码是另一个事实，必须算改动。

拒绝一次的语义不变（`conflictGate`：第一次拒、再点一次「写入」= 确认覆盖）。

## 73.2 联机里为什么必须自己判权限

计划书 §5（`docs/Mlog辅助-规划.md:254`）的规划口径是「写入走 `build.configure`，服务端执行，权限不足时
明确报『无权限』」，`docs/Mlog辅助-规划.md:293` 把它列为「还没做」。真源码取证（Mindustry-Source v160.x）：

- `core/src/mindustry/entities/comp/BuildingComp.java:388-392`：`configure(Object value)` 只是
  `block.lastConfig = value; Call.tileConfig(player, self(), value);`——联机里本地不执行写入。
- `core/src/mindustry/input/InputHandler.java:705-729`：`@Remote(... forward = true) tileConfig(...)`，
  服务端两道闸 `!Units.canInteract(player, build)` 与 `!netServer.admins.allowAction(player,
  ActionType.configure, build.tile, …)`。被拒时：远程玩家 `throw new ValidateException(player, "Player
  cannot configure a tile.")`；本地玩家**静默 return**，但两种情况下客户端那侧都被发了一个撤销包——
  源码注释原话：`// undo the config on the client`。
- `core/src/mindustry/entities/Units.java:134-136`：`canInteract(player, tile)` = `player == null ||
  tile == null || tile.interactable(player.team()) || state.rules.editor`；`Teams.java:125-127`：
  `canInteract(team, other) = team == other || other == Team.derelict`。
- `core/src/mindustry/world/blocks/logic/LogicBlock.java:325` / `:362-369`：`updateCode(new String(bytes,
  charset))` 把载荷文本**原样**存进 `code` ⇒ 可以拿 sidecar 返回的 `code` 直接跟 `b.code` 比。

结论：客户端拿不到任何错误信号，必须自己判。两层：

1. **写前拦**（`permWhy(b)`）：复刻第一道闸。单机（`Vars.net` 为 null）直接返回 null，一次多余的判断
   都没有；联机里 `b.interactable(player.team()) || state.rules.editor` 放行，否则返回「无权限：这块
   处理器属于 X，你在 Y；联机里服务端只接受本方队伍（或编辑器规则）的写入，这次一台都没写」。
   `writeBuild()` 里在「载荷有 bytes_b64」之后接一道；`writeMany()` 里进预检 `bad[]` ⇒ 整批一台都不写。
2. **写后回读**（`armWriteCheck()` / `writeCheckTick()`）：服务端拒绝不会报错，只能回读验证。写完
   `armWriteCheck(b, wantCode(res), null)`，`WRITE_CHECK_WAIT_MS = 1500` 后读一次 `String(b.code)`，
   用 `normCode()`（手写去尾部空白，不用带 `+` 量词的正则——真 Rhino 上那等价空匹配）比较；对不上就
   再等，`WRITE_CHECK_TRIES = 3` 次都对不上才 `hint()`：「无权限：… 的写入没生效（服务端没有接受）。
   联机里逻辑块由服务端执行，需要房主/管理员给权限，或改本方队伍的处理器」。方块被拆了
   （`w.b.tile.build !== w.b`）就销案，不误报。

## 73.3 改动清单

`MlogAuxiliary/scripts/main.js`（`MOD_VERSION` → `0.12.8`）：

| 新东西 | 作用 |
| --- | --- |
| `var JOB_LINKS = {}` | `"x,y" -> 投递作业那一刻的链接表签名` |
| `linkSig(b)` / `linkSigText(sig)` | 链接表 → 排序签名 / 签名 → 人读文本（空 = 「空」） |
| `netClient()` / `localPlayer()` / `isAdmin()` / `permWhy(b)` | 联机判定 + 队伍闸 |
| `WRITE_CHECK` / `WRITE_CHECK_WAIT_MS = 1500` / `WRITE_CHECK_TRIES = 3` | 写后回读队列与参数 |
| `normCode(s)` / `wantCode(res)` / `armWriteCheck(b, want, label)` / `writeCheckTick()` | 回读比对与提示 |
| `api.maiLinkConflictProbe` / `api.maiNetProbe` / `api.maiWriteCheckProbe` | 三个自检口 |

改的既有函数：`rememberOrig()`（记三张表）、`forgetOrig()`（清三张表）、`conflictReason()`（两条都报）、
`writeBuild()`（多一道 `permWhy` + 写完 `armWriteCheck`）、`writeMany()`（预检带 `permWhy` + 逐台
`armWriteCheck`）、update 钩子（`jobBoxTick();` 之后 `writeCheckTick();`）。

`MlogAuxiliary/mod.hjson`：`version: "0.12.8"` + description 追加一段（插在 `description: "` 行的最后一个
`"` 之前——文件末尾还有 `hidden: true` 等字段，不能按文末追加）。

`tests/mlogauxiliary/run_ui_smoke.py`：三个新探针 + 三条断言 + 八条 v0.12.8 源码红线；旧红线
`JOB_ORIG[procKey(b)] = String(b.code)` 改成 `JOB_ORIG[k] = String(b.code)`（`rememberOrig` 重构后原串
不存在了——这是本版唯一一次「红」，改的是测试里跟着代码走的那一条，不是放松判据）。

## 73.4 验证

```
node --check MlogAuxiliary/scripts/main.js            # 0
python -X utf8 tests/mlogauxiliary/run_ui_smoke.py    # EXIT=0
python gate.py                                        # 11/11
python gate.py --full --kb-build                      # 16/16 in 45.9s
```

ui smoke 的新行（真 v160.7 无头引擎）：

```
MAIDIAG:版本：0.12.8（游戏构建 160） …
MAICONFLICT:ok
MAILINKCONFLICT:ok
MAINET:net=false admin=false player=null perm=null
MAIWRITECHECK:offline queue=0
```

`maiLinkConflictProbe()` 的七件事：没动过不问 / 拆掉一条要拦 / 拒绝一次后放行 / 改回原样不问 /
同名换位置算改 / 代码与链接同时改时两条都报 / `forgetOrig()` 之后不问。

断言表新增 L2-58（冲突基线连链接表一起比）与 L2-59（联机被拒必须明确报「无权限」），现 **118 条**
（L1 31 / L2 59 / L3 6 / L4 4 / S 18）。计划书 §9 加了 v0.12.8 行，§5 的「还没做」两项都改成已完成。

## 73.5 没做 / 下一步

- **真联机没实测**：要开服（房主 + 一个非管理员玩家）才能验「服务端拒绝 → 回读三次 → 报无权限」。
  无头引擎 `Vars.net` 为 null，只验了单机分支不进闸。这条写进了断言表 L2-59 的判据列。
- 下一步是用户批准的顺序第 ③ 项：快照补全 `blocks` / `items` / `liquids` / `units` / `enemies`
  （`docs/Mlog辅助-规划.md:116-131` 的 schema v1 只填了五段）。
