# -*- coding: utf-8 -*-
"""探测：能否从公开源取到某字的甲骨文/金文/篆书字形图与出处（用于构建字形演变链）"""
import io, re, sys, urllib.parse, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Accept-Language": "zh-CN,zh;q=0.9"}


def fetch(u, timeout=40):
    return urllib.request.urlopen(urllib.request.Request(u, headers=H),
                                  timeout=timeout).read().decode("utf-8", "replace")


def strip(t):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t)


print("=== 1) 国学大师《甲骨文合集》释文检索：能否按字查出片号 ===")
for ch in ["屯", "史", "寅", "大", "春"]:
    try:
        u = f"https://www.guoxuedashi.com/jgwhj/?bh={urllib.parse.quote(ch)}"
        t = fetch(u)
        txt = strip(t)
        print(f"  [{ch}] len={len(t)}")
        m = re.findall(r"合\s*(\d{1,5})", txt)[:8]
        print(f"       片号样例: {m}")
        # 找释文片段
        mm = re.search(r"(?:编号|序号|释文)[^。]{0,120}", txt)
        if mm:
            print(f"       {mm.group(0)[:150]}")
    except Exception as e:
        print(f"  [{ch}] ERR {type(e).__name__} {str(e)[:60]}")

print("\n=== 2) zdic 字源字形页：能否取到甲骨文/金文/小篆的分组 ===")
for ch in ["屯", "史", "寅"]:
    try:
        t = fetch(f"https://www.zdic.net/hans/{urllib.parse.quote(ch)}")
        txt = strip(t)
        i = txt.find("字源演变")
        seg = txt[i:i + 400] if i >= 0 else ""
        print(f"  [{ch}] {seg[:220]}")
        # 图片 url
        imgs = re.findall(r'(https?://[^"\']+\.(?:gif|png|jpg))', t)
        zy = [x for x in imgs if "zy" in x or "sw" in x or "jgw" in x][:6]
        print(f"       图片: {zy}")
    except Exception as e:
        print(f"  [{ch}] ERR {type(e).__name__} {str(e)[:60]}")

print("\n=== 3) 小学堂 字形演变 ===")
for u in ["https://xiaoxue.iis.sinica.edu.tw/yanbian?char=%E5%B1%AF",
          "https://xiaoxue.iis.sinica.edu.tw/yanbian/Search?char=%E5%B1%AF"]:
    try:
        t = fetch(u)
        print(f"  {u[-46:]:48s} len={len(t)}")
        imgs = re.findall(r'(?:src|href)="([^"]+\.(?:gif|png|jpg))"', t)
        print(f"       图: {imgs[:6]}")
    except Exception as e:
        print(f"  {u[-46:]:48s} ERR {type(e).__name__} {str(e)[:50]}")
