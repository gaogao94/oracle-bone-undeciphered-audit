# -*- coding: utf-8 -*-
"""
从 facsimile（摹本）切出候选字及其上下文，生成大图供视觉分析
facsimile 与 rubbing 像素对齐，Position 同样适用
"""
import io, json, os, sys, zipfile, collections
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
OUT = os.path.join(HERE, "result", "plates")
os.makedirs(OUT, exist_ok=True)

ZF = zipfile.ZipFile(os.path.join(OB, "facsimile.zip"))
ZR = zipfile.ZipFile(os.path.join(OB, "rubbing.zip"))
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
cp = lambda l: mc.get(l, {}).get("codepoint") or "?"

_zc = {}


def img_of(z, path):
    if path not in _zc:
        _zc[path] = Image.open(z.open(path)).convert("RGB")
        if len(_zc) > 60:
            _zc.pop(next(iter(_zc)))
    return _zc[path]


def sheet_for(label, max_rows=8):
    """为某字形生成：每个出现处的整片摹本 + 该字放大图"""
    rows = []
    for p in data:
        for g in p.get("RecordUtilSentenceGroupVoList") or []:
            chars = sorted([c for c in (g.get("RecordUtilOracleCharVoList") or [])
                            if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
            for c in chars:
                if c["Label"] == label:
                    rows.append({"piece": p.get("RubbingName"), "fac": p.get("Facsimile"),
                                 "rub": p.get("Rubbing"), "pos": c.get("Position"),
                                 "char": c})
    rows = rows[:max_rows]
    if not rows:
        print(f"{label}: 无出现")
        return
    TH = 200
    ims = []
    for r in rows:
        try:
            im = img_of(ZF, r["fac"]).copy()
        except Exception as e:
            continue
        x, y, w, h = [int(v) for v in r["pos"].split(",")]
        pad = max(12, int(0.6 * max(w, h)))
        box = (max(0, x - pad), max(0, y - pad),
               min(im.width, x + w + pad), min(im.height, y + h + pad))
        if box[2] - box[0] < 5 or box[3] - box[1] < 5:
            continue
        crop = im.crop(box)
        sc = TH / crop.height
        crop = crop.resize((max(1, int(crop.width * sc)), TH), Image.LANCZOS)
        # 该字单独放大
        ch = im.crop((x, y, x + w, y + h)).resize((TH, TH), Image.LANCZOS)
        ims.append((r, crop, ch))
    if not ims:
        print(f"{label}: 切图失败")
        return
    cols = len(ims)
    W = 420 + cols * (max(i[1].width for i in ims) + 12)
    sheet = Image.new("RGB", (W, TH * 2 + 90), "white")
    dr = ImageDraw.Draw(sheet)
    try:
        F = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 20)
        FS = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 16)
    except Exception:
        F = FS = ImageFont.load_default()
    dr.text((8, 6), f"label={label}   glyph={cp(label)}   出现 {len(ims)} 处", fill="black", font=F)
    x0 = 8
    for i, (r, crop, ch) in enumerate(ims):
        sheet.paste(crop, (x0, 40))
        sheet.paste(ch, (x0 + crop.width // 2 - TH // 2, 40 + TH + 22))
        dr.text((x0, 40 + TH + 2), r["piece"], fill="black", font=FS)
        x0 += crop.width + 12
    dr.text((8, TH + 50), "上排：原片摹本局部（含上下文）　下排：本字放大", fill="black", font=FS)
    out = os.path.join(OUT, f"plate_{label}.png")
    sheet.save(out)
    print(f"[写出] {out}  ({len(ims)} 处)")
    return out


for lab in ["mepmffeebh", "fybnj2savm", "ptd0rmmnrv"]:
    sheet_for(lab)
