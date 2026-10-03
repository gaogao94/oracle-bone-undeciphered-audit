# -*- coding: utf-8 -*-
"""
扩大候选池：把「手形/持物」类字纳入，并对 󵱙 做全上下文覆盖 + 结构距离双重检验
"""
import io, json, os, sys, collections, zipfile
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

sents = []
for p in data:
    nm = p.get("RubbingName")
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        seq = sorted([c for c in (g.get("RecordUtilOracleCharVoList") or [])
                      if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
        if seq:
            sents.append((nm, [c["Label"] for c in seq]))
freq = collections.Counter()
for _, s in sents:
    freq.update(s)

TGT = "urzeocieq8"


def boxstat(path):
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
    H, W = bb.shape
    rowsum = bb.sum(axis=1)
    wide = np.nonzero(rowsum >= 0.6 * W)[0]
    if len(wide) == 0:
        return None
    return np.array([W / H, wide.min() / H, wide.max() / H,
                     (wide.max() - wide.min() + 1) / H])


tv = np.mean([boxstat(p) for p in by_label[TGT] if boxstat(p) is not None], axis=0)
print(f"目标 󵱙: 宽高比={tv[0]:.3f} 上缘={tv[1]:.3f} 下缘={tv[2]:.3f} 高占比={tv[3]:.3f}\n")

# 「X入」框架的产出者 + 手形类字
POOL = set()
for nm, s in sents:
    if len(s) == 2 and cp(s[1]) == "入":
        POOL.add(s[0])
for ch in ["又", "尹", "及", "取", "秉", "用", "爭", "手", "丑", "付", "受", "史", "事",
           "吏", "父", "攴", "支", "彗", "帚", "冊", "目", "峀", "以", "入"]:
    lab = label_of_char.get(ch)
    if lab:
        POOL.add(lab)

rows = []
for lab in POOL:
    if lab not in by_label:
        continue
    sts = [boxstat(p) for p in by_label[lab][:12]]
    sts = [s for s in sts if s is not None]
    if not sts:
        continue
    v = np.mean(sts, axis=0)
    d = float(np.abs(v - tv).sum())
    # 是否产出过「□入」
    has_ru = any(len(s) == 2 and s[0] == lab and cp(s[1]) == "入" for _, s in sents)
    rows.append((d, cp(lab) or lab, freq[lab], len(sts), has_ru))

rows.sort()
print(f"{'字':<6}{'結構距離':>9}{'語料次數':>9}{'字形數':>7}{'曾產出□入':>10}")
for d, ch, f, ns, hr in rows:
    print(f"{ch:<6}{d:>9.3f}{f:>9}{ns:>7}{'  是' if hr else '  否':>10}")

# 图：目标 + 结构最近的 5 个
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
    if len(ys) < 5:
        return None
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


top5 = [r for r in rows if r[1] != (cp(TGT) or TGT)][:5]
sheetrows = [("未釋字 󵱙", TGT)] + [(f"{r[1]}（{r[2]}次）", label_of_char[r[1]]) for r in top5
                                   if r[1] in label_of_char]
ncol = min(8, max(len(by_label[l]) for _, l in sheetrows))
W = 250 + CELL * ncol
H = CELL * len(sheetrows) + 66
sheet = Image.new("L", (W, H), 255)
dr = ImageDraw.Draw(sheet)
dr.text((10, 8), "圖G  未釋字 󵱙 與結構最近的五個已釋字", fill=0, font=F)
for i, (name, lab) in enumerate(sheetrows):
    y = 52 + i * CELL
    dr.text((10, y + CELL // 2), name, fill=0, font=FS)
    for j, p in enumerate(by_label.get(lab, [])[:ncol]):
        im = gimg(p)
        if im:
            sheet.paste(im, (250 + j * CELL, y))
    dr.line([(0, y + CELL), (W, y + CELL)], fill=205, width=1)
sheet.save(os.path.join(FIG, "figG_pool.png"))
print(f"\n[写出] figG_pool.png {sheet.width}x{sheet.height}")
