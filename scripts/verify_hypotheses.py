# -*- coding: utf-8 -*-
"""验证：把平行辞例推出的假设代回语料，看形成的辞例是否为已知套语"""
import io, json, os, sys, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
OB = os.path.join(D, "obimd")
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))

sents = []
for piece in data:
    nm = piece.get("RubbingName") or "?"
    for grp in piece.get("RecordUtilSentenceGroupVoList") or []:
        seq = sorted(((c.get("OrderNumber") or 0), c.get("Label"))
                     for c in (grp.get("RecordUtilOracleCharVoList") or [])
                     if c.get("Label"))
        lab = [l for _, l in seq]
        if lab:
            sents.append((nm, lab))

cp = lambda l: mc.get(l, {}).get("codepoint") or ""
freq = collections.Counter()
for _, s in sents:
    freq.update(s)

# 已释辞例串（全部已释且非空）
decoded = {l for l in freq if (mc.get(l, {}).get("transcription") or []) != [] and cp(l)}
strings = collections.Counter()
for nm, s in sents:
    if all(l in decoded for l in s):
        strings[" ".join(cp(l) for l in s)] += 1

print(f"全已释辞例串 {len(strings)} 种，覆盖 {sum(strings.values())} 条辞例")
print("\n最高频套语（用于验证假设是否有语料支撑）：")
for k, v in strings.most_common(15):
    print(f"  {v:>4}×  {k}")

HYP = [
    ("󵖪", "卜 爭 貞", "卜爭貞"),
    ("󴲍", "己 丑", "己丑"),
    ("󹛛", "癸 亥 卜 史 貞 旬 亡", "癸亥卜史貞旬亡"),
    ("󹥠", "叀 畢 令", "叀畢令"),
    ("󴷨", "叀 畢 令", "叀畢令"),
    ("󵀈", "隹 㞢 雨", "隹㞢雨"),
    ("󾒻", "貞 以", "貞以"),
    ("󴆻", "勿 于", "勿于"),
    ("󾤶", "于 帚", "于帚"),
    ("󾣲", "自 西", "自西"),
    ("󻟟", "不 隹", "不隹"),
    ("󿧠", "來 且 乙", "來且乙"),
]
print("\n" + "=" * 76)
print("假设回查：假设成立后形成的辞例，在语料中出现多少次？")
print("=" * 76)
print(f"{'未释字':>4} {'假设读法':<22} {'完整串出现':>8} {'其片段出现':>9}")
print("-" * 76)
out = []
for glyph, hyp, _ in HYP:
    n_full = strings.get(hyp, 0)
    # 片段（连续 2 字）出现次数
    toks = hyp.split()
    frag = 0
    for i in range(len(toks) - 1):
        frag += sum(1 for s in strings if f"{toks[i]} {toks[i+1]}" in s)
    print(f"{glyph:>4} {hyp:<22} {n_full:>8} {frag:>9}")
    out.append({"glyph": glyph, "hypothesis": hyp, "full": n_full, "fragment": frag})

json.dump(out, open(os.path.join(HERE, "result", "hypothesis_check.json"),
                    "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n[写出] result/hypothesis_check.json")
print("\n解读：'完整串出现' >0 表示该读法能产生语料中真实存在的辞例；")
print("      '其片段出现' 表示即便完整串未见，其相邻二字组合在语料中有据。")
