# -*- coding: utf-8 -*-
"""从样式表定位 ICS4 字体文件，用于解出 PUA 码位"""
import io, os, re, sys, gzip, json, urllib.parse, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Accept-Language": "zh-CN,zh;q=0.9", "Accept-Encoding": "gzip, deflate"}


def get(u, t=40, raw=False):
    with urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=t) as r:
        b = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            b = gzip.decompress(b)
        return b if raw else b.decode("utf-8", "replace")


for css in ["https://www.guoxuedashi.com/img/style.css?20262",
            "https://www.guoxuedashi.com/img/style.css"]:
    try:
        t = get(css)
    except Exception as e:
        print(f"{css} ERR {e}")
        continue
    print("=" * 92)
    print(f"{css}  len={len(t)}")
    print("=" * 92)
    for m in re.finditer(r"@font-face\s*\{[^}]*\}", t, re.I):
        print("  @font-face:", re.sub(r"\s+", " ", m.group(0))[:300])
    hits = re.findall(r"ICS4[^;}\n]{0,120}", t, re.I)
    print("  ICS4 出现:", hits[:8])
    urls = set(re.findall(r"url\((['\"]?)([^)'\"]+\.(?:woff2?|ttf|otf|eot))\1\)", t, re.I))
    print("  字体 URL:", list(urls)[:10])
    # 从 style.css 里找 @import
    print("  @import:", re.findall(r"@import[^;]{0,120}", t)[:6])
    break

print("\n" + "=" * 92)
print("试探常见字体路径")
print("=" * 92)
cands = ["https://www.guoxuedashi.com/img/ICS4.ttf",
         "https://www.guoxuedashi.com/img/ICS4.woff",
         "https://www.guoxuedashi.com/img/ICS4.woff2",
         "https://www.guoxuedashi.com/font/ICS4.ttf",
         "https://www.guoxuedashi.com/img/font/ICS4.ttf",
         "https://m.gxdq.com/img/ICS4.ttf"]
for u in cands:
    try:
        b = get(u, raw=True)
        print(f"  OK  {u}  {len(b)} bytes")
        open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "ICS4.bin"), "wb").write(b)
        break
    except Exception as e:
        print(f"  ERR {u}  {type(e).__name__} {str(e)[:40]}")
