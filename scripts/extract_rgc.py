# -*- coding: utf-8 -*-
"""从论文中找数据集来源、获取方式、组别清单"""
import io, os, re, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
t = open(os.path.join(HERE, "data", "papers", "rgc_2026_0503.txt"), encoding="utf-8").read()

print("=" * 92)
print("搜索：数据集来源 / 获取方式 / 链接")
print("=" * 92)
for pat in [r"[^。]{0,120}(?:數據集|数据集|构建|來源|来源|爬取|采集|收集)[^。]{0,160}。",
            r"[^。]{0,80}(?:https?://|www\.|github|zenodo|figshare|kaggle)[^。]{0,120}",
            r"[^。]{0,100}(?:殷契文淵|殷契文渊|甲骨文合集|合集|拓片|圖像庫|图像库)[^。]{0,140}。"]:
    print(f"\n--- 模式 {pat[:30]} ---")
    hits = re.findall(pat, t)
    seen = set()
    for h in hits[:12]:
        h = h.strip()
        if h in seen or len(h) < 15:
            continue
        seen.add(h)
        print("  ", h[:220])

print("\n" + "=" * 92)
print("搜索：24 个组别的名称")
print("=" * 92)
for pat in [r"[^。]{0,60}24\s*个?组别[^。]{0,200}。",
            r"[^。]{0,60}(?:師組|师组|賓組|宾组|出組|出组|何組|何组|黃組|黄组|歷組|历组|無名組|无名组)[^。]{0,140}。"]:
    hits = re.findall(pat, t)
    for h in hits[:10]:
        print("  ", h.strip()[:240])

print("\n" + "=" * 92)
print("搜索：组别-时期-贞人 三级标注体系细节")
print("=" * 92)
for m in re.finditer(r"[^。]{0,80}三级标注[^。]{0,220}。", t):
    print("  ", m.group(0).strip()[:280])

print("\n" + "=" * 92)
print("全文中的表格与数字（找组别分布）")
print("=" * 92)
for m in re.finditer(r"[^。]{0,60}(?:表\s*\d|Tab\.?\s*\d|样本数|數量|数量)[^。]{0,160}", t):
    s = m.group(0).strip()
    if any(c.isdigit() for c in s) and len(s) > 20:
        print("  ", s[:200])
