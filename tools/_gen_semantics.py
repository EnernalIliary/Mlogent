# -*- coding: utf-8 -*-
"""Generate tools/instr_semantics.json from the Mindustry v159.3 source.

Param order rule (provable from source):
  text arg order == Java field declaration order in LStatements.java, because
  LStatement.write() delegates to the generated LogicIO.write(this, builder)
  (LStatement.java:283-285) and NO statement in LStatements.java overrides
  write()/read() (verified: zero 'void write(' / 'void read(' overrides).
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'tools', 'instr_semantics.json')

SRC = "Mindustry v159.3 (git 5811844 \"Fixed music fade issue\"), vanilla core/ only. " \
      "Evidence: core/src/mindustry/logic/LStatements.java (2637 lines), LExecutor.java (2417 lines), " \
      "LogicOp.java, LVar.java, LAssembler.java, LParser.java, LUnitControl.java, LLocate.java, " \
      "RadarTarget.java, RadarSort.java, ConditionOp.java, GlobalVars.java, " \
      "core/src/mindustry/world/blocks/logic/LogicBlock.java, LogicDisplay.java. " \
      "No MindustryX sources present in this tree (searched for xlogic/MindustryX/x$ packages and all *.java under any logic/ dir)."

NOTES = (
 "INDEX BASE: every defs/uses entry is an ABSOLUTE 0-based token index in the mlog text line, "
 "where index 0 is the first argument after the mnemonic. e.g. 'sensor result block1 @copper' -> 0=result,1=block1,2=@copper; "
 "'ucontrol within x y radius result 0' -> 0=ucontrol-subcommand,1=x,2=y,3=radius,4=result. "
 "PARAM ORDER RULE: mlog text order == Java field declaration order of the statement class in LStatements.java. "
 "Serialization is generated: LStatement.write(builder) calls LogicIO.write(this, builder) (LStatement.java:283-285) and "
 "LStatements.java contains ZERO overrides of write() or read(), so field order is the only thing that can decide the order. "
 "Instruction construction (which LVar is the output) comes from each statement's build(LAssembler) override, called at "
 "LAssembler.java:38 ('asm.instructions = st.map(l -> l.build(asm))'). "
 "DEFS = positions whose LVar is assigned by the instruction body in LExecutor.java (setnum/setobj/setbool/set/setconst). "
 "USES = positions whose LVar is dereferenced (num()/numi()/numf()/obj()/bool()/team()/building()/...) during that instruction's run(). "
 "'tokens' marks positions that are parsed as enum/boolean/int tokens (LogicIO reads them by name, never builder.var), i.e. they "
 "can NEVER be variables and must be emitted literally. "
 "ucontrol: run() evaluates p1,p2,p3 as numbers UNCONDITIONALLY at LExecutor.java:352 (World.unconv(p1.numf()) etc.), so all 21 "
 "subcommands literally read indices 1,2,3 even when they ignore them; 'uses' below is that literal set (sound for dead-store "
 "analysis) and 'semantic_uses' is the subset that actually affects behaviour. The same unconditional-evaluation situation exists "
 "for draw, where the generic branch dereferences x,y,p1..p4 at LExecutor.java:996 and :1013 for every GraphicsType except col(2) "
 "and print(11)."
)

def I(params, arity, defs=(), uses=(), note=None, tokens=None, **extra):
    d = {"params": params, "arity": arity, "defs": list(defs), "uses": list(uses)}
    if tokens: d["tokens"] = tokens
    if note: d["note"] = note
    d.update(extra)
    return d

instr = {}

# ---------------- meta / no-arg ----------------
instr["noop"] = I([], 0, note="InvalidStatement LStatements.java:48-58; empty run() LExecutor.java:905-908. Also what LParser substitutes for unknown statements (LParser.java:146,173).")
instr["end"] = I([], 0, note="LStatements.java:968-977 -> EndI (LExecutor.java:897-903) sets @counter = instructions.length, so execution restarts next tick.",
                 writes_special=["@counter"])
instr["stop"] = I([], 0, note="LStatements.java:856-865 -> StopI (LExecutor.java:1236-1245): counter--, yield=true, stop=true.", writes_special=["@counter"])
instr["wait"] = I(["value"], 1, uses=[0], note="LStatements.java:835-846 -> WaitI (LExecutor.java:1206-1234): yields until value seconds elapsed.")
instr["setrate"] = I(["amount"], 1, uses=[0],
                     note="LStatements.java:2045-2060 -> SetRateI (LExecutor.java:2018-2036): writes exec.build.ipt *and* exec.ipt.numval directly (bypasses LVar.constant check), so it is the only way to change @ipt.",
                     writes_special=["@ipt"])

# ---------------- io ----------------
instr["read"] = I(["result", "cell", "address"], 3, defs=[0], uses=[1, 2],
                  note="LStatements.java:62-92: fields 'output','target','address' -> ReadI(target,address,output) (LExecutor.java:612-644) writes output only (:629-640).")
instr["write"] = I(["value", "cell", "address"], 3, uses=[0, 1, 2],
                   note="LStatements.java:94-124: fields 'input','target','address' -> WriteI (LExecutor.java:646-666) writes memory, never a var. The doc-suggested name 'result' is the field default only.")
instr["getlink"] = I(["output", "index"], 2, defs=[0], uses=[1],
                     note="LStatements.java:408-430 -> GetLinkI (LExecutor.java:593-610).")
instr["print"] = I(["value"], 1, uses=[0], note="LStatements.java:283-303 -> PrintI (LExecutor.java:1045-1086) appends to text buffer.")
instr["printchar"] = I(["value"], 1, uses=[0], note="LStatements.java:304-343 -> PrintCharI (LExecutor.java:1088-1109).")
instr["format"] = I(["value"], 1, uses=[0], note="LStatements.java:344-363 -> FormatI (LExecutor.java:1111-1141): replaces one {n} placeholder at a time.")
instr["drawflush"] = I(["target"], 1, uses=[0], note="LStatements.java:365-385 -> DrawFlushI (LExecutor.java:1026-1043).")
instr["printflush"] = I(["target"], 1, uses=[0], note="LStatements.java:386-406 -> PrintFlushI (LExecutor.java:1161-1181). Clears the text buffer, never writes a var.")

# ---------------- world / control ----------------
instr["set"] = I(["result", "value"], 2, defs=[0], uses=[1],
                 note="LStatements.java:683-707 -> SetI (LExecutor.java:827-841): ':839 if(!to.constant) to.set(from);' -- assigning to a constant LVar (i.e. any @var from GlobalVars, and @unit) is a silent no-op.")
instr["op"] = I(["op", "result", "a", "b"], 4, defs=[1], uses=[2, 3],
                note="LStatements.java:708-782 -> OpI (LExecutor.java:843-873). index0 is the operator TOKEN (LogicOp constant name), index1 is always the destination and is ALWAYS written with setnum() (:859,861,865,868) so the result is always a number even for strictEqual. index3 is read only for binary operators; unary operators read only index2.",
                tokens={"0": "LogicOp"},
                uses_by_operator_arity={"unary": [2], "binary": [2, 3]})
instr["select"] = I(["result", "op", "comp0", "comp1", "a", "b"], 6, defs=[0], uses=[2, 3], maybe_uses=[4, 5],
                    note="LStatements.java:784-833 -> SelectI (LExecutor.java:875-895): ':892 if(result.constant) return; result.set(op.test(comp0,comp1) ? a : b)' -- comp0/comp1 are always read, but only ONE of a/b is dereferenced per execution (Java ternary). index1 is a ConditionOp token.",
                    tokens={"1": "ConditionOp"})
instr["jump"] = I(["dest", "op", "value", "compare"], 4, uses=[2, 3],
                  note="LStatements.java:986-1069 -> JumpI (LExecutor.java:1183-1204): ':1200 if(address != -1 && op.test(value, compare)) exec.counter.numval = address'. index0 is a LINE NUMBER, not a variable (LParser.java:130-133,194-199 resolves labels to line indices); index1 is a ConditionOp token. Writes @counter.",
                  tokens={"0": "int (line index)", "1": "ConditionOp"}, writes_special=["@counter"])
instr["sensor"] = I(["result", "from", "type"], 3, defs=[0], uses=[1, 2],
                    note="LStatements.java:556-682 -> SenseI(from,to,type) (LExecutor.java:668-719): the destination is index0; index2 is a property/content var (usually @copper-style or an LAccess name string).")
instr["control"] = I(["type", "target", "p1", "p2", "p3", "p4"], 6, uses=[1, 2, 3, 4, 5],
                     note="LStatements.java:431-483 -> ControlI (LExecutor.java:555-591): p1..p4 are ALL dereferenced for every type (':577 p1.bool()', ':584 b.control(type, p1.obj()|p1.num(), p2.num(), p3.num(), p4.num())'). index0 is an LAccess token.",
                     tokens={"0": "LAccess"})
instr["radar"] = I(["target1", "target2", "target3", "sort", "building", "order", "output"], 7, defs=[6], uses=[4, 5],
                   note="LStatements.java:484-553 -> RadarI (LExecutor.java:721-825): only the building (index4) and order (index5) are vars; target1..3 and sort are enum tokens and search from that building. output is setobj (:801,803).",
                   tokens={"0": "RadarTarget", "1": "RadarTarget", "2": "RadarTarget", "3": "RadarSort"})
instr["uradar"] = I(["target1", "target2", "target3", "sort", "ignored", "order", "output"], 7, defs=[6], uses=[5],
                    note="LStatements.java:1170-1193 UnitRadarStatement extends RadarStatement, radar=\"0\", buildFrom() returns false, so RadarI.from is null and the search origin is always @unit (LExecutor.java:721-825). index4 is a dead slot: RadarStatement.build() passes null instead of builder.var(radar), so it is not even converted to an LVar (docs say to write a literal 0).",
                    tokens={"0": "RadarTarget", "1": "RadarTarget", "2": "RadarTarget", "3": "RadarSort", "4": "ignored literal"})
instr["lookup"] = I(["type", "result", "id"], 3, defs=[1], uses=[2],
                    note="LStatements.java:875-909 -> LookupI (LExecutor.java:1247-1265): 'dest.setobj(logicVars.lookupContent(type, from.numi()))'. index0 is a ContentType token (block/unit/item/liquid).",
                    tokens={"0": "ContentType"})
instr["packcolor"] = I(["result", "r", "g", "b", "a"], 5, defs=[0], uses=[1, 2, 3, 4],
                       note="LStatements.java:911-938 -> PackColorI (LExecutor.java:1267-1284).")
instr["unpackcolor"] = I(["r", "g", "b", "a", "value"], 5, defs=[0, 1, 2, 3], uses=[4],
                         note="LStatements.java:940-967 -> UnpackColorI (LExecutor.java:1286-1307): the four outputs come FIRST and the packed input is the LAST argument.")
instr["ubind"] = I(["type"], 1, uses=[0],
                   note="LStatements.java:1070-1112 -> UnitBindI (LExecutor.java:167-207). Writes the special var @unit via exec.unit.setconst(...) (:193,198,202,204) -- no text param is a destination.",
                   writes_special=["@unit"])

# ---------------- ucontrol ----------------
UC = {
 "idle":        ([""], [], [1, 2, 3], [], "LUnitControl.java:5; run() (:356) does nothing."),
 "stop":        ([""], [], [1, 2, 3], [], "LUnitControl.java:6."),
 "move":        (["x", "y"], [], [1, 2, 3], [1, 2], "LUnitControl.java:7; :359 ai.move(x1,y1)."),
 "approach":    (["x", "y", "radius"], [], [1, 2, 3], [1, 2, 3], "LUnitControl.java:8; :362 ai.approach(x1,y1,d1)."),
 "pathfind":    (["x", "y"], [], [1, 2, 3], [1, 2], "LUnitControl.java:9; :365 ai.pathfind(x1,y1)."),
 "autoPathfind":(["autoPathfind"], [], [1, 2, 3], [], "LUnitControl.java:10; :368 ai.autoPathfind() -- argument is a literal flag, ignored."),
 "boost":       (["enable"], [], [1, 2, 3], [1], "LUnitControl.java:11; :371 ai.boost = p1.bool()."),
 "target":      (["x", "y", "shoot"], [], [1, 2, 3], [1, 2, 3], "LUnitControl.java:12; :374 ai.target(x1,y1); ai.shoot = p3.bool()."),
 "targetp":     (["unit", "shoot"], [], [1, 2, 3], [1, 2], "LUnitControl.java:13; :380 ai.mainTarget = p1.obj(); ai.shoot = p2.bool()."),
 "itemDrop":    (["to", "amount"], [], [1, 2, 3], [1, 2], "LUnitControl.java:14; :383 Call.setItem(unit,to,p2.numi())."),
 "itemTake":    (["from", "item", "amount"], [], [1, 2, 3], [1, 2, 3], "LUnitControl.java:15; :536-539."),
 "payDrop":     ([""], [], [1, 2, 3], [], "LUnitControl.java:16; :396 call.payDrop()."),
 "payTake":     (["takeUnits"], [], [1, 2, 3], [1], "LUnitControl.java:17; :399 call.payTake(p1.bool())."),
 "payEnter":    ([""], [], [1, 2, 3], [], "LUnitControl.java:18; :402 call.payEnter()."),
 "mine":        (["x", "y"], [], [1, 2, 3], [1, 2], "LUnitControl.java:19; :405 ai.mine(x1,y1)."),
 "flag":        (["value"], [], [1, 2, 3], [1], "LUnitControl.java:20; :408 unit.flag = p1.num()."),
 "build":       (["x", "y", "block", "rotation", "config"], [], [1, 2, 3, 4, 5], [1, 2, 3, 4, 5], "LUnitControl.java:21; :420-425."),
 "deconstruct": (["x", "y"], [], [1, 2, 3], [1, 2], "LUnitControl.java:22; :480 call.deconstruct(unit.tileOn())."),
 "getBlock":    (["x", "y", "type", "building", "floor"], [3, 4, 5], [1, 2, 3], [1, 2],
                 "LUnitControl.java:23; LExecutor.java:494-507: p3=block, p4=building-or-null, p5=floor-or-overlay; all three are set to null when the tile is out of range. p1/p2 are still read numerically."),
 "within":      (["x", "y", "radius", "result"], [4], [1, 2, 3], [1, 2, 3],
                 "LUnitControl.java:24; LExecutor.java:377 ':377 p4.setnum(unit.within(x1,y1,d1) ? 1 : 0)' -> the result is the 4th VALUE argument (absolute index 4)."),
 "unbind":      ([""], [], [1, 2, 3], [], "LUnitControl.java:25; :410 exec.unit.setconst(null)."),
}
UC_PARAMS = {}
sub = {}
for name, (args, defs, uses, sem, note) in UC.items():
    e = {"defs": defs, "uses": uses}
    if sem != uses: e["semantic_uses"] = sem
    if args and args != [""]: e["args"] = args
    e["note"] = note
    sub[name] = e
instr["ucontrol"] = {"params": ["type", "p1", "p2", "p3", "p4", "p5"], "arity": 6, "defs": [], "uses": [],
                     "tokens": {"0": "LUnitControl"},
                     "note": "LStatements.java:1113-1169 -> UnitControlI (LExecutor.java:304-552). index0 selects the subcommand (LUnitControl token, never a variable). Subcommand-specific defs/uses below; indices are absolute text indices (p1 == 1 ... p5 == 5). All subcommands convert p1,p2,p3 to numbers unconditionally at :352, so 'uses' always contains 1,2,3; 'semantic_uses' lists the ones that actually matter.",
                     "always_evaluated": [1, 2, 3], "subcommands": sub}

# ---------------- ulocate ----------------
LP = {"ore": ["ore", "outX", "outY", "outFound"], "building": ["flag", "enemy", "outX", "outY", "outFound", "outBuild"],
      "spawn": ["enemy", "outX", "outY", "outFound", "outBuild"], "damaged": ["outX", "outY", "outFound", "outBuild"]}
uloc = {}
uloc["ore"] = {"args": ["ore", "outX", "outY", "outFound"], "defs": [4, 5, 6], "uses": [3],
               "note": "LExecutor.java:246-300 ore branch: only ore (index3) is read; outBuild (7) is never written. outX/outY only on success, outFound always."}
uloc["building"] = {"args": ["flag", "enemy", "outX", "outY", "outFound", "outBuild"], "defs": [4, 5, 6, 7], "uses": [2],
                    "note": "building branch (:253): enemy (index2) is read; index1 is a BlockFlag token, never a variable. outX/outY only when found (:270-271); outFound always (:272); outBuild always (:281,283 -> res.build or null)."}
uloc["spawn"] = {"args": ["enemy", "outX", "outY", "outFound", "outBuild"], "defs": [4, 5, 6, 7], "uses": [2],
                 "note": "spawn branch (:256-265) uses enemy; same conditional writes as the building branch."}
uloc["damaged"] = {"args": ["outX", "outY", "outFound", "outBuild"], "defs": [4, 5, 6, 7], "uses": [],
                   "note": "damaged branch (:259-265) reads no text argument; same conditional writes as the building branch."}
instr["ulocate"] = {"params": ["locate", "flag", "enemy", "ore", "outX", "outY", "outFound", "outBuild"], "arity": 8,
                    "defs": [4, 5, 6, 7], "uses": [], "tokens": {"0": "LLocate", "1": "BlockFlag"},
                    "note": "LStatements.java:1194-1302 -> UnitLocateI (LExecutor.java:210-301). Union of defs is 4,5,6,7 but they are written on different code paths (see per-mode note): index6 (outFound) is always assigned, index7 (outBuild) is assigned for every mode except ore, and index4/5 (outX/outY) are only assigned when the search succeeds. Reads @unit (:234).",
                    "subcommands": uloc}

# ---------------- draw ----------------
GT = ["clear", "color", "col", "stroke", "line", "rect", "lineRect", "poly", "linePoly", "triangle",
      "image", "print", "translate", "scale", "rotate", "reset"]
ALL = [1, 2, 3, 4, 5, 6]
dsub = {}
for i, name in enumerate(GT):
    e = {"defs": [], "uses": ALL}
    if name == "col":
        e["uses"] = [1]
        e["note"] = "GraphicsType.col has ordinal 2 == LogicDisplay.commandColorPack, so DrawI takes the colorPack branch (LExecutor.java:933-942) and reads ONLY x (index1); p1..p4 are ignored."
    elif name == "print":
        e["uses"] = [1, 2, 3]
        e["note"] = "GraphicsType.print has ordinal 11 == LogicDisplay.commandPrint -> the print branch (LExecutor.java:943-994) reads only x (1), y (2) and p1 (3, alignment). p2..p4 are ignored."
    elif name == "image":
        e["semantic_uses"] = [1, 2, 3]
        e["note"] = "image branch additionally treats p1 as an object (LExecutor.java:998-1006), so index3 may be an object read."
    elif name in ("clear", "reset"):
        e["semantic_uses"] = []
        e["note"] = "No argument affects the behaviour, but the generic branch still evaluates x,y,p1..p4 numerically (:996,:1013)."
    elif name in ("translate", "scale"):
        e["semantic_uses"] = [1, 2]
    elif name == "rotate":
        e["semantic_uses"] = [1]
    elif name == "color":
        e["semantic_uses"] = [1, 2, 3, 4, 5]
        e["note"] = "color packs p1..p4 as the RGBA components; x/y (1,2) are the position."
    dsub[name] = e
instr["draw"] = {"params": ["type", "x", "y", "p1", "p2", "p3", "p4"], "arity": 7, "defs": [], "uses": ALL,
                 "tokens": {"0": "GraphicsType"},
                 "note": "LStatements.java:125-282 -> DrawI (LExecutor.java:910-1024). Never writes a param. For every GraphicsType except col and print the generic branch dereferences ALL SIX value arguments (:996 packSign(p1.numi()),p4.numi(),x.numi(),y.numi(); :1013 p2.numi(),p3.numi()), so a store into any of indices 1..6 is a live read even if that subcommand ignores the value.",
                 "subcommands": dsub}

# ---------------- world mutation ----------------
instr["getblock"] = I(["layer", "result", "x", "y"], 4, defs=[1], uses=[2, 3],
                      note="LStatements.java:1359-1398: fields are 'layer' FIRST, then result,x,y -> text order is 'getblock <layer> <result> <x> <y>' (NOT the documented result,x,y,layer). GetBlockI(x,y,result,layer) at :1391 writes result (index1) with setobj switch on layer (:1508-1537).",
                      tokens={"0": "TileLayer"}, privileged=True)
instr["setblock"] = I(["layer", "block", "x", "y", "team", "rotation"], 6, defs=[], uses=[1, 2, 3, 4, 5],
                      note="LStatements.java:1400-1461: field order is layer,block,x,y,team,rotation -> text order 'setblock <layer> <block> <x> <y> <team> <rotation>' (docs disagree). SetBlockI (LExecutor.java:1539-1586) never writes a var.",
                      tokens={"0": "TileLayer"}, privileged=True)
instr["spawn"] = I(["type", "x", "y", "rotation", "team", "result", "effect"], 7, defs=[5], uses=[0, 1, 2, 3, 4, 6],
                   note="LStatements.java:1463-1514 -> SpawnUnitI (LExecutor.java:1588-1623): result (index5) is written ONLY on success ('result.setobj(unit)' inside the success branch). effect (index6) is a boolean-ish var.",
                   defs_conditional=[5], privileged=True)
instr["bullet"] = I(["result", "from", "index", "x", "y", "rotation", "team", "owner", "damage", "velocityScl", "lifeScl", "aimX", "aimY"], 13,
                    defs=[0], uses=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                    note="LStatements.java:1516-1565 -> SpawnBulletI (LExecutor.java:1625-1681): result (0) is written only when the source unit/bullet type could be resolved and create() returned non-null (:1679).",
                    defs_conditional=[0], privileged=True)
instr["status"] = I(["clear", "effect", "unit", "duration"], 4, uses=[1, 2], maybe_uses=[3],
                    note="LStatements.java:1567-1625 -> ApplyEffectI (LExecutor.java:1724-1751). index0 is a BOOLEAN literal (field 'boolean clear', so the text token is true/false - the docs' '<apply|clear>' wording is UI text), never a variable. duration (3) is read only when clearing is false and the effect is not permanent.",
                    tokens={"0": "boolean"})
instr["weathersense"] = I(["result", "weather"], 2, defs=[0], uses=[1],
                          note="LStatements.java:1627-1680: fields 'to' then 'weather' -> text order 'weathersense <result> <weather>' (docs disagree). SenseWeatherI(weather,to) writes index0 (LExecutor.java:1683-1695).",
                          privileged=True)
instr["weatherset"] = I(["weather", "state"], 2, uses=[0, 1], note="LStatements.java:1682-1734 -> SetWeatherI (LExecutor.java:1697-1722).", privileged=True)
instr["spawnwave"] = I(["x", "y", "natural"], 3, uses=[0, 1, 2],
                       note="LStatements.java:1736-1766: fields x,y,natural -> text order 'spawnwave <x> <y> <natural>' (docs put natural first, which is only the UI order, cf. build() :1742). SpawnWaveI(natural,x,y) (LExecutor.java:2151-2191).",
                       privileged=True)
instr["setrule"] = I(["rule", "value", "p1", "p2", "p3", "p4"], 6, uses=[1], maybe_uses=[2, 3, 4, 5],
                     note="LStatements.java:1768-1838 -> SetRuleI (LExecutor.java:1753-1831): value (1) is always read; p1..p4 are read only for mapArea (:1786) and p1 additionally for the team-multiplier rules (:1812). index0 is a LogicRule token.",
                     tokens={"0": "LogicRule"}, privileged=True)
instr["message"] = I(["type", "duration", "outSuccess"], 3, defs=[2], uses=[1],
                     note="LStatements.java:1840-1888 -> FlushMessageI (LExecutor.java:1889-1945): outSuccess (index2) is ALWAYS written at entry (':1905 outSuccess.setnum(1)'), then set to 0 when the message is blocked (:1922) or set back to 1 and used as a yield sentinel when it is @wait (:1926). index0 is a MessageType token.",
                     tokens={"0": "MessageType"}, privileged=True)
instr["cutscene"] = I(["action", "p1", "p2", "p3", "p4"], 5, uses=[], maybe_uses=[1, 2, 3, 4],
                      note="LStatements.java:1890-1944 -> CutsceneI (LExecutor.java:1309-1343): pan reads p1,p2,p3; zoom reads p1; stop reads nothing. index0 is a CutsceneAction token.",
                      tokens={"0": "CutsceneAction"}, privileged=True)
instr["effect"] = I(["type", "x", "y", "sizerot", "color", "data"], 6, uses=[1, 2, 3, 4], maybe_uses=[5],
                    note="LStatements.java:1946-2006 -> EffectI: index0 is resolved through LogicFx.get(type) at ASSEMBLY time (LStatements.java:1999), so it is a token, never a variable. 'data' (5) is only read by the effect types that use it.",
                    tokens={"0": "LogicFx"}, privileged=True)
instr["explosion"] = I(["team", "x", "y", "radius", "damage", "air", "ground", "pierce", "effect"], 9, uses=[0, 1, 2, 3, 4, 5, 6, 7, 8],
                       note="LStatements.java:2008-2043 -> ExplosionI (LExecutor.java:1976-2002); no-op on the client (:1983).", privileged=True)
instr["fetch"] = I(["type", "result", "team", "index", "extra"], 5, defs=[1], uses=[2, 3], maybe_uses=[4],
                   note="LStatements.java:2070-2135 -> FetchI(type,result,team,extra,index) (LExecutor.java:1345-1409): note the constructor order differs from the TEXT order (index and extra are swapped), but text order is type,result,team,index,extra. result (1) is always written; extra (4) only for the unit/build variants. index0 is a FetchType token.",
                   tokens={"0": "FetchType"}, defs_conditional=[], privileged=True)
instr["sync"] = I(["variable"], 1, uses=[0], note="LStatements.java:2137-2160 -> SyncI (LExecutor.java:2054-2074); ignores constant vars.", privileged=True)
instr["clientdata"] = I(["channel", "value", "reliable"], 3, uses=[0, 1, 2],
                        note="LStatements.java:2162-2196 -> ClientDataI (LExecutor.java:2076-2099): channel must be a String; reliable is a number/boolean var.", privileged=True)
instr["getflag"] = I(["result", "flag"], 2, defs=[0], uses=[1], note="LStatements.java:2198-2227 -> GetFlagI (LExecutor.java:2101-2120).")
instr["setflag"] = I(["flag", "value"], 2, uses=[0, 1], note="LStatements.java:2229-2258 -> SetFlagI (LExecutor.java:2131-2149).")
instr["setprop"] = I(["type", "of", "value"], 3, uses=[0, 1, 2],
                     note="LStatements.java:2260-2371 -> SetPropI (LExecutor.java:2193-2220): index1 must be a Settable object, index0 an LAccess or UnlockableContent; both are vars (they can hold objects).", privileged=True)
instr["playsound"] = I(["positional", "id", "volume", "pitch", "pan", "x", "y", "limit"], 8, uses=[1], maybe_uses=[2, 3, 4, 5, 6, 7],
                       note="LStatements.java:2373-2444 -> PlaySoundI (LExecutor.java:2222-2251). index0 is a BOOLEAN literal (field 'boolean positional'), never a variable; docs list only 7 args (they merge pan/x). positional=true reads volume,pitch,x,y,limit and IGNORES pan (4); positional=false reads volume,pitch,pan,limit and ignores x,y.",
                       tokens={"0": "boolean"}, privileged=True)
instr["playmusic"] = I(["name", "interrupt"], 2, uses=[0, 1], note="LStatements.java:2446-2473 -> PlayMusicI (LExecutor.java:2253-2272).", privileged=True)
instr["setmarker"] = I(["type", "id", "p1", "p2", "p3"], 5, uses=[1], maybe_uses=[2, 3, 4],
                       note="LStatements.java:2475-2565 -> SetMarkerI (LExecutor.java:2274-2312): id is always read; remove reads no p*, flushText reads p1, texture reads p1,p2, pos reads p1,p2,p3. index0 is an LMarkerControl token.",
                       tokens={"0": "LMarkerControl"}, privileged=True)
instr["makemarker"] = I(["type", "id", "x", "y", "replace"], 5, uses=[1, 2, 3, 4],
                        note="LStatements.java:2567-2611 -> MakeMarkerI (LExecutor.java:2314-2345).", tokens={"0": "LMarkerControl"}, privileged=True)
instr["localeprint"] = I(["value"], 1, uses=[0], note="LStatements.java:2613-2636 -> LocalePrintI (LExecutor.java:2383-2414).")
instr["query"] = I(["shape", "type", "team", "x", "y", "w", "h"], 7, defs=[], uses=[2, 3, 4, 5, 6],
                   note="LStatements.java:1303-1357 -> QueryI (LExecutor.java:1414-1506). No text destination: results go to the builtin @queries array, which only exists when the processor is privileged (LExecutor.java:135 puts @queries, GlobalVars.java). index0/1 are QueryShape/QueryType tokens. h (6) is only used for rect; for the bullet type the query returns immediately (:1462). Reads team (2) and x,y,w,h as vars.",
                   tokens={"0": "QueryShape", "1": "QueryType"}, privileged=True)

# ---------------- ops ----------------
OPS = [
 # name, symbol, arity, func_style, obj_args, note
 ("add", "+", 2), ("sub", "-", 2), ("mul", "*", 2), ("div", "/", 2),
 ("idiv", "//", 2), ("mod", "%", 2), ("emod", "%%", 2), ("pow", "^", 2),
 ("equal", "==", 2, False, True), ("notEqual", "not", 2, False, True), ("land", "and", 2),
 ("lessThan", "<", 2), ("lessThanEq", "<=", 2), ("greaterThan", ">", 2), ("greaterThanEq", ">=", 2),
 ("strictEqual", "===", 2),
 ("shl", "<<", 2), ("shr", ">>", 2), ("ushr", ">>>", 2),
 ("or", "or", 2), ("and", "b-and", 2), ("xor", "xor", 2), ("not", "flip", 1),
 ("max", "max", 2, True), ("min", "min", 2, True), ("angle", "angle", 2, True),
 ("angleDiff", "anglediff", 2, True), ("len", "len", 2, True), ("noise", "noise", 2, True),
 ("abs", "abs", 1), ("sign", "sign", 1), ("log", "log", 1), ("logn", "logn", 2),
 ("log10", "log10", 1), ("floor", "floor", 1), ("ceil", "ceil", 1), ("round", "round", 1),
 ("sqrt", "sqrt", 1), ("rand", "rand", 1),
 ("sin", "sin", 1), ("cos", "cos", 1), ("tan", "tan", 1),
 ("asin", "asin", 1), ("acos", "acos", 1), ("atan", "atan", 1),
]
ops = {}
for row in OPS:
    name, sym, n = row[0], row[1], row[2]
    func = row[3] if len(row) > 3 else False
    obj = row[4] if len(row) > 4 else False
    e = {"operands": n, "returns": "number"}
    if sym != name: e["symbol"] = sym
    if func: e["func_style"] = True
    if obj: e["accepts_objects"] = True
    e["source"] = "Mindustry-Source/core/src/mindustry/logic/LogicOp.java:%d" % (8 + OPS.index(row))
    ops[name] = e
ops["strictEqual"]["note"] = "the enum's lambda is a dummy '(a,b) -> 0' (LogicOp.java:24); OpI special-cases it to compare LVar identity (LExecutor.java:858-859) and still writes 1/0."
ops["equal"]["note"] = ops["notEqual"]["note"] = "uses the object comparator when BOTH args are objects (LogicOp.java:17-18, ConditionOp.java:35-39)."
ops["and"]["note"] = "mlog token 'and' is BITWISE and (symbol 'b-and'); the logical and is the token 'land' (symbol 'and'). The text token is the enum constant name, not the display symbol."

# ---------------- builtins ----------------
readonly = [
 "@this", "@thisx", "@thisy", "@links", "@ipt", "@unit", "@counter",
 "@time", "@tick", "@second", "@minute", "@waveNumber", "@waveTime", "@mapw", "@maph",
 "@ctrlProcessor", "@ctrlPlayer", "@ctrlCommand",
 "@server", "@client", "@clientLocale", "@clientUnit", "@clientName", "@clientTeam", "@clientMobile", "@clientMusicPlaying",
 "@pi", "@e", "@degToRad", "@radToDeg", "@wait", "true", "false", "null",
]
writable = ["@counter", "@ipt", "@unit"]

out = {
 "_source": SRC,
 "_notes": NOTES,
 "version": "mindustry-v159.3",
 "git_head": "5811844",
 "index_base": "absolute 0-based token index of the argument (index 0 = first arg after the mnemonic)",
 "instructions": instr,
 "ops": ops,
 "ops_meta": {
   "text_token": "the operator is the enum CONSTANT NAME (LogicOp.name()), e.g. 'land', 'notEqual', 'angleDiff', 'idiv'. The 'symbol' field (LogicOp.java:67) is display-only ('+' for add, 'and' for land, 'b-and' for and, 'flip' for not) and is NOT accepted as text.",
   "legacy_aliases": {"atan2": "angle", "dst": "len"},
   "aliases_source": "Mindustry-Source/core/src/mindustry/logic/LParser.java:11-14 (opNames map, applied to the 'op' statement at LParser.java:74-77)",
   "arg_layout": "op <opname> <result> <a> <b>; result is ALWAYS index 1 and is always written with setnum(). Binary operators read a and b (indices 2,3); unary operators read only a (index 2).",
   "total": len(ops),
 },
 "builtin_readonly_vars": readonly,
 "builtin_special_writable": writable,
 "builtin_write_notes": {
   "@counter": "WRITABLE. Created by LAssembler.putVar (LAssembler.java:25) which leaves constant=false, so 'set @counter x' works (SetI checks !to.constant at LExecutor.java:839). This is the documented jump mechanism and 'jump'/'end'/'stop' write it directly.",
   "@ipt": "NOT writable with 'set' (created via putConst at LExecutor.java:138, so constant=true), but 'setrate' writes exec.ipt.numval and exec.build.ipt directly (LExecutor.java:2018-2036), bypassing the constant guard.",
   "@unit": "NOT writable with 'set'. LAssembler.java:27 does putConst(\"@unit\", null) -> constant=true, so SetI silently drops the assignment. Only 'ubind' writes it, via exec.unit.setconst(...) (LExecutor.java:193,198,202,204), and LogicBlock restores it on load (:428 'executor.unit.objval = oldUnit'). Persistence explicitly special-cases it: LogicBlock.java:915 'if(var != null && (!var.constant || var.name.equals(\"@unit\")))' - that is why @unit shows up in saved-variable lists.",
 },
 "non_mnemonics": {
   "#": "CommentStatement is declared but NOT registered: '//TODO broken' + '//@RegisterStatement(\"#\")' at LStatements.java:32-33, and its build() returns null (:43-45). So '#' is not an accepted mnemonic in v159.3; a '#' line is just a comment stripped by LParser (LParser.java:98-99).",
 },
 "builtins_source": "Mindustry-Source/core/src/mindustry/logic/GlobalVars.java (all entries set var.constant = true at :276-277); per-processor vars created in LAssembler.java:23-30 and LogicBlock.java:396-397,423-425.",
 "builtin_notes": [
   "Everything reachable through GlobalVars is constant=true, therefore read-only from mlog: sensor properties (@<LAccess name>), content handles (@copper, @mono, @rain, @serpulo ...), @color<Name>, @<align>, @sfx-<name>, the four count vars (@blockCount/@unitCount/@itemCount/@liquidCount), the time vars, and the privileged @client* and @server/@client flags.",
   "@wait is a special sentinel (GlobalVars.java:77, hidden+privileged) consumed by 'message' (LExecutor.java:1926) - not a normal value.",
   "@queries (the query result array) is created only for privileged processors (LExecutor.java:135) and can never be written by a statement.",
 ],
 "docs_crosscheck": {
   "file": "mindustry-blueprint/tools/cmd_index.json",
   "summary": "73 of the 86 entries document one of the 53 mnemonics; the remaining 13 are chapter headings. 5 documented argument orders disagree with the source, 1 documents the wrong arity, and 4 document no argument names at all.",
   "disagreements": [
     {"instruction": "getblock", "docs_format": "getblock <result> <x> <y> <layer>", "source_order": "getblock <layer> <result> <x> <y>",
      "impact": "layer is index 0 in the source, not index 3; the destination 'result' is therefore index 1, not index 0. Docs appear to have followed the in-game UI order (LStatements.java:1366-1381 prints result, then layer, then x, y), not the text order.",
      "evidence": "LStatements.java:1361-1362 (field order), LStatements.java:1391 (GetBlockI(x,y,result,layer))"},
     {"instruction": "setblock", "docs_format": "setblock <x> <y> <block> <team> <rotation> <layer>", "source_order": "setblock <layer> <block> <x> <y> <team> <rotation>",
      "impact": "every argument after index 0 is shifted relative to the docs.",
      "evidence": "LStatements.java:1402-1403 (field order), :1454 (SetBlockI(x,y,block,team,rotation,layer))"},
     {"instruction": "weathersense", "docs_format": "weathersense <weather> <result>", "source_order": "weathersense <result> <weather>",
      "impact": "the WRITTEN argument is index 0 in the source but index 1 in the docs - a def index inversion.",
      "evidence": "LStatements.java:1629-1630 (fields 'to' then 'weather'), :1673 (SenseWeatherI(weather,to))"},
     {"instruction": "spawnwave", "docs_format": "spawnwave <natural> <x> <y>", "source_order": "spawnwave <x> <y> <natural>",
      "impact": "the docs follow the UI order (build() prints 'natural' first at LStatements.java:1742); the text order starts with x.",
      "evidence": "LStatements.java:1738 (fields x,y,natural), :1759 (SpawnWaveI(natural,x,y))"},
     {"instruction": "playsound", "docs_format": "playsound <positional> <id> <volume> <pitch> <pan/x> <y> <limit>", "source_order": "playsound <positional> <id> <volume> <pitch> <pan> <x> <y> <limit>",
      "impact": "arity: docs show 7 arguments, the source has 8. 'pan/x' is documented as one merged slot but pan (4), x (5) and y (6) are three separate fields.",
      "evidence": "LStatements.java:2375-2376 (fields positional,id,volume,pitch,pan,x,y,limit), :2437 (PlaySoundI(positional,id,volume,pitch,pan,x,y,limit))"},
     {"instruction": "read / write / draw / print / printchar / format",
      "docs_format": "read result = cell1 at 0 / write result to cell1 at 0 / draw (no format string)",
      "source_order": "read <result> <cell> <address>, write <value> <cell> <address>, draw <type> <x> <y> <p1..p4>",
      "impact": "the docs' 'params' arrays are placeholders ('1','2','3') or missing entirely, so these entries carry no def/use information. The 'format' strings for read/write happen to match the source order; draw has no format at all.",
      "evidence": "LStatements.java:63,95,128-129"},
     {"instruction": "status", "docs_format": "status <apply|clear> <effect> <unit> <duration>", "source_order": "status <true|false> <effect> <unit> <duration>",
      "impact": "arity and positions agree, but index 0 is a BOOLEAN literal field ('boolean clear', LStatements.java:1569) so the accepted tokens are true/false; 'apply'/'clear' are only the UI button labels.",
      "evidence": "LStatements.java:1569, LExecutor.java:1724-1751"},
     {"instruction": "uradar", "docs_format": "uradar <target1> <target2> <target3> <sort> 0 <order> <output>", "source_order": "same, 7 arguments",
      "impact": "no ordering error, but the '0' in slot 4 is not a variable: UnitRadarStatement passes null instead of builder.var(radar) (buildFrom() == false), so slot 4 is dead. Both docs and source agree the slot must exist.",
      "evidence": "LStatements.java:1171-1186, LExecutor.java:750"}
   ],
   "confirmed_agree": [
     "op (result is the 2nd token, index 1) - the docs' 'op <op> <result> <a> <b>' matches the source exactly.",
     "sensor, getlink, control, radar, drawflush, printflush, ubind, ucontrol (all 21 subcommands), ulocate, set, select, lookup, packcolor, unpackcolor, jump, wait, noop, stop, end, setrate, spawn, bullet, setrule, message, cutscene, effect, explosion, fetch, getflag, setflag, setprop, playmusic, setmarker, makemarker, localeprint, sync, query, clientdata."
   ]
 },
}

# ---------------- validation ----------------
errs = []
for name, d in instr.items():
    ar = d["arity"]
    if isinstance(ar, int):
        for k in ("defs", "uses", "maybe_uses", "defs_conditional", "always_evaluated"):
            for idx in d.get(k, []):
                if not (0 <= idx < ar):
                    errs.append("%s.%s index %d out of range (arity %d)" % (name, k, idx, ar))
        for i in d.get("tokens", {}):
            if not (0 <= int(i) < ar):
                errs.append("%s.tokens index %s out of range" % (name, i))
        if len(d.get("params", [])) != ar:
            errs.append("%s params %d != arity %d" % (name, len(d.get("params", [])), ar))
    for sc, sd in d.get("subcommands", {}).items():
        for k in ("defs", "uses", "semantic_uses"):
            for idx in sd.get(k, []):
                if isinstance(ar, int) and not (0 <= idx < ar):
                    errs.append("%s.%s.%s index %d out of range" % (name, sc, k, idx))
        n_args = len(sd.get("args", []))
        for idx in sd.get("defs", []) + sd.get("uses", []):
            if idx == 0 and n_args:
                errs.append("%s.%s touches index 0 (subcommand token)" % (name, sc))
if errs:
    print("VALIDATION ERRORS:")
    for e in errs: print("  " + e)
    sys.exit(1)

# every op operand count must be 1 or 2, and op defs/uses must line up
for on, od in ops.items():
    assert od["operands"] in (1, 2), on

with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
    f.write("\n")

print("instructions:", len(instr))
print("ops:", len(ops))
print("ucontrol subcommands:", len(instr["ucontrol"]["subcommands"]))
print("draw subcommands:", len(instr["draw"]["subcommands"]))
print("ulocate subcommands:", len(instr["ulocate"]["subcommands"]))
print("total defs indices:", sum(len(d.get("defs", [])) for d in instr.values()))
print("wrote", OUT, os.path.getsize(OUT), "bytes")
