# -*- coding: utf-8 -*-
"""放大对照 󺡅 vs 朱/未/桑/余（骨架相同的字）"""
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
CANDS = ["朱", "未", "桑", "余", "木", "末", "本", "來", "乘", "黍"]
rows = [("󺡅 未釋", TGT)]
for ch in CANDS:
    l = label_of_char.get(ch)
    if l and by_label.get(l):
        rows.append((f"{ch}（{freq[l]}）", l))

CELL = 260
F = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 22)
FS = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 18)


def gimg(path, box=CELL):
    a = np.asarray(Image.open(ZS.open(path)).convert("L"))
    dark = a < 128
    b = dark if dark.mean() <= 0.5 else ~dark
    ys, xs = np.nonzero(b)
    if len(ys) < 5:
        return None
    bb = b[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = bb.shape
    pad = 18
    s = (box - 2 * pad) / max(h, w)
    nh, nw = max(1, int(round(h * s))), max(1, int(round(w * s)))
    im2 = Image.fromarray((bb * 255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
    im2 = im2.point(lambda v: 255 if v > 100 else 0)
    cv = Image.new("L", (box, box), 255)
    cv.paste(Image.fromarray(255 - np.asarray(im2)), ((box - nw) // 2, (box - nh) // 2))
    return cv


NC = 4
W = 220 + CELL * NC
H = CELL * len(rows) + 70
sheet = Image.new("L", (W, H), 255)
dr = ImageDraw.Draw(sheet)
dr.text((10, 8), "圖 U  󺡅 與骨架相同的諸字（放大）", fill=0, font=F)
for i, (nm, lab) in enumerate(rows):
    y = 54 + i * CELL
    dr.text((10, y + CELL // 2), nm, fill=0, font=FS)
    for j, p in enumerate(by_label.get(lab, [])[:NC]):
        im = gimg(p)
        if im:
            sheet.paste(im, (220 + j * CELL, y))
    dr.line([(0, y + CELL), (W, y + CELL)], fill=205, width=1)
fp = os.path.join(FIG, "figU_skeleton.png")
sheet.save(fp)
print(f"[写出] {fp}  {sheet.width}x{sheet.height}  {len(rows)} 行")

# 候选字的辞例（看语法位）
for ch in ["朱", "未", "桑"]:
    l = label_of_char.get(ch)
    if not l:
        continue
    print(f"\n【{ch}】{freq[l]} 次")
    n = 0
    for p in data:
        nm = p.get("RubbingName") or ""
        for g in p.get("RecordUtilSentenceGroupVoList") or []:
            seq = sorted([c for c in (g.get("RecordUtilOracleCharVoList") or [])
                          if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
            labs = [c["Label"] for c in seq]
            if l in labs and n < 12:
                i = labs.index(l)
                print(f"   {nm}: " + " ".join(f"【{ch}】" if k == i else (cp(x) or "□")
                                              for k, x in enumerate(labs)))
                n += 1
