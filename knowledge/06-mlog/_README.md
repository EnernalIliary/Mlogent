# 06-mlog index (file names starting with `_` ⇒ the check_kb.py gate does not scan them as articles)

The mlog language layer: 10 articles + 2 machine-readable tables. Wording follows the v159.3 source (semantics) and the v160.7 jar / live game (numbers).

## Articles

| File | id | Lines | Topic |
|---|---|---|---|
| M01-执行模型总览.md | MLOG.EXEC.001 | 116 | tick / @counter / budget / program steps |
| M02-变量与作用域.md | MLOG.VAR.001 | 125 | the three LVar states, null, built-in variables |
| M03-控制流.md | MLOG.FLOW.001 | 120 | the 8 jump conditions, loops, wait, rewriting @counter |
| M04-读写与感知.md | MLOG.IO.001 | 131 | read/write/sensor/radar/ulocate/getlink/lookup |
| M05-绘制与文本.md | MLOG.DRAW.001 | 138 | draw/print/printflush/@message/color packing |
| M06-世界交互.md | MLOG.WORLD.001 | 130 | control/setrule/the 26 world processor instructions |
| M07-单位与逻辑控制.md | MLOG.UNIT.001 | 117 | ubind/the 21 ucontrol subcommands/the @unit lifecycle |
| M08-性能与限制.md | MLOG.PERF.001 | 116 | budget caps/latency/stutter/memory limits |
| M09-Mindcode.md | MLOG.MIND.001 | 202 | the .mnd→mlog compile front end: cm/pm, three entry points, version arbitration, the three diagnostic columns, failure classes |
| M10-Mindcode-Syntax.md | MLOG.MIND.002 | 176 | Mindcode syntax cheat sheet (measured): variables/branches/loops/function inlining/heap arrays/interpolation, each with its compiled output |

## instructions.json (73 instructions)

Top level: `meta` + `instructions[]`. Counted by docs group: unit 24 / control 5 / op 6 / io 6 / block 6 / world 26.

| Field | Meaning |
|---|---|
| num | docs section number |
| name | mnemonic (the mlog keyword) |
| title | Chinese name |
| category | group (the 6 classes above) |
| format | export format (**72 have a value, `draw` is null**) |
| arity | number of argument slots |
| params[] | slot names (text order) |
| defs[] / uses[] | slot indices written / read (0 = the first argument after the mnemonic, from `instr_semantics.json`) |
| tokens | number of tokens this instruction takes in text |
| since_build / ver | version |
| desc | one-line description |
| doc_params[] | the docs parameter table as-is (may be placeholders `1`/`2`) |
| trap | **23 entries** carry a trap warning |
| unverified | docs have a `## 未验证内容` (unverified content) section (45 hits) |
| src | source `file:line` |

### meta.discrepancies (cmd_index and docs conflict, **docs win**, 7 entries)

| Instruction | cmd_index spelling | docs/source spelling |
|---|---|---|
| getblock | `<result> <x> <y> <layer>` | `<layer> <result> <x> <y>` |
| setblock | `<x> <y> <block> <team> <rotation> <layer>` | `<layer> <block> <x> <y> <team> <rotation>` |
| weathersense | `<weather> <result>` | `<result> <weather>` (def is at slot 0) |
| spawnwave | `<natural> <x> <y>` | `<x> <y> <natural>` |
| playsound | 7 params (merges pan/x) | 8 params: `<positional> <id> <volume> <pitch> <pan> <x> <y> <limit>` |
| status | apply / clear | true / false (the source field is a boolean clear) |
| uradar | all 7 params are live | slot 5 is a dead slot (the source passes null) |

## enums.json (13 enum groups)

| Key | Count | Use |
|---|---|---|
| RadarTarget | 8 | radar/uradar target filter |
| RadarSort | 5 | sort key |
| LLocate | 4 | ulocate locate type |
| LUnitControl | 21 | ucontrol subcommand |
| BlockFlag | 18 | block flag for control/sensor |
| ControlType | 5 | control type |
| ConditionOp | 8 | jump condition |
| GraphicsType | 16 | draw subcommand |
| LogicRule | 29 | setrule rule name |
| FetchType | 8 | which kind of entity fetch takes |
| ContentType | 18 | content type for lookup/fetch (includes `_UNUSED`) |
| LogicOp | 45 | op operation |
| LAccess | 77 | sensor attribute (v160.7 jar reflection) |

## Usage

```bash
# 查一条指令 grep -A2 '"name": "ucontrol"' instructions.json
# 统计带坑指令 python -c "import json;d=json.load(open('instructions.json',encoding='utf-8'));print([i['name'] for i in d['instructions'] if i.get('trap')])"
```

## Boundaries with other layers

- **06-mlog**: the language itself (how to write it so it matches the semantics).
- **01-execution**: engine implementation details (why it is this way, which source file).
- **08-evidence**: the evidence line numbers for every conclusion (claims.jsonl).

When the same fact appears in two layers, 06-mlog gives "how to write it" and 01-execution gives "why + file:line"; do not copy details across.

## Change log

| Date | Change | Basis |
|---|---|---|
| 2026-11-08 | task-14 expansion: M03 gains the full ConditionOp 8-value table + the truth about the test() :32-33 short-circuit; M06 gains the TileLayer four-layer writability table + layer in slot 0 + the four message/cutscene/query enums; M07 gains the 21-row ucontrol parameter table (tile coordinate convention) + radar target 8 / sort 5 / uradar's dead slot 5 + ulocate output semantics | ConditionOp.java:6-13,:31-40; TileLayer.java:3-9; LUnitControl.java:4-24; RadarTarget.java:6-14; RadarSort.java:6-11; LLocate.java:3-7 |
| 2026-11-08 | LogicRule count 30 -> 29 (counted line by line in the v159.3 source) | LogicRule.java:4-34 |
| 2026-11-17 | added M09-Mindcode.md (MLOG.MIND.001, 202 lines): the three entry points of the compile front end tools/mindcode.py, the jar/java resolution order, the 3.21.0 deadlock and the 3.19.3 ruling, the three diagnostic columns, the BOM boundary, the line between `unsupported_environment` and `compilation_error` | tools/mindcode.py:113-120,:267-290,:487-569,:704-710; tools/mlog_mcp.py:531-564; docs/Mindcode集成.md:54-84 |
