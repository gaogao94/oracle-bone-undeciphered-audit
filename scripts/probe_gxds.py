# -*- coding: utf-8 -*-
"""测国学大师《甲骨文合集》释文能否按片号抓取（含类组标注）"""
import io, re, sys, gzip, urllib.request, urllib.error
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Accept-Language": "zh-CN,zh;q=0.9",
     "Accept-Encoding": "gzip, deflate"}


def get(u, t=35):
    req = urllib.request.Request(u, headers=H)
    with urllib.request.urlopen(req, timeout=t) as r:
        b = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            b = gzip.decompress(b)
        for enc in ("utf-8", "gbk", "gb18030"):
            try:
                return b.decode(enc)
            except Exception:
                continue
        return b.decode("utf-8", "replace")


for bh in ["1", "10", "6057", "11401"]:
    u = f"https://www.guoxuedashi.com/jgwhj/?bh={bh}"
    try:
        raw = get(u)
    except Exception as e:
        print(f"bh={bh} ERR {type(e).__name__} {str(e)[:60]}")
        continue
    print("=" * 92)
    print(f"bh={bh}  len={len(raw)}")
    print("=" * 92)
    # 找释文区块
    for pat in [r"<div[^>]*class=\"[^\"]*(?:con|content|text|jgwhj)[^\"]*\"[^>]*>(.*?)</div>",
                r"编号[:：]?\s*([^<]{0,200})",
                r"([\u4e00-\u9fff]{2,}[，。、；：][^<]{5,200})"]:
        ms = re.findall(pat, raw, re.S)
        if ms:
            for m in ms[:3]:
                s = re.sub(r"<[^>]+>", " ", m)
                s = re.sub(r"\s+", " ", s).strip()
                if len(s) > 10:
                    print(f"   [{pat[:22]}] {s[:220]}")
            break
    # 类组关键词
    zu = re.findall(r"(賓組|宾组|出組|出组|何組|何组|黃組|黄组|師組|师组|歷組|历组|無名組|无名组|圓體|圆体|師賓間|师宾间|子組|子组|午組|午组|典賓|典宾)", raw)
    print(f"   类组关键词命中: {set(zu) if zu else '无'}")
