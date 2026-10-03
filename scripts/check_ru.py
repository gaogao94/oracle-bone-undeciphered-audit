# -*- coding: utf-8 -*-
"""检查「以」「入」的用法，以及 󵱙 是否可能为「以」类动词"""
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

TGT = "urzeocieq8"
print("=" * 92)
print(f"目标字 {cp(TGT) or TGT} 的辞例")
print("=" * 92)
for nm, s in sents:
    if TGT in s:
        i = s.index(TGT)
        print(f"  {nm}: " + " ".join("【□】" if k == i else (cp(x) or "◻") for k, x in enumerate(s)))

for ch in ["以", "入", "冊", "目", "峀"]:
    lab = label_of_char.get(ch)
    if not lab:
        print(f"\n【{ch}】不在字表")
        continue
    print("\n" + "=" * 92)
    print(f"【{ch}】label={lab}  出现 {freq[lab]} 次")
    print("=" * 92)
    n = 0
    for nm, s in sents:
        if lab in s and n < 14:
            i = s.index(lab)
            print(f"  {nm}: " + " ".join("【%s】" % ch if k == i else (cp(x) or "◻")
                                          for k, x in enumerate(s)))
            n += 1

# 「入」之前的字分布（谁在做"入"这个动作）
print("\n" + "=" * 92)
print("「入」之前的字（全语料）")
print("=" * 92)
before = collections.Counter()
for nm, s in sents:
    for i, x in enumerate(s):
        if cp(x) == "入" and i > 0:
            before[cp(s[i - 1]) or "◻"] += 1
print(f"  {before.most_common(25)}")

# 「X入」双字辞例的全部收录
print("\n" + "=" * 92)
print("全部「X 入」双字辞例（X = 已释字）")
print("=" * 92)
cnt = collections.Counter()
for nm, s in sents:
    if len(s) == 2 and cp(s[1]) == "入":
        cnt[cp(s[0]) or "◻"] += 1
for k, v in cnt.most_common(20):
    print(f"  {k} 入   ×{v}")
