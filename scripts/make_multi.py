# -*- coding: utf-8 -*-
"""多假设并排对照：候选字 vs 各假设字的全部字形"""
import io, json, os, sys, zipfile, collections
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
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


def load(path, box=150):
    try:
        im = Image.open(Z.open(path)).convert("L")
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


try:
    F = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 20)
    FS = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 15)
except Exception:
    F = FS = ImageFont.load_default()


def compare(cand_label, hyps, n_show=5, fname=None):
    own = by_label.get(cand_label, [])
    cell = 150
    rows = 1 + len(hyps)
    sheet = Image.new("L", (cell * (n_show + 1) + 170, cell * rows + 40), 255)
    dr = ImageDraw.Draw(sheet)
    dr.text((8, 6), f"UNKNOWN {mc.get(cand_label,{}).get('codepoint') or cand_label}"
                    f"  ({len(own)} images)", fill=0, font=F)
    for j, p in enumerate(own[:n_show]):
        im = load(p)
        if im:
            sheet.paste(im, (170 + j * cell, 0))
    for i, hy in enumerate(hyps):
        y = 40 + i * cell
        dr.text((8, y + cell // 2 - 10), f"{hy}", fill=0, font=F)
        rl = label_of_char.get(hy)
        refs = by_label.get(rl, []) if rl else []
        dr.text((8, y + cell // 2 + 10), f"({len(refs)} imgs)", fill=0, font=FS)
        for j, p in enumerate(refs[:n_show]):
            im = load(p)
            if im:
                sheet.paste(im, (170 + j * cell, y))
    out = os.path.join(OUT, fname or f"multi_{cand_label}.png")
    sheet.save(out)
    print(f"[写出] {out}  ({sheet.width}x{sheet.height})")


# 1) mepmffeebh：验"矢+田+人"结构 → 寅/黃/堇/周
compare("mepmffeebh", ["寅", "黃", "堇", "周", "矢", "大"])
# 2) 󳦑：验是否人形字
compare("ptd0rmmnrv", ["大", "天", "夫", "交", "亦"])
# 3) 󺆑：验是否史/中/尹
compare("fybnj2savm", ["史", "中", "尹", "事", "吏"])
