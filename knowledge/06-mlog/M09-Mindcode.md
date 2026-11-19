---
id: MLOG.MIND.001
title: "The Mindcode compile front end: the .mnd → mlog entry points, version arbitration and failure classes"
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
tags: [mindcode, compile front end, version arbitration, diagnostics, MCP]
tokens: 1964
---

# M09 The Mindcode compile front end

## In one sentence

Mindcode is an **external Java compiler** that turns a high-level `.mnd` source into mlog; this repo does not embed it. A thin front end, `tools/mindcode.py`, pins down the layer "locate a jar/JRE → run `cm` → parse stderr into `file:line:col`", and the CLI / Python API / MCP entry points all share one result dict.

## Rules / formulas

### 1. What it is

- **An external process, not a library**. The only interface is one subprocess call: `java -jar mindcode.jar cm <src.mnd> -o <out.mlog> -l <out.log>` [src: tools/mindcode.py:515-516].
- **It performs one conversion only**: `.mnd` → mlog text. Static checks, simulation and assertions are not its job, so the verification chain for a Mindcode program is `.mnd → compile → mlog → check → sim → assertions` [src: the integration doc (docs/Mindcode集成.md:129-135)].
- **The output is ordinary mlog**, so it is subject to the same engine hard caps (1000 instructions, 400-character text buffer; see M01 / M08).

### 2. How `cm` and `pm` differ

| Subcommand | Alias | Input | Output | Does this repo call it |
|---|---|---|---|---|
| `cm` | compile-mindcode | `.mnd` source | `.mlog` text | **yes, the only one used** [src: tools/mindcode.py:515] |
| `pm` | process-mlog / dm / decompile-mlog | `.mlog` (a file or an in-game processor) | the processed / decompiled result | no |
| `cs` | compile-schematic | a schematic definition | `.msch` | no |
| `ps` | process-schematic | `.msch` | — | no |

Source: the Actions table of `java -jar mindcode-3.19.3.jar --help` [measured: this machine's 3.19.3 jar]. In one line: **`cm` goes forward (source becomes mlog), `pm` goes backward (take mlog and process/decompile it)**, and this repo only goes forward.

### 3. Three entry points

| Entry point | How to call | Returns | When to use |
|---|---|---|---|
| CLI | `python tools/mindcode.py compile FILE.mnd -o FILE.mlog --target 7.0 [--no-optimize] [--json]`; `doctor`; `version` | exit code 0/1/2 + an optional JSON line | a human running it by hand, CI steps [src: tools/mindcode.py:809-831] |
| Python API | `locate()`, `compile_source(text, *, target="7.0", optimize=True, timeout=120.0, workdir=None)`, `compile_file(path, **kw)`, `doctor(smoke=True)` | an 8-key result dict (see §7) | other scripts in the repo [src: tools/mindcode.py:582-621] |
| MCP | `mindcode_compile(source\|path, target, optimize, out, level)`; `mlog_validate(mind\|mnd_path, ticks, expect, level)` | the `mlog-eval/v1` envelope | the model side: one call answers "did it compile + is the compiled output actually right" [src: tools/mlog_mcp.py:155-193] |

`mlog_validate`'s `mind`/`mnd_path` **compile first, then validate**: when compilation fails the stage stops at `compilation` rather than pretending to run static checks or simulation [src: tools/mlog_mcp.py:595-604].

The MCP side **currently exposes 11 tools**, and Mindcode enters and leaves only through the two above: `mlog_sim` consumes mlog (`path`/`logic`), not `.mnd`, and the `scene`/`project`/`project_every`/`rt` it later gained are sandbox projection parameters unrelated to the compile chain [src: tools/mlog_mcp.py:121-154].

### 4. Version and JVM resolution order

jar (the first candidate that passes probing wins):

1. `$MINDCODE_JAR` (once set it is the **only** candidate)
2. `out/_mindcode/mindcode-3.19.3.jar` (this repo's agreed location, what takes effect by default)
3. `out/_mindcode/mindcode.jar` (possibly 3.21.0, the one that deadlocks)
4. `~/src/mindcode-dist/mindcode.jar`

java (likewise; once `$MINDCODE_JAVA` is set it is the only candidate):

1. `$MINDCODE_JAVA`
2. `out/jre21/jdk-21.0.5+11-jre/bin/java.exe` (**cannot run 3.19.3**, skipped after probing)
3. `out/_mindcode/jdk-25.0.5+8-jre/bin/java.exe` (the one actually used)

The order comes from the candidate table itself [src: tools/mindcode.py:113-120] and the two `_candidates()` functions [src: tools/mindcode.py:157-177].

Two "why"s:

- **Why the java on PATH is ignored**: this machine's PATH java is **Java 8** and Mindcode needs **Java 22+**; using it only yields `UnsupportedClassVersionError` or the even more obscure `LinkageError`, so the candidate table **deliberately leaves PATH out** and reports `ok=False` outright when no usable combination is found [src: tools/mindcode.py:53-56].
- **Why JRE 21 is not enough either**: 3.19.3 is compiled to class file **66.0** (= Java 22) and JRE 21 accepts only up to **65.0**. So a java candidate is not accepted on a `stat()`; it **really runs one `--version` probe**, classifies such failures as `incompatible`, writes them into `notes` and moves to the next candidate [src: tools/mindcode.py:267-290, 58-66].

### 5. Why the baseline is 3.19.3: 3.21.0 deadlocks

| Fact | Basis |
|---|---|
| 3.21.0's `--version` and `cm --help` **return instantly**, yet `cm` hangs forever | `--version` only handles the version number and never triggers the update check [src: docs/Mindcode集成.md:56-57] |
| root cause: `Main.java:40` registers `--no-update-check` only on the **top-level parser**, while `ToolAppAction.java:41` reads it from the **subcommand namespace** → always `null` → the update check runs unconditionally | [src: docs/Mindcode集成.md:73-77] |
| the update check uses `dev.dirs` and on Windows runs `powershell -EncodedCommand` with inline C#; the Java side only reads stdout and **never drains stderr**, so a full pipe locks both sides | [src: docs/Mindcode集成.md:74-77] |
| so a version probe **cannot detect** the deadlock; only a real compile can | `doctor`'s `smoke-compile` exists for exactly this [src: tools/mindcode.py:664-681] |

What the wrapper does about it: 3.21 stays in the candidate table (because of the search order), but once it is picked it is written into `warnings`/`notes` [src: tools/mindcode.py:362-367]; on a compile timeout it adds a "use 3.19.3 instead" hint [src: tools/mindcode.py:532-534].

### 6. The error format and the three diagnostic columns

The compiler writes diagnostics to **stderr**, one per line:

```text
<绝对路径>:<行>:<列> <类别>: <消息>
```

`_DIAG_RE` captures the first three fields `file/line/col` [src: tools/mindcode.py:131] and hands the rest to `_CATEGORY_RE` to split into `kind/message` [src: tools/mindcode.py:132-135]. Key point: **only parse/syntax/compile/internal/runtime error and warning/note/info carry an explicit category prefix**; semantic errors have no prefix, in which case `kind` falls back to `error` and `message` takes the rest of the line [src: tools/mindcode.py:430].

| What stderr looks like | Parsed result | Basis |
|---|---|---|
| `bad.mnd:1:6 Parse error: missing semicolon after '1'` | kind=`Parse error`, line=1, col=6 | measured |
| the `bad.mnd:1:1 error` shape: `Function 'sensor': wrong number of arguments (expected 2, found 3).` | kind=`error` (no category prefix) | measured |
| `Automatically added missing 'printflush(message1);' call …` | **does not enter diagnostics**, it goes into `notes` (any line not matching `_DIAG_RE` counts as compiler chatter) | [src: tools/mindcode.py:424-427] |
| `java.lang.UnsupportedClassVersionError …` | classified as `incompatible`, goes into `notes` and that java candidate is skipped | [src: tools/mindcode.py:279-284] |

Two more easily missed: diagnostic text is emitted in the **ANSI code page** (cp936 on this machine), so each stream goes through a three-stage decode of "UTF-8 → locale code page → replace" [src: tools/mindcode.py:188-202]; on the CLI diagnostics go to stderr and read `path:line:col: kind: message` [src: tools/mindcode.py:713-720].

### 7. The JSON return shape

`compile_source` / `compile_file` always return 8 keys [src: tools/mindcode.py:471-475]:

| Key | Meaning |
|---|---|
| `ok` | decided by "**code was produced** and **there is no error-level diagnostic**", **not** by the exit code [src: tools/mindcode.py:561-562] |
| `mlog` | the normalised mlog (LF, exactly one trailing newline); `null` on failure |
| `diagnostics[]` | the five fields `{file, line, col, kind, message}` [src: tools/mindcode.py:435-436] |
| `stats` | `ast_nodes` / `instructions` / `optimized_instructions` / `timings_ms{parsed,compiled,optimized}` / `raw` / `exit_code` / `timed_out` [src: tools/mindcode.py:394-396] |
| `tool` | `{name, version, jar, java}` [src: tools/mindcode.py:493-494] |
| `elapsed_ms` | wall clock |
| `source_sha256` | the hash of the text **after the BOM is stripped** |
| `notes` | the wrapper's own remarks: skipped java candidates, compiler chatter, the `-o -` fallback rerun |

The MCP layer wraps that in a `mlog-eval/v1` envelope: `schema / ok / stage / failure_type / message / level / levels / diagnostics / artifacts / next_steps / trace / elapsed_ms` [src: tools/mlog_eval.py:122-139] (`mlog_validate` also adds a `program` field naming which program it is [src: tools/mlog_mcp.py:617]), and the three `level` settings `summary|diagnostics|full` control the size [src: tools/mlog_eval.py:62, 85-103]; at `summary` level the compiled output is given as an `mlog_ref` pointer instead of the whole body [src: tools/mlog_mcp.py:516-528].

### 8. The boundary between `unsupported_environment` and `compilation_error`

**By contract**: the source does not compile → `compilation_error` (next step: fix the source); this machine has no runnable compiler → `unsupported_environment` (next step: fix the environment, **do not retry**) [src: tools/mlog_mcp.py:549-555].

**In the implementation the test is "`tool.jar` and `tool.java` are both non-empty"** [src: tools/mlog_mcp.py:554-555, 587-588], while `mindcode.py` **fills the candidate path strings into `tool` whether it succeeds or fails** [src: tools/mindcode.py:493-494, 338-341]. Consequences (two measured):

| Scenario | Actual failure_type | message |
|---|---|---|
| `MINDCODE_JAR` points at a jar that does not exist | `compilation_error` | `mindcode unavailable: no mindcode jar found: …` |
| `path` points at an `.mnd` that does not exist | `unsupported_environment` | `FileNotFoundError: …` |

In other words: **an environment failure only lands in `unsupported_environment` through the early-exit branches (file unreadable / not UTF-8, so `tool`'s jar and java are `null`)** [src: tools/mindcode.py:601-616]; the path where the compiler "is there but will not run" is labelled `compilation_error`.

In the first measurement the envelope **contradicts itself**: `failure_type=compilation_error` (meaning "your source is wrong"), while that same envelope's `diagnostics[0]` is `{"kind":"environment","line":0,"col":0,"message":"mindcode unavailable: …"}` (meaning "this machine has no compiler") — kind and `line:0,col:0` are constructed directly by `mindcode.py` when `res["ok"]` is false [src: tools/mindcode.py:497-502]. So **the envelope's `failure_type` must not be taken on its own**. The very same failure is judged "environment" on the CLI side — exit code 2 [src: tools/mindcode.py:704-710]; the two entry points attribute the same failure differently, which is the direct reason this article asks you to "look at kind first".

The right way to read it: **look at `diagnostics[0].kind` first, then at `failure_type`**. The four kinds `environment` / `timeout` / `io` / `encoding` are environment and input problems, not a source error [src: tools/mindcode.py:144] — the CLI's `_exit_code()` returns **2** for exactly this set (1 for a source error) [src: tools/mindcode.py:704-710].

## Numbers

| Quantity | Value | Source |
|---|---|---|
| integration baseline version | 3.19.3 | measured with `mindcode.py version` |
| minimum Java | 22 (class file 66.0) | [src: tools/mindcode.py:58-64] |
| the repo's bundled JRE 21 | 21.0.5+11 (class file 65.0, incompatible, skipped) | [src: tools/mindcode.py:119, 279-284] |
| the JRE actually used | 25.0.5+8 | [src: tools/mindcode.py:120] |
| `--version` probe timeout | 30 s | [src: tools/mindcode.py:122] |
| default compile timeout | 120 s | [src: tools/mindcode.py:582-583] |
| CLI exit code | 0 success / 1 the source did not compile / 2 it would not run (environment, timeout, I/O) | [src: tools/mindcode.py:15-18, 704-710] |
| failure vocabulary | 7 values (compilation_error … simulation_real_difference) | [src: tools/mlog_eval.py:51-59] |
| simple program measured | 6 AST → 3 instructions (2 after optimisation), compiled 195 ms | measured with `print(1);` |
| summing loop measured | 23 AST → 10 instructions → **2** (constant folding) | measured with `for i in 1..5` |
| the same source with `-O 0` | 11 instructions, 11 lines of mlog | measured |

## Source anchors

| Location | Content |
|---|---|
| `tools/mindcode.py:113-120` | candidate table constants: `PREFERRED_JAR` / `FALLBACK_JAR` / `USER_JAR` / `JAVA_21` / `JAVA_25` |
| `tools/mindcode.py:157-177` | `_jar_candidates()` / `_java_candidates()`: an environment variable, once set, is the only candidate |
| `tools/mindcode.py:267-290` | `_probe_version()`: really runs `--version`, recognises `UnsupportedClassVersionError` before the version number |
| `tools/mindcode.py:308-381` | `_resolve()`: the cartesian product of candidates × probing; the first usable one wins, the rest go into `notes` |
| `tools/mindcode.py:487-569` | `_compile()`: temp directory, BOM-free write, the `cm` command line, timeout / the `-o -` fallback |
| `tools/mindcode.py:416-441` | `_parse_diagnostics()` / `_error_diags()` |
| `tools/mindcode.py:596-621` | `compile_file()`: `utf-8-sig` decoding (which also strips the BOM) + early exit on io/encoding |
| `tools/mindcode.py:646-698` | `doctor()`: candidate table + compatibility + **a real compile smoke test** |
| `tools/mlog_mcp.py:531-564` | `mindcode_compile`: result → `mlog-eval/v1` envelope |
| `tools/mlog_mcp.py:567-592` | `_compile_mind()`: the compile pre-step of `mlog_validate(mind=…)` |
| `tools/mlog_eval.py:51-80` | the failure vocabulary and the `NEXT_STEPS` mapping |

## Measured facts and counter-examples

- ✅【E】`sum = 0; for i in 1..5 do sum += i; end; print("total=", sum); printflush(message1);` → `23 AST nodes, 10 unoptimized, 2 optimized`; the output is only two lines: `print "total=15"` + `printflush message1`.
- ✅【E】the same source with `-O 0` (`optimize=False`) → 11 instructions, 11 lines of mlog, the loop kept as written, ending with a `print "Compiled by Mindcode 3.19.3 …"` signature line.
- ✅【E】3.21.0: `locate()` returns `ok=True, version=3.21.0`, `compile_source(timeout=8)` is killed at 8 s, the diagnostic has `kind=timeout` and its `message` carries "use the 3.19.3 jar instead".
- ✅【E】BOM: feeding a `.mnd` **with a UTF-8 BOM straight to the jar** → rc=1 and stderr line one reads `<path>:1:1 Parse error: extraneous input '?' …`; the same file through `compile_file()` → `ok=True` (the BOM is stripped by `utf-8-sig` at decode time [src: tools/mindcode.py:609]).
- Counter-example (a boundary that does not hold): **"a BOM makes compilation fail" does not hold for the wrapper** — both `_strip_bom()` and a BOM-free write are done [src: tools/mindcode.py:461, 512]; that pitfall only bites people who bypass the wrapper and call the jar directly.
- Counter-example: **"variables from the Mindcode source still exist after compilation" does not hold**. The default `-O` folds the whole loop away, so `sum` does not exist at runtime at all; hence `mlog_validate(mind=…, expect=[{var:"sum", op:"==", value:15}])` yields `failure_type=assertion_failed` with `levels` = `execution=true / static=true / simulation=false` (measured this time). To assert on Mindcode, assert **observable side effects** (text buffer, memory cells, block state), never source variable names.
- Counter-example: **"exit code 1 means a syntax error" does not hold** — `ok` does not look at the exit code [src: tools/mindcode.py:561-562]; `cm --help` itself returns 1.
- 【Not done】No runtime source map (mlog line → `.mnd` line) has been built; only the compile-time `line/col` exists. The `pm` reverse path is not wired in. This article covers **the front end only**, not the Mindcode language syntax itself [src: the integration doc (docs/Mindcode集成.md:137-142)].

## Common misconceptions

1. **"If `--version` runs, the jar is usable."** — wrong. 3.21.0's `--version` and `cm --help` both return instantly, yet `cm` hangs forever. The test is `doctor`'s `smoke-compile`, which really compiles a small program [src: tools/mindcode.py:664-681].
2. **"A java on PATH means it compiles."** — wrong. PATH holds Java 8, Mindcode needs 22+, and the candidate table **deliberately leaves PATH out**; `doctor` merely writes the PATH java into `notes` to remind you it was ignored [src: tools/mindcode.py:117-120, 691-693].
3. **"Having a JRE means it compiles."** — wrong. The bundled JRE 21 exists but cannot run a class-file-66.0 jar, so you must **probe** rather than `stat()`, or you will mistake "a JRE exists" for "it can compile" [src: tools/mindcode.py:58-66].
4. **"`compilation_error` always means my source is wrong."** — no; environment failures are labelled that way in the current implementation too (see §8), so read it together with `diagnostics[0].kind` [src: tools/mlog_mcp.py:554-555].

## Related

- MLOG.EXEC.001 Execution model (the tick budget the compiled output consumes and the 1000-instruction cap)
- MLOG.PERF.001 Performance and limits (hard caps such as the 400-character text buffer; the compiler's generated error checks follow the same)
- the integration doc (`docs/Mindcode集成.md`) — the long article on the same theme: interfaces, four measured traps, version arbitration
- Data table: `06-mlog/instructions.json#meta` (which 73 instructions the compiled output lands on)
