# -*- coding: utf-8 -*-
"""找分页 URL 格式并测试第二个条件"""
import io, re, sys, gzip, urllib.parse, urllib.request
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


u1 = "https://www.guoxuedashi.com/jgwhj/?bhfl=1&bh=&jgwfl=" + urllib.parse.quote("典賓")
h1 = get(u1)
print("=" * 90)
print("分页链接原文（含 page= 的片段）")
print("=" * 90)
for m in re.finditer(r".{0,120}page=\d+.{0,80}", h1):
    print("  ", re.sub(r"\s+", " ", m.group(0))[:220])
    break
for m in list(re.finditer(r"<a[^>]*>[^<]*</a>", h1))[:200]:
    s = m.group(0)
    if "page" in s or "下一页" in s or "末页" in s:
        print("  LINK:", re.sub(r"\s+", " ", s)[:220])

print("\n" + "=" * 90)
print("测试第二页")
print("=" * 90)
for u2 in [u1 + "&page=2",
           "https://www.guoxuedashi.com/jgwhj/page=2?bhfl=1&bh=&jgwfl=" + urllib.parse.quote("典賓"),
           "https://www.guoxuedashi.com/jgwhj/?page=2&bhfl=1&bh=&jgwfl=" + urllib.parse.quote("典賓")]:
    try:
        h2 = get(u2)
        tds = re.findall(r"<td[^>]*>(.*?)</td>", h2, re.S)
        cells = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", x)).strip() for x in tds]
        print(f"  {u2[-60:]:62s} len={len(h2)}  td数={len(tds)}  前几个={cells[5:11]}")
    except Exception as e:
        print(f"  {u2[-60:]:62s} ERR {str(e)[:50]}")
