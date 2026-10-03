# -*- coding: utf-8 -*-
"""超清晰对照图：未释字 gx21ndp7yy 全部字形 vs 宋/宗/室，逐个并排、大尺寸"""
import io, json, os, sys, zipfile, collections
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
FIG = os.path.join(HERE, "figures")
ZS = zipfile.ZipFile(os.path.join(OB, "subchar_images.zip"))
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))

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

FONT = "C:/Windows/Fonts/simhei.ttf"
F = ImageFont.truetype(FONT, 30)
FS = ImageFont.truetype(FONT, 22)

CELL = 260


def gimg(path, box=CELL):
    im = Image.open(ZS.open(path)).convert("L")
    a = np.asarray(im, dtype=np.float32)
    if a.mean() < 128:
        a = 255 - a
    a = 255 - a
    b = a > 40
    ys, xs = np.nonzero(b)
    bb = b[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = bb.shape
    pad = 20
    s = (box - 2 * pad) / max(h, w)
    nh, nw = max(1, int(round(h * s))), max(1, int(round(w * s)))
    # 用 LANCZOS 放大后二值化，得到干净的粗线
    im2 = Image.fromarray((bb * 255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
    im2 = im2.point(lambda v: 255 if v > 110 else 0)
    cv = Image.new("L", (box, box), 255)
    cv.paste(Image.fromarray(255 - np.asarray(im2)), ((box - nw) // 2, (box - nh) // 2))
    return cv


TGT = "gx21ndp7yy"
rows = [("未釋字 gx21ndp7yy", TGT)]
for ch in ["宋", "宗", "室", "宀", "木"]:
    lab = label_of_char.get(ch)
    if lab:
        rows.append((f"{ch}", lab))

ncol = max(len(by_label[l]) for _, l in rows)
W = 260 + CELL * ncol
H = CELL * len(rows) + 70
sheet = Image.new("L", (W, H), 255)
dr = ImageDraw.Draw(sheet)
dr.text((10, 8), "圖7  未釋字 gx21ndp7yy（54 次）與「宋」「宗」「室」等字形逐形對照（放大、二值）",
        fill=0, font=F)
for i, (name, lab) in enumerate(rows):
    y = 60 + i * CELL
    dr.text((10, y + CELL // 2 - 16), name, fill=0, font=FS)
    dr.text((10, y + CELL // 2 + 12), f"{len(by_label[lab])}形", fill=0, font=FS)
    for j, p in enumerate(by_label[lab][:ncol]):
        im = gimg(p)
        sheet.paste(im, (260 + j * CELL, y))
    dr.line([(0, y + CELL), (W, y + CELL)], fill=200, width=1)
out = os.path.join(FIG, "fig7b_clean.png")
sheet.save(out)
print(f"[写出] {out}  {sheet.width}x{sheet.height}")
for name, lab in rows:
    print(f"  {name}: {len(by_label[lab])} 形")
