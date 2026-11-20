---
name: mindustry-blueprint
description: 生成、解析和验证 Mindustry 蓝图（.msch 或粘贴码），编写 mlog，或查询编写所需的指令、方块与单位属性。对现有 mlog 做系统审查时优先用 mlog-agentskill。
---

# Mindustry 蓝图与 mlog

从本技能目录向上找到同时包含 `mindustry-blueprint/SKILL.md` 和 `tools/mlog.py` 的仓库根，在仓库根运行命令。这里的工具统一使用根目录 `tools/`。

- 解析蓝图（含处理器代码）用 `python tools/mlog.py parse <文件>`。生成蓝图前检查源代码，用 `python tools/mlog.py check <文件> --cost`，再用 `python tools/mlog.py gen <文件> --name <名称>`。根据交付要求验证生成物能解析。
- 查指令用 `python tools/mlog.py cmd <指令>` 或 `explain <指令>`。查方块、单位和可读属性用 `block`、`unit`、`sensor` 子命令。
- 需要验证运行行为时用 `python tools/mlogsim.py <文件> --ticks <数量>` 或会话中可用的 Mindustry 模拟工具。用 `python tools/mlog.py doctor` 排查 Java 或服务端 jar 环境。交付时区分静态检查、模拟结果与实机验证。

按需求查阅[仓库技能母本](../../../mindustry-blueprint/SKILL.md)的相关章节。需要机制解释时查[参考资料](../../../mindustry-blueprint/REFERENCE.md)，需要整体蓝图分析时查[蓝图分析手册](../../../mindustry-blueprint/BLUEPRINT-ANALYSIS.md)。
