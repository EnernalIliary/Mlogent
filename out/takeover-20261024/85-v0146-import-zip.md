# 85 · v0.14.6：发行包能被游戏直接导入，导入后后端也能自己起来

用户 m06631：「游戏因为没有检测到mod.hjson无法从zip直接导入，解决一下」。
这条需求其实有两半，只修一半会在游戏里立刻撞上第二半。

## 一、前半：游戏认不出我们的 zip（根因在游戏源码）

游戏内 **模组 → 导入** 走 `Mods.importMod()`（`Mindustry-Source/core/src/mindustry/mod/Mods.java:107-149`）：
把选中的文件复制成 `saves/mods/<文件名>.zip`，再 `loadMod()`。决定「模组根在哪」的是两小段：

| 位置 | 逻辑 |
| --- | --- |
| `Mods.resolveRoot()`（Mods.java:1070-1074） | zip 根**恰好只有一个目录**时下钻一层，否则根就是 zip 根 |
| `Mods.findMeta()`（Mods.java:997-1000） | 只在那一层找 `mod.json` / `mod.hjson` / `plugin.json` / `plugin.hjson` |

发行包 `MAI-0.14.6.zip` 顶层有 `mod/`、`install.ps1`、`uninstall.ps1`、`stop-sidecar.ps1`、`安装.bat` 等**多个**条目
⇒ `resolveRoot()` 不下钻 ⇒ `findMeta()` 在 zip 根上找不到 `mod.hjson` ⇒ 游戏报「没有检测到 mod.hjson」。
zip 内容本身没问题（`mod/MlogAuxiliary/mod.hjson` 一直在，`安装.bat` 就是这么装的），只是游戏导入不认这个层级。

**改法**：`tools/package.py` 另出一个 `<name>-mod.zip`，顶层只有一个 `MlogAuxiliary/`，`mod.hjson` 就在它下面；
`build_mod_zip()` 里缺 `mod.hjson` 直接 `RuntimeError`；`verify()` 第 7 步按游戏的 `resolveRoot()+findMeta()` 规则验形状；
`tests/packaging/run_pack_tests.py` 第 3b 组同一套规则 + **反向断言整包 zip 顶层不是单目录**（否则这组会退化成自证）；
`packaging/使用说明.md` 加「也可以在游戏里直接导入」与一条排障行。

## 二、后半：导入后模组是 ZipFi，随包的 exe 执行不了

导入成功后 `m.root` 不再是目录，而是 `arc.files.ZipFi`。原来的 `sidecarExe()` 拿
`m.root.child("sidecar").child("bin").child("logicd.exe")` 交给 `ProcessBuilder` ——
zip 里的条目不是文件系统里的文件：执行不了，`pb.directory(new File(...))` 也拿不到目录。
不处理的话，玩家导入成功、模组能开，但 sidecar 永远起不来（满屏「连不上 sidecar」）。

**改法**（`MlogAuxiliary/scripts/main.js`，v0.14.6）：

- `sidecarIsZip()`：`String(m.root.getClass().getName()).indexOf("ZipFi") >= 0`。
- `sidecarCopyTree(src, dst)`：递归 `list()`，逐文件 `read()` → `write(InputStream, false)`，
  已存在且 `length()` 相同就跳过（101 个文件、约 40 MB，只解一次）。
  **不能写 `try{…}finally{…}`** —— v160.7 的 Rhino 在 finally 体里带 try/catch 时 codegen 会炸，
  `run_ui_smoke.py` 有一条红线专门守着这个。
- `sidecarBinDir()`：磁盘安装（`安装.bat`）走原路径、不解压；zip 安装解到
  `Vars.dataDirectory/mlogauxiliary/sidecar/<MOD_VERSION>/`（目录名带版本号 ⇒ 升级自动换新），
  首次 hint「从模组包解出逻辑后端（首次约 40 MB）…」。
- `sidecarExe()` / `sidecarDir()` 都改成问 `sidecarBinDir()`，其余代码不变。

## 三、实测

```
PACK:import-zip MAI-0.14.6-mod.zip files=157 tops=MlogAuxiliary
  ok  import zip: MlogAuxiliary/mod.hjson at root, 157 file(s), 8.4 MB
11 check(s), 0 problem(s)
```

导入 zip 里 `MlogAuxiliary/scripts/main.js` 实测含 `function sidecarIsZip(` / `function sidecarCopyTree(` /
`function sidecarBinDir(` / `Vars.dataDirectory.child("mlogauxiliary").child("sidecar")`，
且不含 `}finally{`；`MlogAuxiliary/mod.hjson` 的 `version: "0.14.6"`。

产物（`out/_dist/`）：

| 文件 | 大小 | sha256 | 用途 |
| --- | --- | --- | --- |
| `MAI-0.14.6-mod.zip` | 8408196 B | `4E177F36…CDFF60` | **游戏内导入用** |
| `MAI-0.14.6.zip` | 8428606 B | `574C22BD…990342` | 整包（`安装.bat` 双击装机用） |

`node --check` 0；ui smoke EXIT=0；`tests/packaging/run_pack_tests.py` 11 组全过；
`gate.py --full --kb-build` 17/17（含 `package` 步的 `verify()` 与包内 exe 的 `/health`）。

## 四、留给玩家的两句话

- 要游戏内导入：选 `MAI-<版本>-mod.zip`（首次进游戏会看到「从模组包解出逻辑后端」，等几秒）。
- 要双击装机：解压整包（`MAI-<版本>.zip`）跑 `安装.bat`，装在磁盘上、不用解压。
