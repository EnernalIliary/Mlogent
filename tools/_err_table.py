"""Dump every finding of the blueprint-pack scan as a reviewable, tiered table.

Written for the "让我评判一下" pass. The key lesson from that pass: an
"undeclared variable" is *four different things* in this community, and only
one of them is a bug.

  A. 真错      -- the name is read where its value actually changes behaviour
  B. 恒真守卫  -- both sides of a `jump` are constants, so the branch is fixed
                  (very often a signature smuggled into a comparison: `colour`
                  `ender` is one integrator's name)
  C. 无效参数  -- the name sits past the last parameter the instruction reads
                  (`control` only honours 3), so the game never looks at it
  D. 署名      -- the name exists only to appear in the editor's variable list

B and C are warnings, D is info, only A is an error. The tiers come from the
user's reading of the game, not from the language, so they are recorded here
rather than guessed at in the checker.
"""
from __future__ import annotations

import collections
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN = ROOT / "out" / "caime_scan.json"

# What an undefined read *does*, by the statement that reads it. This is the
# column that makes the table judgeable: `print` of an unset name is invisible,
# `op add` with an unset operand silently adds 0, and a `jump` on one is a
# constant branch.
EFFECT = {
    "jump": "控制流:比较对象恒为 0/null ⇒ 分支恒真或恒假",
    "op": "算术:操作数静默当 0",
    "control": "目标:指向的方块名/参数不存在 ⇒ 指令无效果",
    "printflush": "目标:要 flush 的 message 不存在 ⇒ 无输出",
    "radar": "目标:排序/过滤参数无效",
    "uradar": "目标:排序/过滤参数无效",
    "sensor": "数据源:读不到 ⇒ 结果 null",
    "read": "数据源:读不到 ⇒ 结果 null",
    "write": "目标:写不到 ⇒ 静默丢弃",
    "ulocate": "目标:定位参数无效",
    "ucontrol": "目标:控制参数无效",
    "ubind": "目标:绑不到单位 ⇒ @unit 为 null",
    "lookup": "目标:查不到类型 ⇒ 结果 null",
    "getlink": "目标:链接不存在 ⇒ 结果 null",
    "getblock": "目标:读不到方块 ⇒ 结果 null",
    "setprop": "目标:属性写不进",
    "set": "值:赋进去的是 0/null",
    "select": "值:被选中的分支恒为 0/null",
    "draw": "绘制:坐标/颜色为 0",
    "print": "打印:输出 null 文本",
}

TIER_OF = {
    "ERR": "A",
    "WARN": "B",   # split further below: surplus-parameter warnings are tier C
    "INFO": "D",
}


def mnemonic(code: str) -> str:
    p = code.split()
    return p[0].lower() if p else "?"


def var_of(msg: str) -> str:
    m = re.search(r"`([^`]*)`", msg)
    return m.group(1) if m else "?"


def read_scan() -> tuple[list, list, list, list]:
    """(errs, constant_guards, surplus, signatures) as row tuples."""
    data = json.loads(SCAN.read_text("utf-8"))
    errs: list[tuple[str, str, int, str, str]] = []
    guards: list[tuple[str, str, int, str, str]] = []
    surplus: list[tuple[str, str, int, str, str]] = []
    signed: list[tuple[str, str, int, str, str]] = []
    for r in data["rows"]:
        name = Path(r["file"]).name
        for b in r["detail"]:
            where = f'{b["block"]} @({b["at"][0]},{b["at"][1]})'
            for sev, ln, code, msg in b["findings"]:
                row = (name, where, ln, code, msg)
                if sev == "ERR":
                    errs.append(row)
                elif sev == "INFO":
                    signed.append(row)
                elif "parameter slot" in msg or "given 3 args" in msg:
                    # Both are the same disease: the name sits where the
                    # instruction never looks. `op rand g 255 b` is a signature
                    # parked in a unary operator's third (ignored) slot.
                    surplus.append(row)
                elif sev == "WARN":
                    guards.append(row)
    return errs, guards, surplus, signed


def reason_for(var: str, kinds: collections.Counter) -> str:
    """Why this particular name, read here, is a bug rather than a habit."""
    if var == "flase":
        return "`false` 拼错 ⇒ 参数变成 0"
    if var in ("max", "min"):
        return "想要无穷大/极值,实际拿到 0"
    if set(kinds) == {"ubind"}:
        return "绑不到单位 ⇒ `@unit` 为 null"
    if kinds.get("control") or kinds.get("printflush"):
        return "指向不存在的方块 ⇒ 指令无效果"
    if kinds.get("ulocate") or kinds.get("ucontrol"):
        return "控制/定位参数写成变量名 ⇒ 退化成默认值"
    if set(kinds) == {"jump"}:
        return "守卫恒真或恒假,分支从此固定"
    if kinds.get("op"):
        return "算术里静默当 0"
    if kinds.get("sensor") or kinds.get("read"):
        return "读不到 ⇒ 结果恒 null"
    return "未赋值就被用"


def var_table(rows: list[tuple[str, str, int, str, str]],
              title: str, verdict_note: str | None = None) -> list[str]:
    by_var: dict[str, list[str]] = collections.defaultdict(list)
    for _, _, _, code, msg in rows:
        by_var[var_of(msg)].append(mnemonic(code))
    out = [f"### {title}", ""]
    if verdict_note:
        out.append("| 次数 | 变量 | 被哪种语句读 | 判读 |")
        out.append("|---:|---|---|---|")
    else:
        out.append("| 次数 | 变量 | 被哪种语句读 | 为什么是错 |")
        out.append("|---:|---|---|---|")
    for var, kinds in sorted(by_var.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:40]:
        c = collections.Counter(kinds)
        mix = ", ".join(f"`{k}`×{n}" for k, n in c.most_common(4))
        note = verdict_note if verdict_note else reason_for(var, c)
        out.append(f"| {len(kinds)} | `{var}` | {mix} | {note} |")
    out.append("")
    return out


def shape_table(rows: list[tuple[str, str, int, str, str]], top: int = 20) -> list[str]:
    shapes = collections.Counter()
    for _, _, _, code, _ in rows:
        s = re.sub(r"`[^`]*`", "`X`", code)
        s = re.sub(r"-?\d+(\.\d+)?", "N", s)
        shapes[s] += 1
    out = ["| 次数 | 语句形态 | 运行时后果 |", "|---:|---|---|"]
    for s, n in shapes.most_common(top):
        out.append(f"| {n} | `{s}` | {EFFECT.get(mnemonic(s), '?')} |")
    out.append("")
    return out


def main() -> int:
    errs, guards, surplus, signed = read_scan()

    out: list[str] = []
    out.append("# 蓝图包错误清单(926 份)—— 按「是不是真错」分四层")
    out.append("")
    out.append("包来源:`非mod+像素工厂蓝图【彩末整合】160+v-30`,由 colour ender(彩色末影)整合,")
    out.append("内容来自服务器/档案馆/残阳蓝图库 ⇒ 这**不是一个人**的作品,只能代表一批作者。")
    out.append("926 份里 481 份有逻辑,1698 个逻辑块,359,131 条语句。")
    out.append("")
    out.append("| 层 | 含义 | 条数 |")
    out.append("|---|---|---:|")
    out.append(f"| **A 真错** | 名字被读的地方,值真的改变行为 | **{len(errs)}** |")
    out.append(f"| B 恒真守卫 | `jump` 两侧都是常量 ⇒ 分支固定,常是署名 | {len(guards)} |")
    out.append(f"| C 无效参数 | 名字落在指令读不到的参数位上 | {len(surplus)} |")
    out.append(f"| D 署名 | 只为出现在变量列表里 | {len(signed)} |")
    out.append("")
    out.append("只有 A 需要改。B/C/D 都是这个社区的写作习惯,不是错误。")
    out.append("")

    out.append("## A 真错 —— 按变量")
    out.append("")
    out.extend(var_table(errs, f"共 {len(errs)} 条 / "
                               f"{len({var_of(m) for *_, m in errs})} 个名字"))
    out.append("## A 真错 —— 按语句形态")
    out.append("")
    out.extend(shape_table(errs))
    out.append("## B 恒真守卫 —— 按变量")
    out.append("")
    out.extend(var_table(guards, "比较两侧都是常量,分支恒真或恒假", "改写成 `always`,或那是署名"))
    out.append("## C 无效参数 —— 按变量")
    out.append("")
    out.extend(var_table(surplus, "落在指令读不到的参数位上,运行时被忽略", "不用改"))
    out.append("## D 署名 —— 出现最多的名字")
    out.append("")
    out.extend(var_table(signed, "只为在编辑器变量列表里留名", "不用改"))

    out.append("## 附录:A 层逐条明细")
    out.append("")
    cur = None
    for name, where, ln, code, msg in sorted(errs):
        if name != cur:
            cur = name
            out.append("")
            out.append(f"### {name}")
            out.append("")
            out.append("| 行 | 块 | 语句 | 说明 |")
            out.append("|---:|---|---|---|")
        out.append(f"| {ln} | {where} | `{code}` | `{var_of(msg)}` 未赋值 |")

    dest = ROOT / "out" / "caime_errs.md"
    dest.write_text("\n".join(out) + "\n", "utf-8")
    print(f"wrote {dest}  A={len(errs)} B={len(guards)} C={len(surplus)} D={len(signed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
