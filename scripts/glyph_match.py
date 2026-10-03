# -*- coding: utf-8 -*-
"""
字形驱动检索（用户思路的正式实现）
================================================
不再用"槽位推断"，而是直接用字形图像：
  对每一个未释字形，在全部已释字形图像中检索最相似者，
  用图像相似度排序，输出对照图供人工判定。

这是"偏旁分析 / 对照法"的图像化实现——唐兰四法里被认为最可靠的那一路。
"""
import io, json, os, sys, zipfile, collections
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
OB = os.path.join(D, "obimd")
RES = os.path.join(HERE, "result")
IMG = os.path.join(RES, "glyph_match")
os.makedirs(IMG, exist_ok=True)

mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
Z = zipfile.ZipFile(os.path.join(OB, "subchar_images.zip"))

by_label = collections.defaultdict(list)
for n in Z.namelist():
    if n.lower().endswith(".png"):
        p = n.split("/")
        if len(p) >= 4:
            by_label[p[1]].append(n)

is_anon = lambda l: (mc.get(l, {}).get("transcription") or []) == []
anon_labels = [l for l in by_label if is_anon(l)]
known_labels = [l for l in by_label if not is_anon(l) and l in mc
                and len(mc[l].get("codepoint") or "") == 1]
print(f"图像覆盖：匿名 {len(anon_labels)} 类｜已释（有单字）{len(known_labels)} 类")

N = 48          # 归一化网格


def norm_array(path, box=96, pad=6):
    """读图 → 反相 → 裁到墨迹外框 → 等比缩放 → 居中 → 二值 48x48"""
    im = Image.open(Z.open(path)).convert("L")
    a = np.asarray(im, dtype=np.float32)
    if a.mean() < 128:                    # 黑底白字 → 反相
        a = 255.0 - a
    a = 255.0 - a                          # 变成"墨=高值"
    a[a < 40] = 0
    ys, xs = np.nonzero(a > 40)
    if len(ys) == 0:
        return None
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    crop = a[y0:y1 + 1, x0:x1 + 1]
    h, w = crop.shape
    s = (box - 2 * pad) / max(h, w)
    nh, nw = max(1, int(round(h * s))), max(1, int(round(w * s)))
    im2 = Image.fromarray(crop.astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("L", (box, box), 0)
    canvas.paste(im2, ((box - nw) // 2, (box - nh) // 2))
    small = canvas.resize((N, N), Image.BOX)
    v = np.asarray(small, dtype=np.float32) / 255.0
    return v


def feats(v):
    b = (v > 0.35).astype(np.float32)
    ys, xs = np.nonzero(b)
    if len(ys) == 0:
        return None
    bb = b[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = bb.shape
    return {
        "bin": b,
        "ink": float(b.mean()),
        "aspect": w / h,
        "row": b.sum(axis=1),
        "col": b.sum(axis=0),
    }


def cosv(u, v):
    nu, nv = np.linalg.norm(u), np.linalg.norm(v)
    return float(u @ v / (nu * nv)) if nu and nv else 0.0


def score(fa, fb):
    b1, b2 = fa["bin"], fb["bin"]
    inter = float((b1 * b2).sum())
    uni = float(((b1 + b2) > 0).sum())
    iou = inter / uni if uni else 0.0
    cos = float(inter / np.sqrt(b1.sum() * b2.sum())) if b1.sum() and b2.sum() else 0.0
    proj = (cosv(fa["row"], fb["row"]) + cosv(fa["col"], fb["col"])) / 2
    aren = min(fa["ink"], fb["ink"]) / max(fa["ink"], fb["ink"], 1e-6)
    asp = min(fa["aspect"], fb["aspect"]) / max(fa["aspect"], fb["aspect"], 1e-6)
    return {"iou": iou, "cos": cos, "proj": proj, "area": aren, "aspect": asp,
            "total": 0.40 * iou + 0.25 * cos + 0.15 * proj + 0.10 * aren + 0.10 * asp}


# ---- 参考库：每个已释类最多取 8 个字形
print("构建参考字形库 …")
ref = []
for lab in known_labels:
    for p in by_label[lab][:8]:
        v = norm_array(p)
        if v is None:
            continue
        f = feats(v)
        if f:
            ref.append((lab, p, f))
print(f"参考字形 {len(ref):,} 个（来自 {len(known_labels)} 个已释类）")

# ---- 查询：全部匿名类
print("比对匿名字形 …")
rows = []
for lab in anon_labels:
    best = []
    for p in by_label[lab][:3]:
        v = norm_array(p)
        if v is None:
            continue
        fq = feats(v)
        if fq is None:
            continue
        for rl, rp, fr in ref:
            s = score(fq, fr)
            best.append((s["total"], rl, rp, s, fq))
    if not best:
        rows.append({"label": lab, "status": "无可用字形"})
        continue
    best.sort(key=lambda x: -x[0])
    top = best[:5]
    rows.append({
        "label": lab,
        "glyph": mc.get(lab, {}).get("codepoint") or lab,
        "best": [{"char": mc.get(rl, {}).get("codepoint"), "ref_label": rl,
                  "detail": {k: round(v, 4) for k, v in s.items()}} for _, rl, _, s, _ in top],
        "score": round(top[0][0], 4),
        "_imgs": (by_label[lab][0], [rp for _, _, rp, _, _ in top]),
    })

rows.sort(key=lambda r: -r.get("score", 0))

# ---- 对照图
try:
    F = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 15)
except Exception:
    F = ImageFont.load_default()

for r in rows:
    if "_imgs" not in r:
        continue
    own, refs = r["_imgs"]
    cell = 120
    sheet = Image.new("L", (cell * (len(refs) + 1), cell + 30), 255)
    dr = ImageDraw.Draw(sheet)
    v = norm_array(own, 100)
    if v is not None:
        sheet.paste(Image.fromarray((255 - v * 255).astype(np.uint8)),
                    (cell // 2 - 50, cell // 2 - 50))
    dr.text((4, cell + 4), f"UNK {r['glyph']}", fill=0, font=F)
    for i, rp in enumerate(refs):
        v = norm_array(rp, 100)
        if v is not None:
            sheet.paste(Image.fromarray((255 - v * 255).astype(np.uint8)),
                        (cell * (i + 1) + cell // 2 - 50, cell // 2 - 50))
        dr.text((cell * (i + 1) + 4, cell + 4), r["best"][i]["char"] or "?", fill=0, font=F)
    out = os.path.join(IMG, f"{r['label']}.png")
    sheet.save(out)
    r["sheet"] = os.path.relpath(out, HERE)
    del r["_imgs"]

print("\n" + "=" * 96)
print("字形相似度检索结果（未释字形 → 最相似的已释字形）")
print("=" * 96)
print(f"{'未释字':>4} {'最高分':>7}  Top5 已释字（分数）")
print("-" * 96)
for r in rows[:30]:
    if "best" not in r:
        continue
    ts = "  ".join(f"{b['char']}({b['detail']['total']:.3f})" for b in r["best"])
    print(f"{r['glyph']:>4} {r['score']:>7.3f}  {ts}")

json.dump(rows[:200], open(os.path.join(RES, "glyph_match.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"\n[写出] result/glyph_match.json")
print(f"[对照图] {IMG}  （{sum(1 for r in rows if 'sheet' in r)} 张）")
