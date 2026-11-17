import argparse, sys, re
sys.stdout.reconfigure(encoding="utf-8")

# 权重表：只写非 0；未赋值的变量读出来就是 0 = 该物品不参与调度
WEIGHTS = [
    ("copper", 0.5), ("lead", 0.5), ("metaglass", 1), ("graphite", 1),
    ("titanium", 5), ("thorium", 2), ("silicon", 5), ("plastanium", 0.8),
    ("phase-fabric", 0.1), ("surge-alloy", 1), ("blast-compound", 0.01),
    ("pyratite", 0.01),
]
# 原版 20 种物品名：供 --supply 时用 draw 一次性声明成 @this 槽位
ITEM_NAMES = "copper lead metaglass graphite sand coal titanium thorium scrap silicon plastanium phase-fabric surge-alloy spore-pod blast-compound pyratite beryllium tungsten oxide carbide".split()
PAD_DEFAULT = "@landing-pad"


class Prog:
    def __init__(self):
        self.items = []
        self.labels = {}
        self.stmts = 0

    def i(self, text):
        self.items.append(("i", text))
        self.stmts += 1

    def l(self, name):
        self.labels[name] = self.stmts
        self.items.append(("l", name))

    def j(self, label, cond, a=None, b=None):
        self.items.append(("j", label, cond, a, b))
        self.stmts += 1

    def count(self):
        return self.stmts

    def render(self, labeled):
        out = []
        for it in self.items:
            if it[0] == "l":
                if labeled:
                    out.append(it[1] + ":")
            elif it[0] == "i":
                out.append(it[1])
            else:
                _, lb, cond, a, b = it
                tgt = lb if labeled else self.labels[lb]
                if cond == "always":
                    out.append("jump %s always" % tgt)
                elif b is None:
                    out.append("jump %s %s %s" % (tgt, cond, a))
                else:
                    out.append("jump %s %s %s %s" % (tgt, cond, a, b))
        return "\n".join(out) + "\n"


def build(a):
    p = Prog()
    pad = a.pad_block
    retry = 2
    sup = a.supply

    for k, v in WEIGHTS:
        p.i("set %s %s" % (k, v))

    p.l("init")
    p.i("set next 0")
    p.i("set core null")
    p.i("set last -1")
    p.i("set uiok 0")
    p.i("set time.rec @time")

    p.l("main")
    p.j("work", "greaterThanEq", "@time", "next")
    p.j("main", "always")
    p.l("work")
    p.i("op add next @time %d" % a.period)

    if not getattr(a, "no_skip", False):
        p.i("sensor tmp.tot core @totalItems")
        p.j("run", "notEqual", "tmp.tot", "last")
        p.j("main", "always")

    p.l("run")
    p.i("set npad 0")
    p.i("set p 0")
    p.l("c0")
    p.j("c1", "greaterThanEq", "p", "@links")
    p.i("getlink b p")
    p.j("c2", "strictEqual", "b", "null")
    p.i("sensor ty b @type")
    p.j("c2", "notEqual", "ty", pad)
    p.i("op add npad npad 1")
    p.l("c2")
    p.i("op add p p 1")
    p.j("c0", "always")
    p.l("c1")

    p.l("l0")
    p.i("sensor cap core @itemCapacity")
    p.j("p1x", "notEqual", "cap", "null")
    p.i("set core null")
    p.i("set ui uiok")
    p.l("fc")
    p.i("lookup unit uty ui")
    p.i("ubind uty")
    p.j("fok", "notEqual", "@unit", "null")
    p.i("op add ui ui 1")
    p.j("fc", "lessThan", "ui", 52)
    p.j("l1b", "always")
    p.l("fok")
    p.i("set uiok ui")
    p.i("ulocate building core false 0 cx cy f core")
    p.i("ucontrol unbind 0 0 0 0 0")
    p.j("p1x", "notEqual", "core", "null")
    p.l("l1b")
    if not a.no_board:
        p.i('print "[#ffd166] 落子 LUOZI[]\\n-调和+占空着陆控制逻辑  \\n\\n[red]启动受阻[gray]\\n[yellow]检查你是否有任意可用单位。[]\\n若有、链接任意数量接收台。而后即可开始。\\n\\nBy - [blue]DeepSeek[] x [blue]Ili[#8abcd1]ary[#654321]艾铭[#ffb6c1]✽"')
        p.i("printflush " + a.board_target)
    p.i("set p 0")
    p.l("l1c")
    p.j("p1x", "greaterThanEq", "p", "@links")
    p.i("getlink b p")
    p.i("op add p p 1")
    p.j("l1c", "strictEqual", "b", "null")
    p.i("sensor cap b @itemCapacity")
    p.j("l1c", "strictEqual", "cap", "null")
    p.j("l1c", "lessThan", "cap", a.core_cap)
    p.i("set core b")

    p.l("p1x")
    p.j("r1", "strictEqual", "core", "null")
    p.i("set i 0")
    p.i("set mx 0")
    p.l("p1")
    p.i("lookup item it i")
    p.i("sensor amt core it")
    p.i("op max mx mx amt")
    p.i("op add i i 1")
    p.j("p1", "lessThan", "i", "@itemCount")
    p.i("op max mx mx 1")

    p.i("set i 0")
    p.i("set sum 0")
    p.l("p2")
    p.i("lookup item it i")
    p.i("sensor amt core it")
    p.i("op sub d mx amt")
    p.i("sensor nm it @name")
    p.i("read w @this nm")
    p.i("op mul d d w")
    if sup:
        p.i("read uo @this nm")
        p.i("op add uf uo %s" % a.supply_c)
        p.i("op div d d uf")
    p.i("op add sum sum d")
    p.i("op add i i 1")
    p.j("p2", "lessThan", "i", "@itemCount")

    p.j("p3", "greaterThan", "sum", "0")
    p.j("r1", "always")
    p.l("p3")
    p.i("set i 0")
    p.i("set cu 0")
    p.i("set p 0")
    p.l("p3l")
    p.i("set cnt 0")
    p.i("set busy 0")
    p.i("lookup item it i")
    p.i("sensor amt core it")
    p.i("op sub d mx amt")
    p.i("sensor nm it @name")
    p.i("read w @this nm")
    p.i("op mul d d w")
    if sup:
        p.i("read uo @this nm")
        p.i("op add uf uo %s" % a.supply_c)
        p.i("op div d d uf")
    p.j("p3n", "lessThanEq", "d", 0)
    p.i("op add cu cu d")
    p.i("op mul tk npad cu")
    p.i("op div tk tk sum")
    p.i("op floor tk tk")
    p.j("p3n", "greaterThanEq", "cnt", "tk")
    p.l("p3a")
    p.j("p3n", "greaterThanEq", "p", "@links")
    p.i("getlink b p")
    p.i("op add p p 1")
    p.j("p3a", "strictEqual", "b", "null")
    p.i("sensor ty b @type")
    p.j("p3a", "notEqual", "ty", pad)
    p.i("control config b it")
    p.i("control enabled b true")
    p.i("op add cnt cnt 1")
    if sup:
        p.i("sensor bt b @totalItems")
        p.i("op add busy busy bt")
    if not a.no_board:
        p.i("printchar it")
    p.j("p3a", "lessThan", "cnt", "tk")
    p.l("p3n")
    if sup:
        p.j("p3w", "lessThanEq", "cnt", 0)
        p.i("op div smp busy cnt")
        p.i("op div smp smp 100")
        p.j("p3x", "always")
        p.l("p3w")
        p.i("set smp 0")
        p.l("p3x")
        p.i("op sub tmp.d smp uo")
        p.i("op mul tmp.d tmp.d %s" % a.supply_lr)
        p.i("op add smp uo tmp.d")
        p.i("write smp @this nm")
    if not a.no_board:
        p.j("p3q", "lessThanEq", "cnt", 0)
        p.i('print "\\n"')
        p.l("p3q")
    p.i("op add i i 1")
    p.j("p3l", "lessThan", "i", "@itemCount")
    if not a.no_board:
        p.i("op sub delta.s @time time.rec")
        p.i("op idiv delta.s delta.s 10")
        p.i("op div delta.s delta.s 100")
        p.i("set time.rec @time")
        p.i('print "\\n控制周期：{0}s"')
        p.i("format delta.s")
        p.i('print "\\nBy - [blue]DeepSeek[] x [blue]Ili[#8abcd1]ary[#654321]艾铭[#ffb6c1]✽"')
        p.i("printflush " + a.board_target)
        p.i('print "[#ffd166] 落子 LUOZI[]\\n-调和+占空着陆控制逻辑  \\n\\n正在调配\\n{0}  x\\n\\n"')
        p.i("format npad")

    p.i("sensor last core @totalItems")
    if a.probe_links:
        for k in range(1, a.probe_links + 1):
            p.i("sensor pcfg%d sorter%d @config" % (k, k))
    p.j("main", "always")

    p.l("r1")
    if not a.no_board:
        p.i("printflush " + a.board_target)
    p.i("op add next @time %d" % (retry * 1000))
    p.j("main", "always")

    if sup:
        # 不可达：把 20 个物品名一次性声明成 @this 槽位（write/read 才不丢）
        for k in range(0, len(ITEM_NAMES), 6):
            p.i("draw triangle " + " ".join(ITEM_NAMES[k:k + 6]))
        p.j("main", "always")
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-skip", action="store_true")
    ap.add_argument("--period", type=int, default=10000)
    ap.add_argument("--pad-block", default=PAD_DEFAULT)
    ap.add_argument("--core-cap", default="4000")
    ap.add_argument("--board-target", default="message1")
    ap.add_argument("--no-board", action="store_true")
    ap.add_argument("--supply", action="store_true")
    ap.add_argument("--supply-c", default="0.02")
    ap.add_argument("--supply-lr", default="0.25")
    ap.add_argument("--probe-links", type=int, default=0)
    ap.add_argument("-o", "--out", default="")
    ap.add_argument("--labeled", action="store_true")
    a = ap.parse_args()
    p = build(a)
    src = p.render(a.labeled)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(src)
        print("statements: %d" % p.count())
        print("wrote " + a.out)
    else:
        print(src)


if __name__ == "__main__":
    main()
