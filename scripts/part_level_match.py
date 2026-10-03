# -*- coding: utf-8 -*-
"""
部件级检索：找含「矢镞 + 方框 + 人足」结构组合的字形
做法：把字形切成上/中/下三段，分别量化各段的横向占用剖面与连通域特征，
      再在全部字形里找三段结构同时相近者。避免整体 IoU 被墨量主导。
"""
import io, json, os, sys, zipfile, collections
import numpy as np
from PIL import Image
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
RES = os.path.join(HERE, "result")

mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
Z = zipfile.ZipFile(os.path.join(OB, "subchar_images.zip"))
by_label = collections.defaultdict(list)
for n in Z.namelist():
    if n.lower().endswith(".png"):
        p = n.split("/")
        if len(p) >= 4:
            by_label[p[1]].append(n)

SZ = 64
BOX = 96
PAD = 6


def mask(path):
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
    s = (BOX - 2 * PAD) / max(h, w)
    nh, nw = max(1, int(round(h * s))), max(1, int(round(w * s)))
    im2 = Image.fromarray((bb * 255).astype(np.uint8)).resize((nw, nh), Image.NEAREST)
    cv = Image.new("L", (BOX, BOX), 0)
    cv.paste(im2, ((BOX - nw) // 2, (BOX - nh) // 2))
    m = np.asarray(cv) > 127
    if m.sum() < 5:
        return None
    # 裁到墨迹，保证按字形本体分三段
    ys, xs = np.nonzero(m)
    return m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def segments(m, k=3):
    """按高度均分为 k 段，返回每段的占用剖面与统计"""
    H, W = m.shape
    out = []
    for i in range(k):
        seg = m[i * H // k:(i + 1) * H // k + (1 if i == k - 1 else 0), :]
        if seg.size == 0:
            out.append(None)
            continue
        col = seg.sum(axis=0).astype(np.float32)
        if col.max() > 0:
            col = col / col.max()
        # 重采样到固定 16 列，便于比较
        idx = np.linspace(0, len(col) - 1, 16).astype(int)
        prof = col[idx]
        # 段内墨迹在水平方向是否集中（方框/矢镞特征）
        ink = float(seg.mean())
        cols_used = float((seg.sum(axis=0) > 0).mean())
        # 段内质心（左右对称性）
        xs = np.nonzero(seg.any(axis=0))[0]
        center = float((xs.mean() / max(1, W - 1))) if len(xs) else 0.5
        out.append({"prof": prof, "ink": ink, "cols_used": cols_used, "center": center})
    return out


def seg_sim(a, b):
    if a is None or b is None:
        return 0.0
    u, v = a["prof"] - a["prof"].mean(), b["prof"] - b["prof"].mean()
    nu, nv = np.linalg.norm(u), np.linalg.norm(v)
    pc = float(u @ v / (nu * nv)) if nu > 1e-6 and nv > 1e-6 else 0.0
    ink = min(a["ink"], b["ink"]) / max(a["ink"], b["ink"], 1e-6)
    cu = min(a["cols_used"], b["cols_used"]) / max(a["cols_used"], b["cols_used"], 1e-6)
    cen = 1.0 - abs(a["center"] - b["center"])
    return 0.45 * pc + 0.25 * ink + 0.15 * cu + 0.15 * cen


TARGET = "mepmffeebh"
tgt_masks = [mask(p) for p in by_label[TARGET]]
tgt_masks = [m for m in tgt_masks if m is not None]
print(f"目标 {TARGET}: {len(tgt_masks)} 个字形")
tgt_segs = [segments(m) for m in tgt_masks]
for i, s in enumerate(tgt_segs[0]):
    print(f"  段{i+1}: 墨量={s['ink']:.3f} 横向占比={s['cols_used']:.3f} 质心={s['center']:.3f}")

print("\n构建全库分段特征 …")
feat = []
for i, lab in enumerate(by_label):
    for p in by_label[lab][:25]:
        m = mask(p)
        if m is None:
            continue
        sg = segments(m)
        if any(s is None for s in sg):
            continue
        feat.append((lab, sg))
    if (i + 1) % 400 == 0:
        print(f"   … {i+1}/{len(by_label)}  {len(feat):,}")
print(f"特征 {len(feat):,}")

best = collections.defaultdict(float)
for rl, rsg in feat:
    s = sum(seg_sim(t, r) for t, r in zip(tgt_segs[0], rsg)) / 3
    if s > best[rl]:
        best[rl] = s

top = sorted(best.items(), key=lambda x: -x[1])[:20]
print("\n" + "=" * 80)
print("部件级（三段结构）检索 — 最相似的已释字")
print("=" * 80)
for rl, s in top:
    c = mc.get(rl, {}).get("codepoint") or "?"
    print(f"  {c}  ({rl})  相似度 {s:.4f}   字形数 {len(by_label[rl])}")

json.dump([{"char": mc.get(rl, {}).get("codepoint"), "label": rl, "score": round(s, 4)}
           for rl, s in top],
          open(os.path.join(RES, "part_level_match.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n[写出] result/part_level_match.json")
