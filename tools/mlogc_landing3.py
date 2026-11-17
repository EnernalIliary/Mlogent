# -*- coding: utf-8 -*-
"""群控接收台 v3 —— 精简版 + 信息板 UI

结构（一段一句话）：
  权重表 -> wait -> [UI] -> 库存未变就跳过 -> 数台(npap) -> 找核心 -> pass1 求 mx
  -> pass2 求 sum -> pass3 累计切片下发 -> 缓存库存 -> 回到 wait

相对 v2 的三处精简：
  1) 权重只写非 0 的（未赋值的变量读成 0 = 不参与），20 行 -> 12 行
  2) 库存（核心 @totalItems）没变就整圈跳过，稳态每圈只烧 ~10 条指令
  3) 核心定位去掉多余的重试标号
  4) 信息板 = message1 文本板：重算时 print 一次「台数 + 核心名 + 每种货分了几台」
"""
import argparse, re, sys

sys.stdout.reconfigure(encoding='utf-8')

PAD_DEFAULT = "@landing-pad"

WEIGHTS = [
    ("copper", "0.5"), ("lead", "0.5"), ("metaglass", "1"), ("graphite", "1"),
    ("titanium", "5"), ("thorium", "2"), ("silicon", "5"), ("plastanium", "0.8"),
    ("phase-fabric", "0.1"), ("surge-alloy", "1"),
    ("blast-compound", "0.01"), ("pyratite", "0.01"),
]


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

    def j(self, label, cond="always", a=None, b=None):
        self.items.append(("j", label, cond, a, b))
        self.stmts += 1

    def count(self):
        return self.stmts

    def render(self, labeled=False):
        out = []
        for it in self.items:
            if it[0] == "l":
                if labeled:
                    out.append(it[1] + ":")
                continue
            if it[0] == "i":
                out.append(it[1])
                continue
            _, label, cond, a, b = it
            tgt = label if labeled else str(self.labels[label])
            if cond == "always":
                out.append("jump %s always" % tgt)
            else:
                out.append("jump %s %s %s %s" % (tgt, cond, a, b))
        return "\n".join(out) + "\n"


def build(a):
    p = Prog()
    pad = a.pad_block
    retry = 2

    if a.header:
        for line in a.header.split("|"):
            p.i('print "%s"' % line)

    # ---- 权重表：只写非 0；没赋值的变量读成 0 = 该物品不参与 ----
    for k, v in WEIGHTS:
        p.i("set %s %s" % (k, v))

    # ---- init ----
    p.l("init")
    p.i("set next 0")
    p.i("set npad 0")
    p.i("set p 0")
    p.i("set i 0")
    p.i("set mx 0")
    p.i("set sum 0")
    p.i("set vol 0")
    p.i("set pf 0")
    p.i("set core null")
    p.i("set last -1")
    p.i("set uiok 0")

    p.l("main")
    p.j("work", "greaterThanEq", "@time", "next")
    p.j("main", "always")
    p.l("work")
    p.i("op add next @time %d" % a.period)

    # ---------------- 逻辑显示屏（可选，--hud 才画） ----------------
    if a.hud:
        p.i("draw clear 0.02 0.03 0.05")
        p.i("sensor tmp.ds display1 @displayWidth")
        p.j("hd0", "notEqual", "tmp.ds", "null")
        p.i("set tmp.ds 64")
        p.l("hd0")
        p.i("op div tmp.cell tmp.ds 8")
        p.i("op sub tmp.sz tmp.cell 1")
        p.i("op sub tmp.ty tmp.ds 12")
        p.i("draw color 255 200 90 255")
        p.i('print "PADS "')
        p.i("print npad")
        p.i("draw print 2 tmp.ty bottomLeft")
        p.i("set p 0")
        p.i("set hx 1")
        p.i("op sub hy tmp.ds 20")
        p.l("h0")
        p.j("h1", "greaterThanEq", "p", "@links")
        p.i("getlink b p")
        p.i("op add p p 1")
        p.j("h0", "strictEqual", "b", "null")
        p.i("sensor ty b @type")
        p.j("h0", "notEqual", "ty", pad)
        p.i("sensor cf b @config")
        p.j("h0", "strictEqual", "cf", "null")
        p.i("draw image hx hy cf tmp.sz 0")
        p.i("op add hx hx tmp.cell")
        p.j("h0", "lessThan", "hx", "tmp.ds")
        p.i("set hx 1")
        p.i("op sub hy hy tmp.cell")
        p.j("h0", "greaterThanEq", "hy", "0")
        p.l("h1")
        p.i("drawflush display1")

    # ---------------- 库存没变就整圈跳过 ----------------
    p.i("sensor tmp.tot core @totalItems")
    p.j("run", "notEqual", "tmp.tot", "last")
    p.j("main", "always")

    p.l("run")
    # ---------------- L0 数台 ----------------
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
    p.j("l0", "greaterThan", "npad", "0")

    # ---------------- 信息板：表头（只在真正重算时写） ----------------
    if a.board:
        p.i("printchar " + pad)
        p.i('print "[#ffd166]  RECEIVER[]  pads={0}\\n"')
        p.i("format npad")

    # ---------------- L1 找核心：缓存有效就跳过；否则借单位 ulocate，再退回链接扫描 ----------------
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

    # ---------------- pass1: mx = 单物品最大库存 ----------------
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

    # ---------------- pass2: sum = Σ (w*(mx-amt))^e ----------------
    p.i("set i 0")
    p.i("set sum 0")
    p.l("p2")
    p.i("lookup item it i")
    p.i("sensor amt core it")
    p.i("op sub d mx amt")
    p.i("sensor nm it @name")
    p.i("read w @this nm")
    p.i("op mul d d w")
    p.i("op pow d d @e")
    p.i("op add sum sum d")
    p.i("op add i i 1")
    p.j("p2", "lessThan", "i", "@itemCount")

    # ---------------- pass3: 累计切片，跨过一份 vol 就分一台 ----------------
    p.i("op div vol sum npad")
    p.j("p3", "greaterThan", "vol", "0")
    p.j("r1", "always")
    p.l("p3")
    p.i("set i 0")
    p.i("set pf 0")
    p.i("set p 0")
    p.l("p3l")
    p.i("set cnt 0")
    p.i("lookup item it i")
    p.i("sensor amt core it")
    p.i("op sub d mx amt")
    p.i("sensor nm it @name")
    p.i("read w @this nm")
    p.i("op mul d d w")
    p.i("op pow d d @e")
    p.j("p3n", "lessThanEq", "d", 0)
    p.i("op add pf pf d")
    p.j("p3n", "lessThan", "pf", "vol")
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
    p.i("op sub pf pf vol")
    p.j("p3a", "greaterThanEq", "pf", "vol")
    p.l("p3n")
    if a.board:
        p.j("p3q", "lessThanEq", "cnt", "0")
        p.i("printchar it")
        p.i('print "  x{0}\\n"')
        p.i("format cnt")
        p.l("p3q")
    p.i("op add i i 1")
    p.j("p3l", "lessThan", "i", "@itemCount")
    if a.board:
        p.i("printflush " + a.board_target)

    # 缓存本圈库存（必须重读：定位核心可能发生在本圈更早的时候）
    p.i("sensor last core @totalItems")
    if a.probe_links:
        for k in range(1, a.probe_links + 1):
            p.i("sensor pcfg%d sorter%d @config" % (k, k))
    p.j("main", "always")

    # 失败快重试：不动 last，下一圈立刻重算
    p.l("r1")
    if a.board:
        p.i("printflush " + a.board_target)
    p.i("op add next @time %d" % (retry * 1000))
    p.j("main", "always")
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--period", type=int, default=10000, help="重算周期 ms（库存不变会跳过）")
    ap.add_argument("--pad-block", default=PAD_DEFAULT)
    ap.add_argument("--core-cap", default="4000", help="链接扫描时用容量区分核心/容器")
    ap.add_argument("--hud", dest="hud", action="store_true", help="额外在 display1 上画图标板（默认关）")
    ap.add_argument("--no-board", dest="board", action="store_false", help="不生成 message1 文本信息板")
    ap.add_argument("--board-target", default="message1")
    ap.add_argument("--header", default="")
    ap.add_argument("--probe-links", type=int, default=0)
    ap.add_argument("-o", "--out", default="")
    ap.add_argument("--labeled", action="store_true")
    a = ap.parse_args()
    p = build(a)
    src = p.render(a.labeled)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(src)
        print("statements: %d" % p.count())
        print("wrote %s" % a.out)
    else:
        print(src)


if __name__ == "__main__":
    main()