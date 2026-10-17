# 蓝图包错误清单(926 份)—— 按「是不是真错」分四层

包来源:`非mod+像素工厂蓝图【彩末整合】160+v-30`,由 colour ender(彩色末影)整合,
内容来自服务器/档案馆/残阳蓝图库 ⇒ 这**不是一个人**的作品,只能代表一批作者。
926 份里 481 份有逻辑,1698 个逻辑块,359,131 条语句。

| 层 | 含义 | 条数 |
|---|---|---:|
| **A 真错** | 名字被读的地方,值真的改变行为 | **78** |
| B 恒真守卫 | `jump` 两侧都是常量 ⇒ 分支固定,常是署名 | 55 |
| C 无效参数 | 名字落在指令读不到的参数位上 | 944 |
| D 死引用 | 形如链接名,但这块处理器没有这个链接 | 788 |
| E 署名 | 只为出现在变量列表里 | 5540 |

A 和 D 需要改;B/C/E 是这个社区的写作习惯,不是错误。
D 的危险在于它**看起来**是有效引用:`control shootp scatter1` 不会报错,
`LExecutor` 的 `validLink` 直接把它挡掉,塔一发不发。

## A 真错 —— 按变量

### 共 78 条 / 21 个名字

| 次数 | 变量 | 被哪种语句读 | 为什么是错 |
|---:|---|---|---|
| 42 | `max` | `jump`×30, `set`×12 | 想要无穷大/极值,实际拿到 0 |
| 7 | `unit3.distance` | `ucontrol`×7 | 控制/定位参数写成变量名 ⇒ 退化成默认值 |
| 4 | `x` | `write`×2, `set`×2 | 未赋值就被用 |
| 2 | `0:` | `set`×2 | 未赋值就被用 |
| 2 | `a` | `op`×2 | 算术里静默当 0 |
| 2 | `itemName` | `control`×2 | 指向不存在的方块 ⇒ 指令无效果 |
| 2 | `mmm` | `control`×2 | 指向不存在的方块 ⇒ 指令无效果 |
| 2 | `padNeedCount` | `op`×2 | 算术里静默当 0 |
| 2 | `point` | `op`×2 | 算术里静默当 0 |
| 2 | `y` | `set`×2 | 未赋值就被用 |
| 1 | `Carrot` | `control`×1 | 指向不存在的方块 ⇒ 指令无效果 |
| 1 | `O` | `op`×1 | 算术里静默当 0 |
| 1 | `b` | `op`×1 | 算术里静默当 0 |
| 1 | `bx` | `ucontrol`×1 | 控制/定位参数写成变量名 ⇒ 退化成默认值 |
| 1 | `by` | `ucontrol`×1 | 控制/定位参数写成变量名 ⇒ 退化成默认值 |
| 1 | `noop` | `noop`×1 | 未赋值就被用 |
| 1 | `scatter` | `radar`×1 | 未赋值就被用 |
| 1 | `selectedItem` | `set`×1 | 未赋值就被用 |
| 1 | `size` | `op`×1 | 算术里静默当 0 |
| 1 | `t` | `ucontrol`×1 | 控制/定位参数写成变量名 ⇒ 退化成默认值 |
| 1 | `ucontrol` | `ucontrol`×1 | 控制/定位参数写成变量名 ⇒ 退化成默认值 |

## A 真错 —— 按语句形态

| 次数 | 语句形态 | 运行时后果 |
|---:|---|---|
| 12 | `jump N lessThan i max` | 控制流:比较对象恒为 0/null ⇒ 分支恒真或恒假 |
| 12 | `set now max` | 值:赋进去的是 0/null |
| 7 | `ucontrol within upgrade[N].x upgrade[N].y unitN.distance upgrade[N].within N` | 目标:控制参数无效 |
| 6 | `jump N greaterThanEq now max` | 控制流:比较对象恒为 0/null ⇒ 分支恒真或恒假 |
| 6 | `jump N equal now max` | 控制流:比较对象恒为 0/null ⇒ 分支恒真或恒假 |
| 6 | `jump N greaterThanEq i max` | 控制流:比较对象恒为 0/null ⇒ 分支恒真或恒假 |
| 2 | `control config pad itemName N N N` | 目标:指向的方块名/参数不存在 ⇒ 指令无效果 |
| 2 | `op mod n n padNeedCount` | 算术:操作数静默当 0 |
| 2 | `control config unloaderN mmm N N N` | 目标:指向的方块名/参数不存在 ⇒ 指令无效果 |
| 2 | `set i N:` | 值:赋进去的是 0/null |
| 2 | `write x cellN N` | 目标:写不到 ⇒ 静默丢弃 |
| 2 | `ucontrol within bx by N aat N` | 目标:控制参数无效 |
| 2 | `op add nNeedUnit a b` | 算术:操作数静默当 0 |
| 1 | `set minItemName selectedItem` | 值:赋进去的是 0/null |
| 1 | `ucontrol move N N N N N` | 目标:控制参数无效 |
| 1 | `op equal M C O` | 算术:操作数静默当 0 |
| 1 | `op mod map.x point N` | 算术:操作数静默当 0 |
| 1 | `op idiv map.y point N` | 算术:操作数静默当 0 |
| 1 | `op add d dtc size` | 算术:操作数静默当 0 |
| 1 | `noop` | ? |

## B 恒真守卫 —— 按变量

### 比较两侧都是常量,分支恒真或恒假

| 次数 | 变量 | 被哪种语句读 | 判读 |
|---:|---|---|---|
| 16 | `colour` | `jump`×16 | 改写成 `always`,或那是署名 |
| 16 | `ender` | `jump`×16 | 改写成 `always`,或那是署名 |
| 6 | `padNeedCount` | `jump`×6 | 改写成 `always`,或那是署名 |
| 3 | `flase` | `ulocate`×3 | 改写成 `always`,或那是署名 |
| 3 | `resourceTB` | `jump`×3 | 改写成 `always`,或那是署名 |
| 3 | `x` | `jump`×3 | 改写成 `always`,或那是署名 |
| 1 | `coalx` | `jump`×1 | 改写成 `always`,或那是署名 |
| 1 | `euardamount` | `jump`×1 | 改写成 `always`,或那是署名 |
| 1 | `forceOff` | `jump`×1 | 改写成 `always`,或那是署名 |
| 1 | `out` | `jump`×1 | 改写成 `always`,或那是署名 |
| 1 | `selectedItem` | `jump`×1 | 改写成 `always`,或那是署名 |
| 1 | `t` | `jump`×1 | 改写成 `always`,或那是署名 |
| 1 | `upt` | `ucontrol`×1 | 改写成 `always`,或那是署名 |
| 1 | `y` | `jump`×1 | 改写成 `always`,或那是署名 |

## C 无效参数 —— 按变量

### 落在指令读不到的参数位上,运行时被忽略

| 次数 | 变量 | 被哪种语句读 | 判读 |
|---:|---|---|---|
| 528 | `op rand` | `op`×528 | 不用改 |
| 203 | `op floor` | `op`×203 | 不用改 |
| 48 | `op abs` | `op`×48 | 不用改 |
| 48 | `op ceil` | `op`×48 | 不用改 |
| 40 | `op sin` | `op`×40 | 不用改 |
| 32 | `op cos` | `op`×32 | 不用改 |
| 8 | `op sqrt` | `op`×8 | 不用改 |
| 7 | `storageY` | `ucontrol`×7 | 不用改 |
| 6 | `by` | `control`×5, `ucontrol`×1 | 不用改 |
| 5 | `bicker` | `control`×5 | 不用改 |
| 2 | `dd` | `ucontrol`×2 | 不用改 |
| 2 | `hy` | `ucontrol`×2 | 不用改 |
| 2 | `op log10` | `op`×2 | 不用改 |
| 2 | `s` | `control`×2 | 不用改 |
| 2 | `y` | `control`×2 | 不用改 |
| 2 | `矿y` | `ucontrol`×2 | 不用改 |
| 1 | `0sensor` | `control`×1 | 不用改 |
| 1 | `0​` | `control`×1 | 不用改 |
| 1 | `jj` | `ucontrol`×1 | 不用改 |
| 1 | `op atan` | `op`×1 | 不用改 |
| 1 | `op log` | `op`×1 | 不用改 |
| 1 | `range` | `ucontrol`×1 | 不用改 |
| 1 | `wi` | `ucontrol`×1 | 不用改 |

## D 死引用 —— 引用了不存在的链接

### 形如链接名,但这块处理器的链接表里没有它

| 次数 | 变量 | 被哪种语句读 | 判读 |
|---:|---|---|---|
| 140 | `unloader99` | `control`×140 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 43 | `message1` | `printflush`×43 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 42 | `switch1` | `sensor`×24, `control`×17, `op`×1 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 23 | `sorter1` | `control`×11, `sensor`×10, `jump`×2 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 21 | `projector1` | `control`×12, `jump`×4, `sensor`×3, `set`×1 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 20 | `unloader2` | `control`×20 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 16 | `yaddrx2` | `control`×8, `ucontrol`×8 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 12 | `unloader6` | `control`×12 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 11 | `unloader5` | `control`×11 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 10 | `malign1` | `sensor`×6, `control`×3, `radar`×1 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 9 | `message2` | `printflush`×9 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 9 | `scan3` | `set`×9 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 9 | `scan4` | `set`×9 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 9 | `scan5` | `set`×9 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 9 | `scan6` | `set`×9 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 8 | `unloader1` | `control`×8 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 7 | `arc1` | `control`×4, `sensor`×3 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 7 | `malign2` | `sensor`×4, `control`×3 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 7 | `malign3` | `sensor`×4, `control`×3 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 7 | `sorter2` | `control`×7 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 7 | `vault1` | `jump`×3, `set`×3, `control`×1 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 6 | `display2` | `drawflush`×6 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 6 | `display3` | `drawflush`×6 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 6 | `door1` | `control`×6 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 6 | `t3` | `sensor`×6 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 6 | `unloader11` | `control`×6 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 6 | `unloader3` | `control`×6 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 6 | `unloader9` | `control`×6 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 5 | `driver2` | `sensor`×4, `control`×1 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 5 | `reconstructor1` | `sensor`×4, `op`×1 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 5 | `unloader4` | `control`×5 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 4 | `block1` | `sensor`×4 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 4 | `router1` | `sensor`×2, `control`×2 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 4 | `sorter85` | `control`×4 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 4 | `unloader10` | `control`×4 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 3 | `conveyor1` | `set`×3 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 3 | `dome1` | `control`×2, `sensor`×1 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 3 | `driver1` | `sensor`×2, `control`×1 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 3 | `generator3` | `sensor`×2, `control`×1 | `control`/`printflush`/`sensor` 用到时静默无效 |
| 3 | `hail1` | `sensor`×2, `control`×1 | `control`/`printflush`/`sensor` 用到时静默无效 |

## E 署名 —— 出现最多的名字

### 只为在编辑器变量列表里留名

| 次数 | 变量 | 被哪种语句读 | 判读 |
|---:|---|---|---|
| 2325 | `?` | `jump`×2325 | 不用改 |
| 230 | `i` | `op`×112, `getlink`×37, `jump`×25, `write`×22 | 不用改 |
| 228 | `n` | `op`×112, `jump`×56, `read`×48, `getlink`×7 | 不用改 |
| 125 | `x` | `op`×46, `ucontrol`×42, `control`×16, `set`×10 | 不用改 |
| 105 | `y` | `op`×40, `ucontrol`×28, `control`×14, `jump`×14 | 不用改 |
| 60 | `cs` | `op`×40, `print`×20 | 不用改 |
| 56 | `t` | `op`×29, `jump`×22, `write`×4, `sensor`×1 | 不用改 |
| 55 | `s` | `control`×52, `jump`×3 | 不用改 |
| 55 | `use.item` | `control`×50, `set`×4, `jump`×1 | 不用改 |
| 34 | `by:NOSB(hghg` | `print`×34 | 不用改 |
| 31 | `try.item` | `set`×30, `jump`×1 | 不用改 |
| 30 | `a` | `op`×25, `lookup`×2, `jump`×1, `write`×1 | 不用改 |
| 30 | `li` | `jump`×24, `op`×6 | 不用改 |
| 29 | `hp` | `jump`×13, `op`×12, `print`×4 | 不用改 |
| 29 | `use.need` | `op`×25, `set`×4 | 不用改 |
| 28 | `m2` | `op`×16, `jump`×12 | 不用改 |
| 28 | `try.need` | `op`×14, `set`×14 | 不用改 |
| 27 | `chest` | `sensor`×21, `jump`×3, `ucontrol`×3 | 不用改 |
| 27 | `rc` | `set`×27 | 不用改 |
| 25 | `建筑` | `sensor`×20, `ucontrol`×5 | 不用改 |
| 24 | `time` | `op`×20, `jump`×3, `set`×1 | 不用改 |
| 22 | `charge` | `jump`×14, `op`×8 | 不用改 |
| 22 | `u1` | `ubind`×8, `jump`×7, `sensor`×7 | 不用改 |
| 21 | `animate_returnTo` | `set`×21 | 不用改 |
| 21 | `revolution` | `jump`×18, `op`×3 | 不用改 |
| 20 | `nx` | `op`×12, `jump`×6, `write`×2 | 不用改 |
| 19 | `dr` | `sensor`×8, `control`×6, `ucontrol`×3, `jump`×2 | 不用改 |
| 19 | `ii` | `control`×16, `read`×1, `write`×1, `op`×1 | 不用改 |
| 18 | `carryType` | `jump`×9, `ucontrol`×9 | 不用改 |
| 18 | `coal` | `op`×18 | 不用改 |
| 18 | `copper` | `jump`×9, `set`×9 | 不用改 |
| 18 | `mb` | `control`×18 | 不用改 |
| 18 | `silicon.unit` | `op`×18 | 不用改 |
| 18 | `try.itall` | `op`×18 | 不用改 |
| 17 | `Need` | `op`×17 | 不用改 |
| 17 | `tile` | `op`×12, `write`×4, `read`×1 | 不用改 |
| 16 | `coal.unit` | `op`×16 | 不用改 |
| 16 | `e-y` | `jump`×16 | 不用改 |
| 16 | `graphite.unit` | `op`×9, `jump`×7 | 不用改 |
| 16 | `item` | `set`×9, `ucontrol`×3, `control`×3, `jump`×1 | 不用改 |

## 附录:A 层逐条明细


### 2048.msch

| 行 | 块 | 语句 | 说明 |
|---:|---|---|---|
| 53 | hyper-processor @(5,2) | `set i 0:` | `0:` 未赋值 |
| 528 | hyper-processor @(5,2) | `set i 0:` | `0:` 未赋值 |

### fly bird高级版.msch

| 行 | 块 | 语句 | 说明 |
|---:|---|---|---|
| 33 | logic-processor @(3,0) | `write x cell1 0` | `x` 未赋值 |

### 分类器画在主视角显示器.msch

| 行 | 块 | 语句 | 说明 |
|---:|---|---|---|
| 15 | world-processor @(1,0) | `jump 26 greaterThanEq now max` | `max` 未赋值 |
| 24 | world-processor @(1,0) | `jump 16 lessThan i max` | `max` 未赋值 |
| 25 | world-processor @(1,0) | `set now max` | `max` 未赋值 |
| 27 | world-processor @(1,0) | `jump 33 equal now max` | `max` 未赋值 |
| 32 | world-processor @(1,0) | `jump 28 greaterThanEq i max` | `max` 未赋值 |
| 33 | world-processor @(1,0) | `set now max` | `max` 未赋值 |
| 45 | world-processor @(1,0) | `jump 34 lessThan i max` | `max` 未赋值 |
| 15 | world-processor @(2,0) | `jump 26 greaterThanEq now max` | `max` 未赋值 |
| 24 | world-processor @(2,0) | `jump 16 lessThan i max` | `max` 未赋值 |
| 25 | world-processor @(2,0) | `set now max` | `max` 未赋值 |
| 27 | world-processor @(2,0) | `jump 33 equal now max` | `max` 未赋值 |
| 32 | world-processor @(2,0) | `jump 28 greaterThanEq i max` | `max` 未赋值 |
| 33 | world-processor @(2,0) | `set now max` | `max` 未赋值 |
| 48 | world-processor @(2,0) | `jump 34 lessThan i max` | `max` 未赋值 |
| 15 | world-processor @(3,0) | `jump 26 greaterThanEq now max` | `max` 未赋值 |
| 24 | world-processor @(3,0) | `jump 16 lessThan i max` | `max` 未赋值 |
| 25 | world-processor @(3,0) | `set now max` | `max` 未赋值 |
| 27 | world-processor @(3,0) | `jump 33 equal now max` | `max` 未赋值 |
| 32 | world-processor @(3,0) | `jump 28 greaterThanEq i max` | `max` 未赋值 |
| 33 | world-processor @(3,0) | `set now max` | `max` 未赋值 |
| 48 | world-processor @(3,0) | `jump 34 lessThan i max` | `max` 未赋值 |

### 分类器画显示器.msch

| 行 | 块 | 语句 | 说明 |
|---:|---|---|---|
| 15 | world-processor @(1,0) | `jump 26 greaterThanEq now max` | `max` 未赋值 |
| 24 | world-processor @(1,0) | `jump 16 lessThan i max` | `max` 未赋值 |
| 25 | world-processor @(1,0) | `set now max` | `max` 未赋值 |
| 27 | world-processor @(1,0) | `jump 33 equal now max` | `max` 未赋值 |
| 32 | world-processor @(1,0) | `jump 28 greaterThanEq i max` | `max` 未赋值 |
| 33 | world-processor @(1,0) | `set now max` | `max` 未赋值 |
| 45 | world-processor @(1,0) | `jump 34 lessThan i max` | `max` 未赋值 |
| 15 | world-processor @(2,0) | `jump 26 greaterThanEq now max` | `max` 未赋值 |
| 24 | world-processor @(2,0) | `jump 16 lessThan i max` | `max` 未赋值 |
| 25 | world-processor @(2,0) | `set now max` | `max` 未赋值 |
| 27 | world-processor @(2,0) | `jump 33 equal now max` | `max` 未赋值 |
| 32 | world-processor @(2,0) | `jump 28 greaterThanEq i max` | `max` 未赋值 |
| 33 | world-processor @(2,0) | `set now max` | `max` 未赋值 |
| 48 | world-processor @(2,0) | `jump 34 lessThan i max` | `max` 未赋值 |
| 15 | world-processor @(3,0) | `jump 26 greaterThanEq now max` | `max` 未赋值 |
| 24 | world-processor @(3,0) | `jump 16 lessThan i max` | `max` 未赋值 |
| 25 | world-processor @(3,0) | `set now max` | `max` 未赋值 |
| 27 | world-processor @(3,0) | `jump 33 equal now max` | `max` 未赋值 |
| 32 | world-processor @(3,0) | `jump 28 greaterThanEq i max` | `max` 未赋值 |
| 33 | world-processor @(3,0) | `set now max` | `max` 未赋值 |
| 48 | world-processor @(3,0) | `jump 34 lessThan i max` | `max` 未赋值 |

### 堡垒自动进攻.msch

| 行 | 块 | 语句 | 说明 |
|---:|---|---|---|
| 40 | logic-processor @(0,0) | `op add d dtc size` | `size` 未赋值 |

### 小鸟飞飞打球.msch

| 行 | 块 | 语句 | 说明 |
|---:|---|---|---|
| 33 | logic-processor @(3,0) | `write x cell1 0` | `x` 未赋值 |

### 推箱子.msch

| 行 | 块 | 语句 | 说明 |
|---:|---|---|---|
| 208 | logic-processor @(0,1) | `op mod map.x point 8` | `point` 未赋值 |
| 209 | logic-processor @(0,1) | `op idiv map.y point 8` | `point` 未赋值 |

### 搬运8冰雹.msch

| 行 | 块 | 语句 | 说明 |
|---:|---|---|---|
| 15 | micro-processor @(2,2) | `radar enemy any any distance scatter 1 enemy` | `scatter` 未赋值 |

### 搬运T5 大超.msch

| 行 | 块 | 语句 | 说明 |
|---:|---|---|---|
| 299 | logic-processor @(16,22) | `op add nNeedUnit a b` | `a` 未赋值 |
| 299 | logic-processor @(16,22) | `op add nNeedUnit a b` | `b` 未赋值 |

### 搬运T5白爬 大超.msch

| 行 | 块 | 语句 | 说明 |
|---:|---|---|---|
| 1 | micro-processor @(11,1) | `op add result a b` | `a` 未赋值 |

### 核心11大硅.msch

| 行 | 块 | 语句 | 说明 |
|---:|---|---|---|
| 8 | micro-processor @(5,10) | `control config unloader1 mmm 0 0 0` | `mmm` 未赋值 |
| 13 | micro-processor @(5,10) | `control config unloader3 mmm 0 0 0` | `mmm` 未赋值 |

### 核心23接收 大超.msch

| 行 | 块 | 语句 | 说明 |
|---:|---|---|---|
| 2 | micro-processor @(10,14) | `control config pad itemName 0 0 0` | `itemName` 未赋值 |
| 5 | micro-processor @(10,14) | `op mod n n padNeedCount` | `padNeedCount` 未赋值 |
| 3 | micro-processor @(13,4) | `control config pad itemName 0 0 0` | `itemName` 未赋值 |
| 6 | micro-processor @(13,4) | `op mod n n padNeedCount` | `padNeedCount` 未赋值 |
| 31 | micro-processor @(3,8) | `set minItemName selectedItem` | `selectedItem` 未赋值 |

### 核心2路辅2空辅.msch

| 行 | 块 | 语句 | 说明 |
|---:|---|---|---|
| 15 | micro-processor @(3,9) | `set leadx x` | `x` 未赋值 |
| 16 | micro-processor @(3,9) | `set leady y` | `y` 未赋值 |
| 18 | micro-processor @(3,9) | `set copperx x` | `x` 未赋值 |
| 19 | micro-processor @(3,9) | `set coppery y` | `y` 未赋值 |

### 核心5T3.msch

| 行 | 块 | 语句 | 说明 |
|---:|---|---|---|
| 151 | micro-processor @(4,9) | `ucontrol within upgrade[1].x upgrade[1].y unit3.distance upgrade[1].within 0` | `unit3.distance` 未赋值 |
| 278 | micro-processor @(4,9) | `ucontrol within upgrade[2].x upgrade[2].y unit3.distance upgrade[2].within 0` | `unit3.distance` 未赋值 |
| 405 | micro-processor @(4,9) | `ucontrol within upgrade[3].x upgrade[3].y unit3.distance upgrade[3].within 0` | `unit3.distance` 未赋值 |
| 532 | micro-processor @(4,9) | `ucontrol within upgrade[4].x upgrade[4].y unit3.distance upgrade[4].within 0` | `unit3.distance` 未赋值 |
| 675 | micro-processor @(4,9) | `ucontrol within upgrade[5].x upgrade[5].y unit3.distance upgrade[5].within 0` | `unit3.distance` 未赋值 |
| 802 | micro-processor @(4,9) | `ucontrol within upgrade[6].x upgrade[6].y unit3.distance upgrade[6].within 0` | `unit3.distance` 未赋值 |
| 929 | micro-processor @(4,9) | `ucontrol within upgrade[7].x upgrade[7].y unit3.distance upgrade[7].within 0` | `unit3.distance` 未赋值 |

### 核心6碳化.msch

| 行 | 块 | 语句 | 说明 |
|---:|---|---|---|
| 1 | micro-processor @(4,0) | `control config Carrot 0914 0 0 0` | `Carrot` 未赋值 |

### 死星自动进攻.msch

| 行 | 块 | 语句 | 说明 |
|---:|---|---|---|
| 12 | hyper-processor @(1,1) | `ucontrol within bx by 60 aat 0` | `bx` 未赋值 |
| 12 | hyper-processor @(1,1) | `ucontrol within bx by 60 aat 0` | `by` 未赋值 |
| 17 | hyper-processor @(1,1) | `noop` | `noop` 未赋值 |

### 通用自动进攻寻路版 大.msch

| 行 | 块 | 语句 | 说明 |
|---:|---|---|---|
| 166 | hyper-processor @(1,2) | `ucontrol within x t ctrlr ctrlmod 0` | `t` 未赋值 |

### 逻辑 错误.msch

| 行 | 块 | 语句 | 说明 |
|---:|---|---|---|
| 11 | micro-processor @(7,0) | `ucontrol move 10 10 0 0 0` | `ucontrol` 未赋值 |

### 黑沙6大硅.msch

| 行 | 块 | 语句 | 说明 |
|---:|---|---|---|
| 14 | micro-processor @(7,10) | `op equal M C O` | `O` 未赋值 |
