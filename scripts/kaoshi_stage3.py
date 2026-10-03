# -*- coding: utf-8 -*-
"""
阶段 III：分布替换检验 + 音韵相容性 → 双维度候选排序
--------------------------------------------------------------
核心检验（可证伪）：
  对未释字 u 与已识字 k，计算
    P(u 出现 | 上下文) 与 P(k 出现 | 上下文) 的差异（Jensen-Shannon 散度）
  若 k 在 u 的所有平行辞例槽位中都能替换而不违和 → k 与 u 同槽位。

为什么这符合前人判据：
  · 陈剑释「徹」靠的就是「辞例极相似 + 类组分布互补」——替换检验是其量化形式；
  · 蒋玉斌释「蠢」的胜负手也是「该字与金文『反某方』同位」——即槽位身份。
  但替换相容 ≠ 同字（同一槽位可容纳近义不同字），所以只作候选生成，不作结论。

音韵相容性用于对候选做第二维过滤（王力系统 声纽/韵部）。
"""
import io, json, math, os, sys, time, collections, urllib.parse, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
OB = os.path.join(D, "obimd")
RES = os.path.join(HERE, "result")
CACHE = os.path.join(D, "cache_phon.json")
os.makedirs(RES, exist_ok=True)

# ---------------------------------------------------------------- 载入
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))

sents = []
for piece in data:
    for grp in piece.get("RecordUtilSentenceGroupVoList") or []:
        seq = sorted(((c.get("OrderNumber") or 0), c.get("Label"))
                     for c in (grp.get("RecordUtilOracleCharVoList") or [])
                     if c.get("Label"))
        labels = [l for _, l in seq]
        if labels:
            sents.append(labels)

freq = collections.Counter()
for s in sents:
    freq.update(s)


def cp(l):
    return mc.get(l, {}).get("codepoint") or ""


def anon(l):
    return (mc.get(l, {}).get("transcription") or []) == []


cands = sorted((l for l in freq if anon(l) and freq[l] >= 3), key=lambda l: -freq[l])
known = [l for l in freq if not anon(l) and cp(l)]
print(f"辞例 {len(sents):,}｜字形类 {len(freq):,}｜候选 {len(cands)}｜已识字类 {len(known)}")

# ---------------------------------------------------------------- 上下文模型
# 用「左右邻字类别 + 位置」做上下文特征；对每个已识字统计其上下文分布
def ctx_feats(s, i):
    n = len(s)
    left = cp(s[i - 1]) if i > 0 else "^"
    right = cp(s[i + 1]) if i < n - 1 else "$"
    pos = "首" if i == 0 else ("末" if i == n - 1 else "中")
    return left, right, pos


# 每个已识字类的上下文计数
KCTX = {}
for l in known:
    KCTX[l] = collections.Counter()
for s in sents:
    n = len(s)
    for i, l in enumerate(s):
        if l in KCTX:
            KCTX[l][ctx_feats(s, i)] += 1

print("已识字上下文模型构建完毕")

# ---------------------------------------------------------------- 替换检验
def js_divergence(c1, c2):
    keys = set(c1) | set(c2)
    t1 = sum(c1.values()) or 1
    t2 = sum(c2.values()) or 1
    d = 0.0
    for k in keys:
        p = c1.get(k, 0) / t1
        q = c2.get(k, 0) / t2
        m = (p + q) / 2
        if p > 0:
            d += 0.5 * p * math.log2(p / m)
        if q > 0:
            d += 0.5 * q * math.log2(q / m)
    return d


phon = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}


def ph(ch):
    r = phon.get(ch) or {}
    return r.get("initial"), r.get("rhyme")


results = []
for u in cands:
    U = collections.Counter()
    for s in sents:
        n = len(s)
        for i, l in enumerate(s):
            if l == u:
                U[ctx_feats(s, i)] += 1
    scored = []
    for k in KCTX:
        # 只比较规模相近的类，避免高频字因平滑而虚假胜出
        if KCTX[k].total() < 2:
            continue
        j = js_divergence(U, KCTX[k])
        scored.append((j, k))
    scored.sort()
    top = scored[:20]
    # 音韵标记：候选字与其高频共现字的音韵是否相容（仅作标注，不作取舍）
    rc = collections.Counter()
    lc = collections.Counter()
    for s in sents:
        n = len(s)
        for i, l in enumerate(s):
            if l == u:
                if i > 0 and cp(s[i - 1]):
                    lc[cp(s[i - 1])] += 1
                if i < n - 1 and cp(s[i + 1]):
                    rc[cp(s[i + 1])] += 1
    results.append({
        "glyph": cp(u) or u, "label": u, "occurrences": freq[u],
        "n_contexts": U.total(),
        "top_right": rc.most_common(10), "top_left": lc.most_common(10),
        "substitution_candidates": [
            {"char": cp(k), "js": round(j, 4), "freq": KCTX[k].total(),
             "initial": ph(cp(k))[0], "rhyme": ph(cp(k))[1]} for j, k in top],
        "examples": [],
    })
    for s in sents:
        if u in s and len(s) >= 4 and len(results[-1]["examples"]) < 6:
            results[-1]["examples"].append(
                " ".join("□" if l == u else (cp(l) or "?") for l in s))

# ---------------------------------------------------------------- 输出
results.sort(key=lambda r: -r["occurrences"])
with open(os.path.join(RES, "stage3_substitution.json"), "w", encoding="utf-8") as f:
    json.dump({"method": "Jensen-Shannon contextual substitution test; "
                         "candidate generation only, NOT decipherment",
               "n_sentences": len(sents), "n_candidates": len(cands),
               "results": results}, f, ensure_ascii=False, indent=1)

with open(os.path.join(RES, "stage3_report.md"), "w", encoding="utf-8") as f:
    f.write("# 阶段 III 报告：分布替换检验\n\n")
    f.write("> ⚠️ 本报告输出的是**候选生成**，不是释读结论。替换相容 ≠ 同字。\n\n")
    f.write(f"- 语料：OBIMD {len(data):,} 片，重建辞例 {len(sents):,} 条\n")
    f.write(f"- 匿名字形中 ≥3 次出现者：**{len(cands)}** 个\n")
    f.write(f"- 检验：对每个候选，计算其上下文分布与全部已识字类上下文分布的 "
            f"Jensen-Shannon 散度，取最小的 20 个作为「同槽位候选」\n\n")
    for r in results:
        f.write(f"## {r['glyph']}　出现 {r['occurrences']} 次（{r['n_contexts']} 个上下文）\n\n")
        f.write(f"- 高频右邻：{'、'.join(f'{c}×{n}' for c, n in r['top_right'][:8]) or '—'}\n")
        f.write(f"- 高频左邻：{'、'.join(f'{c}×{n}' for c, n in r['top_left'][:8]) or '—'}\n")
        f.write(f"- 同槽位候选（JS 越小越相容）：\n\n")
        f.write("  | 序 | 候选字 | JS 散度 | 该字出现次数 | 声纽 | 韵部 |\n")
        f.write("  |---|---|---|---|---|---|\n")
        for i, c in enumerate(r["substitution_candidates"], 1):
            f.write(f"  | {i} | {c['char']} | {c['js']} | {c['freq']} | "
                    f"{c['initial'] or '?'} | {c['rhyme'] or '?'} |\n")
        f.write(f"\n- 辞例样本（□=本字）：\n\n")
        for e in r["examples"]:
            f.write(f"  - {e}\n")
        f.write("\n")

print("\n" + "=" * 82)
print("阶段 III：分布替换检验 —— 前 10 个候选的「同槽位候选」")
print("=" * 82)
for r in results[:10]:
    print(f"\n■ {r['glyph']}  (出现 {r['occurrences']} 次)")
    print("   右邻: " + "、".join(f"{c}×{n}" for c, n in r["top_right"][:6]))
    print("   同槽位候选: " + "  ".join(
        f"{c['char']}(JS={c['js']},{c['initial'] or '?'}{c['rhyme'] or '?'})"
        for c in r["substitution_candidates"][:6]))
    for e in r["examples"][:2]:
        print("     例: " + e)

print(f"\n[写出] {os.path.join(RES, 'stage3_substitution.json')}")
print(f"[写出] {os.path.join(RES, 'stage3_report.md')}")
