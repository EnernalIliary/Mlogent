#!/usr/bin/env node
/* 配比计算器命令行 —— 给 bot / 脚本用，算法与网页共用 core.js（单一真相源）。
 *
 * 用法示例：
 *   node ratio-calc/cli.cjs --item graphite --rate 1
 *   node ratio-calc/cli.cjs --block graphite-press --count 2
 *   node ratio-calc/cli.cjs --item silicon --rate 5 --src sand=drill:laser-drill:8 --src coal=import
 *   node ratio-calc/cli.cjs --item silicon --rate 5 --gen combustion-generator --genfuel coal
 *   node ratio-calc/cli.cjs --item graphite --rate 1 --format json
 *   node ratio-calc/cli.cjs --chain dagger --chainrate 0.05
 *   node ratio-calc/cli.cjs --list
 */
"use strict";

const path = require("path");

const DIR = __dirname;

/* 没给 --boundary 时的默认外部输入：和网页一致（煤、沙）。
 * --boundary all  = 所有"挖出来的矿"都算外部输入（铜铅煤沙废钛钍铍钨）
 * --boundary none = 全都不算，任何有配方的物品都会自己造
 */
const DEFAULT_BOUNDARY = ["coal", "sand"];
const RAW_BOUNDARY = ["copper", "lead", "coal", "sand", "scrap", "titanium",
                      "thorium", "beryllium", "tungsten"];

function loadData(dataFile) {
  global.window = global;
  require(dataFile || path.join(DIR, "data", "gamedata.js"));
  require(path.join(DIR, "core.js"));
  const DATA = global.MBO_DATA;
  if (!DATA) throw new Error("数据没加载成功（data/gamedata.js 应设置 window.MBO_DATA）");
  DATA.__index = global.RatioCore.buildIndex(DATA);
  return { DATA: DATA, R: global.RatioCore, idx: DATA.__index };
}

/* ---------------- 参数解析 ---------------- */

function parseArgs(argv) {
  const out = { src: [], _: [] };
  /* 可重复的参数（--src 可以出现多次，各记一条）
   * --liquid / --liquidname / --attr 也允许多次出现（各 液体=方式、物品=属性），
   * 早先只认 --src，写两条 --liquid 时后者会把前者覆盖掉（oil=make 就丢了，退回到自动选泵）。 */
  const REPEAT = { src: true, liquid: true, liquidname: true, attr: true };
  const set = (key, val) => {
    if (REPEAT[key]) { if (!Array.isArray(out[key])) out[key] = []; out[key].push(val); }
    else out[key] = val;
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith("--")) { out._.push(a); continue; }
    const key = a.slice(2);
    const eq = key.indexOf("=");
    if (eq >= 0) { set(key.slice(0, eq), key.slice(eq + 1)); continue; }
    const next = argv[i + 1];
    if (next === undefined || next.startsWith("--")) set(key, true);
    else { set(key, next); i++; }
  }
  return out;
}

function num(v, dflt) {
  if (v === undefined || v === true || v === "") return dflt;
  const n = Number(v);
  if (!Number.isFinite(n)) throw new Error("不是数字：" + v);
  return n;
}

function csv(v) {
  if (!v || v === true) return [];
  return String(v).split(",").map(s => s.trim()).filter(Boolean);
}

function parseForce(v) {
  const force = {};
  csv(v).forEach(pair => {
    const i = pair.indexOf("=");
    if (i < 0) return;
    force[pair.slice(0, i).trim()] = pair.slice(i + 1).trim();
  });
  return force;
}

/* --src sand=drill:laser-drill:8:1  或  --src scrap=multi:disassembler 或 --src coal=import */
/* 外部运入的默认入料方式：跟 core.js 的 DEFAULT_CHANNEL 保持一致（蓝带） */
const DEFAULT_CHANNEL = "belt-blue";

/* --attr oil=0.7,water=1.2  环境属性（Attribute.*）
 * 抽液方块的产量取决于它看的地板属性：Fracker(oil) 22.5@1.5、SolidPump(water) 6.6@0。
 * 不传就是数据里的默认值（oil 满黑沙 1.5；water 0 = 无属性地面）。 */
function parseAttrs(spec) {
  const out = {};
  if (!spec) return out;
  const spec2 = Array.isArray(spec) ? spec.join(",") : String(spec);
  spec2.split(",").forEach(part => {
    const s2 = part.trim();
    if (!s2) return;
    const eq = s2.indexOf("=");
    if (eq < 0) throw new Error("--attr 格式：名字=数值（如 oil=0.7,water=1.2）：" + s2);
    const k = s2.slice(0, eq).trim();
    const v = Number(s2.slice(eq + 1));
    if (!isFinite(v) || v < 0) throw new Error("--attr " + k + " 的数值不对：" + s2);
    out[k] = v;
  });
  return out;
}

/* 把属性渲染成人话：oil 0.7（oil-extractor 10.5/s）、water 1（water-extractor 13.2/s） */
function attrText(env, attrs) {
  if (!attrs) return "";
  const idx2 = env.R.applyAttrs(env.idx, attrs);
  return Object.keys(attrs).sort().map(k => {
    let best = null;
    idx2.pumps.forEach(pp => {
      if (pp.attribute !== k || !(pp.perSecond > 0)) return;
      if (!best || pp.perSecond > best.perSecond) best = pp;
    });
    return k + " " + fmtNum(attrs[k]) + (best ? "（" + best.name + " " + fmtNum(best.perSecond) + "/s）" : "");
  }).join("、");
}

function parseSources(list) {
  if (!list) list = [];
  if (!Array.isArray(list)) list = [list];
  const cfg = {};
  list.forEach(spec => {
    const eq = spec.indexOf("=");
    if (eq < 0) throw new Error("--src 格式：item=type:参数…（" + spec + "）");
    const item = spec.slice(0, eq).trim();
    const parts = spec.slice(eq + 1).split(":").map(s => s.trim());
    const type = parts[0];
    if (type === "import") cfg[item] = { type: "import" };
    else if (type === "drill") cfg[item] = {
      type: "drill", drill: parts[1] || "laser-drill",
      tiles: parts[2] ? Number(parts[2]) : 8,
      boosted: parts[3] === undefined ? true : !(parts[3] === "0" || parts[3] === "false")
    };
    else if (type === "multi") cfg[item] = { type: "multi", block: parts[1] || "separator" };
    else if (type === "pump") cfg[item] = { type: "pump", pump: parts[1] || "mechanical-pump" };
    else if (type === "belt") cfg[item] = { type: "import", via: parts[1] || DEFAULT_CHANNEL };
    else throw new Error("未知来源类型：" + type + "（import / drill / multi / pump / belt）");
  });
  return cfg;
}

/* 链结果 → 统一 JSON 形状（--chain 与 --block <兵厂> 都走这里，避免两份实现） */
function chainResult(env, ch, count) {
  const R = env.R;
  const machines = {};
  ch.rows.forEach(r => { if (r.count > 0) machines[r.block] = (machines[r.block] || 0) + r.count; });
  const mine = ch.rows.filter(r => r.tier === ch.topTier)[0];
  /* 链的材料也要按"外部入料"过一遍，卡片/JSON 才能显示蓝带条数 */
  const tmp = { machines: Object.assign({}, machines), demand: ch.materials, liquidExtra: {}, extraPower: 0 };
  R.applySources(env.DATA, tmp, {});
  const beltPower = tmp.extraPower || 0;
  return {
    mode: "chain", chain: ch,
    target: ch.start + " → " + ch.top,
    requested: { topCount: count, topTier: ch.topTier },
    products: [{ name: mine ? mine.unit : ch.top, type: "unit", rate: mine ? mine.capacity : ch.achieved }],
    machines: Object.keys(machines).sort().map(name => {
      const b = R.anyBlock(env.idx, name);
      return {
        name, count: machines[name], kind: b ? b.kind : "unit",
        icon: b ? (b.icon || "") : "", size: b ? b.size : 0,
        powerEach: b ? b.power : 0, powerTotal: b ? b.power * machines[name] : 0,
        outItems: [], outputs: []
      };
    }),
    demand: Object.keys(ch.materials).sort().map(k => ({ name: k, perSecond: ch.materials[k] })),
    sources: tmp.sources || [],
    power: ch.power + beltPower
  };
}

/* ---------------- 查询 ---------------- */

/* --mix "silicon-smelter:2,graphite-press:3" → [{block,count}]（第三段可选，兵厂的生产计划号） */
function parseMix(v) {
  if (!v || v === true) throw new Error("--mix 要写成 block:count,block:count（例如 silicon-smelter:2,graphite-press:3）");
  const list = String(v).split(",").map(s => s.trim()).filter(Boolean).map(spec => {
    const p = spec.split(":").map(x => x.trim());
    if (!p[0]) throw new Error("--mix 里有一段没写方块名：" + spec);
    const count = p[1] === undefined || p[1] === "" ? 1 : Number(p[1]);
    if (!Number.isFinite(count) || count <= 0) throw new Error("--mix 台数要大于 0：" + spec);
    return { block: p[0], count: count, plan: p[2] ? Number(p[2]) : 0 };
  });
  if (!list.length) throw new Error("--mix 至少要一个目标");
  return list;
}

/* 液体自产参数
 *   --liquids auto              机器吃的液体没人供时自动接钻井（没有钻井就用转化方块）
 *   --liquid oil=make           逐种指定方式：auto | pump | make | import
 *   --liquid oil=make:spore-press  方式 + 方块名
 *   --liquidname oil=spore-press   只指定方块名（方式仍按 auto 判）
 * 只传 --liquid / --liquidname 时会自动把 --liquids 打开。 */
function liquidOptions(opts) {
  const out = {};
  const on = opts.liquids !== undefined && opts.liquids !== true
    ? String(opts.liquids) : (opts.liquids === true ? "auto" : "");
  if (on && on !== "off" && on !== "no") out.liquids = on;
  const how = {}, name = {};
  csv(opts.liquid).forEach(spec => {
    const m = /^([^=]+)=([^:]+)(?::(.+))?$/.exec(String(spec));
    if (!m) throw new Error("--liquid 要写成 液体=方式[:方块名]（例如 oil=make 或 oil=make:spore-press）");
    how[m[1].trim()] = m[2].trim();
    if (m[3]) name[m[1].trim()] = m[3].trim();
  });
  csv(opts.liquidname).forEach(spec => {
    const p = String(spec).split("=");
    if (p.length !== 2) throw new Error("--liquidname 要写成 液体=方块名（例如 oil=spore-press）");
    name[p[0].trim()] = p[1].trim();
  });
  if (Object.keys(how).length) { out.liquid = how; out.liquids = out.liquids || "auto"; }
  if (Object.keys(name).length) { out.liquidName = name; out.liquids = out.liquids || "auto"; }
  return out;
}

function query(opts) {
  const env = loadData(opts.data);
  const DATA = env.DATA, R = env.R, idx = env.idx;
  const given = csv(opts.boundary);
  // 没写 --boundary 时，默认和网页一致（煤、沙当外部输入），避免算出 oil→coal 这种绕路链
  let boundary;
  if (!given.length) boundary = DEFAULT_BOUNDARY.slice();
  else if (given.length === 1 && (given[0] === "all" || given[0] === "raw")) boundary = RAW_BOUNDARY.slice();
  else if (given.length === 1 && given[0] === "none") boundary = [];
  else boundary = given;
  const force = parseForce(opts.force);
  const depth = num(opts.depth, 12);
  /* 环境属性：--attr oil=0.7,water=1.2（通用）；--oilfloor 0.7 是 attrs.oil 的旧写法。
   * 抽液方块每秒 = pumpAmount×60×(validTiles+属性)，所以属性一变台数就变。 */
  const attrOpts = parseAttrs(opts.attr);
  const oilFloor = num(opts.oilfloor, 0);
  if (oilFloor > 0) attrOpts.oil = oilFloor;
  const attrsOn = Object.keys(attrOpts).length ? attrOpts : null;
  const oilFloorVal = (attrsOn && attrsOn.oil != null) ? attrsOn.oil : ((env.idx && env.idx.oilFloor) || 1.5);
  const sources = parseSources(opts.src || []);
  const liqOpts = liquidOptions(opts);
  /* --multi：允许分离机/解离机自动参与递归（默认关，否则铜/铅/钛会被自动改建成吃矿渣的分离机） */
  const multiOn = opts.multi === true || opts.multi === "on" || opts.multi === "1" || opts.multi === "yes";
  /* --flow：归一化模式（学 TMI）——台数不向上取整，给"满效等价的分数台数"，速率全部按每秒守恒 */
  const flowOn = opts.flow === true || opts.flow === "on" || opts.flow === "1" || opts.flow === "yes";

  const res = {
    ok: true, snapshot: DATA.snapshot || "", mode: null, target: null, requested: null,
    products: [], inputs: [], machines: [], demand: [], liquids: [], power: 0,
    warnings: [], sources: [], liquidSources: [], supply: null, chain: null,
    flow: flowOn
  };

  if (opts.chain) {
    /* 快捷写法：--chain dagger --chainexpr 5t5 → 等价于"选 T5 兵厂 + 台数 5"，同一条装配路径 */
    const expr = opts.chainexpr !== undefined ? String(opts.chainexpr) : null;
    const m = expr ? /^(\d+(?:\.\d+)?)\s*[x×*]?\s*t\s*([1-5])$/i.exec(expr.trim()) : null;
    let ch;
    if (m) {
      ch = R.chainFromTop(DATA, String(opts.chain), parseInt(m[2], 10), parseFloat(m[1]));
      Object.assign(res, chainResult(env, ch, parseFloat(m[1])));
    } else {
      const rate = num(opts.chainrate !== undefined ? opts.chainrate : opts.rate, 0.05);
      ch = R.unitChain(DATA, String(opts.chain), rate);
      const out = Object.assign(res, chainResult(env, ch, ch.topCount || null));
      out.requested = rate;
    }
  }

  if (res.mode === "chain") {
    /* 兵厂链：chainResult 已经装好，这里只等下面统一补图标（不能再 return，否则图标会缺） */
  } else if (opts.mix) {
    /* 混合厂：多个目标（物品工厂 / 发电设备）合并算上游，共享中间产物只建一份 */
    const targets = parseMix(opts.mix);
    const r = R.expandMixed(DATA, targets, Object.assign({
      boundary: boundary, force: force, maxDepth: depth, sources: sources, multi: multiOn,
      attrs: attrsOn, flow: flowOn
    }, liqOpts));
    res.mode = "mixed";
    res.targets = r.targets.map(t => ({
      block: t.block, count: t.count, kind: t.kind,
      products: (t.products || []).map(p => ({ name: p.name, type: p.type, rate: round(p.rate) })),
      inputs: (t.inputs || []).map(i => ({ name: i.name, amount: round(i.amount) })),
      power: round(t.power), powerOut: round(t.powerOut)
    }));
    res.target = targets.map(t => t.block + "×" + t.count).join(" + ");
    res.requested = targets.reduce((a, t) => a + t.count, 0);
    res.products = r.products;
    res.inputs = r.inputs;
    res.machines = flattenMachines(DATA, R, r);
    res.demand = Object.keys(r.demand).sort().map(k => ({ name: k, perSecond: r.demand[k] }));
    res.power = r.power;
    res.powerOut = r.powerOut;
    res.netPower = r.netPower;
    res.shared = (r.shared || []).map(s => Object.assign({}, s));
    res.internals = r.internals || [];
    res.compare = r.compare || null;
    res.liquids = r.liquids || [];
    res.warnings = r.warnings || [];
    res.sources = r.sources || [];
    res.liquidSources = r.liquidSources || [];
    res.liquidFrom = r.liquidFrom || {};
    res.liquidNet = r.liquidNet || [];
    res.byproducts = r.byproducts || [];
  res.loops = r.loops || [];
  res.cycles = r.cycles || [];
  } else if (opts.block) {
    const count = num(opts.count, 1);
    /* 选中的是兵厂 → 直接走 T1→T5 大循环（和页面「按目标建筑台数」一致） */
    const selB = env.idx ? R.anyBlock(env.idx, String(opts.block)) : null;
    if (selB && selB.kind === "unit") {
      const planIdx = num(opts.plan, 0);
      const line = selB.plans && selB.plans[planIdx] ? selB.plans[planIdx].unit : (opts.chainline ? String(opts.chainline) : null);
      const ch = R.chainFromBlock(DATA, String(opts.block), count, line ? { chainStart: line } : null);
      if (ch) return attachIcons(Object.assign(res, chainResult(env, ch, count)));
    }
    const r = R.expandBuilding(DATA, String(opts.block), count, Object.assign({
      boundary: boundary, force: force, maxDepth: depth,
      plan: num(opts.plan, 0), sources: sources,
      fuel: opts.genfuel ? String(opts.genfuel) : null, multi: multiOn,
      attrs: attrsOn, flow: flowOn
    }, liqOpts));
    res.mode = "building";
    res.target = String(opts.block);
    res.requested = count;
    res.products = r.products || [];
    res.inputs = r.inputs || [];
    res.machines = flattenMachines(DATA, R, r);
    res.demand = Object.keys(r.demand || {}).sort().map(k => ({ name: k, perSecond: r.demand[k] }));
    res.power = r.power || 0;
    res.supply = r.supply || null;
    res.liquids = r.liquids || [];
    res.warnings = r.warnings || [];
    res.sources = r.sources || [];
    res.liquidSources = r.liquidSources || [];
    res.liquidFrom = r.liquidFrom || {};
    res.liquidNet = r.liquidNet || [];
    res.byproducts = r.byproducts || [];
  res.loops = r.loops || [];
  res.cycles = r.cycles || [];
    if (r.planTotal > 1) res.warnings.push("该兵厂有 " + r.planTotal + " 个生产计划，用的是第 " + (r.plan + 1) + " 个（--plan 可换）");
  } else if (opts.item) {
    const rate = num(opts.rate, 1);
    const r = R.expand(DATA, String(opts.item), rate, boundary, force,
      Object.assign({ maxDepth: depth, sources: sources, multi: multiOn,
        attrs: attrsOn, flow: flowOn }, liqOpts));
    res.mode = "item";
    res.target = String(opts.item);
    res.requested = rate;
    res.products = [{ name: String(opts.item), type: "item", rate: r.achieved || 0 }];
    res.machines = flattenMachines(DATA, R, r);
    res.demand = Object.keys(r.demand || {}).sort().map(k => ({ name: k, perSecond: r.demand[k] }));
    res.power = r.power || 0;
    res.supply = r.supply || null;
    res.liquids = r.liquids || [];
    res.warnings = r.warnings || [];
    res.sources = r.sources || [];
    res.liquidSources = r.liquidSources || [];
    res.liquidFrom = r.liquidFrom || {};
    res.liquidNet = r.liquidNet || [];
    res.byproducts = r.byproducts || [];
  res.loops = r.loops || [];
  res.cycles = r.cycles || [];
  } else {
    throw new Error("要给 --item <物品> --rate <每秒> 或 --block <方块> --count <台数>");
  }

  if (opts.gen) {
    const demand = num(opts.gendemand, res.power);
    if (demand <= 0) {
      res.warnings.push("电力需求是 0，不需要发电厂（可用 --gendemand 手填要覆盖的电力）");
    } else {
      const plan = R.generatorPlan(DATA, demand, String(opts.gen), opts.genfuel ? String(opts.genfuel) : "");
      const manual = num(opts.gencount, 0);
      res.supply = manual > 0
        ? R.generatorSupply(DATA, String(opts.gen), opts.genfuel ? String(opts.genfuel) : "", manual)
        : plan;
      if (manual > 0 && manual * res.supply.netEach < demand) {
        res.warnings.push("手填台数 " + manual + " 不够覆盖 " + round(demand) + "/s 电力（差 "
          + round(demand - manual * res.supply.netEach) + "/s）");
      }
    }
  }
  res.warnings = Array.from(new Set(res.warnings));
  res.attrs = attrsOn;
  res.oilFloor = oilFloorVal;
  /* render 层没有 env，这里先渲染好；默认也写 oil 口径（1.5），否则石油钻井的 22.5 看不出出处 */
  res.attrText = attrText(env, attrsOn || { oil: oilFloorVal });
  /* machines 可能是 {名:台数} 也可能是 attach 前的行数组，两种都认 */
  var mNames = Array.isArray(res.machines)
    ? res.machines.map(function (m) { return m.name; })
    : Object.keys(res.machines || {});
  res.usesAttr = mNames.some(function (n) {
    var p = env.idx.pumps.get(n);
    return !!(p && p.attribute);
  });
  return attachIcons(res);
}

/* 给产出/边界输入/液体补图标（卡片渲染和 bot 富文本都用得上）。
 * 液体没有贴图，icon 留空、另给 color 让卡片画色点。 */
function attachIcons(res) {
  const env = loadData();
  const idx = env.idx, DATA = env.DATA;
  res.products.forEach(p => { p.icon = iconOfIndex(idx, p.name, p.type); });
  /* 多产物方块的副产：也补图标（卡片/富文本里一目了然） */
  (res.byproducts || []).forEach(b => { b.icon = iconOfIndex(idx, b.name, "item"); });
  res.demand.forEach(d => { d.icon = iconOfIndex(idx, d.name, "item"); });
  const paint = (l) => {
    /* 原版液体贴图：sprites/items/liquid-<名>.png（export_data 已内联） */
    l.icon = (idx.liquidIcons && idx.liquidIcons[l.name]) || "";
    const meta = (idx.liquidColors && idx.liquidColors[l.name]) || null;
    if (meta) l.color = meta;
  };
  (res.liquids || []).forEach(paint);
  (res.liquidNet || []).forEach(paint);
  Object.keys(res.liquidFrom || {}).forEach(k => paint(res.liquidFrom[k]));
  if (res.liquidSources) res.liquidSources.forEach(paint);
  res.liquidColors = (idx && idx.liquidColors) || {};
  res.liquidIcons = (idx && idx.liquidIcons) || {};
  /* 泵换算：水这类液体按"几台泵"计量更直观（小泵→中泵→大泵） */
  res.liquidEquiv = {};
  const amountOf = {};
  (res.liquidNet && res.liquidNet.length ? res.liquidNet : (res.liquids || [])).forEach(l => {
    amountOf[l.name] = l.perSecond;
  });
  Object.keys(res.liquidFrom || {}).forEach(k => {
    const a = res.liquidFrom[k];
    if (amountOf[k] === undefined) amountOf[k] = round((a.count || 0) * (a.perSecondEach || 0));
  });
  res.pumps = {};
  res.machines.forEach(m => { if (idx.pumps.has(m.name)) res.pumps[m.name] = m.count; });
  res.pumpMix = {};
  /* flow（归一化）模式下液体已经用小数台数精确表示，整数泵换算会自相矛盾（"小数 1.03 台" vs "整台 2 台"） */
  if (env.R && env.R.pumpMix && !res.flow) {
    Object.keys(amountOf).forEach(name => {
      const mix = env.R.pumpMix(DATA, name, amountOf[name], res.attrs);
      if (mix) res.pumpMix[name] = mix;
    });
  }
  if (res.supply && res.supply.fuel) res.supply.fuel.icon = iconOfIndex(idx, res.supply.fuel.name, "item");
  /* 液体自产来源做成"能用图标就用图标"：方块图标给钻井/转化方块，parts 里每档泵也带图标 */
  const blockIcon = (name) => {
    const b = env.R && env.R.anyBlock ? env.R.anyBlock(idx, name) : null;
    return (b && b.icon) || "";
  };
  Object.keys(res.liquidFrom || {}).forEach(k => {
    const a = res.liquidFrom[k];
    a.icon = (idx.liquidIcons && idx.liquidIcons[k]) || "";
    a.blockIcon = blockIcon(a.block);
    (a.parts || []).forEach(pt => { pt.icon = blockIcon(pt.pump); });
  });
  (res.liquidSources || []).forEach(src => { src.icon = (idx.liquidIcons && idx.liquidIcons[src.liquid]) || ""; src.pumpIcon = blockIcon(src.pump); });
  /* 外部电力：自己没发电（或发电不够）时要接进来的电，按"几台发电厂"计量（与泵同一套逻辑） */
  res.powerMix = null;
  const imported = round((res.power || 0) - (res.powerOut || 0));
  if (env.R && env.R.powerMix && imported > 1e-9) {
    const pm = env.R.powerMix(DATA, imported);
    if (pm) {
      /* 发电厂图标：页面/卡片渲染"外部电力换算"要用 */
      (pm.gens || []).forEach(g => { g.icon = blockIcon(g.block); });
      res.powerMix = pm;
    }
  }
  return res;
}

/* 「电力 646/s ≈ 蒸汽发电机 2 台（合计 660/s，富余 14/s）」 */
function powerMixText(mix) {
  if (!mix || !mix.gens || !mix.gens.length) return "";
  const parts = mix.gens.map(g => g.block + " " + g.count + " 台");
  return "电力 " + fmtNum(mix.need) + "/s ≈ " + parts.join(" + ") +
    "（合计 " + fmtNum(mix.total) + "/s" + (mix.extra > 1e-6 ? "，富余 " + fmtNum(mix.extra) + "/s" : "") + "）";
}

/* 泵的叫法：机械泵=小泵、回转泵=中泵、脉冲泵=大泵；其它泵写自己的特点 */
const PUMP_LABEL = {
  "mechanical-pump": "小泵",
  "rotary-pump": "中泵",
  "impulse-pump": "大泵",
  "reinforced-pump": "强化泵",
  "water-extractor": "地下水抽取器",
  "oil-extractor": "石油钻井"
};

/* 台数文案：整数原样，小数两位（flow 归一化下 1.03 台这种） */
function fmtCnt(c) {
  const n = round(c);
  return Number.isInteger(n) ? String(n) : String(Math.round(n * 100) / 100);
}

/* 自产来源的文字：单一方块 → "oil-extractor ×1（钻井，22.5/s）"；多档泵 → "大泵 45 台 + 中泵 3 台" */
function selfText(s) {
  if (!s) return "";
  if (s.parts && s.parts.length) {
    const sum = s.parts.reduce((a, p) => a + p.count * p.perSecondEach, 0);
    return s.parts.map(p => (PUMP_LABEL[p.pump] || p.pump) + " " + fmtCnt(p.count) + " 台").join(" + ")
      + "（钻井合计 " + fmtNum(sum) + "/s）";
  }
  const kind = s.type === "make" ? "转化方块" : "钻井";
  return s.block + " ×" + fmtCnt(s.count) + "（" + kind + " " + fmtNum(s.perSecondEach) + "/s）";
}

/* 「water 630/s ≈ 大泵 45 台 + 中泵 3 台（合计 630/s）」——按"几台小泵 + 几台中泵 + 几台大泵"加和计量 */
function mixText(name, mix) {
  if (!mix || !mix.pumps || !mix.pumps.length) return "";
  const parts = mix.pumps.map(p => (PUMP_LABEL[p.pump] || p.pump) + " " + fmtCnt(p.count) + " 台");
  return name + " " + fmtNum(mix.need) + "/s ≈ " + parts.join(" + ") +
    "（合计 " + fmtNum(mix.total) + "/s" + (mix.extra > 1e-6 ? "，富余 " + fmtNum(mix.extra) + "/s" : "") + "）";
}

/* 「water 630/s ≈ 小泵 90 台（mechanical-pump）/ 中泵 53 台（rotary-pump）/ 大泵 48 台（impulse-pump）」 */
function equivText(name, eq) {
  if (!eq || !eq.pumps || !eq.pumps.length) return "";
  if (eq.pumps.length === 1) return "";   /* 只有一种泵（比如石油只有钻井）不必换算 */
  return name + " " + fmtNum(eq.need) + "/s ≈ " + eq.pumps.map(p => {
    const label = PUMP_LABEL[p.pump] || p.pump;
    const extra = p.pump === "reinforced-pump" ? "，要氢"
      : p.pump === "water-extractor" ? "，要地下水"
      : "";
    return label + " " + p.count + " 台（" + p.pump + " " + fmtNum(p.perSecondEach) + "/s" + extra + "）";
  }).join(" / ");
}

function iconOfIndex(idx, name, type) {
  if (!idx) return "";
  if (type === "unit") return (idx.unitIcons && idx.unitIcons[name]) || "";
  return (idx.itemIcons && idx.itemIcons.get(name)) || "";
}

function flattenMachines(DATA, R, r) {
  const idx = R.indexOf(DATA);
  const rows = R.machineRows(DATA, r) || [];
  return rows.map(x => ({
    name: x.name, count: x.count, kind: x.kind, icon: x.icon || "",
    countCeil: x.countCeil, eff: x.eff, flow: !!x.flow,
    powerEach: round(x.powerEach), powerTotal: round(x.powerTotal), rateEach: round(x.rateEach),
    outItems: (x.outItems || []).map(o => ({
      name: o.name, type: o.type, perSecond: round(o.perSecond), icon: iconOfIndex(idx, o.name, o.type)
    })),
    /* 吃料：钻井吃 sand/water、离心机吃 oil —— 以前只进递归不显示，容易被当成"没算" */
    inItems: (x.inItems || []).map(i => ({
      name: i.name, type: i.type, perSecond: round(i.perSecond), icon: iconOfIndex(idx, i.name, i.type)
    }))
  }));
}

function round(x) { return Math.round((x || 0) * 1000) / 1000; }

/* JSON 给 bot 用：默认把 base64 图标剔掉（一条命令能省几百 KB），--icons 可保留 */
function stripIcons(v) {
  if (Array.isArray(v)) return v.map(stripIcons);
  if (v && typeof v === "object") {
    const o = {};
    Object.keys(v).forEach(k => {
      if (k === "icon" || k === "blockIcon" || k === "unitIcon"
        || k === "liquidIcons" || k === "liquidColors") return;
      o[k] = stripIcons(v[k]);
    });
    return o;
  }
  return v;
}

/* ---------------- 输出 ---------------- */

function fmtNum(x) {
  const n = round(x);
  return Number.isInteger(n) ? String(n) : String(n);
}

/* flow（归一化）模式下台数是小数（满效等价值）：显示两位小数；整台模式仍是整数台数。 */
function fmtCount(m) {
  const c = (m && m.count != null) ? m.count : 0;
  if (!(m && m.flow)) return String(Math.round(c * 1000) / 1000);
  return String(Math.round(c * 100) / 100);
}

/* flow 下"只建整台的话，每台实际跑多少效率" */
function effNote(m) {
  if (!(m && m.flow)) return "";
  const ceil = m.countCeil || Math.ceil(m.count - 1e-9);
  if (!(ceil > 0) || Math.abs(ceil - m.count) < 1e-9) return "";
  return "（整台 " + ceil + " 台 ⇒ 每台 " + (Math.round(m.count / ceil * 1000) / 10) + "%）";
}

function renderText(res) {
  const L = [];
  if (res.mode === "chain") {
    const c = res.chain;
    L.push("兵厂大循环：" + c.start + " → " + c.top + "，目标 " +
      (c.topCount != null
        ? c.topCount + " 台 T" + c.topTier + "（≈ " + fmtNum(c.rate) + "/s）"
        : fmtNum(c.rate) + " 台/s"));
    c.rows.forEach(r => {
      const it = (r.items || []).filter(i => i.perSecond > 0);
      L.push("  T" + r.tier + "  " + r.block + " ×" + r.count
        + (r.count > 0 ? "  → " + r.unit + " " + fmtNum(r.actual) + "/s" : "（不建）")
        + (it.length ? "（" + it.map(i => i.name + " " + fmtNum(i.perSecond) + "/s").join("、") + "）" : ""));
    });
    L.push("  合计：" + c.rows.reduce((a, r) => a + r.count, 0) + " 台兵厂，电力 " + fmtNum(c.power) + "/s");
    if (c.bottleneck) {
      L.push("  整链实际达成 " + fmtNum(c.achieved) + "/s（受最慢的 T" + c.bottleneckTier + " " + c.bottleneck + " 限制）");
    }
    c.rows.forEach((r, i) => {
      if (r.count > 0 && r.feedsNext && c.rows[i + 1] && c.rows[i + 1].count > 0) {
        L.push("  比例：1 台 T" + r.tier + " " + r.unit + " 能带 " + fmtNum(r.feedsNext)
          + " 台 T" + c.rows[i + 1].tier + " " + c.rows[i + 1].unit
          + "（台数不必 1:1，按各自建造时间算）");
      }
    });
    const mats = Object.keys(c.materials).filter(k => c.materials[k] > 0);
    if (mats.length) {
      L.push("  材料：" + mats.map(k => k + " " + fmtNum(c.materials[k]) + "/s").join("、"));
      L.push("  材料（每分钟）：" + mats.map(k => k + " " + fmtNum(c.materials[k] * 60) + "/min").join("、"));
    }
    return L.join("\n");
  }
  const head = res.mode === "building"
    ? "配比：" + res.target + " ×" + fmtNum(res.requested) + "（建筑模式，满效）"
    : res.mode === "mixed"
      ? "混合厂：" + res.target + "（" + res.targets.length + " 个目标，合并算上游，共享产物只建一份）"
      : "配比：" + res.target + " " + fmtNum(res.requested) + "/s（物品模式）";
  L.push(head);
  if (res.mode === "mixed" && res.targets) {
    res.targets.forEach(t => {
      const outs = (t.products || []).map(p => p.name + " " + fmtNum(p.rate) + "/s").join("、");
      const ins = (t.inputs || []).map(i => i.name + " " + fmtNum(i.amount) + "/s").join("、");
      L.push("  · " + t.block + " ×" + t.count + (outs ? " → " + outs : "")
        + (ins ? "（吃 " + ins + "）" : "") + (t.powerOut ? "（发电 " + fmtNum(t.powerOut) + "/s）" : ""));
    });
  }
  if (res.products.length) {
    L.push("  产出：" + res.products.map(p => p.name + " " + fmtNum(p.rate) + "/s").join("、"));
  }
  const pumps = res.pumps || {};
  const fac = res.machines.filter(m => !pumps[m.name]);
  const pl = res.machines.filter(m => pumps[m.name]);
  if (fac.length) {
    fac.forEach(m => {
      let line = "  " + m.name + " ×" + fmtCount(m) + effNote(m);
      if (m.powerTotal) line += "（电 " + fmtNum(m.powerTotal) + "/s）";
      if (m.inItems && m.inItems.length) {
        line += "，吃 " + m.inItems.map(i => i.name + " " + fmtNum(i.perSecond) + "/s").join(" + ");
      }
      /* 产出一律写出来（之前物品工厂不写：看不到 pulverizer → sand，
       * 就会误以为「油井吃的沙没算进去」） */
      if (m.outItems && m.outItems.length) {
        line += " → " + m.outItems.map(o => o.name + " " + fmtNum(o.perSecond) + "/s").join("、");
      }
      L.push(line);
    });
  }
  const total = fac.reduce((a, m) => a + m.count, 0);
  L.push("  工厂合计：" + (res.flow ? Math.round(total * 100) / 100 : total) + " 台，电力 " + fmtNum(res.power) + "/s" +
         (pl.length ? "（含抽水 " + fmtNum(pl.reduce((a, m) => a + (m.powerTotal || 0), 0)) + "/s）" : "") +
         (res.mode === "mixed" && res.powerOut ? "，厂内发电 " + fmtNum(res.powerOut) +
           "/s，净 " + fmtNum(res.netPower) + "/s" : ""));
  if (pl.length) {
    L.push("  抽水：" + pl.map(m => m.name + " ×" + fmtCount(m) + effNote(m)
      + (m.powerTotal ? "（电 " + fmtNum(m.powerTotal) + "/s）" : "")
      + (m.inItems && m.inItems.length
        ? "，吃 " + m.inItems.map(i => i.name + " " + fmtNum(i.perSecond) + "/s").join(" + ") : "")).join(" + "));
  }
  if (res.flow) L.push("  归一化：台数为满效等价值（可为小数），数量按每秒守恒；整台建时每台效率 = 小数台数 / 向上取整");
  if (res.powerMix) L.push("  外部电力：" + powerMixText(res.powerMix));
  if (res.mode === "mixed" && res.shared && res.shared.length) {
    const hit = res.shared.filter(s => s.saved > 0);
    res.shared.forEach(s => {
      let line = "  共享 " + s.item + "：" + s.block + " ×" + s.mixedCount + "（混合）";
      if (s.fromTargets > 0) line += "，目标自产抵扣 " + fmtNum(s.fromTargets) + "/s";
      if (s.separateCount) line += "，分别建要 ×" + s.separateCount + (s.saved ? "（省 " + s.saved + " 台）" : "");
      L.push(line);
    });
    if (res.compare) {
      L.push("  对比分别建：机器 " + res.compare.machinesSeparate + " → " + res.compare.machinesMixed +
             "（省 " + res.compare.savedMachines + "），占地 " + res.compare.tilesSeparate + " → " +
             res.compare.tilesMixed + "（省 " + res.compare.savedTiles + " 格）" +
             (res.compare.savedPower ? "，电力省 " + fmtNum(res.compare.savedPower) + "/s" : ""));
    }
    if (!hit.length) L.push("  （这组目标没有共享的中间产物，混合只省了取整误差）");
  }
  /* 边界输入：物品 + 液体一起列（液体也是边界，不列出来就不知道煤处理线断在哪一环） */
  const needLiq = Array.isArray(res.liquidNet) ? res.liquidNet : (res.liquids || []);
  if (res.demand.length || needLiq.length) {
    const items = res.demand.map(d => d.name + " " + fmtNum(d.perSecond) + "/s");
    const liqs = needLiq.map(d => {
      const pump = (res.liquidSources || []).filter(s => s.liquid === d.name)[0];
      return d.name + " " + fmtNum(d.perSecond) + "/s（液体" + (pump ? "，" + pump.pump + " 抽" : "，外部运入") + "）";
    });
    L.push("  边界输入：" + items.concat(liqs).join("、"));
  }
  /* 液体自产（--liquids auto）：oil ← oil-extractor / spore-press 这类 */
  Object.keys(res.liquidFrom || {}).forEach(k => {
    L.push("  液体自产：" + k + " ← " + selfText(res.liquidFrom[k]));
  });
  Object.keys(res.pumpMix || {}).forEach(k => {
    const t = mixText(k, res.pumpMix[k]);
    if (t) L.push("  泵换算：" + t);
  });
  /* 环境属性：显式给了属性、或场上有吃属性的抽液方块（石油钻井/抽水机）时提一句 */
  if (res.attrs || res.usesAttr) {
    L.push("  环境属性：" + (res.attrText || ("oil " + fmtNum(res.oilFloor))));
  }
  if ((res.byproducts || []).length) {
    L.push("  顺带产物：" + res.byproducts.map(b => b.name + " " + fmtNum(b.perSecond) + "/s").join("、")
      + "（多产物方块副产，不算进需求）");
  }
  (res.liquidSources || []).forEach(s => {
    let line = "  液体 " + s.liquid + " ← " + s.pump + " ×" + s.count
      + "（单台 " + fmtNum(s.perSecondEach) + "/s，合计 " + fmtNum(s.perSecondTotal) + "/s";
    if (s.power) line += "，电 " + fmtNum(s.power) + "/s";
    if (s.inputs && s.inputs.length) line += "，吃 " + s.inputs.map(i => i.name + " " + fmtNum(i.perSecond)).join("、");
    if (s.inputLiquids && s.inputLiquids.length) line += "，吃 " + s.inputLiquids.map(i => i.name + " " + fmtNum(i.perSecond)).join("、");
    line += "）";
    L.push(line);
  });
  if (res.sources && res.sources.length) {
    res.sources.forEach(s => {
      let line = "  来源 " + s.item + " ← ";
      if (s.type === "import") {
        if (s.via) {
          const idx2 = loadData().idx;
          const ch = idx2.channelsByKey.get(s.via);
          line += (ch ? ch.label : s.via) +
            (s.count == null ? "（不限速）"
              : " ×" + s.count + " 条（单条 " + fmtNum(s.perSecondEach) + "/s，合计 "
                + fmtNum(s.perSecondTotal) + "/s" + (s.power ? "，电 " + fmtNum(s.power) + "/s" : "") + "）");
        } else line += "外部运入";
      }
      else if (s.type === "drill") {
        line += s.drill + " ×" + s.count + "（" + s.tiles + " 格矿"
          + (s.boosted ? "，加水" : "，不加水") + "，单台 " + fmtNum(s.perSecondEach) + "/s）";
      } else if (s.type === "multi") {
        line += s.block + " ×" + s.count + "（电 " + fmtNum(s.power) + "/s，副产 "
          + (s.byproducts || []).map(b => b.name + " " + fmtNum(b.perSecond)).join("、") + "）";
      }
      L.push(line);
    });
  }
  if (res.supply) {
    const s = res.supply;
    let line = "  供电：" + s.name + " ×" + s.count + "（净 " + fmtNum(s.netTotal) + "/s";
    if (s.netEach !== s.netTotal / Math.max(1, s.count)) line += "";
    if (s.fuel) line += "，烧 " + s.fuel.name + " " + fmtNum(s.fuel.perSecond) + "/s";
    if (s.liquids && s.liquids.length) line += "，" + s.liquids.map(l => l.name + " " + fmtNum(l.perSecond) + "/s").join("、");
    line += "）";
    L.push(line);
  }
  if (res.warnings.length) res.warnings.forEach(w => L.push("  ⚠ " + w));
  return L.join("\n");
}

function renderMarkdown(res) {
  const L = [];
  if (res.mode === "chain") {
    const c = res.chain;
    L.push("**兵厂大循环：" + c.start + " → " + c.top + "（" +
      (c.topCount != null
        ? c.topCount + " 台 T" + c.topTier + " ≈ " + fmtNum(c.rate) + "/s"
        : fmtNum(c.rate) + " 台/s") + "）**");
    L.push("");
    L.push("| 层级 | 方块 | 台数 | 产物 | 材料/s |");
    L.push("|---|---|---|---|---|");
    c.rows.forEach(r => {
      L.push("| T" + r.tier + " | " + r.block + " | " + r.count + " | " + r.unit + " " + fmtNum(r.actual) + "/s | "
        + (r.items.length ? r.items.map(i => i.name + " " + fmtNum(i.perSecond)).join("<br>") : "—") + " |");
    });
    L.push("");
    L.push("合计电力 **" + fmtNum(c.power) + "/s**");
    if (c.bottleneck) {
      L.push("");
      L.push("整链实际达成 **" + fmtNum(c.achieved) + "/s**，受最慢的 T" + c.bottleneckTier
        + " " + c.bottleneck + " 限制；台数不必 1:1（按各自建造时间算）。");
    }
    return L.join("\n");
  }
  L.push("**" + (res.mode === "building"
    ? "配比：" + res.target + " ×" + fmtNum(res.requested)
    : res.mode === "mixed"
      ? "混合厂：" + res.target + "（" + res.targets.length + " 个目标，合并算上游）"
      : "配比：" + res.target + " " + fmtNum(res.requested) + "/s") + "**");
  L.push("");
  if (res.mode === "mixed" && res.targets) {
    L.push("| 目标 | 台数 | 产出/s | 吃料/s |");
    L.push("|---|---|---|---|");
    res.targets.forEach(t => {
      L.push("| " + t.block + " | " + t.count + " | " +
        ((t.products || []).map(p => p.name + " " + fmtNum(p.rate)).join("<br>") || "—") + " | " +
        ((t.inputs || []).map(i => i.name + " " + fmtNum(i.amount)).join("<br>") || "—") + " |");
    });
    L.push("");
  }
  if (res.products.length) L.push("产出：" + res.products.map(p => p.name + " " + fmtNum(p.rate) + "/s").join("、"));
  L.push("");
  L.push("| 建筑 | 台数 | 电力/s |");
  L.push("|---|---|---|");
  res.machines.forEach(m => L.push("| " + m.name + " | " + m.count + " | " + (m.powerTotal ? fmtNum(m.powerTotal) : "—") + " |"));
  L.push("");
  if (res.mode === "mixed" && res.compare) {
    L.push("电力 **" + fmtNum(res.power) + "/s**" +
      (res.powerOut ? "，厂内发电 " + fmtNum(res.powerOut) + "/s，净 **" + fmtNum(res.netPower) + "/s**" : "") +
      "；对比分别建：机器 " + res.compare.machinesSeparate + " → " + res.compare.machinesMixed +
      "（省 " + res.compare.savedMachines + "），占地 " + res.compare.tilesSeparate + " → " +
      res.compare.tilesMixed + " 格（省 " + res.compare.savedTiles + "）。");
    const sh = (res.shared || []).filter(s => s.separateCount && s.saved > 0);
    if (sh.length) {
      L.push("");
      L.push("共享产物（混合只建一份）：" + sh.map(s =>
        s.item + " ×" + s.mixedCount + "（分别建 ×" + s.separateCount + "，省 " + s.saved + "）").join("、"));
    }
    L.push("");
  }
  const needLiqMd = Array.isArray(res.liquidNet) ? res.liquidNet : (res.liquids || []);
  if (res.demand.length || needLiqMd.length) {
    const items = res.demand.map(d => d.name + " " + fmtNum(d.perSecond) + "/s");
    const liqs = needLiqMd.map(d => d.name + " " + fmtNum(d.perSecond) + "/s（液体）");
    L.push("边界输入：" + items.concat(liqs).join("、"));
  }
  Object.keys(res.liquidFrom || {}).forEach(k => {
    L.push("液体自产：" + k + " ← " + selfText(res.liquidFrom[k]));
  });
  Object.keys(res.pumpMix || {}).forEach(k => {
    const t = mixText(k, res.pumpMix[k]);
    if (t) L.push("泵换算：" + t);
  });
  if (res.flow) L.push("归一化：台数为满效等价值（可为小数），数量按每秒守恒；整台建时每台效率 = 小数台数 / 向上取整");
  if (res.powerMix) L.push("外部电力：" + powerMixText(res.powerMix));
  (res.liquidSources || []).forEach(s => {
    L.push("液体 " + s.liquid + "：" + s.pump + " ×" + s.count + "（单台 " + fmtNum(s.perSecondEach)
      + "/s，电 " + fmtNum(s.power) + "/s" + (s.inputLiquids && s.inputLiquids.length
        ? "，吃 " + s.inputLiquids.map(i => i.name + " " + fmtNum(i.perSecond)).join("、") : "") + "）");
  });
  if (res.sources && res.sources.length) {
    res.sources.forEach(s => {
      if (s.type === "import") L.push("来源 " + s.item + "：外部运入");
      else if (s.type === "drill") L.push("来源 " + s.item + "：" + s.drill + " ×" + s.count + "（" + s.tiles + " 格矿" + (s.boosted ? "，加水" : "") + "）");
      else if (s.type === "multi") L.push("来源 " + s.item + "：" + s.block + " ×" + s.count);
    });
  }
  if (res.supply) {
    const s = res.supply;
    L.push("供电：" + s.name + " ×" + s.count + "（净 " + fmtNum(s.netTotal) + "/s"
      + (s.fuel ? "，烧 " + s.fuel.name + " " + fmtNum(s.fuel.perSecond) + "/s" : "") + "）");
  }
  if (res.attrs || res.usesAttr) L.push("- 环境属性：" + (res.attrText || ""));
  if (res.warnings.length) L.push("> ⚠ " + res.warnings.join("；"));
  return L.join("\n");
}

function renderList(env) {
  const { DATA, R } = env;
  const idx = DATA.__index;
  const names = arr => arr.map(x => (typeof x === "string" ? x : x.name)).join(", ");
  const L = [];
  L.push("物品（" + idx.items.length + "）：" + names(idx.items));
  const allBlocks = Array.from(idx.blocks.values());
  const itemFactories = allBlocks.filter(b => (b.kind || "item") === "item");
  const unitFactories = allBlocks.filter(b => b.kind === "unit");
  L.push("物品工厂（" + itemFactories.length + "）：" + names(itemFactories));
  L.push("兵厂（" + unitFactories.length + "）：" + names(unitFactories));
  L.push("发电厂（" + idx.generators.size + "）：" + Array.from(idx.generators.values()).map(g => g.name + " " + fmtNum(g.perSecond)).join(", "));
  L.push("钻头（" + idx.drills.size + "）：" + Array.from(idx.drills.values()).map(d => d.name + " t" + d.tier).join(", "));
  L.push("多产物（" + idx.multi.size + "）：" + Array.from(idx.multi.values()).map(m => m.name).join(", "));
  L.push("抽水泵（" + idx.pumps.size + "）：" + Array.from(idx.pumps.values())
    .map(p => p.name + " " + p.liquid + " " + fmtNum(p.perSecond) + "/s").join(", "));
  L.push("兵厂链（" + idx.unitChains.length + "）：" + idx.unitChains.map(c => c.start + "→" + c.tiers[c.tiers.length - 1].unit).join(", "));
  return L.join("\n");
}

function usage() {
  return [
    "配比计算器 CLI（算法与网页共用 core.js）",
    "",
    "  --item <物品> --rate <每秒>          按物品速率算（默认 1/s）",
    "  --block <方块> --count <台数>        按目标建筑台数算（满效）",
    "  --mix \"a:2,b:3\"                     混合厂：多个目标合并算上游（共享中间产物只建一份）",
    "  --plan <N>                          兵厂有多个生产计划时选第几个（0 起）",
    "  --chain <单位> --chainexpr 5t5      兵厂 T1→T5 大循环（5t5 = 5 台 T5 厂满效）",
    "  --chain <单位> --chainrate <台/s>    同上，但按顶级单位速率给",
    "  --boundary a,b                      边界输入（物品或液体，都按外部运入处理；液体写进来就不再抽/压）",
    "  --force item=block,...              强制指定配方（如 graphite=multi-press）",
    "  --depth <N>                         递归层数上限（默认 12）",
    "  --src item=import|drill:<钻头>:<矿格数>:<0|1>|multi:<方块>   外部来源（可重复）",
    "  --liquids auto                      液体自产：机器吃的液体没人供时自动接钻井/转化方块",
    "  --multi                             分离机/解离机也参与自动递归（默认只在“指定配方”里选才用）",
    "  --attr oil=0.7,water=1.2            环境属性（Attribute.*）：抽液方块每秒 = pumpAmount×60×(validTiles+属性)",
    "  --oilfloor <X>                      等价于 --attr oil=X（默认 1.5 = 满黑沙；石油钻井 = 0.25×60×X）",
    "  --liquid oil=make|pump|import[:方块]  逐种液体指定自产方式（oil=make:spore-press）",
    "  --liquidname oil=<方块>              只指定产液方块（方式按 auto 判）",
    "  --flow                              归一化模式：台数不取整，所有数量按每秒（学 TMI）",
    "  --gen <发电厂> --genfuel <燃料> [--gencount N] [--gendemand X]  供电方案（N=0/省略则自动补足）",
    "  --format text|md|json               输出格式（默认 text）",
    "  --icons                             JSON 里保留 base64 图标（默认剔掉，省体积）",
    "  --data <gamedata.js>                换数据文件",
    "  --list                              列出可用物品/工厂/发电厂/钻头/兵厂链",
    "",
    "例：node ratio-calc/cli.cjs --item silicon --rate 5 --src sand=drill:laser-drill:8 \\",
    "      --gen combustion-generator --genfuel coal --format md"
  ].join("\n");
}

/* ---------------- 入口 ---------------- */

function main(argv) {
  const opts = parseArgs(argv);
  if (opts.help || opts.h) { console.log(usage()); return 0; }
  if (opts.list) { console.log(renderList(loadData(opts.data))); return 0; }
  const res = query(opts);
  const fmt = String(opts.format || "text").toLowerCase();
  if (fmt === "json") console.log(JSON.stringify(opts.icons ? res : stripIcons(res), null, 2));
  else if (fmt === "md" || fmt === "markdown") console.log(renderMarkdown(res));
  else console.log(renderText(res));
  return 0;
}

if (require.main === module) {
  try {
    process.exitCode = main(process.argv.slice(2));
  } catch (err) {
    const fmt = (process.argv.join(" ").match(/--format[=\s]+(json)/) || [])[1];
    if (fmt) console.log(JSON.stringify({ ok: false, error: String(err.message || err) }, null, 2));
    else console.error("× " + (err.message || err));
    process.exitCode = 2;
  }
}

module.exports = { query, renderText, renderMarkdown, renderList, loadData, parseArgs, usage, stripIcons };
