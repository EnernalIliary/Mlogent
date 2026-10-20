# 三个盲区合成台

现实场景（PVP / campaign / open / garded-line / maze）覆盖世界语义；这三张台子只补现实场景里不好摆的东西：跨处理器内存、四种处理器的 ipt/特权、单位属性矩阵。

```
python out/scenes/benches/build.py   # 生成两张 .msch
python out/scenes/benches/run.py     # 三张台子全跑，打印 PASS/FAIL
```

`run.py` 需要 `out/_server160.jar`（v160.7）和 `out/jre21/...`，与 `mlogsim` 默认一致。

## memory-bench.msch

布局（相对坐标，全部在 10 格链接范围内）：

| 方块 | 位置 | 代码要点 |
|---|---|---|
| writer (micro) | 0,0 | `write 7 cell1 0`、`write 8 cell1 1`、`set declared 42` |
| cell1 | 3,0 | — |
| reader (micro) | 6,0 | 读 cell1[0]、cell1[3]（未写）、cell2[0]、`writer1 "declared"` |
| coord (micro) | 9,0 | 读 cell1[1]、写 99 到 cell1[2]、再读回 |
| cell2 | 12,0 | — |

期望（12 tick）：

- `a=7`、`e=8`、`f=99`；
- **`b=0`、`c=0`**——未写过的记忆格槽读 **0**，不是 null（这和“未声明的变量读 null”是两回事）；
- `d=42`——`read d writer1 "declared"` 能读别的处理器里 `set` 出来的变量；
- `f=99`——同一轮里 `write` 后立刻 `read` 已能看到新值（写入立即生效）。

## processor-bench.msch

四个处理器并排（0/4/8/12），各自旁边 2 格一个 memory cell；hyper 的 2 格处还有一个 memory bank。

期望（14 tick）：

| 处理器 | @ipt | 附加 |
|---|---|---|
| micro | 2 | — |
| logic | 8 | — |
| hyper | 25 | `write @ipt bank1 63` → 读回 25（512 槽可用） |
| world | 8 | `setrule unitCap 77` 这一行被保留并生效 |

**链接范围**：`LogicBlock.range = 8 * 10` 世界单位 = **10 格**（`LogicBlock.java:49`）。超出范围的链接不会报错，直接在装载时变成 `null`；第一版台子把 cell 放到 14 格外，结果 read 出 null，就是这个原因。

## sensor-bench（无 .msch）

单位不能存进蓝图，所以由 `run.py` 直接 spawn 五个单位（flag 1..5），再用一段生成的 mlog 逐个 `ubind` + `sensor`，把每个读数和引擎里的值对比。

实测矩阵（v160.7，64×64 空白世界）：

| unit | flag | health | armor | shield | range | speed | controlled |
|---|---|---|---|---|---|---|---|
| dagger | 1 | 150 | 0 | 0 | 18.25 | 3.75 | 0 |
| flare | 2 | 70 | 0 | 0 | 9.5 | 20.25 | 0 |
| mono | 3 | 100 | 0 | 0 | 6.25 | 11.25 | 0 |
| mega | 4 | 460 | 3 | 0 | 22.25 | 18.75 | 0 |
| fortress | 5 | 900 | 9 | 0 | 29.5 | 3.225 | 0 |

- `range` 是 tile（`type.maxRange / 8`），`speed` 是 tile/秒（`type.speed * 60 / 8`）。
- 没有玩家、没有指挥命令、没有 `ucontrol` 时 `controlled` 一律 0；`ucontrol` 接管后才是 1。
- `sensor ... @type` 返回单位类型对象，不是字符串。

## 这张台子证不了什么

- 只验证“读到的值等于引擎里的值”，不验证引擎值本身对不对（那要真游戏）。
- sensor-bench 的单位是 `T.spawn` 出来的，不带出生点/核心归属；`@flag` 是脚本设的。
- memory-bench 的写入顺序依赖处理器在蓝图里的排列；换排列会改变同一 tick 内的先后，但 12 tick 后结果一致。
