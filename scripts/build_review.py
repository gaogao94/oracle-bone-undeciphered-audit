# -*- coding: utf-8 -*-
"""
组装「形 / 辞例 / 音」三类证据齐备的候选审阅包
每条假设输出：
  ① 辞例证据：本字辞例、平行辞例、同位字、片号
  ② 字形证据：该字形类的字形数、异构体数、与已释字基准的比较
  ③ 音韵证据：本字（未释，无音）↔ 假设读法 ↔ 平行同位字的音韵相容性
  ④ 回查结果：假设成立后形成的辞例在语料中的出现次数
  ⑤ 待人工判定事项：明确列出机器无法判定的部分
"""
import io, json, os, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
OB = os.path.join(D, "obimd")
RES = os.path.join(HERE, "result")
PHON = os.path.join(D, "cache_phon.json")

solv = json.load(open(os.path.join(RES, "hapax_solvability_v3.json"), encoding="utf-8"))
glyph = json.load(open(os.path.join(RES, "glyph_evidence.json"), encoding="utf-8"))
hypchk = json.load(open(os.path.join(RES, "hypothesis_check.json"), encoding="utf-8"))
phon = json.load(open(PHON, encoding="utf-8")) if os.path.exists(PHON) else {}
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))

hypmap = {h["glyph"]: h for h in hypchk}
glmap = {g["glyph"]: g for g in glyph["enriched"]}


def ph(ch):
    r = phon.get(ch) or {}
    s = r.get("systems") or {}
    return s, r.get("guangyun")


def rhyme_of(ch):
    s, _ = ph(ch)
    for k in ("王力系统", "黄侃系统", "白一平－沙加尔系统", "郑张尚芳系统", "unknown"):
        if k in s:
            return s[k]
    return None


# 只取 hapax 且有平行辞例的
rows = [r for r in solv["rows"] if r["occurrences"] == 1 and r["parallel"]]
rows.sort(key=lambda r: (-(hypmap.get(r["glyph"], {}).get("full", 0)), r["glyph"]))

print(f"待组装假设数：{len(rows)}")
print(f"音韵缓存可用字数：{len(phon)}\n")

review = []
for r in rows:
    g, lab = r["glyph"], r["label"]
    p = r["parallel"][0]
    sub = p["substitute"]
    h = hypmap.get(g, {})
    ge = glmap.get(g, {})

    sub_rh = rhyme_of(sub)
    sub_ph, sub_gy = ph(sub)

    rec = {
        "glyph": g, "label": lab,
        "evidence_context": {                      # ① 辞例
            "own_sentence": r["contexts"][0] if r["contexts"] else None,
            "parallel_sentence": p["parallel_line"],
            "substitute": sub, "substitute_freq": p["sub_freq"],
            "own_piece": r["pieces"][0] if r["pieces"] else None,
            "parallel_piece": p["piece"],
            "n_parallel_found": len(r["parallel"]),
        },
        "evidence_form": {                         # ② 字形
            "n_glyphs": ge.get("n_glyphs"),
            "n_sublabels": ge.get("n_sublabels"),
            "deciphered_mean_glyphs": round(glyph["stats"]["known_glyph_mean"], 1),
            "note": "字形数远低于已释字均值 → 该形出现频次低、变体少，笔画细部无多例可比",
        },
        "evidence_phon": {                         # ③ 音韵
            "own": "未释字，无音韵信息",
            "substitute_systems": sub_ph,
            "substitute_rhyme": sub_rh,
            "substitute_guangyun": sub_gy,
        },
        "crosscheck": {                            # ④ 回查
            "hypothesis_full_sentence": h.get("hypothesis"),
            "full_corpus_hits": h.get("full", 0),
            "fragment_hits": h.get("fragment", 0),
        },
        "human_verdict_needed": [                  # ⑤
            "比对本字拓片与假设读法的字形是否同构（需图像判定）",
            "确认该片所属类组/时期，检验类组分布是否互补",
            "核对本字是否为已知字的异体（查《甲骨文字编》《新甲骨文编》著录）",
        ],
    }
    review.append(rec)

# ---------------- 输出 markdown
with open(os.path.join(RES, "review_package.md"), "w", encoding="utf-8") as f:
    f.write("# 未释字候选审阅包（形 / 辞例 / 音 三类证据链）\n\n")
    f.write("> 语料：OBIMD（CC-BY-4.0，10,077 片）｜生成日期：2026-10-02\n")
    f.write("> **本包输出的是待审假设，不是释读结论。** 每条末尾列出必须由人判定的部分。\n\n")
    f.write(f"- 候选总数：{len(review)}（从 161 个 hapax 中筛出）\n")
    f.write(f"- 筛选条件：同长度辞例中，**其余位置全部为已释字**，且同位为已释字\n\n")
    f.write("---\n\n")
    for i, rec in enumerate(review, 1):
        f.write(f"## {i}. 字形 {rec['glyph']}（内部编号 `{rec['label']}`）\n\n")
        ec = rec["evidence_context"]
        f.write("### ① 辞例证据\n\n")
        f.write(f"- 本字辞例（□=本字）：`{ec['own_sentence']}`　片号 **{ec['own_piece']}**\n")
        f.write(f"- 平行辞例（□=同位已释字）：`{ec['parallel_sentence']}`　片号 **{ec['parallel_piece']}**\n")
        f.write(f"- 平行辞例推出的同位字：**{ec['substitute']}**"
                f"（该字在语料中出现 {ec['substitute_freq']} 次）\n")
        f.write(f"- 共找到合格平行辞例 {ec['n_parallel_found']} 条\n\n")
        ef = rec["evidence_form"]
        f.write("### ② 字形证据\n\n")
        f.write(f"- 该字形类含 **{ef['n_glyphs']}** 个具体字形、{ef['n_sublabels']} 个异构体\n")
        f.write(f"- 对照：已释字平均含 {ef['deciphered_mean_glyphs']} 个字形\n")
        f.write(f"- {ef['note']}\n\n")
        ep = rec["evidence_phon"]
        f.write("### ③ 音韵证据\n\n")
        f.write(f"- 本字：{ep['own']}\n")
        f.write(f"- 假设同位字「{ec['substitute']}」：{ep['substitute_systems'] or '未取到'}"
                f"　《广韵》{ep['substitute_guangyun'] or '—'}\n\n")
        cc = rec["crosscheck"]
        f.write("### ④ 假设回查\n\n")
        f.write(f"- 假设成立后形成的辞例：`{cc['hypothesis_full_sentence']}`\n")
        f.write(f"- 该辞例在语料中出现 **{cc['full_corpus_hits']}** 次"
                f"（相邻二字组合出现 {cc['fragment_hits']} 次）\n\n")
        f.write("### ⑤ 必须由人判定\n\n")
        for x in rec["human_verdict_needed"]:
            f.write(f"- [ ] {x}\n")
        f.write("\n---\n\n")

json.dump({"n": len(review), "review": review},
          open(os.path.join(RES, "review_package.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# ---------------- 控制台摘要
print("=" * 96)
print("审阅包摘要（按 回查命中 降序）")
print("=" * 96)
print(f"{'字形':>4} {'假设读法':<22} {'完整串':>5} {'字形数':>5} {'已释均值':>7} {'同位字音韵':<16}")
print("-" * 96)
for rec in review:
    ec, ef, ep, cc = (rec["evidence_context"], rec["evidence_form"],
                      rec["evidence_phon"], rec["crosscheck"])
    print(f"{rec['glyph']:>4} {str(cc['hypothesis_full_sentence']):<22} "
          f"{cc['full_corpus_hits']:>5} {ef['n_glyphs']:>5} {ef['deciphered_mean_glyphs']:>7} "
          f"{str(ep['substitute_rhyme'] or '—'):<16}")

print(f"\n[写出] result/review_package.md")
print(f"[写出] result/review_package.json")
