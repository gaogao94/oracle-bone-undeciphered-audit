# -*- coding: utf-8 -*-
"""
最终交付：完整证据链包（形 / 辞例 / 音 三类齐备）
================================================
整合：
  · 形  ← 字形图像相似度检索（已通过留一法标定，top-1 78.9%）+ 字形图对照
  · 辞例 ← 平行辞例检验（同长度、其余位置全为已释字、同位为已释字）
  · 音  ← zdic 上古音（黄侃/王力系统），仅覆盖已释字
并明确标注：
  [机器可证] / [需人工判定] / [本语料不可证]
"""
import io, json, os, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
OB = os.path.join(D, "obimd")
RES = os.path.join(HERE, "result")

mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
phon = json.load(open(os.path.join(D, "cache_phon.json"), encoding="utf-8"))
match = json.load(open(os.path.join(RES, "glyph_match.json"), encoding="utf-8"))
solv = json.load(open(os.path.join(RES, "hapax_solvability_v3.json"), encoding="utf-8"))
val = json.load(open(os.path.join(RES, "retrieval_validation.json"), encoding="utf-8"))

sents = []
for piece in data:
    nm = piece.get("RubbingName")
    for g in piece.get("RecordUtilSentenceGroupVoList") or []:
        seq = sorted(((c.get("OrderNumber") or 0), c.get("Label"))
                     for c in (grp if False else (g.get("RecordUtilOracleCharVoList") or []))
                     if c.get("Label"))
        lab = [l for _, l in seq]
        if lab:
            sents.append((nm, lab))

freq = collections.Counter()
for _, s in sents:
    freq.update(s)
cp = lambda l: mc.get(l, {}).get("codepoint") or ""
is_anon = lambda l: (mc.get(l, {}).get("transcription") or []) == []

# 匿名类按语料出现次数分层
anon = sorted((l for l in freq if is_anon(l)), key=lambda l: -freq[l])
layers = collections.Counter()
for l in anon:
    v = freq[l]
    layers["1次" if v == 1 else "2次" if v == 2 else "3–9次" if v <= 9 else "≥10次"] += 1
print("匿名字形分层（按语料实际出现次数）:", dict(layers))
print(f"匿名类总数 {len(anon)}（其中辞例频次为1的 {layers['1次']}）")

mat = {m["label"]: m for m in match if "best" in m}
solvm = {r["label"]: r for r in solv["rows"]}

# 每个匿名字形：三类证据
rows = []
for lab in anon:
    m = mat.get(lab, {})
    s = solvm.get(lab, {})
    top = (m.get("best") or [{}])[0]
    char = top.get("char")
    sys_ = (phon.get(char) or {}).get("systems") or {}
    rows.append({
        "label": lab,
        "glyph": cp(lab) or lab,
        "corpus_occurrences": freq[lab],
        "form": {                                   # 形
            "top_match": char,
            "top_score": top.get("detail", {}).get("total"),
            "second_match": (m.get("best") or [{}, {}])[1].get("char") if len(m.get("best") or []) > 1 else None,
            "second_score": (m.get("best") or [{}, {}])[1].get("detail", {}).get("total") if len(m.get("best") or []) > 1 else None,
            "sheet": m.get("sheet"),
            "method_reliability_top1": round(val["top1"], 3),
        },
        "context": {                                # 辞例
            "parallel": s.get("parallel") or [],
            "sentences": s.get("contexts") or [],
            "piece": (s.get("pieces") or [None])[0],
        },
        "phon": {                                   # 音
            "of_top_match": sys_,
            "note": "本字为未释字，无音韵；音韵仅能由假设读法提供",
        },
        "verdict": {
            "machine_provable": (
                f"字形与「{char}」相似度 {top.get('detail',{}).get('total')}"
                if char else "无字形数据"),
            "needs_human": [
                "确认笔画连接方式与「%s」是否同构" % char if char else "无候选",
                "查《甲骨文字编》《新甲骨文编》该形著录与旧释",
                "确认该片类组/时期，检验是否与「%s」类组互补" % char if char else "—",
            ],
            "not_provable_here": [
                "若该形仅此一见，无法用辞例互证（孤证）",
                "OBIMD 无类组标注，无法做类组检验",
            ],
        },
    })

# 按"形似度 × 与次名的间隔"排序（间隔越大越可信）
def key(r):
    t = r["form"]["top_score"] or 0
    s2 = r["form"]["second_score"] or 0
    return -(t * 0.6 + (t - s2) * 0.4)
rows.sort(key=key)

json.dump({"validation": val, "layers": dict(layers),
           "n_anon": len(anon), "rows": rows},
          open(os.path.join(RES, "evidence_chains.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

print("\n" + "=" * 100)
print("完整证据链 — 前 20（形似度 × 领先间隔 排序）")
print("=" * 100)
print(f"{'未释字':>4} {'次数':>4} {'形似候选':<10} {'形似分':>6} {'次名':<8} {'间隔':>6} {'辞例平行':>7} {'音韵'}")
print("-" * 100)
for r in rows[:20]:
    f = r["form"]
    gap = (f["top_score"] or 0) - (f["second_score"] or 0)
    sys_ = r["phon"]["of_top_match"]
    syss = "、".join(f"{k[:2]}:{v}" for k, v in sys_.items()) or "—"
    par = len(r["context"]["parallel"])
    print(f"{r['glyph']:>4} {r['corpus_occurrences']:>4} {str(f['top_match']):<10} "
          f"{(f['top_score'] or 0):>6.3f} {str(f['second_match']):<8} {gap:>6.3f} {par:>7}  {syss}")

strong = [r for r in rows if (r["form"]["top_score"] or 0) >= 0.70
          and ((r["form"]["top_score"] or 0) - (r["form"]["second_score"] or 0)) >= 0.10]
print(f"\n强候选（形似 ≥0.70 且领先次名 ≥0.10）：{len(strong)} 个")
for r in strong:
    f = r["form"]
    print(f"  {r['glyph']} → 「{f['top_match']}」 形似 {f['top_score']:.3f}"
          f"（次名 {f['second_match']} {f['second_score']:.3f}）"
          f" 语料 {r['corpus_occurrences']} 次  对照图 {f['sheet']}")

print("\n[写出] result/evidence_chains.json")
