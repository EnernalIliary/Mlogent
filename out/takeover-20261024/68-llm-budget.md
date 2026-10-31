# §68 logicd v0.12.3：推理模型把回复预算想光了（空回复 → 升档重试 + 诊断）

日期：2026-10-31。上一轮 §67（v0.12.2）把「同区域同描述重投必回放旧作业」拆掉之后，
玩家按提示重启了 sidecar 并重投同一句描述 —— 作业 id 确实变成了 `<首轮>-2`（修复生效），
但作业仍然 `rejected`，这次的 finding 把真凶写清楚了：**模型根本没写出 `content`，预算被思考吃光了**。

## 68.1 症状（真机截图 + 作业文件）

面板（模组版本仍是 v0.12.1，本轮没动模组）：

```
作业 f122e54f918974ff-2：被门禁拒绝（尝试 3 次，ERR 1 条）
  ERR L0 model endpoint answered with an empty message (
  refused after 3 attempt(s): the gate never saw a clean pro
```

`out/jobs/f122e54f918974ff-2.json`（1424 B）关键字段：

```
state: rejected          attempts: 3          code: ""
explanation: refused after 3 attempt(s): the gate never saw a clean program
findings[0].msg: model endpoint answered with an empty message (finish_reason=length;
                 message keys=content,reasoning_content,role;
                 usage={"completion_tokens": 1600, "prompt_tokens": 502})
retry_of: f122e54f918974ff      mode: new      ipt: 2
origin: {x: 296, y: 78}         links: [{name: message1, x: 297, y: 78}]
snapshot: build 160 / mod 0.12.1 / map "[#c0ceff]蓝图[#87ceeb]实验室1.58"
```

## 68.2 根因

`deepseek-flash` 是推理模型：回复里带 `reasoning_content`（思考）+ `content`（答案），
**两者共用 `max_tokens`**。`tools/mlogprovider.py:263` 的 `HttpProvider.__init__(..., max_tokens=1600)`
对普通模型够用，对推理模型则是：思考先把 1600 花完 → `finish_reason=length` → `content` 是空串。

证据是自洽的：prompt 只有 **502** token（不是 prompt 太大），completion 正好压在 **1600** 上限，
失败的三次尝试全是同一个形态。所以这不是「模型不会写 mlog」，也不是 vite 地址/密钥问题
（v0.12.1 的 `/llm/probe` 早前实测 200 + 12 字符真回复）。

## 68.3 改动（只动 sidecar，模组不变、不用重装）

`tools/mlogprovider.py`

- `DEFAULT_MAX_TOKENS = 4096`、`TOKENS_CEILING = 16000`。`max_tokens` 是**上限不是目标**，
  模型写完就停，放宽默认值不额外花钱 —— 花掉的那个数不会超过模型真想说的量。
- `HttpProvider.__call__` 拆成外层 + `_once(prompt, budget, timeout)`：首次用 `self.max_tokens`；
  若错误里出现 `finish_reason=length` 且还有升级空间，就 `bigger = min(ceiling, max_tokens * 4)`、
  `wider = min(600, max(timeout, 30) * 3)` 重试一次；仍然截断才报错。
- 新增 `_budget_hint(err, budget)`：错误文本里点名 `--llm-max-tokens`，并解释
  「预算被 reasoning_content 先花了」——上一版的错误只说 `finish_reason=length`，玩家看不出该改什么。
- `provider_from_args()` 把 `args.llm_max_tokens` 传下去。

`tools/logicd.py`

- `SIDECAR_VERSION = '0.12.3'`；`GET /health` 现在回 `{ok, protocol, version}`（`Handler.server_version` 同源）。
  这一条是给「改了代码却没重启进程」准备的：老进程照样回 200，过去只能靠比对进程启动时间才发现。
- `LLM_STATE` 增 `max_tokens`；`GET /llm` 回报；`POST /llm` 接受 `max_tokens`（64..64000，越界 400），
  并把它传给热替换出来的 `HttpProvider`；CLI 增 `--llm-max-tokens`。
- `POST /llm/probe` 的预算从 `128` 改成 `max(512, max_tokens // 4)`：128 对推理模型连一个 JSON 都写不完，
  自测会给出「端点可疑」的假阴性。

## 68.4 测试（`tests/logicd/run_logicd_tests.py`：`test_llm()` 8 → 11 项，`test_protocol()` 多一条）

假 OpenAI 端点（`_StubEndpoint`）现在记录每次请求的 body，并能按次数回 `finish_reason=length` + 空 content：

- ⑨ 预算生效 + 自动升档：`POST /llm {max_tokens: 800}` → 第一次截断、第二次成功 → 作业 `done`，
  端点收到的两次预算是 `[800, 3200]`。
- ⑩ 一直截断：错误同时含 `finish_reason=length` 与 `--llm-max-tokens`，阶梯 `[500, 2000]`。
- ⑪ `GET /llm` 回 `max_tokens == 800`；`POST /llm {max_tokens: 10}` → 400。
- `test_provider()` 里默认值断言从 `== 1600` 改成 `== DEFAULT_MAX_TOKENS >= 4096`。
- `test_protocol()` 断言 `/health.version` 是 `x.y.z` 形状。

## 68.5 复跑

```
python -X utf8 tests/logicd/run_logicd_tests.py --no-sim
  protocol: 26 check(s) passed
  jobs: 15 check(s) passed
  provider: 11 check(s) passed
  llm: 11 check(s) passed
  logicd OK (protocol only)
```

## 68.6 真机复测（需要玩家做，两分钟）

1. 关掉旧 sidecar：`Get-CimInstance Win32_Process -Filter "Name='python.exe'"` 里命令行含 `logicd` 的那个
   → `Stop-Process -Id <pid> -Force`。
2. 重新起：`python tools/logicd.py`（或原样带 `--llm-url ... --llm-model deepseek-flash`）。
3. 开一次面板 —— 或者直接 `curl http://127.0.0.1:8765/health`，应该看到
   `{"ok": true, "protocol": 1, "version": "0.12.3"}`。看不到 version 就是还没换成新进程。
4. 同一台处理器、同一句「打印最近的玩家名称」再点一次「生成」：这次 id 会是 `f122e54f918974ff-3`
   （v0.12.2 的规则：终态作业不再占着内容 id），作业应该 `done`。

## 68.7 边界

- 真端点我这边仍未联调（本机没有 key，环境变量全空）——⑨⑩ 是假端点上的确定性验证，
  真模型那一步只能由玩家复测。若真机仍空回复，`GET /llm` 的 `max_tokens` 与 finding 里的
  `completion_tokens` 会直接告诉我们够不够，把 `--llm-max-tokens 8192` 传给 sidecar 即可。
- 模组版本仍是 0.12.1（`mod.hjson` / `main.js` 未动）；面板上看到的版本号不会变，这是有意的。

## 68.8 下一刀

①面板批量入口（P5 第三刀下半）②联机拒绝写入的「无权限」提示 ③冲突检测只比代码文本、不比链接表
④打包/安装即用（用户已定最后解决）。
