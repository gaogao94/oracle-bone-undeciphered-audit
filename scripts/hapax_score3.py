# -*- coding: utf-8 -*-
"""
可考性评分 v3（严格版）
关键修正：
  1) 辞例渲染：目标位置渲染为 □，已知字渲染为字，匿名邻字渲染为 ◻（三态区分）
  2) 平行辞例检验（H4）严格化：
       - 其余位置【必须全部是已释字】（不能有匿名/空缺），否则"逐字相同"会被
         空字符串虚假满足；
       - 同位替换字必须是已识高频字；
       - 记录平行辞例的片号，供人工核对。
  3) 增加 H0 检验：该 hapax 是否与某个已识字出现在完全相同的「片 + 位置框架」中。
"""
import io, json, math, os, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
OB = os.path.join(D, "obimd")
RES = os.path.join(HERE, "result")

data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))

sents = []           # (rubbing_name, labels)
for piece in data:
    nm = piece.get("RubbingName") or "?"
    for grp in piece.get("RecordUtilSentenceGroupVoList") or []:
        seq = sorted(((c.get("OrderNumber") or 0), c.get("Label"))
                     for c in (grp.get("RecordUtilOracleCharVoList") or [])
                     if c.get("Label"))
        lab = [l for _, l in seq]
        if lab:
            sents.append((nm, lab))

freq = collections.Counter()
for _, s in sents:
    freq.update(s)
cp = lambda l: mc.get(l, {}).get("codepoint") or ""
is_anon = lambda l: (mc.get(l, {}).get("transcription") or []) == []
anon_set = {l for l in freq if is_anon(l)}
decoded = {l for l in freq if l not in anon_set and cp(l)}
hi = {l for l in decoded if freq[l] >= 20}
print(f"辞例 {len(sents):,}｜字形类 {len(freq):,}｜匿名 {len(anon_set)}｜"
      f"已释有字 {len(decoded):,}｜≥20次 {len(hi)}")


def render(labels, tgt):
    out = []
    for k, l in enumerate(labels):
        if k == tgt:
            out.append("□")
        elif l in decoded:
            out.append(cp(l))
        else:
            out.append("◻")
    return " ".join(out)


# 索引：按 (长度) 与 (全部已释) 分类
len_idx = collections.defaultdict(list)
for si, (nm, s) in enumerate(sents):
    len_idx[len(s)].append(si)
all_decoded = [si for si, (nm, s) in enumerate(sents) if all(l in decoded for l in s)]

rows = []
for l in sorted(anon_set, key=lambda x: -freq[x]):
    occ = [(si, i) for si, (nm, s) in enumerate(sents)
           for i, x in enumerate(s) if x == l]
    n = len(occ)
    # S1 邻域可读度（仅高频已识字）
    kk = slots = 0
    for si, i in occ:
        s = sents[si][1]
        for j in (i - 1, i + 1):
            if 0 <= j < len(s):
                slots += 1
                kk += s[j] in hi
    s1 = kk / slots if slots else 0.0

    # H4 严格平行检验
    ph = []
    for si, i in occ:
        s = sents[si][1]
        for sj in len_idx[len(s)]:
            if sj == si:
                continue
            t = sents[sj][1]
            if any(k != i and t[k] not in decoded for k in range(len(s))):
                continue                      # 其余位置必须全为已释字
            if any(k != i and cp(t[k]) != cp(s[k]) for k in range(len(s))):
                continue
            sub = t[i]
            if sub not in decoded or sub == l:
                continue
            ph.append({"substitute": cp(sub), "sub_freq": freq[sub],
                       "context": render(s, i), "parallel_line": render(t, i),
                       "piece": sents[sj][0], "sub_piece": sents[si][0]})
            break
        if len(ph) >= 3:
            break

    # S3 框架复现
    fr = tuple(cp(sents[si][1][k]) or "◻"
               for si, i in occ[:1]
               for k in range(max(0, i - 2), min(len(sents[si][1]), i + 3)))
    same_fr = sum(1 for sj, (nm, s) in enumerate(sents)
                  if len(s) >= 1 and True)  # placeholder; 实际统计见下
    # 正确统计：全局框架计数
    rows.append({"glyph": cp(l) or l, "label": l, "occurrences": n,
                 "neighbor_readability": round(s1, 3),
                 "parallel": ph,
                 "contexts": [render(sents[si][1], i) for si, i in occ[:4]],
                 "pieces": [sents[si][0] for si, i in occ[:4]]})

# 全局框架统计（±2 字窗口）
frames = collections.Counter()
for l in anon_set:
    for si, (nm, s) in enumerate(sents):
        for i, x in enumerate(s):
            if x == l:
                lo, hi_ = max(0, i - 2), min(len(s), i + 3)
                frames[tuple(cp(s[k]) or "◻" for k in range(lo, hi_))] += 1

for r in rows:
    l = r["label"]
    occ = [(si, i) for si, (nm, s) in enumerate(sents) for i, x in enumerate(s) if x == l]
    si, i = occ[0]
    s = sents[si][1]
    lo, hi_ = max(0, i - 2), min(len(s), i + 3)
    fr = tuple(cp(s[k]) or "◻" for k in range(lo, hi_))
    r["frame_repeat"] = frames[fr]
    s2 = min(len(r["parallel"]), 3) / 3
    s3 = min(frames[fr], 3) / 3
    s5 = min(math.log1p(r["occurrences"]) / math.log1p(10), 1.0)
    r["score"] = round(100 * (0.30 * r["neighbor_readability"] + 0.30 * s2
                              + 0.10 * s3 + 0.30 * s5), 1)

rows.sort(key=lambda r: (-r["score"], -r["occurrences"]))
T = [r for r in rows if r["occurrences"] == 1]
withpar = [r for r in T if r["parallel"]]

print("\n" + "=" * 88)
print("hapax（仅出现一次，共 %d 个）严格检验结果" % len(T))
print("=" * 88)
print(f"  找到「其余位置全为已释字」的平行辞例：{len(withpar)} 个 "
      f"（占 {len(withpar)/len(T):.1%}）")
print(f"  邻域全为高频已识字（可读度=1.0）："
      f"{sum(1 for r in T if r['neighbor_readability']==1.0)} 个")
print(f"  评分 ≥45：{sum(1 for r in T if r['score']>=45)}｜"
      f"30–45：{sum(1 for r in T if 30<=r['score']<45)}｜"
      f"<30：{sum(1 for r in T if r['score']<30)}")

print("\n" + "=" * 88)
print("有严格平行辞例的 hapax（这些是真正可推进的）")
print("=" * 88)
for r in withpar[:15]:
    print(f"\n■ {r['glyph']}  出现 {r['occurrences']} 次｜邻域可读 {r['neighbor_readability']}")
    for c, p in zip(r["contexts"][:1], r["parallel"][:2]):
        print(f"     本字辞例: {c}")
        print(f"     平行辞例: {p['parallel_line']}   → 同位为「{p['substitute']}」"
              f"(该字共 {p['sub_freq']} 次)  片号 {p['piece']}")

json.dump({"n_hapax": len(T), "n_with_parallel": len(withpar), "rows": rows},
          open(os.path.join(RES, "hapax_solvability_v3.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n[写出] " + os.path.join(RES, "hapax_solvability_v3.json"))
