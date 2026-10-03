# -*- coding: utf-8 -*-
"""
正面比对：󺡅 vs 图 V 第 6 行那个字（U+Fxxxx，15 次）
并在《合集》里检索「王X叀（惠）吉」位置上出现过的可读字
"""
import io, os, re, sys, json, collections, zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import gxds2

OB = os.path.join(_HERE, "data", "obimd")
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
label_of_char, label_of_glyph = {}, {}
for lab, v in mc.items():
    c = v.get("codepoint") or ""
    if len(c) == 1:
        label_of_char.setdefault(c, lab)
    if c:
        label_of_glyph[c] = lab
freq = collections.Counter()
for p in data:
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        for c in g.get("RecordUtilOracleCharVoList") or []:
            if c.get("Label"):
                freq[c["Label"]] += 1

# 找图 V 第 6 行那个字：指纹最近列表里的第二个未释? 不，它是已释的
# 从 fingerprint 结果：'򣹻' 距离 1.453 出现 15 次
CAND = None
for lab, v in mc.items():
    c = v.get("codepoint") or ""
    if c and freq.get(lab, 0) == 15 and len(by_label.get(lab, [])) >= 2:
        # 需要判断是否为 򣹻
        if ord(c) > 0xFFFF or 0xE000 <= ord(c) <= 0xF8FF:
            CAND = lab
            print(f"候选字 label={lab} glyph={c} freq={freq[lab]} 形{len(by_label[lab])}个")
            break

TGT = "gx21ndp7yy"
CELL = 280
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


rows = [("󺡅 未釋", TGT)]
for ch in ["舞", "奭", "亦"]:
    l = label_of_char.get(ch)
    if l and by_label.get(l):
        rows.append((f"{ch}（{freq[l]}）", l))
if CAND:
    rows.insert(1, (f"圖V第6行（{freq[CAND]}）", CAND))

NC = 3
W = 250 + CELL * NC
H = CELL * len(rows) + 70
sheet = Image.new("L", (W, H), 255)
dr = ImageDraw.Draw(sheet)
dr.text((10, 8), "圖 W  󺡅 與舞／奭／亦 放大正面對比", fill=0, font=F)
for i, (nm, lab) in enumerate(rows):
    y = 54 + i * CELL
    dr.text((10, y + CELL // 2), nm, fill=0, font=FS)
    for j in range(NC):
        ps = by_label.get(lab, [])
        if j >= len(ps):
            continue
        im = gimg(ps[j])
        if im:
            sheet.paste(im, (250 + j * CELL, y))
    dr.line([(0, y + CELL), (W, y + CELL)], fill=205, width=1)
fp = os.path.join(FIG, "figW_dance.png")
sheet.save(fp)
print(f"[写出] {fp}  {sheet.width}x{sheet.height}")

# 《合集》检索「王?惠吉」位置的历史读法
print("\n" + "=" * 96)
print("《合集》中「王X叀（惠）吉」位置出现过的可读字（历史读法）")
print("=" * 96)
def sg(t):
    return re.sub(r"（[^）]*）|\([^)]*\)|〔[^〕]*〕|【[^】]*】", "", t)

for q in ["惠吉", "叀", "吉"]:
    try:
        rows2, total = gxds2.query(q, maxpages=3)
    except Exception:
        continue
    hits = []
    for r in rows2:
        s = sg(r["text"])
        for m in re.finditer(r"王(.)(?:叀|惠)吉", s):
            ch = m.group(1)
            if 0x4E00 <= ord(ch) <= 0x9FFF:
                hits.append((ch, r["group"], r["text"]))
    if hits:
        print(f"  「{q}」检索中，X 位为可读汉字的实例:")
        for ch, gp, tx in hits[:15]:
            print(f"     X=「{ch}」 [{gp}] {tx[:84]}")
    break
else:
    print("  未找到 X 位为可读汉字的实例（与早前结论一致：该位置《合集》从未用已释字写过）")
