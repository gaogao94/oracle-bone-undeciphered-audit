# -*- coding: utf-8 -*-
"""
致命核查：候选字若已是甲骨文常用字，OBIMD 语料里是否已有该字的字形类？
若已有，则未释字 = 该字的假设意味着「同一字被分成两类」，需要额外论证。
"""
import io, json, os, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
cp = lambda l: mc.get(l, {}).get("codepoint") or ""
freq = collections.Counter()
for p in data:
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        for c in g.get("RecordUtilOracleCharVoList") or []:
            if c.get("Label"):
                freq[c["Label"]] += 1
label_of_char = {}
for lab, v in mc.items():
    c = v.get("codepoint") or ""
    if len(c) == 1:
        label_of_char.setdefault(c, lab)

print("=" * 90)
print("候选字在 OBIMD 语料中的既有字形类")
print("=" * 90)
for ch in ["禾", "殺", "雀", "其", "今", "新", "轡", "琡", "告", "中"]:
    lab = label_of_char.get(ch)
    if lab:
        print(f"  「{ch}」已在語料中：label={lab}  出現 {freq[lab]} 次")
    else:
        print(f"  「{ch}」不在語料字表中")

print("\n" + "=" * 90)
print("三个保留候选的资格判断")
print("=" * 90)
for ch, zg in [("禾", 20), ("殺", 0), ("雀", 40)]:
    lab = label_of_char.get(ch)
    in_obimd = lab is not None
    print(f"\n【{ch}】")
    print(f"  該字在《合集》等甲骨著錄中的用例數：{zg}")
    print(f"  該字是否已存在於 OBIMD 語料：{'是，'+str(freq.get(lab,0))+'次' if in_obimd else '否'}")
    if zg == 0:
        print(f"  → ❌ 該字無甲骨文用例，不能作為甲骨文未釋字的候選")
    elif not in_obimd:
        print(f"  → ⚠ 該字有甲骨文用例，但本語料未收其字形類；可能是採樣缺失，需查")
    else:
        print(f"  → ⚠ 該字在本語料已有字形類。若未釋字即該字，則意味著同一字被分為兩類，")
        print(f"     需舉證：該未釋字形與既有字形類是否為同一字的不同寫法")
