# -*- coding: utf-8 -*-
"""
系统比较：󳪫 的构形特征「人形 + 椭圆头 + 头内笔画」属于哪个字？
列出 OBIMD 中全部「人形字」的字形，逐一目验对照。
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
freq = collections.Counter()
for p in data:
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        for c in g.get("RecordUtilOracleCharVoList") or []:
            if c.get("Label"):
                freq[c["Label"]] += 1

TGT = "2lep30tiiz"
CANDS = ["天", "大", "夫", "文", "交", "夭", "立", "夾", "央", "亦", "頁", "元",
         "兄", "兒", "先", "光", "堯", "吳", "走", "奔", "乘", "眾", "老", "長",
         "尸", "卩", "人", "儿", "兄", "競", "並", "替", "朁", "僉"]

print("=" * 96)
print("候选字在 OBIMD 中的情况")
print("=" * 96)
rows = [("󳪫 未釋（4 形）", TGT)]
for ch in CANDS:
    lab = label_of_char.get(ch)
    if lab and len(by_label.get(lab, [])) > 0:
        print(f"  「{ch}」label={lab}  {freq[lab]} 次  {len(by_label[lab])} 形")
        if ch not in [r[0] for r in rows]:
            rows.append((f"{ch}（{freq[lab]}次）", lab))
    elif lab:
        print(f"  「{ch}」在字表但无字形图")
    else:
        print(f"  「{ch}」不在字表")

# 出图
F = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 20)
FS = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 16)
CELL = 150
NC = 4


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


W = 250 + CELL * NC
H = CELL * len(rows) + 70
sheet = Image.new("L", (W, H), 255)
dr = ImageDraw.Draw(sheet)
dr.text((10, 8), "圖 O  未釋字 󳪫 與「人形」諸字的字形對照", fill=0, font=F)
for i, (nm, lab) in enumerate(rows):
    y = 54 + i * CELL
    dr.text((10, y + CELL // 2), nm, fill=0, font=FS)
    for j, p in enumerate(by_label.get(lab, [])[:NC]):
        im = gimg(p)
        if im:
            sheet.paste(im, (250 + j * CELL, y))
    dr.line([(0, y + CELL), (W, y + CELL)], fill=205, width=1)
p = os.path.join(FIG, "figO_humanform.png")
sheet.save(p)
print(f"\n[写出] {p}  {sheet.width}x{sheet.height}  共 {len(rows)} 行")
