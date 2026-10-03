# -*- coding: utf-8 -*-
"""
󺡅 的偏旁分解尝试
构形假说：上部（枝杈/止形）＋ 中部（目）＋ 下部（人/腿）
检验该组合是否等于「望」「監」「臨」「見」等字
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

TGT = "gx21ndp7yy"

# 「望」的辞例
print("=" * 100)
print("「望」的辞例（看是否与本字同语法位）")
print("=" * 100)
lab_wang = label_of_char.get("望")
n = 0
for p in data:
    nm = p.get("RubbingName") or ""
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        seq = sorted([c for c in (g.get("RecordUtilOracleCharVoList") or [])
                      if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
        labs = [c["Label"] for c in seq]
        if lab_wang in labs and n < 20:
            i = labs.index(lab_wang)
            print(f"  {nm}: " + " ".join("【望】" if k == i else (cp(x) or "□")
                                         for k, x in enumerate(labs)))
            n += 1

# 望 的前邻/后邻
print("\n" + "=" * 100)
print("「望」的前后邻字")
print("=" * 100)
bf, af = collections.Counter(), collections.Counter()
for p in data:
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        seq = sorted([c for c in (g.get("RecordUtilOracleCharVoList") or [])
                      if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
        labs = [c["Label"] for c in seq]
        C = [cp(x) or "□" for x in labs]
        for i, x in enumerate(labs):
            if x == lab_wang:
                bf[C[i - 1] if i > 0 else "(句首)"] += 1
                af[C[i + 1] if i + 1 < len(C) else "(句末)"] += 1
print(f"  前邻: {bf.most_common(12)}")
print(f"  后邻: {af.most_common(12)}")

# 出大字图：󺡅 4 形 放大 + 望
F = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 22)
FS = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 17)
CELL = 230


def gimg(path, box=CELL):
    a = np.asarray(Image.open(ZS.open(path)).convert("L"))
    dark = a < 128
    b = dark if dark.mean() <= 0.5 else ~dark
    ys, xs = np.nonzero(b)
    if len(ys) < 5:
        return None
    bb = b[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = bb.shape
    pad = 16
    s = (box - 2 * pad) / max(h, w)
    nh, nw = max(1, int(round(h * s))), max(1, int(round(w * s)))
    im2 = Image.fromarray((bb * 255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
    im2 = im2.point(lambda v: 255 if v > 100 else 0)
    cv = Image.new("L", (box, box), 255)
    cv.paste(Image.fromarray(255 - np.asarray(im2)), ((box - nw) // 2, (box - nh) // 2))
    return cv


rows = [("󺡅 未釋", TGT), ("望", lab_wang), ("見", label_of_char.get("見")),
        ("省", label_of_char.get("省")), ("目", label_of_char.get("目"))]
rows = [(a, b) for a, b in rows if b]
NC = 4
W = 240 + CELL * NC
H = CELL * len(rows) + 70
sheet = Image.new("L", (W, H), 255)
dr = ImageDraw.Draw(sheet)
dr.text((10, 8), "圖 Q  󺡅 與「望／見／省／目」的放大對照", fill=0, font=F)
for i, (nm, lab) in enumerate(rows):
    y = 54 + i * CELL
    dr.text((10, y + CELL // 2), nm, fill=0, font=FS)
    for j, p in enumerate(by_label.get(lab, [])[:NC]):
        im = gimg(p)
        if im:
            sheet.paste(im, (240 + j * CELL, y))
    dr.line([(0, y + CELL), (W, y + CELL)], fill=205, width=1)
p = os.path.join(FIG, "figQ_zoom.png")
sheet.save(p)
print(f"\n[写出] {p}  {sheet.width}x{sheet.height}")
