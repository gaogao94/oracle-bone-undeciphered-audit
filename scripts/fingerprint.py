# -*- coding: utf-8 -*-
"""
按"画"检索：把 󺡅 的视觉母题写出来，在全库中按结构筛同构字
母题：竖干 + 横（两侧各一向下弧笔） + 中央框/实体 + 下部叉
方法：对每个已释字，取其字形的"行宽分布"作为结构指纹，找同构者
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


def load_mask(lab, k=0):
    ps = by_label.get(lab, [])
    if k >= len(ps):
        return None
    a = np.asarray(Image.open(ZS.open(ps[k])).convert("L"))
    dark = a < 128
    b = dark if dark.mean() <= 0.5 else ~dark
    ys, xs = np.nonzero(b)
    if len(ys) < 5:
        return None
    bb = b[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return bb


def profile(box, nb=16):
    """纵向切成 nb 段，记录每段的最左/最右/宽度 -> 结构指纹"""
    h, w = box.shape
    cuts = np.linspace(0, h, nb + 1).astype(int)
    out = []
    for i in range(nb):
        seg = box[cuts[i]:cuts[i + 1]]
        if seg.size == 0:
            out.append((0.0, 0.0))
            continue
        cols = np.nonzero(seg.any(axis=0))[0]
        if len(cols) == 0:
            out.append((0.0, 0.0))
            continue
        out.append((cols.min() / w, cols.max() / w))
    return np.array(out)


TGT = "gx21ndp7yy"
tb = load_mask(TGT)
tp = profile(tb)
print(f"󺡅 结构指纹（每段的最左、最右，归一化）:")
h, w = tb.shape
print(f"  高宽比 {h/w:.2f}")
for i, (l, r) in enumerate(tp):
    bar = " " * int(l * 40) + "█" * max(1, int((r - l) * 40))
    print(f"  段{i+1:>2} {l:.2f}-{r:.2f} |{bar}")

# 全库找指纹最近的字
print("\n全库结构指纹比对 …")
res = []
for lab in by_label:
    if (mc.get(lab, {}).get("transcription") or []) == []:
        continue
    ch = cp(lab)
    if len(ch) != 1:
        continue
    best = 1e9
    for k in range(min(6, len(by_label[lab]))):
        b = load_mask(lab, k)
        if b is None:
            continue
        p = profile(b)
        d = float(np.abs(p - tp).sum())
        best = min(best, d)
    if best < 1e9:
        res.append((best, ch, lab))
res.sort()
print(f"\n结构指纹最近的 25 个字：")
for d, ch, lab in res[:25]:
    print(f"  {ch}  距离 {d:.3f}  出现 {freq[lab]} 次")

# 出图
CELL = 240
F = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 22)
FS = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 17)


def render(box, cell=CELL):
    hh, ww = box.shape
    pad = 16
    s = (cell - 2 * pad) / max(hh, ww)
    nh, nw = max(1, int(round(hh * s))), max(1, int(round(ww * s)))
    im2 = Image.fromarray((box * 255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
    im2 = im2.point(lambda v: 255 if v > 100 else 0)
    cv = Image.new("L", (cell, cell), 255)
    cv.paste(Image.fromarray(255 - np.asarray(im2)), ((cell - nw) // 2, (cell - nh) // 2))
    return cv


top = res[:8]
rows = [("󺡅 未釋", TGT)] + [(f"{ch}（{freq[lab]}）", lab) for _, ch, lab in top]
NC = 3
W = 230 + CELL * NC
H = CELL * len(rows) + 70
sheet = Image.new("L", (W, H), 255)
dr = ImageDraw.Draw(sheet)
dr.text((10, 8), "圖 V  結構指紋最接近 󺡅 的八個字", fill=0, font=F)
for i, (nm, lab) in enumerate(rows):
    y = 54 + i * CELL
    dr.text((10, y + CELL // 2), nm, fill=0, font=FS)
    for j in range(NC):
        b = load_mask(lab, j)
        if b is None:
            continue
        sheet.paste(render(b), (230 + j * CELL, y))
    dr.line([(0, y + CELL), (W, y + CELL)], fill=205, width=1)
fp = os.path.join(FIG, "figV_fingerprint.png")
sheet.save(fp)
print(f"\n[写出] {fp}  {sheet.width}x{sheet.height}")
