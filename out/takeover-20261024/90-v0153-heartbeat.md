# v0.15.3：心跳 JSON 化 + 旧副本移出 mods

2026-11-01。触发：用户 m08537「显示sidecar 已就绪：http://127.0.0.1:9046 但是仍然无法投递」，
随后 m08559 要求「直接覆盖修复然后继续你的工作」。

## 1 现场

装机目录下有两个「同名」模组：

```
saves\mods\MlogAuxiliary                 0.15.2，没有 sidecar.log
saves\mods\MlogAuxiliary.bak-...-050914  0.15.1，sidecar/bin/sidecar.log 写入于 05:23:54
```

那个日志只有两行：

```
logicd listening on http://127.0.0.1:9046
logicd idle for 45 s with no ping, exiting
```

两件事同时成立：**游戏跑的是旧副本**（`Mods.loadMods()` 用 `meta.internalName` 去重，
扫描顺序靠后的赢），**后端是因为收不到心跳才退出的**（不是崩溃）。

## 2 根因一：心跳包不是 JSON

`MlogAuxiliary/scripts/main.js` 的 `sidecarPing()`：

```js
httpJson("POST", "/ping", {}, function(code, text){ ... })
```

`httpRaw()` 拼请求时用 `String(body)`，JS 对象 `{}` 被转成字符串 `"[object Object]"`，
于是请求体是这 15 个字节。后端 `tools/logicd.py` 的 `/ping` 先 `json.loads`，失败 ⇒ 400。

回调把 400 当成「后端坏了」：`SIDE.state = "failed"`、`spawned = false`、`url = ""`，
**从此不再发心跳**；而后端的 `serve()` 里有 idle 看门狗（`--idle-exit 45`），
45 秒没收到心跳就退出。于是屏幕上还留着「已就绪」那句话，实际已经投不出去了。

`sidecarRetire()` 里的 `"/shutdown", {}` 是同一个错，所以「退役旧后端重拉」这条路径
从上线起就没生效过。

修法：

- 两处 body 改成 `"{}"`（字符串，`httpRaw` 原样发）。
- `SIDE` 加 `pingFail` 计数：`code === -1`（连不上）立刻 `sidecarRetire` 重拉；
  4xx/5xx 连续 3 次才退役（偶发 5xx 不要一直重启）；探测到 up 或 spawn 成功时清零。

## 3 根因二：旧副本留在 mods 里

`packaging/install.ps1` 原来把旧版移到 `$dest + '.bak-' + stamp`——**还在 mods 目录下**。
mods 下任何带 `mod.hjson` 的目录都是一个模组，而旧副本与新版同内部名，
于是每次安装都多一份「同名模组」，谁生效看扫描顺序。

修法：`$bakRoot = <saves>\mod-backups`，旧版移到那里；启动时先把 mods 下
历史遗留的 `MlogAuxiliary.bak-*` 一并挪走。真机执行时挪走了 9 个。

## 4 测试

- `tests/mlogauxiliary/run_ui_smoke.py`：正向红线 `httpJson("POST", "/ping", "{}"`；
  反向红线 `"/ping", {}` / `"/shutdown", {}` 出现即失败。
- `tests/logicd/run_logicd_tests.py`：`test_life` 加 `raw_post()`，断言 `[object Object]` → 400、
  `{}` → 200；`test_improve` 的 echo 断言改成「签名行去掉 payload 后文本一致」+ `decode_meta` 的 `ws`，
  因为 v0.16.0 的 payload v2 会带作业上下文。
- 结果：`logicd OK`（protocol 26 / jobs 17 / provider 12 / improve 8 / llm 12 / diag 7 / life 3 / write path 7）、
  `46/46 passed`、ui smoke EXIT=0、`gate.py --full --kb-build` **17/17 in 105.1s**。

## 5 发行

- 包 `out/_dist/MAI-0.15.3/MAI-0.15.3/`：166 files / 18620162 B；
  `MAI-0.15.3-mod.zip` 8403686 B sha256 `AE88521018922A24F19C0B6A0E362B14842B3E854360D1A2D03ACB5E45E7CD76`；
  `MAI-0.15.3.zip` 8424581 B sha256 `5468537B9958AF4FD45752BD272552DEFC3BFBF3CCC8F5E4EA04A598B9CEE4B5`。
- 包内 exe：`/health` = 0.15.3；`POST /ping` `{}` → 200、`[object Object]` → 400；`/shutdown` 干净退出（码 0）。
- 装机：9 个旧副本挪到 `saves\mod-backups`，mods 下只剩一个 `MlogAuxiliary`（`MOD_VERSION = "0.15.3"`）。

## 6 教训

1. 「已就绪」这句话只能代表某一刻探测成功；之后的心跳失败必须有可见的后果，
   否则界面与现实会长期脱节。这次 45 秒自退 + 界面不动，正是脱节的来源。
2. 装机脚本「保留旧版」时必须离开 mods，不能只改名；同 id 的模组目录有几个，游戏就只看一个。
3. 测试要钉住**真机失败的形态**：`[object Object]` 这种包体，光看代码看不出来，是接上真后端才暴露的。
