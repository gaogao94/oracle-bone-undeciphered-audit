# -*- coding: utf-8 -*-
"""生成高分辨率候选 vs 目标字 的字形对照大图，供视觉判定"""
import io, json, os, sys, zipfile, collections
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
OB = os.path.join(D, "obimd")
OUT = os.path.join(HERE, "result", "verdict")
os.makedirs(OUT, exist_ok=True)

mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
Z = zipfile.ZipFile(os.path.join(OB, "subchar_images.zip"))
by_label = collections.defaultdict(list)
for n in Z.namelist():
    if n.lower().endswith(".png"):
        p = n.split("/")
        if len(p) >= 4:
            by_label[p[1]].append(n)

label_of_char = {}
for lab, v in mc.items():
    c = v.get("codepoint") or ""
    if len(c) == 1:
        label_of_char.setdefault(c, lab)

N = 48


def load(path, box=200):
    im = Image.open(Z.open(path)).convert("L")
    a = np.asarray(im, dtype=np.float32)
    if a.mean() < 128:
        a = 255 - a
    a = 255 - a
    a[a < 40] = 0
    b = (a > 40).astype(np.float32)
    ys, xs = np.nonzero(b)
    if len(ys) < 5:
        return None
    bb = b[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = bb.shape
    pad = 14
    s = (box - 2 * pad) / max(h, w)
    nh, nw = max(1, int(round(h * s))), max(1, int(round(w * s)))
    im2 = Image.fromarray((bb * 255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
    cv = Image.new("L", (box, box), 255)
    cv.paste(Image.fromarray(255 - np.asarray(im2)), ((box - nw) // 2, (box - nh) // 2))
    return cv


try:
    F = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 22)
    FS = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 18)
except Exception:
    F = FS = ImageFont.load_default()

# 三个重点候选
CAND = [("fybnj2savm", "史"), ("ptd0rmmnrv", "大"), ("mepmffeebh", "寅")]

for lab, hy in CAND:
    own = by_label.get(lab, [])
    rl = label_of_char.get(hy)
    refs = by_label.get(rl, [])[:6] if rl else []
    if not own:
        print(f"{lab}: 无图")
        continue
    cols = 1 + len(refs)
    cell = 200
    head = 44
    sheet = Image.new("L", (cols * cell, 2 * cell + head + 34), 255)
    dr = ImageDraw.Draw(sheet)
    dr.text((8, 8), f"UNKNOWN {mc.get(lab,{}).get('codepoint') or lab}   "
                    f"({len(own)} images)  →  hypothesis: {hy}   ({len(by_label.get(rl,[]))} images)",
            fill=0, font=F)
    # 第一行：未释字全部字形
    for i, p in enumerate(own[:cols]):
        im = load(p)
        if im:
            sheet.paste(im, (i * cell, head))
    if len(own) < cols:
        for i in range(len(own), cols):
            sheet.paste(Image.new("L", (cell, cell), 245), (i * cell, head))
    # 第二行：假设字的前 N 个字形
    for i, p in enumerate(refs):
        im = load(p)
        if im:
            sheet.paste(im, ((1 + i) * cell, head + cell))
    dr.text((8, head + 2 * cell + 6), "row1 = unknown forms     row2 = forms of the hypothesized character",
            fill=0, font=FS)
    out = os.path.join(OUT, f"verdict_{lab}.png")
    sheet.save(out)
    print(f"[写出] {out}")

# 另外做一张：三个候选并排的"未知字形"总览
sheet = Image.new("L", (3 * 240, 200 + 40), 255)
dr = ImageDraw.Draw(sheet)
for i, (lab, hy) in enumerate(CAND):
    own = by_label.get(lab, [])
    if own:
        im = load(own[0], 200)
        if im:
            sheet.paste(im, (i * 240 + 20, 30))
    dr.text((i * 240 + 20, 6), f"{mc.get(lab,{}).get('codepoint') or lab} → {hy}",
            fill=0, font=F)
out = os.path.join(OUT, "verdict_all.png")
sheet.save(out)
print(f"[写出] {out}")
