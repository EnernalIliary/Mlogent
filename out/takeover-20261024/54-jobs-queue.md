# 54 · P4 第一刀：作业队列 + 写入门禁

日期 2026-10-30。对应规划 `docs/Mlog辅助-规划.md` §4（P4）与 §9 实施状态表。**这一刀不接模型**。

## 1. 为什么先做队列而不是先接模型

规划 §4 的 P4 是「一句话 → 后台生成 → 游戏内拿回代码」三段：队列 / 模型 / 门禁。
最容易被忽略、也最容易把后面两步带歪的是**中间那份状态**：谁在跑、跑到第几次、失败了算谁的。
如果先接模型，调试时无法区分「模型输出差」和「作业丢了/重复跑了/重启后卡在 running」。
所以第一刀只做队列 + 状态机 + 门禁，模型留成一个 `provider` 函数（默认实现就是已有的 `/plan` 意图路由，
所以整条链路**离线可跑、不需要任何 API key**）。

## 2. 契约与状态机（`tools/jobqueue.py`）

job 结构照规划 §4.1，落盘 `<jobs-dir>/<id>.json`：

```
{id: sha1(snapshot+desc+mode)[:16], created, state, mode: new|edit, desc, snapshot,
 links[], ipt, origin, attempts, findings[], code, explanation, assumptions[], template, params, bytes_b64}
```

状态 `queued → running → done|rejected|failed|cancelled`，要点：

- **每次跃迁先落盘再报状态**（`tmp + flush + fsync + os.replace`），不是「跑完才写」。
- **重启可续**：`Queue.__init__` 读目录，残留的 `running` 一律改回 `queued`（`attempts` 保留，不白送一次），
  `resumed` 计数给测试断言用。sidecar 崩了/被 kill 不会留下永远 running 的僵尸作业。
- **幂等**：`POST /jobs` 同 body 二次提交返回同一个 id 且 `created: false`（id 是内容哈希，天然幂等）。
- **取消**：`DELETE /jobs?id=` 置 `cancel_requested`（`queued` 直接 `cancelled`），worker 在每次尝试前后检查点退出。
- 三个端点：`POST /jobs`、`GET /jobs?id=|?state=`（不带 `state` 只回未完成的）、`DELETE /jobs?id=`。

## 3. 门禁比分析器严一档

`mlogcheck` 对 `link-name-not-bound`（代码里用了 `container9` 这种形似链接名、但处理器没有该链接）只给 **WARN**——
这是对的：人写代码时线还没接完是常态。但作业是**机器输出直接写进处理器**，留一个不存在的链接名等于交付一个坏程序。
所以：

```python
FATAL_RIDS = ('link-name-not-bound',)
```

`gate()` 把这一条的 `sev` 提升为 `ERR`、加 `fatal=True`，并让 `ok=False`。
最多 3 次尝试（1 + 2 次 self-repair，第二次起把上一轮的 findings 当提示回给 provider）；
仍不过 → `rejected`，且 **`code` 恒为空串**——被拒的作业绝不留下可写入的代码。

这条提升有单测兜底：`jobqueue.gate('sensor x container9 @copper\nend', ['container1'])` 必须 `ok False` 且 fatal 里 `sev=ERR`。

## 4. provider 是唯一接模型的缝

```python
Queue(store, provider=...)   # provider(job, hint) -> {'code': ...} | {'template': ..., 'params': ...} | {'error': ...}
```

- 默认 `template_provider`：调 `logicd.plan({'intent': desc, ...})`，命中六模板之一就走锚定档（`compose`）。
- `FakeProvider`：表按描述子串**最长匹配**（否则「先坏后修好」会被「好」抢走）；值可以是 list（按尝试次数依次消费 = self-repair 用例），
  也可以是带 `sleep` 的 dict（= 取消用例的时间窗）。CLI `--jobs-provider fake --fake-provider FILE`。
- 于是「真模型」这件事被压缩成**换一个函数**，队列/门禁/双写全都不用动。

## 5. 验收

`tests/logicd/run_logicd_tests.py` 新增 `test_jobs()`，9 项，**不需要 JRE、不需要模型**：

| # | 断言 |
|---|---|
| 1 | 干净代码 → `done`、attempts 1、`code`+`bytes_b64` 非空、`<qdir>/<id>.json` 已落盘 |
| 2 | 同 body 二次 POST → 幂等，同 id，`created: false` |
| 3 | 幻觉链接 `container9` → `rejected`、attempts 3、findings 含 `link-name-not-bound` 且 `sev=ERR`、`code == ""` |
| 4 | 先坏后好（list 值）→ attempts 2 → `done` |
| 5 | 慢任务 running 时 DELETE → `cancelled` |
| 6 | 列表/负控：`?state=done` count≥2；`GET /jobs` 不含终止态；未知 id 404；`?state=bogus` 400；空 desc 400 |
| 7 | 默认 provider 模板档：「容器里铜够 100 就打印」→ `template=item-threshold` 且代码含 `sensor`/`container1` |
| 8 | 重启续跑：手写 `state=running, attempts=1` → `Queue` 后 `resumed==1`、状态 `queued`、`drain()` 后 `done` |
| 9 | `jobqueue.gate()` 单测把 `link-name-not-bound` 提升为 ERR |

复跑：

```
python -X utf8 tests/logicd/run_logicd_tests.py --no-sim
# protocol: 25 check(s) passed / jobs: 9 check(s) passed / logicd OK (protocol only)

python -X utf8 tests/logicd/run_logicd_tests.py
# protocol: 25 / jobs: 9 / write path: 7 template(s) accepted by the game / logicd OK
```

### 诚实缺口

1. 游戏内还没有 1 s 轮询 `GET /jobs` 与「完成提示」的 UI（= P4 第二刀）。
2. 真 provider 与规划 §4.4 的三段 prompt 未接。
3. 自由档的 `cost` + sim 200 tick 复检未接（现在锚定/自由两档都只过静态分析）。
4. 队列是单 worker 串行（够用：一次只会有一个人框一句话），没有优先级与并发上限。

断言表新增 L2-41；验证记录新增同日一节；规划 §4 末尾加「实际落地（P4 第一刀）」。
