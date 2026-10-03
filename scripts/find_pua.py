# -*- coding: utf-8 -*-
"""找国学大师的 PUA 映射表 / 字体（用于解出释文里的私有码位字）"""
import io, os, re, sys, gzip, json, urllib.parse, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Accept-Language": "zh-CN,zh;q=0.9", "Accept-Encoding": "gzip, deflate"}


def get(u, t=40):
    with urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=t) as r:
        b = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            b = gzip.decompress(b)
        return b.decode("utf-8", "replace")


# 1) 页面里引用的字体与脚本
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "gxds2")
f0 = sorted(os.listdir(CACHE))[0]
html = open(os.path.join(CACHE, f0), encoding="utf-8").read()
print("=" * 92)
print("页面引用的字体 / 样式 / 脚本")
print("=" * 92)
for pat in [r'@font-face[^}]{0,400}\}', r'font-family\s*:[^;"\']{0,120}', r'<link[^>]*>',
            r'<script[^>]*src="[^"]*"', r'\.(?:woff2?|ttf|otf|eot)\b']:
    hits = re.findall(pat, html, re.I)
    print(f"\n--- {pat[:40]} ---")
    for h in hits[:10]:
        print("   ", re.sub(r"\s+", " ", h)[:200])

print("\n" + "=" * 92)
print("尝试常见字体路径")
print("=" * 92)
for u in ["https://www.guoxuedashi.com/fonts/",
          "https://www.guoxuedashi.com/jgwhj/fonts/",
          "https://www.guoxuedashi.com/css/",
          "https://www.guoxuedashi.com/images/"]:
    try:
        t = get(u)
        print(f"  {u} len={len(t)}  {re.sub(r'<[^>]+>',' ',t)[:120]!r}")
    except Exception as e:
        print(f"  {u} ERR {type(e).__name__} {str(e)[:40]}")

print("\n" + "=" * 92)
print("搜站内是否有造字/字库说明页")
print("=" * 92)
for q in ["造字", "字库", "PUA", "扩展字", "显示"]:
    try:
        t = get("https://www.guoxuedashi.com/search.php?q=" + urllib.parse.quote(q))
        print(f"  '{q}': len={len(t)}")
    except Exception as e:
        print(f"  '{q}': ERR {str(e)[:40]}")
