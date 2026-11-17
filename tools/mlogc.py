#!/usr/bin/env python3
"""mlogc.py - 单位多控逻辑编译器（极限响应架构）

把「N 个槽位」的长度参数从手写展开变成编译期生成：改一个数字就得到
N 条槽位的直线代码，没有空槽、没有运行时 N 判断。

架构（已实测）：
  * 直线槽位：每单位 k 条 ucontrol，micro 2 ipt => 1 单位 = 1 tick
  * 时间门控补员：循环尾一条 jump 回跳，稳态 0 额外指令
  * @controller 三态：==@this 归我 / null 死或空 / 其它 被抢（夺回）
  * 补员扫描只在 refill 段，热循环 0 次 ulocate / 0 次 getlink

三种架构（--live / --twospeed 与默认）：
  默认   ：入口 op @counter 直接落到第 N 槽，一圈成本 = N * stride（与存活数无关）
  --live ：入口用 L（存活槽数），死一个就 L-=1，一圈成本 = L * stride
  --twospeed：快环 2 条/单位保航向 + 慢环每圈只完整处理 1 个单位
"""
import argparse, subprocess, sys, os, re

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


class Prog:
    def __init__(self):
        self.items = []      # ('i', text) | ('j', label, cond, a, b) | ('l', name)
        self.labels = {}
        self.stmts = 0

    def label(self, name):
        if name in self.labels:
            raise SystemExit("duplicate label: %s" % name)
        self.labels[name] = self.stmts
        self.items.append(('l', name))

    def i(self, *tokens):
        self.items.append(('i', " ".join(str(t) for t in tokens)))
        self.stmts += 1

    def j(self, target, cond, a="0", b="0"):
        self.items.append(('j', target, cond, str(a), str(b)))
        self.stmts += 1

    def render(self, labeled=True):
        out = []
        for it in self.items:
            if it[0] == 'l':
                out.append(it[1] + ":")
            elif it[0] == 'i':
                out.append(it[1])
            else:
                _, tgt, cond, a, b = it
                # always 省略多余的两个 0：签名工具只认「jump <n> always」两段式，
                # 多带 "0 0" 它就退化成末尾追加一条不可达语句（check 报 1 warn）
                tail = "" if cond == "always" else " %s %s" % (a, b)
                if labeled:
                    out.append("jump %s %s%s" % (tgt, cond, tail))
                else:
                    out.append("jump %d %s%s" % (self.labels[tgt], cond, tail))
        return out

    def count(self):
        return self.stmts


# 慢环单位块的长度（--twospeed）。改这里的语句数必须同步改 STRIDE_SLOW。
STRIDE_SLOW = 19


def build(args):
    p = Prog()
    n = args.slots
    last = n
    live = args.live
    two = args.twospeed
    dbg = getattr(args, "dbg", False)
    # 助推：--boost 显式开，或挖矿模式默认开（--no-boost 可关）。
    boost = bool(getattr(args, "boost", False)) or (
        args.mode == "mine" and not getattr(args, "no_boost", False))
    # 短路径：itemTake/itemDrop 之后立刻发一条 move 把航向改过来，
    # 否则单位要等一整圈（N=8 约 1 s）才等到下一条 move。
    # 短路径只做在 stateless 槽里（老的有状态槽保持原样，省得改两处 stride）。
    shortpath = bool(getattr(args, "shortpath", True)) and not two and args.stateless

    def emit_item(tag=""):
        """写 cfg.item：--item 写死，否则读物品选择器（sorter）的 @config。

        单独成函数是因为它的位置随 mode 变：haul 放在 loc 段之后（兜底要读核心），
        mine 必须放在 init 里 —— 挖矿版没有 loc 段，补员段的每次出口都直接 jump hot，
        排在末尾的这段代码永远走不到（实测 cfg.item 恒 null，全队停在 gate）。
        """
        if args.item:
            p.i("set cfg.item %s" % args.item)
            return
        src = str(getattr(args, "item_src", "") or args.link)
        if src == str(args.link):
            p.i("sensor tmp.ic tmp.lnk @config")
        else:
            if re.fullmatch(r"\d+", src):
                p.i("getlink tmp.sel %s" % src)
                p.i("sensor tmp.ic tmp.sel @config")
            else:
                p.i("sensor tmp.ic %s @config" % src)
        if getattr(args, "item_fallback", True):
            p.j("ic1" + tag, "notEqual", "tmp.ic", "null")
            p.i("sensor tmp.ic cbc @firstItem")
            p.label("ic1" + tag)
        p.j("ic2" + tag, "strictEqual", "tmp.ic", "null")
        p.i("set cfg.item tmp.ic")
        p.label("ic2" + tag)

    # ---------- init ----------
    p.label("init")
    ndef = args.n or n
    # 槽位是编译期固定的（直线代码），N 只决定「实际启用前几槽」。
    p.i("set N", ndef)
    if live:
        # L = 实际占用的槽数（表长）。N 仍是硬上限，L 只会因为死人而缩小。
        # 起手 L 先取 N（空表也无所谓）：L=0 时热入口算到 base+3+n*stride，
        # 越过 hot 段落到 gate 上，被「没到补员时间」跳回 hot —— 空转死循环。
        # 之后每次补员由收缩段（shN..sh1）把它压到「最高那个活槽」。
        p.i("set L 1")
    # 单位类型提到开头配置区：整个程序里兵种字面量只出现这一处，人改兵种只改这一行。
    # 必须写 sensor ... @type 拿「类型」而不是 set cfg.utype @unit ——
    # @unit 是单位对象：ubind 拿到对象会走 LExecutor.java:200 的对象分支，
    # 永远只绑那一个单位，而不是「按类型扫全队」。
    p.label("boot")
    p.i("ubind", args.type)
    p.i("sensor cfg.utype @unit @type")
    p.j("boot", "strictEqual", "cfg.utype", "null")
    # 补员突发共享一个「绑定次数」预算：每补一个槽至少 1 次 ubind，
    # 扫描时还会反复绑到「已经被我们占着」的单位，所以要留出余量。
    # 8 槽全空时 12 次根本不够（实测只补到 7/8），改成运行时 2N+4；
    # --cap 显式给了才用字面量（调试/极端场景）。
    if getattr(args, "cap", None):
        p.i("set cfg.cap", args.cap)
    else:
        p.i("op mul cfg.cap N 2")
        p.i("op add cfg.cap cfg.cap 4")
    p.i("set cfg.next", 0)
    p.i("set cfg.nloc", 0)
    # 1 = 还没卸过货，第一次进 loc 段就直接定位
    if getattr(args, "needloc", False):
        p.i("set tmp.needloc 1")
    p.i("set sx @thisx")
    p.i("set sy @thisy")
    p.i("set lx @thisx")
    p.i("set ly @thisy")
    if two:
        # 快环用缓存坐标，必须先给个安全值，否则首圈单位会飞向 (0,0)。
        for k in range(1, n + 1):
            p.i("set dx%d sx" % k)
            p.i("set dy%d sy" % k)
    if args.mode == "mine":
        # 物品必须在 init 里就读出来：挖矿版的补员/体检段出口全都 jump hot，
        # 排在末尾的物品读取块永远走不到（cfg.item 恒 null -> 全队停在 gate）。
        emit_item()
        # 矿区缓存（全队共享，语义等同搬运版的 sx/sy）+ 重定位触发位。
        # ox=null 是「还没定位过」的哨兵：槽里靠它挡掉「朝处理器格飞」。
        p.i("set ox null")
        p.i("set oy null")
        p.i("set cfg.ore null")

    # ---------- 每槽指令数（stride）----------
    if two:
        stride = STRIDE_SLOW + (3 if args.graze != "none" else 0)
    elif args.mode == "mine":
        # 挖矿槽固定 18 条（下面有断言兜底）。
        # 不开顺路取货（挖矿没有「货源建筑」）；不写 needloc（矿区只由时间闸门重定位）。
        stride = 18
    elif args.stateless:
        # 状态外化：不看 sK 变量，直接用 @firstItem 判断「空手/带货/杂物」。
        # 顺路取货 +3 条（定位最近容器 / 投递点就跳过 / itemTake）
        # 投递腿：默认「卸空才掉头」多 2 条（sensor + 判定）；--return-anyway 回 v22 行为。
        gate = 0 if getattr(args, "return_anyway", False) else 2
        # 短路径 2 条（sensor 复读 + 空手跳走）——「拿到货」那条不再跳 uKe，
        # 直接落进投递腿（approach lx ly 本来就在投递腿里），省掉原来那条 jump uKe always。
        stride = 12 + (3 if args.graze != "none" else 0) + (2 if shortpath else 0) + gate
    else:
        # 有状态槽 16 条；顺路取货在热路径里是 3 条（ulocate / 跳过投递点 / itemTake），
        # 不是 2 条 —— 写成 2 会让 dispatch 入口错位一格，落在槽中间（v17 前的老账）。
        stride = 3 if args.mode == "hold" else (16 + (0 if args.graze == "none" else 3))
    if args.mode == "haul" and getattr(args, "needloc", False):
        # 卸空标记 set tmp.needloc 1（投递腿里那条「刚卸空」），每槽 1 条
        stride += 1
    if args.probe:
        stride += 1

    def slot(k):
        u, s = "u%d" % k, "s%d" % k
        p.label("u%d" % k)
        if args.probe:
            # 探针：本槽真的被执行到就置位（验证 dispatch 入口落点）。
            p.i("set dbg.s%d 1" % k)
        if args.guard:
            p.j("u%de" % k, "greaterThan", k, "N")
        p.i("ubind", u)
        if args.mode == "mine":
            # 挖矿槽（18 条）。状态仍然只由「手里有什么」推导，没有 sK 记账。
            #   空手                -> 挖矿腿
            #   手上有货但不是目标矿 -> itemDrop @air 清空，顺手落入挖矿腿
            #   手上有目标矿但没满   -> 继续挖（mineTile 会一直挂着）
            #   满了                 -> 去 getlink 1 投递，卸空立刻回矿区
            #
            # 矿区坐标 ox/oy 是**全队共享**的缓存，和搬运版的 sx/sy 一样：
            # 只在「矿物倒进容器那一瞬间」由 loc 段重定位（set tmp.needloc 1），
            # 每槽自己不调 ulocate —— 否则每个单位每圈都重新找一个矿点，
            # N=8 时一圈多 8 次 ulocate + 8 次象限桶查询，而且矿点会随单位位置漂。
            p.i("sensor tmp.f @unit @firstItem")
            p.j("u%dm" % k, "strictEqual", "tmp.f", "null")
            p.j("u%dj" % k, "notEqual", "tmp.f", "cfg.item")
            p.i("sensor tmp.n @unit @totalItems")
            p.i("sensor tmp.c @unit @itemCapacity")
            p.j("u%dm" % k, "lessThan", "tmp.n", "tmp.c")
            # 没有投递目标时别飞向处理器格（lx/ly 还停在 init 的 @thisx/@thisy）
            p.j("u%dm" % k, "strictEqual", "tmp.lnk", "null")
            p.i("ucontrol approach lx ly %s 0 0" % args.approach)
            p.i("ucontrol itemDrop tmp.lnk 999 0 0 0")
            p.i("sensor tmp.f @unit @firstItem")
            p.j("u%dm" % k, "strictEqual", "tmp.f", "null")
            p.j("u%de" % k, "always")
            p.label("u%dj" % k)
            # 杂货直接倒掉：itemDrop @air 走 unit.clearItem()，不受 transferDelay 限制
            # （LExecutor.java:511-519），比找核心倒一趟快得多。
            p.i("ucontrol itemDrop @air 999 0 0 0")
            p.label("u%dm" % k)
            # 还没定位到矿点（ox 恒 null）就什么都别做：否则单位会朝处理器格飞
            # （init 里 sx/sy/lx/ly 都是 @thisx/@thisy）。loc 段一跑完这里就通了。
            p.j("u%de" % k, "strictEqual", "ox", "null")
            # ox/oy 是 ulocate ore 的 outX/outY（格坐标），可以直接喂 approach / mine。
            p.i("ucontrol approach ox oy %s 0 0" % args.approach)
            p.i("ucontrol mine ox oy 0 0 0")
            p.j("u%de" % k, "always")
            p.label("u%de" % k)
            return
        if args.stateless:
            # 空手 -> 去货源取；带货 -> 去投递点放；带杂物 -> 飞回收点倒掉。
            # 没有第二个 move、没有 set sK，状态就是「此刻手里有什么」。
            p.i("sensor tmp.f @unit @firstItem")
            p.j("u%dd" % k, "notEqual", "tmp.f", "null")
            p.i("ucontrol approach sx sy %s 0 0" % args.approach)
            if args.graze != "none":
                # 顺路取货必须放在热循环里：ulocate 给的是「离当前绑定单位最近的容器」，
                # 在补员段做一次全局定位，拿到的容器跟其它单位的航线毫无关系，
                # itemTake 的 45 tile 距离校验永远过不去（v4 的实测结论）。
                p.i("ulocate building %s 0 0 vx vy tmp.g2 vault" % args.graze)
                p.j("u%dk" % k, "equal", "vault", "tmp.lnk")
                p.i("ucontrol itemTake vault cfg.item 999 0 0")
                p.label("u%dk" % k)
            p.i("ucontrol itemTake st cfg.item 999 0 0")
            # 短路径：拿到了就当场把航向改成投递点。原来这里直接跳下一槽，
            # 单位要等整整一圈（N=8 时约 1 s）才有下一条 move，白等一圈。
            # 代价是「核心当时是空的」时这一趟会空跑到投递点，
            # 下一圈 sensor 看到空手会自己飞回来（--no-shortpath 可关）。
            if shortpath:
                # 短路径只在「真的拿到货」时才拐弯。无条件拐弯会让单位在货源和
                # 投递点之间来回摆（取货失败也掉头），两头都到不了 —— 实测
                # 22 格远的投递点：235 次 approach sx / 234 次 approach lx、
                # 一次 itemTake 都没成功。
                # 拿到货就不跳走，直接落进下面的 uKd（投递腿首条会重新判
                # 「手里是不是 cfg.item」）—— 省掉一条 jump uKe always。
                p.i("sensor tmp.f @unit @firstItem")
                p.j("u%de" % k, "strictEqual", "tmp.f", "null")
            else:
                p.j("u%de" % k, "always")
            p.label("u%dd" % k)
            p.j("u%dj" % k, "notEqual", "tmp.f", "cfg.item")
            p.i("ucontrol approach lx ly %s 0 0" % args.approach)
            p.i("ucontrol itemDrop tmp.lnk 999 0 0 0")
            if getattr(args, "return_anyway", False):
                if getattr(args, "needloc", False):
                    p.i("set tmp.needloc 1")
                if shortpath:
                    p.i("ucontrol approach sx sy %s 0 0" % args.approach)
            else:
                # 掉头必须看投递结果：itemDrop 只是「尝试」，可能因为
                #   · 距离不够（45 + size*4/2 wu，LExecutor.java:523）
                #   · 同单位 90 tick 冷却未到（LogicAI.transferDelay）
                # 而没生效。无条件接一条 approach sx sy 会在同一趟里覆盖上面那条
                # approach lx ly，单位永远到不了投递点，只在货源附近打转。
                p.i("sensor tmp.f @unit @firstItem")
                p.j("u%de" % k, "notEqual", "tmp.f", "null")
                if getattr(args, "needloc", False):
                    p.i("set tmp.needloc 1")
                if shortpath:
                    p.i("ucontrol approach sx sy %s 0 0" % args.approach)
            p.j("u%de" % k, "always")
            p.label("u%dj" % k)
            p.i("ucontrol approach cbx cby %s 0 0" % args.approach)
            p.i("ucontrol itemDrop cbc 999 0 0 0")
            p.label("u%de" % k)
            return
        if args.mode == "hold":
            p.i("ucontrol move @thisx @thisy 0 0 0")
            p.i("jump u%de always" % k)
        else:
            p.j("u%de" % k, "strictEqual", "st", "null")
            p.j("u%dd" % k, "greaterThan", s, 0)
            p.i("ucontrol approach sx sy %s 0 0" % args.approach)
            if args.graze != "none":
                p.i("ulocate building %s 0 0 vx vy tmp.g2 vault" % args.graze)
                p.j("u%dk" % k, "equal", "vault", "tmp.lnk")
                p.i("ucontrol itemTake vault cfg.item 999 0 0")
                p.label("u%dk" % k)
            p.i("ucontrol itemTake st cfg.item 999 0 0")
            p.i("sensor tmp.f @unit @firstItem")
            p.j("u%dt" % k, "equal", "tmp.f", "cfg.item")
            p.i("ucontrol itemDrop cbc 999 0 0 0")
            p.j("u%de" % k, "always")
            p.label("u%dt" % k)
            p.i("set", s, 1)
            p.label("u%dd" % k)
            p.i("ucontrol approach lx ly %s 0 0" % args.approach)
            p.i("ucontrol itemDrop tmp.lnk 999 0 0 0")
            p.i("sensor tmp.f @unit @firstItem")
            p.j("u%de" % k, "notEqual", "tmp.f", "null")
            # 走到这里 = 刚卸空（投递前手里有货、投递后 @firstItem 变 null）。
            # 这就是重定位核心的唯一时机：卸空的那一刻说明「这一趟结算完毕」，
            # 此刻重新认最近的核心才有意义（用「目标装满」当条件会在 sorter 这类
            # 没有货舱的建筑上误判，而且装满并不代表该换点）。
            if getattr(args, "needloc", False):
                p.i("set tmp.needloc 1")
            p.i("set", s, 0)
            p.i("ucontrol approach sx sy %s 0 0" % args.approach)
        p.label("u%de" % k)

    def slow(k):
        """--twospeed 的慢环块：完整判定一次，把目标坐标写进 dxK/dyK 给快环用。

        每块必须正好 STRIDE_SLOW 条（下面有断言），否则 @counter 算出的入口会错位。
        三个分支都直接 jump gate，不要再经过中间标签——那会多一次无谓的跳转。
        """
        u = "u%d" % k
        p.label("d%d" % k)
        p.i("ubind", u)
        p.i("sensor tmp.f @unit @firstItem")
        p.j("d%dd" % k, "notEqual", "tmp.f", "null")
        p.i("set dx%d sx" % k)
        p.i("set dy%d sy" % k)
        p.i("ucontrol approach sx sy %s 0 0" % args.approach)
        if args.graze != "none":
            p.i("ulocate building %s 0 0 vx vy tmp.g2 vault" % args.graze)
            p.j("d%dk" % k, "equal", "vault", "tmp.lnk")
            p.i("ucontrol itemTake vault cfg.item 999 0 0")
            p.label("d%dk" % k)
        p.i("ucontrol itemTake st cfg.item 999 0 0")
        p.j("gate", "always")
        p.label("d%dd" % k)
        p.j("d%dj" % k, "notEqual", "tmp.f", "cfg.item")
        p.i("set dx%d lx" % k)
        p.i("set dy%d ly" % k)
        p.i("ucontrol approach lx ly %s 0 0" % args.approach)
        p.i("ucontrol itemDrop tmp.lnk 999 0 0 0")
        p.j("gate", "always")
        p.label("d%dj" % k)
        p.i("set dx%d cbx" % k)
        p.i("set dy%d cby" % k)
        p.i("ucontrol approach cbx cby %s 0 0" % args.approach)
        p.i("ucontrol itemDrop cbc 999 0 0 0")
        p.j("gate", "always")

    # ---------- hot ----------
    if args.dispatch or two:
        # N 夹紧：N=0 会让算出的入口落到槽位区之外
        p.i("op min N N %d" % n)
        p.i("op max N N 1")
        # 夹紧之后才把 L 放到 N：不然 L>N 时热入口会落在 hot 段之前。
        if live:
            p.i("set L N")

    if two:
        # 架构 C：快环 2 条/单位（只保航向），慢环每圈轮转 1 个单位做完整判定。
        p.label("hot")
        for k in range(1, n + 1):
            p.i("ubind u%d" % k)
            p.i("ucontrol move dx%d dy%d %s 0 0" % (k, k, args.arrive))
        p.i("op add tmp.r tmp.r 1")
        p.j("rok", "lessThanEq", "tmp.r", "N")
        p.i("set tmp.r 1")
        p.label("rok")
        # 慢环入口：@counter 直接落到第 r 个块（块反序排：n 在前、1 在末尾）
        p.i("set tmp.cb @counter")
        p.i("op add tmp.offc tmp.cb %d" % (3 + n * stride))
        p.i("op mul tmp.p tmp.r -%d" % stride)
        p.i("op add @counter tmp.offc tmp.p")
        for k in range(n, 0, -1):
            slow(k)
        d0 = p.labels["d%d" % n]
        if p.count() - d0 != n * stride:
            raise SystemExit("twospeed stride mismatch: expect %d, got %d"
                             % (n * stride, p.count() - d0))
        p.label("gate")
        p.j("hot", "lessThan", "@time", "cfg.next")
        hotn = 2 * n + 7 + stride
    else:
        # 相对派发：不预先算「槽表起点 + 总条数」这种绝对地址，而是把槽表末尾的
        # @counter 自己当基准。依据 LExecutor.java:119 —— counter 在 run() 之前自增，
        # 所以执行第 i 条时 @counter == i+1，表尾三条（时间闸门 / 物品空守卫 / 加法）
        # 里的 @counter 恒等于「表尾 + 3」，与前面塞了多少 print 无关。
        #   入口 = @counter - (N*stride + 3)
        # N*stride 一次性在 init 算好（2 条），每圈只剩 1 条 op add；
        # 绝对寻址是每圈 2 条 + init 2 条，而且依赖 tmp.base/tmp.off 两个变量。
        # 槽位仍反序排（槽 n 在前、槽 1 在末尾），从槽 N 往下自然贯穿到槽 1，
        # 用不到的槽根本不会被走到 —— 0 条守卫。
        rel = args.dispatch and not live
        if rel:
            # 注意变量名：体检段（chk）也用 tmp.p 算它自己的入口位移，
            # 补员一次就把 tmp.p 写成 -2N；热派发再用 tmp.p 就会落到槽 604 那种地方
            # （实测 N=8 时 -16 让入口歪到一半处，dbg.sK 一个都没置位）。
            # 所以热派发用专用变量 tmp.hp，只在 init 算一次。
            p.i("op mul tmp.hp N -%d" % stride)
            p.i("op sub tmp.hp tmp.hp 3")
            # 表在物理上位于 hot 之前，入口必须先跳到表尾去算一次位移。
            p.j("hot", "always")
            tbl0 = p.count()
            for k in range(n, 0, -1):
                slot(k)
            if p.count() - tbl0 != n * stride:
                raise SystemExit("dispatch stride mismatch: expect %d, got %d -- slot bodies differ in length"
                                 % (n * stride, p.count() - tbl0))
            p.hot_first = tbl0
            # 时间门控：未到点就落到下面的 hot（稳态 0 额外指令）。
            p.label("gate")
            p.j("refill", "greaterThanEq", "@time", "cfg.next")
            p.label("hot")
            # 物品未知时整圈空转没意义：直接跳回时间闸门。
            # 没有这条，cfg.item=null 时槽里
            #   jump uKt equal tmp.f cfg.item
            # 会拿 null 和 null 比出 true，单位以为拿到货、飞去投递点又飞回来。
            p.j("gate", "strictEqual", "cfg.item", "null")
            p.i("op add @counter @counter tmp.hp")
        else:
            if args.dispatch:
                # 绝对寻址（live 架构用）：入口地址 = base + 4 + (n-N)*stride。
                # base 用 @counter 在运行时抓，增删语句也不会失效。
                p.i("set tmp.base @counter")
                p.i("op add tmp.off tmp.base %d" % (4 + n * stride))
            p.label("hot")
            p.hot_first = p.labels["hot"]
            if args.dispatch:
                p.j("gate", "strictEqual", "cfg.item", "null")
                p.i("op mul tmp.p %s -%d" % ("L" if live else "N", stride))
                p.i("op add @counter tmp.off tmp.p")
            for k in (range(n, 0, -1) if args.dispatch else range(1, n + 1)):
                slot(k)

            gate = p.count()
            # 时间门控：未到点就回跳 hot（稳态 0 额外指令）。
            # 给这条打上 gate 标签：热入口的 cfg.item 空守卫要跳到它（绕过整圈槽位但保留 2 s 节流）。
            p.label("gate")
            p.j("hot", "lessThan", "@time", "cfg.next")
            if args.dispatch and gate - p.labels["hot"] - 3 != n * stride:
                raise SystemExit("dispatch stride mismatch: expect %d, got %d -- slot bodies differ in length"
                                 % (n * stride, gate - p.labels["hot"] - 3))
            if live and (gate - p.labels["hot"] - 2) % stride:
                raise SystemExit("live stride mismatch")

    # ---------- refill ----------
    p.label("refill")
    p.i("op add cfg.next @time", args.refill)

    if args.mode == "mine" and not args.item:
        # 每 2 s 重读一次 sorter1 的 @config：玩家中途换矿种时，全队在下一轮
        # 就会把身上的旧矿 drop @air 掉、改挖新矿（不清空就永远只挖开局那一种）。
        # 放在 refill 段开头而不是末尾：补员突发的每个出口都会 jump hot，
        # 排在后面的代码走不到（haul 版靠 loc 段落下来，mine 版没有 loc）。
        # 标签加后缀 r：init 里已经用过一次 ic2，重名会让 tonum/检查器直接报错。
        emit_item("r")

    if live:
        # 架构 B 的收缩段：直接算到 sh{L} 再往下滚，所以每次补员只花
        # 「3 条 + 4*死的人数」而不是「4*N」。
        p.i("set tmp.shr @counter")
        p.i("op mul tmp.p L -4")
        p.i("op add tmp.shrb tmp.shr %d" % (3 + 4 * n))
        p.i("op add @counter tmp.shrb tmp.p")
        for k in range(n, 0, -1):
            p.label("sh%d" % k)
            p.j("sh%d" % (k - 1), "notEqual", "L", k)
            p.i("sensor tmp.c u%d @controller" % k)
            p.j("sh%d" % (k - 1), "equal", "tmp.c", "@this")
            p.i("op sub L L 1")
        p.label("sh0")
        p.j("rf0", "always")
        p.label("rf0")
        # 收缩可能把 L 压到 0（全死），入口会跑出 hot 段；夹到 1，保证每圈至少扫槽 1。
        p.i("op max L L 1")

    p.i("set tmp.t 0")
    # 投递目标默认用「链接序号」取：getlink 的第二个参数是数字下标（0 基），
    # 源码 LExecutor.java:606-608  address = index.numi(); output = address in [0,links.length) ? links[address] : null
    # 写成名字（set tmp.lnk sorter1）是「按块类型自动命名的变量」，一旦把 1 号链接换成
    # vault/container，sorter1 仍是那个 sorter（或 null），代码就把死目标当成投递点 ——
    # 这就是「tmp.lnk 一直是 sorter」的原因。改用序号后链接换成什么都跟着走。
    if re.fullmatch(r"\d+", str(args.link)):
        p.i("getlink tmp.lnk %s" % args.link)
    else:
        p.i("set tmp.lnk %s" % args.link)
    p.j("rf1", "strictEqual", "tmp.lnk", "null")
    p.i("sensor lx tmp.lnk @x")
    p.i("sensor ly tmp.lnk @y")
    p.label("rf1")
    # ulocate 是「单位指令」：必须先绑到一只真单位，否则 checkLogicAI 失败 -> 整条静默跳过，
    # 只写 outFound=0，outX/outY 一个字节都不写（LExecutor.java:234-237, 273-276）。
    # 取「兵种」只需要 ubind 一只环形单位 + sensor @type，不会认领它
    # （实测：ubind 类型 + sensor @type 之后所有单位仍然 @controller==自身）。
    p.i("ubind cfg.utype")
    p.i("sensor uty @unit @type")
    p.j("hot", "strictEqual", "uty", "null")

    # 突发结束统一落到 loc（haul）——注意不能直接 jump hot：
    # 槽位数 > N 时，fillK 的「k > N」守卫会在 fill 里就把控制流带回 hot，
    # 于是排在最后的 loc 段永远走不到（实测 slots=31/N=8 时 sx/sy 恒为处理器坐标）。
    tail = "loc" if args.mode in ("haul", "mine") else "hot"

    # ---------- 体检 + 补员 ----------
    # 体检段也按 N 派发：只有 chk1..chkN 在路径上，chk(N+1)..chk(slots) 一条都不执行。
    # 槽位比 N 多多少都不花运行时间；N 在游戏里改了也不用重新生成（dispatch 按 N 算）。
    # 布局：chkN..chk1 连续降序（每槽 2 条：sensor + 「空就跳 fill」），
    #       之后 fillN..fill1 连续降序（填好一槽跳回 chk(K-1)，一趟把空位填满）。
    p.i("set tmp.cbk @counter")
    p.i("op mul tmp.p N -2")
    p.i("op add tmp.cbo tmp.cbk %d" % (3 + 2 * n))
    p.i("op add @counter tmp.cbo tmp.p")

    for k in range(n, 0, -1):
        p.label("chk%d" % k)
        p.i("sensor tmp.c u%d @controller" % k)
        p.j("fill%d" % k, "strictEqual", "tmp.c", "null")
    # chk1 的「还活着」分支必须离开体检段，否则会落进 fillN 把活槽覆盖掉。
    p.j(tail, "always")

    for k in range(n, 0, -1):
        u, s = "u%d" % k, "s%d" % k
        p.label("fill%d" % k)
        if dbg:
            p.i("set g%d 1" % k)
        # 不再需要「k > N 就跳 tail0」的守卫：dispatch 只会进 chk1..chkN，
        # fillK 因而只可能被 K<=N 的 chk 跳到。省下每槽 1 条。
        if live:
            # 密度守卫：只有 k <= L+1 才补（k<=L 是补洞，k==L+1 才是加长）。
            # 被挡住时接着体检下一槽（不能跳 tail0，否则高槽空着就整轮放弃，
            # 表长永远长不上去 —— 实测 L 恒为 1、一个槽都补不上）。
            p.j("chk%d" % (k - 1) if k > 1 else tail, "lessThan", "L", k - 1)
        p.label("f%d" % k)
        if dbg:
            p.i("set g%d 9" % k)
        p.i("op add tmp.t tmp.t 1")
        p.j(tail, "greaterThan", "tmp.t", "cfg.cap")
        p.i("ubind uty")
        p.i("sensor tmp.c @unit @controller")
        p.j(tail, "strictEqual", "@unit", "null")
        p.j("f%d" % k, "notEqual", "tmp.c", "@unit")
        p.i("set", u, "@unit")
        if dbg:
            p.i("set g%d 5" % k)
        if live:
            # 补洞时 max 不变，加长时正好 L=k
            p.i("op max L L %d" % k)
        if args.mode == "haul":
            if two:
                p.i("set dx%d sx" % k)
                p.i("set dy%d sy" % k)
            elif not args.stateless:
                # stateless 下 sK 是死变量（状态由 @firstItem 推导），不写。
                p.i("set", s, 0)
        # 给刚绑到的单位打一次 @controller 戳：LExecutor.java:322-329 每条 ucontrol
        # 都会把 controller 改成发令的建筑，所以任意一条 ucontrol 都能占位。
        # 用 payDrop 是因为它对没有 payload 的单位完全 no-op（payDrop 分支只在
        # unit instanceof Payloadc 时才动，且 timeoutDone 早退不影响前面的打戳），
        # 不像原来的 itemDrop cbc + move sx sy —— 那两条会把刚补进来的新兵立刻
        # 赶去核心，cfg.item 未知时整队就堆在核心上空转。
        #
        # 挖矿模式也必须打这一戳：loc 段用它判断「u1 是不是已经归我」，
        # 而挖矿槽在 ox 还是 null 时一条 ucontrol 都不发（否则会朝处理器格飞），
        # 于是新兵 controller 恒 null —— loc 永远进不去，ox 永远是 null（死锁）。
        p.i("ucontrol payDrop")
        # 助推：ai.boost 存在 LogicAI 实例上，而 checkLogicAI 命中已有实例时只改
        # controller（LExecutor.java:322-326）⇒ 认领时打一次就跨圈保持，热路径 0 成本。
        # 站在矿格上时 onSolid() 为假（矿格是 Floor，solid=false），引擎不会自动助推，
        # 所以这条对 canBoost 的矿工（pulsar 1.6x / quasar 2.0x / corvus 2.4x）是真提速；
        # 代价是 LogicAI.java:147 助推时不开火 —— 采矿用不到射击。
        if boost:
            p.i("ucontrol boost 1")
        # 补员是「突发」：填好一槽后立刻接着填下一槽，整轮一次把空位填满。
        # 但要回到 chk（不是直接进 fill）——fillK 只做「这个槽是空的」这一件事，
        # 直接跳 fill(K+1) 会覆盖已经填好的槽，把原来那只单位变成「被我们控制、
        # 却不在任何槽里」的孤儿。
        # 补好一槽之后往哪走：
        #   live（表长架构）往上爬 —— L 刚刚变成 k，k+1 正好过守卫，
        #     一口气把表补到 N；往下走只会一轮补一个槽（实测 8 槽要 14 s）。
        #   默认（固定槽位）往下走 —— 上面的槽刚刚体检过是活的，不用回看。
        if live:
            p.j("chk%d" % (k + 1) if k < n else tail, "always")
        else:
            p.j("chk%d" % (k - 1) if k > 1 else tail, "always")

    p.j(tail, "always")

    if args.mode == "haul":
        # zd：定位必须放在补员之后，而且必须绑一只「已经归我们」的单位。
        # 坑：ulocate 内部调用 UnitControlI.checkLogicAI()（LExecutor.java:235），
        # 那函数不只「检查」——它会 new LogicAI() 并把 controller 设成本处理器
        # （LExecutor.java:322-340）。所以只要拿一只自由单位去 ulocate，
        # 那只单位就被静默认领了：它会一直在干活却不在任何槽里，
        # 其他槽位永远补不到它（实测 8 只单位只填到 7 槽，第 8 只 @controller 恒为处理器）。
        p.label("loc")
        p.i("ubind u1")
        p.j("loc0", "notEqual", "@unit", "null")
        p.j("hot", "always")
        p.label("loc0")
        # 核心位置缓存：ulocate 给的是「离当前绑定单位最近的核心」，两个核心都在附近时
        # 每次补员都可能换一个，单位就在两核之间来回飞（还白跑一整趟）。
        # 只在三种情况下重定位：① 还没认到核心 ② 货源被熔断成 null
        # ③ 投递目标已装满（totalItems >= itemCapacity）；③②都过一道时间节流。
        p.j("locgo", "strictEqual", "cbc", "null")
        p.j("locF", "strictEqual", "st", "null")
        # 重定位时机 = 有单位刚卸空（热循环里 set tmp.needloc 1），再叠一道时间节流
        # 防止两个核心都在附近时来回换点。不再看「投递目标装满」。
        if getattr(args, "needloc", False):
            p.j("locr", "strictEqual", "tmp.needloc", "0")
        p.label("locF")
        p.j("locr", "lessThan", "@time", "cfg.nloc")
        p.label("locgo")
        # building 定位里 ore 参数完全不参与（switch 只看 flag -> getFlagged）：
        # 拿到的是「离当前绑定单位最近的核心」，与 cfg.item 无关。
        p.i("ulocate building %s 0 cfg.item sx sy tmp.g st" % args.source)
        p.i("ulocate building core 0 0 cbx cby tmp.g3 cbc")
        p.i("op add cfg.nloc @time %d" % args.recheck)
        if getattr(args, "needloc", False):
            p.i("set tmp.needloc 0")
        p.j("rf2", "notEqual", "st", "tmp.lnk")
        p.i("set st null")
        p.label("rf2")
        if not args.test_nolink:
            p.j("rf3", "notEqual", "tmp.lnk", "null")
            p.i("set st null")
            p.label("rf3")
        p.label("locr")
    elif args.mode == "mine":
        # 矿区定位（挖矿版的 loc 段）。形状与搬运版完全一致，只是把
        # ulocate building core 换成 ulocate ore，并且多一个「矿种换了」的门。
        # 触发条件（两条并集）：
        #   ① cfg.ore != cfg.item —— 第一次跑 / 玩家把 sorter1 换成别的矿
        #   ② 距上次定位已过 --recheck 毫秒（纯时间闸门，不掺货物状态）
        # 为什么必须先 ubind + 校验 @controller：ulocate 内部调 checkLogicAI()，
        # 那只函数会把被绑定的**自由单位**静默认领（controller 设成本处理器），
        # 于是它干着活却不在任何槽里，见上面搬运版同一段注释。
        p.label("loc")
        p.i("ubind u1")
        p.j("loc0", "notEqual", "@unit", "null")
        p.j("hot", "always")
        p.label("loc0")
        p.i("sensor tmp.c @unit @controller")
        p.j("hot", "notEqual", "tmp.c", "@this")
        # 矿种变了立刻重定位，不受时间闸门限制（不然会白挖一整趟旧矿）。
        p.j("locgo", "notEqual", "cfg.ore", "cfg.item")
        p.j("locr", "lessThan", "@time", "cfg.nloc")
        p.label("locgo")
        # ore 参数在这里是**真的参与**的（LExecutor.java:247-250）：
        # indexer.findClosestOre(unit, item) 找「离当前绑定单位最近的那块该矿」。
        # outX/outY 是格坐标；找不到时 outX/outY 不写、outFound=0（ox 保持 null）。
        p.i("ulocate ore core 0 cfg.item ox oy tmp.gm ob")
        p.i("set cfg.ore cfg.item")
        p.i("op add cfg.nloc @time %d" % args.recheck)
        p.label("locr")
    if args.mode != "mine":
        # haul：物品读取放在 loc 之后 —— 兜底分支要读核心（cbc）现有的第一种货。
        # mine：已经在 init 里发过了（见上面的 emit_item() 调用）。
        emit_item()
    # 程序最后一条必须是「回热循环」：否则补员段跑完会从末尾掉出去，处理器把
    # @counter 归 0 从头执行 init（实测 --item 分支漏了这条，每 24 tick 一次
    # wrap：init 把 sx/sy 重写成处理器格、cfg.nloc 清零 ⇒ 单位永远飞向逻辑位置，
    # 与「没有去目标建筑」的现象完全一致）。
    p.j("hot", "always")
    return p, hotn if two else None


def main():
    ap = argparse.ArgumentParser(description="单位多控逻辑编译器")
    ap.add_argument("--mode", choices=["haul", "hold", "mine"], default="haul",
                    help="haul=搬运；hold=占位；mine=挖矿（ulocate ore 定位 -> approach -> mine -> 满仓投递）")
    ap.add_argument("--slots", type=int, default=8)
    ap.add_argument("--n", type=int, default=0, help="set N 的默认值；0=等于 --slots")
    ap.add_argument("--item", default="", help="写死物品(如 @copper)，不给则从物品选择器的 config 读")
    ap.add_argument("--item-src", dest="item_src", default="",
                    help="物品选择器（有 config 的 sorter）的链接序号；默认等于 --link")
    ap.add_argument("--no-item-fallback", dest="item_fallback", action="store_false",
                    help="选择器 @config 为空时不要退回『搬核心第一种货』")
    ap.add_argument("--test-nolink", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--stateless", action="store_true", help="状态外化：每单位 12 条")
    ap.add_argument("--probe", action="store_true", help="每槽首加 set dbg.sK 1，验证入口落点")
    ap.add_argument("--dispatch", action="store_true", help="op @counter 算入口，0 条守卫")
    ap.add_argument("--guard", action="store_true", help="每槽一条 N 守卫")
    ap.add_argument("--live", action="store_true", help="架构 B：表长 L=存活数，成本 ∝ 存活")
    ap.add_argument("--twospeed", action="store_true", help="架构 C：快环 2 条/单位 + 慢环轮转")
    ap.add_argument("--dbg", action="store_true", help="诊断：fillK 记 gK（1=到达 9=过守卫 5=补上）")
    ap.add_argument("--no-shortpath", dest="shortpath", action="store_false",
                    help="关掉取/放物品后立即转向的短路径（默认开）")
    ap.add_argument("--type", default=None,
                    help="兵种；默认 haul/hold=@flare，mine=@poly（flare 没有 mineSpeed，挖不了矿）")
    ap.add_argument("--refill", type=int, default=2000, help="补员周期 ms")
    # 默认不留「刚卸空」标记：它每槽 1 条（30 槽 = 33 条），换来的是
    # 每次卸空都重定位核心 —— 而 loc 段本来就有 3 s 时间闸门兜底，
    # 实测有无 needloc 的 itemTake/itemDrop 次数完全一样（56/48）。
    # --needloc 可以把卸空触发买回来（要付每槽 1 条）。
    ap.add_argument("--needloc", dest="needloc", action="store_true",
                    help="保留『刚卸空 → 重定位核心』标记（每槽 1 条，默认关）")
    ap.add_argument("--recheck", type=int, default=3000,
                    help="核心重定位的最小间隔 ms（只在目标装满/货源丢失时才会考虑重定位）")
    ap.add_argument("--cap", type=int, default=0)
    ap.add_argument("--link", default="0",
                    help="投递目标的链接序号(0 基, 对应编辑器里链路第 1 个)；也可以直接写建筑变量名")
    ap.add_argument("--source", choices=["core", "storage"], default="core")
    ap.add_argument("--graze", choices=["core", "storage", "none"], default="storage")
    ap.add_argument("--approach", default="6.5", help="approach 半径(格)：默认 6.5 格 -> 停机 45 世界单位 = logicItemTransferRange(Vars.java:125)")  # noqa: E501
    ap.add_argument("--boost", dest="boost", action="store_true",
                    help="补员认领时发 ucontrol boost 1（pulsar/quasar 等 canBoost 单位移动提速）")
    ap.add_argument("--no-boost", dest="no_boost", action="store_true",
                    help="挖矿模式默认会发 boost，给这个开关关掉")
    ap.add_argument("--arrive", default="3")
    ap.add_argument("-o", "--out", default="")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.mode == "mine":
        # 挖矿没有「货源建筑」可顺路取，也不该在 sorter 没配时退回核心第一种货
        # （那个兜底要 ulocate core，而挖矿版根本不定位核心）。
        if a.graze != "none":
            a.graze = "none"
        a.item_fallback = False
        a.stateless = True
    if not a.type:
        a.type = "@poly" if a.mode == "mine" else "@flare"
    if a.dispatch:
        a.guard = False
    if a.live and not a.dispatch:
        raise SystemExit("--live 需要 --dispatch（入口要按 L 动态算）")
    if a.twospeed:
        # 架构 C 已弃用：双速环的单只判定周期下限 = N*(2N+7+22)/120，
        # N=8 时 (8*23+176)/120 ≈ 1.66 s，比单环 A 的 1.06 s 还慢，
        # 因为 22 条的慢块本身就比 A 的整块(15 条)胖；只有「保航向」这一点变快。
        raise SystemExit("架构 C（--twospeed）已弃用：单只判定周期下限 1.66 s > 单环 A 的 1.06 s，"
                         "请用默认(--stateless --dispatch) 或 --live")

    p, hotn_two = build(a)
    lines = p.render(labeled=True)
    body = "\n".join(lines)

    ipt = 2.0
    if a.twospeed:
        # 一圈 = 快环 + 轮转 + 一个慢块；每个单位被完整处理一次要 N 圈
        hotn = hotn_two
        per = hotn / ipt / 60.0
        deep = a.slots * per
        note = "# 一圈 %d 条 (%.3f s)，每单位完整判定 %d 条一轮 -> %.2f s/单位" % (
            hotn, per, a.slots, deep)
    else:
        hotn = p.labels["refill"] - getattr(p, "hot_first", p.labels["hot"])
        hot_s = hotn / ipt / 60.0
        note = "# 热循环 %d 条 -> micro 满载每圈 %.2f tick / %.3f s" % (hotn, hotn / ipt, hot_s)
    cyc = p.count() / ipt / 60.0
    header = [
        "# mlogc 生成：mode=%s slots=%d type=%s refill=%dms cap=%d source=%s%s%s" % (
            a.mode, a.slots, a.type, a.refill, a.cap, a.source,
            " live" if a.live else "", " twospeed" if a.twospeed else ""),
        note,
        "# 全程序 %d 条（含补员突发）；micro(2 ipt) 最坏整圈 %.0f tick / %.2f s" % (
            p.count(), p.count() / ipt, cyc),
        "",
    ]
    text = "\n".join(header) + body + "\n"

    out = a.out or ("out/mlogc-%s-%d.labels.mlog" % (a.mode, a.slots))
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(text)
    print("wrote %s  (hot %d stmts, total %d stmts)" % (out, hotn, p.count()))

    if a.check:
        r = subprocess.run([sys.executable, "tools/mlog.py", "check", out, "--cost"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        print(r.stdout[-2500:] or r.stderr[-2500:])


if __name__ == "__main__":
    main()
