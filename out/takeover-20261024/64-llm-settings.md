# 64 · v0.11.0：设置页里填模型地址 / 密钥 / 模型，点一下就换档

日期：2026-10-31　提交：见 git log　改动：`tools/logicd.py`、`tools/jobqueue.py`、`MlogAuxiliary/scripts/main.js`、
`MlogAuxiliary/mod.hjson`、`tests/logicd/run_logicd_tests.py`、`tests/mlogauxiliary/run_ui_smoke.py`、四份文档。

## 64.1 症状

模型档（`--jobs-provider llm`）从 v0.8.1 起就在，但**只有命令行能开**。玩家在游戏里遇到
「no template matched」时无从知道还有模型档，更没地方填端点；改命令行还得重启 sidecar。
用户要求（逐字）：「先允许玩家在设置内填入链接地址，API密钥，模型名称（允许自动获取）参考DSH。」

## 64.2 sidecar：三个端点 + 密钥只进不出 + provider 热替换

- `LLM_STATE = {kind, url, model, key, timeout}` 是进程内的唯一真源；`jobs_queue().provider` 就是它的投影。
- `GET /llm` → `{ok, kind, url, model, key_set, key_hint, timeout}`；`_mask_key()` 只留末 4 位（`******1234`），
  **明文 key 不出现在任何响应、日志里**（测试专门断言 `sk-secret` 不在 `json.dumps(doc)` 里）。
- `POST /llm`：`{url, model, key, timeout}` 切模型档（url 必须 http(s)、timeout 5–600，否则 400）；
  `{kind: "template"}` 切回离线模板档（`jobqueue.template_provider`）。切档是**换一个可调用对象**，
  不重建队列、不重启进程；已在跑的作业用换档前的 provider 跑完。
- `POST /models`：从 chat url 推导 models url（`/chat/completions`、`/completions`、`/responses` → `/models`；
  已是 `/models` 原样；否则拼 `/models`），GET 带 `Authorization: Bearer`，解析 `data[].id|name` 或 `models[]`，
  排序去重。HTTPError / URLError / 非 JSON 三种失败都翻成人话（`model list refused: HTTP 401 Unauthorized` 等）。
- 命令行参数照旧可用：启动时把 `--jobs-provider/--llm-url/--llm-model/--llm-key-env/--llm-timeout` 灌进 `LLM_STATE`，
  游戏里再改以游戏里为准（重启 sidecar 回命令行值）。
- `template_provider()` 的报错追加一句中文：当前是模板档，去 设置 → Mlog辅助 → 大模型 填地址/密钥/模型再点「启用模型档」。

## 64.3 模组：设置页新增「大模型」段

- 三行输入（地址 / 密钥 / 模型）存 `Core.settings`（`mlogauxiliary-llm-url|-key|-model`），密钥行 `setPasswordMode(true)`。
- 三个按钮：「获取模型」（`POST /models` 代取列表 → `showPickList()` 可滚动点选）、「启用模型档」（`POST /llm`）、
  「回到模板档」（`POST /llm {kind: template}`）。
- **为什么模型列表必须由 sidecar 代取**：模组传输层是裸 `java.net.Socket` 手写的 HTTP/1.1，只有明文 HTTP，
  没有 TLS（v0.4.4 起就是这条，见报告 42 附近的 transport 节）。https 端点只能在 Python 侧打。
- 诊断多一行「大模型：模型档 · <地址> · <模型> · 密钥 已填 ******1234」；面板与日志里永远只有尾巴。
- 控制台 `maiLlmProbe()`：存三件套 → 断言文本含模型名、不含 `sk-probe`/`9999`、含「还没提交给 sidecar」→ 原样恢复。

## 64.4 测试

- `tests/logicd/run_logicd_tests.py` 新增 `_StubEndpoint`（线程 HTTP 服务，`/v1/models` 回两条、`/v1/chat/completions`
  回一段干净代码）与 `test_llm()` 6 项：启动态模板档且无 key 字段；`/models` 的 URL 推导 + Bearer 透传；
  `/llm` 换档只回尾巴；`GET /llm` 保持 url/timeout；**真作业经 stub 模型走到 done**；`ftp://` → 400 且 `{kind: template}` 能回去。
- `tests/mlogauxiliary/run_ui_smoke.py` 新增 `MAILLM:ok`（真引擎里跑 `maiLlmProbe()`）+ 五条源码红线。
- **本轮抓到一个真 flake**：首跑 gate 时 `llm` 项报 `the queue never called the model endpoint`，单独跑却过。
  根因不是并发——`job id = sha1(snapshot + desc + mode)`，`test_llm()` 用的 desc 是固定字符串、jobs 目录又是默认的
  `out/jobs`，于是**上一次运行留下的 done 作业被幂等命中**（`created: false`），provider 根本没被调用，
  代码是上一轮 stub 留下的 `set n 0`，前面几项检查全过、只在「stub 见过 chat 端点」这条炸掉。
  修法两条：测试改用私有 `--jobs-dir`（`tempfile.mkdtemp`），desc 带上 `stub.port` 保证唯一。

## 64.5 复跑与打包

- `python -X utf8 tests/logicd/run_logicd_tests.py --no-sim` → protocol 26 / jobs 12 / provider 9 / **llm 6**，EXIT=0。
- `python -X utf8 tests/mlogauxiliary/run_ui_smoke.py` → EXIT=0；`MAILLM:ok 82`、`MAIDIAG:版本：0.11.0`、
  `MAISELF:设置表格可建，填了 102 行/格`（v0.10.1 时是 70 行）。
- `python -X utf8 tools/kb.py build` → `{chunks: 6460, files: 65}`。
- `python -X utf8 gate.py --full` → **16/16 passed in 46.3s**（首跑 15/16 是上面那个 flake，修完复跑全绿）。
- zip `out/_dist/MlogAuxiliary.zip` **71,363 B sha256 28EE9764CD91068E3CA86F8F2E23C076B3B8ABF53BEBB91DAF487D6651C69DD5**
  （main.js 137,172 B / README 53,950 / mod.hjson 2,389 / quickcheck 8,486 / rules.generated 6,463），
  已覆盖安装到 `E:/Program Files (x86)/Steam/steamapps/common/Mindustry/saves/mods/MlogAuxiliary` 5 文件逐字节 OK。
- 装机后必须重启 sidecar（老进程不认识 `/llm`、`/models`），否则面板报「投递失败 / no such endpoint」。

## 64.6 边界与下一刀

- 模型好坏模组不判断；换档只影响之后的作业。
- 密钥明文存在游戏存档目录的 `settings.json`（和原版所有设置一样），共享机器上别填。
- 面板不显示 key 明文，但也**不提供「清除密钥」**——下一刀可加一个「清空密钥」按钮（`POST /llm {key: ""}` 已支持）。
- 模型列表最多显示 80 条（`showPickList` 的上限），大供应商没问题，自建网关上千模型时会截断——可加搜索框。
- P5 剩余（多处理器事务写入）仍未开始。
