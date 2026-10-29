// ============================================================================
//  逻辑写入服务 (LogicWriter) —— scripts/main.js   v0.1  (P1: API 接入 + 写入通道)
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

    var MOD_VERSION = "0.1";
    var URL_KEY     = "logicwriter-url";
    var DEFAULT_URL = "http://127.0.0.1:8765";
    var KEY_PANEL   = ["f4"];      // F4：开面板（F1/F5/F6/F8/F11/F12 与 F9/F10 已被占用）
    var TIMEOUT_MS  = 4000;        // 连接超时：sidecar 是本机的，慢就是没开

    function log(msg){ print("[logic-writer] " + msg); }

    try{
        var Core    = Packages.arc.Core;
        var Events  = Packages.arc.Events;
        var Threads = Packages.arc.util.Threads;
        var Vars    = Packages.mindustry.Vars;
        var ET      = Packages.mindustry.game.EventType;
        var Groups  = Packages.mindustry.gen.Groups;

        // P2 的两个模块。游戏只执行 scripts/main.js（Mods.loadScripts:809 只取 main.js，
        // 除非 scripts/ 下只有一个文件），其余文件必须 require 进来 —— Scripts.java:30-32
        // 给脚本作用域装了 CommonJS 模块提供器，模块里 module.exports 就是取到的东西。
        var QUICK = null, RULES = null;
        try{
            RULES = require("rules.generated");
            QUICK = require("quickcheck");
            log("quick check loaded: " + Object.keys(RULES.instr).length + " instruction(s)");
        }catch(e){
            log("quick check unavailable (" + e + ") -- 面板会少一行本地预检");
        }

        var base = String(Core.settings.getString(URL_KEY, DEFAULT_URL));
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
                Vars.ui.showText("逻辑写入服务 · 已拒绝", text);
                return;
            }
            Vars.ui.showConfirm("逻辑写入服务 · 确认写入",
                text + "\n\n写入目标：" + describe(b),
                function(){
                    var msg = writeBuild(b, res);
                    log(msg);
                    Vars.ui.showText("逻辑写入服务", msg);
                });
        }

        // ---------------------------------------------------------- 面板
        // 模板按钮来自 GET /capabilities —— 面板本身就是"协议通了"的证据。

        function openPanel(){
            var b = targetBuild();
            var d = new Packages.arc.scene.ui.Dialog("逻辑写入服务 v" + MOD_VERSION);
            d.cont.defaults().pad(4);
            d.cont.add("sidecar: " + base).left().row();
            d.cont.add(describe(b)).left().row();
            var qres = quickRun(b === null ? "" : String(b.code), b);
            d.cont.add(quickSummary(qres)).left().row();
            var qlines = quickLines(qres);
            var qmax = Math.min(qlines.length, 4);
            for(var qi = 0; qi < qmax; qi++){
                d.cont.add("  " + qlines[qi]).left().row();
            }
            if(qlines.length > qmax){ d.cont.add("  … 共 " + qlines.length + " 条（控制台 lwCheck() 看全）").left().row(); }
            d.cont.add("").row();
            var pane = d.cont.pane(function(t){
                t.defaults().pad(2).left();
                t.add("正在读取模板…").row();
            }).height(320).width(520).get();
            d.addCloseButton();
            d.show();

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
                    Vars.ui.showText("逻辑写入服务", "compose 失败（" + code + "）\n" + text);
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
            lwVersion: function(){ return "logic-writer " + MOD_VERSION + "  sidecar=" + base; },
            lwPing:    function(){ return ping(); },
            lwSel:     function(){ return describe(targetBuild()); },
            lwPanel:   function(){ openPanel(); return "opened"; },
            lwCompose: function(template, paramsJson){
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
            lwApply:   function(template, paramsJson){
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
            lwUndo:    function(){ return undo(); },
            lwCheck:   function(code){
                var b = targetBuild();
                var src = (code === undefined || code === null) ? (b === null ? "" : String(b.code)) : String(code);
                var res = quickRun(src, b);
                if(res.missing){ return "本地快检不可用"; }
                var out = [quickSummary(res)];
                var ls = quickLines(res);
                for(var i = 0; i < ls.length; i++){ out.push(ls[i]); }
                return out.join("\n");
            },
            lwScan:    function(){
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

        // 挂到脚本作用域（控制台里能直接敲），并读回自检
        var scope = Vars.mods.getScripts().scope;
        var mounted = 0;
        for(var k in api){
            Packages.rhino.ScriptableObject.putProperty(scope, k, api[k]);
            if(scope.get(k, scope) !== null){ mounted++; }
        }
        log("v" + MOD_VERSION + " ready, " + mounted + "/" + Object.keys(api).length
            + " console function(s), sidecar=" + base);

        // ---------------------------------------------------------- 热键
        if(KEY_PANEL !== null){
            Events.run(ET.Trigger.update, function(){
                try{
                    if(Vars.state.isMenu()){ return; }
                    if(Vars.ui.chatfrag.shown()){ return; }
                    var key = Packages.arc.input.KeyCode[KEY_PANEL[0]];
                    if(Core.input.keyTap(key)){ openPanel(); }
                }catch(e){ /* 每帧回调里绝不抛出去 */ }
            });
        }
    }catch(e){
        print("[logic-writer] init failed: " + e);
    }
}

try{ __logicWriterMain(); }catch(e){ print("[logic-writer] bootstrap failed: " + e); }
