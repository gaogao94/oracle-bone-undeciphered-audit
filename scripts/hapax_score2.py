# -*- coding: utf-8 -*-
"""
可考性评分 v2（修正版）
修正：
  1) 辞例渲染 bug（原先把所有位置都渲染成 □）；
  2) 邻域可读度只统计【已释且高频】的邻字，空位与匿名邻字不计分；
  3) 增加"有效上下文长度"（已识字个数）作为可解释性指标。
评分维度与对应判据：
  S1 邻域可读度  ← 你的提法「它是在已解释的字中间出现的吗？」
  S2 平行辞例    ← 「同框架、同位由已识字复现」＝异体/借字假设的可检验形式
  S3 框架复现    ← 「出现了有没有规律？」
  S4 偏旁族      ← 「偏旁部首与已释字相关吗？」（待字形数据，本版不计分，仅预留）
  S5 出现次数    ← 辞例证据量
"""
import io, json, math, os, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
OB = os.path.join(D, "obimd")
RES = os.path.join(HERE, "result")

data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
sents = []
for piece in data:
    for grp in piece.get("RecordUtilSentenceGroupVoList") or []:
        seq = sorted(((c.get("OrderNumber") or 0), c.get("Label"))
                     for c in (grp.get("RecordUtilOracleCharVoList") or [])
                     if c.get("Label"))
        lab = [l for _, l in seq]
        if lab:
            sents.append(lab)

freq = collections.Counter()
for s in sents:
    freq.update(s)

cp = lambda l: mc.get(l, {}).get("codepoint") or ""
is_anon = lambda l: (mc.get(l, {}).get("transcription") or []) == []
anon = [l for l in freq if is_anon(l)]
anon_set = set(anon)
decoded = [l for l in freq if not is_anon(l) and cp(l)]
hi_known = {l for l in decoded if freq[l] >= 20}
print(f"字形类 {len(freq):,}｜匿名 {len(anon)}｜已释且有字 {len(decoded):,}｜"
      f"其中 ≥20 次 {len(hi_known)}")

pos = collections.defaultdict(list)
for si, s in enumerate(sents):
    for i, x in enumerate(s):
        if x in anon_set:
            pos[x].append((si, i))

len_idx = collections.defaultdict(list)
for si, s in enumerate(sents):
    len_idx[len(s)].append(si)


def render(s, i):
    return " ".join("□" if k == i else (cp(s[k]) or "◻") for k in range(len(s)))


frames = collections.Counter()
frame_of = {}
for l, occ in pos.items():
    for si, i in occ:
        s = sents[si]
        lo, hi = max(0, i - 2), min(len(s), i + 3)
        toks = tuple(cp(s[k]) or "◻" for k in range(lo, hi))
        frame_of.setdefault(l, toks)
        frames[toks] += 1


def parallel_hits(l):
    out = []
    for si, i in pos[l]:
        s = sents[si]
        for sj in len_idx[len(s)]:
            if sj == si:
                continue
            t = sents[sj]
            ok = True
            for k in range(len(s)):
                if k == i:
                    continue
                if cp(s[k]) != cp(t[k]):
                    ok = False
                    break
            if not ok:
                continue
            sub = t[i]
            if sub in anon_set or not cp(sub) or sub == l:
                continue
            out.append({"substitute": cp(sub), "context": render(s, i)})
            return out
    return out


rows = []
for l in anon:
    occ = pos[l]
    n = len(occ)
    kk = slots = 0
    readable = []
    for si, i in occ:
        s = sents[si]
        for j in (i - 1, i + 1):
            if 0 <= j < len(s):
                slots += 1
                if s[j] in hi_known:
                    kk += 1
        readable.append(sum(1 for k in range(len(s)) if k != i
                            and s[k] in decoded and cp(s[k])))
    s1 = kk / slots if slots else 0.0
    ph_ = parallel_hits(l)
    s2 = min(len(ph_), 3) / 3
    f = frame_of.get(l)
    s3 = min(frames.get(f, 0), 3) / 3 if f else 0.0
    s5 = min(math.log1p(n) / math.log1p(10), 1.0)
    score = 100 * (0.30 * s1 + 0.30 * s2 + 0.10 * s3 + 0.30 * s5)
    rows.append({
        "glyph": cp(l) or l, "label": l, "occurrences": n,
        "neighbor_readability": round(s1, 3),
        "mean_readable_context": round(sum(readable) / len(readable), 2) if readable else 0,
        "parallel_sentences": len(ph_), "frame_repeat": frames.get(f, 0) if f else 0,
        "score": round(score, 1),
        "contexts": [render(sents[si], i) for si, i in occ[:4]],
        "parallel_examples": ph_[:3],
    })

rows.sort(key=lambda r: (-r["score"], -r["occurrences"]))
T = [r for r in rows if r["occurrences"] == 1]

print("\n" + "=" * 86)
print("hapax（仅出现一次，共 %d 个）可考性评分 —— 前 20" % len(T))
print("=" * 86)
print(f"{'字形':>4} {'评分':>5} {'邻域可读':>7} {'可读上下文':>8} {'平行辞例':>7}")
print("-" * 86)
for r in T[:20]:
    print(f"{r['glyph']:>4} {r['score']:>5.1f} {r['neighbor_readability']:>7.2f} "
          f"{r['mean_readable_context']:>8.1f} {r['parallel_sentences']:>7}")

buckets = collections.Counter()
for r in rows:
    buckets["hapax"] += (r["occurrences"] == 1)
print(f"\n分层：评分 ≥45 {sum(1 for r in T if r['score']>=45)}｜"
      f"30–45 {sum(1 for r in T if 30<=r['score']<45)}｜"
      f"<30 {sum(1 for r in T if r['score']<30)}")

print("\n" + "=" * 86)
print("Top 12 hapax 证据明细")
print("=" * 86)
for r in T[:12]:
    print(f"\n■ {r['glyph']}  评分 {r['score']}｜邻域可读 {r['neighbor_readability']}｜"
          f"平均可读上下文 {r['mean_readable_context']} 字｜平行辞例 {r['parallel_sentences']}")
    for c in r["contexts"][:2]:
        print(f"     辞例: {c}")
    for p in r["parallel_examples"][:2]:
        print(f"     平行: {p['context']}  → 同位为已识字「{p['substitute']}」")

json.dump({"n_anon": len(anon), "n_hapax": len(T), "rows": rows},
          open(os.path.join(RES, "hapax_solvability_v2.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n[写出] " + os.path.join(RES, "hapax_solvability_v2.json"))
