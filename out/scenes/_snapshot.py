"""Render PNG snapshots of the .msav scenes in out/scenes/.

Loads each save with the real v160.7 server (paused), dumps terrain / blocks /
units through the console `js` bridge, and draws a 64x64 tile map.

    python out/scenes/_snapshot.py            # all scenes
    python out/scenes/_snapshot.py PVP        # one
"""
from __future__ import annotations

import sys
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "out" / "_pylibs"))  # zstandard only; no PIL here

import mlogsim as M  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

SAVES = {
    "open": "Mlog场景-进攻-open.msav",
    "garded-line": "Mlog场景-进攻-garded-line.msav",
    "maze": "Mlog场景-进攻-maze.msav",
    "PVP": "Mlog场景-复杂-PVP.msav",
    "campaign": "Mlog场景-复杂-campaign.msav",
}

# floor name -> single base36 char (0..9a..z); python side maps back to a colour
FLOORS = {
    "stone": 1, "grass": 2, "sand": 3, "water": 4, "deepwater": 5, "ice": 6,
    "slag": 7, "snow": 8, "darksand": 9, "basalt": 10, "metal": 11,
    "shallowwater": 12, "mud": 13, "dirt": 14, "salt": 15, "dacite": 16,
    "hotrock": 17, "magmarock": 18, "char": 19, "spore": 20, "moss": 21,
    "redice": 22, "redstone": 23, "redsand": 24, "arkycite": 25,
    "beryllic": 26, "crystalline": 27, "ferric": 28, "pool": 29, "puddle": 30,
    "mudflat": 31, "metal-floor": 11, "dark-panel-1": 11, "dark-panel-2": 11,
    "dark-panel-3": 11, "dark-panel-4": 11, "dark-panel-5": 11,
    "dark-panel-6": 11, "shale": 14, "crater-stone": 16, "bluemat": 11,
}

SNAP_JS = r"""
var W = Vars.world.width(), H = Vars.world.height();
var fm = %(floors)s;
print("SIZE\t" + W + "\t" + H);
for(var y = 0; y < H; y++){
    var s = "";
    for(var x = 0; x < W; x++){
        var t = Vars.world.tile(x, y);
        var n = t.floor().name;
        var c = fm[n]; if(c == null) c = 32;
        s += (c < 10 ? ("" + c) : String.fromCharCode(87 + c));
    }
    print("ROW\t" + y + "\t" + s);
}
for(var y = 0; y < H; y++){
    for(var x = 0; x < W; x++){
        var t = Vars.world.tile(x, y);
        var b = t.block();
        if(b == null || b.name == "air") continue;
        print("BLK\t" + x + "\t" + y + "\t" + b.name + "\t" + t.team().name);
    }
}
var U = Packages.mindustry.gen.Groups.unit;
for(var k = 0; k < U.size(); k++){
    var u = U.index(k);
    print("UNIT\t" + u.type.name + "\t" + u.team.name + "\t" + (u.x / 8) + "\t" + (u.y / 8) + "\t" + u.health);
}
print("END");
"""

FLOOR_COLORS = {
    0: (16, 18, 22), 1: (66, 68, 72), 2: (52, 84, 48), 3: (150, 132, 88),
    4: (28, 52, 88), 5: (22, 40, 70), 6: (120, 160, 180), 7: (96, 56, 36),
    8: (150, 160, 170), 9: (104, 92, 64), 10: (58, 58, 64), 11: (84, 88, 96),
    12: (36, 70, 108), 13: (74, 62, 46), 14: (86, 70, 52), 15: (140, 140, 132),
    16: (70, 64, 60), 17: (70, 46, 38), 18: (60, 34, 30), 19: (44, 44, 42),
    20: (70, 44, 70), 21: (46, 66, 44), 22: (120, 150, 190), 23: (110, 60, 60),
    24: (130, 84, 70), 25: (60, 90, 60), 26: (60, 70, 100), 27: (80, 70, 110),
    28: (90, 70, 60), 29: (34, 58, 96), 30: (80, 76, 60), 31: (76, 70, 56),
    32: (22, 24, 28),
}

TEAM_COLORS = {
    "sharded": (74, 144, 217), "crux": (217, 74, 74), "blue": (74, 106, 217),
    "green": (74, 217, 122), "derelict": (120, 120, 120),
}

CATEGORIES = [
    ("core", (245, 245, 245), lambda n: n.startswith("core")),
    ("logic", (80, 220, 120), lambda n: n.endswith("processor") or n.startswith("memory") or n in ("message", "switch", "display", "logic-display")),
    ("defense", (230, 90, 90), lambda n: "turret" in n or n in ("ripple", "fuse", "cyclone", "spectre", "meltdown", "salvo", "swarmer", "scatter", "hail", "wave", "lancer", "arc", "parallax", "segment", "tsunami", "breach", "diffuse", "sublimate", "afflict", "disperse")),
    ("power", (240, 170, 60), lambda n: "generator" in n or "solar" in n or "battery" in n or "reactor" in n or "panel" in n or "turbine" in n or "differential" in n or "combustion" in n),
    ("logistics", (230, 210, 90), lambda n: "conveyor" in n or n in ("junction", "bridge-conveyor", "sorter", "gateway", "unloader", "duct", "duct-router", "duct-bridge")),
    ("drill", (90, 200, 220), lambda n: n.endswith("-drill") or n in ("water-extractor", "oil-extractor", "cultivator", "pneumatic-drill")),
    ("production", (170, 130, 230), lambda n: any(k in n for k in ("smelter", "crucible", "mixer", "compressor", "pulverizer", "kiln", "incinerator", "separator", "disassembler", "assembler", "weaver", "synthesizer", "refinery", "centrifuge", "press", "forge", "furnace"))),
    ("unit", (120, 230, 200), lambda n: "factory" in n or "reconstructor" in n or "payload" in n),
    ("wall", (150, 150, 160), lambda n: "wall" in n or "door" in n or "mender" in n or "projector" in n),
]


def category(name: str) -> tuple[str, tuple[int, int, int]]:
    for label, color, test in CATEGORIES:
        try:
            if test(name):
                return label, color
        except Exception:
            pass
    return "other", (200, 200, 200)


def font(size: int):
    for path in (r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\arial.ttf"):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def load(name: str, save: Path):
    srv = M.Server(M._default_java(), M._default_jar(), save=save)
    try:
        lines = srv.js(SNAP_JS % {"floors": str(FLOORS).replace("'", '"')})
    finally:
        srv.close()
    rows, blocks, units = {}, [], []
    size = (64, 64)
    for ln in lines:
        p = ln.split("\t")
        if p[0] == "SIZE":
            size = (int(p[1]), int(p[2]))
        elif p[0] == "ROW":
            rows[int(p[1])] = p[2]
        elif p[0] == "BLK":
            blocks.append((int(p[1]), int(p[2]), p[3], p[4]))
        elif p[0] == "UNIT":
            units.append((p[1], p[2], float(p[3]), float(p[4]), float(p[5])))
    return size, rows, blocks, units


def char_code(ch: str) -> int:
    if ch.isdigit():
        return int(ch)
    return ord(ch) - 87


def render(name: str, size, rows, blocks, units) -> Path:
    W, H = size
    cell = 11
    pad = 16
    header = 46
    footer = 74
    img = Image.new("RGB", (pad * 2 + W * cell, header + H * cell + footer), (10, 11, 14))
    d = ImageDraw.Draw(img)
    f_title = font(17)
    f_small = font(11)

    for y in range(H):
        row = rows.get(y, "0" * W)
        for x in range(W):
            c = char_code(row[x]) if x < len(row) else 0
            d.rectangle([pad + x * cell, header + y * cell,
                         pad + x * cell + cell - 1, header + y * cell + cell - 1],
                        fill=FLOOR_COLORS.get(c, (22, 24, 28)))

    # blocks: per tile, so multi-block cores get fully painted
    for x, y, bname, team in blocks:
        label, color = category(bname)
        tcol = TEAM_COLORS.get(team, (150, 150, 150))
        if label == "core":
            d.rectangle([pad + x * cell, header + y * cell,
                         pad + x * cell + cell - 1, header + y * cell + cell - 1], fill=tcol)
        else:
            d.rectangle([pad + x * cell + 1, header + y * cell + 1,
                         pad + x * cell + cell - 2, header + y * cell + cell - 2], fill=color)

    for uname, team, ux, uy, hp in units:
        cx, cy = pad + ux * cell, header + uy * cell
        r = 4
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=TEAM_COLORS.get(team, (240, 240, 240)),
                  outline=(10, 10, 10))

    # grid every 8 tiles
    grid = (38, 42, 50)
    for g in range(0, max(W, H) + 1, 8):
        if g <= W:
            x = pad + g * cell
            d.line([x, header, x, header + H * cell], fill=grid, width=1)
        if g <= H:
            y = header + g * cell
            d.line([pad, y, pad + W * cell, y], fill=grid, width=1)

    tile_set = {(x, y): (b, t) for x, y, b, t in blocks}
    core_units = []
    for x, y, b, t in blocks:
        if not b.startswith("core"):
            continue
        if tile_set.get((x - 1, y)) == (b, t) or tile_set.get((x, y - 1)) == (b, t):
            continue
        core_units.append((x, y, t, b))
    counts: dict[str, int] = {}
    for _, _, b, _ in blocks:
        label = category(b)[0]
        if label == "core":
            continue
        counts[label] = counts.get(label, 0) + 1
    d.text((pad, 12), f"{name}  {W}x{H}  block tiles={len(blocks)}  units={len(units)}  core buildings={len(core_units)}",
           font=f_title, fill=(235, 238, 245))
    team_txt = ", ".join(f"{t}={sum(1 for c in core_units if c[2] == t)}" for t in sorted({c[2] for c in core_units}))
    d.text((pad, 30), f"cores: {team_txt}   |   " + "  ".join(f"{k}={v}" for k, v in sorted(counts.items())),
           font=f_small, fill=(160, 168, 180))
    for cx, cy, team, bname in core_units:
        d.text((pad + cx * cell + 2, header + cy * cell + 1), team[:1].upper(),
               font=f_small, fill=(10, 10, 10))

    fy = header + H * cell + 8
    d.text((pad, fy), "white core = team colour   red defense   yellow logistics   green logic   cyan drill   purple production   orange power   teal unit   grey wall",
           font=f_small, fill=(170, 176, 188))
    d.text((pad, fy + 16), "floor: dark grey stone   green grass   tan sand   blue water   pale ice   brown slag",
           font=f_small, fill=(140, 146, 158))
    d.text((pad, fy + 32), "grid = every 8 tiles; dots = units (team colour).  generated by out/scenes/_snapshot.py",
           font=f_small, fill=(120, 126, 138))

    out = HERE / f"snap_{name}.png"
    img.save(out)
    return out


def main() -> int:
    only = sys.argv[1:] or list(SAVES)
    for name in only:
        save = HERE / SAVES[name]
        if not save.exists():
            print(f"missing {save}")
            continue
        size, rows, blocks, units = load(name, save)
        out = render(name, size, rows, blocks, units)
        print(f"saved {out} ({out.stat().st_size} B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
