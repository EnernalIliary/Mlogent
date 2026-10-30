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

    var MOD_VERSION = "0.4.7";
    var URL_KEY     = "mlogauxiliary-url";
    var DEFAULT_URL = "http://127.0.0.1:8765";
    var KEY_PANEL   = ["f4"];      // F4：开面板（F1/F5/F6/F8/F11/F12 与 F9/F10 已被占用）
    var KEY_REGION  = ["f7"];      // F7：扫鼠标周围 10 格，列出链接候选
    var TIMEOUT_MS  = 4000;        // 连接超时：sidecar 是本机的，慢就是没开

    function log(msg){ print("[mai] " + msg); }

    // ---------------------------------------------------------- 设置界面
    // 设置 -> 「Mlog辅助」一栏。把调试信息全摊开（版本 / 构建 / 快检模块是否加载 /
    // 规则表条数 / sidecar 地址与可达性 / 数据目录 / mods 目录），省得再往控制台敲命令。
    // 所有游戏对象访问都套 try：无头环境里只是返回 false，不会炸。

    var sidecarOk = null;
    var panel = null;          // 模板块面板的单实例（v0.3.1 之前每次按 F4 都新建一个，能叠起来）
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
        section(t, "说明");
        kv(t, "", "F4 = AI 辅助编程（描述意图 -> 生成 -> 预检 -> 写入）；原版逻辑编辑器底部会多一条「审查」状态栏。地址改完按回车保存。sidecar 不开也能进游戏，只是生成与模板不可用。", mk);
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
        return "设置表格可建，填了 " + ft.count() + " 行/格；诊断 " + diagLines().length
               + " 行；用到的方法 " + ft.methods();
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

        // ---------------------------------------------------------- 写入
        // 唯一的写入口。三道闸：0 ERR、目标存在、载荷由 sidecar 生成（模组不自己拼代码）。

        function writeBuild(b, res){
            if(b === null){ return "没有目标处理器"; }
            if(!res || res.ok !== true){
                return "拒绝写入：静态检查有 ERR（" + ((res && res.errors) || "?") + " 条）";
            }
            if(!res.bytes_b64){ return "拒绝写入：sidecar 没有返回载荷"; }
            try{
                undoStack.push({b: b, code: String(b.code)});
                if(undoStack.length > 20){ undoStack.shift(); }
                b.configure(base64Bytes(res.bytes_b64));
                return "已写入 " + (res.template || "") + "（" + res.statements + " 条语句，"
                     + res.bytes_len + " 字节）";
            }catch(e){
                return "写入失败：" + e;
            }
        }

        function undo(){
            if(!undoStack.length){ return "没有可撤销的写入"; }
            var snap = undoStack.pop();
            try{
                snap.b.updateCode(snap.code);      // P1：仅本地回滚，联机下请重进地图
                return "已回滚到上一版代码（" + String(snap.code).split("\n").length + " 行）";
            }catch(e){ return "回滚失败：" + e; }
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
        // 自加「关闭」按钮 + closeOnBack() + 再按一次 F4 关，并且只保留一个实例。

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

        // ------------------------------------------ AI 辅助编程（F4）
        // 一句话 → sidecar POST /plan → 代码 + 预检 → 确认写入。
        // 现在是规则式意图路由（tools/logicd.py 的 INTENTS 表），模型的接入点只在
        // /plan 的实现里，模组这一侧不用改。

        var aiPanel = null;

        function aiShown(){
            try{ return aiPanel !== null && aiPanel.isShown(); }catch(e){ return false; }
        }

        function toggleAiPanel(){
            if(aiShown()){ try{ aiPanel.hide(); }catch(e){ /* ignore */ } return; }
            showAiPanel();
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

        function showAiPanel(){
            if(aiShown()){ try{ aiPanel.toFront(); return; }catch(e){ /* ignore */ } }
            var b = targetBuild();
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
            d.buttons.button("生成", function(){
                host.clear();
                host.add("正在请求 sidecar…").row();
                plan(intent, b, function(res){ renderPlan(host, res, b, d); });
            }).width(140);
            d.buttons.button("关闭", function(){ d.hide(); }).width(140);
            d.closeOnBack();
            d.show();
            aiPanel = d;
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
            out.push("确认后按 F4 用一句话生成，写入走 logic@config（configure）。");
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
        if(KEY_PANEL !== null){
            Events.run(ET.Trigger.update, function(){
                try{
                    reviewTick();   // 原版逻辑编辑器开着就顺手刷新那条审查栏
                    // 「设置 → Mlog辅助」这一栏只在 Vars.ui 建好之后能注册。脚本加载时
                    // UI 往往还没建（真机日志里是在 ClientLoadEvent 前），所以这里补一次
                    // 有界重试：每 60 帧试一次、最多 600 次（≈10 s @60fps），成功即停。
                    if(!settingsDone && settingsTries < 600){
                        settingsTries++;
                        if(settingsTries % 60 === 0){ registerSettings(); }
                    }
                    if(Vars.state.isMenu()){ return; }
                    if(Vars.ui.chatfrag.shown()){ return; }
                    var key = Packages.arc.input.KeyCode[KEY_PANEL[0]];
                    if(Core.input.keyTap(key)){
                        // 我们的面板开着 -> F4 关掉；别人的对话框开着 -> 别叠上去
                        if(!aiShown() && !panelShown() && Core.scene !== null && Core.scene.hasDialog()){ return; }
                        toggleAiPanel();
                    }
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
                }catch(e){ /* 每帧回调里绝不抛出去 */ }
            });
        }
    }catch(e){
        print("[mai] init failed: " + e);
    }
}

try{ __logicWriterMain(); }catch(e){ print("[mai] bootstrap failed: " + e); }
