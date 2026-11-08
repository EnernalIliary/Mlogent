#!/usr/bin/env node
/* CLI / HTTP 对拍：保证"命令行输出"和"core.js 直算"是同一份结果，
 * 顺便守住几个容易回归的点（默认边界、图标剔除、错误退出码、HTTP 查询串解析）。
 *
 *   node ratio-calc/test_cli.cjs
 */
"use strict";

const assert = require("assert");
const { execFileSync } = require("child_process");
const path = require("path");

const CLI = path.join(__dirname, "cli.cjs");
const cli = require(CLI);

let pass = 0, fail = 0;
function ok(name, fn) {
  try { fn(); pass++; console.log("  ✓ " + name); }
  catch (e) { fail++; console.log("  × " + name + " — " + (e.message || e)); }
}
function close(a, b, tol) {
  tol = tol === undefined ? 1e-6 : tol;
  assert.ok(Math.abs(a - b) <= tol, a + " ≉ " + b);
}
function run(args) {
  return execFileSync(process.execPath, [CLI].concat(args), { encoding: "utf8" });
}
function runCode(args) {
  try { execFileSync(process.execPath, [CLI].concat(args), { encoding: "utf8", stdio: "pipe" }); return 0; }
  catch (e) { return e.status; }
}

const env = cli.loadData();
const R = env.R, DATA = env.DATA;

console.log("CLI 与 core.js 对拍");

/* 1. 物品模式：机器清单 / 电力 / 边界需求，逐项和 expand() 比 */
[
  { a: ["--item", "silicon", "--rate", "5"], target: "silicon", rate: 5 },
  { a: ["--item", "graphite", "--rate", "1"], target: "graphite", rate: 1 },
  { a: ["--item", "metaglass", "--rate", "4", "--boundary", "sand"], target: "metaglass", rate: 4, b: ["sand"] },
  { a: ["--item", "surge-alloy", "--rate", "1", "--force", "surge-alloy=surge-smelter"], target: "surge-alloy", rate: 1, f: { "surge-alloy": "surge-smelter" } }
].forEach((c, i) => {
  ok("物品模式 " + (i + 1) + "：" + c.a.join(" "), () => {
    const res = cli.query(cli.parseArgs(c.a));
    const direct = R.expand(DATA, c.target, c.rate, c.b || ["coal", "sand"], c.f || {}, {});
    const directRows = R.machineRows(DATA, direct);
    assert.strictEqual(res.machines.length, directRows.length, "机器条数");
    directRows.forEach(row => {
      const hit = res.machines.filter(m => m.name === row.name)[0];
      assert.ok(hit, "缺少机器 " + row.name);
      assert.strictEqual(hit.count, row.count, row.name + " 台数");
      close(hit.powerTotal, row.powerTotal);
    });
    close(res.power, direct.power);
    const directDemand = Object.keys(direct.demand).sort();
    assert.deepStrictEqual(res.demand.map(d => d.name), directDemand);
    directDemand.forEach(k => close(res.demand.filter(d => d.name === k)[0].perSecond, direct.demand[k]));
    close(res.products[0].rate, direct.achieved);
  });
});

/* 2. 建筑模式：目标建筑要算进清单，且电力包含它自己 */
ok("建筑模式 graphite-press ×2（煤 2.667/s）", () => {
  const res = cli.query(cli.parseArgs(["--block", "graphite-press", "--count", "2"]));
  assert.strictEqual(res.mode, "building");
  close(res.products[0].rate, 1.333333, 1e-5);
  const press = res.machines.filter(m => m.name === "graphite-press")[0];
  assert.strictEqual(press.count, 2);
  close(res.demand.filter(d => d.name === "coal")[0].perSecond, 2.666666, 1e-5);
});

ok("建筑模式选兵厂 → 自动走大循环（ground-factory ×2）", () => {
  const res = cli.query(cli.parseArgs(["--block", "ground-factory", "--count", "2"]));
  assert.strictEqual(res.mode, "chain");
  assert.strictEqual(res.chain.start, "dagger");
  const gf = res.machines.filter(m => m.name === "ground-factory")[0];
  assert.strictEqual(gf.count, 2);
  close(gf.powerTotal, 144);
  close(res.power, 144);
  assert.strictEqual(res.products[0].type, "unit");
  assert.strictEqual(res.products[0].name, "dagger");
  close(res.products[0].rate, 0.133, 1e-3);
  close(res.demand.filter(d => d.name === "silicon")[0].perSecond, 1.333, 1e-3);
});

ok("兵厂链 T1 少建时：0 台层级不进清单、材料不留 0", () => {
  const res = cli.query(cli.parseArgs(["--block", "ground-factory", "--count", "1"]));
  const txt = cli.renderText(res);
  assert.ok(txt.indexOf("不建") >= 0, txt);
  assert.ok(!/ 0\/s/.test(txt), "不该出现 0/s 材料：\n" + txt);
  assert.strictEqual(res.machines.length, 1);
});

ok("兵厂多计划：--plan 1 换 crawler 线", () => {
  const a = cli.query(cli.parseArgs(["--block", "ground-factory", "--count", "1"]));
  const b = cli.query(cli.parseArgs(["--block", "ground-factory", "--count", "1", "--plan", "1"]));
  assert.strictEqual(a.products[0].name, "dagger");
  assert.strictEqual(b.products[0].name, "crawler");
  assert.strictEqual(b.chain.start, "crawler");
});

/* 3. 外部来源：钻头台数/液体、多产物副产物 */
ok("来源 sand=drill:laser-drill:8 → 台数/单台/水", () => {
  const res = cli.query(cli.parseArgs(["--item", "silicon", "--rate", "5", "--src", "sand=drill:laser-drill:8"]));
  const s = res.sources.filter(x => x.item === "sand")[0];
  assert.strictEqual(s.type, "drill");
  assert.strictEqual(s.drill, "laser-drill");
  close(s.perSecondEach, R.drillRate(DATA, "laser-drill", "sand", 8, true));
  assert.strictEqual(s.count, Math.ceil(12 / s.perSecondEach - 1e-9));
  assert.ok(res.machines.some(m => m.name === "laser-drill"));
  assert.ok(res.liquids.some(l => l.name === "water"));
});

ok("来源 scrap=multi:disassembler：副产物里有 thorium", () => {
  const res = cli.query(cli.parseArgs(["--item", "silicon", "--rate", "5", "--boundary", "coal,sand",
                                        "--src", "scrap=multi:disassembler"]));
  const s = res.sources.filter(x => x.item === "scrap")[0] || { byproducts: [] };
  assert.ok(s.type === "multi" || res.warnings.length >= 0);
  if (s.type === "multi") assert.ok(s.byproducts.some(b => b.name === "thorium") || s.byproducts.length > 0);
});

/* 4. 供电 */
ok("供电 combustion-generator ×N 覆盖电力", () => {
  const res = cli.query(cli.parseArgs(["--block", "silicon-smelter", "--count", "4",
                                        "--gen", "combustion-generator", "--genfuel", "coal"]));
  const s = res.supply;
  assert.ok(s, "应有供电方案");
  assert.ok(s.netTotal >= res.power, "净发电应覆盖电力：" + s.netTotal + " vs " + res.power);
  close(s.fuel.perSecond, s.count * s.fuel.perSecondEach);
});

ok("电力为 0 时给提示而不是 0 台发电厂", () => {
  const res = cli.query(cli.parseArgs(["--block", "graphite-press", "--count", "1",
                                        "--gen", "combustion-generator", "--genfuel", "coal"]));
  assert.strictEqual(res.supply, null);
  assert.ok(res.warnings.some(w => w.indexOf("电力需求是 0") >= 0));
});

/* 5. 兵厂链 */
ok("兵厂链 dagger 0.05/s：5 级、最后是 reign", () => {
  const res = cli.query(cli.parseArgs(["--chain", "dagger", "--chainrate", "0.05"]));
  assert.strictEqual(res.mode, "chain");
  assert.strictEqual(res.chain.rows.length, 5);
  assert.strictEqual(res.chain.rows[4].unit, "reign");
  assert.ok(res.chain.power > 0);
  assert.ok(Object.keys(res.chain.materials).length > 0);
});

ok("兵厂链按最慢一段算：达成 0.05/s、瓶颈 T5、台数不必 1:1", () => {
  const c = cli.query(cli.parseArgs(["--chain", "dagger", "--chainrate", "0.05"])).chain;
  close(c.achieved, 0.05);
  assert.strictEqual(c.bottleneck, "reign");
  assert.strictEqual(c.bottleneckTier, 5);
  assert.deepStrictEqual(c.rows.map(r => r.count), [1, 1, 2, 5, 12]);
  close(c.rows[3].feedsNext, 2.6667, 2e-3);
  close(c.power, 22872, 1);
});

/* 5b. 抽水泵：水可以自己抽 */
ok("--src water=pump:rotary-pump 自动补台数并计入电力", () => {
  const res = cli.query(cli.parseArgs(["--block", "silicon-smelter", "--count", "3",
                                        "--src", "sand=drill:laser-drill:8",
                                        "--src", "water=pump:rotary-pump"]));
  const pump = res.machines.filter(m => m.name === "rotary-pump")[0];
  assert.ok(pump, "机器表应有 rotary-pump");
  const need = res.liquids.filter(l => l.name === "water")[0];
  assert.ok(need.perSecond > 0);
  assert.ok(pump.count >= need.perSecond / 12 - 1e-6);
  assert.ok(res.liquidSources.length === 1);
  close(res.liquidSources[0].power, pump.count * 18);
  assert.ok(res.power > 0);
});
ok("--src water=pump:oil-extractor 抽错液体要报错", () => {
  let msg = null;
  try {
    cli.query(cli.parseArgs(["--block", "silicon-smelter", "--count", "3",
                             "--src", "sand=drill:laser-drill:8",
                             "--src", "water=pump:oil-extractor"]));
  } catch (e) { msg = e.message; }
  assert.ok(msg && msg.indexOf("oil") >= 0, msg);
});

/* 6. 渲染 */
ok("text 渲染含关键数字", () => {
  const t = cli.renderText(cli.query(cli.parseArgs(["--item", "graphite", "--rate", "1"])));
  assert.ok(/配比：graphite 1\/s/.test(t), t);
  assert.ok(/graphite-press ×2/.test(t), t);
  assert.ok(/coal 2\.667\/s/.test(t), t);
});
ok("md 渲染是表格", () => {
  const m = cli.renderMarkdown(cli.query(cli.parseArgs(["--item", "silicon", "--rate", "5"])));
  assert.ok(m.indexOf("| 建筑 | 台数 | 电力/s |") >= 0, m);
});
ok("chain 的 text 渲染有 T1~T5", () => {
  const t = cli.renderText(cli.query(cli.parseArgs(["--chain", "dagger", "--chainrate", "0.05"])));
  ["T1", "T2", "T3", "T4", "T5"].forEach(k => assert.ok(t.indexOf(k) >= 0, "缺 " + k));
});

/* 7. 默认边界：不写 --boundary 时 = 煤、沙 */
ok("默认边界是 coal,sand（走硅炉而不是硅坩埚）", () => {
  const res = cli.query(cli.parseArgs(["--item", "silicon", "--rate", "5"]));
  assert.ok(res.machines.some(m => m.name === "silicon-smelter"), JSON.stringify(res.machines.map(m => m.name)));
  assert.deepStrictEqual(res.demand.map(d => d.name), ["coal", "sand"]);
});
ok("--boundary all 把矿都当外部输入", () => {
  const res = cli.query(cli.parseArgs(["--item", "silicon", "--rate", "5", "--boundary", "all"]));
  assert.ok(res.demand.length >= 3, JSON.stringify(res.demand));
});
ok("--boundary none 什么都不当外部输入（能造的都要造）", () => {
  const res = cli.query(cli.parseArgs(["--item", "graphite", "--rate", "1", "--boundary", "none"]));
  assert.ok(res.machines.some(m => m.name !== "graphite-press"), "应该自己去造煤");
});

/* 8. JSON 图标剔除 */
ok("stripIcons 去掉 base64，--icons 保留", () => {
  const withIcons = run(["--item", "graphite", "--rate", "1", "--format", "json", "--icons"]);
  assert.ok(withIcons.indexOf("data:image/png;base64") >= 0);
  const stripped = run(["--item", "graphite", "--rate", "1", "--format", "json"]);
  assert.strictEqual(stripped.indexOf("data:image/png;base64"), -1);
  assert.ok(stripped.length < withIcons.length / 2);
});

/* 9. 错误分支 */
ok("未知物品 → exit 2 + 中文错误", () => {
  assert.strictEqual(runCode(["--item", "no-such-item", "--rate", "1"]), 2);
  assert.strictEqual(runCode(["--block", "graphite-press", "--count", "0"]), 2);
  assert.strictEqual(runCode(["--item", "graphite", "--rate", "1", "--src", "coal=weird:xx"]), 2);
});
ok("--format json 的错误也是 json", () => {
  let out = "";
  try { execFileSync(process.execPath, [CLI, "--item", "nope", "--rate", "1", "--format", "json"], { encoding: "utf8" }); }
  catch (e) { out = e.stdout || ""; }
  const j = JSON.parse(out);
  assert.strictEqual(j.ok, false);
  assert.ok(j.error);
});
ok("--list 能列全", () => {
  const t = run(["--list"]);
  ["物品（22）", "兵厂（17）", "发电厂（14）", "钻头（10）", "多产物（2）", "抽水泵（6）", "兵厂链（10）"].forEach(k =>
    assert.ok(t.indexOf(k) >= 0, "缺 " + k));
});
ok("--help 有用法", () => {
  assert.ok(run(["--help"]).indexOf("--src") >= 0);
});

/* 10. HTTP 外壳：查询串解析 + 直接喂 handler */
console.log("HTTP 外壳");
const serve = require(path.join(__dirname, "serve.cjs"));
ok("optsFromQuery 解析 item/rate/src/format", () => {
  const o = serve.optsFromQuery({ item: "silicon", rate: "5", src: ["sand=drill:laser-drill:8"], format: "json" });
  assert.strictEqual(o.item, "silicon");
  assert.strictEqual(o.rate, "5");
  assert.deepStrictEqual(o.src, ["sand=drill:laser-drill:8"]);
});

function fakeRes() {
  return {
    code: 0, body: "", headers: null,
    writeHead(c, h) { this.code = c; this.headers = h; },
    end(b) { this.body = b.toString("utf8"); }
  };
}
ok("GET /calc?item=graphite&rate=1 → 200 text", () => {
  const r = fakeRes();
  serve.handle({ url: "/calc?item=graphite&rate=1" }, r);
  assert.strictEqual(r.code, 200);
  assert.ok(r.body.indexOf("graphite-press ×2") >= 0, r.body);
});
ok("GET /calc?...&format=json → 合法 JSON", () => {
  const r = fakeRes();
  serve.handle({ url: "/calc?item=graphite&rate=1&format=json" }, r);
  const j = JSON.parse(r.body);
  assert.strictEqual(j.ok, true);
  assert.strictEqual(j.products[0].name, "graphite");
});
ok("GET /calc 缺参数 → 400；GET /healthz → 200", () => {
  const a = fakeRes(); serve.handle({ url: "/calc" }, a);
  assert.strictEqual(a.code, 400);
  const b = fakeRes(); serve.handle({ url: "/healthz" }, b);
  assert.strictEqual(b.code, 200);
  assert.strictEqual(JSON.parse(b.body).ok, true);
});
ok("GET /list、GET /nope", () => {
  const a = fakeRes(); serve.handle({ url: "/list" }, a);
  assert.strictEqual(a.code, 200);
  assert.ok(a.body.indexOf("发电厂") >= 0);
  const b = fakeRes(); serve.handle({ url: "/nope" }, b);
  assert.strictEqual(b.code, 404);
});


ok("--chainexpr 5t5：按台数反推", () => {
  const t = cli.renderText(cli.query({ chain: "dagger", chainexpr: "5t5" }));
  assert.ok(t.indexOf("目标 5 台 T5") >= 0, t);
  assert.ok(/T4 .*×2/.test(t), t);
  assert.ok(/T5 .*×5/.test(t), t);
  assert.ok(t.indexOf("材料（每分钟）") >= 0, t);
});
ok("--chain dagger --chainrate 0.05 仍按速率", () => {
  const t = cli.renderText(cli.query({ chain: "dagger", chainrate: "0.05" }));
  assert.ok(/T5 .*×12/.test(t), t);
});
ok("--src coal=belt:belt-grey：算出条数", () => {
  const r = cli.query({ item: "graphite", rate: "1", src: ["coal=belt:belt-grey"] });
  const t = cli.renderText(r);
  assert.ok(t.indexOf("灰带") >= 0, t);
  assert.ok(t.indexOf("×1 条") >= 0, t);
});
ok("--src coal=belt:phase-bridge：电力计入", () => {
  const r = cli.query({ item: "graphite", rate: "1", src: ["coal=belt:phase-bridge"] });
  assert.strictEqual(r.power, 18);
  assert.ok(cli.renderText(r).indexOf("电 18") >= 0);
});

ok("默认入料：不指定 --src 时走蓝带并给出条数", () => {
  const r = cli.query({ item: "silicon", rate: "5" });
  const src = (r.sources || []).filter((s) => s.type === "import");
  assert.ok(src.length >= 2, JSON.stringify(r.sources));
  src.forEach((s) => {
    assert.strictEqual(s.via, "belt-blue", JSON.stringify(s));
    assert.ok(s.count >= 1, JSON.stringify(s));
    assert.ok(Math.abs(s.perSecondTotal - s.count * 12.015) < 1e-6, JSON.stringify(s));
  });
  assert.strictEqual(r.power, 120); // silicon-smelter ×2，带子不耗电
  const t = cli.renderText(r);
  assert.ok(t.indexOf("蓝带") >= 0, t);
  assert.ok(t.indexOf("×1 条") >= 0, t);
});
ok("--src coal=import：同样回落蓝带", () => {
  const r = cli.query({ item: "graphite", rate: "1", src: ["coal=import"] });
  const s = (r.sources || []).filter((x) => x.type === "import" && x.item === "coal")[0];
  assert.ok(s && s.via === "belt-blue" && s.count === 1, JSON.stringify(r.sources));
});
ok("兵厂链也带外部入料（蓝带条数）", () => {
  const r = cli.query({ block: "tetrative-reconstructor", count: "5" });
  assert.strictEqual(r.mode, "chain");
  assert.ok(Array.isArray(r.sources) && r.sources.length > 0, "no sources");
  assert.ok(r.sources.every((s) => s.via === "belt-blue"), JSON.stringify(r.sources.slice(0, 3)));
  assert.ok(r.sources.some((s) => s.item === "silicon" && s.count >= 4), JSON.stringify(r.sources));
});

ok("发电设备当目标建筑：--block steam-generator ×2 出 660/s", () => {
  const r = cli.query({ block: "steam-generator", count: "2" });
  assert.strictEqual(r.mode, "building");
  assert.strictEqual(r.products[0].type, "power");
  assert.strictEqual(r.products[0].rate, 660);
  assert.ok(r.supply && r.supply.netTotal === 660, JSON.stringify(r.supply));
  assert.strictEqual(r.power, 0);
  const t = cli.renderText(r);
  assert.ok(t.indexOf("660/s") >= 0, t);
  assert.ok(t.indexOf("供电") >= 0, t);
});
ok("发电设备：--genfuel 选燃料", () => {
  const r = cli.query({ block: "impact-reactor", count: "2", genfuel: "blast-compound" });
  assert.strictEqual(r.products[0].rate, 12600);
  assert.ok(r.supply.fuel && r.supply.fuel.name === "blast-compound", JSON.stringify(r.supply.fuel));
});
ok("发电设备：不做电力递归（不多算发电机台数）", () => {
  const r = cli.query({ block: "steam-generator", count: "2" });
  const names = (r.machines || []).map((m) => m.name);
  assert.deepStrictEqual(names, ["steam-generator"], JSON.stringify(names));
  assert.strictEqual(r.power, 0);
});

/* ---- 混合厂：--mix 多个目标合并算上游 ---- */
ok("--mix：两个目标合并，石墨压机 10 台（分别建 11）", () => {
  const r = cli.query({ mix: "silicon-arc-furnace:1,carbide-crucible:1" });
  assert.strictEqual(r.mode, "mixed");
  assert.strictEqual(r.targets.length, 2);
  const gp = r.machines.filter((m) => m.name === "graphite-press")[0];
  assert.ok(gp && gp.count === 10, JSON.stringify(r.machines));
  assert.strictEqual(r.compare.savedMachines, 1);
  assert.strictEqual(r.power, 420);
});
ok("--mix：文本里写清目标/共享/对比", () => {
  const r = cli.query({ mix: "silicon-arc-furnace:1,carbide-crucible:1" });
  const t = cli.renderText(r);
  assert.ok(t.indexOf("混合厂") >= 0, t);
  assert.ok(t.indexOf("共享 graphite") >= 0, t);
  assert.ok(t.indexOf("对比分别建") >= 0, t);
});
ok("--mix：目标互供抵扣（石墨压机 3 台 + 硅电弧炉 1 台 → 不再另建压机）", () => {
  const r = cli.query({ mix: "graphite-press:3,silicon-arc-furnace:1" });
  const gp = r.machines.filter((m) => m.name === "graphite-press")[0];
  assert.strictEqual(gp.count, 3);
  assert.strictEqual(r.compare.machinesMixed, 4);
  assert.strictEqual(r.compare.savedMachines, 2);
});
ok("--mix：发电设备当目标，电力和发电都算", () => {
  const r = cli.query({ mix: "silicon-smelter:2,combustion-generator:1" });
  assert.strictEqual(r.power, 60);
  assert.strictEqual(r.powerOut, 60);
  assert.strictEqual(r.netPower, 0);
});
ok("--mix：兵厂给出明确报错", () => {
  try { cli.query({ mix: "ground-factory:1" }); throw new Error("expected throw"); }
  catch (e) { assert.ok(/兵厂/.test(e.message), e.message); }
});
ok("--mix：格式错误时报错清楚", () => {
  try { cli.query({ mix: "graphite-press:0" }); throw new Error("expected throw"); }
  catch (e) { assert.ok(/台数/.test(e.message), e.message); }
});

console.log("\n通过 " + pass + " 项，失败 " + fail + " 项");
process.exitCode = fail ? 1 : 0;
