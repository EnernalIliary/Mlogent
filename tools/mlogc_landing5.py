import argparse, re, sys, os
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mlogc_landing4 import Prog, WEIGHTS

# 权重表（与 v5 一致）：只写非 0 项；未列出的物品权重 0
WEIGHT = dict(WEIGHTS)

# 默认物品表 = 本星（Serpulo 系）能落地的原版 16 种。
# 不含 beryllium / tungsten / oxide / carbide：它们在别的星球，LandingPad.config 会静默拒绝。
# 权重 0 的 sand/coal/scrap/spore-pod 必须留着 —— 它们参与 mx（最大库存），只是不参与分配。
DEFAULT_ITEMS = ("copper lead metaglass graphite sand coal titanium thorium scrap silicon "
                 "plastanium phase-fabric surge-alloy spore-pod blast-compound pyratite")


def build(a):
    p = Prog()
    items = [s for s in re.split(r"[,\s]+", a.items) if s]
    pad = a.pad_block
    retry = 2
    sup = a.supply
    board = not a.no_board
    # 权重 0 的物品只参与 mx（最大库存），不参与打分/分配 —— 展开时直接不生成
    scored = [it for it in items if WEIGHT.get(it, 0.0) > 0]
    wsum = sum(WEIGHT.get(it, 0.0) for it in scored)

    # 权重：w.<物品>；@this 槽位用裸物品名 —— 两个名字空间，互不覆盖
    for it in items:
        if it in WEIGHT:
            p.i("set w.%s %s" % (it.replace("-", "_"), WEIGHT[it]))
    if sup:
        for it in items:
            p.i("set %s 0" % it)

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

    if not a.no_skip:
        p.i("sensor tmp.tot core @totalItems")
        p.j("run", "notEqual", "tmp.tot", "last")
        p.j("main", "always")

    # ---------- L0：每圈数台（只认类型，不管状态）；到上限就停 ----------
    p.l("run")
    p.i("set npad 0")
    p.i("set p 0")
    p.l("c0")
    p.j("c1", "greaterThanEq", "p", "@links")
    if a.max_pads:
        p.j("c1", "greaterThanEq", "npad", a.max_pads)
    p.i("getlink b p")
    p.j("c2", "strictEqual", "b", "null")
    p.i("sensor ty b @type")
    p.j("c2", "notEqual", "ty", pad)
    p.i("op add npad npad 1")
    p.l("c2")
    p.i("op add p p 1")
    p.j("c0", "always")
    p.l("c1")

    # ---------- L1：核心（缓存 → 借单位 ulocate → 直连容量判定）----------
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
    if board:
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

    # ---------- pass1：mx（+ 融合模式顺带算 Σw·amt）----------
    p.i("set mx 0")
    if a.fuse:
        p.i("set sw 0")
    for it in items:
        p.i("sensor amt core @%s" % it)
        p.i("op max mx mx amt")
        if a.fuse and WEIGHT.get(it, 0.0) > 0:
            # 权重 0 的物品 w 变量没赋值（读作 0），连乘加都省掉，顺带消掉 check 的 INFO
            p.i("op mul t amt w.%s" % it.replace("-", "_"))
            p.i("op add sw sw t")
    p.i("op max mx mx 1")

    if a.fuse:
        # sum = mx·Σw − Σ(w·amt)：两项都已在 pass1 得到，整趟 pass2 省掉
        p.i("op mul sum mx %s" % wsum)
        p.i("op sub sum sum sw")
    else:
        # ---------- pass2：sum ----------
        p.i("set sum 0")
        for it in scored:
            p.i("sensor amt core @%s" % it)
            p.i("op sub d mx amt")
            p.i("op mul d d w.%s" % it.replace("-", "_"))
            if sup:
                p.i('read uo @this "%s"' % it)
                p.i("op add uf uo %s" % a.supply_c)
                p.i("op div d d uf")
            p.i("op add sum sum d")

    p.j("p3", "greaterThan", "sum", "0")
    p.j("r1", "always")

    # ---------- pass3：累计取整 + 逐物品展开下发 ----------
    p.l("p3")
    p.i("set cu 0")
    p.i("op div rcp npad sum")   # 每圈一次，省掉每物品一条 op div
    p.i("set cnt 0")   # 全局已下发台数（与累计目标 tk 比较，绝不能逐物品清零）
    p.i("set p 0")
    for k, it in enumerate(scored):
        skip = "s%d" % k
        lp = "ld%d" % k
        lend = "lend%d" % k
        p.i("set nc 0")   # 本物品拿到几台
        p.i("set busy 0")
        p.i("sensor amt core @%s" % it)
        p.i("op sub d mx amt")
        p.i("op mul d d w.%s" % it.replace("-", "_"))
        if sup:
            p.i('read uo @this "%s"' % it)
            p.i("op add uf uo %s" % a.supply_c)
            p.i("op div d d uf")
        p.j(skip, "lessThanEq", "d", 0)
        p.i("op add cu cu d")
        p.i("op mul tk cu rcp")
        p.i("op floor tk tk")
        p.j(skip, "greaterThanEq", "cnt", "tk")
        p.i("set it @%s" % it)
        p.l(lp)
        p.j(lend, "greaterThanEq", "p", "@links")
        p.i("getlink b p")
        p.i("op add p p 1")
        p.j(lp, "strictEqual", "b", "null")
        p.i("sensor ty b @type")
        p.j(lp, "notEqual", "ty", pad)
        p.i("control config b it")
        p.i("control enabled b true")
        p.i("op add cnt cnt 1")
        p.i("op add nc nc 1")
        if sup:
            p.i("sensor bt b @totalItems")
            p.i("op add busy busy bt")
        if board:
            p.i("printchar it")
        p.j(lp, "lessThan", "cnt", "tk")
        p.l(lend)
        p.l(skip)
        if sup:
            p.j("sw%d" % k, "lessThanEq", "nc", 0)
            p.i("op div smp busy nc")
            p.i("op div smp smp 100")
            p.j("sx%d" % k, "always")
            p.l("sw%d" % k)
            p.i("set smp 0")
            p.l("sx%d" % k)
            p.i("op sub tmp.d smp uo")
            p.i("op mul tmp.d tmp.d %s" % a.supply_lr)
            p.i("op add smp uo tmp.d")
            p.i('write smp @this "%s"' % it)
        if board:
            p.j("q%d" % k, "lessThanEq", "nc", 0)
            p.i('print "\\n"')
            p.l("q%d" % k)

    # ---------- 兜底：浮点漂移可能让 floor 之和 < npad，把剩下的台补给末位物品 ----------
    # 正常路径只花 1 条 jump；只在漂移/末位物品无缺口时才真正进入
    p.l("p3z")
    p.j("p3e", "greaterThanEq", "cnt", "npad")
    p.i("set it @%s" % scored[-1])
    p.l("p3w")
    p.j("p3e", "greaterThanEq", "p", "@links")
    p.i("getlink b p")
    p.i("op add p p 1")
    p.j("p3w", "strictEqual", "b", "null")
    p.i("sensor ty b @type")
    p.j("p3w", "notEqual", "ty", pad)
    p.i("control config b it")
    p.i("control enabled b true")
    p.i("op add cnt cnt 1")
    p.j("p3z", "always")
    p.l("p3e")

    if board:
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
    p.j("main", "always")

    p.l("r1")
    if board:
        p.i("printflush " + a.board_target)
    p.i("op add next @time %d" % (retry * 1000))
    p.j("main", "always")
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-skip", action="store_true", help="每圈都重算（不给库存不变跳过），用于测真实周期")
    ap.add_argument("--period", type=int, default=10000)
    ap.add_argument("--max-pads", type=int, default=8)
    ap.add_argument("--items", default=DEFAULT_ITEMS)
    ap.add_argument("--pad-block", default="@landing-pad")
    ap.add_argument("--core-cap", default="4000")
    ap.add_argument("--board-target", default="message1")
    ap.add_argument("--no-board", action="store_true")
    ap.add_argument("--supply", action="store_true")
    ap.add_argument("--fuse", action="store_true")
    ap.add_argument("--supply-c", default="0.02")
    ap.add_argument("--supply-lr", default="0.25")
    ap.add_argument("-o", "--out", default="")
    ap.add_argument("--labeled", action="store_true")
    a = ap.parse_args()
    if a.fuse and a.supply:
        raise SystemExit("--fuse 只适用于不带 --supply 的线性打分")
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
