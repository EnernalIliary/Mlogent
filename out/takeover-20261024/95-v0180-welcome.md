# 95 · v0.18.0 首次启动向导

日期：2026-11-01
范围：`MlogAuxiliary/scripts/main.js`、`MlogAuxiliary/mod.hjson`、`MlogAuxiliary/README.md`、
`tools/logicd.py`、`tests/mlogauxiliary/run_ui_smoke.py`、`docs/断言表.md`、`docs/Mlog辅助-规划.md`、`CHANGELOG.md`

## 1. 需求（用户 m10072 原话）

> 第一次启动时候弹出欢迎和快速配置页面，并在验证sidecar可允许，模型配置完成之后重启。

「可允许」按「可用」理解。拆成三件必须成立的事：

1. 只在**第一次**启动弹一次；
2. 页内能**验证 sidecar 可用**；
3. 页内能**把模型配置完**，然后**重启**。

## 2. 实现

### 2.1 首次判定与标记

`WELCOME_KEY = "mlogauxiliary-welcome-done"`，写 `Core.settings`。

- `welcomeSeen()`：`Core.settings.getBool(key, false)`，**读不到就返回 true**（宁可少弹一次，也不能每局都弹）。
- `welcomeMarkSeen()`：弹过一次就写；点「稍后再说」也写。
- `welcomeTick()` 挂在 `Trigger.update`，条件：没标记、没有别的对话框（`Core.scene.hasDialog()`）、不在主菜单、
  `Vars.ui` 与 `Core.scene` 都在。任一条不满足就下一帧再试，绝不强插。

### 2.2 三步页面

`welcomeBuild(t, mk)` 是**纯布线**函数（真机的 `Dialog.cont` 和无头 `fakeTable` 共用同一份代码，
这样没 UI 也能自检）：

| 步 | 内容 | 判据 |
| --- | --- | --- |
| 1 | 状态行 `sidecarStateText()` + 「启动并检测后端」 | `ensureSidecar(false)` 之后 `GET /health` 回 `ok` 才显示「后端可用：vX · 端口 N」 |
| 2 | 地址 / 密钥 / 模型三个输入 + 「获取模型」「测试端点」「保存并启用」 | 先写 `Core.settings`，再 `POST /llm` 切模型档；`ok:true` 才提示下一步 |
| 3 | 说明 + 「完成（稍后自己重启）」「现在退出游戏」 | 退出走 `Core.app.exit()`；不给假的「原地热更」按钮 |

失败分支都落回同一条状态行：后端没起来显示 `sidecarStateText()` 与 `jobWhy()` 的原因；
模型取列表失败提示「也可以直接把模型名填进去」——第一次配置最常见的就是端点还没配好，不能只有一句失败。

### 2.3 入口

设置页「大模型」段新增 `buttonRow(t, ["首次配置向导"], [function(){ welcomeOpen(); }], mk)`，
随时可以重开；`welcomeOpen()` 打开时预填已存的地址/密钥/模型，地址空则预填 `LLM_DEFAULT_URL`。

## 3. 自检与测试

无头环境 `Vars.ui` 为 null，所以向导必须能在没有 Dialog 的情况下证明布线没坏：

- `api.maiWelcomeProbe()`：用 `fakeTable()` 跑 `welcomeBuild()`，返回
  `ok seen=no cells=N side=idle`（smoke 里打印成 `MAIWELCOME:ok seen=no …`）。
- `tests/mlogauxiliary/run_ui_smoke.py` 新增 v0.18.0 段：1 条探针断言 + 1 条「首次标记读回必须是 no」+
  8 条红线（`welcomeBuild` / `welcomeTick` / `WELCOME_KEY` / `welcomeMarkSeen` / `"/health"` /
  `kind: "llm"` / `Core.app.exit()` / 设置页入口）。

实测输出：

```
MAISELF:设置表格可建，填了 154 行/格；…；用到的方法 add,button,color,defaults,field,growX,height,image,labelWrap,left,margin,pad,padBottom,padRight,padTop,row,width
MAIWELCOME:ok seen=no cells=155 side=idle        # 探针（DBGJOINED welcome_ok=True seen_no=True 为一次性回显，已删）
EXIT=0
```

其余：`tests/run_tests.py` 46/46；`tests/logicd/run_logicd_tests.py` 全绿（protocol 26 / jobs 17 / provider 12 /
improve 8 / llm 12 / diag 7 / life 3 / write path 7）；`node --check` 0。

## 4. 断言表

新增 **L2-88**（三类判据：首次标记、三步各自可验、无头纯布线与 8 条红线），总数 146 → **147 条**
（L1 31 / L2 88 / L3 6 / L4 4 / S 18）。

## 5. 教训

1. **调试回显的位置比内容更容易出错**：第一次把 `DBGJOINED` 插在 `text = …` 之后、`lines = […]` 之前，
   `UnboundLocalError: cannot access local variable 'lines'` —— 定位断言要插在 `joined` 之后。
2. **「没看到输出」不等于「没跑」**：smoke 只回显部分行，`MAIWELCOME` 不在回显里但断言是真的在跑；
   用一次性 `DBGJOINED welcome_ok=True seen_no=True` 证伪了「可能没执行」，比反复读日志可靠。
3. 文档补丁要做好**锚点漂移**的准备：`断言表.md` 的状态行原文与记忆里的不同（L2-87 没写进那句话）、
   `规划.md` 的行首是 `| v0.17.1 热键进…`（不是 `| v0.17.1 |`）⇒ 每个锚点先用 `assert count == 1` 挡住，
   再决定插哪。
