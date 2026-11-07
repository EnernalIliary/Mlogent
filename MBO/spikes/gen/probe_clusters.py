"""单端口可行性探针：把「端口簇」当目标，看 1 簇能不能成立。

端口簇 = 所有端口格（item-source / item-void）按 4-邻接分组后的组数。
- 1 簇：源和黑洞相邻，等于"工厂只有一个开口"；
- 2 簇：一进一出各占一个开口（最少 2 个端口方块：源只发不收、黑洞只收不发）。
"""
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from mbo.gamedata import GameData                      # noqa: E402
from mbo.production import expand                     # noqa: E402
from mbo import search as S                           # noqa: E402

PORTS = ("item-source", "item-void", "liquid-source", "liquid-void")
SHORT = {"item-source": "S", "item-void": "x", "liquid-source": "L", "liquid-void": "y"}


def port_cells(cand, gd):
    out = set()
    for name, x, y, _rot, _item in cand.blocks:
        if name in PORTS:
            size = gd.block(name).size
            for dx in range(size):
                for dy in range(size):
                    out.add((x + dx, y + dy))
    return out


def clusters(cells):
    left = set(cells)
    n = 0
    while left:
        n += 1
        stack = [left.pop()]
        while stack:
            x, y = stack.pop()
            for p in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if p in left:
                    left.discard(p)
                    stack.append(p)
    return n


def port_blocks(cand):
    return sum(1 for name, *_ in cand.blocks if name in PORTS)


def ascii_of(lay, gd):
    out = []
    for y in range(lay.h):
        line = ""
        for x in range(lay.w):
            t = lay.tile_at(x, y)
            if t is None:
                line += " "
            elif t.block in SHORT:
                line += SHORT[t.block]
            elif t.block == "graphite-press":
                line += "M"
            elif t.block in ("conveyor", "duct"):
                line += ">v<^"[t.rotation]
            elif t.block in ("overflow-gate", "underflow-gate"):
                line += "+"
            elif t.block in ("router", "junction"):
                line += "n"
            else:
                line += "?"
        if line.strip():
            out.append(line.rstrip())
    return "\n".join(out)


def main():
    gd = GameData()
    plan = expand(gd, "graphite", 1.0, ["coal"])
    cands = S.enumerate_candidates(gd, plan)
    print("枚举候选 %d 张（含模板另算）" % len(cands))

    per_cluster = {}
    for c in cands:
        k = clusters(port_cells(c, gd))
        per_cluster.setdefault(k, []).append(c)

    print("\n簇数 | 候选数 | 其中可行(端口在外+产能够)")
    for k in sorted(per_cluster):
        group = per_cluster[k]
        ok = [c for c in group if c.ok_need]
        print("  %d  | %6d | %6d" % (k, len(group), len(ok)))

    print("\n每簇数下的最省可行解：")
    for k in sorted(per_cluster):
        ok = [c for c in per_cluster[k] if c.ok_need]
        if not ok:
            print("  %d 簇：无可行解" % k)
            continue
        b = min(ok, key=lambda c: (c.tiles, c.box, c.label))
        lay = S.to_layout(b, gd).crop()
        print("  %d 簇：%d 工厂格 / box %d / %d 端口方块 / %.4f/s / %s"
              % (k, b.tiles, b.box, port_blocks(b), b.rate, b.label))
        for line in ascii_of(lay, gd).splitlines():
            print("      " + line)

    # 1 簇为什么一张都不可行：看是被"端口在外"还是被产能否掉
    one = per_cluster.get(1, [])
    if one:
        print("\n1 簇候选 %d 张，逐张看淘汰原因：" % len(one))
        for c in one[:6]:
            lay = S._make(gd, c.blocks, S.GRID)
            if lay is None:
                print("  - %s：建不出布局" % c.label)
                continue
            from mbo import logistics
            outside, msg = logistics.ports_outside(lay, gd)
            est = logistics.estimate(lay, gd, plan)
            print("  - %-46s 端口在外=%s rate=%.4f %s"
                  % (c.label, outside, est["rate"],
                     "" if outside else ("(%s)" % msg)))
    else:
        print("\n枚举里根本没有 1 簇候选（源与黑洞永远不相邻）。")

    # 模板也看一眼
    print("\n模板候选的簇数：")
    for c in S.template_candidates(gd, plan):
        k = clusters(port_cells(c, gd))
        print("  %-22s %d 簇 / %d 端口 / %d 格 / %.4f/s"
              % (c.label, k, port_blocks(c), c.tiles, c.rate))


if __name__ == "__main__":
    main()
