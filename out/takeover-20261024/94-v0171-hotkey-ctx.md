# 94 · v0.17.1：热键进原版按键绑定 + 标题居中 + 蓝图详情页 MAI + 框选先读签名

用户 m09822 一次提了四条（原话）：

> 1.原版有按键绑定界面，我要你在按键绑定那里注册热键。不需要f2和f7。
> 2.设置中所有的标题都没有居中。
> 3.MAI的按键是加在蓝图库->蓝图详情页面的位置，那个位置还有返回、导出和编辑。这个按键用于管理蓝图的上下文。
> 4.框选逻辑之后先尝试从签名挂载读取上下文。

四条全部落在 `MlogAuxiliary/scripts/main.js`（286239 → 289459 字符，18 处替换），另新增两个 bundle 文件。
sidecar 逻辑没动，只把 `SIDECAR_VERSION` 跟到 0.17.1。

## 1. 热键注册进原版按键绑定

**为什么之前是自建的**：v0.17.0 按「允许在设置页改键」写了一套 `HOT_KEY` 存储 + `hotBegin()` 捕获下一次按键，
好处是不用碰引擎 API，坏处是它不在原版「按键绑定」界面里，用户还得回来找设置页。这轮直接换成引擎的正规入口。

- `selKeyBind()`：`Packages.arc.input.KeyBind.add("mai-select", new KeyBind.Axis(KeyCode.f3), "mlogauxiliary")`，
  `KB_SELECT`/`KB_TRIED` 两个守卫保证只注册一次。注册后 `KeybindDialog.rebuildBinds()` 每次打开都遍历
  `KeyBind.all`（`Mindustry-Source/core/src/mindustry/ui/dialogs/KeybindDialog.java`），所以运行期注册也立刻可见，
  改键 / 恢复默认都由原版负责，值存 `Settings` 的 `keybind-default-keyboard-mai-select-key`。
- 键名与分类走模组 bundle：新增 `MlogAuxiliary/bundles/bundle.properties`（`category.mlogauxiliary.name = MAI`、
  `keybind.mai-select.name = MAI: select processors`）与 `bundle_zh_CN.properties`（「框选处理器（MAI）」）。
  `Mods.java:636-660` 会把 `mod.root/bundles/bundle*.properties` 合进根 bundle，所以键名跟着游戏语言走。
- `selKeyCode()` 反读 `kb.value.key`（`public Axis value;`、`Axis.key` 都是 public，Rhino 能直接点），
  读不到就退回 F3；update 钩子里仍然是 `Core.input.keyDown(selKeyCode())` 的按住式拖框，语义没变。
- 设置页「热键」段从三个改键按钮换成两行 `kv` 说明（框选键在原版界面里改；F2/F7 固定）。
  自建的 `HOT_KEY`/`hotGet`/`hotSet`/`hotBegin`/`hotCaptureTick`/`hotLabelsRefresh`/`hotCellSet` 全部删除，
  smoke 加了反断言 `hotBegin(`、`HOT_KEY` 不得回来。

## 2. 设置页标题居中

**根因不是我们没写 `center()`**：v0.17.0 已经给 Cell 调了 `center()`，但 `Cell.center()` 只设 `align = Align.center`
（`Arc-Source/arc-core/src/arc/scene/ui/layout/Cell.java:512-514`），管的是**控件在格子里**的位置；
Label 里文字自己的对齐是 `Label.labelAlign`（`Label.java:34`，默认 `Align.left`）。所以两行标题虽然居中了控件，
文字还是左对齐 —— 用户看到的就是「所有的标题都没有居中」。

- 新增 `alignText(el, align)`：`el.setAlignment(align)`，其它类型 el 安全跳过。
- `titleLine()` 里对取到的 Label 调 `alignText(lbl, Align.center)`；
- `section()` 改成先拿 Cell（`width(ROW_W)` + `center()`）再 `alignText(sc.get(), Align.center)`，段标题也居中。

## 3. 蓝图「详细」页的 MAI 按钮

- `blueprintInfoHook()` 现在只挂一个按钮：`info.buttons.button("MAI", …).width(110)`，跟原版 返回 / 导出 / 编辑 并排。
- 点开的是上下文管理窗（`blueprintChatAsk` 的宿主窗）：标题「Mlog辅助 · 蓝图上下文 · 名」，
  内容是本图的签名 payload v2 上下文（工作区、当时的描述、上次作业）+ 新描述输入框，
  底栏 继续对话 / 写回蓝图 / 复制上下文 / 关闭。
- 去掉 v0.17.0 在蓝图页底栏挂的「MAI 对话」和详情页第二个「继续对话」——用户明确要「就在详情页那排按钮里」，
  两个入口反而要挑。
- smoke 红线随按钮文案同步（`info.buttons.button("MAI", …)`），蓝图页底栏入口的红线删除。

## 4. 框选先读签名挂载

- `sigCtxInRegion(targets)`：扫框里每台处理器的 `String(b.code)`，含 `aigenerated:` 就用 `sigMetaOf()` 解 payload v2 的 `m` 段，
  `ws`/`name`/`prompt` 任一非空即命中（返回 meta + 代码 + 那台处理器 + 坐标）。
- `openQuickJob()` 的顺序改成：签名命中 → `wsLoad(meta.ws)`；磁盘上没有这份（换机器 / 删过）→ `wsFromSig()` 用 meta 重建
  （沿用 `meta.ws` 做 id、`meta.prompt` 做 notes、`sig.job` 留档、把那台处理器 `code` 记进 `row.code`）→ 都没命中才 `wsFindActive(r)`。
- 命中时描述框标题带工作区名、上面多一行「已从签名挂载读到上下文：名（作业 id）· 来自 @x,y」，输入框预填 `ws.notes`。
- `startJobBatch(targets, desc, rect, improve, wsIn)` 多了第 5 参：传了就走 `wsAttachCtx()`（并集扩 bounds + touchProc + 保存），
  不会再为同一片逻辑新建第二个工作区。
- 意义：签名是跟着代码走、跟着蓝图走的；所以「隔了几天 / 换了存档 / 从工坊下了张蓝图」再框同一片处理器，上下文接得上。

## 验证

- `node --check MlogAuxiliary/scripts/main.js` → 0
- `python -X utf8 tests/mlogauxiliary/run_ui_smoke.py` → EXIT=0（新增 v0.17.1 段：11 条正断言 + 2 条反断言；
  `MAIBADGERECT` 几何仍 `box{4,4,48,48}` / `cancel{12,-35,36,18}`）
- `python -X utf8 tests/run_tests.py` → 46/46
- `python -X utf8 tests/logicd/run_logicd_tests.py` → logicd OK（protocol 26 / jobs 17 / provider 12 / improve 8 / llm 12 / diag 7 / life 3 / write path 7 模板）
- 断言表 **L2-87**，实数 146 条（L1 31 / L2 87 / L3 6 / L4 4 / S 18）

## 真机要验的四件事（重启游戏后）

1. 设置 → 控制 → 按键绑定 里能看到分类「MAI」、条目「框选处理器（MAI）」，默认 F3，改成别的键后拖框立即用新键。
2. 设置 → Mlog辅助：两行大标题与每个段标题的文字都居中。
3. 蓝图库选中一张蓝图 →「详细」页：返回 / 导出 / 编辑 旁边有「MAI」，点开是这张图的上下文。
4. F3 框住一片写过逻辑的处理器：描述框标题是那个工作区的名字，上面写着已从签名挂载读到上下文。
