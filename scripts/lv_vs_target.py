# -*- coding: utf-8 -*-
"""
判定 󳪫（71次,4形）与 OBIMD 既有「率」（25次,1形）的关系
看字形 + 看「率」的辞例，判断：
  (a) 󳪫 是另一个字（非率）
  (b) 󳪫 与「率」为同字异体，OBIMD 分类过细
"""
import io, os, sys, json, collections, zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
FIG = os.path.join(HERE, "figures")
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
cp = lambda l: mc.get(l, {}).get("codepoint") or ""
ZS = zipfile.ZipFile(os.path.join(OB, "subchar_images.zip"))
by_label = collections.defaultdict(list)
for n in ZS.namelist():
    if n.lower().endswith(".png"):
        p = n.split("/")
        if len(p) >= 4:
            by_label.setdefault(p[1], []).append(n)
label_of_char = {}
for lab, v in mc.items():
    c = v.get("codepoint") or ""
    if len(c) == 1:
        label_of_char.setdefault(c, lab)

TGT = "2lep30tiiz"
LV = label_of_char.get("率")

print("=" * 96)
print("「率」在 OBIMD 中的辞例")
print("=" * 96)
n = 0
for p in data:
    nm = p.get("RubbingName") or ""
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        seq = sorted([c for c in (g.get("RecordUtilOracleCharVoList") or [])
                      if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
        labs = [c["Label"] for c in seq]
        if LV in labs and n < 25:
            i = labs.index(LV)
            print(f"  {nm}: " + " ".join("【率】" if k == i else (cp(x) or "□")
                                         for k, x in enumerate(labs)))
            n += 1

# 两者是否同片共现
print("\n" + "=" * 96)
print("󳪫 与「率」是否同片共现")
print("=" * 96)
co = 0
for p in data:
    nm = p.get("RubbingName") or ""
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        labs = [c["Label"] for c in (g.get("RecordUtilOracleCharVoList") or []) if c.get("Label")]
        if TGT in labs and LV in labs:
            co += 1
            print(f"  {nm}: " + " ".join(cp(x) or "□" for x in labs))
print(f"  共现 {co} 处")

# 字形图
F = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 20)
FS = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 16)
CELL = 160


def gimg(path, box=CELL):
    a = np.asarray(Image.open(ZS.open(path)).convert("L"))
    dark = a < 128
    b = dark if dark.mean() <= 0.5 else ~dark
    ys, xs = np.nonzero(b)
    if len(ys) < 5:
        return None
    bb = b[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = bb.shape
    pad = 12
    s = (box - 2 * pad) / max(h, w)
    nh, nw = max(1, int(round(h * s))), max(1, int(round(w * s)))
    im2 = Image.fromarray((bb * 255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
    im2 = im2.point(lambda v: 255 if v > 100 else 0)
    cv = Image.new("L", (box, box), 255)
    cv.paste(Image.fromarray(255 - np.asarray(im2)), ((box - nw) // 2, (box - nh) // 2))
    return cv


rows = [("󳪫 未釋字 4 形", TGT)] + ([("率 OBIMD 字表 1 形", LV)] if LV else [])
NC = 5
W = 250 + CELL * NC
H = CELL * len(rows) + 70
sheet = Image.new("L", (W, H), 255)
dr = ImageDraw.Draw(sheet)
dr.text((10, 8), "圖 M  未釋字 󳪫（4 形）與 OBIMD 既有「率」（1 形）", fill=0, font=F)
for i, (nm, lab) in enumerate(rows):
    y = 54 + i * CELL
    dr.text((10, y + CELL // 2), nm, fill=0, font=FS)
    for j, p in enumerate(by_label.get(lab, [])[:NC]):
        im = gimg(p)
        if im:
            sheet.paste(im, (250 + j * CELL, y))
    dr.line([(0, y + CELL), (W, y + CELL)], fill=205, width=1)
p = os.path.join(FIG, "figM_lv_vs_target.png")
sheet.save(p)
print(f"\n[写出] {p} {sheet.width}x{sheet.height}")
