# -*- coding: utf-8 -*-
"""
框架法（有效方法）系统化：为全部 243 个未释字产出候选清单
================================================
本会话已证实：七套图像度量均无判别力（跨类最高 IoU 与同类变异同量级）。
仍然有效的判据只有两类：
  (1) 辞例框架的互斥/相容检验（可证伪）
  (2) 结构比例指标（在特定构形上有效，如「框体位置与比例」）
本脚本只走这两条，输出可复核的候选表。
"""
import io, json, os, sys, collections, zipfile
import numpy as np
from PIL import Image
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
RES = os.path.join(HERE, "result")
ZS = zipfile.ZipFile(os.path.join(OB, "subchar_images.zip"))
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
cp = lambda l: mc.get(l, {}).get("codepoint") or ""

by_label = collections.defaultdict(list)
for n in ZS.namelist():
    if n.lower().endswith(".png"):
        p = n.split("/")
        if len(p) >= 4:
            by_label.setdefault(p[1], []).append(n)

sents = []
for p in data:
    nm = p.get("RubbingName")
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        seq = sorted([c for c in (g.get("RecordUtilOracleCharVoList") or [])
                      if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
        if seq:
            sents.append((nm, [c["Label"] for c in seq]))
freq = collections.Counter()
for _, s in sents:
    freq.update(s)
is_anon = lambda l: (mc.get(l, {}).get("transcription") or []) == []
anon = [l for l in freq if is_anon(l)]
decoded = [l for l in freq if not is_anon(l) and cp(l)]
print(f"未释 {len(anon)}｜已释 {len(decoded)}")

W = 2
key_to_labels = collections.defaultdict(set)
ctx_of = collections.defaultdict(list)
for nm, L in sents:
    C = [cp(x) or "◻" for x in L]
    n = len(C)
    for i, x in enumerate(L):
        lo, hi = max(0, i - W), min(n, i + W + 1)
        win = list(C[lo:hi])
        key = tuple(t for k, t in enumerate(win) if k != i - lo)
        key_to_labels[key].add(x)
        ctx_of[x].append(tuple("□" if k == i else C[k] for k in range(lo, hi)))

# 低频已释字池（前人不会漏高频常用字）
pool = [k for k in decoded if freq[k] <= 60]
print(f"低频已释字池（≤60 次）: {len(pool)}")

rows = []
for x in anon:
    wins = ctx_of.get(x, [])
    if not wins:
        continue
    keys = [tuple(t for t in w if t != "□") for w in wins]
    common = None
    for kk in keys:
        s = key_to_labels.get(kk, set())
        common = set(s) if common is None else (common & s)
        if not common:
            break
    if not common:
        continue
    cands = sorted([k for k in common if k != x and k in pool], key=lambda k: freq[k])
    if not cands:
        continue
    rows.append({
        "label": x, "glyph": cp(x) or x, "freq": freq[x], "n_ctx": len(wins),
        "contexts": [" ".join(w) for w in wins[:4]],
        "cands": [{"char": cp(k), "freq": freq[k]} for k in cands[:6]],
        "n_cands": len(cands),
    })

rows.sort(key=lambda r: (r["n_cands"], -r["n_ctx"], r["freq"]))
print("\n" + "=" * 100)
print("框架法结果：候选数最少、上下文最多者优先")
print("=" * 100)
print(f"{'未释字':>4}{'次数':>5}{'上下文':>7}{'候选数':>7}  辞例 / 候选")
for r in rows[:30]:
    cs = ", ".join(f"{c['char']}({c['freq']})" for c in r["cands"][:4])
    ctx = r["contexts"][0] if r["contexts"] else ""
    print(f"{r['glyph']:>4}{r['freq']:>5}{r['n_ctx']:>7}{r['n_cands']:>7}  {ctx:<22} {cs}")

json.dump(rows, open(os.path.join(RES, "frame_method_all.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"\n通过框架法的未释字 {len(rows)} 个")
print("[写出] result/frame_method_all.json")
