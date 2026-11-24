# Mlogent

[English](README.md) · **简体中文**

[项目网站与配置引导](https://mcp.iliary.life/?lang=zh) · [使用示例](https://mcp.iliary.life/?lang=zh#examples)

Mlogent 是一套 Mindustry 逻辑和蓝图工具。它能从复杂蓝图里取出指定处理器的 mlog，
恢复可读的跳转标签，检查并替换代码，再输出可以粘回游戏的蓝图。也可以用 Mindustry
执行器跑测试、查看指令轨迹，或通过 MCP 把这些操作交给编辑器和代码助理。

电网调试支持原版电网与外部供电曲线。MCP `mlog_sim` 使用 `power: "grid"` 或
`power_profile` 可以验证电池备用、欠电和恢复供电。参数与逐 tick 对照范围见
[电网说明](tools/README.md#电网--power-grid)。

世处脚本可通过 MCP `mlog_sim` 的 `marker_preview` 返回指定 tick 的 marker 状态和 PNG。
也可以先用 `marker_from_svg` 将简单 SVG 转为世处 Mlog，再运行预览。
[单帧预览](tools/README.md#世处-marker-单帧预览) · [静态 SVG 转换](tools/README.md#静态-svg-转世处-marker)

世处调试可以用 `mlog_sim.world_probe` 查看指定 tick 后的地格、建筑、任务旗标和地图规则，
并检查读数是否符合预期。
[地图状态检查](tools/README.md#世处地图状态检查)

在线调试世界支持读取带标签源码、源码哈希、处理器类型、`@ipt` 和链接目标，按 revision
安全修改单台处理器，写后回读并生成可回滚快照。

## 快速开始

需要 Python 3.11 或更新版本。静态检查、蓝图解析和生成不需要安装 Python 第三方包，也不需要 Java。

```bash
git clone https://github.com/EnernalIliary/Mlogent.git
cd Mlogent
python tools/mlog.py doctor
python tools/mlog.py gen --logic "print 42" --name demo --binary demo.msch
python tools/mlog.py check demo.msch --cost
python tools/mlog.py extract-logic demo.msch -o demo-extracted.mlog
```

`gen` 会为出图代码签名。标签会在交付时转成数字跳转，标签名随签名载荷保存，下次提取时可恢复。
`gen` 也会在终端返回蓝图粘贴码。

## 编辑已有蓝图

```bash
python tools/mlog.py parse demo.msch --labelize
python tools/mlog.py extract-logic demo.msch --index 0 -o processor.mlog
python tools/mlog.py extract-logic demo.msch --all --out-dir extracted
```

`extract-logic` 接受 `.msch` 文件、蓝图粘贴码或 `.mlog` 文件，也支持用 `-` 读标准输入。
处理器索引从 0 开始。多处理器蓝图要用 `--index` 选一段，或用 `--all` 全部导出。

要把改好的代码放回原蓝图，用下方的 MCP 流程。它只替换选中处理器的代码，保留链接、其他方块和蓝图配置。

## MCP

本地客户端可用 stdio 启动服务：

```bash
python tools/mlog_mcp.py
```

远程客户端使用 HTTP `/mcp`。部署方式、鉴权、运行时和版本回滚见 [MCP 部署](docs/MCP部署.md)。

公开 MCP 接入地址：`https://mcp.iliary.life/mcp`。
游戏内输入 `/mcp` 可弹出打开项目网站的确认窗口；服务端控制台使用 `mcpguide` 查看文字说明。

| 任务 | 工具 |
| --- | --- |
| 找到要修改的代码 | `mlog_extract` 接受蓝图粘贴码或工作区文件。多处理器时可先列出索引、坐标、链接和注释预览。 |
| 预览并应用改动 | `mlog_inject` 传 `preview: true` 查看差异、静态诊断和链接检查。确认后传回 `expected_sha256` 作为版本保护，获取新蓝图粘贴码与 `revision`。 |
| 查阅或回退 | `mlog_revision` 可查原代码与检查结果。回退时用当前蓝图核对生成版本，匹配后返回原粘贴码。 |
| 检查与调试 | `mlog_check`、`mlog_validate`、`mlog_sim`、`mlog_trace`。轨迹可按标签和变量筛选，并和另一条轨迹比较。 |
| 查机制和指令 | `mlog_kb` 可在包含知识库的部署包里检索，长结果用 `mlog_fetch` 读取。 |

MCP 的接口版本可在 HTTP `/health` 或初始化响应查看。线上部署应保留上一份可回滚的产物，
并把蓝图版本目录放到持久存储。实时游戏世界使用独立的 `tools/world_mcp.py` 入口。

## 模拟与 Mindcode

- **运行 mlog**需要 Mindustry 服务端 jar 和 Java 21+。可用 `MLOGSIM_JAR`、`MLOGSIM_JAVA` 指定环境。
  `python tools/mlogsim.py program.mlog --ticks 120`。模拟结果的适用范围见 [观察与差分](docs/观察与差分-契约.md)。
- **编译 Mindcode**需要 Mindcode jar 和兼容的 Java。默认优先选择已验证的 Mindcode 3.19.3，
  可用 `MINDCODE_JAR`、`MINDCODE_JAVA` 指定。先用 `python tools/mindcode.py doctor` 检查环境。
- **部分反编译**可用 `python tools/mindcode.py decompile program.mlog -o draft.mnd`，
  或用 `extract-logic --format mindcode` 直接从蓝图提取。结果是编辑草稿，其中的跳转通常要重写成循环或条件才能重新编译。
  见 [Mindcode 集成](docs/Mindcode集成.md)。

## 下载与开发

[GitHub Releases](https://github.com/EnernalIliary/Mlogent/releases) 提供四类压缩包：

| 包 | 用途 |
| --- | --- |
| `toolchain` | 本地 CLI、规则、测试和文档 |
| `knowledge` | Mindustry 机制、数据表和验证证据 |
| `skills` | 两份可独立安装的 DSH 技能，随包提供生成的工具 |
| `mcp` | MCP 服务、知识库和部署配置 |

每份 Release 附 `SHA256SUMS.txt`。发布包不含游戏或 Mindcode 的 Java 运行时。
Codex 从仓库的 `.agents/skills/` 发现项目技能；DSH 技能发布包从同一份根目录工具自动打包。

```bash
python gate.py
python tools/check_manifest.py
python tools/build_skills.py --verify-only
```

缺少可选运行时的测试会在门禁中标为跳过。更多入口见 [工具手册](tools/README.md)、[文档索引](docs/README.md)
和 [变更记录](CHANGELOG.md)。项目采用 [MIT 许可](LICENSE)。


## 语言支持

项目网站与授权页支持简体中文和英文，可根据浏览器语言选择。网站也可使用语言切换入口。

在线游戏服的 Mlogent 提示按客户端语言选择；中文使用简体中文，其他语言回退英文。使用 `/language zh`、`/language en`、`/language auto` 设置 Mlogent 提示语言；Wayzer 命令另用 `/lang zh` 或 `/lang en`。地图名称和第三方地图脚本不自动翻译，部分插件菜单仍包含硬编码中文。
