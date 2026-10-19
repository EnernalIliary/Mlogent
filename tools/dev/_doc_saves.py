"""Add the save-sweep section to the notes and the two SKILL files."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTES = ROOT / "mlog工作笔记.md"

SECTION = """## 15.37 存档里的逻辑：103,787 个处理器，其实只有 4,366 份程序

`mlog.py map` 能读一个存档；把它乘上整个 `saves/` 目录，就是这个游戏里
「真实存在的逻辑」的全貌。1421 个 `.msav`（v7 289 / v8 149 / v9 61 / v10 45 /
v11 877）全部解析成功，**103,787 个处理器、963 万行代码**。

按**源码文本**的 sha1 去重（不含 links —— 同一段程序贴到四十个处理器上，是
一个 bug，不是四十个）：

| 指标 | 数值 |
| --- | --- |
| 处理器 | 103,787 |
| 不同程序 | **4,366** |
| 完全相同的副本 | 99,421（**95.8%**） |
| 被复制最多的一份 | 9,699 份（22 行，`236.msav`） |
| 发现总数 | 10,544（ERR 839 / SUSPECT 97 / WARN 3,306 / INFO 6,302） |

硬错里最大的一类还是「读了从没赋过值的变量」（814 条），其次是 `@dead` 极性
（97）、链接名拼错（约 500）、无出口死循环（11）、`noop`（9）。

三个教训：

1. **去重改变分母。** 不去重时，9,699 份同一个 22 行程序的错误会把
   「每处理器错误率」变成「副本数统计」。凡是要说「这个游戏里逻辑质量如何」，
   分母必须是**不同的程序**。
2. **聚合要按「规则」，不能按「出问题的那一行」。** `Finding.code` 字段装的是
   **源码行**（方便打印 `[ERR] L12 jump 99 always 0 0: ...`），直接拿它分组会得到
   5,023 个类 —— 等于没分组。按消息把数字和反引号名字归并掉，才得到 24 条规则。
3. **一张图 = 一份程序 + 一万份实例。** 95.8% 的处理器是复制品，说明这类地图
   （逻辑计算机、像素屏、塔防）的写法是「写一次，铺满地图」，而不是「每格单独写」。
   所以查这类图要抽样，不能逐个看。

"""

CHANGELOG = ("- 第 44 次整理：把 `mlog.py map` 乘以整个 `saves/`（1421 个存档、103,787 个处理器），"
             "按源码哈希去重后发现只有 4,366 份不同的程序、95.8% 是副本。方法论："
             "「聚合的单位决定了你能看见什么 —— 按行分组看见的都是行，按规则分组才看得见规则。」")

s = NOTES.read_text(encoding="utf-8")
assert "## 15.37" not in s, "section already there"
anchor = "\n## 16. ⚠️"
assert anchor in s, "section 16 anchor missing"
s = s.replace(anchor, "\n" + SECTION + anchor, 1)
s = s.rstrip("\n") + "\n" + CHANGELOG + "\n"
NOTES.write_text(s, encoding="utf-8")
print("notes: ok")

ADD = """
### 全量体检（1421 个存档）

`mlog.py map` 一次读一个文件。要看**所有**存档，先按源码哈希去重再跑静态检查
（`tools/_sweep_analyse.py`）：1421 个存档、103,787 个处理器，去重后只有
**4,366 份不同的程序**（95.8% 是同一段代码的副本）——所以报告里所有比率的分母
都是「不同的程序」，不是「处理器」。
"""

for rel in ("mindustry-blueprint/SKILL.md", ".dsh/skills/mlog-agentskill/SKILL.md"):
    p = ROOT / rel
    t = p.read_text(encoding="utf-8")
    if "### 全量体检" in t:
        print(f"{rel}: already there")
        continue
    key = "## 读整个存档里的逻辑"
    i = t.find(key)
    if i < 0:
        print(f"{rel}: !! section not found")
        continue
    j = t.find("\n## ", i + len(key))
    j = len(t) if j < 0 else j
    t = t[:j] + ADD + t[j:]
    p.write_text(t, encoding="utf-8")
    print(f"{rel}: ok")
