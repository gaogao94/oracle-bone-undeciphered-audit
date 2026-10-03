# -*- coding: utf-8 -*-
"""
OBIMD 实测 → 甲骨文语料账（不再是假设模型）
OBIMD: 10,077 片甲骨，逐字标注，Label=主字形类，SubLabel=异体子类，SeatFont=残泐占位
"""
import io, json, math, os, sys
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data", "obimd")
OUT = os.path.join(HERE, "data")

data = json.load(open(os.path.join(D, "data.json"), encoding="utf-8"))
mc = json.load(open(os.path.join(D, "main_character.json"), encoding="utf-8"))

# ---------- 1. 统计 ----------
lab, sub, seat, n_tok = Counter(), Counter(), 0, 0
n_pieces_with_text = 0
for piece in data:
    got = False
    for grp in piece.get("RecordUtilSentenceGroupVoList") or []:
        for ch in grp.get("RecordUtilOracleCharVoList") or []:
            n_tok += 1
            if ch.get("SeatFont"):
                seat += 1
                continue
            L = ch.get("Label")
            if L:
                lab[L] += 1
                got = True
            S = ch.get("SubLabel")
            if S:
                sub[S] += 1
    if got:
        n_pieces_with_text += 1

print("=" * 78)
print("第一部分：OBIMD 实测统计")
print("=" * 78)
print(f"  甲骨片数                 {len(data):,}")
print(f"  其中含可识别字的片        {n_pieces_with_text:,} "
      f"({n_pieces_with_text/len(data):.1%})")
print(f"  字符标注实例（含残泐）     {n_tok:,}")
print(f"  残泐占位（SeatFont）      {seat:,}  ({seat/n_tok:.1%})")
print(f"  有 Label 的 token         {sum(lab.values()):,}")
print(f"  主字形类（Label）         {len(lab):,}")
print(f"  异体子类（SubLabel）      {len(sub):,}")
print(f"  片均 token               {sum(lab.values())/len(data):.2f}")

# ---------- 2. 频段分布 ----------
print()
print("=" * 78)
print("第二部分：字频分布（实测，非估计）")
print("=" * 78)
bands = [(1000, 10**9), (500, 999), (100, 499), (50, 99), (10, 49), (2, 9), (1, 1)]
tot_tok = sum(lab.values())
cum = 0
band_rows = []
for lo, hi in bands:
    n = sum(1 for v in lab.values() if lo <= v <= hi)
    tok = sum(v for v in lab.values() if lo <= v <= hi)
    cum += tok
    band_rows.append((f"{lo}–{hi if hi<10**9 else '∞'}", n, tok, tok/tot_tok, cum/tot_tok))
    print(f"  {lo:>5}–{str(hi) if hi<10**9 else '∞':>5} 次: {n:>5} 类  "
          f"{tok:>7,} token  ({tok/tot_tok:6.2%})  累计 {cum/tot_tok:6.2%}")
top10 = sum(v for _, v in lab.most_common(10)) / tot_tok
top100 = sum(v for _, v in lab.most_common(100)) / tot_tok
print(f"\n  Top-10 类占 token  {top10:.1%}")
print(f"  Top-100 类占 token {top100:.1%}")

# 用主字表翻译 Top10
top10_lab = [(mc.get(k, {}).get("codepoint", k), v) for k, v in lab.most_common(10)]
print(f"  Top-10: " + "、".join(f"{c}({v})" for c, v in top10_lab))

# ---------- 3. 语料扩张下的边际收益（实测基线） ----------
print()
print("=" * 78)
print("第三部分：语料 ×(1+g) 后，各类新增出现次数（实测基线 + 泊松假设）")
print("=" * 78)


def pois_ge(lam, k):
    if lam <= 0:
        return 0.0
    return max(0.0, 1.0 - sum(math.exp(-lam) * lam ** x / math.factorial(x)
                              for x in range(k)))


print(f"{'g':>7} | " + " | ".join(f"≥{t:>2}次" for t in (2, 3, 5, 10, 50)))
print("-" * 60)
growth_rows = []
for g in (0.35, 0.45, 0.54, 1.00, 2.00, 5.00):
    cells = []
    for thr in (2, 3, 5, 10, 50):
        n = sum(pois_ge(v * g, thr) for v in lab.values())
        cells.append(n)
    growth_rows.append((g, cells))
    print(f"{g:>6.0%} | " + " | ".join(f"{c:>5.0f}" for c in cells))

print(f"\n  分母：现有 {len(lab):,} 个主字形类")
print(f"  注意 g=0.45 对应《三编》中枢情景（净增 ~2.47 万片 / 基准 5.54 万片）")

# ---------- 4. 漏斗 ----------
print()
print("=" * 78)
print("第四部分：从「待考」到「真能考释」的漏斗（实测基线）")
print("=" * 78)
CAT = {"已识": 1273, "有争议": 378, "未识": 2112}
PENDING = CAT["有争议"] + CAT["未识"]
g_mid = 0.446
gains3 = sum(pois_ge(v * g_mid, 3) for v in lab.values())
hapax = sum(1 for v in lab.values() if v == 1)
one_two = sum(1 for v in lab.values() if v <= 2)
print(f"  OBIMD 中仅一见字（hapax）     {hapax:,} / {len(lab):,} ({hapax/len(lab):.1%})")
print(f"  OBIMD 中出现 ≤2 次的类        {one_two:,} ({one_two/len(lab):.1%})")
print()
print(f"  《甲骨文字综理表》待考字形      {PENDING}")
print(f"  其中「残疑字/不可辨识」（约 23%）  {PENDING*0.77:.0f}")
print(f"  语料 ×1.45 后新增 ≥3 次证据     {gains3:.0f}   ← 关键数字")
print(f"  且落在可通读辞例中（×0.5）      {gains3*0.5:.0f}")
print(f"  且字形/音韵可补齐（×0.35）      {gains3*0.5*0.35:.0f}")

# ---------- 5. 需要多大规模 ----------
print()
print("=" * 78)
print("第五部分：要让「典型待考字」达到 50 次，语料要多大？")
print("=" * 78)
tail_vals = sorted(lab.values())[-PENDING:]
med = tail_vals[len(tail_vals) // 2]
print(f"  尾部 {PENDING} 类的出现次数：中位 {med}，均值 {sum(tail_vals)/len(tail_vals):.1f}，"
      f"最大 {max(tail_vals)}")
print(f"  → 中位类达到 50 次需语料扩大 {50/med:.0f} 倍")
print(f"  → 即约 {tot_tok*50/med/1e6:.0f} 百万 token（现有实测 {tot_tok/1000:.0f}K）")
print(f"  → 相当于 {len(data)*50/med/1000:.0f} 千片同密度甲骨")
print(f"  → 现存甲骨约 16 万片，全部数字化也只有 {160000/len(data):.1f} 倍")

res = {
    "obimd": {"pieces": len(data), "pieces_with_text": n_pieces_with_text,
              "tokens": n_tok, "seatfont": seat, "labeled_tokens": tot_tok,
              "label_classes": len(lab), "sublabel_classes": len(sub),
              "hapax": hapax, "top10_share": top10, "top100_share": top100},
    "bands": band_rows,
    "growth": [(g, c) for g, c in growth_rows],
    "funnel": {"pending": PENDING, "g_mid": g_mid, "gains_ge3": gains3},
    "tail": {"median": med, "max": max(tail_vals),
             "multiplier_for_50": 50 / med,
             "pieces_for_50": len(data) * 50 / med},
}
with open(os.path.join(OUT, "obimd_result.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
print(f"\n[写出] {os.path.join(OUT, 'obimd_result.json')}")
