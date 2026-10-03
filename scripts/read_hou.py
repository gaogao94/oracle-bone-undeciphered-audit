# -*- coding: utf-8 -*-
"""取「侯虎」「侯屯」相关文章，提取所有「侯X」人名用例"""
import io, re, sys, urllib.parse, urllib.request, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Accept-Language": "zh-CN,zh;q=0.9"}


def strip(t):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = t.replace("&nbsp;", " ").replace("&ldquo;", "「").replace("&rdquo;", "」")
    return re.sub(r"\s+", " ", t)


def get(u, t=40):
    return urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=t
                                 ).read().decode("utf-8", "replace")


def find_links(q):
    raw = get("https://www.xianqin.org/blog/?s=" + urllib.parse.quote(q))
    return re.findall(r'<h2[^>]*entry-title[^>]*>\s*<a[^>]*href="([^"]+)"', raw)


seen = set()
for q in ["侯虎", "侯屯", "侯璞", "侯告", "比侯", "王比"]:
    for u in find_links(q)[:2]:
        if u in seen:
            continue
        seen.add(u)
        try:
            txt = strip(get(u))
        except Exception as e:
            print(f"{u} ERR {e}")
            continue
        print("=" * 96)
        print(f"{u}")
        print("=" * 96)
        # 抓所有「侯X」片段
        for m in re.finditer(r"侯[\u4e00-\u9fff]", txt):
            a = max(0, m.start() - 80)
            print(f"    …{txt[a:m.start()+90]}…")
        # 抓「比」的用例
        for m in list(re.finditer(r"比[\u4e00-\u9fff]", txt))[:6]:
            a = max(0, m.start() - 70)
            print(f"    [比] …{txt[a:m.start()+80]}…")
        print()
        time.sleep(0.4)
