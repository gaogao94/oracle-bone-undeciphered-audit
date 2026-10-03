# -*- coding: utf-8 -*-
"""
严格判据引擎 v2
================================================
修正 v1 的缺陷：
  1) v1 的上下文检验是「部分匹配即可」，导致高频字因上下文多而虚假胜出。
     v2 改为 **全上下文覆盖**：X 的每一个上下文，都必须能被 K 的某个出现位置复现。
  2) v1 未限制候选频率。v2 只允许 freq(K) ≤ 60 的低频已释字（高频常用字
     前人不可能漏；且低频字的判据才可闭合）。
  3) 加入「同上下文异标签」检验：若两个字标签的上下文完全重合，则二者极可能是
     同一字形的不同分类 —— 这本身就是可报告的发现。
"""
import io, json, os, sys, collections
import numpy as np
from PIL import Image
import zipfile
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
            sents.append({"piece": nm, "labels": [c["Label"] for c in seq],
                          "chars": [cp(c["Label"]) or "◻" for c in seq]})
freq = collections.Counter()
for s in sents:
    freq.update(s["labels"])
is_anon = lambda l: (mc.get(l, {}).get("transcription") or []) == []
anon = [l for l in freq if is_anon(l)]
decoded = [l for l in freq if not is_anon(l) and cp(l)]
print(f"未释 {len(anon)}｜已释 {len(decoded)}")


def ctxset(lab, w=2):
    """该字每个出现位置的上下文（左右各 w 字的字符串，本字位为 □）"""
    out = []
    for s in sents:
        L, C = s["labels"], s["chars"]
        for i, x in enumerate(L):
            if x != lab:
                continue
            lo, hi = max(0, i - w), min(len(C), i + w + 1)
            out.append(tuple("□" if k == i else C[k] for k in range(lo, hi)))
    return out


def covered_by(pat, k_lab, w=2):
    """pat 去掉本字位后，是否与 K 某个出现位置的同样窗口逐字相同"""
    tgt = [t for t in pat if t != "□"]
    for s in sents:
        L, C = s["labels"], s["chars"]
        for i, x in enumerate(L):
            if x != k_lab:
                continue
            lo, hi = max(0, i - w), min(len(C), i + w + 1)
            win = [C[k] for k in range(lo, hi)]
            src = [t for t in win if True]
            if len(pat) != len(win):
                continue
            a = [t for k, t in enumerate(pat) if k != pat.index("□")]
            b = [t for k, t in enumerate(win) if k != i - lo]
            if a == b:
                return True
    return False


print("\n" + "=" * 100)
print("严格检验 v2：未释字 × 低频已释字（freq≤60）")
print("=" * 100)

LOWK = [k for k in decoded if freq[k] <= 60]
print(f"低频已释字池: {len(LOWK)} 个")

results = []
for x in anon:
    cx = ctxset(x)
    if not cx:
        continue
    full = []
    for k in LOWK:
        if freq[k] < freq[x]:
            continue
        # 全部上下文都要能覆盖
        if all(covered_by(p, k) for p in cx):
            full.append(k)
    if full:
        results.append({"label": x, "glyph": cp(x) or x, "freq": freq[x],
                        "n_ctx": len(cx), "cands": [(cp(k), freq[k], k) for k in full]})

results.sort(key=lambda r: (-r["n_ctx"], r["freq"]))
print(f"\n通过「全上下文覆盖」的未释字: {len(results)} 个\n")
for r in results[:30]:
    cs = ", ".join(f"{c}({f})" for c, f, _ in r["cands"][:5])
    print(f"  {r['glyph']:>3} freq={r['freq']} ctx={r['n_ctx']}  → {cs}")

json.dump([{**r, "cands": [{"char": c, "k_freq": f, "label": l} for c, f, l in r["cands"]]}
           for r in results],
          open(os.path.join(RES, "strict_v2.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---------------- 同上下文异标签检验 ----------------
print("\n" + "=" * 100)
print("同上下文异标签检验（发现可能被拆分/误分的字形）")
print("=" * 100)
ctx2lab = collections.defaultdict(set)
for l in freq:
    for p in ctxset(l):
        ctx2lab[p].add(l)
pairs = collections.Counter()
for p, ls in ctx2lab.items():
    if len(ls) > 1:
        L = sorted(ls)
        for i in range(len(L)):
            for j in range(i + 1, len(L)):
                pairs[(L[i], L[j])] += 1
print(f"共享上下文的位置组合: {len(pairs)} 组")
shown = 0
for (a, b), n in pairs.most_common(40):
    if a in anon or b in anon:
        print(f"  {cp(a) or a}（{freq[a]}次） × {cp(b) or b}（{freq[b]}次）  共享 {n} 个上下文"
              f"   {'[未释]' if a in anon or b in anon else ''}")
        shown += 1
        if shown >= 25:
            break
json.dump([{"a": cp(a), "b": cp(b), "n": n, "a_anon": a in set(anon), "b_anon": b in set(anon)}
           for (a, b), n in pairs.most_common(200)],
          open(os.path.join(RES, "shared_context_pairs.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n[写出] result/strict_v2.json, result/shared_context_pairs.json")
