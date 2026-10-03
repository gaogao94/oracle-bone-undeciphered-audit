# -*- coding: utf-8 -*-
"""
高价值目标集：最强位置只容 1 个已知字的未释字（15 个）
这些是最可能闭合的案子：异体 / 误分 / 罕见写法
"""
import io, json, os, sys, collections, zipfile
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
is_anon = lambda l: (mc.get(l, {}).get("transcription") or []) == []

by_label = collections.defaultdict(list)
for n in ZS.namelist():
    if n.lower().endswith(".png"):
        p = n.split("/")
        if len(p) >= 4:
            by_label.setdefault(p[1], []).append(n)

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

cs = json.load(open(os.path.join(RES, "constraint_strength.json"), encoding="utf-8"))
targets = [r for r in cs if r["best_n_rep"] == 1]
print(f"最强位置只容 1 字的未释字：{len(targets)} 个\n")

# 找 label
label_of = {}
for l, v in mc.items():
    c = v.get("codepoint") or ""
    if len(c) == 1:
        label_of.setdefault(c, l)

rows = []
for r in targets:
    g = r["glyph"]
    lab = label_of.get(g)
    if not lab:
        # 可能是内部编号
        lab = g if g in freq else None
    if not lab:
        continue
    cand = r["cands"]
    # 该未释字的全部辞例
    ex = []
    for nm, s in sents:
        if lab in s:
            C = [cp(x) or "◻" for x in s]
            i = s.index(lab)
            ex.append(f"{nm}: " + " ".join("【□】" if k == i else C[k] for k in range(len(C))))
    rows.append({"glyph": g, "label": lab, "freq": freq[lab], "n_occ": r["n_occ"],
                 "cad": cand, "sig": r["best_sig"], "examples": ex[:3],
                 "n_glyphs": len(by_label.get(lab, []))})

rows.sort(key=lambda r: -r["n_occ"])
print(f"{'未釋字':>6}{'次數':>5}{'字形數':>7}{'最強位候選':>10}  最強位框架")
print("-" * 92)
for r in rows:
    print(f"{r['glyph']:>6}{r['freq']:>5}{r['n_glyphs']:>7}{'、'.join(r['cad'])[:8]:>10}  {' '.join(r['sig'])}")

print("\n" + "=" * 92)
print("逐一列出辞例")
print("=" * 92)
for r in rows:
    print(f"\n■ {r['glyph']}  出现 {r['freq']} 次，字形 {r['n_glyphs']} 个")
    print(f"   最强位置候选（全语料唯一可填字）: {r['cad']}")
    print(f"   该位置框架: {' '.join(r['sig'])}")
    for e in r["examples"]:
        print(f"     {e}")

json.dump(rows, open(os.path.join(RES, "high_value_targets.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# 图：这批目标的字形
F = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 20)
FS = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 17)
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


ncol = 3
W = 250 + CELL * ncol
H = CELL * len(rows) + 70
sheet = Image.new("L", (W, H), 255)
dr = ImageDraw.Draw(sheet)
dr.text((10, 8), "圖H  高價值目標：最強位置只容一個已知字的未釋字", fill=0, font=F)
for i, r in enumerate(rows):
    y = 54 + i * CELL
    dr.text((10, y + 20), f"{r['glyph']} ({r['freq']}次)", fill=0, font=FS)
    dr.text((10, y + 48), f"→ {'/'.join(r['cad'])}", fill=0, font=FS)
    for j, p in enumerate(by_label.get(r["label"], [])[:ncol]):
        im = gimg(p)
        if im:
            sheet.paste(im, (250 + j * CELL, y))
    dr.line([(0, y + CELL), (W, y + CELL)], fill=205, width=1)
sheet.save(os.path.join(FIG, "figH_targets.png"))
print(f"\n[写出] figH_targets.png {sheet.width}x{sheet.height}")
print("[写出] result/high_value_targets.json")
