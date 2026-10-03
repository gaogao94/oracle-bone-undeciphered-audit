# -*- coding: utf-8 -*-
"""解析 zdic 页面的字形图与出处：找到图片 URL 规律与结构"""
import io, re, sys, urllib.parse, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Accept-Language": "zh-CN,zh;q=0.9"}

ch = "寅"
u = f"https://www.zdic.net/hans/{urllib.parse.quote(ch)}"
t = urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=40).read().decode("utf-8", "replace")
print(f"页面长度 {len(t)}")
open(r"D:\coding\gold_hunter\data\_zdic_yin.html", "w", encoding="utf-8").write(t)

# 找所有 img
imgs = re.findall(r'<img[^>]+>', t)
print(f"\n<img> 标签数 {len(imgs)}")
for x in imgs[:25]:
    print("  ", x[:200])

print("\n=== 含 zy / jgw / sw 的路径 ===")
paths = set(re.findall(r'["\'(]([^"\'()\s]+\.(?:gif|png|jpg|jpeg))["\')]', t, re.I))
for p in sorted(paths)[:40]:
    print("  ", p)

print("\n=== 数据接口线索 ===")
for pat in [r'https?://[^"\'\s]*zdic[^"\'\s]*', r'/api/[^"\'\s]+', r'data-[a-z]+="[^"]{0,60}"']:
    hits = sorted(set(re.findall(pat, t)))[:15]
    print(f"  {pat}: {hits}")
