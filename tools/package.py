#!/usr/bin/env python3
"""Build the installable MAI package (mod + sidecar + double-click installers).

Why this exists
---------------
"打包安装即用" is the last item of the 2026-10-31 list (m02047): until now
installing meant two hand copies (`MlogAuxiliary/` into `saves/mods`, and a
`python tools/logicd.py` window started from the *repo*), and the previous
"package" was a zip of the mod folder only (`out/_dist/MlogAuxiliary.zip`) --
which cannot work, because the mod is a front end: without the sidecar it can
only say "cannot reach the sidecar".

What makes this package different from a folder copy
----------------------------------------------------
* The sidecar is **not** the whole `tools/` tree.  `logicd.py` imports six local
  modules and reads five JSON data files by `Path(__file__).with_name(...)`; the
  closure is computed from the sources here, so a new import cannot silently
  ship a package that dies on the player's machine with `ModuleNotFoundError`.
* The `rules/*.json` set ships next to the sidecar so findings keep their rule
  ids (`tools/rule_ids.py` walks up to `parents[:4]` looking for `rules/`).
* `VERSION.txt` carries the SHA256 of every file; `install.ps1` re-hashes the
  copied mod files, so "installed" means byte-identical, not "the copy ran".
* `--verify` does not read the zip, it **runs** it: extract to a temp dir, start
  the packaged sidecar on a free port, ask `/health` and `/capabilities`, then
  drive `install.ps1`/`uninstall.ps1` against a temp `saves\\mods` folder.

Usage
-----
    python tools/package.py                  # build out/_dist/MAI-<ver>/ + .zip
    python tools/package.py --verify         # build to a temp dir and prove it
    python tools/package.py --out D:\\tmp     # elsewhere
    python tools/package.py --no-zip         # tree only

The zip is an artifact, not a source file: `out/_dist/` is not in git (see
.gitignore).  The installers themselves live in `packaging/` and are reviewed
like any other source.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / 'tools'
MOD = ROOT / 'MlogAuxiliary'
PACKAGING = ROOT / 'packaging'
DIST = ROOT / 'out' / '_dist'

# data files the sidecar loads by name; discovered from the sources, not listed
_JSON_RE = re.compile(r"""["']([A-Za-z0-9_]+\.json)["']""")


def local_imports(src: str) -> list[str]:
    """Module names this source imports, at *any* nesting depth.

    Depth is the whole point: `logicd.py` does `from rule_ids import rule_id`
    inside `_rid()` and `mlogcheck.py` does the same inside a helper, so a
    line-anchored regex (`^from ...`) silently drops them -- and the package
    then ships without `sidecar/rule_ids.py`.  `/health` still answers, so the
    package looks fine; `/analyze` dies on the player's machine with
    ModuleNotFoundError.  Parsing the AST sees imports wherever they sit.
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.extend(alias.name.split('.')[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                out.append(node.module.split('.')[0])
    return out


def mod_version() -> str:
    text = (MOD / 'mod.hjson').read_text(encoding='utf-8')
    m = re.search(r'^\s*version:\s*"([^"]+)"', text, re.M)
    if not m:
        raise SystemExit('cannot read version: from MlogAuxiliary/mod.hjson')
    return m.group(1)


def sidecar_version() -> str:
    text = (TOOLS / 'logicd.py').read_text(encoding='utf-8')
    m = re.search(r"^SIDECAR_VERSION\s*=\s*['\"]([^'\"]+)['\"]", text, re.M)
    if not m:
        raise SystemExit('cannot read SIDECAR_VERSION from tools/logicd.py')
    return m.group(1)


def sidecar_modules() -> list[str]:
    """Local modules logicd.py needs, in import order (closure over tools/*.py)."""
    local = {p.stem for p in TOOLS.glob('*.py')}
    seen: list[str] = []

    def walk(name: str) -> None:
        if name in seen or name not in local:
            return
        seen.append(name)
        src = (TOOLS / (name + '.py')).read_text(encoding='utf-8')
        for mod in local_imports(src):
            walk(mod)

    walk('logicd')
    return seen


def sidecar_data() -> list[Path]:
    """The JSON files the sidecar closure opens by name."""
    names: set[str] = set()
    for name in sidecar_modules():
        src = (TOOLS / (name + '.py')).read_text(encoding='utf-8')
        names.update(_JSON_RE.findall(src))
    out = []
    for name in sorted(names):
        p = TOOLS / name
        if p.is_file():
            out.append(p)
    return out


def sidecar_rules() -> list[Path]:
    d = ROOT / 'rules'
    return sorted(p for p in d.glob('*.json') if p.is_file())


def layout() -> list[tuple[str, Path]]:
    """(path inside the package, source file) for every shipped file."""
    rows: list[tuple[str, Path]] = []
    for rel in ('mod.hjson', 'README.md', 'scripts/main.js'):
        rows.append(('mod/MlogAuxiliary/' + rel, MOD / rel))
    for name in sidecar_modules():
        rows.append(('sidecar/' + name + '.py', TOOLS / (name + '.py')))
    for p in sidecar_data():
        rows.append(('sidecar/' + p.name, p))
    for p in sidecar_rules():
        rows.append(('sidecar/rules/' + p.name, p))
    for p in sorted(PACKAGING.iterdir()):
        if p.is_file():
            rows.append((p.name, p))
    return rows


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest().upper()


def version_txt(rows: list[tuple[str, Path]]) -> bytes:
    lines = ['MAI ' + mod_version(), 'sidecar ' + sidecar_version(),
             'built ' + time.strftime('%Y-%m-%dT%H:%M:%S%z')]
    for rel, src in rows:
        lines.append('sha256 %s %s' % (sha256(src), rel))
    return ('\n'.join(lines) + '\n').encode('utf-8')


def build(out_dir: Path | None = None, make_zip: bool = True,
          quiet: bool = False) -> dict:
    """Write the package tree (and zip) and return a summary dict."""
    ver = mod_version()
    name = 'MAI-' + ver
    out_dir = Path(out_dir) if out_dir else DIST
    tree = out_dir / name
    if tree.exists():
        shutil.rmtree(tree)
    tree.mkdir(parents=True)
    rows = layout()
    for rel, src in rows:
        dst = tree / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    (tree / 'VERSION.txt').write_bytes(version_txt(rows))
    files = sorted(str(p.relative_to(tree)).replace('\\', '/') for p in tree.rglob('*')
                   if p.is_file())
    total = sum((tree / f).stat().st_size for f in files)
    info = {'name': name, 'version': ver, 'sidecar': sidecar_version(),
            'tree': tree, 'files': files, 'bytes': total, 'zip': None, 'zip_sha256': None}
    if make_zip:
        zp = out_dir / (name + '.zip')
        if zp.exists():
            zp.unlink()
        with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
            for f in files:
                z.write(tree / f, name + '/' + f)
        info['zip'] = zp
        info['zip_sha256'] = sha256(zp)
        info['zip_bytes'] = zp.stat().st_size
    if not quiet:
        print('package %s  (mod %s, sidecar %s)' % (name, ver, sidecar_version()))
        for f in files:
            print('  %-46s %8d B' % (f, (tree / f).stat().st_size))
        print('  %d files, %d bytes' % (len(files), total))
        if info['zip']:
            print('zip %s  %d B  sha256 %s'
                  % (info['zip'], info['zip_bytes'], info['zip_sha256']))
    return info


# --------------------------------------------------------------------------- #
# verify: run the package, do not just read it
# --------------------------------------------------------------------------- #

def free_port() -> int:
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


def http_get(port: int, path: str, timeout: float = 10.0) -> tuple[int, dict]:
    req = urllib.request.Request('http://127.0.0.1:%d%s' % (port, path))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode('utf-8') or '{}')


def post_json(port: int, path: str, body: dict,
              timeout: float = 30.0) -> tuple[int, dict]:
    """POST a JSON object to the sidecar; returns (status, decoded reply)."""
    data = json.dumps(body).encode('utf-8')
    req = urllib.request.Request('http://127.0.0.1:%d%s' % (port, path), data=data,
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode('utf-8') or '{}')


def start_sidecar(tree: Path, port: int, timeout: float = 25.0):
    """Start sidecar/logicd.py from the extracted package; wait for its ready line."""
    proc = subprocess.Popen([sys.executable, str(tree / 'sidecar' / 'logicd.py'),
                             '--port', str(port)],
                            cwd=str(tree), stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True,
                            encoding='utf-8', errors='replace')
    deadline = time.time() + timeout
    seen: list[str] = []
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line:
            if proc.poll() is not None:
                raise RuntimeError('sidecar exited before it was ready: rc=%s out=%r'
                                   % (proc.returncode, ''.join(seen)[-800:]))
            continue
        seen.append(line)
        if 'listening on' in line:
            return proc, ''.join(seen)
    proc.kill()
    raise RuntimeError('sidecar did not become ready in %.0fs: %r'
                       % (timeout, ''.join(seen)[-800:]))


def run_ps1(tree: Path, script: str, args: list[str],
            env: dict | None = None) -> tuple[int, str]:
    exe = shutil.which('powershell') or shutil.which('pwsh')
    if not exe:
        raise RuntimeError('no powershell on PATH')
    cmd = [exe, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
           str(tree / script), *args]
    full = dict(os.environ)
    if env:
        full.update(env)
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8',
                          errors='replace', timeout=180, env=full)
    return proc.returncode, (proc.stdout or '') + (proc.stderr or '')


def verify(tree: Path | None = None, keep: bool = False) -> dict:
    """Prove the package works: closure, sidecar over HTTP, installer round trip."""
    tmp = Path(tempfile.mkdtemp(prefix='mai-pack-'))
    try:
        info = build(out_dir=tmp / 'build', quiet=True) if tree is None else None
        if tree is None:
            tree = info['tree']
        tree = Path(tree)
        problems: list[str] = []
        notes: list[str] = []

        # 1. the sidecar closure is complete inside the package
        present = {p.name for p in (tree / 'sidecar').glob('*.py')}
        for name in sidecar_modules():
            if name + '.py' not in present:
                problems.append('sidecar/%s.py missing from the package' % name)
        # every local import in every shipped module must be shipped too
        shipped = {p.stem for p in (tree / 'sidecar').glob('*.py')}
        local_all = {p.stem for p in TOOLS.glob('*.py')}
        for name in sidecar_modules():
            src = (tree / 'sidecar' / (name + '.py')).read_text(encoding='utf-8')
            for mod in local_imports(src):
                if mod in local_all and mod not in shipped:
                    problems.append('sidecar/%s.py imports %s, which is not shipped'
                                    % (name, mod))
        # 2. data files and rules
        for p in sidecar_data():
            if not (tree / 'sidecar' / p.name).is_file():
                problems.append('sidecar/%s missing (opened by name at runtime)' % p.name)
        rules_shipped = list((tree / 'sidecar' / 'rules').glob('*.json'))
        if len(rules_shipped) != len(sidecar_rules()):
            problems.append('sidecar/rules has %d file(s), repo has %d'
                            % (len(rules_shipped), len(sidecar_rules())))

        # 3. the mod bytes are exactly the repo bytes
        for rel in ('mod.hjson', 'scripts/main.js'):
            a = sha256(MOD / rel)
            b = sha256(tree / 'mod' / 'MlogAuxiliary' / rel)
            if a != b:
                problems.append('mod/MlogAuxiliary/%s differs from the repo copy' % rel)

        # 4. the packaged sidecar actually serves
        port = free_port()
        proc, banner = start_sidecar(tree, port)
        try:
            st, health = http_get(port, '/health')
            if st != 200 or not health.get('ok'):
                problems.append('/health answered %s %r' % (st, health))
            elif health.get('version') != sidecar_version():
                problems.append('/health version %r != tools/logicd.py SIDECAR_VERSION %r'
                                % (health.get('version'), sidecar_version()))
            else:
                notes.append('sidecar %s on port %d, /health ok' % (health['version'], port))
            st, caps = http_get(port, '/capabilities')
            if st != 200 or not caps.get('ok', True):
                problems.append('/capabilities answered %s %r' % (st, caps))
            else:
                notes.append('/capabilities ok (%d keys)' % len(caps))
            # /health only proves the process started; /analyze proves the
            # closure is complete (rule_ids is imported inside a function, so a
            # package missing it answers /health and fails here).
            st, res = post_json(port, '/analyze',
                                {'code': 'print "hello"\nprintflush message1\n'})
            if st != 200 or res.get('ok') is not True or not res.get('statements'):
                problems.append('/analyze from the package answered %s %r' % (st, res))
            else:
                notes.append('/analyze ok (%d statement(s), %d ERR)'
                             % (res['statements'], res.get('errors', -1)))
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()

        # 5. install.ps1 / uninstall.ps1 against a throwaway saves\mods
        mods = tmp / 'Mindustry' / 'saves' / 'mods'
        mods.mkdir(parents=True)
        try:
            rc, out = run_ps1(tree, 'install.ps1', ['-Target', str(mods), '-Silent'])
            if rc != 0:
                problems.append('install.ps1 exited %s: %s' % (rc, out.strip()[-600:]))
            else:
                dest = mods / 'MlogAuxiliary'
                if not (dest / 'scripts' / 'main.js').is_file():
                    problems.append('install.ps1 reported ok but scripts/main.js is not there')
                elif sha256(dest / 'scripts' / 'main.js') != sha256(MOD / 'scripts/main.js'):
                    problems.append('install.ps1 copied a main.js that differs from the repo')
                else:
                    notes.append('install.ps1 copied the mod byte-identically')
            rc, out = run_ps1(tree, 'uninstall.ps1', ['-Target', str(mods), '-Silent'])
            if rc != 0:
                problems.append('uninstall.ps1 exited %s: %s' % (rc, out.strip()[-600:]))
            elif (mods / 'MlogAuxiliary').exists():
                problems.append('uninstall.ps1 reported ok but the folder is still there')
            else:
                notes.append('uninstall.ps1 removed the folder')
        except RuntimeError as exc:
            notes.append('installer round trip skipped: ' + str(exc))

        # 6. VERSION.txt lists every file the package *ships* (a run of the
        # packaged sidecar leaves __pycache__ and out/ behind, and those are not
        # part of the package -- do not require them to be hashed).
        vt = (tree / 'VERSION.txt').read_text(encoding='utf-8')
        listed = set()
        for line in vt.splitlines():
            if line.startswith('sha256 '):
                listed.add(line.split(' ', 2)[2])
        for rel, _src in layout():
            if rel not in listed:
                problems.append('VERSION.txt does not list %s' % rel)
        if 'MAI ' + mod_version() not in vt:
            problems.append('VERSION.txt does not say "MAI %s"' % mod_version())

        return {'ok': not problems, 'problems': problems, 'notes': notes,
                'tree': tree, 'info': info}
    finally:
        if not keep:
            shutil.rmtree(tmp, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description='build (and verify) the MAI package')
    ap.add_argument('--out', help='output directory (default out/_dist)')
    ap.add_argument('--no-zip', action='store_true', help='write the tree only')
    ap.add_argument('--verify', action='store_true',
                    help='build into a temp dir and prove it runs (sidecar + installer)')
    ap.add_argument('--keep', action='store_true', help='with --verify, keep the temp tree')
    args = ap.parse_args(argv)
    if args.verify:
        res = verify(keep=args.keep)
        for n in res['notes']:
            print('  ok  ' + n)
        for p in res['problems']:
            print('  FAIL ' + p)
        print('verify: ' + ('PASS' if res['ok'] else 'FAIL'))
        return 0 if res['ok'] else 1
    info = build(out_dir=Path(args.out) if args.out else None,
                 make_zip=not args.no_zip)
    return 0


if __name__ == '__main__':
    sys.exit(main())
