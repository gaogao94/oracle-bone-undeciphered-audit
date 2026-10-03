# -*- coding: utf-8 -*-
"""测拓片 URL 的册号映射：大编号片号在哪一册"""
import io, os, sys, time, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Referer": "https://www.guoxuedashi.com/jgwhj/",
     "Accept": "image/avif,image/webp,image/png,image/*,*/*;q=0.8"}

# 已知：1 册覆盖约 1-? 片。测几个大编号找规律
TESTS = ["017382", "003209", "002454", "005373",
         "032009", "022454", "031983", "032513", "033286",
         "005250", "0030519", "0032577"]


def probe(p):
    for vol in range(1, 15):
        u = f"https://pic2.39017.com/jgwhj/{vol}/{p}.png"
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=15) as r:
                b = r.read()
            if len(b) > 1200:
                return vol, len(b)
        except Exception:
            pass
    return None, 0


for p in TESTS:
    v, n = probe(p)
    print(f"  {p} → 册 {v if v else '—'}  {n} bytes")
    time.sleep(0.2)
