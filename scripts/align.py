# -*- coding: utf-8 -*-
"""
逐片对齐：OBIMD 辞例 ↔ 《合集》释文
对每个未释字，取其所在片，用序列对齐找出该位置在《合集》中对应的字。
输出：合集解出 / 合集也占位 / 无法对齐
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
occ = collections.defaultdict(list)
for p in data:
    nm = p.get("RubbingName") or ""
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        seq = sorted([c for c in (g.get("RecordUtilOracleCharVoList") or [])
                      if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
        if not seq:
            continue
        labs = [c["Label"] for c in seq]
        freq.update(labs)
        for i, c in enumerate(seq):
            if is_anon(c["Label"]):
                occ[c["Label"]].append((nm, i, labs))

# 《合集》释文规范化：去掉标点、括号内的释读、占位符
NOISE = set("，。：；、？！「」〔〕（）()…—－　 一二三四五六七八九十")
PLACEHOLDER = set("※□■…")


def norm_corpus_text(t):
    """把《合集》释文行规范成字符序列；保留占位符以备判定"""
    t = re.sub(r"（[^）]*）", "", t)      # 去掉「（貞）」这类今字标注
    t = re.sub(r"\([^)]*\)", "", t)
    t = re.sub(r"〔[^〕]*〕", "", t)
    t = re.sub(r"【[^】]*】", "", t)
    out = []
    for ch in t:
        if ch in "，。：；、？！,.;:?!　 \t":
            continue
        out.append(ch)
    return out


PLATE = {}


def plate(num):
    if num not in PLATE:
        try:
            rows, _ = gxds2.query(num, maxpages=1)
        except Exception:
            rows = []
        PLATE[num] = rows
    return PLATE[num]


def align(ob, cr):
    """
    简单全局对齐（Levenshtein），返回 ob 每个位置对应的 cr 下标或 None
    """
    n, m = len(ob), len(cr)
    INF = 10 ** 6
    dp = [[INF] * (m + 1) for _ in range(n + 1)]
    bt = [[None] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = 0
    for i in range(n + 1):
        for j in range(m + 1):
            if dp[i][j] == INF:
                continue
            if i < n and j < m:
                cost = 0 if ob[i] == cr[j] else 1
                if dp[i][j] + cost < dp[i + 1][j + 1]:
                    dp[i + 1][j + 1] = dp[i][j] + cost
                    bt[i + 1][j + 1] = (i, j, "d")
            if i < n and dp[i][j] + 1 < dp[i + 1][j]:
                dp[i + 1][j] = dp[i][j] + 1
                bt[i + 1][j] = (i, j, "u")
            if j < m and dp[i][j] + 1 < dp[i][j + 1]:
                dp[i][j + 1] = dp[i][j] + 1
                bt[i][j + 1] = (i, j, "l")
    # 回溯
    i, j = n, m
    mapping = {}
    while i > 0 or j > 0:
        b = bt[i][j]
        if b is None:
            break
        pi, pj, op = b
        if op == "d":
            mapping[pi] = pj
        i, j = pi, pj
    return mapping, dp[n][m]


print("=" * 108)
print("逐片对齐：OBIMD 未释字 ↔ 《合集》释文")
print("=" * 108)
records = []
for lab in sorted(occ, key=lambda l: -freq[l]):
    g = cp(lab) or lab
    for nm, idx, labs in occ[lab][:3]:
        num = nm.lstrip("H")
        if not num.isdigit():
            continue
        rows = plate(num)
        if not rows:
            continue
        cr_all = []
        for r in rows:
            cr_all += norm_corpus_text(r["text"]) + ["|"]
        ob = [cp(x) or "◻" for x in labs]
        mp, dist = align(ob, cr_all)
        j = mp.get(idx)
        resolved = None
        if j is not None and j < len(cr_all):
            resolved = cr_all[j]
        status = ("合集解出" if resolved and resolved not in PLACEHOLDER and resolved not in "|"
                  else "合集亦占位" if resolved in PLACEHOLDER else "未对齐")
        records.append({
            "glyph": g, "label": lab, "freq": freq[lab], "plate": num,
            "group": rows[0]["group"] if rows else "",
            "ob": " ".join(ob), "ob_idx": idx,
            "corpus_resolved": resolved, "status": status,
            "edit_dist": dist,
            "corpus_full": " ".join(r["text"] for r in rows)[:150],
        })

json.dump(records, open(os.path.join(RES, "align_records.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

st = collections.Counter(r["status"] for r in records)
print(f"共 {len(records)} 条记录")
print(f"  合集解出   : {st.get('合集解出',0)}")
print(f"  合集亦占位 : {st.get('合集亦占位',0)}")
print(f"  未对齐     : {st.get('未对齐',0)}")

print("\n" + "=" * 108)
print("「合集亦占位」的未释字（这些才可能是真未释）")
print("=" * 108)
for r in records:
    if r["status"] == "合集亦占位":
        print(f"  {r['glyph']:>4}（{r['freq']}次）片 {r['plate']} [{r['group']}]  "
              f"合集占位符号「{r['corpus_resolved']}」")
        print(f"       OBIMD: {r['ob'][:80]}")

print("\n" + "=" * 108)
print("「合集解出」的样本（这些是编码缺失，非未释字）")
print("=" * 108)
for r in [x for x in records if x["status"] == "合集解出"][:25]:
    print(f"  {r['glyph']:>4}（{r['freq']}次）片 {r['plate']} [{r['group']}] → 合集作「{r['corpus_resolved']}」")
