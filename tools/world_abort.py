"""Player-vetoable staging for destructive MCP world calls.

The game owns the veto state; loss of that state fails closed. Queueing is
asynchronous so HTTP timeouts cannot shorten the grace period.
"""
import copy
import json
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
    'world_place', 'world_spawn', 'world_logic_set', 'world_scene',
    'world_console', 'world_js',
}
_execution_lock = threading.Lock()
_owner = uuid.uuid4().hex


def delay_for(name, args):
    # Arbitrary console/JS could shut down the server, so use the longer grace.
    if name in {'world_stop', 'world_console', 'world_js'}:
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
    delay = delay_for(name, args)
    if not delay:
        return fn(args)
    key = uuid.uuid4().hex
    # Install is idempotent and does not replace pending veto state.
    if _js(client, GAME_INSTALL) != 'ready':
        raise RuntimeError('Could not install /abort; operation not executed')
    summary = ', '.join(str(k) + '=' + str(args[k])[:80] for k in
                        ('action', 'map_id', 'map', 'name', 'unit', 'count', 'x', 'y', 'radius') if k in args)
    label = name + (' (' + summary + ')' if summary else '')
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
            tool['description'] += ' Destructive operations are staged for player veto; scheduled is not success. Use world_action_status to confirm.'
