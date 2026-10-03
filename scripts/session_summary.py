# -*- coding: utf-8 -*-
"""
本会话对「量化考释方法」的完整验证报告（含全部否定性结果）
"""
import io, json, os, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "result")
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
freq = collections.Counter()
for s in sents:
    freq.update(s)
anon = [l for l in freq if (mc.get(l, {}).get("transcription") or []) == []]
print(f"语料：辞例 {len(sents):,}｜字形类 {len(freq):,}｜未释 {len(anon)}")

# 汇总各步骤结果
out = {"corpus": {"sentences": len(sents), "classes": len(freq), "anon": len(anon)}}

def load(name):
    p = os.path.join(RES, name)
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    return None

out["retrieval_validation"] = load("retrieval_validation.json")
out["source_comparison"] = load("source_comparison.json")
out["parallel_strength"] = load("parallel_strength.json")
out["constraint_strength_summary"] = None
cs = load("constraint_strength.json")
if cs:
    n0 = sum(1 for r in cs if r["best_n_rep"] == 0)
    n1 = sum(1 for r in cs if r["best_n_rep"] == 1)
    n2 = sum(1 for r in cs if r["best_n_rep"] == 2)
    n3 = sum(1 for r in cs if r["best_n_rep"] == 3)
    out["constraint_strength_summary"] = {"total": len(cs), "n0": n0, "n1": n1, "n2": n2, "n3": n3}

print("\n" + "=" * 92)
print("验证结果汇总")
print("=" * 92)
rv = out["retrieval_validation"]
if rv:
    print(f"  摹本图像检索（宽松参考库）: top-1 {rv['top1']:.1%}  MRR {rv['mrr']:.3f}")
sc = out["source_comparison"]
if sc:
    for m, v in sc.items():
        print(f"  字形来源 [{m}]: top-1 {v['top1']:.1%}  领先间隔中位 {v['margin_median']}")
ps = out["parallel_strength"]
if ps:
    strong = sum(1 for x in ps if x["strength"] >= 0.5)
    weak = sum(1 for x in ps if x["strength"] < 0.2)
    print(f"  平行辞例判据: 共 {len(ps)} 条，证据力≥0.5 的 {strong} 条，<0.2 的 {weak} 条")
cs2 = out["constraint_strength_summary"]
if cs2:
    print(f"  位置约束力: 未释字 {cs2['total']} 个；最强位置可替换字="
          f"0 者 {cs2['n0']}，1 者 {cs2['n1']}，2 者 {cs2['n2']}，3 者 {cs2['n3']}")

json.dump(out, open(os.path.join(RES, "session_summary.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n[写出] result/session_summary.json")
