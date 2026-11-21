"""Read selected map state after an isolated Mindustry simulation."""

import json

MAX_ENTRIES = 32
MAX_FLAG_LENGTH = 128
MAX_TILE_COORD = 32767
RULES = (
    "waves", "waveTimer", "waveSending", "waveSpacing", "initialWaveSpacing",
    "winWave", "attackMode", "canGameOver", "unitCap", "dropZoneRadius",
    "buildSpeedMultiplier", "buildCostMultiplier", "blockHealthMultiplier",
    "blockDamageMultiplier", "solarMultiplier",
)


def validate(value):
    """Validate the public query before starting a game."""
    if not isinstance(value, dict) or not value or value.keys() - {"tiles", "flags", "rules"}:
        raise ValueError("world_probe must specify tiles, flags or rules")
    for key, entries in value.items():
        if not isinstance(entries, list) or not 1 <= len(entries) <= MAX_ENTRIES:
            raise ValueError(f"world_probe.{key} must contain 1 to {MAX_ENTRIES} entries")
    for i, tile in enumerate(value.get("tiles", [])):
        if (not isinstance(tile, dict) or tile.keys() != {"x", "y"}
                or any(type(v) is not int or not 0 <= v <= MAX_TILE_COORD for v in tile.values())):
            raise ValueError(f"world_probe.tiles[{i}] must contain integer x and y in [0, {MAX_TILE_COORD}]")
    for i, name in enumerate(value.get("flags", [])):
        if (not isinstance(name, str) or not name.strip() or len(name) > MAX_FLAG_LENGTH
                or not name.isprintable()):
            raise ValueError(f"world_probe.flags[{i}] must be printable text of 1 to {MAX_FLAG_LENGTH} characters")
    for i, name in enumerate(value.get("rules", [])):
        if name not in RULES:
            raise ValueError(f"world_probe.rules[{i}] must be one of {', '.join(RULES)}")
    return value


def capture(server, query, ticks):
    lines = server.js(_PROBE_JS.replace("__QUERY__", json.dumps(query, ensure_ascii=True)))
    prefix = "MLOG_WORLD_PROBE "
    for line in lines:
        if line.startswith(prefix):
            return {"ticks": ticks, **json.loads(line[len(prefix):])}
    raise RuntimeError("headless server did not return world state")


_PROBE_JS = """
(function(){
    var vars = Packages.mindustry.Vars, world = vars.world, rules = vars.state.rules;
    var query = __QUERY__;
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
    print("MLOG_WORLD_PROBE " + JSON.stringify(output));
})()
"""
