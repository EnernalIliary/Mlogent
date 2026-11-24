"""The public guide is private to the requesting player and contains no secrets."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from world_mcp_guide import DEFAULT_ENDPOINT, DEFAULT_HOME, guide_text, install_script


class GuideTests(unittest.TestCase):
    def test_https_endpoint_and_public_instructions(self):
        text = guide_text()
        self.assertIn(DEFAULT_ENDPOINT, text)
        self.assertIn(DEFAULT_HOME, text)
        self.assertIn('OAuth 2.1', text)
        config = next(line.split('：', 1)[1] for line in text.splitlines() if line.startswith('通用客户端配置：'))
        self.assertEqual(json.loads(config)['mcpServers']['mlogent']['url'], DEFAULT_ENDPOINT)
        for url in ['http://example.com/mcp', 'https://user:secret@example.com/mcp',
                    'https://example.com/mcp?token=secret', 'https://example.com/mcp#secret',
                    'https://example.com/\nsecret']:
            with self.assertRaises(ValueError):
                guide_text(url)

    def test_idempotent_private_player_and_console_commands(self):
        harness = r"""
const vm=require('node:vm'),assert=require('node:assert/strict');
const source=JSON.parse(require('node:fs').readFileSync(0,'utf8'));
function handler(){return {commands:{},removeCommand(n){delete this.commands[n];},
 register(n,p,d,r){this.commands[n]=r;}};}
const client=handler(),messages=[],logs=[],filters=[],opened=[];
// Simulate the old live-world fallback; the new hook must precede it.
filters.push({filter(player,message){return message;}});
class ServerControl{constructor(){this.handler=handler();}}
const control=new ServerControl(),list=[{},control];
const ctx={JavaAdapter:function(t,o){return o;},sb:{append(){}},
 Call:{openURI:(connection,url)=>opened.push({connection,url})},
 java:{lang:{String:function(b){return new String(b.toString('utf8'));}},util:{Base64:{getDecoder:()=>({decode:s=>Buffer.from(s,'base64')})}}},
 Packages:{arc:{util:{CommandHandler$CommandRunner:class{},Log:{info:s=>logs.push(s)}}},mindustry:{net:{Administration$ChatFilter:class{}},server:{ServerControl}}},
 Vars:{netServer:{clientCommands:client,admins:{chatFilters:{insert:(i,f)=>filters.splice(i,0,f)}}}},Core:{app:{getListeners:()=>({size:list.length,get:i=>list[i]})}}};
vm.createContext(ctx);vm.runInContext(source,ctx);vm.runInContext(source,ctx);
assert.deepEqual(Object.keys(client.commands),['mcp']);
assert.deepEqual(Object.keys(control.handler.commands),['mcpguide']);
// Mirror Wayzer's client+console merge: console must not shadow /mcp.
const merged={...client.commands,...control.handler.commands};
assert.equal(merged.mcp,client.commands.mcp);
const connection={id:'requesting-player'};
client.commands.mcp.accept([],{con:connection,sendMessage:s=>messages.push(s)});
assert.equal(messages.length,0);assert.equal(logs.length,0);
assert.equal(opened.length,1);assert.equal(opened[0].connection,connection);
assert.equal(opened[0].url,'https://mcp.iliary.life/');
control.handler.commands.mcpguide.accept([],null);
assert.equal(messages.length,0);assert.equal(logs.length,1);
assert.ok(logs[0].includes('https://mcp.iliary.life/mcp'));
ctx.root={packet:true};assert.equal(filters.length,2);
assert.equal(filters[0].filter({con:connection,sendMessage:s=>messages.push(s)},'/mcp'),null);
assert.equal(messages.length,0);assert.equal(opened.length,2);
assert.equal(opened[1].connection,connection);assert.equal(opened[1].url,'https://mcp.iliary.life/');
assert.equal(filters[0].filter({},'/maps'),'/maps');
"""
        result = subprocess.run(['node', '-e', harness], input=json.dumps(install_script()),
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
