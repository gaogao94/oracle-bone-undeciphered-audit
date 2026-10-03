# -*- coding: utf-8 -*-
"""定案对照：未释字 fybnj2savm 与「中」「史」「尹」「仲」的逐形精确比对"""
import io, json, os, sys, zipfile, collections
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
FIG = os.path.join(HERE, "figures")
ZS = zipfile.ZipFile(os.path.join(OB, "subchar_images.zip"))
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
cp = lambda l: mc.get(l, {}).get("codepoint") or ""

by_label = collections.defaultdict(list)
for n in ZS.namelist():
    if n.lower().endswith(".png"):
        p = n.split("/")
        if len(p) >= 4:
            by_label[p[1]].append(n)
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

F = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 24)
FS = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 18)
CELL = 200


def gimg(path, box=CELL):
    im = Image.open(ZS.open(path)).convert("L")
    a = np.asarray(im, dtype=np.float32)
    if a.mean() < 128:
        a = 255 - a
    a = 255 - a
    b = a > 40
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


TGT = "fybnj2savm"
rows = [("未釋字 fybnj2savm", TGT)]
for ch in ["中", "史", "尹", "仲", "吏", "事", "屯", "冊"]:
    lab = label_of_char.get(ch)
    if lab:
        rows.append((f"{ch}（{freq[lab]}次）", lab))

ncol = max(len(by_label[l]) for _, l in rows)
ncol = min(ncol, 8)
W = 240 + CELL * ncol
H = CELL * len(rows) + 70
sheet = Image.new("L", (W, H), 255)
dr = ImageDraw.Draw(sheet)
dr.text((10, 8), "圖9  未釋字 fybnj2savm 與「中」「史」「尹」等字的逐形精確對照", fill=0, font=F)
for i, (name, lab) in enumerate(rows):
    y = 58 + i * CELL
    dr.text((10, y + CELL // 2 - 10), name, fill=0, font=FS)
    for j, p in enumerate(by_label[lab][:ncol]):
        im = gimg(p)
        if im:
            sheet.paste(im, (240 + j * CELL, y))
    dr.line([(0, y + CELL), (W, y + CELL)], fill=210, width=1)
out = os.path.join(FIG, "fig9_fyb_vs_all.png")
sheet.save(out)
print(f"[写出] {out}  {sheet.width}x{sheet.height}")

# 数值：框的位置与大小（相对字形高度/宽度）
def boxstat(path):
    im = Image.open(ZS.open(path)).convert("L")
    a = np.asarray(im, dtype=np.float32)
    if a.mean() < 128:
        a = 255 - a
    a = 255 - a
    b = a > 40
    ys, xs = np.nonzero(b)
    bb = b[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    H, W = bb.shape
    rowsum = bb.sum(axis=1)
    # 最宽的一段 = 框所在
    wide = np.nonzero(rowsum >= 0.6 * W)[0]
    if len(wide) == 0:
        return None
    return {"W": W, "H": H, "宽段起": wide.min() / H, "宽段止": wide.max() / H,
            "宽段高占比": (wide.max() - wide.min() + 1) / H, "宽高比": W / H}


print("\n框的位置与大小（相对高度）:")
print(f"{'字':<20}{'宽高比':>8}{'宽段起':>8}{'宽段止':>8}{'宽段高占比':>10}")
for name, lab in rows:
    sts = [boxstat(p) for p in by_label[lab][:6]]
    sts = [s for s in sts if s]
    if not sts:
        continue
    ar = np.mean([s["宽高比"] for s in sts])
    a0 = np.mean([s["宽段起"] for s in sts])
    a1 = np.mean([s["宽段止"] for s in sts])
    hh = np.mean([s["宽段高占比"] for s in sts])
    print(f"{name:<20}{ar:>8.2f}{a0:>8.2f}{a1:>8.2f}{hh:>10.2f}")
