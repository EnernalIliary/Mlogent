# data/game/bundles/ —— 两份语言包，为什么在仓库里

`bundle.properties`（英文）与 `bundle_zh_CN.properties`（中文）是 Mindustry 160.7 自带的
语言包，从同级素材项目 `TextureMDT`（原名 `assetsraw`）的 `assets/bundles/` 原样复制过来。

## 为什么复制

`knowledge/tools/gen_name_docs.py` 与 `gen_game_aliases.py` 唯一的输入就是这两个文件。
它们原先从仓库外的素材树找，于是：

- 干净 checkout 里两个生成器都跑不了，CI 也就没法检查 `data/game/aliases.json` 和
  五篇命名文档（`knowledge/02-world/W13..W16`、`04-units/U06`）是不是还和归属数据一致；
- 生成的文档里写着 `zh:N`/`en:N`，指的是**这两个文件的行号**。素材树一旦被重排版或被换版本，
  所有引用都会悄悄指错，而且没有任何东西会报错。

两个文件合计 339 KB，比它们守护的那些生成物还小，所以直接放进仓库。

## 约束：字节一致

- **保持 LF、不要加 BOM、不要重排版**：`zh:N` 是行号，动一下换行就把全部出处挪位。
  `tests/bundles/run_bundle_tests.py` 会检查这两件事。
- 升级游戏版本时：从新素材包重新复制，然后跑
  `python knowledge/tools/gen_name_docs.py` 与 `python knowledge/tools/gen_game_aliases.py`
  重新生成产物（两者都支持 `--check`，只看差异不写盘）。

## 覆盖顺序

`$MLOG_BUNDLES` → 本目录 → `assetsraw/assets/bundles/` → `../TextureMDT/assets/bundles/` →
`../Mindustry_assetsraw/assets/bundles/` → `../assetsraw/assets/bundles/`。
仓库外的素材树只是覆盖用的，行号必须与本目录一致，否则 `zh:N` 就不再诚实。

## 授权

Mindustry 以 GPLv3 发布，语言包是其源码的一部分（`core/assets/bundles/`）。
这里只放两份 `.properties` 文本，不包含任何贴图/音频/地图资源；图片资源仍在外部的
`TextureMDT` 项目里。
