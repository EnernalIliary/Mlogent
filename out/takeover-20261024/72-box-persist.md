# 72 · mai v0.12.7：框选框只在「写入成功」或「主动关闭」之后才消失

日期 2026-10-31。用户 m01944：

> 选框不应该自行消失，只能在应用后消失，或者主动关闭。

## 72.1 原来为什么会自己没

v0.12.5 的形态是「框留到这一批作业全部终态，再多留 8 s」：

```js
var JOB_BOX_LINGER_MS = 8000;
...
if(jobBox.termAt > 0){
    if(now - jobBox.termAt > JOB_BOX_LINGER_MS){ jobBox = null; jobBadge = null; }
    return;
}
```

这是我自己定的「别一直挂在屏幕上」的礼貌，但对玩家来说正好把上下文收走了：作业生成完，
玩家正要对着框里那几个处理器挑一个看、写入，框先没了，右下角的徽标也没了——得重新框一遍。

## 72.2 现在只有两个消失理由

1. **写入成功**（应用）：`writeBuild()` 写成功之后调 `jobBoxWritten(b)`；
   只有写入的处理器落在 `jobBox.r` 里才清框（框选之外、别的处理器上的写入不影响这块框）。
2. **主动关**：
   - 作业管理窗里新增「关闭框选框」按钮；
   - 右键点框右下角的徽标（左键仍然是「点开作业管理窗」）；
   - 徽标文案跟着改成「作业 2/2 · 完成（点开看 · 右键关）」。

`jobBoxTick()` 在 `jobBox.termAt > 0` 时只**停止轮询**（都终态了，没有新状态可查），
框和徽标继续画；`JOB_BOX_LINGER_MS` 这个常量整个删掉——不留「留几秒」的旋钮，
免得以后又被当成可调参数。

新代码：

```js
function closeJobBox(why){
    if(jobBox === null){ return "没有框选框"; }
    jobBox = null;
    jobBadge = null;
    return (why === null || why === undefined || why === "") ? "框选框已关掉" : String(why);
}

function jobBoxContainsBuild(b){
    if(jobBox === null || jobBox.r === null || b === null || b === undefined) { return false; }
    try{
        var t = b.tile;
        if(t === null || t === undefined){ return false; }
        var r = jobBox.r;
        return t.x >= r.x1 && t.x <= r.x2 && t.y >= r.y1 && t.y <= r.y2;
    }catch(e){ return false; }
}

function jobBoxWritten(b){
    if(jobBox === null){ return; }
    if(!jobBoxContainsBuild(b)){ return; }
    jobBox = null;
    jobBadge = null;
}
```

投递成功的提示也改了：「已投 N 个作业：框右下角点开看进度；写入成功后框才消失（右键徽标可主动关）」。

## 72.3 验证

`tests/mlogauxiliary/run_ui_smoke.py`（无头真 v160.7 引擎，不碰 sidecar）：

```
MAIJOBBOXFIN:{"box":true,...,"terminal":2,"done":1,"failed":1,"linger":true,
              "badge":"作业 2/2 · 1 成 1 败（点开看 · 右键关）"}
MAIJOBBOXPIN2:{"box":true,...,"total":1,"terminal":1,"done":1,"linger":true,
               "badge":"作业 1/1 · 完成（点开看 · 右键关）"}
MAIJOBBOXCLOSE:closed
MAIJOBBOX4:{"box":false}
```

- 终态之后 `linger` 仍是 `true`（框还在），这是 v0.12.5 就有的探针，现在它的含义变成「终态后一直留着」；
- `maiJobBoxClose()` 回 `closed`，随后 `maiJobBox()` 回 `{"box": false}`；
- 反向红线：源码里**不许**再出现 `JOB_BOX_LINGER_MS`；
- 正向红线：`function closeJobBox(` / `jobBoxWritten(b)` / `api.maiJobBoxClose = function`。

结果：ui smoke EXIT=0，`MAIDIAG:版本：0.12.7（游戏构建 160）`；
`gate.py --full --kb-build` 16/16；logicd 侧这一版没动，测试计数不变（protocol 26 / jobs 16 / provider 12 / llm 12）。

## 72.4 装机

模组 0.12.7 覆盖到
`E:\Program Files (x86)\Steam\steamapps\common\Mindustry\saves\mods\MlogAuxiliary\`
之后重启游戏；sidecar 这一版没改（`/health` 的 `version` 仍是 0.12.6，正常）。

## 72.5 还剩下的

- 联机里拒绝写入时的「无权限」提示。
- 写前冲突检测只比代码文本，不比链接表。
- 打包/安装即用（用户已定：最后解决）。
