---
id: MLOG.MIND.002
title: "Mindcode syntax cheat sheet (measured): every rule comes with the mlog it compiles to"
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
tags: [mindcode, syntax, compile output, measured]
tokens: 1820
---

# M10 Mindcode syntax cheat sheet (measured)

## In one sentence

Grammar rules obtained by compiling them one at a time under Mindcode 3.19.3 / target 7.0 / `optimize=False`; each rule is followed by the mlog it compiles to, and `tests/mindcode` holds the same set of cases, so a grammar change turns the tests red. For compile options and version arbitration see M09 (`MLOG.MIND.001`).

## Rules / formulas

- **Variables**: `a = 3;` → `set :a 3`. In the output the name carries a `:` prefix (`:a`), Mindcode's namespace, used to stay clear of the game's built-in variables `@counter`/`@this`.
- **Expressions**: they are computed into a compiler-assigned temporary `*tmpN` first, then `set` into the target variable. The numbering is unstable, so do not look for it in the output.
- **Branches**: `if cond then ... else ... end;`. The keyword is **`then`**; `case v when 1 then ... end;` uses `then` as well. The ternary `c ? a : b` works.
- **Range tests**: `x in 1..9` compiles to two comparisons + jumps, not to one instruction.
- **Loops**: `for n in 1..3 do ... end;`, `while cond do ... end;`, the C style `for i = 0; i < n; i += 1 do`, `do ... while cond;`, `loop ... end;` + `break`. `do` belongs to loops only.
- **Functions**: `def f(x) return x * 2; end;` is **inlined**, so there is no call overhead and no stack; the parameters are renamed to `:<function>:<parameter>`, so same-named parameters of different functions do not clash. `void` on a `def` means no return value.
- **Arrays**: there are no literals. Use a heap: `allocate heap in cell1;` + `$expr` (the index may be a runtime variable) → `write`/`read cellN`. `allocate stack` does **not** allocate a heap for external variables.
- **Strings**: only `$"..."` interpolates, and it recognises only `$variable`; it expands into several `print` calls. `"a" + i` is an error and `format()` is not a built-in function.
- **Constants**: `const L = 4;` folds at compile time and occupies no instruction.
- **The semicolon is literal**: a block ends with `end;`; a bare `end` may not appear at the top level.

## Numbers

- The compiler appends one banner line to the end of every executable body: `print "Compiled by Mindcode 3.19.3 - github.com/cardillan/mindcode"`, placed after `end` (so it is unreachable). Line alignment has to exclude it.
- `for n in 1..3` expands to 6 instructions (set / set / jump / op add / op add / jump), one more than the hand-written mlog: `set :n 1`.
- `const L = 4; print(L * 2);` leaves only 1 instruction, `print 8`.
- `def twice(x) return x * 2; end; print(twice(5));` leaves only `print 10` — inlining plus constant propagation removes the whole call chain.
- With the optimiser on (`optimize=True`) an unused variable is a hard error, not a warning.

## Source anchors

- `tools/mindcode.py:641` `compile_source(source, *, target, optimize, ...)`, `:655` `compile_file(path, **kw)`: the only compile entry points.
- `tools/mlog_mcp.py:531-564`: the MCP `mindcode_compile`; `map:true` goes through `sourcemap.build()` (with `optimize=False` hardcoded).
- the integration doc (`docs/Mindcode集成.md:1-60`): why 3.19.3, and the jar/JRE resolution order.
- The grammar itself lives in the jar (`MindcodeParser.g4`); this repo does not copy it.

## Measured facts and counter-examples

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

Counter-examples (all verbatim error text):

- `if v > 5 do` → `missing 'then' at 'do'`.
- `print("i=" + i)` → `Unsupported string expression.`
- `print($"i={i}")` compiles, but `{i}` is **not interpolated**; the output is literally `print "i={i}"`.
- A bare `end` at the end of a function body (no semicolon) → `missing semicolon after 'end'`; `end;` at the top level → `mismatched input 'end'`.
- `allocate stack in cell1;` + `$i` → `No heap allocated for external variables.`
- `optimize=True` + an unused variable → `Variable 'b' is not used.`
- `a = [1, 2, 3];`, `a = (1, 2, 3);` and `a[1]` are all syntax errors (`extraneous input '['`).

## Common misconceptions

- **"A function is an entry point, so calling it costs something"**: no. Functions are inlined at compile time and the output holds no call; `twice(5)` simply becomes `print 10`.
- **"Any expression can go inside `$"..."`"**: it cannot. Only `$variable` is recognised and `{i}` is emitted verbatim; for concatenation, write several `print` calls.
- **"An array is just `a[0]`"**: it is not. Mindcode has only heap cells `$expr`, which land on a real memory block `cellN` and map one-to-one onto mlog's `read/write`.
- **"The optimiser only deletes code"**: it also **errors** — an unused variable fails the compile under `optimize=True`, which is why optimisation must be off when a source map is built.
- **"`end` and `end;` are the same"**: they are not; the semicolon is part of the grammar.

## Related

- `06-mlog/M09-Mindcode.md` (`MLOG.MIND.001`): entry points, version arbitration, the three diagnostic columns, failure classes.
- the execution model overview (`06-mlog/M01-执行模型总览.md`, `MLOG.EXEC.001`): which clock and budget the output finally runs on.
- `tools/sourcemap.py`: maps top-level statements only; statements inside blocks and inlined-away calls are marked `inside control flow` / `dead code or folded`.
