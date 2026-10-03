# -*- coding: utf-8 -*-
"""
修正判定：把候选字分为三类
  (a) 可正常显示的通用汉字 → 真解出（有读法）
  (b) PUA 码位字（站点私有）→ 该字在图库里存在但本会话无法渲染，仍属"字库有、OBIMD 缺"
  (c) 扩展区汉字（如 𠦪）→ 字库有，OBIMD 缺
另：修正循环论证——(b)(c) 类不能靠邻字吻合判定，因为其在《合集》中本就罕见。
"""
import io, os, sys, json, collections, unicodedata
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "result")
OUT = os.path.join(HERE, "甲骨文未释字_邻字校验清单.md")

v = json.load(open(os.path.join(RES, "verify_solved.json"), encoding="utf-8"))


def kind(ch):
    if not ch:
        return "空"
    o = ord(ch)
    if 0xE000 <= o <= 0xF8FF or 0xF0000 <= o <= 0xFFFFD or 0x100000 <= o <= 0x10FFFD:
        return "PUA"
    if o > 0xFFFF:
        return "扩展区"
    try:
        unicodedata.name(ch)
        return "通用汉字"
    except Exception:
        return "未知"


def split(rows):
    a, b, c = [], [], []
    for r in rows:
        k = kind(r.get("cand"))
        r["kind"] = k
        (a if k == "通用汉字" else b if k in ("PUA",) else c).append(r)
    return a, b, c


okA, okBC, okC = split(v["ok"])
badA, badB, badC = split(v["bad"])


def dedup(rows):
    d = {}
    for r in rows:
        kk = r["glyph"]
        if kk not in d or r["freq"] > d[kk]["freq"]:
            d[kk] = r
    return sorted(d.values(), key=lambda r: -r["freq"])


okAd, okBCd = dedup(okA), dedup(okBC)
# 通用汉字里，左右邻字都吻合的（最强）
strong = [r for r in okAd if r["left"] and r["right"]
          and r["corpus_left"] == r["left"] and r["corpus_right"] == r["right"]]
strongest = [r for r in okAd if r["left"] and r["right"] and r["kind"] == "通用汉字"]

L = []
L.append("# OBIMD「未释字」编码缺失筛查：修正后的可信清单\n")
L.append("编制：2026-10-03　数据源：OBIMD ＋《甲骨文合集》释文（国学大师）\n")
L.append("> 本清单经三轮筛除：初判（全局对齐）→ 邻字校验 → **候选字可读性分类**。")
L.append("> 第三轮修正了一个循环论证：若候选字本身是不可渲染的私用区码位，")
L.append("> 则其在《合集》中本就罕见，邻字「吻合」是必然的，不构成证据。\n")
L.append("---\n")

L.append("## 一、为什么必须做第三轮筛除\n")
L.append("前一轮把「候选字在《合集》中的左右邻字与 OBIMD 一致」当作可信标准。")
L.append("但候选字若是站点私用区（PUA）码位，它在全库中只出现极少次，")
L.append("其邻字自然与出处一致——**这是循环论证**。因此必须按候选字的可读性分层。\n")

L.append("## 二、分层结果\n")
L.append("| 类别 | 条数 | 含义 |")
L.append("|---|---|---|")
L.append(f"| 候选为**通用汉字** | {len(okA)} | **真解出**：《合集》给出可读的读法 |")
L.append(f"| 候选为私用区/扩展区码位 | {len(okBC)} | 《合集》字库有该字，本会话无法渲染——**仍属字库有、OBIMD 缺** |")
L.append("")
L.append("按字去重后：**通用汉字候选 "
         f"{len(okAd)} 个**；私用区/扩展区候选 {len(okBCd)} 个。\n")

L.append("## 三、真解出清单（候选为可读通用汉字）\n")
L.append("这些 OBIMD 标为「无隶定」的字，《合集》释文给出了**可读的**读法，且邻字位置吻合。\n")
L.append("| OBIMD 字形 | 出现 | 片号 | 类组 | 《合集》作 | 邻字校验（OBIMD ／ 合集） | 强度 |")
L.append("|---|---|---|---|---|---|---|")
for r in okAd:
    ln = f"{r['left'] or '—'}·□·{r['right'] or '—'}"
    rn = f"{r['corpus_left'] or '—'}·{r['cand']}·{r['corpus_right'] or '—'}"
    s = "★★★" if (r["left"] and r["right"] and r["corpus_left"] == r["left"]
                   and r["corpus_right"] == r["right"]) else \
        ("★★" if r["score"] == 2 else "★")
    L.append(f"| {r['glyph']} | {r['freq']} | {r['plate']} | {r['group']} | "
             f"**{r['cand']}** | {ln} ／ {rn} | {s} |")
L.append("")
L.append(f"其中左右邻字**双重吻合（★★★）者 {len(strong)} 个**——这是证据最强的子集。\n")

L.append("## 四、★ 最强的几个例（逐一说明）\n")
for r in strong:
    L.append(f"### {r['glyph']}（出现 {r['freq']} 次）→ 「{r['cand']}」\n")
    L.append(f"- 片号：《合集》{r['plate']}（类组 **{r['group']}**）")
    L.append(f"- OBIMD 辞例：`{r['left']} · □ · {r['right']}`")
    L.append(f"- 《合集》释文：`{r['corpus_left']} · {r['cand']} · {r['corpus_right']}`")
    L.append(f"- 判定：OBIMD 未编码该字；《合集》作「{r['cand']}」。**非本会话考释所得，而是《合集》已释。**\n")

L.append("## 五、伪解与待核\n")
L.append(f"- 伪解（邻字不吻合）：{len(v['bad'])} 条")
L.append(f"- 待核（部分一致）：{len(v['unclear'])} 条")
L.append("- **自动对齐的整体准确率约 44%**（73/167），不足以直接采信；")
L.append("  本条清单只保留经过邻字校验的条目。\n")

L.append("## 六、结论\n")
L.append(f"1. **{len(okAd)} 个 OBIMD「未释字」确证为编码缺失**（候选为可读通用汉字，邻字吻合）。")
L.append("   其读法**并非本会话的考释成果，而是《合集》释文早已给出**；")
L.append("   本会话的贡献是**证明 OBIMD 未编码它们**，并给出可逐条复核的证据。")
L.append(f"2. 另有 {len(okBCd)} 个候选落在私用区或扩展区，说明《合集》字库收录了这些字形，")
L.append("   而 OBIMD 未收录——同样属编码缺失，但本会话无法渲染其形体，故不列读法。")
L.append("3. **方法学要点**：任何基于公开甲骨文数据集的未释字研究，")
L.append("   应先把「数据集未编码」与「学界未释」分开，否则问题集包含伪问题。")
L.append("   本清单可作为该筛查的前置结果。")
L.append("4. **本会话仍未考释出任何学界未释的甲骨文字。**\n")

L.append("## 附：可复现\n")
L.append("- `gxds2.py`　《合集》释文＋类组抓取器（缓存 629 页）")
L.append("- `align.py`　初判（已证约 1/4 伪解）")
L.append("- `verify_solved.py`　邻字一致性校验")
L.append("- `finalize_verify.py`　可读性分层")
L.append("- `result/verify_solved.json`　全量校验数据")
L.append("")

open(OUT, "w", encoding="utf-8").write("\n".join(L))
print(f"[写出] {OUT}")
print(f"真解出（通用汉字候选）{len(okAd)} 个，其中 ★★★ {len(strong)} 个")
print(f"私用区/扩展区候选 {len(okBCd)} 个")
print(f"伪解 {len(v['bad'])} 条，待核 {len(v['unclear'])} 条")
print("\n★★★ 清单：")
for r in strong:
    print(f"  {r['glyph']:>4}（{r['freq']}次）片{r['plate']} [{r['group']}] → 「{r['cand']}」"
          f"  {r['left']}·□·{r['right']} ／ {r['corpus_left']}·{r['cand']}·{r['corpus_right']}")
