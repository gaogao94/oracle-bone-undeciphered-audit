# -*- coding: utf-8 -*-
"""辞例证据：「中」在语料中的用法 vs 未释字的用法"""
import io, json, os, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
cp = lambda l: mc.get(l, {}).get("codepoint") or ""

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
label_of_char = {}
for lab, v in mc.items():
    c = v.get("codepoint") or ""
    if len(c) == 1:
        label_of_char.setdefault(c, lab)

for ch in ["中", "史"]:
    lab = label_of_char.get(ch)
    print("=" * 90)
    print(f"【{ch}】label={lab}  出现 {freq[lab]} 次")
    print("=" * 90)
    for nm, s in sents:
        if lab in s:
            i = s.index(lab)
            print(f"  {nm}: " + " ".join(
                ("【%s】" % ch) if k == i else (cp(x) or "◻") for k, x in enumerate(s)))
    print()

TGT = "fybnj2savm"
print("=" * 90)
print(f"【未释字 fybnj2savm】出现 {freq[TGT]} 次")
print("=" * 90)
for nm, s in sents:
    if TGT in s:
        i = s.index(TGT)
        print(f"  {nm}: " + " ".join(
            "【□】" if k == i else (cp(x) or "◻") for k, x in enumerate(s)))

# 「中」的邻字统计
print("\n" + "=" * 90)
print("「中」的邻字分布")
print("=" * 90)
lc, rc = collections.Counter(), collections.Counter()
for _, s in sents:
    lab = label_of_char.get("中")
    for i, x in enumerate(s):
        if x == lab:
            if i > 0 and cp(s[i - 1]):
                lc[cp(s[i - 1])] += 1
            if i < len(s) - 1 and cp(s[i + 1]):
                rc[cp(s[i + 1])] += 1
print(f"  左邻: {lc.most_common(12)}")
print(f"  右邻: {rc.most_common(12)}")

# 是否有「侯中」或「中侯」类组合
print("\n  含「侯」且含「中」的辞例:")
for nm, s in sents:
    t = [cp(x) for x in s]
    if "侯" in t and "中" in t:
        print(f"    {nm}: " + " ".join(cp(x) or "◻" for x in s))
