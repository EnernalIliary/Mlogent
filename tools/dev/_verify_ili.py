"""Verify the ILI tagging: every touched file keeps its tiles, its logic code and
its previous label order; exactly one label was appended."""
import pathlib
import sys

sys.path.insert(0, "mindustry-blueprint/tools")
import msch

ROOT = pathlib.Path(__file__).resolve().parents[1]
C = pathlib.Path.home() / "AppData" / "Roaming" / "Mindustry" / "schematics"
backup = sorted((ROOT / "out").glob("_ili_backup_*"))[-1]

bad = 0
checked = 0
for orig in sorted(backup.glob("*.msch")):
    live = C / orig.name
    a = msch.parse_file(str(orig))
    b = msch.parse_file(str(live))
    checked += 1
    same_tiles = [t.block for t in a.tiles] == [t.block for t in b.tiles]
    same_logic = ("\n".join(t.logic.code for t in a.logic_tiles())
                  == "\n".join(t.logic.code for t in b.logic_tiles()))
    la = [l for l in a.labels if l.strip()]
    lb = [l for l in b.labels if l.strip()]
    appended = lb[:len(la)] == la and len(lb) == len(la) + 1 and lb[-1].endswith("ILI")
    if not (same_tiles and same_logic and appended):
        bad += 1
        print(f"  !! {orig.name}: tiles={same_tiles} logic={same_logic} appended={appended}")

print(f"核对 {checked} 份：异常 {bad} 份")
