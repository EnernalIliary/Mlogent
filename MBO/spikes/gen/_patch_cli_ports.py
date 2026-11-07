"""补丁：CLI 接 --layout ported --ports，validate 接端口在外检查。"""
import pathlib

root = pathlib.Path(__file__).resolve().parents[2]

# ---------------- cli.py ----------------
p = root / "mbo" / "cli.py"
s = p.read_text(encoding="utf-8")

s = s.replace('''    merge = args.merge
    if args.layout == "direct" and merge != "pair":
        print("提示：direct 模板固定用 item-void 当输出标记，忽略 --merge %s" % merge)
        merge = "pair"''',
              '''    merge = args.merge
    if args.layout == "direct" and merge != "pair":
        print("提示：direct 模板固定用 item-void 当输出标记，忽略 --merge %s" % merge)
        merge = "pair"
    if args.layout == "ported" and merge not in layout.PORTS_CHOICES:
        print("提示：ported 模板的端口方案取 --ports，忽略 --merge %s" % merge)
        merge = "both"''')

s = s.replace('''    static = validate.static_check(lay, gd, plan)''',
              '''    static = validate.static_check(lay, gd, plan,
                                   strict_ports=(args.layout == "ported"))''')

s = s.replace('''                                       "layout": args.layout, "gate": args.gate, "merge": merge,''',
              '''                                       "layout": args.layout, "gate": args.gate, "merge": merge,
                                       "ports": merge if args.layout == "ported" else None,''')
p.write_text(s, encoding="utf-8")

# ---------------- validate.py ----------------
v = root / "mbo" / "validate.py"
t = v.read_text(encoding="utf-8")

t = t.replace('def static_check(lay, gd, plan=None) -> dict:',
              'def static_check(lay, gd, plan=None, strict_ports: bool = False) -> dict:')

t = t.replace('''        if not any(lay.adjacent(t, s) for s in SINK):''',
              '''        if not any(lay.adjacent(t, s) for s in SINK):''')

marker = '''    return {"ok": not errors, "errors": errors, "warnings": warnings, "info": info}'''
assert marker in t

ports_block = '''    # 端口在外（docs/19）：item-source / item-void 只能当工厂边界之外的 I/O 标记
    from . import logistics
    ports_ok, ports_msg = logistics.ports_outside(lay, gd)
    info["ports_outside"] = ports_ok
    info["ports_msg"] = ports_msg
    if strict_ports and not ports_ok:
        errors.append("端口位置违规：" + ports_msg)
    elif not strict_ports and not ports_ok:
        warnings.append("端口落在工厂矩形内（旧模板）：" + ports_msg)

'''
t = t.replace(marker, ports_block + marker)
v.write_text(t, encoding="utf-8")
print("patched cli.py / validate.py")
