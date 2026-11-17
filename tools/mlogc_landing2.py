#!/usr/bin/env python3
"""群控接收台 v2 生成器：运行时 getlink 统计可用台 + @itemCount 动态遍历 + 累计切片分配。

关键设计（见 docs/群控接收台-架构-v2.md）：
  L0 getlink 扫链，按 @type 与资格（水/空仓）数出 npad —— 不写死台数
  L1 借一只单位 ulocate 核心
  L2 pass1 求 mx，pass2 求 score=(w*(mx-amt))^e 并累加 sum
  L3 vol=sum/npad；物品外循环 + 台游标内循环（游标扫到 @links 为止，不当预算）
  L4 control config + control enabled
"""
import argparse
import sys

sys.stdout.reconfigure(encoding="utf-8")

# 抄自「调和着陆控制逻辑 v4.5」的权重表
WEIGHTS = [
    ("copper", "0.5"), ("lead", "0.5"), ("metaglass", "1"), ("graphite", "1"),
    ("sand", "0"), ("coal", "0"), ("titanium", "5"), ("thorium", "2"),
    ("scrap", "0"), ("silicon", "5"), ("plastanium", "0.8"), ("phase-fabric", "0.1"),
    ("surge-alloy", "1"), ("spore-pod", "0"), ("blast-compound", "0.01"),
    ("pyratite", "0.01"), ("beryllium", "0"), ("tungsten", "0"), ("oxide", "0"),
    ("carbide", "0"),
]


class Prog:
    def __init__(self):
        self.items = []          # ("i", text) | ("j", label, cond, a, b) | ("l", name)
        self.labels = {}
        self.stmts = 0

    def l(self, name):
        assert name not in self.labels, name
        self.labels[name] = self.stmts
        self.items.append(("l", name))

    def i(self, text):
        self.items.append(("i", text))
        self.stmts += 1

    def j(self, label, cond, a=None, b=None):
        self.items.append(("j", label, cond, a, b))
        self.stmts += 1

    def render(self, labeled):
        out = []
        for it in self.items:
            if it[0] == "l":
                if labeled:
                    out.append("%s:" % it[1])
            elif it[0] == "i":
                out.append(it[1])
            else:
                _, label, cond, a, b = it
                tgt = label if labeled else str(self.labels[label])
                if cond == "always":
                    out.append("jump %s always" % tgt)
                else:
                    out.append("jump %s %s %s %s" % (tgt, cond, a, b))
        return out


def build(a):
    p = Prog()
    retry = 2
    pad = a.pad_block
    period = a.period

    for line in a.header:
        p.i('print "%s"' % line)
    p.i("printflush message1")

    for name, w in WEIGHTS:
        p.i("set %s %s" % (name, w))

    p.i("set wt 0")
    p.i("set npad 0")
    p.i("set p 0")
    p.i("set pf 0")
    p.i("set vol 0")
    p.i("set i 0")
    p.i("set mx 0")
    p.i("set sum 0")
    p.i("set it null")
    p.i("set core null")
    p.i("set uiok 0")
    p.i("set b null")
    p.i("set cfg null")

    # ---- 主闸门：wait 让路（0 ipt），不依赖 @time ----
    p.l("main")
    p.i("wait wt")

    # ---- L0 统计可用台数 ----
    p.l("work")
    p.i("set wt %d" % (period // 1000))
    p.i("set npad 0")
    p.i("set p 0")
    p.l("c0")
    p.j("c1", "greaterThanEq", "p", "@links")
    p.i("getlink b p")
    p.j("c2", "strictEqual", "b", "null")
    p.i("sensor ty b @type")
    p.j("c2", "notEqual", "ty", pad)
    if a.only_empty:
        p.i("sensor tot b @totalItems")
        p.j("c2", "greaterThan", "tot", "0")
    if a.need_water:
        p.i("sensor eff b @efficiency")
        p.j("c2", "lessThan", "eff", "1")
    p.i("op add npad npad 1")
    p.l("c2")
    p.i("op add p p 1")
    p.j("c0", "always")
    p.l("c1")
    p.j("r0", "greaterThan", "npad", "0")

    # 没有可用台：短等再试
    p.i("set wt %d" % retry)
    p.j("done", "always")
    p.l("r0")

    # ---- L1 定位核心：核心有效就跳过；否则先借单位 ulocate，再退回链接扫描 ----
    p.l("l0")
    p.i("sensor cap core @itemCapacity")
    p.j("p1x", "notEqual", "cap", "null")
    p.i("set core null")
    p.l("l1")
    p.j("p1x", "notEqual", "core", "null")
    p.i("set ui uiok")
    p.l("fc")
    p.i("lookup unit uty ui")
    p.i("ubind uty")
    p.j("fok", "notEqual", "@unit", "null")
    p.i("op add ui ui 1")
    p.j("fc", "lessThan", "ui", "52")
    p.j("l1b", "always")
    p.l("fok")
    p.i("set uiok ui")
    p.i("ulocate building core false 0 cx cy f core")
    p.i("ucontrol unbind 0 0 0 0 0")
    p.j("p1x", "notEqual", "core", "null")
    # 退路：核心没链接上时才扫链找大容量建筑（core-shard 4000 起）
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
    p.j("p1x", "always")
    # 核心还是没有：本圈放弃
    p.l("p1x")
    p.j("r1", "notEqual", "core", "null")
    p.i("set wt %d" % retry)
    p.j("done", "always")
    p.l("r1")

    # ---- L2 pass1: mx ----
    p.i("set i 0")
    p.i("set mx 0")
    p.l("p1")
    p.i("lookup item it i")
    p.i("sensor amt core it")
    p.i("op max mx mx amt")
    p.i("op add i i 1")
    p.j("p1", "lessThan", "i", "@itemCount")
    p.i("op max mx mx 1")

    # ---- L2 pass2: score + sum ----
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

    # ---- L3 分配 ----
    p.i("op div vol sum npad")
    p.j("p3", "greaterThan", "vol", "0")
    p.i("set wt %d" % retry)
    p.j("done", "always")
    p.l("p3")
    p.i("set i 0")
    p.i("set pf 0")
    p.i("set p 0")
    p.l("p3l")
    p.i("lookup item it i")
    p.i("sensor amt core it")
    p.i("op sub d mx amt")
    p.i("sensor nm it @name")
    p.i("read w @this nm")
    p.i("op mul d d w")
    p.i("op pow d d @e")
    p.j("p3n", "lessThanEq", "d", "0")
    p.i("op add pf pf d")
    p.j("p3n", "lessThan", "pf", "vol")
    # 取下一台并下发，直到 pf 不够一份 vol
    p.l("p3a")
    p.j("p3n", "greaterThanEq", "p", "@links")
    p.i("getlink b p")
    p.i("op add p p 1")
    p.j("p3a", "strictEqual", "b", "null")
    p.i("sensor ty b @type")
    p.j("p3a", "notEqual", "ty", pad)
    if a.only_empty:
        p.i("sensor tot b @totalItems")
        p.j("p3a", "greaterThan", "tot", "0")
    if a.need_water:
        p.i("sensor eff b @efficiency")
        p.j("p3a", "lessThan", "eff", "1")
    p.i("control config b it")
    p.i("control enabled b true")
    p.i("op sub pf pf vol")
    p.j("p3a", "greaterThanEq", "pf", "vol")
    p.l("p3n")
    p.i("op add i i 1")
    p.j("p3l", "lessThan", "i", "@itemCount")

    # ---- 收尾 ----
    p.l("done")
    if a.verbose:
        p.i('print "npad="')
        p.i("print npad")
        p.i('print " core="')
        p.i("print core")
        p.i('print " sum="')
        p.i("print sum")
        p.i('print " vol="')
        p.i("print vol")
        p.i('print "\\n"')
        p.i("printflush message1")
    if a.probe_core:
        p.i("sensor pcore container1 @itemCapacity")
    for k in range(1, a.probe_pads + 1):
        p.i("sensor ppad%d pad%d @efficiency" % (k, k))
    for k in range(1, a.probe_links + 1):
        p.i("sensor pcfg%d sorter%d @config" % (k, k))
    p.j("main", "always")
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--period", type=int, default=10000, help="重算周期 ms")
    ap.add_argument("--pad-block", default="@landing-pad", help="台的方块常量（模拟器测试用 @sorter）")
    ap.add_argument("--no-elig", dest="elig", action="store_false", help="（已废弃）默认不再做资格过滤；保留参数仅为兼容")
    ap.add_argument("--only-empty", dest="only_empty", action="store_true", help="只统计空仓的台（满仓的台不参与分配）")
    ap.add_argument("--need-water", dest="need_water", action="store_true", help="额外要求 @efficiency>=1（即水满 100）；默认不要求，没水的台也照样配置")
    ap.add_argument("--header", default=None, help="print 头，用 | 分隔多行")
    ap.add_argument("--core-cap", default="4000", help="链接扫描认定核心的 @itemCapacity 下限")
    ap.add_argument("--verbose", action="store_true", help="每圈打印 npad/core/sum/vol 到 message1")
    ap.add_argument("--probe-pads", type=int, default=0, help="模拟器测试：造 padK 着陆台链接")
    ap.add_argument("--probe-core", action="store_true", help="模拟器测试：造一个 container1 链接")
    ap.add_argument("--probe-links", type=int, default=0, help="模拟器测试：输出 N 个 sorterK 的 @config 探针")
    ap.add_argument("-o", "--out", default="out/landing2.labels.mlog")
    a = ap.parse_args()
    if a.header:
        a.header = a.header.split("|")
    else:
        a.header = [
            "[#ffd166]群控接收台 · 缺口加权调度 v2[]",
            "By DeepSeek  ·  权重表抄 [blue]Il[#7d9396]ia[#716b5b]ry[#654321]艾铭[]",
            "台数运行时 getlink 统计；物品 @itemCount 动态；每 %d s 重算" % (a.period // 1000),
        ]
    p = build(a)
    open(a.out, "w", encoding="utf-8", newline="\n").write("\n".join(p.render(True)) + "\n")
    print("statements: %d" % p.stmts)
    print("wrote %s" % a.out)


if __name__ == "__main__":
    main()