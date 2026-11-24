"""Deliver a reply only to the live connection that issued a native /push."""
import base64
import re

SCHEMA = {
    "name": "world_push_reply",
    "description": "Send one private reply for a pending native /push. Requires its opaque reply ID.",
    "inputSchema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "reply_id": {"type": "string", "pattern": "^[a-f0-9]{32}$"},
            "text": {"type": "string", "minLength": 1, "maxLength": 500},
        },
        "required": ["reply_id", "text"],
    },
}


def _js_text(text):
    # The world console rewrites backslash escapes. Transport only ASCII
    # Base64 here, then reconstruct the original UTF-8 text inside the JVM.
    encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
    return ("new java.lang.String(java.util.Base64.getDecoder().decode('" + encoded
            + "'), java.nio.charset.StandardCharsets.UTF_8)")


def reply(client, arguments):
    key = arguments.get("reply_id")
    text = arguments.get("text")
    if not isinstance(key, str) or not re.fullmatch("[a-f0-9]{32}", key):
        raise ValueError("Invalid push reply ID")
    if not isinstance(text, str) or not 1 <= len(text.strip()) <= 500:
        raise ValueError("Reply must contain 1 to 500 characters")
    text = " ".join(text.split()).replace("[", "［").replace("]", "］")
    code = (
        'if(typeof this._iliaryPushReply !== "function"){sb.append("unavailable");}'
        'else{sb.append(this._iliaryPushReply("' + key + '",' + _js_text(text) + '));}'
    )
    for _ in range(2):
        result = client.call({"op": "js", "code": code, "timeout": 7}, timeout=8)
        lines = result.get("lines") or []
        if lines and lines[0] in {"sent", "expired", "offline", "unavailable"}:
            return {"ok": True, "status": lines[0]}
    return {"ok": True, "status": "unavailable"}

ACTION_SCHEMA = {
    "name": "world_push_action",
    "description": "Run one bounded in-game action requested by a connected admin via native /push.",
    "inputSchema": {
        "type": "object", "additionalProperties": False,
        "properties": {
            "reply_id": {"type": "string", "pattern": "^[a-f0-9]{32}$"},
            "action": {"type": "string", "enum": ["fill_core", "spawn_units", "switch_map"]},
            "map_id": {"type": "integer", "minimum": 10000, "maximum": 99999},
            "item": {"type": "string"}, "unit": {"type": "string"},
            "count": {"type": "integer", "minimum": 1},
        },
        "required": ["reply_id", "action"],
    },
}


def action(client, arguments):
    import json

    key = arguments.get("reply_id")
    if not isinstance(key, str) or not re.fullmatch("[a-f0-9]{32}", key):
        raise ValueError("Invalid push ID")
    op = arguments.get("action")
    if op == "fill_core":
        item = arguments.get("item")
        if not isinstance(item, str) or not re.fullmatch("[a-z0-9-]{1,80}", item):
            raise ValueError("Expected an exact resource ID")
        request = {"action": op, "item": item}
    elif op == "switch_map":
        map_id = arguments.get("map_id")
        if type(map_id) is not int or not 10000 <= map_id <= 99999:
            raise ValueError("Expected an explicit WayZer remote map ID (10000–99999)")
        request = {"action":op,"map_id":map_id}
    elif op == "spawn_units":
        count, unit = arguments.get("count"), arguments.get("unit")
        if type(count) is not int or count < 1 or not isinstance(unit, str) or not re.fullmatch("[a-z0-9-]{1,40}", unit):
            raise ValueError("Expected an exact unit ID and positive integer count")
        request = {"action": op, "unit": unit, "count": count}
    else:
        raise ValueError("Unsupported action")
    code = ('if(typeof this._iliaryPushAction !== "function"){sb.append("{}");}'
            'else{sb.append(JSON.stringify(this._iliaryPushAction("' + key + '",JSON.parse('
            + _js_text(json.dumps(request)) + '))));}')
    for _ in range(2):
        result = client.call({"op": "js", "code": code, "timeout": 7}, timeout=8)
        lines = result.get("lines") or []
        if lines:
            result = json.loads(lines[0])
            if result.get("status") == "authorized" and op == "switch_map":
                from world_wayzer_maps import switch
                return switch(client, request["map_id"])
            if result.get("status"):
                return {"ok": True, **result}
    return {"ok": True, "status": "unavailable"}
