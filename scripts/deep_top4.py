# -*- coding: utf-8 -*-
"""深入检验最强候选 󵱙（4 上下文，4 个候选）"""
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

TGT = None
for l in freq:
    if (mc.get(l, {}).get("transcription") or []) == [] and freq[l] == 4:
        pass
# 直接按 strict_v3 结果里的 label 找
res = json.load(open(os.path.join(HERE, "result", "strict_v3.json"), encoding="utf-8"))
top = res[0]
TGT = top["label"]
print(f"目标: {top['glyph']}  label={TGT}  freq={freq[TGT]}  ctx={top['n_ctx']}")
print(f"候选: {[(c['char'], c['k_freq']) for c in top['cands']]}\n")

print("=" * 92)
print("该字的全部辞例")
print("=" * 92)
for nm, s in sents:
    if TGT in s:
        i = s.index(TGT)
        print(f"  {nm}: " + " ".join("【□】" if k == i else (cp(x) or "◻") for k, x in enumerate(s)))

print("\n" + "=" * 92)
print("各候选字的辞例（看哪个与目标上下文相容）")
print("=" * 92)
for c in top["cands"]:
    lab = c["label"]
    print(f"\n【{c['char']}】出现 {freq[lab]} 次，字形 {len(by_label.get(lab,[]))} 个")
    n = 0
    for nm, s in sents:
        if lab in s and n < 10:
            i = s.index(lab)
            print(f"   {nm}: " + " ".join("【%s】" % c["char"] if k == i else (cp(x) or "◻")
                                          for k, x in enumerate(s)))
            n += 1

# 字形对照图
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


rows = [("未釋字", TGT)] + [(c["char"], c["label"]) for c in top["cands"]]
ncol = min(8, max(len(by_label.get(l, [])) for _, l in rows))
W = 220 + CELL * ncol
H = CELL * len(rows) + 66
sheet = Image.new("L", (W, H), 255)
dr = ImageDraw.Draw(sheet)
dr.text((10, 8), f"圖F  未釋字（4 次）與四個候選字的字形對照", fill=0, font=F)
for i, (name, lab) in enumerate(rows):
    y = 52 + i * CELL
    dr.text((10, y + CELL // 2), f"{name}（{freq[lab]}次）", fill=0, font=FS)
    for j, p in enumerate(by_label.get(lab, [])[:ncol]):
        im = gimg(p)
        if im:
            sheet.paste(im, (220 + j * CELL, y))
    dr.line([(0, y + CELL), (W, y + CELL)], fill=205, width=1)
sheet.save(os.path.join(FIG, "figF_top4.png"))
print(f"\n[写出] figF_top4.png {sheet.width}x{sheet.height}")
