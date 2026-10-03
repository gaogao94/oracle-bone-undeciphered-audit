# -*- coding: utf-8 -*-
"""
严格判据引擎 v3（索引版，O(n) 查询）
================================================
判据：
  (A) 全上下文覆盖：未释字 X 的每一个出现位置，其「去掉本字位后的窗口」
      必须是某已释字 K 某个出现位置的同样窗口。
  (B) 频率相容：freq(K) ≥ freq(X)。
  (C) 低频优先：只考虑 freq(K) ≤ 60 的已释字。
另外做「同上下文异标签」检验：两个字标签若共享大量上下文，可能是同一字形的不同分类。
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
            sents.append({"piece": nm,
                          "labels": [c["Label"] for c in seq],
                          "chars": [cp(c["Label"]) or "◻" for c in seq]})

freq = collections.Counter()
for s in sents:
    freq.update(s["labels"])
is_anon = lambda l: (mc.get(l, {}).get("transcription") or []) == []
anon = [l for l in freq if is_anon(l)]
decoded = [l for l in freq if not is_anon(l) and cp(l)]
print(f"辞例 {len(sents):,}｜未释 {len(anon)}｜已释 {len(decoded)}")

W = 2          # 左右各 2 字

# ---- 一次遍历，建两个索引 ----
# key_without : 去掉本字位后的窗口元组 -> 产出它的字标签集合
# ctx_of      : 字标签 -> 其每个出现位置的窗口（含 □）
key_to_labels = collections.defaultdict(set)
ctx_of = collections.defaultdict(list)
for s in sents:
    L, C = s["labels"], s["chars"]
    n = len(C)
    for i, x in enumerate(L):
        lo, hi = max(0, i - W), min(n, i + W + 1)
        win = list(C[lo:hi])
        key = tuple(t for k, t in enumerate(win) if k != i - lo)
        key_to_labels[key].add(x)
        ctx_of[x].append(tuple("□" if k == i else C[k] for k in range(lo, hi)))

print(f"窗口种类 {len(key_to_labels):,}")

# ---- 判据 A+B+C ----
LOWK = {k for k in decoded if freq[k] <= 60}
print(f"低频已释字池（≤60 次）: {len(LOWK)}")

results = []
for x in anon:
    wins = ctx_of.get(x, [])
    if not wins:
        continue
    keys = [tuple(t for k, t in enumerate(w) if t != "□") for w in wins]
    # 每个 key 的候选标签交集
    common = None
    for kk in keys:
        s = key_to_labels.get(kk, set())
        common = set(s) if common is None else (common & s)
        if not common:
            break
    if not common:
        continue
    cands = [k for k in common if k != x and freq[k] >= freq[x] and k in LOWK]
    if cands:
        cands.sort(key=lambda k: freq[k])
        results.append({"label": x, "glyph": cp(x) or x, "freq": freq[x],
                        "n_ctx": len(wins),
                        "cands": [{"char": cp(k), "label": k, "k_freq": freq[k]} for k in cands[:6]]})

results.sort(key=lambda r: (-r["n_ctx"], r["freq"]))
print("\n" + "=" * 100)
print(f"通过「全上下文覆盖 + 低频候选」的未释字: {len(results)} 个")
print("=" * 100)
for r in results[:30]:
    cs = ", ".join(f"{c['char']}({c['k_freq']})" for c in r["cands"])
    print(f"  {r['glyph']:>3}  freq={r['freq']}  ctx={r['n_ctx']}  →  {cs}")

json.dump(results, open(os.path.join(RES, "strict_v3.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---- 同上下文异标签 ----
print("\n" + "=" * 100)
print("同上下文异标签检验")
print("=" * 100)
pos_key = collections.defaultdict(set)
for s in sents:
    L, C = s["labels"], s["chars"]
    n = len(C)
    for i, x in enumerate(L):
        lo, hi = max(0, i - W), min(n, i + W + 1)
        win = list(C[lo:hi])
        key = tuple(t for k, t in enumerate(win) if k != i - lo)
        pos_key[key].add(x)
pairs = collections.Counter()
for key, ls in pos_key.items():
    if len(ls) > 1:
        L = sorted(ls)
        for i in range(len(L)):
            for j in range(i + 1, len(L)):
                pairs[(L[i], L[j])] += 1
anonS = set(anon)
rows = []
for (a, b), n in pairs.most_common(300):
    if (a in anonS) or (b in anonS):
        rows.append({"a": cp(a) or a, "b": cp(b) or b, "n": n,
                     "a_anon": a in anonS, "b_anon": b in anonS,
                     "a_freq": freq[a], "b_freq": freq[b]})
print(f"涉及未释字的共享上下文对: {len(rows)}")
for r in rows[:25]:
    print(f"  {r['a']}({r['a_freq']}) × {r['b']}({r['b_freq']})  共享 {r['n']} 个上下文")
json.dump(rows, open(os.path.join(RES, "shared_ctx_anon.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n[写出] result/strict_v3.json, result/shared_ctx_anon.json")
