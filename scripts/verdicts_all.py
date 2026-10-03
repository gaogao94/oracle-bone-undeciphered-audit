# -*- coding: utf-8 -*-
"""
核心判定：OBIMD「未释字」= 学界未释，还是数据集编码缺失（合文/异体）？
方法：OBIMD 片号 H<n> ↔ 《合集》编号 n。
      取未释字所在辞例，与《合集》同片释文比对——位置对应即知该字在文献中的读法。
输出每片：OBIMD 辞例、合集释文、类组、以及推测的对应字。
"""
import io, os, re, sys, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import gxds2

OB = os.path.join(_HERE, "data", "obimd")
RES = os.path.join(_HERE, "result")
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
cp = lambda l: mc.get(l, {}).get("codepoint") or ""
is_anon = lambda l: (mc.get(l, {}).get("transcription") or []) == []

freq = collections.Counter()
for p in data:
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        for c in g.get("RecordUtilOracleCharVoList") or []:
            if c.get("Label"):
                freq[c["Label"]] += 1

# 收集：未释字 -> [(片, 辞例字序列, 位置)]
occ = collections.defaultdict(list)
for p in data:
    nm = p.get("RubbingName") or ""
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        seq = sorted([c for c in (g.get("RecordUtilOracleCharVoList") or [])
                      if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
        if not seq:
            continue
        labs = [c["Label"] for c in seq]
        for i, c in enumerate(seq):
            if is_anon(c["Label"]):
                occ[c["Label"]].append((nm, i, labs))

PLATE = {}


def plate(num):
    if num not in PLATE:
        try:
            rows, _ = gxds2.query(num, maxpages=1)
        except Exception:
            rows = []
        PLATE[num] = rows
    return PLATE[num]


print("=" * 104)
print("判定：未释字 = 真未释 ／ 编码缺失")
print("=" * 104)
verdicts = []
targets = sorted(occ, key=lambda l: -freq[l])
for lab in targets:
    g = cp(lab) or lab
    entries = []
    for nm, i, labs in occ[lab][:6]:
        num = nm.lstrip("H")
        if not num.isdigit():
            continue
        rows = plate(num)
        if not rows:
            continue
        corpus = " ".join(r["text"] for r in rows)
        grp = rows[0]["group"]
        ob = " ".join(cp(x) or "□" for x in labs)
        entries.append({"piece": nm, "group": grp, "ob": ob, "corpus": corpus})
    if not entries:
        continue
    gs = collections.Counter(e["group"] for e in entries)
    verdicts.append({"glyph": g, "label": lab, "freq": freq[lab],
                     "groups": dict(gs), "entries": entries})

json.dump(verdicts, open(os.path.join(RES, "verdicts_full.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# 打印：高频前 6 + 低频抽样
show = verdicts[:6] + verdicts[20:26] + verdicts[60:66] + verdicts[120:126] + verdicts[-6:]
seen = set()
for v in show:
    if v["label"] in seen:
        continue
    seen.add(v["label"])
    print(f"\n■ {v['glyph']}（{v['freq']} 次）类组: {v['groups']}")
    for e in v["entries"][:2]:
        print(f"   片 {e['piece']} [{e['group']}]")
        print(f"      OBIMD: {e['ob']}")
        print(f"      合集 : {e['corpus'][:100]}")

print(f"\n共处理未释字 {len(verdicts)} 个")
print(f"[写出] result/verdicts_full.json")
