# -*- coding: utf-8 -*-
"""定位重点候选所在的甲骨片与辞例，准备切原拓"""
import io, json, os, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
cp = lambda l: mc.get(l, {}).get("codepoint") or "?"

occ = collections.defaultdict(list)
for p in data:
    nm = p.get("RubbingName")
    for gi, g in enumerate(p.get("RecordUtilSentenceGroupVoList") or []):
        chars = [c for c in (g.get("RecordUtilOracleCharVoList") or []) if c.get("Label")]
        seq = sorted(chars, key=lambda c: c.get("OrderNumber") or 0)
        toks = [cp(c["Label"]) for c in seq]
        for i, c in enumerate(seq):
            occ[c["Label"]].append({
                "piece": nm, "rubbing": p.get("Rubbing"), "facsimile": p.get("Facsimile"),
                "pos": c.get("Position"), "cat": g.get("GroupCategory"),
                "seq": toks, "idx": i,
                "left": toks[i - 1] if i > 0 else None,
                "right": toks[i + 1] if i < len(toks) - 1 else None,
            })

for lab in ["fybnj2savm", "ptd0rmmnrv", "mepmffeebh", "p3q8m2xk7v"]:
    if lab not in occ:
        continue
    print("=" * 96)
    print(f"{lab}  ({cp(lab)})  共 {len(occ[lab])} 处")
    print("=" * 96)
    for o in occ[lab][:12]:
        print(f"  片 {o['piece']}  位置 {o['pos']}  类 {o['cat']}")
        print(f"     辞例: " + " ".join(("【□】" if i == o["idx"] else t) for i, t in enumerate(o["seq"])))

# mepmffeebh 出现多次，看它的左右邻分布
print("\n" + "=" * 96)
print("mepmffeebh 的邻字统计（用于判断语法角色）")
print("=" * 96)
lc = collections.Counter(o["left"] for o in occ["mepmffeebh"] if o["left"])
rc = collections.Counter(o["right"] for o in occ["mepmffeebh"] if o["right"])
print(f"  出现 {len(occ['mepmffeebh'])} 次")
print(f"  左邻 Top10: {lc.most_common(10)}")
print(f"  右邻 Top10: {rc.most_common(10)}")
