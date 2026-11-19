"""World event streams and installation script, independent of daemon state."""
import json

OPERATIONS = frozenset(('chat', 'chat_log', 'messages', 'push', 'agent_push', 'changes'))

EV_INSTALL_JS = r"""
if(typeof _evlog === 'undefined'){
  _evlog = []; _evseq = 0; _mineHits = []; _mineIgnore = null;
  /* 管理员在游戏里打 /push <文本> = 直接把话插给 agent(队列由 Python 侧取走) */
  _pushlog = [];
  /* 玩家拆掉脉冲地雷 = 结束投影. _mineGone 收所有被清空的格子, 由导演挑出圆心那颗 */
  _mineGone = []; _mineIgnoreAir = null;
  var Cons = Packages.arc.func.Cons;
  /* 注意: 嵌套类必须写成完整的 Packages...EventType$Xxx, 不能拿 ET 再做字符串拼接 */
  var EV_TILE = Packages.mindustry.game.EventType$TileChangeEvent;
  var EV_CONF = Packages.mindustry.game.EventType$ConfigEvent;
  var push = function(kind, t, blockName, teamName, extra){
    _evseq++;
    _evlog.push(kind+'\t'+_evseq+'\t'+Vars.state.tick+'\t'+t.x+'\t'+t.y+'\t'
      +blockName+'\t'+teamName+'\t'+extra);
    /* 环形缓冲: 只留最近 500 条 */
    if(_evlog.length > 500) _evlog.shift();
  };
  Packages.arc.Events.on(EV_TILE, new JavaAdapter(Cons, {get: function(e){
    try{
      var t = e.tile;
      if(t == null) return;
      var b = t.block();
      var sz = 0; try{ sz = b.size; }catch(e2){}
      /* 多格方块落地时, 非原点格会各报一条 air, 靠 size 在 Python 侧消掉 */
      push(b.name=='air' ? 'B' : 'P', t, b.name, t.team().name, 'size='+sz);
      /* 玩家放下脉冲地雷 = 请求投影; _mineIgnore 用来吞掉服务端自己钉回去的那一颗 */
      try{
        if(b.name == %(mineblock)s){
          var mk = t.x + ',' + t.y;
          if(_mineIgnore == mk){ _mineIgnore = null; }
          else { _mineHits.push(mk); }
        }else if(b.name == 'air'){
          /* 拆雷 = 结束. 场景 clear 会先抹掉地雷再钉回来, 那一格由 _mineIgnoreAir 吞掉 */
          var ak = t.x + ',' + t.y;
          if(_mineIgnoreAir == ak){ _mineIgnoreAir = null; }
          else {
            _mineGone.push(ak);
            if(_mineGone.length > 200) _mineGone.shift();
          }
        }
      }catch(e6){}
    }catch(err){}
  }}));
  Packages.arc.Events.on(EV_CONF, new JavaAdapter(Cons, {get: function(e){
    try{
      var b = e.tile; if(b == null) return;
      push('C', b.tile, b.block.name, b.team.name, (e.value==null?'':String(e.value)));
    }catch(err){}
  }}));
  sb.append('installed');
  /* 玩家聊天: 服务端 PlayerChatEvent(player, message), 记到 _chatlog + chat.log */
  try{
    if(typeof _chatlog === 'undefined'){
      /* /push 的核心: 写内存队列 + 追加 push.jsonl + 回执. 命令与 '!push' 共用. */
      function _pushAccept(body, adm, plain, send){
        send = send || function(){};
        if(!adm){
          try{ send('[scarlet]只有管理员能用 /push[]. 让主机在控制台打: admin ' + plain); }catch(ea1){}
          return false;
        }
        body = ('' + (body == null ? '' : body)).replace(/^\s+/, '');
        if(body.length == 0){
          try{ send('[lightgray]用法: [accent]/push <要转交给 agent 的文字>'); }catch(ea2){}
          return false;
        }
        var rec = JSON.stringify({tick: Math.floor(Vars.state.tick), player: '' + plain, message: body});
        _pushlog.push(rec);
        if(_pushlog.length > 50) _pushlog.shift();
        try{
          var pw2 = new java.io.PrintWriter(new java.io.FileWriter(%(pushfile)s, true));
          pw2.println(rec);
          pw2.close();
        }catch(pe){}
        try{ send('[accent][agent][] 收到 /push(' + body.length + ' 字), 已转交给会话'); }catch(pa){}
        return true;
      }
      function _joinArgs(a){
        if(a == null) return '';
        var s = '';
        for(var i = 0; i < a.length; i++){ if(i > 0) s += ' '; s += '' + a[i]; }
        return s;
      }
      /* 注册成真正的服务器命令: 会出现在 /help, 有参数提示, 不再当聊天广播. */
      try{
        var _pushRunner = new JavaAdapter(Packages.arc.util.CommandHandler$CommandRunner, {
          accept: function(args, player){
            var adm = false, plain = '?';
            try{ adm = player != null && player.admin; }catch(eb1){}
            try{ plain = player.plainName(); }catch(eb2){
              try{ plain = player.name; }catch(eb3){ plain = '?'; }
            }
            _pushAccept(_joinArgs(args), adm, plain, function(s){
              try{ player.sendMessage(s); }catch(eb4){}
            });
          }
        });
        Vars.netServer.clientCommands.register('push', '<text...>',
          '把一句话插给 agent 会话（仅管理员）', _pushRunner);
        sb.append(' pushcmd=1');
      }catch(ec){ sb.append(' pushcmd=ERR:' + ec); }
      _chatlog = []; _chatseq = 0;
      var EV_CHAT = Packages.mindustry.game.EventType$PlayerChatEvent;
      var CHATLOG_PATH = %(chatlog)s;
      Packages.arc.Events.on(EV_CHAT, new JavaAdapter(Cons, {get: function(e){
        try{
          var nm = '?'; try{ nm = e.player.name; }catch(e3){}
          var msg = e.message == null ? '' : String(e.message);
          _chatseq++;
          _chatlog.push(_chatseq + '\t' + Vars.state.tick + '\t' + nm + '\t' + msg);
          if(_chatlog.length > 300) _chatlog.shift();
          try{
            var fw = new java.io.PrintWriter(new java.io.FileWriter(CHATLOG_PATH, true));
            fw.println('[' + Math.floor(Vars.state.tick) + '] ' + nm + ': ' + msg); fw.close();
          }catch(e4){}
          /* '!push <文本>' = 老写法, 保留给 /push 命令不可用的场合.
             注意 PlayerChatEvent 在命令分发之前就触发, 所以 '/push' 会走下面的
             注册命令, 这条分支只认 '!push', 否则同一句话会被排队两次. */
          try{
            var low = msg.toLowerCase();
            if(low.indexOf('!push ') == 0){
              var body = msg.substring(6).replace(/^\s+/, '');
              var adm = false; try{ adm = e.player != null && e.player.admin; }catch(e7){}
              var plain = nm; try{ plain = e.player.plainName(); }catch(e8){}
              _pushAccept(body, adm, plain, function(s){
                try{ e.player.sendMessage(s); }catch(e9){}
              });
            }
          }catch(ea){}
        }catch(err){}
      }}));
      sb.append(' chat=1');
    }
  }catch(e5){ sb.append(' chat=ERR:' + e5); }

  /* 调试世界: 进来的玩家自动给 admin, 这样他才能在聊天栏用 /push 跟 agent 说话.
     (真正的线上服不该这样; 用 --no-push-admin 关掉) */
  try{
    if(%(autoadmin)d){
      var EV_JOIN = Packages.mindustry.game.EventType$PlayerJoinEvent;
      Packages.arc.Events.on(EV_JOIN, new JavaAdapter(Cons, {get: function(e){
        try{ if(e.player != null) e.player.admin = true; }catch(ej){}
      }}));
      try{ Packages.mindustry.gen.Groups.player.each(function(p){ try{ p.admin = true; }catch(ep){} }); }catch(ep2){}
      sb.append(' admin=1');
    }
  }catch(ea0){}
  /* 点击门: 玩家点一下地雷/任意方块, 就把他的视角/操作带进沙盘 */
  try{
    if(typeof _doors === 'undefined'){
      _doors = {}; _doorjs = {}; _taplog = []; _tapseq = 0; _ret = {}; _doorHits = [];
      var EV_TAP = Packages.mindustry.game.EventType$TapEvent;
      Packages.arc.Events.on(EV_TAP, new JavaAdapter(Cons, {get: function(e){
        try{
          var t = e.tile; if(t == null) return;
          var np = '-'; try{ np = (e.player == null ? '-' : e.player.name); }catch(e1){}
          _tapseq++;
          _taplog.push(_tapseq + '\t' + Math.floor(Vars.state.tick) + '\t' + t.x + '\t' + t.y + '\t' + np);
          if(_taplog.length > 200) _taplog.shift();
          _doorAct(e.player, t.x, t.y);
        }catch(err){}
      }}));
      sb.append(' tap=1');
    }
  }catch(e6){ sb.append(' tap=ERR:' + e6); }
} else {
  sb.append('already');
}
"""


CHANGES_JS = r"""
if(typeof _evlog === 'undefined'){ sb.append('NOSETUP\t0'); }
else {
  var since = %(since)d, lim = %(limit)d, n = 0;
  for(var i=0;i<_evlog.length;i++){
    var ln = _evlog[i];
    var p = ln.split('\t');
    if(p.length < 2) continue;
    if(parseInt(p[1], 10) <= since) continue;
    sb.append(ln).append('\n');
    if(++n >= lim) break;
  }
  sb.append('SEQ\t').append(_evseq);
}
"""


CHAT_JS = r"""
if(typeof _chatlog === 'undefined'){ sb.append('NOSETUP\t0'); }
else {
  var since = %(since)d, lim = %(limit)d, n = 0;
  for(var i=0;i<_chatlog.length;i++){
    var ln = _chatlog[i];
    var p = ln.split('\t');
    if(p.length < 2) continue;
    if(parseInt(p[0], 10) <= since) continue;
    sb.append(ln).append('\n');
    if(++n >= lim) break;
  }
  sb.append('SEQ\t').append(_chatseq);
}
"""


PUSH_JS = r"""
/* 管理员在游戏里打的 /push 队列: 取走(drain)或只读. 行是 JSON 字符串. */
if(typeof _pushlog === 'undefined'){ sb.append('NOSETUP\t0'); }
else {
  var n2 = _pushlog.length;
  for(var i2 = 0; i2 < n2; i2++){ sb.append(_pushlog[i2]).append('\n'); }
  if(%(drain)d) _pushlog = [];
  sb.append('SEQ\t').append(n2);
}
"""


def read_events(w, req):
    op = (req.get("op") or "").strip()
    if op in ("chat", "chat_log", "messages"):
        since = int(req.get("since") or 0)
        limit = int(req.get("limit") or 80)
        rows, seq = [], since
        for ln in w.js(CHAT_JS % {"since": since, "limit": limit}):
            if ln.startswith("ERR"):
                return {"ok": False, "error": ln[4:]}
            if ln.startswith("NOSETUP"):
                return {"ok": False, "error": "chat hook not installed (daemon predates chat listener)"}
            if ln.startswith("SEQ\t"):
                seq = int(float(ln.split("\t")[1]))
                continue
            p = ln.split("\t")
            if len(p) >= 4:
                rows.append({"seq": int(float(p[0])), "tick": int(float(p[1])),
                             "player": p[2], "message": "\t".join(p[3:])})
        return {"ok": True, "rows": rows, "count": len(rows), "since": since, "nextSeq": seq}
    if op in ("push", "agent_push"):
        drain = 1 if req.get("drain", True) else 0
        rows, seq = [], 0
        for ln in w.js(PUSH_JS % {"drain": drain}):
            if ln.startswith("NOSETUP"):
                return {"ok": False, "error": "push hook not installed (restart the daemon)"}
            if ln.startswith("SEQ\t"):
                seq = int(float(ln.split("\t")[1]))
                continue
            ln = ln.strip()
            if not ln:
                continue
            try:
                rows.append(json.loads(ln))
            except Exception:
                rows.append({"raw": ln})
        return {"ok": True, "rows": rows, "count": len(rows), "nextSeq": seq}
    if op == "changes":
        since = int(req.get("since") or 0)
        limit = int(req.get("limit") or 200)
        rows, seq = [], since
        for ln in w.js(CHANGES_JS % {"since": since, "limit": limit}):
            if ln.startswith("SEQ\t"):
                # Rhino 把 number 交给 StringBuilder.append(double) 会打成 "12.0"
                seq = int(float(ln.split("\t")[1]))
                continue
            if ln.startswith("NOSETUP"):
                return {"ok": False, "error": "event listeners not installed (daemon predates EV_INSTALL_JS)"}
            p = ln.split("\t")
            if len(p) < 8:
                continue
            extra = p[7]
            size = 0
            if extra.startswith("size="):
                try:
                    size = int(float(extra[5:]))
                except Exception:
                    size = 0
                extra = ""
            rows.append({"kind": p[0], "seq": int(float(p[1])), "tick": int(float(p[2])),
                         "x": int(p[3]), "y": int(p[4]), "block": p[5],
                         "team": p[6], "size": size, "extra": extra})
        # 多格方块放置时相邻格会各报一条 air, 只保留原点那一条 + 真正的拆除
        covered = set()
        for r in rows:
            if r["kind"] == "P" and r["size"] > 1:
                for dx in range(r["size"]):
                    for dy in range(r["size"]):
                        if dx or dy:
                            covered.add((r["tick"], r["x"] + dx, r["y"] + dy))
        rows = [r for r in rows
                if not (r["kind"] == "B" and (r["tick"], r["x"], r["y"]) in covered)]
        return {"ok": True, "rows": rows, "count": len(rows), "since": since, "nextSeq": seq}
    return NotImplemented
