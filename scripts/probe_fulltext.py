# -*- coding: utf-8 -*-
"""探测：《甲骨文合集》释文全文能否检索（用于扩充辞例）"""
import io, re, sys, urllib.parse, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Accept-Language": "zh-CN,zh;q=0.9"}


def get(u, t=30):
    return urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=t
                                 ).read().decode("utf-8", "replace")


def strip(t):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t)


print("=== 1) 国学大师《甲骨文合集》释文：按片号取 ===")
for bh in ["1", "2", "6057", "1488"]:
    try:
        t = strip(get(f"https://www.guoxuedashi.com/jgwhj/?bh={bh}"))
        i = t.find("释文")
        print(f"  bh={bh}: len={len(t)}  → {t[max(0,i):i+160] if i>0 else t[:160]}")
    except Exception as e:
        print(f"  bh={bh}: ERR {type(e).__name__} {str(e)[:50]}")

print("\n=== 2) 按字检索（看是否有字词检索） ===")
for q in ["中", "%E4%B8%AD"]:
    for pat in [f"https://www.guoxuedashi.com/jgwhj/?bh={q}",
                f"https://www.guoxuedashi.com/jgwhj/?zi={q}",
                f"https://www.guoxuedashi.com/jgwhj/?sw={q}"]:
        try:
            t = strip(get(pat))
            m = re.findall(r"共\s*(\d+)\s*[条條]", t)
            print(f"  {pat[-40:]:42s} len={len(t)} 命中数={m[:3]}")
        except Exception as e:
            print(f"  {pat[-40:]:42s} ERR {str(e)[:40]}")

print("\n=== 3) 单页结构：能否提取释文正文 ===")
try:
    raw = get("https://www.guoxuedashi.com/jgwhj/?bh=1488")
    txt = strip(raw)
    # 找形如「编号..释文」的片段
    for m in re.finditer(r"[^ ]{0,10}\d{3,5}[^ ]{0,80}", txt):
        s = m.group(0)
        if any(k in s for k in ("卜", "貞", "贞", "王")):
            print("   ", s[:150])
except Exception as e:
    print("   ERR", e)

print("\n=== 4) 其他可能有全文检索的站点 ===")
for u in ["https://www.xianqin.org/", "http://www.xianqin.org/",
          "https://www.bsm.org.cn/", "http://www.bsm.org.cn/"]:
    try:
        t = get(u)
        print(f"  {u:34s} OK len={len(t)}")
    except Exception as e:
        print(f"  {u:34s} ERR {type(e).__name__} {str(e)[:40]}")
