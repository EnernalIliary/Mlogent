"""
scan_mod_blocks.py -- find which installed mods actually REGISTER new blocks.

Registering new content shifts Content.id for everything constructed after it,
which is exactly why a vanilla id table may not match a modded install.

We look for bytecode that constructs a Block subclass and calls a name setter,
i.e. the `new SomeBlock("block-name")` idiom used by every Mindustry mod.
"""
from __future__ import annotations

import collections
import glob
import os
import re
import struct
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from classdump import parse, code_bytes  # noqa: E402

MODS = r"C:\Users\lliary\AppData\Roaming\Mindustry\mods"

# A content-name string in a mod usually looks like "some-block-name".
NAMEISH = re.compile(rb"^[a-z][a-z0-9]*(-[a-z0-9]+)+$")

# superclasses/names that indicate block registration
BLOCK_SUPER = (b"mindustry/world/Block", b"mindustry/world/blocks/")


def class_string_constants(data: bytes) -> list[str]:
    """All UTF8 constants in a class file (cheap string-pool read)."""
    out = []
    for m in re.finditer(rb"[\x01][\x00](.)([\x20-\x7e]{3,60})", data):
        try:
            out.append(m.group(2).decode("ascii"))
        except Exception:
            pass
    return out


def scan_jar(path: str) -> dict:
    res = {"entries": 0, "block_classes": 0, "name_like": set(), "samples": []}
    try:
        zf = zipfile.ZipFile(path)
    except Exception:
        return res
    for n in zf.namelist():
        if not n.endswith(".class"):
            continue
        res["entries"] += 1
        try:
            data = zf.read(n)
        except Exception:
            continue
        is_block = any(s in data for s in BLOCK_SUPER)
        if is_block:
            res["block_classes"] += 1
        # collect lowercase-hyphen names (candidate content ids)
        for s in class_string_constants(data):
            if NAMEISH.match(s.encode()):
                res["name_like"].add(s)
                if len(res["samples"]) < 8:
                    res["samples"].append(s)
    return res


def main() -> None:
    files = sorted(glob.glob(os.path.join(MODS, "*.zip")) +
                   glob.glob(os.path.join(MODS, "*.jar")))
    print(f"mods dir: {len(files)} archives\n")
    rows = []
    for f in files:
        r = scan_jar(f)
        if r["block_classes"] or r["name_like"]:
            rows.append((os.path.basename(f), r))

    rows.sort(key=lambda kv: -kv[1]["block_classes"])
    for name, r in rows:
        names = sorted(r["name_like"])
        print(f"{name}")
        print(f"    classes touching Block : {r['block_classes']}")
        print(f"    hyphen-name strings    : {len(names)}")
        if names:
            show = ", ".join(names[:14])
            print(f"    e.g. {show}")


if __name__ == "__main__":
    main()
