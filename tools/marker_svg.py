"""Compile a bounded subset of static SVG into a world-processor mlog program."""

import argparse
import math
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

MAX_SVG_BYTES = 65536
MAX_MARKERS = 128
_WORLD_UNITS_PER_TILE = 8
_SIM_WORLD_INSTRUCTIONS_PER_TICK = 8
_SVG_NS = "{http://www.w3.org/2000/svg}"
_NUM = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
_STYLE = {"fill", "stroke", "stroke-width", "fill-opacity", "stroke-opacity"}
_GEOMETRY = {
    "svg": {"width", "height", "viewBox"}, "g": set(),
    "line": {"x1", "y1", "x2", "y2"}, "polyline": {"points"}, "polygon": {"points"},
    "rect": {"x", "y", "width", "height"}, "circle": {"cx", "cy", "r"},
    "ellipse": {"cx", "cy", "rx", "ry"},
}
_NAMED_COLORS = {
    "black": "000000", "white": "ffffff", "red": "ff0000", "green": "008000",
    "blue": "0000ff", "yellow": "ffff00", "gray": "808080", "grey": "808080",
    "lime": "00ff00", "cyan": "00ffff", "magenta": "ff00ff",
}
_GEOMETRY_EPS = 1e-9


def _length(value, *, unitless=False):
    suffix = "" if unitless else "(?:px)?"
    match = re.fullmatch(rf"({_NUM}){suffix}", value.strip())
    if not match:
        raise ValueError(f"invalid SVG number or length {value[:48]!r}")
    number = float(match[1])
    if not math.isfinite(number) or abs(number) > 1e6:
        raise ValueError("SVG length exceeds the supported range")
    return number


def _numbers(text):
    if not re.fullmatch(rf"\s*{_NUM}(?:(?:\s*,\s*|\s+){_NUM})*\s*", text):
        raise ValueError("invalid SVG coordinate list")
    return [_length(number) for number in re.findall(_NUM, text)]


def _paint(paint, opacity):
    opacity = _length(opacity, unitless=True)
    if not 0 <= opacity <= 1:
        raise ValueError("paint opacity must be in [0, 1]")
    key = paint.strip().lower()
    if key in ("none", "transparent"):
        return None
    if key in _NAMED_COLORS:
        rgba = _NAMED_COLORS[key]
    elif re.fullmatch(r"#(?:[0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})", key):
        rgba = key[1:]
        if len(rgba) <= 4:
            rgba = "".join(channel * 2 for channel in rgba)
    else:
        raise ValueError(f"unsupported SVG paint {paint[:48]!r}; use a hex color")
    alpha = round(int(rgba[6:] or "ff", 16) * opacity)
    return f"%{rgba[:6]}{alpha:02x}" if alpha else None


def _style(element, inherited, tag):
    for attr in element.attrib:
        if attr not in _STYLE | _GEOMETRY[tag] | {"id", "style"}:
            raise ValueError(f"unsupported SVG attribute {attr[:48]!r} on <{tag}>")
    style = {**inherited, **{k: v for k, v in element.attrib.items() if k in _STYLE}}
    for pair in element.get("style", "").split(";"):
        if pair.strip():
            key, sep, value = pair.partition(":")
            if not sep or key.strip() not in _STYLE:
                raise ValueError(f"unsupported SVG style {key.strip()[:48]!r}")
            style[key.strip()] = value.strip()
    return style


def _outline(element, tag):
    def length(name):
        return _length(element.get(name, "0"))

    if tag == "line":
        return [(length("x1"), length("y1")), (length("x2"), length("y2"))]
    if tag in ("polygon", "polyline"):
        xy = _numbers(element.get("points", ""))
        if len(xy) % 2 or not 4 <= len(xy) <= 128 or (tag == "polygon" and len(xy) < 6):
            raise ValueError(f"<{tag}> requires complete pairs and at most 64 points")
        return list(zip(xy[::2], xy[1::2]))
    if tag == "rect":
        x, y, w, h = (length(name) for name in ("x", "y", "width", "height"))
        if min(w, h) < 0:
            raise ValueError("rectangle sizes must be non-negative")
        return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)] if w and h else []
    cx, cy = length("cx"), length("cy")
    rx, ry = (length("r"),) * 2 if tag == "circle" else (length("rx"), length("ry"))
    if min(rx, ry) < 0:
        raise ValueError("ellipse radii must be non-negative")
    angles = [math.tau * i / 24 for i in range(24)]
    return [(cx + rx * math.cos(a), cy + ry * math.sin(a)) for a in angles] if rx and ry else []


def _cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _edges(points):
    return list(zip(points, points[1:] + points[:1]))


def _intersects(a, b, c, d):
    for axis in (0, 1):
        if max(a[axis], b[axis]) < min(c[axis], d[axis]) or max(c[axis], d[axis]) < min(a[axis], b[axis]):
            return False
    return (_cross(a, b, c) * _cross(a, b, d) <= 0
            and _cross(c, d, a) * _cross(c, d, b) <= 0)


def _fill_quads(points):
    """Represent a simple, possibly concave polygon as white-texture quads."""
    points = list(points)
    if len(points) > 1 and points[0] == points[-1]:
        points.pop()
    edges = _edges(points)
    if any(a == b for a, b in edges) or any(
        _intersects(a, b, c, d)
        for i, (a, b) in enumerate(edges)
        for j, (c, d) in enumerate(edges)
        if i + 1 < j and (i, j) != (0, len(edges) - 1)
    ):
        raise ValueError("filled SVG outline must be a simple polygon")
    area = sum(a[0] * b[1] - a[1] * b[0] for a, b in edges)
    if len(points) < 3 or abs(area) <= _GEOMETRY_EPS:
        raise ValueError("SVG fill has zero area at the chosen scale")
    if area < 0:
        points.reverse()

    if all(_cross(a, b, points[(i + 2) % len(points)]) > _GEOMETRY_EPS
           for i, (a, b) in enumerate(_edges(points))):
        for i in range(1, len(points) - 1, 2):
            piece = [points[0], *points[i:i + 3]]
            if len(piece) == 3:
                piece.append(piece[-1])
            yield piece
        return

    # White-texture quads accept triangles by repeating the last vertex.
    while len(points) > 3:
        size = len(points)
        for i, b in enumerate(points):
            left, right = (i - 1) % size, (i + 1) % size
            a, c = points[left], points[right]
            if _cross(a, b, c) > _GEOMETRY_EPS and not any(
                min(_cross(a, b, p), _cross(b, c, p), _cross(c, a, p)) >= -_GEOMETRY_EPS
                for j, p in enumerate(points) if j not in (left, i, right)
            ):
                yield [a, b, c, c]
                points.pop(i)
                break
        else:
            raise ValueError("SVG fill cannot be triangulated at the chosen scale")
    yield [*points, points[-1]]


def convert(svg, *, width=24, x=2, y=2, start_id=1000):
    """Map the SVG viewBox onto a tile rectangle at (x, y), its lower left."""
    if not isinstance(svg, str) or len(svg) > MAX_SVG_BYTES or len(svg.encode("utf-8")) > MAX_SVG_BYTES:
        raise ValueError("svg must be text of at most 64 KiB")
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)|<\?xml-stylesheet\b", svg, re.I):
        raise ValueError("SVG declarations for DTDs, entities and stylesheets are unsupported")
    if any(type(v) not in (int, float) or not -10000 <= v <= 10000 for v in (width, x, y)) or not 0 < width <= 1024:
        raise ValueError("width must be in (0, 1024]; x and y must be in [-10000, 10000]")
    if type(start_id) is not int or not 0 <= start_id <= 2147483647:
        raise ValueError("start_id must be a non-negative signed 32-bit integer")
    try:
        root = ET.fromstring(svg)
    except ET.ParseError as exc:
        raise ValueError(f"invalid SVG XML: {exc}") from exc
    if root.tag not in ("svg", _SVG_NS + "svg"):
        raise ValueError("expected an <svg> root")
    if "viewBox" in root.attrib:
        box = _numbers(root.attrib["viewBox"])
        if len(box) != 4:
            raise ValueError("viewBox requires four coordinates")
        vx, vy, vw, vh = box
    else:
        vx = vy = 0
        vw, vh = (_length(root.get(name, "0")) for name in ("width", "height"))
    if min(vw, vh) <= 0:
        raise ValueError("SVG needs a positive viewBox or width and height")
    factor = width / vw
    height = vh * factor
    if not 1e-5 <= height <= 1024 or width < 1e-5:
        raise ValueError("scaled SVG width and height must be in [0.00001, 1024] tiles")

    def point(p):
        out = (x + (p[0] - vx) * factor, y + (vy + vh - p[1]) * factor)
        if any(abs(v) > 20000 for v in out):
            raise ValueError("scaled SVG geometry exceeds the supported coordinate range")
        return tuple(round(v, 5) for v in out)

    lines = []
    count = 0

    def marker(kind, xy):
        nonlocal count
        mid = start_id + count
        if count >= MAX_MARKERS:
            raise ValueError(f"SVG needs more than {MAX_MARKERS} markers; simplify the geometry")
        if mid > 2147483647:
            raise ValueError("generated marker IDs exceed the signed 32-bit range")
        lines.append(f"makemarker {kind} {mid} {xy[0]} {xy[1]} true")
        lines.append(f"setmarker drawLayer {mid} {120 + count / 1000:.3f} 0 0")
        count += 1
        return mid

    node_count = 0

    def visit(element, inherited, depth):
        nonlocal node_count
        node_count += 1
        if depth > 16 or node_count > 256:
            raise ValueError("SVG exceeds 16 levels or 256 elements")
        tag = element.tag.removeprefix(_SVG_NS)
        if tag in ("title", "desc"):
            return
        if tag not in _GEOMETRY or (depth and tag == "svg"):
            raise ValueError(f"unsupported SVG element <{tag[:48]}>")
        style = _style(element, inherited, tag)
        if tag in ("svg", "g"):
            for child in element:
                visit(child, style, depth + 1)
            return
        if len(element):
            raise ValueError(f"unexpected child in <{tag}>")
        fill = _paint(style["fill"], style["fill-opacity"]) if tag != "line" else None
        stroke = _paint(style["stroke"], style["stroke-opacity"])
        stroke_width = _length(style["stroke-width"]) * factor
        if not 0 <= stroke_width <= 1024:
            raise ValueError("scaled stroke-width must be in [0, 1024] tiles")
        points = [point(p) for p in _outline(element, tag)]
        points = [p for i, p in enumerate(points) if i == 0 or p != points[i-1]]
        if fill and len(points) >= 3:
            for quad in _fill_quads(points):
                mid = marker("quad", (0, 0))
                for i, (px, py) in enumerate(reversed(quad)):
                    lines.append(f"setmarker posi {mid} {i} {px} {py}")
                lines.append(f"setmarker color {mid} {fill} 0 0")
        if stroke and stroke_width and len(points) >= 2:
            edges = _edges(points) if tag not in ("line", "polyline") else zip(points, points[1:])
            for a, b in edges:
                if a != b:
                    mid = marker("line", a)
                    native_stroke = stroke_width * _WORLD_UNITS_PER_TILE
                    lines.extend([f"setmarker endPos {mid} {b[0]} {b[1]} 0",
                                  f"setmarker color {mid} {stroke} 0 0",
                                  f"setmarker stroke {mid} {native_stroke:.8f} 0 0",
                                  f"setmarker outline {mid} false 0 0"])

    visit(root, {"fill": "black", "stroke": "none", "stroke-width": "1",
                 "fill-opacity": "1", "stroke-opacity": "1"}, 0)
    if not count:
        raise ValueError("SVG has no visible supported geometry")
    lines.append("stop")
    return {
        "mlog": "\n".join(lines) + "\n",
        "bounds": {"min_x": x, "min_y": y, "max_x": x + width, "max_y": y + height, "units": "tiles"},
        "marker_count": count, "instruction_count": len(lines),
        "first_id": start_id, "last_id": start_id + count - 1,
        "preview_ticks": math.ceil(len(lines) / _SIM_WORLD_INSTRUCTIONS_PER_TICK) + 1,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("svg", type=Path)
    parser.add_argument("--width", type=float, default=24, help="output width in tiles")
    parser.add_argument("--x", type=float, default=2)
    parser.add_argument("--y", type=float, default=2)
    parser.add_argument("--start-id", type=int, default=1000)
    parser.add_argument("--out", type=Path, help="write UTF-8 mlog to this file; defaults to stdout")
    args = parser.parse_args(argv)
    try:
        with args.svg.open("rb") as source:
            svg = source.read(MAX_SVG_BYTES + 1).decode("utf-8-sig")
        result = convert(svg, width=args.width, x=args.x, y=args.y, start_id=args.start_id)
        if args.out:
            args.out.write_text(result["mlog"], encoding="utf-8", newline="\n")
        else:
            sys.stdout.write(result["mlog"])
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
