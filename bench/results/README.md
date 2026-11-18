# Onboarding benchmark — recorded runs

`runs.jsonl` is the ledger `python tools/benchmark.py score` reads. One JSON
object per attempt, appended by `python tools/benchmark.py record ...`. It is
committed on purpose: a success rate is worth quoting only if the row behind
it stays next to the tasks that produced it.

## What the columns mean

| column | meaning |
|---|---|
| `task` | id of the file in `bench/tasks/` |
| `success` | the acceptance check passed (`verify` returned ok) |
| `first_pass` | it passed on the agent's first submitted file, with no repair round |
| `tool_calls` | tool invocations the agent made on this task |
| `repairs` | write-and-retry rounds after the first submission |
| `interventions` | times a human had to step in (0 = unattended) |
| `tokens_in` / `tokens_out` | only when the harness reports usage; 0 means "not measured" |
| `seconds` | wall clock from dispatch to the report |
| `notes` | what the run actually did, in one line |

## First recorded batch — 2026-11-18

Six tasks, each given to a **fresh subagent** that saw only the task prompt
(`python tools/benchmark.py prompt <id>`). Subagents were told not to open
`bench/tasks/`, `tests/benchmark/answers/`, or run `verify` — those are the
grader, and reading them would make first-pass meaningless.

| task | first pass | repairs | tool calls | seconds |
|---|---|---|---|---|
| arithmetic-constants | yes | 0 | 6 | 49 |
| branch-on-comparison | yes | 0 | 2 | 49 |
| compute-average | yes | 0 | 4 | 35 |
| emit-a-text-report | **no** | 2 | 4 | 123 |
| repair-a-hanging-program | yes | 0 | 6 | 77 |
| repair-a-static-error | **no** | 3 | 5 | 158 |

`score` on this batch: success 6/6, first-pass 4/6 (0.67), mean repairs 0.83,
mean tool calls 4.5.

The two non-first-pass runs are the interesting ones, and both failed on a
*model of the machine*, not on syntax:

- `emit-a-text-report` — the agent first assumed the text buffer resets
  between ticks, then assumed `end` halts the program (it does not: `EndI`
  only moves `@counter` past the last instruction, so the next tick restarts
  at 0). It settled on `print` + a self-jump idle loop. Both mistakes are
  claims the knowledge base already states (`L1-14`, `L1-37`).
- `repair-a-static-error` — fixed `jump 99` to `jump 0` after trying seven
  candidates; the surviving `numeric-jump` INFO is an advisory, not an error.

## Caveats

- `tokens_in`/`tokens_out` are 0 for this batch: the subagent harness did not
  report usage, so `tokens_per_success` is not meaningful yet.
- Judging is on observable state, plus (since 2026-11-18) an optional
  `executed` check that reads the executor's per-instruction trace. That check
  is what makes "compute it, do not type it" testable: `set r 35` and
  `op add`+`op mul` both end at 35, only one of them executed arithmetic.
  It is a floor, not a proof -- a liar can run a real `op add` and overwrite
  the result -- so the numbers above still measure "reached the state", not
  "wrote the program we would have written".
- Six tasks is a smoke test of the harness, not a ranking. Add tasks before
  quoting these numbers as a model comparison.
