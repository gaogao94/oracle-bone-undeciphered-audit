# -*- coding: utf-8 -*-
"""实测复旦「缀玉联珠」甲骨缀合信息库，核准缀合总量"""
import io, re, sys, urllib.parse, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

URL = "https://www.fdgwz.org.cn/ZhuiHeLab/Home"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
     "Content-Type": "application/x-www-form-urlencoded"}


def post(txt):
    body = urllib.parse.urlencode({"txtname": txt}).encode("utf-8")
    req = urllib.request.Request(URL, data=body, headers=H, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


# 先看首页（GET）
try:
    req = urllib.request.Request(URL, headers=H)
    with urllib.request.urlopen(req, timeout=60) as r:
        home = r.read().decode("utf-8", "replace")
    print(f"[首页] len={len(home)}")
    for m in re.finditer(r"[^<>]{0,60}(?:缀合|條|条|組|组)[^<>]{0,60}", home):
        t = m.group(0).strip()
        if any(k in t for k in ("餘", "余", "共", "信息", "篇", "組", "组")):
            print("   ", t[:120])
except Exception as e:
    print("[首页] ERR", e)

print()
for kw in ["乙", "合", "屯南", "英", "花東", "村中南"]:
    try:
        t = post(kw)
        m = re.search(r"共檢得\s*([\d,]+)\s*條", t) or re.search(r"共检得\s*([\d,]+)\s*条", t)
        n = m.group(1) if m else "?"
        print(f"  检索「{kw}」→ {n} 條")
    except Exception as e:
        print(f"  检索「{kw}」ERR {e}")
