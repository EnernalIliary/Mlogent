# 92 · v0.16.1：蓝图页「MAI 对话」（B2）+ 原版「详细」页「继续对话」（B4）

用户批准：m08460「开工吧 注意签名token也被用于挂载注释，不要冲突。」（B1–B5 全开）；本期完成 B2/B4。
上文：v0.16.0 已交付 B1（框选存原版蓝图）与 B3（上下文进签名 payload v2）。

## 1. 两处入口

| 入口 | 位置 | 做了什么 |
|---|---|---|
| 「MAI 对话」 | 原版蓝图页底栏 `Vars.ui.schematics.buttons` | `blueprintPageHook()` 只挂一次（`BP_PAGE_HOOKED` 守）。点开 `openBlueprintPicker()`：列蓝图（`blueprintList(400)`），选中后 `openBlueprintChat(nm)`。 |
| 「继续对话」 | 原版「蓝图 → 详细」页 `SchematicInfoDialog.buttons` | `blueprintInfoHook()` 反射 `SchematicsDialog` 的私有字段 `info`（`SchematicsDialog.java:33`，`showInfo()` :223-225 只是转发），按 `info.title.getText()`（`[[schematic] 名`，`[[` 是 arc 的转义，靠 `blueprintTitleName()` 剥）拿名字。 |

**一个必须处理的原版行为**：`SchematicInfoDialog.show()` 每次都 `cont.clear()` 且 `buttons.clearChildren()`
（`SchematicsDialog.java:770-830`），所以「标题没变但按钮被清空」是常态 —— 只按标题变化重挂会让同一张图
第二次打开时按钮消失。`blueprintInfoHook()` 因此同时看 `info.buttons.getChildren()` 的数量。

## 2. 读回上下文

`blueprintCtxOf(name)`：

1. `Vars.schematics.all()` 里按 `sc.name()` 找同名 `Schematic`；
2. 遍历 `sc.tiles`，取 `tl.config` 里带 `aigenerated:` 的代码（`LogicBlock` 的 config 就是代码原文）；
3. `sigMetaOf(code)` 解签名 token 里的 payload v2 → `m = {ws, name, prompt, job}`。

## 3. Rhino 的坑：带半角引号的字符类正则会 invalid bytecode

初版 `sigMetaOf()` 用 `txt.match(/aigenerated:([^:"]+):([0-9a-f]{12}):([A-Za-z0-9_-]+)/)`，
真机 v160.7 一调用就 `IllegalStateException: FAILED ASSERTION: invalid bytecode`（`node --check` 与无头引擎都过）。

二分结论（stub 函数体 → 只留正则 → 换字符类）：

| 变体 | 结果 |
|---|---|
| 函数体换成 `return null;` | 绿 |
| 整段包一个大 try/catch | 仍报 |
| 只留那条正则 + `return` | 仍报 |
| 字符类去掉引号 `/aigenerated:([A-Za-z0-9_-]+)/` | 绿 |

⇒ **模组代码里不要用带半角引号（以及半角括号）的字符类正则**，最好完全不用正则。改成手写扫描：
`indexOf("aigenerated:")` → 扫 author（遇 `:` 或 `"` 停）→ 取 12 位 hex → 扫 base64url → `Base64.getUrlDecoder().decode()`
→ `sigInflate()`（`InflaterInputStream` + `ByteArrayOutputStream`，`guard < 4096` 防死循环）→ `JSON.parse()` → `doc.v === 2`。

## 4. 提交与写回

- 提交：`{mode:"improve", desc, links:null, ipt:2, origin:null, snapshot:{}, workspace:{id,name,notes,prevCode,prevJob,prevFindings}}`
  POST `/jobs`，`blueprintChatPoll()` 900 ms 一次 `jobGet()`（面板里能看到生成的代码）。
- 写回：`sch.file` 为空就提示「先存成蓝图再继续对话」（原版只有存过盘的蓝图才有文件）；
  否则覆写目标处理器 `tl.config = code` → `Vars.schematics.saveChanges(sch)` → `blueprintCtxOf()` 回读确认。
- 全部动作由 `blueprintTick()` 挂在 `update()` 里，三件套各自 try/catch，任一步失败不影响游戏循环。

## 5. 验证

- `node --check MlogAuxiliary/scripts/main.js` → 0
- `python -X utf8 tests/mlogauxiliary/run_ui_smoke.py` → **EXIT=0**，三条探针：
  `MAISIGMETA:ws=ws1 name=蓝图甲 job=job7 prompt=数矿石，满了就停`、`MAIBPTITLE:[蓝图甲]`、`MAIBPCHAT:none`
  （无头没有 `Vars.schematics`，读上下文必须回 none 而不是抛错）
- `tests/run_tests.py` 46/46；`tests/logicd/run_logicd_tests.py` → `logicd OK`
- 门禁 `python -X utf8 gate.py --full --kb-build` → 见下（本轮记录）

## 6. 真机待验（需重启游戏）

1. 打开原版蓝图页，底栏应出现「MAI 对话」；
2. 任意蓝图点「详细」，底栏应有「继续对话」（同一张图连开两次都要在）；
3. 拿一张由 MAI 存的蓝图点「继续对话」，描述要改什么 → 作业跑完 → 点「写回」→ 蓝图里的处理器代码应更新；
4. 非 MAI 存的蓝图（代码里没有签名）应提示读不到上下文。
