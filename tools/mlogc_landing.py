# -*- coding: utf-8 -*-
"""群控接收台（着陆台）缺口加权调度生成器。

算法（调和 v4.5 的骨架 + 三项修正）：
  1. 逐物品读核心库存，取全局最大值 mx
  2. score_i = (w_i * (mx - amount_i)) ^ e      —— 超线性放大缺口
  3. vol = sum(score) / N，沿累计 score 轴按 vol 切片，每片一台
     （切片左边界属于谁，这一台就配给谁；余量 carry 给下一片）
修正：
  * M 用 @itemCount 动态，不再硬编码 20
  * 资格过滤：@efficiency < 1（没水）或 @totalItems > 0（满仓）的台跳过
  * 不依赖 block logic id 顺序（不建 name 表，直接重算）
"""
import argparse
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 抄自「调和着陆控制逻辑 v4.5」的初始权重；键 = 物品 @name
WEIGHTS = [
    ("copper", "0.5"), ("lead", "0.5"), ("metaglass", "1"), ("graphite", "1"),
    ("sand", "0"), ("coal", "0"), ("titanium", "5"), ("thorium", "2"),
    ("scrap", "0"), ("silicon", "5"), ("plastanium", "0.8"),
    ("phase-fabric", "0.1"), ("surge-alloy", "1"), ("spore-pod", "0"),
    ("blast-compound", "0.01"), ("pyratite", "0.01"),
    ("beryllium", "0"), ("tungsten", "0"), ("oxide", "0"), ("carbide", "0"),
]

HEADER = [
    "[#ffd166]群控接收台 · 缺口加权调度 v1[]",
    "By DeepSeek  ·  抄 [blue]Il[#7d9396]ia[#716b5b]ry[#654321]艾铭[] 的权重表",
    "N 台 / @itemCount 件；score=(权重x缺口)^e，累计切片分配",
    "link0=message1，link1..N=着陆台；改台数只改 set npad",
]


class Prog:
    def __init__(self):
        self.items = []
        self.stmts = 0
        self.labels = {}

    def i(self, text):
        self.items.append(("i", text))
        self.stmts += 1

    def l(self, name):
        self.items.append(("l", name))
        self.labels[name] = self.stmts

    def j(self, label, cond="always", a="0", b="false"):
        self.items.append(("j", label, cond, a, b))
        self.stmts += 1

    def render(self):
        out = []
        for it in self.items:
            if it[0] == "i":
                out.append(it[1])
            elif it[0] == "l":
                out.append(it[1] + ":")
            else:
                _, lab, cond, a, b = it
                if cond == "always":
                    out.append("jump %s always" % lab)
                else:
                    out.append("jump %s %s %s %s" % (lab, cond, a, b))
        return "\n".join(out) + "\n"


def build(a):
    p = Prog()
    for line in HEADER:
        p.i('print "%s"' % line)
    p.i("printflush message1")

    if not a.no_weights:
        for name, w in WEIGHTS:
            p.i("set %s %s" % (name, w))

    if a.period > 0:
        p.i("set gate 0")
    p.l("main")
    if a.period > 0:
        p.j("work", "greaterThanEq", "@time", "gate")
        p.j("main", "always")
        p.l("work")
    p.j("p1", "notEqual", "core", "null")

    # ---- 没有核心：借一只单位去 ulocate，用完 unbind ----
    p.i("set ui 0")
    p.l("fc")
    p.i("lookup unit uty ui")
    p.i("ubind uty")
    p.i("op add ui ui 1")
    p.j("fok", "notEqual", "@unit", "null")
    p.j("fc", "lessThan", "ui", "52")
    p.l("fok")
    p.j("main", "strictEqual", "@unit", "null")
    p.i("ulocate building core false @copper cx cy f core")
    p.i("ucontrol unbind 0 0 0 0 0")
    p.j("main", "strictEqual", "core", "null")

    # ---- pass1: 全局最大库存 mx ----
    p.l("p1")
    p.i("set i 0")
    p.i("set mx 0")
    p.l("p1l")
    p.i("lookup item it i")
    p.i("sensor amt core it")
    p.i("op max mx mx amt")
    p.i("op add i i 1")
    p.j("p1l", "lessThan", "i", "@itemCount")

    # ---- pass2: sum(score) ----
    p.i("set i 0")
    p.i("set sum 0")
    p.l("p2l")
    p.i("lookup item it i")
    p.i("sensor amt core it")
    p.i("op sub d mx amt")
    p.i("sensor nm it @name")
    p.i("read w @this nm")
    p.i("op mul d d w")
    p.i("op pow d d @e")
    p.i("op add sum sum d")
    p.i("op add i i 1")
    p.j("p2l", "lessThan", "i", "@itemCount")

    p.i("op div vol sum npad")
    p.j("p3", "greaterThan", "vol", "0")
    p.j("done", "always")

    # ---- pass3: 累计切片 ----
    p.l("p3")
    p.i("set i 0")
    p.i("set pf 0")
    p.i("set cfg null")
    p.i("set pk %d" % a.first_link)
    p.l("p3l")
    p.i("lookup item it i")
    p.i("sensor amt core it")
    p.i("op sub d mx amt")
    p.i("sensor nm it @name")
    p.i("read w @this nm")
    p.i("op mul d d w")
    p.i("op pow d d @e")
    p.j("p3n", "lessThanEq", "d", "0")
    p.j("p3c", "notEqual", "pf", "0")
    p.i("set cfg it")
    p.l("p3c")
    p.i("op add pf pf d")
    p.l("p3p")
    p.j("p3n", "lessThan", "pf", "vol")
    p.j("p3k", "greaterThan", "pk", "npad")
    p.i("getlink pad pk")
    p.j("p3s", "strictEqual", "pad", "null")
    if not a.no_elig:
        p.i("sensor eff pad @efficiency")
        p.j("p3s", "lessThan", "eff", "1")
        p.i("sensor tot pad @totalItems")
        p.j("p3s", "greaterThan", "tot", "0")
    p.i("control config pad cfg 0 0 0")
    if a.enable:
        p.i("control enabled pad true 0 0 0")
    p.i("op sub pf pf vol")
    p.i("set cfg it")
    p.i("op add pk pk 1")
    p.j("p3p", "always")
    p.l("p3s")
    p.i("op add pk pk 1")
    p.j("p3p", "always")
    p.l("p3k")
    p.j("done", "always")
    p.l("p3n")
    p.i("op add i i 1")
    p.j("p3l", "lessThan", "i", "@itemCount")
    p.l("done")
    if a.period > 0:
        p.i("op add gate @time %d" % a.period)
    p.j("main", "always")
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=15, help="着陆台数量（默认 15）")
    ap.add_argument("--first-link", type=int, default=1, help="第一个台的链接下标（默认 1，0 留给 message1）")
    ap.add_argument("--no-elig", action="store_true", help="关闭资格过滤（不检查水和空仓）")
    ap.add_argument("--no-weights", action="store_true", help="不生成权重表")
    ap.set_defaults(enable=True)
    ap.add_argument("--period", type=int, default=6000, help="重算周期 ms（0 = 每圈都算）")
    ap.add_argument("--no-enable", dest="enable", action="store_false", help="不生成 control enabled（默认生成，用来救回被 disable 的台）")
    ap.add_argument("-o", "--out", default="out/landing.labels.mlog")
    a = ap.parse_args()
    p = build(a)
    p.i("set npad %d" % a.n)
    # npad 必须在 pass 之前：把它挪到 main 之前
    text = p.render()
    # 简单修正：把 set npad 从末尾移到 main 标签前
    text = text.replace("main:\n", "set npad %d\nmain:\n" % a.n, 1)
    text = text.replace("jump main always\nset npad %d\n" % a.n, "jump main always\n")
    open(a.out, "w", encoding="utf-8", newline="\n").write(text)
    print("statements:", p.stmts - 1)
    print("wrote", a.out)


if __name__ == "__main__":
    main()