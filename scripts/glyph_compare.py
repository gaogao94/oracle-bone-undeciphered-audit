# -*- coding: utf-8 -*-
"""
字形比对：未释字 vs 假设读法 的参考字形
1) 生成对照接触表 PNG（左：未释字；右：假设读法的各字形）
2) 计算多种归一化图像相似度，作为「形近程度」的机器初筛
   注意：这是初筛，不是判定。形近 ≠ 同字。
"""
import io, json, os, sys, zipfile, collections
from PIL import Image, ImageDraw, ImageFont
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
OB = os.path.join(D, "obimd")
RES = os.path.join(HERE, "result")
IMG = os.path.join(RES, "glyph_images")
os.makedirs(IMG, exist_ok=True)

mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
Z = zipfile.ZipFile(os.path.join(OB, "subchar_images.zip"))
by_label = collections.defaultdict(list)
for n in Z.namelist():
    if n.lower().endswith(".png"):
        p = n.split("/")
        if len(p) >= 4:
            by_label[p[1]].append(n)

label_of_char = {}
for lab, v in mc.items():
    c = (v.get("codepoint") or "")
    if len(c) == 1:
        label_of_char.setdefault(c, lab)


def load_norm(n, h=112):
    im = Image.open(Z.open(n)).convert("L")
    w = max(1, int(im.width * h / max(1, im.height)))
    im = im.resize((w, h), Image.LANCZOS)
    px = list(im.getdata())
    if sum(px) / len(px) < 128:
        im = Image.eval(im, lambda v: 255 - v)
    return im


def binary_grid(im, n=32):
    t = im.point(lambda v: 255 if v < 128 else 0)
    return t.resize((n, n), Image.BOX).point(lambda v: 255 if v > 64 else 0)


def metrics(a, b):
    """三种互补的相似度"""
    A, B = binary_grid(a, 32), binary_grid(b, 32)
    pa, pb = list(A.getdata()), list(B.getdata())
    inter = sum(1 for x, y in zip(pa, pb) if x and y)
    uni = sum(1 for x, y in zip(pa, pb) if x or y)
    iou = inter / uni if uni else 0.0
    # 余弦
    na = sum(1 for x in pa if x)
    nb = sum(1 for y in pb if y)
    cos = inter / ((na * nb) ** 0.5) if na and nb else 0.0
    # 投影轮廓（行/列墨量分布的相似度）
    ra = [sum(1 for k in range(32) if pa[r * 32 + k]) for r in range(32)]
    rb = [sum(1 for k in range(32) if pb[r * 32 + k]) for r in range(32)]
    ca = [sum(1 for r in range(32) if pa[r * 32 + c]) for c in range(32)]
    cb = [sum(1 for r in range(32) if pb[r * 32 + c]) for c in range(32)]

    def cosv(u, v):
        nu = sum(x * x for x in u) ** 0.5
        nv = sum(y * y for y in v) ** 0.5
        return sum(x * y for x, y in zip(u, v)) / (nu * nv) if nu and nv else 0.0
    proj = (cosv(ra, rb) + cosv(ca, cb)) / 2
    return {"iou": round(iou, 4), "cos": round(cos, 4), "proj": round(proj, 4)}


try:
    FONT = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 18)
    FONT_S = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 14)
except Exception:
    FONT = FONT_S = ImageFont.load_default()

solv = json.load(open(os.path.join(RES, "hapax_solvability_v3.json"), encoding="utf-8"))
hypchk = json.load(open(os.path.join(RES, "hypothesis_check.json"), encoding="utf-8"))
hypmap = {h["glyph"]: h for h in hypchk}
cands = [r for r in solv["rows"] if r["occurrences"] == 1 and r["parallel"]]

rows = []
for r in cands:
    lab, g = r["label"], r["glyph"]
    sub = r["parallel"][0]["substitute"]
    own = by_label.get(lab, [])
    ref_lab = label_of_char.get(sub)
    ref = by_label.get(ref_lab, []) if ref_lab else []
    if not own or not ref:
        rows.append({"glyph": g, "substitute": sub, "status": "参考字形缺失",
                     "own_images": len(own), "ref_images": len(ref)})
        continue
    oi = load_norm(own[0])
    sims = [metrics(oi, load_norm(x)) for x in ref[:30]]
    best = max(sims, key=lambda s: s["iou"] + s["cos"] + s["proj"]) if sims else {}
    avg = {k: round(sum(s[k] for s in sims) / len(sims), 4) for k in ("iou", "cos", "proj")} if sims else {}

    # 接触表
    cols = min(9, 1 + len(ref))
    cell = 128
    sheet = Image.new("L", (cols * cell, cell + 34), 255)
    dr = ImageDraw.Draw(sheet)
    o2 = load_norm(own[0], 112)
    sheet.paste(o2, ((cell - o2.width) // 2, (cell - o2.height) // 2))
    dr.text((6, cell + 6), f"UNKNOWN {g}", fill=0, font=FONT_S)
    for i, x in enumerate(ref[:cols - 1]):
        im2 = load_norm(x, 112)
        sheet.paste(im2, (cell * (i + 1) + (cell - im2.width) // 2,
                          (cell - im2.height) // 2))
    dr.text((cell + 6, cell + 6), f"hypothesis: {sub}  ({len(ref)} glyphs)", fill=0, font=FONT_S)
    out = os.path.join(IMG, f"cmp_{lab}.png")
    sheet.save(out)

    rows.append({"glyph": g, "label": lab, "substitute": sub,
                 "own_images": len(own), "ref_images": len(ref),
                 "best": best, "mean": avg,
                 "sheet": os.path.relpath(out, HERE),
                 "verdict": ("高形近" if best.get("iou", 0) >= 0.45 else
                             "中等" if best.get("iou", 0) >= 0.25 else "低形近")})

rows.sort(key=lambda r: -(r.get("best", {}).get("iou", 0) if r.get("best") else 0))
print("=" * 100)
print("字形比对结果（机器初筛，非判定）")
print("=" * 100)
print(f"{'未释字':>4} {'假设读法':<8} {'本字字形':>6} {'参考字形':>6} "
      f"{'IoU最佳':>7} {'余弦最佳':>7} {'投影最佳':>7} {'判定'}")
print("-" * 100)
for r in rows:
    if r.get("status"):
        print(f"{r['glyph']:>4} {r['substitute']:<8} {r['own_images']:>6} "
              f"{r['ref_images']:>6}   {r['status']}")
        continue
    b = r["best"]
    print(f"{r['glyph']:>4} {r['substitute']:<8} {r['own_images']:>6} {r['ref_images']:>6} "
          f"{b['iou']:>7.3f} {b['cos']:>7.3f} {b['proj']:>7.3f}  {r['verdict']}")

n_hi = sum(1 for r in rows if r.get("verdict") == "高形近")
n_mid = sum(1 for r in rows if r.get("verdict") == "中等")
print(f"\n高形近 {n_hi}｜中等 {n_mid}｜低形近 "
      f"{sum(1 for r in rows if r.get('verdict')=='低形近')}")

json.dump(rows, open(os.path.join(RES, "glyph_comparison.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("[写出] result/glyph_comparison.json")
print("[对照图] " + IMG)
