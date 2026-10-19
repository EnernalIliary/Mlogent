"""
extract_logic.py -- Extract every logic processor's source code from all .msch
blueprints in the Mindustry schematics folder into a browsable corpus.
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import msch

SCHEM = r"C:\Users\lliary\AppData\Roaming\Mindustry\schematics"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "logic-corpus")

LOGIC_BLOCKS = {"micro-processor", "logic-processor", "hyper-processor",
                "world-processor", "memory-bank", "memory-cell",
                "large-logic-display", "logic-display"}


def safe(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")
    return name[:110] or "unnamed"


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    by_blueprint = os.path.join(OUT, "by-blueprint")
    os.makedirs(by_blueprint, exist_ok=True)

    files = sorted(f for f in os.listdir(SCHEM) if f.lower().endswith(".msch"))
    index: list[dict] = []
    errors: list[dict] = []
    proc_total = 0
    stmt_total = 0

    for fname in files:
        path = os.path.join(SCHEM, fname)
        base = fname[:-5]
        try:
            sch = msch.parse_file(path)
        except Exception as e:
            errors.append({"file": fname, "error": f"{type(e).__name__}: {e}"})
            continue

        logic_tiles = sch.logic_tiles()
        if not logic_tiles:
            continue

        # stable, readable ordering: by y then x, as the game lays them out
        logic_tiles.sort(key=lambda t: (t.y, t.x))

        lines = [
            f"# {sch.name}",
            "",
            f"- file: `{fname}`",
            f"- size: {sch.width}x{sch.height}",
            f"- blocks: {len(sch.tiles)}",
            f"- labels: {sch.labels}",
            f"- logic blocks: {len(logic_tiles)}",
            "",
        ]
        for i, t in enumerate(logic_tiles):
            lg = t.logic
            assert lg is not None
            stmts = lg.statement_lines()
            stmt_total += len(stmts)
            proc_total += 1
            lines.append("---")
            lines.append("")
            lines.append(f"## [{i}] `{t.block}` at ({t.x},{t.y}) rot={t.rotation}")
            lines.append("")
            if lg.links:
                lines.append("**Links:** " +
                             ", ".join(f"`{l.name}`@({l.x},{l.y})" for l in lg.links))
                lines.append("")
            lines.append(f"**{len(stmts)} statements**")
            lines.append("")
            lines.append("```mlog")
            lines.append(lg.code.rstrip("\n") if lg.code else "")
            lines.append("```")
            lines.append("")

        out_path = os.path.join(by_blueprint, safe(base) + ".md")
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))

        index.append({
            "file": fname,
            "name": sch.name,
            "width": sch.width,
            "height": sch.height,
            "tiles": len(sch.tiles),
            "labels": sch.labels,
            "logic_blocks": [
                {
                    "block": t.block,
                    "x": t.x, "y": t.y, "rotation": t.rotation,
                    "statements": len(t.logic.statement_lines()),
                    "links": [l.name for l in t.logic.links],
                }
                for t in logic_tiles
            ],
            "corpus_file": os.path.relpath(out_path, OUT).replace("\\", "/"),
        })

    with open(os.path.join(OUT, "index.json"), "w", encoding="utf-8") as fh:
        json.dump({"blueprints": index, "errors": errors}, fh,
                  ensure_ascii=False, indent=1)

    print(f"blueprints with logic : {len(index)}")
    print(f"logic blocks extracted: {proc_total}")
    print(f"statements            : {stmt_total}")
    print(f"parse errors          : {len(errors)}")
    print(f"output                : {OUT}")


if __name__ == "__main__":
    main()
