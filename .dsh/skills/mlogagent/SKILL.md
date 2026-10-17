---
name: mlogagent
description: 审查 Mindustry mlog 逻辑时使用：一次跑完静态检查/成本/不可达代码/死存储/常量分支/可证 null/打包配置，按证据强弱给出先看哪里，并附每层的校准数字与"不能证明什么"。
whenToUse: 需要审查或解释一段 mlog（.mlog 源码或 .msch 蓝图里的逻辑块）、判断某条语句是否白算、某个分支是否恒真、某个变量是否可能为 null、或某个数字打包了几层字段时。
---

# MLOGAGENT — mlog 逻辑分析

一个入口把六种分析全部跑一遍，并告诉你**先看哪里**。自带完整副本（`tools/` 里 8 个模块 + 5 个数据文件 + `MANIFEST.sha256`），整个目录拷走就能用，不依赖仓库其他部分。

```bash
python tools/mlogagent.py report logic.mlog            # 全部
python tools/mlogagent.py report logic.mlog --brief    # 只要 VERDICT 两行
python tools/mlogagent.py report out.msch              # 蓝图里每个逻辑块各跑一遍
python tools/mlogagent.py info                         # 数据版本 / 模块清单
python tools/mlogagent.py info --verify                # 校验 MANIFEST.sha256
```

位置参数按**后缀**分派：`.msch` 走蓝图解析（一个逻辑块一节），其余按 UTF-8 文本读。

## 先读这一节：六层各自能证明什么

| 层 | 回答的问题 | 证据强度 | 全语料命中 |
|---|---|---|---|
| `check` | 语法/参数位/`@dead` 反用这类**确定**错误 | 最强，可直接改 | 误报 ~0 |
| `ir` → 死存储 | 某个变量**写了没人读** | 强，但分四层（见下） | 抽检 28 站全真 |
| `ir` → 不可达 | 某些语句**永远执行不到** | 最强 | 0 |
| `cost` | 一圈**最坏**要多少指令、`wait` 占多少秒 | 近似，可对拍 | — |
| `values` | 某个条件**恒真/恒假**、某个变量**必为 null** | 中，只报能证明的 | 4.1% 的块有信号 |
| `pack` | 一个数字**打包了几层字段**、低位够装几个 id | 强（低频） | 抽检 3 站全真 |

`VERDICT` 那行是结论摘要；末尾的「先看这里」按上表强弱排序，只指一个地方。

## 死存储必须分层读

`ir` 默认只报 `reported` 层，其余三层计数后隐藏（`--all` 才列出）：

| 层 | 含义 | 该不该改 |
|---|---|---|
| `reported` | 值被覆盖前没人读，或算出来就丢 | **是 bug**，逐条看 |
| `slot` | 语法强制的输出槽（`ulocate` 的 `found`、`ucontrol` 的返回等） | 多数不改，作者不需要那个值 |
| `declaration` | `set x <字面量>` 之后没读 | 作者的声明式初始化，无价值 |
| `annotation` | 变量名是纯标点（`//`、`--`） | 作者拿变量名当注释，不是 bug |

mlog **只有 `#` 起注释**（`LParser.java:98-99`），没有行尾注释 —— 所以 `set // 上个位置` 是**真语句**，游戏照执行。这类占语料 `reported` 的 222 条，已归入 `annotation`。

## 校准数字（真实蓝图 617 文件 / 2409 块）

- `ir`：**82.0% 的处理器一条都不报**，p50 = 0、p90 = 1；均值 0.650/块是被约 20 个代码生成式蓝图（每个 60–78 条）拉高的。看**干净块占比**，别看均值。
- `values`：2396 块里 4.1% 有信号（常量分支 0.120/块、可证 null 0.060/块），39 ms/块，未收敛 0。
- `pack`：2420 块里只有 **3 块**（0.1%）用了打包，bit peel（`x & -x` + `log2`）**0 块**。

出现率差三个数量级 ⇒ **`ir` 是 linter，`pack` 是"点开就说话"的专用检查**，不能拿同一把尺子量。`pack` 也不是 linter：0.1% 的命中率意味着"报了就是有话说"，但"没报"不代表没打包。

## values 的语言事实（不记住会误判）

- `equal x null` ⇔ `x.num() == 0` —— **对从未赋值的变量恒真**（`LVar` 默认 `numval=0`、`isobj=false`）。只有 `===` 区分 null 与 0。（`ConditionOp.java:31-40`）
- NaN / ±Infinity 在 `LVar.setnum()` 里被**静默转成 null**。这就是 `op logn x 2` 在 `x=0` 时得 `-Infinity` → null、从而成为按位剥离循环退出条件的原因 —— **令牌流里没有任何字面信息说"退出"，只有值域说得清**。
- 所以 `op rand` / `op noise` 的值**不能建模成 NaN**（那会变成"必定是 null"）；本项目里它们一律是 ⊤。

## 边界：这些工具证明不了的事

- **不跨处理器**。别的处理器 `read x cell1 "名字"` 看不见；实测 0 例，但 `ir` 报了死存储仍要自查有没有跨块约定。
- **只判"值有没有人用"，不判"值算得对不对"**。`op add dx dy dx` 想算距离却写成加法，`ir` 不报。
- **外部输入一律 ⊤**。`sensor` / `getlink` / `ulocate` 拿到的都是运行期状态 ⇒ 一半变量退化成未知，`values` 只能对纯计算链说话。
- `values` 3 轮后按变量放宽；`cost` 在 1000 条处截断并显式打 `>=`（那是下界，不是总量）。
- `pack` 只认**同一 `src` 上 ≥2 个不同指数**的 `op idiv`，不重建表达式；`MIN_EXP = 3`。

## 典型流程

1. `report --brief` 看 `VERDICT`，先确定有没有 `check` 报错。
2. 看「先看这里」指向哪层，只展开那一节（`--only ir` 之类）。
3. 展开前对照上面的**校准数字**，判断这一层的命中率是"正常噪声"还是"确实该看"。`ir` 报 1 条是常态，报 60 条要看生成方式。
4. 需要逐条证据时用 `--all` / `--trace VAR`，或退回单项工具拿更细的输出。

单项工具仍然可用（同一份 `tools/` 里）：`mlog.py check|ir|values|pack|explain|cmd|id|item|parse|gen`。`explain` 是查**某条指令哪个参数是输出**的唯一权威来源 —— 官方文档有 8 条指令的参数顺序是错的，`explain` 会直接打 `!! DOCS WRONG`。

## 维护

这个技能的 `tools/` 是从 `mindustry-blueprint/tools/` **整份拷过来的副本**，不是链接 —— 目的就是让目录能被单独拷走。改了任何模块之后在仓库里跑：

```
python mindustry-blueprint/tools/sync_mlogagent.py          # 重新拷贝 + 重写 MANIFEST.sha256
python mindustry-blueprint/tools/sync_mlogagent.py --check  # 只比对，过期时 exit 1
```

本目录的 `SKILL.md` **不参与同步**（它只属于这个技能；蓝图技能有自己的一份）。两份工具不一致时 `mlogagent.py info --verify` 会报 `MISMATCH` 并指出是哪几个文件。
