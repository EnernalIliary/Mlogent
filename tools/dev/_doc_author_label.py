"""Record the author-label convention in the notes and the blueprint skill."""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

SEC = """### 15.24 作者标签约定:我产出的蓝图打 `[blue]DeepSeek`

用户在自己的标签体系里新开了一类 **`[blue]DeepSeek`**,用来标记"这是 DeepSeek 做的"。
以后我用 `mschgen` 生成蓝图,`labels=` 一律写这一条:

```python
mschgen.Blueprint(name=..., description="...逻辑 by [#8abcd1]DeepSeek[]",
                  labels=["[blue]DeepSeek"])
```

已落到 `tools/gen_thorium_guard.py`(钍反防爆 v1),并配 `tools/install_thorium_guard.py`
(生成 → 断言标签与署名 → 复制进 `%APPDATA%/Mindustry/schematics` → 回读校验)。

和 ILI 的区别:ILI 是**作者身份**(谁的库),这个类是**作品来源**(谁写的逻辑);
一份蓝图可以两条都有,不冲突。
"""

ROW = ("| 第 34 次整理 | 作者标签约定:我产出的蓝图默认打 `[blue]DeepSeek`(生成器写入);"
       "钍反防爆 v1 已导入游戏目录。**作者身份和作品来源是两个维度,可以同时挂。** |")

SKILL = """## 生成蓝图时的作者标签

本仓库用 `mschgen` 生成的蓝图,`labels` 一律写 `["[blue]DeepSeek"]`
(用户标签体系里的"作品来源"类),描述末尾带 `逻辑 by [#8abcd1]DeepSeek[]`。

"""


def main() -> None:
    p = ROOT / "mlog工作笔记.md"
    s = p.read_text(encoding="utf-8")
    if "### 15.24" not in s:
        i = s.index("## 16.")
        s = s[:i] + SEC + "\n" + s[i:]
    if "第 34 次整理" not in s:
        lines = s.split("\n")
        last = max(i for i, l in enumerate(lines)
                   if l.startswith("| 第 ") and "次整理" in l)
        lines.insert(last + 1, ROW)
        s = "\n".join(lines)
    p.write_text(s, encoding="utf-8")

    q = ROOT / "mindustry-blueprint" / "SKILL.md"
    t = q.read_text(encoding="utf-8")
    if "生成蓝图时的作者标签" not in t:
        t = t.replace("## 参考数据", SKILL + "## 参考数据", 1)
        q.write_text(t, encoding="utf-8")
    print("docs updated")


if __name__ == "__main__":
    main()
