"""Note the 'always use mlog.py gen' rule and the --with-block coordinate gotcha."""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

SEC = """### 15.25 生成蓝图一律走 `mlog.py gen`,不要自己拼 base64

`mlog.py gen` **默认就把 paste-ready 的 base64 打到 stdout**,`--out` 还能存成文件;
`mschgen.py:582` 同样是 `print(base64.b64encode(data).decode())`。
所以在聊天里贴蓝图码的正确做法是:跑 gen,把它打印的那一行原样贴出去。

我犯过的错:自己写 `"bXNjaAF4n" + b64[8:]` —— 前缀 9 个字符却只砍 8 个,长度变成
`4k+1`,游戏报 *Length of Base64 encoded input string is not a multiple of 4*。
**文件本身没问题,坏的是拼字符串那一步。**

顺带弄清的两件事:

* 蓝图码前缀**不一定是 `bXNjaAF4n`**。它取决于 zlib 压缩等级:游戏自己写出来是
  `78 9c`(默认),本仓库的 `mschgen` 用最高压缩 `78 da`,于是第 11 个字符不同
  (`bXNjaAF42mPg...`)。**两种都合法**,游戏只认解码后的 `msch` 魔数。
* `--with-block block@dx,dy` 的 `dx,dy` 是**相对处理器**的**方块中心**,和 `--link`
  同一套约定。帮助文本原来写成 "CENTER coords",容易读成绝对坐标 —— 已经改掉。
  传绝对坐标会让方块整体偏移,`link_report()` 于是警告
  `link target ... is not covered by any placed block`(那个警告本身是对的)。
"""

ROW = ("| 第 35 次整理 | 生成蓝图一律用 `mlog.py gen`(它自己打印 base64),不要手拼前缀;"
       "`--with-block` 的 dx,dy 是相对处理器的中心坐标。**工具已经会做的事,"
       "再手写一遍只会多出一个 bug 的位置。** |")


def main() -> None:
    p = ROOT / "mlog工作笔记.md"
    s = p.read_text(encoding="utf-8")
    if "### 15.25" not in s:
        i = s.index("## 16.")
        s = s[:i] + SEC + "\n" + s[i:]
    if "第 35 次整理" not in s:
        lines = s.split("\n")
        last = max(i for i, l in enumerate(lines)
                   if l.startswith("| 第 ") and "次整理" in l)
        lines.insert(last + 1, ROW)
        s = "\n".join(lines)
    p.write_text(s, encoding="utf-8")
    print("notes updated")


if __name__ == "__main__":
    main()
