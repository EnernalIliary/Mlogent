# 98 · 游戏内 AI 生成 mlog 质量不高的取证分析

- 分析对象：`out/jobs/` 全部 34 个作业 JSON（最新 15 个逐条精读），`tools/mlogprovider.py`（提示词/样板/token 预算），`tools/mlogcheck.py`（`analyse()`），`tools/jobqueue.py`（`gate()`/`_record_attempt()`），`tools/logicd.py`（入口）。
- 方法：①统计作业状态与 findings；②把 `code` 原文按行号贴出逐条判错；③对 `analyse()` 做定向探针（用已知正确/已知错误的语句对拍）；④用 git 历史锁定时点（每个作业当时跑的是哪一版 prompt）。
- 取证脚本（可重跑，全部只读）：`out/_q1_jobs.py`、`out/_q1b_findings.py`、`out/_q2_defects.py`、`out/_q2_dump.py`、`out/_q3_promptver.py`、`out/_q3b_oldrules.py`、`out/_q3c_fingerprint.py`、`out/_q3d_examples.py`、`out/_q4_check.py`、`out/_q4b_probe.py`。
- **本次分析未修改任何源文件**。

---

## 1. 最近 15 个作业的失败与告警分布

### 1.1 状态与重试（`out/jobs/*.json`，按 `created` 倒序）

| # | 作业 id | 时间(10-31) | state | attempts | findings | 行数 | 玩家请求(desc) |
|---|---------|------|-------|----------|----------|------|----------------|
| 1 | d311496d3b19199f | 23:07 | done | 1 | 0 | 3 | 攻击最近的友方玩家 |
| 2 | b19800cc80cbc0e2 | 23:00 | done | 1 | 0 | 14 | 攻击玩家 |
| 3 | 607c8edb78ef197c | 22:50 | rejected | 3 | 1 (ERR) | – | 把 n 从 1 改成 2 |
| 4 | 317f5bac7e2d84ab | 22:50 | rejected | 3 | 1 (ERR) | – | x |
| 5 | b15ae137c36691ff | 22:50 | rejected | 3 | 1 (ERR) | – | 把 n 从 1 改成 2 |
| 6 | 43fe34c6557e3eeb | 21:28 | done | **2** | 0 | 16 | 控制炮台攻击玩家 |
| 7 | 6c6628141fe5e008 | 20:52 | done | 1 | **10 (全 WARN)** | 14 | 控制炮台攻击玩家 |
| 8 | 0684f7db87fdac4a | 20:42 | done | 1 | 2 (WARN) | 14 | 控制炮台攻击玩家 |
| 9 | ac838d21a8a84327 | 20:36 | done | 1 | 0 | 9 | 控制所有炮台攻击最近的玩家 |
| 10 | 0e0958e928b543fa | 20:28 | done | 1 | 0 | 5 | 打印最近玩家的名称 |
| 11 | a4bf4f48f1bfdb1e | 19:16 | done | 1 | 0 | 2 | 打印你好世界 |
| 12 | b427bf122b210915-2 | 18:19 | done | 1 | 0 | 5 | （retry_of=b427bf122b210915） |
| 13 | b427bf122b210915 | 18:17 | done | 1 | 0 | 6 | 控制炮台攻击玩家 |
| 14 | 5288b2215a114c36 | 18:12 | done | 1 | 1 (WARN) | 3 | 命令炮台攻击玩家 |
| 15 | ef8ff52c4b10a16a | 18:06 | done | **2** | 1 (WARN) | 6 | 打印最近的玩家名称 |

**结论表格（一次过 / 重试）：**

| 类别 | 数量 | 作业 |
|------|------|------|
| 一次过（attempts=1 且 done） | **10 / 15** | d311, b19800, 6c66, 0684, ac83, 0e09, a4bf, b427, b427-2, 5288 |
| 重试 2 次后 done | **2 / 15** | 43fe34、ef8ff5 |
| 重试 3 次仍失败（rejected） | **3 / 15** | 607c、317f、b15a |
| 全 34 个作业 | done 18 / rejected 16 | —— |

### 1.2 findings 的 rule id 与次数

| 范围 | rid | 次数 | 严重级 |
|------|-----|------|--------|
| 最新 15 | `link-name-unbindable` | 14 | WARN ×14 |
| 最新 15 | `provider-error` | 3 | ERR ×3 |
| 全部 34 | `link-name-unbindable` | 16 | WARN |
| 全部 34 | `provider-error` | 14 | ERR |
| 全部 34 | `template-needs-link` | 2 | ERR |
| 全部 34 | `link-name-not-bound` | 2 | ERR |

- **没有任何作业的 findings 里出现 `unreachable-statement` / `jump-target-out-of-range`**：这两类规则是 10-31 21:46 之后才进 `analyse()` 的（`git log -S unreachable-statement` → `866589a` v0.13.2，22:05）；用今天的 `analyse()` 重跑，43fe34、6c66、0684 立刻各多出 1 条 `unreachable-statement`（见 1.4）。
- 3 个 rejected 的 `provider-error` 原文：「no template matched this intent -- say what the processor should do: … | 当前是模板档，只能套固定样板；要自由描述，请在 设置 -> Mlog辅助 -> 大模型 里填地址/密钥/模型，再点「启用模型档」」——当时是**模板档**，模型根本没被调用；另两个历史 rejected（f5d3f25c7a4868ae、4d2c0d125679a67b）是 `model endpoint unreachable: HTTP Error 404: Not Found`。

### 1.3 attempt_log 与失败 kind：**完全没有数据**

- `python -X utf8 out/_q_schema.py` 统计 34 个作业的顶层键：`attempt_log`、`diag`、`report` **出现 0 次**；只有 `attempts` 一个整数。
- 原因在源码里写得明白——`tools/jobqueue.py:600-605`：
  ```
  def _record_attempt(self, jid, diag, kind, err, started):
      """Keep what each ask of the model produced and how it ended (v0.15.0).
      The job used to carry the verdict only, so a refusal could not be explained
      afterwards: no model name, no token counts, no finish_reason, no duration.
  ```
  这套 `attempt_log`（含 `finish_reason`、`prompt_tokens`、`completion_tokens`、`kind`）是 **v0.15.0（11-01 03:51）** 才加的，比全部 34 个作业（最晚 10-31 23:08）都晚 → 用户抱怨的那批作业**事后无法判断是截断、超时还是模型瞎写**，这也是「质量不高」一直说不清的直接原因之一。

### 1.4 用今天的 `analyse()` 重跑（`out/_q4_check.py`）

| 作业 | 存量 findings | 今天重跑 | 新增 |
|------|---------------|----------|------|
| 43fe34c6557e3eeb | 0 | 1 | WARN L11 `unreachable-statement`：「no jump reaches it … a jump target is usually off by one」 |
| 6c6628141fe5e008 | 10 | 11 | WARN L9 `unreachable-statement` |
| 0684f7db87fdac4a | 2 | 3 | WARN L9 `unreachable-statement` |
| 43fe34 / c78bd0fc504aa4e5 / c2e67ee9e3b40347 | 0 | 1 | 三个作业有「存量 0 findings 但实际不可达」 |

---

## 2. 模型实际写了什么错（三个代表作业原文）

### 2.1 零 findings、但**整段答非所问**：`d311496d3b19199f`

```
desc: 攻击最近的友方玩家         links: [fuse1]      state=done  attempts=1  findings=0
explanation: (空)   assumptions: []
 1| set n 0
 2| op add n n 1
 3| end
```

这三行**逐字符等于 prompt 里 free tier 的示例字面量**（`tools/mlogprovider.py:237`：`{"code": "set n 0\nop add n n 1\nend", …}`）——`repr` 也是 `'set n 0\nop add n n 1\nend'`。也就是说：模型对这个它拿不准的需求，直接回抄了提示词里的骨架代码；而 gate 只看语法，`set/op/end` 无 ERR → **判 done 交给玩家**。这是最坏的一类失败：用户看到「成功」，拿到的是 hello-world。

补充事实：该作业 `mode=new`、`snapshot.mod='0.14.1'`、处理器只链了 `fuse1`，快照里唯一单位是 `emanate`（己方 `sharded` 队）——「攻击最近的**友方**玩家」本身是做不到的需求。正确行为应该是把「无法攻击队友/没有炮台链接」写进 `assumptions`/`needs_links`，但 `assumptions=[]`、`explanation=''`（全空），管线也没有「代码与需求无关 / explanation 为空」这类检查，于是空解释 + hello-world 一路通过。

### 2.2 findings 最多、但**10 条 WARN 全是同一条**、而且代码确实错：`6c6628141fe5e008`

```
desc: 控制炮台攻击玩家        links: [salvo1..salvo4]     state=done attempts=1  findings=10
 1| radar target salvo1 player any distance      ← 参数顺序全错、且不足 7 个
 2| jump 10 equal target null                    ← 数字行号
 3| sensor px target x                           ← 属性写成 x，正确是 @x
 4| sensor py target y
 5| control salvo1 shoot px py 1                 ← 子命令与方块位置互换
 6| control salvo2 shoot px py 1
 7| control salvo3 shoot px py 1
 8| control salvo4 shoot px py 1
 9| jump 1 always                                ← 1 基意图、0 基语义 → 不回 L1 而回 L2
10| control salvo1 shoot 0 0 0
11| control salvo2 shoot 0 0 0
12| control salvo3 shoot 0 0 0
13| control salvo4 shoot 0 0 0
14| jump 1 always
```
- 正确 v160 是 `radar <filter> <filter> <filter> <sort> <block> <order> <result>`，结果变量**在最后**；模型把 `target` 放在首位（把它当 sensor 那样「结果在前」），于是 L3/L4 的 `target` 成了从未赋值的变量。
- 10 条 finding 全是 `link-name-unbindable`，且消息说的是「`shoot` is the link this `control` acts on…」——检查器把 L5 的 `shoot` 当成方块名，说明它知道位置错，但**只说 WARN，不拒**；`state` 仍是 `done`。
- 模型自己的 reasoning（`out/jobs/6c6628141fe5e008.json` 的 `reasoning` 字段）把话说尽了：「The rules say "jump <label|line> <condition> <a> <b>; a jump target must exist." It doesn't explicitly mention label syntax but likely allowed. … to be safe, use line numbers.」——**它引用的这条规则在 v0.13.2 已被删除**（`git show 866589a^:tools/mlogprovider.py` 第 145 行），见 §3.4。

### 2.3 重试过的：`43fe34c6557e3eeb`（attempts=2，存量 findings=0）

```
desc: 控制炮台攻击玩家      links: [salvo1..salvo4]    state=done  attempts=2
 1| control enabled salvo1 1
 …（2-4 同）
 5| radar player any any distance salvo1 1 target
 6| jump 12 strictEqual target null        ← 想跳到 L13「停止射击」，0 基却落在 L13 中间，L12 永不执行
 7| control shootp salvo1 target 1
 …（8-10 同）
11| jump 5 always 0 0                     ← 想回 L5 重新扫描，0 基回的是 L6 那条 jump
12| control shootp salvo1 null 0          ← 永远执行不到
13| control shootp salvo2 null 0
…
16| jump 5 always 0 0
```
- 两处 off-by-one：`jump 12` 跳过「给 salvo1 停止」的那一行；`jump 5` 跳过 radar 行 → **radar 只跑一次，之后永远拿着第一次的目标坐标**。
- 这个作业正是 v0.13.2 提交说明里点名的取证对象：「`jump 12` 少算一行跳进「停止射击」块中间（L11 永不执行），而 mlogcheck 当时回 no issues found」。
- 用今天的 `analyse()` 重跑 → `WARN L11 unreachable-statement`（`out/_q4_check.py` 输出），证明「存量 findings=0」是检查器漏检，不是代码没问题。

---

## 3. 提示词侧的系统性问题（`tools/mlogprovider.py`）

### 3.1 从不给指令签名表（最致命）

整个 prompt 里关于指令语法的全部内容只有三句（`tools/mlogprovider.py:208-212`）：
```
- print/printflush: print writes into the buffer, printflush sends it.
- sensor <result> <block> <property> reads a property of a linked block.
- control/radar/ucontrol need the documented argument count for v160.
```
`radar` 的 7 个参数位、`control` 的子命令/方块/坐标/开关顺序、`ucontrol`/`ulocate` 的槽位**一处都没有**；`world facts` 段只有一行 `instruction set: v160 (ipt=2)`（:178），`ipt` 是个数字，模型只能猜。实测为 `desc='控制炮台攻击玩家'` 生成的整份 prompt 只有 **2675 字符 ≈ 891 token**（`out/_q3d_examples.py` 输出 `[prompt chars=2675 approx tokens=891]`）——预算极宽裕，却几乎没放任何规范知识。
后果直接对应 §2.2：结果变量放首位、`control` 子命令与方块互换、`sensor px target x`（应为 `@x`）。

### 3.2 few-shot 样板：抱怨发生时是 **0 条**，今天加的 8 条里还有 1 条是错语法

- git 时间线（`out/_q3_promptver.py`）：`a77f591`(v0.14.1, 10-31 22:46) → `examples=0`；`56775df` → 0；`f97e0c3` → 0；**`05a7c09`(v0.15.2, 11-01 05:09) 才 `examples=8`**。全部 34 个作业最晚 10-31 23:08 → **它们看到的 prompt 一条样板都没有**，只有 `:237` 那个三行骨架可抄（§2.1 的 d311 就是抄它）。
- 今天的 8 条样板（`:256-343`），turret 那条（`:293-299`）是：
  ```
  loop:
  radar enemy any any distance turret1 1 target
  jump loop equal target null
  control shoot turret1 target 0      ← 「得到单位目标就开火」的正确写法是 shootp；这行少一个操作数
  jump loop always
  ```
  实测 `analyse()` 对它返回 **0 findings**（`out/_q3d_examples.py`：`## turret … findings=0`），而 `control shoot <block> <x> <y> <shoot>` 需要 4 个操作数，这里只给了 3 个（`target` 当 x、`0` 当 y，`shoot` 缺失）。**样板是「gate 会接受」的，但 gate 不查少参数** → 「照抄一个样板」会稳定复制一个静默失效的开火语句。
- 样板选择逻辑 `_examples_for()`（`:346-364`）永远至少塞 2 条（打分 0 的也补），所以和需求无关的 counter 样板经常混进来；实测 `desc='攻击最近的友方玩家'` 选中 `turret + threshold counter`。

### 3.3 标签要求写得很好，但**没有自检要求**

`:202-207` 明确禁数字行号、要求标签独占一行；但全 prompt 没有任何「输出前逐条核对 jump 目标是否是你定义过的标签」这类自检步骤（只有 `:212` 一句「The whole program must pass the analyzer」，而 analyzer 不管这个）。三个炮台作业（6c66/0684/43fe34）全部无视了标签要求 —— 692 个字符的规则条款，被后续 8 条样板里 6 条 `jump loop always` 的标签写法部分抵消，但数字跳转依然出现，因为模型对「标签在游戏里合法」没有把握（§2.2 的 reasoning 原话就是这么写的）。

### 3.4 提示词更新**没有进到运行中的侧车**

- `tools/logicd.py:81`：`import mlogprovider  # noqa: E402  (prompt / reply parsing / model call; offline at import)`，全仓无 `importlib.reload`；侧车是长驻进程 → **改 prompt 文件不重启侧车等于没改**。
- 证据：`b19800cc80cbc0e2`（23:00，`reasoning` 字段原文）引用了 22:05 已删除的旧规则：「The rule says `jump <label|line> <condition> <a> <b>`; so condition always may still need a,b?」；`6c6628141fe5e008`（20:52）同样引用它。而 `866589a`（v0.13.2, 22:05）已把该行换成标签规则。→ 23:00 那次请求拿到的 prompt 仍是 **pre-0.13.2** 的（`git show 866589a^:tools/mlogprovider.py` 第 145 行原句）。语义上这条旧规则**明确允许「label|line」并只要求「目标存在」**，这正是「数行号」的许可证。

### 3.5 token 预算：机制存在但事后无法验证

- `DEFAULT_MAX_TOKENS = 4096`（`:496`）、`TOKENS_CEILING = 16000`（`:497`）、`ERR_TRUNCATED`（`:514`）+ `TRUNC_TOTAL = 4`（`:527`，截断时预算翻四倍重试）——**都是 v0.15.0 的加料**；34 个作业 0 个有 `finish_reason`（§1.3），所以「是否被 4096 截断」无从判断。
- 可观测的旁证：15 个作业里 `reasoning` 有 14 个正好等于 **12000 字符**，即 `REASONING_MAX = 12000`（`:501`、`:724` `res["reasoning"] = text[:REASONING_MAX]`）——那是**我们自己存盘时的截断**，不是模型截断；说明模型一次要吐的思考量本来就贴近 4k 输出上限，而 code+explanation 与 reasoning 共享这 4096。

---

## 4. 检查器漏检（`tools/mlogcheck.py` 的 `analyse()`）

`ARITY` 表有 53 条（`_load_arity()` `:337-358`），但**只用于「多余参数」方向**：`:199-201` 与 `:726-727` 都是 `if limit is not None and len(p) > limit + 1` 才截断，**少参数方向没有任何规则**。定向探针（`out/_q4b_probe.py`，links 给了 salvo1/turret1/message1）：

| 片段 | 实际对错 | analyse() 判 |
|------|----------|--------------|
| `control shoot turret1 target 0`（**prompt 自己的样板行**） | 错：少 `shoot` 操作数 | **0 findings** |
| `radar target salvo1 player any distance`（6c66 L1） | 错：结果放首位、只有 5 个参数 | **0 findings** |
| `control shoot turret1 1` | 错：少 2 个参数 | **0 findings** |
| `op add n n 1`（读未初始化 n） | 错：自读未初始化 | **0 findings** |
| `radar enemy any any distance salvo1 1 target 5` | 错（多一个参数） | **0 findings** |
| `control salvo1 shoot px py 1`（6c66 L5） | 错：子命令/方块互换 | WARN `link-name-unbindable` + `surplus-parameter-is-not-an-error` |
| `sensor px target @x`（target 未绑定） | 错：未初始化 | WARN `link-name-unbindable` |
| `jump 9 always`（3 行程序） | 错：越界 | **ERR** `jump-target-out-of-range` ✔ |
| `jump 3` 落进不可达 | 错 | WARN `unreachable-statement` ✔（v0.13.2 起） |
| `ucontrol move 10 20 0 0 0`（无 ubind） | 错 | **ERR** `ubind-missing` ✔ |

漏检分类（对 18 个有 code 的作业重跑 + 探针）：
- **34 个作业里 18 个有 code，其中 13 个以 `findings=0` 落地**（`01c09540/0d8a8a3a/0e0958e9/43fe34c6/920e354c/a4bf4f48/ac838d21/b19800cc/b427bf12×2/c2e67ee9/c78bd0fc/d311496d`）。
- 这 13 个里至少 2 个可证明是语义错：`b19800`（`jump 9` 落点错，无目标分支仍用旧坐标开火）、`d311`（回抄骨架，与需求无关）。
- 另有 3 个（43fe34、c78bd0fc504aa4e5、c2e67ee9e3b40347）在 v0.13.2 之前「0 findings 通过」，今天重跑各命中 1 条 `unreachable-statement` —— 正是用户抱怨的那一类。即 13 个「绿灯」里 5 个实际有问题（38%）。
- `gate()`（`tools/jobqueue.py:304-325`）只把 `FATAL_RIDS` 提升为 ERR 并拒绝（`logicd.analyse` 的 `errors` 也仅数 ERR），**WARN 一律放行** → 6c66 那 10 条 WARN 的坏代码照样 `done`。
- 语义类错（参数顺序、参数槽含义、单位/方块类型不匹配、`radar` 的 filter 枚举、`sensor` 属性拼写）**没有规则**；`mlogval.py`/`mlogir.py`/`mlogsim.py`（真 JVM 执行器）都在仓库里，但 gate 只调 `analyse()` 一个函数，从未用它们做二次判定。

---

## 5. 结论：按影响力排序的根因

### R1. 提示词从不给出 v160 指令签名，模型只能凭记忆猜参数位
- 现象：`radar` 结果变量放首位、`control` 子命令与方块互换、`sensor` 属性漏 `@`、少参数被游戏静默补 null（6c66 L1/L3/L5，b19800 靠猜「I need be absolutely sure」写下 radar）。
- 证据：`tools/mlogprovider.py:210`「control/radar/ucontrol need the documented argument count for v160.」之后再无任何参数说明；`:178` 只有 `instruction set: v160 (ipt=2)`；整份 prompt ≈891 token（`out/_q3d_examples.py`）。
- 建议修法：把 `radar/control/sensor/ucontrol/ulocate/op/print` 的**权威签名表**（每个参数槽的名字 + 合法枚举：`enemy/ally/player/any`、`distance/health/…`、`shoot/shootp/enabled/configure`）从 v160 解包数据生成并注入 `world facts` 段，不要手写。

### R2. 抱怨发生的那批作业是**零样板**跑的；今天补的样板里还带着一条错语法
- 现象：d311 直接把 prompt 里的三行骨架当答案交回来；turret 类需求没有可抄的正确范式。
- 证据：`examples=0` 覆盖 10-31 22:46 及之前所有版本（`out/_q3_promptver.py`），EXAMPLES 首次出现于 11-01 05:09 的 `05a7c09`；全部作业 ≤10-31 23:08。骨架字面量在 `:237`；样板错行在 `:298`（`control shoot turret1 target 0`，实测 `analyse()` 0 findings）。
- 建议修法：按任务族（炮台/巡逻/打印/开关/计数/单位控制）补足样板，样板必须用**真实链接名占位 + 正确 arity**，并加一条测试：样板里每条 `control/radar/sensor` 的参数个数必须等于 ARITY；同时把 free-tier 骨架换成「带 radar 的最小真实程序」，并对「输出 == 骨架」直接判失败。

### R3. 检查器只查「多余参数/孤立链接」，不查「少参数/参数顺序/参数含义」，且 WARN 不拦
- 现象：6c66 带 10 条 WARN 仍 `done`；`control shoot` 少一个操作数、`radar` 只有 5 个参数、`op add n n 1` 自读未初始化，全部 0 findings。
- 证据：`tools/mlogcheck.py:199-201`、`:726-727` 只在 `len(p) > limit + 1` 时截断，无 under-arity 规则；`ARITY` 53 条未被双向使用（`out/_q4b_probe.py` 表）；`tools/jobqueue.py:304-325` 的 `gate()` 只提升 `FATAL_RIDS`，WARN 放行。
- 建议修法：新增 under-arity 规则 + 每指令参数槽白名单（`radar` 的 3 个 filter 位只接受枚举、第 4 位只接受 `distance/health/…`、`control` 第 1 位只接受子命令词），把「语义类 WARN」并入 `FATAL_RIDS` 或至少强制一次重试。

### R4. jump 是 0 基语句索引，prompt 从没说过；模型按 1 基行号写 → 系统性差一行
- 现象：43fe34 `jump 12`/`jump 5` 各差一行（前者让 L12 永不执行，后者让 radar 只跑一次）；b19800 `jump 9` 让「无目标」分支继续用旧坐标开火。
- 证据：`tools/mlogcheck.py:1939-1961`（`reachable_set` 按 0 基索引、`_BACKJUMP` 用 `0 <= target < j` 判定回边）→ jump 数字是索引；`b19800` 的 `jump 3 always`（回 L4）与 `jump 9`（应回 L13 收尾）并存即可看出模型在 1 基/0 基之间来回摇摆；prompt 侧 `:202-207` 只禁「数行号」，没讲 0 基语义。
- 建议修法：prompt 里把这条写成硬事实（「jump 的数字是 0 基语句索引；不要用数字，只用标签」），并把全部样板与 free-tier 骨架标签化；gate 里对数字 jump 直接 WARN→触发一次重试。

### R5. 诊断闭环缺失：`finish_reason`/token 不落盘 + 提示词改动不重启侧车（版本漂移）
- 现象：34 个作业 0 个有 `attempt_log`/`diag`/`finish_reason`，无法区分「被 4096 截断」还是「模型瞎写」；23:00 的作业还在用 22:05 已删除的旧 prompt（旧规则明文允许写行号）。
- 证据：`tools/jobqueue.py:600-605` 的注释自认旧作业「no model name, no token counts, no finish_reason, no duration」，`attempt_log` 自 v0.15.0 才有；`tools/logicd.py:81` 只在进程启动 `import mlogprovider`、无 reload；`b19800`/`6c66` 的 `reasoning` 引用了 pre-`866589a` 的第 145 行原文。
- 建议修法：①每次改 prompt/规则后强制重启侧车，或加一个 `/reloadprovider` 与管理面板按钮；②把 `attempt_log`（`finish_reason`、`prompt_tokens`/`completion_tokens`、prompt 版本指纹、`max_tokens`）无条件写进每个作业 JSON（成功也要写）；③作业 JSON 里记录 `prompt_sha` + `EXAMPLES` 版本号，便于事后归因。

---

## 附：一句话总结

这批作业里模型犯的错高度集中在**「猜指令签名」**（radar/control 参数位）和**「数行号」**（0 基/1 基）两件事上；而这两件事都是**提示词本可以提供却没提供的信息**，同时**检查器对这两类错恰好都判 0 findings**——所以坏代码一路 `done` 进了游戏，用户看到的「AI 生成质量不高」是「没给规范 + 没查语义」的乘积，而不是模型能力不行。
