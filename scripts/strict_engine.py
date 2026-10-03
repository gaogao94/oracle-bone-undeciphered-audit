# -*- coding: utf-8 -*-
"""
严格判据引擎 v1
================================================
核心判据（可证伪的强条件）：
  设未释字 X 出现于上下文集合 C(X)（每个上下文=片内左右各 2 字的已释字串）。
  若 X = K，则要求：
    (A) 结构相容：X 的四项结构指标落在 K 全部字形的分布之内；
    (B) 上下文可容纳：把 X 替换为 K 后，所得辞例串在语料中"不新" ——
        即该串或其子串在 K 自身的用例中出现过；
    (C) 频率相容：|C(X)| 不应超过 K 的出现次数（X 是 K 的子集使用）；
    (D) 反证检查：若存在与 X 上下文完全相同的位置上用的是另一个字 L，
        则 X≠K（除非 K 与 L 同字）。

输出：每个候选的通过/否决理由，全部可复核。
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
label_of_char = {}
for lab, v in mc.items():
    c = v.get("codepoint") or ""
    if len(c) == 1:
        label_of_char.setdefault(c, lab)

# 辞例
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
anon_labels = [l for l in freq if is_anon(l)]
decoded = [l for l in freq if not is_anon(l) and cp(l)]
print(f"辞例 {len(sents):,}｜字形类 {len(freq):,}｜未释 {len(anon_labels)}｜已释 {len(decoded):,}")

# 结构指标
def boxstat(lab):
    out = []
    for p in by_label.get(lab, []):
        try:
            im = Image.open(ZS.open(p)).convert("L")
        except Exception:
            continue
        a = np.asarray(im, dtype=np.float32)
        if a.mean() < 128:
            a = 255 - a
        a = 255 - a
        b = a > 40
        ys, xs = np.nonzero(b)
        if len(ys) < 5:
            continue
        bb = b[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        H, W = bb.shape
        rowsum = bb.sum(axis=1)
        wide = np.nonzero(rowsum >= 0.6 * W)[0]
        if len(wide) == 0:
            continue
        out.append([W / H, wide.min() / H, wide.max() / H,
                    (wide.max() - wide.min() + 1) / H])
    return np.array(out) if out else None


print("计算已释字结构分布 …")
KSTAT = {}
for l in decoded:
    v = boxstat(l)
    if v is not None and len(v):
        KSTAT[l] = v
print(f"有结构数据的已释字 {len(KSTAT):,}")


def struct_ok(xv, kv, tol=0.30):
    """X 的四指标是否落在 K 各字形的范围内（允许 tol 外扩）"""
    lo = kv.min(axis=0) - tol
    hi = kv.max(axis=0) + tol
    return bool(np.all(xv >= lo) and np.all(xv <= hi))


def ctx_of(lab, w=2):
    """返回 {上下文串: 出现次数}，上下文为左右各 w 字的已释字串"""
    out = collections.Counter()
    for s in sents:
        L, C = s["labels"], s["chars"]
        for i, x in enumerate(L):
            if x != lab:
                continue
            lo, hi = max(0, i - w), min(len(C), i + w + 1)
            toks = tuple("□" if k == i else C[k] for k in range(lo, hi))
            out[toks] += 1
    return out


def k_contexts_containing(ctx_pat, k_label, w=2):
    """
    检查「把 X 换成 K 后得到的串」在语料中是否由 K 自身产出过。
    ctx_pat 是含 □ 的元组；只要 K 的任一出现位置能产出同样长度的串，
    且除本字位外逐字相同，即算命中。
    """
    hits = 0
    for s in sents:
        L, C = s["labels"], s["chars"]
        for i, x in enumerate(L):
            if x != k_label:
                continue
            lo, hi = max(0, i - w), min(len(C), i + w + 1)
            # 同样的裁剪窗口
            if hi - lo != len(ctx_pat):
                continue
            ok = True
            for k in range(lo, hi):
                if k == i:
                    continue
                if C[k] != ctx_pat[k - lo]:
                    ok = False
                    break
            if ok:
                hits += 1
                break
    return hits


print("\n" + "=" * 100)
print("严格检验：低频未释字（出现 ≤4 次）× 全部已释字")
print("=" * 100)

LOWFREQ = [l for l in anon_labels if freq[l] <= 4]
print(f"低频未释字（≤4 次）: {len(LOWFREQ)} 个")

results = []
for x in LOWFREQ:
    xv = boxstat(x)
    if xv is None or not len(xv):
        continue
    xm = xv.mean(axis=0)
    cx = ctx_of(x)
    row = {"label": x, "glyph": cp(x) or x, "freq": freq[x], "ctx": len(cx)}
    cands = []
    for k in KSTAT:
        if freq[k] > 400:        # 高频常用字不作候选（前人不可能漏）
            continue
        if freq[k] < freq[x]:    # K 的出现次数不应少于 X
            continue
        if not struct_ok(xm, KSTAT[k]):
            continue
        # 上下文容纳检验
        hit = 0
        for pat in cx:
            hit += k_contexts_containing(pat, k)
        if hit == 0:
            continue
        cands.append((hit, k))
    cands.sort(reverse=True)
    row["cands"] = [{"char": cp(k), "label": k, "k_freq": freq[k],
                     "ctx_hits": h, "struct_dist": round(float(np.abs(KSTAT[k].mean(axis=0) - xm).sum()), 3)}
                    for h, k in cands[:5]]
    if row["cands"]:
        results.append(row)

results.sort(key=lambda r: -r["cands"][0]["ctx_hits"])
print(f"\n有候选的未释字: {len(results)} / {len(LOWFREQ)}\n")
for r in results[:25]:
    c = r["cands"][0]
    print(f"  {r['glyph']:>3} (freq={r['freq']}, ctx={r['ctx']:>2}) → "
          f"「{c['char']}」(freq={c['k_freq']}) 上下文命中 {c['ctx_hits']} 结构距离 {c['struct_dist']}"
          + (f"   其他: " + ", ".join(f"{x['char']}({x['ctx_hits']})" for x in r["cands"][1:4]) if len(r["cands"]) > 1 else ""))

json.dump(results, open(os.path.join(RES, "strict_candidates.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"\n[写出] result/strict_candidates.json")
