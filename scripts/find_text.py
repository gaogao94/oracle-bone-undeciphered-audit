# -*- coding: utf-8 -*-
"""找 OBIMD 里的辞例文本字段，看能否支撑"辞例上下文"分析"""
import io, json, os, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "obimd")
data = json.load(open(os.path.join(D, "data.json"), encoding="utf-8"))

# 1. 所有出现过的键
keys_p, keys_g, keys_c = collections.Counter(), collections.Counter(), collections.Counter()
for p in data[:2000]:
    keys_p.update(p.keys())
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        keys_g.update(g.keys())
        for c in g.get("RecordUtilOracleCharVoList") or []:
            keys_c.update(c.keys())
print("片级字段:", dict(keys_p))
print("句组级字段:", dict(keys_g))
print("字符级字段:", dict(keys_c))

# 2. 句组级除字符表外还有什么内容
p0 = data[0]
for g in p0.get("RecordUtilSentenceGroupVoList") or []:
    print("\n句组样本（去掉字符表后）:")
    print({k: (v if k != "RecordUtilOracleCharVoList" else f"<{len(v)} chars>")
           for k, v in g.items()})
    break

# 3. 找一个字段里带中文长文本的
print("\n=== 各字段取值样本（前 30 片） ===")
seen = {}
for p in data[:30]:
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        for k, v in g.items():
            if k == "RecordUtilOracleCharVoList":
                continue
            seen.setdefault(k, []).append(v)
for k, vs in seen.items():
    print(f"  {k}: {vs[:4]}")
