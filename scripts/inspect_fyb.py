# -*- coding: utf-8 -*-
"""放大复核 󺆑（fybnj2savm）的两个字形，逐个精看结构"""
import io, json, os, sys, zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
FIG = os.path.join(HERE, "figures")
ZS = zipfile.ZipFile(os.path.join(OB, "subchar_images.zip"))
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))

by_label = {}
for n in ZS.namelist():
    if n.lower().endswith(".png"):
        p = n.split("/")
        if len(p) >= 4:
            by_label.setdefault(p[1], []).append(n)

F = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 26)
FS = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 20)
CELL = 400


def big(path, box=CELL):
    im = Image.open(ZS.open(path)).convert("L")
    a = np.asarray(im, dtype=np.float32)
    if a.mean() < 128:
        a = 255 - a
    a = 255 - a
    b = a > 40
    ys, xs = np.nonzero(b)
    bb = b[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = bb.shape
    pad = 30
    s = (box - 2 * pad) / max(h, w)
    nh, nw = max(1, int(round(h * s))), max(1, int(round(w * s)))
    im2 = Image.fromarray((bb * 255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
    im2 = im2.point(lambda v: 255 if v > 100 else 0)
    cv = Image.new("L", (box, box), 255)
    cv.paste(Image.fromarray(255 - np.asarray(im2)), ((box - nw) // 2, (box - nh) // 2))
    return cv


TGT = "fybnj2savm"
own = by_label[TGT]
sheet = Image.new("L", (CELL * len(own) + 20, CELL + 60), 255)
dr = ImageDraw.Draw(sheet)
dr.text((10, 8), f"圖8  未釋字 fybnj2savm 的兩個字形（400px 放大）", fill=0, font=F)
for i, p in enumerate(own):
    sheet.paste(big(p), (10 + i * CELL, 50))
    dr.text((10 + i * CELL, CELL + 52 - 20), f"形{i+1}", fill=0, font=FS)
out = os.path.join(FIG, "fig8_fyb_forms.png")
sheet.save(out)
print(f"[写出] {out}  {sheet.width}x{sheet.height}")

# 数值特征：逐行墨迹跨度（看顶/中/底的结构）
for i, p in enumerate(own):
    im = Image.open(ZS.open(p)).convert("L")
    a = np.asarray(im, dtype=np.float32)
    if a.mean() < 128:
        a = 255 - a
    a = 255 - a
    b = a > 40
    ys, xs = np.nonzero(b)
    bb = b[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    H, W = bb.shape
    print(f"\n形{i+1}: {W}x{H} 像素")
    for k in range(8):
        seg = bb[k * H // 8:(k + 1) * H // 8]
        if seg.sum() == 0:
            print(f"   行{k+1}: 空")
            continue
        cols = np.nonzero(seg.any(axis=0))[0]
        print(f"   行{k+1}: 墨迹横向范围 {cols.min()}–{cols.max()} / 宽 {W}"
              f"  占比 {(cols.max()-cols.min()+1)/W:.2f}")
