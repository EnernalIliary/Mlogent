---
name: mlog-agentskill
description: 审查或解释现有 Mindustry mlog 程序或蓝图中的处理器逻辑，定位成本、不可达代码、死存储、常量分支、可能的 null 和多处理器通信问题。
---

# 审查 Mindustry mlog

从本技能目录向上找到包含 `tools/mlogagent.py` 的仓库根，在仓库根运行 `python tools/mlogagent.py report <文件>`。按报告中的证据和影响排序，先指出值得看的位置。需要展开时，用 `python tools/mlog.py check <文件> --cost`、`ir` 或 `values`。涉及多处理器通信时保留原蓝图链接信息，再查 `cross`。

区分可证明的问题与依赖游戏状态的推断。对运行时行为需要进一步验证时，使用会话中可用的 Mindustry 模拟工具，或仓库的 `tools/mlogsim.py`，并注明实际验证范围。

需要各分析层的判读方式、误报边界和校准数据时，查阅 [mlog 审查技能母本](../../../.dsh/skills/mlog-agentskill/SKILL.md)的相关章节。本入口直接调用仓库工具，母本中的独立发布包自检适用于解包后的副本。
