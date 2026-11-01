# 97 — v0.18.2：主题色/强调色可调、选框与高亮分色、高亮贴回正中

日期：2026-11-01。用户原话（m10938）：「允许在设置中调节主题色和强调色」
「逻辑选框应用主题色，选框中的逻辑高亮应用强调色。还有逻辑高亮位置偏右上角半格。」
随后澄清（m10943）：「逻辑高亮位置现在是在它的右上角半格处，改到正中」。

## 一、三个判据

1. **两个颜色成为设置项**：`THEME_KEY = "mlogauxiliary-theme-color"`（默认 `8abcd1`）、
   `EMPH_KEY = "mlogauxiliary-emph-color"`（默认按 `Mindustry-Source/core/src/mindustry/ui/UI.java:107`
   的 `[highlight]` 算法 `Pal.accent.cpy().lerp(Color.white, 0.3f)` 现算）。
   值一律是**六位十六进制字符串**。读法：`Core.settings.get(key, null)` → `hex6()` 手写校验
   （去 `#`/空格、长度 6、逐字符判 `0-9a-f`，不用字符类正则，避开 Rhino `invalid bytecode`）。
   非法输入：输入框退回当前值 + `Vars.ui.showText` 说格式，不影响已存的值。

   **为什么不存数字**：`Arc-Source/arc-core/src/arc/Settings.java:357-359` 的
   `getFloat(name, def)` 是 `(float)get(name, def)`，JS 数字经 `put` 变成 `java.lang.Double`，
   对 `Object` 做 `(float)` 强转先当 `Float` 再拆箱 ⇒ `ClassCastException`。v0.18.1 的
   倍率「拖了不动」就是这个坑，这里直接按字符串存，不重复踩。

2. **设置页新增「外观」段**（`buildSettingsTable` 里，位置在「框选控件」之后、「写入」之前）：
   两行 `colorRow()` = 标签 + 十六进制输入框（宽 120）+ `Tex.whiteui` 色块（22×22，`setColor` 实时刷新）
   + 「默认」按钮 + 行尾 `infoIcon` 悬浮说明。

3. **选框取主题色、框内高亮取强调色，高亮居中**：
   - `drawSelection()`：阴影仍 `Pal.accentBack`（和原版同配方），本体改 `D.color(themeColor())`。
   - `drawLogicHighlight()`：`D.color(emphColor())`，并把
     `L.rect(x * 8, y * 8, 8, 8)` 改成 `L.rect((x - 0.5) * 8, (y - 0.5) * 8, 8, 8)`。
   - 半格的来源：`Mindustry-Source/core/src/mindustry/world/Tile.java:166-172` 的
     `worldx()` 返回 `x * tilesize`，是**格子中心**；`Lines.rect(x,y,w,h)` 的左下角语义
     （`Arc-Source/arc-core/src/arc/graphics/g2d/Lines.java:472-495` → `Fill.crect(x, y, width, stroke)`）
     要求左下角再退半格，否则整体偏右上角。v0.6.0 的选框已经踩过一次（`selDrawArgs` 里
     `(r.x1 - 0.5) * 8` 就是那次修的结果），这次是高亮漏了同一手。

## 二、验证

- `node --check MlogAuxiliary/scripts/main.js` → 0（319038 → 324314 字符）。
- `python -X utf8 tests/mlogauxiliary/run_ui_smoke.py` → EXIT=0。
  新探针：`MAITHEME:ok theme=8abcd1ff emph=ffe0a5ff lines=3 maxline=34 … set=ff8800 back=8abcd1 dflt=8abcd1`
  —— 探针里真的 `put("ff8800")` 再读回，然后 `remove`/还原，证明设置项这条链路通。
  新增红线六条：`var THEME_KEY = "mlogauxiliary-theme-color";`、`var EMPH_KEY = "mlogauxiliary-emph-color";`、
  `section(t, "外观");`、`function colorRow(t, label, key, defHex, mk, expl){`、
  `D.color(themeColor());`、`D.color(emphColor());`、`L.rect((x - 0.5) * 8, (y - 0.5) * 8, 8, 8);`，
  并把 `MAITHEME:` 加进 smoke 的**两处**前缀白名单。
- `python -X utf8 gate.py --full --kb-build` → **17/17 in 95.1s**。
- 断言表 **L2-90**（总 149）；规划表加 v0.18.2 行；CHANGELOG 加 `## 0.18.2`；README 设置表加「外观」一行；
  `mod.hjson` 描述补一句（主题色/强调色可调、选框与高亮分色）。

## 三、文件

- `MlogAuxiliary/scripts/main.js`（颜色存取层 + `colorRow()` + 外观段 + 两处画法 + 探针）
- `MlogAuxiliary/mod.hjson`（version、description）
- `tools/logicd.py`（`SIDECAR_VERSION = '0.18.2'`）
- `tests/mlogauxiliary/run_ui_smoke.py`（白名单两处 + 六条红线 + 探针调用）
- `docs/断言表.md`、`docs/Mlog辅助-规划.md`、`CHANGELOG.md`、`MlogAuxiliary/README.md`

## 四、留给真机验的

1. 设置 → Mlog辅助 → **外观**：两行色块颜色与当前值一致；把主题色改成 `ff8800` → 关掉设置、按住框选键拖框，框是不是橙色。
2. 强调色改成别的颜色 → 框里处理器的高亮跟着变。
3. 高亮是否正好压在处理器格子上（不再偏右上角半格）。
4. 改完重启游戏再回来看：两个颜色还在（存的是 `Core.settings`）。
