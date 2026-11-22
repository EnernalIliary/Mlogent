"""Scene files: one JSON description, reproduced in two hosts.

A scene is the contract between `tools/mlogsim.py` (offline: fast ticks,
itrace, variable dumps) and `tools/world_server.py` (live: a real host players
can join). Both apply the same file, so a run verified in the simulator can be
replayed in the world without re-typing coordinates.

Schema (v1) -- every key optional except "buildings"/"units":

{
  "name": "v27 rig",
  "version": 1,
  "world": {"size": 64, "rules": {"infiniteResources": true, "waves": false,
                                  "canGameOver": false, "logicUnitControl": true,
                                  "allowEditWorldProcessors": true,
                                  "possessionAllowed": true}},
  "clear": [30, 59, 14, 6],
  "buildings": [
    {"block": "micro-processor", "x": 30, "y": 60, "name": "proc",
     "code": "Logic/unit-haul-v27.mlog",
     "links": ["container2", "container1", "sorter1"]},
    {"block": "sorter", "x": 31, "y": 60, "name": "sorter1",
     "config": {"item": "copper"}},
    {"block": "container", "x": 33, "y": 60, "name": "container1",
     "items": {"copper": 90}}
  ],
  "units": [{"type": "poly", "count": 8, "team": "sharded",
             "at": [31, 61], "radius": 2}],
  "checks": [{"logic": "proc", "var": "N", "equals": 8}]
}

Coordinates are the tile handed to Tile.setBlock/setNet: a multi-block is
CENTERED on it (Tile.java:255-288), so a 2x2 container at (33,60) covers
33..34 x 60..61. Every placement echoes tile.build.tile (the origin) in the
report, so an off-by-one is visible instead of silent.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROJECT_KEYS = {"units", "anchor", "at"}


def _xy(v, what):
    """[x, y] (tiles) or None."""
    if v is None:
        return None
    if not (isinstance(v, list) and len(v) == 2):
        raise SceneError("%s must be [x, y]" % what)
    return [int(v[0]), int(v[1])]


TOP_KEYS = {"name", "version", "notes", "world", "clear", "buildings", "units",
            "checks", "project", "frame"}
BUILDING_KEYS = {"block", "x", "y", "name", "team", "enabled", "config", "items",
                 "liquids", "health", "rotation", "code", "code_inline", "links"}
UNIT_KEYS = {"type", "count", "team", "at", "radius"}
DEFAULT_RULES = {
    "infiniteResources": True,
    "waves": False,
    "canGameOver": False,
    "logicUnitControl": True,
    "allowEditWorldProcessors": True,
    "possessionAllowed": True,
}


class SceneError(ValueError):
    pass


# ---------------------------------------------------------------- loading

def _abs(path: str, base: str = ROOT) -> str:
    if not path:
        return path
    return path if os.path.isabs(path) else os.path.join(base, path)


def load(path: str, base: str | None = None, *, workspace_root: str | None = None,
         inline_only: bool = False) -> dict:
    """Read a scene file, with optional containment for server-side references."""
    base = base or ROOT
    full = _abs(path, base)
    root = Path(workspace_root).resolve() if workspace_root is not None else None
    if root is not None:
        resolved = Path(full).resolve()
        if not resolved.is_relative_to(root) or resolved.suffix.lower() != ".json":
            raise SceneError("scene must be a .json file within the server workspace")
        full = str(resolved)
    if not os.path.exists(full):
        raise SceneError("scene not found: %s" % full)
    with open(full, encoding="utf-8-sig") as fh:
        raw = json.load(fh)
    if not isinstance(raw, dict):
        raise SceneError("scene must be a JSON object")

    unknown = set(raw) - TOP_KEYS
    if unknown:
        raise SceneError("unknown top-level key(s): %s" % ", ".join(sorted(unknown)))

    sc = {
        "name": raw.get("name") or os.path.splitext(os.path.basename(full))[0],
        "version": int(raw.get("version") or 1),
        "path": full,
        "dir": os.path.dirname(full),
        "notes": raw.get("notes") or "",
        "world": {},
        "clear": None,
        "buildings": [],
        "units": [],
        "checks": [],
        "project": None,
        "frame": None,
    }
    if inline_only:
        sc["inline_only"] = True
    if raw.get("frame"):
        frame = raw["frame"]
        if not (isinstance(frame, list) and len(frame) == 4):
            raise SceneError("frame must be [x, y, w, h]")
        sc["frame"] = [int(v) for v in frame]

    world = raw.get("world") or {}
    if not isinstance(world, dict):
        raise SceneError("world must be an object")
    rules = world.get("rules", {})
    if not isinstance(rules, dict):
        raise SceneError("world.rules must be an object")
    for key, value in rules.items():
        if (not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", key)
                or type(value) not in (bool, int, float)
                or (type(value) is float and not math.isfinite(value))):
            raise SceneError("world.rules requires rule names and boolean or finite numeric values")
    sc["world"] = {
        "size": int(world.get("size") or 64),
        "rules": {**DEFAULT_RULES, **rules},
    }

    if raw.get("clear"):
        clear = raw["clear"]
        if not (isinstance(clear, list) and len(clear) == 4):
            raise SceneError("clear must be [x, y, w, h]")
        sc["clear"] = [int(v) for v in clear]
        x, y, w, h = sc["clear"]
        size = sc["world"]["size"]
        if inline_only and not (0 <= x <= x + w <= size and 0 <= y <= y + h <= size):
            raise SceneError("uploaded scene clear rectangle must fit within the world")

    by_name: dict[str, dict] = {}
    for i, b in enumerate(raw.get("buildings") or []):
        if not isinstance(b, dict) or not b.get("block") or b.get("x") is None or b.get("y") is None:
            raise SceneError("buildings[%d] needs block/x/y" % i)
        unknown = set(b) - BUILDING_KEYS
        if unknown:
            raise SceneError("buildings[%d] has unknown key(s): %s" % (i, ", ".join(sorted(unknown))))
        name = b.get("name") or ("b%d" % i)
        if inline_only and (not isinstance(name, str) or not name.isprintable() or len(name) > 128):
            raise SceneError("uploaded scene building names must be printable and at most 128 characters")
        if name in by_name:
            raise SceneError("duplicate building name: %s" % name)
        code_text = None
        code_src = None
        if inline_only and "code" in b:
            raise SceneError("uploaded scene buildings must use code_inline instead of file references")
        if b.get("code_inline") is not None:
            if inline_only and (not isinstance(b["code_inline"], str)
                    or len(b["code_inline"].encode("utf-8")) > 100 * 1024):
                raise SceneError("uploaded scene code_inline must be text of at most 100 KiB")
            code_text = str(b["code_inline"])
            code_src = "inline"
        elif b.get("code"):
            # relative paths are tried against the scene's own folder first, then
            # against the repo root, so "Logic/x.mlog" works from scenes/*.json
            raw_code = str(b["code"])
            cands = [_abs(raw_code, sc["dir"])] if not os.path.isabs(raw_code) else [raw_code]
            if not os.path.isabs(raw_code):
                cands.append(_abs(raw_code, ROOT))
            if root is not None:
                guarded = []
                for candidate in cands:
                    resolved = Path(candidate).resolve()
                    if resolved.is_relative_to(root) and resolved.suffix.lower() == ".mlog":
                        guarded.append(str(resolved))
                if not guarded:
                    raise SceneError("scene code must be a .mlog file within the server workspace")
                cands = guarded
            code_src = next((c for c in cands if os.path.exists(c)), None)
            if code_src is None:
                raise SceneError("buildings[%d] (%s): code not found, tried: %s"
                                 % (i, name, ", ".join(cands)))
            if root is not None:
                source = Path(code_src)
                if not source.is_file():
                    raise SceneError("scene code must be a regular .mlog file")
                if source.stat().st_size > 100 * 1024:
                    raise SceneError("scene code exceeds the 100 KiB input limit")
            with open(code_src, encoding="utf-8-sig") as fh:
                code_text = fh.read()
        ent = {
            "block": str(b["block"]),
            "x": int(b["x"]),
            "y": int(b["y"]),
            "name": name,
            "team": str(b.get("team") or "sharded"),
            "enabled": bool(b.get("enabled", True)),
            "enabled_explicit": "enabled" in b,
            "config": b.get("config") or None,
            "items": {str(k): int(v) for k, v in (b.get("items") or {}).items()},
            "liquids": {str(k): float(v) for k, v in (b.get("liquids") or {}).items()},
            "health": (float(b["health"]) if b.get("health") is not None else None),
            "rotation": int(b.get("rotation") or 0) % 4,
            "code": code_text,
            "code_src": code_src,
            "links": [str(v) for v in (b.get("links") or [])],
        }
        if ent["config"] is not None:
            if not isinstance(ent["config"], dict) or not ("item" in ent["config"] or "value" in ent["config"]):
                raise SceneError("buildings[%d] (%s): config needs 'item' or 'value'" % (i, name))
        by_name[name] = ent
        sc["buildings"].append(ent)

    for ent in sc["buildings"]:
        for ln in ent["links"]:
            if ln not in by_name:
                raise SceneError("%s links to unknown building %r" % (ent["name"], ln))

    for i, u in enumerate(raw.get("units") or []):
        if not isinstance(u, dict) or not u.get("type"):
            raise SceneError("units[%d] needs type" % i)
        unknown = set(u) - UNIT_KEYS
        if unknown:
            raise SceneError("units[%d] has unknown key(s): %s" % (i, ", ".join(sorted(unknown))))
        at = u.get("at")
        if at is not None and not (isinstance(at, list) and len(at) == 2):
            raise SceneError("units[%d].at must be [x, y]" % i)
        sc["units"].append({
            "type": str(u["type"]),
            "count": int(u.get("count") or 1),
            "team": str(u.get("team") or "sharded"),
            "at": [int(at[0]), int(at[1])] if at else None,
            "radius": float(u.get("radius", 2)),
        })

    for i, c in enumerate(raw.get("checks") or []):
        if not isinstance(c, dict) or not c.get("logic") or not c.get("var"):
            raise SceneError("checks[%d] needs logic/var" % i)
        if c["logic"] not in by_name:
            raise SceneError("checks[%d]: unknown logic %r" % (i, c["logic"]))
        if "equals" not in c:
            raise SceneError("checks[%d] needs equals" % i)
        sc["checks"].append({"logic": c["logic"], "var": str(c["var"]),
                             "equals": c["equals"], "op": str(c.get("op") or "eq")})

    proj = raw.get("project")
    if proj is not None:
        if not isinstance(proj, dict):
            raise SceneError("project must be an object")
        unknown = set(proj) - PROJECT_KEYS
        if unknown:
            raise SceneError("project has unknown key(s): %s" % ", ".join(sorted(unknown)))
        units_mode = str(proj.get("units") or "mirror")
        if units_mode not in ("mirror", "spawn"):
            raise SceneError("project.units must be mirror|spawn")
        anchor = _xy(proj.get("anchor"), "project.anchor")
        where = _xy(proj.get("at"), "project.at")
        sc["project"] = {"units": units_mode, "anchor": anchor, "at": where}

    errors = validate(sc)
    if (root is not None or inline_only) and sum(u["count"] for u in sc["units"]) > 64:
        errors.append("at most 64 units can be spawned by an MCP scene")
    if errors:
        raise SceneError("; ".join(errors))
    return sc


def validate(sc: dict) -> list[str]:
    errs = []
    size = sc["world"]["size"]
    if not (8 <= size <= 1024):
        errs.append("world.size must be 8..1024, got %d" % size)
    if not sc["buildings"] and not sc["units"]:
        errs.append("scene is empty (no buildings, no units)")
    for b in sc["buildings"]:
        if not (0 <= b["x"] < size and 0 <= b["y"] < size):
            errs.append("%s at (%d,%d) is outside the %dx%d world"
                        % (b["name"], b["x"], b["y"], size, size))
    for u in sc["units"]:
        if u["count"] < 1:
            errs.append("unit %s count must be >= 1" % u["type"])
        if u["at"] and not (0 <= u["at"][0] < size and 0 <= u["at"][1] < size):
            errs.append("unit %s spawn (at) is outside the world" % u["type"])
    return errs


def summary(sc: dict) -> str:
    lines = ["scene   %s  (v%d)" % (sc["name"], sc["version"]),
             "world   %dx%d  rules=%s" % (sc["world"]["size"], sc["world"]["size"],
                                          ",".join(k for k, v in sc["world"]["rules"].items() if v)),
             "build   %d" % len(sc["buildings"])]
    for b in sc["buildings"]:
        bits = [b["block"], "(%d,%d)" % (b["x"], b["y"]), "name=" + b["name"]]
        if b["links"]:
            bits.append("links=" + ",".join(b["links"]))
        if b["config"]:
            bits.append("cfg=" + json.dumps(b["config"], ensure_ascii=False))
        if b["items"]:
            bits.append("items=" + json.dumps(b["items"], ensure_ascii=False))
        if b["code"]:
            bits.append("code=%d chars" % len(b["code"]))
        lines.append("  - " + "  ".join(bits))
    for u in sc["units"]:
        lines.append("  - %s x%d @%s r%.1f" % (u["type"], u["count"],
                                               u["at"] or "auto", u["radius"]))
    if sc["checks"]:
        lines.append("checks  %d" % len(sc["checks"]))
        for c in sc["checks"]:
            lines.append("  - %s.%s == %r" % (c["logic"], c["var"], c["equals"]))
    return "\n".join(lines)


# ---------------------------------------------------------------- JS build

def _js_str(v: str) -> str:
    return json.dumps(v, ensure_ascii=False)


def _js_path(p: str) -> str:
    return _js_str(p.replace("\\", "/"))


def _rules_js(rules: dict) -> str:
    out = []
    for k, v in rules.items():
        out.append("R.%s=%s;" % (k, "true" if v is True else "false" if v is False else v))
    return "".join(out)


_SIM_PRELUDE = (
    "var WT=Vars.world,TA=Packages.mindustry.game.Team.all,AIR=Vars.content.block('air');"
    "var LL=Packages.mindustry.world.blocks.logic.LogicBlock.LogicLink;"
    "function teamOf(n){for(var i=0;i<TA.length;i++){if(TA[i].name==n)return TA[i];}return null;}"
    "function bAt(x,y){var t=WT.tile(x,y);return t==null?null:t.build;}"
)

_WORLD_PRELUDE = (
    "var WT=Vars.world,TA=Packages.mindustry.game.Team.all,AIR=Vars.content.block('air');"
    "var LL=Packages.mindustry.world.blocks.logic.LogicBlock.LogicLink;"
    "function teamOf(n){for(var i=0;i<TA.length;i++){if(TA[i].name==n)return TA[i];}return null;}"
    "function bAt(x,y){var t=WT.tile(x,y);return t==null?null:t.build;}"
)


def _js_rep(flavor: str, parts: list) -> str:
    """One report line. parts are JS expressions (string literals or raw)."""
    if flavor == "sim":
        return "print(%s);" % " + ".join(parts)
    return "sb.append(%s).append('\\n');" % ").append(".join(parts)


def _js_err(flavor: str, tag: str) -> str:
    return _js_rep(flavor, [_js_str("ERR\t" + tag + ": "), "e"])


def _guard(flavor: str, tag: str, body: str) -> str:
    return "try{%s}catch(e){%s}" % (body, _js_err(flavor, tag))


# Statement order matters: every building must exist before anything points at
# it, so placement runs first, config/items second, links+code third, units last.

def _place_stmt(flavor: str, b: dict) -> str:
    put = "setNet" if flavor == "world" else "setBlock"
    extra = ""
    if b.get("health"):
        extra += "b.health=%s;" % repr(float(b["health"]))
    if b.get("liquids"):
        extra += "".join("b.liquids.add(Vars.content.liquid(%s),%s);"
                         % (_js_str(name), repr(float(amt)))
                         for name, amt in b["liquids"].items())
    body = (
        "var tt=WT.tile(%d,%d);"
        "tt.%s(Vars.content.block(%s),teamOf(%s),%d);"
        "var b=tt.build;"
        "if(b==null){%s}"
        "else if(b.block.name!=%s){%s}"
        "else{b.enabled=%s;"
        "if(b.block instanceof Packages.mindustry.world.blocks.storage.CoreBlock){Vars.indexer.addIndex(tt);}"
        "%s"
        "%s}"
        % (b["x"], b["y"], put, _js_str(b["block"]), _js_str(b["team"]),
           int(b.get("rotation") or 0),
           _js_rep(flavor, [_js_str("ERR\tplace %s: no build" % b["name"])]),
           _js_str(b["block"]),
           _js_rep(flavor, [_js_str("ERR\tplace %s: wanted %s, got " % (b["name"], b["block"])),
                            "b.block.name"]),
           "true" if b["enabled"] else "false",
           extra,
           _js_rep(flavor, [_js_str("B\t%s\t" % b["name"]), "b.block.name",
                            "'\t'", "b.tile.x", "'\t'", "b.tile.y"]))
    )
    return _guard(flavor, "place %s (%d,%d)" % (b["name"], b["x"], b["y"]), body)


def _config_stmt(flavor: str, b: dict) -> str:
    cfg = b["config"]
    if "item" in cfg:
        if flavor == "world":
            # configureAny() = Call.tileConfig(null, self(), value): 服务端本地生效
            # **并且广播**给客户端. 直接调 config handler 只改服务端副本, 玩家眼里那台
            # 建筑还是没配过的样子(之前"建筑改动没有同步"就是这个).
            inner = ("try{b.configureAny(Vars.content.item(%s));}"
                     "catch(eC){var h=b.block.configurations.get(Packages.mindustry.type.Item);"
                     "if(h==null){throw 'block takes no Item config';}"
                     "h.get(b,Vars.content.item(%s));}" % (_js_str(cfg["item"]),
                                                          _js_str(cfg["item"])))
        else:
            inner = ("var h=b.block.configurations.get(Packages.mindustry.type.Item);"
                     "if(h==null){throw 'block takes no Item config';}"
                     "h.get(b,Vars.content.item(%s));" % _js_str(cfg["item"]))
        desc = "item=" + str(cfg["item"])
    else:
        val = cfg["value"]
        inner = "b.configureAny(%s);" % json.dumps(val, ensure_ascii=False)
        desc = "value=" + json.dumps(val, ensure_ascii=False)
    body = ("var b=bAt(%d,%d);if(b==null){%s}else{%s%s}"
            % (b["x"], b["y"],
               _js_rep(flavor, [_js_str("ERR\tconfig %s: no build" % b["name"])]),
               inner,
               _js_rep(flavor, [_js_str("C\t%s\t" % b["name"]), _js_str(desc)])))
    return _guard(flavor, "config %s" % b["name"], body)


def _items_stmt(flavor: str, b: dict) -> str:
    # A container is stocked *in addition* to whatever it already holds (a sorter
    # may legitimately keep leftovers).  A core is different: its inventory is the
    # experiment's initial condition, and "add" would make every number depend on
    # what the map happened to hold there -- on a live world the same scene gave
    # 120 + 165 where the offline run gave exactly 120.
    reset = ("if(b.block instanceof Packages.mindustry.world.blocks.storage.CoreBlock)"
             "{b.items.clear();}")
    adds = "".join("b.items.add(Vars.content.item(%s),%d);"
                   % (_js_str(item), amount) for item, amount in b["items"].items())
    desc = ",".join("%s=%d" % (item, amount) for item, amount in b["items"].items())
    body = ("var b=bAt(%d,%d);if(b==null){%s}else{%s%s%s}"
            % (b["x"], b["y"],
               _js_rep(flavor, [_js_str("ERR\titems %s: no build" % b["name"])]),
               reset, adds,
               _js_rep(flavor, [_js_str("I\t%s\t" % b["name"]), _js_str(desc)])))
    return _guard(flavor, "items %s" % b["name"], body)


def _code_path(sc: dict, b: dict) -> str:
    """Absolute path the JVM can read, for both flavors."""
    if b.get("code_src") and b["code_src"] != "inline":
        return b["code_src"]
    outdir = sc["dir"] if sc.get("inline_only") else os.path.join(ROOT, "out", "_scene")
    os.makedirs(outdir, exist_ok=True)
    safe = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in b["name"])
    if sc.get("inline_only"):
        safe = str(sc["buildings"].index(b))
    path = os.path.join(outdir, "%s__%s.mlog" % (os.path.splitext(os.path.basename(sc["path"]))[0], safe))
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(b["code"])
    return path


def _looks_labeled(src: str) -> bool:
    for line in src.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("//"):
            continue
        head = s.split(":", 1)
        if len(head) == 2 and head[0] and all(ch.isalnum() or ch in "-_." for ch in head[0]):
            return True
    return False


def _links_stmt(flavor: str, sc: dict, b: dict) -> str:
    by_name = {x["name"]: x for x in sc["buildings"]}
    links_js = "".join("b.links.add(new LL(%d,%d,%s,true));"
                       % (by_name[ln]["x"], by_name[ln]["y"], _js_str(ln))
                       for ln in b["links"])
    parts = ["var b=bAt(%d,%d);" % (b["x"], b["y"]),
             "if(b==null){%s}else{" % _js_rep(flavor, [_js_str("ERR\tlogic %s: no build" % b["name"])]),
             "b.links.clear();", links_js]
    parts.append("var s=Packages.java.nio.file.Files.readString("
                 "Packages.java.nio.file.Paths.get(%s),"
                 "Packages.java.nio.charset.StandardCharsets.UTF_8);" % _js_path(_code_path(sc, b)))
    parts.append("b.code=s;b.updateCode(s);")
    if flavor == "world":
        # 代码同样要广播: setNet 只把方块摆上去, 客户端那台处理器的代码是空的
        # (玩家点开就是空白). configureAny(byte[]) 走 LogicBlock 的
        # config(byte[].class, readCompressed(data, true)) 分支 —— 与游戏里粘贴
        # 同一路径, 两边都拿到同一份压缩代码.
        parts.append("try{var LB=Packages.mindustry.world.blocks.logic.LogicBlock;"
                     "b.configureAny(LB.compress(s,b.relativeConnections()));}catch(eS){}")
        # readCompressed() rebuilds `links` from the payload with findLinkName(),
        # so a link we named "hub" comes back as "shard2" (core-shard -> shard) and
        # the code's `hub` stays null.  Re-attach the scene's names locally and let
        # updateCode() register them as constants -- the broadcast copy is for the
        # player's eyes, the executor here is what the experiment reads.
        parts.append("b.links.clear();" + links_js + "b.code=s;b.updateCode(s);")
    if flavor == "sim":
        # LogicBlock.updateTile() feeds the accumulator with edelta(), which is
        # scaled by efficiency; a paused simulator world never runs update(), so
        # efficiency would stay 0 and the processor would execute zero instructions.
        parts.append("b.executor.team=teamOf(%s);b.efficiency=1;" % _js_str(b["team"]))
    parts.append(_js_rep(flavor, [_js_str("L\t%s\t" % b["name"]), "b.links.size",
                                  _js_str("\t"), "b.code.length"]))
    # report the mapping the executor really built: invalid links are dropped and
    # the rest compact, so getlink indexes can shift without any error.
    parts.append("var e=b.executor;"
                 "for(var i=0;i<e.links.length;i++){%s}"
                 % _js_rep(flavor, [_js_str("K\t%s\t" % b["name"]), "i",
                                    _js_str("\t"), "e.links[i]"]))
    parts.append("if(e.links.length!=%d){%s}"
                 % (len(b["links"]),
                    _js_rep(flavor, [_js_str("ERR\tlogic %s: declared %d links, resolved " % (b["name"], len(b["links"]))),
                                     "e.links.length",
                                     _js_str(" -- a link was out of range or on another team")])))
    parts.append("}")
    return _guard(flavor, "logic %s" % b["name"], "".join(parts))


def _unit_positions(u: dict) -> list:
    """Golden-angle spiral in world units, same shape as world_server SPAWN_JS."""
    at = u.get("at")
    if not at:
        cx, cy = 0.0, 0.0
    else:
        cx, cy = (at[0] + 0.5) * 8.0, (at[1] + 0.5) * 8.0
    count, radius = u["count"], u["radius"]
    out = []
    for i in range(count):
        r = 0.0 if count <= 1 else radius * math.sqrt((i + 0.5) / count) * 8.0
        ang = i * 2.399963229728653
        out.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
    return out


def _unit_stmt(flavor: str, u: dict) -> str:
    spawns = "".join(
        "var u=ut.spawn(teamOf(%s),%.2f,%.2f);if(u!=null){n=n+1;}"
        % (_js_str(u["team"]), wx, wy) for wx, wy in _unit_positions(u))
    err = _js_rep(flavor, [_js_str("ERR\tunits: no unit type " + u["type"])])
    done = _js_rep(flavor, [_js_str("U\t" + u["type"] + "\t"), "n",
                            _js_str("/" + str(u["count"]))])
    body = ("var ut=null;var us=Vars.content.units();"
            "for(var i=0;i<us.size;i++){var c=us.get(i);"
            "if(c.name==" + _js_str(u["type"]) + "){ut=c;break;}}"
            "if(ut==null){" + err + "}else{var n=0;" + spawns +
            "Vars.state.teams.updateTeamStats();" + done + "}")
    return _guard(flavor, "units " + u["type"], body)


def _rules_stmt(sc: dict) -> str:
    rules = sc["world"]["rules"]
    out = ["var R=Vars.state.rules;"]
    for k, v in rules.items():
        out.append("R.%s=%s;" % (k, "true" if v is True else "false" if v is False else v))
    return "".join(out)


def _clear_stmt(flavor: str, clear: list) -> str:
    x, y, w, h = clear
    # world flavor must go through Tile.setNet: it issues Call.setTile, which both
    # applies locally and broadcasts to every client. Plain setBlock only changes
    # the server's own copy -- players keep seeing the old blocks.
    wipe = ("ct.setNet(AIR, Vars.state.rules.defaultTeam, 0)"
            if flavor == "world" else "ct.setBlock(AIR)")
    body = ("for(var cy=%d;cy<%d;cy++){for(var cx=%d;cx<%d;cx++){"
            "var ct=WT.tile(cx,cy);"
            "if(ct!=null&&ct.build!=null&&!(ct.build.block instanceof "
            "Packages.mindustry.world.blocks.storage.CoreBlock)){%s;}}}"
            % (y, y + h, x, x + w, wipe))
    return _guard(flavor, "clear %d,%d %dx%d" % (x, y, w, h), body)


def anchor_of(sc: dict) -> list:
    """Scene tile that the world-side 'at' point maps onto."""
    proj = sc.get("project") or {}
    if proj.get("anchor"):
        return list(proj["anchor"])
    if sc["clear"]:
        x, y, w, h = sc["clear"]
        return [x + w // 2, y + h // 2]
    if sc["buildings"]:
        xs = [b["x"] for b in sc["buildings"]]
        ys = [b["y"] for b in sc["buildings"]]
        return [(min(xs) + max(xs)) // 2, (min(ys) + max(ys)) // 2]
    return [0, 0]


def frame_of(sc: dict) -> list:
    """Bounding rectangle [x, y, w, h] of a scene, in scene tiles.

    Explicit "frame" wins. Otherwise it is the union of the clear rect and the
    building/unit bounding boxes (plus a 1-tile margin), so a scene file never
    has to repeat its own coordinates twice.
    """
    if sc.get("frame"):
        return list(sc["frame"])
    box = None
    if sc["clear"]:
        x, y, w, h = sc["clear"]
        box = [x, y, x + w - 1, y + h - 1]
    pts = [(b["x"], b["y"]) for b in sc["buildings"]]
    for u in sc["units"]:
        if u.get("at"):
            r = int(u.get("radius") or 0) + 1
            pts += [(u["at"][0] - r, u["at"][1] - r), (u["at"][0] + r, u["at"][1] + r)]
    for px, py in pts:
        if box is None:
            box = [px, py, px, py]
        else:
            box = [min(box[0], px), min(box[1], py), max(box[2], px), max(box[3], py)]
    if box is None:
        return [0, 0, 1, 1]
    m = 1
    x0, y0, x1, y1 = box[0] - m, box[1] - m, box[2] + m, box[3] + m
    return [x0, y0, x1 - x0 + 1, y1 - y0 + 1]


def translate(sc: dict, dx: int, dy: int) -> dict:
    """Copy of the scene moved by (dx, dy) tiles; buildings/clear/units all follow."""
    out = dict(sc)
    out["buildings"] = [dict(b, x=b["x"] + dx, y=b["y"] + dy) for b in sc["buildings"]]
    out["clear"] = ([sc["clear"][0] + dx, sc["clear"][1] + dy, sc["clear"][2], sc["clear"][3]]
                    if sc["clear"] else None)
    out["units"] = [dict(u, at=([u["at"][0] + dx, u["at"][1] + dy] if u["at"] else None))
                    for u in sc["units"]]
    # project.anchor / project.at 也是格坐标: 跟着一起搬, 否则 anchor_of() 会
    # 还指着老位置, 世界侧按老锚点算位移就会把整块沙盘摆歪.
    proj = dict(sc["project"]) if sc.get("project") else None
    if proj:
        if proj.get("anchor"):
            proj["anchor"] = [int(proj["anchor"][0]) + dx, int(proj["anchor"][1]) + dy]
        if proj.get("at"):
            proj["at"] = [int(proj["at"][0]) + dx, int(proj["at"][1]) + dy]
    out["project"] = proj
    out["frame"] = ([sc["frame"][0] + dx, sc["frame"][1] + dy, sc["frame"][2], sc["frame"][3]]
                    if sc.get("frame") else None)
    out["shift"] = [dx, dy]
    return out


def project_units(sc: dict) -> bool:
    """True when units are drawn as markers instead of being spawned."""
    proj = sc.get("project") or {}
    return str(proj.get("units") or "mirror") == "mirror"


def build_js(flavor: str, sc: dict) -> str:
    """Return one JS body applying the scene. No '//' comments -- both hosts fold lines."""
    if flavor not in ("sim", "world"):
        raise SceneError("flavor must be sim|world")
    out = [_SIM_PRELUDE if flavor == "sim" else _WORLD_PRELUDE, _rules_stmt(sc)]
    if sc["clear"]:
        out.append(_clear_stmt(flavor, sc["clear"]))
    for b in sc["buildings"]:
        out.append(_place_stmt(flavor, b))
    for b in sc["buildings"]:
        if b["config"]:
            out.append(_config_stmt(flavor, b))
        if b["items"]:
            out.append(_items_stmt(flavor, b))
    for b in sc["buildings"]:
        if b["code"]:
            out.append(_links_stmt(flavor, sc, b))
    skip_units = flavor == "world" and project_units(sc)
    if not skip_units:
        for u in sc["units"]:
            out.append(_unit_stmt(flavor, u))
    if flavor == "sim":
        # the simulator's tick loop drives one processor by default; publish the
        # scene's own processors so run_mlog() can updateTile() them too
        procs = [b for b in sc["buildings"] if b["code"]]
        if procs:
            # Rhino (the headless console) has no globalThis; a top-level var is global
            out.append("var PROCS=[%s];"
                       % ",".join("bAt(%d,%d)" % (b["x"], b["y"]) for b in procs))
    out.append(_js_rep(flavor, [_js_str("DONE\t%s" % sc["name"])]))
    return "".join(out)


# ---------------------------------------------------------------- apply

def parse(lines: list) -> dict:
    rep = {"placed": 0, "configured": 0, "stocked": 0, "linked": 0, "units": 0,
           "errors": [], "rows": [], "done": False}
    for ln in lines:
        parts = str(ln).split("\t")
        kind = parts[0]
        if kind == "B" and len(parts) >= 5:
            rep["placed"] += 1
            rep["rows"].append({"kind": "building", "name": parts[1], "block": parts[2],
                                "x": int(float(parts[3])), "y": int(float(parts[4]))})
        elif kind == "C" and len(parts) >= 3:
            rep["configured"] += 1
            rep["rows"].append({"kind": "config", "name": parts[1], "config": parts[2]})
        elif kind == "I" and len(parts) >= 3:
            rep["stocked"] += 1
            rep["rows"].append({"kind": "items", "name": parts[1], "items": parts[2]})
        elif kind == "L" and len(parts) >= 4:
            rep["linked"] += 1
            rep["rows"].append({"kind": "logic", "name": parts[1],
                                "links": int(float(parts[2])), "bytes": int(float(parts[3]))})
        elif kind == "K" and len(parts) >= 4:
            rep.setdefault("linkmap", {}).setdefault(parts[1], []).append(parts[3])
            rep["rows"].append({"kind": "link", "name": parts[1],
                                "index": int(float(parts[2])), "target": parts[3]})
        elif kind == "U" and len(parts) >= 3:
            n = int(float(parts[2].split("/")[0]))
            rep["units"] += n
            rep["rows"].append({"kind": "units", "type": parts[1], "spawned": n})
        elif kind == "ERR":
            rep["errors"].append(parts[1] if len(parts) > 1 else ln)
        elif kind == "DONE":
            rep["done"] = True
    if not rep["done"] and not rep["errors"]:
        rep["errors"].append("scene script did not reach DONE (host folded or threw early)")
    return rep


def warn_labeled(sc: dict) -> list:
    out = []
    for b in sc["buildings"]:
        if b["code"] and _looks_labeled(b["code"]):
            out.append("%s: source has labels -- fine in the world, but mlogsim "
                       "counts file lines as pc, so @counter dispatch will misalign; "
                       "use the numbered .mlog" % b["name"])
    return out


def apply_sim(srv, sc: dict) -> dict:
    rep = parse(srv.js(build_js("sim", sc)))
    rep["warnings"] = warn_labeled(sc)
    return rep


def world_js(sc: dict, at=None) -> tuple:
    """(js, dx, dy) for the live world; 'at' re-centres the scene on that tile.

    In a projection (project.units != "spawn") the processors are still placed --
    you want to see the rig -- but they are left disabled: the simulation runs the
    program, a second live copy in the world would fight it over the same units
    and would spend real ipt on a stage it is not needed for.
    """
    proj = sc.get("project") or {}
    if proj.get("units", "mirror") != "spawn":
        for b in sc.get("buildings") or []:
            if b.get("enabled_explicit"):
                continue
            if "processor" in str(b.get("block", "")):
                b["enabled"] = False
    want = _xy(at, "at") or proj.get("at")
    dx = dy = 0
    if want:
        anc = anchor_of(sc)
        dx, dy = want[0] - anc[0], want[1] - anc[1]
        if dx or dy:
            sc = translate(sc, dx, dy)
    return build_js("world", sc), dx, dy


def apply_world(w, sc: dict, at=None) -> dict:
    """Lay the scene down in the live world.

    at = [x, y] tile in the world that the scene's anchor maps onto (typically the
    pulse mine). Without 'at' the scene lands at its own coordinates.
    """
    proj = sc.get("project") or {}
    want = _xy(at, "at") or proj.get("at")
    body, dx, dy = world_js(sc, at)
    if dx or dy:
        sc = translate(sc, dx, dy)
    size = sc["world"]["size"]
    outside = [b["name"] for b in sc["buildings"]
               if not (0 <= b["x"] < size and 0 <= b["y"] < size)]
    rep = parse(w.js(body))
    rep["warnings"] = warn_labeled(sc)
    rep["shift"] = [dx, dy]
    rep["anchor"] = list(want) if want else anchor_of(sc)
    rep["projected"] = project_units(sc)
    rep["scene"] = sc
    if outside:
        rep["errors"].append("off-map after shift: %s" % ", ".join(outside))
    return rep


# ---------------------------------------------------------------- probe

def _probe_vars(flavor: str) -> str:
    # one V line per variable; sim prints, the world daemon appends to its report
    return ("for(var i=0;i<V.length;i++){var v=V[i];var s='';"
            "try{s=v.isobj?String(v.objval):String(v.numval);}catch(e){s='?';}"
            + _js_rep(flavor, ["\"V\\t\"+tag+\"\\t\"+v.name+\"\\t\"+s"]) + "}")


def probe_js(flavor: str, sc: dict) -> str:
    out = [_SIM_PRELUDE if flavor == "sim" else _WORLD_PRELUDE]
    for b in sc["buildings"]:
        if not b["code"]:
            continue
        body = ("var b=bAt(%d,%d);"
                "if(b==null){%s}else{var V=b.executor.vars;var tag=%s;%s}"
                % (b["x"], b["y"],
                   _js_rep(flavor, [_js_str("ERR\tprobe %s: no build" % b["name"])]),
                   _js_str(b["name"]), _probe_vars(flavor)))
        out.append(_guard(flavor, "probe %s" % b["name"], body))
    out.append(_js_rep(flavor, [_js_str("PEND")]))
    return "".join(out)


def _cmp(actual: str, expect) -> bool:
    a = (actual or "").strip()
    if isinstance(expect, bool):
        return a in ("true", "1", "1.0") if expect else a in ("false", "0", "0.0", "null")
    if isinstance(expect, (int, float)):
        try:
            return abs(float(a) - float(expect)) < 1e-6
        except ValueError:
            return False
    return a == str(expect)


def parse_vars(lines: list) -> dict:
    vals = {}
    for ln in lines:
        parts = str(ln).split("\t")
        if parts[0] == "V" and len(parts) >= 4:
            vals[(parts[1], parts[2])] = parts[3]
    return vals


def building_index(sc: dict, rep: dict | None = None) -> dict:
    """Scene building name -> (origin x, origin y, block name).

    The placement report carries the origin the engine actually used, which is
    what Java's toString() prints; multi-block scenes must not guess it.
    """
    rows = {r["name"]: r for r in (rep or {}).get("rows", []) if r.get("kind") == "building"}
    out = {}
    for b in sc["buildings"]:
        row = rows.get(b["name"]) or {"x": b["x"], "y": b["y"]}
        out[b["name"]] = (row["x"], row["y"], b["block"])
    return out


def check_vars(sc: dict, vals: dict, rep: dict | None = None) -> list:
    """Evaluate scene checks. A string 'equals' naming a scene building is
    compared as that building (tile + block), so a check reads
    {"var": "tmp.lnk", "equals": "container1"} and is not tied to entity ids."""
    idx = building_index(sc, rep)
    res = []
    for c in sc["checks"]:
        actual = vals.get((c["logic"], c["var"]))
        expect = c["equals"]
        ok = actual is not None and _cmp(actual, expect)
        if not ok and actual is not None and isinstance(expect, str) and expect in idx:
            ox, oy, blk = idx[expect]
            ok = actual.endswith("[%d,%d]:%s" % (ox, oy, blk))
        res.append({"logic": c["logic"], "var": c["var"], "expect": expect,
                    "actual": actual, "ok": ok})
    return res


def probe_sim(srv, sc: dict) -> dict:
    vals = parse_vars(srv.js(probe_js("sim", sc)))
    return {"vars": {"%s.%s" % k: v for k, v in vals.items()},
            "checks": check_vars(sc, vals, getattr(srv, "_scene_report", None))}


def probe_world(w, sc: dict) -> dict:
    vals = parse_vars(w.js(probe_js("world", sc)))
    return {"vars": {"%s.%s" % k: v for k, v in vals.items()},
            "checks": check_vars(sc, vals, getattr(w, "_scene_report", None))}


# ---------------------------------------------------------------- CLI

def _print_report(rep: dict) -> None:
    print("placed   %d buildings" % rep["placed"])
    print("config   %d" % rep["configured"])
    print("stocked  %d" % rep["stocked"])
    print("logic    %d" % rep["linked"])
    print("units    %d" % rep["units"])
    for w in rep.get("warnings") or []:
        print("warn     " + w)
    for e in rep["errors"]:
        print("ERROR    " + e)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="scene files shared by mlogsim and the world server")
    sub = ap.add_subparsers(dest="cmd")

    c = sub.add_parser("check", help="validate and summarize a scene")
    c.add_argument("path")
    c.add_argument("--json", action="store_true")

    s = sub.add_parser("summary", help="same as check, short form")
    s.add_argument("path")

    e = sub.add_parser("emit", help="print the JS body a host would run")
    e.add_argument("path")
    e.add_argument("--flavor", default="sim", choices=["sim", "world"])

    a = ap.parse_args(argv)
    if not a.cmd:
        ap.print_help()
        return 2

    try:
        sc = load(a.path)
    except SceneError as exc:
        print("scene invalid: %s" % exc, file=sys.stderr)
        return 1

    if a.cmd in ("check", "summary"):
        if getattr(a, "json", False):
            print(json.dumps({"name": sc["name"], "path": sc["path"],
                              "world": sc["world"]["size"],
                              "buildings": len(sc["buildings"]),
                              "units": sum(u["count"] for u in sc["units"]),
                              "checks": len(sc["checks"]),
                              "warnings": warn_labeled(sc)}, ensure_ascii=False, indent=2))
        else:
            print(summary(sc))
            for w in warn_labeled(sc):
                print("warn     " + w)
            print("ok       scene valid")
        return 0

    if a.cmd == "emit":
        print(build_js(a.flavor, sc))
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
