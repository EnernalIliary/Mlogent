"""Read selected map state after an isolated Mindustry simulation."""

import base64
import json
import math

MAX_ENTRIES = 32
MAX_FLAG_LENGTH = 128
MAX_TILE_COORD = 32767
RULES = (
    "waves", "waveTimer", "waveSending", "waveSpacing", "initialWaveSpacing",
    "winWave", "attackMode", "canGameOver", "unitCap", "dropZoneRadius",
    "buildSpeedMultiplier", "buildCostMultiplier", "blockHealthMultiplier",
    "blockDamageMultiplier", "solarMultiplier",
)
_BOOLEAN_RULES = {"waves", "waveTimer", "waveSending", "attackMode", "canGameOver"}
_INTEGER_RULES = {"winWave", "unitCap"}
TILE_FIELDS = {
    "in_bounds": bool, "floor": str, "overlay": str, "block": str, "has_building": bool,
    "building.x": int, "building.y": int, "building.team": str, "building.rotation": int,
    "building.enabled": bool, "building.health": float, "building.max_health": float,
}
_TILE_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["x", "y"],
    "properties": {axis: {"type": "integer", "minimum": 0, "maximum": MAX_TILE_COORD}
                   for axis in ("x", "y")},
}
_FLAG_SCHEMA = {"type": "string", "minLength": 1, "maxLength": MAX_FLAG_LENGTH}
_RULE_SCHEMA = {"type": "string", "enum": list(RULES)}
_MARKER_SCHEMA = {"type": "integer", "minimum": -2147483648, "maximum": 2147483647}
_MEMORY_SCHEMA = {
    "type": "object", "required": ["x", "y", "index"], "additionalProperties": False,
    "properties": {**_TILE_SCHEMA["properties"],
                   "index": {"type": "integer", "minimum": 0, "maximum": 2147483647}},
}
_AREA_SCHEMA = {
    "type": "object", "required": ["x", "y", "width", "height"], "additionalProperties": False,
    "properties": {**_TILE_SCHEMA["properties"],
                   **{side: {"type": "integer", "minimum": 1, "maximum": MAX_TILE_COORD}
                      for side in ("width", "height")},
                   **{name: {"type": "string", "maxLength": 64} for name in ("team", "type")}},
}


def _selection(item):
    return {"type": "array", "minItems": 1, "maxItems": MAX_ENTRIES, "items": item}


def _check_schema(**fields):
    return {"type": "object", "additionalProperties": False,
            "required": list(fields), "properties": fields}


QUERY_SCHEMA = {
    "type": "object", "minProperties": 1, "additionalProperties": False,
    "description": "Read selected map state after the final tick, "
                   "and optionally check expected values. Uses ticks (default 60).",
    "properties": {
        "tiles": _selection(_TILE_SCHEMA),
        "flags": _selection(_FLAG_SCHEMA),
        "rules": _selection(_RULE_SCHEMA),
        "markers": _selection(_MARKER_SCHEMA),
        "memory": _selection(_MEMORY_SCHEMA),
        "unit_counts": _selection(_AREA_SCHEMA),
        "checks": _selection({
            "oneOf": [
                _check_schema(tile=_TILE_SCHEMA, field={"type": "string", "enum": list(TILE_FIELDS)},
                              equals={"type": ["string", "boolean", "number"]}),
                _check_schema(flag=_FLAG_SCHEMA, equals={"type": "boolean"}),
                _check_schema(rule=_RULE_SCHEMA, equals={"type": ["boolean", "number"]}),
                _check_schema(marker=_MARKER_SCHEMA, equals={"type": "boolean"}),
                _check_schema(memory=_MEMORY_SCHEMA, equals={"type": ["null", "string", "number"]}),
                _check_schema(unit_count=_AREA_SCHEMA, equals={"type": "integer", "minimum": 0}),
            ],
        }),
    },
}


def _valid_tile(tile):
    return (isinstance(tile, dict) and tile.keys() == {"x", "y"}
            and all(type(v) is int and 0 <= v <= MAX_TILE_COORD for v in tile.values()))


def _valid_marker(value):
    return type(value) is int and -(2**31) <= value < 2**31


def _valid_memory(value):
    return (isinstance(value, dict) and value.keys() == {"x", "y", "index"}
            and _valid_tile({"x": value["x"], "y": value["y"]})
            and type(value["index"]) is int and 0 <= value["index"] < 2**31)


def _valid_area(value):
    required = {"x", "y", "width", "height"}
    return (isinstance(value, dict) and required <= value.keys() <= required | {"team", "type"}
            and _valid_tile({"x": value["x"], "y": value["y"]})
            and all(type(value[side]) is int and 1 <= value[side] <= MAX_TILE_COORD
                    for side in ("width", "height"))
            and all(isinstance(value[name], str) and 1 <= len(value[name]) <= 64
                    and value[name].isascii() and value[name].isprintable() for name in ("team", "type")
                    if name in value))


def _valid_flag(name):
    return (isinstance(name, str) and bool(name.strip()) and len(name) <= MAX_FLAG_LENGTH
            and name.isprintable())


def _valid_expected(value, kind):
    if kind is type(None):
        return value is None
    if kind is float:
        return type(value) in (int, float) and abs(value) <= 1e30
    if kind is str:
        return isinstance(value, str) and 1 <= len(value) <= 128 and value.isprintable()
    if kind is int:
        return type(value) is int and -(2**31) <= value < 2**31
    return type(value) is kind


_EXTRA_SELECTORS = {
    "marker": ("markers", _valid_marker, bool),
    "memory": ("memory", _valid_memory, (float, str, type(None))),
    "unit_count": ("unit_counts", _valid_area, int),
}


def _validate_checks(query, checks):
    for i, check in enumerate(checks):
        label = f"world_probe.checks[{i}]"
        if not isinstance(check, dict):
            raise ValueError(f"{label} must be an object")
        if check.keys() == {"tile", "field", "equals"}:
            key, target = "tiles", check["tile"]
            if not _valid_tile(target):
                raise ValueError(f"{label}.tile must contain integer x and y in [0, {MAX_TILE_COORD}]")
            field = check["field"]
            if not isinstance(field, str) or field not in TILE_FIELDS:
                raise ValueError(f"{label}.field must be one of {', '.join(TILE_FIELDS)}")
            kind = TILE_FIELDS[field]
        elif check.keys() == {"flag", "equals"}:
            key, target, kind = "flags", check["flag"], bool
            if not _valid_flag(target):
                raise ValueError(f"{label}.flag must be printable text of 1 to {MAX_FLAG_LENGTH} characters")
        elif check.keys() == {"rule", "equals"}:
            key, target = "rules", check["rule"]
            if target not in RULES:
                raise ValueError(f"{label}.rule must be one of {', '.join(RULES)}")
            kind = bool if target in _BOOLEAN_RULES else int if target in _INTEGER_RULES else float
        else:
            selector = next((name for name in _EXTRA_SELECTORS if check.keys() == {name, "equals"}), None)
            if selector is None:
                raise ValueError(f"{label} requires one observation selector plus equals")
            key, validator, kind = _EXTRA_SELECTORS[selector]
            target = check[selector]
            if not validator(target):
                raise ValueError(f"{label}.{selector} is invalid")
        kinds = kind if isinstance(kind, tuple) else (kind,)
        if not any(_valid_expected(check["equals"], expected) for expected in kinds):
            raise ValueError(f"{label}.equals must be a valid {' or '.join(k.__name__ for k in kinds)} for the selected value")
        if key == "unit_counts" and check["equals"] < 0:
            raise ValueError(f"{label}.equals must be a non-negative unit count")
        entries = query.setdefault(key, [])
        if target not in entries:
            if len(entries) == MAX_ENTRIES:
                raise ValueError(f"world_probe.{key} can select at most {MAX_ENTRIES} entries including checks")
            entries.append(target)


def validate(value):
    """Validate the public query before starting a game."""
    if not isinstance(value, dict) or not value or value.keys() - QUERY_SCHEMA["properties"].keys():
        raise ValueError("world_probe must specify at least one supported selection or checks")
    for key, entries in value.items():
        if not isinstance(entries, list) or not 1 <= len(entries) <= MAX_ENTRIES:
            raise ValueError(f"world_probe.{key} must contain 1 to {MAX_ENTRIES} entries")
    for i, tile in enumerate(value.get("tiles", [])):
        if not _valid_tile(tile):
            raise ValueError(f"world_probe.tiles[{i}] must contain integer x and y in [0, {MAX_TILE_COORD}]")
    for i, name in enumerate(value.get("flags", [])):
        if not _valid_flag(name):
            raise ValueError(f"world_probe.flags[{i}] must be printable text of 1 to {MAX_FLAG_LENGTH} characters")
    for i, name in enumerate(value.get("rules", [])):
        if name not in RULES:
            raise ValueError(f"world_probe.rules[{i}] must be one of {', '.join(RULES)}")
    for key, validator, _ in _EXTRA_SELECTORS.values():
        for i, target in enumerate(value.get(key, [])):
            if not validator(target):
                raise ValueError(f"world_probe.{key}[{i}] is invalid")
    query = {key: list(entries) for key, entries in value.items()}
    _validate_checks(query, query.get("checks", []))
    return query


def _tile_field(tile, field):
    if field == "has_building":
        return tile["building"] is not None if tile["in_bounds"] else None
    parent, sep, name = field.partition(".")
    return (tile.get(parent) or {}).get(name) if sep else tile.get(parent)


def _evaluate(checks, frame):
    tiles = {(row["x"], row["y"]): row for row in frame.get("tiles", [])}
    flags = {row["name"]: row["value"] for row in frame.get("flags", [])}
    rules = {row["name"]: row.get("value") for row in frame.get("rules", [])}
    markers = {row["id"]: row["exists"] for row in frame.get("markers", [])}
    results = []
    for check in checks:
        expect = check["equals"]
        available = True
        if "tile" in check:
            coord = check["tile"]
            actual = _tile_field(tiles[coord["x"], coord["y"]], check["field"])
        elif "flag" in check:
            actual = flags[check["flag"]]
        elif "rule" in check:
            actual = rules[check["rule"]]
        elif "marker" in check:
            actual = markers[check["marker"]]
        elif "memory" in check:
            result = next(row for row in frame["memory"] if row["slot"] == check["memory"])
            available = result["kind"] in ("number", "string", "null")
            actual = result["value"]
        else:
            result = next(row for row in frame["unit_counts"] if row["area"] == check["unit_count"])
            available, actual = result["valid"], result["count"]
        if type(actual) in (int, float) and type(expect) in (int, float):
            passed = (math.isclose(actual, expect, rel_tol=1e-7, abs_tol=1e-6)
                      if isinstance(actual, float) or isinstance(expect, float) else actual == expect)
        else:
            passed = type(actual) is type(expect) and actual == expect
        results.append({**check, "actual": actual, "ok": available and passed})
    return results


def capture(js, query, ticks, *, live=False):
    selections = {key: entries for key, entries in query.items() if key != "checks"}
    script = _PROBE_JS.replace("__SINK__", "sb.append" if live else "print")
    encoded = base64.b64encode(json.dumps(selections, ensure_ascii=False).encode("utf-8")).decode("ascii")
    lines = js(script.replace("__QUERY__", encoded))
    prefix = "MLOG_WORLD_PROBE "
    for line in lines:
        if line.startswith(prefix):
            frame = {"ticks": ticks, **json.loads(base64.b64decode(line[len(prefix):], validate=True))}
            if "checks" in query:
                results = _evaluate(query["checks"], frame)
                frame["checks"] = results
                frame["checks_passed"] = all(check["ok"] for check in results)
            return frame
    raise RuntimeError("headless server did not return world state")


_PROBE_JS = """
(function(){
    var vars = Packages.mindustry.Vars, world = vars.world, rules = vars.state.rules;
    var decoded = java.util.Base64.getDecoder().decode("__QUERY__");
    var query = JSON.parse(String(new java.lang.String(decoded,"UTF-8")));
    var output = {width: world.width(), height: world.height()};
    if(query.tiles) output.tiles = query.tiles.map(function(p){
        var tile = world.tile(p.x, p.y);
        if(tile == null) return {x: p.x, y: p.y, in_bounds: false};
        var b = tile.build;
        return {x: p.x, y: p.y, in_bounds: true, floor: String(tile.floor().name),
                overlay: String(tile.overlay().name), block: String(tile.block().name),
                building: b == null ? null : {
                    x: b.tile.x, y: b.tile.y, team: String(b.team.name), rotation: b.rotation,
                    enabled: b.enabled, health: b.health, max_health: b.maxHealth
                }};
    });
    if(query.flags) output.flags = query.flags.map(function(name){
        return {name: name, value: rules.objectiveFlags.contains(name)};
    });
    if(query.rules) output.rules = query.rules.map(function(name){
        return {name: name, value: rules[name]};
    });
    if(query.markers) output.markers = query.markers.map(function(id){
        var marker = vars.state.markers.get(id);
        if(marker == null) return {id:id, exists:false};
        return {id:id, exists:true, type:String(marker.getClass().getSimpleName()),
                world:marker.world >= 0, minimap:marker.minimap >= 0, light:marker.light >= 0};
    });
    if(query.memory){
        var MemoryBuild = Packages.mindustry.world.blocks.logic.MemoryBlock$MemoryBuild;
        var LVar = Packages.mindustry.logic.LVar;
        output.memory = query.memory.map(function(slot){
            var building = world.build(slot.x,slot.y);
            var row = {slot:slot, kind:"not_memory", value:null};
            if(!(building instanceof MemoryBuild)) return row;
            row.block = String(building.block.name);
            if(slot.index >= building.block.memoryCapacity){
                row.kind = "out_of_range";
                return row;
            }
            var index = new LVar("index"), value = new LVar("value");
            index.setnum(slot.index);
            building.read(index,value);
            if(!value.isobj){
                row.kind = "number";
                row.value = value.numval;
            }else if(value.objval == null){
                row.kind = "null";
            }else if(value.objval instanceof java.lang.String || typeof value.objval === "string"){
                row.kind = "string";
                row.value = String(value.objval).slice(0,512);
                if(row.value.length < String(value.objval).length) row.kind = "truncated";
            }else{
                row.kind = "object";
            }
            return row;
        });
    }
    if(query.unit_counts){
        var teams = Packages.mindustry.game.Team.all;
        var teamNames = Object.create(null);
        for(var i=0;i<teams.length;i++) teamNames[String(teams[i].name)] = true;
        output.unit_counts = query.unit_counts.map(function(a){
            var valid = a.x + a.width <= output.width && a.y + a.height <= output.height &&
                        (!a.team || teamNames[a.team] === true) &&
                        (!a.type || vars.content.getByName(Packages.mindustry.ctype.ContentType.unit,a.type) != null);
            return {area:a,valid:valid,count:valid ? 0 : null};
        });
        Packages.mindustry.gen.Groups.unit.each(function(u){
            if(u.dead) return;
            var x = u.x/vars.tilesize, y = u.y/vars.tilesize;
            output.unit_counts.forEach(function(row){
                var a = row.area;
                if(row.valid && a.x <= x && x < a.x+a.width && a.y <= y && y < a.y+a.height &&
                   (!a.team || a.team === String(u.team.name)) && (!a.type || a.type === String(u.type.name))){
                    row.count++;
                }
            });
        });
    }
    var bytes = new java.lang.String(JSON.stringify(output)).getBytes("UTF-8");
    __SINK__("MLOG_WORLD_PROBE " + java.util.Base64.getEncoder().encodeToString(bytes));
})()
"""
