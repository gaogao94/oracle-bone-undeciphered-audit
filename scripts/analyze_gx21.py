# -*- coding: utf-8 -*-
"""
系统分析 󺡅（gx21ndp7yy，54 次）的真实身份
《合集》亦占位（合集5250 作「王□叀（惠）吉」）
用分布分析收窄：前邻、后邻、共现、类组、句式位置
"""
import io, os, sys, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import gxds2

OB = os.path.join(_HERE, "data", "obimd")
RES = os.path.join(_HERE, "result")
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
cp = lambda l: mc.get(l, {}).get("codepoint") or ""

TGT = "gx21ndp7yy"
sents = []
for p in data:
    nm = p.get("RubbingName") or ""
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        seq = sorted([c for c in (g.get("RecordUtilOracleCharVoList") or [])
                      if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
        if seq:
            sents.append((nm, [c["Label"] for c in seq], [cp(c["Label"]) or "◻" for c in seq]))

occ = []
for nm, L, C in sents:
    for i, x in enumerate(L):
        if x == TGT:
            occ.append((nm, i, L, C))

print("=" * 100)
print(f"󺡅 共 {len(occ)} 处")
print("=" * 100)

before = collections.Counter()
after = collections.Counter()
pos = collections.Counter()
lens = collections.Counter()
for nm, i, L, C in occ:
    before[C[i - 1] if i > 0 else "(句首)"] += 1
    after[C[i + 1] if i + 1 < len(C) else "(句末)"] += 1
    pos[i] += 1
    lens[len(C)] += 1

print(f"\n前邻字: {before.most_common(15)}")
print(f"\n后邻字: {after.most_common(15)}")
print(f"\n句内位置: {dict(sorted(pos.items()))}")
print(f"辞例长度: {dict(sorted(lens.items()))}")

# 共现分析：与 󺡅 同句出现的字
co = collections.Counter()
for nm, i, L, C in occ:
    for k, x in enumerate(L):
        if k != i and x != TGT:
            co[C[k]] += 1
print(f"\n共现字（同句其余字）: {co.most_common(20)}")

# 全部辞例
print("\n" + "=" * 100)
print("全部辞例")
print("=" * 100)
for nm, i, L, C in occ:
    s = " ".join("【□】" if k == i else C[k] for k in range(len(C)))
    print(f"  {nm}: {s}")

# 类组（查合集）
print("\n" + "=" * 100)
print("类组分布（取前 15 片的合集释文）")
print("=" * 100)
gs = collections.Counter()
plate_rows = {}
for nm, i, L, C in occ[:20]:
    num = nm.lstrip("H")
    if not num.isdigit():
        continue
    if num not in plate_rows:
        try:
            rows, _ = gxds2.query(num, maxpages=1)
        except Exception:
            rows = []
        plate_rows[num] = rows
    for r in plate_rows[num]:
        gs[r["group"]] += 1
print(f"  {gs.most_common(15)}")

for nm, i, L, C in occ[:12]:
    num = nm.lstrip("H")
    if num in plate_rows and plate_rows[num]:
        print(f"\n  片 {nm}  OBIMD: {' '.join('【□】' if k==i else C[k] for k in range(len(C)))}")
        for r in plate_rows[num][:3]:
            print(f"       合集 [{r['group']}] {r['text'][:88]}")

json.dump({"n": len(occ), "before": dict(before), "after": dict(after),
           "cooc": dict(co.most_common(30)), "groups": dict(gs)},
          open(os.path.join(RES, "gx21_analysis.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"\n[写出] result/gx21_analysis.json")
