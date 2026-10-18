# 逐条待审清单（168 条）

`python tools/review.py show <id>` 看上下文；`ok`/`bad`/`unsure` 判它。

## `jump-to-jump-chain` — 45 条

| id | 级别 | 位置 | 行 | 源码 | 判定 |
|---|---|---|---|---|---|
| `f2a6e68568` | INFO | mindustrytop-25774:343,102 | 8 | `jump 13 equal temp.i temp.j` |  |
| `0f39a633fc` | INFO | mindustrytop-25774:127,114 | 4 | `jump 6 greaterThan silicon 70` |  |
| `65bd4e8551` | INFO | mindustrytop-25774:127,114 | 7 | `jump 9 greaterThan phase-fabric 70` |  |
| `e3eb5bf3fc` | INFO | mindustrytop-25773:314,228 | 2 | `jump 6 notEqual arc1 null` |  |
| `43b9a11ea0` | INFO | mindustrytop-25773:314,228 | 40 | `jump 46 equal shooting true` |  |
| `3e47407d7a` | INFO | mindustrytop-25773:314,228 | 47 | `jump 52 notEqual sx -1` |  |
| `973ca9d7bc` | INFO | mindustrytop-26078:398,403 | 5 | `jump 7 lessThanEq 电力1 100000` |  |
| `4474670106` | INFO | mindustrytop-26078:398,403 | 18 | `jump 20 lessThanEq 电力2 100000` |  |
| `c7bd1b6483` | INFO | mindustrytop-25559:350,269 | 74 | `jump 78 greaterThan drd 7.5` |  |
| `e1a19d03a7` | INFO | mindustrytop-25559:350,269 | 75 | `jump 78 equal strd 0` |  |
| `0f65e5ab65` | INFO | mindustrytop-25559:352,269 | 92 | `jump 93 lessThan tr 360` |  |
| `5c038f161e` | INFO | mindustrytop-26053:57,4 | 14 | `jump 15 notEqual i 0` |  |
| `38711ac48e` | INFO | mindustrytop-26053:57,4 | 16 | `jump 17 notEqual i 1` |  |
| `8e5868e707` | INFO | mindustrytop-26053:57,4 | 18 | `jump 19 notEqual i 2` |  |
| `41508e69db` | INFO | mindustrytop-24936:1,25 | 47 | `jump 50 greaterThanEq 正距离 8` |  |
| `b9464012a5` | INFO | mindustrytop-24936:5,26 | 51 | `jump 53 lessThanEq 绝对X 1` |  |
| `653d607ec0` | INFO | mindustrytop-24936:1,31 | 145 | `jump 150 notEqual 难度 2` |  |
| `f4cd8f1d35` | INFO | mindustrytop-25807:57,4 | 11 | `jump 12 notEqual i 0` |  |
| `94c575ce0a` | INFO | mindustrytop-25807:57,4 | 13 | `jump 14 notEqual i 1` |  |
| `49992ac988` | INFO | mindustrytop-25807:57,4 | 15 | `jump 16 notEqual i 2` |  |
| `88777fd5eb` | INFO | mindustrytop-26076:22,28 | 31 | `jump 32 strictEqual e 1` |  |
| `7f7dfe6a32` | INFO | mindustrytop-26076:22,29 | 30 | `jump 31 strictEqual e 1` |  |
| `81b0dfd204` | INFO | mindustrytop-26076:41,395 | 43 | `jump 44 strictEqual e 1` |  |
| `3ae6f161df` | INFO | mindustrytop-25736:299,4 | 19 | `jump 20 equal core1 1` |  |
| `b78a394aa4` | INFO | mindustrytop-25736:299,4 | 21 | `jump 19 equal core2 0` |  |
| `4bdaddcddd` | INFO | mindustrytop-25736:300,4 | 19 | `jump 20 equal core1 1` |  |
| `b31c44e966` | INFO | mindustrytop-25765:3,14 | 24 | `jump 26 greaterThanEq a 0.8m` |  |
| `4f7dc5c920` | INFO | mindustrytop-14962:0,0 | 5 | `jump 6 equal 存在 0` |  |
| `8b0ec0ace2` | INFO | mindustrytop-14962:2,0 | 6 | `jump 7 equal 生命 0` |  |
| `79c2419d64` | INFO | mindustrytop-14962:2,0 | 15 | `jump 16 greaterThanEq b 0` |  |
| `c6035a65a9` | INFO | mindustrytop-25680:28,31 | 28 | `jump 29 notEqual 铜 0` |  |
| `28e756641c` | INFO | mindustrytop-25680:28,31 | 30 | `jump 31 notEqual 铅 0` |  |
| `f4583cc0f4` | INFO | mindustrytop-25680:28,31 | 32 | `jump 33 notEqual 沙 0` |  |
| `8ce9698a21` | INFO | mindustrytop-26079:227,242 | 55 | `jump 56 equal e1:27:12 0` |  |
| `85942479f8` | INFO | mindustrytop-26079:227,242 | 57 | `jump 58 equal e2:28:12 0` |  |
| `4538c47961` | INFO | mindustrytop-26079:227,242 | 59 | `jump 60 equal e3:29:12 0` |  |
| `ae2a992250` | INFO | mindustrytop-25872:24,15 | 10 | `jump 9 equal __ls_cond_4 0` |  |
| `744c7f0eef` | INFO | mindustrytop-25872:81,15 | 3 | `jump 4 greaterThan a 0` |  |
| `370ed6bf8f` | INFO | mindustrytop-25872:81,33 | 14 | `jump 46 equal @unit null` |  |
| `86ad30d4ed` | INFO | mindustrytop-20445:3,0 | 13 | `jump 15 greaterThanEq shield 3000` |  |
| `074cd4cc3e` | INFO | mindustrytop-20445:65,0 | 12 | `jump 39 equal type @shock-mine` |  |
| `b33707c635` | INFO | mindustrytop-20445:65,0 | 13 | `jump 41 equal size 1` |  |
| `1e44920d54` | INFO | mindustrytop-26083:95,3 | 3 | `jump 4 notEqual 钻头编号 0` |  |
| `b9894a438d` | INFO | mindustrytop-26083:95,3 | 5 | `jump 6 notEqual 钻头编号 1` |  |
| `27e8bd6440` | INFO | mindustrytop-26083:95,3 | 7 | `jump 8 notEqual 钻头编号 2` |  |

> target 13 is itself a jump

## `version-gate` — 34 条

| id | 级别 | 位置 | 行 | 源码 | 判定 |
|---|---|---|---|---|---|
| `b0566c28e7` | INFO | mindustrytop-25774:125,137 | 0 | `` |  |
| `0dc6296964` | INFO | mindustrytop-25774:413,408 | 0 | `` |  |
| `e1e5af969b` | INFO | mindustrytop-25774:3,489 | 0 | `` |  |
| `4ef21258f4` | INFO | mindustrytop-25773:314,228 | 0 | `` |  |
| `1ef638fe8b` | INFO | mindustrytop-25773:290,232 | 0 | `` |  |
| `70271e088e` | INFO | mindustrytop-25773:314,232 | 0 | `` |  |
| `0f51e1fc6c` | INFO | mindustrytop-26075:5,10 | 0 | `` |  |
| `3173ea00bf` | INFO | mindustrytop-26075:5,11 | 0 | `` |  |
| `f3529d202a` | INFO | mindustrytop-26075:5,12 | 0 | `` |  |
| `f8114a42e3` | INFO | mindustrytop-26078:398,403 | 0 | `` |  |
| `e673f5bc41` | INFO | mindustrytop-26053:56,4 | 0 | `` |  |
| `49a416f17a` | INFO | mindustrytop-26053:57,4 | 0 | `` |  |
| `cad12d189c` | INFO | mindustrytop-26053:73,4 | 0 | `` |  |
| `a26d398f2e` | INFO | mindustrytop-24936:5,22 | 0 | `` |  |
| `92276c35ea` | INFO | mindustrytop-24936:1,23 | 0 | `` |  |
| `11bfa747a7` | INFO | mindustrytop-24936:5,23 | 0 | `` |  |
| `4b9bc97632` | INFO | mindustrytop-25807:57,4 | 0 | `` |  |
| `4e69ef15dd` | INFO | mindustrytop-25807:73,4 | 0 | `` |  |
| `bf285c315b` | INFO | mindustrytop-25807:62,16 | 0 | `` |  |
| `72d7dd61bf` | INFO | mindustrytop-26076:22,28 | 0 | `` |  |
| `e03230e4c9` | INFO | mindustrytop-26076:22,29 | 0 | `` |  |
| `4a56fae2da` | INFO | mindustrytop-26076:41,396 | 0 | `` |  |
| `6f5c4ae84e` | INFO | mindustrytop-25736:289,1 | 0 | `` |  |
| `4920c04c6f` | INFO | mindustrytop-25736:294,3 | 0 | `` |  |
| `5edacc5dba` | INFO | mindustrytop-25736:295,3 | 0 | `` |  |
| `6081aa2914` | INFO | mindustrytop-25765:62,192 | 0 | `` |  |
| `ae067afc1f` | INFO | mindustrytop-25765:252,293 | 0 | `` |  |
| `87a84d543b` | INFO | mindustrytop-14962:0,98 | 0 | `` |  |
| `944f9ef55e` | INFO | mindustrytop-26079:242,243 | 0 | `` |  |
| `589d4c1bd8` | INFO | mindustrytop-26079:244,243 | 0 | `` |  |
| `22001e9202` | INFO | mindustrytop-25872:24,69 | 0 | `` |  |
| `62a204ddeb` | INFO | mindustrytop-20445:7,0 | 0 | `` |  |
| `d17ae72cb8` | INFO | mindustrytop-20445:15,0 | 0 | `` |  |
| `bc4749f8dd` | INFO | mindustrytop-20445:16,0 | 0 | `` |  |

> version gate: uses format -- needs build >= 147; on anything older the line is replaced by noop and silently does nothing

## `unary-op-extra-operand` — 34 条

| id | 级别 | 位置 | 行 | 源码 | 判定 |
|---|---|---|---|---|---|
| `c5cc0d4a2a` | INFO | mindustrytop-25774:125,137 | 72 | `op sqrt endl.set n.pad 1` |  |
| `c8ba30ceae` | INFO | mindustrytop-25774:125,137 | 77 | `op rand pad.instruct pad.volum n.pad` |  |
| `ce3727432e` | INFO | mindustrytop-25774:4,497 | 5 | `op cos cos.num temp.i b` |  |
| `26de45439b` | INFO | mindustrytop-25773:314,228 | 25 | `op floor fx x b` |  |
| `c6dee039ec` | INFO | mindustrytop-25773:314,228 | 26 | `op floor fy y b` |  |
| `d77a04a851` | INFO | mindustrytop-25773:314,228 | 66 | `op cos x+ angle 90` |  |
| `8f04158cf1` | INFO | mindustrytop-26075:5,10 | 12 | `op round 剩余时间 @waveTime 1` |  |
| `2f6a05a2eb` | INFO | mindustrytop-26075:5,11 | 12 | `op round 剩余时间 @waveTime 1` |  |
| `bffc83e2e8` | INFO | mindustrytop-26075:5,12 | 12 | `op round 剩余时间 @waveTime 1` |  |
| `7871ba3122` | INFO | mindustrytop-25559:350,269 | 48 | `op cos cx rot3 b` |  |
| `4b1e3fbe22` | INFO | mindustrytop-25559:350,269 | 49 | `op sin sy rot3 b` |  |
| `20907461ed` | INFO | mindustrytop-25559:352,269 | 16 | `op cos cx0 tr b` |  |
| `5ade4a5567` | INFO | mindustrytop-26053:63,17 | 33 | `op round s1 s1 @second` |  |
| `d50338bb3c` | INFO | mindustrytop-24936:1,22 | 35 | `op floor 整差 差 差Y` |  |
| `c6af4de601` | INFO | mindustrytop-24936:1,22 | 39 | `op atan 角度 除数 差Y` |  |
| `0199a981b0` | INFO | mindustrytop-24936:1,22 | 48 | `op sin 抛物线Y 抛物线 2` |  |
| `f488df1326` | INFO | mindustrytop-26076:22,28 | 10 | `op rand xA 1 sx` |  |
| `980569495a` | INFO | mindustrytop-26076:22,28 | 11 | `op rand xR -1 sx` |  |
| `9fcb6965fc` | INFO | mindustrytop-26076:22,28 | 12 | `op rand yA 1 sx` |  |
| `7aa787332d` | INFO | mindustrytop-25736:300,1 | 51 | `op cos sin j b` |  |
| `5859319d72` | INFO | mindustrytop-25736:300,1 | 52 | `op sin cos j b` |  |
| `8d2d4c5613` | INFO | mindustrytop-25736:223,8 | 34 | `op sin sin j b` |  |
| `4e980331bd` | INFO | mindustrytop-14962:0,0 | 11 | `op rand c 10 b` |  |
| `ac9c06e2b9` | INFO | mindustrytop-14962:0,0 | 12 | `op rand b c b` |  |
| `a8849b5033` | INFO | mindustrytop-14962:2,0 | 12 | `op rand b 8 b` |  |
| `da56368073` | INFO | mindustrytop-25680:28,31 | 69 | `op rand r 54 b` |  |
| `3981e4cd15` | INFO | mindustrytop-26079:242,243 | 31 | `op rand &t2 65536000 b` |  |
| `0463ebc023` | INFO | mindustrytop-26079:242,243 | 32 | `op floor &t3 &t2 b` |  |
| `b4e3cb27dd` | INFO | mindustrytop-26079:242,243 | 78 | `op rand &t0:done:150:0 100 b` |  |
| `20157e8ebe` | INFO | mindustrytop-25872:5,33 | 10 | `op sqrt diag _0 0` |  |
| `fc67e37c9d` | INFO | mindustrytop-25872:43,69 | 54 | `op abs __ls_mp_h __ls_func___ls_builtin_mapset_key 0` |  |
| `27501b22bb` | INFO | mindustrytop-25872:43,69 | 103 | `op abs __ls_mp_h __ls_func___ls_builtin_mapget_key 0` |  |
| `bd0124094c` | INFO | mindustrytop-20445:0,25 | 13 | `op cos cos angle b` |  |
| `6a5a26f559` | INFO | mindustrytop-20445:0,25 | 14 | `op sin sin angle b` |  |

> `op sqrt` reads 1 operand(s); the extra 1 token(s) are parsed and then ignored

## `undefined-var-is-not-automatically-an-error` — 26 条

| id | 级别 | 位置 | 行 | 源码 | 判定 |
|---|---|---|---|---|---|
| `f19ca18770` | ERR | mindustrytop-25559:590,11 | 6 | `status false unmoving @unit 0.1` |  |
| `7d59a39468` | ERR | mindustrytop-25559:591,11 | 6 | `status false unmoving @unit 0.1` |  |
| `8a60f332ba` | ERR | mindustrytop-25559:592,11 | 6 | `status false unmoving @unit 0.1` |  |
| `73019bc4f6` | ERR | mindustrytop-26053:64,17 | 33 | `sensor e b @surge-alloy` |  |
| `000c12d99a` | ERR | mindustrytop-26053:66,29 | 1 | `op sub dx sx @thisx` |  |
| `349370b924` | ERR | mindustrytop-26053:66,29 | 2 | `op sub dy sy @thisy` |  |
| `8fc229862e` | ERR | mindustrytop-24936:7,22 | 28 | `makemarker shape ID X Y flase` |  |
| `d09cbb8c33` | ERR | mindustrytop-24936:5,23 | 29 | `makemarker shape 10001 BX BY flase` |  |
| `b3e7346569` | ERR | mindustrytop-24936:1,29 | 24 | `fetch unitCount 信标数量 1 A @oct` |  |
| `6ada69d883` | ERR | mindustrytop-25807:63,27 | 4 | `op add id @thisx temp` |  |
| `9b7e61fa92` | ERR | mindustrytop-26076:22,28 | 28 | `op add rotR rota rotr` |  |
| `73f90a6505` | ERR | mindustrytop-26076:26,28 | 7 | `jump 3 equal n old` |  |
| `845f9c7b7e` | ERR | mindustrytop-25736:300,1 | 14 | `status false fast 结果 1e5` |  |
| `ef89f5f001` | ERR | mindustrytop-25736:226,11 | 13 | `op sub item2 item 10000` |  |
| `1ce9da38fa` | ERR | mindustrytop-14962:95,0 | 42 | `jump 43 greaterThanEq 数量 sl` |  |
| `f828062b82` | ERR | mindustrytop-14962:201,2 | 31 | `status false sapped unit 10` |  |
| `3fbbd06428` | ERR | mindustrytop-14962:201,2 | 35 | `status true sapped unit 10` |  |
| `018acfaf3f` | ERR | mindustrytop-25939:51,6 | 1 | `op sub dx sx @thisx` |  |
| `898dd3ea83` | ERR | mindustrytop-25939:51,6 | 2 | `op sub dy sy @thisy` |  |
| `eac12f47d8` | ERR | mindustrytop-25939:51,6 | 4 | `op add id @thisx temp` |  |
| `8732ccf0d5` | INFO | mindustrytop-25680:28,31 | 2 | `print 咕咕着陆台更新器v1.3` |  |
| `e51a5f2eae` | INFO | mindustrytop-25680:28,31 | 3 | `print 更新时间2026/4/17` |  |
| `73d4c4dc74` | INFO | mindustrytop-25680:28,31 | 6 | `print 0为关闭，1为开启` |  |
| `a97a9918f3` | INFO | mindustrytop-20445:53,0 | 18 | `print 无脑遍历所有单位的智障ai系统` |  |
| `3283154c08` | ERR | mindustrytop-20445:59,0 | 15 | `setprop @cryofluid 炮2 41` |  |
| `39af3dbf0c` | ERR | mindustrytop-20445:59,0 | 16 | `setprop @surge-alloy 炮2 41` |  |

> `unmoving` is read here but is never assigned anywhere in this program (and is not a link or built-in)

## `link-name-not-bound` — 13 条

| id | 级别 | 位置 | 行 | 源码 | 判定 |
|---|---|---|---|---|---|
| `e70b3ab984` | WARN | mindustrytop-25774:127,114 | 1 | `sensor silicon vault1 @silicon` |  |
| `0f68bc9b3e` | WARN | mindustrytop-25774:127,114 | 2 | `sensor phase-fabric vault1 @phase-fabric` |  |
| `6df3a8c908` | WARN | mindustrytop-25774:127,114 | 3 | `sensor surge-alloy vault1 @surge-alloy` |  |
| `7ef146fa2f` | WARN | mindustrytop-25559:389,444 | 19 | `sensor rx1 route1 @x` |  |
| `607848b8a5` | WARN | mindustrytop-25559:389,444 | 20 | `sensor ry1 route1 @y` |  |
| `744be23415` | WARN | mindustrytop-25559:390,445 | 127 | `setmarker remove id6 0 0 0` |  |
| `13c0289127` | WARN | mindustrytop-26053:60,12 | 3 | `sensor result block1 @surge-alloy` |  |
| `2a0fbd9c01` | WARN | mindustrytop-26053:128,27 | 6 | `jump 1 equal a cell2` |  |
| `b4f1dafbfb` | WARN | mindustrytop-26053:65,57 | 38 | `print arial1102` |  |
| `617148a337` | WARN | mindustrytop-20445:15,0 | 50 | `stringmerge write1 tname ".type"` |  |
| `160c8db48e` | WARN | mindustrytop-20445:15,0 | 51 | `stringmerge write2 tname ".category"` |  |
| `665d4a3690` | WARN | mindustrytop-20445:15,0 | 52 | `stringmerge write3 tname ".cost"` |  |
| `157ea038c4` | WARN | mindustrytop-26083:95,2 | 89 | `sensor result block1 @foreshadow` |  |

> `vault1` is shaped like a block link but this processor has no such link (it has: driver1, pad1)

## `dead-polarity` — 11 条

| id | 级别 | 位置 | 行 | 源码 | 判定 |
|---|---|---|---|---|---|
| `063cef3386` | SUSPECT | mindustrytop-25774:139,142 | 2 | `jump 5 notEqual 单位存亡 1` |  |
| `c1f733c795` | SUSPECT | mindustrytop-25559:351,272 | 21 | `jump 18 notEqual dead 1` |  |
| `24fa85543b` | SUSPECT | mindustrytop-25559:427,437 | 131 | `jump 107 notEqual d 1` |  |
| `38ee45f085` | SUSPECT | mindustrytop-25559:393,445 | 8 | `jump 6 notEqual dead 1` |  |
| `331f6153c9` | SUSPECT | mindustrytop-25765:5,16 | 3 | `jump 0 notEqual D 1` |  |
| `c4a6b7ec14` | SUSPECT | mindustrytop-25765:5,17 | 3 | `jump 0 notEqual D 1` |  |
| `9ccac461e1` | SUSPECT | mindustrytop-25872:81,33 | 22 | `jump 9 notEqual __ls_ub_d_1 0` |  |
| `92f0de3e7e` | SUSPECT | mindustrytop-25872:81,33 | 73 | `jump 67 notEqual __ls_ub_d_4 0` |  |
| `05c7b82d28` | SUSPECT | mindustrytop-25872:81,33 | 91 | `jump 70 notEqual __ls_ub_d_4 0` |  |
| `bd2f4e3651` | SUSPECT | mindustrytop-20445:4,0 | 39 | `jump 53 notEqual coreDead 1` |  |
| `62f4e0ba84` | SUSPECT | mindustrytop-20445:0,24 | 2 | `jump 0 notEqual dead 1` |  |

> `单位存亡` holds @dead (1 = DEAD). Checking `notEqual` continues only while ALIVE; to rebind when dead use `equal`

## `constant-null-guard` — 4 条

| id | 级别 | 位置 | 行 | 源码 | 判定 |
|---|---|---|---|---|---|
| `47438109f0` | WARN | mindustrytop-25774:143,138 | 10 | `jump 18 equal colour ender` |  |
| `ee9ba705b7` | WARN | mindustrytop-25774:143,138 | 13 | `jump 18 equal colour ender` |  |
| `fa7c9ba66d` | WARN | mindustrytop-25680:177,140 | 31 | `jump -1 equal colour ender` |  |
| `4a7f30fcfb` | WARN | mindustrytop-25680:178,140 | 6 | `jump 7 equal colour ender` |  |

> `colour` is never assigned, so this comparison is constant: an unset variable is 0 and `null` reads as 0, so only `===` tells null from 0 (a constant branch is often a signature)

## `printflush-clears-buffer` — 1 条

| id | 级别 | 位置 | 行 | 源码 | 判定 |
|---|---|---|---|---|---|
| `f813e96850` | INFO | mindustrytop-25774:125,137 | 25 | `printflush Notification` |  |

> `Notification` is never assigned, so this `printflush` has no valid message block -- and that is NOT a no-op: PrintFlushI clears the print buffer unconditionally (LExecutor.java:1178), so everything queued by `print` is 

