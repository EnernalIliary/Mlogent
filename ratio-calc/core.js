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
        inputLiquids: (b.input_liquids || []).map(function (p) { return { name: p[0], perSecond: p[1] }; }),
        outputLiquids: (b.output_liquids || []).map(function (p) { return { name: p[0], perSecond: p[1] }; }),
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

    var pumps = new Map();
    (data.pumps || []).forEach(function (p) {
      pumps.set(p.name, {
        name: p.name, size: p.size || 1, icon: p.icon || "",
        perSecond: p.perSecond || 0, liquid: p.liquid || "water",
        kind: p.kind || "Pump", power: p.power || 0,
        inputs: (p.inputs || []).map(function (i) { return [i[0], i[1]]; }),
        inputLiquids: (p.inputLiquids || []).map(function (i) { return [i[0], i[1]]; })
      });
    });

    /* 外部入料方式（灰带/蓝带/接收台…）：perSecond=0 视为不限速 */
    var channels = (data.channels || []).map(function (c) {
      return { key: c.key, label: c.label || c.key, block: c.block || "",
               perSecond: c.perSecond || 0, power: c.power || 0, note: c.note || "" };
    });
    var channelsByKey = new Map();
    channels.forEach(function (c) { channelsByKey.set(c.key, c); });

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
                     kind: prod ? prod.kind : "",
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
      pumps: pumps,
      channels: channels,
      channelsByKey: channelsByKey,
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
          liquids: liquidDemand(idx, machines),
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
    // 目标建筑自身也进建造清单（电力/液体要一起算进去：ex.result 里还没有它）
    res.machines[blockName] = (res.machines[blockName] || 0) + count;
    res.machines = sortMachines(res.machines);
    (b.inputLiquids || []).forEach(function (l) {
      res.liquidExtra = res.liquidExtra || {};
      res.liquidExtra[l.name] = (res.liquidExtra[l.name] || 0) + count * l.perSecond;
    });
    recalcPower(idx, res);
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
    var p = idx.pumps.get(name);
    if (p) {
      return { name: name, kind: "pump", size: p.size, power: p.power, icon: p.icon,
               craftTime: 0, cps: 0, inputs: [], outputs: [],
               inputLiquids: p.inputLiquids.map(function (l) { return { name: l[0], perSecond: l[1] }; }),
               plans: [], upgrades: [], factoryKind: "",
               perSecond: p.perSecond, liquid: p.liquid };
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

  /* 抽水泵：要 rate 个/s 的某种液体，要几台泵、多少电、吃什么 */
  function pumpPlan(data, liquidName, amount, pumpName) {
    var idx = indexOf(data);
    var p = idx.pumps.get(pumpName);
    if (!p) throw new Error("未知抽水泵：" + pumpName);
    if (p.liquid !== liquidName) {
      throw new Error(p.name + " 抽的是 " + p.liquid + "，不是 " + liquidName);
    }
    var count = p.perSecond > 0 ? Math.ceil((amount || 0) / p.perSecond - 1e-9) : 0;
    return {
      name: p.name, icon: p.icon, size: p.size, liquid: p.liquid, kind: p.kind,
      count: count, perSecondEach: p.perSecond, perSecondTotal: p.perSecond * count,
      powerEach: p.power, power: p.power * count,
      inputs: p.inputs.map(function (i) { return { name: i[0], perSecond: i[1] * count }; }),
      inputLiquids: p.inputLiquids.map(function (i) { return { name: i[0], perSecond: i[1] * count }; }),
      surplus: p.perSecond * count - (amount || 0)
    };
  }

  /* 兵厂 T1→T5 大循环：要产 rate 个/s 的顶级单位，每级要几台、吃多少料。
   *
   * 模型（不是简单 1:1）：
   *   每级有两个比例参数
   *     inPer   —— 升 1 个这级单位要吃掉几个下级单位（默认 1；T1 没有下级 = 0）
   *     outPer  —— 这个方块一次产出几个这级单位（默认 1）
   *   需要的下级速率： need[k-1] = need[k] * inPer[k]
   *   每台产能：       capacity[k] = count[k] * perSecond[k] * outPer[k]
   *   一级单位能变成多少个顶级单位： factor[k] = Π_{j>k} (1 / inPer[j])
   *   整条链的产出受最慢的一段限制： achieved = min_k (capacity[k] * factor[k])
   *   材料按"整条链实际只跑 achieved"算，多放的机器只会闲置：
   *     craft/s = (achieved / factor[k]) / outPer[k]，材料 = items × craft/s
   *
   * opts.ratios = { 单位名: inPer }  覆盖每级消耗比（例如 {mace: 2} = 2 个 dagger 升 1 个 mace）
   * opts.outs   = { 单位名: outPer } 覆盖每级一次产出数（例如 {mace: 2} = 一次出 2 个）
   */
  function unitChain(data, startUnit, rate, opts) {
    var idx = indexOf(data);
    var chain = null;
    for (var i = 0; i < idx.unitChains.length; i++) {
      if (idx.unitChains[i].start === startUnit) { chain = idx.unitChains[i]; break; }
    }
    if (!chain) throw new Error(startUnit + " 没有 T1→T5 升级链");

    var cfg = opts || {};
    var ratios = cfg.ratios || {};
    var outs = cfg.outs || {};
    var n = chain.tiers.length;

    var stages = chain.tiers.map(function (t, k) {
      var inPer = k === 0 ? 0 : (ratios[t.unit] !== undefined ? Number(ratios[t.unit]) : 1);
      var outPer = outs[t.unit] !== undefined ? Number(outs[t.unit]) : 1;
      if (!(inPer >= 0)) inPer = 1;
      if (!(outPer > 0)) outPer = 1;
      return { t: t, tier: k + 1, inPer: inPer, outPer: outPer,
               each: t.perSecond * outPer };
    });

    /* 两种口径：
     *   ① rate  —— 想要顶级单位 x 个/s
     *   ② topCount/topTier —— 想要 N 台第 T 级的厂满效跑（页面上写「5t5」）
     */
    var topIdx = n - 1;
    var topCount = 0;
    if (cfg.topCount > 0) {
      topIdx = Math.max(0, Math.min(n - 1, (cfg.topTier || n) - 1));
      topCount = Number(cfg.topCount);
    }
    var want = topCount > 0 ? topCount * stages[topIdx].each : Math.max(0, rate || 0);

    /* 从顶级往下推"每级需要产多少" */
    var need = new Array(n);
    for (var k = 0; k < n; k++) need[k] = 0;
    need[topIdx] = want;
    for (var k1 = topIdx; k1 > 0; k1--) need[k1 - 1] = need[k1] * stages[k1].inPer;

    /* 每级台数与产能 */
    stages.forEach(function (s, k) {
      if (topCount > 0 && k === topIdx) {
        s.count = topCount;                                   // 顶级就是用户点名的那几台
      } else {
        s.count = (need[k] > 0 && s.each > 0) ? Math.ceil(need[k] / s.each - 1e-9) : 0;
      }
      s.capacity = s.count * s.each;
    });

    /* 一级单位折算成顶级单位 */
    var factor = new Array(n);
    for (var k3 = 0; k3 < n; k3++) factor[k3] = 0;
    factor[topIdx] = 1;
    for (var k2 = topIdx - 1; k2 >= 0; k2--) factor[k2] = factor[k2 + 1] / (stages[k2 + 1].inPer || 1);

    var achieved = 0;
    if (want > 0) {
      achieved = Infinity;
      for (var k4 = 0; k4 <= topIdx; k4++) {
        achieved = Math.min(achieved, stages[k4].capacity * factor[k4]);
      }
      if (!isFinite(achieved)) achieved = 0;
    }
    var bottleneck = 0;
    for (var k5 = 0; k5 <= topIdx; k5++) {
      if (stages[k5].capacity * factor[k5] < stages[bottleneck].capacity * factor[bottleneck] - 1e-12) bottleneck = k5;
    }

    var rows = [];
    var materials = {};
    var power = 0;
    stages.forEach(function (s, k) {
      var t = s.t;
      var stageActual = factor[k] > 0 ? achieved / factor[k] : 0;   // 这级实际产出（个/s）
      var crafts = s.outPer > 0 ? stageActual / s.outPer : 0;      // 这级方块每秒跑几次
      var rowItems = t.items.map(function (it) {
        var v = it.amount * crafts;
        materials[it.name] = (materials[it.name] || 0) + v;
        return { name: it.name, perSecond: v,
                 perSecondAtFull: s.count > 0 ? it.amount * (s.capacity / s.outPer) : 0 };
      });
      power += s.count * t.power;
      /* 1 台这级的机器，够带几台上一级的机器（不是 1:1：constructTime 不同） */
      var upper = stages[k + 1];
      var feedsNext = null;
      if (upper && upper.count > 0 && upper.t.perSecond > 0) {
        feedsNext = s.each / (upper.t.perSecond * upper.outPer);
      }
      rows.push({
        tier: s.tier, unit: t.unit, block: t.block, kind: t.kind || "",
        icon: idx.unitIcons[t.unit] || "",
        blockIcon: (idx.blocks.get(t.block) || {}).icon || "",
        perSecond: s.each, count: s.count,
        inPer: s.inPer, outPer: s.outPer, need: round(need[k]),
        capacity: round(s.capacity), stageActual: round(stageActual),
        actual: round(achieved), feedsNext: feedsNext === null ? null : round(feedsNext),
        utilization: (s.capacity * factor[k]) > 0 ? achieved / (s.capacity * factor[k]) : 0,
        bottleneck: k === bottleneck,
        powerEach: t.power, power: s.count * t.power, items: rowItems
      });
    });

    return {
      start: startUnit, top: chain.tiers[chain.tiers.length - 1].unit,
      tiers: n, rate: round(want) || want,
      topTier: topIdx + 1, topCount: topCount || null,
      achieved: round(achieved),
      bottleneck: rows[bottleneck] ? rows[bottleneck].unit : null,
      bottleneckTier: rows[bottleneck] ? rows[bottleneck].tier : null,
      rows: rows, materials: sortMachines(materials), power: power
    };
  }

  /* 「5t5」口径：N 台第 T 级的厂满效跑，反推上面各级要几台、整链要多少资源 */
  function chainFromTop(data, startUnit, tier, count, opts) {
    var cfg = {};
    Object.keys(opts || {}).forEach(function (k) { cfg[k] = opts[k]; });
    cfg.topTier = tier;
    cfg.topCount = count;
    return unitChain(data, startUnit, 0, cfg);
  }

  /* 默认优先挑这些“正统地面线”：一个方块的同一个工厂可以服务多条升级线（如 tetrative 同时升地面/空军/机甲） */
  var CHAIN_PREF = ["dagger", "nova", "crawler", "flare", "mono", "risso", "retusa", "stell", "merui", "elude"];

  /* 这个方块可能属于几条链？（每条给出 {start, tier}） */
  function chainsForBlock(data, blockName) {
    var idx = indexOf(data);
    var out = [];
    (idx.unitChains || []).forEach(function (ch) {
      for (var i = 0; i < ch.tiers.length; i++) {
        if (ch.tiers[i].block === blockName) {
          out.push({ start: ch.start, top: ch.top, tier: i + 1, tiers: ch.tiers.length });
          break;
        }
      }
    });
    out.sort(function (a, b) {
      var ia = CHAIN_PREF.indexOf(a.start), ib = CHAIN_PREF.indexOf(b.start);
      if (ia < 0) ia = 99;
      if (ib < 0) ib = 99;
      return (ia - ib) || (a.start < b.start ? -1 : 1);
    });
    return out;
  }

  /* 按「选了哪个兵厂 + 几台」走大循环：在该方块所在的链上定位层级，再交给 chainFromTop */
  function chainFromBlock(data, blockName, count, opts) {
    var cands = chainsForBlock(data, blockName);
    if (!cands.length) return null;
    var pick = cands[0];
    if (opts && opts.chainStart) {
      cands.forEach(function (c) { if (c.start === opts.chainStart) pick = c; });
    }
    return chainFromTop(data, pick.start, pick.tier, count, opts);
  }

  /* 机器清单带来的液体需求（每秒）：方块/兵厂/多产物方块的输入液体 + 钻头加速液 */
  function liquidDemand(idx, machines, extra) {
    var acc = {};
    Object.keys(machines || {}).forEach(function (name) {
      var b = anyBlock(idx, name);
      if (!b) return;
      (b.inputLiquids || []).forEach(function (l) {
        var nm = l.name !== undefined ? l.name : l[0];
        var ps = l.perSecond !== undefined ? l.perSecond : l[1];
        acc[nm] = (acc[nm] || 0) + machines[name] * ps;
      });
    });
    Object.keys(extra || {}).forEach(function (k) { acc[k] = (acc[k] || 0) + extra[k]; });
    return Object.keys(acc).sort().map(function (k) { return { name: k, perSecond: round(acc[k]) }; });
  }

  function recalcPower(idx, res) {
    var power = 0;
    Object.keys(res.machines).forEach(function (name) {
      var mb = anyBlock(idx, name);
      if (mb && mb.kind !== "generator") power += res.machines[name] * mb.power;
    });
    /* 外部入料方式（布桥/质驱）的电力不算在方块里，单独累加，否则会被这次重算抹掉 */
    res.power = power + (res.extraPower || 0);
    res.liquids = liquidDemand(idx, res.machines, res.liquidExtra);
    return res.power;
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
        if (plan.liquid) {
          res.liquidExtra = res.liquidExtra || {};
          res.liquidExtra[plan.liquid.name] = (res.liquidExtra[plan.liquid.name] || 0) + plan.liquid.perSecond;
        }
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
      } else if (type === "import" && c.via) {
        /* 外部运入细分成 灰带/蓝带/绿带/布桥/质驱/接收台/其它：
         * perSecond>0 的按吞吐算要几条，perSecond=0 视为不限速（接收台/其它） */
        var ch = idx.channelsByKey.get(c.via);
        if (!ch) throw new Error("未知入料方式：" + c.via);
        row.via = ch.key;
        row.viaLabel = ch.label;
        if (ch.perSecond > 0) {
          row.count = Math.ceil(need / ch.perSecond - 1e-9);
          row.perSecondEach = ch.perSecond;
          row.perSecondTotal = round(row.count * ch.perSecond);
          row.power = round(row.count * ch.power);
          res.extraPower = (res.extraPower || 0) + row.power;
        } else {
          row.count = null;
          row.perSecondEach = null;
          row.perSecondTotal = null;
          row.power = 0;
        }
      }
      sources.push(row);
    });
    res.sources = sources;
    res.machines = sortMachines(res.machines);

    /* ---- 液体来源：运入 / 抽水机（自动补台数；泵自己也吃液体，最多迭代 6 轮）---- */
    var pumpCfg = {};
    Object.keys(cfg).forEach(function (k) {
      if (cfg[k] && cfg[k].type === "pump") pumpCfg[k] = cfg[k];
    });
    var liquidSources = [];
    if (Object.keys(pumpCfg).length) {
      var base = {};
      Object.keys(res.machines).forEach(function (k) { base[k] = res.machines[k]; });
      var counts = {};
      for (var pass = 0; pass < 6; pass++) {
        res.machines = {};
        Object.keys(base).forEach(function (k) { res.machines[k] = base[k]; });
        Object.keys(counts).forEach(function (liq) {
          if (counts[liq] > 0) {
            var pn = pumpCfg[liq].pump || "mechanical-pump";
            res.machines[pn] = (res.machines[pn] || 0) + counts[liq];
          }
        });
        recalcPower(idx, res);
        var changed = false;
        res.liquids.forEach(function (l) {
          var c = pumpCfg[l.name];
          if (!c) return;
          var p = idx.pumps.get(c.pump || "mechanical-pump");
          if (!p) throw new Error("未知抽水泵：" + (c.pump || "mechanical-pump"));
          if (p.liquid !== l.name) throw new Error(p.name + " 抽的是 " + p.liquid + "，不是 " + l.name);
          var n = p.perSecond > 0 ? Math.ceil(l.perSecond / p.perSecond - 1e-9) : 0;
          if ((counts[l.name] || 0) !== n) { counts[l.name] = n; changed = true; }
        });
        if (!changed) break;
      }
      res.machines = sortMachines(res.machines);
      recalcPower(idx, res);
      Object.keys(counts).sort().forEach(function (liq) {
        var need = 0;
        res.liquids.forEach(function (l) { if (l.name === liq) need = l.perSecond; });
        var plan = pumpPlan(data, liq, need, pumpCfg[liq].pump || "mechanical-pump");
        liquidSources.push({
          liquid: liq, type: "pump", pump: plan.name, count: plan.count,
          perSecondEach: plan.perSecondEach, perSecondTotal: plan.perSecondTotal,
          power: plan.power, inputs: plan.inputs, inputLiquids: plan.inputLiquids,
          icon: plan.icon, surplus: plan.surplus
        });
      });
    }
    res.liquidSources = liquidSources;

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
      } else if (b && b.kind === "pump") {
        outputs = ["抽 " + b.liquid + " " + round(b.perSecond * count) + "/s"];
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
              separatorPlan: separatorPlan, unitChain: unitChain, chainFromTop: chainFromTop,
              chainFromBlock: chainFromBlock, chainsForBlock: chainsForBlock,
              pumpPlan: pumpPlan,
              applySources: applySources, recalcPower: recalcPower,
              liquidDemand: liquidDemand };
  global.RatioCore = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
