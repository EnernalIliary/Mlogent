"""Wrap `out/landing-scheduler.mlog` back into the user's `tst` blueprint layout.

The block layout is copied verbatim from their test schematic: six landing pads at
(1,1) (1,5) (1,9) (6,1) (6,5) (6,9), one micro-processor at (4,4), links pad1..pad6
in the same order the original file used. Only the logic is new.
"""
import base64
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "mindustry-blueprint" / "tools"))
import msch  # noqa: E402
import mschgen  # noqa: E402

C = pathlib.Path.home() / "AppData" / "Roaming" / "Mindustry" / "schematics"
NAME = "着陆调度-最低库存"
CODE = HERE / "out" / "landing-scheduler.mlog"
OUT = HERE / "out" / f"{NAME}.msch"

PADS = [
    ("pad1", 1, 1), ("pad2", 1, 5), ("pad3", 1, 9),
    ("pad4", 6, 9), ("pad5", 6, 5), ("pad6", 6, 1),
]
PX, PY = 4, 4


def main() -> None:
    code = CODE.read_text("utf-8")
    bp = mschgen.Blueprint(
        name=NAME,
        description="[lightgray]6 个着陆板都请求核心库存 [#ffb6c1]最少[] 的资源。"
                    "[]\n[lightgray]优先读链接 [#ffb6c1]core1[];没这个链接就 "
                    "[#ffb6c1]ubind @flare[] + [#ffb6c1]ulocate[] 找核心"
                    "(需要规则允许单位控制、且场上有该单位)。"
                    "[]\n[lightgray]只在资源变化时才写 config,不刷方块。"
                    "[]\n[lightgray]逻辑 by [#8abcd1]DeepSeek[]",
        labels=["[blue]DeepSeek"],
    )
    bp.add_logic(code, PX, PY, block="micro-processor",
                 links=[mschgen.Link(n, x - PX, y - PY) for n, x, y in PADS])
    for _, x, y in PADS:
        bp.add_block("landing-pad", x, y)
    bp.write(str(OUT))

    sch = msch.parse_file(str(OUT))
    back = "\n".join(t.logic.code for t in sch.logic_tiles())
    assert back == code, "logic round-trip failed"
    assert [t.block for t in sch.tiles].count("landing-pad") == 6
    print(f"ok  {len(sch.tiles)} blocks, labels={sch.labels}")
    print(f"ok  links: {[(l.name, l.x, l.y) for l in sch.logic_tiles()[0].logic.links]}")

    if "--install" in sys.argv:
        dst = C / OUT.name
        shutil.copy2(OUT, dst)
        assert msch.parse_file(str(dst)).labels == ["[blue]DeepSeek"]
        print(f"已安装: {dst}")
    else:
        print("(未安装, 加 --install)")

    print("\n--- 蓝图码 ---")
    # The whole file is simply base64'd; that string *is* what the game pastes.
    # An earlier version prepended a 9-char prefix and stripped 8 chars, which
    # made the length 1 (mod 4) and the game refused it with
    # "Length of Base64 encoded input string is not a multiple of 4".
    code64 = base64.b64encode(OUT.read_bytes()).decode()
    assert len(code64) % 4 == 0, len(code64)
    assert msch.parse_base64(code64).labels == ["[blue]DeepSeek"]
    print(code64)


if __name__ == "__main__":
    main()
