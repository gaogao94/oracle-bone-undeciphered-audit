# -*- coding: utf-8 -*-
"""探测上古音数据可得性：能否为任意汉字取得声符/韵部/声纽"""
import io, json, re, ssl, sys, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Accept-Language": "zh-CN,zh;q=0.9"}


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers=H)
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.read().decode("utf-8", "replace")


print("=== 1. ytenx.org（韵典）字形页 ===")
for path in ["/", "/kyonh/", "/tcy/", "/dzih/"]:
    try:
        t = fetch("https://ytenx.org" + path)
        print(f"  {path:10s} len={len(t):>7}  title={re.search(r'<title>(.*?)</title>', t).group(1) if '<title>' in t else '?'}")
    except Exception as e:
        print(f"  {path:10s} ERR {type(e).__name__} {str(e)[:50]}")

print("\n=== 2. 东方语言学（eastling）===")
for u in ["https://www.eastling.org/", "http://www.eastling.org/"]:
    try:
        t = fetch(u)
        print(f"  {u} len={len(t)}")
    except Exception as e:
        print(f"  {u} ERR {type(e).__name__} {str(e)[:60]}")

print("\n=== 3. zdic 汉字页能否提取上古音 ===")
for ch in ["屯", "春", "徹", "阱", "歲", "伐"]:
    try:
        t = fetch(f"https://www.zdic.net/hans/{urllib.parse.quote(ch)}")
        # 找音韵相关区块
        hits = re.findall(r"(上古音|韻部|韵部|聲紐|声纽|王力|郑张|鄭張|白沙|广韵|廣韻)[^<]{0,60}", t)
        print(f"  {ch}: len={len(t)} 命中={len(hits)} 例={hits[:4]}")
    except Exception as e:
        print(f"  {ch}: ERR {type(e).__name__} {str(e)[:50]}")

print("\n=== 4. 小学堂 字形演变 ===")
for u in ["https://xiaoxue.iis.sinica.edu.tw/yanbian?char=%E5%B1%AF",
          "https://xiaoxue.iis.sinica.edu.tw/yanbian/List?char=%E5%B1%AF"]:
    try:
        t = fetch(u)
        print(f"  {u[-40:]:42s} len={len(t):>7}")
    except Exception as e:
        print(f"  {u[-40:]:42s} ERR {type(e).__name__} {str(e)[:50]}")

print("\n=== 5. hanziyuan（字源，含甲骨/金文/小篆字形）===")
for u in ["https://hanziyuan.net/", "https://hanziyuan.net/api/"]:
    try:
        t = fetch(u)
        print(f"  {u:34s} len={len(t):>7}")
    except Exception as e:
        print(f"  {u:34s} ERR {type(e).__name__} {str(e)[:50]}")
