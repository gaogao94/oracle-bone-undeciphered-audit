# -*- coding: utf-8 -*-
"""
诊断：本语料中到底存不存在「强约束框架」？
若存在，说明方法可用、只是目标选错；若不存在，说明问题在语料。
"""
import io, json, os, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
cp = lambda l: mc.get(l, {}).get("codepoint") or ""

sents = []
for p in data:
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        seq = sorted([c for c in (g.get("RecordUtilOracleCharVoList") or [])
                      if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
        if seq:
            sents.append([c["Label"] for c in seq])

# 框架 -> {中心位偏移: 可出现字集合}
frame = collections.defaultdict(lambda: collections.defaultdict(set))
for L in sents:
    C = [cp(x) or "◻" for x in L]
    n = len(C)
    for i in range(n):
        for w in (1, 2, 3):
            lo, hi = max(0, i - w), min(n, i + w + 1)
            key = tuple("□" if k == i else C[k] for k in range(lo, hi))
            frame[key][i - lo].add(L[i])

print("=" * 96)
print("本语料「框架约束力」总体分布")
print("=" * 96)
# 统计：每个框架的中心位可替换字数
dist = collections.Counter()
strong = []
for key, posmap in frame.items():
    for pos, labs in posmap.items():
        if len(key) < 3:
            continue
        n = len(labs)
        b = "1" if n == 1 else "2" if n == 2 else "3-4" if n <= 4 else "5-9" if n <= 9 else "≥10"
        dist[b] += 1
        if n <= 2 and len(key) >= 5:
            strong.append((n, key, pos, [cp(x) or x for x in labs]))
print("  中心位可替换字数的分布（长度≥3 的框架）：")
for k in ["1", "2", "3-4", "5-9", "≥10"]:
    print(f"    {k:>4} 字: {dist.get(k,0):>7,}")

print(f"\n  长度≥5 且中心位只容 ≤2 字的框架（即高约束框架）：{len(strong)} 个")
strong.sort()
for n, key, pos, labs in strong[:25]:
    print(f"    {n} 字  {' '.join(key)}   (可填: {'、'.join(labs[:6])})")

# 其中中心位是未释字的
is_anon = lambda l: (mc.get(l, {}).get("transcription") or []) == []
print("\n" + "=" * 96)
print("高约束框架中，中心位为未释字者（这些才是真正值得下手的目标）")
print("=" * 96)
hits = []
for n, key, pos, labs in strong:
    anon_in = [l for l in labs if is_anon(l)]
    if anon_in:
        hits.append((n, key, pos, labs))
print(f"  共 {len(hits)} 个")
for n, key, pos, labs in hits[:30]:
    print(f"    {n} 字  {' '.join(key)}   候选: {'、'.join(cp(x) or x for x in labs[:5])}")

json.dump({"strong_frames_with_anon": [{"key": list(k), "n_replaceable": n,
                                        "labs": [cp(x) or x for x in ls]}
                                       for n, k, p, ls in hits]},
          open(os.path.join(HERE, "result", "strong_frames.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n[写出] result/strong_frames.json")
