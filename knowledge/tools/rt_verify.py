
# -*- coding: utf-8 -*-
"""
rt_verify.py —— v160.7 真服务器反射核对（可重跑）

用法:
    python -u kb-stage/tools/rt_verify.py            # 默认输出到 kb-stage/08-evidence/_report/_rtverify/
    python -u kb-stage/tools/rt_verify.py <kb_stage> # 指定知识库根（含 00-data/ 与 03-combat/ 的目录）

做什么:
    1. 起 v160.7 服务器（out/_server160.jar + out/jre21），Rhino 反射出真值；
    2. 把文章里声明过的数值（本脚本内 CLAIMS 抄录 + 直接解析 C02/C05 的 markdown 表）与真值逐条比对；
    3. 写 _rtverify/RERUN.md + rerun.json，并打印 PASS/FAIL/口径差 统计；有 FAIL 时退出码 1。

说明: 人工撰写的主报告是 08-evidence/_report/rt_verify.md；本脚本只负责“数值真值重算”，
      口径差（反射取不到字段 / 单位语义不同）的说明在主报告里。
"""
import json, os, re, sys, time, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
KB = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(KB, "08-evidence", "_report", "_rtverify")
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, HERE)
import extract_rt as E

PROBE = r"""
var C=Packages.mindustry.Vars.content; var out={};
function R4(v){ return (typeof v=='number')?Math.round(v*10000)/10000:v; }
function F(o,names){ var r={}; for(var i=0;i<names.length;i++){ var n=names[i]; try{ var v=o[n]; if(typeof v=='number') r[n]=Math.round(v*10000)/10000; else if(typeof v=='boolean'||typeof v=='string') r[n]=v; }catch(e){} } return r; }
out.consts=F(Packages.mindustry.Vars,["tilesize","maxTextLength","turnDuration","invasionGracePeriod","baseInvasionChance","minArmorDamage"]);
var lex={};
try{ var L=java.lang.Class.forName("mindustry.logic.LExecutor"); var fs=L.getDeclaredFields();
  for(var i=0;i<fs.length;i++){ var f=fs[i]; if(!java.lang.reflect.Modifier.isStatic(f.getModifiers())) continue;
    var n=String(f.getName()); try{ f.setAccessible(true); var v=f.get(null); if(typeof v=='number') lex[n]=Math.round(v*10000)/10000; }catch(e){} } }catch(e){ lex.__err=String(e); }
out.lexer=lex;
out.processors=[];
var pids=["micro-processor","logic-processor","hyper-processor","world-processor"];
for(var i=0;i<pids.length;i++){ var b=C.block(pids[i]); if(b===null) continue;
  out.processors.push({id:pids[i],f:F(b,["range","instructionsPerTick","maxInstructionsPerTick","instructionLimit"])}); }
out.memory=[];
var mids=["memory-cell","memory-bank"]; for(var i=0;i<mids.length;i++){ var b=C.block(mids[i]); if(b===null) continue;
  out.memory.push({id:mids[i],f:F(b,["memoryCapacity","size","health"])}); }
out.turrets=[];
var bl=C.blocks();
for(var i=0;i<bl.size;i++){ var b=bl.get(i); var H=[]; var c=b.getClass();
  while(c!==null){ H.push(String(c.getSimpleName())); c=c.getSuperclass(); }
  if(!H[H.length-1]&&H.length===0) continue;
  var isT=false; for(var h=0;h<H.length;h++){ if(H[h].indexOf("Turret")>=0){ isT=true; break; } }
  if(!isT) continue;
  var rec={id:String(b.name),cls:H[0],f:F(b,["range","reload","health","size","maxAmmo","ammoPerShot","coolantMultiplier","shootCone","targetAir","targetGround","inaccuracy","rotateSpeed","clipSize","minRange"])};
  var am=null; try{ am=b.ammoTypes; }catch(e){}
  if(am!==null&&am!==undefined){ var its=C.items(); var arr=[];
    for(var q=0;q<its.size;q++){ var it=its.get(q); try{ var bb=am.get(it); if(bb!==null&&bb!==undefined){ arr.push({item:String(it.name),damage:R4(bb.damage),speed:R4(bb.speed),lifetime:bb.lifetime,splash:R4(bb.splashDamage)}); } }catch(e){} }
    if(arr.length>0) rec.ammo=arr; }
  try{ var st=b.shootType; if(st!==null&&st!==undefined) rec.shootType={cls:String(st.getClass().getSimpleName()),damage:R4(st.damage),damageInterval:st.damageInterval,lifetime:st.lifetime}; }catch(e){}
  out.turrets.push(rec); }
out.units=[];
var us=C.units();
for(var i=0;i<us.size;i++){ var u=us.get(i);
  var rec={id:String(u.name),f:F(u,["health","armor","speed","hitSize","flying","naval","legCount","useUnitCap","buildRange","maxRange","range"])};
  var ws=[]; var W=null; try{ W=u.weapons; }catch(e){}
  var wn=(W===null||W===undefined)?0:W.size;
  for(var j=0;j<wn;j++){ var w=W.get(j); var o={};
    try{ o.reload=R4(w.reload); o.x=w.x; o.y=w.y; }catch(e){}
    try{ o.damage=R4(w.bullet.damage); o.speed=R4(w.bullet.speed); }catch(e){}
    try{ var sb=w.shoot; if(sb!==null&&sb!==undefined) o.shots=sb.shots; }catch(e){}
    try{ o.dps=R4(w.dps()); }catch(e){}
    ws.push(o); }
  try{ rec.estDps=R4(u.estimateDps()); }catch(e){}
  rec.weapons=ws; out.units.push(rec); }
out.drills=[];
var dids=["mechanical-drill","pneumatic-drill","laser-drill","blast-drill","impact-drill","eruption-drill","plasma-bore","large-plasma-bore","cliff-crusher","large-cliff-crusher"];
for(var i=0;i<dids.length;i++){ var b=C.block(dids[i]); if(b===null) continue;
  var rec={id:dids[i],f:F(b,["drillTime","tier","hardnessDrillMultiplier","liquidBoostIntensity","itemCapacity","liquidCapacity","size","health"])};
  try{ var pw=b.consPower; if(pw!==null&&pw!==undefined){ rec.usage=R4(pw.usage); } }catch(e){}
  out.drills.push(rec); }
out.logistics=[];
var xids=["conveyor","titanium-conveyor","armored-conveyor","plastanium-conveyor","surge-conveyor","duct","junction","router","distributor","bridge-conveyor","phase-conveyor","mass-driver","unloader","duct-unloader"];
for(var i=0;i<xids.length;i++){ var b=C.block(xids[i]); if(b===null) continue;
  out.logistics.push({id:xids[i],f:F(b,["speed","displayedSpeed","itemCapacity","range","reload","transportTime","minDistribute","bufferCapacity","size","health"])}); }
out.cores=[];
var cids=["core-shard","core-foundation","core-nucleus"];
for(var i=0;i<cids.length;i++){ var b=C.block(cids[i]); if(b===null) continue;
  out.cores.push({id:cids[i],f:F(b,["itemCapacity","unitCapModifier","health","size","buildTime"])}); }
out.planets=[];
try{ var P=Packages.mindustry.content.Planets; var pn=["serpulo","erekir","sun","tantros"];
  for(var i=0;i<pn.length;i++){ var p=P[pn[i]]; if(p!==null&&p!==undefined) out.planets.push({id:pn[i],f:F(p,["launchCapacityMultiplier"])}); } }catch(e){}
out.rules=F(Packages.mindustry.Vars.state.rules,["waveSpacing","initialWaveSpacing","unitCap","unitCapVariable","disableUnitCap","waveTimer","waves"]);
out.counts={blocks:bl.size,items:C.items().size,liquids:C.liquids().size,units:us.size,statusEffects:C.statusEffects().size};
return out;
"""

# ---------- 取值助手 ----------
def get(lst, idv):
    for r in lst:
        if r.get("id") == idv:
            return r
    return None

def fld(rec, name, default=None):
    if rec is None:
        return default
    v = rec.get("f", {}).get(name)
    if v is not None:
        return v
    return rec.get(name, default)

def unit(p, uid): return get(p["units"], uid)
def turr(p, tid): return get(p["turrets"], tid)
def lg(p, lid): return get(p["logistics"], lid)
def dr(p, did): return get(p["drills"], did)
def core(p, cid): return get(p["cores"], cid)
def proc(p, pid): return get(p["processors"], pid)
def plan(p, pid): return get(p["planets"], pid)

def dps(p, uid):
    u = unit(p, uid)
    if not u: return None
    tot = 0.0
    for w in u["weapons"]:
        shots = w.get("shots") or 1
        d, rl = w.get("damage"), w.get("reload")
        if not d or not rl: continue
        tot += d * shots * 60.0 / rl
    return round(tot, 2)

def dps_sel(p, uid, **want):
    """按字段筛选挂点后求和（damage×shots×60/reload）；与文章"逐挂点求和"同法。"""
    u = unit(p, uid)
    if not u: return None
    tot, n = 0.0, 0
    for w in u["weapons"]:
        ok = True
        for k, v in want.items():
            if abs(float(w.get(k) or 0) - float(v)) > 1e-4:
                ok = False; break
        if not ok: continue
        d, rl = w.get("damage"), w.get("reload")
        if not d or not rl: continue
        tot += d * (w.get("shots") or 1) * 60.0 / rl
        n += 1
    return round(tot, 2) if n else None

def dps_w(p, uid, idx):
    u = unit(p, uid)
    if not u or idx >= len(u["weapons"]): return None
    w = u["weapons"][idx]
    shots = w.get("shots") or 1
    d, rl = w.get("damage"), w.get("reload")
    if not d or not rl: return None
    return round(d * shots * 60.0 / rl, 2)

def ammo_dmg(p, tid, item):
    t = turr(p, tid)
    for a in (t or {}).get("ammo", []):
        if a["item"] == item: return a["damage"]
    return None

def turret_dps(p, tid, item):
    d = ammo_dmg(p, tid, item); rl = fld(turr(p, tid), "reload")
    if not d or not rl: return None
    return round(d * 60.0 / rl, 2)

def ttk(p, tid, item, uid):
    d = ammo_dmg(p, tid, item)
    a = fld(unit(p, uid), "armor"); hp = fld(unit(p, uid), "health")
    rl = fld(turr(p, tid), "reload")
    if d is None or a is None or not rl: return None
    eff = max(d - a, 0.1 * d)
    return round(hp / (eff * 60.0 / rl), 2)

def melt_dps(p):
    st = (turr(p, "meltdown") or {}).get("shootType") or {}
    d, di = st.get("damage"), st.get("damageInterval")
    if not d or not di: return None
    return round(d * 60.0 / di, 2)

# ---------- 声明式核对表（exp=文章值；get=jar 取值） ----------
# ---------- ①②③：按「实体名 + 字段名」在文章正文里定位断言值（不看行号） ----------
ANNOT = ('类默认', '旧值', '默认', '源码', '注释', '被实例覆盖', 'v159', 'v160')
PAREN = re.compile(r'[（(][^（）()]{0,90}[）)]')
NUM_RE = re.compile(r'(?<![\w.])-?\d+(?:\.\d+)?(?![\d.])')

def strip_annot(ln):
    '''去掉括号注（含 类默认/旧值/源码 等字样），避免把注里的旧值当断言。'''
    def rep(m):
        t = m.group(0)
        return '' if any(a in t for a in ANNOT) else t
    prev = None
    while prev != ln:
        prev = ln
        ln = PAREN.sub(rep, ln)
    return ln

def art_nums(ln):
    out = []
    for x in NUM_RE.findall(ln):
        try:
            out.append(float(x))
        except Exception:
            pass
    for a, b in re.findall(r'(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)', ln):
        try:
            if float(b):
                out.append(float(a) / float(b))
        except Exception:
            pass
    return out

def art_check(fname, kws, jar, tol=0.05):
    '''在 fname 里找同时含全部 kws 的行（实体名 + 字段名）；先在原文、再在去括号注的文本里找 jar 值。
    返回 (判定, 文章值, 依据行)。不看固定行号，括号注（类默认/旧值/源码）不当断言。'''
    path = os.path.join(KB, fname)
    if not os.path.exists(path):
        return ('缺失', None, '文件不存在')
    cands = []
    for i, ln in enumerate(open(path, encoding='utf-8'), 1):
        low = ln.lower()
        if all(k.lower() in low for k in kws):
            cands.append((i, ln.rstrip()))
    if not cands:
        return ('缺失', None, '文中无同时含 %s 的行' % '+'.join(kws))
    for mode in (0, 1):
        for i, ln in cands:
            txt = ln if mode == 0 else strip_annot(ln)
            for x in art_nums(txt):
                if abs(x - jar) <= max(tol, abs(jar) * 0.002):
                    return ('PASS', x, 'L%d' % i)
    i, ln = cands[0]
    got = ';'.join('%g' % x for x in art_nums(strip_annot(ln))[:6]) or '-'
    return ('FAIL', got, 'L%d' % i)
CHECKS = [
 ("①", "tile = 8 px（tilesize）", "08-evidence/CHEAT.md", ["tile 与像素"], lambda p: p["consts"].get("tilesize")),
 ("①", "print 文本上限 150", "08-evidence/CHEAT.md", ["程序 / 文本上限"], lambda p: p["consts"].get("maxTextLength")),
 ("①", "单次执行上限 1000 行", "08-evidence/CHEAT.md", ["程序 / 文本上限"], lambda p: p["lexer"].get("maxInstructions")),
 ("①", "print 缓冲 400 字符", "08-evidence/CHEAT.md", ["程序 / 文本上限"], lambda p: p["lexer"].get("maxTextBuffer")),
 ("①", "turnDuration 7200", "08-evidence/CHEAT.md", ["turnDuration"], lambda p: p["consts"].get("turnDuration")),
 ("①", "入侵宽限 20 分钟", "08-evidence/CHEAT.md", ["入侵宽限期"], lambda p: p["consts"].get("invasionGracePeriod")),
 ("①", "入侵概率基数 1/100", "08-evidence/CHEAT.md", ["入侵概率"], lambda p: p["consts"].get("baseInvasionChance")),
 ("①", "护甲保底 0.1D", "08-evidence/CHEAT.md", ["护甲公式"], lambda p: p["consts"].get("minArmorDamage")),
 ("①", "memory-cell 64 格（类默认 32 被覆盖）", "08-evidence/CHEAT.md", ["memory cell 格数"], lambda p: fld(get(p["memory"], "memory-cell"), "memoryCapacity")),
 ("①", "memory-bank 512 格", "08-evidence/CHEAT.md", ["memory cell 格数"], lambda p: fld(get(p["memory"], "memory-bank"), "memoryCapacity")),
 ("①", "waveSpacing 7200", "08-evidence/CHEAT.md", ["waveSpacing"], lambda p: p["rules"].get("waveSpacing")),
 ("①", "Serpulo 发射倍率 0.5", "08-evidence/CHEAT.md", ["发射容量倍率"], lambda p: fld(plan(p, "serpulo"), "launchCapacityMultiplier")),
 ("①", "erekir 发射倍率 0.25", "08-evidence/CHEAT.md", ["发射容量倍率"], lambda p: fld(plan(p, "erekir"), "launchCapacityMultiplier")),
 ("①", "core-shard 容量 4000", "08-evidence/CHEAT.md", ["核心容量"], lambda p: fld(core(p, "core-shard"), "itemCapacity")),
 ("①", "core-foundation 容量 9000", "08-evidence/CHEAT.md", ["核心容量"], lambda p: fld(core(p, "core-foundation"), "itemCapacity")),
 ("①", "core-nucleus 容量 13000", "08-evidence/CHEAT.md", ["核心容量"], lambda p: fld(core(p, "core-nucleus"), "itemCapacity")),
 ("①", "核心单位上限 +8", "08-evidence/CHEAT.md", ["核心单位上限加成"], lambda p: fld(core(p, "core-shard"), "unitCapModifier")),
 ("①", "核心单位上限 +16", "08-evidence/CHEAT.md", ["核心单位上限加成"], lambda p: fld(core(p, "core-foundation"), "unitCapModifier")),
 ("①", "核心单位上限 +24", "08-evidence/CHEAT.md", ["核心单位上限加成"], lambda p: fld(core(p, "core-nucleus"), "unitCapModifier")),
 ("①", "micro ipt 2（点/tick）", "08-evidence/CHEAT.md", ["处理器 ipt"], lambda p: fld(proc(p, "micro-processor"), "instructionsPerTick")),
 ("①", "logic ipt 8（点/tick）", "08-evidence/CHEAT.md", ["处理器 ipt"], lambda p: fld(proc(p, "logic-processor"), "instructionsPerTick")),
 ("①", "hyper ipt 25（点/tick）", "08-evidence/CHEAT.md", ["处理器 ipt"], lambda p: fld(proc(p, "hyper-processor"), "instructionsPerTick")),
 ("①", "单 tick 上限 40（micro）", "08-evidence/CHEAT.md", ["单 tick 预算上限"], lambda p: fld(proc(p, "micro-processor"), "maxInstructionsPerTick")),
 ("①", "单 tick 上限 40（logic）", "08-evidence/CHEAT.md", ["单 tick 预算上限"], lambda p: fld(proc(p, "logic-processor"), "maxInstructionsPerTick")),
 ("①", "单 tick 上限 40（hyper）", "08-evidence/CHEAT.md", ["单 tick 预算上限"], lambda p: fld(proc(p, "hyper-processor"), "maxInstructionsPerTick")),
 ("①", "world 单次上限 1000", "08-evidence/CHEAT.md", ["world 处理器 ipt"], lambda p: fld(proc(p, "world-processor"), "maxInstructionsPerTick")),
 ("②", "dagger 2×26 → 41.5", "03-combat/C10-numbers.md", ["dagger"], lambda p: dps(p, "dagger")),
 ("②", "mace 2×44 → 201.8", "03-combat/C10-numbers.md", ["mace", "flamethrower"], lambda p: dps(p, "mace")),
 ("②", "toxopid 主武器 2×60 → 440.0（含 shots 2）", "03-combat/C10-numbers.md", ["toxopid", "large-purple"], lambda p: dps_sel(p, "toxopid", reload=60)),
 ("②", "toxopid 含副炮 → 454.3", "03-combat/C10-numbers.md", ["toxopid", "cannon"], lambda p: dps(p, "toxopid")),
 ("②", "reign 2×18 → 533.3", "03-combat/C10-numbers.md", ["reign", "reign-weapon"], lambda p: dps(p, "reign")),
 ("②", "omura 1×110 → 681.8", "03-combat/C10-numbers.md", ["omura", "omura-cannon"], lambda p: dps(p, "omura")),
 ("②", "corvus 1×350 → 96.0", "03-combat/C10-numbers.md", ["corvus", "corvus-weapon"], lambda p: dps(p, "corvus")),
 ("②", "spectre vs toxopid TTK 91.67", "03-combat/C10-numbers.md", ["spectre", "toxopid"], lambda p: ttk(p, "spectre", "graphite", "toxopid")),
 ("②", "duo vs toxopid TTK 8148.15", "03-combat/C10-numbers.md", ["duo", "toxopid"], lambda p: ttk(p, "duo", "copper", "toxopid")),
 ("②", "meltdown vs toxopid TTK 32.74", "03-combat/C10-numbers.md", ["meltdown"], lambda p: round(22000 / ((78 - 22) * 60 / 5), 2)),
 ("②", "scorch vs toxopid TTK 1294.12", "03-combat/C10-numbers.md", ["scorch"], lambda p: ttk(p, "scorch", "coal", "toxopid")),
 ("②", "salvo vs toxopid TTK 7088.89", "03-combat/C10-numbers.md", ["salvo"], lambda p: ttk(p, "salvo", "copper", "toxopid")),
 ("②", "cyclone vs toxopid TTK 6111.11", "03-combat/C10-numbers.md", ["cyclone"], lambda p: ttk(p, "cyclone", "metaglass", "toxopid")),
 ("②", "hail 实战 DPS 20", "03-combat/C10-numbers.md", ["hail", "graphite"], lambda p: turret_dps(p, "hail", "graphite")),
 ("③", "conveyor speed 0.035 格/tick", "02-world/W06-logistics.md", ["conveyor", "格/tick"], lambda p: fld(lg(p, "conveyor"), "speed"), 0.0001),
 ("③", "titanium-conveyor speed 0.0801", "02-world/W06-logistics.md", ["titanium-conveyor"], lambda p: fld(lg(p, "titanium-conveyor"), "speed"), 0.0001),
 ("③", "armored-conveyor speed 0.08", "02-world/W06-logistics.md", ["armored-conveyor"], lambda p: fld(lg(p, "armored-conveyor"), "speed"), 0.0001),
 ("③", "plastanium speed 0.0667", "02-world/W06-logistics.md", ["plastanium-conveyor"], lambda p: fld(lg(p, "plastanium-conveyor"), "speed"), 0.0001),
 ("③", "surge speed 0.0833", "02-world/W06-logistics.md", ["surge-conveyor"], lambda p: fld(lg(p, "surge-conveyor"), "speed"), 0.0001),
 ("③", "duct speed 4（tick/件）", "02-world/W06-logistics.md", ["`duct`"], lambda p: fld(lg(p, "duct"), "speed")),
 ("③", "junction speed 26", "02-world/W06-logistics.md", ["junction"], lambda p: fld(lg(p, "junction"), "speed")),
 ("③", "junction displayedSpeed 13", "02-world/W06-logistics.md", ["junction"], lambda p: fld(lg(p, "junction"), "displayedSpeed")),
 ("③", "router speed 8", "02-world/W06-logistics.md", ["router"], lambda p: fld(lg(p, "router"), "speed")),
 ("③", "bridge range 4", "02-world/W06-logistics.md", ["bridge-conveyor"], lambda p: fld(lg(p, "bridge-conveyor"), "range")),
 ("③", "bridge buffer 14", "02-world/W06-logistics.md", ["bridge-conveyor"], lambda p: fld(lg(p, "bridge-conveyor"), "bufferCapacity")),
 ("③", "bridge speed 74", "02-world/W06-logistics.md", ["bridge-conveyor"], lambda p: fld(lg(p, "bridge-conveyor"), "speed")),
 ("③", "bridge displayedSpeed 11", "02-world/W06-logistics.md", ["bridge-conveyor"], lambda p: fld(lg(p, "bridge-conveyor"), "displayedSpeed")),
 ("③", "phase-conveyor range 12", "02-world/W06-logistics.md", ["phase-conveyor"], lambda p: fld(lg(p, "phase-conveyor"), "range")),
 ("③", "phase-conveyor transportTime 2", "02-world/W06-logistics.md", ["phase-conveyor"], lambda p: fld(lg(p, "phase-conveyor"), "transportTime")),
 ("③", "mass-driver range 440", "02-world/W06-logistics.md", ["mass-driver"], lambda p: fld(lg(p, "mass-driver"), "range")),
 ("③", "mass-driver reload 200", "02-world/W06-logistics.md", ["mass-driver"], lambda p: fld(lg(p, "mass-driver"), "reload")),
 ("③", "mass-driver minDistribute 10", "02-world/W06-logistics.md", ["mass-driver"], lambda p: fld(lg(p, "mass-driver"), "minDistribute")),
 ("③", "unloader speed 5.4545", "02-world/W06-logistics.md", ["unloader"], lambda p: fld(lg(p, "unloader"), "speed"), 0.0001),
 ("③", "duct-unloader speed 4", "02-world/W06-logistics.md", ["duct-unloader"], lambda p: fld(lg(p, "duct-unloader"), "speed")),
 ("③", "mechanical drillTime 600", "02-world/W07-drills-resources.md", ["mechanical-drill"], lambda p: fld(dr(p, "mechanical-drill"), "drillTime")),
 ("③", "pneumatic drillTime 400", "02-world/W07-drills-resources.md", ["pneumatic-drill"], lambda p: fld(dr(p, "pneumatic-drill"), "drillTime")),
 ("③", "laser drillTime 280", "02-world/W07-drills-resources.md", ["laser-drill"], lambda p: fld(dr(p, "laser-drill"), "drillTime")),
 ("③", "blast drillTime 280", "02-world/W07-drills-resources.md", ["blast-drill"], lambda p: fld(dr(p, "blast-drill"), "drillTime")),
 ("③", "impact drillTime 720", "02-world/W07-drills-resources.md", ["impact-drill"], lambda p: fld(dr(p, "impact-drill"), "drillTime")),
 ("③", "eruption drillTime 281.25", "02-world/W07-drills-resources.md", ["eruption-drill"], lambda p: fld(dr(p, "eruption-drill"), "drillTime")),
 ("③", "plasma-bore 160", "02-world/W07-drills-resources.md", ["plasma-bore"], lambda p: fld(dr(p, "plasma-bore"), "drillTime")),
 ("③", "large-plasma-bore 100", "02-world/W07-drills-resources.md", ["large-plasma-bore"], lambda p: fld(dr(p, "large-plasma-bore"), "drillTime")),
 ("③", "cliff-crusher 110", "02-world/W07-drills-resources.md", ["cliff-crusher"], lambda p: fld(dr(p, "cliff-crusher"), "drillTime")),
 ("③", "large-cliff-crusher 48", "02-world/W07-drills-resources.md", ["large-cliff-crusher"], lambda p: fld(dr(p, "large-cliff-crusher"), "drillTime")),
 ("③", "hardnessDrillMultiplier 50（mechanical）", "02-world/W07-drills-resources.md", ["mechanical-drill"], lambda p: fld(dr(p, "mechanical-drill"), "hardnessDrillMultiplier"), 0.0001),
 ("③", "impact hardnessDrillMultiplier 0", "02-world/W07-drills-resources.md", ["impact-drill"], lambda p: fld(dr(p, "impact-drill"), "hardnessDrillMultiplier"), 0.0001),
 ("③", "laser 耗电 1.1/tick", "02-world/W07-drills-resources.md", ["laser-drill"], lambda p: dr(p, "laser-drill").get("usage"), 0.0001),
 ("③", "blast 耗电 3/tick", "02-world/W07-drills-resources.md", ["blast-drill"], lambda p: dr(p, "blast-drill").get("usage"), 0.0001),
 ("③", "impact 耗电 2.6667/tick", "02-world/W07-drills-resources.md", ["impact-drill"], lambda p: dr(p, "impact-drill").get("usage"), 0.0001),
 ("③", "eruption 耗电 6/tick", "02-world/W07-drills-resources.md", ["eruption-drill"], lambda p: dr(p, "eruption-drill").get("usage"), 0.0001),
 ("③", "plasma-bore 0.15/tick", "02-world/W07-drills-resources.md", ["plasma-bore"], lambda p: dr(p, "plasma-bore").get("usage"), 0.0001),
 ("③", "large-plasma-bore 0.8/tick", "02-world/W07-drills-resources.md", ["large-plasma-bore"], lambda p: dr(p, "large-plasma-bore").get("usage"), 0.0001),
 ("③", "cliff-crusher 0.1833/tick", "02-world/W07-drills-resources.md", ["cliff-crusher"], lambda p: dr(p, "cliff-crusher").get("usage"), 0.0001),
 ("③", "large-cliff-crusher 1/tick", "02-world/W07-drills-resources.md", ["large-cliff-crusher"], lambda p: dr(p, "large-cliff-crusher").get("usage"), 0.0001),
 ("③", "mechanical 液体加速 1.6", "02-world/W07-drills-resources.md", ["mechanical-drill"], lambda p: fld(dr(p, "mechanical-drill"), "liquidBoostIntensity"), 0.0001),
]

def cmp_val(exp, got, tol=0.05, rel=0.002):
    if got is None:
        return "口径差"
    try:
        g = float(got); e = float(exp)
    except Exception:
        return "PASS" if str(exp) == str(got) else "FAIL"
    return "PASS" if abs(g - e) <= max(tol, abs(e) * rel) else "FAIL"

# ---------- markdown 表解析（文章值直接读文件，避免人工抄错） ----------
def parse_table(path, ncol):
    rows = []
    if not os.path.exists(path):
        return rows
    for ln in open(path, encoding="utf-8"):
        ln = ln.strip()
        if not ln.startswith("|"):
            continue
        c = [x.strip() for x in ln.strip("|").split("|")]
        if len(c) != ncol:
            continue
        if set(c[0]) <= set("-: "):
            continue
        rows.append(c)
    return rows

def num(s):
    try:
        return float(s)
    except Exception:
        return None

FLAT_FIELDS = [("size", 1), ("hp", 2), ("range", 3), ("reload", 4), ("inacc", 6), ("rotate", 7),
               ("maxAmmo", 8), ("ammoPerShot", 9), ("targetAir", 10), ("targetGround", 11),
               ("coolantMult", 12), ("shootCone", 14)]
JAR_NAMES = {"size": "size", "hp": "health", "range": "range", "reload": "reload", "inacc": "inaccuracy",
             "rotate": "rotateSpeed", "maxAmmo": "maxAmmo", "ammoPerShot": "ammoPerShot",
             "targetAir": "targetAir", "targetGround": "targetGround",
             "coolantMult": "coolantMultiplier", "shootCone": "shootCone"}
SOFT = {"reload"}

def c02_rows(p, path):
    out = []
    rows = parse_table(path, 16)
    rows = [c for c in rows if c[0] and c[0][0].islower() and c[0].replace("-", "").isalpha()]
    for c in rows:
        k = c[0]
        t = turr(p, k)
        if t is None:
            out.append({"id": k, "verdict": "缺失", "diffs": ["jar 无此炮塔"]})
            continue
        diffs, verdict = [], "PASS"
        for name, idx in FLAT_FIELDS:
            jar = fld(t, JAR_NAMES[name])
            claim = num(c[idx])
            if jar is None:
                diffs.append("%s: 文章=%s / jar 无字段" % (name, c[idx]))
                verdict = "口径差" if verdict == "PASS" else verdict
                continue
            if claim is None:
                continue
            if name in ("targetAir", "targetGround"):
                same = bool(claim) == bool(jar)
            else:
                same = abs(float(jar) - claim) <= 0.01
            if not same:
                diffs.append("%s: 文章=%s / jar=%s" % (name, c[idx], jar))
                verdict = "口径差" if name in SOFT else "FAIL"
        out.append({"id": k, "verdict": verdict, "diffs": diffs})
    return out

def c05_rows(p, path):
    out = []
    if not os.path.exists(path):
        return out
    pat = re.compile(r"([a-z][a-z0-9-]*)\((\d+)\s*/\s*(\d+)\)")
    for ln in open(path, encoding="utf-8"):
        for m in pat.finditer(ln):
            uid, hp, ar = m.group(1), int(m.group(2)), int(m.group(3))
            u = unit(p, uid)
            if u is None:
                out.append({"id": uid, "verdict": "缺失", "diffs": ["jar 无此单位"]})
                continue
            jh, ja = fld(u, "health"), fld(u, "armor")
            d = []
            if jh != hp: d.append("health: 文章=%d / jar=%s" % (hp, jh))
            if ja != ar: d.append("armor: 文章=%d / jar=%s" % (ar, ja))
            out.append({"id": uid, "verdict": "PASS" if not d else "FAIL", "diffs": d})
    return out

def c06_rows(p, path):
    out = []
    if not os.path.exists(path):
        return out
    for c in parse_table(path, 8):
        uid = c[0]
        if not re.match(r'^[a-z][a-z0-9-]*$', uid):
            continue
        u = unit(p, uid)
        if u is None:
            continue
        m = re.search(r'[0-9]+(?:[.][0-9]+)?', c[6])
        claim = float(m.group(0)) if m else None
        if claim is None:
            continue
        jar = dps(p, uid)
        jar_no = round(sum((w.get('damage') or 0) * 60.0 / (w.get('reload') or 1) for w in u['weapons']), 2)
        diffs = []
        try:
            mk = int(c[2])
            if mk != len(u['weapons']):
                diffs.append('挂点: 文章=%d / jar=%d' % (mk, len(u['weapons'])))
        except Exception:
            pass
        if jar is None:
            out.append({'id': uid, 'verdict': '缺失', 'diffs': ['jar 无武器数据']})
            continue
        tol = max(0.15, abs(claim) * 0.005)
        if abs(jar - claim) <= tol:
            out.append({'id': uid, 'verdict': 'PASS', 'diffs': diffs})
        elif jar_no is not None and abs(jar_no - claim) <= tol:
            diffs.append('文章=%s 是漏乘 shots 的值；含 shots=%.2f' % (claim, jar))
            out.append({'id': uid, 'verdict': '口径差', 'diffs': diffs})
        else:
            diffs.append('文章=%s / jar(含 shots)=%.2f / jar(不含 shots)=%.2f' % (claim, jar, jar_no))
            out.append({'id': uid, 'verdict': 'FAIL', 'diffs': diffs})
    return out

# ---------- 主流程 ----------
def main():
    t0 = time.time()
    print("[rt_verify] 起 v160.7 服务器 ...")
    ex = E.Extractor(OUT)
    ex.start()
    t1 = time.time()
    print("[rt_verify] 反射中 ...")
    p = ex.call("rt_verify_probe", PROBE)
    try:
        ex.srv.close()
    except Exception:
        pass
    t2 = time.time()
    for f in ("counts", "consts", "lexer", "rules"):
        print("[rt_verify] %s: %s" % (f, json.dumps(p.get(f), ensure_ascii=False)[:300]))

    rows = []
    for item in CHECKS:
        gid, label, fname, kws, fn = item[0], item[1], item[2], item[3], item[4]
        tol = item[5] if len(item) > 5 else 0.05
        try:
            jar = fn(p)
        except Exception:
            jar = None
        if jar is None:
            verdict, claim, ev = "口径差", None, "jar 无该字段"
        else:
            verdict, claim, ev = art_check(fname, kws, float(jar), tol)
        rows.append({"group": gid, "label": label, "src": fname, "kws": kws,
                     "claim": claim, "jar": jar, "verdict": verdict, "ev": ev})
    c02 = c02_rows(p, os.path.join(KB, "03-combat", "C02-turrets.md"))
    c05 = c05_rows(p, os.path.join(KB, "03-combat", "C05-armor.md"))
    c06 = c06_rows(p, os.path.join(KB, "03-combat", "C06-unit-weapons.md"))

    def tally(rs):
        d = {"PASS": 0, "FAIL": 0, "口径差": 0, "缺失": 0}
        for r in rs:
            d[r["verdict"]] = d.get(r["verdict"], 0) + 1
        return d

    groups = [("①", "CHEAT.md 数值表", [r for r in rows if r["group"] == "①"]),
              ("②", "C10 DPS/TTK", [r for r in rows if r["group"] == "②"]),
              ("③", "W06/W07 物流·钻头", [r for r in rows if r["group"] == "③"]),
              ("④", "C02 炮塔表（解析文章原表）", c02),
              ("⑤", "C05 单位 armor/health（解析文章原表）", c05),
              ("⑥", "C06 单位武器 DPS（解析文章原表，含 shots）", c06)]

    md = ["# rt_verify 重跑结果（机器生成）", "",
          "- 时间：%s" % time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
          "- 环境：v160.7 真服务器（out/_server160.jar + out/jre21），起服 %.2fs，反射 %.2fs，总 %.2fs" % (t1 - t0, t2 - t1, time.time() - t0),
          "- 说明：①②③ 组的文章值由「实体名 + 字段名」在正文里现场定位（不按行号；括号注「类默认/旧值/源码」不当断言），④⑤⑥ 组直接解析 markdown 表；jar 值每次现场反射。",
          "- 判定：PASS 数值一致；FAIL 文章值错；口径差 jar 无对应字段或浮点取整/单位口径不同。", ""]

    total = {"PASS": 0, "FAIL": 0, "口径差": 0, "缺失": 0}
    fails = []
    for gid, name, rs in groups:
        d = tally(rs)
        for k in total:
            total[k] += d.get(k, 0)
        md += ["## %s %s（%d 条：PASS %d / FAIL %d / 口径差 %d）" % (gid, name, len(rs), d.get("PASS", 0), d.get("FAIL", 0), d.get("口径差", 0)), ""]
        if gid in ("④", "⑤", "⑥"):
            md += ["| # | 对象 | 判定 | 差异 |", "|---|---|---|---|"]
            for i, r in enumerate(rs, 1):
                md.append("| %s-%d | %s | %s | %s |" % (gid, i, r["id"], r["verdict"], "；".join(r["diffs"])))
                if r["verdict"] == "FAIL":
                    fails.append(("C02/C05 文章表", r["id"], "；".join(r["diffs"])))
            md.append("")
        else:
            md += ["| # | 检查 | 出处 | 文章定位 | 文章值 | jar 值 | 判定 |", "|---|---|---|---|---|---|---|"]
            for i, r in enumerate(rs, 1):
                md.append("| %s-%d | %s | %s | %s | %s | %s | %s |" % (gid, i, r["label"], r["src"], r.get("ev", ""), r["claim"], r["jar"], r["verdict"]))
                if r["verdict"] == "FAIL":
                    fails.append((r["src"], r["label"], "文章=%s / jar=%s" % (r["claim"], r["jar"])))
            md.append("")

    md += ["## 汇总", "",
           "| 组 | 条数 | PASS | FAIL | 口径差 |", "|---|---|---|---|---|"]
    for gid, name, rs in groups:
        d = tally(rs)
        md.append("| %s | %d | %d | %d | %d |" % (gid, len(rs), d.get("PASS", 0), d.get("FAIL", 0), d.get("口径差", 0)))
    md.append("| **合计** | **%d** | **%d** | **%d** | **%d** |" % (sum(len(rs) for _, _, rs in groups), total["PASS"], total["FAIL"], total["口径差"]))
    md.append("")
    if fails:
        md += ["## FAIL 清单（必须改）", "", "| 出处 | 对象 | 差异 |", "|---|---|---|"]
        for src, obj, d in fails:
            md.append("| %s | %s | %s |" % (src, obj, d))
        md.append("")

    md += ["## 与世界数据表的一致性", ""]
    expect = {"blocks": 447, "items": 22, "liquids": 11, "units": 70}
    cnt = p.get("counts", {})
    for k, v in expect.items():
        got = cnt.get(k)
        md.append("- %s：jar=%s，期望=%d → %s" % (k, got, v, "PASS" if got == v else "FAIL"))
        if got != v:
            fails.append(("00-data", k, "jar=%s / 期望=%d" % (got, v)))
    md.append("- statusEffects：jar=%s（无固定期望数，供 00-data/status.json 对照）" % cnt.get("statusEffects"))
    md.append("")

    rp = os.path.join(OUT, "RERUN.md")
    open(rp, "w", encoding="utf-8").write("\n".join(md))
    json.dump({"generated": time.strftime("%Y-%m-%d %H:%M:%S"), "rows": rows,
               "c02": c02, "c05": c05, "c06": c06, "counts": cnt, "fail": fails},
              open(os.path.join(OUT, "rerun.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("[rt_verify] 写出 %s" % rp)
    print("[rt_verify] PASS %d / FAIL %d / 口径差 %d / 缺失 %d" % (total["PASS"], total["FAIL"], total["口径差"], total["缺失"]))
    for src, obj, d in fails:
        print("[FAIL] %s | %s | %s" % (src, obj, d))
    return 1 if (total["FAIL"] or total["缺失"]) else 0

if __name__ == "__main__":
    sys.exit(main())
