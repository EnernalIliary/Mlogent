#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""配比计算器的 Python 入口（给 Python 写的 bot 用，只用标准库）。

三种用法：
  1) 当命令行用（等价于 node cli.cjs，只是多了 --image）：
       python -X utf8 ratio-calc/ratio.py --item silicon --rate 5
       python -X utf8 ratio-calc/ratio.py --block ground-factory --count 2 --format md
       python -X utf8 ratio-calc/ratio.py --item silicon --rate 5 --image card.png
  2) 当模块用：
       from ratio import query, text, markdown, image
       r = query(item="silicon", rate=5)          # -> dict（和 CLI --format json 一致）
       print(text(block="graphite-press", count=2))
       image(chain="dagger", chainrate=0.05, out="card.png")
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
    alias = {"chainrate": "chainrate", "gendemand": "gendemand"}
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


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except RuntimeError as e:
        print("× %s" % e, file=sys.stderr)
        raise SystemExit(2)
