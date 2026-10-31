"""Read field/method names + descriptors out of a class inside the v160 jar.

No javap in the bundled JRE, so parse the constant pool by hand: only what the
fields/methods tables need (tag 1 UTF8, 7 Class, 8 String, 9-12 refs, 3-6 numbers,
15/16/18 handles, 17/19/20 dynamic/condy).
"""
import struct
import sys
import zipfile


def parse(data):
    p = 8
    n = struct.unpack_from('>H', data, p)[0]
    p += 2
    pool = [None] * n
    i = 1
    while i < n:
        tag = data[p]
        p += 1
        if tag == 1:
            ln = struct.unpack_from('>H', data, p)[0]
            pool[i] = data[p + 2:p + 2 + ln].decode('utf-8', 'replace')
            p += 2 + ln
        elif tag in (3, 4):
            p += 4
        elif tag in (5, 6):
            p += 8
            i += 1
        elif tag in (7, 8, 16, 19, 20):
            p += 2
        elif tag in (9, 10, 11, 12, 17, 18):
            p += 4
        elif tag == 15:
            p += 3
        else:
            raise SystemExit('bad tag %d at %d' % (tag, p))
        i += 1
    p += 6                                    # access, this, super
    ifc = struct.unpack_from('>H', data, p)[0]
    p += 2 + 2 * ifc
    out = {'fields': [], 'methods': []}
    for kind in ('fields', 'methods'):
        cnt = struct.unpack_from('>H', data, p)[0]
        p += 2
        for _ in range(cnt):
            acc, ni, di = struct.unpack_from('>HHH', data, p)
            p += 6
            acnt = struct.unpack_from('>H', data, p)[0]
            p += 2
            for _ in range(acnt):
                alen = struct.unpack_from('>I', data, p + 2)[0]
                p += 6 + alen
            out[kind].append((acc, pool[ni], pool[di]))
    return out


def main():
    jar, cls = sys.argv[1], sys.argv[2]
    with zipfile.ZipFile(jar) as z:
        data = z.read(cls + '.class')
    info = parse(data)
    want = sys.argv[3] if len(sys.argv) > 3 else None
    for kind in ('fields', 'methods'):
        for acc, name, desc in info[kind]:
            if want and name != want:
                continue
            print('%-7s %-28s %s' % (kind[:-1], name, desc))


main()
