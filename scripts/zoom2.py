# -*- coding: utf-8 -*-
"""放大 17382 等拓片供目验"""
import io, os, sys
import numpy as np
from PIL import Image
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
for name in ["017382", "003209", "002454", "005373"]:
    p = os.path.join(HERE, "data", "rubbings", name + ".png")
    if not os.path.exists(p):
        continue
    im = Image.open(p).convert("L")
    a = np.asarray(im)
    dark = a < 128
    ys, xs = np.nonzero(dark)
    if len(ys) == 0:
        print(f"{name}: 无墨迹")
        continue
    crop = im.crop((max(0, xs.min() - 4), max(0, ys.min() - 4),
                    xs.max() + 5, ys.max() + 5))
    w, h = crop.size
    sc = max(1, int(1600 / max(w, h)))
    big = crop.resize((w * sc, h * sc), Image.LANCZOS)
    fp = os.path.join(FIG, f"rub{name}_zoom.png")
    big.save(fp)
    print(f"{name}: 原 {im.size} → 墨迹 {w}x{h} → 放大 {sc}x → {big.size}  {fp}")
