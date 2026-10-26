
"""Crawl mindustry.top (the map site) and download .msav files.

The site's API rate limit is brutal: a burst of requests earns
{"success":false,"errorMessage":"Too many requests"} with HTTP 400, so this
script keeps a polite delay (default 10 s) and backs off on errors.  The list
endpoint is https://api.mindustry.top/maps/list with query parameters
"begin" (cursor = last map id of the previous page) and "search" (free text);
each page holds 15 maps.  Detail/download URLs and IPFS unwrapping live in
tools/corpus/map_site.py -- download() REQUIRES a Path, not a str.

    python tools/corpus/crawl_maps.py --search 逻辑 --search 塔防 --want 20
    python tools/corpus/crawl_maps.py --list-only        # just refresh ids
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "corpus"))
import map_site  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

UA = {"User-Agent": "Mozilla/5.0 mlog-corpus/1.0", "Accept": "application/json"}
LIST_URL = "https://api.mindustry.top/maps/list?begin="


def fetch_page(search, delay, attempts=3):
    """One list request; returns [] when the site keeps refusing."""
    q = "" if not search else "&search=" + urllib.parse.quote(search)
    for _ in range(attempts):
        try:
            req = urllib.request.Request(LIST_URL + q, headers=UA)
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            print("  %s: HTTP %d -> %.0f s" % (search or "-", e.code, delay * 3), flush=True)
            time.sleep(delay * 3)
        except Exception as e:
            print("  %s: %s -> %.0f s" % (search or "-", type(e).__name__, delay * 2), flush=True)
            time.sleep(delay * 2)
    return []


def main(argv=None):
    ap = argparse.ArgumentParser(description="crawl mindustry.top maps")
    ap.add_argument("--search", action="append", default=[], help="搜索词，可重复；空 = 全站第一页")
    ap.add_argument("--want", type=int, default=20, help="最多下载多少个地图")
    ap.add_argument("--delay", type=float, default=10.0, help="请求间隔秒（站点限速很严）")
    ap.add_argument("--dest", default=str(ROOT / "logic-corpus" / "_maps"))
    ap.add_argument("--list-only", action="store_true")
    a = ap.parse_args(argv)

    dest = Path(a.dest)
    dest.mkdir(parents=True, exist_ok=True)
    lst = dest / "_list.json"
    seen = {}
    if lst.exists():
        for m in json.load(open(lst, encoding="utf-8")):
            seen[m["id"]] = m
    print("seed ids: %d" % len(seen), flush=True)

    for s in (a.search or [""]):
        batch = fetch_page(s, a.delay)
        new = 0
        for m in batch:
            if m["id"] not in seen:
                seen[m["id"]] = m
                new += 1
        print("search %-8s -> %d map(s), %d new (total %d)"
              % (s or "-", len(batch), new, len(seen)), flush=True)
        json.dump(list(seen.values()), open(lst, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        time.sleep(a.delay)
    if a.list_only:
        return 0

    got = 0
    for m in list(seen.values()):
        if got >= a.want:
            break
        mid = str(m["id"])
        out = dest / ("mindustrytop-%s.msav" % mid)
        if out.exists() and out.stat().st_size > 0:
            got += 1
            continue
        try:
            path = map_site.download(mid, out)
            print("  %s %9d B  %s" % (mid, Path(path).stat().st_size, (m.get("name") or "")[:44]), flush=True)
            got += 1
        except Exception as e:
            print("  %s FAIL %s %s" % (mid, type(e).__name__, str(e)[:90]), flush=True)
        time.sleep(a.delay)
    print("maps on disk: %d" % len(list(dest.glob("*.msav"))), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
