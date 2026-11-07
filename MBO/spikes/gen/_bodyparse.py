"""解析 .msch body：tags / 方块字典 / tile 列表（探针用，独立于 mbo.codec）。

config 用最小 TypeIO 跳过器（覆盖语料与生成器实际出现的 tag：
0 null / 1 int / 3 float / 4 string / 5 content / 7 point / 8 point[] / 10 bool / 11 double /
14 byte[] / 6,21 int[] / 16 bool[] / 18 vec2[] / 22 object[]）。
"""
import io as _io
import struct


def skip_obj(f):
    tag = f.read(1)[0]
    if tag == 0:
        return None
    if tag == 1:
        f.read(4)
    elif tag == 3:
        f.read(4)
    elif tag == 11:
        f.read(8)
    elif tag == 4:
        n = struct.unpack(">H", f.read(2))[0]
        f.read(n)
    elif tag == 5:
        f.read(1)
        f.read(2)
    elif tag == 7:
        f.read(4)
    elif tag == 10:
        f.read(1)
    elif tag == 14:
        n = struct.unpack(">i", f.read(4))[0]
        f.read(n)
    elif tag in (6, 21):
        n = struct.unpack(">h", f.read(2))[0]
        f.read(4 * n)
    elif tag == 16:
        n = struct.unpack(">i", f.read(4))[0]
        f.read(n)
    elif tag == 8:
        n = f.read(1)[0]
        f.read(4 * n)
    elif tag == 18:
        n = struct.unpack(">h", f.read(2))[0]
        f.read(8 * n)
    elif tag == 22:
        n = struct.unpack(">i", f.read(4))[0]
        for _ in range(n):
            skip_obj(f)
    else:
        raise ValueError("unknown TypeIO tag %d" % tag)


def parse_body(body: bytes):
    f = _io.BytesIO(body)
    w = struct.unpack(">h", f.read(2))[0]
    h = struct.unpack(">h", f.read(2))[0]
    ntag = f.read(1)[0]
    tags = {}
    for _ in range(ntag):
        k = f.read(struct.unpack(">h", f.read(2))[0]).decode("utf-8")
        v = f.read(struct.unpack(">h", f.read(2))[0]).decode("utf-8", "replace")
        tags[k] = v
    ndict = f.read(1)[0]
    names = []
    for _ in range(ndict):
        names.append(f.read(struct.unpack(">h", f.read(2))[0]).decode("utf-8"))
    total = struct.unpack(">i", f.read(4))[0]
    tiles = []
    for _ in range(total):
        idx = struct.unpack(">b", f.read(1))[0]
        packed = struct.unpack(">i", f.read(4))[0]
        skip_obj(f)
        rot = struct.unpack(">b", f.read(1))[0]
        tiles.append((names[idx], packed & 0xFFFF, packed >> 16, rot))
    return w, h, tags, names, sorted(tiles)
