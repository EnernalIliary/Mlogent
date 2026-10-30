# 59 · v0.9.1：面板把「sidecar 进程太旧」直接说出来

日期 2026-10-30。玩家在游戏里截图：AI 面板投递作业只有一行 `投递失败：no such endpoint: /jobs`。

## 59.1 症状与误判方向

- 模组 v0.9.0，面板按钮会 `POST /jobs`；返回 404，正文 `{"ok": false, "error": "no such endpoint: /jobs"}`。
- 第一反应会是「模组比侧车新」或「路由写错了」，但 `tools/logicd.py` 的 `/jobs` 分支在仓库里明明存在，
  `tests/logicd/run_logicd_tests.py` 的 jobs 12 项也全过——**代码是对的，跑着的东西不对**。

## 59.2 根因：进程里的旧代码

`Get-CimInstance Win32_Process -Filter "Name='python.exe'"` 抓到唯一一个 logicd 进程：

```
PID 59920 :: python.exe -X utf8 tools/logicd.py --port 8765 :: started 10/30/2026 18:18:18
```

启动时间 18:18，而 `/jobs` 是 v0.8.0 才加的（当晚 20 点后）。Python 把模块读进内存之后，
磁盘上再改 `tools/logicd.py` 它不会知道 —— 于是同一个模组版本，重启侧车前 404、重启后立刻正常。
`GET /health` 一直是 200，这正是最容易骗过人的地方：老进程的健康检查跟新进程一模一样。

处置：`Stop-Process -Id 59920 -Force` → `Start-Process` 重新拉起（PID 61368，22:30:38）。
复验：`GET /health` 200、**`GET /jobs` 200 `{"ok": true, "jobs": [], "count": 0}`**、
`GET /capabilities` 报 `mindustry v160.7 (executor jar out/_server160.jar)` + 53 条指令。

## 59.3 模组侧改动：把诊断写进错误里

`MlogAuxiliary/scripts/main.js`：

```js
function sidecarStaleHint(t){
    var s = String(t === null || t === undefined ? "" : t);
    if(s.indexOf("no such endpoint") < 0){ return null; }
    return "sidecar 进程是旧版本，不认识这个接口（" + base + "）\n"
         + "关掉旧的 sidecar 进程再重新启动：python tools/logicd.py --port 8765\n"
         + "（改过 tools/logicd.py 之后必须重启，模组连的是内存里那份旧代码）";
}
function jobWhy(code, text, res){
    var hint = sidecarStaleHint(text) || sidecarStaleHint(res && res.error);
    if(hint !== null){ return hint; }
    return (res && res.error) ? String(res.error) : httpWhy(code, text);
}
```

三个作业接口（`POST /jobs`、`GET /jobs?id=`、`DELETE /jobs?id=`）的错误回调统一走 `jobWhy()`；
其它错误（连接被拒 / 超时 / 非 200）行为不变。红线测试：`tests/mlogauxiliary/run_ui_smoke.py` 增加
`function sidecarStaleHint(` 与 `no such endpoint` 两条源码断言（v0.9.1 段）。

## 59.4 活体复验（真 sidecar，不靠游戏）

重启后直接打 HTTP：

| 请求 | 结果 |
| --- | --- |
| `POST /jobs`（desc「容器里铜够 120 就打印」+ container1 + message1） | `done`，attempts 1，7 条语句，`bytes_b64` 184 字符，0 finding |
| `POST /jobs`（同上但只给 container1，没有消息块） | `rejected`，`template-needs-link` + `link-name-not-bound` |

第一条正是游戏里「处理器接了容器和消息块」的常态，说明默认模板档的整条链路是通的；
第二条不是 bug：**模板要打印就必须有 printflush 的对象**，mlog 没有消息块就什么都看不到，
模板不该凭空写一个不存在的链接。文案已点名「代码里写的 message1，处理器没有这个链接」。

顺带记两个契约细节（排查时容易踩）：

- `job id = sha1(snapshot + desc + mode)[:16]`，**不含 links / origin** ⇒ 同 desc + 同快照换链接会幂等命中旧作业（`created: false`）。
- `GET /jobs?id=` 返回 `{ok, job}`（单个），不是 `{ok, jobs}` 数组。

## 59.5 复跑

- `python gate.py --full`：**15/16 PASS + kb WARN（stale，因刚改过 tools/README.md）**，重跑 `tools/kb.py build` → `{"chunks": 6342, "files": 65}`。
- `tests/mlogauxiliary/run_ui_smoke.py`：PASS（18 个表格方法全 OK_SKIN、假表 66 行、作业队列三条路径 done/rejected/zero-link 全对）。
- `node --check MlogAuxiliary/scripts/main.js`：0。

## 59.6 打包与安装

- `out/_dist/MlogAuxiliary.zip`：5 条目，62,455 B，sha256 `46D131F2DB16743410A1EC631566F431188565868442DE7B397B052203B23BEA`（main.js 117,077 B）。
- 已目录式覆盖安装到 `E:/Program Files (x86)/Steam/steamapps/common/Mindustry/saves/mods/MlogAuxiliary/`，5 文件逐字节 OK。
- 侧车保持 PID 61368 运行在 `http://127.0.0.1:8765`（最新代码）。

## 59.7 下一刀候选

①面板记住上次选中的 provider（模板档/模型档）②处理器有多个 message 时按距离挑最近的 ③旧作业列表里给 rejected 的补一条「加消息块」的可点提示。
