# -*- coding: utf-8 -*-
"""类型键表（type-keyed table）原型生成器。

表行 = 单位类型，键 = 该类型 @type 的 @name（运行时字符串，值即变量名）；
值 = 该类型最近被服务的那只单位。
同类型多只靠 ubind <类型> 的环形游标轮流服务（LExecutor.java:190-195），所以类型行数决定代码量，与每类型单位数无关。
"""
import sys, argparse

sys.stdout.reconfigure(encoding="utf-8")


class Prog:
    def __init__(self):
        self.stmts = []
        self.labels = {}

    def label(self, name):
        assert name not in self.labels, name
        self.labels[name] = sum(1 for s in self.stmts if s[0] != "l")
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
                if st[2] == "always":
                    out.append("jump %s always" % tgt)
                else:
                    out.append("jump %s %s %s %s" % (tgt, st[2], st[3], st[4]))
        return "\n".join(out) + "\n"


def build(args):
    p = Prog()
    types = [t.strip() for t in args.types.split(",") if t.strip()]

    p.label("init")
    for t in types:
        p.i("set %s null" % t)                              # 声明类型槽（@this 只写已存在的变量）
    p.i("set cfg.next 0")
    p.i("set sx @thisx")
    p.i("set sy @thisy")
    p.i("set lx @thisx")
    p.i("set ly @thisy")
    p.i("set cfg.item null")
    p.i("set tmp.lnk null")
    p.label("hot")

    for t in types:
        up = t.upper()
        p.i("ubind @%s" % t)
        p.j("d%s" % up, "strictEqual", "@unit", "null")
        p.i("sensor tmp.ty @unit @type")
        p.i("sensor tmp.nm tmp.ty @name")
        p.i("write @unit @this tmp.nm")                     # 表行：该类型最近服务的单位
        p.i("sensor tmp.f @unit @firstItem")
        p.j("t%s" % up, "notEqual", "tmp.f", "null")        # 有货 → 投递
        p.i("ucontrol approach sx sy %s 0 0" % args.approach)
        p.i("ucontrol itemTake st cfg.item 999 0 0")
        p.j("n%s" % up, "always")
        p.label("t%s" % up)
        p.j("j%s" % up, "notEqual", "tmp.f", "cfg.item")
        p.i("ucontrol approach lx ly %s 0 0" % args.approach)
        p.i("ucontrol itemDrop tmp.lnk 999 0 0")
        p.j("n%s" % up, "always")
        p.label("j%s" % up)
        p.i("ucontrol approach sx sy %s 0 0" % args.approach)
        p.i("ucontrol itemDrop st 999 0 0")
        p.label("n%s" % up)
        p.label("d%s" % up)

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
    p.i("ulocate building core 0 0 sx sy tmp.g st")
    p.j("hot", "always")
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--types", default="poly")
    ap.add_argument("--link", type=int, default=1)
    ap.add_argument("--refill", type=int, default=2000)
    ap.add_argument("--approach", default="6.5")
    ap.add_argument("--header", action="store_true")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args()
    p = build(args)
    if args.header:
        head = [
            'print "[#ffd166]类型键表多控[] v1 · 每类型一行"',
            'print "By DeepSeek"',
            'print "表行=单位类型，键=@type 的 @name（运行时字符串），值=该类型最近服务的单位"',
            'print "同类型多只靠 ubind <类型> 环形游标轮流，代码量只随类型数增长，不随单位数"',
            'print "槽名用 set 声明，@this 只写已存在的变量（LogicBlock.java:644-650）"',
        ]
        p.stmts = [("i", h) for h in head] + p.stmts
        p.labels = {k: v + len(head) for k, v in p.labels.items()}
    labeled = args.out.endswith(".labels.mlog")
    open(args.out, "w", encoding="utf-8").write(p.render(labeled))
    print("wrote %s  (hot %d, total %d, types %s)" % (
        args.out, p.labels["refill"] - p.labels["hot"], p.count(), args.types))


if __name__ == "__main__":
    main()
