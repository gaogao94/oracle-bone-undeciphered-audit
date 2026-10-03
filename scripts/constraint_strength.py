# -*- coding: utf-8 -*-
"""
正确表述的约束力检验
对每个未释字的每个出现位置：
  约束力 = 1 / (能与该位置上下文相容的已释字个数)
只统计「已释字」为可替换集 —— 因为若某位的可替换集只有一个字，
那个字早已被认出，不可能是未释字。
"""
import io, json, os, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
RES = os.path.join(HERE, "result")
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
cp = lambda l: mc.get(l, {}).get("codepoint") or ""
is_anon = lambda l: (mc.get(l, {}).get("transcription") or []) == []

sents = []
for p in data:
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        seq = sorted([c for c in (g.get("RecordUtilOracleCharVoList") or [])
                      if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
        if seq:
            sents.append([c["Label"] for c in seq])

# 已释字在语料中的上下文签名（去掉本字位）
W = 2
sig_of = collections.defaultdict(set)          # 已释字 -> 其所有上下文签名
for L in sents:
    C = [cp(x) or "◻" for x in L]
    n = len(C)
    for i, x in enumerate(L):
        if is_anon(x):
            continue
        lo, hi = max(0, i - W), min(n, i + W + 1)
        win = list(C[lo:hi])
        sig = tuple(t for k, t in enumerate(win) if k != i - lo)
        sig_of[x].add(sig)

# 签名 -> 能产出该签名的已释字集合
sig_to_chars = collections.defaultdict(set)
for ch, sigs in sig_of.items():
    for s in sigs:
        sig_to_chars[s].add(ch)

print("=" * 96)
print("未释字出现位置的「真实约束力」")
print("=" * 96)
print(f"{'未释字':>6}{'次数':>5}{'平均可替换字数':>14}{'最强位置约束力':>14}  最强位置的候选")
rows = []
for x in [l for L in sents for l in L if is_anon(l)]:
    pass
anon_set = {l for L in sents for l in L if is_anon(l)}
for x in anon_set:
    occ = []
    for L in sents:
        C = [cp(y) or "◻" for y in L]
        n = len(C)
        for i, y in enumerate(L):
            if y != x:
                continue
            lo, hi = max(0, i - W), min(n, i + W + 1)
            win = list(C[lo:hi])
            sig = tuple(t for k, t in enumerate(win) if k != i - lo)
            repl = sig_to_chars.get(sig, set())
            occ.append((len(repl), repl, sig))
    if not occ:
        continue
    avg = sum(o[0] for o in occ) / len(occ)
    best = min(occ, key=lambda o: o[0])
    strength = 0.0 if best[0] == 0 else 1.0 / best[0]
    rows.append((best[0], avg, x, best[1], best[2], len(occ)))

rows.sort()
print(f"\n按「最强位置的可替换字数」升序（越少越有约束）—— 前 25")
print("=" * 96)
for nrep, avg, x, repl, sig, nocc in rows[:25]:
    strength = 0.0 if nrep == 0 else 1.0 / nrep
    cand = "、".join(sorted(cp(c) or c for c in repl)[:6]) if repl else "（无已知字吻合）"
    print(f"{cp(x) or x:>6}{nocc:>5}{avg:>14.1f}{strength:>14.3f}  {' '.join(sig)}  → {cand}")

print("\n" + "=" * 96)
print("统计")
print("=" * 96)
n1 = sum(1 for r in rows if r[0] == 1)
n2 = sum(1 for r in rows if r[0] == 2)
n_le3 = sum(1 for r in rows if r[0] <= 3)
print(f"  未释字总数（有位置者）      {len(rows)}")
print(f"  存在某位置可替换字=1 的      {n1}   ← 若为 1，该位置几乎只能是那一个字（但那个字已释，故通常意味着该位是异体或误分）")
print(f"  存在某位置可替换字=2 的      {n2}")
print(f"  存在某位置可替换字≤3 的      {n_le3}")

json.dump([{"glyph": cp(x) or x, "n_occ": nocc, "best_n_rep": nrep, "avg_n_rep": round(avg, 2),
            "best_sig": list(sig), "cands": sorted(cp(c) or c for c in repl)}
           for nrep, avg, x, repl, sig, nocc in rows],
          open(os.path.join(RES, "constraint_strength.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n[写出] result/constraint_strength.json")
