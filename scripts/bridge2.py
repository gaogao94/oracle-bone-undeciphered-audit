# -*- coding: utf-8 -*-
"""桥接验证（独立脚本，不导入会 wrapp stdout 的模块）"""
import io, os, re, sys, gzip, json, time, urllib.parse, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "data", "gxds")
os.makedirs(CACHE, exist_ok=True)
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Accept-Language": "zh-CN,zh;q=0.9", "Accept-Encoding": "gzip, deflate"}
BASE = "https://www.guoxuedashi.com/jgwhj/"


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
        if len(cells) >= 5:
            out.append({"src": cells[0], "no": cells[1], "seq": cells[2],
                        "text": cells[3], "group": cells[4]})
        else:
            out.append({"src": "", "no": cells[0], "seq": cells[1],
                        "text": cells[2], "group": cells[3]})
    return out


def query(q, bhfl=1, page=1, cache_key=None):
    key = cache_key or f"q{bhfl}_{urllib.parse.quote(str(q))}_p{page}"
    p = os.path.join(CACHE, key + ".html")
    if os.path.exists(p):
        return open(p, encoding="utf-8").read()
    u = f"{BASE}?page={page}&bhfl={bhfl}&bh={urllib.parse.quote(str(q))}&jgwfl="
    html = get(u)
    open(p, "w", encoding="utf-8").write(html)
    time.sleep(0.6)
    return html


OB = os.path.join(HERE, "data", "obimd")
mc = json.load(open(os.path.join(OB, "main_character.json"), encoding="utf-8"))
data = json.load(open(os.path.join(OB, "data.json"), encoding="utf-8"))
cp = lambda l: mc.get(l, {}).get("codepoint") or ""
freq = {}
for p in data:
    for g in p.get("RecordUtilSentenceGroupVoList") or []:
        for c in g.get("RecordUtilOracleCharVoList") or []:
            if c.get("Label"):
                freq[c["Label"]] = freq.get(c["Label"], 0) + 1
label_of_char = {}
for lab, v in mc.items():
    c = v.get("codepoint") or ""
    if len(c) == 1:
        label_of_char.setdefault(c, lab)

TARGETS = [("fybnj2savm", "H15410"), ("urzeocieq8", "H2886"),
           ("ptd0rmmnrv", "H15401"), ("gx21ndp7yy", "H7371"),
           ("mepmffeebh", "H553")]

for lab, piece in TARGETS:
    num = piece.lstrip("H")
    print("=" * 96)
    print(f"{cp(lab) or lab} (label={lab}, freq={freq.get(lab)}) 所在片 {piece} -> 试作《合集》{num}")
    print("=" * 96)
    ob = []
    for p in data:
        if p.get("RubbingName") == piece:
            for g in p.get("RecordUtilSentenceGroupVoList") or []:
                seq = sorted([c for c in (g.get("RecordUtilOracleCharVoList") or [])
                              if c.get("Label")], key=lambda c: c.get("OrderNumber") or 0)
                if seq:
                    ob.append(" ".join(cp(c["Label"]) or "?" for c in seq))
    print("  OBIMD 辞例:", ob)
    if not num.isdigit():
        continue
    try:
        html = query(num)
    except Exception as e:
        print("  抓取失败:", e)
        continue
    rows = parse(html)
    print(f"  《合集》释文 ({len(rows)} 条):")
    for r in rows[:6]:
        print(f"     {r['src']} {r['no']}-{r['seq']}  [{r['group']}]  {r['text'][:88]}")
