# -*- coding: utf-8 -*-
"""
国学大师甲骨文释文解析器
从 https://www.guoxuedashi.com/jgwhj/?bhfl=<1-25>&bh=<编号或字词> 抓取
输出字段：著录(合集/合补/屯南/…)、编号、序号、释文、分类(类组)
"""
import io, re, sys, gzip, json, os, time, urllib.parse, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "data", "gxds_cache")
os.makedirs(CACHE, exist_ok=True)
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Accept-Language": "zh-CN,zh;q=0.9", "Accept-Encoding": "gzip, deflate"}
BASE = "https://www.guoxuedashi.com/jgwhj/"


def get(u, t=40):
    req = urllib.request.Request(u, headers=H)
    with urllib.request.urlopen(req, timeout=t) as r:
        b = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            b = gzip.decompress(b)
        m = re.search(r"charset=([\w-]+)", r.headers.get("Content-Type", ""))
        enc = m.group(1) if m else "utf-8"
        try:
            return b.decode(enc)
        except Exception:
            return b.decode("utf-8", "replace")


def parse_rows(html):
    """
    解析释文表。表结构：著录 | 编号 | 序号 | 释文 | 分类
    行以 <tr> 分隔
    """
    out = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S | re.I):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S | re.I)
        if len(tds) < 4:
            continue
        cells = []
        for td in tds:
            s = re.sub(r"<[^>]+>", " ", td)
            s = (s.replace("&nbsp;", " ").replace("&amp;", "&")
                 .replace("&ldquo;", "「").replace("&rdquo;", "」"))
            cells.append(re.sub(r"\s+", " ", s).strip())
        # 过滤表头
        if cells[1] in ("编号", "") or "序号" in cells:
            continue
        out.append({"source": cells[0], "no": cells[1], "seq": cells[2],
                    "text": cells[3], "group": cells[4] if len(cells) > 4 else ""})
    return out


def fetch(bhfl, q, use_cache=True):
    key = f"{bhfl}_{urllib.parse.quote(str(q))}.html".replace("%", "_")
    p = os.path.join(CACHE, key)
    if use_cache and os.path.exists(p):
        return open(p, encoding="utf-8").read()
    u = f"{BASE}?bhfl={bhfl}&bh={urllib.parse.quote(str(q))}"
    html = get(u)
    open(p, "w", encoding="utf-8").write(html)
    time.sleep(0.4)
    return html


if __name__ == "__main__":
    print("=" * 96)
    print("解析测试")
    print("=" * 96)
    for label, bhfl, q in [("合集 1488", 1, "1488"), ("合集 1", 1, "1"),
                           ("字词 屯", 1, "屯"), ("类组 典賓", 1, "")]:
        html = fetch(bhfl, q)
        rows = parse_rows(html)
        print(f"\n【{label}】共解析 {len(rows)} 行")
        for r in rows[:5]:
            print(f"   {r['source']} {r['no']}-{r['seq']}  [{r['group']}]  {r['text'][:70]}")
        # 类组分布
        gs = {}
        for r in rows:
            g = r["group"]
            if g:
                gs[g] = gs.get(g, 0) + 1
        if gs:
            top = sorted(gs.items(), key=lambda x: -x[1])[:8]
            print(f"   类组分布: {top}")
