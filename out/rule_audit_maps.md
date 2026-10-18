# 规则噪声审计（maps）

- 存档 20（失败 0）、发现 1285 条，其中 1285 条落在 25 条规则里、0 条未归类

`precision` = 命中里源码行仍匹配该规则自己 `line_regex` 的比例。100% 只代表「规则和它的说法一致」，**不代表结论正确**。

| 规则 | 种类 | 级别 | 命中 | 程序 | 占比 | precision | 自动? |
|---|---|---:|---:|---:|---:|---:|---|
| `unary-op-extra-operand` | heuristic | INFO | 673 | 13 | 52.4% | 100% |  |
| `version-gate` | semantics | INFO | 243 | 15 | 18.9% | 100% |  |
| `undefined-var-is-not-automatically-an-error` | semantics | INFO | 119 | 10 | 9.3% | 100% |  |
| `jump-to-jump-chain` | heuristic | INFO | 115 | 5 | 8.9% | 100% |  |
| `link-name-not-bound` | semantics | WARN | 106 | 7 | 8.2% | 100% |  |
| `constant-null-guard` | heuristic | WARN | 14 | 2 | 1.1% | 100% |  |
| `dead-polarity` | semantics | SUSPECT | 14 | 6 | 1.1% | 100% |  |
| `printflush-clears-buffer` | semantics | INFO | 1 | 1 | 0.1% | 100% |  |
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
| `undefined-var-read` | semantics | ERR | 0 | 0 | 0.0% | — |  |
| `unknown-op` | semantics | ERR | 0 | 0 | 0.0% | — |  |
| `virus-logic` | semantics | INFO | 0 | 0 | 0.0% | — |  |

## 每条的样本

### `unary-op-extra-operand` — 673 条  ← 占了一半以上，先怀疑它
- `mindustrytop-25774.msav:125,137 L71  op sqrt endl.set n.pad 1`
- `mindustrytop-25774.msav:125,137 L76  op rand pad.instruct pad.volum n.pad`
- `mindustrytop-25773.msav:314,228 L24  op floor fx x b`

### `version-gate` — 243 条
- `mindustrytop-25774.msav:125,137 L0  `
- `mindustrytop-25774.msav:413,408 L0  `
- `mindustrytop-25773.msav:314,228 L0  `

### `undefined-var-is-not-automatically-an-error` — 119 条
- `mindustrytop-25559.msav:590,11 L5  status false unmoving @unit 0.1`
- `mindustrytop-25559.msav:591,11 L5  status false unmoving @unit 0.1`
- `mindustrytop-26053.msav:64,17 L32  sensor e b @surge-alloy`

### `jump-to-jump-chain` — 115 条
- `mindustrytop-25774.msav:6,493 L18  jump 21 always x false`
- `mindustrytop-25774.msav:7,493 L18  jump 21 always x false`
- `mindustrytop-24936.msav:0,118 L205  jump 209 always x false`

### `link-name-not-bound` — 106 条
- `mindustrytop-25774.msav:127,114 L0  sensor silicon vault1 @silicon`
- `mindustrytop-25774.msav:127,114 L1  sensor phase-fabric vault1 @phase-fabric`
- `mindustrytop-25559.msav:389,444 L18  sensor rx1 route1 @x`

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

