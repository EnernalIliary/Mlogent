# §76 打包安装即用（v0.13.0，工具链；模组与 sidecar 版本未变）

日期：2026-10-31。对应清单第 ④ 项（用户 m02047 批准的顺序最后一项，m02776「来，打包」）。
改动提交见 `git log`；本轮**没有**改 `MlogAuxiliary/scripts/main.js`，模组仍是 0.13.0，sidecar 仍是 0.12.9。

## §76.1 为什么

「安装」在此之前是两处手拷：`MlogAuxiliary/` 进 `saves/mods`，再从**仓库**里开一个 `python tools/logicd.py`
窗口。仓库外的玩家拿不到这个过程，而当时唯一的「包」`out/_dist/MlogAuxiliary.zip`（77,236 B）只压了模组
文件夹 —— 模组是前端，没有 sidecar 它只会说「连不上 sidecar」。也就是说，那个包从来没有真的可用过。

## §76.2 包里有什么

`python tools/package.py` → `out/_dist/MAI-0.13.0/`（63 个文件、677,274 B）与 `MAI-0.13.0.zip`
（235,177 B，sha256 `F4FB9B2E…`）。`out/_dist/` 不入 git（`.gitignore` 的 `/dist/` 是另一批对外导出）。

| 包内路径 | 来源 | 作用 |
|---|---|---|
| `mod/MlogAuxiliary/{mod.hjson,scripts/main.js,README.md}` | 仓库同名文件逐字节 | 模组本体 |
| `sidecar/logicd.py` + 5 个模块 | `tools/` 闭包 | 逻辑后端（`logicd`/`mlogcheck`/`rule_ids`/`msch`/`jobqueue`/`mlogprovider`） |
| `sidecar/*.json`（5 个） | `tools/` | `block_sizes`/`content_names`/`instr_semantics`/`sensor_attrs`/`status_names` |
| `sidecar/rules/*.json`（40 个） | `rules/` | findings 的规则 id（`rule_ids.py` 从 `parents[:4]` 往上找 `rules/`） |
| `install.ps1` / `uninstall.ps1` / `stop-sidecar.ps1` | `packaging/` | 装/卸/停后端 |
| `安装.bat` / `卸载.bat` / `启动逻辑后端.bat` / `停止逻辑后端.bat` | `packaging/` | 双击入口（纯 ASCII） |
| `使用说明.md` / `VERSION.txt` | `packaging/` + 生成 | 三步上手 + 每个文件的 SHA256 与两边版本 |

玩家三步：解压到有写权限的目录 → 双击 `安装.bat` → 双击 `启动逻辑后端.bat` 留窗口。`启动逻辑后端.bat 8899`
可换端口，端口被占会拒绝启动而不是叠第二个。

## §76.3 三个坑（都是「看起来成功」的那一类）

1. **`rule_ids` 是函数内导入，行首正则漏了它。** 第一版闭包用 `^from\s+(\w+)\s+import` 扫源码，而
   `tools/logicd.py` 是在 `_rid()` 里 `from rule_ids import rule_id`、`tools/mlogcheck.py` 同样在函数里导入。
   于是包少了 `sidecar/rule_ids.py`：`/health` 照样 200、`/capabilities` 照样 200，只有 `/analyze` 会在玩家
   机器上 `ModuleNotFoundError`。现在闭包走 `ast.walk`（`tools/package.py` 的 `local_imports()`），并且验证
   改成**行为级**——解包后真起 sidecar 打一次 `/analyze`（见 §76.4）。发现它的线索很土：模块数报 5，而
   `grep -c rule_ids tools/*.py` 说有两个模块在用它。
2. **存档目录不是猜的，是 `Vars.loadSettings()` 定的。** 第一版探测把 `%APPDATA%\Mindustry` 排在前面，
   实测装到了 `C:\Users\…\AppData\Roaming\Mindustry\saves\mods`，而游戏读的是
   `E:\Program Files (x86)\Steam\steamapps\common\Mindustry\saves\mods`。原因在
   `Mindustry-Source/core/src/mindustry/Vars.java:494-495`：
   `if(steam || Version.isSteam){ settings.setDataDirectory(Core.files.local("saves/")); }`
   —— **Steam 版的存档目录在游戏目录旁边**，只有非 Steam 版才用 `%APPDATA%\Mindustry`。所以探测顺序改成
   「先找有 `saves\` 的游戏目录，再退 `%APPDATA%`」，`uninstall.ps1` 同序（否则删错目录还报成功）。
   装错的那份已从 `%APPDATA%` 删掉，`saves\mods` 现在只剩 `MlogAuxiliary`。
3. **`.ps1` 少了 UTF-8 BOM 就变乱码。** 我用编辑器回写 `install.ps1` 时把 BOM 弄丢了，PowerShell 5.1 就按
   ANSI（本机 GBK）解码，安装照样成功、但中文全成 `鍚姩閫昏緫鍚庣`。已恢复 BOM，并把「每个 `.ps1` 必须有
   BOM、每个 `.bat` 必须是纯 ASCII」写成测试断言（`tests/packaging/run_pack_tests.py` 第 6 组）。

## §76.4 验证

- `python tools/package.py --verify` → PASS：闭包齐、`/health` 0.12.9、`/capabilities` 7 keys、
  `/analyze` 2 条语句 0 ERR、`install.ps1` 逐字节一致、`uninstall.ps1` 删净。
- `tests/packaging/run_pack_tests.py`（新增，进 `gate.py` 的 `package` 步）→ 9 组全绿：闭包 6 模块 + 5 数据
  文件 + 40 规则、模组三文件与仓库逐字节、`VERSION.txt` 覆盖 `layout()` 每个文件、包内 sidecar 服务
  `/health` + `/analyze`、`install.ps1`/`uninstall.ps1` 往返、**探测顺序两条**（有 Steam 目录时选 Steam、
  没有时退 `%APPDATA%`）、编码（3 个 `.ps1` 有 BOM、4 个 `.bat` 纯 ASCII）、zip 无 `__pycache__`/`.pyc`。
- `out/_pack_e2e.py`（临时，玩家路径）→ PASS：真 zip 解压后 `启动逻辑后端.bat 8899` 起得来、`/health` 0.12.9、
  `taskkill` 后 bat 打印 `sidecar exited` 并退出、忙端口 8765 拒绝启动、`安装.bat`/`卸载.bat` 往返、zip 无垃圾。
  **`停止逻辑后端.bat` 只做源码断言没有真跑**：它会杀掉所有命令行含 `logicd.py` 的 python，而当时机器上正
  跑着玩家自己的 sidecar（pid 51388，8765）。
- 正式装机：`out/_dist/MAI-0.13.0/安装.bat` 双击路径装到
  `E:\Program Files (x86)\Steam\steamapps\common\Mindustry\saves\mods\MlogAuxiliary`，`main.js` sha256
  `515CFBD0B5D00CE776E42C4F368C67E9366A95EF1BA25B7B0643B7A83F97F2E4` 与仓库一致；两份测试产生的
  `.bak-*` 已删。
- `python gate.py --full --kb-build` 见提交前的最后一轮。

## §76.5 边界与没做

- 非 Steam 版（itch/standalone）只做了「退到 `%APPDATA%`」这条路径的模拟测试，没有真机验证。
- 安装器只认四个常见 Steam 库位置（`Program Files (x86)\Steam`、`Program Files\Steam`、`SteamLibrary`、
  `Steam`，C..H 盘）；装在别处的玩家要手动 `-Target`。
- `停止逻辑后端.bat` 会杀掉机器上**所有**命令行含 `logicd.py` 的 python（对单人玩家是对的，对同时在跑两个
  sidecar 的人不是），未提供按端口过滤。
- sidecar 的 API 密钥仍存在游戏 `Core.settings` 里、由模组推给 sidecar；包里不含密钥，换机器要重填。
