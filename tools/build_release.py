"""Build the release assets: four packages plus a checksum file.

Why packages instead of one zip
-------------------------------
The audiences do not overlap.  An agent harness wants the *skills* (a drop-in
directory).  A person writing mlog wants the *toolchain* (pure Python, runs
offline).  Someone quoting a fact wants the *knowledge* base (mother document +
data tables + evidence).  Someone deploying the MCP server wants neither tests
nor docs, but does want the service files.  Shipping one 6 MB zip makes all four
people download the other three audiences' files.

What is deliberately not in any package
---------------------------------------
* `logic-corpus/` (12.8 MB) and the vendored `Mindustry-Source/` / `Arc-Source/`
  trees: they are reference material for the anchors, and the toolchain works
  without them (`claims.py` treats them as external and only checks the shape).
* The Mindustry server jar and a JRE: licensing plus 150 MB.  `mlogsim` explains
  how to point at your own (`MLOGSIM_JAR` / `MLOGSIM_JAVA`).
* Private notes and personal data (`docs/联机调试世界.md`, `Mlog辅助-*`,
  `maps/大肥鱼的调试世界.msav`): not ours to publish.

Every file comes from `git ls-files`, so a package can never contain an
untracked leftover, and zips are written with a fixed timestamp so two builds of
the same commit produce the same bytes.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist", "release")
EPOCH = (2026, 11, 18, 0, 0, 0)


def tracked() -> list[str]:
    out = subprocess.run(["git", "-C", ROOT, "ls-files", "-z"],
                         stdout=subprocess.PIPE, check=True).stdout
    return [p for p in out.decode("utf-8").split("\0") if p]


def keep_dev(rel: str) -> bool:
    """`tools/dev/` holds one-off probes; only the tools that ship are kept."""
    if not rel.startswith("tools/dev/"):
        return True
    return rel in ("tools/dev/README.md", "tools/dev/dump_game.py",
                   "tools/dev/bench.py", "tools/dev/fix_skill_links.py")


PACKAGES = {
    "toolchain": {
        "title": "mlog toolchain (pure Python)",
        "summary": "Static analysis, decoding, generation, scenario runs, differential "
                   "checks and the benchmark harness. No game install, no jar, no "
                   "third-party packages: `python gate.py` should pass everything that "
                   "does not need the Java executor.",
        "pick": lambda rel: (
            rel.startswith(("tools/", "rules/", "data/", "tests/", "docs/",
                            "scenes/", "bench/", "deploy/"))
            or rel in ("README.md", "README.zh-CN.md", "LICENSE", "CHANGELOG.md", "gate.py",
                       "MANIFEST.repo.sha256", ".gitattributes", ".dockerignore")
        ) and keep_dev(rel),
    },
    "knowledge": {
        "title": "mlog knowledge base",
        "summary": "The mother document for Mindustry mlog facts: 130+ articles, 12 "
                   "canonical data tables, 85 claims with anchored evidence, plus the "
                   "game data tables the generators read. Point `tools/kb.py` at this "
                   "directory to build a local index.",
        "pick": lambda rel: rel.startswith(("knowledge/", "data/game/")),
    },
    "skills": {
        "title": "agent skills (drop-in)",
        "summary": "Two skill packs for a DSH-style harness. Copy `mlog-agentskill/` "
                   "and `mindustry-blueprint/` into `~/.dsh/skills/` and the tools "
                   "inside each are self-contained.",
        "pick": lambda rel: rel.startswith(".dsh/skills/"),
        "strip": ".dsh/skills/",
    },
    "mcp": {
        "title": "MCP server (deployable)",
        "summary": "The HTTP form of the MCP server plus everything it reads: `tools/`, "
                   "`rules/`, `data/`, `knowledge/` (for `mlog_kb`), and the systemd "
                   "unit / Dockerfile / reverse-proxy notes under `deploy/`. No tests: a "
                   "server needs the interpreter and its data, and `mlog_doctor` says "
                   "what is missing. "
                   "Start with `python tools/mlog_mcp_http.py --port 8765 --token ...`.",
        # knowledge/ is here because `mlog_kb` reads it: a server that answers
        # "what is core-shard called in Chinese" needs the articles, and the
        # whole base is 1.35 MB -- cheaper than a tool that always returns zero.
        "pick": lambda rel: (
            rel.startswith(("tools/", "rules/", "data/", "deploy/", "knowledge/", "docs/"))
            or rel in ("README.md", "README.zh-CN.md", "LICENSE", "CHANGELOG.md", "SECURITY.md",
                       "docs/MCP部署.md", ".dockerignore")
        ) and keep_dev(rel),
    },
}


SCRUB = [
    ("F:\\OneDrive\\桌面\\AtomicStates", "<repo>"),
    ("F:/OneDrive/桌面/AtomicStates", "<repo>"),
    ("F:\\OneDrive\\文档\\deepseek-harness\\default-workspace\\kb-stage", "<stage>"),
    ("F:/OneDrive/文档/deepseek-harness/default-workspace/kb-stage", "<stage>"),
    ("F:\\\\OneDrive\\\\桌面\\\\AtomicStates", "<repo>"),
    ("F:\\\\OneDrive\\\\文档\\\\deepseek-harness\\\\default-workspace\\\\kb-stage",
     "<stage>"),
    ("C:\\\\Users\\\\lliary", "<home>"),
    ("F:/nonexistent-corpus", "<no-corpus>"),
    ("C:\\Users\\lliary", "<home>"),
    ("C:/Users/lliary", "<home>"),
]


def scrub(text: str) -> str:
    for old, new in SCRUB:
        text = text.replace(old, new)
    return text


def write(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def build(name: str, spec: dict, version: str, vdir: str, files: list[str]) -> str:
    picked = [f for f in files if spec["pick"](f)]
    if not picked:
        raise SystemExit("package %s is empty -- the filter is wrong" % name)
    stage = tempfile.mkdtemp(prefix="rel-%s-" % name)
    try:
        if name == "skills":
            from pathlib import Path
            sys.path.insert(0, os.path.join(ROOT, "tools"))
            import build_skills
            generated = Path(stage) / "generated"
            build_skills.build(generated)
            build_skills.verify(generated)
            for child in generated.iterdir():
                shutil.move(str(child), os.path.join(stage, child.name))
            generated.rmdir()
            picked = []
        prefix = spec.get("strip", "")
        for rel in picked:
            src = os.path.join(ROOT, rel)
            dst = os.path.join(stage, rel[len(prefix):] if prefix and rel.startswith(prefix) else rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            data = open(src, "rb").read()
            if b"\0" not in data[:4096]:
                try:
                    text = data.decode("utf-8")
                except UnicodeDecodeError:
                    pass
                else:
                    fixed = scrub(text)
                    if fixed != text:
                        data = fixed.encode("utf-8")
            with open(dst, "wb") as fh:
                fh.write(data)
        # Path scrubbing changes exported bytes; its integrity manifest must
        # describe the exported tree, rather than the original source checkout.
        if os.path.isfile(os.path.join(stage, 'MANIFEST.repo.sha256')):
            from pathlib import Path
            sys.path.insert(0, os.path.join(ROOT, 'tools'))
            import check_manifest
            write(os.path.join(stage, 'MANIFEST.repo.sha256'),
                  check_manifest.build(Path(stage)))
        file_count = sum(len(names) for _, _, names in os.walk(stage))
        write(os.path.join(stage, "PACKAGE.txt"),
              "package : %s\nversion : %s\ntitle   : %s\nfiles   : %d\n\n%s\n\n"
              "verify  : sha256sum -c SHA256SUMS.txt   (from the download directory)\n"
              "note    : local paths in the evidence logs are rewritten to <repo>/<home>/<stage>\n"
              "repo    : https://github.com/EnernalIliary/Mlogent\n"
              % (name, version, spec["title"], file_count, spec["summary"]))
        out = os.path.join(vdir, "mlog-agent-%s-%s.zip" % (version, name))
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
            for dirpath, _dirs, names in os.walk(stage):
                _dirs.sort()
                for fn in sorted(names):
                    full = os.path.join(dirpath, fn)
                    rel = os.path.relpath(full, stage).replace("\\", "/")
                    info = zipfile.ZipInfo(rel, date_time=EPOCH)
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o644 << 16
                    with open(full, "rb") as fh:
                        zf.writestr(info, fh.read())
        return out
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def main(argv: list[str]) -> int:
    version = argv[1] if len(argv) > 1 else "0.0.0"
    vdir = os.path.join(DIST, "v%s" % version)
    os.makedirs(vdir, exist_ok=True)
    files = tracked()
    built = []
    for name, spec in PACKAGES.items():
        path = build(name, spec, version, vdir, files)
        built.append(path)
        print("%-40s %8.1f KB" % (os.path.basename(path), os.path.getsize(path) / 1024.0))
    lines = []
    for path in built:
        digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
        lines.append("%s  %s" % (digest, os.path.basename(path)))
    write(os.path.join(vdir, "SHA256SUMS.txt"), "\n".join(lines) + "\n")
    print("wrote", os.path.join(vdir, "SHA256SUMS.txt"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
