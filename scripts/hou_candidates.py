# -*- coding: utf-8 -*-
"""
关键检验：「侯X」人名位下的候选字结构比对
候補：虎、屯、告、璞、中
"""
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


def boxstat(path):
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
    H, W = bb.shape
    rowsum = bb.sum(axis=1)
    wide = np.nonzero(rowsum >= 0.6 * W)[0]
    if len(wide) == 0:
        return None
    return np.array([W / H, wide.min() / H, wide.max() / H,
                     (wide.max() - wide.min() + 1) / H])


TGT = "fybnj2savm"
tv = np.mean([boxstat(p) for p in by_label[TGT] if boxstat(p) is not None], axis=0)
print(f"待考字: 宽高比={tv[0]:.3f} 上缘={tv[1]:.3f} 下缘={tv[2]:.3f} 高占比={tv[3]:.3f}\n")

CAND = ["中", "虎", "屯", "告", "璞", "犬", "侯"]
rows = []
for ch in CAND:
    lab = label_of_char.get(ch)
    if not lab or lab not in by_label:
        print(f"  「{ch}」不在字形庫")
        continue
    sts = [boxstat(p) for p in by_label[lab][:20]]
    sts = [s for s in sts if s is not None]
    if not sts:
        continue
    v = np.mean(sts, axis=0)
    d = float(np.abs(v - tv).sum())
    rows.append((d, ch, v, len(sts), freq[lab]))
rows.sort()
print(f"{'字':<6}{'距離':>7}{'宽高比':>9}{'上缘':>8}{'下缘':>8}{'高占比':>8}{'形数':>6}{'语料':>7}")
for d, ch, v, ns, f in rows:
    print(f"{ch:<6}{d:>7.3f}{v[0]:>9.3f}{v[1]:>8.3f}{v[2]:>8.3f}{v[3]:>8.3f}{ns:>6}{f:>7}")

# 图：待考字 vs 前四名
F = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 22)
FS = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 18)
CELL = 170


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
    pad = 14
    s = (box - 2 * pad) / max(h, w)
    nh, nw = max(1, int(round(h * s))), max(1, int(round(w * s)))
    im2 = Image.fromarray((bb * 255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
    im2 = im2.point(lambda v: 255 if v > 100 else 0)
    cv = Image.new("L", (box, box), 255)
    cv.paste(Image.fromarray(255 - np.asarray(im2)), ((box - nw) // 2, (box - nh) // 2))
    return cv


shown = ["中"] + [r[1] for r in rows if r[1] != "中"][:4]
sheetrows = [("未釋字", TGT)] + [(f"{c}（{freq[label_of_char[c]]}次）", label_of_char[c])
                               for c in shown if label_of_char.get(c)]
ncol = 6
W = 250 + CELL * ncol
H = CELL * len(sheetrows) + 70
sheet = Image.new("L", (W, H), 255)
dr = ImageDraw.Draw(sheet)
dr.text((10, 8), "圖E　「侯X」人名位下的候選字字形對照", fill=0, font=F)
for i, (name, lab) in enumerate(sheetrows):
    y = 54 + i * CELL
    dr.text((10, y + CELL // 2 - 10), name, fill=0, font=FS)
    for j, p in enumerate(by_label[lab][:ncol]):
        sheet.paste(gimg(p), (250 + j * CELL, y))
    dr.line([(0, y + CELL), (W, y + CELL)], fill=210, width=1)
sheet.save(os.path.join(FIG, "figE_hou_candidates.png"))
print(f"\n[写出] figE_hou_candidates.png {sheet.width}x{sheet.height}")
