# -*- coding: utf-8 -*-
"""
批量核查：OBIMD 的「未释字」是真未释，还是只是该数据集漏标？
方法：
  1. 取未释字 X 所在片的 OBIMD 辞例（其余字皆已释）
  2. 该片号 n → 《合集》n 的释文（位置一一对应）
  3. 按模式匹配定位 X 在《合集》释文中的对应字
先做高频未释字（出现 ≥10 次），因为它在多片出现，可交叉验证。
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

# 片 -> 辞例列表
pieces = collections.defaultdict(list)
freq = collections.Counter()
for p in data:
    nm = p.get("RubbingName") or ""
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        seq = sorted([c for c in (g.get("RecordUtilOracleCharVoList") or [])
                      if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
        if seq:
            labs = [c["Label"] for c in seq]
            pieces[nm].append(labs)
            freq.update(labs)

HI = sorted((l for l in freq if is_anon(l) and freq[l] >= 10), key=lambda l: -freq[l])
print(f"高频未释字（≥10 次）：{len(HI)} 个")
print(f"涉及片数：{len({p for l in HI for p in pieces})}")

# 《合集》释文缓存
PLATE = {}


def plate_text(n):
    if n in PLATE:
        return PLATE[n]
    try:
        rows, _ = gxds2.query(n, maxpages=1)
    except Exception as e:
        rows = []
    PLATE[n] = rows
    return rows


print("\n" + "=" * 104)
print("核查：未释字在《合集》释文中对应什么字")
print("=" * 104)
report = []
for lab in HI:
    g = cp(lab) or lab
    hits = []
    for nm, sents in pieces.items():
        for labs in sents:
            if lab not in labs:
                continue
            num = nm.lstrip("H")
            if not num.isdigit():
                continue
            rows = plate_text(num)
            if not rows:
                continue
            # 《合集》该片释文合并
            corpus = " ".join(r["text"] for r in rows)
            grp = rows[0]["group"]
            # OBIMD 辞例中的其余字
            idx = labs.index(lab)
            others = [cp(x) for x in labs if x != lab and cp(x)]
            hits.append({"piece": nm, "group": grp, "ob": " ".join(cp(x) or "□" for x in labs),
                         "others": others, "corpus": corpus, "idx": idx,
                         "n_others": len(others)})
    # 汇总类组
    gs = collections.Counter(h["group"] for h in hits if h["group"])
    print(f"\n■ {g}（label={lab}，{freq[lab]} 次）—— 查到 {len(hits)} 片")
    print(f"   类组分布: {dict(gs)}")
    for h in hits[:4]:
        print(f"   片 {h['piece']} [{h['group']}]")
        print(f"      OBIMD : {h['ob']}")
        print(f"      合集  : {h['corpus'][:96]}")
    report.append({"glyph": g, "label": lab, "freq": freq[lab],
                   "groups": dict(gs), "hits": hits})

json.dump(report, open(os.path.join(RES, "hi_freq_check.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"\n[写出] result/hi_freq_check.json")
