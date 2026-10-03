# -*- coding: utf-8 -*-
"""放大《合集》5250 拓片的文字区，供目验 󺡅"""
import io, os, sys
import numpy as np
from PIL import Image
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "figures")

for name in ["005250", "005305"]:
    p = os.path.join(HERE, "data", "rubbings", name + ".png")
    if not os.path.exists(p):
        continue
    im = Image.open(p).convert("L")
    a = np.asarray(im)
    print(f"{name}: {im.size}  均值 {a.mean():.0f}")
    # 找墨迹（黑）区域
    dark = a < 128
    ys, xs = np.nonzero(dark)
    if len(ys) == 0:
        print("  无墨迹")
        continue
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    print(f"  墨迹外框 x[{x0},{x1}] y[{y0},{y1}]")
    # 裁到墨迹并放大 3 倍
    crop = im.crop((x0 - 5, y0 - 5, x1 + 5, y1 + 5))
    w, h = crop.size
    big = crop.resize((w * 3, h * 3), Image.LANCZOS)
    fp = os.path.join(OUT, f"rub_{name}_zoom.png")
    big.save(fp)
    print(f"  [写出] {fp}  {big.size}")
