"""Sync the checked-in DSH Markdown from the canonical blueprint skill."""

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'mindustry-blueprint'
INSTALL = ROOT / '.dsh/skills/mindustry-blueprint'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='report drift without writing')
    args = parser.parse_args()

    sources = sorted(SOURCE.glob('*.md'))
    if not (SOURCE / 'SKILL.md').is_file():
        parser.error('canonical blueprint skill is missing SKILL.md')
    expected_names = {source.name for source in sources}
    unexpected = sorted(path.name for path in INSTALL.glob('*.md') if path.name not in expected_names)
    if unexpected:
        parser.error('installation has Markdown without a canonical source: ' + ', '.join(unexpected))

    if not args.check:
        INSTALL.mkdir(parents=True, exist_ok=True)
    drift = []
    for source in sources:
        target = INSTALL / source.name
        # The DSH copy is two directories deeper than the canonical skill.
        expected = source.read_text(encoding='utf-8').replace('](../', '](../../../')
        if target.is_file() and target.read_text(encoding='utf-8') == expected:
            continue
        if args.check:
            drift.append(source.name)
        else:
            target.write_text(expected, encoding='utf-8', newline='\n')

    if drift:
        parser.error('run without --check to sync: ' + ', '.join(drift))
    print(f'{len(sources)} blueprint skill documents in sync')


if __name__ == '__main__':
    main()
