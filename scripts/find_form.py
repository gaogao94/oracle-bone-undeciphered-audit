# -*- coding: utf-8 -*-
"""找国学大师（gxdq.com）的检索表单与正确查询格式"""
import io, re, sys, gzip, urllib.parse, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Accept-Language": "zh-CN,zh;q=0.9", "Accept-Encoding": "gzip, deflate"}


def get(u, t=35):
    req = urllib.request.Request(u, headers=H)
    with urllib.request.urlopen(req, timeout=t) as r:
        b = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            b = gzip.decompress(b)
        code = r.headers.get("Content-Type", "")
        m = re.search(r"charset=([\w-]+)", code)
        enc = m.group(1) if m else "utf-8"
        try:
            return b.decode(enc)
        except Exception:
            return b.decode("utf-8", "replace")


for u in ["https://www.guoxuedashi.com/jgwhj/", "https://www.gxdq.com/jgwhj/"]:
    try:
        raw = get(u)
    except Exception as e:
        print(f"{u} ERR {type(e).__name__} {str(e)[:60]}")
        continue
    print("=" * 92)
    print(f"{u}  len={len(raw)}")
    print("=" * 92)
    forms = re.findall(r"<form[^>]*>.*?</form>", raw, re.S)
    for f in forms[:3]:
        print("  FORM:", re.sub(r"\s+", " ", f)[:400])
    for inp in re.findall(r"<input[^>]*>", raw)[:10]:
        print("  INPUT:", inp[:200])
    print()
