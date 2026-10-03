# -*- coding: utf-8 -*-
"""调试：定位 zdic 页面里字形演变正文的确切位置"""
import io, re, sys, urllib.parse, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
H = {"User-Agent": "Mozilla/5.0", "Accept-Language": "zh-CN,zh;q=0.9"}


def strip(t):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t)


t = strip(urllib.request.urlopen(urllib.request.Request(
    "https://www.zdic.net/hans/%E4%B8%AD", headers=H), timeout=35
).read().decode("utf-8", "replace"))
print(f"总长 {len(t)}")
i = t.find("字源演变")
print(f"'字源演变' 位置 {i}")
seg = t[i:i + 1400]
print("\n片段原文：")
print(repr(seg[:1400]))
print("\n--- 逐词定位 ---")
for w in ["甲骨文", "金文", "说文", "隶书", "各书体字形实例", "更多"]:
    pos = [m.start() for m in re.finditer(re.escape(w), t)]
    print(f"  '{w}' 位置: {pos[:8]}")
