# -*- coding: utf-8 -*-
"""看 HUST-OBC README，找数据集下载地址"""
import io, sys, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

urls = [
    "https://raw.githubusercontent.com/Pengjie-W/HUST-OBC/main/README.md",
    "https://api.github.com/repos/Pengjie-W/HUST-OBC/git/trees/main?recursive=1",
]
for u in urls:
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            t = r.read().decode("utf-8", "replace")
        print(f"===== {u}  len={len(t)}")
        print(t[:4000])
        print()
    except Exception as e:
        print(f"===== {u} ERR {e}")
