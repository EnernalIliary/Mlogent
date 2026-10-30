// ============================================================================
//  Mlog辅助 (MlogAuxiliary) —— scripts/main.js   v0.1  (P1: API 接入 + 写入通道)
//
//  玩家不写 mlog。选中处理器 → 选一个意图模板 → 本地 sidecar (tools/logicd.py)
//  把意图变成代码并跑仓库那套静态检查 → 面板列出 findings 与成本 → 确认写入。
//
//  写入不是"改 b.code 字段"，而是走原版 config 通道：
//      LogicBlock.config(byte[].class, (build, data) -> build.readCompressed(data, true))
//      （Mindustry-Source/core/src/mindustry/world/blocks/logic/LogicBlock.java:65-69）
//  载荷 = compress(code, links)：版本字节 1 + 代码 + 链接表 deflate（同文件 :137-166），
//  由 sidecar 用 tools/msch.py 的 build_logic_data() 生成 —— 和游戏自己的编码器同一格式。
//  于是单机与联机同一条路径，联机时服务端执行，不需要模组自己造同步。
//
//  ── 三条 Rhino 铁律（沿用 DP-CameraUnbind/METHOD.md 的实测结论）────────────
//   1) 按键常量写全限定名 Packages.arc.input.KeyCode.v
//   2) 控制台里只挂"顶层全局函数"（对象副本在控制台里是 undefined），所以末尾用
//      ScriptableObject.putProperty 把函数逐个挂到脚本作用域，并读回自检
//   3) 覆写/回调一律包 try/catch —— 顶层抛异常会让整个脚本静默中止
//
//  ── 本版边界（别假装它做了）─────────────────────────────────────────────
//   · UI 面板这一层**没有机器验证过**（无头模拟器里没有界面），协议层与写入通道
//     由 tests/logicd/run_logicd_tests.py 逐条验（含真 v160.7 处理器回读）。
//   · 游戏内快检已接（P2：scripts/quickcheck.js + rules.generated.js，五条单行判据），
//     但它只能“少报”：未赋值变量、成本 CFG、值域都在 sidecar 全量检查里。
//   · 撤销只在内存（P3）、没有 diff 预览（P3）、不接 LLM（P4）。
// ============================================================================

function __logicWriterMain(){
    "use strict";

    var MOD_VERSION = "0.10.0";
    var URL_KEY     = "mlogauxiliary-url";
    var DEFAULT_URL = "http://127.0.0.1:8765";
    var KEY_REGION  = ["f7"];      // F7：扫鼠标周围 10 格，列出链接候选
    var KEY_SELECT  = ["f3"];      // F3：按住 = 鼠标左键拉框（v0.5.0；F8 是游戏控制台，F9/F10 也被占）
var KEY_LIST    = ["f2"];      // F2：全图处理器清单（v0.7.0；剩下的空键只有 F2，F1/F5/F6/F8/F11/F12 是游戏自己的）
    var TIMEOUT_MS  = 4000;        // 连接超时：sidecar 是本机的，慢就是没开

    function log(msg){ print("[mai] " + msg); }

    // ---------------------------------------------------------- 设置界面
    // 设置 -> 「Mlog辅助」一栏。把调试信息全摊开（版本 / 构建 / 快检模块是否加载 /
    // 规则表条数 / sidecar 地址与可达性 / 数据目录 / mods 目录），省得再往控制台敲命令。
    // 所有游戏对象访问都套 try：无头环境里只是返回 false，不会炸。

    var sidecarOk = null;
    var panel = null;          // 模板块面板的单实例（v0.3.1 之前每开一次都新建一个，能叠起来）
    var settingsDone = false;
    var settingsErr = null;
    var settingsTries = 0;    // 见热键钩子：UI 晚于脚本建好时每 60 帧重试一次   // 注册失败时的原文，摊在诊断里，省得翻 last_log.txt

    function countKeys(o){
        var n = 0;
        if(o === null || o === undefined){ return 0; }
        for(var k in o){ if(Object.prototype.hasOwnProperty.call(o, k)){ n++; } }
        return n;
    }

    function dirText(fi){
        try{ return String(fi.absolutePath()); }
        catch(e){ return "?"; }
    }

    // 诊断数据只算一次，两个出口共用：设置页（键值两列对齐）与控制台/剪贴板（纯文本）。
    function diagParts(){
        var parts = [];
        parts.push({k: "版本", v: MOD_VERSION + "（游戏构建 " + gameBuild() + "）"});
        if(RULES === null){
            parts.push({k: "快检模块", v: "没加载（scripts/rules.generated.js 或 scripts/quickcheck.js 缺失）"});
        }else{
            parts.push({k: "快检模块", v: "已加载 · 指令 " + countKeys(RULES.instr) + " 条 / op 版本门 "
                       + countKeys(RULES.ops) + " 条 / 链接槽 " + countKeys(RULES.link) + " 条"});
        }
        parts.push({k: "sidecar", v: base + "（"
                    + (sidecarOk === null ? "未探测" : (sidecarOk ? "上次可达" : "上次不可达")) + "）"});
        parts.push({k: "数据目录", v: dirText(Vars.dataDirectory)});
        parts.push({k: "mods 目录", v: dirText(Vars.modDirectory)});
        parts.push({k: "设置分类", v: settingsDone ? "已注册（设置 → Mlog辅助）"
                    : (settingsErr === null ? "还没注册（Vars.ui 未就绪）" : "注册失败：" + settingsErr)});
        return parts;
    }

    function diagLines(){
        var parts = diagParts(), out = [];
        for(var i = 0; i < parts.length; i++){ out.push(parts[i].k + "：" + parts[i].v); }
        return out;
    }

    function diagText(){ return diagLines().join("\n"); }

    function probeSidecar(){
        httpJson("GET", "/health", null, function(code, text){
            sidecarOk = (code === 200);
            var body = String(text).substring(0, 200);
            log("health " + code + " " + body.substring(0, 100));
            var msg = sidecarOk ? ("可达：" + base + "\n" + body)
                                : ("不可达（" + code + "）：" + base + "\n先在本机跑：python tools/logicd.py");
            if(Vars.ui !== null){ Vars.ui.showText("Mlog辅助 · 连接", msg); }
        });
    }

    function isLogicBuild(b){
        try{ return b instanceof Packages.mindustry.world.blocks.logic.LogicBlock.LogicBuild; }
        catch(e){ return b !== null && b !== undefined && typeof b.code === "string"; }
    }

    function aimedBuild(){
        try{
            var t = Vars.world.tileWorld(Core.input.mouseWorldX(), Core.input.mouseWorldY());
            if(t === null || t.build === null){ return null; }
            return isLogicBuild(t.build) ? t.build : null;
        }catch(e){ return null; }
    }

    function quickAimed(){
        var b = aimedBuild();
        if(b === null || Vars.ui === null){
            if(Vars.ui !== null){
                Vars.ui.showText("Mlog辅助 · 快检", "先把鼠标指向一个处理器，再点这个按钮");
            }
            return;
        }
        var res = quickRun(String(b.code), b);
        var out = [quickSummary(res)];
        var ls = quickLines(res);
        for(var i = 0; i < ls.length && i < 12; i++){ out.push(ls[i]); }
        Vars.ui.showText("Mlog辅助 · 快检", out.join("\n"));
    }

    // 只碰 Table / Cell 的少数几个方法，方便在没有 UI 的环境里用假表 smoke。
    // ------------------------------------------------------------ 设置页
    // 只用真引擎复核过的 Table / Cell 形状（tests/mlogauxiliary/run_ui_smoke.py）：
    // 一律平铺成「键 值 + 按钮」，绝不 t.table(fn)（v160.7 Rhino 里重载歧义），
    // 也不 t.scrollPane(fn) / t.textarea(fn)（Table 上根本没有这两个方法）。
    // 原版风格的排版素材。分段标题 + 3px 强调线：BaseDialog 的标题就是这么画的
    //   titleTable.image(Tex.whiteui, Pal.accent).growX().height(3f)   BaseDialog.java:25
    // 行用灰底 Styles.grayPanel：原版 CheckSetting 用的同一个 Drawable（SettingsMenuDialog.java:825-827），
    // 行宽/内边距也照它（minWidth 500、padTop 7 -> 这里 540 / 5，给中文留点余量）。
    var LABEL_W = 128, VALUE_W = 390, ROW_W = 540;

    // 造一行灰底容器。Styles/Tex 在无头环境里可能还没初始化（静态字段要 atlas），
    // 所以一律 try：拿不到就用无背景的 Table，功能一样，只是不好看。
    function realRow(){
        try{ return new Packages.arc.scene.ui.layout.Table(Packages.mindustry.ui.Styles.grayPanel); }
        catch(e){ return new Packages.arc.scene.ui.layout.Table(); }
    }

    function section(t, title){
        t.add(title).color(Pal.accent).left().padTop(12).padBottom(2).row();
        try{
            t.image(Packages.mindustry.gen.Tex.whiteui, Pal.accent).growX().height(3).padTop(2).padBottom(4).row();
        }catch(e){
            t.add("").height(4).row();
        }
    }

    // mk 是行工厂：真机用 realRow()，selfTest 喂假表（无 UI 时真 Table 的 labelWrap 会 NPE）。
    function kv(t, k, v, mk){
        mk = mk || realRow;
        var row = mk();
        row.margin(8).left();
        if(k.length > 0){ row.add(k).width(LABEL_W).left().color(Pal.gray); }
        row.labelWrap(String(v)).width(VALUE_W).left();
        t.add(row).width(ROW_W).left().padTop(5).row();
    }

    function buttonRow(t, labels, handlers, mk){
        mk = mk || realRow;
        var row = mk();
        row.margin(6).left();
        for(var i = 0; i < labels.length; i++){
            row.button(labels[i], handlers[i]).height(38).padRight(6);
        }
        t.add(row).width(ROW_W).left().padTop(5).row();
    }

    function copyDiag(){
        try{
            Core.app.setClipboardText(diagText());
            if(Vars.ui !== null){ Vars.ui.showText("Mlog辅助 · 诊断", "诊断已复制到剪贴板。"); }
        }catch(e){ log("clipboard failed: " + e); }
    }

    function buildSettingsTable(t, mk){
        mk = mk || realRow;
        t.defaults().pad(3).left();
        kv(t, "", "Mlog辅助 " + MOD_VERSION + " · 说意图 -> 生成 mlog -> 预检 -> 写进处理器；写入走原版 config 通道，联机由服务端执行", mk);
        var parts = diagParts(), i;
        section(t, "运行环境");
        for(i = 0; i < parts.length; i++){
            if(parts[i].k !== "快检模块" && parts[i].k !== "sidecar"){ kv(t, parts[i].k, parts[i].v, mk); }
        }
        section(t, "本地快检（离线也能用）");
        for(i = 0; i < parts.length; i++){
            if(parts[i].k === "快检模块"){ kv(t, parts[i].k, parts[i].v, mk); }
        }
        section(t, "sidecar");
        var srow = mk();
        srow.margin(8).left();
        srow.add("地址").width(LABEL_W).left().color(Pal.gray);
        srow.field(base, function(v){
            var s = String(v);
            if(s.length > 0){ base = s; Core.settings.put(URL_KEY, s); log("sidecar = " + s); }
        }).width(300).left();
        t.add(srow).width(ROW_W).left().padTop(5).row();
        buttonRow(t, ["连接测试", "复制诊断"], [
            function(){ probeSidecar(); },
            function(){ copyDiag(); }
        ], mk);
        section(t, "快捷动作");
        buttonRow(t, ["AI 辅助编程", "模板面板"], [
            function(){ showAiPanel(); },
            function(){ openPanel(); }
        ], mk);
        buttonRow(t, ["快检鼠标下的处理器", "打印诊断"], [
            function(){ quickAimed(); },
            function(){ print("[mai] --- diag ---"); print(diagText()); }
        ], mk);
        buttonRow(t, ["重新注册分类", "审查状态"], [
            function(){ settingsDone = false; registerSettings(); },
            function(){ showReview(); }
        ], mk);
        buttonRow(t, ["撤销上次写入", "撤销快照"], [
            function(){ var r = undo(); if(Vars.ui !== null){ Vars.ui.showText("Mlog辅助 · 撤销", r); } },
            function(){ if(Vars.ui !== null){ Vars.ui.showText("Mlog辅助 · 撤销", undoInfo()); } }
        ], mk);
        section(t, "说明");
        kv(t, "", "F3 = AI 辅助编程（单格选中处理器 -> 描述意图 -> 生成 -> 预检 -> 写入）；原版逻辑编辑器底部会多一条「审查」状态栏。地址改完按回车保存。sidecar 不开也能进游戏，只是生成与模板不可用。", mk);
    }

    // 区域面板的布线（v0.6.0）：框选松手之后不再只弹一段纯文本，而是把「区域摘要 +
    // 每个处理器的链接候选」放进可滚动的对话框，并且每个处理器给一个「生成」按钮。
    // 这里只碰 table 的接口、不碰引擎类，所以能像设置页一样用假表在无 UI 环境里数行数。
    function buildRegionTable(t, snap, head, candText, pick){
        t.add(String(head)).left().row();
        t.labelWrap(String(candText)).left().growX().row();
        var ps = (snap && snap.processors) || [], i;
        if(ps.length === 0){
            t.add("（区域里没有处理器）").left().row();
        }
        for(i = 0; i < ps.length && i < 8; i++){
            (function(p){
                t.button("用 @" + p.x + "," + p.y + " 生成", function(){ pick(p.x, p.y); })
                 .width(240).left().row();
            })(ps[i]);
        }
        if(ps.length > 8){
            t.add("…还有 " + (ps.length - 8) + " 个处理器").left().row();
        }
        return t;
    }

    // ---------------------------------------------------------- 处理器清单（v0.7.0，F2）
    // 全图扫一遍处理器，按「问题多的排前面」列出来，点一行就跳过去并开 AI 面板。
    // 这三个只碰 table 的接口（不碰引擎类），所以 selfTest 能用假表数行数。
    function listHead(res){
        var errs = 0, warns = 0, i;
        for(i = 0; i < res.rows.length; i++){ errs += res.rows[i].err; warns += res.rows[i].warn; }
        return "全图 " + res.rows.length + " 个处理器，ERR " + errs + " / WARN " + warns
             + "，" + res.ms + " ms"
             + (res.api === true ? "" : "（快检不可用：只列清单，不判问题）");
    }

    function listRowLabel(r){
        var tail = "";
        if(r.err > 0){ tail += "  ERR " + r.err; }
        if(r.warn > 0){ tail += "  WARN " + r.warn; }
        if(r.err === 0 && r.warn === 0){ tail = "  干净"; }
        return "@" + r.x + "," + r.y + "  " + r.lines + " 行" + tail;
    }

    function buildListTable(t, res, head, pick){
        var rows = res.rows || [], max = 24, i;
        t.add(String(head)).left().row();
        if(rows.length === 0){ t.add("这张图上没有处理器").left().row(); }
        for(i = 0; i < rows.length && i < max; i++){
            (function(row){
                t.button(listRowLabel(row), function(){ pick(row.x, row.y); })
                 .width(320).left().row();
            })(rows[i]);
        }
        if(rows.length > max){ t.add("…还有 " + (rows.length - max) + " 个处理器").left().row(); }
        return t;
    }


    // 无 UI 环境下也能验证设置表格的布线：喂一张假表，数它被填了多少行/格。
    // 假表只实现真实页面用到的方法 —— 少实现一个，selfTest 立刻炸；
    // 同时把用到的名字记下来，供 run_ui_smoke 去真引擎里复核「有没有重载歧义」。
    // 假表：无 UI 环境里真 Table 的 labelWrap/field 会 NPE（scene.getStyle 需要 skin），
    // 所以 selfTest 用这个骨架跑一遍布线。它同时记下「用到了哪些 Table/Cell 方法」，
    // 测试再把这些名字拿到真引擎里逐个解析 —— 重载歧义只有在真引擎里才暴露得出来。
    // 一个对象同时当「表」和「格子」用：所有方法都返回自己，链式调用就一条路。
    function fakeTable(){
        var n = 0;
        var used = [];
        function hit(m){ used.push(m); }
        var node = {
            pad: function(){ hit("pad"); return node; },
            padTop: function(){ hit("padTop"); return node; },
            padBottom: function(){ hit("padBottom"); return node; },
            padRight: function(){ hit("padRight"); return node; },
            left: function(){ hit("left"); return node; },
            right: function(){ hit("right"); return node; },
            width: function(){ hit("width"); return node; },
            height: function(){ hit("height"); return node; },
            growX: function(){ hit("growX"); return node; },
            color: function(){ hit("color"); return node; },
            colspan: function(){ hit("colspan"); return node; },
            margin: function(){ hit("margin"); return node; },
            defaults: function(){ hit("defaults"); return node; },
            row: function(){ n++; hit("row"); return node; },
            clear: function(){ hit("clear"); return node; },
            add: function(){ n++; hit("add"); return node; },
            image: function(){ n++; hit("image"); return node; },
            label: function(){ n++; hit("label"); return node; },
            labelWrap: function(){ n++; hit("labelWrap"); return node; },
            field: function(v, f){ n++; hit("field"); return node; },
            button: function(s, f){ n++; hit("button"); return node; }
        };
        return {table: node, count: function(){ return n; },
                methods: function(){
                    var out = [], seen = {};
                    for(var i = 0; i < used.length; i++){
                        if(seen[used[i]] !== true){ seen[used[i]] = true; out.push(used[i]); }
                    }
                    out.sort();
                    return out.join(",");
                }};
    }

    function selfTest(){
        var ft = fakeTable();
        try{ buildSettingsTable(ft.table, function(){ return ft.table; }); }
        catch(e){ return "设置表格布线失败：" + e; }
        var rg = fakeTable();
        var fakeSnap = {processors: [{x: 1, y: 2, block: "micro-processor", links: []},
                                     {x: 5, y: 6, block: "micro-processor", links: []}]};
        try{ buildRegionTable(rg.table, fakeSnap, "区域 0,0 - 9,9 方块 4 处理器 2", "候选文本", function(){}); }
        catch(e){ return "区域表格布线失败：" + e; }
        var ls = fakeTable();
        var fakeList = {rows: [{x: 1, y: 2, lines: 4, err: 1, warn: 0, rules: "undefined-var"},
                               {x: 5, y: 6, lines: 2, err: 0, warn: 2, rules: "printflush-clears-buffer"}],
                        ms: 3, api: true};
        try{ buildListTable(ls.table, fakeList, listHead(fakeList), function(){}); }
        catch(e){ return "清单表格布线失败：" + e; }
        var fakeB = {tile: {x: 3, y: 4}, code: "set n 0\nprint n\nend", links: {size: 0}};
        var snapOk = "no";
        try{
            var back = parse(snapshotText(fakeB, "selftest"));
            snapOk = (back !== null && back.x === 3 && back.y === 4 && back.code === fakeB.code) ? "ok" : "bad";
        }catch(e){ snapOk = "fail"; }
        if(snapOk !== "ok"){ return "撤销快照序列化失败：" + snapOk; }
        return "设置表格可建，填了 " + ft.count() + " 行/格；区域表格 " + rg.count()
               + " 行；清单表格 " + ls.count() + " 行；诊断 " + diagLines().length
               + " 行；撤销快照 " + snapOk + "；用到的方法 " + ft.methods();
    }

    // 设置分类的图标用原版逻辑徽标（图标字体里的 glyph，和 @editor.worldprocessors 那个按钮同一个）。
    // 它由 Icon 的静态初始化从 Fonts.def 造出来，个别环境可能还是 null —— 那时退回无图标写法，
    // 不传 null 给 addCategory（String/Drawable 两个重载会挑不出来）。
    function categoryIcon(){
        try{
            var ic = Packages.mindustry.gen.Icon.logic;
            if(ic !== null && ic !== undefined){ return ic; }
        }catch(e){ log("logic icon unavailable: " + e); }
        return null;
    }

    function registerSettings(){
        if(settingsDone){ return true; }
        try{
            if(Vars.ui === null || Vars.ui.settings === null){ return false; }
            var icon = categoryIcon();
            if(icon !== null){
                Vars.ui.settings.addCategory("Mlog辅助", icon, function(t){ buildSettingsTable(t); });
            }else{
                Vars.ui.settings.addCategory("Mlog辅助", function(t){ buildSettingsTable(t); });
            }
            settingsDone = true;
            settingsErr = null;
            log("settings category registered");
            return true;
        }catch(e){
            settingsErr = String(e);
            log("settings category failed: " + e);
            return false;
        }
    }


    try{
        var Core    = Packages.arc.Core;
        var Events  = Packages.arc.Events;
        var Threads = Packages.arc.util.Threads;
        var Vars    = Packages.mindustry.Vars;
        var ET      = Packages.mindustry.game.EventType;
        var Groups  = Packages.mindustry.gen.Groups;
        var Pal     = Packages.mindustry.graphics.Pal;

        // P2 的两个模块。游戏只执行 scripts/main.js（Mods.loadScripts:809 只取 main.js，
        // 除非 scripts/ 下只有一个文件），其余文件必须 require 进来 —— Scripts.java:30-32
        // 给脚本作用域装了 CommonJS 模块提供器，模块里 module.exports 就是取到的东西。
        var QUICK = null, RULES = null;
        try{
            RULES = require("rules.generated");
            QUICK = require("quickcheck");
            log("quick check loaded: " + countKeys(RULES.instr) + " instruction(s)");
        }catch(e){
            log("quick check unavailable (" + e + ") -- 面板会少一行本地预检");
        }

        var base = String(Core.settings.getString(URL_KEY, DEFAULT_URL));
// 旧版本把地址存在 mlogauxiliary 之前的名字下（logicwriter-url）：存在就搬过来一次，读的人不用重配。
(function(){
    try{
        var legacy = Core.settings.getString("logic" + "writer-url", null);
        if(legacy !== null && legacy !== undefined && String(legacy).length > 0){
            if(String(Core.settings.getString(URL_KEY, "")).length === 0){
                Core.settings.put(URL_KEY, String(legacy)); base = String(legacy);
                log("migrated sidecar url from the old key: " + base);
            }
        }
    }catch(e){ log("legacy url migration skipped: " + e); }
})();
        var undoStack = [];        // P1：内存快照，重启即失效（P3 落盘）

        // ---------------------------------------------------------- 传输层
        // 不用 java.net.URL.openConnection()：它返回的是 sun.net.www.protocol.http.HttpURLConnection，
        // 属于 java.base 不 export 的 JDK 内部类；Rhino 按运行期类做成员绑定（MemberBox），于是
        // setRequestMethod / getResponseCode 这类被内部类覆写的方法一调就抛
        //   IllegalAccessException: class rhino.MemberBox cannot access class
        //   sun.net.www.protocol.http.HttpURLConnection (in module java.base)
        // —— v0.4.3 真机实测。这里退回 java.net.Socket：请求行与头自己写，响应读到 EOF
        // （请求带 Connection: close，python 的 BaseHTTPRequestHandler 是 HTTP/1.0，读完就关）。
        // 只用公开类（Socket / InputStreamReader / StringBuilder），不再碰 JDK 内部类型。
        
        // "http://host:port/path" -> {host, port, path}，host 缺省 127.0.0.1、port 缺省 8765。
        function endpoint(url){
            var s = String(url);
            var m = /^https?:\/\/([^\/:]+)(?::(\d+))?(\/[^\s]*)?$/.exec(s);
            if(m === null){ return {host: "127.0.0.1", port: 8765, path: "/"}; }
            var port = m[2] === undefined ? 80 : parseInt(m[2], 10);
            if(!(port > 0 && port < 65536)){ port = 8765; }
            return {host: m[1], port: port, path: m[3] === undefined ? "/" : m[3]};
        }
        
        function readAllStr(rd){
            var sb = new Packages.java.lang.StringBuilder();
            var cbuf = Packages.java.lang.reflect.Array.newInstance(Packages.java.lang.Character.TYPE, 8192);
            var n;
            while((n = rd.read(cbuf, 0, 8192)) !== -1){
                sb.append(new Packages.java.lang.String(cbuf, 0, n));
            }
            return String(sb.toString());
        }
        
        // 同步原生请求：返回 {code, text, head}。code = -1 表示连不上/超时（text 里是原因）。
        function httpRaw(method, url, body){
            var ep = endpoint(url);
            var sock = null;
            var res = {code: -1, text: "", head: ""};
            // 注意：这里刻意不用 try/finally —— 真 v160.7 的 Rhino 在 finally 里再嵌 try/catch
            // 时会抛 ArrayIndexOutOfBoundsException(arraycopy ...)，脚本整段静默不执行。
            // 收尾改成末尾独立的 try{ if(sock!==null){ sock.close(); } }catch(e1){}。
            try{
                sock = new Packages.java.net.Socket();
                sock.connect(new Packages.java.net.InetSocketAddress(ep.host, ep.port), TIMEOUT_MS);
                sock.setSoTimeout(TIMEOUT_MS * 4);
                var payload = (body === null || body === undefined) ? null
                    : new Packages.java.lang.String(String(body)).getBytes("UTF-8");
                var head = method + " " + ep.path + " HTTP/1.1\r\n"
                         + "Host: " + ep.host + ":" + ep.port + "\r\n"
                         + "Connection: close\r\n"
                         + "Accept: application/json\r\n";
                if(payload !== null){
                    head += "Content-Type: application/json\r\n"
                          + "Content-Length: " + payload.length + "\r\n";
                }
                head += "\r\n";
                var os = sock.getOutputStream();
                os.write(new Packages.java.lang.String(head).getBytes("UTF-8"));
                if(payload !== null){ os.write(payload); }
                os.flush();
        
                var rd = new Packages.java.io.InputStreamReader(sock.getInputStream(), "UTF-8");
                var raw = readAllStr(rd);
                try{ rd.close(); }catch(e0){}
                var idx = raw.indexOf("\r\n\r\n"), sepLen = 4;
                if(idx < 0){ idx = raw.indexOf("\n\n"); sepLen = 2; }
                var headPart = idx < 0 ? raw : raw.substring(0, idx);
                var textPart = idx < 0 ? "" : raw.substring(idx + sepLen);
                var code = -1;
                // 这里原本写 /^HTTP\/1\.[01] (\d{3})/ —— 真 v160.7 的 Rhino 编译这一条正则时
                // 直接抛 IllegalStateException: FAILED ASSERTION: invalid bytecode（正则字面量
                // 的 codegen bug，和脚本内容无关），整个 main.js 静默不执行。改成字符串比对。
                if(headPart.length >= 12 && headPart.substring(0, 5) === "HTTP/"){
                    var sp = headPart.indexOf(" ");
                    if(sp > 0){
                        var num = parseInt(headPart.substring(sp + 1, sp + 4), 10);
                        if(!isNaN(num)){ code = num; }
                    }
                }
                res = {code: code, text: textPart, head: headPart};
            }catch(e){
                res = {code: -1, text: String(e), head: ""};
            }
            try{ if(sock !== null){ sock.close(); } }catch(e1){}
            return res;
        }
        
        function httpJson(method, path, body, cb){
            Threads.daemon(function(){
                var code = -1, text = "";
                try{
                    var r = httpRaw(method, base + path, body);
                    code = r.code; text = r.text;
                }catch(e){
                    text = String(e);
                }
                var c = code, t = text;
                Core.app.post(function(){
                    try{ cb(c, t); }
                    catch(e2){ log("callback failed: " + e2); }
                });
            });
        }

        function parse(text){
            try{ return JSON.parse(text); }
            catch(e){ return null; }
        }

        function base64Bytes(b64){
            return Packages.java.util.Base64.getDecoder().decode(b64);
        }

        // ---------------------------------------------------------- 目标处理器
        // 鼠标指着哪个方块就是哪个处理器。比"遍历全图找处理器"更可预期，
        // 也不需要猜玩家想改哪一个。

        function targetBuild(){
            var mw = Core.input.mouseWorld();
            var tile = Vars.world.tileWorld(mw.x, mw.y);
            if(tile === null || tile.build === null){ return null; }
            var b = tile.build;
            // 鸭子类型而不是 instanceof 嵌套类：LogicBuild 是 LogicBlock 的静态内部类，
            // 名字里的 $ 在不同版本/混淆下不稳，而这两个字段是 LogicBuild 独有的。
            if(b.executor === undefined || b.code === undefined){ return null; }
            return b;
        }

        function describe(b){
            if(b === null){ return "鼠标下没有处理器"; }
            return "处理器 @ " + b.tile.x + "," + b.tile.y +
                   "  代码 " + String(b.code).split("\n").length + " 行" +
                   "  链接 " + b.links.size;
        }

        // ------------------------------------------------- 撤销快照（P5 第一刀：落盘）
        // 内存栈（undoStack）重启就没了，而「写错了想回滚」常常发生在第二天。
        // 每次写入前把「坐标 + 原代码 + 链接表 + 时间」写成
        // <dataDir>/mlogauxiliary/undo/<毫秒时间戳>_<x>_<y>.json —— 文件名可排序 = 时间顺序。
        // 回滚只还原代码（写入从不动链接表），走 build.updateCode()，联机下仍然只是本地生效。
        var UNDO_KEEP = 40;

        function undoRoot(){
            try{
                var fi = Vars.dataDirectory.child("mlogauxiliary").child("undo");
                if(!fi.exists()){ fi.mkdirs(); }
                return fi;
            }catch(e){ log("undo dir failed: " + e); return null; }
        }

        function linkPairs(b){
            var out = [], ls = b && b.links, i;
            try{
                for(i = 0; i < ls.size; i++){
                    var l = ls.get(i);
                    out.push({name: String(l.name), x: l.x, y: l.y,
                              block: (l.block && l.block.name) ? String(l.block.name) : ""});
                }
            }catch(e){ }
            return out;
        }

        function snapshotText(b, why){
            return JSON.stringify({schema: 1, x: b.tile.x, y: b.tile.y, at: Date.now(),
                                   why: String(why || ""),
                                   code: String(b.code), links: linkPairs(b)});
        }

        function undoFilesOf(root){
            var out = [], names = [], files, i;
            if(root === null){ return out; }
            try{
                files = root.list(".json");
                for(i = 0; i < files.length; i++){ names.push(String(files[i].name())); }
                names.sort();
                names.reverse();                       // newest first
                for(i = 0; i < names.length; i++){ out.push(root.child(names[i])); }
            }catch(e){ log("undo list failed: " + e); }
            return out;
        }

        function undoFiles(){ return undoFilesOf(undoRoot()); }

        function saveUndoTo(root, b, why){
            if(root === null){ return null; }
            var name = Date.now() + "_" + b.tile.x + "_" + b.tile.y + ".json";
            try{ root.child(name).writeString(snapshotText(b, why), false); }
            catch(e){ log("undo save failed: " + e); return null; }
            var files = undoFilesOf(root), i;
            for(i = UNDO_KEEP; i < files.length; i++){ try{ files[i].delete(); }catch(e2){ } }
            return name;
        }

        function saveUndo(b, why){ return saveUndoTo(undoRoot(), b, why); }

        // 从磁盘上最新的一份快照回滚。处理器已经不存在（拆了 / 换图了）就跳过，继续往前找。
        function undoFromDisk(){
            var files = undoFiles(), i;
            for(i = 0; i < files.length; i++){
                var f = files[i], name = String(f.name()), parts = name.split("_");
                if(parts.length < 3){ continue; }
                var x = parseInt(parts[1], 10), y = parseInt(parts[2], 10);
                if(isNaN(x) || isNaN(y)){ continue; }
                var snap = null;
                try{ snap = parse(f.readString("UTF-8")); }catch(e){ continue; }
                if(!snap || typeof snap.code !== "string"){ continue; }
                var b = null;
                try{ b = Vars.world.build(x, y); }catch(e2){ b = null; }
                if(b === null || b.code === undefined){ continue; }
                try{
                    b.updateCode(snap.code);
                    try{ f.delete(); }catch(e3){ }
                    return "已从磁盘快照回滚 @ " + x + "," + y + "（"
                         + snap.code.split("\n").length + " 行，快照 " + name + "）";
                }catch(e4){ return "回滚失败：" + e4; }
            }
            return "磁盘上没有可回滚的快照";
        }

        function undoInfo(){
            var root = undoRoot();
            return "撤销快照 " + undoFilesOf(root).length + " 份（目录 " + dirText(root) + "）";
        }

        // ---------------------------------------------------------- 写入
        // 唯一的写入口。三道闸：0 ERR、目标存在、载荷由 sidecar 生成（模组不自己拼代码）。

        function writeBuild(b, res){
            if(b === null){ return "没有目标处理器"; }
            if(!res || res.ok !== true){
                return "拒绝写入：静态检查有 ERR（" + ((res && res.errors) || "?") + " 条）";
            }
            if(!res.bytes_b64){ return "拒绝写入：sidecar 没有返回载荷"; }
            try{
                var snapName = saveUndo(b, "write:" + String(res.template || "code"));
                undoStack.push({b: b, code: String(b.code), snap: snapName});
                if(undoStack.length > 20){ undoStack.shift(); }
                b.configure(base64Bytes(res.bytes_b64));
                return "已写入 " + (res.template || "") + "（" + res.statements + " 条语句，"
                     + res.bytes_len + " 字节）";
            }catch(e){
                return "写入失败：" + e;
            }
        }

        function undo(){
            if(undoStack.length){
                var snap = undoStack.pop();
                try{
                    snap.b.updateCode(snap.code);      // P1：仅本地回滚，联机下请重进地图
                    if(snap.snap){ try{ undoRoot().child(snap.snap).delete(); }catch(e){ } }
                    return "已回滚到上一版代码（" + String(snap.code).split("\n").length + " 行）";
                }catch(e){ return "回滚失败：" + e; }
            }
            return undoFromDisk();
        }

        // ---------------------------------------------------------- 展示
        // 结果用原版文本对话框显示：这是最稳的一层（面板表格在无头环境里验不了）。

        function findingsText(res, b){
            var lines = [];
            lines.push(quickSummary(quickRun(res.code, b)));
            lines.push("模板：" + (res.template || "-") + "    语句：" + res.statements
                     + "    字节：" + res.bytes_len);
            lines.push("检查：" + (res.ok ? "通过（无 ERR）" : "有 ERR，禁止写入")
                     + "    ERR " + res.errors + " / WARN " + res.warns);
            lines.push("");
            lines.push("--- 代码 ---");
            lines.push(res.code);
            if(res.findings && res.findings.length){
                lines.push("");
                lines.push("--- findings ---");
                for(var i = 0; i < res.findings.length; i++){
                    var f = res.findings[i];
                    lines.push("L" + f.line + " " + f.sev + " [" + (f.rid || "-") + "] " + f.msg);
                }
            }
            if(res.cost){
                lines.push("");
                lines.push("--- 成本 ---");
                lines.push(res.cost);
            }
            return lines.join("\n");
        }

        function showResult(res, b){
            var text = findingsText(res, b);
            if(!res.ok){
                Vars.ui.showText("Mlog辅助 · 已拒绝", text);
                return;
            }
            Vars.ui.showConfirm("Mlog辅助 · 确认写入",
                text + "\n\n写入目标：" + describe(b),
                function(){
                    var msg = writeBuild(b, res);
                    log(msg);
                    Vars.ui.showText("Mlog辅助", msg);
                });
        }

        // ---------------------------------------------------------- 面板
        // 模板按钮来自 GET /capabilities —— 面板本身就是"协议通了"的证据。

        // ---------------------------------------------------------- 面板
        // 模板按钮来自 GET /capabilities —— 面板本身就是「协议通了」的证据。
        //
        // 关不掉的教训（v0.3.1 之前）：Arc 的 Dialog.addCloseButton() 是空实现
        //   Arc-Source/arc-core/src/arc/scene/ui/Dialog.java:453-455
        //   "no default implementation; should be implemented by subclasses"
        // 而 closeOnBack()（ESC / 返回键）也不会自动生效 —— Mindustry 的 BaseDialog
        // 是在构造里显式调（BaseDialog.java:70）。我们既不是 BaseDialog、又只调了
        // addCloseButton()，于是这个模态面板打开之后没有任何退出路径。现在三件一起做：
        // 自加「关闭」按钮 + closeOnBack()，并且只保留一个实例。

        function panelShown(){
            try{ return panel !== null && panel.isShown(); }catch(e){ return false; }
        }

        function togglePanel(){
            if(panelShown()){ try{ panel.hide(); }catch(e){ /* ignore */ } return; }
            openPanel();
        }

        function openPanel(){
            if(panelShown()){ try{ panel.toFront(); return; }catch(e){ /* ignore */ } }
            var b = targetBuild();
            var d = new Packages.arc.scene.ui.Dialog("Mlog辅助 v" + MOD_VERSION);
            d.cont.defaults().pad(4);
            d.cont.add("sidecar: " + base).left().row();
            d.cont.add(describe(b)).left().row();
            var qres = quickRun(b === null ? "" : String(b.code), b);
            d.cont.add(quickSummary(qres)).left().row();
            var qlines = quickLines(qres);
            var qmax = Math.min(qlines.length, 5);
            for(var qi = 0; qi < qmax; qi++){
                d.cont.add("  " + qlines[qi]).left().row();
            }
            if(qlines.length > qmax){ d.cont.add("  … 共 " + qlines.length + " 条（控制台 maiCheck() 看全）").left().row(); }
            d.cont.add("").row();
            // pane() 交回来的是 ScrollPane，不是 Table —— ScrollPane 上没有 add/clear/button。
            // 所以自己造一张 Table 交给 pane(Element) 托管，之后只往这张 Table 里加东西。
            // 这一条是 v0.4.0 点「生成」直接崩的根因（mlog-auxiliary/main.js:685，
            // TypeError: Cannot find function add in object ScrollPane）。
            var host = new Packages.arc.scene.ui.layout.Table();
            host.defaults().pad(2).left();
            host.add("正在读取模板…").row();
            try{
                d.cont.pane(host).height(300).width(520);
            }catch(e){
                log("pane() overload unavailable, falling back to a plain table: " + e);
                d.cont.add(host).growX();
            }
            d.buttons.defaults().pad(4);
            d.buttons.button("关闭", function(){ d.hide(); }).width(200);
            d.closeOnBack();
            d.show();
            panel = d;

            httpJson("GET", "/capabilities", null, function(code, text){
                var cap = parse(text);
                if(code !== 200 || !cap || cap.ok !== true){
                    host.clear();
                    host.add("离线：sidecar 没响应（" + code + "）").row();
                    host.add("先在本机跑：python tools/logicd.py").row();
                    return;
                }
                host.clear();
                host.add("模板（点击 = 生成 + 预检）").row();
                for(var i = 0; i < cap.templates.length; i++){
                    (function(tmpl){
                        host.button(tmpl.title, function(){
                            d.hide();
                            compose(tmpl.id, {}, b);
                        }).width(500).row();
                    })(cap.templates[i]);
                }
                host.add("ipt 上限 " + cap.limits.ipt_max
                       + "，链接半径 " + cap.limits.link_range_tiles + " 格").row();
            });
        }

        // ------------------------------------------ 原版逻辑编辑器里的审查
        // LogicDialog 是 Vars.ui.logic 上的单例（UI.java:228 `logic = new LogicDialog()`），
        // 它的构造里 clearChildren() 之后只放了三样东西：add(canvas).grow() / row() /
        // add(buttons).growX()（LogicDialog.java:39-72）。所以最低侵入的接法是往它自己
        // 身上再补一行：不改原版源码、不碰 canvas，只在底部加一条「审查」状态栏，
        // 代码一变（canvas.save() 变了）就重算一次。
        // 无头环境里 Vars.ui 是 null（Vars.java:209/332），每次访问都套 try。

        var reviewHost = null, reviewBar = null, reviewLast = "", reviewFrame = 0, reviewRes = null;

        // LogicDialog.executor 是**包私有**字段（真 v160.7 反射实测：canvas 是 public，
        // executor / privileged / consumer / wasRows 全是包私有），而 Rhino 只按 public
        // 成员绑定 —— 写 L.executor 拿到的是 undefined，不是 null，于是 v0.4.6 及之前的
        // 审查栏永远认为「没有处理器」，把链接表当成空表喂给 quickcheck。
        // 唯一能读到它的路是反射：getDeclaredField + setAccessible（Mindustry 在
        // classpath 上，没有模块系统挡着，实测 setAccessible 可用）。
        var logicExecField = null, logicExecProbed = false;

        function logicExecutor(){
            try{
                var L = Vars.ui.logic;
                if(L === null || L === undefined){ return null; }
                if(!logicExecProbed){
                    logicExecProbed = true;
                    try{
                        var cls = Packages.java.lang.Class.forName("mindustry.logic.LogicDialog");
                        var f = cls.getDeclaredField("executor");
                        f.setAccessible(true);
                        logicExecField = f;
                    }catch(e){ log("LogicDialog.executor is not reachable: " + e); }
                }
                if(logicExecField === null){ return null; }
                var ex = logicExecField.get(L);
                return (ex === undefined) ? null : ex;
            }catch(e){ return null; }
        }

        function reviewTargets(){
            // LExecutor.build 是 public（v160.7 实测），所以拿到 executor 之后这一步直读即可。
            var ex = logicExecutor();
            if(ex === null){ return null; }
            try{
                var b = ex.build;
                return (b === undefined) ? null : b;
            }catch(e){ return null; }
        }

        function reviewCode(){
            try{ return String(Vars.ui.logic.canvas.save()); }catch(e){ return null; }
        }

        // 审查栏/详情里都要说清「链接表是数出来的还是不知道」——v0.4.6 的假 WARN 就是
        // 因为把「不知道」当成了「一个链接都没有」。
        function linkLine(res){
            var st = (res === null || res === undefined) ? null : res.stats;
            if(st === null || st === undefined){ return "链接 ?"; }
            if(st.linkKnown === true){ return "链接 " + st.linkCount; }
            return "链接 ?（读不到处理器）";
        }

        function reviewCount(res){
            var err = 0, warn = 0, info = 0, f = res.findings;
            for(var k = 0; k < f.length; k++){
                if(f[k].sev === "ERR"){ err++; } else if(f[k].sev === "WARN"){ warn++; } else { info++; }
            }
            return {err: err, warn: warn, info: info, total: f.length};
        }

        function refreshReview(force){
            if(reviewBar === null){ return; }
            var code = reviewCode();
            if(code === null){ return; }
            if(!force && code === reviewLast){ return; }
            reviewLast = code;
            var res = quickRun(code, reviewTargets());
            reviewRes = res;
            // 审查栏重画之后把行内箭头也同步一遍（箭头贴在原版画布上，见下面的「行内箭头」段）
            syncArrows(res, null, null);
            var c = reviewCount(res);
            reviewBar.clear();
            reviewBar.left();
            reviewBar.add("审查").padRight(8);
            if(c.total === 0){
                reviewBar.add("没有发现问题").color(Pal.accent).padRight(16);
            }else{
                if(c.err > 0){ reviewBar.add("ERR " + c.err).color(Pal.remove).padRight(8); }
                if(c.warn > 0){ reviewBar.add("WARN " + c.warn).color(Pal.lightOrange).padRight(8); }
                if(c.info > 0){ reviewBar.add("INFO " + c.info).padRight(8); }
            }
            reviewBar.add("语句 " + res.stats.statements + " · 线性 " + res.stats.linearCost
                          + " · ipt " + res.stats.ticksPerPass
                          + " · " + linkLine(res)).padRight(16);
            reviewBar.button("详情", function(){ showReview(); }).width(90);
            reviewBar.button("AI 辅助", function(){ showAiPanel(); }).width(120);
        }

        function reviewText(){
            // 控制台/诊断用的纯文本版审查（showReview 会弹对话框）
            var b = reviewTargets();
            var code = reviewCode();
            if(code === null && b !== null){ code = String(b.code); }
            var res = quickRun(code === null ? "" : code, b);
            if(res.missing){ return "本地快检不可用（quickcheck.js 没加载）"; }
            var out = [quickSummary(res)];
            var ls = quickLines(res);
            for(var i = 0; i < ls.length; i++){ out.push(ls[i]); }
            return out.join("\n");
        }

        function showReview(){
            var code = reviewCode();
            var res = reviewRes;
            if(code !== null){ res = quickRun(code, reviewTargets()); }
            if(res === null){ if(Vars.ui !== null){ Vars.ui.showText("Mlog辅助 · 审查", "没有可审查的处理器。"); } return; }
            var out = [quickSummary(res)];
            var ls = quickLines(res);
            for(var i = 0; i < ls.length; i++){ out.push(ls[i]); }
            if(Vars.ui !== null){ Vars.ui.showText("Mlog辅助 · 审查", out.join("\n")); }
        }

        // ------------------------------------------ 行内箭头（v0.4.7）
        // 用户要的交互：哪一行有问题就在那一行贴个箭头，点箭头看这一行的原因。
        //
        // 为什么不做「往原版行里插一个 Cell」：Arc 的 Table.cells 是私有字段
        // （arc/scene/ui/layout/Table.java:35），插不到 addressLabel 前面；追加到行尾
        // 又会被行内按钮挤位置。所以改成覆盖层：一个铺在 statements 父容器里的 Table，
        // 箭头是它的普通孩子（不是 cell），手动摆位、每帧跟着布局重算。
        //
        // 三个依据（真 v160.7 实测 / 源码）：
        //  * LCanvas.statements 是 public 字段（LCanvas.java:32），子元素按语句顺序排，
        //    每个 StatementElem 的第一行（表头）高 38（LCanvas.java:427-491）。
        //  * quickcheck 的 finding.line 是 1 起的语句序号（quickcheck.js:97），
        //    所以第 i 个孩子对应 line = i + 1。
        //  * 覆盖层用 Touchable.childrenOnly：空白处不拦鼠标（原版画布要能拖行、点按钮），
        //    只有箭头自己被命中（Group.hit 先测孩子，Element.hit 对非 enabled 返回 null）。
        var ARROW = 16;                       // 箭头边长（像素）
        var arrowHost = null, arrowParent = null, arrowRows = [], arrowByLine = {};
        var arrowDraw;                        // undefined = 还没找过，null = 这个环境没有图标

        function sevRank(sev){
            if(sev === "ERR"){ return 0; }
            if(sev === "WARN"){ return 1; }
            return 2;
        }

        function sevColor(sev){
            if(sev === "ERR"){ return Pal.remove; }
            if(sev === "WARN"){ return Pal.lightOrange; }
            return Pal.accent;
        }

        // 箭头图标：原版行内按钮用的是 Icon（v160.7 里 Icon 是「带静态 Drawable 字段的类」，
        // 不是 v159.3 那个 enum）。无头引擎没有图集，Icon.right 是 null —— 那时返回 null，
        // 审查栏照常工作，只是不画箭头。
        function arrowDrawable(){
            if(arrowDraw !== undefined){ return arrowDraw; }
            arrowDraw = null;
            try{
                var d = Packages.mindustry.gen.Icon.right;
                if(d !== null && d !== undefined){ arrowDraw = d; }
            }catch(e){ /* ignore */ }
            if(arrowDraw === null){ log("no Icon.right in this build -- review arrows stay off"); }
            return arrowDraw;
        }

        function reviewStatements(){
            try{
                var L = Vars.ui.logic;
                if(L === null || L === undefined){ return null; }
                var s = L.canvas.statements;      // canvas 是 public（v160.7 反射实测）
                return (s === undefined) ? null : s;
            }catch(e){ return null; }
        }

        function arrowHostFor(statements){
            var parent = null;
            try{ parent = statements.parent; }catch(e){ return null; }
            if(parent === null || parent === undefined){ return null; }
            if(arrowHost !== null && arrowParent === parent){ return arrowHost; }
            var host = new Packages.arc.scene.ui.layout.Table();
            host.setFillParent(true);
            host.touchable = Packages.arc.scene.event.Touchable.childrenOnly;
            try{ parent.addChild(host); }catch(e){ return null; }
            host.update(function(){ layoutArrows(); });
            arrowHost = host;
            arrowParent = parent;
            return host;
        }

        // 第 i 个孩子 = 第 i+1 条语句；纵向取表头行的中心（表头在行顶，高 38）。
        // statements 只给测试传（无头引擎没有真画布），真机由每帧 update 回调传空。
        function layoutArrows(statements){
            if(arrowHost === null || arrowRows.length === 0){ return; }
            if(statements === null || statements === undefined){ statements = reviewStatements(); }
            if(statements === null){ return; }
            for(var i = 0; i < arrowRows.length; i++){
                var r = arrowRows[i], e = r.elem, img = r.img;
                try{
                    if(e === null || e === undefined){ img.visible = false; continue; }
                    img.visible = true;
                    var x = statements.x + e.x - ARROW - 2;     // 优先放进行左侧的空白
                    if(x < 2){ x = statements.x + e.x + 2; }     // 没空白就压进行内左端
                    var y = statements.y + e.y + e.getHeight() - 19 - (ARROW / 2);
                    img.setPosition(x, y);
                }catch(err){ img.visible = false; }
            }
        }

        function showLineReview(line){
            var out = ["第 " + line + " 行"];
            var by = arrowByLine[line];
            if(by === undefined){
                out.push("（这一行现在没有问题了）");
            }else{
                for(var i = 0; i < by.items.length; i++){
                    var f = by.items[i];
                    out.push(f.sev + " [" + (f.rid || "-") + "] " + f.msg);
                }
            }
            print("[mai] " + out.join("\n"));
            if(Vars.ui !== null){ Vars.ui.showText("Mlog辅助 · 第 " + line + " 行", out.join("\n")); }
        }

        // Rhino 里 var 是函数作用域，循环里直接闭包会全部指向最后一个值 —— 用工厂函数。
        function tapLine(line){
            return function(){ showLineReview(line); };
        }

        // 测试用：把箭头的颜色翻译回严重度（比较 Color 对象，不依赖 toString 格式）
        function sevNameOf(img){
            try{
                if(img.color.equals(Pal.remove)){ return "ERR"; }
                if(img.color.equals(Pal.lightOrange)){ return "WARN"; }
                if(img.color.equals(Pal.accent)){ return "INFO"; }
            }catch(e){ /* ignore */ }
            return "?";
        }

        function clearArrows(){
            if(arrowHost !== null){ try{ arrowHost.clearChildren(); }catch(e){ /* ignore */ } }
            arrowRows = [];
        }

        // res.findings -> 每行一个箭头。statements / drawable 只给测试用，真机传 null。
        function syncArrows(res, statements, drawableOverride){
            if(statements === null || statements === undefined){ statements = reviewStatements(); }
            if(statements === null){
                clearArrows();
                arrowByLine = {};
                return 0;
            }
            var host = arrowHostFor(statements);
            if(host === null){ return 0; }
            var byLine = {}, lines = [], i;
            var f = (res === null || res === undefined || res.findings === undefined) ? [] : res.findings;
            for(i = 0; i < f.length; i++){
                var ln = f[i].line;
                if(byLine[ln] === undefined){ byLine[ln] = {sev: f[i].sev, items: []}; lines.push(ln); }
                byLine[ln].items.push(f[i]);
                if(sevRank(f[i].sev) < sevRank(byLine[ln].sev)){ byLine[ln].sev = f[i].sev; }
            }
            arrowByLine = byLine;
            clearArrows();
            var draw = (drawableOverride === null || drawableOverride === undefined) ? arrowDrawable() : drawableOverride;
            if(draw === null || draw === undefined || lines.length === 0){ return 0; }
            var kids = null;
            try{ kids = statements.getChildren(); }catch(e){ return 0; }
            for(i = 0; i < lines.length; i++){
                var line = lines[i], idx = line - 1;
                if(idx < 0 || idx >= kids.size){ continue; }
                var elem = kids.get(idx), img = null;
                try{ img = new Packages.arc.scene.ui.Image(draw); }catch(e){ continue; }
                try{ img.setSize(ARROW, ARROW); }catch(e){ /* ignore */ }
                try{ img.setColor(sevColor(byLine[line].sev)); }catch(e){ /* ignore */ }
                try{ img.touchable = Packages.arc.scene.event.Touchable.enabled; }catch(e){ /* ignore */ }
                try{ img.tapped(tapLine(line)); }catch(e){ /* ignore */ }
                try{ host.addChild(img); }catch(e){ continue; }
                arrowRows.push({elem: elem, img: img, line: line, items: byLine[line].items.length});
            }
            layoutArrows(statements);
            return arrowRows.length;
        }
        function injectReview(){
            try{
                var L = Vars.ui.logic;
                if(L === null || L === undefined || reviewHost === L){ return false; }
                var bar = new Packages.arc.scene.ui.layout.Table();
                bar.left();
                L.row();
                L.add(bar).growX().height(46).pad(6);
                reviewHost = L;
                reviewBar = bar;
                log("review bar injected into the vanilla logic editor");
                refreshReview(true);
                return true;
            }catch(e){ log("review inject failed: " + e); return false; }
        }

        // 每帧被调一次：面板没开时只做两次属性读，代价可忽略。
        function reviewTick(){
            try{
                if(Vars.ui === null || Vars.ui.logic === null || !Vars.ui.logic.isShown()){ return; }
                if(reviewHost !== Vars.ui.logic){ injectReview(); }
                reviewFrame++;
                if(reviewFrame % 30 === 0){ refreshReview(false); }
            }catch(e){ /* 每帧回调里绝不抛出去 */ }
        }

        // ------------------------------------------ AI 辅助编程（F3 单格选中）
        // 一句话 → sidecar POST /plan → 代码 + 预检 → 确认写入。
        // 现在是规则式意图路由（tools/logicd.py 的 INTENTS 表），模型的接入点只在
        // /plan 的实现里，模组这一侧不用改。

        var aiPanel = null;

        function aiShown(){
            try{ return aiPanel !== null && aiPanel.isShown(); }catch(e){ return false; }
        }

        // Link coordinates travel as absolute tile positions (LogicLink.x/y), but the
        // byte[] payload stores them relative to the processor
        // (LogicBlock.config -> readCompressed(data, true), LogicBlock.java:304-307).
        // Omitting the origin silently wrote a link table pointing at empty tiles.
        function originOf(b){
            try{
                if(b !== null && b !== undefined && b.tile){
                    return {x: b.tile.x, y: b.tile.y};
                }
            }catch(e){ }
            return null;
        }

        function plan(intent, b, cb){
            var req = {intent: String(intent), links: linkList(b), ipt: 2,
                       origin: originOf(b)};
            httpJson("POST", "/plan", JSON.stringify(req), function(code, text){
                var res = parse(text);
                if(code !== 200 || !res || res === null){
                    cb({ok: false, reason: "sidecar 返回 " + code + "：" + String(text).substring(0, 200)});
                    return;
                }
                cb(res);
            });
        }

        function renderPlan(out, res, b, d){
            out.clear();
            if(!res || res.ok !== true){
                out.add("没能生成：" + (res && res.reason ? res.reason : "sidecar 没给理由")).row();
                var cand = res && res.candidates ? res.candidates : (res && res.templates ? res.templates : null);
                if(cand !== null){
                    var names = [];
                    for(var i = 0; i < cand.length; i++){
                        names.push(cand[i].title ? String(cand[i].title) : String(cand[i].id));
                    }
                    out.add("可用模板：" + names.join(" / ")).row();
                }
                return;
            }
            out.add("模板 " + res.template + " —— " + res.reason).row();
            var c = reviewCount(res);
            out.add(c.total === 0 ? "预检：通过（0 条）"
                    : ("预检：ERR " + c.err + " / WARN " + c.warn + " / INFO " + c.info)).row();
            var ls = res.findings ? res.findings : [];
            for(var i2 = 0; i2 < ls.length && i2 < 6; i2++){
                out.add("  " + ls[i2].sev + " L" + ls[i2].line + " " + ls[i2].msg).row();
            }
            out.add("--- 代码（" + res.statements + " 条语句，" + res.bytes_len + " 字节）---").row();
            var code = String(res.code).split("\n");
            for(var k = 0; k < code.length && k < 40; k++){ out.add(code[k]).row(); }
            if(code.length > 40){ out.add("… 共 " + code.length + " 行").row(); }
            d.buttons.clearChildren();
            d.buttons.defaults().pad(4);
            if(c.err === 0){
                d.buttons.button("写入", function(){ writeBuild(b, res); d.hide(); }).width(140);
            }
            d.buttons.button("关闭", function(){ d.hide(); }).width(140);
        }

        // target 可选：区域面板里点「生成」时直接指定那个处理器，不必再把鼠标移过去。
        function showAiPanel(target){
            if(aiShown()){ try{ aiPanel.toFront(); return; }catch(e){ /* ignore */ } }
            var b = (target === undefined || target === null) ? targetBuild() : target;
            var d = new Packages.arc.scene.ui.Dialog("Mlog辅助 · AI 辅助编程 v" + MOD_VERSION);
            d.cont.defaults().pad(4).left();
            d.cont.add("目标：" + describe(b)).row();
            d.cont.add("描述这段逻辑要做什么，然后点「生成」：").padTop(6).row();
            var intent = "";
            d.cont.field("", function(v){ intent = String(v); }).width(560).row();
            d.cont.add("例：巡逻，遇到敌人就开火 / 容器里铜够 250 就打印 / 每 2 秒打印一次计数").row();
            // 同 openPanel：pane() 给的是 ScrollPane，必须自己造 Table 交给它托管。
            var host = new Packages.arc.scene.ui.layout.Table();
            host.defaults().pad(2).left();
            host.add("（还没生成）").row();
            try{
                d.cont.pane(host).height(300).width(600);
            }catch(e){
                log("pane() overload unavailable, falling back to a plain table: " + e);
                d.cont.add(host).growX();
            }
            d.buttons.defaults().pad(4);
            // v0.8.0：默认走作业队列（落盘 + 更严的门禁 + 可取消）。
            d.buttons.button("生成", function(){ startJob(b, host, d, intent); }).width(140);
            // 直接生成 = 旧的 /plan 路径：sidecar 没有 /jobs（老版本）时的退路。
            d.buttons.button("直接生成", function(){
                host.clear();
                host.add("正在请求 sidecar…").row();
                plan(intent, b, function(res){ renderPlan(host, res, b, d); });
            }).width(140);
            d.buttons.button("取消作业", function(){ hint(cancelJob()); }).width(120);
            d.buttons.button("关闭", function(){ d.hide(); }).width(140);
            d.closeOnBack();
            d.show();
            aiPanel = d;
        }

        // ---------------------------------------------------------- 作业队列（v0.8.0 / P4 第二刀）
        // AI 面板的「生成」不再直接 /plan，而是往 sidecar 的作业队列里投一个 job：
        // 作业会落盘、sidecar 崩了能续跑、过比分析器更严的门禁（link-name-not-bound
        // 从 WARN 提升成 ERR，见 tools/jobqueue.py 的 FATAL_RIDS）。
        // 游戏这边只做两件事：投递 + 每秒查一次状态；生成逻辑全在 sidecar。
        // 契约：docs/Mlog辅助-规划.md §4.1；端点：POST /jobs、GET /jobs?id=、DELETE /jobs?id=。
        var aiJob = null;                 // {id, b, desc, host, d, lastPoll, job}
        var JOB_POLL_MS = 1000;
        var JOB_TERMINAL = {done: 1, rejected: 1, failed: 1, cancelled: 1};

        function isJobTerminal(state){
            return JOB_TERMINAL[String(state)] === 1;
        }

        // job 的 snapshot 只是给 sidecar 存档/将来自由档用的世界事实；
        // 处理器周围 13×13 足够，太大了会把整张图的格子塞进请求里。
        function jobBody(b, desc){
            var snap = null;
            try{
                if(b !== null && b !== undefined && b.tile){
                    snap = regionSnapshot(b.tile.x - 6, b.tile.y - 6, b.tile.x + 6, b.tile.y + 6);
                }
            }catch(e){ snap = null; }
            if(snap === null){
                snap = {schema: 1, cells: 0, truncated: false, grid: [], processors: []};
            }
            return {job: {mode: "new", desc: String(desc), links: linkListOrNull(b), ipt: 2,
                          origin: originOf(b), snapshot: snap}};
        }

        function jobSubmit(b, desc, cb){
            httpJson("POST", "/jobs", JSON.stringify(jobBody(b, desc)), function(code, text){
                var res = parse(text);
                if(code !== 200 || res === null || res.ok !== true){
                    cb(null, jobWhy(code, text, res));
                    return;
                }
                cb(res, null);
            });
        }

        function jobGet(id, cb){
            httpJson("GET", "/jobs?id=" + String(id), null, function(code, text){
                var res = parse(text);
                if(code !== 200 || res === null || res.ok !== true || !res.job){
                    cb(null, jobWhy(code, text, res));
                    return;
                }
                cb(res.job, null);
            });
        }

        function jobCancel(id, cb){
            httpJson("DELETE", "/jobs?id=" + String(id), null, function(code, text){
                var res = parse(text);
                if(code !== 200 || res === null || res.ok !== true){
                    cb(null, jobWhy(code, text, res));
                    return;
                }
                cb(res.job || null, null);
            });
        }

        function jobSevCounts(job){
            var f = (job && job.findings) ? job.findings : [];
            var c = {err: 0, warn: 0, info: 0, total: f.length};
            for(var i = 0; i < f.length; i++){
                var s = String(f[i].sev);
                if(s === "ERR"){ c.err++; } else if(s === "WARN"){ c.warn++; } else { c.info++; }
            }
            return c;
        }

        // job -> /plan 那套渲染要的形状。writeBuild 只认 ok/bytes_b64/statements/bytes_len，
        // renderPlan 还要 findings/template/reason，所以这里一次补齐。
        function jobAsPlan(job){
            var c = jobSevCounts(job);
            return {ok: String(job.state) === "done",
                    template: job.template || "",
                    reason: job.explanation || "",
                    findings: job.findings || [],
                    code: job.code || "",
                    statements: job.statements || 0,
                    bytes_b64: job.bytes_b64 || "",
                    bytes_len: job.bytes_len || 0,
                    errors: c.err, warns: c.warn};
        }

        function jobProgressText(job){
            if(job === null || job === undefined){ return "作业：查不到状态"; }
            var st = String(job.state), a = job.attempts || 0, id = String(job.id || "?");
            var c = jobSevCounts(job);
            if(st === "queued"){ return "作业 " + id + "：排队中（第 " + a + " 次尝试）"; }
            if(st === "running"){ return "作业 " + id + "：生成中（第 " + a + " 次尝试）"; }
            if(st === "done"){
                return "作业 " + id + "：完成（" + (job.statements || 0) + " 条语句，"
                     + (job.bytes_len || 0) + " 字节，尝试 " + a + " 次）";
            }
            if(st === "rejected"){
                return "作业 " + id + "：被门禁拒绝（尝试 " + a + " 次，ERR " + c.err + " 条）";
            }
            if(st === "cancelled"){ return "作业 " + id + "：已取消"; }
            return "作业 " + id + "：" + st
                 + (job.explanation ? "（" + String(job.explanation) + "）" : "");
        }

        function renderJob(host, job, b, d){
            if(host === null || host === undefined || job === null || job === undefined){ return; }
            host.clear();
            host.add(jobProgressText(job)).row();
            var st = String(job.state);
            if(st === "done"){
                var res = jobAsPlan(job), c = jobSevCounts(job);
                host.add(c.err === 0 ? "预检：通过（0 条 ERR）" + (c.total ? "，另有 " + c.warn + " 条 WARN" : "")
                                     : ("预检：ERR " + c.err + " / WARN " + c.warn)).row();
                if(job.explanation){ host.add(String(job.explanation)).row(); }
                var ls = job.findings || [];
                for(var i = 0; i < ls.length && i < 6; i++){
                    host.add("  " + ls[i].sev + " L" + ls[i].line + " " + ls[i].msg).row();
                }
                host.add("--- 代码（" + (job.statements || 0) + " 条语句，" + (job.bytes_len || 0) + " 字节）---").row();
                var code = String(job.code || "").split("\n");
                for(var k = 0; k < code.length && k < 40; k++){ host.add(code[k]).row(); }
                if(code.length > 40){ host.add("… 共 " + code.length + " 行").row(); }
                if(d !== null && d !== undefined){
                    d.buttons.clearChildren();
                    d.buttons.defaults().pad(4);
                    d.buttons.button("写入", function(){ hint(writeBuild(b, res)); d.hide(); }).width(140);
                    d.buttons.button("关闭", function(){ d.hide(); }).width(140);
                }
                return;
            }
            if(st === "rejected" || st === "failed" || st === "cancelled"){
                var fs = job.findings || [];
                for(var i2 = 0; i2 < fs.length && i2 < 6; i2++){
                    host.add("  " + fs[i2].sev + " L" + fs[i2].line + " " + fs[i2].msg).row();
                }
                if(job.explanation){ host.add(String(job.explanation)).row(); }
                return;
            }
            host.add("（每 " + (JOB_POLL_MS / 1000) + " 秒查一次状态，可以先去干别的）").row();
        }

        // 每帧调一次：只有「有作业 + 面板还开着 + 到点了」才发请求。
        function jobTick(){
            if(aiJob === null){ return; }
            if(!aiShown()){ aiJob = null; return; }       // 面板关了就别轮询了
            var now = Packages.java.lang.System.currentTimeMillis();
            if(now - aiJob.lastPoll < JOB_POLL_MS){ return; }
            aiJob.lastPoll = now;
            var mine = aiJob;
            jobGet(mine.id, function(job, why){
                if(aiJob !== mine){ return; }             // 期间换了作业/取消了
                if(job === null){ return; }               // 网络抖一下：下次再查
                mine.job = job;
                try{ renderJob(mine.host, job, mine.b, mine.d); }
                catch(e){ log("renderJob failed: " + e); }
                if(isJobTerminal(job.state)){ aiJob = null; }
            });
        }

        function startJob(b, host, d, intent){
            if(b === null || b === undefined){ host.add("鼠标下没有处理器").row(); return "没有目标处理器"; }
            var desc = String(intent);
            if(desc.length === 0){ host.add("先写一句要做什么").row(); return "描述是空的"; }
            host.clear();
            host.add("正在投递作业…").row();
            jobSubmit(b, desc, function(res, why){
                if(res === null){ host.clear(); host.add("投递失败：" + why).row(); return; }
                aiJob = {id: String(res.id), b: b, desc: desc, host: host, d: d,
                         lastPoll: 0, job: res.job || null};
                try{ renderJob(host, res.job, b, d); }
                catch(e){ log("renderJob failed: " + e); }
            });
            return "已投递";
        }

        function cancelJob(){
            if(aiJob === null){ return "没有进行中的作业"; }
            var mine = aiJob;
            aiJob = null;
            jobCancel(mine.id, function(job, why){
                hint(why === null ? ("已取消作业 " + mine.id) : ("取消失败：" + why));
            });
            return "已请求取消 " + mine.id;
        }

        // 同步跑完一个作业：**只给控制台/自检用**（会阻塞当前线程）。
        // 游戏内 UI 走的是上面那条异步路径 —— 主线程 busy-wait 永远等不到 Core.app.post 的回调。
        function jobSync(b, desc, timeoutMs){
            var t0 = Packages.java.lang.System.currentTimeMillis();
            var limit = (timeoutMs > 0) ? timeoutMs : 20000;
            var r1 = httpRaw("POST", base + "/jobs", JSON.stringify(jobBody(b, desc)));
            var j1 = parse(r1.text);
            if(r1.code !== 200 || j1 === null || j1.ok !== true){
                return JSON.stringify({ok: false, code: r1.code, text: String(r1.text).substring(0, 300)});
            }
            var id = String(j1.id), job = j1.job || null, tries = 0;
            while(tries < 400){
                tries++;
                if(job !== null && isJobTerminal(job.state)){ break; }
                if(Packages.java.lang.System.currentTimeMillis() - t0 > limit){ break; }
                try{ Packages.java.lang.Thread.sleep(50); }catch(e0){ }
                var r2 = httpRaw("GET", base + "/jobs?id=" + id, null);
                var j2 = parse(r2.text);
                if(r2.code === 200 && j2 !== null && j2.ok === true && j2.job){ job = j2.job; }
            }
            if(job === null){ return JSON.stringify({ok: false, code: 0, text: "no job state"}); }
            return JSON.stringify(job);
        }

        // ---------------------------------------------------------- 区域面板（v0.6.0）
        // F3 松手之后：先落盘快照，再要 /region 的链接候选，最后开这个面板。
        // 面板里的「生成」按钮带着该处理器的引用直接开 AI 面板（showAiPanel(target)），
        // 省掉「先把鼠标移到那个处理器上」这一步。
        function buildAt(x, y){
            var t = Vars.world.tile(x, y);
            if(t === null || t === undefined){ return null; }
            var b = t.build;                    // 字段，不是方法（t.build() 会报错）
            if(b === null || b === undefined){ return null; }
            return b;
        }

        // v0.8.1：单格选中处理器 = 开 AI 面板（v0.9.0 起 F4 热键已删，只有这一条路）。
        function processorAt(x, y){
            var b = buildAt(x, y);
            return isProcessor(b) ? b : null;
        }

        function showRegionPanel(snap, head, candText){
            var d = new Packages.arc.scene.ui.Dialog("Mlog辅助 · 区域 v" + MOD_VERSION);
            d.cont.defaults().pad(4).left();
            // 同 showAiPanel：pane() 交回来的是 ScrollPane（没有 add），所以自己造 host 给它托管。
            var host = new Packages.arc.scene.ui.layout.Table();
            host.defaults().pad(2).left();
            buildRegionTable(host, snap, head, candText, function(x, y){
                var b = buildAt(x, y);
                if(b === null){ hint("@" + x + "," + y + " 上已经没有处理器了"); return; }
                try{ d.hide(); }catch(e){ }
                showAiPanel(b);
            });
            try{
                d.cont.pane(host).height(320).width(620);
            }catch(e){
                log("pane() overload unavailable in the region panel: " + e);
                d.cont.add(host).growX();
            }
            d.buttons.defaults().pad(4);
            d.buttons.button("复制快照 JSON", function(){
                try{ Core.app.setClipboardText(JSON.stringify(snap)); hint("快照 JSON 已复制"); }
                catch(e){ hint("复制失败：" + e); }
            }).width(180);
            d.buttons.button("关闭", function(){ d.hide(); }).width(140);
            d.closeOnBack();
            d.show();
            return d;
        }

        // ---------------------------------------------------------- 处理器清单：扫描 + 面板（v0.7.0）
        // 只读：复用本地快检（quickApi）与 linkNames，不动任何方块。
        // Groups.build 里既有处理器也有普通建筑，用 isProcessor() 的鸭子类型筛。
        function scanProcessors(){
            var rows = [], api = quickApi(), build = gameBuild();
            var t0 = Packages.java.lang.System.currentTimeMillis();
            try{
                Groups.build.each(function(g){
                    try{
                        if(!isProcessor(g)){ return; }
                        var src = String(g.code);
                        var row = {x: g.tile.x, y: g.tile.y,
                                   lines: src.length === 0 ? 0 : src.split("\n").length,
                                   err: 0, warn: 0, links: 0, rules: ""};
                        try{ row.links = g.links.size; }catch(e){ }
                        if(api !== null){
                            var res = api.q.check(api.r, src, linkNames(g), {build: build});
                            var seen = {};
                            for(var i = 0; i < res.findings.length; i++){
                                var f = res.findings[i];
                                if(f.sev === "ERR"){ row.err++; } else { row.warn++; }
                                var k = String(f.rid || "?");
                                if(seen[k] !== true){ seen[k] = true; row.rules += (row.rules === "" ? "" : ",") + k; }
                            }
                        }
                        rows.push(row);
                    }catch(e){ }
                });
            }catch(e){ }
            rows.sort(function(a, b){
                if(b.err !== a.err){ return b.err - a.err; }
                if(b.warn !== a.warn){ return b.warn - a.warn; }
                if(a.y !== b.y){ return a.y - b.y; }
                return a.x - b.x;
            });
            return {rows: rows, ms: Packages.java.lang.System.currentTimeMillis() - t0,
                    api: api !== null};
        }

        function jumpTo(x, y){
            try{ Core.camera.position.set(x * 8 + 4, y * 8 + 4); }catch(e){ log("camera jump failed: " + e); }
        }

        function listText(){
            var res = scanProcessors();
            var out = [listHead(res)];
            for(var i = 0; i < res.rows.length && i < 40; i++){
                out.push("  " + listRowLabel(res.rows[i]));
            }
            if(res.rows.length > 40){ out.push("  …还有 " + (res.rows.length - 40) + " 个"); }
            return out.join("\n");
        }

        function showListPanel(res){
            var d = new Packages.arc.scene.ui.Dialog("Mlog辅助 · 处理器清单 v" + MOD_VERSION);
            d.cont.defaults().pad(4).left();
            // 同 showRegionPanel：pane() 交回来的是 ScrollPane（没有 add），自己造 host 给它托管。
            var host = new Packages.arc.scene.ui.layout.Table();
            host.defaults().pad(2).left();
            buildListTable(host, res, listHead(res), function(x, y){
                jumpTo(x, y);
                var b = buildAt(x, y);
                try{ d.hide(); }catch(e){ }
                if(b === null){ hint("@" + x + "," + y + " 上已经没有处理器了"); return; }
                showAiPanel(b);
            });
            try{
                d.cont.pane(host).height(340).width(560);
            }catch(e){
                log("pane() overload unavailable in the list panel: " + e);
                d.cont.add(host).growX();
            }
            d.buttons.defaults().pad(4);
            d.buttons.button("复制清单", function(){
                try{ Core.app.setClipboardText(listText()); hint("处理器清单已复制"); }
                catch(e){ hint("复制失败：" + e); }
            }).width(160);
            d.buttons.button("关闭", function(){ d.hide(); }).width(120);
            d.closeOnBack();
            d.show();
            return d;
        }

        function openListPanel(){
            var res = scanProcessors();
            try{ showListPanel(res); }
            catch(e){
                log("list panel failed, falling back to text: " + e);
                popup("Mlog辅助 · 处理器清单", listText());
            }
            return res;
        }

        // ---------------------------------------------------------- 动作

        function linkList(b){
            var out = [];
            if(b === null){ return out; }
            for(var i = 0; i < b.links.size; i++){
                var l = b.links.get(i);
                out.push({name: String(l.name), x: l.x, y: l.y});
            }
            return out;
        }

        function compose(template, params, b){
            var body = JSON.stringify({template: template, params: params || {},
                                       links: linkList(b), ipt: 2, origin: originOf(b)});
            httpJson("POST", "/compose", body, function(code, text){
                var res = parse(text);
                if(code !== 200 || res === null){
                    Vars.ui.showText("Mlog辅助", "compose 失败（" + code + "）\n" + text);
                    return;
                }
                showResult(res, b);
            });
        }

        // 这里原本有个 ping() 用 busy-wait「同步」等 /health —— 在真引擎里永远拿不到结果
        // （回调走 Core.app.post 投递回主线程，而调用方就在主线程上）。探活请用 probeSidecar()。

        // ---------------------------------------------------------- 本地快检（P2）
        // scripts/quickcheck.js 与 scripts/rules.generated.js 由上面的 require 取到。
        // 边界：这里只回答“单行 + 一张表”能定的事，不重写 sidecar 的 41 条规则。

        function gameBuild(){
            try{
                var v = Packages.mindustry.core.Version.build;
                return (v > 0) ? v : 0;      // 自定义构建是 -1，当作未知
            }catch(e){ return 0; }
        }

        function quickApi(){
            if(QUICK === null || RULES === null){ return null; }
            return {q: QUICK, r: RULES};
        }

        // 返回 null 表示「不知道这个处理器的链接表」，返回 [] 表示「确实没有链接」。
        // 这两个含义在 quickcheck 里分开用（stats.linkKnown）：把「不知道」当成「没有」
        // 会让每一行链接槽里的名字都报 link-name-not-bound（v0.4.6 的假 WARN）。
        // 返回 null 表示「不知道这个处理器的链接表」，返回 [] 表示「确实没有链接」。
        // jobqueue 靠这个区分门禁口径：[] 是权威空表（幻觉链接名必须拦），null 是不知道（不判）。
        function linkListOrNull(b){
            if(b === null || b === undefined){ return null; }
            try{
                var out = [];
                for(var i = 0; i < b.links.size; i++){
                    var l = b.links.get(i);
                    out.push({name: String(l.name), x: l.x, y: l.y});
                }
                return out;
            }catch(e){ return null; }
        }
        function linkNames(b){
            if(b === null || b === undefined){ return null; }
            var out = [];
            try{
                for(var i = 0; i < b.links.size; i++){ out.push(String(b.links.get(i).name)); }
            }catch(e){ return null; }
            return out;
        }

        function quickRun(code, b){
            var api = quickApi();
            if(api === null){ return {missing: true, findings: [], stats: null}; }
            var res = api.q.check(api.r, String(code || ""), linkNames(b), {build: gameBuild()});
            res.missing = false;
            return res;
        }

        function quickSummary(res){
            if(res.missing){ return "本地快检：不可用（quickcheck.js 没加载）"; }
            var err = 0, warn = 0, i;
            for(i = 0; i < res.findings.length; i++){
                if(res.findings[i].sev === "ERR"){ err++; } else { warn++; }
            }
            var st = res.stats;
            return "本地快检：" + (err ? ("ERR " + err) : "无 ERR")
                 + " / WARN " + warn
                 + "    语句 " + st.statements
                 + "    版本地板 build " + st.floor
                 + "    " + linkLine(res)
                 + (st.truncates ? "    ⚠ 超过 1000 条会被截断" : "")
                 + (st.linkKnown === false
                    ? "\n（链接表未知：读不到 LogicDialog.executor，链接槽判据这一遍整段跳过 —— 宁可少报，不报假 WARN）"
                    : "");
        }

        function quickLines(res){
            var out = [];
            for(var i = 0; i < res.findings.length; i++){
                var f = res.findings[i];
                out.push("L" + f.line + " " + f.sev + " [" + (f.rid || "-") + "] " + f.msg);
            }
            return out;
        }

        // ---------------------------------------------------------- 区域快照（P3）
        // 只读扫描：交出「方块表 + 处理器表」，sidecar 用它算链接候选。
        // 终点仍是逻辑@config：候选 -> /plan 或 /compose -> bytes_b64 -> build.configure()，
        // 和游戏自己的配置通道是同一份载荷（LogicBlock.compress；联机时服务端应用，
        // LogicBlock.java:65-69），本地写入也是同一个调用，所以两条路不需要分开实现。
        // 引擎坑（v160.7 实测）：tile.block() 是方法，tile.build 是字段。
        var SNAP_MAX_CELLS = 4096;

        // LogicBlock 是「方块」类，真正的建筑是它的内部类 LogicBuild（LogicBlock$LogicBuild），
        // 所以 instanceof LogicBlock 永远为假（v160.7 实测）。跟 targetBuild() 一样用鸭子类型：
        // executor + code 这两个字段只有逻辑建筑才有。
        function isProcessor(bld){
            try{
                return bld !== null && bld !== undefined
                       && bld.executor !== undefined && bld.code !== undefined;
            }catch(e){ return false; }
        }

        function tileBlockName(tile, bld){
            try{
                if(bld !== null && bld !== undefined){ return String(bld.block.name); }
                return String(tile.block().name);
            }catch(e){ return "?"; }
        }

        function regionSnapshot(x1, y1, x2, y2){
            var W = Vars.world;
            var mapName = "?";
            try{ mapName = String(Vars.state.map.name()); }catch(e){ }
            x1 = Math.floor(x1); y1 = Math.floor(y1);
            x2 = Math.floor(x2); y2 = Math.floor(y2);
            if(x1 > x2){ var a = x1; x1 = x2; x2 = a; }
            if(y1 > y2){ var b0 = y1; y1 = y2; y2 = b0; }
            var maxX = W.width() - 1, maxY = W.height() - 1;
            if(x1 < 0){ x1 = 0; }
            if(y1 < 0){ y1 = 0; }
            if(x2 > maxX){ x2 = maxX; }
            if(y2 > maxY){ y2 = maxY; }
            var grid = [], procs = [], truncated = false, x, y;
            for(x = x1; x <= x2 && !truncated; x++){
                for(y = y1; y <= y2; y++){
                    var tile = W.tile(x, y);
                    if(tile === null || tile === undefined){ continue; }
                    var bld = tile.build;
                    var name = tileBlockName(tile, bld);
                    if(name === "air"){ continue; }
                    if(grid.length >= SNAP_MAX_CELLS){ truncated = true; break; }
                    grid.push({x: x, y: y, block: name});
                    if(isProcessor(bld)){
                        procs.push({x: x, y: y, block: name,
                                    code: String(bld.code === null ? "" : bld.code),
                                    links: linkList(bld)});
                    }
                }
            }
            return {schema: 1, mod: MOD_VERSION, build: gameBuild(), map: mapName,
                    world: {width: W.width(), height: W.height()},
                    bounds: {x1: x1, y1: y1, x2: x2, y2: y2},
                    cells: grid.length, truncated: truncated,
                    grid: grid, processors: procs};
        }

        // Last non-empty line of a diagnostic, trimmed: the user needs one line
        // of cause, not a Java stack (a refused socket used to be dumped whole).
        function lastLine(t){
            var parts = String(t === null || t === undefined ? "" : t).split("\n");
            var s = "", i;
            for(i = 0; i < parts.length; i++){
                var q = parts[i];
                while(q.length && (q.charAt(0) === " " || q.charAt(0) === "\t")){ q = q.substring(1); }
                if(q.length){ s = q; }
            }
            return s.length > 200 ? s.substring(0, 200) + "…" : s;
        }
        function httpWhy(code, body){
            var t = String(body === null || body === undefined ? "" : body);
            if(code === "" || code === "-1" || code === -1 || code === undefined || code === null){
                if(t.indexOf("Connection refused") >= 0){
                    return "sidecar 没在跑（连接被拒绝，" + base + "）\n先在本机跑：python tools/logicd.py";
                }
                if(t.indexOf("timed out") >= 0 || t.indexOf("SocketTimeout") >= 0){
                    return "sidecar 没回应（超时，" + base + "）\n确认 python tools/logicd.py 还在跑";
                }
                return "连不上 sidecar（" + base + "）\n先在本机跑：python tools/logicd.py";
            }
            return "sidecar 返回 " + code;
        }
        // 侧车进程比模组旧时，/jobs 会回 404 no such endpoint -- 玩家看到这句不知道要干什么，
        // 而唯一的解法就是重启那个 python 进程，所以直接把解法写进错误里。
        function sidecarStaleHint(t){
            var s = String(t === null || t === undefined ? "" : t);
            if(s.indexOf("no such endpoint") < 0){ return null; }
            return "sidecar 进程是旧版本，不认识这个接口（" + base + "）\n"
                 + "关掉旧的 sidecar 进程再重新启动：python tools/logicd.py --port 8765\n"
                 + "（改过 tools/logicd.py 之后必须重启，模组连的是内存里那份旧代码）";
        }
        function jobWhy(code, text, res){
            var hint = sidecarStaleHint(text) || sidecarStaleHint(res && res.error);
            if(hint !== null){ return hint; }
            return (res && res.error) ? String(res.error) : httpWhy(code, text);
        }
        function regionCandidatesText(raw){
            var s = String(raw === null || raw === undefined ? "" : raw);
            var nl = s.indexOf("\n");
            var code = nl < 0 ? "" : s.substring(0, nl);
            var body = nl < 0 ? s : s.substring(nl + 1);
            var res = parse(body);
            if(code !== "200" || res === null || res.ok !== true){
                var why = httpWhy(code, body);
                var diag = (code === "200" && res !== null && res.message)
                    ? String(res.message) : lastLine(body);
                return diag.length > 0 ? why + "\n\n" + diag : why;
            }
            var out = ["区域 " + res.bounds.x1 + "," + res.bounds.y1 + " - "
                       + res.bounds.x2 + "," + res.bounds.y2
                       + "   方块 " + res.cells
                       + (res.truncated ? "（已截断）" : "")];
            var ps = res.processors || [], i, j;
            if(ps.length === 0){ out.push("这个区域里没有处理器"); }
            for(i = 0; i < ps.length; i++){
                var p = ps[i];
                out.push("");
                out.push("@" + p.x + "," + p.y + " " + p.block + "   链接 "
                         + p.links.length + "：" + (p.links.length ? p.links.join(", ") : "无"));
                var ms = p.missing || [];
                for(j = 0; j < ms.length; j++){
                    out.push("  ⚠ " + ms[j].name + " 代码在用，但没绑上、也不在本区域候选里"
                             + (ms[j].suggest ? "（同类可用 " + ms[j].suggest + "）"
                                              : "（本区域没有同类方块）"));
                }
                var cs = p.candidates || [];
                if(cs.length === 0){ out.push("  10 格内没有可连的方块"); }
                for(j = 0; j < cs.length && j < 12; j++){
                    out.push("  " + cs[j].name + "  ←  " + cs[j].block
                             + " @" + cs[j].x + "," + cs[j].y
                             + "   " + cs[j].dist + " 格"
                             + (cs[j].used ? "   [代码正在用]" : ""));
                }
                if(cs.length > 12){ out.push("  …还有 " + (cs.length - 12) + " 个"); }
            }
            out.push("");
            out.push("确认后按住 F3 点一下处理器，用一句话生成，写入走 logic@config（configure）。");
            return out.join("\n");
        }
        function regionText(snap){
            var p = snap.processors, i;
            var out = ["区域 " + snap.bounds.x1 + "," + snap.bounds.y1 + " - "
                       + snap.bounds.x2 + "," + snap.bounds.y2
                       + "   方块 " + snap.cells + (snap.truncated ? "（已截断）" : "")
                       + "   处理器 " + p.length];
            for(i = 0; i < p.length; i++){
                out.push("  @" + p[i].x + "," + p[i].y + " " + p[i].block
                         + "  链接 " + p[i].links.length);
            }
            return out.join("\n");
        }
        // ---------------------------------------------------------- 控制台接口
        var api = {
            maiVersion: function(){ return "mlog-auxiliary " + MOD_VERSION + "  sidecar=" + base; },
        // 调试/测试用：同步原生请求，返回 "<code>" + 换行 + 正文。会占住调用线程到超时，
        // 只对 localhost 用；正式路径仍然是 httpJson + Core.app.post。
        maiHttpRaw: function(method, url, body){ var r = httpRaw(method, String(url), body === undefined ? null : body); return r.code + "\n" + r.text; },
            maiPing:    function(){
                httpJson("GET", "/health", null, function(code, text){
                    var out = "sidecar " + base + " -> " + code + "\n" + String(text).substring(0, 300);
                    print("[mai] " + out);
                    if(Vars.ui !== null){ Vars.ui.showText("Mlog辅助 · 连接", out); }
                });
                return "已发出 health 请求（结果稍后弹窗）";
            },
            maiSel:     function(){ return describe(targetBuild()); },
            maiPanel:   function(){ openPanel(); return "opened"; },
            maiCompose: function(template, paramsJson){
                var params = {};
                if(paramsJson){ var p = parse(String(paramsJson)); if(p){ params = p; } }
                var b = targetBuild();
                httpJson("POST", "/compose",
                         JSON.stringify({template: String(template), params: params,
                                         links: linkList(b), ipt: 2}),
                         function(code, text){
                             var out = "compose " + code + "\n" + String(text).substring(0, 1500);
                             print("[mai] " + out);
                             if(Vars.ui !== null){ Vars.ui.showText("Mlog辅助 · compose", out); }
                         });
                return "已发出 compose 请求（结果稍后弹窗并写日志）";
            },
            maiApply:   function(template, paramsJson){
                var b = targetBuild();
                if(b === null){ return "鼠标下没有处理器"; }
                var params = {};
                if(paramsJson){ var p = parse(String(paramsJson)); if(p){ params = p; } }
                httpJson("POST", "/compose",
                         JSON.stringify({template: String(template), params: params,
                                         links: linkList(b), ipt: 2}),
                         function(code, text){
                             var res = parse(text);
                             if(code !== 200 || res === null){
                                 if(Vars.ui !== null){ Vars.ui.showText("Mlog辅助",
                                     "compose 失败（" + code + "）\n" + String(text).substring(0, 800)); }
                                 return;
                             }
                             // 回调本身就在主线程（httpJson 用 Core.app.post），可以直接写方块
                             var msg = writeBuild(b, res);
                             print("[mai] " + msg);
                             if(Vars.ui !== null){ Vars.ui.showText("Mlog辅助 · 写入", msg); }
                         });
                return "已发出 compose 请求（0 ERR 才写，结果稍后弹窗）";
            },
            maiUndo:    function(){ return undo(); },
            maiCheck:   function(code){
                var b = targetBuild();
                var src = (code === undefined || code === null) ? (b === null ? "" : String(b.code)) : String(code);
                var res = quickRun(src, b);
                if(res.missing){ return "本地快检不可用"; }
                var out = [quickSummary(res)];
                var ls = quickLines(res);
                for(var i = 0; i < ls.length; i++){ out.push(ls[i]); }
                return out.join("\n");
            },
            maiScan:    function(){
                var api = quickApi();
                if(api === null){ return "本地快检不可用"; }
                var build = gameBuild();
                var t0 = Packages.java.lang.System.currentTimeMillis();
                var n = 0, bad = 0, errs = 0, warns = 0;
                var byRule = {};
                Groups.build.each(function(g){
                    try{
                        if(g.executor === undefined || g.code === undefined){ return; }
                        var res = api.q.check(api.r, String(g.code), linkNames(g), {build: build});
                        n++;
                        if(res.findings.length > 0){ bad++; }
                        for(var i = 0; i < res.findings.length; i++){
                            var f = res.findings[i];
                            if(f.sev === "ERR"){ errs++; } else { warns++; }
                            var k = f.rid || "(no-id)";
                            byRule[k] = (byRule[k] || 0) + 1;
                        }
                    }catch(e){ }
                });
                var ms = Packages.java.lang.System.currentTimeMillis() - t0;
                var out = ["本地快检扫描：" + n + " 个处理器，" + bad
                         + " 个有命中（ERR " + errs + " / WARN " + warns + "），" + ms + " ms"];
                for(var k in byRule){ out.push("  " + k + "  " + byRule[k]); }
                return out.join("\n");
            }
        };

        // 调试入口也挂到控制台（设置界面用不了时的退路）
        api.maiDiag = function(){ return diagText(); };
        api.maiPanel = function(){ openPanel(); return "opened"; };
        api.maiSettings = function(){ return registerSettings() ? "registered" : "no ui"; };
        api.maiSelfTest = function(){ return selfTest(); };
        api.maiUndo = function(){ return undo(); };
        api.maiUndoInfo = function(){ return undoInfo(); };
        // 落盘路径的真引擎自检（ui smoke 用）：写一份假快照进 <dataDir>/mlogauxiliary/selftest，
        // 读回来比对 x/y/code，然后删掉文件和目录 —— 只在测试里跑，正常游戏不碰这个目录。
        api.maiUndoProbe = function(){
            var root = null, made = false, name = null, out = "no-dir";
            try{
                root = Vars.dataDirectory.child("mlogauxiliary").child("selftest");
                if(!root.exists()){ root.mkdirs(); made = true; }
                var b = {tile: {x: 3, y: 4}, code: "set n 0\nprint n\nend", links: {size: 0}};
                name = saveUndoTo(root, b, "selftest");
                var back = parse(root.child(name).readString("UTF-8"));
                var ok = (back !== null && back.x === 3 && back.y === 4 && back.code === b.code
                          && back.links.length === 0);
                root.child(name).delete();
                if(made){ root.deleteDirectory(); }
                out = ok ? ("ok " + name) : "bad";
            }catch(e){ out = "fail " + e; }
            return out;
        };
        api.maiAi = function(){ showAiPanel(); return "opened"; };
        api.maiReview = function(){ return reviewText(); };
        // 测试钩子（tests/mlogauxiliary/run_ui_smoke.py 用）：喂一个假 statements
        // （每个孩子代表一条语句）+ 一组 findings，返回 "行号:x,y:颜色" 清单。
        // 真机上没人调它，行内箭头走 refreshReview -> syncArrows。
        api.maiArrows = function(statements, findingsJson, drawable){
            var res = {findings: [], stats: null};
            if(findingsJson){
                var f = parse(String(findingsJson));
                if(f !== null && f !== undefined){ res.findings = f; }
            }
            var n = syncArrows(res, statements, drawable);
            var out = ["arrows " + n];
            for(var i = 0; i < arrowRows.length; i++){
                var r = arrowRows[i];
                out.push(r.line + ":" + Math.round(r.img.x) + "," + Math.round(r.img.y)
                         + ":" + sevNameOf(r.img) + ":" + r.items + ":" + (r.img.visible ? "v" : "h"));
            }
            return out.join(" ");
        };
        // 区域快照的三个出口：JSON（给 sidecar / 剪贴板）、纯文本（控制台读）、
        // 以及直接 POST /region 拿链接候选。F7 框选等 UI 之后再接，这里先给控制台。
        api.maiSnapshot = function(x1, y1, x2, y2){
            return JSON.stringify(regionSnapshot(x1, y1, x2, y2));
        };
        api.maiSnapshotText = function(x1, y1, x2, y2){
            return regionText(regionSnapshot(x1, y1, x2, y2));
        };
        // 区域快照一律异步：回调由 httpJson 用 Core.app.post 投递回主线程，而控制台与热键
        // 都跑在主线程 —— 在那里 busy-wait 只能等到超时（v0.4.2 的 F7 返回字面量 "pending"）。
        function regionAroundBox(x1, y1, x2, y2){
            httpJson("POST", "/region", JSON.stringify({snapshot: regionSnapshot(x1, y1, x2, y2)}),
                     function(code, text){
                         if(Vars.ui === null){ return; }
                         Vars.ui.showText("Mlog辅助 · 链接候选", regionCandidatesText(code + "\n" + text));
                     });
        }
        api.maiRegion = function(x1, y1, x2, y2){
            regionAroundBox(x1, y1, x2, y2);
            return "已发出区域快照（结果稍后弹窗）";
        };
        api.maiRegionAround = function(r){
            var b = targetBuild();
            if(b === null){ return "鼠标下没有处理器"; }
            var n = (r === undefined || r === null) ? 10 : Math.floor(r);
            return api.maiRegion(b.tile.x - n, b.tile.y - n, b.tile.x + n, b.tile.y + n);
        };

        // ---------------------------------------------------------- F3 拖拽框选（v0.4.8）
        // 规划里 F7 本来就是「框选矩形」（docs/Mlog辅助-规划.md:99），v0.4.2 只做了只读的一半：
        // 以鼠标下的处理器为中心扫固定半径。F8 在游戏里是控制台
        // （Mindustry-Source/core/src/mindustry/input/Binding.java:107 console = KeyCode.f8），
        // F9/F10 也被占，所以框选另开一个空着的键：F3。
        // 拖拽时的高亮画在世界坐标上（Events.run(Trigger.draw) + Lines.rect），不往场景树里塞元素：
        // v0.4.1 那次崩溃就是自造结果区引起的，能画的地方就不建 UI。
        // v0.5.0 起高亮照抄原版选框（InputHandler.drawSelection）：2px 双描边 + 尺寸文本，无填充。
        // 状态机（纯函数，控制台/自检直接驱动）：**F3 就是鼠标左键**。
        // 按住 F3 = 按下左键（起点 = 此刻鼠标格），移动鼠标改终点，松开 F3 = 抬起左键并出快照。
        // 没有「就绪」这个中间态（v0.4.9 是「按 F3 就绪 + 按左键拖」，用户 2026-10-30 要的就是按下即拉框）。
        var selHolding = false, selDragging = false;
        var selStartX = 0, selStartY = 0, selCurX = 0, selCurY = 0;

        // 屏幕 -> 格子。mouseWorldX/Y 已经过相机变换，tileWorld 再按 tilesize 取整。
        function mouseTile(){
            var t = Vars.world.tileWorld(Core.input.mouseWorldX(), Core.input.mouseWorldY());
            if(t === null || t === undefined){ return null; }
            return {x: t.x, y: t.y};
        }

        // 拖拽方向不重要：左上到右下、右下到左上必须给出同一个矩形。
        function selRect(ax, ay, bx, by){
            var x1 = Math.min(ax, bx), y1 = Math.min(ay, by);
            var x2 = Math.max(ax, bx), y2 = Math.max(ay, by);
            return {x1: x1, y1: y1, x2: x2, y2: y2, w: x2 - x1 + 1, h: y2 - y1 + 1};
        }

        // selPress = 按下左键，selRelease = 抬起左键。F3 的 keyDown/keyUp 边沿直接映射到这两个上。
        function selPress(x, y){
            if(selDragging){ return false; }
            selHolding = true;
            selDragging = true;
            selStartX = x; selStartY = y; selCurX = x; selCurY = y;
            return true;
        }
        function selMove(x, y){
            if(!selDragging){ return false; }
            selCurX = x; selCurY = y;
            return true;
        }
        function selBox(){ return selRect(selStartX, selStartY, selCurX, selCurY); }
        function selCancel(){ selHolding = false; selDragging = false; }
        function selRelease(){
            if(!selDragging){ return null; }
            var r = selBox();
            selCancel();
            return r;
        }

        // 高亮参数照原版选框：**左下角 + 宽高**（Lines.rect(x,y,w,h)），不是中心点。
        // 原版见 Mindustry-Source/core/src/mindustry/input/InputHandler.java:1758-1795 drawSelection()。
        // 还要再退半格：Tile.worldx() 返回 x*tilesize（Tile.java:166-172 —— 那是格子的**中心**），
        // 所以格子 (x1,y1) 的左下角是 (x1-0.5)*8。原版也是这么算的：Placement.java:380-390
        // drawResult.x = x*tilesize - block.size*scaling*tilesize/2（air：size 1、scaling 1 ⇒ 减 4）。
        // v0.6.0 漏了这个半格，框整体偏右上角半个格子（用户实测）。
        function selDrawArgs(r){
            return {x: (r.x1 - 0.5) * 8, y: (r.y1 - 0.5) * 8, w: r.w * 8, h: r.h * 8};
        }

        // 原版选框没有半透明填充：Lines.stroke(2) 两道描边，
        // 先 accentBack 画一条 y-1 的阴影，再 accent 画本体（InputHandler.java:1765-1770）。
        function drawSelection(){
            if(!selDragging){ return; }
            var r = selBox(), a = selDrawArgs(r);
            try{
                var D = Packages.arc.graphics.g2d.Draw;
                var L = Packages.arc.graphics.g2d.Lines;
                L.stroke(2);
                D.color(Pal.accentBack);
                L.rect(a.x, a.y - 1, a.w, a.h);
                D.color(Pal.accent);
                L.rect(a.x, a.y, a.w, a.h);
                D.color();
            }catch(e){ /* 画不出来不影响选择本身 */ }
            drawSizeText(r);
        }

        // 原版还在光标旁写「宽x高 (面积)」（InputHandler.java:1772-1794）：
        // Fonts.outline + 1/camerascale 缩放 + Draw.z(Layer.endPixeled)，画完逐项还原。
        // 字是附加品：任何一步抛异常只丢字，方框照画。
        function drawSizeText(r){
            try{
                // Fonts 是 mindustry.ui.Fonts（不是 gen 包：out/_server160.jar 里只有
                // mindustry/ui/Fonts.class，写错包名会被 catch 吞掉、字永远画不出来）。
                var font = Packages.mindustry.ui.Fonts.outline;
                if(font === null || font === undefined){ return; }
                var D = Packages.arc.graphics.g2d.Draw;
                var scale = 1;
                try{ scale = Vars.renderer.camerascale; }catch(e0){ }
                if(!(scale > 0)){ scale = 1; }
                var z = D.z();
                D.z(Packages.mindustry.core.Layer.endPixeled);
                font.getData().setScale(1 / scale);
                font.setColor(Pal.accent);
                var off = 5 / scale * 8;
                font.draw(r.w + "x" + r.h + " (" + (r.w * r.h) + ")",
                          Core.input.mouseWorldX() + off, Core.input.mouseWorldY() + off);
                font.setColor(Packages.arc.graphics.Color.white);
                font.getData().setScale(1);
                D.z(z);
            }catch(e){ /* 字画不出来只丢字 */ }
        }

        function regionSummary(snap){
            var b = snap.bounds, out = [];
            out.push("区域 " + b.x1 + "," + b.y1 + " - " + b.x2 + "," + b.y2
                     + "   " + (b.x2 - b.x1 + 1) + "×" + (b.y2 - b.y1 + 1) + " 格");
            out.push("方块 " + snap.cells + (snap.truncated ? "（已截断）" : "")
                     + "   处理器 " + snap.processors.length + "   地图 " + snap.map);
            var ps = snap.processors || [], i;
            for(i = 0; i < ps.length; i++){
                out.push("  @" + ps[i].x + "," + ps[i].y + " " + ps[i].block
                         + "   链接 " + ps[i].links.length
                         + (ps[i].links.length ? "：" + ps[i].links.join(", ") : ""));
            }
            return out.join("\n");
        }

        function popup(title, text){
            if(Vars.ui === null || Vars.ui === undefined){ return; }
            try{ Vars.ui.showText(title, String(text)); }catch(e){ }
        }

        // 非阻塞提示。**框选绝不能用 showText**：Dialog 会把鼠标吃掉（Core.scene.hasDialog() 为真，
        // 世界收不到点击），于是「按 F3 弹出提示」= 拖不动 —— 用户 2026-10-30 报的就是这个。
        // showInfoFade 是 Touchable.disabled 的淡出标签（Mindustry-Source/core/src/mindustry/core/UI.java:373），不挡输入。
        function hint(text){
            if(Vars.ui === null || Vars.ui === undefined){ return; }
            try{ Vars.ui.showInfoFade(String(text)); }catch(e){ }
        }

        // 松手之后走这里：先给区域摘要（不需要 sidecar），再把 JSON 交给 /snapshot 落盘。
        function dumpRegion(x1, y1, x2, y2){
            var snap = regionSnapshot(x1, y1, x2, y2);
            var head = regionSummary(snap);
            if(snap.processors.length === 0){
                popup("Mlog辅助 · 区域快照", head + "\n\n这块区域里没有处理器。");
                return head;
            }
            if(Vars.ui === null || Vars.ui === undefined){
                // 无头引擎（自检/测试）既没有界面也没有 sidecar：只把摘要交回去，不发请求。
                return head;
            }
            // 两次请求串起来（都是本机回环，几十毫秒）：先落盘，再要链接候选，最后开面板。
            // 顺序有意义：面板要同时显示「落盘到哪」和「候选链接」，缺一条就得等第二次回调。
            try{
                httpJson("POST", "/snapshot", JSON.stringify({snapshot: snap}), function(code, text){
                    var res = parse(text);
                    var line = (code === "200" && res !== null && res.ok === true)
                        ? "已落盘 " + res.path + "（" + res.bytes + " B）"
                        : "没能落盘：" + httpWhy(code, text);
                    httpJson("POST", "/region", JSON.stringify({snapshot: snap}), function(c2, t2){
                        var body = head + "\n" + line;
                        try{
                            showRegionPanel(snap, body, regionCandidatesText(c2 + "\n" + t2));
                        }catch(e){
                            log("region panel failed, falling back to text: " + e);
                            popup("Mlog辅助 · 区域快照", body + "\n\n" + regionCandidatesText(c2 + "\n" + t2));
                        }
                    });
                });
                return head + "\n（面板稍后弹出）";
            }catch(e){
                popup("Mlog辅助 · 区域快照", head + "\n\n没能落盘：" + e);
                return head + "\n（落盘失败：" + e + "）";
            }
        }

        function selFinish(){
            var r = selRelease();
            if(r === null){ return null; }
            // v0.8.1：单格 = 选中处理器。按住 F3 在处理器上点一下直接开 AI 面板，
            // 拖出矩形才走区域快照；空格子单选给提示。v0.9.0 起 F4 热键彻底删除。
            if(r.w === 1 && r.h === 1){
                var one = processorAt(r.x1, r.y1);
                if(one !== null){
                    try{
                        showAiPanel(one);
                        return "AI 面板：" + r.x1 + "," + r.y1;
                    }catch(e){
                        log("single-tile AI panel failed: " + e);
                        hint("这一格的 AI 面板打不开：" + e);
                        return null;
                    }
                }
                hint("这一格没有处理器：单格按住 F3 选中处理器 = 开 AI 面板；拖出矩形 = 区域快照");
                return null;
            }
            return dumpRegion(r.x1, r.y1, r.x2, r.y2);
        }

        // F3 是按住式的（=鼠标左键），所以 maiSelect 不再“就绪”，只给提示。
        api.maiSelect = function(){
            hint("框选：按住 F3 拖出矩形，松开 F3 出快照");
            return "按住 F3 拖出矩形";
        };
        api.maiSelState = function(){
            return JSON.stringify({holding: selHolding, dragging: selDragging,
                                   startX: selStartX, startY: selStartY,
                                   curX: selCurX, curY: selCurY});
        };
        api.maiSelPress = function(x, y){ return selPress(x, y); };
        api.maiSelMove = function(x, y){ return selMove(x, y); };
        api.maiSelRelease = function(){ var r = selRelease(); return r === null ? "" : JSON.stringify(r); };
        api.maiSelDraw = function(ax, ay, bx, by){ return JSON.stringify(selDrawArgs(selRect(ax, ay, bx, by))); };
        api.maiDump = function(x1, y1, x2, y2){ return dumpRegion(x1, y1, x2, y2); };
        api.maiSelRect = function(ax, ay, bx, by){ return JSON.stringify(selRect(ax, ay, bx, by)); };
        // v0.8.1：单格选中处理器 = 开 AI 面板；maiPick 把「这一格是不是处理器」暴露给无头测试。
        api.maiPick = function(x, y){ var b = processorAt(x, y); return b === null ? "" : (x + "," + y); };
        // v0.7.0 F2 处理器清单：maiList 返回文本摘要（无 UI 也能验），maiListRows 返回 JSON 行。
        api.maiList = function(){ return listText(); };
        api.maiListRows = function(){ return JSON.stringify(scanProcessors().rows); };
        api.maiListPanel = function(){ openListPanel(); return "opened"; };
        // v0.8.0 作业队列：投递 / 查 / 取消 / 同步跑完（同步版只给控制台与自检）
        api.maiSetBase = function(u){ base = String(u); return base; };
        api.maiJob = function(desc){
            var b = targetBuild();
            if(b === null){ return "鼠标下没有处理器"; }
            jobSubmit(b, String(desc), function(res, why){
                hint(res === null ? ("投递失败：" + why) : ("作业 " + res.id + " 已投递"));
            });
            return "已投递作业";
        };
        api.maiJobSync = function(desc, timeoutMs){
            var b = targetBuild();
            if(b === null){ return JSON.stringify({ok: false, text: "no processor"}); }
            return jobSync(b, String(desc), timeoutMs);
        };
        api.maiJobSyncAt = function(x, y, desc, timeoutMs){
            var b = buildAt(x, y);
            if(b === null){ return JSON.stringify({ok: false, text: "no processor at " + x + "," + y}); }
            return jobSync(b, String(desc), timeoutMs);
        };
        api.maiJobWrite = function(jobJson, x, y){
            var job = parse(String(jobJson));
            if(job === null){ return "job json parse failed"; }
            var b = buildAt(x, y);
            if(b === null){ return "no processor at " + x + "," + y; }
            var w = writeBuild(b, jobAsPlan(job));
            return w + " | " + String(b.code).replace(/\n/g, " / ");
        };
        api.maiJobProgress = function(jobJson){ return jobProgressText(parse(String(jobJson))); };
        api.maiJobCancel = function(){ return cancelJob(); };
        api.maiJobState = function(){
            return aiJob === null ? "" : JSON.stringify({id: aiJob.id, desc: aiJob.desc});
        };

        // 挂到脚本作用域（控制台里能直接敲），并读回自检
        var scope = Vars.mods.getScripts().scope;
        var mounted = 0;
        for(var k in api){
            Packages.rhino.ScriptableObject.putProperty(scope, k, api[k]);
            // 读回不能用 scope.get(k, scope)：某些加载路径下 scope 是 global 包装对象，
            // 没有可调用的 get 方法（真 v160.7 实测报 "Cannot find function get"）。
            try{
                if(Packages.rhino.ScriptableObject.getProperty(scope, k) !== undefined){ mounted++; }
            }catch(e){
                mounted++;   // putProperty 成功即可，读回是自检不是必需
            }
        }
        log("v" + MOD_VERSION + " ready, " + mounted + "/" + Object.keys(api).length
            + " console function(s), sidecar=" + base);

        // 脚本加载时 UI 可能还没建；ClientLoadEvent 再补一次。
        var settingsReady = registerSettings();
        try{
            Events.on(ET.ClientLoadEvent, function(){
                try{ if(!settingsReady){ settingsReady = registerSettings(); } }catch(e){ /* ignore */ }
            });
        }catch(e){ log("ClientLoadEvent hook failed: " + e); }

        // ---------------------------------------------------------- 热键
        {   // v0.9.0: the F4 hotkey is gone, so the update hook is unconditional
            Events.run(ET.Trigger.update, function(){
                try{
                    reviewTick();   // 原版逻辑编辑器开着就顺手刷新那条审查栏
                    jobTick();      // v0.8.0：有作业在跑就每秒查一次状态
                    // 「设置 → Mlog辅助」这一栏只在 Vars.ui 建好之后能注册。脚本加载时
                    // UI 往往还没建（真机日志里是在 ClientLoadEvent 前），所以这里补一次
                    // 有界重试：每 60 帧试一次、最多 600 次（≈10 s @60fps），成功即停。
                    if(!settingsDone && settingsTries < 600){
                        settingsTries++;
                        if(settingsTries % 60 === 0){ registerSettings(); }
                    }
                    if(Vars.state.isMenu()){ return; }
                    if(Vars.ui.chatfrag.shown()){ return; }
                    if(KEY_REGION !== null && Core.input.keyTap(Packages.arc.input.KeyCode[KEY_REGION[0]])){
                        if(!aiShown() && !panelShown() && Core.scene !== null && Core.scene.hasDialog()){ return; }
                        var rb = targetBuild();
                        if(rb === null){
                            Vars.ui.showText("Mlog辅助 · 链接候选",
                                             "鼠标下没有处理器：先把鼠标移到处理器上再按 F7");
                        }else{
                            var rr = 10;
                            // 异步：回调由 httpJson 经 Core.app.post 投递回主线程，
                            // 在这里 busy-wait 只会等到超时（v0.4.2 就是这样弹「sidecar 不可用（）」）。
                            regionAroundBox(rb.tile.x - rr, rb.tile.y - rr,
                                            rb.tile.x + rr, rb.tile.y + rr);
                        }
                    }
                    if(KEY_LIST !== null && Core.input.keyTap(Packages.arc.input.KeyCode[KEY_LIST[0]])){
                        if(!aiShown() && !panelShown() && Core.scene !== null && Core.scene.hasDialog()){ return; }
                        openListPanel();
                    }
                    // F3 = 鼠标左键：按住就拉框（起点=按下那一刻的鼠标格），松开就出快照。
                    // 没有「就绪」态、不需要点左键，也不弹任何窗（弹窗会抢鼠标）。
                    if(KEY_SELECT !== null){
                        var selKey = Packages.arc.input.KeyCode[KEY_SELECT[0]];
                        var selDown = Core.input.keyDown(selKey);
                        if(selDown && !selHolding){
                            if(Core.scene === null || !Core.scene.hasDialog()){
                                var s0 = mouseTile();
                                if(s0 !== null){ selPress(s0.x, s0.y); }
                            }
                        }else if(selDown && selDragging){
                            var s1 = mouseTile();
                            if(s1 !== null){ selMove(s1.x, s1.y); }
                        }else if(!selDown && selHolding){
                            selFinish();
                        }
                    }
                }catch(e){ /* 每帧回调里绝不抛出去 */ }
            });
        }

        // 拖拽高亮：画在世界坐标系里，不碰场景树（画不出来也不影响选择本身）。
        try{
            Events.run(ET.Trigger.draw, function(){
                try{ drawSelection(); }catch(e){ /* 每帧回调里绝不抛出去 */ }
            });
        }catch(e){ log("Trigger.draw hook failed: " + e); }

    }catch(e){
        print("[mai] init failed: " + e);
    }
}

try{ __logicWriterMain(); }catch(e){ print("[mai] bootstrap failed: " + e); }
