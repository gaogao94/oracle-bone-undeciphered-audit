# -*- coding: utf-8 -*-
"""从 JS/CSS 里挖字体 URL"""
import io, os, re, sys, gzip, urllib.request
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


for u in ["https://www.guoxuedashi.com/img/m.js?20251",
          "https://m.gxdq.com/img/m.js"]:
    try:
        t = get(u)
    except Exception as e:
        print(f"{u} ERR {e}")
        continue
    print("=" * 92)
    print(f"{u}  len={len(t)}")
    print("=" * 92)
    for pat in [r"ICS4", r"font-face", r"[^\"'()\s]{0,60}\.(?:woff2?|ttf|otf|eot)",
                r"@font-face[^}]{0,300}", r"createElement\(['\"]style"]:
        hits = re.findall(pat, t, re.I)
        print(f"  {pat[:26]:28s}: {hits[:6]}")
    # 找所有字符串里的字体名
    print("  字符串中的字体名候选:", set(re.findall(r"[\"']([A-Za-z0-9_]{3,12})[\"']", t)) and
          [x for x in set(re.findall(r"[\"']([A-Za-z0-9_]{3,12})[\"']", t)) if "IC" in x.upper() or "FONT" in x.upper()][:10])

print("\n" + "=" * 92)
print("试探更多字体路径")
print("=" * 92)
paths = []
for base in ["https://www.guoxuedashi.com", "https://m.gxdq.com"]:
    for d in ["/img/", "/font/", "/fonts/", "/css/", "/jgwhj/", "/zi/", "/"]:
        for fn in ["ICS4.ttf", "ICS4.woff", "ICS4.woff2", "ics4.ttf", "ICS4.eot"]:
            paths.append(base + d + fn)
for u in paths:
    try:
        b = get(u, raw=True, t=15)
        if len(b) > 1000:
            print(f"  OK  {u}  {len(b)} bytes")
            open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "ICS4.bin"), "wb").write(b)
            raise SystemExit
    except SystemExit:
        break
    except Exception:
        pass
else:
    print("  未找到")
