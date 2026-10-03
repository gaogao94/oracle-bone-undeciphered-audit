# -*- coding: utf-8 -*-
"""
复核结论表：按「邻字相容性」判定每条假设的通顺性
判据：若候选字 K 在语料中常在「前邻 P」之后（或「后邻 N」之前）出现，则填入后成句自然。
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
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        seq = sorted([c for c in (g.get("RecordUtilOracleCharVoList") or [])
                      if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
        if seq:
            sents.append((p.get("RubbingName"), [c["Label"] for c in seq],
                          [cp(c["Label"]) or "◻" for c in seq]))
freq = collections.Counter()
for _, L, _ in sents:
    freq.update(L)
label_of_char = {}
for lab, v in mc.items():
    c = v.get("codepoint") or ""
    if len(c) == 1:
        label_of_char.setdefault(c, lab)

# 每字的邻字分布
AFTER = collections.defaultdict(collections.Counter)
BEFORE = collections.defaultdict(collections.Counter)
for nm, L, C in sents:
    for j, x in enumerate(L):
        if j > 0:
            BEFORE[x][C[j - 1]] += 1
        if j < len(L) - 1:
            AFTER[x][C[j + 1]] += 1

hv = json.load(open(os.path.join(RES, "high_value_targets.json"), encoding="utf-8"))
for r in hv:
    if r.get("label") not in freq:
        r["label"] = label_of_char.get(r["glyph"], r.get("label"))

print("=" * 100)
print("复核结论（B 判据：填入后邻字相容性）")
print("=" * 100)
print(f"{'#':>3}{'未釋字':>6}{'次':>4}{'候選':>7}{'前鄰':>6}{'前鄰相容':>9}{'後鄰':>6}{'後鄰相容':>9}  判定")
final = []
for k, r in enumerate(hv, 1):
    xlab = r["label"]
    cad = r["cad"][0] if r["cad"] else None
    klab = label_of_char.get(cad)
    if not klab:
        continue
    ok_count = 0
    tot = 0
    details = []
    for nm, L, C in sents:
        for i, x in enumerate(L):
            if x != xlab:
                continue
            prev_c = C[i - 1] if i > 0 else None
            next_c = C[i + 1] if i < len(L) - 1 else None
            b = BEFORE[klab].get(prev_c, 0) if prev_c else 0
            a = AFTER[klab].get(next_c, 0) if next_c else 0
            tot += 1
            if b > 0 or a > 0:
                ok_count += 1
            details.append((nm, prev_c, next_c, b, a))
    d0 = details[0]
    verdict = ("相容" if ok_count == tot else
               "部分相容" if ok_count > 0 else "不相容")
    print(f"{k:>3}{r['glyph']:>6}{r['freq']:>4}{cad:>7}{str(d0[1]):>6}{d0[3]:>9}{str(d0[2]):>6}{d0[4]:>9}  {verdict}")
    final.append({"glyph": r["glyph"], "cand": cad, "freq": r["freq"],
                  "n_occ": tot, "n_compatible": ok_count, "verdict": verdict,
                  "details": [{"piece": d[0], "prev": d[1], "next": d[2],
                               "before_hits": d[3], "after_hits": d[4]} for d in details]})

print("\n" + "=" * 100)
print("按判定分组")
print("=" * 100)
for v in ["相容", "部分相容", "不相容"]:
    grp = [f for f in final if f["verdict"] == v]
    print(f"\n【{v}】{len(grp)} 个")
    for f in grp:
        d = f["details"][0]
        print(f"   {f['glyph']} → {f['cand']}  （{d['piece']}：前鄰「{d['prev']}」在該字前出現 {d['before_hits']} 次；"
              f"後鄰「{d['next']}」在該字後出現 {d['after_hits']} 次）")

json.dump(final, open(os.path.join(RES, "review_verdicts.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"\n[写出] result/review_verdicts.json")
