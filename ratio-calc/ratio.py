#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""配比计算器的 Python 入口（给 Python 写的 bot 用，只用标准库）。

统一入口（推荐 bot 只记这四个 + 一个出图）：
    calc(**kw) -> dict      一次配比计算，返回和 `node cli.cjs --format json` 完全一样的 dict
    text(**kw) -> str       文本
    markdown(**kw) -> str   Markdown 表格（适合消息卡片）
    image(out, **kw) -> str PNG 卡片（bot 直接发图）
    http_query(base, **kw)  走 serve.cjs 的 HTTP 版本

`**kw` 就是网页/CLI 的参数名，一一对应：item/rate、block/count/plan、
boundary/force/depth/gen/genfuel/gencount/src(csv 或列表)。

三种用法：
  1) 命令行（等价于 node cli.cjs，只是多了 --image）：
       python -X utf8 ratio-calc/ratio.py --block tetrative-reconstructor --count 5
       python -X utf8 ratio-calc/ratio.py --item silicon --rate 5 --image card.png
  2) 当模块用：
       from ratio import calc, text, image
       r = calc(item="silicon", rate=5)                 # dict
       print(text(block="graphite-press", count=2))
       # 已经算过一次的话，别重复算：直接拿 dict 出图
       from ratio import card
       card(calc(block="ground-factory", count=2), "gf.png")
  3) 连 HTTP 服务（serve.cjs）：
       from ratio import http_query
       r = http_query("http://127.0.0.1:8799", item="silicon", rate=5)

注意：算法只有一份（core.js），这里只做转发，不复制任何公式。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = os.path.join(HERE, "cli.cjs")
CARD = os.path.join(HERE, "card.py")
NODE = os.environ.get("RATIO_NODE", "node")
PY = os.environ.get("RATIO_PYTHON", sys.executable)


def _flag_args(**kw) -> list:
    """把 {item:'silicon', rate:5, src:['sand=...']} 变成 CLI 参数列表。"""
    alias = {"gendemand": "gendemand"}
    out = []
    for k, v in kw.items():
        if v is None or v is False:
            continue
        key = "--" + (alias.get(k, k).replace("_", "-"))
        if k == "src":
            items = v if isinstance(v, (list, tuple)) else [v]
            for it in items:
                out += ["--src", str(it)]
            continue
        if v is True:
            out.append(key)
        else:
            out += [key, str(v)]
    return out


def _run(cmd: list) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        msg = (p.stdout or "") + (p.stderr or "")
        raise RuntimeError(msg.strip() or ("命令失败：%s" % " ".join(cmd)))
    return p.stdout


def query(fmt: str = "json", icons: bool = False, node: str = None, **kw) -> dict:
    """跑一次配比计算，返回 dict。"""
    args = _flag_args(**kw) + ["--format", "json"]
    if icons:
        args.append("--icons")
    return json.loads(_run([node or NODE, CLI] + args))


def text(**kw) -> str:
    return _run([NODE, CLI] + _flag_args(**kw) + ["--format", "text"]).rstrip("\n")


def markdown(**kw) -> str:
    return _run([NODE, CLI] + _flag_args(**kw) + ["--format", "md"]).rstrip("\n")


def image(out: str, scale: float = 1.0, width: int = 700, **kw) -> str:
    """直接出 PNG 卡片（bot 发图用），返回绝对路径。"""
    args = _flag_args(**kw)
    cmd = [PY, "-X", "utf8", CARD] + args + ["--out", out, "--scale", str(scale), "--width", str(width)]
    _run(cmd)
    return os.path.abspath(out)


def card(res: dict, out: str, width: int = 700, scale: float = 1.0) -> str:
    """拿已经算好的 dict 直接出 PNG（不再跑一次 node）。"""
    try:
        from card import render_png          # 同目录，脚本方式跑时会命中
    except ImportError:
        import importlib.util
        spec = importlib.util.spec_from_file_location("ratio_card", CARD)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        render_png = mod.render_png
    return render_png(res, out, width=width, scale=scale)


def http_query(base: str, timeout: float = 10.0, **kw) -> dict:
    """走 serve.cjs 的 HTTP 服务。"""
    q = {}
    for k, v in kw.items():
        if v is None or v is False:
            continue
        if k == "src":
            q["src"] = v if isinstance(v, (list, tuple)) else [v]
        else:
            q[k] = str(v)
    q["format"] = "json"
    qs = urllib.parse.urlencode(q, doseq=True)
    with urllib.request.urlopen(base.rstrip("/") + "/calc?" + qs, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def main(argv) -> int:
    argv = list(argv)
    image_out = None
    scale = 1.0
    rest = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--image" and i + 1 < len(argv):
            image_out = argv[i + 1]
            i += 2
            continue
        if a == "--scale" and i + 1 < len(argv):
            scale = float(argv[i + 1])
            i += 2
            continue
        rest.append(a)
        i += 1
    if image_out:
        print(image(image_out, scale=scale, **(_flags_to_kw(rest))))
        return 0
    sys.stdout.write(_run([NODE, CLI] + rest))
    return 0


def _flags_to_kw(rest: list) -> dict:
    kw = {}
    i = 0
    while i < len(rest):
        a = rest[i]
        if not a.startswith("--"):
            i += 1
            continue
        key = a[2:]
        val = True
        if i + 1 < len(rest) and not rest[i + 1].startswith("--"):
            val = rest[i + 1]
            i += 1
        if key == "src":
            kw.setdefault("src", [])
            kw["src"] = (kw["src"] + [val]) if isinstance(kw["src"], list) else [kw["src"], val]
        else:
            kw[key.replace("-", "_")] = val
        i += 1
    return kw


# 统一入口的别名：calc 是正式名字（query 保留给老调用）
calc = query

__all__ = ["calc", "query", "text", "markdown", "image", "card", "http_query"]


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except RuntimeError as e:
        print("× %s" % e, file=sys.stderr)
        raise SystemExit(2)
