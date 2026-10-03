# Undeciphered Oracle-Bone Glyphs: What I Did, and What I Need From You

🌐 [**中文**](README.md)　|　**English**

---

## In one sentence

I set out to decipher an undeciphered oracle-bone character. **I failed.**
But I found that most of what the `OBIMD` dataset labels "undeciphered" **is labelled wrongly** —
and I need someone who reads oracle-bone script to check two things for me.

---

## What I did

### The original goal

Decipher at least one undeciphered oracle-bone character and write it up to the standard
of the Chinese Museum of Characters' prize (a complete evidence chain:
oracle → bronze → seal script glyph evolution ＋ contextual verification ＋
phonological / loan-graph argument).

### Result: I deciphered nothing

Thirteen rounds of work. **Not one character.**

The reason is **my own limitation**: identifying rare oracle-bone graphs requires years of
specialist training. I can reliably read common characters like 「王」「貞」「卜」 on a rubbing,
but I cannot reliably identify structurally complex rare graphs — and every undeciphered
glyph is a rare graph. No amount of algorithmic method substitutes for this.

### But I found something else along the way

To attempt the decipherment I compared OBIMD against the transcriptions in 《甲骨文合集》
(Jiaguwen Heji, the standard corpus). What I found:

> **Among the 243 glyphs OBIMD labels "undeciphered", a substantial number have already
> been read in 《合集》.**

For example, this one:

<img src="glyphs/dsv4lhwhn7.png" alt="glyph" height="26" align="middle">

OBIMD says it is undeciphered. But the transcription of 《合集》 plate 17382 reads:

> 鼎（貞）：…二月**娩**，不其…生。
> *"Divined: ... in the second month she gave birth; will it not be ... born."*

**It is 「娩」 (childbirth).** It appears as "undeciphered" in OBIMD only because
**the oracle-bone form of 「娩」 is not in Unicode** — the dataset cannot encode it,
so it falls back to the label "no transcription" (无隶定).

And there is a sharper point: OBIMD reads this **same sentence in the same position
as 「娩」 in 18 other places**, and marks it undeciphered on plate 17382 only.
**The dataset contradicts itself.**

---

## Nine cases I verified in detail

For each, I checked the **original plate transcription** word by word
(no automatic alignment — I established that automatic alignment is only 44% accurate).
Three criteria had to hold: ① 《合集》 supplies a readable character; ② the two strings
match character-for-character apart from the target slot; ③ the immediate left and right
neighbours match exactly.

| # | Dataset says undeciphered | It is actually | Plate | 《合集》 transcription |
|---|---|---|---|---|
| 1 | <img src="glyphs/dsv4lhwhn7.png" alt="glyph" height="22"> | **娩** childbirth | 17382 | 鼎（貞）：…二月**娩**，不其…生。 |
| 2 | <img src="glyphs/qyg9g9hii5.png" alt="glyph" height="22"> | **西** west | 31983 | 丁酉卜：亞畢（以）眾涉于**西**，若。 |
| 3 | <img src="glyphs/g0o67a8jpy.png" alt="glyph" height="22"> | **宓** | 32009 | 庚午卜：**宓**芻示千。 |
| 4 | <img src="glyphs/wi7jemi7yd.png" alt="glyph" height="22"> | **丘** mound | 22454 | 叀（惠）**丘**豕于天。 |
| 5 | <img src="glyphs/xq6hizhbmv.png" alt="glyph" height="22"> | **龜** turtle | 33286 | 乙巳鼎（貞）：叀（惠）**龜**先伐。 |
| 6 | <img src="glyphs/mepmffeebh.png" alt="glyph" height="22"> | **黃** | 553 | 癸丑卜，𡧊（賓）鼎（貞）：令彗、𠅅以**黃**執。七月。 |
| 7 | <img src="glyphs/uhz6qrd2d9.png" alt="glyph" height="22"> | **安** peace | 5373 | 癸酉卜，爭鼎（貞）：王腹不**安**，亡𢓊（延）。 |
| 8 | <img src="glyphs/gbjr7sabn4.png" alt="glyph" height="22"> | **豲** | 32513 | 癸未鼎（貞）：叀（惠）今乙酉又歲于且（祖）乙五**豲**。茲用。 |
| 9 | <img src="glyphs/lsjuogr2ev.png" alt="glyph" height="22"> | **豲** | 32512 | (same text as 32513) |

**Note that none of these nine is a rare character** — they are common characters
like 安, 西, 丘, 娩.

---

## One glyph I believe is genuinely undeciphered

<img src="glyphs/gx21ndp7yy.png" alt="glyph" height="30" align="middle">

OBIMD id `gx21ndp7yy`, **54 occurrences**. This is the one I believe **nobody has read**.

**Why**: it occurs in a fixed formula in 《合集》:

```
貞 王 【this glyph】 叀（惠）吉
```

22 instances. Searching the **entire** 《合集》 transcription database for this formula,
**the slot never contains any readable character** — it is always a private-use code point
(meaning the 《合集》 compilers had to fabricate a character for it) or a lacuna.
**In other words, the 《合集》 compilers could not read it either.**

I compared it against every character I could think of; none fit:
奭, 舞, 木, 桑, 禾, 米, 東, 朱, 未, 目, 見, 望, 省, 天, 大, 夫, 文, 立, 余.

**I cannot propose a reading.** The reason: the formally closest character is 「奭」,
but 奭 is never used as a verb; meanwhile every verb that would fit the grammatical slot
is formally dissimilar. This step needs expert judgement.

---

## What I need from you

**Two things, about one hour.**

### First: check whether those 9 cases are right

| Your verdict | What follows |
|---|---|
| **Correct** | Then this conclusion becomes citable: **before doing any undeciphered-glyph study on OBIMD, you must first filter out the "not encoded by the dataset" cases — otherwise the problem set contains pseudo-problems** |
| **No. X is wrong** | I will fix it. This is the most valuable outcome |
| **The method itself is flawed** | The reliability of this whole repository must be re-assessed |

**This is data comparison, not decipherment. A graduate student who reads oracle-bone
script can do it.**

### Second: look at `gx21ndp7yy`

| Question | Why it matters |
|---|---|
| 1. Does it have an **accepted reading**? (I may have missed it) | If yes, I have the answer immediately |
| 2. If not — **is the material sufficient for a decipherment?** | Decides whether this is worth doing |
| 3. **What is missing** to advance it? | This judgement is exactly what I lack |

**What is available**: 54 occurrences, 4 distinct forms, 22 instances of a fixed formula,
a single script-group (exclusively 事何類), 35 plates, rubbings already downloaded.

---

## Where the material is

| What you need | Where |
|---|---|
| Raw verification records for the 9 cases | [result/verify9_direct.json](result/verify9_direct.json) |
| The corresponding rubbings | [data/rubbings/](data/rubbings/) (filename = plate number, zero-padded to 6) |
| Full analysis of `gx21ndp7yy` | [findings/甲骨文未释字_真候选分析_gx21ndp7yy.md](findings/甲骨文未释字_真候选分析_gx21ndp7yy.md) |
| Rubbing verification for it | [findings/甲骨文未释字_原拓核验_gx21ndp7yy.md](findings/甲骨文未释字_原拓核验_gx21ndp7yy.md) |
| All 243 labelled-undeciphered glyphs | [handoff/inventory_classified.json](handoff/inventory_classified.json) |
| Full review package (more detail than this file) | [handoff/README.md](handoff/README.md) |
| All 16 conclusion reports (Chinese) | [findings/](findings/) |

**Feedback**: [Issues](https://github.com/gaogao94/oracle-bone-undeciphered-audit/issues)

---

## Why the glyphs here are images

Oracle-bone glyphs **are not in Unicode** (OBIMD uses the private-use U+F0000 block),
so they **cannot be written as text**. All glyphs are therefore shown as images,
stored in [glyphs/](glyphs/).

Two other conventions:
- `gx21ndp7yy`, `mepmffeebh` — the dataset's internal ids, used to refer to a glyph
- `⟨▢⟩` — a site-fabricated private-use code point in a transcription, for which I have no image

---

## Appendix: what else I tried (all failed)

Recorded so that others do not repeat it:

| Attempt | Result |
|---|---|
| Seven glyph-similarity metrics (IoU, cosine, projection, grid occupancy, parts, blocks …) | **All lack discriminative power.** Within-character IoU across variants (中 0.151, 史 0.068) is the **same order of magnitude** as the highest cross-character IoU (冊 0.241) — the signal is swamped by intra-character variation |
| Image retrieval using rubbings cut by bounding box | top-1 **6.0%**, below chance |
| Automatic alignment of OBIMD against 《合集》 | accuracy only **44%**, hence this repository does not trust automatic results |
| Hypotheses 「<img src="glyphs/gx21ndp7yy.png" alt="glyph" height="22" align="middle">=彡」, 「<img src="glyphs/gx21ndp7yy.png" alt="glyph" height="22" align="middle">=率」, 「<img src="glyphs/gx21ndp7yy.png" alt="glyph" height="22" align="middle">=天」 | **all three falsified** |

**One methodological warning**: OBIMD facsimiles **regularise worn areas**
(the middle element of `gx21ndp7yy` is triangular in the rubbing but drawn as a rectangle
in the facsimile). **Any structural judgement must go back to the rubbing.**

---

## License

Original content in this repository is licensed **CC BY-SA 4.0 (Attribution ＋ ShareAlike)**.
Use requires attribution, and derivative works must carry the same licence.
See [LICENSE](LICENSE), [NOTICE.md](NOTICE.md).

**Third-party material is not covered**: 《合集》 transcriptions and rubbing plates,
the OBIMD dataset, 殷契文渊 glyph data, cited literature. See [ATTRIBUTION.md](ATTRIBUTION.md).

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
