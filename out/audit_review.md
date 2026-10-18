# 逐条审计（133 条，8 条规则）

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
| `unary-op-extra-operand` | 34 | 0 |
| `version-gate` | 34 | 0 |
| `undefined-var-is-not-automatically-an-error` | 26 | 0 |
| `link-name-not-bound` | 13 | 0 |
| `dead-polarity` | 11 | 0 |
| `jump-to-jump-chain` | 10 | 0 |
| `constant-null-guard` | 4 | 0 |
| `printflush-clears-buffer` | 1 | 0 |

## 规则 `unary-op-extra-operand`

### `a5928f1c49`

- 出处：`mindustrytop-25774` · (125,137) · logic-processor · 141 条语句
- 处理器自己的链接：`message1`, `pad1`, `pad2`, `pad3`, `pad4`, `pad5`, `pad6`, `pad7`, `pad8`, `pad9`, `pad10`, `pad11`, `pad12`, `pad13`, `pad14`, `pad15`
- 被指行：语句序号 **71**
- 规则说：`op sqrt` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
      ... 上面还有 41 条语句
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
>>>>  71  op sqrt endl.set n.pad 1
      72  op idiv endl.set endl.set 1
      73  jump 138 strictEqual n.pad 0
      74  op div pad.volum sum @links
      75  op mul total.transportation 20 n.pad
      76  op rand pad.instruct pad.volum n.pad
      77  print "\n*{1}总运力~={0}/s\n\n"
      78  format total.transportation
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
      ... 下面还有 39 条语句
```

判定:
备注:

### `7ded839bf8`

- 出处：`mindustrytop-25774` · (125,137) · logic-processor · 141 条语句
- 处理器自己的链接：`message1`, `pad1`, `pad2`, `pad3`, `pad4`, `pad5`, `pad6`, `pad7`, `pad8`, `pad9`, `pad10`, `pad11`, `pad12`, `pad13`, `pad14`, `pad15`
- 被指行：语句序号 **76**
- 规则说：`op rand` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
      ... 上面还有 46 条语句
      46  jump 39 lessThan item.i 20
      47  set item.i 0
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
>>>>  76  op rand pad.instruct pad.volum n.pad
      77  print "\n*{1}总运力~={0}/s\n\n"
      78  format total.transportation
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
      ... 下面还有 34 条语句
```

判定:
备注:

### `049fa3e9e6`

- 出处：`mindustrytop-25774` · (4,497) · world-processor · 45 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **4**
- 规则说：`op cos` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
       0  setrate 1000
       1  jump 21 equal state.spawned true
       2  set temp.i 0
       3  set temp.j 0
>>>>   4  op cos cos.num temp.i b
       5  op sin sin.num temp.i b
       6  op mul temp.x cos.num 32.5
       7  op add temp.x temp.x 252
       8  op mul temp.y sin.num 32.5
       9  op add temp.y temp.y 259
      10  op add temp.flag temp.i 1
      11  spawn @antumbra temp.x temp.y temp.i @crux unit.antumbra false
      12  setprop @blast-compound unit.antumbra 180
      13  setprop @flag unit.antumbra temp.flag
      14  setprop @shield unit.antumbra 1000
      15  status false @status-overdrive unit.antumbra 2147483647
      16  status false @status-overclock unit.antumbra 2147483647
      17  op add temp.i temp.i 40
      18  jump 4 lessThan temp.i 360
      19  set state.spawned true
      20  end
      21  set temp.i 0
      22  fetch unitCount antumbra.count @crux 0 @antumbra
      23  fetch unit temp.antumbra @crux temp.i @antumbra
      24  sensor temp.flag temp.antumbra @flag
      25  jump 40 equal temp.flag 0
      26  ubind temp.antumbra
      27  op sub temp.flag temp.flag 1
      28  op add temp.flag temp.flag temp.j
      29  op cos cos.num temp.flag b
      30  op sin sin.num temp.flag b
      31  op mul temp.x cos.num 32.5
      32  op add temp.x temp.x 252
      33  op mul temp.y sin.num 32.5
      34  op add temp.y temp.y 259
      35  ucontrol targetp null false 0 0 0
      36  ucontrol move temp.x temp.y 0 0 0
      37  uradar enemy any any distance 0 1 antumbra.target
      38  jump 40 strictEqual antumbra.target null
      39  ucontrol targetp antumbra.target true 0 0 0
      40  op add temp.i temp.i 1
      41  jump 23 lessThan temp.i antumbra.count
      42  op add temp.j temp.j 0.02
      43  op mod temp.j temp.j 360
      44  end
```

判定:
备注:

### `27e6407c75`

- 出处：`mindustrytop-25773` · (314,228) · world-processor · 102 条语句
- 处理器自己的链接：`arc1`, `switch1`
- 被指行：语句序号 **24**
- 规则说：`op floor` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
       0  setrate 100
       1  jump 6 notEqual arc1 null
       2  op add x @thisx 1
       3  set y @thisy
       4  setblock block @arc x y @sharded 0
       5  jump 0 always x false
       6  jump 11 notEqual switch1 null
       7  op add x @thisx 2
       8  set y @thisy
       9  setblock block @switch x y @sharded 0
      10  jump 0 always x false
      11  op add x @thisx 1
      12  op add y @thisy 1
      13  set floor @air
      14  sensor controlled arc1 @controlled
      15  jump 0 notEqual controlled @ctrlPlayer
      16  sensor e switch1 @enabled
      17  jump 38 equal e true
      18  sensor shooting arc1 @shooting
      19  jump 0 equal shooting false
      20  sensor x arc1 @shootX
      21  op add x x 0.5
      22  sensor y arc1 @shootY
      23  op add y y 0.5
>>>>  24  op floor fx x b
      25  op floor fy y b
      26  jump 36 lessThan fx 318
      27  jump 36 greaterThan fx 593
      28  op add c fx fy
      29  jump 36 lessThan c 530
      30  op sub d fx fy
      31  jump 36 lessThan d 31
      32  getblock building build fx fy
      33  jump 36 strictEqual build null
      34  explosion @sharded fx fy 2 0 false false false
      35  setblock block floor fx fy @derelict 0
      36  wait 0.01
      37  end
      38  sensor shooting arc1 @shooting
      39  jump 46 equal shooting true
      40  set sx -1
      41  set sy -1
      42  set angle -1
      43  set nx -1
      44  set ny -1
      45  end
      46  jump 52 notEqual sx -1
      47  sensor x arc1 @shootX
      48  op add sx x 0.5
      49  sensor y arc1 @shootY
      50  op add sy y 0.5
      51  end
      52  jump 68 notEqual angle -1
      53  sensor x arc1 @shootX
      54  op add x x 0.5
      ... 下面还有 47 条语句
```

判定:
备注:

### `a531463af8`

- 出处：`mindustrytop-25773` · (314,228) · world-processor · 102 条语句
- 处理器自己的链接：`arc1`, `switch1`
- 被指行：语句序号 **25**
- 规则说：`op floor` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
       0  setrate 100
       1  jump 6 notEqual arc1 null
       2  op add x @thisx 1
       3  set y @thisy
       4  setblock block @arc x y @sharded 0
       5  jump 0 always x false
       6  jump 11 notEqual switch1 null
       7  op add x @thisx 2
       8  set y @thisy
       9  setblock block @switch x y @sharded 0
      10  jump 0 always x false
      11  op add x @thisx 1
      12  op add y @thisy 1
      13  set floor @air
      14  sensor controlled arc1 @controlled
      15  jump 0 notEqual controlled @ctrlPlayer
      16  sensor e switch1 @enabled
      17  jump 38 equal e true
      18  sensor shooting arc1 @shooting
      19  jump 0 equal shooting false
      20  sensor x arc1 @shootX
      21  op add x x 0.5
      22  sensor y arc1 @shootY
      23  op add y y 0.5
      24  op floor fx x b
>>>>  25  op floor fy y b
      26  jump 36 lessThan fx 318
      27  jump 36 greaterThan fx 593
      28  op add c fx fy
      29  jump 36 lessThan c 530
      30  op sub d fx fy
      31  jump 36 lessThan d 31
      32  getblock building build fx fy
      33  jump 36 strictEqual build null
      34  explosion @sharded fx fy 2 0 false false false
      35  setblock block floor fx fy @derelict 0
      36  wait 0.01
      37  end
      38  sensor shooting arc1 @shooting
      39  jump 46 equal shooting true
      40  set sx -1
      41  set sy -1
      42  set angle -1
      43  set nx -1
      44  set ny -1
      45  end
      46  jump 52 notEqual sx -1
      47  sensor x arc1 @shootX
      48  op add sx x 0.5
      49  sensor y arc1 @shootY
      50  op add sy y 0.5
      51  end
      52  jump 68 notEqual angle -1
      53  sensor x arc1 @shootX
      54  op add x x 0.5
      55  sensor y arc1 @shootY
      ... 下面还有 46 条语句
```

判定:
备注:

### `ab48903397`

- 出处：`mindustrytop-25773` · (314,228) · world-processor · 102 条语句
- 处理器自己的链接：`arc1`, `switch1`
- 被指行：语句序号 **65**
- 规则说：`op cos` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
      ... 上面还有 35 条语句
      35  setblock block floor fx fy @derelict 0
      36  wait 0.01
      37  end
      38  sensor shooting arc1 @shooting
      39  jump 46 equal shooting true
      40  set sx -1
      41  set sy -1
      42  set angle -1
      43  set nx -1
      44  set ny -1
      45  end
      46  jump 52 notEqual sx -1
      47  sensor x arc1 @shootX
      48  op add sx x 0.5
      49  sensor y arc1 @shootY
      50  op add sy y 0.5
      51  end
      52  jump 68 notEqual angle -1
      53  sensor x arc1 @shootX
      54  op add x x 0.5
      55  sensor y arc1 @shootY
      56  op add y y 0.5
      57  op sub dx x sx
      58  op sub dy y sy
      59  op len len dx dy
      60  jump 67 lessThan len 3
      61  op angle angle dx dy
      62  op add angle angle 45
      63  op idiv angle angle 90
      64  op mul angle angle 90
>>>>  65  op cos x+ angle 90
      66  op sin y+ angle 90
      67  end
      68  jump 72 notEqual nx -1
      69  set nx sx
      70  set ny sy
      71  end
      72  op floor fx nx b
      73  op floor fy ny b
      74  jump 84 lessThan fx 318
      75  jump 84 greaterThan fx 593
      76  op add c fx fy
      77  jump 84 lessThan c 530
      78  op sub d fx fy
      79  jump 84 lessThan d 31
      80  getblock building build fx fy
      81  jump 84 strictEqual build null
      82  explosion @sharded fx fy 2 0 false false false
      83  setblock block floor fx fy @derelict 0
      84  wait 0.01
      85  sensor x arc1 @shootX
      86  op add x x 0.5
      87  sensor y arc1 @shootY
      88  op add y y 0.5
      89  op sub dx x sx
      90  op sub dy y sy
      91  op sub dnx nx sx
      92  op sub dny ny sy
      93  op abs dx+ dx b
      94  op abs dy+ dy b
      95  op abs dnx+ dnx b
      ... 下面还有 6 条语句
```

判定:
备注:

### `750afe1843`

- 出处：`mindustrytop-26075` · (5,10) · world-processor · 28 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **11**
- 规则说：`op round` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
       0  getflag 运行 "阶段4"
       1  jump 0 equal 运行 false
       2  set 开始波次 90
       3  set 总波次 90
       4  print "[red]阶段 4\n[white]波次:{0}/{1}"
       5  op sub 当前波次 @waveNumber 开始波次
       6  format 当前波次
       7  format 总波次
       8  op add 结束波次 开始波次 总波次
       9  jump 15 greaterThanEq @waveNumber 结束波次
      10  print "\n剩余时间:{0}秒"
>>>>  11  op round 剩余时间 @waveTime 1
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

### `92bb89a546`

- 出处：`mindustrytop-26075` · (5,11) · world-processor · 30 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **11**
- 规则说：`op round` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
       0  getflag 运行 "阶段3"
       1  jump 0 equal 运行 false
       2  set 开始波次 35
       3  set 总波次 55
       4  print "[orange]阶段 3\n[white]波次:{0}/{1}"
       5  op sub 当前波次 @waveNumber 开始波次
       6  format 当前波次
       7  format 总波次
       8  op add 结束波次 开始波次 总波次
       9  jump 15 greaterThanEq @waveNumber 结束波次
      10  print "\n剩余时间:{0}秒"
>>>>  11  op round 剩余时间 @waveTime 1
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

### `e63e516348`

- 出处：`mindustrytop-26075` · (5,12) · world-processor · 26 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **11**
- 规则说：`op round` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
       0  getflag 运行 "阶段2"
       1  jump 0 equal 运行 false
       2  set 开始波次 10
       3  set 总波次 25
       4  print "[yellow]阶段 2\n[white]波次:{0}/{1}"
       5  op sub 当前波次 @waveNumber 开始波次
       6  format 当前波次
       7  format 总波次
       8  op add 结束波次 开始波次 总波次
       9  jump 15 greaterThanEq @waveNumber 结束波次
      10  print "\n剩余时间:{0}秒"
>>>>  11  op round 剩余时间 @waveTime 1
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

### `a4e46ced25`

- 出处：`mindustrytop-25559` · (350,269) · world-processor · 109 条语句
- 处理器自己的链接：`wall1`, `duct1`, `cell1`
- 被指行：语句序号 **47**
- 规则说：`op cos` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
      ... 上面还有 17 条语句
      17  makemarker texture id1 0 0 true
      18  makemarker texture id2 0 0 true
      19  makemarker texture id3 0 0 true
      20  makemarker texture id4 0 0 true
      21  makemarker texture id5 0 0 true
      22  makemarker texture id6 0 0 true
      23  setmarker texture id1 0 "smite-blade-l-outline" 0
      24  setmarker texture id2 0 "smite-blade-r-outline" 0
      25  setmarker texture id3 0 "build-tower" 0
      26  setmarker texture id4 0 "titan-barrel-outline" 0
      27  setmarker texture id5 0 "smite-back-l-outline" 0
      28  setmarker texture id6 0 "smite-back-r-outline" 0
      29  setmarker textureSize id1 -2.75 6 0
      30  setmarker textureSize id2 2.75 6 0
      31  setmarker textureSize id3 5 5 0
      32  setmarker textureSize id4 1.75 4 0
      33  setmarker textureSize id5 -5 5 0
      34  setmarker textureSize id6 5 5 0
      35  setmarker drawLayer id1 50.2 0 0
      36  setmarker drawLayer id2 50.2 0 0
      37  setmarker drawLayer id3 50.0 0 0
      38  setmarker drawLayer id4 50.3 0 0
      39  setmarker drawLayer id5 50.1 0 0
      40  setmarker drawLayer id6 50.1 0 0
      41  read rot cell1 110
      42  read rrd cell1 200
      43  read rzd cell1 201
      44  op sub rot rot 90
      45  op mul strd rrd rzd
      46  op add rot3 rot 90
>>>>  47  op cos cx rot3 b
      48  op sin sy rot3 b
      49  op mul rd_dx rd_dl cx
      50  op mul rd_dy rd_dl sy
      51  op mul st_dx st_dl cx
      52  op mul st_dy st_dl sy
      53  op div st_dx1 st_dx 3
      54  op div st_dy1 st_dy 3
      55  op sub cmx wx st_dx
      56  op sub cmy wy st_dy
      57  op sub cmx1 cmx rd_dx
      58  op sub cmy1 cmy rd_dy
      59  op sub cmx2 wx st_dx1
      60  op sub cmy2 wy st_dy1
      61  read afterst cell1 300
      62  jump 67 equal return 1
      63  jump 72 notEqual afterst 1
      64  set st_dl 0.8
      65  set stdr 10
      66  set return 1
      67  op sub st_dl st_dl 0.0008
      68  op sub stdr stdr 0.01
      69  write st_dl cell1 301
      70  jump 72 greaterThan st_dl 0
      71  set return 0
      72  write 1 cell1 202
      73  jump 78 greaterThan drd 7.5
      74  jump 78 equal strd 0
      75  write 0 cell1 202
      76  op add drd drd 0.005
      77  op add rd_dl rd_dl 0.0003
      ... 下面还有 31 条语句
```

判定:
备注:

### `aea0411e03`

- 出处：`mindustrytop-25559` · (350,269) · world-processor · 109 条语句
- 处理器自己的链接：`wall1`, `duct1`, `cell1`
- 被指行：语句序号 **48**
- 规则说：`op sin` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
      ... 上面还有 18 条语句
      18  makemarker texture id2 0 0 true
      19  makemarker texture id3 0 0 true
      20  makemarker texture id4 0 0 true
      21  makemarker texture id5 0 0 true
      22  makemarker texture id6 0 0 true
      23  setmarker texture id1 0 "smite-blade-l-outline" 0
      24  setmarker texture id2 0 "smite-blade-r-outline" 0
      25  setmarker texture id3 0 "build-tower" 0
      26  setmarker texture id4 0 "titan-barrel-outline" 0
      27  setmarker texture id5 0 "smite-back-l-outline" 0
      28  setmarker texture id6 0 "smite-back-r-outline" 0
      29  setmarker textureSize id1 -2.75 6 0
      30  setmarker textureSize id2 2.75 6 0
      31  setmarker textureSize id3 5 5 0
      32  setmarker textureSize id4 1.75 4 0
      33  setmarker textureSize id5 -5 5 0
      34  setmarker textureSize id6 5 5 0
      35  setmarker drawLayer id1 50.2 0 0
      36  setmarker drawLayer id2 50.2 0 0
      37  setmarker drawLayer id3 50.0 0 0
      38  setmarker drawLayer id4 50.3 0 0
      39  setmarker drawLayer id5 50.1 0 0
      40  setmarker drawLayer id6 50.1 0 0
      41  read rot cell1 110
      42  read rrd cell1 200
      43  read rzd cell1 201
      44  op sub rot rot 90
      45  op mul strd rrd rzd
      46  op add rot3 rot 90
      47  op cos cx rot3 b
>>>>  48  op sin sy rot3 b
      49  op mul rd_dx rd_dl cx
      50  op mul rd_dy rd_dl sy
      51  op mul st_dx st_dl cx
      52  op mul st_dy st_dl sy
      53  op div st_dx1 st_dx 3
      54  op div st_dy1 st_dy 3
      55  op sub cmx wx st_dx
      56  op sub cmy wy st_dy
      57  op sub cmx1 cmx rd_dx
      58  op sub cmy1 cmy rd_dy
      59  op sub cmx2 wx st_dx1
      60  op sub cmy2 wy st_dy1
      61  read afterst cell1 300
      62  jump 67 equal return 1
      63  jump 72 notEqual afterst 1
      64  set st_dl 0.8
      65  set stdr 10
      66  set return 1
      67  op sub st_dl st_dl 0.0008
      68  op sub stdr stdr 0.01
      69  write st_dl cell1 301
      70  jump 72 greaterThan st_dl 0
      71  set return 0
      72  write 1 cell1 202
      73  jump 78 greaterThan drd 7.5
      74  jump 78 equal strd 0
      75  write 0 cell1 202
      76  op add drd drd 0.005
      77  op add rd_dl rd_dl 0.0003
      78  jump 83 lessThan drd 2.5
      ... 下面还有 30 条语句
```

判定:
备注:

### `9a5ae795b1`

- 出处：`mindustrytop-25559` · (352,269) · world-processor · 135 条语句
- 处理器自己的链接：`cell1`, `wall1`
- 被指行：语句序号 **15**
- 规则说：`op cos` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
       0  setrate 1000
       1  sensor tx wall1 @x
       2  sensor ty wall1 @y
       3  set buid 0
       4  sensor team @this @team
       5  read rzd cell1 200
       6  read rrd cell1 201
       7  read rgd cell1 202
       8  op mul strd rzd rrd
       9  op mul strd strd rgd
      10  jump 5 notEqual strd 1
      11  set t1 @time
      12  set final 0
      13  read tr cell1 110
      14  op sub tr0 tr 40
>>>>  15  op cos cx0 tr b
      16  op sin sy0 tr b
      17  op mul lx_1 3 cx0
      18  op mul ly_1 3 sy0
      19  op add stx tx lx_1
      20  op add sty ty ly_1
      21  set range 0
      22  op cos cx0 tr0 b
      23  op sin sy0 tr0 b
      24  op mul lx0 2 cx0
      25  op mul ly0 2 sy0
      26  op add bx stx lx0
      27  op add by sty ly0
      28  op mul bu_n buid 6
      29  op add bu_n1 bu_n 1
      30  op add bu_n2 bu_n 2
      31  op add bu_n3 bu_n 3
      32  op add bu_n4 bu_n 4
      33  op add bu_n5 bu_n 5
      34  write bx cell1 bu_n
      35  write by cell1 bu_n1
      36  write tr0 cell1 bu_n2
      37  write range cell1 bu_n3
      38  write 0 cell1 bu_n4
      39  write 1 cell1 bu_n5
      40  op add buid buid 1
      41  op add tr0 tr0 20
      42  jump 21 lessThan buid 5
      43  set buid 0
      44  effect sparkExplosion stx sty 50 %ffe667
      45  effect smokeCloud stx sty 10 %ffe667
      ... 下面还有 89 条语句
```

判定:
备注:

### `1ea653b8e2`

- 出处：`mindustrytop-26053` · (63,17) · world-processor · 64 条语句
- 处理器自己的链接：`cell1`, `nucleus1`
- 被指行：语句序号 **32**
- 规则说：`op round` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
      ... 上面还有 2 条语句
       2  setrule waves 0 0 0 100 100
       3  setrule currentWaveTime 30 0 0 100 100
       4  print "\n"
       5  fetch buildCount 黄队容器数量 @sharded 0 @container
       6  setrate 100
       7  fetch core a 1 0 @container
       8  fetch core b 2 0 @container
       9  sensor 1 a @surge-alloy
      10  sensor 最大生命值1 a @maxHealth
      11  sensor 生命值1 a @health
      12  op div 百分比1 生命值1 最大生命值1
      13  op idiv 百分比1. 百分比1 0.01
      14  select 增加值 lessThanEq @second 360 55 增加值
      15  select 增加值 lessThanEq @second 180 45 增加值
      16  select 增加值 greaterThan @second 360 65 增加值
      17  op mul 加成1 黄队容器数量 15
      18  op add 增加值1 增加值 加成1
      19  print "[#ff6666]当前为入侵模式\n"
      20  print "[#cccc00]黄[#ffffff]"
      21  print 1
      22  print "+"
      23  print 增加值1
      24  print "\n"
      25  print "生命值:"
      26  print 百分比1.
      27  print "%\n"
      28  sensor f a @surge-alloy
      29  sensor e b @surge-alloy
      30  op mod s @second 30
      31  op sub s1 2700 @second
>>>>  32  op round s1 s1 @second
      33  op idiv s2 s1 60
      34  op mod s3 s1 60
      35  print "[#44ff44]绿[#ffffff]剩余时间"
      36  print s2
      37  print ":"
      38  jump 40 greaterThanEq s3 10
      39  print "0"
      40  print s3
      41  print "若时间结束黄队还未被攻破则绿队立即失败"
      42  message mission 3 @wait
      43  getlink dfg 0
      44  jump 50 notEqual dfg null
      45  print "黄队核心已爆炸，绿队赢了。\n地图中所有建筑将会原地爆炸，游戏结束。"
      46  message announce 5 @wait
      47  print "黄队核心已爆炸，绿队赢了。\n地图中所有建筑将会原地爆炸，游戏结束。"
      48  message notify 5 @wait
      49  explosion 3 100 100 999 9999999999999999999 true true 1 true
      50  jump 57 greaterThanEq s1 0
      51  print "进攻时间为零，黄队胜利。\n地图中所有建筑将会原地爆炸，游戏结束。"
      52  message announce 5 @wait
      53  print "进攻时间为零，黄队胜利。\n地图中所有建筑将会原地爆炸，游戏结束。"
      54  message notify 3 @wait
      55  wait 5
      56  explosion 3 100 100 999 9999999999999999999 true true 1 true
      57  jump 4 greaterThanEq s3 1
      58  set ddd 0
      59  op mul w 黄队容器数量 15
      60  op add u f w
      61  op add u1 u 增加值
      62  setprop @surge-alloy a u1
      ... 下面还有 1 条语句
```

判定:
备注:

### `41bcfefbf9`

- 出处：`mindustrytop-24936` · (1,22) · world-processor · 63 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **34**
- 规则说：`op floor` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
      ... 上面还有 4 条语句
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
      16  jump 19 equal F 211
      17  jump 13 notEqual 信标 false
      18  end
      19  set 次数 0
      20  sensor X 信标 @x
      21  sensor Y 信标 @y
      22  sensor BX BOSS @x
      23  sensor BY BOSS @y
      24  effect trail X Y 75 %a923d2d2
      25  wait 0.3
      26  op mul 速度倍率 难度 2
      27  op add 速度 速度倍率 15
      28  setrate 速度
      29  op mul 伤害倍率 难度 30
      30  op add 伤害 伤害倍率 140
      31  op sub 差X BX X
      32  op sub 差Y BY Y
      33  op len 差 差X 差Y
>>>>  34  op floor 整差 差 差Y
      35  op div 距离X 差X 60
      36  op div 距离Y 差Y 60
      37  op div 除数 差X 差Y
      38  op atan 角度 除数 差Y
      39  jump 42 greaterThan 差Y 0
      40  op sub 发射角度 90 角度
      41  jump -1 always 差Y 0
      42  op sub 发射角度 270 角度
      43  set 抛物线 300
      44  set 发射X BX
      45  set 发射Y BY
      46  op sub 抛物线 抛物线 4
      47  op sin 抛物线Y 抛物线 2
      48  op add 移动Y 抛物线Y 距离Y
      49  op sub 发射X 发射X 距离X
      50  op sub 发射Y 发射Y 移动Y
      51  effect trail 发射X 发射Y 8 %7f3d9492
      52  wait 0.02
      53  jump 46 greaterThan 抛物线 60
      54  fetch unitCount 总单位数 1 0 0
      55  op mul 时间倍率 难度 3
      56  op add 持续时间 时间倍率 10
      57  explosion 2 X Y 12 伤害 true true true true
      58  spawn @mono X Y 90 2 塔
      59  setprop @health 塔 持续时间
      60  setprop @flag 塔 212
      61  setprop @health 信标 0
      62  wait 1
```

判定:
备注:

### `3a35b755c1`

- 出处：`mindustrytop-24936` · (1,22) · world-processor · 63 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **38**
- 规则说：`op atan` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
      ... 上面还有 8 条语句
       8  jump 12 always x false
       9  set 难度 1
      10  jump 12 always x false
      11  set 难度 2
      12  set A 0
      13  fetch unit 信标 2 A @mono
      14  op add A A 1
      15  sensor F 信标 @flag
      16  jump 19 equal F 211
      17  jump 13 notEqual 信标 false
      18  end
      19  set 次数 0
      20  sensor X 信标 @x
      21  sensor Y 信标 @y
      22  sensor BX BOSS @x
      23  sensor BY BOSS @y
      24  effect trail X Y 75 %a923d2d2
      25  wait 0.3
      26  op mul 速度倍率 难度 2
      27  op add 速度 速度倍率 15
      28  setrate 速度
      29  op mul 伤害倍率 难度 30
      30  op add 伤害 伤害倍率 140
      31  op sub 差X BX X
      32  op sub 差Y BY Y
      33  op len 差 差X 差Y
      34  op floor 整差 差 差Y
      35  op div 距离X 差X 60
      36  op div 距离Y 差Y 60
      37  op div 除数 差X 差Y
>>>>  38  op atan 角度 除数 差Y
      39  jump 42 greaterThan 差Y 0
      40  op sub 发射角度 90 角度
      41  jump -1 always 差Y 0
      42  op sub 发射角度 270 角度
      43  set 抛物线 300
      44  set 发射X BX
      45  set 发射Y BY
      46  op sub 抛物线 抛物线 4
      47  op sin 抛物线Y 抛物线 2
      48  op add 移动Y 抛物线Y 距离Y
      49  op sub 发射X 发射X 距离X
      50  op sub 发射Y 发射Y 移动Y
      51  effect trail 发射X 发射Y 8 %7f3d9492
      52  wait 0.02
      53  jump 46 greaterThan 抛物线 60
      54  fetch unitCount 总单位数 1 0 0
      55  op mul 时间倍率 难度 3
      56  op add 持续时间 时间倍率 10
      57  explosion 2 X Y 12 伤害 true true true true
      58  spawn @mono X Y 90 2 塔
      59  setprop @health 塔 持续时间
      60  setprop @flag 塔 212
      61  setprop @health 信标 0
      62  wait 1
```

判定:
备注:

### `cd05a52f49`

- 出处：`mindustrytop-24936` · (1,22) · world-processor · 63 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **47**
- 规则说：`op sin` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
      ... 上面还有 17 条语句
      17  jump 13 notEqual 信标 false
      18  end
      19  set 次数 0
      20  sensor X 信标 @x
      21  sensor Y 信标 @y
      22  sensor BX BOSS @x
      23  sensor BY BOSS @y
      24  effect trail X Y 75 %a923d2d2
      25  wait 0.3
      26  op mul 速度倍率 难度 2
      27  op add 速度 速度倍率 15
      28  setrate 速度
      29  op mul 伤害倍率 难度 30
      30  op add 伤害 伤害倍率 140
      31  op sub 差X BX X
      32  op sub 差Y BY Y
      33  op len 差 差X 差Y
      34  op floor 整差 差 差Y
      35  op div 距离X 差X 60
      36  op div 距离Y 差Y 60
      37  op div 除数 差X 差Y
      38  op atan 角度 除数 差Y
      39  jump 42 greaterThan 差Y 0
      40  op sub 发射角度 90 角度
      41  jump -1 always 差Y 0
      42  op sub 发射角度 270 角度
      43  set 抛物线 300
      44  set 发射X BX
      45  set 发射Y BY
      46  op sub 抛物线 抛物线 4
>>>>  47  op sin 抛物线Y 抛物线 2
      48  op add 移动Y 抛物线Y 距离Y
      49  op sub 发射X 发射X 距离X
      50  op sub 发射Y 发射Y 移动Y
      51  effect trail 发射X 发射Y 8 %7f3d9492
      52  wait 0.02
      53  jump 46 greaterThan 抛物线 60
      54  fetch unitCount 总单位数 1 0 0
      55  op mul 时间倍率 难度 3
      56  op add 持续时间 时间倍率 10
      57  explosion 2 X Y 12 伤害 true true true true
      58  spawn @mono X Y 90 2 塔
      59  setprop @health 塔 持续时间
      60  setprop @flag 塔 212
      61  setprop @health 信标 0
      62  wait 1
```

判定:
备注:

### `e7df88211b`

- 出处：`mindustrytop-26076` · (22,28) · world-processor · 51 条语句
- 处理器自己的链接：`switch1`
- 被指行：语句序号 **9**
- 规则说：`op rand` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

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
>>>>   9  op rand xA 1 sx
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

### `cdaae36de7`

- 出处：`mindustrytop-26076` · (22,28) · world-processor · 51 条语句
- 处理器自己的链接：`switch1`
- 被指行：语句序号 **10**
- 规则说：`op rand` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

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
>>>>  10  op rand xR -1 sx
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

### `18ab61724f`

- 出处：`mindustrytop-26076` · (22,28) · world-processor · 51 条语句
- 处理器自己的链接：`switch1`
- 被指行：语句序号 **11**
- 规则说：`op rand` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

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
>>>>  11  op rand yA 1 sx
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

### `ff402cf8c6`

- 出处：`mindustrytop-25736` · (300,1) · world-processor · 69 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **50**
- 规则说：`op cos` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
      ... 上面还有 20 条语句
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
      44  jump 47 equal Ablock 1
      45  jump 58 equal Acore 0
      46  ucontrol approach hx hy range-5 0 0
      47  op sub -x hx x
      48  op sub -y hy y
      49  op angle j -x -y
>>>>  50  op cos sin j b
      51  op sin cos j b
      52  op mul sin sin range-1
      53  op mul cos cos range-1
      54  op add dx x sin
      55  op add dy y cos
      56  ucontrol target dx dy 1 0 0
      57  jump 59 always x false
      58  ucontrol target dx dy 0 0 0
      59  op add s s 1
      60  jump 2 lessThanEq s unitCount
      61  set s 0
      62  end
      63  ucontrol target tx ty 1 0 0
      64  jump 59 always x false
      65  ucontrol targetp enemy 1 1 0 0
      66  jump 59 always x false
      67  ucontrol target fx fy 1 0 0
      68  jump 59 always x false
```

判定:
备注:

### `843ce37b7e`

- 出处：`mindustrytop-25736` · (300,1) · world-processor · 69 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **51**
- 规则说：`op sin` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
      ... 上面还有 21 条语句
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
      44  jump 47 equal Ablock 1
      45  jump 58 equal Acore 0
      46  ucontrol approach hx hy range-5 0 0
      47  op sub -x hx x
      48  op sub -y hy y
      49  op angle j -x -y
      50  op cos sin j b
>>>>  51  op sin cos j b
      52  op mul sin sin range-1
      53  op mul cos cos range-1
      54  op add dx x sin
      55  op add dy y cos
      56  ucontrol target dx dy 1 0 0
      57  jump 59 always x false
      58  ucontrol target dx dy 0 0 0
      59  op add s s 1
      60  jump 2 lessThanEq s unitCount
      61  set s 0
      62  end
      63  ucontrol target tx ty 1 0 0
      64  jump 59 always x false
      65  ucontrol targetp enemy 1 1 0 0
      66  jump 59 always x false
      67  ucontrol target fx fy 1 0 0
      68  jump 59 always x false
```

判定:
备注:

### `2a82668df9`

- 出处：`mindustrytop-25736` · (223,8) · world-processor · 74 条语句
- 处理器自己的链接：`arc1`, `switch1`, `message1`
- 被指行：语句序号 **33**
- 规则说：`op sin` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
      ... 上面还有 3 条语句
       3  printflush message1
       4  sensor team @this @team
       5  set 高度 70
       6  set 范围 18
       7  set 伤害 10000
       8  set 下降速度 0.035
       9  set 个数 0
      10  set 随机范围 0
      11  sensor k switch1 @enabled
      12  fetch core core team 0 @conveyor
      13  jump 11 notEqual k 1
      14  sensor w core @blast-compound
      15  jump 11 lessThan w 25000
      16  control enabled arc1 0 0 0 0
      17  sensor k arc1 @shooting
      18  sensor k arc1 @shooting
      19  sensor zx arc1 @x
      20  sensor zy arc1 @y
      21  set 圈 0
      22  jump 16 strictEqual k 0
      23  setblock block @air zx zy @derelict 0
      24  setblock block @arc zx zy team 0
      25  op sub w w 25000
      26  setprop @blast-compound core w
      27  sensor x arc1 @shootX
      28  sensor y arc1 @shootY
      29  effect breakBlock x y 10 %ffaaff
      30  print "核弹头正在运往指定坐标\n[cyan]◈◈◈◈"
      31  message notify 3 @wait
      32  set j 0
>>>>  33  op sin sin j b
      34  op cos cos j b
      35  op mul sin sin 8
      36  op mul cos cos 8
      37  op add dx sin x
      38  op add dy cos y
      39  jump 43 strictEqual 圈 2
      40  jump 45 greaterThanEq 圈 3
      41  effect lightBlock dx dy 0.82 %9fff6f
      42  jump 46 always x false
      43  effect lightBlock dx dy 0.82 %fffd6f
      44  jump 46 always x false
      45  effect lightBlock dx dy 0.82 %ff1c1c
      46  op add j j 1
      47  jump 51 strictEqual j 130
      48  jump 51 strictEqual j 245
      49  jump 51 strictEqual j 350
      50  jump 52 always j 360
      51  effect warn x y 2 %ffaaff
      52  jump 33 lessThan j 360
      53  op add 圈 圈 1
      54  jump 32 lessThanEq 圈 3
      55  op add Y y 高度
      56  op sub Y Y 下降速度
      57  effect explosion x Y 0.36 %ffaaff
      58  jump 56 greaterThan Y y
      59  effect smokeCloud x y 2 %ff0000
      60  effect wave x y 范围 %ffffff
      61  wait 0.1
      62  effect wave x y 范围 %ffffff
      63  wait 0.1
      ... 下面还有 10 条语句
```

判定:
备注:

### `162960d1ee`

- 出处：`mindustrytop-14962` · (0,0) · world-processor · 37 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **10**
- 规则说：`op rand` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
       0  fetch build  @green 0 @launch-pad
       1  sensor x  @x
       2  sensor y  @y
       3  sensor 存在  @dead
       4  jump 6 equal 存在 0
       5  end
       6  jump 10 equal 存在 1
       7  sensor 存在  @dead
       8  explosion @crux x y 1 5000 true true false
       9  jump 6 always 存在 0
>>>>  10  op rand c 10 b
      11  op rand b c b
      12  jump 14 greaterThanEq b 0
      13  jump 0 always x false
      14  spawn @risso x y 90 @green nova
      15  spawn @retusa x y 90 @green nova
      16  jump 18 greaterThanEq b 2
      17  end
      18  spawn @minke x y 90 @green pulsar
      19  spawn @oxynoe x y 90 @green pulsar
      20  jump 22 greaterThanEq b 4
      21  end
      22  spawn @bryde x y 90 @green quasar
      23  spawn @cyerce x y 90 @green quasar
      24  jump 26 greaterThanEq b 6
      25  end
      26  spawn @sei x y 90 @green vela
      27  spawn @aegires x y 90 @green vela
      28  jump 30 greaterThanEq b 8
      29  end
      30  spawn @omura x y 90 @green corvus
      31  spawn @navanax x y 90 @green corvus
      32  fetch player 玩家 @green 0 @conveyor
      33  sensor id 玩家 @name
      34  print id
      35  print "[red]抽中了"
      36  message toast 3
```

判定:
备注:

### `1a48c8d592`

- 出处：`mindustrytop-14962` · (0,0) · world-processor · 37 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **11**
- 规则说：`op rand` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
       0  fetch build  @green 0 @launch-pad
       1  sensor x  @x
       2  sensor y  @y
       3  sensor 存在  @dead
       4  jump 6 equal 存在 0
       5  end
       6  jump 10 equal 存在 1
       7  sensor 存在  @dead
       8  explosion @crux x y 1 5000 true true false
       9  jump 6 always 存在 0
      10  op rand c 10 b
>>>>  11  op rand b c b
      12  jump 14 greaterThanEq b 0
      13  jump 0 always x false
      14  spawn @risso x y 90 @green nova
      15  spawn @retusa x y 90 @green nova
      16  jump 18 greaterThanEq b 2
      17  end
      18  spawn @minke x y 90 @green pulsar
      19  spawn @oxynoe x y 90 @green pulsar
      20  jump 22 greaterThanEq b 4
      21  end
      22  spawn @bryde x y 90 @green quasar
      23  spawn @cyerce x y 90 @green quasar
      24  jump 26 greaterThanEq b 6
      25  end
      26  spawn @sei x y 90 @green vela
      27  spawn @aegires x y 90 @green vela
      28  jump 30 greaterThanEq b 8
      29  end
      30  spawn @omura x y 90 @green corvus
      31  spawn @navanax x y 90 @green corvus
      32  fetch player 玩家 @green 0 @conveyor
      33  sensor id 玩家 @name
      34  print id
      35  print "[red]抽中了"
      36  message toast 3
```

判定:
备注:

### `ecee973d14`

- 出处：`mindustrytop-14962` · (2,0) · world-processor · 46 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **11**
- 规则说：`op rand` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
       0  fetch build  @blue 1 @impact-reactor
       1  setrate 5
       2  sensor x  @x
       3  sensor y  @y
       4  sensor 生命  @dead
       5  jump 7 equal 生命 0
       6  end
       7  jump 11 equal 生命 1
       8  sensor 生命  @dead
       9  explosion @crux x y 3 0 true true false
      10  jump 7 always x false
>>>>  11  op rand b 8 b
      12  explosion @crux x y 1 9999 true true false
      13  wait 1
      14  jump 16 greaterThanEq b 0
      15  jump 0 always x false
      16  jump 19 greaterThanEq b 1
      17  spawn @eclipse x y 90 @blue reign
      18  end
      19  jump 22 greaterThanEq b 2
      20  spawn @oct x y 90 @blue oct
      21  end
      22  jump 25 greaterThanEq b 3
      23  spawn @reign x y 90 @blue eclipse
      24  end
      25  jump 28 greaterThanEq b 4
      26  spawn @toxopid x y 90 @blue toxopid
      27  end
      28  jump 31 greaterThanEq b 5
      29  spawn @conquer x y 90 @blue conquer
      30  end
      31  jump 34 greaterThanEq b 6
      32  spawn @collaris x y 90 @blue collaris
      33  end
      34  jump 37 greaterThanEq b 7
      35  spawn @disrupt x y 90 @blue disrupt
      36  end
      37  spawn @disrupt x y 90 @blue result
      38  spawn @collaris x y 90 @blue result
      39  spawn @conquer x y 90 @blue result
      40  fetch player 玩家 @blue 0 @conveyor
      41  sensor id 玩家 @name
      42  print "哇"
      43  print id
      44  print "抽出了E星套餐"
      45  message toast 3
```

判定:
备注:

### `5f0881f750`

- 出处：`mindustrytop-25680` · (28,31) · micro-processor · 140 条语句
- 处理器自己的链接：`pad1`, `sorter1`, `pad2`
- 被指行：语句序号 **68**
- 规则说：`op rand` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
      ... 上面还有 38 条语句
      38  lookup item a7 7
      39  jump 41 notEqual 废料 0
      40  lookup item a8 8
      41  jump 43 notEqual 玻璃 0
      42  lookup item a2 2
      43  jump 45 notEqual 石墨 0
      44  lookup item a3 3
      45  jump 47 notEqual 硅 0
      46  lookup item a9 9
      47  jump 49 notEqual 塑钢 0
      48  lookup item a10 10
      49  jump 51 notEqual 布 0
      50  lookup item a11 11
      51  jump 53 notEqual 合金 0
      52  lookup item a12 12
      53  jump 55 notEqual 孢子 0
      54  lookup item a13 13
      55  jump 57 notEqual 爆炸混合物 0
      56  lookup item a14 14
      57  jump 59 notEqual 硫化物 0
      58  lookup item a15 15
      59  jump 61 notEqual 铍 0
      60  lookup item a16 16
      61  jump 63 notEqual 钨 0
      62  lookup item a17 17
      63  jump 65 notEqual 氧化物 0
      64  lookup item a18 18
      65  jump 67 notEqual 碳化物 0
      66  lookup item a19 19
      67  jump 76 notEqual hx null
>>>>  68  op rand r 54 b
      69  lookup unit uty r
      70  ubind uty
      71  jump 68 equal @unit null
      72  sensor co @unit @controlled
      73  jump 68 notEqual co 0
      74  ulocate building core 0 @copper x y found hx
      75  ucontrol unbind 0 0 0 0 0
      76  sensor hxde hx @dead
      77  jump 68 equal hxde 1
      78  set min 99999999
      79  set setcfg null
      80  set imax 15
      81  jump 83 equal E星 0
      82  set imax 19
      83  set i 0
      84  lookup item cfg i
      85  jump 134 greaterThan i imax
      86  op mul jump i 2
      87  op add @counter @counter jump
      88  jump 132 equal cfg a0
      89  jump 127 always x false
      90  jump 132 equal cfg a1
      91  jump 127 always x false
      92  jump 132 equal cfg a2
      93  jump 127 always x false
      94  jump 132 equal cfg a3
      95  jump 127 always x false
      96  jump 132 equal cfg a4
      97  jump 127 always x false
      98  jump 132 equal cfg a5
      ... 下面还有 41 条语句
```

判定:
备注:

### `cd2e502b8f`

- 出处：`mindustrytop-26079` · (242,243) · world-processor · 506 条语句
- 处理器自己的链接：`arc1`, `cell1`
- 被指行：语句序号 **30**
- 规则说：`op rand` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
       0  wait 1
       1  set cell:4:4 cell1
       2  jump 5 notEqual cell:4:4 null
       3  set cell:4:4 cell1
       4  end
       5  set SHARE_T1:10:4 0.3
       6  set SHARE_T2:11:4 0.25
       7  set SHARE_T3:12:4 0.25
       8  set SHARE_T4:13:4 0.2
       9  set SHARE_T5:14:4 0.1
      10  set attackInt:31:4 2
      11  set maxAttackPoints:32:4 2999
      12  write attackInt:31:4 cell:4:4 13
      13  write maxAttackPoints:32:4 cell:4:4 14
      14  set running:35:4 0
      15  set arc1:36:4 arc1
      16  set basicPoints:37:4 1
      17  set maxPoints:38:4 25
      18  set coreWidth:40:4 10
      19  read &t0 cell:4:4 20
      20  jump 19 equal &t0 0
      21  read different:42:4 cell:4:4 20
      22  setrate 200
      23  set launch:46:4 0
      24  jump 34 notEqual launch:46:4 0
      25  set launch:46:4 1
      26  read &t1 cell:4:4 6
      27  jump 30 equal &t1 0
      28  read seed:39:4 cell:4:4 6
      29  jump 34 always x false
>>>>  30  op rand &t2 65536000 b
      31  op floor &t3 &t2 b
      32  write &t3 cell:4:4 6
      33  read seed:39:4 cell:4:4 6
      34  read &t1 cell:4:4 5
      35  jump 38 equal &t1 0
      36  set &rdone:150:0 38
      37  jump 77 always x false
      38  set arc1:36:4 arc1
      39  jump 41 notEqual arc1:36:4 null
      40  set arc1:36:4 arc1
      41  sensor &t2 arc1:36:4 @controlled
      42  jump 52 notEqual &t2 @ctrlPlayer
      43  sensor shootX:57:4 arc1:36:4 @shootX
      44  sensor shootY:58:4 arc1:36:4 @shootY
      45  set size:74:19 25
      46  set &rdrawBlock:74:0 48
      47  jump 91 always x false
      48  sensor &t3 arc1:36:4 @shooting
      49  jump 52 equal &t3 0
      50  set &rstart:118:0 52
      51  jump 450 always x false
      52  jump 34 always x false
      53  end
      54  read &t0:spawnCore:158:0 cell:4:4 1
      55  read &t1:spawnCore:158:0 cell:4:4 3
      56  op add &t2:spawnCore:158:0 &t0:spawnCore:158:0 &t1:spawnCore:158:0
      57  op div centerX:159:10 &t2:spawnCore:158:0 2
      58  read &t3:spawnCore:158:0 cell:4:4 2
      59  read &t4:spawnCore:158:0 cell:4:4 4
      60  op add &t5:spawnCore:158:0 &t3:spawnCore:158:0 &t4:spawnCore:158:0
      ... 下面还有 445 条语句
```

判定:
备注:

### `17de72d0a6`

- 出处：`mindustrytop-26079` · (242,243) · world-processor · 506 条语句
- 处理器自己的链接：`arc1`, `cell1`
- 被指行：语句序号 **31**
- 规则说：`op floor` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
      ... 上面还有 1 条语句
       1  set cell:4:4 cell1
       2  jump 5 notEqual cell:4:4 null
       3  set cell:4:4 cell1
       4  end
       5  set SHARE_T1:10:4 0.3
       6  set SHARE_T2:11:4 0.25
       7  set SHARE_T3:12:4 0.25
       8  set SHARE_T4:13:4 0.2
       9  set SHARE_T5:14:4 0.1
      10  set attackInt:31:4 2
      11  set maxAttackPoints:32:4 2999
      12  write attackInt:31:4 cell:4:4 13
      13  write maxAttackPoints:32:4 cell:4:4 14
      14  set running:35:4 0
      15  set arc1:36:4 arc1
      16  set basicPoints:37:4 1
      17  set maxPoints:38:4 25
      18  set coreWidth:40:4 10
      19  read &t0 cell:4:4 20
      20  jump 19 equal &t0 0
      21  read different:42:4 cell:4:4 20
      22  setrate 200
      23  set launch:46:4 0
      24  jump 34 notEqual launch:46:4 0
      25  set launch:46:4 1
      26  read &t1 cell:4:4 6
      27  jump 30 equal &t1 0
      28  read seed:39:4 cell:4:4 6
      29  jump 34 always x false
      30  op rand &t2 65536000 b
>>>>  31  op floor &t3 &t2 b
      32  write &t3 cell:4:4 6
      33  read seed:39:4 cell:4:4 6
      34  read &t1 cell:4:4 5
      35  jump 38 equal &t1 0
      36  set &rdone:150:0 38
      37  jump 77 always x false
      38  set arc1:36:4 arc1
      39  jump 41 notEqual arc1:36:4 null
      40  set arc1:36:4 arc1
      41  sensor &t2 arc1:36:4 @controlled
      42  jump 52 notEqual &t2 @ctrlPlayer
      43  sensor shootX:57:4 arc1:36:4 @shootX
      44  sensor shootY:58:4 arc1:36:4 @shootY
      45  set size:74:19 25
      46  set &rdrawBlock:74:0 48
      47  jump 91 always x false
      48  sensor &t3 arc1:36:4 @shooting
      49  jump 52 equal &t3 0
      50  set &rstart:118:0 52
      51  jump 450 always x false
      52  jump 34 always x false
      53  end
      54  read &t0:spawnCore:158:0 cell:4:4 1
      55  read &t1:spawnCore:158:0 cell:4:4 3
      56  op add &t2:spawnCore:158:0 &t0:spawnCore:158:0 &t1:spawnCore:158:0
      57  op div centerX:159:10 &t2:spawnCore:158:0 2
      58  read &t3:spawnCore:158:0 cell:4:4 2
      59  read &t4:spawnCore:158:0 cell:4:4 4
      60  op add &t5:spawnCore:158:0 &t3:spawnCore:158:0 &t4:spawnCore:158:0
      61  op div centerY:160:10 &t5:spawnCore:158:0 2
      ... 下面还有 444 条语句
```

判定:
备注:

### `f74d63e6e7`

- 出处：`mindustrytop-26079` · (242,243) · world-processor · 506 条语句
- 处理器自己的链接：`arc1`, `cell1`
- 被指行：语句序号 **77**
- 规则说：`op rand` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
      ... 上面还有 47 条语句
      47  jump 91 always x false
      48  sensor &t3 arc1:36:4 @shooting
      49  jump 52 equal &t3 0
      50  set &rstart:118:0 52
      51  jump 450 always x false
      52  jump 34 always x false
      53  end
      54  read &t0:spawnCore:158:0 cell:4:4 1
      55  read &t1:spawnCore:158:0 cell:4:4 3
      56  op add &t2:spawnCore:158:0 &t0:spawnCore:158:0 &t1:spawnCore:158:0
      57  op div centerX:159:10 &t2:spawnCore:158:0 2
      58  read &t3:spawnCore:158:0 cell:4:4 2
      59  read &t4:spawnCore:158:0 cell:4:4 4
      60  op add &t5:spawnCore:158:0 &t3:spawnCore:158:0 &t4:spawnCore:158:0
      61  op div centerY:160:10 &t5:spawnCore:158:0 2
      62  set coreWidth:40:4 5
      63  set dx:163:13 -2
      64  jump 75 greaterThan dx:163:13 2
      65  set dy:164:17 -2
      66  jump 73 greaterThan dy:164:17 2
      67  op add &t6:spawnCore:158:0 centerX:159:10 dx:163:13
      68  op add &t7:spawnCore:158:0 centerY:160:10 dy:164:17
      69  setblock floor @core-zone &t6:spawnCore:158:0 &t7:spawnCore:158:0 @derelict 0
      70  setblock block @air centerX:159:10 centerY:160:10 @sharded 0
      71  op add dy:164:17 dy:164:17 1
      72  jump 66 always x false
      73  op add dx:163:13 dx:163:13 1
      74  jump 64 always x false
      75  set &fspawnCore:158:0 null
      76  set @counter &rspawnCore:158:0
>>>>  77  op rand &t0:done:150:0 100 b
      78  jump 82 greaterThanEq &t0:done:150:0 coreWidth:40:4
      79  set &rspawnCore:158:0 81
      80  jump 54 always x false
      81  jump 83 always x false
      82  op add coreWidth:40:4 coreWidth:40:4 5
      83  write 0 cell:4:4 0
      84  write 0 cell:4:4 5
      85  read &t1:done:150:0 cell:4:4 12
      86  op add &t2:done:150:0 &t1:done:150:0 1
      87  write &t2:done:150:0 cell:4:4 12
      88  set running:35:4 0
      89  set &fdone:150:0 null
      90  set @counter &rdone:150:0
      91  op div &t0:drawBlock:74:0 shootX:57:4 size:74:19
      92  op or &t1:drawBlock:74:0 &t0:drawBlock:74:0 0
      93  op mul drawX:75:8 &t1:drawBlock:74:0 size:74:19
      94  op div &t2:drawBlock:74:0 shootY:58:4 size:74:19
      95  op or &t3:drawBlock:74:0 &t2:drawBlock:74:0 0
      96  op mul drawY:76:8 &t3:drawBlock:74:0 size:74:19
      97  getblock floor &t4:drawBlock:74:0 shootX:57:4 shootY:58:4
      98  jump 105 equal &t4:drawBlock:74:0 @empty
      99  op div &t5:drawBlock:74:0 size:74:19 2
     100  op add &t6:drawBlock:74:0 drawX:75:8 &t5:drawBlock:74:0
     101  op add &t7:drawBlock:74:0 drawY:76:8 &t5:drawBlock:74:0
     102  effect placeBlock &t6:drawBlock:74:0 &t7:drawBlock:74:0 size:74:19 %ff0000
     103  set &fdrawBlock:74:0 null
     104  set @counter &rdrawBlock:74:0
     105  op div &t5:drawBlock:74:0 size:74:19 2
     106  op add &t6:drawBlock:74:0 drawX:75:8 &t5:drawBlock:74:0
     107  op add &t7:drawBlock:74:0 drawY:76:8 &t5:drawBlock:74:0
      ... 下面还有 398 条语句
```

判定:
备注:

### `5c88fcb686`

- 出处：`mindustrytop-25872` · (5,33) · logic-processor · 17 条语句
- 处理器自己的链接：`board`
- 被指行：语句序号 **7**
- 规则说：`op sqrt` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
       0  set w 5
       1  set h 3
       2  op mul area w h
       3  # @ls-expr-card area "w * h"
       4  op div half area 2
       5  # @ls-expr-card half "area / 2"
       6  op mul _0 w w
>>>>   7  op mul _1 h h
       8  op add _0 _0 _1
       9  op sqrt diag _0 0
      10  print "w=5 h=3: area="
      11  print area
      12  print " half="
      13  print half
      14  print " diag="
      15  print diag
      16  printflush board
```

判定:
备注:

### `0171bbcff7`

- 出处：`mindustrytop-25872` · (43,69) · logic-processor · 241 条语句
- 处理器自己的链接：`board`, `cell1`
- 被指行：语句序号 **52**
- 规则说：`op abs` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
      ... 上面还有 22 条语句
      22  op add __ls_func___ls_builtin_mapget_ret __ls_func___ls_builtin_mapget_ret 2
      23  jump __ls_func___ls_builtin_mapget_entry always x false
      24  set v __ls_func___ls_builtin_mapget_result
      25  set __ls_func___ls_builtin_usethas_mem cell1
      26  set __ls_func___ls_builtin_usethas_base 8
      27  set __ls_func___ls_builtin_usethas_cap 4
      28  set __ls_func___ls_builtin_usethas_key 9
      29  set __ls_func___ls_builtin_usethas_ret @counter
      30  op add __ls_func___ls_builtin_usethas_ret __ls_func___ls_builtin_usethas_ret 2
      31  jump __ls_func___ls_builtin_usethas_entry always x false
      32  set has __ls_func___ls_builtin_usethas_result
      33  set __ls_func___ls_builtin_usetsize_mem cell1
      34  set __ls_func___ls_builtin_usetsize_base 8
      35  set __ls_func___ls_builtin_usetsize_cap 4
      36  set __ls_func___ls_builtin_usetsize_ret @counter
      37  op add __ls_func___ls_builtin_usetsize_ret __ls_func___ls_builtin_usetsize_ret 2
      38  jump __ls_func___ls_builtin_usetsize_entry always x false
      39  set size __ls_func___ls_builtin_usetsize_result
      40  print "m[1]="
      41  print v
      42  print " u 含 9 = "
      43  print has
      44  print " u 元素数="
      45  print size
      46  printflush board
      47  set @counter 0
      48  jump __ls_end always x false
      49  __ls_func___ls_builtin_mapset_entry:
      50  op div __ls_mp_nan 0 0
      51  op strictEqual __ls_mp_bad __ls_func___ls_builtin_mapset_key __ls_mp_nan
>>>>  52  jump __ls_func___ls_builtin_mapset_stmt_33 equal __ls_mp_bad 1
      53  op abs __ls_mp_h __ls_func___ls_builtin_mapset_key 0
      54  op mod __ls_mp_i __ls_mp_h __ls_func___ls_builtin_mapset_cap
      55  set __ls_mp_n 0
      56  set __ls_mp_free -1
      57  __ls_func___ls_builtin_mapset_stmt_7:
      58  jump __ls_func___ls_builtin_mapset_stmt_24 greaterThanEq __ls_mp_n __ls_func___ls_builtin_mapset_cap
      59  op add __ls_mp_a __ls_func___ls_builtin_mapset_base __ls_mp_i
      60  read __ls_mp_k __ls_func___ls_builtin_mapset_mem __ls_mp_a
      61  op strictEqual __ls_mp_e __ls_mp_k __ls_mp_nan
      62  jump __ls_func___ls_builtin_mapset_stmt_15 equal __ls_mp_e 0
      63  jump __ls_func___ls_builtin_mapset_stmt_16 notEqual __ls_mp_free -1
      64  set __ls_mp_free __ls_mp_i
      65  jump __ls_func___ls_builtin_mapset_stmt_16 always x false
      66  __ls_func___ls_builtin_mapset_stmt_15:
      67  jump __ls_func___ls_builtin_mapset_stmt_20 equal __ls_mp_k __ls_func___ls_builtin_mapset_key
      68  __ls_func___ls_builtin_mapset_stmt_16:
      69  op add __ls_mp_i __ls_mp_i 1
      70  op mod __ls_mp_i __ls_mp_i __ls_func___ls_builtin_mapset_cap
      71  op add __ls_mp_n __ls_mp_n 1
      72  jump __ls_func___ls_builtin_mapset_stmt_7 always x false
      73  __ls_func___ls_builtin_mapset_stmt_20:
      74  op add __ls_mp_va __ls_mp_a __ls_func___ls_builtin_mapset_cap
      75  write __ls_func___ls_builtin_mapset_value __ls_func___ls_builtin_mapset_mem __ls_mp_va
      76  set __ls_mp_res 1
      77  set __ls_func___ls_builtin_mapset_result __ls_mp_res
      78  set @counter __ls_func___ls_builtin_mapset_ret
      79  __ls_func___ls_builtin_mapset_stmt_24:
      80  jump __ls_func___ls_builtin_mapset_stmt_31 lessThan __ls_mp_free 0
      81  op add __ls_mp_a2 __ls_func___ls_builtin_mapset_base __ls_mp_free
      82  write __ls_func___ls_builtin_mapset_key __ls_func___ls_builtin_mapset_mem __ls_mp_a2
      ... 下面还有 158 条语句
```

判定:
备注:

### `432741da32`

- 出处：`mindustrytop-25872` · (43,69) · logic-processor · 241 条语句
- 处理器自己的链接：`board`, `cell1`
- 被指行：语句序号 **92**
- 规则说：`op abs` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
      ... 上面还有 62 条语句
      62  jump __ls_func___ls_builtin_mapset_stmt_15 equal __ls_mp_e 0
      63  jump __ls_func___ls_builtin_mapset_stmt_16 notEqual __ls_mp_free -1
      64  set __ls_mp_free __ls_mp_i
      65  jump __ls_func___ls_builtin_mapset_stmt_16 always x false
      66  __ls_func___ls_builtin_mapset_stmt_15:
      67  jump __ls_func___ls_builtin_mapset_stmt_20 equal __ls_mp_k __ls_func___ls_builtin_mapset_key
      68  __ls_func___ls_builtin_mapset_stmt_16:
      69  op add __ls_mp_i __ls_mp_i 1
      70  op mod __ls_mp_i __ls_mp_i __ls_func___ls_builtin_mapset_cap
      71  op add __ls_mp_n __ls_mp_n 1
      72  jump __ls_func___ls_builtin_mapset_stmt_7 always x false
      73  __ls_func___ls_builtin_mapset_stmt_20:
      74  op add __ls_mp_va __ls_mp_a __ls_func___ls_builtin_mapset_cap
      75  write __ls_func___ls_builtin_mapset_value __ls_func___ls_builtin_mapset_mem __ls_mp_va
      76  set __ls_mp_res 1
      77  set __ls_func___ls_builtin_mapset_result __ls_mp_res
      78  set @counter __ls_func___ls_builtin_mapset_ret
      79  __ls_func___ls_builtin_mapset_stmt_24:
      80  jump __ls_func___ls_builtin_mapset_stmt_31 lessThan __ls_mp_free 0
      81  op add __ls_mp_a2 __ls_func___ls_builtin_mapset_base __ls_mp_free
      82  write __ls_func___ls_builtin_mapset_key __ls_func___ls_builtin_mapset_mem __ls_mp_a2
      83  op add __ls_mp_va2 __ls_mp_a2 __ls_func___ls_builtin_mapset_cap
      84  write __ls_func___ls_builtin_mapset_value __ls_func___ls_builtin_mapset_mem __ls_mp_va2
      85  set __ls_mp_res 1
      86  set __ls_func___ls_builtin_mapset_result __ls_mp_res
      87  set @counter __ls_func___ls_builtin_mapset_ret
      88  __ls_func___ls_builtin_mapset_stmt_31:
      89  set __ls_mp_res -1
      90  set __ls_func___ls_builtin_mapset_result __ls_mp_res
      91  set @counter __ls_func___ls_builtin_mapset_ret
>>>>  92  __ls_func___ls_builtin_mapset_stmt_33:
      93  set __ls_mp_res -1
      94  set __ls_func___ls_builtin_mapset_result __ls_mp_res
      95  set @counter __ls_func___ls_builtin_mapset_ret
      96  __ls_func___ls_builtin_mapset_exit:
      97  set @counter __ls_func___ls_builtin_mapset_ret
      98  __ls_func___ls_builtin_mapget_entry:
      99  op div __ls_mp_nan 0 0
     100  op strictEqual __ls_mp_bad __ls_func___ls_builtin_mapget_key __ls_mp_nan
     101  jump __ls_func___ls_builtin_mapget_stmt_19 equal __ls_mp_bad 1
     102  op abs __ls_mp_h __ls_func___ls_builtin_mapget_key 0
     103  op mod __ls_mp_i __ls_mp_h __ls_func___ls_builtin_mapget_cap
     104  set __ls_mp_n 0
     105  __ls_func___ls_builtin_mapget_stmt_6:
     106  jump __ls_func___ls_builtin_mapget_stmt_19 greaterThanEq __ls_mp_n __ls_func___ls_builtin_mapget_cap
     107  op add __ls_mp_a __ls_func___ls_builtin_mapget_base __ls_mp_i
     108  read __ls_mp_k __ls_func___ls_builtin_mapget_mem __ls_mp_a
     109  op strictEqual __ls_mp_e __ls_mp_k __ls_mp_nan
     110  jump __ls_func___ls_builtin_mapget_stmt_12 equal __ls_mp_e 1
     111  jump __ls_func___ls_builtin_mapget_stmt_16 equal __ls_mp_k __ls_func___ls_builtin_mapget_key
     112  __ls_func___ls_builtin_mapget_stmt_12:
     113  op add __ls_mp_i __ls_mp_i 1
     114  op mod __ls_mp_i __ls_mp_i __ls_func___ls_builtin_mapget_cap
     115  op add __ls_mp_n __ls_mp_n 1
     116  jump __ls_func___ls_builtin_mapget_stmt_6 always x false
     117  __ls_func___ls_builtin_mapget_stmt_16:
     118  op add __ls_mp_va __ls_mp_a __ls_func___ls_builtin_mapget_cap
     119  read __ls_mp_res __ls_func___ls_builtin_mapget_mem __ls_mp_va
     120  set __ls_func___ls_builtin_mapget_result __ls_mp_res
     121  set @counter __ls_func___ls_builtin_mapget_ret
     122  __ls_func___ls_builtin_mapget_stmt_19:
      ... 下面还有 118 条语句
```

判定:
备注:

### `b279e20551`

- 出处：`mindustrytop-20445` · (0,25) · world-processor · 30 条语句
- 处理器自己的链接：`nucleus1`
- 被指行：语句序号 **12**
- 规则说：`op cos` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
       0  sensor x11 nucleus1 @x
       1  sensor y11 nucleus1 @y
       2  jump 0 strictEqual nucleus1 null
       3  radar enemy any any distance @this 1 enemy
       4  sensor x enemy @x
       5  sensor y enemy @y
       6  jump 0 strictEqual enemy null
       7  op sub x1 x x11
       8  op sub y1 y y11
       9  op len range x1 y1
      10  op angle angle x1 y1
      11  jump 0 greaterThan range 25
>>>>  12  op cos cos angle b
      13  op sin sin angle b
      14  op add 1x1 x11 cos
      15  op add 1y1 y11 sin
      16  effect shootSmall 1x1 1y1 angle %ffda34
      17  explosion 1 x y 1.5 27 true true false true
      18  playsound true @sfx-shoot 1 1 0 1x1 1y1 0
      19  effect sparkShootBig x y angle %edff63
      20  op add xx x cos
      21  op add yy y sin
      22  explosion 1 xx yy 1.7 15 true true false 0
      23  op add xx xx cos
      24  op add yy yy sin
      25  explosion 1 xx yy 1.8 8 true true false 0
      26  op add xx xx cos
      27  op add yy yy sin
      28  explosion 1 xx yy 2 3 true true false 0
      29  wait 0.1
```

判定:
备注:

### `ce54a45ff3`

- 出处：`mindustrytop-20445` · (0,25) · world-processor · 30 条语句
- 处理器自己的链接：`nucleus1`
- 被指行：语句序号 **13**
- 规则说：`op sin` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

```
       0  sensor x11 nucleus1 @x
       1  sensor y11 nucleus1 @y
       2  jump 0 strictEqual nucleus1 null
       3  radar enemy any any distance @this 1 enemy
       4  sensor x enemy @x
       5  sensor y enemy @y
       6  jump 0 strictEqual enemy null
       7  op sub x1 x x11
       8  op sub y1 y y11
       9  op len range x1 y1
      10  op angle angle x1 y1
      11  jump 0 greaterThan range 25
      12  op cos cos angle b
>>>>  13  op sin sin angle b
      14  op add 1x1 x11 cos
      15  op add 1y1 y11 sin
      16  effect shootSmall 1x1 1y1 angle %ffda34
      17  explosion 1 x y 1.5 27 true true false true
      18  playsound true @sfx-shoot 1 1 0 1x1 1y1 0
      19  effect sparkShootBig x y angle %edff63
      20  op add xx x cos
      21  op add yy y sin
      22  explosion 1 xx yy 1.7 15 true true false 0
      23  op add xx xx cos
      24  op add yy yy sin
      25  explosion 1 xx yy 1.8 8 true true false 0
      26  op add xx xx cos
      27  op add yy yy sin
      28  explosion 1 xx yy 2 3 true true false 0
      29  wait 0.1
```

判定:
备注:

## 规则 `version-gate`

### `b0566c28e7`

- 出处：`mindustrytop-25774` · (125,137) · logic-processor · 141 条语句
- 处理器自己的链接：`message1`, `pad1`, `pad2`, `pad3`, `pad4`, `pad5`, `pad6`, `pad7`, `pad8`, `pad9`, `pad10`, `pad11`, `pad12`, `pad13`, `pad14`, `pad15`
- 被指行：语句序号 **0**
- 规则说：version gate: uses format -- needs build >= 147; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  jump 36 notEqual core null
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
      24  printflush Notification
      25  print "找不到核心，确认你已生产任意可控制单位"
      26  set unit.i 0
      27  lookup unit uty unit.i
      28  ubind uty
      29  op add unit.i unit.i 1
      30  jump 32 notEqual @unit null
      ... 下面还有 110 条语句
```

判定:
备注:

### `0dc6296964`

- 出处：`mindustrytop-25774` · (413,408) · micro-processor · 6 条语句
- 处理器自己的链接：`container1`, `conveyor1`
- 被指行：语句序号 **0**
- 规则说：version gate: uses select -- needs build >= 150; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  getlink building.container 0
       1  getlink building.conveyor 1
       2  sensor item.surge-alloy building.container @surge-alloy
       3  select control.conveyor greaterThan item.surge-alloy 250 true false
       4  control enabled building.conveyor control.conveyor 0 0 0
       5  end
```

判定:
备注:

### `e1e5af969b`

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

### `4ef21258f4`

- 出处：`mindustrytop-25773` · (314,228) · world-processor · 102 条语句
- 处理器自己的链接：`arc1`, `switch1`
- 被指行：语句序号 **0**
- 规则说：version gate: uses getblock -- needs build >= 157; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  setrate 100
       1  jump 6 notEqual arc1 null
       2  op add x @thisx 1
       3  set y @thisy
       4  setblock block @arc x y @sharded 0
       5  jump 0 always x false
       6  jump 11 notEqual switch1 null
       7  op add x @thisx 2
       8  set y @thisy
       9  setblock block @switch x y @sharded 0
      10  jump 0 always x false
      11  op add x @thisx 1
      12  op add y @thisy 1
      13  set floor @air
      14  sensor controlled arc1 @controlled
      15  jump 0 notEqual controlled @ctrlPlayer
      16  sensor e switch1 @enabled
      17  jump 38 equal e true
      18  sensor shooting arc1 @shooting
      19  jump 0 equal shooting false
      20  sensor x arc1 @shootX
      21  op add x x 0.5
      22  sensor y arc1 @shootY
      23  op add y y 0.5
      24  op floor fx x b
      25  op floor fy y b
      26  jump 36 lessThan fx 318
      27  jump 36 greaterThan fx 593
      28  op add c fx fy
      29  jump 36 lessThan c 530
      30  op sub d fx fy
      ... 下面还有 71 条语句
```

判定:
备注:

### `1ef638fe8b`

- 出处：`mindustrytop-25773` · (290,232) · world-processor · 43 条语句
- 处理器自己的链接：`arc1`
- 被指行：语句序号 **0**
- 规则说：version gate: uses getblock -- needs build >= 157; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  setrate 100
       1  jump 6 notEqual arc1 null
       2  op add x @thisx 1
       3  set y @thisy
       4  setblock block @arc x y @sharded 0
       5  jump 0 always x false
       6  op add x @thisx 1
       7  op add y @thisy 1
       8  getblock floor floor x y
       9  sensor controlled arc1 @controlled
      10  jump 0 notEqual controlled @ctrlPlayer
      11  sensor shooting arc1 @shooting
      12  jump 0 equal shooting false
      13  sensor x arc1 @shootX
      14  op add x x 0.5
      15  sensor y arc1 @shootY
      16  op add y y 0.5
      17  op floor fx x b
      18  op floor fy y b
      19  jump 42 lessThan fx 319
      20  jump 42 greaterThan fx 592
      21  op add c fx fy
      22  jump 42 lessThan c 532
      23  op sub d fx fy
      24  jump 42 lessThan d 33
      25  setblock floor floor fx fy @derelict 0
      26  op add fx fx 1
      27  setblock floor floor fx fy @derelict 0
      28  op add fy fy 1
      29  setblock floor floor fx fy @derelict 0
      30  op sub fx fx 1
      31  setblock floor floor fx fy @derelict 0
      32  op sub fx fx 1
      33  setblock floor floor fx fy @derelict 0
      34  op sub fy fy 1
      35  setblock floor floor fx fy @derelict 0
      36  op sub fy fy 1
      37  setblock floor floor fx fy @derelict 0
      38  op add fx fx 1
      39  setblock floor floor fx fy @derelict 0
      40  op add fx fx 1
      41  setblock floor floor fx fy @derelict 0
      42  wait 0.1
```

判定:
备注:

### `70271e088e`

- 出处：`mindustrytop-25773` · (314,232) · world-processor · 98 条语句
- 处理器自己的链接：`arc1`, `switch1`
- 被指行：语句序号 **0**
- 规则说：version gate: uses getblock -- needs build >= 157; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  setrate 100
       1  jump 6 notEqual arc1 null
       2  op add x @thisx 1
       3  set y @thisy
       4  setblock block @arc x y @sharded 0
       5  jump 0 always x false
       6  jump 11 notEqual switch1 null
       7  op add x @thisx 2
       8  set y @thisy
       9  setblock block @switch x y @sharded 0
      10  jump 0 always x false
      11  op add x @thisx 1
      12  op add y @thisy 1
      13  getblock ore floor x y
      14  sensor controlled arc1 @controlled
      15  jump 0 notEqual controlled @ctrlPlayer
      16  sensor e switch1 @enabled
      17  jump 36 equal e true
      18  sensor shooting arc1 @shooting
      19  jump 0 equal shooting false
      20  sensor x arc1 @shootX
      21  op add x x 0.5
      22  sensor y arc1 @shootY
      23  op add y y 0.5
      24  op floor fx x b
      25  op floor fy y b
      26  jump 34 lessThan fx 318
      27  jump 34 greaterThan fx 593
      28  op add c fx fy
      29  jump 34 lessThan c 530
      30  op sub d fx fy
      ... 下面还有 67 条语句
```

判定:
备注:

### `0f51e1fc6c`

- 出处：`mindustrytop-26075` · (5,10) · world-processor · 28 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **0**
- 规则说：version gate: uses format -- needs build >= 147; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  getflag 运行 "阶段4"
       1  jump 0 equal 运行 false
       2  set 开始波次 90
       3  set 总波次 90
       4  print "[red]阶段 4\n[white]波次:{0}/{1}"
       5  op sub 当前波次 @waveNumber 开始波次
       6  format 当前波次
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

### `3173ea00bf`

- 出处：`mindustrytop-26075` · (5,11) · world-processor · 30 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **0**
- 规则说：version gate: uses format -- needs build >= 147; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  getflag 运行 "阶段3"
       1  jump 0 equal 运行 false
       2  set 开始波次 35
       3  set 总波次 55
       4  print "[orange]阶段 3\n[white]波次:{0}/{1}"
       5  op sub 当前波次 @waveNumber 开始波次
       6  format 当前波次
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

### `f3529d202a`

- 出处：`mindustrytop-26075` · (5,12) · world-processor · 26 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **0**
- 规则说：version gate: uses format -- needs build >= 147; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  getflag 运行 "阶段2"
       1  jump 0 equal 运行 false
       2  set 开始波次 10
       3  set 总波次 25
       4  print "[yellow]阶段 2\n[white]波次:{0}/{1}"
       5  op sub 当前波次 @waveNumber 开始波次
       6  format 当前波次
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

### `f8114a42e3`

- 出处：`mindustrytop-26078` · (398,403) · world-processor · 49 条语句
- 处理器自己的链接：`node1`, `node2`
- 被指行：语句序号 **0**
- 规则说：version gate: uses select -- needs build >= 150; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  sensor 电力1 node1 @powerNetStored
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
      39  select sss greaterThanEq 电力1 1000000000 2 1
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

### `e673f5bc41`

- 出处：`mindustrytop-26053` · (56,4) · world-processor · 6 条语句
- 处理器自己的链接：`nucleus1`
- 被指行：语句序号 **0**
- 规则说：version gate: uses select -- needs build >= 150; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  getlink a 0
       1  lookup item b i
       2  op add i i 1
       3  select i strictEqual b null 0 i
       4  jump 1 equal b @surge-alloy
       5  setprop b a 0
```

判定:
备注:

### `49a416f17a`

- 出处：`mindustrytop-26053` · (57,4) · world-processor · 25 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **0**
- 规则说：version gate: uses getblock -- needs build >= 157; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  getblock block a 59 4
       1  getblock block b 58 4
       2  getblock block c 60 11
       3  getblock block d 53 8
       4  jump 9 notEqual a @mender
       5  jump 9 notEqual b @battery
       6  jump 9 notEqual c @tile-logic-display
       7  jump 9 notEqual d @shield-projector
       8  end
       9  setblock block @mender 59 4 2 0
      10  setblock block @battery 58 4 2 0
      11  setblock block @tile-logic-display 60 11 2 0
      12  setblock block @shield-projector 53 8 2 0
      13  jump 15 notEqual i 0
      14  print "你们红队真是该死了竟然连自己的修复器电池显示屏也拆了请你们不要再拆了"
      15  jump 17 notEqual i 1
      16  print "这已经是第二次了，你知道这意味着什么吗？"
      17  jump 19 notEqual i 2
      18  print "这已经是第3次了，这是最后一次警告了。"
      19  jump 21 notEqual i 3
      20  print "[red]气死我了！天天乱拆东西，真是该死啊！\n但我好像不能让你们死因为这样就要被骂了"
      21  jump 23 lessThan i 3
      22  print "算了，拆就拆吧反正能填充回去"
      23  message announce 3 @wait
      24  op add i i 1
```

判定:
备注:

### `cad12d189c`

- 出处：`mindustrytop-26053` · (73,4) · world-processor · 25 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **0**
- 规则说：version gate: uses getblock -- needs build >= 157; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  getblock block a 71 4
       1  getblock block b 72 4
       2  getblock block c 70 11
       3  getblock block d 77 8
       4  jump 9 notEqual a @mender
       5  jump 9 notEqual b @battery
       6  jump 9 notEqual c @tile-logic-display
       7  jump 9 notEqual d @shield-projector
       8  end
       9  setblock block @mender 71 4 1 0
      10  setblock block @battery 72 4 1 0
      11  setblock block @tile-logic-display 70 11 1 0
      12  setblock block @shield-projector 77 8 1 0
      13  jump 15 notEqual i 0
      14  print "你们黄队真是该死了竟然连自己的修复器电池显示屏护盾投影也拆了请你们不要再拆了"
      15  jump 17 notEqual i 1
      16  print "这已经是第二次了，你知道这意味着什么吗？"
      17  jump 19 notEqual i 2
      18  print "这已经是第3次了，这是最后一次警告了。"
      19  jump 21 notEqual i 3
      20  print "[red]气死我了！天天乱拆东西，真是该死啊！\n但我好像不能让你们死因为这样就要被骂了"
      21  jump 23 lessThan i 3
      22  print "算了，拆就拆吧反正能填充回去"
      23  message announce 3 @wait
      24  op add i i 1
```

判定:
备注:

### `a26d398f2e`

- 出处：`mindustrytop-24936` · (5,22) · world-processor · 44 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **0**
- 规则说：version gate: uses bullet -- needs build >= 157; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  fetch unitCount BOSS 2 0 @oxynoe
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
      36  bullet 子弹 @renale 16 X Y 角度 2 null 伤害 0.8 2 -1 -1
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

### `92276c35ea`

- 出处：`mindustrytop-24936` · (1,23) · world-processor · 45 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **0**
- 规则说：version gate: uses bullet -- needs build >= 157; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  fetch unitCount BOSS 2 0 @avert
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
      41  bullet 子弹 @renale 14 X 发Y 180 2 null 伤害 1 1.5 -1 -1
      42  jump 38 lessThanEq 次数 最大数量
      43  setprop @health 信标 0
      44  wait 0.5
```

判定:
备注:

### `11bfa747a7`

- 出处：`mindustrytop-24936` · (5,23) · world-processor · 77 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **0**
- 规则说：version gate: uses bullet -- needs build >= 157; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  fetch unitCount BOSS 2 0 @oxynoe
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
      28  makemarker shape 10001 BX BY flase
      29  setmarker stroke 10001 2倍 12 0
      30  setmarker radius 10001 大小 12 0
      ... 下面还有 46 条语句
```

判定:
备注:

### `4b9bc97632`

- 出处：`mindustrytop-25807` · (57,4) · world-processor · 24 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **0**
- 规则说：version gate: uses getblock -- needs build >= 157; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  getblock block a 59 4
       1  getblock block b 58 4
       2  getblock block c 60 11
       3  jump 7 notEqual a @mender
       4  jump 7 notEqual b @battery
       5  jump 7 notEqual c @tile-logic-display
       6  end
       7  setblock block @mender 59 4 2 0
       8  setblock block @battery 58 4 2 0
       9  setblock block @tile-logic-display 60 11 2 0
      10  jump 12 notEqual i 0
      11  print "你们红队真是该死了竟然连自己的修复器电池显示屏也拆了请你们不要再拆了"
      12  jump 14 notEqual i 1
      13  print "这已经是第二次了，你知道这意味着什么吗？"
      14  jump 16 notEqual i 2
      15  print "这已经是第3次了，这是最后一次警告了。"
      16  jump 22 notEqual i 3
      17  print "[red]死吧！"
      18  message announce 3 @wait
      19  spawnwave 7 101 false
      20  wait 0.5
      21  jump 19 always x false
      22  message announce 3 @wait
      23  op add i i 1
```

判定:
备注:

### `4e69ef15dd`

- 出处：`mindustrytop-25807` · (73,4) · world-processor · 24 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **0**
- 规则说：version gate: uses getblock -- needs build >= 157; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  getblock block a 71 4
       1  getblock block b 72 4
       2  getblock block c 70 11
       3  jump 7 notEqual a @mender
       4  jump 7 notEqual b @battery
       5  jump 7 notEqual c @tile-logic-display
       6  end
       7  setblock block @mender 71 4 1 0
       8  setblock block @battery 72 4 1 0
       9  setblock block @tile-logic-display 70 11 1 0
      10  jump 12 notEqual i 0
      11  print "你们黄队真是该死了竟然连自己的修复器电池显示屏也拆了请你们不要再拆了"
      12  jump 14 notEqual i 1
      13  print "这已经是第二次了，你知道这意味着什么吗？"
      14  jump 16 notEqual i 2
      15  print "这已经是第3次了，这是最后一次警告了。"
      16  jump 22 notEqual i 3
      17  print "[red]死吧！"
      18  message announce 3 @wait
      19  spawnwave 124 101 false
      20  wait 0.5
      21  jump 19 always x false
      22  message announce 3 @wait
      23  op add i i 1
```

判定:
备注:

### `bf285c315b`

- 出处：`mindustrytop-25807` · (62,16) · world-processor · 21 条语句
- 处理器自己的链接：`container1`
- 被指行：语句序号 **0**
- 规则说：version gate: uses select -- needs build >= 150; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  setrate 9999
       1  set 阶段 1
       2  set 队伍 2
       3  set 每轮时间 25
       4  set 每阶段轮数 3
       5  set 第1阶段每轮增加 45
       6  set 第2阶段每轮增加 55
       7  set 第3阶段每轮增加 65
       8  select 当前增加 equal 阶段 1 第1阶段每轮增加 当前增加
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

### `72d7dd61bf`

- 出处：`mindustrytop-26076` · (22,28) · world-processor · 51 条语句
- 处理器自己的链接：`switch1`
- 被指行：语句序号 **0**
- 规则说：version gate: uses bullet -- needs build >= 157; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  ubind @toxopid
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

### `e03230e4c9`

- 出处：`mindustrytop-26076` · (22,29) · world-processor · 48 条语句
- 处理器自己的链接：`switch1`, `wall1`, `wall2`
- 被指行：语句序号 **0**
- 规则说：version gate: uses bullet -- needs build >= 157; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  ubind @eclipse
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
      33  bullet result @fortress 0 Xrandom Yrandom rotrand t null 600 2 ltefsc sx sy
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

### `4a56fae2da`

- 出处：`mindustrytop-26076` · (41,396) · world-processor · 56 条语句
- 处理器自己的链接：`switch1`, `switch2`
- 被指行：语句序号 **0**
- 规则说：version gate: uses bullet -- needs build >= 157; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  ubind @reign
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
      38  bullet result @breach @carbide Xrandom Yrandom rotrand t null 1200 0.5 ltefsc sx sy
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

### `6f5c4ae84e`

- 出处：`mindustrytop-25736` · (289,1) · world-processor · 24 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **0**
- 规则说：version gate: uses getblock -- needs build >= 157; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  setrate 300
       1  set pr @clientUnit
       2  sensor unit pr @type
       3  jump 18 equal unit @nova
       4  jump 18 equal unit @pulsar
       5  jump 18 equal unit @quasar
       6  jump 18 equal unit @vela
       7  jump 18 equal unit @poly
       8  jump 18 equal unit @mega
       9  jump 18 equal unit @quad
      10  jump 18 equal unit @oct
      11  sensor x pr @x
      12  sensor y pr @y
      13  getblock floor floor x y
      14  jump 18 equal floor @empty
      15  jump 18 equal floor @darksand-water
      16  jump 18 equal floor @darksand
      17  jump 1 always x false
      18  sensor team pr @team
      19  fetch core core team 0 @conveyor
      20  sensor hx core @x
      21  sensor hy core @y
      22  setprop @x pr hx
      23  setprop @y pr hy
```

判定:
备注:

### `4920c04c6f`

- 出处：`mindustrytop-25736` · (294,3) · world-processor · 18 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **0**
- 规则说：version gate: uses getblock -- needs build >= 157; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  setrate 500
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
      13  jump 17 always x false
      14  setblock block @air x y @derelict 0
      15  sensor s a @size
      16  effect breakBlock x y s %ffaaff
      17  jump 5 always x false
```

判定:
备注:

### `5edacc5dba`

- 出处：`mindustrytop-25736` · (295,3) · world-processor · 18 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **0**
- 规则说：version gate: uses getblock -- needs build >= 157; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  setrate 500
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
      13  jump 17 always x false
      14  setblock block @air x y @derelict 0
      15  sensor s a @size
      16  effect breakBlock x y s %ffaaff
      17  jump 5 always x false
```

判定:
备注:

### `6081aa2914`

- 出处：`mindustrytop-25765` · (62,192) · world-processor · 5 条语句
- 处理器自己的链接：`scathe1`, `bastion1`
- 被指行：语句序号 **0**
- 规则说：version gate: uses select -- needs build >= 150; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  getlink b 1
       1  getlink B 0
       2  sensor D b @dead
       3  select E equal D 1 1 0
       4  control enabled B E 0 0 0
```

判定:
备注:

### `ae067afc1f`

- 出处：`mindustrytop-25765` · (252,293) · world-processor · 4 条语句
- 处理器自己的链接：`duct1`, `bastion1`
- 被指行：语句序号 **0**
- 规则说：version gate: uses select -- needs build >= 150; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  getlink b 1
       1  sensor D b @dead
       2  select E equal D 1 1 0
       3  control enabled duct1 E 0 0 0
```

判定:
备注:

### `87a84d543b`

- 出处：`mindustrytop-14962` · (0,98) · world-processor · 20 条语句
- 处理器自己的链接：`bastion1`, `bastion2`, `bastion3`, `bastion4`
- 被指行：语句序号 **0**
- 规则说：version gate: uses getblock -- needs build >= 157; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  setrate 1
       1  set limit 10
       2  getlink core i
       3  sensor team core @team
       4  fetch build build team limit @slag-centrifuge
       5  jump 9 notEqual build null
       6  op add i i 1
       7  op mod i i @links
       8  end
       9  sensor x build @x
      10  sensor y build @y
      11  setblock block @message x y team 0
      12  getblock block block x y
      13  jump 11 notEqual block @message
      14  getblock building message x y
      15  print "[red]核弹头造这么多干什么!!!"
      16  print "\n最多只能建 "
      17  print limit
      18  print "个.[]\n 造多了会被核打击"
      19  printflush message
```

判定:
备注:

### `944f9ef55e`

- 出处：`mindustrytop-26079` · (242,243) · world-processor · 506 条语句
- 处理器自己的链接：`arc1`, `cell1`
- 被指行：语句序号 **0**
- 规则说：version gate: uses getblock -- needs build >= 157; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  wait 1
       1  set cell:4:4 cell1
       2  jump 5 notEqual cell:4:4 null
       3  set cell:4:4 cell1
       4  end
       5  set SHARE_T1:10:4 0.3
       6  set SHARE_T2:11:4 0.25
       7  set SHARE_T3:12:4 0.25
       8  set SHARE_T4:13:4 0.2
       9  set SHARE_T5:14:4 0.1
      10  set attackInt:31:4 2
      11  set maxAttackPoints:32:4 2999
      12  write attackInt:31:4 cell:4:4 13
      13  write maxAttackPoints:32:4 cell:4:4 14
      14  set running:35:4 0
      15  set arc1:36:4 arc1
      16  set basicPoints:37:4 1
      17  set maxPoints:38:4 25
      18  set coreWidth:40:4 10
      19  read &t0 cell:4:4 20
      20  jump 19 equal &t0 0
      21  read different:42:4 cell:4:4 20
      22  setrate 200
      23  set launch:46:4 0
      24  jump 34 notEqual launch:46:4 0
      25  set launch:46:4 1
      26  read &t1 cell:4:4 6
      27  jump 30 equal &t1 0
      28  read seed:39:4 cell:4:4 6
      29  jump 34 always x false
      30  op rand &t2 65536000 b
      ... 下面还有 475 条语句
```

判定:
备注:

### `589d4c1bd8`

- 出处：`mindustrytop-26079` · (244,243) · world-processor · 113 条语句
- 处理器自己的链接：`cell1`, `vault1`
- 被指行：语句序号 **0**
- 规则说：version gate: uses getblock -- needs build >= 157; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  wait 1
       1  set vault:3:4 vault1
       2  set maxPoint:4:4 998
       3  set basicPoints:5:4 1
       4  set maxPoints:6:4 25
       5  print "[ACID]等待选择难度中..."
       6  message mission 3 @wait
       7  read &t0 cell1 20
       8  jump 7 equal &t0 0
       9  read different:17:4 cell1 20
      10  setrate 999
      11  read &t1 cell1 11
      12  jump 18 equal &t1 0
      13  read &t2 cell1 10
      14  read &t3 cell1 11
      15  op sub &t4 &t2 &t3
      16  write &t4 cell1 10
      17  write 0 cell1 11
      18  sensor &t2 vault:3:4 @copper
      19  read &t3 cell1 20
      20  op mul &t4 200 &t3
      21  op greaterThanEq &t5 &t2 &t4
      22  sensor &t6 vault:3:4 @lead
      23  read &t7 cell1 20
      24  op mul &t8 200 &t7
      25  op greaterThanEq &t9 &t6 &t8
      26  op land &t10 &t5 &t9
      27  jump 43 equal &t10 0
      28  read &t11 cell1 10
      29  jump 43 greaterThanEq &t11 maxPoint:4:4
      30  sensor &t12 vault:3:4 @copper
      ... 下面还有 82 条语句
```

判定:
备注:

### `22001e9202`

- 出处：`mindustrytop-25872` · (24,69) · logic-processor · 144 条语句
- 处理器自己的链接：`board`, `cell1`
- 被指行：语句序号 **0**
- 规则说：version gate: uses op ushr -- needs build >= 150; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  op idiv _0 3 64
       1  op mod _1 3 64
       2  op shl _2 1 _1
       3  op greaterThanEq _3 3 0
       4  op lessThan _4 3 128
       5  op land _5 _3 _4
       6  op mul _2 _2 _5
       7  op mul _0 _0 _5
       8  op add _6 0 _0
       9  read _7 cell1 _6
      10  op or _7 _7 _2
      11  set __ls_func___ls_builtin_bwrite_mem cell1
      12  set __ls_func___ls_builtin_bwrite_addr _6
      13  set __ls_func___ls_builtin_bwrite_value _7
      14  set __ls_func___ls_builtin_bwrite_ret @counter
      15  op add __ls_func___ls_builtin_bwrite_ret __ls_func___ls_builtin_bwrite_ret 2
      16  jump __ls_func___ls_builtin_bwrite_entry always x false
      17  set r1 __ls_func___ls_builtin_bwrite_result
      18  op idiv _0 5 64
      19  op mod _1 5 64
      20  op shl _2 1 _1
      21  op greaterThanEq _3 5 0
      22  op lessThan _4 5 128
      23  op land _5 _3 _4
      24  op mul _2 _2 _5
      25  op mul _0 _0 _5
      26  op add _6 0 _0
      27  read _7 cell1 _6
      28  op or _7 _7 _2
      29  set __ls_func___ls_builtin_bwrite_mem cell1
      30  set __ls_func___ls_builtin_bwrite_addr _6
      ... 下面还有 113 条语句
```

判定:
备注:

### `62a204ddeb`

- 出处：`mindustrytop-20445` · (7,0) · world-processor · 25 条语句
- 处理器自己的链接：`cell1`
- 被指行：语句序号 **0**
- 规则说：version gate: uses format -- needs build >= 147; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  setrate 30
       1  op idiv min @waveTime 60
       2  op mod sec @waveTime 60
       3  op idiv sec sec 1
       4  read c cell1 0
       5  jump 16 notEqual @clientLocale "zh_CN"
       6  print "[gold]资金： {0}\n[red]波次：\n {1}/150\n({2}:{3}{4}秒)"
       7  format c
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

### `d17ae72cb8`

- 出处：`mindustrytop-20445` · (15,0) · world-processor · 70 条语句
- 处理器自己的链接：`processor1`, `processor2`
- 被指行：语句序号 **0**
- 规则说：version gate: uses format -- needs build >= 147; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  set readType "Turret"
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
      15  format type
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
      ... 下面还有 39 条语句
```

判定:
备注:

### `bc4749f8dd`

- 出处：`mindustrytop-20445` · (16,0) · world-processor · 70 条语句
- 处理器自己的链接：`processor1`, `processor2`
- 被指行：语句序号 **0**
- 规则说：version gate: uses format -- needs build >= 147; on anything older the line is replaced by noop and silently does nothing

```
>>>>   0  set readType "Drill"
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
      15  format type
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
      ... 下面还有 39 条语句
```

判定:
备注:

## 规则 `undefined-var-is-not-automatically-an-error`

### `992432075a`

- 出处：`mindustrytop-25559` · (590,11) · world-processor · 6 条语句
- 处理器自己的链接：`message1`
- 被指行：语句序号 **5**
- 规则说：`unmoving` is read here but is never assigned anywhere in this program (and is not a link or built-in)

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

### `09539ae8b6`

- 出处：`mindustrytop-25559` · (591,11) · world-processor · 6 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **5**
- 规则说：`unmoving` is read here but is never assigned anywhere in this program (and is not a link or built-in)

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

### `96bc4f4170`

- 出处：`mindustrytop-25559` · (592,11) · world-processor · 6 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **5**
- 规则说：`unmoving` is read here but is never assigned anywhere in this program (and is not a link or built-in)

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

### `eb97a7e0d7`

- 出处：`mindustrytop-24936` · (1,29) · world-processor · 61 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **23**
- 规则说：`A` is read here but is never assigned anywhere in this program (and is not a link or built-in)

```
       0  fetch unitCount BOSS 2 0 @avert
       1  jump 10 greaterThanEq BOSS 1
       2  fetch unit 信标 1 0 @oct
       3  setprop @health 信标 0
       4  fetch unit 无敌 2 0 @oct
       5  sensor F 无敌 @flag
       6  jump 8 notEqual F 0
       7  setprop @health 无敌 0
       8  wait 0.3
       9  end
      10  fetch unit BOSS 2 0 @avert
      11  setrate 20
      12  getflag 难1 "普通"
      13  getflag 难2 "困难"
      14  jump 18 equal 难1 1
      15  jump 20 equal 难2 1
      16  set 难度 0
      17  jump 21 always x false
      18  set 难度 1
      19  jump 21 always x false
      20  set 难度 2
      21  op mul 难度倍率 难度 200
      22  op add 难度护盾 难度倍率 400
>>>>  23  fetch unitCount 信标数量 1 A @oct
      24  op add 时间 时间 1
      25  wait 1
      26  jump 0 lessThanEq 时间 60
      27  jump 51 notEqual 信标数量 0
      28  op rand 随机方位 4 b
      29  op floor 随机方位 随机方位 b
      30  jump 36 equal 随机方位 1
      31  jump 39 equal 随机方位 2
      32  jump 42 equal 随机方位 3
      33  spawn @oct 241 112 90 1 信标 true
      34  spawn @oct 308 69 90 2 无敌 true
      35  jump 44 always x false
      36  spawn @oct 213 85 90 1 信标 true
      37  spawn @oct 308 69 90 2 无敌 true
      38  jump 44 always x false
      39  spawn @oct 241 25 90 1 信标 true
      40  spawn @oct 308 69 90 2 无敌 true
      41  jump 44 always x false
      42  spawn @oct 213 53 90 1 信标 true
      43  spawn @oct 308 69 90 2 无敌 true
      44  setprop @speed 信标 0
      45  setprop @speed 无敌 0
      46  setprop @shield 信标 难度护盾
      47  setprop @shield 无敌 20000000
      48  op mul 难度时间 难度 10
      49  op add 最大持续时间 难度时间 25
      50  wait 1
      51  fetch unit 信标 1 0 @oct
      52  sensor 盾 信标 @shield
      53  op sub 最大持续时间 最大持续时间 1
      ... 下面还有 7 条语句
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

### `fee7c06d71`

- 出处：`mindustrytop-25736` · (300,1) · world-processor · 69 条语句
- 处理器自己的链接：（无）
- 被指行：语句序号 **13**
- 规则说：`fast` is read here but is never assigned anywhere in this program (and is not a link or built-in)

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

### `2a8684994a`

- 出处：`mindustrytop-14962` · (201,2) · world-processor · 36 条语句
- 处理器自己的链接：`bastion1`
- 被指行：语句序号 **30**
- 规则说：`sapped` is read here but is never assigned anywhere in this program (and is not a link or built-in)

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

### `630158f92a`

- 出处：`mindustrytop-14962` · (201,2) · world-processor · 36 条语句
- 处理器自己的链接：`bastion1`
- 被指行：语句序号 **34**
- 规则说：`sapped` is read here but is never assigned anywhere in this program (and is not a link or built-in)

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

