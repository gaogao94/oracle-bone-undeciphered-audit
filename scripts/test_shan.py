# -*- coding: utf-8 -*-
"""
假设检验：󷺊 = 「彡」（周祭五祀典之一：彡、翌、祭、劦、肜）
检验：
  A) 󷺊 是否总是出现在「日名」或祭名之前（彡日/彡夕 的位置）
  B) 与「夕」的共现率
  C) OBIMD 中是否已有「彡」的字形类
  D) 全《合集》中「彡」的用例格式
"""
import io, os, re, sys, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import gxds2

OB = os.path.join(_HERE, "data", "obimd")
RES = os.path.join(_HERE, "result")
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
cp = lambda l: mc.get(l, {}).get("codepoint") or ""
is_anon = lambda l: (mc.get(l, {}).get("transcription") or []) == []
label_of_char = {}
for lab, v in mc.items():
    c = v.get("codepoint") or ""
    if len(c) == 1:
        label_of_char.setdefault(c, lab)

TGT = "ff8rp0nh6u"
GAN = set("甲乙丙丁戊己庚辛壬癸")
ZHI = set("子丑寅卯辰巳午未申酉戌亥")
RITUAL = set("彡翌祭劦肜夕")

occ = []
for p in data:
    nm = p.get("RubbingName") or ""
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        seq = sorted([c for c in (g.get("RecordUtilOracleCharVoList") or [])
                      if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
        labs = [c["Label"] for c in seq]
        C = [cp(x) or "◻" for x in labs]
        for i, l in enumerate(labs):
            if l == TGT:
                occ.append({"piece": nm, "i": i, "C": C,
                            "group_cat": g.get("GroupCategory")})

print(f"󷺊 共 {len(occ)} 处\n")
print("=" * 100)
print("A) 后邻字分类（彡 应后接日名或祭名）")
print("=" * 100)
after = collections.Counter()
for o in occ:
    C, i = o["C"], o["i"]
    a = C[i + 1] if i + 1 < len(C) else "(句末)"
    after[a] += 1
print(f"  {after.most_common(30)}")
ganzhi_after = sum(v for k, v in after.items() if k in GAN or k in ZHI)
ritual_after = sum(v for k, v in after.items() if k in RITUAL)
print(f"\n  后邻为天干/地支字: {ganzhi_after}/{len(occ)} = {ganzhi_after/len(occ):.0%}")
print(f"  后邻为祭名字:     {ritual_after}/{len(occ)} = {ritual_after/len(occ):.0%}")

print("\n" + "=" * 100)
print("B) 与「夕」的共现")
print("=" * 100)
with_xi = sum(1 for o in occ if "夕" in o["C"])
print(f"  同片辞例含「夕」者: {with_xi}/{len(occ)} = {with_xi/len(occ):.0%}")

print("\n" + "=" * 100)
print("C) OBIMD 是否已有「彡」的字形类")
print("=" * 100)
for ch in ["彡", "肜", "劦", "協", "祭", "翌"]:
    lab = label_of_char.get(ch)
    if lab:
        n = sum(1 for p in data for g in p.get("RecordUtilSentenceGroupVoList") or []
                for c in g.get("RecordUtilOracleCharVoList") or [] if c.get("Label") == lab)
        print(f"  「{ch}」在语料中：label={lab}，{n} 次")
    else:
        print(f"  「{ch}」不在语料字表中")

print("\n" + "=" * 100)
print("D) 前邻字分布")
print("=" * 100)
before = collections.Counter()
for o in occ:
    C, i = o["C"], o["i"]
    before[C[i - 1] if i > 0 else "(句首)"] += 1
print(f"  {before.most_common(25)}")

# 检查「彡」的替代：若 󷺊=彡，则 󷺊 的位置应能替换为彡且成句
print("\n" + "=" * 100)
print("E) 逐条列出：原辞例 vs 填入「彡」")
print("=" * 100)
for o in occ[:40]:
    C, i = o["C"], o["i"]
    new = list(C)
    new[i] = "彡"
    print(f"  {o['piece']}: {' '.join(C)}")
    print(f"      → {' '.join(new)}")

json.dump({"n": len(occ), "after": dict(after), "before": dict(before),
           "ganzhi_after": ganzhi_after, "ritual_after": ritual_after, "with_xi": with_xi},
          open(os.path.join(RES, "shān_hypothesis.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"\n[写出] result/shān_hypothesis.json")
