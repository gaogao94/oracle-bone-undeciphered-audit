# -*- coding: utf-8 -*-
"""
逐条复核 15 个高价值目标：把候选字填入，检验辞例通顺性
复核方法（三条独立检验）：
  (A) 填入后所得辞例，是否与语料中"该候选字"的真实用例同型（同长度、同框架）
  (B) 该候选字在语料中是否曾出现在同样的相邻字之后/之前
  (C) 填入后是否与已知语法冲突（如「貞…貞」「卜…卜」重复）
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
    nm = p.get("RubbingName")
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        seq = sorted([c for c in (g.get("RecordUtilOracleCharVoList") or [])
                      if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
        if seq:
            sents.append((nm, [c["Label"] for c in seq], [cp(c["Label"]) or "◻" for c in seq]))
freq = collections.Counter()
for _, L, _ in sents:
    freq.update(L)
label_of_char = {}
for lab, v in mc.items():
    c = v.get("codepoint") or ""
    if len(c) == 1:
        label_of_char.setdefault(c, lab)

hv = json.load(open(os.path.join(RES, "high_value_targets.json"), encoding="utf-8"))
# 补充 label 映射
for r in hv:
    if "label" not in r or r["label"] not in freq:
        g = r["glyph"]
        r["label"] = label_of_char.get(g, g)


def occ_of(lab):
    out = []
    for nm, L, C in sents:
        for i, x in enumerate(L):
            if x == lab:
                out.append((nm, i, L, C))
    return out


print("=" * 104)
print("逐条复核：15 个高价值目标")
print("=" * 104)
report = []
for k, r in enumerate(hv, 1):
    xlab = r["label"]
    cad = r["cad"][0] if r["cad"] else None
    klab = label_of_char.get(cad)
    print(f"\n{'─'*104}")
    print(f"[{k}] 未釋字 {r['glyph']}（{r['freq']}次，{r['n_glyphs']}形） → 候選「{cad}」（語料 {freq.get(klab,0)} 次）")
    print(f"{'─'*104}")
    verdict = {"A": "—", "B": "—", "C": "—"}
    for nm, i, L, C in occ_of(xlab):
        filled = list(C)
        filled[i] = cad
        raw = " ".join(C)
        new = " ".join(filled)
        print(f"  原辭例 {nm}: {raw}")
        print(f"  填為     {nm}: {new}")
        # (C) 重复冲突检查
        prev_c = C[i - 1] if i > 0 else None
        next_c = C[i + 1] if i < len(C) - 1 else None
        if prev_c == cad or next_c == cad:
            verdict["C"] = "衝突：填入字與緊鄰字重複"
            print(f"     ⚠ (C) 與緊鄰字重複（{cad}）→ 不通")
        # (A) 是否有同型真实用例：同长度、同位置是该候选字、其余逐字相同
        same = 0
        if klab:
            for nm2, L2, C2 in sents:
                if len(C2) != len(C):
                    continue
                if L2[i] != klab:
                    continue
                if all(j == i or C2[j] == C[j] for j in range(len(C))):
                    same += 1
        verdict["A"] = f"同型真实用例 {same} 条"
        print(f"     (A) 語料中「同長度、同位置為{cad}、其餘逐字相同」的真實用例：{same} 條")
        # (B) 前后邻字相容性
        if klab:
            after = collections.Counter()
            before = collections.Counter()
            for nm2, L2, C2 in sents:
                for j, y in enumerate(L2):
                    if y != klab:
                        continue
                    if j > 0:
                        before[C2[j - 1]] += 1
                    if j < len(L2) - 1:
                        after[C2[j + 1]] += 1
            bn = before.get(prev_c, 0) if prev_c else None
            an = after.get(next_c, 0) if next_c else None
            pb = f"前鄰「{prev_c}」出現 {bn} 次" if prev_c else "無前鄰"
            pa = f"後鄰「{next_c}」出現 {an} 次" if next_c else "無後鄰"
            verdict["B"] = f"{pb}；{pa}"
            print(f"     (B) {cad} 之前接「{prev_c}」的次數 {bn}；之後接「{next_c}」的次數 {an}")
    report.append({**r, "verdict": verdict})

print("\n" + "=" * 104)
print("汇总")
print("=" * 104)
print(f"{'未釋字':>6}{'候選':>6}{'(A)同型用例':>12}{'(C)重複衝突':>12}  結論")
for r in report:
    a = r["verdict"]["A"]
    c = r["verdict"]["C"]
    ok = ("不通" if "衝突" in c else ("通過" if "0 条" not in a else "待考"))
    print(f"{r['glyph']:>6}{r['cad'][0] if r['cad'] else '—':>6}{a:>12}{c:>12}  {ok}")

json.dump(report, open(os.path.join(RES, "review_15.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"\n[写出] result/review_15.json")
