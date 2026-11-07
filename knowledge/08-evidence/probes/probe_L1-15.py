from _harness import probe

# format takes ONE value and fills the LOWEST-numbered {n} placeholder already
# sitting in the text buffer (LExecutor.java:1111-1139), so it needs a prior print.
CODE = 'print "{0}-{1}"\nformat "a"\nformat "b"\n'

def check(rec):
    t = rec.get("text", "")
    return (t.startswith("a-b")), "text=%r (expect a-b; single-digit placeholders only)" % (t,)

def main():
    return probe("L1-15", "format 用 {0}/{1} 占位（正文需先 print，format 每次只填一个）", CODE, check, steps=3)

if __name__ == "__main__":
    raise SystemExit(main())
