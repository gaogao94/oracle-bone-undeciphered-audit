# -*- coding: utf-8 -*-
"""
生成论文所需的全部插图（高分辨率 PNG）
因为甲骨文/金文/篆书无法用文本正常显示，正文一律用图片呈现
"""
import io, json, os, sys, zipfile, collections
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
FIG = os.path.join(HERE, "figures")
os.makedirs(FIG, exist_ok=True)

mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
ZS = zipfile.ZipFile(os.path.join(OB, "subchar_images.zip"))
ZF = zipfile.ZipFile(os.path.join(OB, "facsimile.zip"))
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

FONT = "C:/Windows/Fonts/msyh.ttc"
F = ImageFont.truetype(FONT, 22)
FS = ImageFont.truetype(FONT, 17)
FT = ImageFont.truetype(FONT, 26)


def glyph_img(path, box=170, invert_out=True):
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
    pad = 14
    s = (box - 2 * pad) / max(h, w)
    nh, nw = max(1, int(round(h * s))), max(1, int(round(w * s)))
    im2 = Image.fromarray(((~bb) * 255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
    cv = Image.new("L", (box, box), 255)
    cv.paste(im2, ((box - nw) // 2, (box - nh) // 2))
    return cv


def save_fig(name, sheet):
    p = os.path.join(FIG, name)
    sheet.save(p)
    print(f"[写出] {p}  {sheet.width}x{sheet.height}")


# ============ 图 1：未释字的字形群（按出现次数排序）============
print("图 1 …")
anon = [l for l in by_label if (mc.get(l, {}).get("transcription") or []) == []]
freq = collections.Counter()
for p in data:
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        for c in g.get("RecordUtilOracleCharVoList") or []:
            if c.get("Label"):
                freq[c["Label"]] += 1
anon.sort(key=lambda l: -freq[l])
show = anon[:12]
cell = 170
sheet = Image.new("L", (cell * 6, cell * 2 + 90), 255)
dr = ImageDraw.Draw(sheet)
dr.text((8, 6), "圖1  未釋字形群（依語料出現次數排序，各取首個字形）", fill=0, font=FT)
for i, lab in enumerate(show):
    r, c = divmod(i, 6)
    im = glyph_img(by_label[lab][0], cell) if by_label[lab] else None
    if im:
        sheet.paste(im, (c * cell, 40 + r * cell))
    dr.text((c * cell + 6, 40 + r * cell + cell - 18),
            f"{freq[lab]}次", fill=0, font=FS)
save_fig("fig1_anon_glyphs.png", sheet)

# ============ 图 2：mepmffeebh 的 37 个出现（全部字形）============
print("图 2 …")
lab = "mepmffeebh"
imgs = by_label[lab]
cols = min(10, len(imgs))
rows = (len(imgs) + cols - 1) // cols
cell = 150
W = cell * max(cols, 3)
sheet = Image.new("L", (W, cell * rows + 74), 255)
dr = ImageDraw.Draw(sheet)
dr.text((8, 6), "圖2  未釋字 mepmffeebh 的全部字形", fill=0, font=FT)
for i, p in enumerate(imgs):
    r, c = divmod(i, cols)
    im = glyph_img(p, cell)
    if im:
        sheet.paste(im, (c * cell, 50 + r * cell))
save_fig("fig2_mepm_all_forms.png", sheet)

# ============ 图 3：mepmffeebh vs 寅 / 矢 / 大 並排 ============
print("圖 3 …")
cell = 150
hyps = ["寅", "矢", "大"]
sheet = Image.new("L", (cell * 6 + 130, cell * (1 + len(hyps)) + 70), 255)
dr = ImageDraw.Draw(sheet)
dr.text((8, 6), "圖3  未釋字 mepmffeebh 與三個候選字的字形並排對照", fill=0, font=FT)
for j, p in enumerate(imgs[:6]):
    im = glyph_img(p, cell)
    if im:
        sheet.paste(im, (130 + j * cell, 40))
dr.text((8, 40 + cell // 2), "mepm", fill=0, font=F)
for i, hy in enumerate(hyps):
    y = 40 + (i + 1) * cell
    rl = label_of_char.get(hy)
    dr.text((8, y + cell // 2 - 8), hy, fill=0, font=F)
    for j, p in enumerate((by_label.get(rl, []) if rl else [])[:6]):
        im = glyph_img(p, cell)
        if im:
            sheet.paste(im, (130 + j * cell, y))
save_fig("fig3_mepm_vs_candidates.png", sheet)

# ============ 图 4：󺆑 vs 中 / 史 ============
print("圖 4 …")
lab = "fybnj2savm"
own = by_label[lab]
cell = 160
sheet = Image.new("L", (cell * 6 + 130, cell * 3 + 70), 255)
dr = ImageDraw.Draw(sheet)
dr.text((8, 6), "圖4  未釋字（左）與「中」「史」字形對照", fill=0, font=FT)
dr.text((8, 40 + cell // 2 - 8), "未釋", fill=0, font=F)
for j, p in enumerate(own[:6]):
    im = glyph_img(p, cell)
    if im:
        sheet.paste(im, (130 + j * cell, 40))
for i, hy in enumerate(["中", "史"]):
    y = 40 + (i + 1) * cell
    rl = label_of_char.get(hy)
    dr.text((8, y + cell // 2 - 8), hy, fill=0, font=F)
    for j, p in enumerate((by_label.get(rl, []) if rl else [])[:6]):
        im = glyph_img(p, cell)
        if im:
            sheet.paste(im, (130 + j * cell, y))
save_fig("fig4_fyb_vs_zhong_shi.png", sheet)

# ============ 圖 5：原片摹本局部（mepmffeebh 的辭例）============
print("圖 5 …")
TH = 190
zc = {}


def fac(path):
    if path not in zc:
        zc[path] = Image.open(ZF.open(path)).convert("RGB")
        if len(zc) > 30:
            zc.pop(next(iter(zc)))
    return zc[path]


rows = []
for p in data:
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        chars = sorted([c for c in (g.get("RecordUtilOracleCharVoList") or [])
                        if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
        for c in chars:
            if c["Label"] == "mepmffeebh":
                rows.append({"piece": p.get("RubbingName"), "fac": p.get("Facsimile"),
                             "pos": c.get("Position"), "toks": [cp(x["Label"]) for x in chars],
                             "idx": chars.index(c)})
rows = rows[:6]
if rows:
    panels = []
    for r in rows:
        try:
            im = fac(r["fac"]).copy()
        except Exception:
            continue
        x, y, w, h = [int(v) for v in r["pos"].split(",")]
        pad = max(16, int(0.8 * max(w, h)))
        box = (max(0, x - pad), max(0, y - pad),
               min(im.width, x + w + pad), min(im.height, y + h + pad))
        crop = im.crop(box)
        sc = TH / crop.height
        crop = crop.resize((max(1, int(crop.width * sc)), TH), Image.LANCZOS)
        panels.append((r, crop))
    W = sum(p[1].width + 14 for p in panels) + 10
    sheet = Image.new("RGB", (max(W, 900), TH + 130), "white")
    dr = ImageDraw.Draw(sheet)
    dr.text((8, 6), "圖5  含 mepmffeebh 的原片摹本局部（紅框為本字）", fill="black", font=FT)
    x0 = 8
    for r, crop in panels:
        # 在原圖座標系裡畫紅框：重算縮放後的偏移
        x, y, w, h = [int(v) for v in r["pos"].split(",")]
        pad = max(16, int(0.8 * max(w, h)))
        bx, by = max(0, x - pad), max(0, y - pad)
        sc = TH / (min(fac(r["fac"]).height, y + h + pad) - by)
        rx, ry = (x - bx) * sc, (y - by) * sc
        dr.rectangle([x0 + rx, 40 + ry, x0 + rx + w * sc, 40 + ry + h * sc],
                     outline="red", width=2)
        sheet.paste(crop, (x0, 40))
        dr.text((x0, 40 + TH + 4), r["piece"], fill="black", font=FS)
        x0 += crop.width + 14
    save_fig("fig5_plates.png", sheet)

print("\n全部插圖完成 →", FIG)
