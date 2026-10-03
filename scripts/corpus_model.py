# -*- coding: utf-8 -*-
"""
甲骨文语料账：新增《甲骨文合集三编》对"待考字"可验证性的边际影响
模型：Zipf 分布 + 二项抽样（低计数下等价泊松），显式敏感性分析
"""
import io, json, math, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data")
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------
# 1. 语料构成（全部来自公开报道/权威口径，见报告引注）
# ---------------------------------------------------------------
PUB = {                       # 著录片数
    "合集(1982)":      41956,
    "合集补编(1999)":  13450,
}
BC = 30000          # 《三编》公布口径
DUP = (0.0075, 0.02)  # 重片率区间（补编实测 165/15060=1.10%）
BASE = sum(PUB.values())

# 含字片比例与片均字数（李学勤 1:3 推测；CHANT 实测 18.6 字/片）
TOK_PER_BASE = 53834 * 18.6      # ≈ 1,001,312 字（CHANT 口径的字频分母）
INSCRIBE_RATE = (0.25, 0.50)     # 有字片比例区间

# 《甲骨文字综理表》(中国文字博物馆编, 中西书局 2024-12) —— 权威分母
CAT = {"已识": 1273, "有争议": 378, "未识": 2112}
PENDING = CAT["有争议"] + CAT["未识"]        # 2490
PENDING_HARD = CAT["未识"]                   # 2112

# ---------------------------------------------------------------
# 2. Zipf 拟合：用 3000 高频字覆盖 90% 字频 校准 s
# ---------------------------------------------------------------
def calibrate_s(n_types=4000, top=3000, frac=0.90):
    lo, hi = 0.3, 2.5
    for _ in range(80):
        s = (lo + hi) / 2
        tot = sum(1.0 / (k ** s) for k in range(1, n_types + 1))
        c = sum(1.0 / (k ** s) for k in range(1, top + 1)) / tot
        if c > frac:
            lo = s
        else:
            hi = s
    return (lo + hi) / 2


S = calibrate_s()
print(f"[校准] Zipf 指数 s = {S:.4f}  (假设 4000 字头、前 3000 字占 90% 字频)")

N_TYPES = 4000
TOT = TOK_PER_BASE
H_DEN = sum(1.0 / (k ** S) for k in range(1, N_TYPES + 1))
LAM = [TOT * (1.0 / (k ** S)) / H_DEN for k in range(1, N_TYPES + 1)]  # 每字期望出现次数

# 用"关注子集"模拟待考字：官方巡报称未释字中"大部分是罕用的专名"
FOCUS_N = PENDING            # 2490 个待考字形
focus = LAM[-FOCUS_N:]       # 取分布尾部最罕见的一批
focus = sorted(focus)
print(f"[语料] 基准著录 {BASE:,} 片 → 估可读语料 {TOT:,.0f} 字")
print(f"[待考] 取分布尾部 {FOCUS_N} 个字形，lambda 中位数={focus[len(focus)//2]:.2f}，"
      f"最大={max(focus):.2f}")

# ---------------------------------------------------------------
# 3. 新增语料 → 新出现次数
# ---------------------------------------------------------------
def sweep(dup_rate, insc_rate, n_types, tot_tokens):
    """返回各阈值下的收益表"""
    g = (BC * (1 - dup_rate)) / BASE          # 新增/基准 比例
    g_tok = g * (insc_rate / 0.375)           # 含字率修正（0.375 为先验中值）
    res = {}
    for thr in (2, 3, 4, 5):
        gains = []
        for lam in focus:
            lam_new = lam * g_tok             # 期望新增次数
            p = 0.0
            for x in range(thr):
                p += math.exp(-lam_new) * lam_new ** x / math.factorial(x)
            gains.append(1 - p)               # P(新增 >= thr) = 跨过阈值
        res[thr] = sum(gains)
    return g, g_tok, res


print("\n" + "=" * 74)
print("情景扫描：三编新增片数 × 重片率 → 有多少待考字能跨过『最低语料门槛』")
print("=" * 74)
rows = []
for bc in (20000, 25000, 30000):
    for dup in DUP:
        globals()['BC'] = bc
        g, g_tok, res = sweep(dup, 0.375, N_TYPES, TOT)
        rows.append((bc, dup, g, g_tok, res))
        print(f"\n三编={bc:,}片  重片率={dup:.2%}  → 净增 {bc*(1-dup):,.0f} 片 "
              f"(基准的 {g:.1%}，可读语料 ×{g_tok:.1%})")
        for thr in (2, 3, 4, 5):
            n = res[thr]
            print(f"   ≥{thr} 次新证: {n:6.0f} / {FOCUS_N}  ({n/FOCUS_N:5.1%})")

# ---------------------------------------------------------------
# 4. 条件概率：拿到 ≥3 次新证 且 能凑齐三类证据
# ---------------------------------------------------------------
print("\n" + "=" * 74)
print("从『跨过语料门槛』到『真的能考释』：逐级折损")
print("=" * 74)
globals()['BC'] = 25000
g, g_tok, res = sweep(0.0110, 0.375, N_TYPES, TOT)
print(f"中枢情景：三编 25,000 片、重片率 1.10% → 可读语料 ×{g_tok:.1%}")
stages = [
    ("待考字形（有争议+未识）",            PENDING),
    ("其中排除『残疑字/不可辨识』",          PENDING * 0.77),
]
n3 = res[3]
stages.append(("新增 ≥3 次新辞例证据",              n3))
stages.append(("且新证据落在可通读的辞例中（×0.5）",   n3 * 0.5))
stages.append(("且能补齐字形+音韵（×0.35）",          n3 * 0.5 * 0.35))
for name, v in stages:
    print(f"  {name:38s} {v:7.0f}")

print("\n对照：2016 年设奖至今 9 年，实际获一等奖 3 人 / 获奖共 7 项。")

# ---------------------------------------------------------------
# 5. 写入结果
# ---------------------------------------------------------------
out = {
    "zipf_s": S, "base_pieces": BASE, "base_tokens": TOT,
    "catalog": CAT, "pending": PENDING,
    "sweep": [{"sanbian": r[0], "dup_rate": r[1], "growth": r[2],
               "token_growth": r[3],
               "gains": {str(k): v for k, v in r[4].items()}} for r in rows],
    "central": {"token_growth": g_tok, "gains": {str(k): v for k, v in res.items()}},
    "funnel": [(n, v) for n, v in stages],
}
with open(os.path.join(OUT, "model_result.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print(f"\n[写出] {os.path.join(OUT, 'model_result.json')}")
