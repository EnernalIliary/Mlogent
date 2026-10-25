# 学术端（v146 / CN-ARC BE-25737）的「自由视角」实现考据

> 目的：把那份老包里"自己写的自由视角"逐条读出来，和 v146 原版、以及现在的 160.5 对照，
> 判断**它到底做了什么今天没有的事**，以及模组要不要/能不能还原。
>
> 结论先说：**它做的每一件事，今天的 160.5 原版都已经有了**。它只是比当年原版早了一步。
> 详见 §4。

---

## 1. 这份老包是什么

| 项 | 值 |
|---|---|
| 文件 | `E:\Download\Mindustry-CN-ARC-BE-25737-Desktop.jar`（87.6 MB，5108 条目） |
| 游戏版本 | **v146**（包内 `updatelog` 首行 `[cyan]------------------------[v146-9/4]---------------------------`） |
| 字节码版本 | **major 52 = Java 8**（4273 个类；另有 80 个 51 = Java 7） |
| 分支特征 | 多了整个 `mindustry/arcModule/**` 包（ARCClassLoader / ARCClient / ARCChat / ReplayController / TimeControl / arcScanMode / picToMindustry …），即"CN-ARC 学术端"的私货 |
| 关键类 | `mindustry/input/DesktopInput.class` 40562 B（同时期的原版约 30 KB） |

因为它是 Java 8 字节码，本机的 Android JDK 8 自带 `javap` 能直接反汇编（现在的 160.5 是 major 61，那个 javap 读不了）。
反汇编产物：`F:\OneDrive\桌面\AtomicStates\saves\_old\old-DesktopInput.asm`（3941 行）、`old-DesktopInput.members`。

```powershell
# 提取 + 反汇编（可复现）
Add-Type -AssemblyName System.IO.Compression.FileSystem
$a=[System.IO.Compression.ZipFile]::OpenRead($jar)
[System.IO.Compression.ZipFileExtensions]::ExtractToFile($a.GetEntry('mindustry/input/DesktopInput.class'), "$out\DesktopInput.class", $true)
$a.Dispose()
& 'C:\Program Files\Android\jdk\jdk-8.0.302.8-hotspot\jdk8u302-b08\bin\javap.exe' -p -c -cp "$out" mindustry.input.DesktopInput > old-DesktopInput.asm
```

---

## 2. v146 原版：**完全没有**自由视角

从 GitHub 取 `v146` 的 `DesktopInput.java`（`https://raw.githubusercontent.com/Anuken/Mindustry/v146/core/src/mindustry/input/DesktopInput.java`）：
`update()` 里**一个 `detach-camera` 都没有**。它的相机逻辑只有三段：

```java
// v146 原版 update()
if(input.keyDown(Binding.pan) && !scene.hasField() && !scene.hasDialog()){
    panCam = true;
    panning = true;
}

if((Math.abs(axis(move_x)) > 0 || Math.abs(axis(move_y)) > 0 || keyDown(mouse_move)) && !scene.hasField()){
    panning = false;                       // ← 每帧都会被重置回 false
}

if(!locked){
    if(((player.dead() || state.isPaused()) && !ui.chatfrag.shown()) && !scene.hasField() && !scene.hasDialog()){
        if(keyDown(mouse_move)) panCam = true;
        camera.position.add(Tmp.v1.setZero().add(axis(move_x), axis(move_y)).nor().scl(camSpeed));
    }else if(!player.dead() && !panning){
        // 每帧把相机 lerp 回玩家/核心
        camera.position.lerpDelta(coreTarget != null ? coreTarget : player, smoothcamera ? 0.08f : 1f);
    }
    if(panCam){ /* 鼠标偏移推镜 */ }
}
```

后果：**松手立刻回弹**。你按平移键把镜头拖走，`panning` 只在按住的那些帧为 true，
一松手就被 `lerpDelta` 拽回单位（`smoothcamera=false` 时是 `lerpDelta(...,1f)`，一帧到位，等于瞬移回单位）。

`updateMovement` 也没有自由视角分支：

```java
movement.set(xa, ya).nor().scl(speed);
if(keyDown(mouse_move)) movement.add(input.mouseWorld().sub(player).scl(1f/25f*speed)).limit(speed);
```

单位永远朝**鼠标世界坐标**走，跟相机没关系。

---

## 3. 学术端加的 5 处（这就是"它自己写的自由视角"）

### ① 新增设置 + 开关键

```java
// 字节码 120-190
boolean detached = settings.getBool("detach-camera", false);
...
if(input.keyTap(Binding.detach_camera)){
    settings.put("detach-camera", detached = !detached);
    if(!detached) panning = false;
    follow = null;          // ← 连"跟随某个单位"也一起清
    spectating = null;
}
```

### ② `panning |= detached`（字节码 307-315）

```java
this.panning |= detached;
```

这一行是整套东西的**核心**：`panning` 为 true 时上面那段 `lerpDelta`（自动回位）不执行。
于是只要自由视角开着，相机就**再也不会自己回弹**。

### ③ 让 `detached` 复用"死亡/暂停"那条自由相机分支（字节码 340-342）

```java
if(((player.dead() || state.isPaused() || detached) && !ui.chatfrag.shown()) && ...){
    if(input.keyDown(Binding.mouse_move)) panCam = true;      // ← 右键也会推镜
    camera.position.add(WASD.nor().scl(camSpeed));            // ← WASD 平移相机
}
```

注意 **`if(keyDown(mouse_move)) panCam = true;` 是包在这一支里的**：
所以**自由视角下按住"移动单位"的键，原版同时把镜头朝鼠标推**。这正是用户一直抱怨的那条行为，
它在 v146 学术端就已经是这个样子了。

### ④ 分支里额外清了 `follow` / `spectating`

`follow` 是"相机跟随另一个单位"，`spectating` 是"观察某单位"。进自由视角时两者都清空，
避免"自由视角 + 还在跟随别人"打架。

### ⑤ `updateMovement` 加自由视角分支（字节码 56-135）

```java
if(settings.getBool("detach-camera")){
    movement.set(camera.position).sub(player).limit(speed);            // 目标 = 相机（屏幕中心）
    if(player.within(camera.position, 15f)){
        movement.setZero();
        unit.vel.approachDelta(Vec2.ZERO, unit.speed() * unit.type().accel / 2);   // 到位刹车
    }
}else{
    movement.set(xa, ya).nor().scl(speed);                            // 原版：朝鼠标走
    if(keyDown(mouse_move)) movement.add(input.mouseWorld().sub(player).scl(1f/25f*speed)).limit(speed);
}
```

**这就是"自由视角下单位一直朝着屏幕中心飞、松手也停不下来"的源头。**
原版没有 `else` 以外的路径，所以学术端把"朝鼠标走"整个换成了"朝相机走"。

### 附带：一个 `removePan` 设置（字节码 281-295）

```java
if(!settings.getBool("removePan")) panning = false;   // 紧接着又 panning |= detached
```

先置 false 再立即 `|= detached` → **净效果为零**，是死设置（大概作者想做"自由视角但不保留平移"）。
它在 `mindustry/arcModule/ui/auxilliary/ScriptTable` 里露了个勾选框。

---

## 4. 和现在的 160.5 对比：**原版已经把这 5 处全收了**

用同一个字符串扫描器查 Steam 的 `desktop.jar`（160.5）：

```
node saves\_tools\strscan.js "<steam>\jre\desktop.jar" 'detach-camera'
  mindustry/input/DesktopInput.class        ← 有
  mindustry/ui/dialogs/SettingsMenuDialog.class   ← 设置页里有这个勾选
```

| # | 学术端 v146 的做法 | v146 原版 | **160.5 原版** |
|---|---|---|---|
| ① | `detach-camera` 设置 + 开关键 | ❌ 没有 | ✅ 有（`SettingsMenuDialog` 里就是"自由视角"那一项） |
| ② | `panning \|= detached` | ❌ | ✅ 有 |
| ③ | 相机分支条件 `dead \|\| paused \|\| detached` | 只有 `dead \|\| paused` | ✅ 三个都有 |
| ③b | 该分支里 `mouse_move → panCam = true` | 有（但只在死亡/暂停时进得去） | ✅ 有 |
| ⑤ | `updateMovement` 的 detached 分支（目标=相机、15 格到位刹车） | ❌ 没有 | ✅ 有（模组的覆写就是照它逐行复刻的） |
| — | `removePan` | — | ❌ 没有（死设置） |
| — | 清 `follow` | v146 没这字段 | 160.5 有 `follow`，另行处理 |

**所以：那份老包的"自由视角"是今天原版自由视角的直系祖先，功能上没有它独占的东西。**
在今天的 160.5 上"还原它的效果"= 打开 `设置 → 图像 → 自由视角`，
**不需要任何模组**（除了用户抱怨的那条推镜行为，而那条在 v146 学术端里也是一样的）。

### 唯一真正变了的细节

| 细节 | v146 学术端 | 160.5（本机改端） |
|---|---|---|
| 自动回位开关 | 无（`panning \|= detached` 一刀切） | 多了 `freecam-recenter` 设置项（关掉 = 视角永不自动回位） |
| 平滑 | 只有 `smoothcamera`（0.08 / 1.0） | 同 |
| `player.mouseX` 赋值 | `unit.aimX()`（方法） | `unit.aimX`（**字段**，写成方法会崩） |
| 死亡后回死前视野 | 无 | 本模组 v5.4 加的 |

---

## 5. 对模组的结论

1. 模组**不需要**再实现一遍自由视角 —— 原版已经有了，且算法与学术端一致。
2. 用户觉得"老版本手感对"，最可能不是自由视角本身的差异，而是**当年没有模组在上面加覆写**：
   学术端的 `updateMovement` 就是原版行为，没有"按住右键让单位走到鼠标"这套自定义语义。
3. 因此若要"还原它的效果"，正确的做法是给模组加一个**「原版自由视角」模式**：
   不压镜（`camHold(false)`）、单位移动走原版分支（`camCursor(false)`）、
   即 `movement` 目标 = 相机、15 格到位刹车 —— 这两件事模组**已经能用现有开关做到**，
   只是没有一个"一键切换"的入口。
4. 反过来说，**v5.5 的压制是学术端没有的行为**（学术端自由视角下右键照样推镜），
   所以它是模组的净增量，不是"还原"能得到的。

---

## 6. ⚠ 重要：本机的改端源码里已经有同款补丁

`F:\OneDrive\桌面\AtomicStates\Mindustry-Source` 是 **上游 v159.3**（`git log -1` = `5811844 Fixed music fade issue`，
2026-07-11），工作区只有两个文件被改过：

```
 M core/src/mindustry/input/DesktopInput.java
 M core/src/mindustry/ui/dialogs/SettingsMenuDialog.java
```

`git diff` 显示这两处改动加的正是 **`freecam-recenter`** 与 **`freecam-cursor-move`** 两个开关：

```java
// ① 自动回位开关
}else if((!player.dead() || spectating != null) && !panning && settings.getBool("freecam-recenter", true)){

// ② 自由视角下"单位走到鼠标"
if(settings.getBool("detach-camera")){
    Vec2 targetPos = settings.getBool("freecam-cursor-move", true) && Core.input.keyDown(Binding.mouseMove)
        ? Tmp.v1.set(input.mouseWorld()) : camera.position;
    movement.set(targetPos).sub(player).limit(speed);
    float arrive = settings.getBool("freecam-cursor-move", true) ? 6f : 15f;
    if(settings.getBool("freecam-cursor-move", true) && !Core.input.keyDown(Binding.mouseMove)){
        movement.setZero();
        unit.vel.approachDelta(Vec2.ZERO, unit.speed() * unit.type().accel / 2f);
    }else if(player.within(targetPos, arrive)){ ... }
}
```

**含义**：`freecam-cursor-move`（默认 `true`）在**源码层**已经实现了"按住移动键 → 走到鼠标、松开即停、6 格到位"，
和本模组在 JS 层用 `JavaAdapter` 覆写 `updateMovement` 做的事**完全重叠**。
两个都装时，**JS 覆写会赢**（`Control.setInput()` 换掉处理器后，Java 侧那份补丁的方法根本不被调用）。

因此排查"模组到底有没有生效"时，必须先分清这三种情况：

| 现场 | 谁在控制 movement | 怎么判断 |
|---|---|---|
| 只有改端补丁 | Java 侧 `freecam-cursor-move` | 卸掉模组，行为不变 |
| 只有模组 | JS 覆写 | `camOverride()` 回 `installed`，且 `camWhere().ov` 有帧数 |
| 两个都在 | **JS 覆写优先** | 同上；`"freecam-cursor-move"` 设成 false 也不影响手感 |

---

## 7. 工具（本次新增，留在 `saves\_tools\`）

| 文件 | 作用 |
|---|---|
| `classinfo.js` | 列出 jar 条目、统计 class 字节码版本分布、按正则筛条目 |
| `ziplist.js` | 导出条目清单（用于两个 jar 的类名 diff） |
| `strscan.js` | 扫所有 class 的 Utf8 常量池，按关键词找"哪个类用了这个设置名/字符串" |
| `JavapRun.java` | 老工具；依赖 `com.sun.tools.javap`，**本机 Mindustry 的 jre 没有这个模块**，只能用 Android JDK 8 对 Java 8 的包 |
