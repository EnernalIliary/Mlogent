from _harness import probe

# Draw instructions must not throw in headless mode; the counter keeps advancing.
CODE = 'draw clear 0 0 0 0 0 0\ndraw color 255 0 0 255 0 0\ndraw rect 0 0 10 10 0 0\ndrawflush\n'

def check(rec):
    c = rec.get("counter")
    return (isinstance(c, (int, float)) and c >= 0), "counter=%r (no exception; execution advanced)" % (c,)

def main():
    return probe("L1-21", "headless 下 draw 系指令不报错", CODE, check, steps=10)

if __name__ == "__main__":
    raise SystemExit(main())
