# 逐条审计（97 条，8 条规则）

判法：每条末尾有 `判定:` 一行，在后面填一个词 ——
`ok`（规则说得对）、`bad`（规则说错了）、`unsure`（看不出来）、`skip`（不想看）。
`备注:` 后面可以写一句原因，会被记进那条规则的历史。

填完在仓库根目录跑 `python tools/review.py ingest`，判定会写进 `out/verdicts.csv`，
`python tools/review.py stats` 就按规则算准确率。

**行号是语句序号（0 起）**，和代码里 `jump N` 用的是同一个数；`>>>>` 标的是被指的那一条。
处理器自己的链接名单独列出，所以「名字指错了」这类判定不需要打开地图。

## 目录

| 规则 | 条数 | 已判 |
|---|---|---|
| `version-gate` | 24 | 0 |
| `undefined-var-is-not-automatically-an-error` | 23 | 0 |
| `link-name-not-bound` | 13 | 0 |
| `dead-polarity` | 11 | 0 |
| `status-name-needs-at` | 11 | 0 |
| `jump-to-jump-chain` | 10 | 0 |
| `constant-null-guard` | 4 | 0 |
| `printflush-clears-buffer` | 1 | 0 |

## 规则 `version-gate`

### `d6e13ae7a3`

- 出处：`mindustrytop-25774` · (125,137) · logic-processor · 141 条语句
- 处理器自己的链接：`message1`, `pad1`, `pad2`, `pad3`, `pad4`, `pad5`, `pad6`, `pad7`, `pad8`, `pad9`, `pad10`, `pad11`, `pad12`, `pad13`, `pad14`, `pad15`
- 被指行：语句序号 **78**
- 规则说：version gate: uses format -- needs build >= 147; on anything older the line is replaced by noop and silently does nothing

```
      ... 上面还有 48 条语句
      48  set sum 0
      49  lookup item item item.i
      50  sensor item.name item @name
      51  read weight @this item.name
      52  lookup block UsedAscell item.i
      53  sensor UsedAscell UsedAscell @name
      54  read item.amount @this UsedAscell
      55  op sub item.reverse.amount item.max item.amount
      56  op mul item.reverse.amount item.reverse.amount weight
      57  op pow item.reverse.amount item.reverse.amount @e
      58  write item.reverse.amount @this UsedAscell
      59  op add sum sum item.reverse.amount
      60  op add item.i item.i 1
      61  jump 49 lessThan item.i 20
      62  jump 68 notEqual sum.last sum
      63  op sub timer.coreflash timer.coreflash.set 60000
      64  jump 70 greaterThan timer.coreflash.set timer.coreflash
      65  set core null
      66  set timer.coreflash.set @time
      67  end
      68  set timer.coreflash.set @time
      69  set sum.last sum
      70  op sub n.pad @links 1
      71  op sqrt endl.set n.pad 1
      72  op idiv endl.set endl.set 1
      73  jump 138 strictEqual n.pad 0
      74  op div pad.volum sum @links
      75  op mul total.transportation 20 n.pad
      76  op rand pad.instruct pad.volum n.pad
      77  print "\n*{1}总运力~={0}/s\n\n"
>>>>  78  format total.transportation
      79  format n.pad
      80  jump 85 greaterThanEq pad.volum 50
      81  print "\n[orange]资源基本平衡、着陆板待机中"
      82  print "\n\n[#fdcbe6]「如果能调和一切，那结果会是空心吗？」[white]\n"
      83  set pad.volum 0
      84  set pad.instruct 50
      85  set item.i 0
      86  set pad.filled 0
      87  set i.pad 1
      88  set cfgitem null
      89  lookup item item item.i
      90  jump 92 lessThanEq i.pad n.pad
      91  jump 139 always 0 false
      92  lookup block UsedAscell item.i
      93  sensor UsedAscell UsedAscell @name
      94  read item.reverse.amount @this UsedAscell
      95  sensor item.name item @name
      96  read weight @this item.name
      97  op add pad.filled pad.filled item.reverse.amount
      98  jump 101 notEqual cfgitem null
      99  jump 101 lessThan pad.filled pad.instruct
     100  set cfgitem item
     101  jump 124 lessThan pad.filled pad.volum
     102  getlink pad i.pad
     103  jump 139 greaterThan i.pad n.pad
     104  control config pad cfgitem 0 0 0
     105  jump 109 notEqual display.mode 0
     106  jump 113 equal cfgitem.last cfgitem
     107  set cfgitem.last cfgitem
     108  jump 112 always 0 false
      ... 下面还有 32 条语句
```

判定:
备注:

### `0a6d62c6bc`

- 出处：`mindustrytop-25774` · (413,408) · micro-processor · 6 条语句
- 处理器自己的链接：`container1`, `conveyor1`
- 被指行：语句序号 **3**
- 规则说：version gate: uses select -- needs build >= 150; on anything older the line is replaced by noop and silently does nothing

```
       0  getlink building.container 0
       1  getlink building.conveyor 1
       2  sensor item.surge-alloy building.container @surge-alloy
>>>>   3  select control.conveyor greaterThan item.surge-alloy 250 true false
       4  control enabled building.conveyor control.conveyor 0 0 0
       5  end
```

判定:
备注:

### `93dd190600`

- 出处：`mindustrytop-25774` · (3,489) · world-processor · 2 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **0**
- 规则说：version gate: uses bullet -- needs build >= 157; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  bullet result @salvo 0 @thisx @thisy 315 @sharded @this 500 5 1 -1 -1
       1  wait 0.5
```

判定:
备注:

### `a6f857d50a`

- 出处：`mindustrytop-26075` · (5,10) · world-processor · 28 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **6**
- 规则说：version gate: uses format -- needs build >= 147; on anything older the line is replaced by noop and silently does nothing

```
       0  getflag 运行 "阶段4"
       1  jump 0 equal 运行 false
       2  set 开始波次 90
       3  set 总波次 90
       4  print "[red]阶段 4\n[white]波次:{0}/{1}"
       5  op sub 当前波次 @waveNumber 开始波次
>>>>   6  format 当前波次
       7  format 总波次
       8  op add 结束波次 开始波次 总波次
       9  jump 15 greaterThanEq @waveNumber 结束波次
      10  print "\n剩余时间:{0}秒"
      11  op round 剩余时间 @waveTime 1
      12  format 剩余时间
      13  message mission 3 @wait
      14  end
      15  message mission 3 @wait
      16  fetch unitCount 敌人数量 2 0 null
      17  setrule currentWaveTime 99999999 0 0 100 100
      18  jump 27 greaterThan 敌人数量 0
      19  setrule currentWaveTime 600 0 0 100 100
      20  setblock ore @air 100 500 @derelict 0
      21  setblock ore @spawn 60 950 @derelict 0
      22  setblock ore @spawn 140 950 @derelict 0
      23  setrule mapArea 99999999 0 0 200 1000
      24  setrule dropZoneRadius 75 0 0 200 1000
      25  setflag "阶段4" false
      26  setflag "阶段5" true
      27  end
```

判定:
备注:

### `9ab3d99b5d`

- 出处：`mindustrytop-26075` · (5,11) · world-processor · 30 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **6**
- 规则说：version gate: uses format -- needs build >= 147; on anything older the line is replaced by noop and silently does nothing

```
       0  getflag 运行 "阶段3"
       1  jump 0 equal 运行 false
       2  set 开始波次 35
       3  set 总波次 55
       4  print "[orange]阶段 3\n[white]波次:{0}/{1}"
       5  op sub 当前波次 @waveNumber 开始波次
>>>>   6  format 当前波次
       7  format 总波次
       8  op add 结束波次 开始波次 总波次
       9  jump 15 greaterThanEq @waveNumber 结束波次
      10  print "\n剩余时间:{0}秒"
      11  op round 剩余时间 @waveTime 1
      12  format 剩余时间
      13  message mission 3 @wait
      14  end
      15  message mission 3 @wait
      16  fetch unitCount 敌人数量 2 0 null
      17  fetch unit boss 2 0 @reign
      18  status false @dp-超速+75 boss 1e10
      19  status false @status-shielded boss 1e10
      20  status false @dp-治愈 boss 1e10
      21  setrule currentWaveTime 99999999 0 0 100 100
      22  jump 29 greaterThan 敌人数量 0
      23  setrule currentWaveTime 300 0 0 100 100
      24  setblock ore @air 100 350 @derelict 0
      25  setblock ore @spawn 100 500 @derelict 0
      26  setrule mapArea 99999999 0 0 200 400
      27  setflag "阶段3" false
      28  setflag "阶段4" true
      29  end
```

判定:
备注:

### `ecd5b01aec`

- 出处：`mindustrytop-26075` · (5,12) · world-processor · 26 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **6**
- 规则说：version gate: uses format -- needs build >= 147; on anything older the line is replaced by noop and silently does nothing

```
       0  getflag 运行 "阶段2"
       1  jump 0 equal 运行 false
       2  set 开始波次 10
       3  set 总波次 25
       4  print "[yellow]阶段 2\n[white]波次:{0}/{1}"
       5  op sub 当前波次 @waveNumber 开始波次
>>>>   6  format 当前波次
       7  format 总波次
       8  op add 结束波次 开始波次 总波次
       9  jump 15 greaterThanEq @waveNumber 结束波次
      10  print "\n剩余时间:{0}秒"
      11  op round 剩余时间 @waveTime 1
      12  format 剩余时间
      13  message mission 3 @wait
      14  end
      15  message mission 3 @wait
      16  fetch unitCount 敌人数量 2 0 null
      17  setrule currentWaveTime 99999999 0 0 100 100
      18  jump 25 greaterThan 敌人数量 0
      19  setrule currentWaveTime 300 0 0 100 100
      20  setblock ore @air 100 200 @derelict 0
      21  setblock ore @spawn 100 350 @derelict 0
      22  setrule mapArea 99999999 0 0 200 275
      23  setflag "阶段2" false
      24  setflag "阶段3" true
      25  end
```

判定:
备注:

### `55bf0112e2`

- 出处：`mindustrytop-26078` · (398,403) · world-processor · 49 条语句
- 处理器自己的链接：`node1`, `node2`
- 被指行：语句序号 **39**
- 规则说：version gate: uses select -- needs build >= 150; on anything older the line is replaced by noop and silently does nothing

```
       0  sensor 电力1 node1 @powerNetStored
       1  sensor 电力2 node2 @powerNetStored
       2  op idiv 电力1. 电力1 1
       3  set f1 " "
       4  jump 7 lessThanEq 电力1 100000
       5  op idiv 电力1. 电力1 1000
       6  set f1 "k"
       7  jump 15 lessThanEq 电力1 10000000
       8  op idiv 电力1. 电力1 1000000
       9  op mod 电力1.. 电力1 1000000
      10  op div 电力1.. 电力1.. 1000000
      11  op idiv 电力1.. 电力1.. 0.1
      12  op mul 电力1.. 电力1.. 0.1
      13  op add 电力1. 电力1. 电力1..
      14  set f1 "M"
      15  op idiv 电力2. 电力2 1
      16  set f2 " "
      17  jump 20 lessThanEq 电力2 100000
      18  op idiv 电力2. 电力2 1000
      19  set f2 "k"
      20  jump 28 lessThanEq 电力2 10000000
      21  op idiv 电力2. 电力2 1000000
      22  op mod 电力2.. 电力2 1000000
      23  op div 电力2.. 电力2.. 1000000
      24  op idiv 电力2.. 电力2.. 0.1
      25  op mul 电力2.. 电力2.. 0.1
      26  op add 电力2. 电力2. 电力2..
      27  set f2 "M"
      28  print "[orange]电力大比拼[white]\n电力先到1000M的队伍获胜\n"
      29  print "[yellow]黄[white]当前储存电力:\n"
      30  print 电力1.
      31  print f1
      32  print "\n[red]红[white]当前储存电力:\n"
      33  print 电力2.
      34  print f2
      35  message mission 3 @wait
      36  jump 39 greaterThanEq 电力1 1000000000
      37  jump 39 greaterThanEq 电力2 1000000000
      38  end
>>>>  39  select sss greaterThanEq 电力1 1000000000 2 1
      40  select sss. greaterThanEq 电力1 1000000000 "黄队电力储存大于1000M黄队获胜" "红队电力储存大于1000M红队获胜"
      41  fetch core kkk sss 0 @conveyor
      42  setprop @health kkk 0
      43  jump 0 equal e 1
      44  print sss.
      45  message announce 10 @wait
      46  print sss.
      47  message notify 10 @wait
      48  set e 1
```

判定:
备注:

### `078052e1e1`

- 出处：`mindustrytop-26053` · (56,4) · world-processor · 6 条语句
- 处理器自己的链接：`nucleus1`
- 被指行：语句序号 **3**
- 规则说：version gate: uses select -- needs build >= 150; on anything older the line is replaced by noop and silently does nothing

```
       0  getlink a 0
       1  lookup item b i
       2  op add i i 1
>>>>   3  select i strictEqual b null 0 i
       4  jump 1 equal b @surge-alloy
       5  setprop b a 0
```

判定:
备注:

### `55ae9e4695`

- 出处：`mindustrytop-26053` · (65,7) · world-processor · 12 条语句
- 处理器自己的链接：`nucleus1`, `nucleus2`
- 被指行：语句序号 **6**
- 规则说：version gate: uses select -- needs build >= 150; on anything older the line is replaced by noop and silently does nothing

```
       0  getlink a 0
       1  getlink b 1
       2  jump 5 equal a null
       3  jump 5 equal b null
       4  end
       5  print "两队之中有一个核心爆了\n因为地图设置的是生存模式，所以我好像不得不把另一个核心也炸了否则游戏是无法结束的。\n反正"
>>>>   6  select c notEqual a null "[red]红" "[yellow]黄"
       7  print c
       8  print "[white]队赢了"
       9  message announce 10 @wait
      10  wait 10
      11  explosion 3 0 0 100 9999999 0 true 1 true
```

判定:
备注:

### `55dc059ab1`

- 出处：`mindustrytop-26053` · (62,17) · world-processor · 13 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **6**
- 规则说：version gate: uses select -- needs build >= 150; on anything older the line is replaced by noop and silently does nothing

```
       0  setrate 1000
       1  fetch unit a 3 i b
       2  op add i i 1
       3  setprop @status-spore-slowed a 1000
       4  ubind a
       5  sensor x a @x
>>>>   6  select x. greaterThan x 65 123 6
       7  ucontrol pathfind x. 51 0 0 0
       8  jump 1 notEqual a null
       9  lookup unit b ii
      10  op add ii ii 1
      11  select ii strictEqual b null 0 ii
      12  set i 0
```

判定:
备注:

### `2d7af77217`

- 出处：`mindustrytop-24936` · (5,22) · world-processor · 44 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **36**
- 规则说：version gate: uses bullet -- needs build >= 157; on anything older the line is replaced by noop and silently does nothing

```
       0  fetch unitCount BOSS 2 0 @oxynoe
       1  jump 0 lessThan BOSS 1
       2  fetch unit BOSS 2 0 @oxynoe
       3  getflag 难1 "普通"
       4  getflag 难2 "困难"
       5  jump 9 equal 难1 1
       6  jump 11 equal 难2 1
       7  set 难度 0
       8  jump 12 always x false
       9  set 难度 1
      10  jump 12 always x false
      11  set 难度 2
      12  set A 0
      13  fetch unit 信标 2 A @mono
      14  op add A A 1
      15  sensor F 信标 @flag
      16  jump 19 equal F 224
      17  jump 13 notEqual 信标 false
      18  end
      19  set 重复 0
      20  setrate 7
      21  sensor X 信标 @x
      22  sensor Y 信标 @y
      23  set 次数 0
      24  op add 次数 次数 1
      25  op mul 大小 次数 4
      26  op sub 反大小 600 大小
      27  effect wave X Y 反大小 %8aff93
      28  jump 24 lessThanEq 次数 150
      29  wait 0.3
      30  setrate 300
      31  op mul 伤害倍率 难度 20
      32  op add 伤害 伤害倍率 40
      33  set 角度 0
      34  op add 角度 角度 10.33
      35  op add 发射 发射 1
>>>>  36  bullet 子弹 @renale 16 X Y 角度 2 null 伤害 0.8 2 -1 -1
      37  jump 34 lessThanEq 发射 360
      38  set 发射 0
      39  op add 重复 重复 1
      40  jump 33 lessThanEq 重复 2
      41  set 重复 0
      42  setprop @health 信标 0
      43  wait 1
```

判定:
备注:

### `2fa9c7c5ac`

- 出处：`mindustrytop-24936` · (1,23) · world-processor · 45 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **41**
- 规则说：version gate: uses bullet -- needs build >= 157; on anything older the line is replaced by noop and silently does nothing

```
       0  fetch unitCount BOSS 2 0 @avert
       1  jump 0 lessThan BOSS 1
       2  setrate 25
       3  getflag 难1 "普通"
       4  getflag 难2 "困难"
       5  jump 9 equal 难1 1
       6  jump 11 equal 难2 1
       7  set 难度 0
       8  jump 12 always x false
       9  set 难度 1
      10  jump 12 always x false
      11  set 难度 2
      12  set A 0
      13  fetch unit 信标 2 A @mono
      14  op add A A 1
      15  sensor F 信标 @flag
      16  jump 19 equal F 210
      17  jump 13 notEqual 信标 false
      18  end
      19  set 次数 0
      20  sensor X 信标 @x
      21  sensor Y 信标 @y
      22  op add Y1 Y 9
      23  op sub Y2 Y 9
      24  op mul 倍率 次数 2.4
      25  op sub 发射X X 倍率
      26  op add 次数 次数 1
      27  effect warn 发射X Y 2 %ffaaff
      28  effect warn 发射X Y1 2 %ffaaff
      29  effect warn 发射X Y2 2 %ffaaff
      30  jump 24 lessThanEq 次数 75
      31  wait 1
      32  op mul 伤害倍率 难度 8
      33  op add 伤害 伤害倍率 18
      34  op mul 难度数量 难度 25
      35  op add 最大数量 难度数量 150
      36  set 次数 0
      37  op sub 低Y Y 9
      38  op rand 随机 18 7.5
      39  op add 发Y 低Y 随机
      40  op add 次数 次数 1
>>>>  41  bullet 子弹 @renale 14 X 发Y 180 2 null 伤害 1 1.5 -1 -1
      42  jump 38 lessThanEq 次数 最大数量
      43  setprop @health 信标 0
      44  wait 0.5
```

判定:
备注:

### `fbcb864b41`

- 出处：`mindustrytop-24936` · (5,23) · world-processor · 77 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **71**
- 规则说：version gate: uses bullet -- needs build >= 157; on anything older the line is replaced by noop and silently does nothing

```
      ... 上面还有 41 条语句
      41  sensor X @unit @x
      42  sensor Y @unit @y
      43  sensor BX BOSS @x
      44  sensor BY BOSS @y
      45  uradar enemy any any distance 0 1 敌人
      46  sensor DX 敌人 @x
      47  sensor DY 敌人 @y
      48  setprop @x 信标 DX
      49  setprop @y 信标 DY
      50  op sub 差X BX X
      51  op sub 差Y BY Y
      52  op div 比例 差X 差Y
      53  op atan 角度 比例 差X
      54  jump 57 greaterThan 差Y 0
      55  op sub 角度 90 角度
      56  jump 58 always 差Y 0
      57  op sub 角度 270 角度
      58  jump 24 lessThanEq 大小 280
      59  op sub 小角 角度 6
      60  op add 大角 角度 6
      61  setmarker arc 10001 小角 大角 0
      62  op mul 伤害倍率 难度 20
      63  op add 伤害 伤害倍率 30
      64  op rand 随机角度 6 18
      65  op rand 随机正负 3 18
      66  op floor 随机正负 随机正负 18
      67  op sub 随机正负 随机正负 1
      68  jump 65 equal 随机正负 0
      69  op mul 随机角度 随机角度 随机正负
      70  op add 发射角度 随机角度 角度
>>>>  71  bullet 子弹 @renale 19 BX BY 发射角度 2 null 伤害 1 1 -1 -1
      72  op sub 发射次数 发射次数 1
      73  jump 41 greaterThanEq 发射次数 0
      74  setprop @health 信标 0
      75  setmarker remove 10001 0 0 0
      76  wait 0.75
```

判定:
备注:

### `0781e620f8`

- 出处：`mindustrytop-25807` · (62,16) · world-processor · 21 条语句
- 处理器自己的链接：`container1`
- 被指行：语句序号 **8**
- 规则说：version gate: uses select -- needs build >= 150; on anything older the line is replaced by noop and silently does nothing

```
       0  setrate 9999
       1  set 阶段 1
       2  set 队伍 2
       3  set 每轮时间 25
       4  set 每阶段轮数 3
       5  set 第1阶段每轮增加 45
       6  set 第2阶段每轮增加 55
       7  set 第3阶段每轮增加 65
>>>>   8  select 当前增加 equal 阶段 1 第1阶段每轮增加 当前增加
       9  fetch core 核心 队伍 0 @conveyor
      10  sensor  核心 @surge-alloy
      11  op add .  当前增加
      12  setprop @surge-alloy 核心 .
      13  wait 每轮时间
      14  op add 轮数 轮数 1
      15  jump 9 lessThan 轮数 180
      16  op add 阶段 阶段 1
      17  set 轮数 0
      18  select 当前增加 equal 阶段 2 第2阶段每轮增加 当前增加
      19  select 当前增加 greaterThanEq 阶段 3 第3阶段每轮增加 当前增加
      20  jump 9 always 轮数 180
```

判定:
备注:

### `28d1a2dbe1`

- 出处：`mindustrytop-25807` · (62,17) · world-processor · 21 条语句
- 处理器自己的链接：`container1`
- 被指行：语句序号 **8**
- 规则说：version gate: uses select -- needs build >= 150; on anything older the line is replaced by noop and silently does nothing

```
       0  setrate 9999
       1  set 阶段 1
       2  set 队伍 1
       3  set 每轮时间 25
       4  set 每阶段轮数 3
       5  set 第1阶段每轮增加 45
       6  set 第2阶段每轮增加 55
       7  set 第3阶段每轮增加 65
>>>>   8  select 当前增加 equal 阶段 1 第1阶段每轮增加 当前增加
       9  fetch core 核心 队伍 0 @conveyor
      10  sensor  核心 @surge-alloy
      11  op add .  当前增加
      12  setprop @surge-alloy 核心 .
      13  wait 每轮时间
      14  op add 轮数 轮数 1
      15  jump 9 lessThan 轮数 180
      16  op add 阶段 阶段 1
      17  set 轮数 0
      18  select 当前增加 equal 阶段 2 第2阶段每轮增加 当前增加
      19  select 当前增加 greaterThanEq 阶段 3 第3阶段每轮增加 当前增加
      20  jump 9 always 轮数 180
```

判定:
备注:

### `3cdf76cf37`

- 出处：`mindustrytop-26076` · (22,28) · world-processor · 51 条语句
- 处理器自己的链接：`switch1`
- 被指行：语句序号 **35**
- 规则说：version gate: uses bullet -- needs build >= 157; on anything older the line is replaced by noop and silently does nothing

```
       0  ubind @toxopid
       1  sensor x @unit @x
       2  sensor y @unit @y
       3  sensor sx @unit @shootX
       4  sensor sy @unit @shootY
       5  sensor s @unit @shooting
       6  sensor t @unit @team
       7  sensor r @unit @rotation
       8  sensor e switch1 @enabled
       9  op rand xA 1 sx
      10  op rand xR -1 sx
      11  op rand yA 1 sx
      12  op rand yR -1 sx
      13  op add xrand xA xR
      14  op add yrand yA yR
      15  op add Xrandom xrand x
      16  op add Yrandom yrand y
      17  op sub bx x sx
      18  op sub by y sy
      19  op angle rot bx by
      20  op len lte bx by
      21  op min ltef lte 60
      22  op div ltefs ltef 29.5
      23  op div ltefs2 ltef 18
      24  op div ltefsc ltefs 2
      25  op div ltefsc2 ltefs2 3
      26  op add rotfix rot 180
      27  op add rotR rota rotr
      28  op add rotrand rotfix rotR
      29  op strictEqual bj b 3
      30  jump 32 strictEqual e 1
      31  end
      32  jump 48 strictEqual bj 1
      33  jump 35 strictEqual s 1
      34  end
>>>>  35  bullet result @toxopid 2 x y rotfix t null 3400 2 ltefsc sx sy
      36  bullet result @toxopid 2 x y rotfix t null 3400 2 ltefsc sx sy
      37  bullet result @arkyid 6 x y rotfix t null 3400 2.8 ltefsc2 sx sy
      38  bullet result @arkyid 6 x y rotfix t null 3400 2.4 ltefsc2 sx sy
      39  bullet result @arkyid 6 x y rotfix t null 3400 2.0 ltefsc2 sx sy
      40  bullet result @arkyid 6 x y rotfix t null 3400 1.6 ltefsc2 sx sy
      41  bullet result @arkyid 6 x y rotfix t null 3400 1.2 ltefsc2 sx sy
      42  bullet result @arkyid 6 x y rotfix t null 3400 0.8 ltefsc2 sx sy
      43  bullet result @arkyid 6 x y rotfix t null 3400 0.4 ltefsc2 sx sy
      44  bullet result @arkyid 6 x y rotfix t null 3400 0 ltefsc2 sx sy
      45  op add b b 1
      46  setrate 10000
      47  end
      48  op mul b b 0
      49  wait 2
      50  end
```

判定:
备注:

### `6ff28db87b`

- 出处：`mindustrytop-26076` · (22,29) · world-processor · 48 条语句
- 处理器自己的链接：`switch1`, `wall1`, `wall2`
- 被指行：语句序号 **33**
- 规则说：version gate: uses bullet -- needs build >= 157; on anything older the line is replaced by noop and silently does nothing

```
       0  ubind @eclipse
       1  sensor x @unit @x
       2  sensor y @unit @y
       3  sensor sx @unit @shootX
       4  sensor sy @unit @shootY
       5  sensor s @unit @shooting
       6  sensor t @unit @team
       7  sensor r @unit @rotation
       8  sensor e switch1 @enabled
       9  op rand xA 10 sx
      10  op rand xR -10 sx
      11  op rand yA 10 sx
      12  op rand yR -10 sx
      13  op add xrand xA xR
      14  op add yrand yA yR
      15  op add Xrandom xrand x
      16  op add Yrandom yrand y
      17  op sub bx Xrandom sx
      18  op sub by Yrandom sy
      19  op angle rot bx by
      20  op len lte bx by
      21  op min ltef lte 160
      22  op div ltefs ltef 17
      23  op div ltefs2 ltef 18
      24  op div ltefsc ltefs 2
      25  op div ltefsc2 ltefs2 3
      26  op add rotfix rot 180
      27  op add rotR rota rotr
      28  op add rotrand rotfix rotR
      29  jump 31 strictEqual e 1
      30  end
      31  jump 33 strictEqual s 1
      32  end
>>>>  33  bullet result @fortress 0 Xrandom Yrandom rotrand t null 600 2 ltefsc sx sy
      34  bullet result @fortress 0 Xrandom Yrandom rotrand t null 600 2 ltefsc sx sy
      35  bullet result @fortress 0 Xrandom Yrandom rotrand t null 600 2 ltefsc sx sy
      36  bullet result @fortress 0 Xrandom Yrandom rotrand t null 600 2 ltefsc sx sy
      37  bullet result @fortress 0 Xrandom Yrandom rotrand t null 600 2 ltefsc sx sy
      38  bullet result @fortress 0 Xrandom Yrandom rotrand t null 600 2 ltefsc sx sy
      39  bullet result @fortress 0 Xrandom Yrandom rotrand t null 600 2 ltefsc sx sy
      40  effect crossExplosion Xrandom Yrandom 10 %ff8940
      41  effect hitSquare Xrandom Yrandom 10 %ff8940
      42  effect smokeSquareBig Xrandom Yrandom rotrand %ff8940
      43  effect smokePuff Xrandom Yrandom rotrand %ff8940
      44  effect hitSquare Xrandom Yrandom rotrand %ff8940
      45  effect drillBig Xrandom Yrandom rotrand %ff8940
      46  wait 0.5
      47  end
```

判定:
备注:

### `3582ec9566`

- 出处：`mindustrytop-26076` · (41,396) · world-processor · 56 条语句
- 处理器自己的链接：`switch1`, `switch2`
- 被指行：语句序号 **38**
- 规则说：version gate: uses bullet -- needs build >= 157; on anything older the line is replaced by noop and silently does nothing

```
       0  ubind @reign
       1  sensor x @unit @x
       2  sensor y @unit @y
       3  sensor sx @unit @shootX
       4  sensor sy @unit @shootY
       5  sensor s @unit @shooting
       6  sensor t @unit @team
       7  sensor r @unit @rotation
       8  sensor e switch1 @enabled
       9  op rand xA 200 sx
      10  op rand xR -200 sx
      11  op rand yA 200 sx
      12  op rand yR -200 sx
      13  op add xrand xA xR
      14  op add yrand yA yR
      15  op add Xrandom xrand x
      16  op add Yrandom yrand y
      17  op sub bx Xrandom x
      18  op sub by Yrandom y
      19  op angle rot bx by
      20  op len lte bx by
      21  op min ltef lte 160
      22  op div ltefs ltef 30.75
      23  op div ltefs2 ltef 58.75
      24  op mul ltefsc ltefs 2
      25  op div ltefsc2 ltefs2 2
      26  op add rotfix rot 180
      27  op add rotR rota rotr
      28  op add rotrand rotfix rotR
      29  op strictEqual bjs b 200
      30  op strictEqual bjs2 b2 200
      31  op rand rr 360 200
      32  jump 34 strictEqual e 1
      33  end
      34  jump 52 strictEqual bjs2 1
      35  jump 48 strictEqual bjs 1
      36  jump 38 strictEqual s 1
      37  end
>>>>  38  bullet result @breach @carbide Xrandom Yrandom rotrand t null 1200 0.5 ltefsc sx sy
      39  bullet result @titan @thorium Xrandom Yrandom rotrand t null 1200 2 ltefsc2 sx sy
      40  effect hitSquare Xrandom Yrandom 10 %ff8940
      41  effect smokeSquareBig Xrandom Yrandom rotrand %ff8940
      42  effect smokePuff Xrandom Yrandom rotrand %ff89409e
      43  effect hitSquare Xrandom Yrandom rotrand %ff8940
      44  effect drillBig Xrandom Yrandom rotrand %ff8940
      45  op add b b 1
      46  setrate 25
      47  end
      48  op add b2 b2 1
      49  bullet result @breach @carbide x y rr t null 1200 0.25 50 sx sy
      50  setrate 50
      51  end
      52  op mul b b 0
      53  op mul b2 b2 0
      54  wait 5
      55  end
```

判定:
备注:

### `55105bcf1a`

- 出处：`mindustrytop-25765` · (62,192) · world-processor · 5 条语句
- 处理器自己的链接：`scathe1`, `bastion1`
- 被指行：语句序号 **3**
- 规则说：version gate: uses select -- needs build >= 150; on anything older the line is replaced by noop and silently does nothing

```
       0  getlink b 1
       1  getlink B 0
       2  sensor D b @dead
>>>>   3  select E equal D 1 1 0
       4  control enabled B E 0 0 0
```

判定:
备注:

### `ec03255560`

- 出处：`mindustrytop-25765` · (252,293) · world-processor · 4 条语句
- 处理器自己的链接：`duct1`, `bastion1`
- 被指行：语句序号 **2**
- 规则说：version gate: uses select -- needs build >= 150; on anything older the line is replaced by noop and silently does nothing

```
       0  getlink b 1
       1  sensor D b @dead
>>>>   2  select E equal D 1 1 0
       3  control enabled duct1 E 0 0 0
```

判定:
备注:

### `2e9dc54fe4`

- 出处：`mindustrytop-25872` · (24,69) · logic-processor · 144 条语句
- 处理器自己的链接：`board`, `cell1`
- 被指行：语句序号 **87**
- 规则说：version gate: uses op ushr -- needs build >= 150; on anything older the line is replaced by noop and silently does nothing

```
      ... 上面还有 57 条语句
      57  op land _5 _3 _4
      58  op mul _2 _2 _5
      59  op mul _0 0.0 _5
      60  op add _6 0 _0
      61  read _7 cell1 _6
      62  op and _8 _7 _2
      63  op notEqual b4 _8 0
      64  print "位3="
      65  print b3
      66  print " 位4="
      67  print b4
      68  print " 置位总数="
      69  print n
      70  printflush board
      71  set @counter 0
      72  jump __ls_end always x false
      73  __ls_func___ls_builtin_bwrite_entry:
      74  write __ls_func___ls_builtin_bwrite_value __ls_func___ls_builtin_bwrite_mem __ls_func___ls_builtin_bwrite_addr
      75  set __ls_func___ls_builtin_bwrite_result 1
      76  set @counter __ls_func___ls_builtin_bwrite_ret
      77  __ls_func___ls_builtin_bwrite_exit:
      78  set @counter __ls_func___ls_builtin_bwrite_ret
      79  __ls_func___ls_builtin_bitcount_entry:
      80  set __ls_bit_count 0
      81  set __ls_bit_w 0
      82  __ls_func___ls_builtin_bitcount_stmt_2:
      83  jump __ls_func___ls_builtin_bitcount_while_body_2 lessThan __ls_bit_w __ls_func___ls_builtin_bitcount_words
      84  jump __ls_func___ls_builtin_bitcount_stmt_12 always x false
      85  __ls_func___ls_builtin_bitcount_while_body_2:
      86  op add __ls_bit_addr __ls_func___ls_builtin_bitcount_base __ls_bit_w
>>>>  87  read __ls_bit_word __ls_func___ls_builtin_bitcount_mem __ls_bit_addr
      88  __ls_func___ls_builtin_bitcount_stmt_5:
      89  jump __ls_func___ls_builtin_bitcount_while_body_5 notEqual __ls_bit_word 0
      90  jump __ls_func___ls_builtin_bitcount_stmt_10 always x false
      91  __ls_func___ls_builtin_bitcount_while_body_5:
      92  op and __ls_bit_tmp __ls_bit_word 1
      93  op add __ls_bit_count __ls_bit_count __ls_bit_tmp
      94  op ushr __ls_bit_word __ls_bit_word 1
      95  jump __ls_func___ls_builtin_bitcount_stmt_5 always x false
      96  __ls_func___ls_builtin_bitcount_stmt_10:
      97  op add __ls_bit_w __ls_bit_w 1
      98  jump __ls_func___ls_builtin_bitcount_stmt_2 always x false
      99  __ls_func___ls_builtin_bitcount_stmt_12:
     100  set __ls_func___ls_builtin_bitcount_result __ls_bit_count
     101  set @counter __ls_func___ls_builtin_bitcount_ret
     102  __ls_func___ls_builtin_bitcount_exit:
     103  set @counter __ls_func___ls_builtin_bitcount_ret
     104  __ls_end:
     105  # @logic-sugar-v2 begin
     106  # @logic-sugar-line bitset bits cell1 0 2
     107  # @logic-sugar-line datacall bitset_set r1 "bits, 3"
     108  # @logic-sugar-line datacall bitset_set r2 "bits, 5"
     109  # @logic-sugar-line datacall bitset_count n "bits"
     110  # @logic-sugar-line op idiv _0 3 64
     111  # @logic-sugar-line op mod _1 3 64
     112  # @logic-sugar-line op shl _2 1 _1
     113  # @logic-sugar-line op greaterThanEq _3 3 0
     114  # @logic-sugar-line op lessThan _4 3 128
     115  # @logic-sugar-line op land _5 _3 _4
     116  # @logic-sugar-line op mul _2 _2 _5
     117  # @logic-sugar-line op mul _0 _0 _5
      ... 下面还有 26 条语句
```

判定:
备注:

### `ff0ef072b4`

- 出处：`mindustrytop-20445` · (7,0) · world-processor · 25 条语句
- 处理器自己的链接：`cell1`
- 被指行：语句序号 **7**
- 规则说：version gate: uses format -- needs build >= 147; on anything older the line is replaced by noop and silently does nothing

```
       0  setrate 30
       1  op idiv min @waveTime 60
       2  op mod sec @waveTime 60
       3  op idiv sec sec 1
       4  read c cell1 0
       5  jump 16 notEqual @clientLocale "zh_CN"
       6  print "[gold]资金： {0}\n[red]波次：\n {1}/150\n({2}:{3}{4}秒)"
>>>>   7  format c
       8  format @waveNumber
       9  format min
      10  format sec
      11  jump 14 notEqual sec 0
      12  format "0"
      13  jump 24 always @clientLocale "zh_CN"
      14  format ""
      15  jump 24 always @clientLocale "zh_CN"
      16  print "[gold]Coin： {0}\n[red]Wave：\n {1}/150\n({2}:{3}{4}秒)"
      17  format @waveNumber
      18  format min
      19  format sec
      20  jump 23 notEqual sec 0
      21  format "0"
      22  jump 24 always @clientLocale "zh_CN"
      23  format ""
      24  message mission 10 @wait
```

判定:
备注:

### `b641c91790`

- 出处：`mindustrytop-20445` · (15,0) · world-processor · 70 条语句
- 处理器自己的链接：`processor1`, `processor2`
- 被指行：语句序号 **15**
- 规则说：version gate: uses format -- needs build >= 147; on anything older the line is replaced by noop and silently does nothing

```
       0  set readType "Turret"
       1  setrate 1000
       2  set GetId 0
       3  op mul ctr+ GetId 6
       4  op add ctr ctr+ 3
       5  set isnull 0
       6  wait 0.03
       7  write ctr processor1 "@counter"
       8  read length processor1 "length"
       9  op add GetId GetId 1
      10  wait 0.05
      11  read category processor1 "category"
      12  jump 36 strictEqual category null
      13  jump 17 equal category readType
      14  print "{0}读取失败：category填写错误！请检查category中是否有错字或少字！"
>>>>  15  format type
      16  jump 39 always x false
      17  read type processor1 "type"
      18  read cost processor1 "cost"
      19  read parent0 processor1 "parent[0]"
      20  read parent1 processor1 "parent[1]"
      21  read parent2 processor1 "parent[2]"
      22  read parent3 processor1 "parent[3]"
      23  read parent4 processor1 "parent[4]"
      24  read parent5 processor1 "parent[5]"
      25  op strictEqual root parent0 "newRoot"
      26  jump 48 notEqual parent0 null
      27  jump 48 notEqual parent1 null
      28  jump 48 notEqual parent2 null
      29  jump 48 notEqual parent3 null
      30  jump 48 notEqual parent4 null
      31  jump 48 notEqual parent5 null
      32  print "{0}读取失败：parent为null！"
      33  format type
      34  set isnull 1
      35  jump 39 always x false
      36  print "{0}读取失败：category为null！"
      37  format type
      38  set isnull 1
      39  message notify 3 @wait
      40  sensor x processor1 @x
      41  sensor y processor1 @y
      42  effect lightBlock x y 1 %ff0f09
      43  wait 0.1
      44  effect lightBlock x y 1 %ff0f09
      45  wait 0.1
      ... 下面还有 24 条语句
```

判定:
备注:

### `9858f68133`

- 出处：`mindustrytop-20445` · (16,0) · world-processor · 70 条语句
- 处理器自己的链接：`processor1`, `processor2`
- 被指行：语句序号 **15**
- 规则说：version gate: uses format -- needs build >= 147; on anything older the line is replaced by noop and silently does nothing

```
       0  set readType "Drill"
       1  setrate 1000
       2  set GetId 0
       3  op mul ctr+ GetId 5
       4  op add ctr ctr+ 3
       5  set isnull 0
       6  wait 0.03
       7  write ctr processor1 "@counter"
       8  read length processor1 "length"
       9  op add GetId GetId 1
      10  wait 0.05
      11  read category processor1 "category"
      12  jump 36 strictEqual category null
      13  jump 17 equal category readType
      14  print "{0}读取失败：category填写错误！请检查category中是否有错字或少字！"
>>>>  15  format type
      16  jump 39 always x false
      17  read type processor1 "type"
      18  read cost processor1 "cost"
      19  read parent0 processor1 "parent[0]"
      20  read parent1 processor1 "parent[1]"
      21  read parent2 processor1 "parent[2]"
      22  read parent3 processor1 "parent[3]"
      23  read parent4 processor1 "parent[4]"
      24  read parent5 processor1 "parent[5]"
      25  op strictEqual root parent0 "newRoot"
      26  jump 48 notEqual parent0 null
      27  jump 48 notEqual parent1 null
      28  jump 48 notEqual parent2 null
      29  jump 48 notEqual parent3 null
      30  jump 48 notEqual parent4 null
      31  jump 48 notEqual parent5 null
      32  print "{0}读取失败：parent为null！"
      33  format type
      34  set isnull 1
      35  jump 39 always x false
      36  print "{0}读取失败：category为null！"
      37  format type
      38  set isnull 1
      39  message notify 3 @wait
      40  sensor x processor1 @x
      41  sensor y processor1 @y
      42  effect lightBlock x y 1 %ff0f09
      43  wait 0.1
      44  effect lightBlock x y 1 %ff0f09
      45  wait 0.1
      ... 下面还有 24 条语句
```

判定:
备注:

## 规则 `undefined-var-is-not-automatically-an-error`

### `5da785b665`

- 出处：`mindustrytop-25559` · (391,445) · world-processor · 164 条语句
- 处理器自己的链接：`wall1`, `cell1`
- 被指行：语句序号 **1**
- 规则说：`a` is read here but is never assigned anywhere in this program (and is not a link or built-in)

```
       0  setrate 1000
>>>>   1  op add result a b
       2  op mul ix1 3 @thisx
       3  op mul ix2 7 @thisy
       4  op mul iy1 5 @thisx
       5  op mul iy2 11 @thisy
       6  op add id1 ix1 iy2
       7  op add id2 ix2 iy1
       8  op mul id3 ix1 iy2
       9  op mul id4 ix2 iy1
      10  op add id5 id1 id4
      11  op add id6 id2 id3
      12  sensor wx1 wall1 @x
      13  sensor wy1 wall1 @y
      14  op add wx1 wx1 0.5
      15  op sub wy1 wy1 0.5
      16  set rot1 0
      17  set rot2 0
      18  read rzd cell1 33
      19  read rd cell1 90
      20  op mul st rd rzd
      21  jump 148 equal st 0
      22  makemarker shape id1 0 0 true
      23  makemarker shape id2 0 0 true
      24  makemarker quad id3 0 0 true
      25  makemarker quad id4 0 0 true
      26  makemarker quad id5 0 0 true
      27  makemarker quad id6 0 0 true
      28  setmarker shape id1 6 0 0
      29  setmarker shape id2 360 0 0
      30  setmarker stroke id1 2 0 0
      31  setmarker stroke id2 1.5 0 0
      ... 下面还有 132 条语句
```

判定:
备注:

### `a1a857e0a3`

- 出处：`mindustrytop-26053` · (64,17) · world-processor · 40 条语句
- 处理器自己的链接：`cell1`
- 被指行：语句序号 **32**
- 规则说：`b` is read here but is never assigned anywhere in this program (and is not a link or built-in)

```
       0  read 游戏模式 cell1 2
       1  jump 0 notEqual 游戏模式 "生存"
       2  setblock ore @air 7 101 @derelict 0
       3  print "\n"
       4  fetch buildCount 黄队容器数量 @sharded 0 @container
       5  setrate 100
       6  fetch core a 1 0 @container
       7  sensor 1 a @surge-alloy
       8  sensor 最大生命值1 a @maxHealth
       9  sensor 生命值1 a @health
      10  op div 百分比1 生命值1 最大生命值1
      11  op idiv 百分比1. 百分比1 0.01
      12  select 增加值 lessThanEq @second 360 55 增加值
      13  select 增加值 lessThanEq @second 180 45 增加值
      14  select 增加值 greaterThan @second 360 65 增加值
      15  op mul 加成1 黄队容器数量 15
      16  op add 增加值1 增加值 加成1
      17  print "[#cccc00]黄[#ffffff]"
      18  print 1
      19  print "+"
      20  print 增加值1
      21  print "\n"
      22  print "生命值:"
      23  print 百分比1.
      24  print "%\n"
      25  print "波次倒计时:"
      26  op idiv jjj @waveTime 1
      27  print jjj
      28  print "\n当前波次:"
      29  print @waveNumber
      30  message mission 3 @wait
      31  sensor f a @surge-alloy
>>>>  32  sensor e b @surge-alloy
      33  jump 3 greaterThanEq @waveTime 1
      34  set ddd 0
      35  op mul w 黄队容器数量 15
      36  op add u f w
      37  op add u1 u 增加值
      38  setprop @surge-alloy a u1
      39  wait 3
```

判定:
备注:

### `a24520c9e9`

- 出处：`mindustrytop-26053` · (66,29) · world-processor · 10 条语句
- 处理器自己的链接：`cell1`
- 被指行：语句序号 **0**
- 规则说：`sx` is read here but is never assigned anywhere in this program (and is not a link or built-in)

```
>>>>   0  op sub dx sx @thisx
       1  op sub dy sy @thisy
       2  op len dist dx dy
       3  op add id @thisx temp
       4  read 文字 cell1 1
       5  print 文字
       6  makemarker shapeText id @thisx @thisy true
       7  setmarker flushText id 0 0 0
       8  setmarker fontSize id 2 0 0
       9  wait 0.5
```

判定:
备注:

### `6389166293`

- 出处：`mindustrytop-26053` · (66,29) · world-processor · 10 条语句
- 处理器自己的链接：`cell1`
- 被指行：语句序号 **1**
- 规则说：`sy` is read here but is never assigned anywhere in this program (and is not a link or built-in)

```
       0  op sub dx sx @thisx
>>>>   1  op sub dy sy @thisy
       2  op len dist dx dy
       3  op add id @thisx temp
       4  read 文字 cell1 1
       5  print 文字
       6  makemarker shapeText id @thisx @thisy true
       7  setmarker flushText id 0 0 0
       8  setmarker fontSize id 2 0 0
       9  wait 0.5
```

判定:
备注:

### `50510ae108`

- 出处：`mindustrytop-24936` · (7,22) · world-processor · 68 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **27**
- 规则说：`flase` is read here but is never assigned anywhere in this program (and is not a link or built-in)

```
       0  fetch unitCount BOSS 2 0 @oxynoe
       1  jump 0 lessThan BOSS 1
       2  fetch unit BOSS 2 0 @oxynoe
       3  getflag 难1 "普通"
       4  getflag 难2 "困难"
       5  jump 9 equal 难1 1
       6  jump 11 equal 难2 1
       7  set 难度 0
       8  jump 12 always x false
       9  set 难度 1
      10  jump 12 always x false
      11  set 难度 2
      12  set A 0
      13  fetch unit 信标 2 A @mono
      14  op add A A 1
      15  sensor F 信标 @flag
      16  jump 19 equal F 225
      17  jump 13 notEqual 信标 false
      18  end
      19  set 重复 0
      20  setrate 10
      21  sensor X 信标 @x
      22  sensor Y 信标 @y
      23  set 次数 0
      24  op add 次数 次数 1
      25  op add ID 次数 10001
      26  op mul 大小 次数 66
>>>>  27  makemarker shape ID X Y flase
      28  setmarker shape ID 100 0 0
      29  setmarker stroke ID 24 0 0
      30  setmarker radius ID 大小 0 0
      31  setmarker color ID %4cff4a8b 0 0
      32  wait 0.15
      33  jump 24 lessThan 次数 13
      34  wait 0.4
      35  set 次数 0
      36  set 角度 0
      37  set 大小 8
      38  op mul 伤害倍率 难度 100
      39  op add 伤害 伤害倍率 400
      40  op mul 爆炸倍率 重复 12
      41  op add 爆炸次数 爆炸倍率 24
      42  op mul 速度倍率 重复 50
      43  op add 速度 速度倍率 125
      44  setrate 速度
      45  op div 爆炸夹角 360 爆炸次数
      46  op add 角度 角度 爆炸夹角
      47  op cos CX 角度 b
      48  op sin SY 角度 b
      49  op mul X倍率 CX 大小
      50  op mul Y倍率 SY 大小
      51  op add 发X X倍率 X
      52  op add 发Y Y倍率 Y
      53  explosion 2 发X 发Y 2.8 伤害 true true false true
      54  effect vapor 发X 发Y 2 %5bff50
      55  effect vapor 发X 发Y 2 %5bff50
      56  op add 次数 次数 1
      57  jump 46 lessThan 次数 爆炸次数
      ... 下面还有 10 条语句
```

判定:
备注:

### `c8146bb412`

- 出处：`mindustrytop-24936` · (5,23) · world-processor · 77 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **28**
- 规则说：`flase` is read here but is never assigned anywhere in this program (and is not a link or built-in)

```
       0  fetch unitCount BOSS 2 0 @oxynoe
       1  jump 0 lessThan BOSS 1
       2  fetch unit BOSS 2 0 @oxynoe
       3  getflag 难1 "普通"
       4  getflag 难2 "困难"
       5  jump 9 equal 难1 1
       6  jump 11 equal 难2 1
       7  set 难度 0
       8  jump 12 always x false
       9  set 难度 1
      10  jump 12 always x false
      11  set 难度 2
      12  set A 0
      13  fetch unit 信标 2 A @mono
      14  op add A A 1
      15  ubind 信标
      16  sensor F @unit @flag
      17  jump 20 equal F 222
      18  jump 13 notEqual 信标 false
      19  end
      20  set 重复 0
      21  set 发射次数 40
      22  set 大小 0
      23  setrate 25
      24  op add 大小 大小 5
      25  op mul 2倍 大小 2
      26  sensor BX BOSS @x
      27  sensor BY BOSS @y
>>>>  28  makemarker shape 10001 BX BY flase
      29  setmarker stroke 10001 2倍 12 0
      30  setmarker radius 10001 大小 12 0
      31  setmarker shape 10001 90 0 0
      32  setmarker outline 10001 0 12 0
      33  setmarker color 10001 %50ff5254 12 0
      34  op sub 小角 角度 6
      35  op add 大角 角度 6
      36  setmarker arc 10001 小角 大角 0
      37  jump 41 lessThanEq 大小 280
      38  jump 24 lessThan 大小 300
      39  sensor BX BOSS @x
      40  sensor BY BOSS @y
      41  sensor X @unit @x
      42  sensor Y @unit @y
      43  sensor BX BOSS @x
      44  sensor BY BOSS @y
      45  uradar enemy any any distance 0 1 敌人
      46  sensor DX 敌人 @x
      47  sensor DY 敌人 @y
      48  setprop @x 信标 DX
      49  setprop @y 信标 DY
      50  op sub 差X BX X
      51  op sub 差Y BY Y
      52  op div 比例 差X 差Y
      53  op atan 角度 比例 差X
      54  jump 57 greaterThan 差Y 0
      55  op sub 角度 90 角度
      56  jump 58 always 差Y 0
      57  op sub 角度 270 角度
      58  jump 24 lessThanEq 大小 280
      ... 下面还有 18 条语句
```

判定:
备注:

### `aa3a035e0b`

- 出处：`mindustrytop-24936` · (1,56) · world-processor · 57 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **24**
- 规则说：`ff9561cf` is read here but is never assigned anywhere in this program (and is not a link or built-in)

```
       0  fetch unitCount BOSS 2 0 @merui
       1  jump 0 lessThan BOSS 1
       2  fetch unit BOSS 2 0 @merui
       3  getflag 难1 "普通"
       4  getflag 难2 "困难"
       5  jump 9 equal 难1 1
       6  jump 11 equal 难2 1
       7  set 难度 0
       8  jump 12 always x false
       9  set 难度 1
      10  jump 12 always x false
      11  set 难度 2
      12  set A 0
      13  fetch unit 信标 2 A @mono
      14  op add A A 1
      15  sensor F 信标 @flag
      16  jump 19 equal F 121
      17  jump 13 notEqual 信标 false
      18  end
      19  set 次数 0
      20  sensor X 信标 @x
      21  sensor Y 信标 @y
      22  effect trail X Y 77 %ff9561cf
      23  wait 0.2
>>>>  24  effect trail X Y 77 ff9561cf
      25  wait 0.2
      26  sensor BX BOSS @x
      27  sensor BY BOSS @y
      28  op mul 速度倍率 难度 2
      29  op add 速度 速度倍率 10
      30  setrate 速度
      31  op mul 伤害倍率 难度 45
      32  op add 伤害 伤害倍率 135
      33  op mul 分裂弹伤害 伤害 0.3
      34  op mul 分裂倍率 难度 2
      35  op add 分裂次数 分裂倍率 4
      36  op div 分裂角度 360 分裂次数
      37  set 发射Y BY
      38  op add 发射Y 发射Y 1
      39  op add 次数 次数 1
      40  effect trail BX 发射Y 5 %2bffd1
      41  jump 38 lessThanEq 次数 100
      42  wait 0.5
      43  op add 最高Y Y 100
      44  set 发射Y 最高Y
      45  op sub 次数 次数 1
      46  op sub 发射Y 发射Y 1
      47  effect trail X 发射Y 5 %16ffe5
      48  jump 45 greaterThanEq 次数 0
      49  explosion 2 X 发射Y 11 伤害 false true false true
      50  explosion 2 X 发射Y 11 分裂弹伤害 true false false true
      51  set 角度 0
      52  bullet 子弹 @renale 2 X Y 角度 2 null 分裂弹伤害 1 0.75 -1 -1
      53  op add 角度 角度 分裂角度
      54  jump 52 lessThan 角度 360
      55  setprop @health 信标 0
      56  wait 1
```

判定:
备注:

### `50f8763efa`

- 出处：`mindustrytop-25807` · (63,27) · world-processor · 10 条语句
- 处理器自己的链接：`cell1`
- 被指行：语句序号 **3**
- 规则说：`temp` is read here but is never assigned anywhere in this program (and is not a link or built-in)

```
       0  op sub dx sx @thisx
       1  op sub dy sy @thisy
       2  op len dist dx dy
>>>>   3  op add id @thisx temp
       4  read 文字 cell1 1
       5  print 文字
       6  makemarker shapeText id @thisx @thisy true
       7  setmarker flushText id 0 0 0
       8  setmarker fontSize id 2 0 0
       9  wait 0.5
```

判定:
备注:

### `792f988f09`

- 出处：`mindustrytop-26076` · (22,28) · world-processor · 51 条语句
- 处理器自己的链接：`switch1`
- 被指行：语句序号 **27**
- 规则说：`rota` is read here but is never assigned anywhere in this program (and is not a link or built-in)

```
       0  ubind @toxopid
       1  sensor x @unit @x
       2  sensor y @unit @y
       3  sensor sx @unit @shootX
       4  sensor sy @unit @shootY
       5  sensor s @unit @shooting
       6  sensor t @unit @team
       7  sensor r @unit @rotation
       8  sensor e switch1 @enabled
       9  op rand xA 1 sx
      10  op rand xR -1 sx
      11  op rand yA 1 sx
      12  op rand yR -1 sx
      13  op add xrand xA xR
      14  op add yrand yA yR
      15  op add Xrandom xrand x
      16  op add Yrandom yrand y
      17  op sub bx x sx
      18  op sub by y sy
      19  op angle rot bx by
      20  op len lte bx by
      21  op min ltef lte 60
      22  op div ltefs ltef 29.5
      23  op div ltefs2 ltef 18
      24  op div ltefsc ltefs 2
      25  op div ltefsc2 ltefs2 3
      26  op add rotfix rot 180
>>>>  27  op add rotR rota rotr
      28  op add rotrand rotfix rotR
      29  op strictEqual bj b 3
      30  jump 32 strictEqual e 1
      31  end
      32  jump 48 strictEqual bj 1
      33  jump 35 strictEqual s 1
      34  end
      35  bullet result @toxopid 2 x y rotfix t null 3400 2 ltefsc sx sy
      36  bullet result @toxopid 2 x y rotfix t null 3400 2 ltefsc sx sy
      37  bullet result @arkyid 6 x y rotfix t null 3400 2.8 ltefsc2 sx sy
      38  bullet result @arkyid 6 x y rotfix t null 3400 2.4 ltefsc2 sx sy
      39  bullet result @arkyid 6 x y rotfix t null 3400 2.0 ltefsc2 sx sy
      40  bullet result @arkyid 6 x y rotfix t null 3400 1.6 ltefsc2 sx sy
      41  bullet result @arkyid 6 x y rotfix t null 3400 1.2 ltefsc2 sx sy
      42  bullet result @arkyid 6 x y rotfix t null 3400 0.8 ltefsc2 sx sy
      43  bullet result @arkyid 6 x y rotfix t null 3400 0.4 ltefsc2 sx sy
      44  bullet result @arkyid 6 x y rotfix t null 3400 0 ltefsc2 sx sy
      45  op add b b 1
      46  setrate 10000
      47  end
      48  op mul b b 0
      49  wait 2
      50  end
```

判定:
备注:

### `69d9771071`

- 出处：`mindustrytop-26076` · (26,28) · world-processor · 21 条语句
- 处理器自己的链接：`processor1`
- 被指行：语句序号 **6**
- 规则说：`old` is read here but is never assigned anywhere in this program (and is not a link or built-in)

```
       0  setrate 100
       1  fetch playerCount pc 2 0 @conveyor
       2  jump 4 greaterThan pc 0
       3  end
       4  fetch player p 2 0 @conveyor
       5  sensor n p @name
>>>>   6  jump 3 equal n old
       7  print "[red]：未知信号接入？"
       8  message announce 3 @wait
       9  print "名字:"
      10  print n
      11  message announce 2 @wait
      12  print "[red]：………"
      13  message announce 2 @wait
      14  print "[gray]：我说爆炸降临此处……也永远不会停下"
      15  message announce 3 @wait
      16  print "要多少强度自己填"
      17  wait 2
      18  explosion @crux 54 51 9999999999999 100000000 true true false true
      19  explosion @crux 54 260 9999999999999 100000000 true true false true
      20  jump 17 always x false
```

判定:
备注:

### `ea561073b4`

- 出处：`mindustrytop-25736` · (226,11) · world-processor · 87 条语句
- 处理器自己的链接：`arc1`, `switch1`, `message1`
- 被指行：语句序号 **12**
- 规则说：`item` is read here but is never assigned anywhere in this program (and is not a link or built-in)

```
       0  setrate 340
       1  sensor team @this @team
       2  sensor k switch1 @enabled
       3  jump 2 notEqual k 1
       4  fetch core core team 0 @conveyor
       5  sensor item1 core @blast-compound
       6  sensor item2 core @surge-alloy
       7  control enabled switch1 0 0 0 0
       8  jump 2 lessThan item1 10000
       9  jump 2 lessThan item2 10000
      10  effect sparkExplosion @thisx @thisy 2 %fff679
      11  op sub item1 item1 10000
>>>>  12  op sub item2 item 10000
      13  setprop @blast-compound core item1
      14  setprop @surge-alloy core item2
      15  set 伤害 900
      16  set team 1
      17  set 伤害方 2
      18  set 拖尾高度 12
      19  set 高度 20
      20  set 范围 20
      21  set 锁定半径 8
      22  set 上升速度 0.25
      23  set 圈 7
      24  set 打击圈 4
      25  control enabled arc1 0 0 0 0
      26  sensor k arc1 @shooting
      27  sensor zx arc1 @x
      28  sensor zy arc1 @y
      29  jump 15 strictEqual k 0
      30  sensor x arc1 @shootX
      31  sensor y arc1 @shootY
      32  setblock block @air zx zy team 0
      33  setblock block @arc zx zy team 0
      34  print "正在锁定目标区域\n等待指令中"
      35  message notify 3 @wait
      36  op mul 圈 360 圈
      37  op mul 打击圈 360 打击圈
      38  op sub 打击圈 圈 打击圈
      39  set j 0
      40  set j2 180
      41  set j3 0
      42  op sin sin j b
      ... 下面还有 44 条语句
```

判定:
备注:

### `dc54ad36f3`

- 出处：`mindustrytop-14962` · (95,0) · world-processor · 54 条语句
- 处理器自己的链接：`cell1`
- 被指行：语句序号 **41**
- 规则说：`sl` is read here but is never assigned anywhere in this program (and is not a link or built-in)

```
       0  set 队伍 5
       1  jump 3 always x false
       2  set p 0
       3  fetch playerCount unitc 队伍 0 @conveyor
       4  fetch player unit 队伍 p @conveyor
       5  jump 2 greaterThan p unitc
       6  op add p p 1
       7  sensor 物品 unit @firstItem
       8  sensor 雷达 unit @range
       9  jump 11 equal 雷达 16.375
      10  end
      11  jump 15 equal 物品 @thorium
      12  jump 35 equal 物品 @surge-alloy
      13  end
      14  print 
      15  sensor 数量 unit @totalItems
      16  sensor X unit @shootX
      17  sensor Y unit @shootY
      18  sensor x unit @x
      19  sensor y unit @y
      20  sensor 射击 unit @shooting
      21  jump 23 greaterThanEq 数量 sl
      22  jump 1 always 射击 0
      23  op sub xl X x
      24  op sub yl Y y
      25  op len len xl yl
      26  jump 33 greaterThan len 雷达
      27  jump 29 notEqual 射击 0
      28  jump 33 always 射击 0
      29  setblock block @spectre X Y 队伍 0
      30  op add X1 X 3
      31  setblock block @item-source X1 Y 队伍 0
      32  op add sl sl 1
      33  end
      34  print 
      35  sensor 数量 unit @totalItems
      36  sensor X unit @shootX
      37  sensor Y unit @shootY
      38  sensor x unit @x
      39  sensor y unit @y
      40  sensor 射击 unit @shooting
>>>>  41  jump 43 greaterThanEq 数量 sl
      42  jump 1 always 射击 0
      43  op sub xl X x
      44  op sub yl Y y
      45  op len len xl yl
      46  jump 33 greaterThan len 雷达
      47  jump 49 notEqual 射击 0
      48  jump 1 always 射击 0
      49  op sub X1 X 2
      50  setblock block @heat-source X1 Y 队伍 0
      51  setblock block @afflict X Y 队伍 0
      52  op sub Y Y 1
      53  setblock block @power-source X1 Y 队伍 0
```

判定:
备注:

### `7ed8efd522`

- 出处：`mindustrytop-14962` · (93,201) · world-processor · 53 条语句
- 处理器自己的链接：`reactor1`
- 被指行：语句序号 **40**
- 规则说：`sl` is read here but is never assigned anywhere in this program (and is not a link or built-in)

```
       0  jump 2 always x false
       1  set p 0
       2  fetch playerCount unitc @sharded 0 @conveyor
       3  fetch player unit @sharded p @conveyor
       4  jump 1 greaterThan p unitc
       5  op add p p 1
       6  sensor 物品 unit @firstItem
       7  sensor 雷达 unit @range
       8  jump 10 equal 雷达 16.375
       9  end
      10  jump 14 equal 物品 @thorium
      11  jump 34 equal 物品 @surge-alloy
      12  end
      13  print 
      14  sensor 数量 unit @totalItems
      15  sensor X unit @shootX
      16  sensor Y unit @shootY
      17  sensor x unit @x
      18  sensor y unit @y
      19  sensor 射击 unit @shooting
      20  jump 22 greaterThanEq 数量 sl
      21  jump 0 always 射击 0
      22  op sub xl X x
      23  op sub yl Y y
      24  op len len xl yl
      25  jump 32 greaterThan len 雷达
      26  jump 28 notEqual 射击 0
      27  jump 32 always 射击 0
      28  setblock block @spectre X Y 1 0
      29  op add X1 X 3
      30  setblock block @item-source X1 Y 1 0
      31  op add sl sl 1
      32  end
      33  print 
      34  sensor 数量 unit @totalItems
      35  sensor X unit @shootX
      36  sensor Y unit @shootY
      37  sensor x unit @x
      38  sensor y unit @y
      39  sensor 射击 unit @shooting
>>>>  40  jump 42 greaterThanEq 数量 sl
      41  jump 0 always 射击 0
      42  op sub xl X x
      43  op sub yl Y y
      44  op len len xl yl
      45  jump 32 greaterThan len 雷达
      46  jump 48 notEqual 射击 0
      47  jump 0 always 射击 0
      48  op sub X1 X 2
      49  setblock block @heat-source X1 Y 1 0
      50  setblock block @afflict X Y 1 0
      51  op sub Y Y 1
      52  setblock block @power-source X1 Y 1 0
```

判定:
备注:

### `ba2961e66c`

- 出处：`mindustrytop-14962` · (113,201) · world-processor · 54 条语句
- 处理器自己的链接：`cell1`
- 被指行：语句序号 **41**
- 规则说：`sl` is read here but is never assigned anywhere in this program (and is not a link or built-in)

```
       0  set 队伍 3
       1  jump 3 always x false
       2  set p 0
       3  fetch playerCount unitc 队伍 0 @conveyor
       4  fetch player unit 队伍 p @conveyor
       5  jump 2 greaterThan p unitc
       6  op add p p 1
       7  sensor 物品 unit @firstItem
       8  sensor 雷达 unit @range
       9  jump 11 equal 雷达 16.375
      10  end
      11  jump 15 equal 物品 @thorium
      12  jump 35 equal 物品 @surge-alloy
      13  end
      14  print 
      15  sensor 数量 unit @totalItems
      16  sensor X unit @shootX
      17  sensor Y unit @shootY
      18  sensor x unit @x
      19  sensor y unit @y
      20  sensor 射击 unit @shooting
      21  jump 23 greaterThanEq 数量 sl
      22  jump 1 always 射击 0
      23  op sub xl X x
      24  op sub yl Y y
      25  op len len xl yl
      26  jump 33 greaterThan len 雷达
      27  jump 29 notEqual 射击 0
      28  jump 33 always 射击 0
      29  setblock block @spectre X Y 队伍 0
      30  op add X1 X 3
      31  setblock block @item-source X1 Y 队伍 0
      32  op add sl sl 1
      33  end
      34  print 
      35  sensor 数量 unit @totalItems
      36  sensor X unit @shootX
      37  sensor Y unit @shootY
      38  sensor x unit @x
      39  sensor y unit @y
      40  sensor 射击 unit @shooting
>>>>  41  jump 43 greaterThanEq 数量 sl
      42  jump 1 always 射击 0
      43  op sub xl X x
      44  op sub yl Y y
      45  op len len xl yl
      46  jump 33 greaterThan len 雷达
      47  jump 49 notEqual 射击 0
      48  jump 1 always 射击 0
      49  op sub X1 X 2
      50  setblock block @heat-source X1 Y 队伍 0
      51  setblock block @afflict X Y 队伍 0
      52  op sub Y Y 1
      53  setblock block @power-source X1 Y 队伍 0
```

判定:
备注:

### `d45daa842d`

- 出处：`mindustrytop-25939` · (51,6) · world-processor · 17 条语句
- 处理器自己的链接：`source1`
- 被指行：语句序号 **0**
- 规则说：`sx` is read here but is never assigned anywhere in this program (and is not a link or built-in)

```
>>>>   0  op sub dx sx @thisx
       1  op sub dy sy @thisy
       2  op len dist dx dy
       3  op add id @thisx temp
       4  print "[red]警告:不要试图用发散或者有荷载容量的单位试图偷走这个物品源\n我只要检测到这个物品源消失，你们就死了。(拆掉也算)"
       5  makemarker shapeText id @thisx @thisy true
       6  setmarker flushText id 0 0 0
       7  setmarker fontSize id 2 0 0
       8  wait 0.5
       9  getlink a 0
      10  jump 12 strictEqual a null
      11  end
      12  print "[red]红队物品源消失了?!死吧!!!!!!!!!!!"
      13  message announce 3 @wait
      14  spawnwave 7 101 false
      15  wait 0.1
      16  jump 14 always x false
```

判定:
备注:

### `653d1af378`

- 出处：`mindustrytop-25939` · (51,6) · world-processor · 17 条语句
- 处理器自己的链接：`source1`
- 被指行：语句序号 **1**
- 规则说：`sy` is read here but is never assigned anywhere in this program (and is not a link or built-in)

```
       0  op sub dx sx @thisx
>>>>   1  op sub dy sy @thisy
       2  op len dist dx dy
       3  op add id @thisx temp
       4  print "[red]警告:不要试图用发散或者有荷载容量的单位试图偷走这个物品源\n我只要检测到这个物品源消失，你们就死了。(拆掉也算)"
       5  makemarker shapeText id @thisx @thisy true
       6  setmarker flushText id 0 0 0
       7  setmarker fontSize id 2 0 0
       8  wait 0.5
       9  getlink a 0
      10  jump 12 strictEqual a null
      11  end
      12  print "[red]红队物品源消失了?!死吧!!!!!!!!!!!"
      13  message announce 3 @wait
      14  spawnwave 7 101 false
      15  wait 0.1
      16  jump 14 always x false
```

判定:
备注:

### `f32aaf05f8`

- 出处：`mindustrytop-25939` · (51,6) · world-processor · 17 条语句
- 处理器自己的链接：`source1`
- 被指行：语句序号 **3**
- 规则说：`temp` is read here but is never assigned anywhere in this program (and is not a link or built-in)

```
       0  op sub dx sx @thisx
       1  op sub dy sy @thisy
       2  op len dist dx dy
>>>>   3  op add id @thisx temp
       4  print "[red]警告:不要试图用发散或者有荷载容量的单位试图偷走这个物品源\n我只要检测到这个物品源消失，你们就死了。(拆掉也算)"
       5  makemarker shapeText id @thisx @thisy true
       6  setmarker flushText id 0 0 0
       7  setmarker fontSize id 2 0 0
       8  wait 0.5
       9  getlink a 0
      10  jump 12 strictEqual a null
      11  end
      12  print "[red]红队物品源消失了?!死吧!!!!!!!!!!!"
      13  message announce 3 @wait
      14  spawnwave 7 101 false
      15  wait 0.1
      16  jump 14 always x false
```

判定:
备注:

### `dc850c1773`

- 出处：`mindustrytop-25680` · (28,31) · micro-processor · 140 条语句
- 处理器自己的链接：`pad1`, `sorter1`, `pad2`
- 被指行：语句序号 **1**
- 规则说：`咕咕着陆台更新器v1.3` is never assigned -- signature only (it shows up in the editor's variable list; print outputs `null`)

```
       0  jump 6 always x false
>>>>   1  print 咕咕着陆台更新器v1.3
       2  print 更新时间2026/4/17
       3  print 用参数控制着陆台接受物品
       4  print 可用分类器来显示当前自动选择的物品
       5  print 0为关闭，1为开启
       6  set E星 0
       7  set 铜 1
       8  set 铅 1
       9  set 沙 0
      10  set 煤 0
      11  set 废料 0
      12  set 钛 1
      13  set 钍 1
      14  set 孢子 0
      15  set 硅 1
      16  set 玻璃 1
      17  set 石墨 1
      18  set 塑钢 1
      19  set 合金 1
      20  set 布 1
      21  set 硫化物 1
      22  set 爆炸混合物 1
      23  set 铍 1
      24  set 钨 1
      25  set 氧化物 1
      26  set 碳化物 1
      27  jump 29 notEqual 铜 0
      28  lookup item a0 0
      29  jump 31 notEqual 铅 0
      30  lookup item a1 1
      31  jump 33 notEqual 沙 0
      ... 下面还有 108 条语句
```

判定:
备注:

### `b6080828a3`

- 出处：`mindustrytop-25680` · (28,31) · micro-processor · 140 条语句
- 处理器自己的链接：`pad1`, `sorter1`, `pad2`
- 被指行：语句序号 **2**
- 规则说：`更新时间2026/4/17` is never assigned -- signature only (it shows up in the editor's variable list; print outputs `null`)

```
       0  jump 6 always x false
       1  print 咕咕着陆台更新器v1.3
>>>>   2  print 更新时间2026/4/17
       3  print 用参数控制着陆台接受物品
       4  print 可用分类器来显示当前自动选择的物品
       5  print 0为关闭，1为开启
       6  set E星 0
       7  set 铜 1
       8  set 铅 1
       9  set 沙 0
      10  set 煤 0
      11  set 废料 0
      12  set 钛 1
      13  set 钍 1
      14  set 孢子 0
      15  set 硅 1
      16  set 玻璃 1
      17  set 石墨 1
      18  set 塑钢 1
      19  set 合金 1
      20  set 布 1
      21  set 硫化物 1
      22  set 爆炸混合物 1
      23  set 铍 1
      24  set 钨 1
      25  set 氧化物 1
      26  set 碳化物 1
      27  jump 29 notEqual 铜 0
      28  lookup item a0 0
      29  jump 31 notEqual 铅 0
      30  lookup item a1 1
      31  jump 33 notEqual 沙 0
      32  lookup item a4 4
      ... 下面还有 107 条语句
```

判定:
备注:

### `d49676d15e`

- 出处：`mindustrytop-25680` · (28,31) · micro-processor · 140 条语句
- 处理器自己的链接：`pad1`, `sorter1`, `pad2`
- 被指行：语句序号 **5**
- 规则说：`0为关闭，1为开启` is never assigned -- signature only (it shows up in the editor's variable list; print outputs `null`)

```
       0  jump 6 always x false
       1  print 咕咕着陆台更新器v1.3
       2  print 更新时间2026/4/17
       3  print 用参数控制着陆台接受物品
       4  print 可用分类器来显示当前自动选择的物品
>>>>   5  print 0为关闭，1为开启
       6  set E星 0
       7  set 铜 1
       8  set 铅 1
       9  set 沙 0
      10  set 煤 0
      11  set 废料 0
      12  set 钛 1
      13  set 钍 1
      14  set 孢子 0
      15  set 硅 1
      16  set 玻璃 1
      17  set 石墨 1
      18  set 塑钢 1
      19  set 合金 1
      20  set 布 1
      21  set 硫化物 1
      22  set 爆炸混合物 1
      23  set 铍 1
      24  set 钨 1
      25  set 氧化物 1
      26  set 碳化物 1
      27  jump 29 notEqual 铜 0
      28  lookup item a0 0
      29  jump 31 notEqual 铅 0
      30  lookup item a1 1
      31  jump 33 notEqual 沙 0
      32  lookup item a4 4
      33  jump 35 notEqual 煤 0
      34  lookup item a5 5
      35  jump 37 notEqual 钛 0
      ... 下面还有 104 条语句
```

判定:
备注:

### `9d53ca0dcb`

- 出处：`mindustrytop-20445` · (53,0) · world-processor · 18 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **17**
- 规则说：`无脑遍历所有单位的智障ai系统` is never assigned -- signature only (it shows up in the editor's variable list; print outputs `null`)

```
       0  setrate 1000
       1  sensor t @this @team
       2  set i 0
       3  fetch unit unit t i null
       4  ubind unit
       5  op add i i 1
       6  fetch unitCount unitC t i null
       7  ulocate building core true @copper outx outy found building
       8  ucontrol pathfind outx outy 0 0 0
       9  sensor rng @unit @range
      10  sensor ty @unit @type
      11  jump 14 equal ty @mace
      12  jump 14 equal ty @crawler
      13  op div rng rng 2
      14  ucontrol within outx outy rng ta 0
      15  ucontrol target outx outy ta 0 0
      16  jump 3 lessThan i unitC
>>>>  17  print 无脑遍历所有单位的智障ai系统
```

判定:
备注:

### `2b8d1ce887`

- 出处：`mindustrytop-20445` · (59,0) · world-processor · 19 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **14**
- 规则说：`炮2` is read here but is never assigned anywhere in this program (and is not a link or built-in)

```
       0  setrate 1000
       1  set i 0
       2  sensor t @this @team
       3  fetch build 炮 t i @ripple
       4  fetch buildCount 炮C t i @ripple
       5  fetch build 炮1 t i @spectre
       6  fetch buildCount 炮1C t i @spectre
       7  fetch build 炮1 t i @spectre
       8  fetch buildCount 炮2C t i @foreshadow
       9  op add i i 1
      10  setprop @cryofluid 炮 41
      11  setprop @plastanium 炮 41
      12  setprop @cryofluid 炮1 41
      13  setprop @thorium 炮1 41
>>>>  14  setprop @cryofluid 炮2 41
      15  setprop @surge-alloy 炮2 41
      16  jump 3 lessThan i 炮C
      17  jump 3 lessThan i 炮1C
      18  jump 3 lessThan i 炮2C
```

判定:
备注:

### `fb00900f01`

- 出处：`mindustrytop-20445` · (59,0) · world-processor · 19 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **15**
- 规则说：`炮2` is read here but is never assigned anywhere in this program (and is not a link or built-in)

```
       0  setrate 1000
       1  set i 0
       2  sensor t @this @team
       3  fetch build 炮 t i @ripple
       4  fetch buildCount 炮C t i @ripple
       5  fetch build 炮1 t i @spectre
       6  fetch buildCount 炮1C t i @spectre
       7  fetch build 炮1 t i @spectre
       8  fetch buildCount 炮2C t i @foreshadow
       9  op add i i 1
      10  setprop @cryofluid 炮 41
      11  setprop @plastanium 炮 41
      12  setprop @cryofluid 炮1 41
      13  setprop @thorium 炮1 41
      14  setprop @cryofluid 炮2 41
>>>>  15  setprop @surge-alloy 炮2 41
      16  jump 3 lessThan i 炮C
      17  jump 3 lessThan i 炮1C
      18  jump 3 lessThan i 炮2C
```

判定:
备注:

## 规则 `link-name-not-bound`

### `51521e193c`

- 出处：`mindustrytop-25774` · (127,114) · micro-processor · 14 条语句
- 处理器自己的链接：`pad1`, `driver1`
- 被指行：语句序号 **0**
- 规则说：`vault1` is shaped like a block link but this processor has no such link (it has: driver1, pad1)

```
>>>>   0  sensor silicon vault1 @silicon
       1  sensor phase-fabric vault1 @phase-fabric
       2  sensor surge-alloy vault1 @surge-alloy
       3  jump 6 greaterThan silicon 70
       4  control config pad1 @silicon 0 0 0
       5  end
       6  jump 9 greaterThan phase-fabric 70
       7  control config pad1 @phase-fabric 0 0 0
       8  end
       9  jump 13 greaterThan surge-alloy 700
      10  control config pad1 @surge-alloy 0 0 0
      11  end
      12  end
      13  control config pad1 0 0 0 0
```

判定:
备注:

### `52b6c38cbf`

- 出处：`mindustrytop-25774` · (127,114) · micro-processor · 14 条语句
- 处理器自己的链接：`pad1`, `driver1`
- 被指行：语句序号 **1**
- 规则说：`vault1` is shaped like a block link but this processor has no such link (it has: driver1, pad1)

```
       0  sensor silicon vault1 @silicon
>>>>   1  sensor phase-fabric vault1 @phase-fabric
       2  sensor surge-alloy vault1 @surge-alloy
       3  jump 6 greaterThan silicon 70
       4  control config pad1 @silicon 0 0 0
       5  end
       6  jump 9 greaterThan phase-fabric 70
       7  control config pad1 @phase-fabric 0 0 0
       8  end
       9  jump 13 greaterThan surge-alloy 700
      10  control config pad1 @surge-alloy 0 0 0
      11  end
      12  end
      13  control config pad1 0 0 0 0
```

判定:
备注:

### `dc3412a6be`

- 出处：`mindustrytop-25774` · (127,114) · micro-processor · 14 条语句
- 处理器自己的链接：`pad1`, `driver1`
- 被指行：语句序号 **2**
- 规则说：`vault1` is shaped like a block link but this processor has no such link (it has: driver1, pad1)

```
       0  sensor silicon vault1 @silicon
       1  sensor phase-fabric vault1 @phase-fabric
>>>>   2  sensor surge-alloy vault1 @surge-alloy
       3  jump 6 greaterThan silicon 70
       4  control config pad1 @silicon 0 0 0
       5  end
       6  jump 9 greaterThan phase-fabric 70
       7  control config pad1 @phase-fabric 0 0 0
       8  end
       9  jump 13 greaterThan surge-alloy 700
      10  control config pad1 @surge-alloy 0 0 0
      11  end
      12  end
      13  control config pad1 0 0 0 0
```

判定:
备注:

### `3c07c964de`

- 出处：`mindustrytop-25559` · (389,444) · world-processor · 56 条语句
- 处理器自己的链接：`router1`, `router2`, `router3`, `router4`, `battery1`, `container1`, `wall1`, `router6`, `router5`, `node1`
- 被指行：语句序号 **18**
- 规则说：`route1` is shaped like a block link but this processor has no such link (it has: battery1, container1, node1, router1, router2, router3, router4, router5, router6, wall1)

```
       0  setrate 1000
       1  sensor t @this @team
       2  op mul ix1 3 @thisx
       3  op mul ix2 7 @thisx
       4  op mul iy1 5 @thisy
       5  op mul iy2 11 @thisy
       6  op mul id1 ix1 iy2
       7  op mul id2 ix2 iy1
       8  sensor wx wall1 @x
       9  sensor wy wall1 @y
      10  op add wx wx 0.5
      11  op sub wy wy 0.5
      12  sensor x1 battery1 @x
      13  sensor y1 battery1 @y
      14  sensor x2 node1 @x
      15  sensor y2 node1 @y
      16  sensor cx container1 @x
      17  sensor cy container1 @y
>>>>  18  sensor rx1 route1 @x
      19  sensor ry1 route1 @y
      20  sensor rx2 router2 @x
      21  sensor ry2 router2 @y
      22  sensor rx3 router3 @x
      23  sensor ry3 router3 @y
      24  sensor rx4 router4 @x
      25  sensor ry4 router4 @y
      26  sensor rx5 router5 @x
      27  sensor ry5 router5 @y
      28  sensor rx6 router6 @x
      29  sensor ry6 router6 @y
      30  makemarker texture id1 wx wy true
      31  makemarker texture id2 wx wy true
      32  setmarker texture id1 0 "core-bastion" 0
      33  setmarker texture id2 0 "reinforced-vault-team" 0
      34  setmarker textureSize id1 5 5 0
      35  setmarker textureSize id2 5 5 0
      36  setmarker drawLayer id1 30.1 6 0
      37  setmarker drawLayer id2 30.2 6 0
      38  setmarker color id1 %c6c6c6 6 0
      39  setmarker color id2 %ffd9ba 6 0
      40  setblock block @battery x1 y1 t 0
      41  setblock block @power-node x2 y2 t 0
      42  setblock block @reinforced-liquid-container cx cy t 0
      43  setblock block @reinforced-liquid-router rx1 ry1 t 0
      44  setblock block @reinforced-liquid-router rx2 ry2 t 0
      45  setblock block @reinforced-liquid-router rx3 ry3 t 0
      46  setblock block @reinforced-liquid-router rx4 ry4 t 0
      47  setblock block @reinforced-liquid-router rx5 ry5 t 0
      48  setblock block @reinforced-liquid-router rx6 ry6 t 0
      49  sensor d wall1 @dead
      50  jump 52 equal d 1
      51  jump 40 always x false
      52  explosion @sharded wx wy 5 5000 true true false true
      53  setmarker remove id1 %9e9e9e 6 0
      54  setmarker remove id2 %9e9e9e 6 0
      55  stop
```

判定:
备注:

### `9d4b1b5e6d`

- 出处：`mindustrytop-25559` · (389,444) · world-processor · 56 条语句
- 处理器自己的链接：`router1`, `router2`, `router3`, `router4`, `battery1`, `container1`, `wall1`, `router6`, `router5`, `node1`
- 被指行：语句序号 **19**
- 规则说：`route1` is shaped like a block link but this processor has no such link (it has: battery1, container1, node1, router1, router2, router3, router4, router5, router6, wall1)

```
       0  setrate 1000
       1  sensor t @this @team
       2  op mul ix1 3 @thisx
       3  op mul ix2 7 @thisx
       4  op mul iy1 5 @thisy
       5  op mul iy2 11 @thisy
       6  op mul id1 ix1 iy2
       7  op mul id2 ix2 iy1
       8  sensor wx wall1 @x
       9  sensor wy wall1 @y
      10  op add wx wx 0.5
      11  op sub wy wy 0.5
      12  sensor x1 battery1 @x
      13  sensor y1 battery1 @y
      14  sensor x2 node1 @x
      15  sensor y2 node1 @y
      16  sensor cx container1 @x
      17  sensor cy container1 @y
      18  sensor rx1 route1 @x
>>>>  19  sensor ry1 route1 @y
      20  sensor rx2 router2 @x
      21  sensor ry2 router2 @y
      22  sensor rx3 router3 @x
      23  sensor ry3 router3 @y
      24  sensor rx4 router4 @x
      25  sensor ry4 router4 @y
      26  sensor rx5 router5 @x
      27  sensor ry5 router5 @y
      28  sensor rx6 router6 @x
      29  sensor ry6 router6 @y
      30  makemarker texture id1 wx wy true
      31  makemarker texture id2 wx wy true
      32  setmarker texture id1 0 "core-bastion" 0
      33  setmarker texture id2 0 "reinforced-vault-team" 0
      34  setmarker textureSize id1 5 5 0
      35  setmarker textureSize id2 5 5 0
      36  setmarker drawLayer id1 30.1 6 0
      37  setmarker drawLayer id2 30.2 6 0
      38  setmarker color id1 %c6c6c6 6 0
      39  setmarker color id2 %ffd9ba 6 0
      40  setblock block @battery x1 y1 t 0
      41  setblock block @power-node x2 y2 t 0
      42  setblock block @reinforced-liquid-container cx cy t 0
      43  setblock block @reinforced-liquid-router rx1 ry1 t 0
      44  setblock block @reinforced-liquid-router rx2 ry2 t 0
      45  setblock block @reinforced-liquid-router rx3 ry3 t 0
      46  setblock block @reinforced-liquid-router rx4 ry4 t 0
      47  setblock block @reinforced-liquid-router rx5 ry5 t 0
      48  setblock block @reinforced-liquid-router rx6 ry6 t 0
      49  sensor d wall1 @dead
      50  jump 52 equal d 1
      51  jump 40 always x false
      52  explosion @sharded wx wy 5 5000 true true false true
      53  setmarker remove id1 %9e9e9e 6 0
      54  setmarker remove id2 %9e9e9e 6 0
      55  stop
```

判定:
备注:

### `0c4f2ecd38`

- 出处：`mindustrytop-25559` · (390,445) · world-processor · 128 条语句
- 处理器自己的链接：`wall1`, `cell1`
- 被指行：语句序号 **126**
- 规则说：`id6` is shaped like a block link but this processor has no such link (it has: cell1, wall1)

```
      ... 上面还有 96 条语句
      96  op mul cxn ojrf cx1
      97  op mul syn ojrf sy1
      98  op add y1 y1 syn
      99  op add x1 x1 cxn
     100  op add y2 y2 syn
     101  op add x2 x2 cxn
     102  op add y3 y3 syn
     103  op add x3 x3 cxn
     104  op add y4 y4 syn
     105  op add x4 x4 cxn
     106  jump 108 lessThan ojrf 1
     107  set re 0
     108  setmarker pos id1 x1 y1 0
     109  setmarker pos id2 x2 y2 0
     110  setmarker pos id3 x4 y4 0
     111  setmarker pos id4 wx wy 0
     112  setmarker pos id5 x3 y3 0
     113  setmarker rotation id1 rot y1 0
     114  setmarker rotation id2 rot y1 0
     115  setmarker rotation id3 rot y1 0
     116  setmarker rotation id4 rot y1 0
     117  setmarker rotation id5 rot y1 0
     118  sensor dead wall1 @dead
     119  jump 121 equal dead 1
     120  jump 32 always x false
     121  setmarker remove id1 0 0 0
     122  setmarker remove id2 0 0 0
     123  setmarker remove id3 0 0 0
     124  setmarker remove id4 0 0 0
     125  setmarker remove id5 0 0 0
>>>> 126  setmarker remove id6 0 0 0
     127  stop
```

判定:
备注:

### `f8c972e368`

- 出处：`mindustrytop-26053` · (60,12) · world-processor · 4 条语句
- 处理器自己的链接：`display1`
- 被指行：语句序号 **2**
- 规则说：`block1` is shaped like a block link but this processor has no such link (it has: display1)

```
       0  draw clear 0 0 0 32 0 0
       1  draw image 10 10 @surge-alloy 20 0 0
>>>>   2  sensor result block1 @surge-alloy
       3  drawflush display1
```

判定:
备注:

### `24f3cccde5`

- 出处：`mindustrytop-26053` · (128,27) · world-processor · 8 条语句
- 处理器自己的链接：`processor1`
- 被指行：语句序号 **5**
- 规则说：`cell2` is shaped like a block link but this processor has no such link (it has: processor1)

```
       0  setrate 50
       1  read 游戏模式 cell2 2
       2  jump 1 notEqual 游戏模式 "经典pvp"
       3  getlink a i
       4  op add i i 1
>>>>   5  jump 1 equal a cell2
       6  setprop @health a 0
       7  select i greaterThanEq i 210 0 i
```

判定:
备注:

### `103586d19e`

- 出处：`mindustrytop-26053` · (65,57) · world-processor · 38 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **37**
- 规则说：`arial1102` is shaped like a block link but this processor has no such link (it has: none)

```
       0  fetch playerCount a t 0 @conveyor
       1  fetch playerCount ooo 2 0 @conveyor
       2  fetch player p t i @conveyor
       3  sensor sx p @shootX
       4  sensor sy p @shootY
       5  sensor sô p @shooting
       6  op sub dx sx @thisx
       7  op sub dy sy @thisy
       8  op len dist dx dy
       9  jump 11 greaterThanEq dist 4
      10  jump 23 equal sô true
      11  op add i i 1
      12  jump 0 lessThan i a
      13  op add t t 1
      14  set i 0
      15  jump 0 lessThan t 2
      16  op mul temp @mapw @thisy
      17  op add id @thisx temp
      18  set t 0
      19  print "更换团队红\n换过去之后不要捣乱，不然给你踢了。"
      20  makemarker shapeText id @thisx @thisy true
      21  setmarker flushText id 0 0 0
      22  end
      23  op add a. a ooo
      24  op div ooo. a. 2.5
      25  jump 27 lessThanEq a 1
      26  jump 31 greaterThanEq a ooo.
      27  print "[red]再换队，黄队就没人了，不要再换了!!!"
      28  message notify 3 @wait
      29  wait 5
      30  end
      31  sensor tim p @team
      32  playsound true @sfx-shootLancer 1 1 0 @thisx @thisy true
      33  effect smokePuff @thisx @thisy 2 %ffaaaa
      34  setprop @team p 2
      35  effect trail @thisx @thisy 9 %ffaaaa
      36  wait 0.5
>>>>  37  print arial1102
```

判定:
备注:

### `0911233925`

- 出处：`mindustrytop-20445` · (15,0) · world-processor · 70 条语句
- 处理器自己的链接：`processor1`, `processor2`
- 被指行：语句序号 **49**
- 规则说：`write1` is shaped like a block link but this processor has no such link (it has: processor1, processor2)

```
      ... 上面还有 19 条语句
      19  read parent0 processor1 "parent[0]"
      20  read parent1 processor1 "parent[1]"
      21  read parent2 processor1 "parent[2]"
      22  read parent3 processor1 "parent[3]"
      23  read parent4 processor1 "parent[4]"
      24  read parent5 processor1 "parent[5]"
      25  op strictEqual root parent0 "newRoot"
      26  jump 48 notEqual parent0 null
      27  jump 48 notEqual parent1 null
      28  jump 48 notEqual parent2 null
      29  jump 48 notEqual parent3 null
      30  jump 48 notEqual parent4 null
      31  jump 48 notEqual parent5 null
      32  print "{0}读取失败：parent为null！"
      33  format type
      34  set isnull 1
      35  jump 39 always x false
      36  print "{0}读取失败：category为null！"
      37  format type
      38  set isnull 1
      39  message notify 3 @wait
      40  sensor x processor1 @x
      41  sensor y processor1 @y
      42  effect lightBlock x y 1 %ff0f09
      43  wait 0.1
      44  effect lightBlock x y 1 %ff0f09
      45  wait 0.1
      46  effect lightBlock x y 1 %ff0f09
      47  jump 69 always x false
      48  sensor tname type @name
>>>>  49  stringmerge write1 tname ".type"
      50  stringmerge write2 tname ".category"
      51  stringmerge write3 tname ".cost"
      52  stringmerge write4 tname ".root"
      53  stringmerge wparent0 tname ".parent[0]"
      54  stringmerge wparent1 tname ".parent[1]"
      55  stringmerge wparent2 tname ".parent[2]"
      56  stringmerge wparent3 tname ".parent[3]"
      57  stringmerge wparent4 tname ".parent[4]"
      58  stringmerge wparent5 tname ".parent[5]"
      59  write type processor2 write1
      60  write category processor2 write2
      61  write cost processor2 write3
      62  write root processor2 write4
      63  write parent0 processor2 wparent0
      64  write parent1 processor2 wparent1
      65  write parent2 processor2 wparent2
      66  write parent3 processor2 wparent3
      67  write parent4 processor2 wparent4
      68  write parent5 processor2 wparent5
      69  jump 3 lessThan GetId length
```

判定:
备注:

### `4d7080a7d4`

- 出处：`mindustrytop-20445` · (15,0) · world-processor · 70 条语句
- 处理器自己的链接：`processor1`, `processor2`
- 被指行：语句序号 **50**
- 规则说：`write2` is shaped like a block link but this processor has no such link (it has: processor1, processor2)

```
      ... 上面还有 20 条语句
      20  read parent1 processor1 "parent[1]"
      21  read parent2 processor1 "parent[2]"
      22  read parent3 processor1 "parent[3]"
      23  read parent4 processor1 "parent[4]"
      24  read parent5 processor1 "parent[5]"
      25  op strictEqual root parent0 "newRoot"
      26  jump 48 notEqual parent0 null
      27  jump 48 notEqual parent1 null
      28  jump 48 notEqual parent2 null
      29  jump 48 notEqual parent3 null
      30  jump 48 notEqual parent4 null
      31  jump 48 notEqual parent5 null
      32  print "{0}读取失败：parent为null！"
      33  format type
      34  set isnull 1
      35  jump 39 always x false
      36  print "{0}读取失败：category为null！"
      37  format type
      38  set isnull 1
      39  message notify 3 @wait
      40  sensor x processor1 @x
      41  sensor y processor1 @y
      42  effect lightBlock x y 1 %ff0f09
      43  wait 0.1
      44  effect lightBlock x y 1 %ff0f09
      45  wait 0.1
      46  effect lightBlock x y 1 %ff0f09
      47  jump 69 always x false
      48  sensor tname type @name
      49  stringmerge write1 tname ".type"
>>>>  50  stringmerge write2 tname ".category"
      51  stringmerge write3 tname ".cost"
      52  stringmerge write4 tname ".root"
      53  stringmerge wparent0 tname ".parent[0]"
      54  stringmerge wparent1 tname ".parent[1]"
      55  stringmerge wparent2 tname ".parent[2]"
      56  stringmerge wparent3 tname ".parent[3]"
      57  stringmerge wparent4 tname ".parent[4]"
      58  stringmerge wparent5 tname ".parent[5]"
      59  write type processor2 write1
      60  write category processor2 write2
      61  write cost processor2 write3
      62  write root processor2 write4
      63  write parent0 processor2 wparent0
      64  write parent1 processor2 wparent1
      65  write parent2 processor2 wparent2
      66  write parent3 processor2 wparent3
      67  write parent4 processor2 wparent4
      68  write parent5 processor2 wparent5
      69  jump 3 lessThan GetId length
```

判定:
备注:

### `1fd172411d`

- 出处：`mindustrytop-20445` · (15,0) · world-processor · 70 条语句
- 处理器自己的链接：`processor1`, `processor2`
- 被指行：语句序号 **51**
- 规则说：`write3` is shaped like a block link but this processor has no such link (it has: processor1, processor2)

```
      ... 上面还有 21 条语句
      21  read parent2 processor1 "parent[2]"
      22  read parent3 processor1 "parent[3]"
      23  read parent4 processor1 "parent[4]"
      24  read parent5 processor1 "parent[5]"
      25  op strictEqual root parent0 "newRoot"
      26  jump 48 notEqual parent0 null
      27  jump 48 notEqual parent1 null
      28  jump 48 notEqual parent2 null
      29  jump 48 notEqual parent3 null
      30  jump 48 notEqual parent4 null
      31  jump 48 notEqual parent5 null
      32  print "{0}读取失败：parent为null！"
      33  format type
      34  set isnull 1
      35  jump 39 always x false
      36  print "{0}读取失败：category为null！"
      37  format type
      38  set isnull 1
      39  message notify 3 @wait
      40  sensor x processor1 @x
      41  sensor y processor1 @y
      42  effect lightBlock x y 1 %ff0f09
      43  wait 0.1
      44  effect lightBlock x y 1 %ff0f09
      45  wait 0.1
      46  effect lightBlock x y 1 %ff0f09
      47  jump 69 always x false
      48  sensor tname type @name
      49  stringmerge write1 tname ".type"
      50  stringmerge write2 tname ".category"
>>>>  51  stringmerge write3 tname ".cost"
      52  stringmerge write4 tname ".root"
      53  stringmerge wparent0 tname ".parent[0]"
      54  stringmerge wparent1 tname ".parent[1]"
      55  stringmerge wparent2 tname ".parent[2]"
      56  stringmerge wparent3 tname ".parent[3]"
      57  stringmerge wparent4 tname ".parent[4]"
      58  stringmerge wparent5 tname ".parent[5]"
      59  write type processor2 write1
      60  write category processor2 write2
      61  write cost processor2 write3
      62  write root processor2 write4
      63  write parent0 processor2 wparent0
      64  write parent1 processor2 wparent1
      65  write parent2 processor2 wparent2
      66  write parent3 processor2 wparent3
      67  write parent4 processor2 wparent4
      68  write parent5 processor2 wparent5
      69  jump 3 lessThan GetId length
```

判定:
备注:

### `7badf1c11d`

- 出处：`mindustrytop-26083` · (95,2) · world-processor · 89 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **88**
- 规则说：`block1` is shaped like a block link but this processor has no such link (it has: none)

```
      ... 上面还有 58 条语句
      58  op add i i 1
      59  jump 55 lessThanEq i 99
      60  set i 0
      61  fetch build a10 队伍 i @differential-generator
      62  setprop @pyratite a10 99
      63  op add i i 1
      64  jump 61 lessThanEq i 99
      65  set i 0
      66  fetch build a11 队伍 i @thorium-reactor
      67  setprop @thorium a11 99
      68  op add i i 1
      69  jump 66 lessThanEq i 99
      70  set i 0
      71  fetch build a12 队伍 i @repair-turret
      72  setprop @cryofluid a12 99
      73  op add i i 1
      74  jump 71 lessThanEq i 99
      75  set i 0
      76  fetch build a13 队伍 i @impact-drill
      77  setprop @ozone a13 99
      78  setprop @water a13 99
      79  op add i i 1
      80  jump 76 lessThanEq i 99
      81  set i 0
      82  fetch build a14 队伍 i @foreshadow
      83  setprop @surge-alloy a14 99
      84  setprop @cryofluid a14 99
      85  op add i i 1
      86  jump 82 lessThanEq i 99
      87  end
>>>>  88  sensor result block1 @foreshadow
```

判定:
备注:

## 规则 `dead-polarity`

### `5d93101d61`

- 出处：`mindustrytop-25774` · (139,142) · micro-processor · 14 条语句
- 处理器自己的链接：`reconstructor1`
- 被指行：语句序号 **1**
- 规则说：`单位存亡` holds @dead (1 = DEAD). Checking `notEqual` continues only while ALIVE; to rebind when dead use `equal`

```
       0  sensor 单位存亡 @unit @dead
>>>>   1  jump 5 notEqual 单位存亡 1
       2  ubind @mono
       3  sensor 单位状态1 @unit @controlled
       4  jump 2 notEqual 单位状态1 0
       5  getlink 兵厂 0
       6  sensor x 兵厂 @x
       7  sensor y 兵厂 @y
       8  jump 11 notEqual x null
       9  set x @thisx
      10  set y @thisy
      11  ucontrol boost 1 0 0 0 0
      12  ucontrol move x y 0 0 0
      13  ucontrol payEnter x y 0 0 0
```

判定:
备注:

### `138400f19e`

- 出处：`mindustrytop-25559` · (351,272) · world-processor · 34 条语句
- 处理器自己的链接：`processor1`, `processor2`, `processor3`, `cell1`, `processor4`, `processor5`, `processor6`, `processor7`, `message1`, `wall1`
- 被指行：语句序号 **20**
- 规则说：`dead` holds @dead (1 = DEAD). Checking `notEqual` continues only while ALIVE; to rebind when dead use `equal`

```
       0  sensor px1 processor1 @x
       1  sensor py1 processor1 @y
       2  sensor px2 processor2 @x
       3  sensor py2 processor2 @y
       4  sensor px3 processor3 @x
       5  sensor py3 processor3 @y
       6  sensor px4 processor4 @x
       7  sensor py4 processor4 @y
       8  sensor px5 processor5 @x
       9  sensor py5 processor5 @y
      10  sensor px6 processor6 @x
      11  sensor py6 processor6 @y
      12  sensor px7 processor7 @x
      13  sensor py7 processor7 @y
      14  sensor cx cell1 @x
      15  sensor cy cell1 @y
      16  sensor mx message1 @x
      17  sensor my message1 @y
      18  sensor dead wall1 @dead
      19  write dead cell1 330
>>>>  20  jump 18 notEqual dead 1
      21  write dead cell1 330
      22  wait 0.2
      23  setblock block @air px1 py1 @derelict 0
      24  setblock block @air px2 py2 @derelict 0
      25  setblock block @air px3 py3 @derelict 0
      26  setblock block @air px4 py4 @derelict 0
      27  setblock block @air px5 py5 @derelict 0
      28  setblock block @air px6 py6 @derelict 0
      29  setblock block @air px7 py7 @derelict 0
      30  setblock block @air cx cy @derelict 0
      31  setblock block @air mx my @derelict 0
      32  setblock block @air @thisx @thisy @derelict 0
      33  stop
```

判定:
备注:

### `04ce031d10`

- 出处：`mindustrytop-25559` · (427,437) · world-processor · 147 条语句
- 处理器自己的链接：`duct1`, `duct2`, `duct3`, `duct4`, `duct5`, `duct6`, `duct7`, `duct8`, `duct9`, `duct10`, `duct11`, `duct12`, `duct13`, `duct14`, `duct15`, `duct16`, `duct17`, `duct18`, `duct19`, `duct20`, `battery1`, `processor1`, `processor2`, `processor3`, `processor4`, `processor5`, `processor6`, `processor7`, `processor8`, `processor9`, `wall1`, `cell1`
- 被指行：语句序号 **130**
- 规则说：`d` holds @dead (1 = DEAD). Checking `notEqual` continues only while ALIVE; to rebind when dead use `equal`

```
      ... 上面还有 100 条语句
     100  sensor px8 processor8 @x
     101  sensor py8 processor8 @y
     102  sensor px9 processor9 @x
     103  sensor py9 processor9 @y
     104  sensor cx cell1 @x
     105  sensor cy cell1 @y
     106  sensor team @this @team
     107  setblock block @duct dx1 dy1 team dr1
     108  setblock block @duct dx2 dy2 team dr2
     109  setblock block @duct dx3 dy3 team dr3
     110  setblock block @duct dx4 dy4 team dr4
     111  setblock block @duct dx5 dy5 team dr5
     112  setblock block @duct dx6 dy6 team dr6
     113  setblock block @duct dx7 dy7 team dr7
     114  setblock block @duct dx8 dy8 team dr8
     115  setblock block @duct dx9 dy9 team dr9
     116  setblock block @duct dx10 dy10 team dr10
     117  setblock block @duct dx11 dy11 team dr11
     118  setblock block @duct dx12 dy12 team dr12
     119  setblock block @duct dx13 dy13 team dr13
     120  setblock block @duct dx14 dy14 team dr14
     121  setblock block @duct dx15 dy15 team dr15
     122  setblock block @duct dx16 dy16 team dr16
     123  setblock block @duct dx17 dy17 team dr17
     124  setblock block @duct dx18 dy18 team dr18
     125  setblock block @duct dx19 dy19 team dr19
     126  setblock block @duct dx20 dy20 team dr20
     127  setblock block @battery bx by team 0
     128  sensor d wall1 @dead
     129  write d cell1 455
>>>> 130  jump 107 notEqual d 1
     131  setmarker remove id1 0 0 0
     132  setmarker remove id2 0 0 0
     133  wait 0.5
     134  setblock block @air px1 py1 @derelict 0
     135  setblock block @air px2 py2 @derelict 0
     136  setblock block @air px3 py3 @derelict 0
     137  setblock block @air px4 py4 @derelict 0
     138  setblock block @air px5 py5 @derelict 0
     139  setblock block @air px6 py6 @derelict 0
     140  setblock block @air px7 py7 @derelict 0
     141  setblock block @air px8 py8 @derelict 0
     142  setblock block @air px9 py9 @derelict 0
     143  setblock block @air cx cy @derelict 0
     144  explosion 0 x y 7 105 true true 1 true
     145  setblock block @air @thisx @thisy @derelict 0
     146  stop
```

判定:
备注:

### `118f77e606`

- 出处：`mindustrytop-25559` · (393,445) · world-processor · 33 条语句
- 处理器自己的链接：`wall1`, `processor1`, `processor2`, `processor3`
- 被指行：语句序号 **7**
- 规则说：`dead` holds @dead (1 = DEAD). Checking `notEqual` continues only while ALIVE; to rebind when dead use `equal`

```
       0  wait 0.5
       1  setrate 1000
       2  sensor wx wall1 @x
       3  sensor wy wall1 @y
       4  op add wx wx 0.5
       5  op sub wy wy 0.5
       6  sensor dead wall1 @dead
>>>>   7  jump 6 notEqual dead 1
       8  wait 0.5
       9  sensor x1 processor1 @x
      10  sensor y1 processor1 @y
      11  sensor x2 processor2 @x
      12  sensor y2 processor2 @y
      13  sensor x3 processor3 @x
      14  sensor y3 processor3 @y
      15  setblock block @air x1 y1 @derelict 0
      16  setblock block @air x2 y2 @derelict 0
      17  setblock block @air x3 y3 @derelict 0
      18  op add x2 x2 1
      19  op add x3 x3 1
      20  setblock block @air x2 y2 @derelict 0
      21  setblock block @air x3 y3 @derelict 0
      22  op add x2 x2 1
      23  op add x3 x3 1
      24  setblock block @air x2 y2 @derelict 0
      25  setblock block @air x3 y3 @derelict 0
      26  op add x2 x2 1
      27  op add x3 x3 1
      28  setblock block @air x2 y2 @derelict 0
      29  setblock block @air x3 y3 @derelict 0
      30  explosion 0 wx wy 5 500 true true false true
      31  setblock block @air @thisx @thisy @derelict 0
      32  stop
```

判定:
备注:

### `c7d89cccea`

- 出处：`mindustrytop-25765` · (5,16) · world-processor · 12 条语句
- 处理器自己的链接：`cell1`, `bastion1`
- 被指行：语句序号 **2**
- 规则说：`D` holds @dead (1 = DEAD). Checking `notEqual` continues only while ALIVE; to rebind when dead use `equal`

```
       0  getlink b 1
       1  sensor D b @dead
>>>>   2  jump 0 notEqual D 1
       3  wait 60
       4  write 270 cell1 1
       5  write 80 cell1 2
       6  wait 0.1
       7  write 1 cell1 0
       8  write 30 cell1 3
       9  wait 0.5
      10  write 0 cell1 0
      11  stop
```

判定:
备注:

### `084dc84adc`

- 出处：`mindustrytop-25765` · (5,17) · world-processor · 12 条语句
- 处理器自己的链接：`cell1`, `bastion1`
- 被指行：语句序号 **2**
- 规则说：`D` holds @dead (1 = DEAD). Checking `notEqual` continues only while ALIVE; to rebind when dead use `equal`

```
       0  getlink b 1
       1  sensor D b @dead
>>>>   2  jump 0 notEqual D 1
       3  wait 120
       4  write 25 cell1 1
       5  write 130 cell1 2
       6  wait 0.1
       7  write 2 cell1 0
       8  write 60 cell1 3
       9  wait 0.5
      10  write 0 cell1 0
      11  stop
```

判定:
备注:

### `c8b85ac89d`

- 出处：`mindustrytop-25872` · (81,33) · logic-processor · 194 条语句
- 处理器自己的链接：`board`
- 被指行：语句序号 **18**
- 规则说：`__ls_ub_d_1` holds @dead (1 = DEAD). Checking `notEqual` continues only while ALIVE; to rebind when dead use `equal`

```
       0  set count 0
       1  op mul __ls_ub_uid @thisx 100000
       2  op add __ls_ub_uid __ls_ub_uid @thisy
       3  op add __ls_ub_uid __ls_ub_uid 1
       4  set __ls_ub_n_1 0
       5  set __ls_ub_p_1 0
       6  set __ls_ub_o_1 0
       7  set __ls_ub_a_1 null
       8  set __ls_ub_s_1 0
       9  __ls_ub_scan_1:
      10  op add __ls_ub_s_1 __ls_ub_s_1 1
      11  jump __ls_stmt_4 greaterThan __ls_ub_s_1 8192
      12  ubind @poly
      13  jump __ls_ub_wrap_1 equal @unit null
      14  jump __ls_ub_mark_1 equal __ls_ub_a_1 null
      15  jump __ls_ub_wrap_1 equal @unit __ls_ub_a_1
      16  jump __ls_ub_keep_1 always x false
      17  __ls_ub_mark_1:
>>>>  18  set __ls_ub_a_1 @unit
      19  __ls_ub_keep_1:
      20  sensor __ls_ub_d_1 @unit @dead
      21  jump __ls_ub_scan_1 notEqual __ls_ub_d_1 0
      22  sensor __ls_ub_f_1 @unit @flag
      23  jump __ls_ub_ours_1 equal __ls_ub_f_1 __ls_ub_uid
      24  jump __ls_ub_scan_1 equal __ls_ub_p_1 0
      25  jump __ls_ub_scan_1 notEqual __ls_ub_f_1 0
      26  sensor __ls_ub_c_1 @unit @controlled
      27  jump __ls_ub_scan_1 notEqual __ls_ub_c_1 0
      28  sensor __ls_ub_f_1 @unit @flag
      29  jump __ls_ub_scan_1 notEqual __ls_ub_f_1 0
      30  jump __ls_ub_scan_1 greaterThanEq __ls_ub_n_1 8
      31  jump __ls_ub_scan_1 lessThanEq __ls_ub_r_1 0
      32  set __ls_ub_h_1 @unit
      33  ucontrol flag __ls_ub_uid 0 0 0 0
      34  end
      35  end
      36  end
      37  end
      38  ubind __ls_ub_h_1
      39  jump __ls_ub_scan_1 equal @unit null
      40  sensor __ls_ub_f_1 @unit @flag
      41  jump __ls_ub_scan_1 notEqual __ls_ub_f_1 __ls_ub_uid
      42  op sub __ls_ub_r_1 __ls_ub_r_1 1
      43  jump __ls_ub_give_1 always x false
      44  __ls_ub_ours_1:
      45  jump __ls_ub_count_1 equal __ls_ub_p_1 0
      46  jump __ls_ub_scan_1 greaterThanEq __ls_ub_n_1 8
      47  jump __ls_ub_give_1 always x false
      48  __ls_ub_count_1:
      ... 下面还有 145 条语句
```

判定:
备注:

### `423960e02f`

- 出处：`mindustrytop-25872` · (81,33) · logic-processor · 194 条语句
- 处理器自己的链接：`board`
- 被指行：语句序号 **64**
- 规则说：`__ls_ub_d_4` holds @dead (1 = DEAD). Checking `notEqual` continues only while ALIVE; to rebind when dead use `equal`

```
      ... 上面还有 34 条语句
      34  end
      35  end
      36  end
      37  end
      38  ubind __ls_ub_h_1
      39  jump __ls_ub_scan_1 equal @unit null
      40  sensor __ls_ub_f_1 @unit @flag
      41  jump __ls_ub_scan_1 notEqual __ls_ub_f_1 __ls_ub_uid
      42  op sub __ls_ub_r_1 __ls_ub_r_1 1
      43  jump __ls_ub_give_1 always x false
      44  __ls_ub_ours_1:
      45  jump __ls_ub_count_1 equal __ls_ub_p_1 0
      46  jump __ls_ub_scan_1 greaterThanEq __ls_ub_n_1 8
      47  jump __ls_ub_give_1 always x false
      48  __ls_ub_count_1:
      49  op add __ls_ub_o_1 __ls_ub_o_1 1
      50  jump __ls_ub_scan_1 always x false
      51  __ls_ub_wrap_1:
      52  jump __ls_stmt_4 notEqual __ls_ub_p_1 0
      53  set __ls_ub_p_1 1
      54  set __ls_ub_n_1 0
      55  set __ls_ub_s_1 0
      56  op sub __ls_ub_r_1 8 __ls_ub_o_1
      57  jump __ls_ub_scan_1 equal @unit null
      58  jump __ls_ub_keep_1 always x false
      59  __ls_ub_give_1:
      60  set unit @unit
      61  op add count count 1
      62  op add __ls_ub_n_1 __ls_ub_n_1 1
      63  jump __ls_ub_scan_1 always x false
>>>>  64  __ls_stmt_4:
      65  op mul __ls_ub_uid @thisx 100000
      66  op add __ls_ub_uid __ls_ub_uid @thisy
      67  op add __ls_ub_uid __ls_ub_uid 1
      68  jump __ls_ub_scan_4 equal __ls_ub_h_4 null
      69  ubind __ls_ub_h_4
      70  jump __ls_ub_lost_4 equal @unit null
      71  sensor __ls_ub_d_4 @unit @dead
      72  jump __ls_ub_lost_4 notEqual __ls_ub_d_4 0
      73  sensor __ls_ub_f_4 @unit @flag
      74  jump __ls_ub_take_4 equal __ls_ub_f_4 __ls_ub_uid
      75  __ls_ub_lost_4:
      76  set __ls_ub_h_4 null
      77  __ls_ub_scan_4:
      78  set __ls_ub_s_4 0
      79  set __ls_ub_a_4 null
      80  __ls_ub_loop_4:
      81  op add __ls_ub_s_4 __ls_ub_s_4 1
      82  jump __ls_ub_fail_4 greaterThan __ls_ub_s_4 8192
      83  ubind @poly
      84  jump __ls_ub_fail_4 equal @unit null
      85  jump __ls_ub_fail_4 equal @unit __ls_ub_a_4
      86  jump __ls_ub_keep_4 notEqual __ls_ub_a_4 null
      87  set __ls_ub_a_4 @unit
      88  __ls_ub_keep_4:
      89  sensor __ls_ub_d_4 @unit @dead
      90  jump __ls_ub_loop_4 notEqual __ls_ub_d_4 0
      91  sensor __ls_ub_f_4 @unit @flag
      92  jump __ls_ub_take_4 equal __ls_ub_f_4 __ls_ub_uid
      93  jump __ls_ub_loop_4 notEqual __ls_ub_f_4 0
      94  sensor __ls_ub_c_4 @unit @controlled
      ... 下面还有 99 条语句
```

判定:
备注:

### `1e36fdc911`

- 出处：`mindustrytop-25872` · (81,33) · logic-processor · 194 条语句
- 处理器自己的链接：`board`
- 被指行：语句序号 **78**
- 规则说：`__ls_ub_d_4` holds @dead (1 = DEAD). Checking `notEqual` continues only while ALIVE; to rebind when dead use `equal`

```
      ... 上面还有 48 条语句
      48  __ls_ub_count_1:
      49  op add __ls_ub_o_1 __ls_ub_o_1 1
      50  jump __ls_ub_scan_1 always x false
      51  __ls_ub_wrap_1:
      52  jump __ls_stmt_4 notEqual __ls_ub_p_1 0
      53  set __ls_ub_p_1 1
      54  set __ls_ub_n_1 0
      55  set __ls_ub_s_1 0
      56  op sub __ls_ub_r_1 8 __ls_ub_o_1
      57  jump __ls_ub_scan_1 equal @unit null
      58  jump __ls_ub_keep_1 always x false
      59  __ls_ub_give_1:
      60  set unit @unit
      61  op add count count 1
      62  op add __ls_ub_n_1 __ls_ub_n_1 1
      63  jump __ls_ub_scan_1 always x false
      64  __ls_stmt_4:
      65  op mul __ls_ub_uid @thisx 100000
      66  op add __ls_ub_uid __ls_ub_uid @thisy
      67  op add __ls_ub_uid __ls_ub_uid 1
      68  jump __ls_ub_scan_4 equal __ls_ub_h_4 null
      69  ubind __ls_ub_h_4
      70  jump __ls_ub_lost_4 equal @unit null
      71  sensor __ls_ub_d_4 @unit @dead
      72  jump __ls_ub_lost_4 notEqual __ls_ub_d_4 0
      73  sensor __ls_ub_f_4 @unit @flag
      74  jump __ls_ub_take_4 equal __ls_ub_f_4 __ls_ub_uid
      75  __ls_ub_lost_4:
      76  set __ls_ub_h_4 null
      77  __ls_ub_scan_4:
>>>>  78  set __ls_ub_s_4 0
      79  set __ls_ub_a_4 null
      80  __ls_ub_loop_4:
      81  op add __ls_ub_s_4 __ls_ub_s_4 1
      82  jump __ls_ub_fail_4 greaterThan __ls_ub_s_4 8192
      83  ubind @poly
      84  jump __ls_ub_fail_4 equal @unit null
      85  jump __ls_ub_fail_4 equal @unit __ls_ub_a_4
      86  jump __ls_ub_keep_4 notEqual __ls_ub_a_4 null
      87  set __ls_ub_a_4 @unit
      88  __ls_ub_keep_4:
      89  sensor __ls_ub_d_4 @unit @dead
      90  jump __ls_ub_loop_4 notEqual __ls_ub_d_4 0
      91  sensor __ls_ub_f_4 @unit @flag
      92  jump __ls_ub_take_4 equal __ls_ub_f_4 __ls_ub_uid
      93  jump __ls_ub_loop_4 notEqual __ls_ub_f_4 0
      94  sensor __ls_ub_c_4 @unit @controlled
      95  jump __ls_ub_loop_4 notEqual __ls_ub_c_4 0
      96  sensor __ls_ub_f_4 @unit @flag
      97  jump __ls_ub_loop_4 notEqual __ls_ub_f_4 0
      98  set __ls_ub_h_4 @unit
      99  ucontrol flag __ls_ub_uid 0 0 0 0
     100  end
     101  end
     102  end
     103  end
     104  ubind __ls_ub_h_4
     105  jump __ls_ub_loop_4 equal @unit null
     106  sensor __ls_ub_f_4 @unit @flag
     107  jump __ls_ub_loop_4 notEqual __ls_ub_f_4 __ls_ub_uid
     108  __ls_ub_take_4:
      ... 下面还有 85 条语句
```

判定:
备注:

### `8fd023e58f`

- 出处：`mindustrytop-20445` · (4,0) · world-processor · 66 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **38**
- 规则说：`coreDead` holds @dead (1 = DEAD). Checking `notEqual` continues only while ALIVE; to rebind when dead use `equal`

```
      ... 上面还有 8 条语句
       8  jump 34 always x false
       9  set block @laser-drill
      10  op add return @counter 1
      11  jump 34 always x false
      12  set block @blast-drill
      13  op add return @counter 1
      14  jump 34 always x false
      15  set block @cultivator
      16  op add return @counter 1
      17  jump 34 always x false
      18  set block @cliff-crusher
      19  op add return @counter 1
      20  jump 34 always x false
      21  set block @plasma-bore
      22  op add return @counter 1
      23  jump 34 always x false
      24  set block @large-plasma-bore
      25  op add return @counter 1
      26  jump 34 always x false
      27  set block @impact-drill
      28  op add return @counter 1
      29  jump 34 always x false
      30  set block @eruption-drill
      31  op add return @counter 1
      32  jump 34 always x false
      33  jump 3 always x false
      34  fetch buildCount i team 0 block
      35  jump 54 lessThan @time nextTime
      36  jump 39 equal eCore 1
      37  sensor coreDead core @dead
>>>>  38  jump 53 notEqual coreDead 1
      39  set i 0
      40  fetch core core team i @conveyor
      41  jump 52 equal core null
      42  sensor coreType core @type
      43  jump 48 equal coreType @core-bastion
      44  jump 48 equal coreType @core-citadel
      45  jump 48 equal coreType @core-acropolis
      46  set eCore 0
      47  jump 53 always x false
      48  op add i i 1
      49  set corePre core
      50  set eCore 1
      51  jump 40 always x false
      52  set core corePre
      53  op add nextTime @time 1000
      54  set i 0
      55  fetch build build team i block
      56  jump 65 strictEqual build null
      57  sensor item build @firstItem
      58  sensor taken build item
      59  setprop item build 0
      60  sensor haves core item
      61  op add itemThen taken haves
      62  setprop item core itemThen
      63  op add i i 1
      64  jump 55 always x false
      65  set @counter return
```

判定:
备注:

### `97ad0501f2`

- 出处：`mindustrytop-20445` · (0,24) · world-processor · 5 条语句
- 处理器自己的链接：`nucleus1`, `shard1`, `shard2`, `shard3`
- 被指行：语句序号 **1**
- 规则说：`dead` holds @dead (1 = DEAD). Checking `notEqual` continues only while ALIVE; to rebind when dead use `equal`

```
       0  sensor dead nucleus1 @dead
>>>>   1  jump 0 notEqual dead 1
       2  setprop @health shard1 0
       3  setprop @health shard2 0
       4  setprop @health shard3 0
```

判定:
备注:

## 规则 `status-name-needs-at`

### `e7bd3633fc`

- 出处：`mindustrytop-25559` · (590,11) · world-processor · 6 条语句
- 处理器自己的链接：`message1`
- 被指行：语句序号 **5**
- 规则说：`unmoving` is the name of a status effect, not a variable: a content constant needs the @ prefix (`@unmoving`, and some builds expose it as `@status_unmoving` -- check the variable list in the editor), so as written this reads null and the instruction does nothing

```
       0  setrate 1000
       1  ubind @stell
       2  sensor shooting @unit @shooting
       3  jump 5 equal shooting 1
       4  end
>>>>   5  status false unmoving @unit 0.1
```

判定:
备注:

### `57068e2780`

- 出处：`mindustrytop-25559` · (591,11) · world-processor · 6 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **5**
- 规则说：`unmoving` is the name of a status effect, not a variable: a content constant needs the @ prefix (`@unmoving`, and some builds expose it as `@status_unmoving` -- check the variable list in the editor), so as written this reads null and the instruction does nothing

```
       0  setrate 1000
       1  ubind @locus
       2  sensor shooting @unit @shooting
       3  jump 5 equal shooting 1
       4  end
>>>>   5  status false unmoving @unit 0.1
```

判定:
备注:

### `7721928b85`

- 出处：`mindustrytop-25559` · (592,11) · world-processor · 6 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **5**
- 规则说：`unmoving` is the name of a status effect, not a variable: a content constant needs the @ prefix (`@unmoving`, and some builds expose it as `@status_unmoving` -- check the variable list in the editor), so as written this reads null and the instruction does nothing

```
       0  setrate 1000
       1  ubind @precept
       2  sensor shooting @unit @shooting
       3  jump 5 equal shooting 1
       4  end
>>>>   5  status false unmoving @unit 0.1
```

判定:
备注:

### `aed45859a6`

- 出处：`mindustrytop-24936` · (7,72) · world-processor · 44 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **23**
- 规则说：`unmoving` is the name of a status effect, not a variable: a content constant needs the @ prefix (`@unmoving`, and some builds expose it as `@status_unmoving` -- check the variable list in the editor), so as written this reads null and the instruction does nothing

```
       0  fetch unit 建筑机 1 0 @incite
       1  fetch unit 第二者 1 1 @incite
       2  setprop @health 第二者 0
       3  fetch unit 建筑机1 3 0 @incite
       4  sensor 控制 建筑机1 @controlled
       5  fetch unitCount 数量1 1 0 @incite
       6  fetch unitCount 数量2 3 0 @incite
       7  op add 数量 数量1 数量2
       8  jump 15 notEqual 数量 0
       9  op add 次数 次数 1
      10  wait 0.5
      11  jump 14 lessThanEq 次数 10
      12  spawn @incite 10 60 0 1 伪亚龙 true
      13  wait 3
      14  end
      15  set 次数 0
      16  jump 20 equal 控制 @ctrlPlayer
      17  setprop @team 建筑机1 1
      18  setprop @flag 建筑机1 0
      19  setprop @flag 建筑机 0
      20  sensor 名字 建筑机 @name
      21  sensor 长度 名字 @size
      22  set 作者 "[white]击败"
>>>>  23  status false unmoving 建筑机 3
      24  status false disarmed 建筑机 3
      25  jump 38 equal 名字 作者
      26  op sub 长度 长度 1
      27  read 检测 名字 长度
      28  jump 31 equal 检测 53
      29  jump 26 greaterThanEq 长度 1
      30  jump 0 always 检测 93
      31  op sub 长度 长度 1
      32  read ID2 名字 长度
      33  op sub 长度 长度 1
      34  read ID1 名字 长度
      35  jump 37 notEqual ID1 118
      36  jump 38 equal ID2 66
      37  end
      38  status true unmoving 建筑机 10
      39  status true disarmed 建筑机 10
      40  setprop @team 建筑机 3
      41  setblock block @item-source 12 67 1 0
      42  setblock block @item-source 12 66 3 0
      43  wait 0.2
```

判定:
备注:

### `91ad42e765`

- 出处：`mindustrytop-24936` · (7,72) · world-processor · 44 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **24**
- 规则说：`disarmed` is the name of a status effect, not a variable: a content constant needs the @ prefix (`@disarmed`, and some builds expose it as `@status_disarmed` -- check the variable list in the editor), so as written this reads null and the instruction does nothing

```
       0  fetch unit 建筑机 1 0 @incite
       1  fetch unit 第二者 1 1 @incite
       2  setprop @health 第二者 0
       3  fetch unit 建筑机1 3 0 @incite
       4  sensor 控制 建筑机1 @controlled
       5  fetch unitCount 数量1 1 0 @incite
       6  fetch unitCount 数量2 3 0 @incite
       7  op add 数量 数量1 数量2
       8  jump 15 notEqual 数量 0
       9  op add 次数 次数 1
      10  wait 0.5
      11  jump 14 lessThanEq 次数 10
      12  spawn @incite 10 60 0 1 伪亚龙 true
      13  wait 3
      14  end
      15  set 次数 0
      16  jump 20 equal 控制 @ctrlPlayer
      17  setprop @team 建筑机1 1
      18  setprop @flag 建筑机1 0
      19  setprop @flag 建筑机 0
      20  sensor 名字 建筑机 @name
      21  sensor 长度 名字 @size
      22  set 作者 "[white]击败"
      23  status false unmoving 建筑机 3
>>>>  24  status false disarmed 建筑机 3
      25  jump 38 equal 名字 作者
      26  op sub 长度 长度 1
      27  read 检测 名字 长度
      28  jump 31 equal 检测 53
      29  jump 26 greaterThanEq 长度 1
      30  jump 0 always 检测 93
      31  op sub 长度 长度 1
      32  read ID2 名字 长度
      33  op sub 长度 长度 1
      34  read ID1 名字 长度
      35  jump 37 notEqual ID1 118
      36  jump 38 equal ID2 66
      37  end
      38  status true unmoving 建筑机 10
      39  status true disarmed 建筑机 10
      40  setprop @team 建筑机 3
      41  setblock block @item-source 12 67 1 0
      42  setblock block @item-source 12 66 3 0
      43  wait 0.2
```

判定:
备注:

### `5555e12354`

- 出处：`mindustrytop-24936` · (7,72) · world-processor · 44 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **38**
- 规则说：`unmoving` is the name of a status effect, not a variable: a content constant needs the @ prefix (`@unmoving`, and some builds expose it as `@status_unmoving` -- check the variable list in the editor), so as written this reads null and the instruction does nothing

```
       0  fetch unit 建筑机 1 0 @incite
       1  fetch unit 第二者 1 1 @incite
       2  setprop @health 第二者 0
       3  fetch unit 建筑机1 3 0 @incite
       4  sensor 控制 建筑机1 @controlled
       5  fetch unitCount 数量1 1 0 @incite
       6  fetch unitCount 数量2 3 0 @incite
       7  op add 数量 数量1 数量2
       8  jump 15 notEqual 数量 0
       9  op add 次数 次数 1
      10  wait 0.5
      11  jump 14 lessThanEq 次数 10
      12  spawn @incite 10 60 0 1 伪亚龙 true
      13  wait 3
      14  end
      15  set 次数 0
      16  jump 20 equal 控制 @ctrlPlayer
      17  setprop @team 建筑机1 1
      18  setprop @flag 建筑机1 0
      19  setprop @flag 建筑机 0
      20  sensor 名字 建筑机 @name
      21  sensor 长度 名字 @size
      22  set 作者 "[white]击败"
      23  status false unmoving 建筑机 3
      24  status false disarmed 建筑机 3
      25  jump 38 equal 名字 作者
      26  op sub 长度 长度 1
      27  read 检测 名字 长度
      28  jump 31 equal 检测 53
      29  jump 26 greaterThanEq 长度 1
      30  jump 0 always 检测 93
      31  op sub 长度 长度 1
      32  read ID2 名字 长度
      33  op sub 长度 长度 1
      34  read ID1 名字 长度
      35  jump 37 notEqual ID1 118
      36  jump 38 equal ID2 66
      37  end
>>>>  38  status true unmoving 建筑机 10
      39  status true disarmed 建筑机 10
      40  setprop @team 建筑机 3
      41  setblock block @item-source 12 67 1 0
      42  setblock block @item-source 12 66 3 0
      43  wait 0.2
```

判定:
备注:

### `29bdf305cd`

- 出处：`mindustrytop-25736` · (300,1) · world-processor · 69 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **13**
- 规则说：`fast` is the name of a status effect, not a variable: a content constant needs the @ prefix (`@fast`, and some builds expose it as `@status_fast` -- check the variable list in the editor), so as written this reads null and the instruction does nothing

```
       0  setrate 1000
       1  sensor team @this @team
       2  fetch unit unit team s @conveyor
       3  fetch unitCount unitCount team s @conveyor
       4  ubind unit
       5  sensor range @unit @range
       6  op sub range-1 range 1
       7  op sub range-5 range 5
       8  sensor x @unit @x
       9  sensor y @unit @y
      10  query circle unit 2 294 14.5 14 10
      11  read 结果 @queries 0
      12  jump 29 equal 结果 0
>>>>  13  status false fast 结果 1e5
      14  op add 随机 随机 1
      15  op mod 随机 随机 4
      16  jump 20 strictEqual 随机 1
      17  jump 23 strictEqual 随机 2
      18  jump 26 strictEqual 随机 3
      19  jump 14 always 随机 3
      20  setprop @x 结果 295
      21  setprop @y 结果 90
      22  jump 59 always x false
      23  setprop @x 结果 295
      24  setprop @y 结果 330
      25  jump 59 always x false
      26  setprop @x 结果 295
      27  setprop @y 结果 570
      28  jump 59 always x false
      29  ulocate building turret true @copper tx ty found building
      30  ulocate building generator true @copper fx fy found building
      31  ulocate building core true @copper hx hy found core
      32  uradar enemy attacker ground health 0 0 enemy
      33  ucontrol within tx ty range-1 炮到 0
      34  ucontrol within fx fy range-1 电到 0
      35  ucontrol within hx hy range-1 Acore 0
      36  jump 46 equal Acore 1
      37  ucontrol autoPathfind 0 0 0 0 0
      38  sensor Core-team core @team
      39  query circle building Core-team x y range-5 10
      40  read Ablock @queries 0
      41  jump 63 strictEqual 炮到 1
      42  jump 65 equal enemy 1
      43  jump 67 strictEqual 电到 1
      ... 下面还有 25 条语句
```

判定:
备注:

### `02f0e5fe28`

- 出处：`mindustrytop-14962` · (201,2) · world-processor · 36 条语句
- 处理器自己的链接：`bastion1`
- 被指行：语句序号 **30**
- 规则说：`sapped` is the name of a status effect, not a variable: a content constant needs the @ prefix (`@sapped`, and some builds expose it as `@status_sapped` -- check the variable list in the editor), so as written this reads null and the instruction does nothing

```
       0  fetch coreCount 核心 @green 索引 @conveyor
       1  jump 4 greaterThan 核心 8
       2  jump 20 lessThan 核心 5
       3  end
       4  print "[yellow]绿队核心数量大于8获得了成就"
       5  print "\n [red]扩张"
       6  message notify 3
       7  print "获得buff守卫者"
       8  message notify 3
       9  fetch unitCount unitc @green unitindex @conveyor
      10  fetch unit unit @green unitindex @conveyor
      11  jump 15 greaterThanEq unitindex unitc
      12  op add unitindex unitindex 1
      13  status false boss unit 10
      14  jump 9 always unitindex unitc
      15  set unitindex 0
      16  jump 9 always 核心 8
      17  jump 9 lessThan 核心 8
      18  fetch coreCount 核心 @green 索引 @conveyor
      19  jump 34 always 核心 5
      20  print "[yellow]绿队核心数量小于5获得了成就"
      21  print "\n [red]失落的帝国"
      22  message notify 3
      23  print "获得buff弱化"
      24  message notify 3
      25  set unitindex 0
      26  fetch unitCount unitc @green unitindex @conveyor
      27  fetch unit unit @green unitindex @conveyor
      28  jump 25 greaterThanEq unitindex unitc
      29  op add unitindex unitindex 1
>>>>  30  status false sapped unit 10
      31  jump 34 greaterThanEq 核心 5
      32  fetch coreCount 核心 @green 索引 @conveyor
      33  jump 26 always 核心 5
      34  status true sapped unit 10
      35  status true boss unit 10
```

判定:
备注:

### `77e3da07bb`

- 出处：`mindustrytop-14962` · (201,2) · world-processor · 36 条语句
- 处理器自己的链接：`bastion1`
- 被指行：语句序号 **34**
- 规则说：`sapped` is the name of a status effect, not a variable: a content constant needs the @ prefix (`@sapped`, and some builds expose it as `@status_sapped` -- check the variable list in the editor), so as written this reads null and the instruction does nothing

```
       0  fetch coreCount 核心 @green 索引 @conveyor
       1  jump 4 greaterThan 核心 8
       2  jump 20 lessThan 核心 5
       3  end
       4  print "[yellow]绿队核心数量大于8获得了成就"
       5  print "\n [red]扩张"
       6  message notify 3
       7  print "获得buff守卫者"
       8  message notify 3
       9  fetch unitCount unitc @green unitindex @conveyor
      10  fetch unit unit @green unitindex @conveyor
      11  jump 15 greaterThanEq unitindex unitc
      12  op add unitindex unitindex 1
      13  status false boss unit 10
      14  jump 9 always unitindex unitc
      15  set unitindex 0
      16  jump 9 always 核心 8
      17  jump 9 lessThan 核心 8
      18  fetch coreCount 核心 @green 索引 @conveyor
      19  jump 34 always 核心 5
      20  print "[yellow]绿队核心数量小于5获得了成就"
      21  print "\n [red]失落的帝国"
      22  message notify 3
      23  print "获得buff弱化"
      24  message notify 3
      25  set unitindex 0
      26  fetch unitCount unitc @green unitindex @conveyor
      27  fetch unit unit @green unitindex @conveyor
      28  jump 25 greaterThanEq unitindex unitc
      29  op add unitindex unitindex 1
      30  status false sapped unit 10
      31  jump 34 greaterThanEq 核心 5
      32  fetch coreCount 核心 @green 索引 @conveyor
      33  jump 26 always 核心 5
>>>>  34  status true sapped unit 10
      35  status true boss unit 10
```

判定:
备注:

### `bc7fb32ea0`

- 出处：`mindustrytop-14962` · (201,3) · world-processor · 36 条语句
- 处理器自己的链接：`bastion1`
- 被指行：语句序号 **30**
- 规则说：`sapped` is the name of a status effect, not a variable: a content constant needs the @ prefix (`@sapped`, and some builds expose it as `@status_sapped` -- check the variable list in the editor), so as written this reads null and the instruction does nothing

```
       0  fetch coreCount 核心 @blue 索引 @conveyor
       1  jump 4 greaterThan 核心 8
       2  jump 20 lessThan 核心 5
       3  end
       4  print "[yellow]蓝队核心数量大于8获得了成就"
       5  print "\n [red]扩张"
       6  message notify 3
       7  print "获得buff守卫者"
       8  message notify 3
       9  fetch unitCount unitc @blue unitindex @conveyor
      10  fetch unit unit @blue unitindex @conveyor
      11  jump 15 greaterThanEq unitindex unitc
      12  op add unitindex unitindex 1
      13  status false boss unit 10
      14  jump 9 always unitindex unitc
      15  set unitindex 0
      16  jump 9 always unitindex unitc
      17  jump 9 lessThan 核心 8
      18  fetch coreCount 核心 @blue 索引 @conveyor
      19  jump 34 always 核心 5
      20  print "[yellow]蓝队核心数量小于5获得了成就"
      21  print "\n [red]失落的帝国"
      22  message notify 3
      23  print "获得buff弱化"
      24  message notify 3
      25  set unitindex 0
      26  fetch unitCount unitc @blue unitindex @conveyor
      27  fetch unit unit @blue unitindex @conveyor
      28  jump 25 greaterThanEq unitindex unitc
      29  op add unitindex unitindex 1
>>>>  30  status false sapped unit 10
      31  jump 34 greaterThanEq 核心 5
      32  fetch coreCount 核心 @blue 索引 @conveyor
      33  jump 26 always 核心 5
      34  status true sapped unit 10
      35  status true boss unit 10
```

判定:
备注:

### `c1b6ecd5e0`

- 出处：`mindustrytop-20445` · (27,2) · world-processor · 53 条语句
- 处理器自己的链接：`sorter1`, `switch1`, `message1`
- 被指行：语句序号 **36**
- 规则说：`invincible` is the name of a status effect, not a variable: a content constant needs the @ prefix (`@invincible`, and some builds expose it as `@status_invincible` -- check the variable list in the editor), so as written this reads null and the instruction does nothing

```
       0  sensor t @this @team
       1  set buyX 32
       2  set buyY 3
       3  sensor cfg sorter1 @config
       4  jump 39 equal cfg null
       5  sensor cfgid cfg @id
       6  op mul ctr cfgid 2
       7  op add cfgid cfgid 20
       8  jump 39 greaterThan cfgid 24
       9  lookup unit unit cfgid
      10  print "单位购买点\n消耗硅以购买单位\n当前选择单位：:{0}:\n单位价格：{1}硅"
      11  format unit
      12  op add @counter ctr 14
      13  jump 23 always x false
      14  set coin 45
      15  jump 23 always x false
      16  set coin 205
      17  jump 23 always x false
      18  set coin 455
      19  jump 23 always x false
      20  set coin 1200
      21  jump 23 always x false
      22  set coin 4800
      23  format coin
      24  printflush message1
      25  sensor en switch1 @enabled
      26  jump 1 notEqual en 1
      27  fetch core core t 0 @conveyor
      28  jump 1 equal core null
      29  sensor si core @silicon
      30  fetch unitCount res t 0 unit
      31  jump 49 equal res 30
      32  jump 44 lessThan si coin
      33  op sub si si coin
      34  setprop @silicon core si
      35  spawn unit buyX buyY 90 t unite
>>>>  36  status false invincible unite 3
      37  control enabled switch1 0 0 0 0
      38  end
      39  sensor x sorter1 @x
      40  sensor y sorter1 @y
      41  effect warn x y 2 %ffaaff
      42  control config sorter1 @copper 0 0 0
      43  end
      44  sensor x1 switch1 @x
      45  sensor y1 switch1 @y
      46  effect cross x1 y1 2 %ffaaff
      47  control enabled switch1 0 0 0 0
      48  end
      49  sensor x1 switch1 @x
      50  sensor y1 switch1 @y
      51  effect warn x1 y1 2 %ffaaff
      52  control enabled switch1 0 0 0 0
```

判定:
备注:

## 规则 `jump-to-jump-chain`

### `755f2435d4`

- 出处：`mindustrytop-25774` · (6,493) · world-processor · 23 条语句
- 处理器自己的链接：`reconstructor1`, `reconstructor2`
- 被指行：语句序号 **18**
- 规则说：this jump is unconditional and lands on another unconditional jump (L21), so that hop is executed for nothing

```
       0  setrate 1000
       1  getlink building.reconstructor-1 0
       2  getlink building.reconstructor-2 1
       3  fetch unit unit.mono @crux 0 @mono
       4  jump 22 strictEqual unit.mono null
       5  getflag reconstructor.destroyed "reconstructor-1.destroyed"
       6  jump 11 equal reconstructor.destroyed false
       7  setprop @graphite unit.mono 0
       8  status true @status-fast unit.mono 2147483647
       9  status true @status-invincible unit.mono 2147483647
      10  stop
      11  status false @status-fast unit.mono 2147483647
      12  status false @status-invincible unit.mono 2147483647
      13  sensor mono.graphite unit.mono @graphite
      14  ubind unit.mono
      15  jump 19 greaterThan mono.graphite 0
      16  ucontrol move 161 369 0 0 0
      17  ucontrol itemTake building.reconstructor-2 @graphite 20 0 0
>>>>  18  jump 21 always x false
      19  ucontrol move 125 424 0 0 0
      20  ucontrol itemDrop building.reconstructor-1 20 0 0 0
      21  jump 5 always x false
      22  end
```

判定:
备注:

### `dfd46fd8cd`

- 出处：`mindustrytop-25774` · (7,493) · world-processor · 23 条语句
- 处理器自己的链接：`reconstructor1`, `reconstructor2`
- 被指行：语句序号 **18**
- 规则说：this jump is unconditional and lands on another unconditional jump (L21), so that hop is executed for nothing

```
       0  setrate 1000
       1  getlink building.reconstructor-1 0
       2  getlink building.reconstructor-2 1
       3  fetch unit unit.mono @crux 1 @mono
       4  jump 22 strictEqual unit.mono null
       5  getflag reconstructor.destroyed "reconstructor-2.destroyed"
       6  jump 11 equal reconstructor.destroyed false
       7  setprop @metaglass unit.mono 0
       8  status true @status-fast unit.mono 2147483647
       9  status true @status-invincible unit.mono 2147483647
      10  stop
      11  status false @status-fast unit.mono 2147483647
      12  status false @status-invincible unit.mono 2147483647
      13  sensor mono.graphite unit.mono @metaglass
      14  ubind unit.mono
      15  jump 19 greaterThan mono.graphite 0
      16  ucontrol move 121 423 0 0 0
      17  ucontrol itemTake building.reconstructor-2 @metaglass 20 0 0
>>>>  18  jump 21 always x false
      19  ucontrol move 165 369 0 0 0
      20  ucontrol itemDrop building.reconstructor-1 20 0 0 0
      21  jump 5 always x false
      22  end
```

判定:
备注:

### `906c52587e`

- 出处：`mindustrytop-24936` · (0,118) · world-processor · 403 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **205**
- 规则说：this jump is unconditional and lands on another unconditional jump (L209), so that hop is executed for nothing

```
      ... 上面还有 175 条语句
     175  jump 353 always 随机 4
     176  status false @status-unmoving BOSS 4
     177  spawn @mono DX DY 90 2 信标 true
     178  setprop @flag 信标 1005
     179  wait 3.8
     180  jump 353 always 随机 4
     181  fetch unitCount 存活单位数量 1 0 0
     182  op mul 存活倍率 存活单位数量 0.6
     183  op sub 人数倍率 存活倍率 0.2
     184  op mul 护盾 人数倍率 300
     185  wait 1
     186  spawn @quad X Y 90 2 信标 true
     187  setprop @flag 信标 1006
     188  setprop @shield 信标 护盾
     189  setprop @speed 信标 0
     190  wait 1
     191  jump 353 always 随机 4
     192  status false @status-unmoving BOSS 4
     193  getflag 三阶段 "三阶段"
     194  jump 206 notEqual 三阶段 1
     195  status false @status-unmoving BOSS 5
     196  spawn @mono X Y 90 2 信标 true
     197  setprop @flag 信标 1007
     198  wait 2.5
     199  spawn @mono X Y 90 2 信标 true
     200  setprop @flag 信标 1007
     201  wait 2.5
     202  spawn @mono X Y 90 2 信标 true
     203  setprop @flag 信标 1007
     204  wait 2.5
>>>> 205  jump 209 always x false
     206  spawn @mono X Y 90 2 信标 true
     207  setprop @flag 信标 1007
     208  wait 3.8
     209  jump 353 always 随机 4
     210  jump 216 greaterThanEq 切换形态 1
     211  status false @status-unmoving BOSS 2.5
     212  spawn @mono DX DY 90 2 信标 true
     213  setprop @flag 信标 1008
     214  wait 2.4
     215  jump 220 equal 切换形态 0
     216  status false @status-unmoving BOSS 3.6
     217  spawn @mono DX DY 90 2 信标 true
     218  setprop @flag 信标 1008
     219  wait 3.5
     220  jump 353 always 随机 4
     221  sensor DX 随机玩家 @x
     222  sensor DY 随机玩家 @y
     223  op rand 随机X 40 30
     224  op rand 随机Y 40 30
     225  op sub 位移X 随机X 20
     226  op add 发X 位移X DX
     227  op sub 位移Y 随机Y 20
     228  op add 发Y 位移Y DY
     229  spawn @mono 发X 发Y 90 2 信标 true
     230  getflag 二阶段 "二阶段"
     231  getflag 三阶段 "三阶段"
     232  jump 235 equal 三阶段 1
     233  jump 239 equal 二阶段 1
     234  jump 237 always x false
     235  op rand 随机正负 2 30
      ... 下面还有 167 条语句
```

判定:
备注:

### `e3e61db9b9`

- 出处：`mindustrytop-25736` · (294,3) · world-processor · 18 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **13**
- 规则说：this jump is unconditional and lands on another unconditional jump (L17), so that hop is executed for nothing

```
       0  setrate 500
       1  op add m m 1
       2  op mod m m 254
       3  lookup block j m
       4  set i 0
       5  fetch build a 215 i j
       6  jump 0 strictEqual a null
       7  op add i i 1
       8  sensor x a @x
       9  sensor y a @y
      10  getblock floor 地面 x y
      11  jump 14 equal 地面 @darksand
      12  jump 14 equal 地面 @darksand-water
>>>>  13  jump 17 always x false
      14  setblock block @air x y @derelict 0
      15  sensor s a @size
      16  effect breakBlock x y s %ffaaff
      17  jump 5 always x false
```

判定:
备注:

### `1cddd38d3b`

- 出处：`mindustrytop-25736` · (295,3) · world-processor · 18 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **13**
- 规则说：this jump is unconditional and lands on another unconditional jump (L17), so that hop is executed for nothing

```
       0  setrate 500
       1  op add m m 1
       2  op mod m m 254
       3  lookup block j m
       4  set i 0
       5  fetch build a 3 i j
       6  jump 0 strictEqual a null
       7  op add i i 1
       8  sensor x a @x
       9  sensor y a @y
      10  getblock floor 地面 x y
      11  jump 14 equal 地面 @darksand
      12  jump 14 equal 地面 @darksand-water
>>>>  13  jump 17 always x false
      14  setblock block @air x y @derelict 0
      15  sensor s a @size
      16  effect breakBlock x y s %ffaaff
      17  jump 5 always x false
```

判定:
备注:

### `2d6b64c1e0`

- 出处：`mindustrytop-25736` · (296,3) · world-processor · 18 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **13**
- 规则说：this jump is unconditional and lands on another unconditional jump (L17), so that hop is executed for nothing

```
       0  setrate 500
       1  op add m m 1
       2  op mod m m 254
       3  lookup block j m
       4  set i 0
       5  fetch build a 5 i j
       6  jump 0 strictEqual a null
       7  op add i i 1
       8  sensor x a @x
       9  sensor y a @y
      10  getblock floor 地面 x y
      11  jump 14 equal 地面 @darksand
      12  jump 14 equal 地面 @darksand-water
>>>>  13  jump 17 always x false
      14  setblock block @air x y @derelict 0
      15  sensor s a @size
      16  effect breakBlock x y s %ffaaff
      17  jump 5 always x false
```

判定:
备注:

### `fb838e64cd`

- 出处：`mindustrytop-14962` · (82,0) · world-processor · 18 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **12**
- 规则说：this jump is unconditional and lands on another unconditional jump (L3), so that hop is executed for nothing

```
       0  set 队伍 5
       1  print 负责清空没有弹药的炮塔
       2  setrate 1
       3  jump 5 always x false
       4  set p 0
       5  fetch buildCount p1 队伍 p @duo
       6  fetch build p2 队伍 p @duo
       7  jump 4 greaterThan p p1
       8  op add p p 1
       9  sensor dy p2 @ammo
      10  jump 13 equal dy 0
      11  jump 17 equal dy null
>>>>  12  jump 3 always tiam 200
      13  sensor x p2 @x
      14  sensor y p2 @y
      15  explosion @crux x y 1 251 true true false
      16  end
      17  set dy 1
```

判定:
备注:

### `ebf09e2260`

- 出处：`mindustrytop-14962` · (83,0) · world-processor · 19 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **13**
- 规则说：this jump is unconditional and lands on another unconditional jump (L3), so that hop is executed for nothing

```
       0  set 队伍 5
       1  print 负责清空没有弹药的炮塔
       2  setrate 1
       3  jump 5 always x false
       4  set p 0
       5  fetch buildCount p1 队伍 p @fuse
       6  fetch build p2 队伍 p @fuse
       7  jump 4 greaterThan p p1
       8  op add p p 1
       9  wait 0.25
      10  sensor dy p2 @ammo
      11  jump 14 lessThanEq dy 0
      12  jump 18 equal dy null
>>>>  13  jump 3 always tiam 200
      14  sensor x p2 @x
      15  sensor y p2 @y
      16  explosion @crux x y 1 1981 true true false
      17  end
      18  set dy 1
```

判定:
备注:

### `352a0f1979`

- 出处：`mindustrytop-14962` · (84,0) · world-processor · 19 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **13**
- 规则说：this jump is unconditional and lands on another unconditional jump (L3), so that hop is executed for nothing

```
       0  set 队伍 5
       1  print 负责清空没有弹药的炮塔
       2  setrate 1
       3  jump 5 always x false
       4  set p 0
       5  fetch buildCount p1 队伍 p @afflict
       6  fetch build p2 队伍 p @afflict
       7  jump 4 greaterThan p p1
       8  op add p p 1
       9  wait 0.25
      10  sensor dy p2 @ammo
      11  jump 14 lessThanEq dy 0
      12  jump 18 equal dy null
>>>>  13  jump 3 always tiam 200
      14  sensor x p2 @x
      15  sensor y p2 @y
      16  explosion @crux x y 1 3520 true true false
      17  end
      18  set dy 1
```

判定:
备注:

### `ff6724686f`

- 出处：`mindustrytop-26079` · (243,244) · world-processor · 484 条语句
- 处理器自己的链接：`cell1`
- 被指行：语句序号 **462**
- 规则说：this jump is unconditional and lands on another unconditional jump (L481), so that hop is executed for nothing

```
      ... 上面还有 432 条语句
     432  jump 436 always x false
     433  op add cX:515:8 cursorX:8:4 originX:4:4
     434  op add cY:516:8 cursorY:9:4 originY:5:4
     435  setblock block @snow-pine cX:515:8 cY:516:8 @sharded 0
     436  set &fbiome:225:0 null
     437  set @counter &rbiome:225:0
     438  set &rbiome:225:0 440
     439  jump 252 always x false
     440  op add cursorX:8:4 cursorX:8:4 1
     441  op sub &t0:update:212:0 goalPosX:6:4 originX:4:4
     442  jump 445 lessThan cursorX:8:4 &t0:update:212:0
     443  set cursorX:8:4 0
     444  op add cursorY:9:4 cursorY:9:4 1
     445  set &fupdate:212:0 null
     446  set @counter &rupdate:212:0
     447  read &t0:mainLoop:38:0 cell:2:4 0
     448  op equal &t1:mainLoop:38:0 &t0:mainLoop:38:0 1
     449  read &t2:mainLoop:38:0 cell:2:4 5
     450  op equal &t3:mainLoop:38:0 &t2:mainLoop:38:0 0
     451  op land &t4:mainLoop:38:0 &t1:mainLoop:38:0 &t3:mainLoop:38:0
     452  jump 481 equal &t4:mainLoop:38:0 0
     453  set &rreceiveTask:24:0 455
     454  jump 13 always x false
     455  op sub width:44:16 goalPosX:6:4 originX:4:4
     456  op sub height:45:16 goalPosY:7:4 originY:5:4
     457  op lessThanEq &t5:mainLoop:38:0 width:44:16 0
     458  op lessThanEq &t6:mainLoop:38:0 height:45:16 0
     459  op or &t7:mainLoop:38:0 &t5:mainLoop:38:0 &t6:mainLoop:38:0
     460  jump 463 equal &t7:mainLoop:38:0 0
     461  write 1 cell:2:4 5
>>>> 462  jump 481 always x false
     463  set cursorX:8:4 0
     464  set cursorY:9:4 0
     465  jump 474 greaterThanEq cursorY:9:4 height:45:16
     466  set cursorX:8:4 0
     467  jump 472 greaterThanEq cursorX:8:4 width:44:16
     468  set &rsetAir:544:0 470
     469  jump 32 always x false
     470  op add cursorX:8:4 cursorX:8:4 1
     471  jump 467 always x false
     472  op add cursorY:9:4 cursorY:9:4 1
     473  jump 465 always x false
     474  set cursorX:8:4 0
     475  set cursorY:9:4 0
     476  jump 480 greaterThanEq cursorY:9:4 height:45:16
     477  set &rupdate:212:0 479
     478  jump 438 always x false
     479  jump 476 always x false
     480  write 1 cell:2:4 5
     481  jump 447 always x false
     482  set &fmainLoop:38:0 null
     483  set @counter &rmainLoop:38:0
```

判定:
备注:

## 规则 `constant-null-guard`

### `76f7f6fa4c`

- 出处：`mindustrytop-25774` · (143,138) · micro-processor · 51 条语句
- 处理器自己的链接：`mixer2`, `unloader1`, `mixer1`, `reactor1`, `reactor2`, `factory1`, `reconstructor1`, `reconstructor2`
- 被指行：语句序号 **9**
- 规则说：`colour` is never assigned, so this comparison is constant: an unset variable is 0 and `null` reads as 0, so only `===` tells null from 0 (a constant branch is often a signature)

```
       0  sensor r mixer1 @titanium
       1  jump 10 lessThan r 5
       2  sensor r mixer2 @titanium
       3  jump 10 lessThan r 5
       4  sensor r reactor2 @thorium
       5  jump 13 lessThan r 30
       6  sensor r reactor1 @blast-compound
       7  jump 16 lessThan r 10
       8  control enabled unloader1 0 0 0 0
>>>>   9  jump 18 equal colour ender
      10  control enabled unloader1 1 0 0 0
      11  control config unloader1 @titanium 0 0 0
      12  jump 18 equal colour ender
      13  control enabled unloader1 1 0 0 0
      14  control config unloader1 @thorium 0 0 0
      15  jump 18 equal colour ender
      16  control enabled unloader1 1 0 0 0
      17  control config unloader1 @blast-compound 0 0 0
      18  sensor rb reactor2 @blast-compound
      19  op lessThanEq k rb 9
      20  jump -1 notEqual r 0
      21  sensor r mixer1 @titanium
      22  jump 25 lessThanEq r 9
      23  control config sorter1 null 0 0 0
      24  jump 26 equal colour ender
      25  control config sorter1 @titanium 0 0 0
      26  sensor 电入 reactor1 @powerNetIn
      27  sensor 电出 reactor1 @powerNetOut
      28  op sub 电 电入 电出
      29  op greaterThan k 电 3000
      30  control enabled reconstructor1 k 0 0 0
      31  control enabled reconstructor2 k 0 0 0
      32  sensor 电量 reactor1 @powerNetStored
      33  jump 40 greaterThanEq 电量 20000
      34  jump 38 equal kk 0
      35  jump 37 equal 电量 0
      36  end
      37  set kk 0
      38  control enabled reactor1 0 0 0 0
      39  end
      40  sensor s reactor1 @blast-compound
      41  jump 43 equal kk 1
      42  jump 49 greaterThanEq s 9
      43  sensor 爆 reactor1 @blast-compound
      44  jump 46 equal 爆 0
      45  end
      46  set kk 0
      47  control enabled reactor1 0 0 0 0
      48  end
      49  control enabled reactor1 1 0 0 0
      50  set kk 1
```

判定:
备注:

### `041776057b`

- 出处：`mindustrytop-25774` · (143,138) · micro-processor · 51 条语句
- 处理器自己的链接：`mixer2`, `unloader1`, `mixer1`, `reactor1`, `reactor2`, `factory1`, `reconstructor1`, `reconstructor2`
- 被指行：语句序号 **12**
- 规则说：`colour` is never assigned, so this comparison is constant: an unset variable is 0 and `null` reads as 0, so only `===` tells null from 0 (a constant branch is often a signature)

```
       0  sensor r mixer1 @titanium
       1  jump 10 lessThan r 5
       2  sensor r mixer2 @titanium
       3  jump 10 lessThan r 5
       4  sensor r reactor2 @thorium
       5  jump 13 lessThan r 30
       6  sensor r reactor1 @blast-compound
       7  jump 16 lessThan r 10
       8  control enabled unloader1 0 0 0 0
       9  jump 18 equal colour ender
      10  control enabled unloader1 1 0 0 0
      11  control config unloader1 @titanium 0 0 0
>>>>  12  jump 18 equal colour ender
      13  control enabled unloader1 1 0 0 0
      14  control config unloader1 @thorium 0 0 0
      15  jump 18 equal colour ender
      16  control enabled unloader1 1 0 0 0
      17  control config unloader1 @blast-compound 0 0 0
      18  sensor rb reactor2 @blast-compound
      19  op lessThanEq k rb 9
      20  jump -1 notEqual r 0
      21  sensor r mixer1 @titanium
      22  jump 25 lessThanEq r 9
      23  control config sorter1 null 0 0 0
      24  jump 26 equal colour ender
      25  control config sorter1 @titanium 0 0 0
      26  sensor 电入 reactor1 @powerNetIn
      27  sensor 电出 reactor1 @powerNetOut
      28  op sub 电 电入 电出
      29  op greaterThan k 电 3000
      30  control enabled reconstructor1 k 0 0 0
      31  control enabled reconstructor2 k 0 0 0
      32  sensor 电量 reactor1 @powerNetStored
      33  jump 40 greaterThanEq 电量 20000
      34  jump 38 equal kk 0
      35  jump 37 equal 电量 0
      36  end
      37  set kk 0
      38  control enabled reactor1 0 0 0 0
      39  end
      40  sensor s reactor1 @blast-compound
      41  jump 43 equal kk 1
      42  jump 49 greaterThanEq s 9
      43  sensor 爆 reactor1 @blast-compound
      44  jump 46 equal 爆 0
      45  end
      46  set kk 0
      47  control enabled reactor1 0 0 0 0
      48  end
      49  control enabled reactor1 1 0 0 0
      50  set kk 1
```

判定:
备注:

### `3ed5cd7b66`

- 出处：`mindustrytop-25680` · (177,140) · micro-processor · 31 条语句
- 处理器自己的链接：`reactor1`, `generator1`, `unloader1`, `conveyor1`, `reconstructor1`, `nucleus1`, `crucible1`, `generator2`
- 被指行：语句序号 **30**
- 规则说：`colour` is never assigned, so this comparison is constant: an unset variable is 0 and `null` reads as 0, so only `===` tells null from 0 (a constant branch is often a signature)

```
       0  sensor r reactor1 @cryofluid
       1  op greaterThan k r 12
       2  control enabled reactor1 k 0 0 0
       3  sensor r generator2 @thorium
       4  jump 8 greaterThan r 6
       5  control enabled unloader1 1 0 0 0
       6  control config unloader1 @thorium 0 0 0
       7  end
       8  sensor r generator1 @pyratite
       9  jump 13 greaterThanEq r 9
      10  control enabled unloader1 1 0 0 0
      11  control config unloader1 @pyratite 0 0 0
      12  end
      13  sensor r reactor1 @thorium
      14  jump 18 greaterThanEq r 30
      15  control enabled unloader1 1 0 0 0
      16  control config unloader1 @thorium 0 0 0
      17  end
      18  sensor r reconstructor1 @graphite
      19  jump 23 greaterThanEq r 80
      20  control enabled unloader1 1 0 0 0
      21  control config unloader1 @graphite 0 0 0
      22  end
      23  sensor r reconstructor1 @silicon
      24  jump 28 greaterThanEq r 80
      25  control enabled unloader1 1 0 0 0
      26  control config unloader1 @silicon 0 0 0
      27  end
      28  control enabled unloader1 0 0 0 0
      29  end
>>>>  30  jump -1 equal colour ender
```

判定:
备注:

### `5161f3da21`

- 出处：`mindustrytop-25680` · (178,140) · micro-processor · 42 条语句
- 处理器自己的链接：`reactor1`, `sorter1`, `mixer1`, `factory1`, `factory2`, `conveyor1`, `mixer2`, `nucleus1`, `factory3`
- 被指行：语句序号 **5**
- 规则说：`colour` is never assigned, so this comparison is constant: an unset variable is 0 and `null` reads as 0, so only `===` tells null from 0 (a constant branch is often a signature)

```
       0  sensor r nucleus1 @pyratite
       1  jump 7 notEqual r 0
       2  sensor r reactor1 @blast-compound
       3  jump 6 greaterThanEq r 10
       4  control config sorter1 null 0 0 0
>>>>   5  jump 7 equal colour ender
       6  control config sorter1 @blast-compound 0 0 0
       7  sensor rb reactor1 @blast-compound
       8  op lessThanEq k rb 9
       9  control enabled mixer2 k 0 0 0
      10  jump -1 notEqual r 0
      11  sensor r mixer1 @titanium
      12  jump 15 lessThanEq r 9
      13  control config sorter1 null 0 0 0
      14  jump 16 equal colour ender
      15  control config sorter1 @titanium 0 0 0
      16  sensor 电入 reactor1 @powerNetIn
      17  sensor 电出 reactor1 @powerNetOut
      18  op sub 电 电入 电出
      19  op greaterThan k 电 3000
      20  control enabled factory1 k 0 0 0
      21  control enabled factory2 k 0 0 0
      22  control enabled factory3 k 0 0 0
      23  sensor 电量 reactor1 @powerNetStored
      24  jump 31 greaterThanEq 电量 5000
      25  jump 29 equal kk 0
      26  jump 28 equal 电量 0
      27  end
      28  set kk 0
      29  control enabled reactor1 0 0 0 0
      30  end
      31  sensor s reactor1 @blast-compound
      32  jump 34 equal kk 1
      33  jump 40 greaterThanEq s 9
      34  sensor 爆 reactor1 @blast-compound
      35  jump 37 equal 爆 0
      36  end
      37  set kk 0
      38  control enabled reactor1 0 0 0 0
      39  end
      40  control enabled reactor1 1 0 0 0
      41  set kk 1
```

判定:
备注:

## 规则 `printflush-clears-buffer`

### `269f513151`

- 出处：`mindustrytop-25774` · (125,137) · logic-processor · 141 条语句
- 处理器自己的链接：`message1`, `pad1`, `pad2`, `pad3`, `pad4`, `pad5`, `pad6`, `pad7`, `pad8`, `pad9`, `pad10`, `pad11`, `pad12`, `pad13`, `pad14`, `pad15`
- 被指行：语句序号 **24**
- 规则说：`Notification` is never assigned, so this `printflush` has no valid message block -- and that is NOT a no-op: PrintFlushI clears the print buffer unconditionally (LExecutor.java:1178), so everything queued by `print` is DISCARDED here. A deliberate way to empty the buffer; it also parks the name in the editor's variable list

```
       0  jump 36 notEqual core null
       1  print "显示模式(0或1，分类强迫症或矩形强迫症)，自己调来看"
       2  set display.mode 0
       3  print "优先级（权重）设置，范围是0~∞，1为正常优先级"
       4  set copper 0.5
       5  set lead 0.5
       6  set metaglass 1
       7  set graphite 1
       8  set sand 0
       9  set coal 0
      10  set titanium 2
      11  set thorium 2
      12  set scrap 0
      13  set silicon 3
      14  set plastanium 0.8
      15  set phase-fabric 1.6
      16  set surge-alloy 1.8
      17  set spore-pod 0
      18  set blast-compound 0.01
      19  set pyratite 0.01
      20  set beryllium 0
      21  set tungsten 0
      22  set oxide 0
      23  set carbide 0
>>>>  24  printflush Notification
      25  print "找不到核心，确认你已生产任意可控制单位"
      26  set unit.i 0
      27  lookup unit uty unit.i
      28  ubind uty
      29  op add unit.i unit.i 1
      30  jump 32 notEqual @unit null
      31  jump 27 lessThan unit.i 52
      32  ulocate building core false @copper corex corey f core
      33  ucontrol unbind 0 0 0 0 0
      34  printflush message1
      35  end
      36  print "-*-[gray]调和着陆控制逻辑v4.5[white]-*-"
      37  print "\n——按核心资源缺口智能加权分配着陆数量"
      38  set item.i 0
      39  lookup item item item.i
      40  sensor item.amount core item
      41  lookup block UsedAscell item.i
      42  sensor UsedAscell UsedAscell @name
      43  write item.amount @this UsedAscell
      44  op max item.max item.max item.amount
      45  op add item.i item.i 1
      46  jump 39 lessThan item.i 20
      47  set item.i 0
      48  set sum 0
      49  lookup item item item.i
      50  sensor item.name item @name
      51  read weight @this item.name
      52  lookup block UsedAscell item.i
      53  sensor UsedAscell UsedAscell @name
      54  read item.amount @this UsedAscell
      ... 下面还有 86 条语句
```

判定:
备注:

