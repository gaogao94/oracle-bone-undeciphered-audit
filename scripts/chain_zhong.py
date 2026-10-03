# -*- coding: utf-8 -*-
"""
为「中」建立字形演变链的文本证据：甲骨 → 金文 → 篆
来源：zdic 字源字形区块（甲骨文/金文/楚系简帛/说文/秦系简牍 分组的出处列表）
"""
import io, json, os, re, sys, urllib.parse, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "data")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120 Safari/537.36",
     "Accept-Language": "zh-CN,zh;q=0.9"}


def strip(t):
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t)


STAGES = ["甲骨文", "金文", "楚系简帛", "说文", "秦系简牍", "隶书", "楷书"]


def stage_sources(ch):
    u = f"https://www.zdic.net/hans/{urllib.parse.quote(ch)}"
    t = urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=35
                              ).read().decode("utf-8", "replace")
    txt = strip(t)
    i = txt.find("字源演变")
    if i < 0:
        return {}
    seg = txt[i:]
    out = {}
    for k, st in enumerate(STAGES):
        j = seg.find(st)
        if j < 0:
            continue
        # 找下一个阶段名作为结束
        ends = [seg.find(s, j + len(st)) for s in STAGES[k + 1:]]
        ends = [e for e in ends if e > 0]
        end = min(ends) if ends else j + 400
        body = seg[j + len(st):end].strip()
        # 去掉"更多 →"等
        body = body.replace("更多 →", "").replace("更多", "").strip()
        out[st] = body[:600]
    return out


for ch in ["中", "史", "仲"]:
    print("=" * 96)
    print(f"【{ch}】字形演变链（zdic 字源字形区块）")
    print("=" * 96)
    st = stage_sources(ch)
    for s in STAGES:
        if s in st and st[s]:
            print(f"  {s}: {st[s][:400]}")
    print()

# 另取「中」的上古音与《说文》训释
print("=" * 96)
print("【中】上古音与《说文》")
print("=" * 96)
u = "https://www.zdic.net/hans/%E4%B8%AD"
t = strip(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=35
                                ).read().decode("utf-8", "replace"))
for pat in [r"上古音.{0,160}", r"说文解字.{0,300}", r"廣韻.{0,120}", r"康熙字典.{0,200}"]:
    m = re.search(pat, t)
    if m:
        print(f"  {m.group(0)[:300]}")
