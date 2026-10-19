"""Add a portability/environment section to both skills; fix mlogsearch's hardcoded path."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BP = ROOT / "mindustry-blueprint" / "SKILL.md"
AG = ROOT / ".dsh" / "skills" / "mlog-agentskill" / "SKILL.md"
SEARCH = ROOT / "mindustry-blueprint" / "tools" / "mlogsearch.py"

BP_SECTION = """## 环境要求（分享给别人之前先看这段）

**只需要 Python 3.10+ 和标准库。** 开发机是 3.12.14；全部脚本只用 `argparse base64 collections dataclasses glob hashlib json math os pathlib re shutil struct sys textwrap urllib zlib` —— 没有 numpy、没有 pandas、没有任何要 `pip install` 的东西。

两个可以独立拿走的东西：

| 拿什么 | 大小 | 能不能单独用 |
|---|---|---|
| `.dsh/skills/mlog-agentskill/` | 自带 16 个文件 + `MANIFEST.sha256` | **能**。拷到任何地方 `python tools/mlogagent.py report x.msch`，`info --verify` 自校验 |
| `mindustry-blueprint/` | 工具 + 数据 + 文档 | 能，但下面两条路径要按自己机器改 |

### 两条路径

- **游戏蓝图目录**：默认 `%APPDATA%\\Mindustry\\schematics`（即 `~/AppData/Roaming/Mindustry/schematics`）。换地方就设环境变量 `MLOG_CORPUS`，或对 `find` 传 `--corpus`。
  用到它的只有 `selftest` / `find` / `corpus` 类脚本；`parse` `check` `ir` `values` `pack` `cross` `explain` `unit` `block` `item` `gen` **都不需要游戏目录**。
- **Mindustry 源码目录**：`./Mindustry-Source`（git 忽略，约 8 MB）。只有"从源码重新生成数据表"的脚本要它：`block_ids_from_source.py`、`block_sizes.py`、`items_from_source.py`、`units_from_source.py`、`blocks_from_source.py`、`check_ops.py`。
  **日常使用完全不需要** —— 八张表都已随包提供（`block_ids.json` / `block_sizes.json` / `cmd_index.json` / `item_ids.json` / `instr_semantics.json` / `unit_attrs.json` / `block_attrs.json` / `label_rules.json`）。

### 版本与平台

- 数据表取自 **Mindustry v159.3（git `5811844`）**。游戏更新后要刷新表，就重新 clone 源码再跑上面那几个生成脚本（每个脚本头注释写了它读哪个文件）。
- **路径默认值是按 Windows 写的**。Linux/macOS 上把 `MLOG_CORPUS` 指到 `~/.local/share/Mindustry/schematics` 或 `~/Library/Application Support/Mindustry/schematics` 即可。
- **控制台要 UTF-8**：`chcp 65001`（或设 `PYTHONIOENCODING=utf-8`）。否则中文变量名和图标字形会显示成乱码 —— 那是终端在按 GBK 解码，**文件本身没问题**。
- **不需要**：Java、Mindustry 本体、网络。唯一联网的脚本是 `fetch_wiki_ids.py`（一次性抓 wiki 的方块 ID 表，结果已在仓库里）。

"""

AG_SECTION = """## 环境（这份副本可以单独拿走）

- **Python 3.10+，只用标准库**，没有第三方依赖。
- `tools/` 里 16 个文件自带齐全，`SKILL.md` 与 `MANIFEST.sha256` 一起拷走即可；`python tools/mlogagent.py info --verify` 会核对每个文件的 SHA256。
- 要分析的蓝图可以是 `.msch` 二进制、base64 文本或整个目录；**不读游戏安装目录**，只读你给的文件。
- 控制台需要 UTF-8（`chcp 65001`），否则中文变量名显示为乱码（文件本身没问题）。

"""


def main() -> None:
    # 1. blueprint skill
    t = BP.read_text(encoding="utf-8")
    assert "## 环境要求" not in t
    anchor = "## 参考数据"
    assert anchor in t
    t = t.replace(anchor, BP_SECTION + anchor, 1)
    BP.write_text(t, encoding="utf-8")
    print("blueprint SKILL:", len(t.splitlines()), "lines")

    # 2. mlog-agentskill skill
    t2 = AG.read_text(encoding="utf-8")
    assert "## 环境" not in t2
    anchor2 = "## 维护"
    assert anchor2 in t2
    t2 = t2.replace(anchor2, AG_SECTION + anchor2, 1)
    AG.write_text(t2, encoding="utf-8")
    print("mlog-agentskill SKILL:", len(t2.splitlines()), "lines")

    # 3. mlogsearch: no hardcoded user path
    s = SEARCH.read_text(encoding="utf-8")
    old = 'SCHEM = r"C:\\Users\\lliary\\AppData\\Roaming\\Mindustry\\schematics"'
    new = ('SCHEM = os.environ.get("MLOG_CORPUS") or os.path.join(\n'
           '    os.path.expanduser("~"), "AppData", "Roaming", "Mindustry", "schematics")')
    assert old in s, "hardcoded path not found"
    s = s.replace(old, new, 1)
    SEARCH.write_text(s, encoding="utf-8")
    print("mlogsearch: path now resolvable")


if __name__ == "__main__":
    main()
