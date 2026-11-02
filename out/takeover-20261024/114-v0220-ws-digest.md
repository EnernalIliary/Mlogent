# 114 · v0.22.0 档3：工作区快照接进对话（只读工具）

日期：2026-11-02　用户：m04334「完成之后继续做档3」

## 1. 问题

档1（v0.21.0）把对话窗与工作区窗合成一个窗口，但两者仍然只是**同一个壳**：对话里的模型看不见工作区。
用户在对话里问「备料那个工作区的代码在干嘛」时，模型只能猜，或者要求用户把代码贴进来。
根因是数据边界：工作区落盘读写都在游戏侧（`main.js` 的 `wsAll()` / `wsLoad()`），侧车（`tools/logicd.py` + `tools/chats.py`）
是另一个进程，只认 `/chat` 请求体里的东西 —— 不下发，侧车就永远看不到。

## 2. 方案（只读）

- **每轮下发快照**：`chatSend()` 组请求体时把 `wsDigest()` 一起塞进 `req.workspaces`，并附 `req.map = wsMapName()`。
  不是只在第一轮发 —— 工作区会改名、会新增处理器，每轮重发才跟得上（代价是每轮多几十 KB）。
- **裁剪与预算**（`wsDigestOf(all, map, budget)`）：
  - 每个工作区最多 40 台处理器（`WS_PROCS_MAX`），每段代码最多 6000 字符（`WS_CODE_MAX`），备注 500（`WS_NOTE_MAX`），
    工作区最多 40 个（`WS_MAX`），作业只留最近 12 条（倒序后返回）；
  - 总代码预算 120000 字符：按顺序累加，超预算的那段代码置 `''` 但**仍保留这台处理器的坐标/方阵/描述**，
    这样模型至少知道「那里有一台，代码太长没发过来」，而不是以为那里是空的。
- **侧车只读工具**（`tools/chats.py`）：
  - `ws_list()`：`共 N 个工作区：` + 每个 `- id=… · 状态 · N 台 · 地图` 一行；
  - `ws_get(id 或名字)`：按 id 精确 → 名字精确 → 包含 的顺序找，逐台渲染 `1) @x,y 方阵 —— 描述` + 代码（缩进 3 空格）；
  - `ws_search(q)`：在名字、备注、代码行里搜，最多 20 处，回 `工作区「X」@x,y 第 N 行：…`；
  - 没有快照时明确回「玩家这一轮没有提供工作区快照…不要编工作区」，避免模型凭空捏造；
  - **没有任何写工具**：写回仍由玩家在工作区窗里点「写入」（`wsWrite`），系统提示词写明「只能看、不能改」。
- **界面自证**：`chatRefreshDetailBody()` 在「工具 N 次 · 轮次 M」后追加「助手能看到 N 个工作区（ws_list / ws_get / ws_search，只读）」，
  没有快照时整行不出现 —— 用户一眼能看出这一轮模型到底有没有数据。

## 3. 改法（文件 / 函数）

| 文件 | 改动 |
| --- | --- |
| `MlogAuxiliary/scripts/main.js` | 新增 `wsDigestOf(all, map, budget)`（:5532）与 `wsDigest()`（:5568）；`chatSend()`（:4829 附近）加 `req.workspaces`/`req.map`；`chatRefreshDetailBody()`（:5081）加快照提示行；新增 `api.maiWsDigestProbe`（:8349） |
| `tools/chats.py` | 常量 `WS_MAX=40`/`WS_PROCS_MAX=40`/`WS_CODE_MAX=6000`/`WS_NOTE_MAX=500`；`_cut()`/`_int()`/`_ws_norm()`；`_CTX = threading.local()` 在 `_run_loop` 里装当轮快照；TOOLS 末尾加 `ws_list`/`ws_get`/`ws_search`；`_ws_ctx()`/`_ws_state_cn()`/`_ws_line()`/`_ws_list()`/`_ws_find()`/`_ws_get()`/`_ws_search()`；`_run_tool` 三个分支；SYSTEM_PROMPT 两行；`start()` 收 `workspaces`/`map` 并记 `ws_at` |
| `tests/logicd/run_logicd_tests.py` | `_ChatStub` 改成可配置（`tool`/`args`/`reply`）；`test_chats()` 新增第 8 节：切到 `ws_get` stub → 带快照发一轮 → 断言 tool 消息含 `@12,34` 与 `jump 0 always`、名字是 `ws_get`、`chat['ws']==2`/`ws_map=='区域'`、系统提示词与 tools 列表都提到 `ws_list`；再发一轮不带快照断言旧快照仍在 |
| `tests/mlogauxiliary/run_ui_smoke.py` | 打印 `MAIWSDIGEST:`（两处前缀白名单同步）、断言 `MAIWSDIGEST:ok`；v0.22.0 红线 5 条：`function wsDigestOf(` / `req.workspaces = wsDigest()` / `req.map = wsMapName()` / `api.maiWsDigestProbe` / `个工作区（ws_list / ws_get / ws_search，只读）` |

## 4. 验证

- `python -X utf8 tests/logicd/run_logicd_tests.py --no-sim` → **chats: 11 check(s) passed**（原 9 + 新增 2），8 个 test 全绿，`logicd OK (protocol only)`。
- `python -X utf8 tests/mlogauxiliary/run_ui_smoke.py` → exit 0，新增行 `MAIWSDIGEST:ok ws=2 procs=1+1 clipped=0 kept=10`
  （预算 12 ⇒ 第二个工作区代码被清空 `clipped=0`，坐标 3 仍在；预算 120000 ⇒ 保留 `kept=10`）。
- `node --check MlogAuxiliary\scripts\main.js` → exit 0；`python -X utf8 -m py_compile` 对两个测试文件 exit 0。
- 真机验：`[mai] chat geom:` 与对话面板那行「助手能看到 N 个工作区」要在重启游戏后看（本轮只能确认装机 OK）。

## 5. 留给真机验的

1. 重启游戏后打开「MAI 逻辑助手 → 对话」，左栏随便选一段对话，右栏底部应出现「助手能看到 N 个工作区（…）」；N 与实际工作区数一致。
2. 在对话里问「我最新的工作区里有几台处理器、代码在干什么」，模型应当答得出坐标与代码片段（而不是让你贴代码）。
3. 让模型「把某台处理器的代码改成 X」——它只能描述改法（没有写工具），不会谎称已写入。
4. 若模型说「没有工作区快照」，看 `saves\last_log.txt` 里有没有 `[mai] chat …` 报错，并确认窗口是从「逻辑助手」打开的（老入口也一样）。

## 6. 收尾

版本三处 0.22.0：`MlogAuxiliary/scripts/main.js` 的 `MOD_VERSION`、`MlogAuxiliary/mod.hjson` 的 `version`、`tools/logicd.py` 的 `SIDECAR_VERSION`。
文档：CHANGELOG `## 0.22.0`、`docs/Mlog辅助-规划.md` 版本表 v0.22.0 行、`docs/断言表.md` 追加 **L2-115**（跨进程数据必须裁剪并给预算）与 **L2-116**（只读通道必须只读且系统提示词明说），
口径改 **175 条**（L1 31 / L2 116 / L3 6 / L4 4 / S 18）；报告即本文件；`00-HANDOVER.md` 追加 §113。

**收尾数字（2026-11-03 00:12）**

- 门禁 `python -X utf8 gate.py --full --kb-build` → **17/17 passed in 84.9s**（`out\_gate_v220.log`，kb 覆盖 169 源文件）。
- 打包 `python -X utf8 tools\package.py` → `out/_dist/MAI-0.22.0/` **191 files / 19,442,952 B**；
  `MAI-0.22.0-mod.zip` 8,724,379 B / 182 files，sha256 `210E24E1C1B2355FB53B2A8E414800EAC5634FFC70E29EF8FF31537D709FD9A2`；
  `MAI-0.22.0.zip` 8,746,968 B，sha256 `3B5AF07770226F17CB26742915B2D418048EB3265F93D8ED21F2079BA4056EC0`。
- 装机 `[ok] MAI 0.22.0 installed` → `E:\Program Files (x86)\Steam\steamapps\common\Mindustry\saves\mods\MlogAuxiliary`，
  旧副本备份 `saves\mod-backups\MlogAuxiliary-20261103-001246`；装机目录 `mod.hjson` = `version: "0.22.0"`，
  `main.js` 里 `wsDigestOf|maiWsDigestProbe|req.workspaces` 共 6 处。装机时游戏没在跑 ⇒ 下次启动即生效。
- 本地提交 **f1216fc**「v0.22.0：工作区快照接进对话（只读 ws_list / ws_get / ws_search）」（11 files / +560 −13）。
- 公开仓 `out\_v220_pub.py`（拷 234 文件进 `out\_publish\mai-clone`）→ 克隆里 `tests/run_tests.py` 48/48、`tests/packaging` 13 checks 0 problem
  （logicd 与 ui smoke 因克隆里没有 v160 jar 而 SKIP）→ 提交 **7e4175b** "v0.22.0: let the assistant read the workspace snapshot" + tag v0.22.0；
  push：`git -C out\_publish\mai-clone push origin main` / `push origin refs/tags/v0.22.0`（**这次直连 443 通、本机 10808 代理没在监听**，不加 `-c http.proxy` 均 rc=0）。
- Release `python -X utf8 out\_v220_release.py` → 代理尝试被拒（WinError 10061）后自动退回直连：POST 201 + 两个资产 201，
  `releases/latest` = v0.22.0 → https://github.com/EnernalIliary/MAI-MlogAuxiIliary/releases/tag/v0.22.0
