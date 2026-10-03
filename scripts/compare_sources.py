# -*- coding: utf-8 -*-
"""
原拓 vs 摹本：两种字形源的方法可靠性对照（留一法）
回答一个问题：从原拓切字，是否比用字形包里的摹本更可靠？
"""
import io, json, os, sys, zipfile, collections, random
import numpy as np
from PIL import Image
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
OB = os.path.join(D, "obimd")
RES = os.path.join(HERE, "result")

mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
ZR = zipfile.ZipFile(os.path.join(OB, "rubbing.zip"))
ZS = zipfile.ZipFile(os.path.join(OB, "subchar_images.zip"))

_ic = {}


def get_img(path):
    if path not in _ic:
        _ic[path] = Image.open(ZR.open(path)).convert("L")
        if len(_ic) > 400:
            _ic.pop(next(iter(_ic)))
    return _ic[path]


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
            if w >= 3 and h >= 3:
                occ[c["Label"]].append((rp, (x, y, w, h)))

N = 48


def finish(b, box=96, pad2=6):
    ys, xs = np.nonzero(b)
    if len(ys) < 5:
        return None
    bb = b[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    hh, ww = bb.shape
    s = (box - 2 * pad2) / max(hh, ww)
    nh, nw = max(1, int(round(hh * s))), max(1, int(round(ww * s)))
    im2 = Image.fromarray((bb * 255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("L", (box, box), 0)
    canvas.paste(im2, ((box - nw) // 2, (box - nh) // 2))
    return np.asarray(canvas.resize((N, N), Image.BOX), dtype=np.float32) / 255.0


def crop_rub(rp, box, pad=4):
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
    if a.mean() > 128:
        a = 255.0 - a
    hist, _ = np.histogram(a, bins=256, range=(0, 255))
    tot = a.size
    best, thr, cum = 0, 128, 0
    sumall = float((np.arange(256) * hist).sum())
    for t in range(256):
        cum += hist[t]
        if cum == 0 or cum == tot:
            continue
        wB = cum / tot
        s1 = float((np.arange(t + 1) * hist[:t + 1]).sum())
        mB = s1 / cum
        mF = (sumall - s1) / (tot - cum)
        v = wB * (1 - wB) * (mB - mF) ** 2
        if v > best:
            best, thr = v, t
    return finish((a > max(20, thr)).astype(np.float32))


# 摹本字形包
by_label_sub = collections.defaultdict(list)
for n in ZS.namelist():
    if n.lower().endswith(".png"):
        p = n.split("/")
        if len(p) >= 4:
            by_label_sub[p[1]].append(n)


def crop_sub(path):
    im = Image.open(ZS.open(path)).convert("L")
    a = np.asarray(im, dtype=np.float32)
    if a.mean() < 128:
        a = 255.0 - a
    a = 255.0 - a
    a[a < 40] = 0
    return finish((a > 40).astype(np.float32))


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


def sc(fa, fb):
    b1, b2 = fa["bin"], fb["bin"]
    inter = float((b1 * b2).sum())
    uni = float(((b1 + b2) > 0).sum())
    iou = inter / uni if uni else 0
    cos = float(inter / np.sqrt(b1.sum() * b2.sum())) if b1.sum() and b2.sum() else 0
    proj = (cosv(fa["row"], fb["row"]) + cosv(fa["col"], fb["col"])) / 2
    aren = min(fa["ink"], fb["ink"]) / max(fa["ink"], fb["ink"], 1e-6)
    asp = min(fa["aspect"], fb["aspect"]) / max(fa["aspect"], fb["aspect"], 1e-6)
    return 0.40 * iou + 0.25 * cos + 0.15 * proj + 0.10 * aren + 0.10 * asp


# 取样本：有 ≥4 个位置记录的已释类
pool = [l for l in occ if not (mc.get(l, {}).get("transcription") or []) == []
        and len(mc.get(l, {}).get("codepoint") or "") == 1 and len(occ[l]) >= 4]
random.seed(11)
sample = random.sample(pool, min(200, len(pool)))
print(f"验证样本：{len(sample)} 个已释类（每类留 1 个做查询，其余做参考）")

results = {}
for mode in ("rubbing", "facsimile"):
    ref, qs = [], []
    for lab in sample:
        recs = occ[lab]
        if mode == "facsimile":
            subs = by_label_sub.get(lab, [])
            if len(subs) < 2:
                continue
            vs = []
            for p in subs[:5]:
                v = crop_sub(p)
                if v is not None:
                    f = feats(v)
                    if f:
                        vs.append(f)
            if len(vs) < 2:
                continue
            ref += [(lab, f) for f in vs[:-1]]
            qs.append((lab, vs[-1]))
        else:
            vs = []
            for rp, box in recs[:5]:
                v = crop_rub(rp, box)
                if v is not None:
                    f = feats(v)
                    if f:
                        vs.append(f)
            if len(vs) < 2:
                continue
            ref += [(lab, f) for f in vs[:-1]]
            qs.append((lab, vs[-1]))

    rb = np.stack([f["bin"].ravel() for _, f in ref])
    rink = np.array([f["ink"] for _, f in ref])
    rasp = np.array([f["aspect"] for _, f in ref])
    rrow = np.stack([f["row"] for _, f in ref])
    rcol = np.stack([f["col"] for _, f in ref])
    rlab = [l for l, _ in ref]

    h1 = h5 = 0
    mrr = 0.0
    margins = []
    for lab, f in qs:
        q = f["bin"].ravel()
        inter = rb @ q
        uni = rb.sum(axis=1) + q.sum() - inter
        iou = np.divide(inter, uni, out=np.zeros_like(inter), where=uni > 0)
        den = np.sqrt(rb.sum(axis=1) * q.sum())
        cos = np.divide(inter, den, out=np.zeros_like(inter), where=den > 0)
        rr = np.array([cosv(f["row"], r) for r in rrow])
        cc = np.array([cosv(f["col"], r) for r in rcol])
        proj = (rr + cc) / 2
        aren = np.minimum(rink, f["ink"]) / np.maximum(rink, f["ink"])
        asp = np.minimum(rasp, f["aspect"]) / np.maximum(rasp, f["aspect"])
        tot = 0.40 * iou + 0.25 * cos + 0.15 * proj + 0.10 * aren + 0.10 * asp
        order = np.argsort(-tot)
        rank = next((r for r, idx in enumerate(order, 1) if rlab[idx] == lab), None)
        if rank == 1:
            h1 += 1
        if rank and rank <= 5:
            h5 += 1
        mrr += 1 / rank if rank else 0
        other = [tot[idx] for idx in order if rlab[idx] != lab]
        own = max(tot[idx] for idx in order if rlab[idx] == lab)
        if other:
            margins.append(own - max(other))
    n = len(qs)
    mg = np.array(margins)
    results[mode] = {"n": n, "top1": h1 / n if n else 0, "top5": h5 / n if n else 0,
                     "mrr": mrr / n if n else 0,
                     "margin_median": float(np.median(mg)) if len(mg) else None}
    print(f"\n[{mode}]  查询 {n}")
    print(f"   Top-1 {results[mode]['top1']:.1%}｜Top-5 {results[mode]['top5']:.1%}"
          f"｜MRR {results[mode]['mrr']:.3f}"
          f"｜领先间隔中位 {results[mode]['margin_median']:.3f}")

json.dump(results, open(os.path.join(RES, "source_comparison.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n[写出] result/source_comparison.json")
