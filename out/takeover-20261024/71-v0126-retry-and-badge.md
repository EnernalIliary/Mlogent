# 71 · mai v0.12.6：重试中的 findings 不是结论；角标必须贴住框的右下角

日期 2026-10-31。两个真机反馈各一条，都在这一版修：

- m01735「哦哦，成功了，但是在模型生成被截断的时候还有报错。」
- m01862「在矩形选框的作业提示框错位了。」

## 71.1 「还在重试」被渲染成了「失败」

真机作业 `out/jobs/ef8ff52c4b10a16a.json`：`state=done`、`attempts=2`、`snapshot.mod=0.12.5`，
代码 6 条（`radar player any any distance @this 1 100000 unit` / `sensor ctrl unit @controller` /
`sensor playerName ctrl @name` / `print playerName` / `printflush message1` / `end`），
`reasoning` 满 12000 字符。也就是说**这次是成功的**，第一次尝试被截断、第二次自己成了。

但玩家在作业管理窗里看到的却是第一次尝试留下的 finding：

```
ERR provider-error model endpoint answered with an empty message
    (finish_reason=length; message keys=content,reasoning_content,role;
     usage={"completion_tokens": 1600, "prompt_tokens": 513})
```

`findings` 是「当前这次尝试的问题」的实时字段，不是结论；作业只要还没终态，它随时会被下一次尝试覆盖。
把它按结论渲染，就是「明明在跑，看起来像失败」。

改法两处：

1. **模组**（`MlogAuxiliary/scripts/main.js`）
   - `jobRetryHead(job)`：非终态且 `findings` 非空 → `--- 上一次尝试的问题（第 2 次，还在重试）---`；
   - `jobFindingLines(job, maxLines)`：消息里出现 `finish_reason=length` 时补一行人话
     `（模型把回复预算用在思考上了，sidecar 会自动加大预算再试一次）`；
   - `renderJob()` 的运行分支与 `renderManagerDetail()` 都走这一套（详情页把 `state` 的读取提到 findings 之前）。
2. **sidecar**（`tools/mlogprovider.py`）
   - `_why_blank(doc, budget=None)` 把预算写进消息：`budget=16000 tokens`；
   - `finish_reason == "length"` 时追加 `the model ran out of room mid-thought, before it wrote an answer`；
   - `_once()` 的三条失败路径（没有 message / content 空且解析不出 / `ProviderError`）全部带上 budget。

这样就算只在盘上的作业文件里看，也能分清「模型想太久被截断」和「端点拒绝服务」。

## 71.2 角标错位：位置和点击区算的是两份几何

v0.12.5 的 `drawJobBadge()` 里，画字用 `font.draw(text, bx, by + h)`，点击区用
`{x: bx - 3/s, y: by - 2/s, w: w + 6/s, h: h + 4/s}`，而 `h = 13 / scale` 是个**估算**的行高。
两个后果：

- arc 的 `font.draw(text, x, y)` 里 **y 是基线，字往上涨**（原版 `InputHandler.drawSizeText`
  把尺寸字画在 `mouseWorldY() + offset`，也就是字浮在光标上方，正是这个语义）。
  基线放在 `by + h = 框底边 - 8/scale`，字就整条**压在框底边内侧**——看起来是「错位」，
  而不是「贴在框外」。
- 点击区按「字在基线下方」算，于是**点击区在框外、字在框内**：看得见、点不着。
- 另外没关 `setUseIntegerPositions`：`1/camerascale` 的小数位置被量化成整数，字会整体飘开框的角
  （原版同一段代码是 `font.setUseIntegerPositions(false)`）。

改法：**先算矩形，再按矩形画字、按矩形收点击**。

```js
function jobBadgeRect(a){        // 唯一一份几何
    ...
    var bx = a.x + a.w - w - 4 / scale;   // 右对齐：字右端离框右边 4 屏幕像素
    var top = a.y - 4 / scale;            // 字顶离框底边 4 屏幕像素（整个字在框外）
    return {text: text, x: bx, y: top - hh, w: w, h: hh, scale: scale, top: top, right: bx + w};
}
```

`drawJobBadge()` 只用它画（`font.draw(m.text, m.x, m.y)`，即基线 = `top - 字高`），
`jobBadge` 命中区也只用它（`{x: m.x - 3/s, y: m.y - 3/s, w: m.w + 6/s, h: m.h + 6/s}`），
并且照原版关掉整数对齐、画完还原。

不管引擎把 y 当基线还是当字顶，这个写法都把整条字放在**框底边外侧**，不会再压进框里。

## 71.3 验证

`tests/mlogauxiliary/run_ui_smoke.py`（真 v160.7 引擎，无头）：

```
MAIJOBBOXPIN:{"box":true,...,"total":2,"terminal":0,"badge":"作业 0/2 · 生成中（点开看）"}
MAIBADGERECT:{"rect":true,"scale":1,"box":{"x":4,"y":4,"w":48,"h":48},
              "right":48,"top":0,"x":-105,"y":-13,"w":153,"h":13,
              "text":"作业 0/2 · 生成中（点开看）"}
```

框在 (1,1)-(6,6) → `selDrawArgs` 给 `{x:4, y:4, w:48, h:48}`，即右边 52、底边 4；
角标 `right=48=52-4`、`top=0=4-4`、`y+h=top`、`x+w=right` ⇒ 贴住右下角、整条在框外。

断言（新增）：

- `right` 必须等于 `box.x + box.w - 4/scale`；
- `top` 必须等于 `box.y - 4/scale`；
- `y + h == top`（基线语义自洽）、`x + w == right`；
- 量的字必须是当时那条角标文案；
- 源码红线 `function jobBadgeRect(` / `font.setUseIntegerPositions(false)` / `api.maiBadgeRect = function`。

`tests/logicd/run_logicd_tests.py`（`test_provider()` 第 10 项）：

- 空白回复的消息里必须有 `budget=`；
- 必须有 `ran out of room`。

结果：`protocol: 26 / jobs: 16 / provider: 12 / llm: 12`，`logicd OK (protocol only)`；
ui smoke EXIT=0（`MAIDIAG:版本：0.12.6（游戏构建 160）`）；`gate.py --full --kb-build` 16/16。

## 71.4 装机与重启

- 模组：`E:\Program Files (x86)\Steam\steamapps\common\Mindustry\saves\mods\MlogAuxiliary\`
  覆盖 `main.js` / `mod.hjson` 后**重启游戏**（`MAIDIAG` 里的版本号应变成 0.12.6）。
- sidecar：`python tools/logicd.py`，`GET /health` 的 `version` 应为 `0.12.6`；
  旧进程不重启的话，`/jobs?all=1` 会被忽略（管理窗只剩在飞作业）。

## 71.5 还剩下的

- 联机里拒绝写入时的「无权限」提示（现在只会回一条干巴巴的失败）。
- 写前冲突检测只比代码文本，不比链接表。
- 打包/安装即用（用户已定：最后解决）。
