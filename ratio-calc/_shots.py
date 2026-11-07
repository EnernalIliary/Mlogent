import os, subprocess, tempfile, time, glob

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not os.path.exists(EDGE):
    cands = glob.glob(r"C:\Program Files*\Microsoft\Edge\Application\msedge.exe")
    EDGE = cands[0] if cands else EDGE

BASE = "file:///F:/OneDrive/%E6%A1%8C%E9%9D%A2/AtomicStates/ratio-calc/index.html"
OUT = r"F:\OneDrive\桌面\AtomicStates\ratio-calc\docs"
os.makedirs(OUT, exist_ok=True)

shots = [
    ("screenshot-building.png", "?mode=building&block=graphite-press&count=2&depth=4", "1180,2100"),
    ("screenshot-sources-power.png",
     "?mode=building&block=graphite-press&count=2&depth=4"
     "&src=coal:drill:laser-drill:8:0&gen=combustion-generator&genfuel=coal&gencount=0", "1180,2100"),
    ("screenshot-multi-power.png",
     "?mode=building&block=silicon-smelter&count=3&depth=4&boundary=coal,sand"
     "&src=sand:multi:disassembler&gen=steam-generator&genfuel=coal&gencount=0", "1180,2200"),
    ("screenshot-unit-factory.png", "?mode=building&block=ground-factory&count=1&depth=4", "1180,2100"),
    ("screenshot-unit-chain.png",
     "?mode=building&block=ground-factory&count=1&depth=4&chain=dagger&chainrate=0.05", "1180,2500"),
    ("screenshot-pump.png",
     "?mode=building&block=silicon-smelter&count=3&depth=4&boundary=coal,sand"
     "&src=sand:drill:laser-drill:8:1&src=water:pump:rotary-pump", "1180,2200"),
    ("screenshot-item.png", "?mode=item&item=silicon&rate=5&depth=3", "1180,2100"),
]
for name, q, win in shots:
    dst = os.path.join(OUT, name)
    if os.path.exists(dst):
        os.remove(dst)
    prof = tempfile.mkdtemp(prefix="msedge-shot-")
    cmd = [EDGE, "--headless=new", "--disable-gpu", "--no-sandbox", "--no-first-run",
           "--hide-scrollbars", "--user-data-dir=" + prof, "--window-size=" + win,
           "--virtual-time-budget=5000", "--screenshot=" + dst, BASE + q]
    p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        if os.path.exists(dst) and os.path.getsize(dst) > 20000:
            break
        time.sleep(1)
    time.sleep(1)
    try:
        p.kill()
    except Exception:
        pass
    print(name, os.path.getsize(dst) if os.path.exists(dst) else -1)
