"""Parse every blueprint in the game schematics folder; report read-path coverage."""
import sys, os, glob, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import msch

SCHEM = r"C:\Users\lliary\AppData\Roaming\Mindustry\schematics"

files = sorted(glob.glob(os.path.join(SCHEM, "*.msch")))
ok = 0
errs = []
total_logic = 0
files_with_logic = 0
stmt_total = 0

for f in files:
    try:
        sch = msch.parse_file(f)
    except Exception as e:
        errs.append((os.path.basename(f), f"{type(e).__name__}: {e}"))
        continue
    ok += 1
    lt = sch.logic_tiles()
    if lt:
        files_with_logic += 1
        total_logic += len(lt)
        for t in lt:
            stmt_total += len(t.logic.statement_lines())

print(f"files        : {len(files)}")
print(f"parsed OK    : {ok}")
print(f"parse errors : {len(errs)}")
print(f"files w/ logic: {files_with_logic}")
print(f"logic blocks : {total_logic}")
print(f"statements   : {stmt_total}")
print()
if errs:
    print("--- errors (name | reason) ---")
    for n, why in errs:
        print(f"  {n} | {why}")
