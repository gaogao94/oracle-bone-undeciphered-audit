# -*- coding: utf-8 -*-
"""为 8 个「相容」候选生成字形对照图，逐一目验"""
import io, json, os, sys, zipfile, collections
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
RES = os.path.join(HERE, "result")
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

PAIRS = [("󱊾", "禾"), ("󴓧", "殺"), ("󻊓", "雀"), ("󾢼", "其"),
         ("󼨃", "新"), ("󺃟", "琡"), ("󰾀", "今"), ("󵭟", "轡")]

F = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 22)
FS = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 17)
CELL = 175


def gimg(path, box=CELL):
    a = np.asarray(Image.open(ZS.open(path)).convert("L"))
    dark = a < 128
    b = dark if dark.mean() <= 0.5 else ~dark
    ys, xs = np.nonzero(b)
    if len(ys) < 5:
        return None
    bb = b[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = bb.shape
    pad = 13
    s = (box - 2 * pad) / max(h, w)
    nh, nw = max(1, int(round(h * s))), max(1, int(round(w * s)))
    im2 = Image.fromarray((bb * 255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
    im2 = im2.point(lambda v: 255 if v > 100 else 0)
    cv = Image.new("L", (box, box), 255)
    cv.paste(Image.fromarray(255 - np.asarray(im2)), ((box - nw) // 2, (box - nh) // 2))
    return cv


NC = 6
rows = []
for xg, kc in PAIRS:
    xl = label_of_char.get(xg)
    kl = label_of_char.get(kc)
    if not xl or not kl:
        continue
    rows.append((xg, xl, kc, kl))

W = 230 + CELL * NC
H = CELL * len(rows) * 2 + 80
sheet = Image.new("L", (W, H), 255)
dr = ImageDraw.Draw(sheet)
dr.text((10, 8), "圖I  八個「相容」候選的字形對照（上：未釋字　下：候選字）", fill=0, font=F)
y = 54
for xg, xl, kc, kl in rows:
    dr.text((10, y + CELL // 2), f"未釋 {xg}", fill=0, font=FS)
    dr.text((10, y + CELL + CELL // 2), f"候選 {kc}", fill=0, font=FS)
    for j, p in enumerate(by_label[xl][:NC]):
        im = gimg(p)
        if im:
            sheet.paste(im, (230 + j * CELL, y))
    for j, p in enumerate(by_label[kl][:NC]):
        im = gimg(p)
        if im:
            sheet.paste(im, (230 + j * CELL, y + CELL))
    y += CELL * 2
    dr.line([(0, y - CELL), (W, y - CELL)], fill=200, width=1)
sheet.save(os.path.join(FIG, "figI_verdicts.png"))
print(f"[写出] figI_verdicts.png {sheet.width}x{sheet.height}")
for xg, xl, kc, kl in rows:
    print(f"  {xg}({len(by_label[xl])}形, {freq[xl]}次)  vs  {kc}({len(by_label[kl])}形, {freq[kl]}次)")
