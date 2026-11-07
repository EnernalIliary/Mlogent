"""MBO —— Mindustry Blueprint Optimizer（v1 单条产线生成器）。

模块边界（对齐 docs/01 的 L0–L6）：

    gamedata    L0 版本化游戏数据快照（只读，带 sha256）
    codec       L1 `.msch` 编解码（解析复用 tools/msch.py，写回用本包的完整 TypeIO 写入器）
    model       L1 IR：本包内部用「中心格 + 显式 config」表示方块
    production  L2 生产层：目标产量 → 建筑清单（先 ceil 展开，再交给布局）
    layout      L2 空间/物流层：模板化产线布局 + 电力布线器
    validate    L4 离线校验：重叠/越界/端口/电力连通块
    engine      L4 真机校验：把蓝图放进 v160.7 真引擎跑 tick，读回产量与效率
    report      交付物：runs/<run_id>/ 五件产物
    cli         命令入口：mbo calc / gen / verify

设计约束（来自 docs/13 的实测，别违反）：

    R1  `Tile.x/y` 是**中心格**，origin = (x-(size-1)//2, y-(size-1)//2)
    R2  `Schematics.place(px,py)` 以蓝图中心为锚：ox = px - width//2
    R3  电力连线必须显式写 Point2[] config（tag=8，相对偏移，双向对称）
    R4  电 consumer 必须与 power-node 正交相邻
    R5  power-source ↔ node 也要显式 config
    R6  读数扫 `Vars.world.tile()`，禁用 `Groups.build`
    R7  生成器自校验 occupancy（`Schematics.place` 是静默覆盖）
"""

__version__ = "0.1.0"
