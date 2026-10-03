# -*- coding: utf-8 -*-
"""
定 󳪫（2lep30tiiz，71 次）= 「率」？
关键检验：
  1) OBIMD 是否已有「率」的字形类？若有，出现多少次？
  2) 󳪫 与「率」的辞例是否一致（同片同句）？
  3) 󳪫 与「率」的字形对照
"""
import io, os, sys, json, collections, zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import gxds2

OB = os.path.join(_HERE, "data", "obimd")
RES = os.path.join(_HERE, "result")
FIG = os.path.join(_HERE, "figures")
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
print("检验 1：OBIMD 是否已有「率」")
print("=" * 96)
for ch in ["率", "𧗵", "䢦"]:
    lab = label_of_char.get(ch)
    if lab:
        print(f"  「{ch}」在 OBIMD 字表中：label={lab}，出现 {freq[lab]} 次，字形 {len(by_label[lab])} 个")
    else:
        print(f"  「{ch}」**不在** OBIMD 字表中")

print(f"\n  目标 󳪫：label={TGT}，出现 {freq[TGT]} 次，字形 {len(by_label[TGT])} 个")

print("\n" + "=" * 96)
print("检验 2：󳪫 所在片的《合集》释文")
print("=" * 96)
occ = []
for p in data:
    nm = p.get("RubbingName") or ""
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        seq = sorted([c for c in (g.get("RecordUtilOracleCharVoList") or [])
                      if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
        labs = [c["Label"] for c in seq]
        if TGT in labs:
            occ.append((nm, labs))
print(f"  共 {len(occ)} 处，列出前 12 处并查《合集》")
for nm, labs in occ[:12]:
    num = nm.lstrip("H")
    C = [cp(x) or "□" for x in labs]
    print(f"\n  片 {nm}: {' '.join(C)}")
    if not num.isdigit():
        continue
    try:
        rows, _ = gxds2.query(num, maxpages=1)
    except Exception as e:
        print(f"     抓取失败 {e}")
        continue
    for r in rows[:3]:
        print(f"     《合集》{r['no']}-{r['seq']} [{r['group']}] {r['text'][:96]}")

json.dump([{"piece": nm, "ob": " ".join(cp(x) or "□" for x in labs)} for nm, labs in occ],
          open(os.path.join(RES, "lv_occ.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# 图
F = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 20)
FS = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 16)
CELL = 150


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


lab_lv = label_of_char.get("率")
rows = [("󳪫（未釋）", TGT)] + ([("率", lab_lv)] if lab_lv else [])
NC = 6
W = 230 + CELL * NC
H = CELL * len(rows) + 70
sheet = Image.new("L", (W, H), 255)
dr = ImageDraw.Draw(sheet)
dr.text((10, 8), "圖 L  未釋字 󳪫 與「率」的字形對照", fill=0, font=F)
for i, (nm, lab) in enumerate(rows):
    y = 54 + i * CELL
    dr.text((10, y + CELL // 2), nm, fill=0, font=FS)
    for j, p in enumerate(by_label.get(lab, [])[:NC]):
        im = gimg(p)
        if im:
            sheet.paste(im, (230 + j * CELL, y))
    dr.line([(0, y + CELL), (W, y + CELL)], fill=205, width=1)
sheet.save(os.path.join(FIG, "figL_lv.png"))
print(f"\n[写出] figL_lv.png {sheet.width}x{sheet.height}")
