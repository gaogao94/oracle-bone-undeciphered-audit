# -*- coding: utf-8 -*-
"""最终报告：编码缺失筛查（三轮筛除后的可信清单）"""
import io, os, sys, json, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
RES = os.path.join(HERE, "result")
OUT = os.path.join(HERE, "甲骨文未释字_编码缺失筛查报告.md")

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

# 9 条 ★★★，含在 OBIMD 中的频率
CASES = [
    ("mepmffeebh", 37, "553", "賓三", "黃", "以·□·執", "以·黃·執"),
    ("uhz6qrd2d9", 6, "5373", "賓三", "安", "不·□·亡", "不·安·亡"),
    ("󱼮", 5, "32513", "歷二B3", "豲", "五·□·茲", "五·豲·茲"),
    ("󹧹", 3, "32009", "歷二A2", "宓", "卜·□·芻", "卜·宓·芻"),
    ("󾟷", 3, "22454", "師小字", "丘", "叀·□·豕", "叀·丘·豕"),
    ("󲌬", 2, "32512", "歷二B3", "豲", "五·□·茲", "五·豲·茲"),
    ("󾥗", 1, "17382", "典賓A", "娩", "月·□·不", "月·娩·不"),
    ("󻫐", 1, "31983", "歷二B1", "西", "于·□·若", "于·西·若"),
    ("󹛟", 1, "33286", "歷二B3", "龜", "叀·□·先", "叀·龜·先"),
]
label_of_glyph = {}
for lab, v in mc.items():
    c = v.get("codepoint") or ""
    if c:
        label_of_glyph[c] = lab

L = []
L.append("# OBIMD 甲骨文语料「未释字」的编码缺失筛查报告\n")
L.append("编制：2026-10-03　数据源：OBIMD（CC-BY-4.0，10,077 片）＋《甲骨文合集》释文\n")
L.append("> **本报告不是考释论文。** 它报告的是一项前置性发现：")
L.append("> 公开甲骨文数据集 OBIMD 中标记的 243 个「未释字」，")
L.append("> 有一部分并非学界未释，而是**该数据集自身的编码缺失**。")
L.append("> 任何基于该数据集的未释字研究，若不做此项筛查，问题集将包含伪问题。\n")
L.append("---\n")

L.append("## 一、桥接与数据获取\n")
L.append("### 1.1 片号桥接（已确认）\n")
L.append("**OBIMD 片号 `H<n>` 与《甲骨文合集》编号 `n` 一一对应。**")
L.append("随机抽验 5 片（279、553、5250、15410、32813），释文内容逐条吻合。\n")
L.append("### 1.2 类组数据（此前认为缺失，实为公开可得）\n")
L.append("《合集》释文库每条记录自带**类组**标注，可按片号、按字、按类组检索。")
L.append("例：`合集 553-1 ［賓三］ 癸丑卜，𡧊（賓）鼎（貞）：令彗、𠅷以黃執。七月。`")
L.append("实测「屯」返回 190 条，类组分布：典賓 88、典賓B 25、典賓A 20、賓出 12、")
L.append("賓三 6、師歷間 5、無名組 4、師賓間A 3、黃類 3。\n")
L.append("### 1.3 字表规模\n")
L.append(f"《合集》著录 41,956 片。本会话已抓取释文页 629 页并建缓存。\n")

L.append("## 二、三轮筛除\n")
L.append("| 轮次 | 方法 | 结果 |")
L.append("|---|---|---|")
L.append("| 一 | 全局 Levenshtein 对齐 | 321 条对照，判「合集解出」167 条 |")
L.append("| 二 | 邻字一致性校验 | 167 条中 73 条邻字吻合、43 条伪解、51 条待核 → **自动对齐准确率仅 44%** |")
L.append("| 三 | 候选字可读性分层 | 73 条中仅 11 条候选为可读通用汉字，其中 **9 条左右邻字双重吻合** |")
L.append("")
L.append("第三轮修正了一个**循环论证**：若候选字本身是站点私用区（PUA）码位，")
L.append("它在全库中本就罕见，其邻字自然与出处一致，不构成证据。故必须分层。\n")

L.append("## 三、9 条最强判定（左右邻字双重吻合）\n")
L.append("| OBIMD 字形 | 出现 | 片号 | 类组 | 《合集》作 | OBIMD 邻字 | 《合集》邻字 |")
L.append("|---|---|---|---|---|---|---|")
for g, n, pl, grp, cand, lo, lc in CASES:
    L.append(f"| {g} | {n} | {pl} | {grp} | **{cand}** | {lo} | {lc} |")
L.append("")

L.append("## 四、9 条的性质分类（关键）\n")
L.append("按候选字在 OBIMD 字表中的状态分三类，**结论各不相同**：\n")
L.append("| 候选 | OBIMD 字表中有无 | OBIMD 中实例数 | 性质 |")
L.append("|---|---|---|---|")
for g, n, pl, grp, cand, lo, lc in CASES:
    kl = label_of_char.get(cand)
    if kl is None:
        L.append(f"| {cand} | **无** | — | **OBIMD 未收录该字**：该字的字形类不在字表内 |")
    else:
        L.append(f"| {cand} | 有 | **{freq.get(kl,0)}** | "
                 + ("**内部不一致**：OBIMD 在别处认作该字，此处未认出"
                    if freq.get(kl, 0) > 0 else "该字表条目在语料中无实例") + " |")
L.append("")

L.append("### 4.1 最强的一条：󾥗 → 「娩」\n")
L.append("- 片号：《合集》17382（类组 **典賓A**）")
L.append("- OBIMD 辞例：`貞 二 月 󾥗 不 其 生`")
L.append("- OBIMD 中「娩」的常规辞例：`貞 二 月 娩 不 其 生`（共 18 处）")
L.append("- **同一句话、同一位置，OBIMD 在 18 处认作「娩」，在此片却标为未释字。**")
L.append("- 这是 OBIMD **字形分类内部不一致**的直接证据，与「学界未释」无关。\n")

L.append("### 4.2 「豲」：OBIMD 未收录该字\n")
L.append("- 󱼮（片 32513，歷二B3）与 󲌬（片 32512，歷二B3）")
L.append("- OBIMD 辞例：`癸 未 貞 叀 今 乙 酉 佑 父 歲 于 且 乙 五 □ 茲 用`")
L.append("- 《合集》同片作「**五豲茲用**」")
L.append("- 「豲」不在 OBIMD 字表中 → OBIMD 未收录该字形类。\n")

L.append("### 4.3 「黃」「安」：字表有条目但语料无实例\n")
L.append("- mepmffeebh（37 次，片 553，賓三）→ 《合集》作「以**黃**執」")
L.append("- uhz6qrd2d9（6 次，片 5373，賓三）→ 《合集》作「不**安**亡」")
L.append("- 「黃」「安」在 OBIMD 字表中均有条目，但语料中出现次数为 **0**。")
L.append("  即：OBIMD 收录了这两个字形类，却未在任何片中使用。\n")

L.append("## 五、结论\n")
L.append("1. **OBIMD 的「未释字」集合中，确有不属于「学界未释」的成分。**")
L.append("   本报告给出 9 条经三重校验（对齐＋邻字＋可读性分层）的实例，证据可逐条复核。")
L.append("2. **性质分三类**：数据集未收录某字的字形类；字表有条目但语料零实例；")
L.append("   同一字在数据集内部被分成两个类（内部不一致）。")
L.append("3. **这三类都不是「考释」问题，而是数据工程问题。**")
L.append("   其读法由《合集》释文给出，非本会话所发现。")
L.append("4. **方法学要点**：基于公开甲骨文数据集做未释字研究前，")
L.append("   应先做「数据集未编码」与「学界未释」的分层，否则问题集包含伪问题。")
L.append("5. **本会话仍未考释出任何学界未释的甲骨文字。**")
L.append("   目标（构建甲骨→金文→篆字形链＋辞例验证＋音韵通假三类证据链，")
L.append("   达到中国文字博物馆一等奖水平）**未达成**。\n")

L.append("## 六、可复现\n")
L.append("| 文件 | 说明 |")
L.append("|---|---|")
L.append("| `gxds2.py` | 《合集》释文＋类组抓取器（带缓存） |")
L.append("| `align.py` | 第一轮：全局对齐初判 |")
L.append("| `verify_solved.py` | 第二轮：邻字一致性校验 |")
L.append("| `finalize_v2.py` | 第三轮：可读性分层 |")
L.append("| `verify_9.py` | 9 条最强判定的逐条核验 |")
L.append("| `result/align_records.json` | 321 条逐片对照原始数据 |")
L.append("| `result/verify_solved.json` | 邻字校验全量结果 |")
L.append("| `data/gxds2/` | 释文缓存 629 页 |")
L.append("")

open(OUT, "w", encoding="utf-8").write("\n".join(L))
print(f"[写出] {OUT}")
print(f"行数 {len(L)}")
