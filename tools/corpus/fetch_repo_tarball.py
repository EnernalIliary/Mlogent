"""fetch_repo_tarball.py -- download a whole GitHub schematic repo as a tarball and extract it safely.

WHY: fetch_schematics.py 走 tree API + raw，一文件一请求；遇到上万文件的大仓库（如
     Anon-deisu/Mindustry-schematic-storage：17,564 个 .msch / 216 MB）会被 GitHub 限流拖死。
     整包下载只有一次请求，实测 203 MB @ ~15 MB/s / 13 s。
     另一个坑：这些蓝图的文件名大量是中文，**Windows 自带 tar.exe 会把 UTF-8 文件名按 CP936 解码**
     （1000_核心入冷22温差.msch → 1000_鏍稿績鍏ュ喎22娓╁樊.msch），不同名字撞成同一个文件，
     17,564 个只落下 13,481 个且内容互相覆盖。git clone --depth 1 也不稳（RPC failed / connection reset）。
     所以这里用 Python tarfile（UTF-8 正确）+ 短 ASCII 文件名（避开 MAX_PATH 与编码），
     原名写进 _index.json 供溯源。
WHAT: codeload tar.gz 下载 -> Python tarfile 解到 <dest>/<prefix>-flat/sNNNNNN.msch + _index.json。
HOW:  只依赖标准库；ext = --ext（默认 .msch）。
用法:
  python tools/corpus/fetch_repo_tarball.py --repo Anon-deisu/Mindustry-schematic-storage \
      --dest C:/Users/lliary/mlog-corpus --prefix anon
  # 然后：python tools/corpus/classify_schematics.py --src C:/Users/lliary/mlog-corpus/anon-flat \
  #           --dest C:/Users/lliary/mlog-corpus/anon-corpus
"""
import argparse, json, os, sys, tarfile, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UA = {"User-Agent": "mlog-corpus/1.0"}


def download(url, dest, retries=5, timeout=60):
    """带重试的整包下载；已存在且大小 >0 就跳过（可重入）。"""
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        print("reuse %s (%d B)" % (dest, os.path.getsize(dest)))
        return dest
    last = None
    for i in range(1, retries + 1):
        try:
            t0 = time.time()
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r, open(dest, "wb") as f:
                while True:
                    chunk = r.read(1 << 20)
                    if not chunk:
                        break
                    f.write(chunk)
            print("downloaded %d B in %.0f s" % (os.path.getsize(dest), time.time() - t0))
            return dest
        except Exception as e:                       # 网络抖动是常态
            last = e
            print("download attempt %d/%d failed: %s" % (i, retries, repr(e)[:160]))
            time.sleep(3 * i)
    raise SystemExit("download failed: %r" % (last,))


def extract_flat(tgz, outdir, ext=".msch"):
    """解 tar.gz，蓝图层文件写成 sNNNNNN<ext>，原名进 _index.json（UTF-8 安全、无长路径）。"""
    os.makedirs(outdir, exist_ok=True)
    idx, bad, i = [], [], 0
    t0 = time.time()
    with tarfile.open(tgz, "r:gz") as tf:
        for m in tf:
            if not m.isfile() or not m.name.lower().endswith(ext):
                continue
            short = "s%06d%s" % (i, ext)
            i += 1
            try:
                data = tf.extractfile(m).read()
                with open(os.path.join(outdir, short), "wb") as o:
                    o.write(data)
                idx.append([short, m.name, len(data)])
            except Exception as e:
                bad.append([m.name, "%s: %s" % (type(e).__name__, str(e)[:120])])
    index = {"created_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "tarball": os.path.abspath(tgz),
             "count": len(idx), "bad": bad, "items": idx}
    with open(os.path.join(outdir, "_index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False)
    print("extracted %d %s file(s), %d bad, %.1f s -> %s" % (
        len(idx), ext, len(bad), time.time() - t0, outdir))
    if bad:
        print("first bad: %s" % (bad[0],))
    return index


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="owner/name")
    ap.add_argument("--branch", default="", help="默认取仓库 default_branch")
    ap.add_argument("--dest", default=os.path.join(os.path.expanduser("~"), "mlog-corpus"),
                    help="工作区外的大目录（默认 ~/mlog-corpus，避免 OneDrive 同步 churn）")
    ap.add_argument("--prefix", default="", help="默认取仓库名")
    ap.add_argument("--ext", default=".msch")
    ap.add_argument("--keep-tgz", action="store_true", help="保留 tar.gz（默认保留，--no-keep 删）")
    ap.add_argument("--no-keep", dest="keep_tgz", action="store_false")
    a = ap.parse_args(argv)
    prefix = a.prefix or a.repo.split("/")[-1].lower()
    branch = a.branch
    if not branch:
        import urllib.request as up
        with up.urlopen(up.Request("https://api.github.com/repos/" + a.repo, headers=UA), timeout=30) as r:
            branch = json.loads(r.read().decode("utf-8")).get("default_branch") or "main"
    os.makedirs(a.dest, exist_ok=True)
    url = "https://codeload.github.com/%s/tar.gz/refs/heads/%s" % (a.repo, branch)
    print("tarball %s" % url)
    tgz = os.path.join(a.dest, prefix + ".tar.gz")
    download(url, tgz)
    outdir = os.path.join(a.dest, prefix + "-flat")
    idx = extract_flat(tgz, outdir, a.ext)
    if not a.keep_tgz:
        os.remove(tgz)
    print("\nnext: python tools/corpus/classify_schematics.py --src %s --dest %s" % (
        outdir, os.path.join(a.dest, prefix + "-corpus")))
    return 0 if idx["count"] else 2


if __name__ == "__main__":
    sys.exit(main())
