# -*- coding: utf-8 -*-
"""为 3 个保留候选取字形链（甲骨→金文→篆）与音韵"""
import io, json, os, re, sys, urllib.parse, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Accept-Language": "zh-CN,zh;q=0.9"}


def strip(t):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t)


def chain(ch):
    u = f"https://www.zdic.net/hans/{urllib.parse.quote(ch)}"
    t = strip(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=40
                                    ).read().decode("utf-8", "replace"))
    i = t.find("各书体字形实例")
    if i < 0:
        i = t.find("字源演变")
    out = t[i:i + 900] if i >= 0 else "—"
    m = re.search(r"上古音\s*(黄侃系统：[^；]*；)?\s*(王力系统：[^；]*；)?", t)
    return out, (m.group(0).strip() if m else "—")


for ch in ["禾", "殺", "雀"]:
    c, ph = chain(ch)
    print("=" * 96)
    print(f"【{ch}】")
    print("=" * 96)
    print(f"  音韻: {ph}")
    print(f"  字形演變鏈: {c[:520]}")
    print()
