"""fieldaccess.py —— 全库统计某个字段的 getfield/putfield 访问点

用法: python fieldaccess.py <字段名> [--mods]
原理: 解析 class 常量池 -> 找出 Fieldref(name==字段名) 的 cp 索引集合
      -> 定界每个方法的 Code 段 -> 在 Code 字节里扫 0xB4/0xB5 + u2 索引
      命中即为一次字段访问，同时报告所属方法与字节码偏移。
"""
import sys, os, struct, zipfile, io

JAR = r'E:\Program Files (x86)\Steam\steamapps\common\Mindustry\jre\desktop.jar'
MODS = r'E:\Program Files (x86)\Steam\steamapps\common\Mindustry\saves\mods'


def parse_cp(c):
    """返回 (cp, endpos)。cp[i] = (tag, payload)"""
    n = struct.unpack_from('>H', c, 8)[0]
    p = 10
    cp = [None] * n
    i = 1
    while i < n:
        tag = c[p]; p += 1
        if tag == 1:
            L = struct.unpack_from('>H', c, p)[0]; p += 2
            cp[i] = (1, c[p:p + L].decode('utf-8', 'replace')); p += L
        elif tag in (7, 8, 16, 19, 20):
            cp[i] = (tag, struct.unpack_from('>H', c, p)[0]); p += 2
        elif tag == 15:
            cp[i] = (tag, struct.unpack_from('>BH', c, p)[0:3]); p += 3
        elif tag in (3, 4):
            cp[i] = (tag, c[p:p + 4]); p += 4
        elif tag in (9, 10, 11, 12, 17, 18):
            cp[i] = (tag, struct.unpack_from('>HH', c, p)); p += 4
        elif tag in (5, 6):
            cp[i] = (tag, c[p:p + 8]); p += 8; i += 1
        else:
            raise ValueError('bad cp tag %d at %d' % (tag, p))
        i += 1
    return cp, p


def utf(cp, i):
    e = cp[i]
    return e[1] if e and e[0] == 1 else None


def attr_iter(c, p, count):
    for _ in range(count):
        name_i, alen = struct.unpack_from('>HI', c, p); p += 6
        yield utf(cp_ref, name_i), c[p:p + alen]
        p += alen


def scan_class(c, fieldname):
    """返回 [(方法签名, 'READ'/'WRITE', 偏移)]"""
    out = []
    cp, p = parse_cp(c)
    global cp_ref
    cp_ref = cp
    # 目标 Fieldref 索引
    targets = {}
    for i, e in enumerate(cp):
        if not e or e[0] != 9:  # 9 = CONSTANT_Fieldref
            continue
        cls_i, nt_i = e[1]
        nt = cp[nt_i]
        if not nt or nt[0] != 12:
            continue
        nm, desc = utf(cp, nt[1][0]), utf(cp, nt[1][1])
        if nm == fieldname:
            targets[i] = (utf(cp, cp[cls_i][1]), desc)
    if not targets:
        return out
    # 跳过 access/this/super 与接口表
    p += 6
    ic = struct.unpack_from('>H', c, p)[0]; p += 2 + ic * 2
    # fields
    fc = struct.unpack_from('>H', c, p)[0]; p += 2
    for _ in range(fc):
        p += 6
        ac = struct.unpack_from('>H', c, p)[0]; p += 2
        for _n, _d in attr_iter(c, p, ac):
            pass
        p = _skip_attrs(c, p, ac)
    # methods
    mc = struct.unpack_from('>H', c, p)[0]; p += 2
    for _ in range(mc):
        af, nm_i, de_i, ac = struct.unpack_from('>HHHH', c, p); p += 8
        mname = utf(cp, nm_i) + utf(cp, de_i)
        body = c[p:p + 1]  # 占位
        attrs_start = p
        code = None
        q = p
        for k in range(ac):
            an_i, alen = struct.unpack_from('>HI', c, q); q += 6
            if utf(cp, an_i) == 'Code':
                code = c[q:q + alen]
            q += alen
        if code is not None:
            clen = struct.unpack_from('>I', code, 4)[0]
            bc = code[8:8 + clen]
            for off in range(len(bc) - 2):
                op = bc[off]
                if op in (0xB4, 0xB5):
                    idx = struct.unpack_from('>H', bc, off + 1)[0]
                    if idx in targets:
                        out.append((mname, 'READ' if op == 0xB4 else 'WRITE',
                                    off, targets[idx][0] + '.' + targets[idx][1]))
                elif op in (0xB2, 0xB3):  # getstatic/putstatic
                    idx = struct.unpack_from('>H', bc, off + 1)[0]
                    if idx in targets:
                        out.append((mname, 'READ-STATIC' if op == 0xB2 else 'WRITE-STATIC',
                                    off, targets[idx][0] + '.' + targets[idx][1]))
        p = _skip_attrs(c, attrs_start, ac)
    return out


def _skip_attrs(c, p, count):
    for _ in range(count):
        _, alen = struct.unpack_from('>HI', c, p); p += 6 + alen
    return p


def main():
    field = sys.argv[1]
    print('扫描字段: %s\n' % field)
    total = 0

    def do(src, zf):
        nonlocal total
        for nm in zf.namelist():
            if not nm.endswith('.class'):
                continue
            try:
                data = zf.read(nm)
            except Exception:
                continue
            if field.encode() not in data:
                continue
            try:
                res = scan_class(data, field)
            except Exception as ex:
                print('  !! 解析失败 %s: %s' % (nm, ex)); continue
            for m, kind, off, owner in res:
                total += 1
                print('  [%s] %s' % (src, nm[:-6].replace('/', '.')))
                print('      %-8s %-50s @%d   owner=%s' % (kind, m, off, owner))

    with zipfile.ZipFile(JAR) as zf:
        do('desktop.jar', zf)
    if '--mods' in sys.argv:
        for f in sorted(os.listdir(MODS)):
            if not f.lower().endswith(('.zip', '.jar')):
                continue
            try:
                with zipfile.ZipFile(os.path.join(MODS, f)) as zf:
                    do(f, zf)
            except Exception:
                pass
    print('\n共 %d 处字段访问。' % total)


if __name__ == '__main__':
    main()
