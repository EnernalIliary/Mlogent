"""Public connection instructions for the in-game and console mcp commands."""
import base64
import json
import os
from urllib.parse import urlsplit

DEFAULT_ENDPOINT = 'https://mcp.iliary.life/mcp'
DEFAULT_HOME = 'https://mcp.iliary.life/'


def guide_text(endpoint=DEFAULT_ENDPOINT):
    parsed = urlsplit(endpoint)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment
            or any(ord(c) < 33 for c in endpoint)):
        raise ValueError('MCP endpoint must be a public HTTPS URL without credentials')
    config = {'mcpServers': {'mlogent': {'type': 'http', 'url': endpoint}}}
    return '\n'.join([
        '[accent]Mlogent MCP 配置指南[]',
        '[white]介绍与配置引导：' + DEFAULT_HOME,
        '[white]接入地址：' + endpoint,
        '传输方式：Streamable HTTP；支持 OAuth 2.1（PKCE）和 Bearer Token。',
        '在支持 MCP 的客户端添加以上地址，并完成 OAuth 授权。可用工具和限额以授权账号为准。',
        '通用客户端配置：' + json.dumps(config, ensure_ascii=False, separators=(',', ':')),
        '若客户端使用 Token，请在客户端私密配置中设置 Authorization: Bearer <token>。',
        '不要在游戏聊天中发送密码或 Token。',
        '项目与文档：https://github.com/EnernalIliary/Mlogent',
    ])


def install_script(endpoint=DEFAULT_ENDPOINT):
    encoded = base64.b64encode(guide_text(endpoint).encode('utf-8')).decode('ascii')
    return r"""
(function(){
 var mlogentGuideRootRef=this;
 mlogentGuideRootRef._mcpGuide={text:new java.lang.String(java.util.Base64.getDecoder().decode('ENCODED'),'UTF-8'),url:HOME_URL};
 mlogentGuideRootRef._mcpGuide.open=function(player){
  if(player!=null&&player.con!=null)Call.openURI(player.con,String(mlogentGuideRootRef._mcpGuide.url));
 };
 var runner=new JavaAdapter(Packages.arc.util.CommandHandler$CommandRunner,{
  accept:function(args,player){
   if(player!=null)mlogentGuideRootRef._mcpGuide.open(player);
   else Packages.arc.util.Log.info(String(mlogentGuideRootRef._mcpGuide.text));
  }
 });
 var client=Vars.netServer.clientCommands;
 client.removeCommand('mcp');client.register('mcp','','查看 Mlogent MCP 接入与授权指南',runner);
 // Optional fallback for chat pipelines which run filters before commands.
 // Native/Wayzer command routing may bypass this; registration remains primary.
 // Insert before the legacy text-only filter on already-running worlds.
 // Keep other plugins' filters intact and install this hook only once.
 if(!mlogentGuideRootRef._mlogentGuideLinkHook){
  var linkFilter=new JavaAdapter(Packages.mindustry.net.Administration$ChatFilter,{
   filter:function(player,message){
    if(String(message).trim()!=='/mcp')return message;
    mlogentGuideRootRef._mcpGuide.open(player);return null;
   }
  });
  Vars.netServer.admins.chatFilters.insert(0,linkFilter);
  mlogentGuideRootRef._mlogentGuideLinkHook=linkFilter;
 }
 var listeners=Core.app.getListeners(),consoleInstalled=false;
 for(var i=0;i<listeners.size;i++){
  var control=listeners.get(i);
  if(control instanceof Packages.mindustry.server.ServerControl){
   control.handler.removeCommand('mcp');
   control.handler.removeCommand('mcpguide');
   // Wayzer merges console names after client names. Sharing "mcp" shadows
   // the public client command with a console-only command.
   control.handler.register('mcpguide','','Print Mlogent MCP connection instructions',runner);
   consoleInstalled=true;
  }
 }
 sb.append(JSON.stringify({installed:true,client:true,console:consoleInstalled,action:'open-uri-confirm',url:String(mlogentGuideRootRef._mcpGuide.url)}));
})();
""".replace('ENCODED', encoded).replace('HOME_URL', json.dumps(DEFAULT_HOME))


GAME_INSTALL = install_script(os.environ.get('MLOG_MCP_PUBLIC_URL', DEFAULT_ENDPOINT))
