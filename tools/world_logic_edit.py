"""Read and edit one live processor with a compare-and-swap revision."""

import base64
import json
import re
import uuid
from pathlib import Path

from native_mlog import COMPILE_JS

_REVISION = re.compile(r"[0-9a-f]{64}")
_SNAPSHOT = re.compile(r"[0-9a-f]{32}")


def _coords(value):
    return all(type(value.get(axis)) is int and 0 <= value[axis] <= 32767 for axis in ("x", "y"))


def _link_name(value):
    return isinstance(value, str) and 0 < len(value) <= 128 and value.isprintable()


def _validate_changes(changes):
    if not isinstance(changes, dict) or not changes or changes.keys() - {"add", "remove"}:
        raise ValueError("link_changes must specify add or remove")
    add, remove = changes.get("add", []), changes.get("remove", [])
    if not isinstance(add, list) or not isinstance(remove, list) or not 1 <= len(add) + len(remove) <= 64:
        raise ValueError("link_changes must contain 1 to 64 changes")
    if any(not isinstance(link, dict) or link.keys() - {"x", "y", "name"} or not _coords(link)
           or ("name" in link and not _link_name(link["name"])) for link in add):
        raise ValueError("each added link needs integer x and y and an optional name")
    if not all(_link_name(name) for name in remove) or len(set(remove)) != len(remove):
        raise ValueError("removed link names must be printable and unique")
    return {"add": add, "remove": remove}


def _run(world, request, *, data_dir=None):
    if data_dir is None:
        setup = "var req = " + json.dumps(request, ensure_ascii=True) + ";"
        lines = world.js(setup + _READ_JS + _CALL_JS)
    else:
        # Large source travels through the file channel, not the console command line.
        data = Path(data_dir)
        (data / "logic-revisions").mkdir(exist_ok=True)
        filename = world.put_file(json.dumps(request, ensure_ascii=False), "logic-edit")
        try:
            setup = ("var req = JSON.parse(String(java.nio.file.Files.readString("
                     "java.nio.file.Paths.get(" + json.dumps(filename) + "))));")
            lines = world.js(setup + _READ_JS + COMPILE_JS + _EDIT_JS + _CALL_JS)
        finally:
            (data / filename).unlink(missing_ok=True)
    if len(lines) != 1:
        raise RuntimeError("game did not return a processor response")
    result = json.loads(base64.b64decode(lines[0], validate=True))
    if result.get("ok") and "code" in result:
        _label_source(result)
    return result


def _label_source(state):
    from aigenerated import SignError
    from mlog_labelize import labelize_source

    code = state["code"]
    state["lines"] = len(code.splitlines())
    state["codeLen"] = len(code.encode("utf-8"))
    try:
        state["labelled_code"] = labelize_source(code)[0]
    except (ValueError, SignError) as exc:
        state["label_diagnostic"] = str(exc)


def read(world, request):
    if not _coords(request):
        raise ValueError("processor coordinates must be integers in [0, 32767]")
    return _run(world, {"op": "read", "x": request["x"], "y": request["y"]})


def snapshot(data_dir, snapshot_id):
    if not isinstance(snapshot_id, str) or _SNAPSHOT.fullmatch(snapshot_id) is None:
        raise ValueError("invalid snapshot_id")
    path = Path(data_dir) / "logic-revisions" / (snapshot_id + ".json")
    if not path.is_file():
        return {"ok": False, "error": "Snapshot not found"}
    record = json.loads(path.read_text(encoding="utf-8"))
    before = dict(record.get("before") or {})
    if not isinstance(before.get("code"), str) or not isinstance(before.get("links"), list):
        raise ValueError("snapshot is malformed")
    view = {"snapshot_id": snapshot_id, "x": record.get("x"), "y": record.get("y"),
            "before_revision": record.get("before_revision"),
            "after_revision": record.get("after_revision"), "before": before}
    _label_source(view["before"])
    return {"ok": True, **view}


def edit(world, request, *, audit, data_dir):
    op = request["op"]
    job = {"op": op, "journal": uuid.uuid4().hex}
    if op == "logic_rollback":
        snapshot = request.get("snapshot_id")
        if not isinstance(snapshot, str) or _SNAPSHOT.fullmatch(snapshot) is None:
            raise ValueError("invalid snapshot_id")
        job["snapshot_id"] = snapshot
    else:
        if not _coords(request):
            raise ValueError("processor coordinates must be integers in [0, 32767]")
        revision = request.get("expected_revision")
        if not isinstance(revision, str) or _REVISION.fullmatch(revision) is None:
            raise ValueError("expected_revision from world_logic_code is required")
        job.update(x=request["x"], y=request["y"], expected_revision=revision)
        if "code" in request:
            code = request["code"]
            if not isinstance(code, str) or len(code.encode("utf-8")) > 100 * 1024:
                raise ValueError("code must be UTF-8 Mlog of at most 100 KiB")
            job["code"] = code
        if "link_changes" in request:
            job["link_changes"] = _validate_changes(request["link_changes"])
        if "code" not in job and "link_changes" not in job:
            raise ValueError("supply code or link_changes")
    result = _run(world, job, data_dir=data_dir)
    audit(op, x=result.get("x", job.get("x")), y=result.get("y", job.get("y")),
          ok=result.get("ok"), snapshot_id=result.get("snapshot_id"),
          source_sha256=result.get("source_sha256"), links_sha256=result.get("links_sha256"))
    return result


def batch_preview(world, request, *, data_dir):
    processors = request.get("processors") if isinstance(request, dict) else None
    if not isinstance(processors, list) or not 1 <= len(processors) <= 32:
        raise ValueError("processors must contain 1 to 32 entries")
    checked = []
    for item in processors:
        if not isinstance(item, dict) or not _coords(item):
            raise ValueError("each processor needs integer x and y")
        revision = item.get("expected_revision")
        if not isinstance(revision, str) or _REVISION.fullmatch(revision) is None:
            raise ValueError("each processor needs expected_revision from world_logic_code")
        if "code" not in item and "link_changes" not in item:
            raise ValueError("each processor must supply code or link_changes")
        entry = {"x": item["x"], "y": item["y"], "expected_revision": revision}
        if "code" in item:
            if not isinstance(item["code"], str) or len(item["code"].encode("utf-8")) > 100 * 1024:
                raise ValueError("batch preview code must be UTF-8 Mlog of at most 100 KiB")
            entry["code"] = item["code"]
        if "link_changes" in item:
            entry["link_changes"] = _validate_changes(item["link_changes"])
        checked.append(entry)
    result = _run(world, {"op": "batch_preview", "processors": checked}, data_dir=data_dir)
    for processor in result.get("processors", []):
        if isinstance(processor.get("proposed"), dict):
            _label_source(processor["proposed"])
    return result


def batch_set(world, request, *, audit, data_dir):
    processors = request.get("processors") if isinstance(request, dict) else None
    if not isinstance(processors, list) or not 1 <= len(processors) <= 32:
        raise ValueError("processors must contain 1 to 32 entries")
    checked = []
    for item in processors:
        if not isinstance(item, dict) or not _coords(item):
            raise ValueError("each processor needs integer x and y")
        revision = item.get("expected_revision")
        if not isinstance(revision, str) or _REVISION.fullmatch(revision) is None:
            raise ValueError("each processor needs expected_revision from world_logic_code")
        if "code" not in item and "link_changes" not in item:
            raise ValueError("each processor must supply code or link_changes")
        entry = {"x": item["x"], "y": item["y"], "expected_revision": revision}
        if "code" in item:
            if not isinstance(item["code"], str) or len(item["code"].encode("utf-8")) > 100 * 1024:
                raise ValueError("batch set code must be UTF-8 Mlog of at most 100 KiB")
            entry["code"] = item["code"]
        if "link_changes" in item:
            entry["link_changes"] = _validate_changes(item["link_changes"])
        checked.append(entry)
    result = _run(world, {"op": "batch_set", "processors": checked}, data_dir=data_dir)
    audit("logic_batch_set", ok=result.get("ok"), processors=len(checked))
    for processor in result.get("processors", []):
        if isinstance(processor.get("code"), str):
            _label_source(processor)
    return result


_READ_JS = r"""
var world = Vars.world, Logic = Packages.mindustry.world.blocks.logic.LogicBlock;
var Link = Packages.mindustry.world.blocks.logic.LogicBlock$LogicLink;
var utf8 = java.nio.charset.StandardCharsets.UTF_8;
function bytes(text){ return new java.lang.String(String(text)).getBytes(utf8); }
function hash(text){
    var digest = java.security.MessageDigest.getInstance("SHA-256").digest(bytes(text));
    return String(java.util.HexFormat.of().formatHex(digest));
}
function worldBuild(x,y){
    var tile = world.tile(x,y);
    return tile == null ? null : tile.build;
}
function linkTarget(link, b){
    var target = worldBuild(link.x,link.y);
    return target == null ? null : {
        id:target.id, x:target.tileX(), y:target.tileY(),
        block:String(target.block.name), team:String(target.team.name), valid:b.validLink(target)
    };
}
function stateFor(b, code, links){
    var rows = links.map(function(link){
        return {name:link.name, x:link.x, y:link.y, target:linkTarget(link,b)};
    });
    var sourceHash = hash(code), linksHash = hash(JSON.stringify(rows));
    var scope = [java.lang.System.identityHashCode(Vars.state),
                 java.lang.System.identityHashCode(world.tiles), b.id, b.tileX(), b.tileY()];
    return {ok:true, x:b.tileX(), y:b.tileY(), code:code, processor:String(b.block.name),
            ipt:b.executor.ipt == null ? null : b.executor.ipt.numval,
            instructions_per_tick:b.ipt, source_sha256:sourceHash, links_sha256:linksHash,
            revision:hash(JSON.stringify([scope, sourceHash, linksHash])), links:rows};
}
function linksFor(b){
    var links = [];
    for(var i=0;i<b.links.size;i++){
        var link = b.links.get(i);
        links.push({name:String(link.name), x:link.x, y:link.y});
    }
    return links;
}
"""


_EDIT_JS = r"""
function applyChanges(b, rows, changes){
    if(changes == null) return rows;
    var list = rows.slice();
    changes.remove.forEach(function(name){
        var kept = list.filter(function(link){ return link.name !== name; });
        if(kept.length === list.length) throw new Error("Unknown link: " + name);
        list = kept;
    });
    changes.add.forEach(function(link){
        var target = worldBuild(link.x,link.y);
        if(target == null || target.id === b.id || !b.validLink(target)){
            throw new Error("Invalid link target at " + link.x + "," + link.y);
        }
        var x = target.tileX(), y = target.tileY();
        if(list.some(function(l){ var cur = worldBuild(l.x,l.y); return cur != null && cur.id === target.id; })){
            throw new Error("Target is already linked at " + x + "," + y);
        }
        var prefix = String(Logic.getLinkName(target.block)), name = link.name;
        function used(candidate){ return list.some(function(l){ return l.name === candidate; }); }
        if(name == null){
            var number = 1;
            while(used(prefix + number)) number++;
            name = prefix + number;
        }else if(name.indexOf(prefix) !== 0 || !/^[1-9][0-9]{0,3}$/.test(name.slice(prefix.length)) || used(name)){
            throw new Error("Link name must be unused and match " + prefix + " followed by a positive number");
        }
        list.push({name:name, x:x, y:y});
    });
    return list;
}
function configFor(b, code, links){
    var relative = new Packages.arc.struct.Seq(), broadcast = b.block.accessible();
    var seen = Object.create(null);
    links.forEach(function(l){
        var target = worldBuild(l.x,l.y);
        if(target != null){
            if(l.name.indexOf(String(Logic.getLinkName(target.block))) !== 0 || seen[target.id]){
                broadcast = false;
            }
            seen[target.id] = true;
        }
        relative.add(new Link(l.x - b.tileX(),l.y - b.tileY(),l.name,false));
    });
    var packet = Logic.compress(code, relative);
    return {packet:packet, broadcast:broadcast && packet.length <= 16000};
}
function applyConfig(b, code, links, config){
    if(config.broadcast){
        b.configureAny(config.packet);
    }else{
        b.links.clear();
        links.forEach(function(l){ b.links.add(new Link(l.x,l.y,l.name,false)); });
        b.updateCode(code);
    }
}
function releaseUnlinked(b, previous, current){
    var stillLinked = Object.create(null);
    current.forEach(function(link){
        var target = worldBuild(link.x,link.y);
        if(target != null) stillLinked[target.id] = true;
    });
    previous.forEach(function(link){
        var target = worldBuild(link.x,link.y);
        if(target != null && !stillLinked[target.id] && target.block.autoResetEnabled &&
                target.lastDisabler != null && target.lastDisabler.id === b.id){
            target.enabled = true;
        }
    });
}
function journalPath(id){ return "logic-revisions/" + id + ".json"; }
function persist(snapshot, id){
    var file = new java.io.FileOutputStream(journalPath(id || req.journal));
    try{
        file.write(bytes(JSON.stringify(snapshot)));
        file.getFD().sync();
    }finally{
        file.close();
    }
}
function edit(b, before){
    var previous = {code:before.code, links:linksFor(b)};
    var code = typeof req.code === "string" ? req.code : previous.code;
    var links;
    try{
        if(req.op === "logic_rollback"){
            code = req.before.code;
            links = req.before.links;
        }else{
            links = applyChanges(b, previous.links, req.link_changes);
        }
        if(links.length > 6000) throw new Error("Processor exceeds the game link limit");
        if(bytes(code).length > 102400) throw new Error("Code exceeds the game source limit");
        var compile = compileMlog(code,b.block.privileged);
        if(!compile.ok && (req.op !== "logic_rollback" || compile.instructions == null)){
            return {ok:false, error:"Game assembler rejected the source", compile:compile};
        }
        var config = configFor(b, code, links);
        var restore = configFor(b, previous.code, previous.links);
        var intended = stateFor(b,code,links);
        persist({x:before.x, y:before.y, before:previous, before_revision:before.revision,
                 after_revision:intended.revision});
    }catch(e){
        return {ok:false,error:String(e.javaException || e)};
    }
    try{
        applyConfig(b,code,links,config);
        var after = stateFor(b,String(b.code || ""),linksFor(b));
        if(after.revision !== intended.revision || b.executor.instructions.length !== compile.instructions){
            throw new Error("Processor readback differs from the planned configuration");
        }
        after.before_revision = before.revision;
        after.snapshot_id = req.journal;
        after.compile = compile;
        after.broadcast = config.broadcast;
        releaseUnlinked(b,previous.links,links);
        return after;
    }catch(e){
        var restored = false;
        try{
            applyConfig(b,previous.code,previous.links,restore);
            restored = stateFor(b,String(b.code || ""),linksFor(b)).revision === before.revision;
        }catch(ignored){}
        return {ok:false,error:String(e.javaException || e), restored:restored, snapshot_id:req.journal};
    }
}

function batchPlan(item){
    var b=worldBuild(item.x,item.y);
    if(b==null || !(b.block instanceof Logic)) return {ok:false,x:item.x,y:item.y,error:"No logic processor at the requested tile"};
    var before=stateFor(b,String(b.code||""),linksFor(b));
    if(before.revision !== item.expected_revision){
        return {ok:false,x:item.x,y:item.y,conflict:true,revision:before.revision,
                source_sha256:before.source_sha256,links_sha256:before.links_sha256};
    }
    try{
        var code=typeof item.code === "string" ? item.code : before.code;
        var links=applyChanges(b,before.links,item.link_changes);
        var compile=compileMlog(code,b.block.privileged);
        var config=compile.ok ? configFor(b,code,links) : null;
        var proposed=stateFor(b,code,links);
        return {ok:compile.ok,x:item.x,y:item.y,before_revision:before.revision,
                proposed:proposed,compile:compile,broadcast:config==null?false:config.broadcast};
    }catch(e){
        return {ok:false,x:item.x,y:item.y,error:String(e.javaException || e)};
    }
}

function batchPreview(){
    var rows=[], all=true;
    req.processors.forEach(function(item){ var row=batchPlan(item); rows.push(row); if(!row.ok) all=false; });
    return {ok:all,processors:rows};
}

function batchSet(){
    var plans=[], all=true;
    req.processors.forEach(function(item){ var row=batchPlan(item); plans.push(row); if(!row.ok) all=false; });
    if(!all) return {ok:false,preview:plans};
    var applied=[];
    try{
        plans.forEach(function(plan, index){
            var item=req.processors[index], b=worldBuild(plan.x,plan.y);
            var before=stateFor(b,String(b.code||""),linksFor(b));
            var code=plan.proposed.code, links=plan.proposed.links;
            var config=configFor(b,code,links);
            applyConfig(b,code,links,config);
            var after=stateFor(b,String(b.code||""),linksFor(b));
            if(after.revision !== plan.proposed.revision || !after.ok){
                throw new Error("Processor readback differs at " + plan.x + "," + plan.y);
            }
            var snapshotId=String(java.util.UUID.randomUUID()).replace(/-/g,"");
            persist({x:plan.x,y:plan.y,before:{code:before.code,links:before.links},
                     before_revision:before.revision,after_revision:after.revision},snapshotId);
            after.before_revision=before.revision;
            after.snapshot_id=snapshotId;
            after.compile=plan.compile;
            after.broadcast=config.broadcast;
            releaseUnlinked(b,before.links,links);
            applied.push(after);
        });
        return {ok:true,processors:applied};
    }catch(e){
        var restored=true;
        for(var i=applied.length-1;i>=0;i--){
            try{
                var row=applied[i], b=worldBuild(row.x,row.y), old=plans[i].proposed;
                var before=JSON.parse(JSON.stringify(row));
                var original=req.processors[i];
                /* The pre-write state is stored in the snapshot file and is also in the plan's before row. */
                var snapshotPath=journalPath(row.snapshot_id);
                var saved=JSON.parse(String(java.nio.file.Files.readString(java.nio.file.Paths.get(snapshotPath))));
                applyConfig(b,saved.before.code,saved.before.links,configFor(b,saved.before.code,saved.before.links));
            }catch(ignored){ restored=false; }
        }
        return {ok:false,error:String(e.javaException || e),restored:restored,preview:plans};
    }
}
"""


_CALL_JS = r"""
function run(){
    if(req.op === "batch_preview") return batchPreview();
    if(req.op === "batch_set") return batchSet();
    if(req.op === "logic_rollback"){
        var path = java.nio.file.Paths.get(journalPath(req.snapshot_id));
        if(!java.nio.file.Files.exists(path)) return {ok:false,error:"Snapshot not found"};
        var snapshot = JSON.parse(String(java.nio.file.Files.readString(path)));
        req.x = snapshot.x;
        req.y = snapshot.y;
        req.before = snapshot.before;
        req.expected_revision = snapshot.after_revision;
    }
    var b = worldBuild(req.x,req.y);
    if(b == null || !(b.block instanceof Logic)) return {ok:false,error:"No logic processor at the requested tile"};
    var before = stateFor(b,String(b.code || ""),linksFor(b));
    if(req.op === "read") return before;
    if(before.revision !== req.expected_revision){
        return {ok:false,error:"Processor source, links or world changed; re-read before editing",
                conflict:true, revision:before.revision,
                source_sha256:before.source_sha256, links_sha256:before.links_sha256};
    }
    return edit(b,before);
}
sb.append(java.util.Base64.getEncoder().encodeToString(bytes(JSON.stringify(run()))));
"""
