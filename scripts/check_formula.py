# -*- coding: utf-8 -*-
"""关键核查：「王比侯」后接什么？「贞用」后接什么？——直接检验「中」的读法"""
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
            sents.append((nm, [cp(c["Label"]) or "◻" for c in seq]))

TGT = "fybnj2savm"
lab2c = {l: (v.get("codepoint") or "") for l, v in mc.items()}

# 1) 「比侯」的所有出现
print("=" * 92)
print("1) 含「比 侯」的辞例")
print("=" * 92)
n = 0
for nm, s in sents:
    for i in range(len(s) - 1):
        if s[i] == "比" and s[i + 1] == "侯":
            n += 1
            print(f"  {nm}: " + " ".join(s))
print(f"  共 {n} 例")

# 2) 「侯」后接字的分布
print("\n" + "=" * 92)
print("2) 「侯」之后接什么字（全语料）")
print("=" * 92)
after = collections.Counter()
for nm, s in sents:
    for i, x in enumerate(s):
        if x == "侯" and i + 1 < len(s):
            after[s[i + 1]] += 1
print(f"  {after.most_common(20)}")

# 3) 「貞 用」后接字
print("\n" + "=" * 92)
print("3) 「貞 用」之后接什么字")
print("=" * 92)
after2 = collections.Counter()
for nm, s in sents:
    for i in range(len(s) - 1):
        if s[i] == "貞" and s[i + 1] == "用" and i + 2 < len(s):
            after2[s[i + 2]] += 1
print(f"  {after2.most_common(15)}")

# 4) 「用」之前接什么（看「贞用X」是否为固定格式）
print("\n" + "=" * 92)
print("4) 「用」之前的字")
print("=" * 92)
before = collections.Counter()
for nm, s in sents:
    for i, x in enumerate(s):
        if x == "用" and i > 0:
            before[s[i - 1]] += 1
print(f"  {before.most_common(20)}")

# 5) 「王比」的所有出现
print("\n" + "=" * 92)
print("5) 含「王 比」的辞例")
print("=" * 92)
n2 = 0
for nm, s in sents:
    for i in range(len(s) - 1):
        if s[i] == "王" and s[i + 1] == "比":
            n2 += 1
            print(f"  {nm}: " + " ".join(s))
print(f"  共 {n2} 例")
