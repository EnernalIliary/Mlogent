"""L0：版本化游戏数据快照。

快照目录：`MBO/gamedata/<snapshot>/gamedata.json` + `meta.json`。
`meta.json` 记录 json 的 sha256、来源 jar、导出脚本与导出时间；运行时把
`snapshot_id`（如 `v160.7@ab12cd34`）写进 `trace.json`，保证"这组数字是哪份数据算出来的"可追溯。

字段口径（与 docs/11 一致，别再各处重算）：

- `recipe.craftTime` 是**帧**，`cycles_per_second = 60 / craftTime`；
- `recipe.inputs` 是 consumers 列表，每个 consumer 的 `items` 才是 (name, amount)；
- `recipe.outputItems` 是扁平的 (name, amount) 列表；
- `power.usagePerSecond` / `power.productionPerSecond` 是**每秒**（UI 值，= per-tick × 60）；
- `power-source`（沙盒）的 `productionPerSecond` 是 999999.96，按“无限”处理，不参与净功率。
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field

MBO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOT_ROOT = os.path.join(MBO_ROOT, "gamedata")
DEFAULT_SNAPSHOT = "v160.7"


@dataclass(frozen=True)
class Recipe:
    """一个 crafting 配方。`craft_time_frames` 是帧（不是秒！）。"""

    craft_time_frames: int
    inputs: tuple = ()            # ((item, amount), ...) 每批
    outputs: tuple = ()           # ((item, amount), ...) 每批
    output_liquids: tuple = ()

    @property
    def cycles_per_second(self) -> float:
        return 60.0 / self.craft_time_frames

    @property
    def inputs_per_second(self) -> dict:
        r = self.cycles_per_second
        return {name: amt * r for name, amt in self.inputs}

    @property
    def outputs_per_second(self) -> dict:
        r = self.cycles_per_second
        return {name: amt * r for name, amt in self.outputs}


@dataclass
class Block:
    name: str
    id: int
    size: int
    category: str
    recipe: Recipe | None = None
    power_usage_per_second: float = 0.0
    power_production_per_second: float = 0.0
    consumes_power: bool = False
    produces_power: bool = False
    rotate: bool = False
    item_capacity: int = 0
    laser_range: float = 0.0
    max_nodes: int = 0
    raw: dict = field(default_factory=dict)

    @property
    def is_sandbox_power(self) -> bool:
        return self.name == "power-source"

    @property
    def input_items(self) -> tuple:
        return self.recipe.inputs if self.recipe else ()


def _digest(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _recipe_of(raw: dict) -> Recipe | None:
    r = raw.get("recipe") or {}
    frames = r.get("craftTime") or 0
    if frames <= 0:
        return None
    inputs = []
    for cons in r.get("inputs") or []:
        for it in cons.get("items") or []:
            inputs.append((it["name"], float(it["amount"])))
    outputs = [(it["name"], float(it["amount"])) for it in r.get("outputItems") or []]
    liquids = [(it["name"], float(it["amount"])) for it in r.get("outputLiquids") or []]
    return Recipe(int(frames), tuple(inputs), tuple(outputs), tuple(liquids))


class GameData:
    """一份只读快照。`blocks` 以方块名为键。"""

    def __init__(self, snapshot: str = DEFAULT_SNAPSHOT):
        self.snapshot = snapshot
        d = os.path.join(SNAPSHOT_ROOT, snapshot)
        gpath = os.path.join(d, "gamedata.json")
        mpath = os.path.join(d, "meta.json")
        if not os.path.exists(gpath):
            raise FileNotFoundError(
                "缺少数据快照 %s；先跑 `python -m mbo.cli build-snapshot` 或复制 spikes/data/gamedata.json" % gpath
            )
        self.path = gpath
        with open(gpath, encoding="utf-8") as fh:
            raw = json.load(fh)
        self.sha256 = _digest(gpath)
        self.meta = {}
        if os.path.exists(mpath):
            with open(mpath, encoding="utf-8") as fh:
                self.meta = json.load(fh)
        self.raw_meta = raw.get("meta", {})
        self.items = {it["name"]: it for it in raw.get("items", [])}
        self.liquids = {lq["name"]: lq for lq in raw.get("liquids", [])}
        self.blocks = {b["name"]: self._block(b) for b in raw.get("blocks", [])}

    # ------------------------------------------------------------------ 构造
    @staticmethod
    def _block(raw: dict) -> Block:
        pw = raw.get("power") or {}
        lg = raw.get("logisticsExtras") or {}
        return Block(
            name=raw["name"],
            id=int(raw["id"]),
            size=int(raw.get("size") or 1),
            category=raw.get("category") or "unknown",
            recipe=_recipe_of(raw),
            power_usage_per_second=float(pw.get("usagePerSecond") or 0.0),
            power_production_per_second=float(pw.get("productionPerSecond") or 0.0),
            consumes_power=bool(pw.get("consumesPower")),
            produces_power=bool(pw.get("outputsPower")),
            rotate=bool(raw.get("rotate")),
            item_capacity=int(raw.get("itemCapacity") or 0),
            laser_range=float(lg.get("laserRange") or 0.0),
            max_nodes=int(lg.get("maxNodes") or 0),
            raw=raw,
        )

    # ------------------------------------------------------------------ 查询
    def size(self, name: str) -> int:
        b = self.blocks.get(name)
        return b.size if b else 1

    def item_id(self, name: str) -> int:
        if name not in self.items:
            raise KeyError("快照里没有物品 %r（可用：%s）" % (name, ", ".join(sorted(self.items))))
        return int(self.items[name]["id"])

    def item_name(self, iid) -> str | None:
        for name, it in self.items.items():
            if int(it["id"]) == int(iid):
                return name
        return None

    def block(self, name: str) -> Block:
        if name not in self.blocks:
            raise KeyError("快照里没有方块 %r" % name)
        return self.blocks[name]

    @property
    def snapshot_id(self) -> str:
        return "%s@%s" % (self.snapshot, self.sha256[:12])

    # ------------------------------------------------------------------ 派生
    def crafters(self) -> list:
        return [b for b in self.blocks.values() if b.recipe is not None]

    def producers_of(self, item: str) -> list:
        return [b for b in self.crafters() if any(n == item for n, _ in b.recipe.outputs)]
