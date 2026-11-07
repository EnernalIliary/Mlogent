/* 自动配比计算器 —— 内核
 *
 * 与 MBO/mbo/production.py 的 expand() 保持同一套规则（docs/02 §E1）：
 *   1. 台数 = ceil(需求量 / 单台速率)，向上取整；
 *   2. 输入递归展开，碰到 boundary 里的物品停下（边界是外部输入，不展开到矿）；
 *   3. 同一物品有多个配方时：优先选「输入端也都能自己造」的配方（不新引入边界），
 *      其次比「向上取整后的实际产量」更贴近目标，再比占地（size²），最后按名字定序；
 *   4. 没有配方产出的物品按外部输入处理，并给一条 warning。
 *
 * 两种入口：
 *   expand(data, item, rate, boundary, force)      —— 按目标物品速率（旧口径）
 *   expandBuilding(data, block, count, opts)       —— 按目标建筑台数（满效，新口径）
 *
 * 这个文件不依赖任何框架，浏览器和 node 都能跑（node 里会挂到 module.exports）。
 */
(function (global) {
  "use strict";

  var MAX_DEPTH = 12;

  function buildIndex(data) {
    var blocks = new Map();
    (data.blocks || []).forEach(function (b) {
      var entry = {
        name: b.name,
        kind: b.kind || "item",
        size: b.size || 1,
        power: b.power || 0,
        craftTime: b.craft_time,
        cps: b.craft_time ? 60 / b.craft_time : 0,
        icon: b.icon || "",
        inputs: (b.inputs || []).map(function (p) { return { name: p[0], amount: p[1] }; }),
        outputs: (b.outputs || []).map(function (p) { return { name: p[0], amount: p[1] }; }),
        plans: (b.plans || []).map(function (p) {
          return {
            unit: p.unit,
            time: p.time,
            perSecond: p.time > 0 ? 60 / p.time : 0,
            items: (p.items || []).map(function (q) { return { name: q[0], amount: q[1] }; })
          };
        }),
        upgrades: (b.upgrades || []).map(function (u) { return { from: u[0], to: u[1] }; }),
        factoryKind: b.factory_kind || ""
      };
      blocks.set(b.name, entry);
    });
    var byOutput = new Map();   // item -> [block]
    blocks.forEach(function (b) {
      b.outputs.forEach(function (o) {
        if (!byOutput.has(o.name)) byOutput.set(o.name, []);
        byOutput.get(o.name).push(b);
      });
    });
    byOutput.forEach(function (list) {
      list.sort(function (a, b) { return a.name < b.name ? -1 : a.name > b.name ? 1 : 0; });
    });
    var items = (data.items || []).map(function (i) { return i.name; });
    var itemIcons = new Map();
    var itemProps = new Map();
    (data.items || []).forEach(function (i) {
      itemIcons.set(i.name, i.icon || "");
      itemProps.set(i.name, { hardness: i.hardness || 0, flammability: i.flammability || 0,
                              radioactivity: i.radioactivity || 0 });
    });

    /* 发电厂 / 钻头 / 多产物方块（分离机·解离机）：数组化存储，[a,b,c] 比对象省字节 */
    var generators = new Map();
    (data.generators || []).forEach(function (g) {
      generators.set(g.name, {
        name: g.name, size: g.size || 1, icon: g.icon || "", kind: g.kind || "",
        perSecond: g.perSecond || 0, powerUsage: g.powerUsage || 0,
        fuels: (g.fuels || []).map(function (f) { return [f[0], f[1], f[2]]; }),
        liquids: (g.liquids || []).map(function (l) { return [l[0], l[1]]; })
      });
    });
    var drills = new Map();
    (data.drills || []).forEach(function (d) {
      drills.set(d.name, {
        name: d.name, size: d.size || 1, icon: d.icon || "",
        tier: d.tier || 0, drillTime: d.drillTime || 300,
        hardnessMult: d.hardnessMult || 0,
        boostLiquid: d.boostLiquid || "", boostLiquidPerSecond: d.boostLiquidPerSecond || 0,
        boostIntensity: d.boostIntensity || 1, power: d.power || 0
      });
    });
    var multi = new Map();
    (data.multi || []).forEach(function (m) {
      multi.set(m.name, {
        name: m.name, size: m.size || 1, icon: m.icon || "",
        craftTime: m.craftTime || 0, cps: m.cps || 0, power: m.power || 0,
        inputs: (m.inputs || []).map(function (i) { return [i[0], i[1]]; }),
        inputLiquids: (m.inputLiquids || []).map(function (i) { return [i[0], i[1]]; }),
        outputs: (m.outputs || []).map(function (o) { return [o[0], o[1], o[2]]; })
      });
    });

    /* 兵厂大循环：单位 -> 造它的方块；再串成 T1→T5 */
    var unitProducers = new Map();
    var nextOf = new Map();
    var starts = [];
    blocks.forEach(function (b) {
      if (b.kind !== "unit") return;
      if (b.factoryKind === "reconstructor") {
        b.upgrades.forEach(function (u) {
          nextOf.set(u.from, u.to);
          unitProducers.set(u.to, { unit: u.to, block: b.name, kind: b.factoryKind,
                                    perSecond: b.cps, power: b.power,
                                    items: b.inputs.map(function (i) { return { name: i.name, amount: i.amount }; }) });
        });
      } else {
        b.plans.forEach(function (p) {
          unitProducers.set(p.unit, { unit: p.unit, block: b.name, kind: b.factoryKind,
                                      perSecond: p.perSecond, power: b.power, items: p.items });
        });
        if (b.factoryKind === "unit-factory") {
          b.plans.forEach(function (p) { starts.push(p.unit); });
        }
      }
    });
    var chains = [];
    starts.forEach(function (u) {
      var tiers = [], cur = u, guard = 0;
      while (cur && guard++ < 8) {
        var prod = unitProducers.get(cur);
        tiers.push({ unit: cur, block: prod ? prod.block : "",
                     perSecond: prod ? prod.perSecond : 0, power: prod ? prod.power : 0,
                     items: prod ? prod.items : [] });
        cur = nextOf.get(cur);
      }
      if (tiers.length > 1) chains.push({ start: u, tiers: tiers });
    });

    return {
      items: items,
      itemIcons: itemIcons,
      itemProps: itemProps,
      generators: generators,
      drills: drills,
      multi: multi,
      unitProducers: unitProducers,
      unitChains: chains,
      unitIcons: data.unit_icons || {},
      snapshot: data.snapshot || "",
      itemSet: new Set(items),
      blocks: blocks,
      producersOf: function (item) { return byOutput.get(item) || []; },
      perSecond: function (block, item) {
        var hit = block.outputs.filter(function (o) { return o.name === item; })[0];
        return hit ? hit.amount * block.cps : 0;
      },
      inputPerSecond: function (block) {
        return block.inputs.map(function (i) { return { name: i.name, amount: i.amount * block.cps }; });
      },
      planInputsPerSecond: function (plan) {
        return plan.items.map(function (i) { return { name: i.name, amount: i.amount * plan.perSecond }; });
      }
    };
  }

  function indexOf(data) {
    return data.__index || (data.__index = buildIndex(data));
  }

  /* ---------------------------------------------------------------- *
   * 物品需求的递归展开（两种入口共用）
   * ---------------------------------------------------------------- */
  function makeExpander(idx, boundary, force, maxDepth) {
    var bset = new Set(boundary || []);
    var fmap = force || {};
    var machines = {};
    var order = [];
    var demand = {};
    var warnings = [];
    var maxDepth_ = maxDepth || MAX_DEPTH;

    function servable(item, seen) {
      if (bset.has(item)) return true;
      if (seen.has(item)) return false;
      var cands = idx.producersOf(item);
      if (!cands.length) return false;
      var next = new Set(seen); next.add(item);
      return cands.some(function (b) {
        return b.inputs.every(function (i) { return servable(i.name, next); });
      });
    }

    function choose(item, amount) {
      var cands = idx.producersOf(item);
      var forced = fmap[item];
      if (forced) {
        var only = cands.filter(function (b) { return b.name === forced; });
        if (!only.length) throw new Error(forced + " 不产 " + item);
        cands = only;
      }
      var scored = [];
      cands.forEach(function (b) {
        var per = idx.perSecond(b, item);
        if (per <= 0) return;
        var n = Math.max(1, Math.ceil(amount / per - 1e-9));
        var introduces = !b.inputs.every(function (i) { return servable(i.name, new Set()); });
        scored.push({ block: b, n: n, introduces: introduces, actual: n * per });
      });
      if (!scored.length) throw new Error(item + " 没有可用配方");
      scored.sort(function (a, b) {
        if (a.introduces !== b.introduces) return a.introduces ? 1 : -1;
        if (Math.abs(a.actual - b.actual) > 1e-9) return a.actual - b.actual;
        var as = a.block.size * a.block.size, bs = b.block.size * b.block.size;
        if (as !== bs) return as - bs;
        return a.block.name < b.block.name ? -1 : a.block.name > b.block.name ? 1 : 0;
      });
      return scored[0];
    }

    function need(item, amount, depth, parentNode) {
      if (amount <= 1e-9) return null;
      var node = { item: item, amount: amount, block: null, count: 0, children: [] };
      if (parentNode) parentNode.children.push(node);
      if (bset.has(item) || depth > maxDepth_) {
        node.reason = bset.has(item) ? "boundary" : "depth";
        demand[item] = (demand[item] || 0) + amount;
        return node;
      }
      var cands = idx.producersOf(item);
      if (!cands.length) {
        node.reason = "no-recipe";
        demand[item] = (demand[item] || 0) + amount;
        warnings.push(item + " 没有配方产出，按外部输入处理");
        return node;
      }
      var pick = choose(item, amount);
      var b = pick.block;
      var n = Math.max(1, Math.ceil(amount / idx.perSecond(b, item) - 1e-9));
      node.block = b.name;
      node.count = n;
      node.per = idx.perSecond(b, item);
      node.actual = n * node.per;
      machines[b.name] = (machines[b.name] || 0) + n;
      order.push({ block: b.name, count: n, item: item });
      idx.inputPerSecond(b).forEach(function (i) {
        need(i.name, n * i.amount, depth + 1, node);
      });
      return node;
    }

    return {
      need: need,
      machines: machines,
      order: order,
      result: function (extra) {
        var power = 0;
        Object.keys(machines).forEach(function (name) {
          var b = idx.blocks.get(name);
          if (b) power += machines[name] * b.power;
        });
        var out = {
          machines: machines,
          order: order,
          demand: demand,
          power: power,
          warnings: warnings,
          snapshot: idx.snapshot || ""
        };
        Object.keys(extra || {}).forEach(function (k) { out[k] = extra[k]; });
        return out;
      }
    };
  }

  /* 按目标物品速率（旧口径） */
  function expand(data, target, rate, boundary, force, opts) {
    var idx = indexOf(data);
    if (!idx.itemSet.has(target)) throw new Error("未知物品：" + target);
    var ex = makeExpander(idx, boundary, force, (opts && opts.maxDepth) || MAX_DEPTH);
    var root = ex.need(target, rate, 0, null);
    var res = ex.result({ target: target, requested: rate, tree: root });
    res.achieved = root && root.actual ? root.actual : 0;
    if (opts && opts.sources) applySources(data, res, opts.sources);
    return res;
  }

  /* 按目标建筑台数（满效，新口径）
   * opts = { boundary:[], force:{}, plan: 0, maxDepth: 12 }
   * 返回 { block, count, products:[{name,type,rate}], inputs:[{name,amount}], machines, ... }
   */
  function expandBuilding(data, blockName, count, opts) {
    var idx = indexOf(data);
    opts = opts || {};
    var b = idx.blocks.get(blockName);
    if (!b) throw new Error("未知方块：" + blockName);
    if (!(count > 0)) throw new Error("台数要大于 0");
    var ex = makeExpander(idx, opts.boundary, opts.force, opts.maxDepth || MAX_DEPTH);

    var products = [];
    var inputs = [];

    if (b.kind === "unit") {
      if (b.factoryKind === "reconstructor") {
        // 升级厂：一个周期 constructTime 帧消耗一批材料，产出一台升级后的单位
        var per = b.cps;
        products.push({ name: (b.upgrades[0] ? b.upgrades[0].to : "unit"), type: "unit", rate: per * count });
        b.inputs.forEach(function (i) { inputs.push({ name: i.name, amount: i.amount * per * count }); });
      } else {
        var plans = b.plans || [];
        if (!plans.length) throw new Error(blockName + " 没有生产计划");
        var pi = Math.min(Math.max(0, opts.plan || 0), plans.length - 1);
        var plan = plans[pi];
        products.push({ name: plan.unit, type: "unit", rate: plan.perSecond * count });
        plan.items.forEach(function (i) {
          inputs.push({ name: i.name, amount: i.amount * plan.perSecond * count });
        });
      }
    } else {
      b.outputs.forEach(function (o) {
        products.push({ name: o.name, type: "item", rate: o.amount * b.cps * count });
      });
      b.inputs.forEach(function (i) {
        inputs.push({ name: i.name, amount: i.amount * b.cps * count });
      });
    }

    var root = { block: blockName, count: count, item: null, amount: 0, children: [] };
    inputs.forEach(function (i) { ex.need(i.name, i.amount, 1, root); });

    var res = ex.result({
      block: blockName, count: count, products: products, inputs: inputs, tree: root,
      plan: (b.kind === "unit" && b.factoryKind !== "reconstructor")
        ? Math.min(Math.max(0, opts.plan || 0), Math.max(0, (b.plans || []).length - 1)) : 0,
      planTotal: b.kind === "unit" && b.factoryKind !== "reconstructor" ? (b.plans || []).length : 0
    });
    // 目标建筑自身也进建造清单（电力要一起算进去：ex.result 里还没有它）
    res.machines[blockName] = (res.machines[blockName] || 0) + count;
    res.machines = sortMachines(res.machines);
    res.power = 0;
    Object.keys(res.machines).forEach(function (name) {
      var mb = idx.blocks.get(name);
      if (mb) res.power += res.machines[name] * mb.power;
    });
    if (b.factoryKind === "assembler") {
      res.warnings.push("组装厂消耗的是方块（Payload），这里按外部输入处理，不展开成工厂");
    }
    if (opts.sources) applySources(data, res, opts.sources);
    return res;
  }

  function sortMachines(m) {
    var out = {};
    Object.keys(m).sort().forEach(function (k) { out[k] = m[k]; });
    return out;
  }

  /* ---------------------------------------------------------------- *
   * 外部来源：钻头 / 多产物方块 / 发电厂
   *   公式照 Mindustry 源码（Drill.java / Separator.java / ConsumeGenerator.java）：
   *     钻头每秒 = 60 * 矿格数 * speed² / delay
   *       delay = (drillTime + hardnessMult * 物品硬度) / 该物品的钻头倍率
   *       speed = 加水（有加速液体的钻头）? boostIntensity : 1
   *     分离机 cps = 60/craftTime，每种产物 = cps * (amount / Σamount)
   *     发电厂每台净发电 = 燃料效率 * powerProduction - 自耗电
   * ---------------------------------------------------------------- */

  /* 统一的"方块"视图：物品工厂 / 兵厂 / 钻头 / 多产物 / 发电厂 */
  function anyBlock(idx, name) {
    var b = idx.blocks.get(name);
    if (b) return b;
    var d = idx.drills.get(name);
    if (d) {
      return { name: name, kind: "drill", size: d.size, power: d.power, icon: d.icon,
               craftTime: d.drillTime, cps: 0, inputs: [], outputs: [],
               plans: [], upgrades: [], factoryKind: "", tier: d.tier };
    }
    var m = idx.multi.get(name);
    if (m) {
      return { name: name, kind: "multi", size: m.size, power: m.power, icon: m.icon,
               craftTime: m.craftTime, cps: m.cps,
               inputs: m.inputs.map(function (i) { return { name: i[0], amount: i[1] / (m.cps || 1) }; }),
               outputs: m.outputs.map(function (o) { return { name: o[0], amount: o[1] / (m.cps || 1), share: o[2] }; }),
               plans: [], upgrades: [], factoryKind: "" };
    }
    var g = idx.generators.get(name);
    if (g) {
      return { name: name, kind: "generator", size: g.size, power: 0, icon: g.icon,
               craftTime: 0, cps: 0, inputs: [], outputs: [], plans: [], upgrades: [],
               factoryKind: "", perSecond: g.perSecond };
    }
    return null;
  }

  function hardnessOf(idx, item) {
    var p = idx.itemProps.get(item);
    return p ? (p.hardness || 0) : 0;
  }

  /* 一台钻头采某个物品的每秒产量 */
  function drillRate(data, drillName, itemName, tiles, boosted) {
    var idx = indexOf(data);
    var d = idx.drills.get(drillName);
    if (!d) throw new Error("未知钻头：" + drillName);
    var t = Math.max(1, Math.floor(tiles || 1));
    var mult = (d.multipliers && d.multipliers[itemName]) || 1;
    var delay = (d.drillTime + d.hardnessMult * hardnessOf(idx, itemName)) / mult;
    var speed = (boosted && d.boostLiquid) ? d.boostIntensity : 1;
    if (!(delay > 0)) return 0;
    return 60 * t * speed * speed / delay;
  }

  /* 需要多少台钻头才能供上 amount/s */
  function drillsNeeded(data, drillName, itemName, amount, tiles, boosted) {
    var per = drillRate(data, drillName, itemName, tiles, boosted);
    var idx = indexOf(data);
    var d = idx.drills.get(drillName);
    var n = per > 0 ? Math.max(0, Math.ceil(amount / per - 1e-9)) : 0;
    return {
      drill: drillName, item: itemName, tiles: Math.max(1, Math.floor(tiles || 1)),
      boosted: !!(boosted && d && d.boostLiquid), perSecondEach: per, count: n,
      perSecondTotal: n * per, power: n * (d ? d.power : 0),
      liquid: (boosted && d && d.boostLiquid)
        ? { name: d.boostLiquid, perSecond: n * d.boostLiquidPerSecond } : null
    };
  }

  /* 给定发电厂类型 + 燃料：覆盖 demand 需要几台、每秒烧多少料 */
  function generatorPlan(data, demand, genName, fuelName) {
    var idx = indexOf(data);
    var g = idx.generators.get(genName);
    if (!g) throw new Error("未知发电厂：" + genName);
    var fuels = g.fuels || [];
    var fuel = null;
    if (fuels.length) {
      fuel = fuelName ? fuels.filter(function (f) { return f[0] === fuelName; })[0] : null;
      if (!fuel) fuel = fuels[0];
    }
    var grossEach = fuel ? fuel[2] : g.perSecond;      // 燃料效率已折算进 powerPerSecond
    var netEach = grossEach - g.powerUsage;
    var count = (demand > 0 && netEach > 0) ? Math.ceil(demand / netEach - 1e-9) : 0;
    return {
      name: g.name, icon: g.icon, size: g.size, kind: g.kind,
      fuelName: fuel ? fuel[0] : "",
      grossEach: grossEach, netEach: netEach, count: count,
      netTotal: count * netEach, demand: demand, surplus: count * netEach - demand,
      selfUse: g.powerUsage,
      fuel: fuel ? { name: fuel[0], perSecondEach: fuel[1], perSecond: fuel[1] * count } : null,
      liquids: (g.liquids || []).map(function (l) {
        return { name: l[0], perSecondEach: l[1], perSecond: l[1] * count };
      }),
      fuels: fuels.map(function (f) { return { name: f[0], perSecond: f[1], grossEach: f[2] }; })
    };
  }

  /* 给定发电厂台数：能发多少、烧多少料（UI 里手填台数时用） */
  function generatorSupply(data, genName, fuelName, count) {
    var idx = indexOf(data);
    var g = idx.generators.get(genName);
    if (!g) throw new Error("未知发电厂：" + genName);
    count = Math.max(0, Math.floor(count || 0));
    var fuels = g.fuels || [];
    var fuel = null;
    if (fuels.length) {
      fuel = fuelName ? fuels.filter(function (f) { return f[0] === fuelName; })[0] : null;
      if (!fuel) fuel = fuels[0];
    }
    var grossEach = fuel ? fuel[2] : g.perSecond;
    var netTotal = (grossEach - g.powerUsage) * count;
    return {
      name: g.name, icon: g.icon, count: count,
      fuelName: fuel ? fuel[0] : "",
      netEach: grossEach - g.powerUsage, netTotal: netTotal, selfUse: g.powerUsage * count,
      fuel: fuel ? { name: fuel[0], perSecond: fuel[1] * count, perSecondEach: fuel[1] } : null,
      liquids: (g.liquids || []).map(function (l) {
        return { name: l[0], perSecond: l[1] * count, perSecondEach: l[1] };
      })
    };
  }

  /* 分离机 / 解离机：台数 -> 全部产物 + 输入需求 + 电 */
  function separatorPlan(data, name, count) {
    var idx = indexOf(data);
    var m = idx.multi.get(name);
    if (!m) throw new Error("未知多产物方块：" + name);
    count = Math.max(0, Math.floor(count || 0));
    return {
      name: m.name, icon: m.icon, size: m.size, count: count,
      cps: m.cps, power: m.power * count,
      outputs: m.outputs.map(function (o) {
        return { name: o[0], share: o[2], perSecond: o[1] * count };
      }),
      inputs: m.inputs.map(function (i) { return { name: i[0], perSecond: i[1] * count }; }),
      inputLiquids: m.inputLiquids.map(function (i) { return { name: i[0], perSecond: i[1] * count }; })
    };
  }

  /* 兵厂 T1→T5 大循环：要产 rate 台/s 的顶级单位，每级要几台、吃多少料 */
  function unitChain(data, startUnit, rate) {
    var idx = indexOf(data);
    var chain = null;
    for (var i = 0; i < idx.unitChains.length; i++) {
      if (idx.unitChains[i].start === startUnit) { chain = idx.unitChains[i]; break; }
    }
    if (!chain) throw new Error(startUnit + " 没有 T1→T5 升级链");
    var rows = [];
    var demand = Math.max(0, rate || 0);
    var materials = {};
    var power = 0;
    for (var k = chain.tiers.length - 1; k >= 0; k--) {
      var t = chain.tiers[k];
      var count = (demand > 0 && t.perSecond > 0) ? Math.ceil(demand / t.perSecond - 1e-9) : 0;
      var actual = count * t.perSecond;
      var rowItems = t.items.map(function (it) {
        var v = it.amount * actual;              // 每秒消耗
        materials[it.name] = (materials[it.name] || 0) + v;
        return { name: it.name, perSecond: v };
      });
      power += count * t.power;
      rows.unshift({
        tier: k + 1, unit: t.unit, block: t.block, icon: idx.unitIcons[t.unit] || "",
        blockIcon: (idx.blocks.get(t.block) || {}).icon || "",
        perSecond: t.perSecond, count: count, actual: actual,
        powerEach: t.power, power: count * t.power, items: rowItems
      });
      demand = actual;
    }
    return {
      start: startUnit, top: chain.tiers[chain.tiers.length - 1].unit,
      tiers: chain.tiers.length, rate: rate, rows: rows,
      materials: sortMachines(materials), power: power
    };
  }

  function recalcPower(idx, res) {
    var power = 0;
    Object.keys(res.machines).forEach(function (name) {
      var mb = anyBlock(idx, name);
      if (mb && mb.kind !== "generator") power += res.machines[name] * mb.power;
    });
    res.power = power;
    return power;
  }

  /* 把"外部输入"逐项换成真实来源：import（运入）/ drill（钻头）/ multi（分离机·解离机）
   * cfg 形如 { sand: {type:"drill", drill:"laser-drill", tiles:8, boosted:true},
   *            scrap: {type:"multi", block:"disassembler"},
   *            coal: {type:"import"} }
   */
  function applySources(data, res, cfg) {
    var idx = indexOf(data);
    cfg = cfg || {};
    var sources = [];
    Object.keys(res.demand || {}).sort().forEach(function (item) {
      var need = res.demand[item];
      var c = cfg[item] || {};
      var type = c.type || "import";
      var row = { item: item, demand: need, type: type, power: 0, icon: idx.itemIcons.get(item) || "" };
      if (type === "drill") {
        var plan = drillsNeeded(data, c.drill || "mechanical-drill", item, need,
                                c.tiles || 6, !!c.boosted);
        row.drill = plan.drill; row.tiles = plan.tiles; row.boosted = plan.boosted;
        row.perSecondEach = plan.perSecondEach; row.count = plan.count;
        row.perSecondTotal = plan.perSecondTotal;
        row.power = plan.power; row.liquid = plan.liquid;
        row.icon = (idx.drills.get(plan.drill) || {}).icon || "";
        if (plan.count) res.machines[plan.drill] = (res.machines[plan.drill] || 0) + plan.count;
      } else if (type === "multi") {
        var block = c.block || "separator";
        var m = idx.multi.get(block);
        if (!m) throw new Error("未知多产物方块：" + block);
        var hit = null;
        m.outputs.forEach(function (o) { if (o[0] === item) hit = o; });
        if (!hit) throw new Error(m.name + " 不产 " + item);
        var n = hit[1] > 0 ? Math.ceil(need / hit[1] - 1e-9) : 0;
        var sp = separatorPlan(data, block, n);
        row.block = block; row.perSecondEach = hit[1]; row.count = n;
        row.power = sp.power;
        row.icon = m.icon;
        row.inputs = sp.inputs; row.inputLiquids = sp.inputLiquids;
        row.byproducts = sp.outputs.filter(function (o) { return o.name !== item; });
        if (n) res.machines[block] = (res.machines[block] || 0) + n;
      }
      sources.push(row);
    });
    res.sources = sources;
    res.machines = sortMachines(res.machines);
    recalcPower(idx, res);
    return sources;
  }

  /* 便捷：把结果摊平成表格行 */
  function machineRows(data, result) {
    var idx = indexOf(data);
    return Object.keys(result.machines).map(function (name) {
      var b = anyBlock(idx, name);
      var count = result.machines[name];
      var outputs = [];
      if (b && b.kind === "drill") {
        outputs = ["采集（见外部来源）"];
      } else if (b && b.kind === "unit") {
        if (b.factoryKind === "reconstructor") {
          outputs = (b.upgrades || []).length
            ? ["升级 " + b.upgrades.length + " 种（" + round(b.cps * count) + " 次/s）"]
            : ["升级厂"];
        } else {
          var plan = (b.plans || [])[result.plan || 0] || (b.plans || [])[0];
          if (plan) outputs = [plan.unit + " " + round(plan.perSecond * count) + "/s"];
        }
      } else if (b) {
        outputs = b.outputs.map(function (o) {
          return o.name + " " + round(o.amount * b.cps * count) + "/s";
        });
      }
      return {
        name: name,
        count: count,
        kind: b ? b.kind : "item",
        icon: b ? (b.icon || "") : "",
        size: b ? b.size : 0,
        powerEach: b ? b.power : 0,
        powerTotal: b ? b.power * count : 0,
        outItems: b ? b.outputs.map(function (o) {
          return { name: o.name, type: "item", perSecond: o.amount * b.cps * count };
        }) : [],
        rateEach: b ? (b.kind === "unit"
          ? ((b.plans && b.plans[0]) ? b.plans[0].perSecond : b.cps)
          : (b.outputs.length ? b.outputs[0].amount * b.cps : 0)) : 0,
        outputs: outputs
      };
    });
  }

  function round(x) { return Math.round(x * 1000) / 1000; }

  var api = { buildIndex: buildIndex, indexOf: indexOf,
              expand: expand, expandBuilding: expandBuilding,
              machineRows: machineRows, anyBlock: anyBlock,
              drillRate: drillRate, drillsNeeded: drillsNeeded,
              generatorPlan: generatorPlan, generatorSupply: generatorSupply,
              separatorPlan: separatorPlan, unitChain: unitChain,
              applySources: applySources, recalcPower: recalcPower };
  global.RatioCore = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
