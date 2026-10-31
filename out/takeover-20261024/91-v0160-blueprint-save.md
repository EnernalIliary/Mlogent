# 91 · v0.16.0：框选存成原版蓝图（B1）+ 签名 payload v2（B3）

用户要求：m08460「开工吧 注意签名token也被用于挂载注释，不要冲突。」、m08781「可以，框选存蓝图可以尽量调用原版保存蓝图的接口。」

## 1. B1：框选 → 原版蓝图

全部走原版接口，不自己拼 `.msch`：

1. `Vars.schematics.create(x, y, x2, y2)`（`Mindustry-Source/core/src/mindustry/game/Schematics.java:377`）——
   逐格 `world.build` 后 `new Stile(realBlock, tileX+offsetX, tileY+offsetY, config, rotation)`。
   **`config` 就是 LogicBlock 的代码**，所以处理器逻辑随蓝图走，不需要额外载体。
2. `s.tags.put("name", nm)` —— `Schematic.name()` 读 `tags.get("name")`；不写会一路存成 `unknown.msch`
   （`Schematics.add` 用 `Strings.sanitizeFilename(s.name())` 找文件）。
3. `Vars.schematics.add(s)`（`:347`）—— 找文件、`write`、`schematic.file = file`、`checkLoadout`、`all.sort()`。
4. **回读 `all()` 校验** —— `add()` 与 `create()` 里出异常只 `ui.showException`，不抛，凭返回值判成功等于没验。

入口两处：作业管理窗底栏「存成蓝图」（作用于当前框选框）、工作区详情「存成蓝图」（作用于该工作区 bounds）。
无头环境 `Vars.schematics` 是 null，先守住回「蓝图接口不可用」（探针 `maiBlueprintSaveProbe` 钉住）。

## 2. B3：上下文进签名，但不破坏注释载体

签名值槽原本就装着注释 payload（`encode_comments`）。v0.16.0 把它升级成带版本的容器：

- 无 meta：**仍写 v1 裸数组** `[[line,stmt,text],…]`，老签名老代码照读。
- 有 meta：写 `{"v":2,"c":[[line,stmt,text],…],"m":{ws,name,prompt,job}}`。
- `meta` **不参与** `_hash(author, body)`，所以加它不改作业 id、不失效旧签名；
  重签（`force=True`）时 `meta is None` 就沿用旧 meta，不会把上下文弄丢。
- `meta_of_job(job)` 从 `job['workspace']` 取 id/name、从 `desc` 取 prompt（截 160）、带上 `job['id']`；
  值一律过 `_meta_text()`（引号/反斜杠→`'`、控制字符→空格、压空白），因为它最终要进 mlog 字符串字面量。

`tools/jobqueue.py` 的 `_materialize(job, out, job_id)` 用它签发，于是**写进处理器的代码自带工作区上下文**。

## 3. 验证

| 项 | 结果 |
|---|---|
| `node --check` | 0 |
| `tests/run_tests.py` | 46/46 |
| `tests/mlogauxiliary/run_ui_smoke.py` | EXIT=0（`MAIBP:probeblueprint:蓝图接口不可用`；五条新红线钉住 create/tags.put/add/回读） |
| `tests/logicd/run_logicd_tests.py` | `logicd OK`（improve 8 项，含签名里解出 `ws`） |
| 门禁 | 见下方本轮结果 |
| 断言表 | L2-84，实数 143 条（L1 31 / L2 84 / L3 6 / L4 4 / S 18） |

## 4. 还没做（下一步）

- B2：蓝图页底栏「MAI 对话」入口。
- B4：「详细」页「继续对话」—— 反射取 `SchematicsDialog.info` 的 `SchematicInfoDialog`，
  按 `title` 文本变化重挂按钮，从 `t.config` 的签名 payload v2 读回上下文。
