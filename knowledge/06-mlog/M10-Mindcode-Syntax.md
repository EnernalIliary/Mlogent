---
id: MLOG.MIND.002
title: Mindcode 语法速查（实测）：每条规则都附编译出来的 mlog
domain: mlog
status: active
ver: [v160.7_rt]
conf: E
src:
  - tools/mindcode.py:641-654
  - tools/mindcode.py:655-660
  - tools/mlog_mcp.py:531-564
  - docs/Mindcode集成.md:1-60
data:
  - 06-mlog/instructions.json#meta
depends: [MLOG.MIND.001, MLOG.EXEC.001]
tags: [mindcode, 语法, 编译产物, 实测]
tokens: 1820
---

# M10 Mindcode 语法速查（实测）

## 一句话

Mindcode 3.19.3 / target 7.0 / `optimize=False` 下逐条编译得到的语法规则；每条规则后面都跟着它编出来的 mlog，`tests/mindcode` 里有一组同样的用例，语法变了测试会红。编译选项与版本裁决看 M09（`MLOG.MIND.001`）。

## 规则 / 公式

- **变量**：`a = 3;` → `set :a 3`。变量名在产物里带 `:` 前缀（`:a`），这是 Mindcode 的命名空间，用来避开游戏内置变量 `@counter`/`@this`。
- **表达式**：先算进编译器分配的临时变量 `*tmpN`，再 `set` 进目标变量。编号不稳定，别在产物里找它。
- **分支**：`if cond then ... else ... end;`。关键字是 **`then`**；`case v when 1 then ... end;` 同样用 `then`。三目 `c ? a : b` 可用。
- **范围判断**：`x in 1..9` 编成两条比较 + 跳转，不是一条指令。
- **循环**：`for n in 1..3 do ... end;`、`while cond do ... end;`、C 风格 `for i = 0; i < n; i += 1 do`、`do ... while cond;`、`loop ... end;` + `break`。`do` 只属于循环。
- **函数**：`def f(x) return x * 2; end;`，**内联展开**，没有调用开销也没有栈；参数变量改名成 `:函数名:参数名`，因此不同函数的同名参数不冲突。`void` 修饰 `def` 表示无返回值。
- **数组**：没有字面量。用堆：`allocate heap in cell1;` + `$expr`（下标可以是运行时变量）→ `write`/`read cellN`。`allocate stack` **不**给外部变量分配堆。
- **字符串**：只有 `$"..."` 会插值，且只认 `$变量`；它会展开成多条 `print`。`"a" + i` 是错误，`format()` 不是内置函数。
- **常量**：`const L = 4;` 编译期折叠，不占指令。
- **字面量分号**：块尾写 `end;`；顶层不能出现裸 `end`。

## 数值

- 每条可执行体末尾编译器会追加一行 banner：`print "Compiled by Mindcode 3.19.3 - github.com/cardillan/mindcode"`，位置在 `end` 之后（不可达）。做行对齐时必须排除。
- `for n in 1..3` 展开后是 6 条指令（set / set / jump / op add / op add / jump），比手写 mlog 多 1 条 `set :n 1`。
- `const L = 4; print(L * 2);` 只剩 1 条 `print 8`。
- `def twice(x) return x * 2; end; print(twice(5));` 只剩 `print 10`——内联 + 常量传播把整条调用链消掉了。
- 优化器打开（`optimize=True`）时，未使用变量直接报错，不是警告。

## 源码锚点

- `tools/mindcode.py:641` `compile_source(source, *, target, optimize, ...)`、`:655` `compile_file(path, **kw)`：唯一编译入口。
- `tools/mlog_mcp.py:531-564`：MCP 的 `mindcode_compile`，`map:true` 走 `sourcemap.build()`（固定 `optimize=False`）。
- `docs/Mindcode集成.md:1-60`：为什么是 3.19.3、jar/JRE 定位顺序。
- 语法规范本身在 jar 里（`MindcodeParser.g4`），本仓库不复制。

## 实测与反例

```mindcode
a = 3;
b = a + 4;
print(b);
```
```mlog
set :a 3
op add *tmp0 :a 4
set :b *tmp0
print :b
printflush message1
end
```

```mindcode
s = 0;
for n in 1..3 do
    s += n;
end;
```
```mlog
set :s 0
set :n 1
jump 6 greaterThan :n 3
op add :s :s :n
op add :n :n 1
jump 2 always 0 0
```

```mindcode
allocate heap in cell1;
def store(i, v)
    $i = v;
end;
store(0, 7);
```
```mlog
set :store:i 0
set :store:v 7
write :store:v cell1 0
set *tmp0 :store:v
```

```mindcode
i = 2;
print($"i=$i");
```
```mlog
set :i 2
print "i="
print :i
```

反例（都是真报错原文）：

- `if v > 5 do` → `missing 'then' at 'do'`。
- `print("i=" + i)` → `Unsupported string expression.`
- `print($"i={i}")` 能编过，但 `{i}` **不插值**，产物里就是 `print "i={i}"`。
- 函数体末尾写裸 `end`（不带分号）→ `missing semicolon after 'end'`；顶层写 `end;` → `mismatched input 'end'`。
- `allocate stack in cell1;` + `$i` → `No heap allocated for external variables.`
- `optimize=True` + 未使用变量 → `Variable 'b' is not used.`
- `a = [1, 2, 3];`、`a = (1, 2, 3);`、`a[1]` 都是语法错误（`extraneous input '['`）。

## 常见误解

- **「函数是一个入口，调用有开销」**：不是。函数在编译期内联，产物里没有调用；`twice(5)` 直接变成 `print 10`。
- **「`$"..."` 里可以写任意表达式」**：不能。只认 `$变量`，`{i}` 原样输出；想拼接只能多写几条 `print`。
- **「数组就是 `a[0]`」**：不是。Mindcode 只有堆单元 `$expr`，落在真实内存块 `cellN` 上，和 mlog 的 `read/write` 一一对应。
- **「优化器只删代码」**：它还会**报错**——未使用变量在 `optimize=True` 下编译失败，这是建源码映射时必须关优化的原因。
- **「`end` 和 `end;` 一样」**：不一样，分号属于语法。

## 相关

- `06-mlog/M09-Mindcode.md`（`MLOG.MIND.001`）：入口、版本裁决、诊断三列、失败分类。
- `06-mlog/M01-执行模型总览.md`（`MLOG.EXEC.001`）：产物最终跑在什么时钟与预算上。
- `tools/sourcemap.py`：只对顶层语句建图；块内语句与内联掉的函数调用标 `inside control flow` / `dead code or folded`。
