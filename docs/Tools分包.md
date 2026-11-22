# tools 内部分包

本轮采用同仓库、同版本的内部 Python 包，现有 CLI 文件和 MCP 工具名继续保留。
无需安装 Python distribution，独立技能包仍可直接运行 `python tools/mlog.py`。

## 当前边界

- `tools/mlogent/paths.py`：从实际安装位置计算工具目录与工作区目录，不依赖当前工作目录。
- `tools/mlogent/mcp/analysis.py`：静态检查、IR、变量分析的 MCP 结果适配。
- `tools/mlogent/mcp/blueprints.py`：蓝图生成、提取、注入、预览和持久化 revision 回滚。
- `tools/mlogent/mcp/compilation.py`：Mindcode 编译、可选源码映射、编译产物和 mlog 验证流程。
- `tools/mlogent/mcp/simulation.py`：模拟参数校验、投影路径校验、worker 调用与超时回收、模拟结果与图片返回。
- `tools/mlogent/mcp/tracing.py`：trace 解析、标签过滤、分页与首次差异定位。
- `tools/mlogent/mcp/tasks.py`：任务查看、列表、恢复、备注与清理。
- `tools/mlogent/mcp/queries.py`：知识检索与模拟器能力查询。
- `tools/mlogent/mcp/experiments.py`：场景运行、差分、观测对比和探索适配。
- `tools/mlog_mcp.py`：协议路由、程序读取、artifact 缓存和进程生命周期；保留原工具函数作为委托入口。

analysis 模块通过参数接收程序读取器和 artifact 存储器，不反向导入 MCP 入口，不持有服务端缓存。
blueprints 模块通过 `BlueprintContext` 接收工具目录、工作区目录、路径校验、artifact 存储、
大小阈值和作者缓存读写。context 在每次调用时创建，复用入口持有的缓存，避免出现第二份状态。
revision 的目录环境变量和 JSON 格式保持不变，仍可跨进程读取和回滚。
compilation 模块接收 artifact 存储器和程序读取器；编译器、evaluation 和 taskstate
继续使用原实现，保留编译失败与静态检查失败的区分，以及批量验证的阶段聚合规则。
simulation 模块通过 `SimulationContext` 接收路径、输入限制、JS 超时、trace 变量校验、
worker 与 artifact 存储器。进程执行器另接收工作区、总超时和输出大小限制；入口在每次调用时
读取当前限制。HTTP 的并发控制不迁移。
模块导入不启动 JVM；`mlog_sim` 继续返回同样的文本、缓存引用和 MCP 图片内容。
tracing 通过只读回调读取与 `mlog_fetch` 相同的 artifact 缓存，锁仍由入口持有。
tasks 继续调用 taskstate，保持 `MLOG_TASK_DIR`、记录格式以及源码变化后阶段失效的规则。
queries 和 experiments 延迟加载原实现，不增加独立缓存或持久化目录。
已移除没有调用方的旧进程内模拟器缓存和 `_run_code`，模拟仅走受限 worker 流程。
检查算法暂时仍位于原模块；后续可以独立迁移，避免一次移动所有文件。

## 构建与验证

`build_skills.py` 保留原有顶层载荷，并递归复制 `tools/mlogent/` 下的 Python 和 JSON 文件，
包括 `__init__.py`。不递归收集整个 tools，防止把 dev、corpus 等开发目录带进技能载荷。
技能 manifest 使用相对于 tools 的路径，覆盖嵌套模块；仓库 manifest 也覆盖内部包。
release 的 toolchain 和 mcp 文件筛选本就覆盖 tools 子目录，skills 包通过技能构建器生成。

构建只读取 git 索引中的文件；新模块必须先 `git add`，再执行 `python tools/build_skills.py --verify-only`。
该验证会在隔离的技能目录运行原回归和 `tests/service/run_package_tests.py`。
`gate.py` 的 packages 步骤覆盖包导入、路径计算、公共 MCP 分析工具、蓝图回滚、编译诊断、
artifact 回读、模拟图片返回、worker 输出限制、trace 缓存查询、任务生命周期与观测差异回读。

## 后续迁移顺序

1. MCP 的主要领域适配已拆出；剩余 schema、协议路由、共享状态和入口包装先保留在原文件。
2. 收敛编辑态与交付态源码转换，再迁移 logic 与 blueprint 实现。
3. 迁移 simulation、world 和 knowledge；每次保留旧入口，并验证独立技能包。

不为每个目录发布独立版本，也不同时改工具 schema 或返回格式。
