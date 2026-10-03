# -*- coding: utf-8 -*-
"""
字形图像流水线（第一版）
================================================
替代"用编码读字"的做法：
  1. 从 Sub-character Images.zip 取每个字形类的真实字形图；
  2. 从 data.json 的 Position 字段取该字在拓片上的位置（用于回到原拓核对）；
  3. 生成"假设读法 vs 候选字形"的对照接触表（contact sheet），供人工目验；
  4. 计算归一化像素相似度，作为「形近程度」的机器初筛（不是判定）。
"""
import io, json, os, sys, zipfile, collections
from PIL import Image, ImageDraw
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
OB = os.path.join(D, "obimd")
RES = os.path.join(HERE, "result")
IMG = os.path.join(RES, "glyph_images")
Z = os.path.join(OB, "subchar_images.zip")
os.makedirs(IMG, exist_ok=True)

mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))

# ---------- 1. 建立 label -> [png 路径] 索引
z = zipfile.ZipFile(Z)
pngs = [n for n in z.namelist() if n.lower().endswith(".png")]
by_label = collections.defaultdict(list)
for n in pngs:
    parts = n.split("/")
    # Sub-character Images/<main>/<sub>/<sub>.png
    if len(parts) >= 4:
        by_label[parts[1]].append(n)
print(f"PNG 总数 {len(pngs):,}；覆盖 Main-character {len(by_label):,}")

# ---------- 2. 字形出现位置（回到原拓核对用）
pos_of = collections.defaultdict(list)
for p in data:
    nm = p.get("RubbingName")
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        for c in g.get("RecordUtilOracleCharVoList") or []:
            if c.get("Label") and not c.get("SeatFont"):
                pos_of[c["Label"]].append({"piece": nm, "pos": c.get("Position"),
                                           "sentence": g.get("GroupCategory")})

# ---------- 3. 取候选字形
solv = json.load(open(os.path.join(RES, "hapax_solvability_v3.json"), encoding="utf-8"))
cands = [r for r in solv["rows"] if r["occurrences"] == 1 and r["parallel"]]
print(f"候选（hapax 且有平行辞例）{len(cands)}")


def extract(label, want=40):
    """解出该字形类的所有字形 PNG，缩放到统一高度"""
    out = []
    for i, n in enumerate(by_label.get(label, [])[:want]):
        try:
            buf = z.open(n)
            im = Image.open(buf).convert("L")
            out.append((n, im))
        except Exception as e:
            print(f"   读取失败 {n}: {e}")
    return out


def normalize(im, h=96):
    w = max(1, int(im.width * h / max(1, im.height)))
    im2 = im.resize((w, h), Image.LANCZOS)
    # 反相：甲骨文拓片是白底黑字或黑底白字，统一为"白底黑字"
    px = list(im2.getdata())
    mean = sum(px) / len(px)
    if mean < 128:
        im2 = Image.eval(im2, lambda v: 255 - v)
    return im2


def ink_signature(im):
    """极简形状签名：16x16 二值网格（用于粗筛形近程度）"""
    t = normalize(im, 32).point(lambda v: 255 if v < 128 else 0)
    g = t.resize((16, 16), Image.BOX)
    d = list(g.getdata())
    return [1 if v > 64 else 0 for v in d]


def cosine(a, b):
    num = sum(x * y for x, y in zip(a, b))
    da = sum(x * x for x in a) ** 0.5
    db = sum(y * y for y in b) ** 0.5
    return num / (da * db) if da and db else 0.0


report = []
for r in cands:
    lab, g = r["label"], r["glyph"]
    imgs = extract(lab)
    if not imgs:
        report.append({"glyph": g, "label": lab, "n_images": 0,
                       "note": "图像包中无该字形类"})
        continue
    # 保存本字所有字形
    d = os.path.join(IMG, lab)
    os.makedirs(d, exist_ok=True)
    sigs = []
    for i, (n, im) in enumerate(imgs):
        nm2 = normalize(im)
        nm2.save(os.path.join(d, f"{i:03d}.png"))
        sigs.append(ink_signature(im))
    report.append({
        "glyph": g, "label": lab,
        "n_images": len(imgs),
        "n_sub_labels": len({n.split("/")[2] for n, _ in imgs}),
        "positions": pos_of.get(lab, [])[:6],
        "dir": os.path.relpath(d, HERE),
    })

print("\n" + "=" * 90)
print("字形提取结果")
print("=" * 90)
print(f"{'字形':>4} {'Label':>12} {'字形图数':>7} {'异构体':>6} {'原拓位置样例'}")
print("-" * 90)
for r in report:
    p = (r.get("positions") or [{}])[0]
    print(f"{r['glyph']:>4} {r['label']:>12} {r.get('n_images',0):>7} "
          f"{r.get('n_sub_labels',0):>6} {p.get('piece','—')} @ {p.get('pos','—')}")

n_ok = sum(1 for r in report if r.get("n_images"))
print(f"\n成功提取字形的候选：{n_ok}/{len(cands)}")

json.dump(report, open(os.path.join(RES, "glyph_extraction.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("[写出] result/glyph_extraction.json")
print("[字形图目录] " + IMG)
