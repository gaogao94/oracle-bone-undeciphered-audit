# -*- coding: utf-8 -*-
"""读 xianqin 相关文章，找「王比侯」的完整辞例"""
import io, re, sys, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Accept-Language": "zh-CN,zh;q=0.9"}


def strip(t):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = t.replace("&nbsp;", " ").replace("&ldquo;", "「").replace("&rdquo;", "」")
    return re.sub(r"\s+", " ", t)


URLS = [
    "https://www.xianqin.org/blog/archives/2249.html",
    "https://www.xianqin.org/blog/archives/2075.html",
    "https://www.xianqin.org/blog/archives/1694.html",
    "https://www.xianqin.org/blog/archives/1612.html",
]
for u in URLS:
    try:
        txt = strip(urllib.request.urlopen(
            urllib.request.Request(u, headers=H), timeout=40).read().decode("utf-8", "replace"))
    except Exception as e:
        print(f"{u} ERR {e}")
        continue
    print("=" * 96)
    print(f"{u}   len={len(txt)}")
    print("=" * 96)
    # 抓含「比侯」「侯」「中」的片段
    for kw in ["比侯", "侯", "王比"]:
        for m in re.finditer(re.escape(kw), txt):
            a = max(0, m.start() - 90)
            print(f"  [{kw}] …{txt[a:m.start()+110]}…")
            break
    # 抓释文风格的片段
    frags = re.findall(r"[^ 。]{0,25}(?:卜|貞|贞)[^ 。]{0,60}", txt)
    for f in frags[:6]:
        print("   釋文:", f[:110])
    print()
