# -*- coding: utf-8 -*-
"""高频未释字（出现≥10次）的字形、辞例、候选综合分析"""
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
is_anon = lambda l: (mc.get(l, {}).get("transcription") or []) == []
hi = sorted((l for l in freq if is_anon(l) and freq[l] >= 10), key=lambda l: -freq[l])
print(f"高频未释字（≥10 次）：{len(hi)} 个")

FONT = "C:/Windows/Fonts/msyh.ttc"
F = ImageFont.truetype(FONT, 20)
FS = ImageFont.truetype(FONT, 15)
FT = ImageFont.truetype(FONT, 24)


def gimg(path, box=140):
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


# 图：全部高频未释字，每个给 4 个字形
cell = 140
n_per = 4
rows = len(hi)
W = 210 + cell * n_per
sheet = Image.new("L", (W, cell * rows + 60), 255)
dr = ImageDraw.Draw(sheet)
dr.text((8, 6), "圖6  高頻未釋字（出現 ≥10 次）的字形，各取 4 形", fill=0, font=FT)
for i, lab in enumerate(hi):
    y = 46 + i * cell
    dr.text((8, y + 8), f"{freq[lab]}次", fill=0, font=F)
    dr.text((8, y + 34), lab[:13], fill=0, font=FS)
    for j, p in enumerate(by_label[lab][:n_per]):
        im = gimg(p, cell)
        if im:
            sheet.paste(im, (210 + j * cell, y))
out = os.path.join(FIG, "fig6_high_freq_anon.png")
sheet.save(out)
print(f"[写出] {out}  {sheet.width}x{sheet.height}")

# 辞例与邻字
print("\n" + "=" * 90)
for lab in hi:
    occ = [(nm, s) for nm, s in sents if lab in s]
    lc, rc = collections.Counter(), collections.Counter()
    ex = []
    for nm, s in occ:
        i = s.index(lab)
        if i > 0 and cp(s[i - 1]):
            lc[cp(s[i - 1])] += 1
        if i < len(s) - 1 and cp(s[i + 1]):
            rc[cp(s[i + 1])] += 1
        if len(s) >= 4 and len(ex) < 3:
            ex.append(" ".join("【□】" if k == i else (cp(x) or "◻") for k, x in enumerate(s)))
    print(f"\n■ {lab}  出现 {freq[lab]} 次  字形 {len(by_label[lab])} 个")
    print(f"   左邻: {lc.most_common(6)}")
    print(f"   右邻: {rc.most_common(6)}")
    for e in ex:
        print(f"   例: {e}")

json.dump({"high_freq": [{"label": l, "freq": freq[l], "n_glyphs": len(by_label[l])}
                         for l in hi]},
          open(os.path.join(HERE, "result", "high_freq_anon.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
