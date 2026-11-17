"""mapgen -- 把一张图片烤成 Mindustry 地图（.msav），地板用「染色地板」逐格上色。

为什么是染色地板：v8 的 ColoredFloor 把整格 RGBA 存在 tile.extraData 里
(Mindustry-Source/core/src/mindustry/world/blocks/environment/ColoredFloor.java:17-40)，
所以 128x128 的地图 = 128x128 个像素，颜色完全自由，不需要任何 mod。

写档用游戏自己的 SaveIO：这是唯一 100% 匹配 v160.7 存档格式的写入器（第三方
重写要跟 SaveVersion v13 的分块格式，版本一换就废），所以脚本只负责算像素，
再驱动官方 headless 服务端的 js 控制台去 loadGenerator + SaveIO.save。

    python tools/mapgen.py --size 128 --grid 8 --name 大肥鱼的调试世界 -o maps/x.msav
    python tools/mapgen.py --image art.png --fit cover --size 128 -o maps/art.msav

颜色字节序与 Color.rgba() 一致：R<<24 | G<<16 | B<<8 | A。alpha 有特殊含义
(ColoredFloor.java:19-22)：1 = 不与邻居混色、不画边框（像素画用这个），
2 = 四角插值（相当于线性过滤，照片用这个）。
"""
from __future__ import annotations

import argparse
import os
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mlogsim  # noqa: E402  (launcher reuse: java path, jar path, Server)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FLAG_IGNORE = 1     # ColoredFloor.flagIgnoreDifferentColor
FLAG_SMOOTH = 2     # ColoredFloor.flagSmoothBlend


def parse_color(text: str) -> tuple[int, int, int, int]:
    t = text.strip().lstrip("#")
    if len(t) == 6:
        t += "ff"
    if len(t) != 8:
        raise SystemExit(f"bad color {text!r} (want RRGGBB or RRGGBBAA)")
    r, g, b, a = (int(t[i:i + 2], 16) for i in (0, 2, 4, 6))
    return r, g, b, a


def parse_size(text: str) -> tuple[int, int]:
    t = text.lower().replace("*", "x")
    if "x" in t:
        w, h = t.split("x", 1)
        return int(w), int(h)
    return int(t), int(t)


class Plan:
    """W*H 个 RGBA，按 tile 索引 (x + y*W) 排列，y=0 在最下面（Mindustry 的 y 轴朝上）。"""

    def __init__(self, w: int, h: int, fill=(0, 0, 0, 255)):
        self.w, self.h = w, h
        self.px = bytearray(bytes(fill) * (w * h))

    def set(self, x: int, y: int, rgba) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (x + y * self.w) * 4
            self.px[i:i + 4] = bytes(rgba)

    def get(self, x: int, y: int):
        i = (x + y * self.w) * 4
        return tuple(self.px[i:i + 4])

    def fill_rect(self, x0: int, y0: int, x1: int, y1: int, rgba) -> None:
        for y in range(max(0, y0), min(self.h, y1 + 1)):
            for x in range(max(0, x0), min(self.w, x1 + 1)):
                self.set(x, y, rgba)

    def to_bytes(self) -> bytes:
        return bytes(self.px)


def build_blank(plan: Plan, base, grid: int, grid_color, axis_color, major: int, major_color,
                ticks: int = 0, tick_color=None, rings=(), ring_color=None) -> None:
    for y in range(plan.h):
        for x in range(plan.w):
            plan.set(x, y, base)

    if grid > 0:
        for x in range(0, plan.w, grid):
            for y in range(plan.h):
                plan.set(x, y, grid_color)
        for y in range(0, plan.h, grid):
            for x in range(plan.w):
                plan.set(x, y, grid_color)

    # 交叉点打一个亮点: 数格子时不用一格一格点
    if grid > 0 and tick_color is not None:
        for x in range(0, plan.w, grid):
            for y in range(0, plan.h, grid):
                plan.set(x, y, tick_color)

    if major > 0:
        for x in range(0, plan.w, major):
            for y in range(plan.h):
                plan.set(x, y, major_color)
        for y in range(0, plan.h, major):
            for x in range(plan.w):
                plan.set(x, y, major_color)

    # 以地图中心为圆心的等距圈: 量交互/链接半径时一眼读数
    if rings and ring_color is not None:
        cx0, cy0 = (plan.w - 1) / 2.0, (plan.h - 1) / 2.0
        for y in range(plan.h):
            dy = y - cy0
            for x in range(plan.w):
                dx = x - cx0
                d = (dx * dx + dy * dy) ** 0.5
                for r in rings:
                    if abs(d - r) < 0.5:
                        plan.set(x, y, ring_color)
                        break

    if axis_color is not None:
        cx, cy = plan.w // 2, plan.h // 2
        for y in range(plan.h):
            plan.set(cx, y, axis_color)
        for x in range(plan.w):
            plan.set(x, cy, axis_color)


def build_from_image(plan: Plan, path: str, fit: str, bg, resample: str, flip_y: bool) -> None:
    try:
        from PIL import Image
    except ImportError:
        raise SystemExit("Pillow not available: run via the workspace python")
    src = Image.open(path).convert("RGBA")
    iw, ih = src.size
    tw, th = plan.w, plan.h

    if fit == "center":
        canvas = Image.new("RGBA", (tw, th), bg)
        ox, oy = (tw - iw) // 2, (th - ih) // 2
        canvas.paste(src, (ox, oy))
        src = canvas
    else:
        if fit == "stretch":
            box = (0, 0, tw, th)
        else:
            # contain = 完整塞进去留边；cover = 铺满后裁掉多余
            scale = min(tw / iw, th / ih) if fit == "contain" else max(tw / iw, th / ih)
            nw, nh = max(1, round(iw * scale)), max(1, round(ih * scale))
            resized = src.resize((nw, nh), getattr(Image, resample.upper()))
            canvas = Image.new("RGBA", (tw, th), bg)
            canvas.paste(resized, ((tw - nw) // 2, (th - nh) // 2))
            src = canvas
            box = None
        if fit == "stretch":
            src = src.resize((tw, th), getattr(Image, resample.upper()))
        else:
            # cover: 从中间裁
            left = (src.width - tw) // 2
            top = (src.height - th) // 2
            src = src.crop((left, top, left + tw, top + th))

    px = src.load()
    for y in range(th):
        sy = th - 1 - y if flip_y else y
        for x in range(tw):
            plan.set(x, y, px[x, sy])


def apply_alpha_flag(plan: Plan, flag: int) -> None:
    if flag <= 0:
        return
    for i in range(3, len(plan.px), 4):
        plan.px[i] = flag


def preview(plan: Plan, path: str, scale: int = 4) -> None:
    from PIL import Image
    # alpha 字节在 Mindustry 里是「混色标志」（1 = 不与邻居混色），不是透明度：
    # 原样写进 PNG 会让整张图几乎全透明（看起来是一片白），预览时强制不透明。
    raw = bytearray(plan.to_bytes())
    for i in range(3, len(raw), 4):
        raw[i] = 255
    img = Image.frombytes("RGBA", (plan.w, plan.h), bytes(raw))
    img = img.transpose(Image.FLIP_TOP_BOTTOM)
    img.resize((plan.w * scale, plan.h * scale), Image.NEAREST).save(path)


# ---------------------------------------------------------------- java driver

def paint_js(w: int, h: int, core: str | None, rules: str | None) -> str:
    parts = [
        "var ins=new java.io.DataInputStream(new java.io.BufferedInputStream(new java.io.FileInputStream('plan.bin')));",
        "var cf=Vars.content.block('colored-floor').asFloor();",
        "Vars.world.loadGenerator(%d,%d,function(tiles){for(var i=0;i<%d;i++){var c=ins.readInt();"
        # 先清 overlay（矿物）：mlogsim 的空图是自带生成器铺的，会留一层矿脉 overlay。
        "var t=tiles.geti(i);t.setBlock(Vars.content.block('air'));t.setFloor(cf);t.clearOverlay();"
        "t.extraData=c;}print('PAINT' + '\\t' + %d + 'x' + %d);});" % (w, h, w * h, w, h),
        "ins.close();",
    ]
    if core:
        parts.append(
            "var cb=Vars.content.block('%s');var tm=Packages.mindustry.game.Team.sharded;"
            "var ct=Vars.world.tile(%d,%d);ct.setBlock(cb,tm);"
            "print('CORE' + '\\t' + ct.x + ',' + ct.y + '\\t' + ct.block().name);" % (core, w // 2, h // 2)
        )
    if rules:
        parts.append(rules)
    parts.append(
        "var _o=0;_a=Packages.mindustry.content.Blocks.air.asFloor();"
        "for(var yy=0;yy<Vars.world.height();yy++)for(var xx=0;xx<Vars.world.width();xx++){"
        "if(Vars.world.tile(xx,yy).overlay()!=_a)_o++;}"
        "print('CHECK' + '\\t' + 'ore=' + _o + '\\t' + 'build=' + Packages.mindustry.gen.Groups.build.size + '\\t' + 'core=' + (Vars.world.tile(%d,%d).block().name));"
        % (w // 2, h // 2)
    )
    parts.append("print('WORLD' + '\\t' + Vars.world.width() + 'x' + Vars.world.height());")
    return " ".join(parts)


def save_js(name_file: str, filename: str) -> str:
    # 名字走 UTF-8 文件，不塞进 JS 字面量：控制台管道的中文可能被转码，写进 meta 就变成 unknown。
    # 两个键都要有：Map.name() 读 tags['name']（地图列表靠它显示），writeMeta 另写 tags['mapname']（存档回读靠它）。
    # genfilters 必须显式写成 '[]'：host 地图时 Maps 读 tags['genfilters']，缺失或空串会走 readFilters("")
    # 造出 35 个默认过滤器（每个矿石一条 OreFilter），整张图被重新撒矿 —— 这就是「地板里冒出矿」的来源。
    return (
        "var nf=new java.io.File(%s);"
        "var br=new java.io.BufferedReader(new java.io.InputStreamReader(new java.io.FileInputStream(nf),'UTF-8'));"
        "var nm=br.readLine();"
        "var ds=br.readLine();br.close();"
        "var tags=new Packages.arc.struct.StringMap();"
        "tags.put('name',nm);"
        "tags.put('mapname',nm);"
        "Vars.state.map=new Packages.mindustry.maps.Map(tags);"
        "print('SAVENAME' + '\\t' + Vars.state.map.name());"
        "var et=new Packages.arc.struct.StringMap();"
        "et.put('name',nm);et.put('author','DeepSeek');"
        "et.put('genfilters','[]');"
        "if(ds!=null)et.put('description',ds);"
        "var opts=new Packages.mindustry.io.SaveOptions();"
        "opts.extraTags=et;"
        "var f=Vars.customMapDirectory.child(%s);"
        "Packages.mindustry.io.SaveIO.save(f,opts);"
        "print('SAVED' + '\\t' + f.absolutePath() + '\\t' + f.length());"
        % (js_str(name_file), js_str(filename))
    )


def js_str(s: str) -> str:
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="image -> mindustry colored-floor map (.msav)")
    ap.add_argument("-o", "--out", required=True, help="output .msav path")
    ap.add_argument("--size", default="128", help="128 or 128x96")
    ap.add_argument("--name", default=None, help="map name (default: output stem)")
    ap.add_argument("--image", default=None, help="source image (png/jpg/webp)")
    ap.add_argument("--fit", default="stretch", choices=["stretch", "contain", "cover", "center"])
    ap.add_argument("--resample", default="bilinear", choices=["nearest", "bilinear", "bicubic", "lanczos"])
    ap.add_argument("--bg", default="00000000", help="padding/canvas color for contain/center")
    ap.add_argument("--alpha-flag", default="ignore", choices=["normal", "ignore", "smooth"])
    ap.add_argument("--flip-y", default=True, action=argparse.BooleanOptionalAction,
                    help="image row 0 = top of the map (default on)")
    ap.add_argument("--fill", default="232732", help="blank-map base color")
    ap.add_argument("--grid", type=int, default=8, help="grid line spacing in tiles, 0 = off")
    ap.add_argument("--grid-color", default="2c3242")
    ap.add_argument("--major", type=int, default=32, help="major grid spacing, 0 = off")
    ap.add_argument("--major-color", default="39415a")
    ap.add_argument("--axis", default=True, action=argparse.BooleanOptionalAction, help="center cross lines")
    ap.add_argument("--axis-color", default="4c5a7a")
    ap.add_argument("--ticks", type=int, default=0, help="dot at every N-th grid intersection, 0 = off")
    ap.add_argument("--tick-color", default="55617e")
    ap.add_argument("--rings", default="", help="comma separated radii in tiles, e.g. 10,20,40")
    ap.add_argument("--ring-color", default="2f7f8f")
    ap.add_argument("--core", default="core-shard", help="block placed at the center, 'none' to skip")
    ap.add_argument("--infinite/--no-infinite", dest="infinite", default=True)
    ap.add_argument("--waves/--no-waves", dest="waves", default=False)
    ap.add_argument("--preview", default=None, help="write a PNG preview of the plan")
    ap.add_argument("--java", default=None)
    ap.add_argument("--jar", default=None)
    ap.add_argument("--keep", action="store_true", help="keep the temp workdir")
    a = ap.parse_args(argv)

    w, h = parse_size(a.size)
    if not (1 <= w <= 1000 and 1 <= h <= 1000):
        raise SystemExit("size out of range (1..1000)")

    plan = Plan(w, h, parse_color(a.fill))
    if a.image:
        build_from_image(plan, a.image, a.fit, parse_color(a.bg), a.resample, a.flip_y)
    else:
        rings = tuple(float(s) for s in a.rings.split(",") if s.strip()) if a.rings else ()
        build_blank(plan, parse_color(a.fill), a.grid, parse_color(a.grid_color),
                    parse_color(a.axis_color) if a.axis else None,
                    a.major, parse_color(a.major_color),
                    ticks=a.ticks, tick_color=parse_color(a.tick_color) if a.tick_color else None,
                    rings=rings, ring_color=parse_color(a.ring_color) if a.rings else None)
    flag = {"normal": 0, "ignore": FLAG_IGNORE, "smooth": FLAG_SMOOTH}[a.alpha_flag]
    apply_alpha_flag(plan, flag)

    if a.preview:
        preview(plan, a.preview)
        print("preview  %s" % a.preview)

    name = a.name or os.path.splitext(os.path.basename(a.out))[0]
    rules = (
        "var r=Vars.state.rules;r.infiniteResources=%s;r.waves=%s;r.canGameOver=false;"
        "r.logicUnitControl=true;r.unitCap=200;" % ("true" if a.infinite else "false", "true" if a.waves else "false")
    )
    core = None if a.core in ("", "none", "None") else a.core

    # 优先用仓库自带的完整 JRE 21：Steam 客户端那个是 jlink 裁剪版，缺 java.logging，
    # 服务端一启动就 NoClassDefFoundError: java/util/logging/Logger
    java = a.java or (mlogsim.V159_JAVA if os.path.exists(mlogsim.V159_JAVA) else mlogsim.STEAM_JAVA)
    jar = a.jar or mlogsim.V160_JAR
    t0 = time.time()
    srv = mlogsim.Server(java=java, jar=jar, world_size=max(w, h))
    try:
        with open(os.path.join(srv.workdir, "plan.bin"), "wb") as fh:
            fh.write(plan.to_bytes())
        for ln in srv.js(paint_js(w, h, core, rules), timeout=180):
            if ln.startswith(("PAINT", "CORE", "WORLD", "CHECK")):
                print("game    " + ln)
        with open(os.path.join(srv.workdir, "name.txt"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(name + "\n")
            fh.write("128 格染色地板调试世界 · 由 tools/mapgen.py 生成\n")
        fname = os.path.basename(a.out)
        out = srv.js(save_js("name.txt", fname), timeout=180)
        if any(ln.startswith("SAVENAME") and ln.split("\t")[-1] != name for ln in out):
            raise SystemExit("name round-trip mismatch: " + repr(out))
        line = next((ln for ln in out if ln.startswith("SAVED")), None)
        if not line:
            raise SystemExit("save failed: " + repr(out))
        _, path, length = line.split("\t")
        os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
        import shutil
        shutil.copyfile(path, a.out)
        print("saved   %s  (%d bytes, %.1fs)" % (a.out, int(length), time.time() - t0))
        print("name    %s   size %dx%d   alpha %s" % (name, w, h, a.alpha_flag))
        if core:
            print("core    %s @ (%d,%d)" % (core, w // 2, h // 2))
    finally:
        srv.close()
        if not a.keep:
            import shutil
            shutil.rmtree(srv.workdir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
