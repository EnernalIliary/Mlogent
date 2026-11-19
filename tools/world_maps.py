"""Map switch/reset operations with explicit world and audit dependencies."""
import time
from world_protocol import coerce
from world_queries import STATUS_JS

OPERATIONS = frozenset(('switch', 'reset'))

def switch_map(w, target: str, audit) -> dict:
    """换图但不踢人: nextmap 只登记下一张图, gameover 触发 loadMap;
    NetServer 的连接表不动, 客户端自己重载新地图。"""
    before = None
    try:
        before = float((w.js("sb.append(Vars.state.tick);") or ["0"])[0])
    except Exception:
        pass
    audit("switch", map=target)
    out1 = w.console("nextmap " + target, quiet=0.4, timeout=15)
    out2 = w.console("gameover", quiet=0.6, timeout=30)
    deadline = time.time() + 45
    loaded = False
    while time.time() < deadline:
        time.sleep(0.5)
        try:
            tick = float((w.js("sb.append(Vars.state.tick);") or ["0"])[0])
        except Exception:
            continue
        if before is None or tick < before:
            loaded = True
            break
    if not loaded:
        return {"ok": False, "error": "map did not reload",
                "nextmap": out1.get("lines"), "gameover": out2.get("lines")}
    try:
        w.js("var r=Vars.state.rules; r.waves=false; r.infiniteResources=true; "
             "r.canGameOver=false; r.logicUnitControl=true; sb.append(r.waves);")
    except Exception:
        pass
    try:
        w.map_name = w.js("sb.append(Vars.state.map.name());")[0]
    except Exception:
        w.map_name = target
    st = w.js(STATUS_JS)
    players = next((ln.split("=", 1)[1] for ln in st if ln.startswith("players=")), None)
    return {"ok": True, "map": w.map_name, "players": coerce(players)}


def change_map(w, req, *, audit):
    op = (req.get("op") or "").strip()
    if op == "switch":
        target = str(req.get("map") or w.map_name or "").strip()
        if not target:
            return {"ok": False, "error": "no map name"}
        return switch_map(w, target, audit)
    if op == "reset":
        # 默认走「不踢人」的换图路径；hard=true 才 stop+host（会断开所有玩家）
        if not req.get("hard"):
            target = str(req.get("map") or w.map_name or "").strip()
            if not target:
                return {"ok": False, "error": "no map name"}
            return switch_map(w, target, audit)
        audit("reset", map=w.map_name, hard=True)
        w.console("stop", quiet=0.6, timeout=30)
        res = w.console("host " + (w.map_name or ""), quiet=1.0, timeout=180)
        text = "\n".join(res.get("lines") or [])
        if "Opened a server" not in text:
            return {"ok": False, "error": "rehost failed", "lines": res.get("lines")}
        w.hosted = True
        try:
            w.js("var r=Vars.state.rules; r.waves=false; r.infiniteResources=true; "
                 "r.canGameOver=false; r.logicUnitControl=true; sb.append(r.waves);")
        except Exception:
            pass
        return {"ok": True, "map": w.map_name, "lines": res.get("lines")[-3:]}
    return NotImplemented
