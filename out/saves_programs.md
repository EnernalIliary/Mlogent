# 存档里的逻辑程序：按「像什么」分桶

1421 个存档（0 个读不了），**4367 份不同的程序**，合计 2,081,584 条语句。

存档里的处理器**没有名字**（mlog 没有名字字段，只有蓝图有）。下面每一桶的用途是从三个信号推的：链接的方块类型、指令直方图、代码里唯一的几段字符串。**这是猜测，不是标签**——每行都把证据写在右边，方便你一眼否掉。

| 桶 | 程序数 | 语句数 | 副本数 |
| --- | ---: | ---: | ---: |
| 像素画(逐格 draw) | 2022 | 1,917,828 | 6,285 |
| 单位 | 830 | 65,137 | 19,866 |
| 物流 | 630 | 30,209 | 24,199 |
| 规则/世界 | 384 | 36,349 | 22,684 |
| 显示/UI | 177 | 19,393 | 11,321 |
| 计算/内存 | 151 | 9,216 | 2,152 |
| 其他 | 129 | 2,049 | 10,330 |
| 通信 | 44 | 1,403 | 8,359 |


## 像素画(逐格 draw) — 2022 份

| 副本 | 语句 | 位置 | 链接 | 主要指令 | 代码里的字 |
| ---: | ---: | --- | --- | --- | --- |
| 52 | 994 | `447.msav` (145,120) | display×1 | draw×942, drawflush×52 | — |
| 50 | 990 | `447.msav` (146,120) | display×1 | draw×930, drawflush×60 | — |
| 50 | 996 | `447.msav` (147,120) | display×1 | draw×913, drawflush×83 | — |
| 18 | 999 | `10.msav-backup.msav` (466,261) | display×1 | draw×995, drawflush×4 | — |
| 18 | 999 | `10.msav-backup.msav` (466,262) | display×1 | draw×995, drawflush×4 | — |
| 18 | 999 | `10.msav-backup.msav` (479,263) | display×1 | draw×995, drawflush×4 | — |
| 18 | 999 | `10.msav-backup.msav` (479,264) | display×2 | draw×995, drawflush×4 | — |
| 18 | 999 | `10.msav-backup.msav` (479,265) | display×1 | draw×995, drawflush×4 | — |
| 18 | 999 | `10.msav-backup.msav` (479,266) | display×1 | draw×995, drawflush×4 | — |
| 18 | 999 | `10.msav-backup.msav` (479,267) | display×1 | draw×995, drawflush×4 | — |
| 18 | 999 | `10.msav-backup.msav` (479,268) | display×1 | draw×995, drawflush×4 | — |
| 18 | 999 | `10.msav-backup.msav` (477,269) | display×1 | draw×995, drawflush×4 | — |
| 18 | 999 | `10.msav-backup.msav` (478,269) | display×1 | draw×995, drawflush×4 | — |
| 18 | 999 | `10.msav-backup.msav` (479,269) | display×1 | draw×995, drawflush×4 | — |
| 17 | 999 | `10.msav-backup.msav` (467,261) | display×1 | draw×995, drawflush×4 | — |
| 17 | 999 | `10.msav-backup.msav` (468,261) | display×1 | draw×995, drawflush×4 | — |
| 17 | 999 | `10.msav-backup.msav` (469,261) | display×1 | draw×995, drawflush×4 | — |
| 17 | 999 | `10.msav-backup.msav` (471,261) | display×1 | draw×995, drawflush×4 | — |
| 17 | 999 | `10.msav-backup.msav` (472,261) | display×1 | draw×995, drawflush×4 | — |
| 17 | 999 | `10.msav-backup.msav` (473,261) | display×1 | draw×995, drawflush×4 | — |

（另有 2002 份，见 JSON）

## 单位 — 830 份

| 副本 | 语句 | 位置 | 链接 | 主要指令 | 代码里的字 |
| ---: | ---: | --- | --- | --- | --- |
| 7,649 | 16 | `556.msav` (422,401) | processor×131 | op×6, set×3, ucontrol×3, jump×3, ubind×1 | — |
| 1,502 | 16 | `538.msav` (523,440) | processor×223, wall×1 | op×6, set×3, ucontrol×3, jump×3, ubind×1 | — |
| 408 | 18 | `131.msav` (579,345) | — | jump×3, op×2, wait×2, end×2, fetch×2 | — |
| 385 | 47 | `131.msav` (857,130) | dome×1 | jump×14, sensor×9, set×6, print×5, ucontrol×5 | [white]寻找建筑失败，请连接建筑（需首先连接超速器 |
| 378 | 25 | `182.msav` (555,11) | cell×1 | read×8, jump×5, ucontrol×4, sensor×3, lookup×2 | — |
| 324 | 48 | `165.msav` (241,261) | foreshadow×4, projector×2 | control×18, jump×10, sensor×9, set×6, op×2 | — |
| 323 | 66 | `165.msav` (242,260) | container×1, projector×1 | jump×21, ucontrol×15, sensor×14, set×8, end×3 | — |
| 250 | 40 | `167.msav` (477,163) | cell×1 | read×10, jump×9, ucontrol×8, set×5, sensor×4 | — |
| 222 | 40 | `167.msav` (450,5) | cell×1 | read×10, jump×9, ucontrol×8, set×5, sensor×4 | — |
| 211 | 24 | `131.msav` (815,743) | — | jump×3, set×2, fetch×2, end×2, ubind×2 | 恶魔代理人苏醒了 |
| 211 | 44 | `131.msav` (819,743) | — | sensor×9, jump×6, set×4, end×4, status×4 | — |
| 211 | 66 | `131.msav` (820,743) | — | effect×18, op×12, sensor×8, jump×6, wait×5 | — |
| 211 | 69 | `131.msav` (822,743) | — | effect×20, op×12, sensor×8, jump×6, wait×5 | — |
| 211 | 55 | `131.msav` (823,743) | — | op×12, sensor×10, set×7, jump×7, end×4 | — |
| 211 | 37 | `131.msav` (824,743) | — | op×9, sensor×6, jump×5, end×4, set×3 | — |
| 211 | 27 | `131.msav` (826,743) | — | sensor×6, ucontrol×4, set×3, jump×3, fetch×2 | — |
| 211 | 50 | `131.msav` (827,743) | — | op×10, sensor×10, set×6, jump×6, end×4 | — |
| 211 | 69 | `131.msav` (828,743) | — | effect×20, op×12, sensor×8, jump×6, wait×5 | — |
| 211 | 51 | `131.msav` (829,743) | — | op×12, effect×8, set×7, jump×6, sensor×4 | — |
| 211 | 50 | `131.msav` (831,743) | — | op×10, sensor×10, set×6, jump×6, end×4 | — |

（另有 810 份，见 JSON）

## 物流 — 630 份

| 副本 | 语句 | 位置 | 链接 | 主要指令 | 代码里的字 |
| ---: | ---: | --- | --- | --- | --- |
| 1,481 | 11 | `131.msav` (396,403) | processor×1 | jump×2, end×2, control×2, op×1, getblock×1 | — |
| 422 | 13 | `131.msav` (579,382) | — | op×2, getblock×2, jump×2, end×2, wait×1 | — |
| 422 | 39 | `131.msav` (580,383) | — | jump×8, op×6, getblock×4, print×4, end×3 | \n范围1-40 |
| 422 | 40 | `131.msav` (581,383) | — | jump×8, op×6, getblock×4, print×4, set×3 | \n预设种类1-20 |
| 422 | 40 | `131.msav` (582,383) | — | jump×8, op×6, getblock×4, print×4, set×3 | \n范围1-40 |
| 296 | 9 | `165.msav` (487,217) | reconstructor×6, cell×1, factory×1 | jump×2, print×2, read×1, set×1, getlink×1 | 用这个世处绑定你想要控制开场时间的工厂 |
| 212 | 21 | `131.msav` (824,172) | projector×1, switch×1 | op×4, setblock×3, getblock×3, jump×3, end×3 | — |
| 212 | 3 | `131.msav` (818,204) | cell×1 | write×2, control×1 | — |
| 212 | 7 | `131.msav` (822,205) | processor×50 | op×2, fetch×1, set×1, getlink×1, control×1 | — |
| 212 | 17 | `131.msav` (570,345) | — | jump×3, op×2, wait×2, end×2, fetch×2 | — |
| 212 | 17 | `131.msav` (571,345) | — | jump×3, op×2, wait×2, end×2, fetch×2 | — |
| 212 | 17 | `131.msav` (572,345) | — | jump×3, op×2, wait×2, end×2, fetch×2 | — |
| 212 | 17 | `131.msav` (573,345) | — | jump×3, op×2, wait×2, end×2, fetch×2 | — |
| 212 | 17 | `131.msav` (574,345) | — | jump×3, op×2, wait×2, end×2, fetch×2 | — |
| 212 | 17 | `131.msav` (575,345) | — | jump×3, op×2, wait×2, end×2, fetch×2 | — |
| 212 | 17 | `131.msav` (570,349) | — | jump×3, op×2, wait×2, end×2, fetch×2 | — |
| 212 | 17 | `131.msav` (571,349) | — | jump×3, op×2, wait×2, end×2, fetch×2 | — |
| 212 | 17 | `131.msav` (572,349) | — | jump×3, op×2, wait×2, end×2, fetch×2 | — |
| 212 | 17 | `131.msav` (573,349) | — | jump×3, op×2, wait×2, end×2, fetch×2 | — |
| 212 | 17 | `131.msav` (574,349) | — | jump×3, op×2, wait×2, end×2, fetch×2 | — |

（另有 610 份，见 JSON）

## 规则/世界 — 384 份

| 副本 | 语句 | 位置 | 链接 | 主要指令 | 代码里的字 |
| ---: | ---: | --- | --- | --- | --- |
| 1,696 | 1 | `131.msav` (418,407) | — | setrule×1 | — |
| 1,269 | 41 | `131.msav` (402,408) | — | op×9, jump×6, getblock×4, print×4, set×3 | \n单位攻击力： |
| 1,170 | 12 | `131.msav` (224,435) | acropolis×1 | sensor×4, jump×3, setblock×2, getlink×1, wait×1 | — |
| 1,057 | 41 | `131.msav` (397,408) | — | op×9, jump×6, getblock×4, print×4, set×3 | \n建筑速度： |
| 1,057 | 41 | `131.msav` (398,408) | — | op×9, jump×6, getblock×4, print×4, set×3 | \n建筑血量： |
| 1,057 | 41 | `131.msav` (399,408) | — | op×9, jump×6, getblock×4, print×4, set×3 | \n建筑攻击力： |
| 1,057 | 41 | `131.msav` (400,408) | — | op×9, jump×6, getblock×4, print×4, set×3 | \n单位构造速度： |
| 1,057 | 41 | `131.msav` (401,408) | — | op×9, jump×6, getblock×4, print×4, set×3 | \n单位血量： |
| 1,057 | 41 | `131.msav` (403,408) | — | op×9, jump×6, getblock×4, print×4, set×3 | \n单位构造耗材： |
| 422 | 188 | `131.msav` (578,382) | — | jump×72, effect×34, set×25, sensor×11, op×9 | \n按开关切换特效种类 |
| 212 | 18 | `131.msav` (818,194) | switch×1 | jump×4, end×3, sensor×3, fetch×2, op×1 | — |
| 212 | 7 | `131.msav` (821,205) | cell×1 | effect×4, read×2, wait×1 | — |
| 212 | 6 | `131.msav` (682,401) | — | set×1, fetch×1, setrule×1, op×1, jump×1 | — |
| 212 | 40 | `131.msav` (421,408) | — | op×9, jump×6, getblock×4, print×4, set×3 | \n单位血量： |
| 211 | 13 | `131.msav` (416,417) | cell×1 | write×11, setrule×1, control×1 | — |
| 211 | 13 | `131.msav` (426,417) | cell×1 | write×11, setrule×1, control×1 | — |
| 211 | 39 | `131.msav` (427,418) | — | op×9, jump×6, getblock×4, set×3, read×3 | 太阳能发电倍率： |
| 211 | 38 | `131.msav` (428,418) | — | op×7, jump×7, getblock×4, set×3, read×3 | 单位上限： |
| 211 | 38 | `131.msav` (429,418) | — | op×7, jump×7, getblock×4, set×3, read×3 | 核心禁建范围(上限200)： |
| 211 | 42 | `131.msav` (430,418) | — | jump×9, op×7, set×5, getblock×4, read×3 | 核心禁建范围(上限200)： |

（另有 364 份，见 JSON）

## 显示/UI — 177 份

| 副本 | 语句 | 位置 | 链接 | 主要指令 | 代码里的字 |
| ---: | ---: | --- | --- | --- | --- |
| 9,699 | 22 | `236.msav` (802,162) | display×1, switch×1 | jump×4, op×2, set×2, getblock×2, read×2 | — |
| 800 | 24 | `504.msav` (802,162) | display×1, switch×1 | jump×5, read×3, op×2, set×2, getblock×2 | — |
| 52 | 175 | `458.msav` (46,587) | router×2, conduit×2, reactor×2, generator×1, mixer×1 | op×51, jump×42, print×30, sensor×20, set×13 | 起冲后冲击状态检查，如果电力盈余足够，并且冲击好像无法维 |
| 52 | 53 | `sector-serpulo-164.msav` (60,145) | pad×3, display×2, sorter×2, vault×1, unloader×1 | jump×14, draw×11, control×9, sensor×6, op×6 | — |
| 48 | 53 | `472.msav` (448,517) | pad×3, switch×2, display×2, sorter×2, vault×1 | jump×14, draw×11, control×9, sensor×6, op×6 | — |
| 42 | 122 | `131.msav` (518,251) | pad×6, message×2, switch×1 | jump×31, print×31, set×19, op×9, sensor×8 | \n1.关闭开关、着陆板置空，在着陆板修改任意物品，被修 |
| 31 | 163 | `270.msav` (514,464) | factory×7, reconstructor×2, extractor×2, segment×1, dome×1 | op×44, jump×41, print×32, sensor×17, set×13 | 起冲后冲击状态检查，如果电力盈余足够，并且冲击好像无法维 |
| 28 | 98 | `157.msav` (62,210) | switch×12, display×2, processor×1, cell×1 | draw×40, jump×24, write×14, sensor×13, op×4 | — |
| 24 | 270 | `561.msav` (23,10) | cell×1 | op×73, set×46, jump×44, sensor×27, print×14 | 是否被核心单位上限限制，如果是，那么MCV达到单位上限时 |
| 18 | 134 | `sector-serpulo-133.msav` (102,189) | pad×6, switch×1, message×1 | jump×36, print×35, set×22, op×9, sensor×8 | \n1.关闭开关、着陆板将置空，在着陆板修改任意物品，被 |
| 17 | 137 | `131.msav` (862,125) | wall×31, projector×20, parallax×6, fuse×4 | op×47, set×27, jump×19, print×17, sensor×11 | 连接到显示块显示当前所有建筑盾量与生命状态、此操作消耗大 |
| 15 | 141 | `313.msav` (143,134) | pad×15, message×1 | set×39, jump×24, op×22, print×19, lookup×7 | v3.2：修复了更名为调和着陆逻辑后产生的大量BUG，替 |
| 14 | 122 | `212.msav` (327,105) | message×2, switch×1 | jump×31, print×31, set×19, op×9, sensor×8 | \n1.关闭开关、着陆板置空，在着陆板修改任意物品，被修 |
| 14 | 163 | `269.msav` (526,474) | factory×3, reconstructor×2, crucible×1, press×1, reactor×1 | op×44, jump×41, print×32, sensor×17, set×13 | 起冲后冲击状态检查，如果电力盈余足够，并且冲击好像无法维 |
| 12 | 212 | `131.msav` (307,726) | cell×1, node×1, display×1 | op×61, draw×58, set×46, jump×20, end×15 | — |
| 12 | 201 | `131.msav` (310,726) | cell×1, node×1, display×1 | op×60, draw×55, set×47, jump×20, end×15 | — |
| 12 | 207 | `131.msav` (311,726) | cell×1, node×1, display×1 | op×59, draw×58, set×47, jump×23, end×15 | — |
| 12 | 292 | `465.msav` (1,1) | cell×1 | op×78, jump×53, set×48, sensor×32, print×14 | 是否被核心单位上限限制，如果是，那么MCV达到单位上限时 |
| 12 | 141 | `483.msav` (12,815) | pad×15, message×1 | set×39, jump×24, op×22, print×19, lookup×7 | v3.2：修复了更名为调和着陆逻辑后产生的大量BUG，替 |
| 12 | 10 | `535.msav` (40,420) | display×1 | op×4, draw×3, sensor×2, drawflush×1 | — |

（另有 157 份，见 JSON）

## 计算/内存 — 151 份

| 副本 | 语句 | 位置 | 链接 | 主要指令 | 代码里的字 |
| ---: | ---: | --- | --- | --- | --- |
| 211 | 11 | `131.msav` (465,421) | cell×1 | write×10, stop×1 | — |
| 211 | 5 | `131.msav` (836,743) | cell×1 | set×2, write×2, stop×1 | — |
| 196 | 27 | `131.msav` (581,345) | — | op×10, jump×6, end×3, sensor×3, getblock×2 | — |
| 196 | 27 | `131.msav` (582,345) | — | op×10, jump×6, end×3, sensor×3, getblock×2 | — |
| 195 | 26 | `131.msav` (853,562) | — | op×10, set×9, jump×3, setprop×2, setrate×1 | — |
| 56 | 45 | `504.msav` (248,473) | — | setmarker×16, op×13, makemarker×4, sensor×3, getblock×2 | setx |
| 56 | 927 | `504.msav` (246,474) | processor×1, switch×1 | set×439, op×202, jump×198, write×68, sensor×15 | 裂变产物需求总 |
| 56 | 760 | `504.msav` (247,474) | arc×1 | op×340, print×207, jump×111, write×72, setmarker×17 | \n[#ffff99]   [white] |
| 37 | 12 | `165.msav` (488,218) | cell×1 | write×3, jump×2, print×2, set×1, read×1 | 在此处修改允许开厂时间 |
| 37 | 12 | `165.msav` (490,218) | cell×1 | write×3, jump×2, print×2, set×1, read×1 | 在此处修改允许开厂时间 |
| 37 | 12 | `165.msav` (488,220) | cell×1 | write×3, jump×2, print×2, set×1, read×1 | 在此处修改允许开厂时间 |
| 37 | 12 | `165.msav` (490,220) | cell×1 | write×3, jump×2, print×2, set×1, read×1 | 在此处修改允许开厂时间 |
| 37 | 12 | `165.msav` (488,222) | cell×1 | write×3, jump×2, print×2, set×1, read×1 | 在此处修改允许开厂时间 |
| 37 | 12 | `165.msav` (490,222) | cell×1 | write×3, jump×2, print×2, set×1, read×1 | 在此处修改允许开厂时间 |
| 37 | 12 | `165.msav` (488,224) | cell×1 | write×3, jump×2, print×2, set×1, read×1 | 在此处修改允许开厂时间 |
| 37 | 12 | `165.msav` (490,224) | cell×1 | write×3, jump×2, print×2, set×1, read×1 | 在此处修改允许开厂时间 |
| 29 | 51 | `365.msav` (373,16) | cell×1 | op×21, jump×8, write×7, getblock×4, setmarker×4 | — |
| 16 | 107 | `123.msav` (1,1669) | cell×1 | jump×34, op×25, getblock×14, read×12, write×7 | — |
| 16 | 32 | `123.msav` (3,1669) | cell×1 | write×12, jump×9, read×7, op×4 | — |
| 16 | 5 | `123.msav` (28,1669) | cell×1 | write×5 | — |

（另有 131 份，见 JSON）

## 其他 — 129 份

| 副本 | 语句 | 位置 | 链接 | 主要指令 | 代码里的字 |
| ---: | ---: | --- | --- | --- | --- |
| 1,409 | 0 | `100.msav` (98,84) | — | — | — |
| 1,248 | 10 | `131.msav` (569,428) | — | jump×3, set×2, fetch×2, op×1, sensor×1 | 黑名单 |
| 636 | 16 | `131.msav` (834,194) | — | jump×5, read×2, sensor×2, setprop×2, setrate×1 | — |
| 422 | 6 | `131.msav` (587,389) | source×1 | getlink×1, jump×1, op×1, set×1, setblock×1 | — |
| 212 | 21 | `131.msav` (818,200) | — | jump×4, op×3, end×3, sensor×3, set×2 | — |
| 212 | 6 | `131.msav` (681,401) | — | jump×2, set×1, fetch×1, setprop×1, op×1 | — |
| 212 | 5 | `131.msav` (681,404) | — | setblock×4, wait×1 | — |
| 211 | 22 | `131.msav` (587,390) | — | jump×6, op×3, end×3, getblock×2, sensor×2 | — |
| 211 | 22 | `131.msav` (590,390) | — | jump×6, op×3, end×3, getblock×2, sensor×2 | — |
| 211 | 36 | `131.msav` (587,392) | — | setprop×20, jump×4, end×3, op×2, setrate×1 | — |
| 211 | 36 | `131.msav` (590,392) | — | setprop×20, jump×4, end×3, op×2, setrate×1 | — |
| 211 | 17 | `131.msav` (581,395) | — | jump×4, end×3, op×2, setrate×1, getblock×1 | — |
| 211 | 17 | `131.msav` (586,400) | — | jump×4, end×3, sensor×3, setblock×2, op×1 | — |
| 211 | 29 | `131.msav` (585,405) | — | jump×7, end×4, op×3, wait×3, set×3 | — |
| 211 | 4 | `131.msav` (586,405) | switch×1 | sensor×1, jump×1, fetch×1, setprop×1 | — |
| 211 | 7 | `131.msav` (585,409) | — | setblock×3, set×1, op×1, jump×1, wait×1 | — |
| 211 | 12 | `131.msav` (467,432) | — | op×3, sensor×3, jump×2, getblock×1, wait×1 | — |
| 211 | 23 | `131.msav` (830,743) | — | sensor×4, jump×4, end×4, set×3, fetch×2 | — |
| 211 | 6 | `131.msav` (835,743) | — | op×2, getblock×1, read×1, write×1, wait×1 | — |
| 210 | 9 | `236.msav` (821,204) | processor×50 | set×2, jump×2, op×2, getlink×1, lookup×1 | ut |

（另有 109 份，见 JSON）

## 通信 — 44 份

| 副本 | 语句 | 位置 | 链接 | 主要指令 | 代码里的字 |
| ---: | ---: | --- | --- | --- | --- |
| 1,566 | 29 | `131.msav` (545,345) | cell×1, message×1 | op×9, print×6, jump×3, sensor×3, end×2 | \n限制下半地图区域  |
| 1,057 | 51 | `131.msav` (396,409) | — | op×23, print×17, read×8, getblock×2, printflush×1 | \n单位构造速度： |
| 212 | 21 | `131.msav` (820,194) | — | op×3, print×3, jump×3, getblock×2, end×2 | 给PVE单位添加BUFF: |
| 212 | 22 | `131.msav` (821,194) | — | print×4, op×3, jump×3, getblock×2, end×2 | \n吐槽：虽然0%，但是游戏加速状态很多倍以后，可以看见 |
| 212 | 21 | `131.msav` (824,199) | — | op×3, print×3, jump×3, getblock×2, end×2 | 给PVE单位添加BUFF: |
| 212 | 21 | `131.msav` (825,199) | — | op×3, print×3, jump×3, getblock×2, end×2 | 给PVE单位添加BUFF: |
| 212 | 21 | `131.msav` (826,199) | — | op×3, print×3, jump×3, getblock×2, end×2 | 给PVE单位添加BUFF: |
| 212 | 21 | `131.msav` (828,199) | — | op×3, print×3, jump×3, getblock×2, end×2 | \n效果：140%伤害倍率 95%生命 115&移动速率 |
| 212 | 21 | `131.msav` (829,199) | — | op×3, print×3, jump×3, getblock×2, end×2 | \n效果：115%伤害倍率 115移动速度倍率 125% |
| 212 | 21 | `131.msav` (830,199) | — | op×3, print×3, jump×3, getblock×2, end×2 | 给PVE单位添加BUFF: |
| 212 | 21 | `131.msav` (831,199) | — | op×3, print×3, jump×3, getblock×2, end×2 | \n效果：130%伤害倍率\n150%生命倍率 |
| 212 | 21 | `131.msav` (832,199) | — | op×3, print×3, jump×3, getblock×2, end×2 | 给PVE单位添加BUFF: |
| 212 | 23 | `131.msav` (824,203) | — | print×5, op×3, jump×3, getblock×2, end×2 | 给PVE单位添加BUFF: |
| 212 | 23 | `131.msav` (825,203) | — | print×5, op×3, jump×3, getblock×2, end×2 | \n效果：80%血60%移速 |
| 212 | 24 | `131.msav` (826,203) | — | print×6, op×3, jump×3, getblock×2, end×2 | \n效果：80%血 80%移速 |
| 212 | 22 | `131.msav` (828,203) | — | print×4, op×3, jump×3, getblock×2, end×2 | 给PVE单位添加BUFF: |
| 212 | 22 | `131.msav` (829,203) | — | print×4, op×3, jump×3, getblock×2, end×2 | 给PVE单位添加BUFF: |
| 212 | 23 | `131.msav` (830,203) | — | print×5, op×3, jump×3, getblock×2, end×2 | 给PVE单位添加BUFF: |
| 212 | 21 | `131.msav` (831,203) | — | op×3, print×3, jump×3, getblock×2, end×2 | \n效果：80%血70%移速 |
| 212 | 21 | `131.msav` (832,203) | — | op×3, print×3, jump×3, getblock×2, end×2 | \n效果：70移速% 60%开火速率 |

（另有 24 份，见 JSON）
