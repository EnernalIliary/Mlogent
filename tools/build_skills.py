"""Build standalone skills from the canonical tools/ source tree.

python tools/build_skills.py             # dist/skills (new directory required)
python tools/build_skills.py --verify-only  # temporary build, no installed writes
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil
import os
import stat
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent


def source_files() -> list[Path]:
    """Use tracked working-tree bytes, excluding local scratch and installations."""
    result = subprocess.run(['git', '-C', str(ROOT), 'ls-files', '-z'],
                            capture_output=True, check=True)
    return sorted(Path(name) for name in result.stdout.decode('utf-8').split('\0')
                  if name and (ROOT / name).is_file())


def copy_sources(files: list[Path], source: Path, target: Path) -> None:
    for relative in files:
        if not relative.is_relative_to(source):
            continue
        tail = relative.relative_to(source)
        if 'tools' in tail.parts or '__pycache__' in tail.parts or relative.suffix == '.pyc':
            continue
        output = target / tail
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, output)


def build(dest: Path) -> None:
    """Write a fresh destination; never overwrite an installed skill."""
    files = source_files()
    sources = {
        'mlog-agentskill': Path('.dsh/skills/mlog-agentskill'),
        'mindustry-blueprint': Path('mindustry-blueprint'),
    }
    for source in sources.values():
        if source / 'SKILL.md' not in files:
            raise RuntimeError(f'missing tracked skill source: {source}/SKILL.md')
    dest.mkdir(parents=True, exist_ok=False)
    payload = [p for p in files if p.parent == Path('tools')
               and p.suffix in {'.py', '.json'} and not p.name.startswith('_')]
    for name, source in sources.items():
        target = dest / name
        copy_sources(files, source, target)
        tools = target / 'tools'
        tools.mkdir()
        for relative in payload:
            shutil.copyfile(ROOT / relative, tools / relative.name)
        manifest = ''.join(
            f'{hashlib.sha256(p.read_bytes().replace(bytes([13, 10]), bytes([10]))).hexdigest()}  {p.name}\n'
            for p in sorted(tools.iterdir()))
        (tools / 'MANIFEST.sha256').write_text(manifest, encoding='utf-8')
        copy_sources(files, Path('rules'), target / 'rules')


def remove_generated(path: Path, skill: Path) -> None:
    if not path.resolve().is_relative_to(skill.resolve()):
        raise ValueError(f'cleanup outside skill: {path}')
    def writable(func, target, exc):
        os.chmod(target, stat.S_IWRITE)
        func(target)
    shutil.rmtree(path, onerror=writable)


def verify(dest: Path) -> None:
    for name in ('mlog-agentskill', 'mindustry-blueprint'):
        skill = dest / name
        subprocess.run([sys.executable, '-I', '-B', str(skill / 'tools/mlogagent.py'),
                        'info', '--verify'], cwd=skill, check=True,
                       stdout=subprocess.DEVNULL)
        # Golden behavior must also survive relocation without the source tree.
        shutil.copytree(ROOT / 'tests', skill / 'tests', copy_function=shutil.copyfile,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        try:
            for test in ('run_tests.py', 'service/run_service_tests.py', 'http/run_http_tests.py', 'runtime/run_runtime_tests.py', 'cli/run_cli_tests.py', 'world/run_transport_tests.py', 'world/run_process_tests.py', 'world/run_channel_tests.py', 'world/run_query_tests.py', 'world/run_edit_tests.py', 'world/run_schematic_tests.py', 'world/run_map_tests.py', 'world/run_scene_tests.py', 'world/run_projection_tests.py', 'world/run_projection_action_tests.py', 'world/run_display_tests.py', 'world/run_mirror_tests.py', 'world/run_door_tests.py'):
                subprocess.run([sys.executable, '-I', '-B', str(skill / 'tests' / test)],
                               cwd=skill, check=True)
        finally:
            remove_generated(skill / 'tests', skill)
            for cache in list(skill.rglob('__pycache__')):
                if cache.is_dir():
                    remove_generated(cache, skill)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'dist/skills')
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if args.verify_only:
        with tempfile.TemporaryDirectory(prefix='mlog-skills-') as tmp:
            dest = Path(tmp) / 'skills'
            build(dest)
            verify(dest)
    else:
        build(args.out)
        verify(args.out)
        print(f'Built skills: {args.out.resolve()}')


if __name__ == '__main__':
    main()
