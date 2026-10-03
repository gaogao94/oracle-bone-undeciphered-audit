# -*- coding: utf-8 -*-
"""
检验：󳪫 = 「天」？
「天」的甲骨文构形：大象人形，突出头部（或作一横/圆点于头上）
检验：
  1) OBIMD 是否已有「天」
  2) 󳪫 的辞例与「天」的辞例是否相容
  3) 字形对照
"""
import io, os, sys, json, collections, zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
RES = os.path.join(HERE, "result")
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
freq = collections.Counter()
for p in data:
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        for c in g.get("RecordUtilOracleCharVoList") or []:
            if c.get("Label"):
                freq[c["Label"]] += 1

TGT = "2lep30tiiz"
print("=" * 96)
print("检验：候选字是否在 OBIMD 中")
print("=" * 96)
for ch in ["天", "大", "夫", "文", "交", "夭", "立", "夾", "央", "亦"]:
    lab = label_of_char.get(ch)
    if lab:
        print(f"  「{ch}」在 OBIMD：label={lab}，{freq[lab]} 次，{len(by_label[lab])} 形")
    else:
        print(f"  「{ch}」不在 OBIMD 字表中")

print(f"\n  目标 󳪫：{freq[TGT]} 次，{len(by_label[TGT])} 形")

# 天 的辞例
print("\n" + "=" * 96)
print("「天」在 OBIMD 中的辞例")
print("=" * 96)
lab_tian = label_of_char.get("天")
if lab_tian:
    n = 0
    for p in data:
        nm = p.get("RubbingName") or ""
        for g in p.get("RecordUtilSentenceGroupVoList") or []:
            seq = sorted([c for c in (g.get("RecordUtilOracleCharVoList") or [])
                          if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
            labs = [c["Label"] for c in seq]
            if lab_tian in labs and n < 30:
                i = labs.index(lab_tian)
                print(f"  {nm}: " + " ".join("【天】" if k == i else (cp(x) or "□")
                                             for k, x in enumerate(labs)))
                n += 1

# 图：󳪫 vs 天/大/夫
F = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 20)
FS = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 16)
CELL = 155


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


rows = [("󳪫 未釋（4 形）", TGT)]
for ch in ["天", "大", "夫", "文"]:
    l = label_of_char.get(ch)
    if l:
        rows.append((f"{ch}（{freq[l]}次）", l))
NC = 5
W = 250 + CELL * NC
H = CELL * len(rows) + 70
sheet = Image.new("L", (W, H), 255)
dr = ImageDraw.Draw(sheet)
dr.text((10, 8), "圖 N  未釋字 󳪫 與「天／大／夫／文」的字形對照", fill=0, font=F)
for i, (nm, lab) in enumerate(rows):
    y = 54 + i * CELL
    dr.text((10, y + CELL // 2), nm, fill=0, font=FS)
    for j, p in enumerate(by_label.get(lab, [])[:NC]):
        im = gimg(p)
        if im:
            sheet.paste(im, (250 + j * CELL, y))
    dr.line([(0, y + CELL), (W, y + CELL)], fill=205, width=1)
p = os.path.join(FIG, "figN_tian.png")
sheet.save(p)
print(f"\n[写出] {p} {sheet.width}x{sheet.height}")
