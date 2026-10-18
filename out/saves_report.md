# 存档里的逻辑：一次全量体检

- 存档 1421 个（v7 289 / v8 149 / v9 61 / v10 45 / v11 877），全部解析成功
- 处理器 103,787 个
- 去重后不同的程序 **4,366** 份（99,421 份是完全相同代码的副本，占 95.8%）
- 发现 10,544 条：ERR 839 / INFO 6,302 / SUSPECT 97 / WARN 3,306

## 最常被复制的程序

| 副本数 | 语句 | 首次出现 |
| --- | --- | --- |
| 9,699 | 22 | 236.msav:802,162 |
| 7,649 | 16 | 556.msav:422,401 |
| 1,696 | 1 | 131.msav:418,407 |
| 1,566 | 29 | 131.msav:545,345 |
| 1,502 | 16 | 538.msav:523,440 |
| 1,481 | 11 | 131.msav:396,403 |
| 1,269 | 41 | 131.msav:402,408 |
| 1,248 | 10 | 131.msav:569,428 |

## 规则命中表（按规则归并）

| 次数 | 级别 | 规则 |
| --- | --- | --- |
| 5,194 | INFO | target N is itself a jump |
| 2,254 | WARN | `X` given N args, expects N |
| 918 | WARN | `X` is shaped like a block link but this processor has no such link |
| 814 | ERR | `X` is read here but is never assigned anywhere in this program (and is not a link or built-in) |
| 462 | INFO | version gate: uses getblock |
| 394 | INFO | `X` is never assigned |
| 97 | SUSPECT | `X` holds @dead. Checking `X` continues only while ALIVE |
| 95 | INFO | `X` is never assigned, but the destination `X` is never read either |
| 73 | WARN | `X` sits in a parameter slot this instruction never reads |
| 68 | INFO | version gate: uses format |
| 55 | WARN | `X` is never assigned, so this comparison is constant: an unset variable is N and `X` reads as N, so only `X` tells null from N |
| 38 | INFO | `X` is never assigned, so this `X` has no valid message block |
| 38 | INFO | version gate: uses select |
| 11 | ERR | this loop can never leave: `X` or a `X` command hands the bound unit to this processor (UnitControlI.checkLogicAI sets the controller), so `X` equals `X` from the first pass on and the guard is true forever |
| 10 | INFO | outBuild discarded |
| 9 | ERR | `X` is the game's InvalidStatement |
| 4 | WARN | N noop line(s) = InvalidStatement (LParser.java:N-N). Three causes: a statement from a NEWER build, a privileged world-processor statement sitting in a normal processor (LParser.java:N-N), or a mod statement whose mod is not loaded |
| 3 | ERR | `X` used but there is no `X` -> @unit is null, this silently does nothing |
| 3 | INFO | version gate: uses bullet |
| 2 | WARN | `X` is never assigned, and this parameter is read as a boolean |
| 1 | ERR | unknown op `X` |
| 1 | ERR | jump target N out of range (N..N) |

## 硬错最多的存档

| 硬错 | 处理器 | 警告 | 存档 |
| --- | --- | --- | --- |
| 190 | 88 | 127 | 193.msav |
| 107 | 486 | 1180 | 131.msav |
| 36 | 6 | 12 | sector-serpulo-27.msav |
| 32 | 31 | 31 | sector-serpulo-6.msav |
| 30 | 5 | 0 | sector-serpulo-162.msav |
| 29 | 14 | 6 | 118.msav |
| 22 | 26 | 52 | 156.msav |
| 18 | 131 | 334 | 594.msav |
| 16 | 20 | 71 | sector-serpulo-180.msav |
| 10 | 19 | 48 | 457.msav |
| 10 | 34 | 36 | sector-serpulo-127.msav |
| 10 | 71 | 30 | sector-serpulo-225.msav |

## 现存的实际错误（示例）

- `100.msav` (141,124) L8: `thisflag` is read here but is never assigned anywhere in this program (and is not a link or built-in)
- `100.msav` (141,124) L12: `mine.ore` is read here but is never assigned anywhere in this program (and is not a link or built-in)
- `100.msav` (141,124) L21: `mine.ore` is read here but is never assigned anywhere in this program (and is not a link or built-in)
- `108.msav` (409,303) L23: `air-factory` is read here but is never assigned anywhere in this program (and is not a link or built-in)
- `118.msav` (40,89) L7: `fast` is read here but is never assigned anywhere in this program (and is not a link or built-in)
- `118.msav` (40,89) L10: `fast` is read here but is never assigned anywhere in this program (and is not a link or built-in)
- `118.msav` (40,89) L13: `fast` is read here but is never assigned anywhere in this program (and is not a link or built-in)
- `123.msav` (6,1669) L16: `unmoving` is read here but is never assigned anywhere in this program (and is not a link or built-in)
- `125.msav` (936,840) L35: `dead` holds @dead (1 = DEAD). Checking `notEqual` continues only while ALIVE; to rebind when dead use `equal`
- `125.msav` (936,840) L47: `dead` holds @dead (1 = DEAD). Checking `notEqual` continues only while ALIVE; to rebind when dead use `equal`

## 这组数字不能证明什么

- 只是静态检查。能证明「这段代码永远不会读那个变量」，不能证明「这段逻辑打起来是对的」——没有人跑过这些程序。
- 副本被合并了，所以「每处理器错误率」会被 9,699 份同一个程序放大；本报告刻意只按**不同的程序**计数。
- `INFO target N is itself a jump` 这类是跳转链的普通写法，不是问题，占 INFO 的八成。
