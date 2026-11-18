---
name: mindustry-blueprint
description: Use when generating, parsing, or validating Mindustry blueprints and mlog logic: extracting logic source from a blueprint, rendering logic back into a pasteable blueprint code, statically checking mlog, and looking up block content IDs and instruction formats.
whenToUse: When the task involves Mindustry blueprints (.msch / blueprint codes), writing or reviewing mlog logic, or when a block size or content ID is needed.
---

# Mindustry blueprints and the mlog toolchain


## 60-second quick start (run this first)

```bash
cd <repo>                 # 仓库根；不是 .dsh/skills 下的技能副本
python tools/mlog.py doctor
```

`doctor` prints the entry point and whether Java / the server jar are ready, then lists the five points below.

- A single entry point, `python tools/mlog.py ...`; **do not** `cd` into `.dsh/skills/mindustry-blueprint/tools` (a distributed copy that assumes different paths).
- Output is already UTF-8: read the tool result directly; **do not** redirect to `> tmp\out.txt` and then `read` it (two extra calls means two extra rounds).
- To inspect one program: `check --cost` + `ir` + `values`, three are enough; don't probe parse/text/gen one at a time.
- To run real behaviour: `python tools/mlogsim.py FILE --ticks 120 --update all`; for several files start with `--daemon` first.
- If the session exposes the MCP tools `mlog_check` / `mlog_ir` / `mlog_values` / `mlog_sim` / `mlog_gen`, **prefer calling them directly** (the server is already warm and returns JSON); don't fall back to assembling shell paths. Only use the commands above when they are absent.
- Can't recall an instruction: `python tools/mlog.py cmd <name>` / `explain <name>`, faster than digging through the source.

## Table of contents

- 60-second quick start (run this first)
- What this skill can do
- The standard loop
- Iron rules (self-check each one before generating)
- The pre-delivery checklist for logic (don't skip a single item)
- Before writing logic: look up these four things
- What the unit table has, and what it doesn't
- What the block table has, and what it doesn't
- Before writing logic: see how the corpus writes the same thing
- Writing logic: enumeration, jump table, or memory cell
- The instruction budget: don't guess, it is certain
- ⚠️ The easiest thing to get wrong: block coordinates are the "center tile"
- The author label when generating blueprints
- Automatic tagging
- Common invocations
- What to look at in the cost analysis (`--cost`)
- What `ir` looks at, and what it doesn't
- What `values` looks at, and what it doesn't
- The cross-processor mode of `values`
- `cross` looks only across processors, not at memory cells
- What `pack` looks at, and what it doesn't
- "Undefined variable" needs five tiers before you decide whether to change it
- How to hunt infinite loops
- Virus logic (self-replication)
- Reading the logic in a whole save: `mlog.py map`
- Running the corpus in bulk (in parallel)
- Thorium-reactor (钍反) protection: three facts
- Who says what the semantics are: cross-validation against a second implementation
- The standalone copy
- Run the tests after changing an analyzer
- Environment requirements (read this before sharing with anyone)
- Reference data
- Key facts at a glance


| `ucontrol move x y` takes **4 fields** | The statement object has 6 slots and `LExecutor` converts `p1..p3` unconditionally, but `move` reads only `x,y` (`approach` is the one that reads the third as a radius); `pathfind` is the same. Don't count arguments from the `0 0 0` the editor pads in |
| Writing one extra operand for a unary operator is not an error | `op floor a b`, `op sin y angle 90` — the extra token is dropped by `LParser` and has no effect at runtime, it only counts as INFO. But `op sin` takes radians, so writing `90` usually means the author thought it was degrees |

## What this skill can do

| Capability | Command |
|---|---|
| **Parse a blueprint** — extract the logic source, blocks and links | `mlog.py parse <file.msch> [--plain] [--no-text]` |
| **Generate a blueprint** — produce a pastable blueprint code from mlog | `mlog.py gen <logic.mlog> ...` |
| **Statically check mlog** — catch real bugs such as a reversed `@dead` | `mlog.py check <logic.mlog>` |
| **Cost analysis** — dead code + worst-case instruction count + converted time | `mlog.py check <logic.mlog> --cost` |
| **Dead stores / unreachable code** — CFG + live-variable fixpoint | `mlog.py ir <logic.mlog>` |
| **Constant branches / provable null** — abstract-value fixpoint | `mlog.py values <logic.mlog>` |
| **Packing layout** — field layout + how many ids the low field can hold | `mlog.py pack <logic.mlog>` |
| **Look up a block ID / size** | `mlog.py id [name]` |
| **Look up an item ID / decode a packing layout** | `mlog.py item [name] [--unpack N]` |
| **Look up unit attributes** (step one of writing logic: pick the unit) | `mlog.py unit [name]` (speed/health/armor/weapons/active ability) |
| **Look up a block's recipe / capacity / power draw** | `mlog.py block [name]` |
| **Find reference implementations** | `mlog.py find "a few words"` |
| **Look up what `sensor` can read** | `mlog.py sensor [keyword]` |
| **Look up an instruction's format** | `mlog.py cmd [keyword]` |
| **Read message-board content** — the text a message block holds in a blueprint | mlog.py text <file.msch> [--plain] |
| **Look up an instruction's read/write positions** — which parameter is the output | `mlog.py explain <instruction> [subcommand]` |
| **Look up which version this statement needs** `format` 147 / `select` 150 | `BUILDS.md` (a summary of the GitHub release notes), `mlog.py explain <instruction>` prints it directly |
| **Look up which build this logic needs** — a blueprint stores no version number | the `version gate` line of `mlog.py check` / `build >=N` of `mlogagent report` |
| **Write Mindcode (.mnd), then compile it to mlog** — high-level language → logic | `mindcode.py compile <x.mnd> -o <x.mlog>` |
| **Judge "is it correct" in one call** — static + simulation + assertions | `mlog_validate` (MCP) / `python tools/mlog_eval.py selftest` |
| **Run a whole scenario** — world + program + assertions → one verdict | `scenario.py run scenes/scenarios/<x>.json` |
| **Cross-processor reads and writes** — is what you read null or a constant | `mlog.py cross <blueprint.msch>` |
| **Regression self-test** — round-trip 429 real blueprints | `mlog.py selftest` |

The tools live under `tools/`, with zero third-party dependencies (pure standard library). `python tools/mlog.py --help`.

## What a result looks like: one envelope, four depths

All tools (including the 10 MCP ones) return the same `mlog-eval/v1` structure: `ok / stage / failure_type /
message / levels / next_steps`, and `level` controls the depth:

| level | what it adds | when to use it |
|---|---|---|
| `summary` | —— (9 keys, including `levels`) | the default for every round |
| `diagnostics` | per-item findings, assertion failures, artifacts | why it failed |
| `full` | per-tick `trace` | reproducing a hard case |

The failure reason can only be one of these 7: `compilation_error / static_analysis_error / runtime_error /
assertion_failed / timeout / unsupported_environment / simulation_real_difference`.
**Among the four dimensions of `levels` (execution/static/simulation/real_runtime), `null` = not run, not a pass** —
the executor finishing does not mean the program is correct.

## Mindcode: compiling .mnd into mlog

```bash
python tools/mindcode.py version            # 定位 jar/JRE
python tools/mindcode.py doctor --json      # 候选表 + 兼容性 + 冒烟编译
python tools/mindcode.py compile demo.mnd -o demo.mlog --target 7.0
```

**The default is 3.19.3**: on this machine 3.21.0 hangs forever when running `cm` (the PowerShell
subprocess of the update check's dev.dirs interlocks, and `--no-update-check` is ineffective because it is registered on the wrong parser). 3.19.3 needs **Java 22+**,
and the JRE 21 bundled with the repo can't install it. Diagnostics are `file:line:col category: message`, and the source file **must not carry a BOM**.

To go deeper, read `knowledge/06-mlog/M09-Mindcode.md` (`MLOG.MIND.001`): §3 is the entry point and the return fields,
§5 is the full thread stack of the 3.21.0 deadlock, §8 is "should this report unsupported_environment or compilation_error".
It does **not** cover Mindcode syntax itself (`if`/`for`/`func`/`allocate`); look that up in the upstream docs.

**How to trace an error in the generated mlog back to the source**: `mindcode_compile{source, map:true}` returns one extra
`map` (`mlog` line → `.mnd` line, from `tools/sourcemap.py`). The compiler offers no instruction-level mapping, so this table is
inferred by **prefix-compile alignment**: statements inside a block (in `for`/`while`) are always `inside control flow` and are not guessed;
statements that produce no instruction are `dead code or folded`, which is not a failure either. So "mlog line N is wrong" can start from
`entries`; if it isn't there, go back and read that part of the source honestly — **do not treat an inference as a promise**.

## Scenario: turning "run it once" into "one verdict"

`scenes/scenarios/*.json` (schema v2) = world + program + observations + assertions:

```bash
python tools/scenario.py check scenes/scenarios/unit-control.json   # 只校验 schema
python tools/scenario.py run   scenes/scenarios/unit-control.json   # 跑并判
python tools/scenario.py list
```

Templates: `unit-control` (bind a unit and move it), `building-interaction` (container→unloader→conveyor→core),
`processor-competition` (two processors sharing a memory cell, probing each other). A failed assertion points straight at **which** one
didn't match (`A1: expected ge 999, got 79`) and gives the next step.

Field notes (you will run into these while writing scenarios):
- `op` accepts only the **long name** (`greaterThan`); `op gt` is silently dropped and the variable stays null forever;
- an empty world has no core → `unitCap=0` → a unit is dead the moment it spawns, so give it a `unitCap` first;
- an unloader does not push items into an adjacent container/core; it has to go through a conveyor;
- don't end a console script with `for(...){}` (it echoes the value, and `mlogsim` waits for `undefined` and hangs until timeout).

## Resuming: where the previous round stopped

Verifying the same program three times is the worst deal: the first pass compiles and passes static analysis and simulation, then changing one line starts from zero; and when the second round fails, nobody remembers
what the first round passed. `mlog_task` stores progress as one record (a JSON file under `out/tasks/`), and the next run picks up from there.

```text
mlog_validate{ logic: "...", ticks: 30, expect: [...], next_step: "接显示器" }
  → 返回的 task 块里有 task_id 与 completed_stages
mlog_task{ action: "resume", task_id: "ts-1a2b3c4d5e", source: "<现在的程序文本>" }
  → { next_stage: "assertion", recheck: [], stale_stages: [], hint: "" }
```

Reading it is simple, and three things **must be remembered**:

- `completed_stages` belongs to `source_version` (a content hash of the source). If the source changed, the old progress is demoted into
  `stale_stages` and a `hint` is emitted — **don't treat stale as passed**; that means "verified on a different program".
- `failed_stages` / `recheck` always take priority over `next_stage`: go back and fix the failed step first.
- `next_step` is a note for the human and for the next round of yourself; on failure it should say what to try next.

Progress is **optional**: without `task` it is a one-shot verification with the same behaviour as before. The command-line equivalent:
`python tools/taskstate.py list|show|resume|clear`.

## Differential: it passed offline, is it still right in the game?

The same scenario can be handed to two hosts: `tools/mlogsim.py` (the offline real executor) and `tools/world_server.py`
(the live game world). Each side produces one `mlog-observation/v1` observation, and only after comparing them is it called "verified".

```bash
python tools/differential.py run scenes/scenarios/unit-control.json --json
python tools/differential.py parity scenes/scenarios/unit-control.json   # 只比环境
python tools/fidelity.py list        # 哪些能力离线可判、哪些根本不可
```

**A difference is not a bug**. The offline executor has no wave AI, no power grid, and terrain collision only up to "grade B"; these are written into
the 15 boundaries in `tools/fidelity.py` (verified / unverified / partial / unsupported / unknown), and
the differential report attaches an explanation to every difference — the ones it cannot attach are the real mysteries. Comparison rules are split by type: numbers get a tolerance
(0.5 tile for coordinates, 5% for health), events are matched as a subsequence by key plus a tick tolerance, and **whole-JSON equality is not allowed**.
When the world isn't up or there is no JVM, it is `unsupported_environment` + exit 3, and it will never disguise itself as a difference.

## Projection: drawing the simulation into the game (for humans)

What an offline run produces is numbers. To let a **human** see at a glance what happened (who is stuck, where the cargo piled up, whether a conveyor is reversed),
project the simulation into the live world: buildings are really placed, and units are sprite markers that move with the feed.

```powershell
# 世界侧：只给 feed（场景自己会跟着 feed 来）
python tools/world_server.py --map '<图名>' --watch-feed out/_proj/feed.json

# 仿真侧：--scene 决定复刻什么；--rt 1 = 60 tick/s（看得见的速度）
python tools/mlogsim.py --scene scenes/sim/sandbox-haul.json --ticks 1200 --rt 1 `
  --push out/_proj/feed.json --push-every 3
```

Three things to know:

1. **The scene doesn't need to be pointed at again**. `--scene X --push F` writes X into the feed's `scene` field, and the director reads it itself;
   `--watch-scene` is only used when you want to compare another scene against the same feed. Starting the server first or the simulation first both work (it "hot-connects").
2. **Projection is not verification**. It is a view for humans; the verdict still comes from `mlog_validate` / `mlog_sim --assert` /
   `differential.py`. Don't take "it looks right on screen" as a conclusion.
3. **Judge by numbers**: `count` from `world_client.py projstat` (how many sandboxes are projecting), `builds` (how many buildings were rebuilt,
   which should equal the number of `buildings` entries in the scene), `off` (the coordinate offset). When `count == 0`, first check whether the feed has a `scene`, and
   whether the file the scene's `code` points at still exists.

| Symptom | Most likely cause |
| --- | --- |
| Shadows but no buildings | the feed is in the old format (no `scene`), or the file the scene's `code` points at is gone |
| Buildings appear then vanish | the feed hasn't updated for over 25 s (simulation ended / stuck) |
| The frame flashes once and disappears | frame age > 10 s; use `--hold 60` while debugging |
| `连不上世界控制口` | the server process is dead and `daemon.json` is a leftover handshake — restart the server, don't trust that file |

One-line MCP version: `mlog_sim{scene, ticks, rt, project}` → the return carries `projection.watch` (copy it to start the server);
`world_arm{feed}`; `world_projstat{}`. Full troubleshooting is in `docs/联机调试世界.md` §17.

## The standard loop

```
写 mlog  →  mlog.py check --cost  →  mlog.py gen  →  游戏内实测  →  结论写回本文件
              ↑                                                        │
              └────────────────────────────────────────────────────────┘
```

**When generating a blueprint you must obey "deterministic + self-verifying"**:

- The same source + the same set of parameters → **exactly the same bytes** (don't introduce timestamps/randomness)
- Run `check` before generating
- After generating you **must** parse it back to verify (the tool does this internally and refuses to output on failure)

## Iron rules (self-check each one before generating)

1. **`@dead` returns 1 for a dead unit** — "if it's dead, rebind" must be written with `equal`, not `notEqual`. **This one has caught real bugs.**
2. **You must `ubind` before controlling a unit** — otherwise `@unit` is `null` and every `ucontrol`/`uradar`/`ulocate` silently does nothing. `ubind @flare` **binds the same type in rotation** (an internal counter, +1 each time); `ubind someUnit` binds that specific unit. To keep watching one unit, don't rebind by type repeatedly.
3. **The 8th argument of `ulocate` must be captured** — writing `0` throws the building reference away, and `itemTake`/`itemDrop` are impossible afterwards.
   (`core` is not a built-in keyword; it is merely the **variable name** that receives this output.)
4. **Use `move` at the pickup point, not `approach`** — `approach` stops outside the radius and may not reach the warehouse, while `itemTake` **silently skips** when it cannot reach.
   `move` doesn't read the 3rd parameter. (`move` is accurate to 1 tile; `approach` stops at `radius - 7`)
5. **`ulocate` must run unconditionally; it cannot go inside a branch** — otherwise the coordinates are never assigned on the other path and the unit flies to `(0,0)`.
   Reading core inventory has no built-in variable: first `ubind` to get a friendly unit (commonly `@mono`), then `ulocate building core false @copper cx cy cf core`;
   `sensor n core @silicon` / `sensor cap core @itemCapacity`. When `cf=0`, filter it out first; don't fly to the coordinates.
   `ulocate`'s `outBuild` is given **when in range or on the same team**: `unit.within(max(range, buildingRange)) || build.team == exec.team` (`LExecutor.java:249-259`). So "far away always means null" is wrong — a same-team core is returned no matter how far; only a different team and beyond range is null.
   **A link name is not the block's full name**: the game takes the last hyphen-separated segment of the block name (`silicon-arc-furnace` → `furnace1`), so writing the full name never binds; `check` reports `link-name-hyphen`.
6. **`end` is "jump back to the start"**; it cannot be used to "finish a branch and carry on downwards". For mutually exclusive branches use `jump`.
7. **`jump` stores an absolute line number** — adding or removing a line shifts everything; count them all before generating. Check especially: whether the target lands on a line with side effects such as `sensor`/`set`.
8. **A unit can carry only one kind of item** — `itemCapacity` is the **stack limit**, not the limit per item type.
9. **`op` has a fixed arity** — unary operations such as `abs`/`floor`/`sin`/`rand` take only 2 parameters.
   (extra tokens don't take part in execution and behaviour is normal, but it is also not the operation you thought.)
10. **Don't invent thresholds yourself, and don't do feasibility arithmetic** — the game mechanics only require some lower bound; meeting it is already full efficiency.
    Real battlefields have blockers and traffic jams; **"it runs" is measured, not calculated**.
11. **Don't change correct code just to please the checker** — the checker is a hinting device; measurement is the standard.
12. **Don't write statements after `end`** — it "jumps back to the program start", it doesn't "finish". Everything written after it is dead code.
    One run of `--cost` shows this (it lists them directly).

## The pre-delivery checklist for logic (don't skip a single item)

When you're done, go through it in order; every item must have an answer before delivery:

1. **Ask the person who asked** — quantities, thresholds, failure strategy (what to do when exceeded: stop / degrade / alarm), which blocks it depends on, the required period. If you haven't asked, ask; don't decide yourself. Thresholds are the easiest place to "I thought so": the 0.5 that thorium-reactor (钍反) anti-explosion needs I only know to be the explosion line, and the 0.30 working point is my judgment, which must be stated.
2. **`check`**: `0 error / 0 warn`. Anything like `no-target-jump`, `version drift`, `noop` must be explained first.
3. **`ir`**: no `reported` dead store; unreachable code must come with a "why it is kept".
4. **`cost`**: the `worst-case path` and the ticks per cycle must match the period in the requirements; look at the `⏸ blocking` of `wait` along with it (it burns not a single ipt, but the cycle time is often all in it).
5. **`values`**: no unexpected always-true/always-false branches and no provable null (especially `equal X null` — an unassigned variable is 0, and only `===` distinguishes null from 0).
6. **Cross-processor** (when `read`/`write` on another processor is used): `cross` reports `0 never-assigned`; the slot name must be declared on the other side first, and spelled the same.
7. **Signature**: for AI-generated logic first `python tools/aigenerated.py sign <file>`, and run `verify` once before delivery. `mlog.py gen` now **signs automatically by default** (the source file is signed as well; `--no-sign` turns it off). The signature goes into the **declaration parameter slot** of the last statement: if what precedes `end` is `jump N always <value>`, write it into that jump's compare slot (`jump N always <value> "aigenerated:author:id"`, keeping both the jump and `end`); otherwise replace/append the trailing `end` with `jump 0 always 0 "aigenerated:author:id"` (`always` does not read value/compare, and `jump 0` zeroes the counter just like `end`). A jump that already carries a compare is not overwritten; it falls back to the terminator-line form. `LAssembler.write` always outputs 4 parameters and pads a missing compare with `false`, so occupying the value slot would be rewritten; extra trailing tokens (`end "…"`) are lost when re-serializing. `#` comments are not kept in the body; they are compressed into the token's base64 payload (with the original line number + statement anchor) and can be retrieved with `aigenerated.py extract/restore`; the hash covers only the comment-free body. Changing the logic or deleting the signature both make verification fail (`strip` is rejected by policy). Name variables in the corpus style you see under `style`.
8. **Write the assumptions down**: beyond static analysis, timing, cross-processor reads and writes, unit movement, production/weather/bullet hits all need the real executor via `tools/mlogsim.py` (see the next section); the parts the simulator cannot cover (graphics, wild AI, waves, chain consequences of a destroyed building) are reasoning, not verification. Say explicitly at delivery which parts were "run" and which were "read and look right".
9. **Produce the blueprint with `mlog.py gen`**, don't hand-assemble base64; after generating, run `ir`/`check` once more to confirm the logic wasn't truncated.

## The simulator: `tools/mlogsim.py` (the real executor)

Static analysis answers "does it read correctly"; this tool answers "does it behave like that when run". It drives the real `LExecutor`, not a rewritten VM.

```bash
python tools/mlogsim.py my.mlog --steps 10                  # 指令级：只跑逻辑，不跑世界
python tools/mlogsim.py my.mlog --ticks 120 --update all    # tick 级：工厂/传送带/单位也动
python tools/mlogsim.py my.mlog --save scene.msav --ticks 120 \
  --units fortress:1 --trace out/t.csv --assert-last "chp < 3500"
```

- Defaults to v160.7 (`out/_server160.jar`) + JRE21; override with `MLOGSIM_JAR`/`MLOGSIM_JAVA`. The blank world defaults to 64×64; `--host` uses a random real map; `--save` loads a save (it automatically finds free space next to our core to place the entry processor; `--base X,Y` overrides).
- `--units name:count` spawns units, `--unit-pos X,Y` sets the tile spawn point; `--unit-ai all` makes the units already in the scene act on AI as well. A unit landing on a solid tile gets `kill()`ed on the first `update()`, so there is a `PREFLIGHT:` check — far cheaper than "run 1200 ticks and find the unit never moved"; `--no-preflight` turns off only the unit survival check.
- `--core-items ITEM:N,...` fills the core with inventory (in a blank world a `core-shard` is placed automatically next to the processor); `ulocate`/`itemTake`/`itemDrop` become assertable from there. Taking and dropping items requires the same team, a target that has `items`, and a distance within `45 world + half the block width` (about 6 tiles); `itemTake`/`itemDrop` are also gated by `LogicAI.transferDelay`, so the first few ticks after a unit spawns fail silently — retry in a loop (it only succeeds after about 30–40 ticks), and a single instruction must not be treated as "succeeds in one go".
- `--links auto` (the default for `.mlog`): a bare `.mlog` has no link table, so the simulator finds the link names that are "read but never assigned" (`cell1`, `bank1`, `message1`, `dome1`), places blocks of the same kind next to the processor and connects them (same team, within 10 tiles); `.msch` uses its own link table; `--links off` restores the original behaviour (reads `null`). A link that couldn't be placed, or is beyond 10 tiles, now reports `PREFLIGHT: link 'x' did not bind` in the preflight stage, instead of only being found to be null after the run.
- **Batching and warm-up**: `mlogsim.py a.mlog b.mlog --ticks 60` starts the JVM once and reloads the world before each file (about 0.12 s); `--daemon` warms up in the background first, and `--remote x.mlog --ticks 60` submits a task directly (about 0.6 s per file, about 3.7 s cold). You can start `--daemon` already during the preprocessing stage, then `--remote` after checking/tagging finishes.
- The `@this` address of `read`/`write` is a **processor variable**: `read v @this "slot"` reads and `write v @this "slot"` writes, and the name is a **string**; writing a name that never appears in the program is a silent no-op (`check` reports INFO `self-write-noop`), and reading a name that never appears yields `null` (`self-read-undefined`). A numeric index `read v @this 0` fetches a link, not a variable.
- **Declaration is not assignment**: the assembler's `readVar()` uses `vars.get(name, true)`, so a name appearing for the first time in any statement is created (initial value null) without requiring `set`. Hence `draw triangle a b c d e f` is a compact "declare 6 at once" (each is null→0); only names that never appear anywhere in the text count as undeclared. In `op add x copper 1`, `copper` is declared but never assigned, so what you read is null (not 0); `check` will not report it as "undefined", and you must guarantee the assignment yourself arithmetically.
- Only `--update all` runs `Building.update()` (factories, conveyors, power consumers) and `LogicAI` units; `--power full|none` pins power; `--combat on` (the default with `--ticks`) advances bullet physics/collision/damage in `Logic.updateEntities()` order; `--weather rain` can force the starting weather.
- **The third parameter of `sensor` must be an `LAccess` property** (75 of them: `@x`, `@health`, `@totalItems`, `@itemCapacity`, `@config`, `@shootX`…). Supplying an item/block name (`@copper`, `@hyper-processor`) raises no error; it merely reads null and the branch silently never fires; `check` now reports WARN `sensor-not-a-property`.
- `ucontrol stop` **is not a brake**: it only clears `mineTile`/`building`, and velocity decays through drag (measured: still about 0.1 tile of residual displacement after 120 ticks); to stop immediately, don't issue a `move` or `move` it to the current point.
- `--trace FILE` writes one line of logic-unit trajectory per tick (`unit,tick,ux,uy,uhp,range,tx,ty,dist,cx,cy,chp,bullets,shots`, in tile coordinates); `--assert EXPR` evaluates on every line and `--assert-last EXPR` only on the last line, exiting 3 on failure. The column names are the variable names.
- Privileged statements (`weathersense/weatherset/setrule/message/cutscene/effect/fetch/sync/getblock/setblock/spawn/status`) are understood only by a world processor; put them in a micro processor and **the whole line is silently deleted**. `--processor auto` picks the processor from the statement.
- Privileged **built-in variables** (`@server`, `@client`, `@clientLocale`, `@clientUnit`, `@clientName`, `@clientTeam`, `@clientMobile`, `@clientMusicPlaying`) don't error in an ordinary processor; `GlobalVars.get(name, false)` replaces them with the `null` constant — the branch never fires. To test the player/client in ordinary logic, switch to a world processor or to data observable in-game.
- It can prove: `move/approach/within/@x/@y`, `ipt`, cross-processor reads and writes, production progress, weather timing, damage from bullet hits. It cannot prove: wild AI, waves, the power graph, real terrain collision, the chain reaction of a destroyed building; `draw` executes but draws no picture. **Real game behaviour must be accepted by the player**.

### Value ranges and jump tables: `tools/mlogrange.py`

```bash
python tools/mlogrange.py ranges my.mlog --var unit.n
python tools/mlogrange.py jumps  my.mlog --var unit.n
```

- `ranges` is a forward interval analysis: intervals are propagated only from write points, and branches narrow them by comparison with literals. The results of `sensor`/`read`/`ubind`/`ulocate` are always **unknown** and are not guessed.
- `jumps` unrolls arithmetic dispatch such as `op add/sub @counter @counter V` and gives the target per value; `set @counter <variable>` can only be unknown.
- It answers "what value might it take / where might it land", not "what it definitely will". When a loop doesn't converge it is relaxed to unknown.

### Instruction-level execution flow: `--itrace`

```bash
python tools/mlogsim.py my.mlog --ticks 60 --itrace out/it.tsv --itrace-var unit.n
```

One line per executed statement: `tick  pc  vars  source`. `pc` is the `@counter` at that moment, and `vars` is a snapshot of the named variables (objects show as `<obj>`) — finer than `--trace` (which records only unit trajectories), good for "on which tick did it reach which line, and what were the variables". `.msch` is not supported yet, and per-instruction tracing has overhead.

Scenarios: `out/scenes/` holds 5 real saves (open / garded-line / maze / PVP / campaign); `benches/run.py` is four synthetic benches — memory/processor/sensor/core (62 assertions); `_snapshot.py` produces PNG snapshots.

Note: `mlogsim.py` exists only in `tools/` at the repo root (the standalone skill copy doesn't include it, because it needs Java + `out/_server160.jar`); the commands below all assume the current directory is the repo root.

## Before writing logic: look up these four things

What you lack when writing logic is never syntax; it is the **goal** and the **game facts**. These three commands cover the three big parts of the latter:

```bash
python mlog.py find "wireless overdrive"     # 1. 别人怎么做的（先找参考，别自己发明）
python mlog.py unit flare                    # 2. 这个单位的速度/血量/能带多少货/会不会飞
python mlog.py block silicon-smelter         # 3. 这个方块吃什么、产什么、装多少、多少电
python mlog.py sensor heat                   # 4. 这个属性到底读的是什么（75 条，见下）
```

- `find` scans every blueprint in the game's schematic directory (`MLOG_CORPUS` can override it), scores them by `name/description/message board/variable names/instructions`, and prints a **score breakdown** — when a match is wrong you can see why. By default it skips blocks with >5000 statements and files >2MB (`BADAPPLE!!` is a 560k-statement animation, `Linux on mlogv32` is 16MB), since those are not reference logic. 9 s the first time, 0.7 s from cache afterwards; `--rebuild` forces a rebuild.
- The data for `unit` / `block` is extracted from the source by `tools/units_from_source.py` and `tools/blocks_from_source.py`, and `--check` verifies whether it matches the current source. **They list only the fields written in the source**; a missing field is an engine default (`unit` marks it `(default X)`) — don't fill it in from memory.

**"Does this block accept X"** is the easiest thing to get wrong, and getting it wrong is silent — haul the wrong item and nothing happens on screen. The rule comes from the source
(`BuildingComp.acceptItem` = `block.consumesItem(item) && capacity`, and `consumesItem` is a boolean array filled in by the consumers), so:

| `accepts` | meaning | example |
|---|---|---|
| `any` | checks capacity only, accepts everything | `core-shard`, `container` |
| `recipe` | **accepts only the items in its recipe** | `silicon-smelter` accepts only coal and sand |
| `custom` | accepts, but what it takes and where it goes depends on config | `sorter`, `unloader`, `conveyor` |
| `none` | accepts nothing at all | `landing-pad`, `PayloadUnloader` |

Reverse lookup: `mlog.py block --accepts coal` lists every block that accepts coal (recipe inputs + `any` + `custom`).

### The 75 properties of `sensor`

The third parameter of `sensor <result> <target> <property>` is a **runtime object**, and it may also be a variable. There are only 75 properties,
all from `LAccess.java`; `mlog.py sensor` prints one per line with one plain-language sentence:

```
python mlog.py sensor                # 全部 75 条
python mlog.py sensor heat           # 按名字或说明搜
python mlog.py sensor --settable     # 只有 control 也能写的（只有 3 条）
python mlog.py sensor --on unit      # 只有能从单位读的（37 条）
```

The three easiest to trip on:

| property | trap |
|---|---|
| `@heat` | on a reactor it is heat in 0..1; **on a force projection it is "shield already lost"**, not heat |
| `@size` | for a block it is the side length; **when the target is a string it returns the UTF-16 length** |
| `@dead` | returns 1 when the unit is dead, **and also 1 when the unit is null** — it cannot serve as an existence test |

### Version gate: the baseline is build 146

In `instr_semantics.json`, 46 instructions carry `min_build`: those with a definite source are `format` 147, `select` 150,
`emod`/`ushr` 150, `bullet` 157, `getblock` 157, `effect`/`sync` 146; the rest are marked from the **v7 baseline 146**,
with the reason written in `BUILDS.md`. The gate criterion is `floor > 146`: **equal to the baseline is not reported** (everyone stayed on that version for a year).
Seven of them (`printchar`/`unpackcolor`/`localeprint`/`query`/`makemarker`/`setmarker`/`clientdata`)
have no ascertainable introduction version and are **left blank rather than guessed** — not writing a number without a source is the only rule this file has.
Note that `custom` only answers "might accept"; **"does it accept right now" depends on runtime state** (a sorter's config, whether a router is empty, whether an incinerator has power).

## What the unit table has, and what it doesn't

`mlog.py unit <name>` prefers an exact name match (`unit oct` will no longer be crowded out by `spiroct`), and on a single hit prints three extra lines:

| field | where it comes from | how to use it when writing logic |
|---|---|---|
| `speed` / `health` / `armor` / `hitSize` | the value explicitly assigned in `UnitTypes.java` | compute intercept time, and whether it survives one volley |
| `weapons[].damage/speed/lifetime/pierce/shots` | the `bullet = new XBulletType(...)` inside the `new Weapon(...)` block and its `{{ }}` | estimate DPS; `lifetime × speed` sets the range ceiling |
| `abilities[]` | `abilities.add(new XxxAbility(args))` | whether the unit repairs itself, shields itself, or spawns minions |
| `immune_to` | `immunities(StatusEffects...)` | **none of the 39 vanilla units declares one** — absent from the table means undeclared, don't guess |

**Three reading traps**:
- `abilities.args` is **raw source text**, so it will contain expressions like `60f * 8`. Don't read it as a number; what it expresses is "8 seconds".
- A field **absent** from the table = not written in the source = the engine default (see `defaults` in the JSON), not "zero".
- `itemCapacity (default -1)` means the unit cannot carry anything, not that its capacity is 1.

## What the block table has, and what it doesn't

`block_attrs.json` is extracted from `Blocks.java` by `tools/blocks_from_source.py`; 253 blocks have a behaviour record.

```bash
python mlog.py block cryofluid-mixer     # 一个方块的完整画像
python mlog.py block --accepts coal      # 谁吃煤（按 recipe / ammo / any / custom 分组）
```

For a block you can look up:

| field | example | meaning |
|---|---|---|
| `build` | `lead:65 + silicon:40 + titanium:60  (crafting)` | build recipe + category; several `requirements()` calls merge into a cheap tier/upgrade tier |
| `liquids` | `water:12/s -> cryofluid:12/s` | input liquid → output liquid, **already converted to per second** |
| `inputs` | `coal:1 + sand:2 -> silicon:1  craftTime 40` | recipe inputs (once per craftTime) |
| `booster` | `silicon:1  (optional; speeds the block up)` | optional speed-up input, **it runs without it** |
| `coolant` | `water` | coolant (not part of the recipe, affects efficiency) |
| `accepts` | `any` / `only ...` / `ammo ...` / `nothing` | whether logistics can insert into it |

Three reading traps:

1. **`build` is not the recipe.** The `build` line is "what it takes to build this block"; `inputs` is "what it eats while producing". When writing a production line you need both.
2. **Liquid amounts are per second** (the source writes per tick; `_rate()` converted it). What it can't convert is shown as the source expression verbatim, with a boolean overload.
3. **"Burning a whole item class" has no list.** `rtg-generator` shows `burns radioactive items (no fixed item list)` — the engine decides by category, so don't go looking for exactly which items it eats.

## Before writing logic: see how the corpus writes the same thing

`find` answers "who has done this", `style` answers "what did their code end up looking like". Run it once before writing logic, then write following that naming and shape, so what you generate doesn't look alien.

```
python mlog.py style 着陆 调度        # 多词不用引号
python mlog.py style 钍反 防爆 --limit 2
python mlog.py style 无线超 --code 20  # 连源码前 20 行一起看
```

Every hit prints six items:

| item | what to read it for |
|---|---|
| `naming` | the author's private vocabulary (op names/jump conditions/link names/literals already removed) — pick new variable names in this style |
| `flavour` | how many of each: `dotted`(`i.item.min`) / `underscored` / `Chinese` / `plain` — choose one, don't mix |
| `shape` | instantly recognisable habits: dispatch table, `select`, `wait` pacing, named cross-processor slots, memory cell, `ubind`+`ucontrol`, message board, `sensor @unit/@this` |
| `cost` | the conclusion line of `--cost` (worst-case path / ticks per cycle on a micro processor) |
| `links` | which blocks this kind of logic actually connects — and by the way, you learn what you need to connect |
| `opens` / `closes` | the first two statements and the last two (signatures, `jump N always 0 false` padding and other wrapping-up habits) |

When several processors in the same file hold the same program it is shown only once, marked `(+N more block(s) in this file)`.
The search text includes the **file name**, because the corpus file names are themselves Chinese descriptions (`11-12双液体大超着陆合金气旋`).

## Writing logic: enumeration, jump table, or memory cell

There is no "fetch content by index" primitive in mlog — `@copper` is a constant object, and you cannot write `@[i]`. So "iterate over an item table" always means building the table yourself, and **building the table costs about the same as spelling it out**:

| approach | cost per item | when to choose it |
|---|---|---|
| enumeration (spelled out) | 2 lines (`sensor` + compare) | the list is fixed, each item compares a single value, and the result must be reviewable at a glance |
| jump table `op add @counter @counter i` | also 2 lines (`set it @x` + `jump`) + loop state | the list is long (>20), or each item also has to do several things along the way |
| objects in a memory cell | 1 cell + N init `write`s + 1 `read` per cycle | the list must be changeable at runtime — **but objects in a cell are build 160+ only** |

Three facts you must know first:

- **The third parameter of `sensor` is a runtime object, not a literal**: `LExecutor.java:668-719` `Object sense = type.obj(); if(sense instanceof Content co){ to.setnum(se.sense(co)); }` ⇒ `sensor n core it` (with `@copper` held in it) is legal. **Enumeration is not forced by the syntax**; it just has less state and is cheaper.
- **A tie needs a definite resolution**: enumeration keeps order with a strict comparison (`jump s greaterThanEq n best_val`); the loop version also has to write that rule out explicitly, there is no saving it.
- **Let the generator own the list**: the item array lives as a Python list in `tools/gen_*.py`; adding an item = change one line + regenerate with `mlog.py gen`. Hand-editing the list inside the mlog will definitely drift.

Counter-conditions (don't enumerate then): more than 20 kinds of items, the list has to be configured by someone else in game, or each item also has to do other things along the way.

## The instruction budget: don't guess, it is certain

**One statement = one instruction, and `jump` is 1 too, no different from `op` / `print`.**

In `runOnce()` **`counter` is incremented first, then the instruction executes, regardless of its type** (`LExecutor.java:111-121`):

```java
instructions[(int)(counter.numval++)].run(this);   // ← 无条件 +1
```

⇒ **The cost is spent on "loop iterations × statements in the loop body", not on the word `jump`.**
⇒ Using `jump` to skip a section does save the lines being skipped, but **the jump itself still costs 1**.

**The per-tick allowance** (`LogicBlock.java:564-578`, `ipt = instructionsPerTick`):

| processor | ipt | per second |
|---|---|---|
| micro-processor (微型) | **2** | 120 |
| logic-processor (逻辑) | **8** | 480 |
| hyper-processor (超级) | **25** | 1500 |
| world-processor (世界) | **8** (`maxInstructionsPerTick = 1000`) | 480 |

**Two things that are easy to miss**:

- **Only `wait` / `stop` / `printflush @wait` `yield`**, ending this tick's allowance early; **`jump 0 always` has no such mechanism** and will burn the whole allowance within one tick
- But during `wait` the processor is **idle** and does no other work; to compute while waiting (watch a unit, poll a target, multitask) use `op add cfg.timer @time 500` + `jump ... greaterThan @time cfg.timer`, don't spin on `wait`.
- `setrate` is the only instruction that changes ipt, capped by `maxInstructionsPerTick` (the logic card sets **40**, 5× the default 8); `@ipt` takes the new value immediately, but **this tick's loop boundary is already fixed**, so it only takes effect next tick

**So run `check --cost` before changing a loop.** The seconds it computes are the unit's latency from "seeing" to "reacting".

## ⚠️ The easiest thing to get wrong: block coordinates are the "center tile"

In a schematic the Stile stores the block's **center tile**, not its top-left corner. **Double-verified**:

- Source: `Tile.setBlock()` spreads a multi-tile block with `int offset = -(block.size - 1) / 2` → `(x,y)` is the middle tile
- Empirical: among 624 real blueprints, reading it as a "corner" yields **11 block overlaps**; reading it as a "center" yields **0**

So for a 3×3 block whose footprint should occupy `(3,1)–(5,3)`, **the center must be written as `(4,2)`**.

A link's `name@dx,dy` must likewise point at **any tile within the block's footprint** (the tool validates against the footprint and tells you).

## The author label when generating blueprints

For blueprints this repo generates with `mschgen`, `labels` is always `["[blue]DeepSeek"]`
(the "work source" category in the user's tag system), and the description ends with `逻辑 by [#8abcd1]DeepSeek[]`.

## Automatic tagging

Blueprint tags (color = dimension, private-area icon = value identity) are applied by hand, but **24 of those values can be inferred from the content**,
with held-out precision ≥70%:

```bash
python tools/corpus/label_auto.py                      # 学习规则 + 留出集报表
python tools/corpus/label_auto.py --suggest F.msch      # 只输出可信建议(附依据与精确率)
python tools/corpus/label_auto.py --apply F.msch --out DIR   # 写回副本,不动原件
```

Values such as `数量` / `品质` / `系列` / `无线` / `火控` whose precision cannot be measured never appear in the suggestions —
they are either subjective judgements, or one blueprint touches all three. The write-back rewrites only the tags section and carries every other byte over unchanged.

## Common invocations

> One-line descriptions of every subcommand are in 「工具索引」 of `.dsh/skills/mlog-agentskill/SKILL.md`.

```bash
### 解析:看逻辑源码和结构
python tools/mlog.py parse "schematics/无线超.msch"

### 检查:生成前必做
python tools/mlog.py check logic.mlog
python tools/mlog.py check logic.mlog --cost
python tools/mlog.py check --msch out.msch

`check` 的 INFO 不是错误：`@server` / `@client*` 是特权内置量，micro/logic/hyper 里读到的是 `null` 常量，只有 world processor 有真值；这条 INFO 是在问“这段逻辑到底跑在哪个方块上”。

### 成本分析:死代码 + 最坏多少条指令 + 折合几秒
python tools/mlog.py check --msch out.msch --cost

### 死存储:赋值了但整个程序(含跨周期)从未读取
python tools/mlog.py ir logic.mlog
python tools/mlog.py ir --msch out.msch
python tools/mlog.py ir --all logic.mlog    # 连语法强制的输出槽一起列

### 值域分析:常量分支 + 可证 null
python tools/mlog.py values logic.mlog
python tools/mlog.py values --msch blueprints/*.msch
python tools/mlog.py values logic.mlog --trace r   # 逐次打印 r 的抽象值

### 打包配置:字段布局 + 低位字段能装几个 id(能直接指认容量 bug)
python tools/mlog.py pack logic.mlog
python tools/mlog.py pack --msch out.msch

### 生成:只放处理器(链接目标需自己摆)
python tools/mlog.py gen logic.mlog --name "我的逻辑" --link dome1@3,1

### 生成:连目标方块一起放(--with-block 坐标是【中心格】)
python tools/mlog.py gen logic.mlog --name "示例" \
    --link dome1@2,1 --with-block overdrive-dome@2,1=248 \
    --out paste.txt --binary out.msch

### 查方块 ID 和尺寸
python tools/mlog.py id overdrive

### 查指令格式
python tools/mlog.py cmd ulocate

### 查一条指令到底哪个参数是输出(哪个是枚举、哪个会被读)
python tools/mlog.py explain ulocate
python tools/mlog.py explain ulocate ore     # 只看 ore 分支
python tools/mlog.py explain select
python tools/mlog.py explain op add
```

**Blueprint codes always come from `mlog.py gen`; never assemble the base64 yourself.** Doing it by hand once, the prefix was written as `"bXNjaAF4n" + b64[8:]` (a 9-character prefix but slicing off only 8), the length became `4k+1`, and the game reported straight away `Length of Base64 encoded input string is not a multiple of 4.` — the file was fine; what was broken was the string concatenation step.

Two details that are easy to misread:

- The prefix is **not fixed**: the game writes `78 9c` (default zlib), `mschgen` uses `78 da` (maximum compression) ⇒ the 11th character differs (`bXNjaAF4**2**mPg` vs `bXNjaAF4**n**mPg`). **Both are legal**; only the decoded `msch` magic counts.
- The coordinates of `--with-block` / `--link` are **relative to the processor's center tile**, which is not the same thing as the block's absolute coordinates.
- **Coordinates copied straight from a map/blueprint need `--abs`**: `--at 3,0 --with-block overdrive-dome@5,1 --abs` means "on the map, (5,1)", and internally becomes the relative (2,1); without `--abs`, 5,1 is taken as an offset, the dome gets pushed to (5,1), and the canvas goes from 4×3 to 7×3. When the command detects "offset ≥ --at" it prints a `# note: ... looks absolute` line as a reminder.
- **Output coordinates are always normalized to (0,0)**: `--at 20,20` is only the frame of reference used when placing, and `build()` subtracts the origin of the whole bounding box before writing to disk (real blueprints start at 0 too). It once didn't subtract: `--at 20,20` produced a 24×21 canvas with the content offset into the bottom-right, and after pasting everything was off by 20 tiles — looking at `size` and the tile coordinates with `mlog.py parse` catches it instantly.
- `--source` is read as `utf-8-sig`: PowerShell `Set-Content -Encoding utf8` writes a BOM, and a first line beginning with a BOM compiles to `noop` and is silently dropped (the symptom is that the first statement never executes).

## What to look at in the cost analysis (`--cost`)

```
statements      : 159                     ← 语句数,>1000 会被静默截断
reachability    : all statements reachable ← 或列出永远跑不到的语句
opcodes         : op×62, jump×40, ...      ← 指令构成
loop heads      : L28(×80), L52(×80)       ← 循环起始行 + 推定圈数
worst-case path : ~2001 instructions       ← 一次完整决策最坏多少条
    ⚠ over LExecutor.maxInstructions (1000/tick): one cycle needs 2.0 ticks
    micro-processor  @ipt=2    1000 ticks (  16.7 s) per cycle
  ⏸ blocking      : 2 wait statement(s), ~240 ticks (4.0 s) blocked per cycle
      L3: wait -> ~120 ticks
```

**How to use these three numbers**:

| what you look at | what it tells you |
|---|---|
| **UNREACHABLE is non-empty** | there is dead code. Most often something written after `end`, or a mistyped jump target |
| **worst-case > 1000** | one decision cycle doesn't fit in a tick, so the unit's response lags accordingly |
| **the seconds converted via @ipt** | directly answers "can this logic keep up with the battle" |
| **the ⏸ blocking line** | `wait` burns not one ipt, yet almost all of the cycle time is here |

**Note**:

- Loop iterations are inferred from **the constant in the guard** (`jump 37 greaterThanEq index 80`). A loop with no visible constant counts as one iteration, with a warning
- The result is an **upper bound** (mutually exclusive branches are not pruned), meaning "how bad it can get", not "how much it usually is"
- A back edge to line 0 = the main loop, counted as **one iteration only** (mlog re-runs the whole thing every tick anyway)
- **`wait` is counted separately**: the argument is **seconds** (60 ticks = 1 second), `wait 0` doesn't block, it only means "runs once per tick";
  `blocked` is already multiplied by the iterations of the loop containing it and added into the tick counts of all three processors. When the argument isn't a literal it reports `UNBOUNDED` and doesn't make a number up
- A value such as `>=1001` means **the loop body alone fills the 1000 budget**; the real total is larger and can't be computed;
  a calm-looking `~N` is the one that was actually measured

## What `ir` looks at, and what it doesn't

Four tiers; only the first is printed by default:

| tier | meaning | should you care |
|---|---|---|
| `reported` | nobody read the value before it was overwritten (`overwritten`) / nobody ever read it but it was written more than once (`stale-write`) | **yes, it's a bug, go look** |
| `slot` | a multi-output slot of `ulocate`/`ucontrol`/`radar`/`sensor` is never read, and it is **written only once** | forced by the syntax, not an error |
| `declaration` | `set x <literal>` and nobody reads it | declarative initialisation; **it may also be configuration left for the user** (`set count 0`, `set limit 40`) — if there is a `cfg.` name or a header comment, don't delete it |
| `annotation` | the variable name is pure punctuation (`//`) | mlog has no end-of-line comments (only `#`), so the author used it as one |

`stale-write` is a tier added for "a forced output slot written twice": written **once** with nobody reading it may just be the syntax forcing you to name something (`slot`, demoted and hidden); but **writing the same slot twice** with nobody ever reading it proves the first write is discarded — that is a real bug. Example: in the micro-processor @(16,8) of `17十七硫幽灵四熔毁四油海啸组.msch`, `found` is written by `ulocate` once at `L6` and once at `L61`, and read nowhere in the whole program; before the change it was hidden by the `slot` tier (`dead-store 0(+3 hidden)`), and only after the change was it reported.

**Calibration (whole corpus, 617 files / 2409 blocks, simulator blueprints excluded)**: 80.9% of processors **report nothing at all**, p50=0, p90=1; the mean of 0.829/block is pulled up by about 20 code-generation-style blueprints. 28 sites were sampled and checked by hand, and **all of them were real**.

**It cannot prove your logic is correct**:
- It doesn't cross processors (note: `read`/`write` can access another processor's variables **by name** (the name must be declared over there beforehand, and writing to an undeclared slot is a silent no-op). This idiom is nowhere to be seen in the old blueprint library, so for an old library the judgement "this variable was never assigned" is reliable; in a new library it is a legitimate "assigned elsewhere" path — confirm whether the two logics come from the same generation before reporting tier A.) — another processor using `read x cell1 "name"` to read it is invisible here (measured: 0 cases in the whole corpus, but if `never-read` is reported you still verify it yourself)
- It only judges "is the value used", not "is the value computed correctly" (`op add dx dy dx` meant to compute a distance but wrote addition; `ir` does not report it)

## What `values` looks at, and what it doesn't

`mlog.py values` runs an **abstract-value fixed point**: for every variable at every position it computes an interval/constant, then answers the two questions a token stream cannot.

```
resolved branches: 1
  L3   always taken  jump 5 strictEqual r null    (cond = 1)
provably null: L3 r is null
```

| output | meaning | how to use it |
|---|---|---|
| `always taken` / `never taken` | both sides of the condition are constants, so the branch is fixed | either it's a mistake or a deliberate dead branch — go look |
| `... is null` | when this statement executes, the variable is definitely null | `===` can tell, `==` cannot (see below) |
| `?` | unknown (external input, `rand`/`noise`) | normal, don't treat it as a bug |

**Two language facts you must know first**:

- **An unassigned variable is the number `0`, not null** (`numval = 0` in `new LVar`). So **`equal x null` ⇔ `x.num() == 0`**, and for an `x` that was never assigned it always holds; **only `strictEqual` (`===`) distinguishes null from 0** (`ConditionOp.java:31-40`: objects are compared as objects only when both sides are objects, otherwise as numbers). On seeing `jump ... equal var null`, first suspect that `===` was what it meant.
- **NaN / ±Infinity are silently turned into null** (the `invalid()` check in `LVar.setnum`). This is exactly why a bit-stripping loop can exit: `op logn x 2` on `x=0` gives `-Infinity` → null → `=== null` holds.

**Calibration (whole corpus, 2396 blocks, simulator excluded, 39 ms/block)**: 4.1% of blocks have a signal, on average 0.120 branches / 0.060 provable nulls; 0 non-converged. Sampling checked by hand, all conclusions held.

**What it cannot prove**:
- Every external input is `⊤` — values from `sensor`/`getlink`/`ulocate` all count as "unknown", so **it is only valid for pure computation chains**
- Once the same variable is reassigned 3 times it loses precision to `⊤` (widen), and inside a deep loop it turns back into `?`
- It doesn't cross processors, and doesn't judge "is the value computed correctly" (that is a human's job)

## The cross-processor mode of `values`

Only `--msch` gives it cross-processor knowledge: it first runs `cross` to get the value of every slot, then re-runs carrying that table (**one iteration only**, no fixed point). A lone `.mlog` has no companion, and `read` stays ⊤. When the blueprint is incomplete (the other processor wasn't saved along with it), a reported null may just mean it wasn't saved.

| **How the corpus writes it** — naming/shape/cycle cost | `mlog.py style <keyword...>` |

## `cross` looks only across processors, not at memory cells

`read`/`write` have two completely different uses; don't mix them up:

- `read x cell1 "slot"` — a **memory cell**, and what is inside the quotes is the **address variable name**. Extremely common (82 of my library's files have it).
- `read x processor1 "name"` — **a variable of another processor**, and what is inside the quotes is the **variable name** inside that processor.
  Rare: of the 625 files in my library only **9** actually point at a processor, and of the 926 in 彩末包 only 13.

The readable slot is simply **the target's own variable** (so `set` is enough; `write` is not required), which is also
why "it must first be declared over there". `cross` computes the join (all of the target's own assignments, all external `write`s)
and reports it in four classes: `never assigned` / `always null` / `constant` / `written, never read`.

A self-link (`processor1` at offset 0,0) is legal and reads its own variables.

**Version**: reading and writing another processor / a message block by name only exists in **v7 (build 146)**; a v6 `read`
can only access a memory cell by numeric index ⇒ a blueprint that uses it to read/write a processor won't run on v6 (`cross` carries a
`note : ... v7 (build 146) feature` hint).

**The reporting baseline is build 146** (the first stable v7.0 release): statements that already exist in the baseline are not reported, only newer ones. The criterion is `floor > 146`, not `>= 147`.

## What `pack` looks at, and what it doesn't

`mlog.py pack` recognises the idiom of **packing several fields into one number** (`data = status*1e8 + outputID*1e6 + inputMask`), then computes **how many ids the low field can hold**.

```
    `data`  (first seen L2)
      1e8  ->  status   (= data / 1e8)   at L2
      1e6  ->  outputID (= data / 1e6)   at L3
      1e6  ->  mask     (= data % 1e6)   at L4
      low field `1e6` holds 0..999999  =>  20 usable bit positions (ids 0..19)
      !! 22 items exist but only 20 fit: ids 20..21 overflow into the next field
         (raise the separator, e.g. 1e6 -> 1e7)
      note: `outputID` also contains 100x `status`; a correct decode must first
            assert `status == 0`
```

| output | meaning |
|---|---|
| `1e8 -> status` | what this layer peels off is `status` |
| `N usable bit positions` | the low field can represent `0..10^N-1`; `(10**N-1).bit_length()` is how many ids fit |
| `!! ... only 20 fit` | **a real bug**: vanilla has 22 items, and `fissile-matter` (20) and `dormant-cyst` (21) don't fit |
| `note: ... must first assert X == 0` | `op idiv` does not mask the high bits; the value out of `idiv` still contains higher bits ⇒ you must first assert the high bits are 0 |
| `ok: ... subtract-mask` | first `op mul hi 1eN`, then `op sub` to take the high bits off — **decoding is correct, no warning** |

**It is the only place in the whole toolset that can directly give the conclusion "this code has a bug"**, at the price of a very low hit rate: **only 3 of the 2420 blocks in the whole corpus (0.1%)** use this idiom. So it is **not a linter**: sweep the entire corpus with it and you will see almost nothing, but once it hits, what it gives is a concrete capacity number, not "there might be a problem here".

**Boundaries**: it only recognises `op idiv|mod <dst> <src> 10**exp`, and a pack site requires **at least two different exponents** on the same `src`; it does not rebuild expressions; a separator below `10^3` doesn't count; mask detection is whole-program text matching (no data flow), so a same-shaped `mul`+`sub` elsewhere can let a real miss pass silently.

## "Undefined variable" needs five tiers before you decide whether to change it

When the static check reports "`X` is read here but is never assigned anywhere", **don't change anything yet**. The mlog scene has a whole set of idioms carried by the variable list alone, which no specification can measure. Measured distribution over the 926-blueprint bundle (tiering brought A down from 883 entries to 77):

| tier | meaning | count | change it? |
|---|---|---:|---|
| **A, a real error** | where the name is read, the value really changes behaviour | 77 | **yes** |
| B, always-true guard | both sides of the `jump` are constants ⇒ the branch is fixed | 55 | usually not |
| C, inert parameter | the name lands on a parameter position the instruction **never reads** | 944 | no |
| D, dead reference | it looks like a link name, but this processor doesn't have that link | 788 | **yes** (it fails silently) |
| E, signature | it exists only to show up in the editor's variable list | 5540 | no |

- **E, signature**: the editor's variable list shows every variable the program uses, so writing your own name as a variable is a signature — `print by:NOSB(hghg`, `set Madeby mineqwwe`, `jump 21 equal colour ender`, `control config Carrot 0914 0 0 0`. Reported as **INFO**.
- **C, inert parameter**: when a statement is longer than the number of positions the instruction actually reads, the extra tokens are inert. `control` has only three effective positions (type/target/p1, p2–p4 are ignored by every block); `ucontrol` is counted via `semantic_uses`, and `flag`/`payTake` have only one semantic parameter; the third position of a unary `op` is always dropped (`b` in `op rand g 255 b`).
- **D, dead reference**: `scatter1` looks like a valid link, but it isn't in the processor's link table — `LExecutor`'s `validLink(b)` blocks it outright, so `control shootp scatter1` fires nothing, **without an error and without a crash**. Only `.msch` can be checked (`.mlog` has no link table).
- **`true`/`false` are constants, not ordinary variables**: `GlobalVars.java:54-55` registers them as 1 / 0 via `putEntry`, and `LAssembler.var()` checks `logicVars` before it gets to `putVar` ⇒ `jump T equal X true` is `X == 1`. **I once looked only at `var()` and concluded the two were unassigned variables, conjuring 653 false warnings out of nothing** — judging a built-in means checking "what is registered", not "how the parser function handles it".

`set // 装载电池组` (a variable name that is pure punctuation) is part of this set of idioms too: mlog only has `#` for comments (`LParser.java:98-99`), so writing it this way makes the comment visible in the variable list — it goes in the `annotation` tier or is skipped altogether.

`noop` gets an entry of its own: **judged ERR**. It is `LStatements.InvalidStatement` (`LStatements.java:48-59`), and `build()` returns a `NoopI` that does nothing — the game substitutes it for **a statement it could not parse**. So seeing `noop` means "there used to be a statement here, and it's gone": the most common cause is **logic written on a newer version being opened on an older one**, so statements the old parser doesn't know get dropped. Such a program **is basically dead** — what got dropped is exactly the one doing the work, and the `jump`s after it still point at the wrong place. (In a very few cases it is only a blank-line placeholder; that's the exception: report it as an error so a human takes a look.)

The tier A entries that really need changing: `op mod n n padNeedCount` (modulus 0 ⇒ null), `ubind u` where `u` was never assigned, `control config unloader1 mmm 0 0 0`, `flase` misspelled onto `ulocate`'s enemy position.

**Note the difference between inert positions and inner positions**: tokens **outside** the parameter slots are not read (`b` in `op rand g 255 b`, `x` in `jump T always x false`); but a signature written **inside** the parameter slots (`by`/`bicker` in `control enabled reactor enable 0 by bicker`) really is read by the game — it is only because `control`'s p2–p4 are meaningless to the block that it is still judged C.

## How to hunt infinite loops

`check` reports only the provable kind: a back edge that always holds, with nothing in the loop that could make it false.

- **The `@this` guard**: `@this` can only be claimed by `ubind` (`LExecutor.java:325`/`:329`, the only two places in the whole tree that write `controller`). So
  `jump loop strictEqual ctrl @this` + `ubind @flare` in the body ⇒ true from the first pass on ⇒ **ERR, everything after it is dead code**;
  `jump loop notEqual ctrl @this` + the same `ubind` ⇒ false from the first pass on ⇒ the loop ends after one pass, which is the standard idiom and is **not reported**.
- **Spins waiting on external state** (`jump loop equal on 0`, where `on` comes from `read cell1`) are not reported: the real corpus has 0.33 per block, and reporting them would only drown the conclusion.
- Simulation cannot replace it either: reproducing the previous item requires first constructing a scene where "the unit has already been claimed by this processor", and when the scene can't be fed in, the simulator will say everything is fine.

## Virus logic (self-replication)

```powershell
python mlog.py check someone.msch --msch      # 命中会打 [INFO] virus-logic
```

The criterion is a single line: `ucontrol build <x> <y> <block> <rotation> @this` — the last parameter is the new block's config,
and passing `@this` means "build a block that runs this program of mine", so it copies itself, and the copies copy again. The scene calls it
**virus logic**. `@this` passed through a variable (`set cfg @this`) counts as well.

Measured: in 1,421 saves, 9,151 processors are viruses, but they come from **only 2 different programs** (`556.msav` has 6,616
copies, `538.msav` 1,432). Seeing thousands of processors on one map, suspect this first; don't rush to call it a "logic computer".

## Reading the logic in a whole save: `mlog.py map`

```bash
python tools/mlog.py map "C:/Users/<you>/AppData/Roaming/Mindustry/saves/430.msav"
python tools/mlog.py map <save.msav> --verbose --show 0   # 连干净的一起列，只报汇总
python tools/mlog.py map <save.msav> --code 3            # 每块再打前 3 行源码
```

It supports the three tile layouts after build 146 (save versions 7–9 shortchunk, 10–13 modern);
saves from version 6 and older are not supported, and it says so plainly with `legacy layout`.

- One line per processor: coordinates, block type, statement count, link count, and `check`'s conclusion.
- Link names come from the link table in the save, so warnings such as "this link doesn't exist" are just as reliable in whole-map context.
- Big saves are slow (`235.msav`: 613 processors, 560k statements): start with `--show 0` for the summary.

### Whole-corpus health check (1421 saves)

`mlog.py map` reads one file at a time. To look at **all** saves, deduplicate by source hash first and then run the static check
(`tools/corpus/_sweep_analyse.py`): 1421 saves, 103,787 processors, and after deduplication only
**4,366 different programs** (95.8% are copies of the same code) — so every ratio in the report has "different programs" as its denominator,
not "processors".

### Programs in a save have no name

`mlog` has no name field (only blueprints have `name`/`description`); the only name in a save is the map name. Judging the purpose relies on three signals:
**link names** (block name + index by default), **the instruction histogram** (`draw`=display / `ubind`=units / `control config`=logistics / `setrule`=world rules),
**the strings in the code** (the one or two chunks of text `print`ed out for a human). The ready-made bucketing by these three is in `out/saves_programs.md`.

## Running the corpus in bulk (in parallel)

```powershell
python tools\corpus\_sweep_saves.py              # 1,421 个存档：34 秒
python tools\corpus\_sweep_analyse.py            # 加六种分析：127 秒
python mindustry-blueprint\tools\parallel.py --items 1421   # 先看它会开几个 worker、为什么
```

`parallel.py` works out the worker count itself: it takes the minimum of three caps — core count, available memory, and **the largest file**. Heavy files
(≥1 MB) get a segment of their own with fewer workers — one 4.5 MB save holds 6,600 processors, and splitting workers by the average
would let several such files drain memory at the same time. To tune it, use `--workers N` or `--serial`.

## Thorium-reactor (钍反) protection: three facts

| fact | number | source |
|---|---|---|
| with coolant, `@heat` is always 0 | cleared within one tick, steady state 1.2 liquid/s | `NuclearReactor.java:95-125` |
| `control enabled 0` is not firefighting | even after stopping it takes 1200 ticks (20 s) to fall from 0.999 to 0 | same, ambient cooling |
| full load explodes in 100 ticks | heat gain 0.01/tick, and `@heat >= 0.999` means `kill()` | same |
| a link name cannot prove the type | `reactor1` may be a thorium reactor or an impact reactor, and `@heat` means opposite things on the two; only `sensor x reactor1 @type` proving the type justifies WARN, otherwise it reports INFO as a question | corrected by the user's own test on 2026-10-18 |
| the impact reactor's `@heat` is warmup | output = `warmup^5`: stuck at 0.5 gives only 3.1%, 0.9 gives 59%, 0.99 gives 95%; full output takes ~6908 ticks (115 s), and it **never explodes from heat** | `ImpactReactor.java:117-120` |

The correctness of protection logic is judged not by the threshold but by **the check interval**: at full load you must look again within `(0.999 - threshold)/0.01` ticks,
where the interval = statements in the loop body ÷ the processor's ipt. `mlog.py check` reports `reactor guard is too slow`.

## Who says what the semantics are: cross-validation against a second implementation

Every "language fact" in this repo comes from reading `LExecutor.java`. Reading source can go wrong, so a few key ones were
additionally checked against the processor simulator of [`cardillan/mindcode`](https://github.com/cardillan/mindcode)
(eight probes: six agree, one is unsupported, one is a blueprint-level addition).

| conclusion | status |
|---|---|
| `equal <unassigned> null` always true · `logn(0,2)`→null · `1/0`→null · `sensor @unit @dead`→1 · `print <undeclared>`→`null` · unwritten memory cell→0 | **confirmed by both implementations** |
| `read`/`write` only see variables the other side has **declared**, and `write` to an undeclared name creates no slot | **confirmed by both implementations** (blueprint-level probe `A=7 B=null C=null`) |
| after `ubind`, `@controller == @this` | measured on the real executor (v159.3 / v160.7, `mlogsim`; the mindcode simulator doesn't support `ubind`) |

The re-run method and the probe files are in `EMULATOR-CROSSCHECK.md` (needs JDK 22 and `mindcode.jar`). You don't need mindcode day to day: `tools/mlogsim.py` is the real executor itself, and `out/probes/p1..p8` have been re-run and pass on both v159.3 and v160.7; `tests/run_tests.py` is 36 goldens and doesn't depend on Java.

## The standalone copy

The same toolset is already packaged as the standalone mlog-agentskill skill (.dsh/skills/mlog-agentskill/); the directory carries every module and all the data, and can be copied away as a whole. For a one-shot full analysis use mlogagent.py report <file>; after changing a module, refresh that copy with python tools/sync_mlogagent.py (--check only compares).

## Run the tests after changing an analyzer

```bash
python tests/run_tests.py          # 36 條 golden digest，任何結論變化都會失敗
python tests/run_tests.py -v       # 逐條列出
python tests/run_tests.py --write  # 改了就有意識地改期望值——然後讀 diff
```

The digest is **the conclusion with the wording stripped** (`(severity, line)` pairs, statement counts, branch verdicts, capacity digits…),
so the prose can change freely, but the moment a conclusion changes it goes red. `mlog.py selftest` only proves the parser loses nothing
(429/429 round-trip); the correctness of these five analyzers is caught by this suite.

## Environment requirements (read this before sharing with anyone)

**Only Python 3.10+ and the standard library are required.** The dev machine is 3.12.14; every script uses only `argparse base64 collections dataclasses glob hashlib json math os pathlib re shutil struct sys textwrap urllib zlib` — no numpy, no pandas, nothing that needs `pip install`.

Two things that can be taken away independently:

| what you take | size | can it be used on its own |
|---|---|---|
| `.dsh/skills/mlog-agentskill/` | 16 files included + `MANIFEST.sha256` | **yes**. Copy it anywhere and run `python tools/mlogagent.py report x.msch`; `info --verify` self-checks |
| `mindustry-blueprint/` | tools + data + docs | yes, but the two paths below must be changed for your own machine |

### Two paths

- **The game's schematic directory**: defaults to `%APPDATA%\Mindustry\schematics` (i.e. `~/AppData/Roaming/Mindustry/schematics`). If it lives elsewhere, set the `MLOG_CORPUS` environment variable, or pass `--corpus` to `find`.
  Only `selftest` / `find` / the `corpus` family of scripts use it; `parse` `check` `ir` `values` `pack` `cross` `explain` `unit` `block` `item` `gen` **need no game directory at all**.
- **The Mindustry source directory**: `./Mindustry-Source` (git-ignored, about 8 MB). Only the scripts that "regenerate the data tables from source" need it: `block_ids_from_source.py`, `block_sizes.py`, `items_from_source.py`, `units_from_source.py`, `blocks_from_source.py`, `check_ops.py`.
  **Day-to-day use needs it not at all** — all eight tables ship with the package (`block_ids.json` / `block_sizes.json` / `cmd_index.json` / `item_ids.json` / `instr_semantics.json` / `unit_attrs.json` / `block_attrs.json` / `label_rules.json`).

### Version and platform

- The data tables come from **Mindustry v159.3 (git `5811844`)**. To refresh the tables after a game update, clone the source again and re-run those generator scripts (each script's header comment says which file it reads).
- **The path defaults are written for Windows**. On Linux/macOS just point `MLOG_CORPUS` at `~/.local/share/Mindustry/schematics` or `~/Library/Application Support/Mindustry/schematics`.
- **The console must be UTF-8**: `chcp 65001` (or set `PYTHONIOENCODING=utf-8`). Otherwise Chinese variable names and icon glyphs show up as mojibake — that is the terminal decoding as GBK, **the file itself is fine**.
- **Not needed**: Java, Mindustry itself, the network. The only script that goes online is `fetch_wiki_ids.py` (a one-off fetch of the wiki's block ID table; the result is already in the repo).

### Making the skill take effect in "all projects"

DSH has no "scope of a single skill" switch; the scope **is simply the directory it sits in**:

| location | who can see it |
|---|---|
| `<repo>/.dsh/skills/mlog-agentskill/` | only this repo (this repo is both the source and an example of this usage) |
| `$DSH_HOME/skills/mlog-agentskill/` | **all projects**. On this machine `C:/Users/<you>/.dsh/skills` is a junction pointing at `.dsh-pack/skills/default`, so writing there is the same as installing it as a built-in skill |

One command installs it at user level, then verifies it file by file:

```bash
python tools/sync_mlogagent.py --global          # 装 / 刷新
python tools/sync_mlogagent.py --check --global  # 只核对,不同步就 exit 1
```

It writes to a directory outside the repo and needs filesystem permission; keeping the global copy and the repo copy consistent is this script's job, so don't copy by hand.

### Rules and row-by-row audit (`rules/` + `review.py`)

One command runs the whole audit:

```bash
python tools/review.py run --pages 2      # 抓 30 张图 -> 分析 -> 写 out/audit_review.md
# 在编辑器里给每条的 `判定:` 后面填 ok / bad / unsure / skip，可加 `备注:`
python tools/review.py ingest && python tools/review.py stats
```

- `run` = `fetch` + `build` + `md`; `--pages 0` only analyses images already on disk, and `--serial` is for slow machines.
- **Before rewriting the list it reads back the verdicts filled into the previous md**, so you can run `run`/`md` repeatedly and the verdicts won't be lost.
- Only `build` (a rescan) changes row ids; when that happens, `ingest` first and then `build`, otherwise the old verdicts won't match the new ids.


Every "this line is a problem" the analyzer says should trace back to a rule **with evidence and a counter-example**;
and every rule should be judgeable by one person as "right / wrong / don't know".

```bash
python tools/rule_capture.py list            # 39 条规则，带实测命中数
python tools/rule_capture.py lint -v         # schema + 反例必须不命中
python tools/rule_audit.py --dir out/maps    # 按规则统计噪声 → out/rule_audit_maps.md
python tools/review.py build --dir out/maps  # 压成可判的行 → out/audit_rows.json
python tools/review.py list --unjudged       # 还没判的
python tools/review.py show <id>             # 该行上下文（>>>> 标出）
python tools/review.py bad <id> --note "为什么"
python tools/review.py stats                 # 每条规则你判了几条、错了几条
python tools/review.py export                # out/audit.md，分组表格
python tools/review.py md --unjudged         # out/audit_review.md：源码 + `判定:` 空位，在编辑器里逐条判
python tools/review.py ingest                # 把 md 里填的 ok/bad/unsure/skip 读回 out/verdicts.csv

**判的载体是 markdown，不是游戏里。** `md` 把每条发现摊成：出处、处理器自己的链接名、
带语句序号的源码（`>>>>` 标出被指那一条）、以及一行空的 `判定:`。要判「链接名指错了」
不需要打开地图 —— 链接名就列在那一条里；要判「这行是不是白算」也不需要，源码就在下面。
填完 `ingest` 读回来，`stats` 按规则算准确率。`--window N` 控制每条上下各给几行。
```

- **kind**: `semantics` (this is how the game is; auto-downgrade forbidden) / `heuristic` (statistical, downgradable) / `negative` (looks wrong but is right, used to block a rule you were about to write).
- **A one-way ratchet**: a downgrade (WARN→INFO) can be proposed by the machine; an upgrade always needs a human to nod.
- There are only four verdicts: `ok` / `bad` / `unsure` / `skip`. Once `bad` piles up, it means the rule should be deleted or narrowed.


## Reference data

| file | contents |
|---|---|
| `tools/wiki_block_ids.json` | 422 vanilla blocks → content ID |
| `tools/block_sizes.json` | 446 block sizes (derived from source) |
| `tools/cmd_index.json` | format/parameters/gotchas of 86 mlog instructions |
| [REFERENCE.md](REFERENCE.md) | the complete knowledge base: numbering systems, mechanics, traps, overturned old conclusions |
| [PATTERNS.md](PATTERNS.md) | logic pattern library + blueprint engineering analysis |

## Key facts at a glance

- **A blueprint stores mlog plain-text source**, so no decompilation is needed
- **The content ID is a "construction order number"**: vanilla blocks are constructed first and mods append after ⇒ **a mod does not shift vanilla block IDs**
- **A blueprint stores no content ID**, and the game **resolves by block name** at load time ⇒ placing vanilla blocks only needs the right name
- **`@dead` also returns 1 for a `null` target** ⇒ it doubles as a "unit doesn't exist" test
- **`sensor`'s null is contagious** ⇒ when the target is null, every property returns null
- **`sensor`'s third argument can be a variable** (holding a content object is enough) ⇒ `sensor n core it` is legal, but mlog **has no primitive to fetch content by index**
- **Storing objects in a memory cell is only supported in build 160+** ⇒ on older versions `write @copper cell1 0` actually writes 1
- **A link name = the last segment of the internal name split on `-`, plus an index** ⇒ `overdrive-dome` → `dome1`
- **The effective per-tick budget = `@ipt × @timescale`** ⇒ looking at `@ipt` alone halves the throughput after a speed change (`sensor $ @this @timescale` gets the multiplier)
- **Writing `@counter` takes effect at the "next" position** ⇒ after `op add @counter @counter n` the entry point is **line n+1**
- **An out-of-range `@counter` is undefined behaviour** (N<0 / N≥line count / non-integer) ⇒ a dispatch table must clamp it itself; don't expect the game to catch you
- **A statement that fails to parse becomes `noop` as a whole line** (the editor shows Invalid), not "one parameter ignored" ⇒ the whole line is dead, not part of it
- **`jump` to a nonexistent label = jump -1 = does nothing** (`get(location, -1)` in `LParser` + `if(address != -1)` in `JumpI`) ⇒ `check` reports `no-target-jump`; don't take it for "dead code"
- **The logic limit is 1000 lines; `1e4` is legal, `1.2e3` is not; a variable name may be nearly anything except whitespace and `"` `#` `;`** ⇒ a generator writing by C identifier rules will cut names wrong and emit numbers the game can't parse
- **`idiv` rounds down, `mod` is truncated remainder, `emod` is floor-mod** ⇒ the three are not interchangeable; the identity `a == (a idiv b) * b + (a emod b)` holds only under emod (`LogicOp.java:12-14`)
- **`emod` and `ushr` are new in v150** ⇒ the version gate must look at **the operator name**; `op emod` reports `>=150` rather than the baseline 146
- **Any `ucontrol` command (except `unbind`/`within`) claims the unit for this processor** ⇒ after `sensor c @unit @controller` immediately followed by `ucontrol move …`, `c` equals `@this` at once; to measure distance only without claiming, compute it by hand with `op len`
- **Editor display names and text names are mismatched**: `not` is shown as `flip`, `notEqual` is shown as `not` (`LogicOp.java:32`) ⇒ writing into mlog a name you read off the editor gives you a different operator
- **`@counter`'s meaning is "the line number that will execute after the current one"** ⇒ use `op add ret @counter 1` for a function return address, and after a dispatch table writes `op add @counter @counter n` the entry is at line n+1
- **A gap of more than 10 seconds between control commands drops the control state** ⇒ in a long loop, send at least one `ucontrol` every 10 seconds
- **`ucontrol move x y` is 4 fields** — the statement object has 6 slots and `LExecutor` unconditionally converts `p1..p3`, but `move` reads only `x,y` (`approach` is the one that reads the third as a radius), same for `pathfind`; don't count parameters by the `0 0 0` the editor pads in
- **One extra operand on a unary operator is not an error** — the extra token in `op floor a b`, `op sin y angle 90` is discarded by `LParser` with no run-time effect and counts only as INFO; but `op sin` takes radians, and writing `90` usually means the author thought it was degrees
