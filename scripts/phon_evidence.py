# -*- coding: utf-8 -*-
"""
补完第三类证据：音韵与通假
- 「中」与异体「仲」的音韵关系（同声同韵？）
- 《说文》训释
- 该字作专名时是否需要通假（前人判据：专名不烦通假）
同时探 xianqin.org 的检索能力（用于找第三个辞例）
"""
import io, json, os, re, sys, urllib.parse, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Accept-Language": "zh-CN,zh;q=0.9"}


def strip(t):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t)


def get(u, t=35):
    return urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=t
                                 ).read().decode("utf-8", "replace")


print("=" * 96)
print("一、音韻證據：中 / 仲 / 中丁")
print("=" * 96)
for ch in ["中", "仲", "蟲", "終", "冬"]:
    try:
        t = strip(get(f"https://www.zdic.net/hans/{urllib.parse.quote(ch)}"))
        m = re.search(r"上古音\s*(黄侃系统：[^；]*；)?\s*(王力系统：[^；]*；)?", t)
        g = re.search(r"廣韻[^。]{0,60}", t)
        sy = re.search(r"说文解字[^。]{0,120}", t)
        print(f"  【{ch}】{m.group(0).strip() if m else '—'}")
        if sy:
            print(f"       說文: {sy.group(0)[:110]}")
    except Exception as e:
        print(f"  【{ch}】ERR {type(e).__name__}")

print("\n" + "=" * 96)
print("二、《說文》對「中」的訓釋")
print("=" * 96)
try:
    t = strip(get("https://www.zdic.net/hans/%E4%B8%AD"))
    for pat in [r"中[^。]{0,20}而[^。]{0,80}", r"从[^。]{0,60}丨[^。]{0,60}",
                r"內也[^。]{0,80}", r"上下通[^。]{0,60}"]:
        for m in re.finditer(pat, t):
            print("  ", m.group(0)[:130])
except Exception as e:
    print("  ERR", e)

print("\n" + "=" * 96)
print("三、xianqin.org（先秦史研究室）檢索能力")
print("=" * 96)
try:
    home = get("https://www.xianqin.org/")
    txt = strip(home)
    print(f"  首頁 len={len(home)}")
    # 找检索表单
    forms = re.findall(r"<form[^>]*>", home)
    print(f"  form 數: {len(forms)}")
    for f in forms[:5]:
        print("   ", f[:200])
    inputs = re.findall(r"<input[^>]*>", home)
    for i in inputs[:10]:
        print("   input:", i[:160])
    # 数据库链接
    links = set(re.findall(r'href="([^"]+)"', home))
    db = [l for l in links if any(k in l.lower() for k in ("search", "query", "db", "jia", "gu"))]
    print("  疑似檢索/數據庫鏈接:", sorted(db)[:15])
except Exception as e:
    print("  ERR", e)
