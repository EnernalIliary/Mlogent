# -*- coding: utf-8 -*-
"""extract_rt.py -- v160.7 真服务器反射抽取 knowledge/00-data 事实表。

用法:
    python -u kb-stage/tools/extract_rt.py
    python -u kb-stage/tools/extract_rt.py --out <目录> --keep-raw

原理: 用 tools/mlogsim.py 的 Server(官方 v160.7 服务端 jar) 走控制台 js
(Rhino) 反射 Vars.content / Vars.state.rules; 每个抽取段把结果 JSON 直接
FileWriter 落盘(不依赖控制台打印顺序, 单批 <1s), python 侧再裁剪/归一/校验并写表。

约定(见 knowledge/CONVENTIONS.md 第 8 节): 每条记录带 id/name/src/ver;
浮点统一 4 位小数; 功率内部口径 power/tick, 同时给 /s 派生值。
"""
import argparse
import json
import os
import sys
import time

REPO = r"<repo>"
sys.path.insert(0, os.path.join(REPO, "tools"))
import mlogsim as M  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
VER = "v160.7"
SRC_PREFIX = "jar:v160.7#"
EXPECT = {"blocks": 447, "items": 22, "liquids": 11, "units": 70}

JS_LIB = r"""
var CN=function(v){ if(v===null||v===undefined) return null; try{ var c=v.getClass(); if(c.isEnum()) return String(v.name()); }catch(e){} try{ var n=v.name; if(typeof n=='string') return n; }catch(e){} return null; };
var EN=function(v){ try{ var c=v.getClass(); if(c.isEnum()) return String(v.name()); var fs=c.getFields(); for(var i=0;i<fs.length;i++){ var f=fs[i]; if(!java.lang.reflect.Modifier.isStatic(f.getModifiers())) continue; var sv=null; try{ sv=f.get(null); }catch(e){ continue; } if(sv!==null&&v.equals(sv)) return f.getName(); } }catch(e){} return null; };
var R4=function(x){ return Math.round(x*10000)/10000; };
var LEN=function(a){ if(a===null||a===undefined) return 0; try{ var n=a.length; if(typeof n=='number') return n; }catch(e){} try{ var n=a.size; if(typeof n=='number') return n; }catch(e){} return 0; };
var AT=function(a,i){ try{ return a[i]; }catch(e){} try{ return a.get(i); }catch(e){} return null; };
var __setbuf=[];
var __setcons=new JavaAdapter(Packages.arc.func.Cons, { get:function(x){ __setbuf.push(x); } });
var SETLIST=function(set){ __setbuf=[]; try{ if(set!==null&&set!==undefined) set.each(__setcons); }catch(e){} return __setbuf; };
var PRIM=function(v){ if(v===null||v===undefined) return null; var t=typeof v; if(t=='number') return R4(v); if(t=='boolean'||t=='string') return v; return null; };
var Q=function(o,n){ try{ var v=o[n]; if(v===null||v===undefined) return null; var t=typeof v; if(t=='number') return R4(v); if(t=='boolean'||t=='string') return v; var cn=CN(v); if(cn!==null) return cn; var en=EN(v); if(en!==null&&en.length>0) return "enum:"+en; try{ if(v.getClass().isArray()) return "array:"+LEN(v); }catch(e){} return null; }catch(e){ return null; } };
var HIER=function(o){ var a=[]; var c=o.getClass(); while(c!==null){ a.push(String(c.getName())); c=c.getSuperclass(); } return a; };
var HAS=function(a,n){ for(var i=0;i<a.length;i++){ if(a[i]===n) return true; } return false; };
var BID=function(b){ if(b===null||b===undefined) return null; return "b"+String(java.lang.System.identityHashCode(b)); };
var STK=function(a){ var r=[]; var n=LEN(a); for(var i=0;i<n;i++){ var s=AT(a,i); if(s===null) continue; var o={}; try{ o.item=String(s.item.name); }catch(e){ try{ o.liquid=String(s.liquid.name); }catch(e2){ continue; } } try{ o.amount=s.amount; }catch(e){} r.push(o); } return r; };
var CONS=function(c){ var o={cls:String(c.getClass().getSimpleName())}; var fs=c.getClass().getFields();
  for(var i=0;i<fs.length;i++){ var f=fs[i]; if(java.lang.reflect.Modifier.isStatic(f.getModifiers())) continue; var n=f.getName(); var v=null; try{ v=f.get(c); }catch(e){ continue; } if(v===null) continue;
    var p=PRIM(v); if(p!==null){ o[n]=p; continue; }
    var cn=CN(v); if(cn!==null){ o[n]=cn; continue; }
    var tn=String(v.getClass().getName());
    if(tn.indexOf("mindustry.type.ItemStack")>=0||tn.indexOf("mindustry.type.LiquidStack")>=0||tn.indexOf("mindustry.type.Stack")>=0){ o[n]=STK(v); }
  }
  return o; };
var WF=function(p,s){ var f=new java.io.FileWriter(p); f.write(s); f.close(); return true; };
var WFO=function(p,o){ var s=JSON.stringify(o); if(s===undefined||s===null||s==='') s='{"__err":"undefinable result"}'; return WF(p,s); };
"""

def log(*a):
    print(*a, flush=True)

class Extractor:
    def __init__(self, out_dir, keep_raw=False):
        self.out = out_dir
        self.raw_dir = os.path.join(out_dir, "_raw")
        os.makedirs(self.raw_dir, exist_ok=True)
        self.keep_raw = keep_raw
        self.srv = None
        self.stats = {}

    def start(self):
        t = time.time()
        self.srv = M.Server(M._default_java(), M._default_jar())
        log("[rt] server up in %.2fs (jar=%s)" % (time.time() - t, os.path.basename(M._default_jar())))
        got = self.call("counts", """
        var C=Packages.mindustry.Vars.content;
        return {blocks:C.blocks().size, items:C.items().size, liquids:C.liquids().size,
                units:C.units().size, status:C.statusEffects().size};
        """)
        log("[rt] content counts:", got)
        return got

    def call(self, tag, body, timeout=180):
        path = os.path.join(self.raw_dir, tag + ".json").replace("\\", "/")
        if os.path.exists(path):
            os.remove(path)
        code = JS_LIB + " (function(){ try{ var __r=(function(){ %s })(); WFO('%s', __r); } catch(e){ WFO('%s', {__err:String(e)}); } })();" % (
            " ".join(body.split()), path, path)
        t = time.time()
        try:
            self.srv.js(" ".join(code.splitlines()), timeout=timeout)
        except Exception as e:
            log("[rt] %s: console note: %s" % (tag, str(e).split("tail:")[-1][-300:]))
        deadline = time.time() + timeout
        while time.time() < deadline:
            if os.path.exists(path) and os.path.getsize(path) > 1:
                time.sleep(0.05)
                break
            time.sleep(0.1)
        else:
            raise RuntimeError("extract %s: no output file after %.0fs" % (tag, timeout))
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "__err" in data:
            raise RuntimeError("extract %s failed in JS: %s" % (tag, data["__err"]))
        dt = time.time() - t
        n = len(data) if isinstance(data, list) else 1
        log("[rt] %-10s %5d recs  %5.1fs  %.0fKB" % (tag, n, dt, os.path.getsize(path) / 1024))
        self.stats[tag] = {"n": n, "sec": round(dt, 2), "kb": round(os.path.getsize(path) / 1024, 1)}
        return data

    def extract_blocks(self):
        body = r"""
        var C=Packages.mindustry.Vars.content; var bl=C.blocks(); var its=C.items(); var out=[];
        var POOL=["range","minRange","reload","maxAmmo","ammoPerShot","clipSize","shootCone","inaccuracy",
          "rotateSpeed","targetAir","targetGround","targetBlocks","coolantMultiplier","ammoEjectBack","recoil",
          "recoilTime","shootWarmupSpeed","minWarmup","velocityRnd","reloadWhileCharging",
          "drillTime","tier","hardnessDrillMultiplier","liquidBoostIntensity","warmupSpeed",
          "craftTime","dumpTime","ignoreLiquidFullness","dumpExtraLiquid","outputsLiquid",
          "speed","displayedSpeed","pushUnits","isDuct",
          "powerProduction","powerCapacity","explosionRadius","explosionDamage",
          "heatOutput","heatCapacity","liquidPadding","liquidPressure","coreMerge","chanceDeflect","flashHit",
          "buildTime","buildCostMultiplier","conductivePower","insulated","canOverdrive",
          "isLiquid","shallow","speedMultiplier","dragMultiplier","damageTaken","drownTime"];
        for(var i=0;i<bl.size;i++){
          var b=bl.get(i); var o={}; var h=HIER(b);
          o.n=String(b.name); try{ o.loc=String(b.localizedName); }catch(e){ o.loc=null; }
          o.cls=h[0]; o.hier=h;
          o.cat=Q(b,"category"); o.size=Q(b,"size"); o.health=Q(b,"health"); o.armor=Q(b,"armor");
          o.itemCap=Q(b,"itemCapacity"); o.liqCap=Q(b,"liquidCapacity");
          o.hasPower=Q(b,"hasPower"); o.hasItems=Q(b,"hasItems"); o.hasLiquids=Q(b,"hasLiquids");
          o.rotate=Q(b,"rotate"); o.solid=Q(b,"solid"); o.underBullets=Q(b,"underBullets");
          o.vis=Q(b,"buildVisibility"); o.group=Q(b,"group"); o.priv=Q(b,"privileged");
          o.inEditor=Q(b,"inEditor"); o.placeablePlayer=Q(b,"placeablePlayer");
          o.alwaysReplace=Q(b,"alwaysReplace"); o.rebuildable=Q(b,"rebuildable");
          o.unitCapModifier=Q(b,"unitCapModifier");
          o.req=STK(b.requirements);
          var cs=[]; var cn=LEN(b.consumers);
          for(var j=0;j<cn;j++){ try{ cs.push(CONS(AT(b.consumers,j))); }catch(e){} }
          o.cons=cs;
          var p={};
          for(var k=0;k<POOL.length;k++){ var v=Q(b,POOL[k]); if(v!==null&&v!==undefined) p[POOL[k]]=v; }
          try{ var bi=CN(b.blockedItem); if(bi!==null) p.blockedItem=bi; }catch(e){}
          try{ var st=CN(b.status); if(st!==null) p.status=st; }catch(e){}
          try{ var ld=CN(b.liquidDrop); if(ld!==null) p.liquidDrop=ld; }catch(e){}
          try{ var idd=CN(b.itemDrop); if(idd!==null) p.itemDrop=idd; }catch(e){}
          o.p=p;
          o.outs=STK(b.outputItems); o.outl=STK(b.outputLiquids); o.res=STK(b.results);
          var cp=null;
          try{ var cpx=b.consPower;
            if(cpx!==null&&cpx!==undefined){ cp={cls:String(cpx.getClass().getSimpleName())};
              var fs=cpx.getClass().getFields();
              for(var m=0;m<fs.length;m++){ var f=fs[m];
                if(java.lang.reflect.Modifier.isStatic(f.getModifiers())) continue;
                var vv=null; try{ vv=f.get(cpx); }catch(e){ continue; } if(vv===null) continue;
                var pp=PRIM(vv); if(pp!==null) cp[f.getName()]=pp; } } }catch(e){}
          o.cp=cp;
          var am=[];
          for(var k=0;k<its.size;k++){ var it=its.get(k); var bb=null;
            try{ bb=b.ammoTypes.get(it); }catch(e){ bb=null; }
            if(bb!==null&&bb!==undefined){ am.push(String(it.name)+"|"+BID(bb)); } }
          o.ammo=am;
          out.push(o);
        }
        return out;
        """
        return self.call("blocks", body)

    def extract_turrets(self):
        body = r"""
        var C=Packages.mindustry.Vars.content; var bl=C.blocks(); var items=C.items(); var out=[];
        for(var i=0;i<bl.size;i++){
          var b=bl.get(i); var h=HIER(b);
          var isTur=false; var tcls=null;
          for(var q=0;q<h.length;q++){ var hn=h[q]; if(hn.lastIndexOf("Turret")===hn.length-6){ isTur=true; tcls=hn; break; } }
          if(!isTur) continue;
          var o={ n:String(b.name), cls:h[0] };
          o.tclass=tcls; o.kind=String(tcls.split(".").pop()).replace("Turret","").toLowerCase();
          if(o.kind==="") o.kind="base";
          var keys=["range","minRange","reload","maxAmmo","ammoPerShot","clipSize","shootCone","inaccuracy",
            "rotateSpeed","targetAir","targetGround","targetBlocks","coolantMultiplier","ammoEjectBack","recoil",
            "recoilTime","shootWarmupSpeed","minWarmup","velocityRnd","reloadWhileCharging",
            "consumeAmmoOnce","displayAmmoMultiplier","buildTime","itemCapacity","liquidCapacity"];
          for(var k=0;k<keys.length;k++){ var v=Q(b,keys[k]); if(v!==null&&v!==undefined) o[keys[k]]=v; }
          var ammo=[];
          for(var k=0;k<items.size;k++){ var it=items.get(k); var bb=null;
            try{ bb=b.ammoTypes.get(it); }catch(e){ bb=null; }
            if(bb===null||bb===undefined) continue;
            var a={ item:String(it.name), bullet:BID(bb) };
            a.damage=Q(bb,"damage"); a.speed=Q(bb,"speed"); a.lifetime=Q(bb,"lifetime");
            a.ammoMultiplier=Q(bb,"ammoMultiplier"); a.reloadMultiplier=Q(bb,"reloadMultiplier");
            a.status=Q(bb,"status"); a.statusDuration=Q(bb,"statusDuration");
            ammo.push(a);
          }
          o.ammo=ammo;
          var cs=[]; var cn=LEN(b.consumers);
          for(var j=0;j<cn;j++){ try{ cs.push(CONS(AT(b.consumers,j))); }catch(e){} }
          o.cons=cs;
          var cp=null;
          try{ var cpx=b.consPower;
            if(cpx!==null&&cpx!==undefined){ cp={cls:String(cpx.getClass().getSimpleName())};
              var fs=cpx.getClass().getFields();
              for(var m=0;m<fs.length;m++){ var f=fs[m];
                if(java.lang.reflect.Modifier.isStatic(f.getModifiers())) continue;
                var vv=null; try{ vv=f.get(cpx); }catch(e){ continue; } if(vv===null) continue;
                var pp=PRIM(vv); if(pp!==null) cp[f.getName()]=pp; } } }catch(e){}
          o.cp=cp;
          out.push(o);
        }
        return out;
        """
        return self.call("turrets", body)

    def extract_bullets(self):
        body = r"""
        var C=Packages.mindustry.Vars.content; var bl=C.blocks(); var un=C.units(); var items=C.items();
        var seen=new java.util.IdentityHashMap(); var out=[];
        var add=function(bb){
          if(bb===null||bb===undefined) return;
          if(seen.containsKey(bb)) return;
          seen.put(bb,bb);
          var o={ id:BID(bb), cls:String(bb.getClass().getName()) };
          o.cname=String(bb.getClass().getSimpleName());
          var keys=["damage","speed","lifetime","drag","pierce","pierceCap","splashDamage","splashDamageRadius",
                    "splashDamagePierce","lightning","lightningDamage","lightningLength","fragBullets","fragAngle",
                    "fragVelocityMin","fragVelocityMax","fragLifeMin","fragLifeMax","width","height","hitSize",
                    "ammoMultiplier","reloadMultiplier","status","statusDuration","collides","collidesAir",
                    "collidesGround","collidesTiles","absorbable","hittable","keepVelocity","range","maxRange",
                    "hitShake","hitUnder","knockback","reflectable","laserAbsorb","pierceArmor","shrinkX","shrinkY",
                    "buildingDamageMultiplier","intervalBullets","intervalBulletInterval","intervalRandomSpread"];
          for(var i=0;i<keys.length;i++){ var v=Q(bb,keys[i]); if(v!==null&&v!==undefined) o[keys[i]]=v; }
          out.push(o);
        };
        for(var i=0;i<bl.size;i++){
          var b=bl.get(i); var h=HIER(b);
          if(!HAS(h,"mindustry.world.blocks.defense.turrets.Turret")) continue;
          for(var k=0;k<items.size;k++){ var it=items.get(k); var bb=null;
            try{ bb=b.ammoTypes.get(it); }catch(e){ bb=null; }
            if(bb!==null&&bb!==undefined) add(bb);
          }
        }
        for(var i=0;i<un.size;i++){
          var u=un.get(i); var wn=LEN(u.weapons);
          for(var j=0;j<wn;j++){ var w=AT(u.weapons,j); if(w===null) continue; try{ add(w.bullet); }catch(e){} }
        }
        return out;
        """
        return self.call("bullets", body)

    def extract_units(self):
        body = r"""
        var C=Packages.mindustry.Vars.content; var un=C.units(); var out=[];
        for(var i=0;i<un.size;i++){
          var u=un.get(i); var o={ n:String(u.name) };
          try{ o.loc=String(u.localizedName); }catch(e){ o.loc=null; }
          o.cls=String(u.getClass().getName());
          var keys=["health","armor","speed","flying","naval","legCount","hitSize","range","maxRange","itemCapacity",
                    "buildSpeed","mineSpeed","mineTier","mineRange","buildRange","canBoost","boostMultiplier","useUnitCap",
                    "targetPriority","targetAir","targetGround","targetBlocks","drag","accel","rotateSpeed","omniMovement",
                    "faceTarget","payloadCapacity","engineSize","engineOffset","lightRadius","squareShape","hidden",
                    "lowAltitude","canDrown","drownTimeMultiplier","crushDamage","hovering","researchCostMultiplier",
                    "ammoCapacity","clipSize","isEnemy","playerControllable","logicControllable","hittable","targetable"];
          for(var k=0;k<keys.length;k++){ var v=Q(u,keys[k]); if(v!==null&&v!==undefined) o[keys[k]]=v; }
          var ws=[]; var wn=LEN(u.weapons);
          for(var j=0;j<wn;j++){
            var w=AT(u.weapons,j); if(w===null) continue;
            var wo={}; try{ wo.name=String(w.name); }catch(e){ wo.name=null; }
            try{ wo.bullet=BID(w.bullet); }catch(e){ wo.bullet=null; }
            var wk=["reload","x","y","inaccuracy","shootCone","alternate","mirror","rotate","rotateSpeed",
                    "layerOffset","recoil","shootWarmupSpeed","minWarmup","warmupMaintainTime","linearWarmup",
                    "alwaysContinuous","continuous","targetInterval","predictTarget","shootStatus","noAttack","velocityRnd"];
            for(var m=0;m<wk.length;m++){ var vv=Q(w,wk[m]); if(vv!==null&&vv!==undefined) wo[wk[m]]=vv; }
            ws.push(wo);
          }
          o.weapons=ws;
          var ab=[]; var an=LEN(u.abilities);
          for(var j=0;j<an;j++){
            var a=AT(u.abilities,j); if(a===null) continue;
            var ao={cls:String(a.getClass().getSimpleName())};
            var fs=a.getClass().getFields();
            for(var m=0;m<fs.length;m++){
              var f=fs[m]; if(java.lang.reflect.Modifier.isStatic(f.getModifiers())) continue;
              var n=f.getName(); var v=null; try{ v=f.get(a); }catch(e){ continue; } if(v===null) continue;
              var p=PRIM(v); if(p!==null){ ao[n]=p; continue; }
              var cnn=CN(v); if(cnn!==null){ ao[n]=cnn; continue; }
            }
            ab.push(ao);
          }
          o.abilities=ab;
          var im=[]; try{ var fset=u.getClass().getField("immunities").get(u); var sl=SETLIST(fset); for(var j=0;j<sl.length;j++){ im.push(String(sl[j].name)); } }catch(e){}
          o.immunities=im.sort();
          out.push(o);
        }
        return out;
        """
        return self.call("units", body)

    def extract_meta(self):
        body = r"""
        var C=Packages.mindustry.Vars.content; var out={};
        out.items=[];
        var it=C.items();
        for(var i=0;i<it.size;i++){ var x=it.get(i); var o={n:String(x.name)};
          try{ o.loc=String(x.localizedName); }catch(e){ o.loc=null; }
          var keys=["hardness","cost","flammability","explosiveness","radioactivity","charge","lowPriority",
                    "hidden","alwaysUnlocked","healthScaling","buildable"];
          for(var k=0;k<keys.length;k++){ var v=Q(x,keys[k]); if(v!==null&&v!==undefined) o[keys[k]]=v; }
          try{ o.color=x.color==null?null:x.color.rgba(); }catch(e){}
          try{ o.colorHex=String(x.color.toString()); }catch(e){}
          out.items.push(o);
        }
        out.liquids=[];
        var lq=C.liquids();
        for(var i=0;i<lq.size;i++){ var x=lq.get(i); var o={n:String(x.name)};
          try{ o.loc=String(x.localizedName); }catch(e){ o.loc=null; }
          var keys=["viscosity","heatCapacity","temperature","flammability","explosiveness","coolant","gas",
                    "boilPoint","incinerable","particleSpacing","particleSize","vaporPressure","hidden",
                    "capsParticles","blockReactive","canStayOn"];
          for(var k=0;k<keys.length;k++){ var v=Q(x,keys[k]); if(v!==null&&v!==undefined) o[keys[k]]=v; }
          try{ o.effectCls=x.effect==null?null:String(x.effect.getClass().getName()); }catch(e){}
          try{ o.colorHex=String(x.color.toString()); }catch(e){}
          out.liquids.push(o);
        }
        out.status=[];
        var se=C.statusEffects();
        for(var i=0;i<se.size;i++){ var s=se.get(i); var o={n:String(s.name)};
          try{ o.loc=String(s.localizedName); }catch(e){ o.loc=null; }
          var keys=["damageMultiplier","healthMultiplier","speedMultiplier","reloadMultiplier","buildSpeedMultiplier",
                    "dragMultiplier","disarm","transitionDamage","intervalDamage","intervalDamageTime",
                    "intervalDamagePierce","reactive","effectChance","permanent","show","hidden","applyExtend",
                    "parentizeEffect","parentizeApplyEffect"];
          for(var k=0;k<keys.length;k++){ var v=Q(s,keys[k]); if(v!==null&&v!==undefined) o[keys[k]]=v; }
          try{ o.effect=s.effect==null?null:String(s.effect.getClass().getName()); }catch(e){}
          var ops=[]; try{ var fop=s.getClass().getField("opposites").get(s); var so=SETLIST(fop); for(var j=0;j<so.length;j++){ ops.push(String(so[j].name)); } }catch(e){}
          o.opposites=ops.sort();
          var af=[]; try{ var faf=s.getClass().getField("affinities").get(s); var sa=SETLIST(faf); for(var j=0;j<sa.length;j++){ var ae=sa[j]; af.push(String(ae.name)+"+"+String(R4(ae.damage))); } }catch(e){}
          o.affinities=af.sort();
          try{ o.color=s.color==null?null:s.color.rgba(); }catch(e){}
          out.status.push(o);
        }
        return out;
        """
        return self.call("meta", body)

    def extract_rules(self):
        body = r"""
        var R=Packages.mindustry.Vars.state.rules; var out=[];
        var fs=R.getClass().getFields();
        var def=null; try{ var RC=Packages.mindustry.game.Rules; def=new RC(); }catch(e){ def=null; }
        for(var i=0;i<fs.length;i++){
          var f=fs[i];
          if(java.lang.reflect.Modifier.isStatic(f.getModifiers())) continue;
          var o={ name:String(f.getName()), type:String(f.getType().getSimpleName()) };
          try{ var v=f.get(R); var p=PRIM(v);
            if(p!==null){ o.value=p; }
            else { var cn=CN(v); if(cn!==null) o.value=cn; else { o.value=null; try{ o.valueType=String(v.getClass().getName()); }catch(e){} } }
          }catch(e){ o.value=null; }
          if(def!==null){
            try{ var dv=f.get(def); var dp=PRIM(dv);
              if(dp!==null){ o.default=dp; }
              else { var dcn=CN(dv); if(dcn!==null){ o.default=dcn; } else { o.default=null; try{ o.defaultType=String(dv.getClass().getName()); }catch(e){} } }
            }catch(e){ o.default=null; }
          }
          try{ if(f.getType().isArray()) o.array=true; }catch(e){}
          out.push(o);
        }
        return out;
        """
        return self.call("rules", body)

    def close(self):
        if self.srv is not None:
            try:
                self.srv.close()
            except Exception:
                pass
            self.srv = None

def r4(x):
    if isinstance(x, float):
        return round(x, 4)
    return x

def short_cls(full):
    for p in ("mindustry.world.blocks.", "mindustry.content.", "mindustry.entities.bullet.",
              "mindustry.type.", "mindustry.world."):
        if full.startswith(p):
            return full[len(p):]
    return full

def clean(d):
    out = {}
    for k, v in d.items():
        if v is None:
            continue
        if isinstance(v, float):
            v = r4(v)
        if isinstance(v, list):
            v = [clean(x) if isinstance(x, dict) else r4(x) for x in v]
            v = [x for x in v if (isinstance(x, (dict, list)) and len(x) > 0) or isinstance(x, (int, float, str, bool))]
            if not v:
                continue
        if isinstance(v, dict):
            v = clean(v)
            if not v:
                continue
        out[k] = v
    return out

BLOCK_TYPED = {
    "turret": ["range", "minRange", "reload", "maxAmmo", "ammoPerShot", "clipSize", "shootCone", "inaccuracy",
               "rotateSpeed", "targetAir", "targetGround", "targetBlocks", "coolantMultiplier", "ammoEjectBack",
               "recoil", "recoilTime", "shootWarmupSpeed", "minWarmup", "velocityRnd", "reloadWhileCharging",
               "ammoItems"],
    "drill": ["drillTime", "tier", "hardnessDrillMultiplier", "liquidBoostIntensity", "blockedItem", "warmupSpeed"],
    "crafter": ["craftTime", "dumpTime", "warmupSpeed", "ignoreLiquidFullness", "dumpExtraLiquid", "outputs",
                "outputLiquids"],
    "separator": ["craftTime", "dumpTime", "results"],
    "conveyor": ["speed", "displayedSpeed", "pushUnits", "isDuct"],
    "generator": ["powerProduction", "explosionRadius", "explosionDamage"],
    "battery": ["powerCapacity"],  # v160.7 反射恒为 null，储能看 power.capacity
    "heat": ["heatOutput", "warmupSpeed", "craftTime"],
    "liquid": ["liquidPadding", "liquidPressure", "outputsLiquid"],
    "storage": ["coreMerge"],
    "wall": ["chanceDeflect", "flashHit"],
    "floor": ["isLiquid", "shallow", "speedMultiplier", "dragMultiplier", "damageTaken", "drownTime", "status",
              "liquidDrop"],
    "ore": ["itemDrop"],
}

POWER_KEYS = ["usage", "usagePerSecond", "capacity", "buffered", "production"]

def block_types(hier, pool):
    t = []
    hit = lambda *names: any(n in hier for n in names)
    if any(h.endswith("Turret") for h in hier):
        t.append("turret")
    if hit("mindustry.world.blocks.production.Drill"):
        t.append("drill")
    if hit("mindustry.world.blocks.production.Separator"):
        t.append("separator")
    if hit("mindustry.world.blocks.production.GenericCrafter", "mindustry.world.blocks.production.CraftingBlock",
           "mindustry.world.blocks.production.HeatProducer"):
        t.append("crafter")
    if hit("mindustry.world.blocks.distribution.Conveyor", "mindustry.world.blocks.distribution.Duct"):
        t.append("conveyor")
    if hit("mindustry.world.blocks.power.PowerGenerator"):
        t.append("generator")
    if hit("mindustry.world.blocks.power.Battery"):
        t.append("battery")
    if hit("mindustry.world.blocks.liquid.LiquidBlock"):
        t.append("liquid")
    if hit("mindustry.world.blocks.storage.StorageBlock", "mindustry.world.blocks.storage.CoreBlock"):
        t.append("storage")
    if hit("mindustry.world.blocks.defense.Wall"):
        t.append("wall")
    if hit("mindustry.world.blocks.environment.Floor"):
        t.append("floor")
    if hit("mindustry.world.blocks.environment.OreBlock"):
        t.append("ore")
    if "heatOutput" in pool:
        t.append("heat")
    return t

def _num(v):
    return r4(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None

def build_blocks(raw):
    out = []
    for b in raw:
        p = b.get("p") or {}
        hier = b.get("hier") or [b["cls"]]
        types = block_types(hier, p)
        rec = {
            "id": b["n"], "name": b.get("loc") or b["n"], "src": SRC_PREFIX + b["cls"], "ver": VER,
            "class": short_cls(b["cls"]), "types": types,
            "category": b.get("cat"), "size": b.get("size"), "health": b.get("health"), "armor": b.get("armor"),
            "requirements": b.get("req") or [], "consumers": [],
            "hasPower": b.get("hasPower"), "hasItems": b.get("hasItems"), "hasLiquids": b.get("hasLiquids"),
            "rotate": b.get("rotate"), "solid": b.get("solid"), "underBullets": b.get("underBullets"),
            "itemCapacity": b.get("itemCap"), "liquidCapacity": b.get("liqCap"),
            "buildVisibility": b.get("vis"), "group": b.get("group"), "privileged": b.get("priv"),
            "inEditor": b.get("inEditor"), "placeablePlayer": b.get("placeablePlayer"),
            "alwaysReplace": b.get("alwaysReplace"), "rebuildable": b.get("rebuildable"),
            "unitCapModifier": b.get("unitCapModifier"),
            "buildTime": p.get("buildTime"), "buildCostMultiplier": p.get("buildCostMultiplier"),
        }
        for c in b.get("cons") or []:
            c = dict(c)
            if c.get("cls") == "ConsumePower":
                u = _num(c.get("usage")) or 0.0
                c["usage"] = r4(u)
                c["usagePerSecond"] = r4(u * 60)
                if "capacity" in c:
                    c["capacity"] = _num(c["capacity"])
            c = clean(c)
            if c:
                rec["consumers"].append(c)
        cp = b.get("cp") or {}
        usage = _num(cp.get("usage")) if cp else None
        power = {
            "usage": usage,
            "usagePerSecond": r4(usage * 60) if usage is not None else None,
            "capacity": _num(cp.get("capacity")) if (cp and cp.get("capacity")) else None,
            "buffered": cp.get("buffered") if cp else None,
            "production": _num(p.get("powerProduction")),
        }
        if b.get("hasPower") or any(v is not None for v in power.values()):
            rec["power"] = power
        if b.get("ammo"):
            rec["ammo"] = [{"item": x.split("|")[0], "bullet": x.split("|")[1]} for x in b["ammo"]]
        for t in types:
            for k in BLOCK_TYPED.get(t, []):
                if k == "outputs":
                    rec[k] = b.get("outs") or None
                elif k == "outputLiquids":
                    rec[k] = b.get("outl") or None
                elif k == "results":
                    rec[k] = b.get("res") or None
                elif k == "ammoItems":
                    rec[k] = [x.split("|")[0] for x in (b.get("ammo") or [])] or None
                else:
                    v = p.get(k)
                    rec[k] = _num(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else v
        rec = clean(rec)
        for t in types:
            for k in BLOCK_TYPED.get(t, []):
                rec.setdefault(k, None)
        if "power" in rec:
            for k in POWER_KEYS:
                rec["power"].setdefault(k, None)
        out.append(rec)
    return out

def build_turrets(raw):
    out = []
    keys = ["range", "minRange", "reload", "maxAmmo", "ammoPerShot", "clipSize", "shootCone", "inaccuracy",
            "rotateSpeed", "targetAir", "targetGround", "targetBlocks", "coolantMultiplier", "ammoEjectBack",
            "recoil", "recoilTime", "shootWarmupSpeed", "minWarmup", "velocityRnd", "reloadWhileCharging",
            "consumeAmmoOnce", "displayAmmoMultiplier", "buildTime", "itemCapacity", "liquidCapacity"]
    for t in raw:
        rec = {"id": t["n"], "name": t["n"], "src": SRC_PREFIX + t["cls"], "ver": VER,
               "class": short_cls(t["cls"]), "kind": t.get("kind"),
               "turretClass": short_cls(t.get("tclass") or t["cls"])}
        for k in keys:
            rec[k] = _num(t.get(k)) if isinstance(t.get(k), (int, float)) and not isinstance(t.get(k), bool) else t.get(k)
        ammo = []
        for a in t.get("ammo") or []:
            a = dict(a)
            if a.get("lifetime") and a.get("speed") is not None:
                a["range"] = r4(a["speed"] * a["lifetime"])
                a["rangeDerived"] = True
            ammo.append(clean(a))
        rec["ammo"] = ammo
        rec["consumers"] = [c for c in (clean(x) for x in (t.get("cons") or [])) if c]
        cp = t.get("cp") or {}
        usage = _num(cp.get("usage"))
        if t.get("hasPower") or usage or cp:
            rec["power"] = {"usage": usage, "usagePerSecond": r4(usage * 60) if usage is not None else None,
                            "capacity": _num(cp.get("capacity")) if cp.get("capacity") else None,
                            "buffered": cp.get("buffered")}
        rec = clean(rec)
        for k in keys:
            rec.setdefault(k, None)
        if "power" in rec:
            for k in POWER_KEYS:
                rec["power"].setdefault(k, None)
        out.append(rec)
    return out

def build_bullets(raw):
    out = []
    for b in raw:
        rec = {"id": b["id"], "name": b.get("cname") or b["id"], "alias": None,
               "src": SRC_PREFIX + b["cls"], "ver": VER, "class": short_cls(b["cls"])}
        for k, v in b.items():
            if k in ("id", "cls", "cname"):
                continue
            rec[k] = _num(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else v
        if rec.get("lifetime") and rec.get("speed") is not None:
            rec["range"] = r4(rec["speed"] * rec["lifetime"])
            rec["rangeDerived"] = True
        out.append(clean(rec))
    return out

def link_bullets(blocks, turrets, units, bullets):
    """Fill bullets[].owner/alias and units.weapons[].bulletName from turret ammo + unit weapons."""
    by = {b["id"]: b for b in bullets}
    owners = {}
    for t in turrets:
        for a in t.get("ammo") or []:
            owners.setdefault(a["bullet"], []).append({"type": "turret", "id": t["id"], "via": a["item"]})
    for u in units:
        for i, w in enumerate(u.get("weapons") or []):
            if w.get("bullet"):
                owners.setdefault(w["bullet"], []).append({"type": "unit", "id": u["id"], "via": "weapon%d" % (i + 1)})
    for bid, rec in by.items():
        ow = owners.get(bid, [])
        if ow:
            rec["owner"] = ow[0]["id"]
            rec["ownerType"] = ow[0]["type"]
            rec["alias"] = "%s-%s" % (ow[0]["id"], ow[0]["via"])
            rec["aliases"] = ["%s-%s" % (o["id"], o["via"]) for o in ow]
            rec["owners"] = ow
            rec["name"] = rec["alias"]
    for t in turrets:
        for a in t.get("ammo") or []:
            bb = by.get(a["bullet"])
            a["name"] = (bb.get("alias") or bb.get("name")) if bb else None
    for u in units:
        for w in u.get("weapons") or []:
            bb = by.get(w.get("bullet"))
            w["bulletName"] = (bb.get("alias") or bb.get("name")) if bb else None
    return bullets

def build_units(raw):
    out = []
    for u in raw:
        rec = {"id": u["n"], "name": u.get("loc") or u["n"], "src": SRC_PREFIX + u["cls"], "ver": VER,
               "class": short_cls(u["cls"])}
        for k, v in u.items():
            if k in ("n", "loc", "cls"):
                continue
            rec[k] = v
        rec = clean(rec)
        rec.setdefault("legCount", 0)
        rec["legs"] = bool(rec.get("legCount"))
        rec["legsDerived"] = True
        rec.setdefault("weapons", [])
        rec.setdefault("abilities", [])
        rec.setdefault("immunities", [])
        out.append(rec)
    return out

def build_meta(raw):
    items, liquids, status = [], [], []
    for x in raw["items"]:
        rec = {"id": x["n"], "name": x.get("loc") or x["n"], "src": "jar:v160.7#mindustry.type.Item", "ver": VER}
        for k, v in x.items():
            if k in ("n", "loc"):
                continue
            rec[k] = v
        items.append(clean(rec))
    for x in raw["liquids"]:
        rec = {"id": x["n"], "name": x.get("loc") or x["n"], "src": "jar:v160.7#mindustry.type.Liquid", "ver": VER}
        for k, v in x.items():
            if k in ("n", "loc"):
                continue
            rec[k] = v
        rec = clean(rec)
        if rec.get("effect") is None and rec.get("effectCls"):
            rec["effect"] = rec["effectCls"]
        liquids.append(rec)
    skeys = ["damageMultiplier", "healthMultiplier", "speedMultiplier", "reloadMultiplier", "buildSpeedMultiplier",
             "dragMultiplier", "disarm", "transitionDamage", "intervalDamage", "intervalDamageTime",
             "intervalDamagePierce", "reactive", "effect", "effectChance", "permanent", "show", "hidden", "opposites",
             "affinities", "color"]
    for x in raw["status"]:
        rec = {"id": x["n"], "name": x.get("loc") or x["n"], "src": "jar:v160.7#mindustry.type.StatusEffect", "ver": VER}
        for k, v in x.items():
            if k in ("n", "loc"):
                continue
            rec[k] = v
        rec = clean(rec)
        for k in skeys:
            rec.setdefault(k, None)
        status.append(rec)
    return items, liquids, status

def build_rules(raw):
    out = []
    for x in raw:
        out.append(clean({"id": x["name"], "name": x["name"], "type": x["type"], "value": x.get("value"),
                          "default": x.get("default"), "array": x.get("array"),
                          "src": "jar:v160.7#mindustry.game.Rules", "ver": VER}))
    return out

def coverage(recs, keys):
    n = len(recs)
    return {k: (sum(1 for r in recs if r.get(k) is not None), n) for k in keys}

def write_json(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    return os.path.getsize(path)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(HERE), "00-data"))
    ap.add_argument("--keep-raw", action="store_true")
    args = ap.parse_args()
    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)

    ex = Extractor(out_dir, keep_raw=args.keep_raw)
    t_all = time.time()
    try:
        counts = ex.start()
        bad = {k: (counts.get(k), v) for k, v in EXPECT.items() if counts.get(k) != v}
        if counts.get("status") is None:
            bad["status"] = (None, "?")
        if bad:
            raise SystemExit("content counts mismatch: %s" % bad)
        blocks_raw = ex.extract_blocks()
        turrets_raw = ex.extract_turrets()
        bullets_raw = ex.extract_bullets()
        units_raw = ex.extract_units()
        meta_raw = ex.extract_meta()
        rules_raw = ex.extract_rules()
    finally:
        ex.close()

    blocks = build_blocks(blocks_raw)
    turrets = build_turrets(turrets_raw)
    bullets = build_bullets(bullets_raw)
    units = build_units(units_raw)
    items, liquids, status = build_meta(meta_raw)
    rules = build_rules(rules_raw)
    bullets = link_bullets(blocks, turrets, units, bullets)

    checks = [("items", len(items), 22), ("liquids", len(liquids), 11),
              ("blocks", len(blocks), 447), ("units", len(units), 70),
              ("status", len(status), counts.get("status"))]
    errs = [(n, got, want) for (n, got, want) in checks if want is not None and got != want]
    if errs:
        raise SystemExit("record count mismatch: %s" % errs)
    if not turrets:
        raise SystemExit("no turret extracted")

    sizes = {}
    for name, obj in (("blocks", blocks), ("turrets", turrets), ("bullets", bullets), ("units", units),
                      ("items", items), ("liquids", liquids), ("status", status), ("rules", rules)):
        sizes[name + ".json"] = write_json(os.path.join(out_dir, name + ".json"), obj)

    if sizes["blocks.json"] > 900 * 1024:
        log("[!] blocks.json %.0fKB > 900KB 目标" % (sizes["blocks.json"] / 1024))

    cov = {
        "blocks": coverage(blocks, ["category", "size", "health", "armor", "requirements", "consumers",
                                    "hasPower", "hasItems", "hasLiquids", "rotate", "solid", "underBullets",
                                    "itemCapacity", "liquidCapacity", "buildVisibility", "group", "privileged",
                                    "inEditor", "placeablePlayer", "alwaysReplace", "rebuildable",
                                    "unitCapModifier", "buildTime", "power"]),
        "turrets": coverage(turrets, ["range", "reload", "maxAmmo", "ammo", "targetAir", "targetGround",
                                      "shootCone", "inaccuracy", "rotateSpeed", "coolantMultiplier",
                                      "ammoEjectBack", "minRange", "ammoPerShot", "clipSize", "recoil",
                                      "shootWarmupSpeed", "power"]),
        "bullets": coverage(bullets, ["damage", "speed", "lifetime", "drag", "pierce", "pierceCap",
                                      "splashDamage", "splashDamageRadius", "lightning", "lightningDamage",
                                      "fragBullets", "width", "height", "hitSize", "ammoMultiplier",
                                      "reloadMultiplier", "status", "statusDuration", "collidesAir",
                                      "collidesGround", "absorbable", "hittable", "keepVelocity", "range",
                                      "owner", "alias"]),
        "units": coverage(units, ["health", "armor", "speed", "flying", "naval", "legCount", "legs", "hitSize",
                                  "range", "maxRange", "itemCapacity", "buildSpeed", "mineSpeed", "mineTier",
                                  "buildRange", "canBoost", "boostMultiplier", "useUnitCap", "targetPriority",
                                  "abilities", "immunities", "weapons"]),
        "liquids": coverage(liquids, ["viscosity", "heatCapacity", "temperature", "flammability", "explosiveness",
                                      "coolant", "effect", "gas", "boilPoint", "incinerable", "blockReactive"]),
        "items": coverage(items, ["hardness", "cost", "flammability", "explosiveness", "radioactivity", "charge",
                                  "lowPriority", "color"]),
        "status": coverage(status, ["damageMultiplier", "healthMultiplier", "speedMultiplier", "reloadMultiplier",
                                    "buildSpeedMultiplier", "dragMultiplier", "disarm", "transitionDamage",
                                    "intervalDamage", "intervalDamageTime", "reactive", "effect", "opposites",
                                    "affinities"]),
        "rules": coverage(rules, ["value", "default"]),
    }
    for t, keys in BLOCK_TYPED.items():
        cov["blocks_" + t] = coverage([r for r in blocks if t in (r.get("types") or [])], keys)

    gen_time = time.strftime("%Y-%m-%d %H:%M:%S")
    total = sum(sizes.values())
    elapsed = time.time() - t_all
    log("[rt] total %.0fKB  elapsed %.1fs" % (total / 1024, elapsed))
    for k, v in sizes.items():
        log("  %-14s %7.0fKB" % (k, v / 1024))

    nc = {"blocks": len(blocks), "turrets": len(turrets), "bullets": len(bullets), "units": len(units),
          "items": len(items), "liquids": len(liquids), "status": len(status), "rules": len(rules)}
    write_readme(out_dir, sizes, cov, nc, gen_time, elapsed)
    log("[rt] README.md written; tables in", out_dir)
    return 0

def write_readme(out_dir, sizes, cov, nc, gen_time, elapsed):
    BT = chr(96)
    L = []
    A = L.append
    A("# 00-data — v160.7 机器可读事实表")
    A("")
    A("由 " + BT + "tools/extract_rt.py" + BT + " 从 **v160.7 真服务器 jar 反射**生成（" + BT + "out/_server160.jar" + BT +
      " + jre21 headless），**禁止手改**。")
    A("")
    A("重跑：" + BT + "python -u kb-stage/tools/extract_rt.py" + BT + "（起服务器 2–8s，全量 5–40s，本机本次 %.1fs）。" % elapsed)
    A("")
    A("| 文件 | 条数 | 体积 | 抽取源 |")
    A("|---|---|---|---|")
    srcmap = {
        "blocks.json": "Vars.content.blocks() 全量（447）",
        "turrets.json": "类继承链含 *Turret 的方块（31 条；与 blocks.json 中 types 含 turret 的条数一致）",
        "bullets.json": "炮塔 ammoTypes + 单位 weapons 的 BulletType（IdentityHashMap 去重）",
        "units.json": "Vars.content.units() 全量（70）",
        "items.json": "Vars.content.items() 全量（22）",
        "liquids.json": "Vars.content.liquids() 全量（11）",
        "status.json": "Vars.content.statusEffects() 全量（23）",
        "rules.json": "Vars.state.rules 全部 public 实例字段 + new Rules() 默认值",
    }
    for k in ["blocks.json", "turrets.json", "bullets.json", "units.json", "items.json", "liquids.json",
              "status.json", "rules.json"]:
        key = k.replace(".json", "")
        A("| " + BT + k + BT + " | " + str(nc[key]) + " | %.0fKB | " % (sizes[k] / 1024) + srcmap[k] + " |")
    A("")
    A("## 通用约定（所有表）")
    A("")
    A("- 每条记录必带：" + BT + "id" + BT + "（游戏内 id，kebab-case，等于 name 字段）、" + BT + "name" + BT +
      "（英文名；单位/物品/液体/状态取 localizedName en）、" + BT + "src" + BT + "（" + BT +
      "jar:v160.7#<Java 类全名>" + BT + "，类名里的 " + BT + "$<n>" + BT + " 是匿名内部类）、" + BT + "ver" + BT +
      "（固定 " + BT + "v160.7" + BT + "）。")
    A("- **浮点统一 4 位小数**（jar 里 float 2.700000047683716 记为 2.7）。")
    A("")
    A("### 单位口径（jar 原值 → 游戏单位；换算规则引自 v159.3 源码树 = 语义权威）")
    A("")
    A("| 量 | 表内字段 | jar 单位 | 换算 | 源码依据 |")
    A("|---|---|---|---|---|")
    A("| 世界单位 | — | 1 tile = **8** world units | tiles = v / 8 | " + BT + "core/src/mindustry/Vars.java:135" + BT + "（tilesize = 8） |")
    A("| 时间/进度 | reload, lifetime, craftTime, drillTime, statusDuration | **ticks** | 秒 = v / 60 | " + BT + "core/src/mindustry/world/blocks/defense/turrets/Turret.java:183" + BT + " |")
    A("| 功率 | usage, production, capacity | **power/tick** | /s = v × 60 | " + BT + "ConsumePower.usage" + BT + " 由电网每 tick 结算 |")
    A("| 炮塔射程 | blocks/turrets 的 range | world units | tiles = range / 8 | " + BT + "core/src/mindustry/world/blocks/defense/turrets/Turret.java:421" + BT + "（range() = (range+…) / tilesize） |")
    A("| 弹体速度 | bullet speed | **world units/tick** | tiles/s = v × 60 / 8 | " + BT + "core/src/mindustry/entities/bullet/BulletType.java:439" + BT + "（range() = speed × lifetime） |")
    A("| 弹体射程 | bullet range | world units | tiles = range / 8 | 同上 |")
    A("| 单位速度 | unit speed | **world units/tick** | tiles/s = v × 60 / 8 | " + BT + "core/src/mindustry/type/UnitType.java:791,1441" + BT + "（speed*60f/tilesize） |")
    A("| 单位射程 | unit range / maxRange | world units | tiles = v / 8 | " + BT + "core/src/mindustry/type/UnitType.java:794" + BT + " |")
    A("| 单位体积 | hitSize | world units | blocks = v / 8 | " + BT + "core/src/mindustry/type/UnitType.java:792" + BT + " |")
    A("")
    A("校验样例：duo range=160 → 20 tiles；duo-copper bullet speed=2.5 × lifetime=70 → 175 units → 21.9 tiles；dagger speed=0.5 → 3.75 tiles/s、maxRange=146 → 18.25 tiles、hitSize=8 → 1 tile。")
    A("")
    A("- " + BT + "itemCapacity" + BT + " 是件数；" + BT + "liquidCapacity" + BT + " 是液体单位原值（不换算）。")
    A("- 除按类型白名单强制补齐的字段外，值为 " + BT + "null" + BT + " 的键**省略**；白名单内的键**一定存在**，取不到就是 " +
      BT + "null" + BT + "（下游可直接 " + BT + "rec[\"craftTime\"]" + BT + " 不判键存在）。")
    A("")
    A("## blocks.json")
    A("")
    A("### 稳定契约字段（447 条全部有）")
    A("")
    A(BT + "category" + BT + "、size（格）、health、armor、" + BT + "requirements[].{item,amount}" + BT + "、" +
      BT + "consumers[]" + BT + "、hasPower/hasItems/hasLiquids、rotate/solid/underBullets、itemCapacity/liquidCapacity、" +
      "buildVisibility/group/privileged/inEditor/placeablePlayer/alwaysReplace/rebuildable/unitCapModifier、" +
      "buildTime（ticks）、buildCostMultiplier、" + BT + "types[]" + BT + "（本表类型标签，255/447 条有；墙/植被/岩石/装饰等 192 条无可分类类型，因而没有类型字段）、" +
      BT + "ammo[]" + BT + "（仅炮塔：" + BT + "{item,bullet}" + BT + "，bullet 指向 bullets.json 的 id）。")
    A("")
    A(BT + "consumers[]" + BT + "：" + BT + "{cls,...}" + BT + "。**ConsumePower 必带 " + BT + "usage" + BT +
      "（power/tick）与 " + BT + "usagePerSecond" + BT + "（/s）**；ConsumeItems/ConsumeLiquid 带 " + BT +
      "items[]/liquids[]" + BT + " 栈。")
    A("")
    A("### power 对象（hasPower 或发电机/电池才出现）")
    A("")
    A(BT + "power = {usage, usagePerSecond, capacity, buffered, production}" + BT + "，全部 5 个键**必定存在**（无值 " +
      BT + "null" + BT + "）。" + BT + "usage" + BT + " 单位 power/tick，capacity 是电池储能（battery=" +
      BT + "capacity:4000, buffered:true" + BT + "），production 单位 power/tick。")
    A("")
    A("### 类型特有字段白名单（按 " + BT + "types[]" + BT + " 强制补齐，无值为 null）")
    A("")
    A("| type | 字段（v160.7 真实字段名） |")
    A("|---|---|")
    for tname, keys in BLOCK_TYPED.items():
        A("| " + tname + " | " + ", ".join(keys) + " |")
    A("")
    A("取值来自 jar 同名字段；" + BT + "outputs" + BT + "=" + BT + "outputItems[]" + BT + "、" + BT + "outputLiquids" + BT +
      "=" + BT + "outputLiquids[]" + BT + "、" + BT + "results" + BT + "（Separator 的产出池）、" + BT +
      "ammoItems" + BT + "（炮塔接受的弹药物品名）。反射恒为 " + BT + "null" + BT + " 的字段：" + BT + "ignoreLiquidFullness" + BT + "（v160 已并入其它机制）、" + BT + "powerCapacity" + BT + "（v160 电池没有该字段，储能看 " + BT + "power.capacity" + BT + "）；" + BT + "displayedSpeed" + BT + " 只在传送带上可读（conveyor=8、titanium-conveyor=10），其他类型为 null。")
    A("**白名单是并集**：记录里没有该字段就是 " + BT + "null" + BT + "（如 parallax 无 reload）；v160.7 炮塔基类是 " + BT + "BaseTurret" + BT + "，parallax / segment / repair-point / repair-turret / build-tower 不在 " + BT + "Turret" + BT + " 分支下但仍归 " + BT + "turret" + BT + " 类型。")
    A("")
    A("**best-effort 字段**（反射不保证）：" + BT + "status/liquidDrop/blockedItem/itemDrop" + BT +
      "（枚举/内容引用，取不到即省略）、floor/wall 类附加字段。")
    A("")
    A("## turrets.json")
    A("")
    A("**31 条**（= blocks.json 中 " + BT + "types" + BT + " 含 " + BT + "turret" + BT + " 的条数）。" + BT + "kind" + BT + " 取值：" + BT + "item" + BT + "（弹药炮塔，ammo[] 非空）、" + BT + "liquid" + BT + "（液体炮塔）、" + BT + "power/laser/continuous/continuousliquid" + BT + "（能量类，耗能看 power.usage）、" + BT + "tractorbeam" + BT + "（parallax）、" + BT + "pointdefense" + BT + "（segment）、" + BT + "build" + BT + "（build-tower）、" + BT + "repair" + BT + "（repair-point、repair-turret，无射程无 reload 循环）。" + BT + "turretClass" + BT + " 是命中的继承链类简名（如 " + BT + "defense.turrets.ItemTurret" + BT + "）。")
    A("")
    A("字段：range（world units，÷8=tiles）、minRange、reload（ticks）、maxAmmo、ammoPerShot、clipSize、" + BT + "shootCone" + BT + "（度）、inaccuracy（度）、rotateSpeed（度/tick）、targetAir/targetGround/targetBlocks、" +
      "coolantMultiplier、ammoEjectBack、recoil、recoilTime、shootWarmupSpeed、minWarmup、velocityRnd、" +
      "reloadWhileCharging、consumeAmmoOnce、displayAmmoMultiplier、buildTime、power{...}（同上）。")
    A("")
    A(BT + "ammo[]" + BT + " 每个接受的弹药物品一条：" + BT + "{item, bullet, name, damage, speed, lifetime, range, ammoMultiplier, reloadMultiplier, status, statusDuration}" + BT +
      "；" + BT + "bullet" + BT + " 是 bullets.json 的主键，" + BT + "name" + BT + " 是人读别名（如 " + BT +
      "duo-copper" + BT + "）。" + BT + "range" + BT + " 由 speed*lifetime 派生时带 " + BT + "rangeDerived:true" + BT + "。")
    A("")
    A("## bullets.json")
    A("")
    A("137 条（identity 去重）。" + BT + "id = b<identityHashCode>" + BT + " 是**同一次 run 内**的稳定主键（跨 run 不稳定，" +
      "不要跨 run 比对）；" + BT + "alias" + BT + " = " + BT + "<owner>-<弹药物品|weaponN>" + BT + "，" + BT +
      "owner/ownerType/owners[]" + BT + " 记录所有引用者（炮塔弹药或单位武器），" + BT + "name" + BT +
      " 有 owner 时等于 alias，否则为 Java 匿名类简名。")
    A("")
    A("字段：damage/speed（world units/tick，×60÷8 = tiles/s）/lifetime（ticks）/drag/pierce/pierceCap/splashDamage/splashDamageRadius/" +
      "splashDamagePierce/lightning/lightningDamage/lightningLength/fragBullets/fragAngle/fragVelocityMin/fragVelocityMax/" +
      "width/height/hitSize/ammoMultiplier/reloadMultiplier/status/statusDuration/collides/collidesAir/collidesGround/" +
      "absorbable/hittable/keepVelocity/range/hitShake/hitUnder/knockback/reflectable/laserAbsorb/pierceArmor/" +
      "buildingDamageMultiplier/intervalBullets/intervalBulletInterval。")
    A("")
    A("## units.json")
    A("")
    A("70 条。health/armor/speed（world units/tick，×60÷8 = tiles/s）/flying/naval/legCount/hitSize（÷8 = blocks）/range、maxRange（÷8 = tiles）/itemCapacity/" +
      "buildSpeed/mineSpeed/mineTier/mineRange/buildRange/canBoost/boostMultiplier/useUnitCap/targetPriority/" +
      "targetAir/targetGround/targetBlocks/drag/accel/rotateSpeed/payloadCapacity/engineSize/engineOffset/" +
      "researchCostMultiplier/ammoCapacity/clipSize 等。")
    A("")
    A("- " + BT + "weapons[]" + BT + " = " + BT + "{name, bullet, bulletName, reload, x, y, inaccuracy, shootCone, alternate, mirror, ...}" + BT +
      "，bullet 指向 bullets.json id，bulletName 是可读别名。")
    A("- " + BT + "abilities[]" + BT + " = " + BT + "{cls, <该 Ability 子类 public 标量字段>}" + BT + "。")
    A("- " + BT + "immunities[]" + BT + " = 状态名数组（" + BT + "java.util.Set<StatusEffect>" + BT + " 反射）。")
    A("- " + BT + "legs" + BT + " 是**派生**字段（" + BT + "legCount > 0" + BT + "），带 " + BT + "legsDerived:true" + BT +
      "：v160.7 的 UnitType 没有 " + BT + "legs" + BT + " 布尔字段，别当原始值用；爬行类用 " + BT + "legCount>0 && !flying && !naval" + BT + " 判断更准。")
    A("- v160.7 没有 " + BT + "isCounted" + BT + " 字段，单位上限吃掉与否用 " + BT + "useUnitCap" + BT + "。")
    A("")
    A("## liquids.json / items.json / status.json")
    A("")
    A("liquids（11）：viscosity/heatCapacity/temperature/flammability/explosiveness/coolant/gas/boilPoint/incinerable/" +
      "blockReactive/canStayOn/particleSpacing/effectCls/colorHex；" + BT + "effect" + BT + " 与 " + BT + "effectCls" + BT + " 同值（Effect 类全名，不是实例摘要）。")
    A("")
    A("items（22）：hardness/cost/flammability/explosiveness/radioactivity/charge/lowPriority/color（ARGB int）/" +
      "colorHex/healthScaling/hidden/alwaysUnlocked/buildable。")
    A("")
    A("status（23）：damageMultiplier/healthMultiplier/speedMultiplier/reloadMultiplier/buildSpeedMultiplier/" +
      "dragMultiplier/disarm/transitionDamage/" + BT + "intervalDamage/intervalDamageTime/intervalDamagePierce" + BT +
      "/reactive/effect/effectChance/permanent/show/hidden/opposites[]/affinities[]/color。")
    A("")
    A("**注意**：v160.7 的 StatusEffect 没有 " + BT + "category/duration/interval" + BT + " 字段（本文档旧版按 v159 写的），" +
      "持续伤害改由 " + BT + "intervalDamage*" + BT + " 描述。" + BT + "opposites/affinities" + BT + " 是 " + BT + "arc.struct.ObjectSet" + BT + "（只有 " + BT + "size" + BT + " 和 " + BT + "each(Cons)" + BT + " 可用，Rhino 里用 " + BT + "JavaAdapter" + BT + " 实现 " + BT + "Cons" + BT + " 回调收集），元素都是 StatusEffect：opposites 只记名字，affinities 记 " + BT + "状态名+damage" + BT + "（权重读 StatusEffect 的 " + BT + "damage" + BT + " 字段），均已排序便于 diff；实测 " + BT + "burning" + BT + " opposites=[freezing,wet]、affinities=[tarred+0]，" + BT + "tarred" + BT + " affinities=[burning+0.167, melting+0.3]。")
    A("")
    A("## rules.json")
    A("")
    A("118 条 = " + BT + "mindustry.game.Rules" + BT + " 全部 public 实例字段（一个字段一条，不是一份 rules 对象）。" +
      BT + "name/type/value/default" + BT + "：" + BT + "value" + BT + " 是 headless 服务器 " + BT +
      "Vars.state.rules" + BT + " 的运行值，" + BT + "default" + BT + " 是 " + BT + "new Rules()" + BT + " 的默认值。" +
      "**只记字段与值，语义解释交给 05-campaign / 07-rules 各篇。**")
    A("")
    A("标量覆盖 " + BT + "value 92/118" + BT + "、" + BT + "default 93/118" + BT + "；其余 26 个是对象/集合/默认 null 字段（" + BT +
      "teams" + BT + "、" + BT + "attributes" + BT + "、" + BT + "spawns/loadout/weather/ambientMusic/darkMusic" + BT + "（Seq）、" + BT +
      "bannedBlocks/bannedUnits/revealedBlocks/researched/objectiveFlags" + BT + "（ObjectSet）、" + BT + "blockLimits" + BT + "、" + BT +
      "objectives" + BT + "、" + BT + "tags" + BT + "、staticColor/dynamicColor/ambientLight/cloudColor" + BT + "、4 个字符串（modeName/mission/customBackgroundCallback/backgroundTexture）、" + BT +
      "planet/planetBackground/sector" + BT + "），本表只留 " + BT + "type" + BT + " 不展开；要具体值查存档或 05-campaign。")
    A("")
    A("## 怎么联合查（示例）")
    A("")
    A("查一个炮塔的完整画像（blocks.json 白名单字段 + turrets.json 弹药映射 + bullets.json 弹体）：")
    A("")
    A(BT * 3 + "python")
    A("import json")
    A("D = 'kb-stage/00-data/'")
    A("blocks = {b['id']: b for b in json.load(open(D + 'blocks.json', encoding='utf-8'))}")
    A("turrets = {t['id']: t for t in json.load(open(D + 'turrets.json', encoding='utf-8'))}")
    A("bullets = {b['id']: b for b in json.load(open(D + 'bullets.json', encoding='utf-8'))}")
    A("b, t = blocks['duo'], turrets['duo']")
    A("print(b['category'], b['size'], b['health'], b['range'] / 8, 'tiles', b['reload'], 'ticks', b['power'])   # blocks.json 已有炮塔字段")
    A("for a in t['ammo']:")
    A("    print(a['item'], bullets[a['bullet']]['damage'], bullets[a['bullet']]['speed'] * 60 / 8, 'tiles/s')")
    A(BT * 3)
    A("")
    A("按类型筛 blocks：" + BT + "[b for b in blocks if 'crafter' in b['types']]" + BT + "；" +
      "查制造时间：" + BT + "blocks['graphite-press']['craftTime']" + BT + "（ticks，÷60 秒）。")
    A("")
    A("## 条数与覆盖率")
    A("")
    A("精确条数：blocks=%d, turrets=%d, bullets=%d, units=%d, items=%d, liquids=%d, status=%d, rules=%d。" % (
        nc["blocks"], nc["turrets"], nc["bullets"], nc["units"], nc["items"], nc["liquids"], nc["status"], nc["rules"]))
    A("")
    A("| 表 | 字段 | 有值/总数 |")
    A("|---|---|---|")
    for tname in ["blocks", "turrets", "bullets", "units", "liquids", "items", "status", "rules"]:
        for k, (c, n) in cov[tname].items():
            A("| %s | %s | %d/%d |" % (tname, k, c, n))
    A("")
    A("rules 的 value/default 不到 118/118 的原因：26 个对象/集合型字段默认 null，只记 type，见 rules.json 一节。")
    A("")
    A("blocks 的 " + BT + "types" + BT + " 覆盖 255/447；其余 192 条是静态墙（stone-wall 等）、植被、岩石、装饰方块，v160.7 里没有对应的可分类字段，它们仍有“稳定契约字段”那一段的全部字段。" + BT + "ammo" + BT + " 只出现在炮塔（" + BT + "types" + BT + " 含 " + BT + "turret" + BT + "）。")
    A("")
    A("### blocks.json 各类型白名单覆盖率（该类型条数内）")
    A("")
    A("| type | 条数 | 字段: 有值/条数 |")
    A("|---|---|---|")
    for tname in BLOCK_TYPED:
        key = "blocks_" + tname
        if key not in cov:
            continue
        n = max((v[1] for v in cov[key].values()), default=0)
        parts = ["%s %d/%d" % (k, c, nn) for k, (c, nn) in cov[key].items()]
        A("| " + tname + " | " + str(n) + " | " + "; ".join(parts) + " |")
    A("")
    A("## 已知边界")
    A("")
    A("- jar 反射给的是**代码里的基础值**，不等于运行时生效值（range 会被超速/冷却液/加成改变，craftTime 会被超速改变）。")
    A("- bullets.json 的 id 是 identity hash，**只在本 run 内有效**；不要写进文章，文章引用 " + BT +
      "alias" + BT + "（如 " + BT + "duo-copper" + BT + "）。")
    A("- rules.json 的 value 来自 headless 服务端默认 state，不是某个存档的规则。")
    A("- v160.x 新增内容在 v159.3 源码树里没有：本表不回填源码行号；类层次差异（如 " + BT + "BaseTurret" + BT + " 层）以 jar 反射为准，语义/S 级证据见 01–08 各篇。")
    A("- 反射只覆盖 public 字段 + public 无参 getter 不在此列：private/protected 字段（如部分内部计时器）不在表内。")
    A("")
    A("## 生成命令")
    A("")
    A(BT * 3)
    A("python -u kb-stage/tools/extract_rt.py            # 生成全部表 + 本 README")
    A("python -u kb-stage/tools/extract_rt.py --out DIR  # 指定输出目录")
    A(BT * 3)
    A("")
    A("生成时间：%s　用时：%.1fs" % (gen_time, elapsed))
    A("")
    with open(os.path.join(out_dir, "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L))

if __name__ == "__main__":
    main()
