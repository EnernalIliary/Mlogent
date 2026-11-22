"""Resource admission for the public Mlogent HTTP service."""
import json

LIGHT = frozenset({
    "mlog_doctor", "mlog_kb", "mlog_fetch", "mlog_fidelity",
    "world_status", "world_players", "world_maps", "world_schematics",
    "world_dashboard",
})
HEAVY = frozenset({
    "mindcode_compile", "mlog_sim", "mlog_trace", "mlog_diff", "mlog_explore",
    "mlog_validate", "scenario_run", "world_start", "world_scene",
    "world_reset", "world_load", "world_switch_map", "world_schematic",
})
MAX_BYTES = {"light": 128 * 1024, "bounded": 2 * 1024 * 1024,
             "heavy": 512 * 1024}
HEAVY_LIMITS = {"ticks": 1800, "steps": 50_000}


def category(name):
    if name in HEAVY:
        return "heavy"
    if name in LIGHT:
        return "light"
    return "bounded"


def refusal(name, arguments):
    tier = category(name)
    size = len(json.dumps(arguments, ensure_ascii=True, separators=(",", ":")))
    if size > MAX_BYTES[tier]:
        return "Tool arguments exceed the {} KiB limit.".format(MAX_BYTES[tier] // 1024)
    if tier == "heavy":
        for field, limit in HEAVY_LIMITS.items():
            if field in arguments and (type(arguments[field]) is not int
                                       or not 1 <= arguments[field] <= limit):
                return "{} must be an integer between 1 and {}.".format(field, limit)
    if name == "mlog_explore" and "limit" in arguments:
        limit = arguments["limit"]
        if type(limit) is not int or not 1 <= limit <= 8:
            return "Exploration limit must be an integer between 1 and 8."
    if name == "mlog_sim" and "rt" in arguments:
        pace = arguments["rt"]
        ticks = arguments.get("ticks", arguments.get("steps", 60))
        if type(pace) not in (int, float) or not 0.01 <= pace <= 100 or ticks > 1200 * pace:
            return "Realtime simulation must fit within 20 seconds of pacing."
    return None
