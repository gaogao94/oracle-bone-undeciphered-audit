# -*- coding: utf-8 -*-
"""
图像检索方法的可靠性验证（leave-one-out）
================================================
问题：形近检索出来的第一名，可信吗？
做法：拿【已释字】当查询，看它能否检索回自己的类。
      这是该方法唯一的客观标定方式——若已知字都找不回自己，结果不可信。
指标：top-1 / top-5 命中率、MRR、以及"第一名分数 vs 第二名分数"的间隔分布。
"""
import io, json, os, sys, zipfile, collections
import numpy as np
from PIL import Image
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
OB = os.path.join(D, "obimd")
RES = os.path.join(HERE, "result")

mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
Z = zipfile.ZipFile(os.path.join(OB, "subchar_images.zip"))
by_label = collections.defaultdict(list)
for n in Z.namelist():
    if n.lower().endswith(".png"):
        p = n.split("/")
        if len(p) >= 4:
            by_label[p[1]].append(n)

N = 48


def norm_array(path, box=96, pad=6):
    im = Image.open(Z.open(path)).convert("L")
    a = np.asarray(im, dtype=np.float32)
    if a.mean() < 128:
        a = 255.0 - a
    a = 255.0 - a
    a[a < 40] = 0
    ys, xs = np.nonzero(a > 40)
    if len(ys) == 0:
        return None
    crop = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = crop.shape
    s = (box - 2 * pad) / max(h, w)
    nh, nw = max(1, int(round(h * s))), max(1, int(round(w * s)))
    im2 = Image.fromarray(crop.astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("L", (box, box), 0)
    canvas.paste(im2, ((box - nw) // 2, (box - nh) // 2))
    return np.asarray(canvas.resize((N, N), Image.BOX), dtype=np.float32) / 255.0


def feats(v):
    b = (v > 0.35).astype(np.float32)
    if b.sum() == 0:
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


# 用全部有图像的类做留一验证（每类最多 4 个字形做参考，另取 1 个做查询）
labels = [l for l in by_label if l in mc and len(mc[l].get("codepoint") or "") == 1]
print(f"参与验证的类：{len(labels)}")

ref, queries = [], []
for lab in labels:
    ps = by_label[lab]
    if len(ps) < 2:
        continue
    for p in ps[:5]:
        v = norm_array(p)
        if v is None:
            continue
        f = feats(v)
        if f:
            ref.append((lab, f))
    p = ps[-1]
    v = norm_array(p)
    if v is not None:
        f = feats(v)
        if f:
            queries.append((lab, f))

print(f"参考字形 {len(ref):,}｜查询字形 {len(queries):,}")

ref_bin = np.stack([f["bin"].ravel() for _, f in ref])
ref_ink = np.array([f["ink"] for _, f in ref])
ref_asp = np.array([f["aspect"] for _, f in ref])
ref_row = np.stack([f["row"] for _, f in ref])
ref_col = np.stack([f["col"] for _, f in ref])
ref_lab = [l for l, _ in ref]

hits1 = hits5 = 0
mrr = 0.0
margins = []
for i, (lab, f) in enumerate(queries):
    q = f["bin"].ravel()
    inter = ref_bin @ q
    uni = ref_bin.sum(axis=1) + q.sum() - inter
    iou = np.divide(inter, uni, out=np.zeros_like(inter), where=uni > 0)
    denom = np.sqrt(ref_bin.sum(axis=1) * q.sum())
    cos = np.divide(inter, denom, out=np.zeros_like(inter), where=denom > 0)
    rr = np.array([cosv(f["row"], r) for r in ref_row])
    cc = np.array([cosv(f["col"], r) for r in ref_col])
    proj = (rr + cc) / 2
    aren = np.minimum(ref_ink, f["ink"]) / np.maximum(ref_ink, f["ink"])
    asp = np.minimum(ref_asp, f["aspect"]) / np.maximum(ref_asp, f["aspect"])
    tot = 0.40 * iou + 0.25 * cos + 0.15 * proj + 0.10 * aren + 0.10 * asp
    order = np.argsort(-tot)
    # 排除与自己同 label 的参考项？不排除——那正是正确目标
    rank = None
    for r, idx in enumerate(order, 1):
        if ref_lab[idx] == lab:
            rank = r
            break
    if rank == 1:
        hits1 += 1
    if rank and rank <= 5:
        hits5 += 1
    mrr += 1.0 / rank if rank else 0.0
    # 间隔：第一名（正确）与最高分的不同类之间的差
    other = [tot[idx] for idx in order if ref_lab[idx] != lab]
    if rank and other:
        correct_best = max(tot[idx] for idx in order if ref_lab[idx] == lab)
        margins.append(correct_best - max(other))
    if (i + 1) % 200 == 0:
        print(f"   … {i+1}/{len(queries)}  top1={hits1/(i+1):.1%}")

n = len(queries)
print("\n" + "=" * 78)
print("留一验证结果（图像检索方法的客观可靠性）")
print("=" * 78)
print(f"  查询数        {n:,}")
print(f"  Top-1 命中    {hits1:,}  ({hits1/n:.1%})")
print(f"  Top-5 命中    {hits5:,}  ({hits5/n:.1%})")
print(f"  MRR           {mrr/n:.3f}")
if margins:
    mg = np.array(margins)
    print(f"  正确类领先次名的分数间隔：中位 {np.median(mg):.3f}，"
          f"均值 {mg.mean():.3f}，>0 的比例 {(mg>0).mean():.1%}")

json.dump({"n_queries": n, "top1": hits1 / n, "top5": hits5 / n, "mrr": mrr / n,
           "margin_median": float(np.median(margins)) if margins else None,
           "margin_pos_rate": float((np.array(margins) > 0).mean()) if margins else None},
          open(os.path.join(RES, "retrieval_validation.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n[写出] result/retrieval_validation.json")
