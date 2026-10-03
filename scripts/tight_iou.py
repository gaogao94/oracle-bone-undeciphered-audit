# -*- coding: utf-8 -*-
"""
修正版字形比对：把字形裁到墨迹外框内再等比缩放，杜绝背景混入
（前几版失败根因：归一化后仍含大片"伪墨"背景，致 IoU 全部趋同于 0.91+）
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
cp = lambda l: mc.get(l, {}).get("codepoint") or ""

by_label = collections.defaultdict(list)
for n in ZS.namelist():
    if n.lower().endswith(".png"):
        p = n.split("/")
        if len(p) >= 4:
            by_label.setdefault(p[1], []).append(n)

# 先诊断一张图的真实像素分布
tgt_png = by_label["urzeocieq8"][0]
arr = np.asarray(Image.open(ZS.open(tgt_png)).convert("L"))
print(f"原图 shape={arr.shape}  取值集合={np.unique(arr)[:8]}  均值={arr.mean():.1f}")
vals, cnts = np.unique(arr, return_counts=True)
print("像素直方图（前 8）:", list(zip(vals[:8].tolist(), cnts[:8].tolist())))


def ink_mask(arr):
    """判定墨迹：取少数派像素为墨"""
    v, c = np.unique(arr, return_counts=True)
    # 若深色像素少于一半，则深色为墨；否则浅色为墨
    dark = arr < 128
    if dark.mean() <= 0.5:
        return dark
    return ~dark


m = ink_mask(arr)
print(f"墨迹占比 {m.mean():.4f}")


def tight(path, box=96, pad=6):
    a = np.asarray(Image.open(ZS.open(path)).convert("L"))
    b = ink_mask(a)
    ys, xs = np.nonzero(b)
    if len(ys) < 5:
        return None
    bb = b[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = bb.shape
    # 裁到外框后等比缩放，保证墨迹充满画布
    s = (box - 2 * pad) / max(h, w)
    nh, nw = max(1, int(round(h * s))), max(1, int(round(w * s)))
    im2 = Image.fromarray((bb * 255).astype(np.uint8)).resize((nw, nh), Image.NEAREST)
    cv = Image.new("L", (box, box), 0)
    cv.paste(im2, ((box - nw) // 2, (box - nh) // 2))
    return np.asarray(cv) > 127


T = tight(tgt_png)
print(f"归一化后：shape={T.shape} 墨量={T.mean():.4f}")

# 目标自身的两个形（此处只 1 个）
print("\n先做自检：拿已释字中的已知同字不同形，看 IoU 是否合理")
for ch in ["中", "史", "目", "冊"]:
    lab = next((l for l, v in mc.items() if (v.get("codepoint") or "") == ch), None)
    if not lab or len(by_label[lab]) < 2:
        continue
    a1 = tight(by_label[lab][0])
    a2 = tight(by_label[lab][1])
    if a1 is None or a2 is None:
        continue
    iou = float((a1 & a2).sum()) / float((a1 | a2).sum())
    print(f"  「{ch}」形1 vs 形2: IoU = {iou:.3f}")

print("\n全库比对（已释字，取每字最优形）…")
rows = []
for lab, paths in by_label.items():
    if (mc.get(lab, {}).get("transcription") or []) == []:
        continue
    ch = cp(lab)
    if len(ch) != 1:
        continue
    best = 0.0
    for p in paths[:8]:
        M = tight(p)
        if M is None:
            continue
        inter = float((T & M).sum())
        uni = float((T | M).sum())
        if uni:
            best = max(best, inter / uni)
    if best > 0:
        rows.append((best, ch, lab))
rows.sort(reverse=True)
print(f"\n{'字':<4}{'IoU':>7}")
for b, ch, lab in rows[:25]:
    print(f"{ch:<4}{b:>7.3f}")

json.dump([{"char": ch, "iou": round(b, 4)} for b, ch, lab in rows[:100]],
          open(os.path.join(RES, "tight_iou.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n[写出] result/tight_iou.json")
