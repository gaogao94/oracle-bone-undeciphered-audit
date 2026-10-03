# -*- coding: utf-8 -*-
"""
Round 8 记录：󳪫（71 次，4 形）的构形分析
发现：该字为「人形＋椭圆头」结构；「率」假设被证伪；兼记「天／大」分布异常
"""
import io, os, sys, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "甲骨文未释字_字形分析_2lep30tiiz.md")
OB = os.path.join(HERE, "data", "obimd")
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
cp = lambda l: mc.get(l, {}).get("codepoint") or ""
freq = collections.Counter()
for p in data:
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        for c in g.get("RecordUtilOracleCharVoList") or []:
            if c.get("Label"):
                freq[c["Label"]] += 1
label_of_char = {}
for lab, v in mc.items():
    c = v.get("codepoint") or ""
    if len(c) == 1:
        label_of_char.setdefault(c, lab)

L = []
L.append("# 未释字 󳪫（2lep30tiiz）的构形分析\n")
L.append("编制：2026-10-03\n")
L.append("> 本文报告对一个 71 次未释字的系统分析。**两个假设被证伪，未达成读法。**")
L.append("> 但确立了该字的构形特征，可供后续研究直接使用。\n")
L.append("---\n")

L.append("## 一、对象与基本数据\n")
L.append("| 项 | 值 |")
L.append("|---|---|")
L.append("| OBIMD 码位 | 󳪫 |")
L.append("| 内部编号 | `2lep30tiiz` |")
L.append("| 出现次数 | **71**（未释字中第二高频） |")
L.append("| 字形数 | 4 |")
L.append("| 类组分布 | 典賓B 30、賓出 10、歷二B2 6、典賓 4、賓三 4、歷二B3 4、歷二B1 3，餘散見 |")
L.append("")
L.append("**类组以宾组（典賓系）为主**，与晚期字不同，说明它是武丁时期的常用字。\n")

L.append("## 二、假设一「󳪫 = 率」——被证伪\n")
L.append("### 2.1　假设由来\n")
L.append("《合集》释文中，󳪫 所在片的对应位置常作「率」。例如：")
L.append("```")
L.append("《合集》95-3    鼎（貞）：□率以□（罝）芻。")
L.append("《合集》118-1   戊申卜，𡧊（賓）：令□取析芻。")
L.append("《合集》670-1   鼎（貞）：□〔以〕角女。")
L.append("```")
L.append("### 2.2　证伪证据\n")
L.append("1. **两者在同片共现**，且位置紧邻：")
L.append("   ```")
L.append("   H95    貞 󳪫 率 以 羆 芻     ／  合集95-3   鼎（貞）：□率以罝芻。")
L.append("   H4012  貞 󳪫 弗 其 率 以 󾯊   ／  合集4012    貞：□弗其率以□")
L.append("   ```")
L.append("   《合集》在 󳪫 处留空（字库无此字）、在「率」处写「率」——**同一句内两个字**。")
L.append("2. **字形完全不同**：OBIMD 的「率」作「竖笔贯菱形，上下有短横」，极简；")
L.append("   󳪫 作完整人形，结构复杂（图 M、图 N）。")
L.append("3. 若 󳪫=率，则 H95 成「貞 率 率 以 羆 芻」，文义不通。")
L.append("")
L.append("**结论：假设不成立。**\n")

L.append("## 三、󳪫 的构形特征（本文的主要产出）\n")
L.append("据 4 个字形逐一目验（图 N、图 O）：\n")
L.append("| 部位 | 特征 |")
L.append("|---|---|")
L.append("| 整体 | **完整人形**：有头、双臂（作斜出的两条横画）、双腿（分叉） |")
L.append("| **头部** | **椭圆形或尖头形**，与躯干有明显分界 |")
L.append("| 头部内部 | **多含一横画或短笔画**（4 形中有 3 形如此） |")
L.append("| 第三形 | 更繁：头上有饰，躯干作方框且内有笔画 |")
L.append("")
L.append("### 与相关字的区别\n")
L.append("| 字 | OBIMD 次数 | 头部构形 | 与 󳪫 是否相同 |")
L.append("|---|---|---|---|")
L.append("| **󳪫** | 71 | **椭圆／尖头，内有笔画** | — |")
L.append("| 天 | 3 | **方框头** | ✗ 不同 |")
L.append("| 大 | 624 | **无头**，仅人形 | ✗ 不同 |")
L.append("| 夫 | 11 | 头顶一横 | ✗ 不同 |")
L.append("| 文 | 2 | 胸部交叉 | ✗ 不同 |")
L.append("| 立 | 28 | 人立于地上（一横在下） | ✗ 不同 |")
L.append("| 先 | 85 | 椭圆头＋下部「止」（足）形 | 头部近似，下部不同 |")
L.append("| 光 | 10 | 人形＋头部上方有火形笔画 | 部分近似 |")
L.append("")
L.append("**结论：󳪫 的判定性特征为「人形＋椭圆头＋头内笔画」。**")
L.append("在 OBIMD 已释字中，无任何字的构形与此完全一致。\n")

L.append("## 四、附带发现：「天」与「大」的分布异常\n")
L.append("| 字 | OBIMD 出现次数 | 字形数 |")
L.append("|---|---|---|")
L.append("| 大 | **624** | 17 |")
L.append("| 天 | **3** | 3 |")
L.append("")
L.append("甲骨文中「天」与「大」形近（天为大字加头部标记），二者历来难分。")
L.append("OBIMD 中「大」624 次而「天」仅 3 次，这一比例偏低，")
L.append("**提示 OBIMD 可能把大量「天」归入了「大」**。")
L.append("此项与本课题的未释字问题无关，但可作为数据集质量的一个独立观察记录。\n")

L.append("## 五、结论与限度\n")
L.append("1. 「󳪫 = 率」的假设**被辞例与字形双重证伪**。")
L.append("2. 󳪫 的构形特征已确立：**人形＋椭圆头＋头内笔画**，71 次，宾组为主。")
L.append("3. **仍无判定性读法。** 「先」「光」在头部构形上接近，但下部不符；")
L.append("   在缺乏部件分解数据与类组字形差异表的情况下，无法进一步收窄。")
L.append("4. 该字的辞例多为残辞（「貞 󳪫 率以罝芻」「叀 󳪫 令執寇」），")
L.append("   且 󳪫 常居句首，疑为**人名或族名**——但这只是位置推测，不构成证据。\n")

L.append("![字形对照 󳪫 vs 天/大/夫/文](figures/figN_tian.png)")
L.append("")
L.append("![字形对照 󳪫 vs 率](figures/figM_lv_vs_target.png)")
L.append("")
L.append("## 附：脚本与数据\n")
L.append("- `test_lv.py`　「率」假设检验")
L.append("- `lv_vs_target.py`　与「率」的共现与字形对照")
L.append("- `test_tian.py`　「天」假设检验")
L.append("- `human_forms.py`　人形字系统对照表")
L.append("- `figures/figN_tian.png`、`figures/figM_lv_vs_target.png`、`figures/figO_humanform.png`")
L.append("")

open(OUT, "w", encoding="utf-8").write("\n".join(L))
print(f"[写出] {OUT}")
print(f"行数 {len(L)}")
