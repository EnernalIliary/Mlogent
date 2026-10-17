---
name: mindustry-blueprint
description: 生成/解析/校验 Mindustry 蓝图与 mlog 逻辑时使用：从蓝图提取逻辑源码、按逻辑生成可粘贴的蓝图码、静态检查 mlog、查方块 content ID 与指令格式。
whenToUse: 涉及 Mindustry 蓝图（.msch / 蓝图码）、mlog 逻辑编写或审查、需要方块尺寸或 content ID 时。
---

# Mindustry 蓝图与 mlog 工具链

## 这个技能能做什么

| 能力 | 命令 |
|---|---|
| **解析蓝图** —— 提取逻辑源码、方块、链接 | `mlog.py parse <file.msch>` |
| **生成蓝图** —— 从 mlog 产出可粘贴蓝图码 | `mlog.py gen <logic.mlog> ...` |
| **静态检查 mlog** —— 抓 `@dead` 反用等真实 bug | `mlog.py check <logic.mlog>` |
| **成本分析** —— 死代码 + 最坏指令数 + 折合耗时 | `mlog.py check <logic.mlog> --cost` |
| **死存储 / 不可达代码** —— CFG + 活跃变量不动点 | `mlog.py ir <logic.mlog>` |
| **查方块 ID / 尺寸** | `mlog.py id [名称]` |
| **查物品 ID / 解打包配置** | `mlog.py item [名称] [--unpack N]` |
| **查指令格式** | `mlog.py cmd [关键字]` |
| **回归自测** —— 429 个真实蓝图往返校验 | `mlog.py selftest` |

工具在 `tools/` 下,零第三方依赖(纯标准库)。`python tools/mlog.py --help`。

## 铁律(生成前逐条自查)

1. **`@dead` 死亡返回 1** —— "死了就重绑"必须写 `equal`,不是 `notEqual`。**这条抓出过真实 bug。**
2. **控制单位前必须 `ubind`** —— 否则 `@unit` 为 `null`,所有 `ucontrol`/`uradar`/`ulocate` 静默失效。
3. **`ulocate` 第 8 参必须接住** —— 写 `0` 就丢掉了建筑引用,后面无法 `itemTake`/`itemDrop`。
   (`core` 不是内置关键字,它只是接收这个输出的**变量名**。)
4. **取货点用 `move`,不要用 `approach`** —— `approach` 停在半径外可能够不到仓库,而 `itemTake` 够不到时**静默跳过**。
   `move` 不读第 3 个参数。(`move` 精确到 1 格;`approach` 停在 `radius - 7`)
5. **`ulocate` 要无条件执行,不能放进分支** —— 否则另一条路径上坐标从未赋值,单位会飞向 `(0,0)`。
6. **`end` 是"跳回开头"**,不能用来"结束一个分支后继续往下"。分支互斥请用 `jump`。
7. **`jump` 存的是绝对行号** —— 增删一行全盘偏移,生成前逐条数一遍。重点查:目标是否落在 `sensor`/`set` 这类有副作用的行上。
8. **单位只能带一种物品** —— `itemCapacity` 是**堆叠上限**,不是每种物品的上限。
9. **`op` 是固定元数** —— `abs`/`floor`/`sin`/`rand` 等一元运算只吃 2 个参数。
   (多写的 token 不参与执行,行为正常,但也不是你以为的运算。)
10. **不要自己发明阈值,不要做可行性推算** —— 游戏机制只要求某个下限,满足即满效率。
    实际战场有阻挡、有堵车;**"能跑"是实测出来的,不是算出来的**。
11. **不要为了讨好检查器去改正确的代码** —— 检查器是提示器,实测才是标准。
12. **`end` 之后不要再写语句** —— 它是"跳回程序开头",不是"结束"。写在它后面的都是死代码。
    用 `--cost` 一跑就能看到(会直接列出来)。

## 标准流程

```
写 mlog  →  mlog.py check --cost  →  mlog.py gen  →  游戏内实测  →  结论写回本文件
              ↑                                                        │
              └────────────────────────────────────────────────────────┘
```

**生成蓝图时必须遵守"确定性 + 自验证"**:

- 同一份源码 + 同一组参数 → **完全相同的字节**(不要引入时间戳/随机量)
- 生成前先跑 `check`
- 生成后**必须**重新解析验证(工具已内置,失败会拒绝输出)

## 成本分析(`--cost`)看什么

```
statements      : 159                     ← 语句数,>1000 会被静默截断
reachability    : all statements reachable ← 或列出永远跑不到的语句
opcodes         : op×62, jump×40, ...      ← 指令构成
loop heads      : L28(×80), L52(×80)       ← 循环起始行 + 推定圈数
worst-case path : ~2001 instructions       ← 一次完整决策最坏多少条
    ⚠ over LExecutor.maxInstructions (1000/tick): one cycle needs 2.0 ticks
    micro-processor  @ipt=2    1000 ticks (  16.7 s) per cycle
```

**怎么用这三个数**:

| 看什么 | 说明什么 |
|---|---|
| **UNREACHABLE 非空** | 有死代码。多半是 `end` 之后写了东西,或跳转目标写错 |
| **worst-case > 1000** | 一个决策周期跑不完一 tick,单位响应会有对应延迟 |
| **@ipt 换算的秒数** | 直接回答"这套逻辑跟得上战况吗" |

**注意**:

- 循环圈数靠**守卫里的常量**推定(`jump 37 greaterThanEq index 80`)。看不到常量的循环按一圈算并给出警告
- 结果是**上界**(互斥分支不剪枝),意思是"最坏能到多少",不是"平时多少"
- 回到第 0 行的回边 = 主循环,只算**一圈**(mlog 本来就每 tick 重跑一遍)

## 指令预算:别猜,这是确定的

**一条语句 = 一条指令,`jump` 也是 1 条,和 `op` / `print` 没有区别。**

`runOnce()` 里 **`counter` 先自增再执行,不看指令类型**(`LExecutor.java:111-121`):

```java
instructions[(int)(counter.numval++)].run(this);   // ← 无条件 +1
```

⇒ **钱花在"循环圈数 × 循环体语句数"上,不花在 `jump` 这个字上。**
⇒ 用 `jump` 跳过一段确实省下被跳过那些行,但**跳转自己仍然收 1 条**。

**每 tick 的额度**(`LogicBlock.java:564-578`,`ipt = instructionsPerTick`):

| 处理器 | ipt | 每秒 |
|---|---|---|
| 微型 micro-processor | **2** | 120 |
| 逻辑 logic-processor | **8** | 480 |
| 超级 hyper-processor | **25** | 1500 |
| 世界 world-processor | **8**(`maxInstructionsPerTick = 1000`) | 480 |

**两条容易漏的**:

- **只有 `wait` / `stop` / `printflush @wait` 会 `yield`**,提前结束这一 tick 的额度;**`jump 0 always` 没有这个机制**,会在一个 tick 内把额度烧光
- `setrate` 是唯一能改 ipt 的指令,上限是 `maxInstructionsPerTick`(逻辑卡 **40**,比默认 8 大 5 倍);`@ipt` 立即变新值,但**本 tick 的循环边界已经固定**,下个 tick 才生效

**所以改循环之前先跑 `check --cost`。** 算完的秒数就是单位从"看到"到"反应"的延迟。

## 常用调用

```bash
# 解析:看逻辑源码和结构
python tools/mlog.py parse "schematics/无线超.msch"

# 检查:生成前必做
python tools/mlog.py check logic.mlog
python tools/mlog.py check --msch out.msch

# 成本分析:死代码 + 最坏多少条指令 + 折合几秒
python tools/mlog.py check logic.mlog --cost
python tools/mlog.py check --msch out.msch --cost

# 死存储:赋值了但整个程序(含跨周期)从未读取
python tools/mlog.py ir logic.mlog
python tools/mlog.py ir --msch out.msch
python tools/mlog.py ir --all logic.mlog    # 连语法强制的输出槽一起列

# 生成:只放处理器(链接目标需自己摆)
python tools/mlog.py gen logic.mlog --name "我的逻辑" --link dome1@3,1

# 生成:连目标方块一起放(--with-block 坐标是【中心格】)
python tools/mlog.py gen logic.mlog --name "无线超" \
    --link dome1@3,1 --with-block overdrive-dome@4,2=248 \
    --out paste.txt --binary out.msch

# 查方块 ID 和尺寸
python tools/mlog.py id overdrive

# 查指令格式
python tools/mlog.py cmd ulocate
```

## ⚠️ 最容易搞错的一件事:方块坐标是「中心格」

schematic 里 Stile 存的是方块的**中心格**,不是左上角。**已双重验证**:

- 源码:`Tile.setBlock()` 用 `int offset = -(block.size - 1) / 2` 铺开多格方块 → `(x,y)` 是中间那格
- 实证:624 个真实蓝图里,按"角"解释会产生 **11 处方块重叠**,按"中心"解释 **0 处**

所以一个 3×3 方块,要让它的成品占据 `(3,1)–(5,3)`,**中心要写 `(4,2)`**。

链接的 `name@dx,dy` 也要对到**方块覆盖范围内的任意格**(工具会按 footprint 校验并提示)。

## `ir` 看什么、不看什么

四层分级,默认只打第一层:

| 层 | 含义 | 该不该管 |
|---|---|---|
| `reported` | 算出来的值被覆盖 / 从没人读 | **是 bug,去看** |
| `slot` | `ulocate`/`ucontrol`/`radar`/`sensor` 的多输出槽没读 | 语法强制,不是错 |
| `declaration` | `set x 字面量` 且没人读 | 作者的"声明",忽略 |
| `annotation` | 变量名是纯标点(`//`) | mlog 没有行尾注释(只有 `#`),作者拿它当注释 |

**校准(全语料 617 文件 / 2409 块,已排除模拟器蓝图)**:82.0% 的处理器**一条都不报**,p50=0、p90=1;均值 0.650/块是被约 20 个代码生成式蓝图拉高的。抽样 28 个站点人工核对,**全部为真**。

**它不能证明你的逻辑是对的**:
- 不跨处理器 —— 别的处理器用 `read x cell1 "名字"` 读它,这里看不见(实测全语料 0 例,但报了 `never-read` 仍要自己确认)
- 只判"值有没有人用",不判"值算得对不对"(`op add dx dy dx` 想算距离却写加法,`ir` 不报)

## 参考数据

| 文件 | 内容 |
|---|---|
| `tools/wiki_block_ids.json` | 422 个原版方块 → content ID |
| `tools/block_sizes.json` | 446 个方块尺寸(从源码推导) |
| `tools/cmd_index.json` | 86 条 mlog 指令的格式/参数/注意事项 |
| [REFERENCE.md](REFERENCE.md) | 完整知识库:编号体系、机制、坑、被推翻的旧结论 |
| [PATTERNS.md](PATTERNS.md) | 逻辑模式库 + 蓝图工程分析 |

## 关键事实速查

- **蓝图里存的是 mlog 明文源码**,不需要反编译
- **content ID 是"构造顺序号"**,原版方块先构造、mod 后追加 ⇒ **mod 不会让原版方块 ID 偏移**
- **蓝图不存 content ID**,游戏加载时**按方块名解析** ⇒ 放原版方块只要名字对
- **`@dead` 对 `null` 目标也返回 1** ⇒ 兼作"单位不存在"判断
- **`sensor` 的 null 会传染** ⇒ 目标为 null 时所有属性都返回 null
- **链接名 = 内部名按 `-` 切分取最后一段 + 序号** ⇒ `overdrive-dome` → `dome1`
