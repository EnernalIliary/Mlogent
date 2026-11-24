"""MCP adapter for the WayZer map registry and its bounded host command."""
import json
import re
import time
import urllib.error
import urllib.request

MAPS_SCHEMA = {
    "name": "world_wayzer_maps",
    "description": "Search the WayZer plugin registry for remote Mindustry maps; returns numeric map IDs.",
    "annotations": {"readOnlyHint": True},
    "inputSchema": {"type": "object", "additionalProperties": False, "properties": {
        "query": {"type": "string", "maxLength": 32},
        "page": {"type": "integer", "minimum": 1, "maximum": 12},
    }},
}
ROW = re.compile(r"^\s*(\d+)\s{2,}(.+?)\s*\|\s*([a-z]+)\s*$", re.IGNORECASE)


def maps(client, args):
    query, page = args.get("query", ""), args.get("page", 1)
    if not isinstance(query,str) or (query and not re.fullmatch(r"[\w.-]{1,32}", query)):
        raise ValueError("Use a keyword of up to 32 characters")
    if type(page) is not int or not 1 <= page <= 12:
        raise ValueError("Page must be between 1 and 12")
    filter_value = "site:" + query if query else "site"
    result = client.call({"op":"console","cmd":"maps {} {}".format(filter_value,page),
                          "quiet":2.0,"timeout":16}, timeout=21)
    items = []
    for line in result.get("lines") or []:
        row = ROW.fullmatch(line)
        if row and 10000 <= int(row[1]) <= 99999:
            items.append({"id":int(row[1]),"name":row[2][:160],"mode":row[3]})
    return {"ok":True,"page":page,"maps":items}


def switch(client, map_id):
    endpoint = "https://api.mindustry.top/maps/{}.json".format(map_id)
    try:
        request = urllib.request.Request(endpoint,headers={"Accept":"application/json"})
        with urllib.request.urlopen(request,timeout=5) as response:
            raw = response.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            raise ValueError("Map metadata too large")
        metadata = json.loads(raw)
        name = metadata["tags"]["name"]
        if not isinstance(name,str) or not name.strip():
            raise ValueError("Map name missing")
    except (OSError,ValueError,KeyError,TypeError):
        return {"ok":True,"status":"map_unverified","map_id":map_id}
    request = {"op":"console","cmd":"host {}".format(map_id),"quiet":2.0,"timeout":30}
    try:
        response=client.call(request,timeout=34)
        if not response.get("ok"):
            return {"ok":True,"status":"unavailable","map_id":map_id}
    except RuntimeError:
        return {"ok":True,"status":"unavailable","map_id":map_id}
    deadline=time.monotonic()+29
    while time.monotonic()<deadline:
        try:
            result=client.call({"op":"js","code":'sb.append(String(Vars.state.rules.tags.get("id")));',
                                "timeout":4},timeout=6)
            if result.get("lines")==[str(map_id)]:
                return {"ok":True,"status":"applied","map_id":map_id,"map":name[:160]}
        except RuntimeError:
            pass
        time.sleep(1)
    return {"ok":True,"status":"switch_unconfirmed","map_id":map_id}
