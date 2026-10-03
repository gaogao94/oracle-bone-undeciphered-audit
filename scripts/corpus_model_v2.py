# -*- coding: utf-8 -*-
"""
甲骨文语料账 v2
修正：Zipf 尾部在 4000 字头规模下天然是"个位数出现次数"——这本身就是核心发现。
做法：固定 Zipf 指数 s（不做无意义的尾部截断校准），显式给敏感性区间。
"""
import io, json, math, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data")
os.makedirs(OUT, exist_ok=True)

# ---------- 1. 公开口径 ----------
PUB = {"合集(1982) 41956": 41956, "合集补编(1999) 13450": 13450}
BASE = sum(PUB.values())                       # 55406
SANBIAN = {"低": 20000, "中": 25000, "高": 30000}
DUP = {"低": 0.0075, "中": 0.0110, "高": 0.0200}   # 补编实测 165/15060 = 1.10%

# 《甲骨文字综理表》(中国文字博物馆编, 中西书局 2024-12)
CAT = {"已识": 1273, "有争议": 378, "未识": 2112}
PENDING = CAT["有争议"] + CAT["未识"]           # 2490

N_TYPES = 4000                                  # 字头规模（学界"4000余"）
TOKENS = 53834 * 18.6                           # CHANT 口径 ≈ 1,001,312 字

SCENARIOS = []          # 收集结果


def zipf_lambda(s, n_types=N_TYPES, tokens=TOKENS):
    h = sum(1.0 / (k ** s) for k in range(1, n_types + 1))
    return [tokens * (1.0 / (k ** s)) / h for k in range(1, n_types + 1)]


def pois_ge(lam, k):
    """P(X >= k), X~Poisson(lam)"""
    if lam <= 0:
        return 0.0
    cdf = sum(math.exp(-lam) * lam ** x / math.factorial(x) for x in range(k))
    return max(0.0, 1.0 - cdf)


print("=" * 78)
print("第一部分：现有语料的统计结构（这是全部结论的地基）")
print("=" * 78)
print(f"基准著录片数        {BASE:,} 片")
print(f"估计可读语料        {TOKENS:,.0f} 字（CHANT: 53,834 片 / 近 100 万字）")
print(f"常见字头均值        {TOKENS/N_TYPES:,.0f} 次")
print()

for s in (0.8, 1.0, 1.2):
    lam = zipf_lambda(s)
    tail = lam[-(PENDING):]
    print(f"--- Zipf s={s} ---")
    print(f"  最常用字 λ      = {lam[0]:,.0f} 次")
    print(f"  第 1000 位 λ    = {lam[999]:.1f} 次")
    print(f"  待考区(尾部2490) λ: 中位 {sorted(tail)[len(tail)//2]:.2f} "
          f"/ 均值 {sum(tail)/len(tail):.2f} / 最大 {max(tail):.2f}")
    print(f"  待考区中 λ<1 的比例 = {sum(1 for x in tail if x<1)/len(tail):.1%}")
    print()

# ---------- 2. 新增语料的边际效应 ----------
print("=" * 78)
print("第二部分：三编新增 ~2.5 万片，能让多少待考字跨过语料门槛？")
print("=" * 78)

S_MAIN = 1.0
lam0 = zipf_lambda(S_MAIN)
tail = sorted(lam0[-PENDING:])

for label_b, bc in SANBIAN.items():
    for label_d, dup in DUP.items():
        pieces_new = bc * (1 - dup)
        g = pieces_new / BASE                      # 新增可读语料倍数
        gains = {}
        for thr in (2, 3, 5, 10, 50):
            gains[thr] = sum(pois_ge(x * g, thr) for x in tail)
        SCENARIOS.append({"sanbian": bc, "dup": dup, "growth": g, "gains": gains})
        print(f"三编 {bc:,} 片 × 重片率 {dup:.2%} → 净增 {pieces_new:,.0f} 片"
              f"（可读语料 ×{g:.1%}）")
        for thr in (2, 3, 5, 10, 50):
            print(f"    新增 ≥{thr:2d} 次: {gains[thr]:6.0f} / {PENDING} "
                  f"({gains[thr]/PENDING:5.2%})")
        print()

# ---------- 3. 关键量：达到 50 次需要多少语料 ----------
print("=" * 78)
print("第三部分：要让一个典型待考字达到 50 次出现，语料要多大？")
print("=" * 78)
med = tail[len(tail) // 2]
print(f"待考区 λ 中位数 = {med:.3f} 次（现有 ~100 万字语料）")
print(f"→ 需要语料扩大 {50/med:,.0f} 倍")
print(f"→ 即需要约 {TOKENS*50/med/1e8:.1f} 亿字的可读卜辞")
print(f"→ 现存全部甲骨（约 16 万片）按 18.6 字/片 全读出来也只有 "
      f"{160000*18.6/1e6:.1f} 百万字，即 {160000*18.6/TOKENS:,.1f} 倍")
print()

# ---------- 4. 漏斗 ----------
print("=" * 78)
print("第四部分：从"待考"到"可考释"的逐级折损（中枢情景）")
print("=" * 78)
mid = SCENARIOS[3 - 1] if len(SCENARIOS) >= 3 else SCENARIOS[0]
central = [s for s in SCENARIOS if s["sanbian"] == 25000 and s["dup"] == 0.0110][0]
funnel = [
    ("待考字形（有争议 378 + 未识 2112）",                    PENDING),
    ("  扣除"残疑字/不可辨识"（按殷契文渊字形库比例 ~23%）",  PENDING * 0.77),
    ("  新增 ≥3 次新辞例证据",                                central["gains"][3]),
    ("  且新证据落在可通读的完整辞例中（×0.5）",               central["gains"][3] * 0.5),
    ("  且字形/音韵证据能补齐（×0.35）",                       central["gains"][3] * 0.5 * 0.35),
]
for name, v in funnel:
    print(f"  {name:44s} {v:8.0f}")
print(f"\n对照：2016 年设奖至今 9 年，一等奖 3 人、获奖合计 7 项。")

# ---------- 5. 缀合这条独立杠杆 ----------
print()
print("=" * 78)
print("第五部分：真正高效的杠杆是【缀合】，不是【加片】")
print("=" * 78)
print("  已刊缀合成果（可核）：")
print("    安阳师范学院 AI 系统累计成功缀合        160 组（2026-07）")
print("    林宏明《醉古集》(2011) 图版              382 组")
print("    首都师范大学已建档碎片                   ~1500 组")
print("  VPN 读法：每完成一组缀合 = 直接产出一条新的完整辞例，")
print("            作用等价于"凭空多出若干片从未被读通的甲骨"。")
print("  → 20000 片新增里，若 5%~15% 能构成新缀合，即 1000~3000 组，")
print("    与过去 40 年全部已刊缀合总量（数百至千余组）同量级。")

res = {
    "inputs": {"base_pieces": BASE, "sanbian": SANBIAN, "dup": DUP,
               "tokens": TOKENS, "n_types": N_TYPES, "catalog": CAT,
               "pending": PENDING},
    "lambda_tail": {"s": S_MAIN, "median": med, "max": max(tail),
                    "frac_lt_1": sum(1 for x in tail if x < 1) / len(tail)},
    "required_multiplier_for_50": 50 / med,
    "scenarios": SCENARIOS,
    "funnel": funnel,
}
with open(os.path.join(OUT, "model_result_v2.json"), "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
print(f"\n[写出] {os.path.join(OUT, 'model_result_v2.json')}")
