/* Browser contract test. Requires Playwright and a local Chromium installation.
 * NODE_PATH=<playwright node_modules> node tests/mcphttp/run_apps_ui_tests.js
 * Set CHROMIUM_PATH/PYTHON for other environments. No live game or OAuth needed.
 */
const {chromium} = require('playwright');
const {spawn} = require('node:child_process');
const http = require('node:http');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');

(async () => {
  const child = spawn(process.env.PYTHON || 'python', ['-X', 'utf8', 'tools/mlog_mcp_http_profiles.py',
    '--enable-ui', '--port', '0', '--token', 'local-ui-test-token', '--quiet'], {cwd: root});
  let browser, host;
  try {
    const banner = await new Promise((resolve, reject) => {
      let buffer = '';
      const timer = setTimeout(() => reject(new Error('MCP startup timed out')), 10000);
      child.once('error', reject);
      child.once('exit', code => reject(new Error('MCP exited: ' + code)));
      child.stdout.on('data', data => {
        buffer += data;
        if (buffer.includes('\n')) { clearTimeout(timer); resolve(JSON.parse(buffer.split('\n')[0])); }
      });
    });
    child.stderr.on('data', () => {});
    const rpc = async (method, params = {}) => {
      const response = await fetch(banner.listening, {method: 'POST', headers: {
        'Authorization': 'Bearer local-ui-test-token', 'Content-Type': 'application/json'},
        body: JSON.stringify({jsonrpc: '2.0', id: 1, method, params})});
      const reply = await response.json();
      assert.equal(response.status, 200);
      if (reply.error) throw new Error(reply.error.message);
      return reply.result;
    };
    const call = (name, args) => rpc('tools/call', {name, arguments: args});
    // Calling the original tool without an author must open the same form.
    const signature = await call('mlog_gen', {
      logic: 'set n 42\njump 0 always 0\n', name: '<img src=x onerror=alert(1)>'});
    assert.equal(signature.isError, false);
    const dashboard = {structuredContent: {kind: 'dashboard', ok: true,
      status: {ok: true, map: '测试世界', mode: 'survival', wave: 4, players: 1,
        units: 18, buildings: 749, gamePort: 6567, uptime: 1234, paused: false},
      players: [{name: '<script>bad()</script>', team: 'sharded', x: 4, y: 8, admin: true}],
      errors: [], updated_at: '2026-11-22T06:00:00Z'}};
    const resources = {};
    for (const [kind, uri] of [['signature', 'ui://mlogent/signature-v1.html'], ['dashboard', 'ui://mlogent/world-dashboard-v1.html']]) {
      resources[kind] = (await rpc('resources/read', {uri})).contents[0].text;
    }
    const hostScript = `
      const frame=document.querySelector('iframe');
      addEventListener('message',async event=>{
        if(event.source!==frame.contentWindow)return;
        const m=event.data;
        const reply=result=>frame.contentWindow.postMessage({jsonrpc:'2.0',id:m.id,result},'*');
        if(m.method==='ui/initialize')reply({protocolVersion:'2026-01-26',hostInfo:{name:'test-host',version:'1'},hostCapabilities:{serverTools:{}},hostContext:{theme:'light'}});
        else if(m.method==='ui/notifications/initialized')frame.contentWindow.postMessage({jsonrpc:'2.0',method:'ui/notifications/tool-result',params:window.initialResult},'*');
        else if(m.method==='tools/call'){
          const result=await fetch('/call',{method:'POST',body:JSON.stringify(m.params)}).then(r=>r.json());reply(result);
        }
      });`;
    host = http.createServer(async (req, res) => {
      try {
        if (req.url === '/call') {
          let body = ''; for await (const chunk of req) body += chunk;
          const params = JSON.parse(body);
          res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify(await call(params.name, params.arguments)));
          return;
        }
        const kind = req.url.includes('dashboard') ? 'dashboard' : 'signature';
        if (req.url.startsWith('/frame/')) {
          res.setHeader('Content-Type', 'text/html; charset=utf-8'); res.end(resources[kind]); return;
        }
        const initial = kind === 'signature' ? signature : dashboard;
        res.setHeader('Content-Type', 'text/html; charset=utf-8');
        res.end('<!doctype html><meta charset="utf-8"><style>body{margin:0}iframe{border:0;width:100%;height:1100px}</style>' +
          '<iframe title="MCP App" src="/frame/' + kind + '"></iframe><script>window.initialResult=' +
          JSON.stringify(initial).replaceAll('<', '\\u003c') + ';' + hostScript + '</script>');
      } catch (error) { res.statusCode = 500; res.end(JSON.stringify({error: error.message})); }
    });
    await new Promise(resolve => host.listen(0, '127.0.0.1', resolve));
    const base = 'http://127.0.0.1:' + host.address().port;
    browser = await chromium.launch({headless: true, executablePath: process.env.CHROMIUM_PATH ||
      'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
    const page = await browser.newPage({viewport: {width: 800, height: 1100}});
    const errors = []; page.on('pageerror', error => errors.push(error.message));
    await page.goto(base + '/signature');
    const frame = page.frameLocator('iframe');
    await frame.locator('#review').waitFor({state: 'visible'});
    assert.equal(await frame.locator('#name').textContent(), '<img src=x onerror=alert(1)>');
    assert.equal(await frame.locator('#name img').count(), 0);
    await frame.locator('#author').fill('浏览器测试作者');
    await page.screenshot({path: path.join(require('node:os').tmpdir(), 'mlogent-signature-ui.png')});
    await frame.locator('#submit').click();
    await frame.locator('#delivery').waitFor({state: 'visible'});
    assert.match(await frame.locator('#blueprint').inputValue(), /^bXNja/);
    assert.match(await frame.locator('#signed-author').textContent(), /浏览器测试作者/);
    await frame.locator('#copy').click();
    await page.goto(base + '/dashboard');
    await frame.locator('.metric').first().waitFor();
    assert.equal(await frame.locator('.metric').count(), 9);
    assert.match(await frame.locator('#players').textContent(), /<script>bad\(\)<\/script>/);
    assert.equal(await frame.locator('#players script').count(), 0);
    await page.screenshot({path: path.join(require('node:os').tmpdir(), 'mlogent-dashboard-ui.png')});
    await frame.locator('#refresh').click();
    // The fixture server has no world; refresh must show the real offline state.
    await frame.locator('#state').filter({hasText: '不可用'}).waitFor();
    await page.setViewportSize({width: 390, height: 1000});
    assert.equal(await frame.locator('body').evaluate(body => body.scrollWidth <= innerWidth), true);
    assert.deepEqual(errors, []);
    console.log('MCP Apps browser tests passed: author submission, delivery, safe text, refresh, mobile layout.');
  } finally {
    if (browser) await browser.close();
    if (host) await new Promise(resolve => host.close(resolve));
    child.kill();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
