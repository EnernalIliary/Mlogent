# 方法论：从零给 Mindustry 做"只改自己"的脚本模组

> 这份文档是一次完整实战的沉淀（自由视角修复模组，v1 → v3.9）。
> 记的是**怎么做**，不是"这个模组怎么用"——目标是下次遇到同类需求能照着走一遍。
>
> 环境基线：Mindustry **160.5**（Steam 版） + 改端 **MindustryX**
> 源码克隆：`F:\OneDrive\桌面\AtomicStates\Mindustry-Source`（159.3，**与你实际运行的不是同一份**，见 §1.3）

---

## 目录

- [0. 一句话总纲](#0-一句话总纲)
- [1. 定位源码：查源码的固定动作](#1-定位源码查源码的固定动作)
- [2. JS 脚本模组能做到什么（关键技巧）](#2-js-脚本模组能做到什么关键技巧)
- [3. 结论一：相机没人会"自动回单位"](#3-结论一相机没人会自动回单位)
- [4. 结论二：`hidden: true` = 自用模组的正确姿势](#4-结论二hidden-true--自用模组的正确姿势)
- [5. 工具箱：本地验证工具](#5-工具箱本地验证工具)
- [6. 踩坑清单（每条都真实崩过或"看着没效果"过）](#6-踩坑清单每条都真实崩过或看着没效果过)
- [7. 标准作业流程](#7-标准作业流程)

---

## 0. 一句话总纲

> **别猜，去读反汇编；别用印象核对成员名，用反射导出真实签名；
> 改不动的地方不要"事后纠正"，要去掉它的成因；
> 同一功能只留一份实现，注释别和文档重复。**

四条都是从实际失败里换来的：

| 我猜/凭印象做过的事 | 结果 |
|---|---|
| 凭印象写 `unit.aimX()` | 崩游戏（`aimX` 是字段） |
| 用 `DesktopInput.prototype.update.call()` | 崩游戏（Rhino 里 `prototype` 是 null） |
| "帧尾把相机写回上一帧" | 不崩，但**画面抖动** |
| 看 159.3 源码推断 `panning` 恒为 true | **结论是错的**（实际那份不同） |
| 同时发布 `cam.xxx()` 和 `camXxx()` 两套接口 | 纯冗余，且可靠的那套只有全局函数 |
| 把原理讲解抄在脚本注释里 | 与 METHOD.md 重复，改一处忘一处（曾留下错误注释） |

---

## 1. 定位源码：查源码的固定动作

### 1.1 找到那个功能对应的代码行

Mindustry 的功能几乎都在 `core/src/mindustry/` 下，按功能猜目录：

| 想改什么 | 去哪找 |
|---|---|
| 鼠标/键盘、单位移动、相机 | `input/DesktopInput.java`（移动端是 `MobileInput.java`） |
| 设置界面的选项 | `ui/dialogs/SettingsMenuDialog.java` |
| 游戏主循环、输入调度 | `core/Control.java` |
| 渲染、相机矩阵 | `core/Renderer.java`、`graphics/` |
| 联机、join 校验 | `core/NetServer.java`、`core/NetClient.java` |
| 模组加载、meta 解析 | `mod/Mods.java`、`mod/Mod.java`、`mod/Plugin.java` |

**用 grep 工具搜字符串比读整个文件快**（`grep` 工具，不要用 shell 的 grep）：

```
grep  pattern: "detach-camera"          path: Mindustry-Source/core/src
grep  pattern: "getModStrings"          path: Mindustry-Source/core/src
grep  pattern: "camera.position"        path: Mindustry-Source/core/src/mindustry/input
```

设置项的键名（如 `"detach-camera"`、`"smoothcamera"`）是**最好的搜索锚点** —— 它能直接从界面文案串到实现代码。

### 1.2 用反汇编确认"实际运行的代码"

源码可能与编译产物不一致。**以字节码为准**：

```powershell
$javap = 'C:\Program Files (x86)\Android\openjdk\jdk-17.0.14\bin\javap.exe'
$jar   = 'E:\Program Files (x86)\Steam\steamapps\common\Mindustry\jre\desktop.jar'

# 看某个类的完整字节码（含偏移，用于与源码逐行对照）
& $javap -p -c -cp $jar mindustry.input.DesktopInput | Out-File out.asm -Encoding utf8

# 只看方法签名/字段（快）
& $javap -p -cp $jar mindustry.input.InputHandler
```

读字节码时的两个习惯：

1. **先找方法的起始行**（`public void update();`），再按偏移区间读，别从头读
2. **条件跳转要看反向**：`ifne 306` 表示"非零就跳到 306"，所以 306 那段是 `cond == false` 的分支

### 1.3 ⚠️ 最重要的一条：改端会替换核心类

**MindustryX 包里带着自己的 `mindustry/input/DesktopInput.class`，与你 `desktop.jar` 里的不是同一个文件**（39842 B vs 38680 B）。

所以查源码前，先确认**你实际跑的是哪一份**：

```powershell
# 列出改端替换了哪些核心类
$z = [System.IO.Compression.ZipFile]::OpenRead($modZip)
$z.Entries | Where-Object { $_.FullName -like 'mindustry/*/*.class' } | Select -ExpandProperty FullName
```

实测 MindustryX 替换了这些：

```
mindustry/core/       ContentLoader, Control, Logic, NetClient, Renderer, UI, Version, World
mindustry/input/      DesktopInput, InputHandler, MobileInput
mindustry/mod/        Mods
```

（注意：**没有 `NetServer`** —— 服务端逻辑它改不了。）

确认之后，用同样方式提取改端的那一份再反汇编，**两份对比**：

```powershell
& $javap -p -c -cp "<提取目录>;$jar" 'X_DesktopInput' | Out-File X.asm -Encoding utf8
# 然后对比两份 update() 里的方法调用序列（我曾用一个 node 脚本做多重集合差分）
```

这次对比出的关键差异（X 版 `update()` 多出来的）：

```java
1979-1992:  if(!LogicExt.noUpdatePlayerMovement) updateMovement(player.unit());   // X 自己的门控
2736/2744:  pollInputPlayer();                                                    // X 新增的输入轮询
```

### 1.4 用反射确认每个成员的**真实形态**

**这是最省钱的一步** —— 一次崩溃（崩的是游戏）就能被避免。

有 JVM 的时候最省事的就是反射：

```java
// RefDump.java：把脚本要用的成员逐个核对"是字段还是方法"
Class<?> c = Class.forName(cls);
try{ Field f = c.getField(n);  ... }        // 字段 → obj.n
catch(NoSuchFieldException e){
  for(Method m : c.getMethods()) if(m.getName().equals(n)) ...   // 方法 → obj.n(...)
}
```

**但本机没这么顺**：Mindustry 自带的 `jre` 里**没有 `javap`**，而且 `jdk.compiler` 被剔掉了 ——
连 `java Foo.java`（单文件源码模式）都会报
`InternalError: Module jdk.compiler not in boot Layer`；系统 Java 只有 8，读不了 17 的 class 文件；
反射要 `-cp desktop.jar` 把类加载起来，缺 Arc 依赖就 `NoClassDefFoundError`。

所以写了 **`node tools/class-members.js <jar> <类名> [成员名...]`**：
在 Node 里直接解析 ZIP + class 文件结构，**不开 JVM、不加载类、没有依赖问题**。

```
node tools/class-members.js "...\jre\desktop.jar" mindustry.gen.Unit type
  类 mindustry/gen/Unit
    字段  type Lmindustry/type/UnitType;   public
    方法  type ()Lmindustry/type/UnitType;   public      ← 两个都有！看描述符才知道该写哪个
```

> ⚠️ **写这个解析器时踩的坑**：常量池里 tag `9/10/11/12/17/18`（Fieldref / Methodref /
> InterfaceMethodref / NameAndType / Dynamic / InvokeDynamic）各带**两个 u2**，我一开始让它们
> 落到 `default: p += 2`，于是常量池从第 ~365 项起整池错位，解析出的"tag"其实是 UTF-8
> 字符串里的 ASCII 字节。**症状很好认**：解析出的 tag 变成 97 / 119 / 101（`a` `w` `e`）
> 这种字母。另一条同类坑：`CONSTANT_Class(7)` 指向的是**一个 Utf8 的索引**，不跳这一层
> 会打出 `?10` 而不是类名。

实测结果（务必记住这几类）：

| 成员 | 形态 | 正确写法 |
|---|---|---|
| `Unit.aimX` / `aimY` | **字段** float | `unit.aimX` |
| `Unit.vel` / `x` / `y` | 字段 | `unit.vel` |
| **`Unit.type`** | **方法** `type()`（字段 `type` 也在，但脚本里读到的是方法） | **`unit.type()`** |
| `Unit.speed()` / `lookAt` / `prefRotation` / `movePref` / `aim` / `controlWeapons` | 方法 | `unit.speed()` |
| `UnitType.omniMovement` / `accel` / `faceTarget` | 字段 | **`unit.type().accel`** |
| `UnitType.hasWeapons()` | 方法 | **`unit.type().hasWeapons()`** |
| `Player.shooting` / `boosting` / `mouseX` / `mouseY` | 字段 | `player.shooting` |
| `Player.dead()` / `within()` / `unit()` | 方法 | `player.dead()` |
| `Binding.moveX` / `mouseMove` / `pan` / `boost` | 字段（值是 `KeyBind`） | `Core.input.keyDown(Binding.mouseMove)` |
| `DesktopInput.panSpeed` / `panBoostSpeed` / `panScale` | **public 字段** | `input.panSpeed = 0` |
| `InputHandler.spectating` | public **boolean 字段** | `if(inp.spectating)`（见 §5.6） |
| `Arc 的 Seq.size` | **字段**（不是 `size()`！） | `seq.size` |

> 🔴 **`Unit.type` 这一行原先写错了**（记成"字段 → `unit.type`"），代价是：`unit.type.omniMovement`
> 取到 `undefined` → 抛 `TypeError` → 被覆写的安全网吞掉 → `superBroken = true` 永久卸载覆写 →
> **整块功能无声失效**（十几个断言一起红，看着像"模组没加载"）。见 §5.6 与踩坑表 #18。
> **这一条现在是 `check-members.js` 里的自动规则**，不会再靠记性。

> 还要注意 `getField()` **不返回父类继承的 public 字段**。查 `InputHandler` 的字段要在 `DesktopInput` 上查。

---

## 2. JS 脚本模组能做到什么（关键技巧）

### 2.1 可以**真正覆写 Java 方法**

用 Rhino 的 `JavaAdapter` 生成子类，再用 `Control.setInput()` 换掉输入处理器：

```js
// 只覆写想改的方法；方法体整段照抄原版，只改动那一处
var def = {
    updateMovement: function(unit){
        // ... 原版逻辑，替换掉目标点
    }
};
var adapter = new JavaAdapter(Packages.mindustry.input.DesktopInput, def);
Vars.control.setInput(adapter);   // 见 Control.java:385，它会正确处理注册/注销
```

- 目标方法**必须是 `protected` 或 `public`**（`DesktopInput.updateMovement(Unit)` 正好是 protected）
- `Vars.control.input` 是 public 静态字段，`setInput` 是 public 方法
- 这就是**不需要重新构建游戏**就能改核心行为的关键

### 2.2 ⚠️ 绝对不能做的三件事

| 不要 | 原因 |
|---|---|
| `DesktopInput.prototype.update.call(this)` | Rhino 里 `prototype` 是 **null**（`update()` 声明在父类 `InputHandler` 上）→ 崩游戏 |
| 写 `super.update()` | `super` 是 JS **保留字** → 语法错误，Node 直接报 |
| 整段复刻 `DesktopInput.update()` | 700+ 行，漏一处就丢功能（建造/指挥/payload 全在里面） |

**结论：Rhino 里无法安全调用父类实现 → 需要"撤销父类行为"时，改用别的手段（见 §3.3、§4）。**

### 2.3 必须给覆写套一层 try/catch 安全网

```js
def.updateMovement = function(unit){
    if(superBroken) return;
    try{ realUpdateMovement(this, unit); }
    catch(e){
        superBroken = true;
        log("⚠ updateMovement 覆写出错，已停用覆写（游戏不会崩）：" + e);
        try{ Vars.control.setInput(new Packages.mindustry.input.DesktopInput()); }catch(e2){}
    }
};
```

**为什么必须有**：JavaAdapter 里抛出的 JS 异常会一路冒到 `Control.update` → **崩游戏**（我崩过两次）。
有了这层网，脚本出错只会记一行日志并自动退回原版。这条网在开发期还帮我发现了 mock 的缺陷（见 §5.2）。

### 2.4 帧序：`Trigger.update` 在 `input.update()` 之后

```
Control.update(){
    input.update();    ← DesktopInput 在这里读鼠标、解单位移动、**挪相机**
    logic.update(); }  ← Trigger.update 在这里 fire，也就是你的回调
```

```js
Events.run(ET.Trigger.update, function(){ /* 你在这一帧的"最后" */ });
```

**实践含义**：
- 想改 `movement`：在覆写 `updateMovement` 里改（那才是它的计算处），别在 Trigger 里抢
- 想撤销相机的本帧位移：你的回调跑在之后，**可以**（但见 §3.3 的抖动教训）

### 2.5 相机写入的正确姿势

```js
Core.camera.position.set(x, y);
Core.camera.update();      // ← 必须！否则矩阵是旧的，mouseWorld() 会解出错位的世界坐标
```

`Camera.update()` 只在游戏的 `Renderer.draw()` 里被调用，所以脚本改完坐标一定要自己刷矩阵。

### 2.6 控制台接口：只挂全局函数，别挂对象

实测两次失败：`cam.measure`、`cam.drift` 在控制台里都是 `undefined`，而同一行发布的 `cam.version` 却正常。

**对策：只发布顶层全局函数，不要维护对象副本。**

```js
var globals = { camVersion: fn, camDrift: fn, camHold: fn, /* ... */ };
var scope = Vars.mods.getScripts().scope;
for(var g in globals){
    Packages.rhino.ScriptableObject.putProperty(scope, g, globals[g]);
}
```

并**自检读回**（确认真的挂上了，而不是相信"应该挂上了"）：

```js
var bk = Packages.rhino.ScriptableObject.getProperty(scope, "camVersion");
log("控制台接口自检：" + ((typeof bk === "function" && bk() == MOD_VERSION) ? "OK" : "读回来不对劲"));
```

> **冗余教训**：我一度同时发布了"对象"和"全局函数"两套（`cam.version()` 和 `camVersion()`）。
> 那是纯冗余 —— 每个功能存了两份，还得维护两套文档。既然全局函数才是可靠的那套，
> 对象就该删掉（v4.0 已删）。

---

## 3. 结论一：相机没人会"自动回单位"

### 3.1 那两行在哪（这是最初的目标）

`core/src/mindustry/input/DesktopInput.java`：

```java
// ① update() 第 283-291 行：把相机朝 panTarget（= 玩家单位）插值
283: }else if((!player.dead() || spectating != null) && !panning){
287:     Position panTarget = coreTarget != null ? coreTarget : spectating != null ? spectating : player;
289:     Core.camera.position.lerpDelta(panTarget, Core.settings.getBool("smoothcamera") ? 0.08f : 1f);

// ② updateMovement() 第 981-999 行：自由视角下单位朝**屏幕中心**飞
981: if(settings.getBool("detach-camera")){
985:     Vec2 targetPos = camera.position;                      // ← 目标 = 屏幕中心
988:     movement.set(targetPos).sub(player).limit(speed);
990:     float arrive = ... ? 6f : 15f;
992:     if(... && !Core.input.keyDown(Binding.mouseMove)){      // ← 松手即停
```

### 3.2 关键事实：`panning |= detached`（源码 273 行）

```java
273: panning |= detached;
```

→ **自由视角开着时 `panning` 恒为 true → 第 289 行的 `lerpDelta` 根本不执行。**

**但别高兴太早**：实测（见 §3.4）证明你实际运行的那份里 `panning` 在按住移动键时是 **false**，289 行**确实在执行**。
**源码 159.3 与运行中的 160.5/X 版在这一点上不一致 —— 这就是"读源码 ≠ 读运行代码"的活教材。**

### 3.3 ⚠️ 反面教材：不要"事后把相机写回去"

我最初的方案是：在 Trigger 回调里把相机写回上一帧末的坐标，以此撤销本帧的自动位移。

**结果：功能对了，但画面抖动。** 因为相机在"漂移后的位置"和"上一帧位置"之间每帧来回摆 —— 渲染看到的位置逐帧变化。

```
第 N 帧：游戏写 P+D → 我写回 P     （渲染看到 P）
第 N+1 帧：游戏写 P+D' → 我写回 P  （渲染看到 P）
```
看起来应该稳定，但实际存在一子帧的时序差，表现为抖动。

### 3.4 ✅ 正确做法：去掉成因，而不是事后纠正

要压掉两处（都在 `update()` 里）：

| # | 位置 | 机制 | 治法 |
|---|---|---|---|
| ① | 第 294-297 行 | 按住移动键 → 推镜向鼠标，位移 = `clamp(鼠标偏移*panScale,-1,1) * camSpeed`，而 `camSpeed = panSpeed * Time.delta`（第 239 行） | **把 `panSpeed`/`panBoostSpeed` 置 0** → 位移变成"加 0"，原版自己什么都不写 |
| ② | 第 289 行 | `lerpDelta(panTarget, 0.08f)` 每帧吸回单位 | 每帧把相机写回**同一个锚点** → lerp 起点=终点，等于 no-op |

```js
// 进入拖拽的第一帧记锚点，之后每帧钉回它（位置恒定 → 不抖）
if(!pinned){ pinX = camera.position.x; pinY = camera.position.y; pinned = true; }
if(Math.abs(c.position.x - pinX) > 0.001){ c.position.set(pinX, pinY); Core.camera.update(); }
setPanSpeedZero(true);   // 并让原版推不动
```

**为什么这样就不抖**：写入的是**同一个值**，而不是两个值之间来回摆。

### 3.5 用户需求演化出的最终规则（`holdCamera()`）

```js
function holdCamera(){
    if(!cameraHoldEnabled) return false;
    if(wasBusy) return false;                                  // 界面打开
    if(player == null || player.dead()) return false;          // 死了镜头该跟
    if(!settings.getBool("detach-camera", false)) return false;// 只在自由视角下
    if(inp.spectating != null || inp.locked()) return false;   // 观察/剪影
    if(coreInputKeyDown(Binding.pan)) return false;            // ★ 玩家按平移键 → 相机交回游戏
    return mouseMoveHeld();                                    // 只在按移动键时压
}
```

**`Binding.pan` 那条是"中键+右键同时按住就同时移动镜头和单位"的实现** —— 按平移键时我不置零、不钉相机，原版推镜照常；同时 `updateMovement` 的覆写让单位走到鼠标。两个效果天然叠加。

### 3.6 参数

| 名字 | 值 | 含义 |
|---|---|---|
| `ARRIVE_DIST` / `CURSOR_ARRIVE` | 6.0 | 距离鼠标多近算到位（世界单位，1 格 = 8） |
| 原版 `arrive` | 15f | 退回原版行为时用原值 |

---

## 4. 结论二：`hidden: true` = 自用模组的正确姿势

### 4.1 机制链（四处源码）

**① 上报名单过滤掉 hidden** —— `mod/Mods.java:940`

```java
public Seq<String> getModStrings(){
    return mods.select(l -> !l.meta.hidden && l.enabled())
               .map(l -> l.name + ":" + l.meta.version);
}
```

**② 全代码库只有一处把它发给服务器** —— `core/NetClient.java:108`

```java
c.mods = mods.getModStrings();
```

**③ 服务端据此校验** —— `core/NetServer.java:210-224`

```java
Seq<String> extraMods   = packet.mods.copy();
Seq<String> missingMods = mods.getIncompatibility(extraMods);
if(!extraMods.isEmpty() || !missingMods.isEmpty()){
    con.kick("[accent]Incompatible mods![]...");   // extraMods = 你装了服务端没有的 mod
}
```

**④ hidden 只跳过"内容"** —— `mod/Mods.java:837`

```java
for(LoadedMod mod : orderedMods()){
    //hidden mods can't load content
    if(mod.main != null && !mod.meta.hidden){
        mod.content.setCurrentMod(mod);
        mod.main.loadContent();     // ← 只跳过这个
    }
}
```

> **`init()`、事件监听、类替换全部照常执行。** 所以"纯代码改动"的模组可以安全 hidden。

### 4.2 MindustryX 就是这么干的

直接读它的 `mod.hjson`（在包里）：

```hjson
name: MindustryX
main: mindustryX.loader.Main
version: "2026.10.02.B502"
hidden: true          ← 全部秘密
dependencies: []
```

它没有伪造版本号（`Version` 类仍从 `version.properties` 读），**只是把自己标成 hidden**，而它干的活全是代码级的（替换 `NetClient`/`Control`/`Renderer` 等类），不需要注册内容 —— 所以"免装"与"改端"两件事同时成立。

### 4.3 三种做法对比

| | `hidden: true` | `Plugin` 子类 | 普通 mod |
|---|---|---|---|
| 客户端免装 | ✅ | ✅（隐含 hidden） | ❌ |
| 需要编译 jar | ❌ 脚本也行 | ✅ 必须 | ❌ |
| 能跑代码/监听事件 | ✅ | ✅ | ✅ |
| 能加新内容 | ❌ | ❌ | ✅ |
| 能改别人客户端的手感 | ❌ | ❌ | ❌ |
| 放哪 | 各自 `mods/` | 服务端 `config/mods/` | 各自 `mods/` |

`Plugin` 定义整个类就一行：

```java
/** Defines a special type of mod that is always hidden. */
public abstract class Plugin extends Mod{}
```

官方文档：[Plugins & JVM Mods](https://mindustrygame.github.io/wiki/modding/2-plugins/) —— 原文：
> All plugin main classes should extend `mindustry.mod.Plugin`. This makes them implicitly *hidden* — clients will not need to download the plugin to join the server.

元文件名候选（`mod/Mods.java:34`）：

```java
private static final String[] metaFiles = {"mod.json", "mod.hjson", "plugin.json", "plugin.hjson"};
```

### 4.4 ⚠️ 内容是双向的

- **纯代码 mod**（改输入/渲染/联机判定）→ 可以 `hidden`，功能不受影响
- **内容 mod**（新方块/单位/物品）→ **不能** hidden，标了它自己的内容会加载不出来；这种只能"进服前禁用"或"只在同 mod 服务器玩"

### 4.5 检查你的 mods 目录

用本文档附录的 `ModsScan.java`：

```
文件                       内部名            hidden   join 影响
DP-CameraUnbind.zip        camera-unbind     true     不影响（不上报）
yuria-...newhorizonmod.zip new-horizon       false    会被当成多余 mod → 可能被踢
```

**只要有一个非 hidden 的启用 mod，就会被原版服务器踢。** 排查时看被踢提示里的
`Unnecessary mods:` / `Missing:` 两段 —— 前者说你多了什么，后者说你缺什么。

---

## 5. 工具箱：本地验证工具

都放在 `saves\_tools\` 下（需要 JDK 17，路径见 §1.2）。

### 5.1 打包与包结构验证

| 工具 | 用途 |
|---|---|
| `pack.ps1`（模组目录里） | **唯一**允许的打包方式。用 `ZipArchive.CreateEntry("scripts/main.js", …)` 写**正斜杠** |
| `ZipProbe.java` | 用游戏自己的 `ZipFi` 检查包结构 |

**⚠️ 绝对不要用 `Compress-Archive`** —— 它写反斜杠条目名，而 arc 的 `ZipFi` 目录识别要求条目名里有 `/`，结果就是 `No main.js found for mod X`。

```powershell
& $java -cp "$jar;$tools" ZipProbe $zip
# 期望：scripts.findAll(js).size = 1 / main.js isDirectory=false
```

### 5.2 本地测试夹具（`test-harness.js`）

一个用 node 跑的假游戏，**50+ 条断言**。它的价值在于：改一行代码就能回归，不用每次重启游戏。

**但它必须"忠实"，否则测试会静默空转。** 我在这一版上吃过大亏：

| mock 缺什么 | 后果 |
|---|---|
| `JavaAdapter` / `setInput` / `updateMovement` | 覆写相关的断言**从没执行过覆写** |
| `Vec2.sub` / `Tmp` / `Angles` / `prefRotation` | 覆写一跑就抛异常，被安全网卸载 → 测试静默失效 |
| `Binding.pan` 是字符串而非 `KeyBind` | "按中键"的用例**永远不成立** |
| `Seq.size` 写成方法而非字段 | 诊断路径走不通 |
| `control.input` 是字面量而非 `DesktopInput` 实例 | `instanceof` 判断失败，覆写装不上 |

**教训**：当测试"全绿"但功能无效时，**先怀疑 mock，而不是代码**。判断方法是加一条"覆写真的被调用了吗"的断言：

```js
ok(typeof control.input.updateMovement === 'function' && control.input === inputAdapter,
   '输入处理器上确实有我们的 updateMovement 覆写');
```

### 5.3 静态检查（`check-members.js`）

按 §1.4 得到的"字段/方法规则表"，扫源码里的每一处成员访问，抓 `aimX()` / `unit.type.omniMovement` 这类错误：

```
检查了 109 处成员访问；问题 0 个
```

**规则表是活的**：每次靠"猜成员形态"踩了坑，就把那条写进 `rules`，让它从此自动守。
本次补进去的是 `'type': 'method'` —— 旧表把它记成 `field`，于是同一类错误它抓不到，
反而在修好之后**误报**成"[FAIL] .type 是字段，却被当成方法调用"。

```
// check-members.js
// ⚠ type 是**方法**：Unit.type() 返回 UnitType，写成 unit.type.omniMovement 会抛
//   TypeError（undefined 上取属性）→ 被覆写的安全网吞掉 → superBroken=true 永久卸载覆写，
//   表现为"整块逻辑无声失效"。v5.5 前一直是错的，靠这条规则抓出来。
'type': 'method',
'omniMovement': 'field', 'accel': 'field', 'faceTarget': 'field',
```

配合 `node --check scripts/main.js` 做语法检查。**成员形态拿不准时**，用
`node tools/class-members.js "<jar>" <类名> <成员名>` 直接读 class 文件（§1.4）。

### 5.4 运行期诊断的写法

**关键原则：让游戏自己报告，别靠控制台。** 控制台的对象属性解析不可靠（§2.6）。

```js
// 1) 自检关键前提，写进日志
log("hidden 自检：" + (hid ? "hidden=true ✓" : "hidden=false ✗")
    + "（服务器校验名单里出现 " + reported.length + " 次）");

// 2) 安装后立刻读回验证
log("输入处理器已替换为子类 [是本人=" + (Vars.control.input === adapter)
    + " updateMovement=" + (typeof Vars.control.input.updateMovement) + "]");

// 3) 量化"手感"问题（如抖动）：帧尾采样，统计逐帧位移
log("drift 报告：样本 N 帧 | 帧间位移 最大 X 平均 Y | 按着移动键的帧数 M");
```

### 5.5 ⚠️ 调试探针把 bug 藏起来了（heisenbug 的两种成因）

这一条是本次**代价最大**的教训：同一个 bug 查了四次，前三次都被自己的探针误导。

**成因一：判定函数带副作用 → 探针一调就扰动结论。**

`shouldRestoreDeathView()` 里曾经同时干两件事：判定"该不该恢复"，以及
**自增 `snapFrames`、并记下"见过降落动画"（`snapSawCut = true`）**。
我在探针里顺手调了一次它来打印结果 —— 于是探针本身把状态推进了，日志显示
`加探针 95/0、去掉探针 92/3`，而且稳定复现，看起来像"代码依赖探针"。

> **规则：谓词函数（`shouldXxx` / `isXxx` / `canXxx`）不许改状态。**
> 观察与推进必须拆成两个函数（现在拆成了 `recordDeathViewCut()` 与
> `shouldRestoreDeathView()`）。写探针时只调纯的那个。

**成因二：把"记录一个观察"挂在"前置条件成立才执行"的路径上。**

"见过降落动画"这件事原先记在 `shouldRestoreDeathView()` 里，而它只能经由
`restoreDeathView()` 到达 —— 可 `restoreDeathView()` 的第一道门正是
`Vars.player.dead() → return false`（"活着"才有"重生"可言），
**而降落动画期间玩家恰恰是死的**。于是那条记录在真正需要它的那段窗口里
永远执行不到，只能靠 600 帧（10 秒）超时兜底，表现为"重生后镜头不回死前视野"。

> **规则：`if(前置)` 之外的"无条件观察"要放在 `if` 之前、且与 `dead` 之类的
> 临时状态解耦。** 判断"我看到了什么"和"现在能不能动手"是两件事。

**成因三（同类）：调用点被更早的 `return` 跳过。**

原先恢复调用放在 `applyCameraHold()` 里，而 `apply()` 在它之前有一道
`if(Vars.renderer.isCutscene()) return;` —— 降落期间整个函数进不来。
只要在脑内模拟"这一帧会走到哪一行"，就会发现那条路径根本不存在。

> **规则：加了一个"每帧做一次"的动作后，回溯一遍它上游所有的 `return`，
> 确认目标帧真的能走到。** 放在"最外层守卫之后、任何业务分支之前"最安全。

**排查手法（下次直接用）：**

1. 日志**一次**打出全部前因（不要每帧只打一半），字段对齐、可肉眼比较。
2. 看到"探针一撤就红"，**先怀疑探针有副作用**，不要先怀疑编译器/缓存。
3. 副作用类探针改成只读镜像：把状态快照到独立变量，探针只读快照。
4. 加一个"帧号 + 关键布尔量"的逐帧表，比打点式断言快得多。

### 5.6 ⚠️ 别拿 `!= null` 判布尔字段（"未生效"的第二种根因）

`holdCamera()` 里原本有一道"观战中就别管"的门，写成：

```js
if(inp != null && inp.spectating != null) return false;   // 错！
```

`spectating` 是 **boolean 字段**（普通游玩 `false`，观战 `true`）。`false != null`
**恒为 true** —— 于是这道门**每帧都 return false**，整个压制从不生效，而从外面看
就是"模组好像没加载"。用户实测报的「未生效」，两个根因里这是第二个（第一个是
平移键的门，见 §3.5）。

> **规则：判"某个标志位是否打开"就写 `if(inp != null && inp.spectating)`。**
> `!= null`（判"取到了没"）和 `=== true`（判"严格等于真"）都不能拿来判布尔标志 ——
> 前者对 `false` 也成立，后者会把 Java 侧返回的其他真值形态挡掉。
> 拿不准字段类型时先反射（§1.4），别猜。

同一个坑还有两个变体，一起记下：

- **别把"取到了没"和"标志开着没"塞进同一个条件**。要分两步：
  `if(inp == null) return false;` 然后 `if(inp.spectating) return false;`，
  这样日志里说得出是"没取到"还是"在观战"。
- **覆写体抛异常会伪装成"这段代码没跑"**。`updateMovement` 覆写体最外层有安全网
  （§2.3）：抛异常 → 打印一行警告 → `superBroken = true` **永久停用覆写**。
  于是一处 `TypeError`（本次是 `unit.type` 忘了加括号 → `unit.type().omniMovement`）
  会同时压掉十几个断言，看起来像"整块逻辑没生效"。**看到"整体无声失效"先去日志里
  找那行 `⚠ … 已停用覆写`。**

**排查手法补充**（配合 §5.5）：

5. 探针里**别只打结论**，把全部输入一起打出来（本次一行
   `inp: spec=false locked=false pan=false mm=true wasd=false um=true` 直接锁定
   "输入全对、函数却返回 false" → 问题只可能在门本身）。
6. 定位到"某个函数不该返回 false"时，**用隔离副本法**：把 `main.js` 复制成
   `scripts/main-probe.js`、夹具复制成 `test-harness-probe.js` 并改加载路径，
   在副本里随便插探针，改完只删副本、不动交付件（本次靠它几分钟锁定
   `spectating` 那道门）。**副本必须删掉，别进交付包。**

### 5.7 ⚠️ 计时器：被覆写的对象身上有自己的字段

模组把 `panSpeed` **置 0** 来压掉原版的"朝鼠标推镜"，而 `panSpeed` 是
`DesktopInput` 的**实例字段**。我们换上去的是 `JavaAdapter` 造的**子类实例**：
游戏里 `Core.input` / `Vars.control.input` 都指向它，所以模组写的就是"真的那个"。

自测夹具一度在这里失真：夹具读自己那份基础 `input` 对象的 `panSpeed`（永远是 4.5），
而模组写的是适配器实例的字段 —— 断言因此假红。

> **规则：断言一个"模组会改的引擎字段"时，必须透过它与引擎的接缝读**
> （这里就是 `Core.input.<字段>`），不要读夹具自己的影子副本。
> 更稳的写法是让夹具直接 `Object.assign(input, { panSpeed: control.input.panSpeed })`，
> 或者干脆断言 `Core.input.panSpeed === 0`。

### 5.8 模组文档里要留的东西

- **版本号 + 版本日志**（每次改都写清"改了什么、为什么"）
- **字节码证据的位置**（哪个类、哪个偏移、什么现象），下次不用重查
- **已知限制**（如 §4.4 内容 mod 不能 hidden）

---

## 6. 踩坑清单（每条都真实崩过或"看着没效果"过）

| # | 现象 | 根因 | 解法 |
|---|---|---|---|
| 1 | `No main.js found for mod X` | `Compress-Archive` 写反斜杠条目名 | 用 `ZipArchive.CreateEntry("scripts/main.js", …)` |
| 2 | **崩游戏**：`Cannot call property aimX … it is "number"` | `aimX` 是**字段**，写成了 `aimX()` | 反射核对每个成员（§1.4） |
| 3 | **崩游戏**：`Cannot read property "update" from null` | `DesktopInput.prototype` 在 Rhino 里是 null | 不要用 `prototype`；改用 `JavaAdapter` 覆写子方法 |
| 4 | 语法错误：`'super' keyword unexpected here` | `super` 是保留字 | 不要用；见 §3.4 的"去掉成因"思路 |
| 5 | 覆写抛异常把游戏搞崩 | JavaAdapter 里的 JS 异常会冒到主循环 | 覆写体套 try/catch + 自动卸载（§2.3） |
| 6 | 功能看着没效果 | mock 空转 / 几何巧合（鼠标与屏幕中心同向） | 让游戏自报数据（§5.4） |
| 7 | **画面抖动** | "帧尾把相机写回上一帧"→ 两值之间摆 | 去掉成因（置零 panSpeed）+ 钉同一锚点（§3.4） |
| 8 | 改了相机但 `mouseWorld()` 解错位 | 没调 `Core.camera.update()` | 写完坐标必须刷矩阵（§2.5） |
| 9 | 控制台 `cam.xxx is not a function` | 对象属性解析不可靠 | 只挂全局函数 + 读回自检（§2.6） |
| 9b | 同一功能存了两份实现（对象 + 全局） | 冗余，文档要维护两套 | 留可靠的那套，删另一套（§2.6） |
| 9c | 脚本注释里抄了一大段原理，后来结论被推翻 | 注释与 METHOD.md 重复，改一处忘一处 | 注释只写"怎么做+约束"，原理归文档 |
| 10 | 进别人服务器被踢 | 装了非 hidden 的 mod | `hidden: true`（§4） |
| 11 | 标了 hidden 后自己的方块没了 | hidden 跳过 `loadContent()` | 内容 mod 不要 hidden（§4.4） |
| 12 | **"源码明明写着 X，行为却是 Y"** | 改端替换了核心类，你读的不是运行的那份 | 先确认改端替换了哪些类（§1.3） |
| 13 | PowerShell 编辑源码后中文乱码/行被吞 | `Set-Content` / `-replace` 默认编码问题 | **永远用 `edit` 工具编辑 UTF-8 源码**，不要用 shell 文本命令 |
| 14 | **"加探针就绿、去掉探针就红"** | 判定函数带副作用（`snapFrames++` / `snapSawCut=true`），探针调用它推进了状态 | 谓词不许改状态；观察与推进拆开（§5.5 成因一） |
| 15 | "重生后镜头不回死前视野" | "记录见过降落动画"被挂在 `player.dead() → return` 之后，降落期间（玩家是死的）永远走不到 | 无条件观察放到 `dead` 判定之外（§5.5 成因二） |
| 16 | "每帧该做的事根本没做" | 调用点上游有更早的 `if(isCutscene()) return` 把它跳过了 | 加每帧动作后回溯上游所有 `return`（§5.5 成因三） |
| 17 | **用户实测"未生效"，但一切日志正常** | `if(inp.spectating != null) return false` —— boolean 字段 `false != null` 恒真，那道门每帧都拦 | 判布尔标志就写 `if(inp.spectating)`；"取到了没"另起一步（§5.6） |
| 18 | **整块逻辑无声失效（十几个断言一起红）** | 覆写体抛 `TypeError`（`unit.type.omniMovement` —— `type()` 是方法）+ 安全网 `superBroken = true` 永久卸载 | 先找日志里的 `⚠ … 已停用覆写`；成员是方法还是字段先反射（§5.6 / §1.4） |
| 19 | 夹具断言"模组没改 panSpeed"，实际改了 | 模组写的是 `JavaAdapter` 实例自己的字段，夹具读的是影子副本 | 透过 `Core.input.<字段>` 读，或断言 `Core.input.panSpeed`（§5.7） |

---

## 7. 标准作业流程

```
① 明确"要改的到底是哪一方的行为"
     客户端（输入/渲染/手感）→ 只能改自己；服务端（规则/命令）→ 可做 Plugin 免装
     ↓
② 找源码位置
     grep 设置项键名 / 功能字符串 → 定位到类与行
     ↓
③ 确认运行的是哪一份
     改端替换了哪些核心类？（§1.3）  必要时提取 + 反汇编 + 双方对比
     ↓
④ 反射导出成员真实形态
     RefDump → 生成/更新 check-members.js 的规则表（§1.4）
     ↓
⑤ 选实现手段
     · 能覆写 protected/public 方法 → JavaAdapter + setInput（§2.1）
     · 改不动的东西（无法调父类）→ 去掉它的**成因**，别事后纠正（§3.4）
     · 需要"免装" → hidden: true；需要服务端逻辑 → Plugin（§4）
     ↓
⑥ 三重验证
     node --check           语法
     check-members.js       成员形态
     test-harness.js        行为回归（先确保 mock 忠实！§5.2）
     ↓
⑦ 打包与安装
     pack.ps1 → ZipProbe → 覆盖安装
     ↓
⑧ 进游戏看自检日志
     "hidden 自检：…" / "输入处理器已替换…[是本人=true]" / "drift 报告：…"
     ↓
⑨ 记录
     版本号 + 版本日志 + 字节码证据位置 + 已知限制
```

---

## 附录：本次涉及的关键源码位置速查

| 内容 | 位置 |
|---|---|
| 相机自动回单位 | `input/DesktopInput.java:283-291`（`lerpDelta` 在 289） |
| 自由视角下单位移动目标 | `input/DesktopInput.java:981-999`（目标在 985，松手在 992） |
| 推镜向鼠标（panCam） | `input/DesktopInput.java:294-297`；`camSpeed` 在 239 |
| `panning` 的赋值 | `input/DesktopInput.java:261-273`（273 是 `panning \|= detached`） |
| 设置项注册 | `ui/dialogs/SettingsMenuDialog.java` 的 `graphics.checkPref(...)` |
| 输入处理器替换 | `core/Control.java:385`（`setInput`） |
| 主循环调用顺序 | `core/Control.java` `update(){ input.update(); logic.update(); }` |
| mod 清单过滤 | `mod/Mods.java:940`（`getModStrings`） |
| mod 元文件候选名 | `mod/Mods.java:34` |
| hidden 跳过内容加载 | `mod/Mods.java:837-842` |
| Plugin 隐含 hidden | `mod/Mods.java:1180-1183` |
| 上报 mod 清单 | `core/NetClient.java:108` |
| 服务端 mod 校验/踢人 | `core/NetServer.java:210-224` |
| 自定义客户端校验 | `core/NetServer.java:239-242` |
| `Version.build == -1` 的含义 | `core/Version.java:21`（custom build） |
