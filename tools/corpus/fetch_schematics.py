
"""fetch_schematics.py -- download public Mindustry .msch schematic packs for corpus work.

WHY: rules/ 的判据只在本地 1421 个存档上验证过；第三方（社区/地图站）蓝图是更硬的外部样本，
     能暴露本地语料里没有的写法（多绑定、图论连线、逻辑展示屏）。
WHAT: 只下载、不解码；解码/归类见 tools/dev/classify_schematics.py。
HOW:  GitHub tree API 拿清单 -> raw.githubusercontent 并发下载 -> 按 sha1 去重存 logic-corpus/<owner>-<repo>/。
      网络不可用时退出码 2，不写任何文件。

用法:
  python tools/dev/fetch_schematics.py                 # 抓清单里全部仓库
  python tools/dev/fetch_schematics.py --only foxitOS  # 只抓名字含该子串的仓库
  python tools/dev/fetch_schematics.py --dry-run       # 只列清单不下载
"""
import argparse, hashlib, json, os, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = {"User-Agent": "mlog-corpus-fetch/1.0 (+local research)"}
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEST = os.path.join(ROOT, "logic-corpus")
API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"

# (owner/repo, branch) -- branches verified 2026-10-26 via the tree API
REPOS = [
    ("foxitOS/CMD-pack", "main"),
    ("pixecoz/SchematicsPack", "main"),
    ("acoaco/schematics", "master"),
    ("acoaco/Mindustry-multi-binding-schematics-pack", "master"),
    ("dmgnr/Mindustry-logic-schem-collection", "main"),
    ("holmes-g/logic-schematics", "main"),
    ("B00M3000/Mindustry-Schematics", "master"),
]

def get(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def listing(repo, branch):
    out = []
    page = 0
    while True:
        url = "%s/repos/%s/git/trees/%s?recursive=1" % (API, repo, branch)
        tree = json.loads(get(url)).get("tree", [])
        for t in tree:
            if t.get("type") == "blob" and t["path"].lower().endswith(".msch"):
                out.append((t["path"], t.get("size") or 0))
        if len(tree) < 100000 or page:
            return out
        return out

def raw_url(repo, branch, path):
    q = "/".join(urllib.parse.quote(seg) for seg in path.split("/"))
    return "%s/%s/%s/%s" % (RAW, repo, branch, q)

def safe_rel(repo, path):
    return os.path.join(repo.replace("/", "-"), *[p.replace(os.sep, "_") for p in path.split("/")])

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--jobs", type=int, default=8)
    a = ap.parse_args(argv)
    repos = [r for r in REPOS if a.only.lower() in ("", r[0].lower())]
    plan, failures = [], []
    for repo, branch in repos:
        try:
            items = listing(repo, branch)
            print("list %-52s %4d .msch" % (repo, len(items)))
        except Exception as e:
            failures.append((repo, "list", repr(e)[:120]))
            print("list %-52s FAIL %s" % (repo, repr(e)[:90]))
            continue
        for path, size in items:
            plan.append((repo, branch, path, size))
    if not plan:
        print("nothing to fetch (network down?)")
        return 2
    total = sum(p[3] for p in plan)
    print("plan: %d file(s), %.2f MB (before dedupe)" % (len(plan), total / 1048576.0))
    if a.dry_run:
        for repo, branch, path, size in plan[:20]:
            print("   ", repo, path, size)
        return 0
    os.makedirs(DEST, exist_ok=True)
    seen, saved, dup = {}, 0, 0
    t0 = time.time()
    def work(item):
        repo, branch, path, size = item
        return item, get(raw_url(repo, branch, path))
    with ThreadPoolExecutor(max_workers=a.jobs) as ex:
        for item, data in ex.map(work, plan):
            repo, branch, path, size = item
            h = hashlib.sha1(data).hexdigest()
            if h in seen:
                dup += 1
                continue
            seen[h] = os.path.join(repo, path)
            dst = os.path.join(DEST, safe_rel(repo, path))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "wb") as f:
                f.write(data)
            saved += 1
    dt = time.time() - t0
    index = {"fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
             "repos": [{"repo": r, "branch": b} for r, b in repos],
             "files": saved, "duplicates": dup, "failures": failures,
             "index": {h: p for h, p in seen.items()}}
    with open(os.path.join(DEST, "_index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=1)
    print("saved %d file(s) (%d duplicate payload(s)) in %.1f s -> %s" % (saved, dup, dt, os.path.relpath(DEST, ROOT)))
    if failures:
        print("failures: %d" % len(failures))
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
