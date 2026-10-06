# DP-副官调试插件（Adjutant Debug）v3.3

一个**真正需要加载的模组**：`mod.hjson` + `scripts/main.js`，由游戏脚本引擎（Rhino）执行，全局生效、不绑定地图。

```
DP-AdjutantPlugin/
├── mod.hjson          ← 模组元数据
├── icon.png
├── scripts/main.js    ← HUD 面板 + 控制台 API + 联机聊天命令 + 热键
└── README.md
```

---

## 0. ⚠ 你机器的三个"环境事实"（踩过坑，务必先看）

### 0.1 你的数据目录是**游戏目录下的 `saves\`**（便携模式），不是 `%APPDATA%`

- 真正生效的模组目录：`E:\Program Files (x86)\Steam\steamapps\common\Mindustry\saves\mods\`
- 真正生效的日志：同目录下 `saves\last_log.txt`（最新一次运行，2026/10/3 2:09）
- `%APPDATA%\Mindustry\` 里那份是 **7 月的旧数据**（`last_log.txt` 停留在 2026/7/8），
  之前照着它排查，得到的是过期结论（"版本 159.1"其实来自旧日志）。

> 判断哪份生效的最快方法：比较两个 `last_log.txt` 的时间戳。

### 0.2 单机**没有聊天栏**

- `ChatFragment.visible()` = `net.active() && ui.hudfrag.shown`，而 `Net.active()` 只在联机时为真
  （单机不调 `net.host`，只有 PVP 地图会自动开服 —— `Control.java:149`）。
- 单机按 `Enter` 打开的是**脚本控制台**（`ConsoleFragment`），它把输入交给
  `mods.getScripts().runConsole(...)`（`ConsoleFragment.java:208`）→ **当 JavaScript 求值**。
- 所以在控制台里写 `/adj help` 报 `unterminated regular expression literal`（`/` 当正则起始），
  写 `!adj help` 报 `missing ; before statement`（`!` 是一元非）——**都不是模组的问题**。
- 正确用法：**HUD 面板**（本版主入口），或控制台里的 JS 形式 `adj.help()`。

### 0.3 三条 Rhino 铁律（都在你机器上跑通的模组 / 真实日志里验证过）

| # | 规则 | 反例（会炸） | 正例 |
|---|---|---|---|
| 1 | **按键必须写全限定名** | `KeyCode.F7` → `EvaluatorException: Java class "arc.input.KeyCode" has no public instance field or method named "F7"` | `Packages.arc.input.KeyCode.F7`（本机跑通的模组就是这么写的） |
| 2 | **同名字段遮蔽方法** | `unit.health()`、`unit.team()`、`build.size()`、`b.dead()` | `unit.health`、`unit.team`、`Groups.build.size`（字段）；而 `player.team()`、`heal()`、`kill()`、`within()`、`isValid()` 是方法 |
| 3 | 回调可直接传箭头函数 | 不必要 | `Events.on(ClientLoadEvent, () => {})`、`Groups.unit.each(u => {})`、`Timer.schedule(() => {}, 2, 2)` |

**v1.0~v1.3 全部失效的原因就是第 1 条**：`KeyCode.F7` 在**顶层配置区**抛异常，整个脚本从那一行中止 ——
面板、控制台 API、热键一个都没生效。v1.4 不但改用全限定名，还把初始化拆成多个 `try`，
并在日志里打印 `副官调试插件：事件已注册，加载完成` 这样的标记，**任何失败都会留下痕迹而不是静默死亡**。

---

## 1. 安装与加载

1. 把 `DP-AdjutantPlugin.zip` 放进 `...\Mindustry\saves\mods\`（见 0.1；`%APPDATA%` 那份也放一份更保险）。
2. 游戏内 **「模组」** 确认「副官调试插件」是启用状态（新模组默认启用）。
3. **重启游戏**（「重载模组」= 退出重进）。
4. 进任意地图 → 屏幕**左侧**出现「副官调试面板」。

**怎么确认加载成功**（看 `saves\last_log.txt`）：

```
[I] Loading mod: adjutant-debug
[I] [adjutant-debug/main.js]: 副官调试插件：控制台 API 已发布（输入 adj.help()）
[I] [adjutant-debug/main.js]: 副官调试插件：事件已注册，加载完成
[I] [adjutant-debug/main.js]: 副官调试插件：HUD 面板已注入
```

有任何 `[E] ... main.js#行号` 就是出错，把那几行发我即可精确定位。

## 2. 调试项（在「设置」→「副官调试」页）

调试面板**不再是 HUD 浮窗**，而是挂在设置里的一页；游戏内按 `F6` 直接打开设置。
（`SettingsMenuDialog` 的 categories 只做 append、显示时不清空，所以启动时加一次就长期有效。）

| 区域 | 按钮 | 作用 |
|---|---|---|
| 单位 | `◀ ▶` | 循环切换单位（含所有模组单位） |
| | `生成 x1` `x5` `x20` | 在**鼠标位置**生成选中单位 |
| 战场 | `修理/治疗` | 修理/治疗周围 40 格内己方建筑与单位 |
| | `清除敌人` | 清除所有敌方单位 |
| | `下一波` | 立刻开始下一波 |
| 开关 | `自动副官` | 自动修理 + 玩家单位持续回血 + 每 2 秒补料 |
| | `日志` | 波次开始 / 己方建筑被摧毁时输出提示 |
| | `沙盒作弊` | 无限资源 + 秒建 + 取消单位上限 |
| | `波次` | 关掉就不会再刷怪（安静测试） |
| | `补料` | 往核心塞 21 种基础物品各 1000 |
| 物品 | `◀ ▶` `给1000` | 选物品并往核心塞 1000 |
| 状态行 | — | 波次 / 我 / 敌 / 建筑 / FPS（自动刷新） |

## 2.5 副官通讯窗（复刻逻辑处理器版副官）

进图后出现在屏幕约 60% 处（可拖动，位置会记住）：

| 元素 | 行为 |
|---|---|
| 头像 | 拖动它移动整个窗口；鼠标悬停时显示名字「喻晓暮」 |
| 头像 | 5 张表情图已**打包进模组**（`sprites/yumu*.png`，区域名 `adjutant-debug-yumu*`），
          取图顺序：模组自带 → 数据包的 `dp-Yumu*` → 单位图标；按 64:71 比例显示、不会被拉变形 |
| 位置 | **以头像为基准（框架级做法）**：消息框的**高度在每条消息开始时按整句量出并定死**（`adjBoxCell.height(...)`），文本 Cell 用 `.top()` 贴框顶向下生长，悬停名字行也是固定高度 —— 于是打字/换行/悬停全程**窗口尺寸不变，头像纹丝不动**。跨消息的高度变化由锚点 `posX/posTop`（每帧按锚点摆放窗口）处理。拖动**头像或名字**整块即可移动，锚点写入设置。原因见下：位置只有一个来源——锚点 `posX/posTop`（`posTop` 就是头像上沿）。窗口每帧按锚点摆放，所以打字换行、消息收起时**头像一动不动**，只在下方长出/收回文本框；拖动**头像或名字**（整块）即可移动，松手后锚点写入设置。因为拖动改的是锚点、摆放也读锚点，二者不会互相抢位置 |
| 表情 | 与你的逻辑版一致：`怎么了/什么事`→confused，`敌方尚无动向`→working，`我在/空想误国/点击消息框`→normal，
          `装填钛`→gracias，开场白→gracias |
| 眨眼 | **照逻辑版移植**：90ms 节拍轮询、10% 概率触发、眨眼保持 90ms 后恢复当前表情；
          触发后下次检查 4000±2000ms，未触发则 200±50ms |
| 文本框 | 打字机逐字显示（25 字/秒，带打字音）；**点击** = 打字中快进，已打完则移除 |
| 台词 | 开场白 2 句（含你的指挥官名）→ 之后随机闲聊 9 句（不连着重复同一句） |
| 节奏 | 打字 25 字/秒 → 打完停留 5~24 秒 → 收起后空闲 6~12 秒再来一句；没消息时不显示空文本框 |
| 开关 | `F5`，或面板上的「副官窗」按钮 |

头像贴图取自你数据包的 `dp-Yumu` / `dp-Yumu-working` / `dp-Yumu-confused` / `dp-Yumu-blinking` /
`dp-Yumu-gracias`（就是 `content/blocks/Yumu*.json` 对应的 sprite）。
**没导入数据包时**会自动退回单位图标，不会报错。

```js
adj.line("自定义台词")   // 让副官说一句
adj.lines()              // 随机台词
adj.avatar(false)        // 收起副官窗
```

### 怎么区分「模组的框」和「逻辑处理器的框」

如果你同时还开着逻辑处理器版副官，屏幕上会有两个框，别搞混：

| | 模组版（本插件） | 逻辑处理器版 |
|---|---|---|
| 位置 | **紧贴在头像下方** | 由 marker 定位（默认也在屏幕 60% 附近） |
| 外观 | 圆角深色面板（`Styles.black3`） | **灰色方框（`quad` + `%484848` + outline）** |
| 附加物 | 没有任何世界标记 | **金色 X / 斜线 / 小地图点**（`id.Frame.button`、`id.Line.Pinglocation` 等 marker） |
| 文本来源 | `Label` 渲染，颜色标记原生支持、自动换行 | `setmarker flushText`，逐字 `printchar` 拼 `message1` 缓冲 |

看到"重复一个字"这类问题，先看框上有没有金色 marker：有 → 那是逻辑版的（它的 `printchar`/`printflush` 缓冲时序会出这种问题）；
模组版的文本**永远是原文的前缀**（前缀查表法，见下），结构上不可能重复字符。

设置页里有 **「打字机自检」** 按钮：它用一句包含数字、字母、中文的固定文本单独验证模组打字机；
控制台也可以 `adj.type("任意文字")`。

### 用到的引擎 API（不照搬逻辑版的算法）

逻辑版的效果是参考，实现全部改用 Mindustry/arc 现成的高层接口（都已核对源码存在）：

| 效果 | 用的引擎 API | 之前（照搬逻辑版思路） |
|---|---|---|
| 窗口淡入 | `Actions.fadeIn(0.35f)` + `Element.addAction` | 自己每帧累加 alpha |
| 头像出场"弹一下" | `setOrigin(Align.center)` + `setScale(0.5)` + `Actions.scaleTo(1,1,0.32f, Interp.swingOut)` | 逻辑版的 `textureSize` 缓动 |
| 悬停显示名字 | `Actions.fadeIn/fadeOut` + **固定高度 cell** | `visibility` 切换（会改变尺寸） |
| 打字停留后收起 | `Timer.schedule(runnable, delay)` → 返回可 `.cancel()` 的 `Task` | 每帧轮询 `holdUntil` |
| 眨眼 | `Timer.schedule` 递归排程 + 90ms 后恢复 | 90ms 节拍自算概率 |
| 文本按顶对齐生长 | **`Cell.height(h).top()`**（固定高度 + 顶部对齐） | 每帧挪窗口补偿 |
| 位置管理 | 锚点 `posX/posTop`（拖动写锚点、每帧按锚点摆放） | 拖动与钉住互相抢坐标 |
| 旋转（菱形框，未做） | `Element.setRotation(45)` / `Actions.rotateTo` | 逻辑版的 `shape 4` + `rotation 45` |

### 为什么必须"固定高度 + 顶部对齐"

arc 的 `Table` 每次布局都按内容**重算自身尺寸**（`getPrefHeight()` → 设为自身高度），而子元素相对表底定位 ——
**只要高度会变，整个窗口就会重排、头像必然被推走**。靠"每帧把窗口挪回去"永远晚一帧（布局发生在绘制阶段），
所以看起来就是"头像没定住"。

框架里"顶部基准的文本展示"就是：**给容器固定高度，文本 cell 用 `.top()` 对齐**。
本项目做法：每条消息开始时先把整句临时塞进 Label 量出所需高度 → `adjBoxCell.height(boxH)` 定死 → 清空再开始打字。
跨消息（开始/收起）的高度变化由锚点 `posX/posTop` 处理：拖动写锚点、每帧按锚点摆放窗口，二者不抢位置。

**打字机实现（v1.9 起）**

三种做法的取舍（为什么不是"每帧截断重排"）：

| 做法 | 问题 |
|---|---|
| 逻辑版：每字 `printchar` + `flushText` | 每字重排、缓冲时序易错（就会出现"重复一个字"那种现象） |
| 逐帧截断字符串交给 `Label` | 文本每帧重排 → **换行位置会变**，字会突然跳到下一行、框会抖 |
| **先排版一次 + 按索引露出**（本模组 v1.9） | 用 `GlyphLayout(Fonts.def, s).width` 量宽度，先把整句断行固化进字符串（`wrapStyled`，颜色标记不占宽度、英文单词尽量不从中间断），之后打字只是按可见字数取前缀 → **行位置从第一个字就固定**；消息变高时保持窗口上沿不动 |
| 引擎级 glyph reveal（最正统） | arc 的 `Label` 没有"只画前 N 个字形"的 API；要自己遍历 `GlyphLayout.runs` 画字形并处理颜色/翻转，风险大收益小 —— 需要的话可以再实现 |：预先算好"打出 k 个可见字符时应截到哪个下标"（`buildCuts`），
每帧只做 `text.substring(0, cuts[k])` 取前缀；已显示字数由经过的 tick 数唯一决定（纯函数、单调递增、钳制）。
颜色标记 `[xxx]` 并入它前面的截断点，所以不会出现"半截标记"被当文本显示。

**与逻辑版的差别**：逻辑版用 marker + 相机坐标换算把 UI 画在世界里（每帧换算、要管 8 个 marker、
跟随相机会抖、文字没有自动换行）；模组版是真正的 Scene UI 元素（自动跟随屏幕、自动缩放、
颜色标记与换行由 Label 渲染）。
**暂未复刻**：`id.Pinglocation` / `id.Line.Pinglocation`（地图 ping 点与指向线）、菱形边框（用圆角面板代替）。

## 3. 热键

`F5` 开关副官窗 · `F5` 开关副官窗 · `F6` 打开设置 · `F7` 生成 1 个副官 · `F8` 清除敌人 · `F9` 自动副官 · `F10` 事件日志

（若某个键在你的版本里解析失败，日志会写 `热键 Fx 解析失败，已跳过`，模组其余功能照常。）

## 4. 另外两个通道（可选）

**脚本控制台**（单机按 `Enter`）——控制台和模组脚本共享同一个 Rhino scope，本模组把 API 挂在全局 `adj`：

```js
adj.help()      adj.spawn("flare", 5)     adj.heal()      adj.give("copper", 10000)
adj.kill()      adj.wave()                adj.waves(true) adj.auto(true)
adj.log(true)   adj.cheat(true)           adj.panel(false) adj.report()
adj.resetPos()                            // 面板跑偏了？把它复位到屏幕左侧中间
adj("spawn flare 5")                      // 字符串形式，和聊天命令同一套解析
```

控制台还预置了 `unit` `player` `team` `core` `items` `build` `cursor` `cursorUnit` 可直接用
（`ConsoleFragment.injectConsoleVariables()`，这也是报错行号总从 `#2` 起的原因）。

**聊天栏**（仅联机）：`!adj help`、`!adj spawn flare 5`（`/adj ...` 也行，但原版会多回一行 Unknown command）。

## 5. 配置

`scripts/main.js` 顶部配置区：`CMD` / `CMD_ALT` / `API_NAME`、`DEFAULT_UNIT`、`MAX_SPAWN`、
`HEAL_RADIUS`、`HEAL_EVERY`、`FEED_EVERY`、`FEED_AMOUNT`、`PANEL_W`、`FEED_ITEMS`。
热键那几行是 `Packages.arc.input.KeyCode.xxx`，改键就改这里。

## 6. 版本记录

| 版本 | 改动 |
|---|---|
| 1.0 | 联机聊天命令 + 热键 + 自动副官 |
| 1.1 | 修 `PlayerChatEvent` 双触发导致的开关抵消；加权威侧门控 |
| 1.2 | 发现单机没有聊天栏 → 发布控制台 API `adj.*` |
| 1.3 | 加 HUD 面板；修正"字段当方法调用"；改用箭头函数回调 |
| **1.4** | **修致命问题**：`KeyCode.F7` 裸名解析失败导致整个脚本中止 → 改全限定名 + 分层 try + 日志标记；安装位置修正为 `saves\mods\`；`Groups.build.size()` → 字段 |
| **3.3** | **去掉头像窗底板**：窗口不再画背景（原来 300×122 的 `Styles.black6` 面板就是头像后面那块深色底板），宽度收窄到 104（头像框 92 + margin 12）；消息框宽度仍 300，改为相对头像居中并加屏幕边界夹取 |
| **3.2** | **几何全部改为常量**：头像窗尺寸写死为 `ADJ_WIN_W/ADJ_WIN_H`（边框 92 + 名字 18 + margin 12）并显式 `setSize+validate`，每帧摆放 / 消息框定位 / 夹边全部由常量算出，不再回读 `getHeight()`（场景根 Table 的布局时序不可靠，正是"基准偏上"和"盖住头像"的共同根因）。新增 `ADJ_GAP`（默认 2px）微调间隙 |
| **3.1** | **修消息框盖住头像**：独立框是普通 Table，摆放时 `getHeight()` 仍为 0 → 退化成"底边对齐"，而它按自然尺寸**向上**绘制 → 正好压在头像上。现在高度**自己算**（行数 × 24，再用 Label 的 `prefHeight` 校正并钳制），`setSize + validate` 后再摆放，第一帧就贴到头像窗下沿 |
| **3.0** | **矩形描边框**取代菱形（`Stack` + `setOrigin(Align.center)` 在尺寸为 0 时调用 → 原点落在角上，旋转变成"绕角飞出去"）；删掉消息框左侧竖线；**消息框拆成独立元素**（可自由伸缩，不再固定尺寸、不再截断），头像窗尺寸恒定 |
| **2.9** | **头像基准彻底固定**：消息框高度改为常量 `ADJ_BOX_H`（超出 6 行截断加省略号），没消息时只把背景设透明、**占位保留** → 窗口尺寸在整个会话中恒定，头像不再依赖任何每帧补偿。**新增菱形描边框**（Stack + 两个 45° 旋转方块叠出描边，`Actions.forever + rotateTo` 缓慢自转，转 90° 与自身重合故接缝不可见） |
| **2.8** | **改用引擎高层 API**（不再复刻逻辑版算法）：`Actions.fadeIn/scaleTo`（窗口淡入、头像出场弹跳）、`Timer.schedule` + `Task.cancel()`（停留收起、眨眼排程）、`Cell.height().top()`（顶部基准）、锚点定位 —— 见上文「用到的引擎 API」表 |
| **2.7** | 悬停名字行改为固定高度（显隐不再改变窗口尺寸） |
| **2.6** | **改用框架的"顶部基准"做法**：消息框高度按整句量出并定死 + 文本 cell `.top()` → 打字全程窗口尺寸不变，头像不再被推走 |
| **2.5** | **修拖动与定位两个真 bug**：① `Image` 默认 `touchable=disabled`（libGDX 行为）→ 挂在头像上的拖动/悬停监听器从未收到事件；现已显式打开并把拖动挂到头像+名字整块。② 位置原来有两个来源（拖动改窗口坐标 + 每帧钉住再改一次）→ 纵向被抢回原位、回弹；现改为**锚点唯一来源** |
| **2.4** | **以头像为基准**：窗口上沿持续钉住（原来只在尺寸变化瞬间补偿一次，有一帧延迟与取整漂移）→ 换行时头像完全不动；拖动期间暂停钉住，松手后更新基准 |
| **2.3** | **头像与表情**：5 张 `yumu*` 表情图（取自你的数据包 `sprites/Yumu*.png`）打进模组 `sprites/`；按 `adjutant-debug-yumu*` 三级兜底取图；按 64:71 显示；移植逻辑版的眨眼调度；模组图标换成 Yumu |
| **2.2** | **修字符串被改写成第一个字**（日志证据：长度对、字符全是首字；46 字被撑成 312 字）→ `wrapStyled`/`buildCuts` 里的 `charAt` 换成 `substring(i,i+1)`、循环内 `const` 换成 `var`；新增**断行自检 + 回退**（宁可少排版也不显示坏字） |
| **2.1** | 加按键探针日志：查出这一版 `KeyCode` 的功能键是**小写常量**（`f5 f6 f7 f8 f9 f10`） |
| **2.0** | 修两处静默失效：热键大小写两种都试；控制台 API 改用 `ScriptableObject.putProperty()` 发布（原来 `scope.put` 不可用）；消息框加青色左边条便于区分模组框/逻辑 marker 框；加打字机诊断日志 |
| **1.9** | **打字机排版优化**：先用 `GlyphLayout` 按字体真实宽度把整句断行固化（`wrapStyled`），打字时行位置固定、不再跳行；消息变高时保持窗口上沿不动 |
| **1.8** | **打字机重写**：改为前缀查表法（先算好每个可见字符的截断下标，每帧只取 `substring` 前缀）→ 结构上不可能出现重复/乱序字符；显示字数由 tick 数唯一决定；设置页新增「打字机自检」按钮，控制台新增 `adj.type("文字")` |
| **1.7** | **修时间单位错误**：Mindustry 的 `Time.delta/Time.time` 单位是 **tick** 不是秒（`ClientLauncher: setDeltaProvider(() -> getDeltaTime() * 60f)`），我把"停留 5~8 秒"写成 5~8 tick → 对话框 0.1 秒消失、疯狂切换、反复重播同一句。现在统一 ×`TPS(60)`。**调试面板移入「设置」→「副官调试」页**，浮动面板及其拖动/折叠/位置保存/自愈定时器全部删除，`F6` 改为打开设置 |
| **1.6** | **新增副官通讯窗**（复刻逻辑处理器版：头像/悬停名字/打字机/点击快进移除/拖动记忆位置/表情闪烁/开场白与闲聊，F5 开关） |
| **1.5** | **修面板叠加**（`getChildren().contains()` 在 Rhino 下恒为 false → 每 2 秒重复注入；改成 `contentTable.parent != null` + 注入前 `remove()`）；**面板可拖动**（挂到 `Core.scene` 场景根，位置不被布局重置；拖动算法照 arc `Dialog`；位置存 `Core.settings`）；`adj.resetPos()` |

参考：本地克隆的官方 v159.3 源码（[ChatFragment.java](../Mindustry-Source/core/src/mindustry/ui/fragments/ChatFragment.java)、
[ConsoleFragment.java](../Mindustry-Source/core/src/mindustry/ui/fragments/ConsoleFragment.java)），
本机 `saves\mods` 里已跑通的 JS 模组（Ferlern extended-UI、Resource Rate Monitor），
以及 `jre\desktop.jar` 的 class 常量池核对结果（`Table`/`Cell`/`Element`/`WidgetGroup`/`Styles` 的成员名）。

> 你实际运行的是 **官方 160.5 的 `jre\desktop.jar` + MindustryX**（日志 `[Mindustry] Version: 160.5`）。
