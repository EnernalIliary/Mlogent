"""浠庣湡 v160.7 鏈嶅姟绔?jar 閲?dump 娓告垙鏁版嵁锛圧hino JS + 鍙嶅皠锛?> gamedata.json

璺嚎锛歚java -jar out/_server160.jar` 璧峰畼鏂规湇鍔＄锛岀敤鎺у埗鍙?`js` 鍛戒护锛圧hino锛?閬嶅巻 `Vars.content`銆傚姣忎釜瀵硅薄鍋?**鍏湁瀛楁鍙嶅皠**锛岃€屼笉鏄墜宸ュ垪瀛楁鍚嶁€斺€?鍥犳 v159.3 婧愮爜 / v160.7 jar 鐨勫瓧娈靛樊寮備笉浼氳 dump 澶辫触锛屽彇涓嶅埌鐨勫瓧娈电洿鎺ヤ笉鍑虹幇銆?
鐢ㄦ硶锛?    python MBO/spikes/data/extract_game_data.py [--jar PATH] [--java PATH] [--out PATH]

浜х墿锛歁BO/spikes/data/gamedata.json
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, ROOT)

HERE = os.path.dirname(os.path.abspath(__file__))

DEFAULT_JAR = os.path.join(ROOT, "out", "_server160.jar")
DEFAULT_JAVA = os.path.join(ROOT, "out", "jre21", "jdk-21.0.5+11-jre", "bin", "java.exe")
DEFAULT_OUT = os.path.join(HERE, "gamedata.json")

# ---------------------------------------------------------------- server channel


class ServerError(RuntimeError):
    pass


class Server:
    """Minimal launcher for the official server jar + Rhino `js` console."""

    def __init__(self, java: str, jar: str, workdir: str):
        self.workdir = workdir
        os.makedirs(os.path.join(workdir, "config", "logs"), exist_ok=True)
        self.proc = subprocess.Popen(
            [java, "-Dstdout.encoding=UTF-8", "-Dstderr.encoding=UTF-8", "-jar", jar],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=workdir,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        self.lines: queue.Queue = queue.Queue()
        self.all: list[str] = []
        self.exit_code = None
        threading.Thread(target=self._pump, daemon=True).start()
        self.wait_for("Server loaded.", 120)

    def _pump(self):
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self.lines.put(line.rstrip("\r\n"))
        self.exit_code = self.proc.wait()
        self.lines.put(None)

    def send(self, cmd: str):
        assert self.proc.stdin is not None
        self.proc.stdin.write(cmd + "\n")
        self.proc.stdin.flush()

    def wait_for(self, needle: str, timeout: float = 120.0) -> list[str]:
        deadline = time.time() + timeout
        out: list[str] = []
        while time.time() < deadline:
            try:
                line = self.lines.get(timeout=0.2)
            except queue.Empty:
                continue
            if line is None:
                raise ServerError(f"server exited (code={self.exit_code}):\n" + "\n".join(self.all[-25:]))
            self.all.append(line)
            out.append(line)
            if needle in line:
                return out
        raise ServerError(f"timeout waiting for {needle!r}; tail:\n" + "\n".join(self.all[-25:]))

    def js(self, script: str, timeout: float = 180.0, needle: str = "undefined") -> list[str]:
        """Run one console `js` command (must be one line); return printed lines."""
        one_line = " ".join(script.splitlines())
        self.send("js " + one_line)
        lines = self.wait_for(needle, timeout)
        payload = []
        for ln in lines:
            m = re.search(r"\[none/base\.js\]:\s?(.*)$", ln)
            if m:
                payload.append(m.group(1))
        errs = [ln for ln in lines if "Exception" in ln or ln.startswith("\tat ")]
        if errs:
            raise ServerError("\n".join(errs[:20]))
        return payload

    def close(self):
        try:
            if self.proc.poll() is None:
                self.send("exit")
                try:
                    self.proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass
        finally:
            for s in (self.proc.stdin, self.proc.stdout):
                try:
                    s.close()
                except Exception:
                    pass


# ---------------------------------------------------------------- JS dump script

# Generic public-field reflection.  `fmt` only accepts values that serialize
# cleanly: numbers / booleans / strings / enums / Item / Liquid / ItemStack[] /
# LiquidStack[].  Everything else (textures, draw blocks, functions) is skipped.
JS_COMMON = r"""
function fmt(v, ty){
  if(v === null || v === undefined) return null;
  var n = ty.getName();
  if(n == 'boolean') return v ? '1' : '0';
  if(n == 'int' || n == 'float' || n == 'double' || n == 'short' || n == 'long' || n == 'byte' || n == 'char') return '' + v;
  if(n == 'java.lang.String') return '' + v;
  try{
    /* NOTE: many content objects are anonymous subclasses (Items$1, Blocks$128),
       so exact class-name matching is useless -- always use instanceof.
       (JS is joined into a single line before being sent: never use // comments here.) */
    if(v instanceof Packages.mindustry.ctype.Content) return '' + v.name;
    if(v instanceof Packages.java.lang.Class) return '' + v.getName();
    if(v instanceof Packages.java.lang.Enum) return '' + v.name();
    var c = v.getClass();
    if(c.isArray()){
      var s = '';
      for(var i = 0; i < v.length; i++){
        var q = v[i];
        if(q === null) continue;
        var t = 'x';
        if(q instanceof Packages.mindustry.type.ItemStack) t = 'i';
        else if(q instanceof Packages.mindustry.type.LiquidStack) t = 'l';
        else continue;
        var nm = (t == 'i') ? q.item.name : q.liquid.name;
        s += (s ? ';' : '') + t + ':' + nm + ':' + q.amount;
      }
      return '[' + s + ']';
    }
  }catch(e){}
  return null;
}
function fields(o, sep){
  var out = '', seen = {}, c = o.getClass();
  while(c !== null && ('' + c.getName()).indexOf('mindustry') == 0){
    var fs = null;
    try{ fs = c.getDeclaredFields(); }catch(e){}
    if(fs !== null){
      for(var i = 0; i < fs.length; i++){
        var f = fs[i];
        try{
          if(!Packages.java.lang.reflect.Modifier.isPublic(f.getModifiers())) continue;
          if(Packages.java.lang.reflect.Modifier.isStatic(f.getModifiers())) continue;
          var nm = f.getName();
          if(seen[nm]) continue;
          seen[nm] = 1;
          try{ f.setAccessible(true); }catch(e3){}
          var v = f.get(o);
          var sv = fmt(v, f.getType());
          if(sv === null) continue;
          out += (out ? sep : '') + nm + '=' + sv;
        }catch(e2){}
      }
    }
    c = c.getSuperclass();
  }
  return out;
}
function cls(o){ return '' + o.getClass().getName(); }
"""

JS_ITEMS = (
    JS_COMMON
    + r"""
(function(){
var it = Vars.content.items();
for(var i = 0; i < it.size; i++){
  var x = it.get(i);
  try{ print('IT|' + x.id + '|' + x.name + '|' + fields(x, '\t')); }
  catch(e){ print('ITERR|' + i + '|' + e); }
}
})();"""
)

JS_LIQUIDS = (
    JS_COMMON
    + r"""
(function(){
var lt = Vars.content.liquids();
for(var i = 0; i < lt.size; i++){
  var x = lt.get(i);
  try{ print('LQ|' + x.id + '|' + x.name + '|' + fields(x, '\t')); }
  catch(e){ print('LQERR|' + i + '|' + e); }
}
})();"""
)

JS_BLOCKS = (
    JS_COMMON
    + r"""
(function(START, END){
var bt = Vars.content.blocks();
if(END > bt.size) END = bt.size;
for(var i = START; i < END; i++){
  var b = bt.get(i);
  var cn = cls(b), rc = cn;
  try{
    var cc = b.getClass();
    while(('' + cc.getName()).indexOf('mindustry.content.Blocks') == 0 && cc.getSuperclass() !== null){
      cc = cc.getSuperclass();
    }
    rc = '' + cc.getName();
  }catch(e9){}
  print('BH|' + b.id + '|' + b.name + '|' + cn + '|' + rc);
  try{
    for(var k = 0; k < b.consumers.length; k++){
      var c = b.consumers[k];
      print('BC|' + b.id + '|' + cls(c) + '~' + fields(c, ','));
    }
  }catch(e1){ print('BCERR|' + b.id + '|' + e1); }
  try{
    var fld = fields(b, '\t');
    var parts = fld.split('\t');
    for(var p = 0; p < parts.length; p++){
      if(parts[p]) print('BF|' + b.id + '|' + parts[p]);
    }
  }catch(e2){ print('BFERR|' + b.id + '|' + e2); }
}
print('SDONE');
})(%d, %d);"""
)

JS_META = r"""
(function(){
var m = [];
try{ m.push('build=' + Packages.mindustry.core.Version.build); }catch(e){}
try{ m.push('modifier=' + Packages.mindustry.core.Version.modifier); }catch(e){}
try{ m.push('buildDate=' + Packages.mindustry.core.Version.buildDate); }catch(e){}
try{ m.push('contentBlocks=' + Vars.content.blocks().size); }catch(e){}
try{ m.push('contentItems=' + Vars.content.items().size); }catch(e){}
try{ m.push('contentLiquids=' + Vars.content.liquids().size); }catch(e){}
try{ m.push('contentUnits=' + Vars.content.units().size); }catch(e){}
print('META|' + m.join('\t'));
})();"""


# ---------------------------------------------------------------- parsing helpers


def parse_fields(blob: str, sep: str = "\t") -> dict[str, str]:
    out: dict[str, str] = {}
    if not blob:
        return out
    for part in blob.split(sep):
        if "=" not in part:
            continue
        k, _, v = part.partition("=")
        out[k.strip()] = v
    return out


def parse_stacks(v: str) -> list[dict]:
    """'[i:copper:1;l:water:0.5]' -> [{'kind':'item','name':...}]"""
    v = (v or "").strip()
    if not v.startswith("["):
        return []
    body = v[1:-1]
    out = []
    for s in body.split(";"):
        if not s:
            continue
        bits = s.split(":")
        if len(bits) < 3:
            continue
        out.append({"kind": "item" if bits[0] == "i" else "liquid",
                    "name": bits[1], "amount": round(float(bits[2]), 4)})
    return out


def fnum(d: dict, key: str, default=None):
    if key not in d:
        return default
    try:
        f = float(d[key])
    except ValueError:
        return default
    if f.is_integer() and abs(f) < 1e9:
        return int(f)
    return round(f, 6)


def fbool(d: dict, key: str, default=False):
    if key not in d:
        return default
    return d[key] == "1"


def fstr(d: dict, key: str, default=None):
    return d.get(key, default)



# Java class (from the server jar) -> coarse MBO family.  v160.7 ships anonymous
# Blocks$NNN subclasses, so `realClass` is the first non-anonymous superclass.
_FAMILY_BY_CLASS = {
    "Drill": "drill", "BurstDrill": "drill", "WallCrafter": "drill",
    "Conveyor": "conveyor", "StackConveyor": "conveyor", "ArmoredConveyor": "conveyor",
    "Duct": "duct", "DuctBridge": "duct",
    "Conduit": "conduit", "LiquidBridge": "conduit", "ConduitBridge": "conduit",
    "PowerNode": "powerNode", "BeamNode": "powerNode", "LongPowerNode": "powerNode",
    "PowerGenerator": "generator", "ConsumeGenerator": "generator",
    "ImpactReactor": "generator", "NuclearReactor": "generator",
    "SolarGenerator": "generator", "ThermalGenerator": "generator",
    "SingleTypeGenerator": "generator", "ItemLiquidGenerator": "generator",
    "VariableReactor": "generator",
    "Pump": "pump",
    "Separator": "separator",
    "GenericCrafter": "crafter", "AttributeCrafter": "crafter", "Crafter": "crafter",
    "Wall": "environment", "Floor": "environment", "OreBlock": "environment",
    "TreeBlock": "environment", "Prop": "environment", "StaticWall": "environment",
    "ItemTurret": "turret", "LiquidTurret": "turret", "PowerTurret": "turret",
    "BaseTurret": "turret",
    "Router": "distribution", "Junction": "distribution", "Sorter": "distribution",
    "OverflowGate": "distribution", "UnderflowGate": "distribution",
    "ItemBridge": "distribution", "MassDriver": "distribution",
    "LogicBlock": "logic", "Battery": "power", "PowerSource": "power",
    "StorageBlock": "storage", "CoreBlock": "core", "UnitFactory": "units",
    "Reconstructor": "units", "PayloadConveyor": "distribution",
}


def _family_from_class(base: str):
    if base in _FAMILY_BY_CLASS:
        return _FAMILY_BY_CLASS[base]
    for k, v in _FAMILY_BY_CLASS.items():
        if base.endswith(k):
            return v
    return None


# ---------------------------------------------------------------- normalization


def normalize_consumer(cls: str, blob: str) -> dict:
    f = parse_fields(blob, ",")
    kind = "other"
    short = cls.rsplit(".", 1)[-1]
    if "ConsumeItems" in short or short in ("ConsumeItemList",):
        kind = "item"
    elif "ConsumeLiquids" in short or short in ("ConsumeLiquid", "ConsumeLiquidBase"):
        kind = "liquid"
    elif short.startswith("ConsumePower"):
        kind = "power"
    elif "Payload" in short:
        kind = "payload"
    c = {
        "class": short,
        "kind": kind,
        "optional": fbool(f, "optional"),
        "booster": fbool(f, "booster"),
        "items": parse_stacks(f.get("items", "")),
        "liquids": parse_stacks(f.get("liquids", "")),
    }
    # ConsumeLiquid / ConsumeLiquidBase store a single `liquid` + `amount`
    # instead of a LiquidStack[] -- normalise it into the same shape.
    if not c["liquids"] and f.get("liquid"):
        amt = fnum(f, "amount", 0) or 0
        c["liquids"] = [{"kind": "liquid", "name": f["liquid"], "amount": round(float(amt), 4)}]
    if not c["items"] and f.get("item"):
        amt = fnum(f, "amount", 0) or 0
        c["items"] = [{"kind": "item", "name": f["item"], "amount": round(float(amt), 4)}]
    if not kind == "power" and c["liquids"]:
        c["kind"] = "liquid"
    if not kind == "power" and c["items"]:
        c["kind"] = "item"
    for k in ("usage", "capacity", "amount", "maxAmount", "minAmount", "usagePerSecond"):
        if k in f:
            c[k] = fnum(f, k)
    if c["kind"] == "power" and "usage" in c:
        c["usagePerSecond"] = round(c["usage"] * 60.0, 4)
    # keep the raw field map for anything we did not model
    c["raw"] = f
    return c


def normalize_block(bid: int, name: str, cls: str, realcls: str,
                    consumers: list[dict], f: dict[str, str]) -> dict:
    short = cls.rsplit(".", 1)[-1] if cls else ""
    base = realcls.rsplit(".", 1)[-1] if realcls else short.split("$")[0]

    req = parse_stacks(f.get("requirements", ""))
    out_items = parse_stacks(f.get("outputItems", ""))
    out_liquids = parse_stacks(f.get("outputLiquids", ""))
    results = parse_stacks(f.get("results", ""))  # Separator
    craft_time = fnum(f, "craftTime")

    # ---- power
    has_power = fbool(f, "hasPower")
    consumes_power = fbool(f, "consumesPower")
    outputs_power = fbool(f, "outputsPower")
    usage = None
    capacity = None
    for c in consumers:
        if c["kind"] == "power":
            usage = c.get("usage")
            capacity = c.get("capacity")
            break
    power_prod = fnum(f, "powerProduction")
    block = {
        "id": bid,
        "name": name,
        "class": realcls or cls,
        "rawClass": cls,
        "baseClass": base,
        "category": fstr(f, "category", "none"),
        "group": fstr(f, "group", "none"),
        "buildVisibility": fstr(f, "buildVisibility"),
        "size": fnum(f, "size", 1),
        "health": fnum(f, "health", -1),
        "hasPower": has_power,
        "hasItems": fbool(f, "hasItems"),
        "hasLiquids": fbool(f, "hasLiquids"),
        "itemCapacity": fnum(f, "itemCapacity"),
        "liquidCapacity": fnum(f, "liquidCapacity"),
        "rotate": fbool(f, "rotate"),
        "solid": fbool(f, "solid"),
        "underBullets": fbool(f, "underBullets"),
        "squareSprite": fbool(f, "squareSprite", True),
        "requirements": req,
        "consumers": consumers,
        "power": {
            # Block.consumesPower defaults to TRUE and is meaningless on its own
            # (Block.java:53).  Real consumers are blocks that carry a ConsumePower.
            "consumesPower": usage is not None,
            "outputsPower": outputs_power,
            "hasPower": has_power,
            "usage": usage,                       # per tick (game internal unit)
            "usagePerSecond": None if usage is None else round(float(usage) * 60.0, 4),
            "capacity": capacity,
            "powerProduction": power_prod,        # per tick
            "productionPerSecond": None if power_prod is None else round(float(power_prod) * 60.0, 4),
        },
        "recipe": None,
    }

    # ---- recipe
    recipe_inputs = [c for c in consumers if c["kind"] in ("item", "liquid")]
    if craft_time or out_items or out_liquids or results:
        ct = fnum(f, "craftTime", 0) or 0
        cycles = round(60.0 / ct, 6) if ct else None
        r = {
            "craftTime": ct,
            "cyclesPerSecond": cycles,
            "inputs": recipe_inputs,
            "outputItems": out_items,
            "outputLiquids": out_liquids,
        }
        if results:
            r["results"] = results
            r["resultsSemantics"] = "one random result per craft, weighted by amount"
        if cycles and out_items:
            r["outputItemsPerSecond"] = [
                {"kind": "item", "name": s["name"], "amount": round(s["amount"] * cycles, 6)}
                for s in out_items]
        if cycles and out_liquids:
            r["outputLiquidsPerSecond"] = [
                {"kind": "liquid", "name": s["name"], "amount": round(s["amount"] * cycles, 6)}
                for s in out_liquids]
        block["recipe"] = r

    # ---- family classification -------------------------------------------------
    # Content classes in a server jar are obfuscated/anonymous (mindustry.content.Blocks$128),
    # so we classify by *field signature* instead of class name.  Version-proof.
    family = _family_from_class(base) or "block"
    if family == "block" and ("drillTime" in f or "hardnessDrillMultiplier" in f):
        family = "drill"
    elif family == "block" and (f.get("isDuct") == "1" or "Duct" in base):
        family = "duct"
    elif family == "block" and ("displayedSpeed" in f or ("speed" in f and "itemCapacity" in f)):
        family = "conveyor"
    elif family == "block" and ("laserRange" in f or "maxNodes" in f):
        family = "powerNode"
    elif family == "block" and "pumpAmount" in f:
        family = "pump"
    elif family == "block" and "powerProduction" in f:
        family = "generator"
    elif family == "block" and "results" in f:
        family = "separator"
    elif family == "block" and ("Conduit" in base or "LiquidBridge" in base):
        family = "conduit"
    elif family == "block" and craft_time:
        family = "crafter"
    elif family == "block" and "liquidCapacity" in f and fnum(f, "liquidCapacity", 0) and not craft_time:
        family = "liquidBlock"
    block["family"] = family

    # ---- drill family
    if family == "drill":
        dt = fnum(f, "drillTime")
        hdm = fnum(f, "hardnessDrillMultiplier")
        size = block["size"] or 1
        block["drill"] = {
            "tier": fnum(f, "tier"),
            "drillTime": dt,
            "hardnessDrillMultiplier": hdm,
            "liquidBoostIntensity": fnum(f, "liquidBoostIntensity"),
            "blockedItem": fstr(f, "blockedItem"),
            "outputItem": fstr(f, "outputItem"),
            "baseRateItemsPerSecond": None if not dt else round(60.0 / dt * size * size, 6),
            "formula": "drillTime(item) = (drillTime + hardnessDrillMultiplier*item.hardness)/drillMultiplier; "
                       "rate(items/s) = coveredOreTiles * 60/drillTime(item) * size^2 (see Drill.java)",
        }

    # ---- conveyor family
    if family == "conveyor":
        sp = fnum(f, "speed")
        ds = fnum(f, "displayedSpeed")
        block["conveyor"] = {
            "speed": sp,
            "displayedSpeed": ds,
            "itemsPerSecond": ds,          # displayedSpeed == items/s as shown by the game
            "itemCapacity": block["itemCapacity"],
            "rateNote": "speed is tiles/tick (x60 = tiles/s); displayedSpeed is the in-game items/s stat",
        }
    elif family in ("duct",):
        block["conveyor"] = {
            "speed": fnum(f, "speed"),
            "displayedSpeed": fnum(f, "displayedSpeed"),
            "itemsPerSecond": fnum(f, "speed"),   # Duct.speed is already items/s
            "itemCapacity": block["itemCapacity"],
            "rateNote": "Duct.speed is items/s (different unit from Conveyor.speed)",
        }

    # ---- conduit / pump / bridge / node logistics extras
    logi = {}
    for k in ("laserRange", "maxNodes", "range", "transportTime", "liquidPressure",
              "pumpAmount", "liquidMultiplier", "consumesLiquid", "outputLiquid",
              "itemDrop", "liquidDrop", "wallOre", "isLiquid", "oreDefault",
              "bridgeWidth", "reload", "shots", "inaccuracy", "rotateSpeed"):
        if k in f:
            v = f[k]
            logi[k] = v if v in ("1", "0") else (fnum(f, k) if _isnum(v) else v)
    if logi:
        block["logisticsExtras"] = logi

    block["raw"] = f
    return block


def _isnum(v: str) -> bool:
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


# ---------------------------------------------------------------- main


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jar", default=DEFAULT_JAR)
    ap.add_argument("--java", default=DEFAULT_JAVA)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--keep-run", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.jar):
        print(f"missing jar: {args.jar}", file=sys.stderr)
        return 2
    if not os.path.exists(args.java):
        print(f"missing java: {args.java}", file=sys.stderr)
        return 2

    runbase = os.path.join(HERE, "_run")
    os.makedirs(runbase, exist_ok=True)
    workdir = tempfile.mkdtemp(prefix="dump-", dir=runbase)

    t0 = time.time()
    srv = Server(args.java, args.jar, workdir)
    try:
        meta_lines = srv.js(JS_META)
        items_lines = srv.js(JS_ITEMS)
        liquids_lines = srv.js(JS_LIQUIDS)
        # The server console caps how much output a single `js` command may
        # produce (~10k lines), so dump blocks in slices.
        _meta = [ln for ln in meta_lines if ln.startswith("META|")]
        _mf = parse_fields(_meta[0].split("|", 1)[1]) if _meta else {}
        total = int(float(_mf.get("contentBlocks", 447)))
        blocks_lines: list[str] = []
        step = 50
        for st in range(0, total, step):
            en = min(st + step, total)
            chunk = srv.js(JS_BLOCKS % (st, en), needle="SDONE")
            blocks_lines += chunk
            print(f"  blocks {st}..{en - 1}: {len(chunk)} lines", file=sys.stderr)
    finally:
        srv.close()
        if not args.keep_run:
            shutil.rmtree(workdir, ignore_errors=True)
    elapsed = time.time() - t0

    def keep(lines, tag):
        return [ln for ln in lines if ln.startswith(tag)]

    meta = parse_fields("".join(keep(meta_lines, "META|")).split("|", 1)[1]) if keep(meta_lines, "META|") else {}

    items = []
    for ln in keep(items_lines, "IT|"):
        _, iid, name, blob = ln.split("|", 3)
        f = parse_fields(blob, "\t")
        items.append({
            "id": int(iid), "name": name,
            "color": fstr(f, "color"),
            "hardness": fnum(f, "hardness", 0),
            "cost": fnum(f, "cost"),
            "explosiveness": fnum(f, "explosiveness", 0),
            "flammability": fnum(f, "flammability", 0),
            "radioactivity": fnum(f, "radioactivity", 0),
            "charge": fnum(f, "charge", 0),
            "lowPriority": fbool(f, "lowPriority"),
            "raw": f,
        })

    liquids = []
    for ln in keep(liquids_lines, "LQ|"):
        _, lid, name, blob = ln.split("|", 3)
        f = parse_fields(blob, "\t")
        liquids.append({
            "id": int(lid), "name": name,
            "color": fstr(f, "color"),
            "heatCapacity": fnum(f, "heatCapacity", 0),
            "viscosity": fnum(f, "viscosity", 0),
            "temperature": fnum(f, "temperature", 0),
            "flammability": fnum(f, "flammability", 0),
            "explosiveness": fnum(f, "explosiveness", 0),
            "gas": fbool(f, "gas"),
            "raw": f,
        })

    blocks = []
    heads: dict[int, dict] = {}
    for ln in blocks_lines:
        if ln.startswith("BH|"):
            _, bid, name, cls, realcls = ln.split("|", 4)
            rec = {"id": int(bid), "name": name, "class": cls,
                   "realClass": realcls, "consumers": [], "fields": {}}
            heads[rec["id"]] = rec
        elif ln.startswith("BC|"):
            _, bid, blob = ln.split("|", 2)
            rec = heads.get(int(bid))
            if not rec:
                continue
            ccls, _, cblob = blob.partition("~")
            try:
                rec["consumers"].append(normalize_consumer(ccls, cblob))
            except Exception as exc:  # never let one bad consume kill the dump
                rec["consumers"].append({"class": ccls, "kind": "other", "error": str(exc)})
        elif ln.startswith("BF|"):
            _, bid, kv = ln.split("|", 2)
            rec = heads.get(int(bid))
            if rec and "=" in kv:
                k, _, v = kv.partition("=")
                rec["fields"][k.strip()] = v
    for bid in sorted(heads):
        rec = heads[bid]
        blocks.append(normalize_block(bid, rec["name"], rec["class"], rec["realClass"],
                                      rec["consumers"], rec["fields"]))

    data = {
        "meta": {
            "source": "mindustry official server jar, Rhino reflection dump",
            "jar": os.path.basename(args.jar),
            "jarBytes": os.path.getsize(args.jar),
            "gameVersion": (meta.get("modifier") + "-" + meta.get("build", "?")),
            "versionBuild": meta.get("build"),
            "versionModifier": meta.get("modifier"),
            "buildDate": meta.get("buildDate"),
            "dumpSeconds": round(elapsed, 1),
            "counts": {
                "items": len(items), "liquids": len(liquids), "blocks": len(blocks),
            },
        },
        "items": items,
        "liquids": liquids,
        "blocks": blocks,
        "environment": {
            # floor blocks that yield a resource: the ore a drill mines, or the
            # liquid a pump can draw (Drill.canMine uses Floor.itemDrop).
            "oreBlocks": [{"block": b["name"], "item": b["raw"]["itemDrop"]}
                          for b in blocks if b["raw"].get("itemDrop")],
            "liquidBlocks": [{"block": b["name"], "liquid": b["raw"]["liquidDrop"]}
                             for b in blocks if b["raw"].get("liquidDrop")],
        },
    }

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)

    # ---- coverage report printed to stdout (feeds the report)
    cov = coverage(blocks)
    print(json.dumps({"meta": data["meta"], "coverage": cov}, ensure_ascii=False, indent=2))
    print(f"\nwrote {args.out} ({os.path.getsize(args.out)} bytes) in {elapsed:.1f}s")
    return 0


def coverage(blocks: list[dict]) -> dict:
    n = len(blocks)
    def has(pred):
        return sum(1 for b in blocks if pred(b))

    crafters = [b for b in blocks if b["recipe"]]
    with_outputs = [b for b in crafters if b["recipe"]["outputItems"] or b["recipe"]["outputLiquids"] or b["recipe"].get("results")]
    with_inputs = [b for b in crafters if b["recipe"]["inputs"]]
    full = [b for b in crafters if b["recipe"]["craftTime"] and b["recipe"]["inputs"]
            and (b["recipe"]["outputItems"] or b["recipe"]["outputLiquids"] or b["recipe"].get("results"))]
    fams: dict[str, int] = {}
    for b in blocks:
        fams[b["family"]] = fams.get(b["family"], 0) + 1
    return {
        "blocks": n,
        "withCraftTime": sum(1 for b in blocks if b["recipe"] and b["recipe"]["craftTime"]),
        "withRecipeObject": len(crafters),
        "withOutputs": len(with_outputs),
        "withInputs": len(with_inputs),
        "fullRecipe": len(full),          # craftTime + inputs + outputs
        "withRequirements": has(lambda b: bool(b["requirements"])),
        "hasPower": has(lambda b: b["hasPower"]),
        "consumesPower": has(lambda b: b["power"]["consumesPower"]),
        "outputsPower": has(lambda b: b["power"]["outputsPower"]),
        "powerUsageValue": has(lambda b: b["power"]["usage"] is not None),
        "powerProductionValue": has(lambda b: b["power"]["powerProduction"]),
        "drills": has(lambda b: b.get("drill") is not None),
        "drillsWithTier": has(lambda b: b.get("drill") and b["drill"]["tier"] is not None),
        "conveyors": has(lambda b: b.get("conveyor") is not None),
        "conveyorsWithRate": has(lambda b: b.get("conveyor") and b["conveyor"].get("itemsPerSecond")),
        "rotatable": has(lambda b: b["rotate"]),
        "hasLiquids": has(lambda b: b["hasLiquids"]),
        "itemDrop": has(lambda b: b["raw"].get("itemDrop")),
        "liquidDrop": has(lambda b: b["raw"].get("liquidDrop")),
        "familyCounts": fams,
    }


if __name__ == "__main__":
    sys.exit(main())

