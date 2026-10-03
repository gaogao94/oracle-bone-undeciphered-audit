# -*- coding: utf-8 -*-
"""
最终严格核验：
1) 用四指标法扫描「比侯」槽位的候选字（告等）及全部「侯+□」位置的已释字
2) 对「中」假说作证伪测试：若本字为「中」，其结构是否与「中」的所有变体相容
"""
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


def boxstat(path):
    try:
        im = Image.open(ZS.open(path)).convert("L")
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
    H, W = bb.shape
    rowsum = bb.sum(axis=1)
    wide = np.nonzero(rowsum >= 0.6 * W)[0]
    if len(wide) == 0:
        return None
    return (W / H, wide.min() / H, wide.max() / H, (wide.max() - wide.min() + 1) / H)


TGT = "fybnj2savm"
tst = [boxstat(p) for p in by_label[TGT]]
tst = [s for s in tst if s]
tv = np.mean(tst, axis=0)
print(f"待考字四指标: 宽高比={tv[0]:.3f} 上缘={tv[1]:.3f} 下缘={tv[2]:.3f} 高占比={tv[3]:.3f}")

# 「侯」后接字的所有已释字（从步骤 2 的统计）
HOU_AFTER = ['翦', '屯', '璞', '告', '叶', '歸', '豹', '弗', '其', '佑', '奠', '芻', '印', '及', '昷', '祸', '隹']
CAND = set(HOU_AFTER) | {"告", "中", "史", "冊", "侯", "尹", "史"}

print("\n" + "=" * 88)
print("候選字四指標 vs 待考字（距離 = 四項標準化差之和）")
print("=" * 88)
rows = []
for ch in sorted(CAND):
    lab = label_of_char.get(ch)
    if not lab or lab not in by_label:
        continue
    sts = [boxstat(p) for p in by_label[lab][:10]]
    sts = [s for s in sts if s]
    if not sts:
        continue
    v = np.mean(sts, axis=0)
    d = sum(abs(v[i] - tv[i]) for i in range(4))
    rows.append((d, ch, v, len(sts), freq[lab]))
rows.sort()
print(f"{'字':<6}{'距離':>7}{'宽高比':>9}{'上缘':>8}{'下缘':>8}{'高占比':>8}{'形数':>6}{'语料':>7}")
for d, ch, v, ns, f in rows:
    print(f"{ch:<6}{d:>7.3f}{v[0]:>9.3f}{v[1]:>8.3f}{v[2]:>8.3f}{v[3]:>8.3f}{ns:>6}{f:>7}")

print("\n待考字自身: " + f"{tv[0]:.3f} {tv[1]:.3f} {tv[2]:.3f} {tv[3]:.3f}")

# 结论
print("\n" + "=" * 88)
print("「中」假說的證偽檢驗")
print("=" * 88)
zj = label_of_char.get("中")
if zj:
    # 「中」的全部字形中，有多少在四指標上接近待考字
    close = 0
    tot = 0
    for p in by_label[zj]:
        s = boxstat(p)
        if not s:
            continue
        tot += 1
        d = sum(abs(s[i] - tv[i]) for i in range(4))
        if d < 0.25:
            close += 1
    print(f"  「中」共 {tot} 形；四指標距離 <0.25 的有 {close} 形（{close/tot:.1%}）")
    print(f"  → 若比例高，說明待考字落在「中」的形體變異範圍內；反之則落在範圍外")
