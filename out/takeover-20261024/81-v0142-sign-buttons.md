# 81 · v0.14.2：写入后框不消失 + 框角两按钮 + 签名并入生成流程（+ 蓝图方案稿）

日期：2026-10-31。用户 m04549 一次提了四件事，本轮做完 1/3/4，第 2 件按要求只出方案。

## 1. item3「工作区不应该在写入之后就直接消失」

根因：v0.14.0 的 W1 只保证磁盘上不丢，UI 这一层还是 v0.12.7 的老行为 —— `writeBuild()` 成功后
`jobBoxWritten(b)` 直接 `closeJobBox()`，框（= 工作区的可视锚点）当场没了，`jobBox.ws` 也一起清掉。

改法（`MlogAuxiliary/scripts/main.js`）：
- `jobBoxWritten(b)` 只记 `jobBox.written = (jobBox.written || 0) + 1`，不再 `closeJobBox()`；
- `jobBadgeText()` 去掉「（点开看 · 右键关）」散文，写入后追加「已写入 N 台」；
- 框留到玩家主动关（徽标右键 / 管理窗「关闭框选框」）或工作区被归档/释放。

## 2. item4「作业区的点开看和右键关文案 → 两个不会 autoscale 的按钮（查看、取消）」

旧实现是 `font.draw()` 即时画的文字，整条文字当热区，宽度靠 `GlyphLayout` 自己量，跟 arc 控件的
autoscale 没有共同基准。新段「作业框按钮（v0.14.2）」：

```
JOB_BTN_H = 18      // 像素高，乘 1/camerascale 换算到 stage
JOB_BTN_PAD = 9     // 按钮内边距
JOB_BTN_GAP = 6     // 两钮间距
JOB_BTN_EDGE = 4    // 距框边缘
jobTextMeasure(text)         -> GlyphLayout 量出来的 {w,h}
jobButtonLayout(a)           -> 两个按钮的 stage 矩形（从框右下角往左排：取消在最右、查看在左）
drawJobButtons(r, a)         -> Fill.rect 底 + Lines.rect 边 + font.draw 字（左下角基准）
jobButtonsClick()            -> 命中判定，左键：取消=closeJobBox，查看=openJobManager
```

全部走**屏幕空间即时绘制**：`Core.camera.project()` 拿像素坐标，固定 `1/camerascale` 换算，
`font.setUseIntegerPositions(false)`，绕开控件 autoscale 和 stage 坐标换算（`Arc-Source` 里根本没有
`Stage.java`，换算无从查证）。

验证：`python tests/mlogauxiliary/run_ui_smoke.py` EXIT=0，`MAIBADGERECT` 实测
`box{x:4,y:4,w:48,h:48}` / `status{y:-13,h:13}` / `cancel{x:12,y:-35,w:36,h:18}` / `view{x:-30,...}`；
断言：两钮 `['cancel','view']`、高 18 px、取消贴右缘（`12+36=48`）、间距 6 px（`-30+36-12=-6`）、
都在框外、`text` 无旧散文。

## 3. item1「AI签名和挂载消失了」+「工作流没有过签名流程，并入一下」

根因：`tools/aigenerated.py` 的 `sign_text()` 一直是现成的，但**两个写入口从来没调它** ——
`tools/jobqueue.py` 的 `_materialize()` 与 `tools/logicd.py` 的 `compose()` 都直接
`msch.build_logic_data(code)`。所以模组写进处理器的程序既没有签名行，也没有「挂载」
（= `:pid:` 之后的 base64 注释包）。

改法（teammate `sidecar-sign` 实现，Lead 复验）：
- `jobqueue._materialize()` / `logicd.compose()`：**先签名 → 再门禁/分析 → 再编译**，作业 JSON 与
  `/compose` 回复多一个 `sig`（12 hex）；`SignError` 变 `rid=sign-error` 的 ERR finding（不写未签名代码）；
- `SIGN_AUTHOR = aigenerated.SIGN_AUTHOR`（`MAI_SIGN_AUTHOR` 可覆盖），`SIDECAR_VERSION='0.14.2'`；
- **`sign_text()` 的放置规则必须跟着改**：6 个内置模板里 5 个以 2 操作数 `jump loop always` 结尾，
  旧规则先补 `end` 再把 `end` 换成签名跳 ⇒ 签名行落在死循环之后，`mlogcheck` 报
  `unreachable-statement`、面板每份产物多一条假警告、`run_logicd_tests.py` 的 `need(not res['findings'])` 必红。
  新规则：末条是无条件跳转 ⇒ token 进它的 value 槽并删掉后面那个死 `end`（`jump loop always 0 "sig"`），
  裸 2 操作数先补 `0`；pid 对 `verify_text()` 会重建的 body 取哈希 ⇒ **既有 id 全部不变**；
- `#` 注释只活在 payload 里、不进交付文本（游戏汇编丢注释行，`b.code` 由汇编结果重建，留着会被
  `armWriteCheck()` 误判成「无权限」）。

验证（Lead 复跑）：
- `python tests/run_tests.py` → 46/46（`slot_end_kept: true→false`）；
- `python tests/logicd/run_logicd_tests.py` → protocol 26 / jobs 16 / provider 12 / improve 8 / llm 12，
  **write path 7 模板**（把 `/compose` 的 `bytes_b64` 真灌进 v160.7 处理器、回读 `b.code === code`，
  这条就是 `armWriteCheck` 的回归护栏）；
- 独立脚本 `out/_v142_tpl_sign.py`：6 个模板签名前后行数不变、findings 不变、`verify_text()==[]`、
  token 恰好 1 个；`out/_v142_verify_sign.py`：2 操作数跳尾不加 `end`、`end`-only 程序可重签、
  仓里既有签名文件 `写满停*.mlog` 重签逐字节不变。

## 4. item2 蓝图方案（只出方案，未实现）

`docs/Mlog辅助-蓝图方案.md`：调原版 `Vars.schematics.create()` + `tags.put("name")` +
`Vars.schematics.add()` 存盘（`add()` 吞异常 ⇒ 必须回读 `all()` 校验）；上下文写进**签名 payload**
（schema v2 `{"v":2,"c":[…],"m":{…}}`，跟着蓝图走，不建外部索引）；入口往
`Vars.ui.schematics.buttons` 加按钮（该表只在构造函数建一次，`setup()` 不重建）。
分 B1–B4 四步、估 2–3 人日，B3 依赖 item1 先落地（同一个 `aigenerated.py`）。

## 5. 本轮没做

- 真机验证：签名/按钮都要玩家重启游戏（模组 0.14.2）+ 重启 sidecar（`GET /health` 应为 `0.14.2`）才看得到。
- 蓝图实现（等用户点头）。
- 运行中的 sidecar 还是老版本；打包 exe 本轮会重建成 0.14.2。
