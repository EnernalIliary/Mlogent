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

    var MOD_VERSION = "0.4.0";
    var URL_KEY     = "mlogauxiliary-url";
    var DEFAULT_URL = "http://127.0.0.1:8765";
    var KEY_PANEL   = ["f4"];      // F4：开面板（F1/F5/F6/F8/F11/F12 与 F9/F10 已被占用）
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
    var LABEL_W = 92, VALUE_W = 430;

    function section(t, title){
        t.add("── " + title + " ──────────────").colspan(2).left().padTop(10).padBottom(2).row();
    }

    function kv(t, k, v){
        t.add(k).width(LABEL_W).right().padRight(8);
        t.labelWrap(v).width(VALUE_W).left().row();
    }
    function copyDiag(){
        try{
            Core.app.setClipboardText(diagText());
            if(Vars.ui !== null){ Vars.ui.showText("Mlog辅助 · 诊断", "诊断已复制到剪贴板。"); }
        }catch(e){ log("clipboard failed: " + e); }
    }

    function buildSettingsTable(t){
        t.defaults().pad(3).left();
        kv(t, "", "Mlog辅助 " + MOD_VERSION + " · 把意图变成 mlog 写进处理器；写入走原版 config 通道，联机时由服务端执行");
        var parts = diagParts(), i;
        section(t, "运行环境");
        for(i = 0; i < parts.length; i++){
            if(parts[i].k !== "快检模块" && parts[i].k !== "sidecar"){ kv(t, parts[i].k, parts[i].v); }
        }
        section(t, "本地快检（离线也能用）");
        for(i = 0; i < parts.length; i++){
            if(parts[i].k === "快检模块"){ kv(t, parts[i].k, parts[i].v); }
        }
        section(t, "sidecar（本机进程，关掉也不影响进游戏）");
        t.add("地址").width(LABEL_W).right().padRight(8);
        t.field(base, function(v){
            var s = String(v);
            if(s.length > 0){ base = s; Core.settings.put(URL_KEY, s); log("sidecar = " + s); }
        }).width(300).left().row();
        t.add("操作").width(LABEL_W).right().padRight(8);
        t.button("连接测试", function(){ probeSidecar(); }).width(110);
        t.button("复制诊断", function(){ copyDiag(); }).width(110).row();
        section(t, "快捷动作");
        t.add("").width(LABEL_W);
        t.button("AI 辅助编程", function(){ showAiPanel(); }).width(130);
        t.button("模板面板", function(){ openPanel(); }).width(110).row();
        t.add("").width(LABEL_W);
        t.button("快检鼠标下的处理器", function(){ quickAimed(); }).width(190);
        t.button("打印诊断", function(){
            print("[mai] --- diag ---");
            print(diagText());
        }).width(110).row();
        t.add("").width(LABEL_W);
        t.button("重新注册分类", function(){ settingsDone = false; registerSettings(); }).width(150);
        t.button("审查状态", function(){ showReview(); }).width(110).row();
        section(t, "说明");
        kv(t, "", "F4 = AI 辅助编程（描述意图 → 生成 → 预检 → 写入）；原版逻辑编辑器底部会多一条「审查」状态栏。"
                  + "地址改完按回车保存。sidecar 不开也能进游戏，只是生成与模板不可用。");
    }


    // 无 UI 环境下也能验证设置表格的布线：喂一张假表，数它被填了多少行/格。
    // 假表只实现真实页面用到的方法 —— 少实现一个，selfTest 立刻炸；
    // 同时把用到的名字记下来，供 run_ui_smoke 去真引擎里复核「有没有重载歧义」。
    function fakeTable(){
        var n = 0;
        var used = [];
        function hit(m){ used.push(m); }
        var cell = {
            pad: function(){ hit("pad"); return cell; },
            padTop: function(){ hit("padTop"); return cell; },
            padBottom: function(){ hit("padBottom"); return cell; },
            padRight: function(){ hit("padRight"); return cell; },
            left: function(){ hit("left"); return cell; },
            right: function(){ hit("right"); return cell; },
            width: function(){ hit("width"); return cell; },
            colspan: function(){ hit("colspan"); return cell; },
            row: function(){ n++; hit("row"); return cell; }
        };
        var t = {
            defaults: function(){ hit("defaults"); return cell; },
            add: function(){ n++; hit("add"); return cell; },
            labelWrap: function(){ n++; hit("labelWrap"); return cell; },
            label: function(){ n++; hit("label"); return cell; },
            field: function(v, f){ n++; hit("field"); return cell; },
            button: function(s, f){ n++; hit("button"); return cell; },
            row: function(){ n++; hit("row"); return cell; }
        };
        return {table: t, count: function(){ return n; },
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
        try{ buildSettingsTable(ft.table); }
        catch(e){ return "设置表格布线失败：" + e; }
        return "设置表格可建，填了 " + ft.count() + " 行/格；诊断 " + diagLines().length
               + " 行；用到的方法 " + ft.methods();
    }

    function registerSettings(){
        if(settingsDone){ return true; }
        try{
            if(Vars.ui === null || Vars.ui.settings === null){ return false; }
            Vars.ui.settings.addCategory("Mlog辅助", function(t){ buildSettingsTable(t); });
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
        // Rhino 里做 HTTP 会卡渲染线程，所以整段网络调用丢进守护线程，
        // 结果用 Core.app.post 回到游戏线程再碰界面/世界。

        function readAll(is){
            var br = new Packages.java.io.BufferedReader(
                new Packages.java.io.InputStreamReader(is, "UTF-8"));
            var sb = new Packages.java.lang.StringBuilder();
            var line;
            while((line = br.readLine()) !== null){ sb.append(line); sb.append("\n"); }
            br.close();
            return String(sb.toString());
        }

        function httpJson(method, path, body, cb){
            Threads.daemon(function(){
                var code = -1, text = "";
                try{
                    var con = new Packages.java.net.URL(base + path).openConnection();
                    con.setConnectTimeout(TIMEOUT_MS);
                    con.setReadTimeout(TIMEOUT_MS * 4);
                    con.setRequestMethod(method);
                    if(body !== null){
                        con.setDoOutput(true);
                        con.setRequestProperty("Content-Type", "application/json");
                        var os = con.getOutputStream();
                        os.write(new Packages.java.lang.String(body).getBytes("UTF-8"));
                        os.close();
                    }
                    code = con.getResponseCode();
                    var is = (code >= 400) ? con.getErrorStream() : con.getInputStream();
                    text = is === null ? "" : readAll(is);
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
            var pane = d.cont.pane(function(t){
                t.defaults().pad(2).left();
                t.add("正在读取模板…").row();
            }).height(300).width(520).get();
            d.buttons.defaults().pad(4);
            d.buttons.button("关闭", function(){ d.hide(); }).width(200);
            d.closeOnBack();
            d.show();
            panel = d;

            httpJson("GET", "/capabilities", null, function(code, text){
                var cap = parse(text);
                if(code !== 200 || !cap || cap.ok !== true){
                    pane.clear();
                    pane.add("离线：sidecar 没响应（" + code + "）").row();
                    pane.add("先在本机跑：python tools/logicd.py").row();
                    return;
                }
                pane.clear();
                pane.add("模板（点击 = 生成 + 预检）").row();
                for(var i = 0; i < cap.templates.length; i++){
                    (function(tmpl){
                        pane.button(tmpl.title, function(){
                            d.hide();
                            compose(tmpl.id, {}, b);
                        }).width(500).row();
                    })(cap.templates[i]);
                }
                pane.add("ipt 上限 " + cap.limits.ipt_max
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

        function reviewTargets(){
            try{
                var L = Vars.ui.logic;
                if(L !== null && L !== undefined && L.executor !== null){ return L.executor.build; }
            }catch(e){ /* ignore */ }
            return null;
        }

        function reviewCode(){
            try{ return String(Vars.ui.logic.canvas.save()); }catch(e){ return null; }
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
                          + " · ipt " + res.stats.ticksPerPass).padRight(16);
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

        function plan(intent, b, cb){
            var req = {intent: String(intent), links: linkList(b), ipt: 2};
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
                if(res && res.templates){ out.add("可用模板：" + res.templates.join(" / ")).row(); }
                return;
            }
            out.add("模板 " + res.template + " —— " + res.reason).row();
            var c = reviewCount(res);
            out.add(c.total === 0 ? "预检：通过（0 条）"
                    : ("预检：ERR " + c.err + " / WARN " + c.warn + " / INFO " + c.info)).row();
            var ls = res.findings;
            for(var i = 0; i < ls.length && i < 6; i++){
                out.add("  " + ls[i].sev + " L" + ls[i].line + " " + ls[i].msg).row();
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
            d.cont.add("例：巡逻，遇到敌人就开火 / 20% 物品以下给核心补货 / 每 2 秒打印一次计数").row();
            var out = d.cont.pane(function(t){
                t.defaults().pad(2).left();
                t.add("（还没生成）").row();
            }).height(300).width(580).get();
            d.buttons.defaults().pad(4);
            d.buttons.button("生成", function(){
                out.clear();
                out.add("正在请求 sidecar…").row();
                plan(intent, b, function(res){ renderPlan(out, res, b, d); });
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
                                       links: linkList(b), ipt: 2});
            httpJson("POST", "/compose", body, function(code, text){
                var res = parse(text);
                if(code !== 200 || res === null){
                    Vars.ui.showText("Mlog辅助", "compose 失败（" + code + "）\n" + text);
                    return;
                }
                showResult(res, b);
            });
        }

        function ping(){
            var out = "?";
            httpJson("GET", "/health", null, function(code, text){ out = code + " " + text; });
            // 同步等待：仅调试用，最多 TIMEOUT_MS 后返回（正式路径不这么干）
            var waited = 0;
            while(out === "?" && waited < TIMEOUT_MS){ waited += 50; }
            return "sidecar " + base + " -> " + out;
        }

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

        function linkNames(b){
            var out = [];
            if(b === null || b === undefined){ return out; }
            for(var i = 0; i < b.links.size; i++){ out.push(String(b.links.get(i).name)); }
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
                 + (st.truncates ? "    ⚠ 超过 1000 条会被截断" : "");
        }

        function quickLines(res){
            var out = [];
            for(var i = 0; i < res.findings.length; i++){
                var f = res.findings[i];
                out.push("L" + f.line + " " + f.sev + " [" + (f.rid || "-") + "] " + f.msg);
            }
            return out;
        }

        // ---------------------------------------------------------- 控制台接口
        var api = {
            maiVersion: function(){ return "mlog-auxiliary " + MOD_VERSION + "  sidecar=" + base; },
            maiPing:    function(){ return ping(); },
            maiSel:     function(){ return describe(targetBuild()); },
            maiPanel:   function(){ openPanel(); return "opened"; },
            maiCompose: function(template, paramsJson){
                var params = {};
                if(paramsJson){ var p = parse(String(paramsJson)); if(p){ params = p; } }
                var got = "pending";
                var b = targetBuild();
                httpJson("POST", "/compose",
                         JSON.stringify({template: String(template), params: params,
                                         links: linkList(b), ipt: 2}),
                         function(code, text){ got = code + "\n" + text; });
                var waited = 0;
                while(got === "pending" && waited < TIMEOUT_MS){ waited += 50; }
                return got;
            },
            maiApply:   function(template, paramsJson){
                var b = targetBuild();
                if(b === null){ return "鼠标下没有处理器"; }
                var params = {};
                if(paramsJson){ var p = parse(String(paramsJson)); if(p){ params = p; } }
                var got = null;
                httpJson("POST", "/compose",
                         JSON.stringify({template: String(template), params: params,
                                         links: linkList(b), ipt: 2}),
                         function(code, text){ got = {code: code, res: parse(text)}; });
                var waited = 0;
                while(got === null && waited < TIMEOUT_MS * 2){ waited += 50; }
                if(got === null){ return "sidecar 超时"; }
                return writeBuild(b, got.res);
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
                }catch(e){ /* 每帧回调里绝不抛出去 */ }
            });
        }
    }catch(e){
        print("[mai] init failed: " + e);
    }
}

try{ __logicWriterMain(); }catch(e){ print("[mai] bootstrap failed: " + e); }
