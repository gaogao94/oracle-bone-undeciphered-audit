# -*- coding: utf-8 -*-
"""解析类组分类论文，看有无公开的类组数据/数据集"""
import io, os, re, sys
from pypdf import PdfReader
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, "data", "papers", "rgc_2026_0503.pdf")
r = PdfReader(P)
print(f"页数 {len(r.pages)}")
txt = []
for i, pg in enumerate(r.pages):
    try:
        t = pg.extract_text() or ""
    except Exception as e:
        t = f"[err {e}]"
    txt.append(f"\n===== p{i+1} =====\n{t}")
full = "".join(txt)
open(os.path.join(HERE, "data", "papers", "rgc_2026_0503.txt"), "w", encoding="utf-8").write(full)
print(f"提取字符数 {len(full)}")
print(full[:4000])
