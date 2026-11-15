from _harness import probe

# \n in a string becomes a real newline; text buffer caps at ~400 chars.
PAY = "a" * 450
CODE = 'print "L1\\nL2"\nprint "' + PAY + '"\n'

def check(rec):
    t = rec.get("text", "")
    nl = ("L1\nL2" in t)
    return (nl and len(t) < 450), "newline_ok=%s len(text)=%d (buffer truncation)" % (nl, len(t))

def main():
    return probe("L1-14", "print 的 \\n 换行；文本缓冲约 400 字符", CODE, check, steps=6)

if __name__ == "__main__":
    raise SystemExit(main())
