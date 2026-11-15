# -*- coding: utf-8 -*-
import sys, pathlib
sys.stdout.reconfigure(encoding='utf-8')
BT = chr(96)
p = pathlib.Path(r'<scratch-dir>\kb-stage\08-evidence\bench\README.md')
txt = p.read_text(encoding='utf-8')
add = r'''
---

## 10. hybrid 基线（kb.py 混合引擎 × 仓库 knowledge）

> **状态：待 DB READY 后填入**（lead 的「DB READY: <时间戳> <chunks>」信号到达后，
> 由 recon-a-mechanics 用同一套冻结 300 题跑 «--engine kb» 并在此填数；本节填完前，
> 全文引用 hybrid 数字的地方一律视为未完成）。

口径（与 §4 的 L1 严格可比）：

- **gold 仍用 «knowledge/» 目录**（不把 kb.py 额外收录的 «mindustry-blueprint/»、«docs/游戏速查/»、
  «tools/*.py» 算进 gold），否则 lexical 与 hybrid 的 coverage 不是同一个分母。
- 额外单列 **「命中落在 knowledge 之外」的题占比**：如果 hybrid 有很多分是靠
  «mindustry-blueprint/REFERENCE.md» 这类超大宽文档拿到的，那它不代表文章变好，只代表宽文档变多。
- 命令：«python tools/eval_kb.py --questions 08-evidence/bench/questions.jsonl --kb <repo>\knowledge --root <repo> --engine kb -k 6 --out <hybrid.json> --per-question <hybrid_pq.json>»
  （«--root» 必须显式给仓库根：在 kb-stage 下默认值会算错）。

填表模板（DB READY 后原地替换）：

| 引擎 | 语料 | coverage | hit@1 | hit@6 | mrr | strong@6 | knowledge 外命中 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| lexical BM25 | kb-stage 104 文件 / 1051 chunk | 100% | 45.3% | 78.7% | 0.582 | 92.2% | 0% |
| kb.py hybrid | 仓库 knowledge（DB READY 快照） | 待填 | 待填 | 待填 | 待填 | 待填 | 待填 |

**结论（lead 已批准、本节必带的一句）**：题库里 86.7% 的题本质是「查常量/查行号」，
hybrid 命中率高只证明**锚点搬对了**，不证明 AI 能推导；判断推导能力要看 §9 末的 46 题。

---

## 11. v2 草案：跨源推导题 24 道（«questions-derive.jsonl»，不进主指标）

**为什么单独一个文件**：300 题已冻结（«questions.jsonl» 一字不改，主指标只认它）。
v2 想解决的是 §9 暴露的结构性问题 —— 86.7% 的题只需查一行源码，考不出「组合两个真源做推导」。
这 24 道题是**样本草案**，用来先看清「推导型覆盖」长什么样，再决定是否扩成 v2 正式题库。

**规格**

| 项 | 值 |
| --- | --- |
| 题数 / id | 24 题，«BENCH.0301»–«BENCH.0324»（与冻结题库 id 段不冲突） |
| 分布 | 12 域 × 2 题；难度全为 3（hard）；类型 calc 11 / mc 9 / short 4 |
| 新增字段 | «srcs»（**≥2** 个真源，每题都校验存在性与行号）、«derive»（一句话说明「为什么必须组合才能答」） |
| 是否进主指标 | **否**。主评测只跑 «questions.jsonl»；本节数字仅作 v2 参考 |
| 生成器 | «_gen_derive.py»（可重跑，同样做「文件存在 + 行号不越界」断言） |

**三个样例（每题都能看出「少一个源就答不出」）**

- «BENCH.0301»（执行模型）：«instructionsPerTick=2»（«world/blocks/logic/LogicBlock.java:46»）×
  «maxInstructions=1000»（«logic/LExecutor.java:41»）→ 600 条指令要 300 tick = 5 s，且未突破 1000 上限；
  只查一个常量答不出耗时，只查上限也答不出。
- «BENCH.0319»（电力与热）：impact-reactor «power=25/tick»（«tools/block_attrs.json»）× 1 tick=1/60 s
  （«knowledge/VERSION.md»）÷ 冷却液 «cryofluid:15/s»（同一数据表）→ **100 电力/液体单位**。
- «BENCH.0324»（战斗与单位）：护甲公式 «max(damage-armor, 0.1·damage)»
  （«entities/Damage.java:659-660» + «Vars.java:133 minArmorDamage=0.1»）代入
  mace «armor=4»（«data/game/units.json»）→ 9 伤害打 5；armor=20 时被 0.9 保底 —— 三个源缺一不可。

**草案已测（lexical，kb-stage 104 文件 / 1051 chunk）**：coverage 100%、hit@6 **91.7%**（22/24）。
注意这个数字偏乐观：出题时已保证「每个源都有文章写过」，它测的是**组合检索**能不能一次捞到多个源，
不测 AI 会不会主动想到组合。真正的 v2 验收标准应是「多源问答的正确率」，不是 hit@6。

**如果扩成 v2 正式题库，建议规则**

1. 每域 ≥5 题、总量 ≥60，且**公式题占比 ≥40%**（当前 300 题只有 7.3%）；
2. 每题 «srcs» 至少跨两类真源（源码 / 数据表 / 实测 / 文档口径），并写明「缺哪个源就答错」；
3. 与冻结 300 题共用同一套 «eval_kb.py» 与 gold 口径，但在报告里**永远单列**，不合并总分；
4. 新增「答案必须给数值 + 单位」的判分项：推导题的失败大多不是检索失败，而是单位换算错（/tick 与 /s 差 60 倍）。
'''
add = add.replace(chr(171), BT).replace(chr(187), BT)
if '## 10. hybrid' in txt or '## 11. v2' in txt:
    raise SystemExit('already appended')
p.write_text(txt.rstrip() + '\n' + add, encoding='utf-8')
print('appended', len(add), 'chars, README now', len(p.read_text(encoding='utf-8').splitlines()), 'lines')
