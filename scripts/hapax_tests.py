# -*- coding: utf-8 -*-
"""
hapax（仅出现一次）字形的可考性检验
================================================
针对三个提法逐一做可证伪的检验：
  H1「出现了有没有规律？」      → 槽位/句式规律性检验
  H2「它是在已解释的字中间出现的吗？」→ 邻域可读度检验
  H3「偏旁部首和已解释的字有相关性吗？」→ 部首共享检验
再加两个：
  H4 复现检验：某 hapax 的完整上下文是否与另一已识字完全相同（异体/借字假设）
  H5 包围检验：左右邻皆为高频已识字 → 即便只出现一次，语境仍然高度受限
"""
import io, json, os, sys, collections, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
OB = os.path.join(D, "obimd")
RES = os.path.join(HERE, "result")
os.makedirs(RES, exist_ok=True)

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
hapax = [l for l in anon if freq[l] == 1]
rare2 = [l for l in anon if freq[l] == 2]
print(f"字形类 {len(freq):,}｜匿名 {len(anon)}｜hapax {len(hapax)}｜出现2次 {len(rare2)}")

# 高频已识字（用作"可读邻域"的参照）
hi_known = {l for l in freq if not is_anon(l) and freq[l] >= 20}
print(f"高频已识字（≥20次）{len(hi_known)} 个，覆盖 "
      f"{sum(freq[l] for l in hi_known)/sum(freq.values()):.1%} 的 token")

# ---------------------------------------------------------------- H2 邻域可读度
def context_of(l):
    out = []
    for si, s in enumerate(sents):
        n = len(s)
        for i, x in enumerate(s):
            if x == l:
                out.append({
                    "si": si, "i": i, "len": n,
                    "left": s[i - 1] if i > 0 else None,
                    "right": s[i + 1] if i < n - 1 else None,
                    "seq": s,
                })
    return out


h2 = []
for l in hapax:
    for c in context_of(l):
        L, R = c["left"], c["right"]
        n_known = (1 if L in hi_known else 0) + (1 if R in hi_known else 0)
        n_slots = (1 if L else 0) + (1 if R else 0)
        h2.append({"glyph": cp(l) or l, "label": l, "sent_len": c["len"],
                   "left": cp(L) if L else None, "right": cp(R) if R else None,
                   "known_neighbors": n_known, "slots": n_slots,
                   "context": " ".join("□" if x == l else (cp(x) or "?") for x in c["seq"])})

bracket = [x for x in h2 if x["known_neighbors"] == 2]
one_side = [x for x in h2 if x["known_neighbors"] == 1]
print("\n" + "=" * 78)
print("H2 邻域可读度：hapax 是不是出现在已识字中间？")
print("=" * 78)
print(f"  左右邻皆为高频已识字（强包围）  {len(bracket)} 个 ({len(bracket)/len(hapax):.1%})")
print(f"  一侧为高频已识字                {len(one_side)} 个 ({len(one_side)/len(hapax):.1%})")
print(f"  两侧皆非高频字                  {len(hapax)-len(bracket)-len(one_side)} 个")
print("\n  强包围样本（这些即使只出现一次，语境仍高度受限）：")
for x in bracket[:15]:
    print(f"    {x['glyph']:>3}  {x['context']}")

# ---------------------------------------------------------------- H1 句式规律性
print("\n" + "=" * 78)
print("H1 规律性：hapax 所在的句式是否反复出现？")
print("=" * 78)
frames = collections.Counter()
for x in h2:
    toks = x["context"].split()
    if "□" not in toks:
        continue
    j = toks.index("□")
    lo, hi = max(0, j - 2), min(len(toks), j + 3)   # ±2 字框架
    frames[" ".join(toks[lo:hi])] += 1
# 统计每个 hapax 的框架是否被其它 hapax 共用
own_frame = {}
for x in h2:
    toks = x["context"].split()
    if "□" not in toks:
        continue
    j = toks.index("□")
    lo, hi = max(0, j - 2), min(len(toks), j + 3)
    own_frame[x["glyph"]] = " ".join(toks[lo:hi])
shared = sum(1 for g, f in own_frame.items() if frames[f] > 1)
print(f"  可提取框架（±2 字）{len(frames)} 种")
print(f"  框架被 ≥2 个 hapax 共用的：{shared} 个 "
      f"（占 {shared/len(own_frame):.1%}）")
print("  最高频框架：")
for f, v in frames.most_common(12):
    print(f"    {v:>3}×  {f}")

# ---------------------------------------------------------------- H4 复现检验
print("\n" + "=" * 78)
print("H4 复现检验：hapax 的完整上下文是否在别处由已识字复现？")
print("=" * 78)
known_sent = collections.defaultdict(list)
for si, s in enumerate(sents):
    known_sent[tuple(s)].append(si)
hits = 0
h4_rows = []
hapax_set = set(hapax)
for x in h2:
    toks = x["context"].split()
    tgt_idx = toks.index("□")
    found = False
    for si, s in enumerate(sents):
        if len(s) != len(toks) or found:
            continue
        # 必须同位是【已识字】，且不是该 hapax 本身、也不是匿名/占位
        sub = s[tgt_idx]
        if sub in hapax_set or is_anon(sub):
            continue
        if not cp(sub):
            continue
        if all((k == tgt_idx) or (cp(s[k]) == toks[k]) for k in range(len(toks))):
            h4_rows.append({"glyph": x["glyph"], "parallel": x["context"],
                            "substitute": cp(sub),
                            "parallel_context": " ".join(cp(z) or "?" for z in s)})
            found = True
print(f"  找到「同框架但同位为已识字」的平行辞例：{len(h4_rows)} 个 "
      f"（占 hapax 的 {len(h4_rows)/len(hapax):.1%}）")
for r in h4_rows[:12]:
    print(f"    {r['glyph']:>3}  {r['parallel']}   ←→   {r['parallel_context']}  (可替换为「{r['substitute']}」)")

# ---------------------------------------------------------------- H3 部首共享
print("\n" + "=" * 78)
print("H3 偏旁/部首：hapax 与已识字是否共享部首？")
print("=" * 78)
DZ = json.load(open(os.path.join(D, "DZ.json"), encoding="utf-8"))
by_rad = collections.defaultdict(list)
for r in DZ:
    if r.get("FTZ"):
        by_rad[r["BSBM"]].append(r["FTZ"])
multi = {k: v for k, v in by_rad.items() if len(v) >= 5}
print(f"  殷契文渊字形库：{len(DZ):,} 行，{len(by_rad)} 个部首；"
      f"其中含 ≥5 个字形的部首 {len(multi)} 个")
print("  部首规模（Top 10，展示一字形可对应多字的部首类别）：")
for k, v in sorted(multi.items(), key=lambda x: -len(x[1]))[:10]:
    sample = "、".join(sorted(set(v))[:10])
    print(f"    {k}: {len(v):>4} 个字形，例：{sample}")
print("\n  说明：殷契文渊以部首（BSBM）组织字形库，同一部首下聚集的字形")
print("  天然构成「偏旁族」。未释字若与已识字同族，即满足 H3。")

# ---------------------------------------------------------------- 汇总
summary = {
    "n_anon": len(anon), "n_hapax": len(hapax), "n_rare2": len(rare2),
    "bracketed": len(bracket), "one_side": len(one_side),
    "n_frames": len(frames), "n_frames_repeated": sum(1 for v in frames.values() if v > 1),
    "n_parallel": len(h4_rows),
    "hi_known_coverage": sum(freq[l] for l in hi_known) / sum(freq.values()),
}
json.dump({"summary": summary, "bracketed": bracket[:120],
           "parallel": h4_rows[:120],
           "top_frames": frames.most_common(60)},
          open(os.path.join(RES, "hapax_analysis.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n[写出] " + os.path.join(RES, "hapax_analysis.json"))
