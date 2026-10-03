# -*- coding: utf-8 -*-
"""核对「宋」等假设：语料是否已有该字、其字形与未释字比对"""
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

sents = []
for p in data:
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        seq = sorted([c for c in (g.get("RecordUtilOracleCharVoList") or [])
                      if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
        if seq:
            sents.append([c["Label"] for c in seq])
freq = collections.Counter()
for s in sents:
    freq.update(s)

print("=== 假设字是否已在语料中 ===")
for ch in ["宋", "宗", "室", "安", "宀", "木", "株", "柰", "索", "崇", "祼"]:
    lab = label_of_char.get(ch)
    if lab:
        print(f"  「{ch}」存在 label={lab}  出现 {freq[lab]} 次  字形 {len(by_label.get(lab,[]))} 个")
    else:
        print(f"  「{ch}」不在 OBIMD 字表中")

print("\n=== 目标未释字 gx21ndp7yy 的辞例 ===")
TGT = "gx21ndp7yy"
for s in sents:
    if TGT in s:
        i = s.index(TGT)
        print("   " + " ".join("【□】" if k == i else (cp(x) or "◻") for k, x in enumerate(s)))

FONT = "C:/Windows/Fonts/msyh.ttc"
F = ImageFont.truetype(FONT, 20)
FS = ImageFont.truetype(FONT, 15)
FT = ImageFont.truetype(FONT, 22)


def gimg(path, box=150):
    try:
        im = Image.open(ZS.open(path)).convert("L")
    except Exception:
        return None
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
    pad = 12
    s = (box - 2 * pad) / max(h, w)
    nh, nw = max(1, int(round(h * s))), max(1, int(round(w * s)))
    im2 = Image.fromarray(((~bb) * 255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
    cv = Image.new("L", (box, box), 255)
    cv.paste(im2, ((box - nw) // 2, (box - nh) // 2))
    return cv


hyps = [c for c in ["宋", "宗", "室", "安"] if label_of_char.get(c)]
cell = 150
sheet = Image.new("L", (cell * 6 + 130, cell * (1 + len(hyps)) + 60), 255)
dr = ImageDraw.Draw(sheet)
dr.text((8, 6), "圖7  未釋字 gx21ndp7yy（54 次，祭名／地名位）與假設字對照", fill=0, font=FT)
dr.text((8, 40 + cell // 2), "未釋", fill=0, font=F)
for j, p in enumerate(by_label[TGT][:6]):
    im = gimg(p, cell)
    if im:
        sheet.paste(im, (130 + j * cell, 40))
for i, hy in enumerate(hyps):
    y = 40 + (i + 1) * cell
    lab = label_of_char[hy]
    dr.text((8, y + cell // 2), hy, fill=0, font=F)
    for j, p in enumerate(by_label[lab][:6]):
        im = gimg(p, cell)
        if im:
            sheet.paste(im, (130 + j * cell, y))
out = os.path.join(FIG, "fig7_vs_song.png")
sheet.save(out)
print(f"\n[写出] {out}")
