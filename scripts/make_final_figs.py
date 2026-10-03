# -*- coding: utf-8 -*-
"""
论文最终图：未释字 fybnj2savm 的完整字形链与判定证据
"""
import io, json, os, sys, zipfile, collections
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
FIG = os.path.join(HERE, "figures")
os.makedirs(FIG, exist_ok=True)
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
label_of_char = {}
for lab, v in mc.items():
    c = v.get("codepoint") or ""
    if len(c) == 1:
        label_of_char.setdefault(c, lab)

F = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 26)
FS = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 20)
FX = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 17)


def gimg(path, box=200):
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
    pad = 18
    s = (box - 2 * pad) / max(h, w)
    nh, nw = max(1, int(round(h * s))), max(1, int(round(w * s)))
    im2 = Image.fromarray((bb * 255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
    im2 = im2.point(lambda v: 255 if v > 100 else 0)
    cv = Image.new("L", (box, box), 255)
    cv.paste(Image.fromarray(255 - np.asarray(im2)), ((box - nw) // 2, (box - nh) // 2))
    return cv


TGT = "fybnj2savm"
CELL = 200

# ============ 图 A：未释字两形 vs 中/史 全部形 ============
rows = [("未釋字（本論文討論對象）", TGT), ("中", label_of_char.get("中")),
        ("史", label_of_char.get("史"))]
rows = [(n, l) for n, l in rows if l]
ncol = max(min(len(by_label[l]), 8) for _, l in rows)
W = 300 + CELL * ncol
H = CELL * len(rows) + 80
sheet = Image.new("L", (W, H), 255)
dr = ImageDraw.Draw(sheet)
dr.text((10, 8), "圖A　未釋字與「中」「史」的字形對照（同尺度、同二值化）", fill=0, font=F)
for i, (name, lab) in enumerate(rows):
    y = 62 + i * CELL
    dr.text((10, y + CELL // 2 - 10), name, fill=0, font=FS)
    for j, p in enumerate(by_label[lab][:ncol]):
        im = gimg(p)
        if im:
            sheet.paste(im, (300 + j * CELL, y))
    dr.line([(0, y + CELL), (W, y + CELL)], fill=205, width=1)
sheet.save(os.path.join(FIG, "figA_main_compare.png"))
print(f"[写出] figA_main_compare.png {sheet.width}x{sheet.height}")

# ============ 图 B：结构指标条形对比 ============


def boxstat(path):
    im = Image.open(ZS.open(path)).convert("L")
    a = np.asarray(im, dtype=np.float32)
    if a.mean() < 128:
        a = 255 - a
    a = 255 - a
    b = a > 40
    ys, xs = np.nonzero(b)
    bb = b[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    Hh, Ww = bb.shape
    rowsum = bb.sum(axis=1)
    wide = np.nonzero(rowsum >= 0.6 * Ww)[0]
    if len(wide) == 0:
        return None
    return (Ww / Hh, wide.min() / Hh, wide.max() / Hh, (wide.max() - wide.min() + 1) / Hh)


sets = [("未釋字", TGT, (70, 70, 70)), ("中", label_of_char.get("中"), (200, 30, 30)),
        ("史", label_of_char.get("史"), (30, 60, 200)), ("冊", label_of_char.get("冊"), (150, 150, 30))]
sets = [s for s in sets if s[1]]
stats = {}
for name, lab, col in sets:
    sts = [boxstat(p) for p in by_label[lab][:8]]
    sts = [s for s in sts if s]
    if sts:
        stats[name] = (np.mean([s[0] for s in sts]), np.mean([s[1] for s in sts]),
                       np.mean([s[2] for s in sts]), np.mean([s[3] for s in sts]), col)

BW, BH = 900, 460
sheet = Image.new("RGB", (BW, BH), "white")
dr = ImageDraw.Draw(sheet)
dr.text((12, 8), "圖B　結構指標對比：框體位置與比例（紅=未釋字推定的讀法「中」）", fill="black", font=F)
metrics = [("寬高比", 0), ("框體上緣", 1), ("框體下緣", 2), ("框體高度佔比", 3)]
mx = [1.2, 0.8, 0.8, 0.7]
x0 = 150
bw = 130
for mi, (mname, idx) in enumerate(metrics):
    base = 60 + mi * 100
    dr.text((12, base + 20), mname, fill="black", font=FS)
    for si, (name, lab, col) in enumerate(sets):
        if name not in stats:
            continue
        v = stats[name][idx]
        w = int(bw * min(v / mx[mi], 1.0))
        dr.rectangle([x0 + si * 20, base + 10, x0 + si * 20 + w, base + 46],
                     outline=stats[name][4], width=3)
        dr.text((x0 + si * 20 + w + 8, base + 20), f"{name} {v:.2f}", fill=stats[name][4], font=FS)
sheet.save(os.path.join(FIG, "figB_metrics.png"))
print(f"[写出] figB_metrics.png {sheet.width}x{sheet.height}")

# ============ 图 C：字形链（甲骨→金文→篆→隶）文本链 ============
CH = {
    "甲骨文": "甲398、甲547、乙7741 合811（賓組）、前1.6.1 合1488（賓組）、前4.27.5 合5581（𠂤組）",
    "金文": "中鐃 集成370（商代晚期）、中爵 集成7716（商代晚期）、中盉 集成9316（商代晚期）",
    "說文小篆": "說文‧丨部（小篆）、說文古文、說文籀文",
    "隸書": "武威簡、孫臏132（西漢）等 22 例",
    "楷書": "中",
    "異體字": "仲、𠁦、𠁧、𠁩、𠔈、𠔗、𠖌",
}
sheet = Image.new("RGB", (1100, 60 + 62 * len(CH)), "white")
dr = ImageDraw.Draw(sheet)
dr.text((12, 10), "圖C　「中」的字形演變鏈（據《漢典》字源字形庫所載出處）", fill="black", font=F)
for i, (k, v) in enumerate(CH.items()):
    y = 56 + i * 62
    dr.text((14, y), k, fill="black", font=FS)
    dr.text((190, y), v, fill=(60, 60, 60), font=FX)
    dr.line([(12, y + 40), (1088, y + 40)], fill=(220, 220, 220), width=1)
sheet.save(os.path.join(FIG, "figC_chain.png"))
print(f"[写出] figC_chain.png {sheet.width}x{sheet.height}")

json.dump({k: list(v[:5]) for k, v in stats.items()},
          open(os.path.join(HERE, "result", "final_metrics.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n指标:", {k: [round(x, 3) for x in v[:4]] for k, v in stats.items()})
