# -*- coding: utf-8 -*-
"""
国学大师甲骨文释文抓取器（类组 + 全《合集》释文）
按字抓取该字在《合集》等 25 部著录中的全部出现，含「分类」（类组）。
"""
import io, re, sys, gzip, json, os, time, random, urllib.parse, urllib.request
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
        except Exception as e:
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


def npages(html):
    m = re.search(r"page=(\d+)[^>]*>末页", html)
    return int(m.group(1)) if m else 1


def crawl(bhfl=1, q="", jgwfl="", maxpages=60, tag=None):
    tag = tag or (jgwfl or q or "all")[:20]
    rows, page = [], 1
    while page <= maxpages:
        p = os.path.join(CACHE, f"{bhfl}_{urllib.parse.quote(tag)}_{page}.html")
        if os.path.exists(p):
            html = open(p, encoding="utf-8").read()
        else:
            u = f"{BASE}?page={page}&bhfl={bhfl}&bh={urllib.parse.quote(q)}&jgwfl={urllib.parse.quote(jgwfl)}"
            html = get(u)
            open(p, "w", encoding="utf-8").write(html)
            time.sleep(0.5 + random.random() * 0.4)
        rs = parse(html)
        if not rs:
            break
        rows += rs
        total = npages(html)
        if page == 1:
            print(f"  [{tag}] 共 {total} 页")
        if page >= total:
            break
        page += 1
        if page % 10 == 0:
            print(f"    … {tag} 第 {page} 页，累计 {len(rows)} 行")
    return rows


if __name__ == "__main__":
    tests = [("屯", dict(bhfl=1, q="屯", tag="屯", maxpages=10)),
             ("典賓", dict(bhfl=1, jgwfl="典賓", tag="典賓", maxpages=3))]
    allrows = {}
    for name, kw in tests:
        print("=" * 94)
        print(f"抓取：{name}")
        print("=" * 94)
        rows = crawl(**kw)
        allrows[name] = rows
        gs = {}
        for r in rows:
            gs[r["group"]] = gs.get(r["group"], 0) + 1
        print(f"  共 {len(rows)} 行；类组分布前 10：")
        for g, c in sorted(gs.items(), key=lambda x: -x[1])[:10]:
            print(f"     {g or '(空)'}: {c}")
    json.dump(allrows, open(os.path.join(HERE, "result", "gxds_test.json"), "w",
                            encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n[写出] result/gxds_test.json")
