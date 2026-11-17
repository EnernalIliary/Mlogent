# KB.md 补丁候选（来源：06-mlog 侦察 / task-14）

> 用法：把下面 3 条并入 KB.md 的「陷阱 Top10」。每条都带源码锚点，不要改写成无来源的结论短语。

1. **`wait` 的参数是秒，不是 tick** —— `LExecutor.java:1218-1232` 用 `curTime += Time.delta/60f` 累加真实秒；`wait 1` ≈ 60 tick ≈ 1 s，最小粒度 1 tick（要 1 tick 就写 `wait 0.0166`）。旧资料「wait 单位是 tick」是错的。
2. **`@time` 是毫秒，`@second` 才是秒** —— `GlobalVars.java:195` `varTime = tick/60*1000`；`@second = tick/60`、`@minute = tick/3600`、`@waveTime = wavetime/60`。把 `@time` 当秒用会差 1000 倍。
3. **`set @ipt` / `set @unit` 会被静默丢弃** —— 二者由 `LAssembler.java:25-30` 的 `putConst` 注册，SetI 写入既不生效也不报错；`@counter` 是 `putVar` 可以写。想改执行速度只能用 `setrate`（`LExecutor.java:2031` 做 clamp）。

## 同类候选（备选，未进 Top10）

- `setblock` 不能写 `building` 层：`TileLayer.settable = {floor, ore, block}`（`TileLayer.java:9`），源码注释 `//building case not allowed`（`LExecutor.java:1582`）。
- `uradar` 的第 5 个参数是死槽：`UnitRadarStatement` 固定 `radar="0"` 且不渲染该字段（`LStatements.java:1171-1186`），源码直接用 `@unit`。
- `strictEqual`（`===`）不是「恒 false」：`ConditionOp.java:12` 的 lambda 确实返回 false，但 `test()` 在 `:32-33` 特判为「类型位一致 + 精确相等」，jump（`LExecutor.java:1200`）走的是 test()。

## 全局口径提醒（不是陷阱，但 KB.md 应先声明）

mlog 里所有坐标类参数（`ucontrol x y`、`radar`、`ulocate` 输出、`query`、`getblock`）单位一律是 **tile（格）**，不是世界像素：源码统一用 `World.unconv`（×8，core/World.java:170-172）或 `numfWorld()`（LVar.java:69-72）转成世界坐标后再算。
