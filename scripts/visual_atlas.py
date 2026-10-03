# -*- coding: utf-8 -*-
"""
视觉语言检索：按"画的是什么"归类，而非按字比对
目标 󺡅 的视觉构成：尖顶(人形/帳篷) + 中部实体(有内画) + 下部双腿
建一批"人形/屋形/木形"字的图集，放大目验
"""
import io, os, sys, json, collections, zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
FIG = os.path.join(HERE, "figures")
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
label_of_char = {}
for lab, v in mc.items():
    c = v.get("codepoint") or ""
    if len(c) == 1:
        label_of_char.setdefault(c, lab)
freq = collections.Counter()
for p in data:
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        for c in g.get("RecordUtilOracleCharVoList") or []:
            if c.get("Label"):
                freq[c["Label"]] += 1

# 按"视觉母题"分组
GROUPS = {
    "屋形／尖顶＋下部双腿": ["余", "舍", "宋", "宗", "宀", "京", "高", "亳", "亯", "享", "亭", "郭", "宮", "室", "安", "宿", "冓", "來", "麥"],
    "木形／树": ["木", "桑", "粟", "黍", "禾", "米", "東", "朱", "未", "本", "末", "林", "森", "楚", "李", "杏"],
    "人形／立人": ["大", "天", "夫", "文", "立", "交", "亦", "央", "夾", "乘", "眾", "先", "光", "堯", "老", "長", "元", "兄", "兒"],
    "手形／持物": ["又", "尹", "及", "取", "秉", "用", "爭", "受", "父", "攴", "史", "事"],
    "目形／眼": ["目", "見", "望", "省", "直", "監", "臨", "相", "眉", "臣", "民"],
}

F = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 22)
FS = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 17)
CELL = 150
NC = 5


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


TGT = "gx21ndp7yy"
for gi, (gname, chars) in enumerate(GROUPS.items()):
    rows = [("󺡅 未釋", TGT)]
    for ch in chars:
        l = label_of_char.get(ch)
        if l and by_label.get(l):
            rows.append((f"{ch}({freq[l]})", l))
    if len(rows) < 3:
        continue
    W = 250 + CELL * NC
    H = CELL * len(rows) + 70
    sheet = Image.new("L", (W, H), 255)
    dr = ImageDraw.Draw(sheet)
    dr.text((10, 8), f"圖 S{gi+1}  󺡅 與「{gname}」諸字", fill=0, font=F)
    for i, (nm, lab) in enumerate(rows):
        y = 54 + i * CELL
        dr.text((10, y + CELL // 2), nm, fill=0, font=FS)
        for j, p in enumerate(by_label.get(lab, [])[:NC]):
            im = gimg(p)
            if im:
                sheet.paste(im, (250 + j * CELL, y))
        dr.line([(0, y + CELL), (W, y + CELL)], fill=205, width=1)
    fp = os.path.join(FIG, f"figS{gi+1}_visual.png")
    sheet.save(fp)
    print(f"[写出] {fp}  {sheet.width}x{sheet.height}  {len(rows)} 行  ({gname})")
