# Writing style: English knowledge base

The knowledge base is the project's mother document. Readers are models and
people who work with Mindustry logic; the interface layer (tools, MCP, SKILL)
is already English, so the articles are being brought into the same language.

## What "English" means here

Translate every sentence a reader reads: headings, prose, list items, table
prose cells, caption lines, image alt text, block-quote text, YAML `title` and
`tags`.

## What stays as it is

These are **name mappings** (对照) or load-bearing literals. Keeping them in
Chinese is the point, not an oversight:

| Item | Example | Why |
|---|---|---|
| Official Chinese game names | `flare (星辉)`, `差扰 (parallax)` | the mapping is the product |
| Name-table cells | `| 星辉 | flare | ... |` | the name table *is* the 对照 |
| `id` in front matter | `MLOG.MIND.001` | identifier |
| Anchors | `LogicBlock.java:565` | must resolve |
| Assertion ids | `L1-14`, `S-11` | referenced by `claims.jsonl` |
| Wiki links | `[[W11-block-state]]` | resolved by tooling |
| Code fences | every byte | they are runnable samples |
| File names | `E05-链接与@常量.md` | stable ids used by links and the index |

Inside a table, a cell may hold a Chinese name (`星辉`, `flare / 星辉`). It may
not hold a Chinese sentence. Rule of thumb: a cell with more than ~16 CJK
characters, or with `。`、`，`、`；` in it, is prose and must be English.

Inside prose, a Chinese gloss is allowed only in parentheses right after the
Latin term: `flare (星辉)`. A bare Chinese clause is a translation miss.

## Do not change

* numbers, units, formulas, table row/column counts
* heading count and heading levels (`#`, `##`, `###`)
* the order of sections, list items and table rows
* front-matter keys (`id`, `domain`, `status`, `ver`, `conf`, `src`, `tags`,
  `title`, `tokens`) and every value except `title` / `tags`
* `src:` / `[src: ...]` anchors, counts included: `file.ext:NN` must survive
  one-for-one
* anything inside a fenced code block

## Voice

Write like the existing English documents: short declarative sentences, the
number first, the reason second. Prefer "the executor drains two instructions
per tick" over "it can be seen that instructions are drained". Keep the
imperative in procedures ("Set the core stock, then run 120 ticks").

## Check

```bash
python knowledge/tools/check_en.py <files...>
```

With no arguments it checks every article. Exit code 1 lists prose lines that are still Chinese, headings that are still
Chinese, unbalanced code fences, or front-matter `title`/`tags` that still hold
CJK. A file is done when the checker is silent for it.
