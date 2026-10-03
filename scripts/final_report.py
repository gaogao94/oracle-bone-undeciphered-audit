# -*- coding: utf-8 -*-
"""生成最终判定报告（15 个目标的逐条复核结果）"""
import io, json, os, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "result")
OB = os.path.join(HERE, "data", "obimd")
OUT = os.path.join(HERE, "甲骨文未释字_复核判定报告.md")

mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
cp = lambda l: mc.get(l, {}).get("codepoint") or ""
freq = collections.Counter()
for p in data:
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        for c in g.get("UtilOracleCharVoList") if False else (g.get("RecordUtilOracleCharVoList") or []):
            if c.get("Label"):
                freq[c["Label"]] += 1

rv = json.load(open(os.path.join(RES, "review_verdicts.json"), encoding="utf-8"))

# 人工视觉判定（本次逐图目验所得）
VIS = {
    "禾": ("相符", "未釋字作「木形＋下部小框」，禾之甲骨文正作木形帶垂穗；形體吻合"),
    "殺": ("基本相符", "未釋字作「倒矢形＋兩手持器」，殺象以兵器刺獸，構形接近"),
    "雀": ("相符", "未釋字作「上小下大＋兩側點」，雀象小鳥，構形接近"),
    "其": ("不符", "其作簸箕形（方框＋內交叉），未釋字為三叉形，結構不同"),
    "今": ("不符", "今作倒口形＋橫畫，未釋字作倒矢形＋交叉，結構不同"),
    "琡": ("不符", "琡從玉，未釋字無玉形"),
    "新": ("不符", "新從斤從木，未釋字為倒矢形，結構不同"),
    "轡": ("不符", "轡象馬轡之形，未釋字作植物形，結構不同"),
}

L = []
L.append("# 甲骨文未释字：15 个高价值目标的复核判定\n")
L.append("编制：2026-10-02　数据源：OBIMD（CC-BY-4.0，10,077 片）\n")
L.append("> 本报告对上一步筛出的 15 个「最强位置全语料唯一可填」的未释字逐条复核。")
L.append("> 复核含两道独立检验：**辞例通顺性**（邻字相容）与**字形结构**（逐图目验）。")
L.append("> 两道的判定均已记录，未通过者明确剔除。\n")
L.append("---\n")

L.append("## 一、复核方法\n")
L.append("**检验一：辞例通顺性**。把候选字填入未释字位置，检查：")
L.append("- 该候选字在语料中是否常在「前邻字」之后出现（记为前邻相容次数）")
L.append("- 该候选字在语料中是否常在「后邻字」之前出现（记为后邻相容次数）")
L.append("- 若两者皆为 0，则填入后成句不自然，判「不相容」\n")
L.append("**检验二：字形结构**。逐图目验未释字与候选字的构形，判「相符／基本相符／不符」。")
L.append("本会话已证实像素级相似度无判别力（同类变异与跨类差异同量级），故此处只作结构性目验，不用数值。\n")

L.append("## 二、逐条结果\n")
L.append("| # | 未释字 | 出现 | 候选字 | 前邻相容 | 后邻相容 | 辞例判定 | 字形判定 | 最终 |")
L.append("|---|---|---|---|---|---|---|---|---|")
final_ok = []
for r in rv:
    cad = r["cand"]
    d = r["details"][0]
    vis, _ = VIS.get(cad, ("未判", ""))
    ok = (r["verdict"] in ("相容", "部分相容")) and vis in ("相符", "基本相符")
    if ok:
        final_ok.append((r["glyph"], cad, r, vis))
    L.append(f"| {rv.index(r)+1} | {r['glyph']} | {r['freq']} | **{cad}** | "
             f"{d['before_hits']} | {d['after_hits']} | {r['verdict']} | {vis} | "
             f"{'**保留**' if ok else '剔除'} |")
L.append("")

L.append("## 三、保留的候选（两道检验均通过）\n")
L.append("| 未释字 | 候选 | 辞例证据 | 字形证据 |")
L.append("|---|---|---|---|")
for g, cad, r, vis in final_ok:
    d = r["details"][0]
    L.append(f"| **{g}** | **{cad}** | 「{d['piece']}」：前鄰「{d['prev']}」在{cad}前出現 {d['before_hits']} 次，"
             f"後鄰「{d['next']}」在{cad}後出現 {d['after_hits']} 次 | {VIS[cad][1]} |")
L.append("")
L.append("### 各条的完整辞例\n")
for g, cad, r, vis in final_ok:
    for d in r["details"]:
        L.append(f"- **{g} → {cad}**（{d['piece']}）：前鄰「{d['prev']}」，后邻「{d['next']}」")
L.append("")

L.append("## 四、剔除的候选及理由\n")
L.append("| 未释字 | 候选 | 剔除理由 |")
L.append("|---|---|---|")
for r in rv:
    cad = r["cand"]
    vis, note = VIS.get(cad, ("未判", ""))
    if (r["verdict"] in ("相容", "部分相容")) and vis in ("相符", "基本相符"):
        continue
    reason = []
    if r["verdict"] == "不相容":
        reason.append("辞例不相容（前邻、后邻相容次数皆为 0）")
    if vis in ("不符",):
        reason.append(f"字形不符：{note}")
    if not reason:
        reason.append("部分相容，证据不足")
    L.append(f"| {r['glyph']} | {cad} | {'；'.join(reason)} |")
L.append("")

L.append("## 五、结论与限度\n")
L.append(f"1. 15 个目标中，**辞例与字形两道检验均通过者 {len(final_ok)} 个**。")
L.append("2. 剔除的主要原因是**字形不符**——这说明「最强位置唯一可填」这一统计判据")
L.append("   虽然有效，但**必须与字形结构检验并用**，单独使用会产生假阳性。")
L.append("3. 全部 15 个目标均为出现 1–2 次的低频字，其中 14 个只有 1 个字形。")
L.append("   这既是它们未被认出的原因，也是本项研究证据量的上限。")
L.append("4. **本报告不作「已考释」之声明**。上述保留候选仍缺两项关键证据：")
L.append("   一是**类组归属**（OBIMD 无类组标注，无法作类组互补检验）；")
L.append("   二是**字形链**（甲骨→金文→篆）的逐阶段核对，本会话仅取到「中」一字的完整链。")
L.append("   故本报告的性质是**候选清单与复核记录**，供古文字学者审定。\n")

L.append("## 附：本会话的否定性结果（供后续研究参考）\n")
L.append("- **七套字形相似度度量全部失败**。根因：同字不同形的 IoU（中 0.151、史 0.068、目 0.181）")
L.append("  与跨类最高 IoU（冊 0.241、丁 0.235）处于同一量级，像素信号被字形内部变异淹没。")
L.append("- **原拓按边界框切字路径失败**：留一法 top-1 仅 6.0%，低于随机（拓片噪点未处理）。")
L.append("- **原报的 26 条「平行辞例」假设全部作废**：该位可替换字常达 9–361 个，证据力均 <0.5。")
L.append("- **未释字 fybnj2savm = 「中」不成立**：「中」在语料中出现 68 次属常用字，")
L.append("  而该字仅 2 条残辞，证据分量不足。\n")

open(OUT, "w", encoding="utf-8").write("\n".join(L))
print(f"[写出] {OUT}")
print(f"保留候选 {len(final_ok)} 个：", [(g, c) for g, c, _, _ in final_ok])
