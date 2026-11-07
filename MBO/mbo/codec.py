"""L1：`.msch` 编解码。

解析复用 `tools/msch.py`（全语料 831/833 可解析，已验证）；写回用本模块的完整
TypeIO 写入器——stock 的 `msch.build_schematic` 只能往返 **27.68%**，因为缺数组分支
（电力节点的 Point2[] links 就卡在这）。

解析时把 TypeIO 标签号保留在 `TaggedList` / `TaggedDouble` 上，否则写回会丢
`6/8/16/18/21/22` 之间的区别（见 docs/10 §2）。
"""

from __future__ import annotations

import os
import struct
import sys
import zlib

from .gamedata import MBO_ROOT

REPO_ROOT = os.path.dirname(MBO_ROOT)
TOOLS = os.path.join(REPO_ROOT, "tools")
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)

import msch  # noqa: E402  （工作区已验证的解析器，禁止修改）

MAGIC = b"msch"
CURRENT_VERSION = 1


class TaggedList(list):
    """带 TypeIO 标签的 list（6=IntSeq / 8=Point2[] / 16=bool[] / 21=int[] / 22=Object[]）。"""

    __slots__ = ("tag",)

    def __init__(self, items=(), tag=None):
        super().__init__(items)
        self.tag = tag


class TaggedDouble(float):
    """T_DOUBLE(11) 与 T_FLOAT(3) 都读成 float，写回时要靠标签区分。"""

    __slots__ = ("tag",)

    def __new__(cls, value, tag=11):
        obj = float.__new__(cls, value)
        obj.tag = tag
        return obj


_orig_read_object = msch._read_object


def _tagged_read_object(r, depth=0):
    tag = r.data[r.pos] if r.pos < len(r.data) else None
    obj = _orig_read_object(r, depth)
    if depth == 0 and isinstance(obj, list) and not isinstance(obj, TaggedList):
        obj = TaggedList(obj, tag)
    elif depth == 0 and isinstance(obj, float) and not isinstance(obj, bool) and tag == 11:
        obj = TaggedDouble(obj, 11)
    return obj


if not getattr(msch, "_mbo_tagged", False):
    msch._read_object = _tagged_read_object
    msch._mbo_tagged = True


# ---------------------------------------------------------------- 读
def read(path: str):
    """解析 .msch → `msch.Schematic`（tile 坐标为中心格，config 带标签）。"""
    return msch.parse_file(path)


def read_bytes(data: bytes):
    return msch.parse_bytes(data)


def to_base64(data: bytes) -> str:
    import base64

    return base64.b64encode(data).decode("ascii")


# ---------------------------------------------------------------- 写
def _write_object(out: bytearray, obj) -> None:
    """TypeIO.writeObject 的完整版（分支依据 Mindustry-Source core/src/mindustry/io/TypeIO.java）。"""
    if obj is None:
        out.append(0)
    elif isinstance(obj, bool):
        out.append(10)
        out.append(1 if obj else 0)
    elif isinstance(obj, int):
        out.append(1)
        out += struct.pack(">i", obj)
    elif isinstance(obj, float):
        if getattr(obj, "tag", None) == 11:
            out.append(11)
            out += struct.pack(">d", float(obj))
        else:
            out.append(3)
            out += struct.pack(">f", float(obj))
    elif isinstance(obj, str):
        out.append(4)
        out.append(1)
        sb = obj.encode("utf-8")
        out += struct.pack(">H", len(sb)) + sb
    elif isinstance(obj, (bytes, bytearray)):
        out.append(14)
        out += struct.pack(">i", len(obj)) + bytes(obj)
    elif isinstance(obj, dict) and "__content__" in obj:
        out.append(5)
        out.append(msch.CONTENT_TYPES.index(obj["__content__"]))
        out += struct.pack(">h", obj["id"])
    elif isinstance(obj, dict) and "__point__" in obj:
        out.append(7)
        out += struct.pack(">ii", *obj["__point__"])
    elif isinstance(obj, dict) and "__technode__" in obj:
        ctype, cid = obj["__technode__"]
        out.append(9)
        out.append(ctype)
        out += struct.pack(">h", cid)
    elif isinstance(obj, dict) and "__building__" in obj:
        out.append(12)
        out += struct.pack(">i", obj["__building__"])
    elif isinstance(obj, dict) and "__laccess__" in obj:
        out.append(13)
        out += struct.pack(">h", obj["__laccess__"])
    elif isinstance(obj, dict) and "__unit__" in obj:
        out.append(17)
        out += struct.pack(">i", obj["__unit__"])
    elif isinstance(obj, dict) and "__vec2__" in obj:
        out.append(19)
        out += struct.pack(">ff", *obj["__vec2__"])
    elif isinstance(obj, dict) and "__team__" in obj:
        out.append(20)
        out.append(obj["__team__"] & 0xFF)
    elif isinstance(obj, dict) and "__unitcommand__" in obj:
        out.append(23)
        out += struct.pack(">H", obj["__unitcommand__"])
    elif isinstance(obj, (list, tuple)):
        tag = getattr(obj, "tag", None) or 6
        if tag in (6, 21):
            out.append(tag)
            out += struct.pack(">h", len(obj))
            for v in obj:
                out += struct.pack(">i", v)
        elif tag == 8:
            # Point2[]：byte 长度 + 每元素 4 字节 packed（注意坐标可能 >0x7FFF，
            # 必须用 ">I" 并先 & 0xFFFFFFFF，stock 的 ">i" 会溢出）
            out.append(8)
            out.append(len(obj) & 0xFF)
            for v in obj:
                if isinstance(v, dict) and "__point__" in v:
                    vx, vy = v["__point__"]
                elif isinstance(v, (tuple, list)) and len(v) == 2:
                    vx, vy = v
                else:
                    out += struct.pack(">i", v)
                    continue
                out += struct.pack(">I", (((vx & 0xFFFF) << 16) | (vy & 0xFFFF)) & 0xFFFFFFFF)
        elif tag == 16:
            out.append(16)
            out += struct.pack(">i", len(obj))
            for v in obj:
                out.append(1 if v else 0)
        elif tag == 18:
            out.append(18)
            out += struct.pack(">h", len(obj))
            for v in obj:
                vx, vy = v["__vec2__"] if isinstance(v, dict) else v
                out += struct.pack(">ff", vx, vy)
        elif tag == 22:
            out.append(22)
            out += struct.pack(">i", len(obj))
            for v in obj:
                _write_object(out, v)
        else:
            raise msch.MschError("unsupported array tag %s" % tag)
    else:
        raise msch.MschError("cannot serialize config of type %s" % type(obj).__name__)


def build_schematic_ext(sch) -> bytes:
    """完整写回器：`msch.Schematic` → .msch 字节（含 zlib 压缩）。"""
    body = bytearray()
    body += struct.pack(">hh", sch.width, sch.height)

    body.append(len(sch.tags) & 0xFF)
    for k, v in sch.tags.items():
        for s in (k, v):
            sb = str(s).encode("utf-8")
            body += struct.pack(">H", len(sb)) + sb

    names: list[str] = []
    for t in sch.tiles:
        if t.block not in names:
            names.append(t.block)
    body.append(len(names) & 0xFF)
    for n in names:
        nb = n.encode("utf-8")
        body += struct.pack(">H", len(nb)) + nb

    body += struct.pack(">i", len(sch.tiles))
    for t in sch.tiles:
        body.append(names.index(t.block) & 0xFF)
        body += struct.pack(">i", ((t.x & 0xFFFF) << 16) | (t.y & 0xFFFF))
        _write_object(body, t.config)
        body.append(t.rotation & 0xFF)

    return MAGIC + bytes([CURRENT_VERSION]) + zlib.compress(bytes(body), 9)


def write(path: str, sch) -> bytes:
    data = build_schematic_ext(sch)
    with open(path, "wb") as fh:
        fh.write(data)
    return data


def body_of(data: bytes) -> bytes:
    """取出未压缩 body（往返保真度比对用）。"""
    if data[:4] != MAGIC:
        raise ValueError("not an msch file")
    return zlib.decompress(data[5:])


def semantic_tiles(sch) -> list:
    """(block, x, y, rotation, canon(config)) 排序列表，用于语义比对。"""
    return sorted(
        (t.block, t.x, t.y, t.rotation, canon(t.config))
        for t in sch.tiles
        if t.block != "air"
    )


def canon(obj):
    if isinstance(obj, dict):
        return tuple(sorted((k, canon(v)) for k, v in obj.items()))
    if isinstance(obj, (list, tuple)):
        return tuple(canon(v) for v in obj)
    if isinstance(obj, (bytes, bytearray)):
        return ("bytes", len(obj), zlib.crc32(bytes(obj)))
    if isinstance(obj, float):
        return round(float(obj), 6)
    return obj
