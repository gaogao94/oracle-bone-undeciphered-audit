# -*- coding: utf-8 -*-
"""
攻真候选：用《合集》全文检索找同文例
对每个真候选，取其辞例中可检索的关键字，在全《合集》中找同文例，
看该位置在别处用什么字（= 已释出的对应字）。
"""
import io, os, re, sys, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import gxds2

RES = os.path.join(_HERE, "result")
recs = json.load(open(os.path.join(RES, "align_records.json"), encoding="utf-8"))
real = {}
for r in recs:
    if r["status"] == "合集亦占位":
        k = r["label"]
        if k not in real or r["freq"] > real[k]["freq"]:
            real[k] = r
real = sorted(real.values(), key=lambda r: -r["freq"])
print(f"真候选 {len(real)} 个\n")

# 取辞例中长度≥2 的连续已释字串作为检索词
def keywords(ob):
    toks = [t for t in ob.split() if t and t != "◻" and not (len(t) == 1 and ord(t) > 0xE000)]
    out = []
    for n in (3, 2):
        for i in range(len(toks) - n + 1):
            s = "".join(toks[i:i + n])
            if all("\u4e00" <= c <= "\u9fff" for c in s):
                out.append(s)
    return out


print("=" * 104)
print("真候选的同文例检索")
print("=" * 104)
report = []
for r in real[:20]:
    kws = keywords(r["ob"])[:4]
    print(f"\n■ {r['glyph']}（{r['freq']}次）片 {r['plate']} [{r['group']}]")
    print(f"   辞例: {r['ob']}")
    found = []
    for kw in kws:
        try:
            rows, total = gxds2.query(kw, maxpages=1)
        except Exception as e:
            continue
        for x in rows[:8]:
            if x["no"] == r["plate"]:
                continue
            found.append({"kw": kw, "plate": x["no"], "group": x["group"],
                          "text": x["text"]})
    if found:
        print(f"   找到同文例 {len(found)} 条:")
        seen = set()
        for f in found:
            key = f["text"][:40]
            if key in seen:
                continue
            seen.add(key)
            print(f"     合集{f['plate']} [{f['group']}] {f['text'][:88]}")
    else:
        print(f"   未找到同文例（检索词: {kws}）")
    report.append({"glyph": r["glyph"], "label": r["label"], "freq": r["freq"],
                   "plate": r["plate"], "group": r["group"], "ob": r["ob"],
                   "keywords": kws, "parallels": found})

json.dump(report, open(os.path.join(RES, "parallels.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"\n[写出] result/parallels.json")
