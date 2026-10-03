# -*- coding: utf-8 -*-
"""
核验 9 个 ★★★ 判定：候选字是否在 OBIMD 字表中？
  若在 → 「同一字被分成两类」，需说明
  若不在 → 「OBIMD 未收录该字」，结论不同
同时输出每条的完整辞例供目验
"""
import io, os, sys, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
RES = os.path.join(HERE, "result")
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
cp = lambda l: mc.get(l, {}).get("codepoint") or ""

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

CASES = [("mepmffeebh", "553", "黃"), ("uhz6qrd2d9", "5373", "安"),
         ("󱼮", "32513", "豲"), ("󹧹", "32009", "宓"), ("󾟷", "22454", "丘"),
         ("󲌬", "32512", "豲"), ("󾥗", "17382", "娩"), ("󻫐", "31983", "西"),
         ("󹛟", "33286", "龜")]

print("=" * 100)
print("核验：候选字是否在 OBIMD 字表中")
print("=" * 100)
label_of_glyph = {}
for lab, v in mc.items():
    c = v.get("codepoint") or ""
    if c:
        label_of_glyph[c] = lab

for g, plate, cand in CASES:
    lab = label_of_glyph.get(g)
    kl = label_of_char.get(cand)
    print(f"\n■ OBIMD {g}（label={lab}，{freq.get(lab,0)}次） 片{plate} → 候选「{cand}」")
    if kl:
        print(f"   「{cand}」已在 OBIMD 字表中：label={kl}，出现 {freq.get(kl,0)} 次")
        print(f"   → 若判定成立，则意味着同一字被分为两个字形类，需举证二者为同字异写")
    else:
        print(f"   「{cand}」**不在** OBIMD 字表中 → 结论应为「OBIMD 未收录该字」")
    # 该片的全部 OBIMD 辞例
    for p in data:
        if (p.get("RubbingName") or "").lstrip("H") == plate:
            for gg in p.get("RecordUtilSentenceGroupVoList") or []:
                seq = sorted([c for c in (gg.get("RecordUtilOracleCharVoList") or [])
                              if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
                if seq:
                    s = " ".join(cp(c["Label"]) or "◻" for c in seq)
                    mark = " ←" if any(c["Label"] == lab for c in seq) else ""
                    print(f"      OBIMD: {s}{mark}")
