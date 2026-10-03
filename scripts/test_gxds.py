# -*- coding: utf-8 -*-
"""测试国学大师甲骨文检索：按片号与按类组"""
import io, re, sys, gzip, urllib.parse, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Accept-Language": "zh-CN,zh;q=0.9", "Accept-Encoding": "gzip, deflate"}


def get(u, t=35):
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


def strip(t):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t)


BASE = "https://www.guoxuedashi.com/jgwhj/"
tests = [
    ("片号 1", f"{BASE}?bhfl=1&bh=1"),
    ("片号 1488", f"{BASE}?bhfl=1&bh=1488"),
    ("类组=賓組", f"{BASE}?bhfl=1&bh=&jgwfl=" + urllib.parse.quote("賓組")),
    ("类组=典賓", f"{BASE}?bhfl=1&bh=&jgwfl=" + urllib.parse.quote("典賓")),
    ("字词=屯", f"{BASE}?bhfl=1&bh=" + urllib.parse.quote("屯")),
]
for name, u in tests:
    try:
        raw = get(u)
    except Exception as e:
        print(f"【{name}】ERR {type(e).__name__} {str(e)[:60]}")
        continue
    txt = strip(raw)
    zus = set(re.findall(r"(賓組|出組|何組|黃組|師組|歷組|無名組|圓體|師賓間|子組|午組|典賓|師賓間類|歷組一類)", raw))
    print("=" * 92)
    print(f"【{name}】len={len(raw)}  类组命中={zus if zus else '无'}")
    print("=" * 92)
    # 找释文主体
    body = re.search(r"编号.{0,600}", txt)
    print("   ", (body.group(0) if body else txt[400:1000])[:520])
    print()
