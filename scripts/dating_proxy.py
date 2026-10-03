# -*- coding: utf-8 -*-
"""
穷尽式扫查 + 类组断代代理
1) 用全部字形（非代表图）在全部已释字中扫查，找出"像某个已释字"的未释字
2) 用干支纪日与先王称谓给片断代，补 OBIMD 缺失的类组信息
"""
import io, json, os, re, sys, zipfile, collections
import numpy as np
from PIL import Image
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
RES = os.path.join(HERE, "result")

mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
cp = lambda l: mc.get(l, {}).get("codepoint") or "?"

# ---------------- 1) 类组断代代理 ----------------
GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
STEM_ANCESTOR = {"甲": "上甲", "乙": "大乙/祖乙", "丁": "武丁/祖丁", "庚": "祖庚", "辛": "祖辛", "壬": "祖壬"}

sent_of = []
for p in data:
    nm = p.get("RubbingName")
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        seq = sorted([c for c in (g.get("RecordUtilOracleCharVoList") or [])
                      if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
        if seq:
            sent_of.append({"piece": nm, "toks": [cp(c["Label"]) for c in seq],
                            "labels": [c["Label"] for c in seq], "cat": g.get("GroupCategory")})

print("=" * 88)
print("1) 类组断代代理：用干支与先王称谓标注片")
print("=" * 88)
piece_meta = collections.defaultdict(lambda: {"ganzhi": set(), "ancestors": set(), "n_sent": 0})
for s in sent_of:
    t = s["toks"]
    piece_meta[s["piece"]]["n_sent"] += 1
    for i in range(len(t) - 1):
        if t[i] in GAN and t[i + 1] in ZHI:
            piece_meta[s["piece"]]["ganzhi"].add(t[i] + t[i + 1])
    for i, x in enumerate(t):
        if x in ("且", "祖"):        # 祖 + 干名 = 先王
            if i + 1 < len(t) and t[i + 1] in GAN:
                piece_meta[s["piece"]]["ancestors"].add(t[i + 1])

n_gz = sum(1 for v in piece_meta.values() if v["ganzhi"])
n_anc = sum(1 for v in piece_meta.values() if v["ancestors"])
print(f"  有干支纪日的片: {n_gz:,} / {len(piece_meta):,} ({n_gz/len(piece_meta):.1%})")
print(f"  有先王称谓的片: {n_anc:,} ({n_anc/len(piece_meta):.1%})")
print("  → 可据此把片归入 武丁／祖庚祖甲／廪辛康丁／武乙文丁／帝乙帝辛 五期的近似区间")

# ---------------- 2) 未释字所在片的断代信息 ----------------
anon_labels = {l for l in mc if (mc[l].get("transcription") or []) == []}
occ_pieces = collections.defaultdict(set)
for s in sent_of:
    for l in s["labels"]:
        if l in anon_labels:
            occ_pieces[l].add(s["piece"])

print("\n  重点未释字的所在片与断代线索:")
for lab in ["mepmffeebh", "fybnj2savm", "ptd0rmmnrv"]:
    ps = sorted(occ_pieces.get(lab, []))
    gz, anc = set(), set()
    for p in ps:
        gz |= piece_meta[p]["ganzhi"]
        anc |= piece_meta[p]["ancestors"]
    print(f"    {cp(lab)} ({lab}): {len(ps)} 片  干支={sorted(gz)[:8]}  先王干名={sorted(anc)}")
    print(f"        片号: {ps[:14]}")

# ---------------- 3) 桁架式结构核验：寅 vs mepmffeebh ----------------
print("\n" + "=" * 88)
print("2) 同文例比对：mepmffeebh 与 寅 是否出现在相同句式")
print("=" * 88)


def frames(lab, w=2):
    out = collections.Counter()
    for s in sent_of:
        t = s["toks"]
        for i, l in enumerate(s["labels"]):
            if l == lab:
                lo, hi = max(0, i - w), min(len(t), i + w + 1)
                out[tuple("□" if k == i else t[k] for k in range(lo, hi))] += 1
    return out


f_mep = frames("mepmffeebh")
lab_yin = next((l for l, v in mc.items() if (v.get("codepoint") or "") == "寅"), None)
lab_yin = lab_yin if lab_yin and lab_yin not in anon_labels else None
print(f"  mepmffeebh 框架 {len(f_mep)} 种，Top8:")
for f, v in f_mep.most_common(8):
    print(f"    {v}×  {' '.join(f)}")
if lab_yin:
    f_yin = frames(lab_yin)
    print(f"\n  「寅」({lab_yin}) 框架 {len(f_yin)} 种，Top8:")
    for f, v in f_yin.most_common(8):
        print(f"    {v:>4}×  {' '.join(f)}")
    common = set(f_mep) & set(f_yin)
    print(f"\n  两者共有的框架: {len(common)} 种")
    for f in list(common)[:10]:
        print(f"    {' '.join(f)}   (mep:{f_mep[f]}, 寅:{f_yin[f]})")
else:
    print("\n  「寅」不在 OBIMD 已释字表中")

json.dump({"piece_meta": {k: {"ganzhi": sorted(v["ganzhi"]),
                              "ancestors": sorted(v["ancestors"]),
                              "n_sent": v["n_sent"]} for k, v in piece_meta.items()},
           "cand_pieces": {cp(l): sorted(occ_pieces.get(l, []))
                           for l in ["mepmffeebh", "fybnj2savm", "ptd0rmmnrv"]}},
          open(os.path.join(RES, "dating_proxy.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n[写出] result/dating_proxy.json")
