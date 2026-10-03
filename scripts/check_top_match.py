# -*- coding: utf-8 -*-
"""
对图像检索出的头号命中进行语料与字表核查
核查项：
  A. 该未释字在语料中的全部辞例（是否与「史」的用法相符）
  B. 「史」本身是否已存在于字表中（若存在，说明这是异体而非新字）
  C. 该未释字是否与「史」出现在相同的句式框架中
  D. 其他候选（中/貯/余）的排除理由
"""
import io, json, os, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
OB = os.path.join(D, "obimd")
RES = os.path.join(HERE, "result")

mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
sents = []
for piece in data:
    nm = piece.get("RubbingName")
    for g in piece.get("RecordUtilSentenceGroupVoList") or []:
        seq = sorted(((c.get("OrderNumber") or 0), c.get("Label"))
                     for c in (g.get("RecordUtilOracleCharVoList") or [])
                     if c.get("Label"))
        lab = [l for _, l in seq]
        if lab:
            sents.append((nm, lab))

freq = collections.Counter()
for _, s in sents:
    freq.update(s)
cp = lambda l: mc.get(l, {}).get("codepoint") or ""
is_anon = lambda l: (mc.get(l, {}).get("transcription") or []) == []


def label_of_char(ch):
    for lab, v in mc.items():
        if (v.get("codepoint") or "") == ch:
            return lab
    return None


TARGET = "fybnj2savm"      # 图像检索头号命中：󺆑 ≈ 史
CANDIDATES = ["史", "中", "貯", "余"]

print("=" * 84)
print(f"A. 未释字 {cp(TARGET)}（label={TARGET}）的全部辞例")
print("=" * 84)
print(f"  在语料中出现 {freq[TARGET]} 次")
for nm, s in sents:
    if TARGET in s:
        print(f"   片 {nm}: " + " ".join("□" if l == TARGET else (cp(l) or "◻") for l in s))

print("\n" + "=" * 84)
print("B. 候选字本身是否已在字表中")
print("=" * 84)
for ch in CANDIDATES:
    lab = label_of_char(ch)
    if lab:
        n = freq.get(lab, 0)
        print(f"  「{ch}」已存在，label={lab}，语料中出现 {n} 次，"
              f"字形图 {len(os.listdir(os.path.join(RES,'glyph_match'))) if False else ''}")
    else:
        print(f"  「{ch}」不在 OBIMD 字表中")

print("\n" + "=" * 84)
print("C. 未释字与候选字的句式框架对比")
print("=" * 84)


def frames_of(lab, w=2):
    out = collections.Counter()
    for nm, s in sents:
        n = len(s)
        for i, x in enumerate(s):
            if x == lab:
                lo, hi = max(0, i - w), min(n, i + w + 1)
                out[tuple(cp(s[k]) or "◻" if k != i else "□" for k in range(lo, hi))] += 1
    return out


ft = frames_of(TARGET)
print(f"  未释字 {cp(TARGET)} 的框架（{len(ft)} 种）:")
for f, v in ft.most_common(8):
    print(f"    {v}×  {' '.join(f)}")

for ch in CANDIDATES:
    lab = label_of_char(ch)
    if not lab:
        continue
    fk = frames_of(lab)
    print(f"\n  「{ch}」的框架（共 {len(fk)} 种，语料 {freq[lab]} 次），前 8:")
    for f, v in fk.most_common(8):
        print(f"    {v:>4}×  {' '.join(f)}")

print("\n" + "=" * 84)
print("D. 结论要点")
print("=" * 84)
print(f"  · 未释字仅出现 {freq[TARGET]} 次，无法用辞例统计区分候选")
print(f"  · 「史」在语料中出现 {freq.get(label_of_char('史'), 0)} 次，"
      f"框架种类 {len(frames_of(label_of_char('史')))}")
print("  · 因此判定必须依赖字形：图像相似度 史=0.822，次名 中=0.622，差距显著")
print("  · 但「同构字形」仍需人眼确认笔画连接方式，机器不能替代")
