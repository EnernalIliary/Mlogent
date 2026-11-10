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

  /* 外部运入的默认入料方式：蓝带（12.015/s）。"外部入料按蓝带默认"就是这里，
   * 网页下拉 / CLI / 卡片都读这一个常量；要换成绿带或接收台只改这一行。 */
  var DEFAULT_CHANNEL = "belt-blue";

  /* 发电设备：建筑页选中发电厂时的默认燃料（不做电力递归——发电厂自己耗的电只用"自耗"字段展示，
   * 不再倒推需要更多发电厂，避免无限套娃）。 */
  var DEFAULT_GENERATOR = "combustion-generator";
  var DEFAULT_FUEL = "coal";

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

    /* 多产物方块（分离机 / 解离机）也是"能产某物品的方块"，要能进递归候选：
     * 视图与 anyBlock 的 multi 分支同形（inputs/outputs 归一成每 craft 量），
     * 于是 perSecond(视图, item) = 数据里的每秒量（= cps × 份额），need() 按台数反推即可。
     * 液体输入（分离机的矿渣）单独放 inputLiquids，交给液体自产那一层去补。 */
    var multiViews = new Map();
    var multiByOutput = new Map();
    multi.forEach(function (m) {
      var view = { name: m.name, kind: "multi", isMulti: true, size: m.size, power: m.power,
                   icon: m.icon, craftTime: m.craftTime, cps: m.cps,
                   inputs: m.inputs.map(function (i) { return { name: i[0], amount: i[1] / (m.cps || 1) }; }),
                   inputLiquids: m.inputLiquids.map(function (l) { return { name: l[0], perSecond: l[1] }; }),
                   outputLiquids: [],
                   outputs: m.outputs.map(function (o) { return { name: o[0], amount: o[1] / (m.cps || 1), share: o[2] }; }),
                   plans: [], upgrades: [], factoryKind: "" };
      multiViews.set(m.name, view);
      m.outputs.forEach(function (o) {
        if (!multiByOutput.has(o[0])) multiByOutput.set(o[0], []);
        multiByOutput.get(o[0]).push(view);
      });
    });

    var pumps = new Map();
    (data.pumps || []).forEach(function (p) {
      pumps.set(p.name, {
        name: p.name, size: p.size || 1, icon: p.icon || "",
        perSecond: p.perSecond || 0, liquid: p.liquid || "water",
        kind: p.kind || "Pump", power: p.power || 0,
        /* Attribute 通用化：按 pumpAmount/validTiles/attribute 可以重算任意属性下的产量 */
        pumpAmount: p.pumpAmount || 0, validTiles: p.validTiles || 0,
        attribute: p.attribute || "",
        floorAttr: p.floorAttr || 0, floorName: p.floorName || "",
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

    /* 液体来源索引（自产液体用）
     *   liquidPumps —— 钻井：pumps 里 perSecond>0 的（oil-extractor 15/s，吃 sand 1/s）
     *   liquidMakers —— 转化方块：output_liquids 非空的物品工厂（spore-press 0.9/s，吃 spore-pod 1）
     * 两者都按"单位产能高、入料少"排好序，挑选时取第一个。 */
    var liquidPumps = new Map();
    pumps.forEach(function (p) {
      if (!(p.perSecond > 0)) return;
      if (!liquidPumps.has(p.liquid)) liquidPumps.set(p.liquid, []);
      liquidPumps.get(p.liquid).push(p);
    });
    liquidPumps.forEach(function (arr) {
      arr.sort(function (a, b) {
        /* 优先不喝液体的泵（reinforced-pump 要 hydrogen 1.5/s，会绕出氢氧互供的死循环），
         * 再比单位产能（越大越省地方），最后比耗电与名字。 */
        var al = a.inputLiquids.length ? 1 : 0, bl = b.inputLiquids.length ? 1 : 0;
        if (al !== bl) return al - bl;
        return (b.perSecond - a.perSecond) || (a.power - b.power)
            || (a.name < b.name ? -1 : a.name > b.name ? 1 : 0);
      });
    });
    var liquidMakers = new Map();
    blocks.forEach(function (b) {
      b.outputLiquids.forEach(function (l) {
        if (!liquidMakers.has(l.name)) liquidMakers.set(l.name, []);
        liquidMakers.get(l.name).push({
          block: b, perSecond: l.perSecond,
          inputs: b.inputs.map(function (i) { return { name: i.name, amount: i.amount * b.cps }; })
        });
      });
    });
    liquidMakers.forEach(function (arr) {
      arr.sort(function (a, b) {
        return (a.block.inputs.length - b.block.inputs.length) || (b.perSecond - a.perSecond)
            || (a.block.name < b.block.name ? -1 : a.block.name > b.block.name ? 1 : 0);
      });
    });

    return {
      items: items,
      itemIcons: itemIcons,
      itemProps: itemProps,
      generators: generators,
      drills: drills,
      multi: multi,
      pumps: pumps,
      liquidPumps: liquidPumps,
      liquidMakers: liquidMakers,
      liquidColors: data.liquid_colors || {},
      /* 油田属性默认值（数据里 Fracker 的 perSecond 就是按这个属性算的） */
      oilFloor: (function () {
        var f = 0;
        pumps.forEach(function (p) { if (p.kind === "Fracker" && p.floorAttr > 0) f = p.floorAttr; });
        return f || 1.5;
      })(),
      liquidIcons: data.liquid_icons || {},
      channels: channels,
      channelsByKey: channelsByKey,
      defaultChannel: DEFAULT_CHANNEL,
      unitProducers: unitProducers,
      unitChains: chains,
      unitIcons: data.unit_icons || {},
      snapshot: data.snapshot || "",
      itemSet: new Set(items),
      blocks: blocks,
      multiViews: multiViews,
      /* 列出用：物品工厂 + 多产物方块（分离机/解离机）——配方下拉、递归树里能看到它们 */
      producersOf: function (item) {
        return (byOutput.get(item) || []).concat(multiByOutput.get(item) || []);
      },
      /* 自动展开用：只有单一产物工厂。多产物方块要"指定配方"或 opts.multi 才参与，
       * 否则铜/铅/钛这类本该挖矿来的物品会被自动改建成"吃矿渣的分离机"，把默认结果全带偏。 */
      autoProducersOf: function (item) { return byOutput.get(item) || []; },
      hasMultiProducer: function (item) { return (multiByOutput.get(item) || []).length > 0; },
      multiProducersOf: function (item) { return multiByOutput.get(item) || []; },
      shareOf: function (block, item) {
        var hit = (block.outputs || []).filter(function (o) { return o.name === item; })[0];
        return hit && hit.share != null ? hit.share : null;
      },
      /* 多产物方块的"顺带产物"：同一台机器一起出、但不是本次需求的东西 */
      byproductsOf: function (block, item, n) {
        if (!block || !block.isMulti) return null;
        return (block.outputs || []).filter(function (o) { return o.name !== item; })
          .map(function (o) { return { name: o.name, share: o.share || 0,
                                       perSecond: round(o.amount * block.cps * (n || 0)) }; });
      },
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

  /* 选配方（两个入口共用：单目标展开 / 混合厂）
   * 优先"不引入新物品"的配方（免得绕出奇怪的长链），其次总产出刚好盖住需求的，
   * 再其次方块占地小的，最后按名字定序（保证确定性）。 */
  function chooseProducer(idx, item, amount, fmap, servable, liqOk, allowMulti) {
    var forced = fmap && fmap[item];
    var cands = (forced || allowMulti) ? idx.producersOf(item) : idx.autoProducersOf(item);
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
      if (!introduces && liqOk) {
        introduces = !(b.inputLiquids || []).every(function (l) { return liqOk(l.name); });
      }
      scored.push({ block: b, n: n, introduces: introduces, actual: n * per });
    });
    if (!scored.length) throw new Error(item + " 没有可用配方");
    scored.sort(function (a, b) {
      if (a.introduces !== b.introduces) return a.introduces ? 1 : -1;
      /* 同样"不引入新东西"时，优先单一产物工厂，多产物方块只在被指定/没别的配方时用 */
      var am = a.block.isMulti ? 1 : 0, bm = b.block.isMulti ? 1 : 0;
      if (am !== bm) return am - bm;
      if (Math.abs(a.actual - b.actual) > 1e-9) return a.actual - b.actual;
      var as = a.block.size * a.block.size, bs = b.block.size * b.block.size;
      if (as !== bs) return as - bs;
      return a.block.name < b.block.name ? -1 : a.block.name > b.block.name ? 1 : 0;
    });
    return scored[0];
  }

  /* 液体来源方案：要 amount 个/s 的某种液体，用钻井还是转化方块、要几台、吃什么。
   * how  = "auto"（钻井优先）| "pump"（钻井）| "make"（转化方块）| "import"（不自产）
   * name 可选：指定泵 / 转化方块的方块名（如 oil 用 spore-press 而不是 oil-extractor）。 */
  /* 环境属性（Attribute.*）覆盖：抽液方块的产量取决于它看的地板属性——
   *   SolidPump / Fracker：每秒 = pumpAmount × 60 × (validTiles + 属性均值)
   *   Pump（吃地形水）：与属性无关，按有效水格数算
   * attrs 形如 {oil:0.7, water:1.2}；没给的属性沿用数据里的默认值（oil 默认满黑沙 1.5）。
   * 返回一份浅拷贝的 index（pumps 与 liquidPumps 都换成重算后的对象），不污染缓存。 */
  function applyAttrs(idx, attrs) {
    if (!attrs) return idx;
    var map = {}, any = false;
    Object.keys(attrs).forEach(function (k) {
      var v = Number(attrs[k]);
      if (isFinite(v) && v >= 0) { map[k] = v; any = true; }
    });
    if (!any) return idx;
    var pumps = new Map();
    idx.pumps.forEach(function (p, k) {
      var name = p.attribute || "";
      var given = name && map[name] != null ? map[name] : null;
      if (given == null || !(p.pumpAmount > 0) || p.kind === "Pump") {
        pumps.set(k, p);
        return;
      }
      var want = round(p.pumpAmount * 60 * ((p.validTiles || 0) + given));
      if (Math.abs(want - p.perSecond) < 1e-9) {
        pumps.set(k, p);
        return;
      }
      var q = {};
      Object.keys(p).forEach(function (key) { q[key] = p[key]; });
      q.perSecond = want;
      q.attrValue = given;
      if (name === "oil") q.floorAttr = given;
      pumps.set(k, q);
    });
    var liquidPumps = new Map();
    pumps.forEach(function (p) {
      if (!(p.perSecond > 0)) return;
      if (!liquidPumps.has(p.liquid)) liquidPumps.set(p.liquid, []);
      liquidPumps.get(p.liquid).push(p);
    });
    liquidPumps.forEach(function (arr) {
      arr.sort(function (a, b) {
        var al = a.inputLiquids.length ? 1 : 0, bl = b.inputLiquids.length ? 1 : 0;
        if (al !== bl) return al - bl;
        return (b.perSecond - a.perSecond) || (a.power - b.power)
            || (a.name < b.name ? -1 : a.name > b.name ? 1 : 0);
      });
    });
    var out = {};
    Object.keys(idx).forEach(function (key) { out[key] = idx[key]; });
    out.pumps = pumps;
    out.liquidPumps = liquidPumps;
    out.attrs = {};
    Object.keys(idx.attrs || {}).forEach(function (k) { out.attrs[k] = idx.attrs[k]; });
    Object.keys(map).forEach(function (k) { out.attrs[k] = map[k]; });
    out.oilFloor = out.attrs.oil != null ? out.attrs.oil : (idx.oilFloor || 1.5);
    return out;
  }

  /* 兼容旧入口：--oilfloor / opts.floor 就是 attrs.oil */
  function applyFloor(idx, floor) {
    if (!(floor > 0)) return idx;
    return applyAttrs(idx, { oil: floor });
  }

  /* 把「数字或属性表」统一成属性表 */
  function attrsOf(x) {
    if (x == null) return null;
    if (typeof x === "number") return x > 0 ? { oil: x } : null;
    var keys = Object.keys(x).filter(function (k) { return Number(x[k]) >= 0; });
    if (!keys.length) return null;
    var out = {};
    keys.forEach(function (k) { out[k] = Number(x[k]); });
    return out;
  }

  function liquidSourcePlan(idx, liquid, amount, how, name, flow) {
    var pumps = idx.liquidPumps.get(liquid) || [];
    var makers = idx.liquidMakers.get(liquid) || [];
    var pump = null, maker = null;
    if (how === "pump") {
      pump = pumps.filter(function (p) { return !name || p.name === name; })[0] || null;
      if (!pump) throw new Error("没有钻井能抽液体 " + liquid + (name ? "（" + name + "）" : ""));
    } else if (how === "make" || how === "press") {
      maker = makers.filter(function (m) { return !name || m.block.name === name; })[0] || null;
      if (!maker) throw new Error("没有方块能把物品转成液体 " + liquid + (name ? "（" + name + "）" : ""));
    } else {
      /* auto：指定了方块名就先按名字找（钻井或转化方块都行），否则钻井优先、没有钻井再用转化方块 */
      if (name) {
        pump = pumps.filter(function (p) { return p.name === name; })[0] || null;
        if (!pump) maker = makers.filter(function (m) { return m.block.name === name; })[0] || null;
        if (!pump && !maker) throw new Error("没有钻井或转化方块能产液体 " + liquid + "（" + name + "）");
      } else {
        pump = pumps[0] || null;
        if (!pump) maker = makers[0] || null;
      }
    }
    if (pump) {
      /* flow（归一化）模式：不取整，台数可以是小数。
       * 没指定具体泵时按"大泵铺满 + 最小一档吃零头"给连续解（总量正好等于需求，没有富余）。 */
      if (flow && !name) {
        var fmix = pumpMixFlow(idx, liquid, amount);
        if (fmix) {
          var fcounts = {}, ftotal = 0;
          fmix.pumps.forEach(function (t) { fcounts[t.pump] = t.count; ftotal += t.count; });
          var ffirst = idx.pumps.get(fmix.pumps[0].pump);
          return {
            type: "pump", block: fmix.pumps[0].pump, count: ftotal,
            perSecond: ftotal > 0 ? amount / ftotal : 0,
            counts: fcounts, mix: fmix.pumps,
            inputs: ((ffirst && ffirst.inputs) || []).map(function (i) { return { name: i[0], amount: i[1] }; })
          };
        }
      }
      var n = flow ? amount / pump.perSecond
                   : Math.max(1, Math.ceil(amount / pump.perSecond - 1e-9));
      var plan = {
        type: "pump", block: pump.name, count: n, perSecond: pump.perSecond,
        inputs: pump.inputs.map(function (i) { return { name: i[0], amount: i[1] }; })
      };
      /* 没指定具体泵时，用"小泵 N 台 + 中泵 M 台 + 大泵 K 台"的加和来满足，避免一台大泵富余太多
       * （flow 模式不拆档：已经用小数台数精确满足了，拆档反而变成整数又回到取整问题） */
      if (!name && !flow) {
        var mix = pumpMixIdx(idx, liquid, amount);
        if (mix) {
          var counts = {}, total = 0;
          mix.pumps.forEach(function (t) { counts[t.pump] = t.count; total += t.count; });
          plan.counts = counts;
          plan.count = total;
          plan.mix = mix.pumps;
          plan.perSecond = mix.total / total;
          var first = idx.pumps.get(mix.pumps[0].pump);
          plan.block = mix.pumps[0].pump;
          plan.inputs = ((first && first.inputs) || []).map(function (i) { return { name: i[0], amount: i[1] }; });
        }
      }
      return plan;
    }
    if (maker) {
      var m = flow ? amount / maker.perSecond
                   : Math.max(1, Math.ceil(amount / maker.perSecond - 1e-9));
      return {
        type: "make", block: maker.block.name, count: m, perSecond: maker.perSecond,
        inputs: maker.inputs.map(function (i) { return { name: i.name, amount: i.amount }; })
      };
    }
    return null;
  }

  /* ---------------------------------------------------------------- *
   * 物品需求的递归展开（两种入口共用）
   * ---------------------------------------------------------------- */
  /* flow = "归一化"模式：台数不向上取整（可以是 1.5 台），所有速率都按每秒精确守恒。
   * 这是学 TMI 的口径：先给"满效等价的分数台数"，要建整台时再看 eff = 分数/向上取整。 */
  function makeExpander(idx, boundary, force, maxDepth, allowMulti, flow) {
    var flowMode = !!flow;
    var bset = new Set(boundary || []);
    var fmap = force || {};
    var machines = {};
    var order = [];
    var demand = {};
    var byprod = {};
    var warnings = [];
    var cycles = [];
    var maxDepth_ = maxDepth || MAX_DEPTH;

    function servable(item, seen) {
      if (bset.has(item)) return true;
      if (seen.has(item)) return false;
      var cands = allowMulti ? idx.producersOf(item) : idx.autoProducersOf(item);
      if (!cands.length) return false;
      var next = new Set(seen); next.add(item);
      return cands.some(function (b) {
        return b.inputs.every(function (i) { return servable(i.name, next); });
      });
    }

    /* 液体能不能自给：在边界里，或者有钻井/转化方块能产（矿渣这种没来源的就算"引入"） */
    function liqOk(name) {
      if (bset.has(name)) return true;
      return !!liquidSourcePlan(idx, name, 1, "auto");
    }

    function choose(item, amount) {
      return chooseProducer(idx, item, amount, fmap, servable, liqOk, allowMulti);
    }

    /* 环检测：item 在自己的祖先链里出现过 => 这条链成环了。
     * 停在这里（不再往上展开，否则台数会一轮轮放大），把缺的量子按"环内自供 + 外部补"记下来。 */
    function need(item, amount, depth, parentNode, chain) {
      if (amount <= 1e-9) return null;
      var path = chain || [];
      var node = { item: item, amount: amount, block: null, count: 0, children: [] };
      if (parentNode) parentNode.children.push(node);
      var at = path.indexOf(item);
      if (at >= 0) {
        node.reason = "cycle";
        node.cycle = path.slice(at).concat([item]);
        var label = node.cycle.join(" ← ");
        demand[item] = (demand[item] || 0) + amount;
        cycles.push({ path: node.cycle.slice(), item: item, amount: round(amount) });
        if (warnings.indexOf("循环产线：" + label) < 0) {
          warnings.push("循环产线：" + label
            + "（环内自供，停在这一层不再展开；缺的量按外部输入记在 " + item + " 上）");
        }
        return node;
      }
      if (bset.has(item) || depth > maxDepth_) {
        node.reason = bset.has(item) ? "boundary" : "depth";
        demand[item] = (demand[item] || 0) + amount;
        return node;
      }
      var cands = allowMulti ? idx.producersOf(item) : idx.autoProducersOf(item);
      if (!cands.length) {
        node.reason = "no-recipe";
        demand[item] = (demand[item] || 0) + amount;
        /* 只有多产物方块能产（铜/铅/钛/沙…）时给个提示：想让它进递归树就在"指定配方"里选 */
        warnings.push(item + " 没有配方产出，按外部输入处理"
          + (idx.hasMultiProducer(item)
             ? "（分离机/解离机能产它，要展开请在“指定配方”里选，或加 --multi）" : ""));
        return node;
      }
      var pick = choose(item, amount);
      var b = pick.block;
      var per = idx.perSecond(b, item);
      var n = flowMode ? (per > 0 ? amount / per : 0)
                       : Math.max(1, Math.ceil(amount / per - 1e-9));
      node.block = b.name;
      node.kind = b.kind || "item";
      node.count = n;
      node.per = per;
      node.actual = n * node.per;
      /* 多产物方块：记下"这个物品占多少份额"和同一批机器顺带出的其它产物（不进需求，只做展示） */
      if (b.isMulti) {
        node.share = idx.shareOf(b, item);
        node.byproducts = idx.byproductsOf(b, item, n);
        (node.byproducts || []).forEach(function (o) {
          byprod[o.name] = (byprod[o.name] || 0) + o.perSecond;
        });
      }
      machines[b.name] = (machines[b.name] || 0) + n;
      order.push({ block: b.name, count: n, item: item });
      var nextPath = path.concat([item]);
      idx.inputPerSecond(b).forEach(function (i) {
        need(i.name, n * i.amount, depth + 1, node, nextPath);
      });
      return node;
    }

    /* 液体自产：机器清单里没人供、又不在 boundary 的液体，用钻井或转化方块补机器。
     * opts.liquid = {oil:"make"|"pump"|"import"} 指定方式；opts.liquidName = {oil:"spore-press"} 指定方块；
     * 补出来的机器如果吃物品（钻井吃 sand、spore-press 吃 spore-pod），走 need() 继续往上展开。 */
    function resolveLiquids(opts, extraLiquids) {
      opts = opts || {};
      var howMap = opts.liquid || {};
      var nameMap = opts.liquidName || {};
      var used = {};
      for (var pass = 0; pass < 6; pass++) {
        var net = {};
        Object.keys(extraLiquids || {}).forEach(function (k) { net[k] = extraLiquids[k]; });
        Object.keys(machines).forEach(function (name) {
          var b = anyBlock(idx, name);   // 钻井类液体源也在 machines 里，要一起算（oil-extractor 吃 water 9/s）
          if (!b) return;
          (b.inputLiquids || []).forEach(function (l) { net[l.name] = (net[l.name] || 0) + machines[name] * l.perSecond; });
          (b.outputLiquids || []).forEach(function (l) { net[l.name] = (net[l.name] || 0) - machines[name] * l.perSecond; });
        });
        var changed = false;
        Object.keys(net).sort().forEach(function (liq) {
          if (!(net[liq] > 1e-9)) return;
          if (bset.has(liq)) return;
          var how = howMap[liq] || "auto";
          if (how === "import" || how === "off") return;
          var plan = liquidSourcePlan(idx, liq, net[liq], how, nameMap[liq], flowMode);
          if (!plan) return;
          /* plan.counts：多档泵加和（大泵/中泵/小泵各有台数），否则就是单一方块 count 台 */
          var want = plan.counts || {};
          if (!plan.counts) want[plan.block] = plan.count;
          var added = 0;
          Object.keys(want).sort().forEach(function (block) {
            var cur = machines[block] || 0;
            var add = want[block] - cur;
            if (add <= 0) return;
            machines[block] = cur + add;
            order.push({ block: block, count: add, item: null, liquid: liq });
            added += add;
          });
          if (!added) return;
          changed = true;
          if (!used[liq]) {
            used[liq] = { liquid: liq, type: plan.type, block: plan.block, count: 0,
                          perSecondEach: plan.perSecond, parts: plan.mix || null };
          }
          used[liq].count += added;
          plan.inputs.forEach(function (i) { need(i.name, added * i.amount, 1, null, []); });
        });
        if (!changed) break;
      }
      return used;
    }

    return {
      need: need,
      machines: machines,
      order: order,
      resolveLiquids: resolveLiquids,
      result: function (extra) {
        var power = 0;
        Object.keys(machines).forEach(function (name) {
          var b = anyBlock(idx, name);        // 多产物方块/钻井也要计电（以前只查 idx.blocks 会漏）
          if (b && b.kind !== "generator") power += machines[name] * b.power;
        });
        var out = {
          machines: machines,
          order: order,
          demand: demand,
          power: power,
          liquids: liquidDemand(idx, machines),
          byproducts: Object.keys(byprod).sort().map(function (k) {
            return { name: k, perSecond: round(byprod[k]) };
          }),
          warnings: warnings,
          cycles: cycles,
          attrs: idx.attrs || null,
          snapshot: idx.snapshot || ""
        };
        Object.keys(extra || {}).forEach(function (k) { out[k] = extra[k]; });
        return out;
      }
    };
  }

  /* 机器图上的环检测：方块 -> 它吃的物品（含液体）-> 能产这个物品的方块。
   * 液体来源（钻井 / 转化方块）也算边，所以 coal-centrifuge 吃 oil、oil-centrifuge 吃 coal
   * 这种"液体绕回来的环"也能抓到（递归展开是按树走的，看不到液体这一层）。
   * 只从"这次真的建了"的机器出发找；返回 [{ path:[方块, 物品, 方块, …, 方块] }]，
   * 同一个环只报一次（按节点集合去重）。 */
  function detectCycles(idx, machines) {
    var names = Object.keys(machines || {}).filter(function (n) { return (machines[n] || 0) > 0; });
    if (names.length < 2) return [];
    var built = new Set(names);
    var cache = new Map();
    function producersOf(item) {
      if (cache.has(item)) return cache.get(item);
      var out = [];
      (idx.producersOf(item) || []).forEach(function (b) {
        if (b && built.has(b.name)) out.push({ name: b.name, via: "item" });
      });
      (idx.liquidPumps.get(item) || []).forEach(function (p) {
        if (built.has(p.name)) out.push({ name: p.name, via: "liquid" });
      });
      (idx.liquidMakers.get(item) || []).forEach(function (m) {
        if (m.block && built.has(m.block.name)) out.push({ name: m.block.name, via: "liquid" });
      });
      cache.set(item, out);
      return out;
    }
    var adj = new Map();
    names.forEach(function (n) {
      var b = anyBlock(idx, n);
      var ins = [];
      if (b) {
        (b.inputs || []).forEach(function (i) { ins.push(i.name); });
        (b.inputLiquids || []).forEach(function (l) { ins.push(l.name); });
      }
      adj.set(n, ins.map(function (item) { return { item: item, next: producersOf(item) }; }));
    });

    var found = [], seen = new Set(), guard = 0;
    function walk(start, cur, path, items) {
      if (guard++ > 4000) return;
      var edges = adj.get(cur) || [];
      for (var i = 0; i < edges.length; i++) {
        var e = edges[i];
        for (var j = 0; j < e.next.length; j++) {
          var to = e.next[j].name;
          if (to === start && path.length >= 2) {
            var key = path.slice().sort().join("|");
            if (!seen.has(key)) {
              seen.add(key);
              found.push({ path: path.concat([start]), items: items.concat([e.item]) });
            }
          } else if (path.indexOf(to) < 0 && path.length < 8) {
            walk(start, to, path.concat([to]), items.concat([e.item]));
          }
        }
      }
    }
    names.forEach(function (n) { walk(n, n, [n], []); });
    return found;
  }

  /* 把环渲染成一行：A -[物品]-> B -[物品]-> A */
  function cycleText(loop) {
    if (!loop || !loop.path) return "";
    var out = [loop.path[0]];
    for (var i = 0; i < loop.items.length; i++) {
      out.push("-[ " + loop.items[i] + " ]->");
      out.push(loop.path[i + 1]);
    }
    return out.join(" ");
  }

  /* 把 detectCycles 的结果挂到结果上，并往 warnings 里写一条 */
  function attachLoops(idx, res) {
    res.loops = detectCycles(idx, res.machines || {});
    if (!res.warnings) res.warnings = [];
    res.loops.forEach(function (lp) {
      res.warnings.push("循环产线：" + cycleText(lp)
        + "（环内互相供料；环里产不抵耗的部分已按外部输入记）");
    });
    return res.loops;
  }

  /* 按目标物品速率（旧口径）
   * opts.liquids = "auto" 时，机器吃但没人供的液体（如 coal-centrifuge 的 oil）自动接钻井/转化方块，
   * 这就是"不允许外部输入"时把煤炭处理线（coal-centrifuge → oil-extractor）带出来的开关。 */
  function expand(data, target, rate, boundary, force, opts) {
    var idx = applyAttrs(indexOf(data), attrsOf(opts && (opts.attrs || (opts.floor > 0 ? opts.floor : null))));
    if (!idx.itemSet.has(target)) throw new Error("未知物品：" + target);
    var ex = makeExpander(idx, boundary, force, (opts && opts.maxDepth) || MAX_DEPTH,
                          !!(opts && opts.multi), !!(opts && opts.flow));
    var root = ex.need(target, rate, 0, null);
    var liquidFrom = (opts && opts.liquids) ? ex.resolveLiquids(opts) : {};
    var res = ex.result({ target: target, requested: rate, tree: root, liquidFrom: liquidFrom });
    res.oilFloor = idx.oilFloor;
    res.attrs = idx.attrs || null;
    res.flow = !!(opts && opts.flow);
    res.achieved = root && root.actual ? root.actual : 0;
    recalcPower(idx, res);          // 液体自产会把钻井/抽水泵塞进 machines，电力和液体都要重算一次
    attachLoops(idx, res);
    if (opts && opts.sources) applySources(data, res, opts.sources);
    return res;
  }

  /* 按目标建筑台数（满效，新口径）
   * opts = { boundary:[], force:{}, plan: 0, maxDepth: 12 }
   * 返回 { block, count, products:[{name,type,rate}], inputs:[{name,amount}], machines, ... }
   */
  /* 发电设备当"目标建筑"：算总发电、燃料、液体、自耗电。
   * 不递归电力：发电厂的自耗只显示，不再换算成更多发电厂。 */
  function expandGenerator(data, genName, count, opts) {
    var idx = applyAttrs(indexOf(data), attrsOf(opts && (opts.attrs || (opts.floor > 0 ? opts.floor : null))));
    opts = opts || {};
    var g = idx.generators.get(genName);
    if (!g) throw new Error("未知发电厂：" + genName);
    count = Math.max(1, Math.floor(count));
    var fuel = null;
    if ((g.fuels || []).length) {
      var want = opts.fuel || DEFAULT_FUEL;
      fuel = g.fuels.filter(function (f) { return f[0] === want; })[0]
          || g.fuels.filter(function (f) { return f[0] === g.fuels[0][0]; })[0];
    }
    var grossEach = fuel ? fuel[2] : g.perSecond;
    var netEach = grossEach - (g.powerUsage || 0);
    /* 用户 2026-11-09：其它工厂缺电不递归（电力只当数字），但发电厂当目标建筑时必须有递归树 ——
     * 燃料（煤/孢子荚/黄铀…）和液体（水/氰气…）从哪来要跟普通工厂一样展开。 */
    var ex = makeExpander(idx, opts.boundary, opts.force, opts.maxDepth || MAX_DEPTH, false, !!opts.flow);
    var root = { block: genName, count: count, item: null, amount: 0, children: [] };
    var inputs = [];
    if (fuel) inputs.push({ name: fuel[0], amount: round(fuel[1] * count) });
    inputs.forEach(function (i) { ex.need(i.name, i.amount, 1, root); });
    var extraLiq = {};
    (g.liquids || []).forEach(function (l) {
      extraLiq[l[0]] = (extraLiq[l[0]] || 0) + l[1] * count;
    });
    var liquidFrom = opts.liquids ? ex.resolveLiquids(opts, extraLiq) : {};
    var res = ex.result({
      block: genName, count: count,
      products: [{ name: "电力", type: "power", rate: round(netEach * count) }],
      inputs: inputs, tree: root, liquidFrom: liquidFrom, plan: 0, planTotal: 0
    });
    res.oilFloor = idx.oilFloor;
    res.attrs = idx.attrs || null;
    res.flow = !!opts.flow;
    res.machines[genName] = (res.machines[genName] || 0) + count;
    res.machines = sortMachines(res.machines);
    res.supply = {
      name: genName, icon: g.icon, count: count,
      grossEach: round(grossEach), netEach: round(netEach),
      gross: round(grossEach * count), net: round(netEach * count),
      grossTotal: round(grossEach * count), netTotal: round(netEach * count),
      surplus: round(netEach * count),
      selfUse: round((g.powerUsage || 0) * count),
      selfUseEach: round(g.powerUsage || 0),
      fuel: fuel ? { name: fuel[0], perSecondEach: fuel[1], perSecond: round(fuel[1] * count) } : null,
      liquids: (g.liquids || []).map(function (l) {
        return { name: l[0], perSecondEach: l[1], perSecond: round(l[1] * count) };
      })
    };
    recalcPower(idx, res);          // 发电厂 power 记 0，这里只汇总液体
    attachLoops(idx, res);
    if (opts.sources) applySources(data, res, opts.sources);
    return res;
  }

  function expandBuilding(data, blockName, count, opts) {
    var idx = applyAttrs(indexOf(data), attrsOf(opts && (opts.attrs || (opts.floor > 0 ? opts.floor : null))));
    opts = opts || {};
    if (idx.generators && idx.generators.get(blockName)) return expandGenerator(data, blockName, count, opts);
    var b = idx.blocks.get(blockName);
    if (!b) throw new Error("未知方块：" + blockName);
    if (!(count > 0)) throw new Error("台数要大于 0");
    var ex = makeExpander(idx, opts.boundary, opts.force, opts.maxDepth || MAX_DEPTH, false, !!opts.flow);

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

    /* 目标建筑自己吃的液体也要先算进去，液体自产才知道要不要接钻井 */
    var extraLiq = {};
    (b.inputLiquids || []).forEach(function (l) {
      extraLiq[l.name] = (extraLiq[l.name] || 0) + l.perSecond * count;
    });
    var liquidFrom = opts.liquids ? ex.resolveLiquids(opts, extraLiq) : {};

    var res = ex.result({
      block: blockName, count: count, products: products, inputs: inputs, tree: root, liquidFrom: liquidFrom,
      plan: (b.kind === "unit" && b.factoryKind !== "reconstructor")
        ? Math.min(Math.max(0, opts.plan || 0), Math.max(0, (b.plans || []).length - 1)) : 0,
      planTotal: b.kind === "unit" && b.factoryKind !== "reconstructor" ? (b.plans || []).length : 0
    });
    res.oilFloor = idx.oilFloor;
    res.attrs = idx.attrs || null;
    res.flow = !!opts.flow;
    // 目标建筑自身也进建造清单（电力/液体要一起算进去：ex.result 里还没有它）
    res.machines[blockName] = (res.machines[blockName] || 0) + count;
    res.machines = sortMachines(res.machines);
    /* 注意：目标建筑的液体已经通过 machines 进 liquidDemand，别再塞 liquidExtra，否则会重复计一遍
     * （expandBuilding(coal-centrifuge,2) 曾经因此把 15/s 的油显示成 9/s）。 */
    recalcPower(idx, res);
    attachLoops(idx, res);
    if (b.factoryKind === "assembler") {
      res.warnings.push("组装厂消耗的是方块（Payload），这里按外部输入处理，不展开成工厂");
    }
    if (opts.sources) applySources(data, res, opts.sources);
    return res;
  }

  /* ---------------------------------------------------------------- *
   * 混合厂：多个目标方块（物品工厂 / 发电设备）合成一份计划
   *   1) 先算每个目标"满效"的表面量（产什么、吃什么、要什么液体）；
   *   2) 所有目标的物品输入汇总成速率，再统一反推上游 —— 同一中间产物只建一份，
   *      取整只在汇总后做一次（分别建时每张图各取整一次，会多买机器）；
   *   3) 目标之间自产自销（A 产的石墨喂给 B）先抵扣，不重复建；
   *   4) 同图里的发电设备按净发电抵扣，给出 netPower；
   *   5) 附带 compare：同一组目标"分别建"要多少机器/电/占地，省了多少。
   * 兵厂不在这里算（它自带 T1→T5 大循环），选兵厂请用大循环页。
   * ---------------------------------------------------------------- */

  /* 一个目标方块满效时的表面量（不含上游展开） */
  function surfaceOf(idx, blockName, count, planIdx) {
    count = Math.max(1, Math.floor(count || 1));
    var b = idx.blocks.get(blockName);
    if (!b) {
      var g = idx.generators && idx.generators.get(blockName);
      if (!g) throw new Error("未知方块：" + blockName);
      var fuel = (g.fuels || [])[0];
      var grossEach = fuel ? fuel[2] : g.perSecond;
      var netEach = grossEach - (g.powerUsage || 0);
      return {
        block: blockName, kind: "generator", count: count, power: 0,
        powerOut: round(netEach * count), selfUse: round((g.powerUsage || 0) * count),
        products: [{ name: "电力", type: "power", rate: round(netEach * count) }],
        inputs: fuel ? [{ name: fuel[0], amount: round(fuel[1] * count) }] : [],
        inputLiquids: (g.liquids || []).map(function (l) {
          return { name: l[0], perSecond: round(l[1] * count) };
        })
      };
    }
    if (b.kind === "unit") {
      /* 用户 2026-11-10：兵厂大循环限制太多，就当正常工厂看待 ——
       * 台数 × 生产计划（或升级周期）算出单位产出与吃料，材料照常进混合厂的共享递归。 */
      var uProducts = [];
      var uInputs = [];
      var uPlan = 0;
      if (b.factoryKind === "reconstructor") {
        var uPer = b.cps;
        uProducts.push({ name: (b.upgrades[0] ? b.upgrades[0].to : "unit"), type: "unit",
                         rate: round(uPer * count) });
        b.inputs.forEach(function (i) {
          uInputs.push({ name: i.name, amount: round(i.amount * uPer * count) });
        });
      } else {
        var uPlans = b.plans || [];
        if (!uPlans.length) throw new Error(blockName + " 没有生产计划");
        uPlan = Math.min(Math.max(0, planIdx || 0), uPlans.length - 1);
        var uPlanObj = uPlans[uPlan];
        uProducts.push({ name: uPlanObj.unit, type: "unit", rate: round(uPlanObj.perSecond * count) });
        uPlanObj.items.forEach(function (i) {
          uInputs.push({ name: i.name, amount: round(i.amount * uPlanObj.perSecond * count) });
        });
      }
      return {
        block: blockName, kind: "unit", count: count, power: round((b.power || 0) * count), powerOut: 0,
        plan: uPlan, planTotal: (b.plans || []).length,
        products: uProducts, inputs: uInputs,
        inputLiquids: (b.inputLiquids || []).map(function (l) {
          return { name: l.name, perSecond: round(l.perSecond * count) };
        })
      };
    }
    var products = [];
    var inputs = [];
    b.outputs.forEach(function (o) {
      products.push({ name: o.name, type: "item", rate: round(o.amount * b.cps * count) });
    });
    b.inputs.forEach(function (i) {
      inputs.push({ name: i.name, amount: round(i.amount * b.cps * count) });
    });
    return {
      block: blockName, kind: "item", count: count, power: round(b.power * count), powerOut: 0,
      products: products, inputs: inputs,
      inputLiquids: b.inputLiquids.map(function (l) {
        return { name: l.name, perSecond: round(l.perSecond * count) };
      })
    };
  }

  /* targets = [{block:"silicon-smelter", count:2}, {block:"graphite-press", count:3}] */
  function expandMixed(data, targets, opts) {
    var idx = applyAttrs(indexOf(data), attrsOf(opts && (opts.attrs || (opts.floor > 0 ? opts.floor : null))));
    opts = opts || {};
    var list = (targets || []).map(function (t) {
      if (!t || !t.block) throw new Error("混合厂的每个目标都要写方块名");
      return surfaceOf(idx, t.block, t.count, t.plan);
    });
    if (!list.length) throw new Error("混合厂至少要一个目标");
    var bset = new Set(opts.boundary || []);
    var fmap = opts.force || {};
    var allowMulti = !!opts.multi;
    var flowMode = !!opts.flow;
    var maxDepth_ = opts.maxDepth || MAX_DEPTH;
    var warnings = [];
    var planByBlock = {};   /* 兵厂目标各自选的生产计划，机器表要按它写产出 */

    /* "这个物品能不能一路接到边界/自产到底"——与单目标展开同一套判定 */
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

    var roots = [];
    list.forEach(function (s) {
      s.inputs.forEach(function (i) { roots.push({ item: i.name, amount: i.amount, depth: 1 }); });
    });

    /* 一遍"按速率展开"：rate[item] 是汇总后的每秒需求，配方按累计量选 */
    var rate = {}, graph = {}, picks = {}, boundaryRate = {}, noRecipe = {}, overflow = {};

    function runPass() {
      rate = {}; graph = {}; boundaryRate = {}; noRecipe = {}; overflow = {};
      var queue = roots.slice();
      var guard = 0;
      while (queue.length && guard++ < 500000) {
        var cur = queue.shift();
        var item = cur.item, amount = cur.amount;
        if (!(amount > 1e-9)) continue;
        if (bset.has(item)) { boundaryRate[item] = (boundaryRate[item] || 0) + amount; continue; }
        if (!(allowMulti ? idx.producersOf(item) : idx.autoProducersOf(item)).length) {
          noRecipe[item] = true; boundaryRate[item] = (boundaryRate[item] || 0) + amount; continue;
        }
        if (cur.depth > maxDepth_) {
          overflow[item] = true; boundaryRate[item] = (boundaryRate[item] || 0) + amount; continue;
        }
        rate[item] = (rate[item] || 0) + amount;
        if (!picks[item]) picks[item] = chooseProducer(idx, item, rate[item], fmap, servable, function (liq) {
          return bset.has(liq) || !!liquidSourcePlan(idx, liq, 1, "auto");
        }, allowMulti).block.name;
        var blk = anyBlock(idx, picks[item]);
        var per = idx.perSecond(blk, item);
        graph[item] = { block: picks[item], per: per, inputs: idx.inputPerSecond(blk) };
        graph[item].inputs.forEach(function (i) {
          queue.push({ item: i.name, amount: amount / per * i.amount, depth: cur.depth + 1 });
        });
      }
    }

    /* 用汇总后的速率复核配方；配方变了就整轮重来（最多 6 轮，实际 1~2 轮就稳） */
    var iter = 0;
    for (; iter < 6; iter++) {
      runPass();
      var changed = false;
      Object.keys(rate).forEach(function (item) {
        var best = chooseProducer(idx, item, rate[item], fmap, servable, function (liq) {
          return bset.has(liq) || !!liquidSourcePlan(idx, liq, 1, "auto");
        }, allowMulti).block.name;
        if (best !== picks[item]) { picks[item] = best; changed = true; }
      });
      if (!changed) break;
    }
    if (iter >= 6) warnings.push("混合厂配方 6 轮内没有收敛，按最后一轮结果算");

    Object.keys(overflow).forEach(function (it) {
      warnings.push(it + " 递归超过 " + maxDepth_ + " 层，按外部输入处理");
    });
    Object.keys(noRecipe).forEach(function (it) {
      warnings.push(it + " 没有配方产出，按外部输入处理");
    });

    /* 目标之间自产自销：一个目标的产出先抵扣别的目标的需求 */
    var producedByTargets = {};
    var generatorNet = {};
    list.forEach(function (s) {
      s.products.forEach(function (p) {
        if (p.type !== "item") return;
        producedByTargets[p.name] = (producedByTargets[p.name] || 0) + p.rate;
      });
      if (s.kind === "generator") generatorNet[s.block] = (generatorNet[s.block] || 0) + s.powerOut;
    });

    var internals = [];   // 目标之间共享的中间产物（A 产 B 用）
    var netRate = {};
    Object.keys(rate).forEach(function (item) {
      var need = rate[item];
      var have = producedByTargets[item] || 0;
      var used = Math.min(need, have);
      if (used > 1e-9) internals.push({ item: item, need: round(need), fromTargets: round(used), stillNeed: round(Math.max(0, need - have)) });
      netRate[item] = Math.max(0, need - have);
    });

    /* 汇总后一次性取整：每种物品的机器只买一次 */
    var machines = {};
    var order = [];
    var allocByItem = {};
    var sharedItems = [];
    Object.keys(netRate).sort().forEach(function (item) {
      var g = graph[item];
      if (!g) return;
      if (!(netRate[item] > 1e-9)) { allocByItem[item] = 0; return; }
      var n = flowMode ? netRate[item] / g.per
                       : Math.max(1, Math.ceil(netRate[item] / g.per - 1e-9));
      allocByItem[item] = n;
      machines[g.block] = (machines[g.block] || 0) + n;
      order.push({ block: g.block, count: n, item: item, rate: round(netRate[item]), per: round(g.per) });
      sharedItems.push({ item: item, block: g.block, perMachine: round(g.per),
                         need: round(rate[item]), fromTargets: round(producedByTargets[item] || 0),
                         netNeed: round(netRate[item]), count: n });
    });
    /* 一个方块产多种被需要的物品时，机器数会重复记，给个提示（当前原版物品工厂基本都是单一产物） */
    var blockUse = {};
    order.forEach(function (o) { blockUse[o.block] = (blockUse[o.block] || 0) + 1; });
    /* 多产物方块（分离机/解离机）一台就同时出所有产物：台数取各需求项里的最大值，别累加 */
    Object.keys(blockUse).forEach(function (blkName) {
      var mb = anyBlock(idx, blkName);
      if (!mb || !mb.isMulti) return;
      var mx = 0, which = null;
      order.forEach(function (o) { if (o.block === blkName && o.count > mx) { mx = o.count; which = o.item; } });
      if (mx) {
        machines[blkName] = mx;
        warnings.push(blkName + " 是多产物方块，台数按最大的那项（" + which + "）算 " + mx + " 台，其余产物顺带出");
      }
    });

    var products = [], inputs = [], liquidExtra = {}, powerOut = 0, targetRows = [];
    list.forEach(function (s) {
      if (s.kind === "unit") planByBlock[s.block] = s.plan || 0;
      machines[s.block] = (machines[s.block] || 0) + s.count;
      s.products.forEach(function (p) {
        products.push({ name: p.name, type: p.type, rate: p.rate, block: s.block });
      });
      s.inputs.forEach(function (i) {
        inputs.push({ name: i.name, amount: i.amount, block: s.block });
      });
      /* 注意：目标方块的输入液体已经通过上面那行 machines[s.block] 进 liquidDemand，
       * 再塞 liquidExtra 就会重复计一遍（mixed 模式 coal-centrifuge 3 台的油曾算成 36/s）。 */
      powerOut += s.powerOut || 0;
      targetRows.push({ block: s.block, count: s.count, kind: s.kind, products: s.products,
                        inputs: s.inputs, inputLiquids: s.inputLiquids || [],
                        plan: s.plan || 0, planTotal: s.planTotal || 0,
                        power: s.power, powerOut: s.powerOut || 0 });
    });

    /* 分别建：每个目标各展开一遍，用来对比混合省了多少 */
    var sep = { machines: {}, power: 0, tiles: 0 };
    var sepByItem = {};
    list.forEach(function (s) {
      if (s.kind === "generator") {
        sep.machines[s.block] = (sep.machines[s.block] || 0) + s.count;
        sep.power += 0;
        var gb = anyBlock(idx, s.block);
        sep.tiles += (gb && gb.size ? gb.size * gb.size : 1) * s.count;
        return;
      }
      var one = expandBuilding(data, s.block, s.count, {
        boundary: opts.boundary, force: opts.force, maxDepth: maxDepth_,
        plan: s.plan || 0,
        liquids: opts.liquids, liquid: opts.liquid, liquidName: opts.liquidName
      });
      Object.keys(one.machines).forEach(function (k) {
        sep.machines[k] = (sep.machines[k] || 0) + one.machines[k];
      });
      sep.power += one.power || 0;
      (one.order || []).forEach(function (o) {
        sepByItem[o.item] = (sepByItem[o.item] || 0) + o.count;
      });
      Object.keys(one.machines).forEach(function (k) {
        var b = anyBlock(idx, k);
        sep.tiles += (b && b.size ? b.size * b.size : 1) * one.machines[k];
      });
    });

    var res = {
      mode: "mixed",
      targets: targetRows,
      products: products,
      inputs: inputs,
      machines: machines,
      order: order,
      demand: {},
      power: 0,
      powerOut: round(powerOut),
      liquids: [],
      liquidExtra: liquidExtra,
      generatorNet: generatorNet,
      shared: sharedItems,
      planByBlock: planByBlock,
      internals: internals,
      warnings: warnings,
      tree: null,
      oilFloor: idx.oilFloor,
      attrs: idx.attrs || null,
      snapshot: idx.snapshot || ""
    };
    Object.keys(boundaryRate).sort().forEach(function (k) {
      res.demand[k] = round(boundaryRate[k]);
    });
    /* 液体自产（混合厂）：机器清单里没人供的液体接钻井/转化方块。
     * 转化方块（spore-press）自己的物品入料在混合厂里不继续展开，直接记为外部输入并给提示；
     * 要完整展开（spore-pod ← cultivator）请用单目标页 / --item。 */
    if (opts.liquids) {
      var howMap = opts.liquid || {};
      var nameMap = opts.liquidName || {};
      var usedLiq = {};
      for (var lp = 0; lp < 4; lp++) {
        var supply = {};
        Object.keys(res.machines).forEach(function (name) {
          var mb = anyBlock(idx, name);
          if (!mb) return;
          (mb.outputLiquids || []).forEach(function (l) {
            supply[l.name] = (supply[l.name] || 0) + res.machines[name] * l.perSecond;
          });
        });
        var changed = false;
        liquidDemand(idx, res.machines, {}).forEach(function (l) {
          var net = l.perSecond - (supply[l.name] || 0);
          if (!(net > 1e-9)) return;
          if ((opts.boundary || []).indexOf(l.name) >= 0) return;
          var how = howMap[l.name] || "auto";
          if (how === "import" || how === "off") return;
          var plan = liquidSourcePlan(idx, l.name, net, how, nameMap[l.name], flowMode);
          if (!plan) return;
          var cur = res.machines[plan.block] || 0;
          var add = plan.count - cur;
          if (add <= 0) return;
          res.machines[plan.block] = cur + add;
          order.push({ block: plan.block, count: add, item: null, liquid: l.name });
          changed = true;
          if (!usedLiq[l.name]) {
            usedLiq[l.name] = { liquid: l.name, type: plan.type, block: plan.block, count: 0, perSecondEach: plan.perSecond };
          }
          usedLiq[l.name].count += add;
          plan.inputs.forEach(function (i) {
            var amt = add * i.amount;
            if ((opts.boundary || []).indexOf(i.name) < 0) {
              warnings.push("混合厂液体自产： " + plan.block + " 吃 " + i.name + " " + round(amt) + "/s，按外部输入计");
            }
            res.demand[i.name] = round((res.demand[i.name] || 0) + amt);
          });
        });
        if (!changed) break;
      }
      res.liquidFrom = usedLiq;
    }

    res.machines = sortMachines(res.machines);
    recalcPower(idx, res);
    res.netPower = round(res.power - powerOut);

    /* 对比表 */
    var mixedTiles = 0;
    Object.keys(res.machines).forEach(function (k) {
      var b = anyBlock(idx, k);
      mixedTiles += (b && b.size ? b.size * b.size : 1) * res.machines[k];
    });
    var sepTiles = sep.tiles;
    var sumCount = function (m) { return Object.keys(m).reduce(function (a, k) { return a + m[k]; }, 0); };
    var shared = sharedItems.map(function (s) {
      var pool = sepByItem[s.item] || 0;
      return {
        item: s.item, block: s.block, perMachine: s.perMachine,
        need: s.need, fromTargets: s.fromTargets, netNeed: s.netNeed,
        mixedCount: s.count, separateCount: pool, saved: Math.max(0, pool - s.count),
        tileEach: (function () { var b = anyBlock(idx, s.block); return b && b.size ? b.size * b.size : 1; })()
      };
    });
    res.shared = shared;
    res.compare = {
      machinesMixed: sumCount(res.machines),
      machinesSeparate: sumCount(sep.machines),
      savedMachines: sumCount(sep.machines) - sumCount(res.machines),
      powerMixed: round(res.power),
      powerSeparate: round(sep.power),
      savedPower: round(sep.power - res.power),
      tilesMixed: mixedTiles,
      tilesSeparate: sepTiles,
      savedTiles: sepTiles - mixedTiles,
      detail: sep.machines
    };
    if (shared.some(function (s) { return s.separateCount > 0 && s.saved > 0; })) {
      // 有共享产物被省下来，前端/命令行会把 compare 打出来
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
    /* 多产物方块（分离机/解离机）在 gamedata 里同时有 blocks 条目（产出为空）和 multi 条目，
     * 这里优先返回 multi 视图，否则机器表会写成"没有产出"，电力/份额也拿不到。 */
    var mv = idx.multi.get(name);
    if (mv) {
      return { name: name, kind: "multi", isMulti: true, size: mv.size, power: mv.power, icon: mv.icon,
               craftTime: mv.craftTime, cps: mv.cps,
               inputs: mv.inputs.map(function (i) { return { name: i[0], amount: i[1] / (mv.cps || 1) }; }),
               inputLiquids: mv.inputLiquids.map(function (l) { return { name: l[0], perSecond: l[1] }; }),
               outputLiquids: [],
               outputs: mv.outputs.map(function (o) { return { name: o[0], amount: o[1] / (mv.cps || 1), share: o[2] }; }),
               plans: [], upgrades: [], factoryKind: "" };
    }
    var b = idx.blocks.get(name);
    if (b) return b;
    var d = idx.drills.get(name);
    if (d) {
      return { name: name, kind: "drill", size: d.size, power: d.power, icon: d.icon,
               craftTime: d.drillTime, cps: 0, inputs: [], outputs: [],
               plans: [], upgrades: [], factoryKind: "", tier: d.tier };
    }
    var g = idx.generators.get(name);
    if (g) {
      return { name: name, kind: "generator", size: g.size, power: 0, icon: g.icon,
               craftTime: 0, cps: 0, inputs: [], outputs: [], plans: [], upgrades: [],
               factoryKind: "", perSecond: g.perSecond, powerUsage: g.powerUsage,
               fuels: g.fuels || [], liquids: g.liquids || [],
               /* 发电厂当目标建筑时也得让它吃的液体进 liquidDemand（水/氰气），否则树里有、总量表里没有 */
               inputLiquids: (g.liquids || []).map(function (l) { return { name: l[0], perSecond: l[1] }; }) };
    }
    var p = idx.pumps.get(name);
    if (p) {
      return { name: name, kind: "pump", size: p.size, power: p.power, icon: p.icon,
               craftTime: 0, cps: 0,
               inputs: p.inputs.map(function (i) { return { name: i[0], amount: i[1] }; }),
               outputs: [],
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
  function pumpPlan(data, liquidName, amount, pumpName, floor) {
    var idx = applyAttrs(indexOf(data), attrsOf(floor));
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

  /* 液体需求换算成抽水机台数：小泵(机械泵)→中泵(回转泵)→大泵(脉冲泵)…
   * 用户口径里水常按"几台泵"计，所以每种液体都给出各档泵要几台（向上取整）。 */
  function pumpEquivalents(data, liquidName, amount, floor) {
    var idx = applyAttrs(indexOf(data), attrsOf(floor));
    var out = [];
    idx.pumps.forEach(function (p) {
      if (p.liquid !== liquidName || !(p.perSecond > 0)) return;
      out.push({
        pump: p.name, size: p.size, perSecondEach: p.perSecond, powerEach: p.power,
        count: Math.max(0, Math.ceil((amount || 0) / p.perSecond - 1e-9))
      });
    });
    /* 小 → 大：先按每秒排，再按尺寸 */
    out.sort(function (a, b) { return (a.perSecondEach - b.perSecondEach) || (a.size - b.size); });
    return out;
  }

  /* 泵组合：把液体需求摊成"小泵 N 台 + 中泵 M 台 + 大泵 K 台"的加和（用户口径）。
   * 只用主线的三档（机械泵 7/s、回转泵 48/s、脉冲泵 118.8/s）。
   * 目标顺序（用户 2026-11-09 指定）：先让**富余尽量小**，富余相同再比台数。
   * 例：18/s 水 → 小泵 3 台（合计 21/s，富余 3/s），而不是中泵 1 台（48/s，富余 30/s）。 */
  var PUMP_TIERS = ["mechanical-pump", "rotary-pump", "impulse-pump"];
  function pumpMix(data, liquidName, amount, floor) {
    return pumpMixIdx(applyAttrs(indexOf(data), attrsOf(floor)), liquidName, amount);
  }
  /* flow（归一化）用的泵组合：和 pumpMixIdx 同一个"大 → 小"思路，但台数是小数，
   * 大泵按整台铺、剩下的零头给最小一档 —— 总量正好等于需求，既不留富余也不取整。 */
  function pumpMixFlow(idx, liquidName, amount) {
    var tiers = [];
    PUMP_TIERS.forEach(function (n) {
      var p = idx.pumps.get(n);
      if (p && p.liquid === liquidName && p.perSecond > 0) {
        tiers.push({ pump: n, perSecondEach: p.perSecond });
      }
    });
    if (!tiers.length) return null;
    tiers.sort(function (a, b) { return b.perSecondEach - a.perSecondEach; });
    var rem = amount, list = [];
    tiers.forEach(function (t, i) {
      if (i === tiers.length - 1) return;              // 最小一档留给零头
      if (t.perSecondEach > rem + 1e-9) return;
      var c = Math.floor(rem / t.perSecondEach + 1e-9);
      if (c > 0) {
        list.push({ pump: t.pump, count: c, perSecondEach: t.perSecondEach });
        rem -= c * t.perSecondEach;
      }
    });
    var small = tiers[tiers.length - 1];
    if (rem > 1e-9) list.push({ pump: small.pump, count: rem / small.perSecondEach, perSecondEach: small.perSecondEach });
    if (!list.length) return null;
    var total = list.reduce(function (a, b) { return a + b.count; }, 0);
    return { need: amount, pumps: list, total: total };
  }

  function pumpMixIdx(idx, liquidName, amount) {
    var tiers = [];
    PUMP_TIERS.forEach(function (n) {
      var p = idx.pumps.get(n);
      if (p && p.liquid === liquidName && p.perSecond > 0) {
        tiers.push({ pump: n, perSecondEach: p.perSecond, powerEach: p.power, size: p.size });
      }
    });
    if (tiers.length < 2) return null;
    /* 大 → 小 排：先尽量用大泵，再补中泵、小泵 */
    tiers.sort(function (a, b) { return b.perSecondEach - a.perSecondEach; });
    var big = tiers[0], mid = tiers[1], small = tiers[2] || tiers[1];
    var perBig = big.perSecondEach, perMid = mid.perSecondEach, perSmall = small.perSecondEach;
    var best = null;
    var maxBig = Math.ceil(amount / perBig - 1e-9);
    for (var nb = 0; nb <= maxBig; nb++) {
      var rem1 = amount - nb * perBig;
      if (rem1 <= 1e-9) {
        var cand0 = [{ pump: big.pump, count: nb, perSecondEach: perBig }];
        best = better(best, cand0, nb * perBig);
        continue;
      }
      var maxMid = Math.ceil(rem1 / perMid - 1e-9);
      for (var nm = 0; nm <= maxMid; nm++) {
        var rem2 = rem1 - nm * perMid;
        var ns = rem2 > 1e-9 ? Math.ceil(rem2 / perSmall - 1e-9) : 0;
        var list = [];
        if (nb) list.push({ pump: big.pump, count: nb, perSecondEach: perBig });
        if (nm) list.push({ pump: mid.pump, count: nm, perSecondEach: perMid });
        if (ns) list.push({ pump: small.pump, count: ns, perSecondEach: perSmall });
        var total = nb * perBig + nm * perMid + ns * perSmall;
        best = better(best, list, total);
      }
    }
    if (!best) return null;
    return { need: amount, pumps: best.list, total: round(best.total),
             extra: round(best.total - amount), count: best.count };

    /* 富余优先（量化到 0.01 免得浮点噪声），富余相同再比台数少 */
    function better(cur, list, total) {
      var count = list.reduce(function (a, b) { return a + b.count; }, 0);
      if (!cur) return { list: list, total: total, count: count };
      var e1 = Math.round((total - amount) * 100) / 100;
      var e2 = Math.round((cur.total - amount) * 100) / 100;
      if (e1 !== e2) return e1 < e2 ? { list: list, total: total, count: count } : cur;
      if (count !== cur.count) return count < cur.count ? { list: list, total: total, count: count } : cur;
      return (total - amount) < (cur.total - amount) ? { list: list, total: total, count: count } : cur;
    }
  }

  /* 电力组合：外部电力（自己没发电、要从外面接进来）按"几台发电厂"计量，
   * 逻辑与泵一致：燃烧发电机 60/s（小）、蒸汽发电机 330/s（中）、差速发电机 1080/s（大），
   * 先让富余小，再让台数少。 */
  var POWER_TIERS = ["combustion-generator", "steam-generator", "differential-generator"];
  function powerMix(data, amount) {
    return powerMixIdx(indexOf(data), amount);
  }
  function powerMixIdx(idx, amount) {
    var tiers = [];
    POWER_TIERS.forEach(function (n) {
      var g = idx.generators.get(n);
      if (g && g.perSecond > 0) {
        tiers.push({ block: n, perSecondEach: g.perSecond, size: g.size,
                     fuel: (g.fuels && g.fuels[0]) ? g.fuels[0][0] : null });
      }
    });
    if (tiers.length < 2 || !(amount > 0)) return null;
    tiers.sort(function (a, b) { return b.perSecondEach - a.perSecondEach; });
    var big = tiers[0], mid = tiers[1], small = tiers[2] || tiers[1];
    var perBig = big.perSecondEach, perMid = mid.perSecondEach, perSmall = small.perSecondEach;
    var best = null;
    var maxBig = Math.ceil(amount / perBig - 1e-9);
    for (var nb = 0; nb <= maxBig; nb++) {
      var rem1 = amount - nb * perBig;
      var addBig = function (list, total) {
        best = better(best, list, total);
      };
      if (rem1 <= 1e-9) { addBig([{ block: big.block, count: nb || 1, perSecondEach: perBig }], (nb || 1) * perBig); continue; }
      var maxMid = Math.ceil(rem1 / perMid - 1e-9);
      for (var nm = 0; nm <= maxMid; nm++) {
        var rem2 = rem1 - nm * perMid;
        var ns = rem2 > 1e-9 ? Math.ceil(rem2 / perSmall - 1e-9) : 0;
        var list = [];
        if (nb) list.push({ block: big.block, count: nb, perSecondEach: perBig });
        if (nm) list.push({ block: mid.block, count: nm, perSecondEach: perMid });
        if (ns) list.push({ block: small.block, count: ns, perSecondEach: perSmall });
        if (!list.length) continue;
        addBig(list, nb * perBig + nm * perMid + ns * perSmall);
      }
    }
    if (!best) return null;
    return { need: amount, gens: best.list, total: round(best.total),
             extra: round(best.total - amount), count: best.count };

    function better(cur, list, total) {
      var count = list.reduce(function (a, b) { return a + b.count; }, 0);
      if (!cur) return { list: list, total: total, count: count };
      var e1 = Math.round((total - amount) * 100) / 100;
      var e2 = Math.round((cur.total - amount) * 100) / 100;
      if (e1 !== e2) return e1 < e2 ? { list: list, total: total, count: count } : cur;
      if (count !== cur.count) return count < cur.count ? { list: list, total: total, count: count } : cur;
      return (total - amount) < (cur.total - amount) ? { list: list, total: total, count: count } : cur;
    }
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

  /* 机器清单带来的液体产出（转化方块 outputLiquids + 钻井 liquid 字段），用于算净需求 */
  function liquidSupply(idx, machines) {
    var acc = {};
    Object.keys(machines || {}).forEach(function (name) {
      var b = anyBlock(idx, name);
      if (!b) return;
      (b.outputLiquids || []).forEach(function (l) {
        if (l.perSecond === undefined) return;
        acc[l.name] = (acc[l.name] || 0) + machines[name] * l.perSecond;
      });
      if (b.liquid && b.perSecond > 0) acc[b.liquid] = (acc[b.liquid] || 0) + machines[name] * b.perSecond;
    });
    return acc;
  }

  /* 净需求：需求 − 自产，只要还要从外面进的（负数和 0 过滤掉） */
  function liquidNetDemand(idx, machines, extra) {
    var sup = liquidSupply(idx, machines);
    return liquidDemand(idx, machines, extra)
      .map(function (l) { return { name: l.name, perSecond: round(l.perSecond - (sup[l.name] || 0)) }; })
      .filter(function (l) { return l.perSecond > 1e-9; });
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
    /* 净液体需求（自产抵掉之后还要从外面进的）：液体自产时卡片/命令行优先显示这个 */
    res.liquidNet = liquidNetDemand(idx, res.machines, res.liquidExtra);
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
      } else if (type === "import") {
        /* 外部运入细分成 灰带/蓝带/绿带/布桥/质驱/接收台/其它：
         * perSecond>0 的按吞吐算要几条，perSecond=0 视为不限速（接收台/其它）。
         * 不指定 via 时用默认蓝带。 */
        var ch = idx.channelsByKey.get(c.via || DEFAULT_CHANNEL);
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
    /* 环境属性会改抽液方块的每秒产量，所以这里也要按 result 的属性重算索引 */
    var idx = applyAttrs(indexOf(data), attrsOf(result && (result.attrs || (result.oilFloor > 0 ? result.oilFloor : null))));
    /* flow（归一化）模式：台数是"满效等价值"，可能是 1.5 台这种小数。
     * countCeil = 真要建整台时的台数，eff = 只建整台时每台实际跑的效率（1.5/2 = 75%）。 */
    var isFlow = !!(result && result.flow);
    return Object.keys(result.machines).map(function (name) {
      var b = anyBlock(idx, name);
      var count = result.machines[name];
      var countCeil = isFlow ? Math.ceil(count - 1e-9) : count;
      var eff = (isFlow && countCeil > 0) ? count / countCeil : 1;
      var outputs = [];
      var drillOuts = [];
      if (b && b.kind === "drill") {
        /* 钻头就是工厂配比里的一员：写清采集什么、每台多少、合计多少（数据来自 applySources 的来源行） */
        (result.sources || []).forEach(function (x) {
          if (x.drill !== name) return;
          drillOuts.push({ name: x.item, type: "item",
                           perSecond: (x.perSecondEach || 0) * (x.count || 0),
                           perSecondEach: x.perSecondEach || 0 });
        });
        outputs = drillOuts.length
          ? drillOuts.map(function (o) { return "采集 " + o.name + " " + round(o.perSecond) + "/s"; })
          : ["采集（未指定来源）"];
      } else if (b && b.kind === "generator") {
        var sup = result.supply || {};
        /* 混合厂里一台发电设备的净发电记在 result.generatorNet 上；单目标展开用 result.supply */
        var genNet = (result.generatorNet && result.generatorNet[name] != null)
          ? result.generatorNet[name] - b.power * 0
          : (sup.net || 0);
        outputs = ["发电 " + round(genNet) + "/s" +
                   (sup.fuel ? "，烧 " + sup.fuel.name + " " + round(sup.fuel.perSecond) + "/s" : "")];
      } else if (b && b.kind === "pump") {
        outputs = ["抽 " + b.liquid + " " + round(b.perSecond * count) + "/s"];
      } else if (b && b.kind === "unit") {
        if (b.factoryKind === "reconstructor") {
          outputs = (b.upgrades || []).length
            ? ["升级 " + b.upgrades.length + " 种（" + round(b.cps * count) + " 次/s）"]
            : ["升级厂"];
        } else {
          var planIdx_ = (result.planByBlock && result.planByBlock[name] != null)
            ? result.planByBlock[name] : (result.plan || 0);
          var plan = (b.plans || [])[planIdx_] || (b.plans || [])[0];
          if (plan) outputs = [plan.unit + " " + round(plan.perSecond * count) + "/s"];
        }
      } else if (b) {
        outputs = b.outputs.map(function (o) {
          return o.name + " " + round(o.amount * b.cps * count) + "/s";
        });
      }
      return {
        name: name,
        count: isFlow ? Math.round(count * 100) / 100 : count,
        countRaw: count,
        countCeil: countCeil,
        eff: isFlow && countCeil > 0 ? Math.round(count / countCeil * 1000) / 1000 : 1,
        flow: isFlow,
        kind: b ? b.kind : "item",
        icon: b ? (b.icon || "") : "",
        size: b ? b.size : 0,
        powerEach: b ? b.power : 0,
        powerTotal: b ? b.power * count : 0,
        /* 吃料：钻井吃 sand/water、离心机吃 oil 这些输入以前只进递归、不显示，用户会以为没算。
         * 泵的 inputs 已是"每秒/台"；工厂与多产物方块的 inputs 是"每 craft"，要乘 cps；液体一律每秒。 */
        inItems: b ? (function () {
          var rate = b.kind === "pump" ? 1 : (b.cps || 1);
          var list = [];
          (b.inputs || []).forEach(function (i) {
            var amt = (i.amount != null ? i.amount : (i.perSecond || 0)) * rate * count;
            if (amt > 1e-9) list.push({ name: i.name, type: "item", perSecond: round(amt) });
          });
          (b.inputLiquids || []).forEach(function (l) {
            if ((l.perSecond || 0) > 1e-9) {
              list.push({ name: l.name, type: "liquid", perSecond: round(l.perSecond * count) });
            }
          });
          return list;
        })() : [],
        outItems: b ? (b.kind === "generator"
          ? [{ name: "电力", type: "power", perSecond: round(genNet || 0) }]
          : (b.kind === "drill" ? drillOuts : b.outputs.map(function (o) {
              return { name: o.name, type: "item", perSecond: o.amount * b.cps * count };
            }))) : [],
        rateEach: b ? (b.kind === "drill"
          ? (drillOuts.length ? drillOuts[0].perSecondEach : 0)
          : b.kind === "pump"
          ? (b.perSecond || 0)
          : b.kind === "unit"
          ? ((b.plans && b.plans[0]) ? b.plans[0].perSecond : b.cps)
          : (b.outputs.length ? b.outputs[0].amount * b.cps : 0)) : 0,
        outputs: outputs
      };
    });
  }

  function round(x) { return Math.round(x * 1000) / 1000; }

  var api = { DEFAULT_CHANNEL: DEFAULT_CHANNEL,
              DEFAULT_GENERATOR: DEFAULT_GENERATOR, DEFAULT_FUEL: DEFAULT_FUEL,
              expandGenerator: expandGenerator,
              buildIndex: buildIndex, indexOf: indexOf,
              expand: expand, expandBuilding: expandBuilding,
              expandMixed: expandMixed, surfaceOf: surfaceOf,
              machineRows: machineRows, anyBlock: anyBlock,
              drillRate: drillRate, drillsNeeded: drillsNeeded,
              generatorPlan: generatorPlan, generatorSupply: generatorSupply,
              separatorPlan: separatorPlan, unitChain: unitChain, chainFromTop: chainFromTop,
              chainFromBlock: chainFromBlock, chainsForBlock: chainsForBlock,
              pumpPlan: pumpPlan, pumpEquivalents: pumpEquivalents, pumpMix: pumpMix,
      applyFloor: applyFloor,
      applyAttrs: applyAttrs,
      detectCycles: detectCycles,
      cycleText: cycleText,
      attrsOf: attrsOf,
              powerMix: powerMix,
              applySources: applySources, recalcPower: recalcPower,
              liquidDemand: liquidDemand, DEFAULT_CHANNEL: DEFAULT_CHANNEL };
  global.RatioCore = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof window !== "undefined" ? window : globalThis);
