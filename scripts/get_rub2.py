# -*- coding: utf-8 -*-
"""
用新获得的原拓能力，核验 󾥗 = 「娩」（《合集》17382）
同时取同片及对照片，目验字形
"""
import io, os, sys, gzip, time, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Referer": "https://www.guoxuedashi.com/jgwhj/",
     "Accept": "image/avif,image/webp,image/png,image/*,*/*;q=0.8"}

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "rubbings")
os.makedirs(OUT, exist_ok=True)

PLATES = ["017382", "003209", "002454", "0031983", "0032513", "005373", "0033286"]
for p in PLATES:
    got = False
    for vol in [str(i) for i in range(1, 14)]:
        u = f"https://pic2.39017.com/jgwhj/{vol}/{p}.png"
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=25) as r:
                b = r.read()
            if len(b) > 1500:
                open(os.path.join(OUT, p + ".png"), "wb").write(b)
                print(f"  OK {u}  {len(b)} bytes")
                got = True
                break
        except Exception:
            continue
        time.sleep(0.1)
    if not got:
        print(f"  {p}: 未找到")
