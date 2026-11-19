# 常驻世界后端重构

更新：2026-11-19。范围：`world_server.py`、客户端/MCP 契约和生成技能包。路由、运行期和启动装配收敛已完成；完整联机验收尚未完成。提交信息以 Git 记录为准。

## 当前模块

| 模块 | 职责 |
| --- | --- |
| `world_protocol.py` | JSON 行 TCP 服务、TSV 解析、单位表格；显式注入分派器 |
| `world_runtime.py` | 路径与具名服务配置、TCP/后台线程/JVM 退出与握手清理 |
| `world_cli.py` | CLI 参数解析、启动装配、握手发布及退出协调 |
| `world_process.py` | JVM、stdout 缓冲、进程退出、Windows job 与管道/日志回收 |
| `world_channel.py` | 串行控制台、JS 文件结果、文本输入输出和启动等待 |
| `world_events.py` | 聊天、推送、建筑变更事件读取及安装脚本 |
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
- 新增 84 项无 JVM/真实 TCP 契约，覆盖模块独立性、生命周期、并发隔离、错误返回、文件通道、查询/编辑/地图/蓝图、布局、投影启动和槽位状态、显示、镜像、门持久化。
- `python gate.py --only world`：17/17 门禁通过。
- 两个生成技能包均通过 50 项工具回归、sidecar 契约及新增 World 契约。
- 关键查询/编辑/蓝图结果、审计参数和脚本与提交前比对；feed/布局和镜像函数逻辑保持一致。
- 真 v160.7 JVM 在 `out/_world_tests` 的独立临时目录验证无地图启动、控制台、并发 JS、中文/引号/反斜杠文件载荷、JS 错误与恢复、正常退出和资源回收。
- 整仓 `python gate.py --full`：60 项中 52 项通过、7 项跳过、1 项警告，无失败（188.4 秒）。跳过项为缺少独立项目的 quickcheck/rhinoparity/ui/package/gtb/gtbprobe，以及没有活动世界的 differential；警告为本地知识库索引旧于源码。
- 独立 toolchain ZIP 解包后，导出源码清单和全部 World 门禁通过。源码清单共 294 个文件，差异格式检查通过。

本机 Java 不适合在系统临时目录写配置，真 JVM 验证采用项目内临时目录。测试未切换现有世界地图或修改其目录/握手文件。完整联机投影、门和显示尚未验收。

## 本次收敛

- `scene/scene_probe` 执行归入场景模块，`tap` 归入门模块，通用命令归入控制通道；`OperationRouter` 校验重复注册并统一分派，保持旧操作和错误返回兼容。
- `WorldPaths` 集中目录，`World` 在启动前接收实例路径和权限策略；查询、编辑、蓝图、门、镜像与审计使用实例配置。旧全局保留为兼容默认值。
- 投影动作、导演、控制与启动工厂使用具名 frozen dataclass 服务，移除 `globals()`/`SimpleNamespace` 绑定。
- CLI 参数和启动主体迁到 `world_cli`；`world_server.main` 负责组装依赖并调用启动入口。
- `WorldRuntime` 统一关闭 TCP/JVM、停止并限时等待后台线程、清理握手，移除强制 `os._exit`。修复 `--no-projection` 未生效及 `no_push_admin` 赋值晚于启动脚本的问题。
- 新接口已用隔离真 JVM 验证显式路径、TCP ping/JS/shutdown、审计位置、正常返回及资源回收。

## 剩余工作

完整联机投影、多槽交互、门和显示仍需在实际游戏客户端验收。兼容入口和默认全局继续保留；删除前应确认调用方及弃用策略。本地知识库索引需要按需重建。本轮不继续按单条操作拆文件。
