#!/usr/bin/env python3
"""Compile a server Kotlin script in a disposable, non-hosting Mindustry JVM.

Copy the live server's config (except saves and runtime data) into a temporary
world root, then ask ScriptAgent to load the selected script there. This avoids
compiling a first-time script load on the public game process.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

from world_runtime import WorldPaths  # noqa: E402
import world_server  # noqa: E402

DEFAULT_DATA = Path(world_server.default_paths().data)
DEFAULT_JAR = Path(world_server.DEFAULT_JAR)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('script', help='ScriptAgent script path or id, for example wayzer/user/nameExt.kts')
    parser.add_argument('--source-data', type=Path, default=DEFAULT_DATA,
                        help='live server data directory containing config/scripts and config/mods')
    parser.add_argument('--jar', type=Path, default=DEFAULT_JAR)
    parser.add_argument('--java', help='Java executable; defaults to world_server Java discovery')
    parser.add_argument('--keep', action='store_true', help='keep the disposable directory for inspection')
    return parser


def _script_id(value: str) -> str:
    value = value.replace('\\', '/').strip('/')
    if not value or not re.fullmatch(r'[A-Za-z0-9_./-]+', value) or '..' in value.split('/'):
        raise ValueError('script must be a relative ScriptAgent path using letters, digits, dot, underscore, slash or hyphen')
    return value


def _copy_config(source_data: Path, target_data: Path) -> None:
    source = source_data / 'config'
    if not (source / 'scripts').is_dir():
        raise FileNotFoundError(f'no ScriptAgent scripts directory: {source / "scripts"}')
    if not (source / 'mods').is_dir():
        raise FileNotFoundError(f'no mods directory: {source / "mods"}')
    target_config = target_data / 'config'
    target_config.mkdir(parents=True)
    ignored = {'saves', 'logs', 'maps', 'mod-backups', 'assets'}
    for entry in source.iterdir():
        target = target_config / entry.name
        if entry.name in ignored:
            continue
        if entry.is_dir():
            shutil.copytree(entry, target, dirs_exist_ok=True)
        elif entry.is_file():
            shutil.copy2(entry, target)


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        script = _script_id(args.script)
        source_data = args.source_data.resolve()
        if not args.jar.is_file():
            raise FileNotFoundError(f'Mindustry jar not found: {args.jar}')
        if os.name != 'nt':
            try:
                os.nice(10)
            except OSError:
                pass
        temp_parent = ROOT / 'out' / '_world_compile'
        temp_parent.mkdir(parents=True, exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix='stage-', dir=temp_parent))
        paths = WorldPaths.from_root(stage)
        _copy_config(source_data, Path(paths.data))
        print(f'[offline] isolated config: {paths.data}', flush=True)
        print('[offline] starting JVM without hosting a map or opening a game port', flush=True)
        world = world_server.World(world_server.find_java(args.java), str(args.jar.resolve()),
                                   map_name=None, host=False, paused=True,
                                   server_name='offline-script-compile', paths=paths,
                                   no_push_admin=True)
        try:
            result = world.console('sa load ' + script, quiet=1.0, timeout=180)
            lines = result.get('lines', [])
            for line in lines:
                print(line)
            output = '\n'.join(lines)
            if re.search(r'(?i)(compilationerror|failed to compile|script compilation failed)', output):
                return 1
            print('[offline] ScriptAgent load command completed; inspect output above for script-specific diagnostics.')
        finally:
            world.close(force=True)
        if args.keep:
            print(f'[offline] preserved staging directory: {stage}')
        else:
            shutil.rmtree(stage, ignore_errors=True)
        return 0
    except Exception as exc:
        print(f'[offline] {type(exc).__name__}: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
