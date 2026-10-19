"""Append the auto-labelling section to the notes and a line to SKILL.md."""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

SECTION = """
### 15.23 自动打标签:标签到底能不能从内容推出来

标签是分面的:颜色=维度、私有区图标=值的身份、末尾文字=值名。70 个值 / 14 个维度,
`000标签排序.msch` 把 69 个值全挂在一份蓝图里当配色卡。**全部手打** —— 所以问题是
"哪些值的出现与否,其实是内容的函数"。

做法不是手写规则,是**学一半、测另一半**:把 625 份按文件名的 sha1 分成两半,
在一半上学 `值 -> 方块/逻辑记号`(`train`),在另一半上量精确率(`precision`)。
一个方块能当签名,要同时满足:出现在该值 ≥75% 的文件里、全语料占比 ≤20%、
lift ≥0.45。**`UBIQUITOUS = 0.20` 这一条是关键** —— `micro-processor` 在每份带逻辑的
蓝图里都有,不排掉的话「含微处理器」这条规则会在几乎全语料上开火(实测平均精确率
44% → 5% 那次就是它)。同理只保留**单个**签名:`cryofluid-mixer` 作为 冲反/温差/冷冻
的第二签名会把三条规则同时污染到 6%~27%。

**结果:43 个值能学到规则,其中 24 个留出集精确率 ≥70%**,可以直接用:
t5厂、世处、冲反、分裂、力墙、厄兆、塑钢、大硅、小超、幽灵、抽水、核心蓝图、气旋、
水炮、涡轮、温差、熔毁、着陆、窑炉、自冷、蜂群、质驱、钍反、雷光。
剩下的(<70%)是判断题,或者根本不是内容的函数:

- `数量`(`1…9` / `10~19` / `20~29` / `极多`):高段确实等于「同一种方块的最大重复数」
  的中位数 16 / 31 / 44,低段 1–9 与核心数、超频数、逻辑块数都不相关 ⇒ 不可推;
- `品质`(`常用` / `未分类或低效`)、`系列`(`ILI`)、`实用`:主观判断;
- `无线`、`火控`、`兵控`:逻辑形态能提示(`ulocate`+`ucontrol`+`ubind`、`radar`),
  但同一份蓝图常常三种都沾 ⇒ 精确率 15%~24%,不建议自动;
- `冷冻`、`串联`、`绿带`、`白沙`、`黑沙`、`硫化`:要么是地形/布局,要么是作者的
  组织习惯,方块层面留不下签名。

**写回是外科手术式的**:`.msch` 的正文是 zlib 流,标签只是 tags 里的一个 JSON 字符串。
所以 `rewrite_labels()` 解压 → 走到 tags 结束的位置(`Reader.pos`)→ 只重写 tags 段 →
**把剩下全部字节原样接回去**再压缩。这样非逻辑方块的配置(连线数组等)一个字节都不会动,
也不会踩到导出工具「226 skipped」那个坑。实测往返 66 方块 / 1 逻辑块 / 16 标签无损。

命令:`python tools/label_auto.py`(学习+留出集报表)、`--suggest F.msch`(只出可信建议)、
`--apply F.msch --out DIR`(写回副本,永不覆盖原件)。
"""

CHANGELOG = """
- **第 32 次整理**:新增 §15.23。方法论:**一个标签值是不是"内容的函数",可以用留出法量出来;量不出来的,就是人给的定义,别假装能推。**

"""


def main() -> None:
    notes = ROOT / "mlog工作笔记.md"
    s = notes.read_text(encoding="utf-8")
    if "### 15.23" not in s:
        i = s.index("## 16.")
        s = s[:i] + SECTION + "\n" + s[i:]
    if "第 32 次整理" not in s:
        j = s.index("## 18.")
        k = s.index("\n", s.index("\n", j) + 1) + 1
        # insert right after the changelog heading block's first blank line
        s = s[:k] + CHANGELOG.lstrip("\n") + s[k:]
    notes.write_text(s, encoding="utf-8")

    skill = ROOT / "mindustry-blueprint" / "SKILL.md"
    t = skill.read_text(encoding="utf-8")
    marker = "## 参考数据"
    if "自动打标签" not in t:
        block = """## 自动打标签

蓝图标签(颜色=维度、私有区图标=值身份)是手打的,但**其中 24 个值可以从内容推出来**,
留出集精确率 ≥70%:

```bash
python tools/label_auto.py                      # 学习规则 + 留出集报表
python tools/label_auto.py --suggest F.msch      # 只输出可信建议(附依据与精确率)
python tools/label_auto.py --apply F.msch --out DIR   # 写回副本,不动原件
```

`数量` / `品质` / `系列` / `无线` / `火控` 这类量不出精确率的值不会出现在建议里 ——
它们要么是主观判断,要么同一份蓝图三种都沾。写回只重写 tags 段,其余字节原样搬运。

"""
        t = t.replace(marker, block + marker, 1)
    skill.write_text(t, encoding="utf-8")
    print("notes + skill updated")


if __name__ == "__main__":
    main()
