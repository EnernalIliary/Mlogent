# MAI 蓝图（blueprint）方案

> 状态：**方案稿**（用户 m04549 item2 要求：先出方案 + 推荐，不马上实现）。
> 相关：`docs/Mlog辅助-工作区快照-规划.md` §5.2（仿蓝图界面的自有对话框）、v0.14.1 的 `mode:"improve"`。

## 1. 一句话结论

1. **保存**：调原版 `Vars.schematics.create(x, y, x2, y2)` 抓当前选框 → 自己 `tags.put("name", …)` → `Vars.schematics.add(s)`。走原版接口，文件落 `saves/schematics/<名字>.msch`，蓝图页立刻出现（带预览），不碰文件格式。
2. **上下文**：写进**逻辑签名区**（`aigenerated` 签名的 payload），不另建索引文件 —— 蓝图的 `Stile.config` 原样存逻辑代码，签名行随代码进蓝图，复制/上传/创意工坊/改名都带着它。
3. **入口**：往 `Vars.ui.schematics.buttons` 追加一个「MAI 对话」按钮（该表在构造函数里建一次、`setup()` 不重建 ⇒ 只加一次即常驻），点开列出 `Vars.schematics.all()`，选中一个 → 取其处理器代码作为 `prevCode` 开 improve 作业。

## 2. 取证（都在本仓源码里核对过）

### 2.1 保存路径（`Mindustry-Source/core/src/mindustry/game/Schematics.java`）
- `create(int x, int y, int x2, int y2)` (:377)：`Placement.normalizeArea(...)` 裁到 `maxSchematicSize`；跳过未发现/不可见方块；抓 `Stile(realBlock, x+offsetX, y+offsetY, tile.config(), rotation)` (:433) ⇒ **LogicBlock 的代码就是它的 config，原样进蓝图**。空选区返回 `Schematic(new Seq<>(), new StringMap(), 1, 1)`。
- `add(Schematic)` (:347)：`all.add` → `write(schematic, findFile(sanitize(name)))` → `schematic.file = file` → `checkLoadout(schematic, true)` → `all.sort()`。**异常只 `ui.showException` + `Log.err`，不往外抛** ⇒ 写完要自己回读 `all()` 判断真的存进去了。
- `create()` 返回的 `tags` 是空的 ⇒ `Schematic.name()` (:63) = `tags.get("name", "unknown")` = `"unknown"` ⇒ **不自己 put name 就会存成 `unknown.msch`、蓝图页显示 unknown**。
- 另有 `writeBase64` (:437) / `readBase64` / `read(Fi)` (:534) 可用于导出文本、导入。
- 反向构造（不抓世界、只用代码造蓝图）：`new Schematic(new Seq<>(), new StringMap(), w, h)` + `tiles.add(new Stile(Blocks.microProcessor, x, y, code, (byte)0))`。`Schematic` 构造、`tiles`(final Seq)、`Stile` 构造（`Stile(Block, int, int, Object, byte)` :132）全 public。

### 2.2 蓝图页（`Mindustry-Source/core/src/mindustry/ui/dialogs/SchematicsDialog.java`）
- 字段：`public SchematicsDialog schematics;`（`core/UI.java:75`，`Vars.ui.schematics`）。
- 构造函数 (:42-72)：`addCloseButton()` + `buttons.button("@schematic.import", Icon.download, this::showImport)` + `makeButtonOverlay()` + `shown(() -> { searchField.setText(""); setup(); })` + `onResize(this::setup)`。⇒ **`buttons` 行只建一次**，我们追加的按钮不会被 `setup()` 清掉。
- `setup()` (:74)：`cont.clear()` 后重建搜索框/标签行/蓝图列表；`rebuildPane` (:135-209) 每行 `t.clear()` 重建，行内自带 info/upload/pencil/trash 小按钮 ⇒ **不 hook 行**，注入会被重建抹掉。
- `Dialog.shown(Runnable)`（`Arc-Source/.../Dialog.java:406`）可叠加监听；我们的监听注册在构造函数之后 ⇒ 在每次显示时跑（可用于刷新自己的列表）。

### 2.3 签名区载荷（`tools/aigenerated.py`）
- 签名 = 把结尾 `end` 换成 `jump 0 always 0 "aigenerated:<作者>:<12hex>[:<payload>]"`（`SIG_LINE` :70）；`SIG_RE` (:72) 只允许**一个** payload 段 `[A-Za-z0-9_-]+`。
- payload = `base64url(('z'|'j') + JSON)`，JSON = `[[line, stmt, text], …]` 注释三元组（`encode_comments` :172 / `decode_comments` :183），zlib 9 压过再 base64。
- 关键性质：payload 字符集只有 `A-Za-z0-9_-` ⇒ 塞进 mlog 字符串字面量安全（不会有引号/反斜杠）；且逻辑代码进蓝图后这段字符串原样保留。

## 3. 推荐设计

### 3.1 保存（B1）
面板加「存成蓝图」按钮（框选框的按钮区已有 查看/取消 两个，第三个位置够）：
```
var s = Vars.schematics.create(r.x1, r.y1, r.x2, r.y2);
if(s.tiles.size === 0){ hint("框里没有可存的方块"); return; }
s.tags.put("name", <工作区名 or 描述前 24 字>);
s.tags.put("description", "MAI 生成 · " + <工作区 id>);
Vars.schematics.add(s);
// 回读校验：add() 吞异常
var ok = Vars.schematics.all().find(x => String(x.name()) === name) != null;
```
- 名字要 `Strings.sanitizeFilename` 后不重复（重名会存成 `name_1.msch`，`findFile` :333 自己处理，但回读判断要按前缀比）。
- 无头模拟器里 `Vars.schematics` 为 null ⇒ 探针只能报 `schematics=no`，真机才验。

### 3.2 蓝图页入口（B2）
```
var btns = Vars.ui.schematics.buttons;      // public final Table
btns.button("MAI 对话", fun…);              // 只加一次（模块加载时）
```
点开后的列表读 `Vars.schematics.all()`，每个 `Schematic`：`name()`、`tiles`、`file`。取代码：遍历 `s.tiles`，`t.block instanceof LogicBlock` 的 `t.config` 就是代码字符串（`LogicBlock.java` 里 code 原样存）。
选中 → `jobBody(b, desc, wsInfo)` 带 `mode:"improve"` + `prevCode`（复用 v0.14.1 已有链路，sidecar 侧 `previous_version()` 已支持）。

### 3.3 上下文写进签名区（B3，推荐）
payload 升 **schema v2**：`{"v":2,"c":[[line,stmt,text],…],"m":{"ws":"<工作区 id>","name":"<蓝图名>","prompt":"<用户描述>","job":"<作业 id>"}}`。
- `decode` 兼容 v1（顶层是数组 ⇒ 无 meta）；`sign_text` 重签时保留旧 `m`（和现在保留旧注释行号同理）。
- mod 侧读：`Packages.java.util.Base64.getUrlDecoder()` + `Packages.java.util.zip.Inflater` + 手写最小扫描只取 `m`（不做通用 JSON 解析，Rhino 里别引第三方）。
- 为什么不用 sidecar 索引文件：蓝图会被复制、改名、上传创意工坊、删档 —— 外部索引一定与文件失联；签名在代码里就跟着蓝图走。这也是用户「推荐写入逻辑签名区」的判断依据。
- 体积：meta 几十字节，zlib 后几十字节，对 `.msch` 无感。

## 4. 分步与估时（2–3 人日）

| 步 | 内容 | 依赖 |
| --- | --- | --- |
| B1 | 选框 → 蓝图（原版 create/add + 命名 + 回读校验）+ 面板按钮 | 无 |
| B2 | 蓝图页「MAI 对话」按钮 + 蓝图列表 + 选中开 improve | B1 的列表读取代码 |
| B3 | 签名 payload v2（Python 侧）+ mod 读取 | **item1 签名并入先落地**（同一个 `aigenerated.py`，避免打架） |
| B4 | 真机验证 + 断言 L2-69/L2-70 + 报告 | B1–B3 |

## 5. 不做 / 风险
- **不** hook 原版蓝图页的行布局或行内按钮（`rebuildPane` 每次重建，注入必丢）。
- **不**把整段对话历史塞进签名（只放 id + 提示词 + 工作区引用；历史留在 sidecar 作业里，避免签名串无限膨胀）。
- 风险：`Vars.schematics.add()` 吞异常 ⇒ 必须回读校验，否则用户以为存了。
- 风险：创意工坊蓝图是只读的（`mod` 字段非空 / 非 `schematicDirectory` 下的文件，`overwrite` :147 会拒绝），我们只读不写它们。
