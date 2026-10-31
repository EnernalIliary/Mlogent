# §77 v0.13.1：后端随包 + 模组自己拉起（把「第三步」去掉）

日期：2026-10-31。上一版 v0.13.0 的交付物是「一个 zip，装完双击 `安装.bat`」，
但装完还要**双击 `启动逻辑后端.bat` 留一个黑窗口**，源码检出还要**玩家自己装 Python 3**。
用户原话（m03139）：「能做即装即用吗」；给了三档方案后用户选 A（打 exe + 模组自己拉后端），
并另外要一份「改成 JS 的成本评估」（见 §77.5）。

## 77.1 为什么是 exe，而不是换成 Node

「即装即用」的唯一判据是**玩家侧零依赖**。换后端语言没用：

| 方案 | 玩家要装 | 结论 |
| --- | --- | --- |
| 现状 v0.13.0 | Python 3 + 手动开窗口 | 已废 |
| 换 Node/Deno 后端 | 还要装 Node | 只是换了个要装的东西 |
| **随包 exe + 模组拉起**（本版） | **什么都不用装** | 采用 |
| 全搬进游戏内 Rhino | 什么都不用装、连 exe 都没有 | 成本大，见 §77.5 评估书 |

## 77.2 包里多了什么

`python tools/package.py` 现在会带一个冻结的 sidecar：

```
MAI-0.13.1/
  mod/MlogAuxiliary/
    mod.hjson  README.md  scripts/main.js
    sidecar/            6 个 .py + 5 个数据表 + rules/（40 个 json）
    sidecar/bin/        logicd.exe + _internal/（100 个文件，约 2.2 MB，onedir）
  安装.bat  卸载.bat  启动逻辑后端.bat  停止逻辑后端.bat
  install.ps1  uninstall.ps1  stop-sidecar.ps1  使用说明.md  VERSION.txt
```

一共 163 个文件、18,518,357 B；zip `out/_dist/MAI-0.13.1.zip` 8,379,571 B
（v0.13.0 的包是 235,592 B —— 大了 35 倍，因为带了运行时）。

构建缓存：exe 只在「sidecar 模块 / 数据表 / 规则表有改动」时重建（`exe_sources()` 比 mtime），
缓存在 `out/_exe/`，日常改模组不会重新跑 PyInstaller。

## 77.3 三个坑（都是「看起来成功」的那一类）

1. **onefile 在这台机器上跑不起来。** onefile 会先解包到 `%TEMP%` 再从那里执行，被策略拦成
   `[PYI-xxxx:ERROR] Could not create temporary directory!`；换成 `%TEMP%` 下的另一个目录也一样，
   只有工作区内的目录能跑。**onedir 正常**：`bin/logicd.exe` + `bin/_internal/`。
   所以 `package.py` 里 `EXE_SUB = 'bin'` 并明确禁止 onefile（`verify()` 会检查 `_internal` 在不在）。
2. **`Runtime.exec` 会把路径按空格切开。** `saves\mods` 常常在 `Program Files (x86)` 下面，
   用单字符串命令行必然失败。改用 `ProcessBuilder` 的字符串数组（Rhino 里要先用
   `java.lang.reflect.Array.newInstance(String, n)` 造数组）。
3. **不重定向输出的子进程会卡死。** 模组不读子进程的 stdout，管道攒满 64 KB 后后端就卡在写日志上，
   表现为「后端随机卡住」。改成 `redirectErrorStream(true)` + `redirectOutput(sidecar.log)`。

另外，`sidecarExe()` 一开始被我写成 `Vars.mods.getMod("mods." === "" ? "" : "mlog-auxiliary")`，
是编辑时混进来的死表达式（结果虽然对，但读起来像 bug），已改成直接 `getMod("mlog-auxiliary")`。

## 77.4 验证

- `python tools/package.py` → 163 文件 / 18,518,357 B；zip 8,379,571 B。
- `python tools/package.py --verify` → **PASS**：`frozen exe 2.2 MB`、
  `started the packaged sidecar via the exe`、`sidecar 0.13.1 on port 2116`、
  `/capabilities ok (7 keys)`、`/analyze ok (2 statement(s), 0 ERR)`、install/uninstall 往返。
- `python tests/packaging/run_pack_tests.py` → **10 组全绿**：`PACK:exe 2197272 B files=100`、
  `PACK:launcher-bat exe-first`、`PACK:encoding ps1=3 bat=4`、`PACK:zip 163 entries`。
  新增断言：exe 存在且 >1 MB、`_internal` 在、`启动逻辑后端.bat` 里必须出现
  `sidecar\bin\logicd.exe` 与 `goto run_exe`、`start_sidecar` 必须报 `kind == 'exe'`。
- `python tests/mlogauxiliary/run_ui_smoke.py` → EXIT=0，新探针
  `MAISIDECAR:ok exe=none dir=none port=8765 state=idle->idle`（无头环境里没有 exe，走 `noexe` 分支不抛）。
  新增七条源码红线：`function ensureSidecar(` / `function sidecarTick(` /
  `new Packages.java.lang.ProcessBuilder(arr)` / `pb.redirectOutput(new Packages.java.io.File(` /
  `ensureSidecar();` / `sidecarTick();` / `api.maiSidecarProbe = function`。
  —— 写红线时踩了一次：`code_only` 里注释已被剥掉，所以红线不能带 `// v0.13.1` 这类行尾注释。
- `python gate.py --full --kb-build` → 17/17。

## 77.5 同时交付：JS 移植评估书

用户选 C 的第二半是「先 exe + 要一份 JS 移植的详细评估书」。已写
`docs/Mlog辅助-JS移植评估.md`（约 150 行）：现状架构、要移植的 5,640 行清单、
「换个运行时不算解法」的三条路对比、逐模块 JS 行数与人日估算（3,000–3,500 行 / 14–20 人日）、
六个真风险（Rhino 正则语义、缺 ES6 一半、性能要实测、进程生命周期、两份实现漂移、密钥与 TLS）、
三档方案（A 现状 / B 混合 / C 全搬）、六个阶段的分步路线与验收方式。

结论写在评估书开头：**短期不需要做**；v0.13.1 已经把玩家侧依赖降到零；
想要「连 exe 都没有」再上方案 B（只搬 `mlogcheck`/`msch`/`rule_ids`，8–11 人日）；
Python 那份永远不能删（它是 `gate.py` 的母本与裁判）。

## 77.6 边界（没做的）

- **模组在真游戏里拉起 exe 这一步没有实测过。** 无头引擎里 `Vars.mods` 有但包里没有 exe，
  所以只验证了「找不到 exe 时安静退回」；「找到 exe → 拉起 → 轮询到就绪」这条链在真机上要玩家重启游戏后确认
  （屏幕应依次出现「正在启动 sidecar …」与「sidecar 已就绪」，`sidecar/bin/sidecar.log` 里会有 ready 行）。
- **`停止逻辑后端.bat` 仍然只做源码断言，没有真跑** —— 它会杀掉机器上所有命令行含 `logicd.py` 的 python，
  而玩家自己的 sidecar 正在 8765 上跑。
- 包体积从 235 KB 涨到 8.4 MB（zip）/ 18.5 MB（解压）：这是带运行时的必然代价。
  如果以后在意体积，可以在打包时裁掉 `_internal` 里用不到的 Tcl/Tk 与测试模块（本次没做）。
