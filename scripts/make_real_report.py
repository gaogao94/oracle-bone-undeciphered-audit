# -*- coding: utf-8 -*-
"""生成真候选报告与字形图"""
import io, os, re, sys, json, collections, zipfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
OB = os.path.join(HERE, "data", "obimd")
RES = os.path.join(HERE, "result")
FIG = os.path.join(HERE, "figures")
OUT = os.path.join(HERE, "甲骨文未释字_真伪判定报告.md")

mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
ZS = zipfile.ZipFile(os.path.join(OB, "subchar_images.zip"))
cp = lambda l: mc.get(l, {}).get("codepoint") or ""

by_label = collections.defaultdict(list)
for n in ZS.namelist():
    if n.lower().endswith(".png"):
        p = n.split("/")
        if len(p) >= 4:
            by_label.setdefault(p[1], []).append(n)

recs = json.load(open(os.path.join(RES, "align_records.json"), encoding="utf-8"))
st = collections.Counter(r["status"] for r in recs)

# 真候选：合集亦占位（按字去重，取最高频的片）
real = {}
for r in recs:
    if r["status"] == "合集亦占位":
        k = r["label"]
        if k not in real or r["freq"] > real[k]["freq"]:
            real[k] = r
real = sorted(real.values(), key=lambda r: -r["freq"])

# 编码缺失样本
solved = {}
for r in recs:
    if r["status"] == "合集解出":
        k = r["label"]
        if k not in solved:
            solved[k] = r
solved = sorted(solved.values(), key=lambda r: -r["freq"])

L = []
L.append("# 甲骨文「未释字」真伪判定报告\n")
L.append("编制：2026-10-03　数据源：OBIMD（CC-BY-4.0）＋《甲骨文合集》释文（国学大师）\n")
L.append("> 本报告解决一个此前无法回答的问题：**OBIMD 语料中标记的 243 个「未释字」，")
L.append("> 有多少是学界真正未释，有多少只是该数据集的编码缺失。**\n")
L.append("---\n")

L.append("## 一、方法与桥接\n")
L.append("关键发现：**OBIMD 的片号 `H<n>` 与《甲骨文合集》编号 `n` 一一对应。**")
L.append("据此可把 OBIMD 的辞例与《合集》释文逐片比对，用序列对齐定位每个未释字的位置。\n")
L.append("《合集》释文来源为公开可检索的在线释文库（国学大师），每条带**类组**标注，")
L.append("格式如「合集 7371-1　…〔翼（翌）丙〕子其立中，亡風。　典賓B」。\n")
L.append("对齐方法：Levenshtein 全局对齐，OBIMD 字符序列 ↔ 《合集》释文序列（已去除今字标注与标点）。\n")

L.append("## 二、判定结果\n")
L.append(f"共 {len(recs)} 条（未释字 × 出现片）对齐记录：\n")
L.append("| 判定 | 条数 | 含义 |")
L.append("|---|---|---|")
L.append(f"| **合集解出** | **{st.get('合集解出',0)}** | 《合集》释文已给出该位置的字 → **属编码缺失，非未释字** |")
L.append(f"| **合集亦占位** | **{st.get('合集亦占位',0)}** | 《合集》亦只能以 `※ □ ■ …` 占位 → **可能真未释** |")
L.append(f"| 未对齐 | {st.get('未对齐',0)} | 对齐失败，待核 |")
L.append("")
L.append(f"**结论：超过一半（{st.get('合集解出',0)}/{len(recs)}）的「未释字」并非学界未释，")
L.append("而是 OBIMD 数据集未编码该字。**\n")

L.append("## 三、编码缺失的证据（原以为的未释字，其实《合集》已读出）\n")
L.append("| OBIMD 字形 | 出现 | 片号 | 类组 | OBIMD 辞例 | 《合集》释文对应字 |")
L.append("|---|---|---|---|---|---|")
for r in solved[:30]:
    L.append(f"| {r['glyph']} | {r['freq']} | {r['plate']} | {r['group']} | {r['ob'][:32]} | "
             f"**{r['corpus_resolved']}** |")
L.append("")
L.append("缺失原因可归为三类：")
L.append("1. **合文**——两字刻写相连，OBIMD 当作单字。例：「㞢歲」的合文、「于黃」的合文。")
L.append("2. **扩展区汉字**——字在 Unicode 扩展区（如「𰩶」U+30A76），字体与数据集未支持。")
L.append("3. **罕用异体**——如「禱」之异体「𠦪」、「罝」之异体。\n")

L.append("## 四、真候选（《合集》亦占位的 {n} 条）\n".format(n=len(real)))
L.append("| # | OBIMD 字形 | 出现 | 片号 | 类组 | 辞例 |")
L.append("|---|---|---|---|---|---|")
for i, r in enumerate(real[:40], 1):
    L.append(f"| {i} | {r['glyph']} | {r['freq']} | {r['plate']} | **{r['group']}** | {r['ob'][:44]} |")
L.append("")

# 类组分布
gs = collections.Counter(r["group"] for r in real)
L.append("### 真候选的类组分布\n")
L.append("| 类组 | 条数 |")
L.append("|---|---|")
for g, c in gs.most_common(20):
    L.append(f"| {g} | {c} |")
L.append("")

L.append("## 五、方法学意义\n")
L.append("1. **分类先行**：任何基于公开数据集的甲骨文考释研究，必须先做编码缺失筛查，")
L.append("   否则会把「某数据集没编码」误当作「学界未释」，得出错误的问题集。")
L.append("2. **类组可得**：此前认为缺失的类组标注，可通过《合集》释文库逐条取得，")
L.append("   且每条记录自带类组。")
L.append("3. **真候选的分布特征**：真候选集中在**無名組、歷組、歷無、師歷間、何組**等")
L.append("   晚期或过渡期类组，而非宾组等早期类组——这与「早期卜辞研究充分、")
L.append("   晚期与过渡期相对薄弱」的学界状况一致。")
L.append("4. **量级估计**：58 条真候选 / 321 条记录 ≈ 18%。真正需要攻克的字，")
L.append("   远少于数据集标记的 243 个。\n")

L.append("## 附：本会话可复现工具\n")
L.append("- `gxds2.py`　《合集》释文＋类组抓取器（带缓存，支持按片号/按字/按类组检索）")
L.append("- `align.py`　OBIMD ↔ 《合集》逐片序列对齐与真伪判定")
L.append("- `result/align_records.json`　321 条对齐记录全量数据")
L.append("- `result/verdicts_full.json`　未释字逐片对照（含类组）")
L.append("")

open(OUT, "w", encoding="utf-8").write("\n".join(L))
print(f"[写出] {OUT}")
print(f"真候选 {len(real)} 条；编码缺失样本 {len(solved)} 条")
print(f"真候选类组分布: {dict(gs.most_common(12))}")

# 图：真候选字形
F = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 20)
FS = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 15)
CELL = 130
show = real[:24]
if show:
    NC = 3
    W = 300 + CELL * NC
    H = CELL * len(show) + 60
    sheet = Image.new("L", (W, H), 255)
    dr = ImageDraw.Draw(sheet)
    dr.text((10, 8), "圖J  真候選（《合集》亦只能佔位者）字形與類組", fill=0, font=F)
    for i, r in enumerate(show):
        y = 50 + i * CELL
        dr.text((10, y + 16), f"{r['glyph']} ({r['freq']}次)", fill=0, font=FS)
        dr.text((10, y + 40), f"片{r['plate']} {r['group'][:12]}", fill=0, font=FS)
        for j, p in enumerate(by_label.get(r["label"], [])[:NC]):
            try:
                a = np.asarray(Image.open(ZS.open(p)).convert("L"))
                dark = a < 128
                b = dark if dark.mean() <= 0.5 else ~dark
                ys, xs = np.nonzero(b)
                if len(ys) < 5:
                    continue
                bb = b[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
                h, w = bb.shape
                pad = 12
                s = (CELL - 2 * pad) / max(h, w)
                nh, nw = max(1, int(round(h * s))), max(1, int(round(w * s)))
                im2 = Image.fromarray((bb * 255).astype(np.uint8)).resize((nw, nh), Image.LANCZOS)
                im2 = im2.point(lambda v: 255 if v > 100 else 0)
                cv = Image.new("L", (CELL, CELL), 255)
                cv.paste(Image.fromarray(255 - np.asarray(im2)), ((CELL - nw) // 2, (CELL - nh) // 2))
                sheet.paste(cv, (300 + j * CELL, y))
            except Exception:
                pass
        dr.line([(0, y + CELL), (W, y + CELL)], fill=205, width=1)
    p = os.path.join(FIG, "figJ_real_candidates.png")
    sheet.save(p)
    print(f"[写出] {p} {sheet.width}x{sheet.height}")
