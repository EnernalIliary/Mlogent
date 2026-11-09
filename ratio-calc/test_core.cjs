/* 对拍：JS 内核 vs `python -m mbo calc`（同一份快照、同一套规则）
 * 用法：node ratio-calc/test_core.cjs
 */
const fs = require("fs");
const path = require("path");

const dir = __dirname;
global.window = global;
require(path.join(dir, "data", "gamedata.js"));
require(path.join(dir, "core.js"));

const DATA = global.MBO_DATA;
const R = global.RatioCore;
DATA.__index = R.buildIndex(DATA);

const cases = JSON.parse(fs.readFileSync(path.join(dir, "cases.json"), "utf8"));
let bad = 0;

function fmt(x) { return Number(x.toFixed(3)); }
function sortedObj(o) {
  const out = {};
  Object.keys(o).sort().forEach(k => { out[k] = fmt(o[k]); });
  return out;
}

for (const c of cases) {
  const res = R.expand(DATA, c.target, c.rate, c.boundary || [], c.force || {});
  const got = { machines: sortedObj(res.machines), demand: sortedObj(res.demand), power: fmt(res.power) };
  const want = { machines: sortedObj(c.expect.machines), demand: sortedObj(c.expect.demand), power: fmt(c.expect.power) };
  const ok = JSON.stringify(got) === JSON.stringify(want);
  if (!ok) {
    bad++;
    console.log("FAIL", c.label || c.target, "\n  got :", JSON.stringify(got), "\n  want:", JSON.stringify(want));
  } else {
    console.log("ok  ", c.label || (c.target + " " + c.rate + "/s"), JSON.stringify(got.machines));
  }
}
console.log(bad ? `\n${bad} 个不一致` : "\n全部一致");

/* ---------- 新算法单测：钻头 / 发电 / 多产物 / 兵厂大循环 ---------- */
let f2 = 0;
function near(name, got, want, tol) {
  tol = tol == null ? 1e-3 : tol;
  const ok = Math.abs(got - want) <= tol;
  if (!ok) f2++;
  console.log(ok ? "ok  " : "FAIL", name, "got", got, "want", want);
}
function eq(name, got, want) {
  const ok = JSON.stringify(got) === JSON.stringify(want);
  if (!ok) f2++;
  console.log(ok ? "ok  " : "FAIL", name, "got", JSON.stringify(got), "want", JSON.stringify(want));
}
function ok(name, cond, extra) {
  const good = !!cond;
  if (!good) f2++;
  console.log(good ? "ok  " : "FAIL", name, extra === undefined ? "" : extra);
}

// 钻头：60 * 矿格数 * speed² / delay，delay = (drillTime + hardnessMult*hardness)/mult
near("drillRate mechanical-drill/coal/8 格（煤硬度 2）", R.drillRate(DATA, "mechanical-drill", "coal", 8, false), 480 / 700);
near("drillRate laser-drill/coal/8 格（煤硬度 2）", R.drillRate(DATA, "laser-drill", "coal", 8, false), 1.263157894736842);
near("drillRate laser-drill/coal/8 格 + 水（×1.6²）", R.drillRate(DATA, "laser-drill", "coal", 8, true), 1.263157894736842 * 2.56);
near("drillRate blast-drill/copper/10 格 + 水（×1.8²）", R.drillRate(DATA, "blast-drill", "copper", 10, true),
     60 * 10 * (1.8 * 1.8) / (280 + 50 * 1));
eq("drillsNeeded coal 2.6667/s 用 laser-drill 8 格", R.drillsNeeded(DATA, "laser-drill", "coal", 2.6666667, 8, false).count, 3);

// 发电：台数按净发电算，燃料按 itemDuration/60 算
const g1 = R.generatorPlan(DATA, 198, "combustion-generator", "coal");
eq("燃烧发电机 198/s → 4 台", [g1.count, Math.round(g1.netEach)], [4, 60]);
near("燃烧发电机烧煤 2/s", g1.fuel.perSecond, 2);
const g2 = R.generatorPlan(DATA, 500, "steam-generator", "coal");
eq("蒸汽发电机 500/s → 2 台", [g2.count, Math.round(g2.netEach)], [2, 330]);
near("蒸汽发电机烧煤 1.333/s", g2.fuel.perSecond, 1.3333333, 1e-4);
near("蒸汽发电机要水 12/s", g2.liquids[0].perSecond, 12);
const g3 = R.generatorPlan(DATA, 7800, "impact-reactor", "blast-compound");
eq("冲击反应堆 7800/s → 2 台（自耗 1500）", [g3.count, Math.round(g3.netEach), Math.round(g3.selfUse)], [2, 6300, 1500]);
near("冲击反应堆烧爆炸混合物 0.857/s", g3.fuel.perSecond, 0.857142, 1e-4);
near("冲击反应堆要冷却液 30/s", g3.liquids[0].perSecond, 30);

// 多产物：加权随机一件 ⇒ share = amount/Σ
const sp = R.separatorPlan(DATA, "separator", 2);
near("分离机 2 台电力", sp.power, 132);
near("分离机 2 台要矿渣 8/s", sp.inputLiquids[0].perSecond, 8);
near("分离机 2 台铜 1.4286/s", sp.outputs.find(o => o.name === "copper").perSecond, 1.428571, 1e-4);
near("分离机 2 台钛 0.5714/s", sp.outputs.find(o => o.name === "titanium").perSecond, 0.571428, 1e-4);
const dp = R.separatorPlan(DATA, "disassembler", 1);
near("解离机 1 台钍 0.8/s", dp.outputs.find(o => o.name === "thorium").perSecond, 0.8);
near("解离机 1 台吃废料 4/s", dp.inputs.find(i => i.name === "scrap").perSecond, 4);

// 外部来源：把 demand 换成钻头/多产物
const bres = R.expandBuilding(DATA, "graphite-press", 2, { boundary: ["coal"], force: {} });
R.applySources(DATA, bres, { coal: { type: "drill", drill: "laser-drill", tiles: 8 } });
eq("来源=钻头：机器表含 3 台激光钻", [bres.machines["laser-drill"], bres.machines["graphite-press"]], [3, 2]);
near("来源=钻头：电力重算 198", bres.power, 198);
const mres = R.expandBuilding(DATA, "silicon-smelter", 3, { boundary: ["coal", "sand"], force: {} });
R.applySources(DATA, mres, { sand: { type: "multi", block: "disassembler" } });
eq("来源=解离机：6 台", [mres.machines["disassembler"], mres.machines["silicon-smelter"]], [6, 3]);
near("来源=解离机：电力 1530", mres.power, 1530);
near("来源=解离机：副产钍 4.8/s",
     mres.sources.find(s => s.item === "sand").byproducts.find(b => b.name === "thorium").perSecond, 4.8);

// 兵厂大循环 T1~T5
const ch = R.unitChain(DATA, "dagger", 0.05);
eq("dagger 链五级台数", ch.rows.map(r => [r.tier, r.unit, r.count]),
   [[1, "dagger", 1], [2, "mace", 1], [3, "fortress", 2], [4, "scepter", 5], [5, "reign", 12]]);
near("dagger 链实际达成 0.05/s", ch.achieved, 0.05, 1e-9);
eq("dagger 链瓶颈是最慢的 T5", ch.bottleneck, "reign");
near("dagger 链总耗电", ch.power, 22872, 1);
near("dagger 链硅 101.5/s", ch.materials.silicon, 101.5, 1e-3);
// 台数比例不必 1:1：1 台 T4 scepter（0.01111/s）够带 2.67 台 T5 reign（0.00417/s）
const t4 = ch.rows[3], t5 = ch.rows[4];
near("1 台 T4 带 2.67 台 T5", t4.feedsNext, 2.6667, 1e-3);
near("T4 单台 0.01111/s", t4.perSecond, 0.011111, 1e-5);
const ch2 = R.unitChain(DATA, "stell", 0.02);
eq("erekir stell 链三级", ch2.rows.map(r => [r.tier, r.unit, r.count]), [[1, "stell", 1], [2, "locus", 1], [3, "precept", 2]]);
eq("erekir 链瓶颈是 T1 stell", ch2.bottleneck, "stell");

// 抽水泵（液体来源）
const pp = R.pumpPlan(DATA, "water", 14.4, "rotary-pump");
eq("rotary-pump 补 14.4/s 水要 1 台", pp.count, 1);
near("rotary-pump 单台 48/s（2×2=4 格 × 0.2/tick × 60）", pp.perSecondEach, 48, 1e-4);
near("rotary-pump 1 台电 18/s", pp.power, 18, 1e-9);
eq("mechanical-pump 7/s 要 3 台", R.pumpPlan(DATA, "water", 14.4, "mechanical-pump").count, 3);
near("mechanical-pump 不耗电", R.pumpPlan(DATA, "water", 14.4, "mechanical-pump").power, 0, 1e-9);
const po = R.pumpPlan(DATA, "oil", 30, "oil-extractor");
eq("oil-extractor 补 30/s 油要 2 台", po.count, 2);
near("oil-extractor 2 台电 360/s", po.power, 360, 1e-9);
near("oil-extractor 2 台吃沙 2/s", po.inputs[0].perSecond, 2, 1e-9);
near("oil-extractor 2 台吃水 18/s", po.inputLiquids[0].perSecond, 18, 1e-9);
let thrown = null;
try { R.pumpPlan(DATA, "water", 1, "oil-extractor"); } catch (e) { thrown = e.message; }
ok("抽错液体要报错", !!(thrown && thrown.indexOf("oil") >= 0), thrown);

// 液体来源接进 expandBuilding：钻头加水 + 抽水机补
const wres = R.expandBuilding(DATA, "silicon-smelter", 3,
  { boundary: ["coal", "sand"], force: {},
    sources: { sand: { type: "drill", drill: "laser-drill", tiles: 8, boosted: true },
               water: { type: "pump", pump: "rotary-pump" } } });
near("抽水机：水需求 14.4/s", wres.liquids.find(l => l.name === "water").perSecond, 14.4, 1e-6);
eq("抽水机：补 1 台 rotary-pump", wres.machines["rotary-pump"], 1);
near("抽水机：电力 90+198+18 = 306", wres.power, 306, 1e-6);
eq("抽水机：liquidSources 有 1 条", (wres.liquidSources || []).length, 1);


// 兵厂链「5t5」口径：给台数（5 台 T5 厂满效），自动反推上面各级台数
const c5 = R.chainFromTop(DATA, "dagger", 5, 5);
eq("5t5：台数 1/1/1/2/5", c5.rows.map(r => r.count), [1, 1, 1, 2, 5]);
eq("5t5：topTier/topCount", [c5.topTier, c5.topCount], [5, 5]);
near("5t5：整链达成 5×0.004167（保留 3 位 0.021）", c5.achieved, 0.021, 1e-9);
eq("5t5：瓶颈是 reign", c5.bottleneck, "reign");
near("5t5：硅 42.292/s", c5.materials.silicon, 42.291666, 1e-4);
eq("3t4：T5 不参与（0 台）", R.chainFromTop(DATA, "dagger", 4, 3).rows.map(r => r.count), [1, 1, 1, 3, 0]);
eq("5t1：只有 T1", R.chainFromTop(DATA, "dagger", 1, 5).rows.map(r => r.count), [5, 0, 0, 0, 0]);

// 外部入料方式：灰带 / 布桥（要电）/ 接收台（不限速）
function graphiteWith(via) {
  const r = R.expand(DATA, "graphite", 1, ["coal", "sand"], {}, { maxDepth: 6 });
  R.applySources(DATA, r, { coal: { type: "import", via: via } });
  return r;
}
const gGrey = graphiteWith("belt-grey");
const coalGrey = gGrey.sources.filter(s => s.item === "coal")[0];
eq("灰带：煤 2.667/s 要 1 条", coalGrey.count, 1);
near("灰带：单条 5.25/s", coalGrey.perSecondEach, 5.25, 1e-9);
near("灰带：不耗电", gGrey.power, 0, 1e-9);
const gBlue = graphiteWith("belt-blue");
eq("蓝带：单条 12.015/s", gBlue.sources.filter(s => s.item === "coal")[0].perSecondEach, 12.015);
const gPhase = graphiteWith("phase-bridge");
near("布桥：电力 18 计入总量", gPhase.power, 18, 1e-9);
const gPad = graphiteWith("pad");
eq("接收台：不限速（台数留空）", gPad.sources.filter(s => s.item === "coal")[0].count, null);
eq("入料方式共 7 种", (DATA.channels || []).length, 7);

// 建筑页选兵厂 → chainFromBlock（和页面/CLI 同一条路）
const candT = R.chainsForBlock(DATA, "tetrative-reconstructor");
eq("chainsForBlock(tetrative)：多条线可选", candT.length > 1, true);
eq("chainsForBlock 首选 dagger 线", candT[0].start, "dagger");
eq("chainsForBlock：tetrative 在第 5 级", candT[0].tier, 5);
const cb1 = R.chainFromBlock(DATA, "ground-factory", 2);
eq("chainFromBlock(ground-factory ×2)：台数 [2,0,0,0,0]", cb1.rows.map(r => r.count), [2, 0, 0, 0, 0]);
eq("chainFromBlock：topTier 1", cb1.topTier, 1);
near("chainFromBlock：电力 144", cb1.power, 144, 1e-9);
const cb2 = R.chainFromBlock(DATA, "tetrative-reconstructor", 5);
eq("chainFromBlock(tetrative ×5)：1/1/1/2/5", cb2.rows.map(r => r.count), [1, 1, 1, 2, 5]);
eq("chainFromBlock 默认走 dagger", cb2.start, "dagger");
const cb3 = R.chainFromBlock(DATA, "tetrative-reconstructor", 5, { chainStart: "flare" });
eq("chainFromBlock 指定 flare 线", cb3.start, "flare");
eq("flare 线 T5 是 eclipse", cb3.rows[4].unit, "eclipse");
eq("chainFromBlock(物品工厂) 返回 null", R.chainFromBlock(DATA, "graphite-press", 1), null);

/* ---- 发电设备当目标建筑（按台数算发电，不做电力递归） ---- */
const gen1 = R.expandGenerator(DATA, "steam-generator", 2);
near("expandGenerator(steam ×2)：发电 660/s", gen1.products[0].rate, 660, 1e-9);
eq("expandGenerator：产出类型是 power", gen1.products[0].type, "power");
near("expandGenerator：烧煤 1.333/s", gen1.demand.coal, 1.333, 1e-6);
near("expandGenerator：抽水 12/s", gen1.liquids[0].perSecond, 12, 1e-9);
near("expandGenerator：自身不计耗电", gen1.power, 0, 1e-9);
near("expandGenerator：supply.netTotal 660", gen1.supply.netTotal, 660, 1e-9);
near("expandGenerator：单台净发电 330", gen1.supply.netEach, 330, 1e-9);
const gen2 = R.expandBuilding(DATA, "combustion-generator", 1);
near("expandBuilding(combustion ×1) 走发电分支：60/s", gen2.products[0].rate, 60, 1e-9);
const gen3 = R.expandGenerator(DATA, "impact-reactor", 2, { fuel: "blast-compound" });
near("expandGenerator(impact ×2, blast-compound)：12600/s", gen3.products[0].rate, 12600, 1e-9);
near("expandGenerator(impact)：单台自耗 1500/s", gen3.supply.selfUseEach, 1500, 1e-9);
near("expandGenerator(impact)：两台自耗 3000/s", gen3.supply.selfUse, 3000, 1e-9);
near("expandGenerator(impact)：净发电已扣自耗", gen3.supply.netEach, 6300, 1e-9);

/* ---- 混合厂：多个目标合并算上游，共享中间产物只建一份 ---- */
const MIXB = { boundary: ["coal", "sand", "tungsten"] };   // 与网页/CLI 的默认边界同口径
const mix1 = R.expandMixed(DATA, [
  { block: "silicon-arc-furnace", count: 1 },
  { block: "carbide-crucible", count: 1 }
], MIXB);
eq("expandMixed：模式是 mixed", mix1.mode, "mixed");
eq("expandMixed：目标数 2", mix1.targets.length, 2);
eq("expandMixed：石墨压机合并后 10 台", mix1.machines["graphite-press"], 10);
near("expandMixed：石墨需求合计 6.655/s", mix1.shared.filter(s => s.item === "graphite")[0].need, 6.655, 1e-3);
eq("expandMixed：分别建要 11 台石墨压机", mix1.compare.detail["graphite-press"], 11);
eq("expandMixed：省 1 台", mix1.compare.savedMachines, 1);
near("expandMixed：电力 420/s", mix1.power, 420, 1e-9);
near("expandMixed：边界 coal 13.31/s", mix1.demand.coal, 13.31, 1e-2);

// 目标互供：3 台石墨压机自产 2/s 石墨，硅电弧炉只吃 1.2/s ⇒ 不再另建石墨压机
const mix2 = R.expandMixed(DATA, [
  { block: "graphite-press", count: 3 },
  { block: "silicon-arc-furnace", count: 1 }
], MIXB);
eq("expandMixed：目标自产后不再建石墨压机", mix2.machines["graphite-press"] || 0, 3);
eq("expandMixed：石墨被目标抵扣完（stillNeed 0）",
   mix2.internals.filter(i => i.item === "graphite")[0].stillNeed, 0);
eq("expandMixed：分别建 6 台 → 混合 4 台（省 2 台）", mix2.compare.machinesMixed, 4);
eq("expandMixed：省 2 台", mix2.compare.savedMachines, 2);

// 发电设备当目标：只进清单，并入总电，不做电力递归
const mix3 = R.expandMixed(DATA, [
  { block: "silicon-smelter", count: 2 },
  { block: "combustion-generator", count: 1 }
], MIXB);
near("expandMixed：电力 60/s", mix3.power, 60, 1e-9);
near("expandMixed：发电 60/s", mix3.powerOut, 60, 1e-9);
near("expandMixed：净电 0", mix3.netPower, 0, 1e-9);

// 兵厂不能进混合厂（自带 T1→T5 大循环）
let mixBoom = null;
try { R.expandMixed(DATA, [{ block: "ground-factory", count: 1 }]); } catch (e) { mixBoom = e.message; }
eq("expandMixed：兵厂给出明确报错", /兵厂/.test(mixBoom || ""), true);

// 液体自产：煤炭不在外部输入时，coal-centrifuge 要吃 oil ⇒ 自动接石油钻井（煤炭处理线）
const liq1 = R.expand(DATA, "coal", 2, [], {}, { liquids: "auto" });
eq("液体自产：带出煤炭分离机", liq1.machines["coal-centrifuge"], 1);
eq("液体自产：带出液体钻井", liq1.machines["oil-extractor"], 1);
eq("液体自产：oil 记在 liquidFrom 里", (liq1.liquidFrom.oil || {}).block, "oil-extractor");
near("液体自产：oil 自产速率 15/s", liq1.liquidFrom.oil.perSecondEach, 15, 1e-9);
eq("液体自产：oil 不再算外部净需求", (liq1.liquidNet || []).filter(l => l.name === "oil").length, 0);
near("液体自产：电力含钻井 252/s（水走 2 台机械泵不耗电）", liq1.power, 252, 1e-9);

// 换成孢子压缩路线：liquid oil=make ⇒ spore-press（吃 spore-pod），再往上展开种植机
const liq2 = R.expand(DATA, "coal", 2, [], {}, { liquids: "auto", liquid: { oil: "make" } });
eq("液体自产（转化）：用 spore-press", liq2.machines["spore-press"] >= 1, true);
eq("液体自产（转化）：不再用石油钻井", liq2.machines["oil-extractor"] || 0, 0);
eq("液体自产（转化）：spore-pod 由种植机带出", liq2.machines["cultivator"] >= 1, true);

// 不开液体自产时保持旧行为：只建分离机，oil 仍是外部需求
const liq3 = R.expand(DATA, "coal", 2, [], {}, {});
eq("不开启时只建分离机", liq3.machines["coal-centrifuge"], 1);
eq("不开启时 oil 仍是外部净需求", (liq3.liquidNet || []).filter(l => l.name === "oil").length, 1);

// 泵换算：液体需求按"几台泵"计量（小泵→中泵→大泵），水有 5 种泵可用
const eqs = R.pumpEquivalents(DATA, "water", 630);
eq("泵换算：水有 5 种泵", eqs.length, 5);

/* 液体也是边界：oil 写进 boundary 就不该再抽/压，煤炭处理线到分离机为止 */
{
  const b1 = R.expand(DATA, "coal", 2, ["oil"], {}, { liquids: "auto" });
  eq("边界液体：oil 在边界里就不建石油钻井", b1.machines["oil-extractor"] || 0, 0);
  eq("边界液体：oil 仍算外部净需求", (b1.liquidNet || []).filter(function (l) { return l.name === "oil"; }).length, 1);
  const b2 = R.expand(DATA, "coal", 2, [], {}, {});
  eq("边界液体：不开自产时 oil 也在净需求里（按外部运入）",
     (b2.liquidNet || []).filter(function (l) { return l.name === "oil"; }).length, 1);
}
eq("泵换算：按每秒从少到多排（第一个是最小的地下水抽取器 6.6）", eqs[0].perSecondEach, 6.6);
eq("泵换算：地下水抽取器要 96 台", eqs[0].count, 96);
eq("泵换算：小泵（机械泵 7/s）要 90 台", (eqs.find(p => p.pump === "mechanical-pump") || {}).count, 90);
eq("泵换算：中泵（回转泵 48/s）要 14 台", (eqs.find(p => p.pump === "rotary-pump") || {}).count, 14);
eq("泵换算：大泵（脉冲泵 118.8/s）要 6 台", (eqs.find(p => p.pump === "impulse-pump") || {}).count, 6);
eq("泵换算：油只有钻井一种", R.pumpEquivalents(DATA, "oil", 6).length, 1);

/* 出液量单位回归：dump 的 outputLiquids 是 per-tick，每秒 = amount×60（不是 ×cyclesPerSecond） */
{
  const press = DATA.blocks.filter(b => b.name === "spore-press")[0];
  near("孢子压缩机 18 油/s（amount 0.3/tick × 60）", press.output_liquids[0][1], 18, 1e-6);
  const melter = DATA.blocks.filter(b => b.name === "melter")[0];
  near("熔炉 12 渣/s（amount 0.2/tick × 60）", melter.output_liquids[0][1], 12, 1e-6);
}
/* 孢子路线配比：培养基 : 压缩 : 分离 = 5 : 1 : 3（用户口里的"513"） */
{
  const r = R.expand(DATA, "coal", 6, [], {}, { liquids: "auto", liquid: { oil: "make" } });
  eq("孢子线 3 台分离机 → 培养基 5 / 压缩 1",
     [r.machines["coal-centrifuge"], r.machines["cultivator"], r.machines["spore-press"]], [3, 5, 1]);
}

/* 泵的"加和"计量：最终结果是几台小泵 + 几台中泵 + 几台大泵 */
{
  /* 口径（用户 2026-11-09）：先让富余尽量小，富余相同再比台数 */
  const m9 = R.pumpMix(DATA, "water", 9);
  eq("泵加和：9/s → 小泵 2 台（14/s，富余 5）", [m9.count, m9.pumps[0].pump, m9.total, m9.extra],
     [2, "mechanical-pump", 14, 5]);
  const m18 = R.pumpMix(DATA, "water", 18);
  eq("泵加和：18/s → 小泵 3 台（21/s，富余 3）", [m18.count, m18.pumps[0].pump, m18.total, m18.extra],
     [3, "mechanical-pump", 21, 3]);
  const m90 = R.pumpMix(DATA, "water", 90);
  near("泵加和：90/s 凑整不富余（合计 90）", m90.total, 90, 1e-4);
  near("泵加和：90/s 富余 0", m90.extra, 0, 1e-4);
}
/* 外部电力按"几台发电厂"计量（与泵同一套逻辑：先富余小，再台数少） */
{
  const p646 = R.powerMix(DATA, 646);
  eq("外部电力：646/s → 蒸汽 2 台", [p646.gens[0].block, p646.gens[0].count], ["steam-generator", 2]);
  eq("外部电力：646/s 合计 660（富余 14）", [p646.total, p646.extra], [660, 14]);
  const p1080 = R.powerMix(DATA, 1080);
  eq("外部电力：1080/s → 差速 1 台（不富余）",
     [p1080.gens[0].block, p1080.gens[0].count, p1080.extra], ["differential-generator", 1, 0]);
}
/* 钻头不是「外部来源」里的另一类，它就是工厂配比里的一员：机器行要写清采集什么、每秒多少 */
{
  const dr = R.expand(DATA, "graphite", 1, ["coal", "sand"], {},
                      { sources: { coal: { type: "drill", drill: "laser-drill", tiles: 8 } } });
  const rows = R.machineRows(DATA, dr);
  const lr = rows.filter(r => r.name === "laser-drill")[0];
  ok("钻头并入工厂配比：机器表有 laser-drill", !!lr, JSON.stringify(rows.map(r => r.name)));
  ok("钻头：机器行写采集 coal（3 台补 2.667/s 需求）",
        !!lr && lr.outItems.length === 1 && lr.outItems[0].name === "coal" &&
        Math.abs(lr.outItems[0].perSecond - 3.789) < 0.01 &&
        /^采集 coal 3\.789\/s$/.test(lr.outputs[0]),
        lr ? JSON.stringify(lr.outItems) + " " + JSON.stringify(lr.outputs) : "");
  ok("钻头：电力计入工厂总电力（3 × 66 = 198，不是单列一类）", Math.abs(dr.power - 198) < 1.5, String(dr.power));
}
function s2sum(m) { return m.pumps.reduce((a, p) => a + p.count, 0); }

console.log(f2 ? `\n${f2} 项新算法断言失败` : "\n新算法断言全部通过");
process.exit(bad || f2 ? 1 : 0);
