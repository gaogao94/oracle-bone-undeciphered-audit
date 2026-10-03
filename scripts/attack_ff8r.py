# -*- coding: utf-8 -*-
"""
攻 󷺊（40 次，黄组占 35）：辞例「王賓X亡祸」
求全《合集》中「王賓…亡祸/亡尤」的全部用例，看该位置用什么字。
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

TGT = "ff8rp0nh6u"   # 󷺊
print("=" * 100)
print(f"目标 󷺊 (label={TGT}) 的全部辞例")
print("=" * 100)
sents = []
for p in data:
    nm = p.get("RubbingName") or ""
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        seq = sorted([c for c in (g.get("RecordUtilOracleCharVoList") or [])
                      if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
        if seq:
            labs = [c["Label"] for c in seq]
            sents.append((nm, labs))
            if TGT in labs:
                i = labs.index(TGT)
                print(f"  {nm}: " + " ".join("【□】" if k == i else (cp(x) or "◻")
                                             for k, x in enumerate(labs)))

# 在《合集》里检索「王賓」组合
print("\n" + "=" * 100)
print("《合集》中「王賓」的用例")
print("=" * 100)
seen = {}
for kw in ["王賓", "王宾"]:
    try:
        rows, total = gxds2.query(kw, maxpages=3)
    except Exception as e:
        print(f"  检索 {kw} 失败: {e}")
        continue
    print(f"  「{kw}」命中 {len(rows)} 行 / {total} 页")
    for r in rows:
        key = (r["no"], r["seq"])
        if key in seen:
            continue
        seen[key] = r
        print(f"     {r['no']}-{r['seq']} [{r['group']}] {r['text'][:92]}")

json.dump(list(seen.values()), open(os.path.join(RES, "wangbin.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"\n[写出] result/wangbin.json（{len(seen)} 条）")
