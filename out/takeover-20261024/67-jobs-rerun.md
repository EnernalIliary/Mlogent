# 67 路 v0.12.2：重投不再回放旧结论（sidecar 侧，模组未变）

## 67.1 症状

`out/jobs/` 里最近三条作业全部 `rejected`、`attempts: 3`，唯一 finding 是
`ERR L0 provider-error: empty reply`（03:01:56 / 03:05:24 / 03:07:52，`snapshot.mod` 都已经是 `0.12.1`）。
`POST /llm/probe` 之后确认端点、密钥、模型名都是好的（`finish_reason: stop`、`content_len: 12`），
所以「修好了再点一次生成」本该成功——但玩家原地重投，拿回来的还是那条 `empty reply`。

## 67.2 根因：内容寻址的 id 被已终态的作业粘住

- `tools/jobqueue.py:67` `job_id()` = `sha1(json.dumps({'snapshot','desc','mode'}, sort_keys=True))[:16]`。
- `tools/jobqueue.py:212` `enqueue()`：`old = self.jobs.get(job['id']); if old is not None: return dict(old), False`。
- 模组侧 `MlogAuxiliary/scripts/main.js:1638` `jobBody()` 送的快照由 `main.js:2104` `regionSnapshot()` 生成，
  字段是 `{schema, mod, build, map, world, bounds, cells, truncated, grid, processors[]}`——**没有时间戳、没有 nonce**。

于是「同一台处理器 + 同一句话」永远是同一个 id，而 `enqueue()` 把同 id 一律当幂等：
一条死在 `provider-error: empty reply` 的作业替这句话把 id 永久占住了，模型再也不会被问第二次。
用 `out/jobs/af91a583e578f39b.json` 里的 snapshot 本地重算 sha1，得到的正是 `af91a583e578f39b`，
链就闭合了。

玩家视角：`renderJob()` 对 rejected/failed/cancelled **不重建按钮**，所以「生成」还在，
点下去 0.1 秒就回同一个结论——看起来像「修了没用」。这正是上一轮 §66 之后玩家问的那句「这是正常的吗。」的延续。

## 67.3 改动（只改 sidecar）

**`tools/jobqueue.py`**

- 新增 `RETRY_MAX = 99`（一份内容 id 最多顺延到 `<id>-99`，再往后加随机尾巴）。
- 新增 `Queue._free_id(base)`：从 `base` 开始找，`self.jobs` 里**没有**这个 id → 用它；
  有但**还在飞**（queued/running）→ 幂等，回旧作业（这就是 §4.2 那条「同 body 二次提交是 no-op」的本意）；
  有但**已终态** → 换 `<base>-2`、`<base>-3`… 继续找。`enqueue()` 改用它，顺延时写 `retry_of = base`，
  失败那次照样留在盘上可对比。
- 同版修掉两处写盘薄弱点（§66 里被记成「环境性偶发」的那次 `FAIL jobs: … last state 'running'` 的真因）：
  - `Store.save()` 的 `os.replace` 在 Windows/OneDrive 目录下会撞 `PermissionError: [WinError 5]`
    （`tools/jobqueue.py:177`，同步引擎/扫描器/读者短暂占住目标文件）。异常被 `_loop` 的
    `except Exception: traceback.print_exc()` 吞掉之后，作业**永久停在 running**。
    现在 save 对这类冲突重试 `SAVE_TRIES = 6` 次（`SAVE_WAIT = 0.03` 递增退避，
    `_contended()` 只认 `PermissionError` / WinError 5·32·33，`_replace()` 留出测试注入口），
    临时文件名加上 pid + 线程 id 以免同 id 并发写互相踩；用尽仍失败则清理 tmp 再抛。
  - `_loop()` 兜底新增 `_strand(jid, exc)`：未预期的异常 → `failed` + `worker-error` finding + 原因文本
    （已经是终态的作业不覆盖）。面板上「不动」和「还在跑」玩家分不出来，这个必须落成终态。

**`tests/logicd/run_logicd_tests.py`**（`test_jobs()` 12 → 15 项）

- 终态后重投：`id == <首轮>-2`、`retry_of == 首轮`、`wait_job(... ('done',))`、`attempts == 1`、`<id>-2.json` 落盘。
- 在飞时仍幂等：desc 用 `'慢一点'`（只含 `'慢'`，FakeProvider 取最长 key；`'慢一点（好）'` 会误中 `'好'`
  拿到不 sleep 的干净代码，会假通过）。
- 撞车重试：`_replace` 前两次抛 `PermissionError(5, …)`、第 3 次放行 → save 成功、文件可读、`tries == 3`。
- 卡死兜底：`Store.save` 在 `state == 'running'` 时抛一次 `FileNotFoundError(2, …)` → 作业必须 `failed`、
  findings 含 `worker-error`、盘上也是 `failed`，且 worker traceback 里确实是那个 `FileNotFoundError`。
  worker 的 stderr 用 `contextlib.redirect_stderr(io.StringIO())` 收走，否则 gate 把 stderr 当失败。

**文档**

- `docs/断言表.md`：L2-41 幂等语义改写、L2-44 计数 12→15，新增 L2-49（终态不占内容 id）与
  L2-50（撞车重试 + 卡死落 failed），表头判定计数脚注补「按表内编号实数 109 条」。
- `docs/Mlog辅助-规划.md`：§4.2 的 `POST /jobs` 行改写 + 一段「幂等只对『在飞』成立（v0.12.2）」，
  `test_jobs()` 12→15（两处），§9 表加一行。
- `tools/README.md`：jobqueue 段改写幂等语义，加「为什么要拆掉一律幂等」与「同版修的两处写盘薄弱点」两段。

## 67.4 验证

    python -X utf8 tests/logicd/run_logicd_tests.py --no-sim
    protocol: 26 check(s) passed / jobs: 15 check(s) passed / provider: 11 / llm: 8   EXIT=0

    python -X utf8 gate.py --kb-build      -> 11/11 passed in 102.5s
    python -X utf8 gate.py --full          -> 16/16 passed in 70.1s

`tools/sync_mlogagent.py --mirror all --check` 报三处副本 in sync：`jobqueue.py` / `logicd.py` /
`mlogprovider.py` 本来就不在 21 个 payload 文件里（sidecar 不进 skill 副本），所以这次不需要同步。

### 67.4.1 用那条真卡住的作业跑一遍（离线，走完整代码路径）

`out/_verify_rerun.py`：把 `out/jobs/` 整份拷到私有 jobs-dir，起一份自己的 sidecar
（`--jobs-provider fake --fake-provider`，不联网），然后把 `af91a583e578f39b.json` 里**原封不动的 body**
（同一个 snapshot、同一句「打印最近的玩家名称」）重新 POST 一次：

    stored job: af91a583e578f39b rejected attempts 3 findings [('ERR','provider-error','empty reply')]
    POST /jobs -> 200 id af91a583e578f39b-2 created True retry_of af91a583e578f39b
    final state: done attempts 1 code 'print "rerun-ok"\nend' lines 2
    file on disk: True
    second re-send -> 200 id af91a583e578f39b-3 retry_of af91a583e578f39b
    RESULT: PASS

这就是玩家那条「怎么修都没反应」的作业：v0.12.2 之前它会一秒回到 `empty reply`，现在真的重跑了一遍并被写入。
玩家侧只要**重启 sidecar**（模组不用重装），再点一次「生成」就会得到新作业 `<id>-2`。

## 67.5 诊断教训（省下一轮）

`tests/logicd/run_logicd_tests.py:72` 起的 sidecar 用 `stderr=subprocess.STDOUT`，
**ready 行之后就没有人再读那条 pipe 了**——worker 线程的 traceback 全躺在 pipe 缓冲里，
所以「作业卡在 running」在测试输出里看不到任何原因（表现就是 60 s 超时后一句
`last state 'running'`）。要看它，就按同样参数单独起一份 sidecar 并开线程持续 drain stdout；
本轮就是这么拿到 `PermissionError: [WinError 5] … queue2\6071609d6bfae4c4.json.tmp -> …json` 那行的。

## 67.6 边界

- 模组没动（`MlogAuxiliary/mod.hjson` 仍 `0.12.1`，`main.js` 未改）——游戏安装目录至今没定位、
  重装成本高，而服务端就足以让「再点一次生成」产生新作业。玩家只要重启 sidecar。
- `<id>-N` 上限 99；`retry_of` 只指首轮，不链式（`<id>-2` 的 `retry_of` 是 `<id>`，不是 `<id>-1`）。
- 写盘重试只对「文件刚被占了一下」这一类语义生效；目录不存在、权限真不足第一次就抛。
- `_strand()` 是最佳努力：如果磁盘持续拒写，没有地方能落下这个结论。

## 67.7 下一刀

①面板批量入口（P5 第三刀下半：`writeMany` 已经在 v0.12.0 里了，缺「一次给多台投作业 + 汇总预览」）
②联机拒绝写入的「无权限」提示 ③冲突检测只比代码文本、不比链接表 ④打包/安装即用（用户已明确最后解决）。
