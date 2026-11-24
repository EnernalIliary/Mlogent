"""Native private-push identity, persistence, retry and MCP adapter contracts."""
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from game_push_reply import installation
from world_push_reply import reply, action

class PushTests(unittest.TestCase):
    def test_private_reply_and_action_validate_ids_before_transport(self):
        client=Mock()
        for args in ({'reply_id':'bad','text':'reply'},{'reply_id':'a'*32,'text':' '}):
            with self.assertRaises(ValueError):reply(client,args)
        with self.assertRaises(ValueError):action(client,{'reply_id':'a'*32,'action':'spawn_units','unit':'dagger','count':True})
        client.call.assert_not_called()
        client.call.return_value={'ok':True,'lines':['sent']}
        self.assertEqual(reply(client,{'reply_id':'a'*32,'text':'中文 [red] 私信'})['status'],'sent')
        self.assertNotIn('中文',client.call.call_args.args[0]['code'])

    def test_native_handler_is_private_bound_and_reinstalled_without_duplicate_filters(self):
        script=r'''
const vm=require('node:vm'),assert=require('node:assert/strict');
const source=JSON.parse(require('node:fs').readFileSync(0,'utf8'));
const files={},messages=[],commands={},filters=[];let uuid=0,failed=false;
function File(a,b){this.path=b===undefined?String(a):a.path+'/'+b;}
File.prototype.isDirectory=()=>true;File.prototype.mkdirs=()=>true;
File.prototype.delete=function(){delete files[this.path]};
File.prototype.renameTo=function(target){files[target.path]=files[this.path];delete files[this.path];return true;};
function Writer(file){this.path=file.path||String(file)}
Writer.prototype.println=function(text){files[this.path]=text};Writer.prototype.close=function(){};Writer.prototype.checkError=()=>failed;
const ctx={_pushlog:[],sb:{append(){}},java:{lang:{System:{currentTimeMillis:()=>100000}},
util:{UUID:{randomUUID:()=>({toString:()=>String(++uuid).padStart(32,'a')})}},io:{File,FileWriter:File,PrintWriter:Writer}},
JavaAdapter:function(type,object){return object},Packages:{arc:{util:{CommandHandler$CommandRunner:{}}},mindustry:{net:{Administration$ChatFilter:{}}}},
Vars:{state:{tick:12},netServer:{clientCommands:{removeCommand(){},register:(name,args,description,runner)=>commands[name]=runner},admins:{chatFilters:{insert:(n,f)=>filters.splice(n,0,f)}}}}};
vm.createContext(ctx);vm.runInContext(source,ctx);vm.runInContext(source,ctx);
assert.equal(filters.length,1);
const connection={equals(other){return this===other}};
const player={admin:true,con:connection,isAdded:()=>true,plainName:()=> 'tester',sendMessage:text=>messages.push(text)};
assert.equal(filters[0].filter(player,'/push private request'),null);
const path=Object.keys(files).find(p=>p.endsWith('.json')),row=JSON.parse(files[path]);
assert.equal(row.message,'private request');assert.equal(row.reply_id.length,32);
assert.ok(messages.at(-1).includes('Agent'));assert.equal(ctx._pushlog.length,1);
assert.equal(ctx._iliaryPushReply(row.reply_id,'private response'),'sent');
const count=messages.length;assert.equal(ctx._iliaryPushReply(row.reply_id,'duplicate'),'sent');assert.equal(messages.length,count);
commands.push.accept(['next'],player);const second=JSON.parse(files[Object.keys(files).filter(p=>p.endsWith('.json')).at(-1)]);
player.con={equals(){return false}};assert.equal(ctx._iliaryPushReply(second.reply_id,'wrong connection'),'offline');
player.admin=false;const queued=ctx._pushlog.length;commands.push.accept(['unauthorized'],player);assert.equal(ctx._pushlog.length,queued);
player.admin=true;failed=true;commands.push.accept(['disk failure'],player);assert.equal(ctx._pushlog.length,queued);assert.ok(messages.at(-1).includes('unavailable'));
assert.equal(filters[0].filter(player,'normal chat'),'normal chat');
'''
        result=subprocess.run(['node','-e',script],input=json.dumps(installation('/tmp/push.jsonl')),text=True,capture_output=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

if __name__=='__main__':unittest.main()
