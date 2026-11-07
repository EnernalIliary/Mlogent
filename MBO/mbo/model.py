"""L1 IR：`Tile` / `Layout`。

三条容易踩的语义（docs/13 R1、R2、R7）：

- 存的是**中心格**：2×2 方块传 (5,4) 就占 (5..6, 4..5)；3×3 传 (5,4) 占 (4..6, 3..5)。
- 重叠必须自己拦：游戏 `Schematics.place()` 是静默覆盖，后写盖前写、不报错。
- 传送带方向：rot 0=东 / 1=南 / 2=西 / 3=北（1 是 `-y`，实测钉死，见 docs/14）。
"""

from __future__ import annotations

from dataclasses import dataclass

from . import codec

ROT = {"E": 0, "S": 1, "W": 2, "N": 3}
DIRV = {0: (1, 0), 1: (0, -1), 2: (-1, 0), 3: (0, 1)}

# 实测常量（docs/14 §1）：传送带稳态吞吐与首货延迟
BELT_RATE = 4.9          # items/s，保守值（单条实测 4.93）
BELT_LATENCY = 0.47      # s/tile

# 物流门：同一类方块，靠 invert 字段区分（Mindustry-Source .../OverflowGate.java）
#   overflow-gate （溢流门）：直行优先，直行堵了才分两侧（两侧都通则按 rotation 位交替）
#   underflow-gate（反溢流门）：两侧优先（都通则交替），两侧都堵才直行
GATES = {"overflow-gate": "overflow", "underflow-gate": "underflow"}
# 门实测（docs/16）：反溢门 1.360/s（0.674/0.674 完全均衡）、溢流门 1.323/s（0.676/0.637）
# 1 带 1 门方案 vs 2 个独立 source：6 blocks/18 tiles vs 10 blocks/22 tiles，吞吐持平


def rot_for(dx: int, dy: int) -> int:
    """给一个朝向向量，返回传送带 rotation（只接受正交单位向量）。"""
    for rot, v in DIRV.items():
        if v == (dx, dy):
            return rot
    raise ValueError("不是正交单位向量：(%r, %r)" % (dx, dy))


def item_cfg(gd, item: str) -> dict:
    """item-source / sorter / unloader 的 Content config。"""
    return {"__content__": "item", "id": gd.item_id(item)}


def point_cfg(pts) -> "codec.TaggedList":
    """power-node / power-source 的 Point2[] config（tag=8，元素是相对偏移）。"""
    return codec.TaggedList([(int(x), int(y)) for x, y in pts], tag=8)


def read_points(cfg) -> list:
    """从 config 里取出 Point2 列表（容忍 dict / tuple 两种读法）。"""
    out = []
    for v in cfg or []:
        if isinstance(v, dict) and "__point__" in v:
            out.append(tuple(v["__point__"]))
        elif isinstance(v, (tuple, list)) and len(v) == 2:
            out.append((int(v[0]), int(v[1])))
    return out


@dataclass
class Tile:
    block: str
    x: int                      # 中心格
    y: int
    rotation: int = 0
    config: object = None

    def as_stile(self):
        return codec.msch.Stile(self.block, self.x, self.y, self.rotation, self.config)


class Layout:
    """一张蓝图的工作区。`sizes` 是 方块名 → 尺寸 的表（来自 GameData）。"""

    def __init__(self, width: int, height: int, sizes: dict, name: str = "", description: str = ""):
        self.w = width
        self.h = height
        self.sizes = sizes
        self.name = name
        self.description = description
        self.tiles: list[Tile] = []
        self.occ: dict[tuple, Tile] = {}

    # ------------------------------------------------------------------ 几何
    def origin(self, block: str, x: int, y: int) -> tuple:
        d = (self.sizes.get(block, 1) - 1) // 2
        return x - d, y - d

    def cells(self, block: str, x: int, y: int) -> set:
        s = self.sizes.get(block, 1)
        ox, oy = self.origin(block, x, y)
        return {(ox + i, oy + j) for i in range(s) for j in range(s)}

    def free(self, block: str, x: int, y: int) -> bool:
        for cx, cy in self.cells(block, x, y):
            if not (0 <= cx < self.w and 0 <= cy < self.h):
                return False
            if (cx, cy) in self.occ:
                return False
        return True

    def find_free(self, block: str, cx: int, cy: int, radius: int = 0) -> tuple | None:
        """从 (cx,cy) 向外螺旋找第一个放得下 block 的位置。"""
        if self.free(block, cx, cy):
            return cx, cy
        for r in range(1, radius + 1):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    if max(abs(dx), abs(dy)) != r:
                        continue
                    if self.free(block, cx + dx, cy + dy):
                        return cx + dx, cy + dy
        return None

    # ------------------------------------------------------------------ 写
    def add(self, block: str, x: int, y: int, rotation: int = 0, config=None) -> Tile:
        if not self.free(block, x, y):
            raise ValueError("overlap/out-of-bounds: %s@(%d,%d) size=%d"
                             % (block, x, y, self.sizes.get(block, 1)))
        t = Tile(block, x, y, rotation, config)
        for c in self.cells(block, x, y):
            self.occ[c] = t
        self.tiles.append(t)
        return t

    def set_config(self, tile: Tile, config) -> None:
        tile.config = config

    def tile_at(self, x: int, y: int) -> Tile | None:
        return self.occ.get((x, y))

    def of_block(self, block: str) -> list:
        return [t for t in self.tiles if t.block == block]

    def adjacent(self, tile: Tile, block: str | None = None) -> list:
        """与 tile footprint 正交相邻的 tile（可按方块名过滤）。"""
        out = []
        for cx, cy in self.cells(tile.block, tile.x, tile.y):
            for dx, dy in DIRV.values():
                other = self.occ.get((cx + dx, cy + dy))
                if other is None or other is tile:
                    continue
                if block is None or other.block == block:
                    if other not in out:
                        out.append(other)
        return out

    # ------------------------------------------------------------------ 导出
    def crop(self) -> "Layout":
        """把画布裁到实际占格的外接矩形（原地修改）。

        生成的蓝图默认是整块画布（24×24），但真正需要粘进游戏的只有占用的那一小块。
        裁切后 `w/h` 就是图形的外接矩形，`place()` 的锚点也随之变准。
        """
        if not self.tiles:
            return self
        xs, ys = [], []
        for t in self.tiles:
            for cx, cy in self.cells(t.block, t.x, t.y):
                xs.append(cx)
                ys.append(cy)
        x0, y0 = min(xs), min(ys)
        w, h = max(xs) - x0 + 1, max(ys) - y0 + 1
        if (w, h) == (self.w, self.h) and x0 == 0 and y0 == 0:
            return self
        for t in self.tiles:
            t.x -= x0
            t.y -= y0
        self.w, self.h = w, h
        self.occ = {}
        for t in self.tiles:
            for c in self.cells(t.block, t.x, t.y):
                self.occ[c] = t
        return self

    def stats(self) -> dict:
        blocks = len(self.tiles)
        tiles = len(self.occ)
        counts: dict[str, int] = {}
        for t in self.tiles:
            counts[t.block] = counts.get(t.block, 0) + 1
        return {"blocks": blocks, "tiles": tiles, "footprint": self.w * self.h, "counts": counts}

    def to_schematic(self):
        tags = {"name": self.name or "mbo", "description": self.description or ""}
        return codec.msch.Schematic(self.w, self.h, tags, [t.as_stile() for t in self.tiles])

    def to_bytes(self) -> bytes:
        return codec.build_schematic_ext(self.to_schematic())

    def snapshot(self) -> list:
        """可序列化的布局（写进 trace.json，供 `mbo verify` 重建）。"""
        return [
            {"block": t.block, "x": t.x, "y": t.y, "rotation": t.rotation,
             "config": _jsonable(t.config)}
            for t in self.tiles
        ]

    @classmethod
    def from_snapshot(cls, data: list, width: int, height: int, sizes: dict, name: str = "",
                      description: str = ""):
        lay = cls(width, height, sizes, name=name, description=description)
        for d in data:
            lay.add(d["block"], d["x"], d["y"], d.get("rotation", 0),
                    _from_jsonable(d.get("config")))
        return lay


def _jsonable(cfg):
    if cfg is None or isinstance(cfg, (bool, int, str)):
        return cfg
    if isinstance(cfg, float):
        return {"__float__": float(cfg), "tag": getattr(cfg, "tag", 3)}
    if isinstance(cfg, (list, tuple)):
        return {"__array__": [_jsonable(v) for v in cfg], "tag": getattr(cfg, "tag", None)}
    if isinstance(cfg, dict):
        return {"__dict__": {k: _jsonable(v) for k, v in cfg.items()}}
    if isinstance(cfg, (bytes, bytearray)):
        import base64

        return {"__bytes__": base64.b64encode(bytes(cfg)).decode("ascii")}
    raise TypeError("不能序列化 config: %r" % (cfg,))


def _from_jsonable(obj):
    if isinstance(obj, dict):
        if "__array__" in obj:
            tag = obj.get("tag")
            return codec.TaggedList([_from_jsonable(v) for v in obj["__array__"]], tag=tag)
        if "__float__" in obj:
            tag = obj.get("tag", 3)
            v = obj["__float__"]
            return codec.TaggedDouble(v, 11) if tag == 11 else v
        if "__dict__" in obj:
            return {k: _from_jsonable(v) for k, v in obj["__dict__"].items()}
        if "__bytes__" in obj:
            import base64

            return base64.b64decode(obj["__bytes__"])
    return obj
