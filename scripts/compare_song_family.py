# -*- coding: utf-8 -*-
"""穷尽比对：未释字 gx21ndp7yy 与「宀部」「木部」全部字的逐形相似度"""
import io, json, os, sys, zipfile, collections
import numpy as np
from PIL import Image
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
ZS = zipfile.ZipFile(os.path.join(OB, "subchar_images.zip"))
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
cp = lambda l: mc.get(l, {}).get("codepoint") or ""

by_label = collections.defaultdict(list)
for n in ZS.namelist():
    if n.lower().endswith(".png"):
        p = n.split("/")
        if len(p) >= 4:
            by_label[p[1]].append(n)
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

B = 64


def mk(path):
    im = Image.open(ZS.open(path)).convert("L")
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
    box, pad = 96, 8
    s = (box - 2 * pad) / max(h, w)
    nh, nw = max(1, int(round(h * s))), max(1, int(round(w * s)))
    im2 = Image.fromarray((bb * 255).astype(np.uint8)).resize((nw, nh), Image.NEAREST)
    cv = Image.new("L", (box, box), 0)
    cv.paste(im2, ((box - nw) // 2, (box - nh) // 2))
    m = np.asarray(cv) > 127
    return m


def profile(m, nrows=4, ncols=8):
    """把字形分成 nrows×ncols 块，返回每块的占用率（结构布局，与墨量弱相关）"""
    H, W = m.shape
    out = np.zeros((nrows, ncols), dtype=np.float32)
    for i in range(nrows):
        for j in range(ncols):
            blk = m[i * H // nrows:(i + 1) * H // nrows,
                    j * W // ncols:(j + 1) * W // ncols]
            out[i, j] = blk.mean() if blk.size else 0
    return out


def sym(m):
    """左右对称度"""
    return 1.0 - float(np.abs(m.astype(float) - m[:, ::-1].astype(float)).mean())


def rowshape(m, k=5):
    """每行墨迹的水平跨度（捕捉 屋顶/横梁/两足 的轮廓）"""
    H = m.shape[0]
    out = []
    for i in range(k):
        seg = m[i * H // k:(i + 1) * H // k]
        if seg.sum() == 0:
            out.append(np.zeros(16, dtype=np.float32))
            continue
        col = seg.sum(axis=0).astype(np.float32)
        col = col / col.max()
        idx = np.linspace(0, len(col) - 1, 16).astype(int)
        out.append(col[idx])
    return out


TGT = "gx21ndp7yy"
tgt = [mk(p) for p in by_label[TGT]]
tgt = [m for m in tgt if m is not None]
tp = [profile(m) for m in tgt]
tr = [rowshape(m) for m in tgt]
print(f"目标 {TGT}: {len(tgt)} 形")
print("  左右对称度:", [f"{sym(m):.3f}" for m in tgt])
for i, r in enumerate(tr[0]):
    print(f"  行{i+1} 跨度: {np.round(r,2)}")

# 特殊候选集：宀部与木部的字
SPECIAL = {"宋", "宗", "室", "安", "宀", "木", "定", "宣", "宮", "寢", "宅", "宕", "家", "宓",
           "官", "守", "宜", "相", "李", "朱", "株", "束", "東", "本", "末", "未", "果", "樂",
           "乘", "桑", "柏", "楚", "林", "森", "杏", "杕", "欒", "甯", "崇", "祀", "示"}
pool = collections.defaultdict(list)
for ch in SPECIAL:
    lab = label_of_char.get(ch)
    if lab:
        pool[ch] = [mk(p) for p in by_label[lab][:20]]
        pool[ch] = [m for m in pool[ch] if m is not None]
print(f"\n特殊候选池: {[(k, len(v)) for k, v in pool.items() if v]}")


def sim(a, b):
    pa, pb = profile(a), profile(b)
    u, v = pa.ravel() - pa.mean(), pb.ravel() - pb.mean()
    nu, nv = np.linalg.norm(u), np.linalg.norm(v)
    pc = float(u @ v / (nu * nv)) if nu > 1e-6 and nv > 1e-6 else 0
    ra, rb = rowshape(a), rowshape(b)
    rs = np.mean([float(x @ y / (np.linalg.norm(x) * np.linalg.norm(y) + 1e-9))
                  for x, y in zip(ra, rb)])
    sa, sb = sym(a), sym(b)
    return 0.45 * pc + 0.35 * rs + 0.20 * (1 - abs(sa - sb))


print("\n" + "=" * 70)
print("与特殊候选池的相似度（取每字最高）")
print("=" * 70)
res = []
for ch, ms in pool.items():
    if not ms:
        continue
    best = max(sim(t, m) for t in tgt for m in ms)
    res.append((best, ch, len(ms), freq.get(label_of_char[ch], 0)))
res.sort(reverse=True)
for s, ch, n, f in res:
    print(f"  {ch}  相似度 {s:.4f}  字形 {n} 个  语料出现 {f} 次")
