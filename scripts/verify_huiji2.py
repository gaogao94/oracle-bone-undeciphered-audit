# -*- coding: utf-8 -*-
"""取「吉」的检索结果，聚焦事何類/何組，看「王X叀（惠）吉」有无已释实例"""
import io, os, re, sys, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import gxds2


def sg(t):
    return re.sub(r"（[^）]*）|\([^)]*\)|〔[^〕]*〕|【[^】]*】", "", t)


rows, total = gxds2.query("吉", maxpages=6, verbose=True)
print(f"「吉」→ {len(rows)} 行 / {total} 页")
seen, uniq = set(), []
for r in rows:
    k = (r["no"], r["seq"], r["text"][:26])
    if k in seen:
        continue
    seen.add(k)
    uniq.append(r)
print(f"去重 {len(uniq)} 行")

gs = collections.Counter(r["group"] for r in uniq)
print(f"\n类组分布: {gs.most_common(15)}")

print("\n" + "=" * 104)
print("事何類 / 何組 中含「吉」的实例（全部列出）")
print("=" * 104)
targets = [r for r in uniq if "事何" in (r["group"] or "") or "何" in (r["group"] or "")]
print(f"共 {len(targets)} 条")
for r in targets[:40]:
    print(f"   [{r['group']:<12}] {r['text'][:92]}")

print("\n" + "=" * 104)
print("「王?叀吉」/「王?惠吉」模式检索")
print("=" * 104)
hits = []
for r in uniq:
    s = sg(r["text"])
    for m in re.finditer(r"王(.)(?:叀|惠)吉", s):
        hits.append((r, m.group(1)))
print(f"命中 {len(hits)} 条")
for r, x in hits[:20]:
    print(f"   X=「{x}」(U+{ord(x):04X})  [{r['group']}] {r['text'][:88]}")

print("\n" + "=" * 104)
print("「?叀吉」/「?惠吉」前字分布（全部样本）")
print("=" * 104)
pre = collections.Counter()
ex = []
for r in uniq:
    s = sg(r["text"])
    for m in re.finditer(r"(.)(?:叀|惠)吉", s):
        pre[m.group(1)] += 1
        if len(ex) < 20:
            ex.append((r, m.group(1)))
for k, v in pre.most_common(25):
    print(f"   「{k}」U+{ord(k):04X} ×{v}")
print("\n实例:")
for r, x in ex:
    print(f"   [{r['group']}] …{x}叀/惠吉… {r['text'][:80]}")
