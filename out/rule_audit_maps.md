# 规则噪声审计（maps）

- 存档 20（失败 0）、发现 1626 条，其中 1626 条落在 25 条规则里、0 条未归类

`precision` = 命中里源码行仍匹配该规则自己 `line_regex` 的比例。100% 只代表「规则和它的说法一致」，**不代表结论正确**。

| 规则 | 种类 | 级别 | 命中 | 程序 | 占比 | precision | 自动? |
|---|---|---:|---:|---:|---:|---:|---|
| `unary-op-extra-operand` | heuristic | INFO | 673 | 13 | 41.4% | 100% |  |
| `jump-to-jump-chain` | heuristic | INFO | 456 | 17 | 28.0% | 100% |  |
| `version-gate` | semantics | INFO | 243 | 15 | 14.9% | 100% |  |
| `undefined-var-is-not-automatically-an-error` | semantics | INFO | 119 | 10 | 7.3% | 100% |  |
| `link-name-not-bound` | semantics | WARN | 106 | 7 | 6.5% | 100% |  |
| `constant-null-guard` | heuristic | WARN | 14 | 2 | 0.9% | 100% |  |
| `dead-polarity` | semantics | SUSPECT | 14 | 6 | 0.9% | 100% |  |
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

### `unary-op-extra-operand` — 673 条
- `mindustrytop-25774.msav:125,137 L72  op sqrt endl.set n.pad 1`
- `mindustrytop-25774.msav:125,137 L77  op rand pad.instruct pad.volum n.pad`
- `mindustrytop-25773.msav:314,228 L25  op floor fx x b`

### `jump-to-jump-chain` — 456 条
- `mindustrytop-25774.msav:343,102 L8  jump 13 equal temp.i temp.j`
- `mindustrytop-25774.msav:127,114 L4  jump 6 greaterThan silicon 70`
- `mindustrytop-25773.msav:314,228 L2  jump 6 notEqual arc1 null`

### `version-gate` — 243 条
- `mindustrytop-25774.msav:125,137 L0  `
- `mindustrytop-25774.msav:413,408 L0  `
- `mindustrytop-25773.msav:314,228 L0  `

### `undefined-var-is-not-automatically-an-error` — 119 条
- `mindustrytop-25559.msav:590,11 L6  status false unmoving @unit 0.1`
- `mindustrytop-25559.msav:591,11 L6  status false unmoving @unit 0.1`
- `mindustrytop-26053.msav:64,17 L33  sensor e b @surge-alloy`

### `link-name-not-bound` — 106 条
- `mindustrytop-25774.msav:127,114 L1  sensor silicon vault1 @silicon`
- `mindustrytop-25774.msav:127,114 L2  sensor phase-fabric vault1 @phase-fabric`
- `mindustrytop-25559.msav:389,444 L19  sensor rx1 route1 @x`

### `constant-null-guard` — 14 条
- `mindustrytop-25774.msav:143,138 L10  jump 18 equal colour ender`
- `mindustrytop-25774.msav:143,138 L10  jump 18 equal colour ender`
- `mindustrytop-25680.msav:177,140 L31  jump -1 equal colour ender`

### `dead-polarity` — 14 条
- `mindustrytop-25774.msav:139,142 L2  jump 5 notEqual 单位存亡 1`
- `mindustrytop-25559.msav:351,272 L21  jump 18 notEqual dead 1`
- `mindustrytop-25559.msav:427,437 L131  jump 107 notEqual d 1`

### `printflush-clears-buffer` — 1 条
- `mindustrytop-25774.msav:125,137 L25  printflush Notification`

