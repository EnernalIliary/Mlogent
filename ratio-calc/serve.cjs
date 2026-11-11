#!/usr/bin/env node
/* 配比计算器的 HTTP 形态 —— 给 bot（或任何语言）用 HTTP 调用，不在本进程里跑 JS。
 *
 *   node ratio-calc/serve.cjs --port 8799
 *   curl "http://127.0.0.1:8799/calc?item=silicon&rate=5&format=md"
 *   curl "http://127.0.0.1:8799/calc?block=ground-factory&count=2&gen=steam-generator&genfuel=coal&format=json"
 *   curl "http://127.0.0.1:8799/list"
 *   curl "http://127.0.0.1:8799/healthz"
 *
 * 查询串和 CLI 参数一一对应（--src 用 src=物品:drill:钻头:矿格数:0/1，可重复）。
 * 算法全部来自 cli.cjs / core.js，这里只做 HTTP 外壳。
 */
"use strict";

const http = require("http");
const url = require("url");
const { query, renderText, renderMarkdown, renderList, loadData, stripIcons, usage } = require("./cli.cjs");

const REPEATABLE = new Set(["src"]);

/* query string -> parseArgs 那种 opts 对象 */
function optsFromQuery(qs) {
  const opts = { src: [] };
  Object.keys(qs).forEach(key => {
    const vals = qs[key];
    const v = Array.isArray(vals) ? vals[vals.length - 1] : vals;
    if (REPEATABLE.has(key)) opts[key] = (Array.isArray(vals) ? vals : [v]).filter(x => x != null);
    else if (v === "" || v === "true") opts[key] = true;
    else opts[key] = v;
  });
  return opts;
}

/* query string -> {pathname, query}：同名 key 出现多次时收成数组 */
function parseQuery(raw) {
  const u = new URL(raw || "/", "http://127.0.0.1");
  const q = {};
  u.searchParams.forEach((v, k) => {
    if (q[k] === undefined) q[k] = v;
    else if (Array.isArray(q[k])) q[k].push(v);
    else q[k] = [q[k], v];
  });
  return { pathname: u.pathname.replace(/\/+$/, "") || "/", query: q };
}

function send(res, code, body, type) {
  const buf = Buffer.from(body, "utf8");
  res.writeHead(code, {
    "Content-Type": (type || "text/plain") + "; charset=utf-8",
    "Content-Length": buf.length,
    "Cache-Control": "no-store",
    "Access-Control-Allow-Origin": "*"
  });
  res.end(buf);
}

function handle(req, res) {
  const { pathname, query: q } = parseQuery(req.url);
  try {
    if (pathname === "/healthz") return send(res, 200, JSON.stringify({ ok: true, pid: process.pid }), "application/json");
    if (pathname === "/" || pathname === "/help") return send(res, 200, usage());
    if (pathname === "/list") return send(res, 200, renderList(loadData()));
    if (pathname !== "/calc") return send(res, 404, "× 只有 /calc、/list、/healthz、/");

    const opts = optsFromQuery(q);
    const fmt = String(opts.format || "text").toLowerCase();
    if (!opts.item && !opts.block) {
      return send(res, 400, "× 要给 item+rate 或 block+count\n\n" + usage());
    }
    const result = query(opts);
    if (fmt === "json") {
      return send(res, 200, JSON.stringify(opts.icons ? result : stripIcons(result)), "application/json");
    }
    if (fmt === "md" || fmt === "markdown") return send(res, 200, renderMarkdown(result), "text/markdown");
    return send(res, 200, renderText(result));
  } catch (err) {
    const fmt = String(q.format || "text").toLowerCase();
    if (fmt === "json") return send(res, 400, JSON.stringify({ ok: false, error: String(err.message || err) }), "application/json");
    return send(res, 400, "× " + (err.message || err));
  }
}

function main(argv) {
  let port = 8799, host = "127.0.0.1";
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--port") port = Number(argv[++i]);
    else if (argv[i] === "--host") host = argv[++i];
    else if (argv[i] === "--help") { console.log("node ratio-calc/serve.cjs [--port 8799] [--host 127.0.0.1]"); return; }
  }
  const server = http.createServer(handle);
  server.listen(port, host, () => {
    console.log("配比计算器 HTTP 服务：http://" + host + ":" + port + "/calc?item=silicon&rate=5");
  });
}

if (require.main === module) main(process.argv.slice(2));

module.exports = { handle, optsFromQuery, stripIcons };
