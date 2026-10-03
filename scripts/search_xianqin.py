# -*- coding: utf-8 -*-
"""用 xianqin.org 站内检索找「比侯」「中」相关辞例"""
import io, re, sys, urllib.parse, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Accept-Language": "zh-CN,zh;q=0.9"}


def strip(t):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t)


def get(u, t=40):
    return urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=t
                                 ).read().decode("utf-8", "replace")


for q in ["比侯", "侯中", "中丁", "王比"]:
    u = "https://www.xianqin.org/blog/?s=" + urllib.parse.quote(q)
    try:
        raw = get(u)
        txt = strip(raw)
        # 结果条数与标题
        titles = re.findall(r'<h2[^>]*class="[^"]*entry-title[^"]*"[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                            raw, re.S)
        print("=" * 88)
        print(f"檢索「{q}」 → 頁面 len={len(raw)}，結果 {len(titles)} 條")
        for href, ttl in titles[:8]:
            print(f"   - {strip(ttl)[:70]}  {href[:90]}")
        if not titles:
            m = re.search(r"(沒有找到|未找到|nothing found|No results)", txt, re.I)
            print("   無結果" if m else "   （未識別到結果塊）")
    except Exception as e:
        print(f"檢索「{q}」 ERR {type(e).__name__} {str(e)[:60]}")
