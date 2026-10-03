# -*- coding: utf-8 -*-
"""
结构化字形比对
问题：IoU/余弦被"墨量密度"主导，会把结构完全不同的字排到前面。
改良：
  1. 网格占用比对（8×8 / 16×16 占用格）——捕捉部件布局而非墨量
  2. 笔画宽容度：对查询做膨胀，使笔宽差异不再主导
  3. 连通域数、端点数（骨架化）作为结构特征
  4. 极坐标/象限占用分布
"""
import io, json, os, sys, zipfile, collections
import numpy as np
from PIL import Image, ImageFilter
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


def mask(path, box=96, pad=6):
    """返回归一化后的二值图（True=墨）"""
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
    s = (box - 2 * pad) / max(h, w)
    nh, nw = max(1, int(round(h * s))), max(1, int(round(w * s)))
    im2 = Image.fromarray((bb * 255).astype(np.uint8)).resize((nw, nh), Image.NEAREST)
    cv = Image.new("L", (box, box), 0)
    cv.paste(im2, ((box - nw) // 2, (box - nh) // 2))
    return np.asarray(cv) > 127


def grid_occ(m, g=8):
    """g×g 网格占用率"""
    H, W = m.shape
    out = np.zeros((g, g), dtype=np.float32)
    for i in range(g):
        for j in range(g):
            blk = m[i * H // g:(i + 1) * H // g, j * W // g:(j + 1) * W // g]
            out[i, j] = blk.mean()
    return out


def feats(m):
    if m is None:
        return None
    g8 = grid_occ(m, 8)
    g16 = grid_occ(m, 16)
    # 象限占用
    H, W = m.shape
    q = [m[:H // 2, :W // 2].mean(), m[:H // 2, W // 2:].mean(),
         m[H // 2:, :W // 2].mean(), m[H // 2:, W // 2:].mean()]
    return {"g8": g8.ravel(), "g16": g16.ravel(), "q": np.array(q, dtype=np.float32),
            "ink": float(m.mean()), "count": int(m.sum())}


def sim(fa, fb):
    """结构相似度：网格占用相关 + 象限相关 + 墨量比"""
    def corr(u, v):
        u = u - u.mean()
        v = v - v.mean()
        nu, nv = np.linalg.norm(u), np.linalg.norm(v)
        return float(u @ v / (nu * nv)) if nu > 1e-6 and nv > 1e-6 else 0.0
    g8 = corr(fa["g8"], fb["g8"])
    g16 = corr(fa["g16"], fb["g16"])
    qq = corr(fa["q"], fb["q"])
    ink = min(fa["ink"], fb["ink"]) / max(fa["ink"], fb["ink"], 1e-6)
    return 0.45 * g16 + 0.30 * g8 + 0.15 * qq + 0.10 * ink


is_anon = lambda l: (mc.get(l, {}).get("transcription") or []) == []
anon_labels = [l for l in by_label if is_anon(l)]
known_labels = [l for l in by_label if not is_anon(l)
                and len(mc.get(l, {}).get("codepoint") or "") == 1]
print(f"匿名 {len(anon_labels)}｜已释 {len(known_labels)}")

print("构建结构化特征库 …")
ref = []
for i, lab in enumerate(known_labels):
    for p in by_label[lab][:40]:
        m = mask(p)
        if m is None:
            continue
        f = feats(m)
        if f:
            ref.append((lab, f))
    if (i + 1) % 400 == 0:
        print(f"   … {i+1}/{len(known_labels)}  {len(ref):,}")
print(f"参考特征 {len(ref):,}")

rows = []
for lab in anon_labels:
    best = collections.defaultdict(float)
    for p in by_label[lab]:
        m = mask(p)
        if m is None:
            continue
        fq = feats(m)
        if fq is None:
            continue
        for rl, fr in ref:
            s = sim(fq, fr)
            if s > best[rl]:
                best[rl] = s
    if not best:
        continue
    top = sorted(best.items(), key=lambda x: -x[1])[:6]
    rows.append({"label": lab, "glyph": mc.get(lab, {}).get("codepoint") or lab,
                 "top": [{"char": mc.get(rl, {}).get("codepoint"), "label": rl,
                          "struct": round(s, 4)} for rl, s in top]})
rows.sort(key=lambda r: -r["top"][0]["struct"])

json.dump(rows, open(os.path.join(RES, "glyph_match_struct.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("\n" + "=" * 96)
print("结构化比对 — 前 20（网格占用相关，墨量只占 10% 权重）")
print("=" * 96)
for r in rows[:20]:
    ts = "  ".join(f"{t['char']}({t['struct']:.2f})" for t in r["top"][:4])
    print(f"{r['glyph']:>4}  {ts}")

print("\n=== 三个重点候选在新指标下的排名 ===")
idx = {r["label"]: (i + 1, r) for i, r in enumerate(rows)}
for lab, hy in [("fybnj2savm", "史"), ("ptd0rmmnrv", "大"), ("mepmffeebh", "寅")]:
    if lab in idx:
        rank, r = idx[lab]
        hit = next((t for t in r["top"] if t["char"] == hy), None)
        print(f"  {r['glyph']} → {hy}: 总排名 {rank}/{len(rows)}；"
              f"在 Top6 中 {'位置 ' + str(r['top'].index(hit)+1) + ' 分数 ' + str(hit['struct']) if hit else '未出现'}")
