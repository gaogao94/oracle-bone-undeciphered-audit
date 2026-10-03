# -*- coding: utf-8 -*-
"""生成四指标距离排序图（最终判定依据）"""
import io, json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")

rows = [("中", 0.118), ("冊", 0.415), ("芻", 0.434), ("祸", 0.486), ("弗", 0.494),
        ("璞", 0.567), ("告", 0.666), ("隹", 0.667), ("翦", 0.778), ("其", 0.787),
        ("史", 0.814), ("昷", 0.950), ("佑", 0.988), ("叶", 1.017),
        ("豹", 1.200), ("侯", 1.232), ("奠", 1.332)]

F = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 24)
FS = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 19)
W, H = 1000, 90 + len(rows) * 34
sheet = Image.new("RGB", (W, H), "white")
dr = ImageDraw.Draw(sheet)
dr.text((12, 10), "圖6　待考字與各候選字的結構距離（四項指標標準差之和，越小越近）",
        fill="black", font=F)
dr.text((12, 48), "距離", fill=(90, 90, 90), font=FS)
dr.text((300, 48), "字", fill=(90, 90, 90), font=FS)
SCALE = 480
mx = 1.45
for i, (ch, d) in enumerate(rows):
    y = 80 + i * 34
    w = int(SCALE * d / mx)
    col = (200, 25, 25) if ch == "中" else ((40, 90, 200) if ch == "告" else (140, 140, 140))
    dr.rectangle([300, y, 300 + w, y + 24], outline=col, width=2)
    if ch == "中":
        dr.rectangle([300, y, 300 + w, y + 24], fill=(255, 225, 225))
    if ch == "告":
        dr.rectangle([300, y, 300 + w, y + 24], fill=(225, 235, 255))
    dr.text((250, y + 2), f"{d:.3f}", fill=(60, 60, 60), font=FS)
    dr.text((318 + w, y + 1), ch, fill=col, font=FS)
dr.text((12, H - 26), "紅＝「中」（距離 0.118，斷層第一）　藍＝「告」（槽位候選，距離 0.666，可排除）",
        fill=(60, 60, 60), font=FS)
sheet.save(os.path.join(FIG, "figD_distance.png"))
print(f"[写出] figD_distance.png {sheet.width}x{sheet.height}")
