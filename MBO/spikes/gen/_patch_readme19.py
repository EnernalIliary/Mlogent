"""回写 README + docs/18 指向 docs/19。"""
import pathlib

root = pathlib.Path(__file__).resolve().parents[2]

p = root / "README.md"
s = p.read_text(encoding="utf-8")

s = s.replace(
    "│   ├── 18-石墨蓝图下界与10格最小蓝图.md  direct：10 格下界证明 + 5×2 蓝图 + 分数周期计量",
    "│   ├── 18-石墨蓝图下界与10格最小蓝图.md  direct：10 格下界证明 + 5×2 蓝图 + 分数周期计量\n"
    "│   ├── 19-端口在外与物流限速.md      端口只能在外 + 速率由物流决定：8/4、9/3、12/2 三条前沿",
)

s = s.replace(
    "├── tests/test_mbo.py               ← 39 项单元测试（python -m unittest discover -s MBO/tests）",
    "├── tests/test_mbo.py               ← 49 项单元测试（python -m unittest discover -s MBO/tests）",
)
s = s.replace("39 项单测通过", "49 项单测通过")

# 验证表：在 direct 行后追加 ported 行
row_direct = [l for l in s.split("\n") if l.startswith("| `mbo gen --layout direct --crop`")]
assert row_direct, "direct 行没找到"
new_rows = (
    "| `mbo gen --layout ported --ports both --crop`（端口在外） | 源/黑洞只能落在工厂外框之外，"
    "每台压机各一进一出：**工厂 8 格 / 4 端口 / 6 方块 / 1.282/s（−3.9%）**；"
    "gate 变体 9 格/3 端口/1.287/s，one 变体 12 格/2 端口/1.359/s | "
    "新口径下 10 格 direct 失效（端口嵌在工厂里），前沿改为 8/4、9/3、12/2，见 `docs/19` |"
)
s = s.replace(row_direct[0], row_direct[0] + "\n" + new_rows)

# §5 复现命令
s = s.replace(
    "python -X utf8 -m mbo gen graphite:1/s --boundary coal --layout direct --crop --out d10",
    "python -X utf8 -m mbo gen graphite:1/s --boundary coal --layout direct --crop --out d10\n"
    "python -X utf8 -m mbo gen graphite:1/s --boundary coal --layout ported --ports both --crop --out p-both\n"
    "python -X utf8 -m mbo gen graphite:1/s --boundary coal --layout ported --ports one  --crop --out p-one\n"
    "python -X utf8 spikes/gen/search_ported.py   # 端口在外 + 物流限速的枚举/随机搜索",
)
p.write_text(s, encoding="utf-8")

d18 = root / "docs" / "18-石墨蓝图下界与10格最小蓝图.md"
t = d18.read_text(encoding="utf-8")
if "docs/19" not in t:
    t = t.rstrip("\n") + (
        "\n\n## 8 后续：口径变了，下界要重求\n\n"
        "用户 m02384 追加了两条硬约束——**输入/输出标记只能在绘制区域之外**、**速率由物流元件决定**。"
        "本文件的 10 格蓝图把源与黑洞嵌在两台机器之间，在新口径下不再合法"
        "（`logistics.ports_outside=False`）。"
        "在“端口在外”的前提下重新做枚举搜索，得到三条前沿：工厂 8 格/4 端口、9 格/3 端口、12 格/2 端口，"
        "真机 1.2817–1.3588/s。详见 `docs/19-端口在外与物流限速.md`。\n"
    )
    d18.write_text(t, encoding="utf-8")

print("README + docs/18 updated")
