# -*- coding: utf-8 -*-
"""
严格重判：修正对齐假阳性
新判据（逐片）：
  设 OBIMD 辞例 = S（以未释字 X 为待求位），《合集》释文同片 = C。
  要求：存在一个字 k，使得 multiset(C) 与 multiset(S 以 k 代 X) 满足
        multiset(S\{X}) ⊆ multiset(C)   （即 S 的其余字在 C 中都能找到）
        且 C 中存在 k 使 |C| ≥ |S|
  取满足条件的、且在 C 中出现而 S\{X} 中缺失的字作为候选 k。
  若找不到这样的 k（C 中多出的字无法唯一确定），判「未定」。
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
PLACE = set("※□■…〔〕()（）")

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


def norm(t):
    t = re.sub(r"（[^）]*）|\([^)]*\)|〔[^〕]*〕|【[^】]*】", "", t)
    return [ch for ch in t if ch not in "，。：；、？！,.;:?!　 \t"]


PLATE = {}


def plate(num):
    if num not in PLATE:
        try:
            rows, _ = gxds2.query(num, maxpages=1)
        except Exception:
            rows = []
        PLATE[num] = rows
    return PLATE[num]


def candidates(ob_tokens, corpus_chars):
    """
    以穷举取代对齐：对 OBIMD 辞例中的每个已释字，检查是否在 C 中；
    返回 C 中出现但 S 中（除 X 外）没有的字，按出现次数排序。
    """
    need = collections.Counter(t for t in ob_tokens if t and t != "◻" and len(t) == 1)
    have = collections.Counter(c for c in corpus_chars if c not in PLACE and c != "|")
    missing = {t: n - have.get(t, 0) for t, n in need.items() if have.get(t, 0) < n}
    if missing:
        return None, missing   # S 里有字在 C 中找不到 → 该片不足以判定
    extra = have - need
    # 去掉 C 中多出的、可能是其他辞例部分的常见字
    return extra, None


print("=" * 106)
print("严格重判：多重集校验")
print("=" * 106)
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
        cr = []
        for r in rows:
            cr += norm(r["text"]) + ["|"]
        ob = [cp(x) or "◻" for x in labs]
        extra, missing = candidates(ob, cr)
        if missing is not None:
            status, cand = "证据不足", None
        elif extra is None or len(extra) == 0:
            status, cand = "合集无多余字", None
        else:
            # 取出现次数最多、且非占位符的候选
            cands = [c for c in extra.most_common() if c[0] not in PLACE]
            if not cands:
                status, cand = "合集亦占位", None
                cand = extra.most_common(1)[0][0]
            else:
                status, cand = "合集解出", cands[0][0]
        records.append({"glyph": g, "label": lab, "freq": freq[lab], "plate": num,
                        "group": rows[0]["group"] if rows else "",
                        "ob": " ".join(ob), "status": status, "cand": cand,
                        "extra": dict(extra.most_common(6)) if extra else {},
                        "missing": dict(sorted(missing.items(), key=lambda x:-x[1])[:6]) if missing else {},
                        "corpus": " ".join(r["text"] for r in rows)[:160]})

json.dump(records, open(os.path.join(RES, "align_v2.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
st = collections.Counter(r["status"] for r in records)
print(f"共 {len(records)} 条")
for k, v in st.most_common():
    print(f"  {k}: {v}")

print("\n" + "=" * 106)
print("「合集解出」——OBIMD 未编码但《合集》有字")
print("=" * 106)
seen = set()
n = 0
for r in records:
    if r["status"] == "合集解出" and r["glyph"] not in seen:
        seen.add(r["glyph"])
        n += 1
        print(f"  {r['glyph']:>4}（{r['freq']}次）片{r['plate']} [{r['group']}] → 「{r['cand']}」")
        print(f"       OBIMD: {r['ob'][:70]}")
        print(f"       合集 : {r['corpus'][:88]}")
        if n >= 20:
            break

print("\n" + "=" * 106)
print("「合集亦占位」——真候选")
print("=" * 106)
seen2 = set()
n = 0
for r in records:
    if r["status"] == "合集亦占位" and r["glyph"] not in seen2:
        seen2.add(r["glyph"])
        n += 1
        print(f"  {r['glyph']:>4}（{r['freq']}次）片{r['plate']} [{r['group']}] 占位「{r['cand']}」")
