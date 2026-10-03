# -*- coding: utf-8 -*-
"""诊断：类组检索的表格结构 + 分页机制"""
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


url = "https://www.guoxuedashi.com/jgwhj/?bhfl=1&bh=&jgwfl=" + urllib.parse.quote("典賓")
html = get(url)
print(f"len={len(html)}")
# 找所有 table
tables = re.findall(r"<table[^>]*>.*?</table>", html, re.S | re.I)
print(f"table 数 {len(tables)}")
for i, t in enumerate(tables):
    trs = re.findall(r"<tr[^>]*>.*?</tr>", t, re.S | re.I)
    if len(trs) < 3:
        continue
    print(f"\n--- table {i}: {len(trs)} 行 ---")
    for tr in trs[:4]:
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S | re.I)
        cells = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", x)).strip() for x in tds]
        print(f"    {len(cells)} 列: {cells[:6]}")

print("\n" + "=" * 90)
print("分页线索")
print("=" * 90)
for pat in [r"page\s*=\s*\d+", r"下一页", r"共\s*\d+\s*[页条]", r"href=\"[^\"]*page[^\"]*\"",
            r"总[共计]\s*\d+"]:
    hits = re.findall(pat, html, re.I)
    print(f"  {pat}: {hits[:8]}")

# 找「字词 屯」的分页
html2 = get("https://www.guoxuedashi.com/jgwhj/?bhfl=1&bh=" + urllib.parse.quote("屯"))
print("\n" + "=" * 90)
print("「屯」检索页的分页线索")
print("=" * 90)
for pat in [r"page\s*=\s*\d+", r"下一页[^<]{0,40}", r"共\s*\d+\s*[页条]", r"href=\"([^\"]*page[^\"]*)\""]:
    hits = re.findall(pat, html2, re.I)
    print(f"  {pat}: {hits[:8]}")
# 找页面里像总数的数字
m = re.findall(r"(?:共|总计|检索到)[^<>]{0,20}(\d+)[^<>]{0,10}", html2)
print("  总数线索:", m[:6])
