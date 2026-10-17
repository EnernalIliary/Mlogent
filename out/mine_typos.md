# 手误排查 —— 我自己的蓝图库

扫描范围:`C:\Users\lliary\AppData\Roaming\Mindustry\schematics`(624 份,跳过 1 份 mlogv32 模拟器),2420 个逻辑块。

方法:对每个块,取"被读但全程序没被赋值"的名字,和"已赋值的名字"逐个算编辑距离;距离 1(长度 ≥6 时允许 2)就列出来。名字像链接(`message1`/`sorter1`)的另案处理,不算手误。

结果:**确认 10 处真手误**,另有 2 类是我的误报(已修)和 1 类待确认。

## A. 确认是手误

| 文件 | 位置 | 写错 | 应该是 | 后果 |
|---|---|---|---|---|
| `时间之锁.msch` | world-processor @(0,0) L95、L101 | `progoress.l1` | `progress.l1` | 多打一个 `o`,比较恒按 0 走 |
| `贴核5t3.msch` | micro-processor @(4,9) L180、L330、L480 …(7 处) | `unit3.distance` | 缺 `set unit3.distance 300` | 距离表只有 unit0/1/2(30/150/250),而 `unit.distance_max` 是 300;第四档永为 0 |
| `落地神风（路辅）.msch` | micro @(12,4) L134、L143 | `ucontrol idle ax ay` | `ucontrol idle fx fy` | 本块所有定位都走 `fx/fy`;`ax/ay` 从未赋值 ⇒ 单位被叫去 (0,0) |
| 同上 | logic @(13,0) L18、L24、L40 | `er` / `ax` / `ay` | `r` / `fx` / `fy` | `jump 19 notEqual er null` 恒假;`ucontrol within ax ay 1` 在 (0,0) 判定 |
| `落地神风单元2.0.msch` | 5 个 micro 块 L134、L143 | `ax ay` | `fx fy` | 同上,同一份逻辑的复制链 |
| `落地Poly神风V2.0_1.msch` | micro @(11,4)、@(12,4);logic @(13,0) | `ax ay` / `er` | `fx fy` / `r` | 同上 |
| `大型矿场.msch` | hyper @(5,5)、@(8,1)、@(8,5)、@(11,1) L22、L51 | 两个**长得一样的图标字形**当成两个变量 | 同一个变量 | `uradar` 写进其中一个,`ucontrol mine` 读另一个 ⇒ 挖的是 0 |
| `堆叠外水温冲.msch` | micro @(6,4) L3–L4 | `op add a b b` / `op div d 2 b` | `b` 应先赋值 | 整块 9 行、5 行引用不存在的名字 ⇒ 疑似损坏的残片 |
| `[#ffff00]水滴网0.9.3+公测版.msch` | micro @(1,0) L93、L159 | `equal type world-cell` | `equal type @world-cell` | 少了 `@` ⇒ 比的是变量 `world-cell`=0,永假 |
| `01大核'冲03RGT05蜂群02裂解01抽水.msch` | micro @(10,9) L71、L73 | `set d.h temp` | 先 `set temp d.h` | `temp` 从未赋值 ⇒ 半交换写反(紧邻 `set d.h d.w`) |

## B. 我的误报(已修)

| 现象 | 原因 | 修法 |
|---|---|---|
| `getblock block b ax+ ay` 里的 `b` 被当成未赋值 | `defs_of` 没有 `getblock` 分支,结果槽(索引 2)从不算写入 | 加语义表兜底:按 `defs` 的 arg-relative 下标取输出槽 |
| `spawn msl x y r t m` 里的 `m` 被当成未赋值 | 同上,`spawn` 结果槽在索引 5 | 同一处兜底覆盖 |

## C. 待确认

- `printflush you`(27 处)、`printflush log`(11 处):若这些 message 方块确实链接了,是我的链接名识别不全;若没链接,`printflush` 静默无效。
- `ILOS.test.msch` 的 `format hour` / `format min` / `format sec`:`format` 的语义我还没核到源码,先不下结论。
