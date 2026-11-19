# 常驻世界后端重构

更新：2026-11-19。范围：`world_server.py`、客户端/MCP 契约和生成技能包。当前为阶段性重构，启动装配与完整联机验收尚未完成。提交信息以 Git 记录为准。

## 当前模块

| 模块 | 职责 |
| --- | --- |
| `world_protocol.py` | JSON 行 TCP 服务、TSV 解析、单位表格；显式注入分派器 |
| `world_process.py` | JVM、stdout 缓冲、进程退出、Windows job 与管道/日志回收 |
| `world_channel.py` | 串行控制台、JS 文件结果、文本输入输出和启动等待 |
| `world_queries.py` | 状态、地图、玩家、单位、建筑和处理器逻辑查询 |
| `world_edits.py` | 放置、清除、生成/清理单位、清理建筑、逻辑写入 |
| `world_maps.py` | 默认不踢人的换图、硬重置与加载结果检测 |
| `world_schematics.py` | 蓝图放置、导出、列表；目录与审计显式传入 |
| `world_scenes.py` | feed 读取、场景装载、世界尺寸缓存与布局计算 |
| `world_projection.py` | 投影导演循环；通过显式 services 调用世界动作 |
| `world_projection_actions.py` | 投影启停和每世界/槽位状态 |
| `world_display.py` | 日志板、渲染去重、边界 marker |
| `world_mirrors.py` | 单位镜像、feed 监听、代次检查、停止清扫 |
| `world_doors.py` | 门登记/持久化/重载、交互分派与清空 |

`World` 继承进程管理能力并组合控制通道；保留游戏启动步骤。`world_server` 继续导出原有函数和脚本名称，客户端命令及 MCP schema 未变。业务模块不反向导入启动模块。

## 修复与行为边界

- 启动失败（包括 `SystemExit`）统一清理；关闭可重复调用，等待进程退出，必要时强制结束，回收 Windows job、管道和日志。清理失败记录在 `cleanup_errors`，不遮蔽原启动异常。
- stdout pump 异常设置 EOF 并通知等待者。
- JS 结果持续不可读时按预算报超时，并附近期 stdout，不再返回空成功；轮询使用单调时钟。
- 无场景文件、仅投影单位影子时也初始化锚点，修复 `ax/ay` 未赋值。
- 日志板使用世界对象的数据目录；查询/编辑/蓝图/门的目录与审计依赖显式传入。
- 默认 reset 仍走 nextmap/gameover；只有 hard reset 才 stop/host。单位镜像保留安装前后两次代次检查与停止时两次清扫。

## 验证记录

- 原有 feed、文本通道、MCP schema 和协议测试通过。
- 新增 58 项无 JVM/真实 TCP 契约，覆盖模块独立性、生命周期、并发隔离、错误返回、文件通道、查询/编辑/地图/蓝图、布局、投影启动和槽位状态、显示、镜像、门持久化。
- `python gate.py --only world`：14/14 门禁通过。
- 两个生成技能包均通过 50 项工具回归、sidecar 契约及新增 World 契约。
- 关键查询/编辑/蓝图结果、审计参数和脚本与提交前比对；feed/布局和镜像函数逻辑保持一致。
- 真 v160.7 JVM 在 `out/_world_tests` 的独立临时目录验证无地图启动、控制台、并发 JS、中文/引号/反斜杠文件载荷、JS 错误与恢复、正常退出和资源回收。
- 源码清单与差异格式检查通过。本次 World 阶段没有宣称重新执行整仓 `--full` 验收。

本机 Java 不适合在系统临时目录写配置，真 JVM 验证采用项目内临时目录。测试未切换现有世界地图或修改其目录/握手文件。完整联机投影、门和显示尚未验收。

## 剩余事项

1. 迁移事件记录读取：chat/chat_log/messages、push/agent_push、changes 及事件安装脚本。
2. 整理剩余控制分派：tap、arm、frames、projection/projstat/sblog、mirror/marker、scene/scene_probe、通用控制台/JS/存档命令。
3. 统一操作注册和显式依赖，收敛仍由 `world_server` 装配的投影/显示服务。
4. 将目录、握手文件、审计、启动配置与 CLI 收敛到明确的运行期/装配层，保留兼容入口。
5. 执行整仓门禁、隔离世界端到端和发布解包验收，记录环境跳过项后再考虑进一步收缩兼容层。

下一项优先迁移事件读取，随后处理场景控制分派；不继续无边界地新增小模块。
