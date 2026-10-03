# -*- coding: utf-8 -*-
"""
外部验证：用国学大师按字检索「惠」/「叀」/「吉」，看「王X惠吉」的写法
并检索事何類（廪辛—康丁）该套语的全部实例
"""
import io, os, re, sys, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import gxds2


def strip_gloss(t):
    return re.sub(r"（[^）]*）|\([^)]*\)|〔[^〕]*〕|【[^】]*】", "", t)


allrows = []
for q in ["惠吉", "叀吉", "惠", "叀"]:
    try:
        rows, total = gxds2.query(q, maxpages=4, verbose=True)
    except Exception as e:
        print(f"  检索「{q}」失败: {e}")
        continue
    print(f"  「{q}」→ {len(rows)} 行 / {total} 页")
    allrows += rows

print(f"\n合计 {len(allrows)} 行")
seen = set()
uniq = []
for r in allrows:
    k = (r["src"], r["no"], r["seq"], r["text"][:30])
    if k in seen:
        continue
    seen.add(k)
    uniq.append(r)
print(f"去重后 {len(uniq)} 行")

print("\n" + "=" * 104)
print("检索「王 X 叀（惠）吉」的全部实例（含 OCR/编码信息）")
print("=" * 104)
hits = []
for r in uniq:
    s = strip_gloss(r["text"])
    for m in re.finditer(r"王(.)(?:叀|惠)吉", s):
        hits.append((r, m.group(1)))
print(f"命中 {len(hits)} 条")
c = collections.Counter(x for _, x in hits)
print(f"X 位字符分布: {[(f'U+{ord(k):04X}' if ord(k) > 0x2000 else k, v) for k, v in c.most_common(15)]}")
for r, x in hits[:25]:
    print(f"   [{r['group']}] {r['text'][:92]}")

print("\n" + "=" * 104)
print("检索「?叀吉」/「?惠吉」的前字分布")
print("=" * 104)
pre = collections.Counter()
for r in uniq:
    s = strip_gloss(r["text"])
    for m in re.finditer(r"(.)(?:叀|惠)吉", s):
        pre[m.group(1)] += 1
print(f"  前字分布: {[(f'U+{ord(k):04X}' if ord(k) > 0x2000 else k, v) for k, v in pre.most_common(25)]}")

print("\n" + "=" * 104)
print("检索「王叀」/「王惠」的所有实例（看王后直接接惠的）")
print("=" * 104)
n = 0
for r in uniq:
    s = strip_gloss(r["text"])
    for m in re.finditer(r"王(叀|惠)", s):
        a = max(0, m.start() - 20)
        print(f"   [{r['group']}] …{s[a:m.start()+30]}…")
        n += 1
        if n >= 20:
            break
    if n >= 20:
        break

json.dump([{"group": r["group"], "text": r["text"], "x": x} for r, x in hits],
          open(os.path.join(_HERE, "result", "huiji_external.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"\n[写出] result/huiji_external.json")
