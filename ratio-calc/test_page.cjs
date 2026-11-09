/* 无浏览器验证 index.html 的内联脚本：用最小 DOM 桩把页面逻辑跑一遍。
 * 目的不是像素级渲染，而是确认「选建筑/物品 → 计算 → 填表格」这条链路不报错、数字正确。
 * 用法：node ratio-calc/test_page.cjs
 */
const fs = require("fs");
const path = require("path");

const dir = __dirname;
const html = fs.readFileSync(path.join(dir, "index.html"), "utf8");
const inline = html.match(/<script>([\s\S]*?)<\/script>/)[1];

/* ---------------- 最小 DOM 桩 ---------------- */
function makeEl(id, tag) {
  const el = {
    id, tag: tag || "div", value: "", textContent: "", innerHTML: "", style: {},
    children: [], disabled: false, _attrs: {},
    classList: {
      _s: new Set(),
      add(c) { this._s.add(c); },
      remove(c) { this._s.delete(c); },
      toggle(c, on) { if (on === undefined) { this._s.has(c) ? this._s.delete(c) : this._s.add(c); } else if (on) { this._s.add(c); } else { this._s.delete(c); } return this._s.has(c); },
      contains(c) { return this._s.has(c); }
    },
    get firstChild() { return el.children[0] || null; },
    appendChild(c) { el.children.push(c); return c; },
    removeChild(c) { const i = el.children.indexOf(c); if (i >= 0) el.children.splice(i, 1); return c; },
    addEventListener() {},
    setAttribute(k, v) { el._attrs[k] = String(v); },
    getAttribute(k) { return k in el._attrs ? el._attrs[k] : null; },
    querySelectorAll() { return []; },
    insertAdjacentHTML(_pos, h) { el.innerHTML += h; }
  };
  return el;
}

const registry = new Map();
const document = {
  getElementById(id) {
    if (!registry.has(id)) registry.set(id, makeEl(id));
    return registry.get(id);
  },
  createElement(tag) { return makeEl("", tag); },
  querySelectorAll() { return []; }
};

// HTML 里写死的 input 初值，桩不会自动读属性，这里补上
document.getElementById("rate").value = "1";
document.getElementById("count").value = "1";
document.getElementById("depth").value = "6";
document.getElementById("oilfloor").value = "1.5";

global.window = global;
global.document = document;
global.location = { search: "" };
global.alert = (m) => { throw new Error("alert: " + m); };

require(path.join(dir, "data", "gamedata.js"));
require(path.join(dir, "core.js"));

// 执行页面脚本
new Function(inline)();

/* ---------------- 断言 ---------------- */
let bad = 0;
function check(name, cond, extra) {
  if (cond) { console.log("ok  ", name); }
  else { bad++; console.log("FAIL", name, extra || ""); }
}
const $ = (id) => document.getElementById(id);
const txt = (id) => $(id).innerHTML || $(id).textContent || "";

/* --- 默认：建筑模式（graphite-press × 1，满效） --- */
check("数据摘要已填充", /release-160/.test($("meta").textContent) && /33/.test($("meta").textContent) &&
      /17/.test($("meta").textContent), $("meta").textContent);
check("物品下拉已填充", $("target").children.length === 22, String($("target").children.length));
check("默认边界含 coal/sand 与无配方物品（边界是开关，不是文本）",
      window.__ratio.bnd().indexOf("coal") >= 0 && window.__ratio.bnd().indexOf("scrap") >= 0,
      window.__ratio.bnd().join(","));
check("边界开关：物品芯片按物品数铺满，且没有文本输入框",
      (txt("bnditems").match(/data-bnd=/g) || []).length === 22 &&
      !/<textarea id="boundary"/.test(html) && !/<textarea id="force"/.test(html),
      String((txt("bnditems").match(/data-bnd=/g) || []).length));
check("配方选择：多配方物品列成下拉（石墨/硅 至少有）",
      /data-force="graphite"/.test(txt("forcelist")) && /data-force="silicon"/.test(txt("forcelist")),
      txt("forcelist").slice(0, 400));

check("输出区已展开", !$("out").classList.contains("hidden"));
check("建筑模式：机器表有 graphite-press × 1",
      /graphite-press/.test(txt("machines")) && />1</.test(txt("machines")), txt("machines").slice(0, 200));
check("建筑模式：产出卡片有石墨 0.667/s", /graphite/.test(txt("cards")) && /0\.667/.test(txt("cards")),
      txt("cards").slice(0, 240));
check("建筑模式：边界表含煤 1.333/s", /coal/.test(txt("demand")) && /1\.333/.test(txt("demand")),
      txt("demand").slice(0, 200));
check("建筑模式：复现命令指向 mbo calc",
      /mbo calc graphite:0\.667\/s/.test($("cmd").textContent) && /--force graphite=graphite-press/.test($("cmd").textContent),
      $("cmd").textContent);
check("递归树有层级（根是建筑、下有煤）",
      /graphite-press/.test(txt("tree")) && /coal/.test(txt("tree")) &&
      (txt("tree").match(/class="row"/g) || []).length >= 2, txt("tree").slice(0, 200));
check("机器表带图标", /<img class="ic/.test(txt("machines")) && /data:image\/png;base64/.test(txt("machines")));
check("边界表带物品图标", /<img class="ic/.test(txt("demand")));
check("建筑选择器：工厂 + 兵厂都在",
      (txt("bgrid-item").match(/class="bcell"/g) || []).length === 33 &&
      (txt("bgrid-unit").match(/class="bcell"/g) || []).length === 17,
      (txt("bgrid-item").match(/class="bcell"/g) || []).length + "/" + (txt("bgrid-unit").match(/class="bcell"/g) || []).length);
check("建筑贴图按原尺寸（graphite-press 2×2 → 44px）",
      /width:44px;height:44px/.test(txt("bgrid-item")), txt("bgrid-item").slice(0, 160));

/* --- 切到兵厂：ground-factory × 2 计划 dagger --- */
window.__ratio.block("ground-factory");
$("count").value = "2";
$("plan").value = "0";
$("plan").children = [makeEl("", "option"), makeEl("", "option"), makeEl("", "option")];
window.__ratio.run();
check("兵厂模式：机器表有 ground-factory × 2",
      /ground-factory/.test(txt("machines")) && />2</.test(txt("machines")), txt("machines").slice(0, 260));
check("兵厂模式：产出卡片是 dagger",
      /dagger/.test(txt("cards")) && /0\.133/.test(txt("cards")), txt("cards").slice(0, 260));
check("兵厂模式：走大循环（链表出现 T1/T5 两行）",
      /T1/.test(txt("chaintable")) && /T5/.test(txt("chaintable")), txt("chaintable").slice(0, 200));
check("兵厂模式：材料直接当边界输入（硅 1.333/s，不再展开硅炉）",
      /silicon/.test(txt("demand")) && /1\.333/.test(txt("demand")) && !/silicon-smelter/.test(txt("machines")),
      txt("demand").slice(0, 200));
check("兵厂模式：同型号兵厂只出现一次",
      txt("machines").split("<tr>").filter((r) => /ground-factory/.test(r)).length === 1,
      txt("machines").slice(0, 300));

/* --- 切回物品模式：graphite 1/s --- */
window.__ratio.setMode("item");
$("target").value = "graphite";
$("rate").value = "1";
window.__ratio.run();
check("物品模式：机器表 graphite-press × 2",
      /graphite-press/.test(txt("machines")) && />2</.test(txt("machines")), txt("machines").slice(0, 200));
check("物品模式：复现命令正确",
      /mbo calc graphite:1\/s/.test($("cmd").textContent), $("cmd").textContent);
check("物品模式：递归树有层级",
      /graphite-press/.test(txt("tree")) && (txt("tree").match(/class="row"/g) || []).length >= 2);
check("物品图标格有 22 个", (txt("grid").match(/class="cell"/g) || []).length === 22,
      String((txt("grid").match(/class="cell"/g) || []).length));

/* --- 递归层数可编辑：层数=1 时树里不再出现压机（上游被截断） --- */
$("depth").value = "1";
window.__ratio.run();
const tree1 = txt("tree");
check("递归层数=1：上游被截断成外部输入",
      /超过递归层数/.test(tree1) || /外部输入/.test(tree1), tree1.slice(0, 240));
$("depth").value = "6";
window.__ratio.run();

/* --- 新：外部来源（钻头 / 多产物）+ 供电表 + 兵厂 T1~T5 大循环 --- */
window.__ratio.setMode("building");
window.__ratio.block("graphite-press");
$("count").value = "2";
window.__ratio.run();
check("外部来源表：coal 可选来源", /data-src-item="coal"/.test(txt("sources")), txt("sources").slice(0, 200));
check("外部来源表：默认是接收", /接收/.test(txt("sources")), txt("sources").slice(0, 200));
check("供电表：有需要电力一行", /需要电力/.test(txt("powertable")), txt("powertable").slice(0, 160));
check("供电表：默认燃烧发电机（0 电 → 0 台）", /combustion|需要电力/.test(txt("powertable")));

window.__ratio.src("coal", { type: "drill", drill: "laser-drill", tiles: 8 });
check("钻头来源：机器表出现 laser-drill × 3",
      /laser-drill/.test(txt("machines")) && />3</.test(txt("machines")), txt("machines").slice(0, 300));
check("钻头来源：来源表显示单台 1.263/s",
      /1\.263/.test(txt("sources")), txt("sources").slice(0, 400));

const pt = window.__ratio.setGen("combustion-generator", "coal", 0);
check("供电表：燃烧发电机 4 台覆盖 198/s", /198/.test(pt) && /4/.test(pt), pt);
check("供电表：燃料煤 2 /s", /coal/.test(pt) && /2 \/s/.test(pt), pt);
const pt2 = window.__ratio.setGen("steam-generator", "coal", 2);
check("供电表：蒸汽发电机 2 台烧煤 1.333/s 并要水 12/s",
      /1\.333/.test(pt2) && /water/.test(pt2) && /12/.test(pt2), pt2);

const chainHtml = window.__ratio.chain("dagger", 0.05);
check("兵厂大循环：五级都在（ground-factory → reign）",
      /ground-factory/.test(chainHtml) && /additive-reconstructor/.test(chainHtml) &&
      /tetrative-reconstructor/.test(chainHtml) && /reign/.test(chainHtml), chainHtml.slice(0, 300));
check("兵厂大循环：T5 需要 12 台 tetrative", /12/.test(chainHtml) && /T5/.test(chainHtml));

window.__ratio.block("silicon-smelter");
$("count").value = "3";
window.__ratio.setBoundary("coal, sand");
window.__ratio.src("sand", { type: "multi", block: "disassembler" });
check("多产物来源：机器表出现 disassembler × 6",
      /disassembler/.test(txt("machines")) && />6</.test(txt("machines")), txt("machines").slice(0, 400));
check("多产物来源：副产物钍出现在来源表",
      /thorium/.test(txt("sources")) && /4\.8/.test(txt("sources")), txt("sources").slice(0, 500));

/* 钻头并入工厂配比：机器表写出采集量，计入工厂合计 */
window.__ratio.block("graphite-press");
$("count").value = "2";
window.__ratio.setBoundary("coal, sand");
window.__ratio.src("coal", { type: "drill", drill: "laser-drill", tiles: 8 });
check("钻头并入工厂配比：机器表有 laser-drill 且写采集量",
      /laser-drill/.test(txt("machines")) && /coal/.test(txt("machines")) &&
      /\/s/.test(txt("machines")), txt("machines").slice(0, 500));
check("钻头：不再显示「采集（见外部来源）」", !/见外部来源/.test(txt("machines")), txt("machines").slice(0, 300));

/* --- 液体需求表 --- */
window.__ratio.block("graphite-press");
$("count").value = "2";
window.__ratio.setBoundary("coal, sand");
window.__ratio.src("coal", { type: "import" });
window.__ratio.run();
check("液体需求表：没有液体时显示「无」",
      /无（不需要液体）/.test(txt("liquids")), txt("liquids").slice(0, 200));

window.__ratio.src("coal", { type: "drill", drill: "laser-drill", tiles: 8, boosted: true });
check("液体需求表：钻头加水后出现 water 4.8/s",
      /water/.test(txt("liquids")) && /4\.8/.test(txt("liquids")), txt("liquids").slice(0, 300));

/* --- 液体来源：抽水机（4.8/s 水 → rotary-pump 12/s 需要 1 台）--- */
window.__ratio.src("water", { type: "pump", pump: "rotary-pump" });
const liq2 = txt("liquids");
check("液体来源：水可以改成抽水机",
      /rotary-pump/.test(liq2) && /1 台/.test(liq2), liq2.slice(0, 400));
check("液体来源：抽水机电力计入机器表与合计",
      /rotary-pump/.test(txt("machines")) && /18/.test(txt("machines")), txt("machines").slice(0, 400));
window.__ratio.src("water", { type: "import" });

/* --- 兵厂链新口径：瓶颈 / 达成 / 台数不必 1:1 --- */
const chain2 = window.__ratio.chain("dagger", 0.05);
check("兵厂链：显示瓶颈标记与「实际达成」",
      /瓶颈/.test(chain2) && /实际达成/.test(chain2), chain2.slice(0, 400));
check("兵厂链：1 台 T4 能带 2.66 台 T5", /2\.66/.test(chain2), chain2.slice(0, 1500));
check("兵厂链：利用率列出现", /90%/.test(chain2), chain2.slice(0, 1500));


// 兵厂链挪到「按目标物品速率」页
check("兵厂链块属于建筑页（mode-block，不是 item 页）",
  /<div class="mode-block hidden" id="chainsec">/.test(html),
  (html.match(/.{0,80}chainsec.{0,120}/) || [""])[0]);

window.__ratio.block("graphite-press");
$("count").value = "1";
window.__ratio.run();
check("选中物品工厂时链块隐藏", (function () {
  const sec = $("chainsec");
  return sec.classList.contains("hidden") && $("chaintable").innerHTML === "";
})(), $("chainsec").className);

// 5t5 口径：5 台 T5 厂满效 → 自动反推 T4/T3/T2/T1
const top5 = window.__ratio.chainTop("dagger", 5, 5);
check("5t5：表里有「目标」标记", /目标/.test(top5.table), top5.table.slice(0, 200));
check("5t5：T5 台数 5", /<td class="num">5<\/td>/.test(top5.table), top5.table.slice(0, 800));
check("5t5：资源表有 silicon", /silicon/.test(top5.res), top5.res.slice(0, 300));
check("5t5：资源表每分钟列有 2537", /2537/.test(top5.res), top5.res.slice(0, 600));

// 外部入料方式：边界输入旁边有「灰带/蓝带/接收台」下拉
window.__ratio.block("graphite-press");
$("count").value = "2";
window.__ratio.run();
window.__ratio.src("coal", { type: "import", via: "belt-grey" });
check("入料方式：来源表出现灰带选项",
  /data-via-item="coal"/.test($("sources").innerHTML) && /灰带/.test($("sources").innerHTML),
  $("sources").innerHTML.slice(0, 400));
check("入料方式：灰带说明带条数", /条/.test($("sources").innerHTML), $("sources").innerHTML.slice(0, 800));

// 建筑页选兵厂：一台重建厂能升多条线时给「升级线」下拉
window.__ratio.block("tetrative-reconstructor");
$("count").value = "5";
window.__ratio.run();
check("升级线：多个候选时下拉出现", $("chainlinebar").style.display === "" &&
  $("chainline").innerHTML.split("<option").length - 1 > 1,
  $("chainline").innerHTML.slice(0, 300));
check("升级线：默认第一条是 dagger 线", /dagger/.test($("chainline").innerHTML),
  $("chainline").innerHTML.slice(0, 200));

$("chainline").value = "flare";
window.__ratio.run();
check("升级线：切到 flare 线后 T5 显示 eclipse",
  /eclipse/.test($("chaintable").innerHTML), $("chaintable").innerHTML.slice(0, 400));

// 只服务一条线的兵厂：下拉藏起来
window.__ratio.block("ground-factory");
$("count").value = "2";
window.__ratio.run();
check("升级线：候选只有一条时下拉隐藏", $("chainlinebar").style.display === "none",
  String($("chainlinebar").style.display));

// 外部入料：不给来源时默认蓝带（12.015/s），并给出条数
window.__ratio.setMode("item");
$("item").value = "silicon";
$("rate").value = "5";
window.__ratio.clearSources();
check("默认入料：来源下拉默认选中蓝带",
  /value="belt-blue" selected/.test($("sources").innerHTML),
  $("sources").innerHTML.slice(0, 600));
check("默认入料：蓝带显示条数（×1 条）",
  /蓝带[^<]*×1 条/.test($("sources").innerHTML), $("sources").innerHTML.slice(0, 900));
check("默认入料：合计吞吐 12.015/s",
  /12\.015/.test($("sources").innerHTML), $("sources").innerHTML.slice(0, 900));

// 发电设备：第三组选单 + 选中后只算发电量，不做电力递归
check("发电设备：建筑选单出现 14 个发电厂", ($("bgrid-power").innerHTML.match(/data-block=/g) || []).length === 14,
  String(($("bgrid-power").innerHTML.match(/data-block=/g) || []).length));
window.__ratio.block("steam-generator");
$("count").value = "2";
$("genfuel").value = "coal";
window.__ratio.setMode("building");
window.__ratio.run();
check("发电设备：卡片产出是「⚡ 电力 660/s」", /⚡[^<]*660\/s/.test(txt("cards")), txt("cards").slice(0, 400));
check("发电设备：供电表写总发电 660 且不做递归",
  /总发电[^<]*<\/td><td>660/.test(txt("powertable")) && /不做电力递归/.test(txt("powertable")),
  txt("powertable").slice(0, 600));
check("发电设备：煤在边界时机器清单只有发电机自己", /steam-generator/.test(txt("machines")) &&
  !/combustion-generator/.test(txt("machines")), txt("machines").slice(0, 400));
/* 用户 2026-11-09：其它工厂缺电不递归，但电厂当目标建筑时必须有递归树 */
window.__ratio.block("combustion-generator");
$("count").value = "2";
window.__ratio.setBoundary("sand");
window.__ratio.run();
check("发电厂树：煤不在边界时机器表出现上游离心机",
  /coal-centrifuge/.test(txt("machines")), txt("machines").slice(0, 600));
check("发电厂树：树里挂出煤的上游",
  /coal-centrifuge/.test(txt("tree")) || /coal/.test(txt("tree")), txt("tree").slice(0, 600));
window.__ratio.setBoundary("coal, sand");
window.__ratio.run();
check("发电厂树：煤回到边界后不再展开上游",
  !/coal-centrifuge/.test(txt("machines")), txt("machines").slice(0, 600));
window.__ratio.setBoundary("coal, sand");

/* --- 混合厂：多个目标合并算上游，共享产物只建一份 --- */
$("mixcount").value = "1";
window.__ratio.mix([["silicon-arc-furnace", 1], ["carbide-crucible", 1]]);
check("混合厂：模式切过去", window.__ratio.mode() === "mixed", window.__ratio.mode());
check("混合厂：输出区展开且目标清单有 2 项",
      !$("out").classList.contains("hidden") &&
      (($("mixlist").innerHTML.match(/chiptag/g) || []).length === 2), $("mixlist").innerHTML.slice(0, 300));
check("混合厂：共享石墨 10 台、分别建 11 台",
      /graphite/.test($("mixtable").innerHTML) && /×10</.test($("mixtable").innerHTML) &&
      /×11/.test($("mixtable").innerHTML), $("mixtable").innerHTML.slice(0, 1200));
check("混合厂：卡片写「对比分别建」省 1 台",
      /对比分别建/.test(txt("cards")) && /机器 −1/.test(txt("cards")), txt("cards").slice(0, 500));
check("混合厂：机器表含 10 台石墨压机",
      /graphite-press/.test(txt("machines")) && />10</.test(txt("machines")), txt("machines").slice(0, 400));
check("混合厂：等价命令是 cli --mix",
      /cli\.cjs --mix "/.test($("cmd").textContent) && /carbide-crucible:1/.test($("cmd").textContent),
      $("cmd").textContent);

// 目标互供抵扣：3 台石墨压机 + 1 台硅电弧炉（硅炉吃石墨 1.2/s），石墨全由目标自产
window.__ratio.mix([["graphite-press", 3], ["silicon-arc-furnace", 1]]);
check("混合厂：目标自产抵扣后不再建石墨压机（省 2 台）",
      /省 2/.test($("mixtable").innerHTML) && !/>10</.test(txt("machines")),
      $("mixtable").innerHTML.slice(0, 900));

// 发电设备当目标：只进清单，照样并入总电
window.__ratio.mix([["silicon-smelter", 2], ["combustion-generator", 1]]);
check("混合厂：发电设备当目标（电力 60、发电 60）",
      /60\/s/.test(txt("cards")) && /combustion-generator/.test(txt("machines")), txt("cards").slice(0, 400));

// 空清单不崩（会隐藏输出区）
window.__ratio.mix([]);
check("混合厂：空清单隐藏输出区且不报错", $("out").classList.contains("hidden"));

/* --- 液体自产：煤炭不允许外部输入时，自动带出煤炭处理线 --- */
window.__ratio.setMode("item");
$("target").value = "coal";
$("rate").value = "2";
window.__ratio.autoliq(true, "");
check("液体自产：带出煤炭分离机和石油钻井",
  /coal-centrifuge/.test(txt("machines")) && /oil-extractor/.test(txt("machines")), txt("machines").slice(0, 500));
check("液体自产：液体表写「自产」并带原版液体贴图",
  /自产/.test($("liquids").innerHTML) && /liqimg/.test($("liquids").innerHTML), $("liquids").innerHTML.slice(0, 800));
check("液体自产：水按泵台数换算（加和口径、富余优先：9/s → 小泵 2 台富余 5）",
  /小泵 2 台/.test($("liquids").innerHTML) && /合计 14\/s/.test($("liquids").innerHTML),
  $("liquids").innerHTML.slice(0, 1200));
check("液体自产：等价命令带 --liquids auto", /--liquids auto/.test($("cmd").textContent), $("cmd").textContent);
window.__ratio.autoliq(false, "");
check("关掉液体自产：回到只建分离机", !/oil-extractor/.test(txt("machines")), txt("machines").slice(0, 400));

/* --- 液体也是边界：煤炭分离机要的油能从边界接进来（就不建钻井了），边界表要带液体图标 --- */
window.__ratio.autoliq(false, "");
window.__ratio.setMode("item");
$("target").value = "coal";
$("rate").value = "2";
window.__ratio.run();
check("边界液体：煤炭分离机要油，默认按外部运入写在边界表里",
  /oil/.test(txt("demand")) && /（液体）/.test(txt("demand")), txt("demand").slice(0, 500));
check("边界液体：液体行带原版液体贴图", /liqimg/.test(txt("demand")), txt("demand").slice(0, 500));
check("边界液体：芯片列出 11 种液体", (txt("bndliqs").match(/data-bnd=/g) || []).length === 11,
  String((txt("bndliqs").match(/data-bnd=/g) || []).length));

window.__ratio.autoliq(true, "");
check("边界液体：开启自产时先建石油钻井", /oil-extractor/.test(txt("machines")), txt("machines").slice(0, 400));
window.__ratio.bnd("oil");
check("边界液体：把 oil 点进边界后不再建钻井（煤处理线到分离机为止）",
  !/oil-extractor/.test(txt("machines")) && /oil/.test(txt("demand")), txt("machines").slice(0, 400));
check("边界液体：芯片写着 oil 已选中", /class="chiptag on"[^>]*data-bnd="oil"/.test(txt("bndliqs")),
  txt("bndliqs").slice(0, 600));

/* 指定配方：选 silicon-crucible 就该按它的配方算（而不是自动挑硅电弧炉） */
window.__ratio.bnd();  // 保持当前边界
window.__ratio.setMode("item");
$("target").value = "silicon";
$("rate").value = "1";
window.__ratio.autoliq(false, "coal, sand");
window.__ratio.force("silicon", "silicon-crucible");
check("配方选择：指定 silicon-crucible 后机器表就是它",
  /silicon-crucible/.test(txt("machines")) && !/silicon-arc-furnace/.test(txt("machines")),
  txt("machines").slice(0, 400));
check("配方选择：等价命令带 --force",
  /--force silicon=silicon-crucible/.test($("cmd").textContent), $("cmd").textContent);

/* 多产物方块（分离机 / 解离机）进递归树 */
check("多产物：页面有「分离机/解离机参与递归」开关", /id="multichk"/.test(html));
check("多产物：配方下拉里能选到 separator",
  /value="separator"/.test(txt("forcelist")), txt("forcelist").slice(0, 600));

window.__ratio.setMode("item");
$("target").value = "lead";
$("rate").value = "2";
window.__ratio.autoliq(false, "coal, sand");
window.__ratio.multi(false);
check("多产物：默认 lead 仍走外部输入（机器表没有 separator）",
  !/separator/.test(txt("machines")), txt("machines").slice(0, 300));
window.__ratio.multi(true);
check("多产物：打开开关后 lead 由分离机产（5 台）",
  /separator/.test(txt("machines")) && />5</.test(txt("machines")), txt("machines").slice(0, 300));
check("多产物：递归树写出份额与顺带产物",
  /份额/.test(txt("tree")) && /顺带/.test(txt("tree")), txt("tree").slice(0, 500));

window.__ratio.multi(false);
$("target").value = "graphite";
$("rate").value = "1";
window.__ratio.force("graphite", "separator");
check("多产物：指定配方 separator 后机器表出现 separator",
  /separator/.test(txt("machines")), txt("machines").slice(0, 300));
check("多产物：指定配方时树节点带份额（1/6）", /份额 16\.7%/.test(txt("tree")), txt("tree").slice(0, 500));
window.__ratio.force("graphite", "");
window.__ratio.autoliq(false, "coal, sand");


/* 石油钻井：Fracker 满黑沙属性 = 0.25×60×1.5 = 22.5 油/s ⇒ 3 台煤炭分离机(18/s)只要 1 台钻井 */
window.__ratio.setMode("item");
$("target").value = "coal";
$("rate").value = "6";
window.__ratio.autoliq(true, "none, sand");
check("石油钻井：coal 6/s 只建 1 台 oil-extractor（3:1）",
  /oil-extractor/.test(txt("machines")) && /22\.5\/s/.test(txt("machines")), txt("machines").slice(0, 600));
check("吃料：机器表有「吃料/s」列，钻井那行写吃 sand",
  /吃料\/s/.test(txt("machines")) && /sand/.test(txt("machines")), txt("machines").slice(0, 800));
check("发电厂图标：外部电力换算行带发电机贴图",
  /外部电力换算/.test($("powertable").innerHTML) &&
  /<img[^>]+alt="(combustion|steam|differential)-generator"/.test($("powertable").innerHTML),
  $("powertable").innerHTML.slice(0, 600));

/* 油田属性（Attribute.oil）：页面上能改，改完钻井台数跟着变 */
check("油田属性：页面有 #oilfloor 输入框（默认 1.5）",
  !!$("oilfloor") && $("oilfloor").value === "1.5", $("oilfloor") && $("oilfloor").value);
window.__ratio.oilfloor(0.7);
check("油田属性：改成 0.7 后钻井变 2 台、单台 10.5 油/s",
  ((window.__ratio.last() || {}).machines || {})["oil-extractor"] === 2 &&
  /10\.5\/s/.test(txt("machines")), txt("machines").replace(/<img[^>]*>/g, "").slice(0, 400));
window.__ratio.oilfloor(1.5);
check("油田属性：调回 1.5 后钻井回到 1 台", /22\.5\/s/.test(txt("machines")),
  txt("machines").slice(0, 400));
window.__ratio.autoliq(false, "coal, sand");

/* 环境属性通用化 + 循环产线：页面也能表达（water 输入、液体来源下拉、树里 ⟲） */
check("环境属性：页面有 #waterfloor 输入框", !!$("waterfloor"));
check("环境属性：__ratio.attrs({oil:0.7}) 时钻井变 2 台、单台 10.5/s", (() => {
  $("target").value = "coal";
  $("rate").value = "6";
  window.__ratio.setBoundary("sand");
  window.__ratio.autoliq(true);
  window.__ratio.attrs({ oil: 0.7 });
  const m = (window.__ratio.last() || {}).machines || {};
  const each = ((window.__ratio.last() || {}).liquidFrom || {}).oil || {};
  return m["oil-extractor"] === 2 && Math.abs((each.perSecondEach || 0) - 10.5) < 1e-6;
})(), txt("machines"));
check("环境属性：__ratio.attrs(1.5) 回到 1 台、22.5/s", (() => {
  window.__ratio.attrs(1.5);
  const m = (window.__ratio.last() || {}).machines || {};
  const each = ((window.__ratio.last() || {}).liquidFrom || {}).oil || {};
  return m["oil-extractor"] === 1 && Math.abs((each.perSecondEach || 0) - 22.5) < 1e-6;
})(), txt("machines"));
check("液体来源：下拉里有「转化」选项（make）", (() => {
  /* 油改成外部运入 ⇒ 油那一行的下拉会列出所有来源：外部运入 / 石油钻井 / spore-press（转化） */
  $("target").value = "coal";
  $("rate").value = "6";
  window.__ratio.setBoundary("sand");
  window.__ratio.autoliq(false);
  window.__ratio.src("oil", { type: "import" });
  const h = txt("liquids");
  return /make:/.test(h) && /转化/.test(h);
})(), txt("liquids").slice(0, 600));
check("循环产线：石油走 spore-press、水走强化泵时树里出现 ⟲ 循环", (() => {
  $("target").value = "coal";
  $("rate").value = "6";
  window.__ratio.setBoundary("none");
  window.__ratio.autoliq(true);
  window.__ratio.liq("oil", "make:spore-press");
  window.__ratio.liq("water", "pump:reinforced-pump");
  const links = (window.__ratio.last() || {}).loops || [];
  const html = txt("tree") + " " + txt("warn");
  window.__ratio.liq("oil", "import");
  window.__ratio.liq("water", "import");
  return links.length >= 1 || /⟲/.test(html);
})(), txt("tree"));
check("循环产线：恢复默认后没有 ⟲", (() => {
  window.__ratio.autoliq(false);
  window.__ratio.setBoundary("coal, sand");
  window.__ratio.attrs(1.5);
  return !/⟲/.test(txt("tree"));
})(), txt("tree"));

check("归一化：勾上后压机 1.5 台、表里写「整台 2」", (() => {
  $("target").value = "graphite";
  $("rate").value = "1";
  window.__ratio.setBoundary("coal, sand");
  window.__ratio.autoliq(false);
  window.__ratio.flow(true);
  const m = (window.__ratio.last() || {}).machines || {};
  const h = txt("machines");
  return m["graphite-press"] === 1.5 && /1\.5/.test(h) && /整台 2/.test(h);
})(), txt("machines"));
check("归一化：关掉后回到 2 台", (() => {
  window.__ratio.flow(false);
  const m = (window.__ratio.last() || {}).machines || {};
  return m["graphite-press"] === 2 && window.__ratio.flow() === false;
})(), txt("machines"));

console.log(bad ? `\n${bad} 项失败` : "\n页面链路全部通过");
process.exit(bad ? 1 : 0);
