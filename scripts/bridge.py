# -*- coding: utf-8 -*-
"""验证桥接：OBIMD 片号 ↔ 《合集》编号，并给候选字定类组"""
import io, json, os, sys, re, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gxds_crawl import crawl, get, parse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
cp = lambda l: mc.get(l, {}).get("codepoint") or ""

# 候选所在片
TARGETS = {"fybnj2savm": "H15410", "urzeocieq8": "H2886", "ptd0rmmnrv": "H15401",
           "gx21ndp7yy": "H7371", "mepmffeebh": "H553"}
for lab, piece in TARGETS.items():
    num = piece.lstrip("H")
    print("=" * 94)
    print(f"{cp(lab) or lab}（label={lab}）所在片 {piece} → 《合集》{num}")
    print("=" * 94)
    # OBIMD 该片辞例
    ob_txt = []
    for p in data:
        if p.get("RubbingName") == piece:
            for g in p.get("RecordUtilSentenceGroupVoList") or []:
                seq = sorted([c for c in (g.get("RecordUtilOracleCharVoList") or [])
                              if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
                if seq:
                    ob_txt.append(" ".join(cp(c["Label"]) or "◻" for c in seq))
    print(f"  OBIMD 辞例: {ob_txt}")
    if not num.isdigit():
        continue
    try:
        rows = crawl(bhfl=1, q=num, tag=f"plate{num}", maxpages=1)
    except Exception as e:
        print(f"  抓取失败: {e}")
        continue
    print(f"  《合集》释文（{len(rows)} 条）:")
    for r in rows:
        print(f"     {r['src']} {r['no']}-{r['seq']}  [{r['group']}]  {r['text'][:90]}")
