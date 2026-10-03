# -*- coding: utf-8 -*-
"""
可考性评分：把 hapax/低频字的"可解 vs 不可解"落成 0-100 分
评分维度（每项都有对应的前人判据）：
  S1 邻域可读度  ——「在已识字中间出现」          → 语境的可用信息量
  S2 平行辞例    ——「同框架同位是已识字」        → 异体/借字假设可检验性
  S3 框架复现    ——「句式有没有规律」            → 套语约束强度
  S4 偏旁族      ——「部首与已识字相关」          → 转写（待字形数据）
  S5 出现次数    —— 辞例证据量
"""
import io, json, os, sys, collections, math
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
hi_known = {l for l in freq if not is_anon(l) and freq[l] >= 20}
anon_set = set(anon)

# 出现位置
pos = collections.defaultdict(list)
for si, s in enumerate(sents):
    for i, x in enumerate(s):
        if is_anon(x):
            pos[x].append((si, i))

# 所有辞例的长度索引（用于平行检验）
len_idx = collections.defaultdict(list)
for si, s in enumerate(sents):
    len_idx[len(s)].append(si)

# 框架统计（±2 字，仅已识字串）
frames = collections.Counter()
frame_of = {}
for l, occ in pos.items():
    for si, i in occ:
        s = sents[si]
        lo, hi = max(0, i - 2), min(len(s), i + 3)
        toks = tuple(cp(s[k]) or "?" for k in range(lo, hi))
        if l not in frame_of:
            frame_of[l] = toks
            frames[toks] += 1


def parallel_hits(l):
    """同长度、逐字相同、同位为已识字、且不是自己"""
    out = []
    for si, i in pos[l]:
        s = sents[si]
        for sj in len_idx[len(s)]:
            t = sents[sj]
            if sj == si:
                continue
            if all(k == i or cp(t[k]) == cp(s[k]) or not cp(s[k]) for k in range(len(s))):
                sub = t[i]
                if sub in anon_set or not cp(sub):
                    continue
                out.append({"substitute": cp(sub),
                            "context": " ".join("□" if k == i else (cp(s[k]) or "?")
                                                for k in range(len(s)))})
                break
    return out


rows = []
for l in anon:
    occ = pos[l]
    n = len(occ)
    # S1 邻域可读度
    kk, slots = 0, 0
    for si, i in occ:
        s = sents[si]
        for j in (i - 1, i + 1):
            if 0 <= j < len(s):
                slots += 1
                if s[j] in hi_known:
                    kk += 1
    s1 = kk / slots if slots else 0
    # S2 平行辞例
    ph_ = parallel_hits(l)
    s2 = min(len(ph_), 3) / 3
    # S3 框架复现
    f = frame_of.get(l)
    s3 = min(frames.get(f, 0), 3) / 3 if f else 0
    # S5 次数
    s5 = min(math.log1p(n) / math.log1p(10), 1.0)

    score = 100 * (0.30 * s1 + 0.30 * s2 + 0.10 * s3 + 0.30 * s5)
    rows.append({
        "glyph": cp(l) or l, "label": l, "occurrences": n,
        "neighbor_readability": round(s1, 3), "parallel_sentences": len(ph_),
        "frame_repeat": frames.get(f, 0) if f else 0,
        "S1": round(s1, 3), "S2": round(s2, 3), "S3": round(s3, 3), "S5": round(s5, 3),
        "score": round(score, 1),
        "parallel_examples": ph_[:4],
        "contexts": [" ".join("□" if (si, i) == o else (cp(x) or "?")
                              for x in sents[si])
                     for o in occ[:5] for si, i in [o]],
    })

rows.sort(key=lambda r: -r["score"])

T = [r for r in rows if r["occurrences"] == 1]
print("=" * 82)
print("hapax（仅出现一次）的「可考性评分」排名 —— 前 25")
print("=" * 82)
print(f"{'字形':>4} {'评分':>5} {'邻域可读':>7} {'平行辞例':>7} {'框架复现':>7}")
print("-" * 82)
for r in T[:25]:
    print(f"{r['glyph']:>4} {r['score']:>5.1f} {r['neighbor_readability']:>7.2f} "
          f"{r['parallel_sentences']:>7} {r['frame_repeat']:>7}")
print(f"\nhapax 总数 {len(T)}")
print(f"  评分 ≥60（有望推进）：{sum(1 for r in T if r['score']>=60)} 个")
print(f"  评分 40–60（需补充证据）：{sum(1 for r in T if 40<=r['score']<60)} 个")
print(f"  评分 <40（当前无解）：{sum(1 for r in T if r['score']<40)} 个")

print("\n" + "=" * 82)
print("Top 10 hapax 的证据明细")
print("=" * 82)
for r in T[:10]:
    print(f"\n■ {r['glyph']}  评分 {r['score']}  (邻域{r['neighbor_readability']}, "
          f"平行辞例{r['parallel_sentences']}, 框架复现{r['frame_repeat']})")
    for c in r["contexts"][:3]:
        print(f"    辞例: {c}")
    for p in r["parallel_examples"][:3]:
        print(f"    平行: {p['context']}  → 同位可替换为「{p['substitute']}」")

json.dump({"rows": rows, "n_anon": len(anon), "n_hapax": len(T),
           "tier": {"ge60": sum(1 for r in T if r["score"] >= 60),
                    "40_60": sum(1 for r in T if 40 <= r["score"] < 60),
                    "lt40": sum(1 for r in T if r["score"] < 40)}},
          open(os.path.join(RES, "hapax_solvability.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n[写出] " + os.path.join(RES, "hapax_solvability.json"))
