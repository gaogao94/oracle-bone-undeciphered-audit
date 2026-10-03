# -*- coding: utf-8 -*-
"""核查：同字形的不同 SubLabel 是否图像不同（判断检索的"自己人"干扰）"""
import io, json, os, sys, zipfile, collections
import numpy as np
from PIL import Image
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
Z = zipfile.ZipFile(os.path.join(OB, "subchar_images.zip"))

by_label = collections.defaultdict(list)
for n in Z.namelist():
    if n.lower().endswith(".png"):
        p = n.split("/")
        if len(p) >= 4:
            by_label[p[1]].append(n)

N = 48


def arr(path):
    im = Image.open(Z.open(path)).convert("L")
    a = np.asarray(im, dtype=np.float32)
    if a.mean() < 128:
        a = 255 - a
    a = 255 - a
    a[a < 40] = 0
    b = (a > 40).astype(np.float32)
    ys, xs = np.nonzero(b)
    if len(ys) < 5:
        return None
    bb = b[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    h, w = bb.shape
    box, pad = 96, 6
    s = (box - 2 * pad) / max(h, w)
    nh, nw = max(1, int(round(h * s))), max(1, int(round(w * s)))
    im2 = Image.fromarray((bb * 255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
    cv = Image.new("L", (box, box), 0)
    cv.paste(im2, ((box - nw) // 2, (box - nh) // 2))
    return np.asarray(cv.resize((N, N), Image.BOX), dtype=np.float32) / 255.0


def iou(a, b):
    x = (a > 0.35)
    y = (b > 0.35)
    i = float((x & y).sum())
    u = float((x | y).sum())
    return i / u if u else 0.0


# 1) 同一 SubLabel 内的多个字形，是否图像相同？
print("=== 同一 SubLabel 内的字形重复度 ===")
dups = []
for lab in list(by_label)[:300]:
    imgs = by_label[lab]
    if len(imgs) < 2:
        continue
    a = arr(imgs[0])
    b = arr(imgs[1])
    if a is None or b is None:
        continue
    dups.append(iou(a, b))
dups = np.array(dups)
print(f"  样本 {len(dups)}；IoU 均值 {dups.mean():.3f}，中位 {np.median(dups):.3f}，"
      f"IoU>0.95 的比例 {(dups>0.95).mean():.1%}")

# 2) 同 Main-character 内、不同 SubLabel 之间
print("\n=== 同 Main-character 内不同 SubLabel 的相似度 ===")
cross = []
for lab in list(by_label)[:300]:
    imgs = by_label[lab]
    subs = collections.defaultdict(list)
    for n in imgs:
        subs[n.split("/")[2]].append(n)
    keys = list(subs)
    if len(keys) < 2:
        continue
    a = arr(subs[keys[0]][0])
    b = arr(subs[keys[1]][0])
    if a is None or b is None:
        continue
    cross.append(iou(a, b))
cross = np.array(cross)
print(f"  样本 {len(cross)}；IoU 均值 {cross.mean():.3f}，中位 {np.median(cross):.3f}")

# 3) 目标候选 vs 其图像包里的"自己"
print("\n=== 候选 fybnj2savm（󺆑）的图像 ===")
tgt = by_label.get("fybnj2savm", [])
print(f"  图像数 {len(tgt)}: {tgt}")
if tgt:
    a = arr(tgt[0])
    print(f"  归一化后墨量 {a.mean():.3f}")

# 4) 史（h3nw474wwr）的图像数量与内部相似度
print("\n=== 「史」h3nw474wwr 的图像 ===")
sh = by_label.get("h3nw474wwr", [])
print(f"  图像数 {len(sh)}")
subs = collections.Counter(n.split("/")[2] for n in sh)
print(f"  SubLabel 数 {len(subs)}，各含 {list(subs.values())[:12]}")
if tgt and sh:
    a = arr(tgt[0])
    sims = [iou(a, arr(x)) for x in sh[:20] if arr(x) is not None]
    sims = [s for s in sims if s is not None]
    print(f"  与「史」前 20 张的 IoU: 最高 {max(sims):.3f}，均值 {np.mean(sims):.3f}")
