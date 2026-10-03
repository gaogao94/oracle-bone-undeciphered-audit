# -*- coding: utf-8 -*-
"""
校验上一轮 167 条「合集解出」：邻字一致性
判据：若对齐正确，候选字 k 在《合集》全库中应常与该位置的邻字搭配。
      分别统计 k 的「前邻」「后邻」在《合集》中的出现次数（用已抓取的字检索页）。
另：对每条给出「OBIMD 邻字是否在同一片释文中出现」的局部证据（更可靠）。
"""
import io, os, re, sys, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import gxds2

RES = os.path.join(_HERE, "result")
recs = json.load(open(os.path.join(RES, "align_records.json"), encoding="utf-8"))
solved = [r for r in recs if r["status"] == "合集解出"]
print(f"待校验 {len(solved)} 条\n")

PLACE = set("※□■…〔〕()（）")


def norm(t):
    t = re.sub(r"（[^）]*）|\([^)]*\)|〔[^〕]*〕|【[^】]*】", "", t)
    return [ch for ch in t if ch not in "，。：；、？！,.;:?!　 \t"]


print("=" * 108)
print("局部校验：OBIMD 邻字是否出现在《合集》同片释文中，且与候选字相邻")
print("=" * 108)
ok, bad, unclear = [], [], []
for r in solved:
    toks = r["ob"].split()
    i = r["ob_idx"]
    cand = r["corpus_resolved"]
    left = toks[i - 1] if i > 0 else None
    right = toks[i + 1] if i + 1 < len(toks) else None
    cr = norm(r["corpus_full"])
    # 在《合集》释文中找 cand，看其左右是否与 OBIMD 邻字一致
    hit = None
    for j, ch in enumerate(cr):
        if ch != cand:
            continue
        lc = cr[j - 1] if j > 0 else None
        rc = cr[j + 1] if j + 1 < len(cr) else None
        score = (1 if left and lc == left else 0) + (1 if right and rc == right else 0)
        if hit is None or score > hit[0]:
            hit = (score, lc, rc)
    rec = {"glyph": r["glyph"], "freq": r["freq"], "plate": r["plate"],
           "group": r["group"], "cand": cand, "left": left, "right": right,
           "corpus_left": hit[1] if hit else None, "corpus_right": hit[2] if hit else None,
           "score": hit[0] if hit else -1}
    if not hit or hit[0] == 0:
        bad.append(rec)
    elif hit[0] == 2 or (hit[0] == 1 and (not left or not right)):
        ok.append(rec)
    else:
        unclear.append(rec)

print(f"\n邻字一致（可信）  : {len(ok)}")
print(f"邻字不一致（伪解）: {len(bad)}")
print(f"部分一致（待核）  : {len(unclear)}")

print("\n" + "=" * 108)
print("可信的「合集解出」（邻字吻合）")
print("=" * 108)
seen = set()
for r in ok:
    if r["glyph"] in seen:
        continue
    seen.add(r["glyph"])
    print(f"  {r['glyph']:>4}（{r['freq']}次）片{r['plate']} [{r['group']}] → 「{r['cand']}」"
          f"   邻: {r['left']}·□·{r['right']}  /  合集: {r['corpus_left']}·{r['cand']}·{r['corpus_right']}")

print("\n" + "=" * 108)
print("疑似伪解（邻字不吻合）样本")
print("=" * 108)
seen2 = set()
for r in bad[:20]:
    if r["glyph"] in seen2:
        continue
    seen2.add(r["glyph"])
    print(f"  {r['glyph']:>4}（{r['freq']}次）片{r['plate']} → 候选「{r['cand']}」"
          f"   邻: {r['left']}·□·{r['right']}  /  合集实为: {r['corpus_left']}·{r['cand']}·{r['corpus_right']}")

json.dump({"ok": ok, "bad": bad, "unclear": unclear},
          open(os.path.join(RES, "verify_solved.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"\n[写出] result/verify_solved.json")
