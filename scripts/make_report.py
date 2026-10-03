# -*- coding: utf-8 -*-
"""
本次会话的完整方法验证报告（含全部否定结果 + 15 个高价值目标）
输出为 Markdown
"""
import io, json, os, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "result")
OB = os.path.join(HERE, "data", "obimd")
OUT = os.path.join(HERE, "甲骨文未释字_方法验证与目标清单.md")

mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
cp = lambda l: mc.get(l, {}).get("codepoint") or ""
sents = []
for p in data:
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        seq = sorted([c for c in (g.get("RecordUtilOracleCharVoList") or [])
                      if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
        if seq:
            sents.append([c["Label"] for c in seq])
freq = collections.Counter()
for s in sents:
    freq.update(s)
anon = [l for l in freq if (mc.get(l, {}).get("transcription") or []) == []]

hv = json.load(open(os.path.join(RES, "high_value_targets.json"), encoding="utf-8"))
ps = json.load(open(os.path.join(RES, "parallel_strength.json"), encoding="utf-8"))
cs = json.load(open(os.path.join(RES, "constraint_strength.json"), encoding="utf-8"))
rv = json.load(open(os.path.join(RES, "retrieval_validation.json"), encoding="utf-8"))
sc = json.load(open(os.path.join(RES, "source_comparison.json"), encoding="utf-8"))

L = []
L.append("# 甲骨文未释字的量化考释：方法验证与目标清单\n")
L.append("编制：2026-10-02　语料：OBIMD（CC-BY-4.0，10,077 片）\n")
L.append("> 本文记录一次完整的量化考释尝试，**包括七套失败的字形度量**。")
L.append("> 结论是：图像相似度在本语料上不具判定力，可用的判据只有「辞例框架约束」一类，")
L.append("> 且其强度必须逐条量化，不能默认成立。\n")
L.append("---\n")

L.append("## 一、语料基本盘\n")
L.append(f"- 辞例 {len(sents):,} 条｜字形类 {len(freq):,} 个｜未释字形类 **{len(anon)}** 个")
n0 = sum(1 for r in cs if r["best_n_rep"] == 0)
n1 = sum(1 for r in cs if r["best_n_rep"] == 1)
n2 = sum(1 for r in cs if r["best_n_rep"] == 2)
L.append(f"- 未释字按最强位置约束力分层：可替换字 0 个者 {n0}，1 个者 **{n1}**，2 个者 {n2}\n")

L.append("## 二、七套字形度量，全部失败（否定性结果）\n")
L.append("| 度量 | 结果 | 失败原因 |")
L.append("|---|---|---|")
L.append(f"| 摹本图像检索（宽松参考库） | top-1 {rv['top1']:.1%} | 参考库类别分布过宽，虚高 |")
L.append(f"| 摹本图像检索（严格同分布 200 类） | top-1 {sc['facsimile']['top1']:.1%} | 可靠性基准应取此值 |")
L.append(f"| 拓本按 Position 切字 | top-1 {sc['rubbing']['top1']:.1%} | 低于随机；拓片噪点未处理 |")
L.append("| 交并比（IoU） | 跨类最高 0.241 | 与同类变异同量级（中 0.151、史 0.068、目 0.181） |")
L.append("| 余弦相似度 | 全部趋同 0.91+ | 被墨量密度主导 |")
L.append("| 网格占用率 / 分段部件 | 各法排序互不一致 | 特征无判别力 |")
L.append("| 墨迹外框内 IoU（修正版） | 跨类最高 0.241 | 同上 |")
L.append("")
L.append("**关键证据**：同类不同形的 IoU（中 0.151、史 0.068、目 0.181）")
L.append("与跨类最高 IoU（冊 0.241、丁 0.235）**处于同一量级**。")
L.append("这意味着像素级相似度信号完全被字形内部变异淹没，无论怎样设计特征。\n")

L.append("## 三、辞例框架判据：可用，但必须逐条量化强度\n")
L.append("本会话曾报出「26 条平行辞例假设」。经强度量化，**全部作废**：\n")
L.append("| 未释字 | 候选字 | 该位可替换字数 | 证据力 |")
L.append("|---|---|---|---|")
for p in sorted(ps, key=lambda x: -x["strength"])[:8]:
    L.append(f"| {p['glyph']} | {p['cand']} | {p['n_replaceable']} | {p['strength']:.3f} |")
L.append("")
strong = sum(1 for p in ps if p["strength"] >= 0.5)
weak = sum(1 for p in ps if p["strength"] < 0.2)
L.append(f"证据力 ≥0.5（该位只容 1–2 字）者：**{strong} 条**；<0.2（近乎无约束）者：{weak} 条。\n")
L.append("原因：这些「平行辞例」所在框架在全语料均只出现 1 次，")
L.append("且槽位可替换字常达 9–361 个。例如「叀 X 令」全语料 40 余条，X 位可填 30 余字。\n")

L.append("## 四、高价值目标清单（15 个）\n")
L.append("筛选条件：**未释字的最强位置，全语料只有唯一一个已释字可填**。")
L.append("这类字最可能闭合（异体 / 误分 / 罕见写法），是继续攻克的首选目标。\n")
L.append("> ⚠️ 但「唯一可填」不等于「就是那个字」。槽位的句法角色必须另行核对——")
L.append("> 例如已核出「貞我㚔□」若填「貞」则成「貞我㔟貞」，不通。\n")
L.append("| # | 未释字 | 出现 | 字形数 | 全语料唯一可填字 | 最强位置框架 | 辞例 | 核查结论 |")
L.append("|---|---|---|---|---|---|---|---|")
for i, r in enumerate(hv, 1):
    cad = "、".join(r["cad"])
    sig = " ".join(r["sig"])
    ex = r["examples"][0] if r["examples"] else ""
    ex = ex.split(":", 1)[-1].strip()[:34]
    note = "槽位角色待核" if cad in ("貞", "其", "卜") else "待核"
    L.append(f"| {i} | {r['glyph']} | {r['freq']} | {r['n_glyphs']} | **{cad}** | {sig} | {ex} | {note} |")
L.append("")
L.append("### 已核出的一处不成立\n")
L.append("- 未释字 󲥈（2 次）的最强位置框架为「我 㚔」，全语料唯一可填字为「貞」。")
L.append("  然「癸酉卜賓貞我㚔【□】」若填「貞」，则成「貞我㔟貞」，于辞例不通。")
L.append("  故该位置**不存在真正的平行**，本条的「唯一可填」属统计巧合。")
L.append("  这说明：**框架约束的有效性必须逐条以辞例通顺性复核**，这正是前人考释的必经一步。\n")

L.append("## 五、结论\n")
L.append("1. **图像相似度在本语料上不可用于考释**。七套度量一致失败，根因是跨类差异")
L.append("   与同类变异同量级——瓶颈不在算法，在字形数据的结构化程度。")
L.append("2. **辞例框架约束是唯一可用判据，但强度必须量化**。本会话原报的 26 条平行辞例")
L.append("   假设经量化后全部作废，这是方法自检的必要一步。")
L.append("3. **可下手的目标是 15 个**：其最强位置在全语料中只有唯一候选。")
L.append("   但其中至少 1 条已核出为统计巧合，故须逐条以辞例通顺性复核。")
L.append("4. **对高频常用字提出新读，需要压倒性证据**。本会话曾提出未释字 fybnj2savm = 「中」，")
L.append("   其字形结构距离（0.118）虽断层领先，但「中」在本语料出现 68 次、")
L.append("   属常用字，且该字仅 2 条残辞，证据分量不足，不主张成立。\n")

L.append("## 附：可复现脚本\n")
for f in ["strict_v3.py", "constraint_strength.py", "parallel_strength.py",
          "high_value.py", "tight_iou.py", "frame_method.py", "frame_ceiling.py"]:
    L.append(f"- `{f}`")
L.append("")

open(OUT, "w", encoding="utf-8").write("\n".join(L))
print(f"[写出] {OUT}")
print(f"行数 {len(L)}")
