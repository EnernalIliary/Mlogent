# 规则噪声审计（maps）

- 存档 20（失败 0）、发现 584 条，其中 584 条落在 27 条规则里、0 条未归类

`precision` = 命中里源码行仍匹配该规则自己 `line_regex` 的比例。100% 只代表「规则和它的说法一致」，**不代表结论正确**。

| 规则 | 种类 | 级别 | 命中 | 程序 | 占比 | precision | 自动? |
|---|---|---:|---:|---:|---:|---:|---|
| `version-gate` | semantics | INFO | 216 | 11 | 37.0% | 100% |  |
| `jump-to-jump-chain` | heuristic | INFO | 115 | 5 | 19.7% | 100% |  |
| `link-name-not-bound` | semantics | WARN | 106 | 7 | 18.2% | 100% |  |
| `undefined-var-is-not-automatically-an-error` | semantics | INFO | 82 | 10 | 14.0% | 100% |  |
| `status-name-needs-at` | semantics | INFO | 36 | 5 | 6.2% | 100% |  |
| `constant-null-guard` | heuristic | WARN | 14 | 2 | 2.4% | 100% |  |
| `dead-polarity` | semantics | SUSPECT | 14 | 6 | 2.4% | 100% |  |
| `printflush-clears-buffer` | semantics | INFO | 1 | 1 | 0.2% | 100% |  |
| `arity-is-not-effective-params` | semantics | INFO | 0 | 0 | 0.0% | — |  |
| `bool-param-constantly-zero` | heuristic | WARN | 0 | 0 | 0.0% | — |  |
| `cross-processor-slot-undeclared` | semantics | WARN | 0 | 0 | 0.0% | — |  |
| `impact-reactor-cap-is-not-protection` | semantics | WARN | 0 | 0 | 0.0% | — |  |
| `jump-target-out-of-range` | semantics | ERR | 0 | 0 | 0.0% | — |  |
| `noop-means-version-drift` | semantics | ERR | 0 | 0 | 0.0% | — |  |
| `reactor-guard-response-time` | heuristic | WARN | 0 | 0 | 0.0% | — |  |
| `reactor-link-name-proves-nothing` | semantics | INFO | 0 | 0 | 0.0% | — |  |
| `spin-deadlock` | semantics | ERR | 0 | 0 | 0.0% | — |  |
| `surplus-parameter-is-not-an-error` | semantics | WARN | 0 | 0 | 0.0% | — |  |
| `ubind-missing` | semantics | ERR | 0 | 0 | 0.0% | — |  |
| `ulocate-flag-invalid` | semantics | ERR | 0 | 0 | 0.0% | — |  |
| `unary-op-extra-operand` | heuristic | INFO | 0 | 0 | 0.0% | — |  |
| `undefined-var-read` | semantics | ERR | 0 | 0 | 0.0% | — |  |
| `unknown-op` | semantics | ERR | 0 | 0 | 0.0% | — |  |
| `virus-logic` | semantics | INFO | 0 | 0 | 0.0% | — |  |

## 每条的样本

### `version-gate` — 216 条
- `mindustrytop-25774.msav:125,137 L78  format total.transportation`
- `mindustrytop-25774.msav:413,408 L3  select control.conveyor greaterThan item.surge-alloy 250 true false`
- `mindustrytop-26075.msav:5,10 L6  format 当前波次`

### `jump-to-jump-chain` — 115 条
- `mindustrytop-25774.msav:6,493 L18  jump 21 always x false`
- `mindustrytop-25774.msav:7,493 L18  jump 21 always x false`
- `mindustrytop-24936.msav:0,118 L205  jump 209 always x false`

### `link-name-not-bound` — 106 条
- `mindustrytop-25774.msav:127,114 L0  sensor silicon vault1 @silicon`
- `mindustrytop-25774.msav:127,114 L1  sensor phase-fabric vault1 @phase-fabric`
- `mindustrytop-25559.msav:389,444 L18  sensor rx1 route1 @x`

### `undefined-var-is-not-automatically-an-error` — 82 条
- `mindustrytop-25559.msav:391,445 L1  op add result a b`
- `mindustrytop-25559.msav:391,445 L1  op add result a b`
- `mindustrytop-26053.msav:64,17 L32  sensor e b @surge-alloy`

### `status-name-needs-at` — 36 条
- `mindustrytop-25559.msav:590,11 L5  status false unmoving @unit 0.1`
- `mindustrytop-25559.msav:591,11 L5  status false unmoving @unit 0.1`
- `mindustrytop-24936.msav:7,72 L23  status false unmoving 建筑机 3`

### `constant-null-guard` — 14 条
- `mindustrytop-25774.msav:143,138 L9  jump 18 equal colour ender`
- `mindustrytop-25774.msav:143,138 L9  jump 18 equal colour ender`
- `mindustrytop-25680.msav:177,140 L30  jump -1 equal colour ender`

### `dead-polarity` — 14 条
- `mindustrytop-25774.msav:139,142 L1  jump 5 notEqual 单位存亡 1`
- `mindustrytop-25559.msav:351,272 L20  jump 18 notEqual dead 1`
- `mindustrytop-25559.msav:427,437 L130  jump 107 notEqual d 1`

### `printflush-clears-buffer` — 1 条
- `mindustrytop-25774.msav:125,137 L24  printflush Notification`

