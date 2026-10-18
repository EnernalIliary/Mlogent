#!/usr/bin/env python3
"""Vendor the mlog toolchain into the standalone `mlogagent` skill.

The `mlogagent` skill is meant to be self-contained: copy
`.dsh/skills/mlog-agentskill` somewhere else and it still runs, without the rest of
this repo.  That means the skill carries its own copy of every module and data
file, and this script is the one place that produces that copy -- so "which
version is in the skill" never becomes a guess.

Only the *tools* are synced.  `mlogagent/SKILL.md` is authored in place: it
belongs to that skill alone, while `mindustry-blueprint/SKILL.md` is a different
document.  (Copying it here once clobbered the playbook and silently removed the
skill from the catalog -- hence the explicit exclusion below.)

    python tools/sync_mlogagent.py            # copy + rewrite MANIFEST.sha256
    python tools/sync_mlogagent.py --check    # compare only, exit 1 if stale

Run it after touching any module listed in `mlogagent._MODULES`, then
`python .dsh/skills/mlog-agentskill/tools/mlogagent.py info --verify` to confirm.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _repo_root(start: Path) -> Path:
    """Find the checkout root by looking for `.dsh/skills`.

    This script lives in two places at *different depths*
    (`mindustry-blueprint/tools/` and, after the sync, `tools/`), so a fixed
    `parents[N]` resolves correctly in one and silently lands one level too high
    in the other (symptom: "skill directory not found").  Walking up until the
    marker appears keeps both copies honest.
    """
    for p in [start, *start.parents]:
        if (p / ".dsh" / "skills").is_dir():
            return p
    return start.parent


ROOT = _repo_root(HERE)
SKILL = ROOT / ".dsh" / "skills" / "mlog-agentskill"
DEST = SKILL / "tools"

sys.path.insert(0, str(HERE))
import mlogagent  # noqa: E402  (needs the sys.path line above)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def payload() -> list[str]:
    """Modules + data files, in a stable order.  Never SKILL.md."""
    return list(mlogagent._MODULES) + list(mlogagent._DATA)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="do not write; report what differs from the skill copy")
    args = ap.parse_args(argv)

    if not SKILL.is_dir():
        print(f"!! skill directory not found: {SKILL}")
        return 2

    names = payload()
    stale: list[str] = []

    if args.check:
        for n in names:
            dst = DEST / n
            if not dst.exists():
                stale.append(f"{n}: missing from the skill")
            elif sha256(HERE / n) != sha256(dst):
                stale.append(f"{n}: differs")
    else:
        DEST.mkdir(parents=True, exist_ok=True)
        for n in names:
            shutil.copy2(HERE / n, DEST / n)
        lines = [f"{sha256(DEST / n)}  {n}" for n in names]
        (DEST / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", "utf-8")

    if stale:
        print(f"STALE  {len(stale)} file(s) differ from {HERE}:")
        for s in stale:
            print(f"  {s}")
        print("run: python tools/sync_mlogagent.py")
        return 1

    print(f"ok     {len(names)} tool file(s) vendored into {DEST}")
    print(f"       manifest: {DEST / 'MANIFEST.sha256'}")
    if not args.check:
        print("verify : python .dsh/skills/mlog-agentskill/tools/mlogagent.py info --verify")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
