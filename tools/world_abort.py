"""Player-vetoable staging for destructive MCP world calls.

The game owns the veto state; loss of that state fails closed. Queueing is
asynchronous so HTTP timeouts cannot shorten the grace period.
"""
import copy
import json
import re
import threading
import time
import uuid
from pathlib import Path

GAME_INSTALL = r"""
if(!this._mcpVeto){
 this._mcpVeto={jobs:{},order:[]};
 var runner=new JavaAdapter(Packages.arc.util.CommandHandler$CommandRunner,{
  accept:function(args,player){
   var q=thisScope._mcpVeto,all=args.length>0&&String(args[0])==='all',n=0;
   for(var i=q.order.length-1;i>=0;i--){
    var j=q.jobs[q.order[i]];
    if(j&&j.state==='pending'){j.state='cancelled';n++;if(!all)break;}
   }
   if(n) Call.sendMessage('[accent][MCP][] '+player.plainName()+' 否决了 '+n+' 项待执行操作。');
   else player.sendMessage('[accent][MCP][] 没有可否决的待执行操作。');
  }
 });
 var thisScope=this;
 Vars.netServer.clientCommands.removeCommand('abort');
 Vars.netServer.clientCommands.register('abort','[all]','否决最近一项 MCP 操作；all 否决全部（所有人可用）',runner);
}
sb.append('ready');
"""

DESTRUCTIVE = {
    'world_stop', 'world_load', 'world_reset', 'world_switch_map',
    'world_clear', 'world_clear_buildings', 'world_kill_units',
    'world_place', 'world_spawn', 'world_logic_set', 'world_logic_batch_set', 'world_logic_batch_rollback', 'world_logic_rollback', 'world_scene',
    'world_console', 'world_js',
}
_execution_lock = threading.Lock()
_owner = uuid.uuid4().hex


def describe_action(name, args):
    labels = {
        'world_stop': '关闭游戏服务器', 'world_load': '载入世界存档',
        'world_reset': '重置当前世界', 'world_switch_map': '切换游戏地图',
        'world_clear': '清除指定区域', 'world_clear_buildings': '清除建筑',
        'world_kill_units': '清除单位', 'world_place': '放置或替换建筑',
        'world_spawn': '生成单位', 'world_logic_set': '修改逻辑处理器程序',
        'world_logic_rollback': '回滚逻辑处理器程序和链接',
        'world_scene': '部署场景并修改世界', 'world_console': '执行服务器控制台操作',
        'world_js': '执行修改世界的脚本', 'world_push_action': '切换游戏地图',
    }
    label = labels.get(name, '修改游戏世界')
    if name in {'world_console', 'world_js'} and delay_for(name, args) == 60:
        label = '执行可能关闭游戏服务器的操作'
    details = []
    for key, title in (('map_id', '地图编号'), ('map', '地图'), ('name', '名称'),
                       ('unit', '单位类型'), ('count', '数量'), ('x', '横坐标'),
                       ('y', '纵坐标'), ('radius', '范围半径')):
        if key in args:
            value = ' '.join(str(args[key]).split())[:80].replace('[', '［').replace(']', '］')
            details.append(title + '：' + value)
    return label + ('（' + '，'.join(details) + '）' if details else '')


def delay_for(name, args):
    if name == 'world_stop':
        return 60
    if name in {'world_console', 'world_js'} and re.search(
            r'\b(?:exit|quit|shutdown|stop)\b|closeServer|System\s*\.\s*exit',
            json.dumps(args), re.IGNORECASE):
        return 60
    if name in DESTRUCTIVE:
        return 15
    if name == 'world_push_action' and args.get('action') == 'switch_map':
        return 15
    return 0


def _js(client, code):
    result = client.call({'op': 'js', 'code': code, 'timeout': 10}, timeout=14)
    lines = result.get('lines') or []
    if not result.get('ok') or not lines:
        raise RuntimeError('MCP veto state could not be verified; operation not executed')
    return lines[0]


def _record(key, **fields):
    root = Path(__file__).resolve().parent.parent / 'out' / '_world' / 'mcp_actions'
    root.mkdir(parents=True, exist_ok=True)
    path = root / (key + '.json')
    old = json.loads(path.read_text()) if path.exists() else {}
    old.update(fields, id=key, owner=_owner)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(old, ensure_ascii=False, default=str), encoding='utf-8')
    tmp.replace(path)


def _finish(client, key, delay, fn, args):
    try:
        time.sleep(delay)
        with _execution_lock:
            # Claim on the game thread. /abort and claiming cannot interleave.
            code = ('var q=this._mcpVeto,j=q&&q.jobs[' + json.dumps(key) + '];'
                    'if(!j){sb.append("lost");}else if(j.state!=="pending"){sb.append(j.state);}'
                    'else if(java.lang.System.currentTimeMillis()<j.deadline){sb.append("early");}'
                    'else{j.state="executing";sb.append("execute");}')
            state = _js(client, code)
            if state != 'execute':
                _record(key, state='cancelled' if state == 'cancelled' else 'not_executed', reason=state)
                return
            _record(key, state='executing')
            result = fn(args)
            _record(key, state='completed', result=result)
    except Exception as exc:
        _record(key, state='failed', error=str(exc))


def schedule(client, name, fn, args):
    if name == 'world_stop':
        # Occupancy and the state change are checked under the owner's lock.
        # Never install the in-game veto queue just to stop a sleeping JVM.
        stop_sleeping = getattr(client, 'stop_if_sleeping', None)
        if stop_sleeping is not None:
            stopped = stop_sleeping()
            if stopped is not None:
                return stopped
    delay = delay_for(name, args)
    if not delay:
        return fn(args)
    key = uuid.uuid4().hex
    # Install is idempotent and does not replace pending veto state.
    if _js(client, GAME_INSTALL) != 'ready':
        raise RuntimeError('Could not install /abort; operation not executed')
    label = describe_action(name, args)
    message = '[MCP] ' + label + ' 将在 ' + str(delay) + ' 秒后执行。任何玩家可输入 /abort 否决，/abort all 否决全部。'
    # Transport ASCII only: the world console rewrites unicode escapes.
    import base64
    encoded = base64.b64encode(message.encode()).decode()
    code = ('var q=this._mcpVeto;if(!q){throw new Error("veto state missing");}'
            'q.jobs[' + json.dumps(key) + ']={state:"pending",deadline:java.lang.System.currentTimeMillis()+' + str(delay * 1000) + '};'
            'q.order.push(' + json.dumps(key) + ');'
            'Call.sendMessage(new java.lang.String(java.util.Base64.getDecoder().decode("' + encoded + '"),java.nio.charset.StandardCharsets.UTF_8));sb.append("queued");')
    if _js(client, code) != 'queued':
        raise RuntimeError('Could not announce pending operation; not executed')
    _record(key, state='pending', tool=name, delay_seconds=delay, arguments=args)
    threading.Thread(target=_finish, args=(client, key, delay, fn, copy.deepcopy(args)), daemon=True).start()
    return {'ok': True, 'status': 'scheduled', 'action_id': key, 'delay_seconds': delay,
            'message': 'Not executed yet. Any player can veto with /abort.',
            'status_tool': 'world_action_status'}


def install(handlers, tools, client):
    for name in list(handlers):
        if name in DESTRUCTIVE or name == 'world_push_action':
            original = handlers[name]
            handlers[name] = lambda args, n=name, f=original: schedule(client, n, f, args)
    def status(args):
        key = args.get('action_id', '')
        if not isinstance(key, str) or len(key) != 32 or any(c not in '0123456789abcdef' for c in key):
            raise ValueError('Invalid action_id')
        path = Path(__file__).resolve().parent.parent / 'out' / '_world' / 'mcp_actions' / (key + '.json')
        if not path.exists():
            return {'status': 'unknown'}
        record = json.loads(path.read_text())
        if record.get('state') == 'pending':
            if record.get('owner') != _owner:
                record.update(state='not_executed', reason='MCP service restarted')
            else:
                state = _js(client, 'var q=this._mcpVeto,j=q&&q.jobs[' + json.dumps(key) + '];sb.append(j?j.state:"lost");')
                if state != 'pending':
                    record.update(state=state)
        record.pop('arguments', None)
        record.pop('owner', None)
        return record
    handlers['world_action_status'] = status
    tools.append({'name': 'world_action_status', 'description': 'Read a staged MCP action result. Scheduled does not mean executed.',
                  'inputSchema': {'type': 'object', 'properties': {'action_id': {'type': 'string'}}, 'required': ['action_id'], 'additionalProperties': False}})
    for tool in tools:
        if tool['name'] in DESTRUCTIVE or tool['name'] == 'world_push_action':
            tool['description'] += (' Sleeping-world shutdown is immediate without waking it; running-world shutdown saves a recovery checkpoint after its 60-second player veto period.'
                                    if tool['name'] == 'world_stop' else '')
            tool['description'] += ' Destructive operations on a running world are staged for player veto; scheduled is not success. Use world_action_status to confirm staged operations.'
