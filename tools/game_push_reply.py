"""Install the native /push reply handler into the Mindustry runtime."""
import json
from pathlib import Path

INSTALL = r"""
(function(){
var mlogentPushRootRef = this;
if(mlogentPushRootRef._iliaryPushVersion !== 7){
  var mlogentPushPriorReply = mlogentPushRootRef._iliaryPushReply;
  var mlogentPushPendingRef = {};
  var mlogentPushOrderRef = [];
  var mlogentPushClock = function(){ return java.lang.System.currentTimeMillis(); };
  var reply = function(id, text){
    var entry = mlogentPushPendingRef[id];
    if(!entry) return typeof mlogentPushPriorReply === 'function' ? mlogentPushPriorReply(id,text) : 'expired';
    if(mlogentPushClock() - entry.at > 300000) return 'expired';
    var player = entry.player;
    if(!player.con || !player.con.equals(entry.connection) || !player.isAdded()) return 'offline';
    if(entry.replied) return 'sent';
    player.sendMessage('[accent][晓暮][] ' + text);
    entry.replied = true;
    return 'sent';
  };

  var action = function(id, request){
    var entry = mlogentPushPendingRef[id];
    if(!entry || mlogentPushClock() - entry.at > 300000) return {status:'expired'};
    var p = entry.player;
    if(!p.con || !p.con.equals(entry.connection) || !p.isAdded() || !p.admin) return {status:'not_authorized'};
    if(request.action === 'switch_map'){
      var body=entry.body || '';
      var target=String(request.map_id);
      if(!/换图|切图|换到|切到|切换|换地图/.test(body) || !(new RegExp('(^|[^0-9])'+target+'([^0-9]|$)')).test(body)) return {status:'explicit_map_required'};
      if(entry.actionResult) return {status:'already_requested'};
      if(String(Vars.state.rules.tags.get('id')) === target) return {status:'already_loaded',map_id:request.map_id};
      entry.actionResult={status:'switch_requested'};
      return {status:'authorized'};
    }
    if(entry.actionResult) return entry.actionResult;
    var team=p.team(), result;
    if(request.action === 'fill_core'){
      var core=team.core();
      var item=Vars.content.getByName(Packages.mindustry.ctype.ContentType.item, request.item);
      if(!core || !item) return {status:'not_found'};
      var before=core.items.get(item), capacity=core.storageCapacity;
      if(capacity<1) return {status:'not_found'};
      Packages.mindustry.gen.Call.setItem(core,item,Math.max(before,capacity));
      result={status:'applied',action:'fill_core',item:request.item,amount:core.items.get(item),added:Math.max(0,capacity-before)};
    }else if(request.action === 'spawn_units'){
      var type=Vars.content.getByName(Packages.mindustry.ctype.ContentType.unit,request.unit);
      if(!type) return {status:'not_found'};
      if(request.count<1 || request.count!==Math.floor(request.count)) return {status:'invalid_count'};
      var spawned=0;
      for(var i=0;i<request.count;i++){
        try{ if(type.spawn(team,p.x,p.y)) spawned++; }catch(e){ break; }
      }
      result={status:spawned===request.count?'applied':'partial',action:'spawn_units',unit:request.unit,amount:spawned};
    }else{
      return {status:'invalid_action'};
    }
    entry.actionResult=result;
    return result;
  };

  mlogentPushRootRef._iliaryPushAccept = function(args, player){
      if(!player || !player.admin){
        if(player) player.sendMessage('[scarlet]只有管理员能用 /push[].');
        return;
      }
      var parts = [];
      for(var i=0; args && i<args.length; i++) parts.push(String(args[i]));
      var body = parts.join(' ').trim();
      if(!body) return;
      body = body.slice(0,1600);
      var id = String(java.util.UUID.randomUUID()).replace(/-/g,'');
      mlogentPushPendingRef[id] = {player: player, connection: player.con, at: mlogentPushClock(), body: body};
      mlogentPushOrderRef.push(id);
      if(mlogentPushOrderRef.length>50) delete mlogentPushPendingRef[mlogentPushOrderRef.shift()];
      var row = {tick: Math.floor(Vars.state.tick), player: String(player.plainName()), message: body};
      try{
        var log = new java.io.PrintWriter(new java.io.FileWriter(PUSH_FILE, true));
        try{ log.println(JSON.stringify(row)); } finally{ log.close(); }
      }catch(err){}
      var dir = new java.io.File(PUSH_SPOOL);
      if(!dir.isDirectory()&&!dir.mkdirs()){
        delete mlogentPushPendingRef[id];
        player.sendMessage('[scarlet]Server Agent queue unavailable.');return;
      }
      var temp = new java.io.File(dir, id + '.pending');
      var target = new java.io.File(dir, id + '.json');
      try{
        var file = new java.io.PrintWriter(temp, 'UTF-8');
        try{
          row.reply_id = id;
          row.created_ms = mlogentPushClock();
          file.println(JSON.stringify(row));
          if(file.checkError()) throw new Error('push event write failed');
        }finally{ file.close(); }
        if(!temp.renameTo(target)) throw new Error('push event publish failed');
      }catch(error){
        temp.delete();
        delete row.reply_id;
        delete row.created_ms;
        delete mlogentPushPendingRef[id];
        player.sendMessage('[scarlet]Server Agent queue unavailable. Please retry.');
        return;
      }
      _pushlog.push(JSON.stringify(row));
      if(_pushlog.length>50) _pushlog.shift();
      player.sendMessage('[accent][服务器 Agent][] 已提交请求，回复将私下发送。');
  };
  var runner = new JavaAdapter(Packages.arc.util.CommandHandler$CommandRunner,{
    accept:function(args,player){mlogentPushRootRef._iliaryPushAccept(args,player);}
  });
  Vars.netServer.clientCommands.removeCommand('push');
  Vars.netServer.clientCommands.register('push','<text...>','交给服务器 Agent，私下回复（仅管理员）',runner);
  if(!mlogentPushRootRef._iliaryPushChatFilter){
    var filter=new JavaAdapter(Packages.mindustry.net.Administration$ChatFilter,{
      filter:function(player,message){
        var match=/^\s*[!/]push(?:\s+([\s\S]*))?\s*$/.exec(String(message));
        if(!match)return message;
        mlogentPushRootRef._iliaryPushAccept([match[1]||''],player);return null;
      }
    });
    Vars.netServer.admins.chatFilters.insert(0,filter);
    mlogentPushRootRef._iliaryPushChatFilter=filter;
  }
  mlogentPushRootRef._iliaryPushReply = reply;
  mlogentPushRootRef._iliaryPushAction = action;
  mlogentPushRootRef._iliaryPushVersion = 7;
}
sb.append(typeof mlogentPushRootRef._iliaryPushReply === 'function' ? 'ready' : 'missing');
})();
"""


def installation(path):
    return (INSTALL.replace("PUSH_FILE", json.dumps(str(path)))
            .replace("PUSH_SPOOL", json.dumps(str(Path(path).with_name('push_replies')))))
