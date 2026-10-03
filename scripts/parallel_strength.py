# -*- coding: utf-8 -*-
"""
量化「平行辞例」这一判据的真实证据力
方法：对每条平行辞例，统计其框架在全语料中出现次数、以及该位置有多少种不同的字。
      框架越常见、可替换字越多 → 证据力越低（近乎零）。
"""
import io, json, os, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
RES = os.path.join(HERE, "result")
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

# 框架索引：对每个长度≥3 的串，取以某位置为中心的 ±2 窗口
frame_pos = collections.defaultdict(lambda: collections.defaultdict(set))
for nm, L in sents:
    C = [cp(x) or "◻" for x in L]
    n = len(C)
    for i in range(n):
        lo, hi = max(0, i - 2), min(n, i + 3)
        key = tuple("□" if k == i else C[k] for k in range(lo, hi))
        frame_pos[key][i - lo].add(L[i])

print("=" * 100)
print("对「平行辞例」判据的强度量化")
print("=" * 100)
print("检验对象：第 3 轮 strict 平行辞例得到的候选（框架 + 同位候选字）")

# 取第 3 轮的核心表
try:
    hp = json.load(open(os.path.join(RES, "hapax_solvability_v3.json"), encoding="utf-8"))
except Exception:
    hp = {"rows": []}

rows = [r for r in hp.get("rows", []) if r.get("occurrences") == 1 and r.get("parallel")]
print(f"共 {len(rows)} 条\n")
print(f"{'未释字':>5}{'候选字':>7}{'框架全语料出现':>14}{'该位可替换字数':>14}{'证据力':>8}")
out = []
for r in rows:
    p0 = r["parallel"][0]
    ctx = p0["context"]
    toks = ctx.split()
    if "□" not in toks:
        continue
    j = toks.index("□")
    # 还原该位置的中心索引：需要重新在语料里找
    key = tuple(toks)
    # 该框架的可替换字（用中心位反推 —— frame_pos 的 key 是用中心位标 □ 的）
    rep = set()
    total = 0
    for k, posmap in frame_pos.items():
        if len(k) != len(key):
            continue
        if all((k[idx] == key[idx]) for idx in range(len(key)) if idx != j):
            for pos, labs in posmap.items():
                rep |= labs
            total += 1
    n_rep = len(rep)
    strength = 0.0 if n_rep <= 1 else round(1.0 / n_rep, 3)
    print(f"{r['glyph']:>5}{p0['substitute']:>7}{total:>14}{n_rep:>14}{strength:>8.3f}")
    out.append({"glyph": r["glyph"], "cand": p0["substitute"], "frame_total": total,
                "n_replaceable": n_rep, "strength": strength})

print("\n" + "=" * 100)
print("结论")
print("=" * 100)
strong = [o for o in out if o["strength"] >= 0.5]
weak = [o for o in out if o["strength"] < 0.2]
print(f"  证据力 ≥0.5（该位只容 1–2 字）：{len(strong)} 条")
for o in strong:
    print(f"     {o['glyph']} → {o['cand']}  该位可替换字 {o['n_replaceable']} 个")
print(f"  证据力 <0.2（该位可容 5 字以上）：{len(weak)} 条 ← 近乎无约束")
json.dump(out, open(os.path.join(RES, "parallel_strength.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n[写出] result/parallel_strength.json")
