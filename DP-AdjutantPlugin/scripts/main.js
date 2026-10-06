// ============================================================================
//  副官调试插件 (Adjutant Debug) —— scripts/main.js    v3.3
//
//  v2.7 悬停名字行改为固定高度（显隐不再改变窗口尺寸，文本框不会跟着跳）。
//
//  v3.3 去掉头像窗底板 + 宽度贴合：
//   · 头像窗原来是 Styles.black6 的 300x122 面板，视觉上就是头像后面一大块深色底板；
//     现在窗口**不画背景**，宽度收窄到 104（= 头像框 92 + margin 12），只留头像 + 矩形框 + 名字。
//   · 消息框本就独立，宽度仍 300，改为相对头像水平居中，并加了屏幕边界夹取。
//
//  v3.2 几何全部改为常量（不再读布局）：
//   · 现象：消息框基准偏上，偏移量约等于头像窗高度的一半 —— 又是"场景根 Table 的 getHeight() 不可靠"。
//   · 现在头像窗尺寸写成常量（ADJ_WIN_W/ADJ_WIN_H，内容恒定：边框 92 + 名字 18 + margin 12），
//     并显式 setSize+validate；每帧摆放、消息框定位、夹边全部由常量算出，不再依赖任何布局回读。
//   · 新增 ADJ_GAP（默认 2px）用于微调头像窗底边与消息框上沿的间隙。
//
//  v3.1 修"消息框盖住头像"：
//   · 根因：独立元素是普通 Table，`getHeight()` 在摆放时仍为 0 → 摆放公式退化成"底边对齐"，
//     而它按自然尺寸**向上**绘制，于是正好盖在头像上。
//   · 现在尺寸**自己算**：行数 × ADJ_LINE_H（并用 Label 的 prefHeight 校正，带合理性钳制），
//     显式 setSize + validate 后再摆放 → 第一帧就贴到头像窗下沿，不再依赖布局时序。
//   · 消息框根元素直接就是带背景的框（不再嵌套一层）。
//
//  v3.0 按反馈调整：
//   · **矩形描边框**取代菱形：菱形是 `Stack` + `setOrigin(Align.center)`，但调用时元素尺寸还是 0，
//     原点落在左下角 → 旋转变成"绕角飞出去"。现在改成 3×3 网格的四条 2px 边，**完全不旋转**。
//   · **删掉消息框左侧的青色竖线**。
//   · **消息框不再固定尺寸**：把它拆成**独立元素**（自己挂到场景根），每帧只把它的上沿贴到头像窗下沿。
//     于是文本框可以随内容自由变高变矮，而头像窗尺寸恒定 → 头像依然不可能被推动。
//
//  v2.9 头像基准彻底固定 + 菱形框：
//   · 消息框高度改为**常量** ADJ_BOX_H（超出 ADJ_LINES 行截断加省略号），
//     没消息时只把背景设透明、**占位保留** → 窗口尺寸在整个会话里恒定不变，
//     于是"头像为基准"不再依赖每帧补偿（物理上不可能被推动）。
//   · 菱形描边框：Stack + 两个旋转 45° 的白色方块（外框 accent 半透明、内块深色）叠出描边，
//     用 Actions.forever + rotateTo 缓慢自转（转 90° 与自身重合，接缝不可见）。
//
//  v2.8 改用引擎高层 API（不再复刻逻辑版的算法）：
//   · 淡入：Actions.fadeIn(0.35)（原来自己每帧累加 alpha）
//   · 头像出场"弹一下"：setOrigin(Align.center) + setScale(0.5) + Actions.scaleTo(1,1,0.32,Interp.swingOut)
//     （对应逻辑版的 textureSize 缓动，但用引擎动画）
//   · 悬停名字：Actions.fadeIn/fadeOut（原来用 visibility 切换）
//   · 停留自动收起：Timer.schedule(...) 返回可 cancel 的 Task（原来轮询 holdUntil）
//   · 眨眼：Timer.schedule 递归排程（原来自己算 tick 概率）
//
//  v2.6 用框架的"顶部基准"方式定位文本：
//   · 问题根源：arc 的 Table 每次布局都按内容**重算自身尺寸**，只要高度会变，头像必被推动；
//     靠每帧挪窗口补偿永远晚一帧 → 看起来就是"头像没定住"。
//   · 正解：**固定高度 + 顶部对齐**。消息框的 Cell 高度在每条消息开始时按整句量出并定死
//     （adjBoxCell.height(boxH)），文本 Cell 用 .top() 贴框顶向下生长 →
//     打字全程窗口尺寸不变，头像纹丝不动；跨消息的高度变化由锚点（每帧按 posTop 摆放）处理。
//
//  v2.5 修拖动与定位（两个真 bug）：
//   · `Image` 默认 touchable=disabled（libGDX 行为）→ 挂在头像上的拖动/悬停监听器**从来没收到过事件**；
//     现在显式打开 touchable，并把拖动监听器挂到头像+名字整块（head）。
//   · 位置原来有**两个来源**：拖动直接改窗口坐标，而每帧"钉住"又用 pinTop 改一次 → 纵向被抢回原位。
//     现在唯一来源是锚点 adjSt.posX / posTop：拖动改锚点，每帧按锚点摆放窗口，两者不可能打架。
//
//  v2.4 以头像为基准：
//   · 窗口**上沿持续钉住**（= 头像位置固定），打字换行、消息收起时只向下/向上生长，头像一动不动；
//     拖动头像时暂停钉住，松手后把新位置作为基准（并写入设置）。
//
//  v2.3 头像与表情：
//   · 5 张表情图（yumu / -working / -confused / -blinking / -gracias，源自你的数据包 sprites/Yumu*.png）
//     已打进模组 sprites/，区域名 = adjutant-debug-yumu*；取图顺序：模组自带 → dp-Yumu* → 单位图标。
//   · 眨眼系统照逻辑版移植：90ms 节拍轮询、10% 概率眨眼、眨眼 90ms、下次检查 4000±2000ms（没眨则 200±50ms）。
//   · 头像按 64:71 显示（setScaling(fit)），不再被拉成正方形；模组图标换成 Yumu。
//
//  v2.2 修"字符串被改写成第一个字"：
//   · 日志证明：传进 adjSay 的字符串长度正确、但字符全变成第一个字（如 271 字的自我介绍变成 271 个"你"），
//     而唯一重建字符串的地方是 wrapStyled → 它和 buildCuts 都用了 `styled.charAt(i)` + 循环内 `const`。
//     现在统一改为 `substring(i, i+1)` + 循环内 `var`（这两点在 Rhino 上更稳）；
//     其余循环内的 const 也一并换成 var（spawn/feed 等）。
//   · 新增**断行自检**：比对"源的前 8 个可见字符"与"排版结果的前 8 个"，不一致就回退为不预排版
//     —— 宁可少排版，也绝不显示坏字。每次消息都会打印 源/最终 长度与开头 12 字，便于继续定位。
//
//  v2.0 修的两个"静默失效"（都来自真实日志）：
//   · 热键全部解析失败：这一版 arc 的 KeyCode 功能键**大小写混用**（F1 f2 F3 F4 f5 f6 F7 f8 F9 f10 f11 F12），
//     所以 KeyCode.F5/F6/F8/F10 根本不存在 → 现在两种写法都试，并打印哪个可用。
//   · 控制台 API 从未发布：Vars.mods.getScripts().scope 从 JS 看是普通全局对象（没有 Java 的 put）→
//     改用 Packages.rhino.ScriptableObject.putProperty()，并保留属性赋值/Java put 两种兜底。
//   · 附带：消息框左侧加青色竖条（区分模组框与逻辑 marker 框）；
//     每条消息打印"原文/排版后/可见字数/cuts/开头"，打完也打印 —— 用于定位打字机问题。
//
//  v1.9 打字机排版优化：
//   · 不再"每帧截断后交给 Label 重新排版"：先用 GlyphLayout 按**字体真实宽度**把整句断行一次
//     （wrapStyled，标记不占宽度、英文单词尽量不切断），换行位置从此固定 → 打字时字不会跳行、框不会抖。
//   · 打字本身仍按"可见字符索引"取前缀（Label 没有 glyph 级 reveal API，硬做要自己遍历
//     GlyphLayout.runs 画字形，风险大且收益低；这样已是"排版一次 + 按索引露出"的正统做法）。
//   · 消息变高时保持窗口上沿不动（原来会把头像往上顶）。
//
//  v1.8 打字机重写：
//   · 改成**前缀查表法**：预先算好"打出 k 个可见字符时的截断下标"，每帧只查表取前缀
//     → 显示内容永远是原文前缀，结构上不可能出现重复字符/乱序（并规避逐帧扫描的边界问题）
//   · 已显示字数只由经过的 tick 决定（纯函数、单调递增、钳制到 [0, 可见字数]）
//   · 设置页新增「打字机自检」按钮；控制台可 adj.type("任意文字")
//
//  v1.7 修的问题 / 改动：
//   · **时间单位错误**：Mindustry 的 Time.delta/Time.time 单位是 **tick** 而不是秒
//     （ClientLauncher: setDeltaProvider(() -> getDeltaTime() * 60f)），
//     我却把"停留 5~8 秒"写成 5~8 tick → 对话框 0.1 秒就消失、疯狂切换、反复重播同一句。
//     现在所有时长统一 ×TPS(60)：停留/空闲/眨眼/淡入/打字音效节流全部修正。
//   · 调试面板从 HUD 浮窗改为**「设置」里的一页**（Vars.ui.settings.addCategory），
//     浮动面板及其拖动/折叠/位置保存/自愈定时器/夹边等代码全部删除；F6 改为直接打开设置。
//   · 副官窗：没有消息时不再显示空文本框；随机台词不连着重复同一句。
//
//  v1.6 新功能：**副官通讯窗**（复刻你的逻辑处理器版副官）
//   · 头像（数据包 dp-Yumu* 贴图）+ 悬停显示名字 + 打字机文本框 + 点击快进/移除
//   · 拖动头像移动位置（位置存 Core.settings）；眨眼/表情切换；开场白 + 随机闲聊；F5 开关
//   · 逻辑版用 marker + 相机坐标换算硬拼屏幕 UI，这里用真正的 arc Scene UI 实现，无需换算
//
//  v1.5 修的显示问题：
//   · 面板会**叠加**：ensurePanel() 用 getChildren().contains(contentTable) 判断面板是否还在，
//     但 Rhino 传给 Java 方法的是包装对象，contains 恒为 false → 每 2 秒又注入一个新面板；
//     你点收起的只是其中一个，其余副本仍显示展开的菜单。
//     → 改成判断 contentTable.parent != null（真实 Java 引用的 null 比较）+ 注入前先 remove() 旧面板。
//   · **可拖动**：面板改挂在场景根 Core.scene.add(panel)（那里不做布局，位置不会被重置），
//     标题行拖动，算法照 arc.scene.ui.Dialog；位置存进 Core.settings，下次启动还原。
//
//  v1.4 修的致命问题（来自你的 last_log.txt）：
//    rhino.EvaluatorException: Java class "arc.input.KeyCode" has no public
//    instance field or method named "F7".  (adjutant-debug/main.js#29)
//  → 裸写 KeyCode.F7 在你这版环境里解析失败，而且它位于**顶层配置区**，
//    异常直接让整个脚本中止：面板、控制台 API、热键全部没生效。
//
//  ── 三条 Rhino 铁律（都在你机器上跑通的模组里 / 日志里验证过）───────────
//   1) 按键写全限定名：Packages.arc.input.KeyCode.F7
//      （本机已跑通的模组：Core.input.keyTap(Packages.arc.input.KeyCode.mouseRight)）
//   2) 同名字段遮蔽方法：unit.health / unit.team / build.team / build.x / Groups.build.size
//      都是**字段**，写成 unit.health() / build.size() 会运行时报错。
//      对照：player.team() 是方法（Player 没有同名字段）。
//   3) 事件监听/回调直接传箭头函数即可，不必包 cons()/run()/boolf()
//
//  ── 三个输入通道 ────────────────────────────────────────────────────────
//   1) HUD 面板（单机/联机通用）：进游戏后屏幕左侧「副官调试面板」，F6 折叠
//   2) 脚本控制台（单机按 Enter）：控制台执行的是 **JavaScript** →
//        adj.help()   adj.spawn("flare", 5)   adj.auto()
//      别写 !adj / /adj（会被当 JS 语法解析而报错）
//   3) 聊天栏（**仅联机**）：!adj help
//
//  改完必须重启游戏（「重载模组」= 退出重进）
// ============================================================================

// 全部初始化包在 try 里：任何一处出错都会在日志留下明确记录，而不是静默失效
function __adjutantMain(){
    "use strict";

    // ======================== 配置区（改这里） ========================

    const CMD           = "!adj";     // 联机聊天命令主前缀
    const CMD_ALT       = "/adj";     // 备用前缀
    const API_NAME      = "adj";      // 单机控制台里的全局对象名

    const DEFAULT_UNIT  = "flare";     // 默认副官单位名
    const MAX_SPAWN     = 50;          // 一次最多生成
    const HEAL_RADIUS   = 40 * 8;      // 自动修理半径（像素；8 像素 = 1 格）
    const HEAL_EVERY    = 30;          // 每多少 tick 修理一次
    const FEED_EVERY    = 120;         // 每多少 tick 补一次物品
    const FEED_AMOUNT   = 1000;        // 每次补多少
    const TPS           = 60;          // 重要：Mindustry 的 Time.delta / Time.time 单位是 tick（1 = 1/60 秒），
                                       // 不是秒！ClientLauncher 里 setDeltaProvider(() -> getDeltaTime() * 60f)

    // 热键：**必须用全限定名**（裸 KeyCode 在你这版会抛异常，见文件头说明）
    // ⚠ 这一版 arc 的 KeyCode 里功能键**大小写混用**（实测 class 常量：
    //   F1 f2 F3 F4 f5 f6 F7 f8 F9 f10 f11 F12）——这才是 F5~F10 全部"不存在"的真正原因，
    //   单纯写全限定名并不够。所以每种键两种写法都试一遍。
    function keyPick(names){
        const K = Packages.arc.input.KeyCode;
        for(let i = 0; i < names.length; i++){
            try{
                const v = K[names[i]];
                if(v != null){
                    print("副官调试插件：热键 " + names[i] + " 可用");
                    return v;
                }
            }catch(e){}
        }
        print("副官调试插件：热键 " + names.join("/") + " 都不可用（不影响按钮，设置页里都有）");
        return null;
    }

    // 交叉验证探针：先确认"点访问"这条路径本身可用（mouseRight 在其它模组里是能用的），
    // 再分别探 f6 / F6 两种拼写 —— 这样如果括号访问在 Rhino 里不可用，也能立刻看出来（避免假阴性）。
    try{ print("副官探针：KeyCode.mouseRight = " + Packages.arc.input.KeyCode.mouseRight); }
    catch(e){ print("副官探针：mouseRight 失败 → " + e); }
    try{ print("副官探针：KeyCode.f6 = " + Packages.arc.input.KeyCode.f6); }
    catch(e){ print("副官探针：f6 失败 → " + e); }
    try{ print("副官探针：KeyCode.F6 = " + Packages.arc.input.KeyCode.F6); }
    catch(e){ print("副官探针：F6 失败 → " + e); }
    try{ print("副官探针：KeyCode[enter] = " + Packages.arc.input.KeyCode["enter"]); }
    catch(e){ print("副官探针：括号访问 enter 失败 → " + e); }

    const KEY_ADJ   = keyPick(["f5", "F5"]);
    const KEY_PANEL = keyPick(["f6", "F6"]);
    const KEY_SPAWN = keyPick(["F7", "f7"]);
    const KEY_KILL  = keyPick(["f8", "F8"]);
    const KEY_AUTO  = keyPick(["F9", "f9"]);
    const KEY_LOG   = keyPick(["f10", "F10"]);

    // 自动补料尝试的物品名（找不到的自动跳过）
    const FEED_ITEMS = [
        "copper", "lead", "metaglass", "graphite", "sand", "coal", "titanium", "thorium",
        "scrap", "silicon", "plastanium", "phase-fabric", "surge-alloy", "spore-pod",
        "blast-compound", "pyratite", "beryllium", "tungsten", "oxide", "carbide", "fissile-matter"
    ];

    // 单位列表兜底（万一 content.units() 取不到，面板也能用）
    const FALLBACK_UNITS = [
        "flare", "dagger", "mace", "fortress", "scepter", "reign", "mono", "poly", "mega", "quad",
        "oct", "toxopid", "crawler", "atrax", "spiroct", "arkyid", "nova", "pulsar", "quasar", "vela",
        "corvus", "risso", "minke", "bryde", "sei", "omura", "retusa", "oxynoe", "cyerce", "aegires",
        "navanax", "alpha", "beta", "gamma"
    ];

    // ======================== 运行时状态 ========================

    const st = {
        auto: false, log: false, tick: 0,
        unitIndex: 0, itemIndex: 0
    };

    let contentTable = null;

    // ======================== 小工具 ========================

    function headless(){
        return Vars.headless || Core.input == null || Vars.ui == null;
    }

    function inGame(){
        return !headless() && Vars.state != null && Vars.state.isGame()
            && Vars.player != null && Vars.player.unit() != null;
    }

    function myTeam(){
        return Vars.player.team();          // Player.team() 是方法
    }

    function toast(text){
        try{ if(!headless()) Vars.ui.showInfoToast(text, 3); }catch(e){}
    }

    function say(text){
        try{ if(!headless() && Vars.ui.chatfrag != null) Vars.ui.chatfrag.addMessage(text); }catch(e){}
        print(text);
    }

    function cursor(){
        try{
            const v = Core.input.mouseWorld();
            if(v != null) return [v.x, v.y];
        }catch(e){}

        const u = (Vars.player == null) ? null : Vars.player.unit();
        return u == null ? [0, 0] : [u.x, u.y];    // 单位坐标是字段
    }

    function fx(x, y){
        try{ Fx.heal.at(x, y); }catch(e){}
    }

    function alive(e){
        try{ return e != null && e.isValid(); }catch(err){ return false; }
    }

    // ======================== 功能 ========================

    function spawnAdj(unitName, amount){
        const type = Vars.content.unit(unitName);
        if(type == null){
            toast("[scarlet]找不到单位：" + unitName);
            return 0;
        }

        const n = Math.min(amount, MAX_SPAWN);
        const pos = cursor();
        const x = pos[0], y = pos[1];
        let spawned = 0;

        var i = 0, a = 0, d = 0, u = null;
        for(i = 0; i < n; i++){
            a = Math.random() * 360;
            d = 8 + Math.random() * 24;
            try{
                u = type.spawn(myTeam(), x + Mathf.cosDeg(a) * d, y + Mathf.sinDeg(a) * d);
                if(u != null) spawned++;
            }catch(e){
                print("spawn 失败: " + e);
            }
        }

        fx(x, y);
        toast("[accent]副官 x" + spawned + " [lightgray](" + unitName + ")");
        return spawned;
    }

    function healArea(){
        if(!inGame()) return 0;

        const t = myTeam();
        const u = Vars.player.unit();
        const x = u.x, y = u.y;                     // 字段
        let count = 0;

        Groups.build.each((b) => {
            if(b.team == t && alive(b) && b.health < b.maxHealth && b.within(x, y, HEAL_RADIUS)){
                b.heal(b.maxHealth);                // heal()/within() 是方法
                count++;
            }
        });

        Groups.unit.each((o) => {
            if(o.team == t && alive(o) && o.health < o.maxHealth && o.within(x, y, HEAL_RADIUS)){
                o.heal(o.maxHealth);
                count++;
            }
        });

        return count;
    }

    function feedCore(){
        if(!inGame()) return 0;

        const core = myTeam().core();
        if(core == null){
            toast("[scarlet]当前队伍没有核心");
            return 0;
        }

        let n = 0;
        var i = 0, item = null;
        for(i = 0; i < FEED_ITEMS.length; i++){
            item = Vars.content.item(FEED_ITEMS[i]);
            if(item != null){
                core.items.add(item, FEED_AMOUNT);  // items 字段，add() 方法
                n++;
            }
        }
        return n;
    }

    function giveItem(itemName, amount){
        if(!inGame()) return "不在游戏里";

        const item = Vars.content.item(itemName);
        if(item == null) return "找不到物品：" + itemName;

        const core = myTeam().core();
        if(core == null) return "当前队伍没有核心";

        const n = (amount == null) ? FEED_AMOUNT : amount;
        core.items.add(item, n);
        toast("[accent]已加入 " + item.localizedName + " x" + n);
        return "已加入 " + item.localizedName + " x" + n;
    }

    function killEnemies(){
        if(!inGame()) return 0;

        const t = myTeam();
        const list = [];

        Groups.unit.each((u) => {
            if(u.team != t && !u.isPlayer() && alive(u)) list.push(u);
        });

        for(let i = 0; i < list.length; i++){
            list[i].kill();
        }
        return list.length;
    }

    function countUnits(mine){
        if(!inGame()) return 0;
        const t = myTeam();
        let n = 0;
        Groups.unit.each((u) => {
            if((u.team == t) == mine) n++;
        });
        return n;
    }

    function toggleCheat(force){
        if(!inGame()) return false;

        const r = Vars.state.rules;
        const on = (force == null) ? !r.infiniteResources : !!force;

        r.infiniteResources = on;
        r.instantBuild = on;
        r.buildSpeedMultiplier = on ? 100 : 1;
        r.unitBuildSpeedMultiplier = on ? 100 : 1;
        r.disableUnitCap = on;
        return on;
    }

    function setAuto(v){
        st.auto = (v == null) ? !st.auto : !!v;
        toast("[accent]自动副官：" + (st.auto ? "开" : "关"));
        return st.auto;
    }

    function setLog(v){
        st.log = (v == null) ? !st.log : !!v;
        toast("[accent]事件日志：" + (st.log ? "开" : "关"));
        return st.log;
    }

    function setWaves(v){
        if(!inGame()) return false;
        Vars.state.rules.waves = (v == null) ? !Vars.state.rules.waves : !!v;
        toast("[accent]波次：" + (Vars.state.rules.waves ? "开" : "关"));
        return Vars.state.rules.waves;
    }

    function runWave(){
        try{
            Vars.logic.runWave();
            toast("[accent]已触发下一波");
            return "已触发下一波";
        }catch(err){
            return "触发波次失败：" + err;
        }
    }

    // ======================== 文本 ========================

    function helpText(){
        return "[accent]===== 副官调试插件 =====\n"
            + "[white]调试项[]：在「设置」→「副官调试」页（F6 打开设置）\n"
            + "[white]" + API_NAME + ".spawn(\"单位\", 数量)[]  生成副官（默认 " + DEFAULT_UNIT + "）\n"
            + "[white]" + API_NAME + ".heal()[]  修理/治疗周围 " + Mathf.round(HEAL_RADIUS / 8) + " 格\n"
            + "[white]" + API_NAME + ".give(\"物品\", 数量)[]  往核心塞物品\n"
            + "[white]" + API_NAME + ".kill()[]  清除所有敌方单位\n"
            + "[white]" + API_NAME + ".wave()[] / " + API_NAME + ".waves()[] / " + API_NAME + ".cheat()[]\n"
            + "[white]" + API_NAME + ".auto()[] / " + API_NAME + ".log()[] / " + API_NAME + ".panel()[] / " + API_NAME + ".report()[]\n"
            + "[lightgray]字符串形式：" + API_NAME + "(\"spawn flare 5\")\n"
            + "[white]" + API_NAME + ".line(\"台词\")[]  让副官说一句    " + API_NAME + ".avatar(false)[]  收起副官窗\n"
            + "[lightgray]热键：F5 副官窗 / F6 设置 / F7 生成 / F8 清场 / F9 自动副官 / F10 日志\n"
            + "[lightgray]联机聊天栏：" + CMD + " help     （单机没有聊天栏，请用控制台或面板）";
    }

    function reportText(){
        if(!inGame()) return "不在游戏里";
        return "[accent]===== 副官报告 =====\n"
            + "波次 [white]" + Vars.state.wave + "[]  下一波 [white]"
            + Strings.autoFixed(Vars.state.wavetime / 60, 1) + "s[]  波次开关 [white]" + Vars.state.rules.waves + "\n"
            + "单位：我方 [white]" + countUnits(true) + "[]  敌方 [white]" + countUnits(false)
            + "[]  建筑 [white]" + Groups.build.size + "\n"
            + "自动副官 [white]" + (st.auto ? "开" : "关") + "[]  日志 [white]" + (st.log ? "开" : "关")
            + "[]  无限资源 [white]" + Vars.state.rules.infiniteResources + "\n"
            + "帧率 [white]" + Core.graphics.getFramesPerSecond()
            + "[]  单位上限 [white]" + (Vars.state.rules.unitCap <= 0 ? "无限制" : Vars.state.rules.unitCap);
    }

    // ======================== 命令分发 ========================

    function runCommand(text){
        const rest = String(text == null ? "" : text).trim();
        const parts = rest.length == 0 ? [] : rest.split(" ");
        const sub = parts.length == 0 ? "help" : String(parts[0]).toLowerCase();

        if(sub == "help" || sub == "?"){
            const t = helpText();
            say(t);
            return t;

        }else if(sub == "spawn" || sub == "s"){
            const un = parts.length > 1 ? parts[1] : DEFAULT_UNIT;
            const amount = parts.length > 2 ? parseInt(parts[2]) : 1;
            return "已生成 " + spawnAdj(un, (isNaN(amount) || amount <= 0) ? 1 : amount) + " 个 " + un;

        }else if(sub == "heal" || sub == "h"){
            const n = healArea();
            toast("[accent]已修理/治疗 " + n + " 个目标");
            return "已修理/治疗 " + n + " 个目标";

        }else if(sub == "give" || sub == "g"){
            if(parts.length < 2) return "用法：give <物品名> [数量]";
            const amount = parts.length > 2 ? parseInt(parts[2]) : FEED_AMOUNT;
            return giveItem(parts[1], isNaN(amount) ? FEED_AMOUNT : amount);

        }else if(sub == "kill" || sub == "k"){
            const n = killEnemies();
            toast("[accent]清除了 " + n + " 个敌方单位");
            return "清除了 " + n + " 个敌方单位";

        }else if(sub == "wave" || sub == "w"){
            return runWave();

        }else if(sub == "waves"){
            return "波次：" + (setWaves(null) ? "开" : "关");

        }else if(sub == "auto" || sub == "a"){
            return "自动副官：" + (setAuto(null) ? "开" : "关");

        }else if(sub == "log" || sub == "l"){
            return "事件日志：" + (setLog(null) ? "开" : "关");

        }else if(sub == "cheat" || sub == "c"){
            const on = toggleCheat(null);
            toast("[accent]沙盒作弊：" + (on ? "开" : "关"));
            return "沙盒作弊：" + (on ? "开" : "关");

        }else if(sub == "settings" || sub == "panel" || sub == "p"){
            try{ Vars.ui.settings.show(); }catch(e){}
            return "已打开设置（副官调试页）";

        }else if(sub == "report" || sub == "r"){
            const t = reportText();
            say(t);
            return t;
        }

        return "未知子命令：" + sub + "（用 help 看列表）";
    }

    // ======================== 单位 / 物品 选择 ========================

    function nameOf(c){
        try{
            if(typeof c.name == "string") return c.name;
        }catch(e){}
        return String(c);
    }

    function contentList(getter){
        try{
            const l = getter();
            if(l != null && l.size > 0) return l;    // Seq.size 是字段
        }catch(e){
            print("读取内容列表失败：" + e);
        }
        return null;
    }

    function listSize(getter, fallback){
        const l = contentList(getter);
        return (l == null) ? fallback.length : l.size;
    }

    function pickName(getter, fallback, index){
        const l = contentList(getter);
        if(l == null){
            const i = ((index % fallback.length) + fallback.length) % fallback.length;
            return fallback[i];
        }
        const i = ((index % l.size) + l.size) % l.size;
        return nameOf(l.get(i));
    }

    function unitName(){
        return pickName(() => Vars.content.units(), FALLBACK_UNITS, st.unitIndex);
    }

    function itemName(){
        return pickName(() => Vars.content.items(), FEED_ITEMS, st.itemIndex);
    }

    function cycleUnit(dir){
        const n = listSize(() => Vars.content.units(), FALLBACK_UNITS);
        if(n > 0) st.unitIndex = ((st.unitIndex + dir) % n + n) % n;
        rebuild();
    }

    function cycleItem(dir){
        const n = listSize(() => Vars.content.items(), FEED_ITEMS);
        if(n > 0) st.itemIndex = ((st.itemIndex + dir) % n + n) % n;
        rebuild();
    }

    // ======================== 副官通讯窗（复刻逻辑处理器版副官） ========================
    // 你的逻辑版用 marker（texture/text/quad/line）+ 相机坐标换算在屏幕上"画"出：
    //   头像、菱形边框、名字（悬停显示）、打字机文本框（点击快进/移除）、拖动头像、表情闪烁、随机闲聊。
    // 这里用真正的 arc Scene UI 复刻同样观感：不需要坐标换算，也不需要管理 marker。
    // 头像直接取数据包 dp-Yumu* 的贴图（导入「补丁与资源」后图集里就有这些区域）。

    const ADJ_NAME = "喻晓暮";

    // 头像贴图：优先用模组自带的那 5 张（从你的数据包里取出来的 yumu*.png，
    // 打包后区域名 = 模组名 + "-" + 文件名，见 Mods.packSprites），
    // 再退回数据包的 dp-Yumu*，最后退回单位图标 —— 三条路都试，永远有图可显示。
    const ADJ_AVATARS = {
        normal:   ["adjutant-debug-yumu", "yumu", "dp-Yumu"],
        working:  ["adjutant-debug-yumu-working", "yumu-working", "dp-Yumu-working"],
        confused: ["adjutant-debug-yumu-confused", "yumu-confused", "dp-Yumu-confused"],
        blink:    ["adjutant-debug-yumu-blinking", "yumu-blinking", "dp-Yumu-blinking"],
        gracias:  ["adjutant-debug-yumu-gracias", "yumu-gracias", "dp-Yumu-gracias"]
    };

    // 台词（保留你原来的颜色标记，由 Label 渲染）
    const ADJ_INTRO = [
        ["[accent]-<接收到通讯请求>-[]\n正在连线...\n[gray]协议版本v1.0[]", "working", 3.2],
        ["你好、[accent]{0}[white]指挥官\n\n受恶劣天气的影响，核心的降落位置出现了一些偏差。幸亏我们对这个核心试行了 MCV 改装。\n\n目前 MCV 正在赶往预定作战区域，请稍等片刻。\n\n……\n\n哦对了，自我介绍一下——\n我是[highlight]喻晓暮[]，根据作战协议，现确认担任您的[highlight]副官[]。\n我的职责包括：播报战场态势、传达任务目标、协助调查当前区域。\n\n[gray]提示：拖动头像可以调整副官显示位置；点击消息框可快进或移除已读信息[]", "gracias", 24.0]
    ];

    const ADJ_IDLE = [
        ["怎么了？", "confused", 5.0],
        ["什么事？", "confused", 5.0],
        ["敌方尚无动向，指挥官。", "working", 8.0],
        ["我在、指挥官。", "normal", 6.0],
        ["空想误国，实干兴邦。", "normal", 6.0],
        ["[highlight]点击消息框[]可以快进和移除已读信息哦。", "normal", 8.0],
        ["装填钛的巡弋为反导核弹井。如果面临核威胁，可以建造[highlight]钛巡弋[]。", "gracias", 8.0],
        ["我的名字？喻姓是真实存在的。不过可以通余姓，这个更常用。晓暮的话，不是我起的名字，寓意我也不是很清楚。", "confused", 14.0],
        ["我的生日？我也不知道、指挥官。嗯，真的。", "confused", 8.0]
    ];

    const ADJ_CPS = 25;      // 打字速度（字符/秒；逻辑版是 2 字 / 80ms）
    const ADJ_TEXT_W = 280;  // 消息框内文本可用宽度（像素），用于预先断行
    // （消息框不再有固定高度：它已独立成元素，可以自由伸缩而不影响头像）
    const ADJ_LINE_H = 24;   // 行高估算（用于自己算消息框高度，不依赖布局时序）
    // 头像窗的尺寸是**恒定**的（边框 92 + 名字 18 + margin 12），所以直接写成常量：
    // 所有几何都由常量算出，不再读挂在场景根的 Table 的 getHeight()（那儿布局时序不可靠）
    const ADJ_WIN_W  = 104;  // 只贴合头像框（92 + margin 12）——窗口不再画底板，不需要这么宽
    const ADJ_WIN_H  = 122;
    const ADJ_GAP    = 2;    // 头像窗底边与消息框上沿之间的间隙（像素）
    const ADJ_CPT = ADJ_CPS / TPS;   // 每 tick 打几个字

    const adjSt = {
        open: true, built: false, hovering: false,
        expr: "normal", picked: {}, bgOn: true,
        text: "", plain: 0, shown: 0, startTime: 0, hold: 6, typing: false,
        idleAt: 0, introIndex: 0, fade: 0, lastIdle: -1,
        cuts: null, plainCount: 0, lastH: 0,
        posX: -1, posTop: -1           // 位置唯一来源：窗口左上角；posTop 就是头像上沿，打字时不动
    };

    let adjWindow = null, adjAvatar = null, adjName = null, adjText = null, adjBox = null, adjBoxRoot = null, adjTickAt = 0;

    // 贴图：优先 dp-Yumu*，找不到就退回默认单位的图标
    function adjAvatarDrawable(key){
        const names = ADJ_AVATARS[key] || ADJ_AVATARS.normal;
        for(let i = 0; i < names.length; i++){
            try{
                if(Core.atlas.has(names[i])){
                    if(!adjSt.picked[key]){
                        adjSt.picked[key] = names[i];
                        print("副官头像：" + key + " → " + names[i]);
                    }
                    return new TextureRegionDrawable(Core.atlas.find(names[i]));
                }
            }catch(e){}
        }
        try{
            return new TextureRegionDrawable(Vars.content.unit(DEFAULT_UNIT).uiIcon);
        }catch(e){}
        return null;
    }

    function adjSetExpr(key){
        adjSt.expr = key;
        try{
            const d = adjAvatarDrawable(key);
            if(d != null && adjAvatar != null) adjAvatar.setDrawable(d);
        }catch(e){}
    }

    // ---- 预先断行：用字体真实宽度排版**一次**，把换行固化进字符串 ----
    // 这样打字过程中行位置不再变化（不会像逐帧重排那样"字跳行"），
    // 之后打字机只需按索引取前缀。英文单词尽量不断在中间。
    function measureWidth(s){
        try{
            return new GlyphLayout(Fonts.def, s).width;
        }catch(e){
            return s.length * 16;      // 兜底：粗估（中文约 16px/字）
        }
    }

    function toksToStr(toks, from, to){
        let s = "";
        for(let i = from; i < to; i++){
            s += (toks[i].m != null) ? toks[i].m : toks[i].c;
        }
        return s;
    }

    function toksPlain(toks){
        let s = "";
        for(let i = 0; i < toks.length; i++){
            if(toks[i].c != null) s += toks[i].c;
        }
        return s;
    }

    function wrapStyled(styled, maxWidth){
        // 先切成 token：颜色标记 / 普通字符
        const toks = [];
        var i = 0, ch = "", close = 0;
        while(i < styled.length){
            ch = styled.substring(i, i + 1);          // 用 substring 而不是 charAt（Rhino 兼容性）
            if(ch == "["){
                close = styled.indexOf("]", i);
                if(close > i){ toks.push({m: styled.substring(i, close + 1)}); i = close + 1; continue; }
            }
            toks.push({c: ch});
            i++;
        }

        let line = [], result = "";
        var k = 0, tk = null, plain = "";
        for(k = 0; k < toks.length; k++){
            tk = toks[k];

            if(tk.m != null){ line.push(tk); continue; }        // 标记不占宽度

            if(tk.c == "\n"){
                result += toksToStr(line, 0, line.length) + "\n";
                line = [];
                continue;
            }

            plain = toksPlain(line);
            if(plain.length > 0 && measureWidth(plain + tk.c) > maxWidth){
                // 断行：若当前行内有空格且新字符是英文/数字，退到空格处断（避免切断单词）
                var cut = -1, x = 0;
                if(tk.c != null && /[A-Za-z0-9]/.test(tk.c)){
                    for(x = line.length - 1; x >= 0; x--){
                        if(line[x].c == " "){ cut = x; break; }
                    }
                }
                if(cut > 0){
                    result += toksToStr(line, 0, cut) + "\n";
                    line = line.slice(cut + 1);
                }else{
                    result += toksToStr(line, 0, line.length) + "\n";
                    line = [];
                }
            }

            line.push(tk);
        }
        return result + toksToStr(line, 0, line.length);
    }

    // 取前 n 个"可见"字符（跳过换行）—— 也用作断行自检的比对
    function firstVisibleChars(s, n){
        let out = "", i = 0, ch = "";
        while(i < s.length && out.length < n){
            ch = s.substring(i, i + 1);
            i++;
            if(ch == "\n") continue;
            out += ch;
        }
        return out;
    }

    // ---- 打字机：前缀查表法 ----
    // 先算好"打出 k 个可见字符时该截到哪个下标"，之后每帧只查表取一个前缀：
    // 显示内容永远是 text.substring(0, cuts[k])，**结构上不可能出现重复字符或乱序**。
    // 颜色标记 [xxx] 并入它前面那个截断点，所以标记不会被打断成半截显示。
    function buildCuts(styled){
        const cuts = [0];
        var i = 0, ch = "", close = 0;
        while(i < styled.length){
            ch = styled.substring(i, i + 1);
            if(ch == "["){
                close = styled.indexOf("]", i);
                if(close > i){
                    cuts[cuts.length - 1] = close + 1;   // 标记并入上一个截断点
                    i = close + 1;
                    continue;
                }
            }
            i++;
            cuts.push(i);
        }
        return cuts;
    }

    function adjTextAt(k){
        const cuts = adjSt.cuts;
        if(cuts == null || cuts.length == 0) return "";
        const kk = Math.max(0, Math.min(k, cuts.length - 1));
        return adjSt.text.substring(0, cuts[kk]);
    }

    function adjPlayerName(){
        try{
            if(Vars.player != null && Vars.player.name != null) return String(Vars.player.name);
        }catch(e){}
        return "指挥官";
    }

    function adjBuild(){
        try{
            if(adjWindow != null) adjWindow.remove();
            adjWindow = null;

            const w = new Table();          // 不画底板：只保留头像 + 矩形描边框 + 名字
            w.margin(6);
            w.touchable = Touchable.enabled;
            w.visibility = () => panelVisible() && adjSt.open;

            // 头像（同时是拖动把手，和逻辑版"拖动头像"一致）
            const head = w.table().get();
            // 头像 + **菱形描边框**（对应逻辑版 id.Frame：旋转 45° 的方框 + stroke）：
            // 两个白色方块用不同 scale 叠出"描边"，整体 3.6 秒转 90°（正方形转 90° 与自身重合，
            // 所以循环重置时看不出接缝 → 表现为缓慢自转）。
            adjAvatar = new Image(adjAvatarDrawable(adjSt.expr));
            try{ adjAvatar.setScaling(Scaling.fit); }catch(e){}
            try{ adjAvatar.touchable = Touchable.enabled; }catch(e){}
            try{
                adjAvatar.setOrigin(Align.center);
                adjAvatar.setScale(0.5);
                adjAvatar.addAction(Actions.scaleTo(1, 1, 0.32, Interp.swingOut));
            }catch(e){}

            let avatarPlaced = false;
            try{
                // **矩形描边框**（不再旋转、不再有原点问题）：3×3 网格，四条 2px 边 + 中间头像
                const frame = new Table();
                const bar = () => {
                    const i = new Image(Tex.whiteui);
                    i.setColor(Pal.accent.r, Pal.accent.g, Pal.accent.b, 0.85);
                    return i;
                };
                frame.add(bar()).growX().height(2).colspan(3); frame.row();
                frame.add(bar()).width(2).growY();
                frame.add(adjAvatar).size(88, 88);
                frame.add(bar()).width(2).growY(); frame.row();
                frame.add(bar()).growX().height(2).colspan(3);
                head.add(frame).padBottom(2);
                avatarPlaced = true;
            }catch(e){
                print("副官调试插件：头像边框构建失败，退回纯头像 → " + e);
            }
            if(!avatarPlaced){
                try{ head.add(adjAvatar).size(68, 76); }catch(e){}
            }
            try{ head.touchable = Touchable.enabled; }catch(e){}
            // ★ Image 默认 touchable=disabled（libGDX 行为），不打开的话拖动与悬停都收不到事件
            try{ adjAvatar.touchable = Touchable.enabled; }catch(e){}
            try{ head.touchable = Touchable.enabled; }catch(e){}
            head.row();
            adjName = new Label(ADJ_NAME);
            // 名字行给固定高度：悬停时只是显隐，**不改变窗口尺寸**（否则文本框会跟着跳）
            head.add(adjName).padTop(1).height(18);
            try{ adjName.color.a = 0; }catch(e){}    // 用透明度显隐（cell 高度固定，不会引起重排）
            w.row();

            // ★ 消息框改成**独立元素**（不再放进头像窗）：
            //   这样文本框能随内容自由变高变矮（**不固定尺寸**），而头像窗自身尺寸恒定不变，
            //   于是头像永远不可能被推动 —— 框的位置由每帧"贴到头像窗下沿"决定。
            // 根**就是**消息框本身（不再嵌套）：尺寸由每帧显式算出并设定，
            // 这样第一帧就不会算错高度（之前 getHeight() 为 0 → 框向上画、盖住头像）。
            adjBoxRoot = new Table(Styles.black3);
            adjBoxRoot.touchable = Touchable.enabled;
            adjBoxRoot.top();
            adjBoxRoot.visibility = () => adjSt.text.length > 0;
            adjBox = adjBoxRoot;
            adjText = new Label("");
            try{ adjText.setWrap(true); }catch(e){}
            adjBox.add(adjText).width(288).left().top().pad(4);   // 文本贴框顶、向下生长
            adjBox.clicked(() => adjClick());
            Core.scene.add(adjBoxRoot);                            // 独立挂进场景根

            // 悬停检测（显示名字）
            adjAvatar.addListener(JavaAdapter(Packages.arc.scene.event.InputListener, {
                enter: function(event, x, y, pointer, fromActor){
                    adjSt.hovering = true;
                    try{ adjName.clearActions(); adjName.addAction(Actions.fadeIn(0.15)); }catch(e){}
                },
                exit:  function(event, x, y, pointer, toActor){
                    adjSt.hovering = false;
                    try{ adjName.clearActions(); adjName.addAction(Actions.fadeOut(0.2)); }catch(e){}
                }
            }));

            // ★ 显式设定头像窗尺寸（内容恒定）：几何全部来自常量，不依赖布局时序
            try{ w.top(); w.setSize(ADJ_WIN_W, ADJ_WIN_H); w.validate(); }catch(e){}

            makeDraggable(head, w, adjSavePos);      // 头像+名字整块都能拖
            Core.scene.add(w);
            adjWindow = w;
            adjSt.built = true;

            // 位置：优先用上次拖动保存的（逻辑版固定 0.6/0.6，这里默认也是屏幕 60% 处）
            // 锚点 = 从设置里读回来的"上沿位置"（首次用屏幕 60% / 70% 处）
            let ax = -1, at = -1;
            try{
                ax = Core.settings.getInt("adjutant-avatar-x", -1);
                at = Core.settings.getInt("adjutant-avatar-y", -1);
            }catch(e){}
            if(ax < 0 || at < 0){
                let sw = 1280, sh = 720;
                try{ sw = Core.graphics.getWidth(); sh = Core.graphics.getHeight(); }catch(e){}
                ax = Math.round(sw * 0.6);
                at = Math.round(sh * 0.7);
            }
            adjSt.posX = ax;
            adjSt.posTop = at;
            w.setPosition(ax, Math.max(0, at - 120));    // 下一帧会按真实高度对齐到锚点
            adjSt.lastH = 0;
            // 淡入：直接用引擎动画（原来是自己每帧累加 alpha）
            try{ w.color.a = 0; w.addAction(Actions.fadeIn(0.35)); }catch(e){}
            adjScheduleBlink();

            print("副官调试插件：副官通讯窗已建立");
        }catch(e){
            print("副官调试插件：建立副官窗失败 → " + e);
        }
    }

    function adjClamp(){
        try{
            if(adjWindow == null || adjWindow.parent == null) return;
            const sw = Core.graphics.getWidth(), sh = Core.graphics.getHeight();
            const ww = ADJ_WIN_W, hh = ADJ_WIN_H;
            adjSt.posX = Mathf.clamp(adjSt.posX < 0 ? adjWindow.x : adjSt.posX, 0, Math.max(0, sw - ww));
            adjSt.posTop = Mathf.clamp(adjSt.posTop < 0 ? adjWindow.y + hh : adjSt.posTop, hh, sh);
            adjWindow.setPosition(Math.round(adjSt.posX), Math.round(adjSt.posTop - hh));
        }catch(e){}
    }

    function adjSavePos(){
        try{
            Core.settings.put("adjutant-avatar-x", Math.round(adjSt.posX));
            Core.settings.put("adjutant-avatar-y", Math.round(adjSt.posTop));
        }catch(e){}
    }

    // 一条新消息：打字机从 0 开始
    function adjSay(styled, expr, hold){
        if(adjWindow == null) return;
        adjSt.open = true;
        const src = String(styled);
        let wrapped = src;
        try{
            const w = wrapStyled(src, ADJ_TEXT_W);
            // 自检：断行只允许"插入换行"，不允许改变字符顺序 —— 比对前 8 个可见字符
            if(firstVisibleChars(w, 8) == firstVisibleChars(src, 8)){
                wrapped = w;
            }else{
                print("副官打字机：断行自检未通过，回退为不预排版（文字仍可读）"
                    + " ｜源「" + firstVisibleChars(src, 8) + "」vs 结果「" + firstVisibleChars(w, 8) + "」");
            }
        }catch(e){
            print("副官打字机：预排版异常，回退 → " + e);
        }

        adjSt.text = wrapped;
        adjSt.cuts = buildCuts(adjSt.text);
        adjSt.plain = adjSt.cuts.length - 1;      // 可见字符总数
        adjSt.shown = 0;
        print("副官打字机：原文 " + src.length + " 字 → 最终 " + adjSt.text.length
            + " 字 / 可见 " + adjSt.plain + " / cuts " + (adjSt.cuts == null ? -1 : adjSt.cuts.length)
            + " ｜开头「" + firstVisibleChars(adjSt.text, 12) + "」");
        // 不限制行数：消息框是独立元素，多高都不影响头像

        adjSt.startTime = Time.time;
        adjSt.hold = ((hold == null) ? 6 : hold) * TPS;      // 秒 → tick
        adjCancelHold();
        adjSt.typing = true;
        adjSetExpr(expr || "normal");
        try{ adjText.setText(""); }catch(e){}

        // 通讯开启音（逻辑版：playsound @sfx-uiChat 1.2 1）
        try{ Sounds.uiChat.play(0.8, 1.0, 0); }catch(e){ try{ Sounds.uiChat.play(); }catch(e2){} }
    }

    function adjHide(){
        adjSt.typing = false;
        adjCancelHold();
        adjSt.text = "";
        adjSt.shown = 0;
        adjSt.cuts = null;
        try{ adjText.setText(""); }catch(e){}
        adjSt.idleAt = Time.time + (2 + Math.random() * 4) * TPS;
    }

    // 点击消息框：打字中→立刻打完；已打完→移除（和逻辑版一致）
    function adjClick(){
        if(adjSt.typing){
            adjSt.shown = adjSt.plain;
            try{ adjText.setText(adjSt.text); }catch(e){}
            adjSt.typing = false;
            adjHoldStart(adjSt.hold / TPS);      // 停留交给引擎定时器（点第二下可直接 cancel）
        }else if(adjSt.text.length > 0){
            adjHide();
        }
    }

    // ---- 引擎定时器：停留自动收起 / 延迟眨眼（取代原来自己算 tick 的 holdUntil 轮询与眨眼调度） ----
    let adjHoldTask = null, adjBlinkRestore = null;

    function adjCancelHold(){
        try{ if(adjHoldTask != null) adjHoldTask.cancel(); }catch(e){}
        adjHoldTask = null;
    }

    function adjHoldStart(seconds){
        adjCancelHold();
        try{
            adjHoldTask = Timer.schedule(() => { adjHoldTask = null; adjHide(); }, Math.max(0.5, seconds));
        }catch(e){}
    }

    // 眨眼：Timer 排到点就眨一下，90ms 后恢复（等效效果，不再逐帧判断）
    function adjScheduleBlink(){
        try{
            Timer.schedule(() => {
                if(headless() || !adjSt.built) return;
                if(adjSt.typing && adjSt.text.length > 0){
                    try{
                        const d = adjAvatarDrawable("blink");
                        if(d != null) adjAvatar.setDrawable(d);
                        adjBlinkRestore = Timer.schedule(() => { try{ adjSetExpr(adjSt.expr); }catch(e){} }, 0.09);
                    }catch(e){}
                }
                adjScheduleBlink();
            }, 1.5 + Math.random() * 3.5);
        }catch(e){}
    }

    function adjRandomLine(){
        let i = Math.floor(Math.random() * ADJ_IDLE.length);
        if(ADJ_IDLE.length > 1 && i == adjSt.lastIdle) i = (i + 1) % ADJ_IDLE.length;
        adjSt.lastIdle = i;
        const m = ADJ_IDLE[i];
        adjSay(m[0], m[1], m[2]);
    }

    function adjToggle(v){
        adjSt.open = (v == null) ? !adjSt.open : !!v;
        if(adjSt.open && adjWindow != null){
            adjSt.introIndex = ADJ_INTRO.length;      // 手动打开时跳过开场白
            adjHide();
        }
        return adjSt.open;
    }

    // 每帧驱动：淡入 / 打字机 / 眨眼 / 空闲闲聊 / 到点收起
    function adjUpdate(){
        if(headless() || !adjSt.built || adjWindow == null || !adjSt.open) return;
        if(!panelVisible()) return;

        const now = Time.time;

        // ★ 位置唯一来源是锚点 posX / posTop：窗口每帧按锚点摆放，所以打字换行时**上沿（头像）不动**，
        //   而拖动时改的也是锚点 —— 两者永远不会互相抢位置（这就是之前纵向回弹的原因）。
        try{
            const h = ADJ_WIN_H;                 // ★ 常量，不读布局
            {
                let sw = 1280, sh = 720;
                try{ sw = Core.graphics.getWidth(); sh = Core.graphics.getHeight(); }catch(e){}
                const ww = ADJ_WIN_W;
                adjSt.posX = Mathf.clamp(adjSt.posX, 0, Math.max(0, sw - ww));
                adjSt.posTop = Mathf.clamp(adjSt.posTop, h, sh);
                const ty = adjSt.posTop - h;
                if(Math.abs(adjWindow.x - adjSt.posX) > 0.5 || Math.abs(adjWindow.y - ty) > 0.5){
                    adjWindow.setPosition(Math.round(adjSt.posX), Math.round(ty));
                }
                if(adjSt.lastH == 0){
                    print("副官调试插件：副官窗 " + Math.round(ww) + "x" + Math.round(h)
                        + " 上沿 " + Math.round(adjSt.posTop) + " / x " + Math.round(adjSt.posX));
                }
            }
            adjSt.lastH = h;
        }catch(e){}



        // ★ 消息框独立摆放：尺寸由**行数自己算**并显式设定（不依赖布局时序，第一帧就正确），
        //   上沿紧贴头像窗下沿 → 框自由伸缩，头像完全不受影响。
        try{
            if(adjBoxRoot != null && adjSt.text.length > 0){
                let lines = 1;
                for(let q = 0; q < adjSt.text.length; q++){
                    if(adjSt.text.substring(q, q + 1) == "\n") lines++;
                }
                let needH = lines * ADJ_LINE_H + 12;
                try{
                    const ph = adjText.getPrefHeight();          // Label 自己量（宽度已定）
                    if(ph > 4 && ph < needH * 2) needH = ph + 12;
                }catch(e){}
                const needW = 300;
                if(Math.abs(adjBoxRoot.getHeight() - needH) > 0.5 || Math.abs(adjBoxRoot.getWidth() - needW) > 0.5){
                    adjBoxRoot.setSize(needW, needH);
                }
                try{ adjBoxRoot.validate(); }catch(e){}
                let bx = adjSt.posX + (ADJ_WIN_W - needW) / 2;      // 相对头像水平居中
                try{
                    let sw = 1280;
                    try{ sw = Core.graphics.getWidth(); }catch(e){}
                    bx = Mathf.clamp(bx, 0, Math.max(0, sw - needW));   // 别把框推出屏幕
                }catch(e){}
                const by = (adjSt.posTop - ADJ_WIN_H) - needH - ADJ_GAP;   // 头像窗底边下方
                if(Math.abs(adjBoxRoot.x - bx) > 0.5 || Math.abs(adjBoxRoot.y - by) > 0.5){
                    adjBoxRoot.setPosition(Math.round(bx), Math.round(by));
                }
            }
        }catch(e){}

        // 开场白
        if(adjSt.introIndex < ADJ_INTRO.length && !adjSt.typing && adjSt.text.length == 0){
            const m = ADJ_INTRO[adjSt.introIndex++];
            adjSay(String(m[0]).replace("{0}", adjPlayerName()), m[1], m[2]);
            return;
        }

        // 打字机
        if(adjSt.typing){
            // 纯函数：已显示的可见字符数只由经过的 tick 决定 → 单调递增、可重复、不会错位
            const k = Math.floor((now - adjSt.startTime) * ADJ_CPT);
            const shown = Math.max(0, Math.min(k, adjSt.plain));
            if(shown != adjSt.shown){
                adjSt.shown = shown;
                try{ adjText.setText(adjTextAt(shown)); }catch(e){}

                // 打字音（节流；逻辑版每字 playsound @sfx-uiChat 0.3 ...）
                if(shown % 2 == 0 && now - adjTickAt > 0.05 * TPS){
                    adjTickAt = now;
                    try{ Sounds.uiChat.play(0.22, 1.7, 0); }catch(e){ try{ Sounds.uiChat.play(); }catch(e2){} }
                }
            }
            if(adjSt.shown >= adjSt.plain){
                adjSt.typing = false;
                adjHoldStart(adjSt.hold / TPS);      // 停留时长交给引擎定时器
                print("副官打字机：打完 " + adjSt.shown + "/" + adjSt.plain);
            }
            return;
        }

        // 停留到点 → 收起
        if(false){   // 收起已改由 Timer.schedule 负责（见 adjHoldStart）
            adjHide();
            return;
        }

        // 空闲时随机闲聊
        if(adjSt.text.length == 0 && now >= adjSt.idleAt && adjSt.introIndex >= ADJ_INTRO.length){
            adjSt.idleAt = now + (6 + Math.random() * 6) * TPS;
            if(Math.random() < 0.75) adjRandomLine();
        }
    }

    // ======================== HUD 面板 ========================

    function panelVisible(){
        try{
            return Vars.ui != null && Vars.ui.hudfrag != null && Vars.ui.hudfrag.shown;
        }catch(e){
            return false;
        }
    }

    function statusText(){
        if(!inGame()) return "[gray]不在游戏中";
        return "波次 " + Vars.state.wave + "  我 " + countUnits(true) + "  敌 " + countUnits(false)
            + "  建筑 " + Groups.build.size + "  " + Core.graphics.getFramesPerSecond() + "fps";
    }

    function onOff(v){
        return v ? "[green]开[]" : "[gray]关[]";
    }

    function rebuild(){
        if(contentTable == null) return;
        try{
            contentTable.clearChildren();
            contentTable.defaults().pad(2);

            let sub = null;

            // 单位
            sub = contentTable.table(Styles.black3).growX().get();
            sub.add("[lightgray]单位").left().padLeft(4).width(40);
            sub.button("◀", Styles.flatt, () => cycleUnit(-1)).size(30, 30);
            sub.add(unitName()).left().padLeft(4).growX();
            sub.button("▶", Styles.flatt, () => cycleUnit(1)).size(30, 30);
            contentTable.row();

            // 生成
            sub = contentTable.table(Styles.black3).growX().get();
            sub.button("生成 x1", Styles.flatt, () => spawnAdj(unitName(), 1)).height(30).growX();
            sub.button("x5", Styles.flatt, () => spawnAdj(unitName(), 5)).height(30).width(48);
            sub.button("x20", Styles.flatt, () => spawnAdj(unitName(), 20)).height(30).width(54);
            contentTable.row();

            // 战场
            sub = contentTable.table(Styles.black3).growX().get();
            sub.button("修理/治疗", Styles.flatt, () => healArea()).height(30).growX();
            sub.button("清除敌人", Styles.flatt, () => killEnemies()).height(30).growX();
            sub.button("下一波", Styles.flatt, () => runWave()).height(30).growX();
            contentTable.row();

            // 开关
            sub = contentTable.table(Styles.black3).growX().get();
            sub.button("自动副官 " + onOff(st.auto), Styles.flatt, () => { setAuto(null); rebuild(); }).height(30).growX();
            sub.button("日志 " + onOff(st.log), Styles.flatt, () => { setLog(null); rebuild(); }).height(30).growX();
            contentTable.row();

            sub = contentTable.table(Styles.black3).growX().get();
            const cheatOn = inGame() && Vars.state.rules.infiniteResources;
            sub.button("沙盒作弊 " + onOff(cheatOn), Styles.flatt, () => { toggleCheat(null); rebuild(); }).height(30).growX();
            const wavesOn = inGame() && Vars.state.rules.waves;
            sub.button("波次 " + onOff(wavesOn), Styles.flatt, () => { setWaves(null); rebuild(); }).height(30).growX();
            sub.button("补料", Styles.flatt, () => feedCore()).height(30).width(56);
            contentTable.row();

            // 副官通讯窗（复刻逻辑版副官）
            sub = contentTable.table(Styles.black3).growX().get();
            sub.button("副官窗 " + onOff(adjSt.open), Styles.flatt, () => { adjToggle(null); rebuild(); }).height(30).growX();
            sub.button("说一句", Styles.flatt, () => adjRandomLine()).height(30).width(70);
            sub.button("打字机自检", Styles.flatt, () => adjSay("打字机自检：一二三四五六七八九十 ABCDEFG 0123456789。若出现重复或乱序字符，请截图。", "working", 12)).height(30).growX();
            contentTable.row();

            // 物品
            sub = contentTable.table(Styles.black3).growX().get();
            sub.add("[lightgray]物品").left().padLeft(4).width(40);
            sub.button("◀", Styles.flatt, () => cycleItem(-1)).size(30, 30);
            sub.add(itemName()).left().padLeft(4).growX();
            sub.button("▶", Styles.flatt, () => cycleItem(1)).size(30, 30);
            sub.button("给1000", Styles.flatt, () => giveItem(itemName(), 1000)).height(30).width(70);
            contentTable.row();

            // 状态（动态标签，自动刷新）
            sub = contentTable.table(Styles.grayPanel).growX().get();
            sub.label(() => statusText()).left().padLeft(4);
            contentTable.row();

        }catch(e){
            print("副官调试插件：面板构建失败 → " + e);
        }
    }

    // ---- 拖动：照 arc.scene.ui.Dialog 的官方算法 ----
    // 关键：touchDragged 里用 target.x/target.y（Element 的字段）重算**绝对位置**，
    // 而不是 moveBy(增量)——元素跟着动，局部坐标也在变，moveBy 会重复累加。
    function makeDraggable(handle, target, onEnd){
        let dragging = false, startX = 0, startY = 0;

        // 用 JavaAdapter（游戏 global.js 的 extend() 内部就是这么干的）而不是 new Class(){} 语法：
        // 这样脚本仍是合法 JS，能被外部工具做语法校验。
        const listener = JavaAdapter(Packages.arc.scene.event.InputListener, {
            touchDown: function(event, x, y, pointer, button){
                if(button != Packages.arc.input.KeyCode.mouseLeft) return false;
                dragging = true;
                startX = x;
                startY = y;
                return true;
            },
            touchUp: function(event, x, y, pointer, button){
                if(dragging && onEnd != null) onEnd();
                dragging = false;
            },
            touchDragged: function(event, x, y, pointer){
                if(!dragging) return;
                // 拖动只更新**锚点**（不是直接和"每帧摆放"抢窗口坐标），所以纵向也能自由拖
                const nx = Math.round(target.x + (x - startX));
                const ny = Math.round(target.y + (y - startY));
                adjSt.posX = nx;
                adjSt.posTop = ny + target.getHeight();
                target.setPosition(nx, ny);
            }
        });

        handle.addListener(listener);
    }

    // （v1.7：调试面板改为「设置」里的一页，面板位置/夹边相关函数已删除）

    // 调试项不再做成 HUD 浮窗，改为**挂进「设置」里的一页**。
    // SettingsMenuDialog 的 categories 只做 append、显示时不清空，所以启动时加一次就够。
    function injectPanel(){
        try{
            Vars.ui.settings.addCategory("副官调试", (t) => {
                contentTable = t.table().growX().get();
                rebuild();
            });
            print("副官调试插件：已在「设置」中添加「副官调试」页");
        }catch(e){
            print("副官调试插件：添加设置页失败 → " + e);
        }
    }

    // （v1.7：面板不再浮动，自愈检查已删除）

    // ======================== 单机控制台 API ========================

    function publishApi(){
        const api = (text) => runCommand(text);

        api.help   = () => runCommand("help");
        api.spawn  = (unit, amount) => spawnAdj(unit == null ? DEFAULT_UNIT : String(unit), amount == null ? 1 : amount);
        api.heal   = () => runCommand("heal");
        api.give   = (item, amount) => giveItem(String(item), amount);
        api.kill   = () => runCommand("kill");
        api.wave   = () => runCommand("wave");
        api.waves  = (v) => setWaves(v);
        api.auto   = (v) => setAuto(v);
        api.log    = (v) => setLog(v);
        api.cheat  = (v) => toggleCheat(v);
        api.settings = () => { Vars.ui.settings.show(); return "已打开设置（副官调试页）"; };
        api.resetPos = () => {

            try{
                Core.settings.put("adjutant-avatar-x", -1);
                Core.settings.put("adjutant-avatar-y", -1);
            }catch(e){}
            if(adjWindow != null){
                let sw = 1280, sh = 720;
                try{ sw = Core.graphics.getWidth(); sh = Core.graphics.getHeight(); }catch(e){}
                adjSt.posX = Math.round(sw * 0.6);
                adjSt.posTop = Math.round(sh * 0.7);
            }
            return "面板与副官窗位置已复位";
        };
        api.report = () => runCommand("report");
        api.avatar = (v) => adjToggle(v);                       // 开关副官窗
        api.line   = (t) => { adjSay(String(t == null ? "我在、指挥官。" : t), "normal", 6); return "已播报"; };
        api.lines  = () => { adjRandomLine(); return "随机台词"; };
        api.type   = (t) => { adjSay(String(t == null ? "测试" : t), "normal", 8); return "打字机开始"; };

        // scope 从 JS 看是普通全局对象（没有 Java 的 put 方法，日志里就是这么失败的），
        // 所以优先用 rhino 的静态方法写入，再依次退化为属性赋值 / Java put。
        let sc = null;
        try{ sc = Vars.mods.getScripts().scope; }catch(e){}
        if(sc == null){
            print("副官调试插件：拿不到脚本 scope，控制台 API 未发布（其余功能正常）");
            return false;
        }

        const ways = [
            () => Packages.rhino.ScriptableObject.putProperty(sc, API_NAME, api),
            () => { sc[API_NAME] = api; },
            () => { sc.put(API_NAME, sc, api); }
        ];
        for(let i = 0; i < ways.length; i++){
            try{
                ways[i]();
                print("副官调试插件：控制台 API 已发布（方式 " + (i + 1) + "）→ 控制台输入 " + API_NAME + ".help()");
                return true;
            }catch(e){
                print("副官调试插件：发布方式 " + (i + 1) + " 失败 → " + e);
            }
        }
        return false;
    }

    // ======================== 联机聊天命令 ========================

    let lastCmdText = "";
    let lastCmdTime = -100;

    function onPlayerChat(e){
        if(headless() || e == null || e.message == null) return;
        if(Vars.net.client()) return;                 // 只在权威侧执行

        const text = String(e.message).trim();

        let body = null;
        if(text.indexOf(CMD) == 0){
            body = text.substring(CMD.length);
        }else if(text.indexOf(CMD_ALT) == 0){
            body = text.substring(CMD_ALT.length);
        }
        if(body == null) return;

        if(text == lastCmdText && Time.time - lastCmdTime < 0.25) return;   // 去重（单机/主机侧会双发）
        lastCmdText = text;
        lastCmdTime = Time.time;

        runCommand(body);
    }

    function onWave(e){
        if(!st.log || !inGame()) return;
        say("[lightgray][副官] 第 [white]" + Vars.state.wave + "[] 波开始");
    }

    function onBlockDestroy(e){
        if(!st.log || !inGame() || e == null || e.tile == null) return;
        const b = e.tile.build;
        if(b != null && b.team == myTeam()){          // b.team 是字段
            say("[lightgray][副官] 建筑被摧毁：[white]" + b.block.localizedName
                + "[] @ " + Mathf.round(b.x / 8) + "," + Mathf.round(b.y / 8));
        }
    }

    // ======================== 主循环 ========================

    function onUpdate(){
        if(headless() || Vars.state == null || !Vars.state.isGame()) return;

        st.tick++;
        adjUpdate();          // 副官窗：打字机 / 眨眼 / 闲聊 / 淡入

        if(KEY_ADJ != null && Core.input.keyTap(KEY_ADJ)){
            adjToggle(null);
            toast("[accent]副官窗：" + (adjSt.open ? "开" : "关"));
        }

        if(KEY_PANEL != null && Core.input.keyTap(KEY_PANEL)){
            try{ Vars.ui.settings.show(); }catch(e){}
        }

        if(KEY_SPAWN != null && Core.input.keyTap(KEY_SPAWN) && inGame()){
            spawnAdj(unitName(), 1);
        }

        if(KEY_KILL != null && Core.input.keyTap(KEY_KILL) && inGame()){
            toast("[accent]清除了 " + killEnemies() + " 个敌方单位");
        }

        if(KEY_AUTO != null && Core.input.keyTap(KEY_AUTO)) setAuto(null);
        if(KEY_LOG  != null && Core.input.keyTap(KEY_LOG))  setLog(null);

        if(!st.auto || !inGame()) return;

        if(st.tick % HEAL_EVERY == 0) healArea();
        if(st.tick % FEED_EVERY == 0) feedCore();

        const u = Vars.player.unit();
        if(u != null && u.health < u.maxHealth) u.heal(u.maxHealth);   // 字段
    }

    // ======================== 启动 ========================

    function onClientLoad(e){
        try{
            injectPanel();
            adjBuild();

        }catch(err){
            print("副官调试插件：注入面板失败 → " + err);
        }

        if(Vars.net.active()){
            say("[accent]副官调试插件已加载[] —— 「副官调试面板」拖标题可移动；联机聊天栏 " + CMD + " help");
        }else{
            say("[accent]副官调试插件已加载[] —— 「副官调试面板」直接点（拖标题移动 / F6 折叠）；控制台可用 " + API_NAME + ".help()");
        }
    }

    // ---- 注册（每步单独 try，避免一处失败拖垮整体）----
    try{
        publishApi();
    }catch(e){
        print("副官调试插件：publishApi 异常 → " + e);
    }

    try{
        Events.on(PlayerChatEvent, onPlayerChat);
        Events.on(WaveEvent, onWave);
        Events.on(BlockDestroyEvent, onBlockDestroy);
        Events.on(ClientLoadEvent, onClientLoad);
        Events.on(WorldLoadEvent, (e) => adjClamp());
        Events.on(ResizeEvent, (e) => adjClamp());
        Events.run(Trigger.update, onUpdate);
        print("副官调试插件：事件已注册，加载完成");
    }catch(e){
        print("副官调试插件：注册事件失败 → " + e);
    }
}

// 最外层兜底：无论如何都要在日志里留下痕迹
try{
    __adjutantMain();
}catch(e){
    print("副官调试插件：脚本初始化失败 → " + e);
}
