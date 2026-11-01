# 99 · v0.18.3：设置页瘦身、MAI 控制面板管工作区、本地快检进包

用户 `m11124` 一次提了六件事，前三件是文档/入口文案，后三件是两个「功能静默缺失」加一条质量问题。

## 一、六件事怎么落

| 用户原话 | 落点 |
|---|---|
| `mod.hjson` 作者改 `Iliary艾铭&DeepSeek`、简介改「在一次选框中创建Mlog工作区并开始VibecodeingMlog。」 | `MlogAuxiliary/mod.hjson:3-4`（行级替换；这个文件是 UTF-8 无 BOM + LF，用 `Get-Content -replace` 会把中文读成 GBK 乱码） |
| MAI 控制面板用来管理工作区，替代以前的查看页面 | `main.js` 蓝图页底栏 `MAI 控制面板` 的 handler 由 `openBlueprintPicker()` 改成 `openWorkspaceDialog()` |
| 按钮不用预览最近提示，只要显示一个复制 | 提示页只剩一颗「复制」（`hintLogCopy()`），「清空」删掉 |
| 快捷动作页、说明页毫无意义，诊断全部移动到最近提示页 | 删 `section "快捷动作"` / `"说明"` / `"本地快检"` 三段（共 2838 字符），`"最近提示"` 改名 `"诊断与最近提示"`，把 `diagParts()` 的每一行摊进去 |
| 撤销功能移入 MAI 控制面板 | `openWorkspaceDialog()` 底栏新增「撤销上次写入」（`undo()`）与「撤销快照」（`undoInfo()`） |
| 本地快检显示未加载 | 见 §二.1 |
| 运行环境的设置项显示未注册 | 见 §二.2 |

新段落序：大模型 / 聊天播报 / 框选控件 / 外观 / 写入（热键两条是 kv 行）/ 诊断与最近提示 / 运行环境。

## 二、两个真根因

1. **本地快检「未加载」**：`tools/package.py:161-185` 的 `layout()` 只拷 `('mod.hjson','README.md','scripts/main.js')`。
   而 `main.js` 自己 `require("rules.generated")` 与 `require("quickcheck")`（游戏只执行 `scripts/` 里唯一的 `.js`，
   所以规则副本必须作为独立文件发出去）。装机目录里 `scripts/` 只有 `main.js` ⇒ require 抛异常 ⇒ `RULES` 恒 null
   ⇒ 设置页永远写「未加载」。修法：`layout()` 改成 glob `scripts/*.js`；`tests/packaging/run_pack_tests.py`
   新增 2c 段，逐个文件比 sha256，并检查 `main.js` 是否真的 require 了每个非 main 的脚本。
2. **设置项「未注册」是假阴性**：`diagParts()` 用 `settingsDone` 判断，但 `selfTest()` 走的是假表路径——
   它照样会让 `buildSettingsTable()` 跑一遍，此时 `settingsDone` 还是 false。修法：新增 `SETTINGS_LIVE`，
   `buildSettingsTable()` 首行置 true、末尾置 false，判断改成 `(settingsDone || SETTINGS_LIVE)`。

## 三、验证

- `node --check MlogAuxiliary/scripts/main.js` → 0；`main.js` 324314 → 323188 字符。
- `python -X utf8 tests/mlogauxiliary/run_ui_smoke.py` → **EXIT=0**（红线新增 `SETTINGS_LIVE`、`诊断与最近提示`、
  单「复制」、`撤销上次写入`，删掉的四段用「不得出现」反向断言；段序断言同步成新顺序）。
- `python -X utf8 tests/packaging/run_pack_tests.py` → 见门禁 `package` 步。

## 四、留给真机验

1. 设置页只剩七段，提示页只有一颗「复制」；诊断行都在提示页下面。
2. 蓝图库底栏「MAI 控制面板」点开是工作区列表，底栏有「撤销上次写入」「撤销快照」。
3. 设置页「本地快检」不再是「未加载」（包里带了 `rules.generated.js` 与 `quickcheck.js`）。
4. 「运行环境 / 设置项」写「已注册」。

## 五、质量问题的取证

单独写进了 `out/takeover-20261024/98-quality-analysis.md`（teammate `quality-analyst`，只读）：
坏逻辑集中在「猜指令签名」与「数行号」两件事，而提示词本可提供规范、检查器又恰好都判 0 findings
—— 是「没给规范 × 没查语义」的乘积。R1–R5 的修法见那份报告，本轮放在 v0.18.4 做。


## 五、第二轮（2026-11-01 下午）：多格处理器去重 + 高亮缩放（用户 m11320 / m11340）

- 用户原话：「中核和超核逻辑不应该一次下发四个或九个作业。」＋澄清「中核占四格，超算占9格，在完全框选到它们时候会对同一逻辑下发多次作业，把这个bug修了」；「注意逻辑高亮也要同步缩放。」
- **根因**：`regionSnapshot` 的快照循环对多格建筑逐格 `procs.push` —— 逻辑处理器（中核）2×2 ⇒ 同一台被枚举 4 条、超核处理器 3×3 ⇒ 9 条；`openQuickJob` 每条投一单 ⇒ 完全框选一台就下发 4/9 个作业。库存早已用 `seenIds` 按建筑去重，处理器漏了同一手。
- **修复**：
  1. `regionSnapshot`：`seenProcs`（按 `bld.id`，无 id 退 `t<x>,<y>`）去重后才 push —— 工作区的处理器表也随之变成一台一行。
  2. `openQuickJob`：收集目标再按 `pb.id` 去重（安全网，防上游改回逐格）。
  3. `drawLogicHighlight`（用户 m11340「高亮同步缩放」）：`seenH` 按 `b.id` 去重，每台画**一整块**外框 `L.rect(bx - bsize*4, by - bsize*4, bsize*8, bsize*8)` —— `Building.x/y` 是几何中心、`block.size` 是格数 ⇒ 中核 16 px、超核 24 px，随建筑尺寸缩放；不再逐格画 4/9 个 8px 框。
- **验证**：`node --check` 0；ui smoke EXIT=0（红线换成 `L.rect(bx - bsize * 4, ...)` / `seenH` / `seenProcs` 三条）；门禁 17/17；打包自检 13/13。
