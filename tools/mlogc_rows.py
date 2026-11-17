# -*- coding: utf-8 -*-
"""行表多控（building-variable row table）。

表 = 处理器自己的变量空间（@this），行键 = 单位类型名（lookup unit i -> @name），
行值 = 一只单位对象。遍历靠 lookup + @name + read，键全部运行时求值，代码里只有一份循环。
"""
import sys, argparse, io

sys.stdout.reconfigure(encoding="utf-8")


class Prog:
    def __init__(self):
        self.stmts = []
        self.labels = {}

    def label(self, name):
        assert name not in self.labels, name
        self.labels[name] = self.count()
        self.stmts.append(("l", name))

    def i(self, text):
        self.stmts.append(("i", text))

    def j(self, label, cond, a="0", b="0"):
        self.stmts.append(("j", label, cond, a, b))

    def count(self):
        return sum(1 for s in self.stmts if s[0] != "l")

    def render(self, labeled):
        out = []
        for st in self.stmts:
            if st[0] == "l":
                if labeled:
                    out.append(st[1] + ":")
                continue
            if st[0] == "i":
                out.append(st[1])
            else:
                tgt = st[1] if labeled else str(self.labels[st[1]])
                out.append("jump %s always" % tgt if st[2] == "always"
                           else "jump %s %s %s %s" % (tgt, st[2], st[3], st[4]))
        return "\n".join(out) + "\n"


def build(args):
    rows = [n.strip() for n in io.open(args.names, encoding="utf-8").read().split("\n") if n.strip()]
    rows = rows[:args.rows]
    p = Prog()

    p.label("init")
    p.i("set cfg.next 0")
    p.i("set cfg.item null")
    p.i("set tmp.lnk null")
    p.i("set sx @thisx")
    p.i("set sy @thisy")
    p.i("set lx @thisx")
    p.i("set ly @thisy")

    p.label("hot")
    p.i("set tmp.i 0")
    p.label("row")
    p.i("lookup unit tmp.ty tmp.i")                 # 第 i 个类型
    p.i("sensor tmp.nm tmp.ty @name")               # 行键（运行时字符串）
    p.i("read u @this tmp.nm")                      # 行值（单位对象）
    p.j("next", "strictEqual", "u", "null")
    p.i("ubind u")
    p.j("next", "strictEqual", "@unit", "null")
    p.i("sensor tmp.f @unit @firstItem")
    p.j("drop", "notEqual", "tmp.f", "null")
    p.i("ucontrol approach sx sy %s 0 0" % args.approach)
    p.i("ucontrol itemTake st cfg.item 999 0 0")
    p.j("next", "always")
    p.label("drop")
    p.j("junk", "notEqual", "tmp.f", "cfg.item")
    p.i("ucontrol approach lx ly %s 0 0" % args.approach)
    p.i("ucontrol itemDrop tmp.lnk 999 0 0")
    p.j("next", "always")
    p.label("junk")
    p.i("ucontrol approach sx sy %s 0 0" % args.approach)
    p.i("ucontrol itemDrop st 999 0 0")
    p.label("next")
    p.i("op add tmp.i tmp.i 1")
    p.j("row", "lessThan", "tmp.i", str(len(rows)))
    p.j("hot", "lessThan", "@time", "cfg.next")

    p.label("refill")
    p.i("op add cfg.next @time %d" % args.refill)
    p.i("getlink tmp.lnk %d" % args.link)
    p.i("sensor lx tmp.lnk @x")
    p.i("sensor ly tmp.lnk @y")
    p.i("sensor tmp.ic sorter1 @config")
    p.j("ic1", "strictEqual", "tmp.ic", "null")
    p.i("set cfg.item tmp.ic")
    p.label("ic1")
    p.i("ubind @%s" % args.type)                    # ulocate 是单位指令，@unit 必须有效
    p.j("ic2", "strictEqual", "@unit", "null")
    p.i("ulocate building core 0 0 sx sy tmp.g st")
    p.label("ic2")
    p.i("set tmp.i 0")
    p.i("set tmp.t 0")
    p.label("fill")
    p.i("lookup unit tmp.ty tmp.i")
    p.i("sensor tmp.nm tmp.ty @name")
    p.i("read u @this tmp.nm")
    p.j("fnext", "notEqual", "u", "null")
    p.i("ubind @%s" % args.type)                    # 按类型环形取下一只
    p.j("fnext", "strictEqual", "@unit", "null")
    p.i("sensor tmp.c @unit @controller")
    p.j("fnext", "notEqual", "tmp.c", "@unit")      # 只收自由单位
    p.i("write @unit @this tmp.nm")                 # 登记到空行
    p.i("ucontrol payDrop")                         # 打归属戳，下轮 @controller = 本处理器
    p.i("op add tmp.t tmp.t 1")
    p.j("rfend", "greaterThanEq", "tmp.t", str(args.cap))
    p.label("fnext")
    p.i("op add tmp.i tmp.i 1")
    p.j("fill", "lessThan", "tmp.i", str(len(rows)))
    p.label("rfend")
    p.j("hot", "always")
    if getattr(args, "decl_end", False):
        # 行键声明：draw 的每个参数都会被 LParser 建成变量（可 write/read），
        # 但这些语句本身不需要执行。放在上面那条无条件 jump 之后 = 不可达、
        # 零运行时成本，check 会报 unreachable（预期，忽略）。
        for k in range(0, len(rows), 6):
            p.i("draw triangle " + " ".join(rows[k:k + 6]))
        p.j("hot", "always")        # 末尾留一条 jump，给签名槽用
    return p, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--names", default="out/unitnames.txt")
    ap.add_argument("--rows", type=int, default=50)
    ap.add_argument("--header", action="store_true")
    ap.add_argument("--emit-decl", default="", help="把行键声明写进单独文件（draw 一行 6 个）")
    ap.add_argument("--decl-end", action="store_true", help="行键用程序末尾的 draw 语句声明（不可达，零运行时成本）")
    ap.add_argument("--type", default="poly")
    ap.add_argument("--link", type=int, default=1)
    ap.add_argument("--cap", type=int, default=6)
    ap.add_argument("--refill", type=int, default=2000)
    ap.add_argument("--approach", default="6.5")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()
    p, rows = build(args)
    if args.header:
        head = [
            'print "[#ffd166]行表多控[] v2 · 建筑变量存单位"',
            'print "By DeepSeek"',
            'print "表 = 处理器变量空间(@this)：行键 = 单位类型名，行值 = 一只单位对象"',
            'print "遍历 lookup unit i -> sensor @name -> read u @this 名 -> ubind u"',
            'print "空行 6 条(3 tick)，满行 17 条(8.5 tick)；50 行满扫约 2.9 s"',
            'print "行键在末尾 draw 声明（不可达，零开销）：@this 只写已存在的变量"',
        ]
        p.stmts = [("i", h) for h in head] + p.stmts
        p.labels = {k: v + len(head) for k, v in p.labels.items()}
    open(args.out, "w", encoding="utf-8").write(p.render(args.out.endswith(".labels.mlog")))
    if args.emit_decl:
        decl = []
        for k in range(0, len(rows), 6):
            decl.append("draw triangle " + " ".join(rows[k:k + 6]))
        io.open(args.emit_decl, "w", encoding="utf-8").write("\n".join(decl) + "\n")
        print("decl -> %s (%d lines)" % (args.emit_decl, len(decl)))
    print("wrote %s  hot=%d total=%d rows=%d" % (
        args.out, p.labels["refill"] - p.labels["hot"], p.count(),
        len([1 for l in io.open(args.names, encoding="utf-8").read().split("\n") if l.strip()])))


if __name__ == "__main__":
    main()
