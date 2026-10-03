# -*- coding: utf-8 -*-
"""
对照：󷺊 与 彡 在 OBIMD 中的类组分布、字形数、后邻字
以及 󷺊 是否可能是「彡」的晚期异体
"""
import io, os, sys, json, collections, zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
RES = os.path.join(HERE, "result")
FIG = os.path.join(HERE, "figures")
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
cp = lambda l: mc.get(l, {}).get("codepoint") or ""
label_of_char = {}
for lab, v in mc.items():
    c = v.get("codepoint") or ""
    if len(c) == 1:
        label_of_char.setdefault(c, lab)
ZS = zipfile.ZipFile(os.path.join(OB, "subchar_images.zip"))
by_label = collections.defaultdict(list)
for n in ZS.namelist():
    if n.lower().endswith(".png"):
        p = n.split("/")
        if len(p) >= 4:
            by_label.setdefault(p[1], []).append(n)


def group_cat(lab):
    """按 GroupCategory 统计（片级）"""
    c = collections.Counter()
    for p in data:
        gc = p.get("GroupCategory")
        for g in p.get("RecordUtilSentenceGroupVoList") or []:
            for x in g.get("RecordUtilOracleCharVoList") or []:
                if x.get("Label") == lab:
                    c[gc or "(无)"] += 1
    return c


def after_dist(lab):
    c = collections.Counter()
    for p in data:
        for g in p.get("RecordUtilSentenceGroupVoList") or []:
            seq = sorted([x for x in (g.get("RecordUtilOracleCharVoList") or [])
                          if x.get("Label")], key=lambda x: x.get("OrderNumber") or 0)
            C = [cp(x["Label"]) or "◻" for x in seq]
            L = [x["Label"] for x in seq]
            for i, x in enumerate(L):
                if x == lab and i + 1 < len(C):
                    c[C[i + 1]] += 1
    return c


TGT = "ff8rp0nh6u"
SAN = label_of_char.get("彡")
print("=" * 96)
print("对照：󷺊  与  「彡」")
print("=" * 96)
for name, lab in [("󷺊", TGT), ("彡", SAN)]:
    if not lab:
        continue
    n = sum(1 for p in data for g in p.get("RecordUtilSentenceGroupVoList") or []
            for x in g.get("RecordUtilOracleCharVoList") or [] if x.get("Label") == lab)
    print(f"\n【{name}】label={lab}  出现 {n} 次  字形 {len(by_label.get(lab,[]))} 个")
    gc = group_cat(lab)
    print(f"  GroupCategory 分布: {gc.most_common(12)}")
    ad = after_dist(lab)
    print(f"  后邻字: {ad.most_common(12)}")
    print(f"  后邻为「亡」的比例: {ad.get('亡',0)}/{sum(ad.values())} = {ad.get('亡',0)/max(1,sum(ad.values())):.0%}")

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


rows = [("󷺊（未釋）", TGT), ("彡", SAN)]
rows = [(a, b) for a, b in rows if b]
NC = 6
W = 230 + CELL * NC
H = CELL * len(rows) + 70
sheet = Image.new("L", (W, H), 255)
dr = ImageDraw.Draw(sheet)
dr.text((10, 8), "圖K  󷺊 與「彡」的字形對照", fill=0, font=F)
for i, (nm, lab) in enumerate(rows):
    y = 54 + i * CELL
    dr.text((10, y + CELL // 2), nm, fill=0, font=FS)
    for j, p in enumerate(by_label.get(lab, [])[:NC]):
        im = gimg(p)
        if im:
            sheet.paste(im, (230 + j * CELL, y))
    dr.line([(0, y + CELL), (W, y + CELL)], fill=205, width=1)
sheet.save(os.path.join(FIG, "figK_shan.png"))
print(f"\n[写出] figK_shan.png {sheet.width}x{sheet.height}")
