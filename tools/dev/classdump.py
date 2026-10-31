"""
classdump.py -- minimal JVM class-file parser + bytecode scanner.

Written to answer: "what does MindustryX's patched LogicBlock set
maxInstructionsPerTick to, given the vanilla default is 40?"
"""
from __future__ import annotations

import io
import struct


def parse(data: bytes):
    """Return (major_version, {cp_index: (kind, value)}, [(name, desc, code_bytes)])."""
    f = io.BytesIO(data)
    magic, minor, major = struct.unpack(">IHH", f.read(8))
    if magic != 0xCAFEBABE:
        raise ValueError("not a class file")
    cp_count = struct.unpack(">H", f.read(2))[0]

    pool: dict[int, tuple[str, object]] = {}
    i = 1
    while i < cp_count:
        tag = f.read(1)[0]
        if tag == 1:                                        # CONSTANT_Utf8
            ln = struct.unpack(">H", f.read(2))[0]
            pool[i] = ("utf8", f.read(ln).decode("utf-8", "replace"))
        elif tag in (3, 4):                                 # Integer / Float
            pool[i] = ("int", struct.unpack(">i", f.read(4))[0])
        elif tag in (5, 6):                                 # Long / Double (2 slots)
            pool[i] = ("long", struct.unpack(">q", f.read(8))[0])
            i += 1
        elif tag in (7, 8, 16, 19, 20):                     # Class/String/MethodType/Module/Package
            pool[i] = ("ref", struct.unpack(">H", f.read(2))[0])
        elif tag == 15:                                     # MethodHandle
            pool[i] = ("mh", f.read(3))
        elif tag in (9, 10, 11, 12, 17, 18):               # refs / NameAndType / Dynamic
            pool[i] = ("pair", struct.unpack(">HH", f.read(4)))
        else:
            raise ValueError(f"unknown constant pool tag {tag} at index {i}")
        i += 1

    struct.unpack(">H", f.read(2))                          # access_flags
    struct.unpack(">H", f.read(2))                          # this_class
    struct.unpack(">H", f.read(2))                          # super_class
    f.read(2 * struct.unpack(">H", f.read(2))[0])           # interfaces

    def skip_attributes(count: int):
        for _ in range(count):
            struct.unpack(">H", f.read(2))                  # attribute_name_index
            ln = struct.unpack(">I", f.read(4))[0]
            f.read(ln)

    for _ in range(struct.unpack(">H", f.read(2))[0]):      # fields
        f.read(6)                                           # access, name, desc
        skip_attributes(struct.unpack(">H", f.read(2))[0])

    methods = []
    for _ in range(struct.unpack(">H", f.read(2))[0]):
        acc, name_i, desc_i = struct.unpack(">HHH", f.read(6))
        attr_count = struct.unpack(">H", f.read(2))[0]
        code = None
        for _ in range(attr_count):
            name_idx = struct.unpack(">H", f.read(2))[0]
            ln = struct.unpack(">I", f.read(4))[0]
            body = f.read(ln)
            if pool.get(name_idx, ("", ""))[1] == "Code":
                code = body
        methods.append((pool.get(name_i, ("", ""))[1],
                        pool.get(desc_i, ("", ""))[1], code))
    return major, pool, methods


def code_bytes(code_attr: bytes) -> bytes:
    """Extract the raw bytecode array from a Code attribute body."""
    max_stack, max_locals = struct.unpack(">HH", code_attr[:4])
    length = struct.unpack(">I", code_attr[4:8])[0]
    return code_attr[8:8 + length]


def names_of(pool) -> dict[int, str]:
    return {k: v[1] for k, v in pool.items() if v[0] == "utf8"}


def scan(pool, code: bytes):
    """Linear bytecode walk yielding (pc, opname, operand) for int/field ops."""
    names = names_of(pool)
    b = code_bytes(code)
    pc, out, stack = 0, [], []

    def field_name(idx: int) -> str:
        ref = pool.get(idx)
        if not ref or ref[0] != "ref":
            return "?"
        nt = pool.get(ref[1])
        if not nt or nt[0] != "pair":
            return "?"
        return names.get(nt[1][0], "?")

    while pc < len(b):
        op = b[pc]
        if op == 0x10:                                       # bipush
            stack.append(b[pc + 1] if b[pc + 1] < 128 else b[pc + 1] - 256)
            out.append((pc, "bipush", stack[-1])); pc += 2
        elif op == 0x11:                                     # sipush
            stack.append(struct.unpack(">h", b[pc + 1:pc + 3])[0])
            out.append((pc, "sipush", stack[-1])); pc += 3
        elif 0x02 <= op <= 0x08:                             # iconst_<n>
            stack.append(op - 3); out.append((pc, "iconst", op - 3)); pc += 1
        elif op == 0x12:
            v = pool.get(b[pc + 1])
            val = v[1] if v and v[0] == "int" else "?"
            stack.append(val); out.append((pc, "ldc", val)); pc += 2
        elif op == 0x13:
            v = pool.get(struct.unpack(">H", b[pc + 1:pc + 3])[0])
            val = v[1] if v and v[0] == "int" else "?"
            stack.append(val); out.append((pc, "ldc_w", val)); pc += 3
        elif op in (0xb5, 0xb3):                             # putfield / putstatic
            idx = struct.unpack(">H", b[pc + 1:pc + 3])[0]
            val = stack[-1] if stack else "?"
            out.append((pc, "putfield" if op == 0xb5 else "putstatic",
                        (field_name(idx), val)))
            pc += 3
        elif op == 0x84:
            pc += 3
        elif 0x99 <= op <= 0xa8 or op in (0xc6, 0xc7):
            pc += 3
        elif op in (0xb2, 0xb4, 0xb6, 0xb7, 0xb8, 0xb9, 0xba,
                    0xbb, 0xbd, 0xc0, 0xc1, 0xbc):
            pc += 3
        elif op == 0xc5:
            pc += 4
        elif op in (0xaa, 0xab):
            pad = (4 - ((pc + 1) % 4)) % 4
            pc += 1 + pad
            if op == 0xaa:
                lo, hi = struct.unpack(">ii", b[pc + 4:pc + 12])
                pc += 12 + 4 * (hi - lo + 1)
            else:
                n = struct.unpack(">i", b[pc + 4:pc + 8])[0]
                pc += 8 + 8 * n
        elif op == 0xc4:
            pc += 6 if b[pc + 1] == 0x84 else 4
        else:
            pc += 1
    return out


if __name__ == "__main__":
    import sys
    import zipfile

    jar = sys.argv[1]
    zf = zipfile.ZipFile(jar)
    for cls in sys.argv[2:]:
        try:
            major, pool, methods = parse(zf.read(cls))
        except Exception as e:
            print(f"!! {cls}: {type(e).__name__}: {e}")
            continue
        print(f"=== {cls} (major {major})")
        for n, d, c in methods:
            if not c:
                continue
            pairs = [o for o in scan(pool, c)
                     if o[1] in ("putfield", "putstatic")
                     and isinstance(o[2][1], int) and o[2][1] > 1]
            for pc, _, (fname, val) in pairs:
                print(f"   {n}{d} @{pc}: {fname} = {val}")
