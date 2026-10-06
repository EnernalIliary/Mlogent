# 自由视角修复（Camera Unbind）v5.4

Mindustry 脚本模组（`mod.hjson` + `scripts/main.js`，Rhino 执行）。

> 📘 **想了解"怎么做出这类模组"（而不是"这个模组怎么用"）请看 [METHOD.md](METHOD.md)**
> —— 那份是方法论：怎么查反汇编、怎么用 `JavaAdapter` 覆写核心方法、
> 怎么做 `hidden` 免装、踩过哪些坑，以及全套本地验证工具。
> 本文件（README）只讲**这个模组本身**。
>
> ⚠️ 下面的 1.x / 2.x 章节是 v2.x 时代的分析记录，**部分结论后来被实测推翻**
> （最关键的一条：当时以为"自由视角下原版不会把相机拉回单位"，实测证明你实际
> 运行的那份**会**）。当前行为的权威描述见 §0 与 METHOD.md §3。

## 0. 当前行为（v5.4，以此为准）

**作用**：自由视角下按住「鼠标移动」键拖动时 ——

| 你的操作 | 结果 |
|---|---|
| 只按**移动键**（右键） | 单位走到**鼠标指的位置**停下；**镜头钉住不动** |
| **平移键 + 移动键**同按 | **镜头与单位同时移动**（按平移键时相机交回原版） |
| 按着移动键时**点小地图** | 镜头听玩家的（跳到该处，并以新位置为锚，不弹回旧锚点） |
| 按着移动键时按 **W/A/S/D** | 单位移动、**镜头跟着走**（玩家要动视角，不被钉死） |
| 松开移动键 | 单位靠**惯性滑停**（原版没有"松手"概念，会继续朝屏幕中心飞） |
| 接近鼠标（15 格内） | 停止驱动 → 靠**物理阻尼自然滑行**停住（与原版同机制） |
| **死亡 → 重生** | **落地动画允许走完**（这段完全不插手），**重生后定位回死前视野**（不是停在核心/新单位处） |
| 死亡 / 观战 / 界面打开 | **脚本一个字节都不碰相机**（死亡时只把镜头放到核心一次，与原版一致） |

- 设置位置：**设置 → 图像 → 「自由视角」正下方的那一项**（v3.0 起**默认开启**）
- 前提：**设置 → 图像 → 自由视角** 要开着（这是原版的开关，本模组不动它）
- **触发键**：原版「鼠标移动」默认绑在**鼠标侧键（Thumb Mouse Button / mouseBack）**，
  不是左键；想改用别的键去 设置 → 操作 里改 `鼠标移动`
- 热键：`V` 开关本功能，`N` 立刻把视角拉回单位
- **免装**：`mod.hjson` 里 `hidden: true` —— 自用不影响进任何服务器（原理见 METHOD.md §4）
- **控制台接口**（单机按 `Enter`）—— **顶层全局函数**，没有 `cam` 对象
  （v4.0 起移除了那个冗余副本：实测 `cam.measure` / `cam.drift` 在控制台里取不到，
  同一批挂上去的 `cam.version` 却正常 → 对象属性解析不可靠，全局名才稳）：

  ```
  camVersion()        版本号
  camWhere()          当前状态（JSON）
  camMeasure(6)       实测单位往哪走
  camDrift(6)         抖动诊断（帧间位移统计）
  camHold(true|false) 相机压制开关
  camCursor(false)    单位移动退回原版行为
  camOverride(false)  卸掉 updateMovement 覆写
  camHelp()           全部列出
  ```

**实现方式**：用 Rhino 的 `JavaAdapter` 生成 `DesktopInput` 的子类、
覆写 `updateMovement`，再 `Control.setInput()` 换掉输入处理器 ——
**不需要重新构建游戏**。相机压制则靠"按住移动键期间把 `panSpeed`/`panBoostSpeed`
置 0 + 把相机钉在固定锚点"（都写同一位置，所以不抖）。

---

> 以下为历史分析记录（v2.x）。**已修正的过时结论**：
> §1.1 当时断言"原版自由视角本来就不会把相机拉回单位"——
> 实测表明你实际运行的那份（160.5 / 改端）**会**执行那句 `lerpDelta`，
> 因此 v3.7 起才需要同时压掉"推镜"和"吸回单位"两处。详见 METHOD.md §3。

> **为什么需要 `camera.update()`（v2.1 修的致命 bug）**
> `Core.input.mouseWorld()` 是拿 `camera.inv` 逆投影算出来的，而 `inv` 只在
> `Camera.update()`（`mat.setOrtho` + `inv.set(mat).inv()`）里重算，游戏原本
> 每帧只在 `Renderer.draw()` 里更新一次。我们既然在同一帧里改了 `position`，
> 就必须自己再 `update()` 一次 —— 否则 `mouseWorld()` 会用"漂移相机 + 鼠标像素"
> 解出错误的世界坐标，表现就是**看着完全没生效**。这条现在有专门断言守着。

---

## 1. 它到底改了什么（对着 160.5 的反汇编说）

### 1.1 先说清楚：原版自由视角**本来就不会**"把相机拉回单位"

`DesktopInput.update()`（用 `javap -c` 从你正在跑的 `jre\desktop.jar` 出来，偏移 219–677）：

```java
// 偏移 320-391（对应 v159.3 源码 DesktopInput.java:267-270）
if(Math.abs(input.axis(Binding.moveX)) > 0 || Math.abs(input.axis(Binding.moveY)) > 0
   || input.keyDown(Binding.mouseMove)){
    panning = false;          // ← 注意：玩家自己一操作，panning 就被清掉
    spectating = null;
}
...
// 偏移 520-540
if((!player.dead() || spectating != null) && !panning){      // ← panning 为真才跳过
    ...
    Core.camera.position.lerpDelta(panTarget, smoothcamera ? 0.08f : 1f);   // 偏移 674
}
```

也就是说：**按住鼠标移动的那几帧**里 `panning` 刚被置 true，`lerpDelta` 会被跳过；
但**松开鼠标、或改用 W/A/S/D 的那一帧**，`panning` 立刻变回 false，
`lerpDelta` 就又生效了 —— 这正是"镜头被重新定向回单位"的来源。
所以"相机跟着单位"其实是两件事叠在一起：

| # | 现象 | 原因 |
|---|---|---|
| 1 | 拖着鼠标时画面一直滚、看着像镜头在追单位 | 单位永远朝**屏幕中心**飞（1.2 节） |
| 2 | 松开鼠标 / 按 WASD 后镜头被拽回单位 | `panning` 变回 false，`lerpDelta` 又生效（1.1 节） |

### 1.2 现象 #1 的原因：单位永远朝"屏幕中心"飞

`DesktopInput.updateMovement()`（同上反汇编，方法内偏移 56–142）：

```
 59: ldc "detach-camera"                    // if(settings.getBool("detach-camera"))
 68: getstatic Core.camera.position         //   Vec2 targetPos = camera.position;   ← 目标 = 屏幕中心
 82: Vec2.set(Vec2)
 88: Vec2.sub(Position)                     //   movement = targetPos - player
 92: Vec2.limit(speed)
103: Player.within(Position, 15.0f)         //   if(player.within(targetPos, 15f))
113: Vec2.setZero() + Vec2.approachDelta(…) //     movement.setZero(); vel.approachDelta(ZERO, speed*accel/2)
```

也就是：**单位总是朝"当前相机坐标"走，直到自己跑到屏幕中心为止**。
相机不动 ⇒ 屏幕中心是一个固定的世界坐标 ⇒ 松开鼠标单位也**不会停**，
会继续朝那个点飞。位移动的是**单位**，但画面上是整个世界在滚 —— 这就是
"感觉镜头在追单位"。

### 1.3 本模组做的事

只在**自由视角 + 鼠标移动键按住**时，把上面那一支的目标从
"相机坐标（屏幕中心）"换成"**鼠标所在的世界坐标**"：

```java
// 原版
movement.set(camera.position).sub(player).limit(speed);
if(player.within(camera.position, 15f)){ movement.setZero(); vel.approachDelta(ZERO, speed*accel/2); }

// 本模组（等价伪代码）
movement.set(mouseWorld).sub(player).limit(speed);          // 方向 = 鼠标，不是屏幕中心
if(dist(player, mouseWorld) < ARRIVE_DIST) movement.setZero(), vel.approachDelta(ZERO, …);
else if(dist < BRAKE_DIST) 线性减速                            // 防过冲抖动
```

结果：**相机一动不动**（自由视角本来就不动），**单位走到鼠标指的地方就停**。
可以在控制台用 `cam.where()` 看实时数据：
`cursorActive`（是否生效）、`d`（单位到鼠标的世界距离）、`move`（当前 movement 向量）。

### 1.4 相机那部分保留了什么

因为原版自由视角下相机本来就不回单位，本模组只在**同一帧把相机写回锚点**
（防止极端情况下 `panning` 被重置成 false 时那一帧的 `lerpDelta` 生效），
其他一切交给原版：

| 情况 | 行为 |
|---|---|
| **玩家什么都不按** | 取消游戏那一帧"把镜头吸回单位"的位移（**只有这一种情况我们会写相机**） |
| **按住平移键（默认 mouseForward／你绑的中键）** | 一个字节都不写，相机完全交给游戏 |
| **按住"鼠标移动"键（默认 mouseBack／你绑的右键）** | 一个字节都不写；只把单位的移动目标改成鼠标位置 |
| **按 W/A/S/D** | 一个字节都不写（`panning` 被清掉、走键盘平移分支，原版也不会吸回单位） |
| 玩家死亡 → 视角转向核心 | 不拦，交给原版（我们主动把相机放过去，和原版一致） |
| 自由观察某个单位（spectating） | 不拦 |
| 换单位 / 复活 / 接管单位 | 相机一概不动（原版自己会处理） |
| 换地图 / 重开 | 相机一概不动 |
| 剪影（逻辑 processors cutscene）、聊天/控制台/输入框打开 | 一概不碰 |
| **自由视角关着 / 开关关着** | 一行都不执行 |

> 判定"该不该拦"的唯一依据是 `Vars.control.input.panning == false`
> —— 也就是**游戏确实要执行那句自动跟随**的时候。这样就不会跟玩家的任何操作抢相机。

---

## 2. 安装

1. `DP-CameraUnbind.zip` 放进模组目录：
   - 你的机器是**便携模式**，生效目录是
     `E:\Program Files (x86)\Steam\steamapps\common\Mindustry\saves\mods\`
     （`%APPDATA%\Mindustry\mods\` 那份是 7 月的旧数据，见 `DP-AdjutantPlugin/README.md` 0.1 节）
2. 游戏内「模组」确认「镜头解绑」已启用（新模组默认启用）
3. **重启游戏**（模组重载 = 退出重进）
4. 进图 → **设置 → 游戏 → 镜头解绑** → 勾上（或按 `V`）

### ⚠ 打包陷阱：条目名必须用 `/`，不能用 `Compress-Archive`

第一版就是栽在这里：`Compress-Archive` 在 Windows 上把 zip 条目名写成反斜杠
（`scripts\main.js`），而 arc 的 [ZipFi](../Arc-Source/arc-core/src/arc/files/ZipFi.java)
只按 `/` 认层级和扩展名，于是：

```
root.child("scripts").findAll(f -> f.extEquals("js")).size == 0
mod.root.child("scripts").child("main.js").isDirectory() == true   // 走 else 分支
→ 日志：[E] No main.js found for mod camera-unbind.
```

用游戏自带的 arc 代码实测（`arc.files.ZipFi` 直接跑）：

| 包 | 条目名 | `findAll(js)` | 结果 |
|---|---|---|---|
| `Compress-Archive` 打的 | `scripts\main.js` | **0** | 报 "No main.js found" |
| 已跑通的副官插件 | `scripts/main.js` | 1 | 正常 |

**重新打包请用 [pack.ps1](pack.ps1)**（它手工指定正斜杠条目名并自检），
不要用 `Compress-Archive`。

### 怎么确认加载成功

看 `saves\last_log.txt`，应有这几行（都以 `[camera-unbind]` 开头）：

```
[I] [camera-unbind/scripts/main.js]: [camera-unbind] 热键 开关镜头解绑 = KeyCode.v
[I] [camera-unbind/scripts/main.js]: [camera-unbind] Trigger.update 已挂上
[I] [camera-unbind/scripts/main.js]: [camera-unbind] 客户端已加载：Mindustry / 语言=zh_CN
[I] [camera-unbind/scripts/main.js]: [camera-unbind] 设置项注入成功：设置 → 游戏 → 镜头解绑
[I] [camera-unbind/scripts/main.js]: [camera-unbind] 自检：CheckSetting=true | 游戏设置页=true | 当前开关=false
```

进图后还会打印一行"锚点已建立 (x, y) 单位#id 死亡=false" —— 那是视角被钉住的坐标。

任何 `[E] ... main.js#行号` 就是出错，把行号发我即可精确定位。

---

## 3. 用到的引擎 API（都已对着 `jre\desktop.jar` = 160.5 核对过）

| 用途 | API |
|---|---|
| 挂每帧 | `arc.Events.run(Trigger.update, Runnable)` |
| 相机坐标 | `Core.camera.position`（`Vec2`，字段，不是方法） |
| 单位/玩家判定 | `Vars.player.unit()`、`Vars.player.dead()`、`Vars.player.bestCore()`、`unit.id`、`unit.x/y`（字段） |
| 自由观察 | `Vars.control.input.spectating`、`InputHandler.locked()` |
| 剪影 | `Vars.renderer.isCutscene()` |
| 设置读写 | `Core.settings.getBool(k, def)` / `put(k, v)` / **`defaults(k, def)`**（只注册默认值，绝不覆盖玩家已保存的选择） |
| 设置界面 | `Vars.ui.settings.game`（`SettingsMenuDialog.SettingsTable`）→ `getSettings()` / `add(...)` / `rebuild()` |
| 设置项本体 | `new SettingsMenuDialog.SettingsTable.CheckSetting(name, def, null)`（官方给模组用的构造器，`Boolc` 传 `null`），标题/描述走 bundle 的 `setting.<name>.name` / `.description` |
| 换图重置 | `Events.on(WorldLoadEvent, ...)`、`Events.on(ResetEvent, ...)` |
| 延迟重试 | `Timer.schedule(Runnable, 帧)` |
| 控制台接口 | `rhino.ScriptableObject.putProperty(Vars.mods.getScripts().scope, "cam", api)` |

---

## 4. 逻辑自测（不用开游戏）

`test-harness.js` 把上面这些 Java API 用 JS 模拟出来（含"每帧自动跟随"那一句），
直接跑 `scripts/main.js` 做断言：

```
cd DP-CameraUnbind
node test-harness.js
```

覆盖（49 项断言，全绿）：

| 组 | 验的东西 |
|---|---|
| 1 | 设置项注入、键名、默认值走 `settings.defaults()`、重复注入幂等 |
| 1.5 | **重启后保留玩家自己的勾选**（不会被默认值抹掉）、重置默认能回到 `false` |
| 2 | 开关关闭时脚本完全不碰相机 |
| **2.5** | **开关打开但自由视角没开 → 一行都不许碰**（相机照原版被 lerp 回单位） |
| 3 | 自由视角 + 开关打开：锚点落在"打开那一刻"的位置；一帧自动跟随被完整还原；单位连跑 1100 格视角纹丝不动 |
| 4 | 换单位（复活/接管）时视角瞬移过去，之后继续钉住 |
| 5 | 玩家死亡 → 视角转向核心，且稳定不抖 |
| 6 | 换图重置锚点；`ResetEvent` 不炸 |
| 6.5 | 关掉后恢复原版跟随；重新打开时锚点落在当前相机位置（不跳回旧锚点） |
| 7 | 界面吃键盘（聊天/控制台/输入框）时不抢镜头、热键不误触发 |
| 7.2 | 关闭界面的那一刻：界面里挪过的视角被保留，且同一帧就重新钉住 |
| 7.5 | 热键 `V` 开关、`N` 拉回视角、`keyTap` 一帧只触发一次 |
| **7.8** | **自由视角下"走到鼠标位置"**：movement 指向鼠标且长度=速度；相机全程不动；到位归零；接近时减速；自由视角关着 / 没按鼠标键时**完全不碰 movement**（哨兵值验证） |
| 8 | 控制台 `cam.*` 接口（含 `cursorActive` / `d` / `move` 字段）与提示 |
| 9 | 全程无失败/出错日志 |

> 注意：这个自测只能证明**逻辑**（控制流、锚点数学、幂等、异常处理、持久化语义）是对的；
> Rhino ↔ Java 的类型转换（`new CheckSetting(...)`、`Events.run(..., function(){})` 等）
> 只能在真机日志里验证。所以第一次进游戏请照第 2 节看一眼 `last_log.txt`。

> 踩过的坑：这个自测里的 `Vec2` 桩一开始把 `set(a, b)` 当成 `set(Vec2)` 处理，
> 于是 `locked.set(x, y)` 静默失效 —— **测试桩必须和 arc 的重载语义对齐**，
> 否则测试会"绿灯"地骗人（这次是红了才暴露出来）。

### 另外两个"不开游戏也能验"的工具（`tools/`）

| 工具 | 验什么 | 怎么跑 |
|---|---|---|
| [tools/ZipProbe.java](tools/ZipProbe.java) | 用**游戏自带的 arc 代码**（`arc.files.ZipFi`）打开压缩包，确认 `findAll(js).size == 1`、`main.js` 不是目录 —— 这一条正是第一版 "No main.js found" 的根因 | `javac -encoding UTF-8 -cp <jre>\desktop.jar -d . tools\ZipProbe.java` 然后 `java -cp "<jre>\desktop.jar;." ZipProbe ..\DP-CameraUnbind.zip` |
| [tools/RhinoRun.java](tools/RhinoRun.java) + [tools/rhinoProbe.js](tools/rhinoProbe.js) | 在游戏自带的 Rhino（注意：它被搬到 `rhino` 包，不是 `org.mozilla.javascript`）里跑脚本片段，验证 `new CheckSetting(name, false, null)`、`title/description` 读得到、`Events.run/on` 收 JS 函数等类型转换 | `javac -encoding UTF-8 -cp <jre>\desktop.jar -d . tools\RhinoRun.java` 然后 `java -cp "<jre>\desktop.jar;." RhinoRun tools\rhinoProbe.js` |

两条都在本机上实跑通过：`CheckSetting class = [JavaClass mindustry.ui.dialogs.SettingsMenuDialog$SettingsTable$CheckSetting]`、
`new CheckSetting(name, false, null) = OK`、`title = [dp-camera-unbind]`（bundle 没键时的回退值）、写入 `title` 后读回中文正常。

---

## 5. 已知取舍

- **只在自由视角下生效**：这是刻意的 —— 你确认要的就是"在原版自由视角的基础上只改这一件事"，
  所以自由视角关着时本模组一行都不执行（第 2.5 组断言就是守这条）。
- **原版自由视角本来就不把相机拉回单位**（1.1 节），所以"相机不动"这件事我们没有额外发明什么；
  真正被换掉的是"单位朝屏幕中心飞"那条移动求解。
- 需要找单位时按 `N`（或小地图点一下）——`N` 会把视角拉回单位/核心。
- 到位阈值 `ARRIVE_DIST = 6`（≈0.75 格）、减速起点 `BRAKE_DIST = 28`，都在
  `scripts/main.js` 顶部配置区；觉得"停得太早/太晚"就改这两个数。
- 运输单位（Tank/Mech 那类非 omniMovement）走的是 `rotateMove`：本模组只改 `movement` 向量，
  所以它们依旧"边走边转向"，行为与原版一致，只是目标点变成了鼠标。
- 与 MindustryX 不冲突（本模组只用官方 API，没有 patch 任何类）。

## 6. 版本记录

| 版本 | 内容 |
|---|---|
| **5.4** | **「死前视野」**：用户选定（选前比较过三版判据，全被实测推翻）—— 死亡瞬间把锚点钉在**死前那一刻的视野**上，死亡延迟与**落地动画一律放手让游戏走完**，重生之后再定位回死前视野；另外给恢复加 30 帧宽限期（落地那一刻玩家通常什么都没按，否则恢复的下一帧就被原版 AutoFollow 拽回重生点，肉眼是"闪一下又飞走"）。根因链：160.5 里死亡时**没有任何代码动相机**，把镜头拉到新单位的是两条既有 vanilla 路径（`CoreBlock.zoomLaunch()` 锁核心 + 新单位在核心处生成），而本模组当时在死亡窗口主动放手，等于把相机交给了它们。修 bug 期间踩到三个 heisenbug（谓词带副作用 / 观察被挂在 `dead` 判定之后 / 调用点被上游 `return` 跳过），已写进 METHOD.md §5.5 |
| 5.3 | 修"按住移动键拖拽时的画面抖动"：去掉成因（按住期间把 `panSpeed`/`panBoostSpeed` 置 0）而不是事后把相机写回上一帧 —— "帧尾写回旧值"与"同帧原版写入"会在两值之间摆动 |
| 5.2 | 覆写 `panCamera(Vec2)`，修"按着移动键时点小地图/按 WASD 无法改变视角"（把 `panning`/锚点判定交给原版路径，锚点改用不变量"相机是否仍停在上次钉住的位置"） |
| 5.1 | 修"中键平移时镜头与单位不同步"；`hidden: true`（免装进服务器，见 §4/METHOD.md） |
| 4.0 | 去冗余（接口破坏性变更）：删真死码 `ARRIVE_DIST`、删冗余 `api` 对象（只保留顶层全局函数）、诊断状态合并为 `diagState()`；新增 `tools/deadcode.js` |
| **2.4** | **"松开移动键就停"**：原版在自由视角下**没有"松手"这个概念** —— `updateMovement` 每帧都把 `movement` 重算成"朝屏幕中心"，所以松开键以后单位还在继续飞、画面继续滚（这本身就是"看着没效果"的原因之一）。现在只要本模组开着，松开移动键时会把 `movement` 清零并把速度收敛到 0，单位原地停下。同时给 `cam.where()` 加上 `last`（相机/单位/鼠标坐标 + 生效帧数）和 `bindMove`/`bindPan`（绑定实况 + 是否按下），用于现场定位 |
| 2.3 | **修"中键/右键都不能动、镜头卡在原地"**：根因是我在外面**按住相机**（每帧把坐标写回锚点），把游戏自己的相机写入在同一帧擦掉了。现在只在**游戏确实要吸回镜头**的那一帧动手 —— 唯一依据是 `Vars.control.input.panning == false`；其余所有帧一个字节都不写相机 |
| 2.2 | 试图按"是否按了移动键"决定要不要按住相机 —— 规则自相矛盾（按住相机 ⇔ 没按移动键，而功能又要求按了移动键才生效），等于什么都没做 |
| 2.1 | **修致命 bug**：改完相机坐标没调 `Camera.update()` → `mouseWorld()` 逆投影用的是旧矩阵 → 解出错误世界坐标，实测表现是"完全没生效"。另把选项从「游戏」页挪到**「图像」页、紧随原版「自由视角」之后** |
| 2.0 | 把范围收窄到"自由视角下的移动单位"：接管 `updateMovement` 的自由视角分支，把移动目标从"屏幕中心"换成"鼠标世界坐标" |
| 1.0 | 首个版本：无条件把相机钉在锚点（**范围过宽**，已废弃） |
