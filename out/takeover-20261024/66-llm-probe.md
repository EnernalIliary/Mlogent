# 66 · v0.12.1：模型档报错说人话（地址补全 / 端点自测 / 重启后自动重同步）

## 66.1 症状（两张玩家截图）

- 截图一：作业被门禁拒绝 3 次，唯一 finding 是
  `ERR L0 model endpoint unreachable: HTTP Error 404: Not Found`。
- 截图二：换了地址之后变成 `ERR L0 empty reply` 与
  `refused after 3 attempt(s): the gate never saw a clean pro…`。

两句都不指向原因。玩家问「这是正常的吗」——不正常，但也不是模组的逻辑错，是**模型档的
配置与诊断**两头都缺东西。

## 66.2 现场取证

`GET http://127.0.0.1:8765/llm` 当时回：

    {"ok": true, "kind": "llm", "url": "https://api.deepseek.com/v1",
     "model": "deepseek-flash", "key_set": true, "key_hint": "******9e2b", "timeout": 60}

**url 是 API base，不是 chat 端点**：`HttpProvider` 直接 POST 这个地址，端点回 404。
同一把 key 经 sidecar `POST /models` 是通的：

    {"ok": true, "url": "https://api.deepseek.com/v1/models",
     "models": ["deepseek-flash", "deepseek-v4-pro"], "count": 2}

⇒ 模型名合法、密钥合法，**纯粹是 URL 形状错**。

第二张截图的 `empty reply` 来自 `parse_reply()`：`not text.strip()` 时抛
`ProviderError("empty reply")`（tools/mlogprovider.py）。也就是说端点回了 HTTP 200、
`choices[0].message.content` 是空的——典型是推理模型把 `max_tokens`（当时 900）
全花在 reasoning 上，或者代理换了一条路径。

第三个发现（当时没人报，但会反复咬人）：**sidecar 的模型档配置只在进程内存里**，
重启后 `GET /llm` 回到 `kind: template`，玩家明明设置过却静悄悄退回模板档，
看到的就是「找不到样板」那类报错。

## 66.3 改动

### sidecar（tools/logicd.py）

- 新增 `completion_url(url)`：以 `/chat/completions`、`/completions`、
  `/responses` 结尾原样放行，否则 `rstrip('/') + '/chat/completions'`；
  空串抛 `ValueError('model url is empty')`。`apply_llm()` 与
  `probe_model()` 都走它。
- 新增 `probe_model(req)` 与路由 `POST /llm/probe`：一次最小 chat 调用
  （`temperature 0`、`max_tokens 128`、要求只回 `{"ok": true}`），
  回 `{ok, url, model, status, error, raw, raw_len, finish_reason, content, content_len,
  message_keys, reasoning_len, usage}`；`HTTPError` 单独捕获并带回 body 前 1200 字符。

### provider（tools/mlogprovider.py）

- `max_tokens` 默认 **900 → 1600**。
- `__call__` 新增 `except urllib.error.HTTPError`（在 `URLError` 之前）：
  `model endpoint refused: HTTP <code> <reason>`；404 追加
  `(a 404 usually means the url is the API base, not the full chat endpoint -- <url>/chat/completions)`
  并附 body 前 300 字符。
- 空 content 不再只报 `empty reply`：先试 `_alt_text(doc)`（`reasoning_content` /
  `reasoning` 里的 JSON 兜底），否则
  `model endpoint answered with an empty message` + `_why_blank(doc)`。
- 新 helper `_alt_text(doc)`、`_why_blank(doc)`（拼 `finish_reason=…`、
  `message keys=…`、`usage={prompt_tokens, completion_tokens}`、`error=…`），
  `parse_reply` 抛错时也拼上。

### 模组（MlogAuxiliary/scripts/main.js）

- `MOD_VERSION` → 0.12.1（4 空格缩进）。
- 设置页「大模型」按钮行 3 → 4 个：获取模型 / **测试端点** / 启用模型档 / 回到模板档。
- 新增 `llmProbe()`：`POST /llm/probe`，把 地址 / HTTP 状态 / finish_reason /
  回复长度 / 「只回了 reasoning」/ 回复或原文 摊在 `llmNote` 里。
- 新增 `llmSync(cb)`：`GET /llm`，若 `kind !== 'llm'` 或模型名不一致，就把
  `Core.settings` 里的三件套 `POST /llm` 推回去（日志
  `llm tier re-synced from settings: <url>`）。载入时与每次 `showAiPanel()` 都调。
- `llmEnable()` 成功后比对一次端点模型列表，模型名不在列表里就当场提示。
- 说明文案改成「只填到 /v1 也行…sidecar 重启会忘记模型档，模组下次开面板会自动重新同步」。

## 66.4 测试

- `tests/logicd/run_logicd_tests.py`：`test_llm` 6 → **8**（base url 归一、
  满 URL 不被改写、`/llm/probe` 打到 stub 并带回回复原文）；`test_provider` 9 → **11**
  （`max_tokens == 1600`、空回复必须带 `finish_reason=length`、404 必须带
  `/chat/completions` 提示）。stub 加 `blank` / `strict` 两个开关。
- `tests/mlogauxiliary/run_ui_smoke.py`：v0.12.1 源码红线三条
  （`function llmSync(`、`function llmProbe(`、`"/llm/probe"`）。
- 实测：protocol 26 / jobs 12 / provider 11 / llm 8，EXIT=0；ui smoke EXIT=0，
  `MAIDIAG:版本：0.12.1`、`MAISELF:…填了 103 行/格`、`MAILLM:ok 82`。

### 一个假失败，别误判

同一命令连挂两次（`FAIL jobs: job <id> never reached ('done',) (last state 'running')`），
但把 `test_jobs()` 单独 import 跑是 12 项全过、自建 sidecar 探针三路（done / rejected×3 /
zero-link rejected）也都对。第三次跑全绿。判为环境性偶发，与 §63 记录的「并行满载假超时」同类。
排查提示：`jobqueue._run` 里 `self._materialize(...)` 没有 try/except，若真的挂起，
去 sidecar 子进程 stdout 里找 traceback。

## 66.5 复跑与交付

- `python -X utf8 tools/kb.py build` → 见 handover §66 记录。
- `python -X utf8 gate.py --full` → 16/16。
- zip 重打 + 装机（main.js 与 mod.hjson 都改了，必须重打）。
- 玩家侧要做的：重启游戏（加载 v0.12.1）；设置页点一次「测试端点」看端点到底回什么；
  模型档配置现在会自动重同步，不必每次重启 sidecar 后手动重填。

## 66.6 边界与下一刀

- 模组裸 Socket 只有明文 HTTP，模型列表与自测必须经 sidecar（https 由 Python 侧发）。
- 自动重同步只有一个方向（模组 → sidecar）；命令行 `--llm-*` 仍会被游戏设置覆盖。
- 冲突检测只比代码文本，不比链接表（旧候选，仍在）。
- 面板批量入口（P5 第三刀下半）、联机无权限提示、打包安装即用（用户已定「最后解决」）仍未做。
