# 自由视角两行改动（DesktopInput）

> 这份说明对应 **Mindustry 160.5**。你本地跑的是 `jre\desktop.jar`（160.5），
> 工作目录里的克隆是 **159.3**，但这两处的代码与字节码**逐行一致**（我用 javap 反汇编核对过）。
>
> 两个改动都已通过**类型校验**：把新增的表达式抽出来对着 `desktop.jar` 编译，`javac` 退出码 0。

---

## 改动 1：取消"镜头自动回到单位"（`update()`，第 283-290 行）

**位置**：[core/src/mindustry/input/DesktopInput.java](../Mindustry-Source/core/src/mindustry/input/DesktopInput.java) 里 `update()` 的第二个分支。

原版：

```java
}else if((!player.dead() || spectating != null) && !panning){
    //TODO do not pan
    Team corePanTeam = state.won ? state.rules.waveTeam : player.team();
    Position coreTarget = state.gameOver && !state.rules.pvp && corePanTeam.data().lastCore != null ? corePanTeam.data().lastCore : null;
    Position panTarget = coreTarget != null ? coreTarget : spectating != null ? spectating : player;

    Core.camera.position.lerpDelta(panTarget, Core.settings.getBool("smoothcamera") ? 0.08f : 1f);   // ← 就是这一句
}
```

改成（只加一个开关判断）：

```java
}else if((!player.dead() || spectating != null) && !panning && settings.getBool("freecam-recenter", true)){
    //TODO do not pan
    //NOTE: 加了 freecam-recenter 开关后，关掉它 = 视角永远不自动回到单位/核心。
    Team corePanTeam = state.won ? state.rules.waveTeam : player.team();
    Position coreTarget = state.gameOver && !state.rules.pvp && corePanTeam.data().lastCore != null ? corePanTeam.data().lastCore : null;
    Position panTarget = coreTarget != null ? coreTarget : spectating != null ? spectating : player;

    Core.camera.position.lerpDelta(panTarget, Core.settings.getBool("smoothcamera") ? 0.08f : 1f);
}
```

> 说明：`settings` 在这个类里指的是 `arc.Core.settings`（类头有 `import static arc.Core.*`）。
>
> **重要事实**：v160.5 里前面有一句 `panning |= detached;`（`update()` 第 273 行），
> 所以**自由视角开着时 `panning` 恒为 true，这一分支本来就不会执行** ——
> 如果你只开自由视角，这个开关看不出差别；但只要关掉自由视角（或切自由观察单位），它就会生效。

---

## 改动 2：单位改为"走到鼠标位置并停下"（`updateMovement()`，第 981-999 行）

**位置**：同一文件的 `updateMovement(Unit unit)`。

原版：

```java
if(settings.getBool("detach-camera")){
    Vec2 targetPos = camera.position;                       // ← 目标 = 屏幕中心

    movement.set(targetPos).sub(player).limit(speed);       // ← 就是这一句

    if(player.within(targetPos, 15f)){
        movement.setZero();
        unit.vel.approachDelta(Vec2.ZERO, unit.speed() * unit.type().accel / 2f);
    }
}else{
```

改成：

```java
if(settings.getBool("detach-camera")){
    //自由视角下单位移动的目标：
    //  原版 = camera.position（屏幕中心）→ 单位永远朝屏幕中心飞，松开键也不停，画面一直滚
    //  开关打开 = 按住"鼠标移动"时走到**鼠标指的位置**，够近就停；松开就停
    Vec2 targetPos = settings.getBool("freecam-cursor-move", true) && Core.input.keyDown(Binding.mouseMove)
        ? Tmp.v1.set(input.mouseWorld()) : camera.position;

    movement.set(targetPos).sub(player).limit(speed);

    float arrive = settings.getBool("freecam-cursor-move", true) ? 6f : 15f;

    if(settings.getBool("freecam-cursor-move", true) && !Core.input.keyDown(Binding.mouseMove)){
        //松开移动键 → 原地停下（原版这里没有"松手"的概念）
        movement.setZero();
        unit.vel.approachDelta(Vec2.ZERO, unit.speed() * unit.type().accel / 2f);
    }else if(player.within(targetPos, arrive)){
        movement.setZero();
        unit.vel.approachDelta(Vec2.ZERO, unit.speed() * unit.type().accel / 2f);
    }
}else{
```

三个关键点：

| 点 | 说明 |
|---|---|
| `Tmp.v1.set(input.mouseWorld())` | 用 arc 的临时向量，**不 new**、不破坏原版行为；目标是**鼠标世界坐标**而不是相机坐标 |
| 松手分支 | 原版没有"松手"，`movement` 每帧都被重算成朝屏幕中心，所以松开键单位还在飞 —— 这一支让它停下 |
| `arrive` 6f / 15f | 鼠标模式下 6 世界单位（≈0.75 格）就算到位；退回原版行为时仍是原来的 15f |

---

## 改动 3：两个开关的注册与文案

**注册**（`core/src/mindustry/ui/dialogs/SettingsMenuDialog.java`，`graphics.checkPref("detach-camera", false);` 之后）：

```java
if(!mobile){
    graphics.checkPref("detach-camera", false);
    //自由视角的两个附加开关（默认 = 修掉原版这两个手感问题）
    //  freecam-recenter   : 关掉后视角永远不自动回到单位/核心
    //  freecam-cursor-move: 自由视角下按住"鼠标移动"时，单位走到鼠标位置并停下
    graphics.checkPref("freecam-recenter", true);
    graphics.checkPref("freecam-cursor-move", true);
}
```

**文案**（这个克隆里没有 `core/assets`，所以写在你的资源目录 `assetsraw/assets/bundles/`）：

- `bundle.properties`（英文）
- `bundle_zh_CN.properties`（中文）

各加 4 个键：

```properties
setting.freecam-recenter.name = Free Camera: Auto-Recenter
setting.freecam-recenter.description = When off, the camera never moves back to your unit or core on its own.\nOnly relevant while Free Camera is enabled.
setting.freecam-cursor-move.name = Free Camera: Move Unit To Cursor
setting.freecam-cursor-move.description = While Free Camera is on, hold the mouse-move key to walk your unit to the cursor and stop there; releasing stops it.\nVanilla instead flies the unit toward the screen center, so the view keeps scrolling as if the camera were chasing the unit.
```

**没加文案也不会坏**：`Setting` 取不到键时会退回显示键名（界面上显示 `freecam-recenter`），功能照样生效。

---

## 构建与验证

```powershell
cd F:\OneDrive\桌面\AtomicStates\Mindustry-Source
.\gradlew.bat desktop:dist          # 产物在 desktop/build/libs/
```

验证清单（每一条都能单独判定）：

1. **设置 → 图像** 里，「自由视角」下面应出现两项：
   `Free Camera: Auto-Recenter` 和 `Free Camera: Move Unit To Cursor`
2. 开「自由视角」，**按住"鼠标移动"键（默认是鼠标侧键，你在设置→操作里绑的是右键）拖动**
   → 单位应当**走向鼠标**，到鼠标附近停下，画面不再持续滚动
3. **松开**按键 → 单位**原地停下**（这一条最能说明改动生效：原版会继续朝屏幕中心飞）
4. 把「Move Unit To Cursor」**关掉** → 单位立刻恢复原版行为（朝屏幕中心飞）
5. 把「Auto-Recenter」**关掉**、再**关掉自由视角** → 无论你怎么移动单位，镜头都不再被吸回单位

## 我改动了哪些文件

| 文件 | 改动 |
|---|---|
| `Mindustry-Source/core/src/mindustry/input/DesktopInput.java` | 改动 1 + 改动 2 |
| `Mindustry-Source/core/src/mindustry/ui/dialogs/SettingsMenuDialog.java` | 注册两个开关 |
| `assetsraw/assets/bundles/bundle.properties` | 英文文案 |
| `assetsraw/assets/bundles/bundle_zh_CN.properties` | 中文文案 |

> ⚠ `Mindustry-Source` 是你自己的 git 克隆，我用 `git diff` 就能完整回退；
> 如果你不希望我直接动它，告诉我，我把改动挪成 patch 文件（`.diff`）由你自己 `git apply`。
