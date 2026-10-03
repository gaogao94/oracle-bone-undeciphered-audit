# -*- coding: utf-8 -*-
"""核对辞例口径，确保方法文档里的数字与 OBIMD 官方口径一致"""
import io, json, os, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))

tot_groups = 0
cat = collections.Counter()
with_chars = 0
sent_cats = 0
for p in data:
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        tot_groups += 1
        c = g.get("GroupCategory")
        cat[c] += 1
        ch = g.get("RecordUtilOracleCharVoList") or []
        if ch:
            with_chars += 1
        if c and c.startswith("InscriptionSentence"):
            sent_cats += 1

print(f"片数                     {len(data):,}")
print(f"句组总数（Group 条目）    {tot_groups:,}")
print(f"  其中 GroupCategory 以 InscriptionSentence 开头: {sent_cats:,}")
print(f"  其中有字符的             {with_chars:,}")
print("\nGroupCategory 取值分布:")
for k, v in cat.most_common():
    print(f"  {k}: {v:,}")

# 按 OrderNumber 去重后能构成的最长序列数（真正的"辞例"）
seqs = 0
for p in data:
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        ch = [c for c in (g.get("RecordUtilOracleCharVoList") or []) if c.get("Label")]
        if ch:
            seqs += 1
print(f"\n含 ≥1 个有标签字符的句组  {seqs:,}  ← 本方法使用的口径")

# README 称 21,941 sentences + 4,192 non-sentential
print(f"\nREADME 口径: 21,941 sentences + 4,192 non-sentential = {21941+4192:,}")
print(f"本数据句组总数: {tot_groups:,}")
print(f"差额: {21941+4192-tot_groups:,}")
