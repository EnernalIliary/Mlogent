"""fieldaccess2.py —— 列出某个类里所有访问指定字段的方法与字节码偏移

用法: python fieldaccess2.py <全限定类名> <字段名> [zip路径]
输出: 方法签名 | READ/WRITE | 字节码偏移 | owner.字段
"""
import sys, struct, zipfile

JAR = r'E:\Program Files (x86)\Steam\steamapps\common\Mindustry\jre\desktop.jar'


def parse_cp(c):
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
            cp[i] = (tag, struct.unpack_from('>BH', c, p)); p += 3
        elif tag in (3, 4):
            cp[i] = (tag, c[p:p + 4]); p += 4
        elif tag in (9, 10, 11, 12, 17, 18):
            cp[i] = (tag, struct.unpack_from('>HH', c, p)); p += 4
        elif tag in (5, 6):
            cp[i] = (tag, c[p:p + 8]); p += 8; i += 1
        else:
            raise ValueError('bad cp tag %d' % tag)
        i += 1
    return cp, p


def utf(cp, i):
    e = cp[i] if 0 < i < len(cp) else None
    return e[1] if e and e[0] == 1 else None


def skip_attrs(c, p, count):
    for _ in range(count):
        _, alen = struct.unpack_from('>HI', c, p); p += 6 + alen
    return p


def scan(c, fieldname):
    cp, p = parse_cp(c)
    targets = {}
    for i, e in enumerate(cp):
        if not e or e[0] != 9:
            continue
        cls_i, nt_i = e[1]
        nt = cp[nt_i]
        if not nt or nt[0] != 12:
            continue
        nm, desc = utf(cp, nt[1][0]), utf(cp, nt[1][1])
        if nm == fieldname:
            targets[i] = utf(cp, cp[cls_i][1]) + '.' + desc
    out = []
    p += 6
    ic = struct.unpack_from('>H', c, p)[0]; p += 2 + ic * 2
    fc = struct.unpack_from('>H', c, p)[0]; p += 2
    for _ in range(fc):
        ac = struct.unpack_from('>H', c, p + 6)[0]
        p = skip_attrs(c, p + 6, ac)
    mc = struct.unpack_from('>H', c, p)[0]; p += 2
    for _ in range(mc):
        af, nm_i, de_i, ac = struct.unpack_from('>HHHH', c, p); p += 8
        mname = (utf(cp, nm_i) or '?') + (utf(cp, de_i) or '')
        q = p
        for k in range(ac):
            an_i, alen = struct.unpack_from('>HI', c, q); q += 6
            if utf(cp, an_i) == 'Code':
                code = c[q:q + alen]
                clen = struct.unpack_from('>I', code, 4)[0]
                bc = code[8:8 + clen]
                for off in range(len(bc) - 2):
                    op = bc[off]
                    if op in (0xB2, 0xB3, 0xB4, 0xB5):
                        idx = struct.unpack_from('>H', bc, off + 1)[0]
                        if idx in targets:
                            kind = {0xB2: 'READ-static', 0xB3: 'WRITE-static',
                                    0xB4: 'READ', 0xB5: 'WRITE'}[op]
                            out.append((mname, kind, off, targets[idx]))
            q += alen
        p = skip_attrs(c, p, ac)
    return out, targets


def main():
    clsname = sys.argv[1]
    field = sys.argv[2]
    src = sys.argv[3] if len(sys.argv) > 3 else JAR
    entry = clsname.replace('.', '/') + '.class'
    with zipfile.ZipFile(src) as zf:
        c = zf.read(entry)
    out, targets = scan(c, field)
    print('类 %s 中对字段 %s 的访问：' % (clsname, field))
    if not targets:
        print('  （常量池里没有该名字段的 Fieldref —— 此字段未被本类直接访问）')
    for m, k, off, owner in out:
        print('  %-9s @%-6d %-46s  owner=%s' % (k, off, m, owner))
    print('  共 %d 处。' % len(out))


if __name__ == '__main__':
    main()
