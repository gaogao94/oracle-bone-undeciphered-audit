# -*- coding: utf-8 -*-
"""
关键工具：用《合集》释文判定 OBIMD「未释字」的真伪
原理：OBIMD 片号 H<n> ↔ 《合集》编号 n。查《合集》释文即可知该字是否已被释出。
"""
import io, os, re, sys, json, gzip, time, urllib.parse, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "data", "gxds")
os.makedirs(CACHE, exist_ok=True)
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Accept-Language": "zh-CN,zh;q=0.9", "Accept-Encoding": "gzip, deflate"}


def get(u, t=45, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=t) as r:
                b = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    b = gzip.decompress(b)
                return b.decode("utf-8", "replace")
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(1.5 * (i + 1))


def parse(html):
    out = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S | re.I):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S | re.I)
        if len(tds) < 4:
            continue
        cells = []
        for td in tds:
            s = re.sub(r"<[^>]+>", " ", td)
            s = (s.replace("&nbsp;", " ").replace("&amp;", "&")
                 .replace("&ldquo;", "「").replace("&rdquo;", "」").replace("&hellip;", "…"))
            cells.append(re.sub(r"\s+", " ", s).strip())
        if cells[0] in ("合/补", "编号") or "序号" in cells:
            continue
        if len(cells) >= 5 and cells[1].isdigit():
            out.append({"src": cells[0], "no": cells[1], "seq": cells[2],
                        "text": cells[3], "group": cells[4]})
    return out


def plate(num):
    p = os.path.join(CACHE, f"q1_{urllib.parse.quote(str(num))}_p1.html")
    if os.path.exists(p):
        html = open(p, encoding="utf-8").read()
    else:
        html = get(f"https://www.guoxuedashi.com/jgwhj/?page=1&bhfl=1&bh={num}&jgwfl=")
        open(p, "w", encoding="utf-8").write(html)
        time.sleep(0.6)
    return parse(html)


OB = os.path.join(HERE, "data", "obimd")
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
cp = lambda l: mc.get(l, {}).get("codepoint") or ""
is_anon = lambda l: (mc.get(l, {}).get("transcription") or []) == []
freq = {}
for p in data:
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        for c in g.get("RecordUtilOracleCharVoList") or []:
            if c.get("Label"):
                freq[c["Label"]] = freq.get(c["Label"], 0) + 1

# 对若干未释字：取其出现片，查《合集》释文，看该位置的字是否已被释出
TARGETS = ["fybnj2savm", "ptd0rmmnrv", "gx21ndp7yy", "urzeocieq8", "2lep30tiiz"]
print("=" * 100)
print("判定 OBIMD「未释字」的真伪：《合集》释文是否已给出该字")
print("=" * 100)
report = []
for lab in TARGETS:
    occ = []
    for p in data:
        nm = p.get("RubbingName") or ""
        for g in p.get("RecordUtilSentenceGroupVoList") or []:
            seq = sorted([c for c in (g.get("RecordUtilOracleCharVoList") or [])
                          if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
            for i, c in enumerate(seq):
                if c["Label"] == lab:
                    occ.append({"piece": nm, "idx": i,
                                "ob": [cp(x["Label"]) or "◻" for x in seq],
                                "group_cat": g.get("GroupCategory")})
    print(f"\n■ {cp(lab) or lab}（label={lab}，{freq.get(lab,0)} 次，{len(occ)} 处）")
    for o in occ[:2]:
        nm = o["piece"]
        num = nm.lstrip("H")
        print(f"   片 {nm}  OBIMD: {' '.join(o['ob'])}")
        if not num.isdigit():
            continue
        try:
            rows = plate(num)
        except Exception as e:
            print(f"     抓取失败 {e}")
            continue
        for r in rows:
            print(f"     《合集》{r['no']}-{r['seq']} [{r['group']}]: {r['text'][:80]}")
            report.append({"label": lab, "ob_glyph": cp(lab) or lab, "piece": nm,
                           "group": r["group"], "corpus_text": r["text"]})

json.dump(report, open(os.path.join(HERE, "result", "authenticity_check.json"),
                       "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\n[写出] result/authenticity_check.json（{len(report)} 条）")
