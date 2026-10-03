# -*- coding: utf-8 -*-
"""核查最强约束的槽位句法角色：我㚔X / 比侯X / 卜角獲X"""
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

for kw in ["我", "㚔", "角", "獲"]:
    print("=" * 94)
    print(f"全语料含「{kw}」的辞例（前 20）")
    print("=" * 94)
    n = 0
    for nm, s in sents:
        C = [cp(x) or "◻" for x in s]
        if kw in C and n < 20:
            print(f"  {nm}: " + " ".join(C))
            n += 1
    print()

print("=" * 94)
print("「我 X」 的所有搭配（X = 我后第一个字）")
print("=" * 94)
cnt = collections.Counter()
for nm, s in sents:
    C = [cp(x) or "" for x in s]
    for i, x in enumerate(C):
        if x == "我" and i + 1 < len(C):
            cnt[C[i + 1] or "◻"] += 1
print("  ", cnt.most_common(20))
