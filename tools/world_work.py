"""Temporary online-world execution for MCP work; empty worlds return to sleep.

The game owns expiring leases, so an MCP crash cannot leave autoPause disabled.
Only actual work handlers enter this scope, never read-only queries or offline sim.
"""
from contextlib import contextmanager
import base64
import functools
import json
import sys
import threading
import uuid

TARGET = '大肥鱼的调试世界'
WORK = frozenset({
    'world_place', 'world_spawn', 'world_kill_units', 'world_clear_buildings',
    'world_clear', 'world_logic_set', 'world_logic_batch_set', 'world_logic_batch_rollback',
    'world_logic_rollback', 'world_schematic', 'world_scene', 'world_scene_probe',
    'world_mirror_state', 'world_mirror_feed', 'world_arm', 'world_projection', 'world_door',
    'world_js', 'world_console', 'mlog_diff',
})

ACQUIRE = r'''
var root=this, now=java.lang.System.currentTimeMillis();
var q=root._mcpWorldWork;
if(!q){
 q={leases:{},managed:false}; root._mcpWorldWork=q;
 var timer=new JavaAdapter(Packages.arc.util.Timer.Task,{run:function(){
  Core.app.post(new java.lang.Runnable({run:function(){
   var t=java.lang.System.currentTimeMillis(),live=false;
   for(var k in q.leases){if(q.leases[k]>t){live=true;}else{delete q.leases[k];}}
   if(q.managed&&!live){
    Core.settings.put('autoPause',true); q.managed=false;
    if(Groups.player.size()===0&&Vars.state.isGame()){
     Vars.state.set(Packages.mindustry.core.GameState.State.paused);
    }
   }
  }}));
 }});
 Packages.arc.util.Timer.schedule(timer,1,1); q.timer=timer;
}
if(Groups.player.size()===0){
 var target=new java.lang.String(java.util.Base64.getDecoder().decode(TARGET64),java.nio.charset.StandardCharsets.UTF_8);
 var current=Packages.arc.util.Strings.stripColors(Vars.state.map.name());
 if(String(current)!==String(target)){
  var map=null; var maps=Vars.maps.all();
  for(var i=0;i<maps.size;i++){
   var m=maps.get(i);
   if(String(Packages.arc.util.Strings.stripColors(m.name()))===String(target)){map=m;break;}
  }
  if(map===null){throw new Error('Default MCP debug map not found');}
  var backup=new Packages.arc.files.Fi('config/saves/mcp-before-work-'+now+'.msav');
  Packages.mindustry.io.SaveIO.save(backup);
  if(Groups.player.size()!==0){throw new Error('Player joined; automatic map switch cancelled');}
  Vars.world.loadMap(map,map.applyRules(Packages.mindustry.game.Gamemode.sandbox));
  Vars.logic.play();
  Vars.state.rules.waves=false;Vars.state.rules.infiniteResources=true;
  Vars.state.rules.canGameOver=false;Vars.state.rules.logicUnitControl=true;
 }
 Vars.state.set(Packages.mindustry.core.GameState.State.playing);
}
q.managed=true;Core.settings.put('autoPause',false);
q.leases[LEASE]=now+60000;
sb.append('ready');
'''

RENEW = "var q=this._mcpWorldWork;if(q&&q.leases[LEASE]){q.leases[LEASE]=java.lang.System.currentTimeMillis()+60000;}sb.append('ready');"
RELEASE = r'''
var q=this._mcpWorldWork;
if(q){
 delete q.leases[LEASE];var live=false,t=java.lang.System.currentTimeMillis();
 for(var k in q.leases){if(q.leases[k]>t){live=true;}}
 if(q.managed&&!live){Core.settings.put('autoPause',true);q.managed=false;
  if(Groups.player.size()===0&&Vars.state.isGame()){
   Vars.state.set(Packages.mindustry.core.GameState.State.paused);
  }
 }
}
sb.append('ready');
'''


def needs_world(name, arguments):
    if name not in WORK:
        return False
    if arguments.get('preview'):
        return False
    if name == 'world_console':
        cmd = str(arguments.get('command', arguments.get('cmd', ''))).strip().lower()
        if cmd.startswith(('pause', 'config autopause', 'stop', 'exit', 'host', 'nextmap', 'gameover')):
            return False
    return True


def _js(client, code):
    result = client.call({'op': 'js', 'code': code}, timeout=12)
    if not result.get('ok') or result.get('lines') != ['ready']:
        raise RuntimeError('MCP world execution lease failed: ' + str(result))


@contextmanager
def awake(client):
    lease = json.dumps(uuid.uuid4().hex)
    target = json.dumps(base64.b64encode(TARGET.encode()).decode())
    acquire = ACQUIRE.replace('TARGET64', target).replace('LEASE', lease)
    _js(client, acquire)
    stop = threading.Event()
    def renew():
        while not stop.wait(15):
            try:
                _js(client, RENEW.replace('LEASE', lease))
            except Exception as exc:
                sys.stderr.write('world lease renewal failed: %s\n' % exc)
                return
    thread = threading.Thread(target=renew, daemon=True)
    thread.start()
    try:
        yield
    finally:
        stop.set()
        thread.join(timeout=13)
        try:
            _js(client, RELEASE.replace('LEASE', lease))
        except Exception as exc:
            # Expiry on the game's independent Timer still restores autoPause.
            sys.stderr.write('world lease release failed; expiry will recover: %s\n' % exc)


def wrap(name, handler, client):
    @functools.wraps(handler)
    def run(arguments):
        if not needs_world(name, arguments):
            return handler(arguments)
        with awake(client):
            return handler(arguments)
    return run
