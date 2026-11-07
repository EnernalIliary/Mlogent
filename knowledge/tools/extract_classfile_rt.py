#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_rt.py - 从 mindustry 服务器 jar (v160.7) 直接解析 .class 常量池/字节码，
导出指定类的字段默认值（替代 javac 反射；本机无 JDK，只有 JRE21）。

用法:
  python -u extract_rt.py --jar out/_server160.jar --fields "mindustry.Vars#minArmorDamage,mindustry.Vars#tilesize"
  python -u extract_rt.py --jar out/_server160.jar --fields-file fields.txt --out rt_values.json
  python -u extract_rt.py --jar out/_server160.jar --list mindustry.game.Rules

实现：只用 stdlib(zipfile/struct/json/argparse)。
  1. 解析 constant pool (tag 1/3/4/5/6/7/8/9/10/11/12/15/16/17/18/19/20)
  2. 字段：读 ConstantValue 属性（static final 编译期常量）
  3. 方法：在 <init>/<clinit> 的 Code 里匹配 aload_0? + ldc/bipush/sipush/iconst/fconst/lconst/dconst + putfield/putstatic
  4. 输出 {class: {field: {desc, const, default}}}
不追求完整反汇编：只识别"加载常量 -> 存字段"的相邻指令对，漏掉的字段 default 为 null。
"""
import json, struct, zipfile, argparse

def parse_class(data):
    assert data[:4] == b"\xca\xfe\xba\xbe", "bad magic"
    p = 8
    cpcount = struct.unpack_from(">H", data, p)[0]; p += 2
    cp = [None] * cpcount
    i = 1
    while i < cpcount:
        tag = data[p]; p += 1
        if tag == 1:
            ln = struct.unpack_from(">H", data, p)[0]; p += 2
            cp[i] = ("utf8", data[p:p+ln].decode("utf-8", "replace")); p += ln
        elif tag in (3, 4):
            cp[i] = ("int" if tag == 3 else "float", data[p:p+4]); p += 4
        elif tag in (5, 6):
            cp[i] = ("long" if tag == 5 else "double", data[p:p+8]); p += 8
            i += 1
        elif tag in (7, 8, 16, 19, 20):
            cp[i] = (tag, struct.unpack_from(">H", data, p)[0]); p += 2
        elif tag in (9, 10, 11, 12, 17, 18):
            cp[i] = (tag, struct.unpack_from(">HH", data, p)); p += 4
        elif tag == 15:
            cp[i] = (tag, struct.unpack_from(">BH", data, p)); p += 3
        else:
            raise ValueError("unknown cp tag %d at %d" % (tag, p))
        i += 1

    def utf(idx):
        e = cp[idx] if 0 <= idx < cpcount else None
        return e[1] if e and e[0] == "utf8" else None

    def const_val(idx):
        e = cp[idx] if 0 <= idx < cpcount else None
        if e is None: return None
        t = e[0]
        if t == "int": return struct.unpack(">i", e[1])[0]
        if t == "float": return round(struct.unpack(">f", e[1])[0], 6)
        if t == "long": return struct.unpack(">q", e[1])[0]
        if t == "double": return round(struct.unpack(">d", e[1])[0], 6)
        return None

    p += 6
    ifc = struct.unpack_from(">H", data, p)[0]; p += 2 + 2 * ifc

    fields = []
    fc = struct.unpack_from(">H", data, p)[0]; p += 2
    for _ in range(fc):
        acc, name_i, desc_i, ac = struct.unpack_from(">HHHH", data, p); p += 8
        cv = None
        for _a in range(ac):
            an_i, alen = struct.unpack_from(">HI", data, p); p += 6
            body = data[p:p+alen]; p += alen
            if utf(an_i) == "ConstantValue":
                cv = const_val(struct.unpack_from(">H", body, 0)[0])
        fields.append({"name": utf(name_i), "desc": utf(desc_i), "const": cv})

    methods = []
    mc = struct.unpack_from(">H", data, p)[0]; p += 2
    for _ in range(mc):
        acc, name_i, desc_i, ac = struct.unpack_from(">HHHH", data, p); p += 8
        code = None
        for _a in range(ac):
            an_i, alen = struct.unpack_from(">HI", data, p); p += 6
            body = data[p:p+alen]; p += alen
            if utf(an_i) == "Code":
                clen = struct.unpack_from(">I", body, 4)[0]
                code = body[8:8+clen]
        methods.append({"name": utf(name_i), "desc": utf(desc_i), "code": code})
    return {"utf": utf, "const": const_val, "fields": fields, "methods": methods, "cp": cp}

LOADS = {0x02:-1, 0x03:0, 0x04:1, 0x05:2, 0x06:3, 0x07:4, 0x08:5}
FCONST = {0x0b:0.0, 0x0c:1.0, 0x0d:2.0}
LCONST = {0x09:0, 0x0a:1}
DCONST = {0x0e:0.0, 0x0f:1.0}

def scan_pairs(cls):
    res = []
    for m in cls["methods"]:
        code = m.get("code")
        if not code: continue
        i = 0; n = len(code); cp = cls["cp"]
        while i < n:
            j = i + 1 if code[i] == 0x2a else i
            if j + 2 >= n: break
            op = code[j]; val = None; adv = 0
            if op == 0x12:
                ci = code[j+1]; adv = 2
                e = cp[ci] if ci < len(cp) else None
                if e and e[0] in ("int", "float"): val = cls["const"](ci)
                elif e and e[0] == 8: val = cls["utf"](e[1])
            elif op == 0x13:
                ci = struct.unpack_from(">H", code, j+1)[0]; adv = 3
                e = cp[ci] if ci < len(cp) else None
                if e and e[0] in ("int", "float"): val = cls["const"](ci)
                elif e and e[0] == 8: val = cls["utf"](e[1])
            elif op == 0x14:
                ci = struct.unpack_from(">H", code, j+1)[0]; adv = 3
                e = cp[ci] if ci < len(cp) else None
                if e and e[0] in ("long", "double"): val = cls["const"](ci)
            elif op == 0x10:
                val = struct.unpack_from(">b", code, j+1)[0]; adv = 2
            elif op == 0x11:
                val = struct.unpack_from(">h", code, j+1)[0]; adv = 3
            elif op in LOADS: val = LOADS[op]; adv = 1
            elif op in FCONST: val = FCONST[op]; adv = 1
            elif op in LCONST: val = LCONST[op]; adv = 1
            elif op in DCONST: val = DCONST[op]; adv = 1
            if val is not None and adv:
                k = j + adv
                if k + 2 < n and code[k] in (0xb5, 0xb3):
                    fr = struct.unpack_from(">H", code, k+1)[0]
                    e = cp[fr] if fr < len(cp) else None
                    if e and e[0] == 9:
                        nat = cp[e[1][1]]
                        if nat and nat[0] == 12:
                            res.append((cls["utf"](nat[1][0]), val))
                i = k
                continue
            i += 1
    return res

def collect(data, want):
    cls = parse_class(data)
    out = {}
    for f in cls["fields"]:
        out[f["name"]] = {"desc": f["desc"], "const": f["const"], "default": None}
    for fname, val in scan_pairs(cls):
        if fname in out and out[fname]["default"] is None:
            out[fname]["default"] = val
    if want:
        out = {k: v for k, v in out.items() if k in want}
    return out

def dump_consts(data):
    """按方法顺序列出所有被加载的常量（用于读枚举构造参数等非字段默认值）。"""
    cls = parse_class(data)
    out = {}
    for m in cls["methods"]:
        code = m.get("code")
        if not code: continue
        vals = []
        i = 0; n = len(code); cp = cls["cp"]
        while i < n:
            op = code[i]
            v = None; adv = 1
            if op == 0x12:
                ci = code[i+1]; adv = 2
                e = cp[ci] if ci < len(cp) else None
                if e and e[0] in ("int", "float"): v = cls["const"](ci)
                elif e and e[0] == 8: v = cls["utf"](e[1])
            elif op == 0x13:
                ci = struct.unpack_from(">H", code, i+1)[0]; adv = 3
                e = cp[ci] if ci < len(cp) else None
                if e and e[0] in ("int", "float"): v = cls["const"](ci)
                elif e and e[0] == 8: v = cls["utf"](e[1])
            elif op == 0x14:
                ci = struct.unpack_from(">H", code, i+1)[0]; adv = 3
                e = cp[ci] if ci < len(cp) else None
                if e and e[0] in ("long", "double"): v = cls["const"](ci)
            elif op == 0x10:
                v = struct.unpack_from(">b", code, i+1)[0]; adv = 2
            elif op == 0x11:
                v = struct.unpack_from(">h", code, i+1)[0]; adv = 3
            elif op in LOADS: v = LOADS[op]
            elif op in FCONST: v = FCONST[op]
            elif op in DCONST: v = DCONST[op]
            if v is not None: vals.append(v)
            i += adv
        out[m["name"] + m["desc"]] = vals
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jar", required=True)
    ap.add_argument("--fields", default="")
    ap.add_argument("--fields-file", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--list", default="")
    ap.add_argument("--dump-consts", default="")
    a = ap.parse_args()

    specs = [s for s in a.fields.split(",") if s.strip()]
    if a.fields_file:
        with open(a.fields_file, encoding="utf-8") as fh:
            specs += [l.strip() for l in fh if l.strip() and not l.startswith("#")]
    byclass = {}
    for s in specs:
        c, _, f = s.partition("#")
        byclass.setdefault(c, set()).add(f)

    if a.dump_consts:
        with zipfile.ZipFile(a.jar) as z:
            print(json.dumps(dump_consts(z.read(a.dump_consts.replace(".", "/") + ".class")), ensure_ascii=False, indent=1))
        return

    result = {}
    with zipfile.ZipFile(a.jar) as z:
        names = set(z.namelist())
        targets = list(byclass) if byclass else ([a.list] if a.list else [])
        for c in targets:
            entry = c.replace(".", "/") + ".class"
            if entry not in names:
                result[c] = {"__error__": "class not found in jar"}
                continue
            result[c] = collect(z.read(entry), byclass.get(c))
    text = json.dumps(result, ensure_ascii=False, indent=1, sort_keys=True)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh: fh.write(text)
        print("wrote %s (%d classes)" % (a.out, len(result)))
    else:
        print(text)

if __name__ == "__main__":
    main()
