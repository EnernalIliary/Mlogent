"""Docs for the program-fingerprint pass (section 15.38 + changelog 45 + skills)."""
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
notes = HERE / "mlog工作笔记.md"
s = notes.read_text(encoding="utf-8")

SECTION = """
## 15.38 给匿名的程序起一个「像什么」的名字

存档里的处理器**没有名字**。mlog 语言里不存在名字字段——只有蓝图（`.msch`）有 `name`/`description`/`labels`；存档里唯一的名字是地图名（`meta.mapname`），不是程序的。所以 4,367 份不同的程序全是匿名的，判用途只能读代码。

但「用途」可以不靠名字推。三个廉价信号就够：

| 信号 | 为什么有信息量 | 例子 |
| --- | --- | --- |
| 链接名 | 链接名默认就是方块名+序号，作者通常不改 | `display1`/`dome1`/`sorter…` |
| 指令直方图 | 每个领域有专属指令 | `draw`=显示、`ubind`=单位、`control config`=物流、`setrule`=世界规则 |
| 代码里的字符串 | 全程序往往只有一两段给人看的字 | `'队伍'`、`'黑名单'`、`'一键生成空辅路辅'` |

跑出来的分桶（`tools/_label_programs.py` → `out/saves_programs.md`）：

| 桶 | 程序数 | 语句数 | 副本数 |
| --- | ---: | ---: | ---: |
| 像素画(逐格 draw) | 2,022 | 1,933,000 | 6,285 |
| 单位 | 830 | 64,331 | 19,866 |
| 物流 | 630 | 30,209 | 24,199 |
| 规则/世界 | 384 | 36,349 | 22,684 |
| 显示/UI | 177 | 46,000 | 11,321 |
| 计算/内存 | 151 | 9,179 | 2,152 |
| 其他 | 129 | 2,049 | 10,330 |
| 通信 | 44 | 1,403 | 8,359 |

三条教训：

1. **第一版分类全塞进「显示」**——因为把「出现过一次 `draw`」当成了显示程序。改成「draw 占语句一半以上 = 逐格画的像素图」之后，2,209 份里分出 2,022 份是真像素画。**阈值要比「存在性」更严**。
2. **中文只在两处**：给人看的 `print` 文字，和少数人拿中文当变量名。所以「语言混杂」的真实形态不是中英混排，而是**三套命名体系并存**：序号流（`a/b/c`）、拼音缩写（`anwser`/`tims`/`spe`）、点号字段（`d.h`）。三套之间没有可推断的对应关系。
3. **别把桶当标签**。每一行都在右边写了证据（链接、指令、字符串），所以打印出来的是「像什么 + 凭什么」，不是「是什么」。
"""

anchor = "\n## 16. ⚠️"
assert anchor in s, "section 16 anchor missing"
if "## 15.38" not in s:
    s = s.replace(anchor, SECTION + anchor, 1)

if "第 45 次整理" not in s:
    s = s.rstrip("\n") + (
        "\n- 第 45 次整理：给匿名的程序分桶（`tools/_label_programs.py` → "
        "`out/saves_programs.md`）。方法论：**没有名字的语料不是没用的语料，是要求你从结构里读用途**；"
        "但判类阈值要比「存在性」严（一次 `draw` 不算显示程序，一半语句是 `draw` 才算）。\n")
notes.write_text(s, encoding="utf-8")
print("notes ok")

SKILL_BLOCK = """
### 存档里的程序没有名字

`mlog` 没有名字字段（只有蓝图有 `name`/`description`）；存档里唯一的名字是地图名。判用途靠三个信号：
**链接名**（默认是方块名+序号）、**指令直方图**（`draw`=显示 / `ubind`=单位 / `control config`=物流 / `setrule`=世界规则）、
**代码里的字符串**（`print` 出去给人看的那一两段字）。按这三样分桶的现成结果在 `out/saves_programs.md`。
"""

for path in [HERE / "mindustry-blueprint" / "SKILL.md",
             HERE / ".dsh" / "skills" / "mlog-agentskill" / "SKILL.md"]:
    t = path.read_text(encoding="utf-8")
    if "存档里的程序没有名字" in t:
        print(f"{path.name}: already there")
        continue
    marker = "\n## 参考数据"
    if marker in t:
        t = t.replace(marker, SKILL_BLOCK + marker, 1)
    else:
        t = t.rstrip("\n") + "\n" + SKILL_BLOCK
    path.write_text(t, encoding="utf-8")
    print(f"{path}: ok")
