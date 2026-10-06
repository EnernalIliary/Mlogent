// Rhino 互操作探针：验证脚本里那些"吃类型转换"的写法在游戏自带 Rhino 上能不能过
var _p = print;

_p("--- 1) 嵌套类取用 + new（脚本最关键的一步）---");
var cs = Packages.mindustry.ui.dialogs.SettingsMenuDialog.SettingsTable.CheckSetting;
_p("CheckSetting class = " + cs);

var el = new cs("dp-camera-unbind", false, null);
_p("new CheckSetting(name, false, null) = OK");
_p("  name        = [" + el.name + "]");
_p("  def         = [" + el.def + "]");
_p("  title       = [" + el.title + "]   <- bundle 没键时的回退值");
_p("  description = [" + el.description + "]");
el.title = "镜头解绑（测试）";
_p("  写入 title 后 = [" + el.title + "]");

_p("--- 2) 第三个参数传 JS 函数（Boolc）---");
var el2 = new cs("dp-test-cb", true, function(v){ });
_p("new CheckSetting(name, true, JS函数) = OK (def=" + el2.def + ")");

_p("--- 3) arc.Settings ---");
var S = Packages.arc.Core.settings;
S.defaults("dp-probe-x", true);
_p("defaults 后 getBool(dp-probe-x)          = " + S.getBool("dp-probe-x"));
S.put("dp-probe-x", false);
_p("put(false) 后 getBool                    = " + S.getBool("dp-probe-x"));
S.put("dp-camera-unbind", true);
_p("getBool(dp-camera-unbind, false)         = " + S.getBool("dp-camera-unbind", false));
S.remove("dp-camera-unbind");

_p("--- 4) arc.Events 用 JS 函数当回调 ---");
var ET = Packages.mindustry.game.EventType;
Packages.arc.Events.run(ET.Trigger.update, function(){ });
_p("Events.run(Trigger.update, function(){}) = OK");
Packages.arc.Events.on(ET.WorldLoadEvent, function(){ });
_p("Events.on(WorldLoadEvent, function(){})  = OK");

_p("--- 5) Timer.schedule 用 JS 函数 + 3 个参数 ---");
Packages.arc.util.Timer.schedule(function(){ }, 3);
_p("Timer.schedule(function(){}, 3) = OK");

_p("--- 6) Vec2 / Mathf / 字段访问 ---");
var v = new Packages.arc.math.geom.Vec2();
v.set(1.5, 2.5);
_p("Vec2.set(1.5,2.5) -> (" + v.x + "," + v.y + ")   注意 x 是字段，写 x() 会报错");
_p("Mathf.round(1.6) = " + Packages.arc.math.Mathf.round(1.6));

_p("--- 7) KeyCode 的大小写（决定热键写法）---");
_p("KeyCode.v  = " + Packages.arc.input.KeyCode.v);
_p("KeyCode.n  = " + Packages.arc.input.KeyCode.n);
_p("KeyCode.F7 = " + Packages.arc.input.KeyCode.F7);
_p("KeyCode.f7 = " + Packages.arc.input.KeyCode.f7);

_p("--- 8) Vars 静态字段可见性 ---");
_p("Vars.state  = " + Packages.mindustry.Vars.state);
_p("Vars.player = " + Packages.mindustry.Vars.player);
_p("Vars.ui     = " + Packages.mindustry.Vars.ui);
_p("Vars.ui.settings = " + (Packages.mindustry.Vars.ui == null ? "null" : Packages.mindustry.Vars.ui.settings));

_p("=== Rhino 互操作探针结束 ===");
