from _harness import probe

# select needs a build with build >= 150; headless maps expose no such build,
# so the only thing observable here is "no crash".
CODE = 'select 1 0 0 0 0\nprint "|"\nprint @counter\n'

def check(rec):
    t = rec.get("text", "")
    if t == "":
        return (None, "select never executed headless")
    return (None, "text=%r: ran without crash, but build>=150 precondition is not observable headless" % (t,))

def main():
    return probe("L1-20", "select 需要 build >= 150（headless 不可判定）", CODE, check, steps=4)

if __name__ == "__main__":
    raise SystemExit(main())
