"""用游戏自己的 API 交叉验证编码层（docs: mindustry.game.Schematics）。

headless 服务端上的可用性（实测）：
  - `Schematics.readBase64` / `Schematics.place` / `Schematics.rotate`：静态，可用
  - `Vars.schematics` 是 **null**（服务端没加载该 manager）→ 必须自己 `new Schematics()`
  - `inst.writeBase64(sch)`：可用（真实的官方编码输出，可直接和我们的字节比）
  - `inst.create(x,y,x1,y1)`：headless 下返回 1x1/0 tile，抓不到世界区域（不可用）

做两件事：
  A. 我们的 b64 → 游戏 readBase64 → 游戏 writeBase64 → 解压 body，与我们 body 逐字节比
  B. rotate(sch, 1) 的尺寸/rot 分布（确认旋转语义；以后做变体用）
"""
from __future__ import annotations

import base64
import pathlib
import sys
import time
import zlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "spikes" / "sim"))

import engine_probe as ep  # noqa: E402
from _bodyparse import parse_body  # noqa: E402
from mbo import codec, gamedata, model  # noqa: E402

PX, PY = 64, 64

JS_PARTS = [
    "var S=Packages.mindustry.game.Schematics;var sch=S.readBase64('%(b64)s');",
    "var inst=new S();",
    "var w=inst.writeBase64(sch);",
    "var r=S.rotate(sch,1);",
    "var rb=inst.writeBase64(r);",
    "print('API\\t'+w+'\\t'+rb);",
]
JS = "".join(JS_PARTS)


def build(gd):
    lay = model.Layout(16, 12, {n: b.size for n, b in gd.blocks.items()}, name="api-probe")
    lay.add("item-source", 6, 4, rotation=model.ROT["S"], config=model.item_cfg(gd, "coal"))
    lay.add("underflow-gate", 6, 5)
    lay.add("graphite-press", 4, 5)
    lay.add("graphite-press", 7, 5)
    lay.add("container", 4, 3)
    lay.add("container", 9, 5)
    return lay


def body_of_b64(b64: str) -> bytes:
    raw = base64.b64decode(b64)
    assert raw[:4] == b"msch", raw[:8]
    return zlib.decompress(raw[5:])


def tiles_sig(data: bytes):
    sch = codec.read_bytes(data)
    return (sch.width, sch.height,
            sorted((t.block, t.x, t.y, t.rotation) for t in sch.tiles))


def main():
    gd = gamedata.GameData()
    lay = build(gd)
    data = lay.to_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    our_body = zlib.decompress(data[5:])
    w, h, ours = tiles_sig(data)
    print("layout: %d tiles, %dx%d, ours b64=%d chars" % (len(ours), w, h, len(b64)))

    srv = ep.Server()
    try:
        time.sleep(13)
        srv.js(ep.BP_PREP_JS % {"n": 128})
        srv.js(ep.BP_PLACE_JS % {"b64": b64, "i": 0, "px": PX, "py": PY})
        line = next(ln for ln in srv.js(JS % {"b64": b64}) if ln.startswith("API"))
        parts = line.split("\t")
        game_b64, rot_b64 = parts[1], parts[2]

        game_body = body_of_b64(game_b64)
        print("\nA. 官方 writeBase64: ours=%d B  game=%d B  body_identical=%s"
              % (len(our_body), len(game_body), game_body == our_body))
        print("   ours b64=%d chars  game b64=%d chars  b64_identical=%s"
              % (len(b64), len(game_b64), game_b64 == b64))
        gw, gh, gtags, gnames, gtiles = parse_body(game_body)
        ow, oh, otags, onames, otiles = parse_body(our_body)
        print("   tags: ours=%s" % (otags,))
        print("   tags: game=%s" % ({k: (v[:60] + "...") if len(v) > 60 else v
                                     for k, v in gtags.items()},))
        print("   dict: ours=%s  game=%s" % (onames, gnames))
        print("   tile 层一致=%s（ours=%d game=%d）" % (otiles == gtiles, len(otiles), len(gtiles)))
        print("   w/h 一致=%s" % ((ow, oh) == (gw, gh),))
        if game_body != our_body:
            n = min(len(our_body), len(game_body))
            for i in range(n):
                if our_body[i] != game_body[i]:
                    print("   第一处差异 offset=%d" % i)
                    print("   ours[%d:%d]=%s" % (i, i + 20, our_body[i:i + 20].hex()))
                    print("   game[%d:%d]=%s" % (i, i + 20, game_body[i:i + 20].hex()))
                    break
            if len(our_body) != len(game_body):
                print("   长度不同：ours=%d game=%d" % (len(our_body), len(game_body)))

        rw, rh, rots = tiles_sig(base64.b64decode(rot_b64))
        print("\nB. rotate(sch,1): %dx%d (原 %dx%d), %d tiles" % (rw, rh, w, h, len(rots)))
        print("   sample:", rots[:4])
        print("   rot 值分布:", sorted({r[3] for r in rots}))
        print("   尺寸互换=%s  tile 数守恒=%s" % ((rw, rh) == (h, w), len(rots) == len(ours)))
    finally:
        srv.close()


if __name__ == "__main__":
    main()
