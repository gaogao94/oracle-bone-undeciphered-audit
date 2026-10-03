# -*- coding: utf-8 -*-
"""下载《合集》5250 等片的拓片图，看 󺡅 在原拓中的实际字形"""
import io, os, sys, gzip, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Referer": "https://www.guoxuedashi.com/jgwhj/",
     "Accept": "image/avif,image/webp,image/png,image/*,*/*;q=0.8"}

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "rubbings")
os.makedirs(OUT, exist_ok=True)

PLATES = ["005250", "005252", "005253", "005254", "005259", "005305", "005326"]
# 该站图分册目录，先试 1 册
for p in PLATES:
    ok = False
    for vol in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13"]:
        u = f"https://pic2.39017.com/jgwhj/{vol}/{p}.png"
        try:
            req = urllib.request.Request(u, headers=H)
            with urllib.request.urlopen(req, timeout=30) as r:
                b = r.read()
            if len(b) > 2000:
                fp = os.path.join(OUT, f"{p}.png")
                open(fp, "wb").write(b)
                print(f"  OK {u}  {len(b)} bytes → {fp}")
                ok = True
                break
        except Exception as e:
            continue
    if not ok:
        print(f"  {p}: 未找到")
