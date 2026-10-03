# -*- coding: utf-8 -*-
"""
原拓切字流水线 + 重跑字形比对
================================================
1) 按 Position(x,y,w,h) 从 rubbing/*.jpg 切出真实拓片字形
2) 对候选字重跑形近检索（对照组：已释字的原拓字形）
3) 生成原拓对照图，与摹本结果比较
4) 留一法复标定：换到原拓后 top-1 是否保持
"""
import io, json, os, sys, zipfile, collections, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
OB = os.path.join(D, "obimd")
RES = os.path.join(HERE, "result")
OUT = os.path.join(RES, "rubbing_match")
os.makedirs(OUT, exist_ok=True)

mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
Z = zipfile.ZipFile(os.path.join(OB, "rubbing.zip"))

# 预打所有图像到内存（10,077 张，约 532MB 压缩；只按需读，加缓存）
_imgcache = {}


def get_img(path):
    if path not in _imgcache:
        _imgcache[path] = Image.open(Z.open(path)).convert("L")
        if len(_imgcache) > 400:
            _imgcache.pop(next(iter(_imgcache)))
    return _imgcache[path]


# 收集：label -> [(rubbing_path, (x,y,w,h))]
occ = collections.defaultdict(list)
for p in data:
    rp = p.get("Rubbing")
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        for c in g.get("RecordUtilOracleCharVoList") or []:
            if c.get("SeatFont") or not c.get("Label") or not c.get("Position"):
                continue
            try:
                x, y, w, h = [int(v) for v in c["Position"].split(",")]
            except Exception:
                continue
            if w < 3 or h < 3:
                continue
            occ[c["Label"]].append((rp, (x, y, w, h)))
print(f"可切字的字形类 {len(occ):,}；位置记录 {sum(len(v) for v in occ.values()):,}")

N = 48


def crop_norm(rp, box, pad=4):
    """从拓片切出字形 → 反相 → 裁墨迹 → 归一化"""
    try:
        im = get_img(rp)
    except Exception:
        return None
    x, y, w, h = box
    x0, y0 = max(0, x - pad), max(0, y - pad)
    x1, y1 = min(im.width, x + w + pad), min(im.height, y + h + pad)
    if x1 - x0 < 3 or y1 - y0 < 3:
        return None
    a = np.asarray(im.crop((x0, y0, x1, y1)), dtype=np.float32)
    if a.mean() > 128:                 # 白底黑字 → 反相
        a = 255.0 - a
    # 自适应阈值：拓片噪点多，用 Otsu 近似
    hist, _ = np.histogram(a, bins=256, range=(0, 255))
    tot = a.size
    best, thr, cum, sumall = 0, 128, 0, float((np.arange(256) * hist).sum())
    for t in range(256):
        cum += hist[t]
        if cum == 0:
            continue
        wB = cum / tot
        mB = float((np.arange(t + 1) * hist[:t + 1]).sum()) / cum
        if cum == tot:
            break
        mF = (sumall - float((np.arange(t + 1) * hist[:t + 1]).sum())) / (tot - cum)
        v = wB * (1 - wB) * (mB - mF) ** 2
        if v > best:
            best, thr = v, t
    b = (a > max(20, thr)).astype(np.float32)
    ys, xs = np.nonzero(b)
    if len(ys) < 5:
        return None
    bb = b[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    hh, ww = bb.shape
    box96, pad2 = 96, 6
    s = (box96 - 2 * pad2) / max(hh, ww)
    nh, nw = max(1, int(round(hh * s))), max(1, int(round(ww * s)))
    im2 = Image.fromarray((bb * 255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("L", (box96, box96), 0)
    canvas.paste(im2, ((box96 - nw) // 2, (box96 - nh) // 2))
    return np.asarray(canvas.resize((N, N), Image.BOX), dtype=np.float32) / 255.0


def feats(v):
    b = (v > 0.35).astype(np.float32)
    if b.sum() < 3:
        return None
    ys, xs = np.nonzero(b)
    bb = b[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = bb.shape
    return {"bin": b, "ink": float(b.mean()), "aspect": w / h,
            "row": b.sum(axis=1), "col": b.sum(axis=0)}


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
    return 0.40 * iou + 0.25 * cos + 0.15 * proj + 0.10 * aren + 0.10 * asp


is_anon = lambda l: (mc.get(l, {}).get("transcription") or []) == []
anon_labels = [l for l in occ if is_anon(l)]
known_labels = [l for l in occ if not is_anon(l) and len(mc.get(l, {}).get("codepoint") or "") == 1]
print(f"原拓可切：匿名 {len(anon_labels)} 类｜已释 {len(known_labels)} 类")

# ---- 参考库
print("切参考字形 …")
ref = []
random.seed(7)
for lab in known_labels:
    picks = occ[lab][:2] + random.sample(occ[lab], min(2, len(occ[lab])))
    for rp, box in picks[:3]:
        v = crop_norm(rp, box)
        if v is None:
            continue
        f = feats(v)
        if f:
            ref.append((lab, f))
print(f"参考字形 {len(ref):,}")

# ---- 候选检索
print("比对候选 …")
rows = []
for i, lab in enumerate(anon_labels):
    best = []
    for rp, box in occ[lab][:2]:
        v = crop_norm(rp, box)
        if v is None:
            continue
        fq = feats(v)
        if fq is None:
            continue
        for rl, fr in ref:
            best.append((score(fq, fr), rl))
    if not best:
        continue
    best.sort(key=lambda x: -x[0])
    # 同一类的多个字形只保留最高分
    seen, top = set(), []
    for sc, rl in best:
        if rl in seen:
            continue
        seen.add(rl)
        top.append((sc, rl))
        if len(top) == 5:
            break
    rows.append({"label": lab, "glyph": mc.get(lab, {}).get("codepoint") or lab,
                 "top": [{"char": mc.get(rl, {}).get("codepoint"), "label": rl,
                          "score": round(sc, 4)} for sc, rl in top]})
    if (i + 1) % 50 == 0:
        print(f"   … {i+1}/{len(anon_labels)}")

rows.sort(key=lambda r: -r["top"][0]["score"])
json.dump(rows, open(os.path.join(RES, "rubbing_match.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("\n" + "=" * 92)
print("原拓字形检索 — 前 15")
print("=" * 92)
for r in rows[:15]:
    ts = "  ".join(f"{t['char']}({t['score']:.3f})" for t in r["top"])
    print(f"{r['glyph']:>4} {r['top'][0]['score']:>7.3f}  {ts}")

print("\n[写出] result/rubbing_match.json")
