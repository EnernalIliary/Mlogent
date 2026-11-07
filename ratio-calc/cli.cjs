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
  /* 可重复的参数（--src 可以出现多次，各记一条）*/
  const REPEAT = { src: true };
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
    else if (type === "belt") cfg[item] = { type: "import", via: parts[1] || "belt-grey" };
    else throw new Error("未知来源类型：" + type + "（import / drill / multi / pump / belt）");
  });
  return cfg;
}

/* ---------------- 查询 ---------------- */

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
  const sources = parseSources(opts.src || []);

  const res = {
    ok: true, mode: null, target: null, requested: null,
    products: [], inputs: [], machines: [], demand: [], liquids: [], power: 0,
    warnings: [], sources: [], liquidSources: [], supply: null, chain: null
  };

  if (opts.chain) {
    res.mode = "chain";
    const expr = opts.chainexpr !== undefined ? String(opts.chainexpr) : null;
    const m = expr ? /^(\d+(?:\.\d+)?)\s*[x×*]?\s*t\s*([1-5])$/i.exec(expr.trim()) : null;
    if (m) {
      res.chain = R.chainFromTop(DATA, String(opts.chain), parseInt(m[2], 10), parseFloat(m[1]));
      res.requested = { topCount: parseFloat(m[1]), topTier: parseInt(m[2], 10) };
    } else {
      const rate = num(opts.chainrate !== undefined ? opts.chainrate : opts.rate, 0.05);
      res.chain = R.unitChain(DATA, String(opts.chain), rate);
      res.requested = rate;
    }
    res.target = res.chain.start + " → " + res.chain.top;
    return res;
  }

  if (opts.block) {
    const count = num(opts.count, 1);
    /* 选中的是兵厂 → 直接走 T1→T5 大循环（和页面「按目标建筑台数」一致） */
    const selB = env.idx ? R.anyBlock(env.idx, String(opts.block)) : null;
    if (selB && selB.kind === "unit") {
      const planIdx = num(opts.plan, 0);
      const line = selB.plans && selB.plans[planIdx] ? selB.plans[planIdx].unit : (opts.chainline ? String(opts.chainline) : null);
      const ch = R.chainFromBlock(DATA, String(opts.block), count, line ? { chainStart: line } : null);
      if (ch) {
        const machines = {};
        ch.rows.forEach(r => { if (r.count > 0) machines[r.block] = (machines[r.block] || 0) + r.count; });
        res.mode = "chain";
        res.chain = ch;
        res.target = ch.start + " → " + ch.top;
        res.requested = { topCount: count, topTier: ch.topTier };
        const mine = ch.rows.filter(r => r.tier === ch.topTier)[0];
        res.products = [{ name: mine ? mine.unit : ch.top, type: "unit", rate: mine ? mine.capacity : ch.achieved }];
        res.machines = Object.keys(machines).sort().map(name => {
          const b = R.anyBlock(env.idx, name);
          return {
            name, count: machines[name], kind: b ? b.kind : "unit",
            icon: b ? (b.icon || "") : "", size: b ? b.size : 0,
            powerEach: b ? b.power : 0, powerTotal: b ? b.power * machines[name] : 0,
            outItems: [], outputs: []
          };
        });
        res.demand = Object.keys(ch.materials).sort().map(k => ({ name: k, perSecond: ch.materials[k] }));
        res.power = ch.power;
        return res;
      }
    }
    const r = R.expandBuilding(DATA, String(opts.block), count, {
      boundary: boundary, force: force, maxDepth: depth,
      plan: num(opts.plan, 0), sources: sources
    });
    res.mode = "building";
    res.target = String(opts.block);
    res.requested = count;
    res.products = r.products || [];
    res.inputs = r.inputs || [];
    res.machines = flattenMachines(DATA, R, r);
    res.demand = Object.keys(r.demand || {}).sort().map(k => ({ name: k, perSecond: r.demand[k] }));
    res.power = r.power || 0;
    res.liquids = r.liquids || [];
    res.warnings = r.warnings || [];
    res.sources = r.sources || [];
    res.liquidSources = r.liquidSources || [];
    if (r.planTotal > 1) res.warnings.push("该兵厂有 " + r.planTotal + " 个生产计划，用的是第 " + (r.plan + 1) + " 个（--plan 可换）");
  } else if (opts.item) {
    const rate = num(opts.rate, 1);
    const r = R.expand(DATA, String(opts.item), rate, boundary, force, { maxDepth: depth, sources: sources });
    res.mode = "item";
    res.target = String(opts.item);
    res.requested = rate;
    res.products = [{ name: String(opts.item), type: "item", rate: r.achieved || 0 }];
    res.machines = flattenMachines(DATA, R, r);
    res.demand = Object.keys(r.demand || {}).sort().map(k => ({ name: k, perSecond: r.demand[k] }));
    res.power = r.power || 0;
    res.liquids = r.liquids || [];
    res.warnings = r.warnings || [];
    res.sources = r.sources || [];
    res.liquidSources = r.liquidSources || [];
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
  // 给产出/边界输入补图标（卡片渲染和 bot 富文本都用得上）
  res.products.forEach(p => { p.icon = iconOfIndex(idx, p.name, p.type); });
  res.demand.forEach(d => { d.icon = iconOfIndex(idx, d.name, "item"); });
  res.liquids.forEach(l => { l.icon = ""; });
  if (res.supply && res.supply.fuel) res.supply.fuel.icon = iconOfIndex(idx, res.supply.fuel.name, "item");
  return res;
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
    powerEach: round(x.powerEach), powerTotal: round(x.powerTotal),
    outItems: (x.outItems || []).map(o => ({
      name: o.name, type: o.type, perSecond: round(o.perSecond), icon: iconOfIndex(idx, o.name, o.type)
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
      if (k === "icon" || k === "blockIcon" || k === "unitIcon") return;
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
    : "配比：" + res.target + " " + fmtNum(res.requested) + "/s（物品模式）";
  L.push(head);
  if (res.products.length) {
    L.push("  产出：" + res.products.map(p => p.name + " " + fmtNum(p.rate) + "/s").join("、"));
  }
  if (res.machines.length) {
    res.machines.forEach(m => {
      let line = "  " + m.name + " ×" + m.count;
      if (m.powerTotal) line += "（电 " + fmtNum(m.powerTotal) + "/s）";
      if (m.outItems && m.outItems.length && m.kind !== "item") {
        line += " → " + m.outItems.map(o => o.name + " " + fmtNum(o.perSecond) + "/s").join("、");
      }
      L.push(line);
    });
  }
  const total = res.machines.reduce((a, m) => a + m.count, 0);
  L.push("  机器合计：" + total + " 台，电力 " + fmtNum(res.power) + "/s");
  if (res.demand.length) {
    L.push("  边界输入：" + res.demand.map(d => d.name + " " + fmtNum(d.perSecond) + "/s").join("、"));
  }
  if (res.liquids && res.liquids.length) {
    L.push("  液体需求：" + res.liquids.map(d => {
      const pump = (res.liquidSources || []).filter(s => s.liquid === d.name)[0];
      return d.name + " " + fmtNum(d.perSecond) + "/s" + (pump ? "（" + pump.pump + " 抽）" : "（外部运入）");
    }).join("、"));
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
    : "配比：" + res.target + " " + fmtNum(res.requested) + "/s") + "**");
  L.push("");
  if (res.products.length) L.push("产出：" + res.products.map(p => p.name + " " + fmtNum(p.rate) + "/s").join("、"));
  L.push("");
  L.push("| 建筑 | 台数 | 电力/s |");
  L.push("|---|---|---|");
  res.machines.forEach(m => L.push("| " + m.name + " | " + m.count + " | " + (m.powerTotal ? fmtNum(m.powerTotal) : "—") + " |"));
  L.push("");
  if (res.demand.length) L.push("边界输入：" + res.demand.map(d => d.name + " " + fmtNum(d.perSecond) + "/s").join("、"));
  if (res.liquids && res.liquids.length) {
    L.push("液体需求：" + res.liquids.map(d => {
      const pump = (res.liquidSources || []).filter(s => s.liquid === d.name)[0];
      return d.name + " " + fmtNum(d.perSecond) + "/s" + (pump ? "（" + pump.pump + " 抽）" : "（外部运入）");
    }).join("、"));
  }
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
    "  --plan <N>                          兵厂有多个生产计划时选第几个（0 起）",
    "  --chain <单位> --chainexpr 5t5      兵厂 T1→T5 大循环（5t5 = 5 台 T5 厂满效）",
    "  --chain <单位> --chainrate <台/s>    同上，但按顶级单位速率给",
    "  --boundary a,b                      边界输入（这些物品按外部运入处理）",
    "  --force item=block,...              强制指定配方（如 graphite=multi-press）",
    "  --depth <N>                         递归层数上限（默认 12）",
    "  --src item=import|drill:<钻头>:<矿格数>:<0|1>|multi:<方块>   外部来源（可重复）",
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
