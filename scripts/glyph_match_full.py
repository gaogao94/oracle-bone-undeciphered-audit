# -*- coding: utf-8 -*-
"""
修正版字形检索：用【全部字形】而非"每类第一张"
- 参考库：每类的全部字形（上限 60）
- 候选：全部字形对参考库取最优
- 同时报告：类级中位相似度、最优间隔、以及参考类的字形总数
"""
import io, json, os, sys, zipfile, collections
import numpy as np
from PIL import Image
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
OB = os.path.join(D, "obimd")
RES = os.path.join(HERE, "result")
os.makedirs(RES, exist_ok=True)

mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
Z = zipfile.ZipFile(os.path.join(OB, "subchar_images.zip"))
by_label = collections.defaultdict(list)
for n in Z.namelist():
    if n.lower().endswith(".png"):
        p = n.split("/")
        if len(p) >= 4:
            by_label[p[1]].append(n)

N = 48
CACHE = {}


def arr(path):
    if path in CACHE:
        return CACHE[path]
    try:
        im = Image.open(Z.open(path)).convert("L")
    except Exception:
        CACHE[path] = None
        return None
    a = np.asarray(im, dtype=np.float32)
    if a.mean() < 128:
        a = 255 - a
    a = 255 - a
    a[a < 40] = 0
    b = (a > 40).astype(np.float32)
    ys, xs = np.nonzero(b)
    if len(ys) < 5:
        CACHE[path] = None
        return None
    bb = b[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = bb.shape
    box, pad = 96, 6
    s = (box - 2 * pad) / max(h, w)
    nh, nw = max(1, int(round(h * s))), max(1, int(round(w * s)))
    im2 = Image.fromarray((bb * 255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
    cv = Image.new("L", (box, box), 0)
    cv.paste(im2, ((box - nw) // 2, (box - nh) // 2))
    v = np.asarray(cv.resize((N, N), Image.BOX), dtype=np.float32) / 255.0
    if len(CACHE) < 60000:
        CACHE[path] = v
    return v


is_anon = lambda l: (mc.get(l, {}).get("transcription") or []) == []
anon_labels = [l for l in by_label if is_anon(l)]
known_labels = [l for l in by_label if not is_anon(l)
                and len(mc.get(l, {}).get("codepoint") or "") == 1]
print(f"匿名 {len(anon_labels)} 类｜已释 {len(known_labels)} 类")

MAXREF = 60
print("构建参考库（全部字形）…")
ref_bins, ref_lab = [], []
for i, lab in enumerate(known_labels):
    for p in by_label[lab][:MAXREF]:
        v = arr(p)
        if v is not None:
            ref_bins.append((v > 0.35).ravel())
            ref_lab.append(lab)
    if (i + 1) % 400 == 0:
        print(f"   … {i+1}/{len(known_labels)}  参考字形 {len(ref_bins):,}")
RB = np.stack(ref_bins).astype(np.float32)
RL = np.array(ref_lab)
print(f"参考字形总数 {RB.shape[0]:,}")

ref_sum = RB.sum(axis=1)


def query(bin_q):
    inter = RB @ bin_q
    uni = ref_sum + bin_q.sum() - inter
    iou = np.divide(inter, uni, out=np.zeros_like(inter), where=uni > 0)
    return inter, iou


rows = []
print("检索候选 …")
for i, lab in enumerate(anon_labels):
    scores = collections.defaultdict(list)
    for p in by_label[lab]:
        v = arr(p)
        if v is None:
            continue
        q = (v > 0.35).ravel().astype(np.float32)
        if q.sum() < 5:
            continue
        inter, iou = query(q)
        for j in np.nonzero(iou > 0.25)[0]:
            scores[RL[j]].append(float(iou[j]))
    if not scores:
        continue
    stat = []
    for L, vs in scores.items():
        vs = sorted(vs, reverse=True)
        stat.append((max(vs), float(np.median(vs)), len(vs), L))
    stat.sort(reverse=True)
    rows.append({
        "label": lab,
        "glyph": mc.get(lab, {}).get("codepoint") or lab,
        "n_own_images": len(by_label[lab]),
        "top": [{"char": mc.get(L, {}).get("codepoint"), "label": L,
                 "best_iou": round(b, 4), "median_iou": round(m, 4), "n_hits": n,
                 "n_ref_images": len(by_label[L])}
                for b, m, n, L in stat[:6]],
    })
    if (i + 1) % 50 == 0:
        print(f"   … {i+1}/{len(anon_labels)}")

rows.sort(key=lambda r: -r["top"][0]["best_iou"])
json.dump(rows, open(os.path.join(RES, "glyph_match_full.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("\n" + "=" * 100)
print("全量字形检索 — 前 20（best_iou｜median_iou｜命中数）")
print("=" * 100)
for r in rows[:20]:
    ts = "  ".join(f"{t['char']}({t['best_iou']:.2f}/{t['median_iou']:.2f}/{t['n_hits']})"
                   for t in r["top"][:4])
    print(f"{r['glyph']:>4} [{r['n_own_images']}图]  {ts}")

print("\n=== 重点：候选的类级稳定性（median 高才算真像，仅 best 高可能是巧合）===")
stable = [r for r in rows if r["top"][0]["median_iou"] >= 0.30 and r["top"][0]["n_hits"] >= 3]
print(f"类级中位 IoU ≥0.30 且命中 ≥3 的候选：{len(stable)}")
for r in stable[:15]:
    t = r["top"][0]
    print(f"  {r['glyph']} → 「{t['char']}」 best={t['best_iou']:.3f} "
          f"median={t['median_iou']:.3f} 命中{t['n_hits']} 参考{t['n_ref_images']}图")
