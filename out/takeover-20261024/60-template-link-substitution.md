# 60 · v0.9.2：模板写 message1、处理器上只有 message2 时，自动挑最近的那个

日期 2026-10-30。上一刀候选②。

## 60.1 症状

玩家在处理器上接的显示/消息块叫 `message2`（多处理器共用一台显示时的常态），而锚定档模板
（`item-threshold`、`timer-flush` 等）生成的代码里写死 `printflush message1`。
`compose()` 的做法是：模板 refs 里出现处理器没有的名字 → `template-needs-link` **ERR** 拒绝，
面板上就是「投递失败」，玩家得自己回去改名字或改模板，白投一次作业。

## 60.2 判据

链接名 = `<方块名><序号>`（`LogicBlock.java:331-360` `findLinkName()`），所以 `message1` 与
`message2` 是**同一个方块的不同编号**，在语义上可替换，区别只在连到了哪个对象。
于是规则定为：模板要的链接名未绑定 → 找**同族**（去掉尾部数字后相同）且**已绑定**的链接，
按到处理器的欧氏距离取最近的替换；同族一个都没有才维持原来的 ERR。

## 60.3 改动（`tools/logicd.py`）

三个 helper（插在 `_relative_links()` 之前）：

| 名字 | 职责 |
| --- | --- |
| `_link_stem(name)` | `message2` → `message`；`re.match(r'^(.*?)(\d+)$', ...)`，无数字返回原名 |
| `_nearest_link(name, links, origin)` | 同族已绑定候选里按 `(x-ox)**2+(y-oy)**2` 取最近；无 origin 时距离全 0（取第一个）；links 元素兼容 dict 与裸字符串 |
| `_substitute_links(code, subs)` | 整词替换，`(?<![A-Za-z0-9_-])old(?![A-Za-z0-9_-])` ⇒ `message1` 不会误伤 `message10` |

`compose()` 的判定顺序改成：先算 `subs`（每个未绑定 ref → `_nearest_link`）→ 有替换就改 `code` →
`missing = [n for n in refs if n not in names and n not in subs]` → `analyse()` → 每条替换插一条
`{'sev': 'INFO', 'rid': 'template-link-substituted', 'msg': "template 'item-threshold' writes message1 but
this processor has no such link; used message3 instead (nearest bound link of the same block)"}`。
payload 用**替换后**的 code 构建，所以写进处理器的就是能跑的那份。

## 60.4 踩到的坑：同名函数被覆盖

第一版把 helper 叫 `_link_base`，实测完全不生效（`_link_base('message1')` 返回 `'message1'`）。
原因：`tools/logicd.py:709` **早就有一个** `_link_base(block)`（`LogicBlock.getLinkName()` 语义：
取最后一个 `-` 段，若为 `large` 或纯数字则取倒数第二段），Python 后定义覆盖先定义 ⇒ 我的版本被吃掉。
改名 `_link_stem` 并替换三处调用后正常。**教训：往 1500 行以上的文件插 helper 之前，先 grep 函数名。**

## 60.5 复验

- in-process（`out/_near_t.py`）：links `container1@198,190 / message2@260,190 / message3@199,190`，
  origin `197,190` → `ok True`、code 含 `message3` 不含 `message1`、findings 只有
  `('INFO','template-link-substituted')`。同族全缺（只有 container1）→ 仍 `ok False` +
  `('ERR','template-needs-link')` + `('WARN','link-name-not-bound')`。
- `tests/logicd/run_logicd_tests.py` 新增一块（compose + 上述三链接 + origin，断言 ok / 换成 message3 /
  有 INFO rid），`--no-sim` → **protocol 26（原 25）/ jobs 12 / provider 9，EXIT=0**。
- `gate.py --full` 首跑 15/16（kb stale，因为改了 tools/README.md）→ `tools/kb.py build`
  `{chunks 6359, files 65}` → **16/16 passed in 34.3s**。

## 60.6 没做的事

模组侧一行未改（`main.js` 没动、`mod.hjson` 不 bump），因为替换发生在侧车的 `compose()` 里，
面板拿到的是同一条 `/compose` 响应，只是 `findings` 里多一条 INFO。**因此不重打 zip、不重装游戏。**
副作用提醒：旧版侧车进程不会带上这个兜底，改完要重启 sidecar（见 v0.9.1 那节）。

## 60.7 下一刀候选

①面板记住上次选中的 provider ②`rejected` 作业在面板上给「加消息块」可点提示
③替换也覆盖自由档（模型档 `needs_links` 目前是硬拒绝，不走同族兜底）。
