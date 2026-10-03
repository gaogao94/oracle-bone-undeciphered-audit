# -*- coding: utf-8 -*-
"""
关键假设：󵱙（4次，1个字形）可能是某个已释字「单字形类」的异体/误分。
已释字中的单字形类（只被收录一次字形者）是重点嫌疑。
"""
import io, json, os, sys, collections, zipfile
import numpy as np
from PIL import Image
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
RES = os.path.join(HERE, "result")
ZS = zipfile.ZipFile(os.path.join(OB, "subchar_images.zip"))
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
cp = lambda l: mc.get(l, {}).get("codepoint") or ""

by_label = collections.defaultdict(list)
for n in ZS.namelist():
    if n.lower().endswith(".png"):
        p = n.split("/")
        if len(p) >= 4:
            by_label.setdefault(p[1], []).append(n)

sents = []
for p in data:
    nm = p.get("RubbingName")
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        seq = sorted([c for c in (g.get("RecordUtilOracleCharVoList") or [])
                      if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
        if seq:
            sents.append((nm, [c["Label"] for c in seq]))
freq = collections.Counter()
for _, s in sents:
    freq.update(s)

TGT = "urzeocieq8"
tgt_png = by_label[TGT][0]
tgt_m = np.asarray(Image.open(ZS.open(tgt_png)).convert("L")) > 128

print(f"目标 󵱙: {len(by_label[TGT])} 个字形，出现 {freq[TGT]} 次")
print(f"  原图尺寸 {tgt_m.shape}, 墨占比 {tgt_m.mean():.4f}")

# 全部「1 字形」的已释字类
one_glyph = [l for l in by_label
             if len(by_label[l]) == 1
             and (mc.get(l, {}).get("transcription") or []) != []
             and len(cp(l)) == 1]
print(f"已释字中的「单字形类」: {len(one_glyph)} 个")

B = 64


def norm(mask, box=96, pad=8):
    ys, xs = np.nonzero(mask)
    if len(ys) < 5:
        return None
    bb = mask[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = bb.shape
    s = (box - 2 * pad) / max(h, w)
    nh, nw = max(1, int(round(h * s))), max(1, int(round(w * s)))
    im2 = Image.fromarray((bb * 255).astype(np.uint8)).resize((nw, nh), Image.NEAREST)
    cv = Image.new("L", (box, box), 0)
    cv.paste(im2, ((box - nw) // 2, (box - nh) // 2))
    return np.asarray(cv) > 127


T = norm(tgt_m)
print(f"  归一化后墨量 {T.mean():.3f}")

rows = []
for l in one_glyph:
    try:
        m = np.asarray(Image.open(ZS.open(by_label[l][0])).convert("L")) > 128
    except Exception:
        continue
    M = norm(m)
    if M is None:
        continue
    inter = float((T & M).sum())
    uni = float((T | M).sum())
    iou = inter / uni if uni else 0.0
    cos = inter / ((float(T.sum()) * float(M.sum())) ** 0.5) if T.sum() and M.sum() else 0.0
    # 形状比例
    ty, tx = np.nonzero(T)
    my, mx = np.nonzero(M)
    ar_t = (tx.max() - tx.min() + 1) / (ty.max() - ty.min() + 1)
    ar_m = (mx.max() - mx.min() + 1) / (my.max() - my.min() + 1)
    ar = min(ar_t, ar_m) / max(ar_t, ar_m)
    score = 0.45 * iou + 0.35 * cos + 0.20 * ar
    rows.append((score, iou, cos, ar, cp(l), freq[l], l))

rows.sort(reverse=True)
print("\n" + "=" * 92)
print("与「单字形类」的相似度排序（前 20）")
print("=" * 92)
print(f"{'字':<4}{'综合':>7}{'IoU':>7}{'余弦':>7}{'长宽比':>7}{'语料次数':>9}")
for sc, iou, cos, ar, ch, f, l in rows[:20]:
    print(f"{ch:<4}{sc:>7.3f}{iou:>7.3f}{cos:>7.3f}{ar:>7.3f}{f:>9}")

json.dump([{"char": ch, "score": round(sc, 4), "iou": round(iou, 4), "cos": round(cos, 4),
            "ar": round(ar, 4), "freq": f} for sc, iou, cos, ar, ch, f, l in rows[:60]],
          open(os.path.join(RES, "one_glyph_match.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"\n[写出] result/one_glyph_match.json")
