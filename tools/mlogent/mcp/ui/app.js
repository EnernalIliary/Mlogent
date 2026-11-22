(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const page = document.body.dataset.page;
  const pending = new Map();
  let nextId = 0, ready = false, data = null, busy = false, dead = false;
  const notify = (method, params = {}) => parent.postMessage({jsonrpc: '2.0', method, params}, '*');
  function notice(message = '', error = false) {
    $('notice').textContent = message;
    $('notice').className = error ? 'error' : '';
  }
  function rpc(method, params) {
    if (dead) return Promise.reject(new Error('界面已关闭，请重新打开。'));
    return new Promise((resolve, reject) => {
      const id = ++nextId;
      const timer = setTimeout(() => { pending.delete(id); reject(new Error('请求超时，请重试。')); }, 30000);
      pending.set(id, {resolve, reject, timer});
      parent.postMessage({jsonrpc: '2.0', id, method, params}, '*');
    });
  }
  async function call(name, args) {
    const result = await rpc('tools/call', {name, arguments: args});
    if (result.isError) throw new Error(result.content?.find(c => c.type === 'text')?.text || '工具调用失败');
    const output = result.structuredContent || JSON.parse(result.content.find(c => c.type === 'text').text);
    render(output);
    return output;
  }
  function theme(context) {
    if (context?.theme) document.documentElement.style.colorScheme = context.theme;
  }
  function render(output) {
    if (!output || output.kind !== page) return;
    data = output;
    notice();
    if (page === 'signature') {
      const complete = data.status === 'complete' || data.status === 'preview';
      const preview = data.status === 'preview';
      const unsigned = data.signed === false;
      const requiresAuthor = data.signature_required !== false;
      $('title').textContent = complete ? (preview ? '蓝图预览' : unsigned ? '蓝图交付' : '签名完成') : requiresAuthor ? '确认作者签名' : '确认蓝图交付';
      $('state').textContent = preview ? '预览' : complete ? (unsigned ? '未签名' : '已签名') : '待确认';
      $('state').className = complete ? 'badge good' : 'badge';
      $('review').hidden = complete;
      $('delivery').hidden = !complete;
      if (complete) {
        $('intro').textContent = preview ? '检查处理器更新预览。' : unsigned ? '代码没有安全签名槽，已保留原有指令并生成未签名蓝图。' : '蓝图已生成，可以复制到游戏中使用。';
        $('delivery-title').textContent = preview ? '蓝图预览' : unsigned ? '蓝图已生成（未签名）' : '蓝图已签名';
        $('signed-author').textContent = preview ? '这是预览，尚未写入蓝图。' : unsigned ? '该蓝图不含作者签名。' : '作者：' + (data.author || '未署名');
        $('blueprint').value = data.result?.blueprint_base64 || JSON.stringify(data.result || {}, null, 2);
        if (unsigned && data.result?.warning) notice(data.result.warning, true);
      } else {
        $('name').textContent = data.name;
        $('operation').textContent = data.operation === 'mlog_inject' ? '更新处理器' : '生成新蓝图';
        $('digest').textContent = 'SHA-256 · ' + data.sha256;
        $('target').hidden = !data.target;
        if (data.target) {
          const target = data.target.processor;
          $('target').textContent = `目标：${target.block} @ (${target.x}, ${target.y}) · 处理器 ${target.index}`;
        }
        $('source-summary').textContent = `查看 ${data.lines} 行代码${data.preview_truncated ? '（预览已截断）' : ''}`;
        $('source').textContent = data.code_preview;
        $('cleanup-note').hidden = !data.parameter_cleanup?.length;
        $('cleanup-note').textContent = data.parameter_cleanup?.length ?
          '已移除无效占位参数：' + data.parameter_cleanup.map(c => `第 ${c.line} 行 (${c.removed.join(', ')})`).join('；') : '';
        if (document.activeElement !== $('author')) $('author').value = data.author || '';
        $('author').readOnly = data.author_locked;
        $('author').required = requiresAuthor;
        for (const id of ['author', 'author-label', 'author-note']) $(id).hidden = !requiresAuthor;
        $('submit').textContent = requiresAuthor ? '确认签名并生成蓝图' : '直接生成（不签名）';
        $('intro').textContent = requiresAuthor ? '检查这次交付的代码，填写署名。确认后生成带作者签名的蓝图。' : '代码没有可用签名槽，将保留原有指令并生成未签名蓝图。';
        $('author-note').textContent = data.author_locked ? '保留原有有效签名的作者名称。' : '仅用于这次交付，不修改其他会话的默认署名。';
        $('submit').disabled = !ready || busy;
      }
    } else {
      $('state').textContent = data.ok ? '运行中' : '不可用';
      $('state').className = data.ok ? 'badge good' : 'badge';
      $('updated').textContent = '更新于 ' + new Date(data.updated_at).toLocaleString();
      const s = data.status || {};
      const metrics = [['当前地图', s.map], ['模式', s.mode], ['波次', s.wave],
        ['在线玩家', s.players], ['单位', s.units], ['建筑', s.buildings],
        ['游戏端口', s.gamePort], ['世界状态', data.ok ? (s.paused ? '暂停' : '运行') : '未连接'],
        ['运行时长', typeof s.uptime === 'number' ? (s.uptime / 3600).toFixed(1) + ' 小时' : null]];
      $('metrics').replaceChildren(...metrics.map(([label, value]) => {
        const card = document.createElement('div'); card.className = 'metric';
        const title = document.createElement('span'); title.textContent = label;
        const content = document.createElement('strong'); content.textContent = value ?? '—';
        card.append(title, content); return card;
      }));
      const players = Array.isArray(data.players) ? data.players : [];
      $('player-count').textContent = players.length + ' 人';
      $('players').replaceChildren(...players.map(player => {
        const row = document.createElement('tr');
        for (const value of [player.name, player.team, `${player.x ?? '—'}, ${player.y ?? '—'}`, player.admin ? '管理员' : '玩家']) {
          const cell = document.createElement('td'); cell.textContent = value ?? '—'; row.append(cell);
        }
        return row;
      }));
      $('empty').hidden = players.length > 0;
      $('empty').textContent = data.ok ? '当前没有在线玩家。' : '世界状态暂不可用。';
      if (data.errors?.length) notice(data.errors.join('\n'), true);
    }
  }
  window.addEventListener('message', event => {
    if (event.source !== parent || event.data?.jsonrpc !== '2.0') return;
    const message = event.data;
    if (pending.has(message.id)) {
      const task = pending.get(message.id); pending.delete(message.id); clearTimeout(task.timer);
      if (message.error) task.reject(new Error(message.error.message || '宿主拒绝了请求'));
      else task.resolve(message.result);
    } else if (message.method === 'ui/notifications/tool-result') {
      if (message.params?.isError) notice(message.params.content?.[0]?.text || '工具调用失败', true);
      else render(message.params?.structuredContent);
    } else if (message.method === 'ui/notifications/host-context-changed') {
      theme(message.params);
    } else if (message.method === 'ui/notifications/tool-cancelled') {
      notice('调用已取消。', true);
    } else if (message.method === 'ui/resource-teardown') {
      dead = true;
      for (const task of pending.values()) { clearTimeout(task.timer); task.reject(new Error('界面已关闭')); }
      pending.clear();
      parent.postMessage({jsonrpc: '2.0', id: message.id, result: {}}, '*');
    } else if (message.method === 'ping') {
      parent.postMessage({jsonrpc: '2.0', id: message.id, result: {}}, '*');
    }
  });
  if (page === 'signature') {
    $('signature-form').addEventListener('submit', async event => {
      event.preventDefault();
      if (busy || !ready || !data || data.status !== 'pending') return;
      busy = true; $('submit').disabled = true; notice('正在签名并生成蓝图…');
      try { await call('mlog_signature_submit', {request_id: data.request_id, author: $('author').value.trim()}); }
      catch (error) { notice(error.message, true); }
      finally { busy = false; $('submit').disabled = false; }
    });
    $('copy').addEventListener('click', async () => {
      try { await navigator.clipboard.writeText($('blueprint').value); notice('粘贴码已复制。'); }
      catch { $('blueprint').focus(); $('blueprint').select(); notice('请复制已选中的粘贴码。'); }
    });
  } else {
    $('refresh').disabled = true;
    $('refresh').addEventListener('click', async () => {
      if (busy || !ready) return;
      busy = true; $('refresh').disabled = true; notice('正在刷新…');
      try { await call('world_dashboard', {}); } catch (error) { notice(error.message, true); }
      finally { busy = false; $('refresh').disabled = false; }
    });
  }
  rpc('ui/initialize', {appInfo: {name: 'Mlogent', version: '1.0.0'},
    appCapabilities: {availableDisplayModes: ['inline']}, protocolVersion: '2026-01-26'})
    .then(result => {
      ready = true; theme(result.hostContext); notify('ui/notifications/initialized');
      if (!data) notice('等待工具结果…');
      if (page === 'dashboard') $('refresh').disabled = false;
      else if (data) render(data);
      new ResizeObserver(() => notify('ui/notifications/size-changed', {
        height: document.documentElement.scrollHeight, width: document.documentElement.clientWidth
      })).observe(document.body);
    }).catch(error => notice('无法连接交互界面：' + error.message, true));
})();
