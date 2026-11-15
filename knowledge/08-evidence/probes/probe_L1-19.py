from _harness import probe

# Unit fields are in tiles / plain units: fortress range 29.5, health 900, half-tile pos offset.
CODE = 'ubind @fortress\nsensor rg @unit @range\nsensor hp @unit @health\nsensor ux @unit @x\nprint rg\nprint "|"\nprint hp\nprint "|"\nprint ux\n'

def check(rec):
    v = rec.get("vars") or {}
    if v.get("rg") in (None, "null"):
        return (None, "no @fortress on the headless map; ubind found no unit (needs a scene with fortress)")
    return (str(v.get("rg")) == "29.5" and str(v.get("hp")) == "900"), "range=%r health=%r x=%r" % (v.get("rg"), v.get("hp"), v.get("ux"))

def main():
    return probe("L1-19", "@x/@y/@range 以 tile 为单位（fortress range 29.5/health 900）", CODE, check, ticks=3)

if __name__ == "__main__":
    raise SystemExit(main())
