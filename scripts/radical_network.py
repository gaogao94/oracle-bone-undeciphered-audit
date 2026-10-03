# -*- coding: utf-8 -*-
"""1) 查 OBIMD 仓库文件清单，定位图像真实路径
   2) 深挖殷契文渊字形库的「多部首」结构 —— 这可能是现成的部件标注"""
import io, json, os, sys, collections, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
H = {"User-Agent": "Mozilla/5.0"}

print("=== 1) OBIMD 仓库文件清单 ===")
for api in ["https://hf-mirror.com/api/datasets/KLOBIP/OBIMD",
            "https://hf-mirror.com/api/datasets/KLOBIP/OBIMD/tree/main"]:
    try:
        r = urllib.request.urlopen(urllib.request.Request(api, headers=H), timeout=30)
        j = json.loads(r.read().decode("utf-8"))
        if isinstance(j, dict) and "siblings" in j:
            sib = [s["rfilename"] for s in j["siblings"]]
            print(f"  {api} -> {len(sib)} 个文件")
            for s in sib[:40]:
                print("     ", s)
            # 统计图像前缀
            pref = collections.Counter(s.split("/")[0] for s in sib if "/" in s)
            print("  顶层目录分布:", dict(pref.most_common(12)))
            break
        if isinstance(j, list):
            print(f"  {api} -> {len(j)} 项")
            for it in j[:40]:
                print("     ", it.get("type"), it.get("path"), it.get("size"))
            break
    except Exception as e:
        print(f"  {api} ERR {type(e).__name__} {str(e)[:60]}")

print("\n=== 2) 殷契文渊字形库：多部首结构分析 ===")
DZ = json.load(open(os.path.join(D, "DZ.json"), encoding="utf-8"))
byzk = collections.defaultdict(set)
rad_chars = collections.defaultdict(set)
for r in DZ:
    byzk[r["ZKBM"]].add(r["BSBM"])
    if r["FTZ"]:
        rad_chars[r["BSBM"]].add(r["FTZ"])

sizes = collections.Counter(len(v) for v in byzk.values())
print(f"  字形码 {len(byzk)} 个；归属部首数分布: {dict(sorted(sizes.items()))}")
multi = {k: v for k, v in byzk.items() if len(v) >= 2}
print(f"  归属 ≥2 个部首的字形码: {len(multi)} ({len(multi)/len(byzk):.1%})")

# 取一个有多个部首的例子看它到底归在哪些类下
for zk, bs in list(multi.items())[:6]:
    labels = sorted({r["FTZ"] for r in DZ if r["ZKBM"] == zk and r["FTZ"]})
    print(f"    {zk}: {len(bs)} 个部首 {sorted(bs)}  隶定={labels}")

print("\n=== 3) 部首共现网络（= 部件/偏旁相关性）===")
co = collections.Counter()
for zk, bs in byzk.items():
    bl = sorted(bs)
    for i in range(len(bl)):
        for j in range(i + 1, len(bl)):
            co[(bl[i], bl[j])] += 1
print(f"  部首对 {len(co)} 种，共现 ≥5 次的 {sum(1 for v in co.values() if v>=5)} 种")
print("  最强共现的部首对（前 15）：")
for (a, b), v in co.most_common(15):
    ea = "、".join(sorted(rad_chars[a])[:6])
    eb = "、".join(sorted(rad_chars[b])[:6])
    print(f"    {a} × {b}: {v:>4} 次   [{ea}] × [{eb}]")

# 部首之间的相似度矩阵（Jaccard）
print("\n=== 4) 部首相似度（Jaccard，用于偏旁族判定）===")
rad_sets = {r: rad_chars[r] for r in rad_chars if len(rad_chars[r]) >= 3}
names = list(rad_sets)
pairs = []
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        a, b = names[i], names[j]
        s = rad_sets[a] & rad_sets[b]
        u = rad_sets[a] | rad_sets[b]
        if len(s) >= 3:
            pairs.append((len(s) / len(u), a, b, len(s)))
pairs.sort(reverse=True)
print(f"  部首对（共享 ≥3 个隶定字）{len(pairs)} 组；相似度最高的 12 组：")
for jac, a, b, n in pairs[:12]:
    shared = "、".join(sorted(rad_sets[a] & rad_sets[b])[:8])
    print(f"    {a} ~ {b}: Jaccard={jac:.3f} 共享 {n} 字  [{shared}]")

json.dump({"radical_cooccurrence": {f"{a}|{b}": v for (a, b), v in co.most_common(300)},
           "radical_similarity": [{"a": a, "b": b, "jaccard": round(j, 4), "shared": n}
                                  for j, a, b, n in pairs[:300]]},
          open(os.path.join(HERE, "result", "radical_network.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n[写出] result/radical_network.json")
