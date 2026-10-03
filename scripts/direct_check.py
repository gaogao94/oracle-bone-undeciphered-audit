# -*- coding: utf-8 -*-
"""直接抓取（不用缓存）：核实《合集》对若干片的释文"""
import io, os, re, sys, gzip, time, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
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
        except Exception as e:
            if i == tries - 1:
                raise
            time.sleep(2)


def parse(html):
    out = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S | re.I):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S | re.I)
        if len(tds) < 4:
            continue
        cells = []
        for td in tds:
            s = re.sub(r"<[^>]+>", " ", td)
            s = s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&hellip;", "…")
            cells.append(re.sub(r"\s+", " ", s).strip())
        if cells[0] in ("合/补", "编号") or "序号" in cells:
            continue
        if len(cells) >= 5 and cells[1].isdigit():
            out.append((cells[0], cells[1], cells[2], cells[3], cells[4]))
    return out


for num in ["7371", "15410", "32813", "15401", "2886", "95"]:
    u = f"https://www.guoxuedashi.com/jgwhj/?page=1&bhfl=1&bh={num}&jgwfl="
    try:
        rows = parse(get(u))
    except Exception as e:
        print(f"《合集》{num}: 抓取失败 {type(e).__name__} {str(e)[:50]}")
        continue
    print("=" * 96)
    print(f"《合集》{num}  —— {len(rows)} 条")
    print("=" * 96)
    for src, no, seq, txt, grp in rows[:6]:
        print(f"   [{grp}] {txt[:96]}")
    time.sleep(0.5)
