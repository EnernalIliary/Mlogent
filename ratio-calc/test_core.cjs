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
   [[1, "dagger", 2], [2, "mace", 1], [3, "fortress", 2], [4, "scepter", 5], [5, "reign", 12]]);
near("dagger 链总耗电", ch.power, 22944, 1);
near("dagger 链硅 111.22/s", ch.materials.silicon, 111.222222, 1e-3);
const ch2 = R.unitChain(DATA, "stell", 0.02);
eq("erekir stell 链三级", ch2.rows.map(r => [r.tier, r.unit, r.count]), [[1, "stell", 2], [2, "locus", 1], [3, "precept", 2]]);

console.log(f2 ? `\n${f2} 项新算法断言失败` : "\n新算法断言全部通过");
process.exit(bad || f2 ? 1 : 0);
