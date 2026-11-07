"""一次性补丁：重写 mbo/logistics.py 的 build_net（建边修正）。"""
import pathlib

NEW = '''def build_net(lay, gd, item: str, want: str) -> _Dinic:
    """按 item / 方向建容量网络。want="in" 供给机器，want="out" 收集机器产出。

    节点约定：每个方块都有入口 `_in(t)` 与出口 `_out(t)`；
    - 传送带/门/路由器/交叉器：入口→出口一条 `TILE_CAP` 边（整格吞吐上限）；
      传送带的出口只连**正前方**一格（方向性），其余方块出口可连所有相邻入口；
    - 机器：入口→T 容量=该物品每秒需求（in），或 S→出口 容量=每秒产出（out）；
    - 端口：item-source 接 S，item-void/容器/仓库 接 T。
    """
    d = _Dinic()
    S, T = ("S",), ("T",)

    def is_transit(b):
        return b in TRANSPORT or b in NODES

    def accepts(tile) -> bool:
        """该方块能否作为本方向的落点。"""
        b = tile.block
        if is_transit(b):
            return True
        if want == "in":
            return _machine(gd, tile) is not None
        return b in SINKS

    # 1) 所有运输/节点方块：入口 → 出口
    for t in lay.tiles:
        if is_transit(t.block):
            d.add(_in(t), _out(t), TILE_CAP)

    # 2) 传送带方向性：只推给正前方
    for t in lay.tiles:
        if t.block in TRANSPORT:
            f = _front(lay, t)
            if f is not None and accepts(f) and f.block not in TRANSPORT or (
                    f is not None and accepts(f)):
                d.add(_out(t), _in(f), TILE_CAP)

    # 3) 门/路由器/交叉器：任意相邻运输方块或节点之间可通（整格容量已在上一步）
    for t in lay.tiles:
        if t.block in NODES:
            for o in _neighbors(lay, t):
                if o.block in NODES:
                    d.add(_out(o), _in(t), TILE_CAP)
                elif o.block in TRANSPORT:
                    # 带子只在自己朝向门时才向门送货；门可以往任何相邻带子送货
                    if _front(lay, o) is t:
                        d.add(_out(o), _in(t), TILE_CAP)
                if is_transit(o.block):
                    d.add(_out(t), _in(o), TILE_CAP)

    # 4) 机器
    for t in lay.tiles:
        b = _machine(gd, t)
        if b is None:
            continue
        if want == "in":
            need = b.recipe.inputs_per_second.get(item, 0.0)
            if need <= 1e-9:
                continue
            d.add(_in(t), T, need)
            for o in _neighbors(lay, t):
                if o.block in NODES:
                    d.add(_out(o), _in(t), TILE_CAP)
                elif o.block in TRANSPORT and _front(lay, o) is t:
                    d.add(_out(o), _in(t), TILE_CAP)
        else:
            out = b.recipe.outputs_per_second.get(item, 0.0)
            if out <= 1e-9:
                continue
            d.add(S, _out(t), out)
            for o in _neighbors(lay, t):
                if is_transit(o.block) or o.block in SINKS:
                    d.add(_out(t), _in(o), TILE_CAP)

    # 5) 端口
    for t in lay.tiles:
        if t.block == "item-source" and want == "in":
            d.add(S, _out(t), SOURCE_CAP)
            for o in _neighbors(lay, t):
                if accepts(o):
                    d.add(_out(t), _in(o), SOURCE_CAP)
        elif t.block in SINKS and want == "out":
            d.add(_in(t), T, 1e12)
    return d


'''

p = pathlib.Path("mbo/logistics.py")
s = p.read_text(encoding="utf-8")
i = s.index("def build_net")
j = s.index("def flow(")
p.write_text(s[:i] + NEW + s[j:], encoding="utf-8")
print("patched", len(s), "->", len(p.read_text(encoding="utf-8")))
