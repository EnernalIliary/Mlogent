# tools/ 索引

日常只有两个入口：`mlog.py`（解析/检查/生成蓝图与逻辑）和 `mlogsim.py`（拿真执行器跑逻辑：默认官方 **v160.7** server jar `out/_server160.jar`；`MLOGSIM_JAR` 可切 `_server159.jar` / `_server146.jar`，见 `mlogsim.py:116-122`。注意数据表的 `source:` 仍写 v159.3 —— 那是数据表来源版本，不是模拟器版本）。
其余文件是它们的数据、分析层和一次性维护脚本。

环境：先跑 `python tools/mlog.py doctor`。静态分析（check/ir/values/pack/cross/report）**全部只用 Python 标准库**；只有 `kb.py` 的本地知识库检索要 `fastembed`（仓库根 `requirements.txt`）；模拟器要 Java 21 + server jar。全部可覆盖的环境变量见仓库根 `.env.example`。

## 常用命令

| 想做什么 | 命令 |
|---|---|
| 看蓝图里的逻辑 | `python tools/mlog.py parse 图.msch` |
| 静态检查 | `python tools/mlog.py check x.mlog`（`--cost` 加成本/最坏指令数，`--rid` 每行尾部显示规则 id） |
| 生成只含处理器的蓝图 | `python tools/mlog.py gen --name 名字 --code x.mlog` |
| 模拟运行 | `python tools/mlogsim.py x.mlog --ticks 120 --trace t.csv` |
| 调试着陆台（真 4×4 接收台，带水/卸货） | `python tools/mlogsim.py x.mlog --ticks 1200 --pads 9 --pad-drain 2 --units flare:1 --core-items copper:400` |
| 把仿真画进真世界（状态镜） | `python tools/mlogsim.py x.mlog --units poly:8 --ticks 240 --push out/_world/mirror.json --push-every 15`，服务端用 `--mirror-feed out/_world/mirror.json` 启动 |
| 超大场景（几千台）跑模拟 | `python tools/mlogsim.py 图.msch --ticks 110 --js-timeout 3600`（默认预算 180 s，几万台会把一条 js 命令跑到几分钟） |
| 一次启动跑多个文件 | `python tools/mlogsim.py a.mlog b.mlog c.mlog --ticks 60` |
| 预热模拟器（预处理时先起） | `python tools/mlogsim.py --daemon` → `python tools/mlogsim.py --remote x.mlog --ticks 60` |
| 值域 / 跳转表 | `python tools/mlog.py ranges x.mlog --var n`；`python tools/mlog.py jumps x.mlog --var n` |
| 指令级执行流 | `python tools/mlogsim.py x.mlog --ticks 120 --itrace t.tsv --itrace-var n` |
| 把数字跳转换成标签，方便编辑 | `python tools/mlog.py labelize x.mlog`（输出 `x.labels.mlog`；签名文件会先把注释还原到正文） |
| 交付前把标签转回行号并签名 | `python tools/mlog.py post x.labels.mlog -o x.mlog`（`#` 注释打包进签名 token） |
| 看/取回签名里的注释 | `python tools/aigenerated.py extract x.mlog` / `restore x.mlog`（按原始行号与语句锚点） |
| 这个程序需要哪些世界符号 | `python tools/mlog_needs.py 图.msch` |
| 整批存档里的逻辑 | `python tools/mlog.py map <存档目录>` |
| 规则逐条审计 | `python tools/review.py md` |
| 本地知识库（向量+可选重排） | `python tools/kb.py search "read @this 怎么写" -k 6` |
| MCP 服务（模型直接调用工具） | `python tools/mlog_mcp.py`（stdio，见下节） |
| 自检工具链 | `python tools/mlog.py selftest`（`--jobs N` 分片）；`python tests/run_tests.py` |
| 调试世界契约 | `python tests/world/run_world_tests.py`（feed 读取 / 文本通道 / 43 个 MCP 工具的 schema 与协议，不需要 JVM） |

`mlog.py --help` 是子命令总表；`tools/mlogsim.py --help` 是模拟器参数（世界、单位、战斗 tick、trace/assert）。

### 着陆台（`--pads N`）

`--pads 9` 在处理器周围放 9 台真 `landing-pad`（4×4），按序接成 link 0..8（名字 `pad1..pad9`），每 tick 记一次落地，结束时打印
`PAD <名字> <x> <y> cfg= <物品> arriving= <在途物品> cd= <冷却> items= <库存> water= <水> eff= <效率> landings= <落地次数>`
（`--json` 里是 `rec["pads"]`）。默认每 tick 把水箱补满，`--no-pad-refill` 才能看到"两次落地后水空、eff=0"的真实供给约束；`--pad-drain N` 每 tick 从台里抽 N 件货（模拟输出物流，台子空仓才会再落）。

两个不修就调不通的坑（都由 --pads 自动处理）：
- **多格建筑是按中心对齐放置的**：`Tile.setBlock` 的偏移是 `-(size-1)/2`（Tile.java:255-288），4×4 台摆 origin 会覆盖处理器格 → 处理器 `isValid()` 变假 → 程序里所有 `read x @this <名字>` 恒 null（而 `sensor @this @type` 仍正常，很容易误判）。模拟器现在按居中矩形做避让。
- **`LandingPad.config()` 在沙盒里被 `accessible()` 静默拒绝**（LandingPad.java:73-77、:160-163）：非战役非编辑器世界 `accessible()=false`，`control config` 不报错但 cfg 一直 null。`--pads` 会打开 `rules.allowEditWorldProcessors`（唯一不改变消耗语义的 accessible 分支）。

## 大场景 / 长跑：`--js-timeout` 与分批装载

- **一条 `js` 命令 = 一次墙钟预算**。场景模式把「摆方块 + 配置 + 整个 tick 循环 + 回收变量」全塞进一条命令，默认预算 180 s（`Server.js_timeout`，`Server.wait_for` 超时抛 `SimError("timeout waiting for ...")`）。台数一多必然超：d=64 的 3,758 台跑 120 tick 实测 **1,010 s**，不调预算就只会看到 `r*` 全 null。
- 调法：CLI `--js-timeout SEC`（float，默认 180），库方式 `srv.js_timeout = 3600`。**只影响等待上限，不影响语义**；测试仍 50/50。
- **第二条墙是单条命令的体积**。场景 JSON 里每条处理器都带全文代码，d=128（22,278 台 × ~850 行）拼成一条命令约 700 MB，GraalJS 会直接 `NullPointerException: ... FieldOrMethodRef.getType() because "m" is null`。解法是**分批装载**：先按批 `setBlock` 全部方块，再按批 `b.updateCode()` 并累积到全局 `procs`，最后单独发循环命令。参考实现 `out/_scratch/tfprobe3/_wpe_batch.py`（d=128 装载 50 s、2 tick 3 s）。
- 回收变量时注意：`srv.js()` 返回的是**已去掉 `[none/base.js]:` 前缀**的行，直接喂 `parse_results`；拿 `srv.all` 会因时间戳前缀匹配不到。

## 模拟器 JS 控制台 API（`mlogsim.Server`）

库方式驱动模拟器时，`srv.js(src)` 里的代码跑在游戏进程内（GraalJS），返回它 `print` 出来的行。手工摆方块/刷单位有三件套必须补，否则容易得到「单位没死 / ubind 绑不到」的假结论：

1. `Vars.state.rules.unitCap = 1000;` —— 空白世界没有核心，`Units.getCap()` 是 0，**每个单位在 `add()` 里就被移除**（这是历史「落地即死」的来源，跟 spawn 落点无关）。
2. `Vars.state.rules.logicUnitControl = true;` —— 处理器 `ubind` / `ucontrol` 控制单位的前提。
3. 刷完单位后 `Vars.state.teams.updateTeamStats();` —— 暂停的世界不会自己跑 team 统计，不调这一步 `ubind` 看到的是空。

读取式（GraalJS 里字段和方法不通用，写错会抛 `EcmaError: ... is not a function`）：

| 写法 | 说明 |
|---|---|
| `Groups.unit.size()` | 方法，不是属性 |
| `U.dead` / `U.health` / `U.x` / `U.y` / `U.valid` | 属性，不要加 `()` |
| `U.isValid()` | 方法 |
| `T.block()` / `T.floor()` | 方法 |
| `T.build` | 属性，可能为 null |

最小可复现示例（存成 `out/_assert_runs/tmp_probe.py`，能打印 SPAWN 行就说明环境通了）：

```python
import os, sys
sys.path.insert(0, "tools")
import mlogsim

srv = mlogsim.Server(os.path.abspath("out/jre21/jdk-21.0.5+11-jre/bin/java.exe"),
                     os.path.abspath("out/_server160.jar"), 64)
try:
    print(srv.js('''
        Vars.state.rules.unitCap = 1000;
        Vars.state.rules.logicUnitControl = true;
        var UT=null;
        for(var i=0;i<Vars.content.units().size;i++){var u=Vars.content.units().get(i); if(u.name=="dagger") UT=u;}
        var U=UT.spawn(Packages.mindustry.game.Team.sharded, 30*8+4, 30*8+4);
        Vars.state.teams.updateTeamStats();
        print("SPAWN\\t"+U.id+"\\tvalid="+U.isValid()+"\\tdead="+U.dead+"\\thp="+U.health);
    '''))
finally:
    srv.close()
```

输出 `['SPAWN\t210\tvalid=true\tdead=false\thp=150']`（`capacity` 调大后 spawn 才成立；不调 `unitCap` 时这一行会抛 `CountUnitException` 或单位数恒 0）。

- `srv.js(script)` 用 "undefined" 当结束哨兵（`tools/mlogsim.py:300-311`）：**脚本最后一条必须是语句**，不要以赋值/对象字面量这类「有返回值的表达式」结尾，否则控制台打印的是返回值（例如 `true`），`js()` 会一直等到超时。要调试输出就在末尾 `print(...)`，或写成 `var x = ...;`。
- `Server(java, jar, ...)` 的 java/jar 建议传绝对路径：Java 子进程的 cwd 是 `out/_sim/run-*`，相对路径会按**调用方** cwd 解析（本版本已内置 `_abs_path`，见 `tools/mlogsim.py`）。
- 坑：`sensor dead @unit @dead` 在 `@unit` 为 null 时读到 **1**（见 `docs/验证记录.md` L2-02），拿 `dead=1` 判「单位死了」不可靠，先判 `@unit` 非 null。
- 自写 JS 驱动推进逻辑必须照 `mlogsim.py:854-869`（`itr_exec`）的写法：先 `obj.accumulator += obj.block.instructionsPerTick`，再 `while(obj.accumulator >= 1){ obj.executor.runOnce(); obj.accumulator -= 1; }`。**只调 `b.updateTile()` 不会推进指令流**（它只重建方块、把 team 拷进去），ipt 也不进累加器 —— 症状是「逻辑一条都没跑」的中断器计数始终为 0。
- `LINK_ALIASES`（`mlogsim.py:980-995`）只有 cell / bank / message / switch / sorter / unloader / dome / projector / mender / router / junction / spectre / furnace / pad，**没有 `vault` / 容器别名**：要读容器库存（`sensor n vault1 @copper`）只能自己写 JS 摆方块再 `config`，别指望 `--links auto` 猜出 vault1。

## 子进程生命周期（孤儿 JVM）

`mlogsim.Server` 起的 Java 子进程过去会活过它的 Python 父进程：父进程被强杀（gate 超时、Ctrl-C、探针崩溃）时 Windows 不连带杀子进程，JVM 继续占着内存。曾经堆到 61 个，把机器压到 `There is insufficient memory for the Java Runtime Environment to continue`，`probes` 26 条全红。现在三道闸：

1. **Windows job object**（`KILL_ON_JOB_CLOSE`）：`Server.__init__` 把子进程放进一个属于本进程的 job，本进程无论怎么结束（包括 `taskkill /F`）内核都会带走它；实测硬杀父进程后 3 秒内子进程消失。
2. **atexit 兜底**：正常退出路径上 `_close_live_servers()` 逐个 `close()`。
3. **`close()` 幂等**：置 `_closed`、发 `exit`、`wait(15)`，超时 `kill()`；finally 里关 `stdin`/`stdout` 并释放 job 句柄。

残留清理只清我们自己的 jar（按命令行里的 `_server160.jar` / `jre21` 识别，游戏本体也跑 java.exe），且只清父进程已死的：

```bash
python tools/mlogsim.py --sweep-orphans     # orphan sweep: N stale JVM(s) 1234 5678
```

`tests/probes/run_probes.py` 跑完一轮扫一次；`tests/mlogauxiliary/run_ui_smoke.py` 退出前显式 `_close_live_servers()` —— 它以前从不 `srv.close()`，每跑一次泄漏一个 JVM。

## MCP 服务（`mlog_mcp.py`）

把检查器和模拟器直接暴露成工具，模型不用记路径、不用拼 PowerShell：

```bash
python tools/mlog_mcp.py          # stdio JSON-RPC，供 DSH / Claude Desktop 连接
```

工具（15 个）：`mlog_doctor`、`mlog_check{path,cost,limit,level}`、`mlog_ir{path}`、
`mlog_values{path}`、`mlog_gen{source|logic,name,links,blocks,out}`、
`mlog_sim{path|logic,ticks,units,save,...}`、`mindcode_compile{source|path,target,optimize,out,map}`、
`mlog_validate{path|logic|mind|mnd_path,ticks,expect,level,task,hypothesis,next_step}`、
`mlog_task{action,task_id,source,hypothesis,next_step}`、`scenario_run{path,via,level}`、
`mlog_diff{path,spec,level}`、`mlog_fidelity{action,capability,difference}`、
`mlog_observe{a,b,spec,level}`、`mlog_explore{action,template,seeds,params,modifiers,via,limit,shrink}`、
`mlog_fetch{ref,offset,limit}`。
每个工具都接受 `level: summary|diagnostics|full`，返回同一个 `mlog-eval/v1` 信封
（见 `tools/mlog_eval.py`）：默认只回 10 个键的摘要（`task` 恒在，未接任务时为 `null`），大块内容（mlog 源码、变量转储、
完整轨迹）自动换成 `artifact_ref`，用 `mlog_fetch` 取回。
模拟器在服务进程内保温，首次约 3.7 s，之后约 0.6 s。DSH 侧配置片段：

```yaml
- insert:
    - id: mcp-mlog
      name: '@deepseek-ai/dsh-mcp-client'
      config:
        serverName: mlog
        transport: stdio
        command: '<python.exe>'
        args: ['<repo>/tools/mlog_mcp.py']
```

## 联机调试世界（`world_server.py` + `world_mcp.py`）

把「一个真人玩家正在玩的 Mindustry 世界」暴露给模型：常驻的 headless 服务端负责世界，
MCP 外壳只做翻译，所以 MCP 随会话重启时玩家不会掉线。详见 `docs/联机调试世界.md`。

```powershell
python tools/world_server.py --map Fork        # 起世界（前台；关掉即散场）
python tools/world_client.py status            # 不开 MCP 也能问
python tools/world_client.py units --radius 40 --x 149 --y 204
python tools/world_mcp.py                      # stdio JSON-RPC，供 DSH 连接
```

工具（42 个）：`world_status`、`world_players`、`world_units`（`format:"table"` 出对齐表）、`world_unit`（按 id）、`world_changes`（建筑变更日志，`since` 增量）、`world_buildings`、`world_building`（查单格）、`world_maps`、
`world_logic{,_code,_vars,_set}`、`world_place`、`world_clear`、`world_console`、`world_js`、
`world_chat`（读玩家聊天，`since` 增量）、`world_push`（取走管理员在游戏里打的 `/push` 消息）、`world_say`、`world_pause`、`world_save`、`world_load`、`world_start`、`world_stop`，
以及调试用的 `world_spawn`（造兵）、`world_kill_units`、`world_clear_buildings`、`world_reset`（重开图，
默认走 `nextmap`+`gameover` **不踢人**）、`world_switch_map`（换图且保住玩家连接），
还有 `world_scene` / `world_scene_probe`（铺场景文件 + 按 checks 判定变量）、`world_door`（点击门：注册/列出/清除/代按，`action=set|list|clear|enter`，默认 `kind=watch`；这个机制已废弃，只是还留着接口）、`world_taps`（谁点了哪一格），
`world_arm`（启动「放雷即投影」监听，可给多个场景）、`world_projection`（手动开关投影）、`world_projstat`（看圆心/复刻清单/feed/偏移）、
`world_frames`（多场景矩形边界：`action=list|clear|paint`，边界是一圈 `ShapeMarker`，**不动地形**），
以及状态镜 `world_mirror_state`（给一组单位状态直接画 marker）、`world_mirror_feed`（盯住 mlogsim `--push` 写的 JSON 文件实时重画），
还有文本日志板 `world_sblog`（`action=log|list|clear`：每块沙盘一块 `TextMarker` 面板，写 feed 龄 / 投影状态 / 建筑数 / 单位数 / 最近事件）。

投影出来的处理器是 **`enabled=false`** 的模型（真跑逻辑的是仿真进程）；它的代码与 sorter 配置由
`scene.py` 的 `configureAny(LogicBlock.compress(...))` 广播给客户端，投影铺完还会 RESYNC 补发一遍。
每块沙盘另有一块 `TextMarker` 文本日志板（`world_sblog` 读）。细节见 `docs/联机调试世界.md` §15.7–15.8。

「把仿真画进游戏里」的完整用法（**场景自己会跟着 feed 走，不用再指一遍**）：

```powershell
# 服务端：只给 feed。场景从 feed 的 scene 字段里读，先起服务还是先起仿真都行
python tools/world_server.py --map '大肥鱼的调试世界' --watch-feed out/_proj/feed.json

# 仿真：--scene 决定复刻什么（路径会写进 feed），--rt 1 让人看得见
python tools/mlogsim.py --scene scenes/sim/sandbox-haul.json --ticks 1200 --rt 1 `
  --push out/_proj/feed.json --push-every 3
```

`mlogsim --scene X --push F` 把 X 的绝对路径与场景名写进 F（`{"scene": ..., "label": ...}`）：
只给 `--watch-feed` 时 director 按它补场景，建筑、落雷框、日志板、单位影子一起出来；
`--watch-scene` 退化成「覆盖」，只有想拿另一张场景对照同一条 feed 时才需要。
老格式 feed（没有 `scene`）仍按老行为只画影子，不会报错。

玩家在任意位置放一颗 `shock-mine` → 场景在该处复刻（建筑真放、单位只有贴图 marker）；
**把地雷拆掉 → 复刻出来的建筑（含核心）和全部 marker 一起消失**，玩家后放的方块不会被误拆。
复刻出来的处理器会 **enabled=false**（仿真在跑同一份程序，世界里再来一份会抢单位）。

多场景时用 `--watch-feed` 重复给（每条 feed 认自己带的场景），或 `--watch-scene` 重复给来覆盖；
每个场景的矩形边界用一圈小方块 marker 画出来（`world_frames`），**不铺地板**：地形一点不动，
玩家自己刷的染色地板不会被盖。雷放进哪个框就复刻哪个场景。

Agent 侧的判据与排错见 `docs/联机调试世界.md` §17；MCP 一行版是
`mlog_sim{scene, ticks, rt, project}`（返回 `projection.watch` 命令）+ `world_arm{feed}` + `world_projstat`。

两条硬规矩：**没有仿真就不画框**（feed 超过 10 s 没更新就擦掉，框本身就是"仿真在跑"的指示灯）；
**场景固定排布**（`--frame-cell` 默认 64，按格从地图左上角起排，锚点在格心），雷放框外直接拒绝。

三个必须知道的点：

- 端口大概率不是 6567 —— Windows/Hyper-V 会在动态端口段里圈走成片的端口，脚本用 `port_free()`
  （TCP+UDP 都试）探一遍、失败就从 15000 往上找，真实端口见握手与 `world_status.gamePort`。
  被圈走的端口 bind 报 **WinError 10013（拒绝访问）**，不是「占用」，但游戏客户端会把两种失败都打印成
  `Port 6567 already in use`。看圈子：`netsh interface ipv4 show excludedportrange protocol=tcp`；
  修法（管理员）：`net stop winnat` → `netsh int ipv4 set dynamicport tcp start=49152 num=16384` →
  `net start winnat`，之后 6xxx 不再被预留。`world_server.py` 自己会绕，**游戏客户端里的 Host 没有退路**。
- `world_pause` 有玩家在线时会被解除，改完世界要复核 `paused`。
- `world_js` 里没有 `Java`/`mindustry` 全局，静态方法走实例（`Vars.maps.all()`）；`tile.setBlock()` 放出来的方块是 `enabled=false` + `derelict`，要用 `world_place`。
- `Groups.build` 只收**会 update** 的方块（核心、处理器），container/传送带/墙这类 `update=false` 的根本不在里面 —— 所以 `world_buildings`/`world_logic` 改成直接扫 tile，多格建筑只在原点格报一次。

## 地图生成（`mapgen.py`）

把一张图片（或空白画布）写成 Mindustry 的**染色地板**世界，导出成任意尺寸的 `.msav`。
写档不自己实现格式：像素在 Python 侧算，落盘交给官方 headless 调它的 `SaveIO`，
所以出来的文件与游戏里「编辑器保存」完全同构（v160.7 / SaveVersion 13）。

```powershell
# 空白调试世界：128x128，8 格细网格 + 32 格主线 + 中心十字 + 中心核心
python tools/mapgen.py --size 128 --name '大肥鱼的调试世界' --preview out/map_preview.png -o maps/大肥鱼的调试世界.msav

# 图片转染色地板：按图片逐像素上色（--fit contain 留边、--resample lanczos 抗锯齿）
python tools/mapgen.py --image photo.png --size 128 --fit contain --resample lanczos --name 我的图 -o maps/my.msav
```

| 参数 | 说明 |
| --- | --- |
| `--size W` / `WxH` | 地图尺寸，默认 128x128 |
| `--image P` | 源图；省略则画空白底 + 网格 |
| `--fit stretch\|contain\|cover\|center` | 图片适配方式（默认 stretch） |
| `--resample nearest\|bilinear\|bicubic\|lanczos` | 缩放算法（像素画用 nearest） |
| `--alpha-flag 1\|0\|2` | Mindustry 的 alpha 字节：1=不与邻居混色（像素画，默认）、2=两角插值（照片更柔） |
| `--flip-y` | 图片第 0 行当地图**顶部**（默认开；Mindustry 的 y 轴朝上） |
| `--grid N` / `--major N` / `--axis` | 细网格 / 主线 / 中心十字（0 关） |
| `--ticks N` / `--tick-color` | 每 N 格网格交点打一个亮点（数格子用，默认 0 关） |
| `--rings "10,20,40"` / `--ring-color` | 以地图中心为圆心的等距圈（量交互/链接半径时读数） |
| `--core core-shard\|none` | 中心放核心（默认 core-shard；要纯图就别放） |

四个必须知道的点：

- **矿物不是地图里的**：host 一张图时 `Map.filters()` 读 `tags['genfilters']`，缺失就走 `Maps.readFilters("")` 现造 35 个默认过滤器重新撒矿。脚本固定写 `genfilters='[]'`，所以生成的地图是 100% 干净的。
- **alpha 字节是混色标志**，不是透明度；预览 PNG 会强制 alpha=255（否则看起来一片白）。
- 名字要写进 `SaveOptions.extraTags`（`writeMeta` 只写标准键），只塞 `Map` 构造器的话游戏里显示 `unknown`。
- 必须用**完整 JRE**（`out/jre21/...`）：Steam 自带的 jlink 裁剪版缺 `java.logging`，服务端起不来。

## 本地知识库（`kb.py`）

把仓库里的公开文档与工具源码切成块，存进 SQLite，检索走“向量召回 + FTS 召回 → RRF 融合”，加 `--rerank` 再走 cross-encoder。模型与索引都在本机，不进仓库。

```bash
# 首次：下载模型并建索引（约 1 分钟）
python tools/kb.py build
# 查询：默认向量+FTS+RRF（重排需显式 --rerank）
python tools/kb.py search "模拟器战斗 tick 怎么开" -k 6
python tools/kb.py search "ulocate" -k 4 --kind code --rerank
# MCP stdio 服务（给 DSH / Claude Desktop 之类用）
python tools/kb.py serve
```

- 依赖与模型：`fastembed` 装在 `out/_kblibs`，模型缓存在 `out/_kbmodels`（`BAAI/bge-small-zh-v1.5` + `BAAI/bge-reranker-base`）。首次运行前设置 `HF_ENDPOINT=https://hf-mirror.com`（国内镜像）。
- 索引：`out/_kb/kb.sqlite3`；`build` 可重复跑，重建整表。
- MCP 配置（以 DSH 的 mcp 配置为例）：

```json
{"mcpServers": {"mlog-kb": {
  "command": "python",
  "args": ["tools/kb.py", "serve"],
  "env": {"HF_ENDPOINT": "https://hf-mirror.com"}
}}}
```

- 工具名 `kb_search(query, k=6, kind="")`；`kind` 取 `doc` 或 `code`。
- **两个分数别看错**：`score` 是 RRF 融合分，算法就是名次倒数 `1/(60+rank)`，所以相邻名次
  只差百分之一二（报出来的 0.0159 / 0.0167 就是名次 60 前后的倒数，不是相关度）。
  判断「这条像不像」看 `sim` —— 那是命中块与问题的余弦相似度，0.6 以上通常真相关。
- 分块：正文 1400 字符、代码/00-data 摘要 120 字符。超长**行**按句末标点切开再硬切
  （2026-11-15 修：旧实现只在塞满后 flush，长段落单行会整行超限，实测 128 块里 84 块
  超过 1400、最长 1622；现在块长上限真的成立，最长 1396）。代码行与数据记录行不拆
  —— 那里「一行 = 一条记录」，切开等于把一条记录撕成两半。


## Mlog辅助（sidecar）

`logicd.py` 是游戏内模组 `MlogAuxiliary/` 的后端：玩家在游戏里选意图模板，模组 POST 过来，
它生成 mlog、跑全量静态检查（`mlogcheck.analyse()` + `cost_report()`）、再把代码编成
**游戏自己的** config 载荷（`msch.build_logic_data()` 与 `LogicBlock.compress()` 同一字节格式），
模组用 `build.configure(bytes)` 走原版通道写进处理器。

```
python tools/logicd.py                            # 127.0.0.1:8765（--port 0 = 随机端口，就绪行里打印）
python tools/logicd.py --print-template patrol    # 不启服务，只打一个模板的代码
python tests/logicd/run_logicd_tests.py           # 契约测试：协议 26 项 + 作业队列 12 项 + provider 9 项 + 模型档 6 项 + 真 v160.7 写入 7 项
python tests/logicd/run_logicd_tests.py --no-sim  # 只跑协议层（不需要 JRE）
```

接口十四个：`GET /health`、`GET /capabilities`、`POST /analyze`、`POST /compose`、`POST /plan`、`POST /region`、`POST /snapshot`，作业队列的三个 `POST /jobs` / `GET /jobs?id=|?state=` / `DELETE /jobs?id=`，以及模型档的三个 `GET /llm` / `POST /llm` / `POST /models`
（一句话意图 -> 选模板 + 抽参数。**模型只有这一个接入点**：把 `_route()` 换成模型调用，返回形状不变，
模组侧一行不用改，模型也就永远没办法把没检查过的 mlog 塞进存档）；
`ok` 的语义是**没有 ERR**（ERR 一律拒绝写入）。设计、契约细节、分期与「已验证/未验证」
边界写在 `docs/Mlog辅助-设计.md`，模组安装与操作写在 `MlogAuxiliary/README.md`，
P2–P5 的路线（框选 → 队列 → 模型 → 写入）在 `docs/Mlog辅助-规划.md`。
`POST /compose` 与 `POST /plan` 支持 `origin: {x, y}`（处理器的 tile 坐标，v0.4.6）：载荷里的链接坐标是
**相对处理器**的（`LogicBlock.java:65-69` 的 `readCompressed(data, true)` → `:304-307` `x += tileX()`），
而模组读到的 `LogicLink.x/y` 是绝对坐标（`:102`），所以带链接的请求必须把处理器位置一起发过来；
`origin` 不是对象时返回 400，不传则原样透传（视作已经是相对坐标，老调用方不受影响）。

`POST /region` 是给游戏内**区域快照**用的（v0.4.2，F7）：模组把鼠标周围一片区域读成
`{grid[], processors[{x,y,block,code,links[]}]}` 交给它，它只回**每个处理器能连哪些方块、链接名该叫什么**
（`candidates[{name,block,x,y,dist,used}]`），**不生成代码、不写文件**。距离与命名的依据全在游戏源码：
`LogicBlock.range = 8*10`（`LogicBlock.java:49`）、`other.within(this, range + other.block.size*tilesize/2f)`
（`:736`）、`getLinkName`（`:123-135`）、`findLinkName`（`:331-360`）；`tools/mschgen.py:547` 的
`link_name_for()` 是同一套规则，测试拿 `tools/block_sizes.json` 全表 446 个方块做零漂移比对。

`POST /snapshot` 是**落盘**入口（v0.4.8 起，F3 拖拽框选；v0.5.0 起 F3 是**按住式左键**，按下即拉框、松开即出快照）：模组把 `regionSnapshot()` 的结果原样发来，
它校验 `schema == 1`、`bounds` 四个整数字段后写成 `out/snapshots/snap-<YYYYmmdd-HHMMSS>-<sha1 前 8>.json`
（`indent=1, sort_keys=True`，同一份快照写两次会因时间戳不同得到两个文件，这是故意的：留时间线），
返回 `{ok, path, bytes, bounds, cells, processors}`，`path` 是相对仓库根的正斜杠路径。
校验失败一律 400（非对象 / `schema` 不是 1 / 没有 `bounds` / bound 是浮点）——**不落盘半成品**。

`POST /jobs` 是**作业队列**入口（P4 第一刀，`tools/jobqueue.py`）：模组把「一句话 + 框选快照」当作业发来，
它入队、由 worker 生成代码、跑与门禁同一套分析，只有干净的程序才会进入 `done`。job 契约与状态机照
`docs/Mlog辅助-规划.md` §4.1：`{id: sha1(snapshot+desc+mode)[:16], created, state, mode, desc, snapshot,
attempts, findings[], code, explanation, assumptions[]}`，状态 `queued -> running -> done|rejected|failed|cancelled`；
**每次跃迁先写 `<jobs-dir>/<id>.json`**（tmp + `os.replace`，重启时把残留的 `running` 放回 `queued` 且 attempts 保留 = 双写可续）。
`POST /jobs` 同 body 二次提交在**上一次还在飞**时幂等（回 `created: false`）；上一次已终态后同 body 起新跑
`<id>-2`、`<id>-3`…（带 `retry_of` 指回首轮，v0.12.2）；`GET /jobs?id=` 查一个、`?state=` 过滤（不带 state 只回未完成）；
**模型思考（v0.12.4）**：provider 回包里的 `reasoning_content` 会作为 `reasoning` 存进 job（上限 20000 字符），模组面板在状态行下面直接摊开——推理模型想歪或者把预算花在想上时，这是唯一能看出「为什么」的地方；
**空白回复要自己说明白（v0.12.6）**：`_why_blank(doc, budget)` 现在把「用了多少预算」和「是不是被截断」写进消息（`budget=16000 tokens` + `the model ran out of room mid-thought`）——重试期间的作业文件里只有这一行能分清「模型想太久被截断」和「端点拒绝服务」。
**历史与在飞（v0.12.5）**：不带参数的 `GET /jobs` 只答在飞（queued/running），作业管理窗要的是「发生过什么」，所以加 `?all=1`（`limit` 默认 50、夹在 1..200）：`Queue.history()` 按 `(created, id)` 降序回全部作业，并用 `job_brief()` 剥掉 `snapshot`/`code`/`bytes_b64`/`reasoning`/`links`/`assumptions`（列表每秒拉一次，不能几十 KB 地拖）。`SIDECAR_VERSION` 随之是 `0.12.5`——改过 `tools/logicd.py` 记得重启那个进程，`GET /health` 的 `version` 是唯一能确认的方法；
`DELETE /jobs?id=` 取消（running 也能取消，worker 在检查点退出）。
**为什么要拆掉「一律幂等」（v0.12.2）**：`id` 是 `sha1(snapshot+desc+mode)[:16]`，内容寻址。把已终态的作业也当成
「同 body 已答过」，等于让一条死在 `provider-error: empty reply` 的作业永久占住这句话——玩家把端点修好、原地再点一次
「生成」，拿回来的还是那条 `empty reply`，模型根本不会再被问一次，看起来就是「修了没用」。现在只有 queued/running
占着 id（`jobqueue._free_id()`，上限 `RETRY_MAX = 99` 轮顺延），失败的那次照样留在盘上可对比，模组不用改也不用重装。
同版还修了两处写盘薄弱点（`jobqueue.py`）：`Store.save()` 对 `PermissionError`/WinError 5·32·33 这类「文件刚被别人
占了一下」的冲突重试 `SAVE_TRIES = 6` 次（Windows + OneDrive 目录下实测会撞），`_loop()` 兜底 `_strand()` 把仍然写不下去
的作业落成 `failed` + `worker-error`，不再让它永久停在 `running`——面板上「不动」和「还在跑」玩家分不出来。
**门禁比分析器更严**：`mlogcheck` 对「形似链接名但处理器没有这个链接」只给 WARN（人可能还没接完线），
但作业是机器输出直接写进处理器，所以 `jobqueue.FATAL_RIDS = ('link-name-not-bound',)` 把这一条**提升为 ERR**：
最多 3 次尝试（1 + 2 次 self-repair，第二次起把 findings 当提示回给 provider），仍不过就 `rejected` 且 `code == ""`——绝不写入。
v0.9.0 起 `links` 的 `[]` 与 `null` 不再等价：`[]` 是**权威空表**（处理器确实没接任何链接，链接名判据照查），
`null` 是「模组读不到链接表」（判据跳过）；模组侧用 `linkListOrNull()` 发这个区别，`jobqueue._materialize()` 原样保留。
provider 是唯一接模型的缝（P4 第三刀，`tools/mlogprovider.py`）：默认 `template`（就是上面的 `/plan` 意图路由，全离线可跑）；
`--jobs-provider fake --fake-provider FILE` 喂固定答案；`--jobs-provider llm` 才是真模型，两种入口：
`--llm-url URL [--llm-model NAME] [--llm-key-env VAR] [--llm-timeout N] [--llm-max-tokens N]` 走 OpenAI 兼容的 `/chat/completions`（只用标准库，
key 从环境变量读、绝不出现在命令行），或 `--llm-replay FILE` 回放录制好的回复（离线测试/回归都走这条）。
`--llm-record FILE` 会把每次的 `{prompt, reply}` 追加成 JSONL，真跑一次就得到可回放的脚本。
prompt 是规划 §4.4 的三段：**世界事实**（处理器坐标 + 快照摘要 + 附近方块 + 链接名白名单，`links: null` 写「UNKNOWN」、`[]` 写「EMPTY」）、
**规则摘要**（mlog 语法与 v160 要点、必须有 end、任何 ERR 即拒）、**任务与 JSON 契约**（锚定档 `{template, params, explanation}` /
自由档 `{code, explanation, assumptions, needs_links}`）；self-repair 时把上一轮的 findings 逐条附在任务段后面。
回复用 `parse_reply()` 解析：容忍 markdown 围栏和前后散文（只取第一个配平的 `{...}`），字段类型不对就抛 `ProviderError`、作业按失败重试；
`needs_links` 里出现白名单外的名字，`jobqueue` 直接判 `link-name-not-bound` ERR 并拒绝——不等分析器发现。
锚定档还有一个兜底（v0.9.2）：模板写进代码的链接名（如 `message1`）如果处理器上没有、但**同族**的链接在
（`message2`、`display3`……），`compose()` 会按到处理器的距离挑最近的那个替换进去，并给一条
`template-link-substituted` INFO 说明换成了谁——不是静默改，也不再直接 `template-needs-link` 拒绝。
同族全都没有才报 ERR（判据在 `tools/logicd.py` 的 `_nearest_link()`，`message1` 不会误伤 `message10`）。
模组侧（v0.8.0）已接：F4 面板投作业 + 每秒 `GET /jobs?id=` 轮询 + 完成/拒绝渲染 + 取消按钮，
`--jobs-dir` 换队列目录（默认 `out/jobs`，或 `$MLOG_JOBS_DIR`），`--jobs-drain` 跑完就退（一次性批处理）。


**模型档可以在游戏里配**（v0.11.0）：设置 → Mlog辅助 → 大模型 里填 地址 / 密钥 / 模型，
模组只把它们发给本机 sidecar，由 sidecar 在进程里把 `provider` 换成 `mlogprovider.HttpProvider` ——
**不用重启 sidecar**，也不用改命令行。三个端点：

- `GET /llm` → `{ok, kind: llm|template|fake, url, model, key_set, key_hint, timeout, max_tokens}`。
  **密钥只进不出**：只回 `key_set` 与掩码尾巴（`******1234`），明文永不出现在任何响应里。
- `POST /llm` body `{url, model, key, timeout, max_tokens}` 切到模型档（`url` 必须是 http(s)，否则 400；
  `timeout` 5–600 秒；`max_tokens` 64–64000，缺省沿用当前值）；body `{kind: "template"}` 切回离线模板档。
- `POST /models` body `{url, key}` → `{ok, url, models: [id...], count}`：从
  `/chat/completions` 推导出 `/models`（`/completions`、`/responses` 同理；已经是 `/models` 就原样），
  GET 时带 `Authorization: Bearer`，解析 `data[].id|name` 或 `models[]`。
  **必须由 sidecar 代取**：模组侧是裸 `java.net.Socket` 手写的 HTTP/1.1，只有明文 HTTP，没有 TLS。

- `POST /llm/probe` body `{url, model, key, timeout}`（缺省用现存配置）→ 一次最小 chat
  调用，回 `{ok, url, model, status, error, raw, raw_len, finish_reason, content,
  content_len, message_keys, reasoning_len, usage}`。**给玩家用的自测**：作业路径只会说
  `empty reply` / `HTTP 404`，这个端点把端点到底回了什么摊开（v0.12.1）。
  同一版起 `POST /llm` 与 `/llm/probe` 都会把「只填到 API base」的地址补成
  `/chat/completions`（`completion_url()`），模组开面板时还会用 `Core.settings` 里的
  设置把重启后丢失的模型档重新推给 sidecar。

**回复预算（v0.12.3）**：推理模型先把 `reasoning_content` 想满、再写 `content`，两者共用 `max_tokens`，
预算偏小时回复不是短而是**空的**（真机取证：`finish_reason=length`、`completion_tokens` 正好 1600、`prompt_tokens` 502、
`content` 空、`reasoning_content` 满）。所以默认预算 4096（上限不是目标，写完就停）、
`HttpProvider` 见到 `finish_reason=length` 就自动升一档重试一次（×4、封顶 16000、超时同档放宽），
仍然不够就把 `--llm-max-tokens` 写进错误里；`/llm/probe` 的预算也从 128 提到 512 起 ——
128 对推理模型连一个 JSON 都写不完，自测会给你假阴性。

`--jobs-provider llm --llm-url ...` 仍然可用：启动时把命令行参数灌进同一份 `LLM_STATE`，
游戏里再改就以游戏里为准。`GET /llm` 只反映**进程内存里**的档位，重启 sidecar 回到命令行参数。

**改过 `tools/logicd.py` 必须重启那个进程**（v0.9.1）：模组连的是**已经加载进内存**的 Python 进程，
磁盘上改了代码它不知道。症状很一致：面板回「投递失败：no such endpoint: /jobs」，而 `GET /health` 依然是 200——
老进程没有新路由，但健康检查从第一版就有。**v0.12.3 起 `GET /health` 直接回 `{ok, protocol, version}`**，
一眼就能看出跑的是不是新进程（不再需要比对启动时间）。排查一行就够：
`Get-CimInstance Win32_Process -Filter "Name='python.exe'"` 里命令行含 `logicd` 的那个进程，
**启动时间早于改动时间**就是它；`Stop-Process -Id <pid> -Force` 后再 `python tools/logicd.py --port 8765`。
模组侧（v0.9.1 起）`jobWhy()` 会把 `no such endpoint` 翻成「sidecar 进程是旧版本 → 关掉旧的再重新启动」，
不再只把一句英文丢给玩家。
**所有 HTTP 入口都是异步的**（v0.4.3 修）：`httpJson()` 把结果用 `Core.app.post(...)` 投递回主线程，
所以主线程上的「同步等待」永远等不到 —— 控制台命令与 F7 热键都跑在主线程，early 版本在这里 busy-wait，
拿到的只是字面量 `pending`（症状：F7 弹出「sidecar 不可用（）」）。现在的写法是发出去就返回、处理放进回调；
`run_ui_smoke.py` 的源码红线禁止 `while(x === "pending")` 这类自旋。

**传输层是裸 socket**（v0.4.4 修）：不能用 `java.net.URL.openConnection()` —— 它交回的是内部类
`sun.net.www.protocol.http.HttpURLConnection`，`java.base` 没 export，Rhino 按运行期类绑成员（`rhino.MemberBox`），
`setRequestMethod` / `getResponseCode` / `getInputStream` 一律抛 `IllegalAccessException`。现在 `httpRaw()` 用
`java.net.Socket` 手写 HTTP/1.1（`Connection: close` + 可选 `Content-Length`，响应读到 EOF；sidecar 是
`BaseHTTPRequestHandler`，默认 HTTP/1.0，不 chunked 不 keep-alive）。控制台多了 `maiHttpRaw()` 方便在游戏里定位。

**写 `MlogAuxiliary/scripts/main.js` 的两个禁区**（真 v160.7 的 Rhino 编译期 bug，都表现为「整段脚本静默不执行」，
因为 `Scripts.runConsole` 把异常当返回值）：①`finally` 体里再嵌 `try/catch` ⇒ `arraycopy: last source index ...`；
②某些正则字面量（实测 `/^HTTP\/1\.[01] (\d{3})/`）⇒ `FAILED ASSERTION: invalid bytecode`。两条都在
`tests/mlogauxiliary/run_ui_smoke.py` 有源码红线（禁 `}finally{`、禁 `openConnection(`）。

### 游戏内快检（P2）

游戏里没有 Python，所以「这行指令存在吗 / 要更新版本吗 / 这个名字是链接吗」这类
**单行 + 一张表**就能定的事实由 `MlogAuxiliary/scripts/quickcheck.js` 在游戏内回答。
它的规则表 `MlogAuxiliary/scripts/rules.generated.js` 是**生成的**，不是手抄的：

```
python tools/rules_export.py            # 从 instr_semantics.json + mlogcheck 重新生成
python tools/rules_export.py --check    # 磁盘上的文件与生成结果不一致 -> exit 1（gate 跑这个）
python tests/mlogauxiliary/run_quickcheck_tests.py   # 14 个用例 + require 契约 + 不误报交叉验证
python tests/mlogauxiliary/run_rhino_parity.py       # 同一批用例在真 v160.7 的 Rhino 里重跑，与 node 逐条比对（无 JRE 则 SKIP）
python tests/mlogauxiliary/run_ui_smoke.py           # 整个 main.js 在真引擎里初始化 + 让模组把设置表格造到一张假 Table 上（无 JRE 则 SKIP）
```

**为什么需要第 4 条**：真 Rhino（v160.7）里 `"abc def".split(/\s+/)` 会按每个字符切开
—— 带 `+` 量词的正则在它的 `split` 里等价于空匹配，只有单字符/无量化模式正常。
node 用的是 V8，14 个用例全绿也照样带着这个 bug 进游戏，所以快检的分词/裁剪/标识符判断
一律手写扫描（不碰 `split(正则)`），并且每个用例都要在真引擎里再对一遍。

### 设置界面（v0.3）

模组自己的调试入口不再是控制台命令，而是**设置 → Mlog辅助**一栏（`Vars.ui.settings.addCategory`，
`SettingsMenuDialog.java:329-330`；分类只在显示设置菜单时 rebuild，所以脚本加载时机不影响它出现）。
这一栏直接列出：版本 / 游戏构建 / 快检模块是否加载（指令、op 版本门、链接槽各几条）/ sidecar 地址与上次探测结果 / 
**数据目录与 mods 目录**，并给出「连接测试」「复制诊断」「AI 辅助编程」「模板面板」「快检鼠标下的处理器」「打印诊断」「重新注册分类」「审查状态」几组按钮。
控制台还留了退路：`maiDiag()` / `maiSelfTest()`。鼠标指向处理器按 **F7** 看周围 10 格的链接候选（v0.4.2）；
**F2** 打开全图处理器清单（v0.7.0：一行一个 `@x,y 行数 ERR/WARN`，问题多的排前面，点一行跳相机并开 F4 面板，
底部「复制清单」把同样的文本放进剪贴板；无 UI 时 `maiList()` / `maiListRows()` 是退路）。
**v0.8.1 起 F4 并入 F3**：单格按住 F3 点一下处理器 = 开这台处理器的 AI 面板（原来 F4 做的事），
拖出矩形才是区域快照；F4 键仍然能用，只是不再需要记。

**为什么需要第 5 条测试**：无头模拟器里 `Vars.ui` 是 null（`Vars.java:209/332`），真界面没法验，
但**整段 main.js 的初始化**可以验 —— `run_ui_smoke.py` 按 `Mods.loadScripts` 的方式把 main.js 灌进真 v160.7 
的脚本作用域，然后调 `maiSelfTest()` 让模组把设置表格建到一张假 Table 上。第一版就栽在这里：挂控制台函数后读回
写成 `scope.get(k, scope)`，真引擎报 `Cannot find function get in object [object global]`，初始化在「规则表已加载」
之后整个中止 —— node 侧全绿也照样是半装状态。现在的读回改用静态 `ScriptableObject.getProperty`，失败也不算错。

**第二个坑是 Java 重载歧义**（v0.3.1 修掉）：真 v160.7 里 `Table.table(function)`、`scrollPane` 这类容器回调
在方法**解析阶段**就抛 `InternalError: The choice of Java method arc.scene.ui.layout.Table.table ... is ambiguous`，
而假表只是 JS 对象，看不出这一点 —— 于是设置分类整个注册失败、游戏里根本没有那一栏，异常还被 `catch` 吞掉。
现在设置页**一律平铺加行**（`t.button(...)` / `t.labelWrap(...)` / `t.field(...)`，这些实测能解析，只是 headless 下
skin 为 null）。`run_ui_smoke.py` 也因此多了一道探针：`maiSelfTest()` 报出**页面实际用到的 Table/Cell 方法名**，
测试拿这些名字去真引擎里逐个调用，`ambiguous` / `Cannot find function` 一律 FAIL；同时源码级拦
`.table(function)` / `.scrollPane(function)`。改设置页布局先跑这条测试。

**第三个坑是 `pane()` 交回来的不是 Table**（v0.4.1 修掉）：`Table.pane(Cons<Table>)` 返回 `Cell<ScrollPane>`
（Arc `Table.java:295/311`），把 `.get()` 的返回值当表用，点按钮时就是 `TypeError: Cannot find function add in
object ScrollPane` —— 而且 `clear()` 还在（`Group.java:357` 有 clear，add 是 `addChild(Element)`，`Group.java:251`），
所以崩在第二句。正确写法：自己造 `new Table()` 交给 `pane(host)`（Element 重载）托管，之后只往 host 里加东西；
`run_ui_smoke.py` 现在会在真引擎里断言 ScrollPane 上没有 `add`，源码级拦 `.pane(function` 与 `.pane(...).get()`。

**第四个坑是「读不到」被当成「没有」**（v0.4.7 修掉）：审查栏要拿处理器的链接名去喂快检，而链接表挂在
`LogicDialog.executor` 上 —— 这个字段是**包私有**（真 v160.7 反射实测可见性 `executor:pkg`），Rhino 只暴露 public
成员，所以 `L.executor` 读出来是 `undefined`，取 `.build` 抛 TypeError 被 `catch` 吞掉，`linkNames()` 退回空数组，
快检就把每个链接槽都判成「没链接」（用户看到的就是「有链接也报无链接」）。现在 `logicExecutor()` 用
`Class.forName("mindustry.logic.LogicDialog")` + `getDeclaredField("executor")` + `setAccessible(true)` 读，并且
`linkNames()` 读不到时返回 `null`（不是 `[]`）：快检收到 `null` 整段跳过链接槽判据、`stats.linkKnown` 记成 false，
统计行显示「链接 ?（读不到处理器）」。**空数组和「不知道」在数据流上必须分开**，否则「少报」会变成「瞎报」。

审查行内箭头（v0.4.7）也是覆盖层：`Table.cells` 是私有字段（`Table.java:35`），插不进原版语句行，所以铺一张
`Touchable.childrenOnly`（`arc/scene/event/Touchable.java`）的 Table 在 `LCanvas.statements` 的父容器上，箭头用
`addChild` 手动摆位、`host.update()` 每帧按 `finding.line -> statements.getChildren().get(line-1)` 重算
（`x = statements.x + e.x - 18` 优先进行左侧空白，`y = statements.y + e.y + h - 19 - 8` 取表头行中心，表头高 38）；
`run_ui_smoke.py` 的 `arrow_probe()` 在真引擎里建 4 行假 statements + `pack()`，按公式逐箭头核位置/颜色/条数。
顺带一个无头环境的坑：`Table.add(CharSequence)` 要 Label 样式（`Core.scene.getStyle`），无头时 `Core.scene` 是 null
⇒ 测试里只能用 `Image` 当孩子，不能写 `t.add('x')`（这条和「设置页平铺」那节是同一个原因）。

五条判据：未知指令 / 子命令拼错（整行变 NoopI）/ 版本门（`min_build` 大于当前 build）/
链接名未绑定 / 语句数超 1000。**它只许少报，不许瞎报**：测试里用 `mlogcheck.analyse()`
做单向包含验证 —— quickcheck 说是断链的行，全量检查必须也这么说。未赋值变量的槽位分级、
成本 CFG、值域这些需要数据流推理的判据**不在游戏内**，仍然只由 sidecar 回答。

游戏只执行 `scripts/main.js`（`Mods.java:809`），其它脚本文件靠 `require()` 进来
（`Scripts.java:30-32` 装了 CommonJS 模块提供器）—— v160.7 实测 `typeof require` 是函数。


## 评估信封（`mlog_eval.py`）

所有工具对外的「结果」是同一个结构，而不是各自拍脑袋的 dict。Agent 拿到的永远是
`ok / stage / failure_type / message / levels / next_steps`，深浅由 `level` 决定：

| level | 内容 | 典型用量 |
|---|---|---|
| `summary` | 9 个键：`schema ok stage failure_type message level levels next_steps elapsed_ms`（外加 `*_ref` 引用） | 每轮默认 |
| `diagnostics` | 再加 `diagnostics`（逐条发现/断言失败）与 `artifacts` | 要看为什么失败 |
| `full` | 再加 `trace`（逐 tick 变量轨迹） | 复现疑难 |

失败原因走**封闭词表**（`compilation_error`、`static_analysis_error`、`runtime_error`、
`assertion_failed`、`timeout`、`unsupported_environment`、`simulation_real_difference`），
`ok=False` 却不给类型会直接抛 `ValueError` —— 「未分类的失败」是这套东西要防的头号问题。

`levels` 是四个成功维度（`execution` / `static` / `simulation` / `real_runtime`）：
`true` 是通过、`false` 是失败、**`null` 是没跑**。「执行器跑完了」不等于「程序写对了」。

```bash
python tools/mlog_eval.py selftest        # 22 项契约自检
python tests/eval/run_eval_tests.py       # 信封/裁剪/断言流水线
```

## Mindcode 编译前端（`mindcode.py`）

把 `.mnd`（Mindcode 高级语言）编成 mlog，然后照常走静态检查与仿真。详见
`docs/Mindcode集成.md`；一句话：**默认 3.19.3，因为最新的 3.21.0 在本机 `cm` 会永久挂住**
（更新检查里 dev.dirs 的 PowerShell 子进程互锁，doctor 用真编译冒烟能测出来）。

```bash
python tools/mindcode.py version           # 定位 jar/java
python tools/mindcode.py doctor --json     # 候选表 + 兼容性 + 冒烟编译
python tools/mindcode.py compile demo.mnd -o demo.mlog --target 7.0
python tests/mindcode/run_mindcode_tests.py   # exit 3 = 本机没有可用编译器
```

jar/JRE 走 `MINDCODE_JAR` / `MINDCODE_JAVA`；默认落点 `out/_mindcode/`（gitignored）。
注意 3.19.3 要 **Java 22+**，仓库自带的 JRE 21 装不了它。

## 任务进度（`taskstate.py`）

一条流水线跑三遍最容易亏在哪儿：第一遍编译、静态、仿真都过了，改一行又从头来，
而且第二遍失败时没人记得第一遍过了什么。`taskstate.py` 把进度落成**一个 JSON 文件**
（默认 `out/tasks/`，`$MLOG_TASK_DIR` 可改）：

```bash
python tools/taskstate.py list                     # 有哪些任务、各自到哪一步
python tools/taskstate.py show   ts-1a2b3c4d5e     # 完整记录（含 history）
python tools/taskstate.py resume ts-1a2b3c4d5e --source prog.mlog
python tools/taskstate.py clear  ts-1a2b3c4d5e
```

规划 §5 要求的六个字段是记录的主干：`task_id`、`source_version`（源码的 12 位内容哈希）、
`completed_stages`、`failed_stages`、`current_hypothesis`、`next_step`。三条语义值得记住：

- **进度属于某个版本的源码**。源码一改，旧的 `completed_stages` 降级进 `stale_stages`
  （"在另一个程序上验过"是事实，但不构成跳过工作的理由），`resume()` 会说明原因。
- **失败从不等于跳过**。`failed_stages` 里的阶段在 `resume()` 里是 `recheck`，优先于
  "下一步该跑什么"。
- **先落盘再上报**。`record()` 在信封返回之前写文件，所以中途崩掉也留得下"跑到哪儿"。

落盘复用了 `jobqueue.Store`（tmp + `os.replace` + 争用重试），没有第二套写盘逻辑。
接线只需在 `mlog_eval.evaluate(..., task=task)` 传记录，MCP 侧传 `task`/`task_id` 给
`mlog_validate` 即可，`mlog_task` 负责读、续跑与记笔记。

## 证据指针（`claims.py`）

`knowledge/08-evidence/claims.jsonl` 是 85 条断言的唯一出处，每条带一个 `src` 列表。
这些指针原来写行号（`docs/断言表.md:19`），而文档每加一段上文，行号就整体下移 ——
2026-11-18 实测 **168 个指针里 89 个已经指错**，而且没有任何东西会报错。

现在指针写成 **id 锚点**：`docs/断言表.md#L1-01` 指「首列是 L1-01 的那一行」，`a/b` 拆分
（`L2-10a`）也认。行号形式仍能读（老记录不炸），但会被**校验**而不是信任。

```bash
python tools/claims.py check          # 有指针指错就 exit 1（gate 的 claims 步）
python tools/claims.py list L2-10     # 一条 claim 解析到哪里
python tools/claims.py fix --write    # 把行号指针改写成锚点
```

`Mindustry-Source/` 这类不在本 checkout 里的源码指针只校验形状，不校验内容。

## 结果缓存（`cache.py`）

同一段程序反复问同样的问题，是这个工具链最常见的浪费：一次 `cm` 编译要起 JVM（1 秒以上），
一次静态分析扫几百行（几十毫秒），而**输入字节没变，答案就不会变**。`cache.py` 是一个
内容寻址的缓存，默认**关着**，只在你明确要的时候生效：

```bash
MLOG_CACHE=1 python tools/mlog.py check prog.mlog     # 这一次开始走缓存
python tools/cache.py stats                           # 有多少条、占多少字节
python tools/cache.py prune                           # 按 LRU 收到 4000 条 / 64 MB 内
python tools/cache.py clear static                    # 清某个命名空间
python tools/cache.py selftest
```

接线是两处，都只看输入：`mindcode.compile_source`（键 = 源码 sha256 + jar 版本 + jar mtime +
target + 是否优化）和 `mlog_eval` 的静态分析（键 = 源码 + `mlogcheck.py` 的 mtime）。因此
换 jar、换分析器、改参数都会自然失效，不需要手工清。三条约定：

- **默认关闭**。不开 `MLOG_CACHE` 时返回值与从前逐字节相同，测试永远看不到缓存命中。
- **失败也缓存，但环境类不缓存**。"没有 java" 这种下次可能好了，绝不该被记住。
- **半截文件读作未命中**：`put` 先写 `.tmp` 再 `os.replace`，读到坏的 JSON 就当没缓存并删掉。

`mlog_doctor` 会报当前是否开启、有多少条目、占多少字节——排查"为什么结果没变"先看这里。

## 场景（`scenario.py`）

一个场景 = 世界 + 程序 + 观测 + 断言，跑完给**一个判决**，而不是一堆变量：

```bash
python tools/scenario.py check scenes/scenarios/unit-control.json   # 只校验 schema
python tools/scenario.py run   scenes/scenarios/unit-control.json --level summary
python tools/scenario.py list                                       # 有哪些模板
```

模板在 `scenes/scenarios/`（`unit-control` 绑单位走位、`building-interaction` 用方块、
`processor-competition` 多处理器竞争）。MCP 侧是 `scenario_run`。

`--via world` 把同一个场景铺进活世界跑（先 `python tools/world_server.py`）。这条路和离线
仿真有四处**行为不同**，第一次跑真世界时全踩了一遍，写在这里省下一轮：

| 现象 | 原因 | 现在怎么处理 |
|---|---|---|
| 扰动报 "applied ... NOT APPLIED" | 活世界只收 `sb.append(...)` 的行，脚本里的 `print` 没人看 | 扰动脚本统一走 `MOD_say()`，运行期按 `typeof sb` 选通道 |
| 程序里的链接变量是 `null` | 代码广播走 `configureAny` → `readCompressed()` 用 `findLinkName()` **重新起名**（`core-shard` → `shard1`） | 广播后在本地按场景的名字重挂链接，再 `updateCode()` |
| 核心库存比场景写的多 | `items` 是**累加**语义，活世界里那块地本来就压着库存 | 核心先 `items.clear()` 再补（普通容器仍是累加） |
| 改了 `tools/scene.py` 不生效 | 世界服是常驻进程，启动时 `import scene` 就固定了模块 | 改完**重启世界服**（`world_client` 没有 reload op） |

```bash
python tools/scenario.py run scenes/scenarios/generated-resource-drain.json --via world --level full
```

## 差分验证（`observation.py` + `differential.py` + `fidelity.py`）

离线执行器是**真执行器 + 真单位更新**，但不是游戏：没有波次 AI、没有电网、地形碰撞只到
「B 级」。规划 §3 要求把同一个场景交给两边、**比较观察**，把差异变成有名字的边界。

三个模块分工：

| 模块 | 干什么 |
|---|---|
| `observation.py` | `mlog-observation/v1`：`summary/state/events/env` 四段，`from_scenario()` 与 `from_world()` 产出同构观察；`compare()` 四类规则（`exact`/`tolerance`/`match`/`ordered`），**禁止整体 JSON 相等** |
| `differential.py` | 一个场景跑两遍（sim + 活世界），给出差分信封；不一致是 `simulation_real_difference`，世界不可用是 `unsupported_environment` + exit 3 |
| `fidelity.py` | 15 条能力边界的判定表（verified/unverified/partial/unsupported/unknown），`annotate()` 把每条差异挂到已知边界上（`state.units[].item` 这类由指令决定的字段**不算**动理学差异） |

```bash
python tools/fidelity.py list                       # 哪些能力离线可判、哪些不可
python tools/differential.py run scenes/scenarios/unit-control.json --json
python tools/differential.py parity scenes/scenarios/unit-control.json   # 只比环境
python tools/observation.py compare a.json b.json   # 两个观察文件直接差分
```

比较规则写在 `docs/观察与差分-契约.md`（字段级容差、`"5%"` 相对容差、事件按 key 做子序列
匹配 + tick 容差）。MCP 侧：`mlog_diff` 跑一个场景的两边，`mlog_fidelity` 判一条差异属于哪个
已知边界（`action=explain` 返回 `null` = 这差异是真的），`mlog_observe` 比较两份观察文件；
`scenario_run` 的 `via=world` 走同一套。

## 基准（`benchmark.py`）

「一个 Agent 第一次上手这套工具链，能不能把一件小事做成」——用机械判据量化，而不是让它自己打分。

```bash
python tools/benchmark.py list                     # 有哪些任务
python tools/benchmark.py prompt arithmetic-constants  # 给冷启动 Agent 的题面
python tools/benchmark.py verify arithmetic-constants --file out/answer.mlog
python tools/benchmark.py record --task arithmetic-constants --success yes --tools 4 --tokens-in 1200 --tokens-out 90
python tools/benchmark.py score                    # 每个模型/主机的成功率与 token 效率
```

任务在 `bench/tasks/*.json`（`id/title/prompt/tools_hint/acceptance`），运行记录追加进
`out/benchmark/runs.jsonl`（`$MLOG_BENCH_DIR` 可改，不入库）。

**判分只认观测到的状态**，不认 Agent 的自述：

- `validate`：把答案喂给裸处理器，`--ticks N` 后读变量 / 文本缓冲；
- `static`：不跑，只让分析器说话（无 jar 的干净 checkout 也能判，CI 因此覆盖得到）；
- 检查项复用 `mlog_eval._matches`（`eq/ne/gt/ge/lt/le/contains`）与 `text_contains`。

**为什么任务都很短**：执行器的「每 tick 跑几条指令」不稳定（实测同一个循环程序
`--ticks 600` 到 n=32、`--ticks 1200` 反而停在 n=16），所以判据不能依赖循环跑完多少轮。
现成的六个任务都在几条指令内到终态，`--ticks` 只是给足预算。

已知短板（写在 `tests/benchmark` 的用例名里）：判官看的是程序变量，所以「直接把答案写进去」
也能过；要堵住得用 trace 判分，而需要 rig 的移动类任务还没发布。

## 场景扰动（`modifier.py`）

一个场景是「世界 + 程序」，扰动是**在跑的过程中**往世界里塞变化：单位瞬移/生成/死亡、
控制权整队易主、方块增删、核心缓冲加减、时间压力、规则键变更。

```bash
python tools/modifier.py list                      # 8 类可用的扰动
python tools/modifier.py show unit_movement        # 参数与约束
python tools/modifier.py plan scenes/scenarios/unit-control.json --json   # 这个场景能挂哪些
```

场景文件里写 `modifiers: [{kind, at_tick, params...}]`，`scenario.py` 按 `(at_tick, 声明序)`
稳定排序后对 sim 侧分段执行、对活世界侧在轮询里触发（真实 tick 与计划不符会写进
`artifacts.notes`）。**不适用的扰动会降级成 note 而不是让场景失败**，因为「这台机器上没有
电网」和「程序写错了」不是一回事。

参数化生成：`scenario.py generate --template unit-control --seed 7` 按种子产出可复现的场景，
障碍落点受世界尺寸与已有方块约束，同 seed 逐字节一致。

## 源码映射（`sourcemap.py`）

Mindcode **没有**指令级映射可用：`-r none|comments|passive|active` 只改日志注释（编出来的 mlog
里没有注释行），`-u source` 不打 listing，`pm --trace-execution` 只给 instruction 编号。所以这
张表是**推断**出来的，方法写在这里，读的人可以自己判断信不信：

```bash
python tools/sourcemap.py build demo.mnd            # mlog 行 -> .mnd 行
python tools/sourcemap.py show demo.mnd 3           # 第 3 行 mlog 是从哪条语句来的
python tools/sourcemap.py selftest
```

做法是**前缀编译对齐**：逐条顶层语句重编一次，用 `difflib.SequenceMatcher` 比对前后两份 mlog，
只认 `insert/replace` 段。不能假设「前缀的输出是现在的尾巴」——死代码与被折叠的表达式会让某条
语句**一条指令都不产生**，两段输出因此未必成前缀关系。由此有三条铁律：

- 块内语句（`for`/`while`/`do` 里面）**不猜**，直接标 `inside control flow`：前缀编译到那里时
  循环体还没展开，任何归因都是编的；
- 产生不了指令的语句标 `no instruction of its own (dead code or folded)`，不是「映射失败」；
- MCP 的 `mindcode_compile{map:true}` **固定 `optimize=False`** 建图：优化器正是把你想标位置的
  语句删掉的那一步，开着它对齐等于拿删干净的输出找原句。

前缀编译的代价是「每行一个编译器」——25 条语句 = 50 次（两个方向各一遍），实测 17.4 秒。所以
每条前缀的编译结果按「它之前的文本 + 工具版本（jar mtime）」记忆起来：**没改的源码重跑 0.14 秒，
改最后一行 1.5 秒**（只重编尾部）。这是内部记忆，不等 `MLOG_CACHE=1`（`cache.put(..., force=True)`），
`MLOG_CACHE=0` 可以关掉；**失败不记**——缺 JVM、超时这类失败若被记下来，下次会当成答案。

## 自动探索与失败缩减（`explore.py`）

场景能跑还不够，得知道**哪一批**会坏、坏在哪。`explore.py` 干两件事：

```bash
python tools/explore.py list                                     # 模板与参数
python tools/explore.py run --template unit-control --seeds 1-20 --save
python tools/explore.py run --seeds 1-5 --modifier-file mods.json --limit 1
python tools/explore.py shrink --seeds 7 --modifier-file mods.json --json
```

- `space()` 是**枚举**不是抽样：同一个 spec 得到同一个列表，所以「seed 7 会坏」这句话可以重放。
- `explore()` 把「跑不了」和「跑坏了」分开记：宿主不支持（没 jar/JRE）是 `skipped`，不是 failed ——
  机器的问题不是场景的问题。
- `shrink()` 用 delta debugging（`ddmin`）把失败的扰动束缩到最小，**只缩扰动、不动种子**：
  种子是这条复现的身份，边缩边换种子，报出来的案例就复现不了。每轮重验，因为两个单独无害的
  扰动可以联手致命。
- 账本落 `out/explore/<时间戳>.json`（`$MLOG_EXPLORE_DIR` 可改），`--save` 才写。

只走 `via="sim"`：探索会把运行次数乘上几十倍，而活世界只有一个服、全排在它后面。真要跑真机，
就用 `scenario.run(via="world")` 跑你挑中的那一个。

MCP 侧是 `mlog_explore`（`action=list` 看模板与旋钮，`action=run` 传 `template`+`seeds`，
`shrink=true` 顺手把第一个失败缩成最小复现）。

## 文件分层

1. **入口**：`mlog.py`（统一下发子命令）、`mlogagent.py`（`report` / `info` 一条命令跑完五层）、
   `logicd.py`（本地 sidecar：给游戏内模组 `MlogAuxiliary/` 提供 compose/analyze 的 HTTP 接口）、
   `jobqueue.py`（P4 作业队列：状态机 + 双写落盘 + 写入门禁，provider 可换，默认走模板档）、
   `mlogprovider.py`（P4 第三刀：§4.4 三段 prompt + 回复解析 + OpenAI 兼容调用 + 录制/回放，导入时不联网）、
   `rules_export.py`（把 instr_semantics.json + mlogcheck 的链接槽表导出成游戏内快检用的 JS）。
2. **分析层**：`mlogir.py`（解析/IR）、`mlogcheck.py`（静态检查）、`mlogval.py`（值域）、`mlogcross.py`（跨处理器）、`mlogpack.py`（打包配置）、`msch.py`/`mschgen.py`（蓝图容器）。
3. **模拟器**：`mlogsim.py`（真执行器驱动）、`mlog_needs.py`（扫程序需要的地图/方块/单位/全局量）。
4. **语料与存档**：`map_logic.py`（读存档）+ `parallel.py`（并行 worker）；语料挖掘、分桶、标注在 `corpus/`。
5. **规则**：`review.py`、`rule_seed.py`、`rule_capture.py`、`rule_audit.py`；规则数据在 `rules/`。
6. **数据表维护**：`*_from_source.py`、`build_cmd_index.py`、`block_sizes.py`——需要 `Mindustry-Source`，输出 JSON 已在仓库里，平时不用跑。
7. **语料流水线**（`corpus/`，低频，文档里有引用）：`analyze_logic.py`、`rank_logic.py`、`mine_idioms.py`、`check_ops.py`、`scan_all.py`、`extract_logic.py`、`label_*.py`、`sweep_*.py`、`pack_scan.py`、`typo_*.py`、`_sweep_saves.py`、`_sweep_analyse.py`、`_label_programs.py`、`_err_table.py` 等。脚本已按新位置改过路径，能直接跑。

8. **外部逻辑语料**（`corpus/`，2026-10-26 新增，需要网络，不进 gate）：三条流水线，共用 `check_corpus.py` 按 rule id 聚合。小蓝图包走 GitHub tree API，成品地图走 mindustry.top 站点（限速极狠，默认 10 s 间隔），上万文件的大仓库走整包 tarball。

   ```
   python tools/corpus/fetch_schematics.py      # 小包：GitHub tree API + raw -> logic-corpus/<owner>-<repo>/
   python tools/corpus/crawl_maps.py --search 逻辑 --search 塔防 --want 20
                                                # 站点抓 .msav -> logic-corpus/_maps/（--list-only 只刷 id）
   python tools/corpus/extract_maps.py          # 读存档 + 去重 -> logic-corpus/_maps_procs/<sha>.mlog
   python tools/corpus/fetch_repo_tarball.py --repo owner/name --dest D:/mlog-corpus --prefix anon
                                                # 大仓库：codeload tar.gz + Python tarfile -> <dest>/<prefix>-flat/ + _index.json
   python tools/corpus/classify_schematics.py [--src <别的目录>] [--dest <语料根>]
                                                # 解码 + 去重 -> <dest>/_procs/<sha>.mlog + _meta.json
   python tools/corpus/check_corpus.py                            # 蓝图：_procs
   python tools/corpus/check_corpus.py --procs _maps_procs        # 地图：_maps_procs
   python tools/corpus/check_corpus.py --procs _procs --jobs 16   # 4 万程序 / 3 千万行：16 进程 199 s（串行要 20 min）
   python tools/corpus/check_corpus.py --procs _procs --stride 37 --limit 400 --fail-on-errors
                                                 # 抽样冒烟：只跑 400 个，分析器抛异常就 exit 1（gate --full 用）
   python tools/corpus/instr_coverage.py --src <doc>/_procs --json out/_crawl/instr-coverage-anon.json
                                                 # 指令覆盖率：语料里每条 instruction/op/draw 子命令出现几次
   python tools/corpus/instr_coverage.py --src <doc>/_procs --limit 400 --baseline tests/corpus-coverage-baseline.json
                                                 # 覆盖率关：绝对值随样本漂，只钉「这批样本从不使用的指令集合」；
                                                 # 集合一变就 FAIL，要人重录基线（--write-baseline）
    python tools/corpus/precision_sheet.py --corpus logic-corpus --procs _procs --label blueprint
                                                 # 判读表：每条规则 6 条样本 + 机器旁证（名字出现次数 / 是否赋值 /
                                                 # 是否本蓝图链接名），判读栏留空交人填；--verdicts 回填 TP/FP/mixed
    python tools/corpus/precision_sheet.py --corpus D:/mlog-corpus/anon-corpus \
        --procs _procs --label anon --stride 8 --jobs 12   # 4 万程序抽样 5.5k，67 s
   python tools/mlog_needs.py <doc>/_procs --brief --no-detail --stride 10
                                                 # 世界符号清单（传感器/单位/方块/全局量）；大语料必须 --no-detail
   ```

   `logic-corpus/` 已 gitignore（可随时重抓）；三条命令都把蓝图/存档里声明的链接名传进
   `mlogcheck.analyse(links=...)`，所以 `link-name-not-bound` 这类规则在外部语料上才有意义。
   `map_site.download()` 的 `dest` 必须是 `Path`（传 `str` 报 `AttributeError`）。
   上万文件 / 上百 MB 的仓库放在**工作区外**（如 `D:/mlog-corpus`），别塞进 OneDrive 目录；
   这类仓库的**文件名多为中文，Windows 自带 `tar.exe` 会按 CP936 解码 UTF-8 文件名**（`核心入冷` → `鏍稿績鍏ュ喎`），
   不同名字撞成同一文件、只落一半且互相覆盖——必须用 Python `tarfile` 解包；
   `git clone --depth 1` 对大包也不稳（`RPC failed; curl 28 Recv failure: Connection was reset`）。

   语料还能当**回归基线**用：`python gate.py --full` 末尾有一个 `corpus` 步，
   对 4 万程序按 `--stride 37` 抽 400 个跑 `check_corpus.py --fail-on-errors`
   （约 10 s），断言「分析器在真实代码上不崩」。紧接着的 `coverage` 步用同一批样本跑
   `instr_coverage.py --limit 400 --baseline tests/corpus-coverage-baseline.json`（0.5 s），
   断言零覆盖指令集合仍是签过字的那 18 条 —— 往 `instr_semantics.json` 加一行、或样本里
   丢一条指令，集合就变，必须有人重新录基线。两步都依赖语料目录；不在 git 里，机器上没有时 SKIP，
   目录可用 `MLOG_CORPUS` 覆盖（默认 `~/mlog-corpus/anon-corpus`）。
   与语料无关的还有一个 `shapes` 步（0.1 s）：`python tests/shapes/run_shapes.py`
   断言检查器自己的**语句形状不变量**——每条规则对坏样例追加 1/2/5 个惰性 token 与行尾注释后仍必须开火，
   防的是整行锚定正则 fail-open（`op select` 那类漏洞；`--module` 可指向旧版做负向自证）。
    和语料无关的还有一个 `docsig` 步（0.2 s）：`python tests/docsig/run_docsig.py` 把五份文档里每个
    「助记符 + `<占位符>`」签名与 `tools/instr_semantics.json` 机检——占位符个数、逐槽名字、`mlog` 代码块的
    示例参数数、表头含 param 的表格列序，以及**第五项**：枚举槽里的名字必须真实存在（`ucontrol`/`draw`/`ulocate`
    第 1 槽查 `instr_semantics.json` 的 `subcommands`、`status` 第 1 槽必须是 `true`/`false` 且第 2 槽查
    `tools/status_names.json`、`sensor` 第 3 槽查 `tools/sensor_attrs.json` 的 LAccess 或 `tools/content_names.json`；
    这几槽在语义表里是枚举 token，**不可能装变量**，所以「不在表里」一定是文档错——2026-10-29 一次抓出 6 处真错：
    `sensor ... @damage`（LAccess 无此项，读 null）、`status <apply|clear>`（第一槽是布尔，写 `apply` 反而静默不生效）、
    `ulocate locate ...`（第一槽是 LLocate，非法值整条编译成 `NoopI`）、`@velX`/`@velY`（真名 `@velocityX`/`@velocityY`）。
    `--self-test` 用合成文档自证五项检查会开火。**第六项**是引用存在性：`docs/速查卡.md` 里每个
    `L\d-\d\d` 必须在 `docs/断言表.md` 里存在，且每个 `## ` 小节至少引用一个 id —— 速查卡是给人查的入口，
    指错编号比没有更糟（负向自证：把 `L9-99` 写进卡片立刻 MISMATCH）。它抓的是「文档教错语法」：
    `getblock <result> <x> <y> <layer>` 这种**数目对、顺序错**的签名（真序 `layer,result,x,y`）在旧文档里
    活了整个版本，玩家照着写就是静默错位。原理写在脚本 docstring 里：mlog 文本 token 序 = Java **字段声明序**
    （`build(LAssembler)` 的传参序与之无关）；`radar` 那种「槽位数没错、语义错」属于已知盲区，只能靠 `probes` 钉住。
    `--full` 独有的四步（`selftest` / `probes` / `corpus` / `coverage`）互不依赖——各自起 JVM、
    各写各的 `out/_bench` 文件、互不读对方输出——所以 `gate.py` 把它们**并发**跑：75 s → 44 s。
    两条长杆内部再各自并行：`probes` 每条探针一个 JVM（`run_probes.py --jobs`，默认 min(8, CPU)，41 s → 9.6 s）；
    `selftest` 用进程池把 420 个蓝图分片（`mlog.py selftest --jobs`，26 s → 5.3 s），
    并且**验证用的重建蓝图改用 deflate 级别 1**（`Blueprint(deflate_level=1)`）——级别只影响压缩耗时，
    解析回来的内容一模一样（level 9 = 0.200 s/MB，level 1 = 0.008 s/MB，这一项曾占自检 89% 的时间）；
    生成路径的默认级别仍是 9，蓝图字节与改前逐字节相同。现在 `--full` 约 **15 s**。
    `--serial` 回到串行，`--stream` 也强制串行。
    日常改完跑默认档即可（3.3 s，含 `shapes` 与 `lint`），`--full` 留给提交前/发版前。
   注意 `mlog_needs.py` 的 `programs_detail` 在大语料上是几百 MB，
   4 万程序全量跑要加 `--no-detail`，否则 JSON 慢到像挂死。

9. **一次性脚本**：`dev/`——探针、patch、调试脚本，默认被忽略，不保证能跑，不要依赖。
10. **数据 JSON**（顶层，和代码同目录）：`block_attrs`(253)、`sensor_attrs`(75)、`unit_attrs`、`instr_semantics`、`cmd_index`(86)、`wiki_block_ids`(422)、`block_sizes`(446)、`item_ids`、`status_names`、`label_rules`。

## 不要手改的副本

### 场景文件（`scene.py`，模拟器与真世界共用）

一份 JSON 描述整套台子（建筑/配置/物品/链接/代码/单位/断言），`mlogsim --scene` 和
`world_client.py scene` 都能铺，省掉「模拟器调好再手抄坐标到游戏里」这一步。

```powershell
python tools/mlogsim.py --scene scenes/v27-rig.json --scene-probe --ticks 400
python tools/world_client.py scene_probe scenes/v27-rig.json   # 铺 + 读变量判定
python tools/scene.py check scenes/v27-rig.json                # 只校验
python tools/scene.py emit --flavor sim scenes/v27-rig.json    # 看要执行什么
```

顺序固定：place → config/items → links+code → units（链接要指向已存在的建筑）。
报告带 `K` 行（执行器真实的 `getlink` 下标映射）与 `ERR` 行（声明 N 条链接只解析出 M 条），
因为不合法链接会被 `updateCode()` 丢掉并把下标往前挤，光看坐标看不出错位。
