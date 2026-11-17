# 06-mlog 索引（文件名以 `_` 开头 ⇒ 门禁 check_kb.py 不当作文章扫描）

mlog 语言层：9 篇文章 + 2 个机读表。写作口径来自 v159.3 源码（语义）与 v160.7 jar/真机（数值）。

## 文章

| 文件 | id | 行数 | 主题 |
|---|---|---|---|
| M01-执行模型总览.md | MLOG.EXEC.001 | 116 | tick / @counter / 预算 / 程序步骤 |
| M02-变量与作用域.md | MLOG.VAR.001 | 125 | LVar 三态、null、内置变量 |
| M03-控制流.md | MLOG.FLOW.001 | 120 | jump 8 条件、循环、wait、改写 @counter |
| M04-读写与感知.md | MLOG.IO.001 | 131 | read/write/sensor/radar/ulocate/getlink/lookup |
| M05-绘制与文本.md | MLOG.DRAW.001 | 138 | draw/print/printflush/@message/颜色打包 |
| M06-世界交互.md | MLOG.WORLD.001 | 130 | control/setrule/world processor 26 指令 |
| M07-单位与逻辑控制.md | MLOG.UNIT.001 | 117 | ubind/ucontrol 21 子命令/@unit 生命周期 |
| M08-性能与限制.md | MLOG.PERF.001 | 116 | 预算上限/延迟/卡顿/内存上限 |
| M09-Mindcode.md | MLOG.MIND.001 | 202 | .mnd→mlog 编译前端：cm/pm、三种入口、版本裁决、诊断三列、失败分类 |

## instructions.json（73 条指令）

顶层：`meta` + `instructions[]`。按 docs 分组计数：unit 24 / control 5 / op 6 / io 6 / block 6 / world 26。

| 字段 | 含义 |
|---|---|
| num | 文档章节序号 |
| name | 助记符（mlog 关键字） |
| title | 中文名 |
| category | 分组（上表 6 类） |
| format | 导出格式（**72 条有值，`draw` 为 null**） |
| arity | 参数槽数 |
| params[] | 槽位名（文本序） |
| defs[] / uses[] | 被写 / 被读的槽下标（0 = 助记符后第一个参数，来自 `instr_semantics.json`） |
| tokens | 该指令在文本里的 token 数 |
| since_build / ver | 版本 |
| desc | 一句话功能 |
| doc_params[] | docs 参数表原样（可能是占位符 `1`/`2`） |
| trap | **23 条**带坑提示 |
| unverified | docs 有 `## 未验证内容` 小节（45 处命中） |
| src | 源码 `文件:行` |

### meta.discrepancies（cmd_index 与 docs 冲突，**以 docs 为准**，7 条）

| 指令 | cmd_index 写法 | docs/源码写法 |
|---|---|---|
| getblock | `<result> <x> <y> <layer>` | `<layer> <result> <x> <y>` |
| setblock | `<x> <y> <block> <team> <rotation> <layer>` | `<layer> <block> <x> <y> <team> <rotation>` |
| weathersense | `<weather> <result>` | `<result> <weather>`（def 在 0 号） |
| spawnwave | `<natural> <x> <y>` | `<x> <y> <natural>` |
| playsound | 7 参（把 pan/x 合并） | 8 参：`<positional> <id> <volume> <pitch> <pan> <x> <y> <limit>` |
| status | apply / clear | true / false（源码字段是 boolean clear） |
| uradar | 7 参全有效 | 第 5 槽是死槽（源码传 null） |

## enums.json（13 组枚举）

| 键 | 数量 | 用途 |
|---|---|---|
| RadarTarget | 8 | radar/uradar 目标过滤 |
| RadarSort | 5 | 排序键 |
| LLocate | 4 | ulocate 定位类型 |
| LUnitControl | 21 | ucontrol 子命令 |
| BlockFlag | 18 | control/sensor 的 block flag |
| ControlType | 5 | control 类型 |
| ConditionOp | 8 | jump 条件 |
| GraphicsType | 16 | draw 子命令 |
| LogicRule | 29 | setrule 规则名 |
| FetchType | 8 | fetch 取哪类实体 |
| ContentType | 18 | lookup/fetch 的内容类型（含 `_UNUSED`） |
| LogicOp | 45 | op 运算 |
| LAccess | 77 | sensor 属性（v160.7 jar 反射） |

## 用法

```bash
# 查一条指令 grep -A2 '"name": "ucontrol"' instructions.json
# 统计带坑指令 python -c "import json;d=json.load(open('instructions.json',encoding='utf-8'));print([i['name'] for i in d['instructions'] if i.get('trap')])"
```

## 与其它层的边界

- **06-mlog**：语言本身（怎么写才符合语义）。
- **01-execution**：引擎实现细节（为什么这样、源码在哪个文件）。
- **08-evidence**：每条结论的证据行号（claims.jsonl）。

同一事实在两层出现时，06-mlog 给「怎么写」、01-execution 给「为什么 + 文件:行」，不要互相抄细节。

## 变更记录

| 日期 | 变更 | 依据 |
|---|---|---|
| 2026-11-08 | task-14 扩写：M03 加 ConditionOp 8 值全表 + test() :32-33 短路真相；M06 加 TileLayer 四层可写性表 + layer 在 0 号槽 + message/cutscene/query 四枚举；M07 加 ucontrol 21 行参数表（tile 坐标口径）+ radar target 8 / sort 5 / uradar 第 5 槽死槽 + ulocate 输出语义 | ConditionOp.java:6-13,:31-40；TileLayer.java:3-9；LUnitControl.java:4-24；RadarTarget.java:6-14；RadarSort.java:6-11；LLocate.java:3-7 |
| 2026-11-08 | LogicRule 计数 30 -> 29（v159.3 源码逐行数） | LogicRule.java:4-34 |
| 2026-11-17 | 新增 M09-Mindcode.md（MLOG.MIND.001，202 行）：编译前端 tools/mindcode.py 的三种入口、jar/java 定位顺序、3.21.0 死锁与 3.19.3 裁决、诊断三列、BOM 边界、`unsupported_environment` 与 `compilation_error` 分界 | tools/mindcode.py:113-120,:267-290,:487-569,:704-710；tools/mlog_mcp.py:531-564；docs/Mindcode集成.md:54-84 |
