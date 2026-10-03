# -*- coding: utf-8 -*-
"""从 zdic 提取：上古音（声纽/韵部）+ 声符（部件分解）"""
import io, re, json, sys, urllib.parse, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Accept-Language": "zh-CN,zh;q=0.9"}


def fetch(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=30
                                  ).read().decode("utf-8", "replace")


def strip(t):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t)


for ch in ["屯", "春", "蠢", "徹", "阱", "歲", "伐", "王"]:
    try:
        html = fetch(f"https://www.zdic.net/hans/{urllib.parse.quote(ch)}")
    except Exception as e:
        print(f"{ch}: ERR {e}")
        continue
    txt = strip(html)
    # 上古音区块
    m = re.search(r"上古音.{0,220}", txt)
    shang = m.group(0) if m else "—"
    # 部件 / 声符
    parts = []
    for pat in [r"部\s*件\s*[:：]?\s*([^ ]{1,40})",
                r"聲\s*符\s*[:：]?\s*([^ ]{1,20})",
                r"声\s*符\s*[:：]?\s*([^ ]{1,20})",
                r"構\s*成\s*[:：]?\s*([^ ]{1,40})"]:
        mm = re.search(pat, txt)
        if mm:
            parts.append(mm.group(1))
    print(f"[{ch}] 上古音: {shang[:150]}")
    if parts:
        print(f"      部件/声符: {parts}")
    print()
