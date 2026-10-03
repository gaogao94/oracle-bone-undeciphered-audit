# -*- coding: utf-8 -*-
"""最终核验：󹥠/󴷨 的「叀 □ 令」——两条独立方法是否同指一字"""
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

print("=" * 94)
print("1) 全语料中所有「叀 X 令」辞例")
print("=" * 94)
for nm, s in sents:
    C = [cp(x) or "◻" for x in s]
    for i in range(len(C) - 2):
        if C[i] == "叀" and C[i + 2] == "令":
            print(f"  {nm}: " + " ".join(C))

print("\n" + "=" * 94)
print("2) 两个未释字的全部辞例")
print("=" * 94)
for lab in ["ytyfg2q0y0", "gcl8bbz6jf", "ahpipvmufk"]:
    if lab not in freq:
        continue
    for nm, s in sents:
        if lab in s:
            C = [cp(x) or "◻" for x in s]
            i = s.index(lab)
            print(f"  [{cp(lab) or lab}] {nm}: " + " ".join("【□】" if k == i else C[k]
                                                          for k in range(len(C))))

# 找出所有「叀 □ 令」的未释字
print("\n" + "=" * 94)
print("3) 「叀 □ 令」中的未释字是谁")
print("=" * 94)
for nm, s in sents:
    C = [cp(x) or "" for x in s]
    for i in range(len(C) - 2):
        if C[i] == "叀" and C[i + 2] == "令":
            lab = s[i + 1]
            tag = "未釋" if (mc.get(lab, {}).get("transcription") or []) == [] else "已釋"
            print(f"  {nm}: 叀 [{cp(lab) or lab}]({tag}) 令   label={lab}  freq={freq[lab]}")

print("\n" + "=" * 94)
print("4) 「畢」的全部辞例与频率")
print("=" * 94)
bl = next((l for l, v in mc.items() if (v.get("codepoint") or "") == "畢"), None)
print(f"  畢 label={bl} freq={freq.get(bl, 0)}")
if bl:
    n = 0
    for nm, s in sents:
        if bl in s and n < 20:
            C = [cp(x) or "◻" for x in s]
            i = s.index(bl)
            print(f"   {nm}: " + " ".join("【畢】" if k == i else C[k] for k in range(len(C))))
            n += 1
