"""补丁 2：--layout ported 选项 + --ports 参数 + extra 记录 ports。"""
import pathlib

root = pathlib.Path(__file__).resolve().parents[2]
p = root / "mbo" / "cli.py"
s = p.read_text(encoding="utf-8")

s = s.replace('''                   choices=["auto", "cells", "split", "direct"],
                   help="auto=能分门就分门；cells=每台独立源+带；split=物流门分流；"
                        "direct=10 格最小（源/黑洞当 I/O 标记）")''',
              '''                   choices=["auto", "cells", "split", "direct", "ported"],
                   help="auto=能分门就分门；cells=每台独立源+带；split=物流门分流；"
                        "direct=10 格最小（端口嵌在工厂里，docs/18）；"
                        "ported=端口在工厂外框之外（docs/19）")''')

s = s.replace('''    g.add_argument("--merge", default="pair",''',
              '''    g.add_argument("--ports", default=None, choices=["both", "gate", "one"],
                   help="ported 模板的端口方案：both=每台一进一出(8 格)；"
                        "gate=单源经门+每台一出(9 格)；one=单进单出(12 格)")
    g.add_argument("--merge", default="pair",''')

s = s.replace('''    if args.layout == "ported" and merge not in layout.PORTS_CHOICES:
        print("提示：ported 模板的端口方案取 --ports，忽略 --merge %s" % merge)
        merge = "both"''',
              '''    if args.layout == "ported":
        ports = args.ports or "both"
        if args.merge != "pair":
            print("提示：ported 模板的端口方案取 --ports，忽略 --merge %s" % args.merge)
        merge = ports''')

s = s.replace('''"crop": bool(getattr(args, "crop", False))})''',
              '''"crop": bool(getattr(args, "crop", False)),
                                       "ports": merge if args.layout == "ported" else None})''')
p.write_text(s, encoding="utf-8")
print("ok")
