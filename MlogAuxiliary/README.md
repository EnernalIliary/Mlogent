# MlogAuxiliary —— 游戏内Mlog辅助（P1 + P2 + 设置界面 + AI 面板 + 区域面板，v0.7.0）

把「写 mlog」这件事从玩家手里拿走：**说意图，不写代码**。

    [游戏内] 选中处理器 → 选模板/填参数 → POST 给本地 sidecar
                                              ↓
    [sidecar] tools/logicd.py: 意图 → mlog → 静态检查(41 条规则 + 成本) → 字节载荷
                                              ↓
    [游戏内] 面板显示 findings + 成本 → 确认 → build.configure(bytes) 写进处理器

P1 做 **API 接入** 与 **写入通道**；P2 把**快检**搬进游戏（没有 Python 也能先判一轮）；
v0.3 起调试入口是**设置 → Mlog辅助**一栏，不再依赖控制台。
v0.4 起有两个正面入口：**F4 的 AI 辅助面板**（一句话 -> sidecar 选模板并预检 -> 预览 -> 写入）
与**原版逻辑编辑器底部的审查栏**（打开原版编辑器就自动挂上，代码一改就重算）。
v0.4.2 起多一个**只读**入口：**F7 把鼠标周围 10 格扫成区域快照**，sidecar 算出每个处理器「还能连哪些方块、
该叫什么链接名」，用文本弹窗列出来 —— 先看清楚，再决定要不要按 F4 写。

生成层仍是确定性模板（模型只能选模板、填参数，不能直接产 mlog）；框选 + 队列是 P3/P4，路线见
`docs/Mlog辅助-规划.md`。

## 为什么写入走 config 通道

`LogicBlock` 的 `config(byte[].class, ...)` 就是原版「客户端把代码推给服务端」的通道
（`Mindustry-Source/core/src/mindustry/world/blocks/logic/LogicBlock.java:65-69`），
载荷格式是 `compress(code, links)`：版本字节 + 代码 + 链接表 deflate（同文件 `:137-166`）。
模组直接 `build.configure(bytes)`：

* 单机与联机同一条路径 —— 联机时由服务端执行 `readCompressed`，**不用自己造同步**；
* 载荷由 `tools/msch.py:447 build_logic_data()` 生成，和游戏自己的编码器同一格式，
  `tests/logicd/run_logicd_tests.py` 会把这段字节灌进真 v160.7 处理器逐条验。

## 安装

1. 先找到**真正在用的数据目录** —— 不要凭印象。Steam 版可能是桌面版（`%APPDATA%\Mindustry`），
   也可能是**便携版**（数据目录就是游戏目录下的 `saves`）。判据：游戏跑起来后看这两个位置的
   `last_log.txt` 谁的修改时间是刚刚，或者直接用游戏内「模组 → 打开文件夹」。
2. 把 `MlogAuxiliary/` **整个目录**放进那个 `mods` 下（本机实测是
   `E:/Program Files (x86)/Steam/steamapps/common/Mindustry/saves/mods/MlogAuxiliary/`）。
   **用 zip 也行，但 zip 里必须只包一层 `MlogAuxiliary/` 目录**：`Mods.resolveRoot()`（`Mods.java:1070-1074`）
   只在「根下恰好一个目录」时才下钻，否则把 zip 根当模组根，`scripts/main.js` 会 `exists()==false`，
   日志里就是 `[E] No main.js found for mod mlog-auxiliary.` —— 模组列表里看得见它、脚本却一行没跑，
   控制台自然找不到 `maiVersion`。`out/_dist/MlogAuxiliary.zip` 已经按这个形状打好了。
3. 启动 sidecar：`python tools/logicd.py`（默认 `http://127.0.0.1:8765`）。不开也能进游戏，
   只是没有生成/写入；**本地快检照常工作**。
4. 进游戏（模组是 `hidden` 的，不会出现在模组列表里，这是故意的：联机不会被当成不兼容模组）：
   **设置 → Mlog辅助**，这一栏会直接告诉你加载是否成功（版本 / 构建 / 快检模块 / sidecar / 两个目录）。
   把鼠标指向一个处理器再按 **F4** 打开 **AI 辅助面板**（一句话生成 + 预检 + 写入）；
  纯模板面板走那一栏的「模板面板」按钮。

## 控制台函数

| 函数 | 作用 |
| --- | --- |
| `maiVersion()` | 模组版本 + sidecar 地址 |
| `maiPing()` | 异步 GET `/health`，结果弹窗 + 写日志（返回「已发出…」） |
| `maiSel()` | 报告鼠标下的方块是不是处理器、它现在有几行代码几个链接 |
| `maiPanel()` | 打开面板 |
| `maiCompose(template, paramsJson)` | 异步 compose，结果弹窗并写日志（返回「已发出…」） |
| `maiApply(template, paramsJson)` | 异步 compose + 直接写进鼠标下的处理器（0 ERR 才写，结果弹窗） |
| `maiUndo()` | 撤销上一次写入（P1 是内存快照，重启游戏即失效） |
| `maiCheck([code])` | 本地快检：不给参数就查鼠标下的处理器，给了就查这段代码 |
| `maiScan()` | 全图扫描所有处理器跑本地快检，返回「N 个处理器 / 多少有命中 / 规则分布 / 耗时」 |
| `maiDiag()` | 诊断文本（就是设置界面里那段） |
| `maiSelfTest()` | 拿一张假 Table 建一遍设置表格，报告填了多少行/格（无 UI 环境的自检） |
| `maiSettings()` | 再尝试注册设置分类；返回 `registered` 或 `no ui` |
| `maiAi()` | 打开 AI 辅助面板（等同 F4） |
| `maiReview()` | 纯文本版审查：原版编辑器里的代码 + 快检结论 + findings（不弹窗） |
| `maiSnapshot(x1,y1,x2,y2)` | 区域快照 JSON 文本（tile 坐标，clamp 到地图内，上限 4096 格） |
| `maiSnapshotText(...)` | 同一份快照的人读摘要 |
| `maiRegion(x1,y1,x2,y2)` | 异步 `POST /region`，回包解析后弹窗（返回「已发出…」） |
| `maiRegionAround(r)` | 以鼠标下处理器为中心扫 `r` 格（F7 就是 `r=10`） |
| `maiHttpRaw(method,url,body)` | 调试用：同步发一个请求，返回 `code` 换行 `text`（v0.4.4 起走裸 socket，连不上回 `-1`） |

## 设置界面（v0.4）

`设置 → Mlog辅助`，一栏把调试要看的都摊开，不用再往控制台敲命令：

v0.4 把这一页按用途分段（`── 运行环境 ──` 这样的标题行 + 左标签右值两列）：

* **运行环境**：版本 / 游戏构建（`Version.build`）/ 快检模块是否加载（指令、op 版本门、链接槽各几条）/ 
  数据目录 / mods 目录 / 设置分类状态 —— 装错位置、规则表没加载，一眼看出来；
* **本地快检**：快检能否使用、规则表条数；
* **sidecar**：地址（可直接改，回车即存进 `Core.settings` 的 `mlogauxiliary-url`）、连接测试（GET `/health`）、**复制诊断**到剪贴板；
* **快捷动作**：AI 辅助编程 / 模板面板 / 快检鼠标下的处理器 / 打印诊断 / 重新注册分类 / 审查状态。

分类图标用原版逻辑徽标 `Icon.logic`（`Vars.ui.settings.addCategory(name, Drawable, Cons)`，
`SettingsMenuDialog.java:324`）：取不到图标（无头环境 `Core.atlas` 是 `null`）就退回纯文字重载（`:329`）。

排版只用了在真 v160.7 里实测能解析的 `Table` / `Cell` 方法（`add` / `labelWrap` / `button` / `field` +
`colspan` / `left` / `right` / `width` / `pad` / `padTop` / `padBottom` / `padRight` / `row`），
`run_ui_smoke.py` 会把 `maiSelfTest()` 报出的每个方法名拿到真引擎里调一遍。

注册走 `Vars.ui.settings.addCategory(name, Cons<SettingsTable>)`（`SettingsMenuDialog.java:329-330`），
分类只在显示设置菜单时 rebuild（`:357`、`:658`），所以脚本加载时机不影响它出现；脚本加载时 UI 还可能不存在，
`ClientLoadEvent` 上再补注册一次，之后热键钩子里还有一次**有界重试**（每 60 帧一次、最多 600 次）。
诊断里最后一行 `设置分类：` 会直接告诉你注册成功还是在哪个异常上失败。

**v0.3.0 那一栏没出现的原因**：设置表格用了 `t.table(function(tt){...})` 做按钮分组，真 v160.7 的 Rhino 在
**方法解析阶段**就抛 `InternalError: ... Table.table ... is ambiguous`（重载歧义），异常被注册函数吞掉，
于是游戏里根本没有这一栏 —— 而假表 smoke 还是绿的。v0.3.1 改成**平铺加行**（`t.button` / `t.labelWrap` /
`t.field`，实测都能解析），并且 `run_ui_smoke.py` 多了一道探针：把 `maiSelfTest()` 报出的方法名逐个拿到
真引擎里调用，出现 `ambiguous` 即 FAIL。**无头环境**（模拟器、`Vars.ui == null`）里 `maiSettings()` 返回
`no ui` 而不是抛错，设置表格的布线由 `maiSelfTest()` 用假表验证。

## AI 辅助面板（v0.4，F4）

把鼠标指向任意处理器按 **F4**（或设置页的「AI 辅助编程」、控制台 `maiAi()`）：

1. 一句话说清要什么，例如「让 @flare 从 10 10 来回巡逻到 30 12」「容器里铜够 250 就打印」；
2. 模组把这句话 + 该处理器的链接名列表 `POST /plan` 给 sidecar；
3. sidecar 用关键词路由选出模板（六个之一）并抽参数（数字、`@单位`、链接名），再走同一条
   确定性生成 + 全量检查，返回 `{template, params, reason, code, findings, cost, bytes_b64}`；
4. 面板显示**选中的模板与理由**、预检计数、前几条 findings、前 40 行代码；
5. 0 ERR 时出现「写入」按钮 —— 与模板面板同一个写入函数（`build.configure(bytes)`）。

有 ERR 就没有写入按钮：是拒绝写入，不是降级写入。意图太模糊（没命中任何关键词）时服务端
返回 `ok:false` + 六个候选模板名，面板照原样显示，不瞎猜。

**模型只有一个接入点**：`tools/logicd.py` 的 `_route()`。它是纯规则（关键词表 + 参数抽取），
换成模型调用时返回形状不变，模组这一侧一行都不用改 —— 所以模型永远没法把没检查过的 mlog 塞进存档。

## 原版编辑器审查栏（v0.4）

打开**原版逻辑编辑器**（点处理器 → 编辑）时，模组在对话框底部补一条 46 px 状态栏：

* 「审查」+ ERR/WARN/INFO 计数（`Pal.remove` / `Pal.lightOrange` 上色）+ 语句数 / 线性成本 / ipt；
* 「详情」= 全部 findings（`Vars.ui.showText`）；「AI 辅助」= 直接开 AI 面板；
* 代码一改（`canvas.save()` 变了）就重算，最多每 30 帧一次；编辑器没开时每帧只做两次属性读。

接法是最低侵入的：不自造对话框、不碰 canvas，只在 `Vars.ui.logic`（单例，`UI.java:79` / `:228`）
身上 `row()` 之后 `add(bar).growX()`。`LogicDialog` 的构造里 `clearChildren()` 之后只有
`add(canvas).grow()` / `row()` / `add(buttons).growX()` 三样（`LogicDialog.java:39-72`），
所以这一行是它的第四行，原版按钮一个都不动。
## v0.4.1：修掉「点生成就崩」+ 设置页按原版风格分隔

**崩溃根因（真机日志定的）**：v0.4.0 用 `d.cont.pane(function(t){...}).get()` 当结果区，但 `Table.pane(Cons)`
返回 `Cell<ScrollPane>`（Arc `Table.java:295/311`），`.get()` 拿到的是 ScrollPane。弹窗能开，一点「生成」就：

```
rhino.EcmaError: TypeError: Cannot find function add in object ScrollPane. (main.js#685)
```

因为 Group 有 `clear()`（`Group.java:357`）却没有公开的 `add`（真正的 API 是 `addChild(Element)`，`Group.java:251`），
`out.clear()` 过得去、`out.add(...)` 当场抛错，而模态窗口又没有关闭按钮（`Dialog.addCloseButton()` 是空实现，
`Dialog.java:453-455`），于是一路打到崩溃上报。

修法：结果区自己造一张 `new Table()` 交给 `pane(host)` 托管（Element 重载），之后只往 host 里加东西；
`pane()` 不可用时回落成 `d.cont.add(host).growX()`。AI 面板与模板面板两处都改了。

**设置页改成原版的样子**：不再手画「── 标题 ──」，改用原版自己的两样东西 —— 分段标题下一条 accent 强调线
（`titleImage = titleTable.image(Tex.whiteui, Pal.accent).growX().height(3f)`，`BaseDialog.java:25`），以及灰底行
（`Styles.grayPanel`，原版设置项 `CheckSetting` 用的同一个 Drawable，`SettingsMenuDialog.java:824-846`）。
行宽 540、内边距 8/5 也照它取。

`pane()` 这个坑现在有三道闸：`run_ui_smoke.py` 在真引擎里断言 ScrollPane 上没有 `add`；源码级禁止
`.pane(function` 与 `.pane(...).get()`；页面上每个 Table/Cell 方法名仍然逐个拿到真引擎里解析
（`margin` / `growX` / `height` / `color` / `image` 是这一版新用到的五个）。

## v0.4.2：区域快照 + F7 链接候选（P3 第一刀）

P3 原本是「框选 + 队列」，这一版只做**只读的那一半**：把鼠标周围一片区域读成快照，
让 sidecar 算清楚「每个处理器还能连哪些方块、链接名该叫什么」，人看完再决定写什么。
**它不写任何东西** —— 写入仍然只有 F4 面板那一条路（`build.configure(bytes)`）。

### 快照里有什么

把鼠标指向处理器按 **F7**（或控制台 `maiSnapshot(x1,y1,x2,y2)`）：

```json
{"schema":1,"mod":"0.4.2","build":160,"map":"...","world":{"width":...,"height":...},
 "bounds":{"x1":...,"y1":...,"x2":...,"y2":...},"cells":6,"truncated":false,
 "grid":[{"x":13,"y":10,"block":"container"}, ...],
 "processors":[{"x":10,"y":10,"block":"micro-processor","code":"...",
                "links":[{"name":"container1","x":13,"y":10}]}]}
```

* 坐标是 **tile 坐标**（`Vars.world.tile(x,y)` 那一套），空格子（`air`）不进 `grid`；
* 框会先交换大小值再 **clamp 到地图内** —— 处理器在 `(0,0)` 时问 `-1,-1` 是常态，不 clamp 会读到 null tile；
* 上限 `SNAP_MAX_CELLS = 4096`，超了置 `truncated:true` 并截断（prompt 装不下就不装）。

### sidecar 算出来的链接候选

`POST /region` 收这份快照，回答每个处理器「10 格内哪些方块能连、叫什么名」：

* **距离**：`LogicBlock.range = 8*10` 世界单位（`LogicBlock.java:49`），判定是
  `other.within(this, range + other.block.size*tilesize/2f)`（`LogicBlock.java:736`），tilesize=8
  → 中心距上限 `80 + size*4`。所以 2x2 的 container 到 10.5 格仍可连，1x1 的 switch 到 11 格就不行。
* **名字**：`LogicBlock.getLinkName`（`:123-135`，取方块名 `-` 的最后一段，末段是 `large` 或数字时取倒数第二段）
  加 `findLinkName`（`:331-360`，已有 `base<n>` 就取已占数字，否则从 1 起找最小空号）。`tools/mschgen.py:547`
  早就有同一套 `link_name_for()`，`tests/logicd/run_logicd_tests.py` 拿 `tools/block_sizes.json` 全表 446 个方块做零漂移比对。
* 候选按「代码里正在用的排前面、再按距离」排，并标 `[代码正在用]`；每个处理器最多显示 12 个。

F7 弹的是纯文本（`Vars.ui.showText`），不引入新的对话框/布局 —— v0.4.1 那次崩溃就是自造结果区引起的，
这一版刻意不再碰 UI 树。

### 引擎里踩到的两个坑（都写进了代码注释）

1. **`LogicBlock` 是方块类，建筑是它的内部类 `LogicBlock$LogicBuild`** —— `bld instanceof LogicBlock`
   恒为假，第一版快照的 `processors` 因此是空数组。判据改成鸭子类型（有 `executor` 且有 `code`），
   与既有的 `targetBuild()` 一致。
2. **`tile.block()` 是方法、`tile.build` 是字段** —— 写成 `tile.build()` 会得到
   `TypeError: Cannot call property build in object stone:air:air[2,0]`。

### 边界

只读、只回答「能连什么」，**没有**框选拖拽、没有队列、没有批量写入 —— 那些是 P3 后半段与 P4/P5。

## v0.4.3：F7 为什么弹出「sidecar 不可用」——同步等待在主线程上永远拿不到结果

v0.4.2 装进游戏后，F7 弹出的是一个空回复：

```
sidecar 不可用（ ）
pending
```

不是 sidecar 没起来，是**等待方式根本不可能成功**：

* `httpJson()` 把请求放到 daemon 线程，拿到结果后用 `Core.app.post(...)` 投递回调 ——
  也就是说回调**只能在主线程空闲后**执行；
* 控制台命令与热键分支都跑在**主线程**上，它们里面的 `while(got === "pending"){ waited += 50; }`
  既没有真的 sleep，又占着主线程 —— 计时器瞬间走完，函数带着字面量 `"pending"` 返回，
  于是 `regionCandidatesText()` 收到一段没有换行的文本：`code` 为空、`body` 是 `pending`。

四个同步入口（`maiPing` / `maiCompose` / `maiApply` / `maiRegion`）全是这个形状，一个都没法用。

**修法：全部改成异步。** 请求发出去就返回一句「已发出…（结果稍后弹窗）」，真正的处理放在回调里 ——
回调本身就在主线程（`Core.app.post`），所以照样能调 `Vars.ui.showText`、能 `build.configure(bytes)`：
F7 现在走 `regionAroundBox()`；`maiApply` 在回调里判断 0 ERR 再 `writeBuild()`。

错误文案也换了：连不上时直接说「连不上 sidecar（地址），先在本机跑 python tools/logicd.py」，
不再把空 code 印成一对空括号。`ping()` 这个同步探活函数整个删掉，探活统一走设置页的「连接测试」
（`probeSidecar()`，本来就是异步的）。

**这条现在有闸**：`run_ui_smoke.py` 的源码红线禁止 `while(x === "pending")` 与 `while(out === "?")`，
并要求 `regionAroundBox(` 存在、`regionCandidatesText(rtext)` 不再出现。


## v0.4.4：传输层换成裸 socket（顺带挖出 Rhino 的两个 codegen bug）

v0.4.3 修好等待方式之后，F7 换了新的报错，而且这回是完整的 Java 异常：

```
java.lang.IllegalAccessException: class rhino.MemberBox cannot access class
sun.net.www.protocol.http.HttpURLConnection (in module java.base) because module java.base does not
export sun.net.www.protocol.http to unnamed module
```

`java.net.URL.openConnection()` 交回来的对象是 `sun.net.www.protocol.http.HttpURLConnection` —— 
`java.base` 的内部类，没有 export。Rhino 绑成员时用的是**运行期类**（`rhino.MemberBox`），
于是 `setRequestMethod` / `getResponseCode` / `getInputStream` 这些被内部类覆写的方法一调就抛。

**修法：自己用 `java.net.Socket` 写 HTTP/1.1。** 请求行 + `Host` + `Connection: close`，有 body 时加
`Content-Type` / `Content-Length`（UTF-8 字节长度）；响应用 `InputStreamReader(..., "UTF-8")` 读到 EOF，
按 `\r\n\r\n` 切头与正文，状态码用 `substring` + `parseInt` 解析。sidecar 是 `BaseHTTPRequestHandler`
（`tools/logicd.py:717`），默认 `protocol_version = "HTTP/1.0"`，不 chunked 也不 keep-alive，读到 EOF 正好是正文尾。

**改的时候踩到两条真 v160.7 的 Rhino 编译期 bug**（两条都让整段脚本静默不执行）：

1. 状态行解析原本写 `/^HTTP\/1\.[01] (\d{3})/` —— Rhino 编译它时直接 `IllegalStateException: FAILED ASSERTION:
   invalid bytecode`。同一个文件里 `endpoint()` 那条长正则却没事，只能逐段 bisect 才定位到。
2. 收尾原本是 `try{ ... }finally{ try{ sock.close(); }catch(e1){} }` —— `finally` 体里再嵌 `try/catch`
   会让 Rhino 抛 `ArrayIndexOutOfBoundsException: arraycopy: last source index N out of bounds for object array[M]`。
   最小形是 `function t(){ try{ return 1; }finally{ try{ }catch(e){} } }`。现在改成 try/catch + 末尾独立的
   `try{ if(sock !== null){ sock.close(); } }catch(e1){}`。

**这两条最阴的地方是「静默」**：`Scripts.runConsole`（`Mindustry-Source/.../mod/Scripts.java:44-65`）
`catch(Throwable)` 之后**把错误当返回值返回**，不抛也不打印，所以控制台上看起来脚本「加载成功」，
实际一个函数都没定义。诊断时唯一的入口是把 `runConsole()` 的返回值打印出来。

**这条现在有闸**：`run_ui_smoke.py` 起一个真的本地 `http.server`，用 `maiHttpRaw` 打三枪 —— 
GET 200 且正文含 `MAISIDECAR-OK`、POST 200 且回显 `MAIPING`、死端口 `127.0.0.1:1` 必须回 `code -1`；
另有四条源码红线：禁 `openConnection(`、要求 `new Packages.java.net.Socket()`、禁 `}finally{`、
要求那句显式 `sock.close()`。

## v0.4.5：F7 不再贴 Java 栈，并把「代码在用但没绑上」的链接名点出来

v0.4.4 之后真机按 F7 看到的是：

    连不上 sidecar（http://127.0.0.1:8765）
    JavaException: java.net.ConnectException: Connection refused: getsockopt

传输层其实已经好了 —— 是 sidecar 没在跑。可这句话对用户没有用，所以 v0.4.5 做了两件事：

1. **三种失败分开说**（`main.js` 的 `httpWhy` + `lastLine`）：连接被拒绝 ⇒「sidecar 没在跑（连接被拒绝）」，超时 ⇒「sidecar 没回应（超时）」，其它 ⇒「连不上 sidecar」，各配一句启动命令；并且**只贴最后一行诊断**（超过 200 字截断），不再把 Java 栈整段糊上去。
2. **F7 点出「代码用到、但既没绑定也不在候选里」的链接名**（`/region` 新增 `missing`）。这是 `core` 那个老问题的机器化：`getLinkName`（`LogicBlock.java:123-135`）把 `core-shard` 变成 `shard`，游戏永远不会交给你一个叫 `core` 的链接名，可代码里写 `core` 很自然。现在面板会显示：

       ⚠ core 代码在用，但没绑上、也不在本区域候选里（同类可用 shard1）

判据在 `tools/logicd.py`（`_linkish` / `_code_idents` / `_result_names`）：

- 一个词要么是方块链接基名，要么是某个方块名的前缀（`core` → `core-shard`）；少于 3 个字母不算；
- 排除 `@内容`（`@copper` 是物品不是链接）、指令名与 op 名（`mlogcheck.SPECS` / `OP_*`）、结果槽里的名字（每行 token 1）、以及 `turretX` 这类大写后缀变量（`turret` 不因为 `turretX` 出现就被当成链接）；
- 同基名或同前缀的候选存在时给出替代建议。

`missing` 只报告，**不改代码、不写文件**；写入仍然只走 `build.configure(logic@config)`。

## v0.4.6：链接坐标是相对处理器的——不告诉 sidecar 处理器在哪，链接表就写到空地上

现象：v0.4.5 之后 F7 正常、面板能生成能写入，但写进去的程序一跑，`container1` / `message1` 这些链接全是 `null`，
游戏不报任何错。

根因：写入走的是 `LogicBlock.config(byte[].class, (build, data) -> build.readCompressed(data, true))`
（`LogicBlock.java:65-69`），第二个参数 `relative = true`，`readCompressed` 里
`if(relative){ x += tileX(); y += tileY(); }`（`:304-307`）—— 载荷里存的是**相对处理器**的偏移量；
而模组 `linkList(b)` 读出来的 `LogicLink.x/y`（`:102`）是**绝对** tile 坐标。原样塞进
`msch.build_logic_data()`，游戏就把绝对坐标当相对偏移又加了一次处理器坐标，整张链接表平移到地图另一边，
落在空地块上：`link.valid = false`，运行时读 `null`，全程无报错。

真 v160.7 实测（`out/_v46_probe2.py`）：处理器在 `(10,10)`、container 在 `(13,10)`。

- 载荷写绝对 `(13,10)` ⇒ 回读 `container1@23,20->null`
- 载荷写相对 `(3,0)` ⇒ 回读 `container1@13,10->container` ✓

（这个 bug 一直没被测出来，是因为测试里处理器都放在 `(0,0)`，绝对坐标和相对偏移数值相同。）

修法：

1. `tools/logicd.py` 新增 `_relative_links(links, origin)`；`POST /compose` 与 `POST /plan` 接受
   `origin: {x, y}`（处理器的 tile 坐标），把绝对坐标减成相对偏移再打包；`origin` 不是对象时返回 400；
   返回体回显 `origin` 便于对账。
2. `main.js` 新增 `originOf(b)`（`b.tile` 存在就给 `{x, y}`），`/plan` 与 `/compose` 两个请求体都带上。
3. 测试加两条：带 origin 时 `msch.parse_logic(..., relative_to=...)` 必须还原出绝对坐标、裸 parse 得到相对偏移；
   写入路径把目标处理器另放到 `base + (16,16)`（`(0,0)` 处绝对=相对，测不出这个 bug），四个链接方块就位后
   回读 `name>block` 必须全部解析，**负控**是同一组绝对坐标不带 origin 再写一次、必须出现 `>null`。

不传 `origin` 时行为不变（原样透传，视作已经是相对坐标），老的调用方不会被这次改动破坏。

## v0.4.7：审查栏的行内箭头 —— 以及「有链接也报无链接」的真凶

用户要的交互是：哪一行有问题，就在那一行贴个箭头，点箭头看这一行的原因。

### 为什么是覆盖层，不是往原版行里插一个格子

Arc 的 `Table.cells` 是私有字段（`arc/scene/ui/layout/Table.java:35`），插不到行内 `addressLabel` 前面；追加到行尾又会被行内按钮挤。所以做成一个铺在 `LCanvas.statements` 父容器上的 Table：箭头是它的普通孩子（`addChild`，不是 cell），手动摆位，`host.update()` 每帧跟着布局重算。

三条依据：

* `LCanvas.statements` 是 public 字段（`LCanvas.java:32`），子元素按语句顺序排；每个 `StatementElem` 的表头行高 38（`LCanvas.java:427-491`）。
* quickcheck 的 `finding.line` 是 1 起的语句序号（`quickcheck.js:97`），所以第 i 个孩子对应 `line = i + 1`。
* 覆盖层用 `Touchable.childrenOnly`（`arc/scene/event/Touchable.java`）：空白处不拦鼠标，原版画布照常拖行、点按钮；只有箭头自己被命中（`Group.hit` 先测孩子，`Element.hit` 对非 enabled 返回 null）。

箭头横向优先放进行左侧的空白（`statements.x + e.x - 18`），没有空白就压进行内左端（`+2`）；纵向取表头行中心。颜色 ERR 红（`Pal.remove`）/ WARN 橙（`Pal.lightOrange`）/ INFO 蓝（`Pal.accent`），同一行多条取最严重的那条，点开列出全部。

无头引擎没有图集（`Icon.right` 是 null，`new Image(null)` 还会因为 4 个重载歧义直接抛），所以找不到图标时只少画箭头，审查栏与统计照常工作。

### 「有链接也报无链接」的真凶：`LogicDialog.executor` 是包私有字段

真 v160.7 反射实测：`LogicDialog` 的字段可见性是 `canvas:public, consumer:pkg, privileged:pkg, executor:pkg, globalsDialog:pkg, wasRows:pkg, wasPortrait:pkg, forceRestart:pkg`。Rhino 只暴露 public 成员，所以 `L.executor` 读出来是 `undefined`（不是 null），取 `.build` 抛 TypeError，被 try/catch 吞掉 → `linkNames()` 返回空数组 → 快检把每个链接槽里的名字都判成「没链接」。

两处修：

1. `logicExecutor()` 走反射：`Class.forName("mindustry.logic.LogicDialog")` → `getDeclaredField("executor")` → `setAccessible(true)` → `get(L)`，再读 public 的 `ex.build`（`LExecutor.build` 是 public，`LogicBlock$LogicBuild.links` 也是 public）。
2. 「没有链接」和「读不到链接表」必须分开：`linkNames()` 读不到时返回 `null`（不是 `[]`），`quickcheck.check()` 收到 `null` 就整段跳过链接槽判据，并在 `stats.linkKnown` 里记下来；审查栏统计行显示「链接 ?（读不到处理器）」而不是「链接 0」。

真引擎对照探针（`out/_v47_probe.py`）：放处理器、用 `msch.build_logic_data` 写带两条链接的载荷，读回 `links.size=2`，把真链接名喂 `quickcheck.check` ⇒ 零命中；喂空数组 ⇒ 第 1、3 行各一条 WARN。所以快检逻辑本身没错，错的是喂进去的东西。

## v0.7.0：F2 —— 全图处理器清单

之前「哪台处理器有问题」只能一台一台把鼠标挪过去按 F4，或者去控制台敲 `maiScan()` 看一段纯文本。
v0.7.0 把这件事做成面板：

- **F2** 扫一遍全图（`Groups.build` 里用 `isProcessor()` 的鸭子类型筛处理器，和 `targetBuild()` 同一套判据），
  对每台跑一次本地快检，然后按 **ERR 多 → WARN 多 → 坐标** 排序。
- 每行一个按钮：`@x,y  12 行  ERR 2  WARN 1`（干净的写「干净」）。点一行 = 相机跳到那台处理器
  并把面板关掉、直接开 F4 面板 —— 也就是「从清单直接进到能改它的地方」。
- 底部「复制清单」把同样的文本放进剪贴板（`Core.app.setClipboardText`），贴给 AI 或存档都行。
- 面板建不出来时回落成纯文本弹窗；控制台退路是 `maiList()`（文本摘要）与 `maiListRows()`（JSON 行）。

只读：不写方块、不写代码，跑的是和审查栏同一个快检函数（`api.q.check`）。

键位：F2 是这张图上唯一还空着的功能键 —— `Binding.java` 里 F1（方块信息）/F5（电力线）/F6（方块状态）/
F8（控制台）/F11（全屏）/F12（截图）都被游戏占着，F3/F4/F7 是我们自己的。

## v0.6.1：选框偏了半格 —— Tile.worldx() 是格子中心

玩家实测（v0.5.0/v0.6.0）：「选框位置偏右上角越半格」。

根因在坐标口径，不在画法：`Tile.worldx()` 返回的是 `x * tilesize`
（`Mindustry-Source/core/src/mindustry/world/Tile.java:166-172`），也就是**格子中心**的世界坐标；
格子 `(x1,y1)` 的左下角其实是 `(x1 - 0.5) * 8`。v0.5.0 直接把 `r.x1 * 8` 当左下角传给了
`Lines.rect(x,y,w,h)`（它按左下角 + 宽高画），于是整框向右上各偏 4 px = 半格。

原版也是先减半格的：`Placement.java:380-390`
`drawResult.x = result.x * tilesize - block.size * scaling * tilesize / 2`（air：size 1、scaling 1 ⇒ 减 4）。

修法一行：`selDrawArgs(r)` 改成
`{x: (r.x1 - 0.5) * 8, y: (r.y1 - 0.5) * 8, w: r.w * 8, h: r.h * 8}`。

测试：`MASELDRAW` 的期望值跟着改（`(bx+5)*8-4`），并新增源码红线
`(r.x1 - 0.5) * 8` / `(r.y1 - 0.5) * 8` 必须同时出现 —— 少了半格就红。

## v0.6.0：框选之后有面板了 —— 候选链接 + 一键交给 AI

v0.5.0 的 F3 松手只做了一件事：把快照 POST 到 sidecar 落盘，然后弹一段纯文本说「已落盘 xxx.json」。
对玩家来说这等于「框了半天，只得到一个文件路径」。v0.6.0 把松手之后的出口换成**区域面板**：

- 顺序：`POST /snapshot`（落盘）→ `POST /region`（每个处理器 10 格内的可连方块与链接名）→ 开对话框。
- 面板内容：区域摘要（bounds / 方块数 / 处理器数）+ 落盘路径 + 每个处理器的链接候选与
  「代码在用但没绑上」的告警（复用 v0.4.5 的 `missing`）。
- 每个处理器一行按钮「用 @x,y 生成」：点了直接开 F4 的 AI 面板，**并且以那个处理器为目标**
  （`showAiPanel(target)` 新参数），不用再把鼠标挪过去。
- 底部两个按钮：「复制快照 JSON」（`Core.app.setClipboardText`）、「关闭」。
- 面板建不出来时（`pane()` 重载缺失等）回落到旧的纯文本弹窗，不会连候选都看不到。

代码位置：`buildRegionTable()` 在脚本顶层（只碰 table 接口，能用假表在无 UI 环境数行数），
`showRegionPanel()` / `buildAt()` 在引擎作用域里。`dumpRegion()` 从「一次请求 + popup」
改成「两次请求串起来 + 面板」。

测试：ui smoke 的 `maiSelfTest()` 现在多建一张区域表（假表 8 行），并新增四条源码红线
（`buildRegionTable`/`showRegionPanel`、`buildAt`+`showAiPanel(b)`、`labelWrap(String(candText))`、
`function showAiPanel(target)`）。无头引擎里 F3 那条路径本来就直接返回摘要、不发请求，所以面板只在真机上出现。

## v0.5.0：F3 就是鼠标左键，高亮改成原版选框样子

用户原话（m11493）：「框选区域是ohno，尝试做成原版的矩形选框风格。而且我要的是按下快捷建后就直接拉矩形，相当于f3就是鼠标左键。」

两件事：

1. **F3 是按住式的左键，不再有「就绪」这个中间态。**
   按住 F3 = 按下左键（起点 = 此刻鼠标格），移动鼠标改终点，**松开 F3 = 抬起左键并出快照**。
   v0.4.9 的“按 F3 就绪 → 再按住左键拖”已经去掉：框选不再碰鼠标左键。
2. **高亮照抄原版选框**（`InputHandler.java:1758-1795` `drawSelection`）：
   `Lines.stroke(2)` 两次描边，先 `Pal.accentBack` 画一条 `y-1` 的阴影，再 `Pal.accent` 画本体，
   坐标用**左下角 + 宽高**（`Lines.rect(x,y,w,h)`）；另外在光标旁写「宽x高 (面积)」
   （`mindustry.ui.Fonts.outline` + `1/camerascale` 缩放 + `Draw.z(Layer.endPixeled)`，画完逐项还原）。
   原版**没有半透明填充**，所以 v0.4.8/v0.4.9 那个 `Draw.alpha(0.35)` 的方块去掉了。

顺带修掉一个潜在错误：`Fonts` 是 **`mindustry.ui.Fonts`**，不是 `mindustry.gen.Fonts`
（`out/_server160.jar` 里只有 `mindustry/ui/Fonts.class`）—— 写错包名会被 `catch` 吞掉，字永远画不出来。

测试：`tests/mlogauxiliary/run_ui_smoke.py` 的 `select_probe()` 直接驱动状态机
（`maiSelPress` 就是按下、`maiSelRelease` 就是抬起，中间没有 arm），并用反射钉住
`Lines.rect(float,float,float,float)` / `Lines.stroke(float)` / `Draw.color(Color)` / `Pal.accentBack` / `mindustry.ui.Fonts.outline`；
源码红线：必须有 `L.stroke(2);`、`Pal.accentBack`、`function drawSizeText(`、`Core.input.keyDown(selKey)`，
不得出现 `selArmed`、`D.alpha(0.35)`、`keyTap(Packages.arc.input.KeyCode[KEY_SELECT`。

## v0.4.9：修掉 F3 的两个手感 bug

v0.4.8 装进游戏后用户立刻报了两条，都是真 bug：

1. **按 F3 弹出提示框，结果拖不动。** 提示用的是 `showText`（Dialog），而 Dialog 会吃掉鼠标
   （`Core.scene.hasDialog()` 为真，世界收不到点击），于是「就绪提示」本身把框选废了。
   现在改成 `showInfoFade`（`Mindustry-Source/core/src/mindustry/core/UI.java:373`，
   `Touchable.disabled` 的淡出标签，不挡输入），而且**按 F3 只置就绪、什么都不弹**。
2. **预览框的中心落在指针上。** `Draw.rect(region, x, y, w, h)` 的 x,y 是**中心**不是左上角
   （`Arc-Source/arc-core/src/arc/graphics/g2d/Draw.java:378`：`batch.draw(region, x - w/2f, y - h/2f, …)`），
   v0.4.8 传的是角点，框就被画到指针的左上。现在传 `(x1 + w/2) * 8` 这样的中心坐标。

顺手改了一处语义：**拖拽起点取「按下左键的那一格」**，不是按 F3 的位置 —— 否则按完 F3
鼠标还没动就已经有一个框，松手就是 1×1 的「以指针为中心」的小方块。只点一下不拖会提示
「没有拖动」，不再落盘。

控制台新增拖拽状态机的测试钩子：`maiSelState()`、`maiSelPress(x,y)`、`maiSelMove(x,y)`、
`maiSelRelease()`、`maiSelDraw(x1,y1,x2,y2)`；断言见 L2-37。
## v0.4.8：F3 拖拽框选 —— 框选矩形终于能自己画，快照直接落盘

规划里 F7 一直是「框选矩形」（`docs/Mlog辅助-规划.md:99`），但 v0.4.2 只落地了只读的一半：
以鼠标下的处理器为中心扫固定 10 格。v0.4.8 把拖拽补上，但**没有用 F7 也没有用 F8** ——
游戏里 F8 是控制台（`Mindustry-Source/core/src/mindustry/input/Binding.java:107`
`console = KeyBind.add("console", KeyCode.f8)`），F9/F10 也被占，所以框选落在 **F3**。

用法：按 **F3** 进入就绪 → 按住左键拖出矩形（半透明高亮）→ 松手弹摘要。再按 F3 取消。

- 高亮画在**世界坐标**里（`Events.run(ET.Trigger.draw)` + `Draw.rect(Tex.whiteui, …)`），
  不往场景树里塞元素 —— v0.4.1 那次「点生成就崩」就是自造结果区引起的，能画的地方就不建 UI。
- 松手先给区域摘要（方块数 / 处理器数 / 每个处理器的链接），**不依赖 sidecar**；
  再把快照 JSON `POST /snapshot` 落盘成 `out/snapshots/snap-<时间>-<sha1 前 8>.json`，
  弹窗里补一行「已落盘 <路径>（N B）」。sidecar 没起也能看摘要，只是不落盘。
- `selRect()` 只做归一化（从右下往左上拖 = 同一个矩形），裁到地图边界仍由 `regionSnapshot()` 负责。
- 无头引擎（`Vars.ui === null`）不发请求，只返回摘要 —— 自检不该连网络。
- 控制台：`maiSelect()`（等同按 F3）、`maiDump(x1,y1,x2,y2)`（直接出摘要并落盘）、
  `maiSelRect(ax,ay,bx,by)`（拖拽数学，测试钩子）。
## 接口契约（sidecar v1）


| 方法 | 路径 | 请求 | 响应 |
| --- | --- | --- | --- |
| GET | `/health` | – | `{ok, protocol}` |
| GET | `/capabilities` | – | `{ok, protocol, game, instructions, ops, templates[], limits{ipt_max, link_range_tiles}}` |
| POST | `/analyze` | `{code, links, ipt}` | `{ok, findings[{sev,line,stmt,rid,msg}], errors, warns, statements, cost}` |
| POST | `/compose` | `{template, params, links, ipt}` | 同上 + `{template, code, links, bytes_b64, bytes_len}` |
| POST | `/plan` | `{intent, links, ipt}` | `/compose` 的全部字段 + `{intent, params, reason}`；没命中时 `{ok:false, template:null, reason, candidates[]}` |
| POST | `/region` | `{snapshot}` | `{ok, bounds, cells, truncated, processors[{x,y,block,links[],statements,in_range,used_unlinked,candidates[{name,block,x,y,dist,used}]}]}`；**不写文件、不生成代码** |

* `ok` 的语义是 **没有 ERR**。有 ERR 时模组拒绝写入，WARN/INFO 照常写入但会列在面板上。
* `findings[].line` 是代码里的行号（1 起），`stmt` 是指令槽位序号 —— 两者不同，因为标签行不是语句
  （`LParser.java:117-125`）。
* 模板声明要用某个链接名而请求里没有 → 服务端补一条 `rid=template-needs-link` 的 ERR。

## 游戏内快检（P2）

`scripts/quickcheck.js` 是纯函数、无游戏依赖的 ES5，回答五类**单行**问题：指令是否存在、
`ucontrol`/`draw`/`ulocate` 子命令是否拼错（拼错整行会被解析成 `NoopI`，静默不执行）、
是否用到比当前 build 更新的指令、链接槽里的名字是否真的连着、语句数是否超过 1000（尾部会被截断）。

规则表 `scripts/rules.generated.js` 由 `python tools/rules_export.py` 从
`tools/instr_semantics.json` + `tools/mlogcheck.py` 生成；`gate.py` 跑 `--check` 防漂移，
`tests/mlogauxiliary/` 跑 14 个用例、`require()` 契约、以及「quickcheck 说断链时全量检查也必须同意」的单向验证。

真 Rhino 与 node 的**逐条比对**是独立一步：`python tests/mlogauxiliary/run_rhino_parity.py`
（无 JRE 时 SKIP）。理由是真 v160.7 的 Rhino 里 `"abc def".split(/\s+/)` 会按**每个字符**切开
（带 `+` 量词的正则在它的 `String.prototype.split` 里等价于空匹配，只有单字符模式正常），
node 侧永远发现不了 —— 所以本文件的分词、裁剪、标识符判断全部手写扫描，不用 `split(正则)`。

两条源码事实（v160.7 实测）：

* 游戏只执行 `scripts/main.js`（`Mods.java:809`），其余文件必须 `require()` 进来；
  `Scripts.java:30-32` 装了 CommonJS 模块提供器，实测 `typeof require` 是函数。
* 版本号取 `Packages.mindustry.core.Version.build`（`Version.java:22`，自定义构建是 `-1`，
  此时版本门不启用）。

**边界**：快检只许少报，不许瞎报。未赋值变量的槽位分级、成本 CFG、值域这些需要数据流
推理的判据不在游戏内，仍由 sidecar 回答。

## 明确没做

* 撤销只在内存里，不落盘（P3：`<dataDir>/mlogauxiliary/undo/`）
* 没有 diff 预览，整段替换（P3）
* 框选只做到「读」：F7 扫的是鼠标周围固定 10 格（`maiRegionAround(r)` 可换半径），没有拖拽矩形、也没有队列
* 自然语言已经能用，但只是**关键词路由**：`/plan` 的 `_route()` 是规则表，没接模型（P4）
* 多处理器批量写入与撤销落盘（P5）：区域快照只回答「能连什么」，不生成代码
* 真界面的**像素**没法机器验证（无头模拟器里 `Vars.ui` 是 null）：`run_ui_smoke.py` 只验到
  「main.js 整段初始化不抛错 + 设置表格能建到假 Table 上 + 页面用到的每个 Table 方法在真引擎里能解析」，
  按钮点下去的实际效果、这一栏在设置菜单里的位置与排版仍要人看
* 两个面板的模板按钮只用默认参数（改参数走控制台 `maiCompose(id, paramsJson)` 或 AI 面板的一句话）
* AI 面板只覆盖六个模板能表达的意图，多处理器 / 多步流程它做不到
