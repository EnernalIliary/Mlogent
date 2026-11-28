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
    if(n) Call.sendMessage('[accent][MCP][] '+player.plainName()+' \u5426\u51b3\u4e86 '+n+' \u9879\u5f85\u6267\u884c\u64cd\u4f5c');
    else player.sendMessage('[accent][MCP][] \u6ca1\u6709\u53ef\u5426\u51b3\u7684\u5f85\u6267\u884c\u64cd\u4f5c');
  }
 });
 var thisScope=this;
 Vars.netServer.clientCommands.removeCommand('abort');
 Vars.netServer.clientCommands.register('abort','[all]','\u5426\u51b3\u6700\u8fd1\u4e00\u9879 MCP \u64cd\u4f5c\uff1ball \u5426\u51b3\u5168\u90e8\uff08\u6240\u6709\u4eba\u53ef\u7528\uff09',runner);
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
        'world_stop': '\u5173\u95ed\u6e38\u620f\u670d\u52a1\u5668',
        'world_load': '\u52a0\u8f7d\u6307\u5b9a\u5b58\u6863',
        'world_reset': '\u91cd\u7f6e\u5f53\u524d\u4e16\u754c',
        'world_switch_map': '\u5207\u6362\u6e38\u620f\u5730\u56fe',
        'world_clear': '\u6e05\u9664\u6307\u5b9a\u683c\u5efa\u7b51',
        'world_clear_buildings': '\u6e05\u9664\u5efa\u7b51',
        'world_kill_units': '\u6e05\u9664\u5355\u4f4d',
        'world_place': '\u653e\u7f6e\u6216\u66ff\u6362\u5efa\u7b51',
        'world_spawn': '\u751f\u6210\u5355\u4f4d',
        'world_logic_set': '\u4fee\u6539\u903b\u8f91\u5904\u7406\u5668\u4ee3\u7801',
        'world_logic_rollback': '\u56de\u6eda\u903b\u8f91\u5904\u7406\u5668\u4fee\u6539',
        'world_scene': '\u90e8\u7f72\u573a\u666f\u5e76\u4fee\u6539\u4e16\u754c',
        'world_console': '\u6267\u884c\u670d\u52a1\u5668\u63a7\u5236\u53f0\u547d\u4ee4',
        'world_js': '\u6267\u884c\u4fee\u6539\u4e16\u754c\u7684\u811a\u672c',
        'world_push_action': '\u66f4\u6539\u6e38\u620f\u4e16\u754c',
    }
    label = labels.get(name, '\u4fee\u6539\u6e38\u620f\u4e16\u754c')
    if name in {'world_console', 'world_js'} and delay_for(name, args) == 60:
        label = '\u6267\u884c\u53ef\u80fd\u5173\u95ed\u6e38\u620f\u670d\u52a1\u5668\u7684\u64cd\u4f5c'
    purpose = normalize_purpose(args.get('purpose'))
    details = []
    for key, title in (('map_id', '\u5730\u56fe\u7f16\u53f7'), ('map', '\u5730\u56fe'), ('name', '\u5b58\u6863\u540d'),
                       ('unit', '\u5355\u4f4d\u7c7b\u578b'), ('count', '\u6570\u91cf'), ('x', '\u5750\u6807X'),
                       ('y', '\u5750\u6807Y'), ('radius', '\u5f71\u54cd\u534a\u5f84')):
        if key in args:
            value = ' '.join(str(args[key]).split())[:80].replace('[', '\uff3b').replace(']', '\uff3d')
            details.append(title + '\uff1a' + value)
    parts = [label]
    if purpose:
        parts.append('\u4f5c\u7528\uff1a' + purpose)
    if details:
        parts.append('\u53c2\u6570\uff1a' + '\uff1b'.join(details))
    return '\n'.join(parts)


def normalize_purpose(value):
    if not isinstance(value, str):
        return ''
    value = ' '.join(value.split()).strip()
    return value[:240].replace('[', '\uff3b').replace(']', '\uff3d')

def delay_for(name, args):
    if name == 'world_stop':
        return 60
    if name == 'world_console':
        command = str(args.get('cmd', '')).strip()
        if re.match(r'^(?:exit|quit|stop|shutdown)(?:\s|$)', command, re.IGNORECASE) or re.search(
                r'closeServer|System\s*\.\s*exit', command, re.IGNORECASE):
            return 60
    if name == 'world_js' and re.search(
            r'(?:Vars\s*\.\s*net\s*\.\s*closeServer\s*\(|System\s*\.\s*exit\s*\(|Core\s*\.\s*app\s*\.\s*exit\s*\()',
            str(args.get('code', '')), re.IGNORECASE):
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
    purpose = normalize_purpose(args.get('purpose'))
    if delay and len(purpose) < 8:
        raise ValueError('A concise purpose is required so players can review the pending world change in-game')
    action_args = {key: value for key, value in args.items() if key != 'purpose'}
    if name == 'world_stop':
        # Occupancy and the state change are checked under the owner's lock.
        # Never install the in-game veto queue just to stop a sleeping JVM.
        stop_sleeping = getattr(client, 'stop_if_sleeping', None)
        if stop_sleeping is not None:
            stopped = stop_sleeping()
            if stopped is not None:
                return stopped
    if not delay:
        return fn(action_args)
    key = uuid.uuid4().hex
    # Install is idempotent and does not replace pending veto state.
    if _js(client, GAME_INSTALL) != 'ready':
        raise RuntimeError('Could not install /abort; operation not executed')
    label = describe_action(name, args)
    message = '[MCP] ' + label + ' \u5c06\u5728 ' + str(delay) + ' \u79d2\u540e\u6267\u884c\u3002\u4efb\u4f55\u73a9\u5bb6\u90fd\u53ef\u4ee5\u8f93\u5165 /abort \u5426\u51b3\uff0c/abort all \u5426\u51b3\u5168\u90e8\u3002'
    # Transport ASCII only: the world console rewrites unicode escapes.
    import base64
    encoded = base64.b64encode(message.encode()).decode()
    code = ('var q=this._mcpVeto;if(!q){throw new Error("veto state missing");}'
            'q.jobs[' + json.dumps(key) + ']={state:"pending",deadline:java.lang.System.currentTimeMillis()+' + str(delay * 1000) + '};'
            'q.order.push(' + json.dumps(key) + ');'
            'Call.sendMessage(new java.lang.String(java.util.Base64.getDecoder().decode("' + encoded + '"),java.nio.charset.StandardCharsets.UTF_8));sb.append("queued");')
    if _js(client, code) != 'queued':
        raise RuntimeError('Could not announce pending operation; not executed')
    _record(key, state='pending', tool=name, purpose=purpose, delay_seconds=delay, arguments=action_args)
    threading.Thread(target=_finish, args=(client, key, delay, fn, copy.deepcopy(action_args)), daemon=True).start()
    return {'ok': True, 'status': 'scheduled', 'action_id': key, 'delay_seconds': delay,
            'purpose': purpose,
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
            schema = tool.setdefault('inputSchema', {})
            properties = schema.setdefault('properties', {})
            properties['purpose'] = {
                'type': 'string', 'minLength': 8, 'maxLength': 240,
                'description': 'Required: concise Chinese explanation of what this operation changes and why; shown to players in-game during the veto period.'
            }
            if tool['name'] != 'world_push_action':
                required = schema.setdefault('required', [])
                if 'purpose' not in required:
                    required.append('purpose')
            tool['description'] += ' Supply purpose in concise Chinese; it is displayed in-game with the pending action during the veto period.'
            tool['description'] += (' Sleeping-world shutdown is immediate without waking it; running-world shutdown saves a recovery checkpoint after its 60-second player veto period.'
                                    if tool['name'] == 'world_stop' else '')
            tool['description'] += ' Destructive operations on a running world are staged for player veto; scheduled is not success. Use world_action_status to confirm staged operations.'
