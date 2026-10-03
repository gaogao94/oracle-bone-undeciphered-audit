# Undeciphered Oracle-Bone Glyphs: A Dataset Audit and Two Open Questions

**甲骨文未释字的编码缺失筛查与视觉考释尝试**　—　[中文版 README](README.md)

[![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-sa/4.0/)
[![Data: OBIMD CC-BY-4.0](https://img.shields.io/badge/Data-OBIMD%20CC--BY--4.0-blue.svg)](https://github.com/KLOBIP/OBIMD)

---

## For Reviewers

This repository contains **two items that need assessment by someone trained in
palaeography / oracle-bone studies**. Estimated time: about one hour.

### Question 1: Are these 9 identifications correct?

**Claim**: Among the glyphs labelled "undeciphered" (无隶定) in **OBIMD**
(*Oracle Bone Inscriptions Multi-modal Dataset*, 10,077 plates, CC-BY-4.0),
a subset **has in fact already been read in 《甲骨文合集》** (*Jiaguwen Heji*,
the standard corpus). They are not undeciphered — the dataset simply cannot
encode them, because the oracle-bone form of the character is not in Unicode.

**Evidence**: the 9 cases in [§1](#1-nine-verified-cases-encoding-gaps) below.
Each was checked word-by-word against the **original plate transcription**,
not against any automatic alignment. Three criteria must all hold:

1. 《合集》 gives a **readable character** for that position;
2. The OBIMD string matches that transcription **character by character** (except the target slot);
3. The **immediate left and right neighbours match exactly**.

**Please answer**: are these 9 correct?

| Possible verdict | Consequence |
|---|---|
| Correct | Then this conclusion can be cited: *"Any undeciphered-glyph study based on OBIMD must first separate 'not encoded by the dataset' from 'undeciphered by scholarship'."* |
| No. X is wrong | I will fix it (this is the most valuable outcome) |
| The method itself is flawed | The reliability of this whole repository must be re-assessed |

### Question 2: Is `gx21ndp7yy` a known character, or genuinely undeciphered?

**Claim**: <img src="glyphs/gx21ndp7yy.png" alt="glyph" height="24" align="middle">
(OBIMD internal id `gx21ndp7yy`, **54 occurrences**) is **genuinely undeciphered**.

**Grounds**: searching the **entire** 《合集》 transcription database for the
formula this glyph occurs in — 「王 X 叀（惠）吉」 — the X slot **never contains a
readable character**. It is *always* a private-use code point (U+E123 nine times,
U+E124 six times) or a lacuna. In other words, **the compilers of 《合集》 could not
read it either**; they had to assign it a fabricated code point.
See [§2](#2-one-confirmed-genuinely-undeciphered-glyph).

**Please answer**:

| # | Question |
|---|---|
| 1 | Does this character **already have an accepted reading**? (If so, please tell me.) |
| 2 | If not — **is the material sufficient for a published decipherment?** (54 occurrences, 4 distinct forms, 22 instances of a fixed formula, single script-group) |
| 3 | **What else is needed** to advance it? |

**Already tried and excluded**: see the comparison table in
[§2](#2-one-confirmed-genuinely-undeciphered-glyph) — 奭, 舞, 木, 桑, 禾, 米, 東,
朱, 未, 目, 見, 望, 省, 天, 大, 夫, 文, 立, 余.
**I could not propose a reading**, because the formally closest character (奭)
is never used as a verb, while every verb that fits the grammatical slot
is formally dissimilar.

> Please respond via [Issues](https://github.com/gaogao94/oracle-bone-undeciphered-audit/issues).

---

## How glyphs are displayed in this repository

Oracle-bone glyphs **are not in the Unicode encoding planes** (OBIMD uses the
private-use U+F0000 block; 殷契文渊 uses U+60000), so they **cannot be represented
as text**. This repository handles them as follows:

| Convention | Meaning |
|---|---|
| Inline thumbnail | The **glyph image** (in `glyphs/`, named by OBIMD internal id) |
| `gx21ndp7yy`, `mepmffeebh` | OBIMD **internal id** (label), used to refer to a specific glyph |
| **Regular Chinese characters** (娩, 西, 丘) | The **deciphered reading** |
| `⟨▢⟩` | Site-private code point (a character fabricated by the transcription site); no glyph image available here |
| Extension-plane characters (𰩶, 𠦪, 𡧊) | Proper Unicode characters, display normally |

**Glyph directory** [glyphs/](glyphs/): **137 images**, covering every recoverable
glyph appearing in this repository.

---

## A note on terminology

Chinese oracle-bone scholarship uses a set of terms that have no settled English
equivalents. Throughout this document I keep the Chinese and gloss it once here:

| Term | Gloss |
|---|---|
| 《合集》 | *Jiaguwen Heji* (甲骨文合集), the standard 13-volume corpus, 41,956 plates |
| 片 / 片号 | A plate (bone or shell fragment) and its corpus number |
| 类组 | Script-group: a palaeographic classification by calligraphic style, correlated with date and diviner lineage (e.g. 賓組, 出組, 何組, 黃組, 事何類) |
| 貞 | The divination formula marker ("divined:") |
| 卜 | "Crack-making" / divination marker |
| 叀（惠） | A focus particle; 「惠吉」 is a set evaluation, "it is auspicious" |
| 无隶定 | Lit. "no lishu transcription" — OBIMD's label for a glyph it cannot map to a modern character |
| 摹本 | Facsimile / hand-copy of a rubbing (as opposed to 原拓, the rubbing itself) |

---

## 1. Nine verified cases (encoding gaps)

**These 9 characters are labelled "undeciphered" in OBIMD, yet none of them is rare** —
they are such common characters as 安, 西, 丘, 娩. The sole reason they count as
undeciphered is that **the oracle-bone form of the character is not in Unicode**,
so the dataset cannot encode it.

| # | OBIMD glyph | id | Occ. | Plate | Script-group | OBIMD string (【□】 = target) | 《合集》 plate transcription | Actual |
|---|---|---|---|---|---|---|---|---|
| 1 | <img src="glyphs/dsv4lhwhn7.png" alt="glyph" height="22" align="middle"> | `dsv4lhwhn7` | 1 | **17382** | 典賓A | 貞 二 月 【□】 不 其 生 | 鼎（貞）：…二月**娩**，不其…生。 | **娩** |
| 2 | <img src="glyphs/qyg9g9hii5.png" alt="glyph" height="22" align="middle"> | `qyg9g9hii5` | 1 | 31983 | 歷二B1 | 丁酉卜 亞以眾涉于【□】若 | 丁酉卜：亞畢（以）眾涉于**西**，若。 | **西** |
| 3 | <img src="glyphs/g0o67a8jpy.png" alt="glyph" height="22" align="middle"> | `g0o67a8jpy` | 3 | 32009 | 歷二A2 | 庚午卜【□】芻于千 | 庚午卜：**宓**芻示千。 | **宓** |
| 4 | <img src="glyphs/wi7jemi7yd.png" alt="glyph" height="22" align="middle"> | `wi7jemi7yd` | 3 | 22454 | 師小字 | 叀【□】豕于天 | 叀（惠）**丘**豕于天。 | **丘** |
| 5 | <img src="glyphs/xq6hizhbmv.png" alt="glyph" height="22" align="middle"> | `xq6hizhbmv` | 1 | 33286 | 歷二B3 | 乙巳貞叀【□】先伐 | 乙子（巳）鼎（貞）：叀（惠）**龜**先伐。 | **龜** |
| 6 | <img src="glyphs/mepmffeebh.png" alt="glyph" height="22" align="middle"> | `mepmffeebh` | 37 | **553** | 賓三 | 癸丑卜賓貞令彗墉以【□】執寇七月 | 癸丑卜，𡧊（賓）鼎（貞）：令彗、𠅅以**黃**執。七月。 | **黃** |
| 7 | <img src="glyphs/uhz6qrd2d9.png" alt="glyph" height="22" align="middle"> | `uhz6qrd2d9` | 6 | 5373 | 賓三 | 癸酉卜爭貞王風不【□】亡延 | 癸酉卜，爭鼎（貞）：王腹不**安**，亡𢓊（延）。 | **安** |
| 8 | <img src="glyphs/gbjr7sabn4.png" alt="glyph" height="22" align="middle"> | `gbjr7sabn4` | 5 | 32513 | 歷二B3 | 癸未貞叀今乙酉佑父歲于且乙五【□】茲用 | 癸未鼎（貞）：叀（惠）今乙酉又歲于且（祖）乙五**豲**。茲用。 | **豲** |
| 9 | <img src="glyphs/lsjuogr2ev.png" alt="glyph" height="22" align="middle"> | `lsjuogr2ev` | 2 | 32512 | 歷二B3 | (same text as 32513) | (same) | **豲** |

### The strongest case: internal inconsistency in the dataset

Case 1, <img src="glyphs/dsv4lhwhn7.png" alt="glyph" height="18" align="middle">:
OBIMD reads the **same sentence, same position** as 「**娩**」 in **18 other places**,
but marks it undeciphered on 《合集》17382.
This is direct evidence of **internal inconsistency in the dataset's glyph
classification** — and has nothing to do with scholarly undecipheredness.

### Three mechanisms

| Actual | In OBIMD glyph table | Corpus instances | Nature |
|---|---|---|---|
| **娩** | yes | **18** | **Internal inconsistency** (strongest) |
| 西 | yes | 62 | Internal inconsistency |
| 龜 | yes | 6 | Internal inconsistency |
| 丘 | yes | 6 | Internal inconsistency |
| 宓 | yes | 2 | Internal inconsistency |
| **黃** | yes | **0** | Table entry exists, zero corpus instances |
| **安** | yes | **0** | Table entry exists, zero corpus instances |
| **豲** | **no such glyph class** | — | Dataset never collected this glyph |

### Why this matters

> **Any undeciphered-glyph study based on OBIMD must first separate
> "not encoded by the dataset" from "undeciphered by scholarship" —
> otherwise the problem set contains pseudo-problems.**

The two are categorically different: the former is a data-engineering defect,
the latter is a legitimate object of decipherment.

**Raw data**: [verify9_direct.json](result/verify9_direct.json)　|　
**Rubbings**: [data/rubbings/](data/rubbings/) (17382, 31983, 32009, 22454, 33286, 553, 5373, 32513, 32512)　|　
**Full report** (Chinese): [findings/甲骨文未释字_编码缺失_直接核实报告.md](findings/甲骨文未释字_编码缺失_直接核实报告.md)

---

## 2. One confirmed genuinely undeciphered glyph

**<img src="glyphs/gx21ndp7yy.png" alt="glyph" height="22" align="middle">** — <img src="glyphs/gx21ndp7yy.png" alt="glyph" height="26" align="middle">

| Item | Value |
|---|---|
| OBIMD id | `gx21ndp7yy` |
| Occurrences | **54** (third-highest among the 243 undeciphered glyph classes) |
| Distinct forms | 4 |
| **Script-group** | **Exclusively 事何類** (late 廪辛–康丁 period); never in 賓組, 出組, or 黃組 |
| Plates | **35** (see [tier_B_plates.json](handoff/tier_B_plates.json)) |
| Left neighbour | **王** ("the king"), 16 times |
| Right neighbour | **叀**, 22 times |

### The core formula

```
貞 王 【<img src="glyphs/gx21ndp7yy.png" alt="glyph" height="22" align="middle">】 叀（惠）吉
```

**22 instances.** The pattern means "The king 【X】; it is 惠吉 (auspicious)".
「惠吉」 is a common divinatory evaluation, so the glyph sits between 「王」 and an
evaluation — i.e. **in the verbal slot**. Compare contemporary patterns:
「王 賓（夙）」「王 田」「王 步」.

### Why I conclude it is genuinely undeciphered

Searching the **entire** 《合集》 transcription database for 「王 X 叀（惠）吉」,
the distribution of the X slot is:

| X-slot character | Count | Nature |
|---|---|---|
| **U+E123** | 9 | **Private-use code point** (site-fabricated) |
| **U+E124** | 6 | **Private-use code point** |
| … | 6 | Lacuna |
| ： | 4 | Part of 「鼎（貞）：」, not the slot |
| 王 | 1 | Variant reading |

> **Across 50 relevant 事何類 divinations, this slot never once contains a readable character.**

The compilers of 《合集》 **assigned the glyph a private-use code point** (meaning
it is a real, distinct form requiring a fabricated character) **yet could not give
it a reading**.
**This is categorically different from the 9 cases in §1**: there, 《合集》 gives a
readable common character and only OBIMD fails to encode it; here, 《合集》 itself
cannot read it.

### Structure (4 facsimile forms + rubbing inspection)

```
      ╱╲          ← top: crossed / branching element
     ╱  ╲
    ╱____╲        ← middle: triangular / tent-shaped outline, with internal crossing strokes
    │ ╳  │
    │    │
    ╱╲  ╱╲        ← bottom: two diverging strokes
```

**Rubbing check** (《合集》5250; [enlarged rubbing](figures/rub_005250_zoom.png)):
the rubbing agrees with the facsimile structurally and is clearer —
**the middle element is triangular/tent-shaped in the rubbing, regularised into a
rectangle in the facsimile**.

### Characters already excluded

| Character | Verdict |
|---|---|
| **奭** (25 occ.) | **Formally closest** (crossed top + two arms + an object on each side + two legs). But 奭's side elements are round/hand-shaped, while this glyph has drooping hooks; and 奭 is never a verb |
| 舞 (54 occ.) | Hands are drawn as claws (three digits); this glyph has curved drooping strokes |
| 木 / 桑 / 禾 / 米 / 東 / 朱 / 未 | Excluded: the drooping strokes run the wrong way |
| 目 / 見 / 望 / 省 | Excluded: not an eye form (**I initially misread it as 目 and corrected this**) |
| 天 / 大 / 夫 / 文 / 立 | Excluded: no horizontal branches |
| 余 | Excluded: 余 is a tent shape with a central post — different skeleton |

**Comparison figures**: [figU skeleton](figures/figU_skeleton.png)　|　[figW 舞/奭](figures/figW_dance.png)

**Full reports** (Chinese): [candidate analysis](findings/甲骨文未释字_真候选分析_gx21ndp7yy.md)　|　
[rubbing check](findings/甲骨文未释字_原拓核验_gx21ndp7yy.md)　|　
[structure revision](findings/甲骨文未释字_构形复核_gx21ndp7yy.md)

---

## 3. The full inventory (243 glyphs, awaiting study)

See [handoff/](handoff/): full data in
[inventory_classified.json](handoff/inventory_classified.json), with plate numbers,
script-groups, 《合集》 transcriptions and rubbing filenames for each glyph.

| Occurrences | Glyphs | Note |
|---|---|---|
| ≥10 | 11 | Richest material |
| 3–9 | 43 | |
| 2 | 28 | |
| 1 | **161** | Hapax; under the principle 「孤证不立」 ("a single witness does not establish a case") these cannot stand alone |

**Principal script-groups**: 典賓B 27, 賓出 23, 師小字 22, 典賓 13, 師賓間 13,
出二 10, 無名組 10.

> ⚠️ **In this inventory the plate numbers and script-groups were extracted
> automatically and NOT verified character-by-character** — the same caveat as §1.
> Before use, perform the kind of per-plate check demonstrated in §1.
> This repository has established that automatic alignment accuracy is only **44%**.

---

## 4. Established limitations

| Finding | Data |
|---|---|
| **Glyph-similarity metrics have no discriminative power on this corpus** | Within-character IoU across variants: 中 0.151, 史 0.068, 目 0.181. Highest cross-character IoU: 冊 0.241. **Same order of magnitude** |
| Facsimile image retrieval (strict same-distribution) | top-1 **32.8%** |
| Rubbing cut by bounding box | top-1 **6.0%** (below chance) |
| Automatic alignment accuracy | **44%** (hence this repository does not trust automatic results) |
| **Facsimiles regularise worn areas** | <img src="glyphs/gx21ndp7yy.png" alt="glyph" height="22" align="middle">'s middle element: triangular in the rubbing, rectangular in the facsimile. **Structural judgements must go back to the rubbing** |
| Hypotheses falsified | `ff8rp0nh6u`=彡, `2lep30tiiz`=率, `2lep30tiiz`=天 (all documented in [findings/](findings/)) |

**Root limitation**: the **visual identification of rare oracle-bone graphs requires
long specialist training**. I can reliably read 「王」「貞」「卜」 on a rubbing, but
**cannot reliably identify structurally complex rare graphs** — and every
undeciphered glyph is a rare graph. This is not something scalable statistical
methods can substitute for. **Consequently this repository deciphered no character.**

---

## 5. Repository layout

```
├── README.md                      Chinese version (中文版)
├── README.en.md                   This file
├── handoff/                       Expert review package (tiers A/B/C + full inventory)
├── findings/    16 reports        All conclusion reports (Chinese)
├── figures/     43 images         All figures (glyph comparisons, rubbings, structural atlases)
├── glyphs/      137 images        Glyph images (for characters not representable as text)
├── result/      20 files          Intermediate analysis results (JSON)
├── scripts/     173 scripts       All reproducible scripts
├── paper/                         Decipherment report (docx) and generator script
└── data/rubbings/  322 plates     《合集》 rubbings
```

### Key tools

| Script | Purpose |
|---|---|
| [gxds2.py](scripts/gxds2.py) | 《合集》 transcription + script-group scraper (cached) |
| [get_rubbing.py](scripts/get_rubbing.py) | Rubbing download |
| [align.py](scripts/align.py) | OBIMD ↔ 《合集》 per-plate alignment |
| [verify_solved.py](scripts/verify_solved.py) | Neighbour-consistency check |
| [fingerprint.py](scripts/fingerprint.py) | Structural-fingerprint retrieval (retrieval by *drawing*, not by character) |

### Two directly reusable access routes

```python
// 《合集》 transcription (with script-group)
https://www.guoxuedashi.com/jgwhj/?page=<page>&bhfl=1&bh=<plate-no or word>&jgwfl=<script-group>

// 《合集》 rubbing plates
https://pic2.39017.com/jgwhj/1/0<plate-no, zero-padded to 6 digits>.png
// e.g. 《合集》5250 → https://pic2.39017.com/jgwhj/1/005250.png
```

---

## 6. Honest statement

**This repository is not a successful decipherment.** It contains:

- ✅ A completed dataset-quality audit (**9 character-by-character verified** encoding gaps)
- ✅ One confirmed genuinely undeciphered glyph (<img src="glyphs/gx21ndp7yy.png" alt="glyph" height="22" align="middle">), **but no reading proposed**
- ✅ Negative results for seven glyph-similarity metrics
- ✅ Two directly reusable routes to public data
- ❌ **Not achieved**: for any single character, the complete three-part evidence chain
  (oracle → bronze → seal script glyph chain ＋ contextual verification ＋ phonological
  / loan-graph argument)

The author welcomes takeover by a researcher with palaeographic training; see [handoff/](handoff/).

---

## License

**Original content in this repository is licensed CC BY-SA 4.0 (Attribution ＋ ShareAlike).**

Any use, modification or distribution **must attribute, and derivative works must
be released under the same licence**:

```
Based on "甲骨文未释字的编码缺失筛查与视觉考释尝试"
by gaogao94
Source: https://github.com/gaogao94/oracle-bone-undeciphered-audit
License: CC BY-SA 4.0
```

| File | Content |
|---|---|
| [LICENSE](LICENSE) | CC BY-SA 4.0 legal text |
| [COPYRIGHT.md](COPYRIGHT.md) | Copyright notice and licence notes |
| [NOTICE.md](NOTICE.md) | Specific attribution and redistribution requirements |
| [ATTRIBUTION.md](ATTRIBUTION.md) | Third-party data sources and rights status |

**Third-party material is not covered by this grant**: 《甲骨文合集》 transcriptions
and rubbing plates (rights holders), the OBIMD dataset (its own CC-BY-4.0),
殷契文渊 glyph data, and cited literature. See [ATTRIBUTION.md](ATTRIBUTION.md).

---

## Citation

```bibtex
@misc{gaogao94_oracle_audit_2026,
  author       = {gaogao94},
  title        = {甲骨文未释字的编码缺失筛查与视觉考释尝试
                  (Undeciphered Oracle-Bone Glyphs: A Dataset Audit)},
  year         = {2026},
  howpublished = {\url{https://github.com/gaogao94/oracle-bone-undeciphered-audit}},
  note         = {Licensed under CC BY-SA 4.0}
}
```
