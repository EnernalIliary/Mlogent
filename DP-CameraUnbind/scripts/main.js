// ============================================================================
//  自由视角修复 (Camera Unbind) —— scripts/main.js    v4.0
//
//  只改两件事，都发生在原版 DesktopInput 里：
//    ① updateMovement()  —— 自由视角下单位的移动目标是 camera.position（屏幕中心），
//       改成"鼠标世界坐标"，并补上原版没有的"松手即停"。
//       做法：JavaAdapter 生成子类覆写该方法，再 Control.setInput() 换掉输入处理器。
//    ② update() 的 panCam 段 —— 按住"鼠标移动"键时原版会把镜头推向鼠标。
//       做法：按住期间把 panSpeed/panBoostSpeed 置 0（位移变成"加 0"），
//       并把相机钉在进入拖拽时的锚点。**每帧写同一个值**，所以不抖。
//
//  深度原理、字节码证据、踩坑清单全部在 METHOD.md，此处不再重复。
//
//  ── 三条 Rhino 铁律 ─────────────────────────────────────────────────
//   1) 按键常量写全限定名 Packages.arc.input.KeyCode.v（裸 KeyCode.v 会抛异常，
//      而顶层抛异常会让整个脚本静默中止）
//   2) 同名字段遮蔽方法：unit.aimX / x / type 是**字段**（写 aimX() 会崩游戏），
//      而 unit.speed() / player.dead() 是方法
//   3) 事件回调直接传函数字面量即可
//   初始化全程包在 try 里：任何一步失败都会在日志里留下 [camera-unbind] 的痕迹。
// ============================================================================

function __cameraUnbindMain(){
    "use strict";

    var log = function(msg){ print("[camera-unbind] " + msg); };

    // ============================ 配置区 ============================
    var MOD_VERSION  = "5.6";               // 版本号（camVersion() 会回报它）
    var PREF_KEY     = "dp-camera-unbind";  // 设置项的键名（存进 settings.bin）
    var DEFAULT_ON   = true;                // 默认开：本版是"让自由视角好用"的修复，装上即生效

    // 「学术端原味」模式（v5.6 新增，默认**关**）。
    //
    // 背景：用户的旧包（v146 + CN-ARC，BE-25737）自己给原版加了自由视角，
    //   5 处改动全部考据在 LEGACY-FREECAM.md 里。今天 160.5 已经把 5 处全收了，
    //   唯一能"还原"的差异是**它没有模组这层覆写**，所以单位移动用的是原版语义：
    //     目标 = camera.position（屏幕中心），15 格内到位刹车。
    //   本开关把模组拨回那个语义，**但保留相机压制**（镜头不乱动是用户要的净增量）。
    //
    // 与主开关的关系（两个都是"开"时）：
    //   · 单位移动 = 原版（朝屏幕中心走）
    //   · 相机     = 仍被压住（按住移动键时不被推向鼠标）
    //   · WASD     = 平移相机（原版语义），不再被当成"在移动单位"
    // 只开主开关：单位走到鼠标位置 + 相机压住（v5.5 行为）。
    var LEGACY_KEY   = "dp-camera-unbind-legacy";
    var DEFAULT_LEGACY = false;

    // ⚠ 热键必须避开原版**已绑定**的键 —— 尤其是有正式键位名、玩家能改的那些。
    //   踩过的坑：最初用 V 和 N，结果
    //     Binding.respawn      = KeyCode.v   // ← V 是原版「重生」！死亡界面写着「按 V 键重生」
    //     Binding.planetMap    = KeyCode.n   // ← N 是「星球地图」
    //   于是按 V 复活的同时把本模组的开关 toggle 掉了，表现为"有时弹回去有时不弹"。
    //   （顺带纠正一个误解：Binding.detachCamera 的默认值是 KeyCode.**unset**，
    //     自由视角默认根本没绑键 —— 我当时误以为 V 是它。）
    //
    //   已占用的常用键（Binding.java 全文）：WASD/SHIFT/CTRL/ALT、Q E R T F G H J C M N P V B X Z、
    //   1-0、方向键、空格、TAB、ENTER、逗号句号、方括号、F1 F5 F6 F8 F11 F12、鼠标三键、滚轮。
    //   实测 F10 在本体与改端 MindustryX 里都**没有任何引用**，故用它。
    //   写 null 表示不要该热键。
    var KEY_TOGGLE   = ["f10"];             // F10：开关本功能
    var KEY_RECENTER = null;                // 默认不给"拉回单位"配热键（N 已被星球地图占用）
    var KEY_LEGACY   = ["f9"];              // F9：切换「学术端原味」（v5.6 新增；F9 同样空闲）
    // ================================================================

    try{
        var Core   = Packages.arc.Core;
        var Events = Packages.arc.Events;
        var Timer  = Packages.arc.util.Timer;
        var Vars   = Packages.mindustry.Vars;
        var ET     = Packages.mindustry.game.EventType;

        var settings = Core.settings;
        var ui       = Vars.ui;

        // ---------------------------- 状态 ----------------------------
        var lastUnitId  = 0;
        var lastDead    = false;
        var wasBusy     = false;        // 上一帧界面是否在吃键盘

        // 「死前视野」快照：死亡那一刻的相机坐标（null = 没有待恢复的视野）。
        // 用途见 handleDeathView()/applyCameraHold() —— 重生落地后定位回这里。
        var deathSnap   = null;
        // 取快照之后有没有真的进过"降落动画"（isCutscene）。恢复要等落地动画走完
        // （见 shouldRestoreDeathView），这个标志就是"落地"的判定依据。
        var snapSawCut  = false;
        var snapFrames  = 0;            // 取快照后经过的帧数（没进过过场时的超时兜底）
        // 恢复「死前视野」之后的短暂锁定帧数。
        // ⚠ 必须有：holdCamera() 要求"玩家此刻正按着移动键"，而重生落地那一刻玩家
        //   往往什么都没按 —— 恢复的下一帧 holdCamera() 就为假，applyCameraHold()
        //   会把 pinned 清掉、原版 AutoFollow 立刻把相机从死前视野 lerp 回重生点，
        //   肉眼看到的就是"镜头闪一下又飞走"。夹具实测：恢复后第 2 帧相机从 1200
        //   被拽回 6000。给一小段宽限，让"把镜头放回去"这件事真的站得住。
        var restoreHold = 0;
        // 宽限长度：0.5 秒（30 帧）。够让玩家看清镜头回到死前视野，又不会久到
        // 妨碍他立刻接管。
        var RESTORE_HOLD_FRAMES = 30;

        // ------------------------- 设置项的读写 -------------------------
        function settingOn(){
            try{ return !!settings.getBool(PREF_KEY, DEFAULT_ON); }
            catch(e){ return false; }
        }

        function setSetting(v){
            try{ settings.put(PREF_KEY, !!v); }catch(e){ log("写设置失败：" + e); }
        }

        // 「学术端原味」模式的读写。和主开关完全独立的两份真相（各自一个设置键），
        // 但**语义上**它只在主开关开着时才有意义：主开关关着 = 模组整个不接管。
        function legacyOn(){
            try{ return !!settings.getBool(LEGACY_KEY, DEFAULT_LEGACY); }
            catch(e){ return false; }
        }

        function setLegacy(v){
            try{ settings.put(LEGACY_KEY, !!v); }catch(e){ log("写 legacy 设置失败：" + e); }
        }

        // 注册"默认值"。
        // ⚠ 这里**只能**用 settings.defaults()（只补默认值，不碰玩家已经保存的选择），
        //   绝对不能用 settings.put() —— 那会在每次启动时把玩家勾上的开关重新抹成默认值。
        // （官方 SettingsTable.checkPref/CheckSetting 内部就是 settings.defaults(name, def)）
        function registerDefault(){
            try{
                settings.defaults(PREF_KEY, !!DEFAULT_ON);
                settings.defaults(LEGACY_KEY, !!DEFAULT_LEGACY);
                return true;
            }catch(e){ log("注册默认值失败：" + e); return false; }
        }

        // 把「镜头解绑」复选框塞进「设置 → 图像」页，**紧跟在原版「自由视角」（detach-camera）后面**。
        // 用官方现成的 CheckSetting(String,boolean,Boolc)（第三个参数传 null 表示不需要回调），
        // 这样标题/描述/落盘/重置默认全都由游戏自己的机制负责。
        function injectSetting(){
            var table = null;
            try{ table = ui.settings.graphics; }catch(e){}
            if(table == null){ log("拿不到「图像」设置页（ui.settings.graphics 为空）"); return false; }

            // 默认值先注册好（玩家已经保存过的选择不受影响）
            registerDefault();

            var list = null;
            try{ list = table.getSettings(); }catch(e){ log("getSettings() 失败：" + e); return false; }
            if(list == null){ log("设置列表为空"); return false; }

            // 幂等：已经注入过就不重复加（避免界面上出现两个同名开关）
            try{
                for(var i = 0; i < list.size; i++){
                    var it = list.get(i);
                    if(it != null && it.name == PREF_KEY){
                        log("设置项已存在，跳过注入（当前值=" + settingOn() + "）");
                        return true;
                    }
                }
            }catch(e){ log("遍历设置列表出错（继续注入）：" + e); }

            var CheckSetting = null;
            try{ CheckSetting = Packages.mindustry.ui.dialogs.SettingsMenuDialog.SettingsTable.CheckSetting; }catch(e){}
            if(CheckSetting == null){ log("取不到 CheckSetting 类"); return false; }

            var el = null;
            try{
                // 官方给模组用的构造器；(String name, boolean def, @Nullable Boolc changed)
                // 勾选状态由 CheckSetting.add() 里 box.update(() -> box.setChecked(settings.getBool(name))) 读，
                // 值只有一个来源，所以第三个参数传 null 就够。
                el = new CheckSetting(PREF_KEY, !!DEFAULT_ON, null);
            }catch(e2){
                log("new CheckSetting 失败：" + e2);
                return false;
            }
            if(el == null){ log("new CheckSetting 返回空对象"); return false; }

            // 标题/描述：Setting 的构造器会查 setting.<name>.name（我们 bundles/ 里已提供）。
            // 万一 bundle 没吃到（版本/语言不匹配），这里兜底写中文，保证界面上不是一串英文键名。
            try{
                if(el.title == null || el.title.length === 0 || el.title == PREF_KEY || el.title.indexOf("setting.") === 0){
                    el.title = "镜头解绑（单位走到鼠标位置）";
                    log("bundle 里没有标题，使用内置中文标题");
                }else{
                    log("设置项标题：" + el.title);
                }
                if(el.description == null || el.description.length === 0){
                    el.description = "开着「自由视角」时，按住鼠标移动键会让单位走到鼠标指的位置就停下，相机全程一动不动。"
                        + "原版是让单位一直朝屏幕中心飞，所以画面会一直滚。"
                        + "自由视角关着时本模组不生效；按 F10 开关本功能（F10 是刻意挑的空闲键，"
                        + "不占用原版任何键位 —— 尤其避开了「重生」的 V）。";
                }
            }catch(e3){ log("写标题/描述失败（不影响功能）：" + e3); }

            // 插到「自由视角」那一项后面。SettingsTable.list 是 protected 字段，
            // 反射拿不到就退化成"加到末尾"（功能一样，只是位置在页尾）。
            var inserted = false;
            try{
                var f = table.getClass().getDeclaredField("list");
                f.setAccessible(true);
                var arr = f.get(table);
                var idx = -1;
                for(var k = 0; k < arr.size; k++){
                    var s = arr.get(k);
                    if(s != null && s.name == "detach-camera"){ idx = k; break; }
                }
                if(idx >= 0){
                    arr.insert(idx + 1, el);
                    inserted = true;
                }else{
                    log("没找到原版「自由视角」项（detach-camera），退化为加到页尾");
                }
            }catch(ex){ log("反射插入失败（退化为加到页尾）：" + ex); }

            if(!inserted){
                try{ list.add(el); }catch(e4){ log("加入设置列表失败：" + e4); return false; }
            }

            // 第二个复选框：「学术端原味」。失败不影响主功能（还有控制台 camLegacy()）。
            try{ injectLegacySetting(table, list); }catch(e6){ log("注入 legacy 设置项失败（不影响功能）：" + e6); }

            try{ table.rebuild(); }catch(e5){ log("rebuild 失败：" + e5); }

            log("设置项注入成功：设置 → 图像 → 自由视角 下面「" + el.title + "」（当前值=" + settingOn()
                + (inserted ? "，位置=紧随自由视角" : "，位置=页尾") + "）");
            return true;
        }

        // v5.6：在同一个设置页里再塞一个「学术端原味」复选框，紧跟主开关后面。
        //   幂等：先按 LEGACY_KEY 扫一遍，已存在就跳过。
        //   失败**不影响主功能** —— 最坏情况只是这个复选框进不了界面，
        //   仍然可以用控制台 camLegacy(true|false) 切换。
        function injectLegacySetting(table, list){
            try{
                for(var i = 0; i < list.size; i++){
                    var it = list.get(i);
                    if(it != null && it.name == LEGACY_KEY) return true;
                }
            }catch(e){ /* 遍历失败就继续尝试注入 */ }

            var CheckSetting = null;
            try{ CheckSetting = Packages.mindustry.ui.dialogs.SettingsMenuDialog.SettingsTable.CheckSetting; }catch(e2){}
            if(CheckSetting == null){ log("legacy：取不到 CheckSetting 类"); return false; }

            var el = null;
            try{ el = new CheckSetting(LEGACY_KEY, !!DEFAULT_LEGACY, null); }
            catch(e3){ log("legacy：new CheckSetting 失败：" + e3); return false; }
            if(el == null){ log("legacy：CheckSetting 返回空对象"); return false; }

            try{
                if(el.title == null || el.title.length === 0 || el.title == LEGACY_KEY || el.title.indexOf("setting.") === 0){
                    el.title = "学术端原味（单位朝屏幕中心走）";
                }
                if(el.description == null || el.description.length === 0){
                    el.description = "勾上后单位移动**完全按原版**：目标 = 屏幕中心，走到 15 格内停下并刹车；"
                        + "WASD 变成平移镜头而不是移动单位。"
                        + "「按住移动键时镜头不被推向鼠标」这条压制**仍然有效**。"
                        + "这个模式复刻的是 v146 学术端（BE-25737）那份自己写的自由视角的手感，"
                        + "考据见 LEGACY-FREECAM.md。默认关；也可以按 F9 切换。";
                }
            }catch(e4){ log("legacy：写标题/描述失败（不影响功能）：" + e4); }

            // 紧跟主开关（主开关在 detach-camera 后面，所以这里就是 detach-camera + 2）
            var placed = false;
            try{
                var f = table.getClass().getDeclaredField("list");
                f.setAccessible(true);
                var arr = f.get(table);
                var idx = -1;
                for(var k = 0; k < arr.size; k++){
                    var s = arr.get(k);
                    if(s != null && s.name == PREF_KEY){ idx = k; break; }
                }
                if(idx >= 0){
                    arr.insert(idx + 1, el);
                    placed = true;
                }else{
                    log("legacy：没找到主开关项，退化为加到页尾");
                }
            }catch(e5){ log("legacy：反射插入失败（退化为页尾）：" + e5); }

            if(!placed){
                try{ list.add(el); }catch(e6){ log("legacy：加入设置列表失败：" + e6); return false; }
            }
            log("设置项注入成功（legacy）：「" + el.title + "」（当前值=" + legacyOn() + "，位置="
                + (placed ? "紧随主开关" : "页尾") + "）");
            return true;
        }

        // ---------------------------- 热键 ----------------------------
        function keyPick(names, what){
            if(names == null) return null;
            var K = Packages.arc.input.KeyCode;
            for(var i = 0; i < names.length; i++){
                try{
                    var v = K[names[i]];
                    if(v != null){
                        log("热键 " + what + " = KeyCode." + names[i]);
                        checkHotkeyFree(names[i], v, what);
                        return v;
                    }
                }catch(e){}
            }
            log("热键 " + what + " 不可用（不影响设置页里的开关）");
            return null;
        }

        // 热键冲突自检：把候选键与原版 Binding 里的**每一个**键位比对。
        //   ⚠ 这条检查是为了补上一个真实事故：最初用 V 当开关热键，而 V 是原版「重生」
        //     （Binding.respawn，死亡界面还写着「按 V 键重生」）—— 按 V 复活的同时
        //     把本模组开关 toggle 掉了，表现为"镜头有时弹回去有时不弹"。
        //   有了这条，以后挑到冲突键会在启动日志里立刻报出来。
        function checkHotkeyFree(name, keyCode, what){
            try{
                var B = Packages.mindustry.input.Binding;
                var fields = B.getClass().getFields();
                var clash = [];
                for(var i = 0; i < fields.length; i++){
                    try{
                        var f = fields[i];
                        var kb = f.get(B);
                        if(kb == null || kb.value == null) continue;
                        var v = kb.value;
                        // KeyBind 的值可能是 KeyCode，也可能是 KeyBind$Axis（含 min/max）
                        if(v === keyCode || v.min === keyCode || v.max === keyCode){
                            clash.push(f.getName());
                        }
                    }catch(e){}
                }
                if(clash.length > 0){
                    log("⚠ 热键冲突！" + what + " 用的 " + name + " 已被原版占用：" + clash.join(", ")
                        + " —— 请改 KEY_TOGGLE / KEY_RECENTER（见文件头配置区）");
                }else{
                    log("热键自检：" + name + " 未被原版任何键位占用 ✓");
                }
            }catch(e){
                log("热键自检跳过（" + e + "）");   // 只是自检，不该影响功能
            }
        }

        var KEY_ON   = keyPick(KEY_TOGGLE,   "开关镜头解绑");
        var KEY_BACK = keyPick(KEY_RECENTER, "视角拉回单位");
        var KEY_LEG  = keyPick(KEY_LEGACY,   "切换学术端原味");

        // 界面正在吃键盘（聊天 / 控制台 / 输入框）时不要抢按键
        function uiBusy(){
            try{
                if(Core.scene != null && Core.scene.hasKeyboard()) return true;
                if(ui.chatfrag != null && ui.chatfrag.shown()) return true;
                if(ui.consolefrag != null && ui.consolefrag.shown()) return true;
            }catch(e){}
            return false;
        }

        // ---------------------------- 提示 ----------------------------
        function notify(msg){
            try{ ui.showInfoFade(msg); return; }catch(e){}
            try{ ui.showInfo(msg); return; }catch(e){}
            log("提示（无法弹窗）：" + msg);
        }

        function label(){
            try{
                var k = "setting." + PREF_KEY + ".name";
                if(Core.bundle != null && Core.bundle.has(k)) return Core.bundle.get(k);
            }catch(e){}
            return "镜头解绑";
        }

        // ------------------- 视角"该看谁"（与原版一致）-------------------
        // 自由观察的单位 > 死亡时的核心 > 玩家自己。
        // 死亡/观察时把相机**直接**放过去（这两个时刻原版也会这么干）。
        function target(){
            if(Vars.player == null) return null;
            try{
                var input = Vars.control != null ? Vars.control.input : null;
                var spec = input != null ? input.spectating : null;
                if(spec != null && spec.isValid && spec.isValid()) return spec;
            }catch(e){}
            try{
                if(Vars.player.dead()){
                    var core = Vars.player.bestCore();
                    if(core != null) return core;
                }
            }catch(e){}
            return Vars.player;
        }

        // 直接把相机放过去（一次性动作，只用于死亡 / 观察 / 热键 N）
        function cameraTo(pos){
            if(pos == null) return;
            var x = pos.x, y = pos.y;
            if(isNaN(x) || isNaN(y)) return;
            try{
                Core.camera.position.set(x, y);
                // ⚠ 改完坐标必须刷新相机矩阵：Core.input.mouseWorld() 是拿 camera.inv
                //   做逆投影的，而 inv 只在 Camera.update() 里重算（游戏原本每帧在
                //   Renderer.draw() 里更新一次）。不刷新就会解出错位的世界坐标。
                Core.camera.update();
            }catch(e){}
        }

        // ------------------- 「死前视野」的记与恢复 -------------------
        // 需求（用户选定）：死亡瞬间把锚点钉在**死前那一刻的视野**上；死亡延迟与
        // 落地动画期间一律放手，让游戏把动画走完；重生之后再定位回死前视野。
        //
        // 为什么必须记在 `changed && dead`（死亡的那一帧）而不是等落地结束：
        //   160.5 里没有任何代码在死亡时动相机，动相机的是两条既有的 vanilla 路径 ——
        //     · CoreBlock.zoomLaunch() 里 `Core.camera.position.set(this)`（降落锁核心）
        //     · 延迟重生：PlayerComp.update() 里 `deathTimer >= deathDelay` 才 requestSpawn
        //   等落地结束再记，记到的就是**核心**坐标 —— 那正是"重生后视角被拉到新单位"
        //   的成因（新单位恰好生成在核心处，见 CoreBlock.playerSpawn）。
        //   所以要在相机还没被挪走之前记 —— 也就是 apply() 里**先 snapDeathView()、
        //   再 cameraTo(target())** 那个顺序（cameraTo 会把相机放到核心）。
        function snapDeathView(){
            try{
                var c = Core.camera.position;
                if(isNaN(c.x) || isNaN(c.y)) return;
                deathSnap = { x: c.x, y: c.y };
                snapSawCut = false;      // 还没进过降落动画
                snapFrames = 0;
                log("已记下死前视野 " + Math.round(c.x) + "," + Math.round(c.y) + "（重生后定位回这里）");
                console.log('[SNAP] took ' + Math.round(c.x) + ',' + Math.round(c.y));
            }catch(e){ deathSnap = null; }
        }

        // 该不该把相机恢复成死前视野？两件事都要成立：
        //   ① 已经过了"游戏自己在放降落动画"的阶段（isCutscene → landTime > 0）；
        //   ② 已经有有效单位（重生完成）。
        //
        // ⚠ 曾经还有第③条「玩家有没有在死亡空档里自己挪走视角」，判据试过三版，
        //   **全都删了**。写下来免得第四次再犯：
        //   ①版「用 movedAway」→ 错：死亡期间我们一直在放手，camWasPinned 早就是 false，
        //        等恢复时 movedAway 恰好为 false，恢复分支根本不执行。
        //   ②版「相机离快照 > 600 格就算玩家挪过」→ 错：**本模组自己在死亡那一帧
        //        就 cameraTo(核心)**（与原版一致），战局里核心离死亡地点通常是几千格，
        //        于是在"核心 ≠ 死亡地点"的任何一局里恢复都会被误判掉。夹具实测：
        //        f=133 `snap=1200,1300 cam=6000,6000` → 距离 6700 > 600 → 直接放弃。
        //   ③版「比到**核心**的距离」→ 同样错，而且错在最常见的成功路径上：重生单位
        //        确实在核心，可**落地动画结束时的相机并不在核心**。夹具实测：
        //        core=(5000,5000)、重生单位与相机都在 (6000,6000) → 距离 1414 > 603
        //        → 恢复被自己挡掉，镜头停在 6000 而不是死前的 1200。
        //   结论：**没法定量区分**"原版把相机挪到核心附近"和"玩家自己平移过"。别再试了。
        //   现在的做法是压根不猜 —— 恢复时机足够早（落地那一段 isCutscene 还在，
        //   我们根本没在接管），玩家真在这段里平移了，下一帧 holdCamera() 与
        //   「按下 pan 键」两条都会让位，下面那条即时判据已经够用。
        // 「死前视野」的观察记录 —— 必须在**死亡判定之外**做。
        //
        // ⚠⚠ 这是本功能最后一个坑，也是"加探针就绿、去掉探针就红"那个 heisenbug 的真身。
        //   原先"记录见过降落动画"这件事写在 shouldRestoreDeathView() 里，而那个函数
        //   只能从 restoreDeathView() 走到 —— 可 restoreDeathView() 的第一道门是
        //   `Vars.player.dead() → return false`（活着才有"重生"可言），**而降落动画
        //   期间玩家恰恰是死的**。于是：
        //     · 降落那段永远进不去 → snapSawCut 永远是 false
        //     · 回到 !snapSawCut 分支只能靠 snapFrames 涨到 600（10 秒超时）兜底
        //     · 表现："重生后镜头不回死前视野"（3 条断言红）
        //   而我在 restoreDeathView() 里加的调试探针**自己调了一次
        //   shouldRestoreDeathView()**，顺手把 snapSawCut 置了 true —— 于是探针在就绿、
        //   探针一撤就红（95/0 ↔ 92/3），连查四次才定位。
        //   教训：**"记录一个观察"不能挂在"某个前置条件成立才执行"的路径上**；
        //        判定函数带副作用（snapFrames++ / snapSawCut=true）会让探针扰动结论。
        //   现在拆成两件事：观察在这里（无条件、只要有快照），恢复时机仍由
        //   shouldRestoreDeathView() 负责。
        function recordDeathViewCut(){
            if(deathSnap == null || snapSawCut) return;
            try{
                if(Vars.renderer != null && Vars.renderer.isCutscene()) snapSawCut = true;
            }catch(e){}
        }

        function shouldRestoreDeathView(){
            if(deathSnap == null) return false;
            var cut = false;
            try{ cut = Vars.renderer != null && Vars.renderer.isCutscene(); }catch(e){}
            // 正在放降落动画 —— 用户选定（m08021）"落地动画允许走完"：这段里一个字节
            // 都不碰相机。注意这里**只判定、不记录**："见过降落"由 recordDeathViewCut()
            // 在更早、且不受 dead 判定影响的地方记（否则又回到那个 heisenbug）。
            if(cut) return false;
            var u = null;
            try{ u = Vars.player.unit(); }catch(e){}
            if(u == null || !u.isValid()) return false;                                // 还没重生；快照留着
            // ⚠ 必须等"见过降落、且降落已经结束"才恢复。否则恢复会提前到**死亡那一帧**
            //   就跑掉（那一帧 dead 已为真……但那一帧 isCutscene 还是 false，条件恰好
            //   全满足），快照当场被消费，落地后就无处可回。夹具实测：死亡帧 745 就打印了
            //   "重生落地结束：定位回死前视野 1200,1300"，到真正的重生帧 761 已无快照。
            //   例外：死亡但渲染层没进过过场（没有降落动画可等）→ 别死等，用超时兜底。
            if(!snapSawCut){
                snapFrames++;
                if(snapFrames < 600) return false;      // 最多等 10 秒，之后照样恢复
            }
            // 玩家此刻正按着平移键 → 尊重玩家当下的视野，这次不恢复
            try{
                var B = Packages.mindustry.input.Binding;
                if(Core.input.keyDown(B.pan)) return false;
            }catch(e){}
            return true;
        }

        // 「死前视野」的一次性恢复 —— 在 applyCameraHold() 最开头调用，**必须先于
        // holdCamera() 判断**。
        //
        // ⚠ 这里踩了第二个坑：曾经把恢复写在 `if(!holdCamera()) return;` 之后，
        //   而 holdCamera() 要求"玩家此刻正按着移动键/WASD"。可重生的那一刻玩家
        //   往往还什么都没按（落地动画刚结束），于是 holdCamera() 为假、恢复被跳过；
        //   等玩家终于按下移动键时，apply() 已在更早的帧把快照清掉（见那边的注释）。
        //   帧日志证据：f=133 `hold=false snap=yes dead=false` —— 已经复活、快照还在，
        //   但就是没恢复。
        //   语义上也应该是这样：把镜头放回去是**一次性动作**，跟"此刻该不该按住相机"
        //   是两件事。恢复之后 holdCamera() 若为真，下面照常把它钉住。
        function restoreDeathView(){
            if(deathSnap == null) return false;
            if(!settingOn()) return false;
            if(!cameraHoldEnabled) return false;
            try{
                if(Vars.player == null || Vars.player.dead()) return false;
                if(!settings.getBool("detach-camera", false)) return false;   // 只在自由视角下
                if(uiBusy()) return false;
            }catch(e){ return false; }
            if(!shouldRestoreDeathView()) return false;
            pinX = deathSnap.x;
            pinY = deathSnap.y;
            deathSnap = null;
            pinned = true;
            camWasPinned = false;
            restoreHold = RESTORE_HOLD_FRAMES;   // 宽限期内即使没按移动键也钉住
            cameraTo({ x: pinX, y: pinY });
            log("重生落地结束：定位回死前视野 " + Math.round(pinX) + "," + Math.round(pinY));
            return true;
        }

        // 说明：旧的 restoreCamera(px,py) 已删除 —— 现在不做事后还原，
        // 相机由 applyCameraHold()（置零 panSpeed + 钉锚点）处理。

        function recenter(){
            var t = target();
            if(t == null) t = Vars.player;
            cameraTo(t);
            notify("[" + label() + "] 视角已拉回单位");
        }

        // 诊断用：把"谁在操作相机"的现场状态一次性取出（camWhere() 会回报）
        function diagState(){
            var o = { panning: null, wasd: false, cursor: false };
            try{
                var inp = Vars.control != null ? Vars.control.input : null;
                o.panning = inp != null && inp.panning === true;
            }catch(e){}
            try{
                o.wasd = Math.abs(Core.input.axis(Packages.mindustry.input.Binding.moveX)) > 0
                      || Math.abs(Core.input.axis(Packages.mindustry.input.Binding.moveY)) > 0;
            }catch(e){}
            o.cursor = mouseMoveHeld();
            return o;
        }

        // ------------------- 自由视角下"走到鼠标位置" -------------------
        // 原版 DesktopInput.updateMovement() 在自由视角（detach-camera）下是：
        //     Vec2 targetPos = Core.camera.position;                 // ← 目标 = 屏幕中心
        //     movement.set(targetPos).sub(player).limit(speed);      // ← 永远朝屏幕中心飞
        //     if(player.within(targetPos, 15f)){ movement.setZero(); … }
        // 于是单位总往屏幕中心飞、松开鼠标也不停 → 画面持续滚动，看起来像"镜头跟着单位走"。
        //
        // 做法（v3.0 起改用真正的子类覆写，不再靠每帧抢 movement）：
        //   用 Rhino 的 JavaAdapter 生成 DesktopInput 的子类，覆写 protected updateMovement(Unit)，
        //   整段照抄原版，只把上面那一处目标换成"鼠标世界坐标 + 松手即停"，
        //   然后 Control.setInput(...) 把输入处理器换掉（它会正确处理注册/注销）。
        //   这样是**方法级覆写**，没有帧序问题，也不需要重新构建游戏。
        // 诊断用：是否"处在自由视角 + 正按着移动键"（= 本模组正在接管单位移动）
        function mouseMoveDown(){
            try{
                if(!settings.getBool("detach-camera", false)) return false;
                return mouseMoveHeld();
            }catch(e){ return false; }
        }
        var DBG = { d: -1, n: 0 };   // d = 单位到鼠标的世界距离；n = 覆写生效帧数
        var OV = { frames: 0, holding: false };   // 覆写内部状态（camWhere() 会回报）
        // 诊断：每帧实际选了哪个目标。camDrift() 跑完会回报。
        //   mouse  = 走本模组分支（目标是鼠标世界坐标）
        //   camera = 走原版分支（目标是相机/屏幕中心）
        //   maxTargetVsCam = "鼠标世界坐标 离 相机" 的最大值 ——
        //     若它一直很小，说明鼠标就在屏幕中心附近，"走向镜头"是几何巧合而非取错目标。
        var TGT = { mouse: 0, camera: 0, wasd: 0, maxTargetVsCam: 0, minTargetVsCam: 1e9 };

        // ------------------------------------------------------------------
        // camTrace(秒)：逐帧记录"覆写实际用到的坐标"，跑完打报告。
        // 目的：一次性分清三种可能 ——
        //   A. 走的是原版分支（branch 里带 camera）→ on/holding 没成立，参数不对
        //   B. 走鼠标分支但"鼠标世界坐标 ≈ 相机坐标" → 几何巧合（光标在屏幕中心附近）
        //   C. 走鼠标分支且两者差得远 → 目标逻辑没问题，问题在相机钳制或渲染
        // 不打逐帧日志（会淹掉日志文件），只在结束时打统计 + 首/末样本。
        // ------------------------------------------------------------------
        var TRC = { on: false, frames: 0, first: null, last: null, mouseEqCam: 0 };

        function traceSample(){
            if(!TRC.on) return;
            var s = "mouse=" + Math.round(TRC.mouseX) + "," + Math.round(TRC.mouseY)
                  + " cam=" + Math.round(TRC.camX) + "," + Math.round(TRC.camY)
                  + " unit=" + Math.round(TRC.unitX) + "," + Math.round(TRC.unitY)
                  + " branch=" + TRC.branch;
            TRC.frames++;
            if(!TRC.first) TRC.first = s;
            TRC.last = s;
            var dx = TRC.mouseX - TRC.camX, dy = TRC.mouseY - TRC.camY;
            if(Math.sqrt(dx * dx + dy * dy) < 24) TRC.mouseEqCam++;   // 3 格以内算"重合"
        }

        function camTrace(seconds){
            TRC = { on: true, frames: 0, first: null, last: null, mouseEqCam: 0 };
            var frames = Math.max(30, Math.round((seconds || 5) * 60));
            log("camTrace 开始：现在【按住右键拖动单位】约 " + (frames / 60).toFixed(1) + " 秒");
            var n = 0;
            var tick = function(){
                if(++n > frames){
                    TRC.on = false;
                    if(TRC.frames === 0){
                        log("camTrace 报告：一次样本都没采到 —— 说明整个窗口里 "
                            + "覆写都没进入自由视角分支（detach-camera 没开？）");
                    }else{
                        log("camTrace 报告：样本 " + TRC.frames + " 帧"
                            + " | 鼠标世界坐标与相机重合(＜3格) " + TRC.mouseEqCam + " 帧");
                        log("camTrace 首帧：" + (TRC.first || "-"));
                        log("camTrace 末帧：" + (TRC.last || "-"));
                    }
                    return;
                }
                try{ Timer.schedule(tick, 1); }catch(e){}
            };
            try{ Timer.schedule(tick, 1); }catch(e){ log("camTrace 排程失败：" + e); }
            return "tracing";
        }

        // 覆写里"是否接管单位移动" = **用户设置项**本身。
        //
        // ⚠ 曾经这里是个独立的模块级变量 cursorEnabled（默认 true），由 camCursor() 改写。
        //   于是它和用户设置**互不相干**：一旦（比如调试时）调过 camCursor(false)，
        //   它就会永久停在 false —— 此后无论在设置里怎么开，
        //   覆写都走"原版目标 = 相机/屏幕中心"这一支，
        //   现象就是"启用之后单位会走到镜头"。这与 holdCamera 漏查设置项是同一类错误。
        //   现在只用设置项，不再有第二份真相。
        function cursorOn(){
            return settingOn();
        }
        var cameraHoldEnabled = true;   // 打开"按住鼠标移动键时不让镜头被推向鼠标"（默认开）
        // 为什么可以默认开：holdCamera() 的判据收得很窄 —— 只在
        //   「自由视角开着」且「正按着鼠标移动键」的那些帧里才把相机写回上一帧坐标，
        // 其余时刻一个字节都不碰。上一版是"任何时候都在帧尾写相机"，
        // 那会与改端 MindustryX 的 update()（它自带 pollInputPlayer 等额外处理）
        // 全程抢相机，实测表现为抖动 —— 那是被否掉的做法。

        // 抖/不抖的 A/B 开关也要作用于 holdCamera()
        // （下面 holdCamera() 里会读它）

        // 覆写用的方法体：**整段复刻 DesktopInput.updateMovement**，只改自由视角那一支的目标
        var PANSTATS = { errLogged: false };   // 诊断：panCamera 出错只报一次
        function buildOverride(DesktopInput, Binding, Vec2, Mechc, Tmp, Time, Angles, Payloadc){
            var def = {};

            // ⚠⚠ 安全网：JavaAdapter 里抛出的任何 JS 异常都会直接冒到 Control.update → 崩游戏。
            //      所以整个方法体包一层 try/catch：出错只记一次日志，并退回原生 updateMovement，
            //      绝不让脚本错误崩掉游戏。
            var superBroken = false;

            function realUpdateMovement(self, unit){
                var omni = unit.type().omniMovement;
                var speed = unit.speed();
                var xa = Core.input.axis(Binding.moveX);
                var ya = Core.input.axis(Binding.moveY);
                var boosted = (Mechc != null && (unit instanceof Mechc)) && unit.isFlying();

                var Vars0 = Packages.mindustry.Vars;
                // 「学术端原味」开着 → 单位移动**退回原版分支**（③ 目标 = 相机/屏幕中心），
                // 但相机压制（holdCamera）不受影响 —— 那是由主开关单独管的。
                var on = cursorOn() && !legacyOn();

                if(settings.getBool("detach-camera")){
                    var holding = Core.input.keyDown(Binding.mouseMove);
                    OV.frames++;                            // 诊断：覆写实际生效帧数
                    OV.holding = holding;

                    // 三段式：每段只干一件事，互不干扰。
                    //   ① 本模组开着 → 目标是**鼠标世界坐标**
                    //   ② 本模组开着但松开移动键 → 停止驱动（原地，靠阻尼滑停）
                    //   ③ 本模组关着 → **逐字照抄原版**（目标是相机＝屏幕中心）
                    //
                    // ⚠ 早先写成"if(on && holding) 取鼠标 else 取相机"——把②和③塞进同一个
                    //   else，于是"开着但松手"时会去追相机，表现为"单位跟着镜头走"。
                    //   三段分开后，②永远不可能退回③，两者再也不会互相污染。
                    if(on){
                        if(holding){
                            // ① 目标是鼠标世界坐标（用私有向量，不借用 Tmp.v1，避免被别处改写）
                            var mw = Core.input.mouseWorld();
                            var tx = mw.x, ty = mw.y;
                            self.movement.set(tx, ty).sub(Vars0.player).limit(speed);

                            var tdx = tx - Vars0.player.x, tdy = ty - Vars0.player.y;
                            DBG.d = Math.sqrt(tdx * tdx + tdy * tdy);
                            DBG.n = (DBG.n || 0) + 1;      // 生效帧数（camWhere() 会回报）

                            TGT.mouse++;
                            var dxm = tx - Core.camera.position.x, dym = ty - Core.camera.position.y;
                            var dm = Math.sqrt(dxm * dxm + dym * dym);
                            if(dm > TGT.maxTargetVsCam) TGT.maxTargetVsCam = dm;
                            if(dm < TGT.minTargetVsCam) TGT.minTargetVsCam = dm;

                            TRC.mouseX = tx; TRC.mouseY = ty;
                            TRC.camX = Core.camera.position.x; TRC.camY = Core.camera.position.y;
                            TRC.unitX = Vars0.player.x; TRC.unitY = Vars0.player.y;
                            TRC.branch = "mouse";
                            traceSample();

                            // 到位判定用原版同一个阈值 15f，只是目标换了。
                            // 这里**只归零、不加刹车**：那句 approachDelta 是"急停"，
                            // 拿它处理"到位"会把滑行惯性吃光。
                            if(Vars0.player.within(tx, ty, 15.0)) self.movement.setZero();
                        }else if(xa !== 0 || ya !== 0){
                            // ② W/A/S/D → **直接移动单位**。
                            //   原版自由视角下 WASD 是"键盘平移"（挪相机），单位不响应；
                            //   这里改成与常规模式相同的写法来驱动单位，而相机由 holdCamera()
                            //   钉住 → 于是"上下左右直接控制单位，但不拉视角"。
                            TGT.wasd++;
                            self.movement.set(xa, ya).nor().scl(speed);
                        }else{
                            // ③ 既没按鼠标移动键、也没按 WASD → 停止驱动
                            //   （原版没有"松手"概念，会继续朝屏幕中心飞）
                            TGT.camera++;
                            self.movement.setZero();
                        }
                    }else{
                        // ④ 关掉开关：＝原版，一行不差
                        var cam = Core.camera.position;
                        self.movement.set(cam.x, cam.y).sub(Vars0.player).limit(speed);
                        if(Vars0.player.within(cam.x, cam.y, 15.0)){
                            self.movement.setZero();
                            unit.vel.approachDelta(Vec2.ZERO, unit.speed() * unit.type().accel / 2);
                        }
                    }
                }else{
                    self.movement.set(xa, ya).nor().scl(speed);
                    if(Core.input.keyDown(Binding.mouseMove)){
                        self.movement.add(Core.input.mouseWorld().sub(Vars0.player).scl(1 / 25 * speed)).limit(speed);
                    }
                }

                var mouseAngle = Angles.mouseAngle(unit.x, unit.y);
                var aimCursor = omni && Vars0.player.shooting && unit.type().hasWeapons() && unit.type().faceTarget && !boosted;

                if(aimCursor){
                    unit.lookAt(mouseAngle);
                }else{
                    unit.lookAt(unit.prefRotation());
                }

                unit.movePref(self.movement);
                unit.aim(Core.input.mouseWorld());
                unit.controlWeapons(true, Vars0.player.shooting && !boosted);

                Vars0.player.boosting = Core.input.keyDown(Binding.boost);
                //⚠ aimX / aimY 是**字段**（float），不是方法 —— 写成 unit.aimX() 会抛 TypeError 并崩游戏
                Vars0.player.mouseX = unit.aimX;
                Vars0.player.mouseY = unit.aimY;

                // payload 输入（照抄原版，否则搬运单位会失灵）
                if(Payloadc != null && (unit instanceof Payloadc)){
                    if(Core.input.keyTap(Binding.pickupCargo)){
                        self.tryPickupPayload();
                        self.lastPayloadKeyTapMillis = Time.millis();
                    }
                    if(Core.input.keyDown(Binding.pickupCargo)
                        && Time.timeSinceMillis(self.lastPayloadKeyHoldMillis) > 20
                        && Time.timeSinceMillis(self.lastPayloadKeyTapMillis) > 200){
                        self.tryPickupPayload();
                        self.lastPayloadKeyHoldMillis = Time.millis();
                    }
                    if(Core.input.keyTap(Binding.dropCargo)){
                        self.tryDropPayload();
                        self.lastPayloadKeyTapMillis = Time.millis();
                    }
                    if(Core.input.keyDown(Binding.dropCargo)
                        && Time.timeSinceMillis(self.lastPayloadKeyHoldMillis) > 20
                        && Time.timeSinceMillis(self.lastPayloadKeyTapMillis) > 200){
                        self.tryDropPayload();
                        self.lastPayloadKeyHoldMillis = Time.millis();
                    }
                }
            }

            // 对外的覆写入口：包一层 try/catch，出错只记一次日志并退回原生实现
            def.updateMovement = function(unit){
                if(superBroken) return;
                try{
                    realUpdateMovement(this, unit);
                }catch(e){
                    superBroken = true;
                    log("⚠ updateMovement 覆写出错，已停用覆写（游戏不会崩）：" + e);
                    try{ Vars.control.setInput(new Packages.mindustry.input.DesktopInput()); }catch(e2){}
                    try{ overrideInstalled = false; }catch(e3){}
                }
            };

            // ------------------------------------------------------------------
            // 覆写 panCamera(Vec2) —— 这是"玩家主动把视角挪到某处"的唯一入口。
            // 原版（DesktopInput.java:965-971）：
            //     public void panCamera(Vec2 position){
            //         if(!locked()){ panning = true; camera.position.set(position); }
            //     }
            // 调用者：全屏小地图 MinimapFragment.panTo()、角落小地图 Minimap 的右键点击、
            //         受伤核心提示 HudFragment、编辑器 MapProcessorsDialog。
            //
            // 我们照原版做（不改变行为），只是多**同步刷新一次相机矩阵** ——
            // 与 applyCameraHold() 保持一致，免得同一帧内解出错误的 mouseWorld。
            //
            // 注：不需要靠一个"标志位"来判断压制该不该让行。
            //     因为 panCamera 是"瞬移"（一次移动几百格），而压制要治的漂移是每帧 1-2 格；
            //     applyCameraHold() 直接用"位移是否超过阈值"来区分（见那里的 JUMP 判断）。
            //     这样也不依赖 ui.update() / scene.update() 与 Trigger.update 的先后顺序。
            // ------------------------------------------------------------------
            def.panCamera = function(position){
                // ⚠ 这里必须用 `this`，不能用 updateMovement 里的 `self`
                //   （那是在另一个函数里 `var self = this` 声明的，此处不可见）
                try{
                    if(!this.locked()){
                        this.panning = true;
                        Core.camera.position.set(position);
                        Core.camera.update();
                    }
                }catch(e){
                    if(!PANSTATS.errLogged){ PANSTATS.errLogged = true; log("⚠ panCamera 覆写出错（只报一次）：" + e); }
                }
            };

            return def;
        }

        // ------------------------------------------------------------------
        // 让原版"推不动镜头"：把 panSpeed / panBoostSpeed 在按住移动键期间临时置 0。
        //
        // 原版 DesktopInput.update() 第 294-297 行的位移是：
        //     camera.position.x += clamp((mouseX - W/2) * panScale, -1, 1) * camSpeed;
        //     camera.position.y += clamp((mouseY - H/2) * panScale, -1, 1) * camSpeed;
        // 而 camSpeed = (!boost ? panSpeed : panBoostSpeed) * Time.delta   （同文件第 239 行）
        // 所以把这两个速度置 0，那两句就变成"加 0" —— **原版自己什么都不写**。
        //
        // 对比被否掉的旧做法（帧尾把相机写回上一帧坐标）：那种做法让相机在
        // "漂移后的位置"和"上一帧位置"之间每帧来回摆，画面表现为**抖动**。
        // 置 0 速度没有这个问题：原版不写，相机自然一动不动。
        // ------------------------------------------------------------------
        var camSave = { x: 0, y: 0, ok: false };   // 上一帧末相机坐标（用于"拖拽开始时把镜头定住"）
        var panSpeedSaved = null;                  // { input, speed, boostSpeed }
        var panZeroed = false;

        function setPanSpeedZero(zero){
            try{
                var inp = Vars.control != null ? Vars.control.input : null;
                if(inp == null) return;
                if(zero){
                    if(!panZeroed){
                        if(panSpeedSaved == null || panSpeedSaved.input !== inp){
                            panSpeedSaved = { input: inp, speed: inp.panSpeed, boostSpeed: inp.panBoostSpeed };
                        }
                        inp.panSpeed = 0;
                        inp.panBoostSpeed = 0;
                        panZeroed = true;
                    }
                }else if(panZeroed){
                    if(panSpeedSaved != null && panSpeedSaved.input === inp){
                        inp.panSpeed = panSpeedSaved.speed;
                        inp.panBoostSpeed = panSpeedSaved.boostSpeed;
                    }
                    panZeroed = false;
                }
            }catch(e){}
        }

        // 按住移动键的那一段：把镜头钉在"开始拖拽前"的位置，并让原版推不动它
        //
        // 要同时治两个机制（两个都会让镜头漂）：
        //   ① 推镜：DesktopInput.update() 第 294-297 行，位移正比于 panSpeed
        //      → 把 panSpeed/panBoostSpeed 置 0，它就变成"加 0"；
        //   ② 吸回单位：同文件第 291 行 `camera.position.lerpDelta(panTarget, 0.08f)`
        //      → 每帧把相机写回锚点，于是 lerp 的起点就是终点，等于 no-op。
        //
        // ⚠ 与"事后还原"的关键区别：这里每帧都把相机写成**同一个值**（锚点），
        //   而不是在"漂移后的位置"和"上一帧位置"之间来回摆 ——
        //   所以渲染看到的位置逐帧恒定，不会抖。
        var pinned = false;
        var pinX = 0, pinY = 0;
        // 上一帧我们是否真的把相机写在了锚点上
        var camWasPinned = false;
        // 上一帧是否处于"接管"状态 —— 只用于"每次拖拽记一行诊断"
        var holdWasOn = false;

        // 游戏正在自己接管相机 —— 此时我们**绝不能**插手。
        //
        // ① 降落/发射动画（重生就是在核心降落）：
        //      Renderer.update(){ if(landTime > 0){ camerascale = launchAnimator.zoomLaunch(); ... } }
        //    而 CoreBlock.zoomLaunch() 里就是 `Core.camera.position.set(this)` —— **相机被锁在核心上**。
        //    Renderer.isCutscene() 恰好就是 `landTime > 0`，覆盖整个降落过程。
        // ② 没有有效单位（死亡到附身之间的空档，Player.dead() == unit == null || !isValid()）：
        //    这段镜头本来就该跟着核心/降落走。
        function gameControlsCamera(){
            try{
                if(Vars.renderer != null && Vars.renderer.isCutscene()) return true;
            }catch(e){}
            try{
                var u = Vars.player.unit();
                if(u == null || !u.isValid()) return true;
            }catch(e){}
            return false;
        }

        // 把锚点刷新成"此刻镜头所在的位置"
        function refreshPin(){
            try{
                pinX = Core.camera.position.x;
                pinY = Core.camera.position.y;
                return true;
            }catch(e){ return false; }
        }

        // 相机钳制：在 holdCamera() 为真的帧里，把相机钉在锚点上。
        //
        // ⚠ 锚点判定换过两版，都是被时序打败的：
        //   ① 「距离 > 32 格算瞬移」→ 错：降落若只挪了不到 32 格，就会沿用旧锚点，
        //      一钉把镜头拉回去。现象正是"一会儿弹一会儿不弹"。
        //   ② 「不接管 → 接管的状态边沿」→ 也错：点小地图时，panCamera 先把
        //      panning 置 true（我们让行），而按住移动键又让原版在同一帧把它改回 false，
        //      于是边沿被吃掉，锚点停在点击之前的位置。
        //
        //   最终用的是一条**不变量**，与阈值无关、与调用顺序无关：
        //     只有当相机"确实还停在我们上次钉住的位置上"时，才把它钉回锚点；
        //     一旦发现它已被别人挪走（小地图 / 降落 / 任何来源），就以**新位置为锚**。
        //   于是"我们从不把相机往回转"，也就永远不会把它拽回旧位置。
        // ------------------------------------------------------------------
        // 还原安全网：只要本模组**不再接管**（设置关了 / 没在按移动键），
        //   panSpeed / panBoostSpeed 就必须立刻回到原值。
        //
        // 为什么单列一条：置零 panSpeed 是本模组唯一"改动游戏对象字段"的操作，
        //   一旦因异常路径没还原，原版的推镜速度会永久变成 0 —— 那正是"关闭后
        //   不恢复原版"的一类症状。放在 Trigger 回调最外层（不受 applyCameraHold
        //   内部提前 return / 异常影响），确保总能执行。
        // ------------------------------------------------------------------
        function restorePanSpeedIfIdle(){
            try{
                if(panZeroed && !holdCamera()) setPanSpeedZero(false);
            }catch(e){}
        }

        function applyCameraHold(){
            // ① 「死前视野」的一次性恢复**不在这里** —— 它搬去了 apply() 里
            //    `if(!on || !freeCam) return;` 之后、`isCutscene()` return **之前**。
            //    原因：降落动画期间 apply() 会因 isCutscene() 提前 return，
            //    函数根本进不来，shouldRestoreDeathView() 里"记录见过过场"那一步
            //    （snapSawCut）永远执行不到，恢复只能靠 600 帧超时兜底 ——
            //    表现为"重生后镜头不回死前视野"。详见 apply() 里的注释。

            // ② 恢复之后的宽限：这一段里即使玩家什么都没按，也继续把相机钉在
            //    死前视野上。理由见 restoreHold 的声明处（否则恢复的下一帧就被
            //    原版 AutoFollow 拽回重生点了）。宽限期内玩家一按平移键就立刻让位。
            //
            // ⚠ 平移键这条让位判据**不能**带 `&& !unitMoveInputHeld()`（跟 holdCamera()
            //   里那条不一样）：这里是"恢复了死前视野之后"的短暂维持，玩家一按中键
            //   就是想自己看，必须马上交回 —— 否则重生后 0.5 秒内中键平移完全无效。
            if(restoreHold > 0){
                var held = false;
                if(uiBusy() || Vars.player == null || Vars.player.dead()
                   || !settings.getBool("detach-camera", false)
                   || coreInputKeyDown(Packages.mindustry.input.Binding.pan)){
                    restoreHold = 0;            // 条件没了 → 结束宽限，走正常路径
                }else{
                    restoreHold--;
                    held = true;
                }
                if(held){
                    var ch = null;
                    try{ ch = Core.camera.position; }catch(e){ ch = null; }
                    if(ch != null){
                        try{
                            if(Math.abs(ch.x - pinX) > 0.001 || Math.abs(ch.y - pinY) > 0.001){
                                ch.set(pinX, pinY);
                                Core.camera.update();
                            }
                        }catch(e){}
                    }
                    pinned = true;
                    camWasPinned = true;
                    setPanSpeedZero(true);
                    return;
                }
            }

            if(!holdCamera()){
                setPanSpeedZero(false);
                pinned = false;
                camWasPinned = false;
                holdWasOn = false;      // 松开后允许下一次拖拽再记一行诊断
                return;
            }
            var c = null;
            try{ c = Core.camera.position; }catch(e){ return; }

            // ③ 相机还在我们上次钉住的位置吗？（容差 1 格；原版每帧漂移远小于此）
            var movedAway = true;
            if(camWasPinned){
                var dxp = c.x - pinX, dyp = c.y - pinY;
                movedAway = Math.sqrt(dxp * dxp + dyp * dyp) > 1;
            }

            if(movedAway){
                if(!refreshPin()){
                    return;                        // 被别人挪走了（或这是头一帧）→ 认新位置为锚
                }
                pinned = true;
            }
            // 钉回锚点（写的是同一个值，所以位置恒定、不抖）
            try{
                if(Math.abs(c.x - pinX) > 0.001 || Math.abs(c.y - pinY) > 0.001){
                    c.set(pinX, pinY);
                    Core.camera.update();
                }
            }catch(e){}
            camWasPinned = true;
            setPanSpeedZero(true);

            // —— 自动诊断：每次"按住移动键"的第一帧，把关键状态写一行进日志 ——
            // 不用你敲任何命令；正常玩，日志里就有据可查。
            if(!holdWasOn){
                holdWasOn = true;
                logDragStart();
            }
        }

        // 每次开始拖拽时记录一次现场（只记一行，不会刷屏）
        var dragLogged = 0;
        function logDragStart(){
            try{
                var B = Packages.mindustry.input.Binding;
                var u = Vars.player.unit();
                var mw = Core.input.mouseWorld();
                var cam = Core.camera.position;
                var mx = mw.x, my = mw.y;
                var dxm = mx - cam.x, dym = my - cam.y;
                var dm = Math.sqrt(dxm * dxm + dym * dym);          // 鼠标世界坐标 离 相机
                var dxu = mx - Vars.player.x, dyu = my - Vars.player.y;
                var du = Math.sqrt(dxu * dxu + dyu * dyu);          // 鼠标 离 单位
                var dxc = cam.x - Vars.player.x, dyc = cam.y - Vars.player.y;
                var dc = Math.sqrt(dxc * dxc + dyc * dyc);          // 相机 离 单位
                dragLogged++;
                log("拖拽#" + dragLogged + " 设置=" + settingOn()
                    + " 移动键=" + String(B.mouseMove.value.key) + (Core.input.keyDown(B.mouseMove) ? "(按下)" : "(未按下)")
                    + " 鼠标世界=" + Math.round(mx) + "," + Math.round(my)
                    + " 相机=" + Math.round(cam.x) + "," + Math.round(cam.y)
                    + " 单位=" + Math.round(Vars.player.x) + "," + Math.round(Vars.player.y));
                log("   → 单位到鼠标 " + Math.round(du) + " 格｜单位到相机 " + Math.round(dc)
                    + " 格｜鼠标到相机 " + Math.round(dm) + " 格"
                    + (dm < 60 ? "  ⚠ 鼠标就在屏幕中心附近：此时'走向鼠标'与'走向屏幕中心'几乎同向" : ""));
                traceDrag(mx, my, cam.x, cam.y, Vars.player.x, Vars.player.y, du, dc);
            }catch(e){ log("拖拽诊断失败：" + e); }
        }

        // ------------------------------------------------------------------
        // 轨迹测量：拖拽开始时记下"鼠标/相机/单位"三个坐标，1 秒后再记一次，
        // 直接回答"单位到底朝谁走了"：看它离谁变近了。
        //   若 "到鼠标" 大幅减小、"到相机" 增大  → 单位追的是鼠标（本模组语义）
        //   若 "到相机" 减小、"到鼠标" 不变      → 单位追的是镜头 ← 那才是真 bug
        // ------------------------------------------------------------------
        function traceDrag(mx0, my0, cx0, cy0, ux0, uy0, du0, dc0){
            var n = 0;
            var tick = function(){
                if(++n < 30){ try{ Timer.schedule(tick, 1); }catch(e){} return; }
                try{
                    var px = Vars.player.x, py = Vars.player.y;
                    var cam = Core.camera.position;
                    var dxu = mx0 - px, dyu = my0 - py;
                    var du1 = Math.sqrt(dxu * dxu + dyu * dyu);          // 到"拖拽开始时的鼠标世界坐标"
                    var dxc = cam.x - px, dyc = cam.y - py;
                    var dc1 = Math.sqrt(dxc * dxc + dyc * dyc);          // 到"当前相机位置"
                    var moved = Math.sqrt((px - ux0) * (px - ux0) + (py - uy0) * (py - uy0));
                    var toward = (du1 < du0 - 1) ? "朝鼠标 ✓" : "没朝鼠标";
                    if(dc1 < dc0 - 1 && du1 >= du0 - 1) toward = "朝相机 ✗（真 bug）";
                    log("轨迹#" + dragLogged + "（1 秒后）单位移动了 " + Math.round(moved)
                        + " 格｜到鼠标 " + Math.round(du0) + "→" + Math.round(du1)
                        + "｜到相机 " + Math.round(dc0) + "→" + Math.round(dc1)
                        + "｜判定：" + toward);
                }catch(e){}
            };
            try{ Timer.schedule(tick, 1); }catch(e){}
        }

        function saveCameraNow(){
            try{
                camSave.x = Core.camera.position.x;
                camSave.y = Core.camera.position.y;
                camSave.ok = true;
            }catch(e){ camSave.ok = false; }
        }

        // 本帧该不该"按住相机"（撤销这一次 update() 对相机的写入）
        //
        // ⚠ 这里刻意**收得很窄**，只治一个具体的冲突：
        //   原版 DesktopInput.update() 里 ——
        //       278: if(input.keyDown(Binding.mouseMove)) panCam = true;      // 按住"鼠标移动"键
        //       294: if(panCam){ camera.position += clamp((mouseX - W/2)*panScale, -1, 1)*camSpeed; }
        //   也就是"鼠标移动"这个键**同时**被用来移动单位**和**把镜头推向鼠标。
        //   所以我们只在"确实按着鼠标移动键、且处在自由视角"的那些帧里把相机按住，
        //   其余任何时刻一概不碰相机 —— 这样既不会像上一版那样跟改端 MindustryX 的
        //   update() 全程抢相机（那会抖），也不会让 followcamera 把镜头拉走。
        function holdCamera(){
            // ⚠ 必须**同时**看用户设置项与本模块的覆盖开关。
            //   曾经只写了 cameraHoldEnabled（那是 camHold() 用的覆盖位，默认 true），
            //   结果用户在界面里/F10 关掉设置后，相机钳制照旧生效 ——
            //   表现为"关了也不恢复原版跟随"。
            if(!settingOn()) return false;
            if(!cameraHoldEnabled) return false;
            try{
                if(wasBusy) return false;
                if(Vars.player == null || Vars.player.dead()) return false;
                if(!settings.getBool("detach-camera", false)) return false;   // 只在自由视角下
                // ⚠ 游戏自己在放降落/发射动画、或还没有有效单位时 → 一律不插手
                //   （重生就是在核心降落，这时相机被 CoreBlock.zoomLaunch() 锁在核心上）
                if(gameControlsCamera()) return false;
                var inp = Vars.control != null ? Vars.control.input : null;
                // NOTE: spectating is a boolean field (false in normal play, true only
                // in spectator mode). The old `!= null` test was true for BOTH, so this
                // gate returned false on every frame and the pin never engaged.
                if(inp != null && inp.spectating) return false;
                if(inp != null && inp.locked()) return false;
                // ⚠ 玩家在**主动操作相机**时一律放手（否则会把玩家的操作覆盖掉）：
                //   · 平移键（默认 mouseForward，你绑的中键）→ 原版推镜照常。
                //     这样"中键 + 右键同时按住"就同时具备两种效果：
                //       平移键 → 镜头推向鼠标；移动键 → 单位走到鼠标。
                //   · W/A/S/D → 见下面 unitMoveInputHeld()：自由视角下我们用覆写把它
                //     变成"直接移动单位"，所以**不再**当作"玩家要动视角"而放手。
                //   · 本帧调用过 panCamera()（点小地图 / 核心提示 / 编辑器跳转）→ 那是明确的相机指令。
                //
                // ⚠⚠ `&& !unitMoveInputHeld()` 是用户实测报的"未生效"的根因所在：
                //   现场键位是**平移=中键、移动单位=右键、两个键一起按**（不用 WASD）。
                //   原先这里是无条件 `return false`，于是 pan 恒为真 → 压制永远不生效 →
                //   镜头照旧被原版 panCam 推向鼠标（现场日志：相机 1360 → 1504 → 1580
                //   跟着鼠标漂，"单位到鼠标"的格数 446/517/518 一直不收敛）。
                //   加上"没在移动单位"之后：两个键一起按时 pan 的推镜被下一帧钉回，
                //   视觉上镜头不动；**只**按平移键时原版推镜照常。
                if(coreInputKeyDown(Packages.mindustry.input.Binding.pan) && !unitMoveInputHeld()) return false;
                // ⚠ 只要玩家在用键鼠移动单位（鼠标移动键 或 W/A/S/D），就把镜头钉住 ——
                //   全新语义："上下左右直接控制单位，但不拉视角"。
                return unitMoveInputHeld();
            }catch(e){ return false; }
        }

        function coreInputKeyDown(bind){
            try{ return Core.input.keyDown(bind); }catch(e){ return false; }
        }

        // 玩家是否正在用键鼠移动单位：鼠标移动键 或 W/A/S/D
        //
        // ⚠ v5.6：「学术端原味」模式下 **W/A/S/D 不算"在移动单位"**。
        //   原因是那个模式把单位移动交回原版（目标 = 屏幕中心），
        //   此时 WASD 在原版里是「平移相机」。如果仍把它算成"在移动单位"，
        //   holdCamera() 就会把相机钉住 → WASD 推不动镜头 → 玩家没法调视角，
        //   整个模式就废了（这正是"判据要和模式对齐"的老坑）。
        function unitMoveInputHeld(){
            if(mouseMoveHeld()) return true;
            if(legacyOn()) return false;          // 学术端原味：WASD 归相机
            return wasdHeld();
        }

        // 是否按着 W/A/S/D（原版自由视角下用它做**键盘平移**；我们改成"直接移动单位"）
        function wasdHeld(){
            try{
                var B = Packages.mindustry.input.Binding;
                return Math.abs(Core.input.axis(B.moveX)) > 0 || Math.abs(Core.input.axis(B.moveY)) > 0;
            }catch(e){ return false; }
        }

        // 是否正按着"鼠标移动"键（= 正在用鼠标移动单位，同时原版会推镜）
        function mouseMoveHeld(){
            try{ return Core.input.keyDown(Packages.mindustry.input.Binding.mouseMove); }catch(e){ return false; }
        }

        // 启动自检：本模组是否 hidden？这决定进别人服务器会不会被当成"多余 mod"。
        //   hidden = true  → 不会出现在上报给服务器的 mod 列表里 → 不会被 mod 校验踢
        //   hidden = false → 会被上报，服务端若没有同名 mod 就会踢你（"Unnecessary mods"）
        // 判定依据（游戏源码）：
        //   Mods.getModStrings() 只收 `!meta.hidden && enabled()` 的 mod（Mods.java:940）
        //   客户端在 NetClient.java:108 把它发给服务端
        //   服务端在 NetServer.java:210-224 校验，extraMods 非空即踢
        function checkHidden(){
            try{
                var mods0 = Vars.mods;
                var me = null;
                var seq = mods0.getMods();
                for(var i = 0; i < seq.size; i++){
                    var m = seq.get(i);
                    if(m != null && String(m.name).toLowerCase().indexOf("camera-unbind") >= 0){ me = m; break; }
                }
                if(me == null){ log("hidden 自检：找不到自己的 mod 记录"); return; }
                var hid = me.meta != null && me.meta.hidden;
                // 再看"上报给服务器的名单"里到底有没有自己（这才是决定会不会被踢的东西）
                var reported = [];
                var all = mods0.getModStrings();
                if(all != null){
                    var n = (all.size != null) ? all.size : (typeof all.size === 'function' ? all.size() : 0);
                    for(var j = 0; j < n; j++){
                        var s = String(all.get(j));
                        if(s.toLowerCase().indexOf("camera-unbind") >= 0) reported.push(s);
                    }
                }
                log("hidden 自检：" + (hid ? "hidden=true ✓ 不会因 mod 清单被服务器踢" : "hidden=false ✗ 进服可能被当成多余 mod")
                    + "（服务器校验名单里出现 " + reported.length + " 次"
                    + (reported.length ? "：" + reported.join(",") : "，即不上报") + "）");
            }catch(e){ log("hidden 自检失败：" + e); }
        }

        // 安装覆写：换掉输入处理器
        function installOverride(){
            var DesktopInput = null;
            try{ DesktopInput = Packages.mindustry.input.DesktopInput; }catch(e){}
            if(DesktopInput == null){ log("找不到 DesktopInput 类"); return false; }

            // 如果游戏已经带了源码改动（有 freecam-cursor-move 这个开关），就不必再覆写
            try{
                if(settings.has("freecam-cursor-move")){
                    log("检测到游戏自带 freecam-cursor-move 开关（源码已改），跳过覆写");
                    return false;
                }
            }catch(e){}

            var input = null;
            try{ input = Vars.control != null ? Vars.control.input : null; }catch(e){}
            if(input == null){ log("拿不到当前 input"); return false; }
            if(!(input instanceof DesktopInput)){ log("当前输入处理器不是 DesktopInput（可能是移动端），跳过"); return false; }

            var d = null;
            try{
                d = buildOverride(
                    DesktopInput,
                    Packages.mindustry.input.Binding,
                    Packages.arc.math.geom.Vec2,
                    Packages.mindustry.gen.Mechc,
                    Packages.arc.util.Tmp,
                    Packages.arc.util.Time,
                    Packages.arc.math.Angles,
                    Packages.mindustry.gen.Payloadc
                );
            }catch(e){ log("准备覆写方法失败：" + e); return false; }

            var adapter = null;
            try{
                adapter = new JavaAdapter(DesktopInput, d);
            }catch(e1){
                log("JavaAdapter(DesktopInput, ...) 失败：" + e1);
                try{
                    adapter = JavaAdapter.apply(null, [DesktopInput, d]);
                }catch(e2){
                    log("JavaAdapter.apply 也失败：" + e2 + " → 覆写不可用，回退到每帧改 movement");
                    return false;
                }
            }
            if(adapter == null){ log("JavaAdapter 生成的对象为空"); return false; }

            try{
                Vars.control.setInput(adapter);
                log("输入处理器已替换为子类（updateMovement 覆写生效）"
                    + " [是本人=" + (Vars.control.input === adapter)
                    + " updateMovement=" + (typeof Vars.control.input.updateMovement) + "]");
                return true;
            }catch(e3){
                log("setInput 失败：" + e3);
                return false;
            }
        }

        var overrideInstalled = false;

        // 回退：换回原生 DesktopInput
        function uninstallOverride(){
            try{
                Vars.control.setInput(new Packages.mindustry.input.DesktopInput());
                overrideInstalled = false;
                log("已换回原生 DesktopInput");
                return true;
            }catch(e){ log("回退失败：" + e); return false; }
        }


        // ------------------------- 每帧主逻辑 -------------------------
        // 相机由 applyCameraHold() 单独处理；这里只管开关、热键、死亡跟随这些状态。
        function apply(){
            try{
                if(!Vars.state.isGame() || Vars.state.isEditor()) return;
                if(Vars.player == null) return;

                var cam = Core.camera.position;
                if(isNaN(cam.x) || isNaN(cam.y)) return;

                // 界面占用键盘（对话框 / 聊天 / 控制台 / 输入框）时：
                //   · 不抢镜头 —— 原版这段时间也不自己动相机（DesktopInput.update() 有
                //     !scene.hasDialog() / !scene.hasField() 的同款判断），所以两边都不动才是对的；
                //   · 不响应热键 —— 免得打字时误触发。
                var busy = uiBusy();
                if(busy){
                    wasBusy = true;
                    camSave.ok = false;      // 界面期间不记录，免得关闭后把镜头拽回打开前
                    return;
                }
                if(wasBusy){
                    wasBusy = false;
                    camSave.ok = false;
                }

                var on = settingOn();

                // V：开关本功能（关着的时候也要能按开）
                try{
                    if(KEY_ON != null && Core.input.keyTap(KEY_ON)){
                        on = !on;
                        setSetting(on);
                        notify("[" + label() + "] " + (on ? "已开启：视角不再跟随单位" : "已关闭：恢复原版跟随"));
                    }
                }catch(e){}
                // N：立刻把视角拉回单位 / 核心（只在开启状态下有意义）
                try{
                    if(KEY_BACK != null && Core.input.keyTap(KEY_BACK) && on) recenter();
                }catch(e){}
                // F9：切换「学术端原味」（v5.6）。它只在主开关开着时才有意义，所以不做 gating，
                //     先让玩家能随时切，下次开主开关时直接生效。
                try{
                    if(KEY_LEG != null && Core.input.keyTap(KEY_LEG)){
                        var lg = !legacyOn();
                        setLegacy(lg);
                        notify("[camera-unbind] 学术端原味 " + (lg
                            ? "已开启：单位朝屏幕中心走（WASD 平移镜头），镜头仍不乱动"
                            : "已关闭：单位走到鼠标位置"));
                    }
                }catch(e){}

                // 本模组作用的前提是**自由视角（设置 → 图像 → 自由视角）开着**。
                // 自由视角关着时我们**一点也别碰**，原版什么样就什么样。
                var freeCam = false;
                try{ freeCam = settings.getBool("detach-camera", false); }catch(e){}
                if(!on || !freeCam) return;

                // ⚠⚠ 「死前视野」的一步在这里做 —— **不能**放在 applyCameraHold() 里！
                //   因为下面马上就有"过场期间直接 return"，而**降落动画期间正需要
                //   记录"见过过场"这个事实**（见 shouldRestoreDeathView）：
                //   放在 applyCameraHold() 里就永远等不到那次调用，snapSawCut 永远是
                //   false，恢复只能靠 600 帧超时兜底 —— 表现就是"重生后镜头不回死前
                //   视野"，而且这个 bug 会被"在外面顺手调一次 shouldRestore"的探针
                //   意外掩盖（踩过：加探针 95/0，去掉探针 92/3，连查三次才定位）。
                //   放在这里：过场/非过场两帧都会走到，一次性动作与"要不要按住相机"解耦。
                // ⚠ 顺序要紧：先记录"见过降落动画"（死亡期间也要走），再尝试恢复。
                recordDeathViewCut();
                restoreDeathView();

                // 单位移动已改为"方法级覆写"（见 installOverride），这里不需要每帧抢 movement。
                // 相机部分仍然保留：只在"游戏确实要把镜头吸回单位"的静止帧里抵消一次。

                // 逻辑剪影 / 演出期间不抢镜头（相机那两个还原点在函数开头已经判过了）
                try{
                    if(Vars.renderer != null && Vars.renderer.isCutscene()) return;
                }catch(e){}

                var unit = null;
                try{ unit = Vars.player.unit(); }catch(e){}
                var uid  = unit != null ? unit.id : 0;
                var dead = false;
                try{ dead = Vars.player.dead(); }catch(e){}

                // 死亡 / 换单位时把相机放过去。
                // ⚠ 只在**本功能开着**时才做：关掉后应当与原版完全一致，
                //   不能有任何由本模组引起的相机写入。
                var changed = (uid != lastUnitId) || (dead != lastDead);
                // ⚠⚠ 赋值必须**晚于**死亡转变的判定：`lastDead` 一旦提前被写成当前值，
                //   `!lastDead` 就永远为假，快照永远记不下来（踩过：日志里 A7 明明
                //   打印 `dead=true lastDead=false changed=true`，却一条 [SNAP] 都没有）。
                var wasDead = lastDead;
                lastUnitId = uid;
                lastDead = dead;
                if(on && changed){
                    // ⚠ 顺序要紧：先记快照，再 cameraTo() —— cameraTo 会把相机
                    //   放到核心，记在后面就记成核心坐标了。
                    //
                    // ⚠ 快照的**消费**放在 applyCameraHold() 里，这里绝不主动清掉它。
                    //   踩过的坑：曾经在这里写 `else deathSnap = null`（"活着 = 作废"），
                    //   但 holdCamera() 要求"有有效单位"才为真，也就是**只有活着的那一帧
                    //   才可能恢复** —— 而那一帧 apply() 已经先把快照清掉了，于是恢复
                    //   永远不执行、镜头停在核心。日志证据：先 `PROBE2 hold=false snap=yes
                    //   dead=false`，紧接着就是 `snap=none` 且从未出现 shouldRestore 的探针。
                    //
                    // ⚠ 必须限定在"活着 → 死"的**那一次转变**（!wasDead），不能只看 dead。
                    //   `changed` 是 (uid 变了 || dead 变了) 的或，而**换单位**也会让 uid 变。
                    //   曾经写成 `if(dead) snapDeathView()`，于是"已经是死的、又换了一次
                    //   单位引用"的帧会**再记一次**快照，而且记到的是已经放手之后、相机
                    //   被挪向核心那一路上的位置。夹具实证：
                    //     [D7] uid=0 dead=true lastDead=true lastUnitId=0 changed=true cam=2000
                    //   → 记下 (2000,2000)，随后在**完全不相干**的用例 [7] 里被恢复，
                    //     把相机从 (1000,1000) 拽到 (2000,2000)，连带 3 条断言失败
                    //     （movement 归零 / 相机矩阵一致 / 抵消吸回单位）。
                    if(dead && !wasDead) snapDeathView();
                }
                if(on && changed && dead) cameraTo(target());
            }catch(e){
                if(!apply._logged){ apply._logged = true; log("每帧逻辑出错（只报一次）：" + e); }
            }
        }

        // ---------------------------- 注册 ----------------------------
        // 帧内顺序（关键）：Control.update(){ input.update(); logic.update(); }
        //   → DesktopInput 在 input.update() 里改相机，而 Trigger.update 在
        //     logic.update() 里 fire，也就是下面这个回调跑在同一帧的"最后"。
        //
        //   ⚠ 但**不要**在这里"把相机写回上一帧的坐标" —— 那会让相机在两个值之间
        //     每帧来回摆，画面表现为**抖动**（试过，被否掉）。
        //     正确做法是 applyCameraHold()：置零 panSpeed + 钉住固定锚点，
        //     每帧写同一个值，所以位置恒定。
        //
        //   ⚠ 顺序很重要：applyCameraHold() 必须排在**原版写完相机之后**（也就是本帧的
        //     倒数第二步）。否则"进入接管那一帧"记下的锚点是**上一帧的位置**，
        //     原版紧接着一 lerp 就把它顶偏 —— 表现为接管瞬间镜头被拉一下。
        try{
            Events.run(ET.Trigger.update, function(){
                try{
                    apply();                 // ① 状态逻辑：开关、热键、死亡跟随等
                    saveCameraNow();         // ② 记下"本帧原版写完相机之后"的位置
                    applyCameraHold();       // ③ 相机钳制：需要时把相机钉在这个位置上
                    driftSample();           // ④ 抖动诊断采样（camDrift() 开启时才有数据）
                }finally{
                    // ⑤ 兜底：上面任何一步出错，也必须保证"不再接管时 panSpeed 已还原"，
                    //    否则原版推镜速度会永久变成 0（＝关闭后不恢复原版）。
                    restorePanSpeedIfIdle();
                }
            });
            log("Trigger.update 已挂上（帧尾钉锚点 + 置零 panSpeed，不做事后还原）");
        }catch(e){ log("挂 Trigger.update 失败：" + e); }

        // 换图 / 重开
        try{
            Events.on(ET.WorldLoadEvent, function(){
                // 把"当前是谁"重置，免得拿上一张图的单位 id 做比较。
                // 相机一概不动（原版自由视角自己会摆好）。
                lastUnitId = 0;
                lastDead = false;
                deathSnap = null;      // 换图了，旧图的"死前视野"没有意义
                snapSawCut = false;    // 连同"见过降落动画"的记录一起清掉，
                snapFrames = 0;        //   否则新图第一次死亡会直接跳过"等降落"那一步
                restoreHold = 0;       // 上一张图残留的宽限期不能让新图开局就钉住相机
                log("世界已加载（不碰相机，视角交给原版）");
            });
        }catch(e){ log("挂 WorldLoadEvent 失败：" + e); }

        try{
            Events.on(ET.ResetEvent, function(){
                lastUnitId = 0;
                lastDead = false;
                deathSnap = null;
                snapSawCut = false;
                snapFrames = 0;
                restoreHold = 0;
            });
        }catch(e){}

        // 客户端加载完成 → 注入设置页（失败就隔几帧重试；设置对话框早就构造好了，
        // 正常情况下一次就成功）
        function tryInject(tries){
            if(injectSetting()) return;
            if(tries > 0){
                try{ Timer.schedule(function(){ tryInject(tries - 1); }, 3); }
                catch(e){ log("Timer.schedule 不可用，放弃重试：" + e); }
            }
        }

        try{
            Events.on(ET.ClientLoadEvent, function(){
                log("客户端已加载：" + Core.bundle.get("mod.name", "Mindustry")
                    + " / 语言=" + Core.bundle.getLocale());
                tryInject(6);
                // 自检：让游戏自己报告本模组是否 hidden（决定进服务器会不会被当成"多余 mod"）
                checkHidden();
                // 关键：把输入处理器换成 DesktopInput 的子类（覆写 updateMovement）。
                // 放在 ClientLoadEvent 里，因为 Control.setInput 需要输入处理器已经注册过。
                try{
                    overrideInstalled = installOverride();
                    log("覆写状态：installed=" + overrideInstalled
                        + "，开关=" + settingOn() + "，自由视角=" + settings.getBool("detach-camera", false));
                }catch(e){ log("安装覆写异常：" + e); }
            });
        }catch(e){ log("挂 ClientLoadEvent 失败：" + e); }

        // ---------------- 脚本控制台接口（单机按 Enter 打开）----------------
        // 控制台与模组脚本共享同一个 Rhino 作用域，所以挂**顶层全局函数**即可。
        //
        // ⚠ 为什么不挂 `cam` 对象：实测两次踩坑 —— `cam.measure` / `cam.drift`
        //   在控制台里都是 `Cannot call property ... it is undefined`（同一批挂上去的
        //   `cam.version` 却正常）。对象属性解析不可靠，全局名一直很稳。
        //   所以只用全局函数，不再维护一份对象副本（那是纯冗余）。
        try{
            var scope = Vars.mods.getScripts().scope;
            var globals = {
                camVersion:  function(){ return MOD_VERSION; },
                camWhere:    function(){ return describe(); },
                camMeasure:  measure,          // 实测"单位到底往哪走了"
                camDrift:    driftReport,      // 抖动诊断（帧间位移统计）
                camHelp:     function(){
                    return "camVersion() 版本 | camWhere() 状态 | camMeasure(秒) 实测 | camDrift(秒) 抖动诊断 | "
                         + "camHold(true|false) 相机压制开关 | camCursor(true|false) 单位移动模式 | "
                         + "camLegacy(true|false) 学术端原味（单位朝屏幕中心走） | "
                         + "camOverride(true|false) 覆写开关";
                },
                camHold: function(on){
                    if(on === undefined) return cameraHoldEnabled ? "hold" : "free";
                    cameraHoldEnabled = !!on;
                    log("相机压制 → " + (cameraHoldEnabled ? "按住移动键时镜头不动" : "放手（交回原版）"));
                    return cameraHoldEnabled ? "hold" : "free";
                },
                // camClearHold()：立刻结束「死前视野」恢复后的 30 帧宽限期。
                // 给逻辑夹具用 —— 宽限期会跨用例残留（表现为"相机怎么按都不动"）。
                camClearHold: function(){ restoreHold = 0; return restoreHold; },
                // camCursor(true|false)：等价于直接改**用户设置项**。
                // 不再维护第二份状态 —— 见 cursorOn() 上面的说明。
                camCursor: function(on){
                    if(on === undefined) return settingOn() ? "on" : "off";
                    setSetting(!!on);
                    log("单位移动 → " + (settingOn() ? "走到鼠标位置" : "原生（朝屏幕中心）")
                        + "（已写入设置项 dp-camera-unbind=" + settingOn() + "）");
                    return settingOn() ? "on" : "off";
                },
                // camLegacy(true|false)：学术端原味（v5.6）。
                //   和 camCursor 的区别：camCursor 改的是**主开关**（整模组关掉），
                //   而 legacy 只改"单位移动目标"，**相机压制照旧生效**。
                camLegacy: function(on){
                    if(on === undefined) return legacyOn() ? "legacy" : "cursor";
                    setLegacy(!!on);
                    log("单位移动目标 → " + (legacyOn() ? "相机/屏幕中心（学术端原味）" : "鼠标位置")
                        + "（已写入设置项 " + LEGACY_KEY + "=" + legacyOn() + "）");
                    return legacyOn() ? "legacy" : "cursor";
                },
                camOverride: function(on){
                    if(on === undefined) return overrideInstalled ? "installed" : "not installed";
                    if(on){ overrideInstalled = installOverride(); return overrideInstalled ? "installed" : "failed"; }
                    return uninstallOverride() ? "removed" : "failed";
                }
            };
            for(var gname in globals){
                try{ Packages.rhino.ScriptableObject.putProperty(scope, gname, globals[gname]); }
                catch(e3){ log("挂全局 " + gname + " 失败：" + e3); }
            }

            // 自检：读回来确认真的挂上了（而不是相信"应该挂上了"）
            try{
                var bkVer   = Packages.rhino.ScriptableObject.getProperty(scope, "camVersion");
                var bkDrift = Packages.rhino.ScriptableObject.getProperty(scope, "camDrift");
                var okd = (typeof bkVer === "function") && (bkVer() == MOD_VERSION) && (typeof bkDrift === "function");
                log("控制台接口自检：" + (okd ? "OK" : "读回来不对劲")
                    + "（camVersion()=" + (typeof bkVer === "function" ? bkVer() : "?")
                    + " / camDrift=" + (typeof bkDrift) + "）");
            }catch(e2){ log("控制台接口自检失败：" + e2); }
        }catch(e){ log("发布控制台接口失败（不影响功能）：" + e); }

        // 诊断"镜头抖动"：在帧尾采样相机坐标，统计逐帧位移。
        //   delta = 本帧末与上帧末的位移（玩家看到的"抖动"就是这个）
        //   按住移动键期间 delta 应当 ≈ 0（镜头钉住），松开后随原版走。
        var driftBuf = null;
        function driftSample(){
            if(driftBuf == null) return;
            try{
                var c = Core.camera.position;
                if(driftBuf.lastX != null){
                    var dx = c.x - driftBuf.lastX, dy = c.y - driftBuf.lastY;
                    var d = Math.sqrt(dx*dx + dy*dy);
                    if(d > driftBuf.maxDelta) driftBuf.maxDelta = d;
                    driftBuf.sum += d;
                    driftBuf.n++;
                }
                driftBuf.lastX = c.x; driftBuf.lastY = c.y;
                try{ if(mouseMoveHeld()) driftBuf.held++; }catch(e){}
                if(driftBuf.n >= driftBuf.frames){
                    log("drift 报告：样本 " + driftBuf.n + " 帧 | 帧间位移 最大 " + driftBuf.maxDelta.toFixed(4)
                        + " 平均 " + (driftBuf.sum / Math.max(1, driftBuf.n)).toFixed(4)
                        + " | 按着移动键的帧数 " + driftBuf.held
                        + " | 压制=" + (cameraHoldEnabled ? "on" : "off"));
                    // 目标选择统计 —— 判断"单位走向镜头"到底是取错目标还是几何巧合
                    log("目标统计：走鼠标分支 " + TGT.mouse + " 帧 / 走 WASD 分支 " + TGT.wasd
                        + " 帧 / 停止驱动 " + TGT.camera
                        + " 帧 | 鼠标世界坐标离相机 最小 " + (TGT.minTargetVsCam > 1e8 ? "n/a" : TGT.minTargetVsCam.toFixed(1))
                        + " 最大 " + TGT.maxTargetVsCam.toFixed(1)
                        + (TGT.mouse > 0 && TGT.maxTargetVsCam < 60
                           ? "  ← 鼠标一直在屏幕中心附近：'走向镜头'是几何巧合" : ""));
                    TGT = { mouse: 0, camera: 0, wasd: 0, maxTargetVsCam: 0, minTargetVsCam: 1e9 };
                    driftBuf = null;
                }
            }catch(e){}
        }

        function driftReport(seconds){
            var frames = Math.max(30, Math.round((seconds || 5) * 60));
            driftBuf = { frames: frames, n: 0, sum: 0, maxDelta: 0, held: 0, lastX: null, lastY: null };
            log("drift 诊断开始：现在【按住右键拖动单位】约 " + (frames / 60).toFixed(1) + " 秒");
            return "sampling";
        }

        // 这是判断"到底有没有生效"的唯一硬证据：
        //   · 生效  → 单位朝鼠标靠近（到鼠标的 d 变小），且与屏幕中心的距离会拉大/稳定
        //   · 没生效→ 单位朝屏幕中心靠近（d 基本不变、到相机中心的距离变小）
        function measure(seconds){
            var left = Math.max(1, Math.round((seconds || 6) * 2));   // 每 0.5 秒打一条
            var u = null;
            try{ u = Vars.player.unit(); }catch(e){}
            if(u == null){ log("cam.measure: 当前没有可控单位"); return "no unit"; }
            var lastD = -1, lastC = -1;
            log("cam.measure 开始：请【按住鼠标移动键】拖动，持续约 " + (left / 2) + " 秒");
            try{
                Timer.schedule(function(){
                    try{
                        if(left-- <= 0){ log("cam.measure 结束"); return; }
                        var uu = Vars.player.unit();
                        if(uu == null || !settingOn()){ log("cam.measure 中止（没单位或开关关了）"); return; }
                        var mw = Core.input.mouseWorld();
                        var dxm = mw.x - uu.x, dym = mw.y - uu.y;
                        var dMouse = Math.sqrt(dxm * dxm + dym * dym);
                        var dxc = Core.camera.position.x - uu.x, dyc = Core.camera.position.y - uu.y;
                        var dCam = Math.sqrt(dxc * dxc + dyc * dyc);
                        var trend = "";
                        if(lastD >= 0){
                            trend = "  到鼠标 " + (dMouse < lastD - 0.5 ? "变近↓" : (dMouse > lastD + 0.5 ? "变远↑" : "不变"))
                                  + " / 到屏幕中心 " + (dCam < lastC - 0.5 ? "变近↓(像原版)" : (dCam > lastC + 0.5 ? "变远↑" : "不变"));
                        }
                        log("剩余 " + (left / 2).toFixed(1) + "s 键=" + (mouseMoveDown() ? "按下" : "松开")
                            + " d鼠标=" + Math.round(dMouse) + " d屏中=" + Math.round(dCam)
                            + " move=" + controlMovementDesc() + trend);
                        lastD = dMouse; lastC = dCam;
                    }catch(e){ log("cam.measure 出错：" + e); }
                }, 0, 30);
            }catch(e){ log("cam.measure 无法排程：" + e); return "err"; }
            return "measuring";
        }

        // camWhere() 的实现：把当前状态一次性打成 JSON（排查用）
        function describe(){
            var o = {};
            try{ o.setting = settingOn(); }catch(e){ o.setting = "?"; }
            // v5.6：学术端原味开关 + 当前实际生效的"单位移动目标"
            try{ o.legacy = legacyOn(); }catch(e){ o.legacy = "?"; }
            try{ o.moveTarget = (settingOn() && !legacyOn()) ? "mouse" : "camera"; }catch(e){}
            try{ o.inGame = Vars.state.isGame(); }catch(e){}
            try{ o.unitId = Vars.player.unit() != null ? Vars.player.unit().id : 0; }catch(e){}
            try{ o.dead = Vars.player.dead(); }catch(e){}
            // 待恢复的「死前视野」快照（null 表示没有）
            try{ o.deathSnap = deathSnap == null ? "none"
                : (Math.round(deathSnap.x) + "," + Math.round(deathSnap.y)); }catch(e){}
            try{ o.camera = Math.round(Core.camera.position.x) + "," + Math.round(Core.camera.position.y); }catch(e){}
            try{ o.detachCamera = settings.getBool("detach-camera"); }catch(e){}
            // 本模组接管链路：cursorActive=true 时 d 是"单位到鼠标的世界距离"；
            // 接近目标会按 v=sqrt(2·a·d) 减速（保留滑行惯性）；applied 是覆写生效帧数。
            try{ o.cursorActive = mouseMoveDown(); }catch(e){}
            try{ o.d = Math.round(DBG.d); }catch(e){}
            try{ o.move = controlMovementDesc(); }catch(e){}
            try{ o.applied = DBG.n || 0; }catch(e){}
            try{
                o.camSave = camSave.ok ? (Math.round(camSave.x) + "," + Math.round(camSave.y)) : "none";
                o.camSaveX = Math.round(camSave.x); o.camSaveY = Math.round(camSave.y);
            }catch(e){}
            try{
                o.pin = pinned ? (Math.round(pinX) + "," + Math.round(pinY)) : "none";
                o.pinX = Math.round(pinX); o.pinY = Math.round(pinY);
            }catch(e){}
            // 相机：hold=true 表示这一帧会把相机钉在锚点（即"镜头不动"）
            try{ o.hold = holdCamera(); }catch(e){}
            try{
                var ds = diagState();
                o.panning = ds.panning; o.wasd = ds.wasd; o.moveInput = ds.cursor;
            }catch(e){}
            try{ o.ov = "frames=" + OV.frames + " holding=" + OV.holding; }catch(e){}
            try{ o.tgt = "mouse=" + TGT.mouse + " camera=" + TGT.camera
                + " maxTargetVsCam=" + Math.round(TGT.maxTargetVsCam); }catch(e){}
            // 绑定实况：确认"移动/平移"到底绑在哪个键上、按下时能不能读到
            try{
                var bm = Packages.mindustry.input.Binding;
                o.bindMove = String(bm.mouseMove.value.key) + (Core.input.keyDown(bm.mouseMove) ? "(按下)" : "");
                o.bindPan = String(bm.pan.value.key) + (Core.input.keyDown(bm.pan) ? "(按下)" : "");
            }catch(e){ o.bindMove = "err"; }
            return JSON.stringify(o);
        }

        function controlMovementDesc(){
            try{
                var input = Vars.control != null ? Vars.control.input : null;
                if(input == null || input.movement == null) return "n/a";
                return Math.round(input.movement.x * 100) / 100 + "," + Math.round(input.movement.y * 100) / 100;
            }catch(e){ return "err"; }
        }

        // 进图自检（确认设置项到底有没有挂上；出问题看这几行就够）
        try{
            Events.on(ET.WorldLoadEvent, function(){
                var cs = null;
                try{ cs = Packages.mindustry.ui.dialogs.SettingsMenuDialog.SettingsTable.CheckSetting; }catch(e){}
                var gameTable = null;
                try{ gameTable = ui.settings != null ? ui.settings.game : null; }catch(e){}
                log("自检：CheckSetting=" + (cs != null) + " | 游戏设置页=" + (gameTable != null)
                    + " | 当前开关=" + settingOn());
            });
        }catch(e){}

        log("加载完成（v" + MOD_VERSION + "）：默认开启。位置：设置 → 图像 → 「自由视角」下面那项；也可按 F10 切换");
    }catch(e){
        print("[camera-unbind] 顶层初始化失败：" + e);
    }
}

__cameraUnbindMain();
