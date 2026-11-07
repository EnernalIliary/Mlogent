"""回写 README：docs/20、56 项单测、preview 贴图说明。"""
import pathlib

R = pathlib.Path(__file__).resolve().parents[2]   # MBO/
p = R / "README.md"
s = p.read_text(encoding="utf-8")

# 1) 目录树：docs 加 20 行
old = "│   ├── 19-端口在外与物流限速.md      端口只能在外 + 速率由物流决定：8/4、9/3、12/2 三条前沿\n"
new = old + "│   ├── 20-原版贴图预览.md            用 assetsraw 原版贴图渲染 preview（缺图自动回落色块）\n"
assert old in s
s = s.replace(old, new, 1)

# 2) 目录树：模块与测试数
s = s.replace("│   ├── layout.py / validate.py / engine.py / report.py / cli.py\n",
              "│   ├── layout.py / validate.py / engine.py / report.py / cli.py\n"
              "│   ├── logistics.py / preview.py / sprites.py\n", 1)
s = s.replace("├── tests/test_mbo.py               ← 49 项单元测试",
              "├── tests/test_mbo.py               ← 56 项单元测试", 1)
s = s.replace("├── runs/<run_id>/                  ← 每次 gen 的 5 件产物（msch / b64 / metrics / report / trace）+ preview.png",
              "├── runs/<run_id>/                  ← 每次 gen 的 5 件产物（msch / b64 / metrics / report / trace）+ preview.png（原版贴图）", 1)

# 3) preview 命令说明
old_cmd = "python -X utf8 -m mbo preview --all      # 画廊 runs/index.html（所有 run 一页看完）\n"
new_cmd = old_cmd + (
    "python -X utf8 -m mbo preview --all --scale 3 --sprites   # 重绘全部 PNG + 画廊（贴原版贴图）\n"
    "python -X utf8 -m mbo preview d10 --no-sprites             # 强制色块（对比/排障用）\n")
assert old_cmd in s
s = s.replace(old_cmd, new_cmd, 1)

p.write_text(s, encoding="utf-8")
print("README 已回写")
