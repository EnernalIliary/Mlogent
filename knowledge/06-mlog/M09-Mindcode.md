---
id: MLOG.MIND.001
title: Mindcode 编译前端：.mnd → mlog 的入口、版本裁决与失败分类
domain: mlog
status: active
ver: [v160.7_rt]
conf: S
src:
  - tools/mindcode.py:113-120
  - tools/mindcode.py:157-177
  - tools/mindcode.py:267-290
  - tools/mindcode.py:487-569
  - tools/mindcode.py:704-710
  - tools/mlog_mcp.py:531-564
  - tools/mlog_eval.py:51-59
  - docs/Mindcode集成.md:54-84
data:
  - 06-mlog/instructions.json#meta
depends: [MLOG.EXEC.001]
tags: [mindcode, 编译前端, 版本裁决, 诊断, MCP]
tokens: 1964
---

# M09 Mindcode 编译前端

## 一句话

Mindcode 是「把高级语言 `.mnd` 编译成 mlog」的**外部 Java 编译器**；本仓库不内嵌它，只用薄前端 `tools/mindcode.py` 把「找 jar/JRE → 跑 `cm` → 把 stderr 解析成 `file:line:col`」这一层固定下来，CLI / Python API / MCP 三种入口共用同一个结果字典。

## 规则 / 公式

### 1. 它是什么

- **外部进程，不是库**。唯一接口是一次子进程调用：`java -jar mindcode.jar cm <src.mnd> -o <out.mlog> -l <out.log>` [src: tools/mindcode.py:515-516]。
- **只做一件转换**：`.mnd` → mlog 文本。静态检查、仿真、断言都不在它这里，所以 Mindcode 程序的验证链是 `.mnd → compile → mlog → check → sim → assertions` [src: docs/Mindcode集成.md:129-135]。
- **产物是普通 mlog**，因此照样受引擎硬限制约束（1000 条指令、400 字符文本缓冲，见 M01 / M08）。

### 2. `cm` 与 `pm` 的区别

| 子命令 | 别名 | 输入 | 输出 | 本仓库是否调用 |
|---|---|---|---|---|
| `cm` | compile-mindcode | `.mnd` 源码 | `.mlog` 文本 | **是，唯一用到的** [src: tools/mindcode.py:515] |
| `pm` | process-mlog / dm / decompile-mlog | `.mlog`（文件或游戏内处理器） | 处理后/反编译结果 | 否 |
| `cs` | compile-schematic | schematic 定义 | `.msch` | 否 |
| `ps` | process-schematic | `.msch` | — | 否 |

来源：`java -jar mindcode-3.19.3.jar --help` 的 Actions 表 [实测: 本机 3.19.3 jar]。一句话记：**`cm` 是正向（写代码变 mlog），`pm` 是反向（拿 mlog 做处理/反编译）**，本仓库只走正向。

### 3. 三种入口

| 入口 | 怎么调 | 返回 | 什么时候用 |
|---|---|---|---|
| CLI | `python tools/mindcode.py compile FILE.mnd -o FILE.mlog --target 7.0 [--no-optimize] [--json]`；`doctor`；`version` | 退出码 0/1/2 + 可选 JSON 行 | 人手动跑、写 CI 步骤 [src: tools/mindcode.py:809-831] |
| Python API | `locate()`、`compile_source(text, *, target="7.0", optimize=True, timeout=120.0, workdir=None)`、`compile_file(path, **kw)`、`doctor(smoke=True)` | 8 键结果字典（见 §7） | 仓库内其它脚本 [src: tools/mindcode.py:582-621] |
| MCP | `mindcode_compile(source\|path, target, optimize, out, level)`；`mlog_validate(mind\|mnd_path, ticks, expect, level)` | `mlog-eval/v1` 信封 | 模型侧：一个调用拿到「编过了没 + 编译产物是否真对」[src: tools/mlog_mcp.py:155-193] |

`mlog_validate` 的 `mind`/`mnd_path` 是**先编译再验证**：编译失败时 stage 直接停在 `compilation`，不会再假装去跑静态或仿真 [src: tools/mlog_mcp.py:595-604]。

MCP 侧**目前共 11 个工具**，Mindcode 只从上面这两个进出：`mlog_sim` 吃的是 mlog（`path`/`logic`）而不是 `.mnd`，它后来新增的 `scene`/`project`/`project_every`/`rt` 是沙盘投影参数，与编译链路无关 [src: tools/mlog_mcp.py:121-154]。

### 4. 版本与 JVM 定位顺序

jar（首个探测通过的胜出）：

1. `$MINDCODE_JAR`（设了就是**唯一**候选）
2. `out/_mindcode/mindcode-3.19.3.jar`（本仓库约定的落点，默认生效）
3. `out/_mindcode/mindcode.jar`（可能是 3.21.0，即会死锁的那个）
4. `~/src/mindcode-dist/mindcode.jar`

java（同样，`$MINDCODE_JAVA` 设了就是唯一候选）：

1. `$MINDCODE_JAVA`
2. `out/jre21/jdk-21.0.5+11-jre/bin/java.exe`（**装不了 3.19.3**，探测后跳过）
3. `out/_mindcode/jdk-25.0.5+8-jre/bin/java.exe`（实际生效的那个）

顺序来自候选表本身 [src: tools/mindcode.py:113-120] 与两个 `_candidates()` [src: tools/mindcode.py:157-177]。

两个「为什么」：

- **为什么忽略 PATH 上的 java**：本机 PATH 的 java 是 **Java 8**，Mindcode 要 **Java 22+**；用它只会得到 `UnsupportedClassVersionError` 甚至更晦涩的 `LinkageError`，所以候选表**故意不含 PATH**，找不到可用组合时直接 `ok=False` [src: tools/mindcode.py:53-56]。
- **为什么 JRE 21 也不够**：3.19.3 编成 class file **66.0**（= Java 22），JRE 21 只认到 **65.0**。所以 java 候选不是 `stat()` 一下就算可用，而是**真跑一次 `--version` 探测**，把这类失败归类为 `incompatible` 写进 `notes` 再跳到下一个 [src: tools/mindcode.py:267-290, 58-66]。

### 5. 为什么基线是 3.19.3：3.21.0 会死锁

| 事实 | 依据 |
|---|---|
| 3.21.0 的 `--version`、`cm --help` **秒回**，但 `cm` 永久挂住 | `--version` 只做版本号，不触发更新检查 [src: docs/Mindcode集成.md:56-57] |
| 根因：`Main.java:40` 只把 `--no-update-check` 注册在**顶层 parser**，而 `ToolAppAction.java:41` 从**子命令 namespace** 读 → 永远 `null` → 无条件执行更新检查 | [src: docs/Mindcode集成.md:73-77] |
| 更新检查用 `dev.dirs` 在 Windows 上跑 `powershell -EncodedCommand` 内联 C#；Java 侧只读 stdout、**不排空 stderr**，管道写满即互锁 | [src: docs/Mindcode集成.md:74-77] |
| 因此版本探测**测不出**死锁，只有真编译能测出 | `doctor` 的 `smoke-compile` 就是为此存在 [src: tools/mindcode.py:664-681] |

包装侧的处置：3.21 仍保留在候选表里（搜索顺序使然），但一旦被选中就写进 `warnings`/`notes` [src: tools/mindcode.py:362-367]；编译超时时再补一句「换 3.19.3」的提示 [src: tools/mindcode.py:532-534]。

### 6. 错误格式与诊断三列

编译器把诊断写在 **stderr**，一行一条：

```text
<绝对路径>:<行>:<列> <类别>: <消息>
```

`_DIAG_RE` 抓前三个字段 `file/line/col` [src: tools/mindcode.py:131]，剩下部分再交给 `_CATEGORY_RE` 拆 `kind/message` [src: tools/mindcode.py:132-135]。关键：**只有 parse/syntax/compile/internal/runtime error 与 warning/note/info 才有显式类别前缀**；语义错误没有前缀，此时 `kind` 兜底为 `error`、`message` 取整行剩余 [src: tools/mindcode.py:430]。

| stderr 长什么样 | 解析结果 | 依据 |
|---|---|---|
| `bad.mnd:1:6 Parse error: missing semicolon after '1'` | kind=`Parse error`, line=1, col=6 | 实测 |
| `bad.mnd:1:1 error` 形态：`Function 'sensor': wrong number of arguments (expected 2, found 3).` | kind=`error`（无类别前缀） | 实测 |
| `Automatically added missing 'printflush(message1);' call …` | **不进 diagnostics**，进 `notes`（不匹配 `_DIAG_RE` 的行都算编译器闲聊） | [src: tools/mindcode.py:424-427] |
| `java.lang.UnsupportedClassVersionError …` | 归 `incompatible`，进 `notes` 并跳过该 java 候选 | [src: tools/mindcode.py:279-284] |

另外两件容易漏的：诊断文本按 **ANSI 代码页**输出（本机 cp936），所以每个流走「UTF-8 → locale 代码页 → replace」三级解码 [src: tools/mindcode.py:188-202]；CLI 下诊断打到 stderr、体会是 `path:line:col: kind: message` [src: tools/mindcode.py:713-720]。

### 7. JSON 返回形状

`compile_source` / `compile_file` 恒定 8 个键 [src: tools/mindcode.py:471-475]：

| 键 | 含义 |
|---|---|
| `ok` | 由「**拿到了代码** 且 **没有 error 级诊断**」决定，**不看退出码** [src: tools/mindcode.py:561-562] |
| `mlog` | 归一化后的 mlog（LF、恰好一个结尾换行）；失败时为 `null` |
| `diagnostics[]` | `{file, line, col, kind, message}` 五字段 [src: tools/mindcode.py:435-436] |
| `stats` | `ast_nodes` / `instructions` / `optimized_instructions` / `timings_ms{parsed,compiled,optimized}` / `raw` / `exit_code` / `timed_out` [src: tools/mindcode.py:394-396] |
| `tool` | `{name, version, jar, java}` [src: tools/mindcode.py:493-494] |
| `elapsed_ms` | 墙钟 |
| `source_sha256` | 对**去掉 BOM 后**的文本取哈希 |
| `notes` | 包装自己的话：跳过的 java 候选、编译器的闲聊、`-o -` 兜底重跑 |

MCP 层再包一层 `mlog-eval/v1` 信封：`schema / ok / stage / failure_type / message / level / levels / diagnostics / artifacts / next_steps / trace / elapsed_ms` [src: tools/mlog_eval.py:122-139]（`mlog_validate` 还会补一个 `program` 字段标明是哪段程序 [src: tools/mlog_mcp.py:617]），`level` 三档 `summary|diagnostics|full` 控制体积 [src: tools/mlog_eval.py:62, 85-103]；`summary` 档里编译产物以 `mlog_ref` 指针形式给出而不是整段正文 [src: tools/mlog_mcp.py:516-528]。

### 8. `unsupported_environment` 与 `compilation_error` 的分界

**契约上**：源码编不过 → `compilation_error`（下一步是改源码）；这台机器上没有能跑的编译器 → `unsupported_environment`（下一步是修环境，**别再重试**）[src: tools/mlog_mcp.py:549-555]。

**实现上判定的是「`tool.jar` 和 `tool.java` 都非空」** [src: tools/mlog_mcp.py:554-555, 587-588]，而 `mindcode.py` **无论成功失败都会把候选路径字符串填进 `tool`** [src: tools/mindcode.py:493-494, 338-341]。后果（实测两条）：

| 场景 | 实际 failure_type | message |
|---|---|---|
| `MINDCODE_JAR` 指向不存在的 jar | `compilation_error` | `mindcode unavailable: no mindcode jar found: …` |
| `path` 指向不存在的 `.mnd` | `unsupported_environment` | `FileNotFoundError: …` |

也就是说：**环境类失败只有早退分支（读不到文件 / 非 UTF-8，`tool` 的 jar、java 为 `null`）才会落到 `unsupported_environment`** [src: tools/mindcode.py:601-616]；编译器「在但跑不动」的那条路会被标成 `compilation_error`。

第一条实测里信封是**自相矛盾**的：`failure_type=compilation_error`（含义「你的源码错了」），而同一份 `diagnostics[0]` 是 `{"kind":"environment","line":0,"col":0,"message":"mindcode unavailable: …"}`（含义「这台机器没有编译器」）——kind 与 `line:0,col:0` 由 `mindcode.py` 在 `res["ok"]` 为假时直接构造 [src: tools/mindcode.py:497-502]。所以**信封的 `failure_type` 不可单独采信**。同一件事在 CLI 侧则被判成「环境」——退出码 2 [src: tools/mindcode.py:704-710]；两个入口对同一失败的归因不一致，这也是本文要求「先看 kind」的直接原因。

正确的读法：**先看 `diagnostics[0].kind`，再看 `failure_type`**。`environment` / `timeout` / `io` / `encoding` 这四种是环境与输入问题，不是源码错 [src: tools/mindcode.py:144]——CLI 的 `_exit_code()` 正是按这个集合返回 **2**（源码错返回 1）[src: tools/mindcode.py:704-710]。

## 数值

| 量 | 值 | 来源 |
|---|---|---|
| 集成基线版本 | 3.19.3 | `mindcode.py version` 实测 |
| 最低 Java | 22（class file 66.0） | [src: tools/mindcode.py:58-64] |
| 仓库自带 JRE 21 | 21.0.5+11（class file 65.0，不兼容，被跳过） | [src: tools/mindcode.py:119, 279-284] |
| 实际使用的 JRE | 25.0.5+8 | [src: tools/mindcode.py:120] |
| `--version` 探测上限 | 30 s | [src: tools/mindcode.py:122] |
| 默认编译超时 | 120 s | [src: tools/mindcode.py:582-583] |
| CLI 退出码 | 0 成功 / 1 源码没编过 / 2 跑不起来（环境、超时、IO） | [src: tools/mindcode.py:15-18, 704-710] |
| 失败词表 | 7 个值（compilation_error … simulation_real_difference） | [src: tools/mlog_eval.py:51-59] |
| 简单程序实测 | 6 AST → 3 指令（优化后 2），compiled 195 ms | 实测 `print(1);` |
| 求和循环实测 | 23 AST → 10 指令 → **2** 条（常量折叠） | 实测 `for i in 1..5` |
| 同一源 `-O 0` | 11 条指令、11 行 mlog | 实测 |

## 源码锚点

| 位置 | 内容 |
|---|---|
| `tools/mindcode.py:113-120` | 候选表常量：`PREFERRED_JAR` / `FALLBACK_JAR` / `USER_JAR` / `JAVA_21` / `JAVA_25` |
| `tools/mindcode.py:157-177` | `_jar_candidates()` / `_java_candidates()`：环境变量一旦设置即唯一候选 |
| `tools/mindcode.py:267-290` | `_probe_version()`：真跑 `--version`，先认 `UnsupportedClassVersionError` 再认版本号 |
| `tools/mindcode.py:308-381` | `_resolve()`：候选 × 探测的笛卡尔积，首个可用的胜出，其余进 `notes` |
| `tools/mindcode.py:487-569` | `_compile()`：临时目录、BOM-free 写盘、`cm` 命令行、超时/`-o -` 兜底 |
| `tools/mindcode.py:416-441` | `_parse_diagnostics()` / `_error_diags()` |
| `tools/mindcode.py:596-621` | `compile_file()`：`utf-8-sig` 解码（顺带剥 BOM）+ io/encoding 早退 |
| `tools/mindcode.py:646-698` | `doctor()`：候选表 + 兼容性 + **真编译冒烟** |
| `tools/mlog_mcp.py:531-564` | `mindcode_compile`：结果 → `mlog-eval/v1` 信封 |
| `tools/mlog_mcp.py:567-592` | `_compile_mind()`：`mlog_validate(mind=…)` 的编译前置 |
| `tools/mlog_eval.py:51-80` | 失败词表与 `NEXT_STEPS` 映射 |

## 实测与反例

- ✅【E】`sum = 0; for i in 1..5 do sum += i; end; print("total=", sum); printflush(message1);` → `23 AST nodes, 10 unoptimized, 2 optimized`，产物只有两行：`print "total=15"` + `printflush message1`。
- ✅【E】同一源加 `-O 0`（`optimize=False`）→ 11 条指令、11 行 mlog，循环原样保留，末尾带 `print "Compiled by Mindcode 3.19.3 …"` 签名行。
- ✅【E】3.21.0：`locate()` 返回 `ok=True, version=3.21.0`，`compile_source(timeout=8)` 在 8 s 被杀，诊断 `kind=timeout`、`message` 里带「use the 3.19.3 jar instead」。
- ✅【E】BOM：把带 UTF-8 BOM 的 `.mnd` **直接喂 jar** → rc=1，stderr 首行 `<path>:1:1 Parse error: extraneous input '?' …`；同一个文件走 `compile_file()` → `ok=True`（BOM 在解码处就被 `utf-8-sig` 剥掉 [src: tools/mindcode.py:609]）。
- 反例（不成立边界）：**「BOM 会让编译失败」对包装而言不成立**——`_strip_bom()` 与 BOM-free 写盘都做了 [src: tools/mindcode.py:461, 512]；这个坑只教训绕过包装直接调 jar 的人。
- 反例：**「Mindcode 源码里的变量编译后还在」不成立**。默认 `-O` 会把整段循环常量折叠掉，`sum` 运行时根本不存在；于是 `mlog_validate(mind=…, expect=[{var:"sum", op:"==", value:15}])` 得到 `failure_type=assertion_failed`，`levels` 是 `execution=true / static=true / simulation=false`（本次实测）。要在 Mindcode 上做断言就断言**可观察副作用**（文本缓冲、内存格、方块状态），不要断言源变量名。
- 反例：**「退出码 1 就是语法错」不成立**——`ok` 不看退出码 [src: tools/mindcode.py:561-562]；`cm --help` 本身就返回 1。
- 【未做项】运行时源码映射（mlog 行号 → `.mnd` 行号）没有建表，只有编译期 `line/col`；`pm` 反向路径未接入；本文只覆盖**前端**，不覆盖 Mindcode 语言语法本身 [src: docs/Mindcode集成.md:137-142]。

## 常见误解

1. **「`--version` 能跑就说明 jar 能用」** —— 错。3.21.0 的 `--version` 与 `cm --help` 都秒回，`cm` 却永久挂住。判据是 `doctor` 的 `smoke-compile`，它真编译一个小程序 [src: tools/mindcode.py:664-681]。
2. **「PATH 上有 java 就能编译」** —— 错。PATH 上是 Java 8，Mindcode 要 22+，候选表**故意不含 PATH**；`doctor` 只会把 PATH 的 java 写进 `notes` 提醒你它被忽略了 [src: tools/mindcode.py:117-120, 691-693]。
3. **「有 JRE 就能编译」** —— 错。仓库自带 JRE 21 存在但装不了 class file 66.0 的 jar，必须**探测**而不是 `stat()`，否则会把「有 JRE」错当成「能编译」 [src: tools/mindcode.py:58-66]。
4. **「`compilation_error` 一定是我的源码写错了」** —— 不对，环境类失败在当前实现里也会被标成它（见 §8），要配合 `diagnostics[0].kind` 一起读 [src: tools/mlog_mcp.py:554-555]。

## 相关

- MLOG.EXEC.001 执行模型（编译产物要吃的 tick 预算与 1000 条上限）
- MLOG.PERF.001 性能与限制（400 字符文本缓冲等硬上限，编译器生成的报错检查也按这个来）
- `docs/Mindcode集成.md`（同主题长文：接口、四个实测陷阱、版本裁决）
- 数据表：`06-mlog/instructions.json#meta`（编译产物落到哪 73 条指令）
