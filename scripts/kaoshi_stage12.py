# -*- coding: utf-8 -*-
"""
阶段 I-III 原型：匿名字形筛选 → 辞例证据向量 → 候选排序
数据：OBIMD (CC-BY-4.0) 10,077 片逐字标注，含阅读顺序与辞例分组
判据来源：唐兰四法 / 裘锡圭「字形之无忤，文义之大安」/ 中国文字博物馆设奖公告
          以及蒋玉斌（蠢）、陈剑（徹）、王子杨（阱）三项获奖案例的实际论证结构
"""
import io, json, math, os, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data", "obimd")
OUT = os.path.join(HERE, "data")
RES = os.path.join(HERE, "result")
os.makedirs(RES, exist_ok=True)

data = json.load(open(os.path.join(D, "data.json"), encoding="utf-8"))
mc = json.load(open(os.path.join(D, "main_character.json"), encoding="utf-8"))

# ---------------------------------------------------------------- 载入
# 重建每条辞例的字符序列（按 OrderNumber 排序）
sentences = []          # [(piece_idx, group_idx, category, [label,...])]
for pi, piece in enumerate(data):
    for gi, grp in enumerate(piece.get("RecordUtilSentenceGroupVoList") or []):
        chars = grp.get("RecordUtilOracleCharVoList") or []
        seq = [(c.get("OrderNumber") or 0, c.get("Label"))
               for c in chars if c.get("Label")]
        seq.sort(key=lambda x: x[0])
        labels = [l for _, l in seq]
        if labels:
            sentences.append((pi, gi, grp.get("GroupCategory"), labels))

print(f"辞例总数（有字）        {len(sentences):,}")
lens = [len(s[3]) for s in sentences]
print(f"辞例长度：均值 {sum(lens)/len(lens):.1f}，中位 {sorted(lens)[len(lens)//2]}，最长 {max(lens)}")
print(f"长度≥5 的辞例           {sum(1 for x in lens if x>=5):,} "
      f"({sum(1 for x in lens if x>=5)/len(lens):.1%})")

# 字形类 → 是否已释
def label_text(lab):
    e = mc.get(lab) or {}
    tr = e.get("transcription") or []
    cp = e.get("codepoint") or ""
    return {"codepoint": cp, "transcription": tr,
            "is_anon": len(tr) == 0}

freq = collections.Counter()
for _, _, _, labels in sentences:
    freq.update(labels)

anon = {l for l in freq if (mc.get(l, {}).get("transcription") or []) == []}
print(f"\n字形类总数              {len(freq):,}")
print(f"其中匿名字形（无隶定）   {len(anon):,} ({len(anon)/len(freq):.1%})")
anon_tok = sum(freq[l] for l in anon)
print(f"匿名字形 token 数        {anon_tok:,} / {sum(freq.values()):,} "
      f"({anon_tok/sum(freq.values()):.1%})")

# ---------------------------------------------------------------- 阶段 I
# 筛选：孤证不立 → 只保留有 ≥3 次辞例证据的匿名字形
MIN_OCC = 3
cands = {l: freq[l] for l in anon if freq[l] >= MIN_OCC}
print(f"\n[阶段I] 出现 ≥{MIN_OCC} 次的匿名字形  {len(cands):,}")
band = collections.Counter()
for l in anon:
    v = freq[l]
    b = "1次" if v == 1 else "2次" if v == 2 else "3-4" if v <= 4 else "5-9" if v <= 9 else "10-49" if v <= 49 else "≥50"
    band[b] += 1
print("  匿名字形频段分布:", dict(band))

# ---------------------------------------------------------------- 阶段 II
# 辞例证据向量：槽位画像 + 共现 + 句法位置分布
POS_NAME = {0: "句首", 1: "句末", 2: "句中"}


def profile(lab):
    occ = []            # 每次出现：位置类别、左邻、右邻、句长、类别
    for pi, gi, cat, labels in sentences:
        n = len(labels)
        for i, l in enumerate(labels):
            if l != lab:
                continue
            slot = "句首" if i == 0 else ("句末" if i == n - 1 else "句中")
            occ.append({
                "piece": data[pi].get("RubbingName"),
                "cat": cat, "slot": slot, "sent_len": n, "pos": i,
                "left": labels[i - 1] if i > 0 else None,
                "right": labels[i + 1] if i < n - 1 else None,
            })
    left = collections.Counter(o["left"] for o in occ if o["left"])
    right = collections.Counter(o["right"] for o in occ if o["right"])
    slots = collections.Counter(o["slot"] for o in occ)
    cats = collections.Counter(o["cat"] for o in occ)
    return occ, left, right, slots, cats


def ctx_str(lab_seq, target):
    return " ".join(("□" if l == target else
                     (mc.get(l, {}).get("codepoint") or "?") ) for l in lab_seq)


def cp(lab):
    """字形类 -> 现代字（无则回退到内部编号）"""
    return mc.get(lab, {}).get("codepoint") or lab


def join_neighbors(pairs, k=6):
    """[(label, count)] -> '字×次数、…'"""
    if not pairs:
        return "—"
    return "、".join(f"{cp(l)}×{c}" for l, c in pairs[:k])


# 排序依据：证据量 × 辞例完整度（长辞例更有价值）× 位置多样性
def score(lab):
    occ, left, right, slots, cats = profile(lab)
    n = len(occ)
    rich = sum(1 for o in occ if o["sent_len"] >= 5)
    div = len(slots)
    return n * (1 + 0.5 * rich / max(n, 1)) * (1 + 0.3 * (div - 1))


ranked = sorted(cands, key=score, reverse=True)
print(f"\n[阶段II] 候选排序完成，Top 20：")
print(f"{'字形码':>4} {'次数':>5} {'长辞例':>6} {'槽位':>4}  最高频左邻 / 右邻")
print("-" * 78)
dossiers = {}
for lab in ranked:
    occ, left, right, slots, cats = profile(lab)
    rich = sum(1 for o in occ if o["sent_len"] >= 5)
    dossiers[lab] = {
        "glyph_code": cp(lab), "label": lab, "occurrences": len(occ),
        "rich_contexts": rich, "slots": dict(slots), "categories": dict(cats),
        "left_neighbors": left.most_common(12), "right_neighbors": right.most_common(12),
        "examples": occ,
    }
    if len(dossiers) <= 20:
        L = dossiers[lab]["glyph_code"]
        lt = join_neighbors(left.most_common(3), 3)
        rt = join_neighbors(right.most_common(3), 3)
        print(f"{L:>4} {len(occ):>5} {rich:>6} {len(slots):>4}  {lt}  /  {rt}")

# ---------------------------------------------------------------- 导出
with open(os.path.join(OUT, "anon_glyphs.json"), "w", encoding="utf-8") as f:
    json.dump({"n_anon": len(anon), "n_candidates_ge3": len(cands),
               "freq_bands": dict(band),
               "freq": {l: freq[l] for l in anon}}, f, ensure_ascii=False, indent=1)

with open(os.path.join(RES, "candidates_stage2.json"), "w", encoding="utf-8") as f:
    json.dump({"method": "OBIMD order-reconstructed contexts; "
                         "stage I anon+>=3 occurrences; stage II slot/neighbor profile",
               "n_sentences": len(sentences), "n_anon": len(anon),
               "candidates": [dossiers[l] for l in ranked]},
              f, ensure_ascii=False, indent=1)

# 人可读报告
with open(os.path.join(RES, "candidates_stage2.md"), "w", encoding="utf-8") as f:
    f.write("# 阶段 I–II 候选清单（匿名字形 + 辞例证据画像）\n\n")
    f.write(f"- 语料：OBIMD 10,077 片，重建辞例 {len(sentences):,} 条\n")
    f.write(f"- 字形类 {len(freq):,}，其中匿名（无隶定）{len(anon):,}\n")
    f.write(f"- 出现 ≥3 次的匿名字形：**{len(cands):,}** 个（进入阶段 III 的字形链检验）\n\n")
    f.write("## Top 54 候选（按证据量×辞例完整度×槽位多样性排序）\n\n")
    for lab in ranked:
        d = dossiers[lab]
        L = d["glyph_code"]
        f.write(f"### {L}　（出现 {d['occurrences']} 次，长辞例 {d['rich_contexts']} 条）\n\n")
        f.write(f"- 槽位分布：{d['slots']}\n")
        f.write(f"- 高频左邻：{join_neighbors(d['left_neighbors'])}\n")
        f.write(f"- 高频右邻：{join_neighbors(d['right_neighbors'])}\n")
        f.write(f"- 辞例样本（□=本字）：\n\n")
        shown = 0
        for pi, gi, cat, labels in sentences:
            if lab in labels and len(labels) >= 4 and shown < 8:
                f.write(f"  - {ctx_str(labels, lab)}\n")
                shown += 1
        f.write("\n")

print(f"\n[写出] {os.path.join(RES, 'candidates_stage2.json')}")
print(f"[写出] {os.path.join(RES, 'candidates_stage2.md')}")
print(f"[写出] {os.path.join(OUT, 'anon_glyphs.json')}")
