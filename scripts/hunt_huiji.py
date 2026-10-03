# -*- coding: utf-8 -*-
"""
穷举缓存释文，找「王X叀（惠）吉」中 X 已释出的实例
并统计事何類里「王叀（惠）吉」类套语的分布
"""
import io, os, re, sys, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "gxds2")
files = [f for f in os.listdir(CACHE) if f.endswith(".html")]
print(f"缓存 HTML {len(files)} 个")

rows = []
for f in files:
    t = open(os.path.join(CACHE, f), encoding="utf-8").read()
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S | re.I):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S | re.I)
        if len(tds) < 4:
            continue
        cells = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", x)).strip() for x in tds]
        if len(cells) >= 5 and cells[1].isdigit():
            rows.append({"src": cells[0], "no": cells[1], "seq": cells[2],
                         "text": cells[3], "group": cells[4]})
        elif len(cells) >= 4 and cells[0].isdigit():
            rows.append({"src": "", "no": cells[0], "seq": cells[1],
                         "text": cells[2], "group": cells[3]})
print(f"解析出 {len(rows)} 行释文")

# 去掉今字标注后再匹配
def strip_gloss(t):
    return re.sub(r"（[^）]*）|\([^)]*\)|〔[^〕]*〕|【[^】]*】", "", t)

print("\n" + "=" * 104)
print("检索「王 ? 叀 吉」——看 X 位置已释出的实例")
print("=" * 104)
hits = []
for r in rows:
    s = strip_gloss(r["text"])
    for m in re.finditer(r"王(.)叀吉", s):
        hits.append((r, m.group(1)))
if hits:
    c = collections.Counter(x for _, x in hits)
    print(f"  命中 {len(hits)} 条，X 位字符分布：")
    for ch, n in c.most_common(20):
        print(f"     「{ch}」×{n}")
    print("\n  实例：")
    for r, x in hits[:15]:
        print(f"     [{r['group']}] {r['text'][:88]}")
else:
    print("  未命中（缓存的释文页中无此模式）")

print("\n" + "=" * 104)
print("检索「王 叀 吉」直接相连——看是否有省略 X 的实例")
print("=" * 104)
h2 = [r for r in rows if "王叀吉" in strip_gloss(r["text"])]
print(f"  命中 {len(h2)} 条")
for r in h2[:15]:
    print(f"     [{r['group']}] {r['text'][:88]}")

print("\n" + "=" * 104)
print("检索「叀吉」的全部实例及其前字")
print("=" * 104)
pre = collections.Counter()
ex = []
for r in rows:
    s = strip_gloss(r["text"])
    for m in re.finditer(r"(.)叀吉", s):
        pre[m.group(1)] += 1
        if len(ex) < 20:
            ex.append((r, m.group(1)))
print(f"  「?叀吉」前字分布: {pre.most_common(25)}")
print("\n  实例：")
for r, x in ex[:20]:
    print(f"     [{r['group']}] …{x}叀吉…  ← {r['text'][:70]}")

json.dump({"wang_x_huiji": [(r, x) for r, x in hits],
           "wang_huiji": h2, "pre_huiji": dict(pre)},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "result", "huiji_pattern.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n[写出] result/huiji_pattern.json")
