# -*- coding: utf-8 -*-
"""
国学大师《甲骨文合集》释文抓取器 v2（修正缓存键与解析）
URL: https://www.guoxuedashi.com/jgwhj/?page=<n>&bhfl=<1-25>&bh=<编号或字词>&jgwfl=<类组>
表格列：著录 | 编号 | 序号 | 释文 | 分类(类组)
"""
import io, os, re, sys, gzip, json, time, random, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "data", "gxds2")
os.makedirs(CACHE, exist_ok=True)
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Accept-Language": "zh-CN,zh;q=0.9", "Accept-Encoding": "gzip, deflate"}
BASE = "https://www.guoxuedashi.com/jgwhj/"


def _get(u, t=45, tries=4):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(u, headers=H)
            with urllib.request.urlopen(req, timeout=t) as r:
                b = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    b = gzip.decompress(b)
                return b.decode("utf-8", "replace")
        except Exception as e:
            last = e
            time.sleep(1.5 * (i + 1) + random.random())
    raise last


def parse(html):
    """返回 [{src,no,seq,text,group}]"""
    out = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S | re.I):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S | re.I)
        if len(tds) < 4:
            continue
        cells = []
        for td in tds:
            s = re.sub(r"<[^>]+>", " ", td)
            s = (s.replace("&nbsp;", " ").replace("&amp;", "&")
                 .replace("&ldquo;", "「").replace("&rdquo;", "」")
                 .replace("&hellip;", "…").replace("&mdash;", "—"))
            cells.append(re.sub(r"\s+", " ", s).strip())
        a, b, c = cells[0], cells[1], cells[2]
        # 表头
        if a in ("合/补", "编号", "") and b in ("编号", "序号", ""):
            continue
        if "序号" in cells:
            continue
        if len(cells) >= 5:
            src, no, seq, text, grp = cells[0], cells[1], cells[2], cells[3], cells[4]
        else:
            src, no, seq, text, grp = "", cells[0], cells[1], cells[2], cells[3]
        if not no.isdigit():
            continue
        out.append({"src": src, "no": no, "seq": seq, "text": text, "group": grp})
    return out


def npages(html):
    m = re.search(r"page=(\d+)[^>]*>末页", html)
    return int(m.group(1)) if m else 1


def fetch_page(q, bhfl=1, jgwfl="", page=1):
    key = f"{bhfl}__{urllib.parse.quote(str(q))}__{urllib.parse.quote(jgwfl)}__{page}.html"
    p = os.path.join(CACHE, key)
    if os.path.exists(p) and os.path.getsize(p) > 5000:
        return open(p, encoding="utf-8").read()
    u = (f"{BASE}?page={page}&bhfl={bhfl}&bh={urllib.parse.quote(str(q))}"
         f"&jgwfl={urllib.parse.quote(jgwfl)}")
    html = _get(u)
    open(p, "w", encoding="utf-8").write(html)
    time.sleep(0.5 + random.random() * 0.5)
    return html


def query(q, bhfl=1, jgwfl="", maxpages=40, verbose=False):
    rows, page, total = [], 1, 1
    while page <= min(maxpages, total):
        html = fetch_page(q, bhfl, jgwfl, page)
        rs = parse(html)
        if page == 1:
            total = npages(html)
            if verbose:
                print(f"    '{q}' bhfl={bhfl} jgwfl={jgwfl}: {total} 页")
        if not rs and page > 1:
            break
        rows += rs
        page += 1
    return rows, total


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    print("=" * 92)
    print("自检：解析结果")
    print("=" * 92)
    for q in ["7371", "15410", "屯"]:
        rows, total = query(q, maxpages=2, verbose=True)
        print(f"\n【{q}】{len(rows)} 行 / 共 {total} 页")
        for r in rows[:4]:
            print(f"   {r['src']} {r['no']}-{r['seq']} [{r['group']}] {r['text'][:70]}")
