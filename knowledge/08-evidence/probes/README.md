# 08-evidence/probes — 可复跑的断言探针（20 条）

把 `08-evidence/claims.jsonl` 中 conf=E 的前 20 条断言逐条做**执行级验证**：mlog 源码喂进**真实 v160.7 执行器**，
回读变量表 / 文本缓冲 / @counter，与断言期望比对，输出 PASS / FAIL / INCONCLUSIVE 与实测快照。
目的：机制断言从"文档说"升级为"跑出来"，任何读者一条命令复现。

## 运行

```powershell
cd knowledge\08-evidence\probes
python _run_all.py          # 全部 20 条，结果写 out/<id>.txt，末行给 fails 统计
python probe_L1-15.py       # 单条
```

依赖：Python 3.11+、JDK 21（`jre21`）、仓库 `out/_server160.jar`、`tools/mlogsim.py`；仓库根可用 `MLOG_REPO` 覆盖。
实现：**进程内**调用 `mlogsim.Server`+`run_mlog`（与 MCP `mlog_sim` 同一路径），**无 jar 反射、无 CLI 子进程**；
单 JVM 复用（~6–9 s 启动一次），20 条约 40 s 跑完。

判定口径：`PASS`=断言被复现；`FAIL`=断言被推翻（见"与 claims 冲突"）；`INCONCLUSIVE`=headless 场景缺少前置条件。

## 已知环境坑（必读）

仓库在 OneDrive 同步目录。`tools/mlogsim.py:361` 用 `tempfile.mkdtemp(dir=<repo>/out/_sim)` 建每次运行工作目录，
**该目录下 mkdtemp 会卡死**（实测 >120 s 无进展，栈停在 `tempfile.py:375 / genericpath.isdir`；同机 `%TEMP%`
与 workspace 下均 0.003 s）。`_harness.py:26-38` monkeypatch 到 `probes/out/_simwork` 绕过。
**直接跑 `mlogsim` CLI 同样会挂**（日志有 Server loaded→Shutting down 却不退出），不是探针问题。

## 结果（2026-11-08，v160.7，17 PASS / 1 FAIL / 2 INCONCLUSIVE）

| 探针 | 断言 | mlog 要点 | 实测回读 | 判定 |
|---|---|---|---|---|
| L1-01 | end 后 @counter 归 0，下一 tick 从头跑 | `print @tick`+`end`，ticks=3 | text=`23`，counter=2.0，ipt=2.0 | PASS |
| L1-02 | end 之后语句永不执行 | `print "X"`/`end`/`print "Y"` | text=`XXXX`，无 Y | PASS |
| L1-03 | `jump 0 always` 等价 end | jump 代替 end | text=`56` | PASS |
| L1-04 | @counter<0 归 0 从头跑 | `jump -1 always` | text=`AAAA` | PASS |
| L1-05 | 未赋值变量为 null，print 输出 null | `print x` 两次 | text=`nullnull` | PASS |
| L1-06 | 不 ubind 时 `sensor d @unit @dead`=1 | 无 ubind | d=`1` | PASS |
| L1-07 | `equal x null` 对未赋值 x 为真 | 分支打印 T/F | text=`TT` | PASS |
| L1-08 | `logn 0 2` 与 `1/0` 均 null | `op logn`/`op div` | text=`null|null`，vars 均 null | PASS |
| L1-09 | sin/cos 用度 | `op sin r 90`/`op cos s 180` | text=`1|-1`（弧度则 0.894/-0.598） | PASS |
| L1-10 | jump N 从 0 起算 | 行0 `jump 2 always` | text=`BB`（A 从未打印） | PASS |
| L1-11 | `op add @counter` 基址 i+1 | 行0 加 1 跳一行 | text=`BB`（跳过 A） | PASS |
| L1-12 | 首 tick 不执行指令 | ticks=1 | text=``（空） | PASS |
| L1-13 | print 只取 1 个参数 | `print "a" "b"` | text=`acac`，无 b，不报错 | PASS |
| L1-14 | print 的 \n 换行；缓冲 400 | 450 字符 + `"L1\nL2"` | newline=True，len(text)=**400** | PASS |
| L1-15 | format 用 {0}/{1} | 先 `print "{0}-{1}"` 再两次 format | text=`a-b`（**机制与 claims 描述不同**，见下） | PASS |
| L1-16 | read/write 经 @this 变量 | `write z cell1 0`+`read r` | vars.r=`7` | PASS |
| L1-18 | 记忆格越界读出 0 | cap+`read cell1 64/-1` | cap=**64**；0..63→`0`，64/-1→`null` | **FAIL（断言错）** |
| L1-19 | @x/@y/@range 以 tile 计 | `ubind @fortress`+sensor | headless 地图无 unit，ubind 失败 | INCONCLUSIVE |
| L1-20 | select 需 build≥150 | `select 1 0 0 0 0` | 无崩溃、counter 前进；前置不可观测 | INCONCLUSIVE |
| L1-21 | headless 下 draw 不报错 | clear/color/rect/drawflush | counter=2.0，无异常 | PASS |

每个 `out/<id>.txt` 含：claim 原文、模式（ticks/steps）、verdict、why、python/仓库路径、**可粘贴 mlog**、执行器 JSON 回读。

## 与 claims 冲突（重要，建议回改 claims.jsonl）

### 1) L1-18「记忆格越界读出 0」→ 实际是 **null（NaN）**
- 源码锚点：`Mindustry-Source/core/src/mindustry/world/blocks/logic/MemoryBlock.java:65-69`，注释原文
  `//Return null when out of bounds. (instead of 0)`，越界分支返回 `Double.NaN`；`write()` 越界则**静默丢弃**（同文件 :77-80）。
- 运行时实测：`sensor cap cell1 @memoryCapacity` → `64`；读 0/31/63 → `0`；读 64 与 -1 → `null`。
- 容量事实：`memory-cell`=64（`Blocks.java:6875`），`memory-bank`=512（`Blocks.java:6881`）；
  `MemoryBlock.java:12` 的类默认值是 32（被具体方块覆盖，勿引用 32 当成品容量）。
- 建议改法：claim 改为"越界读出 **null**；未写入的合法地址读出 **0**"，并把探针 out/L1-18.txt 作为证据。

### 2) L1-15「format 用 {0}/{1} 占位」→ 描述不完整，易误用
- 唯一实测可工作的形态：`print "{0}-{1}"` → `format "a"` → `format "b"` ⇒ `a-b`。
  即 **format 只吃 1 个值**，在**已存在于文本缓冲**的占位符里挑**编号最小**的一个替换（`LExecutor.java:1111-1139`），
  语句定义只有 1 个字段（`LStatements.java:344-356`）。
- 占位符只支持**单个数字 0–9**（源码判断 `charAt(i+1)` 是数字且 `charAt(i+2)=='}'`）；
  实测 `print "{10}"` + `format "x"` → 文本仍是 `{10}`，**不替换**。
- 建议改法：补一句"format 每次填一个值，最低编号占位符优先，正文需先 print"。

### 3) L1-19 / L1-20 仍是未验证（应保持 conf=U 或标注需场景）
headless 服务器地图没有可选单位，也没有 build≥150 的建造；两条断言只能靠带场景的 save（`mlog_sim --save`）验证。

## 文件

- `_harness.py` — 执行器封装（单 JVM 复用、mkdtemp 绕过、`probe()` 统一落盘、INCONCLUSIVE 支持）
- `probe_L1-0x.py` / `probe_L1-1x.py` — 每条：`CODE`(mlog)、`check(rec)`(判定)、`main()`；可单跑
- `_run_all.py` — 顺序跑 20 条并统计 fails
- `out/<id>.txt` — 实测快照；`out/_simwork/` — 模拟器临时工作目录
- `run-latest.log` — 最近一次全量运行终端输出（17 PASS / 1 FAIL / 2 INCONCLUSIVE）
