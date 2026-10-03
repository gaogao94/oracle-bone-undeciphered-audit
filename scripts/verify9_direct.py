# -*- coding: utf-8 -*-
"""
核实 9 条「最强判定」：直接取《合集》原片释文，逐字核对
不依赖任何自动对齐——人工目验《合集》释文，看该位置究竟是什么字。
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

CASES = [
    ("mepmffeebh", "553", "黃", "以·□·執"),
    ("uhz6qrd2d9", "5373", "安", "不·□·亡"),
    ("󱼮", "32513", "豲", "五·□·茲"),
    ("󹧹", "32009", "宓", "卜·□·芻"),
    ("󾟷", "22454", "丘", "叀·□·豕"),
    ("󲌬", "32512", "豲", "五·□·茲"),
    ("󾥗", "17382", "娩", "月·□·不"),
    ("󻫐", "31983", "西", "于·□·若"),
    ("󹛟", "33286", "龜", "叀·□·先"),
]
label_of_glyph = {}
for lab, v in mc.items():
    c = v.get("codepoint") or ""
    if c:
        label_of_glyph[c] = lab

print("=" * 104)
print("逐条核实：《合集》原片释文 vs OBIMD 辞例")
print("=" * 104)
report = []
for g, plate, cand, pattern in CASES:
    lab = label_of_glyph.get(g)
    print(f"\n{'─'*104}")
    print(f"【{g}】判为「{cand}」  片《合集》{plate}  模式 {pattern}")
    print(f"{'─'*104}")
    # OBIMD 该片辞例
    obs = []
    for p in data:
        if (p.get("RubbingName") or "").lstrip("H") == plate:
            for gg in p.get("RecordUtilSentenceGroupVoList") or []:
                seq = sorted([c for c in (gg.get("RecordUtilOracleCharVoList") or [])
                              if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
                if seq:
                    labs = [c["Label"] for c in seq]
                    s = " ".join(cp(c["Label"]) or "□" for c in seq)
                    mark = ""
                    if lab in labs:
                        i = labs.index(lab)
                        s = " ".join("【□】" if k == i else (cp(c["Label"]) or "□")
                                     for k, c in enumerate(seq))
                        mark = "  ← 目标字所在"
                    obs.append(s + mark)
    print("  OBIMD:")
    for s in obs:
        print(f"     {s}")
    # 合集原文
    try:
        rows, _ = gxds2.query(plate, maxpages=1)
    except Exception as e:
        print(f"  抓取失败: {e}")
        continue
    print("  《合集》释文（原文）:")
    for r in rows:
        print(f"     [{r['group']}] {r['text']}")
    # 候选字是否在释文中出现
    alltext = " ".join(r["text"] for r in rows)
    present = cand in alltext
    print(f"  → 候选字「{cand}」在《合集》该片释文中：{'**出现**' if present else '**未出现**'}")
    if present:
        for m in re.finditer(re.escape(cand), alltext):
            a = max(0, m.start() - 25)
            print(f"       上下文: …{alltext[a:m.start()+25]}…")
    report.append({"glyph": g, "plate": plate, "cand": cand, "pattern": pattern,
                   "ob_terms": obs, "corpus": [r["text"] for r in rows],
                   "corpus_group": rows[0]["group"] if rows else "",
                   "cand_present": present})

json.dump(report, open(os.path.join(RES, "verify9_direct.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
n_present = sum(1 for r in report if r["cand_present"])
print(f"\n{'='*104}")
print(f"汇总：{n_present}/{len(report)} 条的候选字在《合集》原片中直接出现")
print(f"[写出] result/verify9_direct.json")
