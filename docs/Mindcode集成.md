# Mindcode 集成

Mindcode（<https://github.com/cardillan/mindcode>）是一个把高级语言 `.mnd` 编译成
Mindustry 逻辑 `.mlog` 的第三方编译器。本仓库不内嵌它，而是把它当作**外部工具**驱动：
`tools/mindcode.py` 负责定位 jar/JRE、跑编译、把 `stderr` 上的诊断解析成结构化的
`{file, line, col, kind, message}`，MCP 层再包成统一的 evaluation 信封。

这样做的理由：编译器是别人的代码，版本半年一动；把「怎么找到它」「它挂了怎么办」
隔离在一个薄包装里，工具链的其余部分就只依赖一个稳定的函数签名。

## 一、接口

```python
import sys; sys.path.insert(0, "tools")
import mindcode

mindcode.locate()                       # {"jar","java","version","ok","notes"}
mindcode.compile_source(src, *, target="7.0", optimize=True, timeout=60, workdir=None)
mindcode.compile_file(path, **kw)       # 诊断里带调用者的路径，而不是 "<source>"
mindcode.doctor(smoke=True)             # 候选表 + 兼容性 + 真编译冒烟
```

`compile_source()` 返回：

```json
{"ok": true,
 "mlog": "print \"total=15\"\nprintflush message1",
 "diagnostics": [],
 "stats": {"ast_nodes": 29, "instructions": 10, "optimized_instructions": 2,
           "timings_ms": {"parsed": 103, "compiled": 280, "optimized": 161},
           "raw": "Mindcode: 29 AST nodes, ...", "exit_code": 0, "timed_out": false},
 "tool": {"name": "mindcode", "version": "3.19.3", "jar": "...", "java": "..."},
 "elapsed_ms": 992,
 "source_sha256": "...",
 "notes": []}
```

`ok` 由「拿到了代码且没有 error 级诊断」决定，**不看退出码**：编译器在写不出输出、
或者被环境问题打断时也会返回非零，那与「源码有语法错」不是一回事。

CLI：

```bash
python tools/mindcode.py version
python tools/mindcode.py doctor --json
python tools/mindcode.py compile demo.mnd -o demo.mlog --target 7.0 [--no-optimize] [--json]
python tools/mindcode.py decompile demo.mlog -o draft.mnd
python tools/mlog.py extract-logic demo.msch --format mindcode --all --out-dir drafts
python tests/mindcode/run_mindcode_tests.py      # 退出码 3 = 这台机器上没有可用编译器
```

反编译复用 Mindcode 的 `dm`。省略 `-o` 时将草稿输出到终端。
`extract-logic --format mindcode` 还可以接收蓝图粘贴码或 mlog，先恢复标签名再反编译。
输出里的标签和 `goto` 需要手动改成循环、条件等结构才能重新编译；它无法还原原始源码。

MCP 工具：`mindcode_compile`（`source` 或 `path`，`target`、`optimize`、`out`、`level`）。
编译失败返回 `failure_type="compilation_error"`，诊断逐条带 `line`/`col`；
没有可用编译器时返回 `unsupported_environment` —— 那不是用户源码的错。

## 二、为什么默认用 3.19.3，而不是最新版

**v3.21.0 在本机会死锁**，任何真正干活的子命令（`cm`、`pm`）都会永久挂住，
而 `--version`、`cm --help` 秒回，很容易误判成「jar 是好的」。

`jcmd <pid> Thread.print` 的 main 线程栈（截断到关键帧）：

```
java.io.FileInputStream.readBytes
 <- java.lang.Process$PipeInputStream.read
 <- java.io.BufferedReader.readLine
 <- dev.dirs.Util.runCommands(Util.java:203)
 <- runWinCommands:233 <- getWinDirs:164
 <- ProjectDirectories.fromPath:255 <- ProjectDirectories.from:309
 <- UpdateChecker.checkForUpdates(UpdateChecker.java:26)
 <- ToolAppAction.handle(ToolAppAction.java:42)
 <- Main.handleCommandLine(Main.java:61)
```

根因（已对照源码）：`Main.java:40` 只把 `--no-update-check` 注册在**顶层 parser** 上，
而 `ToolAppAction.java:41` 从**子命令 namespace** 读 `arguments.getBoolean("no-update-check")`，
永远拿到 `null`，于是无条件执行更新检查；更新检查用 dev.dirs 定位用户目录，dev.dirs 在
Windows 上会 `powershell -NoProfile -EncodedCommand` 跑内联 C#（`Add-Type` +
`SHGetKnownFolderPath`），Java 侧只读 stdout、不排空 stderr，管道写满即互锁。

实测绕不过：`--no-update-check` 放前放后、stdin 接 NUL、换 jar 副本、删掉代理环境变量——
全部照挂。手动复现那段 PowerShell 本身 4.7 秒正常返回，所以卡的是 Java 侧的管道处理。

因此集成基线是 **v3.19.3**（`out/_mindcode/mindcode-3.19.3.jar`，或任何
`MINDCODE_JAR` 指向的同版本 jar）。`doctor` 会**真编译一次**当探针——只有这样才测得
出 3.21 的死锁，光看 `--version` 是测不出的。

## 三、定位顺序

jar（首个可用的胜出，`MINDCODE_JAR` 一旦设置就是**唯一**候选，不会再偷偷换别的）：

1. `$MINDCODE_JAR`
2. `out/_mindcode/mindcode-3.19.3.jar`（本仓库约定的落点）
3. `out/_mindcode/mindcode.jar`
4. `C:\Users\<user>\src\mindcode-dist\mindcode.jar`（上游下载）

java（同样，`MINDCODE_JAVA` 一旦设置就是唯一候选）：

1. `$MINDCODE_JAVA`
2. `out/jre21/.../java.exe`（仓库自带，**装不了 3.19.3**，会被探测跳过）
3. `out/_mindcode/jdk-25.0.5+8-jre/bin/java.exe`（实际生效的那个）

`PATH` 上的 java 8 被**故意忽略**：Mindcode 要 Java 22+，用它只会得到误导性的报错。

**Mindcode 3.19.3 需要 Java 22+**（class file 66.0）。仓库自带的 JRE 21 装不了它，
会报：

```
java.lang.UnsupportedClassVersionError: ... class file version 66.0,
this version of the Java Runtime only recognizes class file versions up to 65.0
```

`doctor` 把这类组合跳过并写进 `notes`，所以「有 JRE」不等于「能编译」。

## 四、四个实测陷阱（都已在本模块里处理）

| 现象 | 原因 | 处理 |
|---|---|---|
| 良好源码报 `1:1 Parse error: extraneous input '?'` | 源文件带 UTF-8 BOM | 临时源文件按 `utf-8`（无 BOM）写；读入用 `utf-8-sig`；`source_sha256` 不含 BOM |
| 诊断中文乱码 | 编译器按 ANSI 代码页（cp936）输出，mlog 本身是 UTF-8 | 三级解码：`utf-8` → `locale.getpreferredencoding(False)` → `utf-8 replace` |
| 超时了却返回完整统计、`exit_code=0` | `taskkill /F /T` 在本机对活进程返回 255 且要 5–10 s | 先 `proc.kill()`（实测 0.3 s 生效），`taskkill` 只作孙进程清扫、上限 2 s |
| 编译「成功」却没有输出文件 | 目标目录的 `-o` 写不进去时编译器退出码 1 但无 error 诊断 | 检测到「无文件、无 error 诊断」时用 `-o -` 重跑，从 stdout 取回代码并记 `notes` |

错误格式（stderr，一行一条）：

```
D:\...\bad.mnd:1:11 Parse error: missing semicolon after '1'
D:\...\bad.mnd:2:7  Parse error: unexpected '"'
```

## 五、和其它部分的关系

- **静态检查**（`tools/mlogcheck.py`）检查的是编译产物 mlog，不是 `.mnd`；
- **仿真**（`tools/mlogsim.py`）只吃 mlog —— 所以 Mindcode 程序的验证链是
  `.mnd → compile → mlog → check → sim → assertions`；
- **统一信封**（`tools/mlog_eval.py`）把它们串成一次调用：`mlog_validate` 或
  `mindcode_compile` 的输出都是同一个 `mlog-eval/v1` 结构，失败原因走同一套词表。

## 六、还没做的

- `.mnd` 到 mlog 的**源码映射**（错误行号回映到 Mindcode 源）只做了编译期
  `line/col`，运行时逻辑（mlog 行号 → `.mnd` 行号）尚未建表；
- 知识库（`knowledge/`）里还没有 Mindcode 语法条目，目前只有本文档；
- 把 `mindcode.py` 纳入 `tools/mlogagent.py` 的镜像集合（skill 分发）未做——
  它依赖一个 33 MB 的 jar，随 skill 分发的意义不大，需要时再议。
